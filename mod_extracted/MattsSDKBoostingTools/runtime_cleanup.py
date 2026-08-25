"""Central release point for UObject-adjacent caches during world travel."""
from __future__ import annotations

import sys
import time
from typing import Any

from mods_base import hook
from unrealsdk import logging
from unrealsdk.hooks import Type

from .hook_gate import disable_join_hooks, request_arm_when_pawn_ready, try_arm_from_controller
from .travel_gate import mark_menu, mark_travel

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
    from . import third_person_camera
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
    _call("third person", third_person_camera.clear_travel_backups)

    panel = sys.modules.get(f"{__package__}.blimgui_panel")
    if panel is not None:
        _call("BLImGui", getattr(panel, "clear_travel_caches", None))


def _world_package_name(*hook_args: Any, **hook_kwargs: Any) -> str:
    """Read only the FName argument. Do not stringify the player controller."""
    args = hook_args[1] if len(hook_args) > 1 else hook_kwargs.get("args")
    if args is None:
        return ""
    for attr in ("WorldPackageName", "WorldName"):
        try:
            value = getattr(args, attr, None)
        except Exception:
            value = None
        if value is None:
            continue
        try:
            text = str(value)
        except Exception:
            continue
        if text:
            return text.lower()
    return ""


def _looks_like_menu(text: str) -> bool:
    name = (text or "").lower().replace("\\", "/")
    return any(
        marker in name
        for marker in ("mainmenu", "title_screen", "titlescreen", "frontendmap", "/frontend")
    )


def _looks_like_gameplay(text: str) -> bool:
    if _looks_like_menu(text):
        return False
    name = (text or "").lower()
    if any(marker in name for marker in ("world_p", "fortress_", "vault_", "cityvault", "raid_")):
        return True
    # Banjo_P is also the title menu (Banjo_P.MainMenu). Only treat DLC loads.
    return any(marker in name for marker in ("ft_banjo", "lt_banjo", "dlc/banjo", "banjo_p.banjo_p"))


@hook(
    "OakGame.OakPlayerController:ClientTravel",
    Type.PRE,
    immediately_enable=False,
    hook_identifier="msbt_runtime_cleanup_travel_oak_v1",
)
@hook(
    "Engine.PlayerController:ClientTravel",
    Type.PRE,
    immediately_enable=False,
    hook_identifier="msbt_runtime_cleanup_travel_engine_v1",
)
def _after_travel(*_args: Any, **_kwargs: Any) -> None:
    # Travel and return-to-menu both tear the world down. Drop join-unsafe hooks
    # immediately; do not touch other MSBT modules here.
    mark_travel()
    try:
        disable_join_hooks()
    except Exception:
        pass
    try:
        logging.info(f"{_PREFIX} quiet on (ClientTravel); hooks off")
    except Exception:
        pass


@hook(
    "OakGame.OakPlayerController:ServerNotifyLoadedWorld",
    Type.POST,
    immediately_enable=True,
    hook_identifier="msbt_runtime_cleanup_loaded_oak_v1",
)
@hook(
    "Engine.PlayerController:ServerNotifyLoadedWorld",
    Type.POST,
    immediately_enable=True,
    hook_identifier="msbt_runtime_cleanup_loaded_engine_v1",
)
def _after_loaded_world(*args: Any, **kwargs: Any) -> None:
    # Host may already be in World_P while this client still has no pawn.
    # Never inspect the controller here; never arm hooks on world name alone.
    world = _world_package_name(*args, **kwargs)
    if _looks_like_menu(world):
        mark_menu()
        try:
            disable_join_hooks()
        except Exception:
            pass
        try:
            logging.info(f"{_PREFIX} menu world; hooks off ({world[:80]})")
        except Exception:
            pass
        return
    if not _looks_like_gameplay(world):
        try:
            disable_join_hooks()
        except Exception:
            pass
        try:
            logging.info(f"{_PREFIX} not gameplay yet; hooks stay off ({world[:80]})")
        except Exception:
            pass
        return
    try:
        from .hook_gate import hooks_enabled
        if hooks_enabled():
            return
    except Exception:
        pass
    mark_travel()
    try:
        disable_join_hooks()
    except Exception:
        pass
    try:
        request_arm_when_pawn_ready(1.0)
    except Exception as exc:
        try:
            logging.warning(f"{_PREFIX} pawn wait failed: {exc!r}")
        except Exception:
            pass
    try:
        logging.info(f"{_PREFIX} gameplay map; waiting for live pawn ({world[:80]})")
    except Exception:
        pass


@hook(
    "OakGame.OakPlayerController:ClientRestart",
    Type.POST,
    immediately_enable=True,
    hook_identifier="msbt_runtime_cleanup_restart_oak_v1",
)
@hook(
    "Engine.PlayerController:ClientRestart",
    Type.POST,
    immediately_enable=True,
    hook_identifier="msbt_runtime_cleanup_restart_engine_v1",
)
def _after_client_restart(obj: Any, *_args: Any, **_kwargs: Any) -> None:
    # Guest join fires this while the pawn is still missing. Leave hooks off
    # until OakCharacter/Pawn is actually on this controller.
    try:
        try_arm_from_controller(obj)
    except Exception:
        pass
