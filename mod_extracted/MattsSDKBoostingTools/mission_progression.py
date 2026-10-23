"""Explicit shared-lobby mission jobs. Called on the bridge/Quick Menu game thread.

Completion is not isolated to the selected player. A pinned player supplies normal
acceptance context; every participant and the host campaign can be affected.
Objective rollback and full progress erasure are deliberately not approximated.
"""
from __future__ import annotations
from .mission_native import native_address, native_fingerprint

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
# Mission4 /mission/records/0/entries/78: brepeatable=true. A normal reload
# reopens this arena, so automatic completion must not farm it on every run.
AUTOMATIC_REPEATABLE = {'Mission_Mandolin_CircleOfSlaughter'}
# Mission4 /mission/records/1/entries/7 and /8 have no mission set/type;
# registered Part 1 contains the later stages. Keep authored rows visible, and
# only exclude these legacy splits when the current native inventory lacks them.
LEGACY_SPLITS = {'Mission_Micro_BackMcCrackyPt2', 'Mission_Micro_BackMcCrackyPt3'}
_runtime = None
_job = None


def _engine():
    global _runtime
    if _runtime is not None and (_job is None or _job.get('closed') or _job.get('state') in ('completed', 'cancelled')):
        import sys
        full = sys.modules.get(__package__ + '.full_progress_runtime')
        runner = getattr(full, '_runner', None)
        full_job = getattr(runner, 'job', None)
        if not full_job or full_job.get('state') in ('finished', 'cancelled'):
            try:
                _runtime.ensure_world()
            except RuntimeError as exc:
                if str(exc) != 'Mission run stopped: world instance changed; explicit reload required':
                    raise
                _runtime = None
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


def _metadata(name):
    if name.startswith('bounty:'):
        return dict(name=name, title='Current tracked bounty', category='bounty', exit_names=['None'])
    return CATALOG[name]


def _row(snapshot, name):
    if name.startswith('bounty:'):
        rows = [r for r in snapshot['missions'] if r['token'] == name[7:]]
        if len(rows) != 1 or rows[0].get('generated') != 1 or rows[0].get('replication_type') != 0 or rows[0].get('ownership') != 0:
            raise ValueError('Tracked bounty instance is missing or is not shared')
        return rows[0]
    rows = [r for r in snapshot['missions'] if (r['source_identity'] or {}).get('name') == name]
    if len(rows) != 1 or rows[0]['generated'] or rows[0]['replication_type'] != 0:
        raise ValueError('Mission is missing, ambiguous, generated or not an ordinary shared mission: ' + name)
    return rows[0]


def _state(row):
    return (row['status_fact'] or {}).get('known_status')


def _automatic_exclusion(snapshot, name):
    if name in NONPERSISTENT:
        return 'This replayable mission is source-marked never saved; permanent completion is not supported'
    if name in AUTOMATIC_REPEATABLE:
        return 'Repeatable arena; use individual completion or Practice to play another run'
    if name in LEGACY_SPLITS and not any(
            str((row.get('source_identity') or {}).get('name', '')).casefold() == name.casefold()
            for row in snapshot['missions']):
        return 'Legacy split definition not registered in this game; the playable first mission contains these stages'
    return None


def _campaign_names(snapshot):
    # Completion's public catalog is not a reset inventory. Internal mission
    # records and the prologue also retain progress and parent-group state.
    names = [(r.get('source_identity') or {}).get('name') for r in snapshot['missions']
             if not r.get('generated') and r.get('replication_type') == 0]
    names = [name for name in names if name]
    if len(names) != len(set(names)):
        raise ValueError('Ambiguous campaign mission records; reset was not started')
    return names


def select(snapshot, scope, names=None, challenge_id=None):
    if scope == 'challenge_credit':
        from .mission_challenges import CREDIT_MISSIONS, credit_definition
        if challenge_id:
            authored=list(credit_definition(challenge_id)['missions'])
            if names is None:return authored
            if not isinstance(names,list) or not names or any(
                    not isinstance(name,str) or name not in authored for name in names):
                raise ValueError('Credit selection must contain distinct missions from the authored challenge')
            if len(names)!=len(set(names)):
                raise ValueError('Credit selection must contain distinct missions from the authored challenge')
            return [name for name in authored if name in names]
        return [n for n in CREDIT_MISSIONS if any((r.get('source_identity') or {}).get('name')==n
                and _state(r)=='completed' and not r.get('generated') and r.get('replication_type')==0
                for r in snapshot['missions'])]
    if scope in UNVERIFIED:
        raise ValueError(UNVERIFIED[scope])
    if scope == 'bounty':
        candidates = [r for r in snapshot['missions'] if r['token'] in snapshot['tracked']
                      and r.get('generated') == 1 and r.get('replication_type') == 0
                      and r.get('ownership') == 0 and _state(r) in ('active', 'accepted')]
        if len(candidates) != 1:
            raise ValueError('Track exactly one active shared bounty before using current bounty')
        selected = ['bounty:' + candidates[0]['token']]
        if names and names != selected:
            raise ValueError('Tracked bounty changed; refresh preview before completing it')
        return selected
    if scope == 'current':
        tracked = set(snapshot['tracked']) - {'0' * 24}
        candidates = [r for r in snapshot['missions'] if r['token'] in tracked
                      and not r.get('generated') and r.get('replication_type', 0) == 0
                      and (r.get('source_identity') or {}).get('name') in CATALOG]
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
    names = select(snapshot, scope, payload.get('missions'),payload.get('challenge_id'))
    entries = []
    for name in names:
        try:
            row = _row(snapshot, name)
            if scope == 'bounty':
                _validate_exit(_engine(), row, name)
            state = _state(row)
            reason = None if state == 'completed' or (scope != 'challenge_credit' and state in ('active', 'accepted', 'available')) else 'Mission completion is required before credit repair'
        except ValueError as exc:
            state, reason = 'unavailable', str(exc)
        exclusion = _automatic_exclusion(snapshot, name) if scope in CATEGORY_SCOPES else (
            _automatic_exclusion(snapshot, name) if name in NONPERSISTENT else None)
        if exclusion:
            reason = exclusion
        entries.append(dict(_metadata(name), state=state, blocked_reason=reason,
                            resets_host_completion=state == 'completed' and scope != 'challenge_credit', excluded=bool(exclusion)))
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
    return dict(ok=True, packs=list(mission_dlc.inspect(_party(),engine=_engine()).values()))


