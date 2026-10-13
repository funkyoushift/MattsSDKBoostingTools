"""Scene loading must precede outcomes and retain player recovery ownership."""
import importlib.util
import importlib.resources
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace as NS

import pytest

ROOT=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools'


@pytest.fixture
def scene(monkeypatch):
    pkg=ModuleType('completion_placement_test');pkg.__path__=[str(ROOT)]
    monkeypatch.setitem(sys.modules,pkg.__name__,pkg)
    spec=importlib.util.spec_from_file_location(pkg.__name__+'.mission_completion_placement',ROOT/'mission_completion_placement.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    events=[];calls=[]
    owner=NS(_job=dict(state='running',phase='complete',completion_context={}),
             _journal=events.append,_party=lambda:['Host','Guest'])
    native=NS(active=None)
    def start(child,rows,journal):
        calls.append(('start',rows));native.active=child
        child.update(phase='placement',placement=[dict(held=True)])
        journal(dict(event='placement_started'))
    def cancel(reason,state):
        if native.active is None:return False
        calls.append(('cancel',state));return True
    def retry(child,journal):
        if not any(r.get('held') for r in child.get('placement',[])):return False
        child.update(state='running',phase='placement');native.active=child
        calls.append(('retry',));return True
    monkeypatch.setitem(sys.modules,pkg.__name__+'.mission_practice_placement',
                        NS(start=start,tick=lambda:None,cancel=cancel,retry_cleanup=retry))
    objective=dict(token='one',group=0,completion_anchor=dict(map='World_P',location=dict(x=1,y=2,z=3)))
    return NS(m=m,owner=owner,calls=calls,events=events,native=native,objective=objective)


def test_scene_must_finish_and_restore_movement_before_outcome(scene):
    s=scene
    assert not s.m.ready(s.owner,'Mission',s.objective)
    assert not s.m.ready(s.owner,'Mission',s.objective)
    assert not s.m.observe(s.owner)
    child=s.native.active;child['phase']='world_ready'
    assert not s.m.observe(s.owner)  # A success phase cannot excuse held movement.
    child['placement'][0]['held']=False
    assert s.m.observe(s.owner)
    assert s.m.ready(s.owner,'Mission',s.objective)
    assert s.calls==[('start',['Host','Guest'])]
    assert s.owner._job['phase']=='complete'
    assert s.events[-1]['event']=='completion_placement_verified'


def test_authored_scene_fallback_loads_without_a_completion_anchor(scene):
    s=scene
    anchor=s.objective.pop('completion_anchor')
    s.objective['scene_anchor']=anchor
    assert not s.m.ready(s.owner,'Mission',s.objective)
    assert s.native.active['anchor']==anchor
    s.native.active.update(phase='world_ready',placement=[])
    assert s.m.observe(s.owner)
    assert s.m.ready(s.owner,'Mission',s.objective)


def test_loaded_encounter_in_range_preserves_players_current_standing_position(scene,monkeypatch):
    s=scene;s.objective['encounter_scene']={'actor':{'map':'World_P'}}
    monkeypatch.setattr(s.m,'_encounter_ready',lambda *a:True)
    assert s.m.ready(s.owner,'Mission',s.objective)
    assert not s.calls and s.events[-1]['event']=='completion_scene_loaded'


def test_encounter_stages_at_authored_entry_then_waits_for_actual_scene(scene,monkeypatch):
    s=scene;s.objective['encounter_scene']={'actor':{'map':'World_P'}}
    entry=dict(map='World_P',location=dict(x=5,y=6,z=7));s.objective['scene_anchor']=entry
    loaded=[False];monkeypatch.setattr(s.m,'_encounter_ready',lambda *a:loaded[0])
    assert not s.m.ready(s.owner,'Mission',s.objective)
    assert s.native.active['anchor']==entry
    assert 'navigation_scene' not in s.native.active
    s.native.active.update(phase='world_ready',placement=[]);assert s.m.observe(s.owner)
    assert not s.m.ready(s.owner,'Mission',s.objective)
    loaded[0]=True;assert s.m.ready(s.owner,'Mission',s.objective)
    assert len(s.calls)==1


@pytest.mark.parametrize('fault',['none','unloaded','outside','nonfinite','ambiguous_layer','foreign_map'])
def test_native_navigation_requires_real_projection_within_encounter_boundary(scene,monkeypatch,fault):
    s=scene;w=NS();layer=NS(_get_address=lambda:10)
    scene_data=dict(actor=dict(map='World_P'),radius=100.,center=dict(x=0.,y=0.,z=0.))
    encounter=NS(SpawnerActivation=NS(Radius=200.))
    monkeypatch.setattr(s.m,'_encounter',lambda *a:encounter)
    layers=[NS(DefaultNavMeshLayer=layer)]
    if fault=='ambiguous_layer':layers.append(NS(DefaultNavMeshLayer=NS(_get_address=lambda:20)))
    point=NS(X=float('nan') if fault=='nonfinite' else 250. if fault=='outside' else 150.,Y=0.,Z=0.)
    lib=NS(MakeGbxNavQueryData=lambda *a:NS(),ProjectToNavMesh=lambda *a:(fault!='unloaded',point))
    monkeypatch.setitem(sys.modules,'unrealsdk',NS(find_all=lambda *a,**kw:layers,
        find_object=lambda *a:lib,make_struct=lambda n,**kw:NS(**kw)))
    monkeypatch.setitem(sys.modules,'completion_placement_test.mission_completion_context',
        NS(world=lambda:w,map_name=lambda w:'other' if fault=='foreign_map' else 'world_p'))
    assert s.m.navigation_point(NS(),scene_data)==(dict(X=150.,Y=0.,Z=0.) if fault=='none' else None)


@pytest.mark.parametrize('fault',['none','streamed','far_guest','old_world','wrong_group','destroying','ambiguous','airborne'])
def test_loaded_interactive_scene_preserves_safe_position_only_for_exact_nearby_target(scene,monkeypatch,fault):
    s=scene;w=NS(_get_address=lambda:100)
    actor=NS(GetLevel=lambda:NS(OwningWorld=NS(_get_address=lambda:200 if fault=='old_world' else 100)),
        _path_name=lambda:'/Game/Test/_Generated_/Cell.Test:Console' if fault=='streamed' else '/Game/Test.Test:Console',
        FactsConduit=NS(RegistryName=NS(Name=NS(Name='Console')),GroupName=NS(Name='Other' if fault=='wrong_group' else 'Mission')),
        IsActorBeingDestroyed=lambda:fault=='destroying',K2_GetActorLocation=lambda:NS(X=0.,Y=0.,Z=0.))
    monkeypatch.setitem(sys.modules,'unrealsdk',NS(find_all=lambda *a,**kw:[actor,actor] if fault=='ambiguous' else [actor]))
    monkeypatch.setitem(sys.modules,'completion_placement_test.mission_completion_context',NS(world=lambda:w,map_name=lambda w:'test'))
    monkeypatch.setitem(sys.modules,'completion_placement_test.mission_practice_placement',NS(players_grounded=lambda rows:fault!='airborne'))
    s.owner._party=lambda:[dict(pc=NS(Pawn=NS(K2_GetActorLocation=lambda:NS(X=5100. if fault=='far_guest' else 2000.,Y=0.,Z=0.))))]
    anchor=dict(map='Test',actor='registry.test.top.mission.console.__nochannel')
    if fault=='ambiguous':
        with pytest.raises(RuntimeError,match='ambiguous'):s.m._object_scene_ready(s.owner,anchor)
    else:assert s.m._object_scene_ready(s.owner,anchor)==(fault in ('none','streamed'))


@pytest.mark.parametrize('change',['none','streamed','other_world','other_group','other_actor','ambiguous','far_guest','airborne','nonfinite'])
def test_encounter_readiness_validates_actor_and_every_player(scene,monkeypatch,change):
    s=scene;path='/Game/World_P.World_P';w=NS(_path_name=lambda:path,_get_address=lambda:100)
    identity=dict(map='World_P',groupname='Mission',registryname='Encounter')
    scene_data=dict(actor=identity,radius=100.,center=dict(x=0.,y=0.,z=0.))
    def actor(prefix=path,group='Mission',name='Encounter'):
        return NS(_path_name=lambda:prefix+':PersistentLevel.Actor',
            GetLevel=lambda:NS(OwningWorld=NS(_get_address=lambda:200 if prefix=='/Game/Old.Old' else 100)),
            IsEncounterEnabled=lambda:False,FactsConduit=NS(
            RegistryName=NS(Name=NS(Name=name)),GroupName=NS(Name=group)))
    actors=[actor()]
    if change=='streamed':actors=[actor(prefix='/Game/World_P/_Generated_/Cell.World_P')]
    if change=='other_world':actors=[actor(prefix='/Game/Old.Old')]
    if change=='other_group':actors=[actor(group='Other')]
    if change=='other_actor':actors=[actor(name='Other')]
    if change=='ambiguous':actors*=2
    x=200. if change=='far_guest' else float('nan') if change=='nonfinite' else 0.
    rows=[dict(pc=NS(Pawn=NS(K2_GetActorLocation=lambda:NS(X=x,Y=0.,Z=0.))))]
    s.owner._party=lambda:rows
    monkeypatch.setitem(sys.modules,'unrealsdk',NS(find_all=lambda *a,**k:actors))
    monkeypatch.setitem(sys.modules,'completion_placement_test.mission_completion_context',NS(world=lambda:w,map_name=lambda w:'world_p'))
    monkeypatch.setitem(sys.modules,'completion_placement_test.mission_practice_placement',NS(players_grounded=lambda rows:change!='airborne'))
    if change=='ambiguous':
        with pytest.raises(RuntimeError,match='ambiguous'):s.m._encounter_ready(s.owner,scene_data)
    else:assert s.m._encounter_ready(s.owner,scene_data)==(change in ('none','streamed'))


@pytest.mark.parametrize('change',['none','disabled','empty','old_spawner','old_actor','destroying','airborne'])
def test_spawned_encounter_does_not_need_unsafe_marker_teleport(scene,monkeypatch,change):
    s=scene;path='/Game/World_P.World_P';w=NS(_path_name=lambda:path,_get_address=lambda:100)
    identity=dict(map='World_P',groupname='Mission',registryname='Encounter')
    enemy=NS(_path_name=lambda:('/Game/Old.Old' if change=='old_actor' else path)+':Enemy',
             GetLevel=lambda:NS(OwningWorld=NS(_get_address=lambda:200 if change=='old_actor' else 100)),
             IsActorBeingDestroyed=lambda:change=='destroying')
    spawner=NS(_path_name=lambda:('/Game/Old.Old' if change=='old_spawner' else path)+':Spawner.Component',
               GetOwner=lambda:NS(GetLevel=lambda:NS(OwningWorld=NS(_get_address=lambda:200 if change=='old_spawner' else 100))),
               GetAliveActors=lambda *a:[] if change=='empty' else [enemy])
    encounter=NS(_path_name=lambda:path+':Encounter',IsEncounterEnabled=lambda:change!='disabled',
                 GetLevel=lambda:NS(OwningWorld=w),
                 SpawnerComponents=[spawner],FactsConduit=NS(RegistryName=NS(Name=NS(Name='Encounter')),
                                                          GroupName=NS(Name='Mission')))
    s.owner._party=lambda:[dict(pc=NS(Pawn=NS(K2_GetActorLocation=lambda:NS(X=1000.,Y=0.,Z=0.))))]
    monkeypatch.setitem(sys.modules,'unrealsdk',NS(find_all=lambda *a,**k:[encounter]))
    monkeypatch.setitem(sys.modules,'completion_placement_test.mission_completion_context',NS(world=lambda:w,map_name=lambda w:'world_p'))
    monkeypatch.setitem(sys.modules,'completion_placement_test.mission_practice_placement',NS(players_grounded=lambda rows:change!='airborne'))
    assert s.m._encounter_ready(s.owner,dict(actor=identity,radius=100.,center=dict(x=0.,y=0.,z=0.)))==(change=='none')


@pytest.mark.parametrize('change',[dict(completion_anchor=None),dict(travel_map='other'),dict(finish_actions_pending=True)])
def test_unresolved_travel_and_sibling_scenes_are_not_relocated(scene,change):
    s=scene;s.objective.update(change)
    assert s.m.ready(s.owner,'Mission',s.objective)
    assert not s.calls and not s.events


def test_cancel_waits_for_owned_movement_restoration(scene):
    s=scene;s.m.ready(s.owner,'Mission',s.objective)
    assert s.m.stop(s.owner)
    assert s.owner._job['state']=='running'
    assert not s.m.observe(s.owner)
    child=s.native.active;child['state']='cancelled';child['placement'][0]['held']=False
    s.native.active=None
    assert not s.m.observe(s.owner)
    assert s.owner._job['state']=='cancelled'
    assert s.events[-1]['state']=='cancelled'
    assert sum(c[0]=='start' for c in s.calls)==1


def test_stopped_polling_cannot_lose_cleanup_receipt(scene):
    s=scene;s.m.ready(s.owner,'Mission',s.objective)
    child=s.native.active;child.update(state='uncertain',message='Floor did not load')
    s.native.active=None
    with pytest.raises(RuntimeError,match='Floor did not load'):s.m.observe(s.owner)
    assert s.m.stop(s.owner,state='stopped')
    assert s.owner._job['state']=='uncertain'
    assert s.calls==[('start',['Host','Guest'])]
    # Repeated status/exception handling is not permission to retry an
    # uncertain origin return. Only a new explicit Stop request permits it.
    assert s.m.stop(s.owner,state='stopped')
    assert len(s.calls)==1
    assert s.m.stop(s.owner,retry=True)
    assert s.calls[-1]==('retry',)
    assert s.owner._job['completion_context']['placement'] is child
    assert sum(c[0]=='start' for c in s.calls)==1


def test_next_objective_stages_separately_after_previous_scene_settles(scene):
    s=scene;s.m.ready(s.owner,'Mission',s.objective)
    s.native.active.update(phase='world_ready',placement=[])
    assert s.m.observe(s.owner)
    assert not s.m.ready(s.owner,'Mission',dict(s.objective,token='two'))
    assert len(s.calls)==2


@pytest.mark.parametrize('module_name',['mission_progression','mission_practice'])
def test_coordinator_poll_does_not_rearm_failed_cleanup(scene,monkeypatch,module_name):
    s=scene;s.m.ready(s.owner,'Mission',s.objective)
    child=s.native.active;child.update(state='uncertain',message='Floor did not load')
    s.native.active=None
    monkeypatch.setattr(importlib.resources,'files',lambda package:ROOT)
    package='completion_placement_test'
    monkeypatch.setitem(sys.modules,package+'.mission_completion_placement',s.m)
    spec=importlib.util.spec_from_file_location(package+'.'+module_name,ROOT/(module_name+'.py'))
    m=importlib.util.module_from_spec(spec);monkeypatch.setitem(sys.modules,spec.name,m);spec.loader.exec_module(m)
    m._job=s.owner._job;m._job.update(id='job',index=0,issued=[],started=0,completion_path='objective_graph')
    monkeypatch.setattr(m,'status',lambda:dict(m._job))
    if module_name=='mission_progression':
        monkeypatch.setattr(m,'_journal',s.events.append)
        monkeypatch.setitem(sys.modules,package+'.mission_completion_context',NS(observe=s.m.observe))
        poll=lambda:m.poll('job')
        cancel=lambda:m.cancel('job')
    else:
        m._job['started']=m.time.time()
        monkeypatch.setattr(m,'_save',lambda event=None:s.events.append(event))
        monkeypatch.setattr(m,'_step',lambda:s.m.observe(m._CompletionOwner()))
        poll=lambda:m.step({'job_id':'job'})
        cancel=lambda:m.dispatch('mission_practice_cancel',{'job_id':'job'})
    assert poll()['state']=='uncertain'
    assert poll()['state']=='uncertain'
    assert s.calls==[('start',['Host','Guest'])]
    assert cancel()['state']=='running'
    assert s.calls[-1]==('retry',)
