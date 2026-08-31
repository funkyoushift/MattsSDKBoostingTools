"""Live map discovery for a targeted party player.

Fog hide (`no_fog_of_war.py`) only zeros the big-map overlay material.
This marks the selected player's discovery state the same way the offline
save editor does — regions, seen-world lists, and FoD bit arrays — then
still tries a walk-radius widen if those fields exist.

Listen-host can write PlayerArray objects in this process. A remote guest's
own overlay still lives in their process unless discovery replicates.
"""
from __future__ import annotations

import ctypes
import struct
from typing import Any

from mods_base import get_pc
from unrealsdk import find_all, find_object, logging
from ctypes import wintypes

try:
    from unrealsdk.unreal import WrappedStruct
except Exception:  # pragma: no cover
    WrappedStruct = None  # type: ignore[misc, assignment]

_PREFIX = "[Matts SDK Boosting Tools | FoD]"
_UNFOG_RADIUS = 100000.0
_UNFOG_RATE = 10.0

_FLOAT_FIELDS = (
    "UnfogRadius",
    "UnfogRadiusVehicle",
    "UnfogHeight",
    "UnfogHeightVehicle",
    "UnfogRate",
    "UnfogSaveRate",
    "UnfogMovementThreshold",
    "PercentageOfUnfogRadiusThatIsFull",
)
_BOOL_FIELDS = ("bUseOverrideUnfog",)
_OFFSET_ATTRS = (
    "Offset_Internal",
    "offset_internal",
    "Offset",
    "offset",
    "PropertyOffset",
    "InternalOffset",
)
_HOLDER_CLASSES = (
    "GbxDiscoveryUnfogData",
    "GbxDiscoveryPinConfig",
    "GbxDiscoveryGlobals",
    "GbxDiscoveryViewableMapDef",
    "GbxDiscoveryViewableMapBehaviorDef",
    "GbxDiscoveryDiscovererDef",
    "GbxDiscoveryFODManagerCPU",
    "GbxDiscoverySaveGameData",
    "GbxDiscoveryPerCharacterProgressRole",
    "GbxDiscoveryPerCharacterProgressRole_Shared",
    "NexusConfigStoreGbxDiscoveryDiscovererDef",
    "NexusConfigStoreGbxDiscoveryViewableMapBehaviorDef",
    "NexusConfigStoreGbxDiscoveryViewableMapDef",
    "NexusConfigStoreGbxDiscoveryPinConfig",
)
_ROOT_ATTRS = (
    "PlayerState",
    "Pawn",
    "OakCharacter",
    "AcknowledgedPawn",
    "Discoverer",
    "DiscovererDef",
    "UnfogData",
    "OverrideUnfogData",
    "ViewableMapBehavior",
    "ViewableMapBehaviorDef",
    "PinConfig",
    "DiscoveryComponent",
    "GbxDiscoveryComponent",
    "OakDiscoveryComponent",
    "DiscoveryPinningState",
    "GbxDiscoveryGlobals",
)
_NEST_ATTRS = (
    "UnfogData",
    "OverrideUnfogData",
    "PinConfig",
    "DiscovererDef",
    "ViewableMapBehavior",
    "ViewableMapBehaviorDef",
    "PlayerDiscovererDef",
    "MapViewerDiscovererDef",
)
# Same worlds / regions Matt Editor writes into gbx_discovery_pc.
_LEVEL_NAMES = (
    "Intro_P",
    "World_P",
    "Vault_Grasslands_P",
    "Fortress_Grasslands_P",
    "Vault_ShatteredLands_P",
    "Fortress_Shatteredlands_P",
    "Vault_Mountains_P",
    "Fortress_Mountains_P",
    "ElpisElevator_P",
    "Elpis_P",
    "UpperCity_P",
)
_REGION_NAMES = (
    "KairosGeneric",
    "grasslands_Prison",
    "grasslands_RegionA",
    "grasslands_RegionB",
    "grasslands_RegionC",
    "grasslands_RegionD",
    "grasslands_RegionE",
    "Grasslands_Fortress",
    "Grasslands_Vault",
    "shatteredlands_RegionA",
    "shatteredlands_RegionB",
    "shatteredlands_RegionC",
    "shatteredlands_RegionD",
    "shatteredlands_RegionE",
    "shatteredlands_Fortress",
    "shatteredlands_Vault",
    "mountains_RegionA",
    "mountains_RegionB",
    "mountains_RegionC",
    "mountains_RegionD",
    "mountains_RegionE",
    "Mountains_Fortress",
    "Mountains_Vault",
    "elpis_elevator",
    "elpis",
    "city_RegionA",
    "city_RegionB",
    "city_RegionC",
    "city_Upper",
)
_REGION_METHODS = (
    "ServerSetDiscoveryRegion",
    "SetDiscoveryRegion",
    "ClientSetDiscoveryRegion",
)
_LOCATION_METHODS = (
    "ServerDiscoveryMakeNonAuthoritativeDiscovery",
    "DiscoveryMakeNonAuthoritativeDiscovery",
    "ClientDiscoveryNotifyLocationDiscoveredStateChanged",
    "DiscoverForHost",
    "DiscoverForSelf",
    "DiscoverLocation",
    "ClientReveal",
    "RevealEverything",
)
_SEEN_LIST_ATTRS = (
    "HasSeenWorldList",
    "HasSeenRegionList",
    "SeenWorldList",
    "SeenRegionList",
    "hasseenworldlist",
    "hasseenregionlist",
)
_DISCOVERED_KEY_PATH = "/Script/GbxGame.GbxDiscoveryDiscoveredKey"
_DISCOVERY_NAME_TOKENS = (
    "discover",
    "fod",
    "hasseen",
    "seenworld",
    "seenregion",
    "revealed",
    "explored",
)
_DISCOVERY_NAME_SKIP = (
    "blackmarket",
    "machine",
    "buddy",
    "dimension",
    "grid",
    "version",
    "compression",
    "pinning",
)
# Live OakGameState reflection (not the stale NHA +0x670 slot).
_GS_DISC_BIT_ARRAY = 0xA70
_GS_DISC_LIVE_ACTORS = 0xB90
# Live FoD tile grid: GbxDiscoveryFODManagerCPU + 0xB0 TArray, 128x128 bytes.
# Walk radius lives at +0xC0 / +0xC8 (defaults 30000). Widen commits via real unfog.
_FOD_MANAGER_CLS = "GbxDiscoveryFODManagerCPU"
_FOD_GRID_COUNT = 128 * 128
_FOD_GRID_OFF = 0xB0
_FOD_UNFOG_OFFS = (0xC0, 0xC8)
_FOD_UNFOG_WIDEN = 10000000.0

