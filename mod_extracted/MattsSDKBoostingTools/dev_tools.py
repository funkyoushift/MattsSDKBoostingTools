"""Developer perk and debug camera helpers for Matt's SDK Boosting Tools."""
from __future__ import annotations

from typing import Any
import time

import unrealsdk
from mods_base import get_pc
from unrealsdk import logging

from .player_economy import _resolve_target_pc_for_index
from .party_helpers import _gbc_is_listen_host_world, _gbc_session_world_and_gamestate

_PREFIX = "[Matts SDK Boosting Tools | Dev]"
_MIN_DEBUG_SPEED = 0.05
_MAX_DEBUG_SPEED = 50.0
_DEFAULT_DEBUG_SPEED = 1.0
_debug_speed_value: float = _DEFAULT_DEBUG_SPEED
_live_dcc_cache: Any | None = None
_live_dcc_cache_until: float = 0.0
_toggle_states_by_player: dict[str, dict[int, bool]] = {}

_DEVPERK_LABELS = {
    0: "Give Experience",
    1: "Give 1 Million Cash",
    2: "Give 100k Eridium",
    3: "Kill All Enemies",
    4: "Grant ALL Customizations and Hover Drives",
    5: "Infinite Ammo",
    6: "Demigod",
    7: "Spawn Legendary/Epic Loot",
}


def _log(message: str) -> None:
    logging.info(f"{_PREFIX} {message}")


def clamp_debug_speed(value: float) -> float:
    try:
        v = float(value)
    except Exception:
        v = _DEFAULT_DEBUG_SPEED
    return max(_MIN_DEBUG_SPEED, min(v, _MAX_DEBUG_SPEED))


def devperk_label(index: int) -> str:
    return _DEVPERK_LABELS.get(int(index), f"Unknown Perk {int(index)}")


def _devperk_player_key_from_pc(pc: Any | None, player_index: int | None = None) -> str:
    """Return a stable-ish key for tracking toggle-only dev perks per player.

    Infinite Ammo and Demigod are server toggle commands. The game does not expose
    a reliable readable ON/OFF value through the SDK, so the UI tracks what this
    mod last requested. New/unknown players intentionally start OFF.
    """
    ps = getattr(pc, "PlayerState", None) if pc is not None else None
    for attr in ("UniqueId", "PlayerId", "SavedNetworkAddress", "PlayerNamePrivate", "PlayerName"):
        try:
            value = getattr(ps, attr, None) if ps is not None else None
            if callable(value):
                value = value()
            if value not in (None, ""):
                return f"ps:{attr}:{value}"
        except Exception:
            pass
    try:
        name_fn = getattr(ps, "GetPlayerName", None) if ps is not None else None
        if callable(name_fn):
            name = name_fn()
            if name:
                return f"name:{name}"
    except Exception:
        pass
    if pc is not None:
        try:
            return f"pc:{getattr(pc, 'Name', None) or pc}"
        except Exception:
            return f"pc:{pc}"
    return f"party_index:{player_index}"


def _devperk_states_for_player(player_index: int | None = None, pc: Any | None = None) -> dict[int, bool]:
    if pc is None:
        try:
            pc, _ = _pc_for_party_index(player_index)
        except Exception:
            pc = None
    key = _devperk_player_key_from_pc(pc, player_index)
    return _toggle_states_by_player.setdefault(key, {5: False, 6: False})


def devperk_toggle_state(index: int, player_index: int | None = None) -> bool | None:
    """Return cached toggle state for toggled dev perks for one player.

    New/unknown players are assumed OFF until this mod toggles them ON.
    """
    perk = int(index)
    if perk not in (5, 6):
        return None
    return bool(_devperk_states_for_player(player_index).get(perk, False))


def devperk_button_label(index: int, player_index: int | None = None) -> str:
    label = devperk_label(index)
    state = devperk_toggle_state(index, player_index)
    if state is None:
        return label
    return f"{label} [{'ON' if state else 'OFF'}]"


def _is_listen_host_safe() -> bool:
    try:
        world, _gs = _gbc_session_world_and_gamestate()
        return bool(world is not None and _gbc_is_listen_host_world(world))
    except Exception:
        return False


def _pc_for_party_index(player_index: int | None) -> tuple[Any | None, str]:
    # Dev perk server RPCs can be requested from a joined client through that
    # client's own local PlayerController. Do not block all cheats just because
    # we are not the listen host. Only host-side remote targeting should use the
    # PlayerArray resolver.
    if player_index is None:
        pc = get_pc()
        return pc, "" if pc is not None else "No local PlayerController found."
    if not _is_listen_host_safe():
        pc = get_pc()
        if pc is None:
            return None, "No local PlayerController found."
        return pc, "client-local PlayerController"
    pc, err = _resolve_target_pc_for_index(int(player_index))
    return pc, err


