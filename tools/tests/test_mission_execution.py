"""Native graphs must settle without falling back to mission status writes."""
import copy
import importlib.resources
import importlib.util
import json
import struct
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace as NS

import pytest

ROOT = Path(__file__).parents[2] / 'mod_extracted/MattsSDKBoostingTools'


@pytest.fixture
def rig(monkeypatch):
    monkeypatch.setattr(importlib.resources, 'files', lambda package: ROOT)
    package = ModuleType('execution_test'); package.__path__ = [str(ROOT)]
    monkeypatch.setitem(sys.modules, 'execution_test', package)
    spec = importlib.util.spec_from_file_location('execution_test.mission_execution', ROOT / 'mission_execution.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    context=NS(observe=lambda owner:True,prepare=lambda *args:True,prepare_reset=lambda *args:True,expect_finish=lambda *args:None,begin=lambda *args:{},
               map_name=lambda value:'world_p',world=lambda:None,objective_ready=lambda *args:True)
    monkeypatch.setitem(sys.modules,'execution_test.mission_completion_context',context)
    data = dict(title='Test mission',execution_map='world_p',groups=[dict(index=0, objectives=[dict(name='first'), dict(name='hidden')]),
                        dict(index=1, objectives=[dict(name='next')])])
    rows = [dict(name='first', token='one', pointer='0x1000', state=4, hidden=False),
            dict(name='hidden', token='two', pointer='0x2000', state=3, hidden=True),
            dict(name='next', token='three', pointer='0x3000', state=3, hidden=False)]
    groups = {0x1080: 0, 0x2080: 0, 0x3080: 1}
    engine = NS(base=0, u64=lambda address: address,
                read=lambda address, size: bytes.fromhex(m.OUTCOME_BYTES) if size == 32 else struct.pack('<i', groups[address]))
    monkeypatch.setitem(sys.modules, 'execution_test.mission_objectives', NS(read=lambda *args: copy.deepcopy(rows)))
    calls, events = [], []
    def factory(*signature):
        def bind(address):
            def invoke(pointer, outcome):
                assert events[-1]['event'] == 'issued'
                calls.append((address, pointer, outcome))
                next(o for o in rows if int(o['pointer'], 16) == pointer)['state'] = 10
            return invoke
        return bind
    monkeypatch.setattr(m.C, 'WINFUNCTYPE', factory)
    receipt = {}
    def advance(checkpoint=None):
        return m.advance(engine, dict(token='mission'), 'test', receipt, events.append,
                         checkpoint=checkpoint, definition=data)
    return NS(m=m, data=data, rows=rows, engine=engine, groups=groups, calls=calls,
              events=events, receipt=receipt, advance=advance)


def test_finish_phases_prevent_duplicate_and_next_outcome(rig):
    r = rig; r.advance(); r.rows[2]['state'] = 4
    for state in (4, 10, 11, 12):
        r.rows[0]['state'] = state
        assert not r.advance()['ready']
        assert len(r.calls) == 1
    r.rows[0]['state'] = 13
    r.advance()
    assert [c[1] for c in r.calls] == [0x1000, 0x3000]
    assert all(c[0] == r.m.OUTCOME_RVA for c in r.calls)


def test_selected_objective_does_not_advance_other_active_steps(rig):
    r=rig;r.rows[2]['state']=4
    def selected():
        return r.m.advance(r.engine,dict(token='mission'),'test',r.receipt,r.events.append,
                           definition=r.data,selected_token='three')
    selected()
    assert [c[1] for c in r.calls]==[0x3000]
    r.rows[2]['state']=13
    assert selected()['ready']
    assert [c[1] for c in r.calls]==[0x3000] and r.rows[0]['state']==4


def test_selected_composite_only_advances_its_authored_children(rig):
    r=rig
    r.data['groups'][0]['objectives'][0]['wait_for_objectives']=['hidden']
    r.data['groups'][0]['objectives'][1]['optional']=True
    r.rows[1]['state']=4;r.rows[2]['state']=4
    r.m.advance(r.engine,dict(token='mission'),'test',r.receipt,r.events.append,
                definition=r.data,selected_token='one')
    assert [c[1] for c in r.calls]==[0x2000]
    r.rows[0]['state']=13;r.rows[1]['state']=13
    assert r.m.advance(r.engine,dict(token='mission'),'test',r.receipt,r.events.append,
                       definition=r.data,selected_token='one')['ready']
    assert len(r.calls)==1 and r.rows[2]['state']==4


