"""Unreleased read-only capture for AFK inventory-preservation research.

Uses extracted native field names; never empties, removes, spawns or equips items.
Two matching passes mean only that these reads agreed, not that a restore is safe.
Call step() from the game tick with the same resolved player, after join readiness.
"""
from __future__ import annotations


class NativeReadError(ValueError):
    pass


def _field(value, path, convert=None):
    try:
        for part in path.split("."):
            value = getattr(value, part)
        return convert(value) if convert else value
    except Exception:
        raise NativeReadError(f"Native field unavailable: {path}") from None


def _native_serial(identity):
    from .item_serial_reader import item_identity_serial_info
    return item_identity_serial_info(identity).get("serial", "")


def inventory_api_names(statics=None):
    """List native API names for research without invoking inventory methods."""
    if statics is None:
        from .streamer_chaos import _inventory_statics
        statics = _inventory_statics()
    if statics is None:
        return {"ok": False, "message": "Native inventory statics are unavailable"}
    terms = ("item", "inventory", "container", "remove", "consume", "destroy")
    names = sorted(name for name in dir(statics) if not name.startswith("_")
                   and any(term in name.lower() for term in terms))
    return {"ok": True, "class": str(statics.Class.Name), "names": names,
            "message": "Names only; no inventory methods were invoked", "cleanup_allowed": False}


def restoration_api_schema(find_class=None):
    """Read reflected function signatures, never invoke a game function.

    Reflection access uses the installed SDK's documented UStruct/UFunction
    interfaces. Signatures provide research leads, not proof of safe writes.
    """
    if find_class is None:
        from unrealsdk import find_class
    result = []
    errors = []
    terms = ('inventory', 'backpack', 'equip', 'item', 'flag', 'favorite')
    for name in ('OakInventoryStatics', 'OakPlayerState', 'OakPlayerController'):
        try:
            cls = find_class(name)
            for owner in cls._superfields():
                for field in owner._fields():
                    if not any(term in str(field.Name).lower() for term in terms):
                        continue
                    # Fields which are not UFunctions have no NumParams.
                    try:
                        param_count = int(field.NumParams)
                    except AttributeError:
                        continue
                    parameters = []
                    for prop in field._properties():
                        parameters.append({'name': str(prop.Name), 'type': type(prop).__name__,
                                           'flags': int(prop.PropertyFlags),
                                           'offset': int(prop.Offset_Internal),
                                           'element_size': int(prop.ElementSize)})
                    result.append({'requested_class': name, 'owner': str(owner.Name),
                                   'function': str(field.Name), 'path': str(field._path_name()),
                                   'flags': int(field.FunctionFlags), 'parameter_count': param_count,
                                   'parameters': parameters})
        except Exception as exc:
            errors.append({'class': name, 'error': type(exc).__name__})
    return {'ok': not errors, 'functions': result, 'errors': errors,
            'cleanup_allowed': False, 'restoration_verified': False,
            'message': 'Reflection metadata only; no inventory or equipment functions invoked'}


def _read_row(row, serial_reader):
    inventory = _field(row, "InventoryItem")
    item = _field(inventory, "item")
    serial = serial_reader(_field(item, "data.Identity"))
    if not isinstance(serial, str) or not serial.startswith("@U"):
        raise NativeReadError("Item serial unavailable; empty-slot interpretation is unverified")
    # Native metadata stays separate from the serial. No guessed flag meanings.
    return {
        "serial": serial,
        "handle": _field(inventory, "Handle.Handle", int),
        "instance_id": _field(item, "data.InstanceId", int),
        "inventory_flags": _field(inventory, "Flags", int),
        "equip_slot": _field(inventory, "EquipSlot", int),
        "quantity": _field(item, "State.Quantity", int),
        "item_flags": _field(item, "State.Flags", int),
        "slot_locked": _field(row, "IsLocked", bool),
        "slot_max_quantity": _field(row, "MaxQuantity", int),
        "slot_type": _field(row, "type", str),
    }


