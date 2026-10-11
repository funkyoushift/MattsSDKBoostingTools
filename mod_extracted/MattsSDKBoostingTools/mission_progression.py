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
                            resets_host_completion=state == 'completed', excluded=name in NONPERSISTENT))
    return dict(ok=True, scope='shared_lobby', selection_scope=scope, missions=entries, max_batch=MAX_BATCH,
                catalog_total=len(entries), excluded_total=sum(r['excluded'] for r in entries),
                unsupported=UNVERIFIED, message='Changes can affect host and all connected players. Preview is read-only.')


def status():
    if _job is None:
        return dict(ok=True, state='idle', unsupported=UNVERIFIED, max_batch=MAX_BATCH)
    return {k: v for k, v in _job.items() if k not in ('binding', 'target', 'journal', 'names')}


def _journal(event):
    with Path(_job['journal']).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(dict(event, time=time.time())) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def start(payload):
    global _job
    if _job and _job['state'] in ('running', 'uncertain'):
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
        if state == 'completed' and payload.get('reset_completed') is not True:
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
                guest_persistence='requires own-game verification')
    _journal(dict(event='start', missions=names, binding=_job['binding'], target=target))
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
                _job['state'] = 'completed'
            _job['message'] = 'Verified locally: ' + name
            _journal(dict(event='state', state=_job['state'], index=_job['index']))
            return status()
        row = _row(before, name)
        _validate_exit(engine, row, name)
        state = _state(row)
        phase = _job['phase']
        if phase == 'accept' and state in ('active', 'accepted', 'completed'):
            _journal(dict(event='observed_activation', mission=name, after=row))
            _job['phase'] = phase = 'complete'
        if phase == 'complete' and state == 'completed':
            _job['completed'].append(name)
            _job['index'] += 1
            _job['phase'] = 'prepare'
            if _job['index'] == len(_job['names']):
                _job['state'] = 'completed'
            _job['message'] = f'{CATALOG[name]["title"]}: game completed it after acceptance; verified without another write'
            _journal(dict(event='observed_completed', mission=name, after=row))
            _journal(dict(event='state', state=_job['state'], index=_job['index']))
            return status()
        if phase == 'prepare':
            operation = {'completed': 'reset', 'available': 'accept', 'active': 'complete', 'accepted': 'complete'}.get(state)
        elif phase == 'accept' and state == 'available':
            operation = 'accept'
        elif phase == 'complete' and state in ('active', 'accepted'):
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
            raise RuntimeError('Native result did not match; do not repeat automatically')
        _job['phase'] = next_phase
        if operation == 'complete':
            _job['completed'].append(name)
            _job['index'] += 1
            if _job['index'] == len(_job['names']):
                _job['state'] = 'completed'
        _job['message'] = f'{CATALOG[name]["title"]}: {operation} verified in shared lobby'
    except Exception as exc:
        _job.update(ok=False, state='uncertain' if issued else 'stopped', message=str(exc))
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


def cancel(job_id):
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