def test_missing_selected_token_never_advances_a_replacement(rig):
    with pytest.raises(RuntimeError,match='Selected objective is unavailable'):
        rig.m.advance(rig.engine,dict(token='mission'),'test',{},rig.events.append,
                      definition=rig.data,selected_token='gone')
    assert not rig.calls


def test_native_npc_scene_may_finish_after_two_minutes_without_reissue(rig,monkeypatch):
    r=rig;clock=[10.]
    monkeypatch.setattr(r.m.time,'monotonic',lambda:clock[0])
    r.advance();clock[0]=190.
    assert not r.advance()['ready'] and len(r.calls)==1
    r.rows[0]['state']=13;r.rows[2]['state']=4
    r.advance()
    assert [c[1] for c in r.calls]==[0x1000,0x3000]


def test_finish_wait_still_has_a_bounded_stop_without_reissue(rig,monkeypatch):
    r=rig;clock=[10.]
    monkeypatch.setattr(r.m.time,'monotonic',lambda:clock[0])
    r.advance();clock[0]+=r.m.FINISH_TIMEOUT+1
    with pytest.raises(RuntimeError,match='needs inspection'):r.advance()
    assert len(r.calls)==1


def test_talk_uses_normal_interaction_once_without_forcing_outcome(rig,monkeypatch):
    r=rig;used=[]
    r.data['groups'][0]['objectives'][0]['interaction']={'kind':'talk'}
    available=[False]
    def prepare(obj):return (lambda:used.append(obj['token'])) if available[0] else False
    monkeypatch.setitem(sys.modules,'execution_test.mission_interactions',NS(prepare=prepare))
    assert not r.advance()['ready']
    assert not r.calls and not used and not r.events
    available[0]=True;r.advance();r.advance()
    assert used==['one'] and not r.calls
    assert r.events[0]['via']=='npc_use' and r.receipt['issued']==['one']
    r.rows[0]['state']=13;r.rows[2]['state']=4;r.advance()
    assert [c[1] for c in r.calls]==[0x3000]


def test_talk_failure_never_falls_back_to_objective_outcome(rig,monkeypatch):
    r=rig;r.data['groups'][0]['objectives'][0]['interaction']={'kind':'talk'}
    def use():raise RuntimeError('Lost reply')
    monkeypatch.setitem(sys.modules,'execution_test.mission_interactions',NS(prepare=lambda obj:use))
    with pytest.raises(RuntimeError,match='unconfirmed'):r.advance()
    assert r.receipt['pending']=='one' and not r.calls


def test_required_hidden_objective_is_processed(rig):
    r = rig; r.rows[0]['state'] = 13; r.rows[1]['state'] = 4
    r.advance()
    assert r.calls[0][1] == 0x2000


def test_native_tracker_waits_for_hidden_child_instead_of_starting_its_scene_early(rig):
    r=rig;r.data['groups'][0]['objectives'][0]['wait_for_objectives']=['hidden']
    r.rows[1]['state']=4
    r.advance()
    assert [c[1] for c in r.calls]==[0x2000]
    r.rows[1]['state']=13
    # Let the native watcher react; do not force its outcome even after the child.
    r.advance();assert len(r.calls)==1
    r.rows[0]['state']=11;r.rows[2]['state']=4
    r.advance();assert len(r.calls)==1
    r.rows[0]['state']=13;r.advance()
    assert [c[1] for c in r.calls]==[0x2000,0x3000]


def test_overarching_native_tracker_does_not_complete_before_later_child(rig):
    r=rig;r.data['groups'][0]['objectives'][0]['wait_for_objectives']=['next']
    r.rows[2]['state']=4;r.advance()
    assert [c[1] for c in r.calls]==[0x3000]


def test_required_tracker_can_use_its_optional_child(rig):
    r=rig;r.data['groups'][0]['objectives'][0]['wait_for_objectives']=['hidden']
    r.data['groups'][0]['objectives'][1]['optional']=True
    r.rows[1]['state']=4;r.advance()
    assert [c[1] for c in r.calls]==[0x2000]
    r.rows[0]['state']=13;r.rows[2]['state']=4
    # Keep waiting for the issued child after the native parent settles.
    r.advance();assert len(r.calls)==1
    r.rows[1]['state']=13;r.advance()
    assert [c[1] for c in r.calls]==[0x2000,0x3000]


