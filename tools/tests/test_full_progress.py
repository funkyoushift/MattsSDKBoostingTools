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

def test_roster_change_stops_before_write(tmp_path):
    d=Driver();r=m.Run(d,tmp_path);job=r.start({'acknowledge_shared_progress':True});d.binding='changed'
    assert r.step(job['id'])['state']=='stopped'
    assert not d.calls

def test_unknown_outcome_never_reissued(tmp_path):
    d=Driver();r=m.Run(d,tmp_path);job=r.start({'acknowledge_shared_progress':True})
    def fail(*args):d.calls.append('once');raise RuntimeError('Unknown')
    d.begin=fail
    assert r.step(job['id'])['state']=='uncertain'
    r.step(job['id']);assert d.calls==['once']
    assert m.Run(d,tmp_path).status()['state']=='interrupted'

def test_finished_is_not_save_proof(tmp_path):
    d=Driver();r=m.Run(d,tmp_path);job=r.start({'acknowledge_shared_progress':True})
    for _ in m.STAGES:r.step(job['id'])
    assert r.status()['state']=='finished'
    assert not r.status()['completion_verified']


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
    tree=ast.parse(source)
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Driver')
    calls=[]
    economy=NS(_MAX_WALLET_AMOUNT=1000,_MAX_SDU_POINTS=3225,_SDU_POINTS_POOL_INDEX=0,
               _target_character_for_pc=lambda pc:NS(GbxProgressionManager=NS(ProgressPointsContainer=NS(PointsAcquiredPerPool=[3225]))),
               _set_experience_level_via_bp=lambda ps,t,cap:calls.append(('level',ps,t,cap)) or True,
               _give_currency_on_pc=lambda pc,t,amount:calls.append(('currency',pc,t,amount)) or True,
               _set_max_sdu_points_on_pc=lambda pc:True)
    env=dict(vehicle_stub=NS(_load_vehicle_catalog_rows=lambda:[]),economy=economy,MAX_PLAYER_LEVEL=70,MAX_SPEC_LEVEL=701,MAX_VAULT_CARD_LEVEL=9999,time=time)
    exec(compile(ast.Module(body=[cls],type_ignores=[]),'<driver>','exec'),env)
    return env['Driver'](),calls


def test_character_tops_up_delta_and_never_reduces_existing_progress():
    d,calls=character_driver()
    row=dict(pc='guest',state='guest_state',label='Guest')
    sample=dict(level=80,specialization=800,currencies={'Cash':900,'eridium':1000},vault_cards=[])
    result=d.character(row,sample,{'packs':{'missing':{'allowed':False}}})
    assert calls==[('currency','guest','Cash',100)]
    assert result['skipped'] and not result['completion_verified']


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


def test_discovery_batch_stops_immediately_on_uncertain():
    from types import SimpleNamespace as NS
    d,_=character_driver();env=d.poll.__globals__;calls=[]
    def step(ident):
        calls.append(ident)
        return dict(state='uncertain' if len(calls)==2 else 'running')
    env['missions']=NS(step=step)
    env['time']=NS(monotonic=lambda:0)
    assert d.poll('map_locations',dict(kind='mission',id='child'),{})['state']=='uncertain'
    assert len(calls)==2


def test_discovery_batch_has_count_and_time_bounds_and_missions_stay_single():
    from types import SimpleNamespace as NS
    d,_=character_driver();env=d.poll.__globals__;calls=[]
    env['missions']=NS(step=lambda ident:calls.append(ident) or dict(state='running'))
    env['time']=NS(monotonic=lambda:0)
    d.poll('map_locations',dict(kind='mission',id='child'),{});assert len(calls)==4
    calls.clear();d.poll('missions',dict(kind='mission',id='child'),{});assert len(calls)==1
    calls.clear();times=iter([0,.021]);env['time']=NS(monotonic=lambda:next(times))
    d.poll('map_locations',dict(kind='mission',id='child'),{});assert len(calls)==1


@pytest.mark.parametrize('raises',[False,True])
def test_vault_card_level_failure_is_reported_and_other_progress_continues(raises):
    from types import SimpleNamespace as NS
    d,calls=character_driver();env=d.character.__globals__
    def level(*args):
        if raises:raise RuntimeError('Inactive card')
        return False
    env['economy']._set_experience_level_via_bp=level
    row=dict(pc='guest',state=NS(PlayerId=2),label='Guest')
    sample=dict(level=70,specialization=701,currencies={'Cash':900,'eridium':1000,'VaultCard02_Tokens':1000},vault_cards=[dict(card=2,rank=0)])
    snapshot=dict(packs={'vaultcard2':dict(allowed=False,players=[dict(player_id=2,access='enabled')])})
    result=d.character(row,sample,snapshot)
    assert any('activate that card' in s for s in result['skipped'])
    assert calls==[('currency','guest','Cash',100)]


def final_driver(states,done=()):
    from types import SimpleNamespace as NS
    d,_=character_driver();env=d.final_recheck.__globals__;starts=[]
    def start(payload):
        starts.append(payload.copy());return dict(id='child',state='running')
    env['missions']=NS(CATALOG={n:dict(title=n) for n in states},NONPERSISTENT=set(),
        _engine=lambda:NS(snapshot=lambda:states),_row=lambda s,n:s[n],_state=lambda r:r,start=start)
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
