import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace as NS

import pytest

ROOT = Path(__file__).parents[2] / 'mod_extracted/MattsSDKBoostingTools'


@pytest.fixture
def controls(monkeypatch):
    package = ModuleType('dialogue_test'); package.__path__ = [str(ROOT)]
    monkeypatch.setitem(sys.modules, 'dialogue_test', package)
    calls = []
    monkeypatch.setitem(sys.modules, 'dialogue_test.camera_tick', NS(
        register=lambda *a, **k: calls.append(('register', a[0])),
        set_needed=lambda *a: calls.append(('needed', *a))))
    monkeypatch.setitem(sys.modules, 'dialogue_test.travel_gate', NS(is_travel_quiet=lambda: False))
    spec = importlib.util.spec_from_file_location('dialogue_test.dialogue_controls', ROOT / 'dialogue_controls.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    world = NS(_path_name=lambda: 'world', _get_address=lambda: 123)
    pc = NS(Pawn=True, _path_name=lambda: 'world:pc', GetLevel=lambda: NS(OwningWorld=world), HasAuthority=lambda: True)
    monkeypatch.setitem(sys.modules, 'mods_base', NS(get_pc=lambda **kw: pc))
    monkeypatch.setitem(sys.modules, 'unrealsdk', NS(find_all=lambda *a, **k: []))
    monkeypatch.setitem(sys.modules,'dialogue_test.mission_runtime',NS(MissionRuntime=lambda:NS()))
    module.calls = calls; module.pc = pc
    return module


def test_session_default_and_cleanup(controls):
    assert not controls.status()['enabled']
    controls.set_enabled(True); assert controls.status()['enabled']
    controls.clear_runtime_state()
    assert not controls.status()['enabled'] and controls.calls[-1] == ('needed', 'dialogue_skip', False)


def test_uses_shared_pump_and_boolean_validation(controls):
    assert not controls.set_enabled('false')['ok'] and not controls.calls
    controls.set_enabled(True)
    assert controls.calls == [('register', 'dialogue_skip'), ('needed', 'dialogue_skip', True)]


def test_failure_stops_without_retry(controls, monkeypatch):
    calls = []
    def fail(*a, **k):
        calls.append(True); raise RuntimeError('unknown native result')
    monkeypatch.setattr(sys.modules['unrealsdk'], 'find_all', fail)
    controls.set_enabled(True); controls._tick(); controls._next_at = 0.; controls._tick()
    assert len(calls) == 1 and not controls.status()['enabled'] and not controls.status()['ok']


def test_travel_and_clients_never_skip(controls, monkeypatch):
    monkeypatch.setattr(sys.modules['unrealsdk'], 'find_all', lambda *a, **k: pytest.fail('Must not scan dialogue'))
    controls.set_enabled(True)
    monkeypatch.setattr(sys.modules['dialogue_test.travel_gate'], 'is_travel_quiet', lambda: True)
    controls._tick(); assert controls.status()['enabled']
    monkeypatch.setattr(sys.modules['dialogue_test.travel_gate'], 'is_travel_quiet', lambda: False)
    controls.pc.HasAuthority = lambda: False
    controls._next_at = 0.; controls._tick()
    assert not controls.status()['enabled'] and not controls.status()['ok']


def test_normal_native_completion_is_checked_separately_from_audio_stop(controls,monkeypatch):
    state=dict(now=1.,playing=True,calls=0)
    performance=NS(DialogThreadID=7,Performance='native-line',DialogLineRef=NS(LineName='one'),PlayingAudioInstance=object())
    provider=NS(_path_name=lambda:'world:provider',CurrentPerformance=performance)
    def stop(instance,fade):
        assert instance is performance.PlayingAudioInstance and fade==0.
        state['calls']+=1;state['playing']=False
    monkeypatch.setitem(sys.modules,'dialogue_test.mission_progression',NS(_engine=lambda:NS(check_build=lambda:None)))
    def finish(p,engine,thread):
        assert p is provider and thread==7
        stop(performance.PlayingAudioInstance,0.);return True
    monkeypatch.setitem(sys.modules,'dialogue_test.dialogue_native',NS(complete=finish))
    audio=NS(Stop=stop);dialog=NS(IsDialogThreadPlaying=lambda pc,thread:state['playing'])
    monkeypatch.setattr(sys.modules['unrealsdk'],'find_all',lambda *a,**k:[provider])
    monkeypatch.setattr(sys.modules['unrealsdk'],'find_object',lambda cls,path:audio if cls=='GbxAudioBlueprintFunctionLibrary' else dialog,raising=False)
    controls.time=NS(monotonic=lambda:state['now'])
    controls.set_enabled(True);controls._tick();state['now']+=1.;controls._tick()
    assert state['calls']==1 and controls.status()['native_thread_ends']==1 and controls.status()['skip_verified']


def test_map_transitions_do_not_disable_the_dialogue_toggle(controls,monkeypatch):
    engine=NS(ensure_world=lambda:pytest.fail('Dialogue must not use a mission world binding'))
    monkeypatch.setitem(sys.modules,'dialogue_test.mission_runtime',NS(MissionRuntime=lambda:engine))
    monkeypatch.setitem(sys.modules,'dialogue_test.dialogue_native',NS(complete=lambda *a:True))
    monkeypatch.setattr(sys.modules['unrealsdk'],'find_object',lambda *a:NS(IsDialogThreadPlaying=lambda *a:False),raising=False)
    controls.set_enabled(True);controls._tick();assert controls.status()['enabled']
    controls.pc.GetLevel=lambda:NS(OwningWorld=NS(_path_name=lambda:'/Engine/Transient.World',_get_address=lambda:999))
    controls._next_at=0.;controls._tick()
    assert controls.status()['enabled'] and not controls.status()['disabled']
    assert controls._runtime is engine