class Capture:
    """Bounded, uncapped, duplicate-preserving native row capture.

    No party-index lookup: the caller must keep the original player identity.
    Any unreadable row or changing inventory invalidates the entire capture.
    Empty containers remain observations, not proof that a guest save is loaded.
    """
    def __init__(self, player_state, *, batch_size=16, serial_reader=None):
        if player_state is None:
            raise ValueError("A resolved player state is required")
        if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size < 1:
            raise ValueError("batch_size must be a positive integer")
        self.player_state = player_state
        self.batch_size = batch_size
        self.serial_reader = serial_reader or _native_serial
        self.phase = "capture"
        self.cursor = 0
        self.expected_rows = None
        self.records = []
        self.error = ""
        self.error_index = None
        self.reads = 0
        self.done = False

    def _fail(self, message, index=None):
        self.error = message
        self.error_index = index
        self.records.clear()
        self.done = True
        self.phase = "failed"
        return self.status()

    def step(self, current_player_state):
        if self.done:
            return self.status()
        if current_player_state != self.player_state:
            return self._fail("Player changed or left; capture cancelled")
        try:
            rows = current_player_state.BackpackItems.items
            row_count = len(rows)
        except Exception:
            return self._fail("Native backpack container could not be read")
        if self.expected_rows is None:
            self.expected_rows = row_count
        if row_count != self.expected_rows:
            return self._fail("Inventory row count changed; capture discarded")
        for _ in range(self.batch_size):
            if self.cursor >= row_count:
                if self.phase == "capture":
                    self.phase = "verify"
                    self.cursor = 0
                    # Start the verification pass on a later tick, including
                    # empty containers. Never loop through both passes at once.
                    return self.status()
                self.done = True
                self.phase = "complete"
                return self.status()
            index = self.cursor
            try:
                record = _read_row(rows[index], self.serial_reader)
            except NativeReadError as exc:
                return self._fail(str(exc), index)
            except Exception:
                return self._fail("Inventory row or serial could not be fully read", index)
            self.reads += 1
            if self.phase == "capture":
                self.records.append(record)
            elif record != self.records[index]:
                return self._fail("Inventory contents changed; capture discarded", index)
            self.cursor += 1
        return self.status()

    def status(self):
        return {"phase": self.phase, "done": self.done, "ok": self.phase == "complete",
                "expected_rows": self.expected_rows, "rows_read": self.reads,
                "error": self.error, "error_index": self.error_index,
                # No downstream caller may treat this experimental capture as
                # authorization or proof for deletion or restoration.
                "restoration_verified": False, "cleanup_allowed": False}

    def snapshot(self):
        if self.phase != "complete":
            raise RuntimeError("No complete stable capture is available")
        return {**self.status(), "rows": [dict(record) for record in self.records]}


def compare_captures(before, after):
    """Describe two captures, never infer which additions are reward-generated."""
    if not before.get("ok") or not after.get("ok"):
        raise ValueError("Both captures must be complete")
    def indexed(snapshot):
        result = {}
        for row in snapshot["rows"]:
            key = (row["handle"], row["instance_id"])
            if key in result:
                raise ValueError("Repeated native item identity; comparison is ambiguous")
            result[key] = row
        return result
    previous, current = indexed(before), indexed(after)
    added = [dict(row) for key, row in current.items() if key not in previous]
    missing = [dict(row) for key, row in previous.items() if key not in current]
    changed = [{"before": dict(row), "after": dict(current[key])}
               for key, row in previous.items() if key in current and row != current[key]]
    return {"added": added, "missing": missing, "changed": changed,
            "original_rows_unchanged": not missing and not changed,
            "reward_attribution_verified": False, "cleanup_allowed": False}


