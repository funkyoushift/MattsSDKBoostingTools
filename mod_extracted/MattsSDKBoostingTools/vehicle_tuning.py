"""Vehicle presets + curated personal-vehicle spawn catalog (SQBT-inspired, reimplemented)."""
from __future__ import annotations

import json
import pkgutil
import time
from typing import Any

from mods_base import get_pc
from unrealsdk import logging

from .movement_adjustments import live_player_controllers, pawn_for_controller

_PREFIX = "[Matts SDK Boosting Tools | Vehicle]"

_PRESETS: dict[str, dict[str, float]] = {
    "boost": {
        "maxspeed": 12000.0,
        "BoostMaxSpeed": 20000.0,
        "MaxAccel": 40000.0,
        "BoostMaxAccel": 60000.0,
        "BoostConsumptionRateScalar": 0.0,
    },
    "crawl": {"maxspeed": 500.0, "BoostMaxSpeed": 700.0, "MaxAccel": 1200.0},
    "floaty": {
        "AirControl": 25.0,
        "AirBraking": 100.0,
        "DownforceCoefficient": 0.0,
        "PowerslideJumpHeight": 800.0,
        "GravityScalar": 0.35,
    },
    "orbit": {
        "maxspeed": 9000.0,
        "BoostMaxSpeed": 16000.0,
        "AirControl": 40.0,
        "DownforceCoefficient": 0.0,
        "PowerslideJumpHeight": 1200.0,
        "GravityScalar": -1.0,
    },
    "heavy": {"Mass": 25000.0, "DownforceCoefficient": 20.0, "maxspeed": 2500.0},
    "drift": {
        "BrakingAccel": 500.0,
        "BoostingBrakingAccel": 500.0,
        "PowerslideBoostSlideTime": 8.0,
        "PowerslideBoostDuration": 5.0,
        "maxspeed": 9000.0,
    },
}

# Retyped MIT-safe catalog (IDs/aliases/unlocks match SQBT vehicle_movement builtin).
_VEHICLE_SPAWN_BUILTIN: list[dict[str, Any]] = [
    {
        "id": "PV_Grazer",
        "aliases": ["grazer"],
        "label": "Grazer",
        "category": "base",
        "unlock": "Unlockable_Vehicles.Grazer",
        "verified": True,
    },
    {
        "id": "PV_Borg",
        "aliases": ["borg"],
        "label": "Borg",
        "category": "base",
        "unlock": "Unlockable_Vehicles.Borg",
        "verified": True,
    },
    {
        "id": "PV_Base",
        "aliases": ["base"],
        "label": "Base",
        "category": "base",
        "unlock": "Unlockable_Vehicles.Base",
    },
    {
        "id": "PV_shatterlandV1",
        "aliases": ["shatterland", "shatterlandv1", "shatter"],
        "label": "Shatterland V1",
        "category": "promo",
        "unlock": "Unlockable_Vehicles.ShatterlandV1",
    },
    {
        "id": "PV_City",
        "aliases": ["city"],
        "label": "City",
        "category": "promo",
        "unlock": "Unlockable_Vehicles.City",
    },
    {
        "id": "PV_CityOrder",
        "aliases": ["cityorder", "city_order"],
        "label": "City Order",
        "category": "promo",
        "unlock": "Unlockable_Vehicles.CityOrder",
    },
    {
        "id": "PV_Mountain",
        "aliases": ["mountain", "cello"],
        "label": "Mountain (Vault Card)",
        "category": "dlc",
        "unlock": "Unlockable_Vehicles.Mountain",
    },
    {
        "id": "PV_DarkSiren",
        "aliases": ["darksiren", "siren"],
        "label": "Dark Siren",
        "category": "character",
        "unlock": "Unlockable_Vehicles.DarkSiren",
    },
    {
        "id": "PV_DarkSiren_Proto",
        "aliases": ["darksiren_proto", "siren_proto"],
        "label": "Dark Siren (Proto)",
        "category": "character",
        "unreleased": True,
    },
    {
        "id": "PV_ExoSoldier",
        "aliases": ["exosoldier", "exo"],
        "label": "Exo Soldier",
        "category": "character",
        "unlock": "Unlockable_Vehicles.ExoSoldier",
    },
    {
        "id": "PV_ExoSoldier_Proto",
        "aliases": ["exosoldier_proto", "exo_proto"],
        "label": "Exo Soldier (Proto)",
        "category": "character",
        "unreleased": True,
    },
    {
        "id": "PV_Gravitar",
        "aliases": ["gravitar"],
        "label": "Gravitar",
        "category": "character",
        "unlock": "Unlockable_Vehicles.Gravitar",
    },
    {
        "id": "PV_Gravitar_Proto",
        "aliases": ["gravitar_proto"],
        "label": "Gravitar (Proto)",
        "category": "character",
        "unreleased": True,
    },
    {
        "id": "PV_Paladin",
        "aliases": ["paladin"],
        "label": "Paladin",
        "category": "character",
        "unlock": "Unlockable_Vehicles.Paladin",
    },
    {
        "id": "PV_Paladin_Proto",
        "aliases": ["paladin_proto"],
        "label": "Paladin (Proto)",
        "category": "character",
        "unreleased": True,
    },
]

