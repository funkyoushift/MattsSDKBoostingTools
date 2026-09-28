"""Direct queue pacing, identity failure isolation, journaling, and shared routing."""
import ast
import importlib.util
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / 'mod_extracted' / 'MattsSDKBoostingTools'
spec = importlib.util.spec_from_file_location('direct_delivery_test', SDK / 'direct_delivery.py')
delivery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(delivery)


class Clock:
    value = 0.0
    def __call__(self): return self.value


class Log:
    path = Path('test.jsonl')
    def __init__(self): self.events = []
    def event(self, event, **data): self.events.append((event, data))


def job(serials=None, targets=None, resolve=None, add=None):
    calls, clock, log = [], Clock(), Log()
    targets = targets or [{'name':'A','token':'a'},{'name':'B','token':'b'}]
    engine = delivery.Delivery(serials or ['@Ua'], targets, resolve or (lambda t:t['token']),
                               add or (lambda pc,s:calls.append((pc,s))), log, clock)
    return engine, calls, clock, log


def drain(engine, clock):
    for _ in range(10000):
        if engine.done: return
        clock.value = max(clock.value, engine.next,
                          min(t['ready'] for t in engine.targets if not t['done']))
        engine.step()
    raise AssertionError('Queue did not finish')


def test_chunks_use_characters_preserve_duplicates_and_do_not_impose_item_count():
    serials = ['@Ua'] * 100 + ['@U' + 'x'*7890, '@Ub']
    chunks = delivery.chunks_for(serials)
    assert [s for c in chunks for s in c] == serials
    assert len(chunks[0]) > 40
    assert all(sum(map(len,c)) <= 8192 for c in chunks)
    assert len(chunks) == 2
    with pytest.raises(ValueError): delivery.chunks_for(['@U'+'x'*8191])
    with pytest.raises(ValueError): delivery.chunks_for(['@Ué'])


def test_one_insert_per_tick_both_players_progress_and_duplicate_ticks_do_not_replay():
    engine,calls,clock,log = job(['@Ua','@Ub'])
    engine.step(); engine.step()
    assert calls == [('a','@Ua')]
    clock.value = engine.next; engine.step()
    assert calls == [('a','@Ua'),('b','@Ua')]
    drain(engine,clock)
    assert calls == [('a','@Ua'),('b','@Ua'),('a','@Ub'),('b','@Ub')]
    assert engine.done and not engine.error
    engine.step(); assert len(calls) == 4
    assert [e[0] for e in log.events].count('attempt') == 4


def test_full_gap_after_slow_native_call_and_chunk_pause():
    clock = Clock(); calls=[]
    def add(pc,serial):
        calls.append(serial); clock.value += .2
    engine=delivery.Delivery(['@U'+'a'*8190,'@Ub'],[{'name':'A','token':'a'}],
                             lambda t:t,add,Log(),clock)
    engine.step()
    assert engine.next == pytest.approx(.208)
    assert engine.targets[0]['ready'] == pytest.approx(.95)
    clock.value = .94; engine.step(); assert len(calls)==1
    clock.value = .95; engine.step(); assert len(calls)==2
    assert not engine.done
    clock.value=engine.targets[0]['ready']-.001; engine.step(); assert not engine.done
    clock.value+=.001; engine.step(); assert engine.done


def test_replaced_guest_fails_without_retargeting_and_other_guest_finishes():
    def resolve(t):
        if t['token']=='a': raise RuntimeError('Original player left')
        return t['token']
    engine,calls,clock,log=job(resolve=resolve)
    drain(engine,clock)
    assert calls==[('b','@Ua')]
    assert 'Original player left' in engine.error
    assert engine.progress('guests')['guest_save_verified'] is False


def test_uncertain_add_is_not_retried_and_yields_before_other_target():
    calls=[]
    def add(pc,s):
        calls.append(pc)
        if pc=='a': raise RuntimeError('Native outcome uncertain')
    engine,_,clock,log=job(add=add)
    engine.step(); assert calls==['a']
    drain(engine,clock); assert calls==['a','b']
    assert engine.targets[0]['sent']==0
    assert [x for e,x in log.events if e=='attempt' and x['target']==0]==[{'target':0,'index':0}]


def test_journal_failure_before_attempt_prevents_native_mutation():
    engine,calls,clock,log=job()
    log.event=lambda *a,**k:(_ for _ in ()).throw(OSError('disk full'))
    drain(engine,clock)
    assert calls==[] and engine.done


