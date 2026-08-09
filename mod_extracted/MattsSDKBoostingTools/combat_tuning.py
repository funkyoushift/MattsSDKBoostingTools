"""Curated damage / resource tuning for MSBT (apply-once; sticky off by default).

Field names mirror Live Editor OakDamageState / OakDamageCauserData dumps.
Session-only: values may reset on travel — call apply again after map change.
"""
from __future__ import annotations

from typing import Any

from mods_base import get_pc
from unrealsdk import logging

from .movement_adjustments import live_player_controllers, live_player_pawns, pawn_for_controller

_PREFIX = "[Matts SDK Boosting Tools | CombatTuning]"

# Curated subset — not the full SQBT slider matrix.
_DS_FIELDS = (
    "DamageTakenMultiplier",
    "RadiusDamageTakenMultiplier",
    "HealingReceivedMultiplier",
)
_DCD_FIELDS = (
    "DamageDealtMultiplier",
    "RadiusDamage_DamageMultiplier",
    "HealingDealtMultiplier",
)
_REPAIR_PATHS = (
    "HealthState.RepairKitMaxCharges",
    "HealthState.RepairKitCooldown",
    "HealthState.RepairKitDuration",
)
_AMMO_FIELDS = ("ammoregenrate",)

# Sticky re-apply is OFF by default (Matt preference). Last payload retained for
# optional reapply-after-travel from Electron / QM.
_last_payload: dict[str, float] = {}
_sticky_enabled: bool = False


def _log(msg: str) -> None:
    logging.info(f"{_PREFIX} {msg}")


def _write_gbx_pair(container: Any, field: str, value: float) -> bool:
    if container is None:
        return False
    try:
        st = getattr(container, field, None)
    except Exception:
        return False
    if st is None:
        return False
    ok = False
    for sub in ("Value", "BaseValue"):
        if hasattr(st, sub):
            try:
                current = getattr(st, sub)
                new_value = int(round(value)) if isinstance(current, int) else float(value)
                setattr(st, sub, new_value)
                ok = True
            except Exception:
                continue
    if ok:
        return True
    try:
        setattr(container, field, float(value))
        return True
    except Exception:
        return False


def _resolve_path(root: Any, path: str) -> Any | None:
    obj = root
    for part in str(path).split("."):
        if obj is None:
            return None
        try:
            obj = getattr(obj, part)
        except Exception:
            return None
    return obj


def _write_pawn_pair(pawn: Any, path: str, value: float) -> bool:
    parts = str(path).rsplit(".", 1)
    if len(parts) != 2:
        return _write_gbx_pair(pawn, path, value)
    return _write_gbx_pair(_resolve_path(pawn, parts[0]), parts[1], value)


def _damage_state(pawn: Any) -> Any | None:
    for attr in ("DamageState", "damageState"):
        try:
            ds = getattr(pawn, attr, None)
            if ds is not None:
                return ds
        except Exception:
            continue
    return None


def _damage_causer_data(pawn: Any) -> Any | None:
    for attr in ("DamageCauserData", "damageCauserData"):
        try:
            d = getattr(pawn, attr, None)
            if d is not None:
                return d
        except Exception:
            continue
    return None


def _is_local_pc(pc: Any) -> bool:
    if pc is None:
        return False
    try:
        local = get_pc()
        if local is not None and pc is local:
            return True
    except Exception:
        pass
    for attr_name in ("IsLocalPlayerController", "IsPrimaryPlayer", "bIsLocalPlayerController"):
        try:
            attr = getattr(pc, attr_name, None)
            if callable(attr) and bool(attr()):
                return True
            if attr is not None and not callable(attr) and bool(attr):
                return True
        except Exception:
            continue
    return False


def _pawns_for_scope(scope: str) -> list[Any]:
    key = str(scope or "local").strip().lower()
    if key not in ("local", "all", "others"):
        key = "local"
    controllers = live_player_controllers()
    out: list[Any] = []
    seen: set[int] = set()
    for pc in controllers:
        is_local = _is_local_pc(pc)
        if key == "local" and not is_local:
            continue
        if key == "others" and is_local:
            continue
        pawn = pawn_for_controller(pc)
        if pawn is None:
            continue
        pid = id(pawn)
        if pid in seen:
            continue
        seen.add(pid)
        out.append(pawn)
    if key == "all" and not out:
        for pawn in live_player_pawns():
            pid = id(pawn)
            if pid not in seen:
                seen.add(pid)
                out.append(pawn)
    return out


