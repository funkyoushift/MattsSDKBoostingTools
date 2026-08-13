"""Hoard Builder wave runner — sequenced ASD_spawnai waves with clear-when-dead advance.

Host-session state only. Electron persists the plan in localStorage; this module
owns the live run (index, tracked actors, tick). Does not import BLImGui.
"""
from __future__ import annotations

import importlib
import time
from typing import Any

from unrealsdk import logging

_PREFIX = "[Matts SDK Boosting Tools | Hoard]"

# Grace period after spawnai so async/queued spawns are not treated as "cleared".
_SPAWN_GRACE_S = 3.0
# Extra wait after grace before giving up if we never saw a live actor.
# ASD thin-air often queues and only reports alive a few seconds later.
_SPAWN_ARM_EXTRA_S = 12.0
_MAX_WAVES = 40
_MAX_COUNT = 12

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
    distance = _clamp_float(raw.get("distance") or raw.get("dev_ai_distance"), 0.0, 20000.0, 350.0)
    z_offset = _clamp_float(raw.get("z_offset") or raw.get("dev_ai_z_offset"), -5000.0, 5000.0, 0.0)
    aggro = str(raw.get("aggro") or raw.get("aggro_mode") or raw.get("mode") or "").strip().lower()

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
    if len(entries) > _MAX_COUNT:
        entries = entries[:_MAX_COUNT]

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
    }


