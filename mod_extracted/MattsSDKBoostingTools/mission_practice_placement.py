"""Bounded practice placement with collision readback and reversible movement hold.

Authored encounter/interaction waypoints are not necessarily standing surfaces.
Practice searches directly below its waypoint, within 50 m. Encounter scene
loading can instead use BL4's native navigation projection within the encounter
radius. A short independent watchdog restores temporary settings even when the
desktop stops polling. See the 2026-10-13 completion verification change note.
"""
import math
import time

HOOK = '/Script/Engine.CameraModifier:BlueprintModifyCamera'
IDENT = 'msbt_practice_placement_v1'
MAX_FLOOR_DISTANCE = 5000.
_active = None


def _vector(value):
    import unrealsdk
    return unrealsdk.make_struct('/Script/CoreUObject.Vector', **value)


def _point(value):
    return {key: float(getattr(value, key)) for key in ('X', 'Y', 'Z')}


def _frame():
    from .vault_card_challenges import _frame as frame
    return frame()


def _context(record):
    import unrealsdk
    # Resolve independently: one unpossessed guest must not prevent restoring
    # every other player. The ordinary party validator requires all pawns ready.
    pc = unrealsdk.find_object('OakPlayerController', record['controller'])
    if pc is None:
        raise RuntimeError('Practice player left during placement')
    pawn = pc.Pawn
    if pawn is None or pawn._get_address() != record['pawn'] or pawn._path_name() != record['pawn_path']:
        raise RuntimeError('Practice player respawned during placement')
    move = pawn.CharacterMovement
    if move is None or move._get_address() != record['movement']:
        raise RuntimeError('Practice movement component changed')
    return pawn, move


def _event(event, **fields):
    try:
        _active['journal'](dict(event=event, **fields))
    except Exception as exc:
        if not _active.get('emergency'):
            raise
        # Cleanup cannot depend on disk availability. This mode can only end
        # uncertain, and never sends another forward placement request.
        _active['job']['placement_journal_error'] = str(exc)


def _restore(record, pawn, move):
    # Record intent first; retries restore captured values, never hardcoded defaults.
    record['restore_pending'] = True
    journal_error = None
    try:
        _event('placement_restore_issued', player=record['label'])
    except Exception as exc:
        journal_error = exc
    move.GravityScale = record['gravity']
    move.SetMovementMode(record['mode'], record['custom'])
    if (float(move.GravityScale) != record['gravity'] or int(move.MovementMode) != record['mode']
            or int(move.CustomMovementMode) != record['custom']):
        raise RuntimeError('Practice movement restoration is unconfirmed')
    record.update(restore_pending=False, held=False)
    if journal_error is not None:
        raise RuntimeError('Movement restored, but its journal could not be saved') from journal_error
    _event('placement_restore_returned', player=record['label'])


def _floor(pawn, move, point, distance):
    import unrealsdk
    return move.K2_ComputeFloorDist(
        _vector(point), distance, distance, float(pawn.CapsuleComponent.GetScaledCapsuleRadius()),
        unrealsdk.make_struct('/Script/Engine.FindFloorResult'))[1]


def _usable(floor):
    return bool(floor.bBlockingHit and floor.bWalkableFloor and not floor.HitResult.bStartPenetrating)


def _distance(floor):
    # BL4 can return a valid line floor while the capsule sweep distance remains
    # negative (observed at Abandoned Post's authored datapad). Use the successful
    # query's distance; the hit flags still gate every placement.
    return float(floor.LineDist if getattr(floor,'bLineTrace',False) else floor.FloorDist)


