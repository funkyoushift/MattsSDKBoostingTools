from mission_profile_fixture import exec_with_profiles
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
    exec_with_profiles(spec, module, monkeypatch)
    monkeypatch.setattr(module, '_dlc_requirement', lambda name: None)
    monkeypatch.setattr(module, '_credit_completed', lambda engine, party, name: None)
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


@pytest.mark.parametrize('name', ['Mission_Micro_BackMcCrackyPt2', 'Mission_Micro_BackMcCrackyPt3'])
def test_legacy_split_exclusion_requires_native_absence(mod, name):
    assert 'Legacy split' in mod._automatic_exclusion({'missions': []}, name)
    for status in ('available', 'locked', 'completed'):
        assert mod._automatic_exclusion({'missions': [row(name, status)]}, name) is None
    # Ambiguous/generated records must reach the existing rejection path.
    assert mod._automatic_exclusion({'missions': [dict(row(name), generated=1)]}, name) is None


def test_other_missing_missions_are_never_silently_excluded(mod):
    assert mod._automatic_exclusion({'missions': []}, 'Mission_Main_Beach') is None


@pytest.mark.parametrize('scope,excluded', [('all', True), ('dlc', True), ('named', False), ('current', False)])
def test_repeatable_arena_excluded_only_from_automatic_completion(mod, monkeypatch, scope, excluded):
    name = 'Mission_Mandolin_CircleOfSlaughter'
    r = row(name, 'available')
    monkeypatch.setattr(mod, '_engine', lambda: NS(snapshot=lambda: dict(missions=[r], tracked=[r['token']])))
    monkeypatch.setattr(mod, 'CATALOG', {name: dict(name=name, title='Circle of Slaughter', category='dlc')})
    monkeypatch.setattr(mod, '__package__', 'arena_preview_test')
    monkeypatch.setitem(sys.modules, 'arena_preview_test', NS(mission_discovery=NS(SCOPES=())))
    result = mod.preview(dict(scope=scope, missions=[name]))['missions'][0]
    assert result['excluded'] is excluded
    assert bool(result['blocked_reason']) is excluded
    assert name not in mod.NONPERSISTENT


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


def test_interrupted_receipt_blocks_preflight_until_explicitly_closed(mod, monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, 'mods_base', NS(SETTINGS_DIR=tmp_path))
    folder = tmp_path / 'msbt_missions'; folder.mkdir()
    receipt = folder / ('a' * 32 + '.jsonl')
    receipt.write_text(json.dumps(dict(event='issued', state='uncertain')) + '\n')
    with pytest.raises(RuntimeError, match='interrupted or uncertain'):
        mod.require_clear_journals()
    with receipt.open('a') as stream:
        stream.write(json.dumps(dict(event='recovered', state='stopped')) + '\n')
    mod.require_clear_journals()


def test_mission_pump_does_not_interrupt_a_scene_waiting_for_dialogue(mod, monkeypatch):
    calls = []
    monkeypatch.setattr(mod, '__package__', 'scene_test')
    monkeypatch.setitem(sys.modules, 'scene_test.progress_dialogue', NS(
        DialogueSkipper=lambda:NS(poll=lambda *args:calls.append('interrupted'))))
    monkeypatch.setitem(sys.modules, 'unrealsdk', NS(find_all=lambda cls:[]))
    monkeypatch.setitem(sys.modules, 'mods_base', NS(ENGINE=NS(GameViewport=NS(World=NS(_path_name=lambda:'World')))))
    mod._job = dict(id='job', state='running', mode='complete', operation_scope='missions')
    def step(ident):
        mod._job['await_tick'] = True
        return dict(state='running', message='Waiting for native scene')
    monkeypatch.setattr(mod, 'step', step)
    assert mod.poll('job')['state'] == 'running'
    assert calls == []


@pytest.mark.parametrize('acknowledged', [False, True])
def test_close_unloaded_objective_run_never_reads_or_repeats_native_calls(mod, monkeypatch, tmp_path, acknowledged):
    monkeypatch.setitem(sys.modules, 'mods_base', NS(SETTINGS_DIR=tmp_path))
    monkeypatch.setattr(mod, '_engine', lambda: pytest.fail('Old process identities must not be dereferenced'))
    folder = tmp_path / 'msbt_missions'; folder.mkdir()
    ident = 'a' * 32; path = folder / (ident + '.jsonl')
    event = dict(event='issued', operation='objective_complete', mission='Mission_Main_Beach',
                 before=dict(token='old-process-token'), objective=dict(token='old-objective'))
    path.write_text(json.dumps(event) + '\n')
    if not acknowledged:
        with pytest.raises(ValueError, match='Acknowledge'):
            mod.recover(dict(job_id=ident, mode='close'))
        assert len(path.read_text().splitlines()) == 1
        return
    result = mod.recover(dict(job_id=ident, mode='close', acknowledge_shared_progress=True))
    assert result['closed'] and result['report']['observed'] == 'unverified_after_reload'
    saved = json.loads(path.read_text().splitlines()[-1])
    assert saved['state'] == 'stopped' and saved['closed']
    mod.require_clear_journals()


def test_full_run_quarantines_one_failed_mission_and_continues_next(mod, monkeypatch, tmp_path):
    names=['Mission_Main_Beach','Mission_Side_Heist']
    rows=[row(name,'completed') for name in names]
    monkeypatch.setattr(mod,'_engine',lambda:NS(snapshot=lambda:{'missions':rows}))
    pc=NS(_path_name=lambda:'host')
    monkeypatch.setattr(mod,'_party',lambda:[dict(pc=pc,host=True)])
    monkeypatch.setattr(mod,'_binding',lambda party:['same'])
    monkeypatch.setattr(mod,'_validate_exit',lambda *args:None)
    calls=[]
    def credit(engine,party,name):
        calls.append(name)
        if name==names[0]:raise RuntimeError('Native side effect unverified')
    monkeypatch.setattr(mod,'_credit_completed',credit)
    mod._job=dict(id='job',ok=True,state='running',binding=['same'],target='host',
                  names=names,index=0,total=2,completed=[],deferred=[],phase='complete',
                  completion_path='normal_acceptance',continue_on_mission_failure=True,
                  preserve_completed=True,
                  journal=str(tmp_path/'job.jsonl'))
    first=mod.step('job')
    assert first['state']=='running' and first['index']==1
    assert first['unverified_operations'][0]['mission']==names[0]
    second=mod.step('job')
    assert second['state']=='stopped'
    assert calls==names and mod._job['completed']==[names[1]],second