kernel32 = ctypes.windll.kernel32
kernel32.VirtualProtect.argtypes = (
    wintypes.LPVOID,
    ctypes.c_size_t,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
)
kernel32.VirtualProtect.restype = wintypes.BOOL
PAGE_EXECUTE_READWRITE = 0x40

_last_status: dict[str, Any] = {
    "wrote": 0,
    "setattr": 0,
    "memory": 0,
    "holders": 0,
    "regions": 0,
    "seen_lists": 0,
    "arrays": 0,
    "location_rpcs": 0,
    "fod_grid": 0,
    "unfog_widen": 0,
    "radius": _UNFOG_RADIUS,
    "message": "FoD reveal idle.",
}


def _log(msg: str) -> None:
    try:
        logging.info(f"{_PREFIX} {msg}")
    except Exception:
        print(f"{_PREFIX} {msg}")


def _safe_str(obj: Any) -> str:
    try:
        return str(obj)
    except Exception:
        return type(obj).__name__


def _obj_addr(obj: Any) -> int:
    get_addr = getattr(obj, "_get_address", None)
    if not callable(get_addr):
        return 0
    try:
        addr = int(get_addr())
    except Exception:
        return 0
    if addr in (0, -1):
        return 0
    return addr


def _is_skip_type(obj: Any) -> bool:
    path = _safe_str(obj)
    if path.startswith("Class'"):
        return True
    if "Default__" in path:
        return True
    if path.startswith("ScriptStruct'"):
        return True
    return False


def _find_all_safe(class_name: str) -> list[Any]:
    for exact in (False, True):
        try:
            return list(find_all(class_name, exact) or [])
        except TypeError:
            try:
                return list(find_all(class_name) or [])
            except Exception:
                return []
        except Exception:
            continue
    return []


def _iter_ustructs(obj: Any) -> list[Any]:
    struct = getattr(obj, "Class", None) or getattr(obj, "_type", None)
    if struct is None:
        return []
    out = [struct]
    try:
        out.extend(list(struct._superfields()))
    except Exception:
        pass
    return out


def prop_offset(prop: Any) -> int:
    """Public for tests: first plausible UProperty offset."""
    if prop is None:
        return -1
    for name in _OFFSET_ATTRS:
        try:
            raw = getattr(prop, name, None)
        except Exception:
            continue
        if raw is None or callable(raw):
            continue
        try:
            value = int(raw)
        except Exception:
            continue
        if 0 <= value < 0x100000:
            return value
    getter = getattr(prop, "get_offset", None) or getattr(prop, "GetOffset", None)
    if callable(getter):
        try:
            value = int(getter())
            if 0 <= value < 0x100000:
                return value
        except Exception:
            pass
    return -1