def _grounded_probe(pawn, move, point):
    """Use loaded geometry below the waypoint before raising an indoor probe.

    A waypoint can be above an NPC or just below a ceiling. The narrow native
    line query supplies only a candidate; the player's capsule floor query must
    also confirm that it fits on walkable support. Unloaded geometry falls back
    to the existing held streaming probe, never a guessed neighbouring point.
    """
    import unrealsdk
    from .mission_completion_placement import _same_world
    lib=unrealsdk.find_object('KismetSystemLibrary','/Script/Engine.Default__KismetSystemLibrary')
    if lib is None:return None
    level=pawn.GetLevel()
    world=getattr(level,'OwningWorld',None) if level is not None else None
    if world is None:return None
    ignored=[actor for actor in unrealsdk.find_all('OakCharacter',exact=False)
             if _same_world(actor,world)]
    end=dict(point);end['Z']-=MAX_FLOOR_DISTANCE
    color=unrealsdk.make_struct('/Script/CoreUObject.LinearColor')
    result=lib.LineTraceSingle(WorldContextObject=pawn,Start=_vector(point),End=_vector(end),
        TraceChannel=0,bTraceComplex=False,ActorsToIgnore=ignored,DrawDebugType=0,
        OutHit=unrealsdk.make_struct('/Script/Engine.HitResult'),bIgnoreSelf=True,
        TraceColor=color,TraceHitColor=color,DrawTime=0.)
    if not result[0]:return None
    hit=result[2]
    if not hit.bBlockingHit or hit.bStartPenetrating:return None
    surface=_point(hit.ImpactPoint)
    if (not all(math.isfinite(v) for v in surface.values()) or
            not 0. <= point['Z']-surface['Z'] <= MAX_FLOOR_DISTANCE or
            abs(surface['X']-point['X'])>1. or abs(surface['Y']-point['Y'])>1.):return None
    standing=dict(point);standing['Z']=surface['Z']+float(pawn.CapsuleComponent.GetScaledCapsuleHalfHeight())+3.
    floor=_floor(pawn,move,standing,50.)
    if not _usable(floor) or not 0. <= _distance(floor) <= 15.:return None
    return standing


def _hold(record):
    pawn, move = _context(record)
    record['held'] = True
    move.StopMovementImmediately()
    move.SetMovementMode(5, 0)
    move.GravityScale = 0.
    return pawn, move


def _navigation_probe(pawn, move, scene):
    from .mission_completion_placement import navigation_point
    surface=navigation_point(pawn,scene)
    if surface is None:return None
    standing=dict(surface)
    standing['Z']+=float(pawn.CapsuleComponent.GetScaledCapsuleHalfHeight())+3.
    floor=_floor(pawn,move,standing,50.)
    if not _usable(floor):return None
    distance=_distance(floor)
    if not math.isfinite(distance) or abs(distance)>50.:return None
    if not 0. <= distance <= 15.:
        # Navigation polygons approximate the collision surface. At the native
        # entrance point the walkable capsule sweep returned -8.175cm without
        # penetration. Correct only its measured vertical offset, then require
        # a fresh supported capsule result; never accept a negative landing.
        standing['Z']+=3.-distance
        floor=_floor(pawn,move,standing,50.)
    if not _usable(floor) or not 0. <= _distance(floor) <= 15.:return None
    return standing


def _maintain_hold(record, target):
    """Keep our bounded hold through native movement refreshes after streaming."""
    pawn, move = _context(record)
    actual = _point(pawn.K2_GetActorLocation())
    if (not all(math.isfinite(v) for v in actual.values()) or
            sum((actual[k]-target[k])**2 for k in actual) > 150.**2):
        raise RuntimeError('Player moved outside the protected placement area')
    gravity = float(move.GravityScale)
    mode, custom = int(move.MovementMode), int(move.CustomMovementMode)
    if not math.isfinite(gravity):raise RuntimeError('Temporary movement state is unavailable')
    if abs(gravity) > .0001 or mode != 5 or custom != 0:
        _event('placement_hold_refreshed', player=record['label'], gravity=gravity,
               mode=mode, custom=custom, location=actual)
        pawn, move = _hold(record)
    return pawn, move


def _teleport_held(record, point):
    pawn, move = _hold(record)
    try:
        actual=_point(pawn.K2_GetActorLocation())
        if sum((actual[k]-point[k])**2 for k in point)<=1.:
            floor=_floor(pawn,move,actual,50.)
            if _usable(floor) and -3. <= _distance(floor) <= 15.:
                _event('placement_teleport_unneeded',player=record['label'],location=actual)
                return True,float(move.GravityScale)
        result = pawn.K2_TeleportTo(_vector(point), pawn.K2_GetActorRotation())
        pawn, move = _context(record)
        gravity_after = float(move.GravityScale)
        return result, gravity_after
    finally:
        # Native teleport refreshes movement synchronously, even on failure.
        # Re-resolve the same player before reasserting our hold, within this
        # call, including rollback and landing. Never touch a replacement pawn.
        _hold(record)


def players_grounded(rows):
    """Possession alone precedes the end of map loading in BL4."""
    for row in rows:
        pawn=row['pc'].Pawn
        if pawn is None:return False
        move=pawn.CharacterMovement
        if move is None or int(move.MovementMode) not in (1,3):return False
        floor=_floor(pawn,move,_point(pawn.K2_GetActorLocation()),50.)
        if not _usable(floor) or not -3. <= _distance(floor) <= 15.:return False
    return bool(rows)


