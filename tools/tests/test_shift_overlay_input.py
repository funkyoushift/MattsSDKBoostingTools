"""Deferred SHiFT cleanup must preserve newer native menu ownership."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

TARGET = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools/shift_overlay.py'

class OverlayInputTests(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.now=100.;self.visible=False;self.context_active=False
        self.pc=types.SimpleNamespace(Player=object(), Pawn=object(), bBlockInput=False)
        self.lib=types.SimpleNamespace(IsVisible=lambda:self.visible,IsInitialized=lambda:True,
            Open=lambda n:self.calls.append(('open',n)),Close=lambda:self.calls.append(('close',)))
        base=types.ModuleType('mods_base');base.get_pc=lambda:self.pc
        base.keybind=lambda *a,**k:types.SimpleNamespace(enable=lambda:None,disable=lambda:None)
        self.sub=types.SimpleNamespace(Name='Local',Outer=self.pc.Player,Class=types.SimpleNamespace(_implements=lambda x:True))
        self.context=types.SimpleNamespace(Name='PauseMenu',_path_name=lambda:'/Game/UI/Input/Context_UI_Menu.Context_UI_Menu')
        sdk=types.ModuleType('unrealsdk');sdk.find_class=lambda *a:object()
        sdk.find_object=lambda kind,*a:types.SimpleNamespace(ClassDefaultObject=self.lib) if kind=='Class' else object()
        sdk.find_all=lambda name,exact:[self.sub] if name=='EnhancedInputLocalPlayerSubsystem' else [self.context]
        sdk.unreal=types.SimpleNamespace(BoundFunction=lambda *a:lambda c,p:(self.context_active,1))
        self.sdk=sdk
        capture=types.ModuleType('overlay_candidate.shift_capture');capture.enable=lambda:{};capture.restore=lambda:None
        package=types.ModuleType('overlay_candidate');package.__path__=[]
        self.quick=types.ModuleType('overlay_candidate.quick_menu');self.quick.STATE=types.SimpleNamespace(is_open=False)
        self.quick._force_game_only_input=lambda:self.calls.append(('release',))
        self.companion=types.ModuleType('ShiftManagement')
        self.companion._background=types.SimpleNamespace(native=types.SimpleNamespace(owned=False),_ownership=False)
        self.modules=patch.dict(sys.modules,{'mods_base':base,'unrealsdk':sdk,'overlay_candidate':package,
            'overlay_candidate.quick_menu':self.quick,'overlay_candidate.shift_capture':capture,'ShiftManagement':self.companion})
        self.modules.start();self.addCleanup(self.modules.stop)
        spec=importlib.util.spec_from_file_location('overlay_candidate.shift_overlay',TARGET)
        self.mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.mod)
        clock=patch.object(self.mod.time,'monotonic',lambda:self.now);clock.start();self.addCleanup(clock.stop)

    def release_count(self):
        return self.calls.count(('release',))

    def test_new_pause_menu_cancels_prior_close_releases(self):
        self.assertTrue(self.mod.control('close')['ok'])
        self.assertEqual(self.release_count(),1)
        self.context_active=True;self.now+=.5;self.mod.tick()
        self.assertEqual(self.release_count(),1,'The newer pause menu must keep its focus')
        self.assertFalse(self.mod._release_at);self.assertIsNone(self.mod._owner)
        self.context_active=False;self.now+=2;self.mod.tick()
        self.assertEqual(self.release_count(),1,'Cancelled old timers must not restart')

    def test_unknown_context_cancels_automatic_restoration(self):
        self.mod.control('close')
        self.sdk.find_all=lambda *a:(_ for _ in ()).throw(RuntimeError('unsupported scan'))
        self.now+=1;self.mod.tick()
        self.assertEqual(self.release_count(),1,'Unreadable UI state must not steal input')
        self.assertFalse(self.mod._release_at)

    def test_ambiguous_local_subsystems_cancel_automatic_restoration(self):
        self.mod.control('close')
        self.sdk.find_all=lambda name,exact:[self.sub,self.sub] if name=='EnhancedInputLocalPlayerSubsystem' else []
        self.now+=1;self.mod.tick();self.assertEqual(self.release_count(),1)

    def test_cursor_only_context_is_not_a_different_menu(self):
        self.context._path_name=lambda:'/Game/UI/Input/Context_UI_Cursor.Context_UI_Cursor'
        self.context_active=True;self.mod.control('close')
        for delta in (.25,.75,1.5):self.now=100+delta;self.mod.tick()
        self.assertEqual(self.release_count(),4)
        self.assertIsNone(self.mod._owner)

    def test_gameplay_releases_retain_existing_bounded_schedule(self):
        self.mod.control('open')
        for delta in (.25,.75,1.5,4,10):self.now=100+delta;self.mod.tick()
        self.assertEqual(self.release_count(),3)

    def test_background_visibility_is_not_misclassified_as_native_close(self):
        self.visible=True;self.mod.control('open');self.mod.tick()
        self.visible=False;self.companion._background.native.owned=True
        self.now+=2;self.mod.tick()
        self.assertEqual(self.release_count(),0,'Companion now owns native presentation and restoration')
        self.assertFalse(self.mod._closing);self.assertFalse(self.mod._release_at)
        self.assertIsNone(self.mod._owner)

    def test_explicit_release_and_quick_menu_guard_unchanged(self):
        self.context_active=True
        self.assertTrue(self.mod.control('release')['ok']);self.assertEqual(self.release_count(),1)
        self.quick.STATE.is_open=True
        self.assertFalse(self.mod.control('release')['ok']);self.assertEqual(self.release_count(),1)

    def test_player_change_cancels_before_mutation(self):
        self.mod.control('open');self.pc=None
        self.now+=1;self.mod.tick();self.assertEqual(self.release_count(),0)
        self.assertIsNone(self.mod._owner)

if __name__=='__main__':unittest.main()
