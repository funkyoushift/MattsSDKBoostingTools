"""Travel never repeats issued outcomes, loses the selected guest or uses old pointers."""
import copy
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace as NS,ModuleType
import pytest

ROOT=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools'

@pytest.fixture
def scene(monkeypatch):
    pkg=ModuleType('completion_context_test');pkg.__path__=[str(ROOT)]
    monkeypatch.setitem(sys.modules,pkg.__name__,pkg)
    spec=importlib.util.spec_from_file_location(pkg.__name__+'.mission_completion_context',ROOT/'mission_completion_context.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    clock=NS(now=10.)
    monkeypatch.setattr(m.time,'monotonic',lambda:clock.now)
    def world(name,address):return NS(_path_name=lambda:'/Game/'+name+'.'+name,_get_address=lambda:address)
    state=NS(world=world('World_P',1),grounded=True)
    monkeypatch.setattr(m,'world',lambda:state.world)
    def party(prefix):
        return [dict(label=label,host=host,state=NS(PlayerId=i),pc=NS(_path_name=lambda i=i:prefix+':PC'+str(i),
                     Pawn=NS(_path_name=lambda i=i:prefix+':Pawn'+str(i))))
                for i,label,host in [(1,'Host',True),(2,'Guest',False)]]
    rows=party(state.world._path_name())
    binding=lambda rs:[r['pc']._path_name() for r in rs]
    mission=dict(token='original',state='active')
    events=[];calls=[];reads=[]
    engine=NS(world_address=1,ensure_world=lambda:reads.append('new-world-only'),snapshot=lambda:{})
    receipt=dict(token='original',issued=['settled'],pending='unconfirmed')
    owner=NS(_runtime=engine,_party=lambda:rows,_binding=binding,_row=lambda snap,name:mission,_state=lambda row:row['state'],
             _journal=events.append,_job=dict(completion_path='objective_graph',binding=binding(rows),target=rows[1]['pc']._path_name(),
                    state='running',message='test',objective_runs={'Mission':receipt}))
    owner._job['completion_context']=m.begin(rows,owner._job['target'])
    monkeypatch.setitem(sys.modules,'mods_base',NS(get_pc=lambda:rows[0]['pc']))
    monkeypatch.setitem(sys.modules,pkg.__name__+'.mission_practice_placement',NS(players_grounded=lambda rs:state.grounded))
    monkeypatch.setitem(sys.modules,pkg.__name__+'.travel',NS(travel_to_map=lambda dest,before_issue:(before_issue(),calls.append(dest))))
    owner.status=lambda:dict(owner._job)
    definition=dict(title='Mission',execution_map='harmonica_p',successor_maps=['harmonica_p'])
    def arrive(name='Harmonica_P'):
        state.world=world(name,2);rows[:]=party(state.world._path_name());clock.now+=1
    return NS(m=m,owner=owner,rows=rows,mission=mission,clock=clock,state=state,arrive=arrive,
              definition=definition,calls=calls,events=events,reads=reads,receipt=receipt)

@pytest.mark.parametrize('path',['objective_graph','mission_replay'])
def test_authored_travel_issues_once_then_rebinds_same_selected_guest(scene,path):
    s=scene;original=s.owner._runtime
    s.owner._job['completion_path']=path
    assert not s.m.prepare(s.owner,'Mission',s.mission,s.definition)
    assert s.calls==['harmonica_p']
    for _ in range(3):assert not s.m.observe(s.owner)
    assert s.calls==['harmonica_p'] and not s.reads
    s.arrive();s.state.grounded=False
    assert not s.m.observe(s.owner) and not s.reads
    s.state.grounded=True;assert not s.m.observe(s.owner)
    s.clock.now+=.6;assert s.m.observe(s.owner)
    assert s.owner._runtime is not original and original.world_address==1
    assert s.owner._job['target'].endswith(':PC2')
    assert s.owner._job['objective_runs']['Mission'] is s.receipt
    assert s.receipt['pending']=='unconfirmed' and s.receipt['issued']==['settled']
    assert s.calls==['harmonica_p']

@pytest.mark.parametrize('failure',['map','player','token','unfinished'])
def test_automatic_map_change_requires_authored_successor_and_finished_identity(scene,failure):
    s=scene;s.m.expect_finish(s.owner,'Mission',s.mission,s.definition)
    s.mission['state']='completed';s.arrive('Cowbell_P' if failure=='map' else 'Harmonica_P')
    if failure=='player':s.rows[1]['label']='Different guest'
    if failure=='token':s.mission['token']='replacement'
    if failure=='unfinished':s.mission['state']='active'
    with pytest.raises(RuntimeError):
        if not s.m.observe(s.owner):s.clock.now+=.6;s.m.observe(s.owner)
    assert not s.calls and s.owner._runtime.world_address==1
    assert s.owner._job['target']=='/Game/World_P.World_P:PC2'

def test_natural_completed_transition_does_not_repeat_objectives(scene):
    s=scene;s.m.expect_finish(s.owner,'Mission',s.mission,s.definition)
    s.mission['state']='completed';s.arrive()
    assert not s.m.observe(s.owner)
    s.clock.now+=.6;assert s.m.observe(s.owner)
    assert not s.calls and s.receipt['issued']==['settled']


@pytest.mark.parametrize('fault',['none','pending','unfinished','missing','old_arrival','inactive_arrival','foreign_work'])
def test_native_midmission_arrival_requires_settled_issued_work_and_new_map_objective(scene,monkeypatch,fault):
    s=scene;s.receipt.pop('pending',None)
    if fault=='pending':s.receipt['pending']='settled'
    rows=[dict(token='settled',state=10 if fault=='unfinished' else 13,group=2),
          dict(token='arrival',state=4 if fault=='inactive_arrival' else 13,group=1 if fault=='old_arrival' else 3,travel_map='harmonica_p'),
          dict(token='talk',state=4,group=4,completion_maps=['other' if fault=='foreign_work' else 'harmonica_p'])]
    if fault=='missing':rows.pop(0)
    monkeypatch.setitem(sys.modules,'completion_context_test.mission_execution',NS(DATA={'Mission':{}},objectives=lambda *a:rows))
    # Use a nonempty definition, as unresolved catalog coverage must stay blocked.
    sys.modules['completion_context_test.mission_execution'].DATA['Mission']={'groups':[]}
    s.definition['groups']=[dict(objectives=[dict(travel_map='harmonica_p')])]
    s.m.expect_finish(s.owner,'Mission',s.mission,s.definition)
    s.arrive();assert not s.m.observe(s.owner)
    s.clock.now+=.6
    assert s.m.observe(s.owner)==(fault=='none')
    assert not s.calls and s.receipt['issued']==['settled']
    assert s.owner._job['completion_context']['world']==(2 if fault=='none' else 1)

def test_unknown_travel_outcome_stays_uncertain(scene,monkeypatch):
    s=scene
    def fail(dest,before_issue):
        before_issue()
        raise RuntimeError('Connection failed after request')
    monkeypatch.setitem(sys.modules,'completion_context_test.travel',NS(travel_to_map=fail))
    with pytest.raises(RuntimeError):s.m.prepare(s.owner,'Mission',s.mission,s.definition)
    assert s.owner._job['state']=='uncertain'
    assert s.owner._job['completion_context']['travel']
    assert [e['event'] for e in s.events]==['completion_map_issued']

@pytest.mark.parametrize('arrival_state',[10,11,12])
def test_long_native_arrival_waits_without_rebinding_until_finish_settles(scene,monkeypatch,arrival_state):
    s=scene;s.receipt.pop('pending');rows=[dict(token='settled',state=13,group=2),
        dict(token='arrival',state=arrival_state,group=3,travel_map='harmonica_p'),
        dict(token='talk',state=None,group=4,completion_maps=['harmonica_p'])]
    monkeypatch.setitem(sys.modules,'completion_context_test.mission_execution',
                        NS(DATA={'Mission':{'groups':[]}},objectives=lambda *a:rows))
    s.definition['groups']=[dict(objectives=[dict(travel_map='harmonica_p')])]
    s.m.expect_finish(s.owner,'Mission',s.mission,s.definition)
    s.arrive();assert not s.m.observe(s.owner)
    s.clock.now+=.6;assert not s.m.observe(s.owner)
    s.clock.now+=1500.;assert not s.m.observe(s.owner)
    assert s.owner._job['completion_context']['world']==1 and not s.calls
    assert s.receipt['issued']==['settled']
    rows[1]['state']=13
    assert not s.m.observe(s.owner)  # Destination work can activate later.
    s.clock.now+=1.;s.state.grounded=False
    assert not s.m.observe(s.owner)
    s.state.grounded=True;assert not s.m.observe(s.owner)
    s.clock.now+=.6;rows[2]['state']=4
    assert s.m.observe(s.owner)
    assert s.owner._job['completion_context']['world']==2
    assert 'arrival_wait_since' not in s.owner._job['completion_context']
    assert 'arrival_settle_since' not in s.owner._job['completion_context']


@pytest.mark.parametrize('fault',['timeout','missing_issued','pending','old_group','wrong_map','not_finishing'])
def test_long_arrival_wait_requires_verified_native_finish_state_and_stays_bounded(scene,monkeypatch,fault):
    s=scene;s.receipt.pop('pending');rows=[dict(token='settled',state=13,group=2),
        dict(token='arrival',state=4 if fault=='not_finishing' else 11,group=1 if fault=='old_group' else 3,
             travel_map='other_p' if fault=='wrong_map' else 'harmonica_p')]
    if fault=='missing_issued':rows.pop(0)
    if fault=='pending':s.receipt['pending']='settled'
    monkeypatch.setitem(sys.modules,'completion_context_test.mission_execution',
                        NS(DATA={'Mission':{'groups':[]}},objectives=lambda *a:rows))
    s.definition['groups']=[dict(objectives=[dict(travel_map='harmonica_p')])]
    s.m.expect_finish(s.owner,'Mission',s.mission,s.definition)
    s.arrive();assert not s.m.observe(s.owner)
    s.clock.now+=.6;assert not s.m.observe(s.owner)
    s.clock.now+=s.m.ARRIVAL_FINISH_TIMEOUT+1 if fault=='timeout' else 361.
    with pytest.raises(RuntimeError,match='did not settle'):s.m.observe(s.owner)
    assert not s.calls and s.owner._job['completion_context']['world']==1


def test_loading_timeout_never_reissues_travel(scene):
    s=scene;s.m.prepare(s.owner,'Mission',s.mission,s.definition)
    s.clock.now+=361
    with pytest.raises(RuntimeError,match='did not settle'):s.m.observe(s.owner)
    assert s.calls==['harmonica_p']


def test_rejected_travel_has_no_pending_or_issued_request(scene,monkeypatch):
    s=scene
    def fail(dest,before_issue):raise RuntimeError('Temporary control cleanup failed')
    monkeypatch.setitem(sys.modules,'completion_context_test.travel',NS(travel_to_map=fail))
    with pytest.raises(RuntimeError):s.m.prepare(s.owner,'Mission',s.mission,s.definition)
    assert not s.owner._job['completion_context'].get('travel')
    assert not s.events and not s.calls and s.owner._job['state']=='running'


@pytest.mark.parametrize('mode',['inspect','continue','close'])
def test_recovery_observes_late_arrival_without_reissuing(scene,mode):
    s=scene;s.m.prepare(s.owner,'Mission',s.mission,s.definition)
    s.owner._job.update(state='uncertain',ok=False)
    events=list(s.events);payload=dict(mode=mode,acknowledge_shared_progress=True)
    assert s.m.recover(s.owner,payload,events,True)['observed']=='loading'
    s.arrive();assert s.m.recover(s.owner,payload,events,True)['observed']=='loading'
    s.clock.now+=.6
    result=s.m.recover(s.owner,payload,events,True)
    assert result.get('observed')=='loaded' if mode=='inspect' else result['state']==('stopped' if mode=='close' else 'running')
    assert s.calls==['harmonica_p'] and s.receipt['issued']==['settled']
    assert s.owner._job['target'].endswith(':PC2')


def test_active_multimap_mission_does_not_return_to_opening_map(scene):
    s=scene;s.definition['execution_maps']=['world_p','harmonica_p']
    assert s.m.prepare(s.owner,'Mission',s.mission,s.definition)
    assert not s.calls and not s.events


def test_objective_map_travel_preserves_issued_work_and_rebinds(scene):
    s=scene;objective=dict(name='Enter',token='enter',completion_maps=['harmonica_p'])
    assert not s.m.objective_ready(s.owner,'Mission',s.mission,s.definition,objective)
    assert s.calls==['harmonica_p'] and s.events[-1]['event']=='completion_map_returned'
    assert s.events[0]['objective']==objective
    s.arrive();assert not s.m.observe(s.owner)
    s.clock.now+=.6;assert s.m.observe(s.owner)
    assert s.receipt['issued']==['settled'] and s.receipt['pending']=='unconfirmed'
    assert s.m.objective_ready(s.owner,'Mission',s.mission,s.definition,objective)
    assert s.calls==['harmonica_p'] and s.receipt['progress_at']==s.clock.now


def test_ambiguous_objective_map_never_requests_guessed_destination(scene):
    s=scene
    with pytest.raises(RuntimeError,match='ambiguous'):
        s.m.objective_ready(s.owner,'Mission',s.mission,s.definition,
                            dict(name='Enter',completion_maps=['harmonica_p','cowbell_p']))
    assert not s.calls and not s.events


def test_missing_objective_map_retains_current_map(scene):
    s=scene
    assert s.m.objective_ready(s.owner,'Mission',s.mission,s.definition,dict(name='Talk',completion_maps=[]))
    assert not s.calls


def test_scene_only_anchor_loads_its_explicit_map(scene):
    s=scene
    objective=dict(name='MovingNPC',completion_maps=[],scene_anchor=dict(map='Harmonica_P'))
    assert not s.m.objective_ready(s.owner,'Mission',s.mission,s.definition,objective)
    assert s.calls==['harmonica_p']
    assert s.events[0]['objective']==objective


def test_restart_can_close_map_receipt_without_native_context(scene,tmp_path):
    s=scene;s.m.prepare(s.owner,'Mission',s.mission,s.definition)
    path=tmp_path/'old.jsonl';path.write_text('')
    s.owner._job=None
    result=s.m.recover(s.owner,dict(mode='close',acknowledge_shared_progress=True,job_id='old'),s.events,False,path)
    assert result['closed'] and result['state']=='stopped'
    assert 'unverified_after_reload' in path.read_text()
    assert s.calls==['harmonica_p'] and not s.reads


def test_world_change_during_placement_cannot_rebind_or_issue_outcomes(scene):
    s=scene;s.owner._job['completion_context']['placement']={'state':'running'}
    s.arrive()
    with pytest.raises(RuntimeError,match='World changed during objective placement'):
        s.m.observe(s.owner)
    assert s.owner._runtime.world_address==1 and not s.reads and not s.calls


def test_reset_only_runs_after_mission_map_is_unloaded(scene):
    s=scene;s.definition.update(execution_map='world_p',execution_maps=['world_p'])
    assert not s.m.prepare_reset(s.owner,'Mission',s.mission,s.definition)
    assert s.calls==['intro_p']
    s.arrive('Intro_P');assert not s.m.observe(s.owner)
    s.clock.now+=.6;assert s.m.observe(s.owner)
    assert s.m.prepare_reset(s.owner,'Mission',s.mission,s.definition)
    assert s.calls==['intro_p']


def test_reset_does_not_detour_when_already_outside_mission_map(scene):
    s=scene
    assert s.m.prepare_reset(s.owner,'Mission',s.mission,s.definition)
    assert not s.calls


def test_reset_with_no_reviewed_holding_map_never_guesses(scene):
    s=scene;s.definition['execution_maps']=['world_p','intro_p']
    with pytest.raises(RuntimeError,match='holding map'):
        s.m.prepare_reset(s.owner,'Mission',s.mission,s.definition)
    assert not s.calls


@pytest.mark.parametrize('objective',[
    dict(name='Boss',completion_maps=['world_p'],scene_anchor=dict(map='World_P',position=[1,2,3])),
    dict(name='Talk',completion_maps=[]),
])
def test_completion_in_place_never_imports_or_runs_pawn_placement(scene,monkeypatch,objective):
    s=scene;s.owner._job['placement_policy']='map_only'
    monkeypatch.setitem(sys.modules,'completion_context_test.mission_completion_placement',None)
    assert s.m.observe(s.owner)
    assert s.m.objective_ready(s.owner,'Mission',s.mission,s.definition,objective)
    assert s.calls==[] and 'placement' not in s.owner._job['completion_context']


def test_completion_still_loads_required_other_map_then_runs_in_place(scene,monkeypatch):
    s=scene;s.owner._job['placement_policy']='map_only'
    monkeypatch.setitem(sys.modules,'completion_context_test.mission_completion_placement',None)
    objective=dict(name='Enter',completion_maps=['harmonica_p'])
    assert not s.m.objective_ready(s.owner,'Mission',s.mission,s.definition,objective)
    assert s.calls==['harmonica_p']
    s.arrive();assert not s.m.observe(s.owner)
    s.clock.now+=.6;assert s.m.observe(s.owner)
    assert s.m.objective_ready(s.owner,'Mission',s.mission,s.definition,objective)
    assert s.receipt['issued']==['settled'] and s.calls==['harmonica_p']


def test_active_completion_checks_selected_objective_map_without_opening_detour(scene):
    s=scene;s.owner._job['placement_policy']='map_only'
    assert s.m.prepare(s.owner,'Mission',s.mission,s.definition)
    assert not s.calls


def test_completion_rejects_retained_placement_before_any_native_work(scene):
    s=scene;s.owner._job['placement_policy']='map_only'
    s.owner._job['completion_context']['placement']={'state':'running'}
    with pytest.raises(RuntimeError,match='cannot retain objective placement'):s.m.observe(s.owner)
    assert not s.calls and not s.reads
