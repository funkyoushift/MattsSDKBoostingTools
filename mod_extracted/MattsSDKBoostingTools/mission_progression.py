"""Explicit shared-lobby mission jobs. Called on the bridge/Quick Menu game thread.

Completion is not isolated to the selected player. A pinned player supplies normal
acceptance context; every participant and the host campaign can be affected.
Objective rollback and full progress erasure are deliberately not approximated.
"""
from __future__ import annotations

import ctypes as C
import json
import os
import struct
import time
import uuid
from importlib.resources import files
from pathlib import Path

CATALOG = {r['name']: r for r in json.loads(files(__package__).joinpath('mission_catalog.json').read_text())}
UNVERIFIED = {
    'objective': 'Generic objective completion is not verified; mission-specific triggers are not interchangeable.',
    'undo_objective': 'Undo must restore objective dependencies and side effects; a status reversal is not a verified undo.',
    'reset_all': 'Removing mission completion alone does not return objectives, unlocks and world state to not started.',
}
CATEGORY_SCOPES = ('story', 'sides', 'dlc', 'all')
MAX_BATCH = len(CATALOG)  # Bound jobs to the reviewed mission catalog.
NONPERSISTENT = {'Mission_DLC_Tuba_Base', 'Mission_DLC_Tuba_Hardcore', 'Mission_DLC_Tuba_TimerBase'}
_runtime = None
_job = None


def _engine():
    global _runtime
    if _runtime is None:
        from .mission_runtime import MissionRuntime
        _runtime = MissionRuntime()
    return _runtime


def _party():
    from . import farming_targets
    rows = farming_targets.party()
    for row in rows:
        pc = row['pc']
        if pc is None or pc.Pawn is None or not pc.HasAuthority():
            raise RuntimeError('Every participant must be loaded in the host game')
    return rows


def _binding(rows):
    return sorted((r['pc']._path_name(), r['state']._path_name(), int(r['state'].PlayerId)) for r in rows)


def _row(snapshot, name):
    rows = [r for r in snapshot['missions'] if (r['source_identity'] or {}).get('name') == name]
    if len(rows) != 1 or rows[0]['generated'] or rows[0]['replication_type'] != 0:
        raise ValueError('Mission is missing, ambiguous, generated or not an ordinary shared mission: ' + name)
    return rows[0]


def _state(row):
    return (row['status_fact'] or {}).get('known_status')


def select(snapshot, scope, names=None):
    if scope == 'challenge_credit':
        from .mission_challenges import MISSIONS
        return [n for n in MISSIONS if any((r.get('source_identity') or {}).get('name')==n
                and _state(r)=='completed' and not r.get('generated') and r.get('replication_type')==0
                for r in snapshot['missions'])]
    if scope in UNVERIFIED:
        raise ValueError(UNVERIFIED[scope])
    if scope == 'current':
        tracked = set(snapshot['tracked']) - {'0' * 24}
        candidates = [r for r in snapshot['missions'] if r['token'] in tracked]
        if len(candidates) != 1:
            raise ValueError('Track exactly one shared mission before using current mission')
        names = [(candidates[0]['source_identity'] or {}).get('name')]
    elif scope in ('story', 'sides', 'dlc', 'all'):
        names = [n for n, r in CATALOG.items() if scope == 'all' or r['category'] == scope]
    elif scope != 'named' or not isinstance(names, list) or not names:
        raise ValueError('Choose current, named, story, sides, dlc or all')
    if len(set(names)) != len(names) or any(n not in CATALOG for n in names):
        raise ValueError('Mission list contains duplicate or unreviewed definitions')
    return list(names)


