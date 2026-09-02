"""Hoard Builder wave runner — sequenced ASD_spawnai waves with clear-when-dead advance.

Host-session state only. Electron persists the plan in localStorage; this module
owns the live run (index, tracked actors, tick). Does not import BLImGui.
"""
from __future__ import annotations

import importlib
import random
import time
from collections import deque
from typing import Any

from unrealsdk import logging

_PREFIX = "[Matts SDK Boosting Tools | Hoard]"

# Grace period after spawnai so async/queued spawns are not treated as "cleared".
_SPAWN_GRACE_S = 3.0
# Extra wait after grace before giving up if we never saw a live actor.
# ASD thin-air often queues and only reports alive a few seconds later.
_SPAWN_ARM_EXTRA_S = 12.0

# Pacing — not small caps — is what keeps frames survivable. One ASD spawn call
# per scheduled step, never two at once.
_SPAWN_STEP_INTERVAL_S = 0.45
_SPAWN_STEP_MIN_S = 0.15
_SPAWN_STEP_MAX_S = 5.0

# Waves are effectively unlimited; this only stops a malformed payload from
# allocating forever.
_MAX_WAVES = 500
# 60 live AI per wave is roughly where BL4's own encounters top out, and at the
# default burst pacing it still trickles in over ~14s instead of one spike.
_MAX_COUNT = 60
_MAX_WAVE_TOTAL = 60
_MAX_WAVE_TYPES = 12

# Spawn nodes: distinct points around the player, not one perfect ring.
_SPAWN_POINTS_DEFAULT = 6
_SPAWN_POINTS_MIN = 1
_SPAWN_POINTS_MAX = 12
# Enemies that emerge from one node per turn (round-robin between nodes).
_BURST_DEFAULT = 2
_BURST_MIN = 1
_BURST_MAX = 6
# Break up the geometry: angle wobble inside each sector, distance wobble per node.
_NODE_ANGLE_JITTER = 0.7
_NODE_DISTANCE_JITTER = 0.30
# 350uu is roughly melee range, so the old default dropped bosses on top of the
# player. The floor is applied after jitter, so a node can never land inside the
# player even at the smallest distance the UI allows.
_NODE_DISTANCE_MIN = 600.0
_NODE_DISTANCE_MAX = 4000.0
_WAVE_DISTANCE_DEFAULT = 900.0

# hide_ground_loot() parks every InventoryPickup in a far XY pocket. Running that
# automatically at every wave transition used to crash the game, so it is opt-in
# and rate limited.
_LOOT_CLEANUP_MIN_INTERVAL_S = 20.0

# Three crashes in a row all landed in the same window: this module reaching into
# spawner actors — or the actors those spawners own — while the engine was still
# processing a mass death. Deferring the destroy only moved the window; it did not
# close it. So nothing here destroys an actor any more. Waves only ever switch
# spawners off (flag flips, no ownership walk), and the destructive ASD_clear
# stays behind the user's own Clear button.
_POST_WAVE_DISABLE_DELAY_S = 2.0
_CLEAR_BUTTON_CLEANUP_DELAY_S = 2.5
_CLEANUP_RETRY_DELAY_S = 0.5
# No spawner component is touched, and no wave is spawned, within this long of a
# wave dying. "Kill All" drops a whole wave in one frame and the engine keeps
# walking those actors for death, loot and score handling well past it.
_DEATH_QUIET_S = 1.5

# Harvested OakSpawner pads in the loaded cell. Read location only — never
# Reset/enable map spawners. 4–8 discrete points, then cycle them.
_HARVEST_MIN = 4
_HARVEST_MAX = 8
_HARVEST_DEDUP_UU = 400.0
_ARENA_HERE = "here"
_ARENA_ABANDONED_POST = "World_P.FT_GRA_BeachTower"
_HARVEST_SKIP_TOKENS = (
    "grapple",
    "zipline",
    "ladder",
    "elevator",
    "fasttravel",
    "travelstation",
    "checkpoint",
    "savepoint",
    "mission",
    "quest",
    "interact",
    "io_",
    "loot",
    "pickup",
    "chest",
    "container",
    "vehicle",
    "vending",
    "shop",
    "menu",
    "tutorial",
    "cine",
    "cinematic",
    "msbt",
)

# The bridge tick hook is /Script/GbxUIUMG.GbxUIUMGTickWidget:BP_TickWidget, which
# fires once per widget instance and so can run many times in a single frame.
# Collapse that into at most one hoard operation per interval, globally.
_TICK_MIN_INTERVAL_S = 0.10

# Skipping a step because the world is not ready is cheap; spinning forever is not.
_MAX_WORLD_WAIT_S = 45.0

_rng = random.Random()

_plan: list[dict[str, Any]] = []
_running: bool = False
_complete: bool = False
_wave_index: int = 0
_message: str = "Idle"
_wave_items: list[Any] = []  # ASD DeployedActor entries for the active wave
_wave_spawners: list[Any] = []
_expected_count: int = 0
_spawn_grace_until: float = 0.0
_pre_spawn_keys: set[str] = set()
_pre_spawn_spawner_ids: set[int] = set()
_last_alive: int = 0
_wave_seen_alive: bool = False
_spawn_phase: bool = False
_spawn_next_at: float = 0.0
_pending_spawn_jobs: deque[dict[str, Any]] = deque()
_spawn_failures: list[str] = []
_active_wave: dict[str, Any] = {}
_spawn_nodes: list[dict[str, Any]] = []
_spawn_requested: int = 0
# Reentrancy guards: ASD spawns load packages and finish deferred actors, which
# can pump the engine and re-enter the bridge tick hook we are called from.
_spawn_in_flight: bool = False
_tick_in_flight: bool = False
_world_wait_since: float = 0.0
_loot_cleanup_last_at: float = 0.0
# Deferred cleanup (spawner disable / user-invoked ASD clear / opt-in loot hide).
_pending_cleanup_at: float = 0.0
_pending_cleanup_spawners: list[Any] = []
_pending_cleanup_asd_clear: bool = False
_pending_cleanup_loot: bool = False
_cleanup_in_flight: bool = False
# When we last saw a wave die. Everything that touches the world stays clear of it.
_last_death_at: float = 0.0
_last_tick_at: float = 0.0
_arena_station: str = ""
_harvested_points: list[dict[str, Any]] = []
_harvest_pending: bool = False


def _log(msg: str) -> None:
    logging.info(f"{_PREFIX} {msg}")


def _clamp_int(value: object, lo: int, hi: int, default: int) -> int:
    try:
        n = int(value)  # type: ignore[arg-type]
    except Exception:
        return default
    return max(lo, min(hi, n))