def _dlc_requirement(name):
    from . import mission_dlc
    if not any(n.casefold()==name.casefold() for n in mission_dlc.DATA['missions']):
        return None
    return mission_dlc.requirement(name, mission_dlc.inspect(_party(),engine=_engine()))


def _defer(name, reason, access=None):
    entry = dict(name=name, title=_metadata(name)['title'], reason=reason, state='deferred')
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


def _quarantine_failed_mission(name, exc, issued, operation):
    """Retain an unresolved receipt and continue independent Full Game work."""
    item=dict(mission=name,title=_metadata(name)['title'],operation=operation,
              issued=bool(issued or getattr(exc,'issued',False)),reason=str(exc))
    if getattr(exc,'operation',None):item['operation']=exc.operation
    if getattr(exc,'address',None):item['address']=exc.address
    _job.setdefault('unverified_operations',[]).append(item)
    _journal(dict(event='operation_quarantined',**item))
    _job.update(ok=True,state='running')
    return _defer(name,'Unverified operation retained; no automatic retry: '+str(exc))


def _journal(event):
    with Path(_job['journal']).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(dict(event, time=time.time())) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def require_clear_journals():
    """Reject an interrupted run before either coordinator changes the world."""
    from mods_base import SETTINGS_DIR
    folder = Path(SETTINGS_DIR) / 'msbt_missions'
    for previous in folder.glob('*.jsonl'):
        lines = previous.read_text(encoding='utf-8').splitlines()
        if lines and json.loads(lines[-1]).get('state') not in ('completed', 'cancelled', 'stopped'):
            raise RuntimeError('An earlier job was interrupted or uncertain; reconcile its receipt before another run: ' + previous.name)