@pytest.mark.parametrize('pending', [False, True])
def test_uncertain_challenge_credit_keeps_its_mission_receipt(mod, monkeypatch, tmp_path, pending):
    names=['Mission_Main_Beach','Mission_Side_Heist']
    monkeypatch.setattr(mod,'_engine',lambda:NS(snapshot=lambda:{'missions':[row(n,'completed') for n in names]}))
    monkeypatch.setattr(mod,'_party',lambda:[dict(pc=NS(_path_name=lambda:'host'),host=True)])
    monkeypatch.setattr(mod,'_binding',lambda party:['same'])
    monkeypatch.setattr(mod,'_validate_exit',lambda *args:None)
    class CreditUncertain(Exception):
        issued=True
    calls=[]
    def credit(engine,party,name):
        calls.append(name)
        raise CreditUncertain('Original callback has no confirmed result')
    monkeypatch.setattr(mod,'_credit_completed',credit)
    receipt=dict(mission=names[0],operation='challenge_credit')
    mod._job=dict(id='job',ok=True,state='running',binding=['same'],target='host',
                  names=names,index=0,total=2,completed=[],deferred=[],phase='complete',
                  completion_path='normal_acceptance',continue_on_mission_failure=True,
                  challenge_pending=receipt if pending else None,
                  journal=str(tmp_path/'job.jsonl'))
    result=mod.step('job')
    assert result['state']=='uncertain' and result['index']==0
    assert result.get('challenge_pending')==receipt if pending else not result.get('challenge_pending')
    assert not result.get('unverified_operations')
    assert calls==[names[0]]
    assert mod.step('job')['state']=='uncertain' and calls==[names[0]]


def test_manual_failed_mission_still_stops_without_skip(mod, monkeypatch, tmp_path):
    name='Mission_Main_Beach'
    monkeypatch.setattr(mod,'_engine',lambda:NS(snapshot=lambda:{'missions':[row(name,'completed')]}))
    pc=NS(_path_name=lambda:'host')
    monkeypatch.setattr(mod,'_party',lambda:[dict(pc=pc,host=True)])
    monkeypatch.setattr(mod,'_binding',lambda party:['same'])
    monkeypatch.setattr(mod,'_validate_exit',lambda *args:None)
    monkeypatch.setattr(mod,'_credit_completed',lambda *args:(_ for _ in ()).throw(RuntimeError('Side effect failed')))
    mod._job=dict(id='job',ok=True,state='running',binding=['same'],target='host',
                  names=[name],index=0,total=1,completed=[],deferred=[],phase='complete',
                  completion_path='normal_acceptance',continue_on_mission_failure=False,
                  journal=str(tmp_path/'job.jsonl'))
    result=mod.step('job')
    assert result['state']=='stopped' and result['index']==0
    assert not result.get('unverified_operations')


def test_unreturned_call_can_close_after_restart_without_native_reads(mod, monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules,'mods_base',NS(SETTINGS_DIR=tmp_path))
    monkeypatch.setattr(mod,'_engine',lambda:pytest.fail('Closing must not read process-local state'))
    folder=tmp_path/'msbt_missions';folder.mkdir()
    ident='b'*32;path=folder/(ident+'.jsonl')
    path.write_text(json.dumps(dict(event='issued',mission='Mission_Main_Beach',
                                    operation='safehouse_claim',address='registry.World_P.top.test.actor.State'))+'\n')
    result=mod.recover(dict(job_id=ident,mode='close',acknowledge_shared_progress=True))
    assert result['closed'] and result['report']['observed']=='unverified_after_reload'
    assert mod.status()['state']=='idle'


def test_live_full_run_recovers_unknown_unreturned_call_by_quarantining(mod, monkeypatch, tmp_path):
    ident='c'*32;name='Mission_Main_Beach';path=tmp_path/(ident+'.jsonl')
    path.write_text(json.dumps(dict(event='issued',mission=name,operation='switch_toggle'))+'\n')
    pc=NS(_path_name=lambda:'host')
    monkeypatch.setattr(mod,'_party',lambda:[dict(pc=pc,host=True)])
    monkeypatch.setattr(mod,'_binding',lambda party:['same'])
    monkeypatch.setitem(sys.modules,'mods_base',NS(SETTINGS_DIR=tmp_path))
    mod._job=dict(id=ident,ok=False,state='uncertain',binding=['same'],target='host',
                  names=[name],index=0,total=1,completed=[],deferred=[],phase='complete',
                  completion_path='normal_acceptance',continue_on_mission_failure=True,
                  journal=str(path))
    before=path.read_bytes()
    assert mod.recover(dict(job_id=ident,mode='inspect'))['observed']=='unverified'
    assert path.read_bytes()==before
    result=mod.recover(dict(job_id=ident,mode='continue',acknowledge_shared_progress=True))
    assert result['state']=='stopped' and result['index']==1
    assert result['unverified_operations'][0]['operation']=='switch_toggle'
    assert sum(json.loads(line).get('event')=='issued' for line in path.read_text().splitlines())==1


