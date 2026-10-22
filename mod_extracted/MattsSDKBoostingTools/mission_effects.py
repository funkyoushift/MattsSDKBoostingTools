"""Reviewed completion dependencies, not a substitute for all authored actions.

Beach evidence: docs/changes/2026-10-12-playable-progress-effects.md.
The safehouse is an external objective of Recruitment Drive. Completing the
story record alone neither satisfies its door prerequisite nor claims it.
"""
BEACH = 'Mission_Main_Beach'
SAFEHOUSE = 'ZoneActivity_Grasslands_SafehouseMain'
CHECKPOINTS = (
    'missions.MissionSet_Main_Beach.Mission_Main_Beach.Final.Melee_the_Door_0_EndState',
    'missions.missionset_main_beach.Mission_Main_Beach.Final.activate__cl4ptps_safehouse_endstate',
)

SAFEHOUSE_SWITCHES = (
    'Grasslands_ClaptrapSafeHouse_DatapadThingy',
    'Grasslands_ClaptrapSafeHouse_CommandConsole',
)


def _world_safehouse_claim_address(name, resources):
    """Return the reviewed base-game PoA State address, if this is a safehouse."""
    if not name.startswith('ZoneActivity_') or 'Safehouse' not in name:
        return None
    import json
    actors = json.loads(resources.joinpath('mission_activity_actors.json').read_text())
    identity = actors.get(name, {}).get('actor')
    if not identity or identity['map'] != 'World_P':
        return None
    return '.'.join(('registry', identity['map'], 'top', identity['groupname'],
                     identity['registryname'], 'State'))


def _verify_safehouse_claim(owner, target, name, address):
    """Apply the authored safehouse effect to the loaded actor or stored fact.

    Nexus-Data-Mission4.json gives all 14 World_P safehouses a completed action
    of PoA.State=Claimed. A fast mission callback can finish the mission record
    without running that action. Readback keeps a locked safehouse from being
    reported as captured.
    """
    import unrealsdk
    import json
    from importlib.resources import files
    identity = json.loads(files(__package__).joinpath('mission_activity_actors.json').read_text())[name]['actor']
    actors = [actor for actor in unrealsdk.find_all('PoAActor')
              if str(actor.FactsConduit.GroupName.Name).casefold() == identity['groupname'].casefold()
              and str(actor.FactsConduit.RegistryName.Name.Name).casefold() == identity['registryname'].casefold()]
    if len(actors) > 1:
        raise RuntimeError(name + ': safehouse actor is ambiguous; capture not issued')
    if actors:
        actor = actors[0]
        lib = unrealsdk.find_object('GbxActorStateBlueprintLibrary',
                                   '/Script/GbxEngine.Default__GbxActorStateBlueprintLibrary')
        key = unrealsdk.make_struct('/Script/GbxEngine.GbxActorStateMachineKey', Name='State', Index=0)
        def read():
            return str(lib.GetActorStateValue(OwnerContext=actor, StateName=key)[0])
        def write():
            states = lib.GetActorStateMachineStates(OwnerContext=actor, StateMachine=key)[0]
            claimed = [state for state in states if str(state.Name).casefold() == 'claimed']
            if len(claimed) != 1:
                raise RuntimeError(name + ': unique Claimed actor state unavailable')
            lib.SetActorStateValue(OwnerContext=actor, StateName=key, StateValue=claimed[0])
        channel = 'loaded_actor'
    else:
        facts = unrealsdk.find_object('FactsBlueprintLibrary', '/Script/GbxGame.Default__FactsBlueprintLibrary')
        def read():
            return str(facts.ReadFact(OwnerContext=target, AddressString=address,
                                      AsName='None', AsInt=0, AsBool=False)[1])
        def write():
            facts.WriteFact(OwnerContext=target, AddressString=address,
                            AsName='Claimed', AsInt=0, AsBool=False)
        channel = 'stored_fact'

    before = read()
    if before.casefold() == 'claimed':
        owner._journal(dict(event='safehouse_claim_verified', mission=name,
                            address=address, channel=channel, before=before))
        return
    if before.casefold() not in ('none', 'initialization', 'discovered', 'claimable'):
        raise RuntimeError(name + ': capture state is unknown; console unlock not issued')
    owner._journal(dict(event='issued', mission=name, operation='safehouse_claim',
                        address=address, channel=channel, before=before))
    try:
        write()
        after = read()
        owner._journal(dict(event='returned', mission=name, operation='safehouse_claim',
                            address=address, channel=channel, after=after))
        if after.casefold() != 'claimed':
            raise RuntimeError(name + ': capture did not read back as Claimed')
    except Exception as exc:
        error = RuntimeError(name + ': capture is unconfirmed; inspect before continuing')
        error.issued = True
        raise error from exc


