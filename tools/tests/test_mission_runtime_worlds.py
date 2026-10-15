from mission_profile_fixture import exec_with_profiles
"""World admission must include authored DLC while rejecting menus and stale bindings."""
import importlib.util
import importlib.resources
from pathlib import Path
from types import SimpleNamespace as NS
import sys
import pytest

ROOT=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools'

@pytest.fixture
def runtime(monkeypatch):
    monkeypatch.setattr(importlib.resources,'files',lambda package:ROOT)
    monkeypatch.setitem(sys.modules,'unrealsdk',NS())
    monkeypatch.setitem(sys.modules,'mods_base',NS(ENGINE=NS(),get_pc=lambda:None))
    spec=importlib.util.spec_from_file_location('mission_world_test',ROOT/'mission_runtime.py')
    m=importlib.util.module_from_spec(spec);exec_with_profiles(spec, m, monkeypatch)
    obj=m.MissionRuntime.__new__(m.MissionRuntime);obj.world_address=None
    return m,obj

def bind(m,path,address=100,pc_path=None):
    m.ENGINE.GameViewport=NS(World=NS(_path_name=lambda:path,_get_address=lambda:address))
    m.get_pc=lambda:NS(Pawn=object(),PlayerState=object(),_path_name=lambda:pc_path or path+':PersistentLevel.Player')

@pytest.mark.parametrize('path',[
 '/Game/Maps/WorldLevels/World_P.World_P',
 '/Game/Maps/WorldLevels/Intro/Intro_P.Intro_P',
 '/Game/DLC/Cowbell/Maps/Cowbell_P.Cowbell_P',
 '/Game/DLC/Harmonica/Maps/Harmonica_P.Harmonica_P',
])
def test_authored_gameplay_maps_admitted(runtime,path):
    m,obj=runtime;bind(m,path);obj.ensure_world();assert obj.world_address==100

@pytest.mark.parametrize('path',[
 '/Engine/Transient.World_P',
 '/Game/Maps/MainMenu.MainMenu',
 '/Game/Maps/World_P/_Generated_/Cell.World_P',
 '/Game/Maps/Unknown_P.Unknown_P',
])
def test_menu_transient_sublevel_and_unknown_rejected(runtime,path):
    m,obj=runtime;bind(m,path)
    with pytest.raises(RuntimeError,match='gameplay world left'):obj.ensure_world()
    assert obj.world_address is None

def test_new_world_instance_requires_refresh(runtime):
    m,obj=runtime;path='/Game/DLC/Cowbell/Maps/Cowbell_P.Cowbell_P';bind(m,path)
    obj.ensure_world();bind(m,path,101)
    with pytest.raises(RuntimeError,match='world instance changed'):obj.ensure_world()
    assert obj.world_address==100

def test_controller_from_previous_world_rejected(runtime):
    m,obj=runtime;bind(m,'/Game/DLC/Cowbell/Maps/Cowbell_P.Cowbell_P',pc_path='/Game/Maps/WorldLevels/World_P.World_P:PersistentLevel.Player')
    with pytest.raises(RuntimeError,match='controller belongs to another world'):obj.ensure_world()


def test_lightweight_context_retains_thread_build_and_world_checks(runtime,monkeypatch):
    m,obj=runtime;calls=[];obj.thread=m.threading.get_ident()
    monkeypatch.setattr(obj,'check_build',lambda:calls.append('build'))
    monkeypatch.setattr(obj,'ensure_world',lambda:calls.append('world'))
    obj.validate_context();assert calls==['build','world']
    obj.thread=-1;calls.clear()
    with pytest.raises(RuntimeError,match='game thread'):obj.validate_context()
    assert not calls