def test_uncertain_full_run_can_close_without_reissuing_returned_call(mod, monkeypatch, tmp_path):
    ident='d'*32;name='Mission_Main_Beach';path=tmp_path/(ident+'.jsonl')
    path.write_text(''.join(json.dumps(e)+'\n' for e in [
        dict(event='issued',mission=name,operation='complete'),
        dict(event='returned',mission=name,operation='complete'),
        dict(event='state',state='uncertain')]))
    monkeypatch.setitem(sys.modules,'mods_base',NS(SETTINGS_DIR=tmp_path))
    monkeypatch.setattr(mod,'_engine',lambda:pytest.fail('Close must not reissue or read native calls'))
    mod._job=dict(id=ident,ok=False,state='uncertain',names=[name],index=0,
                  completion_path='normal_acceptance',continue_on_mission_failure=True,
                  journal=str(path))
    result=mod.recover(dict(job_id=ident,mode='close',acknowledge_shared_progress=True))
    assert result['closed'] and mod.status()['state']=='stopped'
    assert json.loads(path.read_text().splitlines()[-1])['report']['observed']=='unverified_without_retry'


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
@pytest.mark.parametrize('paced', [True, False])
def test_reset_accept_complete_is_one_call_per_step_and_never_retries_uncertain(mod, monkeypatch, tmp_path, native_matches, paced):
    clock=[10.0]
    monkeypatch.setattr(mod.time,'monotonic',lambda:clock[0])
    r = dict(row(state='completed'), record='0x100000', storage='0x200000')
    calls = []
    base = 0x140000000
    def read(address, size):
        return b'\1' if size == 1 else bytes.fromhex(r['token'])
    def u64(address):
        return {0x100000: 0x300000, 0x1000a8: 0x200000,
                0x3000f8: base + 0xd80660, 0x300110: base + 0x419fefa}[address]
    engine = NS(profile='steam-25372571', base=base, read=read, u64=u64,
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
    mod._job['settle_guest_progress']=paced
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
        result = mod.step('job')
        assert result['state'] == 'completed'
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


@pytest.mark.parametrize('party_size', [1, 2])
@pytest.mark.parametrize('phase', ['prepare', 'complete'])
def test_preserved_completed_mission_checks_credit_without_reset(mod, monkeypatch, tmp_path, party_size, phase):
    pc = NS(_path_name=lambda: 'pc')  # No native mutation methods on the fake.
    monkeypatch.setattr(mod, '_engine', lambda: NS(snapshot=lambda: {'missions': [row(state='completed')]}))
    monkeypatch.setattr(mod, '_party', lambda: [{'pc': pc}] * party_size)
    monkeypatch.setattr(mod, '_binding', lambda rows: ['fixed'])
    monkeypatch.setattr(mod, '_validate_exit', lambda *args: None)
    credits=[]
    monkeypatch.setattr(mod, '_credit_completed', lambda e,p,n: credits.append(n))
    mod._job = dict(id='job', ok=True, state='running', binding=['fixed'], target='pc',
                    names=['Mission_Main_Beach'], index=0, completed=[], phase=phase,
                    preserve_completed=True, journal=str(tmp_path/'job.jsonl'))
    result=mod.step('job')
    assert result['state'] == ('completed' if party_size==1 else 'stopped')
    assert credits == (['Mission_Main_Beach'] if party_size==1 else [])
    events=[json.loads(x)['event'] for x in (tmp_path/'job.jsonl').read_text().splitlines()]
    assert 'issued' not in events


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
    engine = NS(profile='steam-25372571', base=base, snapshot=lambda: {'missions': [copy.deepcopy(r)]}, read=lambda *args: b'\1',
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
        {'name': 'electi', 'parent': 'base', 'blocked_reason': None},
        {'name': 'heist', 'parent': 'base', 'blocked_reason': None},
        {'name': 'vending', 'parent': 'base', 'blocked_reason': 'parent unfinished'},
        {'name': 'travel_0', 'blocked_reason': None}])
    monkeypatch.setitem(sys.modules, 'repair_test', pkg)
    monkeypatch.setattr(mod, '__package__', 'repair_test')
    mod._job = {'checked_prerequisites': ['electi']}
    monkeypatch.setattr(mod, '_dlc_requirement', lambda name:None)
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
    module = importlib.util.module_from_spec(spec); exec_with_profiles(spec, module, monkeypatch)
    args = parser.parse_args(['run', '--player', 'Guest', '--reset-completed'])
    module.mission_command(args)
    assert [x[0] for x in calls] == ['mission_start', 'mission_step']
    assert calls[0][1]['target_player'] == 'Guest'
    assert calls[0][1]['reset_completed'] is True


@pytest.mark.parametrize('state,operation,returned_state,allowed', [
    ('available','accept','available',True),
    ('active','accept','available',True),
    ('completed','complete','active',True),
    ('active','complete','active',False),
    ('locked','accept','available',False),
])
def test_recovery_reads_receipt_without_repeating_native_calls(mod, monkeypatch, tmp_path, state, operation, returned_state, allowed):
    ident = 'a' * 32
    old = row(state=returned_state)
    current = row(state=state)
    journal = tmp_path / (ident + '.jsonl')
    events = [dict(event='issued', mission='Mission_Main_Beach', operation=operation, before=old, time=1),
              dict(event='returned', mission='Mission_Main_Beach', operation=operation, after=old, time=2),
              dict(event='state', state='uncertain')]
    journal.write_text(''.join(json.dumps(e)+'\n' for e in events))
    mod._job = dict(id=ident, state='uncertain', journal=str(journal), names=['Mission_Main_Beach'],
                    index=0, completed=[], binding=['fixed'], target='pc', phase='accept')
    monkeypatch.setitem(sys.modules, 'mods_base', NS(SETTINGS_DIR=tmp_path))
    monkeypatch.setattr(mod, '_engine', lambda:NS(snapshot=lambda:{'missions':[current]}))
    monkeypatch.setattr(mod, '_validate_exit', lambda *args:None)
    monkeypatch.setattr(mod, '_party', lambda:[])
    monkeypatch.setattr(mod, '_binding', lambda rows:['fixed'])
    before = journal.read_bytes()
    payload=dict(job_id=ident, mode='inspect')
    if not allowed:
        with pytest.raises(ValueError, match='unresolved'):mod.recover(payload)
        assert journal.read_bytes()==before
        return
    assert mod.recover(payload)['observed']==state
    assert journal.read_bytes()==before
    result=mod.recover(dict(payload, mode='continue', acknowledge_shared_progress=True))
    if state=='available':
        assert result['state']=='stopped' and result['verified_count']==0 and len(result['deferred'])==1
    else:assert result['state']=='running'
    assert sum(json.loads(line)['event']=='issued' for line in journal.read_text().splitlines())==1