def set_plan(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Store the ordered wave list from Electron (or a prior session restore)."""
    global _plan, _running, _complete, _wave_index, _message
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
    if _running:
        # Plan replace mid-run is allowed for UI edits, but does not restart.
        _message = f"Plan updated ({len(_plan)} wave(s)); run continues at wave {_wave_index + 1}."
    else:
        _complete = False
        _wave_index = 0
        _message = f"Plan ready: {len(_plan)} wave(s)." if _plan else "Idle"
    return {
        "ok": True,
        "message": _message,
        "wave_total": len(_plan),
        "waves": list(_plan),
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

def _count_spawner_alive(spawner: Any) -> int:
    if spawner is None:
        return 0
    try:
        comp = spawner.GetSpawnerComponent()
    except Exception:
        return 0
    if comp is None:
        return 0
    asd = _asd()
    alive_fn = getattr(asd, "_alive_actors_for_spawner_component", None) if asd else None
    if callable(alive_fn):
        try:
            actors = alive_fn(comp) or []
            return len(list(actors))
        except Exception:
            pass
    for meth, args in (("GetNumAliveActors", (0,)), ("GetNumAliveActors", ())):
        fn = getattr(comp, meth, None)
        if not callable(fn):
            continue
        try:
            return max(0, int(fn(*args)))
        except Exception:
            continue
    return 0


def count_alive() -> int:
    """Best-effort alive count for the current wave."""
    global _last_alive, _wave_seen_alive
    asd = _asd()
    find_live = getattr(asd, "_find_live_spawned_actor", None) if asd else None
    live_keys: set[str] = set()
    alive = 0

    for item in list(_wave_items):
        actor = None
        if callable(find_live):
            try:
                actor = find_live(item)
            except Exception:
                actor = None
        if actor is None:
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
        if key in live_keys:
            continue
        live_keys.add(key)
        alive += 1

    # Spawner component counts catch async rows not yet mirrored into _SPAWNED.
    for spawner in list(_wave_spawners):
        n = _count_spawner_alive(spawner)
        if n > alive:
            alive = n

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


def _disable_wave_spawners() -> None:
    """Stop throwaway OakSpawners for the finished wave so they cannot respawn."""
    asd = _asd()
    disable_fn = getattr(asd, "_disable_and_destroy_spawner", None) if asd else None
    for spawner in list(_wave_spawners):
        if callable(disable_fn):
            try:
                disable_fn(spawner)
                continue
            except Exception:
                pass
        try:
            comp = spawner.GetSpawnerComponent()
        except Exception:
            comp = None
        if comp is None:
            continue
        for fn_name, args in (("SetSpawnerEnabled", (False,)), ("SetSpawnPointEnabled", (False,))):
            fn = getattr(comp, fn_name, None)
            if callable(fn):
                try:
                    fn(*args)
                except Exception:
                    pass


def _clear_wave_tracking() -> None:
    global _wave_items, _wave_spawners, _expected_count, _pre_spawn_keys, _pre_spawn_spawner_ids, _wave_seen_alive
    _wave_items = []
    _wave_spawners = []
    _expected_count = 0
    _pre_spawn_keys = set()
    _pre_spawn_spawner_ids = set()
    _wave_seen_alive = False


def status_fields() -> dict[str, Any]:
    total = len(_plan)
    alive = count_alive() if (_running or _wave_items) else 0
    return {
        "running": bool(_running),
        "complete": bool(_complete),
        "wave_index": int(_wave_index),
        "wave_total": int(total),
        "alive": int(alive),
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


def _spawn_current_wave() -> dict[str, Any]:
    """Spawn plan[_wave_index] via the same ASD_spawnai path as Dev Spawner.

    Waves may list multiple actor entries; all are spawned for this wave and
    tracked together for clear-when-dead.
    """
    global _message, _spawn_grace_until, _expected_count, _pre_spawn_keys, _pre_spawn_spawner_ids, _wave_items, _wave_spawners

    if _wave_index < 0 or _wave_index >= len(_plan):
        return {"ok": False, "message": "No wave to spawn."}

    wave = _plan[_wave_index]
    entries = list(wave.get("entries") or [])
    if not entries:
        legacy = _normalize_entry(wave)
        entries = [legacy] if legacy else []
    if not entries:
        return {"ok": False, "message": f"Wave {_wave_index + 1} has no actors."}

    from .backend_actions import (
        _asd_note_spawn_for_autoclear,
        _run_actor_script_deployer_spawnai_like_debug_menu,
    )

    _clear_wave_tracking()
    _pre_spawn_keys = _snapshot_spawned_keys()
    _pre_spawn_spawner_ids = _snapshot_created_spawner_ids()
    _expected_count = sum(int(e.get("count") or 1) for e in entries)
    # Extra grace when several spawnai calls queue in one wave.
    grace = _SPAWN_GRACE_S + max(0, len(entries) - 1) * 1.25
    _spawn_grace_until = time.monotonic() + grace

    last_result: dict[str, Any] = {"ok": True, "message": ""}
    failures: list[str] = []
    for entry in entries:
        actor_id = str(entry.get("actor_id") or "").strip()
        count = int(entry.get("count") or 1)
        if not actor_id:
            continue
        result = _run_actor_script_deployer_spawnai_like_debug_menu(
            name=actor_id,
            count=count,
            distance=float(wave.get("distance") or 350.0),
            spacing=float(wave.get("spacing") or 125.0),
            scale=float(wave.get("scale") or 1.0),
            z_offset=float(wave.get("z_offset") or 0.0),
            extra_loads=[],
            direct_only=False,
        )
        last_result = dict(result)
        try:
            _asd_note_spawn_for_autoclear()
        except Exception:
            pass
        _refresh_wave_tracking()
        if not result.get("ok"):
            failures.append(f"{actor_id}: {result.get('message') or 'spawn failed'}")

    try:
        _apply_wave_aggro(wave)
    except Exception as exc:
        _log(f"aggro apply failed: {exc!r}")

    ok = not failures
    # ASD often queues with 0 immediate actors; arm clear-when-dead once spawn
    # commands were accepted so a later empty board advances to the next wave.
    if ok and _expected_count > 0:
        _mark_wave_armed(reason="spawn queued")
    detail = "; ".join(failures) if failures else str(last_result.get("message") or "")
    alive = count_alive()
    kinds = len(entries)
    _message = (
        f"Wave {_wave_index + 1}/{len(_plan)} — {alive} alive ({kinds} type(s)) — next on clear"
        if ok
        else f"Wave {_wave_index + 1} spawn failed: {detail}"
    )
    out = dict(last_result)
    out["ok"] = ok
    out["message"] = _message if ok else detail
    out.update(status_fields())
    _log(_message)
    return out


def start() -> dict[str, Any]:
    global _running, _complete, _wave_index, _message
    if not _plan:
        return {"ok": False, "message": "No hoard plan set. Build waves in Hoard Builder first.", **status_fields()}
    if _running:
        return {"ok": False, "message": "Hoard already running.", **status_fields()}
    _complete = False
    _wave_index = 0
    _running = True
    _message = f"Starting wave 1/{len(_plan)}…"
    result = _spawn_current_wave()
    if not result.get("ok"):
        _running = False
        return result
    return {"ok": True, "message": _message, **status_fields()}


def stop() -> dict[str, Any]:
    """Stop auto-advance; leave actors in the world."""
    global _running, _message
    was = _running
    _running = False
    if _complete:
        _message = "Complete"
    elif was:
        _message = f"Stopped at wave {_wave_index + 1}/{len(_plan)} ({count_alive()} alive)."
    else:
        _message = _message or "Idle"
    return {"ok": True, "message": _message, **status_fields()}


def clear() -> dict[str, Any]:
    """ASD clear + stop runner."""
    global _running, _complete, _message, _wave_index
    _running = False
    _disable_wave_spawners()
    _clear_wave_tracking()

    from .backend_actions import run_dev_spawner_action

    clear_result = run_dev_spawner_action("dev_spawner_clear", {})
    _complete = False
    _wave_index = 0
    base = str(clear_result.get("message") or "ASD clear sent.")
    _message = f"Cleared. {base}".strip()
    out = dict(clear_result)
    out["message"] = _message
    out.update(status_fields())
    return out


def tick() -> None:
    """Bridge tick: if running and wave is clear, advance or complete."""
    global _running, _complete, _wave_index, _message, _spawn_grace_until

    if not _running:
        return
    if not _plan:
        _running = False
        _message = "Idle"
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
        _message = (
            f"Wave {_wave_index + 1} never reported alive actors; hoard stopped. "
            "Check ASD / actor id, then Start again."
        )
        _log(_message)
        return

    # Wave cleared — disable spawners so they cannot refill, then advance.
    _disable_wave_spawners()
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
