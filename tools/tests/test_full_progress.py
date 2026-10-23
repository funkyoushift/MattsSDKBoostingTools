import importlib.util
from pathlib import Path
import pytest

P=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools/full_progress.py'
spec=importlib.util.spec_from_file_location('full_progress',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Driver:
    def __init__(self,n=2,owned=False):
        self.n=n;self.owned=owned;self.calls=[];self.binding='fixed';self.wait=False
    def preflight(self):
        return dict(players=list(range(self.n)),binding=self.binding,packs={'dlc':dict(allowed=self.owned,title='DLC',reason='Missing')})
    def check_idle(self):pass
    def begin(self,name,snapshot):
        self.calls.append(name)
        return dict(state='running' if self.wait else 'finished',child=name,message='Done')
    def poll(self,*args):return dict(state='finished')
    def cancel(self,child):return True

@pytest.mark.parametrize('n,owned,allowed',[(0,True,False),(1,False,True),(2,False,True),(3,False,True),(4,False,True),(4,True,True)])
def test_lobby_gate(n,owned,allowed):
    d=Driver(n,owned);s=d.preflight()
    assert m.eligibility(s['players'],s['packs'])['allowed']==allowed

def test_no_write_before_gate_or_ack(tmp_path):
    d=Driver(0);r=m.Run(d,tmp_path)
    with pytest.raises(ValueError):r.start({'acknowledge_shared_progress':True})
    d.owned=True;d.n=3
    with pytest.raises(ValueError):r.start({})
    assert not d.calls


def test_start_records_cleanup_of_uncertain_prior_uvh(tmp_path):
    d=Driver();d.prepare_start=lambda **kwargs:[dict(ok=True,kind='uvh',discarded_steps=25,prior_requests_sent=2)]
    run=m.Run(d,tmp_path)
    job=run.start({'acknowledge_shared_progress':True})
    assert job['prior_uvh_cleanup'][0]['discarded_steps']==25
    import json
    first=json.loads(Path(run.job['path']).read_text().splitlines()[0])
    assert first['prior_uvh_cleanup']==job['prior_uvh_cleanup']

def test_waits_before_next_stage(tmp_path):
    d=Driver();d.wait=True;r=m.Run(d,tmp_path);job=r.start({'acknowledge_shared_progress':True})
    assert r.step(job['id'])['index']==0
    assert r.step(job['id'])['index']==1
    assert d.calls==['missions']


def test_mission_transition_waits_before_stale_preflight_and_updates_binding(tmp_path):
    d=Driver();d.wait=True;r=m.Run(d,tmp_path);job=r.start({'acknowledge_shared_progress':True})
    r.step(job['id']);old_preflight=d.preflight
    d.preflight=lambda:pytest.fail('Old-world preflight must not run while travelling')
    d.observe_transition=lambda child,binding:dict(ready=False,message='Loading')
    assert r.step(job['id'])['state']=='running' and d.calls==['missions']
    d.binding='verified-world';d.preflight=old_preflight
    d.observe_transition=lambda child,binding:dict(ready=True,binding=d.binding)
    assert r.step(job['id'])['index']==1
    assert r.job['binding']=='verified-world' and d.calls==['missions']

def test_roster_change_stops_before_write(tmp_path):
    d=Driver();r=m.Run(d,tmp_path);job=r.start({'acknowledge_shared_progress':True});d.binding='changed'
    assert r.step(job['id'])['state']=='stopped'
    assert not d.calls


def test_roster_change_restores_active_selection_and_records_child(tmp_path):
    d=Driver();d.wait=True;r=m.Run(d,tmp_path);job=r.start({'acknowledge_shared_progress':True})
    r.step(job['id'])
    restored=[];d.stop=lambda child:restored.append(child);d.binding='changed'
    result=r.step(job['id'])
    assert result['state']=='uncertain' and restored==['missions']
    import json
    event=json.loads(Path(r.job['path']).read_text().splitlines()[-1])
    assert event['child']=='missions' and event['event']=='stopped'

def test_unknown_outcome_never_reissued(tmp_path):
    d=Driver();r=m.Run(d,tmp_path);job=r.start({'acknowledge_shared_progress':True})
    def fail(*args):d.calls.append('once');raise RuntimeError('Unknown')
    d.begin=fail
    assert r.step(job['id'])['state']=='uncertain'
    r.step(job['id']);assert d.calls==['once']
    assert m.Run(d,tmp_path).status()['state']=='interrupted'


def test_begin_failure_records_owned_mission_child_for_restart(tmp_path):
    import json
    d=Driver();d.begin=lambda *args:(_ for _ in ()).throw(RuntimeError('Native callback uncertain'))
    d.pending_child=lambda stage:dict(kind='mission',id='started-before-error')
    run=m.Run(d,tmp_path);job=run.start(dict(acknowledge_shared_progress=True))
    stopped=run.step(job['id'])
    assert stopped['state']=='uncertain'
    assert stopped['child']==dict(kind='mission',id='started-before-error')
    event=json.loads(Path(run.job['path']).read_text().splitlines()[-1])
    assert event['child']==stopped['child']


def test_interrupted_run_closes_owned_child_before_new_start(tmp_path):
    import json
    d=Driver();seen=[]
    d.close_interrupted=lambda events:seen.append(events[-1]['child']['id'])
    run=m.Run(d,tmp_path);ident='f'*32
    (tmp_path/(ident+'.jsonl')).write_text(json.dumps(dict(event='stopped',
        state='uncertain',child=dict(kind='mission',id='child-job')))+'\n')
    result=run.close(dict(job_id=ident,acknowledge_shared_progress=True))
    assert result['state']=='cancelled' and seen==['child-job']
    assert run.status()['state']=='idle'


def test_cancel_cleanup_failure_blocks_poll_and_resume(tmp_path):
    d=Driver();d.wait=True;r=m.Run(d,tmp_path);job=r.start({'acknowledge_shared_progress':True});r.step(job['id'])
    def fail(child):raise RuntimeError('Original card not restored')
    d.cancel=fail
    with pytest.raises(RuntimeError,match='not restored'):r.cancel(job['id'])
    assert r.job['cancel_requested'] and r.job['state']=='uncertain'
    d.poll=lambda *args:pytest.fail('Cancelled work must not advance')
    assert r.step(job['id'])['state']=='uncertain'
    with pytest.raises(RuntimeError,match='Cancellation is pending'):r.resume(dict(job_id=job['id'],acknowledge_shared_progress=True))

def test_finished_is_not_save_proof(tmp_path):
    d=Driver();r=m.Run(d,tmp_path);job=r.start({'acknowledge_shared_progress':True})
    for _ in m.STAGES:r.step(job['id'])
    assert r.status()['state']=='finished'
    assert not r.status()['completion_verified']
    assert '100% completion is not verified' in r.status()['message']


def test_finished_run_keeps_partial_and_skipped_stages_visible(tmp_path):
    d=Driver();r=m.Run(d,tmp_path)
    def begin(name,snapshot):
        d.calls.append(name)
        state='partial' if name in ('missions','character') else 'skipped' if name=='mayhem' else 'finished'
        return dict(state=state,child=name,message='Needs review' if state!='finished' else 'Done')
    d.begin=begin
    job=r.start({'acknowledge_shared_progress':True})
    for _ in m.STAGES:r.step(job['id'])
    result=r.status()
    assert result['state']=='finished' and result['completion_verified'] is False
    assert result['stage_summary']==dict(finished=6,partial=2,skipped=1)
    assert '2 incomplete and 1 skipped' in result['message']
    assert len(result['results'])==9 and len(d.calls)==9
    r.step(job['id']);assert len(d.calls)==9


def test_close_requires_ack_and_idle_children(tmp_path):
    d=Driver();r=m.Run(d,tmp_path);j=r.start({'acknowledge_shared_progress':True})
    with pytest.raises(RuntimeError):r.close({'job_id':j['id'],'acknowledge_shared_progress':True})
    r.cancel(j['id'])
    with pytest.raises(ValueError):r.close({'job_id':j['id']})
    assert r.close({'job_id':j['id'],'acknowledge_shared_progress':True})['state']=='cancelled'


def character_driver():
    import ast,time
    from types import SimpleNamespace as NS
    source=(P.parent/'full_progress_runtime.py').read_text().replace('            from . import vehicle_tuning','            vehicle_tuning = vehicle_stub').replace('        from . import mission_discovery','        mission_discovery = discovery_stub')
    source=source.replace('from . import sdu_progress', 'sdu_progress = sdu_stub')
    source=source.replace('from . import challenge_objective_complete', 'challenge_objective_complete = challenge_stub')
    source=source.replace('from . import mission_challenges', 'mission_challenges = credit_stub')
    source=source.replace('from . import dlc_refresh', 'dlc_refresh = refresh_stub')
    tree=ast.parse(source)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Driver')
    class RestoreError(RuntimeError):
        def __init__(self, name):
            self.original_name=name
            super().__init__('Could not restore '+name)
    calls=[]
    economy=NS(_MAX_WALLET_AMOUNT=1000,_MAX_SDU_POINTS=3225,_SDU_POINTS_POOL_INDEX=0,
               _target_character_for_pc=lambda pc:NS(GbxProgressionManager=NS(ProgressPointsContainer=NS(PointsAcquiredPerPool=[3225]))),
               _set_experience_level_via_bp=lambda ps,t,cap:calls.append(('level',ps,t,cap)) or True,
               _set_owned_vault_card_level=lambda pc,c,cap:calls.append(('card_level',pc,c,cap)) or True,
               VaultCardRestoreError=RestoreError,
               _give_currency_on_pc=lambda pc,t,amount:calls.append(('currency',pc,t,amount)) or True,
               _set_max_sdu_points_on_pc=lambda pc:True)
    env=dict(vehicle_stub=NS(_load_vehicle_catalog_rows=lambda:[],_load_vehicle_unlock_rows=lambda:[]),economy=economy,MAX_PLAYER_LEVEL=70,MAX_SPEC_LEVEL=701,MAX_VAULT_CARD_LEVEL=9999,time=time,
             credit_stub=NS(CreditReadbackMismatch=type('CreditReadbackMismatch',(RuntimeError,),{}),CreditPending=type('CreditPending',(RuntimeError,),{})),
             sdu_stub=NS(snapshot=lambda *a: None, advance=lambda *a: True), missions=NS(_engine=lambda: None),
             mission_credit_plan=lambda snapshot:([],[]),
             fact_trigger_plan=lambda snapshot,incomplete:([],[]))
    exec(compile(ast.Module(body=[cls],type_ignores=[]),'<driver>','exec'),env)
    return env['Driver'](),calls


@pytest.mark.parametrize('profile,warning',[
    ('steam-26007962',True),('epic-6d531d91',True),('steam-25372571',False)])
def test_current_build_catalog_limit_shown_for_steam_and_epic(profile,warning):
    from types import SimpleNamespace as NS
    driver,_=character_driver();env=driver.preflight.__globals__
    rows=[dict(pc='host',label='Host')]
    env['farming_targets']=NS(resolve=lambda payload:rows)
    env['missions']=NS(_engine=lambda:NS(profile=profile),_binding=lambda party:'fixed')
    env['mission_dlc']=NS(inspect=lambda party,engine:dict())
    result=driver.preflight(character=False)
    assert any('catalogs still come from 1.10' in limit for limit in result['limits']) is warning


def test_challenge_readback_retains_incomplete_names_after_unavailable_samples():
    from types import SimpleNamespace as NS
    driver,_=character_driver();env=driver.poll.__globals__
    env['backend']=NS(complete_challenges_status=lambda:dict(active=False,failed_count=0,message='Done'),
                      _full_progress_queue_guard=None,_challenge_retry_failed=False)
    env['missions']=NS(_engine=lambda:'engine')
    names=[f'Unavailable_{i}' for i in range(25)]+['ActuallyIncomplete']
    env['challenge_stub']=NS(inspect_batch=lambda engine,pc,batch:[dict(name=n,
        exists=n=='ActuallyIncomplete',complete=False) for n in batch])
    child=dict(kind='challenges',names=names,skipped=0)
    result=driver.poll('challenges',child,dict(rows=[dict(pc='host',label='Host')]))
    assert result['state']=='partial'
    assert result['child']['readback']['incomplete']==1
    assert result['child']['readback']['incomplete_names']==[
        dict(player='Host',challenge='ActuallyIncomplete')]
    assert len(result['child']['readback']['samples'])==20


def test_read_only_challenge_audit_pages_native_state_without_grants():
    import ast
    from types import SimpleNamespace as NS
    source=(P.parent/'full_progress_runtime.py').read_text().replace(
        'from . import challenge_objective_complete','challenge_objective_complete = challenge_stub')
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='challenge_audit')
    names=[f'Challenge_{i}' for i in range(70)]
    calls=[]
    def inspect(engine,pc,batch):
        calls.append((pc,tuple(batch)))
        return [dict(name=n,exists=True,complete=n!='Challenge_63') for n in batch]
    env=dict(Driver=lambda:NS(preflight=lambda **kwargs:dict(rows=[dict(pc='host',label='Host')],players=['Host'],binding='same-lobby')),
             challenge_plan=lambda snapshot:dict(selected=[(n,1) for n in names]),
             missions=NS(_engine=lambda:'engine'),challenge_stub=NS(inspect_batch=inspect))
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<challenge-audit>','exec'),env)
    result=env['challenge_audit'](dict(offset=0))
    assert result['next_offset']==64 and result['total']==70
    assert result['binding']=='same-lobby'
    assert result['rows']==[dict(player='Host',challenge='Challenge_63',state='incomplete')]
    assert len(calls)==1 and len(calls[0][1])==64
    assert env['challenge_audit'](dict(offset=64))['next_offset'] is None