def start(payload, *, manage_replay_travel=True, use_objective_graph=True):
    # Practice owns the same unload/return sequence around its child reset.
    # This internal argument is deliberately not accepted from bridge payloads.
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
    names = [r['name'] for r in entries] if discovery_job else select(snapshot, scope, payload.get('missions'),payload.get('challenge_id'))
    credit_challenge=payload.get('challenge_id') if scope=='challenge_credit' else None
    if credit_challenge:
        incomplete=[]
        for name in names:
            try:
                row=_row(snapshot,name)
                if _state(row)!='completed' or row.get('generated') or row.get('replication_type',0)!=0:
                    incomplete.append(name)
            except ValueError:
                incomplete.append(name)
        if incomplete:
            raise ValueError('Mission credit requires completed shared mission records: '+', '.join(incomplete[:8]))
    mode = payload.get('mode', 'complete')
    if mode not in ('complete', 'reopen', 'reset_completed'):
        raise ValueError('Unknown mission operation')
    preserve_completed = payload.get('preserve_completed') is True
    if preserve_completed and mode != 'complete':
        raise ValueError('Preserving completed missions requires completion mode')
    if mode == 'reopen' and (discovery_job or scope not in ('named', 'current') or len(names) != 1):
        raise ValueError('Choose one started ordinary mission to reopen')
    if mode == 'reset_completed':
        if discovery_job or scope != 'all':
            raise ValueError('Campaign reset requires all missions; use Reopen for one mission')
        names = _campaign_names(snapshot)
        if 'Mission_Main_PrisonPrologue' not in names:
            raise ValueError('The campaign opening record is unavailable; no reset started')
    if not discovery_job and mode != 'reset_completed' and len(names) > MAX_BATCH:
        raise ValueError(f'A job cannot exceed the reviewed catalog of {MAX_BATCH} missions')
    dynamic = scope in CATEGORY_SCOPES and mode == 'complete'
    exclusion_reasons = {n: reason for n in names
                         if dynamic and (reason := _automatic_exclusion(snapshot, n))}
    excluded = list(exclusion_reasons)
    names = [n for n in names if n not in excluded]
    graph = use_objective_graph and mode == 'complete' and not discovery_job and scope not in ('bounty','challenge_credit')
    replay_travel = mode == 'reopen' and manage_replay_travel
    if replay_travel:
        from .mission_execution import DATA
        definition = DATA.get(names[0], {})
        maps = definition.get('execution_maps') or [definition.get('execution_map')]
        if not definition.get('execution_map') or not maps or any(not m for m in maps):
            raise ValueError('Authored mission map is unresolved; no replay reset started')
    coverage_issues = {}
    if graph:
        from . import mission_execution
        for name in names:
            if preserve_completed:
                try:
                    if _state(_row(snapshot,name)) == 'completed':continue
                except ValueError:pass
            reason=mission_execution.coverage_error(name)
            definition=mission_execution.DATA.get(name,{})
            reason=reason or (None if definition.get('execution_map') else 'Authored mission map is unresolved')
            if reason:coverage_issues[name]=reason
        if coverage_issues and not dynamic:
            raise ValueError('; '.join(_metadata(n)['title']+': '+reason for n,reason in coverage_issues.items()))
    initial_completed = []
    for name in ([] if discovery_job else names):
        if name in NONPERSISTENT and mode != 'reset_completed':
            raise ValueError('This replayable mission cannot be permanently completed: ' + name)
        try:
            state = _state(_row(snapshot, name))
        except ValueError:
            if dynamic:
                continue
            raise
        if state == 'completed':
            initial_completed.append(name)
        if mode == 'reopen' and state not in ('completed', 'active', 'accepted'):
            raise ValueError('Choose a started mission to reopen')
        if mode != 'reset_completed' and not dynamic and state not in ('active', 'accepted', 'available', 'completed'):
            raise ValueError('Mission prerequisites are not available: ' + name)
        if state == 'completed' and scope != 'challenge_credit' and payload.get('reset_completed') is not True and not preserve_completed:
            raise ValueError('Host already completed this mission; explicitly choose reset-and-complete')
    from . import farming_targets
    selected = farming_targets.resolve(payload)
    if len(selected) != 1:
        raise ValueError('Choose one acceptance player; completion still affects the shared lobby')
    rows = _party()
    if preserve_completed and len(rows) != 1:
        raise ValueError('Completed missions can only be preserved in solo completion; guest credit needs separate verification')
    target = selected[0]['pc']._path_name()
    if target not in [r['pc']._path_name() for r in rows]:
        raise ValueError('Selected player is no longer in this lobby')
    completion_context=None
    if graph or replay_travel:
        from .mission_completion_context import begin
        completion_context=begin(rows,target)
    from mods_base import SETTINGS_DIR
    ident = uuid.uuid4().hex
    folder = Path(SETTINGS_DIR) / 'msbt_missions'
    folder.mkdir(parents=True, exist_ok=True)
    require_clear_journals()
    journal = folder / (ident + '.jsonl')
    journal.touch(exist_ok=False)
    _job = dict(ok=True, id=ident, state='running', scope='shared_lobby', names=names,
                index=0, completed=[], total=len(names), binding=_binding(rows), target=target,
                operation_scope=scope if discovery_job else 'missions', unit='locations or requirements' if discovery_job else 'missions',
                journal=str(journal), phase='prepare', message='Ready for one guarded step',
                dynamic=dynamic, selection_scope=scope, initial_completed=initial_completed,
                mode=mode, preserve_completed=preserve_completed,
                completion_path='objective_graph' if graph else 'mission_replay' if replay_travel else 'normal_acceptance', objective_runs={},
                placement_policy='map_only' if graph else 'replay',
                coverage_issues=coverage_issues,
                campaign_replay=mode == 'reset_completed',
                catalog_total=len(names) + len(excluded), excluded=excluded, pending=[], stall_since=None,
                exclusion_reasons=exclusion_reasons,
                deferred=[], defer_unconfirmed_mission_credit=payload.get('defer_unconfirmed_mission_credit') is True,
                continue_on_mission_failure=payload.get('continue_on_mission_failure') is True,
                unverified_operations=[],
                unverified_challenge_credit=[],
                credit_challenge=credit_challenge,
                settle_guest_progress=payload.get('settle_guest_progress') is True, next_step_at=0.0,
                guest_persistence='requires own-game verification')
    if graph or replay_travel:
        _job['completion_context']=completion_context
    if not names:
        _job.update(state='completed', message='No completed missions are eligible for this operation')
    _journal(dict(event='start', missions=names, binding=_job['binding'], target=target,
                  completion_path=_job['completion_path'],
                  campaign_replay=_job['campaign_replay']))
    if _job['state']=='completed':
        _journal(dict(event='state',state='completed',index=0))
    return status()


def _validate_exit(engine, row, name):
    import unrealsdk
    expected = []
    for label in _metadata(name)['exit_names']:
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
            and not ((access := _dlc_requirement(r['parent'])) and not access['allowed'])
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
        pending.append(dict(name=name, title=_metadata(name)['title'], state=state, reason=reason))
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
    if name.startswith('bounty:'):
        return True
    import sys
    if _job.get('selection_scope')!='challenge_credit':
        from . import mission_effects
        mission_effects.complete_dependencies(sys.modules[__name__], engine, party, name)
    from . import mission_challenges
    if _job.get('challenge_pending'):
        mission_challenges.reconcile(engine, party, _job['challenge_pending'], _journal)
        _job.pop('challenge_pending')
    if _job.get('cancel_requested'):
        _job.update(state='cancelled', message='Issued credit verified; remaining work cancelled')
        _journal(dict(event='state', state='cancelled', index=_job['index']))
        return False
    def record_mismatch(item):
        pending=_job['unverified_challenge_credit']
        if not any(r['mission']==item['mission'] and r.get('player_id')==item['player_id']
                   and r.get('player_path')==item['player_path'] for r in pending):
            pending.append(item)
            _journal(dict(event='challenge_credit_deferred',**item))
    receipts = mission_challenges.credit_completed(
        engine, party, name, _journal,
        on_mismatch=record_mismatch if _job.get('defer_unconfirmed_mission_credit') else None,
        challenge_id=_job.get('credit_challenge'))
    if receipts:
        _job['challenge_credit'] = receipts
    return True