_vehicle_catalog_cache: list[dict[str, Any]] | None = None
_last_vehicle_spawn_at = 0.0


def _log(msg: str) -> None:
    logging.info(f"{_PREFIX} {msg}")


def list_vehicle_presets() -> list[str]:
    return sorted(_PRESETS.keys())


def _normalize_vehicle_row(raw: dict[str, Any]) -> dict[str, Any] | None:
    def_id = str(raw.get("id") or "").strip()
    if not def_id:
        return None
    aliases = raw.get("aliases") if isinstance(raw.get("aliases"), list) else []
    row: dict[str, Any] = {
        "id": def_id,
        "aliases": [str(a).strip() for a in aliases if str(a).strip()],
        "label": str(raw.get("label") or def_id).strip() or def_id,
        "category": str(raw.get("category") or "vehicle").strip() or "vehicle",
    }
    unlock = str(raw.get("unlock") or "").strip()
    if unlock:
        row["unlock"] = unlock
    if raw.get("verified") is True:
        row["verified"] = True
    if raw.get("unreleased") is True:
        row["unreleased"] = True
    return row


def _load_vehicle_catalog_rows() -> list[dict[str, Any]]:
    """Prefer packaged vehicle_catalog.json when present; else builtin."""
    global _vehicle_catalog_cache
    if _vehicle_catalog_cache is not None:
        return [dict(row) for row in _vehicle_catalog_cache]
    rows: list[dict[str, Any]] = []
    try:
        package = __package__ or "MattsSDKBoostingTools"
        packaged = pkgutil.get_data(package, "vehicle_catalog.json")
        if packaged:
            data = json.loads(packaged.decode("utf-8"))
            entries = data.get("entries") if isinstance(data, dict) else None
            if isinstance(entries, list):
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    normalized = _normalize_vehicle_row(entry)
                    if normalized:
                        rows.append(normalized)
    except Exception as exc:
        _log(f"vehicle_catalog.json load failed: {exc!r}")
        rows = []
    if not rows:
        rows = [dict(row) for row in _VEHICLE_SPAWN_BUILTIN]
    _vehicle_catalog_cache = rows
    return [dict(row) for row in rows]


def list_vehicle_catalog() -> list[dict[str, Any]]:
    return _load_vehicle_catalog_rows()


def _write_float_field(obj: Any, attr: str, value: float) -> bool:
    if obj is None:
        return False
    try:
        current = getattr(obj, attr, None)
    except Exception:
        current = None
    if current is not None:
        wrote = False
        for sub in ("Value", "BaseValue"):
            if hasattr(current, sub):
                try:
                    cur = getattr(current, sub)
                    setattr(current, sub, int(value) if isinstance(cur, int) else float(value))
                    wrote = True
                except Exception:
                    continue
        if wrote:
            return True
    try:
        setattr(obj, attr, float(value))
        return True
    except Exception:
        return False


def _vehicle_roots(pawn: Any) -> list[Any]:
    roots: list[Any] = []
    if pawn is None:
        return roots
    roots.append(pawn)
    for attr in (
        "VehicleMovement",
        "OakVehicleMovement",
        "MovementComponent",
        "VehicleMovementComponent",
        "CharMoveComp",
    ):
        try:
            comp = getattr(pawn, attr, None)
            if comp is not None:
                roots.append(comp)
        except Exception:
            continue
    # Also try the vehicle the pawn is currently in.
    for attr in ("Vehicle", "CurrentVehicle", "GetVehicle"):
        try:
            val = getattr(pawn, attr, None)
            if callable(val):
                val = val()
            if val is not None:
                roots.append(val)
                for vattr in ("VehicleMovement", "OakVehicleMovement", "MovementComponent"):
                    try:
                        vcomp = getattr(val, vattr, None)
                        if vcomp is not None:
                            roots.append(vcomp)
                    except Exception:
                        pass
        except Exception:
            continue
    return roots


