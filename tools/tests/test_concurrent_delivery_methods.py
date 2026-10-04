"""Shared manual/AFK admission, immutable targets, and independent completion."""
import ast
import sys
import types
import typing
from types import SimpleNamespace

import pytest

from test_afk_concurrent import queues, afk, make_lobby, row, ticks
from test_direct_delivery import SDK, load_functions


@pytest.mark.parametrize('count', [1, 35, 70, 71, 85, 500])
@pytest.mark.parametrize('legacy', [False, True])
def test_manual_and_afk_lists_overlap_with_exact_counts(queues, count, legacy):
    ns, queue, submitted, clock = queues
    queue(1, ['@UA'] * 500)
    ns['_do_give_serial_to_player_indices'](['@UB'] * count, [2],
        bulk_authorized=True, delivery_method='rewards' if legacy else 'direct')
    ns['_pending_serial_delivery_sequences'][-1]['direct_delivery'].clock = clock
    jobs = list(ns['_pending_serial_delivery_sequences'])
    ns['_process_pending_serial_delivery_sequences']()
    assert [(p, s) for p, s, _ in submitted] == [(1, '@UA'), (2, '@UB')]
    for _ in range(10000):
        if not ns['_pending_serial_delivery_sequences']:
            break
        clock.value += .01
        ns['_process_pending_serial_delivery_sequences']()
    assert [s for p, s, _ in submitted if p == 1] == ['@UA'] * 500
    assert [s for p, s, _ in submitted if p == 2] == ['@UB'] * count
    assert all(job['direct_delivery'].done and not job['direct_delivery'].error for job in jobs)
    assert not ns['_pending_serial_delivery_sequences']


def test_party_request_is_atomic_and_does_not_replace_running_jobs(queues):
    ns, queue, _, _ = queues
    queue(1, ['@UA'], concurrent=False)
    original = list(ns['_pending_serial_delivery_sequences'])
    with pytest.raises(RuntimeError, match='no part'):
        ns['_queue_direct_delivery'](['@UB'], [1, 2, 3], scope_label='party', mode='all', bulk_authorized=False)
    assert ns['_pending_serial_delivery_sequences'] == original
    ns['_queue_direct_delivery'](['@UC'], [2, 3], scope_label='others', mode='nonhost', bulk_authorized=False)
    assert len(ns['serial_delivery_progress']()['players']) == 3


def test_exclusive_recovery_cannot_mix_either_direction(queues):
    ns, queue, _, _ = queues
    ns['_queue_direct_delivery'](['@UA'], [1], scope_label='recovery', mode='selected', bulk_authorized=True, exclusive=True)
    assert not ns['_afk_direct_delivery_available'](2)
    with pytest.raises(RuntimeError, match='exclusive'):
        queue(2, ['@UB'], concurrent=False)
    ns['_pending_serial_delivery_sequences'].clear()
    queue(2, ['@UB'], concurrent=False)
    with pytest.raises(RuntimeError, match='exclusive'):
        ns['_queue_direct_delivery'](['@UA'], [1], scope_label='recovery', mode='selected', bulk_authorized=True, exclusive=True)


def backend_functions(names, **values):
    tree = ast.parse((SDK / 'backend_actions.py').read_text(encoding='utf-8'))
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    ns = {'Any':object, 'MAX_ITEM_LEVEL':70, '_installation_authorized':lambda *a:True, **values}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), 'backend-test', 'exec'), ns)
    return ns


@pytest.mark.parametrize('mode', ['selected', 'local', 'all', 'nonhost'])
def test_backend_modes_share_queue_and_keep_their_own_report(queues, mode):
    ns, queue, _, _ = queues
    queue(1, ['@UA'])
    backend = backend_functions({'_deliver_serials_with_target', '_serial_delivery_count_note'},
        serial_rewards=SimpleNamespace(**ns), _players=lambda:[(2, 'B'), (3, 'C')],
        _non_host_party_player_indices=lambda:[2,3], _local_party_index=lambda:0,
        get_selected_player_index=lambda:2, get_selected_player_name=lambda:'B')
    result = backend['_deliver_serials_with_target'](['@UB'], mode)
    assert result['ok'], result
    assert result['report_path'] == ns['_pending_serial_delivery_sequences'][-1]['report_path']
    assert result['report_path'] != ns['_pending_serial_delivery_sequences'][0]['report_path']


