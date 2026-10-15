"""Observe authored mission travel without retaining old-world record pointers."""
import copy
import json
import os
import time

# Native arrival finish graphs can include the full credits (observed >20min).
# This is a bounded waiting policy, never evidence that the graph completed.
ARRIVAL_FINISH_TIMEOUT = 3600.


def world():
    from .campaign_replay import world as current
    return current()


def map_name(value):
    return value._path_name().rsplit('.',1)[-1].casefold()


def player_key(row):
    return (row['label'],int(row['state'].PlayerId),bool(row['host']))


def roster(rows):
    return sorted(player_key(row) for row in rows)


def begin(rows,target):
    w=world()
    return dict(pid=os.getpid(),world=w._get_address(),world_path=w._path_name(),
                roster=roster(rows),target=player_key(next(r for r in rows if r['pc']._path_name()==target)))


def _waiting(owner,message,timeout=360.,timer='wait_since'):
    ctx=owner._job['completion_context']
    # A long verified sequence must not consume the following short settling
    # window. Keep its absolute deadline even across temporary loading phases.
    if 'arrival_wait_since' in ctx:
        if time.monotonic()-ctx['arrival_wait_since']>ARRIVAL_FINISH_TIMEOUT:
            raise RuntimeError('Mission map loading did not settle; no travel or outcome repeated')
        if timer=='wait_since':timer='arrival_settle_since'
    if time.monotonic()-ctx.setdefault(timer,time.monotonic())>timeout:
        raise RuntimeError('Mission map loading did not settle; no travel or outcome repeated')
    owner._job.update(await_tick=True,message=message)
    return False


def _objective_arrival(owner, engine, row, destination):
    """Verify a native mid-mission map transition from fresh objective states."""
    from .mission_execution import DATA,objectives
    name=owner._job['completion_context']['mission']
    definition=DATA.get(name)
    if not definition:return False
    receipt=owner._job.get('objective_runs',{}).get(name,{})
    if not receipt.get('issued') or receipt.get('pending'):return False
    rows=objectives(engine,row,definition)
    by_token={o['token']:o for o in rows}
    issued=[by_token.get(token) for token in receipt['issued']]
    if any(o is None or o['state']!=13 or 'group' not in o for o in issued):return False
    last_group=max(o['group'] for o in issued)
    arrivals=[o for o in rows if o.get('travel_map')==destination and o['group']>=last_group]
    if any(arrival['state']==13 and o['state']==4 and o.get('group',-1)>=arrival['group'] and
           destination in o.get('completion_maps',[]) for arrival in arrivals for o in rows):
        return 'ready'
    if any(o['state'] in (10,11,12) for o in arrivals):return 'finishing'
    return False