def step(job_id):
    if not _job or job_id != _job['id']:
        raise ValueError('Mission job identifier changed')
    if _job['state'] != 'running':
        return status()
    issued = False
    _job.pop('await_tick', None)
    try:
        if _job.get('campaign_replay'):
            import sys
            from . import campaign_replay
            campaign_replay.step(sys.modules[__name__])
            return status()
        if _job.get('completion_path') in ('objective_graph', 'mission_replay'):
            import sys
            from .mission_completion_context import observe
            if not observe(sys.modules[__name__]):return status()
        engine = _engine()
        if _job.get('operation_scope') in ('map_locations', 'travel_stations'):
            # These reads use the discovery manager, not mission records. Keep
            # all context guards without rescanning every mission per location.
            engine.validate_context()
            before = {}
        else:
            before = engine.snapshot()
        party = _party()
        if _binding(party) != _job['binding']:
            raise RuntimeError('Party changed; remaining work stopped')
        if _job.get('preserve_completed') and len(party) != 1:
            raise RuntimeError('Solo completion changed; guest credit is not inferred from host progress')
        target = next(r['pc'] for r in party if r['pc']._path_name() == _job['target'])
        if _job.get('mode') == 'reset_completed':
            from . import mission_reset
            if _job['phase'] == 'prepare':
                reset_rows = [_row(before, name) for name in _job['names']
                              if _state(_row(before, name)) in
                              ('accepted', 'active', 'completed', 'failed', 'available', 'locked')]
                _job.update(phase='campaign_verify', state='uncertain', ok=False)
                _journal(dict(event='campaign_reset_issued', missions=_job['names'],
                              tokens={name: _row(before, name)['token'] for name in _job['names']}))
                issued = True
                mission_reset.reset_campaign(engine, reset_rows, _journal)
                _journal(dict(event='campaign_reset_returned'))
                _job.update(state='running', ok=True, message='Mission data reset; checking normal story activation')
                return status()
            states = {name: _state(_row(before, name)) for name in _job['names']}
            remaining = [dict(name=name, title=CATALOG.get(name, {}).get('title', name), state=value)
                         for name, value in states.items() if value == 'completed']
            _job['remaining_completed'] = remaining
            if remaining:
                raise RuntimeError(f'{len(remaining)} reset records still read completed; no reset repeated. '
                                   'Inspect or close this reset job; retained world state still needs repair.')
            first = 'Mission_Main_PrisonPrologue' if 'Mission_Main_PrisonPrologue' in states else 'Mission_Main_Beach'
            later_active = [name for name, value in states.items()
                if CATALOG.get(name, {}).get('category') == 'story' and name != first
                and value in ('active', 'accepted')]
            if later_active:
                raise RuntimeError('Later story missions activated unexpectedly: ' + ', '.join(later_active))
            _job.update(state='completed', index=len(states), completed=list(states),
                message='Named mission records reset, including internal records. '
                        'World activity state and normal replay still require verification; '
                        'this does not yet establish a complete fresh-game reset.')
            _journal(dict(event='state', state='completed', index=_job['index'], observed=states))
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
            if confirmed(old):
                _journal(dict(event='already_complete', operation=_job['operation_scope'], name=name, observed=old))
            else:
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
        if _job.get('preserve_completed') and state == 'completed' and phase == 'prepare':
            _job['phase'] = phase = 'complete'
        if name in _job.get('related_completion', ()) and phase == 'prepare':
            if state == 'completed':
                _job['phase'] = phase = 'complete'  # Never reset a cascaded completion.
            elif state in ('locked', None):
                since = _job.setdefault('related_wait_since', time.monotonic())
                if time.monotonic() - since > 10:
                    raise RuntimeError('Related mission is still unavailable after prerequisite rechecks')
                _job['message'] = 'Waiting for related mission prerequisites; no mission call repeated'
                return status()
            else:
                _job.pop('related_wait_since', None)
        if _job.get('mode') in ('reopen', 'reset_completed'):
            if _job.get('completion_path') == 'mission_replay':
                import sys
                from . import mission_execution, mission_completion_context
                definition = mission_execution.DATA[name]
                owner = sys.modules[__name__]
                if phase == 'prepare':
                    if not mission_completion_context.prepare_reset(owner,name,row,definition):return status()
                elif not mission_completion_context.travel_to(owner,name,row,definition['title'],definition['execution_map']):
                    return status()
            issued = phase == 'prepare' or state == 'available'
            return _reopen_step(engine, row, name, target)
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
            _job['message'] = f'{_metadata(name)["title"]}: completion and applicable mission credit verified'
            _journal(dict(event='observed_completed', mission=name, after=row))
            _journal(dict(event='state', state=_job['state'], index=_job['index']))
            return status()
        native_graph = (_job.get('completion_path') == 'objective_graph' and
                        not name.startswith('bounty:'))
        if native_graph:
            reason=_job.get('coverage_issues',{}).get(name)
            if reason:return _defer(name,reason)
            import sys
            from . import mission_execution,mission_completion_context
            definition=mission_execution.DATA.get(name)
            mission_execution.require_coverage(name)
            prepare=(mission_completion_context.prepare_reset if state=='completed' and phase=='prepare'
                     else mission_completion_context.prepare)
            if not prepare(sys.modules[__name__],name,row,definition):return status()
        if native_graph and state in ('locked', None) and phase == 'accept':
            since = _job.setdefault('activation_since', time.monotonic())
            if time.monotonic() - since > 120:
                raise RuntimeError('Reopened mission prerequisites did not activate; no reset repeated')
            _job['message'] = 'Waiting for reopened mission prerequisites; no reset repeated'
            return status()
        # Restore the original normal-acceptance completion path.
        _job.pop('activation_wait', None)
        if phase == 'prepare':
            operation = {'completed': 'reset', 'available': 'accept', 'active': 'complete', 'accepted': 'complete'}.get(state)
        elif phase == 'accept' and state == 'available':
            operation = 'accept'
        elif phase == 'complete' and state in ('active', 'accepted'):
            operation = 'complete'
        else:
            raise ValueError('Mission changed outside this job; stopped without retry')
        if name.startswith('bounty:') and operation != 'complete':
            raise ValueError('Bounty action only completes the existing active instance; refresh preview')
        if operation is None:
            raise ValueError('Mission is not eligible for this step')
        if native_graph and operation == 'complete':
            from . import mission_execution
            definition = mission_execution.DATA.get(name)
            if definition is None:
                raise RuntimeError('Authored mission graph is unavailable; no status shortcut issued')
            receipt = _job.setdefault('objective_runs', {}).setdefault(name, {})
            if state == 'accepted':
                since = receipt.setdefault('progress_at', time.monotonic())
                if time.monotonic() - since > 120:
                    return _defer(name,'Mission opening actions did not activate on its authored map; no acceptance repeated')
                _job.update(phase='complete', await_tick=True, message='Waiting for normal mission opening actions.')
                return status()
            mission_completion_context.expect_finish(sys.modules[__name__],name,row,definition)
            result = mission_execution.advance(engine, row, name, receipt, _journal,
                current_map=mission_completion_context.map_name(mission_completion_context.world()),
                before_outcome=lambda objective: mission_completion_context.objective_ready(
                    sys.modules[__name__],name,row,definition,objective))
            # The bounded poll loop may observe a synchronously finished graph
            # immediately. Its next fresh read will yield if actions still own
            # the objective; do not force a network roundtrip after every call.
            _job.update(phase='complete', await_tick=not result.get('issued',False), message=result['message'])
            return status()
        record, storage = int(row['record'], 16), int(row['storage'], 16)
        vt = engine.u64(record)
        if engine.u64(vt + 0xf8) != native_address(engine, 0xd80660) or engine.u64(vt + 0x110) != native_address(engine, 0x419fefa):
            raise RuntimeError('Mission callbacks differ from the reviewed build')
        if engine.u64(record + 0xa8) != storage or engine.read(storage, 1) == b'\0':
            raise RuntimeError('Mission storage is no longer valid')
        _journal(dict(event='issued', mission=name, operation=operation, before=row))
        issued = True
        if operation == 'reset':
            if native_graph:
                from . import mission_reset
                mission_reset.reopen(engine, row, _journal)
                _job.setdefault('objective_runs', {}).pop(name, None)
                _job.pop('activation_since', None)
                expected = ('locked', None, 'available', 'accepted', 'active')
            else:
                C.WINFUNCTYPE(None, C.c_void_p, C.c_uint8, C.c_bool)(native_address(engine, 0x3d32a5c))(storage, 2, False)
                expected = ('available',)
            next_phase = 'accept'
        elif operation == 'accept':
            import unrealsdk
            token = unrealsdk.make_struct('/Script/CoreUObject.SToken',
                Hash=struct.unpack('<i', bytes.fromhex(row['token'])[:4])[0], Name=name)
            if engine.read(token._get_address(), 12).hex() != row['token']:
                raise RuntimeError('Mission token mismatch')
            target.ServerActivateMission(token, 1, True, int(target.PlayerState.StableIndex))
            expected, next_phase = ('accepted', 'active', 'completed'), 'complete'
        else:
            C.WINFUNCTYPE(None, C.c_void_p, C.c_uint8, C.c_bool)(native_address(engine, 0xf19ee4))(record, 6, False)
            expected, next_phase = ('completed',), 'prepare'
        after = _row(engine.snapshot(), name)
        _journal(dict(event='returned', mission=name, operation=operation, after=after))
        if _state(after) not in expected:
            _job['failure'] = dict(mission=name, title=_metadata(name)['title'], operation=operation,
                                   observed=_state(after))
            raise RuntimeError(f'{_metadata(name)["title"]}: {operation} returned {_state(after)}; expected {", ".join(map(str, expected))}. Use Recover stopped job; no automatic retry.')
        _job['phase'] = next_phase
        if operation == 'complete':
            if _credit_completed(engine, party, name) is False:
                return status()
            _job['completed'].append(name)
            _job['index'] += 1
            if _job['index'] == len(_job['names']):
                _job['state'] = 'stopped' if _job.get('deferred') else 'completed'
        _job['message'] = f'{_metadata(name)["title"]}: {operation} verified in shared lobby'
    except Exception as exc:
        if hasattr(exc, 'receipt') and exc.__class__.__name__ == 'CreditPending':
            _job.update(challenge_pending=exc.receipt, phase='complete', state='running', message=str(exc))
            _journal(dict(event='state', state='running', index=_job['index'], message=str(exc)))
            return status()
        pending_campaign = _job.get('campaign_replay') and _job.get('state') == 'uncertain'
        pending_travel = _job.get('completion_context',{}).get('travel') and _job.get('state')=='uncertain'
        if _job.get('completion_context',{}).get('placement'):
            import sys
            from .mission_completion_placement import stop
            stop(sys.modules[__name__],str(exc),'stopped')
            return status()
        if (_job.get('continue_on_mission_failure') and not pending_campaign and not pending_travel
                and not _job.get('challenge_pending') and exc.__class__.__name__ != 'CreditUncertain'
                and _job.get('completion_path') == 'normal_acceptance'
                and 'name' in locals() and name == _job['names'][_job['index']]):
            try:
                if _binding(_party()) == _job['binding']:
                    return _quarantine_failed_mission(name,exc,issued,locals().get('operation'))
            except Exception:
                pass  # A changed or unreadable lobby is a global stop, not a skipped mission.
        _job.update(ok=False, state='uncertain' if issued or pending_campaign or pending_travel or getattr(exc, 'issued', False) else 'stopped', message=str(exc))
    _journal(dict(event='state', state=_job['state'], index=_job['index'], message=_job['message']))
    return status()