def test_async_conversion_pins_original_target_even_after_selection_and_slot_change(queues):
    ns, _, _, _ = queues
    callbacks, finished, selected = [], [], [1]
    rewards = SimpleNamespace(**ns)
    rewards.needs_async_serial_resolution = lambda _:True
    rewards.queue_serial_resolution = lambda rows, callback:callbacks.append(callback)
    backend = backend_functions({'give_serials', '_deliver_serials_with_target', '_serial_delivery_count_note'},
        serial_rewards=rewards, _parse_serial_text=lambda text:[text],
        get_selected_player_index=lambda:selected[0], _players=lambda:[(3,'original'), (2,'new')])
    backend['_finish_give_serials'] = lambda rows, **kw: finished.append(kw) or {'ok':True}
    assert backend['give_serials']('decoded code')['ok']
    selected[0] = 2
    callbacks[0](['@UA'], None)
    assert finished[0]['target_snapshot'] == [{'state':1}]
    rewards._direct_delivery_preflight = lambda i:{'state':1 if i == 3 else i}
    result = backend['_deliver_serials_with_target'](['@UA'], 'selected', target_snapshot=finished[0]['target_snapshot'])
    assert result['ok'] and ns['_pending_serial_delivery_sequences'][-1]['targets'] == [3]
    rewards._direct_delivery_preflight = lambda i:{'state':i}
    result = backend['_deliver_serials_with_target'](['@UB'], 'selected', target_snapshot=finished[0]['target_snapshot'])
    assert not result['ok'] and 'original delivery target' in result['message']
    assert len(ns['_pending_serial_delivery_sequences']) == 1


def test_manual_delivery_defers_afk_kick_including_shared_connections(queues):
    ns, queue, _, _ = queues
    queue(2, ['@UB'], concurrent=False)
    game = afk.Game()
    game.is_host = lambda:True
    rows = [dict(row('A',1),connection='shared'), dict(row('B',2),connection='shared')]
    game.roster = lambda:('world',rows)
    calls = []
    game.backend = lambda:SimpleNamespace(serial_rewards=SimpleNamespace(**ns),
        _kick_party_player_by_index=lambda *args:calls.append(args) or True)
    assert game.kick({'token':'A'})['deferred'] and not calls
    rows[1]['connection'] = 'other'
    assert game.kick({'token':'A'})['ok'] and len(calls) == 1
    rows[1]['connection'] = None
    assert game.kick({'token':'A'})['deferred'] and len(calls) == 1


def test_deferred_kicks_do_not_exhaust_retry_limit():
    game, lobby = make_lobby(auto_kick=True)
    game.rows = [row('A')]
    game.kick = lambda job:{'ok':False, 'deferred':True}
    ticks(lobby)
    assert lobby.completed
    for n in range(10):
        lobby._flush_kicks(game.rows, 1000000000 + n * 20)
    assert not lobby.completed[0].get('kick_attempted')
    assert not lobby.completed[0].get('kick_attempts')


def test_async_finish_forwards_pinned_targets_through_real_finish(queues):
    ns, _, _, _ = queues
    callbacks, selected = [], [1]
    rewards = SimpleNamespace(**ns)
    rewards.needs_async_serial_resolution = lambda _:True
    rewards.queue_serial_resolution = lambda rows, cb:callbacks.append(cb)
    rewards._log_error = lambda message:pytest.fail(message)
    backend = backend_functions({'give_serials', '_finish_give_serials', '_deliver_serials_with_target', '_serial_delivery_count_note'},
        serial_rewards=rewards, _parse_serial_text=lambda text:[text],
        _clamp_int=lambda value, low, high:int(value), _truthy=bool,
        _serials_with_level_override=lambda rows, enabled, level:(rows, 0, []),
        note_last_command=lambda *a, **k:None,
        get_selected_player_index=lambda:selected[0], _players=lambda:[(3,'original'), (2,'new')])
    assert backend['give_serials']('decoded code')['ok']
    selected[0] = 2
    rewards._direct_delivery_preflight = lambda i:{'state':1 if i == 3 else i}
    callbacks[0](['@UA'], None)
    assert ns['_pending_serial_delivery_sequences'][0]['targets'] == [3]


def test_console_async_conversion_also_pins_targets(monkeypatch):
    callbacks, calls = [], []
    package = types.ModuleType('console_concurrent_test')
    package.backend_actions = SimpleNamespace(_deliver_serials_with_target=lambda *a, **k:calls.append((a,k)) or {'ok':True})
    monkeypatch.setitem(sys.modules, package.__name__, package)
    ns = load_functions({'_cmd_give_serial'}, __package__=package.__name__,
        argparse=SimpleNamespace(Namespace=object), Optional=typing.Optional,
        command=lambda *a, **k:lambda function:function, _safe_int=int,
        _expand_serial_token=lambda text:[text], needs_async_serial_resolution=lambda rows:True,
        _direct_delivery_preflight=lambda index:{'original':index},
        queue_serial_resolution=lambda rows, callback:callbacks.append(callback),
        _set_serial_delivery_status=lambda *a, **k:None, _log_error=lambda message:pytest.fail(message))
    ns['_cmd_give_serial'](SimpleNamespace(parts=['decoded code', 'index', '2', 'all']))
    ns['_direct_delivery_preflight'] = lambda index:{'replacement':index}
    callbacks[0](['@UA'], None)
    assert calls[0][1]['target_snapshot'] == [{'original':2}]