class Audit:
    """One explicit read-only audit, advanced by the existing bridge game tick."""
    def __init__(self, roster, is_boosting, *, clock=None, capture_factory=Capture):
        import time
        self.roster = roster
        self.is_boosting = is_boosting
        self.clock = clock or time.monotonic
        self.capture_factory = capture_factory
        self.job = None
        self.next_tick = 0.0

    def _error(self, message):
        return {"ok": False, "message": message}

    def start(self, player_index):
        import uuid
        if self.job and self.job["phase"] in ("waiting", "capturing"):
            return self._error("An inventory capture is already running")
        if isinstance(player_index, bool) or not isinstance(player_index, int) or player_index < 0:
            return self._error("Choose an explicit guest player index")
        if self.is_boosting():
            return self._error("Stop AFK boosting before running this read-only inventory check")
        world, rows = self.roster()
        target = next((r for r in rows if r['index'] == player_index), None)
        if world is None or target is None:
            return self._error("Guest is no longer in this lobby")
        self.job = {"id": uuid.uuid4().hex, "world": world, "token": target['token'],
                    "name": target['name'], "index": player_index, "phase": "waiting",
                    "capture": None, "baseline": None, "comparison": None,
                    "error": "", "deadline": self.clock() + 300}
        self.next_tick = 0
        return {"ok": True, "audit": self.status()}

    def status(self):
        if not self.job:
            return {"phase": "idle", "cleanup_allowed": False}
        j = self.job
        capture = j['capture']
        return {"id": j['id'], "phase": j['phase'], "name": j['name'],
                "player_index": j['index'], "error": j['error'],
                "capture": capture.status() if capture else None, "cleanup_allowed": False}

    def _cancel(self, message):
        self.job['phase'] = 'cancelled'
        self.job['error'] = message
        self.job['capture'] = None

    def control(self, mode, audit_id):
        if not self.job or audit_id != self.job['id']:
            return self._error('Inventory capture ID does not match; nothing changed')
        if mode == 'cancel':
            self._cancel('Inventory check cancelled')
        elif mode == 'compare':
            if self.job['phase'] != 'complete' or self.is_boosting():
                return self._error('Complete the first capture and stop AFK boosting before comparing')
            if self.job['baseline'] is None:
                self.job['baseline'] = self.job['capture'].snapshot()
            self.job['capture'] = None
            self.job['comparison'] = None
            self.job['phase'] = 'waiting'
            self.job['deadline'] = self.clock() + 300
            self.next_tick = 0
        elif mode == 'snapshot':
            if self.job['phase'] != 'complete':
                return self._error('No complete inventory capture is available')
            return {'ok': True, 'audit': self.status(), 'snapshot': self.job['capture'].snapshot(),
                    'comparison': self.job['comparison']}
        elif mode != 'status':
            return self._error('Unknown inventory check operation')
        return {'ok': True, 'audit': self.status()}

    def tick(self):
        if not self.job or self.job['phase'] not in ('waiting', 'capturing'):
            return
        now = self.clock()
        if now < self.next_tick:
            return
        self.next_tick = now + .25
        if self.is_boosting():
            self._cancel('Boosting started; read-only inventory check cancelled')
            return
        if now >= self.job['deadline']:
            self._cancel('Inventory check timed out without a complete stable capture')
            return
        try:
            world, rows = self.roster()
            target = next((r for r in rows if r['token'] == self.job['token']), None)
            if world != self.job['world'] or target is None:
                self._cancel('Guest left or world changed; inventory check cancelled')
                return
            if not target['ready']:
                if self.job['capture'] is not None:
                    self._cancel('Guest character changed or unloaded during inventory capture')
                return
            self.job['index'] = target['index']
            if self.job['capture'] is None:
                self.job['capture'] = self.capture_factory(target['token'])
            self.job['phase'] = 'capturing'
            result = self.job['capture'].step(target['token'])
            if result['done']:
                self.job['phase'] = 'complete' if result['ok'] else 'failed'
                self.job['error'] = result['error']
                if result['ok'] and self.job['baseline'] is not None:
                    self.job['comparison'] = compare_captures(self.job['baseline'], self.job['capture'].snapshot())
        except Exception:
            self._cancel('Native inventory read failed; capture discarded')
