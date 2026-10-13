"""Load authored objective locations before issuing completion outcomes.

The existing placement watchdog owns temporary movement changes. A child job
keeps its phases separate from the mission coordinator and retains cleanup
receipts when polling stops. No location is inferred for unresolved targets.
"""
import time
import math

# Scene-loading proximity policy, not a native interaction or melee range.
LOADED_OBJECT_DISTANCE = 5000.


def _same_world(actor, world):
    # World Partition actors retain their generated level's package path.
    # BL4's actual level ownership, not a path prefix, identifies the live world.
    if actor is None:return False
    level=actor.GetLevel()
    owning=getattr(level,'OwningWorld',None) if level is not None else None
    return owning is not None and owning._get_address()==world._get_address()


def _encounter(scene, w):
    import unrealsdk
    identity=scene['actor']
    matches=[]
    for actor in unrealsdk.find_all('SpawnEncounter',exact=False):
        if not _same_world(actor,w):continue
        conduit=actor.FactsConduit
        if str(conduit.RegistryName.Name.Name).casefold()!=identity['registryname'].casefold():continue
        if identity.get('groupname') and str(conduit.GroupName.Name).casefold()!=identity['groupname'].casefold():continue
        matches.append(actor)
    if len(matches)>1:raise RuntimeError('The authored encounter scene is ambiguous')
    return matches[0] if matches else None


def navigation_point(pawn, scene):
    """Ask BL4's native navigation mesh for a bounded encounter approach.

    The configured encounter radius bounds this query; it does not prove that
    the encounter has activated. Missing streamed navigation stays unresolved.
    """
    import unrealsdk
    from .mission_completion_context import world, map_name
    w=world()
    if w is None or map_name(w)!=scene['actor']['map'].casefold():return None
    encounter=_encounter(scene,w)
    if encounter is None:return None
    radius=max(float(scene['radius']),float(encounter.SpawnerActivation.Radius))
    if not math.isfinite(radius) or radius<=0.:return None
    layers={}
    for settings in unrealsdk.find_all('GbxNavSettings',exact=False):
        layer=settings.DefaultNavMeshLayer
        if layer is not None:layers[layer._get_address()]=layer
    if len(layers)!=1:return None
    lib=unrealsdk.find_object('GbxNavBlueprintLibrary','/Script/GbxNav.Default__GbxNavBlueprintLibrary')
    if lib is None:return None
    start={k.upper():float(v) for k,v in scene['center'].items()}
    vector=unrealsdk.make_struct('/Script/CoreUObject.Vector',**start)
    query=lib.MakeGbxNavQueryData(next(iter(layers.values())),None,None)
    found,point=lib.ProjectToNavMesh(pawn,vector,radius,query,vector)
    if not found:return None
    result={k:float(getattr(point,k)) for k in ('X','Y','Z')}
    if (not all(math.isfinite(v) for v in result.values()) or
            sum((result[k]-start[k])**2 for k in result)>radius**2):return None
    return result


def _encounter_ready(owner, scene):
    """Keep safe players in an already spawned encounter or its marker area."""
    from .mission_completion_context import world, map_name
    from .mission_practice_placement import players_grounded
    identity=scene['actor'];w=world()
    if w is None or map_name(w)!=identity['map'].casefold():return False
    rows=owner._party()
    if not rows or not players_grounded(rows):return False
    in_area=True
    for row in rows:
        point=row['pc'].Pawn.K2_GetActorLocation()
        distance=sum((float(getattr(point,k.upper()))-scene['center'][k])**2 for k in ('x','y','z'))
        if not math.isfinite(distance) or distance>scene['radius']**2:
            in_area=False
    encounter=_encounter(scene,w)
    if encounter is None:return False
    # A HUD waypoint radius is not the encounter's activation boundary. Native
    # spawners can already have enemies alive while players stand outside that
    # marker (observed at The Rescue's dam). Do not move them onto the marker's
    # unsafe centre solely to satisfy our scene-loading heuristic.
    if in_area:return True
    if not encounter.IsEncounterEnabled():return False
    for spawner in encounter.SpawnerComponents:
        if spawner is None or not _same_world(spawner.GetOwner(),w):continue
        for actor in spawner.GetAliveActors(0,False):
            if (_same_world(actor,w)
                    and not actor.IsActorBeingDestroyed()):
                return True
    return False


