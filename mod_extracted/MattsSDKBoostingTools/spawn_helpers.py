"""Thin spawn-anchor + aggro helpers for Dev Spawner (MIT-pattern reimplementation).

Tracks recently spawned ASD actors best-effort and can re-aggro them toward
the local player / party. Not a full port of SQBT mob_spawner aggro.py.
"""
from __future__ import annotations

import time
from typing import Any

import unrealsdk
from mods_base import get_pc
from unrealsdk import logging

from .movement_adjustments import live_player_controllers, pawn_for_controller

_PREFIX = "[Matts SDK Boosting Tools | SpawnHelpers]"

AGGRO_MODES = ("passive", "attack_me", "attack_party", "free_for_all")
SPAWN_ANCHORS = ("local", "selected", "party", "npc_nearest")

_tracked_mobs: list[Any] = []
_tracked_at: float = 0.0
_TRACK_TTL_S = 180.0
_current_aggro_mode = "passive"
_current_spawn_anchor = "local"


def _log(msg: str) -> None:
    logging.info(f"{_PREFIX} {msg}")


def set_aggro_mode(mode: str) -> str:
    global _current_aggro_mode
    key = str(mode or "passive").strip().lower()
    if key in ("none", "off"):
        key = "passive"
    if key not in AGGRO_MODES:
        return f"Unknown aggro mode '{mode}'. Use: {', '.join(AGGRO_MODES)}"
    _current_aggro_mode = key
    return f"Aggro mode set to {_current_aggro_mode}."


def get_aggro_mode() -> str:
    return _current_aggro_mode


def set_spawn_anchor(anchor: str) -> str:
    global _current_spawn_anchor
    key = str(anchor or "local").strip().lower()
    if key not in SPAWN_ANCHORS:
        return f"Unknown spawn anchor '{anchor}'. Use: {', '.join(SPAWN_ANCHORS)}"
    _current_spawn_anchor = key
    return f"Spawn anchor set to {_current_spawn_anchor}."


def get_spawn_anchor() -> str:
    return _current_spawn_anchor


