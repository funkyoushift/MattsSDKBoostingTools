"""Offline job safety and selection tests; no guest persistence claims."""
import importlib.util
import importlib.resources
import json
import copy
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

ROOT = Path(__file__).parents[2] / 'mod_extracted/MattsSDKBoostingTools'


@pytest.fixture
def mod(monkeypatch):
    monkeypatch.setattr(importlib.resources, 'files', lambda package: ROOT)
    spec = importlib.util.spec_from_file_location('mission_test', ROOT / 'mission_progression.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row(name='Mission_Main_Beach', state='active', token='01' * 12):
    return dict(source_identity={'name': name}, token=token, generated=0,
                replication_type=0, status_fact={'known_status': state})


def test_current_requires_exact_tracked_record(mod):
    r = row()
    snapshot = dict(missions=[r], tracked=[r['token']])
    assert mod.select(snapshot, 'current') == ['Mission_Main_Beach']
    snapshot['tracked'] = ['00' * 12]
    with pytest.raises(ValueError, match='Track exactly one'):
        mod.select(snapshot, 'current')


@pytest.mark.parametrize('scope', ['objective', 'undo_objective', 'reset_all'])
def test_unverified_operations_do_not_touch_runtime(mod, scope):
    with pytest.raises(ValueError):
        mod.select({}, scope)


def test_unknown_duplicate_and_generated_missions_rejected(mod):
    for names in [['unreviewed'], ['Mission_Main_Beach'] * 2]:
        with pytest.raises(ValueError):
            mod.select({}, 'named', names)
    r = row(); r['generated'] = 1
    with pytest.raises(ValueError):
        mod._row({'missions': [r]}, 'Mission_Main_Beach')


def test_explicit_shared_acknowledgement_before_native_access(mod):
    assert not mod.dispatch('mission_start', {})['ok']
    assert mod._runtime is None


def test_party_change_stops_before_journal_or_native_mutation(mod, monkeypatch, tmp_path):
    r = row()
    monkeypatch.setattr(mod, '_engine', lambda: NS(snapshot=lambda: {'missions': [r]}))
    monkeypatch.setattr(mod, '_party', lambda: [])
    mod._job = dict(id='job', state='running', binding=[('old', 'state', 1)], index=0,
                    names=['Mission_Main_Beach'], journal=str(tmp_path/'job.jsonl'))
    result = mod.step('job')
    assert result['state'] == 'stopped'
    events = [json.loads(x) for x in (tmp_path/'job.jsonl').read_text().splitlines()]
    assert [x['event'] for x in events] == ['state']


def test_wrong_job_and_cancellation_do_not_repeat_work(mod, tmp_path):
    mod._job = dict(id='job', state='running', index=1, completed=['done'], journal=str(tmp_path/'job.jsonl'))
    with pytest.raises(ValueError):
        mod.step('other')
    assert mod.cancel('job')['state'] == 'cancelled'
    assert mod.step('job')['completed'] == ['done']


def test_uncertain_job_cannot_be_overwritten_or_cancelled_to_bypass(mod):
    mod._job = dict(id='job', state='uncertain')
    with pytest.raises(ValueError, match='uncertain'):
        mod.start({})
    assert mod.cancel('job')['state'] == 'uncertain'


@pytest.mark.parametrize('native_matches', [True, False])
def test_reset_accept_complete_is_one_call_per_step_and_never_retries_uncertain(mod, monkeypatch, tmp_path, native_matches):
    r = dict(row(state='completed'), record='0x100000', storage='0x200000')
    calls = []
    base = 0x140000000
    def read(address, size):
        return b'\1' if size == 1 else bytes.fromhex(r['token'])
    def u64(address):
        return {0x100000: 0x300000, 0x1000a8: 0x200000,
                0x3000f8: base + 0xd80660, 0x300110: base + 0x419fefa}[address]
    engine = NS(base=base, read=read, u64=u64,
                snapshot=lambda: {'missions': [copy.deepcopy(r)]})
    def factory(*signature):
        def bind(address):
            def invoke(pointer, state, flag):
                calls.append((address, state))
                if native_matches:
                    r['status_fact']['known_status'] = 'available' if state == 2 else 'completed'
            return invoke
        return bind
    def accept(*args):
        calls.append(('accept', args[1:]))
        r['status_fact']['known_status'] = 'accepted'
    pc = NS(_path_name=lambda: 'pc', PlayerState=NS(StableIndex=2), ServerActivateMission=accept)
    monkeypatch.setitem(sys.modules, 'unrealsdk', NS(make_struct=lambda *a, **k: NS(_get_address=lambda: 123)))
    monkeypatch.setattr(mod.C, 'WINFUNCTYPE', factory)
    monkeypatch.setattr(mod, '_engine', lambda: engine)
    monkeypatch.setattr(mod, '_validate_exit', lambda *args: None)
    monkeypatch.setattr(mod, '_party', lambda: [{'pc': pc}])
    monkeypatch.setattr(mod, '_binding', lambda rows: ['fixed'])
    mod._job = dict(id='job', ok=True, state='running', binding=['fixed'], target='pc',
                    names=['Mission_Main_Beach'], index=0, completed=[], phase='prepare',
                    journal=str(tmp_path/'job.jsonl'))
    first = mod.step('job')
    assert len(calls) == 1
    if not native_matches:
        assert first['state'] == 'uncertain'
        mod.step('job')
        assert len(calls) == 1
    else:
        assert first['phase'] == 'accept'
        assert mod.step('job')['phase'] == 'complete'
        assert len(calls) == 2
        assert mod.step('job')['state'] == 'completed'
        mod.step('job')
        assert len(calls) == 3


def test_game_completed_after_acceptance_advances_without_native_call(mod, monkeypatch, tmp_path):
    pc = NS(_path_name=lambda: 'pc')
    monkeypatch.setattr(mod, '_engine', lambda: NS(snapshot=lambda: {'missions': [row(state='completed')]}))
    monkeypatch.setattr(mod, '_party', lambda: [{'pc': pc}])
    monkeypatch.setattr(mod, '_binding', lambda rows: ['fixed'])
    monkeypatch.setattr(mod, '_validate_exit', lambda *args: None)
    mod._job = dict(id='job', ok=False, state='stopped', binding=['fixed'], target='pc',
                    names=['Mission_Main_Beach'], index=0, completed=[], phase='complete',
                    journal=str(tmp_path/'job.jsonl'))
    assert mod.resume('job')['state'] == 'running'
    assert mod.step('job')['state'] == 'completed'
    assert mod._job['completed'] == ['Mission_Main_Beach']
    events = [json.loads(x)['event'] for x in (tmp_path/'job.jsonl').read_text().splitlines()]
    assert events == ['resume', 'observed_completed', 'state']


@pytest.mark.parametrize('state', ['uncertain', 'cancelled', 'completed', 'running'])
def test_resume_does_not_bypass_terminal_or_uncertain_state(mod, state):
    mod._job = dict(id='job', state=state, phase='complete')
    with pytest.raises(ValueError):
        mod.resume('job')


def test_resume_requires_original_party_and_completed_record(mod, monkeypatch):
    mod._job = dict(id='job', state='stopped', phase='complete', binding=['original'], names=['Mission_Main_Beach'], index=0)
    monkeypatch.setattr(mod, '_party', lambda: [])
    monkeypatch.setattr(mod, '_binding', lambda rows: ['changed'])
    with pytest.raises(ValueError, match='party changed'):
        mod.resume('job')
    monkeypatch.setattr(mod, '_binding', lambda rows: ['original'])
    monkeypatch.setattr(mod, '_engine', lambda: NS(snapshot=lambda: {'missions': [row(state='active')]}))
    monkeypatch.setattr(mod, '_validate_exit', lambda *args: None)
    with pytest.raises(ValueError, match='not confirmed completed'):
        mod.resume('job')


def test_category_rechecks_locked_missions_after_progress(mod, monkeypatch, tmp_path):
    names = list(mod.CATALOG)[:3]
    mod._job = dict(names=names[:], index=0, initial_completed=[], pending=[], stall_since=None,
                    phase='prepare', state='running', journal=str(tmp_path/'job.jsonl'))
    snapshot = {'missions': [row(names[0], 'locked'), row(names[1], 'available'), row(names[2], 'locked')]}
    assert mod._schedule_category(snapshot)
    assert mod._job['names'] == [names[1], names[0], names[2]]
    mod._job['index'] = 1
    snapshot['missions'][0]['status_fact']['known_status'] = 'available'
    assert mod._schedule_category(snapshot)
    assert mod._job['names'][1] == names[0]


def test_category_reports_unresolved_instead_of_false_completion(mod, monkeypatch, tmp_path):
    name = next(iter(mod.CATALOG))
    mod._job = dict(names=[name], index=0, initial_completed=[], pending=[], stall_since=None,
                    phase='prepare', state='running', journal=str(tmp_path/'job.jsonl'))
    snapshot = {'missions': [row(name, 'locked')]}
    monkeypatch.setattr(mod.time, 'monotonic', lambda: 100)
    assert not mod._schedule_category(snapshot)
    assert mod._job['state'] == 'running'
    monkeypatch.setattr(mod.time, 'monotonic', lambda: 111)
    assert not mod._schedule_category(snapshot)
    assert mod._job['state'] == 'stopped'
    assert mod._job['pending'][0]['name'] == name
    assert mod._job['index'] == 0


def test_category_does_not_reset_cascaded_completion(mod):
    name = next(iter(mod.CATALOG))
    mod._job = dict(names=[name], index=0, initial_completed=[], pending=[], stall_since=None, phase='prepare')
    assert mod._schedule_category({'missions': [row(name, 'completed')]})
    assert mod._job['phase'] == 'complete'
    mod._job.update(initial_completed=[name], phase='prepare')
    assert mod._schedule_category({'missions': [row(name, 'completed')]})
    assert mod._job['phase'] == 'prepare'


@pytest.mark.parametrize('natural_state', ['active', 'accepted', 'completed'])
def test_auto_activation_after_reset_skips_duplicate_accept(mod, monkeypatch, tmp_path, natural_state):
    r = dict(row(state=natural_state), record='0x100000', storage='0x200000')
    base = 0x140000000
    calls = []
    pc = NS(_path_name=lambda: 'pc')  # No acceptance method: calling it fails the test.
    engine = NS(base=base, snapshot=lambda: {'missions': [copy.deepcopy(r)]}, read=lambda *args: b'\1',
                u64=lambda address: {0x100000: 0x300000, 0x1000a8: 0x200000,
                0x3000f8: base + 0xd80660, 0x300110: base + 0x419fefa}[address])
    def factory(*signature):
        def bind(address):
            def invoke(*args):
                calls.append(address)
                r['status_fact']['known_status'] = 'completed'
            return invoke
        return bind
    monkeypatch.setattr(mod.C, 'WINFUNCTYPE', factory)
    monkeypatch.setattr(mod, '_engine', lambda: engine)
    monkeypatch.setattr(mod, '_party', lambda: [{'pc': pc}])
    monkeypatch.setattr(mod, '_binding', lambda rows: ['fixed'])
    monkeypatch.setattr(mod, '_validate_exit', lambda *args: None)
    mod._job = dict(id='job', ok=False, state='stopped', binding=['fixed'], target='pc',
                    names=['Mission_Main_Beach'], index=0, completed=[], phase='accept',
                    journal=str(tmp_path/'job.jsonl'))
    assert mod.resume('job')['state'] == 'running'
    assert mod.step('job')['state'] == 'completed'
    assert calls == ([] if natural_state == 'completed' else [base + 0xf19ee4])


def test_automatic_prerequisites_are_bounded_and_not_repeated(mod, monkeypatch):
    import types
    pkg = types.ModuleType('repair_test')
    pkg.mission_discovery = NS(plan=lambda *args: [
        {'name': 'electi', 'blocked_reason': None},
        {'name': 'heist', 'blocked_reason': None},
        {'name': 'vending', 'blocked_reason': 'parent unfinished'},
        {'name': 'travel_0', 'blocked_reason': None}])
    monkeypatch.setitem(sys.modules, 'repair_test', pkg)
    monkeypatch.setattr(mod, '__package__', 'repair_test')
    mod._job = {'checked_prerequisites': ['electi']}
    assert mod._pending_repairs({}) == ['heist']


def test_dynamic_resume_requires_new_eligibility_or_reviewed_repair(mod, monkeypatch, tmp_path):
    name = next(iter(mod.CATALOG))
    mod._job = dict(id='job', state='stopped', phase='prepare', dynamic=True,
                    binding=['fixed'], names=[name], index=0, journal=str(tmp_path/'job.jsonl'))
    monkeypatch.setattr(mod, '_party', lambda: [])
    monkeypatch.setattr(mod, '_binding', lambda rows: ['fixed'])
    monkeypatch.setattr(mod, '_engine', lambda: NS(snapshot=lambda: {'missions': [row(name, 'locked')]}))
    monkeypatch.setattr(mod, '_pending_repairs', lambda snapshot: [])
    with pytest.raises(ValueError, match='No newly eligible'):
        mod.resume('job')
    monkeypatch.setattr(mod, '_pending_repairs', lambda snapshot: ['electi'])
    assert mod.resume('job')['state'] == 'running'
    assert mod._job['index'] == 0


def test_review_console_stops_on_uncertain_step(monkeypatch):
    import argparse
    import types
    parser = argparse.ArgumentParser()
    def command(*args, **kwargs):
        def decorate(fn):
            fn.add_argument = parser.add_argument
            return fn
        return decorate
    calls = []
    def action(name, payload, **kwargs):
        calls.append((name, payload))
        return dict(ok=name == 'mission_start', id='job',
                    state='running' if name == 'mission_start' else 'uncertain')
    pkg = types.ModuleType('mission_console_test'); pkg.__path__ = [str(ROOT)]
    monkeypatch.setitem(sys.modules, 'mission_console_test', pkg)
    monkeypatch.setitem(sys.modules, 'mods_base', NS(command=command))
    monkeypatch.setitem(sys.modules, 'unrealsdk', NS(logging=NS(info=lambda text: None)))
    monkeypatch.setitem(sys.modules, 'mission_console_test.backend_actions', NS(run_quick_menu_action=action))
    spec = importlib.util.spec_from_file_location('mission_console_test.mission_commands', ROOT / 'mission_commands.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    args = parser.parse_args(['run', '--player', 'Guest', '--reset-completed'])
    module.mission_command(args)
    assert [x[0] for x in calls] == ['mission_start', 'mission_step']
    assert calls[0][1]['target_player'] == 'Guest'
    assert calls[0][1]['reset_completed'] is True