def test_journal_failure_after_add_does_not_repeat_native_call():
    engine,calls,clock,log=job()
    original=log.event
    def event(kind,**data):
        if kind=='returned': raise OSError('disk full after call')
        original(kind,**data)
    log.event=event
    drain(engine,clock)
    assert calls==[('a','@Ua'),('b','@Ua')]
    assert engine.error


def test_cancel_and_read_only_progress_cannot_add_items():
    engine,calls,clock,log=job()
    for _ in range(10): engine.progress('guests')
    engine.cancel('world changed'); engine.step()
    assert not calls and engine.done and engine.error


def test_manifest_and_attempt_log_retain_exact_serials_and_duplicates(tmp_path):
    serials=['@Ux`Y','@Ux`Y']
    journal=delivery.Journal(serials,[{'name':'Guest','token':{'state':4}}],'test',tmp_path)
    journal.event('attempt',target=0,index=0)
    journal.event('returned',target=0,index=0)
    manifest=json.loads(journal.path.with_suffix('.json').read_text())
    assert manifest['serials']==serials
    assert manifest['guest_save_verified'] is False
    assert [json.loads(x)['event'] for x in journal.path.read_text().splitlines()]==['queued','attempt','returned']


def load_functions(names, **namespace):
    tree=ast.parse((SDK/'serial_rewards.py').read_text(encoding='utf-8'))
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    ns={'_installation_authorized':lambda password=None:False,'List':list,'Any':object,**namespace}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'serial_rewards_test','exec'),ns)
    return ns


def test_shared_app_qm_afk_route_defaults_to_direct_and_restore_can_use_rewards():
    calls=[]
    ns=load_functions({'_do_give_serial_to_player_indices'},
        _queue_direct_delivery=lambda *a,**k:calls.append(('direct',a,k)),
        _queue_serial_delivery_sequence=lambda *a,**k:calls.append(('rewards',a,k)),
        _active_serial_delivery_progress={'method':'direct'})
    ns['_do_give_serial_to_player_indices'](['@Ua'],[1,2],bulk_authorized=True)
    ns['_do_give_serial_to_player_indices'](['@Ub'],[1],delivery_method='rewards',bulk_authorized=True)
    assert [x[0] for x in calls]==['direct','rewards']
    assert calls[0][1][1]==[1,2] and calls[0][2]['bulk_authorized'] is True


def test_serial_queue_keeps_afk_pending_through_final_settlement():
    engine,calls,clock,log=job()
    seq={'direct_delivery':engine,'chunks':engine.chunks,'index':0,'scope_label':'guests'}
    pending=[seq]
    ns=load_functions({'_process_pending_serial_delivery_sequences'},
        time=SimpleNamespace(time=clock),_pending_serial_delivery_sequences=pending,
        _active_serial_delivery_progress={},_set_serial_delivery_status=lambda *a,**k:None)
    ns['_process_pending_serial_delivery_sequences']()
    clock.value=engine.next; ns['_process_pending_serial_delivery_sequences']()
    assert pending and seq['index']==0 and len(calls)==2
    clock.value=31; ns['_process_pending_serial_delivery_sequences']()
    assert pending==[] and seq['index']==len(seq['chunks'])
    assert ns['_active_serial_delivery_progress']['stage']=='complete'


def test_identity_resolution_ignores_reused_party_indices():
    class Obj:
        def __init__(self,n):self.n=n
        def _get_address(self):return self.n
    world=Obj(1); original=Obj(3); replacement=Obj(6); pawn=Obj(4)
    pc=Obj(2);pc.PlayerState=original;pc.Pawn=pawn
    gs=SimpleNamespace(PlayerArray=[replacement,original])
    ns=load_functions({'_direct_token','_resolve_direct_target'},
        _gbc_session_world_and_gamestate=lambda:(world,gs),
        _gbc_find_pc_for_player_state=lambda ps,w:pc if ps is original else None)
    target={'token':ns['_direct_token'](world,pc)}
    assert ns['_resolve_direct_target'](target) is pc
    gs.PlayerArray=[replacement]
    with pytest.raises(RuntimeError,match='Original player left'): ns['_resolve_direct_target'](target)


