"""Bridge-safe backend actions for Matt's SDK Boosting Tools.

This module must not import the optional in-game UI. It owns the small bit of
external-bridge state needed by headless bridge actions.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import pkgutil
import re
import sys
import time
from collections import deque
from typing import Any

from mods_base import ENGINE, command, get_pc

from . import player_economy, quick_menu_registry, serial_rewards
from .golden_chest_keybinds import _close_golden_chest, _open_golden_chest
from .inventory_capacity import (
    auto_apply_inventory_sizes_if_needed,
    clamp_container_size,
    load_inventory_settings,
    save_extra_settings,
    set_inventory_sizes_for_all_party,
    set_inventory_sizes_for_party_index,
)
from .dev_tools import activate_devperk as _activate_devperk
from .dev_tools import reset_skills_for_pc as _reset_skills_for_pc
from .dev_tools import copy_debug_cam_location as _copy_debug_cam_location
from .dev_tools import debug_cam_status as _debug_cam_status
from .dev_tools import disable_debug_cam as _disable_debug_cam
from .dev_tools import set_debug_cam_distance as _set_debug_cam_distance
from .dev_tools import set_debug_cam_speed as _set_debug_cam_speed
from .dev_tools import teleport_debug_cam_to_pawn as _teleport_debug_cam_to_pawn
from .dev_tools import teleport_pawn_to_debug_cam as _teleport_pawn_to_debug_cam
from .dev_tools import toggle_debug_cam as _toggle_debug_cam
from .item_pool_spawning import _normalize_spit_direction, spawn_item_pool
from .movement_adjustments import (
    apply_movement_advanced_to_all_players,
    delete_ground_items,
    fire_super_dash,
    get_azzy_super_dash_state,
    get_super_dash_state,
    hide_ground_loot,
    infinite_jump_status,
    pawn_for_controller,
    pull_ground_loot_here,
    refresh_jump_counts_all_players,
    request_azzy_super_dash,
    reset_movement_advanced_all_players,
    set_force_fly,
    set_infinite_jump_all,
    set_infinite_jump_for_index,
    set_no_target,
    set_noclip,
    set_super_dash_strength,
    set_time_dilation,
    teleport_pawn_to_pawn,
    toggle_azzy_super_dash,
    toggle_infinite_jump_for_index,
    toggle_infinite_jump_for_scope,
    toggle_players_only,
    toggle_super_dash,
    zero_vault_power_costs_all_players,
)
from .party_helpers import (
    _gbc_find_pc_for_player_state,
    _gbc_session_world_and_gamestate,
    _kick_party_player_by_index,
    _list_party_players,
)
from .serial_converter import human_to_serial as _human_to_serial, serial_to_human as _serial_to_human
from .shinies import DEFAULT_ITEM_LEVEL as _SHINY_DEFAULT_LEVEL, drop_all_shinies
from .travel import (
    _exec_console,
    delete_location_bookmark as _delete_location_bookmark,
    go_location_bookmark as _go_location_bookmark,
    list_location_bookmarks as _list_location_bookmarks,
    save_location_bookmark as _save_location_bookmark,
    travel_to_map as _travel_to_map,
    travel_to_station as _travel_to_station,
)
from .combat_tuning import (
    apply_combat_tuning as _apply_combat_tuning,
    reapply_combat_tuning as _reapply_combat_tuning,
    reset_combat_tuning as _reset_combat_tuning,
)
from . import streamer_chaos
from . import hoard_runner
from .spawn_helpers import (
    apply_aggro_to_tracked as _apply_aggro_to_tracked,
    get_aggro_mode as _get_aggro_mode,
    get_spawn_anchor as _get_spawn_anchor,
    note_spawned_actors as _note_spawned_actors,
    reaggro_tracked as _reaggro_tracked,
    resolve_spawn_anchor_actor as _resolve_spawn_anchor_actor,
    set_aggro_mode as _set_aggro_mode,
    set_spawn_anchor as _set_spawn_anchor,
)
from .vehicle_tuning import (
    apply_vehicle_preset as _apply_vehicle_preset,
    list_vehicle_catalog as _list_vehicle_catalog,
    list_vehicle_presets as _list_vehicle_presets,
    spawn_personal_vehicle as _spawn_personal_vehicle,
    unlock_all_vehicles_for_pc as _unlock_all_vehicles_for_pc,
)
from . import extreme_combat_xp as _cxp
from . import instant_click_holds as _ich
from . import no_fog_of_war as _nfow

CURRENCY_KINDS = ["cash", "eridium", "vaultcard1", "vaultcard2", "vaultcard3", "vaultcard4"]
EXP_TRACKS = [
    "player",
    "specialization",
    "vaultcard_xp_1",
    "vaultcard_xp_2",
    "vaultcard_xp_3",
    "vaultcard_xp_4",
]
MAX_WALLET_AMOUNT = 2147483647
MAX_PLAYER_LEVEL = 60
MAX_SPEC_LEVEL = 701
MAX_VAULT_CARD_LEVEL = 9999999
RARITY_ROWS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("common", "Common", ("CommonModifier",)),
    ("uncommon", "Uncommon", ("UncommonModifier",)),
    ("rare", "Rare", ("RareModifier",)),
    ("epic", "Epic", ("VeryRareModifier", "EpicModifier")),
    ("legendary", "Legendary", ("LegendaryModifier",)),
    ("pearlescent", "Pearlescent", ("PearlModifier", "PearlescentModifier")),
)

_selected_player_index: int | None = None
_selected_player_name: str = ""
_last_refresh_error: str = ""
# Last runnable command for Quick Menu pin / repeat (bridge-safe, no UI).
_last_command: dict[str, Any] | None = None
_last_drop: dict[str, Any] | None = None
# Option C: optional lock-to-player for repeat-last-drop (skip picker when valid).
_drop_lock_enabled: bool = False
_drop_lock_index: int | None = None
_drop_lock_name: str = ""
serial_text: str = ""
serial_tools_input: str = ""
serial_tools_serialized: str = ""
serial_tools_deserialized: str = ""
serial_tools_parts_breakdown: str = ""
serial_tools_status: str = "Paste a @U serial or deserialized serial text above."
# Last in-game serial read (equipped / backpack). Bridge + QM picker consume this.
_last_read_serials: list[dict[str, Any]] = []
_last_read_serials_title: str = ""
_last_read_serials_clipboard: bool = False
_last_read_serials_dump_paths: list[str] = []
_movement_no_target_enabled = False
_movement_noclip_enabled = False
_movement_force_fly_enabled = False
_rarity_baseline: dict[str, dict[str, float]] = {}

# Research-only challenge introspection. Off by default in shipping builds.
# Set environment MSBT_DEBUG_PROBES=1 to enable bridge/console probe.
ENABLE_CHALLENGE_API_PROBE = os.environ.get("MSBT_DEBUG_PROBES", "").strip().lower() in (
    "1",
    "true",
    "yes",
    "on",
)

def challenge_api_probe_enabled() -> bool:
    return bool(ENABLE_CHALLENGE_API_PROBE)


def _load_rarity_weights_from_settings() -> dict[str, float]:
    """Match BLImGui: restore saved multipliers (and migrate old rarity_disabled flags)."""
    settings = load_inventory_settings()
    saved = dict(settings.get("rarity_weights", {}) or {})
    old_disabled = dict(settings.get("rarity_disabled", {}) or {})
    weights: dict[str, float] = {}
    for key, _label, _fields in RARITY_ROWS:
        if key in saved:
            try:
                val = float(saved.get(key, 1.0))
            except Exception:
                val = 1.0
        else:
            val = 0.0 if bool(old_disabled.get(key, False)) else 1.0
        weights[key] = max(0.0, min(1.0, float(val)))
    return weights


_rarity_weights: dict[str, float] = _load_rarity_weights_from_settings()
_rarity_revision: int = 0
UVH_RANKS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "UVH 1",
        (
            "Challenge_UVH_Rankup_1_Firmware",
            "Challenge_UVH_Rankup_1_BMVM",
            "Challenge_UVH_Rankup_1_TrueBoss",
            "UVH_Rankup_1_FinalChallenge",
        ),
    ),
    (
        "UVH 2",
        (
            "Challenge_UVH_Rankup_2_Kratch",
            "Challenge_UVH_Rankup_2_Creep",
            "Challenge_UVH_Rankup_2_Order",
            "Challenge_UVH_Rankup_2_Ripper",
            "UVH_Rankup_2_FinalChallenge",
        ),
    ),
    (
        "UVH 3",
        (
            "Challenge_UVH_Rankup_3_Cat",
            "Challenge_UVH_Rankup_3_Pangolin",
            "Challenge_UVH_Rankup_3_Order",
            "Challenge_UVH_Rankup_3_Ripper",
            "UVH_Rankup_3_FinalChallenge",
        ),
    ),
    (
        "UVH 4",
        (
            "Challenge_UVH_Rankup_4_Beast",
            "Challenge_UVH_Rankup_4_Order",
            "Challenge_UVH_Rankup_4_Ripper",
            "Challenge_UVH_Rankup_4_Thresher",
            "UVH_Rankup_4_FinalChallenge",
        ),
    ),
    (
        "UVH 5",
        (
            "Challenge_UVH_Rankup_5_GL",
            "Challenge_UVH_Rankup_5_MOU",
            "Challenge_UVH_Rankup_5_SL",
            "UVH_Rankup_5_FinalChallenge",
        ),
    ),
    ("UVH 6", ("Challenge_UVH_Rankup_6_Bloomreaper",)),
    ("UVH 7", ("Challenge_UVH_Rankup_7_Parent",)),
)
_UVH_NORMAL_STEP_DELAY_SECONDS = 0.30
_UVH_PRE_FINAL_DELAY_SECONDS = 0.30
_UVH_TIER_ACTIVATION_DELAY_SECONDS = 0.30
_uvh_queue: deque[tuple[str, str, float]] = deque()
_uvh_targets: list[Any] = []
_uvh_next_at = 0.0
_uvh_running = False
_uvh_paused_queue: deque[tuple[str, str, float]] = deque()
_uvh_paused_targets: list[Any] = []
_uvh_last_status = "Ready. UVH tier boosts are based on Azzy UVH Booster by Azalea Asvail."
_DEV_SPAWNER_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_./:-]+$")
_DEV_SPAWNER_SAFE_STATE_LIST = re.compile(r"^[A-Za-z0-9_,./:-]+$")
_ASD_COMMAND_ATTRS = {
    "ASD_status": "_cmd_status",
    "ASD_clear": "_cmd_clear",
    "ASD_activate_last": "_cmd_activate_last",
    "ASD_scriptdump": "_cmd_scriptdump",
    "ASD_cache_status": "_cmd_cache_status",
    "ASD_targets": "_cmd_targets",
    "ASD_spawn": "_cmd_spawn",
    "ASD_lostloot": "_cmd_lostloot",
    "ASD_spawnai": "_cmd_spawnai",
    "ASD_probeai": "_cmd_probeai",
    "ASD_cache": "_cmd_cache",
    "ASD_barrellogo": "_cmd_barrellogo",
    "ASD_logo_options": "_cmd_logo_options",
    "ASD_spawnerdiag": "_cmd_spawnerdiag",
}
# ASD auto-clear used fixed batch windows: first spawn opened a batch, and at the
# end of the window we fired ASD_clear.
#
# That is off now (0 disables it). ASD_clear walks _CREATED_SPAWNERS and calls
# GetSpawnerComponent / SetActive / ResetSpawner / K2_DestroyActor on every entry
# with no "is this actor still alive" pre-check, so it happily reaches into
# spawners that are already gone. Firing that on a timer, unattended, minutes into
# a hoard, is exactly the kind of unsupervised destruction that has now crashed
# the game three times. Clearing is the user's Clear button only.
_ASD_BATCH_WINDOW_S = 0.0
_asd_batch_start = 0.0
_asd_batch_clear_due = 0.0
_asd_batch_armed = False


def _asd_note_spawn_for_autoclear() -> None:
    global _asd_batch_start, _asd_batch_clear_due, _asd_batch_armed
    if float(_ASD_BATCH_WINDOW_S) <= 0.0:
        return
    now = time.monotonic()
    if not _asd_batch_armed:
        _asd_batch_start = now
        _asd_batch_clear_due = now + float(_ASD_BATCH_WINDOW_S)
        _asd_batch_armed = True
        return
    # Still inside the current collection window — leave the clear time alone.
    if now <= float(_asd_batch_clear_due):
        return
    if _asd_autoclear_should_wait():
        # A hoard wave owns these actors; wiping them here would both delete the
        # fight in progress and destroy actors the engine is still finishing.
        _asd_batch_start = now
        _asd_batch_clear_due = now + float(_ASD_BATCH_WINDOW_S)
        return
    # Past the window: clear the prior wave now, then open a new batch for this spawn.
    try:
        ok, msg = _run_actor_script_deployer_command("ASD_clear")
        try:
            from unrealsdk import logging as _ulog

            _ulog.info(
                f"[Matts SDK Boosting Tools | DevSpawner] Closed ASD batch on late spawn "
                f"(ok={ok}): {msg}"
            )
        except Exception:
            pass
    except Exception:
        pass
    _asd_batch_start = now
    _asd_batch_clear_due = now + float(_ASD_BATCH_WINDOW_S)
    _asd_batch_armed = True


def _asd_disarm_autoclear() -> None:
    global _asd_batch_armed, _asd_batch_clear_due, _asd_batch_start
    _asd_batch_armed = False
    _asd_batch_clear_due = 0.0
    _asd_batch_start = 0.0


def _asd_autoclear_should_wait() -> bool:
    """Hold the batch clear while the hoard runner still owns live actors.

    ASD_clear destroys every tracked spawner and actor. Firing that mid-wave —
    or in the frame a wave just died — races the engine's own death handling.
    """
    try:
        if hoard_runner._spawn_in_flight or hoard_runner._spawn_phase:
            return True
        if hoard_runner._running:
            return True
        if hoard_runner.cleanup_pending():
            return True
    except Exception:
        return False
    return False


def tick_asd_autoclear() -> None:
    """Clear one ASD spawn batch when its window ends."""
    global _asd_batch_armed, _asd_batch_clear_due
    if not _asd_batch_armed or float(_ASD_BATCH_WINDOW_S) <= 0.0:
        return
    now = time.monotonic()
    if now < float(_asd_batch_clear_due):
        return
    if _asd_autoclear_should_wait():
        _asd_batch_clear_due = now + 2.0
        return
    ok = False
    msg = "ASD auto-clear skipped"
    try:
        ok, msg = _run_actor_script_deployer_command("ASD_clear")
        try:
            note_last_command(
                "dev_spawner_clear",
                label="Auto Clear ASD Spawns (batch)",
                payload={},
                is_drop=False,
                needs_player=False,
            )
        except Exception:
            pass
    except Exception as exc:
        ok, msg = False, f"ASD auto-clear failed: {exc!r}"
    try:
        from unrealsdk import logging as _ulog

        _ulog.info(
            f"[Matts SDK Boosting Tools | DevSpawner] Auto-cleared ASD batch "
            f"({int(_ASD_BATCH_WINDOW_S)}s window, ok={ok}): {msg}"
        )
    except Exception:
        pass
    _asd_disarm_autoclear()


def _clamp_int(value: object, min_value: int, max_value: int) -> int:
    return max(int(min_value), min(int(value), int(max_value)))


def _clamp_float(value: object, min_value: float, max_value: float, default: float) -> float:
    try:
        fvalue = float(str(value).replace(",", "").strip())
    except Exception:
        fvalue = default
    return max(min_value, min(max_value, fvalue))


def _dev_spawner_bool(value: object) -> bool:
    return str(value or "").strip().lower() in ("1", "true", "yes", "on", "checked")


def _dev_spawner_token(value: object, field_name: str, *, required: bool = False) -> str:
    text = str(value or "").strip()
    if not text:
        if required:
            raise ValueError(f"{field_name} is required.")
        return ""
    if not _DEV_SPAWNER_SAFE_TOKEN.match(text):
        raise ValueError(f"{field_name} contains unsupported characters for a dev-spawner console argument.")
    return text


def _dev_spawner_state_list(value: object, field_name: str) -> str:
    text = str(value or "").strip().replace(" ", "")
    if not text:
        return ""
    if not _DEV_SPAWNER_SAFE_STATE_LIST.match(text):
        raise ValueError(f"{field_name} contains unsupported characters for a dev-spawner state list.")
    return text


def _dev_spawner_quoted_text(value: object) -> str:
    text = str(value or "").replace("\r\n", "|").replace("\r", "|").replace("\n", "|").strip()
    # Keep this as a single ASD argument. Semicolons are removed to avoid accidental console chaining.
    text = text.replace(";", ",").replace('"', "'")
    return f'"{text}"'


def _run_actor_script_deployer_command(command_line: str) -> tuple[bool, str]:
    """Run an ActorScriptDeployer mods_base command without going through Unreal console text."""
    command_name = str(command_line or "").split(None, 1)[0]
    attr_name = _ASD_COMMAND_ATTRS.get(command_name)
    if not attr_name:
        return False, f"No ActorScriptDeployer mapping for {command_name!r}."
    try:
        asd = importlib.import_module("ActorScriptDeployer")
    except Exception as exc:
        return False, f"ActorScriptDeployer import failed: {exc!r}"
    patch_ok, patch_message = _install_asd_spawn_runtime_patches(asd)
    if not patch_ok:
        return False, patch_message
    command_obj = getattr(asd, attr_name, None)
    handle = getattr(command_obj, "_handle_cmd", None)
    if not callable(handle):
        return False, f"ActorScriptDeployer command object {attr_name!r} is unavailable."
    handle(command_line, len(command_name))
    return True, f"ActorScriptDeployer command object; {patch_message}"


def _actor_script_deployer_command(attr_name: str) -> tuple[Any | None, str]:
    try:
        asd = importlib.import_module("ActorScriptDeployer")
    except Exception as exc:
        return None, f"ActorScriptDeployer import failed: {exc!r}"
    command_obj = getattr(asd, attr_name, None)
    if not callable(command_obj):
        return None, f"ActorScriptDeployer command object {attr_name!r} is unavailable."
    return command_obj, "ActorScriptDeployer direct command object"


def _install_asd_sdk03_actor_def_patch(asd: Any) -> tuple[bool, str]:
    if getattr(asd, "_msbt_sdk03_actor_def_patch", False):
        return True, "ActorScriptDeployer SDK 03 actor-def pointer patch already installed"

    original = getattr(asd, "_make_actor_def_shell", None)
    if not callable(original):
        return True, "ActorScriptDeployer actor-def shell helper not present; SDK 03 patch not needed"

    def _make_actor_def_shell_sdk03(actor_def: str) -> Any:
        name = str(actor_def or "").strip()
        if not name:
            raise ValueError("ActorScriptDeployer SDK 03 actor-def pointer requires a non-empty actor name.")

        try:
            import unrealsdk as _unrealsdk
        except Exception as exc:
            raise RuntimeError(f"ActorScriptDeployer SDK 03 actor-def pointer could not import unrealsdk: {exc!r}") from exc

        struct = None
        find_object_fn = getattr(asd, "find_object", None)
        if callable(find_object_fn):
            for class_name in ("ScriptStruct", "Object"):
                try:
                    struct = find_object_fn(class_name, "/Script/GbxSpawn.GbxActorDef")
                except Exception:
                    struct = None
                if struct is not None:
                    break

        struct_arg = struct or "/Script/GbxSpawn.GbxActorDef"
        try:
            return _unrealsdk.unreal.FGbxDefPtr(name, struct_arg)
        except Exception as exc:
            raise RuntimeError(
                "ActorScriptDeployer SDK 03 actor-def pointer failed: "
                f"FGbxDefPtr({name!r}, {struct_arg!r}) -> {exc!r}"
            ) from exc

    try:
        setattr(asd, "_msbt_original_make_actor_def_shell", original)
        setattr(asd, "_make_actor_def_shell", _make_actor_def_shell_sdk03)
        setattr(asd, "_msbt_sdk03_actor_def_patch", True)
    except Exception as exc:
        return False, f"ActorScriptDeployer SDK 03 actor-def pointer patch failed: {exc!r}"

    return True, "ActorScriptDeployer SDK 03 actor-def pointer patch installed: FGbxDefPtr(name, GbxActorDef)"


def _install_asd_nonblocking_spawn_poll_patch(asd: Any) -> tuple[bool, str]:
    """Safety net: force ASD spawn verification onto the non-blocking protocol.

    Newer ActorScriptDeployer builds default ``_poll_spawner_for_alive_actors`` to
    a one-shot check and disable world-wide ``find_all("Actor")`` scans. Older
    ASD installs still sleep (~0.75–3s) and snapshot the whole actor list on the
    Unreal tick queue, which freezes BL4.

    Always install this patch so MSBT spawn paths (ASD_spawnai / ASD_spawn /
    ASD_lostloot / ASD_barrellogo / cache) stay hitch-free even on older ASD.
    Spawns may return queued_unverified when actors are not immediately alive.
    """
    if getattr(asd, "_msbt_nonblocking_spawn_poll_patch", False):
        return True, "ActorScriptDeployer non-blocking spawn poll patch already installed"

    notes: list[str] = []

    original_poll = getattr(asd, "_poll_spawner_for_alive_actors", None)
    if callable(original_poll):
        alive_fn = getattr(asd, "_alive_actors_for_spawner_component", None)

        def _poll_spawner_for_alive_actors_nonblocking(
            comp: Any,
            *,
            timeout: float = 0.0,
            interval: float = 0.15,
        ) -> list[Any]:
            del timeout, interval  # MSBT never blocks the tick thread waiting.
            if not callable(alive_fn):
                return []
            try:
                actors = alive_fn(comp)
            except Exception:
                return []
            return list(actors or [])

        try:
            setattr(asd, "_msbt_original_poll_spawner_for_alive_actors", original_poll)
            setattr(asd, "_poll_spawner_for_alive_actors", _poll_spawner_for_alive_actors_nonblocking)
            notes.append("poll=once-no-sleep")
        except Exception as exc:
            return False, f"ActorScriptDeployer non-blocking spawn poll patch failed: {exc!r}"
    else:
        notes.append("poll=missing")

    original_snapshot = getattr(asd, "_world_actor_snapshot", None)
    if callable(original_snapshot):
        def _world_actor_snapshot_skip() -> set[str]:
            return set()

        try:
            setattr(asd, "_msbt_original_world_actor_snapshot", original_snapshot)
            setattr(asd, "_world_actor_snapshot", _world_actor_snapshot_skip)
            notes.append("world-snapshot=skipped")
        except Exception as exc:
            return False, f"ActorScriptDeployer world-snapshot skip patch failed: {exc!r}"
    else:
        notes.append("world-snapshot=missing")

    original_delta = getattr(asd, "_find_new_world_actors_near", None)
    if callable(original_delta):
        def _find_new_world_actors_near_skip(*_args: Any, **_kwargs: Any) -> list[Any]:
            return []

        try:
            setattr(asd, "_msbt_original_find_new_world_actors_near", original_delta)
            setattr(asd, "_find_new_world_actors_near", _find_new_world_actors_near_skip)
            notes.append("world-delta=skipped")
        except Exception as exc:
            return False, f"ActorScriptDeployer world-delta skip patch failed: {exc!r}"
    else:
        notes.append("world-delta=missing")

    # Also force the ASD module flag off when present (native protocol gate).
    if hasattr(asd, "_SPAWN_ALLOW_WORLD_ACTOR_SCAN"):
        try:
            setattr(asd, "_msbt_original_spawn_allow_world_actor_scan", getattr(asd, "_SPAWN_ALLOW_WORLD_ACTOR_SCAN"))
            setattr(asd, "_SPAWN_ALLOW_WORLD_ACTOR_SCAN", False)
            notes.append("world-scan-flag=off")
        except Exception:
            notes.append("world-scan-flag=unpatched")

    try:
        setattr(asd, "_msbt_nonblocking_spawn_poll_patch", True)
    except Exception as exc:
        return False, f"ActorScriptDeployer non-blocking spawn poll patch flag failed: {exc!r}"

    return True, "ActorScriptDeployer non-blocking spawn poll patch installed: " + ", ".join(notes)


def _install_asd_clear_spawners_patch(asd: Any) -> tuple[bool, str]:
    """Ensure ASD_clear disables/destroys throwaway OakSpawners, not only tracked actors.

    Heavy ASD_spawnai runs leave enabled disposable OakSpawners behind. Killing
    spawned enemies is not enough — those spawners keep restocking. Bundle ASD
    already clears them; this patch covers older folder installs.
    """
    if getattr(asd, "_msbt_clear_spawners_patch", False):
        return True, "ActorScriptDeployer clear-spawners patch already installed"

    if not hasattr(asd, "_CREATED_SPAWNERS"):
        try:
            setattr(asd, "_CREATED_SPAWNERS", [])
        except Exception as exc:
            return False, f"ActorScriptDeployer clear-spawners patch could not create tracker: {exc!r}"

    original_deferred = getattr(asd, "_spawn_actor_deferred", None)
    if callable(original_deferred) and not getattr(asd, "_msbt_track_created_spawners", False):
        def _spawn_actor_deferred_tracked(
            gs: Any,
            world: Any,
            cls: Any,
            transform: Any,
            *,
            class_name: str = "Actor",
            source: Any = None,
            collision_handling: int = 1,
        ) -> Any:
            spawned = original_deferred(
                gs,
                world,
                cls,
                transform,
                class_name=class_name,
                source=source,
                collision_handling=collision_handling,
            )
            if spawned is not None and str(class_name) == "OakSpawner":
                track = getattr(asd, "_track_created_spawner", None)
                if callable(track):
                    try:
                        track(spawned)
                    except Exception:
                        pass
                else:
                    try:
                        created = getattr(asd, "_CREATED_SPAWNERS", None)
                        if isinstance(created, list):
                            created.append(spawned)
                    except Exception:
                        pass
            return spawned

        try:
            setattr(asd, "_msbt_original_spawn_actor_deferred", original_deferred)
            setattr(asd, "_spawn_actor_deferred", _spawn_actor_deferred_tracked)
            setattr(asd, "_msbt_track_created_spawners", True)
        except Exception as exc:
            return False, f"ActorScriptDeployer clear-spawners spawn tracker patch failed: {exc!r}"

    # If this ASD build already ships the full clear helper, keep it and only
    # ensure the tracker flag is set.
    if callable(getattr(asd, "_disable_and_destroy_spawner", None)) and callable(
        getattr(asd, "_collect_tracked_spawners", None)
    ):
        try:
            setattr(asd, "_msbt_clear_spawners_patch", True)
        except Exception as exc:
            return False, f"ActorScriptDeployer clear-spawners patch flag failed: {exc!r}"
        return True, "ActorScriptDeployer clear-spawners patch installed: native disable/destroy helpers present"

    original_clear = getattr(asd, "_clear_spawned_actors", None)
    if not callable(original_clear):
        return False, "ActorScriptDeployer clear-spawners patch failed: _clear_spawned_actors missing"

    safe_set = getattr(asd, "_safe_set_attr", None)
    alive_fn = getattr(asd, "_alive_actors_for_spawner_component", None)
    safe_key = getattr(asd, "_safe_actor_key", None)
    log_info = getattr(asd, "_log_info", None)
    log_warn = getattr(asd, "_log_warn", None)
    spawned_list = getattr(asd, "_SPAWNED", None)

    def _collect_spawners() -> list[Any]:
        spawners: list[Any] = []
        seen: set[str] = set()
        refs: list[Any] = []

        def _add(candidate: Any) -> None:
            if candidate is None:
                return
            key = ""
            if callable(safe_key):
                try:
                    key = str(safe_key(candidate) or "")
                except Exception:
                    key = ""
            if key:
                if key in seen:
                    return
                seen.add(key)
            else:
                if any(existing is candidate for existing in refs):
                    return
                refs.append(candidate)
            spawners.append(candidate)

        if isinstance(spawned_list, list):
            for item in list(spawned_list):
                _add(getattr(item, "source", None))
        created = getattr(asd, "_CREATED_SPAWNERS", None)
        if isinstance(created, list):
            for spawner in list(created):
                _add(spawner)
        return spawners

    def _disable_and_destroy_spawner(spawner: Any) -> tuple[int, int]:
        actors_destroyed = 0
        spawner_destroyed = 0
        comp = None
        try:
            comp = spawner.GetSpawnerComponent()
        except Exception:
            comp = None
        if comp is not None:
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
                except TypeError:
                    try:
                        fn()
                    except Exception:
                        pass
                except Exception:
                    pass
            if callable(safe_set):
                for field in (
                    "bSpawnerEnabled",
                    "bSpawnPointEnabled",
                    "bEnabled",
                    "bActive",
                    "bCanSpawn",
                    "bAllowSpawn",
                    "bAllowRespawn",
                    "bRespawnEnabled",
                    "bInfinite",
                    "bUnlimitedSpawns",
                ):
                    try:
                        safe_set(comp, field, False)
                    except Exception:
                        pass
            if callable(alive_fn):
                try:
                    for actor in list(alive_fn(comp) or []):
                        try:
                            if bool(getattr(actor, "bActorIsBeingDestroyed", False)):
                                continue
                        except Exception:
                            pass
                        try:
                            actor.K2_DestroyActor()
                            actors_destroyed += 1
                        except Exception:
                            pass
                except Exception:
                    pass
            try:
                comp.ResetSpawner(False)
            except TypeError:
                try:
                    comp.ResetSpawner()
                except Exception:
                    pass
            except Exception:
                pass
        try:
            if bool(getattr(spawner, "bActorIsBeingDestroyed", False)):
                return actors_destroyed, 0
        except Exception:
            pass
        try:
            spawner.K2_DestroyActor()
            spawner_destroyed = 1
        except Exception as exc:
            if callable(log_warn):
                try:
                    log_warn(f"MSBT clear could not destroy spawner {spawner}: {exc}")
                except Exception:
                    pass
        return actors_destroyed, spawner_destroyed

    def _clear_spawned_actors_msbt() -> int:
        destroyed = 0
        spawners_destroyed = 0
        for spawner in _collect_spawners():
            actors_from_spawner, spawner_gone = _disable_and_destroy_spawner(spawner)
            destroyed += int(actors_from_spawner)
            spawners_destroyed += int(spawner_gone)
        try:
            destroyed += int(original_clear() or 0)
        except Exception:
            pass
        created = getattr(asd, "_CREATED_SPAWNERS", None)
        if isinstance(created, list):
            created.clear()
        if spawners_destroyed and callable(log_info):
            try:
                log_info(f"MSBT clear destroyed {spawners_destroyed} throwaway OakSpawner(s).")
            except Exception:
                pass
        return destroyed

    try:
        setattr(asd, "_msbt_original_clear_spawned_actors", original_clear)
        setattr(asd, "_clear_spawned_actors", _clear_spawned_actors_msbt)
        setattr(asd, "_msbt_clear_spawners_patch", True)
    except Exception as exc:
        return False, f"ActorScriptDeployer clear-spawners patch failed: {exc!r}"

    return True, "ActorScriptDeployer clear-spawners patch installed: disable/destroy throwaway OakSpawners"


def _install_asd_spawn_runtime_patches(asd: Any) -> tuple[bool, str]:
    """Install all MSBT-side ActorScriptDeployer runtime patches used for spawns."""
    messages: list[str] = []
    for installer in (
        _install_asd_sdk03_actor_def_patch,
        _install_asd_nonblocking_spawn_poll_patch,
        _install_asd_clear_spawners_patch,
    ):
        ok, message = installer(asd)
        messages.append(message)
        if not ok:
            return False, message
    return True, "; ".join(messages)


_ASD_LOG_WINDOW_S = 10.0
_ASD_LOG_MAX_INFO_PER_WINDOW = 10
_ASD_LOG_MAX_PROBLEM_PER_WINDOW = 30
_ASD_LOG_DUPLICATE_WINDOW_S = 5.0
_ASD_LOG_DIGITS = re.compile(r"(0x)?[0-9a-fA-F]{3,}|\d+")
_asd_log_window_start = 0.0
_asd_log_forwarded: dict[str, int] = {"info": 0, "problem": 0}
_asd_log_suppressed = 0
_asd_log_signatures: dict[str, float] = {}


def _asd_log_signature(text: str) -> str:
    """Collapse actor names/addresses/counters so repeats share one signature."""
    return _ASD_LOG_DIGITS.sub("#", str(text))[:160]


def _asd_log_should_forward(level: str, text: str) -> bool:
    """Rate limit ActorScriptDeployer chatter without silencing real problems.

    ASD emitted ~835 lines/minute during a paced hoard. Warnings and errors still
    get through (that is how spawn failures stay diagnosable); only repeats and
    routine info lines are dropped.
    """
    global _asd_log_window_start, _asd_log_suppressed
    now = time.monotonic()
    if now - _asd_log_window_start > _ASD_LOG_WINDOW_S:
        dropped = _asd_log_suppressed
        _asd_log_window_start = now
        _asd_log_forwarded["info"] = 0
        _asd_log_forwarded["problem"] = 0
        _asd_log_suppressed = 0
        _asd_log_signatures.clear()
        if dropped > 0:
            try:
                from unrealsdk import logging as _ulog

                _ulog.info(
                    f"[Matts SDK Boosting Tools | ASD] throttled {dropped} repeated "
                    "ActorScriptDeployer log line(s)."
                )
            except Exception:
                pass

    bucket = "info" if level == "info" else "problem"
    signature = f"{bucket}:{_asd_log_signature(text)}"
    seen_at = _asd_log_signatures.get(signature)
    if seen_at is not None and now - seen_at < _ASD_LOG_DUPLICATE_WINDOW_S:
        _asd_log_suppressed += 1
        return False
    cap = _ASD_LOG_MAX_INFO_PER_WINDOW if bucket == "info" else _ASD_LOG_MAX_PROBLEM_PER_WINDOW
    if _asd_log_forwarded[bucket] >= cap:
        _asd_log_suppressed += 1
        return False
    _asd_log_signatures[signature] = now
    _asd_log_forwarded[bucket] += 1
    return True


def _capture_asd_logs(
    asd: Any,
    callback: Any,
    *,
    forward: bool = True,
    throttle: bool = False,
) -> tuple[list[tuple[str, str]], Exception | None]:
    logs: list[tuple[str, str]] = []
    originals = {
        "_log_info": getattr(asd, "_log_info", None),
        "_log_warn": getattr(asd, "_log_warn", None),
        "_log_error": getattr(asd, "_log_error", None),
    }

    def _wrap(level: str, original: Any) -> Any:
        def _logger(message: str) -> None:
            text = str(message)
            logs.append((level, text))
            if not forward or not callable(original):
                return
            if throttle and not _asd_log_should_forward(level, text):
                return
            original(message)

        return _logger

    for attr, original in originals.items():
        level = "info"
        if attr.endswith("warn"):
            level = "warning"
        elif attr.endswith("error"):
            level = "error"
        try:
            setattr(asd, attr, _wrap(level, original))
        except Exception:
            pass

    error: Exception | None = None
    try:
        callback()
    except Exception as exc:
        error = exc
    finally:
        for attr, original in originals.items():
            try:
                setattr(asd, attr, original)
            except Exception:
                pass
    return logs, error


def _parse_asd_spawnai_result(
    *,
    name: str,
    requested_count: int,
    mode: str,
    logs: list[tuple[str, str]],
    error: Exception | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "message": "",
        "mode": mode,
        "requested_count": int(requested_count),
        "verification_status": "unknown",
        "spawn_verified": None,
        "resolved": None,
        "spawned_count": None,
        "alive_count": None,
        "dead_count": None,
        "total_count": None,
        "actor_names": [],
        "warnings": [],
        "asd_log_lines": [message for _level, message in logs],
    }
    if error is not None:
        result["message"] = f"ActorScriptDeployer ASD_spawnai failed: {error!r}"
        return result

    actor_names: list[str] = []
    warnings: list[str] = [
        message
        for level, message in logs
        if level in ("warning", "error")
        or "did not return an actor" in message
        or "no alive actors" in message
        or "resolved=False" in message
    ]
    count_pattern = re.compile(
        r"ASD_spawnai thin-air actor_def=(?P<actor_def>\S+) resolved=(?P<resolved>True|False).*?"
        r"counts=\(alive=(?P<alive>-?\d+), spawned=(?P<spawned>-?\d+), dead=(?P<dead>-?\d+), total=(?P<total>-?\d+)\) "
        r"actors=(?P<actors>\[.*\])"
    )
    complete_pattern = re.compile(r"ASD_spawnai complete:\s*(?P<actor>.+)$")

    for _level, message in logs:
        count_match = count_pattern.search(message)
        if count_match:
            result["resolved"] = count_match.group("resolved") == "True"
            result["alive_count"] = int(count_match.group("alive"))
            result["spawned_count"] = int(count_match.group("spawned"))
            result["dead_count"] = int(count_match.group("dead"))
            result["total_count"] = int(count_match.group("total"))
            actors_text = count_match.group("actors").strip()
            if actors_text and actors_text != "[]":
                actor_names.append(actors_text)
            continue

        complete_match = complete_pattern.search(message)
        if complete_match:
            actor_names.append(complete_match.group("actor").strip())

    result["warnings"] = warnings
    result["actor_names"] = actor_names

    resolved = result.get("resolved")
    alive_count = result.get("alive_count")
    spawned_count = result.get("spawned_count")
    saw_complete = bool(actor_names)
    no_actor_warning = any(
        "did not return an actor" in warning or "no alive actors" in warning
        for warning in warnings
    )

    if resolved is False:
        result["ok"] = True
        result["verification_status"] = "queued_unverified"
        result["message"] = (
            f"ActorScriptDeployer accepted ASD_spawnai for {name}, but the immediate poll did not verify the actor. "
            "Watch the game world; some ActorScriptDeployer spawns finish after this response."
        )
        return result
    if alive_count == 0 and spawned_count == 0:
        result["ok"] = True
        result["verification_status"] = "queued_unverified"
        result["message"] = (
            f"ActorScriptDeployer accepted ASD_spawnai for {name}, but the immediate poll reported 0 spawned/alive actors. "
            "Watch the game world; some ActorScriptDeployer spawns finish after this response."
        )
        return result
    if no_actor_warning and not saw_complete:
        result["ok"] = True
        result["verification_status"] = "queued_unverified"
        result["message"] = (
            f"ActorScriptDeployer accepted ASD_spawnai for {name}, but did not return an actor immediately. "
            "Watch the game world; some ActorScriptDeployer spawns finish after this response."
        )
        return result
    if saw_complete or (resolved is True and (int(alive_count or 0) > 0 or int(spawned_count or 0) > 0)):
        result["ok"] = True
        result["verification_status"] = "verified_spawned"
        result["spawn_verified"] = True
        result["message"] = f"ActorScriptDeployer spawned {name}."
        return result

    result["verification_status"] = "unknown"
    result["message"] = (
        f"ActorScriptDeployer received ASD_spawnai for {name}, but MSBT could not verify a spawned actor from "
        "the immediate command output."
    )
    return result


def _run_actor_script_deployer_spawnai_like_debug_menu(
    *,
    name: str,
    count: int,
    distance: float,
    spacing: float,
    scale: float,
    z_offset: float,
    extra_loads: list[str],
    direct_only: bool,
    angle_degrees: float = 0.0,
) -> dict[str, Any]:
    """Run ActorScriptDeployer's native AI spawn command for standard row spawns.

    `angle_degrees` is accepted for call-site compatibility and ignored. Honouring
    it required replacing ActorScriptDeployer's `_spawn_transform_for_index` for
    the duration of the call, i.e. mutating a third-party module while its native
    spawn and deferred-actor code ran on a tick that can re-enter us. ASD has no
    bearing argument, so directional placement is gone rather than patched.
    """
    try:
        asd = importlib.import_module("ActorScriptDeployer")
    except Exception as exc:
        return {"ok": False, "message": f"ActorScriptDeployer import failed: {exc!r}", "requested_count": count}

    patch_ok, patch_message = _install_asd_spawn_runtime_patches(asd)
    if not patch_ok:
        return {"ok": False, "message": patch_message, "requested_count": count}

    spawnai_fn = getattr(asd, "_cmd_spawnai", None)
    if not callable(spawnai_fn):
        return {
            "ok": False,
            "message": "ActorScriptDeployer command object '_cmd_spawnai' is unavailable.",
            "requested_count": count,
        }
    message = f"ActorScriptDeployer direct command object; {patch_message}"

    def _spawn_first() -> None:
        spawnai_fn(
            argparse.Namespace(
                name=name,
                distance=distance,
                count=count,
                spacing=spacing,
                scale=scale,
                z_offset=z_offset,
                zoffset=z_offset,
                load=list(extra_loads),
                direct_only=direct_only,
            )
        )

    logs, error = _capture_asd_logs(asd, _spawn_first, throttle=True)
    result = _parse_asd_spawnai_result(
        name=name,
        requested_count=count,
        mode=message,
        logs=logs,
        error=error,
    )
    return result


def _module_available(name: str) -> bool:
    try:
        if name in sys.modules:
            return True
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def _module_version(name: str) -> str:
    try:
        module = sys.modules.get(name) or importlib.import_module(name)
    except Exception:
        return ""
    for attr in ("__version__", "VERSION", "version"):
        try:
            value = getattr(module, attr, "")
        except Exception:
            value = ""
        if value:
            return str(value)
    return ""


_SDK_DIAGNOSTICS_TTL_SECONDS = 30.0
_sdk_diagnostics_cache: dict[str, Any] | None = None
_sdk_diagnostics_cached_at = 0.0


def _sdk_diagnostics(refresh: bool = False) -> dict[str, Any]:
    """Lightweight SDK/runtime status for the external bridge.

    Keep this best-effort only: diagnostics should never block startup or action
    processing if an optional module is missing or an SDK build hides version
    metadata.
    """
    global _sdk_diagnostics_cache, _sdk_diagnostics_cached_at
    now = time.monotonic()
    if (
        not refresh
        and _sdk_diagnostics_cache is not None
        and now - _sdk_diagnostics_cached_at < _SDK_DIAGNOSTICS_TTL_SECONDS
    ):
        return dict(_sdk_diagnostics_cache)
    try:
        py_version = sys.version.split()[0]
    except Exception:
        py_version = ""
    try:
        from . import __version__ as msbt_mod_version
    except Exception:
        msbt_mod_version = ""
    result = {
        "msbt_loaded": True,
        "msbt_mod_version": str(msbt_mod_version or ""),
        "python_version": py_version,
        "mods_base_version": _module_version("mods_base"),
        "unrealsdk_version": _module_version("unrealsdk"),
        "pyunrealsdk_version": _module_version("pyunrealsdk"),
        "blimgui_available": _module_available("blimgui"),
        "actor_script_deployer_available": _module_available("ActorScriptDeployer"),
    }
    _sdk_diagnostics_cache = result
    _sdk_diagnostics_cached_at = now
    return dict(result)


def clear_uobject_caches() -> None:
    """Release cached UObject controller references before travel/unload."""
    _uvh_targets.clear()
    _challenge_targets.clear()


def _max_level_for_track(track: object) -> int:
    try:
        track_index = int(track)
    except Exception:
        key = str(track or "").strip().lower()
        track_index = EXP_TRACKS.index(key) if key in EXP_TRACKS else 0
    if track_index == 0:
        return MAX_PLAYER_LEVEL
    if track_index == 1:
        return MAX_SPEC_LEVEL
    return MAX_VAULT_CARD_LEVEL


def _kind_from_input(kind_or_index: object) -> str | None:
    raw = str(kind_or_index or "").strip().lower()
    try:
        idx = int(raw)
        if 0 <= idx < len(CURRENCY_KINDS):
            return CURRENCY_KINDS[idx]
    except Exception:
        pass
    if raw in CURRENCY_KINDS:
        return raw
    return None


def _track_from_input(track_or_index: object) -> str | None:
    raw = str(track_or_index or "").strip().lower()
    try:
        idx = int(raw)
        if 0 <= idx < len(EXP_TRACKS):
            return EXP_TRACKS[idx]
    except Exception:
        pass
    if raw in EXP_TRACKS:
        return raw
    return None


def _players() -> list[tuple[int, str]]:
    try:
        return [(int(idx), str(name)) for idx, name in _list_party_players()]
    except Exception as exc:
        global _last_refresh_error
        _last_refresh_error = repr(exc)
        return []


def _player_name_key(name: object) -> str:
    return str(name or "").strip().casefold()


def _find_player_by_exact_name(players: list[tuple[int, str]], name: object) -> tuple[int, str] | None:
    key = _player_name_key(name)
    if not key:
        return None
    for idx, player_name in players:
        if _player_name_key(player_name) == key:
            return idx, player_name
    return None


def refresh_players() -> list[dict[str, Any]]:
    """Refresh and return the current party player list."""
    global _selected_player_index, _selected_player_name, _last_refresh_error
    _last_refresh_error = ""
    players = _players()
    if players:
        name_match = _find_player_by_exact_name(players, _selected_player_name)
        if name_match is not None:
            _selected_player_index, _selected_player_name = name_match
        elif _selected_player_name:
            _selected_player_index = None
            _selected_player_name = ""
        elif _selected_player_index is not None and any(idx == _selected_player_index for idx, _name in players):
            for idx, name in players:
                if idx == _selected_player_index:
                    _selected_player_name = name
                    break
        else:
            _selected_player_index = None
            _selected_player_name = ""
    else:
        _selected_player_index = None
        _selected_player_name = ""
    return [{"index": idx, "name": name} for idx, name in players]


def get_selected_player_index() -> int | None:
    refresh_players()
    return _selected_player_index


def get_selected_player_name() -> str:
    refresh_players()
    return _selected_player_name


def ensure_selected_player(*, prefer_host: bool = True) -> dict[str, Any]:
    """Keep a valid party target. If none selected, pick host (preferred) or first player."""
    players = refresh_players()
    if get_selected_player_index() is not None:
        return {
            "ok": True,
            "message": f"Target player already set to {get_selected_player_index()}: {get_selected_player_name()}",
            "selected_player": get_selected_player_name(),
            "selected_player_index": get_selected_player_index(),
            "auto_selected": False,
        }
    if not players:
        return {"ok": False, "message": "No party players found.", "needs_player": True}
    target_index: int | None = None
    if prefer_host:
        host_idx = _host_player_index_value()
        if host_idx is not None and any(int(p.get("index", -1)) == int(host_idx) for p in players):
            target_index = int(host_idx)
    if target_index is None:
        try:
            target_index = int(players[0].get("index"))
        except Exception:
            target_index = None
    if target_index is None:
        return {"ok": False, "message": "No party players found.", "needs_player": True}
    result = set_target_player(target_index)
    if result.get("ok"):
        result["auto_selected"] = True
        result["message"] = f"Auto-selected target {get_selected_player_index()}: {get_selected_player_name()}"
    return result


def set_target_player(index_or_name: object) -> dict[str, Any]:
    """Set selected target by party index, "index|name" payload, or name text."""
    global _selected_player_index, _selected_player_name
    # Important: party index 0 is valid; do not use `value or ""` (0 is falsy).
    if index_or_name is None:
        raw = ""
    else:
        raw = str(index_or_name).strip()
    raw_name = ""
    if "|" in raw:
        raw, raw_name = (part.strip() for part in raw.split("|", 1))
    if not raw:
        raw = raw_name
    if not raw:
        return {"ok": False, "message": "No target player was selected."}

    players = _players()
    wanted_index: int | None = None
    try:
        wanted_index = int(raw)
    except Exception:
        wanted_index = None

    if wanted_index is not None:
        for idx, name in players:
            if idx == wanted_index:
                if raw_name and _player_name_key(raw_name) != _player_name_key(name):
                    name_match = _find_player_by_exact_name(players, raw_name)
                    if name_match is not None:
                        idx, name = name_match
                        _selected_player_index = idx
                        _selected_player_name = name
                        return {
                            "ok": True,
                            "message": f"Target player set to {idx}: {name}",
                            "selected_player": name,
                            "selected_player_index": idx,
                        }
                    return {
                        "ok": False,
                        "message": f"Could not find party player {raw_name!r}. Press Refresh Status and try again.",
                    }
                _selected_player_index = idx
                _selected_player_name = name
                return {
                    "ok": True,
                    "message": f"Target player set to {idx}: {name}",
                    "selected_player": name,
                    "selected_player_index": idx,
                }
        return {
            "ok": False,
            "message": f"Could not find party player index {wanted_index}. Press Refresh Players and try again.",
        }

    needle = raw.lower()
    matches = [(idx, name) for idx, name in players if needle in name.lower()]
    if not matches:
        return {
            "ok": False,
            "message": f"Could not find party player matching {raw!r}. Press Refresh Players and try again.",
        }
    if len(matches) > 1:
        labels = ", ".join(f"{idx}: {name}" for idx, name in matches[:5])
        return {"ok": False, "message": f"Target player {raw!r} is ambiguous: {labels}"}

    idx, name = matches[0]
    _selected_player_index = idx
    _selected_player_name = name
    return {
        "ok": True,
        "message": f"Target player set to {idx}: {name}",
        "selected_player": name,
        "selected_player_index": idx,
    }


def _command_snapshot(
    action: str,
    *,
    label: str = "",
    payload: dict[str, Any] | None = None,
    is_drop: bool = False,
    needs_player: bool = False,
) -> dict[str, Any]:
    return {
        "action": str(action or "").strip(),
        "label": str(label or action or "").strip(),
        "payload": dict(payload or {}),
        "is_drop": bool(is_drop),
        "needs_player": bool(needs_player),
        "recorded_at": float(time.time()),
    }


def note_last_command(
    action: str,
    *,
    label: str = "",
    payload: dict[str, Any] | None = None,
    is_drop: bool = False,
    needs_player: bool = False,
) -> dict[str, Any]:
    """Record the last runnable command for Quick Menu pin / repeat."""
    global _last_command, _last_drop
    snap = _command_snapshot(
        action,
        label=label,
        payload=payload,
        is_drop=is_drop,
        needs_player=needs_player,
    )
    if not snap["action"]:
        return {"ok": False, "message": "No action to record."}
    _last_command = snap
    if snap["is_drop"]:
        _last_drop = dict(snap)
    return {"ok": True, "message": f"Recorded last command: {snap['label']}", "command": dict(snap)}


def get_last_command() -> dict[str, Any] | None:
    return dict(_last_command) if isinstance(_last_command, dict) else None


def get_last_drop() -> dict[str, Any] | None:
    return dict(_last_drop) if isinstance(_last_drop, dict) else None


def get_serial_delivery_progress() -> dict[str, Any]:
    """Lightweight delivery progress for Quick Menu toasts (no party refresh)."""
    try:
        delivery_progress = serial_rewards.serial_delivery_progress()
    except Exception as exc:
        return {
            "active": False,
            "message": "",
            "last_error": f"serial delivery progress unavailable: {exc!r}",
        }
    try:
        delivery_status = serial_rewards.serial_delivery_status()
    except Exception:
        delivery_status = ""
    if isinstance(delivery_progress, dict):
        progress = dict(delivery_progress)
        progress.setdefault("last_message", delivery_status or progress.get("message", ""))
        progress.setdefault("last_error", "")
        return progress
    return {"active": False, "message": str(delivery_progress or ""), "last_error": ""}


def set_drop_player_lock(enabled: object, index_or_name: object | None = None) -> dict[str, Any]:
    """Option C: lock repeat-last-drop to a party player (or clear the lock)."""
    global _drop_lock_enabled, _drop_lock_index, _drop_lock_name
    want = _truthy(enabled)
    if not want:
        _drop_lock_enabled = False
        _drop_lock_index = None
        _drop_lock_name = ""
        return {"ok": True, "message": "Drop player lock cleared.", "lock_enabled": False}

    target = index_or_name
    if target is None or str(target).strip() == "":
        target = get_selected_player_index()
        if target is None:
            target = get_selected_player_name()
    result = set_target_player(target)
    if not result.get("ok"):
        return result
    _drop_lock_enabled = True
    _drop_lock_index = get_selected_player_index()
    _drop_lock_name = get_selected_player_name()
    return {
        "ok": True,
        "message": f"Drop player lock set to {_drop_lock_name or _drop_lock_index}.",
        "lock_enabled": True,
        "lock_index": _drop_lock_index,
        "lock_name": _drop_lock_name,
    }


def get_drop_player_lock() -> dict[str, Any]:
    return {
        "enabled": bool(_drop_lock_enabled),
        "index": _drop_lock_index,
        "name": str(_drop_lock_name or ""),
    }


def _sync_drop_lock_from_layout(drop_lock: object) -> None:
    data = quick_menu_registry.sanitize_drop_lock(drop_lock)
    if not data.get("enabled"):
        set_drop_player_lock(False)
        return
    index = data.get("index")
    name = str(data.get("name") or "").strip()
    if index is not None and name:
        target: object = f"{index}|{name}"
    elif index is not None:
        target = index
    else:
        target = name
    set_drop_player_lock(True, target)


def get_quick_menu_layout() -> dict[str, Any]:
    return quick_menu_registry.get_quick_menu_snapshot()


def set_quick_menu_layout(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    result = quick_menu_registry.set_quick_menu_layout(dict(payload or {}))
    if result.get("ok"):
        _sync_drop_lock_from_layout(result.get("layout", {}).get("drop_lock"))
        result["revision"] = quick_menu_registry.get_layout_revision()
    return result


def assign_quick_menu_slot(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    result = quick_menu_registry.assign_quick_menu_slot(dict(payload or {}))
    if result.get("ok"):
        result["revision"] = quick_menu_registry.get_layout_revision()
    return result


def clear_quick_menu_page(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    result = quick_menu_registry.clear_quick_menu_page(dict(payload or {}))
    if result.get("ok"):
        result["revision"] = quick_menu_registry.get_layout_revision()
    return result


def _apply_drop_player_lock_if_needed() -> dict[str, Any] | None:
    """If lock is enabled, re-select the locked player. Returns an error dict on failure."""
    if not _drop_lock_enabled:
        return None
    target: object
    if _drop_lock_index is not None and _drop_lock_name:
        # Validate both values. set_target_player() will recover by exact name
        # if party indices changed after reconnect/reorder.
        target = f"{_drop_lock_index}|{_drop_lock_name}"
    elif _drop_lock_index is not None:
        target = _drop_lock_index
    elif _drop_lock_name:
        target = _drop_lock_name
    else:
        return {"ok": False, "message": "Drop player lock is enabled but empty."}
    result = set_target_player(target)
    if not result.get("ok"):
        return {
            "ok": False,
            "message": f"Locked drop player unavailable: {result.get('message', 'unknown error')}",
        }
    return None


def replay_recorded_command(command: dict[str, Any] | None, *, apply_lock: bool = False) -> dict[str, Any]:
    """Re-run a previously recorded command dict."""
    if not isinstance(command, dict):
        return {"ok": False, "message": "No recorded command."}
    action = str(command.get("action") or "").strip()
    if not action:
        return {"ok": False, "message": "Recorded command has no action."}
    payload = command.get("payload") if isinstance(command.get("payload"), dict) else {}
    if apply_lock and bool(command.get("needs_player")):
        lock_err = _apply_drop_player_lock_if_needed()
        if lock_err is not None:
            return lock_err
    return run_quick_menu_action(action, payload, record=False)


def repeat_last_drop(player_index_or_name: object | None = None) -> dict[str, Any]:
    """Repeat the last drop/delivery. Player is chosen at run time unless lock-to-player (option C)."""
    drop = get_last_drop()
    if drop is None:
        return {"ok": False, "message": "No last drop to repeat."}
    if player_index_or_name is not None and str(player_index_or_name).strip() != "":
        selected = set_target_player(player_index_or_name)
        if not selected.get("ok"):
            return selected
    elif bool(drop.get("needs_player")):
        if _drop_lock_enabled:
            lock_err = _apply_drop_player_lock_if_needed()
            if lock_err is not None:
                return lock_err
        else:
            return {
                "ok": False,
                "message": "Select a player at run time (or enable lock-to-player) before repeating the last drop.",
                "needs_player": True,
            }
    return replay_recorded_command(drop, apply_lock=False)


def run_quick_menu_action(
    action: str,
    payload: dict[str, Any] | None = None,
    *,
    record: bool = True,
) -> dict[str, Any]:
    """Dispatch a Quick Menu / pin-friendly named action through backend handlers."""
    payload = dict(payload or {})
    key = str(action or "").strip()
    label = str(payload.pop("_label", "") or key)
    is_drop = False
    needs_player = False

    if key == "repeat_last_drop":
        result = repeat_last_drop(payload.get("target_player"))
        return result
    if key == "max_all":
        result = max_all()
    elif key == "max_currency":
        result = max_currency()
    elif key == "max_eridium":
        result = max_eridium()
    elif key == "max_sdu":
        result = max_sdu()
    elif key == "max_player_level":
        result = max_player_level()
    elif key == "max_spec_level":
        result = max_spec_level()
    elif key == "give_currency":
        result = give_currency(payload.get("currency_kind", "cash"), payload.get("amount", 0))
        needs_player = True
    elif key == "set_level":
        result = give_experience(payload.get("xp_track", "player"), payload.get("level", 60))
        needs_player = True
    elif key == "open_golden_chest":
        result = open_golden_chest()
    elif key == "close_golden_chest":
        result = close_golden_chest()
    elif key == "spawn_golden_chest":
        result = spawn_golden_chest()
    elif key == "spawn_black_market":
        result = spawn_black_market()
    elif key == "black_market_clear_cooldown":
        result = black_market_clear_cooldown()
    elif key == "black_market_status":
        result = black_market_status()
    elif key == "rewards_open_everyone":
        result = rewards_open_everyone()
    elif key == "open_bank":
        result = open_bank_anywhere()
    elif key == "drop_all_shinies":
        result = drop_all_shinies_selected()
        is_drop = True
        needs_player = False
    elif key in ("shiny_selected", "deliver_shinies_selected"):
        result = deliver_shinies("selected")
        is_drop = True
        needs_player = True
    elif key in ("shiny_all", "deliver_shinies_all"):
        result = deliver_shinies("all")
        is_drop = True
    elif key in ("shiny_nonhost", "deliver_shinies_nonhost"):
        result = deliver_shinies("nonhost")
        is_drop = True
    elif key == "spawn_itempool":
        result = spawn_itempool(
            payload.get("itempool_name") or payload.get("pool_name"),
            payload.get("itempool_count") or payload.get("count") or 1,
            payload.get("itempool_level") or payload.get("level") or 60,
            payload,
        )
        is_drop = True
    elif key == "spawn_itempool_all":
        result = spawn_itempool_all(payload)
        is_drop = True
    elif key == "spawn_itempool_cancel":
        result = spawn_itempool_cancel()
    elif key == "spawn_itempool_status":
        result = spawn_itempool_status()
    elif key == "give_serial_selected":
        result = give_serials(
            payload.get("serial_text") or "",
            "selected",
            payload.get("serial_override_level") or payload.get("override_level") or False,
            payload.get("serial_level") or payload.get("level") or 60,
        )
        is_drop = True
        needs_player = True
    elif key == "give_serial_all":
        result = give_serials(
            payload.get("serial_text") or "",
            "all",
            payload.get("serial_override_level") or payload.get("override_level") or False,
            payload.get("serial_level") or payload.get("level") or 60,
        )
        is_drop = True
    elif key == "give_serial_nonhost":
        result = give_serials(
            payload.get("serial_text") or "",
            "nonhost",
            payload.get("serial_override_level") or payload.get("override_level") or False,
            payload.get("serial_level") or payload.get("level") or 60,
        )
        is_drop = True
    elif key == "travel_to_map":
        result = travel_to_map(payload.get("travel_map") or payload.get("map"))
    elif key == "travel_to_station":
        result = travel_to_station(payload.get("travel_station") or payload.get("station"))
    elif key == "location_bookmark_save":
        result = location_bookmark_save(payload.get("bookmark_name") or payload.get("name"))
    elif key == "location_bookmark_go":
        result = location_bookmark_go(payload.get("bookmark_name") or payload.get("name"))
    elif key == "location_bookmark_list":
        result = location_bookmark_list()
    elif key == "location_bookmark_delete":
        result = location_bookmark_delete(payload.get("bookmark_name") or payload.get("name"))
    elif key == "kick_player":
        result = kick_selected_player()
        needs_player = True
    elif key == "uvh_boost_all":
        result = uvh_boost_all()
    elif key.startswith("uvh_boost_tier_"):
        result = uvh_boost_tier(key.rsplit("_", 1)[-1])
    elif key == "uvh_boost_cancel":
        result = uvh_boost_cancel()
    elif key == "uvh_boost_resume":
        result = uvh_boost_resume()
    elif key == "uvh_boost_status":
        result = uvh_boost_status()
    elif key == "toggle_debug_cam":
        result = toggle_debug_cam()
    elif key == "disable_debug_cam":
        result = disable_debug_cam()
    elif key == "teleport_debug_cam":
        result = teleport_debug_cam()
    elif key == "debug_cam_to_target":
        result = debug_cam_to_target()
    elif key == "debug_cam_copy_location":
        result = debug_cam_copy_location()
    elif key == "debug_cam_set_speed":
        result = debug_cam_set_speed(payload.get("debug_cam_speed") or payload.get("speed"))
    elif key == "debug_cam_set_distance":
        result = debug_cam_set_distance(payload.get("debug_cam_distance") or payload.get("distance"))
    elif key.startswith("devperk_"):
        result = activate_devperk(key.rsplit("_", 1)[-1])
        needs_player = True
    elif key == "movement_apply_all":
        result = movement_apply_all(payload)
    elif key == "movement_reset_all":
        result = movement_reset_all()
    elif key.startswith("movement_preset_"):
        result = movement_apply_preset(key.removeprefix("movement_preset_"))
    elif key == "movement_toggle_no_target":
        result = movement_toggle_no_target()
    elif key == "movement_toggle_noclip":
        result = movement_toggle_noclip(payload)
    elif key == "movement_toggle_force_fly":
        result = movement_toggle_force_fly(payload)
    elif key == "movement_players_only":
        result = movement_toggle_players_only()
    elif key == "movement_delete_ground_items":
        result = movement_delete_ground_items()
    elif key == "movement_hide_ground_loot":
        result = movement_hide_ground_loot()
    elif key == "movement_pull_ground_loot":
        result = movement_pull_ground_loot()
    elif key == "movement_super_dash":
        result = movement_super_dash(payload.get("dash_strength"))
    elif key == "movement_super_dash_toggle":
        result = movement_super_dash_toggle()
    elif key == "movement_azzy_super_dash":
        result = movement_azzy_super_dash(payload.get("dash_strength"))
    elif key == "movement_azzy_super_dash_toggle":
        result = movement_azzy_super_dash_toggle()
    elif key == "movement_zero_vault":
        result = movement_zero_vault()
    elif key == "movement_set_time":
        result = movement_set_time(
            payload.get("movement_time_dilation")
            or payload.get("time_dilation")
            or payload.get("time")
            or 1.0
        )
    elif key == "movement_reset_time":
        result = movement_reset_time()
    elif key == "movement_infinite_jump_all_on":
        result = movement_infinite_jump_all(True)
    elif key == "movement_infinite_jump_all_off":
        result = movement_infinite_jump_all(False)
    elif key == "movement_infinite_jump_toggle":
        result = movement_infinite_jump_toggle(payload)
    elif key == "movement_infinite_jump_selected_on":
        result = movement_infinite_jump_set_selected(
            payload.get("infinite_jump_target") or payload.get("target_player"),
            True,
        )
        needs_player = True
    elif key == "movement_infinite_jump_selected_off":
        result = movement_infinite_jump_set_selected(
            payload.get("infinite_jump_target") or payload.get("target_player"),
            False,
        )
        needs_player = True
    elif key == "movement_infinite_jump_toggle_selected":
        result = movement_infinite_jump_selected(
            payload.get("infinite_jump_target") or payload.get("target_player")
        )
        needs_player = True
    elif key == "movement_teleport_to_slot":
        result = movement_teleport_selected_to_slot(payload.get("slot", 0))
        needs_player = True
    elif key == "movement_teleport_selected_to_me":
        result = movement_teleport_selected_to_me()
        needs_player = True
    elif key == "movement_teleport_me_to_selected":
        result = movement_teleport_me_to_selected()
        needs_player = True
    elif key == "movement_teleport_all_to_me":
        result = movement_teleport_all_to_me()
    elif key == "combat_tuning_apply":
        result = combat_tuning_apply(payload)
    elif key == "combat_tuning_reapply":
        result = combat_tuning_reapply()
    elif key == "combat_tuning_reset":
        result = combat_tuning_reset(payload.get("scope") or "local")
    elif key == "vehicle_preset_apply":
        result = vehicle_preset_apply(
            payload.get("vehicle_preset") or payload.get("preset") or payload.get("name"),
            payload.get("scope") or payload.get("vehicle_scope") or "local",
        )
    elif key == "vehicle_spawn":
        result = vehicle_spawn(
            payload.get("vehicle_id") or payload.get("name") or payload.get("alias"),
            payload.get("scope") or payload.get("vehicle_scope") or "local",
        )
    elif key == "vehicle_catalog":
        result = vehicle_catalog()
    elif key == "challenge_catalog_list":
        result = challenge_catalog_list(payload)
    elif key == "complete_challenges":
        result = complete_challenges(payload)
    elif key == "complete_challenges_all":
        result = complete_challenges_all(payload)
    elif key == "complete_challenges_cancel":
        result = complete_challenges_cancel()
    elif key == "complete_challenges_status":
        result = complete_challenges_status()
    elif key == "rarity_apply":
        result = rarity_apply(payload)
    elif key == "rarity_reset":
        result = rarity_reset()
    elif key == "rarity_only_legendary":
        result = rarity_only("legendary")
    elif key == "rarity_only_pearlescent":
        result = rarity_only("pearlescent")
    elif key.startswith("dev_spawner_"):
        result = run_dev_spawner_action(key, payload)
        if key in ("dev_spawner_spawnai", "dev_spawner_spawn", "dev_spawner_lostloot"):
            is_drop = True
    elif key == "set_backpack_bank_selected":
        result = set_inventory_sizes_selected(
            payload.get("backpack_size") or 1000,
            payload.get("bank_size") or 1000,
        )
    elif key == "set_backpack_bank_all":
        result = set_inventory_sizes_all_party(
            payload.get("backpack_size") or 1000,
            payload.get("bank_size") or 1000,
        )
    elif key == "refresh_players":
        players = refresh_players()
        result = {"ok": True, "message": f"Refreshed {len(players)} player(s).", "players": players}
    elif key == "set_target_player":
        result = set_target_player(payload.get("target_player"))
    elif key == "read_equipped_serials":
        result = read_equipped_serials(payload.get("target_player"))
        needs_player = True
    elif key == "read_backpack_serials":
        result = read_backpack_serials(payload.get("target_player"))
        needs_player = True
    elif key == "read_inventory":
        result = read_inventory(payload.get("target_player"))
        needs_player = True
    elif key == "copy_read_serial":
        result = copy_read_serial(payload.get("index") if "index" in payload else payload.get("serial_index"))
    elif key == "copy_all_read_serials":
        result = copy_all_read_serials()
    elif key == "chaos_launch":
        result = chaos_launch(payload.get("z") or payload.get("launch_z"))
        needs_player = True
    elif key == "chaos_drop_backpack":
        result = chaos_drop_backpack()
        needs_player = False
        is_drop = True
    elif key == "chaos_drop_backpack_targeted":
        result = chaos_drop_backpack_targeted()
        needs_player = True
        is_drop = True
    elif key == "chaos_empty_backpack":
        result = chaos_empty_backpack(payload)
        needs_player = True
    elif key in ("chaos_undo_empty_backpack", "backpack_undo_delete"):
        result = chaos_undo_empty_backpack(payload)
        is_drop = True
        needs_player = True
    elif key in ("chaos_clear_empty_backpack_memory", "backpack_clear_deleted_memory"):
        result = chaos_clear_empty_backpack_memory()
    elif key == "chaos_kill":
        result = chaos_kill()
        needs_player = True
    elif key == "chaos_ffyl":
        result = chaos_ffyl()
        needs_player = True
    elif key == "chaos_invert_look":
        result = chaos_invert_look(payload.get("seconds") or payload.get("secs"))
        needs_player = True
    elif key == "chaos_lock_look":
        result = chaos_lock_look(payload.get("seconds") or payload.get("secs"))
        needs_player = True
    elif key == "chaos_lock_move":
        result = chaos_lock_move(payload.get("seconds") or payload.get("secs"))
        needs_player = True
    elif key == "chaos_lock_both":
        result = chaos_lock_both(payload.get("seconds") or payload.get("secs"))
        needs_player = True
    elif key == "chaos_unlock":
        result = chaos_unlock()
        needs_player = True
    elif key == "reset_skills":
        result = reset_skills()
    elif key == "cxp_on":
        result = cxp_set_enabled(True, payload.get("multiplier") or payload.get("cxp_multiplier"))
    elif key == "cxp_off":
        result = cxp_set_enabled(False)
    elif key == "cxp_toggle":
        result = cxp_toggle(payload.get("multiplier") or payload.get("cxp_multiplier"))
    elif key == "cxp_set_mult":
        result = cxp_set_multiplier(payload.get("multiplier") or payload.get("cxp_multiplier"))
    elif key == "cxp_status":
        result = cxp_status()
    elif key == "instant_drops_on":
        result = instant_drops_set_enabled(True)
    elif key == "instant_drops_off":
        result = instant_drops_set_enabled(False)
    elif key == "instant_drops_toggle":
        result = instant_drops_toggle()
    elif key == "instant_drops_status":
        result = instant_drops_status()
    elif key == "instant_holds_on":
        result = instant_holds_set_enabled(True)
    elif key == "instant_holds_off":
        result = instant_holds_set_enabled(False)
    elif key == "instant_holds_toggle":
        result = instant_holds_toggle()
    elif key == "instant_holds_status":
        result = instant_holds_status()
    elif key == "fog_of_war_clear":
        result = fog_of_war_clear(payload.get("target_player") or payload.get("name"))
        needs_player = True
    elif key == "fog_of_war_on":
        result = fog_of_war_set_enabled(True)
    elif key == "fog_of_war_off":
        result = fog_of_war_set_enabled(False)
    elif key == "fog_of_war_toggle":
        result = fog_of_war_toggle()
    elif key == "fog_of_war_status":
        result = fog_of_war_status()
    elif key == "hoard_set_plan":
        result = hoard_set_plan(payload)
    elif key == "hoard_start":
        result = hoard_start()
    elif key == "hoard_stop":
        result = hoard_stop()
    elif key == "hoard_clear":
        result = hoard_clear(payload)
    elif key == "hoard_status":
        result = hoard_status()
    elif key == "unlock_cosmetics":
        result = unlock_cosmetics()
        needs_player = True
    elif key == "unlock_vehicles":
        result = unlock_vehicles()
        needs_player = True
    else:
        return {"ok": False, "message": f"Unknown quick menu action: {key}"}

    # Drop helpers above already call note_last_command; only record non-drop pins here.
    if record and result.get("ok") and not is_drop:
        note_last_command(
            key,
            label=label or key,
            payload=payload,
            is_drop=False,
            needs_player=needs_player,
        )
    return result


def _infinite_jump_status_safe() -> dict[str, Any]:
    try:
        return infinite_jump_status()
    except Exception:
        return {"enabled": False, "enabled_local": False, "count": 0, "names": "none"}


def get_status() -> dict[str, Any]:
    players = refresh_players()
    try:
        delivery_progress = serial_rewards.serial_delivery_progress()
    except Exception as exc:
        delivery_progress = {
            "active": False,
            "message": "",
            "last_error": f"serial delivery progress unavailable: {exc!r}",
        }
    try:
        delivery_status = serial_rewards.serial_delivery_status()
    except Exception:
        delivery_status = ""
    if isinstance(delivery_progress, dict):
        delivery_progress = dict(delivery_progress)
        delivery_progress.setdefault("last_message", delivery_status or delivery_progress.get("message", ""))
        delivery_progress.setdefault("last_error", "")
    else:
        delivery_progress = {"active": False, "message": str(delivery_progress or ""), "last_error": ""}
    return {
        "players": players,
        "selected_player": _selected_player_name,
        "selected_player_index": _selected_player_index,
        "host_player_index": _host_player_index_value(),
        "last_refresh_error": _last_refresh_error,
        "last_command": get_last_command(),
        "last_drop": get_last_drop(),
        "drop_player_lock": get_drop_player_lock(),
        "serial_delivery": delivery_progress,
        "serial_text": serial_text,
        "read_serials": get_last_read_serials(),
        "diagnostics": _sdk_diagnostics(),
        "rarity_weights": get_rarity_weights(),
        "rarity_revision": get_rarity_revision(),
        "asd_autoclear": _asd_autoclear_status(),
        "spawn_aggro_mode": _get_aggro_mode(),
        "spawn_anchor": _get_spawn_anchor(),
        "location_bookmarks": _list_location_bookmarks(),
        "vehicle_presets": _list_vehicle_presets(),
        "vehicle_catalog": _list_vehicle_catalog(),
        "cxp": _cxp.get_status_dict(),
        "instant_drops": _ich.get_status_dict(),
        "instant_holds": _ich.get_holds_status_dict(),
        "fog_of_war": _nfow.get_status_dict(),
        "infinite_jump": _infinite_jump_status_safe(),
        "challenge_bulk": _challenge_progress_payload(),
        "itempool_bulk": _itempool_progress_payload(),
        "uvh_boost": uvh_boost_status(),
        "debug_cam": _debug_cam_status(),
        "deleted_backpack": _deleted_backpack_status(),
    }


def kick_selected_player() -> dict[str, Any]:
    idx = get_selected_player_index()
    name = get_selected_player_name()
    if idx is None or not name:
        return {"ok": False, "message": "No party player selected."}
    ok = _kick_party_player_by_index(idx, "Kicked by host")
    if not ok:
        return {"ok": False, "message": f"Kick selected player failed for {idx}: {name}."}
    return {"ok": True, "message": "Kick selected player requested."}


def open_golden_chest() -> dict[str, Any]:
    try:
        _open_golden_chest()
        return {"ok": True, "message": "Open Golden Chest requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Open Golden Chest failed: {exc!r}"}


def close_golden_chest() -> dict[str, Any]:
    try:
        _close_golden_chest()
        return {"ok": True, "message": "Close Golden Chest requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Close Golden Chest failed: {exc!r}"}


def spawn_golden_chest() -> dict[str, Any]:
    """Host-safe IO spawn next to Open/Close Golden Chest (ASD spawnai)."""
    host_ok, host_msg = _challenge_is_host()
    if not host_ok:
        return {"ok": False, "message": "Spawn Golden Chest is host / listen only."}
    return run_dev_spawner_action(
        "dev_spawner_spawnai",
        {"dev_ai_name": "Lootable_GoldenChest", "dev_ai_count": 1},
    )


_BM_COOLDOWN_ATTRS = (
    "PurchaseCooldown",
    "LastPurchaseTime",
    "TimeUntilNextPurchase",
    "NextPurchaseTime",
    "CooldownRemaining",
    "PurchaseLockoutSeconds",
    "BlackMarketPurchaseCooldown",
    "bPurchaseOnCooldown",
)


def _live_black_market_objects() -> list[Any]:
    found: list[Any] = []
    seen: set[int] = set()
    try:
        import unrealsdk
    except Exception:
        return found
    for cls in (
        "InteractiveObject",
        "OakVendingMachine",
        "VendingMachine",
        "LootableObject",
    ):
        try:
            objs = unrealsdk.find_all(cls, False) or []
        except Exception:
            continue
        for obj in objs:
            if obj is None:
                continue
            try:
                text = str(obj)
            except Exception:
                continue
            if "Default__" in text:
                continue
            low = text.lower()
            if "blackmarket" not in low and "bmvm" not in low:
                continue
            oid = id(obj)
            if oid in seen:
                continue
            seen.add(oid)
            found.append(obj)
    return found


def spawn_black_market() -> dict[str, Any]:
    """Spawn a black-market vending machine via ASD spawnai.

    Dev Spawner catalogs list both ``io_VendingMachine_BlackMarket`` (preset
    command ``ssp_spawnai io_VendingMachine_BlackMarket``, "Black market step 1")
    and ``IO_VendingMachine_BlackMarket``. The lowercase IO is the name that
    actually resolves for spawnai; uppercase often returns queued_unverified
    with nothing in the world. After a spawn, activate last IO.
    """
    host_ok, host_msg = _challenge_is_host()
    if not host_ok:
        return {"ok": False, "message": "Spawn Black Market is host / listen only."}

    candidates = (
        "io_VendingMachine_BlackMarket",
        "IO_VendingMachine_BlackMarket",
    )
    last: dict[str, Any] = {}
    used = ""
    for name in candidates:
        last = run_dev_spawner_action(
            "dev_spawner_spawnai",
            {"dev_ai_name": name, "dev_ai_count": 1, "dev_ai_distance": 200},
        )
        used = name
        if _black_market_spawn_looks_real(last):
            break

    activate = run_dev_spawner_action("dev_spawner_activate_last", {})
    machines = _live_black_market_objects()
    if machines or _black_market_spawn_looks_real(last):
        spawn_msg = str(last.get("message") or "").strip()
        activate_msg = str(activate.get("message") or "").strip()
        extra = " ".join(part for part in (spawn_msg, activate_msg) if part)
        return {
            "ok": True,
            "message": (
                f"Spawn Black Market via {used} "
                f"({len(machines)} live machine(s)). {extra}"
            ).strip(),
            "actor": used,
            "machines": len(machines),
        }

    fallback = run_dev_spawner_action(
        "dev_spawner_spawn",
        {
            "dev_actor_name": "io_VendingMachine_BlackMarket",
            "dev_actor_count": 1,
            "dev_actor_distance": 200,
        },
    )
    run_dev_spawner_action("dev_spawner_activate_last", {})
    machines = _live_black_market_objects()
    if machines or fallback.get("ok"):
        return {
            "ok": True,
            "message": (
                f"Spawn Black Market via ASD_spawn io_VendingMachine_BlackMarket "
                f"({len(machines)} live). {fallback.get('message') or ''}"
            ).strip(),
            "actor": "io_VendingMachine_BlackMarket",
            "machines": len(machines),
        }

    detail = str((last or {}).get("message") or (fallback or {}).get("message") or "no spawn verified")
    return {
        "ok": False,
        "message": (
            "Spawn Black Market did not place a live machine. "
            f"Tried {', '.join(candidates)} then ASD_spawn. Last: {detail}"
        ),
        "actor": used,
        "machines": 0,
    }


def _black_market_spawn_looks_real(result: dict[str, Any] | None) -> bool:
    if not isinstance(result, dict):
        return False
    if result.get("spawn_verified") is True:
        return True
    if result.get("resolved") is True and int(result.get("alive_count") or 0) > 0:
        return True
    names = result.get("actor_names") or []
    if isinstance(names, list) and any(str(name).strip() for name in names):
        return True
    status = str(result.get("verification_status") or "").strip().lower()
    if status in ("verified", "spawned"):
        return True
    return False


def black_market_clear_cooldown() -> dict[str, Any]:
    """Best-effort clear of purchase-cooldown fields on live BMVM objects."""
    machines = _live_black_market_objects()
    cleared = 0
    for obj in machines:
        for attr in _BM_COOLDOWN_ATTRS:
            try:
                current = getattr(obj, attr, None)
            except Exception:
                continue
            if current is None:
                continue
            try:
                if isinstance(current, bool):
                    setattr(obj, attr, False)
                else:
                    setattr(obj, attr, 0)
                cleared += 1
            except Exception:
                continue
    return {
        "ok": True,
        "message": (
            f"Black market cooldown: found {len(machines)} live machine(s), "
            f"cleared {cleared} field(s)."
            if machines
            else "Black market cooldown: no live BMVM found. Spawn one first, or stand near a machine."
        ),
        "machines": len(machines),
        "cleared": cleared,
    }


def black_market_status() -> dict[str, Any]:
    machines = _live_black_market_objects()
    return {
        "ok": True,
        "message": f"Black market: {len(machines)} live machine(s) in world.",
        "machines": len(machines),
    }


def rewards_open_everyone() -> dict[str, Any]:
    """Open pending Reward Center packages on every live player manager."""
    try:
        opened = int(serial_rewards._open_all_live_reward_packages() or 0)
    except Exception as exc:
        return {"ok": False, "message": f"Open rewards everyone failed: {exc!r}"}
    return {
        "ok": True,
        "message": f"Opened pending Reward Center packages on {opened} player manager(s).",
        "opened": opened,
    }


def drop_all_shinies_selected() -> dict[str, Any]:
    try:
        count = drop_all_shinies(_SHINY_DEFAULT_LEVEL)
        result = {"ok": True, "message": f"Drop All Shinies requested for {count} shiny itempool(s)."}
        note_last_command("drop_all_shinies", label="Drop All Shinies", is_drop=True, needs_player=False)
        return result
    except Exception as exc:
        return {"ok": False, "message": f"Drop All Shinies failed: {exc!r}"}


def _electron_msbt_data_candidates(file_name: str) -> list[str]:
    """Best-effort paths where Electron writes remote catalog cache (delivery catalogs).

    Electron owns refresh; SDK only reads last-good JSON if present. Never fetches.
    Override with MSBT_DATA_CACHE pointing at the msbt_data directory.
    """
    name = os.path.basename(str(file_name or "").strip())
    if not name:
        return []
    out: list[str] = []
    env_dir = str(os.environ.get("MSBT_DATA_CACHE") or "").strip()
    if env_dir:
        out.append(os.path.join(env_dir, name))
    appdata = str(os.environ.get("APPDATA") or "").strip()
    if appdata:
        for app_folder in (
            "matts-sdk-boosting-tools",
            "Matt's SDK Boosting Tools",
            "MattsSDKBoostingTools",
        ):
            out.append(os.path.join(appdata, app_folder, "msbt_data", name))
    # De-dupe while preserving order.
    seen: set[str] = set()
    unique: list[str] = []
    for path in out:
        key = os.path.normcase(os.path.abspath(path))
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return unique


def _read_json_bytes_prefer_electron_cache(file_name: str, packaged_blob: bytes | None) -> tuple[bytes, str]:
    for candidate in _electron_msbt_data_candidates(file_name):
        try:
            if os.path.isfile(candidate):
                with open(candidate, "rb") as fh:
                    return fh.read(), candidate
        except Exception:
            continue
    if packaged_blob is not None:
        return packaged_blob, "packaged"
    raise FileNotFoundError(f"{file_name} not found in Electron cache or packaged mod data.")


def _load_shiny_serials() -> list[str]:
    package_name = __package__ or __name__.rpartition(".")[0]
    packaged = pkgutil.get_data(package_name, "shiny_serials.json")
    blob, _source = _read_json_bytes_prefer_electron_cache("shiny_serials.json", packaged)
    data = json.loads(blob.decode("utf-8"))
    if not isinstance(data, list):
        raise RuntimeError("shiny_serials.json must contain a JSON list.")

    serials: list[str] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        serial = str(entry.get("serial", "")).strip()
        if serial:
            serials.append(serial)
    if not serials:
        raise RuntimeError("No serial values found in shiny_serials.json.")
    return serials


def deliver_shinies(mode: str = "selected") -> dict[str, Any]:
    try:
        raw_serials = _load_shiny_serials()
        serials = serial_rewards._resolve_give_serial_strings(raw_serials)
        result = _deliver_serials_with_target(serials, mode, parsed_count=len(raw_serials))
        if result.get("ok"):
            mode_key = str(mode or "selected").lower().strip()
            action = {
                "selected": "shiny_selected",
                "all": "shiny_all",
                "nonhost": "shiny_nonhost",
                "non_host": "shiny_nonhost",
                "all_non_host": "shiny_nonhost",
            }.get(mode_key, "shiny_selected")
            note_last_command(
                action,
                label={
                    "shiny_selected": "Shinies Selected",
                    "shiny_all": "Shinies All",
                    "shiny_nonhost": "Shinies Non-Host",
                }.get(action, "Deliver Shinies"),
                is_drop=True,
                needs_player=(action == "shiny_selected"),
            )
        return result
    except Exception as exc:
        return {"ok": False, "message": f"Shiny reward delivery failed: {exc!r}"}


def open_bank_anywhere() -> dict[str, Any]:
    try:
        _exec_console("gbx.ui.view.stateadd MENU_BANK")
        return {"ok": True, "message": "Open Bank Anywhere requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Open Bank Anywhere failed: {exc!r}"}


def set_inventory_sizes_selected(backpack_size: object, bank_size: object) -> dict[str, Any]:
    idx = get_selected_player_index()
    if idx is None:
        return {"ok": False, "message": "No party player selected."}
    try:
        bp = clamp_container_size(int(backpack_size), 1000)
        bank = clamp_container_size(int(bank_size), 1000)
    except Exception:
        return {"ok": False, "message": "Backpack and Bank Size must be numbers."}
    try:
        name = set_inventory_sizes_for_party_index(idx, bp, bank)
        return {"ok": True, "message": f"Set inventory sizes for {name}: backpack {bp}, bank {bank}."}
    except Exception as exc:
        return {"ok": False, "message": f"Set backpack/bank size for selected player failed: {exc!r}"}


def set_inventory_sizes_all_party(backpack_size: object, bank_size: object) -> dict[str, Any]:
    try:
        bp = clamp_container_size(int(backpack_size), 1000)
        bank = clamp_container_size(int(bank_size), 1000)
    except Exception:
        return {"ok": False, "message": "Backpack and Bank Size must be numbers."}
    try:
        count = set_inventory_sizes_for_all_party(bp, bank)
        return {"ok": True, "message": f"Set inventory sizes for {count} party player(s): backpack {bp}, bank {bank}."}
    except Exception as exc:
        return {"ok": False, "message": f"Set backpack/bank size for all party players failed: {exc!r}"}


def auto_apply_inventory_sizes(backpack_size: object, bank_size: object, enabled: object = True) -> dict[str, Any]:
    try:
        is_enabled = str(enabled).strip().lower() not in ("", "0", "false", "off", "no", "none")
        bp = clamp_container_size(int(backpack_size), 1000)
        bank = clamp_container_size(int(bank_size), 1000)
    except Exception:
        return {"ok": False, "message": "Backpack and Bank Size must be numbers."}
    try:
        count = auto_apply_inventory_sizes_if_needed(is_enabled, bp, bank, source="external-bridge")
        if not is_enabled:
            return {"ok": True, "message": "Automatic inventory sizing disabled.", "applied": 0}
        if count:
            return {
                "ok": True,
                "message": f"Auto-applied inventory sizes to {count} party player(s): backpack {bp}, bank {bank}.",
                "applied": count,
            }
        return {"ok": True, "message": "Automatic inventory sizing checked; waiting for loaded party players.", "applied": 0}
    except Exception as exc:
        return {"ok": False, "message": f"Automatic inventory update failed: {exc!r}"}


def give_currency(kind_or_index: object, amount: object) -> dict[str, Any]:
    name = get_selected_player_name()
    if not name:
        return {"ok": False, "message": "No party player selected."}
    kind = _kind_from_input(kind_or_index)
    if kind is None:
        return {"ok": False, "message": f"Unsupported currency kind: {kind_or_index}"}
    try:
        amount_i = _clamp_int(amount, -MAX_WALLET_AMOUNT, MAX_WALLET_AMOUNT)
    except Exception:
        return {"ok": False, "message": "Currency amount must be a number."}
    try:
        player_economy._do_give_currency(kind, amount_i, name)
        return {"ok": True, "message": f"Give {amount_i} {kind} requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Give currency failed: {exc!r}"}


def give_experience(track_or_index: object, level: object) -> dict[str, Any]:
    name = get_selected_player_name()
    if not name:
        return {"ok": False, "message": "No party player selected."}
    track = _track_from_input(track_or_index)
    if track is None:
        return {"ok": False, "message": f"Unsupported XP track: {track_or_index}"}
    try:
        level_i = _clamp_int(level, 0, _max_level_for_track(track))
    except Exception:
        return {"ok": False, "message": "Level must be a number."}
    try:
        player_economy._do_give_experience(track, level_i, name)
        return {"ok": True, "message": f"Set {track} level {level_i} requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Set level failed: {exc!r}"}


def max_player_level() -> dict[str, Any]:
    name = get_selected_player_name()
    if not name:
        return {"ok": False, "message": "No party player selected."}
    try:
        player_economy._do_give_experience("player", MAX_PLAYER_LEVEL, name)
        return {"ok": True, "message": "Max player level requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Max player level failed: {exc!r}"}


def max_spec_level() -> dict[str, Any]:
    name = get_selected_player_name()
    if not name:
        return {"ok": False, "message": "No party player selected."}
    try:
        player_economy._do_give_experience("specialization", MAX_SPEC_LEVEL, name)
        return {"ok": True, "message": "Max specialization requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Max specialization failed: {exc!r}"}


def max_currency() -> dict[str, Any]:
    name = get_selected_player_name()
    if not name:
        return {"ok": False, "message": "No party player selected."}
    try:
        player_economy._do_give_currency("cash", MAX_WALLET_AMOUNT, name)
        return {"ok": True, "message": "Max cash requested for selected player."}
    except Exception as exc:
        return {"ok": False, "message": f"Max cash failed: {exc!r}"}


def max_eridium() -> dict[str, Any]:
    name = get_selected_player_name()
    if not name:
        return {"ok": False, "message": "No party player selected."}
    try:
        player_economy._do_give_currency("eridium", MAX_WALLET_AMOUNT, name)
        return {"ok": True, "message": "Max eridium requested for selected player."}
    except Exception as exc:
        return {"ok": False, "message": f"Max eridium failed: {exc!r}"}


def max_sdu() -> dict[str, Any]:
    name = get_selected_player_name()
    if not name:
        return {"ok": False, "message": "No party player selected."}
    try:
        player_economy._do_msbt_maxsdu(["name", name])
        return {"ok": True, "message": "Max SDU requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Max SDU failed: {exc!r}"}


def _selected_player_controller() -> Any | None:
    idx = get_selected_player_index()
    if idx is None:
        return None
    return _party_controller_for_index(idx)


def _party_controller_for_index(idx: int | None) -> Any | None:
    if idx is None:
        return None
    world, gs = _gbc_session_world_and_gamestate()
    pa = getattr(gs, "PlayerArray", None) if gs is not None else None
    if pa is None:
        return get_pc() if idx == 0 else None
    try:
        ps = pa[int(idx)]
    except Exception:
        return get_pc() if idx == 0 else None
    pc = _gbc_find_pc_for_player_state(ps, world)
    return pc or (get_pc() if idx == 0 else None)


def _selected_player_label(idx: int | None, name: str) -> str:
    if name:
        return name
    if idx is not None:
        return f"party index {idx}"
    return "selected player"


def _max_all_for_player_controller(pc: Any) -> tuple[bool, str]:
    ps = getattr(pc, "PlayerState", None)
    ok_bits: list[str] = []
    fail_bits: list[str] = []

    if ps is None:
        fail_bits.append("player state")
    else:
        if player_economy._set_experience_level_via_bp(ps, 0, MAX_PLAYER_LEVEL):
            ok_bits.append(f"player {MAX_PLAYER_LEVEL}")
        else:
            fail_bits.append("player level")
        if player_economy._set_experience_level_via_bp(ps, 1, MAX_SPEC_LEVEL):
            ok_bits.append(f"spec {MAX_SPEC_LEVEL}")
        else:
            fail_bits.append("spec level")

    currency_aliases = getattr(player_economy, "_CURRENCY_KIND_ALIASES", {})
    for kind in ("cash", "eridium"):
        token = currency_aliases.get(kind)
        if token and player_economy._give_currency_on_pc(pc, token, MAX_WALLET_AMOUNT):
            ok_bits.append(f"{kind} {MAX_WALLET_AMOUNT:,}")
        else:
            fail_bits.append(kind)

    if player_economy._set_max_sdu_points_on_pc(pc):
        ok_bits.append("max SDU")
    else:
        fail_bits.append("max SDU")

    try:
        from .vault_card_boost import max_all_vault_cards_for_pc

        vc_ok, vc_detail = max_all_vault_cards_for_pc(pc)
        if vc_ok:
            ok_bits.append(f"vault cards: {vc_detail[:120]}")
        else:
            fail_bits.append(f"vault cards partial: {vc_detail[:120]}")
    except Exception as exc:
        fail_bits.append(f"vault cards failed: {exc!r}")

    # Cosmetics / hover drives via ServerActivateDevPerk(4)
    try:
        perk_fn = getattr(pc, "ServerActivateDevPerk", None)
        if callable(perk_fn):
            perk_fn(4)
            ok_bits.append("cosmetics+hovers (devperk 4)")
        else:
            fail_bits.append("cosmetics (no ServerActivateDevPerk)")
    except Exception as exc:
        fail_bits.append(f"cosmetics failed: {exc!r}")

    # Personal vehicles unlock
    try:
        cars_ok, cars_detail = _unlock_all_vehicles_for_pc(pc)
        if cars_ok:
            ok_bits.append(f"cars: {cars_detail}")
        else:
            fail_bits.append(f"cars partial: {cars_detail}")
    except Exception as exc:
        fail_bits.append(f"cars failed: {exc!r}")

    # UVH 1-7 queued for this controller (accumulates across scoped Max All runs)
    try:
        uvh_ok, uvh_detail = _uvh_queue_for_pc(pc, list(range(len(UVH_RANKS))))
        if uvh_ok:
            ok_bits.append(f"UVH 1-7: {uvh_detail}")
        else:
            fail_bits.append(f"UVH: {uvh_detail}")
    except Exception as exc:
        fail_bits.append(f"UVH failed: {exc!r}")

    # Fog of war (client-local material hide; still run during Max All)
    try:
        fog_msg = _nfow.clear_fog()
        ok_bits.append(f"fog: {fog_msg}")
    except Exception as exc:
        fail_bits.append(f"fog failed: {exc!r}")

    detail = "; ".join(ok_bits)
    if fail_bits:
        if detail:
            detail += "; "
        detail += "failed: " + ", ".join(fail_bits)
    return not fail_bits, detail or "no writes reported"


def _pawn_for_party_index(idx: int | None) -> Any | None:
    pc = _party_controller_for_index(idx)
    if pc is None:
        return None
    try:
        pawn = pawn_for_controller(pc)
        if pawn is not None:
            return pawn
    except Exception:
        pass
    for attr in ("OakCharacter", "Character", "Pawn", "AcknowledgedPawn"):
        try:
            pawn = getattr(pc, attr, None)
            if pawn is not None:
                return pawn
        except Exception:
            pass
    return None


def max_all() -> dict[str, Any]:
    refresh_players()
    idx = _selected_player_index
    name = _selected_player_name
    if idx is None and not name:
        return {"ok": False, "message": "No party player selected."}
    try:
        pc = _party_controller_for_index(idx)
        label = _selected_player_label(idx, name)
        if pc is None:
            return {
                "ok": False,
                "message": (
                    f"Max All could not resolve a live player controller for {label}. "
                    "Refresh Players and try again."
                ),
            }
        ok, detail = _max_all_for_player_controller(pc)
        return {
            "ok": ok,
            "message": (
                f"Max All {'completed' if ok else 'partially completed'} for {label}: {detail}."
            ),
        }
    except Exception as exc:
        return {"ok": False, "message": f"Max All failed: {exc!r}"}


def cxp_set_enabled(enabled: bool, multiplier: object = None) -> dict[str, Any]:
    try:
        if multiplier is not None and str(multiplier).strip() != "":
            msg_m = _cxp.set_multiplier(float(multiplier))
            if "must be" in msg_m:
                return {"ok": False, "message": msg_m}
        msg = _cxp.set_enabled(bool(enabled))
        return {"ok": True, "message": msg, "cxp": _cxp.get_status_dict()}
    except Exception as exc:
        return {"ok": False, "message": f"CXP toggle failed: {exc!r}"}


def cxp_toggle(multiplier: object = None) -> dict[str, Any]:
    try:
        if multiplier is not None and str(multiplier).strip() != "":
            msg_m = _cxp.set_multiplier(float(multiplier))
            if "must be" in msg_m:
                return {"ok": False, "message": msg_m}
        msg = _cxp.toggle_enabled()
        return {"ok": True, "message": msg, "cxp": _cxp.get_status_dict()}
    except Exception as exc:
        return {"ok": False, "message": f"CXP toggle failed: {exc!r}"}


def cxp_set_multiplier(multiplier: object) -> dict[str, Any]:
    try:
        msg = _cxp.set_multiplier(float(multiplier))
        ok = "must be" not in msg
        return {"ok": ok, "message": msg, "cxp": _cxp.get_status_dict()}
    except Exception as exc:
        return {"ok": False, "message": f"CXP multiplier failed: {exc!r}"}


def cxp_status() -> dict[str, Any]:
    return {"ok": True, "message": _cxp.status_message(), "cxp": _cxp.get_status_dict()}


def instant_drops_set_enabled(enabled: bool) -> dict[str, Any]:
    try:
        msg = _ich.set_enabled(bool(enabled))
        return {
            "ok": True,
            "message": msg,
            "instant_drops": _ich.get_status_dict(),
            "instant_holds": _ich.get_holds_status_dict(),
        }
    except Exception as exc:
        return {"ok": False, "message": f"Instant drops failed: {exc!r}"}


def instant_drops_toggle() -> dict[str, Any]:
    try:
        msg = _ich.toggle_enabled()
        return {
            "ok": True,
            "message": msg,
            "instant_drops": _ich.get_status_dict(),
            "instant_holds": _ich.get_holds_status_dict(),
        }
    except Exception as exc:
        return {"ok": False, "message": f"Instant drops failed: {exc!r}"}


def instant_drops_status() -> dict[str, Any]:
    return {
        "ok": True,
        "message": _ich.status_message(),
        "instant_drops": _ich.get_status_dict(),
        "instant_holds": _ich.get_holds_status_dict(),
    }


def instant_holds_set_enabled(enabled: bool) -> dict[str, Any]:
    try:
        msg = _ich.set_holds_enabled(bool(enabled))
        return {
            "ok": True,
            "message": msg,
            "instant_drops": _ich.get_status_dict(),
            "instant_holds": _ich.get_holds_status_dict(),
        }
    except Exception as exc:
        return {"ok": False, "message": f"Instant holds failed: {exc!r}"}


def instant_holds_toggle() -> dict[str, Any]:
    try:
        msg = _ich.toggle_holds_enabled()
        return {
            "ok": True,
            "message": msg,
            "instant_drops": _ich.get_status_dict(),
            "instant_holds": _ich.get_holds_status_dict(),
        }
    except Exception as exc:
        return {"ok": False, "message": f"Instant holds failed: {exc!r}"}


def instant_holds_status() -> dict[str, Any]:
    return {
        "ok": True,
        "message": _ich.holds_status_message(),
        "instant_drops": _ich.get_status_dict(),
        "instant_holds": _ich.get_holds_status_dict(),
    }


def fog_of_war_set_enabled(enabled: bool) -> dict[str, Any]:
    try:
        msg = _nfow.set_enabled(bool(enabled))
        return {"ok": True, "message": msg, "fog_of_war": _nfow.get_status_dict()}
    except Exception as exc:
        return {"ok": False, "message": f"Fog of war failed: {exc!r}"}


def fog_of_war_toggle() -> dict[str, Any]:
    try:
        msg = _nfow.toggle_enabled()
        return {"ok": True, "message": msg, "fog_of_war": _nfow.get_status_dict()}
    except Exception as exc:
        return {"ok": False, "message": f"Fog of war failed: {exc!r}"}


def fog_of_war_status() -> dict[str, Any]:
    return {
        "ok": True,
        "message": _nfow.status_message(),
        "fog_of_war": _nfow.get_status_dict(),
    }


def hoard_set_plan(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return hoard_runner.set_plan(payload)


def hoard_start() -> dict[str, Any]:
    return hoard_runner.start()


def hoard_stop() -> dict[str, Any]:
    return hoard_runner.stop()


def hoard_clear(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return hoard_runner.clear(payload)


def hoard_status() -> dict[str, Any]:
    return hoard_runner.status()


def hoard_tick() -> None:
    hoard_runner.tick()


def fog_of_war_clear(target: object = None) -> dict[str, Any]:
    """Targeted fog clear: resolve party player (selected / name), then apply local fog hide."""
    refresh_players()
    label = _selected_player_label(_selected_player_index, _selected_player_name)
    if target is not None and str(target).strip():
        sel = set_target_player(target)
        if not sel.get("ok"):
            return sel
        label = _selected_player_label(_selected_player_index, _selected_player_name)
    if _selected_player_index is None and not _selected_player_name:
        return {"ok": False, "message": "No party player selected for fog_of_war_clear."}
    try:
        pc = _party_controller_for_index(_selected_player_index)
        if pc is None:
            return {
                "ok": False,
                "message": f"Fog clear could not resolve controller for {label}.",
            }
        msg = _nfow.clear_fog()
        return {
            "ok": True,
            "message": (
                f"Fog clear for target {label}: {msg}. "
                "Map fog materials are client-local; guests need their own clear for their map."
            ),
            "fog_of_war": _nfow.get_status_dict(),
        }
    except Exception as exc:
        return {"ok": False, "message": f"Fog clear failed: {exc!r}"}


def unlock_cosmetics() -> dict[str, Any]:
    idx = get_selected_player_index()
    name = get_selected_player_name()
    if idx is None and not name:
        return {"ok": False, "message": "No party player selected."}
    try:
        label = _activate_devperk(4, idx)
        return {
            "ok": True,
            "message": f"Cosmetics unlock requested for {_selected_player_label(idx, name)}: {label}.",
        }
    except Exception as exc:
        return {"ok": False, "message": f"Cosmetics unlock failed: {exc!r}"}


def unlock_vehicles() -> dict[str, Any]:
    idx = get_selected_player_index()
    name = get_selected_player_name()
    if idx is None and not name:
        return {"ok": False, "message": "No party player selected."}
    try:
        pc = _party_controller_for_index(idx)
        label = _selected_player_label(idx, name)
        if pc is None:
            return {"ok": False, "message": f"Could not resolve controller for {label}."}
        ok, detail = _unlock_all_vehicles_for_pc(pc)
        return {
            "ok": ok,
            "message": f"Vehicle unlock for {label}: {detail}.",
        }
    except Exception as exc:
        return {"ok": False, "message": f"Vehicle unlock failed: {exc!r}"}


@command("msbt_fog", description="Clear map fog for a targeted player: msbt_fog name <substring>")
def _cmd_msbt_fog(args: argparse.Namespace) -> None:
    from unrealsdk import logging as _sdk_logging

    parts = [str(p) for p in (getattr(args, "parts", None) or [])]
    if not parts:
        _sdk_logging.info("[MSBT Fog] Usage: msbt_fog name <substring>")
        return
    _head, name_sub = player_economy._parse_name_suffix(parts)
    if not name_sub and parts:
        name_sub = " ".join(parts)
    if not name_sub:
        _sdk_logging.info("[MSBT Fog] Usage: msbt_fog name <substring>")
        return
    result = fog_of_war_clear(name_sub)
    _sdk_logging.info(f"[MSBT Fog] {result.get('message')}")


_cmd_msbt_fog.add_argument(
    "parts",
    nargs="+",
    help="name <substring>",
)


def _uvh_live(obj: Any) -> bool:
    if obj is None:
        return False
    try:
        _ = obj.Name
        _ = obj.Class
        return True
    except Exception:
        return False


def _uvh_obj_addr(obj: Any) -> int:
    try:
        return int(obj._get_address())
    except Exception:
        return 0


def _uvh_obj_path(obj: Any) -> str:
    try:
        return str(obj._path_name())
    except Exception:
        return ""


def _uvh_is_runtime_controller(obj: Any) -> bool:
    if not _uvh_live(obj):
        return False
    path = _uvh_obj_path(obj)
    if not path or path.startswith("/Script/"):
        return False
    try:
        cls = str(obj.Class.Name)
    except Exception:
        cls = ""
    return "PlayerController" in cls or cls.endswith("Controller")


def _uvh_discover_controllers() -> list[Any]:
    try:
        import unrealsdk as _unrealsdk
    except Exception:
        _unrealsdk = None

    local = get_pc()
    found: list[Any] = []
    if _uvh_live(local):
        found.append(local)
    if _unrealsdk is not None:
        for cls in ("OakPlayerController", "PlayerController"):
            try:
                objects = _unrealsdk.find_all(cls, False)
            except TypeError:
                try:
                    objects = _unrealsdk.find_all(cls)
                except Exception:
                    objects = []
            except Exception:
                objects = []
            for obj in objects:
                if _uvh_is_runtime_controller(obj):
                    found.append(obj)

    local_addr = _uvh_obj_addr(local)
    unique: list[Any] = []
    seen: set[str] = set()
    for obj in found:
        addr = _uvh_obj_addr(obj)
        key = f"a:{addr}" if addr else f"p:{_uvh_obj_path(obj)}"
        if key in seen:
            continue
        seen.add(key)
        try:
            player_state = obj.PlayerState
        except Exception:
            player_state = None
        if _uvh_live(player_state) or (local_addr and addr == local_addr):
            unique.append(obj)
    return unique


def _uvh_delay_after(challenges: tuple[str, ...], index: int) -> float:
    if index == len(challenges) - 1:
        return _UVH_TIER_ACTIVATION_DELAY_SECONDS
    next_challenge = challenges[index + 1]
    if next_challenge.startswith("UVH_Rankup_") and next_challenge.endswith("_FinalChallenge"):
        return _UVH_PRE_FINAL_DELAY_SECONDS
    return _UVH_NORMAL_STEP_DELAY_SECONDS


def _uvh_build_plan(indices: list[int]) -> list[tuple[str, str, float]]:
    plan: list[tuple[str, str, float]] = []
    for rank_index in indices:
        label, challenges = UVH_RANKS[rank_index]
        plan.extend((label, challenge, _uvh_delay_after(challenges, step)) for step, challenge in enumerate(challenges))
    return plan


def _uvh_set_status(message: str) -> None:
    global _uvh_last_status
    _uvh_last_status = message
    try:
        from unrealsdk import logging as _sdk_logging

        _sdk_logging.info(f"[Matts SDK Boosting Tools | UVH] {message}")
    except Exception:
        pass


def _uvh_start(indices: list[int]) -> dict[str, Any]:
    global _uvh_queue, _uvh_targets, _uvh_next_at, _uvh_running, _uvh_paused_queue, _uvh_paused_targets
    if get_pc() is None:
        _uvh_set_status("Cannot start UVH boost: load into a character first.")
        return {"ok": False, "message": _uvh_last_status}
    targets = _uvh_discover_controllers()
    if not targets:
        _uvh_set_status("Cannot start UVH boost: no live players found.")
        return {"ok": False, "message": _uvh_last_status}
    plan = _uvh_build_plan(indices)
    if not plan:
        _uvh_set_status("Cannot start UVH boost: no UVH tier steps were selected.")
        return {"ok": False, "message": _uvh_last_status}
    _uvh_queue = deque(plan)
    _uvh_targets = targets
    _uvh_paused_queue = deque()
    _uvh_paused_targets = []
    _uvh_next_at = time.monotonic()
    _uvh_running = True
    names = ", ".join(UVH_RANKS[i][0] for i in indices)
    _uvh_set_status(f"UVH boost queued for {len(targets)} player(s): {names}; {len(plan)} challenge step(s).")
    return {"ok": True, "message": _uvh_last_status, "steps": len(plan), "players": len(targets)}


def _uvh_queue_for_pc(pc: Any, indices: list[int]) -> tuple[bool, str]:
    """Queue UVH steps for one controller; accumulate targets across Max All scope runs."""
    global _uvh_queue, _uvh_targets, _uvh_next_at, _uvh_running
    if pc is None or not _uvh_live(pc):
        return False, "no live controller"
    plan = _uvh_build_plan(indices)
    if not plan:
        return False, "empty UVH plan"
    addr = _uvh_obj_addr(pc)
    if not _uvh_running or not _uvh_queue:
        _uvh_queue = deque(plan)
        _uvh_targets = [pc]
        _uvh_next_at = time.monotonic()
        _uvh_running = True
        return True, f"queued {len(plan)} step(s)"
    # Already running — ensure this PC receives remaining steps.
    if not any(_uvh_obj_addr(t) == addr for t in _uvh_targets if t is not None):
        _uvh_targets.append(pc)
        return True, f"added to active UVH run ({len(_uvh_queue)} step(s) left)"
    return True, f"already in active UVH run ({len(_uvh_queue)} step(s) left)"


def uvh_boost_tier(tier: object) -> dict[str, Any]:
    try:
        index = int(tier) - 1
    except Exception:
        return {"ok": False, "message": f"Invalid UVH tier: {tier!r}."}
    if index < 0 or index >= len(UVH_RANKS):
        return {"ok": False, "message": f"Invalid UVH tier: {tier!r}. Choose 1-7."}
    return _uvh_start(list(range(index + 1)))


def uvh_boost_all() -> dict[str, Any]:
    return _uvh_start(list(range(len(UVH_RANKS))))


def uvh_boost_cancel() -> dict[str, Any]:
    global _uvh_queue, _uvh_targets, _uvh_running, _uvh_paused_queue, _uvh_paused_targets
    active = _uvh_running or bool(_uvh_queue)
    _uvh_paused_queue = deque(_uvh_queue)
    _uvh_paused_targets = list(_uvh_targets)
    remaining = len(_uvh_paused_queue)
    _uvh_queue = deque()
    _uvh_targets = []
    _uvh_running = False
    if active:
        _uvh_set_status(f"UVH boost paused ({remaining} step(s) left). Resume to continue.")
    else:
        _uvh_set_status("No UVH boost is active.")
    return {"ok": True, "message": _uvh_last_status, "paused_steps": remaining}


def uvh_boost_resume() -> dict[str, Any]:
    global _uvh_queue, _uvh_targets, _uvh_next_at, _uvh_running, _uvh_paused_queue, _uvh_paused_targets
    if _uvh_running or _uvh_queue:
        return {"ok": True, "message": f"UVH boost already running ({len(_uvh_queue)} step(s) left)."}
    if not _uvh_paused_queue:
        _uvh_set_status("Nothing to resume. Start UVH 1–7 (or Up to rank N) first.")
        return {"ok": False, "message": _uvh_last_status}
    live = [controller for controller in _uvh_paused_targets if _uvh_live(controller)]
    if not live:
        live = _uvh_discover_controllers()
    if not live:
        _uvh_set_status("Cannot resume UVH boost: no live players found.")
        return {"ok": False, "message": _uvh_last_status}
    _uvh_queue = deque(_uvh_paused_queue)
    _uvh_targets = live
    _uvh_paused_queue = deque()
    _uvh_paused_targets = []
    _uvh_next_at = time.monotonic()
    _uvh_running = True
    _uvh_set_status(f"UVH boost resumed for {len(live)} player(s); {len(_uvh_queue)} step(s) left.")
    return {"ok": True, "message": _uvh_last_status, "steps_remaining": len(_uvh_queue), "players": len(live)}


def uvh_boost_status() -> dict[str, Any]:
    return {
        "ok": True,
        "message": _uvh_last_status,
        "active": _uvh_running,
        "steps_remaining": len(_uvh_queue),
        "paused_steps": len(_uvh_paused_queue),
        "players": len(_uvh_targets) or len(_uvh_paused_targets),
    }


def uvh_boost_tick() -> None:
    global _uvh_next_at, _uvh_running
    if not _uvh_queue or time.monotonic() < _uvh_next_at:
        return
    if get_pc() is None:
        return
    label, challenge, delay = _uvh_queue.popleft()
    live_targets = [controller for controller in _uvh_targets if _uvh_live(controller)]
    sent = 0
    for controller in live_targets:
        try:
            controller.ServerIncrementChallengeForPlayer(challenge, 1)
            sent += 1
        except Exception as exc:
            _uvh_set_status(f"{challenge} failed for one player: {exc!r}")
    _uvh_next_at = time.monotonic() + delay
    if _uvh_queue:
        _uvh_set_status(f"{label}: sent {challenge} to {sent}/{len(live_targets)} player(s); {len(_uvh_queue)} step(s) left.")
    else:
        _uvh_running = False
        _uvh_targets.clear()
        _uvh_set_status(f"UVH boost complete. Final step sent to {sent}/{len(live_targets)} player(s).")


# Drain catalog grants on the UMG tick. Large amounts are sent in one RPC;
# if that RPC fails we retry in 250-sized chunks so the SUM still reaches the goal.
_CHALLENGE_STEP_DELAY_SECONDS = 0.0
_CHALLENGE_BATCH_SIZE = 64
_CHALLENGE_CHUNK_AMOUNT = 250
_CHALLENGE_STATUS_EVERY = 50
_challenge_catalog_cache: list[tuple[str, int]] | None = None
_challenge_queue: deque[tuple[str, int]] = deque()
_challenge_targets: list[Any] = []
_challenge_next_at = 0.0
_challenge_running = False
_challenge_last_status = "Ready."
_challenge_total_steps = 0
_challenge_ok = 0
_challenge_failed = 0
_challenge_granted: set[str] = set()

# MIT-reimplemented category filters (behavior inspired by SQBT; no GPL imports).
_CHALLENGE_CATEGORY_LABELS: tuple[str, ...] = (
    "All non-UVHM",
    "Story challenge flags",
    "Activities",
    "Collectibles",
    "Loot",
    "Combat",
    "Enemies",
    "Elemental",
    "Economy",
    "Character",
)
_CHALLENGE_CATEGORY_RULES: dict[str, tuple[str, ...]] = {
    "story challenge flags": (
        "completemainstory",
        "completesidemissions",
        "challenges_achievements_24_missions_",
        "challenges_achievements_25_missions_",
        "challenges_achievements_26_missions_",
        "challenges_achievements_27_missions_",
        "challenges_achievements_28_missions_",
        "challenges_achievements_29_missions_",
    ),
    "activities": ("challenge_tutorial_activity_", "challenge_activity_"),
    "collectibles": ("challenge_tutorial_collectible_", "challenge_collect_"),
    "loot": ("challenge_loot_",),
    "combat": (
        "challenge_assault_",
        "challenge_heavyweapon_",
        "challenge_grenade_",
        "challenge_melee_",
        "challenge_sniper_",
        "challenge_shotgun_",
        "challenge_pistol_",
        "challenge_smg_",
        "challenge_borg_",
        "challenge_daedalus_",
        "challenge_jakobs_",
        "challenge_maliwan_",
        "challenge_order_",
        "challenge_ripper_",
        "challenge_tediore_",
        "challenge_torgue_",
        "challenge_vladof_",
        "challenge_repairkit_",
        "challenge_revive",
        "challenge_secondwind",
        "challenge_shield_",
        "challenge_spareparts_",
        "loyaltychallenge_",
        "cowbell_challenges_combat_",
    ),
    "enemies": ("challenge_kill_", "challenge_killarmy_", "cowbell_challenges_enemies_"),
    "elemental": (
        "challenge_fire_",
        "challenge_cryo_",
        "challenge_corrosive_",
        "challenge_shock_",
        "challenge_radiation_",
        "challenge_2_status_effects",
        "challenge_all_status_effects",
        "challenge_maliwan_status",
    ),
    "economy": (
        "challenge_sellloot",
        "challenge_tutorial_misc_blackmarket",
        "challenge_getcash",
        "challenge_geteridium",
        "challenge_havecash",
        "challenge_havemorecash",
    ),
    "character": (
        "_levelup",
        "challenge_darksiren_",
        "challenge_exosoldier_",
        "challenge_gravitar_",
        "challenge_paladin_",
        "cowbell_challenges_characters_robodealer_",
    ),
}


def _challenge_set_status(message: str) -> None:
    global _challenge_last_status
    _challenge_last_status = message
    try:
        from unrealsdk import logging as _sdk_logging

        _sdk_logging.info(f"[Matts SDK Boosting Tools | Challenges] {message}")
    except Exception:
        pass


def _challenge_should_skip(challenge_id: str) -> bool:
    """Skip aggregate parents that cascade into many child rewards."""
    return challenge_id.startswith("ChallengeParent_")


def _challenge_normalize_key(challenge_id: str) -> str:
    return str(challenge_id or "").casefold().replace("-", "_")


def _challenge_grant_amount(amount: int) -> int:
    """Keep the catalog goal; never clamp completeness down to a stub grant."""
    try:
        value = int(amount)
    except Exception:
        value = 1
    return max(1, value)


def _challenge_delay_for_amount(amount: int) -> float:
    if amount > 100:
        return 0.02
    return _CHALLENGE_STEP_DELAY_SECONDS


def _challenge_is_host() -> tuple[bool, str]:
    """Allow standalone + listen host; refuse join clients. Fail open if NetMode is ambiguous."""
    try:
        from .party_helpers import _gbc_session_world_and_gamestate

        pc = get_pc()
        if pc is not None:
            try:
                if not bool(pc.HasAuthority()):
                    return False, "Complete challenges on the host / listen session, not as a join client."
            except Exception:
                pass
        world, _gs = _gbc_session_world_and_gamestate()
        if world is None:
            return True, ""
        try:
            from unrealsdk.unreal import ENetMode

            mode = world.GetNetMode()
            if mode in (ENetMode.NM_ListenServer, ENetMode.NM_Standalone):
                return True, ""
        except Exception:
            pass
        try:
            mode_i = int(world.GetNetMode())
            if mode_i in (0, 2):
                return True, ""
            if mode_i == 3:
                return False, "Complete challenges on the host / listen session, not as a join client."
        except Exception:
            return True, ""
        return True, ""
    except Exception:
        return True, ""


def _challenge_increment_one(controller: Any, challenge: str, amount: int) -> None:
    """Grant the full catalog amount; chunk only if the native RPC rejects the full value."""
    fn = getattr(controller, "ServerIncrementChallengeForPlayer", None)
    if not callable(fn):
        raise RuntimeError("ServerIncrementChallengeForPlayer unavailable")
    grant = _challenge_grant_amount(amount)
    try:
        fn(challenge, int(grant))
        return
    except Exception:
        leftover = int(grant)
        last_exc: Exception | None = None
        while leftover > 0:
            step = min(_CHALLENGE_CHUNK_AMOUNT, leftover)
            try:
                fn(challenge, int(step))
                leftover -= step
            except Exception as exc:
                last_exc = exc
                break
        if leftover > 0:
            raise last_exc or RuntimeError(f"{challenge} increment failed")


def _load_challenge_catalog() -> list[tuple[str, int]]:
    global _challenge_catalog_cache
    if _challenge_catalog_cache is not None:
        return list(_challenge_catalog_cache)
    rows: list[tuple[str, int]] = []
    try:
        package = __package__ or "MattsSDKBoostingTools"
        packaged = pkgutil.get_data(package, "challenge_catalog.json")
        raw, _source = _read_json_bytes_prefer_electron_cache("challenge_catalog.json", packaged)
        if raw:
            data = json.loads(raw.decode("utf-8"))
            entries = data.get("entries") if isinstance(data, dict) else None
            if isinstance(entries, list):
                for entry in entries:
                    if not isinstance(entry, dict):
                        continue
                    challenge_id = str(entry.get("id") or "").strip()
                    if not challenge_id or _challenge_should_skip(challenge_id):
                        continue
                    try:
                        amount = max(1, int(entry.get("amount") or 1))
                    except Exception:
                        amount = 1
                    rows.append((challenge_id, amount))
    except Exception as exc:
        _challenge_set_status(f"Challenge catalog load failed: {exc!r}")
        rows = []
    _challenge_catalog_cache = rows
    return list(rows)


def _challenge_rows_for_category(category: str, search: str = "") -> list[tuple[str, int]]:
    """Filter catalog rows by category + search. Always skips UVHM tokens (uvh)."""
    category_key = str(category or "All non-UVHM").strip().casefold()
    rules = _CHALLENGE_CATEGORY_RULES.get(category_key)
    needle = str(search or "").strip().casefold()
    out: list[tuple[str, int]] = []
    for challenge_id, amount in _load_challenge_catalog():
        key = _challenge_normalize_key(challenge_id)
        if "uvh" in key:
            continue
        if category_key != "all non-uvhm":
            if not rules or not any(rule in key for rule in rules):
                continue
        if needle and needle not in challenge_id.casefold():
            continue
        out.append((challenge_id, amount))
    return out


def challenge_catalog_list(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Read-only filtered challenge catalog for the Boosting Challenges panel."""
    payload = payload or {}
    category = str(payload.get("category") or "All non-UVHM").strip() or "All non-UVHM"
    search = str(payload.get("search") or payload.get("q") or "").strip()
    rows = _challenge_rows_for_category(category, search)
    return {
        "ok": True,
        "categories": list(_CHALLENGE_CATEGORY_LABELS),
        "entries": [{"id": cid, "amount": amt} for cid, amt in rows],
        "count": len(rows),
        "category": category,
        "search": search,
        "message": f"{len(rows)} challenge(s) for {category}" + (f" matching '{search}'" if search else "") + ".",
    }


