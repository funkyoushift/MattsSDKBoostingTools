"""Backpack / bank container size helpers for Matt's SDK Boosting Tools."""
from __future__ import annotations

import json
import threading
import time
import atexit
from pathlib import Path
from typing import Any

from mods_base import ENGINE
from unrealsdk import logging

from .party_helpers import _gbc_resolve_player_display_name

_PREFIX = "[Matts SDK Boosting Tools | Inventory]"

_MIN_CONTAINER_SIZE = 1
_MAX_CONTAINER_SIZE = 9999
_DEFAULT_BACKPACK_SIZE = 70
_DEFAULT_BANK_SIZE = 500

# Auto-apply tuning. PlayerState exists before the profile/inventory containers
# are fully settled. Apply a tiny burst after a player spawn/joins, then stop
# until that stable player key disappears and reappears.
_AUTO_DEFER_SECONDS = 0.0
_AUTO_RETRY_SECONDS = 0.75
_AUTO_MAX_APPLIES_PER_SPAWN = 3
_AUTO_POLL_SECONDS = 0.25

_SETTINGS_FILE_NAME = "MattsSDKBoostingTools_settings.json"
_settings_lock = threading.RLock()
_background_started = False
_background_stop = False
_background_thread: threading.Thread | None = None
_background_stop_event = threading.Event()
_last_background_log = 0.0
_auto_apply_lock = threading.RLock()

_DEFAULT_SETTINGS = {
    "auto_inventory_sizes": False,
    "backpack_size": _DEFAULT_BACKPACK_SIZE,
    "bank_size": _DEFAULT_BANK_SIZE,
}


def _candidate_settings_paths() -> list[Path]:
    paths: list[Path] = []
    try:
        cwd = Path.cwd()
        paths.append(cwd / "sdk_mods" / _SETTINGS_FILE_NAME)
        paths.append(cwd / _SETTINGS_FILE_NAME)
    except Exception:
        pass
    try:
        paths.append(Path.home() / "Documents" / "My Games" / "Borderlands 4" / "Saved" / _SETTINGS_FILE_NAME)
    except Exception:
        pass
    # Last resort: next to loose source files. This is read-only inside zipped sdkmods,
    # but useful while developing loose mods.
    try:
        paths.append(Path(__file__).resolve().parent / _SETTINGS_FILE_NAME)
    except Exception:
        pass

    out: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        key = str(path)
        if key not in seen:
            seen.add(key)
            out.append(path)
    return out


def _settings_path_for_read() -> Path:
    for path in _candidate_settings_paths():
        try:
            if path.exists():
                return path
        except Exception:
            pass
    return _candidate_settings_paths()[0]


def _settings_path_for_write() -> Path:
    for path in _candidate_settings_paths():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            test = path.parent / (path.name + ".tmp")
            test.write_text("ok", encoding="utf-8")
            test.unlink(missing_ok=True)
            return path
        except Exception:
            continue
    return _candidate_settings_paths()[0]


def load_inventory_settings() -> dict[str, Any]:
    settings = dict(_DEFAULT_SETTINGS)
    path = _settings_path_for_read()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            settings.update(raw)
    except Exception:
        pass
    settings["auto_inventory_sizes"] = bool(settings.get("auto_inventory_sizes", False))
    settings["backpack_size"] = clamp_container_size(settings.get("backpack_size", _DEFAULT_BACKPACK_SIZE), _DEFAULT_BACKPACK_SIZE)
    settings["bank_size"] = clamp_container_size(settings.get("bank_size", _DEFAULT_BANK_SIZE), _DEFAULT_BANK_SIZE)
    return settings


def save_inventory_settings(*, auto_inventory_sizes: bool | None = None, backpack_size: int | None = None, bank_size: int | None = None) -> dict[str, Any]:
    with _settings_lock:
        settings = load_inventory_settings()
        if auto_inventory_sizes is not None:
            settings["auto_inventory_sizes"] = bool(auto_inventory_sizes)
        if backpack_size is not None:
            settings["backpack_size"] = clamp_container_size(backpack_size, _DEFAULT_BACKPACK_SIZE)
        if bank_size is not None:
            settings["bank_size"] = clamp_container_size(bank_size, _DEFAULT_BANK_SIZE)
        path = _settings_path_for_write()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(settings, indent=2, sort_keys=True), encoding="utf-8")
        except Exception as exc:
            _log(f"Could not save inventory settings: {exc!r}")
        return settings