def _finish(state, message):
    global _active
    import unrealsdk
    from unrealsdk.hooks import Type
    active = _active
    job = active['job']
    pending = any(r.get('held') or r.get('restore_pending') for r in job['placement'])
    if pending:
        state = 'uncertain'
        message += ' Player movement remains protected. Use Stop practice setup to retry recovery.'
    job.update(state=state, ok=state == 'running', message=message)
    if state == 'running':
        job['phase'] = 'world_ready'
    try:
        _event('placement_finished', state=state)
    except Exception as exc:
        job.update(state='uncertain', ok=False, message='Placement finished but its receipt could not be saved: '+str(exc))
    finally:
        _active = None
        unrealsdk.hooks.remove_hook(HOOK, Type.POST, IDENT)


def cancel(reason='Practice preparation stopped.', state='cancelled'):
    if _active is None:
        return False
    active = _active
    if not active.get('rollback'):
        active.update(rollback=True, failure=reason, final_state=state, deadline=time.monotonic()+10)
        active['job'].update(state='running', ok=False, message=reason+' Restoring player placement.')
        _event('placement_rollback_started', reason=reason)
    return True


def retry_cleanup(job, journal):
    """Explicit stop retries only pending restoration, never mission/forward work."""
    global _active
    if _active is not None:
        return cancel()
    records = job.get('placement', [])
    if not any(r.get('held') or r.get('restore_pending') or r.get('cleanup_error') for r in records):
        return False
    import unrealsdk
    from unrealsdk.hooks import Type
    for record in records:
        if record.get('cleanup_error') and not record.get('held') and not record.get('restore_pending'):
            # Native recovery can return the same pawn to a safe spawn after
            # our origin-return. Verify its restored movement in place; never
            # teleport it again solely to clear an old location error.
            record.update(verify_cleanup_only=True, rollback_done=False)
        if record.get('held') or record.get('restore_pending'):
            record.pop('rollback_done', None)
            record.pop('cleanup_error', None)
            # This explicit user recovery request may retry an origin-return
            # whose result was false/unknown. Forward placement never repeats.
            if not record.get('rollback_returned'):
                record.pop('rollback_issued', None)
    _active = dict(job=job, journal=journal, rollback=True, emergency=True,
                   failure='Practice preparation stopped.', final_state='cancelled',
                   deadline=time.monotonic()+10, last_frame=None, last_at=0)
    job.update(state='running', ok=False, phase='placement', message='Retrying safe player recovery.')
    unrealsdk.hooks.add_hook(HOOK, Type.POST, IDENT, tick)
    return True


def start(job, rows, journal):
    global _active
    if _active is not None:
        raise RuntimeError('A practice placement still requires cleanup')
    import unrealsdk
    from unrealsdk.hooks import Type
    records = []
    for row in rows:
        pawn = row['pc'].Pawn
        move = pawn.CharacterMovement
        point = _point(pawn.K2_GetActorLocation())
        gravity = float(move.GravityScale)
        if not math.isfinite(gravity) or not all(math.isfinite(v) for v in point.values()):
            raise RuntimeError('Player movement state is unavailable')
        records.append(dict(controller=row['pc']._path_name(), label=row['label'],
                            pawn=pawn._get_address(), pawn_path=pawn._path_name(),
                            movement=move._get_address(), origin=point, gravity=gravity,
                            mode=int(move.MovementMode), custom=int(move.CustomMovementMode),
                            held=False, phase='hold'))
    if not records:
        raise RuntimeError('No players available for practice placement')
    job['placement'] = records
    job.update(phase='placement', message='Loading a safe standing surface at the checkpoint.')
    _active = dict(job=job, journal=journal, deadline=time.monotonic()+15, last_frame=None, last_at=0)
    try:
        _event('placement_started')
        unrealsdk.hooks.add_hook(HOOK, Type.POST, IDENT, tick)
        if not unrealsdk.hooks.has_hook(HOOK, Type.POST, IDENT):
            raise RuntimeError('Practice placement watchdog could not start')
    except Exception:
        _active = None
        raise


