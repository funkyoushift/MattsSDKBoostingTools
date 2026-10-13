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


def _reset_stored_fact(name, address, allowed, value, journal):
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
    if before in ('None', value):
        journal(dict(event='stored_interaction_unchanged', mission=name, address=address, before=before))
        return
    if before not in allowed:
        raise RuntimeError('Unknown stored activity state; reset not issued')
    journal(dict(event='stored_interaction_reset_issued', mission=name, address=address, before=before))
    try:
        lib.WriteFact(OwnerContext=pc, AddressString=address, AsName=value, AsInt=0, AsBool=False)
        after = read()
        journal(dict(event='stored_interaction_reset_returned', mission=name, address=address, after=after))
        if after != value:
            raise RuntimeError('Stored activity state did not reset')
    except Exception as exc:
        error = RuntimeError('Stored activity reset unconfirmed; inspect before retrying')
        error.issued = True
        raise error from exc


def reset_activity_state(name, journal):
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
              if str(a.FactsConduit.GroupName.Name) == identity.get('groupname', 'None')
              and str(a.FactsConduit.RegistryName.Name.Name) == identity['registryname']]
    if not actors:
        address = '.'.join(('registry', identity['map'], 'top',
                            identity.get('groupname', 'None'), identity['registryname'], 'State'))
        _reset_stored_fact(name, address, ('Claimed', 'Claimable'), 'Initialization', journal)
        return
    if len(actors) != 1:
        raise RuntimeError('Activity actor identity is ambiguous; reset not issued')
    actor = actors[0]
    lib = unrealsdk.find_object('GbxActorStateBlueprintLibrary',
                               '/Script/GbxEngine.Default__GbxActorStateBlueprintLibrary')
    key = unrealsdk.make_struct('/Script/GbxEngine.GbxActorStateMachineKey', Name='State', Index=0)
    states = lib.GetActorStateMachineStates(OwnerContext=actor, StateMachine=key)[0]
    initial = [s for s in states if str(s.Name) == 'Initialization']
    if len(initial) != 1:
        raise RuntimeError('Activity has no known initialization state; reset not issued')
    before = str(lib.GetActorStateValue(OwnerContext=actor, StateName=key)[0])
    if before == 'Initialization':
        return
    journal(dict(event='activity_reset_issued', mission=name, before=before))
    try:
        lib.SetActorStateValue(OwnerContext=actor, StateName=key, StateValue=initial[0])
        after = str(lib.GetActorStateValue(OwnerContext=actor, StateName=key)[0])
        journal(dict(event='activity_reset_returned', mission=name, after=after))
        if after != 'Initialization':
            raise RuntimeError('Activity initialization not confirmed')
    except Exception as exc:
        error = RuntimeError('Activity reset unconfirmed; inspect before retrying')
        error.issued = True
        raise error from exc


def reset_interactions(name, journal, objective=None):
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
        if current not in ('TRUE', 'FALSE'):
            raise RuntimeError('Unknown safehouse switch state; reset not issued')
        actors[alias] = (actor, current)
    for alias in names:
        if alias not in actors:
            identity = identities[alias]
            address = '.'.join(('registry', identity['map'], 'top',
                                identity.get('groupname', 'None'), alias, 'Pressed'))
            _reset_stored_fact(name, address, ('TRUE',), 'FALSE', journal)
            continue
        actor, before = actors[alias]
        if before == 'FALSE':
            continue
        journal(dict(event='interaction_reset_issued', mission=name, alias=alias, before=before))
        try:
            lib.SetActorStateValue(OwnerContext=actor, StateName=key, StateValue=value)
            after = str(lib.GetActorStateValue(OwnerContext=actor, StateName=key)[0])
            journal(dict(event='interaction_reset_returned', mission=name, alias=alias, after=after))
            if after != 'FALSE':
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
    if name != BEACH and not children and not requirements:
        return
    snapshot = engine.snapshot()
    if owner._state(owner._row(snapshot, name)) != 'completed':
        title = 'Recruitment Drive' if name == BEACH else name
        raise RuntimeError('Complete ' + title + ' before repairing its related requirements')
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