def preview(payload):
    snapshot = _engine().snapshot()
    from . import mission_discovery as discovery
    scope = payload.get('scope', 'current')
    if scope in discovery.SCOPES:
        entries = discovery.plan(scope, snapshot)
        return dict(ok=True, scope=scope, missions=entries, max_batch=len(entries), unit='locations or requirements', message='Discovery and travel requirements affect shared party progress.')
    names = select(snapshot, scope, payload.get('missions'))
    entries = []
    for name in names:
        try:
            state = _state(_row(snapshot, name))
            reason = None if state in ('active', 'accepted', 'available', 'completed') else 'Mission prerequisites are not available'
        except ValueError as exc:
            state, reason = 'unavailable', str(exc)
        if name in NONPERSISTENT:
            reason = 'This replayable mission is source-marked never saved; permanent completion is not supported'
        entries.append(dict(CATALOG[name], state=state, blocked_reason=reason,
                            resets_host_completion=state == 'completed' and scope != 'challenge_credit', excluded=name in NONPERSISTENT))
    return dict(ok=True, scope='shared_lobby', selection_scope=scope, missions=entries, max_batch=MAX_BATCH,
                catalog_total=len(entries), excluded_total=sum(r['excluded'] for r in entries),
                unsupported=UNVERIFIED, message='Changes can affect host and all connected players. Preview is read-only.')


def status():
    if _job is None:
        from mods_base import SETTINGS_DIR
        folder = Path(SETTINGS_DIR) / 'msbt_missions'
        for path in sorted(folder.glob('*.jsonl')):
            events = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
            if events and events[-1].get('state') not in ('completed', 'cancelled', 'stopped'):
                return dict(ok=False, state='interrupted', id=path.stem,
                            message='An interrupted job needs recovery before another run. Use Recover stopped job.')
        return dict(ok=True, state='idle', unsupported=UNVERIFIED, max_batch=MAX_BATCH)
    result = {k: v for k, v in _job.items() if k not in ('binding', 'target', 'journal', 'names')}
    result['verified_count'] = len(_job.get('completed', []))
    return result


def dlc_status():
    from . import mission_dlc
    return dict(ok=True, packs=list(mission_dlc.inspect(_party()).values()))


def _dlc_requirement(name):
    from . import mission_dlc
    if name not in mission_dlc.DATA['missions']:
        return None
    return mission_dlc.requirement(name, mission_dlc.inspect(_party()))


def _defer(name, reason, access=None):
    entry = dict(name=name, title=CATALOG[name]['title'], reason=reason, state='deferred')
    if access:
        entry.update(pack=access['title'], blocking_players=access['blocking_players'])
    _journal(dict(event='deferred', mission=name, details=entry))
    _job.setdefault('deferred', []).append(entry)
    _job['index'] += 1
    _job['phase'] = 'prepare'
    _job['message'] = entry['title'] + ': deferred; ' + reason
    if _job['index'] >= len(_job['names']):
        _job.update(state='stopped', message='Finished available work; deferred missions remain.')
    _journal(dict(event='state', state=_job['state'], index=_job['index']))
    return status()


