"""Configured count -> authorization -> class filtering -> paced native-call boundary.

The Unreal insertion is stubbed; these tests do not claim guest inventory proof.
"""
import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

SDK = Path(__file__).resolve().parents[2] / 'mod_extracted/MattsSDKBoostingTools'


@pytest.mark.parametrize('count', [1, 35, 70, 71, 85, 500])
@pytest.mark.parametrize('pool_size', [40, 985])
@pytest.mark.parametrize('concurrent', [False, True])
def test_count_survives_authorization_selection_and_all_batches(monkeypatch, count, pool_size, concurrent):
    package = types.ModuleType('afk_count_test')
    package.__path__ = [str(SDK)]
    monkeypatch.setitem(sys.modules, package.__name__, package)
    modules = {}
    for name in ('afk_loot', 'afk_lobby', 'direct_delivery'):
        spec = importlib.util.spec_from_file_location(f'{package.__name__}.{name}', SDK / f'{name}.py')
        module = importlib.util.module_from_spec(spec)
        monkeypatch.setitem(sys.modules, spec.name, module)
        spec.loader.exec_module(module)
        setattr(package, name, module)
        modules[name] = module
    afk, direct = modules['afk_lobby'], modules['direct_delivery']
    pool = ['@U' + str(i).zfill(5) + 'x' * 150 for i in range(pool_size)]
    game = afk.Game()
    game.prepare_loot = lambda payload: payload['codes'].splitlines()
    game.classify_loot = lambda serials: [None] * len(serials)
    game.is_host = lambda: True
    game.load_join_count = lambda: 0
    # Represent the actual persisted installation unlock; no password resubmission.
    unlocked = False
    game.authorize_bulk_loot = lambda password=None: unlocked
    lobby = afk.Lobby(game)
    payload = {'loot':True, 'loot_mode':'random70', 'random_count':str(count), 'codes':'\n'.join(pool)}
    payload['concurrent_guests'] = concurrent
    expected = min(count, pool_size)
    first = lobby.start(payload)
    if expected > 70:
        assert first['password_required'] and not lobby.enabled
        unlocked = True
        assert lobby.start(payload)['ok']
    else:
        assert first['ok']
    assert lobby.config['random_count'] == count
    assert lobby.config['bulk_loot_authorized'] == (expected > 70)
    sequences, submitted, queued = [], [], []
    clock = [0.0]

    def send(serials, indices, **kwargs):
        assert indices == [2]
        assert kwargs.get('bulk_authorized', False) == (expected > 70)
        assert kwargs.get('afk_concurrent', False) == concurrent
        engine = direct.Delivery(serials, [{'name':'Guest','token':'ps'}],
            lambda target: target['token'], lambda pc, serial: submitted.append((pc, serial)),
            SimpleNamespace(event=lambda *a, **k: None, path=Path('test-delivery.jsonl')), clock=lambda: clock[0])
        queued.append(engine)
        sequences.append({'direct_delivery':engine, 'chunks':engine.chunks, 'index':0})

    rewards = SimpleNamespace(_pending_serial_delivery_sequences=sequences,
        _afk_direct_delivery_available=lambda index: not sequences,
        _serial_delivery_busy=lambda: bool(sequences), _do_give_serial_to_player_indices=send,
        serial_delivery_status=lambda: 'finished')
    game.backend = lambda: SimpleNamespace(serial_rewards=rewards)
    job = {'pc':'pc', 'token':'ps', 'index':2, 'name':'Guest'}
    assert game.step('loot', job, lobby.config) is None
    assert len(job['loot_selection']) == expected
    assert game.step('loot', job, lobby.config) is None and len(queued) == 1
    engine = queued[0]
    for _ in range(10000):
        if engine.done:
            break
        clock[0] = max(clock[0], engine.next, min(t['ready'] for t in engine.targets if not t['done']))
        engine.step()
    assert engine.done and not engine.error
    assert [serial for pc, serial in submitted] == job['loot_selection']
    assert len(submitted) == len(set(serial for pc, serial in submitted)) == expected
    assert all(sum(map(len, chunk)) <= direct.CHARACTER_BUDGET for chunk in engine.chunks)
    if expected == 500:
        assert len(engine.chunks) > 1
    sequence = sequences.pop()
    sequence['index'] = len(sequence['chunks'])
    assert game.step('loot', job, lobby.config)['ok'] and len(queued) == 1
