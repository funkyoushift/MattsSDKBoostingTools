"""Direct SHiFT routing and bounded focus restoration."""
import importlib.util
import sys
import types
from pathlib import Path


def setup_overlay(monkeypatch):
    calls=[]; now=[100.0]; pc=types.SimpleNamespace(bBlockInput=False)
    lib=types.SimpleNamespace(IsVisible=lambda:False,IsInitialized=lambda:True,
        Open=lambda n:calls.append(('open',n)),Close=lambda:calls.append(('close',)))
    base=types.ModuleType('mods_base');base.get_pc=lambda:pc
    base.keybind=lambda *a,**k:types.SimpleNamespace(enable=lambda:None,disable=lambda:None)
    sdk=types.ModuleType('unrealsdk');sdk.find_object=lambda *a:types.SimpleNamespace(ClassDefaultObject=lib)
    capture=types.ModuleType('overlay_test.shift_capture');capture.enable=lambda:{'capture_affinity':0};capture.restore=lambda:None
    monkeypatch.setitem(sys.modules,'overlay_test.shift_capture',capture)
    pkg=types.ModuleType('overlay_test');pkg.__path__=[]
    quick=types.ModuleType('overlay_test.quick_menu');quick.STATE=types.SimpleNamespace(is_open=False)
    quick._force_game_only_input=lambda:calls.append(('release',))
    for name,obj in [('mods_base',base),('unrealsdk',sdk),('overlay_test',pkg),('overlay_test.quick_menu',quick)]:
        monkeypatch.setitem(sys.modules,name,obj)
    path=Path(__file__).resolve().parents[2]/'mod_extracted/MattsSDKBoostingTools/shift_overlay.py'
    spec=importlib.util.spec_from_file_location('overlay_test.shift_overlay',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    monkeypatch.setattr(mod.time,'monotonic',lambda:now[0])
    return mod,calls,now,quick,base


def test_direct_open_releases_input_only_during_startup(monkeypatch):
    m,calls,now,_,_=setup_overlay(monkeypatch)
    assert m.control('open')['ok'];assert calls==[('open',0)]
    for delta in (.25,.75,1.5,3,4):
        now[0]=100+delta;m.tick()
    assert calls==[('open',0)]+[('release',)]*3
    assert m.control('close')['ok'];assert calls[-2:]==[('close',),('release',)]


def test_quick_menu_and_travel_cancel_input_changes(monkeypatch):
    m,calls,now,q,base=setup_overlay(monkeypatch)
    q.STATE.is_open=True
    assert not m.control('open')['ok'];assert calls==[]
    q.STATE.is_open=False;m.control('open')
    base.get_pc=lambda:None
    m.get_pc=base.get_pc
    now[0]+=2;m.tick()
    assert calls==[('open',0)]


def test_capture_restore_failure_cannot_trap_menu_or_bindings(monkeypatch):
    m,calls,_,_,_=setup_overlay(monkeypatch)
    def fail():
        raise OSError('capture restoration failed')
    monkeypatch.setattr(sys.modules['overlay_test.shift_capture'],'restore',fail)
    m.control('open');m.tick()
    assert m.control('close')['ok']
    assert calls[-2:]==[('close',),('release',)]
    assert m._owner is not None and m._release_at
    m.stop()
    assert not m._bindings


def test_travel_clears_owner_after_startup_releases_finished(monkeypatch):
    m,calls,now,_,_=setup_overlay(monkeypatch)
    m.control('open')
    for delta in (.25,.75,1.5):
        now[0]=100+delta;m.tick()
    monkeypatch.setattr(m,'get_pc',lambda:None)
    now[0]+=5;m.tick()
    assert m._owner is None and not m._release_at


def test_close_releases_again_after_native_shutdown_then_stops(monkeypatch):
    m,calls,now,_,_=setup_overlay(monkeypatch)
    assert m.control('close')['ok']
    for delta in (.25,.75,1.5,3,4):
        now[0]=100+delta; m.tick()
    assert calls == [('close',)] + [('release',)] * 4
    assert m._owner is None and not m._release_at


def test_native_back_close_restores_input(monkeypatch):
    m,calls,now,_,_=setup_overlay(monkeypatch)
    visible=[True]; m.library().IsVisible=lambda:visible[0]
    m.control('open'); m.tick()
    visible[0]=False; now[0]+=2; m.tick()
    assert calls[-1] == ('release',) and m._closing
    for delta in (.25,.75,1.5):
        now[0]=102+delta; m.tick()
    assert m._owner is None


def test_delayed_close_does_not_steal_quick_menu_focus(monkeypatch):
    m,calls,now,q,_=setup_overlay(monkeypatch)
    m.control('close'); q.STATE.is_open=True
    now[0]+=1; m.tick()
    assert calls == [('close',),('release',)]
    assert not m._release_at and m._owner is None
