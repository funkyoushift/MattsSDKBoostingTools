"""Tested Mayhem unlock workflow; invoke only on the backend game thread.

Evidence and scope: docs/changes/2026-10-09-mayhem-progression-discovery.md.
Mission/global facts are shared lobby state, not a private guest registry.
This does not complete the combat mission or write active difficulty.
"""
import unrealsdk

MAX_RANK = 20
INTRO_STATUS = 'Missions.MissionSet_DLC_Tuba.Mission_DLC_Tuba.Status'
HIGHEST_RANK = 'global.highest_unlocked_mayhem_level'


def boost(pc, rank, label):
    if isinstance(rank, bool) or not str(rank).strip().isdigit():
        raise ValueError('Mayhem rank must be a whole number from 1 to 20')
    rank = int(rank)
    if not 1 <= rank <= MAX_RANK:
        raise ValueError('Mayhem rank must be from 1 to 20')
    if pc is None or not pc.HasAuthority() or pc.Pawn is None:
        raise RuntimeError('Load the selected player in your hosted world first')
    ps = pc.PlayerState
    if ps is None:
        raise RuntimeError('Selected player state is unavailable')
    facts = unrealsdk.find_object(
        'FactsBlueprintLibrary', '/Script/GbxGame.Default__FactsBlueprintLibrary')
    if facts is None:
        raise RuntimeError('Mayhem progression interface is unavailable')
    # Preflight all required fields before the first write. Never reduce unlocks.
    before = int(ps.HighestUnlockedMayhemLevel)
    previous = facts.ReadFact(OwnerContext=pc, AddressString=HIGHEST_RANK,
                              AsName='None', AsInt=0, AsBool=False)
    intro = facts.ReadFact(OwnerContext=pc, AddressString=INTRO_STATUS,
                           AsName='None', AsInt=0, AsBool=False)
    target = max(before, rank)
    lobby_rank = max(int(previous[2]), target)
    applied = []
    try:
        ps.HighestUnlockedMayhemLevel = target
        applied.append('player rank')
        if int(previous[2]) != lobby_rank:
            facts.WriteFact(OwnerContext=pc, AddressString=HIGHEST_RANK,
                            AsName='None', AsInt=lobby_rank, AsBool=False)
            applied.append('lobby rank access')
        if str(intro[1]).casefold() != 'completed':
            facts.WriteFact(OwnerContext=pc, AddressString=INTRO_STATUS,
                            AsName='Completed', AsInt=0, AsBool=False)
            applied.append('Takedown prerequisite')
        actual = int(ps.HighestUnlockedMayhemLevel)
        highest = facts.ReadFact(OwnerContext=pc, AddressString=HIGHEST_RANK,
                                 AsName='None', AsInt=0, AsBool=False)
        complete = facts.ReadFact(OwnerContext=pc, AddressString=INTRO_STATUS,
                                  AsName='None', AsInt=0, AsBool=False)
        if actual != target or int(highest[2]) < target or str(complete[1]).casefold() != 'completed':
            raise RuntimeError('Unlock readback did not match the requested progress')
    except Exception as exc:
        # Mission facts can trigger downstream changes. Do not pretend a scalar
        # rollback undoes them or silently repeat an uncertain partial operation.
        return dict(ok=False, target=label, applied=applied,
                    message=f'Mayhem boost for {label} was not fully verified: {exc}. Refresh before retrying.')
    return dict(ok=True, target=label, before=before, rank=actual,
                lobby_unlock_rank=int(highest[2]), prerequisite_completed=True,
                message=f'{label}: Mayhem unlocked through rank {actual}. '
                        'Takedown access is enabled for this lobby; active difficulty is unchanged. '
                        'Reopen the terminal. Save/quit normally to keep progress.')
