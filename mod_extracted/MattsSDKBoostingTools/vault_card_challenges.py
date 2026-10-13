"""Complete only the native current daily/weekly schedules, one game tick at a time.

VaultCardsManager supplies owned card definitions and active pool indices. Native
activation must settle before grants, and grants before completion readback.
Never use the entire rotation pool as a list of currently completable objectives.
"""
import time


def schedules(pc):
    manager = pc.VaultCardsManager
    if manager is None or not 0 < len(manager.VaultCards) <= 32:
        raise RuntimeError('Vault-card schedule is unavailable')
    result = []
    for card in manager.VaultCards:
        active, pool = [], []
        for kind in ('DailyChallenges', 'WeeklyChallenges'):
            definitions = getattr(card.VaultCardDef, kind).Challenges
            indices = list(getattr(card, kind).ActiveChallengeIndices)
            if len(definitions) > 4096 or len(indices) > 64 or len(indices) != len(set(indices)):
                raise RuntimeError('Unexpected vault-card challenge schedule')
            if any(i < 0 or i >= len(definitions) for i in indices):
                raise RuntimeError('Vault-card challenge index is outside its pool')
            pool.extend(str(h._name) for h in definitions)
            active.extend(str(definitions[i]._name) for i in indices)
        result.append(dict(card=str(card.VaultCardDef._name), names=active, pool=pool))
    if len({r['card'] for r in result}) != len(result):
        raise RuntimeError('Duplicate vault-card definitions')
    return result


def plan(rows, amounts, allowed):
    tasks, pools, active, skipped = [], set(), set(), []
    for row in rows:
        for card in schedules(row['pc']):
            pools.update(n.casefold() for n in card['pool'])
            if not allowed(row, card['card']):
                skipped.append(dict(player=row['label'], card=card['card'], reason='Content access not confirmed'))
                continue
            active.update(n.casefold() for n in card['names'])
            if any(n.casefold() not in amounts for n in card['names']):
                raise RuntimeError('Current vault-card challenge is missing its authored goal')
            tasks.append(dict(player_id=int(row['state'].PlayerId), player=row['label'],
                              controller=row['pc']._path_name(),
                              card=card['card'], names=card['names'],
                              amounts=[amounts[n.casefold()] for n in card['names']]))
    return dict(tasks=tasks, index=0, challenge_index=0, phase='ready', verified=0,
                skipped=skipped, inactive_count=len(pools-active)), pools


def _context(job, rows):
    task = job['tasks'][job['index']]
    matches = [r for r in rows if int(r['state'].PlayerId) == task['player_id']]
    if len(matches) != 1 or matches[0]['pc']._path_name() != task['controller']:
        raise RuntimeError('Vault-card player changed; no requests repeated')
    pc = matches[0]['pc']
    current = next((c for c in schedules(pc) if c['card'] == task['card']), None)
    if current is None or current['names'] != task['names']:
        raise RuntimeError('Vault-card schedule changed; start a fresh preview after reviewing issued work')
    manager = pc.VaultCardsManager
    definition = next(c.VaultCardDef for c in manager.VaultCards if str(c.VaultCardDef._name) == task['card'])
    return task, pc, manager, definition


def _progress(pc, name):
    from .challenge_objective_complete import _library
    from unrealsdk.unreal import FGameDataHandle
    args = dict(OakPC=pc, challenge=FGameDataHandle(16413, name))
    lib = _library()
    return bool(lib.IsChallengeCompleteForPlayer(**args)), int(lib.GetChallengeProgressForPlayer(**args))


def _frame():
    import unrealsdk
    library=unrealsdk.find_object('KismetSystemLibrary','/Script/Engine.Default__KismetSystemLibrary')
    return int(library.GetFrameCount())


def restore(job, rows, checkpoint):
    """Restore the selection even after a failed grant or explicit cancellation."""
    original = job.get('original')
    if original is None:
        return
    task = job['tasks'][job['index']]
    matches = [r for r in rows if int(r['state'].PlayerId) == task['player_id']]
    if len(matches) != 1 or matches[0]['pc']._path_name() != task['controller']:
        raise RuntimeError('Original vault-card player is unavailable for selection restoration')
    manager = matches[0]['pc'].VaultCardsManager
    if str(manager.ActivatedVaultCardDef._name) != original:
        definition = next((c.VaultCardDef for c in manager.VaultCards if str(c.VaultCardDef._name) == original), None)
        if definition is None:
            raise RuntimeError('Original vault card is unavailable for restoration: ' + original)
        job['restore_required'] = original
        checkpoint('restore_issued')
        manager.Server_ActivateVaultCard(VaultCardDefPtr=definition)
    if str(manager.ActivatedVaultCardDef._name) != original:
        raise RuntimeError('Original vault-card selection restoration is unconfirmed')
    job.pop('restore_required', None)
    job.pop('original', None)
    checkpoint('restored')


def step(job, rows, checkpoint):
    if job.get('restore_required') or job['phase'] == 'uncertain' or job['phase'].endswith('_issued'):
        raise RuntimeError('Vault-card request needs inspection; no calls repeated')
    if job['index'] >= len(job['tasks']):
        return True
    frame=_frame()
    if job.get('last_frame')==frame:
        return False
    job['last_frame']=frame
    try:
        task, pc, manager, definition = _context(job, rows)
        if job['phase'] == 'ready':
            # Completed schedules require neither activation nor another reward.
            if all(_progress(pc, n)[0] for n in task['names']):
                job['verified'] += len(task['names'])
                job['index'] += 1
                return job['index'] == len(job['tasks'])
            job['original'] = str(manager.ActivatedVaultCardDef._name)
            job['phase'] = 'activate_issued'
            checkpoint('activate_issued')
            manager.Server_ActivateVaultCard(VaultCardDefPtr=definition)
            job.update(phase='grant', challenge_index=0)
            return False
        if str(manager.ActivatedVaultCardDef._name) != task['card']:
            raise RuntimeError('Vault-card selection changed during completion')
        if job['challenge_index'] == len(task['names']):
            restore(job, rows, checkpoint)
            job.update(index=job['index']+1, phase='ready', challenge_index=0)
            return job['index'] == len(job['tasks'])
        name = task['names'][job['challenge_index']]
        complete, progress = _progress(pc, name)
        if complete:
            job['verified'] += 1
            job['challenge_index'] += 1
            job['phase'] = 'grant'
            return False
        if job['phase'] == 'verify':
            if time.monotonic()-job['issued_at'] > 5:
                raise RuntimeError('Vault-card completion is unconfirmed: ' + name)
            return False
        remaining = int(task['amounts'][job['challenge_index']])-progress
        if remaining <= 0 or progress < 0:
            raise RuntimeError('Vault-card progress disagrees with its completion state: ' + name)
        job.update(phase='increment_issued', issued_at=time.monotonic(), issued_name=name, issued_amount=remaining)
        checkpoint('increment_issued')
        pc.ServerIncrementChallengeForPlayer(name, remaining)
        job['phase'] = 'verify'
        return False
    except Exception:
        job['phase'] = 'uncertain'
        checkpoint('uncertain')
        restore(job, rows, checkpoint)
        raise