def test_blocked_dlc_skips_before_reset_and_names_player(mod, monkeypatch, tmp_path):
    name='mission_main_cowbell0'
    monkeypatch.setattr(mod, '_dlc_requirement', lambda n:dict(allowed=False,title='Vault',reason='Game reports no access: Guest',blocking_players=['Guest']))
    monkeypatch.setattr(mod, '_engine', lambda:NS(snapshot=lambda:{'missions':[]}))
    monkeypatch.setattr(mod, '_party', lambda:[{'pc':NS(_path_name=lambda:'pc')}])
    monkeypatch.setattr(mod, '_binding', lambda rows:['fixed'])
    mod._job=dict(id='job',state='running',names=[name],index=0,completed=[],binding=['fixed'],target='pc',phase='prepare',journal=str(tmp_path/'job.jsonl'))
    result=mod.step('job')
    assert result['state']=='stopped' and result['verified_count']==0
    assert result['deferred'][0]['blocking_players']==['Guest']
    assert 'issued' not in [json.loads(line)['event'] for line in (tmp_path/'job.jsonl').read_text().splitlines()]


def test_credit_repair_never_resets_completed_mission(mod, monkeypatch, tmp_path):
    name = 'Mission_Side_Heist'
    pc = NS(_path_name=lambda: 'pc')
    monkeypatch.setattr(mod, '_engine', lambda: NS(snapshot=lambda: {'missions': [row(name, 'completed')]}))
    monkeypatch.setattr(mod, '_party', lambda: [{'pc': pc}])
    monkeypatch.setattr(mod, '_binding', lambda rows: ['fixed'])
    monkeypatch.setattr(mod, '_validate_exit', lambda *args: None)
    calls = []
    monkeypatch.setattr(mod, '_credit_completed', lambda engine, party, mission: calls.append(mission))
    mod._job = dict(id='job', ok=True, state='running', binding=['fixed'], target='pc',
                    names=[name], index=0, completed=[], phase='prepare', selection_scope='challenge_credit',
                    journal=str(tmp_path/'job.jsonl'))
    assert mod.step('job')['state'] == 'completed'
    assert calls == [name]
    events = [json.loads(x)['event'] for x in (tmp_path/'job.jsonl').read_text().splitlines()]
    assert 'issued' not in events


def test_credit_pending_does_not_advance_or_reset(mod, monkeypatch, tmp_path):
    class CreditPending(Exception):
        receipt = {'mission': 'Mission_Side_Heist'}
    name = 'Mission_Side_Heist'
    pc = NS(_path_name=lambda: 'pc')
    monkeypatch.setattr(mod, '_engine', lambda: NS(snapshot=lambda: {'missions': [row(name, 'completed')]}))
    monkeypatch.setattr(mod, '_party', lambda: [{'pc': pc}])
    monkeypatch.setattr(mod, '_binding', lambda rows: ['fixed'])
    monkeypatch.setattr(mod, '_validate_exit', lambda *args: None)
    def pending(*args): raise CreditPending('settling')
    monkeypatch.setattr(mod, '_credit_completed', pending)
    mod._job = dict(id='job', ok=True, state='running', binding=['fixed'], target='pc',
                    names=[name], index=0, completed=[], phase='prepare', selection_scope='challenge_credit',
                    journal=str(tmp_path/'job.jsonl'))
    result = mod.step('job')
    assert result['index'] == 0 and result['phase'] == 'complete'
    assert result['state'] == 'running' and result['challenge_pending']
    with pytest.raises(ValueError): mod.cancel('wrong')
    assert mod.cancel('job')['cancel_requested']
    assert mod._job['state'] == 'running'


@pytest.mark.parametrize('end_state', ['running', 'uncertain', 'completed'])
def test_shared_poll_stops_on_terminal_result_and_has_count_bound(mod, monkeypatch, end_state):
    calls=[]
    mod._job=dict(id='job',state='running',operation_scope='map_locations')
    monkeypatch.setattr(mod.time,'monotonic',lambda:0)
    monkeypatch.setattr(mod,'step',lambda ident:calls.append(ident) or dict(state=end_state))
    assert mod.poll('job')['state']==end_state
    assert len(calls)==(16 if end_state=='running' else 1)


def test_shared_poll_yields_on_time_budget(mod,monkeypatch):
    mod._job=dict(id='job',state='running',operation_scope='travel_stations')
    times=iter([0,.021]);calls=[]
    monkeypatch.setattr(mod.time,'monotonic',lambda:next(times))
    monkeypatch.setattr(mod,'step',lambda ident:calls.append(ident) or dict(state='running'))
    mod.poll('job');assert calls==['job']


