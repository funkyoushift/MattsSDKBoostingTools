import importlib.util
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType, SimpleNamespace as NS
import pytest

from test_afk_inventory_recovery import module as recovery, row, snapshot


def load(monkeypatch):
    package='test_native_recovery_package'
    monkeypatch.setitem(sys.modules,package,ModuleType(package))
    monkeypatch.setitem(sys.modules,package+'.afk_inventory_recovery',recovery)
    class Capture:
        def __init__(self,player):self.player=player
        def step(self,player):return {'ok':True,'done':True}
        def snapshot(self):return deepcopy(self.player.snapshot)
    capture=ModuleType(package+'.afk_inventory_capture');capture.Capture=Capture
    monkeypatch.setitem(sys.modules,capture.__name__,capture)
    path=Path(__file__).resolve().parents[2]/'mod_extracted/MattsSDKBoostingTools/afk_inventory_native_recovery.py'
    spec=importlib.util.spec_from_file_location(package+'.native',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    clock=[0.0];monkeypatch.setattr(module,'time',NS(monotonic=lambda:clock[0]))
    return module,clock


def game_for(original):
    player=NS(snapshot=deepcopy(original));pc=object();calls=[];seqs=[]
    def clear(target):
        assert target is pc
        calls.append('clear');player.snapshot=snapshot(*player.snapshot['rows'][:1])
        return 'empty backpack OK'
    def send(serials,indices,**kwargs):
        calls.append(('send',list(serials),indices))
        seqs.append({'index':0,'chunks':[list(serials)]})
    rewards=NS(_serial_delivery_busy=lambda:bool(seqs),_pending_serial_delivery_sequences=seqs,
               _do_give_serial_to_player_indices=send)
    backend=NS(serial_rewards=rewards,afk_lobby_status=lambda:{'enabled':False},
        complete_challenges_status=lambda:{'active':False},uvh_boost_status=lambda:{'active':False},
        streamer_chaos=NS(empty_backpack_for_pc=clear,result_ok=lambda msg:msg=='empty backpack OK'))
    roster=[dict(token=player,pc=pc,index=1,ready=True)]
    game=NS(roster=lambda:('world',roster),backend=lambda:backend,is_host=lambda:True)
    return game,player,calls,seqs,roster


def test_native_clear_captures_first_and_restores_only_missing_duplicates(monkeypatch):
    native,clock=load(monkeypatch)
    original=snapshot(row(handle=1),row(handle=2),row(handle=3))
    game,player,calls,seqs,roster=game_for(original)
    adapter=native.NativeAdapter(game,player,'world')
    assert adapter.preflight(original)['ok']
    record={'original':original,'delivery_serials':[]}
    token=adapter.begin('clear',record,player,'world')
    assert calls==[]
    assert adapter.poll(token,player,'world') is None
    assert calls==['clear']
    clock[0]=4
    cleared=adapter.poll(token,player,'world');assert len(cleared['snapshot']['rows'])==1
    record['retained']=cleared['snapshot']
    roster[0]['index']=2
    restore=adapter.begin('restore',record,player,'world')
    assert calls[-1]==('send',['@UDuplicate','@UDuplicate'],[2])
    assert seqs[0]['afk_player_state'] is player
    assert adapter.poll(restore,player,'world') is None
    seqs[0]['index']=1;seqs.clear();clock[0]=8
    assert adapter.poll(restore,player,'world') is None
    clock[0]=12;assert adapter.poll(restore,player,'world')['ok']


def test_missing_original_prevents_clear(monkeypatch):
    native,clock=load(monkeypatch);original=snapshot(row(),row(handle=2))
    game,player,calls,seqs,roster=game_for(original)
    adapter=native.NativeAdapter(game,player,'world')
    player.snapshot=snapshot(row())
    token=adapter.begin('clear',{'original':original},player,'world')
    assert not adapter.poll(token,player,'world')['ok'] and calls==[]


def test_dead_slots_after_successful_clear_defer_verification_to_restore(monkeypatch):
    native,clock=load(monkeypatch);original=snapshot(row())
    game,player,calls,seqs,roster=game_for(original)
    adapter=native.NativeAdapter(game,player,'world')
    token=adapter.begin('clear',{'original':original},player,'world')
    assert adapter.poll(token,player,'world') is None and calls==['clear']
    token['capture']=NS(step=lambda player:{'done':True,'ok':False,'error':'Empty-slot serial unavailable'})
    clock[0]=4
    result=adapter.poll(token,player,'world')
    assert result['ok'] and result['clear_submitted'] and result['snapshot'] is None
    assert calls==['clear']  # Never repeat the destructive operation.


def test_stack_and_active_delivery_preflight_reject_before_clear(monkeypatch):
    native,clock=load(monkeypatch);original=snapshot(row())
    game,player,calls,seqs,roster=game_for(original);adapter=native.NativeAdapter(game,player,'world')
    assert not adapter.preflight(snapshot())['ok']
    original['rows'][0]['quantity']=2
    assert not adapter.preflight(original)['ok']
    original['rows'][0]['quantity']=1;seqs.append({})
    assert not adapter.preflight(original)['ok'] and calls==[]


def test_combined_native_flow_returns_originals_plus_selected_serials(tmp_path,monkeypatch):
    native,clock=load(monkeypatch)
    original=snapshot(row(handle=1),row(handle=2),row(handle=3))
    selected=['@UDuplicate','@UNew','@UNew']
    game,player,calls,seqs,roster=game_for(original)
    adapter=native.NativeAdapter(game,player,'world')
    job=recovery.Recovery(tmp_path,original,player_token=player,world_token='world',
        guest_name='Guest',delivery_serials=selected,restore_metadata=False)
    next_handle=500
    for _ in range(30):
        job.advance(player,'world',adapter)
        for seq in list(seqs):
            for serial in seq['chunks'][0]:
                player.snapshot['rows'].append(row(serial,next_handle));next_handle+=1
            seq['index']=len(seq['chunks']);seqs.remove(seq)
        clock[0]+=4
        if job.can_kick:break
    assert job.can_kick
    assert recovery.item_counts(player.snapshot)=={'@UDuplicate':4,'@UNew':2}
    assert [c[1] for c in calls if isinstance(c,tuple)]==[selected,['@UDuplicate','@UDuplicate']]


@pytest.mark.parametrize('repair_succeeds', [True, False])
def test_automatic_repair_only_sends_missing_copies_and_is_bounded(tmp_path, monkeypatch, repair_succeeds):
    native, clock = load(monkeypatch)
    original = snapshot(row(handle=1), row(handle=2), row(handle=3))
    game, player, calls, seqs, roster = game_for(original)
    adapter = native.NativeAdapter(game, player, 'world')
    job = recovery.Recovery(tmp_path, original, player_token=player, world_token='world',
        guest_name='Guest', delivery_serials=['@UNew', '@UNew'], restore_metadata=False)
    handle = 100
    sends = 0
    for _ in range(100):
        job.advance(player, 'world', adapter)
        for seq in list(seqs):
            sends += 1
            # The first new-loot delivery and original return each lose one copy.
            serials = seq['chunks'][0]
            delivered = serials[:-1] if sends <= 2 else (serials if repair_succeeds else [])
            for serial in delivered:
                player.snapshot['rows'].append(row(serial, handle)); handle += 1
            seq['index'] = len(seq['chunks']); seqs.remove(seq)
        clock[0] += 4
        if job.record['phase'] in ('blocked', 'complete'):
            break
    assert calls.count('clear') == 1
    retries = [c[1] for c in calls if isinstance(c, tuple)][2:]
    assert len(retries) == (1 if repair_succeeds else 3)
    assert all(sorted(items) == ['@UDuplicate', '@UNew'] for items in retries)
    assert job.can_kick is repair_succeeds
    assert job.record['phase'] == ('complete' if repair_succeeds else 'blocked')
    if repair_succeeds:
        assert recovery.item_counts(player.snapshot) == {'@UDuplicate': 3, '@UNew': 2}
        assert 'delivery_error' not in job.record


def test_unstable_capture_retries_then_succeeds_without_resending(monkeypatch):
    native, clock = load(monkeypatch)
    original = snapshot(row())
    game, player, calls, seqs, roster = game_for(original)
    adapter = native.NativeAdapter(game, player, 'world')
    token = adapter.begin('verify', {'original': original, 'delivery_serials': [],
                                   'restore_metadata': False}, player, 'world')
    token['capture'] = NS(step=lambda _: {'done': True, 'ok': False, 'error': 'Inventory contents changed'})
    assert adapter.poll(token, player, 'world') is None
    clock[0] = 3
    assert adapter.poll(token, player, 'world')['delivery_reconciled']
    assert calls == []


def test_late_arrival_cancels_deficit_retry_and_disconnect_never_targets_replacement(monkeypatch):
    native, clock = load(monkeypatch)
    original = snapshot(row())
    game, player, calls, seqs, roster = game_for(original)
    adapter = native.NativeAdapter(game, player, 'world')
    record = {'original': original, 'delivery_serials': ['@UNew'], 'restore_metadata': False}
    token = adapter.begin('verify', record, player, 'world')
    assert adapter.poll(token, player, 'world') is None
    player.snapshot['rows'].append(row('@UNew', 10)); clock[0] = 6
    assert adapter.poll(token, player, 'world')['delivery_reconciled']
    assert calls == []
    roster[0]['token'] = object()
    with pytest.raises(RuntimeError):
        adapter.poll(token, player, 'world')
    assert calls == []


def test_historical_recovery_does_not_block_next_guest_capture(tmp_path, monkeypatch):
    native, clock = load(monkeypatch)
    package = native.__package__
    monkeypatch.setitem(sys.modules, package+'.afk_inventory_native_recovery', native)
    path = Path(native.__file__).with_name('afk_lobby.py')
    spec = importlib.util.spec_from_file_location(package+'.afk_lobby', path)
    lobby = importlib.util.module_from_spec(spec); spec.loader.exec_module(lobby)
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path))
    directory = tmp_path / 'MattsSDKBoostingTools/inventory-recovery'
    old = recovery.Recovery(directory, snapshot(row()), player_token=1, world_token=2, guest_name='Left')
    old._block('Disconnected')
    game, player, calls, seqs, roster = game_for(snapshot(row()))
    instance = lobby.Game(); instance.backend = game.backend; instance.roster = game.roster
    job = {'pc':roster[0]['pc'], 'token':player, 'name':'Next guest'}
    assert instance.step('inventory_capture', job, {})['ok']
    assert recovery.Recovery.inspect(old.path)['phase'] == 'blocked'


