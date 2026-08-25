"""Read portable @U item serials from live InventoryIdentity memory.

Offset layout and identity discovery follow Oak2LiveObjectViewer (LOV) 0.10+:

    InventoryIdentity + 0xA0 -> pointer to @U Base85 serial
    +0xB0 -> serial length
    +0xB8 -> serial capacity
    +0xC4 -> item level

Focused on equipped slots and backpack/inventory rows on a **selected party
player** (host can target guests via PlayerArray PlayerState). Ground / dropped
/ nearby pickups are intentionally unsupported.
"""
from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from datetime import datetime
from pathlib import Path
from typing import Any

from unrealsdk import logging

from .inventory_capacity import get_player_state_by_party_index

_LOG = "[MSBT SerialRead]"
_SERIAL_META_WARNED = False

try:
    from . import serial_item_meta as _serial_item_meta
except Exception as exc:
    _serial_item_meta = None
    try:
        logging.warning(f"{_LOG} serial_item_meta import failed: {exc!r}")
    except Exception:
        pass

ITEM_SERIAL_POINTER_OFFSET = 0xA0
ITEM_SERIAL_LENGTH_OFFSET = 0xB0
ITEM_SERIAL_CAPACITY_OFFSET = 0xB8
ITEM_LEVEL_OFFSET = 0xC4
ITEM_SERIAL_MAX_CHARS = 131072

# LOV named slots + likely weapon indices for BL4's four guns.
_EQUIP_SLOT_NAMES: dict[int, str] = {
    0: "Weapon 1",
    1: "Weapon 2",
    2: "Weapon 3",
    3: "Weapon 4",
    4: "Shield",
    5: "Ordnance",
    6: "Repkit",
    7: "Enhancement",
    8: "Class Mod",
}

_BACKPACK_ITEM_ATTRS = (
    "BackpackItems",
    "InventoryItems",
    "PlayerInventoryItems",
)

_PAWN_ATTRS = (
    "PawnPrivate",
    "Pawn",
    "AcknowledgedPawn",
    "OakCharacter",
    "Character",
    "ControlledPawn",
)

_ACTIVE_WEAPON_ATTRS = (
    "CurrentWeapon",
    "ActiveWeapon",
    "EquippedWeapon",
    "Weapon",
)

_BACKPACK_READ_CAP = 48
# Full inventory browser (Electron Inventory tab). Soft safety ceiling.
_INVENTORY_READ_CAP = 2000

# Last diagnostic snapshot for empty-read status messages (equipped / backpack).
_last_read_diag: dict[str, dict[str, Any]] = {}


class _MemoryBasicInformation(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", ctypes.c_ulong),
        ("PartitionId", ctypes.c_ushort),
        ("RegionSize", ctypes.c_size_t),
        ("State", ctypes.c_ulong),
        ("Protect", ctypes.c_ulong),
        ("Type", ctypes.c_ulong),
    ]


def _log(message: str) -> None:
    try:
        logging.info(f"{_LOG} {message}")
    except Exception:
        pass


def _native_range_readable(address: int, size: int) -> bool:
    if address <= 0 or size < 0:
        return False
    try:
        kernel32 = ctypes.windll.kernel32
    except Exception:
        return False
    try:
        info = _MemoryBasicInformation()
        result = kernel32.VirtualQuery(
            ctypes.c_void_p(address), ctypes.byref(info), ctypes.sizeof(info)
        )
        if not result or int(info.State) != 0x1000:
            return False
        if int(info.Protect) & (0x01 | 0x100):
            return False
        start = int(info.BaseAddress or 0)
        return address >= start and address + size <= start + int(info.RegionSize)
    except Exception:
        return False


def _read_native_memory(address: int, size: int) -> bytes | None:
    if not _native_range_readable(address, size):
        return None
    try:
        return ctypes.string_at(address, size)
    except Exception:
        return None


def _read_native_u32(address: int) -> int | None:
    raw = _read_native_memory(address, 4)
    return int.from_bytes(raw, "little") if raw is not None else None


