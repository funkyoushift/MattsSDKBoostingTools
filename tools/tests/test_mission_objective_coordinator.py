"""Selected objective operations share scene/travel guards without extra work."""
import copy
import importlib.resources
import importlib.util
import struct
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace as NS

import pytest

ROOT=Path(__file__).parents[2]/'mod_extracted/MattsSDKBoostingTools'


@pytest.mark.parametrize('operation,policy',[('complete','map_only'),('replay','replay')])
def test_objective_completion_and_replay_have_distinct_placement_policies(rig,operation,policy):
    rig.m._last={'mission':'test','operation':operation}
    rig.m._begin_context(rig.m._progress()._party())
    assert rig.m._last['placement_policy']==policy


@pytest.fixture
def rig(monkeypatch):
    package=ModuleType('objective_coordinator_test');package.__path__=[str(ROOT)]
    monkeypatch.setitem(sys.modules,package.__name__,package)
    monkeypatch.setattr(importlib.resources,'files',lambda package:ROOT)
    spec=importlib.util.spec_from_file_location(package.__name__+'.mission_objectives',ROOT/'mission_objectives.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    m._interrupted_checked=True
    monkeypatch.setitem(sys.modules,spec.name,m)
    rows=[dict(token='one',name='first',pointer='0x2000',state=4,hidden=False,fact=None),
          dict(token='two',name='later',pointer='0x3000',state=4,hidden=False,fact=None)]
    row=dict(token='mission',record='0x1000',state='active',replication_type=0)
    calls=[];events=[];binding=[1];ready=[True];unloaded=[False]
    engine=NS(profile='steam-25372571', base=0,world_address=101,snapshot=lambda:{},
              u64=lambda addr:0xb973820 if addr==0x1000 else 0x1000 if addr in (0x2028,0x4028) else addr,
              read=lambda addr,size:bytes.fromhex('5657534883ec404889d74889ce488b053a90df034831e04889442438e8212a64')
              if addr==0x89068f2 else bytes.fromhex('4157415641545657534883ec3889d3488b054ae090084831e04889442430488b')
              if size==32 else struct.pack('<i',0 if addr==0x2080 else 1))
    pc=NS(_path_name=lambda:'World:PC')
    party=[dict(pc=pc,host=True)]
    progress=NS(_runtime=engine,_engine=lambda:engine,_party=lambda:party,
                _binding=lambda party:list(binding),_row=lambda *args:row,_state=lambda row:row['state'],
                _job=None,require_clear_journals=lambda:None,_dlc_requirement=lambda name:None)
    monkeypatch.setattr(m,'_progress',lambda:progress)
    monkeypatch.setattr(m,'read',lambda *args:copy.deepcopy(rows))
    durable_save=m._save
    monkeypatch.setattr(m,'_save',lambda:events.append(copy.deepcopy(m._last)))
    context=NS(begin=lambda *args:dict(world=101),observe=lambda owner:True,
               prepare_reset=lambda *args:unloaded[0],travel_to=lambda *args:True,
               world=lambda:None,map_name=lambda w:'world_p',expect_finish=lambda *args:None,
               objective_ready=lambda *args:ready[0])
    monkeypatch.setitem(sys.modules,package.__name__+'.mission_completion_context',context)
    monkeypatch.setitem(sys.modules,package.__name__+'.mission_completion_placement',NS(stop=lambda *args,**kw:False))
    monkeypatch.setitem(sys.modules,package.__name__+'.mission_effects',NS(reset_interactions=lambda *args:None))
    execution=importlib.import_module(package.__name__+'.mission_execution')
    execution.DATA={'test':dict(title='Test',execution_map='world_p',execution_maps=['world_p'],groups=[
        dict(index=0,objectives=[dict(name='first',completion_maps=['world_p'])]),
        dict(index=1,objectives=[dict(name='later')])])}
    def factory(*args):
        def bind(address):
            def invoke(*values):
                calls.append((address,values))
                if address==0x89068f2:rows[0]['state']=None
                else:rows[0]['state']=10
            return invoke
        return bind
    monkeypatch.setattr(m.C,'WINFUNCTYPE',factory)
    m._preview=dict(id='preview',consumed=False,name='test',token='mission',pid=m.os.getpid(),
                    world=101,binding=[1],signature=m._signature(rows))
    return NS(m=m,rows=rows,row=row,calls=calls,events=events,binding=binding,ready=ready,
              unloaded=unloaded,context=context,engine=engine,durable_save=durable_save)


@pytest.mark.parametrize('failure',[None,PermissionError,OSError])
def test_journal_replacement_retry_is_bounded_and_never_repeats_native(rig,monkeypatch,tmp_path,failure):
    r=rig;r.m._last=dict(id='journal',issued=['already-issued'])
    monkeypatch.setitem(sys.modules,'mods_base',NS(SETTINGS_DIR=tmp_path))
    replace=r.m.os.replace;attempts=[];delays=[]
    def transient(source,target):
        attempts.append(True)
        if failure is not None:raise failure('locked')
        if len(attempts)<3:raise PermissionError('reader holds destination')
        replace(source,target)
    monkeypatch.setattr(r.m.os,'replace',transient)
    monkeypatch.setattr(r.m.time,'sleep',delays.append)
    if failure:
        with pytest.raises(failure):r.durable_save()
        assert len(attempts)==(4 if failure is PermissionError else 1)
    else:
        r.durable_save()
        import json
        assert json.loads((tmp_path/'msbt_objectives/journal.json').read_text())==r.m._last
        assert len(attempts)==3
    assert len(delays)==len(attempts)-1 and not r.calls


def begin(r):
    return r.m.complete(dict(preview_id='preview',objective_token='one',acknowledge_shared_progress=True))


def test_selected_completion_waits_for_scene_and_never_completes_later(rig):
    r=rig;r.ready[0]=False
    result=begin(r)
    assert result['ok'] and result['state']=='running' and not r.calls
    r.ready[0]=True;r.m.step(dict(job_id=result['id']))
    assert len(r.calls)==1
    r.rows[0]['state']=13
    assert r.m.step(dict(job_id=result['id']))['state']=='completed'
    assert len(r.calls)==1 and r.rows[1]['state']==4


def test_changed_party_stops_before_outcome(rig):
    r=rig;r.ready[0]=False;result=begin(r)
    r.ready[0]=True;r.binding.append(2)
    stopped=r.m.step(dict(job_id=result['id']))
    assert stopped['state']=='stopped' and not r.calls
    assert 'players changed' in stopped['message']


@pytest.mark.parametrize('terminal',['completed','replayed','cancelled'])
def test_settled_receipt_survives_later_world_and_party_changes(rig,terminal):
    r=rig;result=begin(r)
    r.m._last.update(state=terminal,ok=terminal!='cancelled',message='Recorded result')
    r.engine.world_address=999;r.binding.append(2)
    r.m._progress=lambda:pytest.fail('Settled receipt must not inspect later gameplay')
    status=r.m.status()
    assert status['id']==result['id'] and status['state']==terminal
    assert status['message']=='Recorded result'


def test_replay_unloads_and_uses_fresh_pointer_only_once(rig):
    r=rig;result=begin(r);r.rows[0]['state']=13;r.m.status();r.calls.clear()
    replay=r.m.replay_last(dict(acknowledge_shared_progress=True))
    assert replay['state']=='running' and not r.calls
    r.unloaded[0]=True;r.rows[0]['pointer']='0x4000'
    r.m.step(dict(job_id=replay['id']))
    assert r.calls==[(0x89068f2,(0x1000,0x4000))]
    assert r.m.step(dict(job_id=replay['id']))['state']=='running'
    r.rows[0]['state']=4
    assert r.m.step(dict(job_id=replay['id']))['state']=='replayed'
    assert len(r.calls)==1


def test_replay_activation_timeout_does_not_repeat_rewind(rig,monkeypatch):
    r=rig;result=begin(r);r.rows[0]['state']=13;r.m.status();r.calls.clear();r.unloaded[0]=True
    replay=r.m.replay_last(dict(acknowledge_shared_progress=True));r.m.step(dict(job_id=replay['id']))
    r.m._last['replay_wait_started']=0
    monkeypatch.setattr(r.m.time,'monotonic',lambda:121)
    assert r.m.step(dict(job_id=replay['id']))['state']=='stopped'
    assert len(r.calls)==1


def test_close_retains_unknown_result_without_calling_again(rig):
    r=rig;result=begin(r)
    closed=r.m.recover(dict(job_id=result['id'],mode='close',acknowledge_shared_progress=True))
    assert closed['state']=='cancelled' and not closed['ok']
    r.rows[0]['state']=13
    assert r.m.status()['state']=='cancelled' and len(r.calls)==1


def test_mutations_remain_blocked_until_objective_reconciled(rig):
    r=rig;begin(r)
    assert r.m.conflict('mission_start') and r.m.conflict('full_progress_start')
    assert not r.m.conflict('mission_objective_step') and not r.m.conflict('give_serials')
    r.rows[0]['state']=13;r.m.status()
    assert not r.m.conflict('mission_start')


def test_selected_parent_waits_for_all_issued_children(rig):
    r=rig;result=begin(r)
    r.m._last['objective_runs']['test']['issued'].append('two')
    r.rows[0]['state']=13;r.rows[1]['state']=11
    assert r.m.status()['state']!='completed'
    r.rows[1]['state']=13
    assert r.m.status()['state']=='completed'


def test_recovery_reconciles_exact_pending_child_without_reissuing(rig):
    r=rig;result=begin(r)
    receipt=r.m._last['objective_runs']['test']
    receipt.update(issued=['one','two'],pending='two')
    r.m._last.update(state='uncertain',ok=False)
    r.rows[1]['state']=13
    r.m.recover(dict(job_id=result['id'],mode='continue',acknowledge_shared_progress=True))
    assert 'pending' not in receipt and receipt['issued']==['one','two']
    assert len(r.calls)==1


def test_restart_record_requires_close_and_never_replays_old_pointers(rig,monkeypatch,tmp_path):
    import json
    r=rig;result=begin(r)
    folder=tmp_path/'msbt_objectives';folder.mkdir()
    record=copy.deepcopy(r.m._last);record['pid']=-1
    (folder/'old.json').write_text(json.dumps(record))
    monkeypatch.setitem(sys.modules,'mods_base',NS(SETTINGS_DIR=tmp_path))
    r.m._last=None;r.m._interrupted_checked=False
    assert r.m.status()['state']=='interrupted'
    with pytest.raises(ValueError,match='original game session'):
        r.m.recover(dict(job_id=result['id'],mode='continue',acknowledge_shared_progress=True))
    assert r.m.recover(dict(job_id=result['id'],mode='close',acknowledge_shared_progress=True))['state']=='cancelled'
    assert len(r.calls)==1 and not r.m.conflict('mission_start')


def test_unowned_dlc_objective_rejects_before_consuming_preview_or_native_call(rig):
    r=rig;r.m._progress()._dlc_requirement=lambda name:dict(allowed=False,reason='Guest lacks this DLC')
    with pytest.raises(ValueError,match='Guest lacks'):
        begin(r)
    assert not r.calls and not r.m._preview['consumed'] and r.m._last is None


def test_changed_dlc_access_while_preparing_stops_before_outcome(rig):
    r=rig;r.ready[0]=False;result=begin(r)
    r.ready[0]=True;r.m._progress()._dlc_requirement=lambda name:dict(allowed=False,reason='Access unconfirmed')
    assert r.m.step(dict(job_id=result['id']))['state']=='stopped'
    assert not r.calls


@pytest.mark.parametrize('size',[2,4])
def test_selected_objective_completes_in_shared_lobby_without_advancing_sibling(rig,size):
    r=rig;progress=r.m._progress();party=progress._party()
    party.extend(dict(pc=NS(_path_name=lambda i=i:'World:Guest'+str(i)),host=False) for i in range(1,size))
    r.binding[:]=list(range(size));r.m._preview['binding']=list(r.binding)
    result=begin(r);assert len(r.calls)==1 and r.m._last['placement_policy']=='map_only'
    r.rows[0]['state']=13
    assert r.m.step(dict(job_id=result['id']))['state']=='completed'
    assert len(r.calls)==1 and r.rows[1]['state']==4