def observe(owner):
    """Runs before either coordinator inspects mission or ownership pointers."""
    job=owner._job
    if not job or job.get('completion_path') not in ('objective_graph','mission_replay'):return True
    ctx=job['completion_context']
    if ctx['pid']!=os.getpid():raise RuntimeError('Game process changed during mission completion')
    w=world()
    pending=ctx.get('travel')
    if job.get('placement_policy')=='map_only' and ctx.get('placement'):
        raise RuntimeError('Completion runs cannot retain objective placement; inspect the previous run')
    if ctx.get('placement') and (w is None or w._get_address()!=ctx['world']):
        raise RuntimeError('World changed during objective placement; no outcome issued')
    if w is not None and w._get_address()==ctx['world'] and not pending:
        if job.get('placement_policy')=='map_only':return True
        from .mission_completion_placement import observe as observe_placement
        return observe_placement(owner)
    if w is None:return _waiting(owner,'Waiting for the mission map to load; no calls repeated.')
    if pending and w._get_address()==pending['from']:
        return _waiting(owner,'Loading the authored mission map; no travel repeated.')
    expected=[pending['destination']] if pending else ctx.get('expected_maps',[])+ctx.get('objective_maps',[])
    if map_name(w) not in expected:
        raise RuntimeError('Mission completion reached an unexpected map; inspect before continuing')
    from mods_base import get_pc
    pc=get_pc()
    if pc is None or pc.Pawn is None or not pc._path_name().startswith(w._path_name()+':'):
        return _waiting(owner,'Waiting for players to finish loading.')
    try:rows=owner._party()
    except RuntimeError as exc:
        if str(exc)=='Every participant must be loaded in the host game':
            return _waiting(owner,'Waiting for every party member to finish loading.')
        raise
    if roster(rows)!=ctx['roster']:raise RuntimeError('Players changed during mission map loading')
    if any(not r['pc']._path_name().startswith(w._path_name()+':') or
           not r['pc'].Pawn._path_name().startswith(w._path_name()+':') for r in rows):
        return _waiting(owner,'Waiting for the full party on the mission map.')
    from .mission_practice_placement import players_grounded
    if not players_grounded(rows):
        ctx.pop('stable_since',None)
        return _waiting(owner,'Waiting for everyone to stand safely after travel.')
    if time.monotonic()-ctx.setdefault('stable_since',time.monotonic())<.5:
        return _waiting(owner,'Verifying the loaded mission map.')
    engine=copy.copy(owner._runtime)
    engine.world_address=None
    engine.ensure_world()
    snapshot=engine.snapshot()
    name=ctx.get('mission')
    if name:
        row=owner._row(snapshot,name)
        if row['token']!=ctx['token']:raise RuntimeError('Mission identity changed during travel')
        if not pending and owner._state(row)!='completed':
            if map_name(w) not in ctx.get('objective_maps',[]):
                raise RuntimeError('Map changed before the issued mission finished; no outcome repeated')
            arrival=_objective_arrival(owner,engine,row,map_name(w))
            if arrival=='finishing':
                ctx.pop('arrival_settle_since',None)
                return _waiting(owner,'The mission is playing its arrival sequence; waiting for normal completion.',
                                ARRIVAL_FINISH_TIMEOUT,'arrival_wait_since')
            if arrival!='ready':
                return _waiting(owner,'Waiting for the authored map-arrival objective to settle; no calls repeated.')
    target=next((r for r in rows if player_key(r)==tuple(ctx['target'])),None)
    if target is None:raise RuntimeError('The selected acceptance player changed during travel')
    binding=owner._binding(rows)
    owner._journal(dict(event='completion_map_verified',from_binding=job['binding'],binding=binding,
                        world=w._path_name(),mission=name))
    owner._runtime=engine
    job.update(binding=binding,target=target['pc']._path_name())
    if pending or map_name(w) in ctx.get('objective_maps',[]):
        receipt=job.get('objective_runs',{}).get(name)
        if receipt is not None:receipt['progress_at']=time.monotonic()
    ctx.update(world=w._get_address(),world_path=w._path_name())
    for key in ('travel','wait_since','arrival_wait_since','arrival_settle_since','stable_since','expected_maps'):ctx.pop(key,None)
    return True


def prepare(owner,name,row,definition):
    """Move to the mission's authored map before resetting/accepting it."""
    # An active cross-map mission is positioned by its selected objective.
    # Returning to the opening map here would undo every verified stage travel.
    if owner._state(row)=='active' and (owner._job.get('placement_policy')=='map_only' or
                                       len(definition.get('execution_maps',[]))>1):return True
    return travel_to(owner,name,row,definition['title'],definition.get('execution_map'))


def prepare_reset(owner,name,row,definition):
    """Unload the mission's actors before resetting their mission state."""
    maps=set(definition.get('execution_maps') or [definition.get('execution_map')])
    if not maps or None in maps:raise RuntimeError('Mission reset map is unresolved')
    if map_name(world()) not in maps:return True
    destination=next((m for m in ('world_p','intro_p') if m not in maps),None)
    if destination is None:raise RuntimeError('No reviewed holding map is available for this mission reset')
    return travel_to(owner,name,row,definition['title'],destination)


def objective_ready(owner,name,row,definition,objective):
    destinations=objective.get('completion_maps',[])
    if not destinations and objective.get('scene_anchor'):
        destinations=[objective['scene_anchor']['map'].casefold()]
    current=map_name(world())
    if not destinations or current in destinations:
        owner._job['completion_context'].pop('travel_recovery',None)
        # Completion still runs native finish actions on their authored maps.
        # Only explicit replay selection may relocate/hold individual pawns.
        if owner._job.get('placement_policy')=='map_only':return True
        from .mission_completion_placement import ready
        return ready(owner,name,objective)
    if len(destinations)!=1:
        raise RuntimeError('Objective completion spans ambiguous maps: '+objective['name'])
    return travel_to(owner,name,row,definition['title'],destinations[0],objective)