def _read_native_u64(address: int) -> int | None:
    raw = _read_native_memory(address, 8)
    return int.from_bytes(raw, "little") if raw is not None else None


def _type_name(value: Any) -> str:
    """Resolve UObject / WrappedStruct type names the way LOV does.

    Plain ``type(value).__name__`` is often ``WrappedStruct`` for inventory
    rows and InventoryIdentity — that breaks EquipSlot / identity checks.
    """
    if value is None:
        return ""
    if _live(value):
        try:
            cls = getattr(value, "Class", None)
            name = getattr(cls, "Name", None) if cls is not None else None
            if name:
                return str(name)
        except Exception:
            pass
    try:
        struct_type = getattr(value, "_type", None)
        if struct_type is not None:
            name = getattr(struct_type, "Name", None)
            if name:
                return str(name)
    except Exception:
        pass
    try:
        return type(value).__name__
    except Exception:
        return ""


def _live(obj: Any) -> bool:
    """True only for live UObjects (have Name + Class), matching LOV.

    WrappedStructs such as InventoryIdentity expose ``_get_address()`` but are
    NOT UObjects. Treating them as live rejected every identity and produced
    empty serial reads despite finding backpack rows.
    """
    if obj is None:
        return False
    try:
        _ = obj.Name
        _ = obj.Class
        return True
    except Exception:
        return False


def _identity_address(identity: Any) -> int:
    try:
        return int(identity._get_address())
    except Exception:
        return 0


def _looks_like_inventory_identity(value: Any) -> bool:
    # InventoryIdentity is a WrappedStruct — must NOT use UObject-live rejection
    # incorrectly. LOV rejects live UObjects here; structs pass through.
    if value is None or _live(value):
        return False
    try:
        return _type_name(value) == "InventoryIdentity" and _identity_address(value) > 0
    except Exception:
        return False


def item_identity_from_value(value: Any) -> Any:
    """Locate an InventoryIdentity on a backpack row or live inventory actor."""
    if _looks_like_inventory_identity(value):
        return value
    paths = (
        ("Identity",),
        ("data", "Identity"),
        ("item", "data", "Identity"),
        ("InventoryItem", "item", "data", "Identity"),
    )
    for path in paths:
        node = value
        try:
            for name in path:
                node = getattr(node, name)
        except Exception:
            continue
        if _looks_like_inventory_identity(node):
            return node
    if _live(value):
        try:
            function = getattr(value, "GetIdentity", None)
            node = function() if callable(function) else None
            if _looks_like_inventory_identity(node):
                return node
        except Exception:
            pass
    return None


def item_identity_serial_info(identity: Any) -> dict[str, Any]:
    address = _identity_address(identity)
    if not address:
        return {}
    data_address = _read_native_u64(address + ITEM_SERIAL_POINTER_OFFSET)
    length = _read_native_u64(address + ITEM_SERIAL_LENGTH_OFFSET)
    capacity = _read_native_u64(address + ITEM_SERIAL_CAPACITY_OFFSET)
    if data_address is None or length is None or capacity is None:
        return {}
    if (
        length < 2
        or length > ITEM_SERIAL_MAX_CHARS
        or capacity < length
        or capacity > ITEM_SERIAL_MAX_CHARS * 2
    ):
        return {}
    raw = _read_native_memory(int(data_address), int(length))
    if raw is None:
        return {}
    try:
        serial = raw.split(b"\x00", 1)[0].decode("ascii")
    except Exception:
        return {}
    if not serial.startswith("@U"):
        return {}
    level = _read_native_u32(address + ITEM_LEVEL_OFFSET)
    return {
        "serial": serial,
        "level": int(level) if level is not None else -1,
        "serial_length": len(serial),
    }


def item_identity_serial(identity: Any) -> str:
    return str(item_identity_serial_info(identity).get("serial") or "")


def equip_slot_label(slot: int) -> str:
    if slot in _EQUIP_SLOT_NAMES:
        return _EQUIP_SLOT_NAMES[int(slot)]
    return f"Slot {int(slot)}"


