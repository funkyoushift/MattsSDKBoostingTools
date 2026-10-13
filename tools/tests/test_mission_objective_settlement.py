"""Finishing is not finished: don't certify native callbacks before they settle."""
import importlib.util
import importlib.resources
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

ROOT = Path(__file__).parents[2] / 'mod_extracted/MattsSDKBoostingTools'


@pytest.fixture
def objective(monkeypatch):
    monkeypatch.setattr(importlib.resources, 'files', lambda package: ROOT)
    spec = importlib.util.spec_from_file_location('objective_settlement_test', ROOT / 'mission_objectives.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = NS(world_address=101, snapshot=lambda: {})
    mission = dict(token='mission-token', state='active')
    progress = NS(_engine=lambda: engine, _party=lambda: [], _binding=lambda rows: [],
                  _row=lambda snapshot, name: mission, _state=lambda row: row['state'])
    monkeypatch.setattr(module, '_progress', lambda: progress)
    monkeypatch.setattr(module, '_save', lambda: None)
    module._last = dict(id='receipt', pid=module.os.getpid(), world=101, binding=[],
                        token='mission-token', mission='Mission_Main_Beach',
                        objective=dict(token='objective-token'), state='uncertain', returned=True)
    return module


@pytest.mark.parametrize('phase', [10, 11, 12])
def test_finish_phases_remain_pending(objective, monkeypatch, phase):
    monkeypatch.setattr(objective, 'read', lambda engine, row: [dict(token='objective-token', state=phase)])
    result = objective.status()
    assert result['state'] == 'running'
    assert not result['ok']
    assert 'finishing' in result['message']


def test_only_postfinished_confirms(objective, monkeypatch):
    monkeypatch.setattr(objective, 'read', lambda engine, row: [dict(token='objective-token', state=13)])
    result = objective.status()
    assert result['state'] == 'completed'
    assert result['ok']


def test_terminal_objective_can_be_released_after_mission_finishes(objective, monkeypatch):
    objective._progress()._row = lambda *args: dict(token='mission-token', state='completed')
    monkeypatch.setattr(objective, 'read', lambda *args: [])
    result = objective.status()
    assert result['ok'] and result['state'] == 'completed'
    assert not result['replay_supported'] and result['restart_supported']


def test_missing_objective_in_active_mission_is_not_completion(objective, monkeypatch):
    monkeypatch.setattr(objective, 'read', lambda *args: [])
    assert not objective.status()['ok']


def test_terminal_without_native_return_is_not_certified(objective, monkeypatch):
    objective._last.pop('returned')
    objective._progress()._row = lambda *args: dict(token='mission-token', state='completed')
    monkeypatch.setattr(objective, 'read', lambda *args: [])
    assert not objective.status()['ok']


def test_replaced_instance_does_not_confirm_old_objective(objective, monkeypatch):
    progress = objective._progress()
    progress._row = lambda snapshot, name: dict(token='replacement')
    monkeypatch.setattr(objective, '_progress', lambda: progress)
    monkeypatch.setattr(objective, 'read', lambda *args: pytest.fail('Must reject before reading replacement'))
    assert objective.status()['state'] == 'uncertain'


def test_replay_waits_for_playable_checkpoint(objective, monkeypatch):
    objective._last['operation'] = 'replay'
    rows = [dict(token='objective-token', state=None, hidden=False)]
    monkeypatch.setattr(objective, 'read', lambda *args: rows)
    assert objective.status()['state'] == 'uncertain'
    rows[0]['state'] = 4
    result = objective.status()
    assert result['ok'] and result['state'] == 'replayed'
    assert not result['replay_supported']


def test_replay_accepts_authored_earlier_checkpoint(objective, monkeypatch):
    objective._last['operation'] = 'replay'
    monkeypatch.setattr(objective, 'read', lambda *args: [
        dict(token='objective-token', state=None, hidden=False),
        dict(token='authored-earlier-step', state=4, hidden=False)])
    assert objective.status()['state'] == 'replayed'


def test_uncertain_replay_never_issues_second_native_call(objective, monkeypatch):
    progress = objective._progress()
    progress._job = None
    monkeypatch.setattr(objective, '_progress', lambda: progress)
    objective._last['operation'] = 'replay'
    with pytest.raises(ValueError, match='No completed objective'):
        objective.replay_last(dict(acknowledge_shared_progress=True))
