"""Campaign reset across map loads, using normal station travel and acceptance.

Evidence: docs/changes/2026-10-12-campaign-reset.md. Loaded World_P actors can
restore completed activity state. Clear that residue after unloading World_P.
Never retain native record pointers across travel or repeat an uncertain call.
"""
import copy
import json
import struct
import time

WORLD = '/Game/Maps/WorldLevels/World_P.World_P'
INTRO = '/Game/Maps/WorldLevels/Intro/Intro_P.Intro_P'
FIRST = 'Mission_Main_PrisonPrologue'


def roster(rows):
    return sorted((r['label'], int(r['state'].PlayerId), bool(r['host'])) for r in rows)


def world():
    from mods_base import ENGINE
    return getattr(getattr(ENGINE, 'GameViewport', None), 'World', None)


def travel(owner, destination, next_phase, rows):
    from . import travel as stations
    job = owner._job
    w = world()
    job.update(phase='campaign_travel', travel_from=w._get_address(),
               travel_destination=destination, travel_next=next_phase,
               travel_roster=roster(rows), travel_since=time.monotonic(),
               state='uncertain', ok=False)
    owner._journal(dict(event='campaign_travel_issued', destination=destination,
                        next_phase=next_phase, roster=job['travel_roster']))
    stations.travel_to_station('Intro_P.Respawn' if destination == INTRO else 'World_P.Game_Start')
    owner._journal(dict(event='campaign_travel_returned', destination=destination))
    job.update(state='running', ok=True, message='Loading the campaign opening map; no mission calls repeated')


def finish_travel(owner):
    job = owner._job
    if time.monotonic() - job['travel_since'] > 360:
        raise RuntimeError('Campaign travel has not finished; inspect the map before continuing')
    w = world()
    if w is None or w._get_address() == job['travel_from']:
        return False
    if w._path_name() != job['travel_destination']:
        raise RuntimeError('Campaign reset reached an unexpected map')
    from mods_base import get_pc
    pc = get_pc()
    if pc is None or pc.Pawn is None or not pc._path_name().startswith(w._path_name() + ':'):
        return False
    rows = owner._party()
    if roster(rows) != job['travel_roster']:
        raise RuntimeError('Players changed during campaign reset travel')
    # The runtime stores only build/name metadata and its world binding. snapshot
    # locates the current shard and records afresh; no old pointer is reused.
    owner._runtime = copy.copy(owner._runtime)
    owner._runtime.world_address = None
    owner._runtime.ensure_world()
    job.update(binding=owner._binding(rows),
               target=next(r['pc']._path_name() for r in rows if r['host']),
               phase=job['travel_next'])
    owner._journal(dict(event='campaign_travel_verified', destination=w._path_name(), phase=job['phase']))
    return True


def reset(owner, engine, snapshot, names, event):
    from . import mission_reset
    job = owner._job
    rows = [owner._row(snapshot, name) for name in names]
    rows = [r for r in rows if owner._state(r) in ('accepted', 'active', 'completed', 'failed', 'available', 'locked')]
    job.update(state='uncertain', ok=False)
    owner._journal(dict(event=event + '_issued', missions=names,
                        tokens={n: owner._row(snapshot, n)['token'] for n in names}))
    mission_reset.reset_campaign(engine, rows, owner._journal)
    owner._journal(dict(event=event + '_returned'))
    job.update(state='running', ok=True)