def _reopen_step(engine, row, name, target):
    """Reset once, then observe or accept; never complete the reopened mission."""
    from . import mission_reset
    phase, state = _job['phase'], _state(row)
    if phase == 'prepare':
        _journal(dict(event='issued', mission=name, operation='reopen', before=row))
        # Record the pending phase before native calls so an exception cannot
        # leave this job eligible to issue the reset a second time.
        _job.update(phase='reopen_wait', state='uncertain', ok=False)
        mission_reset.reopen(engine, row, _journal)
        after = _row(engine.snapshot(), name)
        _journal(dict(event='returned', mission=name, operation='reopen', after=after))
        _job.update(state='running', ok=True, reopen_since=time.monotonic())
        if _job.get('mode') == 'reset_completed':
            if _state(after) == 'completed':
                raise RuntimeError('Mission still reads completed after reset; no retry issued')
            _job['completed'].append(name)
            _job['index'] += 1
            _job['phase'] = 'prepare'
            if _job['index'] == _job['total']:
                _job['state'] = 'completed'
            _job['message'] = f'{_metadata(name)["title"]}: completed mission data reset. Eligible missions may activate again normally.'
    elif state == 'accepted' and _job.get('completion_path') == 'mission_replay':
        since = _job.setdefault('reopen_activation_since', time.monotonic())
        if time.monotonic() - since > 120:
            raise RuntimeError('Mission opening did not activate after reload; no reset or acceptance repeated')
        _job.update(await_tick=True, message='Mission area reloaded; waiting for its opening objectives to activate.')
    elif state in ('active', 'accepted'):
        _job.update(state='completed', index=1, completed=[name],
                    message=(f'{_metadata(name)["title"]}: reset and accepted; opening sequence is still pending. '
                             'If it does not start, save and quit, then reload this character.' if state == 'accepted' else
                             f'{_metadata(name)["title"]}: active again; verify its normal gameplay interactions. No completion call issued.'))
    elif state == 'available':
        import unrealsdk
        token = unrealsdk.make_struct('/Script/CoreUObject.SToken',
            Hash=struct.unpack('<i', bytes.fromhex(row['token'])[:4])[0], Name=name)
        if engine.read(token._get_address(), 12).hex() != row['token']:
            raise RuntimeError('Mission token mismatch')
        if _job.get('reopen_accept_issued'):
            raise RuntimeError('Reopen acceptance is unconfirmed; inspect status before retrying')
        _job['reopen_accept_issued'] = True
        _journal(dict(event='issued', mission=name, operation='reopen_accept', before=row))
        target.ServerActivateMission(token, 1, True, int(target.PlayerState.StableIndex))
        _journal(dict(event='returned', mission=name, operation='reopen_accept', after=_row(engine.snapshot(), name)))
    elif state == 'locked' and time.monotonic() - _job['reopen_since'] < 10:
        _job['message'] = 'Mission reset; waiting for its normal prerequisite update'
    else:
        _job.update(ok=False, state='stopped',
                    message=f'{_metadata(name)["title"]}: reset returned {state}; normal mission availability is still required')
    _journal(dict(event='state', state=_job['state'], index=_job['index']))
    return status()