def test_exact_challenge_probe_restricts_catalog_and_reads_both_players():
    import ast
    from types import SimpleNamespace as NS
    source=(P.parent/'full_progress_runtime.py').read_text().replace(
        'from . import challenge_objective_complete','challenge_objective_complete = challenge_stub')
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='challenge_probe')
    calls=[]
    def inspect(engine,pc,names):
        calls.append((pc,tuple(names)))
        return [dict(challenge=name,native_complete=False) for name in names]
    env=dict(Driver=lambda:NS(preflight=lambda **kwargs:dict(
        rows=[dict(pc='host',label='Host'),dict(pc='guest',label='Guest')],
        players=['Host','Guest'],binding='same-lobby')),
        challenge_plan=lambda snapshot:dict(selected=[('Allowed',1)]),
        missions=NS(_engine=lambda:'engine'),challenge_stub=NS(inspect_exact_progress=inspect))
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<challenge-probe>','exec'),env)
    result=env['challenge_probe'](dict(challenge_ids=['Allowed']))
    assert result['ok'] and len(result['results'])==2
    assert calls==[('host',('Allowed',)),('guest',('Allowed',))]
    with pytest.raises(ValueError,match='outside'):
        env['challenge_probe'](dict(challenge_ids=['Unknown']))
    assert len(calls)==2