def _iter_named_props(obj: Any) -> list[tuple[str, Any, int]]:
    found: list[tuple[str, Any, int]] = []
    seen: set[str] = set()
    for struct in _iter_ustructs(obj):
        try:
            props = list(struct._properties())
        except Exception:
            continue
        for prop in props:
            try:
                name = str(getattr(prop, "Name", "") or "")
            except Exception:
                name = ""
            if not name or name in seen:
                continue
            seen.add(name)
            found.append((name, prop, prop_offset(prop)))
    return found


def _write_f32(addr: int, value: float) -> bool:
    if addr < 0x10000:
        return False
    data = struct.pack("<f", float(value))
    old = wintypes.DWORD()
    if not kernel32.VirtualProtect(ctypes.c_void_p(addr), len(data), PAGE_EXECUTE_READWRITE, ctypes.byref(old)):
        return False
    ctypes.memmove(addr, data, len(data))
    restored = wintypes.DWORD()
    kernel32.VirtualProtect(ctypes.c_void_p(addr), len(data), old.value, ctypes.byref(restored))
    return True


def _read_f32(addr: int) -> float | None:
    if addr < 0x10000:
        return None
    try:
        return float(struct.unpack("<f", ctypes.string_at(addr, 4))[0])
    except Exception:
        return None


def _read_u64(addr: int) -> int:
    if addr < 0x10000:
        return 0
    try:
        return int(struct.unpack("<Q", ctypes.string_at(addr, 8))[0])
    except Exception:
        return 0


def _read_i32(addr: int) -> int:
    if addr < 0x10000:
        return 0
    try:
        return int(struct.unpack("<i", ctypes.string_at(addr, 4))[0])
    except Exception:
        return 0


def _write_bytes(addr: int, data: bytes) -> bool:
    if addr < 0x10000 or not data:
        return False
    old = wintypes.DWORD()
    if not kernel32.VirtualProtect(ctypes.c_void_p(addr), len(data), PAGE_EXECUTE_READWRITE, ctypes.byref(old)):
        return False
    ctypes.memmove(addr, data, len(data))
    restored = wintypes.DWORD()
    kernel32.VirtualProtect(ctypes.c_void_p(addr), len(data), old.value, ctypes.byref(restored))
    return True


def _set_float_field(obj: Any, name: str, value: float) -> str:
    """Return 'setattr', 'memory', or ''."""
    before = None
    try:
        before = getattr(obj, name)
    except Exception:
        before = None
    try:
        setattr(obj, name, float(value))
        after = getattr(obj, name)
        if after is not None and abs(float(after) - float(value)) < 0.01:
            return "setattr"
    except Exception:
        pass

    offset = -1
    for pname, _prop, poff in _iter_named_props(obj):
        if pname == name:
            offset = poff
            break
    base = _obj_addr(obj)
    if base and offset >= 0:
        if _write_f32(base + offset, float(value)):
            got = _read_f32(base + offset)
            if got is not None and abs(got - float(value)) < 0.01:
                return "memory"
    if before is not None:
        try:
            if abs(float(getattr(obj, name)) - float(value)) < 0.01:
                return "setattr"
        except Exception:
            pass
    return ""


def _set_bool_field(obj: Any, name: str, value: bool) -> bool:
    try:
        setattr(obj, name, bool(value))
        return True
    except Exception:
        return False


def _apply_unfog_fields(obj: Any, radius: float) -> dict[str, int]:
    counts = {"setattr": 0, "memory": 0, "bools": 0}
    for flag in _BOOL_FIELDS:
        if _set_bool_field(obj, flag, True):
            counts["bools"] += 1
    values = {
        "UnfogRadius": radius,
        "UnfogRadiusVehicle": radius,
        "UnfogHeight": radius,
        "UnfogHeightVehicle": radius,
        "UnfogRate": _UNFOG_RATE,
        "UnfogSaveRate": _UNFOG_RATE,
        "PercentageOfUnfogRadiusThatIsFull": 1.0,
    }
    for name, value in values.items():
        method = _set_float_field(obj, name, value)
        if method:
            counts[method] += 1
    return counts


def _add_holder(holders: list[tuple[str, Any]], seen: set[int], label: str, obj: Any) -> None:
    if obj is None or _is_skip_type(obj):
        return
    key = _obj_addr(obj) or id(obj)
    if key in seen:
        return
    seen.add(key)
    holders.append((label, obj))


def _walk_object(holders: list[tuple[str, Any]], seen: set[int], label: str, obj: Any, depth: int = 0) -> None:
    if obj is None or depth > 3:
        return
    _add_holder(holders, seen, label, obj)
    for name in _NEST_ATTRS:
        try:
            child = getattr(obj, name, None)
        except Exception:
            child = None
        if child is None or callable(child):
            continue
        _walk_object(holders, seen, f"{label}.{name}", child, depth + 1)