def _journal(event):
    with Path(_job['journal']).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(dict(event, time=time.time())) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def start(payload):
    global _job
    if _job and (_job['state'] in ('running', 'uncertain') or _job.get('challenge_pending')):
        raise ValueError('A mission job is running or has an uncertain result; inspect it before starting another')
    if payload.get('acknowledge_shared_progress') is not True:
        raise ValueError('Review and acknowledge that this changes shared host/party progress')
    engine = _engine()
    snapshot = engine.snapshot()
    from . import mission_discovery as discovery
    scope = payload.get('scope', 'current')
    discovery_job = scope in discovery.SCOPES
    entries = discovery.plan(scope, snapshot, payload.get('missions')) if discovery_job else []
    if any(r['blocked_reason'] for r in entries):
        raise ValueError('Travel requirement parent mission is unfinished')
    names = [r['name'] for r in entries] if discovery_job else select(snapshot, scope, payload.get('missions'))
    if not discovery_job and len(names) > MAX_BATCH:
        raise ValueError(f'A job cannot exceed the reviewed catalog of {MAX_BATCH} missions')
    dynamic = scope in CATEGORY_SCOPES
    excluded = [n for n in names if n in NONPERSISTENT] if dynamic else []
    names = [n for n in names if n not in excluded]
    initial_completed = []
    for name in ([] if discovery_job else names):
        if name in NONPERSISTENT:
            raise ValueError('This replayable mission cannot be permanently completed: ' + name)
        try:
            state = _state(_row(snapshot, name))
        except ValueError:
            if dynamic:
                continue
            raise
        if state == 'completed':
            initial_completed.append(name)
        if not dynamic and state not in ('active', 'accepted', 'available', 'completed'):
            raise ValueError('Mission prerequisites are not available: ' + name)
        if state == 'completed' and scope != 'challenge_credit' and payload.get('reset_completed') is not True:
            raise ValueError('Host already completed this mission; explicitly choose reset-and-complete')
    from . import farming_targets
    selected = farming_targets.resolve(payload)
    if len(selected) != 1:
        raise ValueError('Choose one acceptance player; completion still affects the shared lobby')
    rows = _party()
    target = selected[0]['pc']._path_name()
    if target not in [r['pc']._path_name() for r in rows]:
        raise ValueError('Selected player is no longer in this lobby')
    from mods_base import SETTINGS_DIR
    ident = uuid.uuid4().hex
    folder = Path(SETTINGS_DIR) / 'msbt_missions'
    folder.mkdir(parents=True, exist_ok=True)
    for previous in folder.glob('*.jsonl'):
        lines = previous.read_text(encoding='utf-8').splitlines()
        if lines and json.loads(lines[-1]).get('state') not in ('completed', 'cancelled', 'stopped'):
            raise RuntimeError('An earlier job was interrupted or uncertain; reconcile its receipt before another run: ' + previous.name)
    journal = folder / (ident + '.jsonl')
    journal.touch(exist_ok=False)
    _job = dict(ok=True, id=ident, state='running', scope='shared_lobby', names=names,
                index=0, completed=[], total=len(names), binding=_binding(rows), target=target,
                operation_scope=scope if discovery_job else 'missions', unit='locations or requirements' if discovery_job else 'missions',
                journal=str(journal), phase='prepare', message='Ready for one guarded step',
                dynamic=dynamic, selection_scope=scope, initial_completed=initial_completed,
                catalog_total=len(names) + len(excluded), excluded=excluded, pending=[], stall_since=None,
                deferred=[],
                settle_guest_progress=payload.get('settle_guest_progress') is True, next_step_at=0.0,
                guest_persistence='requires own-game verification')
    if not names:
        _job.update(state='completed', message='No completed missions are eligible for challenge-credit repair')
    _journal(dict(event='start', missions=names, binding=_job['binding'], target=target))
    if _job['state']=='completed':
        _journal(dict(event='state',state='completed',index=0))
    return status()


def _validate_exit(engine, row, name):
    import unrealsdk
    expected = []
    for label in CATALOG[name]['exit_names']:
        token = unrealsdk.make_struct('/Script/CoreUObject.SToken', Name=label)
        expected.append(engine.read(token._get_address() + 4, 8).hex())
    fact = row['exit_fact']
    if fact is None or fact['tag'] == 0:
        selected = '0' * 16
    elif fact['tag'] == 3:
        selected = fact['fname']
    else:
        raise ValueError('Unsupported mission exit variant')
    if row['exit_names'] != expected or expected.count(selected) != 1:
        raise ValueError('Unreviewed or ambiguous mission exit')


def _pending_repairs(snapshot):
    # Six exact positive dependencies proven in the prior side/DLC test; no arbitrary facts.
    from . import mission_discovery as discovery
    allowed = {'electi', 'heist', 'vending', 'clapgen', 'cowbell_ellie', 'cowbell_hatchery'}
    return [r['name'] for r in discovery.plan('travel_requirements', snapshot)
            if r['name'] in allowed and not r['blocked_reason']
            and r['name'] not in _job.get('checked_prerequisites', [])]


def _schedule_category(snapshot):
    """Recheck the unprocessed catalog after progress; never retry a native call."""
    pending = []
    for i in range(_job['index'], len(_job['names'])):
        name = _job['names'][i]
        access = _dlc_requirement(name)
        if access and not access['allowed']:
            _job['names'].insert(_job['index'], _job['names'].pop(i))
            return True
        try:
            state = _state(_row(snapshot, name))
            reason = 'Prerequisites not yet available' if state not in ('active', 'accepted', 'available', 'completed') else None
        except ValueError as exc:
            state, reason = 'unavailable', str(exc)
        if reason is None:
            _job['names'].insert(_job['index'], _job['names'].pop(i))
            _job['stall_since'] = None
            _job['pending'] = []
            if state == 'completed' and name not in _job['initial_completed']:
                _job['phase'] = 'complete'  # Cascaded completion: observe, do not reset.
            return True
        pending.append(dict(name=name, title=CATALOG[name]['title'], state=state, reason=reason))
    _job['pending'] = pending
    if _job['stall_since'] is None:
        _job['stall_since'] = time.monotonic()
    waited = time.monotonic() - _job['stall_since']
    _job['message'] = f"{len(pending)} missions still locked or unavailable; waiting for normal prerequisite updates."
    if waited >= 10:
        _job.update(ok=False, state='stopped', message=f"Incomplete: {len(pending)} missions remain locked or unavailable after prerequisite rechecks. No locked states were forced.")
        _journal(dict(event='state', state='stopped', index=_job['index'], pending=pending))
    return False