def test_exact_challenge_record_probe_reads_goal_and_relationship_without_writes():
    import ast
    import struct
    from types import SimpleNamespace as NS
    source=(P.parent/'challenge_objective_complete.py').read_text()
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)
              and n.name=='inspect_exact_progress')
    node.body=[item for item in node.body if not isinstance(item,ast.ImportFrom)]
    def sparse(engine,address,stride,maximum):
        return {1000+0x290:[2000,2100],1000+0x2e0:[4000],
                1000+0x3d8:[8000],8008:[8100,8200]}[address]
    pointers={2008:3000,2108:3100,4000:3000,4500:3100,3000:6000,3100:6100,
              6000+0x498:7000,6100+0x498:0,7000:5,
              8100:3000,8108:9000,8200:3100,8208:9100}
    def read(address,size):
        values={2000:b'aaaaaaaa',2100:b'bbbbbbbb',5000+0x394:struct.pack('<i',2),
                8000:struct.pack('<i',2),6000+0x160:b'\x0e'+b'\0'*7,
                6100+0x160:b'\x01'+b'\0'*7,6000+0x4a0:b'\x01',
                6100+0x4a0:b'\x00',
                6000+0x120:b'\x01'*16+struct.pack('<Q',1234),
                6100+0x120:b'\0'*24,9000:struct.pack('<q',1),
                9100:struct.pack('<q',0),
                9000+0x10:bytes.fromhex('00000000ffffffff3d05000000000000010000000000000001000000'),
                9100+0x10:bytes.fromhex('00000000ffffffffffffffff00000000000000000000000001000000')}
        return values[address][:size]
    engine=NS(profile='steam-26007962',ensure_world=lambda:None,
              read=read,u64=lambda address:pointers[address],
              array=lambda address,maximum:(4500,1))
    pc=NS(PlayerState=NS(_get_address=lambda:5000,PlayerId=2),Pawn=object(),
          OakChallengeManager=NS(_get_address=lambda:1000),HasAuthority=lambda:True)
    lib=NS(GetChallengeProgressForPlayer=lambda **kwargs:1,
           IsChallengeCompleteForPlayer=lambda **kwargs:False)
    env=dict(sparse_entries=sparse,_name=lambda engine,name:(b'aaaaaaaa' if name=='A' else b'bbbbbbbb'),
             FGameDataHandle=lambda *args:args,_library=lambda:lib)
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<exact-progress>','exec'),env)
    result=env['inspect_exact_progress'](engine,pc,['A','B'])
    assert result[0]['definition_type']==14 and result[0]['final_goal']==5
    assert result[0]['related_parents']==[dict(challenge='B',definition_type=1)]
    assert result[0]['gate_18']==1341 and result[0]['gate_28']==1
    assert result[0]['linked_reference_cached'] is True
    assert result[1]['linked_reference_cached'] is False
    assert result[1]['tier_count']==0 and result[1]['final_goal'] is None


def test_fact_trigger_plan_uses_exact_native_shortfall_and_skips_other_types():
    import ast
    from types import SimpleNamespace as NS
    source=(P.parent/'full_progress_runtime.py').read_text().replace(
        'from . import challenge_objective_complete','challenge_objective_complete = challenge_stub')
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)
              and n.name=='fact_trigger_plan')
    inspected=[]
    def inspect(engine,pc,names):
        inspected.append((pc,tuple(names)))
        return [dict(challenge=name,exists=True,progress_present=True,
                     definition_type=14 if name=='Bridge' else 1,
                     tier_count=1,final_goal=2,native_count=1,record_count=1,
                     gate_11=0,gate_18=1341,gate_28=1) for name in names]
    env=dict(missions=NS(_engine=lambda:NS(profile='steam-26007962')),
             challenge_stub=NS(inspect_exact_progress=inspect))
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<fact-plan>','exec'),env)
    snapshot=dict(rows=[dict(pc='host',label='Host')])
    plan,issues=env['fact_trigger_plan'](snapshot,[
        dict(player='Host',challenge='Bridge'),dict(player='Host',challenge='Parent')])
    assert plan==[dict(player='Host',challenge='Bridge',amount=1,expected_goal=2)]
    assert issues==[] and inspected==[('host',('Bridge','Parent'))]
    assert env['fact_trigger_plan'](snapshot,[])==([],[])


def test_fact_trigger_repair_issues_once_then_rechecks_without_repeating():
    from types import SimpleNamespace as NS
    driver,_=character_driver();env=driver.fact_trigger_repair.__globals__
    calls=[]
    env['fact_trigger_plan']=lambda snapshot,incomplete:([
        dict(player='Host',challenge='Bridge',amount=1,expected_goal=2)],[])
    def inspect(engine,pc,names):
        return [dict(challenge='Bridge',definition_type=14,final_goal=2,
            record_count=2 if calls else 1,native_count=2 if calls else 1,
            native_complete=bool(calls),gate_11=0,gate_18=1341,gate_28=1)]
    env['challenge_stub']=NS(inspect_exact_progress=inspect)
    env['missions']=NS(_engine=lambda:'engine',_binding=lambda rows:'bound')
    env['farming_targets']=NS(resolve=lambda payload:['host'])
    backend=NS(_full_progress_queue_guard=None,_challenge_retry_failed=True,
        _challenge_queue_start=lambda rows,**kwargs:calls.append((rows,kwargs)) or dict(ok=True),
        complete_challenges_status=lambda:dict(active=False,failed_count=0,message='Done'))
    env['backend']=backend
    snapshot=dict(rows=[dict(pc='host',label='Host')],binding='bound')
    child=dict(readback=dict(incomplete_names=[dict(player='Host',challenge='Bridge')]))
    first=driver.fact_trigger_repair(child,snapshot)
    assert first['state']=='running' and calls[0][0]==[('Bridge',1)]
    assert calls[0][1]['targets']==['host']
    second=driver.fact_trigger_repair(child,snapshot)
    assert second['state']=='running' and child['fact_repair_done']
    assert 'readback' not in child and len(calls)==1
    assert driver.fact_trigger_repair(child,snapshot) is None