def _party_roots() -> list[tuple[str, Any]]:
    roots: list[tuple[str, Any]] = []
    pc = get_pc()
    if pc is not None:
        roots.append(("local_pc", pc))
    world = None
    try:
        world = getattr(pc, "World", None) if pc is not None else None
    except Exception:
        world = None
    gs = getattr(world, "GameState", None) if world is not None else None
    pa = getattr(gs, "PlayerArray", None) if gs is not None else None
    if pa is None:
        return roots
    try:
        count = len(pa)
    except Exception:
        return roots
    for i in range(count):
        try:
            ps = pa[i]
        except Exception:
            continue
        if ps is None:
            continue
        roots.append((f"ps[{i}]", ps))
        for attr in ("Owner", "OwnerPawn", "PawnPrivate", "Pawn"):
            try:
                pawn = getattr(ps, attr, None)
            except Exception:
                pawn = None
            if pawn is not None:
                roots.append((f"ps[{i}].{attr}", pawn))
    return roots


def _collect_holders() -> list[tuple[str, Any]]:
    holders: list[tuple[str, Any]] = []
    seen: set[int] = set()
    for cls_name in _HOLDER_CLASSES:
        for obj in _find_all_safe(cls_name)[:24]:
            _walk_object(holders, seen, cls_name, obj)
        for path in (
            f"/Script/GbxGame.Default__{cls_name}",
            f"/Script/OakGame.Default__{cls_name}",
        ):
            try:
                cdo = find_object("Object", path)
            except Exception:
                cdo = None
            if cdo is not None:
                _walk_object(holders, seen, f"CDO.{cls_name}", cdo)
    for label, obj in _party_roots():
        _walk_object(holders, seen, label, obj)
        for attr in _ROOT_ATTRS:
            try:
                child = getattr(obj, attr, None)
            except Exception:
                child = None
            if child is None or callable(child):
                continue
            _walk_object(holders, seen, f"{label}.{attr}", child)
    return holders


def last_status() -> dict[str, Any]:
    return dict(_last_status)


def _player_state(pc: Any) -> Any | None:
    if pc is None:
        return None
    try:
        return getattr(pc, "PlayerState", None)
    except Exception:
        return None


def _pawn_of(pc: Any) -> Any | None:
    if pc is None:
        return None
    for name in ("Pawn", "AcknowledgedPawn", "OakCharacter"):
        try:
            pawn = getattr(pc, name, None)
        except Exception:
            pawn = None
        if pawn is not None:
            return pawn
    ps = _player_state(pc)
    if ps is None:
        return None
    for name in ("PawnPrivate", "Pawn", "OwnerPawn"):
        try:
            pawn = getattr(ps, name, None)
        except Exception:
            pawn = None
        if pawn is not None:
            return pawn
    return None


def _pawn_location(pc: Any) -> Any | None:
    pawn = _pawn_of(pc)
    if pawn is None:
        return None
    for name in ("K2_GetActorLocation", "GetActorLocation"):
        getter = getattr(pawn, name, None)
        if not callable(getter):
            continue
        try:
            loc = getter()
        except Exception:
            continue
        if loc is not None:
            return loc
    return getattr(pawn, "Location", None)


def _looks_discovery(name: str) -> bool:
    lower = str(name or "").lower()
    if any(tok in lower for tok in _DISCOVERY_NAME_SKIP):
        return False
    return any(tok in lower for tok in _DISCOVERY_NAME_TOKENS)


def _call_variants(obj: Any, name: str, variants: list[tuple[Any, ...]]) -> bool:
    fn = getattr(obj, name, None)
    if not callable(fn):
        return False
    for args in variants:
        try:
            fn(*args)
            return True
        except TypeError:
            continue
        except Exception as exc:
            msg = str(exc)
            if (
                "Unable to cast" in msg
                or "cannot convert" in msg.lower()
                or "not an instance of" in msg
            ):
                continue
            _log(f"{type(obj).__name__}.{name} ERR {exc!r}")
            return False
    return False


def _new_struct(path: str) -> Any | None:
    if WrappedStruct is None:
        return None
    for candidate in (path, path.rsplit(".", 1)[-1]):
        try:
            st = find_object("ScriptStruct", candidate)
        except Exception:
            st = None
        if st is None:
            continue
        try:
            return WrappedStruct(st)
        except Exception:
            continue
    return None


def _mark_discovery_regions(pc: Any, ps: Any) -> int:
    """ServerSetDiscoveryRegion is the live equivalent of hasseenregionlist."""
    wrote = 0
    targets = [obj for obj in (ps, pc) if obj is not None]
    for obj in targets:
        for method in _REGION_METHODS:
            hits = 0
            for region in _REGION_NAMES:
                if _call_variants(obj, method, [(region,)]):
                    hits += 1
            if hits:
                wrote += hits
                _log(f"{type(obj).__name__}.{method} marked {hits} region(s)")
    return wrote