def _clamp_float(value: object, lo: float, hi: float, default: float) -> float:
    try:
        n = float(value)  # type: ignore[arg-type]
    except Exception:
        return default
    if n != n:  # NaN
        return default
    return max(lo, min(hi, n))


def _normalize_entry(raw: object) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    actor_id = str(
        raw.get("actor_id")
        or raw.get("actor")
        or raw.get("dev_ai_name")
        or raw.get("name")
        or ""
    ).strip()
    if not actor_id:
        return None
    count = _clamp_int(raw.get("count") or raw.get("dev_ai_count") or 1, 1, _MAX_COUNT, 1)
    return {"actor_id": actor_id, "count": count}


def _normalize_wave(raw: object) -> dict[str, Any] | None:
    """Accept multi-entry waves or legacy single actor_id/count waves."""
    if not isinstance(raw, dict):
        return None
    spacing = _clamp_float(raw.get("spacing") or raw.get("dev_ai_spacing"), 1.0, 5000.0, 125.0)
    scale = _clamp_float(raw.get("scale") or raw.get("dev_ai_scale"), 0.05, 20.0, 1.0)
    distance = _clamp_float(
        raw.get("distance") or raw.get("dev_ai_distance"),
        _NODE_DISTANCE_MIN,
        _NODE_DISTANCE_MAX,
        _WAVE_DISTANCE_DEFAULT,
    )
    z_offset = _clamp_float(raw.get("z_offset") or raw.get("dev_ai_z_offset"), -5000.0, 5000.0, 0.0)
    aggro = str(raw.get("aggro") or raw.get("aggro_mode") or raw.get("mode") or "").strip().lower()
    spawn_points = _clamp_int(
        raw.get("spawn_points") or raw.get("nodes"),
        _SPAWN_POINTS_MIN,
        _SPAWN_POINTS_MAX,
        _SPAWN_POINTS_DEFAULT,
    )
    burst = _clamp_int(
        raw.get("burst") or raw.get("per_burst"), _BURST_MIN, _BURST_MAX, _BURST_DEFAULT
    )
    stagger = _clamp_float(
        raw.get("stagger") or raw.get("step_interval"),
        _SPAWN_STEP_MIN_S,
        _SPAWN_STEP_MAX_S,
        _SPAWN_STEP_INTERVAL_S,
    )

    entries: list[dict[str, Any]] = []
    raw_entries = raw.get("entries")
    if isinstance(raw_entries, list) and raw_entries:
        for item in raw_entries:
            entry = _normalize_entry(item)
            if entry is None:
                continue
            # Merge duplicate actor ids in the same wave.
            matched = next((e for e in entries if e["actor_id"] == entry["actor_id"]), None)
            if matched is not None:
                matched["count"] = _clamp_int(
                    int(matched["count"]) + int(entry["count"]), 1, _MAX_COUNT, 1
                )
            else:
                entries.append(entry)
    else:
        legacy = _normalize_entry(raw)
        if legacy is not None:
            entries.append(legacy)

    if not entries:
        return None
    entries = entries[:_MAX_WAVE_TYPES]
    remaining = _MAX_WAVE_TOTAL
    bounded_entries: list[dict[str, Any]] = []
    for entry in entries:
        if remaining <= 0:
            break
        count = min(int(entry["count"]), remaining)
        bounded_entries.append({"actor_id": entry["actor_id"], "count": count})
        remaining -= count
    entries = bounded_entries

    total_count = sum(int(e["count"]) for e in entries)
    # Keep actor_id/count mirrors for older status UIs / logs.
    return {
        "entries": entries,
        "actor_id": str(entries[0]["actor_id"]),
        "count": int(total_count),
        "spacing": spacing,
        "scale": scale,
        "distance": distance,
        "z_offset": z_offset,
        "aggro": aggro,
        "spawn_points": spawn_points,
        "burst": burst,
        "stagger": stagger,
        # Old plans stored cleanup_loot=True; the between-wave loot pass is now
        # opt-in, so a missing key means off.
        "cleanup_loot": bool(raw.get("cleanup_loot", False)),
    }


def limits() -> dict[str, Any]:
    """Advertise the current bounds so the desktop UI can stay in sync."""
    return {
        "max_waves": _MAX_WAVES,
        "max_wave_total": _MAX_WAVE_TOTAL,
        "max_wave_types": _MAX_WAVE_TYPES,
        "max_count_per_entry": _MAX_COUNT,
        "spawn_points": [_SPAWN_POINTS_MIN, _SPAWN_POINTS_MAX, _SPAWN_POINTS_DEFAULT],
        "burst": [_BURST_MIN, _BURST_MAX, _BURST_DEFAULT],
        "stagger": [_SPAWN_STEP_MIN_S, _SPAWN_STEP_MAX_S, _SPAWN_STEP_INTERVAL_S],
        "distance": [_NODE_DISTANCE_MIN, _NODE_DISTANCE_MAX, _WAVE_DISTANCE_DEFAULT],
        "harvest_points": [_HARVEST_MIN, _HARVEST_MAX],
        "abandoned_post_station": _ARENA_ABANDONED_POST,
    }


def _normalize_arena_station(raw: object) -> str:
    text = str(raw or "").strip()
    if not text or text.lower() in ("here", "current", "current_cell", "harvest"):
        return _ARENA_HERE
    key = text.lower().replace(" ", "")
    if key in (
        "abandonedpost",
        "abandoned_post",
        "beachtower",
        "ft_gra_beachtower",
        "world_p.ft_gra_beachtower",
    ):
        return _ARENA_ABANDONED_POST
    return text


def _normalize_point(raw: object) -> dict[str, float] | None:
    if not isinstance(raw, dict):
        if isinstance(raw, (list, tuple)) and len(raw) >= 3:
            raw = {"x": raw[0], "y": raw[1], "z": raw[2]}
        else:
            return None
    try:
        x = float(raw.get("x", raw.get("X")))
        y = float(raw.get("y", raw.get("Y")))
        z = float(raw.get("z", raw.get("Z")))
    except Exception:
        return None
    if any(n != n for n in (x, y, z)):
        return None
    return {"x": x, "y": y, "z": z}


def _normalize_harvested_points(raw: object) -> list[dict[str, float]]:
    if not isinstance(raw, list):
        return []
    points: list[dict[str, float]] = []
    seen: set[tuple[int, int, int]] = set()
    for item in raw:
        point = _normalize_point(item)
        if point is None:
            continue
        key = (int(point["x"] / _HARVEST_DEDUP_UU), int(point["y"] / _HARVEST_DEDUP_UU), int(point["z"] / 200.0))
        if key in seen:
            continue
        seen.add(key)
        points.append(point)
        if len(points) >= _HARVEST_MAX:
            break
    return points