def _reset_stored_fact(name, address, allowed, value, journal, *, validate_only=False):
    """Reset an authored registry fact even when its actor is streamed out."""
    import unrealsdk
    from mods_base import get_pc
    pc = get_pc()
    if pc is None:
        raise RuntimeError('No local mission context for activity reset')
    lib = unrealsdk.find_object('FactsBlueprintLibrary', '/Script/GbxGame.Default__FactsBlueprintLibrary')
    def read():
        return str(lib.ReadFact(OwnerContext=pc, AddressString=address,
                               AsName='None', AsInt=0, AsBool=False)[1])
    before = read()
    if before.casefold() in ('none', value.casefold()):
        if not validate_only:
            journal(dict(event='stored_interaction_unchanged', mission=name, address=address, before=before))
        return
    if before.casefold() not in {s.casefold() for s in allowed}:
        raise RuntimeError(f'Unknown stored activity state {before!r} at {address}; this fact was not reset')
    if validate_only:return
    journal(dict(event='stored_interaction_reset_issued', mission=name, address=address, before=before))
    try:
        lib.WriteFact(OwnerContext=pc, AddressString=address, AsName=value, AsInt=0, AsBool=False)
        after = read()
        journal(dict(event='stored_interaction_reset_returned', mission=name, address=address, after=after))
        if after.casefold() != value.casefold():
            raise RuntimeError('Stored activity state did not reset')
    except Exception as exc:
        error = RuntimeError('Stored activity reset unconfirmed; inspect before retrying')
        error.issued = True
        raise error from exc


def reset_activity_state(name, journal, *, validate_only=False):
    """Restart the loaded activity marker's native state machine, not discovery.

    Actor identities are extracted from each reviewed mission's authored alias.
    The native Initialization state is resolved by name in the loaded actor.
    """
    import json
    from importlib.resources import files
    identities = json.loads(files(__package__).joinpath('mission_activity_actors.json').read_text())
    if name not in identities:
        return
    import unrealsdk
    identity = identities[name]['actor']
    actors = [a for a in unrealsdk.find_all('PoAActor')
              if str(a.FactsConduit.GroupName.Name).casefold() == identity.get('groupname', 'None').casefold()
              and str(a.FactsConduit.RegistryName.Name.Name).casefold() == identity['registryname'].casefold()]
    if not actors:
        address = '.'.join(('registry', identity['map'], 'top',
                            identity.get('groupname', 'None'), identity['registryname'], 'State'))
        # Discovered is retained by an unclaimed activity too (live Silo1
        # receipt in completion-and-ui-verification); it needs the same reset.
        _reset_stored_fact(name, address, ('Claimed', 'Claimable', 'Discovered'),
                           'Initialization', journal, validate_only=validate_only)
        return
    if len(actors) != 1:
        raise RuntimeError('Activity actor identity is ambiguous; reset not issued')
    actor = actors[0]
    lib = unrealsdk.find_object('GbxActorStateBlueprintLibrary',
                               '/Script/GbxEngine.Default__GbxActorStateBlueprintLibrary')
    key = unrealsdk.make_struct('/Script/GbxEngine.GbxActorStateMachineKey', Name='State', Index=0)
    states = lib.GetActorStateMachineStates(OwnerContext=actor, StateMachine=key)[0]
    initial = [s for s in states if str(s.Name).casefold() == 'initialization']
    if len(initial) != 1:
        raise RuntimeError('Activity has no known initialization state; reset not issued')
    before = str(lib.GetActorStateValue(OwnerContext=actor, StateName=key)[0])
    if validate_only or before.casefold() == 'initialization':
        return
    journal(dict(event='activity_reset_issued', mission=name, before=before))
    try:
        lib.SetActorStateValue(OwnerContext=actor, StateName=key, StateValue=initial[0])
        after = str(lib.GetActorStateValue(OwnerContext=actor, StateName=key)[0])
        journal(dict(event='activity_reset_returned', mission=name, after=after))
        if after.casefold() != 'initialization':
            raise RuntimeError('Activity initialization not confirmed')
    except Exception as exc:
        error = RuntimeError('Activity reset unconfirmed; inspect before retrying')
        error.issued = True
        raise error from exc