def test_mission_credit_plan_requires_live_rules_and_completed_shared_records():
    import ast
    from types import SimpleNamespace as NS
    source=(P.parent/'full_progress_runtime.py').read_text().replace(
        'from . import mission_challenges','mission_challenges = credit_stub')
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef)
              and n.name=='mission_credit_plan')
    definitions=[dict(challenge='Valid',missions=['A','B']),
                 dict(challenge='Changed',missions=['C'])]
    def read(engine,pc,definition):
        if definition['challenge']=='Changed':raise RuntimeError('Mission credit counting rules changed')
        return dict(credited={0,1} if pc=='host' else {0})
    credit=NS(MISSION_CREDIT_CATALOG=dict(entries=definitions),
              credit_definition=lambda challenge:next(d for d in definitions if d['challenge']==challenge),
              read_player=read)
    engine=NS(snapshot=lambda:dict(missions=[]))
    env=dict(credit_stub=credit,missions=NS(_engine=lambda:engine,
             _row=lambda snapshot,name:dict(name=name),_state=lambda row:'completed'),
             challenge_plan=lambda snapshot:dict(selected=[('Valid',1),('Changed',1)]),
             mission_dlc=NS(requirement=lambda name,packs:None))
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<credit-plan>','exec'),env)
    plan,issues=env['mission_credit_plan'](dict(rows=[dict(pc='host'),dict(pc='guest')],packs={}))
    assert plan==[dict(challenge='Valid',missions=['B'])]
    assert issues==[dict(challenge='Changed',reason='Mission credit counting rules changed')]


def test_full_game_repairs_only_planned_missing_mission_credit_before_readback():
    from types import SimpleNamespace as NS
    driver,_=character_driver();env=driver.mission_credit_repair.__globals__
    started=[];polled=[]
    env['mission_credit_plan']=lambda snapshot:([dict(challenge='Reviewed',missions=['B'])],[])
    env['missions']=NS(start=lambda payload,**kwargs:started.append((payload,kwargs)) or dict(id='child',state='running'),
                       poll=lambda ident:polled.append(ident) or dict(id=ident,state='completed'))
    snapshot=dict(rows=[dict(host=True,index=0,label='Host')],binding='fixed')
    child=dict(kind='challenges')
    first=driver.mission_credit_repair(child,snapshot)
    assert first['state']=='running' and child['credit_active']['id']=='child'
    assert started[0][0]['scope']=='challenge_credit'
    assert started[0][0]['missions']==['B'] and started[0][0]['challenge_id']=='Reviewed'
    assert started[0][1]==dict(use_objective_graph=False)
    assert driver.mission_credit_repair(child,snapshot) is None
    assert polled==['child'] and child['credit_done'] and not child['credit_issues']


def test_full_game_skips_unstartable_credit_group_without_repeating_it():
    from types import SimpleNamespace as NS
    driver,_=character_driver();env=driver.mission_credit_repair.__globals__
    calls=[]
    env['mission_credit_plan']=lambda snapshot:([dict(challenge='Reviewed',missions=['B'])],[])
    def fail(*args,**kwargs):
        calls.append(True);raise ValueError('Mission completion changed')
    env['missions']=NS(start=fail)
    snapshot=dict(rows=[dict(host=True,index=0,label='Host')],binding='fixed')
    child=dict(kind='challenges')
    assert driver.mission_credit_repair(child,snapshot)['state']=='running'
    assert driver.mission_credit_repair(child,snapshot) is None
    assert len(calls)==1 and child['credit_done']
    assert child['credit_issues']==[dict(challenge='Reviewed',reason='Mission completion changed')]


def test_full_game_cancel_waits_for_issued_mission_credit():
    from types import SimpleNamespace as NS
    driver,_=character_driver();env=driver.cancel.__globals__
    cancelled=[]
    env['missions']=NS(cancel=lambda ident:dict(state='running'))
    env['backend']=NS(complete_challenges_cancel=lambda:cancelled.append('bulk'))
    child=dict(kind='challenges',credit_active=dict(id='child',challenge='Reviewed'))
    assert driver.cancel(child) is False and child['credit_active']['id']=='child'
    assert not cancelled
    env['missions']=NS(cancel=lambda ident:dict(state='cancelled'))
    assert driver.cancel(child) is True and child['credit_active'] is None
    assert cancelled==['bulk']


@pytest.mark.parametrize('state',['uncertain','interrupted'])
def test_full_game_cancel_keeps_credit_receipt_until_recovery_closes_it(state):
    from types import SimpleNamespace as NS
    driver,_=character_driver();env=driver.cancel.__globals__
    closed=[];cancelled=[]
    env['missions']=NS(cancel=lambda ident:dict(state=state),
        recover=lambda payload:closed.append(payload) or dict(closed=False))
    env['backend']=NS(complete_challenges_cancel=lambda:cancelled.append('bulk'))
    child=dict(kind='challenges',credit_active=dict(id='child',challenge='Reviewed'))
    assert driver.cancel(child) is False
    assert child['credit_active']['id']=='child' and not cancelled
    assert closed==[dict(job_id='child',mode='close',acknowledge_shared_progress=True)]
    env['missions'].recover=lambda payload:dict(closed=True)
    assert driver.cancel(child) is True
    assert child['credit_active'] is None and cancelled==['bulk']


def test_full_game_recovery_closes_uncertain_credit_without_reissuing():
    from types import SimpleNamespace as NS
    driver,_=character_driver();env=driver.recover.__globals__;calls=[]
    env['missions']=NS(status=lambda:dict(id='child',state='uncertain'),
        recover=lambda payload:calls.append(payload) or dict(closed=True))
    child=dict(kind='challenges',credit_active=dict(id='child',challenge='Reviewed'),
               credit_index=0)
    driver.recover(child,dict(rows=[]))
    assert calls==[dict(job_id='child',mode='close',acknowledge_shared_progress=True)]
    assert child['credit_active'] is None and child['credit_index']==1
    assert child['credit_issues'][0]['challenge']=='Reviewed'


@pytest.mark.parametrize('action',[
    'full_progress_challenge_audit','full_progress_mission_credit_probe',
    'full_progress_challenge_probe'])
def test_challenge_audit_is_reachable_through_bridge(action):
    from test_bridge_perf_bounds import _load_bridge
    bridge=_load_bridge();calls=[]
    bridge.backend_actions.run_quick_menu_action=lambda action,payload,record=False:(
        calls.append((action,payload,record)) or dict(ok=True,rows=[]))
    result=bridge._handle_action(action,dict(offset=64))
    assert result['ok'] and calls==[(action,dict(offset=64),False)]
    assert action in bridge._PROGRESS_JOB_ACTIONS


def test_interrupted_full_run_closes_only_matching_mission_receipt():
    from types import SimpleNamespace as NS
    d,_=character_driver();env=d.close_interrupted.__globals__;calls=[]
    env['missions']=NS(status=lambda:dict(state='interrupted',id='owned'),
        recover=lambda payload:calls.append(payload))
    events=[dict(event='observed',result=dict(child=dict(kind='mission',id='owned')))]
    d.close_interrupted(events)
    assert calls==[dict(job_id='owned',mode='close',acknowledge_shared_progress=True)]
    calls.clear()
    with pytest.raises(RuntimeError,match='does not match'):
        d.close_interrupted([dict(child=dict(kind='mission',id='other'))])
    assert not calls


@pytest.mark.parametrize('child',[
    dict(kind='challenges',credit_active=dict(id='owned',challenge='Credit')),
    dict(kind='final_recheck',active=dict(stage='missions',child=dict(kind='mission',id='owned'))),
])
def test_interrupted_full_run_closes_nested_mission_receipt(child):
    from types import SimpleNamespace as NS
    d,_=character_driver();env=d.close_interrupted.__globals__;calls=[]
    env['missions']=NS(status=lambda:dict(state='interrupted',id='owned'),
        recover=lambda payload:calls.append(payload))
    d.close_interrupted([dict(event='stopped',child=child)])
    assert calls==[dict(job_id='owned',mode='close',acknowledge_shared_progress=True)]


