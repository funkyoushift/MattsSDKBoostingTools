"""Golden chest open/close helper keybinds."""

from __future__ import annotations

import threading
from typing import Any, Optional

from mods_base import get_pc, keybind
from unrealsdk import find_all, find_object, logging
from unrealsdk.unreal import WrappedStruct

_PREFIX = "[Matts SDK Boosting Tools | GoldenChest]"
_STATE_KEY_PATH = "/Script/GbxEngine.GbxActorStateMachineStateKey"
_CLOSE_AFTER_DETACH_DELAY_S = 0.75


def _log(msg: str, *args: Any) -> None:
    logging.info(_PREFIX + " " + (msg % args if args else msg))


def _log_err(msg: str, *args: Any) -> None:
    logging.error(_PREFIX + " " + (msg % args if args else msg))


def _get_player_pawn() -> Optional[Any]:
    pc = get_pc()
    if pc is None:
        return None
    return getattr(pc, "OakCharacter", None) or getattr(pc, "Pawn", None)


def _distance_sq(a: Any, b: Any) -> float:
    dx = float(a.X - b.X)
    dy = float(a.Y - b.Y)
    dz = float(a.Z - b.Z)
    return dx * dx + dy * dy + dz * dz


def _find_nearest_golden_chest(chests: list[Any]) -> Any:
    pawn = _get_player_pawn()
    if pawn is None:
        _log_err("Could not get player pawn; falling back to first live golden chest.")
        return chests[0]

    try:
        player_loc = pawn.K2_GetActorLocation()
    except Exception as e:
        _log_err("Could not read player location; falling back to first live golden chest: %s", e)
        return chests[0]

    nearest_chest = None
    nearest_dist_sq = 0.0
    for chest in chests:
        try:
            chest_loc = chest.K2_GetActorLocation()
            dist_sq = _distance_sq(chest_loc, player_loc)
        except Exception as e:
            _log_err("Could not read golden chest location; skipping %s: %s", chest, e)
            continue
        if nearest_chest is None or dist_sq < nearest_dist_sq:
            nearest_chest = chest
            nearest_dist_sq = dist_sq

    if nearest_chest is None:
        _log_err("Could not read any golden chest locations; falling back to first live golden chest.")
        return chests[0]

    _log("Selected nearest golden chest at %.0f uu: %s", nearest_dist_sq**0.5, nearest_chest)
    return nearest_chest


def _find_golden_chest_script() -> Optional[Any]:
    try:
        chests = [o for o in find_all("LootableObject") if "Lootable_GoldenChest" in str(o)]
    except Exception as e:
        _log_err("Could not scan LootableObject instances: %s", e)
        return None
    if not chests:
        _log_err("No live Lootable_GoldenChest found. Move near/load the chest and try again.")
        return None

    chest = _find_nearest_golden_chest(chests)
    try:
        instances = getattr(getattr(chest, "ScriptData", None), "Instances", None)
        if instances:
            return instances[0]
    except Exception as e:
        _log_err("Could not read golden chest ScriptData.Instances: %s", e)
        return None

    _log_err("Golden chest found, but no script instance was available: %s", chest)
    return None


def _new_state_key() -> Optional[WrappedStruct]:
    try:
        return WrappedStruct(find_object("ScriptStruct", _STATE_KEY_PATH))
    except Exception as e:
        _log_err("Could not create GbxActorStateMachineStateKey: %s", e)
        return None


def _open_golden_chest() -> None:
    script = _find_golden_chest_script()
    if script is None:
        return
    state_key = _new_state_key()
    if state_key is None:
        return
    try:
        script.Success__OnStateEnabled(state_key, False)
        script.Open__OnStateEnabled(state_key, False)
        _log("Called Success + Open on %s", script)
    except Exception as e:
        _log_err("Open failed: %s", e)


def _close_golden_chest() -> None:
    script = _find_golden_chest_script()
    if script is None:
        return
    try:
        script.DetachUnclaimedLoot()
        _log("Called DetachUnclaimedLoot on %s", script)
    except Exception as e:
        _log_err("DetachUnclaimedLoot failed; continuing close: %s", e)

    def _finish_close() -> None:
        try:
            script.SetScriptStateEnabled("Open", False)
            script.SetScriptStateEnabled("Idle", True)
            _log("Called Open=false + Idle=true on %s", script)
        except Exception as close_e:
            _log_err("Close failed: %s", close_e)

    try:
        threading.Timer(_CLOSE_AFTER_DETACH_DELAY_S, _finish_close).start()
        _log("Scheduled close in %.2fs after detach.", _CLOSE_AFTER_DETACH_DELAY_S)
    except Exception as e:
        _log_err("Could not schedule delayed close; closing now: %s", e)
        _finish_close()


OPEN_GOLDEN_CHEST_KEY = keybind(
    "Open Golden Chest",
    "F8",
    callback=_open_golden_chest,
    display_name="Open Golden Chest",
    description="Calls the golden chest Success + Open script handlers on the nearest live golden chest.",
)

CLOSE_GOLDEN_CHEST_KEY = keybind(
    "Close Golden Chest",
    "F9",
    callback=_close_golden_chest,
    display_name="Close Golden Chest",
    description="Detaches unclaimed loot, disables Open, and re-enables Idle on the nearest live golden chest.",
)