@pytest.mark.parametrize('scope',['map_locations','travel_stations','travel_requirements'])
@pytest.mark.parametrize('already_complete',[True,False])
def test_discovery_uses_only_required_snapshot_and_skips_completed_writes(mod,monkeypatch,tmp_path,scope,already_complete):
    calls=[]
    engine=NS(validate_context=lambda:calls.append('guard'),snapshot=lambda:calls.append('snapshot') or {})
    monkeypatch.setattr(mod,'_engine',lambda:engine)
    monkeypatch.setattr(mod,'_party',lambda:[dict(pc=NS(_path_name=lambda:'pc'))])
    monkeypatch.setattr(mod,'_binding',lambda rows:['fixed'])
    def operation(*args):
        calls.append('read')
        return 2 if already_complete else 0,lambda:calls.append('write') or 2,lambda value:value==2
    monkeypatch.setitem(sys.modules,'discovery_progress_test',NS(mission_discovery=NS(operation=operation)))
    mod.__package__='discovery_progress_test'
    mod._job=dict(id='job',ok=True,state='running',binding=['fixed'],target='pc',names=['location'],
        index=0,total=1,phase='prepare',completed=[],operation_scope=scope,journal=str(tmp_path/'job.jsonl'))
    assert mod.step('job')['state']=='completed'
    assert calls==(['snapshot'] if scope=='travel_requirements' else ['guard'])+['read']+([] if already_complete else ['write'])
    events=[json.loads(line)['event'] for line in (tmp_path/'job.jsonl').read_text().splitlines()]
    assert events==(['already_complete'] if already_complete else ['issued','returned'])+['state']


def test_discovery_context_failure_prevents_read_or_mutation(mod,monkeypatch,tmp_path):
    def fail():raise RuntimeError('World changed')
    monkeypatch.setattr(mod,'_engine',lambda:NS(validate_context=fail))
    mod._job=dict(id='job',state='running',operation_scope='map_locations',index=0,journal=str(tmp_path/'job.jsonl'))
    result=mod.step('job')
    assert result['state']=='stopped' and result['message']=='World changed'

@pytest.mark.parametrize('observed', ['active', 'available', 'accepted'])
def test_completion_readiness_mismatch_never_reissues(mod, monkeypatch, tmp_path, observed):
    monkeypatch.setattr(mod, '_engine', lambda: NS(snapshot=lambda: {'missions': [row(state=observed)]}))
    monkeypatch.setattr(mod, '_party', lambda: [dict(pc=NS(_path_name=lambda:'pc'))])
    monkeypatch.setattr(mod, '_binding', lambda rows:['fixed'])
    mod._job=dict(id='job',state='running',binding=['fixed'],target='pc',names=['Mission_Main_Beach'],
        index=0,phase='complete',completed=[],journal=str(tmp_path/'job.jsonl'),
        transition_readiness=dict(mission='Mission_Main_Beach',operation='complete',expected=['completed']))
    result=mod.step('job')
    assert result['state']=='stopped'
    assert mod._job['completed']==[]
    assert mod._job['transition_readiness']['operation']=='complete'

def test_current_ignores_concurrently_tracked_bounty(mod):
    mission = row()
    bounty = dict(row(token='02'*12), source_identity=None, generated=1, ownership=0)
    snapshot = dict(missions=[mission,bounty],tracked=[mission['token'],bounty['token']])
    assert mod.select(snapshot,'current') == ['Mission_Main_Beach']
    assert mod.select(snapshot,'bounty') == ['bounty:'+bounty['token']]
    assert mod._row(snapshot,'bounty:'+bounty['token']) is bounty
    with pytest.raises(ValueError,match='changed'):
        mod.select(snapshot,'bounty',['bounty:'+'03'*12])

@pytest.mark.parametrize('field,value',[('ownership',1),('replication_type',1),('generated',0)])
def test_bounty_rejects_non_shared_instance(mod,field,value):
    bounty=dict(row(),source_identity=None,generated=1,ownership=0)
    bounty[field]=value
    with pytest.raises(ValueError):
        mod._row(dict(missions=[bounty]),'bounty:'+bounty['token'])


@pytest.mark.parametrize('mode', ['reopen', 'reset_completed'])
def test_reopen_resets_once_and_never_completes(mod, monkeypatch, tmp_path, mode):
    r = row('Mission_Main_Grasslands1', 'completed')
    calls=[]
    def reset(engine, current, journal):
        calls.append('reset')
        r['status_fact']['known_status']='locked'
    monkeypatch.setitem(sys.modules,'reopen_test',NS(mission_reset=NS(reopen=reset)))
    monkeypatch.setattr(mod,'__package__','reopen_test')
    engine=NS(snapshot=lambda:dict(missions=[r]))
    mod._job=dict(id='job',mode=mode,state='running',phase='prepare',index=0,
                  total=1,completed=[],journal=str(tmp_path/'job.jsonl'))
    result=mod._reopen_step(engine,r,'Mission_Main_Grasslands1',None)
    assert calls==['reset']
    if mode=='reset_completed':
        assert result['state']=='completed'
        assert mod._state(r)=='locked'
    else:
        mod._reopen_step(engine,r,'Mission_Main_Grasslands1',None)
        assert calls==['reset']
        r['status_fact']['known_status']='active'
        assert mod._reopen_step(engine,r,'Mission_Main_Grasslands1',None)['state']=='completed'
        assert mod._state(r)=='active'


def test_reopen_failure_preserves_pending_phase(mod, monkeypatch, tmp_path):
    def fail(*args):raise RuntimeError('native call uncertain')
    monkeypatch.setitem(sys.modules,'reopen_test',NS(mission_reset=NS(reopen=fail)))
    monkeypatch.setattr(mod,'__package__','reopen_test')
    mod._job=dict(id='job',mode='reopen',state='running',phase='prepare',index=0,
                  journal=str(tmp_path/'job.jsonl'))
    with pytest.raises(RuntimeError,match='uncertain'):
        mod._reopen_step(None,row(state='completed'),'Mission_Main_Beach',None)
    assert mod._job['state']=='uncertain'
    assert mod._job['phase']=='reopen_wait'
    assert mod.step('job')['state']=='uncertain'