def _existing_name_keys(container: Any) -> set[str]:
    keys: set[str] = set()
    try:
        for item in container:
            text = str(item or "").strip()
            if text:
                keys.add(text.casefold())
    except Exception:
        pass
    return keys


def _append_names(container: Any, names: tuple[str, ...]) -> int:
    if container is None:
        return 0
    wrote = 0
    existing = _existing_name_keys(container)
    for name in names:
        if name.casefold() in existing:
            continue
        try:
            container.append(name)
            existing.add(name.casefold())
            wrote += 1
            continue
        except Exception:
            pass
        try:
            container.append(name)  # some TArrays reject FName until a retry
            wrote += 1
        except Exception:
            continue
    return wrote


def _fill_bit_container(container: Any) -> int:
    if container is None:
        return 0
    writes = 0
    try:
        length = int(len(container))
    except Exception:
        length = 0
    target = max(length, 8)
    for index in range(target):
        item = None
        if index < length:
            try:
                item = container[index]
            except Exception:
                item = None
        if item is None:
            for candidate in (0xFFFFFFFF, -1, True, 1):
                try:
                    container.append(candidate)
                    writes += 1
                    break
                except Exception:
                    continue
            continue
        filled = False
        for attr in ("Bits", "BitMask", "Value", "CompletedBits", "Data"):
            if not hasattr(item, attr):
                continue
            for candidate in (0xFFFFFFFF, -1):
                try:
                    setattr(item, attr, candidate)
                    filled = True
                    writes += 1
                    break
                except Exception:
                    continue
        if filled:
            continue
        if isinstance(item, (int, bool)):
            for candidate in (0xFFFFFFFF, -1, True):
                try:
                    container[index] = candidate
                    writes += 1
                    break
                except Exception:
                    continue
    return writes


def _fill_named_seen_lists(obj: Any) -> int:
    wrote = 0
    for attr in _SEEN_LIST_ATTRS:
        try:
            container = getattr(obj, attr, None)
        except Exception:
            container = None
        if container is None or callable(container):
            continue
        names = _LEVEL_NAMES if "world" in attr.lower() else _REGION_NAMES
        added = _append_names(container, names)
        if added:
            wrote += added
            _log(f"appended {added} name(s) to {type(obj).__name__}.{attr}")
    return wrote


def _fill_discovery_prop(obj: Any, name: str, value: Any) -> int:
    if value is None or callable(value):
        return 0
    lower = name.lower()
    if any(tok in lower for tok in ("list", "world", "region", "level")):
        names = _LEVEL_NAMES if "world" in lower or "level" in lower else _REGION_NAMES
        added = _append_names(value, names)
        if added:
            return added
    if any(tok in lower for tok in ("bit", "array", "fod", "reveal", "explor")):
        filled = _fill_bit_container(value)
        if filled:
            return filled
    if isinstance(value, (int, bool)) or lower.startswith("b"):
        try:
            setattr(obj, name, True if not isinstance(value, int) else 1)
            return 1
        except Exception:
            return 0
    return 0


def _discovery_objects(pc: Any, ps: Any) -> list[tuple[str, Any]]:
    roots: list[tuple[str, Any]] = []
    seen: set[int] = set()

    def _add(label: str, obj: Any) -> None:
        if obj is None:
            return
        key = _obj_addr(obj) or id(obj)
        if key in seen:
            return
        seen.add(key)
        roots.append((label, obj))

    _add("pc", pc)
    _add("ps", ps)
    pawn = _pawn_of(pc)
    _add("pawn", pawn)
    world = None
    try:
        world = getattr(pc, "World", None) if pc is not None else None
    except Exception:
        world = None
    _add("world", world)
    gs = getattr(world, "GameState", None) if world is not None else None
    _add("gamestate", gs)
    for cls_name in (
        "GbxDiscoverySaveGameData",
        "GbxDiscoveryFODManagerCPU",
        "GbxDiscoveryFODBase",
        "GbxDiscoveryManager",
        "GbxDiscoveryPerCharacterProgressRole",
        "GbxDiscoveryPerCharacterProgressRole_Shared",
    ):
        for obj in _find_all_safe(cls_name)[:8]:
            if _is_skip_type(obj):
                continue
            _add(cls_name, obj)
    return roots


def _viewport_world() -> Any | None:
    try:
        from mods_base import ENGINE
    except Exception:
        return None
    try:
        viewport = getattr(ENGINE, "GameViewport", None)
        return getattr(viewport, "World", None) if viewport is not None else None
    except Exception:
        return None


