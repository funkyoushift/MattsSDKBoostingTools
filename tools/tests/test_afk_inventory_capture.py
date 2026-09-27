"""Read-only preservation precursor; no SDK or live inventory mutations."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import pytest

path = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools/afk_inventory_capture.py'
spec = importlib.util.spec_from_file_location('capture_test', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def row(serial='@USameCase', handle=1, quantity=1, equipped=-1):
    return NS(InventoryItem=NS(item=NS(data=NS(Identity=serial, InstanceId=handle+100),
        State=NS(Quantity=quantity, Flags=4)), Handle=NS(Handle=handle), Flags=2, EquipSlot=equipped),
        IsLocked=True, MaxQuantity=99, type='Backpack')


def test_restoration_signature_probe_only_reads_reflection():
    param=NS(Name='Handle',PropertyFlags=128,Offset_Internal=0,ElementSize=4)
    function=NS(Name='EquipInventoryItem',NumParams=1,FunctionFlags=64,
                _properties=lambda:iter([param]),_path_name=lambda:'/Script/Test.EquipInventoryItem')
    owner=NS(Name='NativeController',_fields=lambda:iter([function,NS(Name='InventoryProperty')]))
    cls=NS(_superfields=lambda:iter([owner]))
    result=module.restoration_api_schema(lambda name:cls)
    assert result['ok'] and len(result['functions'])==3
    assert result['functions'][0]['parameters'][0]['name']=='Handle'
    assert not result['cleanup_allowed'] and not result['restoration_verified']


def test_restoration_signature_probe_reports_unavailable_class():
    def unavailable(name):raise ValueError('not loaded')
    result=module.restoration_api_schema(unavailable)
    assert not result['ok'] and len(result['errors'])==3


def player(rows):
    return NS(BackpackItems=NS(items=rows))


def finish(capture, ps):
    for _ in range(2000):
        if capture.step(ps)['done']: return capture.status()
    raise AssertionError('capture did not finish')


def test_duplicates_quantity_and_equipped_metadata_preserved_without_cap():
    ps=player([row(handle=i, quantity=3, equipped=0 if i==0 else -1) for i in range(2100)])
    calls=[]
    capture=module.Capture(ps, serial_reader=lambda serial:calls.append(serial) or serial)
    capture.step(ps)
    assert len(calls)==16 and not capture.done
    assert finish(capture,ps)['ok']
    snapshot=capture.snapshot()
    assert len(snapshot['rows'])==2100 and len(calls)==4200
    assert all(r['serial']=='@USameCase' and r['quantity']==3 for r in snapshot['rows'])
    assert snapshot['rows'][0]['equip_slot']==0
    assert snapshot['rows'][1]['equip_slot']==-1
    assert snapshot['rows'][0]['inventory_flags']==2 and snapshot['rows'][0]['item_flags']==4
    assert snapshot['rows'][0]['slot_locked'] is True
    assert not snapshot['cleanup_allowed'] and not snapshot['restoration_verified']
    snapshot['rows'][0]['quantity']=999
    assert capture.snapshot()['rows'][0]['quantity']==3
    assert ps.BackpackItems.items[0].InventoryItem.item.State.Quantity==3


@pytest.mark.parametrize('mutation', ['serial','quantity','flags','equipped','handle','count'])
def test_changes_between_passes_invalidate_capture(mutation):
    ps=player([row()]);capture=module.Capture(ps,serial_reader=lambda x:x)
    assert capture.step(ps)['phase']=='verify'
    r=ps.BackpackItems.items[0]
    if mutation=='serial': r.InventoryItem.item.data.Identity='@UChanged'
    elif mutation=='quantity': r.InventoryItem.item.State.Quantity=2
    elif mutation=='flags': r.InventoryItem.Flags=8
    elif mutation=='equipped': r.InventoryItem.EquipSlot=0
    elif mutation=='handle': r.InventoryItem.Handle.Handle=9
    else: ps.BackpackItems.items.append(row(handle=2))
    assert not finish(capture,ps)['ok']
    with pytest.raises(RuntimeError): capture.snapshot()


@pytest.mark.parametrize('kind', ['missing_container','missing_row','bad_serial','missing_flags'])
def test_incomplete_reads_never_return_partial_snapshot(kind):
    ps=player([row(),row(handle=2)])
    if kind=='missing_container': del ps.BackpackItems
    elif kind=='missing_row': ps.BackpackItems.items[1]=None
    elif kind=='bad_serial': ps.BackpackItems.items[1].InventoryItem.item.data.Identity=''
    else: del ps.BackpackItems.items[1].InventoryItem.Flags
    capture=module.Capture(ps,serial_reader=lambda x:x)
    assert not finish(capture,ps)['ok']
    assert capture.records==[]
    with pytest.raises(RuntimeError): capture.snapshot()


def test_leaving_guest_cancels_and_empty_inventory_never_allows_cleanup():
    ps=player([row()]);capture=module.Capture(ps,serial_reader=lambda x:x)
    assert not capture.step(None)['ok'] and capture.done
    empty=player([]);capture=module.Capture(empty)
    assert not capture.step(empty)['done']
    assert capture.step(empty)['ok']
    assert capture.snapshot()['rows']==[] and not capture.snapshot()['cleanup_allowed']


def audit_fixture():
    ps=player([row()]);clock=[0.0];boosting=[False]
    live={'world':'world','rows':[{'token':ps,'index':1,'name':'Guest','ready':True}]}
    audit=module.Audit(lambda:(live['world'],live['rows']),lambda:boosting[0],clock=lambda:clock[0],
        capture_factory=lambda token:module.Capture(token,serial_reader=lambda serial:serial))
    return audit,ps,clock,boosting,live


def test_audit_is_explicit_paced_and_does_not_change_target_on_slot_reorder():
    audit,ps,clock,boosting,live=audit_fixture()
    started=audit.start(1);assert started['ok'];job_id=started['audit']['id']
    audit.tick();assert audit.status()['phase']=='capturing'
    assert not audit.start(1)['ok']
    audit.tick();assert audit.status()['phase']=='capturing'
    live['rows'][0]['index']=3;clock[0]=.25;audit.tick()
    result=audit.control('snapshot',job_id)
    assert result['ok'] and result['audit']['player_index']==3
    assert result['snapshot']['rows'][0]['serial']=='@USameCase'
    assert not result['snapshot']['cleanup_allowed']
    assert not audit.control('cancel','wrong-id')['ok']
    assert audit.status()['phase']=='complete'


@pytest.mark.parametrize('change',['left','slot_reused','world','boosting','not_ready','timeout'])
def test_audit_discards_capture_on_lifecycle_change(change):
    audit,ps,clock,boosting,live=audit_fixture();job_id=audit.start(1)['audit']['id']
    audit.tick();clock[0]=.25
    if change=='left':live['rows']=[]
    elif change=='slot_reused':live['rows'][0]['token']=player([row(handle=99)])
    elif change=='world':live['world']='other world'
    elif change=='boosting':boosting[0]=True
    elif change=='not_ready':live['rows'][0]['ready']=False
    else:clock[0]=301
    audit.tick()
    assert audit.status()['phase']=='cancelled'
    assert not audit.control('snapshot',job_id)['ok']


def test_waiting_audit_never_reads_before_character_ready():
    audit,ps,clock,boosting,live=audit_fixture();live['rows'][0]['ready']=False
    job_id=audit.start(1)['audit']['id'];audit.tick()
    assert audit.status()['capture'] is None
    live['rows'][0]['ready']=True;clock[0]=.25;audit.tick();clock[0]=.5;audit.tick()
    assert audit.control('snapshot',job_id)['ok']


def test_audit_requires_guest_index_and_stopped_boosting():
    audit,ps,clock,boosting,live=audit_fixture()
    for invalid in [None, True, -1, '1', 99]:assert not audit.start(invalid)['ok']
    boosting[0]=True;assert not audit.start(1)['ok']
    assert audit.status()['phase']=='idle'


def test_audit_bridge_routes_through_backend_without_manual_target_change():
    import subprocess,sys
    script = r'''
import importlib
from tests.test_quick_menu_last_command import _load_backend_actions
backend=_load_backend_actions()
bridge=importlib.import_module('MattsSDKBoostingTools.external_bridge')
calls=[]
backend.afk_inventory_audit=lambda payload: calls.append(payload) or {'ok':True}
def reject_target(*args):raise AssertionError('Audit changed shared manual target')
backend.set_target_player=reject_target
payload={'mode':'start','player_index':1,'target_player':2}
assert bridge._handle_action('afk_inventory_audit',payload)['ok']
assert calls==[payload]
assert 'afk_inventory_audit' in bridge._QUEUE_PRESERVING_ACTIONS
'''
    result=subprocess.run([sys.executable,'-c',script],cwd=path.parents[2]/'tools',capture_output=True,text=True)
    assert result.returncode==0,result.stdout+result.stderr


def test_native_api_discovery_never_calls_inventory_methods():
    class Statics:
        Class = NS(Name='NativeInventoryStatics')
        def RemoveItem(self): raise AssertionError('Must never be invoked')
        def EmptyContainer(self): raise AssertionError('Must never be invoked')
    result = module.inventory_api_names(Statics())
    assert result['ok'] and not result['cleanup_allowed']
    assert result['names'] == ['EmptyContainer', 'RemoveItem']


def test_missing_native_field_is_identified_without_returning_partial_items():
    ps = player([row()])
    del ps.BackpackItems.items[0].InventoryItem.item.State.Quantity
    capture = module.Capture(ps, serial_reader=lambda x:x)
    status = finish(capture, ps)
    assert status['error_index'] == 0 and 'State.Quantity' in status['error']
    assert capture.records == []


def test_comparison_tracks_duplicate_copies_by_native_identity_and_preserves_baseline():
    audit, ps, clock, boosting, live = audit_fixture()
    audit_id = audit.start(1)['audit']['id']
    audit.tick(); clock[0] = .25; audit.tick()
    ps.BackpackItems.items.append(row(handle=2))
    assert audit.control('compare', audit_id)['ok']
    clock[0] = .5; audit.tick(); clock[0] = .75; audit.tick()
    diff = audit.control('snapshot', audit_id)['comparison']
    assert len(diff['added']) == 1 and diff['added'][0]['serial'] == '@USameCase'
    assert diff['original_rows_unchanged'] and not diff['cleanup_allowed']
    assert not diff['reward_attribution_verified']
    ps.BackpackItems.items[0].InventoryItem.item.State.Quantity = 4
    assert audit.control('compare', audit_id)['ok']
    clock[0] = 1; audit.tick(); clock[0] = 1.25; audit.tick()
    diff = audit.control('snapshot', audit_id)['comparison']
    assert len(diff['added']) == 1 and len(diff['changed']) == 1
    assert diff['changed'][0]['before']['quantity'] == 1
    assert not diff['original_rows_unchanged']


def test_comparison_rejects_ambiguous_native_identity_and_incomplete_input():
    record = module._read_row(row(), lambda x:x)
    snapshot = {'ok': True, 'rows': [record, dict(record)]}
    with pytest.raises(ValueError, match='ambiguous'):
        module.compare_captures(snapshot, snapshot)
    with pytest.raises(ValueError, match='complete'):
        module.compare_captures({'ok': False}, snapshot)


def test_comparison_identifies_missing_or_reused_items_without_allowing_cleanup():
    before = {'ok': True, 'rows': [module._read_row(row(), lambda x:x)]}
    missing = module.compare_captures(before, {'ok': True, 'rows': []})
    assert len(missing['missing']) == 1 and not missing['original_rows_unchanged']
    after = {'ok': True, 'rows': [module._read_row(row(serial='@UReplacement'), lambda x:x)]}
    changed = module.compare_captures(before, after)
    assert len(changed['changed']) == 1 and not changed['added']
    assert not changed['cleanup_allowed']