@pytest.mark.parametrize('initial_state', ['active', 'accepted', 'completed'])
def test_standalone_replay_unloads_resets_once_and_returns_before_success(mod, monkeypatch, tmp_path, initial_state):
    name='Mission_Main_Beach';r=row(name,initial_state);calls=[]
    gates={'unloaded':False,'returned':False}
    def reset(*args):
        calls.append('reset');r['status_fact']['known_status']='accepted'
    def unload(*args):
        calls.append('unload');return gates['unloaded']
    def arrive(*args):
        calls.append('return');return gates['returned']
    context=NS(observe=lambda owner:True,prepare_reset=unload,travel_to=arrive)
    monkeypatch.setattr(mod,'__package__','reopen_world_test')
    monkeypatch.setitem(sys.modules,mod.__name__,mod)
    monkeypatch.setitem(sys.modules,'reopen_world_test',NS(mission_reset=NS(reopen=reset),
        mission_execution=NS(DATA={name:dict(title='Mission',execution_map='world_p')}),
        mission_completion_context=context))
    monkeypatch.setitem(sys.modules,'reopen_world_test.mission_completion_context',context)
    pc=NS(_path_name=lambda:'host');party=[dict(pc=pc)]
    monkeypatch.setattr(mod,'_engine',lambda:NS(snapshot=lambda:dict(missions=[r])))
    monkeypatch.setattr(mod,'_party',lambda:party)
    monkeypatch.setattr(mod,'_binding',lambda rows:['same'])
    monkeypatch.setattr(mod,'_validate_exit',lambda *args:None)
    mod._job=dict(id='job',mode='reopen',completion_path='mission_replay',completion_context={},
        state='running',phase='prepare',index=0,total=1,names=[name],completed=[],
        binding=['same'],target='host',journal=str(tmp_path/'job.jsonl'))
    assert mod.step('job')['state']=='running' and calls==['unload']
    gates['unloaded']=True
    assert mod.step('job')['state']=='running' and calls==['unload','unload','reset']
    # Acceptance alone is not replay readiness, even after the return request.
    for _ in range(2):assert mod.step('job')['state']=='running'
    gates['returned']=True
    assert mod.step('job')['state']=='running'
    assert 'opening objectives' in mod._job['message']
    r['status_fact']['known_status']='active'
    assert mod.step('job')['state']=='completed'
    assert calls.count('reset')==1
    assert not any(e.get('operation')=='complete' for e in map(json.loads,Path(mod._job['journal']).read_text().splitlines()))


def test_replay_opening_timeout_does_not_reset_again(mod, monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules,'reopen_wait_test',NS(mission_reset=NS(reopen=lambda *a:pytest.fail('No repeated reset'))))
    monkeypatch.setattr(mod,'__package__','reopen_wait_test')
    mod._job=dict(id='job',mode='reopen',completion_path='mission_replay',state='running',
        phase='reopen_wait',index=0,reopen_activation_since=10.,journal=str(tmp_path/'job.jsonl'))
    monkeypatch.setattr(mod.time,'monotonic',lambda:131.)
    with pytest.raises(RuntimeError,match='opening did not activate'):
        mod._reopen_step(None,row(state='accepted'),'Mission_Main_Beach',None)


@pytest.mark.parametrize('owned_by_practice',[False,True])
def test_replay_start_attaches_world_guard_unless_internal_practice_owns_it(mod,monkeypatch,tmp_path,owned_by_practice):
    name='Mission_Main_Beach';r=row(name);pc=NS(_path_name=lambda:'host');party=[dict(pc=pc)]
    context=NS(begin=lambda *args:dict(marker='world guard'))
    monkeypatch.setattr(mod,'__package__','reopen_start_test')
    execution=NS(DATA={name:dict(execution_map='world_p',execution_maps=['world_p'])})
    monkeypatch.setitem(sys.modules,'reopen_start_test',NS(mission_discovery=NS(SCOPES=()),
        farming_targets=NS(resolve=lambda payload:party)))
    monkeypatch.setitem(sys.modules,'reopen_start_test.mission_execution',execution)
    monkeypatch.setitem(sys.modules,'reopen_start_test.mission_completion_context',context)
    monkeypatch.setitem(sys.modules,'mods_base',NS(SETTINGS_DIR=tmp_path))
    monkeypatch.setattr(mod,'_engine',lambda:NS(snapshot=lambda:dict(missions=[r])))
    monkeypatch.setattr(mod,'_party',lambda:party)
    monkeypatch.setattr(mod,'_binding',lambda rows:['same'])
    monkeypatch.setattr(mod,'require_clear_journals',lambda:None)
    payload=dict(scope='named',missions=[name],mode='reopen',acknowledge_shared_progress=True,
                 manage_replay_travel=False)  # A bridge field cannot bypass travel.
    result=mod.start(payload,**(dict(manage_replay_travel=False) if owned_by_practice else {}))
    assert result['completion_path']==('normal_acceptance' if owned_by_practice else 'mission_replay')
    assert ('completion_context' in result) is not owned_by_practice


def test_authored_credit_job_uses_completed_records_without_replaying_mission(mod,monkeypatch,tmp_path):
    name='Mission_Harmonica_Main01';challenge='Achievement_Test'
    # The authored list is supplied by the reviewed challenge catalog; the
    # job may send only guarded Mission credit after a completed shared read.
    r=row(name,'completed');pc=NS(_path_name=lambda:'host');party=[dict(pc=pc)]
    engine=NS(snapshot=lambda:dict(missions=[r]))
    monkeypatch.setattr(mod,'__package__','authored_credit_test')
    monkeypatch.setitem(sys.modules,'authored_credit_test',NS(
        mission_discovery=NS(SCOPES=()),
        farming_targets=NS(resolve=lambda payload:party)))
    monkeypatch.setitem(sys.modules,'authored_credit_test.mission_challenges',NS(
        CREDIT_MISSIONS=(),credit_definition=lambda key:dict(missions=[name]) if key==challenge else None))
    monkeypatch.setitem(sys.modules,'mods_base',NS(SETTINGS_DIR=tmp_path))
    monkeypatch.setattr(mod,'CATALOG',{name:dict(name=name,title='Mission',category='dlc',exit_names=['None'])})
    monkeypatch.setattr(mod,'_engine',lambda:engine)
    monkeypatch.setattr(mod,'_party',lambda:party)
    monkeypatch.setattr(mod,'_binding',lambda rows:['same'])
    monkeypatch.setattr(mod,'_validate_exit',lambda *args:None)
    monkeypatch.setattr(mod,'require_clear_journals',lambda:None)
    credited=[]
    monkeypatch.setattr(mod,'_credit_completed',lambda e,p,n:credited.append((n,mod._job['credit_challenge'])) or True)
    payload=dict(scope='challenge_credit',challenge_id=challenge,mode='complete',
                 acknowledge_shared_progress=True)
    started=mod.start(payload)
    assert started['completion_path']=='normal_acceptance' and started['total']==1
    assert mod.step(started['id'])['state']=='completed'
    assert credited==[(name,challenge)]
    events=[json.loads(line) for line in Path(mod._job['journal']).read_text().splitlines()]
    assert not any(e.get('operation') in ('reset','accept','complete') for e in events)