def test_interrupted_full_run_does_not_use_stale_earlier_child():
    from types import SimpleNamespace as NS
    d,_=character_driver();env=d.close_interrupted.__globals__;calls=[]
    env['missions']=NS(status=lambda:dict(state='interrupted',id='owned'),
        recover=lambda payload:calls.append(payload))
    events=[dict(event='observed',result=dict(child=dict(kind='mission',id='owned'))),
            dict(event='stopped',child=dict(kind='challenges',credit_active=None))]
    with pytest.raises(RuntimeError,match='does not match'):
        d.close_interrupted(events)
    assert not calls


def test_full_game_releases_only_uncertain_paused_uvh():
    from types import SimpleNamespace as NS
    driver,_=character_driver()
    env=driver.check_idle.__globals__
    env['missions']=NS(status=lambda:{'state':'idle'})
    uvh=dict(active=False,paused_steps=25,uncertain=True)
    cleared=[]
    env['backend']=NS(complete_challenges_status=lambda:{'active':False},
                      uvh_boost_status=lambda:uvh.copy(),
                      uvh_boost_discard_paused=lambda **kwargs:cleared.append(True) or dict(ok=True,discarded_steps=25))
    driver.check_idle()
    assert driver.prepare_start()==[dict(ok=True,kind='uvh',discarded_steps=25)] and cleared
    uvh['uncertain']=False
    with pytest.raises(RuntimeError,match='Finish or cancel'):
        driver.check_idle()
    assert len(cleared)==1


def test_full_game_override_stops_pending_work_before_start(tmp_path):
    from types import SimpleNamespace as NS
    driver,_=character_driver()
    env=driver.check_idle.__globals__
    mission=dict(id='old',state='running')
    challenge=dict(active=True,steps_remaining=4)
    uvh=dict(active=False,paused_steps=25,uncertain=False)
    calls=[]
    def stop_mission(ident):
        assert ident=='old';calls.append('mission');mission['state']='cancelled'
        return dict(state='cancelled',message='Remaining mission work cancelled')
    def stop_challenge():
        calls.append('challenge');challenge['active']=False
        return dict(message='Challenges cancelled')
    def discard_uvh(**kwargs):
        assert kwargs['allow_manual'];calls.append('uvh');uvh['paused_steps']=0
        return dict(ok=True,message='Paused UVHM closed',discarded_steps=25)
    env['missions']=NS(status=lambda:mission.copy(),cancel=stop_mission)
    env['backend']=NS(complete_challenges_status=lambda:challenge.copy(),complete_challenges_cancel=stop_challenge,
                      uvh_boost_status=lambda:uvh.copy(),uvh_boost_discard_paused=discard_uvh)
    notes=driver.prepare_start(replace_other_progress=True)
    driver.check_idle()
    assert calls==['mission','challenge','uvh']
    assert [n['kind'] for n in notes]==['mission','challenges','uvh']


def test_campaign_challenges_precede_uvhm_unlocks():
    stages=[name for name,title in m.STAGES]
    assert stages.index('missions') < stages.index('challenges') < stages.index('uvh')
    import json
    policy=json.loads((P.parent/'full_progress_policy.json').read_text(encoding='utf-8'))
    assert policy['challenges']['Challenge_Misc_World_CompleteCityEpilogue']['packs']==[]


def test_character_resolution_skips_possessed_vehicle_and_checks_state():
    import ast
    from types import SimpleNamespace as NS
    source=(P.parent/'player_economy.py').read_text(encoding='utf-8')
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='_target_character_for_pc')
    env=dict(Any=object,Optional=__import__('typing').Optional)
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<character>','exec'),env)
    character=NS(GbxProgressionManager=object())
    vehicle=NS()
    resolve=env['_target_character_for_pc']
    assert resolve(NS(Pawn=vehicle,Character=character)) is character
    assert resolve(NS(Pawn=vehicle,PlayerState=NS(PawnPrivate=character))) is character
    assert resolve(NS(Pawn=vehicle)) is None


def test_locked_guest_campaign_skips_uvhm_without_requests_or_timeout():
    from types import SimpleNamespace as NS
    d,_=character_driver();env=d.begin.__globals__;calls=[]
    env['challenge_stub']=NS(is_complete=lambda pc,name: pc=='host')
    env['backend']=NS(_uvh_queue_for_pc=lambda *a: calls.append(a))
    result=d.begin('uvh',dict(rows=[dict(pc='host',label='Host'),dict(pc='guest',label='Guest')]))
    assert result['state']=='partial' and result['skipped']==['Guest'] and not calls
    assert 'Continuing remaining work' in result['message']


def test_unlocked_party_queues_uvhm_only_after_all_campaign_checks():
    from types import SimpleNamespace as NS
    d,_=character_driver();env=d.begin.__globals__;events=[]
    def complete(pc,name):events.append(('check',pc));return True
    def queue(pc,ranks):events.append(('queue',pc));return True,'Ready'
    env['challenge_stub']=NS(is_complete=complete)
    env['backend']=NS(_uvh_queue_for_pc=queue,UVH_RANKS=['rank1'])
    result=d.begin('uvh',dict(binding='lobby',rows=[dict(pc='host',label='Host'),dict(pc='guest',label='Guest')]))
    assert result['state']=='running'
    assert events==[('check','host'),('check','guest'),('queue','host'),('queue','guest')]


def test_character_tops_up_delta_and_never_reduces_existing_progress():
    d,calls=character_driver()
    row=dict(pc='guest',state='guest_state',label='Guest')
    sample=dict(level=80,specialization=800,currencies={'Cash':900,'eridium':1000},vault_cards=[])
    result=d.character(row,sample,{'packs':{'missing':{'allowed':False}}})
    assert calls==[('currency','guest','Cash',100)]
    assert result['skipped'] and not result['completion_verified']


def test_full_progress_preserves_solo_completion_without_assuming_guest_credit():
    d,_=character_driver()
    host=dict(host=True,index=0,label='Host')
    guest=dict(host=False,index=1,label='Guest')
    assert d.acceptance(dict(rows=[host]))['preserve_completed'] is True
    payload=d.acceptance(dict(rows=[host,guest]))
    assert payload['preserve_completed'] is False and payload['target_player']=='1|Guest'


def test_full_progress_initial_missions_use_original_bulk_completion():
    d,_=character_driver();calls=[];missions=d.begin.__globals__['missions']
    def start(payload,*,use_objective_graph=True):
        calls.append((payload,use_objective_graph));return dict(id='bulk',state='completed',message='Done')
    missions.start=start
    result=d.begin('missions',dict(access_refreshed=True,rows=[dict(host=True,index=0,label='Host')]))
    assert result['state']=='finished' and len(calls)==1
    assert calls[0][0]['scope']=='all' and calls[0][1] is False