def _game_state(pc: Any) -> Any | None:
    world = _viewport_world()
    if world is None and pc is not None:
        for name in ("GetWorld", "K2_GetWorld"):
            getter = getattr(pc, name, None)
            if callable(getter):
                try:
                    world = getter()
                except Exception:
                    world = None
                if world is not None:
                    break
        if world is None:
            try:
                world = getattr(pc, "World", None)
            except Exception:
                world = None
    try:
        gs = getattr(world, "GameState", None) if world is not None else None
    except Exception:
        gs = None
    if gs is not None and not _is_skip_type(gs):
        return gs
    for cls_name in ("OakGameState", "GbxGameState", "GameStateBase"):
        for obj in _find_all_safe(cls_name)[:12]:
            if obj is None or _is_skip_type(obj):
                continue
            path = _safe_str(obj)
            if "PersistentLevel" in path or "Transient" in path:
                return obj
            gs = obj
    return gs


def _dump_offset_window(obj: Any, label: str, lo: int = 0xA40, hi: int = 0xBC0) -> None:
    props = _iter_named_props(obj)
    near = [f"{n}@{off:#x}" for n, _p, off in props if lo <= off <= hi]
    disc = [f"{n}@{off:#x}" for n, _p, off in props if _looks_discovery(n)]
    _log(
        f"{label} nprops={len(props)} near_a70={near[:16] or 'none'} "
        f"discovery_props={disc[:16] or 'none'}"
    )


def _read_tarray(addr: int) -> tuple[int, int, int]:
    data = _read_u64(addr)
    count = _read_i32(addr + 8)
    maxn = _read_i32(addr + 12)
    return data, count, maxn


def _preview_bytes(addr: int, nbytes: int) -> str:
    if addr < 0x10000 or nbytes <= 0:
        return ""
    try:
        return ctypes.string_at(addr, min(16, nbytes)).hex()
    except Exception:
        return ""


def _plausible_tarray(data: int, count: int, maxn: int) -> bool:
    if count < 0 or count > 100000 or maxn < 0 or maxn > 100000:
        return False
    if count > 0 and (data < 0x10000 or data >= 0x7FF000000000):
        return False
    if maxn and count > maxn:
        return False
    return True


def _is_heap_ptr(data: int) -> bool:
    if data < 0x10000 or data >= 0x00007FFFFFF00000:
        return False
    return (data & 0x7) == 0


def _is_fod_grid(data: int, count: int, maxn: int) -> bool:
    return count == _FOD_GRID_COUNT and maxn >= count and _is_heap_ptr(data)


def _fill_existing_bitmap(data: int, count: int, maxn: int, *, min_bytes: int = 1) -> int:
    """Fill an already-allocated TArray. Do not realloc or bump Count."""
    if not _plausible_tarray(data, count, maxn) or count <= 0:
        return 0
    cap = count if maxn <= 0 else min(count, maxn)
    if cap < min_bytes:
        _log(f"GS-DISC skip small array count={count} max={maxn} head={_preview_bytes(data, cap)}")
        return 0
    nbytes = min(int(cap), 8192)
    if _write_bytes(data, b"\xff" * nbytes):
        _log(f"GS-DISC filled bytes={nbytes} head={_preview_bytes(data, 16)}")
        return nbytes
    _log("GS-DISC fill failed VirtualProtect/memmove")
    return 0


def _iter_fastarray_items(holder: Any) -> list[Any]:
    for name in ("items", "Items"):
        try:
            nested = getattr(holder, name, None)
        except Exception:
            nested = None
        if nested is None or nested is holder:
            continue
        rows: list[Any] = []
        try:
            n = int(len(nested))
        except Exception:
            n = -1
        limit = n if n >= 0 else 4096
        for i in range(limit):
            try:
                rows.append(nested[i])
            except Exception:
                break
        if rows:
            return rows
    return []


def _fill_replicated_bitfields(holder: Any) -> int:
    wrote = 0
    for item in _iter_fastarray_items(holder):
        for cand in (0xFFFFFFFF, -1):
            try:
                setattr(item, "BitField", cand)
                wrote += 1
                break
            except Exception:
                continue
    return wrote


def _fill_fod_cpu_grids() -> int:
    """Fill the live 128x128 FoD tile buffer on GbxDiscoveryFODManagerCPU."""
    wrote = 0
    seen: set[int] = set()
    for obj in _find_all_safe(_FOD_MANAGER_CLS):
        if obj is None or _is_skip_type(obj):
            continue
        base = _obj_addr(obj)
        if not base or base in seen:
            continue
        seen.add(base)
        offsets = [_FOD_GRID_OFF]
        for extra in range(0x80, 0x180, 8):
            if extra not in offsets:
                offsets.append(extra)
        filled = 0
        for off in offsets:
            data, count, maxn = _read_tarray(base + off)
            if not _is_fod_grid(data, count, maxn):
                continue
            nbytes = min(int(count), _FOD_GRID_COUNT)
            if _write_bytes(data, b"\xff" * nbytes):
                filled = nbytes
                _log(
                    f"FOD-GRID {_safe_str(obj)[:96]}+{off:#x} "
                    f"filled bytes={nbytes} count={count} max={maxn}"
                )
                break
        if filled:
            wrote += filled
        else:
            _log(f"FOD-GRID miss addr={base:#x} path={_safe_str(obj)[:96]}")
    return wrote


