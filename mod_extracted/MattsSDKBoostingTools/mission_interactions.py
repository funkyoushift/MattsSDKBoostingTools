"""Use authored NPC talk targets through the normal player interaction path.

Calling an objective's outcome does not simulate using its NPC. The Rescue's
InstructMrChew advanced through ServerUseObject after its normal scene reload;
forcing that objective's outcome stranded its scene. See the verification note.
"""


def prepare(objective):
    """Return an immediate callable, False while loading, or None for other types.

    No captured UObject survives the calling game-thread step. Missing or
    ambiguous talk targets never fall back to an objective outcome call.
    """
    interaction=objective.get('interaction')
    if not interaction:return None
    if interaction.get('kind')!='talk':raise RuntimeError('Unknown mission interaction type')
    identity=interaction.get('actor') or {}
    name=identity.get('registryname')
    if not name:raise RuntimeError('The authored NPC talk target is unresolved')
    import unrealsdk
    from mods_base import get_pc
    from .mission_completion_context import world,map_name
    from .mission_completion_placement import _same_world
    w=world();pc=get_pc()
    if w is None or pc is None or pc.Pawn is None:return False
    if identity.get('map') and identity['map'].casefold()!=map_name(w):return False
    prefix=w._path_name()+':'
    if not pc._path_name().startswith(prefix):return False
    matches=[]
    for actor in unrealsdk.find_all('OakCharacter',exact=False):
        if not _same_world(actor,w) or actor.IsActorBeingDestroyed():continue
        conduit=actor.FactsConduit
        if str(conduit.RegistryName.Name.Name).casefold()!=name.casefold():continue
        group=identity.get('groupname')
        if group and str(conduit.GroupName.Name).casefold()!=group.casefold():continue
        matches.append(actor)
    if len(matches)>1:raise RuntimeError('The authored NPC talk target is ambiguous')
    if not matches:return False
    actor=matches[0]
    if pc.ClientCanUseObjectsLock.bLocked or actor.UsableActorState.bInteractabilityLockedReplicated:return False
    # Primary use (0), non-held: same call verified on the live Talk prompt.
    return lambda:pc.ServerUseObject(Usable=actor,UseType=0,bWasHeld=False)