def test_full_game_defers_inconsistent_preexisting_credit_without_claiming_completion():
    d,_=character_driver()
    acceptance=d.acceptance(dict(rows=[dict(host=True,index=0,label='Host')]))
    assert acceptance['defer_unconfirmed_mission_credit'] and acceptance['continue_on_mission_failure']
    result=d.mission_result(dict(state='completed',message='Missions verified',
        unverified_challenge_credit=[dict(mission='mission_main_cityepilogue',reason='Native records disagree')]),
        dict(kind='mission',id='job'))
    assert result['state']=='partial'
    assert len(result['details']['unverified_challenge_credit'])==1


def test_full_game_marks_quarantined_mission_operation_partial():
    d,_=character_driver()
    result=d.mission_result(dict(state='completed',message='Mission batch finished',
        unverified_operations=[dict(mission='Mission_Main_Beach',operation='switch_toggle')]),
        dict(kind='mission',id='job'))
    assert result['state']=='partial'
    assert result['details']['unverified_operations'][0]['operation']=='switch_toggle'


def test_final_credit_recheck_records_persistent_mismatch_and_moves_on():
    from types import SimpleNamespace as NS
    d,_=character_driver();env=d.final_recheck.__globals__;calls=[]
    mismatch=env['credit_stub'].CreditReadbackMismatch
    def inspect_credit(*args):
        calls.append(True)
        raise mismatch('Native records still disagree')
    env['credit_stub'].credit_completed=inspect_credit
    env['missions']=NS(_engine=lambda:NS(snapshot=lambda:{}),
        _row=lambda snapshot,name:dict(state='completed'),_state=lambda row:row['state'],
        CATALOG={'mission_main_cityepilogue':dict(title='Secrets of the Vault')})
    child=dict(kind='final_recheck',done=[],attempted=[],active=None,mayhem_done=True,
        results=[],wait_since=0,credit_pending=[dict(mission='mission_main_cityepilogue')],
        credit_index=0,credit_active=None,credit_unverified=[])
    result=d.final_recheck(child,dict(rows=['host']))
    assert result['state']=='running' and child['credit_index']==1
    assert len(child['credit_unverified'])==1 and len(calls)==1


def test_full_progress_refreshes_access_before_any_mission_start():
    from types import SimpleNamespace as NS
    d,_=character_driver();env=d.begin.__globals__
    env['refresh_stub']=NS(begin=lambda rows:dict(kind='access_refresh',id='refresh'))
    env['missions'].start=lambda *a,**k:pytest.fail('Must wait for refreshed access')
    result=d.begin('missions',dict(rows=['guest']))
    assert result['state']=='running' and result['child']['kind']=='access_refresh'


def test_refresh_ack_rechecks_native_access_before_bulk_start():
    from types import SimpleNamespace as NS
    d,_=character_driver();env=d.poll.__globals__;events=[]
    env['refresh_stub']=NS(ready=lambda token,rows:events.append('ack') or True)
    fresh=dict(binding='same',rows=[dict(host=True,index=0,label='Host')],packs={'paid':{'allowed':False}})
    d.preflight=lambda **kwargs:events.append('fresh access') or dict(fresh)
    d.begin=lambda stage,snapshot:events.append(('start',snapshot['packs']['paid']['allowed'],snapshot['access_refreshed'])) or dict(state='finished')
    assert d.poll('missions',dict(kind='access_refresh',id='r'),dict(binding='same',rows=[]))['state']=='finished'
    assert events==['ack','fresh access',('start',False,True)]


def test_pending_refresh_never_starts_missions():
    from types import SimpleNamespace as NS
    d,_=character_driver();env=d.poll.__globals__
    env['refresh_stub']=NS(ready=lambda *a:False)
    d.begin=lambda *a:pytest.fail('No mission work before guest acknowledgement')
    assert d.poll('missions',dict(kind='access_refresh',id='r'),dict(rows=[]))['state']=='running'


def test_reported_skips_follow_refreshed_access(tmp_path):
    d=Driver(owned=True);d.step_snapshot=lambda stage:d.preflight()
    runner=m.Run(d,tmp_path);job=runner.start({'acknowledge_shared_progress':True})
    assert runner.status()['skipped']==[]
    d.owned=False
    assert runner.step(job['id'])['skipped'][0]['title']=='DLC'


def test_missing_currency_readback_blocks_grant():
    d,calls=character_driver()
    with pytest.raises(RuntimeError,match='balance'):
        d.character(dict(pc='guest',state='state',label='Guest'),
                    dict(level=70,specialization=701,currencies={},vault_cards=[]),{'packs':{'x':{'allowed':False}}})
    assert not calls


def test_optional_unavailable_catalog_entry_does_not_block_multi_guest():
    gate=m.eligibility(['Host','A','B'],{'paid':dict(allowed=True,title='Paid',reason=''),
                       'optional':dict(allowed=False,required=False,title='Catalog entry',reason='Unavailable')})
    assert gate['allowed'] and gate['skipped'][0]['title']=='Catalog entry'


def test_native_access_fingerprint_mismatch_prevents_native_call(monkeypatch):
    import importlib.resources,sys
    from types import SimpleNamespace as NS
    monkeypatch.setattr(importlib.resources,'files',lambda package:P.parent)
    monkeypatch.setitem(sys.modules,'unrealsdk',NS())
    spec=importlib.util.spec_from_file_location('access_test',P.parent/'progress_access.py')
    from tools.tests.mission_profile_fixture import exec_with_profiles
    access=importlib.util.module_from_spec(spec);exec_with_profiles(spec,access,monkeypatch)
    engine=NS(profile='steam-25372571',base=0,ensure_world=lambda:None,read=lambda addr,n:b'\0'*n)
    with pytest.raises(RuntimeError,match='reviewed game build'):access.inspect(engine,[])


def test_compact_status_keeps_results_and_unavailable_without_growing_catalogs():
    value=dict(results=[dict(details=dict(names=['a']*1000,completed=['a']*500,pending=['locked'],message='ok'))])
    result=m.compact_status(value)['results'][0]['details']
    assert result==dict(names_count=1000,completed_count=500,pending=['locked'],message='ok')
    assert len(value['results'][0]['details']['names'])==1000


def test_stage_snapshot_still_checks_binding(tmp_path):
    d=Driver();seen=[]
    def snapshot(stage):seen.append(stage);return d.preflight()
    d.step_snapshot=snapshot
    r=m.Run(d,tmp_path);j=r.start({'acknowledge_shared_progress':True});d.binding='changed'
    assert r.step(j['id'])['state']=='stopped'
    assert seen==['missions'] and not d.calls


@pytest.mark.parametrize('stage',['missions','map_locations','travel_stations','travel_requirements'])
def test_full_progress_uses_shared_mission_pump(stage):
    from types import SimpleNamespace as NS
    d,_=character_driver();env=d.poll.__globals__;calls=[]
    env['missions']=NS(poll=lambda ident:calls.append(ident) or dict(state='uncertain'))
    assert d.poll(stage,dict(kind='mission',id='child'),{})['state']=='uncertain'
    assert calls==['child']


@pytest.mark.parametrize('raises',[False,True])
def test_vault_card_level_failure_is_reported_and_other_progress_continues(raises):
    from types import SimpleNamespace as NS
    d,calls=character_driver();env=d.character.__globals__
    def level(*args):
        if raises:raise RuntimeError('Inactive card')
        return False
    env['economy']._set_owned_vault_card_level=level
    row=dict(pc='guest',state=NS(PlayerId=2),label='Guest')
    sample=dict(level=70,specialization=701,currencies={'Cash':900,'eridium':1000,'VaultCard02_Tokens':1000},vault_cards=[dict(card=2,rank=0)])
    snapshot=dict(packs={'vaultcard2':dict(allowed=False,players=[dict(player_id=2,access='enabled')])})
    result=d.character(row,sample,snapshot)
    assert any('level not confirmed after activation' in s for s in result['skipped'])
    assert calls==[('currency','guest','Cash',100)]