def _is_local_pc(pc: Any) -> bool:
    try:
        local = get_pc()
        if local is not None and pc is local:
            return True
    except Exception:
        pass
    for attr_name in ("IsLocalPlayerController", "IsPrimaryPlayer"):
        try:
            attr = getattr(pc, attr_name, None)
            if callable(attr) and bool(attr()):
                return True
        except Exception:
            continue
    return False


def _pcs_for_scope(scope: str) -> list[Any]:
    key = str(scope or "local").strip().lower()
    out: list[Any] = []
    for pc in live_player_controllers():
        is_local = _is_local_pc(pc)
        if key == "local" and not is_local:
            continue
        if key == "others" and is_local:
            continue
        out.append(pc)
    return out or ([get_pc()] if get_pc() is not None else [])


def apply_vehicle_preset(name: str, *, scope: str = "local") -> str:
    key = str(name or "").strip().lower()
    if key not in _PRESETS:
        return f"Unknown vehicle preset '{name}'. Try: {', '.join(sorted(_PRESETS))}."
    pcs = _pcs_for_scope(scope)
    writes = 0
    touched = 0
    for pc in pcs:
        pawn = pawn_for_controller(pc)
        roots = _vehicle_roots(pawn)
        if not roots:
            continue
        local_writes = 0
        for attr, val in _PRESETS[key].items():
            for root in roots:
                if _write_float_field(root, attr, float(val)):
                    local_writes += 1
                    break
        if local_writes:
            touched += 1
            writes += local_writes
    msg = f"Vehicle preset '{key}' applied scope={scope} players={touched} writes={writes}."
    _log(msg)
    if writes == 0:
        return msg + " No vehicle movement fields found — sit in / near a vehicle and retry."
    return msg


def _try_call(obj: Any, names: tuple[str, ...], arg_sets: tuple[tuple[Any, ...], ...]) -> tuple[bool, str]:
    for name in names:
        fn = getattr(obj, name, None)
        if not callable(fn):
            continue
        for args in arg_sets:
            try:
                fn(*args)
                return True, f"{name}{args!r}"
            except TypeError:
                continue
            except Exception as exc:
                return False, f"{name} failed: {exc!r}"
    return False, "no matching RPC"


def _find_vehicle_entry(def_id_or_alias: str) -> dict[str, Any] | None:
    needle = str(def_id_or_alias or "").strip()
    if not needle:
        return None
    low = needle.casefold()
    for row in _load_vehicle_catalog_rows():
        if str(row["id"]).casefold() == low or low in {a.casefold() for a in row.get("aliases", [])}:
            return row
    return None


def _unlock_token_for_vehicle(def_id: str, entry: dict[str, Any] | None = None) -> str | None:
    if entry is not None:
        token = str(entry.get("unlock") or "").strip()
        if token:
            return token
    stem = def_id[3:] if def_id.startswith("PV_") else def_id
    if stem.lower() == "shatterlandv1":
        return "Unlockable_Vehicles.ShatterlandV1"
    return f"Unlockable_Vehicles.{stem}"


def _get_player_state(pc: Any) -> Any | None:
    for attr in ("PlayerState", "OakPlayerState"):
        try:
            ps = getattr(pc, attr, None)
            if ps is not None:
                return ps
        except Exception:
            continue
    return None


