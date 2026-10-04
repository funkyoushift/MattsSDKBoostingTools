"""Bounded AFK overlap, independent target pacing and interruption safety."""
import sys
import types
import random
from types import SimpleNamespace

import pytest

from test_afk_lobby import module as afk, FakeGame, row, ticks
from test_direct_delivery import delivery, load_functions, Clock
from test_afk_loot_classes import m as loot_selector


def make_lobby(**config):
    game = FakeGame()
    lobby = afk.Lobby(game)
    assert lobby.start(dict(level=True, loot=True, concurrent_guests=True, **config))['ok']
    return game, lobby


def test_default_concurrency_survives_restart_and_exclusive_modes_stay_sequential():
    lobby = afk.Lobby(FakeGame())
    for payload in ({'level': True}, {'level': True}):
        assert lobby.start(payload)['ok']
        assert lobby.config['concurrent_guests']
        lobby.stop()
    for payload in ({'level': True, 'test_host': True},
                    {'uvhm': True, 'cleanup_rewards': True},
                    {'level': True, 'concurrent_guests': False}):
        assert lobby.start(payload)['ok']
        assert not lobby.config['concurrent_guests']
        lobby.stop()


def test_three_ready_guests_each_advance_without_waiting_for_first_delivery():
    game, lobby = make_lobby()
    game.rows = [row('A'), row('B', 2), row('C', 3)]
    def step(action, job, config):
        game.calls.append((action, job['token']))
        return None if action == 'loot' else {'ok':True, 'message':'applied'}
    game.step = step
    ticks(lobby, 1)
    assert game.calls == [('level', 'A'), ('level', 'B'), ('level', 'C')]
    ticks(lobby, 1)
    assert game.calls[3:] == [('loot', 'A'), ('loot', 'B'), ('loot', 'C')]
    assert len(lobby.status()['active_guests']) == 3
    lobby.stop()
    assert sorted(game.cancelled) == ['A', 'B', 'C']


@pytest.mark.parametrize('interruption', ['leave', 'world', 'unready'])
def test_started_jobs_parked_in_queue_are_cancelled_not_lost(monkeypatch, interruption):
    clock = [0.0]
    monkeypatch.setattr(afk.time, 'monotonic', lambda: clock[0])
    game, lobby = make_lobby()
    game.rows = [row('A'), row('B', 2)]
    game.wait = True
    ticks(lobby, 2)
    if interruption == 'leave':
        game.rows = [row('B', 2)]
    elif interruption == 'world':
        game.world = 'new-world'
    else:
        game.rows[0]['ready'] = False
        ticks(lobby, 1)
        clock[0] = 121.0
    ticks(lobby, 1)
    assert game.cancelled.count('A') == 1
    if interruption == 'world':
        assert game.cancelled.count('B') == 1
    else:
        assert 'B' not in game.cancelled


def test_new_ready_guest_starts_while_first_waits_and_loading_guest_does_not_block():
    game, lobby = make_lobby()
    game.rows = [row('A')]
    game.wait = True
    ticks(lobby, 1)
    game.rows += [row('loading', 2, False), row('C', 3)]
    game.wait = False
    ticks(lobby, 1)
    assert ('level', 'C', 3) in game.calls
    assert not any(call[1] == 'loading' for call in game.calls)


def test_shared_steps_have_one_owner_but_do_not_block_personal_boosts():
    game, lobby = make_lobby(uvhm=True)
    game.rows = [row('A'), row('B', 2)]
    def step(action, job, config):
        game.calls.append((action, job['token']))
        return None if action == 'uvhm' else {'ok':True, 'message':'applied'}
    game.step = step
    ticks(lobby, 5)
    assert ('level', 'B') in game.calls
    assert ('uvhm', 'A') in game.calls
    assert ('uvhm', 'B') not in game.calls
    assert sum(job.get('shared_run') is not None for job in list(lobby.queue)+([lobby.current] if lobby.current else [])) == 1


