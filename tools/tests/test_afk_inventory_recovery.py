"""Recovery transaction checks; fake adapters never touch the game."""
import importlib.util
from copy import deepcopy
import json
from pathlib import Path
import pytest

path = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools/afk_inventory_recovery.py'
spec = importlib.util.spec_from_file_location('recovery_test', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def row(serial='@UDuplicate', handle=1, equip=-1):
    return dict(serial=serial, handle=handle, instance_id=handle+100, quantity=1,
                inventory_flags=2, item_flags=4, equip_slot=equip, slot_locked=False,
                slot_max_quantity=1, slot_type='native-slot-description')


def snapshot(*rows):
    return dict(ok=True, phase='complete', rows=list(rows))


class Adapter:
    def __init__(self, original, selected=()):
        self.operations = []
        self.original = original
        self.loot = snapshot(*(row(s, 1000+i) for i,s in enumerate(selected)))
        self.final = snapshot(*deepcopy(original['rows']), *deepcopy(self.loot['rows']))
        for i,r in enumerate(self.final['rows']):
            r['handle'],r['instance_id'] = 2000+i, 3000+i
        self.ready = True
        self.fail = None
    def preflight(self, original):
        return {'ok':self.ready, 'message':'Metadata restoration is not verified'}
    def begin(self, operation, record, player, world):
        self.operations.append(operation)
        return operation
    def poll(self, token, player, world):
        if token == self.fail:
            return {'ok':False, 'message':'Test failure'}
        return {'ok':True, 'snapshot':{'clear':snapshot(), 'deliver':self.loot,
                                       'restore':snapshot(), 'verify':self.final}[token]}


def test_exact_originals_and_selected_loot_restore_before_kick(tmp_path):
    original=snapshot(row(handle=1,equip=0),row(handle=2),row(handle=3))
    selected=['@UNew','@UNew']
    job=module.Recovery(tmp_path,original,player_token='guest',world_token='world',
                        guest_name='Guest',delivery_serials=selected)
    original['rows'][0]['serial']='@UMutatedAfterBackup'
    adapter=Adapter(job.record['original'],selected)
    for _ in range(4):
        job.advance('guest','world',adapter)
        assert not job.can_kick
    job.advance('guest','world',adapter)
    assert adapter.operations == ['clear','deliver','restore','verify']
    assert job.can_kick
    saved=module.Recovery.inspect(job.path)
    assert len(saved['original']['rows'])==3
    assert saved['original']['rows'][0]['serial']=='@UDuplicate'
    assert saved['phase']=='complete' and not saved['restart_replay_allowed']


@pytest.mark.parametrize('change', ['duplicate','quantity','flags','equip','case','extra'])
def test_restore_mismatch_blocks_kick(tmp_path, change):
    original=snapshot(row(handle=1),row(handle=2))
    job=module.Recovery(tmp_path,original,player_token=1,world_token=2,guest_name='Guest')
    adapter=Adapter(original)
    if change=='duplicate':adapter.final['rows'].pop()
    if change=='quantity':adapter.final['rows'][0]['quantity']=2
    if change=='flags':adapter.final['rows'][0]['item_flags']=0
    if change=='equip':adapter.final['rows'][0]['equip_slot']=0
    if change=='case':adapter.final['rows'][0]['serial']='@UDUPLICATE'
    if change=='extra':adapter.final['rows'].append(row('@UUnexpected',999))
    for _ in range(5):job.advance(1,2,adapter)
    assert not job.can_kick and job.record['phase']=='blocked'
    assert len(module.Recovery.inspect(job.path)['original']['rows'])==2


def test_unverified_native_adapter_never_clears(tmp_path):
    original=snapshot(row());adapter=Adapter(original);adapter.ready=False
    job=module.Recovery(tmp_path,original,player_token=1,world_token=2,guest_name='Guest')
    job.advance(1,2,adapter)
    assert adapter.operations==[] and not job.can_kick


def test_slot_replacement_or_world_change_never_delivers(tmp_path):
    for player,world in [(3,2),(1,3)]:
        original=snapshot(row());adapter=Adapter(original)
        job=module.Recovery(tmp_path,original,player_token=1,world_token=2,guest_name='Guest')
        job.advance(1,2,adapter)
        job.advance(player,world,adapter)
        assert adapter.operations==['clear'] and not job.can_kick


def test_write_failure_prevents_native_operation(tmp_path,monkeypatch):
    original=snapshot(row());adapter=Adapter(original)
    job=module.Recovery(tmp_path,original,player_token=1,world_token=2,guest_name='Guest')
    def fail():raise OSError('disk full')
    monkeypatch.setattr(job,'_save',fail)
    with pytest.raises(OSError):job.advance(1,2,adapter)
    assert not adapter.operations and not job.can_kick


def test_pending_operation_is_not_resubmitted(tmp_path,monkeypatch):
    original=snapshot(row());adapter=Adapter(original)
    job=module.Recovery(tmp_path,original,player_token=1,world_token=2,guest_name='Guest')
    monkeypatch.setattr(adapter,'poll',lambda *args:None)
    for _ in range(10):job.advance(1,2,adapter)
    assert adapter.operations==['clear'] and not job.can_kick
    assert module.Recovery.inspect(job.path)['phase']=='clear_pending'


def test_restore_failure_keeps_backup_and_blocks_kick(tmp_path):
    original=snapshot(row());adapter=Adapter(original);adapter.fail='restore'
    job=module.Recovery(tmp_path,original,player_token=1,world_token=2,guest_name='Guest')
    for _ in range(7):job.advance(1,2,adapter)
    assert adapter.operations==['clear','deliver','restore']
    assert not job.can_kick and module.Recovery.inspect(job.path)['original']==original


def test_failed_new_loot_still_restores_originals_and_blocks_kick(tmp_path):
    original=snapshot(row());adapter=Adapter(original,['@UNew']);adapter.fail='deliver'
    job=module.Recovery(tmp_path,original,player_token=1,world_token=2,guest_name='Guest',
        delivery_serials=['@UNew'],restore_metadata=False)
    for _ in range(5):job.advance(1,2,adapter)
    assert adapter.operations==['clear','deliver','restore','verify']
    assert job.record['phase']=='blocked' and not job.can_kick


def test_new_loot_submission_exception_still_attempts_original_return(tmp_path):
    original=snapshot(row());adapter=Adapter(original,['@UNew'])
    original_begin=adapter.begin
    def begin(operation,*args):
        if operation=='deliver':raise RuntimeError('delivery unavailable')
        return original_begin(operation,*args)
    adapter.begin=begin
    job=module.Recovery(tmp_path,original,player_token=1,world_token=2,guest_name='Guest',
        delivery_serials=['@UNew'],restore_metadata=False)
    for _ in range(5):job.advance(1,2,adapter)
    assert adapter.operations==['clear','restore','verify'] and not job.can_kick


def test_stop_before_clear_keeps_originals_and_releases_disk_block(tmp_path):
    job=module.Recovery(tmp_path,snapshot(row()),player_token=1,world_token=2,guest_name='Guest')
    assert job.cancel_before_clear()
    assert module.Recovery.unfinished(tmp_path) is None
    assert not job.can_kick


def test_corrupt_backup_rejected(tmp_path):
    job=module.Recovery(tmp_path,snapshot(row()),player_token=1,world_token=2,guest_name='Guest')
    envelope=json.loads(job.path.read_text());envelope['payload']+=' '
    job.path.write_text(json.dumps(envelope))
    with pytest.raises(ValueError,match='checksum'):module.Recovery.inspect(job.path)


def test_incomplete_snapshot_and_duplicate_identity_rejected(tmp_path):
    for original in [dict(ok=False,phase='failed',rows=[]),snapshot(row(),row())]:
        with pytest.raises(ValueError):
            module.Recovery(tmp_path,original,player_token=1,world_token=2,guest_name='Guest')
    assert list(tmp_path.iterdir())==[]


def test_item_only_restore_allows_unequipped_and_reset_flags():
    original=snapshot(row(handle=1,equip=0),row(handle=2))
    final=deepcopy(original)
    for r in final['rows']:
        r.update(equip_slot=-1,item_flags=0,inventory_flags=0)
    assert module.verify_restored(original,snapshot(),final,restore_metadata=False)['ok']
    assert not module.verify_restored(original,snapshot(),final)['ok']
    final['rows'].pop()
    assert not module.verify_restored(original,snapshot(),final,restore_metadata=False)['ok']


def test_item_only_counts_quantities_without_losing_duplicate_copies():
    original=snapshot(row(handle=1),row(handle=2))
    final=snapshot(row(handle=3));final['rows'][0]['quantity']=2
    assert module.verify_restored(original,snapshot(),final,restore_metadata=False)['ok']


def test_unreadable_after_clear_still_returns_all_originals_and_verifies(tmp_path):
    original=snapshot(row(handle=1),row(handle=2))
    adapter=Adapter(original)
    original_poll=adapter.poll
    adapter.poll=lambda token,*args: ({'ok':True,'snapshot':None,'clear_submitted':True,
        'readback_error':'Empty-slot serial unavailable'} if token=='clear' else original_poll(token,*args))
    job=module.Recovery(tmp_path,original,player_token=1,world_token=2,guest_name='Guest',restore_metadata=False)
    for _ in range(5):job.advance(1,2,adapter)
    assert job.can_kick and adapter.operations==['clear','deliver','restore','verify']
    assert job.record['clear_readback_verified'] is False
    assert job.record['retained']['rows']==[]


def test_unreadable_after_clear_does_not_allow_duplicate_final_items(tmp_path):
    original=snapshot(row(handle=1),row(handle=2));adapter=Adapter(original)
    adapter.final['rows'].append(row(handle=999))
    original_poll=adapter.poll
    adapter.poll=lambda token,*args: ({'ok':True,'snapshot':None,'clear_submitted':True}
        if token=='clear' else original_poll(token,*args))
    job=module.Recovery(tmp_path,original,player_token=1,world_token=2,guest_name='Guest',restore_metadata=False)
    for _ in range(5):job.advance(1,2,adapter)
    assert not job.can_kick and job.record['verification']['unexpected_rows']==1


def test_unfinished_recovery_survives_restart_and_blocks_start(tmp_path):
    original=snapshot(row());adapter=Adapter(original)
    job=module.Recovery(tmp_path,original,player_token=1,world_token=2,guest_name='Guest')
    assert module.Recovery.unfinished(tmp_path)==str(job.path)
    for _ in range(5):job.advance(1,2,adapter)
    assert module.Recovery.unfinished(tmp_path) is None
    job.path.write_text('corrupt')
    assert module.Recovery.unfinished(tmp_path)==str(job.path)


def test_item_only_recovery_accepts_retained_originals_not_reward_junk(tmp_path):
    original=snapshot(row(handle=1),row(handle=2))
    for retained, expected in [(snapshot(row(handle=1)), 'deliver'),(snapshot(row('@UJunk',3)),'blocked')]:
        job=module.Recovery(tmp_path,original,player_token=1,world_token=2,guest_name='Guest',restore_metadata=False)
        adapter=Adapter(original)
        adapter.poll=lambda *args:{'ok':True,'snapshot':retained}
        job.advance(1,2,adapter);job.advance(1,2,adapter)
        assert (adapter.operations[-1] if expected=='deliver' else job.record['phase'])==expected