def save_extra_settings(**extra: Any) -> dict[str, Any]:
    """Persist additional MSBT UI settings alongside inventory settings."""
    with _settings_lock:
        settings = load_inventory_settings()
        settings.update(extra)
        path = _settings_path_for_write()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(settings, indent=2, sort_keys=True), encoding="utf-8")
        except Exception as exc:
            _log(f"Could not save extra settings: {exc!r}")
        return settings

def _log(msg: str) -> None:
    logging.info(f"{_PREFIX} {msg}")


def clamp_container_size(value: int, default: int = 70) -> int:
    try:
        v = int(value)
    except Exception:
        v = int(default)
    return max(_MIN_CONTAINER_SIZE, min(v, _MAX_CONTAINER_SIZE))


def _get_game_state() -> Any | None:
    try:
        world = getattr(ENGINE.GameViewport, "World", None)
    except Exception:
        world = None
    return getattr(world, "GameState", None) if world is not None else None


def get_party_player_states() -> list[tuple[int, str, Any]]:
    gs = _get_game_state()
    pa = getattr(gs, "PlayerArray", None) if gs is not None else None
    if pa is None:
        return []
    try:
        n = len(pa)
    except Exception:
        return []
    out: list[tuple[int, str, Any]] = []
    for i in range(n):
        try:
            ps = pa[i]
        except Exception:
            ps = None
        if ps is not None:
            out.append((i, _gbc_resolve_player_display_name(ps), ps))
    return out


def get_player_state_by_party_index(index: int | None) -> Any | None:
    if index is None:
        return None
    for i, _name, ps in get_party_player_states():
        if i == int(index):
            return ps
    return None


def _set_attr_integer(attr: Any, size: int) -> bool:
    """Set a GbxAttributeInteger-like struct's Value/BaseValue fields."""
    if attr is None:
        return False
    wrote = False
    for field in ("Value", "BaseValue"):
        try:
            setattr(attr, field, int(size))
            wrote = True
        except Exception:
            pass
    for method_name in ("SetValue", "SetBaseValue"):
        method = getattr(attr, method_name, None)
        if callable(method):
            try:
                method(int(size))
                wrote = True
            except Exception:
                pass
    return wrote


def _bump_replication(container: Any) -> None:
    if container is None:
        return
    for rep_field in ("ArrayReplicationKey", "ReplicationKey", "LastReplicationKey"):
        try:
            cur = int(getattr(container, rep_field))
            setattr(container, rep_field, cur + 1)
        except Exception:
            pass
    for method_name in ("MarkItemDirty", "MarkArrayDirty", "ForceNetUpdate", "OnRep_MaxSize"):
        method = getattr(container, method_name, None)
        if callable(method):
            try:
                method()
            except TypeError:
                try:
                    method(container)
                except Exception:
                    pass
            except Exception:
                pass


def _container_max_size(ps: Any, container_name: str) -> Any | None:
    container = getattr(ps, container_name, None) if ps is not None else None
    return getattr(container, "MaxSize", None) if container is not None else None


def _container_values_match(ps: Any, container_name: str, size: int) -> bool:
    attr = _container_max_size(ps, container_name)
    if attr is None:
        return False
    for field in ("Value", "BaseValue"):
        try:
            if int(getattr(attr, field)) != int(size):
                return False
        except Exception:
            return False
    return True


def _safe_obj_name(obj: Any) -> str:
    for attr in ("Name", "name"):
        try:
            value = getattr(obj, attr)
            if value:
                return str(value)
        except Exception:
            pass
    try:
        return str(obj)
    except Exception:
        return "unknown"


def _stable_field_value(obj: Any, field: str) -> str:
    try:
        value = getattr(obj, field)
    except Exception:
        return ""
    if value is None:
        return ""
    if callable(value):
        try:
            value = value()
        except Exception:
            return ""
    text = str(value).strip()
    # Unreal/Python wrapper reprs often contain a transient memory address.
    # Never use those as an auto-apply key, or every UI frame can look like a
    # fresh spawn for the same player.
    if " object at 0x" in text or text.startswith("<") and "0x" in text:
        return ""
    return text[:200]