def _rollback(record, now):
    if record.get('rollback_done'):
        return
    pawn, move = _context(record)
    if record.get('verify_cleanup_only'):
        point = _point(pawn.K2_GetActorLocation())
        floor = _floor(pawn, move, point, 50.)
        if (not _usable(floor) or not 0. <= _distance(floor) <= 15. or
                float(move.GravityScale) != record['gravity'] or
                int(move.MovementMode) != record['mode'] or
                int(move.CustomMovementMode) != record['custom']):
            raise RuntimeError('Player recovery is not yet safe at the current location')
        _event('placement_cleanup_verified', player=record['label'], location=point,
               origin_returned=sum((point[k]-record['origin'][k])**2 for k in point) <= 150.**2)
        record.pop('cleanup_error', None)
        record.pop('verify_cleanup_only', None)
        record['rollback_done'] = True
        return
    if record['phase'] == 'hold' and not record.get('held'):
        record['rollback_done'] = True
        return
    if not record.get('rollback_issued'):
        record['rollback_issued'] = True
        record['held'] = True
        _event('placement_return_issued', player=record['label'])
        if not _teleport_held(record, record['origin'])[0]:
            raise RuntimeError('Could not return player to the original position')
        record['rollback_returned'] = True
        _event('placement_return_returned', player=record['label'])
        return
    if not record.get('rollback_returned'):
        raise RuntimeError('Return teleport outcome is uncertain')
    point = _point(pawn.K2_GetActorLocation())
    if sum((point[k]-record['origin'][k])**2 for k in point) > 150.**2:
        raise RuntimeError('Player did not remain at the original position during cleanup')
    pawn, move = _maintain_hold(record, record['origin'])
    floor = _floor(pawn, move, point, 200.)
    if not _usable(floor) or _distance(floor) > 15.:
        if now >= _active['deadline']:
            record.update(rollback_done=True, restore_pending=True,
                          cleanup_error='Original position has no confirmed standing surface')
        return  # Keep the hold; a timeout is never permission to fall.
    _restore(record, pawn, move)
    record['rollback_done'] = True


def _advance(record, now):
    pawn, move = _context(record)
    anchor = _active['job']['anchor']['location']
    navigation=_active['job'].get('navigation_scene')
    if record['phase'] == 'hold':
        point = {k.upper(): float(anchor[k]) for k in ('x','y','z')}
        supported = (_navigation_probe(pawn,move,navigation) if navigation else
                     _grounded_probe(pawn, move, point))
        if supported is not None:
            point = supported
            _event('placement_loaded_surface', player=record['label'], location=point)
        else:
            # Only an unloaded/unresolved surface needs a raised streaming probe.
            point['Z'] += 2. * float(pawn.CapsuleComponent.GetScaledCapsuleHalfHeight())
        record['held'] = True  # Cleanup covers a failure between individual writes.
        _event('placement_hold_issued', player=record['label'])
        _hold(record)
        record.update(probe=point, phase='teleport_issued')
        _event('placement_teleport_issued', player=record['label'], location=point)
        placed, gravity_after_teleport = _teleport_held(record, point)
        if not placed:
            raise RuntimeError('Game could not place '+record['label']+' at the checkpoint')
        actual = _point(pawn.K2_GetActorLocation())
        if sum((actual[k]-point[k])**2 for k in point) > 150.**2:
            raise RuntimeError('Native placement moved beyond the checkpoint tolerance')
        record.update(probe=actual, phase='floor', since=now)
        _event('placement_teleport_returned', player=record['label'], location=actual,
               gravity_after_teleport=gravity_after_teleport)
        return
    if record['phase'] == 'floor':
        pawn, move = _maintain_hold(record, record['probe'])
        if navigation:
            point=_navigation_probe(pawn,move,navigation)
            if point is None:
                record.pop('floor_since',None)
                return
            if now-record.setdefault('floor_since',now)<.5:return
            record.update(phase='landing_issued',standing=point)
            _event('placement_navigation_landing_issued',player=record['label'],location=point,
                   authored_location=anchor)
            if not _teleport_held(record,point)[0]:
                raise RuntimeError('Game could not place player on the encounter navigation surface')
            record.update(phase='restore',since=now)
            _event('placement_landing_returned',player=record['label'])
            return
        # Authored encounter centres can be well above the playable floor:
        # The Rescue's entrance returned a walkable floor 34.05m below the
        # probe. Keep the native capsule query and bounded vertical search.
        floor = _floor(pawn, move, record['probe'], MAX_FLOOR_DISTANCE)
        if not _usable(floor) or _distance(floor) < 0.:
            record.pop('floor_since', None)
            return
        if now - record.setdefault('floor_since', now) < .5:
            return
        if _distance(floor) <= 15.:
            # A pre-resolved floor can put the first probe directly on support.
            # K2_TeleportTo may return false for a no-op move to that same point.
            # Verify the existing arrival instead of issuing a redundant move.
            record.update(phase='restore', standing=dict(record['probe']), since=now)
            _event('placement_already_supported', player=record['label'], location=record['standing'])
            return
        point = dict(record['probe'])
        point['Z'] -= _distance(floor) - 3.
        record.update(phase='landing_issued', standing=point)
        _event('placement_landing_issued', player=record['label'], location=point)
        if not _teleport_held(record, point)[0]:
            raise RuntimeError('Game could not place player on the checkpoint floor')
        record.update(phase='restore', since=now)
        _event('placement_landing_returned', player=record['label'])
        return
    point = _point(pawn.K2_GetActorLocation())
    target = record['standing']
    if sum((point[k]-target[k])**2 for k in point) > 150.**2:
        raise RuntimeError('Player did not remain at the practice checkpoint')
    floor = _floor(pawn, move, point, 50.)
    if not _usable(floor) or _distance(floor) > 15.:
        _event('placement_surface_rejected',player=record['label'],phase=record['phase'],location=point,
               blocking=bool(floor.bBlockingHit),walkable=bool(floor.bWalkableFloor),
               penetrating=bool(floor.HitResult.bStartPenetrating),
               floor_distance=float(floor.FloorDist),line_distance=float(getattr(floor,'LineDist',0.)),
               line_trace=bool(getattr(floor,'bLineTrace',False)),
               gravity=float(move.GravityScale),movement_mode=int(move.MovementMode))
        raise RuntimeError('Checkpoint arrival has no safe standing surface')
    if record['phase'] == 'restore':
        pawn, move = _maintain_hold(record, target)
        _restore(record, pawn, move)
        record.update(phase='verify', since=now)
        return
    if record['phase'] == 'verify' and now-record['since'] >= 1.:
        record['phase'] = 'done'
        _event('placement_arrival_verified', player=record['label'], location=point)