def _apply_to_pawn(pawn: Any, values: dict[str, float]) -> tuple[int, int]:
    ok = 0
    fail = 0
    ds = _damage_state(pawn)
    dcd = _damage_causer_data(pawn)

    def bump(good: bool) -> None:
        nonlocal ok, fail
        if good:
            ok += 1
        else:
            fail += 1

    for field in _DS_FIELDS:
        if field not in values:
            continue
        bump(_write_gbx_pair(ds, field, float(values[field])) if ds is not None else False)
    for field in _DCD_FIELDS:
        if field not in values:
            continue
        bump(_write_gbx_pair(dcd, field, float(values[field])) if dcd is not None else False)
    for path in _REPAIR_PATHS:
        short = path.rsplit(".", 1)[-1]
        if path not in values and short not in values:
            continue
        bump(_write_pawn_pair(pawn, path, float(values.get(path, values.get(short, 0.0)))))
    for field in _AMMO_FIELDS:
        if field not in values:
            continue
        bump(_write_gbx_pair(pawn, field, float(values[field])))
    return ok, fail


def normalize_combat_payload(payload: dict[str, Any] | None) -> dict[str, float]:
    """Map Electron / bridge keys onto Oak field names."""
    payload = payload or {}
    aliases = {
        "damage_dealt": "DamageDealtMultiplier",
        "damage_taken": "DamageTakenMultiplier",
        "radius_damage_dealt": "RadiusDamage_DamageMultiplier",
        "radius_damage_taken": "RadiusDamageTakenMultiplier",
        "healing_dealt": "HealingDealtMultiplier",
        "healing_received": "HealingReceivedMultiplier",
        "repair_kit_max": "HealthState.RepairKitMaxCharges",
        "repair_kit_cooldown": "HealthState.RepairKitCooldown",
        "repair_kit_duration": "HealthState.RepairKitDuration",
        "ammo_regen": "ammoregenrate",
        "RepairKitMaxCharges": "HealthState.RepairKitMaxCharges",
        "RepairKitCooldown": "HealthState.RepairKitCooldown",
        "RepairKitDuration": "HealthState.RepairKitDuration",
    }
    out: dict[str, float] = {}
    for key, raw in payload.items():
        if key in ("scope", "sticky", "combat_scope", "combat_sticky"):
            continue
        field = aliases.get(str(key), str(key))
        try:
            out[field] = float(raw)
        except Exception:
            continue
    return out


def apply_combat_tuning(payload: dict[str, Any] | None = None) -> str:
    """Apply curated damage/resource values once (sticky off unless requested)."""
    global _last_payload, _sticky_enabled
    payload = dict(payload or {})
    scope = str(payload.get("scope") or payload.get("combat_scope") or "local").strip().lower()
    sticky_raw = payload.get("sticky", payload.get("combat_sticky", False))
    _sticky_enabled = bool(sticky_raw) and str(sticky_raw).strip().lower() not in ("0", "false", "off", "no")
    values = normalize_combat_payload(payload)
    if not values:
        # Sensible defaults when Electron sends only the curated knobs as empty → use 1.0 / repair defaults.
        values = {
            "DamageDealtMultiplier": float(payload.get("damage_dealt", 1.0) or 1.0),
            "DamageTakenMultiplier": float(payload.get("damage_taken", 1.0) or 1.0),
            "HealthState.RepairKitMaxCharges": float(payload.get("repair_kit_max", 3.0) or 3.0),
            "HealthState.RepairKitCooldown": float(payload.get("repair_kit_cooldown", 20.0) or 20.0),
            "ammoregenrate": float(payload.get("ammo_regen", 0.0) or 0.0),
        }
    _last_payload = dict(values)
    pawns = _pawns_for_scope(scope)
    if not pawns:
        return "Combat tuning skipped: no matching player pawns for scope."
    total_ok = 0
    total_fail = 0
    for pawn in pawns:
        ok, fail = _apply_to_pawn(pawn, values)
        total_ok += ok
        total_fail += fail
    sticky_note = " sticky=ON" if _sticky_enabled else " sticky=OFF"
    msg = (
        f"Combat tuning applied scope={scope} pawns={len(pawns)} "
        f"writes_ok={total_ok} miss={total_fail}.{sticky_note}"
    )
    _log(msg)
    return msg


def reapply_combat_tuning() -> str:
    """Re-apply last payload (e.g. after travel). No-op if nothing was applied yet."""
    if not _last_payload:
        return "No prior combat tuning to re-apply."
    return apply_combat_tuning({**_last_payload, "sticky": _sticky_enabled, "scope": "local"})


def reset_combat_tuning(scope: str = "local") -> str:
    """Reset curated fields toward defaults."""
    defaults = {
        "DamageDealtMultiplier": 1.0,
        "DamageTakenMultiplier": 1.0,
        "RadiusDamage_DamageMultiplier": 1.0,
        "RadiusDamageTakenMultiplier": 1.0,
        "HealingDealtMultiplier": 1.0,
        "HealingReceivedMultiplier": 1.0,
        "HealthState.RepairKitMaxCharges": 3.0,
        "HealthState.RepairKitCooldown": 20.0,
        "HealthState.RepairKitDuration": 8.0,
        "ammoregenrate": 0.0,
        "scope": scope,
        "sticky": False,
    }
    return apply_combat_tuning(defaults)


def combat_tuning_sticky_enabled() -> bool:
    return bool(_sticky_enabled)
