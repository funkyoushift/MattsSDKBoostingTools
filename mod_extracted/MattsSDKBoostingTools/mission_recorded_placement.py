"""Place at a recorded grounded beginning without changing native movement."""
import math
import time


def preflight(job, rows):
    from . import mission_practice_placement as p
    point = {k.upper(): float(v) for k, v in job['anchor']['location'].items()}
    if set(point) != {'X', 'Y', 'Z'} or not all(math.isfinite(v) for v in point.values()):
        raise RuntimeError('Recorded mission location is invalid')
    if job.get('ground_to_waypoint') and len(rows) != 1:
        raise RuntimeError('Waypoint replay placement requires the solo host')
    records = []
    # Validate everyone before the first request. An unloaded or obstructed
    # coordinate never invokes the legacy streaming/movement hold.
    for row in rows:
        pawn = row['pc'].Pawn
        move = pawn.CharacterMovement
        if move is None or int(move.MovementMode) not in (1, 3):
            raise RuntimeError('Stand on foot before using a recorded mission location')
        if not math.isfinite(float(move.GravityScale)):
            raise RuntimeError('Player gravity is unavailable; no placement issued')
        if job.get('ground_to_waypoint'):
            # Source markers can be above the floor. Query loaded collision
            # below the marker; never move/hold the pawn to load geometry.
            marker = point
            point = p._grounded_probe(pawn, move, marker)
            if point is None:
                # Authored actor origins can also lie inside the floor/object.
                # Raise the query origin by this pawn's measured capsule height,
                # then require the same native line and capsule fit checks.
                raised = dict(marker)
                raised['Z'] += 2. * float(pawn.CapsuleComponent.GetScaledCapsuleHalfHeight())
                point = p._grounded_probe(pawn, move, raised)
            if point is None:
                raise RuntimeError('Recorded location is not loaded or cannot fit this player. Native station retained.')
        floor = p._floor(pawn, move, point, 50.)
        if not p._usable(floor) or not 0. <= p._distance(floor) <= 15.:
            raise RuntimeError('Recorded location is not loaded or cannot fit this player. Follow the mission waypoint; no movement hold applied.')
        records.append((row, pawn))
    if not records:
        raise RuntimeError('No players are loaded for recorded placement')
    return point, records


def start(job, rows, journal):
    from . import mission_practice_placement as p
    point, records = preflight(job, rows)
    job['anchor'] = dict(job['anchor'], location={k.lower(): v for k, v in point.items()})
    job.update(phase='recorded_verify', state='uncertain', ok=False,
               recorded_placement=[], recorded_verify_since=time.monotonic())
    for row, pawn in records:
        move = pawn.CharacterMovement
        record = dict(controller=row['pc']._path_name(), pawn=pawn._get_address(), returned=False,
                      pawn_path=pawn._path_name(), movement=move._get_address(),
                      gravity=float(move.GravityScale), mode=int(move.MovementMode), custom=int(move.CustomMovementMode))
        if not math.isfinite(record['gravity']):
            raise RuntimeError('Player gravity is unavailable; no placement issued')
        job['recorded_placement'].append(record)
        journal(dict(event='recorded_placement_issued', **record))
        try:
            if not pawn.K2_TeleportTo(p._vector(point), pawn.K2_GetActorRotation()):
                raise RuntimeError('Native placement rejected the recorded point. Applied placements remain; no retry issued.')
        finally:
            # BL4 refreshes movement synchronously even when teleport rejects
            # the location. Restore the captured settings without a flying hold.
            current = row['pc'].Pawn
            if current is None or current._get_address() != record['pawn'] or current.CharacterMovement._get_address() != record['movement']:
                raise RuntimeError('Player changed during recorded placement; movement restoration needs inspection')
            move = current.CharacterMovement
            move.SetMovementMode(record['mode'], record['custom'])
            move.GravityScale = record['gravity']
            if (int(move.MovementMode), int(move.CustomMovementMode), float(move.GravityScale)) != (record['mode'], record['custom'], record['gravity']):
                raise RuntimeError('Movement restoration is unconfirmed; inspect before retrying')
            journal(dict(event='recorded_movement_restored', player=record['controller']))
        record['returned'] = True
        journal(dict(event='recorded_placement_returned', **record))
    job.update(state='running', ok=True, message='Checking normal movement at the recorded beginning.')


def verify(job, rows):
    from . import mission_practice_placement as p
    if time.monotonic() - job['recorded_verify_since'] < .5:
        return False
    point = {k.upper(): float(v) for k, v in job['anchor']['location'].items()}
    by_path = {r['pc']._path_name(): r for r in rows}
    for record in job['recorded_placement']:
        row = by_path.get(record['controller'])
        if row is None or not record['returned'] or row['pc'].Pawn._get_address() != record['pawn']:
            raise RuntimeError('Players changed during recorded placement; no retry issued')
        pawn = row['pc'].Pawn
        actual = p._point(pawn.K2_GetActorLocation())
        if sum((actual[k] - point[k]) ** 2 for k in point) > 150. ** 2:
            raise RuntimeError('Recorded placement moved outside its starting area; inspect before retrying')
    if p.players_grounded(rows):
        return True
    if time.monotonic() - job['recorded_verify_since'] > 10.:
        raise RuntimeError('Normal movement at the recorded beginning is unconfirmed')
    return False