def test_cleanup_and_host_test_cannot_enable_pilot():
    lobby = afk.Lobby(FakeGame())
    assert not lobby.start(dict(loot=True, concurrent_guests=True, test_host=True))['ok']
    assert not lobby.start(dict(challenges=True, concurrent_guests=True, cleanup_rewards=True))['ok']


@pytest.fixture
def queues(monkeypatch, tmp_path):
    package = 'concurrent_direct_test'
    monkeypatch.setitem(sys.modules, package, types.ModuleType(package))
    monkeypatch.setitem(sys.modules, package+'.direct_delivery', delivery)
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path))
    submitted, clock = [], Clock()
    native = SimpleNamespace(add=lambda pc, serial: submitted.append((pc, serial, clock.value)))
    ns = load_functions({'_afk_direct_delivery_available', '_queue_direct_delivery', 'serial_delivery_progress',
                         '_do_give_serial_to_player_indices',
                         '_process_pending_serial_delivery_sequences', '_cancel_direct_sequence'},
        __package__=package, time=SimpleNamespace(time=clock),
        _pending_serial_delivery_sequences=[], _pending_serial_patch_jobs=[],
        _player_name_for_index=lambda i:f'Guest {i}', _direct_delivery_preflight=lambda i:{'state':i},
        _resolve_direct_target=lambda t:t['token']['state'], _direct_native=lambda:native,
        _gbc_run_session_timer_from_give_serial=lambda:None, _set_serial_delivery_tick=lambda enabled:None,
        _set_serial_delivery_status=lambda *a, **k:None, _log_warning=lambda msg:None)
    def queue(index, serials, concurrent=True):
        result = ns['_queue_direct_delivery'](serials, [index], scope_label='test', mode='selected',
                                              bulk_authorized=True, afk_concurrent=concurrent)
        ns['_pending_serial_delivery_sequences'][-1]['direct_delivery'].clock = clock
        return result
    return ns, queue, submitted, clock


def test_independent_500_item_lists_finish_without_summed_target_delays(queues):
    ns, queue, submitted, clock = queues
    lists = {i:['@U'+str(i)+str(n).zfill(4)+'x'*160 for n in range(500)] for i in (1,2,3)}
    for i, serials in lists.items():
        queue(i, serials)
    sequences = list(ns['_pending_serial_delivery_sequences'])
    engines = [seq['direct_delivery'] for seq in sequences]
    process = ns['_process_pending_serial_delivery_sequences']
    process()
    assert [pc for pc, _, _ in submitted] == [1,2,3]  # same callback, one per guest
    assert {t for _, _, t in submitted} == {0.0}
    progress = ns['serial_delivery_progress']()
    assert progress['active'] and len(progress['players']) == 3 and progress['total_serials'] == 1500
    process()
    assert len(submitted) == 3  # no duplicate/early insertion
    for _ in range(10000):
        if not ns['_pending_serial_delivery_sequences']:
            break
        clock.value += .01
        process()
    assert not ns['_pending_serial_delivery_sequences']
    for i, expected in lists.items():
        assert [s for pc, s, _ in submitted if pc == i] == expected
    assert len(submitted) == 1500 and all(e.done and not e.error for e in engines)
    times = [[t for pc, _, t in submitted if pc == i] for i in (1,2,3)]
    assert times[0] == times[1] == times[2]
    assert all(b-a >= delivery.ITEM_GAP for a,b in zip(times[0],times[0][1:]))
    for end in engines[0].ends[:-1]:
        assert times[0][end]-times[0][end-1] >= delivery.CHUNK_PAUSE
    assert clock.value-times[0][-1] >= delivery.SETTLE_SECONDS


def test_admission_mixes_manual_afk_unique_targets_and_four_player_bound(queues):
    ns, queue, submitted, clock = queues
    queue(1, ['@UA'])
    with pytest.raises(RuntimeError, match='already has'):
        queue(1, ['@Uduplicate'])
    queue(2, ['@Umanual'], concurrent=False)
    queue(3, ['@UC']); queue(0, ['@Uhost'], concurrent=False)
    assert not ns['_afk_direct_delivery_available']()
    with pytest.raises(RuntimeError, match='Four player'):
        queue(4, ['@Ufifth'])
    assert len(ns['_pending_serial_delivery_sequences']) == 4 and not submitted