def test_optional_alternatives_wait_for_native_choice_resolution(rig):
    r=rig;r.data['groups'][0]['objectives'][0]['wait_for_objectives']=['hidden','next']
    r.data['groups'][0]['objectives'][1]['optional']=True
    r.data['groups'][1]['objectives'][0]['optional']=True
    r.rows[1]['state']=r.rows[2]['state']=4
    r.advance();r.advance()
    assert [c[1] for c in r.calls]==[0x2000]
    # The native choice deactivates the parent and unused branch.
    r.rows[0]['state']=13;r.rows[1]['state']=13
    r.advance();assert len(r.calls)==1


def test_recursive_optional_tracker_dependencies_and_checkpoint_scope(rig):
    r=rig;r.data['groups'][0]['objectives'][0]['wait_for_objectives']=['hidden']
    r.data['groups'][0]['objectives'][1].update(optional=True,wait_for_objectives=['next'])
    r.data['groups'][1]['objectives'][0]['optional']=True
    r.rows[1]['state']=r.rows[2]['state']=4
    assert r.advance(checkpoint=0)['ready']
    assert not r.calls
    r.advance();assert [c[1] for c in r.calls]==[0x3000]


def test_hidden_checkpoint_trigger_can_coexist_with_later_visible_navigation(rig):
    r=rig;r.rows[0]['state']=13;r.rows[1]['state']=4;r.rows[2]['state']=4
    assert r.advance(checkpoint=0)['ready']
    assert not r.calls and not r.events


def test_later_navigation_does_not_hide_unsettled_prior_checkpoint_work(rig):
    r=rig;r.rows[0]['state']=11;r.rows[1]['state']=4;r.rows[2]['state']=4
    r.data['groups'][0]['index']=-1;r.groups[0x1080]=-1
    r.data['groups'][0]['objectives']=[dict(name='first')]
    r.data['groups'].append(dict(index=0,objectives=[dict(name='hidden')]))
    assert not r.advance(checkpoint=0)['ready']
    assert not r.calls


def test_checkpoint_still_rejects_later_only_navigation(rig):
    r=rig;r.rows[0]['state']=r.rows[1]['state']=13;r.rows[2]['state']=4
    with pytest.raises(RuntimeError,match='advanced beyond'):
        r.advance(checkpoint=0)
    assert not r.calls


def test_finishing_objective_does_not_deadlock_its_active_hidden_sibling(rig):
    r=rig;r.advance();r.rows[0]['state']=11;r.rows[1]['state']=4
    r.advance()
    assert [c[1] for c in r.calls]==[0x1000,0x2000]
    r.advance()
    assert len(r.calls)==2 and r.receipt['issued']==['one','two']


def test_finishing_group_cannot_depart_to_sibling_on_another_map(rig):
    r=rig;r.advance();r.rows[1]['state']=4
    r.data['groups'][0]['objectives'][1]['completion_maps']=['fortress_p']
    seen=[]
    result=r.m.advance(r.engine,dict(token='mission'),'test',r.receipt,r.events.append,
                       definition=r.data,current_map='world_p',before_outcome=lambda o:seen.append(o))
    assert not result['ready'] and not seen and len(r.calls)==1


def test_missing_issued_identity_blocks_even_same_group_sibling(rig):
    r=rig;r.advance();r.rows.pop(0);r.rows[0]['state']=4
    r.advance()
    assert len(r.calls)==1


def test_unresolved_future_definition_blocks_before_first_outcome(rig):
    r=rig
    r.data['groups'][1]['objectives'][0]['unresolved']='missing_definition'
    with pytest.raises(RuntimeError,match='unresolved'):r.advance()
    assert not r.calls and not r.events


def test_coordinate_gaps_do_not_block_objective_execution(rig):
    r=rig
    r.data['groups'][0]['unresolved']=[dict(reason='missing_completion_location')]
    assert r.advance()['issued']


def test_map_departure_waits_for_work_on_current_map_in_same_group(rig):
    r=rig;r.data['groups'][0]['objectives'][0]['completion_maps']=['fortress_p']
    r.data['groups'][0]['objectives'][1]['completion_maps']=['world_p'];r.rows[1]['state']=4
    seen=[]
    r.m.advance(r.engine,dict(token='mission'),'test',r.receipt,r.events.append,
                definition=r.data,current_map='world_p',before_outcome=lambda o:(seen.append(o) or True))
    assert seen[0]['name']=='hidden' and r.calls[0][1]==0x2000