def resume(job_id):
    """Only recover a stopped job whose pending completion is already confirmed."""
    if not _job or job_id != _job['id']:
        raise ValueError('Mission job identifier changed')
    if _job.get('completion_path') in ('objective_graph', 'mission_replay'):
        import sys
        from .mission_completion_context import observe
        if not observe(sys.modules[__name__]):return status()
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
    activation_wait = _job.get('activation_wait', {}).get('mission') == _job['names'][_job['index']]
    graph_run = _job.get('completion_path') == 'objective_graph'
    allowed = ('accepted', 'active', 'completed') if _job['phase'] == 'accept' else ('active', 'completed') if activation_wait or graph_run else ('completed',)
    if graph_run and any(r.get('pending') for r in _job.get('objective_runs', {}).values()):
        raise ValueError('An objective has no return receipt; recover it before continuing')
    if _state(row) not in allowed:
        raise ValueError('Pending mission is not confirmed completed or naturally activated for this phase; no retry issued')
    if graph_run:
        receipt = _job.get('objective_runs', {}).get(_job['names'][_job['index']])
        if receipt is not None:
            receipt['progress_at'] = time.monotonic()
    _job.update(ok=True, state='running', message='Confirmed forward game progression; ready to continue remaining missions')
    _journal(dict(event='resume', state='running', index=_job['index'], observed=row))
    return status()


