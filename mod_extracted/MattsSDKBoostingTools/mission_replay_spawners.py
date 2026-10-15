"""Scoped native spawner refresh for a prepared replay, before character reload.

Observed lead: Mattmab's archived SpawnMultiplierBL4 calls ResetSpawner(False).
The Mudmouth support-spawner reset plus human reload restored normal combat.
This helper issues resets; it does not claim enemies spawned or quests advanced.
No global spawn reset, actor cloning, objective outcomes, or enable overrides.
"""
import os
from .mission_completion_context import world, map_name
from .mission_completion_placement import _same_world


def _identity(component):
    conduit = component.FactsConduit
    group = str(conduit.GroupName.Name).casefold()
    if group == 'none':
        group = 'base'
    return group, str(conduit.RegistryName.Name.Name).casefold()


def refresh_loaded(sdk, engine, owner, specifications, transaction, journal):
    """Refresh explicitly sourced, empty spawners once per replay transaction.

    Call before unloading the target world/character and restoring save progress.
    The caller must subsequently reload and verify normal spawn/death credit.
    Components are freshly resolved; only semantic identities survive travel.
    """
    engine.check_build()
    current = world()
    if current is None or not _same_world(owner, current):
        raise RuntimeError('Replay owner does not belong to the current world')
    if transaction.get('spawn_refresh_pid', os.getpid()) != os.getpid():
        raise RuntimeError('Spawner refresh belongs to a different game process')
    transaction['spawn_refresh_pid'] = os.getpid()
    states = transaction.setdefault('spawn_refresh', {})
    plans, deferred, seen = [], [], set()
    components = list(sdk.find_all('SpawnerComponent', exact=False))
    for spec in specifications:
        if not all(isinstance(spec.get(k), str) and spec[k] for k in ('map', 'group', 'registry', 'source', 'pointer')):
            raise ValueError('Spawner identity requires explicit source evidence')
        identity = tuple(spec[k].casefold() for k in ('map', 'group', 'registry'))
        if identity in seen:
            raise ValueError('Duplicate replay spawner identity')
        seen.add(identity)
        key = '|'.join(identity)
        if states.get(key) == 'issued':
            raise RuntimeError('Spawner reset is unconfirmed; inspect before repeating')
        if states.get(key) in ('returned', 'living'):
            continue
        if map_name(current) != spec['map'].casefold():
            deferred.append(key)
            continue
        matches = [c for c in components if _same_world(c.GetOwner(), current)
                   and _identity(c) == identity[1:]]
        if len(matches) > 1:
            raise RuntimeError('Replay spawner identity is ambiguous')
        if not matches:
            deferred.append(key)
            continue
        component = matches[0]
        # Archive GetEnumeratorName evidence + current live read confirmed
        # ESpawnedActorType 2 = InternalAndExternal. The build gate stays active.
        living = list(component.GetAliveActors(2, False))
        plans.append((key, component, living, spec))
    # Resolve every available identity before issuing the first mutation.
    requested = 0
    for key, component, living, spec in plans:
        latest = world()
        if (latest is None or latest._get_address() != current._get_address()
                or not _same_world(owner, latest)
                or not _same_world(component.GetOwner(), latest)):
            raise RuntimeError('Replay world changed before spawner refresh')
        if living:
            states[key] = 'living'
            journal(dict(event='replay_spawner_living', identity=key, count=len(living)))
            continue
        states[key] = 'issued'
        journal(dict(event='replay_spawner_reset_issued', identity=key,
                     source=spec['source'], pointer=spec['pointer'], destroy_actors=False))
        component.ResetSpawner(False)
        states[key] = 'returned'
        requested += 1
        journal(dict(event='replay_spawner_reset_returned', identity=key))
    return dict(reset_requests=requested, deferred=deferred,
                spawn_verified=False, objective_outcomes_issued=False)
