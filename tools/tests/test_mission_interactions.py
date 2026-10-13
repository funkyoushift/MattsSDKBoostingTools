"""Talk automation resolves the authored NPC, never a nearby name guess."""
import importlib.util
import sys
from pathlib import Path
from types import ModuleType,SimpleNamespace as NS

import pytest

ROOT=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools'


@pytest.fixture
def scene(monkeypatch):
    pkg=ModuleType('interaction_test');pkg.__path__=[str(ROOT)]
    monkeypatch.setitem(sys.modules,pkg.__name__,pkg)
    spec=importlib.util.spec_from_file_location(pkg.__name__+'.mission_interactions',ROOT/'mission_interactions.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    prefix='/Game/Test.Test:'
    world=NS(_path_name=lambda:'/Game/Test.Test',_get_address=lambda:1)
    old_world=NS(_get_address=lambda:2)
    def actor(name='NPC',group='None',path=prefix+'Character',owner=None,destroying=False):
        owner=owner or (old_world if path.startswith('/Game/Old.') else world)
        return NS(_path_name=lambda:path,FactsConduit=NS(RegistryName=NS(Name=NS(Name=name)),GroupName=NS(Name=group)),
                  GetLevel=lambda:NS(OwningWorld=owner),IsActorBeingDestroyed=lambda:destroying,
                  UsableActorState=NS(bInteractabilityLockedReplicated=False))
    target=actor();actors=[actor('Other'),actor(path='/Game/Old.Old:Character'),target];calls=[]
    pc=NS(_path_name=lambda:prefix+'PC',Pawn=object(),ClientCanUseObjectsLock=NS(bLocked=False),
          ServerUseObject=lambda **kwargs:calls.append(kwargs))
    monkeypatch.setitem(sys.modules,'mods_base',NS(get_pc=lambda:pc))
    monkeypatch.setitem(sys.modules,'unrealsdk',NS(find_all=lambda *args,**kwargs:actors))
    monkeypatch.setitem(sys.modules,pkg.__name__+'.mission_completion_context',
                        NS(world=lambda:world,map_name=lambda w:'test'))
    obj=dict(interaction=dict(kind='talk',actor=dict(registryname='NPC')))
    return NS(m=m,obj=obj,actors=actors,target=target,pc=pc,calls=calls,actor=actor,world=world,old_world=old_world)


def test_normal_primary_use_targets_exact_current_world_registry_actor(scene):
    s=scene;operation=s.m.prepare(s.obj)
    assert callable(operation) and not s.calls
    operation()
    assert s.calls==[dict(Usable=s.target,UseType=0,bWasHeld=False)]


@pytest.mark.parametrize('missing',['unloaded','locked_npc','locked_player','map','group'])
def test_unavailable_interaction_waits_without_using_something_else(scene,missing):
    s=scene
    if missing=='unloaded':s.actors.remove(s.target)
    if missing=='locked_npc':s.target.UsableActorState.bInteractabilityLockedReplicated=True
    if missing=='locked_player':s.pc.ClientCanUseObjectsLock.bLocked=True
    if missing=='map':s.obj['interaction']['actor']['map']='other'
    if missing=='group':s.obj['interaction']['actor']['groupname']='Different'
    assert s.m.prepare(s.obj) is False and not s.calls


def test_ambiguous_or_unresolved_npc_never_uses_an_arbitrary_actor(scene):
    s=scene;s.actors.append(s.actor())
    with pytest.raises(RuntimeError,match='ambiguous'):s.m.prepare(s.obj)
    s.obj['interaction']['actor']=None
    with pytest.raises(RuntimeError,match='unresolved'):s.m.prepare(s.obj)
    assert not s.calls


def test_streamed_npc_uses_native_level_world_and_ignores_old_or_destroying_matches(scene):
    s=scene
    target=s.actor(path='/Game/Test/_Generated_/Partition.Test:Character')
    s.actors[:]=[s.actor(owner=s.old_world),s.actor(destroying=True),target]
    operation=s.m.prepare(s.obj)
    assert callable(operation)
    operation()
    assert s.calls==[dict(Usable=target,UseType=0,bWasHeld=False)]
