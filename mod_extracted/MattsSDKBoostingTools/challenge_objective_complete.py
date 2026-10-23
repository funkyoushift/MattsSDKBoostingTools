"""Read native challenge completion; never fabricate objective bit arrays.

The installed ChallengeObjectiveState.CompletedObjectives is a
GbxReplicatedBitArray, not a Python list. Appending empty challenge rows or
filling guessed bits does not complete the native challenge. Evidence:
docs/changes/2026-10-13-completion-and-ui-verification.md.
"""


def _library():
    import unrealsdk
    return unrealsdk.find_object('OakChallengeBlueprintLibrary',
        '/Script/OakGame.Default__OakChallengeBlueprintLibrary')


def is_complete(controller, name):
    from unrealsdk.unreal import FGameDataHandle
    return bool(_library().IsChallengeCompleteForPlayer(
        OakPC=controller, challenge=FGameDataHandle(16413, name)))


def inspect_batch(engine, controller, names):
    """Read a bounded batch from the current player's actual definition table."""
    if len(names) > 64:
        raise ValueError('Challenge readback is limited to 64 definitions per batch')
    from .mission_challenges import sparse_entries, _name
    from unrealsdk.unreal import FGameDataHandle
    engine.ensure_world()
    if controller.PlayerState is None or controller.OakChallengeManager is None:
        raise RuntimeError('Challenge player is not ready for readback')
    manager = controller.OakChallengeManager._get_address()
    definitions = {engine.read(p, 8) for p in
        sparse_entries(engine, manager + 0x290, 24, 10000)}
    lib = _library()
    result = []
    for name in names:
        exists = _name(engine, name) in definitions
        complete = bool(lib.IsChallengeCompleteForPlayer(
            OakPC=controller, challenge=FGameDataHandle(16413, name))) if exists else False
        result.append(dict(name=name, exists=exists, complete=complete))
    return result


def inspect_exact_progress(engine, controller, names):
    """Read bounded current-build challenge records without changing progress."""
    import struct
    from .mission_challenges import sparse_entries, _name
    from unrealsdk.unreal import FGameDataHandle

    if not isinstance(names, list) or not 1 <= len(names) <= 8 or any(
            not isinstance(name, str) or not name or len(name) > 160 for name in names):
        raise ValueError('Inspect one to eight challenge names')
    if getattr(engine,'profile',None)!='steam-26007962':
        raise RuntimeError('Exact challenge record layout is unqualified for this game build')
    engine.ensure_world()
    if controller.PlayerState is None or controller.Pawn is None or controller.OakChallengeManager is None or not controller.HasAuthority():
        raise RuntimeError('Challenge player is not ready for readback')
    manager = controller.OakChallengeManager._get_address()
    state = controller.PlayerState._get_address()
    pid = int(controller.PlayerState.PlayerId)
    if struct.unpack('<i', engine.read(state + 0x394, 4))[0] != pid:
        raise RuntimeError('Challenge player identity differs from reflected identity')
    definitions = {}
    for address in sparse_entries(engine, manager + 0x290, 24, 10000):
        definitions.setdefault(engine.read(address, 8), []).append(engine.u64(address + 8))
    selected_entries = {}
    for name in names:
        matches = definitions.get(_name(engine, name), [])
        if len(matches) == 1:
            selected_entries[matches[0]] = name
    all_entries = {entry for matches in definitions.values() for entry in matches}
    relationships = {}
    for address in sparse_entries(engine, manager + 0x2e0, 32, 10000):
        child = engine.u64(address)
        if child not in selected_entries:
            continue
        parent_data, parent_count = engine.array(address + 8, 64)
        related = []
        for index in range(parent_count):
            parent = engine.u64(parent_data + index * 8)
            if parent not in all_entries:
                raise RuntimeError('Challenge relationship points outside definition table')
            parent_definition = engine.u64(parent)
            related.append(dict(challenge=selected_entries.get(parent),
                                definition_type=engine.read(parent_definition + 0x160, 1)[0]))
        relationships[child] = related
    players = [address for address in sparse_entries(engine, manager + 0x3d8, 96, 16)
               if struct.unpack('<i', engine.read(address, 4))[0] == pid]
    if len(players) != 1:
        raise RuntimeError('Challenge player progress map is missing or ambiguous')
    progress = {}
    for address in sparse_entries(engine, players[0] + 8, 24, 10000):
        progress.setdefault(engine.u64(address), []).append(engine.u64(address + 8))
    lib = _library()
    results = []
    for name in names:
        entries = definitions.get(_name(engine, name), [])
        if len(entries) != 1:
            results.append(dict(challenge=name, exists=False, reason='Definition missing or ambiguous'))
            continue
        records = progress.get(entries[0], [])
        if len(records) != 1:
            results.append(dict(challenge=name, exists=True, progress_present=False,
                                reason='Progress record missing or ambiguous'))
            continue
        definition = engine.u64(entries[0])
        tier_count = engine.read(definition + 0x4a0, 1)[0]
        if tier_count > 32:
            raise RuntimeError('Challenge tier count exceeds diagnostic bound')
        tier_data = engine.u64(definition + 0x498)
        if tier_count and not tier_data:
            raise RuntimeError('Challenge tier pointer is missing')
        tier_goals = [engine.u64(tier_data + index * 0x50) for index in range(tier_count)]
        final_goal = tier_goals[-1] if tier_goals else None
        # The current executable's challenge initializer reads this linked
        # reference before checking per-player shared membership. Capture its
        # stored bytes only; resolving the reference could load game data.
        linked_reference = engine.read(definition + 0x120, 0x18)
        linked_reference_cached = bool(struct.unpack('<Q', linked_reference[0x10:0x18])[0])
        record = records[0]
        raw = engine.read(record + 0x10, 0x1c)
        handle = FGameDataHandle(16413, name)
        results.append(dict(challenge=name, exists=True, progress_present=True,
                            definition_type=engine.read(definition + 0x160, 1)[0],
                            definition_flags=engine.read(definition + 0x160, 8).hex(),
                            tier_count=tier_count,tier_goals=tier_goals,final_goal=final_goal,
                            linked_reference_raw=linked_reference[:0x10].hex(),
                            linked_reference_cached=linked_reference_cached,
                            related_parents=relationships.get(entries[0],[]),
                            native_count=int(lib.GetChallengeProgressForPlayer(OakPC=controller, challenge=handle)),
                            record_count=struct.unpack('<q', engine.read(record, 8))[0],
                            native_complete=bool(lib.IsChallengeCompleteForPlayer(OakPC=controller, challenge=handle)),
                            record_bytes_10_2b=raw.hex(),
                            gate_11=raw[1], gate_18=struct.unpack('<i', raw[8:12])[0],
                            gate_28=raw[0x18]))
    return results


def reconcile_after_bulk(controller, granted_tokens):
    """Report native state without appending or editing replicated rows."""
    names = set(granted_tokens)
    if not names:
        return 'No challenge requests to verify.'
    completed = sum(is_complete(controller, name) for name in names)
    return (f'Native completion confirmed for {completed}/{len(names)} requested challenges; '
            'other definitions may be unavailable, repeatable, scheduled, or incomplete. '
            'Saved guest progress remains unverified.')