def _equip_slot_of(source: Any) -> int | None:
    inventory_item = None
    if _type_name(source) == "InventoryItem":
        inventory_item = source
    else:
        try:
            inventory_item = source.InventoryItem
        except Exception:
            inventory_item = None
    candidates = [inventory_item, source]
    for candidate in candidates:
        if candidate is None:
            continue
        try:
            return int(candidate.EquipSlot)
        except Exception:
            continue
    return None


def _is_equipped_slot(slot: int | None) -> bool:
    if slot is None:
        return False
    # Unequipped rows commonly use -1; reject absurd values.
    return 0 <= int(slot) <= 64


def _iter_sequence(seq: Any) -> list[Any]:
    if seq is None:
        return []
    try:
        count = len(seq)
    except Exception:
        return []
    out: list[Any] = []
    for index in range(int(count)):
        try:
            out.append(seq[index])
        except Exception:
            continue
    return out


def _unwrap_item_rows(container: Any) -> list[Any]:
    """Return inventory rows from a TArray or FastArray-style `.items` wrapper."""
    if container is None:
        return []
    nested_candidates: list[Any] = []
    for name in ("items", "Items", "Entries", "entries"):
        try:
            nested = getattr(container, name, None)
        except Exception:
            nested = None
        if nested is not None and nested is not container:
            nested_candidates.append(nested)
    for candidate in (*nested_candidates, container):
        rows = _iter_sequence(candidate)
        if rows:
            return rows
    return []


def _backpack_items_for_player_state(ps: Any) -> list[Any]:
    if ps is None:
        return []
    for attr in _BACKPACK_ITEM_ATTRS:
        try:
            container = getattr(ps, attr, None)
        except Exception:
            container = None
        rows = _unwrap_item_rows(container)
        if rows:
            return rows
    return []


def _pawn_for_player_state(ps: Any) -> Any | None:
    """Resolve the live character/pawn for a party PlayerState (host guest path)."""
    if ps is None:
        return None
    for attr in _PAWN_ATTRS:
        try:
            pawn = getattr(ps, attr, None)
        except Exception:
            pawn = None
        if _live(pawn):
            return pawn
    try:
        from .party_helpers import _gbc_find_pc_for_player_state, _gbc_session_world_and_gamestate

        world, _gs = _gbc_session_world_and_gamestate()
        pc = _gbc_find_pc_for_player_state(ps, world)
    except Exception:
        pc = None
    if pc is None:
        return None
    for attr in _PAWN_ATTRS:
        try:
            pawn = getattr(pc, attr, None)
        except Exception:
            pawn = None
        if _live(pawn):
            return pawn
    for meth in ("GetPawn", "K2_GetPawn", "GetCharacter"):
        fn = getattr(pc, meth, None)
        if not callable(fn):
            continue
        try:
            pawn = fn()
        except Exception:
            pawn = None
        if _live(pawn):
            return pawn
    return None


def _tag_entry(
    entry: dict[str, Any],
    *,
    player_name: str = "",
    player_index: int | None = None,
) -> dict[str, Any]:
    if player_name:
        entry["player_name"] = player_name
    if player_index is not None:
        entry["player_index"] = int(player_index)
    return entry