def test_authored_credit_job_rejects_incomplete_shared_record_before_journal(mod,monkeypatch,tmp_path):
    name='Mission_Harmonica_Main01';challenge='Achievement_Test'
    monkeypatch.setattr(mod,'__package__','authored_credit_guard_test')
    monkeypatch.setitem(sys.modules,'authored_credit_guard_test',NS(
        mission_discovery=NS(SCOPES=())))
    monkeypatch.setitem(sys.modules,'authored_credit_guard_test.mission_challenges',NS(
        CREDIT_MISSIONS=(),credit_definition=lambda key:dict(missions=[name])))
    monkeypatch.setattr(mod,'_engine',lambda:NS(snapshot=lambda:dict(missions=[row(name,'active')])))
    with pytest.raises(ValueError,match='completed shared mission records'):
        mod.start(dict(scope='challenge_credit',challenge_id=challenge,
                       acknowledge_shared_progress=True))
    assert mod._job is None and not list(tmp_path.iterdir())


def test_authored_credit_selection_is_bounded_and_preserves_definition_order(mod,monkeypatch):
    monkeypatch.setattr(mod,'__package__','authored_credit_subset_test')
    monkeypatch.setitem(sys.modules,'authored_credit_subset_test.mission_challenges',NS(
        CREDIT_MISSIONS=(),credit_definition=lambda key:dict(missions=['A','B','C'])))
    assert mod.select({},'challenge_credit',['C','A'],'Reviewed')==['A','C']
    for names in (['C','C'],['outside'],[{}],[]):
        with pytest.raises(ValueError,match='authored challenge'):
            mod.select({},'challenge_credit',names,'Reviewed')


def test_unresolved_replay_map_rejected_before_reset_or_journal(mod,monkeypatch):
    name='Mission_Main_Beach'
    monkeypatch.setattr(mod,'__package__','reopen_missing_map_test')
    monkeypatch.setitem(sys.modules,'reopen_missing_map_test',NS(mission_discovery=NS(SCOPES=())))
    monkeypatch.setitem(sys.modules,'reopen_missing_map_test.mission_execution',NS(DATA={name:{}}))
    monkeypatch.setattr(mod,'_engine',lambda:NS(snapshot=lambda:dict(missions=[row(name)])))
    with pytest.raises(ValueError,match='map is unresolved'):
        mod.start(dict(scope='named',missions=[name],mode='reopen',acknowledge_shared_progress=True))
    assert mod._job is None


@pytest.mark.parametrize('later_state, expected', [('None','completed'), ('active','stopped')])
def test_campaign_reset_waits_for_group_progression_without_repeating(mod, monkeypatch, tmp_path, later_state, expected):
    rows=[row('Mission_Main_Beach','accepted'),row('Mission_Main_Grasslands1','active')]
    calls=[]
    def reset(engine, selected, journal):
        calls.append([r['source_identity']['name'] for r in selected])
        rows[1]['status_fact']['known_status']=later_state
    monkeypatch.setitem(sys.modules,'campaign_test',NS(mission_reset=NS(reset_campaign=reset)))
    monkeypatch.setattr(mod,'__package__','campaign_test')
    monkeypatch.setattr(mod,'_engine',lambda:NS(snapshot=lambda:dict(missions=rows)))
    monkeypatch.setattr(mod,'_party',lambda:[dict(pc=NS(_path_name=lambda:'pc'))])
    monkeypatch.setattr(mod,'_binding',lambda rows:['fixed'])
    mod._job=dict(id='job',state='running',mode='reset_completed',binding=['fixed'],target='pc',
        names=['Mission_Main_Beach','Mission_Main_Grasslands1'],phase='prepare',completed=[],index=0,
        journal=str(tmp_path/'job.jsonl'))
    assert mod.step('job')['phase']=='campaign_verify'
    assert mod.step('job')['state']==expected
    mod.step('job')
    assert len(calls)==1


def test_campaign_reset_failure_is_not_reissued(mod, monkeypatch, tmp_path):
    calls=[]
    def reset(*args):
        calls.append(1)
        raise RuntimeError('native result unknown')
    monkeypatch.setitem(sys.modules,'campaign_test',NS(mission_reset=NS(reset_campaign=reset)))
    monkeypatch.setattr(mod,'__package__','campaign_test')
    monkeypatch.setattr(mod,'_engine',lambda:NS(snapshot=lambda:dict(missions=[row()])))
    monkeypatch.setattr(mod,'_party',lambda:[dict(pc=NS(_path_name=lambda:'pc'))])
    monkeypatch.setattr(mod,'_binding',lambda rows:['fixed'])
    mod._job=dict(id='job',state='running',mode='reset_completed',binding=['fixed'],target='pc',
        names=['Mission_Main_Beach'],phase='prepare',completed=[],index=0,journal=str(tmp_path/'job.jsonl'))
    assert mod.step('job')['state']=='uncertain'
    mod.step('job')
    assert calls==[1]


