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

@pytest.mark.parametrize('n,owned,allowed',[(0,True,False),(1,False,True),(2,False,True),(3,False,False),(4,False,False),(4,True,True)])
def test_lobby_gate(n,owned,allowed):
    d=Driver(n,owned);s=d.preflight()
    assert m.eligibility(s['players'],s['packs'])['allowed']==allowed

def test_no_write_before_gate_or_ack(tmp_path):
    d=Driver(3);r=m.Run(d,tmp_path)
    with pytest.raises(ValueError):r.start({'acknowledge_shared_progress':True})
    d.owned=True
    with pytest.raises(ValueError):r.start({})
    assert not d.calls

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
             sdu_stub=NS(snapshot=lambda *a: None, advance=lambda *a: True), missions=NS(_engine=lambda: None))
    exec(compile(ast.Module(body=[cls],type_ignores=[]),'<driver>','exec'),env)
    return env['Driver'](),calls


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
    access=importlib.util.module_from_spec(spec);spec.loader.exec_module(access)
    engine=NS(base=0,ensure_world=lambda:None,read=lambda addr,n:b'\0'*n)
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
    def start(payload):
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