def _entry_from_source(
    source: Any,
    *,
    slot_hint: int | None = None,
    label_hint: str = "",
    origin: str = "",
    backpack_index: int | None = None,
    player_name: str = "",
    player_index: int | None = None,
) -> dict[str, Any] | None:
    identity = item_identity_from_value(source)
    if identity is None:
        return None
    info = item_identity_serial_info(identity)
    serial = str(info.get("serial") or "")
    if not serial.startswith("@U"):
        return None
    slot = slot_hint if slot_hint is not None else _equip_slot_of(source)
    if label_hint:
        label = label_hint
    elif slot is not None and _is_equipped_slot(slot):
        label = equip_slot_label(int(slot))
    elif backpack_index is not None:
        label = f"Backpack [{backpack_index}]"
    else:
        label = "Item"
    level = int(info.get("level") or -1)
    entry = {
        "slot": int(slot) if slot is not None else -1,
        "label": label,
        "serial": serial,
        "level": level,
        "origin": origin,
        "summary": f"{label}" + (f" L{level}" if level >= 0 else ""),
        "backpack_index": int(backpack_index) if backpack_index is not None else -1,
    }
    try:
        if _serial_item_meta is None:
            raise RuntimeError("serial_item_meta was not imported")
        _serial_item_meta.enrich_entry(entry)
    except Exception as exc:
        global _SERIAL_META_WARNED
        if not _SERIAL_META_WARNED:
            _SERIAL_META_WARNED = True
            _log(f"item name enrich failed: {exc!r}")
        entry.setdefault("display_name", label)
        entry.setdefault("category", "Other")
        entry.setdefault("rarity", "")
        entry.setdefault("manufacturer", "")
        entry.setdefault("item_type", "")
        entry.setdefault("meta_ok", False)
    return _tag_entry(entry, player_name=player_name, player_index=player_index)


def _append_active_weapon(
    found: list[dict[str, Any]],
    seen: set[str],
    *,
    ps: Any = None,
    player_name: str = "",
    player_index: int | None = None,
) -> None:
    """Prefer the target player's currently held weapon (not local get_pc())."""
    try:
        pawn = _pawn_for_player_state(ps)
        if not _live(pawn):
            return
        for attr in _ACTIVE_WEAPON_ATTRS:
            try:
                weapon = getattr(pawn, attr, None)
            except Exception:
                weapon = None
            entry = _entry_from_source(
                weapon,
                label_hint="Active Weapon",
                origin="active_weapon",
                player_name=player_name,
                player_index=player_index,
            )
            if entry is None:
                continue
            serial = entry["serial"]
            if serial in seen:
                # Promote existing row to Active Weapon label when it matches.
                for existing in found:
                    if existing.get("serial") == serial:
                        existing["label"] = "Active Weapon"
                        existing["origin"] = "active_weapon"
                        existing["summary"] = "Active Weapon" + (
                            f" L{existing['level']}" if int(existing.get("level") or -1) >= 0 else ""
                        )
                        found.remove(existing)
                        found.insert(0, existing)
                        break
            else:
                found.insert(0, entry)
                seen.add(serial)
            break
    except Exception:
        pass


def _probe_row_decode(row: Any) -> str:
    """Classify why a backpack row did not yield a serial (for empty-read status)."""
    identity = item_identity_from_value(row)
    if identity is None:
        return "no_identity"
    info = item_identity_serial_info(identity)
    if not info:
        return "serial_decode_failed"
    serial = str(info.get("serial") or "")
    if not serial.startswith("@U"):
        return "no_at_u_serial"
    return "ok"


def _scan_row_stats(rows: list[Any], *, sample_limit: int = 64) -> dict[str, int]:
    """Sample backpack rows to explain empty reads without scanning thousands."""
    stats = {
        "rows": len(rows),
        "sampled": 0,
        "identities": 0,
        "serials_ok": 0,
        "no_identity": 0,
        "serial_decode_failed": 0,
        "no_at_u_serial": 0,
        "equipped_slots": 0,
    }
    limit = max(1, int(sample_limit))
    for row in rows[:limit]:
        stats["sampled"] += 1
        slot = _equip_slot_of(row)
        if _is_equipped_slot(slot):
            stats["equipped_slots"] += 1
        kind = _probe_row_decode(row)
        if kind == "ok":
            stats["identities"] += 1
            stats["serials_ok"] += 1
        elif kind == "no_identity":
            stats["no_identity"] += 1
        elif kind == "serial_decode_failed":
            stats["identities"] += 1
            stats["serial_decode_failed"] += 1
        else:
            stats["identities"] += 1
            stats["no_at_u_serial"] += 1
    return stats