def activate_devperk(index: int, player_index: int | None = None) -> str:
    perk = int(index)
    if perk < 0 or perk > 7:
        raise ValueError("Dev perk index must be 0 through 7.")
    pc, err = _pc_for_party_index(player_index)
    if pc is None:
        raise RuntimeError(err or "No PlayerController found.")
    fn = getattr(pc, "ServerActivateDevPerk", None)
    if not callable(fn):
        raise RuntimeError("Selected PlayerController does not expose ServerActivateDevPerk.")
    fn(perk)
    if perk in (5, 6):
        states = _devperk_states_for_player(player_index, pc)
        states[perk] = not bool(states.get(perk, False))
    label = devperk_label(perk)
    return label


def _live_local_player() -> Any | None:
    try:
        players = [x for x in unrealsdk.find_all("OakLocalPlayer") if "Default__" not in getattr(x, "Name", "")]
        return players[0] if players else None
    except Exception:
        return None


def _is_debug_camera_controller(obj: Any | None) -> bool:
    if obj is None:
        return False
    try:
        return "DebugCameraController" in str(getattr(obj, "Class", "")) or "DebugCameraController" in str(obj)
    except Exception:
        return False


def _unwrap_debug_camera_controller(pc: Any | None) -> Any | None:
    """Return the original local PlayerController when debug cam has possession.

    Joined-client debug cam can make get_pc()/OakLocalPlayer.PlayerController point
    at a DebugCameraController.  Treating that as the gameplay PC makes host checks
    and UI helpers walk the wrong objects, which causes heavy stutter off-host.
    """
    if not _is_debug_camera_controller(pc):
        return pc
    for attr in ("OriginalControllerRef", "OriginalController"):
        try:
            original = getattr(pc, attr, None)
            if original is not None and not _is_debug_camera_controller(original):
                return original
        except Exception:
            pass
    try:
        cm = getattr(pc, "CheatManager", None)
        original = getattr(cm, "Outer", None) if cm is not None else None
        if original is not None and not _is_debug_camera_controller(original):
            return original
    except Exception:
        pass
    return pc


def _live_pc() -> Any | None:
    # Local host/client-only controller lookup for debug camera.
    # This intentionally does NOT use selected party targets because debug cam is local-only.
    lp = _live_local_player()
    pc = getattr(lp, "PlayerController", None) if lp is not None else None
    if pc is not None:
        return _unwrap_debug_camera_controller(pc)
    try:
        return _unwrap_debug_camera_controller(get_pc())
    except Exception:
        return None


def _live_dcc() -> Any | None:
    global _live_dcc_cache, _live_dcc_cache_until
    now = time.monotonic()
    try:
        if _live_dcc_cache is not None and now < float(_live_dcc_cache_until or 0.0):
            return _live_dcc_cache
    except Exception:
        pass
    try:
        # First try the current/local player controller without scanning all objects.
        for candidate in (get_pc(), getattr(_live_local_player(), "PlayerController", None)):
            if _is_debug_camera_controller(candidate):
                _live_dcc_cache = candidate
                _live_dcc_cache_until = now + 1.0
                return candidate
            try:
                cm = getattr(candidate, "CheatManager", None) if candidate is not None else None
                dcc = getattr(cm, "DebugCameraControllerRef", None) if cm is not None else None
                if dcc is not None:
                    _live_dcc_cache = dcc
                    _live_dcc_cache_until = now + 1.0
                    return dcc
            except Exception:
                pass
    except Exception:
        pass
    try:
        cams = [x for x in unrealsdk.find_all("DebugCameraController", False) if "Default__" not in getattr(x, "Name", "")]
        _live_dcc_cache = cams[0] if cams else None
        _live_dcc_cache_until = now + 1.0
        return _live_dcc_cache
    except Exception:
        _live_dcc_cache = None
        _live_dcc_cache_until = now + 0.25
        return None


def _ensure_cheat_manager(pc: Any) -> Any:
    cm = getattr(pc, "CheatManager", None)
    if cm is not None:
        return cm
    cheat_class = getattr(pc, "CheatClass", None)
    if cheat_class is None:
        raise RuntimeError("PlayerController has no CheatClass.")
    cm = unrealsdk.construct_object(cheat_class, pc, "OakCheatManager_MattsSDKBoostingTools")
    pc.CheatManager = cm
    return cm


