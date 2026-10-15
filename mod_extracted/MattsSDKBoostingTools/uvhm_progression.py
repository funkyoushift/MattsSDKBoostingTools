"""Verify one UVHM native challenge before issuing a later challenge.

Native state is read through IsChallengeCompleteForPlayer. It does not prove a
remote guest's saved rank. Polling bounds are operational, not native unlock
rules. No replicated completion arrays or guessed rank fields are assigned.
"""
VERIFY_TIMEOUT = 30.0


def _identity(pc):
    if pc is None or pc.Pawn is None or pc.PlayerState is None or not pc.HasAuthority():
        raise RuntimeError('UVHM player is unavailable in the hosted world')
    return (pc._get_address(), pc._path_name(), pc.PlayerState._get_address())


def _complete(pc, name):
    from .challenge_objective_complete import is_complete
    return is_complete(pc, name)


def advance(pc, name, receipt, now, delay):
    """True confirms current native completion; False means keep polling."""
    identity = _identity(pc)
    if receipt:
        if receipt['challenge'] != name or tuple(receipt['player']) != identity:
            raise RuntimeError('UVHM target or challenge changed; no request repeated')
        if receipt['state'] == 'uncertain':
            raise RuntimeError('UVHM request result is uncertain; no automatic retry')
        if receipt['state'] == 'verified':
            return True
        if now < receipt['next_at']:
            return False
        if _complete(pc, name):
            receipt['state'] = 'verified'
            return True
        if now >= receipt['deadline']:
            receipt['state'] = 'uncertain'
            raise RuntimeError(name+': native completion not confirmed; later UVHM steps were not sent. Saved guest rank remains unverified.')
        return False
    if _complete(pc, name):
        receipt.update(challenge=name, player=identity, state='verified', sent=False)
        return True
    receipt.update(challenge=name, player=identity, state='issued', sent=True,
                   next_at=now+delay, deadline=now+VERIFY_TIMEOUT)
    try:
        pc.ServerIncrementChallengeForPlayer(name, 1)
    except Exception:
        receipt['state'] = 'uncertain'
        raise
    return False