def test_map_wait_has_no_issued_outcome_and_fresh_read_can_finish_naturally(rig):
    r=rig
    result=r.m.advance(r.engine,dict(token='mission'),'test',r.receipt,r.events.append,
                       definition=r.data,before_outcome=lambda o:False)
    assert result['await_map'] and not r.calls and not r.events and not r.receipt['issued']
    r.rows[0]['state']=13;r.rows[2]['state']=4
    r.advance()
    assert r.calls[0][1]==0x3000


def test_identical_references_are_accepted_but_conflicting_definitions_are_not(rig):
    r=rig;group=r.data['groups'][0]
    group['objectives'].append(dict(group['objectives'][0]))
    assert r.m.coverage_error('test',definition=r.data) is None
    group['objectives'][-1]['pointer']='different'
    assert 'Ambiguous' in r.m.coverage_error('test',definition=r.data)


def test_practice_coverage_only_requires_target_and_preceding_groups(rig):
    r=rig;r.data['groups'][1]['objectives'][0]['unresolved']='missing_definition'
    assert r.m.coverage_error('test',checkpoint=0,definition=r.data) is None
    assert r.m.coverage_error('test',checkpoint=1,definition=r.data)


def test_optional_objective_is_not_forced(rig):
    r = rig; r.data['groups'][0]['objectives'][0]['optional'] = True
    r.advance(); assert not r.calls


def test_practice_preserves_target_until_prior_required_action_finishes(rig):
    r = rig; r.rows[2]['state'] = 4
    assert not r.advance(1)['ready'] and r.calls[0][1] == 0x1000
    r.rows[0]['state'] = 13
    assert r.advance(1)['ready'] and len(r.calls) == 1


def test_reused_objective_membership_accepts_native_group(rig):
    r = rig; r.data['groups'][1]['objectives'].append(dict(name='first'))
    r.groups[0x1080] = 1
    assert r.advance(1)['ready'] and not r.calls


@pytest.mark.parametrize('corruption', ['group', 'missing', 'unresolved', 'duplicate', 'build', 'token'])
def test_identity_failures_prevent_any_native_outcome(rig, corruption):
    r = rig
    if corruption == 'group': r.groups[0x1080] = 3
    elif corruption == 'missing': r.rows[0]['name'] = 'unknown'
    elif corruption == 'unresolved': r.data['groups'][0]['objectives'][0]['unresolved'] = 'missing_definition'
    elif corruption == 'duplicate': r.data['groups'][0]['objectives'].append(dict(name='first', pointer='/conflicting-definition'))
    elif corruption == 'build': r.engine.read = lambda *args: b'\0' * 32 if args[1] == 32 else struct.pack('<i', 0)
    else: r.receipt['token'] = 'other'
    with pytest.raises(RuntimeError): r.advance()
    assert not r.calls and not r.events


def test_missing_issued_objective_is_not_called_again_or_claimed_ready(rig):
    r = rig; r.advance(); r.rows.pop(0); r.rows[-1]['state'] = 4
    assert not r.advance(1)['ready'] and len(r.calls) == 1


def test_native_exception_keeps_receipt_and_reports_uncertainty(rig, monkeypatch):
    r = rig
    def factory(*args):
        def bind(address):
            def fail(*args): raise RuntimeError('native failure')
            return fail
        return bind
    monkeypatch.setattr(r.m.C, 'WINFUNCTYPE', factory)
    with pytest.raises(RuntimeError) as error: r.advance()
    assert error.value.issued and r.receipt['pending'] == 'one'
    assert [e['event'] for e in r.events] == ['issued']


