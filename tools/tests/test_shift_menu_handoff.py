import importlib.util
from pathlib import Path
import sys
import threading
import types
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1] / 'afk_lobby'
spec = importlib.util.spec_from_file_location('shift_menu_handoff', ROOT / 'shift_menu_handoff.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.now = 0.0
        self.identity = ('pc', 'pawn', 'player', 'instance')
        self.sample = m.MenuSnapshot(True, self.identity, False, True, 'active', False)
        self.calls = []
        self.close_result = True
        self.resume_result = True
        self.handoff = m.MenuHandoff(
            lambda: self.sample,
            lambda: self.calls.append('close') is None and self.close_result,
            lambda: self.calls.append('resume') is None and self.resume_result,
            lambda: self.now,
            cancel_resume=lambda: self.calls.append('cancel_resume'))

    def enter_menu(self):
        self.sample = m.MenuSnapshot(True, self.identity, True, True, 'active', False)
        self.handoff.tick()

    def close_menu_and_resume(self):
        self.sample = m.MenuSnapshot(False, self.identity, False, True, 'idle', True)
        self.handoff.tick()
        self.now += .26
        self.handoff.tick()

    def test_observed_menu_closes_once_and_requires_closed_native_view(self):
        self.enter_menu()
        self.assertEqual(['close'], self.calls)
        self.assertEqual('suspended_menu', self.handoff.status()['handoff_state'])
        self.sample = m.MenuSnapshot(False, self.identity, False, True, 'stopping', False)
        self.handoff.tick()
        self.assertNotIn('resume', self.calls)
        self.sample = m.MenuSnapshot(False, self.identity, False, True, 'idle', True)
        self.handoff.tick()
        self.now += .26
        self.handoff.tick()
        self.assertEqual(['close', 'resume'], self.calls)
        self.assertEqual('resuming', self.handoff.status()['handoff_state'])
        self.assertNotIn('active', self.handoff.status().values())
        self.sample = m.MenuSnapshot(True, self.identity, False, True, 'pending', False)
        self.handoff.tick()
        self.assertEqual('resuming', self.handoff.status()['handoff_state'])
        self.sample = m.MenuSnapshot(True, self.identity, False, True, 'active', False)
        self.handoff.tick()
        self.assertEqual('idle', self.handoff.status()['handoff_state'])

    def test_failed_close_does_not_resume_or_retry_and_explicit_start_rearms(self):
        self.close_result = False
        self.enter_menu()
        self.assertEqual('close_pending', self.handoff.status()['handoff_error'])
        self.sample = m.MenuSnapshot(False, self.identity, False, True, 'error', False)
        self.handoff.tick()
        self.now += 10
        self.handoff.tick()
        self.assertEqual(['close'], self.calls)
        self.assertNotIn('resume', self.calls)
        self.handoff.on_start()
        self.sample = m.MenuSnapshot(True, self.identity, True, True, 'active', False)
        self.handoff.tick()
        self.assertEqual(['close', 'close'], self.calls)

    def test_stop_show_disable_and_identity_change_cancel_resume(self):
        for method in ('on_stop', 'on_show', 'on_disabled'):
            self.setUp()
            self.enter_menu()
            self.close_menu_and_resume()
            getattr(self.handoff, method)()
            self.assertEqual('idle', self.handoff.status()['handoff_state'])
            self.assertIn('cancel_resume', self.calls)
        self.setUp()
        self.enter_menu()
        self.close_menu_and_resume()
        self.sample = m.MenuSnapshot(False, ('new-pc',), False, True, 'idle', True)
        self.handoff.tick()
        self.assertEqual('idle', self.handoff.status()['handoff_state'])
        self.assertEqual(1, self.calls.count('cancel_resume'))

    def test_disconnect_or_unknown_menu_cancels_without_resume(self):
        self.enter_menu()
        self.sample = m.MenuSnapshot(False, self.identity, None, True, 'idle', True)
        self.handoff.tick()
        self.assertEqual('idle', self.handoff.status()['handoff_state'])
        self.assertNotIn('resume', self.calls)
        self.enter_menu()
        self.sample = m.MenuSnapshot(False, self.identity, False, False, 'idle', True)
        self.handoff.tick()
        self.assertEqual('idle', self.handoff.status()['handoff_state'])

    def test_native_open_pause_during_resume_does_not_cancel_own_start(self):
        self.enter_menu()
        self.close_menu_and_resume()
        self.sample = m.MenuSnapshot(False, self.identity, True, True, 'pending', False)
        self.handoff.tick()
        self.assertEqual('resuming', self.handoff.status()['handoff_state'])
        self.assertNotIn('cancel_resume', self.calls)
        self.sample = m.MenuSnapshot(True, self.identity, False, True, 'active', False)
        self.handoff.tick()
        self.assertEqual('idle', self.handoff.status()['handoff_state'])
        self.assertEqual(1, self.calls.count('resume'))

    def test_long_menu_dwell_then_exit_resumes_once(self):
        self.enter_menu()
        self.sample = m.MenuSnapshot(False, self.identity, True, True, 'idle', True)
        for now in (121, 180, 3600, 28800):
            self.now = now
            self.handoff.tick()
            self.assertEqual('suspended_menu', self.handoff.status()['handoff_state'])
        self.close_menu_and_resume()
        self.assertEqual(1, self.calls.count('resume'))
        self.sample = m.MenuSnapshot(True, self.identity, False, True, 'active', False)
        self.handoff.tick(); self.handoff.tick()
        self.assertEqual(1, self.calls.count('resume'))

    def test_failed_resume_is_not_repeated(self):
        self.enter_menu(); self.resume_result = False
        self.close_menu_and_resume()
        self.now += 20; self.handoff.tick()
        self.assertEqual('resume_failed', self.handoff.status()['handoff_error'])
        self.assertEqual(1, self.calls.count('resume'))


class ProbeTests(unittest.TestCase):
    class Context:
        def __init__(self, name, path):
            self.Name, self.path = name, path
        def _path_name(self):
            return self.path

    def make_sdk(self, contexts, paused=True):
        player = object()
        subsystem = SimpleNamespace(Name='Local', Outer=player,
                                    Class=SimpleNamespace(_implements=lambda _interface: True))
        pc = SimpleNamespace(Player=player, Pawn=object())
        sdk = SimpleNamespace(
            find_class=lambda name: (SimpleNamespace(ClassDefaultObject=SimpleNamespace(
                IsGamePaused=lambda _pc: paused)) if name == 'GameplayStatics' else object()),
            find_object=lambda *_args: object(),
            find_all=lambda name, _exact: ([subsystem] if name == 'EnhancedInputLocalPlayerSubsystem'
                                           else contexts),
            unreal=SimpleNamespace(BoundFunction=lambda _fn, _sub: lambda context, _priority:
                                   (context.path in self.active, 1)))
        return sdk, pc

    def test_probe_detects_menu_context_but_ignores_cursor_only(self):
        menu = self.Context('menu', '/Game/UI/Input/Context_UI_Menu.Context_UI_Menu')
        self.active = {menu.path}
        sdk, pc = self.make_sdk([menu], paused=False)
        self.assertTrue(m.probe_menu_state(sdk, pc))
        cursor = self.Context('cursor', '/Game/UI/Input/Context_UI_Cursor.Context_UI_Cursor')
        self.active = {cursor.path}
        sdk, pc = self.make_sdk([cursor], paused=False)
        self.assertFalse(m.probe_menu_state(sdk, pc))

    def test_probe_fails_closed_on_ambiguous_or_oversized_contexts(self):
        menu = self.Context('menu', '/Game/UI/Input/Context_UI_Menu.Context_UI_Menu')
        self.active = {menu.path}
        sdk, pc = self.make_sdk([menu] * 129)
        self.assertIsNone(m.probe_menu_state(sdk, pc))
        sdk, pc = self.make_sdk([menu], paused='yes')
        self.assertIsNone(m.probe_menu_state(sdk, pc))


def _load_companion_for_tests():
    package = 'menu_handoff_test_pkg'
    pkg = types.ModuleType(package)
    pkg.__path__ = [str(ROOT)]
    sys.modules[package] = pkg
    peer_spec = importlib.util.spec_from_file_location(package + '.shift_peer_process', ROOT / 'shift_peer_process.py')
    peer = importlib.util.module_from_spec(peer_spec)
    sys.modules[peer_spec.name] = peer
    peer_spec.loader.exec_module(peer)

    base = types.ModuleType('mods_base')
    base.CoopSupport = types.SimpleNamespace(Unknown=None)
    base.Game = types.SimpleNamespace(BL4=None)
    base.SETTINGS_DIR = Path.cwd()
    base.build_mod = lambda **_kwargs: None
    sdk_module = types.ModuleType('unrealsdk')
    sdk_module.logging = types.SimpleNamespace(warning=lambda *_args: None)
    hooks = types.ModuleType('unrealsdk.hooks')
    hooks.Type = types.SimpleNamespace(POST=None, PRE=None)
    saved = {name: sys.modules.get(name) for name in ('mods_base', 'unrealsdk', 'unrealsdk.hooks')}
    sys.modules.update({'mods_base': base, 'unrealsdk': sdk_module, 'unrealsdk.hooks': hooks})
    companion_spec = importlib.util.spec_from_file_location(package + '.shift_storage_companion', ROOT / 'shift_storage_companion.py')
    companion = importlib.util.module_from_spec(companion_spec)
    sys.modules[companion_spec.name] = companion
    companion_spec.loader.exec_module(companion)
    for name, value in saved.items():
        if value is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = value
    return companion


companion = _load_companion_for_tests()


class CompanionHandoffTests(unittest.TestCase):
    class Native:
        def __init__(self):
            self.owned = True
            self.visibility = [1, 1, 1]
        def inspect(self):
            return {'visibility': self.visibility[:], 'owned': self.owned}
        def _inspect(self):
            return ((), tuple(self.visibility), 2, True)

    class Controller:
        def __init__(self):
            self.native = CompanionHandoffTests.Native()
            self._thread = threading.get_ident()
            self._lock = threading.RLock()
            self._tick_running = False
            self._closing = False
            self.state = 'idle'
            self.token = None
            self.calls = []
            self.quiescent = False
            self.get_pc = lambda: None
        def _bind(self):
            return None
        def before_close(self):
            return True
        def status(self):
            return {'available': True, 'state': self.state, 'reason': '', 'token': self.token}
        def _owned(self):
            return self.native.owned
        def request(self, payload):
            self.calls.append(dict(payload))
            if payload['mode'] == 'start':
                self.state, self.token, self.quiescent = 'pending', payload['token'], False
            elif payload['mode'] == 'stop' and payload['token'] == self.token:
                self.state, self.token, self.quiescent = 'stopping', None, True
            return {'ok': True, **self.status()}

    def setUp(self):
        companion._background = self.Controller()
        companion._page_command = None
        companion._page_command_error = ''
        companion._background_terminal_token = None
        companion._instance = 'i' * 32
        companion._server = object()
        companion._server_thread = types.SimpleNamespace(is_alive=lambda: True)
        companion._disabling = False
        companion._setup_menu_handoff(m.MenuHandoff, m.MenuSnapshot, m.probe_menu_state, object())

    def queue_auto_start(self):
        command_id = 'c' * 32
        with companion._command_lock:
            companion._page_command = {'id': command_id, 'mode': 'start', 'deadline': 99_999_999}
            companion._menu_resume_command_id = command_id
        first = companion._background_status()['start_token']
        second = companion._background_status()['start_token']
        self.assertEqual(first, second)
        return first

    def test_cancelled_get_start_token_cannot_become_a_late_explicit_start(self):
        self.setUp()
        stale = self.queue_auto_start()
        companion._cancel_menu_resume()
        result = companion._background.request({'mode': 'start', 'token': stale})
        self.assertFalse(result.get('ok'))
        self.assertEqual([], companion._background.calls)
        fresh = 'd' * 32
        result = companion._background.request({'mode': 'start', 'token': fresh})
        self.assertTrue(result.get('ok'))
        self.assertEqual([{'mode': 'start', 'token': fresh}], companion._background.calls)

    def test_page_stop_revokes_accepted_auto_token_before_forgetting_it(self):
        token = self.queue_auto_start()
        controller = companion._background
        self.assertTrue(controller.request({'mode':'start','token':token})['ok'])
        self.assertTrue(controller.request({'mode':'stop','token':token})['ok'])
        controller.state = 'idle'; controller.quiescent = True
        calls = len(controller.calls)
        self.assertFalse(controller.request({'mode':'start','token':token})['ok'])
        self.assertEqual(calls, len(controller.calls))

    def test_status_keeps_native_protocol_state_and_adds_presentation_overlay(self):
        self.setUp()
        companion._background.state = 'active'
        companion._menu_handoff._phase = 'suspended_menu'
        status = companion._background_status()
        self.assertEqual('active', status['state'])
        self.assertEqual('active', status['native_state'])
        self.assertEqual('suspended_menu', status['handoff_state'])

    def test_desktop_overlay_does_not_change_page_protocol(self):
        for phase in ('suspended_menu', 'resuming'):
            companion._background.state = 'idle'
            companion._menu_handoff._phase = phase
            self.assertEqual('idle', companion._background_status()['state'])
            result = companion.background_control('status')['background']
            self.assertEqual(phase, result['state'])
            self.assertEqual('idle', result['native_state'])
        companion._background.state = 'active'
        self.assertEqual('active', companion.background_control('status')['background']['state'])
        companion._background.state = 'error'
        self.assertEqual('error', companion.background_control('status')['background']['state'])

    def test_explicit_start_revokes_old_resume_before_queueing_new_command(self):
        old_token = self.queue_auto_start()
        old_id = companion._page_command['id']
        companion._menu_handoff._phase = 'resuming'
        library = types.SimpleNamespace(IsVisible=lambda: True, Open=lambda _index: None)
        sdk = types.SimpleNamespace(find_class=lambda _name: types.SimpleNamespace(ClassDefaultObject=library))
        with patch.dict(sys.modules, {'unrealsdk': sdk}):
            result = companion.background_control('start')
        self.assertTrue(result['ok'])
        self.assertIsNotNone(companion._page_command)
        self.assertNotEqual(old_id, companion._page_command['id'])
        self.assertEqual('idle', companion._menu_handoff.status()['handoff_state'])
        self.assertFalse(companion._background.request({'mode':'start','token':old_token})['ok'])

    def test_expired_auto_start_token_is_revoked(self):
        token = self.queue_auto_start()
        companion._page_command['deadline'] = -1
        status = companion._background_status()
        self.assertIn('command_error', status)
        self.assertFalse(companion._background.request({'mode':'start','token':token})['ok'])

    def test_native_hook_avoids_cancelling_handoff_under_controller_tick(self):
        self.setUp()
        companion._menu_handoff._phase = 'resuming'
        companion._background._tick_running = True
        self.assertIsNone(companion._before_close())
        self.assertEqual('resuming', companion._menu_handoff.status()['handoff_state'])
        companion._background._tick_running = False
        self.assertIsNone(companion._before_close())
        self.assertEqual('idle', companion._menu_handoff.status()['handoff_state'])

    def test_cancel_racing_accepted_auto_start_stops_only_its_token(self):
        self.setUp()
        token = self.queue_auto_start()
        entered = threading.Event()
        release = threading.Event()
        controller = companion._background
        original = types.MethodType(self.Controller.request, controller)
        def slow_request(payload):
            entered.set()
            release.wait(2)
            return original(payload)
        controller.request = slow_request
        companion._setup_menu_handoff(m.MenuHandoff, m.MenuSnapshot, m.probe_menu_state, object())
        # Re-establish the queued resume after setup resets private ownership.
        token = self.queue_auto_start()
        worker = threading.Thread(target=lambda: controller.request({'mode': 'start', 'token': token}))
        worker.start()
        self.assertTrue(entered.wait(1))
        cancel = threading.Thread(target=companion._cancel_menu_resume)
        cancel.start()
        release.set()
        worker.join(2); cancel.join(2)
        self.assertFalse(worker.is_alive()); self.assertFalse(cancel.is_alive())
        self.assertEqual('stopping', controller.state)
        self.assertEqual([{'mode': 'start', 'token': token}, {'mode': 'stop', 'token': token}], controller.calls)

    def test_failed_native_close_restores_pause_and_cursor_and_does_not_resume(self):
        self.setUp()
        controller = companion._background
        player = object(); pawn = types.SimpleNamespace(Outer=object())
        pc = types.SimpleNamespace(Player=player, Pawn=pawn, bShowMouseCursor=True)
        paused = {'value': True}
        stats = types.SimpleNamespace(
            IsGamePaused=lambda _pc: paused['value'],
            SetGamePaused=lambda _pc, value: paused.__setitem__('value', value))
        context = ProbeTests.Context('menu', '/Game/UI/Input/Context_UI_Menu.Context_UI_Menu')
        subsystem = types.SimpleNamespace(Name='local', Outer=player,
                                          Class=types.SimpleNamespace(_implements=lambda _i: True))
        sdk = types.SimpleNamespace(
            find_class=lambda name: (types.SimpleNamespace(ClassDefaultObject=stats)
                                     if name == 'GameplayStatics' else object()),
            find_object=lambda *_args: object(),
            find_all=lambda name, _exact: [subsystem] if name == 'EnhancedInputLocalPlayerSubsystem' else [context],
            unreal=types.SimpleNamespace(BoundFunction=lambda *_args: lambda _ctx, _priority: (True, 1)))
        controller.get_pc = lambda: pc
        controller.state = 'active'; controller.quiescent = False
        attempts = []
        def fail_after_native_close():
            attempts.append(1)
            paused['value'] = False
            pc.bShowMouseCursor = False
            controller.state = 'stopping' if len(attempts) == 1 else 'idle'
            controller._closing = len(attempts) == 1
            controller.quiescent = len(attempts) > 1
            controller.native.owned = False; controller.native.visibility = [2, 2, 2]
            return len(attempts) > 1
        controller._stop_attempt = fail_after_native_close
        companion._setup_menu_handoff(m.MenuHandoff, m.MenuSnapshot, m.probe_menu_state, sdk)
        # Install the current game-thread SDK/PC provider for the snapshot adapter.
        controller.get_pc = lambda: pc
        companion._menu_handoff.tick()
        self.assertTrue(paused['value'])
        self.assertTrue(pc.bShowMouseCursor)
        self.assertEqual('suspended_menu', companion._menu_handoff.status()['handoff_state'])
        self.assertEqual('close_pending', companion._menu_handoff.status()['handoff_error'])
        self.assertNotIn('resume', [call['mode'] for call in controller.calls])
        # The normal controller retry path also runs through the preservation
        # wrapper, even after ownership was released by the first attempt.
        self.assertTrue(controller._stop_attempt())
        self.assertTrue(paused['value'])
        self.assertTrue(pc.bShowMouseCursor)
        self.assertEqual(2, len(attempts))


    def test_direct_controller_stop_and_retry_preserve_menu(self):
        self.setUp()
        controller = companion._background
        player = object(); pawn = types.SimpleNamespace(Outer=object())
        pc = types.SimpleNamespace(Player=player, Pawn=pawn, bShowMouseCursor=True)
        paused = {'value': True}
        stats = types.SimpleNamespace(
            IsGamePaused=lambda _pc: paused['value'],
            SetGamePaused=lambda _pc, value: paused.__setitem__('value', value))
        context = ProbeTests.Context('menu', '/Game/UI/Input/Context_UI_Menu.Context_UI_Menu')
        subsystem = types.SimpleNamespace(Name='local', Outer=player,
                                          Class=types.SimpleNamespace(_implements=lambda _i: True))
        sdk = types.SimpleNamespace(
            find_class=lambda name: (types.SimpleNamespace(ClassDefaultObject=stats)
                                     if name == 'GameplayStatics' else object()),
            find_object=lambda *_args: object(),
            find_all=lambda name, _exact: [subsystem] if name == 'EnhancedInputLocalPlayerSubsystem' else [context],
            unreal=types.SimpleNamespace(BoundFunction=lambda *_args: lambda _ctx, _priority: (True, 1)))
        controller.get_pc = lambda: pc
        controller.state = 'active'; controller.quiescent = False
        attempts = []
        def fail_after_native_close():
            attempts.append(1)
            paused['value'] = False
            pc.bShowMouseCursor = False
            controller.state = 'stopping' if len(attempts) == 1 else 'idle'
            controller._closing = len(attempts) == 1
            controller.quiescent = len(attempts) > 1
            controller.native.owned = False; controller.native.visibility = [2, 2, 2]
            return len(attempts) > 1
        controller._stop_attempt = fail_after_native_close
        companion._setup_menu_handoff(m.MenuHandoff, m.MenuSnapshot, m.probe_menu_state, sdk)
        # Install the current game-thread SDK/PC provider for the snapshot adapter.
        controller.get_pc = lambda: pc
        self.assertFalse(controller._stop_attempt())
        self.assertTrue(paused['value'])
        self.assertTrue(pc.bShowMouseCursor)
        self.assertEqual('idle', companion._menu_handoff.status()['handoff_state'])
        self.assertNotIn('resume', [call['mode'] for call in controller.calls])
        # The normal controller retry path also runs through the preservation
        # wrapper, even after ownership was released by the first attempt.
        self.assertTrue(controller._stop_attempt())
        self.assertTrue(paused['value'])
        self.assertTrue(pc.bShowMouseCursor)
        self.assertEqual(2, len(attempts))



if __name__ == '__main__':
    unittest.main()
