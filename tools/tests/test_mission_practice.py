"""Practice preparation must settle prior actions without finishing the target."""
import importlib
import importlib.resources
import importlib.util
import json
import struct
import sys
from pathlib import Path
from types import ModuleType,SimpleNamespace as NS

import pytest

ROOT=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools'

@pytest.fixture
def practice(monkeypatch):
    monkeypatch.setattr(importlib.resources,'files',lambda package:ROOT)
    package=ModuleType('practice_test');package.__path__=[str(ROOT)]
    monkeypatch.setitem(sys.modules,'practice_test',package)
    spec=importlib.util.spec_from_file_location('practice_test.mission_practice',ROOT/'mission_practice.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.DATA={'mission':dict(title='Mission',execution_map='world_p',groups=[dict(index=0,objectives=[dict(name='before')]),dict(index=1,objectives=[dict(name='target')])])}
    row=dict(token='mission-token',state='active')
    world=NS(_get_address=lambda:101,_path_name=lambda:'World.World_P')
    engine=NS(base=0,world_address=101,snapshot=lambda:{},u64=lambda address:address,
              read=lambda address,size:struct.pack('<i',0 if address==0x1080 else 1))
    progress=NS(_engine=lambda:engine,_party=lambda:[],_binding=lambda rows:[],
                _row=lambda *args:row,_state=lambda row:row['state'])
    monkeypatch.setattr(module,'_world',lambda:world)
    monkeypatch.setattr(module,'_progress',lambda:progress)
    monkeypatch.setattr(module,'_save',lambda event=None:None)
    module._real_track=module._track
    monkeypatch.setattr(module,'_track',lambda *a:True)
    context=importlib.import_module('practice_test.mission_completion_context')
    monkeypatch.setattr(context,'world',lambda:world)
    module._job=dict(id='job',pid=module.os.getpid(),world=101,binding=[],name='mission',token='mission-token',
                     phase='checkpoint_settle',selected_objective='target',checkpoint_settle_since=module.time.monotonic(),checkpoint=1,issued=[],state='running',
                     completion_context={'world':101},anchor={'map':'world_p'})
    return module

def objectives(monkeypatch,rows):
    monkeypatch.setitem(sys.modules,'practice_test.mission_objectives',NS(read=lambda *args:rows))


def test_forward_save_selection_is_available_without_a_saved_mission_record(practice,monkeypatch):
    name='Mission_Main_City3'
    definition=json.loads((ROOT/'mission_practice_catalog.json').read_text(encoding='utf-8'))['missions'][name]
    practice.DATA={name:definition}
    progress=practice._progress()
    progress.select=lambda *args:[name]
    def missing(*args):raise ValueError('No existing save record')
    progress._row=missing
    monkeypatch.setitem(sys.modules,'practice_test.mission_dlc',NS(inspect=lambda rows:{},requirement=lambda *args:None))
    monkeypatch.setitem(sys.modules,'practice_test.mission_execution',NS(coverage_error=lambda *args:None))
    result=practice.preview({'scope':'named','missions':[name]})
    assert result['ok'] and any(c['save_backed_supported'] for c in result['choices'])
    assert all(not c['save_backed_reason'] for c in result['choices'])
    assert all(c['blocked_reason']=='Mission prerequisites are not available' for c in result['choices'])

@pytest.mark.parametrize('finishing',[4,10,11,12])
def test_target_is_not_ready_while_prior_issued_action_is_unsettled(practice,monkeypatch,finishing):
    objectives(monkeypatch,[dict(name='before',pointer='0x1000',token='earlier',state=finishing,hidden=False),
                           dict(name='target',pointer='0x2000',token='next',state=4,hidden=False)])
    monkeypatch.setattr(practice,'_teleport',lambda *args:pytest.fail('Must wait for prior authored actions'))
    with pytest.raises(RuntimeError,match='earlier objective remained active'):practice._step()

def test_selected_objective_is_left_active_after_predecessor_settles(practice,monkeypatch):
    rows=[dict(name='before',pointer='0x1000',token='earlier',state=13,hidden=False),
          dict(name='target',pointer='0x2000',token='next',state=4,hidden=False)]
    objectives(monkeypatch,rows);moved=[]
    monkeypatch.setattr(practice,'_teleport',lambda rows:moved.append(True))
    practice._step();practice._step()
    assert moved==[True] and rows[1]['state']==4


def test_mission_beginning_needs_no_anchor_and_issues_no_objective(practice,monkeypatch):
    practice._job.update(checkpoint=0,anchor=None,issued=[],phase='activate_wait')
    monkeypatch.setattr(practice,'_teleport',lambda *args:pytest.fail('Opening uses ordinary travel, not invented coordinates'))
    monkeypatch.setitem(sys.modules,'practice_test.mission_execution',NS(advance=lambda *args,**kw:pytest.fail('Opening must leave objectives for gameplay')))
    practice._step()
    assert practice._job['state']=='completed'
    assert not practice._job['issued']


@pytest.mark.parametrize('recorded',[False,True])
def test_mission_beginning_waits_for_selected_hud_before_completion_or_placement(practice,monkeypatch,recorded):
    practice._job.update(checkpoint=0,anchor={'map':'world_p','recorded':True} if recorded else None,
                         issued=[],phase='activate_wait')
    tracked=[]
    monkeypatch.setattr(practice,'_track',lambda *args:tracked.append(args[2]['token']) or False)
    monkeypatch.setattr(practice,'_teleport',lambda *args:pytest.fail('Tracking must be confirmed before placement'))
    practice._step()
    assert tracked==['mission-token']
    assert practice._job['state']=='running' and practice._job['phase']=='activate_wait'
    assert not practice._job['issued']


def test_missing_jump_anchor_still_prepares_selected_objective_scene(practice,monkeypatch):
    practice._job['anchor']=None
    rows=[dict(name='before',pointer='0x1000',token='earlier',state=13,hidden=False),
          dict(name='target',pointer='0x2000',token='next',state=4,hidden=False)]
    objectives(monkeypatch,rows);calls=[]
    context=importlib.import_module('practice_test.mission_completion_context')
    monkeypatch.setattr(context,'objective_ready',lambda owner,name,row,definition,objective:calls.append(objective['token']) or True)
    monkeypatch.setattr(practice,'_teleport',lambda *args:pytest.fail('A missing anchor must not be invented'))
    practice._step();assert practice._job['phase']=='replay_scene'
    practice._step();assert practice._job['phase']=='world_ready' and calls==['next']
    monkeypatch.setitem(sys.modules,'practice_test.mission_practice_world',NS(ready=lambda *args:True))
    practice._step();assert practice._job['state']=='completed' and rows[1]['state']==4


def test_recorded_start_reloads_area_after_staging_before_placement(practice,monkeypatch):
    practice._job['anchor'].update(recorded=True)
    practice._job['selected_objective']='target'
    calls=[]
    monkeypatch.setitem(sys.modules,'practice_test.mission_execution',NS(
        advance=lambda *a,**k:pytest.fail('Direct replay must never advance earlier steps'),
        objectives=lambda *a:[dict(name='target',state=4)]))
    context=sys.modules['practice_test.mission_completion_context']
    practice._job['phase']='checkpoint_unload'
    monkeypatch.setattr(context,'prepare_reset',lambda *a:calls.append('unload') or True)
    monkeypatch.setattr(context,'travel_to',lambda owner,name,row,title,destination:calls.append(destination) or True)
    def stage(engine,row,selected,checkpoint,journal,**kwargs):
        assert practice._job['state']=='uncertain' and practice._job['phase']=='checkpoint_return'
        calls.append('stage')
    monkeypatch.setitem(sys.modules,'practice_test.mission_reset',NS(stage_checkpoint=stage))
    monkeypatch.setattr(practice,'_teleport',lambda rows:calls.append('placement'))
    for _ in range(5):practice._step()
    assert calls==['unload','stage','world_p','world_p','placement']


def test_recorded_start_refuses_completed_selection_after_reload(practice,monkeypatch):
    practice._job.update(phase='teleport',selected_objective='target')
    practice._job['anchor'].update(recorded=True)
    monkeypatch.setitem(sys.modules,'practice_test.mission_execution',NS(objectives=lambda *a:[dict(name='target',state=13)]))
    monkeypatch.setattr(practice,'_teleport',lambda *a:pytest.fail('Completed objective must not be presented as replayable'))
    with pytest.raises(RuntimeError,match='not active after map reload'):practice._step()


@pytest.mark.parametrize('mission,checkpoint,objective',[
    ('Mission_DLC_Banjo',7,'Banjo_Reach_DLC_Map_Load'),
    ('Mission_Main_Grasslands3',7,'EnterFortress'),
    ('Mission_Main_City2',11,'EnterAscensionChamber'),
])
def test_selected_travel_remains_on_source_authored_approach_map(practice,mission,checkpoint,objective):
    data=json.loads((ROOT/'mission_practice_catalog.json').read_text())['missions'][mission]
    selected=next(o for g in data['groups'] for o in g['objectives'] if o['name']==objective)
    assert practice._return_map(data,selected,checkpoint,None)=='world_p'
    assert selected['travel_map']!='world_p'


def test_missing_arrival_approach_stops_before_reset_instead_of_consuming_target(practice):
    with pytest.raises(RuntimeError,match='approach map is unresolved'):
        practice._return_map(dict(groups=[]),dict(travel_map='banjo_p'),7,None)


def test_fresh_completed_mission_initializes_records_once_before_direct_stage(practice,monkeypatch):
    progress=practice._progress();progress._row({},'mission')['state']='completed'
    rows=[];calls=[]
    monkeypatch.setitem(sys.modules,'practice_test.mission_execution',NS(objectives=lambda *a:rows))
    context=sys.modules['practice_test.mission_completion_context']
    monkeypatch.setattr(context,'prepare_reset',lambda *a:True)
    def start(payload,**kwargs):
        assert practice._job['state']=='uncertain'
        assert payload['mode']=='reopen' and kwargs=={'manage_replay_travel':False}
        calls.append('initialize');return dict(id='child')
    progress.start=start
    progress.poll=lambda ident:dict(state='running')
    practice._job['phase']='checkpoint_unload'
    practice._step();practice._step();practice._step()
    assert calls==['initialize'] and practice._job['phase']=='checkpoint_reopen_wait'
    rows.append(dict(name='target',group=1,state=4,optional=False))
    progress._row({},'mission')['state']='accepted'
    progress.poll=lambda ident:dict(state='completed')
    monkeypatch.setitem(sys.modules,'practice_test.mission_reset',NS(stage_checkpoint=lambda *a,**k:calls.append('stage')))
    practice._step();practice._step()
    assert calls==['initialize','stage'] and practice._job['phase']=='checkpoint_return'


def test_replay_tracking_waits_for_readback_without_repeating_rpc(practice,monkeypatch):
    token='01'*12;tracked=[];calls=[]
    monkeypatch.setitem(sys.modules,'unrealsdk',NS(make_struct=lambda *a,**k:NS(_get_address=lambda:123)))
    engine=NS(read=lambda *a:bytes.fromhex(token),snapshot=lambda:dict(tracked=list(tracked)))
    pc=NS(PlayerState=NS(StableIndex=7),ServerRequestTrackMission=lambda *args:calls.append(args))
    rows=[dict(pc=pc,host=True)]
    assert not practice._real_track(rows,engine,dict(token=token))
    assert not practice._real_track(rows,engine,dict(token=token))
    tracked.append(token)
    assert practice._real_track(rows,engine,dict(token=token))
    assert len(calls)==1 and calls[0][1]==7


def test_replay_tracking_rejects_token_mismatch_before_rpc(practice,monkeypatch):
    monkeypatch.setitem(sys.modules,'unrealsdk',NS(make_struct=lambda *a,**k:NS(_get_address=lambda:123)))
    with pytest.raises(RuntimeError,match='token differs'):
        practice._real_track([],NS(read=lambda *a:b'\0'*12),dict(token='01'*12))
    assert not practice._job.get('tracking_issued')


@pytest.mark.parametrize('field',['travel_map','activation_by_arrival'])
def test_missing_anchor_does_not_consume_selected_arrival_objective(practice,monkeypatch,field):
    practice._job.update(anchor=None,phase='replay_scene')
    practice.DATA['mission']['groups'][1]['objectives'][0][field]='fortress_p' if field=='travel_map' else True
    objectives(monkeypatch,[dict(name='target',pointer='0x2000',token='next',state=4,hidden=False)])
    context=importlib.import_module('practice_test.mission_completion_context')
    monkeypatch.setattr(context,'objective_ready',lambda *args:pytest.fail('Selected arrival must remain for the player'))
    practice._step()
    assert practice._job['phase']=='world_ready'


def test_missing_anchor_keeps_hidden_arrival_trigger_for_gameplay(practice,monkeypatch):
    practice._job.update(anchor=None,phase='replay_scene')
    practice.DATA['mission']['groups'][1]['objectives'][0].update(hidden=True,activation_by_arrival=True)
    objectives(monkeypatch,[dict(name='target',pointer='0x2000',token='next',state=4,hidden=True)])
    context=importlib.import_module('practice_test.mission_completion_context')
    monkeypatch.setattr(context,'objective_ready',lambda *args:pytest.fail('Do not consume the selected hidden arrival'))
    practice._step()
    assert practice._job['phase']=='world_ready'


def test_checkpoint_groups_must_match_native_data_before_any_call(practice,monkeypatch):
    objectives(monkeypatch,[dict(name='before',pointer='0x2000',token='earlier',state=13,hidden=False)])
    with pytest.raises(RuntimeError,match='groups differ'):practice._step()

def test_practice_does_not_block_other_bridge_tools(practice):
    assert practice.conflict('mission_start')
    assert practice.conflict('full_progress_start')
    assert practice.conflict('full_progress_step')
    assert practice.conflict('full_progress_resume')
    assert not practice.conflict('full_progress_status')
    assert not practice.conflict('give_serials')
    assert not practice.conflict('mission_preview')
    assert not practice.conflict('mission_practice_step')


def test_optional_target_cannot_report_checkpoint_success(practice,monkeypatch):
    practice.DATA['mission']['groups'][1]['objectives'][0]['optional']=True
    objectives(monkeypatch,[dict(name='before',pointer='0x1000',token='earlier',state=13,hidden=False),
                           dict(name='target',pointer='0x2000',token='next',state=4,hidden=False)])
    monkeypatch.setattr(practice,'_teleport',lambda *args:pytest.fail('Optional target is not a playable required checkpoint'))
    with pytest.raises(RuntimeError,match='required main objective'):practice._step()

def test_unknown_required_completion_anchor_is_not_offered_as_verified():
    data=json.loads((ROOT/'mission_practice_catalog.json').read_bytes())['missions']
    groups=data['Mission_Main_Grasslands1']['groups']
    assert groups[7]['start_anchor'] is None
    heist=data['Mission_Side_Heist']['groups'][30]['objectives']
    missing=next(o for o in heist if o['name']=='Find_Valuable_4')
    assert missing['unresolved']=='missing_definition'


def test_practice_unloads_current_mission_map_before_reset(practice,monkeypatch):
    context=importlib.import_module('practice_test.mission_completion_context')
    practice._job.update(phase='prepare',checkpoint=0,anchor={'map':'fortress_p'})
    calls=[]
    monkeypatch.setattr(context,'travel_to',lambda owner,name,row,title,destination,*args:calls.append(destination) or False)
    practice._step()
    assert calls==['intro_p'] and practice._job['phase']=='prepare'


def test_practice_owns_travel_for_child_reset(practice,monkeypatch):
    context=importlib.import_module('practice_test.mission_completion_context')
    practice._job.update(phase='prepare',checkpoint=0);calls=[]
    monkeypatch.setattr(context,'prepare_reset',lambda *args:True)
    def start(payload,**kwargs):
        calls.append((payload,kwargs));return dict(id='child')
    practice._progress().start=start
    practice._step()
    assert calls[0][0]['mode']=='reopen'
    assert calls[0][1]==dict(manage_replay_travel=False)
    assert practice._job['mission_job']=='child'


def test_ready_checkpoint_waits_for_anchor_map_before_placement(practice,monkeypatch):
    objectives(monkeypatch,[dict(name='before',pointer='0x1000',token='earlier',state=13,hidden=False),
                           dict(name='target',pointer='0x2000',token='next',state=4,hidden=False)])
    practice._job['anchor']={'map':'fortress_p'}
    context=importlib.import_module('practice_test.mission_completion_context')
    calls=[];moved=[]
    monkeypatch.setattr(context,'travel_to',lambda owner,name,row,title,destination,*args:calls.append(destination) or False)
    monkeypatch.setattr(practice,'_teleport',lambda rows:moved.append(True))
    practice._step();practice._step()
    assert practice._job['phase']=='teleport' and not moved and calls==['fortress_p']
    monkeypatch.setattr(context,'travel_to',lambda *args:True)
    practice._step()
    assert moved==[True]


def test_shared_travel_rebinds_practice_runtime_without_replacing_mission_job(practice):
    progress=practice._progress();progress._job={'id':'mission-child'}
    owner=practice._CompletionOwner();replacement=object()
    owner._runtime=replacement
    assert progress._runtime is replacement
    assert owner._job is practice._job and progress._job=={'id':'mission-child'}


def test_interrupted_mission_receipt_blocks_practice_before_creating_a_job(practice, monkeypatch):
    monkeypatch.setitem(sys.modules, 'practice_test.backend_actions', NS(full_progress_conflict=lambda action:False))
    progress = practice._progress(); progress._job = None
    practice._job = {'id':'previous', 'state':'cancelled'}
    before = practice._job
    def interrupted():
        raise RuntimeError('An earlier job was interrupted or uncertain')
    progress.require_clear_journals = interrupted
    with pytest.raises(RuntimeError, match='interrupted or uncertain'):
        practice.start(dict(acknowledge_shared_progress=True))
    assert practice._job is before


def test_practice_pump_does_not_interrupt_dialogue_before_native_finish(practice, monkeypatch):
    calls = []
    monkeypatch.setitem(sys.modules, 'practice_test.progress_dialogue', NS(
        DialogueSkipper=lambda:NS(poll=lambda *args:calls.append('interrupted'))))
    monkeypatch.setitem(sys.modules, 'unrealsdk', NS(find_all=lambda cls:[]))
    practice._job['started'] = practice.time.time()
    monkeypatch.setattr(practice, '_step', lambda:None)
    assert practice.step({'job_id':'job'})['state'] == 'running'
    assert calls == []


def test_long_practice_keeps_progressing_beyond_six_minutes(practice,monkeypatch):
    clock=[100.]
    monkeypatch.setattr(practice.time,'monotonic',lambda:clock[0])
    practice._job.update(started=practice.time.time()-3600,progress_at=100.)
    def advance():
        practice._job['issued'].append(str(clock[0]))
        clock[0]+=.03  # End this bounded pump after one objective.
    monkeypatch.setattr(practice,'_step',advance)
    for _ in range(4):
        clock[0]+=300.
        assert practice.step({'job_id':'job'})['state']=='running'
    assert len(practice._job['issued'])==4


def test_status_polling_does_not_extend_stalled_practice(practice,monkeypatch):
    clock=[100.];calls=[]
    monkeypatch.setattr(practice.time,'monotonic',lambda:clock[0])
    practice._job['progress_at']=100.
    monkeypatch.setattr(practice,'_step',lambda:calls.append('step'))
    monkeypatch.setitem(sys.modules,'practice_test.mission_practice_placement',NS(cancel=lambda *a:False))
    assert practice.step({'job_id':'job'})['state']=='running'
    clock[0]+=practice.STALL_TIMEOUT+1
    assert practice.step({'job_id':'job'})['state']=='stopped'
    assert calls==['step'] and 'stopped making progress' in practice._job['message']


@pytest.mark.parametrize('result',['finishing','arrived','invalid'])
def test_practice_long_arrival_requires_fresh_context_validation(practice,monkeypatch,result):
    clock=[1000.];calls=[]
    monkeypatch.setattr(practice.time,'monotonic',lambda:clock[0])
    practice._job['progress_at']=100.
    practice._job['completion_context']['arrival_wait_since']=110.
    monkeypatch.setattr(practice,'_step',lambda:calls.append('step'))
    monkeypatch.setitem(sys.modules,'practice_test.mission_practice_placement',NS(cancel=lambda *a:False))
    def observe(owner):
        calls.append('observe')
        if result=='invalid':raise RuntimeError('Arrival identity changed or deadline expired')
        return result=='arrived'
    monkeypatch.setattr(sys.modules['practice_test.mission_completion_context'],'observe',observe)
    status=practice.step({'job_id':'job'})
    assert status['state']==('stopped' if result=='invalid' else 'running')
    assert calls==(['observe','step'] if result=='arrived' else ['observe'])
    assert practice._job['progress_at']==(1000. if result=='arrived' else 100.)