def test_shared_progression_uses_graph_until_mission_naturally_finishes(rig, monkeypatch, tmp_path):
    r = rig
    spec = importlib.util.spec_from_file_location('execution_test.mission_progression', ROOT / 'mission_progression.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    monkeypatch.setitem(sys.modules,spec.name,m)
    name = 'Mission_Main_Beach'; r.m.DATA[name] = r.data
    monkeypatch.setitem(sys.modules, 'execution_test.mission_execution', r.m)
    mission = dict(token='mission', source_identity=dict(name=name), generated=0, replication_type=0,
                   status_fact=dict(known_status='active'))
    r.engine.snapshot = lambda: dict(missions=[mission])
    pc = NS(_path_name=lambda: 'host')
    monkeypatch.setattr(m, '_engine', lambda: r.engine)
    monkeypatch.setattr(m, '_party', lambda: [dict(pc=pc)])
    monkeypatch.setattr(m, '_binding', lambda rows: ['same'])
    monkeypatch.setattr(m, '_validate_exit', lambda *args: None)
    monkeypatch.setattr(m, '_dlc_requirement', lambda *args: None)
    credits = []; monkeypatch.setattr(m, '_credit_completed', lambda *args: credits.append(True))
    # Helper receipt assertions use its own journal for this integration test.
    monkeypatch.setattr(m, '_journal', r.events.append)
    m._job = dict(id='job', state='running', phase='complete', index=0, completed=[], names=[name],
                  binding=['same'], target='host', completion_path='objective_graph')
    assert m.step('job')['state'] == 'running' and not credits
    m.step('job'); assert len(r.calls) == 1
    mission['status_fact']['known_status'] = 'completed'; r.rows.clear()
    assert m.step('job')['state'] == 'completed' and credits == [True]
    assert m._job['completed'] == [name]


def test_completed_mission_uses_native_reopen_before_graph(rig, monkeypatch):
    r = rig
    spec = importlib.util.spec_from_file_location('execution_test.mission_progression', ROOT / 'mission_progression.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    monkeypatch.setitem(sys.modules,spec.name,m)
    monkeypatch.setitem(sys.modules,'execution_test.mission_execution',r.m)
    name = 'Mission_Main_Beach'; r.m.DATA[name] = r.data
    mission = dict(token='mission', source_identity=dict(name=name), generated=0, replication_type=0,
                   record='0x100000', storage='0x200000',
                   status_fact=dict(known_status='completed'))
    r.engine.snapshot = lambda: dict(missions=[mission])
    r.engine.u64 = lambda a: {0x100000: 0x300000, 0x1000a8: 0x200000,
                              0x3000f8: 0xd80660, 0x300110: 0x419fefa}[a]
    r.engine.read = lambda *args: b'\1'
    pc = NS(_path_name=lambda: 'host')
    for method, value in (('_engine', lambda: r.engine), ('_party', lambda: [dict(pc=pc)]),
                          ('_binding', lambda rows: ['same']), ('_validate_exit', lambda *a: None),
                          ('_dlc_requirement', lambda *a: None), ('_journal', lambda e: None)):
        monkeypatch.setattr(m, method, value)
    calls = []
    def reopen(*args): calls.append(True); mission['status_fact']['known_status'] = 'active'
    monkeypatch.setitem(sys.modules, 'execution_test.mission_reset', NS(reopen=reopen))
    m._job = dict(id='job', state='running', phase='prepare', index=0, completed=[], names=[name],
                  binding=['same'], target='host', completion_path='objective_graph')
    assert m.step('job')['phase'] == 'accept' and calls == [True]
    assert not r.calls


def test_real_mandolin_repeated_reference_is_not_ambiguous(rig):
    r = rig
    definition = r.m.DATA['Mission_DLC_Mandolin']
    r.rows[:] = [dict(name='Mandolin_Talk_Electi', token='talk', pointer='0x1000', state=3, hidden=False)]
    r.groups[0x1080] = 7
    rows = r.m.objectives(r.engine, dict(token='mission'), definition)
    assert rows[0]['group'] == 7 and rows[0]['optional'] is True
    assert not r.calls


def progression_rig(rig, monkeypatch):
    r = rig
    spec = importlib.util.spec_from_file_location('execution_test.mission_progression', ROOT / 'mission_progression.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    monkeypatch.setitem(sys.modules,spec.name,m)
    monkeypatch.setitem(sys.modules, 'execution_test.mission_execution', r.m)
    mission = dict(token='mission', source_identity=dict(name='Mission_Main_Beach'), generated=0, replication_type=0,
                   record='0x100000', storage='0x200000', status_fact=dict(known_status='accepted'))
    r.engine.snapshot = lambda: dict(missions=[mission])
    party = [dict(pc=NS(_path_name=lambda: 'host'))]
    for method, value in (('_engine', lambda: r.engine), ('_party', lambda: party),
                          ('_binding', lambda rows: ['same']), ('_validate_exit', lambda *a: None),
                          ('_dlc_requirement', lambda *a: None), ('_credit_completed', lambda *a: None)):
        monkeypatch.setattr(m, method, value)
    return m, mission, party


@pytest.mark.parametrize('scope', ['current','named', 'all'])
def test_public_start_waits_for_activation_then_uses_shared_graph(rig, monkeypatch, tmp_path, scope):
    r = rig; m, mission, party = progression_rig(r, monkeypatch)
    name = mission['source_identity']['name']
    monkeypatch.setitem(sys.modules, 'mods_base', NS(SETTINGS_DIR=tmp_path))
    monkeypatch.setitem(sys.modules, 'execution_test.mission_discovery', NS(SCOPES=()))
    monkeypatch.setitem(sys.modules, 'execution_test.farming_targets', NS(resolve=lambda payload: party))
    monkeypatch.setattr(m, 'select', lambda *args: [name])
    # Scheduling is independent of native completion; retain one eligible row.
    monkeypatch.setattr(m, '_schedule_category', lambda snapshot: True)
    calls = []
    monkeypatch.setattr(m.C, 'WINFUNCTYPE', lambda *args:pytest.fail('No status shortcut is permitted'))
    monkeypatch.setattr(r.m,'advance',lambda *args,**kwargs:(calls.append(True) or dict(issued=True,message='Native objective issued')))
    started = m.start(dict(scope=scope, missions=[name], acknowledge_shared_progress=True))
    result = m.step(started['id'])
    assert result['state']=='running' and result['await_tick'] and not calls
    assert m._job['completion_path']=='objective_graph'
    mission['status_fact']['known_status']='active'
    assert m.step(started['id'])['state']=='running' and calls==[True]
    mission['status_fact']['known_status']='completed'
    assert m.step(started['id'])['state']=='completed' and calls==[True]


@pytest.mark.parametrize('empty',[False,True])
def test_public_start_rejects_future_coverage_gap_before_reset(rig,monkeypatch,tmp_path,empty):
    r=rig;m,mission,party=progression_rig(r,monkeypatch)
    name=mission['source_identity']['name'];r.m.DATA[name]=r.data
    mission['status_fact']['known_status']='completed'
    if empty:r.data['groups']=[]
    else:r.data['groups'][1]['objectives'][0]['unresolved']='missing_definition'
    monkeypatch.setitem(sys.modules,'mods_base',NS(SETTINGS_DIR=tmp_path))
    monkeypatch.setitem(sys.modules,'execution_test.mission_discovery',NS(SCOPES=()))
    monkeypatch.setitem(sys.modules,'execution_test.farming_targets',NS(resolve=lambda payload:party))
    with pytest.raises(ValueError,match='unavailable|unresolved'):
        m.start(dict(scope='named',missions=[name],reset_completed=True,acknowledge_shared_progress=True))
    assert m._job is None and not r.calls
    assert not list(tmp_path.rglob('*.jsonl'))


def test_explicit_graph_resume_refreshes_wait_without_repeating_outcome(rig, monkeypatch, tmp_path):
    r = rig; m, mission, _ = progression_rig(r, monkeypatch)
    durable_journal = m._journal
    monkeypatch.setattr(m, '_journal', lambda event: (durable_journal(event), r.events.append(event)))
    name = mission['source_identity']['name']; r.m.DATA[name] = r.data
    mission['status_fact']['known_status'] = 'active'
    clock = [100.0]
    monkeypatch.setattr(m.time, 'monotonic', lambda: clock[0])
    m._job = dict(id='job', ok=True, state='running', phase='complete', index=0, completed=[], names=[name],
                  binding=['same'], target='host', completion_path='objective_graph', journal=str(tmp_path/'job.jsonl'))
    m.step('job')
    assert len(r.calls) == 1
    clock[0] = 100.0+r.m.FINISH_TIMEOUT+1
    assert m.step('job')['state'] == 'stopped'
    assert m.resume('job')['state'] == 'running'
    assert m.step('job')['state'] == 'running'
    assert len(r.calls) == 1
    r.rows[0]['state'] = 13; r.rows[2]['state'] = 4
    m.step('job')
    assert [call[1] for call in r.calls] == [0x1000, 0x3000]


def test_graph_resume_preserves_uncertain_call_block(rig, monkeypatch, tmp_path):
    r = rig; m, mission, _ = progression_rig(r, monkeypatch)
    name = mission['source_identity']['name']; mission['status_fact']['known_status'] = 'active'
    receipt = dict(token='mission', issued=['one'], pending='one', progress_at=1.0)
    m._job = dict(id='job', state='stopped', phase='complete', index=0, names=[name], binding=['same'],
                  completion_path='objective_graph', objective_runs={name: receipt})
    with pytest.raises(ValueError, match='return receipt'):
        m.resume('job')
    assert receipt['pending'] == 'one' and receipt['progress_at'] == 1.0
    assert not r.calls