def _player_key(ps: Any, fallback_index: int) -> str:
    """Return a stable key for the current player slot.

    Do not include Python/SDK object addresses here: pyunrealsdk can hand the UI
    a different Python wrapper for the same underlying PlayerState between
    frames, which made auto inventory think the same player had spawned again.
    The key intentionally uses stable replicated/user-facing fields plus the
    party index. When that player leaves, the key drops from live_keys and a
    future join/spawn can get a new three-pass burst.
    """
    parts: list[str] = [f"idx:{fallback_index}"]
    for field in (
        "UniqueId",
        "UniqueNetId",
        "PlatformUserId",
        "PlayerId",
        "StableIndex",
        "PlayerName",
        "PlayerNamePrivate",
        "CachedPlayerName",
    ):
        value = _stable_field_value(ps, field)
        if value:
            parts.append(f"{field}:{value}")
    name = _gbc_resolve_player_display_name(ps)
    if name:
        parts.append(f"display:{name}")
    return "|".join(parts)


def _container_items_len(ps: Any, items_name: str) -> int | None:
    try:
        items_container = getattr(ps, items_name)
        items = getattr(items_container, "items")
        return len(items)
    except Exception:
        return None


def _inventory_looks_loaded(ps: Any) -> bool:
    """True once backpack/bank containers are writable.

    The previous auto path waited for owner/pawn and item arrays. In BL4 those
    signals are not reliable for every lobby/client state, which meant the
    automatic checkbox could stay armed but never actually write the values.
    Manual Apply works as soon as the containers exist, so automatic mode now
    uses the same readiness rule and keeps correcting resets during stabilization.
    """
    if ps is None:
        return False
    for container_name in ("BackpackContainer", "BankContainer"):
        container = getattr(ps, container_name, None)
        if container is None or getattr(container, "MaxSize", None) is None:
            return False
    return True

def set_container_size_on_player_state(ps: Any, container_name: str, size: int) -> bool:
    if ps is None:
        raise RuntimeError("PlayerState is not available.")
    container = getattr(ps, container_name, None)
    if container is None:
        raise RuntimeError(f"{container_name} is not available on PlayerState.")
    max_size = getattr(container, "MaxSize", None)
    if max_size is None:
        raise RuntimeError(f"{container_name}.MaxSize is not available.")
    size = clamp_container_size(size)
    if not _set_attr_integer(max_size, size):
        raise RuntimeError(f"Could not write {container_name}.MaxSize Value/BaseValue.")
    _bump_replication(container)
    _bump_replication(getattr(ps, container_name.replace("Container", "Items"), None))
    return True


def set_backpack_size_for_player_state(ps: Any, size: int) -> bool:
    return set_container_size_on_player_state(ps, "BackpackContainer", size)


def set_bank_size_for_player_state(ps: Any, size: int) -> bool:
    return set_container_size_on_player_state(ps, "BankContainer", size)


def set_inventory_sizes_for_player_state(ps: Any, backpack_size: int, bank_size: int) -> tuple[bool, bool]:
    bp = set_backpack_size_for_player_state(ps, backpack_size)
    bank = set_bank_size_for_player_state(ps, bank_size)
    return bp, bank


def set_inventory_sizes_for_party_index(index: int | None, backpack_size: int, bank_size: int) -> str:
    ps = get_player_state_by_party_index(index)
    if ps is None:
        raise RuntimeError("Selected party player was not found.")
    name = _gbc_resolve_player_display_name(ps)
    set_inventory_sizes_for_player_state(ps, backpack_size, bank_size)
    return name


def set_inventory_sizes_for_all_party(backpack_size: int, bank_size: int) -> int:
    count = 0
    errors: list[str] = []
    for _idx, name, ps in get_party_player_states():
        try:
            set_inventory_sizes_for_player_state(ps, backpack_size, bank_size)
            count += 1
        except Exception as exc:
            errors.append(f"{name}: {exc!r}")
    if errors:
        _log("Some inventory size updates failed: " + "; ".join(errors[:4]))
    return count