def _object_scene_ready(owner, anchor):
    """Keep grounded players near the exact loaded interactive target.

    An object's authored origin can be inside its solid mesh. Loaded presence
    only avoids scene placement; it never replaces required NPC interaction.
    """
    parts=str(anchor.get('actor','')).casefold().split('.')
    if len(parts)!=6 or parts[0]!='registry' or parts[2]!='top' or parts[5]!='__nochannel':return False
    import unrealsdk
    from .mission_completion_context import world,map_name
    from .mission_practice_placement import players_grounded
    w=world()
    if w is None or map_name(w)!=parts[1]:return False
    rows=owner._party()
    if not rows or not players_grounded(rows):return False
    matches=[]
    for actor in unrealsdk.find_all('InteractiveObject',exact=False):
        if not _same_world(actor,w) or actor.IsActorBeingDestroyed():continue
        conduit=actor.FactsConduit
        if (str(conduit.RegistryName.Name.Name).casefold()==parts[4] and
                str(conduit.GroupName.Name).casefold()==parts[3]):matches.append(actor)
    if len(matches)>1:raise RuntimeError('The authored interactive scene is ambiguous')
    if not matches:return False
    point=matches[0].K2_GetActorLocation()
    for row in rows:
        here=row['pc'].Pawn.K2_GetActorLocation()
        distance=sum((float(getattr(here,k))-float(getattr(point,k)))**2 for k in ('X','Y','Z'))
        if not math.isfinite(distance) or distance>LOADED_OBJECT_DISTANCE**2:return False
    return True


def _child(owner):
    return owner._job.get('completion_context', {}).get('placement')


def _held(child):
    return any(r.get('held') or r.get('restore_pending') or r.get('cleanup_error')
               for r in child.get('placement', []))


def observe(owner):
    child = _child(owner)
    if child is None:
        return True
    from . import mission_practice_placement as placement
    placement.tick()
    job = owner._job
    stop = child.get('stop_state')
    if stop and child['state'] != 'running':
        if _held(child):
            raise RuntimeError('Player placement still needs recovery; use Stop to retry cleanup')
        job.update(state=stop, ok=False, message=child['stop_reason'])
        owner._journal(dict(event='state', state=stop, message=job['message']))
        return False
    if child['state'] != 'running':
        raise RuntimeError(child.get('message', 'Objective scene placement failed'))
    if child['phase'] == 'world_ready' and not _held(child):
        owner._journal(dict(event='completion_placement_verified', key=child['key'],
                            anchor=child['anchor']))
        ctx = job['completion_context']
        ctx['placed'] = child['key']
        ctx.pop('placement')
        return True
    job.update(await_tick=True, message=child.get('message', 'Loading the objective scene.'))
    return False


def ready(owner, name, objective):
    scene = objective.get('encounter_scene')
    anchor = ((objective.get('scene_anchor') or objective.get('completion_anchor')) if scene else
              objective.get('completion_anchor') or objective.get('scene_anchor'))
    if not anchor or objective.get('travel_map') or objective.get('finish_actions_pending'):
        return True
    ctx = owner._job['completion_context']
    key = [name, objective['token'], objective['group']]
    if (ctx.get('placed')!=key and not scene and not objective.get('interaction') and _child(owner) is None and
            _object_scene_ready(owner,anchor)):
        if ctx.get('placed')!=key:
            owner._journal(dict(event='completion_object_scene_loaded',key=key,anchor=anchor))
            ctx['placed']=key
        return True
    if scene and _child(owner) is None and _encounter_ready(owner,scene):
        if ctx.get('placed')!=key:
            owner._journal(dict(event='completion_scene_loaded',key=key,scene=scene))
            ctx['placed']=key
        ctx.pop('scene_wait_since',None)
        return True
    if ctx.get('placed') == key:
        if scene:
            if time.monotonic()-ctx.setdefault('scene_wait_since',time.monotonic())>120:
                raise RuntimeError('The authored encounter did not load around its staging location')
            return False
        return True
    if _child(owner) is not None:
        return False
    from . import mission_practice_placement as placement
    child = dict(state='running', ok=True, phase='prepare', anchor=anchor, key=key)
    if scene and not objective.get('scene_anchor'):
        child['navigation_scene']=scene
    ctx.pop('scene_wait_since',None)
    ctx['placement'] = child
    def journal(event):
        owner._journal(dict(event='completion_placement', key=key, detail=event))
    placement.start(child, owner._party(), journal)
    owner._job.update(await_tick=True, message='Loading the objective scene before completion.')
    return False


def stop(owner, reason='Remaining steps cancelled; applied progress is retained.', state='cancelled', *, retry=False):
    """Finish owned cleanup before making the parent terminal; never retry work."""
    child = _child(owner)
    if child is None:
        return False
    from . import mission_practice_placement as placement
    child.update(stop_state=state, stop_reason=reason)
    def journal(event):
        owner._journal(dict(event='completion_placement', key=child['key'], detail=event))
    pending = placement.cancel(reason, state)
    if not pending and retry:
        pending = placement.retry_cleanup(child, journal)
    if pending:
        owner._job.update(state='running', ok=False, await_tick=True,
                          message=reason+' Restoring player movement.')
    elif _held(child):
        owner._job.update(state='uncertain', ok=False,
                          message='Player placement still needs recovery; use Stop to retry cleanup')
    else:
        owner._job.update(state=state, ok=False, message=reason)
        owner._journal(dict(event='state', state=state, message=reason))
    return True