def toggle_debug_cam(player_index: int | None = None) -> str:
    # Debug cam is local-only. Do not try to toggle it for remote selected players.
    # Keep the toggle path intentionally close to the SDK Debug Menu/Mattmab
    # console workaround: use the live OakLocalPlayer controller directly,
    # create the native cheat manager if needed, then call ToggleDebugCamera.
    lp = _live_local_player()
    pc = _unwrap_debug_camera_controller(getattr(lp, "PlayerController", None) if lp is not None else None)
    if pc is None or _is_debug_camera_controller(pc):
        pc = _live_pc()
    if pc is None or _is_debug_camera_controller(pc):
        pc = _original_player_controller_for_debugcam()
    if pc is None or _is_debug_camera_controller(pc):
        raise RuntimeError("No local OakPlayerController found.")
    cm = getattr(pc, "CheatManager", None)
    if cm is None:
        cheat_class = getattr(pc, "CheatClass", None)
        if cheat_class is None:
            raise RuntimeError("Local PlayerController has no CheatClass.")
        cm = unrealsdk.construct_object(cheat_class, pc, "OakCheatManager_SDK")
        pc.CheatManager = cm
    toggle = getattr(cm, "ToggleDebugCamera", None)
    if not callable(toggle):
        raise RuntimeError("Local CheatManager does not expose ToggleDebugCamera.")
    global _live_dcc_cache, _live_dcc_cache_until
    _live_dcc_cache = None
    _live_dcc_cache_until = 0.0
    toggle()
    dcc = getattr(cm, "DebugCameraControllerRef", None) or _live_dcc()
    if dcc is not None:
        try:
            _apply_debug_speed_to_controller(dcc, _debug_speed_value)
        except Exception:
            pass
    try:
        _log(f"ToggleDebugCamera pc={pc} cm={cm} debugcam={dcc}")
    except Exception:
        pass
    return "Debug camera toggled locally."


def _apply_debug_speed_to_controller(dcc: Any, speed: float) -> None:
    try:
        dcc.SetPawnMovementSpeedScale(float(speed))
        return
    except Exception:
        pass
    try:
        dcc.SpeedScale = float(speed)
        return
    except Exception as exc:
        raise RuntimeError(f"Speed set failed: {exc!r}")


def _debug_cam_for_pc(pc: Any | None) -> Any | None:
    if pc is not None:
        try:
            cm = getattr(pc, "CheatManager", None)
            if cm is not None:
                dcc = getattr(cm, "DebugCameraControllerRef", None)
                if dcc is not None:
                    return dcc
        except Exception:
            pass
    return _live_dcc()


def set_debug_cam_speed(value: float, player_index: int | None = None) -> str:
    global _debug_speed_value
    _debug_speed_value = clamp_debug_speed(value)
    # Debug cam speed is local-only. Do not try to set this on remote clients.
    pc = _live_pc()
    dcc = _debug_cam_for_pc(pc)
    if dcc is None:
        return f"Debug cam speed stored as {_debug_speed_value:.2f}; no live local debug cam."
    _apply_debug_speed_to_controller(dcc, _debug_speed_value)
    return f"Debug cam speed set to {_debug_speed_value:.2f} on local debug cam."


def get_debug_cam_speed() -> float:
    return float(_debug_speed_value)

def _actor_location(actor: Any | None) -> Any | None:
    if actor is None:
        return None
    for name in ("K2_GetActorLocation", "GetActorLocation"):
        try:
            fn = getattr(actor, name, None)
            if callable(fn):
                return fn()
        except Exception:
            pass
    try:
        root = getattr(actor, "RootComponent", None)
        if root is not None:
            return getattr(root, "RelativeLocation", None)
    except Exception:
        pass
    return None


def _original_player_controller_for_debugcam() -> Any | None:
    dcc = _live_dcc()
    if dcc is not None:
        for attr in ("OriginalControllerRef", "OriginalController", "PendingSwapConnection"):
            try:
                pc = getattr(dcc, attr, None)
                if pc is not None and "PlayerController" in str(getattr(pc, "Class", "")):
                    return pc
            except Exception:
                pass
    try:
        pcs = [x for x in unrealsdk.find_all("OakPlayerController") if "Default__" not in getattr(x, "Name", "")]
        if pcs:
            return pcs[0]
    except Exception:
        pass
    return _live_pc()