def empty_read_reason(stats: dict[str, Any] | None, *, mode: str = "backpack") -> str:
    """Human-readable why a serial read returned nothing."""
    if not stats:
        return "no diagnostic stats available"
    rows = int(stats.get("rows") or 0)
    if rows <= 0:
        return "no inventory item rows on PlayerState (BackpackItems/InventoryItems empty or missing)"
    identities = int(stats.get("identities") or 0)
    serials_ok = int(stats.get("serials_ok") or 0)
    equipped = int(stats.get("equipped_candidates") or stats.get("equipped_slots") or 0)
    decode_fail = int(stats.get("serial_decode_failed") or 0)
    no_id = int(stats.get("no_identity") or 0)
    sampled = int(stats.get("sampled") or 0)
    if mode == "equipped" and equipped <= 0 and serials_ok <= 0:
        return (
            f"found {rows} backpack row(s) but no EquipSlot in 0–64 "
            f"(sampled {sampled}; identities={identities})"
        )
    if mode == "equipped" and equipped > 0 and serials_ok <= 0 and identities <= 0:
        return (
            f"found {equipped} equipped slot row(s) among {rows} backpack row(s) "
            f"but no InventoryIdentity (sampled {sampled}, no_identity={no_id})"
        )
    if identities <= 0:
        return (
            f"found {rows} backpack row(s) but no InventoryIdentity on sampled rows "
            f"({sampled} sampled, no_identity={no_id})"
        )
    if serials_ok <= 0 and decode_fail > 0:
        return (
            f"found {rows} row(s) / {identities} identity(ies) but native @U decode failed "
            f"(offset/read; decode_failed={decode_fail})"
        )
    if serials_ok <= 0:
        return (
            f"found {rows} row(s) / {identities} identity(ies) but no readable @U serials "
            f"(sampled {sampled})"
        )
    return f"found {rows} row(s); decoded {serials_ok} serial(s) in sample"


def read_equipped_serials_for_player_state(
    ps: Any,
    *,
    player_name: str = "",
    player_index: int | None = None,
) -> list[dict[str, Any]]:
    """Return equipped backpack rows that expose a readable @U serial."""
    rows = _backpack_items_for_player_state(ps)
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    equipped_candidates = 0
    for row in rows:
        slot = _equip_slot_of(row)
        if not _is_equipped_slot(slot):
            continue
        equipped_candidates += 1
        entry = _entry_from_source(
            row,
            slot_hint=slot,
            label_hint=equip_slot_label(int(slot)),
            origin="equipped",
            player_name=player_name,
            player_index=player_index,
        )
        if entry is None:
            continue
        serial = entry["serial"]
        if serial in seen:
            continue
        seen.add(serial)
        found.append(entry)

    # Slot order first, then promote currently held weapon to the front.
    found.sort(key=lambda e: (int(e.get("slot", 999)), str(e.get("label") or "")))
    _append_active_weapon(
        found,
        seen,
        ps=ps,
        player_name=player_name,
        player_index=player_index,
    )
    who = player_name or (f"P{int(player_index) + 1}" if player_index is not None else "player")
    stats = _scan_row_stats(rows) if not found else {
        "rows": len(rows),
        "equipped_slots": equipped_candidates,
        "serials_ok": len(found),
        "identities": len(found),
        "sampled": 0,
        "no_identity": 0,
        "serial_decode_failed": 0,
        "no_at_u_serial": 0,
    }
    stats["equipped_candidates"] = equipped_candidates
    _last_read_diag["equipped"] = dict(stats)
    _log(
        f"Equipped serials for {who}: {len(found)} "
        f"(backpack_rows={len(rows)}, equipped_candidates={equipped_candidates})"
    )
    if not found:
        _log(f"  empty reason: {empty_read_reason(stats, mode='equipped')}")
    for entry in found:
        _log(f"  {entry['summary']}: {entry['serial']}")
    return found