# State used by the BLImGui panel for automatic party application.
_auto_state: dict[str, dict[str, Any]] = {}
_auto_last_sizes: tuple[int, int] | None = None


def auto_apply_inventory_sizes_if_needed(enabled: bool, backpack_size: int, bank_size: int, *, source: str = "manual") -> int:
    """Deferred automatic capacity apply for current party members.

    Runs from the BLImGui draw path, not a background thread.  It waits for the
    inventory containers to look loaded, then applies at most three times for a
    stable player key. After those three passes, it stays quiet until that
    player key leaves the party/live set and appears again.
    """
    global _auto_state, _auto_last_sizes
    if not enabled:
        _auto_state = {}
        _auto_last_sizes = None
        return 0

    bp_size = clamp_container_size(backpack_size, _DEFAULT_BACKPACK_SIZE)
    bank_size = clamp_container_size(bank_size, _DEFAULT_BANK_SIZE)
    sizes = (bp_size, bank_size)
    if sizes != _auto_last_sizes:
        _auto_state = {}
        _auto_last_sizes = sizes

    now = time.monotonic()
    players = get_party_player_states()
    live_keys: set[str] = set()
    applied = 0

    for idx, name, ps in players:
        key = _player_key(ps, idx)
        live_keys.add(key)
        state = _auto_state.setdefault(
            key,
            {
                "seen": now,
                "ready_since": None,
                "last": 0.0,
                "last_log": 0.0,
                "name": name,
                "apply_count": 0,
            },
        )
        state["name"] = name

        if not _inventory_looks_loaded(ps):
            state["ready_since"] = None
            continue

        if state.get("ready_since") is None:
            state["ready_since"] = now
            continue

        ready_since = float(state.get("ready_since") or now)
        if now - ready_since < _AUTO_DEFER_SECONDS:
            continue
        if now - float(state.get("last", 0.0)) < _AUTO_RETRY_SECONDS:
            continue

        apply_count = int(state.get("apply_count", 0) or 0)
        if apply_count >= _AUTO_MAX_APPLIES_PER_SPAWN:
            continue

        try:
            set_inventory_sizes_for_player_state(ps, bp_size, bank_size)
            state["last"] = now
            state["apply_count"] = apply_count + 1
            applied += 1
        except Exception as exc:
            state["last"] = now
            if now - float(state.get("last_log", 0.0)) > 10.0:
                state["last_log"] = now
                _log(f"Automatic inventory size update failed for {name}: {exc!r}")

    # Drop players who left.
    for key in list(_auto_state):
        if key not in live_keys:
            _auto_state.pop(key, None)

    return applied


def _auto_inventory_worker() -> None:
    """Legacy worker retained only for compatibility.

    Do not start this in normal builds. Touching Unreal objects from a Python
    background thread during map change/exit can outlive the engine and crash
    with an access violation. Automatic inventory application is now driven from
    the BLImGui/main-thread draw path instead.
    """
    global _last_background_log
    while not _background_stop_event.wait(_AUTO_POLL_SECONDS):
        # Intentionally no Unreal access here.
        pass


def stop_auto_inventory_worker(timeout: float = 1.0) -> None:
    """Stop any legacy background inventory worker without touching Unreal."""
    global _background_stop, _background_thread
    _background_stop = True
    _background_stop_event.set()
    thread = _background_thread
    if thread is not None and thread.is_alive():
        try:
            thread.join(timeout=float(timeout))
        except Exception:
            pass
    _background_thread = None


def start_auto_inventory_worker() -> None:
    """Compatibility no-op.

    Older builds started a daemon thread here. That was unsafe at game shutdown,
    because it could read/write PlayerState containers while BL4/pyunrealsdk was
    tearing down. Leaving this as a no-op prevents the hanging-thread exit crash.
    """
    global _background_started
    if _background_started:
        return
    _background_started = True
    _background_stop_event.set()
    _log("Automatic inventory background worker disabled; using main-thread/menu-safe auto apply.")


try:
    atexit.register(stop_auto_inventory_worker)
except Exception:
    pass