def test_full_run_levels_only_owned_incomplete_cards_for_that_player():
    from types import SimpleNamespace as NS
    d,calls=character_driver()
    row=dict(pc='guest',state=NS(PlayerId=2),label='Guest')
    sample=dict(level=70,specialization=701,currencies={'Cash':1000,'eridium':1000,
        'VaultCard01_Tokens':1000,'VaultCard03_Tokens':1000},vault_cards=[
        dict(card=1,rank=25),dict(card=2,rank=25),dict(card=3,rank=10000)])
    def pack(player):return dict(allowed=False,players=[dict(player_id=player,access='enabled')])
    snapshot=dict(packs={'banjo':pack(2),'vaultcard2':pack(1),'vaultcard3':pack(2)})
    result=d.character(row,sample,snapshot)
    assert calls==[('card_level','guest',1,9999)]
    assert result['currencies']==['Cash','eridium','VaultCard01_Tokens','VaultCard03_Tokens']
    assert result['vault_cards']==[1,3]


def test_character_rechecks_card_rank_after_restoring_selection_without_reissuing():
    import time
    d,calls=character_driver()
    result=dict(player='Host',currencies=[],vault_cards=[1],issued_at=time.time(),skipped=[])
    child=dict(kind='character',index=0,results=[],pending=result)
    sample=dict(level=70,specialization=701,currencies={},vault_cards=[dict(card=1,rank=25)])
    snapshot=dict(rows=[{'pc': 'host'}],samples=[sample])
    assert d.poll('character',child,snapshot)['state']=='running'
    result['issued_at']=time.time()-11
    with pytest.raises(RuntimeError,match='readback'):d.poll('character',child,snapshot)
    assert child['index']==0 and not calls
    sample['vault_cards'][0]['rank']=9999
    assert d.poll('character',child,snapshot)['state']=='finished'
    assert not calls


def test_character_waits_for_sdu_purchases_and_recovers_without_repeating_grants():
    import time
    d,calls=character_driver();env=d.poll.__globals__;polls=[]
    def advance(pc, runtime, state):
        polls.append(pc)
        state.update(completed=len(polls),total=59)
        if len(polls)==2:raise RuntimeError('SDU purchase not confirmed; request not repeated')
        return len(polls)>2
    env['sdu_stub'].advance=advance
    result=dict(player='Host',currencies=[],vault_cards=[],issued_at=time.time(),skipped=[],sdu={})
    child=dict(kind='character',index=0,results=[],pending=result)
    sample=dict(level=70,specialization=701,currencies={},vault_cards=[])
    snapshot=dict(rows=[{'pc':'host'}],samples=[sample])
    assert d.poll('character',child,snapshot)['state']=='running'
    with pytest.raises(RuntimeError,match='not repeated'):d.poll('character',child,snapshot)
    d.recover(child,snapshot)
    assert child['index']==0 and child['pending'] is result
    assert d.poll('character',child,snapshot)['state']=='finished'
    assert not calls and polls==['host']*3


def test_full_run_stops_on_card_restore_failure_before_other_grants():
    from types import SimpleNamespace as NS
    d,calls=character_driver();economy=d.character.__globals__['economy']
    def level(*args):raise economy.VaultCardRestoreError('VaultCard05')
    economy._set_owned_vault_card_level=level
    row=dict(pc='host',state=NS(PlayerId=2),label='Host')
    sample=dict(level=70,specialization=701,currencies={'Cash':0,'eridium':0},
                vault_cards=[dict(card=1,rank=25),dict(card=2,rank=25)])
    pack=dict(allowed=False,players=[dict(player_id=2,access='enabled')])
    with pytest.raises(economy.VaultCardRestoreError,match='restore VaultCard05'):
        d.character(row,sample,dict(packs={'banjo':pack,'vaultcard2':pack}))
    assert not calls


def test_resume_requires_original_card_restored_and_does_not_repeat_grants():
    from types import SimpleNamespace as NS
    d,calls=character_driver();economy=d.character.__globals__['economy']
    def level(*args):raise economy.VaultCardRestoreError('VaultCard05')
    economy._set_owned_vault_card_level=level
    selected=NS(_name='VaultCard01')
    row=dict(pc=NS(VaultCardsManager=NS(ActivatedVaultCardDef=selected)),state=NS(PlayerId=2),label='Host')
    sample=dict(level=70,specialization=701,currencies={'Cash':0,'eridium':0},vault_cards=[dict(card=1,rank=25)])
    pack=dict(allowed=False,players=[dict(player_id=2,access='enabled')])
    snapshot=dict(rows=[row],samples=[sample],packs={'banjo':pack})
    child=dict(kind='character',index=0,results=[])
    with pytest.raises(economy.VaultCardRestoreError):d.poll('character',child,snapshot)
    assert child['restore_required']==dict(card='VaultCard05',player_id=2)
    with pytest.raises(RuntimeError,match='before resuming'):d.recover(child,snapshot)
    assert child['index']==0 and not calls
    selected._name='VaultCard05'
    row['state'].PlayerId=3
    with pytest.raises(RuntimeError,match='before resuming'):d.recover(child,snapshot)
    row['state'].PlayerId=2
    d.recover(child,snapshot)
    assert child['index']==1 and 'restore_required' not in child
    assert d.poll('character',child,snapshot)['state']=='partial'
    assert not calls


def final_driver(states,done=()):
    from types import SimpleNamespace as NS
    d,_=character_driver();env=d.final_recheck.__globals__;starts=[]
    def start(payload,*,use_objective_graph=True):
        assert use_objective_graph is False
        starts.append(payload.copy());return dict(id='child',state='running')
    env['missions']=NS(CATALOG={n:dict(title=n) for n in states},NONPERSISTENT=set(),
        _engine=lambda:NS(snapshot=lambda:states),_row=lambda s,n:s[n],_state=lambda r:r,
        _automatic_exclusion=lambda s,n:None,start=start)
    env['mission_dlc']=NS(requirement=lambda n,p:None)
    env['discovery_stub']=NS(plan=lambda *a:[])
    env['time']=NS(monotonic=lambda:20)
    d.acceptance=lambda s:dict(reset_completed=True)
    child=dict(kind='final_recheck',done=list(done),attempted=[],active=None,mayhem_done=True,results=[],wait_since=0)
    return d,child,starts


def test_final_pass_selects_newly_unlocked_without_resetting_completed():
    d,child,starts=final_driver({'done':'completed','new':'available','locked':'locked'})
    assert d.final_recheck(child,dict(packs={}))['state']=='running'
    assert starts==[dict(scope='named',missions=['new'],reset_completed=False)]


def test_final_pass_never_replays_earlier_verified_mission_even_if_state_regresses():
    d,child,starts=final_driver({'done':'available'},done=['done'])
    assert d.final_recheck(child,dict(packs={}))['state']=='finished'
    assert not starts