def _credit_completed(engine, party, name):
    from . import mission_challenges
    if _job.get('challenge_pending'):
        mission_challenges.reconcile(engine, party, _job['challenge_pending'], _journal)
        _job.pop('challenge_pending')
    if _job.get('cancel_requested'):
        _job.update(state='cancelled', message='Issued credit verified; remaining work cancelled')
        _journal(dict(event='state', state='cancelled', index=_job['index']))
        return False
    receipts = mission_challenges.credit_completed(engine, party, name, _journal)
    if receipts:
        _job['challenge_credit'] = receipts
    return True


def step(job_id):
    if not _job or job_id != _job['id']:
        raise ValueError('Mission job identifier changed')
    if _job['state'] != 'running':
        return status()
    issued = False
    try:
        engine = _engine()
        before = engine.snapshot()
        party = _party()
        if _binding(party) != _job['binding']:
            raise RuntimeError('Party changed; remaining work stopped')
        target = next(r['pc'] for r in party if r['pc']._path_name() == _job['target'])
        if _job.get('settle_guest_progress') and time.monotonic() < _job.get('next_step_at',0):
            _job['message'] = 'Waiting for mission transition to settle before the next operation'
            return status()
        if _job.get('dynamic') and _job['phase'] == 'prepare' and not _schedule_category(before):
            if _job['state'] == 'running':
                from . import mission_discovery as discovery
                repairs = _pending_repairs(before)
                if repairs:
                    key = repairs[0]
                    old, mutate, confirmed = discovery.operation(engine, 'travel_requirements', key, before, target)
                    _journal(dict(event='issued', operation='mission_prerequisite', name=key, before=old))
                    issued = True
                    actual = mutate()
                    _journal(dict(event='returned', operation='mission_prerequisite', name=key, after=actual))
                    if not confirmed(actual):
                        raise RuntimeError('Prerequisite repair unconfirmed; do not retry automatically')
                    _job.setdefault('checked_prerequisites', []).append(key)
                    _job['stall_since'] = None
                    _job['message'] = 'Verified mission prerequisite: ' + key
                    _journal(dict(event='state', state='running', index=_job['index'], prerequisite=key))
            return status()
        name = _job['names'][_job['index']]
        if _job.get('operation_scope', 'missions') != 'missions':
            from . import mission_discovery as discovery
            old, mutate, confirmed = discovery.operation(engine, _job['operation_scope'], name, before, target)
            _journal(dict(event='issued', operation=_job['operation_scope'], name=name, before=old))
            issued = True
            after = mutate()
            _journal(dict(event='returned', name=name, after=after))
            if not confirmed(after):
                raise RuntimeError('Discovery or travel requirement result unconfirmed; do not retry automatically')
            _job['completed'].append(name)
            _job['index'] += 1
            if _job['index'] == _job['total']:
                _job['state'] = 'stopped' if _job.get('deferred') else 'completed'
            _job['message'] = 'Verified locally: ' + name
            _journal(dict(event='state', state=_job['state'], index=_job['index']))
            return status()
        access = _dlc_requirement(name)
        if access and not access['allowed']:
            return _defer(name, access['reason'], access)
        row = _row(before, name)
        _validate_exit(engine, row, name)
        state = _state(row)
        phase = _job['phase']
        if _job.get('selection_scope') == 'challenge_credit':
            if state != 'completed':
                raise RuntimeError('Credit repair stopped: mission is no longer completed')
            _job['phase'] = phase = 'complete'
        if phase == 'accept' and state in ('active', 'accepted', 'completed'):
            _journal(dict(event='observed_activation', mission=name, after=row))
            _job['phase'] = phase = 'complete'
        if phase == 'complete' and state == 'completed':
            if _credit_completed(engine, party, name) is False:
                return status()
            _job['completed'].append(name)
            _job['index'] += 1
            _job['phase'] = 'prepare'
            if _job['index'] == len(_job['names']):
                _job['state'] = 'stopped' if _job.get('deferred') else 'completed'
            _job['message'] = f'{CATALOG[name]["title"]}: completion and applicable Grassroots credit verified'
            _journal(dict(event='observed_completed', mission=name, after=row))
            _journal(dict(event='state', state=_job['state'], index=_job['index']))
            return status()
        # Accepted is not Active: completing during activation can leave guest saves unfinished.
        if state == 'accepted':
            waiting = _job.get('activation_wait')
            if not waiting or waiting['mission'] != name:
                waiting = dict(mission=name, since=time.monotonic())
                _job['activation_wait'] = waiting
                _journal(dict(event='waiting_for_activation', mission=name, after=row))
            if time.monotonic() - waiting['since'] >= 60.0:
                raise RuntimeError(f'{CATALOG[name]["title"]}: still accepted after 60 seconds; stopped before completion. Let the mission activate normally before recovering.')
            _job['message'] = f'{CATALOG[name]["title"]}: waiting for the mission to become active before completing'
            return status()
        _job.pop('activation_wait', None)
        if phase == 'prepare':
            operation = {'completed': 'reset', 'available': 'accept', 'active': 'complete'}.get(state)
        elif phase == 'accept' and state == 'available':
            operation = 'accept'
        elif phase == 'complete' and state == 'active':
            operation = 'complete'
        else:
            raise ValueError('Mission changed outside this job; stopped without retry')
        if operation is None:
            raise ValueError('Mission is not eligible for this step')
        record, storage = int(row['record'], 16), int(row['storage'], 16)
        vt = engine.u64(record)
        if engine.u64(vt + 0xf8) != engine.base + 0xd80660 or engine.u64(vt + 0x110) != engine.base + 0x419fefa:
            raise RuntimeError('Mission callbacks differ from the reviewed build')
        if engine.u64(record + 0xa8) != storage or engine.read(storage, 1) == b'\0':
            raise RuntimeError('Mission storage is no longer valid')
        _journal(dict(event='issued', mission=name, operation=operation, before=row))
        issued = True
        if operation == 'reset':
            C.WINFUNCTYPE(None, C.c_void_p, C.c_uint8, C.c_bool)(engine.base + 0x3d32a5c)(storage, 2, False)
            expected, next_phase = ('available',), 'accept'
        elif operation == 'accept':
            import unrealsdk
            token = unrealsdk.make_struct('/Script/CoreUObject.SToken',
                Hash=struct.unpack('<i', bytes.fromhex(row['token'])[:4])[0], Name=name)
            if engine.read(token._get_address(), 12).hex() != row['token']:
                raise RuntimeError('Mission token mismatch')
            target.ServerActivateMission(token, 1, True, int(target.PlayerState.StableIndex))
            expected, next_phase = ('accepted', 'active', 'completed'), 'complete'
        else:
            C.WINFUNCTYPE(None, C.c_void_p, C.c_uint8, C.c_bool)(engine.base + 0xf19ee4)(record, 6, False)
            expected, next_phase = ('completed',), 'prepare'
        after = _row(engine.snapshot(), name)
        _journal(dict(event='returned', mission=name, operation=operation, after=after))
        if _state(after) not in expected:
            _job['failure'] = dict(mission=name, title=CATALOG[name]['title'], operation=operation,
                                   observed=_state(after))
            raise RuntimeError(f'{CATALOG[name]["title"]}: {operation} returned {_state(after)}; expected {", ".join(expected)}. Use Recover stopped job; no automatic retry.')
        _job['phase'] = next_phase
        if _job.get('settle_guest_progress'):
            _job['next_step_at'] = time.monotonic() + 2.0
        if operation == 'complete':
            if _credit_completed(engine, party, name) is False:
                return status()
            _job['completed'].append(name)
            _job['index'] += 1
            if _job['index'] == len(_job['names']):
                _job['state'] = 'stopped' if _job.get('deferred') else 'completed'
        _job['message'] = f'{CATALOG[name]["title"]}: {operation} verified in shared lobby'
    except Exception as exc:
        if hasattr(exc, 'receipt') and exc.__class__.__name__ == 'CreditPending':
            _job.update(challenge_pending=exc.receipt, phase='complete', state='running', message=str(exc))
            _journal(dict(event='state', state='running', index=_job['index'], message=str(exc)))
            return status()
        _job.update(ok=False, state='uncertain' if issued or getattr(exc, 'issued', False) else 'stopped', message=str(exc))
    _journal(dict(event='state', state=_job['state'], index=_job['index'], message=_job['message']))
    return status()