def test_existing_manual_send_only_blocks_its_own_target(queues):
    ns, queue, _, _ = queues
    queue(1, ['@UA'], concurrent=False)
    assert ns['_afk_direct_delivery_available'](2)
    assert not ns['_afk_direct_delivery_available'](1)
    queue(2, ['@UB'])


def test_one_target_failure_does_not_cancel_or_retarget_others(queues):
    ns, queue, submitted, clock = queues
    queue(1, ['@UA']*2); queue(2, ['@UB']*2)
    first = ns['_pending_serial_delivery_sequences'][0]
    first['direct_delivery'].resolve = lambda _: (_ for _ in ()).throw(RuntimeError('Original player left'))
    for _ in range(400):
        ns['_process_pending_serial_delivery_sequences']()
        clock.value += .01
    assert [(pc,s) for pc,s,t in submitted] == [(2,'@UB'),(2,'@UB')]
    assert 'Original player left' in first['afk_error']
    assert not ns['_pending_serial_delivery_sequences']


def test_full_afk_jobs_send_independent_500_selections_and_wait_for_settlement_before_kicks(queues, monkeypatch):
    ns, _, submitted, clock = queues
    package = 'concurrent_direct_test'
    monkeypatch.setitem(sys.modules, package+'.afk_loot', loot_selector)
    monkeypatch.setattr(afk, '__package__', package)
    monkeypatch.setattr(afk, '_loot_rng', random.Random(19))
    monkeypatch.setattr(afk.time, 'monotonic', clock)
    # Real queue creation binds its default clock at import time; explicitly supply
    # the deterministic test clock without changing any engine behavior.
    original_delivery = delivery.Delivery
    def make_delivery(*args, **kwargs):
        kwargs['clock'] = clock
        return original_delivery(*args, **kwargs)
    monkeypatch.setattr(delivery, 'Delivery', make_delivery)
    rewards = SimpleNamespace(**ns)
    game = afk.Game()
    pool = ['@U'+str(n).zfill(4)+'x'*150 for n in range(985)]
    game.prepare_loot = lambda p:pool
    game.classify_loot = lambda serials:[None]*len(serials)
    game.authorize_bulk_loot = lambda password=None:True
    game.is_host = lambda:True
    game.load_join_count = lambda:0
    game.save_join_count = lambda count:None
    game.save_run_report = lambda job:'test-run-report.json'
    game.roster = lambda:('world', [row(i,i) for i in (1,2,3)])
    game.backend = lambda:SimpleNamespace(serial_rewards=rewards)
    kicks=[]
    game.kick = lambda job:kicks.append((job['token'],clock.value)) or {'ok':True,'message':'kick'}
    lobby = afk.Lobby(game)
    assert lobby.start(dict(loot=True, loot_mode='random70', random_count=500,
                            concurrent_guests=True, auto_kick=True))['ok']
    lobby.tick()
    sequences = list(ns['_pending_serial_delivery_sequences'])
    assert len(sequences) == 3 and all(seq['afk_concurrent'] for seq in sequences)
    selected = {seq['targets'][0]:list(seq['serials']) for seq in sequences}
    assert len({tuple(sorted(value)) for value in selected.values()}) == 3
    for _ in range(10000):
        ns['_process_pending_serial_delivery_sequences']()
        lobby.tick()
        if len(kicks)==3:
            break
        clock.value += .01
    assert len(kicks)==3 and len(lobby.history)==3
    for player, serials in selected.items():
        actual=[(s,t) for pc,s,t in submitted if pc==player]
        assert [s for s,t in actual] == serials and len(actual)==500
        kick_at=next(t for pc,t in kicks if pc==player)
        assert kick_at-actual[-1][1] >= delivery.SETTLE_SECONDS+15
    assert all(any(result['step']=='loot' and result['ok'] and '500/500' in result['message']
                   for result in report['results']) for report in lobby.history)