def _challenge_queue_start(rows: list[tuple[str, int]], *, label: str = "Challenges") -> dict[str, Any]:
    """Shared queue start used by complete-all / selected / category."""
    global _challenge_queue, _challenge_targets, _challenge_next_at, _challenge_running, _challenge_total_steps
    global _challenge_ok, _challenge_failed, _challenge_granted
    if _challenge_running or _challenge_queue:
        remaining = len(_challenge_queue)
        _challenge_set_status(
            f"{label} already running ({remaining} step(s) left). "
            "Use complete_challenges_cancel first."
        )
        return {"ok": False, "message": _challenge_last_status, "active": True, "steps_remaining": remaining}
    host_ok, host_msg = _challenge_is_host()
    if not host_ok:
        _challenge_set_status(host_msg)
        return {"ok": False, "message": host_msg, "host_required": True}
    if get_pc() is None:
        _challenge_set_status("Cannot start: load into a character first.")
        return {"ok": False, "message": _challenge_last_status}
    targets = _uvh_discover_controllers()
    if not targets:
        _challenge_set_status("Cannot start: no live players found.")
        return {"ok": False, "message": _challenge_last_status}
    if not rows:
        _challenge_set_status(f"Cannot start: no challenges matched for {label}.")
        return {"ok": False, "message": _challenge_last_status}
    _challenge_queue = deque(rows)
    _challenge_targets = targets
    _challenge_total_steps = len(rows)
    _challenge_ok = 0
    _challenge_failed = 0
    _challenge_granted = set()
    _challenge_next_at = time.monotonic()
    _challenge_running = True
    _challenge_set_status(
        f"{label} queued for {len(targets)} player(s); {_challenge_total_steps} step(s) "
        f"(batch {_CHALLENGE_BATCH_SIZE}/tick)."
    )
    return {
        "ok": True,
        "message": _challenge_last_status,
        "steps": _challenge_total_steps,
        "players": len(targets),
        "active": True,
        "steps_remaining": _challenge_total_steps,
        "steps_done": 0,
        "ok_count": 0,
        "failed_count": 0,
        "percent": 0,
    }


