"""Central release point for UObject-adjacent caches during world travel."""
from __future__ import annotations

import sys
import time
from typing import Any

from mods_base import hook
from unrealsdk import logging
from unrealsdk.hooks import Type

from .travel_gate import mark_travel

_PREFIX = "[Matts SDK Boosting Tools | Cleanup]"
_last_error_at: dict[str, float] = {}


def _warn_limited(message: str) -> None:
    now = time.monotonic()
    if now - _last_error_at.get(message, 0.0) < 5.0:
        return
    _last_error_at[message] = now
    logging.warning(f"{_PREFIX} {message}")


def _call(label: str, fn: Any) -> None:
    if not callable(fn):
        return
    try:
        fn()
    except Exception as exc:
        _warn_limited(f"{label} cleanup failed: {exc!r}")


def clear_travel_caches() -> None:
    """Release old-world wrappers without importing the optional BLImGui panel."""
    from . import backend_actions, golden_chest_keybinds, hoard_runner
    from . import instant_click_holds, movement_adjustments, no_fog_of_war
    from . import serial_rewards, spawn_helpers, streamer_chaos

    _call("backend", backend_actions.clear_uobject_caches)
    _call("spawns", spawn_helpers.clear_tracked)
    _call("hoard", hoard_runner.clear_travel_state)
    _call("streamer chaos", streamer_chaos.clear_runtime_state)
    _call("golden chest", golden_chest_keybinds.clear_pending_closes)
    _call("serial delivery", serial_rewards.clear_delivery_state)
    _call("movement", movement_adjustments._clear_infinite_jump_runtime_caches)
    _call("instant holds", instant_click_holds.clear_travel_backups)
    _call("fog", no_fog_of_war.clear_travel_backups)

    panel = sys.modules.get(f"{__package__}.blimgui_panel")
    if panel is not None:
        _call("BLImGui", getattr(panel, "clear_travel_caches", None))


@hook(
    "OakGame.OakPlayerController:ClientTravel",
    Type.POST,
    immediately_enable=True,
    hook_identifier="msbt_runtime_cleanup_travel_oak_v1",
)
@hook(
    "Engine.PlayerController:ClientTravel",
    Type.POST,
    immediately_enable=True,
    hook_identifier="msbt_runtime_cleanup_travel_engine_v1",
)
def _after_travel(*_args: Any, **_kwargs: Any) -> None:
    # Only flip the quiet gate here. Cache wipes import other MSBT modules and
    # must not run while the world is unloading or while this package is loading.
    mark_travel()