def resume(job_id):
    """Only recover a stopped job whose pending completion is already confirmed."""
    if not _job or job_id != _job['id']:
        raise ValueError('Mission job identifier changed')
    if _job['state'] != 'stopped' or _job.get('operation_scope', 'missions') != 'missions' or (_job.get('phase') not in ('accept', 'complete') and not (_job.get('dynamic') and _job.get('phase') == 'prepare')):
        raise ValueError('This stopped job requires separate review; it cannot be resumed automatically')
    if _binding(_party()) != _job['binding']:
        raise ValueError('Original party changed; cannot resume this batch')
    snapshot = _engine().snapshot()
    if _job.get('dynamic') and _job['phase'] == 'prepare':
        eligible = False
        for name in _job['names'][_job['index']:]:
            try:
                eligible = eligible or _state(_row(snapshot, name)) in ('active', 'accepted', 'available', 'completed')
            except ValueError:
                pass
        if not eligible and not _pending_repairs(snapshot):
            raise ValueError('No newly eligible missions or reviewed prerequisites remain; unresolved entries still need investigation')
        _job.update(ok=True, state='running', stall_since=None, message='Continuing prerequisite checks and remaining missions')
        _journal(dict(event='resume', state='running', index=_job['index']))
        return status()
    row = _row(snapshot, _job['names'][_job['index']])
    _validate_exit(_engine(), row, _job['names'][_job['index']])
    allowed = ('accepted', 'active', 'completed') if _job['phase'] == 'accept' else ('completed',)
    if _state(row) not in allowed:
        raise ValueError('Pending mission is not confirmed completed or naturally activated for this phase; no retry issued')
    _job.update(ok=True, state='running', message='Confirmed forward game progression; ready to continue remaining missions')
    _journal(dict(event='resume', state='running', index=_job['index'], observed=row))
    return status()


