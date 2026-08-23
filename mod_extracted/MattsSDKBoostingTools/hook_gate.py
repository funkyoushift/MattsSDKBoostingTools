"""Enable engine hooks only after this client has a live pawn.

A guest join can load the host's gameplay world before OakCharacter exists.
World-name checks must not arm camera/viewport/jump hooks, and join callbacks
must not stringify the player controller.
"""
from __future__ import annotations

import sys
import time
from typing import Any

_ENABLED = False
_PENDING_ARM = False
_PENDING_AFTER = 0.0
_TRACKED: list[Any] = []
_PACKAGE = __package__ or "MattsSDKBoostingTools"
_KEEP_HOOK_MODULES = {
    f"{_PACKAGE}.runtime_cleanup",
    f"{_PACKAGE}.travel_watch",
    f"{_PACKAGE}.hook_gate",
    f"{_PACKAGE}.travel_gate",
}


def track(hook_obj: Any) -> Any:
    """Keep dynamically created HookType objects so disable/enable can find them."""
    if hook_obj is not None and hook_obj not in _TRACKED:
        _TRACKED.append(hook_obj)
    return hook_obj


def _is_hook_obj(value: Any) -> bool:
    return hasattr(value, "enable") and hasattr(value, "disable") and hasattr(value, "hook_funcs")


def _iter_package_hooks(*, keep_safe: bool) -> list[Any]:
    found: list[Any] = []
    prefix = f"{_PACKAGE}."
    for name, mod in list(sys.modules.items()):
        if name != _PACKAGE and not name.startswith(prefix):
            continue
        if keep_safe and name in _KEEP_HOOK_MODULES:
            continue
        if mod is None:
            continue
        try:
            values = vars(mod).values()
        except Exception:
            continue
        for value in values:
            if _is_hook_obj(value):
                found.append(value)
    for value in list(_TRACKED):
        if _is_hook_obj(value) and value not in found:
            found.append(value)
    return found


def disable_join_hooks() -> None:
    """Turn off every MSBT engine hook except the travel/load gate."""
    global _ENABLED, _PENDING_ARM
    _PENDING_ARM = False
    _ENABLED = False
    try:
        from . import camera_tick

        camera_tick.disable_shared_hook()
    except Exception:
        pass
    for hook_obj in _iter_package_hooks(keep_safe=True):
        try:
            hook_obj.disable()
        except Exception:
            continue


def request_arm_when_pawn_ready(delay: float = 5.0) -> None:
    """Remember that a gameplay map is up. Do not touch Unreal objects here."""
    global _PENDING_ARM, _PENDING_AFTER
    if _ENABLED:
        return
    _PENDING_ARM = True
    try:
        wait = max(1.0, float(delay))
    except Exception:
        wait = 5.0
    _PENDING_AFTER = time.monotonic() + wait


def try_arm_from_controller(obj: Any) -> None:
    """Game-thread only. Arm after ClientRestart once this controller has a pawn."""
    global _PENDING_ARM
    if _ENABLED or not _PENDING_ARM:
        return
    if time.monotonic() < float(_PENDING_AFTER):
        return
    if obj is None:
        return
    try:
        pawn = getattr(obj, "OakCharacter", None) or getattr(obj, "Pawn", None)
    except Exception:
        return
    if pawn is None:
        return
    _PENDING_ARM = False
    try:
        from unrealsdk import logging

        logging.info("[Matts SDK Boosting Tools] live pawn ready; arming hooks")
    except Exception:
        pass
    try:
        from .travel_gate import schedule_in_world

        schedule_in_world(2.0)
    except Exception:
        pass
    enable_join_hooks()


def enable_join_hooks() -> None:
    """Turn runtime hooks on. Caller must already have a live pawn."""
    global _ENABLED, _PENDING_ARM
    _PENDING_ARM = False
    if _ENABLED:
        return
    _ENABLED = True
    for hook_obj in _iter_package_hooks(keep_safe=True):
        try:
            hook_obj.enable()
        except Exception:
            continue
    try:
        from . import camera_tick

        camera_tick.enable_shared_hook()
    except Exception:
        pass


def enable_join_hooks_later(delay: float = 5.0) -> None:
    request_arm_when_pawn_ready(delay)


def enable_join_hooks_when_pawn_ready(*, first_delay: float = 5.0, retry_delay: float = 2.0) -> None:
    request_arm_when_pawn_ready(first_delay)


def hooks_enabled() -> bool:
    return bool(_ENABLED)