def _widen_fod_unfog_radius(radius: float = _FOD_UNFOG_WIDEN) -> int:
    """Widen live walk-unfog floats on GbxDiscoveryFODManagerCPU +0xC0 / +0xC8."""
    try:
        target = max(10000.0, float(radius))
    except Exception:
        target = _FOD_UNFOG_WIDEN
    wrote = 0
    for obj in _find_all_safe(_FOD_MANAGER_CLS):
        if obj is None or _is_skip_type(obj):
            continue
        base = _obj_addr(obj)
        if not base:
            continue
        for off in _FOD_UNFOG_OFFS:
            before = _read_f32(base + off)
            if before is None or before != before:
                continue
            if not (1.0 <= float(before) <= 1.0e8):
                continue
            if not _write_f32(base + off, target):
                continue
            after = _read_f32(base + off)
            wrote += 1
            _log(f"FOD-UNFOG {_safe_str(obj)[:96]}+{off:#x} {before} -> {after}")
    return wrote


def _fill_replicated_bit_array(holder: Any, label: str) -> int:
    if holder is None or callable(holder):
        return 0
    wrote = _fill_replicated_bitfields(holder)
    if wrote:
        _log(f"GS-DISC {label} BitField items +{wrote}")
    wrote += _fill_bit_container(holder)
    if wrote:
        _log(f"GS-DISC {label} bit container +{wrote}")
    for name, _prop, off in _iter_named_props(holder):
        lower = name.lower()
        if not any(tok in lower for tok in ("bit", "data", "item", "array", "fod", "reveal")):
            continue
        try:
            child = getattr(holder, name, None)
        except Exception:
            continue
        added = _fill_bit_container(child)
        if added:
            wrote += added
            _log(f"GS-DISC {label}.{name}@{off:#x} +{added}")
    base = _obj_addr(holder)
    if base:
        data, count, maxn = _read_tarray(base)
        _log(
            f"GS-DISC {label} as_tarray data={data:#x} count={count} max={maxn} "
            f"head={_preview_bytes(data, count)}"
        )
        if _plausible_tarray(data, count, maxn):
            wrote += _fill_existing_bitmap(data, count, maxn)
        for extra in (0x00, 0x08, 0x10, 0x18):
            data, count, maxn = _read_tarray(base + extra)
            if extra == 0:
                continue
            if _plausible_tarray(data, count, maxn) and count > 0:
                _log(
                    f"GS-DISC {label}+{extra:#x} data={data:#x} count={count} "
                    f"max={maxn} head={_preview_bytes(data, count)}"
                )
                wrote += _fill_existing_bitmap(data, count, maxn)
    return wrote


def _fill_gamestate_discovery_array(gs: Any) -> int:
    """Write live GameState.DiscoveryReplicatedBitArray (offset 0xA70)."""
    if gs is None:
        _log("GS-DISC no GameState")
        return 0
    base = _obj_addr(gs)
    _log(f"GS-DISC obj={_safe_str(gs)[:140]} addr={base:#x}")
    _dump_offset_window(gs, "GS-DISC")
    wrote = 0
    try:
        bits = getattr(gs, "DiscoveryReplicatedBitArray", None)
    except Exception:
        bits = None
    if bits is not None:
        wrote += _fill_replicated_bit_array(bits, "DiscoveryReplicatedBitArray")
    for name, _prop, off in _iter_named_props(gs):
        if name == "DiscoveryReplicatedLiveActors":
            continue
        if off != _GS_DISC_BIT_ARRAY and not _looks_discovery(name):
            continue
        if name == "DiscoveryReplicatedBitArray":
            continue
        try:
            value = getattr(gs, name, None)
        except Exception:
            value = None
        added = _fill_discovery_prop(gs, name, value) if value is not None else 0
        if added:
            wrote += added
            _log(f"GS-DISC reflect {name}@{off:#x} +{added}")
    if base:
        data, count, maxn = _read_tarray(base + _GS_DISC_BIT_ARRAY)
        _log(
            f"GS-DISC tarray+{_GS_DISC_BIT_ARRAY:#x} data={data:#x} "
            f"count={count} max={maxn} head={_preview_bytes(data, count)}"
        )
        if _plausible_tarray(data, count, maxn):
            wrote += _fill_existing_bitmap(data, count, maxn)
    return wrote