def recover(payload):
    """Reconcile a recorded call by reading state. Never replay it or undo it."""
    global _job
    job_id = payload.get('job_id', '')
    if not isinstance(job_id, str) or len(job_id) != 32 or any(c not in '0123456789abcdef' for c in job_id):
        raise ValueError('Invalid recovery job identifier')
    live = _job is not None and _job['id'] == job_id
    if _job and _job['state'] == 'running':
        raise ValueError('Cancel the running job before recovery')
    from mods_base import SETTINGS_DIR
    path = Path(_job['journal']) if live else Path(SETTINGS_DIR) / 'msbt_missions' / (job_id + '.jsonl')
    events = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    issued = next((i for i in range(len(events)-1, -1, -1) if events[i].get('event') == 'issued'), None)
    if issued is None:
        raise ValueError('No recorded mission call to reconcile')
    call = events[issued]
    name, operation = call.get('mission'), call.get('operation')
    if operation == 'challenge_credit':
        from . import mission_challenges
        returned = next((e for e in events[issued+1:] if e.get('event') == 'returned'
                         and e.get('operation') == operation and e.get('mission') == name), None)
        if returned is None:
            raise ValueError('Challenge call has no durable return receipt; inspect before retry')
        receipt = {k: v for k, v in call.items() if k not in ('event', 'time', 'job_id')}
        mission_challenges.reconcile(_engine(), _party(), receipt, lambda event: None)
        report = dict(ok=True, mission=name, title=CATALOG[name]['title'], operation=operation,
                      observed='completed', acceptance_unchanged=False, access=None)
        state = 'completed'
    else:
        if name not in CATALOG or operation not in ('reset', 'accept', 'complete'):
            raise ValueError('This recovery handles mission calls only; other operations still require inspection')
        returned = next((e for e in events[issued+1:] if e.get('event') == 'returned' and e.get('mission') == name and e.get('operation') == operation), None)
        if returned is None or time.time() - returned['time'] < 2:
            raise ValueError('Call has no durable return receipt or is still settling; no retry or clearance issued')
        engine = _engine()
        current = _row(engine.snapshot(), name)
        if current['token'] != call['before']['token']:
            raise ValueError('Mission identity differs from the receipt')
        _validate_exit(engine, current, name)
        state = _state(current)
        accepted = state in ('active', 'accepted', 'completed')
        safe = (operation == 'accept' and (accepted or (state == 'available' and _state(returned['after']) == 'available'))) or (operation == 'reset' and state in ('available', 'accepted', 'active', 'completed')) or (operation == 'complete' and state == 'completed')
        if not safe:
            raise ValueError(f'{CATALOG[name]["title"]}: {operation} still unresolved ({state}); no retry or clearance issued')
        report = dict(ok=True, mission=name, title=CATALOG[name]['title'], operation=operation, observed=state,
                      acceptance_unchanged=operation == 'accept' and state == 'available', access=_dlc_requirement(name))
    mode = payload.get('mode', 'inspect')
    if mode == 'inspect':
        return dict(report, message=f'{report["title"]}: {operation} reconciled as {state}; no game changes made.')
    if mode not in ('continue', 'close') or payload.get('acknowledge_shared_progress') is not True:
        raise ValueError('Choose continue or close and acknowledge shared progress')
    if not live and mode != 'close':
        raise ValueError('Recovered after restart: close the reconciled job, then preview a new batch')
    if mode == 'close':
        event = dict(event='recovered', state='stopped', report=report, time=time.time())
        with path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(event) + '\n'); stream.flush(); os.fsync(stream.fileno())
        if live:
            _job.pop('challenge_pending', None)
            _job.pop('cancel_requested', None)
            _job.update(ok=True, state='stopped', message=f'{report["title"]}: reconciled as {state}. Job closed; previous progress retained.')
        return dict(ok=True, state='stopped', id=job_id, message=f'{report["title"]}: reconciled as {state}. Job closed; previous progress retained. Refresh preview for a new run.')
    party = _party()
    if _binding(party) != _job['binding']:
        from . import farming_targets
        selected = farming_targets.resolve(payload)
        if len(selected) != 1:
            raise ValueError('Select one currently loaded acceptance player')
        _job['binding'], _job['target'] = _binding(party), selected[0]['pc']._path_name()
    _job.pop('challenge_pending', None)
    _job.pop('cancel_requested', None)
    _job.update(ok=True, state='running', stall_since=None)
    _journal(dict(event='recovered', report=report, state='running', binding=_job['binding'], target=_job['target']))
    if report['acceptance_unchanged']:
        return _defer(name, 'Acceptance returned unchanged; skipped without retry.', report['access'])
    _job['phase'] = 'accept' if operation == 'reset' and state == 'available' else 'complete'
    _job['message'] = report['title'] + ': reconciled; continuing without repeating the recorded call.'
    return status()