@pytest.mark.parametrize('oversized', [False, True])
def test_queue_preserves_password_guard_and_refuses_to_replace_active_work(monkeypatch, tmp_path, oversized):
    package='direct_test_package'
    monkeypatch.setitem(sys.modules,package,types.ModuleType(package))
    monkeypatch.setitem(sys.modules,package+'.direct_delivery',delivery)
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path))
    native_calls=[]
    native=SimpleNamespace(add=lambda pc,s:native_calls.append((pc,s)))
    ns=load_functions({'_queue_direct_delivery'},__package__=package,
        _pending_serial_delivery_sequences=[],_pending_serial_patch_jobs=[],
        _player_name_for_index=lambda i:f'Guest {i}',
        _direct_delivery_preflight=lambda i:{'state':i},
        _resolve_direct_target=lambda t:t['token'],_direct_native=lambda:native,
        _gbc_run_session_timer_from_give_serial=lambda:None,_set_serial_delivery_tick=lambda enabled:None)
    queue=ns['_queue_direct_delivery']
    with pytest.raises(PermissionError):
        queue(['@Ua']*71,[1],scope_label='test',mode='selected',bulk_authorized=False)
    assert not list(tmp_path.rglob('*.json'))
    requested = ['@Ua']*71 + (['@U'+'x'*99997] if oversized else [])
    receipt = queue(requested,[1,2],scope_label='test',mode='all',bulk_authorized=True)
    assert receipt['queued_count'] == 71 and receipt['skipped_count'] == int(oversized)
    manifest = json.loads(Path(receipt['report_path']).with_suffix('.json').read_text())
    assert manifest['serials'] == requested and len(manifest['rejected']) == int(oversized)
    original=ns['_pending_serial_delivery_sequences'][0]
    with pytest.raises(RuntimeError,match='still running'):
        queue(['@Ub'],[1],scope_label='test',mode='selected',bulk_authorized=False)
    assert ns['_pending_serial_delivery_sequences']==[original] and native_calls==[]
    assert len(original['direct_delivery'].targets)==2


def test_native_gate_mismatch_cannot_bind_or_call_native_functions(monkeypatch):
    spec=importlib.util.spec_from_file_location('direct_inventory_test',SDK/'direct_inventory.py')
    native=importlib.util.module_from_spec(spec);spec.loader.exec_module(native)
    kernel=SimpleNamespace(GetModuleHandleW=lambda _:0x100000,VirtualQuery=lambda *a:1)
    monkeypatch.setattr(native.C,'WinDLL',lambda *a,**k:kernel,raising=False)
    monkeypatch.setattr(native.NativeInventory,'read',lambda self,p,n:b'\0'*n)
    monkeypatch.setattr(native.C,'CFUNCTYPE',lambda *a:(_ for _ in ()).throw(AssertionError('bound native code')))
    with pytest.raises(RuntimeError,match='not supported'): native.NativeInventory()


def test_oversized_entry_does_not_block_other_codes_or_lose_original_report(tmp_path):
    oversized = '@U' + 'x' * 99997
    requested = ['@Ua', oversized, '@Ub', '@Ua']
    accepted, rejected = delivery.partition_serials(requested)
    assert accepted == ['@Ua', '@Ub', '@Ua']
    assert rejected[0]['index'] == 1 and '99999' in rejected[0]['reason']
    journal = delivery.Journal(requested, [{'name':'A','token':'a'}], 'guest',
                               directory=tmp_path, rejected=rejected)
    clock = Clock(); calls = []
    engine = delivery.Delivery(accepted, [{'name':'A','token':'a'},{'name':'B','token':'b'}],
        lambda t:t['token'], lambda pc,s:calls.append((pc,s)), journal, clock, rejected=rejected)
    drain(engine, clock)
    assert calls == [(pc,s) for s in accepted for pc in ('a','b')]
    progress = engine.progress('guests')
    assert progress['skipped_count'] == 1 and 'Skipped 1' in progress['message']
    assert progress['total_serials'] == 3 and progress['guest_save_verified'] is False
    manifest = json.loads(journal.path.with_suffix('.json').read_text())
    assert manifest['serials'] == requested and manifest['rejected'] == rejected


def test_partition_limit_is_per_item_not_total_list_size():
    serials = ['@U'+'x'*8190] * 100
    accepted, rejected = delivery.partition_serials(serials)
    assert accepted == serials and rejected == []
    accepted, rejected = delivery.partition_serials(['@U'+'x'*8191, '@Ué', None])
    assert accepted == [] and len(rejected) == 3