def _fill_discovery_arrays(pc: Any, ps: Any) -> int:
    wrote = 0
    for label, obj in _discovery_objects(pc, ps):
        wrote += _fill_named_seen_lists(obj)
        for name, _prop, _off in _iter_named_props(obj):
            if not _looks_discovery(name):
                continue
            try:
                value = getattr(obj, name, None)
            except Exception:
                continue
            added = _fill_discovery_prop(obj, name, value)
            if added:
                wrote += added
                _log(f"discovery write {label}.{name} +{added}")
        for nest in ("Metrics", "metrics", "DiscoveryMetrics", "SaveGameData"):
            try:
                child = getattr(obj, nest, None)
            except Exception:
                child = None
            if child is None or callable(child):
                continue
            wrote += _fill_named_seen_lists(child)
    return wrote


def _discover_current_location(pc: Any, ps: Any) -> int:
    loc = _pawn_location(pc)
    key = _new_struct(_DISCOVERED_KEY_PATH)
    if key is not None and loc is not None:
        for field in ("Location", "InLocation", "WorldLocation", "Position"):
            try:
                setattr(key, field, loc)
            except Exception:
                continue
            break
    variants: list[tuple[Any, ...]] = [()]
    if loc is not None:
        variants.extend([(loc,), (loc, 1), (loc, True)])
    if key is not None:
        variants.extend([(key,), (key, 1), (key, True)])
        if ps is not None:
            variants.append((key, 1, ps))
            variants.append((key, True, ps))
    wrote = 0
    for obj in (pc, ps):
        if obj is None:
            continue
        for method in _LOCATION_METHODS:
            if _call_variants(obj, method, variants):
                wrote += 1
                _log(f"{type(obj).__name__}.{method} OK")
    return wrote


def reveal_live_map(target_pc: Any = None, radius: float = _UNFOG_RADIUS) -> dict[str, Any]:
    """Mark discovery for one player, then try a walk-radius widen if present."""
    global _last_status
    try:
        radius_f = max(1000.0, float(radius))
    except Exception:
        radius_f = _UNFOG_RADIUS
    pc = target_pc if target_pc is not None else get_pc()
    ps = _player_state(pc)
    regions = _mark_discovery_regions(pc, ps)
    seen_lists = 0
    location_rpcs = 0
    gs_disc = 0
    fod_grid = _fill_fod_cpu_grids()
    unfog_widen = _widen_fod_unfog_radius(max(radius_f, _FOD_UNFOG_WIDEN))
    if pc is not None or ps is not None:
        seen_lists = _fill_discovery_arrays(pc, ps)
        location_rpcs = _discover_current_location(pc, ps)
        gs_disc = _fill_gamestate_discovery_array(_game_state(pc))

    holders = _collect_holders()
    setattr_n = 0
    memory_n = 0
    bools_n = 0
    touched = 0
    for label, obj in holders:
        props = _iter_named_props(obj)
        unfog_props = [f"{n}@{off}" for n, _p, off in props if "unfog" in n.lower() or n in _BOOL_FIELDS]
        _log(
            f"holder {label}: class={type(obj).__name__} addr={_obj_addr(obj):#x} "
            f"path={_safe_str(obj)[:140]} unfog_props={unfog_props[:12] or 'none'}"
        )
        counts = _apply_unfog_fields(obj, radius_f)
        wrote = int(counts["setattr"]) + int(counts["memory"])
        if wrote <= 0:
            continue
        touched += 1
        setattr_n += int(counts["setattr"])
        memory_n += int(counts["memory"])
        bools_n += int(counts["bools"])
        _log(
            f"wrote {label}: setattr={counts['setattr']} memory={counts['memory']} "
            f"bools={counts['bools']} obj={_safe_str(obj)[:96]}"
        )
    discovered = regions + seen_lists + location_rpcs + gs_disc + fod_grid + unfog_widen
    msg = (
        f"FoD discover regions={regions} seen/arrays={seen_lists} "
        f"location_rpcs={location_rpcs} gs_disc={gs_disc} fod_grid={fod_grid} "
        f"unfog_widen={unfog_widen}; unfog "
        f"{setattr_n + memory_n} field(s) on {touched}/{len(holders)} holder(s)."
    )
    if discovered == 0 and touched == 0:
        msg += " No live discovery writers accepted this pass."
    _log(msg)
    _last_status = {
        "wrote": discovered + setattr_n + memory_n,
        "setattr": setattr_n,
        "memory": memory_n,
        "holders": len(holders),
        "touched": touched,
        "regions": regions,
        "seen_lists": seen_lists,
        "arrays": gs_disc,
        "location_rpcs": location_rpcs,
        "gs_disc": gs_disc,
        "fod_grid": fod_grid,
        "unfog_widen": unfog_widen,
        "radius": radius_f,
        "message": msg,
    }
    return dict(_last_status)