def _try_unlock_unlockable(pc: Any, token: str) -> tuple[bool, str]:
    """Best-effort ClientUnlockUnlockable on PlayerState (no ultra_local_menu dependency)."""
    ps = _get_player_state(pc)
    if ps is None:
        return False, "no PlayerState"
    fn = getattr(ps, "ClientUnlockUnlockable", None)
    if not callable(fn):
        return False, "ClientUnlockUnlockable missing"
    last = "unlock failed"
    candidates: list[Any] = []
    try:
        from unrealsdk.unreal import FGbxDefPtr  # type: ignore[import-not-found]

        ptr = FGbxDefPtr(token, type="UnlockableEntryDef")
        inst = getattr(ptr, "_experimental_instance", None)
        if inst is not None:
            candidates.extend([inst, ptr])
    except Exception:
        pass
    candidates.append(token)
    if "." in token:
        ledger, entry = token.split(".", 1)
        for lv, ev in ((ledger, entry), (f"/Script/OakGame.{ledger}", entry)):
            for args in ((lv, ev), (ev, lv)):
                try:
                    fn(*args)
                    return True, f"ClientUnlockUnlockable({lv},{ev})"
                except Exception as exc:
                    last = str(exc)
    for arg in candidates:
        try:
            fn(arg)
            return True, f"ClientUnlockUnlockable({token})"
        except TypeError:
            continue
        except Exception as exc:
            last = str(exc)
    return False, last


def _try_unlock_vehicle_for_spawn(pc: Any, def_id: str, entry: dict[str, Any] | None = None) -> tuple[bool, str]:
    token = _unlock_token_for_vehicle(def_id, entry)
    if not token:
        return False, "no unlock token"
    return _try_unlock_unlockable(pc, token)


def unlock_all_vehicles_for_pc(pc: Any) -> tuple[bool, str]:
    """Best-effort unlock of every catalog vehicle + known Unlockable_Vehicles tokens."""
    if pc is None:
        return False, "no PlayerController"
    ok = 0
    fail = 0
    seen: set[str] = set()
    for row in _load_vehicle_catalog_rows():
        def_id = str(row.get("id") or "").strip()
        token = _unlock_token_for_vehicle(def_id, row)
        if not token or token in seen:
            continue
        seen.add(token)
        success, _how = _try_unlock_unlockable(pc, token)
        if success:
            ok += 1
        else:
            fail += 1
    # Also hit common personal-vehicle unlock stems even if catalog missed them.
    for stem in (
        "Grazer",
        "Borg",
        "Base",
        "ShatterlandV1",
        "City",
        "CityOrder",
        "Mountain",
        "DarkSiren",
        "ExoSoldier",
        "Gravitar",
        "Paladin",
    ):
        token = f"Unlockable_Vehicles.{stem}"
        if token in seen:
            continue
        seen.add(token)
        success, _how = _try_unlock_unlockable(pc, token)
        if success:
            ok += 1
        else:
            fail += 1
    detail = f"unlocked={ok} failed={fail} tokens={len(seen)}"
    _log(f"unlock_all_vehicles: {detail}")
    return ok > 0, detail


def spawn_personal_vehicle(def_id_or_alias: str, *, scope: str = "local") -> str:
    """Best-effort personal vehicle summon via OakPlayerController RPCs."""
    global _last_vehicle_spawn_at
    now = time.monotonic()
    if now - _last_vehicle_spawn_at < 0.75:
        return "Vehicle spawn cooldown — wait a moment."
    needle = str(def_id_or_alias or "").strip()
    if not needle:
        return "No vehicle id selected."
    entry = _find_vehicle_entry(needle)
    def_id = str(entry["id"]) if entry else (needle if needle.startswith("PV_") else f"PV_{needle}")
    pcs = _pcs_for_scope(scope)
    if not pcs:
        return "Vehicle spawn failed: no player controllers."
    ok_any = False
    details: list[str] = []
    for pc in pcs:
        unlock_ok, unlock_how = _try_unlock_vehicle_for_spawn(pc, def_id, entry)
        details.append(f"unlock={'ok:' + unlock_how if unlock_ok else 'skip:' + unlock_how}")
        wrote, how = _try_call(
            pc,
            ("ServerSetPersonalVehicleDef", "SetPersonalVehicleDef", "ClientSetPersonalVehicleDef"),
            ((def_id,), (def_id, True)),
        )
        details.append(f"set={how}")
        req_ok, req_how = _try_call(
            pc,
            ("ServerRequestPersonalVehicle", "RequestPersonalVehicle", "SummonPersonalVehicle"),
            ((), (True,), (False,)),
        )
        details.append(f"req={req_how}")
        ok_any = ok_any or wrote or req_ok
    if ok_any:
        _last_vehicle_spawn_at = now
    label = entry.get("label", def_id) if entry else def_id
    msg = f"Vehicle spawn requested: {label} ({def_id}) scope={scope}. {' | '.join(details)}"
    _log(msg)
    return msg if ok_any else f"Vehicle spawn likely failed for {def_id}. {msg}"