def step(owner):
    job = owner._job
    if job['phase'] == 'campaign_travel' and not finish_travel(owner):
        return
    engine = owner._engine()
    snapshot = engine.snapshot()
    rows = owner._party()
    if owner._binding(rows) != job['binding']:
        raise RuntimeError('Party changed; campaign reset stopped')
    host = next(r['pc'] for r in rows if r['host'])
    phase = job['phase']
    if phase == 'prepare':
        if world()._path_name() == INTRO:
            # Unload an already-running prologue before clearing it, too.
            travel(owner, WORLD, 'prepare', rows)
            return
        reset(owner, engine, snapshot, job['names'], 'campaign_reset')
        job['phase'] = 'campaign_depart'
        return
    if phase == 'campaign_depart':
        travel(owner, INTRO, 'campaign_residue', rows)
        return
    if phase == 'campaign_residue':
        remaining = [n for n in job['names'] if owner._state(owner._row(snapshot, n)) == 'completed']
        if FIRST in remaining:
            raise RuntimeError('Prologue unexpectedly completed during reset travel')
        job['phase'] = 'campaign_opening'
        job['opening_since'] = time.monotonic()
        if remaining:
            reset(owner, engine, snapshot, remaining, 'campaign_residue_reset')
        return
    if phase != 'campaign_opening':
        raise RuntimeError('Unknown campaign replay phase')
    states = {n: owner._state(owner._row(snapshot, n)) for n in job['names']}
    job['remaining_completed'] = [dict(name=n, title=owner.CATALOG.get(n, {}).get('title', n), state=s)
                                  for n, s in states.items() if s == 'completed']
    if job['remaining_completed']:
        raise RuntimeError('Completed mission state returned after map reload; inspect reset receipt')
    later = [n for n, s in states.items() if n != FIRST and s in ('accepted', 'active')
             and owner.CATALOG.get(n, {}).get('category') == 'story']
    if later:
        raise RuntimeError('Later story missions activated: ' + ', '.join(later))
    current = states.get(FIRST)
    if current == 'available' and not job.get('opening_accept_issued'):
        import unrealsdk
        row = owner._row(snapshot, FIRST)
        token = unrealsdk.make_struct('/Script/CoreUObject.SToken',
            Hash=struct.unpack('<i', bytes.fromhex(row['token'])[:4])[0], Name=FIRST)
        if engine.read(token._get_address(), 12).hex() != row['token']:
            raise RuntimeError('Prologue token identity changed')
        job.update(opening_accept_issued=True, state='uncertain', ok=False)
        owner._journal(dict(event='campaign_opening_accept_issued', mission=FIRST))
        host.ServerActivateMission(token, 1, True, int(host.PlayerState.StableIndex))
        owner._journal(dict(event='campaign_opening_accept_returned', mission=FIRST))
        job.update(state='running', ok=True)
        return
    if current == 'active':
        job.update(state='completed', index=len(states), completed=list(states),
                   message='Mission reset finished: 0 named missions completed. Guns Blazing is active at the opening. '
                           'Equipment, levels, discoveries and other non-mission progress are retained.')
        owner._journal(dict(event='state', state='completed', index=job['index'], observed=states))
    elif time.monotonic() - job['opening_since'] > 360:
        raise RuntimeError('Opening mission has not activated; inspect the opening sequence')
    else:
        job['message'] = 'Mission data reset; waiting for the normal Guns Blazing opening'


def recover(owner, payload, events, live, path):
    """Resume observation, never replay a native reset with an unknown outcome."""
    mode = payload.get('mode', 'inspect')
    if mode not in ('inspect', 'continue', 'close'):
        raise ValueError('Unknown campaign recovery mode')
    if mode != 'inspect' and payload.get('acknowledge_shared_progress') is not True:
        raise ValueError('Acknowledge shared progress before recovery')
    if mode == 'close':
        message = 'Campaign reset closed with partial results; no game calls issued. The opening sequence may be unfinished.'
        if live:
            owner._job.update(state='stopped', closed=True, ok=False, message=message)
            owner._journal(dict(event='campaign_recovery', mode=mode, state='stopped', closed=True))
            return owner.status()
        with path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps(dict(event='campaign_recovery', mode=mode, state='stopped', closed=True, time=time.time())) + '\n')
        return dict(ok=False, id=payload['job_id'], state='stopped', closed=True, message=message)
    if not live:
        if mode == 'inspect':
            return dict(ok=False, id=payload['job_id'], state='stopped',
                        message='Campaign reset was interrupted by a runtime reload. Its receipt is retained; close it after inspecting the character. No calls repeated.')
        raise ValueError('Campaign replay cannot resume after a runtime reload; inspect and close its retained receipt')
    job = owner._job
    pending = None
    for event in events:
        name = event.get('event', '')
        if name.startswith('campaign_') and name.endswith('_issued') and name not in ('campaign_group_issued', 'campaign_record_issued'):
            pending = name[:-7]
        elif pending and name == pending + '_returned':
            pending = None
    if pending:
        raise ValueError('Campaign operation has no return receipt; no reset, acceptance or travel repeated: ' + pending)
    if job['phase'] == 'campaign_travel' and not finish_travel(owner):
        return dict(owner.status(), message='Campaign map is still loading; no travel repeated')
    snapshot = owner._engine().snapshot()
    remaining = [n for n in job['names'] if owner._state(owner._row(snapshot, n)) == 'completed']
    if mode == 'continue':
        job.update(state='running', ok=True, message='Continuing from the recorded campaign phase; completed reset steps will not repeat')
    report = dict(owner.status(), remaining_completed=remaining)
    owner._journal(dict(event='campaign_recovery', mode=mode, state=job['state'], phase=job['phase']))
    return report