def test_campaign_inventory_includes_internal_and_prologue_records(mod):
    records = [row('Mission_Main_PrisonPrologue', 'completed'),
               row('Mission_Main_Harmonica3_HandyCounter', 'completed'),
               row('ZoneActivity_Grasslands_SafehouseMain', 'active'),
               row('Mission_Main_Beach', 'None')]
    generated = row('generated'); generated['generated'] = 1
    unnamed = row(); unnamed['source_identity'] = None
    names = mod._campaign_names(dict(missions=records + [generated, unnamed]))
    assert names == [r['source_identity']['name'] for r in records]
    with pytest.raises(ValueError, match='Ambiguous'):
        mod._campaign_names(dict(missions=records + [records[0]]))


@pytest.mark.parametrize('mode', ['inspect', 'continue', 'close'])
def test_campaign_recovery_keeps_partial_results_without_repeating_reset(mod, monkeypatch, tmp_path, mode):
    ident = 'a' * 32
    name = 'ZoneActivity_Grasslands_Silo1'  # Not in completion's catalog.
    record = row(name, 'completed')
    path = tmp_path / (ident + '.jsonl')
    events = [dict(event='campaign_reset_issued', missions=[name], tokens={name: record['token']}),
              dict(event='campaign_reset_returned')]
    path.write_text(''.join(json.dumps(e) + '\n' for e in events))
    monkeypatch.setitem(sys.modules, 'mods_base', NS(SETTINGS_DIR=tmp_path))
    monkeypatch.setattr(mod, '_engine', lambda: NS(snapshot=lambda: dict(missions=[record])))
    mod._job = dict(id=ident, state='stopped', mode='reset_completed', phase='campaign_verify',
                    journal=str(path), completed=[], index=0)
    result = mod.recover(dict(job_id=ident, mode=mode, acknowledge_shared_progress=True))
    assert result['ok']
    if mode == 'continue':
        assert result['state'] == 'running' and result['phase'] == 'campaign_verify'
    else:
        assert result['remaining_completed'][0]['name'] == name
        if mode == 'close':
            assert result['state'] == 'stopped'
            assert json.loads(path.read_text().splitlines()[-1])['event'] == 'recovered'
    assert 'issued' not in [json.loads(line)['event'] for line in path.read_text().splitlines()]


@pytest.mark.parametrize('has_return,token', [(False, '01' * 12), (True, '02' * 12)])
def test_campaign_recovery_rejects_unknown_outcome_or_changed_identity(mod, monkeypatch, tmp_path, has_return, token):
    ident = 'a' * 32
    name = 'Mission_Main_Beach'
    path = tmp_path / (ident + '.jsonl')
    events = [dict(event='campaign_reset_issued', missions=[name], tokens={name: '01' * 12})]
    if has_return:
        events.append(dict(event='campaign_reset_returned'))
    path.write_text(''.join(json.dumps(e) + '\n' for e in events))
    monkeypatch.setitem(sys.modules, 'mods_base', NS(SETTINGS_DIR=tmp_path))
    monkeypatch.setattr(mod, '_engine', lambda: NS(snapshot=lambda: dict(missions=[row(name, 'None', token)])))
    mod._job = dict(id=ident, state='uncertain', journal=str(path))
    with pytest.raises(ValueError, match='return receipt|identity differs'):
        mod.recover(dict(job_id=ident, mode='close', acknowledge_shared_progress=True))
    assert len(path.read_text().splitlines()) == len(events)


@pytest.mark.parametrize('size',[2,4])
def test_shared_full_mission_uses_objective_graph_and_preserves_guest_binding(mod,monkeypatch,tmp_path,size):
    import types
    monkeypatch.setitem(sys.modules,mod.__name__,mod)
    name='Mission_Main_Beach';r=row();calls=[];credits=[]
    party=[dict(pc=NS(_path_name=lambda i=i:'PC'+str(i)),host=i==0) for i in range(size)]
    monkeypatch.setattr(mod,'_party',lambda:party)
    monkeypatch.setattr(mod,'_binding',lambda rows:[x['pc']._path_name() for x in rows])
    engine=NS(snapshot=lambda:dict(missions=[r]))
    monkeypatch.setattr(mod,'_engine',lambda:engine);monkeypatch.setattr(mod,'_validate_exit',lambda *args:None)
    monkeypatch.setattr(mod,'_credit_completed',lambda e,rows,n:credits.append((len(rows),n)))
    pkg=types.ModuleType('coop_graph_test');pkg.__path__=[str(ROOT)]
    monkeypatch.setitem(sys.modules,pkg.__name__,pkg);monkeypatch.setattr(mod,'__package__',pkg.__name__)
    def advance(*args,**kwargs):
        calls.append(kwargs);r['status_fact']['known_status']='completed'
        return dict(message='Native graph settled')
    definition=dict(title='Test',execution_map='world_p')
    context=NS(observe=lambda owner:True,prepare=lambda *a:True,expect_finish=lambda *a:None,
               world=lambda:None,map_name=lambda w:'world_p',objective_ready=lambda *a:True)
    monkeypatch.setitem(sys.modules,pkg.__name__+'.mission_completion_context',context)
    monkeypatch.setitem(sys.modules,pkg.__name__+'.mission_execution',NS(DATA={name:definition},require_coverage=lambda *a:None,advance=advance))
    mod._job=dict(id='job',ok=True,state='running',binding=['PC'+str(i) for i in range(size)],target='PC1',
        names=[name],index=0,completed=[],phase='prepare',journal=str(tmp_path/'job.jsonl'),
        completion_path='objective_graph',completion_context={},placement_policy='map_only')
    assert mod.step('job')['state']=='running' and len(calls)==1, mod._job.get('message')
    assert mod.step('job')['state']=='completed'
    assert credits==[(size,name)] and len(calls)==1 and mod._job['target']=='PC1'
