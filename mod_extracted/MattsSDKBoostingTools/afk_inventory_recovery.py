"""Durable clear/deliver/restore transaction with saved item lists.

Failed transactions retain evidence without blocking future AFK sessions.
No Unreal calls live here. Advance only on the game tick with a pinned identity.
Interrupted operations are never automatically replayed after a process restart.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import uuid


FIELDS = ("serial", "quantity", "inventory_flags", "item_flags", "equip_slot",
          "slot_locked", "slot_max_quantity", "slot_type")


def _rows(snapshot):
    if snapshot.get("ok") is not True or snapshot.get("phase") != "complete":
        raise ValueError("A complete stable inventory capture is required")
    rows = snapshot["rows"]
    seen = set()
    for row in rows:
        if any(key not in row for key in FIELDS + ("handle", "instance_id")):
            raise ValueError("Inventory metadata is incomplete")
        if not isinstance(row["serial"], str) or not row["serial"].startswith("@U"):
            raise ValueError("Inventory serial is unavailable")
        if type(row["quantity"]) is not int or row["quantity"] < 1:
            raise ValueError("Inventory quantity is invalid")
        identity = row["handle"], row["instance_id"]
        if identity in seen:
            raise ValueError("Inventory identities are ambiguous")
        seen.add(identity)
    return rows


def item_counts(snapshot):
    counts = Counter()
    for row in _rows(snapshot):
        counts[row['serial']] += row['quantity']
    return counts


def verify_restored(original, delivered, final, *, restore_metadata=True):
    """Require original metadata plus exactly the intentionally delivered rows.

    Handles/instance IDs may be recreated; serial case, multiplicity and all
    captured metadata must match. No serial-only success or count-only success.
    """
    def counted(snapshot):
        return Counter(tuple(row[key] for key in FIELDS) for row in _rows(snapshot))
    measure = counted if restore_metadata else item_counts
    expected = measure(original) + measure(delivered)
    actual = measure(final)
    missing, unexpected = expected - actual, actual - expected
    return {"ok": not missing and not unexpected,
            "missing_rows": sum(missing.values()), "unexpected_rows": sum(unexpected.values())}


class Recovery:
    """One guest/session transaction with a persistent original inventory.

    Adapter contract: preflight(original) returns ok only after native clear
    scope, complete capture and metadata restore have been verified. begin()
    submits one operation; poll() returns None while pending, or an ok result.
    clear returns a stable empty snapshot; deliver returns the new loot snapshot;
    restore resends original rows with metadata; verify returns a final snapshot.
    All callbacks must be nonblocking and retain the pinned guest identity.
    """
    def __init__(self, directory, original, *, player_token, world_token, guest_name,
                 delivery_serials=(), restore_metadata=True):
        _rows(original)
        if player_token is None or world_token is None:
            raise ValueError("A pinned guest and world are required")
        if not all(isinstance(s, str) and s.startswith("@U") for s in delivery_serials):
            raise ValueError("Delivery serials must already be validated")
        self.player_token, self.world_token = player_token, world_token
        self.adapter = None
        self.pending = None
        self.path = Path(directory) / (uuid.uuid4().hex + '.json')
        self.record = {"schema": 1, "phase": "prepared", "guest_name": guest_name,
                       "original": deepcopy(original), "delivery_serials": list(delivery_serials),
                       "delivered": None, "retained": None,
                       "restore_metadata": restore_metadata, "error": "", "verification": None,
                       "restart_replay_allowed": False}
        self._save()
        self.export_lists()

    def export_lists(self):
        """Keep paste-ready originals and intended new loot separate for support.

        Export before mutation so even a crash leaves a usable original list.
        These are backups, never automatic redelivery instructions.
        """
        folder = self.path.parent / 'saved-item-lists' / self.path.stem
        folder.mkdir(parents=True, exist_ok=True)
        original = [row['serial'] for row in self.record['original']['rows']
                    for _ in range(row['quantity'])]
        for name, serials in (('original-backpack.txt', original),
                              ('selected-new-loot.txt', self.record['delivery_serials'])):
            (folder / name).write_text('\n'.join(serials) + ('\n' if serials else ''), encoding='utf-8')
        (folder / 'README.txt').write_text(
            'Player: ' + self.record['guest_name'] + '\n'
            'Original backpack: ' + str(len(original)) + ' items.\n'
            'Selected new loot: ' + str(len(self.record['delivery_serials'])) + ' items.\n'
            'These lists preserve duplicates and serial case. They do not prove what arrived.\n'
            'Keep the recovery JSON as evidence. Check with the player before resending to avoid duplicates.\n',
            encoding='utf-8')
        return folder

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self.record, sort_keys=True, ensure_ascii=False).encode('utf-8')
        envelope = json.dumps({"sha256": hashlib.sha256(payload).hexdigest(),
                               "payload": payload.decode('utf-8')}, ensure_ascii=False)
        temporary = self.path.with_suffix('.tmp')
        with temporary.open('w', encoding='utf-8') as stream:
            stream.write(envelope)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, self.path)

    @staticmethod
    def inspect(path):
        """Load recovery evidence, never resume a destructive operation."""
        envelope = json.loads(Path(path).read_text(encoding='utf-8'))
        payload = envelope['payload'].encode('utf-8')
        if hashlib.sha256(payload).hexdigest() != envelope['sha256']:
            raise ValueError('Recovery record checksum mismatch')
        record = json.loads(payload)
        _rows(record['original'])
        return record

    @staticmethod
    def unfinished(directory):
        """Find unresolved evidence for diagnostic review, not AFK startup."""
        for path in sorted(Path(directory).glob('*.json')):
            try:
                record = Recovery.inspect(path)
                if record.get('phase') == 'cancelled_before_clear':
                    continue
                if record.get('phase') != 'complete' or record.get('verification', {}).get('ok') is not True:
                    return str(path)
            except Exception:
                return str(path)
        return None

    def cancel_before_clear(self):
        if self.record['phase'] != 'prepared':
            return False
        self.record['phase'] = 'cancelled_before_clear'
        self.record['error'] = 'Cancelled before any inventory was cleared'
        self._save()
        return True

    @property
    def can_kick(self):
        return self.record['phase'] == 'complete' and self.record['verification']['ok'] is True

    def _block(self, reason):
        self.record['phase'] = 'blocked'
        self.record['error'] = reason
        self.record['reviewed_at_utc'] = datetime.now(timezone.utc).isoformat()
        self._save()
        self.export_review()

    def export_review(self):
        """Human-readable evidence for later repair, never a replay request."""
        folder = self.path.parent / 'saved-item-lists' / self.path.stem
        folder.mkdir(parents=True, exist_ok=True)
        final = self.record.get('final_snapshot')
        expected = item_counts(self.record['original']) + Counter(self.record['delivery_serials'])
        lines = [
            'Player: ' + self.record['guest_name'],
            'UTC: ' + self.record.get('reviewed_at_utc', ''),
            'Result: ' + self.record.get('error', ''),
            'AFK queue continues. This guest was not verified for automatic kick.',
            'Recovery evidence: ' + str(self.path),
            'Original items: original-backpack.txt',
            'Selected loot: selected-new-loot.txt',
            'Automatic deficit repair attempts: ' + str(self.record.get('repair_attempts', 0)),
        ]
        if final:
            actual = item_counts(final)
            for name, counts in (('observed-final-backpack', actual),
                                 ('unmatched-expected', expected - actual),
                                 ('unmatched-observed', actual - expected)):
                (folder / (name + '.txt')).write_text(
                    '\n'.join(counts.elements()) + '\n', encoding='utf-8')
            lines += ['Unmatched expected: ' + str(sum((expected-actual).values())),
                      'Unmatched observed: ' + str(sum((actual-expected).values()))]
        else:
            lines.append('Final inventory readback unavailable; arrival is unknown.')
        lines += ['Unmatched serials are NOT proven missing items. The game may change serial representation.',
                  'Check the player inventory before any resend. Do not clear or resend the entire backup blindly.']
        path = folder / 'RECOVERY-REVIEW.txt'
        path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        return path

    def advance(self, player_token, world_token, adapter):
        if self.record['phase'] in ('blocked', 'complete', 'cancelled_before_clear'):
            return
        if player_token != self.player_token or world_token != self.world_token:
            self._block('Guest left, changed character or world changed; recovery requires review')
            return
        try:
            if self.adapter is not None and adapter is not self.adapter:
                self._block('Recovery adapter changed; operation will not be replayed')
                return
            self.adapter = adapter
            phase = self.record['phase']
            if phase == 'prepared':
                result = adapter.preflight(deepcopy(self.record['original']))
                if result.get('ok') is not True:
                    if result.get('retry') is True:
                        return
                    self._block(result.get('message', 'Native restoration is not verified'))
                    return
                operation = 'clear'
            elif self.pending is not None:
                result = adapter.poll(self.pending, player_token, world_token)
                if result is None:
                    return
                if result.get('ok') is not True:
                    if phase == 'deliver_pending':
                        self.record['delivery_error'] = result.get('message', 'Selected loot delivery failed')
                        result = {'ok':True,'snapshot':{'ok':True,'phase':'complete','rows':[]}}
                    elif phase == 'restore_pending' and not self.record['restore_metadata']:
                        # Verification can repair an interrupted return from a
                        # fresh capture without repeating clear or all items.
                        self.record['restore_error'] = result.get('message', 'Original return interrupted')
                    else:
                        self._block(result.get('message', 'Recovery operation failed'))
                        return
                operation = phase.removesuffix('_pending')
                if operation == 'clear':
                    retained = result['snapshot']
                    if retained is None:
                        if self.record['restore_metadata'] or result.get('clear_submitted') is not True:
                            self._block('Clear outcome is unknown; backup retained')
                            return
                        # Native EmptyContainer can leave unreadable dead rows.
                        # Do not call those rows a verified empty snapshot. Return
                        # every original, then require exact final item counts.
                        self.record['clear_readback_verified'] = False
                        self.record['clear_readback_error'] = result.get('readback_error', '')
                        retained = {'ok':True,'phase':'complete','rows':[]}
                    else:
                        self.record['clear_readback_verified'] = True
                    _rows(retained)
                    if (self.record['restore_metadata'] and retained['rows']) or (
                            item_counts(retained) - item_counts(self.record['original'])):
                        self._block('Backpack clear was not confirmed; delivery stopped')
                        return
                    self.record['retained'] = deepcopy(retained)
                    operation = 'deliver'
                elif operation == 'deliver':
                    _rows(result['snapshot'])
                    self.record['delivered'] = deepcopy(result['snapshot'])
                    # Adapter must confirm the intended serial multiplicity too.
                    actual = Counter(r['serial'] for r in result['snapshot']['rows'])
                    if actual != Counter(self.record['delivery_serials']):
                        self.record['delivery_error'] = 'Delivered loot does not match the selected items'
                    operation = 'restore'
                elif operation == 'restore':
                    operation = 'verify'
                elif operation == 'verify':
                    self.record['final_snapshot'] = deepcopy(result['snapshot'])
                    check = verify_restored(self.record['original'], self.record['delivered'], result['snapshot'],
                                            restore_metadata=self.record['restore_metadata'])
                    if not self.record['restore_metadata']:
                        expected = item_counts(self.record['original']) + Counter(self.record['delivery_serials'])
                        actual = item_counts(result['snapshot'])
                        check = {'ok':actual == expected, 'missing_rows':sum((expected-actual).values()),
                                 'unexpected_rows':sum((actual-expected).values())}
                        self.record['repair_attempts'] = result.get('repair_attempts', 0)
                        if check['ok'] and result.get('delivery_reconciled') is True:
                            self.record.pop('delivery_error', None)
                    self.record['verification'] = check
                    if self.record.get('delivery_error'):
                        self._block(self.record['delivery_error'] + '; final inventory unverified, kick blocked')
                        return
                    if not check['ok']:
                        self._block('Original inventory restoration did not match; auto-kick blocked')
                        return
                    self.record['phase'] = 'complete'
                    self._save()
                    return
                self.pending = None
            else:
                self._block('An interrupted operation cannot be replayed automatically')
                return
            # Persist intent BEFORE the native operation. A crash here must lead
            # to review, not an automatic repeated clear or duplicate delivery.
            self.record['phase'] = operation + '_pending'
            self._save()
            self.pending = adapter.begin(operation, deepcopy(self.record), player_token, world_token)
            if self.pending is None:
                self._block('Operation did not return a tracking token; outcome unknown')
        except Exception as exc:
            if self.record['phase'] == 'deliver_pending' and self.record['retained'] is not None:
                self.record['delivery_error'] = 'Selected loot interrupted: ' + type(exc).__name__
                self.record['delivered'] = {'ok':True,'phase':'complete','rows':[]}
                self.record['phase'] = 'restore_pending'
                try:
                    self._save()
                    self.pending = adapter.begin('restore',deepcopy(self.record),player_token,world_token)
                    if self.pending is not None:
                        return
                except Exception:
                    pass
            self._block('Recovery stopped: ' + type(exc).__name__)