def test_final_pass_reports_still_locked_without_forcing():
    d,child,starts=final_driver({'locked':'locked'})
    result=d.final_recheck(child,dict(packs={}))
    assert result['state']=='partial' and result['skipped'][0]['title']=='locked'
    assert not starts


def test_final_pass_keeps_unknown_issued_operation_unverified_without_retry():
    d,child,starts=final_driver({'Mission_Main_Beach':'available'})
    child['operation_pending']=[dict(mission='Mission_Main_Beach',title='Recruitment Drive',
                                     operation='switch_toggle',issued=True)]
    first=d.final_recheck(child,dict(packs={}))
    assert first['state']=='running' and child['operation_index']==1
    result=d.final_recheck(child,dict(packs={}))
    assert result['state']=='partial'
    assert result['skipped'][0]['title']=='Recruitment Drive'
    assert not starts


def test_final_pass_omits_only_explained_exclusions_and_keeps_other_missing():
    d,child,starts=final_driver({'legacy':'unavailable','missing':'unavailable'})
    d.final_recheck.__globals__['missions']._automatic_exclusion=lambda s,n:'Legacy split' if n=='legacy' else None
    result=d.final_recheck(child,dict(packs={}))
    assert result['state']=='partial'
    assert [row['title'] for row in result['skipped']]==['missing']
    assert not starts


def test_final_pass_uncertain_child_stops_without_reissuing():
    d,child,starts=final_driver({'new':'available'})
    child['active']=dict(stage='missions',child=dict(kind='mission',id='old'))
    d.poll=lambda *a:dict(state='uncertain',message='Unknown')
    assert d.final_recheck(child,dict(packs={}))['state']=='uncertain'
    assert not starts


def test_final_pass_rechecks_dependencies_after_child_completion():
    states={'first':'completed','next':'available'}
    d,child,starts=final_driver(states)
    child['active']=dict(stage='missions',child=dict(kind='mission',id='old'))
    d.poll=lambda *a:dict(state='finished',details=dict(completed=['first']))
    assert d.final_recheck(child,dict(packs={}))['state']=='running'
    assert 'first' in child['done'] and child['active'] is None
    d.final_recheck(child,dict(packs={}))
    assert starts[0]['missions']==['next'] and not starts[0]['reset_completed']


def test_final_credit_callback_must_settle_before_cancel_or_recovery():
    from types import SimpleNamespace as NS
    d,_=character_driver();env=d.cancel.__globals__
    receipt=dict(operation='challenge_credit',player_id=2)
    child=dict(kind='final_recheck',active=None,credit_active=receipt)
    rows=[dict(pc='guest',state=NS(PlayerId=2))]
    env['farming_targets']=NS(resolve=lambda payload:rows)
    env['missions']=NS(_engine=lambda:'engine')
    env['_runner']=NS(record=lambda *a,**kw:None)
    env['backend']=NS(_full_progress_queue_guard=None,_challenge_retry_failed=False)
    calls=[]
    def reconcile(*args):
        calls.append(args[2])
        if len(calls)==1:raise env['credit_stub'].CreditPending('waiting')
    env['credit_stub'].reconcile=reconcile
    assert d.cancel(child) is False and child['credit_active']==receipt
    d.recover(child,dict(rows=rows))
    assert calls==[receipt,receipt] and child['credit_active'] is None
    assert d.cancel(child) is True


def test_resume_keeps_stage_and_never_reissues_begin(tmp_path):
    d=Driver();d.wait=True;d.step_snapshot=lambda stage:d.preflight()
    repaired=[];d.recover=lambda child,snapshot:repaired.append(child)
    r=m.Run(d,tmp_path);j=r.start({'acknowledge_shared_progress':True})
    r.step(j['id'])
    r.job.update(state='uncertain',ok=False)
    r.resume({'job_id':j['id'],'acknowledge_shared_progress':True})
    assert repaired == ['missions']
    assert r.step(j['id'])['index'] == 1
    assert d.calls == ['missions']


def test_resume_failure_preserves_stopped_run(tmp_path):
    d=Driver();d.wait=True;d.step_snapshot=lambda stage:d.preflight()
    def fail(*args):raise RuntimeError('Unresolved native call')
    d.recover=fail
    r=m.Run(d,tmp_path);j=r.start({'acknowledge_shared_progress':True});r.step(j['id'])
    r.job.update(state='uncertain',ok=False)
    with pytest.raises(ValueError):r.resume({'job_id':j['id']})
    with pytest.raises(RuntimeError,match='Unresolved'):r.resume({'job_id':j['id'],'acknowledge_shared_progress':True})
    assert r.job['state']=='uncertain' and d.calls==['missions']
    d.binding='changed'
    with pytest.raises(ValueError,match='lobby'):r.resume({'job_id':j['id'],'acknowledge_shared_progress':True})


def test_resume_observes_map_before_preflight_and_retains_child(tmp_path):
    d=Driver();d.wait=True;r=m.Run(d,tmp_path);j=r.start({'acknowledge_shared_progress':True});r.step(j['id'])
    r.job.update(state='uncertain',ok=False)
    d.step_snapshot=lambda stage:pytest.fail('Cannot read old world during travel')
    d.observe_transition=lambda child,binding:dict(ready=False,message='Loading')
    payload=dict(job_id=j['id'],acknowledge_shared_progress=True)
    assert r.resume(payload)['state']=='uncertain'
    d.binding='verified-world'
    d.observe_transition=lambda child,binding:dict(ready=True,binding=d.binding)
    d.step_snapshot=lambda stage:d.preflight()
    recovered=[];d.recover=lambda child,snapshot:recovered.append(child)
    assert r.resume(payload)['state']=='running'
    assert r.job['binding']=='verified-world' and recovered==['missions'] and d.calls==['missions']


def test_activation_wait_automatically_resumes_without_begin():
    from types import SimpleNamespace as NS
    d,calls=character_driver()
    env=d.mission_result.__globals__
    resumed=[]
    env['missions']=NS(_job={'id':'child','activation_wait':{'mission':'m'},'names':['m'],'index':0},
        _engine=lambda:NS(snapshot=lambda:{}),_row=lambda snapshot,name:{},_state=lambda row:'accepted',
        CATALOG={'m':{'title':'Mission'}},resume=lambda ident:resumed.append(ident) or {'state':'running'},
        _defer=lambda name,reason:resumed.append(('deferred',name)) or {'state':'running'})
    child={'kind':'mission','id':'child'}
    assert d.mission_result({'state':'stopped'},child)['state']=='running'
    assert resumed == [('deferred','m')]
    resumed.clear()
    env['missions']._job['activation_wait']={'mission':'m'}
    env['missions']._state=lambda row:'active'
    assert d.mission_result({'state':'stopped'},child)['state']=='running'
    assert resumed==['child']


def test_four_player_mixed_dlc_lobby_continues_all_eligible_stages_and_lists_skips(tmp_path):
    d=Driver(4,owned=False);r=m.Run(d,tmp_path)
    job=r.start(dict(acknowledge_shared_progress=True))
    assert job['skipped'] and job['state']=='running'
    for _ in m.STAGES:r.step(job['id'])
    assert r.status()['state']=='finished' and d.calls==[name for name,title in m.STAGES]
    assert r.status()['skipped'] and not r.status()['completion_verified']
