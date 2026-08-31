"""Single BlueprintModifyCamera pump for MSBT.

Oak calls that function once per active CameraModifier, several times a frame.
Each extra Python hook multiplies that cost and is the usual FPS leak. Camera-tick
work should register here so the engine only crosses into Python through one hook.

The hook stays off until a feature actually needs it (Quick Menu open, slot
hotkeys, Infinite Jump, Super Dash, Combat XP, Party Reveal, pending
chest/chaos/market).
"""
from __future__ import annotations

import time
from typing import Any, Callable

from . import travel_gate

TickFn = Callable[..., Any]

TICK_PATH = "/Script/Engine.CameraModifier:BlueprintModifyCamera"
HOOK_ID = "msbt_shared_camera_tick_v1"
# Cap shared camera work at 120 Hz. Individual subscribers can skip internally.
MIN_INTERVAL_S = 1.0 / 120.0
_LEGACY_HOOK_IDS = (
    "matts_sdk_boosting_tools_quick_menu_tick_v1",
    "matts_sdk_boosting_tools_backend_infinite_jump_camera_v1",
    "matts_sdk_boosting_tools_super_dash_camera_v2",
    "msbt_golden_chest_close_tick_v1",
    "msbt_cxp_camera_tick_v1",
    "msbt_streamer_chaos_launch_v1",
)

_last_at = 0.0
_in_flight = False
_installed = False
_callbacks: list[tuple[int, str, TickFn]] = []
_needed: set[str] = set()


def register(name: str, callback: TickFn, *, priority: int = 100) -> None:
    """Register a camera-tick callback. Does not install the engine hook."""
    global _callbacks
    key = str(name or "unnamed")
    _callbacks = [(prio, existing, fn) for prio, existing, fn in _callbacks if existing != key]
    _callbacks.append((int(priority), key, callback))
    _callbacks.sort(key=lambda row: (row[0], row[1]))


def _ui_needed() -> bool:
    return any(name.startswith("quick_menu") for name in _needed)


def set_needed(name: str, needed: bool) -> None:
    """Keep the shared camera hook installed only while something needs it.

    Quick Menu and Phone Pairing must poll clicks as soon as they open, even if
    travel-quiet is stuck. Other features still wait for the in-world release.
    """
    key = str(name or "unnamed")
    if needed:
        _needed.add(key)
        if key.startswith("quick_menu") or not travel_gate.is_travel_quiet():
            _ensure_hook()
        return
    _needed.discard(key)
    if not _needed:
        disable_shared_hook()


def enable_shared_hook() -> None:
    if _needed:
        _ensure_hook()


def disable_shared_hook() -> None:
    global _installed
    if not _installed:
        return
    try:
        import unrealsdk
        from unrealsdk.hooks import Type

        unrealsdk.hooks.remove_hook(TICK_PATH, Type.POST, HOOK_ID)
    except Exception:
        pass
    _installed = False
    try:
        from unrealsdk import logging

        logging.info("[Matts SDK Boosting Tools] camera hook off")
    except Exception:
        pass


def _pump(_obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    global _last_at, _in_flight
    if _in_flight:
        return None
    if travel_gate.is_travel_quiet() and not _ui_needed():
        return None
    if travel_gate.consume_pending_clear():
        try:
            from .runtime_cleanup import clear_travel_caches

            clear_travel_caches()
        except Exception:
            pass
    now = time.monotonic()
    if now - _last_at < MIN_INTERVAL_S:
        return None
    _last_at = now
    _in_flight = True
    try:
        quiet = travel_gate.is_travel_quiet()
        for _prio, _name, fn in _callbacks:
            if quiet and not _name.startswith("quick_menu"):
                continue
            try:
                fn(_obj, _args, _ret, _func)
            except Exception:
                pass
    finally:
        _in_flight = False
    return None


def _ensure_hook() -> None:
    global _installed
    if _installed:
        return
    try:
        import unrealsdk
        from unrealsdk.hooks import Type

        for legacy_id in _LEGACY_HOOK_IDS:
            try:
                unrealsdk.hooks.remove_hook(TICK_PATH, Type.PRE, legacy_id)
            except Exception:
                pass
            try:
                unrealsdk.hooks.remove_hook(TICK_PATH, Type.POST, legacy_id)
            except Exception:
                pass
        try:
            unrealsdk.hooks.remove_hook(TICK_PATH, Type.POST, HOOK_ID)
        except Exception:
            pass
        unrealsdk.hooks.add_hook(TICK_PATH, Type.POST, HOOK_ID, _pump)
        _installed = True
        try:
            from unrealsdk import logging

            logging.info(
                "[Matts SDK Boosting Tools] camera hook on ("
                + ",".join(sorted(_needed))
                + ")"
            )
        except Exception:
            pass
        return
    except Exception:
        pass
    try:
        from mods_base import hook

        hook(TICK_PATH, immediately_enable=False, hook_identifier=HOOK_ID)(_pump)
        _installed = True
    except Exception:
        _installed = False