def _player_pawn_from_original_pc() -> tuple[Any | None, Any | None]:
    pc = _original_player_controller_for_debugcam()
    if pc is None:
        return None, None
    for attr in ("OakCharacter", "Character", "Pawn", "AcknowledgedPawn"):
        try:
            pawn = getattr(pc, attr, None)
            if pawn is not None:
                return pc, pawn
        except Exception:
            pass
    for fn_name in ("GetPawn", "K2_GetPawn"):
        try:
            fn = getattr(pc, fn_name, None)
            if callable(fn):
                pawn = fn()
                if pawn is not None:
                    return pc, pawn
        except Exception:
            pass
    try:
        chars = [x for x in unrealsdk.find_all("OakCharacter") if "Default__" not in getattr(x, "Name", "")]
        for ch in chars:
            try:
                if getattr(ch, "Controller", None) == pc:
                    return pc, ch
            except Exception:
                pass
        if chars:
            return pc, chars[0]
    except Exception:
        pass
    return pc, None


def _pawn_for_pc(pc: Any | None) -> Any | None:
    if pc is None:
        return None
    for attr in ("OakCharacter", "Character", "Pawn", "AcknowledgedPawn"):
        try:
            pawn = getattr(pc, attr, None)
            if pawn is not None:
                return pawn
        except Exception:
            pass
    for fn_name in ("GetPawn", "K2_GetPawn"):
        try:
            fn = getattr(pc, fn_name, None)
            if callable(fn):
                pawn = fn()
                if pawn is not None:
                    return pawn
        except Exception:
            pass
    try:
        chars = [x for x in unrealsdk.find_all("OakCharacter") if "Default__" not in getattr(x, "Name", "")]
        for ch in chars:
            try:
                if getattr(ch, "Controller", None) == pc:
                    return ch
            except Exception:
                pass
    except Exception:
        pass
    return None


def teleport_pawn_to_debug_cam(player_index: int | None = None) -> str:
    # Moving a selected pawn to the host/local debug camera requires host-side
    # authority and remote pawn resolution. Keep this one gated off for joined
    # clients; other Cheats / Debug Cam actions remain client-local.
    if not _is_listen_host_safe():
        raise RuntimeError("Teleport Pawn to Debug Cam is host-only.")
    target_pc, err = _pc_for_party_index(player_index)
    if target_pc is None:
        raise RuntimeError(err or "No selected PlayerController found.")

    # Debug cam is local-only. Use the host/local debug cam as the marker/location source.
    # The pawn being moved is still the selected player's pawn.
    dcc = _debug_cam_for_pc(_live_pc())
    if dcc is None:
        raise RuntimeError("No live DebugCameraController. Toggle debug cam first.")

    pc = target_pc
    pawn = _pawn_for_pc(pc)
    if pawn is None:
        raise RuntimeError("Could not find pawn/character on selected PlayerController.")

    # Use the freecam spectator pawn location when present; fall back to the controller transform.
    sp = getattr(dcc, "SpectatorPawn", None)
    loc = _actor_location(sp) if sp is not None else None
    if loc is None:
        loc = _actor_location(dcc)
    if loc is None:
        raise RuntimeError("Could not read debug camera/freecam location.")

    try:
        rot = getattr(dcc, "ControlRotation", None)
    except Exception:
        rot = None
    if rot is None:
        try:
            rot = pawn.K2_GetActorRotation()
        except Exception:
            rot = None

    collision_was_enabled = None
    try:
        collision_was_enabled = bool(getattr(pawn, "bActorEnableCollision"))
    except Exception:
        pass

    try:
        try:
            pawn.SetActorEnableCollision(False)
        except Exception:
            try:
                pawn.bActorEnableCollision = False
            except Exception:
                pass

        ok = False
        try:
            ok = bool(pawn.K2_TeleportTo(loc, rot))
        except Exception:
            try:
                ok = bool(pawn.K2_SetActorLocation(loc, False, None, False))
                if rot is not None:
                    try:
                        pawn.K2_SetActorRotation(rot, False)
                    except Exception:
                        pass
            except Exception as exc:
                raise RuntimeError(f"Teleport call failed: {exc!r}")
        return f"Teleported pawn to debug cam location; ok={ok}."
    finally:
        try:
            if collision_was_enabled is not None:
                pawn.SetActorEnableCollision(collision_was_enabled)
            else:
                pawn.SetActorEnableCollision(True)
        except Exception:
            try:
                if collision_was_enabled is not None:
                    pawn.bActorEnableCollision = collision_was_enabled
            except Exception:
                pass