def _recover_campaign(payload, events, path, live, job_id, issued):
    """Inspect a returned campaign reset without issuing any game calls again."""
    call = events[issued]
    if not any(e.get('event') == 'campaign_reset_returned' for e in events[issued + 1:]):
        raise ValueError('Campaign reset has no durable return receipt; its outcome still needs inspection')
    names = call.get('missions', [])
    if not names or len(names) != len(set(names)):
        raise ValueError('Campaign reset receipt has no unambiguous mission inventory')
    snapshot = _engine().snapshot()
    states = {}
    for name in names:
        row = _row(snapshot, name)
        if name in call.get('tokens', {}) and row['token'] != call['tokens'][name]:
            raise ValueError('Campaign mission identity differs from the reset receipt: ' + name)
        states[name] = _state(row)
    remaining = [dict(name=name, title=CATALOG.get(name, {}).get('title', name), state=state)
                 for name, state in states.items() if state == 'completed']
    report = dict(ok=True, id=job_id, operation='campaign_reset',
                  observed=states, remaining_completed=remaining,
                  message=f'Current lobby inspected: {len(remaining)} of {len(states)} named records '
                          'still read completed. No reset repeated; world-state replay is not verified.')
    mode = payload.get('mode', 'inspect')
    if mode == 'inspect':
        return report
    if mode not in ('continue', 'close') or payload.get('acknowledge_shared_progress') is not True:
        raise ValueError('Choose continue or close and acknowledge shared progress')
    if mode == 'continue':
        if live and _job.get('closed'):
            raise ValueError('This reset job is already closed; refresh the mission preview')
        if not live:
            raise ValueError('Recovered after restart: close this inspected reset job before starting another')
        # Only the verification phase resumes. The native reset is never replayed.
        _job.update(ok=True, state='running', phase='campaign_verify',
                    message='Rechecking the returned reset without repeating any game changes')
        _journal(dict(event='recovered', state='running', report=report))
        return status()
    message = report['message'] + ' Reset job closed; unresolved progress was retained.'
    event = dict(event='recovered', state='stopped', report=report, time=time.time())
    with path.open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(event) + '\n'); stream.flush(); os.fsync(stream.fileno())
    if live:
        _job.update(ok=True, state='stopped', closed=True, message=message, remaining_completed=remaining)
    return dict(report, state='stopped', closed=True, message=message)


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
    if (live and payload.get('mode')=='close' and _job.get('continue_on_mission_failure')
            and _job.get('completion_path')=='normal_acceptance'):
        if payload.get('acknowledge_shared_progress') is not True:
            raise ValueError('Acknowledge shared progress before closing this run')
        if _job.get('challenge_pending') or _job.get('completion_context',{}).get('travel'):
            raise ValueError('An issued operation is still settling; inspect it before closing')
        report=dict(operation='full_run_abandoned',mission=(
            _job['names'][_job['index']] if _job['index']<len(_job['names']) else None),
            observed='unverified_without_retry')
        event=dict(event='recovered',state='stopped',closed=True,report=report,time=time.time())
        with path.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(event)+'\n');stream.flush();os.fsync(stream.fileno())
        _job.update(ok=True,state='stopped',closed=True,
                    message='Run closed; applied progress retained and uncertain work not repeated')
        return dict(ok=True,state='stopped',closed=True,id=job_id,report=report,
                    message=_job['message'])
    if live and _job.get('completion_path') in ('objective_graph', 'mission_replay'):
        import sys
        from . import mission_completion_context
        result=mission_completion_context.recover(sys.modules[__name__],payload,events,live,path)
        if result is not None:return result
        if not mission_completion_context.observe(sys.modules[__name__]):return status()
    elif any(e.get('event')=='completion_map_issued' for e in events):
        import sys
        from . import mission_completion_context
        result=mission_completion_context.recover(sys.modules[__name__],payload,events,live,path)
        if result is not None:return result
    if any(e.get('campaign_replay') for e in events):
        import sys
        from . import campaign_replay
        return campaign_replay.recover(sys.modules[__name__], payload, events, live, path)
    campaign = next((i for i in range(len(events)-1, -1, -1)
                     if events[i].get('event') == 'campaign_reset_issued'), None)
    if campaign is not None:
        return _recover_campaign(payload, events, path, live, job_id, campaign)
    if not live and payload.get('mode')=='close':
        if payload.get('acknowledge_shared_progress') is not True:
            raise ValueError('Acknowledge shared progress before closing this interrupted run')
        last=next((e for e in reversed(events) if e.get('event')=='issued'),{})
        operation,name=last.get('operation'),last.get('mission')
        observed='unverified_after_reload' if operation else 'no_issued_call_found'
        report=dict(operation=operation,mission=name,observed=observed)
        event=dict(event='recovered',state='stopped',closed=True,report=report,time=time.time())
        with path.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(event)+'\n');stream.flush();os.fsync(stream.fileno())
        return dict(ok=True,state='stopped',closed=True,id=job_id,report=report,
                    message='Interrupted mission run closed without repeating or verifying old calls. Applied progress retained.')
    issued = next((i for i in range(len(events)-1, -1, -1) if events[i].get('event') == 'issued'), None)
    if issued is None:
        raise ValueError('No recorded mission call to reconcile')
    call = events[issued]
    name, operation = call.get('mission'), call.get('operation')
    returned = next((e for e in events[issued+1:] if e.get('event') == 'returned'
                     and e.get('operation') == operation and e.get('mission') == name), None)
    if returned is None and payload.get('mode') == 'close':
        if payload.get('acknowledge_shared_progress') is not True:
            raise ValueError('Acknowledge shared progress before closing this interrupted run')
        # Closing is receipt-only. It never infers that an unreturned call worked,
        # and it makes an interrupted run restartable without repeating the call.
        report = dict(operation=operation, mission=name, observed=(
            'unverified_after_reload' if not live and operation=='objective_complete'
            else 'unverified_unreturned_call'))
        event = dict(event='recovered', state='stopped', closed=True, report=report, time=time.time())
        with path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(event) + '\n'); stream.flush(); os.fsync(stream.fileno())
        if live:
            _job.update(ok=True,state='stopped',closed=True,
                        message='Unreturned operation retained as unverified; job closed without retry')
        return dict(ok=True, state='stopped', closed=True, id=job_id, report=report,
                    message='Interrupted operation closed without verifying completion or repeating calls. '
                            'Applied progress is retained. Refresh preview before starting another run.')
    if returned is None and live and _job.get('continue_on_mission_failure') and name in CATALOG:
        mode=payload.get('mode','inspect')
        if mode not in ('inspect','continue'):
            raise ValueError('Choose inspect, continue, or close')
        if _job['names'][_job['index']] != name or _binding(_party()) != _job['binding']:
            raise ValueError('Original mission or lobby changed; close this run before restarting')
        observed=None
        read_error=None
        if operation == 'safehouse_claim' and call.get('address'):
            try:
                from . import mission_effects
                host=next(r['pc'] for r in _party() if r['host'])
                observed=mission_effects.inspect_safehouse_claim(host,name,call['address'])
            except Exception as exc:
                read_error=str(exc)[:500]
        report=dict(ok=True,id=job_id,mission=name,operation=operation,
                    observed=observed['state'] if observed else 'unverified',
                    channel=observed['channel'] if observed else None,read_error=read_error)
        if mode=='inspect':return report
        if payload.get('acknowledge_shared_progress') is not True:
            raise ValueError('Acknowledge shared progress before continuing')
        _job.update(ok=True,state='running')
        if observed and observed['state'].casefold()=='claimed':
            _job['phase']='complete'
            _journal(dict(event='recovered',state='running',report=report))
            return status()
        error=RuntimeError('Issued '+str(operation)+' has no return receipt; no call repeated')
        if operation=='safehouse_claim' and call.get('address'):
            error.address=call['address']
        result=_quarantine_failed_mission(name,error,True,operation)
        return result
    if operation == 'challenge_credit':
        from . import mission_challenges
        returned = next((e for e in events[issued+1:] if e.get('event') == 'returned'
                         and e.get('operation') == operation and e.get('mission') == name), None)
        if returned is None:
            raise ValueError('Challenge call has no durable return receipt; inspect before retry')
        receipt = {k: v for k, v in call.items() if k not in ('event', 'time', 'job_id')}
        mission_challenges.reconcile(_engine(), _party(), receipt, lambda event: None)
        report = dict(ok=True, mission=name, title=_metadata(name)['title'], operation=operation,
                      observed='completed', acceptance_unchanged=False, access=None)
        state = 'completed'
    else:
        if name not in CATALOG or operation not in ('reset', 'accept', 'complete', 'reopen', 'reopen_accept', 'objective_complete'):
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
        if operation in ('reopen','reopen_accept'):
            safe = state in ('locked','available','accepted','active')
        if operation == 'objective_complete':
            from .mission_objectives import read
            objective = call['objective']
            observed = next((o for o in read(engine, current) if o['token'] == objective['token']), None)
            safe = (observed is not None and observed['state'] == 13) or (observed is None and state == 'completed')
        if not safe:
            raise ValueError(f'{_metadata(name)["title"]}: {operation} still unresolved ({state}); no retry or clearance issued')
        report = dict(ok=True, mission=name, title=_metadata(name)['title'], operation=operation, observed=state,
                      acceptance_unchanged=operation == 'accept' and state == 'available', access=_dlc_requirement(name))
    mode = payload.get('mode', 'inspect')
    if mode == 'inspect':
        return dict(report, message=f'{report["title"]}: {operation} reconciled as {state}; no game changes made.')
    if mode not in ('continue', 'close') or payload.get('acknowledge_shared_progress') is not True:
        raise ValueError('Choose continue or close and acknowledge shared progress')
    if not live and mode != 'close':
        raise ValueError('Recovered after restart: close the reconciled job, then preview a new batch')
    if mode == 'continue' and _job and _job.get('mode') == 'reset_completed':
        raise ValueError('Close this reconciled reset job, then preview remaining completed missions')
    if mode == 'close':
        event = dict(event='recovered', state='stopped', report=report, time=time.time())
        with path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(event) + '\n'); stream.flush(); os.fsync(stream.fileno())
        if live:
            _job.pop('challenge_pending', None)
            _job.pop('cancel_requested', None)
            _job.update(ok=True, state='stopped', closed=True, message=f'{report["title"]}: reconciled as {state}. Job closed; previous progress retained.')
        return dict(ok=True, state='stopped', closed=True, id=job_id, message=f'{report["title"]}: reconciled as {state}. Job closed; previous progress retained. Refresh preview for a new run.')
    party = _party()
    if _job.get('preserve_completed') and len(party) != 1:
        raise ValueError('Solo completion cannot resume with guests; close and preview a new job')
    if _binding(party) != _job['binding']:
        from . import farming_targets
        selected = farming_targets.resolve(payload)
        if len(selected) != 1:
            raise ValueError('Select one currently loaded acceptance player')
        _job['binding'], _job['target'] = _binding(party), selected[0]['pc']._path_name()
    _job.pop('challenge_pending', None)
    _job.pop('cancel_requested', None)
    if operation == 'objective_complete':
        receipt = _job.setdefault('objective_runs', {}).setdefault(name, dict(token=current['token'], issued=[]))
        if objective['token'] not in receipt['issued']:
            receipt['issued'].append(objective['token'])
        receipt.pop('pending', None)
        receipt['progress_at'] = time.monotonic()
    _job.update(ok=True, state='running', stall_since=None)
    _journal(dict(event='recovered', report=report, state='running', binding=_job['binding'], target=_job['target']))
    if report['acceptance_unchanged']:
        return _defer(name, 'Acceptance returned unchanged; skipped without retry.', report['access'])
    _job['phase'] = 'accept' if operation == 'reset' and state == 'available' else 'complete'
    if operation in ('reopen','reopen_accept'):
        _job['phase'] = 'reopen_wait'
    _job['message'] = report['title'] + ': reconciled; continuing without repeating the recorded call.'
    return status()


def cancel(job_id):
    if not _job or job_id != _job['id']:
        raise ValueError('Mission job identifier changed')
    if _job.get('completion_context',{}).get('placement'):
        import sys
        from .mission_completion_placement import stop
        stop(sys.modules[__name__],retry=True)
        return status()
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


def poll(job_id):
    """Shared scoped/full-run pump: normal transitions and credit checks."""
    if not _job or _job['id'] != job_id:
        raise ValueError('Mission job identifier changed')
    # Let authored dialogue finish: stopping its audio can strand PlayMoment
    # finish actions, even though the objective already reads "completed".
    deadline = time.monotonic() + 0.020
    for _ in range(16):
        result = step(job_id)
        if result.get('state') != 'running' or _job.get('await_tick') or time.monotonic() >= deadline:
            break
    return result


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
            return poll(payload.get('job_id'))
        if action == 'mission_resume':
            return resume(payload.get('job_id'))
        if action == 'mission_cancel':
            return cancel(payload.get('job_id'))
        raise ValueError('Unknown mission action')
    except Exception as exc:
        return dict(ok=False, message=str(exc))