def complete_challenges_all(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Queue every non-UVHM catalog challenge for live players.

    Electron shows a confirm dialog before calling. Console/QM run immediately.
    Complete ALL matches Squ1ggs: All non-UVHM, skip parent tokens. UVHM stays on the UVH buttons.
    """
    payload = payload or {}
    rows = _challenge_rows_for_category("All non-UVHM", "")
    if not rows:
        _challenge_set_status("Cannot start: challenge catalog is empty or missing.")
        return {"ok": False, "message": _challenge_last_status}
    return _challenge_queue_start(rows, label="Complete ALL challenges")


def _challenge_ids_from_payload(payload: dict[str, Any]) -> list[str]:
    raw_ids = payload.get("challenge_ids") or payload.get("ids") or payload.get("tokens")
    ids: list[str] = []
    if isinstance(raw_ids, str):
        ids.extend(part.strip() for part in raw_ids.split(",") if part.strip())
    elif isinstance(raw_ids, (list, tuple)):
        ids.extend(str(item).strip() for item in raw_ids if str(item).strip())
    single = str(
        payload.get("challenge_id") or payload.get("id") or payload.get("token") or ""
    ).strip()
    if single:
        ids.insert(0, single)
    seen: set[str] = set()
    ordered: list[str] = []
    for item in ids:
        key = item.casefold()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered


def _challenge_rows_for_ids(ids: list[str], fallback_amount: int = 1) -> list[tuple[str, int]]:
    catalog = _load_challenge_catalog()
    by_lower = {cid.casefold(): (cid, amt) for cid, amt in catalog}
    rows: list[tuple[str, int]] = []
    for raw in ids:
        match = by_lower.get(raw.casefold())
        if match is not None:
            rows.append(match)
        else:
            rows.append((raw, max(1, int(fallback_amount))))
    return rows


def complete_challenges(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Queue one or more challenge ids, or a filtered category."""
    payload = payload or {}
    ids = _challenge_ids_from_payload(payload)
    category = str(payload.get("category") or "").strip()

    if ids:
        try:
            amount = max(1, int(payload.get("amount") or 1))
        except Exception:
            amount = 1
        rows = _challenge_rows_for_ids(ids, fallback_amount=amount)
        if len(rows) == 1:
            return _challenge_queue_start(rows, label=f"Challenge {rows[0][0]}")
        return _challenge_queue_start(rows, label=f"{len(rows)} selected challenges")

    if category:
        rows = _challenge_rows_for_category(category, "")
        return _challenge_queue_start(rows, label=f"Category {category}")

    return {
        "ok": False,
        "message": "Provide challenge_id, challenge_ids, or category (or use complete_challenges_all).",
    }


def complete_challenges_cancel() -> dict[str, Any]:
    global _challenge_queue, _challenge_targets, _challenge_running
    active = _challenge_running or bool(_challenge_queue)
    remaining = len(_challenge_queue)
    _challenge_queue = deque()
    _challenge_targets = []
    _challenge_running = False
    _challenge_set_status(
        f"Challenges cancelled ({remaining} step(s) left)."
        if active
        else "No challenge run is active."
    )
    return complete_challenges_status()


def _challenge_progress_payload() -> dict[str, Any]:
    remaining = len(_challenge_queue)
    done = max(0, int(_challenge_total_steps) - remaining) if _challenge_total_steps else 0
    percent = 0
    if _challenge_total_steps:
        percent = int(round(100.0 * done / float(_challenge_total_steps)))
    return {
        "ok": True,
        "message": _challenge_last_status,
        "active": _challenge_running,
        "steps_remaining": remaining,
        "steps_total": _challenge_total_steps,
        "steps_done": done,
        "ok_count": _challenge_ok,
        "failed_count": _challenge_failed,
        "percent": percent,
        "players": len(_challenge_targets),
    }


def complete_challenges_status() -> dict[str, Any]:
    return _challenge_progress_payload()


def _challenge_finish_reconcile(live_targets: list[Any]) -> str:
    notes: list[str] = []
    try:
        from .challenge_objective_complete import reconcile_after_bulk
    except Exception as exc:
        return f"objective reconcile skipped: {exc!r}"
    for controller in live_targets:
        try:
            notes.append(reconcile_after_bulk(controller, _challenge_granted))
        except Exception as exc:
            notes.append(f"reconcile failed: {exc!r}")
    return "; ".join(notes) if notes else ""


def complete_challenges_tick() -> None:
    global _challenge_next_at, _challenge_running, _challenge_ok, _challenge_failed
    if not _challenge_queue or time.monotonic() < _challenge_next_at:
        return
    if get_pc() is None:
        _challenge_queue.clear()
        _challenge_targets.clear()
        _challenge_running = False
        _challenge_set_status("Challenges stopped: no local player controller.")
        return
    live_targets = [controller for controller in _challenge_targets if _uvh_live(controller)]
    if not live_targets:
        _challenge_queue.clear()
        _challenge_targets.clear()
        _challenge_running = False
        _challenge_set_status("Challenges stopped: no live players left.")
        return

    last_challenge = ""
    last_grant_amount = 1
    last_sent = 0
    batch_delay = _CHALLENGE_STEP_DELAY_SECONDS
    for _ in range(max(1, int(_CHALLENGE_BATCH_SIZE))):
        if not _challenge_queue:
            break
        challenge, amount = _challenge_queue.popleft()
        grant_amount = _challenge_grant_amount(amount)
        sent = 0
        last_error = ""
        for controller in live_targets:
            try:
                _challenge_increment_one(controller, challenge, grant_amount)
                sent += 1
            except Exception as exc:
                last_error = f"{type(exc).__name__}: {exc}"
        last_challenge = challenge
        last_grant_amount = grant_amount
        last_sent = sent
        if sent:
            _challenge_ok += 1
            _challenge_granted.add(challenge)
        else:
            _challenge_failed += 1
            _challenge_set_status(
                f"Skipped rejected {challenge}"
                + (f" ({last_error})" if last_error else "")
                + f"; continuing ({_challenge_failed} skipped)."
            )
        batch_delay = max(batch_delay, _challenge_delay_for_amount(grant_amount))

    _challenge_next_at = time.monotonic() + batch_delay
    done = _challenge_total_steps - len(_challenge_queue)
    if _challenge_queue:
        if done == 1 or done % _CHALLENGE_STATUS_EVERY == 0:
            _challenge_set_status(
                f"Challenges: {done}/{_challenge_total_steps} "
                f"(ok {_challenge_ok}, fail {_challenge_failed}) "
                f"{last_challenge} x{last_grant_amount} -> {last_sent}/{len(live_targets)} player(s)."
            )
        return

    reconcile_note = _challenge_finish_reconcile(live_targets)
    _challenge_running = False
    _challenge_targets.clear()
    extra = f" {reconcile_note}" if reconcile_note else ""
    _challenge_set_status(
        f"Challenges finished. {done}/{_challenge_total_steps} "
        f"(ok {_challenge_ok}, fail {_challenge_failed}). "
        f"Final {last_challenge} -> {last_sent}/{len(live_targets)} player(s).{extra}"
    )


def toggle_debug_cam() -> dict[str, Any]:
    idx = get_selected_player_index()
    try:
        message = _toggle_debug_cam(idx)
        return {"ok": True, "message": message, "debug_cam": _debug_cam_status()}
    except Exception as extra:
        return {"ok": False, "message": f"Toggle Debug Cam failed: {extra!r}"}


def disable_debug_cam() -> dict[str, Any]:
    idx = get_selected_player_index()
    try:
        message = _disable_debug_cam(idx)
        return {"ok": True, "message": message, "debug_cam": _debug_cam_status()}
    except Exception as extra:
        return {"ok": False, "message": f"Disable Debug Cam failed: {extra!r}"}


def teleport_debug_cam() -> dict[str, Any]:
    idx = get_selected_player_index()
    try:
        message = _teleport_pawn_to_debug_cam(idx)
        return {"ok": True, "message": message}
    except Exception as extra:
        return {"ok": False, "message": f"Teleport Pawn to Debug Cam failed: {extra!r}"}


def debug_cam_to_target() -> dict[str, Any]:
    idx = get_selected_player_index()
    try:
        message = _teleport_debug_cam_to_pawn(idx)
        return {"ok": True, "message": message}
    except Exception as extra:
        return {"ok": False, "message": f"Pull cam to target failed: {extra!r}"}


def debug_cam_copy_location() -> dict[str, Any]:
    try:
        return _copy_debug_cam_location()
    except Exception as extra:
        return {"ok": False, "message": f"Copy debug cam location failed: {extra!r}"}


def debug_cam_set_speed(speed: object = None) -> dict[str, Any]:
    try:
        message = _set_debug_cam_speed(float(speed if speed is not None else 1.0))
        return {"ok": True, "message": message, "debug_cam": _debug_cam_status()}
    except Exception as extra:
        return {"ok": False, "message": f"Set debug cam speed failed: {extra!r}"}


def debug_cam_set_distance(distance: object = None) -> dict[str, Any]:
    try:
        message = _set_debug_cam_distance(float(distance if distance is not None else 0.0))
        return {"ok": True, "message": message, "debug_cam": _debug_cam_status()}
    except Exception as extra:
        return {"ok": False, "message": f"Set debug cam distance failed: {extra!r}"}


def activate_devperk(perk: object) -> dict[str, Any]:
    idx = get_selected_player_index()
    try:
        label = _activate_devperk(int(perk), idx)
        return {"ok": True, "message": f"Dev perk {int(perk)} requested.", "label": label}
    except Exception as exc:
        return {"ok": False, "message": f"Dev perk failed: {exc!r}"}


_ITEMPOOL_BULK_MAX = 200
_itempool_queue: deque[tuple[str, int, int, int]] = deque()
_itempool_running = False
_itempool_next_at = 0.0
_itempool_total = 0
_itempool_ok = 0
_itempool_failed = 0
_itempool_last_status = "Item pool bulk idle."
_itempool_delay_s = 0.0
_itempool_items_per_tick = 1
_itempool_spit = "forward"


def _itempool_knobs_from_payload(payload: dict[str, Any] | None = None) -> tuple[float, int, str]:
    payload = payload or {}
    delay = _clamp_float(
        payload.get("itempool_delay") if payload.get("itempool_delay") not in (None, "") else payload.get("delay", _itempool_delay_s),
        0.0,
        5.0,
        _itempool_delay_s,
    )
    per_tick = _clamp_int(
        payload.get("itempool_items_per_tick") or payload.get("items_per_tick") or _itempool_items_per_tick,
        1,
        25,
    )
    spit = _normalize_spit_direction(
        str(payload.get("itempool_spit") or payload.get("spit") or _itempool_spit)
    )
    return delay, per_tick, spit


def _apply_itempool_knobs(payload: dict[str, Any] | None = None) -> tuple[float, int, str]:
    global _itempool_delay_s, _itempool_items_per_tick, _itempool_spit
    delay, per_tick, spit = _itempool_knobs_from_payload(payload)
    _itempool_delay_s = delay
    _itempool_items_per_tick = per_tick
    _itempool_spit = spit
    return delay, per_tick, spit


def spawn_itempool(
    pool_name: object,
    count: object,
    level: object,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    global _itempool_queue, _itempool_running, _itempool_next_at
    global _itempool_total, _itempool_ok, _itempool_failed
    name = str(pool_name or "").strip()
    if not name:
        return {"ok": False, "message": "No item pool selected."}
    delay, per_tick, spit = _apply_itempool_knobs(extra)
    try:
        qty = max(1, int(count))
        lvl = int(level)
        if delay > 0.0 and qty > per_tick:
            if not _itempool_running:
                _itempool_total = 0
                _itempool_ok = 0
                _itempool_failed = 0
            _itempool_queue.append((name, lvl, qty, qty))
            _itempool_total += 1
            _itempool_next_at = time.monotonic()
            _itempool_running = True
            _itempool_set_status(
                f"Queued {name} x{qty} (delay {delay:.2f}s, {per_tick}/tick, spit={spit})."
            )
            result = _itempool_progress_payload()
            result["message"] = _itempool_last_status
            note_last_command(
                "spawn_itempool",
                label=f"Spawn {name}",
                payload={
                    "itempool_name": name,
                    "itempool_count": qty,
                    "itempool_level": lvl,
                    "itempool_delay": delay,
                    "itempool_items_per_tick": per_tick,
                    "itempool_spit": spit,
                },
                is_drop=True,
                needs_player=False,
            )
            return result
        spawned = spawn_item_pool(name, lvl, qty, direction=spit)
        result = {
            "ok": True,
            "message": f"Spawned item pool {name} x{spawned} at level {lvl} spit={spit}.",
        }
        note_last_command(
            "spawn_itempool",
            label=f"Spawn {name}",
            payload={
                "itempool_name": name,
                "itempool_count": qty,
                "itempool_level": lvl,
                "itempool_delay": delay,
                "itempool_items_per_tick": per_tick,
                "itempool_spit": spit,
            },
            is_drop=True,
            needs_player=False,
        )
        return result
    except Exception as exc:
        return {"ok": False, "message": f"Spawn item pool failed: {exc!r}"}


def _itempool_set_status(message: str) -> None:
    global _itempool_last_status
    _itempool_last_status = message


def _itempool_progress_payload() -> dict[str, Any]:
    remaining = len(_itempool_queue)
    done = max(0, int(_itempool_total) - remaining) if _itempool_total else 0
    percent = 0
    if _itempool_total:
        percent = int(round(100.0 * done / float(_itempool_total)))
    return {
        "ok": True,
        "message": _itempool_last_status,
        "active": _itempool_running,
        "steps_remaining": remaining,
        "steps_total": _itempool_total,
        "steps_done": done,
        "ok_count": _itempool_ok,
        "failed_count": _itempool_failed,
        "percent": percent,
        "itempool_delay": _itempool_delay_s,
        "itempool_items_per_tick": _itempool_items_per_tick,
        "itempool_spit": _itempool_spit,
    }


def spawn_itempool_all(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Queue every named pool (Electron sends the current filtered list)."""
    global _itempool_queue, _itempool_running, _itempool_next_at
    global _itempool_total, _itempool_ok, _itempool_failed
    payload = payload or {}
    raw_names = payload.get("itempool_names") or payload.get("names") or []
    if isinstance(raw_names, str):
        names = [part.strip() for part in raw_names.split(",") if part.strip()]
    elif isinstance(raw_names, (list, tuple)):
        names = [str(item).strip() for item in raw_names if str(item).strip()]
    else:
        names = []
    if not names:
        return {"ok": False, "message": "No filtered item pools to spawn."}
    if len(names) > _ITEMPOOL_BULK_MAX:
        names = names[:_ITEMPOOL_BULK_MAX]
    level = _clamp_int(payload.get("itempool_level") or payload.get("level") or 60, 1, 60)
    count = _clamp_int(payload.get("itempool_count") or payload.get("count") or 1, 1, 100)
    delay, per_tick, spit = _apply_itempool_knobs(payload)
    _itempool_queue = deque((name, int(level), int(count), int(count)) for name in names)
    _itempool_total = len(_itempool_queue)
    _itempool_ok = 0
    _itempool_failed = 0
    _itempool_next_at = time.monotonic()
    _itempool_running = True
    _itempool_set_status(
        f"Queued {_itempool_total} filtered item pool(s) at level {level} x{count} "
        f"(delay {delay:.2f}s, {per_tick}/tick, spit={spit})."
    )
    return _itempool_progress_payload()


def spawn_itempool_cancel() -> dict[str, Any]:
    global _itempool_queue, _itempool_running
    remaining = len(_itempool_queue)
    active = _itempool_running or remaining > 0
    _itempool_queue = deque()
    _itempool_running = False
    _itempool_set_status(
        f"Item pool bulk cancelled ({remaining} left)." if active else "No item pool bulk is active."
    )
    return _itempool_progress_payload()


def spawn_itempool_status() -> dict[str, Any]:
    return _itempool_progress_payload()


def spawn_itempool_tick() -> None:
    global _itempool_next_at, _itempool_running, _itempool_ok, _itempool_failed
    if not _itempool_queue or time.monotonic() < _itempool_next_at:
        return
    row = _itempool_queue.popleft()
    if len(row) >= 4:
        name, level, remaining, original = row[0], row[1], row[2], row[3]
    else:
        name, level, remaining = row[0], row[1], row[2]
        original = remaining
    batch = max(1, min(int(_itempool_items_per_tick), int(remaining)))
    start_index = max(0, int(original) - int(remaining))
    try:
        spawned = spawn_item_pool(
            name,
            int(level),
            int(batch),
            direction=_itempool_spit,
            start_index=start_index,
        )
        leftover = int(remaining) - int(spawned)
        if leftover > 0:
            _itempool_queue.appendleft((name, int(level), leftover, int(original)))
            _itempool_set_status(
                f"Spawning {name} ({int(original) - leftover}/{original}; "
                f"{len(_itempool_queue)} pool(s) left)."
            )
        else:
            _itempool_ok += 1
            _itempool_set_status(
                f"Spawned {name} x{original} ({_itempool_ok + _itempool_failed}/{_itempool_total}; "
                f"{len(_itempool_queue)} left)."
            )
    except Exception as exc:
        _itempool_failed += 1
        _itempool_set_status(f"{name} failed: {exc!r} ({len(_itempool_queue)} left).")
    _itempool_next_at = time.monotonic() + max(0.0, float(_itempool_delay_s))
    if not _itempool_queue:
        _itempool_running = False
        _itempool_set_status(
            f"Item pool bulk finished. {_itempool_ok} ok, {_itempool_failed} fail "
            f"of {_itempool_total}."
        )


def run_dev_spawner_action(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(payload or {})
    # Non-ASD helpers (aggro / anchor) — handled before console command mapping.
    if action == "dev_spawner_set_aggro":
        msg = _set_aggro_mode(str(payload.get("aggro_mode") or payload.get("mode") or "passive"))
        return {"ok": True, "message": msg, "aggro_mode": _get_aggro_mode()}
    if action == "dev_spawner_set_anchor":
        msg = _set_spawn_anchor(str(payload.get("spawn_anchor") or payload.get("anchor") or "local"))
        return {"ok": True, "message": msg, "spawn_anchor": _get_spawn_anchor()}
    if action == "dev_spawner_reaggro":
        mode = payload.get("aggro_mode") or payload.get("mode")
        if mode:
            _set_aggro_mode(str(mode))
        _note_spawned_actors(None)
        msg = _reaggro_tracked() if not mode else _apply_aggro_to_tracked(mode=str(mode))
        return {"ok": True, "message": msg, "aggro_mode": _get_aggro_mode()}
    if action == "dev_spawner_anchor_info":
        actor, label = _resolve_spawn_anchor_actor()
        name = str(getattr(actor, "Name", "") or "") if actor is not None else ""
        return {
            "ok": True,
            "message": f"Spawn anchor={_get_spawn_anchor()} resolved={label} actor={name or 'none'}",
            "spawn_anchor": _get_spawn_anchor(),
            "resolved": label,
            "actor": name,
        }

    direct_dev_spawner_result: dict[str, Any] | None = None
    try:
        if action == "dev_spawner_status":
            cmd = "ASD_status"
        elif action == "dev_spawner_clear":
            cmd = "ASD_clear"
        elif action == "dev_spawner_activate_last":
            cmd = "ASD_activate_last"
        elif action == "dev_spawner_scriptdump":
            cmd = "ASD_scriptdump"
        elif action == "dev_spawner_cache_status":
            cmd = "ASD_cache_status"
        elif action == "dev_spawner_logo_options":
            cmd = "ASD_logo_options"
        elif action == "dev_spawner_spawnerdiag":
            limit = _clamp_int(payload.get("dev_actor_target_limit") or 20, 1, 200)
            distance = _clamp_float(payload.get("dev_actor_distance"), 0.0, 20000.0, 350.0)
            cmd = f"ASD_spawnerdiag --limit {limit} --distance {distance:g}"
        elif action == "dev_spawner_targets":
            name = _dev_spawner_token(payload.get("dev_actor_name"), "Actor/template name", required=True)
            class_name = _dev_spawner_token(payload.get("dev_actor_class"), "Actor class")
            limit = _clamp_int(payload.get("dev_actor_target_limit") or 20, 1, 200)
            parts = ["ASD_targets", name, "--limit", str(limit)]
            if class_name:
                parts.extend(("--class", class_name))
            if _dev_spawner_bool(payload.get("dev_actor_include_non_generated")):
                parts.append("--include-non-generated")
            cmd = " ".join(parts)
        elif action == "dev_spawner_lostloot":
            class_name = _dev_spawner_token(payload.get("dev_actor_class"), "Actor class")
            count = _clamp_int(payload.get("dev_actor_count") or 1, 1, 50)
            distance = _clamp_float(payload.get("dev_actor_distance"), 0.0, 20000.0, 350.0)
            spacing = _clamp_float(payload.get("dev_actor_spacing"), 0.0, 5000.0, 125.0)
            scale = _clamp_float(payload.get("dev_actor_scale"), 0.01, 20.0, 1.0)
            z_offset = _clamp_float(payload.get("dev_actor_z_offset"), -10000.0, 10000.0, -100.0)
            delay = _clamp_float(payload.get("dev_actor_delay"), 0.0, 30.0, 1.0)
            enable_states = _dev_spawner_state_list(payload.get("dev_actor_enable_states"), "Enable states")
            disable_states = _dev_spawner_state_list(payload.get("dev_actor_disable_states"), "Disable states")
            parts = [
                "ASD_lostloot",
                "--count",
                str(count),
                "--distance",
                f"{distance:g}",
                "--spacing",
                f"{spacing:g}",
                "--scale",
                f"{scale:g}",
                "--z-offset",
                f"{z_offset:g}",
                "--delay",
                f"{delay:g}",
            ]
            if class_name:
                parts.extend(("--class", class_name))
            if enable_states:
                parts.extend(("--enable", enable_states))
            if disable_states:
                parts.extend(("--disable", disable_states))
            if _dev_spawner_bool(payload.get("dev_actor_no_activate")):
                parts.append("--no-activate")
            if _dev_spawner_bool(payload.get("dev_actor_include_non_generated")):
                parts.append("--include-non-generated")
            cmd = " ".join(parts)
        elif action == "dev_spawner_spawn":
            name = _dev_spawner_token(payload.get("dev_actor_name"), "Actor/template name", required=True)
            class_name = _dev_spawner_token(payload.get("dev_actor_class"), "Actor class")
            count = _clamp_int(payload.get("dev_actor_count") or 1, 1, 50)
            distance = _clamp_float(payload.get("dev_actor_distance"), 0.0, 20000.0, 350.0)
            spacing = _clamp_float(payload.get("dev_actor_spacing"), 0.0, 5000.0, 125.0)
            scale = _clamp_float(payload.get("dev_actor_scale"), 0.01, 20.0, 1.0)
            z_offset = _clamp_float(payload.get("dev_actor_z_offset"), -10000.0, 10000.0, -100.0)
            delay = _clamp_float(payload.get("dev_actor_delay"), 0.0, 30.0, 1.0)
            enable_states = _dev_spawner_state_list(payload.get("dev_actor_enable_states"), "Enable states")
            disable_states = _dev_spawner_state_list(payload.get("dev_actor_disable_states"), "Disable states")
            parts = [
                "ASD_spawn",
                name,
                "--count",
                str(count),
                "--distance",
                f"{distance:g}",
                "--spacing",
                f"{spacing:g}",
                "--scale",
                f"{scale:g}",
                "--z-offset",
                f"{z_offset:g}",
                "--delay",
                f"{delay:g}",
            ]
            if class_name:
                parts.extend(("--class", class_name))
            if enable_states:
                parts.extend(("--enable", enable_states))
            if disable_states:
                parts.extend(("--disable", disable_states))
            if _dev_spawner_bool(payload.get("dev_actor_no_activate")):
                parts.append("--no-activate")
            if _dev_spawner_bool(payload.get("dev_actor_include_non_generated")):
                parts.append("--include-non-generated")
            cmd = " ".join(parts)
        elif action in ("dev_spawner_spawnai", "dev_spawner_probeai"):
            name = _dev_spawner_token(payload.get("dev_ai_name"), "AI actor-def name", required=True)
            command = "ASD_spawnai" if action == "dev_spawner_spawnai" else "ASD_probeai"
            parts = [command, name]
            extra_loads: list[str] = []
            if action == "dev_spawner_spawnai":
                count = _clamp_int(payload.get("dev_ai_count") or 1, 1, 12)
                distance = _clamp_float(payload.get("dev_ai_distance"), 0.0, 20000.0, 350.0)
                spacing = _clamp_float(payload.get("dev_ai_spacing"), 1.0, 5000.0, 125.0)
                scale = _clamp_float(payload.get("dev_ai_scale"), 0.05, 20.0, 1.0)
                z_offset = _clamp_float(payload.get("dev_ai_z_offset"), -5000.0, 5000.0, 0.0)
                direct_only = _dev_spawner_bool(payload.get("dev_ai_direct_only"))
                parts.extend(
                    (
                        "--count",
                        str(count),
                        "--distance",
                        f"{distance:g}",
                        "--spacing",
                        f"{spacing:g}",
                        "--scale",
                        f"{scale:g}",
                        "--zoffset",
                        f"{z_offset:g}",
                    )
                )
                if direct_only:
                    parts.append("--direct-only")
            load_path = _dev_spawner_token(payload.get("dev_ai_load"), "AI load path")
            if load_path:
                parts.extend(("--load", load_path))
                extra_loads.append(load_path)
            cmd = " ".join(parts)
            if action == "dev_spawner_spawnai":
                direct_dev_spawner_result = _run_actor_script_deployer_spawnai_like_debug_menu(
                    name=name,
                    count=count,
                    distance=distance,
                    spacing=spacing,
                    scale=scale,
                    z_offset=z_offset,
                    extra_loads=extra_loads,
                    direct_only=direct_only,
                )
        elif action == "dev_spawner_cache":
            name = _dev_spawner_token(payload.get("dev_ai_name"), "AI actor-def/cache name", required=True)
            class_name = _dev_spawner_token(payload.get("dev_ai_class"), "AI source class")
            limit = _clamp_int(payload.get("dev_ai_cache_limit") or 10, 1, 100)
            index = _clamp_int(payload.get("dev_ai_cache_index") or 0, 0, 99)
            parts = ["ASD_cache", name, "--index", str(index), "--limit", str(limit)]
            if class_name:
                parts.extend(("--class", class_name))
            cmd = " ".join(parts)
        elif action == "dev_spawner_barrel_logo":
            text = _dev_spawner_quoted_text(payload.get("dev_logo_text"))
            if text == '""':
                return {"ok": False, "message": "Barrel Logo text is required."}
            actor = _dev_spawner_token(payload.get("dev_logo_actor") or "barrel", "Logo actor")
            distance = _clamp_float(payload.get("dev_logo_distance"), 0.0, 30000.0, 2500.0)
            height = _clamp_float(payload.get("dev_logo_height"), 0.0, 10000.0, 750.0)
            spacing = _clamp_float(payload.get("dev_logo_spacing"), 1.0, 1000.0, 70.0)
            scale = _clamp_float(payload.get("dev_logo_scale"), 0.01, 20.0, 0.45)
            parts = [
                "ASD_barrellogo",
                "--text",
                text,
                "--actor",
                actor,
                "--distance",
                f"{distance:g}",
                "--height",
                f"{height:g}",
                "--spacing",
                f"{spacing:g}",
                "--scale",
                f"{scale:g}",
            ]
            if _dev_spawner_bool(payload.get("dev_logo_include_non_generated")):
                parts.append("--include-non-generated")
            cmd = " ".join(parts)
        else:
            return {"ok": False, "message": f"Unsupported dev spawner action: {action}"}

        if direct_dev_spawner_result is not None:
            result = dict(direct_dev_spawner_result)
            result.setdefault("command", cmd)
            result.setdefault("accepted", bool(result.get("asd_log_lines")))
            result.setdefault("message", "ActorScriptDeployer spawn request processed.")
        else:
            direct_ok, direct_message = _run_actor_script_deployer_command(cmd)
            if not direct_ok:
                return {
                    "ok": False,
                    "message": f"ActorScriptDeployer command was unavailable: {direct_message}",
                    "command": cmd,
                    "mode": "ActorScriptDeployer direct command unavailable",
                }
            result = {
                "ok": True,
                "message": (
                    f"Sent {cmd.split()[0]} to ActorScriptDeployer. "
                    "The bridge only confirms ASD received the command; check unrealsdk.log for spawn/result details."
                ),
                "command": cmd,
                "mode": direct_message,
            }

        if action == "dev_spawner_clear":
            _asd_disarm_autoclear()
        elif action in (
            "dev_spawner_spawnai",
            "dev_spawner_spawn",
            "dev_spawner_lostloot",
            "dev_spawner_barrel_logo",
        ) and result.get("ok"):
            _asd_note_spawn_for_autoclear()
            try:
                _note_spawned_actors(None)
                if _get_aggro_mode() not in ("passive", "none", "off"):
                    aggro_msg = _apply_aggro_to_tracked()
                    prev = str(result.get("message") or "")
                    result["message"] = f"{prev} | {aggro_msg}".strip(" |")
            except Exception:
                pass

        if result.get("ok") and action in (
            "dev_spawner_spawnai",
            "dev_spawner_spawn",
            "dev_spawner_lostloot",
        ):
            if action == "dev_spawner_spawnai":
                target_name = str(payload.get("dev_ai_name") or "").strip()
                pin_payload = {
                    "dev_ai_name": target_name,
                    "dev_ai_count": payload.get("dev_ai_count", 1),
                    "dev_ai_distance": payload.get("dev_ai_distance", 350),
                    "dev_ai_spacing": payload.get("dev_ai_spacing", 125),
                    "dev_ai_scale": payload.get("dev_ai_scale", 1),
                    "dev_ai_z_offset": payload.get("dev_ai_z_offset", 0),
                    "dev_ai_load": payload.get("dev_ai_load", ""),
                    "dev_ai_direct_only": payload.get("dev_ai_direct_only", False),
                }
                pin_label = f"Spawn {target_name}" if target_name else "Spawn Actor"
            else:
                target_name = str(payload.get("dev_actor_name") or "").strip()
                pin_payload = {
                    key: payload.get(key)
                    for key in (
                        "dev_actor_name",
                        "dev_actor_class",
                        "dev_actor_count",
                        "dev_actor_distance",
                        "dev_actor_spacing",
                        "dev_actor_scale",
                        "dev_actor_z_offset",
                        "dev_actor_delay",
                        "dev_actor_enable_states",
                        "dev_actor_disable_states",
                        "dev_actor_no_activate",
                        "dev_actor_include_non_generated",
                    )
                    if key in payload
                }
                pin_label = (
                    "Spawn Lost Loot"
                    if action == "dev_spawner_lostloot"
                    else (f"Spawn {target_name}" if target_name else "Spawn Template")
                )
            note_last_command(
                action,
                label=pin_label,
                payload=pin_payload,
                is_drop=True,
                needs_player=False,
            )
        return result
    except Exception as exc:
        return {"ok": False, "message": f"Dev spawner action failed: {exc!r}"}


def travel_to_map(map_name: object) -> dict[str, Any]:
    try:
        msg = _travel_to_map(str(map_name or "").strip())
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Travel to map failed: {exc!r}"}


def travel_to_station(station_name: object) -> dict[str, Any]:
    try:
        msg = _travel_to_station(str(station_name or "").strip())
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Travel to station failed: {exc!r}"}


def location_bookmark_save(name: object) -> dict[str, Any]:
    try:
        msg = _save_location_bookmark(str(name or "").strip())
        return {"ok": True, "message": msg, "bookmarks": _list_location_bookmarks()}
    except Exception as exc:
        return {"ok": False, "message": f"Save location bookmark failed: {exc!r}"}


def location_bookmark_go(name: object) -> dict[str, Any]:
    try:
        msg = _go_location_bookmark(str(name or "").strip())
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Go location bookmark failed: {exc!r}"}


def location_bookmark_list() -> dict[str, Any]:
    try:
        rows = _list_location_bookmarks()
        return {"ok": True, "message": f"{len(rows)} location bookmark(s).", "bookmarks": rows}
    except Exception as exc:
        return {"ok": False, "message": f"List location bookmarks failed: {exc!r}"}


def location_bookmark_delete(name: object) -> dict[str, Any]:
    try:
        msg = _delete_location_bookmark(str(name or "").strip())
        return {"ok": True, "message": msg, "bookmarks": _list_location_bookmarks()}
    except Exception as exc:
        return {"ok": False, "message": f"Delete location bookmark failed: {exc!r}"}


def _asd_autoclear_status() -> dict[str, Any]:
    now = time.monotonic()
    armed = bool(_asd_batch_armed)
    due = float(_asd_batch_clear_due or 0.0)
    remaining = max(0.0, due - now) if armed and due > 0.0 else 0.0
    return {
        "armed": armed,
        "window_s": float(_ASD_BATCH_WINDOW_S),
        "clear_due_at": due if armed else 0.0,
        "seconds_remaining": round(remaining, 1),
        "batch_started_at": float(_asd_batch_start or 0.0) if armed else 0.0,
    }


def movement_delete_ground_items() -> dict[str, Any]:
    try:
        msg = delete_ground_items()
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Delete ground items failed: {exc!r}"}


def movement_hide_ground_loot() -> dict[str, Any]:
    try:
        msg = hide_ground_loot()
        low = str(msg).lower()
        ok = "failed" not in low and "load into" not in low
        if "no ground loot" in low or "moved" in low:
            ok = True
        return {"ok": ok, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Clear Loot (Hide) failed: {exc!r}"}


def movement_pull_ground_loot() -> dict[str, Any]:
    try:
        msg = pull_ground_loot_here()
        low = str(msg).lower()
        ok = "failed" not in low and "load into" not in low
        if "no ground loot" in low or "moved" in low:
            ok = True
        return {"ok": ok, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Pull loot failed: {exc!r}"}


def movement_super_dash(strength: object = None) -> dict[str, Any]:
    try:
        value = None if strength is None or str(strength).strip() == "" else int(strength)
        msg = fire_super_dash(value)
        return {"ok": "failed" not in str(msg).lower(), "message": msg, "super_dash": get_super_dash_state()}
    except Exception as exc:
        return {"ok": False, "message": f"Super Dash (MSBT) failed: {exc!r}"}


def movement_super_dash_toggle() -> dict[str, Any]:
    try:
        msg = toggle_super_dash()
        return {"ok": True, "message": msg, "super_dash": get_super_dash_state()}
    except Exception as exc:
        return {"ok": False, "message": f"Super Dash (MSBT) toggle failed: {exc!r}"}


def movement_azzy_super_dash(strength: object = None) -> dict[str, Any]:
    try:
        value = None if strength is None or str(strength).strip() == "" else int(strength)
        msg = request_azzy_super_dash(value)
        return {
            "ok": "failed" not in str(msg).lower() and "load into" not in str(msg).lower(),
            "message": msg,
            "super_dash": get_azzy_super_dash_state(),
        }
    except Exception as exc:
        return {"ok": False, "message": f"Super Dash (Azzy) failed: {exc!r}"}


def movement_azzy_super_dash_toggle() -> dict[str, Any]:
    try:
        msg = toggle_azzy_super_dash()
        return {"ok": True, "message": msg, "super_dash": get_azzy_super_dash_state()}
    except Exception as exc:
        return {"ok": False, "message": f"Super Dash (Azzy) toggle failed: {exc!r}"}


def movement_zero_vault() -> dict[str, Any]:
    try:
        msg = zero_vault_power_costs_all_players()
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Zero vault cooldown failed: {exc!r}"}


def _movement_float(value: object, default: float) -> float:
    raw = str(value if value is not None else "").replace("x", "").replace("X", "").strip()
    if raw == "":
        return float(default)
    return float(raw)


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in ("1", "true", "yes", "on", "checked")


def _movement_apply_values(
    *,
    speed_scale: float = 1.0,
    walk_speed: float = 600.0,
    jump_goal: float = 198.0,
    jump_velocity: float = 840.0,
    gravity_scale: float = 1.0,
    max_step_height: float = 45.0,
    jump_count: int = 2,
    jump_off_z_factor: float = 0.5,
    walkable_floor_angle: float = 44.76508331298828,
    walkable_floor_z: float = 0.7099999785423279,
    sprint_jump_goal: float | None = 198.0,
    jump_hold_time: float | None = 0.0,
    glide_speed: float = 1200.0,
    glide_boost: float = 0.0,
    glide_air_control: float = 0.6000000238418579,
    dash_speed: float = 2500.0,
    vault_cost: float | None = None,
    double_jump_goal: float | None = 225.0,
    slide_jump_goal: float | None = 198.0,
    reset_jump_defaults: bool = False,
    scope: str = "all",
) -> dict[str, Any]:
    try:
        msg = apply_movement_advanced_to_all_players(
            speed_scale,
            walk_speed,
            jump_goal,
            jump_velocity,
            gravity_scale,
            max_step_height,
            jump_count,
            jump_off_z_factor,
            walkable_floor_angle,
            walkable_floor_z,
            sprint_jump_goal,
            jump_hold_time,
            glide_speed,
            glide_boost,
            glide_air_control,
            dash_speed,
            vault_cost,
            double_jump_goal=double_jump_goal,
            slide_jump_goal=slide_jump_goal,
            sections={"speed", "jump", "gravity", "wall", "glide", "vault", "jump_count"},
            reset_jump_defaults=reset_jump_defaults,
            scope=scope,
        )
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Apply movement settings failed: {exc!r}"}


def movement_apply_all(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    try:
        jump_goal = _movement_float(payload.get("movement_jump_height"), 198.0)
        floor_angle = _movement_float(payload.get("movement_floor_angle"), 44.76508331298828)
        individual = _truthy(payload.get("movement_individual_jump_goals"))
        scope = str(payload.get("movement_scope") or payload.get("scope") or "all").strip().lower() or "all"
        return _movement_apply_values(
            speed_scale=_movement_float(payload.get("movement_speed_scale"), 1.0),
            walk_speed=_movement_float(payload.get("movement_walk_speed"), 600.0),
            jump_goal=jump_goal,
            jump_velocity=_movement_float(payload.get("movement_jump_velocity"), 840.0),
            gravity_scale=_movement_float(payload.get("movement_gravity_scale"), 1.0),
            max_step_height=_movement_float(payload.get("movement_step_height"), 45.0),
            jump_count=_clamp_int(payload.get("movement_jump_count") or 2, 1, 50),
            jump_off_z_factor=_movement_float(payload.get("movement_jump_off_z_factor"), 0.5),
            walkable_floor_angle=floor_angle,
            walkable_floor_z=_movement_float(payload.get("movement_floor_z"), 0.7099999785423279),
            sprint_jump_goal=_movement_float(payload.get("movement_sprint_jump_goal"), jump_goal) if individual else jump_goal,
            double_jump_goal=_movement_float(payload.get("movement_double_jump_goal"), jump_goal) if individual else jump_goal,
            slide_jump_goal=_movement_float(payload.get("movement_slide_jump_goal"), jump_goal) if individual else jump_goal,
            glide_speed=_movement_float(payload.get("movement_glide_speed"), 1200.0),
            glide_boost=_movement_float(payload.get("movement_glide_boost"), 0.0),
            glide_air_control=_movement_float(payload.get("movement_glide_air_control"), 0.6000000238418579),
            dash_speed=_movement_float(payload.get("movement_dash_speed"), 2500.0),
            vault_cost=0.0 if _truthy(payload.get("movement_zero_vault_on_apply")) else None,
            scope=scope,
        )
    except Exception as exc:
        return {"ok": False, "message": f"Movement values must be numeric: {exc!r}"}


def movement_reset_all() -> dict[str, Any]:
    try:
        msg = reset_movement_advanced_all_players()
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Reset movement settings failed: {exc!r}"}


def movement_apply_preset(name: object) -> dict[str, Any]:
    key = str(name or "").strip().lower()
    presets: dict[str, dict[str, Any]] = {
        "fast": {
            "speed_scale": 5.0, "walk_speed": 3200.0, "jump_goal": 560.0, "jump_velocity": 560.0,
            "glide_speed": 2600.0, "glide_boost": 4200.0, "glide_air_control": 6.0, "dash_speed": 3000.0,
            "sprint_jump_goal": 560.0, "double_jump_goal": 560.0, "slide_jump_goal": 560.0,
        },
        "veryfast": {
            "speed_scale": 8.0, "walk_speed": 5200.0, "jump_goal": 700.0, "jump_velocity": 700.0,
            "glide_speed": 3800.0, "glide_boost": 6500.0, "glide_air_control": 10.0, "dash_speed": 5200.0,
            "sprint_jump_goal": 700.0, "double_jump_goal": 700.0, "slide_jump_goal": 700.0,
        },
        "moon": {
            "jump_goal": 1200.0, "jump_velocity": 1200.0, "gravity_scale": 0.45,
            "sprint_jump_goal": 1200.0, "double_jump_goal": 1200.0, "slide_jump_goal": 1200.0,
        },
        "wallwalk": {
            "speed_scale": 5.0, "walk_speed": 3200.0, "jump_goal": 560.0, "jump_velocity": 560.0,
            "max_step_height": 700.0, "walkable_floor_angle": 89.9, "walkable_floor_z": 0.001,
            "sprint_jump_goal": 560.0, "double_jump_goal": 560.0, "slide_jump_goal": 560.0,
        },
        "fastglide": {
            "speed_scale": 5.0, "walk_speed": 3200.0, "jump_goal": 560.0, "jump_velocity": 560.0,
            "glide_speed": 5200.0, "glide_boost": 8500.0, "glide_air_control": 14.0, "dash_speed": 4500.0,
            "sprint_jump_goal": 560.0, "double_jump_goal": 560.0, "slide_jump_goal": 560.0,
        },
    }
    if key not in presets:
        return {"ok": False, "message": f"Unknown movement preset: {name}"}
    result = _movement_apply_values(**presets[key])
    if result.get("ok"):
        result["message"] = f"Applied {key} movement preset. {result.get('message') or ''}".strip()
    return result


def movement_toggle_no_target() -> dict[str, Any]:
    global _movement_no_target_enabled
    _movement_no_target_enabled = not _movement_no_target_enabled
    try:
        msg = set_no_target(_movement_no_target_enabled)
        return {"ok": True, "message": msg}
    except Exception as exc:
        _movement_no_target_enabled = not _movement_no_target_enabled
        return {"ok": False, "message": f"Toggle no target failed: {exc!r}"}


def movement_toggle_noclip(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    global _movement_noclip_enabled
    payload = payload or {}
    scope = str(payload.get("movement_scope") or payload.get("scope") or "all").strip().lower() or "all"
    _movement_noclip_enabled = not _movement_noclip_enabled
    try:
        msg = set_noclip(_movement_noclip_enabled, scope=scope)
        return {"ok": True, "message": msg, "enabled": _movement_noclip_enabled, "scope": scope}
    except Exception as exc:
        _movement_noclip_enabled = not _movement_noclip_enabled
        return {"ok": False, "message": f"Toggle noclip failed: {exc!r}"}


def movement_toggle_force_fly(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    global _movement_force_fly_enabled
    payload = payload or {}
    scope = str(payload.get("movement_scope") or payload.get("scope") or "all").strip().lower() or "all"
    speed_raw = payload.get("fly_speed") or payload.get("movement_fly_speed")
    try:
        fly_speed = float(speed_raw) if speed_raw not in (None, "") else None
    except Exception:
        fly_speed = None
    _movement_force_fly_enabled = not _movement_force_fly_enabled
    try:
        msg = set_force_fly(_movement_force_fly_enabled, scope=scope, fly_speed=fly_speed)
        return {"ok": True, "message": msg, "enabled": _movement_force_fly_enabled, "scope": scope}
    except Exception as exc:
        _movement_force_fly_enabled = not _movement_force_fly_enabled
        return {"ok": False, "message": f"Toggle force fly failed: {exc!r}"}


def movement_set_time(value: object) -> dict[str, Any]:
    try:
        msg = set_time_dilation(_movement_float(value, 1.0))
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Set time failed: {exc!r}"}


def movement_reset_time() -> dict[str, Any]:
    return movement_set_time(1.0)


def movement_toggle_players_only() -> dict[str, Any]:
    try:
        msg = toggle_players_only()
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Players Only failed: {exc!r}"}


def movement_teleport_selected_to_slot(slot: object) -> dict[str, Any]:
    try:
        slot_idx = _clamp_int(slot, 0, 3)
    except Exception:
        return {"ok": False, "message": "Teleport target slot must be P1, P2, P3, or P4."}
    src_idx = get_selected_player_index()
    if src_idx is None:
        return {"ok": False, "message": "No selected player to teleport. Press Refresh Players and choose a target."}
    if int(src_idx) == int(slot_idx):
        return {"ok": False, "message": f"Selected player is already P{slot_idx + 1}."}
    try:
        src = _pawn_for_party_index(src_idx)
        dst = _pawn_for_party_index(slot_idx)
        if src is None:
            return {"ok": False, "message": "Teleport failed: selected player pawn not found."}
        if dst is None:
            return {"ok": False, "message": f"Teleport failed: P{slot_idx + 1} pawn not found."}
        msg = teleport_pawn_to_pawn(src, dst)
        src_name = get_selected_player_name() or f"P{int(src_idx) + 1}"
        return {"ok": True, "message": f"{msg} {src_name} -> P{slot_idx + 1}."}
    except Exception as exc:
        return {"ok": False, "message": f"Teleport selected player failed: {exc!r}"}


def _local_party_index() -> int | None:
    host = _host_player_index_value()
    if host is not None:
        return int(host)
    try:
        players = refresh_players()
        if players:
            return int(players[0].get("index", 0))
    except Exception:
        pass
    return 0


def movement_teleport_selected_to_me() -> dict[str, Any]:
    """Teleport selected party player to local/host pawn."""
    src_idx = get_selected_player_index()
    me_idx = _local_party_index()
    if src_idx is None:
        return {"ok": False, "message": "No selected player to teleport."}
    if me_idx is None:
        return {"ok": False, "message": "Local player index unavailable."}
    if int(src_idx) == int(me_idx):
        return {"ok": False, "message": "Selected player is already you."}
    try:
        src = _pawn_for_party_index(src_idx)
        dst = _pawn_for_party_index(me_idx)
        if src is None or dst is None:
            return {"ok": False, "message": "Teleport failed: missing pawn."}
        msg = teleport_pawn_to_pawn(src, dst)
        return {"ok": True, "message": f"{msg} Selected -> me."}
    except Exception as exc:
        return {"ok": False, "message": f"Teleport selected to me failed: {exc!r}"}


def movement_teleport_me_to_selected() -> dict[str, Any]:
    """Teleport local/host pawn to selected party player."""
    dst_idx = get_selected_player_index()
    me_idx = _local_party_index()
    if dst_idx is None:
        return {"ok": False, "message": "No selected player destination."}
    if me_idx is None:
        return {"ok": False, "message": "Local player index unavailable."}
    if int(dst_idx) == int(me_idx):
        return {"ok": False, "message": "Already at selected player."}
    try:
        src = _pawn_for_party_index(me_idx)
        dst = _pawn_for_party_index(dst_idx)
        if src is None or dst is None:
            return {"ok": False, "message": "Teleport failed: missing pawn."}
        msg = teleport_pawn_to_pawn(src, dst)
        return {"ok": True, "message": f"{msg} Me -> selected."}
    except Exception as exc:
        return {"ok": False, "message": f"Teleport me to selected failed: {exc!r}"}


def movement_teleport_all_to_me() -> dict[str, Any]:
    """Teleport every other live party pawn to local/host."""
    me_idx = _local_party_index()
    if me_idx is None:
        return {"ok": False, "message": "Local player index unavailable."}
    try:
        dst = _pawn_for_party_index(me_idx)
        if dst is None:
            return {"ok": False, "message": "Local pawn not found."}
        players = refresh_players()
        ok_n = 0
        fail_n = 0
        for row in players:
            try:
                idx = int(row.get("index"))
            except Exception:
                continue
            if idx == int(me_idx):
                continue
            src = _pawn_for_party_index(idx)
            if src is None:
                fail_n += 1
                continue
            try:
                teleport_pawn_to_pawn(src, dst)
                ok_n += 1
            except Exception:
                fail_n += 1
        return {"ok": True, "message": f"Teleported {ok_n} player(s) to you (miss={fail_n})."}
    except Exception as exc:
        return {"ok": False, "message": f"Teleport all to me failed: {exc!r}"}


def combat_tuning_apply(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        msg = _apply_combat_tuning(payload or {})
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Combat tuning apply failed: {exc!r}"}


def _chaos_selected_pc() -> tuple[Any | None, str]:
    """Resolve selected party PC (host or other) for Streamer Chaos actions."""
    refresh_players()
    idx = get_selected_player_index()
    name = get_selected_player_name()
    if idx is None and not name:
        auto = ensure_selected_player(prefer_host=True)
        if not auto.get("ok"):
            return None, "No party player selected."
        idx = get_selected_player_index()
        name = get_selected_player_name()
    label = _selected_player_label(idx, name)
    pc = _party_controller_for_index(idx)
    if pc is None:
        return None, f"Could not resolve live controller for {label}."
    return pc, label


def _chaos_run(effect_name: str, runner: Any, *args: Any) -> dict[str, Any]:
    pc, label = _chaos_selected_pc()
    if pc is None:
        return {"ok": False, "message": label}
    try:
        msg = runner(pc, *args) if args else runner(pc)
    except Exception as exc:
        return {"ok": False, "message": f"{effect_name} failed for {label}: {exc!r}"}
    ok = streamer_chaos.result_ok(str(msg))
    return {"ok": ok, "message": f"{effect_name} → {label}: {msg}"}


def reset_skills() -> dict[str, Any]:
    """Refund regular skill points for the local host pawn only. No party target."""
    host_ok, host_msg = _challenge_is_host()
    if not host_ok:
        return {"ok": False, "message": "Reset Skill Tree is host / listen only — do not run as a join client."}
    try:
        pc = get_pc()
    except Exception as exc:
        return {"ok": False, "message": f"Reset skills host guard could not resolve host: {exc!r}"}
    if pc is None:
        return {"ok": False, "message": "Reset skills: load into a character first."}
    try:
        msg = _reset_skills_for_pc(pc)
    except Exception as exc:
        return {"ok": False, "message": f"Reset skills failed for host: {exc!r}"}
    ok = str(msg).lower().startswith("reset skills ok")
    return {"ok": ok, "message": f"Reset skills → host only: {msg}", "host_only": True}


def chaos_launch(z: object = None) -> dict[str, Any]:
    try:
        z_boost = (
            float(z)
            if z is not None and str(z).strip() != ""
            else streamer_chaos._DEFAULT_LAUNCH_Z
        )
    except Exception:
        z_boost = streamer_chaos._DEFAULT_LAUNCH_Z
    return _chaos_run("Launch", streamer_chaos.launch_for_pc, z_boost)


def chaos_drop_backpack() -> dict[str, Any]:
    """Public backpack drop-all action: always target the local host controller."""
    try:
        pc = get_pc()
    except Exception as exc:
        return {"ok": False, "message": f"Drop backpack host guard could not resolve host: {exc!r}"}
    if pc is None:
        return {"ok": False, "message": "Drop backpack host guard could not resolve the host controller."}
    try:
        msg = streamer_chaos.drop_backpack_for_pc(pc)
    except Exception as exc:
        return {"ok": False, "message": f"Drop backpack failed for host: {exc!r}"}
    ok = streamer_chaos.result_ok(str(msg))
    return {"ok": ok, "message": f"Drop backpack → host only: {msg}", "host_only": True}


def chaos_drop_backpack_targeted() -> dict[str, Any]:
    """Dev Tools backpack drop-all action: honor the selected party target."""
    return _chaos_run("Drop backpack", streamer_chaos.drop_backpack_for_pc)


def chaos_empty_backpack(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Refresh the target's inventory, snapshot backpack @U serials, then EmptyContainer."""
    payload = payload or {}
    pc, label = _chaos_selected_pc()
    if pc is None:
        return {"ok": False, "message": label}
    snapshot = _capture_deleted_backpack_snapshot(payload)
    try:
        msg = streamer_chaos.empty_backpack_for_pc(pc)
    except Exception as exc:
        return {
            "ok": False,
            "message": f"Empty backpack failed for {label}: {exc!r}",
            "deleted_backpack": _deleted_backpack_status(),
        }
    ok = streamer_chaos.result_ok(str(msg))
    captured = 0
    if ok:
        captured = _store_deleted_backpack_snapshot(snapshot)
        extra = (
        f" captured {captured} serial(s) for undo"
        if captured
        else " (nothing captured for undo — inventory read failed or backpack was empty)"
    )
    read_err = str(snapshot.get("read_error") or "").strip()
    if read_err and not captured:
        extra += f" Read failed: {read_err}"
        if "ZipImportError" in read_err or "bad local file header" in read_err:
            extra += " Quit Borderlands 4 fully, then recopy MattsSDKBoostingTools.sdkmod while the game is closed."
    return {
        "ok": ok,
        "message": f"Empty backpack → {label}: {msg}{extra}",
        "deleted_backpack": _deleted_backpack_status(),
        "captured_count": captured,
        "serials": list(snapshot.get("serials") or []) if captured else [],
    }


_BACKPACK_DELETE_CAP = 2000
_backpack_delete_memory: dict[int, dict[str, Any]] = {}


def _deleted_backpack_status() -> dict[str, Any]:
    players = []
    items = 0
    for idx in sorted(_backpack_delete_memory):
        entry = _backpack_delete_memory[idx]
        count = int(entry.get("count") or len(entry.get("serials") or []))
        items += count
        players.append({
            "index": int(idx),
            "name": str(entry.get("name") or f"P{int(idx) + 1}"),
            "count": count,
        })
    return {
        "players": players,
        "player_count": len(players),
        "item_count": items,
    }


def _serials_from_payload(payload: dict[str, Any] | None) -> list[str]:
    payload = payload or {}
    raw = payload.get("serials") or payload.get("serial_text") or payload.get("serials_text") or ""
    values: list[str] = []
    if isinstance(raw, str):
        values.extend(part.strip() for part in raw.replace("\r", "\n").split("\n") if part.strip())
        if len(values) == 1 and "," in values[0]:
            values = [part.strip() for part in values[0].split(",") if part.strip()]
    elif isinstance(raw, (list, tuple)):
        values.extend(str(item).strip() for item in raw if str(item).strip())
    out: list[str] = []
    seen: set[str] = set()
    for item in values:
        if not item.startswith("@U") or item in seen:
            continue
        seen.add(item)
        out.append(item)
        if len(out) >= _BACKPACK_DELETE_CAP:
            break
    return out


def _capture_deleted_backpack_snapshot(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Refresh live inventory for the selected player, then copy backpack serials."""
    refresh_players()
    idx = get_selected_player_index()
    name = get_selected_player_name() or ""
    serials = _serials_from_payload(payload)
    read_error = ""
    if idx is None:
        return {"index": None, "name": name, "serials": serials, "count": len(serials), "read_error": "No party player selected."}
    if not serials:
        try:
            from . import item_serial_reader

            snapshot = item_serial_reader.read_inventory_for_party_index(
                idx,
                player_name=name or f"Player {idx}",
                backpack_limit=max(_BACKPACK_DELETE_CAP, 2000),
            )
            rows = list(snapshot.get("backpack") or [])
            seen: set[str] = set()
            for entry in rows:
                serial = str((entry or {}).get("serial") or "").strip()
                if not serial.startswith("@U") or serial in seen:
                    continue
                seen.add(serial)
                serials.append(serial)
                if len(serials) >= _BACKPACK_DELETE_CAP:
                    break
        except Exception as exc:
            read_error = f"{type(exc).__name__}: {exc}"
            serials = []
    return {
        "index": int(idx),
        "name": name or f"P{int(idx) + 1}",
        "serials": serials,
        "count": len(serials),
        "read_error": read_error,
    }


def _store_deleted_backpack_snapshot(snapshot: dict[str, Any] | None) -> int:
    if not snapshot:
        return 0
    idx = snapshot.get("index")
    serials = [str(item).strip() for item in (snapshot.get("serials") or []) if str(item).strip()]
    if idx is None or not serials:
        return 0
    _backpack_delete_memory[int(idx)] = {
        "index": int(idx),
        "name": str(snapshot.get("name") or f"P{int(idx) + 1}"),
        "serials": serials,
        "count": len(serials),
    }
    return len(serials)


def chaos_undo_empty_backpack(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Give stored deleted-backpack serials to the current target player."""
    payload = payload or {}
    pc, label = _chaos_selected_pc()
    if pc is None:
        return {"ok": False, "message": label, "deleted_backpack": _deleted_backpack_status()}
    serials = _serials_from_payload(payload)
    if not serials:
        idx = get_selected_player_index()
        if idx is not None and int(idx) in _backpack_delete_memory:
            serials = list(_backpack_delete_memory[int(idx)].get("serials") or [])
        elif _backpack_delete_memory:
            last_key = sorted(_backpack_delete_memory)[-1]
            serials = list(_backpack_delete_memory[last_key].get("serials") or [])
    serials = [str(item).strip() for item in serials if str(item).strip().startswith("@U")]
    if not serials:
        return {
            "ok": False,
            "message": "No deleted backpack memory to restore. Empty Backpack first after inventory refresh.",
            "deleted_backpack": _deleted_backpack_status(),
        }
    result = _deliver_serials_with_target(serials, "selected")
    result["deleted_backpack"] = _deleted_backpack_status()
    if result.get("ok"):
        result["message"] = (
            f"Undo empty backpack → {label}: queued {len(serials)} serial(s). "
            f"{result.get('message') or ''}"
        ).strip()
    return result


def chaos_clear_empty_backpack_memory() -> dict[str, Any]:
    status = _deleted_backpack_status()
    _backpack_delete_memory.clear()
    players = int(status.get("player_count") or 0)
    items = int(status.get("item_count") or 0)
    if not players:
        return {
            "ok": True,
            "message": "Deleted backpack memory was already empty.",
            "deleted_backpack": _deleted_backpack_status(),
        }
    return {
        "ok": True,
        "message": f"Cleared deleted backpack memory ({players} player(s), {items} item(s)).",
        "deleted_backpack": _deleted_backpack_status(),
    }


def chaos_kill() -> dict[str, Any]:
    return _chaos_run("Kill", streamer_chaos.kill_for_pc)


def chaos_ffyl() -> dict[str, Any]:
    return _chaos_run("FFYL", streamer_chaos.ffyl_for_pc)


def chaos_invert_look(seconds: object = None) -> dict[str, Any]:
    try:
        secs = (
            float(seconds)
            if seconds is not None and str(seconds).strip() != ""
            else streamer_chaos._DEFAULT_INVERT_SECS
        )
    except Exception:
        secs = streamer_chaos._DEFAULT_INVERT_SECS
    return _chaos_run("Invert look", streamer_chaos.invert_look_for_pc, secs)


def chaos_lock_look(seconds: object = None) -> dict[str, Any]:
    try:
        secs = (
            float(seconds)
            if seconds is not None and str(seconds).strip() != ""
            else streamer_chaos._DEFAULT_LOCK_SECS
        )
    except Exception:
        secs = streamer_chaos._DEFAULT_LOCK_SECS
    return _chaos_run("Lock look", streamer_chaos.lock_look_for_pc, secs)


def chaos_lock_move(seconds: object = None) -> dict[str, Any]:
    try:
        secs = (
            float(seconds)
            if seconds is not None and str(seconds).strip() != ""
            else streamer_chaos._DEFAULT_LOCK_SECS
        )
    except Exception:
        secs = streamer_chaos._DEFAULT_LOCK_SECS
    return _chaos_run("Lock move", streamer_chaos.lock_move_for_pc, secs)


def chaos_lock_both(seconds: object = None) -> dict[str, Any]:
    try:
        secs = (
            float(seconds)
            if seconds is not None and str(seconds).strip() != ""
            else streamer_chaos._DEFAULT_LOCK_SECS
        )
    except Exception:
        secs = streamer_chaos._DEFAULT_LOCK_SECS
    return _chaos_run("Lock both", streamer_chaos.lock_both_for_pc, secs)


def chaos_unlock() -> dict[str, Any]:
    return _chaos_run("Unlock", streamer_chaos.unlock_for_pc)


def combat_tuning_reapply() -> dict[str, Any]:
    try:
        msg = _reapply_combat_tuning()
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Combat tuning reapply failed: {exc!r}"}


def combat_tuning_reset(scope: object = "local") -> dict[str, Any]:
    try:
        msg = _reset_combat_tuning(str(scope or "local"))
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Combat tuning reset failed: {exc!r}"}


def vehicle_preset_apply(name: object, scope: object = "local") -> dict[str, Any]:
    try:
        msg = _apply_vehicle_preset(str(name or ""), scope=str(scope or "local"))
        ok = "Unknown vehicle preset" not in msg
        return {"ok": ok, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Vehicle preset failed: {exc!r}"}


def vehicle_spawn(name: object, scope: object = "local") -> dict[str, Any]:
    try:
        msg = _spawn_personal_vehicle(str(name or ""), scope=str(scope or "local"))
        ok = "failed" not in msg.lower() or "requested" in msg.lower()
        return {"ok": ok, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Vehicle spawn failed: {exc!r}"}


def vehicle_catalog() -> dict[str, Any]:
    try:
        rows = _list_vehicle_catalog()
        presets = _list_vehicle_presets()
        return {
            "ok": True,
            "message": f"{len(rows)} vehicle(s), {len(presets)} preset(s).",
            "catalog": rows,
            "presets": presets,
        }
    except Exception as exc:
        return {"ok": False, "message": f"Vehicle catalog failed: {exc!r}"}


def movement_infinite_jump_refresh() -> dict[str, Any]:
    try:
        msg = refresh_jump_counts_all_players()
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Infinite jump refresh failed: {exc!r}"}


def movement_infinite_jump_all(enabled: bool) -> dict[str, Any]:
    try:
        msg = set_infinite_jump_all(bool(enabled))
        return {"ok": True, "message": msg, "enabled": bool(enabled)}
    except Exception as exc:
        return {"ok": False, "message": f"Infinite jump all toggle failed: {exc!r}"}


def movement_infinite_jump_toggle(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    scope = str(payload.get("movement_scope") or payload.get("scope") or "all").strip().lower() or "all"
    try:
        msg, enabled = toggle_infinite_jump_for_scope(scope)
        return {"ok": True, "message": msg, "enabled": bool(enabled), "scope": scope}
    except Exception as exc:
        return {"ok": False, "message": f"Infinite jump toggle failed: {exc!r}"}


def movement_infinite_jump_selected(index_or_name: object | None = None) -> dict[str, Any]:
    try:
        idx: int | None
        raw = "" if index_or_name is None else str(index_or_name).strip()
        if raw:
            try:
                idx = int(raw.split("|", 1)[0].strip())
            except Exception:
                result = set_target_player(raw)
                if not result.get("ok"):
                    return result
                idx = get_selected_player_index()
        else:
            idx = get_selected_player_index()
        if idx is None:
            return {"ok": False, "message": "No selected player for Infinite Jump. Press Refresh Players and choose a target."}
        msg = toggle_infinite_jump_for_index(int(idx))
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Infinite jump selected toggle failed: {exc!r}"}


def movement_infinite_jump_set_selected(index_or_name: object | None, enabled: bool) -> dict[str, Any]:
    try:
        result = set_target_player(index_or_name)
        if not result.get("ok"):
            return result
        idx = get_selected_player_index()
        if idx is None:
            return {"ok": False, "message": "No selected player for Infinite Jump. Press Refresh Players and choose a target."}
        msg = set_infinite_jump_for_index(int(idx), bool(enabled))
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Infinite jump selected set failed: {exc!r}"}


def _rarity_current_gamestate() -> object | None:
    try:
        viewport = getattr(ENGINE, "GameViewport", None)
        world = getattr(viewport, "World", None) if viewport is not None else None
        return getattr(world, "GameState", None) if world is not None else None
    except Exception:
        return None


def _rarity_state_for_gamestate(gs: object | None) -> object | None:
    if gs is None:
        return None
    for attr in ("RarityState", "RarityModifier", "RarityModifiers", "GameRarityState"):
        try:
            candidate = getattr(gs, attr, None)
            if candidate is not None:
                return candidate
        except Exception:
            pass
    return None


def _rarity_get_modifier(state: object | None, fields: tuple[str, ...]) -> object | None:
    if state is None:
        return None
    for field in fields:
        try:
            mod = getattr(state, field, None)
            if mod is not None:
                return mod
        except Exception:
            pass
    return None


def _rarity_read_float(mod: object | None, name: str) -> float | None:
    if mod is None:
        return None
    try:
        if hasattr(mod, name):
            return float(getattr(mod, name))
    except Exception:
        return None
    return None


def _rarity_snapshot_modifier(mod: object | None) -> dict[str, float]:
    snapshot: dict[str, float] = {}
    for name in ("Value", "CurrentValue", "Current", "BaseValue", "Base", "InitialValue"):
        value = _rarity_read_float(mod, name)
        if value is not None:
            snapshot[name] = value
    return snapshot


def _rarity_capture_baseline(state: object | None) -> None:
    if state is None or _rarity_baseline:
        return
    for key, _label, fields in RARITY_ROWS:
        mod = _rarity_get_modifier(state, fields)
        snapshot = _rarity_snapshot_modifier(mod)
        if snapshot:
            _rarity_baseline[key] = snapshot


def _rarity_baseline_value(key: str) -> float:
    snapshot = _rarity_baseline.get(key, {})
    for name in ("Value", "CurrentValue", "Current", "BaseValue", "Base", "InitialValue"):
        if name in snapshot:
            return float(snapshot[name])
    return 1.0


def _rarity_set_float(mod: object | None, value: float) -> int:
    if mod is None:
        return 0
    writes = 0
    value = max(0.0, min(1.0, float(value)))
    for name in ("Value", "CurrentValue", "Current", "BaseValue", "Base"):
        try:
            if hasattr(mod, name):
                setattr(mod, name, value)
                writes += 1
        except Exception:
            pass
    for name in ("SetValue", "SetBaseValue", "SetCurrentValue"):
        try:
            fn = getattr(mod, name, None)
            if callable(fn):
                fn(value)
                writes += 1
        except Exception:
            pass
    return writes


def _rarity_restore_snapshot(mod: object | None, snapshot: dict[str, float]) -> int:
    if mod is None:
        return 0
    writes = 0
    for name, value in snapshot.items():
        try:
            if hasattr(mod, name):
                setattr(mod, name, float(value))
                writes += 1
        except Exception:
            pass
    method_values = {
        "SetValue": snapshot.get("Value", snapshot.get("CurrentValue", snapshot.get("Current"))),
        "SetBaseValue": snapshot.get("BaseValue", snapshot.get("Base")),
        "SetCurrentValue": snapshot.get("CurrentValue", snapshot.get("Current", snapshot.get("Value"))),
    }
    for name, value in method_values.items():
        if value is None:
            continue
        try:
            fn = getattr(mod, name, None)
            if callable(fn):
                fn(float(value))
                writes += 1
        except Exception:
            pass
    return writes


def _rarity_save_settings() -> None:
    global _rarity_revision
    try:
        _rarity_revision = int(_rarity_revision) + 1
    except Exception:
        _rarity_revision = 1
    try:
        save_extra_settings(
            rarity_weights={
                key: float(max(0.0, min(1.0, float(_rarity_weights.get(key, 1.0)))))
                for key, _label, _fields in RARITY_ROWS
            }
        )
    except Exception:
        pass


def get_rarity_revision() -> int:
    return int(_rarity_revision or 0)


def _rarity_find_blimgui_panel() -> object | None:
    for name in (f"{__package__}.blimgui_panel", "MattsSDKBoostingTools.blimgui_panel"):
        panel = sys.modules.get(name)
        if panel is not None:
            return panel
    return None


def _rarity_sync_optional_blimgui(*, reset_auto_reapply: bool = False) -> None:
    """Push backend weights into the optional BLImGui panel so both UIs stay aligned."""
    panel = _rarity_find_blimgui_panel()
    if panel is None:
        return
    if reset_auto_reapply:
        try:
            setattr(panel, "_rarity_auto_reapply", False)
            setattr(panel, "_rarity_reapply_until", 0.0)
            setattr(panel, "_rarity_reapply_next_try", 0.0)
        except Exception:
            pass
    try:
        panel_weights = getattr(panel, "_rarity_weights", None)
        if isinstance(panel_weights, dict):
            for key, _label, _fields in RARITY_ROWS:
                panel_weights[key] = float(max(0.0, min(1.0, float(_rarity_weights.get(key, 1.0)))))
    except Exception:
        pass
    try:
        # Prefer backend save; still call panel saver when present so its status stays coherent.
        save_settings = getattr(panel, "_rarity_save_settings", None)
        if callable(save_settings):
            save_settings()
    except Exception:
        pass


def _rarity_sync_optional_blimgui_reset() -> None:
    for key, _label, _fields in RARITY_ROWS:
        _rarity_weights[key] = 1.0
    _rarity_save_settings()
    _rarity_sync_optional_blimgui(reset_auto_reapply=True)


def _rarity_apply_current() -> dict[str, Any]:
    state = _rarity_state_for_gamestate(_rarity_current_gamestate())
    if state is None:
        _rarity_save_settings()
        _rarity_sync_optional_blimgui()
        return {"ok": False, "message": "No GameState.RarityState found yet. Load into a world and try again."}
    _rarity_capture_baseline(state)
    writes = 0
    parts: list[str] = []
    for key, label, fields in RARITY_ROWS:
        target = max(0.0, min(1.0, float(_rarity_weights.get(key, 1.0))))
        writes += _rarity_set_float(_rarity_get_modifier(state, fields), target)
        parts.append(f"{label}={int(round(target * 100.0))}%")
    _rarity_save_settings()
    _rarity_sync_optional_blimgui()
    return {"ok": True, "message": "Rarity drop weights applied: " + ", ".join(parts) + f". Writes: {writes}."}


def get_rarity_weights() -> dict[str, float]:
    """Current rarity weight multipliers (1.0 = 100% vanilla)."""
    return {key: float(_rarity_weights.get(key, 1.0)) for key, _label, _fields in RARITY_ROWS}


def rarity_apply(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    for key, _label, _fields in RARITY_ROWS:
        try:
            if key in payload:
                _rarity_weights[key] = max(0.0, min(1.0, float(payload[key])))
            pct_key = f"rarity_{key}_percent"
            if pct_key in payload:
                _rarity_weights[key] = max(0.0, min(1.0, float(payload[pct_key]) / 100.0))
        except Exception:
            return {"ok": False, "message": f"Rarity value for {key} must be numeric."}
    return _rarity_apply_current()


def rarity_reset() -> dict[str, Any]:
    state = _rarity_state_for_gamestate(_rarity_current_gamestate())
    for key, _label, _fields in RARITY_ROWS:
        _rarity_weights[key] = 1.0
    if state is None:
        _rarity_save_settings()
        _rarity_sync_optional_blimgui(reset_auto_reapply=True)
        return {"ok": False, "message": "No GameState.RarityState found yet. Rarity override state was cleared; load into a world and try again."}
    writes = 0
    parts: list[str] = []
    for key, label, fields in RARITY_ROWS:
        writes += _rarity_set_float(_rarity_get_modifier(state, fields), 1.0)
        parts.append(f"{label}=100%")
    _rarity_save_settings()
    _rarity_sync_optional_blimgui(reset_auto_reapply=True)
    return {"ok": True, "message": "Rarity drop weights reset to 100% and live override is off: " + ", ".join(parts) + f". Writes: {writes}."}


def rarity_only(allowed_key: object) -> dict[str, Any]:
    allowed = str(allowed_key or "").strip().lower()
    valid = {key for key, _label, _fields in RARITY_ROWS}
    if allowed not in valid:
        return {"ok": False, "message": f"Unsupported rarity key: {allowed_key}"}
    for key, _label, _fields in RARITY_ROWS:
        _rarity_weights[key] = 1.0 if key == allowed else 0.0
    return _rarity_apply_current()


def get_last_read_serials() -> dict[str, Any]:
    return {
        "title": _last_read_serials_title,
        "entries": [dict(e) for e in _last_read_serials],
        "clipboard_ok": bool(_last_read_serials_clipboard),
        "dump_paths": list(_last_read_serials_dump_paths),
        "serial_text": serial_text,
    }


def _store_read_serials(
    entries: list[dict[str, Any]],
    *,
    title: str,
    empty_detail: str = "",
    clipboard: bool = True,
    dump: bool = True,
) -> dict[str, Any]:
    """Persist read results, optionally copy to clipboard / dump to disk, seed serial_text."""
    global serial_text, _last_read_serials, _last_read_serials_title
    global _last_read_serials_clipboard, _last_read_serials_dump_paths
    from . import item_serial_reader

    cleaned = [dict(e) for e in entries if str(e.get("serial") or "").startswith("@U")]
    _last_read_serials = cleaned
    _last_read_serials_title = str(title or "")
    text = item_serial_reader.entries_to_serial_text(cleaned)
    serial_text = text
    clipboard_ok = False
    if text and clipboard:
        clipboard_ok = bool(item_serial_reader.write_clipboard_text(text))
    _last_read_serials_clipboard = clipboard_ok
    dump_paths = (
        item_serial_reader.write_serial_dump(cleaned, title=title)
        if cleaned and dump
        else []
    )
    _last_read_serials_dump_paths = dump_paths
    summaries = [str(e.get("summary") or e.get("label") or "Item") for e in cleaned]
    if not cleaned:
        detail = (empty_detail or "").strip()
        message = f"{title}: no readable @U serials found."
        if detail:
            message = f"{message} ({detail})"
        return {
            "ok": False,
            "message": message,
            "open_serial_pick": False,
            "read_serials": get_last_read_serials(),
            "empty_detail": detail,
        }
    if clipboard:
        clip_note = "copied to clipboard" if clipboard_ok else "clipboard unavailable — see toast/log/dump"
        message = f"{title}: {len(cleaned)} serial(s) ({', '.join(summaries[:6])}); {clip_note}."
    else:
        message = f"{title}: {len(cleaned)} serial(s) ({', '.join(summaries[:6])})."
    return {
        "ok": True,
        "message": message,
        "open_serial_pick": True,
        "read_serials": get_last_read_serials(),
        "serial_text": serial_text,
    }


def _reading_target_label(idx: int | None, name: str) -> str:
    """Footer/status label: Reading: PlayerName (P2)."""
    who = (name or "").strip() or (f"Player {idx}" if idx is not None else "player")
    if idx is None:
        return f"Reading: {who}"
    return f"Reading: {who} (P{int(idx) + 1})"


def _serial_read_host_note(target_index: int | None) -> str:
    """Soft hint when reading another player off-host (inventory may be incomplete)."""
    if target_index is None:
        return ""
    try:
        from .party_helpers import _gbc_is_listen_host_world, _gbc_session_world_and_gamestate

        world, _gs = _gbc_session_world_and_gamestate()
        if world is not None and _gbc_is_listen_host_world(world):
            return ""
    except Exception:
        pass
    host_idx = _host_player_index_value()
    if host_idx is not None and int(target_index) == int(host_idx):
        return ""
    # Joined client reading a remote party member — local memory often lacks full identities.
    return " (best on listen host; clients often cannot see other players' full inventory serials)"


def _ensure_inventory_read_target(target_player: object | None = None) -> dict[str, Any]:
    """Honor explicit target_player when provided; else keep / auto-pick selected party player."""
    raw = "" if target_player is None else str(target_player).strip()
    if raw:
        selected = set_target_player(target_player)
        if not selected.get("ok"):
            return {
                "ok": False,
                "message": str(selected.get("message") or "Could not set target player."),
                "needs_player": True,
            }
        return selected
    return ensure_selected_player(prefer_host=True)


def _zipimport_reload_hint(exc: BaseException) -> str:
    name = type(exc).__name__
    detail = str(exc)
    if name != "ZipImportError" and "bad local file header" not in detail:
        return ""
    return (
        " The .sdkmod zip was replaced while Borderlands 4 still had it mapped. "
        "Fully quit the game, copy MattsSDKBoostingTools.sdkmod into sdk_mods while closed, then relaunch."
    )


def read_equipped_serials(target_player: object | None = None) -> dict[str, Any]:
    """Read equipped-slot @U serials for the selected party player (P1–P4 target)."""
    ensured = _ensure_inventory_read_target(target_player)
    if not ensured.get("ok"):
        return {
            "ok": False,
            "message": str(ensured.get("message") or "No party player selected."),
            "needs_player": True,
        }
    idx = get_selected_player_index()
    name = get_selected_player_name()
    reading = _reading_target_label(idx, name)
    try:
        from . import item_serial_reader

        entries = item_serial_reader.read_equipped_serials_for_party_index(
            idx,
            player_name=name or f"Player {idx}",
        )
        empty_detail = ""
        if not entries:
            empty_detail = item_serial_reader.empty_read_reason(
                item_serial_reader.get_last_read_diagnostics("equipped"),
                mode="equipped",
            )
    except Exception as exc:
        return {"ok": False, "message": f"{reading} — Read equipped serials failed: {exc!r}{_zipimport_reload_hint(exc)}"}
    title = f"{reading} — Equipped"
    result = _store_read_serials(entries, title=title, empty_detail=empty_detail)
    note = _serial_read_host_note(idx)
    if note and not result.get("ok"):
        result["message"] = str(result.get("message") or "") + note
    elif note and result.get("ok"):
        # Keep success message clean; note only when empty/failed for guests.
        pass
    result["reading"] = reading
    result["selected_player"] = name
    result["selected_player_index"] = idx
    return result


def read_backpack_serials(target_player: object | None = None) -> dict[str, Any]:
    """Read backpack/inventory @U serials for the selected party player (capped list)."""
    ensured = _ensure_inventory_read_target(target_player)
    if not ensured.get("ok"):
        return {
            "ok": False,
            "message": str(ensured.get("message") or "No party player selected."),
            "needs_player": True,
        }
    idx = get_selected_player_index()
    name = get_selected_player_name()
    reading = _reading_target_label(idx, name)
    try:
        from . import item_serial_reader

        entries = item_serial_reader.read_backpack_serials_for_party_index(
            idx,
            player_name=name or f"Player {idx}",
        )
        empty_detail = ""
        if not entries:
            empty_detail = item_serial_reader.empty_read_reason(
                item_serial_reader.get_last_read_diagnostics("backpack"),
                mode="backpack",
            )
    except Exception as exc:
        return {"ok": False, "message": f"{reading} — Read backpack serials failed: {exc!r}{_zipimport_reload_hint(exc)}"}
    title = f"{reading} — Backpack"
    result = _store_read_serials(entries, title=title, empty_detail=empty_detail)
    note = _serial_read_host_note(idx)
    if note and not result.get("ok"):
        result["message"] = str(result.get("message") or "") + note
    result["reading"] = reading
    result["selected_player"] = name
    result["selected_player_index"] = idx
    return result


def read_inventory(target_player: object | None = None) -> dict[str, Any]:
    """Read equipped + backpack inventory for the selected party player (browser payload)."""
    ensured = _ensure_inventory_read_target(target_player)
    if not ensured.get("ok"):
        return {
            "ok": False,
            "message": str(ensured.get("message") or "No party player selected."),
            "needs_player": True,
        }
    idx = get_selected_player_index()
    name = get_selected_player_name()
    reading = _reading_target_label(idx, name)
    try:
        from . import item_serial_reader

        snapshot = item_serial_reader.read_inventory_for_party_index(
            idx,
            player_name=name or f"Player {idx}",
        )
    except Exception as exc:
        return {"ok": False, "message": f"{reading} — Read inventory failed: {exc!r}{_zipimport_reload_hint(exc)}"}

    equipped = list(snapshot.get("equipped") or [])
    backpack = list(snapshot.get("backpack") or [])
    combined = equipped + backpack
    title = f"{reading} — Inventory"
    empty_detail = ""
    if not combined:
        equipped_diag = item_serial_reader.get_last_read_diagnostics("equipped")
        inv_diag = item_serial_reader.get_last_read_diagnostics("inventory")
        empty_detail = item_serial_reader.empty_read_reason(
            equipped_diag if equipped_diag.get("rows") else inv_diag,
            mode="backpack",
        )
    # Avoid dumping / clipboard-pasting hundreds of serials on every browser refresh.
    # Cache equipped (or a tiny backpack sample) for the serial picker — do not echo the
    # full backpack twice on the wire (inventory.* already carries the browser payload).
    cache_entries = equipped if equipped else backpack[:12]
    result = _store_read_serials(
        cache_entries,
        title=title,
        empty_detail=empty_detail if not combined else "",
        clipboard=False,
        dump=False,
    )
    # Browser success is based on the full snapshot, not the lean picker cache.
    if combined:
        result["ok"] = True
        result["open_serial_pick"] = False
        result.pop("serial_text", None)
        # Keep a count-only read_serials stub so clients do not re-download megabytes.
        cached = get_last_read_serials()
        result["read_serials"] = {
            "title": str(cached.get("title") or title),
            "entries": list(cached.get("entries") or []),
            "clipboard_ok": False,
            "dump_paths": [],
            "count": len(combined),
        }
    note = _serial_read_host_note(idx)
    if note and not result.get("ok"):
        result["message"] = str(result.get("message") or "") + note
    result["reading"] = reading
    result["selected_player"] = name
    result["selected_player_index"] = idx
    result["inventory"] = {
        "equipped": equipped,
        "backpack": backpack,
        "total_rows": int(snapshot.get("total_rows") or 0),
        "equipped_count": int(snapshot.get("equipped_count") or len(equipped)),
        "backpack_count": int(snapshot.get("backpack_count") or len(backpack)),
        "backpack_cap": int(snapshot.get("backpack_cap") or 0),
        "truncated": bool(snapshot.get("truncated")),
    }
    if result.get("ok"):
        trunc = " (capped)" if snapshot.get("truncated") else ""
        result["message"] = (
            f"{title}: {len(equipped)} equipped, {len(backpack)} backpack{trunc}."
        )
    return result


def copy_read_serial(index: object = 0) -> dict[str, Any]:
    """Copy one previously-read serial to clipboard and seed serial_text."""
    global serial_text, _last_read_serials_clipboard
    from . import item_serial_reader

    try:
        idx = int(index)
    except Exception:
        idx = 0
    if idx < 0 or idx >= len(_last_read_serials):
        return {"ok": False, "message": "No read serial at that index. Run Read Equipped / Backpack first."}
    entry = dict(_last_read_serials[idx])
    serial = str(entry.get("serial") or "")
    if not serial.startswith("@U"):
        return {"ok": False, "message": "Selected entry has no @U serial."}
    serial_text = serial
    clipboard_ok = bool(item_serial_reader.write_clipboard_text(serial))
    _last_read_serials_clipboard = clipboard_ok
    summary = str(entry.get("summary") or entry.get("label") or "Item")
    if clipboard_ok:
        return {
            "ok": True,
            "message": f"Copied {summary} serial to clipboard.",
            "serial_text": serial_text,
            "read_serials": get_last_read_serials(),
        }
    return {
        "ok": True,
        "message": f"{summary} serial ready in serial_text/log (clipboard unavailable).",
        "serial_text": serial_text,
        "read_serials": get_last_read_serials(),
    }


def copy_all_read_serials() -> dict[str, Any]:
    global serial_text, _last_read_serials_clipboard
    from . import item_serial_reader

    if not _last_read_serials:
        return {"ok": False, "message": "No read serials cached. Run Read Equipped / Backpack first."}
    text = item_serial_reader.entries_to_serial_text(_last_read_serials)
    serial_text = text
    clipboard_ok = bool(item_serial_reader.write_clipboard_text(text)) if text else False
    _last_read_serials_clipboard = clipboard_ok
    if clipboard_ok:
        return {
            "ok": True,
            "message": f"Copied {len(_last_read_serials)} serial(s) to clipboard.",
            "serial_text": serial_text,
            "read_serials": get_last_read_serials(),
        }
    return {
        "ok": True,
        "message": f"{len(_last_read_serials)} serial(s) ready in serial_text/log (clipboard unavailable).",
        "serial_text": serial_text,
        "read_serials": get_last_read_serials(),
    }


def clear_serials() -> dict[str, Any]:
    global serial_text
    serial_text = ""
    return {"ok": True, "message": "Cleared boosting serial input in the backend state."}


def clear_serial_tools() -> dict[str, Any]:
    global serial_tools_input, serial_tools_serialized, serial_tools_deserialized, serial_tools_parts_breakdown, serial_tools_status
    serial_tools_input = ""
    serial_tools_serialized = ""
    serial_tools_deserialized = ""
    serial_tools_parts_breakdown = ""
    serial_tools_status = "Paste a @U serial or deserialized serial text above."
    return {"ok": True, "message": "Cleared Serial Tools state."}


def _parse_serial_text(raw: object) -> list[str]:
    """Parse pasted serial input without corrupting BL4 Base85 payloads.

    `@` and `U` are both valid Base85 alphabet characters, so a contiguous
    `@U...` token may contain `@U` mid-payload. Never split on those. Multiple
    Base85 serials on one line must be whitespace-separated.
    """
    tokens: list[str] = []
    for line in str(raw or "").strip().splitlines():
        text = serial_rewards._strip_wrapping_markdown_backticks(line.strip())
        if not text:
            continue
        if "|" in text:
            tokens.append(text)
            continue
        parts = [serial_rewards._strip_wrapping_markdown_backticks(part) for part in text.split()]
        parts = [part for part in parts if part]
        if len(parts) > 1 and all(part.startswith("@U") for part in parts):
            tokens.extend(parts)
            continue
        tokens.append(text)
    return tokens


def _serial_with_level_override(serial: str, level: int) -> str:
    raw = str(serial or "").strip()
    if not raw:
        return raw
    level_i = _clamp_int(level, 1, 60)
    human = _serial_to_human(raw) if raw.startswith("@U") else raw
    new_human, count = re.subn(r"^(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*)\d+", rf"\g<1>{level_i}", human, count=1)
    if count <= 0:
        raise ValueError("could not find leading item level in serial")
    return _human_to_serial(new_human)


def _serials_with_level_override(serials: list[str], enabled: bool, level: int) -> tuple[list[str], int, list[str]]:
    if not enabled:
        return list(serials), 0, []
    level_i = _clamp_int(level, 1, 60)
    out: list[str] = []
    changed = 0
    failures: list[str] = []
    for i, serial in enumerate(str(s or "").strip() for s in serials):
        if not serial:
            continue
        try:
            out.append(_serial_with_level_override(serial, level_i))
            changed += 1
        except Exception as exc:
            failures.append(f"serial #{i + 1}: {exc}")
            continue
    return out, changed, failures


def _host_player_index_value() -> int | None:
    try:
        pc = get_pc()
    except Exception:
        pc = None
    host_ps = getattr(pc, "PlayerState", None) if pc is not None else None
    _world, gs = _gbc_session_world_and_gamestate()
    pa = getattr(gs, "PlayerArray", None) if gs is not None else None
    if pa is None:
        return None
    try:
        count = len(pa)
    except Exception:
        return None
    if host_ps is None:
        return None
    host_name = ""
    try:
        host_name = str(getattr(host_ps, "PlayerName", "") or getattr(host_ps, "SavedNetworkAddress", "") or "")
    except Exception:
        host_name = ""
    for i in range(count):
        try:
            ps = pa[i]
        except Exception:
            ps = None
        if ps is None:
            continue
        if host_ps is not None and ps is host_ps:
            return i
        try:
            if host_ps is not None and getattr(ps, "Name", None) == getattr(host_ps, "Name", None):
                return i
        except Exception:
            pass
        if host_name:
            try:
                pn = str(getattr(ps, "PlayerName", "") or getattr(ps, "SavedNetworkAddress", "") or "")
                if pn and pn == host_name:
                    return i
            except Exception:
                pass
    return None


def _non_host_party_player_indices() -> list[int]:
    all_indices = [int(idx) for idx, _name in _players()]
    host_idx = _host_player_index_value()
    if host_idx is None:
        return []
    return [idx for idx in all_indices if idx != host_idx]


def _serial_delivery_count_note(parsed_count: int | None, resolved_count: int) -> str:
    if parsed_count is None or int(parsed_count) == int(resolved_count):
        return ""
    return f" Parsed {int(parsed_count)} input row(s), resolved {int(resolved_count)} deliverable serial(s)."


def _deliver_serials_with_target(serials: list[str], mode: str, parsed_count: int | None = None) -> dict[str, Any]:
    if not serials:
        return {"ok": False, "message": "No valid serials to deliver."}
    mode_key = str(mode or "selected").lower().strip()
    if mode_key in ("non_host", "all_non_host"):
        mode_key = "nonhost"
    if mode_key not in ("selected", "all", "nonhost"):
        mode_key = "selected"
    total_serials = len(serials)
    chunks = serial_rewards._serial_delivery_chunks(serials, mode_key)
    max_per_chunk = serial_rewards._serial_delivery_max_serials_per_chunk(mode_key)
    delay = serial_rewards._serial_delivery_post_open_delay(mode_key)
    estimated_wait = max(0.0, (len(chunks) - 1) * float(delay or 0.0)) if chunks else 0.0
    split_note = (
        f" Submitting {total_serials} serial(s) in {len(chunks)} chunk(s), "
        f"max {max_per_chunk} serial(s) per chunk, delay {delay:.2f}s."
    ) if chunks else ""
    if estimated_wait >= 10.0:
        split_note += f" Large delivery queued; estimated throttle wait is about {estimated_wait:.0f}s."
    count_note = _serial_delivery_count_note(parsed_count, total_serials)
    try:
        if mode_key == "all":
            indices = [int(idx) for idx, _name in _players()]
            if not indices:
                return {"ok": False, "message": "No party players found."}
            serial_rewards._do_give_serial_to_player_indices(serials, indices, scope_label="all party players", mode=mode_key)
            return {
                "ok": True,
                "message": f"Requested {total_serials} serial(s) for all party players ({len(indices)} target(s)).{split_note}{count_note}",
            }
        if mode_key == "nonhost":
            indices = _non_host_party_player_indices()
            if not indices:
                return {"ok": False, "message": "No non-host party players found."}
            serial_rewards._do_give_serial_to_player_indices(serials, indices, scope_label="all non-host players", mode=mode_key)
            return {
                "ok": True,
                "message": f"Requested {total_serials} serial(s) for all non-host players ({len(indices)} target(s)).{split_note}{count_note}",
            }
        idx = get_selected_player_index()
        name = get_selected_player_name() or "selected player"
        if idx is None:
            return {"ok": False, "message": "No party player selected."}
        serial_rewards._do_give_serial_to_player_indices(serials, [idx], scope_label=f"selected player {idx} {name}", mode=mode_key)
        return {"ok": True, "message": f"Requested {total_serials} serial(s) for {name}.{split_note}{count_note}"}
    except Exception as exc:
        return {"ok": False, "message": f"Serial delivery failed: {exc!r}"}


def _finish_give_serials(
    serials: list[str] | None,
    *,
    expanded: list[str],
    mode: str,
    override_level: object,
    level: object,
    source_text: str,
) -> dict[str, Any]:
    if serials is None:
        return {
            "ok": False,
            "message": (
                "Serial resolve failed (see SDK log). Base85 may contain non-alphabet "
                "characters (accents/smart quotes replacing a backtick), Discord/markdown "
                "damage, or no deliverable serials after filtering. Paste the full "
                "contiguous @U code without wrapping it in Discord inline backticks."
            ),
        }
    if not serials:
        return {"ok": False, "message": "No valid serials after parsing/resolving."}
    try:
        level_i = _clamp_int(level, 1, 60)
    except Exception:
        level_i = 60
    override_enabled = bool(override_level)
    original_count = len(serials)
    serials, changed, override_failures = _serials_with_level_override(serials, override_enabled, level_i)
    if override_enabled and not serials:
        detail = "; ".join(override_failures[:4])
        if len(override_failures) > 4:
            detail += f"; and {len(override_failures) - 4} more"
        return {"ok": False, "message": f"Level override failed for all selected serials. Nothing was delivered. {detail}".strip()}
    result = _deliver_serials_with_target(serials, mode, parsed_count=len(expanded))
    if result.get("ok") and override_enabled:
        parts: list[str] = []
        if changed:
            parts.append(f"Level override: {changed} serial(s) set to level {level_i}.")
        if override_failures:
            skipped = original_count - len(serials)
            sample = "; ".join(override_failures[:3])
            if len(override_failures) > 3:
                sample += f"; and {len(override_failures) - 3} more"
            parts.append(f"Skipped {skipped} serial(s) that could not be level-overridden ({sample}).")
        if parts:
            result["message"] = f"{result.get('message', '')} {' '.join(parts)}"
    if result.get("ok"):
        mode_key = str(mode or "selected").lower().strip()
        if mode_key in ("non_host", "all_non_host"):
            mode_key = "nonhost"
        action = {
            "selected": "give_serial_selected",
            "all": "give_serial_all",
            "nonhost": "give_serial_nonhost",
        }.get(mode_key, "give_serial_selected")
        note_last_command(
            action,
            label={
                "give_serial_selected": "Give Serial Selected",
                "give_serial_all": "Give Serial All",
                "give_serial_nonhost": "Give Serial Non-Host",
            }.get(action, "Give Serial"),
            payload={
                "serial_text": source_text,
                "serial_override_level": bool(override_enabled),
                "serial_level": int(level_i),
            },
            is_drop=True,
            needs_player=(action == "give_serial_selected"),
        )
    return result


def give_serials(text: object, mode: str = "selected", override_level: object = False, level: object = 60) -> dict[str, Any]:
    global serial_text
    serial_text = str(text or "")
    if not serial_text.strip():
        return {"ok": False, "message": "Paste at least one Base85 serial first."}
    source_text = serial_text
    expanded = _parse_serial_text(source_text)
    if serial_rewards.needs_async_serial_resolution(expanded):
        def _resolved(serials: list[str] | None, error: Exception | None) -> None:
            if error is not None:
                serial_rewards._log_error(f"Serial resolve failed: {error!r}")
                return
            result = _finish_give_serials(
                serials,
                expanded=expanded,
                mode=mode,
                override_level=override_level,
                level=level,
                source_text=source_text,
            )
            if not result.get("ok"):
                serial_rewards._log_error(str(result.get("message") or "Serial delivery failed."))

        serial_rewards.queue_serial_resolution(expanded, _resolved)
        return {"ok": True, "message": "Serial conversion queued in background; delivery will start when ready."}
    try:
        serials = serial_rewards._resolve_give_serial_strings(expanded)
    except Exception as exc:
        return {"ok": False, "message": f"Serial resolve failed: {exc!r}"}
    return _finish_give_serials(
        serials,
        expanded=expanded,
        mode=mode,
        override_level=override_level,
        level=level,
        source_text=source_text,
    )


def serial_convert(text: object) -> dict[str, Any]:
    global serial_tools_input, serial_tools_serialized, serial_tools_deserialized, serial_tools_parts_breakdown, serial_tools_status
    serial_tools_input = str(text or "").strip()
    if not serial_tools_input:
        serial_tools_serialized = ""
        serial_tools_deserialized = ""
        serial_tools_parts_breakdown = ""
        serial_tools_status = "Paste a @U serial or deserialized serial text above."
        return {
            "ok": False,
            "message": serial_tools_status,
            "serialized": "",
            "deserialized": "",
            "breakdown": "",
        }
    try:
        if serial_tools_input.startswith("@U"):
            human = _serial_to_human(serial_tools_input)
            serial = _human_to_serial(human)
        else:
            serial = _human_to_serial(serial_tools_input)
            human = _serial_to_human(serial)
        serial_tools_serialized = serial
        serial_tools_deserialized = human
        serial_tools_parts_breakdown = ""
        serial_tools_status = "Converted successfully."
        return {
            "ok": True,
            "message": serial_tools_status,
            "serialized": serial_tools_serialized,
            "deserialized": serial_tools_deserialized,
            "breakdown": serial_tools_parts_breakdown,
        }
    except Exception as exc:
        serial_tools_serialized = ""
        serial_tools_deserialized = ""
        serial_tools_parts_breakdown = ""
        serial_tools_status = f"Conversion failed: {exc}"
        return {
            "ok": False,
            "message": serial_tools_status,
            "serialized": "",
            "deserialized": "",
            "breakdown": "",
        }


@command(
    "msbt_complete_challenges",
    description=(
        "Hidden: queue complete-all-challenges for live players using the packaged "
        "challenge catalog. Prefer msbt_complete_challenges_cancel to stop."
    ),
)
def _cmd_msbt_complete_challenges(_args: Any = None) -> None:
    result = complete_challenges_all()
    _challenge_set_status(str(result.get("message") or _challenge_last_status))


@command(
    "msbt_complete_challenges_cancel",
    description="Hidden: cancel a running msbt_complete_challenges queue.",
)
def _cmd_msbt_complete_challenges_cancel(_args: Any = None) -> None:
    result = complete_challenges_cancel()
    _challenge_set_status(str(result.get("message") or _challenge_last_status))


def _probe_name_interesting(name: str) -> bool:
    lowered = str(name or "").lower()
    keys = (
        "challenge",
        "mission",
        "progress",
        "complete",
        "increment",
        "grant",
        "reward",
        "achievement",
        "stat",
        "counter",
    )
    return any(key in lowered for key in keys)


def _safe_dir_names(obj: Any, *, limit: int = 400) -> list[str]:
    names: list[str] = []
    try:
        for name in dir(obj):
            if str(name).startswith("_"):
                continue
            names.append(str(name))
            if len(names) >= limit:
                break
    except Exception as exc:
        return [f"<dir failed: {exc!r}>"]
    return names


def _safe_class_function_names(obj: Any, *, limit: int = 400) -> list[str]:
    names: list[str] = []
    try:
        cls = getattr(obj, "Class", None)
        funcs = getattr(cls, "Functions", None) if cls is not None else None
        if funcs is None:
            return []
        for fn in list(funcs):
            try:
                raw = getattr(fn, "Name", None) or getattr(fn, "get_path_name", lambda: None)() or str(fn)
            except Exception:
                raw = str(fn)
            text = str(raw)
            if text.startswith("_"):
                continue
            names.append(text)
            if len(names) >= limit:
                break
    except Exception as exc:
        return [f"<Functions failed: {exc!r}>"]
    return names


def probe_challenge_apis() -> dict[str, Any]:
    """Live introspection for challenge completion APIs (research only)."""
    if not challenge_api_probe_enabled():
        return {
            "ok": False,
            "message": (
                "Challenge API probe is disabled in shipping builds. "
                "Set MSBT_DEBUG_PROBES=1 to enable."
            ),
        }
    pc = get_pc()
    if pc is None:
        return {"ok": False, "message": "No local player controller."}

    payload: dict[str, Any] = {
        "ok": True,
        "message": "Challenge API probe complete.",
        "pc_type": type(pc).__name__,
        "pc_interesting_attrs": [],
        "pc_interesting_funcs": [],
        "pc_method_hits": {},
        "manager_method_hits": {},
        "oak_challenge_manager": None,
        "rewards_manager": None,
        "find_all_challenge_classes": {},
    }

    candidate_methods = (
        "ServerIncrementChallengeForPlayer",
        "ClientIncrementChallengeForPlayer",
        "IncrementChallengeForPlayer",
        "IncrementChallenge",
        "ServerCompleteChallenge",
        "ClientCompleteChallenge",
        "CompleteChallenge",
        "CompleteChallengeForPlayer",
        "ServerSetChallengeProgress",
        "SetChallengeProgress",
        "SetChallengeCompleted",
        "ActivateChallenge",
        "ServerActivateChallenge",
        "DeactivateChallenge",
        "GetChallengeProgress",
        "GetChallengeManager",
        "UpdateChallenge",
        "ServerUpdateChallenge",
        "GrantChallenge",
        "ServerGrantChallenge",
        "ForceCompleteChallenge",
        "DebugCompleteChallenge",
        "CheatCompleteChallenge",
        "Server_OpenAllPackages",
        "Server_OpenPackage",
    )

    def _method_hit(obj: Any, name: str) -> dict[str, Any]:
        info: dict[str, Any] = {"name": name, "hasattr": False, "callable": False}
        try:
            info["hasattr"] = hasattr(obj, name)
        except Exception as exc:
            info["hasattr_error"] = repr(exc)
            return info
        if not info["hasattr"]:
            return info
        try:
            value = getattr(obj, name)
            info["callable"] = callable(value)
            info["value_type"] = type(value).__name__
            info["value_str"] = str(value)[:180]
        except Exception as exc:
            info["getattr_error"] = repr(exc)
        return info

    pc_attrs = _safe_dir_names(pc)
    payload["pc_interesting_attrs"] = [n for n in pc_attrs if _probe_name_interesting(n)]
    payload["pc_interesting_funcs"] = [
        n for n in _safe_class_function_names(pc) if _probe_name_interesting(n)
    ]
    payload["pc_method_hits"] = {
        name: _method_hit(pc, name) for name in candidate_methods if _method_hit(pc, name).get("hasattr")
    }
    # Always include the known UVH method even when absent, for clarity.
    if "ServerIncrementChallengeForPlayer" not in payload["pc_method_hits"]:
        payload["pc_method_hits"]["ServerIncrementChallengeForPlayer"] = _method_hit(
            pc, "ServerIncrementChallengeForPlayer"
        )

    for attr_name, key in (
        ("OakChallengeManager", "oak_challenge_manager"),
        ("ChallengeManager", "oak_challenge_manager"),
        ("RewardsManager", "rewards_manager"),
    ):
        if payload.get(key):
            continue
        try:
            obj = getattr(pc, attr_name, None)
        except Exception as exc:
            payload[key] = {"attr": attr_name, "error": repr(exc)}
            continue
        if obj is None:
            continue
        payload[key] = {
            "attr": attr_name,
            "type": type(obj).__name__,
            "path": str(getattr(obj, "get_path_name", lambda: "")() or obj),
            "interesting_attrs": [n for n in _safe_dir_names(obj) if _probe_name_interesting(n)],
            "all_attrs_sample": _safe_dir_names(obj, limit=120),
            "interesting_funcs": [n for n in _safe_class_function_names(obj) if _probe_name_interesting(n)],
            "all_funcs_sample": _safe_class_function_names(obj, limit=120),
            "method_hits": {
                name: hit
                for name in candidate_methods
                for hit in [_method_hit(obj, name)]
                if hit.get("hasattr")
            },
        }
        if key == "oak_challenge_manager":
            payload["manager_method_hits"] = payload[key]["method_hits"]

    try:
        from unrealsdk import find_all, find_class
    except Exception as exc:
        payload["find_error"] = repr(exc)
        _challenge_set_status(f"Challenge API probe finished (find_* unavailable: {exc!r}).")
        return payload

    for class_name in (
        "OakChallengeManager",
        "ChallengeManager",
        "GbxChallengeManager",
        "OakChallenge",
        "Challenge",
        "OakPlayerChallengeComponent",
        "PlayerChallengeComponent",
        "ChallengeComponent",
        "GbxRewardsManager",
    ):
        entry: dict[str, Any] = {"class": class_name}
        try:
            cls = find_class(class_name)
            entry["find_class"] = bool(cls is not None)
            if cls is not None:
                entry["class_funcs"] = [
                    n for n in _safe_class_function_names(cls) if _probe_name_interesting(n)
                ][:80]
                entry["class_funcs_all_sample"] = _safe_class_function_names(cls, limit=80)
                entry["class_method_hits"] = {
                    name: hit
                    for name in candidate_methods
                    for hit in [_method_hit(cls, name)]
                    if hit.get("hasattr")
                }
        except Exception as exc:
            entry["find_class_error"] = repr(exc)
        try:
            objects = list(find_all(class_name, False) or [])
            if not objects:
                objects = list(find_all(class_name) or [])
            entry["find_all_count"] = len(objects)
            if objects:
                sample = objects[0]
                entry["sample_type"] = type(sample).__name__
                entry["sample_interesting_attrs"] = [
                    n for n in _safe_dir_names(sample) if _probe_name_interesting(n)
                ][:80]
                entry["sample_interesting_funcs"] = [
                    n for n in _safe_class_function_names(sample) if _probe_name_interesting(n)
                ][:80]
                entry["sample_method_hits"] = {
                    name: hit
                    for name in candidate_methods
                    for hit in [_method_hit(sample, name)]
                    if hit.get("hasattr")
                }
                entry["sample_all_attrs"] = _safe_dir_names(sample, limit=200)
        except Exception as exc:
            entry["find_all_error"] = repr(exc)
        payload["find_all_challenge_classes"][class_name] = entry

    _challenge_set_status(
        "Challenge API probe complete; see bridge action probe_challenge_apis result."
    )
    return payload


@command(
    "msbt_probe_challenge_apis",
    description="Hidden: dump live OakChallengeManager / challenge-related API names to the log.",
)
def _cmd_msbt_probe_challenge_apis(_args: Any = None) -> None:
    result = probe_challenge_apis()
    try:
        from unrealsdk import logging as _sdk_logging

        _sdk_logging.info(
            f"[Matts SDK Boosting Tools | Challenges] probe ok={result.get('ok')} "
            f"manager={bool(result.get('oak_challenge_manager'))} "
            f"pc_funcs={len(result.get('pc_interesting_funcs') or [])}"
        )
        mgr = result.get("oak_challenge_manager") or {}
        if isinstance(mgr, dict):
            _sdk_logging.info(
                f"[Matts SDK Boosting Tools | Challenges] manager funcs: "
                f"{', '.join((mgr.get('interesting_funcs') or [])[:40])}"
            )
            _sdk_logging.info(
                f"[Matts SDK Boosting Tools | Challenges] manager attrs: "
                f"{', '.join((mgr.get('interesting_attrs') or [])[:40])}"
            )
    except Exception:
        pass
    _challenge_set_status(str(result.get("message") or "Challenge API probe finished."))