def read_backpack_serials_for_player_state(
    ps: Any,
    *,
    player_name: str = "",
    player_index: int | None = None,
    limit: int = _BACKPACK_READ_CAP,
) -> list[dict[str, Any]]:
    """Return backpack/inventory rows with readable @U serials (capped, not a browser)."""
    rows = _backpack_items_for_player_state(ps)
    found: list[dict[str, Any]] = []
    seen: set[str] = set()
    cap = max(1, int(limit))
    scanned = 0
    for index, row in enumerate(rows):
        if len(found) >= cap:
            break
        scanned += 1
        slot = _equip_slot_of(row)
        if _is_equipped_slot(slot):
            label = equip_slot_label(int(slot))
            origin = "equipped"
        else:
            label = f"Backpack [{index}]"
            origin = "backpack"
        entry = _entry_from_source(
            row,
            slot_hint=slot,
            label_hint=label,
            origin=origin,
            backpack_index=index,
            player_name=player_name,
            player_index=player_index,
        )
        if entry is None:
            continue
        serial = entry["serial"]
        if serial in seen:
            continue
        seen.add(serial)
        found.append(entry)

    who = player_name or (f"P{int(player_index) + 1}" if player_index is not None else "player")
    stats = _scan_row_stats(rows) if not found else {
        "rows": len(rows),
        "serials_ok": len(found),
        "identities": len(found),
        "sampled": scanned,
        "equipped_slots": 0,
        "no_identity": 0,
        "serial_decode_failed": 0,
        "no_at_u_serial": 0,
    }
    stats["scanned_for_serials"] = scanned
    _last_read_diag["backpack"] = dict(stats)
    _log(f"Backpack serials for {who}: {len(found)} (cap {cap}, rows={len(rows)})")
    if not found:
        _log(f"  empty reason: {empty_read_reason(stats, mode='backpack')}")
    for entry in found:
        _log(f"  {entry['summary']}: {entry['serial']}")
    return found


def get_last_read_diagnostics(mode: str = "") -> dict[str, Any]:
    if mode:
        return dict(_last_read_diag.get(mode) or {})
    return {k: dict(v) for k, v in _last_read_diag.items()}


def read_equipped_serials_for_party_index(index: int | None, *, player_name: str = "") -> list[dict[str, Any]]:
    ps = get_player_state_by_party_index(index)
    if ps is None:
        raise RuntimeError("Selected party player was not found.")
    return read_equipped_serials_for_player_state(
        ps,
        player_name=player_name,
        player_index=int(index) if index is not None else None,
    )


def read_backpack_serials_for_party_index(
    index: int | None,
    *,
    player_name: str = "",
    limit: int = _BACKPACK_READ_CAP,
) -> list[dict[str, Any]]:
    ps = get_player_state_by_party_index(index)
    if ps is None:
        raise RuntimeError("Selected party player was not found.")
    return read_backpack_serials_for_player_state(
        ps,
        player_name=player_name,
        player_index=int(index) if index is not None else None,
        limit=limit,
    )


def read_inventory_for_player_state(
    ps: Any,
    *,
    player_name: str = "",
    player_index: int | None = None,
    backpack_limit: int = _INVENTORY_READ_CAP,
) -> dict[str, Any]:
    """Full inventory snapshot: equipped slots + unequipped backpack rows (capped)."""
    equipped = read_equipped_serials_for_player_state(
        ps,
        player_name=player_name,
        player_index=player_index,
    )
    rows = _backpack_items_for_player_state(ps)
    backpack: list[dict[str, Any]] = []
    seen = {str(e.get("serial") or "") for e in equipped}
    cap = max(1, int(backpack_limit))
    scanned = 0
    for index, row in enumerate(rows):
        if len(backpack) >= cap:
            break
        scanned += 1
        slot = _equip_slot_of(row)
        if _is_equipped_slot(slot):
            continue
        entry = _entry_from_source(
            row,
            slot_hint=slot,
            label_hint=f"Backpack [{index}]",
            origin="backpack",
            backpack_index=index,
            player_name=player_name,
            player_index=player_index,
        )
        if entry is None:
            continue
        serial = entry["serial"]
        if serial in seen:
            continue
        seen.add(serial)
        backpack.append(entry)

    who = player_name or (f"P{int(player_index) + 1}" if player_index is not None else "player")
    truncated = len(backpack) >= cap and scanned < len(rows)
    _last_read_diag["inventory"] = {
        "rows": len(rows),
        "equipped": len(equipped),
        "backpack": len(backpack),
        "scanned_for_serials": scanned,
        "backpack_cap": cap,
        "truncated": truncated,
    }
    _log(
        f"Inventory for {who}: equipped={len(equipped)} backpack={len(backpack)} "
        f"(cap {cap}, rows={len(rows)})"
    )
    return {
        "equipped": equipped,
        "backpack": backpack,
        "total_rows": len(rows),
        "equipped_count": len(equipped),
        "backpack_count": len(backpack),
        "backpack_cap": cap,
        "truncated": truncated,
    }