def travel_to(owner,name,row,title,destination,objective=None,station=None):
    ctx=owner._job['completion_context']
    if not destination:raise RuntimeError('The authored mission map is unresolved: '+name)
    if station and station.split('.',1)[0].casefold()!=destination:
        raise RuntimeError('Recorded spawn station does not belong to the selected map')
    w=world()
    if map_name(w)==destination:
        ctx.pop('travel_recovery',None)
        return True
    from . import travel
    if ctx.get('travel'):return _waiting(owner,'Waiting for the requested mission map.')
    def issued():
        # Validation and temporary-control cleanup precede this boundary. A
        # rejected request has not been sent and must not leave pending travel.
        ctx.update(mission=name,token=row['token'],wait_since=time.monotonic(),travel_recovery=True,
                   travel=dict(destination=destination,from_world=w._path_name(),**{'from':w._get_address()}))
        owner._job.update(state='uncertain',ok=False,await_tick=True)
        owner._journal(dict(event='completion_map_issued',mission=name,token=row['token'],destination=destination,
                            objective=objective))
    if station:travel.travel_to_station(station,before_issue=issued)
    else:travel.travel_to_map(destination,before_issue=issued)
    owner._journal(dict(event='completion_map_returned',mission=name,destination=destination))
    owner._job.update(state='running',ok=True,message='Loading the authored map for '+title+'.')
    return False


def expect_finish(owner,name,row,definition):
    # Successor maps still require a completed mission. Mid-mission arrivals
    # separately require a settled authored map objective and fresh local work.
    ctx=owner._job['completion_context']
    ctx.update(mission=name,token=row['token'],expected_maps=definition.get('successor_maps',[]),
               objective_maps=sorted({o['travel_map'] for g in definition.get('groups',[])
                                      for o in g['objectives'] if o.get('travel_map')}))


def recover(owner,payload,events,live,path=None):
    """Reconcile an authored-map request by observation only; never resend it."""
    issued=next((i for i in range(len(events)-1,-1,-1)
                 if events[i].get('event') in ('issued','completion_map_issued')),None)
    if issued is None or events[issued]['event']!='completion_map_issued':return None
    mode=payload.get('mode','inspect')
    if mode not in ('inspect','continue','close') or (mode!='inspect' and payload.get('acknowledge_shared_progress') is not True):
        raise ValueError('Choose continue or close and acknowledge shared progress')
    if not live:
        if mode!='close' or path is None:
            raise ValueError('Original map-travel context is not loaded; inspect the destination and close this record before new work')
        # Closing an old record asserts no completion and never resurrects or
        # retries the lost native request. Applied game progress is retained.
        event=dict(event='recovered',state='stopped',closed=True,time=time.time(),
                   report=dict(operation='map_travel',observed='unverified_after_reload'))
        with path.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(event)+'\n');stream.flush();os.fsync(stream.fileno())
        return dict(ok=True,state='stopped',closed=True,id=payload['job_id'],
                    message='Old travel record closed without verifying completion or repeating calls. Inspect current progress before a new run.')
    if not observe(owner):return dict(owner.status(),operation='map_travel',observed='loading')
    call=events[issued]
    ctx=owner._job['completion_context']
    if map_name(world())!=call['destination'] or ctx.get('mission')!=call['mission'] or ctx.get('token')!=call['token']:
        raise ValueError('The recorded mission map has not been verified; no travel repeated')
    report=dict(operation='map_travel',mission=call['mission'],observed='loaded',destination=call['destination'])
    if mode=='inspect':return dict(ok=True,**report,message='Mission map verified; no game calls repeated.')
    owner._journal(dict(event='recovered',report=report,state='stopped' if mode=='close' else 'running'))
    owner._job.update(ok=True,state='stopped' if mode=='close' else 'running',
                      message='Mission map verified; '+('run closed.' if mode=='close' else 'continuing without repeating travel.'))
    if mode=='close':owner._job['closed']=True
    ctx.pop('travel_recovery',None)
    return owner.status()