def reset_interactions(name, journal, objective=None, *, validate_only=False):
    """Clear authored interaction latches before native checkpoint reset.

    Native reset clears objective memory but can retain safehouse switch presses.
    Streamed-out actors retain registry facts too, so reset those by their
    verified full addresses. Only reviewed aliases/checkpoints are changed.
    """
    if name == SAFEHOUSE:
        if objective is None or objective.casefold() == 'find_the_datapad':
            names = SAFEHOUSE_SWITCHES
        elif objective.casefold() == 'claim_the_command_console':
            names = SAFEHOUSE_SWITCHES[1:]
        else:
            return
        identities = {alias: dict(map='World_P', groupname='Grasslands_ClaptrapSafeHouse',
                                  registryname=alias) for alias in names}
    else:
        if not name.startswith('ZoneActivity_') or 'Safehouse' not in name:
            return
        import json
        from importlib.resources import files
        definitions = json.loads(files(__package__).joinpath('mission_replay_interactions.json').read_text())
        rows = definitions['missions'].get(name, {}).get('interactions', [])
        if objective is not None:
            selected = next((r for r in rows if r['objective'] == objective.casefold()), None)
            if selected is None:
                return
            rows = [r for r in rows if r['order'] >= selected['order']]
        identities = {r['actor']['registryname']: r['actor'] for r in rows}
        if len(identities) != len(rows):
            raise RuntimeError('Duplicate authored interaction identity; reset not issued')
        names = tuple(identities)
        if not names:
            return
    import unrealsdk
    lib = unrealsdk.find_object('GbxActorStateBlueprintLibrary',
                               '/Script/GbxEngine.Default__GbxActorStateBlueprintLibrary')
    key = unrealsdk.make_struct('/Script/GbxEngine.GbxActorStateMachineKey', Name='Pressed', Index=0)
    value = unrealsdk.make_struct('/Script/GbxEngine.GbxActorStateMachineStateKey', Name='FALSE', Index=0)
    actors = {}
    for actor in unrealsdk.find_all('InteractiveSwitch', exact=False):
        conduit = actor.FactsConduit
        alias = str(conduit.RegistryName.Name.Name)
        if alias not in identities or str(conduit.GroupName.Name) != identities[alias].get('groupname', 'None'):
            continue
        if alias in actors:
            raise RuntimeError('Duplicate safehouse interaction alias; reset not issued')
        current = str(lib.GetActorStateValue(OwnerContext=actor, StateName=key)[0])
        if current.casefold() not in ('true', 'false'):
            raise RuntimeError('Unknown safehouse switch state; reset not issued')
        actors[alias] = (actor, current)
    # Validate streamed-out switches before changing any loaded switch.
    for alias in names:
        if alias not in actors:
            identity = identities[alias]
            address = '.'.join(('registry', identity['map'], 'top',
                                identity.get('groupname', 'None'), alias, 'Pressed'))
            _reset_stored_fact(name, address, ('TRUE',), 'FALSE', journal, validate_only=True)
    if validate_only:return
    for alias in names:
        if alias not in actors:
            identity = identities[alias]
            address = '.'.join(('registry', identity['map'], 'top',
                                identity.get('groupname', 'None'), alias, 'Pressed'))
            _reset_stored_fact(name, address, ('TRUE',), 'FALSE', journal)
            continue
        actor, before = actors[alias]
        if before.casefold() == 'false':
            continue
        journal(dict(event='interaction_reset_issued', mission=name, alias=alias, before=before))
        try:
            lib.SetActorStateValue(OwnerContext=actor, StateName=key, StateValue=value)
            after = str(lib.GetActorStateValue(OwnerContext=actor, StateName=key)[0])
            journal(dict(event='interaction_reset_returned', mission=name, alias=alias, after=after))
            if after.casefold() != 'false':
                raise RuntimeError('Switch did not return to its unused state')
        except Exception as exc:
            error = RuntimeError('Safehouse interaction reset unconfirmed; inspect before retrying')
            error.issued = True
            raise error from exc