def test_read_retries_are_bounded_and_busy_preflight_expires(monkeypatch):
    native, clock = load(monkeypatch)
    original = snapshot(row())
    game, player, calls, seqs, roster = game_for(original)
    adapter = native.NativeAdapter(game, player, 'world')
    token = adapter.begin('verify', {'original':original, 'delivery_serials':[],
                                    'restore_metadata':False}, player, 'world')
    for attempt in range(6):
        token['capture'] = NS(step=lambda _: {'done':True, 'ok':False, 'error':'Unstable'})
        result = adapter.poll(token, player, 'world')
        assert (result is None) is (attempt < 5)
        clock[0] += 3
    assert not result['ok'] and calls == []
    seqs.append({})
    assert adapter.preflight(original)['retry']
    clock[0] += 61
    assert not adapter.preflight(original)['retry']


def test_interrupted_original_return_is_repaired_without_second_clear(tmp_path, monkeypatch):
    native, clock = load(monkeypatch)
    original = snapshot(row(handle=1), row(handle=2))
    game, player, calls, seqs, roster = game_for(original)
    adapter = native.NativeAdapter(game, player, 'world')
    job = recovery.Recovery(tmp_path, original, player_token=player, world_token='world',
        guest_name='Guest', restore_metadata=False)
    sends = 0
    for _ in range(60):
        job.advance(player, 'world', adapter)
        for seq in list(seqs):
            sends += 1
            if sends == 1:
                seq['afk_error'] = 'Interrupted'
            else:
                for i, serial in enumerate(seq['chunks'][0]):
                    player.snapshot['rows'].append(row(serial, 100+i))
                seq['index'] = len(seq['chunks'])
            seqs.remove(seq)
        clock[0] += 4
        if job.can_kick: break
    assert job.can_kick and calls.count('clear') == 1
    assert sends == 2 and recovery.item_counts(player.snapshot) == {'@UDuplicate':2}