def _tick():
    active = _active
    if active is None:
        return
    now = time.monotonic()
    if now-active['last_at'] < .1:
        return
    frame = now if active.get('emergency') else _frame()
    if active['last_frame'] == frame:
        return
    active.update(last_at=now, last_frame=frame)
    if now > active['deadline'] and not active.get('rollback'):
        cancel('Checkpoint placement timed out.', 'stopped')
    errors = []
    for record in active['job']['placement']:
        try:
            if active.get('rollback'):
                _rollback(record, now)
            else:
                _advance(record, now)
        except Exception as exc:
            errors.append(str(exc))
            if active.get('rollback'):
                # Always try restoring fields for every still-identical pawn.
                try:
                    pawn, move = _context(record)
                    if record.get('held') or record.get('restore_pending'):
                        support = _floor(pawn, move, _point(pawn.K2_GetActorLocation()), 50.)
                        if not _usable(support) or _distance(support) > 15.:
                            record['restore_pending'] = True
                            raise RuntimeError('Player remains protected until a standing surface is confirmed')
                        _restore(record, pawn, move)
                except Exception as cleanup:
                    record['cleanup_error'] = str(cleanup)
                record['rollback_done'] = True
                record['cleanup_error'] = record.get('cleanup_error') or str(exc)
    if errors and not active.get('rollback'):
        cancel('; '.join(errors), 'stopped')
        return
    records = active['job']['placement']
    if active.get('rollback'):
        if all(r.get('rollback_done') for r in records):
            failed = [r['cleanup_error'] for r in records if r.get('cleanup_error')]
            _finish('uncertain' if failed else active['final_state'],
                    active['failure'] + (' Cleanup needs inspection: '+'; '.join(failed) if failed else ' Original movement settings restored.'))
    elif all(r['phase'] == 'done' for r in records):
        active['job']['teleported'] = [r['controller'] for r in records]
        _finish('running', 'Everyone arrived safely; checking checkpoint world setup.')


def tick(*args):
    try:
        _tick()
    except Exception as exc:
        # Keep the bounded origin-return/floor-wait path alive even when frame
        # readback or persistence fails. Never release gravity in unloaded space.
        active = _active
        if active is None:
            return
        active['emergency'] = True
        if not active.get('rollback'):
            active['deadline'] = time.monotonic()+10
        active.update(rollback=True, failure='Practice placement needs inspection: '+str(exc), final_state='uncertain')
        active['job'].update(state='running', ok=False, message=active['failure']+' Returning players safely.')