def _queue_dependencies(owner, engine, name, children):
    job = owner._job
    snapshot = engine.snapshot()
    for child in children:
        if child in job['names']:
            continue
        try:
            completed = owner._state(owner._row(snapshot, child)) == 'completed'
        except ValueError:
            completed = False  # Availability is rechecked by the ordinary job path.
        if completed:
            continue
        job['names'].append(child)
        job['total'] = len(job['names'])
        job.setdefault('related_completion', []).append(child)
        owner._journal(dict(event='related_completion_queued', mission=child, parent=name))


def complete_dependencies(owner, engine, party, name):
    if owner._job.get('selection_scope') == 'challenge_credit':
        return
    import json
    from importlib.resources import files
    resources = files(__package__)
    dependencies = json.loads(resources.joinpath('mission_completion_dependencies.json').read_text())
    children = dependencies['missions'].get(name, ())
    reviewed = json.loads(resources.joinpath('travel_checkpoints.json').read_text())
    requirements = {key: address for key, (parent, address) in reviewed.items() if parent == name}
    claim_address = _world_safehouse_claim_address(name, resources)
    if name != BEACH and not claim_address and not children and not requirements:
        return
    snapshot = engine.snapshot()
    if owner._state(owner._row(snapshot, name)) != 'completed':
        title = 'Recruitment Drive' if name == BEACH else name
        raise RuntimeError('Complete ' + title + ' before repairing its related requirements')
    if claim_address:
        host = next(r['pc'] for r in party if r['host'])
        _verify_safehouse_claim(owner, host, name, claim_address)
    addresses = list(dict.fromkeys((CHECKPOINTS if name == BEACH else ()) + tuple(requirements.values())))
    if not addresses:
        _queue_dependencies(owner, engine, name, [r['mission'] for r in children])
        return
    target = next(r['pc'] for r in party if r['pc']._path_name() == owner._job['target'])
    import unrealsdk
    facts = unrealsdk.find_object('FactsBlueprintLibrary', '/Script/GbxGame.Default__FactsBlueprintLibrary')
    for address in addresses:
        def read():
            return str(facts.ReadFact(OwnerContext=target, AddressString=address,
                                   AsName='None', AsInt=0, AsBool=False)[1]).casefold()
        before = read()
        if before == 'completed':
            continue
        if before != 'none':
            raise RuntimeError('Unexpected mission prerequisite value; no change issued')
        owner._journal(dict(event='issued', mission=name, operation='completion_checkpoint',
                            address=address, before=before))
        try:
            facts.WriteFact(OwnerContext=target, AddressString=address,
                            AsName='Completed', AsInt=0, AsBool=False)
            after = read()
            owner._journal(dict(event='returned', mission=name, operation='completion_checkpoint',
                                address=address, after=after))
            if after != 'completed':
                raise RuntimeError('Mission prerequisite result unconfirmed')
        except Exception as exc:
            error = RuntimeError('Mission prerequisite result unconfirmed; inspect before continuing')
            error.issued = True
            raise error from exc
    for key in requirements:
        checked = owner._job.setdefault('checked_prerequisites', [])
        if key not in checked:
            checked.append(key)
    _queue_dependencies(owner, engine, name, [SAFEHOUSE] if name == BEACH else [r['mission'] for r in children])