def _point_distance_sq(a: dict[str, float], b: dict[str, float]) -> float:
    return (a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2 + (a["z"] - b["z"]) ** 2


def _actor_xyz(actor: Any) -> dict[str, float] | None:
    if actor is None:
        return None
    for name in ("K2_GetActorLocation", "GetActorLocation"):
        fn = getattr(actor, name, None)
        if not callable(fn):
            continue
        try:
            loc = fn()
        except Exception:
            continue
        try:
            return {"x": float(loc.X), "y": float(loc.Y), "z": float(loc.Z)}
        except Exception:
            continue
    return None


def _spawner_label(obj: Any) -> str:
    try:
        return str(obj)
    except Exception:
        return str(getattr(obj, "Name", "") or "")


def _is_harvest_skip(obj: Any) -> bool:
    blob = f"{_spawner_label(obj)} {getattr(obj, 'Name', '')}".lower()
    if "default__" in blob or "/script/" in blob:
        return True
    return any(token in blob for token in _HARVEST_SKIP_TOKENS)


def _iter_oak_spawners() -> list[Any]:
    try:
        import unrealsdk

        objects = unrealsdk.find_all("OakSpawner", False) or []
    except TypeError:
        try:
            import unrealsdk

            objects = unrealsdk.find_all("OakSpawner") or []
        except Exception:
            return []
    except Exception:
        return []
    return [obj for obj in objects if obj is not None]


def collect_harvest_candidates(spawners: list[Any] | None = None) -> list[dict[str, Any]]:
    """Read-only OakSpawner XYZ. Never Reset/enable map spawners."""
    found: list[dict[str, Any]] = []
    seen: set[tuple[int, int, int]] = set()
    for spawner in list(spawners if spawners is not None else _iter_oak_spawners()):
        if _is_harvest_skip(spawner):
            continue
        point = _actor_xyz(spawner)
        if point is None:
            continue
        key = (
            int(point["x"] / _HARVEST_DEDUP_UU),
            int(point["y"] / _HARVEST_DEDUP_UU),
            int(point["z"] / 200.0),
        )
        if key in seen:
            continue
        seen.add(key)
        found.append({**point, "name": _spawner_label(spawner)[:120]})
    return found


def pick_harvest_points(
    candidates: list[dict[str, Any]],
    *,
    origin: dict[str, float] | None = None,
    min_count: int = _HARVEST_MIN,
    max_count: int = _HARVEST_MAX,
) -> list[dict[str, float]]:
    """Keep 4–8 discrete pads. Prefer spread around the player, never lerp."""
    del min_count
    if not candidates:
        return []
    rows = list(candidates)
    if origin is not None:
        rows.sort(key=lambda row: _point_distance_sq(row, origin))
    picked: list[dict[str, float]] = []
    for row in rows:
        if any(_point_distance_sq(row, existing) < (_HARVEST_DEDUP_UU ** 2) for existing in picked):
            continue
        picked.append({"x": float(row["x"]), "y": float(row["y"]), "z": float(row["z"])})
        if len(picked) >= max_count:
            break
    return picked


def harvest(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Freeze 4–8 live OakSpawner transforms in the loaded cell. Location only."""
    global _harvested_points, _message
    payload = dict(payload or {})
    spawners = payload.get("spawners")
    if spawners is not None and not isinstance(spawners, list):
        spawners = None
    origin = _normalize_point(payload.get("origin"))
    if origin is None:
        origin = _actor_xyz(_local_pawn())
    candidates = collect_harvest_candidates(spawners)
    points = pick_harvest_points(candidates, origin=origin)
    if not points:
        return {
            "ok": False,
            "message": (
                "No harvestable OakSpawner pads in this loaded cell. "
                "Stand in a combat area (or travel to Abandoned Post) and harvest again."
            ),
            **status_fields(),
        }
    _harvested_points = points
    _message = (
        f"Harvested {len(points)} OakSpawner pad(s) in the loaded cell "
        f"(read location only; map spawners were not reset)."
    )
    _log(_message)
    return {
        "ok": True,
        "message": _message,
        "harvested_count": len(points),
        "harvested_points": list(_harvested_points),
        **status_fields(),
    }


def _local_pawn() -> Any | None:
    try:
        from mods_base import get_pc

        pc = get_pc()
    except Exception:
        return None
    if pc is None:
        return None
    for attr in ("OakCharacter", "Pawn", "AcknowledgedPawn"):
        try:
            pawn = getattr(pc, attr, None)
        except Exception:
            pawn = None
        if pawn is not None:
            return pawn
    return None


def _request_arena_travel(station: str) -> str:
    try:
        from .travel import travel_to_station

        return str(travel_to_station(station) or "")
    except Exception as exc:
        return f"Travel to {station} failed: {exc!r}"


def set_plan(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Store the ordered wave list from Electron (or a prior session restore)."""
    global _plan, _running, _complete, _wave_index, _message, _arena_station, _harvested_points
    payload = dict(payload or {})
    waves_raw = payload.get("waves") if "waves" in payload else payload.get("plan")
    if waves_raw is None and isinstance(payload.get("wave"), dict):
        waves_raw = [payload.get("wave")]
    if not isinstance(waves_raw, list):
        return {"ok": False, "message": "hoard_set_plan needs a waves list."}
    if len(waves_raw) > _MAX_WAVES:
        return {"ok": False, "message": f"Too many waves (max {_MAX_WAVES})."}
    waves: list[dict[str, Any]] = []
    for idx, raw in enumerate(waves_raw):
        wave = _normalize_wave(raw)
        if wave is None:
            return {"ok": False, "message": f"Wave {idx + 1} needs at least one actor."}
        waves.append(wave)
    _plan = waves
    if "arena_station" in payload or "arena" in payload:
        _arena_station = _normalize_arena_station(payload.get("arena_station") or payload.get("arena"))
    frozen = payload.get("harvested_points")
    if frozen is None:
        frozen = payload.get("arena_points")
    if frozen is not None:
        _harvested_points = _normalize_harvested_points(frozen)
    if _running:
        # Plan replace mid-run is allowed for UI edits, but does not restart.
        _message = f"Plan updated ({len(_plan)} wave(s)); run continues at wave {_wave_index + 1}."
    else:
        _complete = False
        _wave_index = 0
        _message = f"Plan ready: {len(_plan)} wave(s)." if _plan else "Idle"
        if _harvested_points:
            _message = f"{_message} {len(_harvested_points)} harvested pad(s)."
    return {
        "ok": True,
        "message": _message,
        "wave_total": len(_plan),
        "waves": list(_plan),
        "limits": limits(),
        **status_fields(),
    }


def _asd() -> Any | None:
    try:
        return importlib.import_module("ActorScriptDeployer")
    except Exception:
        return None


def _actor_key(item: Any) -> str:
    key = str(getattr(item, "actor_key", "") or "").strip()
    if key:
        return key
    actor = getattr(item, "actor", None)
    if actor is None:
        return ""
    for attr in ("_actor_key", "_safe_actor_key"):
        # Prefer ASD helpers when available (called via snapshot helpers below).
        pass
    try:
        return str(getattr(actor, "Name", "") or "")
    except Exception:
        return ""


def _snapshot_spawned_keys() -> set[str]:
    asd = _asd()
    if asd is None:
        return set()
    keys: set[str] = set()
    spawned = getattr(asd, "_SPAWNED", None)
    if not isinstance(spawned, list):
        return keys
    safe_key = getattr(asd, "_safe_actor_key", None)
    for item in list(spawned):
        key = str(getattr(item, "actor_key", "") or "").strip()
        if not key and callable(safe_key):
            try:
                key = str(safe_key(getattr(item, "actor", None)) or "").strip()
            except Exception:
                key = ""
        if key:
            keys.add(key)
    return keys


def _snapshot_created_spawner_ids() -> set[int]:
    asd = _asd()
    if asd is None:
        return set()
    created = getattr(asd, "_CREATED_SPAWNERS", None)
    if not isinstance(created, (list, set, tuple)):
        return set()
    return {id(s) for s in list(created) if s is not None}


def _refresh_wave_tracking() -> None:
    """Pick up DeployedActor rows / throwaway spawners that appeared after spawnai."""
    global _wave_items, _wave_spawners
    asd = _asd()
    if asd is None:
        return
    spawned = getattr(asd, "_SPAWNED", None)
    if not isinstance(spawned, list):
        spawned = []
    known_keys = {_actor_key(item) for item in _wave_items if _actor_key(item)}
    known_ids = {id(item) for item in _wave_items}
    spawner_ids = {id(s) for s in _wave_spawners if s is not None}
    for item in list(spawned):
        key = _actor_key(item)
        if key:
            if key in _pre_spawn_keys:
                continue
            if key in known_keys:
                continue
        elif id(item) in known_ids:
            continue
        else:
            source = getattr(item, "source", None)
            if source is None or id(source) in spawner_ids:
                continue
        _wave_items.append(item)
        if key:
            known_keys.add(key)
        known_ids.add(id(item))
        source = getattr(item, "source", None)
        if source is not None and id(source) not in spawner_ids:
            _wave_spawners.append(source)
            spawner_ids.add(id(source))

    created = getattr(asd, "_CREATED_SPAWNERS", None)
    if isinstance(created, (list, set, tuple)):
        for spawner in list(created):
            if spawner is None:
                continue
            sid = id(spawner)
            if sid in spawner_ids or sid in _pre_spawn_spawner_ids:
                continue
            _wave_spawners.append(spawner)
            spawner_ids.add(sid)


def _mark_wave_armed(*, reason: str = "") -> None:
    """Treat the current wave as having started (clear-when-dead may advance)."""
    global _wave_seen_alive
    if _wave_seen_alive:
        return
    _wave_seen_alive = True
    if reason:
        _log(f"wave {_wave_index + 1} armed ({reason})")

def _count_wrapper_alive() -> int:
    """Fallback when hybrid census is unavailable: live wave-item wrappers only."""
    alive = 0
    seen: set[str] = set()
    for item in list(_wave_items):
        actor = getattr(item, "actor", None)
        try:
            name = str(getattr(actor, "Name", "") or "") if actor is not None else ""
            if not name or name.startswith("Default__"):
                actor = None
            elif bool(getattr(actor, "bActorIsBeingDestroyed", False)):
                actor = None
        except Exception:
            actor = None
        if actor is None:
            continue
        key = _actor_key(item) or str(id(actor))
        if key in seen:
            continue
        seen.add(key)
        alive += 1
    return alive


def count_alive() -> int:
    """Alive count for the current wave from the hybrid live-pawn census.

    Does not peek GetAliveActors on a throwaway OakSpawner. That read on a dying
    or already-empty spawner both missed delayed pawns and raced engine death.
    """
    global _last_alive, _wave_seen_alive
    alive = 0
    try:
        from . import asd_hybrid as hybrid

        census_fn = getattr(hybrid, "count_alive", None)
        if callable(census_fn):
            alive = int(census_fn() or 0)
    except Exception:
        alive = 0

    if alive <= 0:
        alive = _count_wrapper_alive()

    now = time.monotonic()
    if alive > 0:
        _mark_wave_armed(reason=f"{alive} live")
        _last_alive = alive
        return alive

    # During grace, never report 0 so a still-empty queue does not look cleared.
    if now < _spawn_grace_until and _expected_count > 0:
        _last_alive = _expected_count
        return _expected_count

    _last_alive = 0
    return 0


def _disable_wave_spawners(spawners: list[Any] | None = None) -> None:
    """Switch throwaway OakSpawners off. This is the only spawner write we make.

    Flag flips do not walk the spawner's owned-actor list, so this cannot follow a
    reference to something the engine is mid-way through destroying. It still only
    runs from the deferred pass, never in the frame a wave died.
    """
    for spawner in list(_wave_spawners if spawners is None else spawners):
        if spawner is None:
            continue
        try:
            comp = spawner.GetSpawnerComponent()
        except Exception:
            comp = None
        if comp is None:
            continue
        for fn_name, args in (
            ("SetSpawnerEnabled", (False,)),
            ("SetSpawnPointEnabled", (False,)),
            ("SetActive", (False,)),
        ):
            fn = getattr(comp, fn_name, None)
            if not callable(fn):
                continue
            try:
                fn(*args)
            except Exception:
                pass


def _note_death_frame() -> None:
    """Record that a wave just died so nothing touches the world for a while."""
    global _last_death_at
    _last_death_at = time.monotonic()


def _queue_deferred_cleanup(
    *,
    spawners: list[Any] | None = None,
    asd_clear: bool = False,
    loot: bool = False,
    delay: float = _POST_WAVE_DISABLE_DELAY_S,
) -> None:
    global _pending_cleanup_at, _pending_cleanup_asd_clear, _pending_cleanup_loot
    for spawner in list(spawners or []):
        if spawner is None:
            continue
        if any(existing is spawner for existing in _pending_cleanup_spawners):
            continue
        _pending_cleanup_spawners.append(spawner)
    _pending_cleanup_asd_clear = bool(_pending_cleanup_asd_clear or asd_clear)
    _pending_cleanup_loot = bool(_pending_cleanup_loot or loot)
    due = time.monotonic() + max(0.0, float(delay))
    # Always take the later time: another wave dying pushes the pass further away
    # from the death frame instead of pulling it into one.
    if due > _pending_cleanup_at:
        _pending_cleanup_at = due


def _drop_deferred_cleanup() -> None:
    global _pending_cleanup_at, _pending_cleanup_asd_clear, _pending_cleanup_loot
    global _pending_cleanup_spawners
    _pending_cleanup_spawners = []
    _pending_cleanup_at = 0.0
    _pending_cleanup_asd_clear = False
    _pending_cleanup_loot = False


def cleanup_pending() -> bool:
    return bool(_pending_cleanup_at > 0.0)


def _process_deferred_cleanup() -> None:
    """Switch finished spawners off, well clear of any death or spawn frame."""
    global _pending_cleanup_at, _pending_cleanup_spawners, _pending_cleanup_asd_clear
    global _pending_cleanup_loot, _cleanup_in_flight
    if _cleanup_in_flight or _pending_cleanup_at <= 0.0:
        return
    now = time.monotonic()
    if now < _pending_cleanup_at:
        return
    if _spawn_in_flight or _spawn_phase:
        _pending_cleanup_at = now + _CLEANUP_RETRY_DELAY_S
        return
    if now - _last_death_at < _DEATH_QUIET_S:
        _pending_cleanup_at = now + _CLEANUP_RETRY_DELAY_S
        return

    spawners = list(_pending_cleanup_spawners)
    want_clear = bool(_pending_cleanup_asd_clear)
    want_loot = bool(_pending_cleanup_loot)
    _drop_deferred_cleanup()

    _cleanup_in_flight = True
    try:
        # Disable only. Destroying the spawner also destroys every actor its
        # component still lists, which is the crash we have now hit three times.
        _disable_wave_spawners(spawners)
        if want_clear:
            try:
                from .backend_actions import run_dev_spawner_action

                result = run_dev_spawner_action("dev_spawner_clear", {})
                _log(f"deferred ASD clear: {result.get('message') or 'sent'}")
            except Exception as exc:
                _log(f"deferred ASD clear failed: {exc!r}")
        if want_loot:
            message = _hide_ground_loot_now()
            if message:
                _log(message)
    finally:
        _cleanup_in_flight = False


def _clear_wave_tracking() -> None:
    global _wave_items, _wave_spawners, _expected_count, _pre_spawn_keys, _pre_spawn_spawner_ids
    global _wave_seen_alive, _spawn_phase, _spawn_next_at, _pending_spawn_jobs
    global _spawn_failures, _active_wave, _spawn_nodes, _spawn_requested, _world_wait_since
    _wave_items = []
    _wave_spawners = []
    _expected_count = 0
    _pre_spawn_keys = set()
    _pre_spawn_spawner_ids = set()
    _wave_seen_alive = False
    _spawn_phase = False
    _spawn_next_at = 0.0
    _pending_spawn_jobs.clear()
    _spawn_failures = []
    _active_wave = {}
    _spawn_nodes = []
    _spawn_requested = 0
    _world_wait_since = 0.0
    # Harvested pads stay frozen across waves; only travel / harvest() replaces them.


def status_fields() -> dict[str, Any]:
    total = len(_plan)
    alive = count_alive() if (_running or _wave_items) else 0
    return {
        "running": bool(_running),
        "complete": bool(_complete),
        "wave_index": int(_wave_index),
        "wave_total": int(total),
        "alive": int(alive),
        "spawning": bool(_spawn_phase),
        "pending_spawns": len(_pending_spawn_jobs),
        "spawn_points": len(_spawn_nodes),
        "spawned_requested": int(_spawn_requested),
        "expected_count": int(_expected_count),
        "cleanup_pending": cleanup_pending(),
        "arena_station": str(_arena_station or _ARENA_HERE),
        "harvested_count": len(_harvested_points),
        "harvested_points": list(_harvested_points),
        "harvest_pending": bool(_harvest_pending),
        "message": str(_message or "Idle"),
        "plan": list(_plan),
    }


def status() -> dict[str, Any]:
    fields = status_fields()
    return {"ok": True, **fields}


def _status_message_for_run() -> str:
    total = len(_plan)
    if not _running:
        if _complete:
            return "Complete"
        return _message or "Idle"
    alive = count_alive()
    return f"Wave {_wave_index + 1}/{total} — {alive} alive — next on clear"


def _apply_wave_aggro(wave: dict[str, Any]) -> None:
    from .spawn_helpers import (
        apply_aggro_to_tracked,
        get_aggro_mode,
        note_spawned_actors,
        set_aggro_mode,
    )

    mode = str(wave.get("aggro") or "").strip().lower()
    if mode:
        set_aggro_mode(mode)
    note_spawned_actors(None)
    if get_aggro_mode() not in ("passive", "none", "off"):
        apply_aggro_to_tracked()


def _nodes_from_harvested(points: list[dict[str, float]] | None = None) -> list[dict[str, Any]]:
    rows = list(points if points is not None else _harvested_points)
    nodes: list[dict[str, Any]] = []
    for index, point in enumerate(rows):
        xyz = (float(point["x"]), float(point["y"]), float(point["z"]))
        nodes.append(
            {
                "index": index,
                "angle": 0.0,
                "distance": 0.0,
                "x": xyz[0],
                "y": xyz[1],
                "z": xyz[2],
                "world_xyz": xyz,
            }
        )
    return nodes


def build_spawn_nodes(wave: dict[str, Any]) -> list[dict[str, Any]]:
    """Harvested OakSpawner pads when frozen; otherwise a jittered player ring.

    Harvested points are discrete world XYZ — never interpolated. The player-ring
    path is only a fallback when no pads were harvested.
    """
    if _harvested_points:
        return _nodes_from_harvested()
    points = _clamp_int(
        wave.get("spawn_points"), _SPAWN_POINTS_MIN, _SPAWN_POINTS_MAX, _SPAWN_POINTS_DEFAULT
    )
    base_distance = _clamp_float(
        wave.get("distance"), _NODE_DISTANCE_MIN, _NODE_DISTANCE_MAX, _WAVE_DISTANCE_DEFAULT
    )
    sector = 360.0 / float(points)
    # Wobble around each sector's midpoint so nodes stay in their own sector and
    # never collapse onto a neighbour.
    wobble = sector * 0.5 * _NODE_ANGLE_JITTER
    nodes: list[dict[str, Any]] = []
    for index in range(points):
        angle = (index * sector + sector * 0.5 + _rng.uniform(-wobble, wobble)) % 360.0
        factor = 1.0 + _rng.uniform(-_NODE_DISTANCE_JITTER, _NODE_DISTANCE_JITTER)
        distance = max(_NODE_DISTANCE_MIN, min(_NODE_DISTANCE_MAX, base_distance * factor))
        nodes.append(
            {
                "index": index,
                "angle": round(angle, 2),
                "distance": round(distance, 1),
            }
        )
    return nodes


def _burst_sizes(total: int, burst: int) -> list[int]:
    """Split one actor type into 1-or-2-at-a-time groups (alternating)."""
    total = max(0, int(total))
    burst = max(_BURST_MIN, int(burst))
    sizes: list[int] = []
    turn = 0
    while total > 0:
        wanted = burst if (burst <= 1 or turn % 2 == 0) else max(1, burst - 1)
        take = min(wanted, total)
        sizes.append(take)
        total -= take
        turn += 1
    return sizes


def build_spawn_jobs(
    wave: dict[str, Any], entries: list[dict[str, Any]], nodes: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Round-robin small bursts across enemy types and spawn nodes.

    Each job is one ASD call for one node, so enemies trickle in from several
    directions instead of arriving as a single ring-shaped burst.
    """
    burst = _clamp_int(wave.get("burst"), _BURST_MIN, _BURST_MAX, _BURST_DEFAULT)
    pending: list[tuple[str, list[int]]] = []
    for entry in entries:
        actor_id = str(entry.get("actor_id") or "").strip()
        if not actor_id:
            continue
        sizes = _burst_sizes(int(entry.get("count") or 1), burst)
        if sizes:
            pending.append((actor_id, sizes))
    if not pending or not nodes:
        return []

    spacing = _clamp_float(wave.get("spacing"), 1.0, 5000.0, 125.0)
    scale = _clamp_float(wave.get("scale"), 0.05, 20.0, 1.0)
    z_offset = _clamp_float(wave.get("z_offset"), -5000.0, 5000.0, 0.0)

    jobs: list[dict[str, Any]] = []
    node_turn = 0
    while any(sizes for _actor, sizes in pending):
        for actor_id, sizes in pending:
            if not sizes:
                continue
            count = sizes.pop(0)
            node = nodes[node_turn % len(nodes)]
            job: dict[str, Any] = {
                "actor_id": actor_id,
                "count": int(count),
                "node": int(node["index"]),
                "angle": float(node.get("angle") or 0.0),
                "distance": float(node.get("distance") or 0.0),
                "spacing": spacing,
                "scale": scale,
                "z_offset": z_offset,
            }
            world_xyz = node.get("world_xyz")
            if world_xyz:
                job["world_xyz"] = tuple(float(v) for v in world_xyz)
            jobs.append(job)
            node_turn += 1
    return jobs


def _spawn_world_ready() -> tuple[bool, str]:
    """Cheap pawn/world/controller probe so we never spawn during a load."""
    try:
        from mods_base import get_pc
    except Exception:
        # Not running inside the game (unit tests / tooling): nothing to gate on.
        return True, ""
    try:
        pc = get_pc()
    except Exception as exc:
        return False, f"player controller unavailable ({exc!r})"
    if pc is None:
        return False, "no player controller yet"
    try:
        pawn = getattr(pc, "Pawn", None)
    except Exception as exc:
        return False, f"pawn unavailable ({exc!r})"
    if pawn is None:
        return False, "no pawn (loading, travelling, or respawning)"
    try:
        if bool(getattr(pawn, "bActorIsBeingDestroyed", False)):
            return False, "pawn is being destroyed"
        # Touching the transform proves the pawn and its world are usable.
        pawn.K2_GetActorLocation()
    except Exception as exc:
        return False, f"pawn not placed in a world yet ({exc!r})"
    return True, ""


def _spawn_current_wave() -> dict[str, Any]:
    """Stage the current wave into per-node bursts for paced spawning."""
    global _message, _spawn_grace_until, _expected_count, _pre_spawn_keys
    global _pre_spawn_spawner_ids, _spawn_phase, _spawn_next_at, _active_wave, _spawn_nodes

    if _wave_index < 0 or _wave_index >= len(_plan):
        return {"ok": False, "message": "No wave to spawn."}

    wave = _plan[_wave_index]
    entries = list(wave.get("entries") or [])
    if not entries:
        legacy = _normalize_entry(wave)
        entries = [legacy] if legacy else []
    if not entries:
        return {"ok": False, "message": f"Wave {_wave_index + 1} has no actors."}

    _clear_wave_tracking()
    _active_wave = dict(wave)
    _pre_spawn_keys = _snapshot_spawned_keys()
    _pre_spawn_spawner_ids = _snapshot_created_spawner_ids()
    _expected_count = sum(int(e.get("count") or 1) for e in entries)
    _spawn_grace_until = 0.0
    if _harvest_pending and not _harvested_points:
        _spawn_nodes = []
        _spawn_phase = True
        _spawn_next_at = max(time.monotonic(), _last_death_at + _DEATH_QUIET_S)
        _message = (
            f"Wave {_wave_index + 1}/{len(_plan)} — waiting for the loaded cell, "
            "then harvesting OakSpawner pads"
        )
        out = {"ok": True, "message": _message}
        out.update(status_fields())
        _log(_message)
        return out
    _spawn_nodes = build_spawn_nodes(wave)
    for job in build_spawn_jobs(wave, entries, _spawn_nodes):
        _pending_spawn_jobs.append(job)

    _spawn_phase = bool(_pending_spawn_jobs)
    # A wave advance happens in the frame the previous wave died. Hold the first
    # burst until the engine is done with those corpses.
    _spawn_next_at = max(time.monotonic(), _last_death_at + _DEATH_QUIET_S)
    stagger = _clamp_float(
        wave.get("stagger"), _SPAWN_STEP_MIN_S, _SPAWN_STEP_MAX_S, _SPAWN_STEP_INTERVAL_S
    )
    source = "harvested pads" if _harvested_points else "player-ring fallback"
    _message = (
        f"Wave {_wave_index + 1}/{len(_plan)} — {_expected_count} enemies "
        f"({len(entries)} type(s)) emerging from {len(_spawn_nodes)} {source}, "
        f"{len(_pending_spawn_jobs)} burst(s) every {stagger:.2f}s"
    )
    out = {"ok": _spawn_phase, "message": _message}
    out.update(status_fields())
    _log(_message)
    return out


def _wave_stagger() -> float:
    return _clamp_float(
        _active_wave.get("stagger"),
        _SPAWN_STEP_MIN_S,
        _SPAWN_STEP_MAX_S,
        _SPAWN_STEP_INTERVAL_S,
    )


def _spawn_next_job() -> None:
    """Run at most one ASD spawn burst per scheduled step, never two at once."""
    global _spawn_phase, _spawn_next_at, _spawn_grace_until, _message, _running
    global _spawn_in_flight, _world_wait_since, _spawn_requested
    global _harvest_pending, _spawn_nodes
    if _spawn_in_flight:
        return
    if not _spawn_phase:
        return
    if not _pending_spawn_jobs and not (_harvest_pending and not _harvested_points):
        return

    stagger = _wave_stagger()
    now = time.monotonic()
    ready, reason = _spawn_world_ready()
    if not ready:
        if _world_wait_since <= 0.0:
            _world_wait_since = now
            _log(f"holding wave {_wave_index + 1} spawns: {reason}")
        _spawn_next_at = now + max(0.5, stagger)
        if now - _world_wait_since > _MAX_WORLD_WAIT_S:
            _running = False
            _spawn_phase = False
            _message = f"Wave {_wave_index + 1} spawns cancelled: {reason}"
            _log(_message)
        return
    _world_wait_since = 0.0

    if _harvest_pending and not _harvested_points:
        harvested = harvest()
        if not harvested.get("ok") or not _harvested_points:
            _running = False
            _spawn_phase = False
            _message = str(harvested.get("message") or "Harvest failed; hoard stopped.")
            _log(_message)
            return
        _harvest_pending = False
        wave = _active_wave or (_plan[_wave_index] if _plan else {})
        entries = list(wave.get("entries") or [])
        _spawn_nodes = _nodes_from_harvested()
        _pending_spawn_jobs.clear()
        for staged in build_spawn_jobs(wave, entries, _spawn_nodes):
            _pending_spawn_jobs.append(staged)
        if not _pending_spawn_jobs:
            _running = False
            _spawn_phase = False
            _message = "Harvested pads, but the current wave has no spawn jobs."
            return
        _message = (
            f"Wave {_wave_index + 1}/{len(_plan)} — harvested {len(_spawn_nodes)} pads, "
            f"spawning {_expected_count} enemies"
        )
        _log(_message)

    if not _pending_spawn_jobs:
        _spawn_phase = False
        return

    job = _pending_spawn_jobs[0]
    # Advance the clock before the call so a reentrant tick cannot double-fire.
    _spawn_next_at = now + stagger
    from .backend_actions import (
        _asd_note_spawn_for_autoclear,
        _run_actor_script_deployer_spawnai_like_debug_menu,
    )

    _spawn_in_flight = True
    try:
        result = _run_actor_script_deployer_spawnai_like_debug_menu(
            name=str(job["actor_id"]),
            count=int(job.get("count") or 1),
            distance=float(job.get("distance") or 0.0),
            spacing=float(job["spacing"]),
            scale=float(job["scale"]),
            z_offset=float(job["z_offset"]),
            extra_loads=[],
            direct_only=False,
            world_xyz=job.get("world_xyz"),
        )
    except Exception as exc:
        result = {"ok": False, "message": f"spawn raised {exc!r}"}
    finally:
        _spawn_in_flight = False
        if _pending_spawn_jobs and _pending_spawn_jobs[0] is job:
            _pending_spawn_jobs.popleft()

    try:
        _asd_note_spawn_for_autoclear()
    except Exception:
        pass
    _refresh_wave_tracking()
    if not result.get("ok"):
        if len(_spawn_failures) < 20:
            _spawn_failures.append(
                f"{job['actor_id']}: {result.get('message') or 'spawn failed'}"
            )
    else:
        _spawn_requested += int(job.get("count") or 1)
        # Only a verified spawn arms clear-when-dead. ASD reports "accepted but
        # unverified" for outright failures too, and arming on that made the
        # runner blow through every wave in seconds.
        if result.get("spawn_verified") or result.get("verification_status") == "verified_spawned":
            _mark_wave_armed(reason="ASD verified a spawned actor")

    if _pending_spawn_jobs:
        _message = (
            f"Wave {_wave_index + 1}/{len(_plan)} — {_spawn_requested}/{_expected_count} "
            f"emerging from {len(_spawn_nodes)} spawn point(s)"
        )
        return

    _spawn_phase = False
    _spawn_grace_until = time.monotonic() + _SPAWN_GRACE_S
    try:
        _apply_wave_aggro(_active_wave or {})
    except Exception as exc:
        _log(f"aggro apply failed: {exc!r}")
    if _spawn_failures and _spawn_requested <= 0:
        _running = False
        _message = f"Wave {_wave_index + 1} spawn failed: {'; '.join(_spawn_failures)}"
        _log(_message)
        return
    _message = (
        f"Wave {_wave_index + 1}/{len(_plan)} — {_spawn_requested}/{_expected_count} "
        f"spawn request(s) sent from {len(_spawn_nodes)} point(s) — next on clear"
    )
    if _spawn_failures:
        _message = f"{_message} ({len(_spawn_failures)} burst(s) failed)"
    _log(_message)


def start() -> dict[str, Any]:
    global _running, _complete, _wave_index, _message, _harvest_pending, _harvested_points
    if not _plan:
        return {"ok": False, "message": "No hoard plan set. Build waves in Hoard Builder first.", **status_fields()}
    if _running:
        return {"ok": False, "message": "Hoard already running.", **status_fields()}
    _complete = False
    _wave_index = 0
    _harvest_pending = False
    station = str(_arena_station or "").strip()
    if station and station != _ARENA_HERE:
        _harvested_points = []
        travel_msg = _request_arena_travel(station)
        _harvest_pending = True
        _message = f"Traveling to {station}; will harvest pads after the cell loads. {travel_msg}"
        _log(_message)
    elif station == _ARENA_HERE and not _harvested_points:
        # Current cell: harvest now if the world is up; otherwise wait on the first tick.
        ready, _reason = _spawn_world_ready()
        if ready:
            harvested = harvest()
            if not harvested.get("ok"):
                return harvested
        else:
            _harvest_pending = True
    _running = True
    _message = f"Starting wave 1/{len(_plan)}…"
    result = _spawn_current_wave()
    if not result.get("ok"):
        _running = False
        return result
    return {"ok": True, "message": _message, **status_fields()}


def stop() -> dict[str, Any]:
    """Stop auto-advance, leave actors alive, and release cached wrappers."""
    global _running, _message, _harvest_pending
    was = _running
    _running = False
    _harvest_pending = False
    alive = count_alive() if _wave_items else 0
    if _complete:
        _message = "Complete"
    elif was:
        _message = f"Stopped at wave {_wave_index + 1}/{len(_plan)} ({alive} alive)."
    else:
        _message = _message or "Idle"
    _clear_wave_tracking()
    return {"ok": True, "message": _message, **status_fields()}


def clear_travel_state() -> None:
    """Stop the runner and release all world-bound actor/spawner wrappers."""
    global _running, _message, _harvest_pending, _harvested_points
    _running = False
    _harvest_pending = False
    _harvested_points = []
    _clear_wave_tracking()
    # Spawners from the old world must never be touched after travel.
    _drop_deferred_cleanup()
    _message = "Stopped for world travel."


def _hide_ground_loot_now() -> str:
    try:
        from .movement_adjustments import hide_ground_loot

        return str(hide_ground_loot() or "")
    except Exception as exc:
        _log(f"loot cleanup failed: {exc!r}")
        return ""


def _should_cleanup_ground_loot(wave: dict[str, Any]) -> bool:
    """Opt-in ground-loot hide, rate limited.

    hide_ground_loot() walks every InventoryPickup and parks it off-map. Running
    that at every wave transition is what took the game down. Keep it off by
    default, never back-to-back, and only ever from the deferred pass so it
    cannot land in a death frame.
    """
    global _loot_cleanup_last_at
    if not bool(wave.get("cleanup_loot", False)):
        return False
    now = time.monotonic()
    if _loot_cleanup_last_at and now - _loot_cleanup_last_at < _LOOT_CLEANUP_MIN_INTERVAL_S:
        return False
    _loot_cleanup_last_at = now
    return True


def clear(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Emergency stop: stop the runner, then switch spawners off and clear ASD actors.

    Everything that touches the world is queued rather than run inline: this button
    is usually pressed right after a kill-all, and touching actors while the engine
    is still processing their deaths is what crashed the game. ASD_clear is the one
    destructive call left in the feature, and it only runs because the user asked
    for it. The physics loot hide never fires from here — it is a separate button.
    """
    global _running, _complete, _message, _wave_index, _harvest_pending
    wanted_loot = bool((payload or {}).get("cleanup_loot", False))
    _harvest_pending = False
    force_loot = bool((payload or {}).get("force_loot_physics", False))
    _running = False
    spawners = list(_wave_spawners)
    _note_death_frame()
    _clear_wave_tracking()
    _queue_deferred_cleanup(
        spawners=spawners,
        asd_clear=True,
        loot=force_loot,
        delay=_CLEAR_BUTTON_CLEANUP_DELAY_S,
    )
    _complete = False
    _wave_index = 0
    note = ""
    if wanted_loot and not force_loot:
        note = (
            " Ground loot left in place — the physics hide is unsafe mid-fight; "
            "use Clear Loot once the fight is over."
        )
    _message = (
        "Emergency clear: spawners switch off and ASD clear runs in "
        f"{_CLEAR_BUTTON_CLEANUP_DELAY_S:.2f}s.{note}"
    )
    return {"ok": True, "message": _message, **status_fields()}


def tick() -> None:
    """Bridge tick: if running and wave is clear, advance or complete.

    The bridge tick hook fires once per GbxUIUMGTickWidget, so a single frame can
    call this many times, and ASD spawns can pump the engine mid-call and re-enter
    it. The interval gate plus the reentrancy flag mean at most one hoard operation
    happens per interval no matter how many widgets ticked.
    """
    global _tick_in_flight, _last_tick_at
    if _tick_in_flight:
        return
    now = time.monotonic()
    if now - _last_tick_at < _TICK_MIN_INTERVAL_S:
        return
    _last_tick_at = now
    _tick_in_flight = True
    try:
        _tick_body()
    finally:
        _tick_in_flight = False


def _tick_body() -> None:
    global _running, _complete, _wave_index, _message, _spawn_grace_until

    # Deferred destroys keep running after the hoard stops or completes.
    _process_deferred_cleanup()

    if not _running:
        return
    if not _plan:
        _running = False
        _message = "Idle"
        return

    if _spawn_phase:
        if time.monotonic() >= _spawn_next_at:
            _spawn_next_job()
        return

    # Keep pulling async DeployedActor rows during / just after grace.
    if time.monotonic() < _spawn_grace_until + _SPAWN_ARM_EXTRA_S or not _wave_items:
        _refresh_wave_tracking()

    if time.monotonic() < _spawn_grace_until:
        _message = _status_message_for_run()
        return

    alive = count_alive()
    _message = _status_message_for_run()
    if alive > 0:
        return

    # Do not treat "never appeared" as clear-when-dead until arm window ends.
    if not _wave_seen_alive:
        if time.monotonic() < _spawn_grace_until + _SPAWN_ARM_EXTRA_S:
            _message = f"Wave {_wave_index + 1}/{len(_plan)} — waiting for spawn…"
            return
        _running = False
        detail = f" Last spawn errors: {'; '.join(_spawn_failures[:3])}" if _spawn_failures else ""
        _message = (
            f"Wave {_wave_index + 1} never reported alive actors; hoard stopped. "
            f"Check ASD / actor id, then Start again.{detail}"
        )
        _log(_message)
        return

    # Wave cleared. This frame is almost always a "Kill All" frame, so nothing
    # here may reach into the world: record the death, queue the spawner disable,
    # and let the deferred pass do it once the engine is done with the corpses.
    _note_death_frame()
    finished_wave = dict(_active_wave or _plan[_wave_index])
    finished_spawners = list(_wave_spawners)
    _queue_deferred_cleanup(
        spawners=finished_spawners,
        loot=_should_cleanup_ground_loot(finished_wave),
    )
    _clear_wave_tracking()
    next_index = _wave_index + 1
    if next_index >= len(_plan):
        _running = False
        _complete = True
        _message = "Complete"
        _log("Hoard complete.")
        return

    _wave_index = next_index
    _message = f"Wave {_wave_index + 1}/{len(_plan)} spawning…"
    result = _spawn_current_wave()
    if not result.get("ok"):
        _running = False
        _message = str(result.get("message") or "Wave spawn failed; hoard stopped.")
        _log(_message)