def read_inventory_for_party_index(
    index: int | None,
    *,
    player_name: str = "",
    backpack_limit: int = _INVENTORY_READ_CAP,
) -> dict[str, Any]:
    ps = get_player_state_by_party_index(index)
    if ps is None:
        raise RuntimeError("Selected party player was not found.")
    return read_inventory_for_player_state(
        ps,
        player_name=player_name,
        player_index=int(index) if index is not None else None,
        backpack_limit=backpack_limit,
    )


def write_clipboard_text(text: str) -> bool:
    """Copy Unicode text to the Windows clipboard (Azzy-style 64-bit-safe ctypes)."""
    try:
        CF_UNICODETEXT, GMEM_MOVEABLE = 13, 0x0002
        user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
        kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = wintypes.LPVOID
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        user32.SetClipboardData.restype = wintypes.HANDLE
        buffer = ctypes.create_unicode_buffer(text)
        size = ctypes.sizeof(buffer)
        handle = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
        if not handle:
            return False
        pointer = kernel32.GlobalLock(handle)
        if not pointer:
            return False
        ctypes.memmove(pointer, buffer, size)
        kernel32.GlobalUnlock(handle)
        if not user32.OpenClipboard(None):
            return False
        try:
            user32.EmptyClipboard()
            return bool(user32.SetClipboardData(CF_UNICODETEXT, handle))
        finally:
            user32.CloseClipboard()
    except Exception as exc:
        _log(f"Clipboard write failed: {exc!r}")
        return False


def dump_dir_candidates() -> list[Path]:
    dirs: list[Path] = []
    local_app = (os.environ.get("LOCALAPPDATA") or "").strip()
    if local_app:
        dirs.append(Path(local_app) / "MattsSDKBoostingTools" / "serial_reads")
    try:
        dirs.append(Path(__file__).resolve().parent / "serial_reads")
    except Exception:
        pass
    out: list[Path] = []
    seen: set[str] = set()
    for path in dirs:
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def write_serial_dump(entries: list[dict[str, Any]], *, title: str = "") -> list[str]:
    """Write stamped + latest text dumps. Returns paths written."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    lines = [
        f"# MSBT serial read {stamp}",
        f"# {title}" if title else "#",
        "",
    ]
    for entry in entries:
        summary = str(entry.get("summary") or entry.get("label") or "Item")
        who = str(entry.get("player_name") or "")
        if who:
            summary = f"{who} — {summary}"
        serial = str(entry.get("serial") or "")
        lines.append(f"# {summary}")
        lines.append(serial)
        lines.append("")
    text = "\n".join(lines)
    written: list[str] = []
    for dump_dir in dump_dir_candidates():
        try:
            dump_dir.mkdir(parents=True, exist_ok=True)
            stamped = dump_dir / f"serial_read_{stamp}.txt"
            latest = dump_dir / "serial_read_latest.txt"
            stamped.write_text(text, encoding="utf-8")
            latest.write_text(text, encoding="utf-8")
            written.append(str(stamped))
            written.append(str(latest))
            _log(f"Wrote dump: {stamped}")
        except Exception as exc:
            _log(f"Failed dump under {dump_dir}: {exc!r}")
    return written


def entries_to_serial_text(entries: list[dict[str, Any]]) -> str:
    return "\n".join(str(e.get("serial") or "") for e in entries if str(e.get("serial") or "").startswith("@U"))
