import importlib.util
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location('shift_background', Path(__file__).parents[1] / 'afk_lobby' / 'shift_background.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
TOKEN = 'a' * 32
OTHER = 'b' * 32

class Native:
    def __init__(self):
        self.owned = False; self.values = [25, 25, 25]; self.calls = []; self.fail = 0
    def bind_thread(self): self.calls.append('bind')
    def enter(self): self.calls.append('enter'); self.owned = True; self.values = [1, 1, 1]
    def inspect(self): self.calls.append('inspect'); return {'visibility': self.values, 'visible': True, 'owned': self.owned, 'canvas_visibility': 2}
    def restore(self):
        self.calls.append('restore')
        if self.fail:
            self.fail -= 1
            raise RuntimeError('restore failed')
        self.owned = False

class Context:
    Name = 'Context'
    def __init__(self, path): self.path = path
    def _path_name(self): return self.path

class SDK:
    def __init__(self, player):
        self.paused = True; self.closes = 0; self.input_calls = 0; self.contexts = []
        self.sub = SimpleNamespace(Name='local', Outer=player, Class=SimpleNamespace(_implements=lambda i: True))
        self.unreal = SimpleNamespace(BoundFunction=lambda fn, obj: lambda context, zero: (True, 1))
        self.stats = SimpleNamespace(SetGamePaused=self.unpause, IsGamePaused=lambda pc: self.paused)
        self.input = SimpleNamespace(ClearAllUserFocus=self.inputcall, SetInputMode_GameOnly=self.inputcall, SetFocusToGameViewport=self.inputcall)
        self.shift = SimpleNamespace(Close=self.close)
    def unpause(self, pc, value): self.paused = value
    def inputcall(self, *args): self.input_calls += 1
    def close(self): self.closes += 1
    def find_class(self, name):
        if name.endswith('EnhancedInputSubsystemInterface'): return object()
        return SimpleNamespace(ClassDefaultObject=self.stats if name == 'GameplayStatics' else self.input if name.endswith('WidgetBlueprintLibrary') else self.shift)
    def find_object(self, *args): return object()
    def find_all(self, name, exact): return [self.sub] if name == 'EnhancedInputLocalPlayerSubsystem' else self.contexts

class BackgroundTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0; self.player = object(); self.pawn = object()
        self.pc = SimpleNamespace(Player=self.player, Pawn=self.pawn)
        self.sdk = SDK(self.player); self.native = Native()
        self.c = m.BackgroundController(self.native, self.sdk, lambda:self.pc, lambda:self.now)
    def request(self, mode, token=TOKEN): return self.c.request({'mode':mode,'token':token})
    def start(self):
        self.assertTrue(self.request('start')['ok']); self.c.tick(); self.assertEqual(self.c.status()['state'],'active')
    def test_lease_ownership_and_stop(self):
        self.start(); before=self.sdk.input_calls
        self.assertFalse(self.request('start',OTHER)['ok']); self.assertTrue(self.request('heartbeat')['ok'])
        self.now=4; self.c.tick(); self.assertEqual(self.sdk.input_calls,before)
        self.now=6; self.c.tick(); self.assertEqual(self.c.status()['state'],'idle'); self.assertEqual(self.sdk.closes,1)
        self.assertFalse(self.request('heartbeat')['ok']); self.assertTrue(self.c.quiescent)
    def test_unavailable_shift_does_not_change_pause_or_input(self):
        self.native.values=[2,2,2]
        self.assertTrue(self.request('start')['ok']); self.c.tick()
        self.assertEqual(self.c.status()['state'],'error')
        self.assertTrue(self.sdk.paused); self.assertEqual(0,self.sdk.input_calls)
        self.assertNotIn('enter',self.native.calls)
    def test_reentrant_tick_during_restore_is_ignored(self):
        self.start(); calls=[]
        def restore():
            calls.append('restore'); self.c.tick(); self.native.owned=False
        self.native.restore=restore
        self.request('stop'); self.c.tick()
        self.assertEqual(['restore'],calls); self.assertTrue(self.c.quiescent)
    def test_reentrant_open_close_are_blocked_during_restore(self):
        self.start(); decisions=[]
        def restore():
            decisions.extend([self.c.before_open(), self.c.before_close()]); self.native.owned=False
        self.native.restore=restore
        self.sdk.shift.Close=lambda: decisions.append(self.c.before_close())
        self.request('stop'); self.c.tick()
        self.assertEqual([False,False,True],decisions);self.assertTrue(self.c.quiescent)
    def test_menu_guard(self):
        self.sdk.contexts=[Context('/Game/Input/UI/Menu')]
        self.assertTrue(self.request('start')['ok']); self.c.tick()
        self.assertEqual(self.c.status()['state'],'error'); self.assertIn('Close other menus',self.c.status()['reason']); self.assertNotIn('enter',self.native.calls)
    def test_mixed_visibility_stops_and_surfaces_error(self):
        self.start(); self.native.values=[1,25,1]
        self.c.tick()
        self.assertEqual(self.native.calls.count('restore'),1)
        self.assertEqual(self.c.status()['state'],'error')
        self.assertIn('visibility changed unexpectedly',self.c.status()['reason'])
        self.assertFalse(self.request('heartbeat')['ok'])
    def test_unexpected_visibility_restore_failure_remains_owned(self):
        self.start(); self.native.values=[4,4,4]; self.native.fail=4
        for _ in range(3): self.c.tick()
        self.assertEqual(self.c.status()['state'],'error')
        self.assertFalse(self.c.quiescent);self.assertTrue(self.native.owned)
        self.assertFalse(self.request('heartbeat')['ok'])
    def test_foreground_does_not_reacquire(self):
        self.start(); self.native.values=[25,25,25]; self.c.tick()
        self.assertEqual(self.c.status()['state'],'foreground'); self.assertEqual(self.sdk.closes,0)
        self.assertFalse(self.request('heartbeat')['ok']); self.c.tick(); self.assertEqual(self.native.calls.count('enter'),1)
    def test_foreground_restore_retry_keeps_view_open(self):
        self.start(); self.native.values=[25,25,25]; self.native.fail=1
        self.c.tick(); self.assertEqual(self.c.status()['state'],'stopping')
        self.c.tick(); self.assertEqual(self.c.status()['state'],'foreground'); self.assertEqual(self.sdk.closes,0)
    def test_close_failure_retries_without_ownership(self):
        self.start(); calls=[]
        def flaky():
            calls.append(1)
            if len(calls)==1: raise RuntimeError('close failure')
        self.sdk.shift.Close=flaky
        self.request('stop'); self.c.tick(); self.assertFalse(self.c.quiescent)
        self.c.tick(); self.assertTrue(self.c.quiescent); self.assertEqual(len(calls),2)
    def test_travel_and_retry(self):
        self.start(); self.native.fail=2; self.pc.Pawn=object()
        self.c.tick(); self.assertEqual(self.c.status()['state'],'stopping'); self.assertFalse(self.c.quiescent)
        self.c.tick(); self.c.tick(); self.assertTrue(self.c.quiescent); self.assertEqual(self.sdk.closes,1)
    def test_partial_enter_restores(self):
        def fail(): self.native.owned=True; raise RuntimeError('partial')
        self.native.enter=fail; self.request('start'); self.c.tick(); self.assertEqual(self.c.status()['state'],'stopping')
        self.c.tick(); self.assertEqual(self.native.calls.count('restore'),1)
    def test_wrong_thread_cannot_touch_native(self):
        self.start(); seen=[]
        def worker():
            try: self.c.tick()
            except RuntimeError: seen.append(True)
        t=threading.Thread(target=worker);t.start();t.join();self.assertEqual(seen,[True])
    def test_shutdown_and_invalid(self):
        self.assertFalse(self.c.request({'mode':'start','token':TOKEN,'extra':1})['ok'])
        self.start(); self.c.shutdown(); self.assertFalse(self.c.quiescent); self.c.tick(); self.assertTrue(self.c.quiescent)
        self.assertFalse(self.request('start')['ok'])

if __name__ == '__main__': unittest.main()