def actor_location(actor: Any) -> Any | None:
    if actor is None:
        return None
    for name in ("K2_GetActorLocation", "GetActorLocation"):
        fn = getattr(actor, name, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
    return None


def _distance_sq(a: Any, b: Any) -> float:
    return (
        (float(a.X) - float(b.X)) ** 2
        + (float(a.Y) - float(b.Y)) ** 2
        + (float(a.Z) - float(b.Z)) ** 2
    )


def _local_pawn() -> Any | None:
    try:
        return pawn_for_controller(get_pc())
    except Exception:
        return None


def _selected_pawn() -> Any | None:
    """Named party target from the live selected-player index (lazy import)."""
    try:
        from . import backend_actions as ba
        idx = ba.get_selected_player_index()
        if idx is None:
            return None
        return ba._pawn_for_party_index(idx)
    except Exception:
        return None


def _party_pawns() -> list[Any]:
    out: list[Any] = []
    seen: set[int] = set()
    for pc in live_player_controllers():
        pawn = pawn_for_controller(pc)
        if pawn is None:
            continue
        pid = id(pawn)
        if pid in seen:
            continue
        seen.add(pid)
        out.append(pawn)
    return out


def nearest_npc(origin_actor: Any, *, max_distance: float = 14000.0) -> Any | None:
    origin = actor_location(origin_actor)
    if origin is None:
        return None
    player_ids = {id(p) for p in _party_pawns()}
    best: Any | None = None
    best_dist = max(100.0, float(max_distance)) ** 2
    seen: set[int] = set()
    for class_name in ("OakCharacter", "GbxCharacter", "Character"):
        try:
            actors = unrealsdk.find_all(class_name, False) or []
        except Exception:
            continue
        for actor in actors:
            key = id(actor)
            if key in seen or key in player_ids:
                continue
            seen.add(key)
            name = str(getattr(actor, "Name", "") or "")
            if not name or name.startswith("Default__"):
                continue
            cls = str(getattr(getattr(actor, "Class", None), "Name", "") or "").lower()
            if "player" in cls:
                continue
            if not any(token in cls for token in ("character", "enemy", "npc", "boss", "badass")):
                continue
            loc = actor_location(actor)
            if loc is None:
                continue
            dist = _distance_sq(origin, loc)
            if dist < best_dist:
                best_dist = dist
                best = actor
    return best


def resolve_spawn_anchor_actor() -> tuple[Any | None, str]:
    """Return (anchor_actor, label) for current spawn-anchor setting."""
    local = _local_pawn()
    mode = _current_spawn_anchor
    if mode == "local":
        return local, "local"
    if mode == "selected":
        pawn = _selected_pawn()
        if pawn is not None:
            return pawn, "selected"
        return local, "local(fallback-no-selected)"
    if mode == "party":
        party = _party_pawns()
        if not party:
            return local, "local(fallback)"
        # Prefer first non-local party member if present, else local.
        try:
            local_id = id(local) if local is not None else -1
            for pawn in party:
                if id(pawn) != local_id:
                    return pawn, "party"
        except Exception:
            pass
        return party[0], "party"
    if mode == "npc_nearest":
        origin = local or ( _party_pawns()[0] if _party_pawns() else None)
        npc = nearest_npc(origin) if origin is not None else None
        if npc is not None:
            return npc, "npc_nearest"
        return local, "local(fallback-no-npc)"
    return local, "local"


def note_spawned_actors(actors: list[Any] | None = None) -> None:
    """Remember actors for later re-aggro. Best-effort; TTL expires old tracks."""
    global _tracked_mobs, _tracked_at
    now = time.monotonic()
    if now - _tracked_at > _TRACK_TTL_S:
        _tracked_mobs = []
    if actors:
        for actor in actors:
            if actor is None:
                continue
            if actor not in _tracked_mobs:
                _tracked_mobs.append(actor)
        _tracked_at = now
        return
    # Fallback: scan nearby non-player characters and keep the newest handful.
    local = _local_pawn()
    origin = actor_location(local) if local is not None else None
    if origin is None:
        return
    player_ids = {id(p) for p in _party_pawns()}
    found: list[tuple[float, Any]] = []
    for class_name in ("OakCharacter", "GbxCharacter"):
        try:
            for actor in unrealsdk.find_all(class_name, False) or []:
                if actor is None or id(actor) in player_ids:
                    continue
                loc = actor_location(actor)
                if loc is None:
                    continue
                dist = _distance_sq(origin, loc)
                if dist <= 8000.0 ** 2:
                    found.append((dist, actor))
        except Exception:
            continue
    found.sort(key=lambda row: row[0])
    for _dist, actor in found[:24]:
        if actor not in _tracked_mobs:
            _tracked_mobs.append(actor)
    _tracked_at = now


def _prune_tracked() -> list[Any]:
    global _tracked_mobs, _tracked_at
    if time.monotonic() - _tracked_at > _TRACK_TTL_S:
        _tracked_mobs = []
        _tracked_at = 0.0
        return []
    live: list[Any] = []
    for mob in _tracked_mobs:
        if mob is None:
            continue
        try:
            name = str(getattr(mob, "Name", "") or "")
            if not name or name.startswith("Default__"):
                continue
            live.append(mob)
        except Exception:
            continue
    _tracked_mobs = live[-48:]
    return list(_tracked_mobs)


def clear_tracked() -> None:
    """Release cached actor wrappers after travel or an explicit cleanup."""
    global _tracked_mobs, _tracked_at
    _tracked_mobs = []
    _tracked_at = 0.0


def _try_set_enemy(attacker: Any, target: Any) -> bool:
    if attacker is None or target is None:
        return False
    controllers = []
    for attr in ("Controller", "AIController", "OakAIController"):
        try:
            ctrl = getattr(attacker, attr, None)
            if ctrl is not None:
                controllers.append(ctrl)
        except Exception:
            pass
    controllers.append(attacker)
    for obj in controllers:
        for meth in ("SetEnemy", "SetFocus", "EngageTarget", "StartCombat", "SetTargetActor"):
            fn = getattr(obj, meth, None)
            if not callable(fn):
                continue
            for args in ((target,), (target, True), (target, 1.0)):
                try:
                    fn(*args)
                    return True
                except TypeError:
                    continue
                except Exception:
                    continue
    return False


def apply_aggro_to_tracked(*, mode: str | None = None) -> str:
    """Apply aggro mode to tracked / nearby mobs."""
    use_mode = str(mode or _current_aggro_mode or "passive").strip().lower()
    if use_mode in ("passive", "none", "off"):
        return "Aggro passive — no targeting applied."
    mobs = _prune_tracked()
    if not mobs:
        note_spawned_actors(None)
        mobs = _prune_tracked()
    if not mobs:
        return "No tracked mobs to aggro. Spawn something first, then Re-Aggro."
    local = _local_pawn()
    party = _party_pawns()
    ok_n = 0
    fail_n = 0
    if use_mode in ("attack_me", "me"):
        if local is None:
            return "Aggro failed: local pawn missing."
        for mob in mobs:
            if _try_set_enemy(mob, local):
                ok_n += 1
            else:
                fail_n += 1
        return f"Attack-me aggro: ok={ok_n} miss={fail_n} mobs={len(mobs)}."
    if use_mode in ("attack_party", "party"):
        if not party:
            return "Aggro failed: no party pawns."
        for i, mob in enumerate(mobs):
            tgt = party[i % len(party)]
            if _try_set_enemy(mob, tgt):
                ok_n += 1
            else:
                fail_n += 1
        return f"Attack-party aggro: ok={ok_n} miss={fail_n} mobs={len(mobs)}."
    if use_mode in ("free_for_all", "ffa"):
        if len(mobs) < 2:
            return "Free-for-all needs 2+ tracked mobs."
        for i, mob in enumerate(mobs):
            tgt = mobs[(i + 1) % len(mobs)]
            if _try_set_enemy(mob, tgt):
                ok_n += 1
            else:
                fail_n += 1
        return f"FFA aggro: ok={ok_n} miss={fail_n} mobs={len(mobs)}."
    return f"Unknown aggro mode '{use_mode}'."


def reaggro_tracked() -> str:
    return apply_aggro_to_tracked(mode=_current_aggro_mode)
