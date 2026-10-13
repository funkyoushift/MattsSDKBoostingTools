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


def reconcile_after_bulk(controller, granted_tokens):
    """Report native state without appending or editing replicated rows."""
    names = set(granted_tokens)
    if not names:
        return 'No challenge requests to verify.'
    completed = sum(is_complete(controller, name) for name in names)
    return (f'Native completion confirmed for {completed}/{len(names)} requested challenges; '
            'other definitions may be unavailable, repeatable, scheduled, or incomplete. '
            'Saved guest progress remains unverified.')
