"""Cooperative, character-budgeted delivery. This module has no game imports."""
from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path

CHARACTER_BUDGET = 8192
CHUNK_PAUSE = 0.75
ITEM_GAP = 0.008
SETTLE_SECONDS = 3.0


def partition_serials(serials):
    """Reject unsupported entries without altering any code or reordering valid ones."""
    accepted, rejected = [], []
    for index, serial in enumerate(serials):
        reason = ''
        if not isinstance(serial, str) or not serial.startswith('@U') or not serial.isascii():
            reason = 'Direct delivery requires an ASCII encoded @U item code'
        elif len(serial) > CHARACTER_BUDGET:
            reason = f'{len(serial)} characters exceeds the tested {CHARACTER_BUDGET}-character per-item limit'
        if reason:
            rejected.append({'index':index, 'reason':reason})
        else:
            accepted.append(serial)
    return accepted, rejected


def chunks_for(serials):
    chunks, chunk, size = [], [], 0
    for serial in serials:
        if not isinstance(serial, str) or not serial.startswith('@U') or not serial.isascii():
            raise ValueError('Direct delivery requires encoded @U item codes')
        length = len(serial)
        if length > CHARACTER_BUDGET:
            raise ValueError(f'Item code exceeds the supported {CHARACTER_BUDGET}-character limit')
        if chunk and size + length > CHARACTER_BUDGET:
            chunks.append(chunk)
            chunk, size = [], 0
        chunk.append(serial)
        size += length
    if chunk:
        chunks.append(chunk)
    return chunks


class Journal:
    """Keep requested codes plus an append-only attempt log; never replay it automatically."""
    def __init__(self, serials, targets, scope, directory=None, rejected=None):
        if directory is None:
            directory = Path(os.environ['LOCALAPPDATA']) / 'MattsSDKBoostingTools' / 'direct-delivery-reports'
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        self.id = uuid.uuid4().hex
        self.path = directory / (self.id + '.jsonl')
        manifest = directory / (self.id + '.json')
        with manifest.open('x', encoding='utf-8') as stream:
            json.dump({'id':self.id, 'created':time.time(), 'scope':scope, 'serials':serials,
                       'targets':targets, 'rejected':list(rejected or []), 'guest_save_verified':False,
                       'settings':{'character_budget':CHARACTER_BUDGET, 'chunk_pause':CHUNK_PAUSE,
                                   'item_gap':ITEM_GAP, 'settle_seconds':SETTLE_SECONDS}}, stream)
        self.event('queued')

    def event(self, event, **data):
        with self.path.open('a', encoding='utf-8') as stream:
            stream.write(json.dumps({'time':time.time(), 'event':event, **data}) + '\n')
            stream.flush()


class Delivery:
    def __init__(self, serials, targets, resolve, add, journal, clock=time.monotonic, rejected=None):
        self.rejected = list(rejected or [])
        self.chunks = chunks_for(serials)
        if not self.chunks or not targets:
            raise ValueError('Direct delivery needs items and loaded targets')
        self.serials = list(serials)
        self.ends, count = [], 0
        for chunk in self.chunks:
            count += len(chunk)
            self.ends.append(count)
        self.targets = [dict(target, sent=0, chunk=0, ready=0.0, done=False, error='') for target in targets]
        self.resolve, self.add, self.journal, self.clock = resolve, add, journal, clock
        self.turn, self.next = 0, 0.0
        self.done, self.busy = False, False

    @property
    def error(self):
        return '; '.join(f"{t['name']}: {t['error']}" for t in self.targets if t['error'])

    def cancel(self, reason):
        for target in self.targets:
            if not target['done']:
                target['error'], target['done'] = reason, True
        self.done = True
        self.journal.event('cancelled', reason=reason)

    def step(self):
        now = self.clock()
        if self.done or self.busy or now < self.next:
            return False
        self.busy = True
        changed = False
        try:
            for offset in range(len(self.targets)):
                i = (self.turn + offset) % len(self.targets)
                target = self.targets[i]
                if target['done'] or now < target['ready']:
                    continue
                changed = True
                attempted = False
                try:
                    pc = self.resolve(target)  # Exact original identity, even during settlement.
                    if target['sent'] == len(self.serials):
                        self.journal.event('settled', target=i, submitted=target['sent'], guest_save_verified=False)
                        target['done'] = True
                        continue
                    index = target['sent']
                    # Record the uncertain boundary BEFORE constructing/inserting. No automatic retry.
                    self.journal.event('attempt', target=i, index=index)
                    attempted = True
                    self.add(pc, self.serials[index])
                    target['sent'] += 1
                    self.journal.event('returned', target=i, index=index)
                    after = self.clock()
                    if target['sent'] == self.ends[target['chunk']]:
                        target['chunk'] += 1
                        target['ready'] = after + CHUNK_PAUSE
                    if target['sent'] == len(self.serials):
                        target['ready'] = after + SETTLE_SECONDS
                    self.next = after + ITEM_GAP
                    self.turn = (i + 1) % len(self.targets)
                    break  # At most ONE insertion across ALL players in this callback.
                except Exception as exc:
                    target['error'], target['done'] = str(exc), True
                    try:
                        self.journal.event('failed', target=i, submitted=target['sent'], error=str(exc))
                    except Exception:
                        pass  # Do not retry an uncertain mutation if the report disk fails.
                    if attempted:
                        self.next = self.clock() + ITEM_GAP
                        self.turn = (i + 1) % len(self.targets)
                        break
            self.done = all(t['done'] for t in self.targets)
            return changed
        finally:
            self.busy = False

    def progress(self, scope):
        total = len(self.serials) * len(self.targets)
        sent = sum(t['sent'] for t in self.targets)
        waiting = sent == total and not self.done
        stage = ('failed' if self.error else 'complete') if self.done else ('settling' if waiting else 'deliver')
        fraction = 1.0 if self.done and not self.error else min(0.99, sent / total)
        message = (f'Direct delivery: {sent}/{total} item additions submitted to {scope}. '
                   + ('Settling before completion.' if waiting else 'Guest saves are not verified.'))
        if self.rejected:
            message += f' Skipped {len(self.rejected)} unsupported item code(s); see delivery report.'
        if self.error:
            message += ' ' + self.error
        return {'active':not self.done, 'stage':stage, 'method':'direct', 'message':message,
                'last_message':message, 'last_error':self.error, 'fraction':fraction,
                'percent':round(fraction*100), 'label':f'{sent}/{total}',
                'target_label':scope, 'total_serials':len(self.serials),
                'total_chunks':len(self.chunks), 'current_chunk':min(t['chunk'] for t in self.targets),
                'current_chunk_serials':0, 'expected_targets':len(self.targets),
                'patched_targets':0, 'opened_managers':0, 'guest_save_verified':False,
                'report_path':str(self.journal.path), 'skipped_count':len(self.rejected),
                'skipped_items':self.rejected,
                'next_delay_seconds':max(0.0,min((t['ready'] for t in self.targets if not t['done']),default=0)-self.clock()),
                'players':[{'name':t['name'], 'submitted':t['sent'], 'total':len(self.serials),
                            'done':t['done'], 'error':t['error']} for t in self.targets]}