def cancel(job_id):
    if not _job or job_id != _job['id']:
        raise ValueError('Mission job identifier changed')
    if _job and _job.get('challenge_pending'):
        _job['cancel_requested'] = True
        _job['message'] = 'Cancelling after issued Grassroots credit verifies'
        return status()
    if not _job or job_id != _job['id']:
        raise ValueError('Mission job identifier changed')
    if _job['state'] == 'running':
        _job.update(state='cancelled', message='Remaining steps cancelled; completed changes are retained')
        _journal(dict(event='state', state='cancelled', index=_job['index']))
    return status()


def clear_runtime_state():
    """Disable pending work; retain uncertainty and durable evidence."""
    global _runtime
    if _job and _job['state'] == 'running':
        cancel(_job['id'])
    _runtime = None


def dispatch(action, payload):
    try:
        if action == 'mission_status':
            return status()
        if action == 'mission_dlc_status':
            return dlc_status()
        if action == 'mission_recover':
            return recover(payload)
        if action == 'mission_preview':
            return preview(payload)
        if action == 'mission_start':
            return start(payload)
        if action == 'mission_step':
            return step(payload.get('job_id'))
        if action == 'mission_resume':
            return resume(payload.get('job_id'))
        if action == 'mission_cancel':
            return cancel(payload.get('job_id'))
        raise ValueError('Unknown mission action')
    except Exception as exc:
        return dict(ok=False, message=str(exc))
