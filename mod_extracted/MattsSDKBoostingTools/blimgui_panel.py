"""Custom BLImGui panel for Matt's SDK Boosting Tools."""
from __future__ import annotations

import sys
import types
from typing import Any, Callable
import re
import json
import os
import time
import threading
import traceback
import pkgutil
import urllib.request
import urllib.parse
import html
from pathlib import Path

import blimgui as _blimgui
try:
    from blimgui import cyber as _cyber
except Exception:  # fall back cleanly if an older BLImGui is installed
    _cyber = None
from mods_base import command, keybind, get_pc, hook, ENGINE
import unrealsdk
from unrealsdk import logging

from .golden_chest_keybinds import _close_golden_chest, _open_golden_chest
from .party_helpers import (
    _kick_party_player_by_index,
    _list_party_players,
    _gbc_session_world_and_gamestate,
    _gbc_find_pc_for_player_state,
    _gbc_resolve_player_display_name,
    _gbc_is_listen_host_world,
)
from .player_economy import _do_msbt_maxsdu, _do_give_currency, _do_give_experience
from .serial_rewards import (
    _do_give_serial,
    _do_give_serial_to_player_indices,
    _expand_serial_token,
    _resolve_give_serial_strings,
    _serial_delivery_chunks,
    _serial_delivery_chunk_stats,
    serial_delivery_status,
    serial_delivery_progress,
    serial_delivery_timing,
    set_serial_delivery_timing,
)
from .serial_converter import human_to_serial as _human_to_serial, serial_to_human as _serial_to_human
try:
    from . import legit_builder_core as _legit_builder
except Exception:
    _legit_builder = None
from .shinies import DEFAULT_ITEM_LEVEL as _SHINY_DEFAULT_LEVEL, drop_all_shinies
from .dev_tools import activate_devperk, clamp_debug_speed, devperk_button_label, devperk_label, devperk_toggle_state, get_debug_cam_speed, set_debug_cam_speed, toggle_debug_cam, teleport_pawn_to_debug_cam
from .movement_adjustments import (
    apply_movement_advanced_to_all_players,
    reset_movement_advanced_all_players,
    set_time_dilation,
    toggle_players_only,
    set_no_target,
    delete_ground_items,
    set_noclip,
    teleport_pawn_to_pawn,
    zero_vault_power_costs_all_players,
    refresh_jump_counts_all_players,
)
from .item_pool_spawning import DEFAULT_ITEM_LEVEL as _ITEMPOOL_DEFAULT_LEVEL, filter_item_pools, item_pool_categories, load_item_pools, spawn_item_pool
from .travel import canonical_travel_map_name, filter_travel_maps, filter_travel_stations, travel_to_map, travel_to_station, _exec_console
_MAIN_THREAD_IDENT = threading.get_ident()
_UI_THREAD_IDENT: int | None = None

from .inventory_capacity import (
    _DEFAULT_BACKPACK_SIZE,
    _DEFAULT_BANK_SIZE,
    auto_apply_inventory_sizes_if_needed,
    clamp_container_size,
    load_inventory_settings,
    save_inventory_settings,
    save_extra_settings,
    set_inventory_sizes_for_all_party,
    set_inventory_sizes_for_party_index,
)



def _effective_game_window_title(value: str | None = None) -> str:
    text = str(_custom_game_title if value is None else value).strip()
    return text or _DEFAULT_GAME_WINDOW_TITLE


def _apply_game_window_title(value: str | None = None) -> None:
    """Apply the saved custom game window title, falling back to the vanilla BL4 title."""
    global _last_applied_game_window_title
    final_title = _effective_game_window_title(value)
    if final_title == _last_applied_game_window_title:
        return
    try:
        try:
            kismet = unrealsdk.find_class("/Script/Engine.KismetSystemLibrary").ClassDefaultObject
        except Exception:
            kismet = unrealsdk.find_class("KismetSystemLibrary").ClassDefaultObject
        kismet.SetWindowTitle(final_title)
        _last_applied_game_window_title = final_title
        _log(f"applied game window title: {final_title!r}")
    except Exception as exc:
        _log(f"could not apply game window title: {exc!r}")


def _save_custom_game_title(value: str) -> None:
    """Persist the raw user title. Blank is meaningful: it restores the vanilla title."""
    try:
        save_extra_settings(custom_game_title=str(value or ""))
    except Exception as exc:
        _log(f"could not save custom game title: {exc!r}")


def _draw_custom_game_title_control() -> None:
    global _custom_game_title
    imgui = _blimgui.imgui
    old_title = _custom_game_title
    _custom_game_title = _input_text("Custom Game Title###msbt_custom_game_title", _custom_game_title, 128)
    if _custom_game_title != old_title:
        _save_custom_game_title(_custom_game_title)
        _apply_game_window_title(_custom_game_title)
    try:
        imgui.same_line()
        _muted_wrapped(f"Blank = {_DEFAULT_GAME_WINDOW_TITLE}")
    except Exception:
        pass


def _canonicalize_travel_map_values(values) -> set[str]:
    out: set[str] = set()
    for value in values or []:
        text = str(value or "").strip()
        if text:
            out.add(canonical_travel_map_name(text))
    return out


def _canonicalize_travel_map_descriptions(raw) -> dict[str, str]:
    out: dict[str, str] = {}
    if not isinstance(raw, dict):
        return out
    for key, value in raw.items():
        canon = canonical_travel_map_name(str(key or "").strip())
        text = str(value or "").strip()
        if canon and text and canon not in out:
            out[canon] = text
    return out

WINDOW_TITLE = "Matt's SDK Boosting Tools"
_DEFAULT_GAME_WINDOW_TITLE = "Borderlands® 4"
_last_applied_game_window_title: str | None = None
_log_lines: list[str] = []
_log_lock = threading.RLock()
_pending_worker_log_lines: list[str] = []
_status_pill_message: str = ""
_status_pill_accent: str = "cyan"
_status_pill_until: float = 0.0
_hud_pill_message: str = ""
_hud_pill_accent: str = "cyan"
_hud_pill_until: float = 0.0
_hud_pill_root = None
_hud_pill_box = None
_hud_pill_text = None
_hud_pill_progress_bg = None
_hud_pill_progress_fill = None
_hud_pill_host = None
_hud_pill_host_hud_name: str = ""
_hud_pill_overlay_widget = None
_hud_pill_original_content = None
_hud_pill_last_message: str = ""
_hud_pill_last_accent: str = ""
_hud_pill_last_progress: float = -1.0
_hud_pill_clear_timer = None
_hud_pill_generation: int = 0
_hud_pill_next_update: float = 0.0
_hud_pill_last_w: float = 0.0
_hud_pill_last_h: float = 0.0
_hud_native_suppressed_until: float = 0.0
_hud_native_client_block_until: float = 0.0
_movement_off_host_pause_until: float = 0.0
_movement_host_cache_value: bool = False
_movement_host_cache_until: float = 0.0


def _hud_native_suppressed() -> bool:
    try:
        return time.monotonic() < float(_hud_native_suppressed_until or 0.0)
    except Exception:
        return False


def _hud_forget_viewport_pill_overlay(cancel_timer: bool = True) -> None:
    """Drop cached HUD UMG references without touching native objects.

    Map/server travel can destroy World/PlayerController/HUD objects while Python
    still holds wrappers.  Probing or removing a stale UMG widget can crash inside
    pyunrealsdk, so travel/load paths only clear Python references.
    """
    global _hud_pill_message, _hud_pill_accent, _hud_pill_until
    global _hud_pill_host, _hud_pill_host_hud_name, _hud_pill_overlay_widget
    global _hud_pill_root, _hud_pill_box, _hud_pill_text, _hud_pill_progress_bg, _hud_pill_progress_fill
    global _hud_pill_last_message, _hud_pill_last_accent, _hud_pill_last_progress, _hud_pill_next_update
    if cancel_timer:
        try:
            _hud_cancel_pill_timer()
        except Exception:
            pass
    _hud_pill_message = ""
    _hud_pill_accent = "cyan"
    _hud_pill_until = 0.0
    _hud_pill_overlay_widget = None
    _hud_pill_host = None
    _hud_pill_host_hud_name = ""
    _hud_pill_root = None
    _hud_pill_box = None
    _hud_pill_text = None
    _hud_pill_progress_bg = None
    _hud_pill_progress_fill = None
    _hud_pill_last_message = ""
    _hud_pill_last_accent = ""
    _hud_pill_last_progress = -1.0
    _hud_pill_next_update = 0.0


def _hud_suppress_native(seconds: float = 15.0) -> None:
    """Temporarily disable AddToViewport HUD writes during map travel/loading."""
    global _hud_native_suppressed_until
    try:
        _hud_native_suppressed_until = max(float(_hud_native_suppressed_until or 0.0), time.monotonic() + max(1.0, float(seconds)))
    except Exception:
        _hud_native_suppressed_until = time.monotonic() + 15.0
    _hud_forget_viewport_pill_overlay()

def _debugcam_original_controller_fast(pc):
    """Unwrap DebugCameraController to its original PlayerController for host checks.

    When joined as a client and debug cam is active, get_pc() can become the
    DebugCameraController.  That controller may report authority-ish values or
    point at transient camera objects, which made HUD/native/menu hot paths run
    client-unsafe work and tank FPS.
    """
    try:
        if pc is not None and "DebugCameraController" in str(getattr(pc, "Class", "")):
            for attr in ("OriginalControllerRef", "OriginalController"):
                try:
                    original = getattr(pc, attr, None)
                    if original is not None and "DebugCameraController" not in str(getattr(original, "Class", "")):
                        return original
                except Exception:
                    pass
    except Exception:
        pass
    return pc


def _local_pc_has_authority_fast() -> bool:
    """Cheap host check used from hot paths. False during client join/travel/debugcam."""
    try:
        pc = _debugcam_original_controller_fast(get_pc())
    except Exception:
        return False
    if pc is None:
        return False
    try:
        return bool(pc.HasAuthority())
    except Exception:
        # Standalone/offline builds may not expose HasAuthority; treat a valid non-debug PC as safe.
        try:
            return "DebugCameraController" not in str(getattr(pc, "Class", ""))
        except Exception:
            return True


def _hud_native_allowed() -> bool:
    """Native AddToViewport HUD toasts are optional and never used from idle paths."""
    try:
        if not bool(_hud_native_toasts_enabled):
            return False
    except Exception:
        return False
    try:
        if _hud_native_suppressed():
            return False
    except Exception:
        return False
    try:
        if not _local_pc_has_authority_fast():
            return False
    except Exception:
        return False
    return True


_selected_player_index: int = 0
_serial_text: str = ""
_serial_delivery_override_level: bool = False
_serial_delivery_level: int = 60
_last_serial_delivery_status_seen: str = ""
_serial_delivery_advanced_timing: bool = False
_serial_delivery_pre_open_delay: float = 1.00
_serial_delivery_post_open_delay: float = 0.50
_serial_tools_input: str = ""
_serial_tools_serialized: str = ""
_serial_tools_deserialized: str = ""
_serial_tools_parts_breakdown: str = ""
_serial_tools_status: str = "Paste a @U serial or deserialized serial text above."
_serial_store_entries: list[dict[str, str]] = []
_serial_store_selected_ids: set[str] = set()
_serial_store_active_id: str = ""
_serial_store_name: str = ""
_serial_store_group: str = "Default"
_serial_store_serial: str = ""
_serial_store_group_filter_index: int = 0
_serial_store_player_index: int = 0
_serial_store_status: str = "Add named @U/deserialized serials, group them, multi-select, then deliver to all party players."
_gzo_url: str = "https://save-editor.be/GZO/Borderlands4/Codes.html"
_SAVE_EDITOR_URL: str = "https://save-editor.be"
_LEGIT_DISCLAIMER: str = "DISCLAIMER: This tool has not been fully verified for Legit loot and all outputs should still be verified against https://save-editor.be."
_gzo_entries: list[dict[str, str]] = []
_gzo_selected_ids: set[str] = set()
_gzo_active_id: str = ""
_gzo_search: str = ""
_gzo_listing_index: int = 0
_gzo_type_filter_index: int = 0
_gzo_manufacturer_filter_index: int = 0
_gzo_rarity_filter_index: int = 0
_gzo_creator_filter_index: int = 0
_gzo_mattmab_filter_index: int = 0
_gzo_player_index: int = 0
_gzo_status: str = "Click Load Cache or Refresh GZO to populate the merged BL4 Codes catalog."
_gzo_last_refresh: float = 0.0
_gzo_cache_autoload_attempted: bool = False
_lootlemon_categories: list[dict[str, str]] = [
    {"name": "Weapons", "url": "https://www.lootlemon.com/db/borderlands-4/weapons"},
    {"name": "Shields", "url": "https://www.lootlemon.com/db/borderlands-4/shields"},
    {"name": "Ordnance", "url": "https://www.lootlemon.com/db/borderlands-4/ordnance"},
    {"name": "Repkits", "url": "https://www.lootlemon.com/db/borderlands-4/repkits"},
    {"name": "Class Mods", "url": "https://www.lootlemon.com/db/borderlands-4/class-mods"},
    {"name": "Enhancements", "url": "https://www.lootlemon.com/db/borderlands-4/enhancements"},
]
_lootlemon_entries: list[dict[str, str]] = []
_lootlemon_selected_ids: set[str] = set()
_lootlemon_active_id: str = ""
_lootlemon_search: str = ""
_lootlemon_category_index: int = 0
_lootlemon_mattmab_filter_index: int = 0
_lootlemon_player_index: int = 0
_lootlemon_status: str = "Click Load Cache to use the bundled/local Lootlemon code cache. Direct Lootlemon scraping is disabled."
_lootlemon_last_refresh: float = 0.0
_lootlemon_cache_autoload_attempted: bool = False
_lootlemon_filter_cache_key: tuple = ()
_lootlemon_filter_cache_result: list[dict[str, str]] = []
_lootlemon_active_cache_id: str = ""
_lootlemon_active_cache_entry: dict[str, str] | None = None
_lootlemon_delivery_override_level: bool = False
_lootlemon_delivery_level: int = 60
_gzo_delivery_override_level: bool = False
_gzo_delivery_level: int = 60
_serial_level_override_cache: dict[tuple[bool, int, int, int], tuple[list[str], int, str | None]] = {}
_serial_parts_cache_serial: str = ""
_serial_parts_cache_text: str = ""
_async_refresh_lock = threading.RLock()
_lootlemon_refresh_thread: threading.Thread | None = None
_lootlemon_refresh_result: tuple[list[dict[str, str]] | None, str | None] | None = None
_lootlemon_refresh_progress: dict[str, object] = {"running": False, "label": "", "done": 0, "total": 0, "found": 0}
_gzo_refresh_thread: threading.Thread | None = None
_gzo_refresh_result: tuple[list[dict[str, str]] | None, str | None, list[str]] | None = None
_gzo_refresh_progress: dict[str, object] = {"running": False, "label": "", "done": 0, "total": 0, "found": 0}
_gzo_filter_options_cache_key: tuple = ()
_gzo_filter_options_cache: dict[str, list[str]] = {}
_gzo_filter_cache_key: tuple = ()
_gzo_filter_cache_result: list[dict[str, str]] = []
_gzo_active_cache_id: str = ""
_gzo_active_cache_entry: dict[str, str] | None = None
_serial_store_search: str = ""
_currency_amount: int = 1000000
_currency_kind_index: int = 0
_exp_level: int = 60
_exp_track_index: int = 0
_inventory_settings = load_inventory_settings()
_custom_game_title: str = str(_inventory_settings.get("custom_game_title", "") or "")
_ui_box_sizes: dict[str, int] = {str(k): int(v) for k, v in dict(_inventory_settings.get("ui_box_sizes", {}) or {}).items()}
# Compact Boosting-tab card height defaults.  Older builds saved very tall card
# heights, which made the tab mostly empty space.  If a saved height still matches
# one of those old defaults, upgrade it to the compact content-fit value.
_BOOSTING_CARD_HEIGHT_UPGRADE: dict[str, tuple[int, int]] = {
    "card_serial_rewards": (340, 430),
    "card_currency": (260, 155),
    "card_experience": (235, 150),
    "card_inventory_size": (255, 165),
    "card_sdu": (265, 150),
    "card_dev_tools": (330, 245),
    "card_rarity_disabler": (340, 325),
}
for _card_key, (_old_h, _new_h) in _BOOSTING_CARD_HEIGHT_UPGRADE.items():
    try:
        if int(_ui_box_sizes.get(_card_key, _old_h)) == int(_old_h):
            _ui_box_sizes[_card_key] = int(_new_h)
    except Exception:
        pass
_backpack_size: int = int(_inventory_settings.get("backpack_size", _DEFAULT_BACKPACK_SIZE))
_bank_size: int = int(_inventory_settings.get("bank_size", _DEFAULT_BANK_SIZE))
_auto_inventory_sizes: bool = bool(_inventory_settings.get("auto_inventory_sizes", False))
_auto_inventory_last_log: float = 0.0
_debug_cam_speed: float = get_debug_cam_speed()
_debug_cam_speed_pending: bool = False
_debug_cam_speed_due: float = 0.0
_debug_cam_speed_apply_delay: float = 0.25
_movement_speed_value: float = 1.25
_movement_jump_goal_value: float = 900.0
_movement_status: str = "Adjusts live movement fields on selected/all party pawns."
_MOVEMENT_DEFAULT_PRESET: dict[str, float | bool] = {
    # Captured live BL4 defaults. Class default objects report zeroes for several of these.
    "speed_scale": 1.0,
    "walk_speed": 600.0,
    "jump_goal": 198.0,
    "jump_velocity": 840.0,
    "sprint_jump_goal": 198.0,
    "double_jump_goal": 225.0,
    "slide_jump_goal": 198.0,
    "jump_hold_time": 0.0,
    "gravity_scale": 1.0,
    "max_step_height": 45.0,
    "jump_count": 2,
    "jump_off_z_factor": 0.5,
    "walkable_floor_angle": 44.76508331298828,
    "walkable_floor_z": 0.7099999785423279,
    "time_dilation": 1.0,
    "glide_speed": 1200.0,
    "glide_boost": 0.0,
    "glide_air_control": 0.6000000238418579,
    "dash_speed": 2500.0,
    "zero_vault_costs": False,
}
_movement_auto_apply_on_load: bool = bool(_inventory_settings.get("movement_auto_apply_on_load", False))
_movement_refresh_jump_count: bool = False  # legacy timer disabled; infinite jump now uses HUD tick spent-counter reset
_movement_jump_refresh_interval: float = 0.06
_movement_infinite_jump_indices: set[int] = set()
_movement_saved_preset: dict[str, object] = dict(_inventory_settings.get("movement_saved_preset", {}) or {})
_movement_apply_on_load_done: bool = False
_movement_last_auto_apply_try: float = 0.0
_movement_last_jump_refresh: float = 0.0
_movement_next_jump_refresh_due: float = 0.0
# Movement slider changes are debounced: the UI value updates immediately, but
# expensive writes to every player are delayed until the slider has been stable.
_movement_debounce_apply_delay: float = 0.35
_movement_pending_apply_due: float = 0.0
_movement_pending_apply: bool = False
_movement_pending_apply_reason: str = ""
_movement_pending_sections: set[str] = set()

# AMD/OpenGL/glfw crash mitigation: when party membership changes, pause the
# external BLImGui draw callback briefly.  The HUD pill stays active because it
# is UMG, not glfw/imgui.
_blimgui_join_safe_mode: bool = True
_blimgui_draw_paused_until: float = 0.0
_blimgui_last_party_signature: str = ""
_movement_infinite_jump_context_cache: list[tuple[int, str, object, object | None, object | None]] = []
_movement_infinite_jump_context_cache_time: float = 0.0
# Do not cache live slider values between game loads.  Only load a user-saved preset
# when Auto Apply on Game Load is checked; otherwise start from vanilla-ish defaults.
_movement_boot_preset: dict[str, object] = dict(_MOVEMENT_DEFAULT_PRESET)
if _movement_auto_apply_on_load and _movement_saved_preset:
    try:
        _movement_boot_preset.update(dict(_movement_saved_preset))
    except Exception:
        pass
_movement_speed_scale: float = float(_movement_boot_preset.get("speed_scale", _MOVEMENT_DEFAULT_PRESET["speed_scale"]) or _MOVEMENT_DEFAULT_PRESET["speed_scale"])
_movement_walk_speed: float = float(_movement_boot_preset.get("walk_speed", _MOVEMENT_DEFAULT_PRESET["walk_speed"]) or _MOVEMENT_DEFAULT_PRESET["walk_speed"])
_movement_jump_goal: float = float(_movement_boot_preset.get("jump_goal", _MOVEMENT_DEFAULT_PRESET["jump_goal"]) or _MOVEMENT_DEFAULT_PRESET["jump_goal"])
_movement_jump_velocity: float = float(_movement_boot_preset.get("jump_velocity", _movement_jump_goal) or _movement_jump_goal)
_movement_sprint_jump_goal: float = float(_movement_boot_preset.get("sprint_jump_goal", _movement_jump_goal) or _movement_jump_goal)
_movement_double_jump_goal: float = float(_movement_boot_preset.get("double_jump_goal", _MOVEMENT_DEFAULT_PRESET["double_jump_goal"]) or _MOVEMENT_DEFAULT_PRESET["double_jump_goal"])
_movement_slide_jump_goal: float = float(_movement_boot_preset.get("slide_jump_goal", _movement_sprint_jump_goal) or _movement_sprint_jump_goal)
_movement_individual_jump_goals: bool = bool(_movement_boot_preset.get("individual_jump_goals", False))
_movement_jump_hold_time: float = 0.0
_movement_gravity_scale: float = float(_movement_boot_preset.get("gravity_scale", _MOVEMENT_DEFAULT_PRESET["gravity_scale"]) or _MOVEMENT_DEFAULT_PRESET["gravity_scale"])
_movement_max_step_height: float = float(_movement_boot_preset.get("max_step_height", _MOVEMENT_DEFAULT_PRESET["max_step_height"]) or _MOVEMENT_DEFAULT_PRESET["max_step_height"])
_movement_jump_count: int = 2
_movement_jump_off_z_factor: float = 0.5
_movement_walkable_floor_angle: float = float(_movement_boot_preset.get("walkable_floor_angle", _MOVEMENT_DEFAULT_PRESET["walkable_floor_angle"]) or _MOVEMENT_DEFAULT_PRESET["walkable_floor_angle"])
_movement_walkable_floor_z: float = float(_movement_boot_preset.get("walkable_floor_z", _MOVEMENT_DEFAULT_PRESET["walkable_floor_z"]) or _MOVEMENT_DEFAULT_PRESET["walkable_floor_z"])
_movement_time_dilation: float = float(_MOVEMENT_DEFAULT_PRESET.get("time_dilation", 1.0) or 1.0)
_movement_glide_speed: float = float(_movement_boot_preset.get("glide_speed", _MOVEMENT_DEFAULT_PRESET["glide_speed"]) or _MOVEMENT_DEFAULT_PRESET["glide_speed"])
_movement_glide_boost: float = float(_movement_boot_preset.get("glide_boost", _MOVEMENT_DEFAULT_PRESET["glide_boost"]) or _MOVEMENT_DEFAULT_PRESET["glide_boost"])
_movement_glide_air_control: float = float(_movement_boot_preset.get("glide_air_control", _MOVEMENT_DEFAULT_PRESET["glide_air_control"]) or _MOVEMENT_DEFAULT_PRESET["glide_air_control"])
_movement_dash_speed: float = float(_movement_boot_preset.get("dash_speed", _MOVEMENT_DEFAULT_PRESET["dash_speed"]) or _MOVEMENT_DEFAULT_PRESET["dash_speed"])
_movement_zero_vault_costs: bool = bool(_movement_boot_preset.get("zero_vault_costs", True))
_movement_no_target: bool = False
_movement_noclip: bool = bool(_inventory_settings.get("movement_noclip", False))


# Loot rarity modifier controls. These are GameState-local, so the live GameState
# object changes on map/world travel. Store user intent here and re-apply only
# when a new GameState is detected, not every frame.
_RARITY_ROWS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("common", "Common", ("CommonModifier",)),
    ("uncommon", "Uncommon", ("UncommonModifier",)),
    ("rare", "Rare", ("RareModifier",)),
    ("epic", "Epic", ("VeryRareModifier", "EpicModifier")),
    ("legendary", "Legendary", ("LegendaryModifier",)),
    ("pearlescent", "Pearlescent", ("PearlModifier", "PearlescentModifier")),
)
_old_rarity_disabled_settings = dict(_inventory_settings.get("rarity_disabled", {}) or {})
_saved_rarity_weights = dict(_inventory_settings.get("rarity_weights", {}) or {})
_rarity_weights: dict[str, float] = {}
for _key, _label, _fields in _RARITY_ROWS:
    if _key in _saved_rarity_weights:
        try:
            _val = float(_saved_rarity_weights.get(_key, 1.0))
        except Exception:
            _val = 1.0
    else:
        _val = 0.0 if bool(_old_rarity_disabled_settings.get(_key, False)) else 1.0
    _rarity_weights[_key] = max(0.0, min(1.0, float(_val)))
_rarity_auto_reapply: bool = bool(_inventory_settings.get("rarity_auto_reapply", True))
_rarity_status: str = "Rarity drop weights idle. 100% is normal weight, 50% is half weight, 0% disables that rarity."
_rarity_last_gamestate_key: str = ""
_rarity_last_state_key: str = ""
_rarity_cached_gamestate: object | None = None
_rarity_cached_state: object | None = None
_rarity_cached_state_key: str = ""
_rarity_next_world_check: float = 0.0
_rarity_reapply_until: float = 0.0
_rarity_reapply_next_try: float = 0.0
_rarity_reapply_reason: str = ""
_rarity_last_fast_check: float = 0.0
_rarity_reapply_scan_used: bool = False
_background_next_rarity_tick: float = 0.0
_background_next_movement_tick: float = 0.0
_hud_native_toasts_enabled: bool = bool(_inventory_settings.get("hud_native_toasts", False))
_active_tab: int = 0
_legit_root_search: str = ""
_legit_root_index: int = 0
_legit_type_index: int = 0
_legit_manufacturer_index: int = 0
_legit_part_search: str = ""
_legit_slot_search: dict[str, str] = {}
_legit_part_table_index: int = 0
_legit_slot_page: int = 0
_legit_grid_hscroll: int = 0
_legit_unlock_rules: bool = False
_ui_hscroll_offsets: dict[int, int] = {}
_boosting_column_scroll: int = 0
_legit_selected_parts_text: str = ""
_legit_level: int = 60
_legit_seed: int = 2
_legit_signature_value: int = int(_inventory_settings.get("legit_signature_value", 1) or 1)
_legit_status: str = "Select a root, add part keys/serials one per line, then Validate or Build."
_legit_human: str = ""
_legit_base85: str = ""
_legit_basic_validation_input: str = ""
_legit_basic_validation_output: str = "Paste one @U/Base85 or decoded human serial, then Validate Basic."
_legit_bulk_validation_input: str = ""
_legit_bulk_validation_output: str = "Paste one serial per line, then Validate Bulk."
_validator_thread: threading.Thread | None = None
_validator_cancel: bool = False
_validator_progress: dict[str, object] = {"running": False, "label": "Idle", "done": 0, "total": 0, "passed": 0, "failed": 0}
_validator_lock = threading.RLock()
_catalog_validator_thread: threading.Thread | None = None
_catalog_validator_cancel: bool = False
_catalog_validator_progress: dict[str, object] = {"running": False, "source": "", "done": 0, "total": 0, "passed": 0, "failed": 0}
_catalog_validator_lock = threading.RLock()
# Catalog validation runs off-thread, but BLImGui/pyunrealsdk and the live
# catalog lists are read by the game/UI thread.  Never mutate those live rows
# or touch HUD/logging from the worker; queue patches and flush them in _draw_ui.
_catalog_validator_pending: dict[str, dict[str, dict[str, str]]] = {"GZO": {}, "Lootlemon": {}}
_catalog_validator_pending_complete: dict[str, dict[str, object] | None] = {"GZO": None, "Lootlemon": None}

# Legit Builder caches: expensive rule/tag checks are keyed by current inputs and
# reused while the menu is merely being redrawn.  They are naturally invalidated
# when root, selected parts, or search text changes.
_legit_cache: dict[str, object] = {
    "roots": None,
    "types": None,
    "mans": {},
    "root_options": {},
    "slots": {},
    "slot_meta": {},
    "allowed": {},
    "describe": {},
}

def _legit_selected_signature() -> str:
    return "\n".join(_legit_selected_part_lines_raw())

def _legit_clear_dynamic_cache(clear_static: bool = False) -> None:
    try:
        _legit_cache.get("slot_meta", {}).clear()
        _legit_cache.get("allowed", {}).clear()
        _legit_cache.get("describe", {}).clear()
        if clear_static:
            _legit_cache["types"] = None
            _legit_cache.get("mans", {}).clear()
            _legit_cache.get("root_options", {}).clear()
            _legit_cache.get("slots", {}).clear()
    except Exception:
        pass

_itempool_search: str = ""
_itempool_category: str = "All"
_itempool_selected_index: int = 0
_itempool_count: int = 1
_itempool_level: int = _ITEMPOOL_DEFAULT_LEVEL
_itempool_page: int = 0
_ITEMPOOL_PAGE_SIZE: int = 90
_travel_map_search: str = ""
_travel_station_search: str = ""
_travel_selected_map_index: int = 0
_travel_selected_station_index: int = 0
_travel_map_scroll_offset: int = 0
_travel_station_scroll_offset: int = 0
_travel_show_all_stations: bool = bool(_inventory_settings.get("travel_show_all_stations", False))
_favorite_itempools: set[str] = set(str(x) for x in _inventory_settings.get("favorite_itempools", []) if str(x).strip())
_favorite_travel_maps: set[str] = _canonicalize_travel_map_values(_inventory_settings.get("favorite_travel_maps", []))
_favorite_travel_stations: set[str] = set(str(x) for x in _inventory_settings.get("favorite_travel_stations", []) if str(x).strip())

_favorite_itempool_descriptions: dict[str, str] = {str(k): str(v) for k, v in dict(_inventory_settings.get("favorite_itempool_descriptions", {}) or {}).items() if str(k).strip() and str(v).strip()}
_favorite_travel_map_descriptions: dict[str, str] = _canonicalize_travel_map_descriptions(_inventory_settings.get("favorite_travel_map_descriptions", {}) or {})
_favorite_travel_station_descriptions: dict[str, str] = {str(k): str(v) for k, v in dict(_inventory_settings.get("favorite_travel_station_descriptions", {}) or {}).items() if str(k).strip() and str(v).strip()}

_CURRENCY_KINDS = ["cash", "eridium", "vaultcard1", "vaultcard2", "vaultcard3"]
_EXP_TRACKS = ["player", "specialization", "vaultcard_xp_1", "vaultcard_xp_2", "vaultcard_xp_3"]
_MAX_WALLET_AMOUNT = 2_147_483_647
_MAX_PLAYER_LEVEL = 60
_MAX_SPEC_LEVEL = 701
_MAX_VAULT_CARD_LEVEL = 9_999_999



def _wrapped_text(text: str, accent: str | None = None) -> None:
    """Draw text that wraps to the current content width, including cyber-muted text.

    BLImGui/imgui.text does not wrap, and the cyber.muted helper uses colored text
    without wrapping. Use this for any explanatory/status text inside cards so it
    cannot spill outside the card bounds.
    """
    imgui = _blimgui.imgui
    color_pushed = False
    if accent and _cyber:
        color = getattr(_cyber, accent.upper(), None) if isinstance(accent, str) else None
        try:
            if color is not None:
                imgui.push_style_color(imgui.Col_.text, _cyber._v4(color))
                color_pushed = True
        except Exception:
            color_pushed = False
    try:
        try:
            imgui.text_wrapped(str(text))
        except Exception:
            imgui.text(str(text))
    finally:
        if color_pushed:
            try:
                imgui.pop_style_color()
            except Exception:
                pass

def _muted_wrapped(text: str) -> None:
    _wrapped_text(text, "muted")

def _clamp_int(value: int, minimum: int, maximum: int) -> int:
    return max(int(minimum), min(int(value), int(maximum)))


def _safe_object_key(obj: object | None) -> str:
    if obj is None:
        return ""
    try:
        return str(obj)
    except Exception:
        try:
            return repr(obj)
        except Exception:
            return str(id(obj))


def _max_level_for_track(track_index: int) -> int:
    if int(track_index) == 0:
        return _MAX_PLAYER_LEVEL
    if int(track_index) == 1:
        return _MAX_SPEC_LEVEL
    return _MAX_VAULT_CARD_LEVEL


def _default_level_for_track(track_index: int) -> int:
    if int(track_index) == 1:
        return _MAX_SPEC_LEVEL
    if int(track_index) == 0:
        return _MAX_PLAYER_LEVEL
    return 1


def _status_accent_for_message(message: str) -> str:
    text = str(message or "").lower()
    if any(token in text for token in ("failed", "error", "no ", "could not", "invalid", "exception")):
        return "red"
    if any(token in text for token in ("delivered", "requested", "set ", "spawned", "dropped", "activated", "travel", "saved", "loaded", "valid")):
        return "green"
    return "cyan"


def _hud_cancel_pill_timer() -> None:
    """Cancel any delayed HUD-pill clear without touching the visible widgets."""
    global _hud_pill_clear_timer
    t = _hud_pill_clear_timer
    _hud_pill_clear_timer = None
    try:
        if t is not None and t.is_alive() and t is not threading.current_thread():
            t.cancel()
    except Exception:
        pass


def _hud_timer_clear_pill(expected_generation: int) -> None:
    """Timer-thread backup: expire state only; UI tick does native cleanup."""
    global _hud_pill_message, _hud_pill_until
    try:
        if int(expected_generation) != int(_hud_pill_generation):
            return
        # Never touch UMG/AddToViewport widgets from a Python Timer thread.  That
        # can hard-crash during client join/travel. The next HUD/UI tick will
        # forget or clear native references on the game thread.
        _hud_pill_message = ""
        _hud_pill_until = 0.0
    except Exception:
        pass


def _hud_schedule_pill_clear(delay: float) -> None:
    """Start a replacement timer so every new pill clears itself after its own duration."""
    global _hud_pill_clear_timer, _hud_pill_generation
    _hud_cancel_pill_timer()
    _hud_pill_generation += 1
    generation = int(_hud_pill_generation)
    try:
        seconds = max(0.25, min(30.0, float(delay)))
    except Exception:
        seconds = 5.0
    try:
        timer = threading.Timer(seconds, _hud_timer_clear_pill, args=(generation,))
        timer.daemon = True
        _hud_pill_clear_timer = timer
        timer.start()
    except Exception:
        _hud_pill_clear_timer = None


def _set_status_pill(message: str, accent: str | None = None, duration: float = 8.0) -> None:
    """Show a short confirmation pill in-menu and briefly on the gameplay HUD."""
    global _status_pill_message, _status_pill_accent, _status_pill_until
    global _hud_pill_message, _hud_pill_accent, _hud_pill_until
    text = str(message or "").strip()
    if not text:
        _status_pill_message = ""
        _status_pill_until = 0.0
        try:
            if _hud_native_allowed():
                _hud_clear_viewport_pill_overlay()
            else:
                _hud_forget_viewport_pill_overlay()
        except Exception:
            pass
        return
    # Keep both pills compact even when the log message is verbose.
    if len(text) > 180:
        text = text[:177].rstrip() + "..."
    pill_accent = str(accent or _status_accent_for_message(text) or "cyan")
    _status_pill_message = text
    _status_pill_accent = pill_accent
    try:
        _status_pill_until = time.monotonic() + max(1.5, float(duration))
    except Exception:
        _status_pill_until = time.monotonic() + 8.0
    _hud_pill_message = text
    _hud_pill_accent = pill_accent
    try:
        # HUD pill is intentionally shorter than the in-menu status line.
        hud_duration = max(2.0, min(5.0, float(duration)))
    except Exception:
        hud_duration = 4.0
    _hud_pill_until = time.monotonic() + hud_duration
    if _hud_native_allowed():
        try:
            # Also try to draw immediately; the tick hook keeps it alive/cleans it up.
            _hud_ensure_pill(_hud_pill_message, _hud_pill_accent)
        except Exception:
            pass
        # The AddToViewport pill can outlive/miss the BL4 UI tick.  Use a replacement
        # timer as a hard cleanup path; each new pill cancels the previous timer so an
        # older message cannot clear a newer one early.
        _hud_schedule_pill_clear(hud_duration)
    else:
        # Keep the in-menu status pill, but do not create/update UMG viewport widgets
        # while we are a joined client. BL4 can hard-crash on stale HUD objects there.
        try:
            _hud_forget_viewport_pill_overlay()
            _hud_cancel_pill_timer()
        except Exception:
            pass


def _is_main_thread() -> bool:
    try:
        ident = threading.get_ident()
        return ident == _MAIN_THREAD_IDENT or (_UI_THREAD_IDENT is not None and ident == _UI_THREAD_IDENT)
    except Exception:
        return True


def _movement_is_listen_host() -> bool:
    """True only when this client is the listen host/server.

    Keep this cheap and client-safe: check local PC authority before touching
    World/GameState/NetDriver. Joining another player as a client can leave those
    objects in a transient state where reflective traversal is unsafe.
    """
    if not _local_pc_has_authority_fast():
        try:
            _hud_forget_viewport_pill_overlay()
        except Exception:
            pass
        return False
    try:
        world, _gs = _gbc_session_world_and_gamestate()
    except Exception:
        world = None
    try:
        return bool(_gbc_is_listen_host_world(world))
    except Exception:
        return True


def _movement_is_listen_host_cached(now: float | None = None) -> bool:
    """Cached version for HUD-tick hot paths."""
    global _movement_host_cache_value, _movement_host_cache_until
    try:
        t = float(now if now is not None else time.monotonic())
    except Exception:
        t = 0.0
    try:
        if t < float(_movement_host_cache_until or 0.0):
            return bool(_movement_host_cache_value)
    except Exception:
        pass
    value = _movement_is_listen_host()
    _movement_host_cache_value = bool(value)
    # Host/client role cannot change many times per second; keep this out of the
    # per-HUD-tick path while still reacting quickly after travel.
    _movement_host_cache_until = t + (1.0 if value else 2.0)
    return bool(value)

def _movement_off_host_status(action: str = "movement tools") -> str:
    return f"Client mode — {action} paused until you are host."

def _movement_require_host(action: str = "movement tools", *, quiet: bool = False) -> bool:
    global _movement_status, _movement_apply_on_load_done, _movement_pending_apply, _movement_pending_apply_due, _movement_pending_apply_reason
    if _movement_is_listen_host():
        return True
    _movement_pending_apply = False
    _movement_pending_apply_due = 0.0
    _movement_pending_apply_reason = ""
    _movement_apply_on_load_done = True
    _movement_status = _movement_off_host_status(action)
    if not quiet:
        try:
            _log(_movement_status)
            _set_status_pill(_movement_status, "gold")
        except Exception:
            pass
    return False



def _rarity_save_settings() -> None:
    try:
        save_extra_settings(
            rarity_weights={k: float(max(0.0, min(1.0, float(v)))) for k, v in dict(_rarity_weights).items()},
            rarity_auto_reapply=bool(_rarity_auto_reapply),
        )
    except Exception as exc:
        try:
            _log(f"Rarity settings save failed: {exc!r}")
        except Exception:
            pass


def _rarity_any_custom() -> bool:
    try:
        return any(abs(float(v) - 1.0) > 0.0001 for v in dict(_rarity_weights).values())
    except Exception:
        return False


def _rarity_obj_world(obj: object | None) -> object | None:
    """Resolve an object's current World without any broad find_all scan."""
    if obj is None:
        return None
    for attr in ("GetWorld", "World"):
        try:
            value = getattr(obj, attr, None)
            world = value() if callable(value) else value
            if world is not None:
                return world
        except Exception:
            pass
    for attr in ("Level", "PersistentLevel", "Outer", "outer"):
        try:
            parent = getattr(obj, attr, None)
        except Exception:
            parent = None
        if parent is None or parent is obj:
            continue
        for wattr in ("OwningWorld", "World", "GetWorld"):
            try:
                value = getattr(parent, wattr, None)
                world = value() if callable(value) else value
                if world is not None:
                    return world
            except Exception:
                pass
    return None


def _rarity_gamestate_has_local_player(gs: object | None, pc: object | None) -> bool:
    if gs is None or pc is None:
        return False
    try:
        local_ps = getattr(pc, "PlayerState", None)
    except Exception:
        local_ps = None
    if local_ps is None:
        return False
    try:
        arr = getattr(gs, "PlayerArray", None)
        if arr is None:
            return False
        for i in range(len(arr)):
            try:
                if arr[i] is local_ps or str(arr[i]) == str(local_ps):
                    return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def _rarity_mark_reapply(reason: str = "world change", seconds: float = 12.0) -> None:
    """Arm a short, low-duty reapply window for map travel/GameState replacement."""
    global _rarity_reapply_until, _rarity_reapply_next_try, _rarity_reapply_reason, _rarity_reapply_scan_used
    if not _rarity_auto_reapply or not _rarity_any_custom():
        return
    _rarity_reapply_scan_used = False
    try:
        now = time.monotonic()
    except Exception:
        now = 0.0
    try:
        _rarity_reapply_until = max(float(_rarity_reapply_until or 0.0), now + max(1.0, float(seconds)))
    except Exception:
        _rarity_reapply_until = now + 12.0
    _rarity_reapply_next_try = 0.0
    _rarity_reapply_reason = str(reason or "world change")[:80]


def _rarity_targeted_find_gamestate() -> tuple[object | None, object | None]:
    """Rare fallback used only during a reapply burst, never every frame.

    Prefer direct pointers, but if those are stale during travel, scan only likely
    GameState classes and choose one with a RarityState. This is intentionally not
    part of the steady-state tick path.
    """
    best = None
    best_score = -1
    for cls_name in ("OakGameState", "GbxGameState", "GameStateBase", "GameState"):
        try:
            objs = unrealsdk.find_all(cls_name, False) or []
        except Exception:
            objs = []
        for gs in objs:
            if gs is None:
                continue
            try:
                s = str(gs)
                if "Default__" in s or "ClassDefaultObject" in s:
                    continue
            except Exception:
                s = ""
            try:
                state = _rarity_state_for_gamestate(gs)
            except Exception:
                state = None
            if state is None:
                continue
            score = 50
            try:
                pa = getattr(gs, "PlayerArray", None)
                score += min(10, len(pa) if pa is not None else 0)
            except Exception:
                pass
            try:
                if "PersistentLevel" in s or "World_P" in s:
                    score += 5
            except Exception:
                pass
            if score > best_score:
                best = gs
                best_score = score
    if best is None:
        return None, None
    try:
        return _rarity_obj_world(best), best
    except Exception:
        return None, best


def _rarity_current_world_gamestate() -> tuple[object | None, object | None]:
    """Resolve the active GameState using the path proven by the pyexec probe.

    BL4 returns None for GetWorld()/World on the local OakPlayerController and
    pawn in several maps.  The reliable path from the probe is:
        ENGINE.GameViewport.World.GameState.RarityState

    Keep this function intentionally tiny: no get_pc(), no PlayerArray walk, and
    no find_all.  It is safe to call during the short travel reapply burst.
    """
    try:
        viewport = getattr(ENGINE, "GameViewport", None)
        world = getattr(viewport, "World", None) if viewport is not None else None
        gs = getattr(world, "GameState", None) if world is not None else None
        if gs is not None and _rarity_state_for_gamestate(gs) is not None:
            return world, gs
    except Exception:
        pass
    return None, None

def _rarity_gamestate_key(gs: object | None) -> str:
    if gs is None:
        return ""
    try:
        return str(gs)
    except Exception:
        try:
            return repr(gs)
        except Exception:
            return str(id(gs))


def _rarity_object_key(obj: object | None) -> str:
    if obj is None:
        return ""
    try:
        return str(obj)
    except Exception:
        try:
            return repr(obj)
        except Exception:
            return str(id(obj))


def _rarity_state_for_gamestate(gs: object | None) -> object | None:
    """Resolve GameState.RarityState with a cached GameState->state pointer.

    This avoids repeated broad discovery during gameplay. GameState comes directly
    from Engine.GameViewport.World; if the cached GameState is still the same,
    reuse its already-resolved RarityState wrapper.
    """
    global _rarity_cached_gamestate, _rarity_cached_state, _rarity_cached_state_key
    if gs is None:
        _rarity_cached_gamestate = None
        _rarity_cached_state = None
        _rarity_cached_state_key = ""
        return None
    try:
        if _rarity_cached_gamestate is gs and _rarity_cached_state is not None:
            return _rarity_cached_state
    except Exception:
        pass
    state = None
    for attr in ("RarityState", "RarityModifier", "RarityModifiers", "GameRarityState"):
        try:
            candidate = getattr(gs, attr, None)
            if candidate is not None:
                state = candidate
                break
        except Exception:
            pass
    _rarity_cached_gamestate = gs
    _rarity_cached_state = state
    _rarity_cached_state_key = _rarity_object_key(state)
    return state


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


def _rarity_float_value(mod: object | None) -> tuple[float | None, float | None]:
    if mod is None:
        return None, None
    value = None
    base = None
    for name in ("Value", "CurrentValue", "Current"):
        try:
            if hasattr(mod, name):
                value = float(getattr(mod, name))
                break
        except Exception:
            pass
    for name in ("BaseValue", "InitialValue", "Base"):
        try:
            if hasattr(mod, name):
                base = float(getattr(mod, name))
                break
        except Exception:
            pass
    return value, base


def _rarity_set_float(mod: object | None, value: float) -> int:
    if mod is None:
        return 0
    writes = 0
    try:
        v = float(value)
    except Exception:
        v = 1.0
    for name in ("Value", "CurrentValue", "Current", "BaseValue", "InitialValue", "Base"):
        try:
            if hasattr(mod, name):
                setattr(mod, name, v)
                writes += 1
        except Exception:
            pass
    # Some wrapped structs expose setter methods rather than fields on certain builds.
    for name in ("SetValue", "SetBaseValue", "SetCurrentValue"):
        try:
            fn = getattr(mod, name, None)
            if callable(fn):
                fn(v)
                writes += 1
        except Exception:
            pass
    return writes


def _rarity_apply_to_gamestate(gs: object | None, *, log_result: bool = False) -> str:
    """Write configured rarity weights directly to the supplied GameState."""
    global _rarity_status, _rarity_last_gamestate_key, _rarity_last_state_key
    state = _rarity_state_for_gamestate(gs)
    if state is None:
        _rarity_status = "No GameState.RarityState found yet. Load into a world and try again."
        if log_result:
            _log(_rarity_status)
        return _rarity_status
    writes = 0
    parts: list[str] = []
    for key, label, fields in _RARITY_ROWS:
        try:
            target = max(0.0, min(1.0, float(_rarity_weights.get(key, 1.0))))
        except Exception:
            target = 1.0
        mod = _rarity_get_modifier(state, fields)
        writes += _rarity_set_float(mod, target)
        parts.append(f"{label}={int(round(target * 100.0))}%")
    _rarity_last_gamestate_key = _rarity_gamestate_key(gs)
    _rarity_last_state_key = _rarity_object_key(state)
    _rarity_status = "Rarity drop weights applied: " + ", ".join(parts) + f". Writes: {writes}."
    if log_result:
        _log(_rarity_status)
        try:
            _set_status_pill(_rarity_status, "purple")
        except Exception:
            pass
    return _rarity_status


def _rarity_apply_modifiers(*, log_result: bool = False, force_all: bool = False) -> str:
    """Apply configured rarity drop weights to the current GameState only."""
    _world, gs = _rarity_current_world_gamestate()
    return _rarity_apply_to_gamestate(gs, log_result=log_result)


def _rarity_set_only(allowed_key: str) -> None:
    allowed_key = str(allowed_key or "").strip().lower()
    for key, _label, _fields in _RARITY_ROWS:
        _rarity_weights[key] = 1.0 if key == allowed_key else 0.0
    _rarity_save_settings()
    _rarity_apply_modifiers(log_result=True)


def _rarity_reset_all() -> None:
    for key, _label, _fields in _RARITY_ROWS:
        _rarity_weights[key] = 1.0
    _rarity_save_settings()
    _rarity_apply_modifiers(log_result=True, force_all=True)


def _rarity_live_matches_desired(state: object | None) -> bool:
    """Cheaply verify the current GameState still has the configured weights."""
    if state is None:
        return False
    for key, _label, fields in _RARITY_ROWS:
        try:
            desired = max(0.0, min(1.0, float(_rarity_weights.get(key, 1.0))))
        except Exception:
            desired = 1.0
        mod = _rarity_get_modifier(state, fields)
        live, base = _rarity_float_value(mod)
        # Value is the important live field; base/initial is written too, but some
        # wrapped structs expose only one side on certain builds.
        if live is None:
            if base is None:
                return False
            live = base
        try:
            if abs(float(live) - float(desired)) > 0.001:
                return False
        except Exception:
            return False
    return True


def _rarity_background_tick() -> None:
    """Short retry burst after module load or travel hooks.

    There is no steady-state verification loop here.  The HUD tick only calls
    this while _rarity_reapply_until is active.  Each retry uses the proven
    GameViewport->World->GameState path and then shuts the burst off on success.
    """
    global _rarity_reapply_until, _rarity_reapply_next_try
    if not _rarity_auto_reapply or not _rarity_any_custom():
        return
    try:
        now = time.monotonic()
    except Exception:
        now = 0.0
    try:
        if now > float(_rarity_reapply_until or 0.0):
            return
        if now < float(_rarity_reapply_next_try or 0.0):
            return
    except Exception:
        return
    _rarity_reapply_next_try = now + 0.75
    _world, gs = _rarity_current_world_gamestate()
    if _rarity_state_for_gamestate(gs) is None:
        return
    _rarity_apply_to_gamestate(gs, log_result=False)
    if _rarity_last_gamestate_key:
        _rarity_reapply_until = 0.0
        _rarity_reapply_next_try = 0.0

def _draw_rarity_disabler_card() -> None:
    global _rarity_auto_reapply
    opened = _begin_resizable_card("card_rarity_disabler", "Rarity Drop Weights", "purple", 325, 285, 520) if _cyber else True
    if opened:
        _muted_wrapped("These sliders control drop-weight multipliers from GameState.RarityState. 100% is the normal vanilla weight, 50% is half weight, and 0% effectively removes that rarity from the drop pool.")
        _card_button_row([
            ("Apply", lambda: (_rarity_save_settings(), _rarity_apply_modifiers(log_result=True)), "purple", 80, 0),
            ("Reset All", _rarity_reset_all, "gold", 100, 0),
            ("Only Legendary", lambda: _rarity_set_only("legendary"), "gold", 140, 0),
            ("Only Pearlescent", lambda: _rarity_set_only("pearlescent"), "pink", 160, 0),
        ])
        old_auto = bool(_rarity_auto_reapply)
        _rarity_auto_reapply = _checkbox("Auto reapply on world change###msbt_rarity_auto_world", bool(_rarity_auto_reapply))
        if old_auto != bool(_rarity_auto_reapply):
            _rarity_save_settings()
        changed = False
        for key, label, _fields in _RARITY_ROWS:
            try:
                current_pct = float(_rarity_weights.get(key, 1.0)) * 100.0
            except Exception:
                current_pct = 100.0
            new_pct = _input_float_slider(f"{label} Weight###msbt_rarity_weight_{key}", current_pct, 0.0, 100.0, "%.0f%%")
            new_pct = max(0.0, min(100.0, float(new_pct)))
            new_val = new_pct / 100.0
            if abs(new_val - float(_rarity_weights.get(key, 1.0))) > 0.0001:
                _rarity_weights[key] = new_val
                changed = True
        if changed:
            _rarity_save_settings()
            _rarity_apply_modifiers(log_result=True)
        _muted_wrapped("Auto reapply is event/burst based: it applies after travel without continuously reading live modifiers.")
        _muted_wrapped(_rarity_status)
    if _cyber:
        _end_resizable_card()


def _flush_worker_log_lines() -> None:
    """Move logs produced by refresh worker threads onto the game/UI thread.

    pyunrealsdk/UMG calls are not safe from Python worker threads.  The Lootlemon
    and GZO refreshers fetch/parse in the background, so any diagnostics produced
    there must be buffered and emitted later by the normal UI polling path.
    """
    if not _is_main_thread():
        return
    with _log_lock:
        pending = list(_pending_worker_log_lines)
        _pending_worker_log_lines.clear()
    for line in pending[-80:]:
        try:
            logging.info(line)
        except Exception:
            pass
        with _log_lock:
            _log_lines.append(line)
            del _log_lines[:-80]


def _log(message: str) -> None:
    line = f"[Matts SDK Boosting Tools | UI] {message}"
    if not _is_main_thread():
        # Never touch pyunrealsdk logging, HUD widgets, or status pill state from
        # background refresh threads.  Doing so can crash near the end of a long
        # Lootlemon extraction when errors/progress are logged from the worker.
        with _log_lock:
            _pending_worker_log_lines.append(line)
            del _pending_worker_log_lines[:-80]
        return
    try:
        logging.info(line)
    except Exception:
        pass
    with _log_lock:
        _log_lines.append(line)
        del _log_lines[:-80]
    # Surface action results in the visible header as a confirmation pill.
    # Ignore noisy internal diagnostics/title-apply messages.
    m = str(message or "")
    lower = m.lower()
    if not any(skip in lower for skip in ("applied game window title", "begin_child", "end_child", "could not save custom game title")):
        _set_status_pill(m)



def _poll_serial_delivery_status_for_pill() -> None:
    """Mirror the serial delivery state machine into the menu + HUD pill."""
    global _last_serial_delivery_status_seen
    try:
        prog = serial_delivery_progress()
        msg = str(prog.get("message") or serial_delivery_status() or "").strip()
    except Exception:
        msg = ""
    if not msg or msg == _last_serial_delivery_status_seen:
        return
    _last_serial_delivery_status_seen = msg
    # Keep delivery status visible long enough for the HUD tick to redraw the bar.
    _set_status_pill(msg, "cyan", duration=7.0)

def _draw_status_pill() -> None:
    """Draw the current confirmation/status pill if it is still active."""
    if not _status_pill_message:
        return
    try:
        if time.monotonic() > float(_status_pill_until):
            return
    except Exception:
        pass
    imgui = _blimgui.imgui
    try:
        imgui.spacing()
    except Exception:
        pass
    label = f"● {_status_pill_message}"
    if _cyber:
        try:
            _wrapped_text(label, _status_pill_accent)
        except Exception:
            imgui.text_wrapped(label)
    else:
        try:
            imgui.text_wrapped(label)
        except Exception:
            imgui.text(label)
    try:
        prog = serial_delivery_progress()
        if bool(prog.get("active", False)):
            frac = max(0.0, min(1.0, float(prog.get("fraction", 0.0) or 0.0)))
            bar_label = str(prog.get("label") or f"{int(frac * 100)}%")
            progress_bar = getattr(imgui, "progress_bar", None)
            if callable(progress_bar):
                try:
                    progress_bar(frac, (520, 18), bar_label)
                except TypeError:
                    try:
                        progress_bar(frac, bar_label)
                    except Exception:
                        imgui.text(bar_label)
            else:
                imgui.text(bar_label)
    except Exception:
        pass
    try:
        imgui.separator()
    except Exception:
        pass



# ---------------- lightweight gameplay HUD pill ----------------

def _hud_make_vec2(x: float, y: float):
    return unrealsdk.make_struct("Vector2D", X=float(x), Y=float(y))


def _hud_make_color(r: float, g: float, b: float, a: float = 1.0):
    return unrealsdk.make_struct("LinearColor", R=float(r), G=float(g), B=float(b), A=float(a))


def _hud_try_call(obj, name: str, *args) -> bool:
    if obj is None:
        return False
    try:
        getattr(obj, name)(*args)
        return True
    except Exception:
        return False


def _hud_live(obj) -> bool:
    if obj is None:
        return False
    try:
        _ = obj.Name
        return True
    except Exception:
        return False


def _hud_class(path: str):
    try:
        return unrealsdk.find_object("Class", path)
    except Exception:
        return unrealsdk.find_class(path)


def _hud_widget(path: str, outer):
    return unrealsdk.construct_object(_hud_class(path), outer)


def _hud_set_slot(widget, x: float, y: float, w: float, h: float, z: int = 0) -> None:
    _hud_try_call(widget, "SetRenderTranslation", _hud_make_vec2(x, y))
    slot = getattr(widget, "slot", None) or getattr(widget, "Slot", None)
    if slot is not None:
        _hud_try_call(slot, "SetPosition", _hud_make_vec2(x, y))
        _hud_try_call(slot, "SetSize", _hud_make_vec2(w, h))
        _hud_try_call(slot, "SetZOrder", int(z))
        _hud_try_call(slot, "SetAutoSize", False)


def _hud_set_color(widget, rgba: tuple[float, float, float, float]) -> None:
    c = _hud_make_color(*rgba)
    _hud_try_call(widget, "SetBrushColor", c)
    _hud_try_call(widget, "SetColorAndOpacity", c)
    _hud_try_call(widget, "SetRenderOpacity", rgba[3])


def _hud_add_child(parent, child) -> None:
    if parent is None or child is None:
        return
    if hasattr(parent, "AddChild"):
        parent.AddChild(child)
    elif hasattr(parent, "SetContent"):
        parent.SetContent(child)


def _hud_main_hud():
    try:
        huds = [w for w in unrealsdk.find_all("UserWidget", False)
                if "WBP_MainHud_C_" in str(w) and "Default__" not in str(w) and hasattr(w, "WidgetTree")]
    except Exception:
        return None
    for hud in huds:
        try:
            if hud.WidgetTree and hud.WidgetTree.RootWidget:
                return hud
        except Exception:
            pass
    return huds[0] if huds else None


def _hud_accent_rgba(accent: str) -> tuple[float, float, float, float]:
    a = str(accent or "").lower()
    if a in ("red", "danger", "error"):
        return (0.62, 0.06, 0.08, 0.90)
    if a in ("green", "success"):
        return (0.05, 0.45, 0.18, 0.90)
    if a in ("gold", "yellow", "warn", "warning"):
        return (0.58, 0.43, 0.05, 0.92)
    if a in ("pink", "purple"):
        return (0.48, 0.12, 0.52, 0.90)
    return (0.02, 0.35, 0.42, 0.90)


def _hud_get_host():
    """Return a standalone AddToViewport CanvasPanel host for the HUD pill.

    The working native menu POC proved the important BL4 detail: WBP_MainHud_C.WidgetTree
    objects can exist and still not be the painted Slate layer.  A manually-created
    UserWidget + WidgetTree + CanvasPanel + AddToViewport is the reliable draw path.
    Keep WBP_MainHud only as a live-game/outer sanity check, and draw the pill into
    this separate non-interactive viewport overlay.
    """
    global _hud_pill_host, _hud_pill_host_hud_name, _hud_pill_overlay_widget
    global _hud_pill_root, _hud_pill_box, _hud_pill_text, _hud_pill_progress_bg, _hud_pill_progress_fill, _hud_pill_last_message, _hud_pill_last_accent, _hud_pill_last_progress

    if not _hud_native_allowed():
        _hud_forget_viewport_pill_overlay()
        return None, None

    # Hot path: do not scan all UserWidgets every game HUD tick.  Once the
    # standalone viewport overlay exists, keep reusing it; full teardown/recreate
    # paths handle map travel or stale widgets.  The previous version called
    # find_all("UserWidget") through _hud_main_hud() on every tick, which is very
    # expensive on the game thread.
    if _hud_live(_hud_pill_overlay_widget) and _hud_live(_hud_pill_host):
        return _hud_pill_overlay_widget, _hud_pill_host

    hud = _hud_main_hud()
    hud_name = ""
    try:
        hud_name = str(getattr(hud, "Name", "") or hud or "")
    except Exception:
        hud_name = ""

    # Stale/removed overlay: drop all cached child widgets and recreate from the
    # same AddToViewport path as BL4_Native_Mods_Menu_POC.
    _hud_pill_overlay_widget = None
    _hud_pill_host = None
    _hud_pill_root = None
    _hud_pill_box = None
    _hud_pill_text = None
    _hud_pill_progress_bg = None
    _hud_pill_progress_fill = None
    _hud_pill_last_message = ""
    _hud_pill_last_accent = ""
    _hud_pill_last_progress = -1.0

    try:
        try:
            pc = mods_base.get_pc(possibly_loading=True)
        except Exception:
            pc = None
        outer = pc if pc is not None else hud
        if outer is None:
            return None, None

        overlay = _hud_widget("/Script/UMG.UserWidget", outer)
        overlay.WidgetTree = unrealsdk.construct_object(
            _hud_class("/Script/UMG.WidgetTree"),
            overlay,
        )
        canvas = _hud_widget("/Script/UMG.CanvasPanel", overlay.WidgetTree)
        overlay.WidgetTree.RootWidget = canvas

        # Non-interactive toast overlay.  Visibility 3 is HitTestInvisible in the
        # working POC, so it draws but does not eat game input.
        _hud_try_call(canvas, "SetVisibility", 3)
        _hud_try_call(canvas, "SetIsEnabled", True)
        _hud_try_call(canvas, "SetRenderOpacity", 1.0)
        _hud_try_call(overlay, "AddToViewport", 999999)
        _hud_try_call(overlay, "SetVisibility", 3)
        _hud_try_call(overlay, "SetRenderOpacity", 1.0)
        _hud_try_call(overlay, "ForceLayoutPrepass")

        _hud_pill_overlay_widget = overlay
        _hud_pill_host = canvas
        _hud_pill_host_hud_name = hud_name
        try:
            logging.info("[Matts SDK Boosting Tools | UI] Created AddToViewport HUD pill host")
        except Exception:
            pass
        return overlay, canvas
    except Exception as exc:
        try:
            logging.error(f"[Matts SDK Boosting Tools | UI] AddToViewport HUD pill host failed: {exc!r}")
        except Exception:
            pass
        return None, None

def _hud_destroy_pill() -> None:
    """Remove the actually visible pill widgets immediately.

    Console testing showed that expiring the timer alone does not remove the
    visible pill, while RemoveFromParent on _hud_pill_box/_hud_pill_text does.
    Keep this as the one hard-clear path and call it from every expire/close/reset
    route before touching cached state or the viewport overlay.
    """
    global _hud_pill_root, _hud_pill_box, _hud_pill_text, _hud_pill_progress_bg, _hud_pill_progress_fill, _hud_pill_last_message, _hud_pill_last_accent, _hud_pill_last_progress
    for w in (_hud_pill_progress_fill, _hud_pill_progress_bg, _hud_pill_text, _hud_pill_box, _hud_pill_root):
        if _hud_live(w):
            _hud_try_call(w, "SetVisibility", 1)
            _hud_try_call(w, "SetRenderOpacity", 0.0)
            _hud_try_call(w, "RemoveFromParent")
    _hud_pill_root = None
    _hud_pill_box = None
    _hud_pill_text = None
    _hud_pill_progress_bg = None
    _hud_pill_progress_fill = None
    _hud_pill_last_message = ""
    _hud_pill_last_accent = ""
    _hud_pill_last_progress = -1.0


def _hud_clear_viewport_pill_overlay(cancel_timer: bool = True) -> None:
    if _hud_native_suppressed():
        _hud_forget_viewport_pill_overlay(cancel_timer=cancel_timer)
        return
    """Fully remove the AddToViewport HUD pill overlay and clear pending toast state.

    The pill host is a standalone viewport UserWidget, matching the working native
    menu POC path.  Because it lives outside the BLImGui window, closing/clearing
    the SDK Boosting Tools panel must explicitly remove this overlay too.
    """
    global _hud_pill_message, _hud_pill_accent, _hud_pill_until
    global _hud_pill_host, _hud_pill_host_hud_name, _hud_pill_overlay_widget
    global _hud_pill_root, _hud_pill_box, _hud_pill_text, _hud_pill_progress_bg, _hud_pill_progress_fill, _hud_pill_last_message, _hud_pill_last_accent, _hud_pill_last_progress

    if cancel_timer:
        try:
            _hud_cancel_pill_timer()
        except Exception:
            pass

    _hud_pill_message = ""
    _hud_pill_accent = "cyan"
    _hud_pill_until = 0.0

    # Hard-remove the visible widgets first.  This is the path verified in the
    # in-game console to actually clear stuck pills.
    try:
        _hud_destroy_pill()
    except Exception:
        pass
    if _hud_live(_hud_pill_overlay_widget):
        _hud_try_call(_hud_pill_overlay_widget, "SetVisibility", 1)
        _hud_try_call(_hud_pill_overlay_widget, "SetRenderOpacity", 0.0)
        _hud_try_call(_hud_pill_overlay_widget, "RemoveFromParent")

    _hud_pill_overlay_widget = None
    _hud_pill_host = None
    _hud_pill_host_hud_name = ""
    _hud_pill_root = None
    _hud_pill_box = None
    _hud_pill_text = None
    _hud_pill_progress_bg = None
    _hud_pill_progress_fill = None
    _hud_pill_last_message = ""
    _hud_pill_last_accent = ""
    _hud_pill_last_progress = -1.0


def _hud_get_desired_size(widget) -> tuple[float, float]:
    """Best-effort UMG desired size lookup with a safe fallback."""
    try:
        size = widget.GetDesiredSize()
        return float(getattr(size, "X", 0.0) or 0.0), float(getattr(size, "Y", 0.0) or 0.0)
    except Exception:
        return 0.0, 0.0



def _hud_estimate_line_count(text: str, max_chars_per_line: int = 34) -> int:
    try:
        import textwrap
        lines = 0
        for raw_line in str(text or "").splitlines() or [""]:
            wrapped = textwrap.wrap(raw_line, width=max(8, int(max_chars_per_line)), break_long_words=False, break_on_hyphens=False)
            lines += max(1, len(wrapped))
        return max(1, lines)
    except Exception:
        return max(1, (len(str(text or "")) // max(8, int(max_chars_per_line))) + 1)



def _hud_ensure_pill(message: str, accent: str) -> None:
    """Create/update the native HUD pill with minimal game-thread work.

    The first native implementation rebuilt layout every HUD tick: it scanned HUD
    widgets, SetText'd, ForceLayoutPrepass'd, measured desired size, recolored and
    reset every slot continuously.  That is why showing the pill could cut FPS in
    half.  This version only mutates UMG when the message/accent/progress bucket
    actually changes, and uses a cheap line-count estimate instead of layout
    prepass/desired-size queries.
    """
    global _hud_pill_root, _hud_pill_box, _hud_pill_text, _hud_pill_progress_bg, _hud_pill_progress_fill
    global _hud_pill_last_message, _hud_pill_last_accent, _hud_pill_last_progress, _hud_pill_last_w, _hud_pill_last_h
    hud, host = _hud_get_host()
    if hud is None or host is None:
        return

    text = f"● {str(message or '').strip()}"
    if len(text) > 160:
        text = text[:157].rstrip() + "..."

    pill_x = 50.0
    pill_y = 50.0
    pill_w = 560.0
    text_x = 16.0
    text_y = 10.0
    text_w = pill_w - 32.0
    min_h = 52.0
    min_text_h = 28.0
    try:
        prog = serial_delivery_progress()
    except Exception:
        prog = {"active": False, "fraction": 0.0}
    show_progress = bool(prog.get("active", False))
    progress_bar_h = 8.0
    progress_gap = 8.0
    progress_bottom_pad = 12.0
    frac = max(0.0, min(1.0, float(prog.get("fraction", 0.0) or 0.0))) if show_progress else -1.0
    # Progress can update many times per second; bucket it so we do not resize the
    # native fill widget every frame.  2% granularity is visually smooth enough.
    progress_bucket = round(frac * 50.0) / 50.0 if show_progress else -1.0

    if not _hud_live(_hud_pill_root):
        root = _hud_widget("/Script/UMG.CanvasPanel", hud.WidgetTree)
        _hud_try_call(root, "SetVisibility", 3)
        _hud_add_child(host, root)
        box = _hud_widget("/Script/UMG.Border", hud.WidgetTree)
        _hud_try_call(box, "SetVisibility", 3)
        _hud_add_child(root, box)
        tb = _hud_widget("/Script/UMG.TextBlock", hud.WidgetTree)
        _hud_try_call(tb, "SetVisibility", 3)
        _hud_try_call(tb, "SetAutoWrapText", True)
        _hud_try_call(tb, "SetWrapTextAt", text_w)
        _hud_add_child(root, tb)
        bg = _hud_widget("/Script/UMG.Border", hud.WidgetTree)
        _hud_try_call(bg, "SetVisibility", 1)
        _hud_try_call(bg, "SetRenderOpacity", 0.0)
        _hud_add_child(root, bg)
        fill = _hud_widget("/Script/UMG.Border", hud.WidgetTree)
        _hud_try_call(fill, "SetVisibility", 1)
        _hud_try_call(fill, "SetRenderOpacity", 0.0)
        _hud_add_child(root, fill)
        _hud_pill_root, _hud_pill_box, _hud_pill_text = root, box, tb
        _hud_pill_progress_bg, _hud_pill_progress_fill = bg, fill
        _hud_pill_last_message = ""
        _hud_pill_last_accent = ""
        _hud_pill_last_progress = -2.0
        _hud_pill_last_w = 0.0
        _hud_pill_last_h = 0.0

    # Nothing visible changed; leave UMG alone this tick.
    if (text == _hud_pill_last_message and str(accent or "") == _hud_pill_last_accent
            and abs(progress_bucket - float(_hud_pill_last_progress or -2.0)) < 0.001):
        return

    line_count = _hud_estimate_line_count(text, 42)
    text_h = max(min_text_h, 20.0 * float(line_count) + 8.0)
    if show_progress:
        bar_x = text_x
        bar_y = text_y + text_h + progress_gap
        bar_w = text_w
        bar_h = progress_bar_h
        pill_h = max(min_h, bar_y + bar_h + progress_bottom_pad)
    else:
        bar_x = text_x
        bar_y = 0.0
        bar_w = text_w
        bar_h = progress_bar_h
        pill_h = max(min_h, text_y + text_h + 14.0)

    # Text/accent changes are rare; avoid doing them for progress-only updates.
    if text != _hud_pill_last_message:
        try:
            _hud_pill_text.SetText(text)
        except Exception:
            _hud_try_call(_hud_pill_text, "SetText", text)
        _hud_set_slot(_hud_pill_text, text_x, text_y, text_w, text_h, 1)
    if str(accent or "") != _hud_pill_last_accent:
        _hud_set_color(_hud_pill_box, _hud_accent_rgba(accent))
        _hud_set_color(_hud_pill_text, (0.92, 0.98, 1.0, 1.0))

    if abs(float(_hud_pill_last_h or 0.0) - pill_h) > 0.5 or abs(float(_hud_pill_last_w or 0.0) - pill_w) > 0.5:
        _hud_set_slot(_hud_pill_root, pill_x, pill_y, pill_w, pill_h, 9999)
        _hud_set_slot(_hud_pill_box, 0, 0, pill_w, pill_h, 0)
        _hud_pill_last_w = pill_w
        _hud_pill_last_h = pill_h

    if show_progress and _hud_live(_hud_pill_progress_bg) and _hud_live(_hud_pill_progress_fill):
        _hud_try_call(_hud_pill_progress_bg, "SetRenderOpacity", 1.0)
        _hud_try_call(_hud_pill_progress_fill, "SetRenderOpacity", 1.0)
        _hud_try_call(_hud_pill_progress_bg, "SetVisibility", 3)
        _hud_try_call(_hud_pill_progress_fill, "SetVisibility", 3)
        if _hud_pill_last_progress < -0.5:
            _hud_set_color(_hud_pill_progress_bg, (0.02, 0.04, 0.05, 0.72))
            _hud_set_color(_hud_pill_progress_fill, (0.82, 0.96, 1.0, 0.96))
            _hud_set_slot(_hud_pill_progress_bg, bar_x, bar_y, bar_w, bar_h, 2)
        _hud_set_slot(_hud_pill_progress_fill, bar_x, bar_y, max(2.0, bar_w * progress_bucket), bar_h, 3)
        _hud_pill_last_progress = progress_bucket
    else:
        if _hud_pill_last_progress >= -0.5:
            if _hud_live(_hud_pill_progress_bg):
                _hud_try_call(_hud_pill_progress_bg, "SetVisibility", 1)
                _hud_try_call(_hud_pill_progress_bg, "SetRenderOpacity", 0.0)
            if _hud_live(_hud_pill_progress_fill):
                _hud_try_call(_hud_pill_progress_fill, "SetVisibility", 1)
                _hud_try_call(_hud_pill_progress_fill, "SetRenderOpacity", 0.0)
        _hud_pill_last_progress = -1.0

    _hud_try_call(_hud_pill_root, "SetRenderOpacity", 1.0)
    _hud_try_call(_hud_pill_root, "SetVisibility", 3)
    _hud_pill_last_message = text
    _hud_pill_last_accent = str(accent or "")

def _tick_hud_pill(_obj=None, _args=None, _ret=None, _func=None):
    global _hud_pill_next_update, _background_next_rarity_tick, _background_next_movement_tick
    try:
        now = time.monotonic()
    except Exception:
        now = 0.0

    # Throttle non-visual background work. The hook still fires every HUD tick,
    # but most ticks now return after pure-Python flag checks.
    try:
        # Rarity work is event/burst-only.  In steady state this is just a few
        # Python bool/float checks and never touches Unreal objects.
        if _rarity_auto_reapply and _rarity_any_custom() and now <= float(_rarity_reapply_until or 0.0):
            if now >= float(_background_next_rarity_tick or 0.0):
                _background_next_rarity_tick = now + 0.25
                fn = globals().get("_rarity_background_tick")
                if callable(fn):
                    fn()
    except Exception:
        pass
    try:
        # Infinite Jump is handled by the camera hook now.  Do not wake the
        # central HUD tick every 0.04s just because Infinite Jump is enabled.
        movement_busy = bool(_movement_pending_apply) or bool(_movement_auto_apply_on_load and not _movement_apply_on_load_done)
        if movement_busy:
            interval = 0.10
            if now >= float(_background_next_movement_tick or 0.0):
                _background_next_movement_tick = now + interval
                fn = globals().get("_movement_background_tick")
                if callable(fn):
                    fn()
    except Exception:
        pass

    try:
        # Absolute idle path: no native HUD message and no existing overlay means
        # no get_pc(), no authority check, no UMG work.
        if not _hud_pill_message:
            if _hud_pill_overlay_widget is not None or _hud_pill_host is not None:
                _hud_forget_viewport_pill_overlay()
            return None
        if now > float(_hud_pill_until):
            _hud_forget_viewport_pill_overlay()
            return None
        if not _hud_native_allowed():
            if _hud_pill_overlay_widget is not None or _hud_pill_host is not None:
                _hud_forget_viewport_pill_overlay()
            return None
        if now < float(_hud_pill_next_update or 0.0):
            return None
        _hud_pill_next_update = now + 0.15
        _hud_ensure_pill(_hud_pill_message, _hud_pill_accent)
    except Exception:
        pass
    return None


try:
    hook(
        "/Script/GbxUIUMG.GbxUIUMGTickWidget:BP_TickWidget",
        immediately_enable=True,
        hook_identifier="matts_sdk_boosting_tools_hud_pill_tick_v1",
    )(_tick_hud_pill)
except Exception as exc:
    try:
        _log(f"HUD pill tick hook failed: {exc!r}")
    except Exception:
        pass

# Mark rarity weights dirty on common travel/possession lifecycle events. These
# callbacks do not scan or write; they only arm a short retry window handled by
# the HUD tick. Missing hook paths are harmless on builds where the function does
# not exist.
def _rarity_travel_event_hook(_obj=None, _args=None, _ret=None, _func=None):
    """Apply rarity weights from reliable travel/start hooks.

    The pyexec probe showed ServerNotifyLoadedWorld, ClientSetHUD, and
    ClientRestart all fire when ENGINE.GameViewport.World.GameState.RarityState
    is already valid.  Apply immediately from that path; if the hook fires a bit
    early, arm a short retry burst.  No find_all and no stale get_pc world path.
    """
    try:
        if not _rarity_auto_reapply or not _rarity_any_custom():
            return None
    except Exception:
        return None
    try:
        if _rarity_state_for_gamestate(_obj) is not None:
            _rarity_apply_to_gamestate(_obj, log_result=False)
            return None
    except Exception:
        pass
    try:
        _world, gs = _rarity_current_world_gamestate()
        if _rarity_state_for_gamestate(gs) is not None:
            _rarity_apply_to_gamestate(gs, log_result=False)
            return None
    except Exception:
        pass
    try:
        _rarity_mark_reapply("travel/start event", 20.0)
    except Exception:
        pass
    return None

for _rarity_hook_path in (
    # Proven by pyexec probe: GameViewport.World.GameState.RarityState is valid here.
    "/Script/Engine.PlayerController:ServerNotifyLoadedWorld",
    "/Script/Engine.PlayerController:ClientSetHUD",
    "/Script/Engine.PlayerController:ClientRestart",
    "/Script/OakGame.OakPlayerController:ServerNotifyLoadedWorld",
    "/Script/OakGame.OakPlayerController:ClientSetHUD",
    "/Script/OakGame.OakPlayerController:ClientRestart",
    "/Script/GbxGame.OakPlayerController:ServerNotifyLoadedWorld",
    "/Script/GbxGame.OakPlayerController:ClientSetHUD",
    "/Script/GbxGame.OakPlayerController:ClientRestart",
    # Extra fallback hooks; these only call the same direct GameViewport path.
    "/Script/Engine.PlayerController:BeginPlayingState",
    "/Script/Engine.Controller:Possess",
    "/Script/Engine.GameStateBase:ReceiveBeginPlay",
    "/Script/Engine.GameStateBase:OnRep_ReplicatedHasBegunPlay",
    "/Script/OakGame.OakGameState:ReceiveBeginPlay",
):
    try:
        hook(_rarity_hook_path, immediately_enable=True, hook_identifier="matts_sdk_boosting_tools_rarity_world_dirty_" + str(abs(hash(_rarity_hook_path))))(_rarity_travel_event_hook)
    except Exception:
        pass

try:
    _rarity_mark_reapply("module load", 8.0)
except Exception:
    pass

def _get_blimgui_window_hub():
    hub = sys.modules.get("_matts_sdk_boosting_tools_blimgui_hub")
    if hub is not None:
        return hub

    hub = types.SimpleNamespace(callbacks={}, host_title="Matt's SDK Boosting Tools Host", host_width=980, host_height=760)

    def _draw_all() -> None:
        try:
            if _blimgui_join_safe_mode and time.monotonic() < float(_blimgui_draw_paused_until or 0.0):
                return
        except Exception:
            pass
        for title, callback in list(hub.callbacks.items()):
            try:
                callback()
            except Exception as exc:
                logging.error(f"[Matts SDK Boosting Tools | UI] draw error for {title}: {exc!r}")
        if not hub.callbacks:
            try:
                if _blimgui.is_window_open():
                    _blimgui.close_window()
            except Exception:
                pass

    def _ensure_host(width: int = 980, height: int = 760) -> None:
        hub.host_width = max(int(width or hub.host_width), int(hub.host_width))
        hub.host_height = max(int(height or hub.host_height), int(hub.host_height))
        _blimgui.set_draw_callback(_draw_all)
        if not _blimgui.is_window_open():
            _blimgui.create_window(hub.host_title, width=hub.host_width, height=hub.host_height)

    def register(title: str, callback, width: int = 980, height: int = 760) -> None:
        hub.callbacks[str(title)] = callback
        _ensure_host(width, height)

    def unregister(title: str) -> None:
        hub.callbacks.pop(str(title), None)
        if not hub.callbacks:
            try:
                if _blimgui.is_window_open():
                    _blimgui.close_window()
            except Exception:
                pass

    def is_open(title: str) -> bool:
        return str(title) in hub.callbacks

    hub.ensure_host = _ensure_host
    hub.register = register
    hub.unregister = unregister
    hub.is_open = is_open
    sys.modules["_matts_sdk_boosting_tools_blimgui_hub"] = hub
    return hub


def _positive_size_arg(value: float, fallback: float = 1.0) -> float:
    try:
        value_f = float(value)
    except Exception:
        value_f = float(fallback)
    # This imgui_bundle build asserts on explicit zero/negative sizes.
    return max(1.0, value_f)


def _cyber_button_safe(label: str, accent: str = "purple", width: float = 0.0, height: float = 0.0) -> bool:
    """Draw a cyber/raw button without ever creating a 1px-tall button.

    Width-only callers are common in this panel.  The previous safety shim turned
    height=0 into height=1, which made all tab/action buttons render as tiny
    flat lines.  Only pass an explicit height when the caller supplied one.
    """
    imgui = _blimgui.imgui
    try:
        w_req = float(width or 0.0)
        h_req = float(height or 0.0)
    except Exception:
        w_req, h_req = 0.0, 0.0
    w = _positive_size_arg(w_req, 1.0) if w_req > 0.0 else 0.0
    h = _positive_size_arg(h_req, 1.0) if h_req > 0.0 else 0.0

    if _cyber:
        cb = getattr(_cyber, "cyber_button", None)
        if callable(cb):
            if w > 0.0 and h > 0.0:
                tries = ((label, accent, w, h), (label, accent, (w, h)), (label, accent, w), (label, accent))
            elif w > 0.0:
                tries = ((label, accent, w), (label, accent), (label,))
            else:
                tries = ((label, accent), (label,))
            for args in tries:
                try:
                    return bool(cb(*args))
                except TypeError:
                    continue
                except Exception:
                    break

    btn = getattr(imgui, "button", None)
    if callable(btn):
        if w > 0.0 and h > 0.0:
            tries = ((label, (w, h)), (label, w, h), (label,))
        else:
            # Raw ImGui button does not safely support width-only on every binding;
            # use autosize instead of manufacturing a 1px height.
            tries = ((label,),)
        for args in tries:
            try:
                return bool(btn(*args))
            except TypeError:
                continue
            except Exception:
                return False
    return False

def _button(label: str, fn: Callable[[], None], accent: str = "purple", width: float = 0.0, height: float = 0.0) -> None:
    pressed = _cyber_button_safe(label, accent, width, height)
    if pressed:
        try:
            fn()
        except Exception as exc:
            _log(f"{label} failed: {exc!r}")


def _input_text(label: str, value: str, max_len: int = 4096) -> str:
    imgui = _blimgui.imgui
    try:
        changed, new_value = imgui.input_text(label, value, max_len)
        return str(new_value) if changed else value
    except TypeError:
        try:
            changed, new_value = imgui.input_text(label, value)
            return str(new_value) if changed else value
        except Exception as exc:
            _log(f"input_text unavailable for {label}: {exc!r}")
            return value


def _input_text_multiline(label: str, value: str, max_len: int = 65536, width: int = 760, height: int = 135) -> str:
    """Safe multiline text input.

    BLImGui/imgui_bundle overloads differ between builds.  Passing a max_len
    integer as the third positional argument can be misread as an ImVec2 size
    and trip IM_ASSERT(Size > 0).  Use the size tuple overload first and fall
    back to single-line input if this binding rejects it.
    """
    imgui = _blimgui.imgui
    multiline = getattr(imgui, "input_text_multiline", None)
    try:
        w = max(32.0, float(width))
        h = max(32.0, float(height))
    except Exception:
        w, h = 760.0, 135.0
    if callable(multiline):
        for args in (
            (label, value, (w, h)),
            (label, value, w, h),
            (label, value),
        ):
            try:
                out = multiline(*args)
                if isinstance(out, tuple) and len(out) >= 2:
                    changed, new_value = out[0], out[1]
                    return str(new_value) if changed else value
                return str(out) if out is not None else value
            except TypeError:
                continue
            except Exception as exc:
                _log(f"input_text_multiline unavailable for {label}: {exc!r}")
                break
    return _input_text(label, value, max_len)

def _copy_text_to_clipboard(label: str, text: str) -> None:
    imgui = _blimgui.imgui
    if not str(text or ""):
        _log(f"{label}: nothing to copy.")
        return
    for name in ("set_clipboard_text", "SetClipboardText"):
        fn = getattr(imgui, name, None)
        if callable(fn):
            try:
                fn(str(text))
                _log(f"Copied {label} to clipboard.")
                return
            except Exception as exc:
                _log(f"Copy {label} failed via {name}: {exc!r}")
    try:
        import pyperclip  # type: ignore
        pyperclip.copy(str(text))
        _log(f"Copied {label} to clipboard.")
        return
    except Exception:
        pass
    _log(f"Clipboard copy unavailable for {label}; select the output text and copy manually.")


def _serials_from_entries(entries: list[dict[str, str]]) -> list[str]:
    serials: list[str] = []
    seen: set[str] = set()
    for e in entries or []:
        serial = str(e.get("serial", "")).strip()
        if not serial or serial in seen:
            continue
        seen.add(serial)
        serials.append(serial)
    return serials


def _copy_serial_list_to_clipboard(label: str, entries: list[dict[str, str]]) -> int:
    serials = _serials_from_entries(entries)
    if not serials:
        _copy_text_to_clipboard(label, "")
        return 0
    _copy_text_to_clipboard(label, "\n".join(serials))
    return len(serials)



_GZO_PARTS_MAP: dict[str, dict[str, str]] | None = None
_GZO_TYPE_ID_INDEX: dict[int, tuple[str, dict[str, str]]] | None = None
_GZO_MAKER_PREFIXES = {
    "DAD": "Daedalus", "JAK": "Jakobs", "ORD": "Order", "TED": "Tediore",
    "TOR": "Torgue", "VLA": "Vladof", "MAL": "Maliwan", "BOR": "Ripper",
    "RIP": "Ripper", "COV": "CoV", "ATL": "Atlas", "HYP": "Hyperion",
}
_GZO_TYPE_SUFFIXES = {
    "PS": "Pistol", "SG": "Shotgun", "AR": "Assault Rifle", "SMG": "SMG", "SR": "Sniper",
    "HW": "Heavy Weapon", "HEAVY": "Heavy Weapon", "SHIELD": "Shield", "GADGET": "Gadget",
    "ENHANCEMENT": "Enhancement", "REPAIR_KIT": "Repkit", "REPKIT": "Repkit", "CLASS_MOD": "Classmod",
}
_GZO_CLASS_NAMES = {
    "siren": "Siren", "dark_siren": "Siren", "forgeknight": "Paladin", "paladin": "Paladin",
    "exo_soldier": "Exo Soldier", "gravitar": "Gravitar", "ai": "AI", "c4sh": "C4SH",
}


def _gzo_load_parts_map() -> dict[str, dict[str, str]]:
    global _GZO_PARTS_MAP, _GZO_TYPE_ID_INDEX
    if _GZO_PARTS_MAP is not None:
        return _GZO_PARTS_MAP
    data: dict[str, dict[str, str]] = {}
    try:
        blob = pkgutil.get_data(__package__ or __name__.rpartition(".")[0], "gzo_parts_map.json")
        if blob:
            raw = json.loads(blob.decode("utf-8", "replace"))
            if isinstance(raw, dict):
                for k, v in raw.items():
                    if isinstance(v, dict):
                        data[str(k)] = {str(pk): str(pv) for pk, pv in v.items()}
    except Exception as exc:
        _log(f"GZO parts map load failed: {exc!r}")
    _GZO_PARTS_MAP = data
    idx: dict[int, tuple[str, dict[str, str]]] = {}
    for key, table in data.items():
        m = re.match(r"\s*(\d+)\s*\|\s*(.+?)\s*$", str(key))
        if m:
            idx[int(m.group(1))] = (m.group(2), table)
    _GZO_TYPE_ID_INDEX = idx
    return data


def _gzo_type_id_index() -> dict[int, tuple[str, dict[str, str]]]:
    _gzo_load_parts_map()
    return _GZO_TYPE_ID_INDEX or {}


def _gzo_title_from_slug(text: str) -> str:
    text = re.sub(r"[_\-]+", " ", str(text or "")).strip()
    return " ".join(w.upper() if w.lower() in ("smg", "ai", "cov") else w.capitalize() for w in text.split())


def _gzo_type_info_from_id(type_id: int) -> dict[str, str]:
    label_table = _gzo_type_id_index().get(int(type_id))
    if not label_table:
        return {"type_id": str(type_id), "set": "", "manufacturer": "", "type": "", "character_class": ""}
    label = label_table[0]
    raw = label.strip()
    low = raw.lower()
    info = {"type_id": str(type_id), "set": raw, "manufacturer": "", "type": "", "character_class": ""}
    if "classmod" in low or "class_mod" in low:
        info["type"] = "Classmod"
        tail = low.replace("classmod", "").replace("class_mod", "").strip("_")
        info["character_class"] = _GZO_CLASS_NAMES.get(tail, _gzo_title_from_slug(tail)) if tail else ""
        return info
    pieces = re.split(r"[_\s]+", raw)
    if pieces:
        prefix = pieces[0].upper()
        if prefix in _GZO_MAKER_PREFIXES:
            info["manufacturer"] = _GZO_MAKER_PREFIXES[prefix]
        suffix = "_".join(pieces[1:]).upper() if len(pieces) > 1 else pieces[0].upper()
        if suffix in _GZO_TYPE_SUFFIXES:
            info["type"] = _GZO_TYPE_SUFFIXES[suffix]
    if not info["type"]:
        for key, val in _GZO_TYPE_SUFFIXES.items():
            if key.lower() in low:
                info["type"] = val
                break
    return info


def _serial_parts_breakdown_text(human: str) -> str:
    human = str(human or "").strip()
    if not human:
        return ""
    m = re.match(r"\s*(\d+)\s*,", human)
    if not m:
        return "Could not find a leading typeID in the deserialized serial."
    type_id = int(m.group(1))
    idx = _gzo_type_id_index()
    type_info = _gzo_type_info_from_id(type_id)
    lines = ["Item TypeID: %s" % type_id]
    if type_info.get("set"):
        lines.append("Primary Set: %s" % type_info["set"])
    if type_info.get("manufacturer") or type_info.get("type") or type_info.get("character_class"):
        meta = " | ".join(x for x in (type_info.get("manufacturer"), type_info.get("type"), type_info.get("character_class")) if x)
        lines.append("Detected: " + meta)
    lines.append("")
    refs = re.findall(r"\{\s*(\d+)(?:\s*:\s*(\d+))?\s*\}", human)
    if not refs:
        lines.append("No {part} or {partSet:part} references found.")
        return "\n".join(lines)
    lines.append("Parts Breakdown:")
    for raw_set, raw_part in refs:
        part_set = int(raw_set) if raw_part else type_id
        part_id = int(raw_part or raw_set)
        label_table = idx.get(part_set)
        set_label = label_table[0] if label_table else "UnknownSet"
        part_name = ""
        if label_table:
            part_name = label_table[1].get(str(part_id), "")
        if part_name:
            lines.append(f"  {{{raw_set + (':' + raw_part if raw_part else '')}}}  set {part_set} {set_label} / part {part_id}: {part_name}")
        else:
            lines.append(f"  {{{raw_set + (':' + raw_part if raw_part else '')}}}  set {part_set} {set_label} / part {part_id}: <unknown>")
    return "\n".join(lines)


def _serial_parts_breakdown_for_value(value: str) -> str:
    """Return the Serial Tools-style parts breakdown for a serialized or human serial."""
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        human = _serial_to_human(text) if text.startswith("@U") else text
        return _serial_parts_breakdown_text(human)
    except Exception as exc:
        return f"Parts breakdown unavailable: {exc}"


def _serial_parts_breakdown_for_value_cached(value: str) -> str:
    """Cache the expensive serial -> human -> parts breakdown work across ImGui frames."""
    global _serial_parts_cache_serial, _serial_parts_cache_text
    serial = str(value or "").strip()
    if serial == _serial_parts_cache_serial:
        return _serial_parts_cache_text
    _serial_parts_cache_serial = serial
    _serial_parts_cache_text = _serial_parts_breakdown_for_value(serial)
    return _serial_parts_cache_text

def _serial_tools_convert() -> None:
    global _serial_tools_serialized, _serial_tools_deserialized, _serial_tools_parts_breakdown, _serial_tools_status
    text = str(_serial_tools_input or "").strip()
    if not text:
        _serial_tools_serialized = ""
        _serial_tools_deserialized = ""
        _serial_tools_parts_breakdown = ""
        _serial_tools_status = "Paste a @U serial or deserialized serial text above."
        return
    try:
        if text.startswith("@U"):
            human = _serial_to_human(text)
            serial = _human_to_serial(human)
        else:
            serial = _human_to_serial(text)
            human = _serial_to_human(serial)
        _serial_tools_serialized = serial
        _serial_tools_deserialized = human
        _serial_tools_parts_breakdown = _serial_parts_breakdown_text(human)
        _serial_tools_status = "Converted successfully."
    except Exception as exc:
        _serial_tools_serialized = ""
        _serial_tools_deserialized = ""
        _serial_tools_parts_breakdown = ""
        _serial_tools_status = f"Conversion failed: {exc}"
        _log(f"Serial Tools conversion failed: {exc!r}")


def _parse_serial_text(raw: str) -> list[str]:
    """Parse menu input into serial/deserialized tokens without corrupting Base85.

    Important: BL4 Base85 serials may contain punctuation such as semicolons,
    commas, braces, equals signs, plus signs, etc. Older UI code split on
    semicolons/commas/spaces, which could truncate valid serials. Treat each
    non-empty line as one full serial/deserialized line. If a user pastes
    multiple Base85 serials on one line, split only at a new @U serial prefix.
    """
    tokens: list[str] = []
    for line in (raw or "").splitlines():
        text = line.strip()
        if not text:
            continue

        # Deserialized human serials contain spaces and pipes, so a whole line
        # must be preserved exactly.
        if "|" in text:
            tokens.append(text)
            continue

        # Base85 serials should be one-per-line. If several were pasted onto
        # one line, split at the next @U prefix, not on punctuation contained
        # inside the Base85 alphabet.
        starts = [m.start() for m in re.finditer(r"(?=@U)", text)]
        if len(starts) > 1:
            starts.append(len(text))
            for i in range(len(starts) - 1):
                part = text[starts[i]:starts[i + 1]].strip()
                if part:
                    tokens.append(part)
            continue

        tokens.append(text)
    return tokens




def _serial_with_level_override(serial: str, level: int) -> str:
    """Return a Base85 serial with its decoded item level replaced."""
    raw = str(serial or "").strip()
    if not raw:
        return raw
    level_i = _clamp_int(level, 1, 60)
    human = _serial_to_human(raw) if raw.startswith("@U") else raw
    new_human, count = re.subn(r"^(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*)\d+", rf"\g<1>{level_i}", human, count=1)
    if count <= 0:
        raise ValueError("could not find leading item level in serial")
    return _human_to_serial(new_human)


def _serials_with_level_override(serials: list[str], enabled: bool, level: int) -> tuple[list[str], int, str | None]:
    """Apply delivery level override lazily and cache by selected serial set.

    The old preview path could deserialize/reserialize hundreds of serials every
    BLImGui frame while the checkbox was enabled, which caused severe hangs.
    This only recomputes when the exact selected list or level changes.
    """
    if not enabled:
        return list(serials), 0, None
    level_i = _clamp_int(level, 1, 60)
    cleaned = tuple(str(s or "").strip() for s in serials if str(s or "").strip())
    key = (True, level_i, len(cleaned), hash(cleaned))
    cached = _serial_level_override_cache.get(key)
    if cached is not None:
        out, changed, error = cached
        return list(out), changed, error
    out: list[str] = []
    changed = 0
    for i, serial in enumerate(cleaned):
        try:
            out.append(_serial_with_level_override(serial, level_i))
            changed += 1
        except Exception as exc:
            result = (list(serials), changed, f"Level override failed on serial #{i + 1}: {exc}")
            _serial_level_override_cache[key] = result
            return list(result[0]), result[1], result[2]
    result = (out, changed, None)
    if len(_serial_level_override_cache) > 24:
        _serial_level_override_cache.clear()
    _serial_level_override_cache[key] = result
    return list(out), changed, None


def _draw_catalog_level_override(prefix: str, enabled: bool, level: int) -> tuple[bool, int]:
    imgui = _blimgui.imgui
    new_enabled = _checkbox(f"Override delivery level###msbt_{prefix}_override_level", bool(enabled))
    imgui.same_line()
    new_level = _input_int_clamped(f"Level###msbt_{prefix}_delivery_level", int(level), 1, 60)
    if new_enabled:
        _muted_wrapped(f"Deliver buttons will deserialize selected serials, set level to {new_level}, reserialize, then deliver.")
    else:
        _muted_wrapped("Deliver buttons use catalog serial levels as-is.")
    return new_enabled, new_level

def _input_int(label: str, value: int) -> int:
    imgui = _blimgui.imgui
    try:
        changed, new_value = imgui.input_int(label, int(value))
        return int(new_value) if changed else int(value)
    except Exception as exc:
        _log(f"input_int unavailable for {label}: {exc!r}")
        return int(value)



def _input_float_slider(label: str, value: float, minimum: float, maximum: float, fmt: str = "%.2f") -> float:
    """BLImGui float slider with safe fallback for older imgui bindings."""
    imgui = _blimgui.imgui
    value = float(value)
    for name in ("slider_float", "drag_float"):
        fn = getattr(imgui, name, None)
        if callable(fn):
            for args in (
                (label, value, float(minimum), float(maximum), fmt),
                (label, value, float(minimum), float(maximum)),
            ):
                try:
                    changed, new_value = fn(*args)
                    return float(new_value) if changed else value
                except TypeError:
                    continue
                except Exception as exc:
                    _log(f"{name} unavailable for {label}: {exc!r}")
                    break
    # Fallback keeps the menu usable even on BLImGui builds without sliders.
    return float(_input_int(label, int(round(value))))


def _input_int_slider(label: str, value: int, minimum: int, maximum: int) -> int:
    """Integer slider used for manual horizontal slot scrolling on small screens."""
    imgui = _blimgui.imgui
    value = _clamp_int(int(value), int(minimum), int(maximum))
    if maximum <= minimum:
        return int(minimum)
    for name in ("slider_int", "drag_int"):
        fn = getattr(imgui, name, None)
        if callable(fn):
            for args in (
                (label, value, int(minimum), int(maximum)),
                (label, value, int(minimum), int(maximum), "%d"),
            ):
                try:
                    changed, new_value = fn(*args)
                    return _clamp_int(int(new_value), int(minimum), int(maximum)) if changed else value
                except TypeError:
                    continue
                except Exception as exc:
                    _log(f"{name} unavailable for {label}: {exc!r}")
                    break
    return _input_int_clamped(label, value, minimum, maximum)

def _input_int_clamped(label: str, value: int, minimum: int, maximum: int) -> int:
    new_value = _input_int(label, value)
    clamped = _clamp_int(new_value, minimum, maximum)
    if new_value != clamped:
        _log(f"{label} capped at {clamped:,}.")
    return clamped




def _save_ui_box_sizes() -> None:
    try:
        save_extra_settings(ui_box_sizes=dict(_ui_box_sizes))
    except Exception as exc:
        _log(f"Could not save UI box sizes: {exc!r}")


def _resizable_height(key: str, label: str, default: int | float, minimum: int | float, maximum: int | float) -> float:
    """Persistent height value; the visible control is a small bottom-right corner handle."""
    k = str(key)
    current = int(_ui_box_sizes.get(k, int(round(float(default)))))
    lo = int(round(float(minimum)))
    hi = int(round(float(maximum)))
    current = _clamp_int(current, lo, hi)
    _ui_box_sizes.setdefault(k, int(current))
    return float(_ui_box_sizes.get(k, current))


def _resizable_width(key: str, label: str, default: int | float, minimum: int | float, maximum: int | float) -> float:
    """Persistent width value; the visible control is a small bottom-right corner handle."""
    k = str(key)
    current = int(_ui_box_sizes.get(k, int(round(float(default)))))
    lo = int(round(float(minimum)))
    hi = int(round(float(maximum)))
    current = _clamp_int(current, lo, hi)
    _ui_box_sizes.setdefault(k, int(current))
    return float(_ui_box_sizes.get(k, current))


def _imgui_mouse_delta() -> tuple[float, float]:
    """Best-effort mouse delta helper across imgui_bundle/BLImGui bindings."""
    imgui = _blimgui.imgui
    get_io = getattr(imgui, "get_io", None)
    if not callable(get_io):
        return (0.0, 0.0)
    try:
        io = get_io()
    except Exception:
        return (0.0, 0.0)
    delta = getattr(io, "mouse_delta", None)
    if delta is None:
        delta = getattr(io, "MouseDelta", None)
    if delta is None:
        return (0.0, 0.0)
    try:
        if isinstance(delta, (tuple, list)) and len(delta) >= 2:
            return (float(delta[0]), float(delta[1]))
        return (float(getattr(delta, "x", 0.0)), float(getattr(delta, "y", 0.0)))
    except Exception:
        return (0.0, 0.0)


def _imgui_button_raw(label: str, width: float = 0.0, height: float = 0.0) -> bool:
    """Draw a tiny raw ImGui button without cyber styling for resize grips."""
    imgui = _blimgui.imgui
    fn = getattr(imgui, "button", None)
    if not callable(fn):
        return False
    # Never pass a zero/negative size into ImGui; some BLImGui builds assert
    # instead of treating it as automatic sizing.
    try:
        w = max(1.0, float(width))
        h = max(1.0, float(height))
    except Exception:
        w, h = 18.0, 18.0
    for args in ((label, w, h), (label, (w, h)), (label,)):
        try:
            return bool(fn(*args))
        except TypeError:
            continue
        except Exception:
            return False
    return False


def _imgui_item_active() -> bool:
    imgui = _blimgui.imgui
    for name in ("is_item_active", "is_item_activated"):
        fn = getattr(imgui, name, None)
        if callable(fn):
            try:
                if bool(fn()):
                    return True
            except Exception:
                pass
    return False


def _imgui_get_cursor_pos() -> tuple[float, float]:
    imgui = _blimgui.imgui
    fn = getattr(imgui, "get_cursor_pos", None)
    if callable(fn):
        try:
            pos = fn()
            if isinstance(pos, (tuple, list)) and len(pos) >= 2:
                return (float(pos[0]), float(pos[1]))
            return (float(getattr(pos, "x", 0.0)), float(getattr(pos, "y", 0.0)))
        except Exception:
            pass
    return (0.0, 0.0)


def _imgui_set_cursor_pos_xy(x: float, y: float) -> None:
    imgui = _blimgui.imgui
    try:
        x = max(0.0, float(x))
        y = max(0.0, float(y))
    except Exception:
        x, y = 0.0, 0.0
    set_pos = getattr(imgui, "set_cursor_pos", None)
    if callable(set_pos):
        try:
            set_pos((x, y))
            return
        except TypeError:
            try:
                set_pos(x, y)
                return
            except Exception:
                pass
        except Exception:
            pass
    _imgui_set_cursor_x(x)


def _resize_corner_pair(width_key: str, height_key: str, default_w: int | float, min_w: int | float, max_w: int | float, default_h: int | float, min_h: int | float, max_h: int | float, label: str = "") -> None:
    """Disabled inner resize grip.

    The experimental per-card grips caused Size>0 asserts on this BLImGui build
    when the window was made small.  Keep saved sizes/defaults, but do not draw
    any child/button-based grip until we can use a true native child-window
    resize API safely.
    """
    return None

def _draw_resize_corner_height(key: str, label: str, default: int | float, minimum: int | float, maximum: int | float) -> None:
    # Height-only callers still get a native-style corner handle; width is the
    # current content width so dragging sideways does not damage layouts which
    # are column-controlled.
    w = max(220.0, _imgui_available_width(360.0))
    _resize_corner_pair(f"{key}_noop_w", key, w, w, w, default, minimum, maximum, label)


def _draw_resize_corner_pair(width_key: str, height_key: str, label: str, default_w: int | float, min_w: int | float, max_w: int | float, default_h: int | float, min_h: int | float, max_h: int | float) -> None:
    _resize_corner_pair(width_key, height_key, default_w, min_w, max_w, default_h, min_h, max_h, label)


_card_resize_stack: list[tuple] = []


def _begin_resizable_card(key: str, title: str, accent: str, default: int | float, minimum: int | float, maximum: int | float) -> bool:
    """Begin a resizable card without nesting it in another scrolling child.

    The previous build wrapped every cyber card in an extra BeginChild to make
    width resizing possible.  That produced double vertical scrollbars and could
    feed bad sizes into ImGui on small windows.  Cards now use the normal cyber
    card drawing path again, with a bottom-right grip for height tuning only.
    """
    h = _resizable_height(key, title, default, minimum, maximum)
    avail_w = int(max(240.0, _imgui_available_width(420.0)))
    wk = f"{key}_w"
    # Keep the width key for settings compatibility, but do not wrap the card in
    # a second child/scroll region.  The active tab viewport handles horizontal
    # scrolling for handheld screens.
    _ui_box_sizes[wk] = avail_w
    _card_resize_stack.append((str(key), str(wk), str(title), avail_w, avail_w, avail_w, int(round(float(default))), int(round(float(minimum))), int(round(float(maximum))), False))
    return _cyber.begin_card(title, accent, max(40.0, h - 4.0)) if _cyber else True


def _end_resizable_card() -> None:
    if _card_resize_stack:
        key, width_key, title, default_w, min_w, max_w, default_h, min_h, max_h, child_open = _card_resize_stack.pop()
    else:
        key = width_key = title = "card"
        default_w = min_w = max_w = max(240, int(_imgui_available_width(420.0)))
        default_h = min_h = max_h = 220
        child_open = False
    if _cyber:
        try:
            _cyber.end_card()
        except Exception as exc:
            _log(f"end_card failed: {exc!r}")
    # Draw the grip after the card body so it is visible, but do not create an
    # additional scrollable child.  Width is locked to current content width;
    # height remains user-tunable.
    _draw_resize_corner_pair(width_key, key, title, default_w, min_w, max_w, default_h, min_h, max_h)
    if child_open:
        _end_child_region()

def _reset_ui_box_sizes() -> None:
    _ui_box_sizes.clear()
    _save_ui_box_sizes()
    _log("Reset custom UI box sizes.")





def _clamped_int_input(label: str, value: int, minimum: int, maximum: int) -> int:
    """Compatibility alias used by the stripped legit builder UI."""
    return _input_int_clamped(label, value, minimum, maximum)


def _checkbox(label: str, value: bool) -> bool:
    imgui = _blimgui.imgui
    try:
        changed, new_value = imgui.checkbox(label, bool(value))
        return bool(new_value) if changed else bool(value)
    except Exception as exc:
        _log(f"checkbox unavailable for {label}: {exc!r}")
        return bool(value)

def _combo(label: str, current: int, items: list[str]) -> int:
    imgui = _blimgui.imgui
    if not items:
        return 0
    current = max(0, min(int(current), len(items) - 1))
    try:
        changed, new_idx = imgui.combo(label, current, items)
        return max(0, min(int(new_idx), len(items) - 1)) if changed else current
    except Exception:
        # Fallback for BLImGui builds without combo support: cycle with a button.
        visible = label.split("###", 1)[0].strip() or "Option"
        imgui.text_wrapped(f"{visible}: {items[current]}")
        if imgui.button(f"Next {label}"):
            return (current + 1) % len(items)
        return current


def _push_full_item_width(pad: float = 34.0, minimum: float = 120.0, maximum: float | None = 520.0) -> bool:
    """Clamp the next input/combo so it cannot run off-screen or become an unreadable mega-bar."""
    imgui = _blimgui.imgui
    push = getattr(imgui, "push_item_width", None)
    if not callable(push):
        return False
    try:
        avail = max(float(minimum), _imgui_available_width(420.0) - float(pad))
        if maximum is not None:
            avail = min(float(maximum), avail)
        push(max(float(minimum), avail))
        return True
    except Exception:
        return False


def _pop_item_width_if(pushed: bool) -> None:
    if not pushed:
        return
    pop = getattr(_blimgui.imgui, "pop_item_width", None)
    if callable(pop):
        try:
            pop()
        except Exception:
            pass


def _filter_input(label: str, widget_id: str, value: str, max_len: int = 4096, width: float = 420.0) -> str:
    """Readable filter input: label above, sane-width control below."""
    imgui = _blimgui.imgui
    imgui.text_wrapped(str(label))
    pushed = _push_full_item_width(maximum=width)
    try:
        return _input_text(f"###{widget_id}", value, max_len)
    finally:
        _pop_item_width_if(pushed)


def _filter_combo(label: str, widget_id: str, current: int, items: list[str], width: float = 240.0) -> int:
    """Readable filter combo: label above, compact control below.

    Keep these deliberately compact.  The filter row wrapper groups the label and
    combo together, so labels cannot drift to the right of the previous dropdown.
    """
    imgui = _blimgui.imgui
    imgui.text_wrapped(str(label))
    pushed = _push_full_item_width(maximum=min(float(width or 240.0), 240.0))
    try:
        return _combo(f"###{widget_id}", current, items)
    finally:
        _pop_item_width_if(pushed)


def _filter_field_row(fields: list[Callable[[], None]], field_width: float = 250.0, gap: float = 14.0) -> None:
    """Draw compact grouped filter fields, wrapping before they run off-panel."""
    imgui = _blimgui.imgui
    avail = _imgui_available_width(980.0)
    used = 0.0
    begin_group = getattr(imgui, "begin_group", None)
    end_group = getattr(imgui, "end_group", None)
    for fn in fields:
        need = float(field_width) + float(gap)
        if used > 0.0 and used + need <= avail:
            try:
                imgui.same_line()
            except Exception:
                pass
            used += need
        else:
            used = float(field_width)
        if callable(begin_group):
            try:
                begin_group()
            except Exception:
                pass
        fn()
        if callable(end_group):
            try:
                end_group()
            except Exception:
                pass



# Party/player list refresh is deliberately debounced.  Some AMD/OpenGL +
# BLImGui setups crash if we rebuild ImGui/HUD state immediately while the
# game is creating player controllers during a join.  All UI reads use this
# cache, and refreshes are performed only from the menu render tick after the
# join has settled.
_party_players_cache: list[tuple[int, str]] = []
_party_players_last_refresh: float = 0.0
_party_players_next_refresh: float = 0.0
_party_players_refresh_pending: bool = True
_party_players_last_signature: tuple | None = None
_party_players_next_signature_check: float = 0.0
_PARTY_REFRESH_IDLE_SECONDS: float = 15.0
_PARTY_REFRESH_DEBOUNCE_SECONDS: float = 0.75
_movement_live_context_cache: list[tuple[int, str, object, object | None, object | None]] = []
_movement_live_context_cache_time: float = 0.0
_movement_live_context_cache_signature: tuple | None = None


def _request_party_refresh(delay: float = _PARTY_REFRESH_DEBOUNCE_SECONDS, reason: str = "") -> None:
    global _party_players_refresh_pending, _party_players_next_refresh
    _party_players_refresh_pending = True
    try:
        when = time.monotonic() + max(0.0, float(delay))
    except Exception:
        when = time.monotonic() + _PARTY_REFRESH_DEBOUNCE_SECONDS
    if _party_players_next_refresh <= 0.0 or when < _party_players_next_refresh:
        _party_players_next_refresh = when
    if reason:
        _queue_worker_log_line(f"Party/player refresh scheduled ({reason}).")


def _party_players_signature() -> tuple:
    """Cheap party signature: GameState + PlayerArray identities and names.

    This is the auto-refresh path. It does not resolve controllers or pawns and
    does not call find_all; it only validates the PlayerArray we already get from
    the current GameState.
    """
    try:
        _world, gs = _gbc_session_world_and_gamestate()
    except Exception:
        gs = None
    gs_key = _safe_object_key(gs)
    pa = getattr(gs, "PlayerArray", None) if gs is not None else None
    pa_key = _safe_object_key(pa)
    if pa is None:
        return (gs_key, pa_key, ())
    try:
        n = len(pa)
    except Exception:
        n = 0
    items: list[tuple[int, str, str]] = []
    for i in range(int(n)):
        try:
            ps = pa[i]
        except Exception:
            ps = None
        if ps is None:
            continue
        try:
            name = _gbc_resolve_player_display_name(ps)
        except Exception:
            name = f"P{i + 1}"
        items.append((int(i), _safe_object_key(ps), str(name)))
    return (gs_key, pa_key, tuple(items))


def _party_players_from_signature(sig: tuple | None) -> list[tuple[int, str]]:
    try:
        return [(int(i), str(name)) for i, _ps_key, name in (sig[2] if sig else ())]
    except Exception:
        return []


def _party_players_for_ui(force: bool = False) -> list[tuple[int, str]]:
    """Return cached party players, refreshing only when the cheap signature changes."""
    global _party_players_cache, _party_players_last_refresh, _party_players_last_signature
    global _party_players_next_refresh, _party_players_refresh_pending, _party_players_next_signature_check
    now = time.monotonic()
    should_check = force or _party_players_refresh_pending or not _party_players_cache
    try:
        if not should_check and now >= float(_party_players_next_signature_check or 0.0):
            should_check = True
    except Exception:
        should_check = True
    if not should_check:
        return list(_party_players_cache)
    if _party_players_refresh_pending and not force:
        try:
            if _party_players_next_refresh > 0.0 and now < float(_party_players_next_refresh):
                return list(_party_players_cache)
        except Exception:
            pass
    _party_players_next_signature_check = now + _PARTY_REFRESH_IDLE_SECONDS
    try:
        sig = _party_players_signature()
        if force or _party_players_refresh_pending or sig != _party_players_last_signature:
            _party_players_cache = _party_players_from_signature(sig)
            _party_players_last_signature = sig
            # Party changed; any cached controller/pawn contexts may now be stale.
            try:
                _movement_live_context_cache.clear()
            except Exception:
                pass
        _party_players_last_refresh = now
        _party_players_next_refresh = 0.0
        _party_players_refresh_pending = False
    except Exception as exc:
        _queue_worker_log_line(f"Party/player signature refresh failed: {exc!r}")
    return list(_party_players_cache)


def _refresh_players_button(label: str = "Refresh Players", width: float = 145.0) -> None:
    _button(label, lambda: _request_party_refresh(0.0, "manual"), "cyan", width, 0)

def _selected_player_name() -> str:
    players = _party_players_for_ui()
    if not players:
        return ""
    idx = max(0, min(_selected_player_index, len(players) - 1))
    return players[idx][1]


def _selected_player_index_value() -> int | None:
    players = _party_players_for_ui()
    if not players:
        return None
    idx = max(0, min(_selected_player_index, len(players) - 1))
    return players[idx][0]


def _selected_player_controller() -> Any | None:
    pidx = _selected_player_index_value()
    if pidx is None:
        return None
    world, gs = _gbc_session_world_and_gamestate()
    if gs is None:
        return None
    pa = getattr(gs, "PlayerArray", None)
    if pa is None:
        return None
    try:
        ps = pa[int(pidx)]
    except Exception:  # noqa: BLE001
        return None
    if ps is None:
        return None
    return _gbc_find_pc_for_player_state(ps, world)


def _all_party_player_indices() -> list[int]:
    return [int(i) for i, _name in _party_players_for_ui()]


def _host_player_index_value() -> int | None:
    try:
        pc = get_pc()
    except Exception:
        pc = None
    host_ps = getattr(pc, "PlayerState", None) if pc is not None else None
    _world, gs = _gbc_session_world_and_gamestate()
    pa = getattr(gs, "PlayerArray", None) if gs is not None else None
    if pa is None:
        return 0
    try:
        n = len(pa)
    except Exception:
        return 0
    host_name = ""
    try:
        host_name = str(getattr(host_ps, "PlayerName", "") or getattr(host_ps, "SavedNetworkAddress", "") or "")
    except Exception:
        host_name = ""
    for i in range(n):
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
    return 0


def _non_host_party_player_indices() -> list[int]:
    all_indices = _all_party_player_indices()
    host_idx = _host_player_index_value()
    return [i for i in all_indices if host_idx is None or i != host_idx]


def _serial_delivery_parts_label(serials: list[str]) -> str:
    chunks = _serial_delivery_chunks(serials)
    if not chunks:
        return "Delivery split: no valid serials."
    total_raw = sum(len(str(x or "").strip()) for x in serials if str(x or "").strip())
    stats = _serial_delivery_chunk_stats(serials)
    if len(chunks) == 1:
        st = stats[0] if stats else {"serials": 0, "raw_chars": 0, "estimated_chars": 0}
        return f"Delivery split: 1 part | {st['serials']} serial(s) | {st['raw_chars']} raw chars | {st['estimated_chars']} estimated payload chars."
    preview = ", ".join(f"P{st['index']}={st['serials']} serials/{st['estimated_chars']} chars" for st in stats[:6])
    if len(stats) > 6:
        preview += ", ..."
    return f"Delivery split: {len(chunks)} parts | {len(serials)} serial(s) | {total_raw} raw chars | {preview}"


def _deliver_serials_with_target(serials: list[str], mode: str, source_label: str) -> str:
    if not serials:
        return "No valid serials to deliver."
    mode = (mode or "selected").lower().strip()
    chunks = _serial_delivery_chunks(serials)
    split_note = f" Split into {len(chunks)} package part(s)." if chunks else ""
    if mode == "all":
        _do_give_serial(serials, True)
        return f"Requested {len(serials)} serial(s) for all party players.{split_note}"
    if mode in ("nonhost", "non_host", "all_non_host"):
        indices = _non_host_party_player_indices()
        if not indices:
            return "No non-host party players found."
        _do_give_serial_to_player_indices(serials, indices, scope_label="all non-host players")
        return f"Requested {len(serials)} serial(s) for all non-host players ({len(indices)} target(s)).{split_note}"
    idx = _selected_player_index_value()
    name = _selected_player_name() or "selected player"
    if idx is None:
        return "No party player selected."
    _do_give_serial_to_player_indices(serials, [idx], scope_label=f"selected player {idx} {name}")
    return f"Requested {len(serials)} serial(s) for {name}.{split_note}"


def _deliver_serial_part_with_target(serials: list[str], part_index: int, mode: str, source_label: str) -> str:
    chunks = _serial_delivery_chunks(serials)
    if not chunks:
        return "No valid serials to deliver."
    if part_index < 0 or part_index >= len(chunks):
        return f"Invalid delivery part {part_index + 1}; this delivery has {len(chunks)} part(s)."
    chunk = chunks[part_index]
    status = _deliver_serials_with_target(chunk, mode, f"{source_label} Part {part_index + 1}/{len(chunks)}")
    return f"Part {part_index + 1}/{len(chunks)}: {status}"


def _draw_serial_delivery_split_controls(serials: list[str], source_label: str, *, max_buttons: int = 30) -> None:
    """Preview automatic delivery chunking and optional advanced timing controls."""
    global _serial_delivery_advanced_timing, _serial_delivery_pre_open_delay, _serial_delivery_post_open_delay
    imgui = _blimgui.imgui
    chunks = _serial_delivery_chunks(serials)
    if not chunks:
        _muted_wrapped("Delivery split: no valid serials selected yet.")
        return

    # Keep the core delivery engine synchronized with the UI values.
    current_pre, current_post = serial_delivery_timing()
    if abs(float(current_pre) - float(_serial_delivery_pre_open_delay)) > 0.001 or abs(float(current_post) - float(_serial_delivery_post_open_delay)) > 0.001:
        _serial_delivery_pre_open_delay, _serial_delivery_post_open_delay = set_serial_delivery_timing(
            _serial_delivery_pre_open_delay,
            _serial_delivery_post_open_delay,
        )

    _muted_wrapped(_serial_delivery_parts_label(serials))
    if len(chunks) > 1:
        approx = len(chunks) * (float(_serial_delivery_pre_open_delay) + float(_serial_delivery_post_open_delay))
        _muted_wrapped(
            f"Auto delivery: deliver -> wait {_serial_delivery_pre_open_delay:.2f}s -> open rewards -> wait {_serial_delivery_post_open_delay:.2f}s -> next part. "
            f"Estimated pacing time for {len(chunks)} part(s): ~{approx:.1f}s."
        )

    _serial_delivery_advanced_timing = _checkbox("Advanced delivery timing###msbt_serial_adv_timing", bool(_serial_delivery_advanced_timing))
    if _serial_delivery_advanced_timing:
        _muted_wrapped("Tune only if clients miss rewards. Both values are clamped from 0.00 to 5.00 seconds.")
        new_pre = _input_float_slider("Post-delivery wait before opening###msbt_serial_pre_open_delay", _serial_delivery_pre_open_delay, 0.0, 5.0, "%.2fs")
        new_post = _input_float_slider("Post-open wait before next delivery###msbt_serial_post_open_delay", _serial_delivery_post_open_delay, 0.0, 5.0, "%.2fs")
        new_pre = max(0.0, min(5.0, float(new_pre)))
        new_post = max(0.0, min(5.0, float(new_post)))
        if abs(new_pre - _serial_delivery_pre_open_delay) > 0.001 or abs(new_post - _serial_delivery_post_open_delay) > 0.001:
            _serial_delivery_pre_open_delay, _serial_delivery_post_open_delay = set_serial_delivery_timing(new_pre, new_post)
        imgui.same_line()
        if _cyber_button_safe("Reset Recommended 1.00 / 0.50###msbt_serial_reset_turbo", "cyan", 190, 0):
            _serial_delivery_pre_open_delay, _serial_delivery_post_open_delay = set_serial_delivery_timing(1.00, 0.50)
        imgui.same_line()
        if _cyber_button_safe("Safe 2.00 / 4.00###msbt_serial_safe_timing", "yellow", 175, 0):
            _serial_delivery_pre_open_delay, _serial_delivery_post_open_delay = set_serial_delivery_timing(2.00, 4.00)


def _draw_inline_target_selector(label: str = "Target Player") -> None:
    """Compact shared target selector for serial catalog pages.

    Delivery buttons use the global selected player.  Showing this selector on
    Lootlemon/GZO avoids switching back to the Boosting tab just to retarget.
    """
    global _selected_player_index
    imgui = _blimgui.imgui
    players = _party_players_for_ui()
    if not players:
        imgui.text_wrapped(f"{label}: no party players found")
        imgui.same_line(); _refresh_players_button()
        return
    labels = [f"{idx}: {name}" for idx, name in players]
    if _selected_player_index < 0 or _selected_player_index >= len(labels):
        _selected_player_index = 0
    _selected_player_index = _combo(f"{label}###inline_target_player", _selected_player_index, labels)
    imgui.same_line(); _refresh_players_button()
    selected_name = _selected_player_name() or "None"
    selected_idx = _selected_player_index_value()
    _muted_wrapped(f"Selected delivery target: {selected_idx if selected_idx is not None else '?'}: {selected_name}")

def _give_currency_selected() -> None:
    name = _selected_player_name()
    if not name:
        _log("No party player selected.")
        return
    amount = _clamp_int(_currency_amount, -_MAX_WALLET_AMOUNT, _MAX_WALLET_AMOUNT)
    if amount != _currency_amount:
        _log(f"Currency amount capped at {amount:,}.")
    _do_give_currency(_CURRENCY_KINDS[_currency_kind_index], amount, name)
    _log(f"Requested {amount} {_CURRENCY_KINDS[_currency_kind_index]} for {name}.")


def _give_experience_selected() -> None:
    name = _selected_player_name()
    if not name:
        _log("No party player selected.")
        return
    level = _clamp_int(_exp_level, 0, _max_level_for_track(_exp_track_index))
    if level != _exp_level:
        _log(f"{_EXP_TRACKS[_exp_track_index]} target level capped at {level}.")
    _do_give_experience(_EXP_TRACKS[_exp_track_index], level, name)
    _log(f"Requested {_EXP_TRACKS[_exp_track_index]} level {level} for {name}.")


def _max_player_level_selected() -> None:
    name = _selected_player_name()
    if not name:
        _log("No party player selected.")
        return
    _do_give_experience("player", 60, name)
    _log(f"Requested player level 60 for {name}.")


def _max_spec_level_selected() -> None:
    name = _selected_player_name()
    if not name:
        _log("No party player selected.")
        return
    _do_give_experience("specialization", 701, name)
    _log(f"Requested specialization level 701 for {name}.")


def _max_currency_selected() -> None:
    name = _selected_player_name()
    if not name:
        _log("No party player selected.")
        return
    _do_give_currency("cash", _MAX_WALLET_AMOUNT, name)
    _log(f"Requested max cash ({_MAX_WALLET_AMOUNT}) for {name}.")


def _max_eridium_selected() -> None:
    name = _selected_player_name()
    if not name:
        _log("No party player selected.")
        return
    _do_give_currency("eridium", _MAX_WALLET_AMOUNT, name)
    _log(f"Requested max eridium ({_MAX_WALLET_AMOUNT}) for {name}.")




def _max_all_selected() -> None:
    name = _selected_player_name()
    if not name:
        _log("No party player selected.")
        return
    _do_give_experience("player", 60, name)
    _do_give_experience("specialization", 701, name)
    _do_give_currency("cash", _MAX_WALLET_AMOUNT, name)
    _do_give_currency("eridium", _MAX_WALLET_AMOUNT, name)
    _do_msbt_maxsdu(["name", name])
    pc = _selected_player_controller()
    if pc is not None:
        from .vault_card_boost import max_all_vault_cards_for_pc

        vc_ok, vc_msg = max_all_vault_cards_for_pc(pc, log=_log)
        _log(
            f"Max All for {name}: player 60, spec 701, cash/eridium {_MAX_WALLET_AMOUNT:,}, "
            f"max SDU, vault cards 1–3 ({'OK' if vc_ok else 'partial'}: {vc_msg[:120]}).",
        )
    else:
        for vc_kind in ("vaultcard1", "vaultcard2", "vaultcard3"):
            _do_give_currency(vc_kind, _MAX_WALLET_AMOUNT, name)
        for vc_xp in ("vaultcard_xp_1", "vaultcard_xp_2", "vaultcard_xp_3"):
            _do_give_experience(vc_xp, _MAX_VAULT_CARD_LEVEL, name)
        _log(
            f"Max All for {name}: player 60, spec 701, cash/eridium {_MAX_WALLET_AMOUNT:,}, "
            "max SDU, vault cards (economy fallback — no PC for ULM path).",
        )




def _set_inventory_sizes_selected() -> None:
    idx = _selected_player_index_value()
    if idx is None:
        _log("No party player selected.")
        return
    bp = clamp_container_size(_backpack_size, _DEFAULT_BACKPACK_SIZE)
    bank = clamp_container_size(_bank_size, _DEFAULT_BANK_SIZE)
    name = set_inventory_sizes_for_party_index(idx, bp, bank)
    _log(f"Set inventory sizes for {name}: backpack {bp}, bank {bank}.")


def _set_inventory_sizes_all_party() -> None:
    bp = clamp_container_size(_backpack_size, _DEFAULT_BACKPACK_SIZE)
    bank = clamp_container_size(_bank_size, _DEFAULT_BANK_SIZE)
    count = set_inventory_sizes_for_all_party(bp, bank)
    _log(f"Set inventory sizes for {count} party player(s): backpack {bp}, bank {bank}.")

def _drop_all_shinies_selected() -> None:
    drop_all_shinies(_SHINY_DEFAULT_LEVEL)
    _log(f"Dropped all shiny itempools near the local player at level {_SHINY_DEFAULT_LEVEL}.")


def _load_shiny_serials() -> list[str]:
    # .sdkmod files are zip imports, so __file__/Path may point inside the archive
    # and cannot reliably be opened with normal filesystem IO. pkgutil.get_data
    # reads package data from both loose folders and zipped .sdkmod archives.
    blob = pkgutil.get_data(__package__ or __name__.rpartition(".")[0], "shiny_serials.json")
    if blob is None:
        raise RuntimeError("Could not load shiny_serials.json from the mod package data.")
    data = json.loads(blob.decode("utf-8"))
    serials: list[str] = []
    if not isinstance(data, list):
        raise RuntimeError("shiny_serials.json must contain a JSON list.")
    for index, entry in enumerate(data, start=1):
        if not isinstance(entry, dict):
            continue
        serial = str(entry.get("serial", "")).strip()
        if serial:
            serials.append(serial)
    if not serials:
        raise RuntimeError("No serial values found in shiny_serials.json.")
    return serials


def _deliver_all_shiny_serials_selected() -> None:
    # Use the same working model as serial_rewards.Give_Serial ... all:
    # grant the loyalty reward to all players, then patch the newest package on
    # every GbxRewardsManager. Do not target a single PlayerArray index here;
    # that made player 1 get the reward consistently while remote players were
    # dependent on whether their selected-index manager/package was resolved in time.
    serials = _load_shiny_serials()
    _do_give_serial(serials, True)
    _log(f"Requested shiny reward package with {len(serials)} serial(s) for all party players.")


def _activate_devperk_selected(perk_index: int) -> None:
    idx = _selected_player_index_value()
    name = _selected_player_name() or "selected player"
    perk = int(perk_index)
    label = activate_devperk(perk, idx)
    if perk in (5, 6):
        # Infinite Ammo and Demigod are toggle-only dev perks.  Use the same
        # cached ON/OFF state shown on the button so the status/log says the
        # actual requested state instead of always saying Activated.
        enabled = bool(devperk_toggle_state(perk, idx))
        verb = "Activated" if enabled else "Deactivated"
        accent = "cyan" if enabled else "gold"
        _set_status_pill(f"{verb} {label} for {name}.", accent)
        _log(f"{verb} {label} for {name}.")
        return
    if perk == 4:
        _set_status_pill("Granted ALL Customizations and Hover Drives.", "pink")
    _log(f"Activated {label} for {name}.")


def _toggle_debug_cam_selected() -> None:
    idx = _selected_player_index_value()
    name = _selected_player_name() or "selected player"
    message = toggle_debug_cam(idx)
    _log(f"{message} Target: {name}.")


def _apply_debug_cam_speed(log_result: bool = True) -> None:
    global _debug_cam_speed, _debug_cam_speed_pending, _debug_cam_speed_due
    idx = _selected_player_index_value()
    name = _selected_player_name() or "selected player"
    _debug_cam_speed = clamp_debug_speed(_debug_cam_speed)
    _debug_cam_speed_pending = False
    _debug_cam_speed_due = 0.0
    message = set_debug_cam_speed(_debug_cam_speed, idx)
    if log_result:
        _log(f"{message} Target: {name}.")


def _schedule_debug_cam_speed_apply() -> None:
    """Debounce debug cam speed writes so the menu does not hammer client debug cam."""
    global _debug_cam_speed_pending, _debug_cam_speed_due
    _debug_cam_speed_pending = True
    _debug_cam_speed_due = time.monotonic() + float(_debug_cam_speed_apply_delay)


def _apply_debug_cam_speed_if_due() -> None:
    if not _debug_cam_speed_pending:
        return
    try:
        if time.monotonic() < float(_debug_cam_speed_due or 0.0):
            return
    except Exception:
        pass
    _apply_debug_cam_speed(False)


def _set_debug_cam_speed_preset(value: float) -> None:
    """Set a debug cam speed preset, update the slider value, and apply immediately."""
    global _debug_cam_speed
    _debug_cam_speed = clamp_debug_speed(value)
    _apply_debug_cam_speed(True)


def _teleport_pawn_to_debug_cam_selected() -> None:
    idx = _selected_player_index_value()
    name = _selected_player_name() or "selected player"
    message = teleport_pawn_to_debug_cam(idx)
    _log(f"{message} Target: {name}.")




def _movement_clamp(value: float, minimum: float, maximum: float) -> float:
    try:
        return max(float(minimum), min(float(maximum), float(value)))
    except Exception:
        return float(minimum)


def _movement_pc_for_player_index(player_index: int | None):
    if not _movement_is_listen_host():
        return None, "Client mode — teleport/movement player targeting is host-only."
    world, gs = _gbc_session_world_and_gamestate()
    if gs is None:
        return None, "No active GameState."
    pa = getattr(gs, "PlayerArray", None)
    if pa is None:
        return None, "GameState.PlayerArray missing."
    try:
        ps = pa[int(player_index)]
    except Exception:
        return None, f"Invalid party player index {player_index}."
    pc = _gbc_find_pc_for_player_state(ps, world)
    if pc is None:
        return None, f"Could not resolve PlayerController for {_gbc_resolve_player_display_name(ps)}."
    return pc, _gbc_resolve_player_display_name(ps)


def _movement_live_party_contexts(selected_only: bool = False) -> list[tuple[int, str, object, object | None, object | None]]:
    out: list[tuple[int, str, object, object | None, object | None]] = []
    if not _movement_is_listen_host():
        # Joined clients should not walk GameState.PlayerArray / NetDriver / remote
        # controllers for movement tools. That path is host-only and can be unsafe
        # during non-host join. Return a local-only snapshot for UI labels.
        try:
            pc = get_pc()
        except Exception:
            pc = None
        if pc is None:
            return out
        try:
            ps = getattr(pc, "PlayerState", None)
            name = _gbc_resolve_player_display_name(ps) if ps is not None else "Local Player"
        except Exception:
            name = "Local Player"
        pawn = None
        for attr in ("Pawn", "AcknowledgedPawn", "Character"):
            try:
                pawn = getattr(pc, attr, None)
                if pawn is not None:
                    break
            except Exception:
                pass
        move = None
        try:
            if pawn is not None:
                for attr in ("CharacterMovement", "MovementComponent", "PawnMovement", "Movement", "OakCharacterMovement"):
                    move = getattr(pawn, attr, None)
                    if move is not None:
                        break
        except Exception:
            move = None
        return [(0, str(name), pc, pawn, move)]
    world, gs = _gbc_session_world_and_gamestate()
    if gs is None:
        return out
    pa = getattr(gs, "PlayerArray", None)
    if pa is None:
        return out
    wanted = _selected_player_index_value() if selected_only else None
    try:
        total = len(pa)
    except Exception:
        total = 0
    for i in range(total):
        if wanted is not None and int(i) != int(wanted):
            continue
        try:
            ps = pa[i]
        except Exception:
            ps = None
        if ps is None:
            continue
        pc = _gbc_find_pc_for_player_state(ps, world)
        if pc is None:
            continue
        name = _gbc_resolve_player_display_name(ps)
        pawn = None
        for attr in ("Pawn", "AcknowledgedPawn", "Character"):
            try:
                pawn = getattr(pc, attr, None)
                if pawn is not None:
                    break
            except Exception:
                pass
        if pawn is None:
            gp = getattr(pc, "GetPawn", None)
            if callable(gp):
                try:
                    pawn = gp()
                except Exception:
                    pawn = None
        move = None
        if pawn is not None:
            for attr in ("CharacterMovement", "MovementComponent", "PawnMovement", "Movement", "OakCharacterMovement"):
                try:
                    move = getattr(pawn, attr, None)
                    if move is not None:
                        break
                except Exception:
                    pass
            if move is None:
                for meth in ("GetMovementComponent", "GetCharacterMovement"):
                    fn = getattr(pawn, meth, None)
                    if callable(fn):
                        try:
                            move = fn()
                            if move is not None:
                                break
                        except Exception:
                            pass
        out.append((i, name, pc, pawn, move))
    return out


def _movement_cached_contexts_still_valid(sig: tuple | None) -> bool:
    """Validate cached controller/pawn refs without resolving anything new."""
    try:
        if not _movement_live_context_cache or sig != _movement_live_context_cache_signature:
            return False
        for _idx, _name, pc, pawn, _move in _movement_live_context_cache:
            cur_pawn = None
            for attr in ("Pawn", "AcknowledgedPawn", "Character"):
                try:
                    cur_pawn = getattr(pc, attr, None)
                    if cur_pawn is not None:
                        break
                except Exception:
                    pass
            if cur_pawn is not None and pawn is not None and cur_pawn is not pawn and str(cur_pawn) != str(pawn):
                return False
        return True
    except Exception:
        return False


def _movement_live_party_contexts_cached(max_age: float = 1.0) -> list[tuple[int, str, object, object | None, object | None]]:
    """Cached party contexts. Resolve controllers/pawns only when the cheap party
    signature changes or cached pawn references are invalid.
    """
    global _movement_live_context_cache, _movement_live_context_cache_time, _movement_live_context_cache_signature
    try:
        now = time.monotonic()
    except Exception:
        now = 0.0
    try:
        if _party_players_last_signature is not None and now < float(_party_players_next_signature_check or 0.0):
            sig = _party_players_last_signature
        else:
            sig = _party_players_signature()
    except Exception:
        sig = None
    try:
        if _movement_cached_contexts_still_valid(sig):
            return list(_movement_live_context_cache)
    except Exception:
        pass
    contexts = _movement_live_party_contexts(False)
    _movement_live_context_cache = list(contexts)
    _movement_live_context_cache_time = time.monotonic()
    _movement_live_context_cache_signature = sig
    return contexts

def _movement_try_set(obj, attr: str, value: float) -> bool:
    if obj is None:
        return False
    try:
        if hasattr(obj, attr):
            setattr(obj, attr, float(value))
            return True
    except Exception:
        return False
    return False


def _movement_try_call(obj, names: tuple[str, ...], value: float) -> bool:
    if obj is None:
        return False
    for name in names:
        fn = getattr(obj, name, None)
        if callable(fn):
            try:
                fn(float(value))
                return True
            except Exception:
                pass
    return False


def _movement_apply_to_context(ctx: tuple[int, str, object, object | None, object | None], speed: float, jump_goal: float) -> tuple[bool, str]:
    _idx, name, _pc, pawn, move = ctx
    changed: list[str] = []
    # Movement speed: use both scale-like and absolute-like fields because BL4
    # builds differ across pawns/controllers.  Missing fields are ignored.
    if _movement_try_call(move, ("SetMovementSpeedScale", "SetPawnMovementSpeedScale", "SetSpeedScale"), speed):
        changed.append("speed-call")
    for attr in ("MovementSpeedScale", "PawnMovementSpeedScale", "SpeedScale", "CustomTimeDilation"):
        if _movement_try_set(move, attr, speed) or _movement_try_set(pawn, attr, speed):
            changed.append(attr)
    # Common character movement absolute speed fields.  Interpret the UI value as
    # a multiplier over the usual 600 baseline so 1.25 == 750 max walk speed.
    abs_speed = 600.0 * float(speed)
    for attr in ("MaxWalkSpeed", "MaxFlySpeed", "MaxAcceleration", "GroundSpeed", "RunSpeed", "SprintSpeed", "MoveSpeed"):
        if _movement_try_set(move, attr, abs_speed) or _movement_try_set(pawn, attr, abs_speed):
            changed.append(attr)
    # JumpGoal is the requested BL4-specific field.  Also write JumpZVelocity as
    # a fallback for movement components which expose UE-style jump height.
    if _movement_try_call(pawn, ("SetJumpGoal",), jump_goal) or _movement_try_call(move, ("SetJumpGoal", "SetJumpZVelocity"), jump_goal):
        changed.append("jump-call")
    for attr in ("JumpGoal", "JumpZVelocity", "JumpVelocity", "JumpHeight"):
        if _movement_try_set(pawn, attr, jump_goal) or _movement_try_set(move, attr, jump_goal):
            changed.append(attr)
    return (bool(changed), f"{name}: {', '.join(dict.fromkeys(changed)) if changed else 'no writable movement fields found'}")


def _apply_player_movement(selected_only: bool = False) -> None:
    global _movement_speed_value, _movement_jump_goal_value, _movement_status
    speed = _movement_clamp(_movement_speed_value, 0.05, 10.0)
    jump = _movement_clamp(_movement_jump_goal_value, 0.0, 5000.0)
    _movement_speed_value = speed
    _movement_jump_goal_value = jump
    contexts = _movement_live_party_contexts(selected_only)
    if not contexts:
        _movement_status = "No live party pawns found."
        _log(_movement_status)
        _set_status_pill(_movement_status, "red")
        return
    ok = 0
    details: list[str] = []
    for ctx in contexts:
        changed, detail = _movement_apply_to_context(ctx, speed, jump)
        if changed:
            ok += 1
        details.append(detail)
    scope = "selected player" if selected_only else "all party players"
    _movement_status = f"Applied movement to {ok}/{len(contexts)} {scope}: speed {speed:.2f}x, JumpGoal {jump:.0f}."
    _log(_movement_status)
    for detail in details[:8]:
        _log("Movement: " + detail)
    _set_status_pill(_movement_status, "cyan")


def _reset_player_movement(selected_only: bool = False) -> None:
    global _movement_speed_value, _movement_jump_goal_value
    _movement_speed_value = 1.0
    _movement_jump_goal_value = 600.0
    _apply_player_movement(selected_only)


def _draw_player_movement_tab() -> None:
    # Back-compat shim: the original simple movement tab only exposed two
    # sliders and is easy to route to by accident.  Always draw the full
    # movement utility tab instead.
    _draw_movement_tab()


def _max_sdu_selected() -> None:
    name = _selected_player_name()
    if not name:
        _log("No party player selected.")
        return
    _do_msbt_maxsdu(["name", name])
    _log(f"Requested max SDU for {name}.")


def _give_serial_selected(mode: str = "selected") -> None:
    raw = (_serial_text or "").strip()
    if not raw:
        _log("Paste at least one Base85 serial first.")
        return
    expanded = _parse_serial_text(raw)
    serials = _resolve_give_serial_strings(expanded)
    if not serials:
        _log("No valid serials after parsing/resolving.")
        return
    serials, changed, error = _serials_with_level_override(serials, _serial_delivery_override_level, _serial_delivery_level)
    if error:
        _log(error)
        return
    status = _deliver_serials_with_target(serials, mode, "Boosting Menu")
    if changed:
        status += f" Level override: {changed} serial(s) set to level {_clamp_int(_serial_delivery_level, 1, 60)}."
    _log(status)



def _kick_selected_player() -> None:
    idx = _selected_player_index_value()
    name = _selected_player_name()
    if idx is None or not name:
        _log("No party player selected.")
        return
    _kick_party_player_by_index(idx, "Kicked by host")

def _small_same_line_button(label: str, fn: Callable[[], None], accent: str = "purple") -> None:
    imgui = _blimgui.imgui
    imgui.same_line()
    _button(label, fn, accent)


def _draw_target_bar(players: list[tuple[int, str]], labels: list[str]) -> None:
    global _selected_player_index
    imgui = _blimgui.imgui
    if _cyber:
        _cyber.section_header("Target Player", "cyan")
    else:
        imgui.separator(); imgui.text("TARGET PLAYER")
    pushed = _push_full_item_width(maximum=520.0)
    try:
        _selected_player_index = _combo("Party Player", _selected_player_index, labels)
    finally:
        _pop_item_width_if(pushed)
    _wrapped_button_row([
        ("Refresh Players", lambda: _request_party_refresh(0.0, "manual"), "cyan", 145, 0),
        ("Kick Player", _kick_selected_player, "red", 110, 0),
    ], max_width=max(220.0, _imgui_available_width(520.0) - 8.0))
    selected = _selected_player_name() or "None"
    if _cyber:
        _muted_wrapped(f"Selected target: {selected}")
    else:
        imgui.text_wrapped(f"Selected target: {selected}")


def _draw_quick_max() -> None:
    imgui = _blimgui.imgui
    if _cyber:
        _cyber.section_header("Quick Max", "gold")
        _wrapped_button_row([
            ("MAX ALL", _max_all_selected, "gold", 74, 0),
            ("MAX CASH", _max_currency_selected, "green", 88, 0),
            ("MAX ERIDIUM", _max_eridium_selected, "purple", 110, 0),
            ("MAX PLAYER 60", _max_player_level_selected, "cyan", 130, 0),
            ("MAX SPEC 701", _max_spec_level_selected, "purple", 120, 0),
        ])
        _muted_wrapped("Caps: cash/eridium 2,147,483,647 | player 60 | spec 701")
    else:
        imgui.separator(); imgui.text("QUICK MAX")
        _button("Max All", _max_all_selected); imgui.same_line(); _button("Max Currency", _max_currency_selected); imgui.same_line(); _button("Max Eridium", _max_eridium_selected)


def _draw_serial_card() -> None:
    global _serial_text, _serial_delivery_override_level, _serial_delivery_level
    imgui = _blimgui.imgui
    opened = _begin_resizable_card("card_serial_rewards", "Serial Rewards", "purple", 430, 340, 900) if _cyber else True
    if opened:
        imgui.text_wrapped("Paste one or more serials below. Rewards are created with GiveRewardAllPlayers, then custom serials are patched onto the selected target packages.")
        _serial_delivery_override_level, _serial_delivery_level = _draw_catalog_level_override("boosting_serials", _serial_delivery_override_level, _serial_delivery_level)
        _serial_text = _input_text_multiline("Serial Input###msbt_serials", _serial_text, 65536, width=int(_fit_width(520, 24, 220)), height=250)
        def _clear_serials_action() -> None:
            global _serial_text
            _serial_text = ""
            _log("Cleared serial input.")
        _card_button_row([
            ("Give Selected", lambda: _give_serial_selected("selected"), "purple", 118, 0),
            ("Give All", lambda: _give_serial_selected("all"), "gold", 82, 0),
            ("Give Non-Host", lambda: _give_serial_selected("nonhost"), "cyan", 122, 0),
            ("Clear Serials", _clear_serials_action, "pink", 110, 0),
        ])
        preview_serials = _parse_serial_text((_serial_text or "").strip()) if (_serial_text or "").strip() else []
        _draw_serial_delivery_split_controls(preview_serials, "Boosting Menu")
    if _cyber:
        _end_resizable_card()


def _draw_currency_card() -> None:
    global _currency_kind_index, _currency_amount
    imgui = _blimgui.imgui
    opened = _begin_resizable_card("card_currency", "Currency", "green", 155, 135, 320) if _cyber else True
    if opened:
        pushed = _push_full_item_width(maximum=300.0)
        try:
            _currency_kind_index = _combo("Currency Kind", _currency_kind_index, _CURRENCY_KINDS)
        finally:
            _pop_item_width_if(pushed)
        _currency_amount = _input_int_clamped("Currency Amount", _currency_amount, -_MAX_WALLET_AMOUNT, _MAX_WALLET_AMOUNT)
        _card_button_row([
            ("Give Currency", _give_currency_selected, "green", 118, 0),
            ("Max Currency", _max_currency_selected, "green", 118, 0),
            ("Max Eridium", _max_eridium_selected, "purple", 112, 0),
            ("Max All", _max_all_selected, "gold", 88, 0),
        ])
        if _cyber:
            imgui.spacing()
            _cyber.metric("Max Cash", f"{_MAX_WALLET_AMOUNT:,}", "green")
            _cyber.metric("Max Eridium", f"{_MAX_WALLET_AMOUNT:,}", "purple")
        else:
            imgui.text_wrapped(f"Cash/Eridium cap: {_MAX_WALLET_AMOUNT:,}")
    if _cyber:
        _end_resizable_card()


def _draw_experience_card() -> None:
    global _exp_track_index, _exp_level
    imgui = _blimgui.imgui
    opened = _begin_resizable_card("card_experience", "Experience", "cyan", 150, 130, 280) if _cyber else True
    if opened:
        previous_exp_track_index = _exp_track_index
        pushed = _push_full_item_width(maximum=300.0)
        try:
            _exp_track_index = _combo("XP Track", _exp_track_index, _EXP_TRACKS)
        finally:
            _pop_item_width_if(pushed)
        if _exp_track_index != previous_exp_track_index:
            _exp_level = _default_level_for_track(_exp_track_index)
        max_track_level = _max_level_for_track(_exp_track_index)
        _exp_level = _input_int_clamped("Target Level", _exp_level, 0, max_track_level)
        _card_button_row([
            ("Set Player Level", _give_experience_selected, "cyan", 132, 0),
            ("Max Player Level", _max_player_level_selected, "cyan", 142, 0),
            ("Set Spec 701", _max_spec_level_selected, "purple", 112, 0),
        ])
        if _cyber:
            _muted_wrapped(f"Allowed target range for {_EXP_TRACKS[_exp_track_index]}: 0 to {max_track_level:,}. Defaults: player 60, spec 701.")
        else:
            imgui.text_wrapped(f"Allowed target range for {_EXP_TRACKS[_exp_track_index]}: 0 to {max_track_level:,}.")
    if _cyber:
        _end_resizable_card()




def _draw_inventory_size_card() -> None:
    global _backpack_size, _bank_size, _auto_inventory_sizes, _auto_inventory_last_log
    imgui = _blimgui.imgui
    opened = _begin_resizable_card("card_inventory_size", "Backpack / Bank Size", "cyan", 165, 140, 340) if _cyber else True
    if opened:
        old_bp, old_bank, old_auto = _backpack_size, _bank_size, _auto_inventory_sizes
        _backpack_size = clamp_container_size(_input_int("Backpack Size", _backpack_size), _DEFAULT_BACKPACK_SIZE)
        _bank_size = clamp_container_size(_input_int("Bank Size", _bank_size), _DEFAULT_BANK_SIZE)
        _auto_inventory_sizes = _checkbox("Automatic Backpack and Bank Size for Party", _auto_inventory_sizes)
        if (old_bp, old_bank, old_auto) != (_backpack_size, _bank_size, _auto_inventory_sizes):
            save_inventory_settings(
                auto_inventory_sizes=_auto_inventory_sizes,
                backpack_size=_backpack_size,
                bank_size=_bank_size,
            )
            _log(f"Saved inventory auto settings: auto={_auto_inventory_sizes}, backpack {_backpack_size}, bank {_bank_size}.")
        # Never use a Python background thread for this. Unreal object access from
        # a daemon thread can survive into shutdown/map teardown and crash on exit.
        # Keep automatic mode main-thread only and throttle it so it does not spam.
        now = time.monotonic()
        if _auto_inventory_sizes:
            if now - float(_auto_inventory_last_log or 0.0) > 1.0:
                _auto_inventory_last_log = now
                try:
                    count = auto_apply_inventory_sizes_if_needed(True, _backpack_size, _bank_size, source="ui-main-thread")
                    if count:
                        _log(f"Auto-applied inventory sizes to {count} party player(s): backpack {_backpack_size}, bank {_bank_size}.")
                except Exception as exc:
                    _log(f"Automatic inventory apply failed: {exc!r}")
        else:
            auto_apply_inventory_sizes_if_needed(False, _backpack_size, _bank_size, source="ui-reset")
        _card_button_row([
            ("Set Backpack + Bank for Selected", _set_inventory_sizes_selected, "cyan", 250, 0),
            ("Apply to All Party", _set_inventory_sizes_all_party, "purple", 150, 0),
        ])
        if _cyber:
            _muted_wrapped("Writes PlayerState BackpackContainer.MaxSize and BankContainer.MaxSize Value/BaseValue.")
        else:
            imgui.text_wrapped("Writes PlayerState BackpackContainer.MaxSize and BankContainer.MaxSize Value/BaseValue.")
    if _cyber:
        _end_resizable_card()

def _draw_sdu_card() -> None:
    imgui = _blimgui.imgui
    opened = _begin_resizable_card("card_sdu", "SDU / Golden Chest / Shinies", "gold", 150, 125, 320) if _cyber else True
    if opened:
        _card_button_row([
            ("Max SDU for Selected", _max_sdu_selected, "cyan", 190, 0),
            ("Open Golden Chest", _open_golden_chest, "gold", 175, 0),
            ("Close Golden Chest", _close_golden_chest, "red", 180, 0),
            ("Drop All Shinies", _drop_all_shinies_selected, "gold", 160, 0),
            ("Shiny Selected", lambda: _deliver_all_shiny_serials_selected("selected"), "purple", 145, 0),
            ("Shiny All", lambda: _deliver_all_shiny_serials_selected("all"), "gold", 110, 0),
            ("Shiny Non-Host", lambda: _deliver_all_shiny_serials_selected("nonhost"), "cyan", 150, 0),
        ])
    if _cyber:
        _end_resizable_card()





def _movement_preset_dict() -> dict[str, object]:
    """Current movement UI values suitable for explicit preset saving."""
    return {
        "speed_scale": float(_movement_speed_scale),
        "walk_speed": float(_movement_walk_speed),
        "jump_goal": float(_movement_jump_goal),
        "jump_velocity": float(_movement_jump_velocity),
        "sprint_jump_goal": float(_movement_sprint_jump_goal),
        "double_jump_goal": float(_movement_double_jump_goal),
        "slide_jump_goal": float(_movement_slide_jump_goal),
        "individual_jump_goals": bool(_movement_individual_jump_goals),
        "jump_hold_time": 0.0,
        "gravity_scale": float(_movement_gravity_scale),
        "max_step_height": float(_movement_max_step_height),
        "jump_count": 2,
        "jump_off_z_factor": 0.5,
        "walkable_floor_angle": float(_movement_walkable_floor_angle),
        "walkable_floor_z": float(_movement_walkable_floor_z),
        "glide_speed": float(_movement_glide_speed),
        "glide_boost": float(_movement_glide_boost),
        "glide_air_control": float(_movement_glide_air_control),
        "dash_speed": float(_movement_dash_speed),
        "zero_vault_costs": bool(_movement_zero_vault_costs),
    }


def _movement_save_settings() -> None:
    """Persist only user intent, not live slider drift.

    Movement values should start from defaults every game load unless the user
    explicitly saved a preset and checked Auto Apply on Game Load.
    """
    try:
        save_extra_settings(
            movement_auto_apply_on_load=bool(_movement_auto_apply_on_load),
            movement_saved_preset=dict(_movement_saved_preset),
            movement_noclip=bool(_movement_noclip),
        )
    except Exception as exc:
        _log(f"Movement settings save failed: {exc!r}")


def _movement_save_current_preset() -> None:
    global _movement_saved_preset, _movement_status
    _movement_saved_preset = _movement_preset_dict()
    _movement_save_settings()
    _movement_status = "Saved current movement values as the movement preset."
    _log(_movement_status)
    _set_status_pill(_movement_status, "green")


def _movement_load_saved_preset(apply_now: bool = True) -> None:
    global _movement_speed_scale, _movement_walk_speed, _movement_jump_goal, _movement_jump_velocity, _movement_sprint_jump_goal, _movement_double_jump_goal, _movement_slide_jump_goal, _movement_individual_jump_goals
    global _movement_gravity_scale, _movement_max_step_height, _movement_walkable_floor_angle, _movement_walkable_floor_z
    global _movement_glide_speed, _movement_glide_boost, _movement_glide_air_control, _movement_dash_speed, _movement_zero_vault_costs, _movement_status
    if not _movement_saved_preset:
        _movement_status = "No movement preset saved yet."
        _log(_movement_status)
        _set_status_pill(_movement_status, "gold")
        return
    p = dict(_MOVEMENT_DEFAULT_PRESET)
    p.update(dict(_movement_saved_preset))
    _movement_speed_scale = float(p.get("speed_scale", _MOVEMENT_DEFAULT_PRESET["speed_scale"]) or _MOVEMENT_DEFAULT_PRESET["speed_scale"])
    _movement_walk_speed = float(p.get("walk_speed", _MOVEMENT_DEFAULT_PRESET["walk_speed"]) or _MOVEMENT_DEFAULT_PRESET["walk_speed"])
    _movement_jump_goal = float(p.get("jump_goal", _MOVEMENT_DEFAULT_PRESET["jump_goal"]) or _MOVEMENT_DEFAULT_PRESET["jump_goal"])
    _movement_jump_velocity = float(p.get("jump_velocity", _MOVEMENT_DEFAULT_PRESET["jump_velocity"]) or _MOVEMENT_DEFAULT_PRESET["jump_velocity"])
    _movement_sprint_jump_goal = float(p.get("sprint_jump_goal", _movement_jump_goal) or _movement_jump_goal)
    _movement_double_jump_goal = float(p.get("double_jump_goal", _MOVEMENT_DEFAULT_PRESET["double_jump_goal"]) or _MOVEMENT_DEFAULT_PRESET["double_jump_goal"])
    _movement_slide_jump_goal = float(p.get("slide_jump_goal", _movement_sprint_jump_goal) or _movement_sprint_jump_goal)
    _movement_individual_jump_goals = bool(p.get("individual_jump_goals", False))
    _movement_gravity_scale = float(p.get("gravity_scale", _MOVEMENT_DEFAULT_PRESET["gravity_scale"]) or _MOVEMENT_DEFAULT_PRESET["gravity_scale"])
    _movement_max_step_height = float(p.get("max_step_height", _MOVEMENT_DEFAULT_PRESET["max_step_height"]) or _MOVEMENT_DEFAULT_PRESET["max_step_height"])
    _movement_walkable_floor_angle = float(p.get("walkable_floor_angle", _MOVEMENT_DEFAULT_PRESET["walkable_floor_angle"]) or _MOVEMENT_DEFAULT_PRESET["walkable_floor_angle"])
    _movement_walkable_floor_z = float(p.get("walkable_floor_z", _MOVEMENT_DEFAULT_PRESET["walkable_floor_z"]) or _MOVEMENT_DEFAULT_PRESET["walkable_floor_z"])
    _movement_glide_speed = float(p.get("glide_speed", _MOVEMENT_DEFAULT_PRESET["glide_speed"]) or _MOVEMENT_DEFAULT_PRESET["glide_speed"])
    _movement_glide_boost = float(p.get("glide_boost", _MOVEMENT_DEFAULT_PRESET["glide_boost"]) or _MOVEMENT_DEFAULT_PRESET["glide_boost"])
    _movement_glide_air_control = float(p.get("glide_air_control", _MOVEMENT_DEFAULT_PRESET["glide_air_control"]) or _MOVEMENT_DEFAULT_PRESET["glide_air_control"])
    _movement_dash_speed = float(p.get("dash_speed", _MOVEMENT_DEFAULT_PRESET["dash_speed"]) or _MOVEMENT_DEFAULT_PRESET["dash_speed"])
    _movement_zero_vault_costs = bool(p.get("zero_vault_costs", True))
    if apply_now:
        _apply_movement_adjustments_all()
    else:
        _movement_status = "Loaded saved movement preset into the UI."
        _log(_movement_status)



def _movement_schedule_debounced_apply(reason: str = "slider", sections: set[str] | None = None) -> None:
    """Arm a delayed movement apply after slider edits settle.

    The UI value changes immediately, but reflected game writes are delayed until
    the slider stops moving.  Keep a union of dirty sections so a speed slider
    does not re-apply jump/glide/etc.
    """
    global _movement_pending_apply_due, _movement_pending_apply, _movement_pending_apply_reason, _movement_pending_sections, _movement_status
    try:
        _movement_pending_apply_due = time.monotonic() + float(_movement_debounce_apply_delay)
    except Exception:
        _movement_pending_apply_due = 0.0
    _movement_pending_apply = True
    _movement_pending_apply_reason = str(reason or "slider")
    try:
        if sections is None:
            _movement_pending_sections = set()
        else:
            cur = set(_movement_pending_sections or set())
            cur.update(set(sections))
            _movement_pending_sections = cur
    except Exception:
        _movement_pending_sections = set(sections or set())
    # Keep this lightweight and do not log every drag frame.
    _movement_status = f"Movement changes pending… applying after slider stops ({_movement_debounce_apply_delay:.2f}s)."


def _movement_apply_pending_if_due(now: float | None = None) -> None:
    """Apply debounced movement changes once the user stops dragging sliders."""
    global _movement_pending_apply_due, _movement_pending_apply, _movement_pending_apply_reason, _movement_pending_sections
    if not _movement_pending_apply:
        return
    try:
        t = time.monotonic() if now is None else float(now)
    except Exception:
        t = time.monotonic()
    if t < float(_movement_pending_apply_due or 0.0):
        return
    _movement_pending_apply = False
    _movement_pending_apply_due = 0.0
    reason = _movement_pending_apply_reason or "slider"
    _movement_pending_apply_reason = ""
    sections = set(_movement_pending_sections or set())
    try:
        _movement_pending_sections.clear()
    except Exception:
        pass
    try:
        _log(f"Movement debounced apply fired after {reason} changes: {sorted(sections) if sections else 'all'}.")
    except Exception:
        pass
    _apply_movement_adjustments_sections(sections or None)


def _movement_changed_sections(before: dict[str, object], after: dict[str, object]) -> set[str]:
    sections: set[str] = set()
    def changed(k: str) -> bool:
        a = before.get(k); b = after.get(k)
        if isinstance(a, bool) or isinstance(b, bool):
            return bool(a) != bool(b)
        try:
            return abs(float(a or 0.0) - float(b or 0.0)) > 0.0001
        except Exception:
            return a != b
    if changed("speed_scale") or changed("walk_speed"):
        sections.add("speed")
    if any(changed(k) for k in ("jump_goal", "jump_velocity", "sprint_jump_goal", "double_jump_goal", "slide_jump_goal", "individual_jump_goals")):
        sections.add("jump")
    if changed("gravity_scale"):
        sections.add("gravity")
    if any(changed(k) for k in ("max_step_height", "walkable_floor_angle", "walkable_floor_z")):
        sections.add("wall")
    if any(changed(k) for k in ("glide_speed", "glide_boost", "glide_air_control", "dash_speed")):
        sections.add("glide")
    if changed("zero_vault_costs"):
        sections.add("vault")
    return sections


def _movement_force_default_jump_type(pawn: object, move: object | None = None) -> None:
    """Best-effort: make the next air jump use the normal DefaultJump type.

    The user's live testing showed the native counter reset works, but if we let
    BL4 reach JumpCurrentCount == 2 it consumes the DoubleJump goal.  We now reset
    as soon as any jump is counted and try to keep CurrentJump on DefaultJump so
    repeated air jumps use the modified default JumpGoal height.
    """
    try:
        if move is None:
            move = getattr(pawn, "OakCharacterMovement", None) or getattr(pawn, "CharacterMovement", None)
    except Exception:
        move = None
    if move is None or _movement_is_default_obj(move):
        return
    try:
        cj = getattr(move, "CurrentJump", None)
        jt = getattr(cj, "JumpType", None) if cj is not None else None
        if jt is None:
            return
        # Mutate a copy-like wrapped struct in place; this is the same shape that
        # SetCurrentJumpType accepts from live CurrentJump.JumpType probes.
        try:
            setattr(jt, "TagName", "Movement.JumpType.DefaultJump")
        except Exception:
            try:
                jt._set_field("TagName", "Movement.JumpType.DefaultJump")
            except Exception:
                pass
        set_type = getattr(move, "SetCurrentJumpType", None)
        if callable(set_type):
            try:
                set_type(jt)
            except Exception:
                pass
        rep = getattr(move, "OnRep_CurrentJump", None)
        if callable(rep):
            try:
                rep()
            except Exception:
                pass
    except Exception:
        pass

def _movement_local_pawn_direct() -> object | None:
    """Resolve the local pawn directly from get_pc(), without world/GameState scans."""
    try:
        pc = get_pc()
    except Exception:
        pc = None
    if pc is None:
        return None
    for attr in ("Pawn", "AcknowledgedPawn", "Character"):
        try:
            pawn = getattr(pc, attr, None)
            if pawn is not None and not _movement_is_default_obj(pawn):
                return pawn
        except Exception:
            pass
    try:
        fn = getattr(pc, "GetPawn", None)
        if callable(fn):
            pawn = fn()
            if pawn is not None and not _movement_is_default_obj(pawn):
                return pawn
    except Exception:
        pass
    return None


def _movement_infinite_move_for_pawn(pawn: object) -> object | None:
    if pawn is None:
        return None
    for attr in ("OakCharacterMovement", "CharacterMovement", "GbxCharacterMovement", "MovementComponent", "PawnMovement", "Movement"):
        try:
            move = getattr(pawn, attr, None)
            if move is not None and not _movement_is_default_obj(move):
                return move
        except Exception:
            pass
    for meth in ("GetMovementComponent", "GetCharacterMovement"):
        try:
            fn = getattr(pawn, meth, None)
            if callable(fn):
                move = fn()
                if move is not None and not _movement_is_default_obj(move):
                    return move
        except Exception:
            pass
    return None


def _movement_set_if_needed(obj: object, attr: str, value: object) -> bool:
    try:
        if obj is None or not hasattr(obj, attr):
            return False
        try:
            cur = getattr(obj, attr)
            if cur == value:
                return False
        except Exception:
            pass
        setattr(obj, attr, value)
        return True
    except Exception:
        return False


def _movement_force_infinite_jump_ready(pawn: object, move: object | None = None) -> bool:
    """Keep BL4's jump gate open without touching glide/input/jump type.

    This restores the proven camera-hook behavior: reset spent jump counters and
    keep max counts high.  Do not call StopJumping(), do not force DefaultJump,
    and do not write CurrentJump.JumpGoal here.
    """
    if pawn is None or _movement_is_default_obj(pawn):
        return False
    try:
        move = move or _movement_infinite_move_for_pawn(pawn)
    except Exception:
        move = move
    changed = False
    for attr, value in (
        ("JumpCurrentCount", 0),
        ("JumpCurrentCountPreJump", 0),
        ("JumpedCount", 0),
        ("CurrentJumpCount", 0),
        ("CurrentJumpCountPreJump", 0),
        ("JumpMaxCount", 999),
        ("JumpMaxCountPreJump", 999),
        ("bProxyIsJumpForceApplied", False),
        ("JumpKeyHoldTime", 0.0),
        ("JumpForceTimeRemaining", 0.0),
    ):
        if _movement_set_if_needed(pawn, attr, value):
            changed = True
    if move is not None and not _movement_is_default_obj(move):
        for attr, value in (
            ("JumpedCount", 0),
            ("JumpCurrentCount", 0),
            ("JumpCurrentCountPreJump", 0),
            ("CurrentJumpCount", 0),
            ("CurrentJumpCountPreJump", 0),
            ("JumpMaxCount", 999),
            ("JumpMaxCountPreJump", 999),
        ):
            if _movement_set_if_needed(move, attr, value):
                changed = True
    return bool(changed)


def _movement_infinite_jump_cached_contexts(now: float) -> list[tuple[int, str, object, object | None, object | None]]:
    """Resolve party contexts for Infinite Jump without scanning every HUD frame."""
    global _movement_infinite_jump_context_cache, _movement_infinite_jump_context_cache_time
    try:
        if _movement_infinite_jump_context_cache and now - float(_movement_infinite_jump_context_cache_time) < 1.0:
            return list(_movement_infinite_jump_context_cache)
    except Exception:
        pass
    try:
        contexts = _movement_live_party_contexts_cached(1.0)
    except Exception:
        contexts = []
    _movement_infinite_jump_context_cache = list(contexts)
    _movement_infinite_jump_context_cache_time = now
    return contexts


def _movement_reset_pawn_jump_counter_if_spent(pawn: object, move: object | None = None) -> bool:
    """Compatibility wrapper for older HUD/pre-jump paths.

    Infinite Jump is now maintained by the camera hook, so this should be a
    narrow counter reset only. It intentionally does not check IsFalling because
    that check caused the next air-jump gate to stay closed in some BL4 states.
    """
    return _movement_force_infinite_jump_ready(pawn, move)

def _movement_infinite_jump_hud_tick(now: float) -> None:
    """HUD-piggybacked infinite jump.

    No hooks, no input polling, and no broad per-frame object discovery.  We only
    look at enabled player pawns and only reset when JumpCurrentCount has crossed
    the native double-jump limit.
    """
    if not _movement_infinite_jump_indices:
        return
    if not _movement_is_listen_host_cached(now):
        return
    for idx, _name, _pc, pawn, _move in _movement_infinite_jump_cached_contexts(now):
        try:
            if int(idx) not in _movement_infinite_jump_indices:
                continue
        except Exception:
            continue
        _movement_reset_pawn_jump_counter_if_spent(pawn, _move)



def _blimgui_note_party_signature_from_hud_tick(now: float) -> None:
    """Track party churn using the cheap PlayerArray signature only."""
    global _blimgui_last_party_signature, _blimgui_draw_paused_until
    if not _blimgui_join_safe_mode:
        return
    try:
        sig = repr(_party_players_signature())
    except Exception:
        return
    if not _blimgui_last_party_signature:
        _blimgui_last_party_signature = sig
        return
    if sig != _blimgui_last_party_signature:
        _blimgui_last_party_signature = sig
        return

def _movement_background_tick() -> None:
    """HUD tick side work: auto-apply once and lightweight infinite jump."""
    global _movement_apply_on_load_done, _movement_last_auto_apply_try, _movement_last_jump_refresh, _movement_next_jump_refresh_due
    global _movement_status, _movement_pending_apply, _movement_pending_apply_due, _movement_pending_apply_reason, _movement_off_host_pause_until
    now = time.monotonic()
    global _blimgui_party_signature_next_check
    if (not _movement_pending_apply) and (not (_movement_auto_apply_on_load and not _movement_apply_on_load_done)):
        return
    try:
        if now >= float(_blimgui_party_signature_next_check or 0.0):
            _blimgui_party_signature_next_check = now + 2.0
            _blimgui_note_party_signature_from_hud_tick(now)
    except Exception:
        pass
    _movement_next_jump_refresh_due = 0.0
    if not _movement_is_listen_host_cached(now):
        # Joined clients must be completely silent: no movement writes, no remote
        # player scans, no HUD toasts, and no repeating host checks every frame.
        _movement_pending_apply = False
        _movement_pending_apply_due = 0.0
        _movement_pending_apply_reason = ""
        _movement_apply_on_load_done = True
        # Do not clear Infinite Jump here. Infinite Jump is local/camera-hook based
        # and should keep working for the local player even when movement apply
        # and remote player targeting are paused off-host.
        if now >= float(_movement_off_host_pause_until or 0.0):
            _movement_status = _movement_off_host_status("movement tools")
            _movement_off_host_pause_until = now + 5.0
        return
    try:
        _movement_apply_pending_if_due(now)
    except Exception:
        pass
    try:
        _movement_infinite_jump_hud_tick(now)
    except Exception:
        pass
    if _movement_auto_apply_on_load and not _movement_apply_on_load_done and now - float(_movement_last_auto_apply_try) >= 2.0:
        _movement_last_auto_apply_try = now
        try:
            _apply_movement_adjustments_all()
            if "0 player pawn(s)" not in str(_movement_status):
                _movement_apply_on_load_done = True
        except Exception:
            pass


def _movement_recalc_floor_z_from_angle() -> None:
    global _movement_walkable_floor_z
    try:
        import math
        _movement_walkable_floor_z = max(0.0, min(1.0, math.cos(math.radians(float(_movement_walkable_floor_angle)))))
    except Exception:
        pass


def _apply_movement_adjustments_all() -> None:
    _apply_movement_adjustments_sections(None)


def _apply_movement_adjustments_sections(sections: set[str] | None = None) -> None:
    """Apply movement tuning to every live player; sections=None means all."""
    global _movement_pending_apply, _movement_pending_apply_due, _movement_pending_apply_reason, _movement_pending_sections
    _movement_pending_apply = False
    _movement_pending_apply_due = 0.0
    _movement_pending_apply_reason = ""
    _movement_pending_sections = set()
    global _movement_speed_scale, _movement_walk_speed, _movement_jump_goal, _movement_jump_velocity, _movement_sprint_jump_goal, _movement_double_jump_goal, _movement_slide_jump_goal, _movement_jump_hold_time, _movement_individual_jump_goals
    global _movement_gravity_scale, _movement_max_step_height, _movement_jump_count, _movement_jump_off_z_factor
    global _movement_walkable_floor_angle, _movement_walkable_floor_z, _movement_glide_speed, _movement_glide_boost, _movement_glide_air_control, _movement_dash_speed, _movement_zero_vault_costs, _movement_status
    if not _movement_require_host("movement apply"):
        return
    _movement_speed_scale = max(0.05, min(25.0, float(_movement_speed_scale)))
    _movement_walk_speed = max(50.0, min(10000.0, float(_movement_walk_speed)))
    _movement_jump_goal = max(0.0, min(10000.0, float(_movement_jump_goal)))
    _movement_jump_velocity = max(0.0, min(10000.0, float(_movement_jump_velocity)))
    if not _movement_individual_jump_goals:
        _movement_sprint_jump_goal = float(_movement_jump_goal)
        _movement_double_jump_goal = float(_movement_jump_goal)
        _movement_slide_jump_goal = float(_movement_jump_goal)
    else:
        _movement_sprint_jump_goal = max(0.0, min(10000.0, float(_movement_sprint_jump_goal)))
        _movement_double_jump_goal = max(0.0, min(10000.0, float(_movement_double_jump_goal)))
        _movement_slide_jump_goal = max(0.0, min(10000.0, float(_movement_slide_jump_goal)))
    _movement_jump_hold_time = 0.0
    _movement_gravity_scale = max(0.0, min(10.0, float(_movement_gravity_scale)))
    _movement_max_step_height = max(0.0, min(1000.0, float(_movement_max_step_height)))
    _movement_jump_count = 2
    _movement_jump_off_z_factor = 0.5
    _movement_walkable_floor_angle = max(0.0, min(89.9, float(_movement_walkable_floor_angle)))
    _movement_walkable_floor_z = max(0.0, min(1.0, float(_movement_walkable_floor_z)))
    _movement_glide_speed = max(0.0, min(30000.0, float(_movement_glide_speed)))
    _movement_glide_boost = max(0.0, min(30000.0, float(_movement_glide_boost)))
    _movement_glide_air_control = max(0.0, min(50.0, float(_movement_glide_air_control)))
    _movement_dash_speed = max(0.0, min(30000.0, float(_movement_dash_speed)))
    try:
        msg = apply_movement_advanced_to_all_players(
            _movement_speed_scale,
            _movement_walk_speed,
            _movement_jump_goal,
            _movement_jump_velocity,
            _movement_gravity_scale,
            _movement_max_step_height,
            _movement_jump_count,
            _movement_jump_off_z_factor,
            _movement_walkable_floor_angle,
            _movement_walkable_floor_z,
            _movement_sprint_jump_goal,
            _movement_jump_hold_time,
            _movement_glide_speed,
            _movement_glide_boost,
            _movement_glide_air_control,
            _movement_dash_speed,
            0.0 if _movement_zero_vault_costs else None,
            double_jump_goal=_movement_double_jump_goal,
            slide_jump_goal=_movement_slide_jump_goal,
            sections=sections,
            reset_jump_defaults=False,
        )
        _movement_save_settings()
        _movement_status = msg
        _log(msg)
        _set_status_pill(msg, "green")
    except Exception as exc:
        _movement_status = f"Movement apply failed: {exc!r}"
        _log(_movement_status)


def _reset_movement_adjustments_all() -> None:
    """Reset the local sliders and apply conservative vanilla-ish values."""
    global _movement_speed_scale, _movement_walk_speed, _movement_jump_goal, _movement_jump_velocity, _movement_sprint_jump_goal, _movement_double_jump_goal, _movement_slide_jump_goal, _movement_individual_jump_goals, _movement_jump_hold_time
    global _movement_gravity_scale, _movement_max_step_height, _movement_jump_count, _movement_jump_off_z_factor
    global _movement_walkable_floor_angle, _movement_walkable_floor_z, _movement_glide_speed, _movement_glide_boost, _movement_glide_air_control, _movement_dash_speed, _movement_zero_vault_costs, _movement_status
    if not _movement_require_host("movement reset"):
        return
    _movement_speed_scale = float(_MOVEMENT_DEFAULT_PRESET["speed_scale"])
    _movement_walk_speed = float(_MOVEMENT_DEFAULT_PRESET["walk_speed"])
    _movement_jump_goal = float(_MOVEMENT_DEFAULT_PRESET["jump_goal"])
    _movement_jump_velocity = float(_MOVEMENT_DEFAULT_PRESET["jump_velocity"])
    _movement_sprint_jump_goal = float(_MOVEMENT_DEFAULT_PRESET["sprint_jump_goal"])
    _movement_double_jump_goal = float(_MOVEMENT_DEFAULT_PRESET["double_jump_goal"])
    _movement_slide_jump_goal = float(_MOVEMENT_DEFAULT_PRESET["slide_jump_goal"])
    _movement_individual_jump_goals = False
    _movement_jump_hold_time = 0.0
    _movement_gravity_scale = float(_MOVEMENT_DEFAULT_PRESET["gravity_scale"])
    _movement_max_step_height = float(_MOVEMENT_DEFAULT_PRESET["max_step_height"])
    _movement_jump_count = 2
    _movement_jump_off_z_factor = 0.5
    _movement_walkable_floor_angle = float(_MOVEMENT_DEFAULT_PRESET["walkable_floor_angle"])
    _movement_walkable_floor_z = float(_MOVEMENT_DEFAULT_PRESET["walkable_floor_z"])
    _movement_glide_speed = float(_MOVEMENT_DEFAULT_PRESET["glide_speed"])
    _movement_glide_boost = float(_MOVEMENT_DEFAULT_PRESET["glide_boost"])
    _movement_glide_air_control = float(_MOVEMENT_DEFAULT_PRESET["glide_air_control"])
    _movement_dash_speed = float(_MOVEMENT_DEFAULT_PRESET["dash_speed"])
    _movement_zero_vault_costs = False
    try:
        msg = reset_movement_advanced_all_players()
        _movement_save_settings()
        _movement_status = f"{msg} Reset movement sliders to defaults."
        _log(_movement_status)
        _set_status_pill("Movement reset to defaults.", "gold")
    except Exception as exc:
        _movement_status = f"Movement reset failed: {exc!r}"
        _log(_movement_status)


def _movement_preset(speed_scale: float, walk_speed: float, jump_goal: float, jump_velocity: float, gravity: float | None = None, step: float | None = None, jumps: int | None = None, floor_angle: float | None = None, floor_z: float | None = None, glide_speed: float | None = None, glide_boost: float | None = None, glide_air: float | None = None, dash_speed: float | None = None, zero_vault: bool | None = None, sprint_jump_goal: float | None = None, jump_hold_time: float | None = None) -> None:
    global _movement_speed_scale, _movement_walk_speed, _movement_jump_goal, _movement_jump_velocity, _movement_sprint_jump_goal, _movement_double_jump_goal, _movement_slide_jump_goal, _movement_individual_jump_goals, _movement_jump_hold_time
    global _movement_gravity_scale, _movement_max_step_height, _movement_jump_count, _movement_walkable_floor_angle, _movement_walkable_floor_z, _movement_glide_speed, _movement_glide_boost, _movement_glide_air_control, _movement_dash_speed, _movement_zero_vault_costs
    _movement_speed_scale = float(speed_scale)
    _movement_walk_speed = float(walk_speed)
    _movement_jump_goal = float(jump_goal)
    _movement_jump_velocity = float(jump_velocity)
    if sprint_jump_goal is not None:
        _movement_sprint_jump_goal = float(sprint_jump_goal)
    else:
        _movement_sprint_jump_goal = float(jump_goal)
    _movement_double_jump_goal = float(jump_goal)
    _movement_slide_jump_goal = float(_movement_sprint_jump_goal)
    _movement_individual_jump_goals = False
    if jump_hold_time is not None:
        _movement_jump_hold_time = float(jump_hold_time)
    if gravity is not None:
        _movement_gravity_scale = float(gravity)
    if step is not None:
        _movement_max_step_height = float(step)
    if jumps is not None:
        _movement_jump_count = int(jumps)
    if floor_angle is not None:
        _movement_walkable_floor_angle = float(floor_angle)
        _movement_recalc_floor_z_from_angle()
    if floor_z is not None:
        _movement_walkable_floor_z = float(floor_z)
    if glide_speed is not None:
        _movement_glide_speed = float(glide_speed)
    if glide_boost is not None:
        _movement_glide_boost = float(glide_boost)
    if glide_air is not None:
        _movement_glide_air_control = float(glide_air)
    if dash_speed is not None:
        _movement_dash_speed = float(dash_speed)
    if zero_vault is not None:
        _movement_zero_vault_costs = bool(zero_vault)
    _apply_movement_adjustments_all()


def _movement_set_time() -> None:
    global _movement_status, _movement_time_dilation
    _movement_time_dilation = max(0.01, min(64.0, float(_movement_time_dilation)))
    msg = set_time_dilation(_movement_time_dilation)
    _movement_save_settings(); _movement_status = msg; _log(msg); _set_status_pill(msg, "cyan")


def _movement_reset_time() -> None:
    global _movement_time_dilation
    _movement_time_dilation = 1.0
    _movement_set_time()


def _movement_toggle_players_only() -> None:
    global _movement_status
    msg = toggle_players_only()
    _movement_status = msg; _log(msg); _set_status_pill(msg, "purple")


def _movement_apply_no_target() -> None:
    global _movement_status
    msg = set_no_target(_movement_no_target)
    _movement_status = msg; _log(msg); _set_status_pill(msg, "purple")

def _movement_toggle_no_target() -> None:
    global _movement_no_target
    _movement_no_target = not bool(_movement_no_target)
    _movement_apply_no_target()


def _movement_apply_noclip() -> None:
    global _movement_status
    msg = set_noclip(_movement_noclip)
    _movement_save_settings(); _movement_status = msg; _log(msg); _set_status_pill(msg, "purple")


def _movement_delete_ground_items() -> None:
    global _movement_status
    msg = delete_ground_items()
    _movement_status = msg; _log(msg); _set_status_pill(msg, "red")

def _movement_zero_vault_now() -> None:
    global _movement_status
    msg = zero_vault_power_costs_all_players()
    _movement_status = msg; _log(msg); _set_status_pill(msg, "green")


def _movement_teleport_selected_to_party_slot(slot_idx: int) -> None:
    global _movement_status
    try:
        selected_idx = _selected_player_index_value()
        contexts = _movement_live_party_contexts(False)
        src = None; dst = None; src_name = None; dst_name = None
        for ctx_idx, name, _pc, pawn, _move in contexts:
            if selected_idx is not None and int(ctx_idx) == int(selected_idx):
                src = pawn; src_name = name
            if int(ctx_idx) == int(slot_idx):
                dst = pawn; dst_name = name
        if src is None:
            _movement_status = "Teleport failed: no selected player pawn."
        elif dst is None:
            _movement_status = f"Teleport failed: P{slot_idx + 1} pawn not found."
        else:
            _movement_status = teleport_pawn_to_pawn(src, dst) + f" {src_name or 'Selected'} -> P{slot_idx + 1} {dst_name or ''}."
        _log(_movement_status)
        _set_status_pill(_movement_status, "cyan")
    except Exception as exc:
        _movement_status = f"Teleport failed: {exc!r}"
        _log(_movement_status)



def _movement_enabled_infinite_names() -> str:
    try:
        contexts = _movement_live_party_contexts_cached(1.0)
    except Exception:
        contexts = []
    names = [str(name) for idx, name, _pc, _pawn, _move in contexts if int(idx) in _movement_infinite_jump_indices]
    return ", ".join(names) if names else "none"


def _movement_pawn_party_index(pawn: object) -> int | None:
    if pawn is None:
        return None
    try:
        contexts = _movement_live_party_contexts_cached(1.0)
    except Exception:
        contexts = []
    pawn_s = str(pawn)
    for idx, _name, _pc, ctx_pawn, _move in contexts:
        try:
            if ctx_pawn is pawn or str(ctx_pawn) == pawn_s:
                return int(idx)
        except Exception:
            pass
    return None


def _movement_set_infinite_jump_for_index(idx: int, enabled: bool) -> None:
    global _movement_status, _movement_infinite_jump_context_cache, _movement_infinite_jump_context_cache_time
    try:
        idx = int(idx)
        if enabled:
            _movement_infinite_jump_indices.add(idx)
        else:
            _movement_infinite_jump_indices.discard(idx)
        _movement_infinite_jump_context_cache = []
        _movement_infinite_jump_context_cache_time = 0.0
        _movement_status = f"Infinite Jump enabled for: {_movement_enabled_infinite_names()}."
        _log(_movement_status)
        _set_status_pill(_movement_status, "green" if enabled else "cyan")
    except Exception as exc:
        _movement_status = f"Infinite Jump toggle failed: {exc!r}"
        _log(_movement_status)
        _set_status_pill(_movement_status, "red")


def _movement_set_infinite_jump_all(enabled: bool) -> None:
    global _movement_status, _movement_infinite_jump_context_cache, _movement_infinite_jump_context_cache_time
    try:
        contexts = _movement_live_party_contexts(False)
        # Treat All ON as a batch of the same per-player toggles, not a broad
        # wildcard.  Only enable slots that currently resolve to a real pawn so
        # stale/default party entries cannot poison the pre-jump hook.
        if enabled:
            _movement_infinite_jump_indices.clear()
            for idx, _name, _pc, pawn, _move in contexts:
                if pawn is not None and not _movement_is_default_obj(pawn):
                    _movement_infinite_jump_indices.add(int(idx))
        else:
            _movement_infinite_jump_indices.clear()
        # Force the HUD tick to re-resolve after a batch toggle.
        _movement_infinite_jump_context_cache = []
        _movement_infinite_jump_context_cache_time = 0.0
        _movement_status = f"Infinite Jump enabled for: {_movement_enabled_infinite_names()}."
        _log(_movement_status)
        _set_status_pill(_movement_status, "green" if enabled else "cyan")
    except Exception as exc:
        _movement_status = f"Infinite Jump all toggle failed: {exc!r}"
        _log(_movement_status)
        _set_status_pill(_movement_status, "red")


def _movement_prepare_infinite_jump_pawn(pawn: object) -> bool:
    """Clear the native BL4 jump gate immediately before validation.

    This is now a helper/fallback for the pre-jump hooks. The primary path is
    the camera hook, but this keeps the old validation hooks useful when they
    fire. It allows local-client index 0 without a host GameState scan.
    """
    if pawn is None or _movement_is_default_obj(pawn):
        return False
    idx = _movement_pawn_party_index(pawn)
    if idx is None:
        try:
            local_pawn = _movement_local_pawn_direct()
            if local_pawn is pawn or (local_pawn is not None and str(local_pawn) == str(pawn)):
                idx = 0
        except Exception:
            idx = None
    if idx is None or int(idx) not in _movement_infinite_jump_indices:
        return False
    return _movement_force_infinite_jump_ready(pawn, _movement_infinite_move_for_pawn(pawn))

def _movement_is_default_obj(obj: object) -> bool:
    try:
        return obj is None or "Default__" in str(obj)
    except Exception:
        return obj is None


def _movement_hook_arg_to_pawn(obj: object) -> object | None:
    """Resolve a hook payload object to the live OakCharacter/Pawn.

    mods_base hook payload shapes differ across SDK builds.  Sometimes arg0 is
    the caller, sometimes a params struct carries Object/obj/self.  Be generous.
    """
    if obj is None or _movement_is_default_obj(obj):
        return None
    # Direct OakCharacter/Character object.
    try:
        if hasattr(obj, "JumpCurrentCount") and hasattr(obj, "JumpMaxCount"):
            return obj
    except Exception:
        pass
    # Common wrapper/caller field names.
    for attr in ("Object", "object", "obj", "self", "This", "this", "Caller", "caller", "Context", "context"):
        try:
            inner = getattr(obj, attr, None)
        except Exception:
            inner = None
        if inner is not None and inner is not obj:
            pawn = _movement_hook_arg_to_pawn(inner)
            if pawn is not None:
                return pawn
    # Controller-like wrapper.
    for attr in ("OakCharacter", "Pawn", "AcknowledgedPawn", "Character", "ControlledPawn"):
        try:
            pawn = getattr(obj, attr, None)
        except Exception:
            pawn = None
        if pawn is not None and not _movement_is_default_obj(pawn):
            try:
                if hasattr(pawn, "JumpCurrentCount") and hasattr(pawn, "JumpMaxCount"):
                    return pawn
            except Exception:
                return pawn
    return None


def _movement_camera_infinite_jump_hook(*args, **kwargs):
    """Hot, cheap Infinite Jump path.

    CameraModifier:BlueprintModifyCamera was the proven reliable tick source for
    BL4. It fires while the player is active, before jump input needs the counters
    open, and does not depend on HUD widgets, menu draw, or GameState polling.
    """
    try:
        if not _movement_infinite_jump_indices:
            return None
        try:
            now = time.monotonic()
        except Exception:
            now = 0.0
        contexts = _movement_infinite_jump_cached_contexts(now)
        touched = set()
        for idx, _name, _pc, pawn, move in contexts:
            try:
                if int(idx) not in _movement_infinite_jump_indices:
                    continue
            except Exception:
                continue
            if pawn is None or _movement_is_default_obj(pawn):
                continue
            key = str(pawn)
            if key in touched:
                continue
            touched.add(key)
            _movement_force_infinite_jump_ready(pawn, move)
        # Safety fallback: when party contexts fail during travel/initial load,
        # still keep the local player working if slot 0 is enabled.
        try:
            if 0 in _movement_infinite_jump_indices:
                pawn = _movement_local_pawn_direct()
                if pawn is not None and str(pawn) not in touched:
                    _movement_force_infinite_jump_ready(pawn, _movement_infinite_move_for_pawn(pawn))
        except Exception:
            pass
    except Exception:
        pass
    return None


def _movement_jump_pre_hook(*args, **kwargs):
    try:
        for obj in list(args) + list(kwargs.values()):
            pawn = _movement_hook_arg_to_pawn(obj)
            if pawn is not None:
                _movement_prepare_infinite_jump_pawn(pawn)
                break
    except Exception:
        pass
    return None


def _movement_register_infinite_jump_hooks() -> None:
    # Primary path: proven camera hook. It is cheap-idle when no Infinite Jump
    # slots are enabled and does not depend on HUD/menu/GameState polling.
    try:
        hook(
            "/Script/Engine.CameraModifier:BlueprintModifyCamera",
            immediately_enable=True,
            hook_identifier="matts_sdk_boosting_tools_infinite_jump_camera_hook_v3",
        )(_movement_camera_infinite_jump_hook)
        try:
            _log("Infinite Jump camera hook installed: /Script/Engine.CameraModifier:BlueprintModifyCamera")
        except Exception:
            pass
    except Exception as exc:
        try:
            _log(f"Infinite Jump camera hook skipped: {exc!r}")
        except Exception:
            pass
    # Keep validation hooks as a backup. The user's manual console sequence worked
    # when counts were cleared before the next jump input; Jump() alone may be too late
    # on some input paths.
    targets = (
        "/Script/Engine.Character:CanJumpInternal",
        "/Script/Engine.Character:CanJump",
        "/Script/Engine.Character:Jump",
        "/Script/GbxGame.OakCharacter:CanJumpInternal",
        "/Script/GbxGame.OakCharacter:CanJump",
        "/Script/GbxGame.OakCharacter:Jump",
        "/Script/OakGame.OakCharacter:CanJumpInternal",
        "/Script/OakGame.OakCharacter:CanJump",
        "/Script/OakGame.OakCharacter:Jump",
    )
    for i, target in enumerate(targets):
        try:
            hook(
                target,
                immediately_enable=True,
                hook_identifier=f"matts_sdk_boosting_tools_infinite_jump_gate_hook_v2_{i}",
            )(_movement_jump_pre_hook)
            try:
                _log(f"Infinite Jump hook installed: {target}")
            except Exception:
                pass
        except Exception as exc:
            try:
                _log(f"Infinite Jump hook skipped {target}: {exc!r}")
            except Exception:
                pass


_movement_register_infinite_jump_hooks()

def _draw_movement_tab() -> None:
    """Lobby-wide player movement controls.  No keybinds are registered here."""
    global _movement_speed_scale, _movement_walk_speed, _movement_jump_goal, _movement_jump_velocity, _movement_sprint_jump_goal, _movement_double_jump_goal, _movement_slide_jump_goal, _movement_individual_jump_goals, _movement_jump_hold_time
    global _movement_gravity_scale, _movement_max_step_height, _movement_jump_count, _movement_jump_off_z_factor
    global _movement_walkable_floor_angle, _movement_walkable_floor_z, _movement_time_dilation, _movement_glide_speed, _movement_glide_boost, _movement_glide_air_control, _movement_dash_speed, _movement_zero_vault_costs, _movement_no_target, _movement_noclip
    global _movement_auto_apply_on_load
    imgui = _blimgui.imgui

    before = _movement_preset_dict()

    def _move_float(label: str, ident: str, value: float, lo: float, hi: float, fmt: str = "%.2f", width: float = 260.0) -> float:
        try:
            imgui.text_wrapped(str(label))
        except Exception:
            pass
        pushed = _push_full_item_width(pad=24.0, minimum=150.0, maximum=float(width))
        try:
            return float(_input_float_slider(f"###{ident}", float(value), float(lo), float(hi), fmt))
        finally:
            _pop_item_width_if(pushed)

    def _changed_enough(a: dict[str, object], b: dict[str, object]) -> bool:
        keys = ("speed_scale","walk_speed","jump_goal","gravity_scale","max_step_height","walkable_floor_angle","walkable_floor_z","glide_speed","glide_boost","glide_air_control","dash_speed","zero_vault_costs")
        for k in keys:
            if isinstance(a.get(k), bool) or isinstance(b.get(k), bool):
                if bool(a.get(k)) != bool(b.get(k)):
                    return True
            else:
                try:
                    if abs(float(a.get(k, 0.0)) - float(b.get(k, 0.0))) > 0.0001:
                        return True
                except Exception:
                    if a.get(k) != b.get(k):
                        return True
        return False

    try:
        imgui.text_wrapped("UI-only controls. Slider changes are debounced and apply after you stop dragging, preventing lag. Movement values start at defaults every game load unless Auto apply on game load is checked.")
        imgui.separator()
    except Exception:
        pass

    opened = _begin_resizable_card("card_player_movement_actions", "Presets / Save / Apply", "green", 260, 210, 440) if _cyber else True
    if opened:
        _card_button_row([
            ("Apply Now", _apply_movement_adjustments_all, "green", 110, 0),
            ("Save Preset", _movement_save_current_preset, "cyan", 125, 0),
            ("Load Saved", lambda: _movement_load_saved_preset(True), "purple", 115, 0),
            ("Reset Defaults", _reset_movement_adjustments_all, "gold", 135, 0),
        ])
        old_auto = _movement_auto_apply_on_load
        _movement_auto_apply_on_load = _checkbox("Auto apply saved preset on game load###msbt_move_auto_load", bool(_movement_auto_apply_on_load))
        if old_auto != _movement_auto_apply_on_load:
            _movement_save_settings()
        _muted_wrapped("Infinite Jump is handled by the existing HUD tick with a tiny counter check, not by input hooks or timers. Use the Infinite Jump card to enable it per player. Save Preset is explicit; normal slider changes are not cached between launches.")
        _card_button_row([
            ("Fast", lambda: _movement_preset(5.0, 3200.0, 560.0, 560.0, None, None, 2, None, None, 2600.0, 4200.0, 6.0, 3000.0, True, 560.0, 0.0), "cyan", 80, 0),
            ("Very Fast", lambda: _movement_preset(8.0, 5200.0, 700.0, 700.0, None, None, 2, None, None, 3800.0, 6500.0, 10.0, 5200.0, True, 700.0, 0.0), "purple", 110, 0),
            ("Moon", lambda: _movement_preset(float(_movement_speed_scale), float(_movement_walk_speed), 1200.0, 1200.0, 0.45, None, 2, None, None, float(_movement_glide_speed), float(_movement_glide_boost), float(_movement_glide_air_control), float(_movement_dash_speed), True, 1200.0, 0.0), "gold", 80, 0),
            ("Wall Walk", lambda: _movement_preset(max(float(_movement_speed_scale), 5.0), max(float(_movement_walk_speed), 3200.0), float(_movement_jump_goal), float(_movement_jump_goal), None, 700.0, 2, 89.9, 0.001, float(_movement_glide_speed), float(_movement_glide_boost), float(_movement_glide_air_control), float(_movement_dash_speed), True), "green", 110, 0),
            ("Fast Glide", lambda: _movement_preset(max(float(_movement_speed_scale), 5.0), max(float(_movement_walk_speed), 3200.0), float(_movement_jump_goal), float(_movement_jump_goal), None, None, 2, None, None, 5200.0, 8500.0, 14.0, 4500.0, True), "cyan", 115, 0),
        ])
        if _movement_status:
            _muted_wrapped(_movement_status)
    if _cyber: _end_resizable_card()

    def _draw_move_core_card() -> None:
        global _movement_speed_scale, _movement_walk_speed
        opened = _begin_resizable_card("card_player_movement_core", "Speed", "cyan", 175, 120, 360) if _cyber else True
        if opened:
            _movement_speed_scale = max(0.05, min(25.0, _move_float("Speed Scale", "msbt_move_speed_scale", float(_movement_speed_scale), 0.05, 25.0, "%.2fx", 240.0)))
            _movement_walk_speed = max(50.0, min(10000.0, _move_float("Walk / Ground Speed", "msbt_move_walk_speed", float(_movement_walk_speed), 50.0, 10000.0, "%.0f", 240.0)))
            _muted_wrapped("Writes MinAnalogWalkSpeed, MaxWalkSpeed, acceleration, and braking fields.")
        if _cyber: _end_resizable_card()

    def _draw_move_jump_card() -> None:
        global _movement_jump_goal, _movement_jump_velocity, _movement_sprint_jump_goal, _movement_double_jump_goal, _movement_slide_jump_goal, _movement_individual_jump_goals, _movement_gravity_scale
        opened = _begin_resizable_card("card_player_movement_jump", "Jump / Gravity", "purple", 225, 165, 400) if _cyber else True
        if opened:
            old_master = float(_movement_jump_goal)
            _movement_jump_goal = max(0.0, min(10000.0, _move_float("Master JumpGoal Height", "msbt_move_jump_goal", float(_movement_jump_goal), 0.0, 10000.0, "%.0f", 240.0)))
            _movement_jump_velocity = float(_movement_jump_goal)
            if abs(float(old_master) - float(_movement_jump_goal)) > 0.0001 and not _movement_individual_jump_goals:
                _movement_sprint_jump_goal = float(_movement_jump_goal)
                _movement_double_jump_goal = float(_movement_jump_goal)
                _movement_slide_jump_goal = float(_movement_jump_goal)
            was_individual = bool(_movement_individual_jump_goals)
            _movement_individual_jump_goals = _checkbox("Set individual jump goals###msbt_move_individual_jumps", bool(_movement_individual_jump_goals))
            if was_individual and not _movement_individual_jump_goals:
                _movement_sprint_jump_goal = float(_movement_jump_goal)
                _movement_double_jump_goal = float(_movement_jump_goal)
                _movement_slide_jump_goal = float(_movement_jump_goal)
            if _movement_individual_jump_goals:
                _movement_sprint_jump_goal = max(0.0, min(10000.0, _move_float("SprintJump GoalHeight", "msbt_move_sprint_goal", float(_movement_sprint_jump_goal), 0.0, 10000.0, "%.0f", 240.0)))
                _movement_double_jump_goal = max(0.0, min(10000.0, _move_float("DoubleJump GoalHeight", "msbt_move_double_goal", float(_movement_double_jump_goal), 0.0, 10000.0, "%.0f", 240.0)))
                _movement_slide_jump_goal = max(0.0, min(10000.0, _move_float("SlideJump GoalHeight", "msbt_move_slide_goal", float(_movement_slide_jump_goal), 0.0, 10000.0, "%.0f", 240.0)))
            _movement_gravity_scale = max(0.0, min(10.0, _move_float("Gravity Scale", "msbt_move_gravity", float(_movement_gravity_scale), 0.0, 10.0, "%.2f", 240.0)))
            _muted_wrapped("Master updates Default/Sprint/Double/Slide unless individual goals are enabled. Writes happen after the slider stops.")
        if _cyber: _end_resizable_card()


    def _draw_move_infinite_jump_card() -> None:
        opened = _begin_resizable_card("card_player_movement_infinite_jump", "Infinite Jump", "green", 210, 150, 420) if _cyber else True
        if opened:
            _muted_wrapped("Enable per player. HUD tick resets the native jump counter as soon as the first jump is counted, forcing repeated DefaultJump height without using the vanilla DoubleJump goal.")
            _card_button_row([
                ("All ON", lambda: _movement_set_infinite_jump_all(True), "green", 90, 0),
                ("All OFF", lambda: _movement_set_infinite_jump_all(False), "red", 95, 0),
            ])
            contexts = _movement_live_party_contexts_cached(1.0)
            if not contexts:
                _muted_wrapped("No live party players found.")
            for idx, name, _pc, _pawn, _move in contexts:
                enabled = int(idx) in _movement_infinite_jump_indices
                label = f"P{int(idx)+1} Infinite Jump [{'ON' if enabled else 'OFF'}]"
                _button(label, lambda i=int(idx), e=not enabled: _movement_set_infinite_jump_for_index(i, e), "green" if enabled else "cyan", 250, 0)
                try:
                    _blimgui.imgui.same_line()
                    _blimgui.imgui.text_wrapped(str(name))
                except Exception:
                    pass
            _muted_wrapped(f"Enabled: {_movement_enabled_infinite_names()}.")
        if _cyber: _end_resizable_card()

    def _draw_move_wall_card() -> None:
        global _movement_max_step_height, _movement_walkable_floor_angle, _movement_walkable_floor_z
        opened = _begin_resizable_card("card_player_movement_wall", "Wall / Step", "gold", 200, 145, 360) if _cyber else True
        if opened:
            _movement_max_step_height = max(0.0, min(1000.0, _move_float("Max Step Height", "msbt_move_step", float(_movement_max_step_height), 0.0, 1000.0, "%.0f", 240.0)))
            old_angle = _movement_walkable_floor_angle
            _movement_walkable_floor_angle = max(0.0, min(89.9, _move_float("Walkable Floor Angle", "msbt_move_floor_angle", float(_movement_walkable_floor_angle), 0.0, 89.9, "%.1f", 240.0)))
            if abs(float(old_angle) - float(_movement_walkable_floor_angle)) > 0.0001:
                _movement_recalc_floor_z_from_angle()
            _movement_walkable_floor_z = max(0.0, min(1.0, _move_float("Walkable Floor Z", "msbt_move_floor_z", float(_movement_walkable_floor_z), 0.0, 1.0, "%.3f", 240.0)))
            _muted_wrapped("Wall Walk preset uses 89.9 angle and FloorZ near 0.0.")
        if _cyber: _end_resizable_card()

    def _draw_move_glide_card() -> None:
        global _movement_glide_speed, _movement_glide_boost, _movement_glide_air_control, _movement_dash_speed, _movement_zero_vault_costs
        opened = _begin_resizable_card("card_player_movement_glide", "Glide / Dash / Vault", "blue", 235, 170, 420) if _cyber else True
        if opened:
            _movement_glide_speed = max(0.0, min(30000.0, _move_float("Gliding Speed", "msbt_move_glide_speed", float(_movement_glide_speed), 0.0, 30000.0, "%.0f", 240.0)))
            _movement_glide_boost = max(0.0, min(30000.0, _move_float("Gliding Speed Boost", "msbt_move_glide_boost", float(_movement_glide_boost), 0.0, 30000.0, "%.0f", 240.0)))
            _movement_glide_air_control = max(0.0, min(50.0, _move_float("Gliding Air Control", "msbt_move_glide_air", float(_movement_glide_air_control), 0.0, 50.0, "%.2f", 240.0)))
            _movement_dash_speed = max(0.0, min(30000.0, _move_float("Dash Speed", "msbt_move_dash", float(_movement_dash_speed), 0.0, 30000.0, "%.0f", 240.0)))
            _movement_zero_vault_costs = _checkbox("Set vault power costs to 0 on apply###msbt_move_zero_vault", bool(_movement_zero_vault_costs))
        if _cyber: _end_resizable_card()

    def _draw_move_utility_card() -> None:
        global _movement_time_dilation, _movement_noclip
        opened = _begin_resizable_card("card_player_movement_util", "World / Utility", "purple", 230, 160, 420) if _cyber else True
        if opened:
            _movement_time_dilation = max(0.01, min(64.0, _move_float("Time Dilation", "msbt_move_time", float(_movement_time_dilation), 0.01, 64.0, "%.2fx", 240.0)))
            nt_label = "No Target [ON]" if _movement_no_target else "No Target [OFF]"
            _card_button_row([
                ("Apply Time", _movement_set_time, "cyan", 115, 0),
                ("Reset Time", _movement_reset_time, "gold", 115, 0),
                ("Players Only", _movement_toggle_players_only, "purple", 130, 0),
                (nt_label, _movement_toggle_no_target, "green" if _movement_no_target else "cyan", 145, 0),
                ("Delete Ground Items", _movement_delete_ground_items, "red", 170, 0),
            ])
            old_nc = _movement_noclip
            _movement_noclip = _checkbox("Noclip local host pawn###msbt_noclip", bool(_movement_noclip))
            if old_nc != _movement_noclip:
                _movement_apply_noclip()
            _muted_wrapped("No Target is a live toggle only and is not cached between launches.")
        if _cyber: _end_resizable_card()

    def _draw_move_teleport_card() -> None:
        opened = _begin_resizable_card("card_player_movement_teleport", "Teleport Selected Player", "cyan", 170, 115, 360) if _cyber else True
        if opened:
            _muted_wrapped("Teleports the selected target player to the selected party slot pawn.")
            _card_button_row([
                ("To P1", lambda: _movement_teleport_selected_to_party_slot(0), "cyan", 84, 0),
                ("To P2", lambda: _movement_teleport_selected_to_party_slot(1), "cyan", 84, 0),
                ("To P3", lambda: _movement_teleport_selected_to_party_slot(2), "cyan", 84, 0),
                ("To P4", lambda: _movement_teleport_selected_to_party_slot(3), "cyan", 84, 0),
            ])
        if _cyber: _end_resizable_card()

    groups = [_draw_move_core_card, _draw_move_jump_card, _draw_move_infinite_jump_card, _draw_move_wall_card, _draw_move_glide_card, _draw_move_utility_card, _draw_move_teleport_card]

    def _draw_move_group(group: Callable[[], None]) -> None:
        try:
            group()
        except Exception as exc:
            try:
                _log(f"Movement card draw skipped after error: {exc!r}")
                imgui.text_wrapped(f"Movement card draw error: {exc!r}")
            except Exception:
                pass

    def _draw_move_column(column_id: str, column_groups: list[Callable[[], None]], width: float, height: float) -> bool:
        opened_child = False
        try:
            opened_child = _begin_child_region(column_id, max(220.0, float(height)), max(240.0, float(width)))
        except Exception as exc:
            try:
                _log(f"Movement column begin failed {column_id}: {exc!r}")
            except Exception:
                pass
            opened_child = False
        if not opened_child:
            return False
        try:
            for group in column_groups:
                _draw_move_group(group)
        finally:
            try:
                _end_child_region()
            except Exception:
                pass
        return True

    # Compact 3-column movement layout without using imgui.columns.  The native
    # columns API crashed this imgui_bundle build with cyber cards/sliders, so we
    # use three normal child regions side-by-side.  Each child gives
    # _begin_resizable_card a narrow available width, making the cards compact
    # while keeping the draw path stable.
    drew_columns = False
    try:
        avail_w = max(760.0, _imgui_available_width(1180.0))
        avail_h = max(360.0, _imgui_available_height(720.0) - 38.0)
        gap = 10.0
        col_w = max(250.0, (avail_w - (gap * 2.0)) / 3.0)
        columns = [
            ("msbt_move_col_left", [_draw_move_core_card, _draw_move_wall_card]),
            ("msbt_move_col_mid", [_draw_move_jump_card, _draw_move_glide_card]),
            ("msbt_move_col_right", [_draw_move_infinite_jump_card, _draw_move_utility_card, _draw_move_teleport_card]),
        ]
        for i, (cid, fns) in enumerate(columns):
            if i:
                try:
                    imgui.same_line()
                except Exception:
                    pass
            if not _draw_move_column(cid, fns, col_w, avail_h):
                drew_columns = False
                break
            drew_columns = True
    except Exception as exc:
        try:
            _log(f"Movement 3-column layout failed: {exc!r}")
        except Exception:
            pass
        drew_columns = False

    if not drew_columns:
        # Fallback remains linear and safe if child-region APIs are missing.
        for group in groups:
            _draw_move_group(group)

    after = _movement_preset_dict()
    changed_sections = _movement_changed_sections(before, after)
    if changed_sections:
        _movement_schedule_debounced_apply("movement slider", changed_sections)
    else:
        _movement_apply_pending_if_due()



def _open_bank_anywhere() -> None:
    """Open the player bank UI from the Boosting menu using the known GBX UI command."""
    cmd = "gbx.ui.view.stateadd MENU_BANK"
    try:
        _exec_console(cmd)
        _log("Opened bank menu from Boosting Tools.")
    except Exception as exc:
        _log(f"Open bank failed: {exc!r}. Try console command manually: {cmd}")


def _draw_dev_tools_card() -> None:
    global _debug_cam_speed
    imgui = _blimgui.imgui
    opened = _begin_resizable_card("card_dev_tools", "Cheats / Debug Cam", "pink", 245, 215, 420) if _cyber else True
    if opened:
        if _cyber:
            _muted_wrapped("Cheats target the selected player on host. As a joined client, cheats run on your local PlayerController; Teleport Pawn to Debug Cam remains host-only.")
        else:
            imgui.text_wrapped("Cheats target the selected player on host. As a joined client, cheats run on your local PlayerController; Teleport Pawn to Debug Cam remains host-only.")
        perks = [
            (0, "Give Experience", "cyan"),
            (1, "Give 1 Million Cash", "gold"),
            (2, "Give 100k Eridium", "purple"),
            (3, "Kill All Enemies", "red"),
            (4, "All Customs + Hovers", "pink"),
            (5, devperk_button_label(5, _selected_player_index_value()), "cyan"),
            (6, devperk_button_label(6, _selected_player_index_value()), "gold"),
            (7, "Spawn Legendary/Epic Loot", "purple"),
        ]
        _card_button_row([(label, lambda perk=perk: _activate_devperk_selected(perk), accent, 220, 0) for perk, label, accent in perks])
        imgui.spacing()
        _card_button_row([
            ("Open Bank Anywhere", _open_bank_anywhere, "cyan", 200, 0),
            ("Toggle Debug Cam", _toggle_debug_cam_selected, "gold", 180, 0),
            ("Teleport Pawn to Debug Cam", _teleport_pawn_to_debug_cam_selected, "cyan", 230, 0),
        ])
        _old_debug_cam_speed = float(_debug_cam_speed)
        _debug_cam_speed = clamp_debug_speed(_input_float_slider("Debug Cam Speed", _old_debug_cam_speed, 0.05, 50.0, "%.2fx"))
        if abs(float(_debug_cam_speed) - _old_debug_cam_speed) > 0.0001:
            _schedule_debug_cam_speed_apply()
        else:
            _apply_debug_cam_speed_if_due()
        _card_button_row([
            ("1x", lambda: _set_debug_cam_speed_preset(1.0), "cyan", 66, 0),
            ("5x", lambda: _set_debug_cam_speed_preset(5.0), "purple", 66, 0),
            ("10x", lambda: _set_debug_cam_speed_preset(10.0), "gold", 72, 0),
            ("Apply Debug Cam Speed", _apply_debug_cam_speed, "cyan", 190, 0),
        ])
        if _cyber:
            _muted_wrapped("Speed is clamped 0.05x to 50x. Presets update the slider and apply to the local debug cam.")
        else:
            imgui.text_wrapped("Speed is clamped 0.05x to 50x. Presets update the slider and apply to the local debug cam.")
    if _cyber:
        _end_resizable_card()



_MSBT_CACHE_DIR_NAME = "sdk_mods"


def _msbt_canonical_cache_dir() -> Path:
    r"""Single canonical user cache dir for all MattsSDKBoostingTools runtime data.

    Do not scan legacy paths, do not sync caches around, and do not use bundled
    seed files.  The only supported runtime cache location is Win64\sdk_mods
    (or the current sdk_mods folder when that is the loader cwd).
    """
    try:
        here = Path(__file__).resolve()
        for parent in here.parents:
            if parent.name.lower() == _MSBT_CACHE_DIR_NAME:
                return parent
    except Exception:
        pass
    try:
        cwd = Path.cwd().resolve()
        if cwd.name.lower() == _MSBT_CACHE_DIR_NAME:
            return cwd
        return cwd / _MSBT_CACHE_DIR_NAME
    except Exception:
        return Path(_MSBT_CACHE_DIR_NAME)


def _msbt_cache_path(file_name: str) -> Path:
    return _msbt_canonical_cache_dir() / file_name


_SERIAL_STORE_FILE_NAME = "MattsSDKBoostingTools_saved_serials.json"


def _serial_store_candidate_paths() -> list[Path]:
    # Single canonical location only.  Legacy files are intentionally ignored.
    return [_msbt_cache_path(_SERIAL_STORE_FILE_NAME)]


def _serial_store_path_for_read() -> Path | None:
    path = _msbt_cache_path(_SERIAL_STORE_FILE_NAME)
    try:
        return path if path.exists() else None
    except Exception:
        return None


def _serial_store_path_for_write() -> Path:
    path = _msbt_cache_path(_SERIAL_STORE_FILE_NAME)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return path

def _serial_store_new_id() -> str:
    return str(int(time.time() * 1000))


def _serial_store_load() -> None:
    global _serial_store_entries
    if _serial_store_entries:
        return
    try:
        path = _serial_store_path_for_read()
        if path is None:
            _serial_store_entries = []
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        entries = data.get("entries", data) if isinstance(data, dict) else data
        out: list[dict[str, str]] = []
        if isinstance(entries, list):
            for i, e in enumerate(entries):
                if not isinstance(e, dict):
                    continue
                serial = str(e.get("serial", "")).strip()
                if not serial:
                    continue
                out.append({
                    "id": str(e.get("id") or f"loaded_{i}_{abs(hash(serial))}"),
                    "name": str(e.get("name") or f"Serial {i + 1}").strip(),
                    "group": str(e.get("group") or "Default").strip() or "Default",
                    "serial": serial,
                })
        _serial_store_entries = out
        if out:
            _log(f"Serial Bookmarks loaded {len(out)} saved serial(s).")
    except Exception as exc:
        _serial_store_entries = []
        _log(f"Serial Bookmarks load failed: {exc!r}")


def _serial_store_save() -> None:
    try:
        path = _serial_store_path_for_write()
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"entries": _serial_store_entries}, f, indent=2, sort_keys=True)
        _log(f"Serial Bookmarks saved {len(_serial_store_entries)} serial(s).")
    except Exception as exc:
        _log(f"Serial Bookmarks save failed: {exc!r}")


def _serial_store_groups() -> list[str]:
    groups = sorted({str(e.get("group") or "Default") for e in _serial_store_entries})
    return ["All"] + (groups or ["Default"])


def _serial_store_filtered_entries() -> list[dict[str, str]]:
    groups = _serial_store_groups()
    idx = max(0, min(int(_serial_store_group_filter_index), len(groups) - 1))
    group = groups[idx]
    if group == "All":
        return list(_serial_store_entries)
    return [e for e in _serial_store_entries if str(e.get("group") or "Default") == group]


def _serial_store_set_active(entry: dict[str, str]) -> None:
    global _serial_store_active_id, _serial_store_name, _serial_store_group, _serial_store_serial
    _serial_store_active_id = str(entry.get("id", ""))
    _serial_store_name = str(entry.get("name", ""))
    _serial_store_group = str(entry.get("group", "Default")) or "Default"
    _serial_store_serial = str(entry.get("serial", ""))


def _serial_store_clear_form() -> None:
    global _serial_store_active_id, _serial_store_name, _serial_store_group, _serial_store_serial, _serial_store_status
    _serial_store_active_id = ""
    _serial_store_name = ""
    _serial_store_group = "Default"
    _serial_store_serial = ""
    _serial_store_status = "Ready for a new saved serial."


def _serial_store_save_form() -> None:
    global _serial_store_active_id, _serial_store_status
    name = (_serial_store_name or "").strip()
    group = (_serial_store_group or "Default").strip() or "Default"
    serial_text = (_serial_store_serial or "").strip()
    if not name:
        _serial_store_status = "Name is required before saving."
        _log("Serial Bookmarks: name is required before saving.")
        return
    if not serial_text:
        _serial_store_status = "Serial is required before saving."
        _log("Serial Bookmarks: serial is required before saving.")
        return
    # Validate/normalize enough to catch obvious mistakes, but keep the original text for deserialized lines.
    expanded = _parse_serial_text(serial_text)
    resolved = _resolve_give_serial_strings(expanded)
    if not resolved:
        _serial_store_status = "Could not resolve the serial text into a deliverable serial."
        _log("Serial Bookmarks: save blocked because serial could not be resolved.")
        return
    if _serial_store_active_id:
        for e in _serial_store_entries:
            if str(e.get("id")) == _serial_store_active_id:
                e.update({"name": name, "group": group, "serial": serial_text})
                _serial_store_status = f"Updated {name}."
                _serial_store_save()
                return
    _serial_store_active_id = _serial_store_new_id()
    _serial_store_entries.append({"id": _serial_store_active_id, "name": name, "group": group, "serial": serial_text})
    _serial_store_status = f"Saved {name}."
    _serial_store_save()


def _serial_store_delete_active() -> None:
    global _serial_store_entries, _serial_store_active_id, _serial_store_selected_ids, _serial_store_status
    if not _serial_store_active_id:
        _serial_store_status = "No saved serial selected to delete."
        return
    old_count = len(_serial_store_entries)
    _serial_store_entries = [e for e in _serial_store_entries if str(e.get("id")) != _serial_store_active_id]
    _serial_store_selected_ids.discard(_serial_store_active_id)
    deleted = old_count - len(_serial_store_entries)
    _serial_store_clear_form()
    _serial_store_status = f"Deleted {deleted} saved serial(s)."
    _serial_store_save()

def _serial_store_duplicate_active() -> None:
    global _serial_store_active_id, _serial_store_name, _serial_store_group, _serial_store_serial, _serial_store_status
    if not _serial_store_active_id:
        _serial_store_status = "Select a saved serial before duplicating."
        return
    _serial_store_active_id = ""
    _serial_store_name = ((_serial_store_name or "Serial").strip() or "Serial") + " Copy"
    _serial_store_status = "Duplicated into a new unsaved entry. Review, then Save."


def _serial_store_select_all_filtered(filtered: list[dict[str, str]]) -> None:
    _serial_store_selected_ids.update(str(e.get("id", "")) for e in filtered if str(e.get("id", "")))


def _serial_store_group_counts() -> dict[str, int]:
    counts: dict[str, int] = {"All": len(_serial_store_entries)}
    for e in _serial_store_entries:
        group = str(e.get("group") or "Default") or "Default"
        counts[group] = counts.get(group, 0) + 1
    return counts


def _serial_store_import_from_tools() -> None:
    global _serial_store_serial, _serial_store_status
    src = (_serial_tools_serialized or _serial_tools_deserialized or _serial_tools_input or "").strip()
    if not src:
        _serial_store_status = "Serial Tools has no output/input to import."
        return
    _serial_store_serial = src
    _serial_store_status = "Imported text from Serial Tools. Add a name/group, then save."


def _serial_store_selected_entries() -> list[dict[str, str]]:
    if _serial_store_selected_ids:
        return [e for e in _serial_store_entries if str(e.get("id")) in _serial_store_selected_ids]
    if _serial_store_active_id:
        return [e for e in _serial_store_entries if str(e.get("id")) == _serial_store_active_id]
    return []


def _serial_store_copy_selected_serials() -> None:
    global _serial_store_status
    count = _copy_serial_list_to_clipboard("selected bookmarked serials", _serial_store_selected_entries())
    _serial_store_status = f"Copied {count} selected bookmarked serial(s) to clipboard." if count else "Select one or more bookmarked serials to copy."


def _serial_store_deliver_selected(mode: str = "selected") -> None:
    global _serial_store_status
    entries = _serial_store_selected_entries()
    if not entries:
        _serial_store_status = "Select one or more saved serials first."
        _log("Serial Bookmarks: no saved serials selected.")
        return
    raw_serials: list[str] = []
    for e in entries:
        raw_serials.extend(_parse_serial_text(str(e.get("serial", ""))))
    serials = _resolve_give_serial_strings(raw_serials)
    if not serials:
        _serial_store_status = "Selected entries did not resolve to any deliverable serials."
        _log("Serial Bookmarks: selected entries did not resolve to any serials.")
        return
    names = ", ".join(str(e.get("name", "Serial")) for e in entries[:4])
    if len(entries) > 4:
        names += f", +{len(entries) - 4} more"
    _serial_store_status = _deliver_serials_with_target(serials, mode, "Serial Bookmarks")
    _log(f"Serial Bookmarks delivered {len(serials)} serial(s) from {names}: {_serial_store_status}")
    _log(f"Serial Bookmarks delivered {len(serials)} serial(s) ({names}) to all party players.")




_LOOTLEMON_CACHE_VERSION = 5
_LOOTLEMON_CACHE_FILE_NAME = "MattsSDKBoostingTools_lootlemon_codes.json"
_LOOTLEMON_EMBEDDED_CACHE_FILE_NAME = "MattsSDKBoostingTools_lootlemon_codes.json"
_LOOTLEMON_SERIAL_RE = re.compile(r"@U[^\s\"'\\]+")
_LOOTLEMON_ITEM_PATH_RE = re.compile(r"^/(weapon|shield|grenade-mod|repkit|class-mod|enhancement)/[^/?#]+-bl4/?$", re.I)
_LOOTLEMON_BAD_NAME_TOKENS = ("function", "const ", "var ", "let ", "textarea", "script", "placeholder", "discord", "{", "}", "=>")




def _serial_html_unescape_preserve_numeric_entities(text: str) -> str:
    """Decode only the HTML escapes that are safe inside BL4 Base85 serials.

    Base85 serials can legitimately contain literal sequences such as '&#4'.
    Python's html.unescape turns numeric entities into control characters, so a
    serial containing '...I9k&#4w3...' became '...I9kw3...' after ASCII cleanup.
    That corrupts the cached code and can make an entire reward package fail.

    Keep numeric entities as literal text, but decode the common HTML escapes
    Lootlemon/GZO may use to protect punctuation in page/JSON markup.
    """
    out = str(text or "")
    # Decode ampersand first, including double-escaped ampersands, but do not
    # feed the result through html.unescape or '&#123;' can become a character.
    for _ in range(3):
        new = re.sub(r"&amp;", "&", out, flags=re.I)
        if new == out:
            break
        out = new
    replacements = {
        "&lt;": "<", "&LT;": "<",
        "&gt;": ">", "&GT;": ">",
        "&quot;": '"', "&QUOT;": '"',
        "&apos;": "'", "&APOS;": "'",
        "&#x27;": "'", "&#X27;": "'", "&#39;": "'",
        "&#x2F;": "/", "&#X2F;": "/", "&#47;": "/",
        "&#x60;": "`", "&#X60;": "`", "&#96;": "`",
    }
    for k, v in replacements.items():
        out = out.replace(k, v)
    return out


def _module_data_path(file_name: str) -> Path:
    try:
        return Path(__file__).resolve().parent / file_name
    except Exception:
        return Path(file_name)


def _lootlemon_embedded_cache_path() -> Path:
    return _module_data_path(_LOOTLEMON_EMBEDDED_CACHE_FILE_NAME)


def _lootlemon_cache_payload_from_path(path: Path) -> dict | None:
    try:
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else None
    except Exception as exc:
        _log(f"Lootlemon local cache read failed for {path}: {exc!r}")
        return None


def _lootlemon_clean_cached_entries(entries_obj) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    seen: set[str] = set()
    if not isinstance(entries_obj, list):
        return cleaned
    for e in entries_obj:
        if not isinstance(e, dict):
            continue
        serial = _lootlemon_repair_known_serial(str(e.get("serial", "")).strip(), str(e.get("url", "")), str(e.get("name", "")))
        if not _lootlemon_is_valid_serial(serial) or serial in seen:
            continue
        seen.add(serial)
        cleaned.append({
            "id": str(e.get("id") or f"lootlemon:{len(cleaned)}"),
            "name": _lootlemon_clean_name(str(e.get("name", "Lootlemon Serial"))),
            "category": _lootlemon_clean_spaces(str(e.get("category", ""))) or "Lootlemon",
            "rarity": _lootlemon_clean_spaces(str(e.get("rarity", ""))),
            "manufacturer": _lootlemon_clean_spaces(str(e.get("manufacturer", ""))),
            "serial": serial,
            "source": "Lootlemon",
            "url": str(e.get("url", "")).strip(),
            "mattmab_validator": _lootlemon_clean_spaces(str(e.get("mattmab_validator", "") or "")),
            "mattmab_validator_detail": _lootlemon_clean_spaces(str(e.get("mattmab_validator_detail", "") or "")),
            "mattmab_validator_time": _lootlemon_clean_spaces(str(e.get("mattmab_validator_time", "") or "")),
        })
    cleaned.sort(key=lambda e: (str(e.get("category", "")).lower(), str(e.get("name", "")).lower()))
    return cleaned


def _lootlemon_local_cache_entries(prefer_user_cache: bool = True) -> list[dict[str, str]]:
    """Load Lootlemon entries from local JSON only; never probes lootlemon.com."""
    paths: list[Path] = []
    if prefer_user_cache:
        paths.append(_msbt_cache_path(_LOOTLEMON_CACHE_FILE_NAME))
    paths.append(_lootlemon_embedded_cache_path())
    seen_paths: set[str] = set()
    for path in paths:
        key = str(path)
        if key in seen_paths:
            continue
        seen_paths.add(key)
        payload = _lootlemon_cache_payload_from_path(path)
        if not payload:
            continue
        version = int(payload.get("version", 0) or 0)
        if version and version != _LOOTLEMON_CACHE_VERSION:
            _log(f"Lootlemon local cache version mismatch for {path}: {version} != {_LOOTLEMON_CACHE_VERSION}")
        cleaned = _lootlemon_clean_cached_entries(payload.get("entries", []))
        if cleaned:
            return cleaned
    return []


def _lootlemon_serial_link_index() -> dict[str, dict[str, str]]:
    return {str(e.get("serial", "")).strip(): e for e in _lootlemon_local_cache_entries(prefer_user_cache=True) if str(e.get("serial", "")).strip()}

def _lootlemon_cache_candidate_paths() -> list[Path]:
    # Single canonical user-created Lootlemon cache only.
    # No legacy Win64 reads, no bundled fallback, no recursive sync/copy.
    return [_msbt_cache_path(_LOOTLEMON_CACHE_FILE_NAME)]

def _cache_path_has_part(path: Path, part_name: str) -> bool:
    try:
        want = part_name.lower()
        return any(str(part).lower() == want for part in path.resolve().parts)
    except Exception:
        try:
            return any(str(part).lower() == part_name.lower() for part in path.parts)
        except Exception:
            return False


def _cache_path_is_bare_win64_legacy(path: Path) -> bool:
    """Legacy cache written directly beside Borderlands4.exe. Never prefer this over sdk_mods."""
    try:
        resolved = path.resolve()
    except Exception:
        resolved = path
    try:
        return str(resolved.parent.name).lower() == "win64"
    except Exception:
        return False


def _cache_path_priority(path: Path) -> int:
    """Higher wins. sdk_mods is canonical; bare Win64 is legacy fallback only."""
    if _cache_path_has_part(path, "sdk_mods"):
        return 400
    if _cache_path_is_bare_win64_legacy(path):
        return 0
    try:
        here_parent = Path(__file__).resolve().parent
        resolved = path.resolve()
        if resolved == here_parent / path.name or here_parent in resolved.parents:
            return 300
    except Exception:
        pass
    try:
        parts = [str(x).lower() for x in path.resolve().parts]
        if "borderlands 4" in parts and "saved" in parts:
            return 200
    except Exception:
        pass
    return 100


def _filter_cache_write_paths(paths: list[Path]) -> list[Path]:
    """Write canonical/non-legacy paths first; avoid refreshing stale bare Win64 copies."""
    non_legacy = [p for p in paths if not _cache_path_is_bare_win64_legacy(p)]
    chosen = non_legacy or paths
    return sorted(chosen, key=lambda p: (_cache_path_priority(p), str(p)), reverse=True)


def _remove_legacy_bare_win64_cache_files(paths: list[Path], label: str) -> None:
    for path in paths:
        if not _cache_path_is_bare_win64_legacy(path):
            continue
        try:
            if path.exists():
                path.unlink()
                _log(f"Removed stale legacy {label} cache from bare Win64 path: {path}")
        except Exception as exc:
            _log(f"Could not remove legacy {label} cache {path}: {exc!r}")

def _lootlemon_cache_score(path: Path) -> tuple[int, int, int]:
    """Return (valid_count, updated, mtime) so startup chooses the freshest real cache, not first path."""
    try:
        if not path.exists():
            return (-1, -1, -1)
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            version = int(data.get("version", 0) or 0)
            if version and version != _LOOTLEMON_CACHE_VERSION:
                return (-1, -1, -1)
            entries = data.get("entries", [])
            updated = int(float(data.get("updated", 0) or 0))
        else:
            entries = data
            updated = 0
        if not isinstance(entries, list):
            return (-1, -1, -1)
        valid = 0
        for e in entries:
            if isinstance(e, dict) and _lootlemon_is_valid_serial(str(e.get("serial", "")).strip()):
                valid += 1
        mtime = int(path.stat().st_mtime)
        return (valid, updated, mtime)
    except Exception:
        return (-1, -1, -1)


def _lootlemon_cache_path_for_read() -> Path | None:
    for path in (_msbt_cache_path(_LOOTLEMON_CACHE_FILE_NAME), _lootlemon_embedded_cache_path()):
        try:
            if _lootlemon_cache_score(path)[0] >= 0:
                return path
        except Exception:
            pass
    return None


def _lootlemon_cache_paths_for_write() -> list[Path]:
    path = _msbt_cache_path(_LOOTLEMON_CACHE_FILE_NAME)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return [path]

def _lootlemon_cache_path_for_write() -> Path:
    return _lootlemon_cache_paths_for_write()[0]


def _atomic_json_replace(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
    try:
        tmp.replace(path)
    except Exception:
        try:
            path.unlink()
        except Exception:
            pass
        tmp.replace(path)


def _remove_tmp_cache_states(candidates: list[Path], label: str) -> None:
    for old in candidates:
        try:
            tmp = old.with_name(old.name + ".tmp")
            if tmp.exists():
                tmp.unlink()
        except Exception as exc:
            _log(f"Could not remove stale {label} tmp cache {old}: {exc!r}")


def _lootlemon_ascii(text: str) -> str:
    text = html.unescape(str(text or ""))
    return "".join(ch if 32 <= ord(ch) <= 126 else " " for ch in text)


def _lootlemon_clean_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", _lootlemon_ascii(text)).strip()


def _trim_serial_markup_tail(serial: str) -> str:
    """Trim HTML tag tails accidentally captured after an encoded Base85 code."""
    s = str(serial or "").strip()
    # Real Base85 may contain '<' followed by printable characters, but a page tag
    # tail usually starts with '</' or common opening tag names after the code.
    for pat in (r"</", r"<br\b", r"<div\b", r"<span\b", r"<button\b", r"<input\b", r"<textarea\b", r"<script\b"):
        m = re.search(pat, s, flags=re.I)
        if m:
            s = s[:m.start()].strip()
            break
    return s

def _lootlemon_is_valid_serial(serial: str) -> bool:
    serial = str(serial or "").strip()
    return bool(serial.startswith("@U") and len(serial) >= 20 and "xxxx" not in serial.lower() and re.fullmatch(r"@[!-~]+", serial))


def _lootlemon_repair_known_serial(serial: str, url: str = "", name: str = "") -> str:
    """Repair known old Lootlemon cache truncations without weakening validation.

    BL4 Base85 serials may legitimately end in punctuation.  Some earlier
    scraper/cache paths dropped a final ')' from Lootlemon codes, which made
    valid catalog rows fail the validator.  Fresh extraction now preserves that
    trailing punctuation, and this narrow migration repairs already-cached rows.
    """
    serial = str(serial or "").strip()
    hay = f"{url} {name}".lower()
    known_missing_close = {
        "sparky-shield-bl4": "@Uge8^+m/*xI!fYv^M>VQ_G&;nG^Z",
        "oak-aged-cask-bl4": "@Uge92<m/*xI!eri{Mm?&1G&aPC^Z",
        "solar-temper-bl4": "@Ugy>*^35E/MjJ*#^iz-y28g&+xsZHfUtwPO0)k3X9<wFfLd}Iy",
    }
    for slug, broken in known_missing_close.items():
        if slug in hay and serial == broken:
            return serial + ")"
    return serial


def _lootlemon_extend_serial_if_split_by_markup(detail_html: str, match: object, serial: str) -> str:
    """Preserve a Base85 closing ')' even when page markup separates it.

    The normal regex keeps ')' when it is contiguous with the @U token.  Some
    Lootlemon detail markup can put the final ')' just after a tag/span boundary;
    for those cases, look immediately after the regex match, remove only HTML
    tags/space, and append a leading ')' if present.
    """
    serial = str(serial or "").strip()
    if not serial or serial.endswith(")"):
        return serial
    try:
        tail = html.unescape(str(detail_html or "")[match.end():match.end() + 96])
        tail = re.sub(r"^\s*(?:</?[^>]+>\s*)*", "", tail)
        if tail.startswith(")"):
            return serial + ")"
    except Exception:
        pass
    return serial


def _lootlemon_clean_name(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", str(text or ""))
    text = _lootlemon_clean_spaces(text)
    text = re.sub(r"^Copy\s+", "", text, flags=re.I)
    text = re.sub(r"\s+Code$", "", text, flags=re.I)
    if not text or any(tok in text.lower() for tok in _LOOTLEMON_BAD_NAME_TOKENS):
        return "Lootlemon Serial"
    return text[:96]


def _lootlemon_fetch(url: str) -> str:
    raise RuntimeError("Direct lootlemon.com scraping is disabled. Use the bundled/local Lootlemon JSON cache instead.")


def _lootlemon_abs_url(href: str) -> str:
    return urllib.parse.urljoin("https://www.lootlemon.com", str(href or ""))


def _lootlemon_slugify_name(text: str) -> str:
    text = _lootlemon_clean_spaces(text).lower()
    text = text.replace("'", "")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text



def _lootlemon_extract_ordnance_table_links(page_html: str) -> list[str]:
    """Fallback for BL4 Ordnance pages that expose table rows without static item hrefs."""
    text = re.sub(r"<[^>]+>", "\n", str(page_html or ""))
    lines = [_lootlemon_clean_spaces(x) for x in text.splitlines()]
    lines = [x for x in lines if x]
    type_values = {"Heavy", "Grenade"}
    makers = {"Daedalus", "Jakobs", "Maliwan", "Order", "Ripper", "Tediore", "Torgue", "Vladof"}
    skip_names = {"Rarity", "Name", "Ordnance Type", "Manufacturer", "Elements", "Content", "Sources", "Filters", "Types", "advertisement"}
    out: list[str] = []
    seen: set[str] = set()
    for i in range(0, max(0, len(lines) - 2)):
        name, typ, maker = lines[i], lines[i + 1], lines[i + 2]
        if typ not in type_values or maker not in makers:
            continue
        if name in skip_names or name in type_values or name in makers:
            continue
        if len(name) < 2 or len(name) > 80:
            continue
        low = name.lower()
        if any(bad in low for bad in ("image", "borderlands", "database", "filter", "advertisement", "lootlemon")):
            continue
        slug = _lootlemon_slugify_name(name)
        if not slug:
            continue
        url = f"https://www.lootlemon.com/grenade-mod/{slug}-bl4"
        if url not in seen:
            seen.add(url)
            out.append(url)
    return out

def _open_external_url(url: str, label: str = "URL") -> bool:
    url = str(url or "").strip()
    if not url:
        _log(f"{label}: no URL available to open.")
        return False
    try:
        unrealsdk.find_class(
            "/Script/Engine.KismetSystemLibrary"
        ).ClassDefaultObject.LaunchURL(url)
        _log(f"Opened {label}: {url}")
        return True
    except Exception as exc:
        _log(f"Could not open {label}: {exc!r}")
        return False


def _lootlemon_open_url(url: str) -> None:
    global _lootlemon_status
    if _open_external_url(url, "Lootlemon item page"):
        _lootlemon_status = "Opened Lootlemon item page."
    else:
        _lootlemon_status = "Could not open Lootlemon item page; see Activity Log."


def _draw_legit_disclaimer() -> None:
    imgui = _blimgui.imgui
    _muted_wrapped(_LEGIT_DISCLAIMER)
    try:
        imgui.same_line()
    except Exception:
        pass
    _button("Open save-editor.be###legit_disclaimer_save_editor", lambda: _open_external_url(_SAVE_EDITOR_URL, "save-editor.be"), "gold", 185, 0)



def _lootlemon_pagination_param_names(page_html: str) -> list[str]:
    """Return Webflow collection pagination query parameter prefixes.

    Lootlemon/Webflow list pages can expose only the first page in static HTML.
    Additional rows are served as normal HTML at URLs like:
        /db/borderlands-4/weapons?aa6d804c_page=2
    The opaque prefix may change when the page is republished, so discover it
    from links/script data when possible and fall back to the current known one.
    """
    names: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(r"[?&]([a-z0-9]{6,16})_page=\d+", str(page_html or ""), flags=re.I):
        name = m.group(1)
        low = name.lower()
        if low not in seen:
            seen.add(low)
            names.append(name)
    # Current Lootlemon/Webflow BL4 database collection prefix observed in 2026.
    if "aa6d804c" not in seen:
        names.append("aa6d804c")
    return names


def _lootlemon_fetch_category_list_pages(category_url: str, max_pages: int = 12) -> list[tuple[str, str]]:
    """Fetch all static Webflow pages for a Lootlemon category list.

    Returns (url, html) pairs.  Stops when the next page yields no new item
    links and no new inline serials.  This keeps the SDK dependency-free while
    still loading Webflow's paginated rows such as weapons page 2.
    """
    base_url = str(category_url or "").strip()
    if not base_url:
        return []

    pages: list[tuple[str, str]] = []
    seen_links: set[str] = set()
    seen_serials: set[str] = set()

    first_html = _lootlemon_fetch(base_url)
    pages.append((base_url, first_html))
    seen_links.update(_lootlemon_extract_item_links(first_html, base_url))
    seen_serials.update(m.group(0) for m in _LOOTLEMON_SERIAL_RE.finditer(_serial_html_unescape_preserve_numeric_entities(first_html)))

    param_names = _lootlemon_pagination_param_names(first_html)
    if not param_names:
        return pages

    parsed_base = urllib.parse.urlparse(base_url)
    base_query = urllib.parse.parse_qsl(parsed_base.query, keep_blank_values=True)

    for page_num in range(2, max_pages + 1):
        page_had_new = False
        page_fetched = False
        for param_name in param_names:
            query = [(k, v) for (k, v) in base_query if k != f"{param_name}_page"]
            query.append((f"{param_name}_page", str(page_num)))
            page_url = urllib.parse.urlunparse(parsed_base._replace(query=urllib.parse.urlencode(query)))
            try:
                page_html = _lootlemon_fetch(page_url)
                page_fetched = True
            except Exception as exc:
                _log(f"Lootlemon list page fetch failed for {page_url}: {exc!r}")
                continue

            links = set(_lootlemon_extract_item_links(page_html, base_url))
            serials = set(m.group(0) for m in _LOOTLEMON_SERIAL_RE.finditer(_serial_html_unescape_preserve_numeric_entities(page_html)))
            new_links = links - seen_links
            new_serials = serials - seen_serials
            if new_links or new_serials:
                seen_links.update(new_links)
                seen_serials.update(new_serials)
                pages.append((page_url, page_html))
                page_had_new = True
                break

        if not page_fetched or not page_had_new:
            break

    return pages

def _lootlemon_extract_item_links(page_html: str, category_url: str) -> list[str]:
    """Extract Lootlemon BL4 item detail links from a category page.

    Best-of-both-worlds parser:
    - keeps the old category-relative /db/borderlands-4/<category>/<slug> links
      which were needed for Repkits/Enhancements and any hydrated slug data;
    - also accepts real BL4 detail paths such as /grenade-mod/atling-gun-bl4,
      which fixes Ordnance.
    """
    links: list[str] = []
    seen: set[str] = set()
    category_url = str(category_url or "").rstrip("/")
    category_name = category_url.rstrip("/").split("/")[-1].lower()

    legacy_detail_markers = (
        "/weapon/", "/shield/", "/ordnance/", "/grenade/", "/heavy/",
        "/repkit/", "/rep-kit/", "/class-mod/", "/enhancement/", "/bonus-item/",
    )

    def add_link(raw: str) -> None:
        raw = html.unescape(str(raw or "")).strip()
        if not raw:
            return
        full_url = _lootlemon_abs_url(raw).split("#", 1)[0].rstrip("/")
        parsed = urllib.parse.urlparse(full_url)
        if parsed.netloc and parsed.netloc.lower() != "www.lootlemon.com":
            return
        clean_url = f"https://www.lootlemon.com{parsed.path.rstrip('/')}"
        lower_url = clean_url.lower()
        if any(x in lower_url for x in ("/about", "/contact", "/privacy", "/builds", "/calculator", "/credits", "/support")):
            return

        ok = False

        # New/direct Lootlemon BL4 item pages, e.g. /grenade-mod/atling-gun-bl4.
        if _LOOTLEMON_ITEM_PATH_RE.match(parsed.path):
            ok = True

        # Old behavior: keep detail pages nested under the category page.  This is
        # required for categories whose item URLs are emitted as
        # /db/borderlands-4/repkits/<slug> or /db/borderlands-4/enhancements/<slug>.
        if category_url and lower_url.startswith((category_url + "/").lower()):
            ok = True

        # Old behavior: accept known item marker paths that may not match the
        # strict -bl4 route.
        if any(marker in lower_url for marker in legacy_detail_markers):
            ok = True

        if not ok:
            return
        if clean_url not in seen:
            seen.add(clean_url)
            links.append(clean_url)

    # Normal anchors plus URLs embedded in hydrated JSON/script data.
    for href in re.findall(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>", page_html, flags=re.I|re.S):
        add_link(href)
    for raw in re.findall(r"https?://www\.lootlemon\.com/[^\"'<>\s)]+", page_html, flags=re.I):
        add_link(raw)

    # Direct item detail paths.
    for raw in re.findall(r"/(?:weapon|shield|grenade-mod|repkit|rep-kit|class-mod|enhancement)/[^\"'<>\s)]+-bl4/?", page_html, flags=re.I):
        add_link(raw)

    # Category-relative hydrated routes from the old parser.  These brought in
    # Repkits and Enhancements before the strict Ordnance path fix.
    for raw in re.findall(r"/(?:db/)?borderlands-4/[^\"'<>\s)]+", page_html, flags=re.I):
        add_link(raw)

    # Hydrated item objects sometimes provide name/title plus slug instead of an href.
    for m in re.finditer(r"[\"'](?:name|title)[\"']\s*:\s*[\"']([^\"']{2,96})[\"'](?:(?![{}]).){0,300}?[\"']slug[\"']\s*:\s*[\"']([^\"']{2,120})[\"']", page_html, flags=re.I|re.S):
        slug = m.group(2).strip("/")
        add_link(category_url + "/" + slug)
    for m in re.finditer(r"[\"']slug[\"']\s*:\s*[\"']([^\"']{2,120})[\"'](?:(?![{}]).){0,300}?[\"'](?:name|title)[\"']\s*:\s*[\"']([^\"']{2,96})[\"']", page_html, flags=re.I|re.S):
        slug = m.group(1).strip("/")
        add_link(category_url + "/" + slug)

    # Ordnance fallback: names in the rendered table may not be emitted as static hrefs.
    if category_name == "ordnance":
        for u in _lootlemon_extract_ordnance_table_links(page_html):
            add_link(u)

    return links

def _lootlemon_extract_meta(detail_html: str, fallback_name: str, category: str) -> dict[str, str]:
    title = fallback_name
    m = re.search(r"<h1[^>]*>(.*?)</h1>", detail_html, flags=re.I|re.S)
    if m:
        title = _lootlemon_clean_name(m.group(1))
    if title == "Lootlemon Serial":
        m = re.search(r"<title[^>]*>(.*?)</title>", detail_html, flags=re.I|re.S)
        if m:
            title = _lootlemon_clean_name(m.group(1).split("•")[0].split("-")[0])
    rarity = ""
    rm = re.search(r"Rarity\s*</[^>]+>\s*<[^>]+>([^<]+)", detail_html, flags=re.I|re.S)
    if rm:
        rarity = _lootlemon_clean_spaces(rm.group(1))[:48]
    manufacturer = ""
    mm = re.search(r"Manufacturer\s*</[^>]+>\s*<[^>]+>([^<]+)", detail_html, flags=re.I|re.S)
    if mm:
        manufacturer = _lootlemon_clean_spaces(mm.group(1))[:48]
    return {"name": title or fallback_name, "category": category, "rarity": rarity, "manufacturer": manufacturer}


def _lootlemon_extract_codes_from_detail(detail_html: str, url: str, category: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    base_name = url.rstrip('/').split('/')[-1].replace('-', ' ').title()
    meta = _lootlemon_extract_meta(detail_html, base_name, category)
    text = _serial_html_unescape_preserve_numeric_entities(detail_html)
    serials: list[str] = []
    for m in _LOOTLEMON_SERIAL_RE.finditer(text):
        serial = _trim_serial_markup_tail(m.group(0).strip())
        serial = _lootlemon_extend_serial_if_split_by_markup(text, m, serial)
        serial = _lootlemon_repair_known_serial(serial, url, str(meta.get("name") or base_name))
        if not serial.startswith("@U"):
            continue
        if "xxxx" in serial.lower() or len(serial) < 20:
            continue
        if serial not in serials:
            serials.append(serial)
    for i, serial in enumerate(serials):
        name = str(meta.get("name") or base_name)
        # Prefer nearby Copy <Name> Code label when present.
        idx = text.find(serial)
        if idx >= 0:
            near = text[max(0, idx-800):idx+200]
            cm = re.search(r"Copy\s+([^<>{}\n\r]{2,120}?)\s+Code", near, flags=re.I)
            if cm:
                name = _lootlemon_clean_name(cm.group(1))
        if len(serials) > 1:
            name = f"{name} #{i+1}"
        eid = f"lootlemon:{category}:{name}:{i}:{abs(hash(serial))}"
        row = dict(meta)
        row.update({"id": eid, "name": _lootlemon_clean_name(name), "serial": serial, "url": url, "source": "Lootlemon"})
        out.append(row)
    return out


def _lootlemon_load_cache(silent: bool = False) -> bool:
    global _lootlemon_entries, _lootlemon_status, _lootlemon_active_id, _lootlemon_selected_ids, _lootlemon_filter_cache_key, _lootlemon_filter_cache_result, _lootlemon_active_cache_id, _lootlemon_active_cache_entry
    try:
        path = _lootlemon_cache_path_for_read()
        if path is None:
            if not silent:
                _lootlemon_status = "No Lootlemon cache found. Click Load Cache."
            return False
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            version = int(data.get("version", 0) or 0)
            if version and version != _LOOTLEMON_CACHE_VERSION:
                if not silent:
                    _lootlemon_status = "Lootlemon cache version differs from this build. Update the bundled/user local JSON cache."
                return False
            entries = data.get("entries", [])
        else:
            entries = data
        if not isinstance(entries, list):
            raise ValueError("cache did not contain an entries list")
        cleaned: list[dict[str, str]] = []
        seen: set[str] = set()
        for e in entries:
            if not isinstance(e, dict):
                continue
            serial = _lootlemon_repair_known_serial(str(e.get("serial", "")).strip(), str(e.get("url", "")), str(e.get("name", "")))
            if not _lootlemon_is_valid_serial(serial):
                continue
            key = serial
            if key in seen:
                continue
            seen.add(key)
            cleaned.append({
                "id": str(e.get("id") or f"lootlemon:{len(cleaned)}"),
                "name": _lootlemon_clean_name(str(e.get("name", "Lootlemon Serial"))),
                "category": _lootlemon_clean_spaces(str(e.get("category", ""))) or "Lootlemon",
                "rarity": _lootlemon_clean_spaces(str(e.get("rarity", ""))),
                "manufacturer": _lootlemon_clean_spaces(str(e.get("manufacturer", ""))),
                "url": str(e.get("url", "")),
                "source": "Lootlemon",
                "serial": serial,
                "mattmab_validator": str(e.get("mattmab_validator", "") or ""),
                "mattmab_validator_detail": str(e.get("mattmab_validator_detail", "") or ""),
                "mattmab_validator_time": str(e.get("mattmab_validator_time", "") or ""),
            })
        _lootlemon_entries = cleaned
        _lootlemon_filter_cache_key = ()
        _lootlemon_filter_cache_result = []
        _lootlemon_active_cache_id = ""
        _lootlemon_active_cache_entry = None
        ids = {str(e.get("id", "")) for e in cleaned}
        _lootlemon_selected_ids = {eid for eid in _lootlemon_selected_ids if eid in ids}
        if cleaned and _lootlemon_active_id not in ids:
            _lootlemon_active_id = cleaned[0]["id"]
        elif not cleaned:
            _lootlemon_active_id = ""
        # Do not save/sync on load. Opening the Lootlemon tab must never contact
        # lootlemon.com or rewrite the user cache; it only reads local JSON.
        if not silent:
            _lootlemon_status = f"Loaded {len(cleaned)} cached Lootlemon code/link(s) from local JSON: {path}."
        return True
    except Exception as exc:
        if not silent:
            _lootlemon_status = f"Lootlemon cache load failed: {exc}"
        _log(f"Lootlemon cache load failed: {exc!r}")
        return False


def _lootlemon_save_cache(entries: list[dict[str, str]] | None = None) -> bool:
    rows = list(_lootlemon_entries if entries is None else entries)
    payload = {
        "version": _LOOTLEMON_CACHE_VERSION,
        "updated": int(time.time()),
        "source": "Lootlemon BL4",
        "entries": rows,
    }
    paths = _lootlemon_cache_paths_for_write()
    wrote = 0
    for path in paths:
        try:
            _atomic_json_replace(path, payload)
            wrote += 1
        except Exception as exc:
            _log(f"Lootlemon cache save failed for {path}: {exc!r}")
    _remove_tmp_cache_states(paths, "Lootlemon")
    return wrote > 0


def _refresh_progress_text(progress: dict[str, object]) -> str:
    label = str(progress.get("label", "") or "")
    done = int(progress.get("done", 0) or 0)
    total = int(progress.get("total", 0) or 0)
    found = int(progress.get("found", 0) or 0)
    if total > 0:
        return f"{label} ({done}/{total}; {found} serials found)"
    if found:
        return f"{label} ({found} serials found)"
    return label


def _draw_refresh_progress(progress: dict[str, object]) -> None:
    imgui = _blimgui.imgui
    if not bool(progress.get("running", False)):
        return
    done = int(progress.get("done", 0) or 0)
    total = int(progress.get("total", 0) or 0)
    frac = 0.0 if total <= 0 else max(0.0, min(1.0, float(done) / float(total)))
    text = _refresh_progress_text(progress)
    progress_bar = getattr(imgui, "progress_bar", None)
    if callable(progress_bar):
        try:
            progress_bar(frac, (520, 22), text)
            return
        except Exception:
            try:
                progress_bar(frac, text)
                return
            except Exception:
                pass
    imgui.text_wrapped(text)


def _set_lootlemon_refresh_progress(label: str, done: int = 0, total: int = 0, found: int = 0, running: bool = True) -> None:
    with _async_refresh_lock:
        _lootlemon_refresh_progress.update({"running": running, "label": label, "done": int(done), "total": int(total), "found": int(found)})


def _set_gzo_refresh_progress(label: str, done: int = 0, total: int = 0, found: int = 0, running: bool = True) -> None:
    with _async_refresh_lock:
        _gzo_refresh_progress.update({"running": running, "label": label, "done": int(done), "total": int(total), "found": int(found)})


def _lootlemon_scrape_catalog_worker_body() -> list[dict[str, str]]:
    """Compatibility shim: build the Lootlemon catalog from local JSON only."""
    _set_lootlemon_refresh_progress("Lootlemon: loading local cache", 0, 1, len(_lootlemon_entries))
    entries = _lootlemon_local_cache_entries(prefer_user_cache=True)
    _set_lootlemon_refresh_progress("Lootlemon: local cache loaded", 1, 1, len(entries), False)
    return entries


def _lootlemon_refresh_worker() -> None:
    global _lootlemon_refresh_result
    try:
        entries = _lootlemon_scrape_catalog_worker_body()
        result: tuple[list[dict[str, str]] | None, str | None] = (entries, None)
    except Exception as exc:
        result = (None, str(exc))
        _log(f"Lootlemon local cache load failed: {exc!r}")
    with _async_refresh_lock:
        _lootlemon_refresh_result = result


def _lootlemon_refresh_catalog() -> None:
    """Load/reload the local Lootlemon cache. This never contacts lootlemon.com."""
    global _lootlemon_entries, _lootlemon_selected_ids, _lootlemon_last_refresh, _lootlemon_active_id, _lootlemon_status, _lootlemon_filter_cache_key, _lootlemon_filter_cache_result, _lootlemon_active_cache_id, _lootlemon_active_cache_entry
    entries = _lootlemon_local_cache_entries(prefer_user_cache=True)
    _lootlemon_entries = entries
    _lootlemon_filter_cache_key = ()
    _lootlemon_filter_cache_result = []
    _lootlemon_active_cache_id = ""
    _lootlemon_active_cache_entry = None
    _lootlemon_selected_ids.clear()
    _lootlemon_last_refresh = time.time() if entries else 0.0
    _lootlemon_active_id = str(entries[0].get("id", "")) if entries else ""
    if entries:
        _lootlemon_status = f"Loaded {len(entries)} Lootlemon code/link(s) from local cache. Direct Lootlemon scraping is disabled."
    else:
        _lootlemon_status = "No local Lootlemon cache found. Direct Lootlemon scraping is disabled."
    _set_lootlemon_refresh_progress(_lootlemon_status, len(entries), len(entries), len(entries), False)
    _log(_lootlemon_status)

def _poll_lootlemon_refresh_result() -> None:
    global _lootlemon_entries, _lootlemon_status, _lootlemon_last_refresh, _lootlemon_active_id, _lootlemon_selected_ids, _lootlemon_refresh_result, _lootlemon_filter_cache_key, _lootlemon_filter_cache_result, _lootlemon_active_cache_id, _lootlemon_active_cache_entry
    _flush_worker_log_lines()
    with _async_refresh_lock:
        result = _lootlemon_refresh_result
        _lootlemon_refresh_result = None
    if result is None:
        return
    entries, error = result
    if error is not None:
        _lootlemon_status = f"Lootlemon refresh failed: {error}"
        _set_lootlemon_refresh_progress(_lootlemon_status, 0, 0, 0, False)
        return
    all_entries = list(entries or [])
    _lootlemon_entries = all_entries
    _lootlemon_filter_cache_key = ()
    _lootlemon_filter_cache_result = []
    _lootlemon_active_cache_id = ""
    _lootlemon_active_cache_entry = None
    _lootlemon_selected_ids.clear()
    _lootlemon_last_refresh = time.time()
    _lootlemon_active_id = all_entries[0]["id"] if all_entries else ""
    saved = _lootlemon_save_cache(all_entries)
    _lootlemon_status = f"Loaded {'and cached ' if saved else 'but could not cache '}{len(all_entries)} Lootlemon BL4 code(s)."
    _set_lootlemon_refresh_progress(_lootlemon_status, len(all_entries), len(all_entries), len(all_entries), False)
    _log(_lootlemon_status)

def _lootlemon_category_names() -> list[str]:
    return ["All"] + [str(c["name"]) for c in _lootlemon_categories]


_MATTMAB_FILTERS: list[str] = ["All", "Legit", "Modded", "Error", "Unchecked"]


def _mattmab_filter_value(index: int) -> str:
    try:
        return _MATTMAB_FILTERS[max(0, min(int(index), len(_MATTMAB_FILTERS) - 1))]
    except Exception:
        return "All"


def _mattmab_entry_matches_filter(e: dict[str, str], filt: str) -> bool:
    want = str(filt or "All").strip().upper()
    if want == "ALL":
        return True
    status = str(e.get("mattmab_validator", "") or "").strip().upper()
    if want == "UNCHECKED":
        return status not in ("PASS", "FAIL", "ERROR")
    if want == "LEGIT":
        return status == "PASS"
    if want == "MODDED":
        return status == "FAIL"
    return status == want


def _mattmab_quick_filter_buttons(prefix: str, current_index: int) -> int:
    idx = int(current_index or 0)
    for label, value, color, width in (
        ("All Results", "All", "cyan", 115),
        ("Legit", "Legit", "green", 80),
        ("Modded", "Modded", "pink", 90),
        ("Error", "Error", "gold", 75),
        ("?", "Unchecked", "purple", 45),
    ):
        if label != "All Results":
            try:
                _blimgui.imgui.same_line()
            except Exception:
                pass
        if _cyber_button_safe(label + f"###{prefix}_{value.lower()}", color, width, 0):
            try:
                idx = _MATTMAB_FILTERS.index(value)
            except ValueError:
                idx = 0
    return idx



def _lootlemon_filtered_entries() -> list[dict[str, str]]:
    global _lootlemon_filter_cache_key, _lootlemon_filter_cache_result
    query = _lootlemon_search.lower().strip()
    cats = _lootlemon_category_names()
    cat = cats[max(0, min(_lootlemon_category_index, len(cats)-1))]
    matt_filter = _mattmab_filter_value(_lootlemon_mattmab_filter_index)
    key = (id(_lootlemon_entries), len(_lootlemon_entries), query, cat, matt_filter)
    if key == _lootlemon_filter_cache_key:
        return _lootlemon_filter_cache_result
    out: list[dict[str, str]] = []
    for e in _lootlemon_entries:
        if cat != "All" and str(e.get("category", "")) != cat:
            continue
        if not _mattmab_entry_matches_filter(e, matt_filter):
            continue
        hay = " ".join(str(e.get(k, "")) for k in ("name", "category", "rarity", "manufacturer", "serial", "url")).lower()
        if query and query not in hay:
            continue
        out.append(e)
    _lootlemon_filter_cache_key = key
    _lootlemon_filter_cache_result = out
    return out


def _lootlemon_active_entry() -> dict[str, str] | None:
    global _lootlemon_active_cache_id, _lootlemon_active_cache_entry
    key = f"{id(_lootlemon_entries)}:{len(_lootlemon_entries)}:{_lootlemon_active_id}"
    if key == _lootlemon_active_cache_id:
        return _lootlemon_active_cache_entry
    found = None
    for e in _lootlemon_entries:
        if str(e.get("id", "")) == _lootlemon_active_id:
            found = e
            break
    if found is None and _lootlemon_entries:
        found = _lootlemon_entries[0]
    _lootlemon_active_cache_id = key
    _lootlemon_active_cache_entry = found
    return found


def _lootlemon_selected_entries() -> list[dict[str, str]]:
    return [e for e in _lootlemon_entries if str(e.get("id", "")) in _lootlemon_selected_ids]


def _lootlemon_copy_selected_serials() -> None:
    global _lootlemon_status
    entries = _lootlemon_selected_entries()
    if not entries:
        active = _lootlemon_active_entry()
        entries = [active] if active else []
    count = _copy_serial_list_to_clipboard("selected Lootlemon serials", entries)
    _lootlemon_status = f"Copied {count} selected Lootlemon serial(s) to clipboard." if count else "Select one or more Lootlemon serials to copy."


def _lootlemon_select_all_filtered(entries: list[dict[str, str]]) -> None:
    for e in entries:
        eid = str(e.get("id", ""))
        if eid:
            _lootlemon_selected_ids.add(eid)


def _lootlemon_import_selected_to_store() -> None:
    global _lootlemon_status
    _serial_store_load()
    entries = _lootlemon_selected_entries()
    if not entries:
        active = _lootlemon_active_entry()
        entries = [active] if active else []
    existing = {str(e.get("serial", "")).strip() for e in _serial_store_entries}
    added = 0; skipped = 0
    for e in entries:
        if not e:
            continue
        serial = str(e.get("serial", "")).strip()
        if not _lootlemon_is_valid_serial(serial):
            continue
        if serial in existing:
            skipped += 1; continue
        group = "Lootlemon - " + (str(e.get("category", "")) or "BL4")
        _serial_store_entries.append({
            "id": _serial_store_new_id() + f"_{added}",
            "name": _lootlemon_clean_name(str(e.get("name", "Lootlemon Serial"))),
            "group": group,
            "serial": serial,
            "created": str(int(time.time())),
            "updated": str(int(time.time())),
        })
        existing.add(serial); added += 1
    _serial_store_save()
    _lootlemon_status = f"Imported {added} Lootlemon serial(s) to Serial Bookmarks" + (f"; skipped {skipped} duplicate(s)." if skipped else ".")


def _lootlemon_deliver_selected(mode: str = "selected") -> None:
    global _lootlemon_status
    entries = _lootlemon_selected_entries()
    if not entries:
        active = _lootlemon_active_entry()
        entries = [active] if active else []
    serials = [str(e.get("serial", "")).strip() for e in entries if e and _lootlemon_is_valid_serial(str(e.get("serial", "")).strip())]
    if not serials:
        _lootlemon_status = "Select one or more valid Lootlemon serials first."
        return
    serials, changed, error = _serials_with_level_override(serials, _lootlemon_delivery_override_level, _lootlemon_delivery_level)
    if error:
        _lootlemon_status = error
        _log(_lootlemon_status)
        return
    _lootlemon_status = _deliver_serials_with_target(serials, mode, "Lootlemon Codes")
    if changed:
        _lootlemon_status += f" Level override: {changed} serial(s) set to level {_clamp_int(_lootlemon_delivery_level, 1, 60)}."
    _log(f"Lootlemon Codes delivered {len(serials)} serial(s): {_lootlemon_status}")


def _draw_lootlemon_codes_tab() -> None:
    global _lootlemon_search, _lootlemon_category_index, _lootlemon_mattmab_filter_index, _lootlemon_player_index, _lootlemon_active_id, _lootlemon_cache_autoload_attempted, _lootlemon_delivery_override_level, _lootlemon_delivery_level
    imgui = _blimgui.imgui
    opened = _begin_resizable_card("card_lootlemon", "Lootlemon Codes", "gold", _tab_card_height(780.0), 320, 1200) if _cyber else True
    if opened:
        if not _lootlemon_cache_autoload_attempted and not _lootlemon_entries:
            _lootlemon_cache_autoload_attempted = True
            _lootlemon_load_cache(silent=True)
        imgui.text_wrapped("Lootlemon BL4 code catalog")
        _muted_wrapped("Uses only the bundled/user local Lootlemon JSON cache. Direct lootlemon.com scraping is disabled; reload this cache after updating your local server export.")
        _wrapped_button_row([
            ("Load Cache", _lootlemon_load_cache, "cyan", 110, 0),
            ("Reload Local Cache", _lootlemon_refresh_catalog, "gold", 170, 0),
            ("Mattmab Validate", lambda: _catalog_validator_start("Lootlemon"), "green", 160, 0),
            ("Import Selected To Bookmarks", _lootlemon_import_selected_to_store, "purple", 210, 0),
        ])
        _draw_refresh_progress(_lootlemon_refresh_progress)
        _draw_catalog_validator_progress("Lootlemon")
        imgui.separator()
        imgui.text_wrapped("Filters")
        _lootlemon_search = _filter_input("Search", "lootlemon_search", _lootlemon_search, 256, width=420.0)
        def _loot_filter_category():
            global _lootlemon_category_index
            _lootlemon_category_index = _filter_combo("Category", "lootlemon_category", _lootlemon_category_index, _lootlemon_category_names(), width=230.0)
        def _loot_filter_mattmab():
            global _lootlemon_mattmab_filter_index
            _lootlemon_mattmab_filter_index = _filter_combo("Mattmab Result", "lootlemon_mattmab_filter", _lootlemon_mattmab_filter_index, _MATTMAB_FILTERS, width=230.0)
        _filter_field_row([_loot_filter_category, _loot_filter_mattmab])
        _lootlemon_mattmab_filter_index = _mattmab_quick_filter_buttons("lootlemon", _lootlemon_mattmab_filter_index)
        filtered = _lootlemon_filtered_entries()
        imgui.text_wrapped(f"{len(filtered)} shown / {len(_lootlemon_entries)} loaded | {len(_lootlemon_selected_ids)} selected")
        _wrapped_button_row([
            ("Select All", lambda: _lootlemon_select_all_filtered(filtered), "purple", 110, 0),
            ("Clear", lambda: _lootlemon_selected_ids.clear(), "pink", 80, 0),
            ("Copy Selected Serials", _lootlemon_copy_selected_serials, "gold", 185, 0),
        ])
        columns = getattr(imgui, "columns", None); next_column = getattr(imgui, "next_column", None); using_columns = False
        if callable(columns) and callable(next_column):
            try:
                columns(2, "msbt_lootlemon_codes_columns", True); using_columns = True
            except Exception:
                try: columns(2); using_columns = True
                except Exception: using_columns = False
        imgui.text_wrapped("CODES")
        child_open = _begin_child_region("msbt_lootlemon_codes_list", _resizable_height("child_lootlemon_list", "Lootlemon list", 430, 160, 900))
        try:
            if not filtered:
                imgui.text_wrapped("No Lootlemon codes loaded/matching. Add/update the local cache JSON, then click Reload Local Cache. Direct Lootlemon scraping is disabled.")
            visible_filtered = filtered[:240]
            if len(filtered) > len(visible_filtered):
                imgui.text_wrapped(f"Showing first {len(visible_filtered)} row(s); narrow Search/Category for more. Select All still selects all filtered rows.")
            for e in visible_filtered:
                eid = str(e.get("id", "")); checked = "[X]" if eid in _lootlemon_selected_ids else "[ ]"; active = "> " if eid == _lootlemon_active_id else "  "
                meta = " / ".join(x for x in [_mattmab_validator_short(e), str(e.get("category", "")), str(e.get("manufacturer", "")), str(e.get("rarity", ""))] if x)
                label = f"{active}{checked} {e.get('name','Lootlemon Serial')}    {meta}###lootlemon_row_{eid}"
                if _selectable_row(label, eid == _lootlemon_active_id):
                    _lootlemon_active_id = eid
                    if eid in _lootlemon_selected_ids: _lootlemon_selected_ids.discard(eid)
                    else: _lootlemon_selected_ids.add(eid)
        finally:
            if child_open: _end_child_region()
        if using_columns: next_column()
        imgui.text_wrapped("DETAILS")
        active = _lootlemon_active_entry()
        if active:
            imgui.text_wrapped(str(active.get("name", "Lootlemon Serial")))
            _muted_wrapped(" | ".join(x for x in [_mattmab_validator_label(active), str(active.get("category", "")), str(active.get("manufacturer", "")), str(active.get("rarity", "")), str(active.get("url", ""))] if x))
            detail = str(active.get("mattmab_validator_detail", "") or "")
            if detail:
                _muted_wrapped(detail)
            _input_text_multiline("Serial###lootlemon_active_serial", str(active.get("serial", "")), 65536, width=int(_fit_width(620, 24, 220)), height=130)
            imgui.separator()
            imgui.text_wrapped("Parts Breakdown")
            parts_text = _serial_parts_breakdown_for_value_cached(str(active.get("serial", "")))
            _input_text_multiline("###lootlemon_active_parts_breakdown", parts_text, 65536, width=int(_fit_width(620, 24, 220)), height=120)
            _button("Copy Parts Breakdown", lambda: _copy_text_to_clipboard("Lootlemon parts breakdown", _serial_parts_breakdown_for_value_cached(str(active.get("serial", "")))), "purple", 190, 0)
            imgui.same_line()
            _button("Copy Serial", lambda: _copy_text_to_clipboard("Lootlemon serial", str(active.get("serial", ""))), "purple", 130, 0)
            imgui.same_line(); _button("Open Item Page", lambda: _lootlemon_open_url(str(active.get("url", ""))), "gold", 150, 0)
            imgui.same_line(); _button("Open Link", lambda: _lootlemon_open_url(str(active.get("url", ""))), "purple", 110, 0)
            imgui.same_line(); _button("Bookmark This", lambda: (_lootlemon_selected_ids.add(str(active.get("id", ""))), _lootlemon_import_selected_to_store()), "cyan", 120, 0)
        else:
            imgui.text_wrapped("Select a Lootlemon code to preview its serial.")
        if using_columns:
            try: columns(1)
            except Exception: pass
        imgui.separator()
        _draw_inline_target_selector("Lootlemon Target")
        _lootlemon_delivery_override_level, _lootlemon_delivery_level = _draw_catalog_level_override("lootlemon", _lootlemon_delivery_override_level, _lootlemon_delivery_level)
        imgui.text_wrapped(f"{len(_lootlemon_selected_ids)} selected | Delivery uses GiveRewardAllPlayers, then patches requested target(s)")
        _wrapped_button_row([
            ("Deliver Selected", lambda: _lootlemon_deliver_selected("selected"), "purple", 165, 0),
            ("Deliver All", lambda: _lootlemon_deliver_selected("all"), "gold", 135, 0),
            ("Deliver Non-Host", lambda: _lootlemon_deliver_selected("nonhost"), "cyan", 185, 0),
        ])
        _lootlemon_preview_entries = _lootlemon_selected_entries() or ([active] if active else [])
        _lootlemon_preview_serials = [str(e.get("serial", "")).strip() for e in _lootlemon_preview_entries if e and str(e.get("serial", "")).strip()]
        if _lootlemon_delivery_override_level:
            _lootlemon_preview_serials, _ll_preview_changed, _ll_preview_error = _serials_with_level_override(_lootlemon_preview_serials, _lootlemon_delivery_override_level, _lootlemon_delivery_level)
        _draw_serial_delivery_split_controls(_lootlemon_preview_serials, "Lootlemon Codes")
        imgui.text_wrapped(_lootlemon_status)
    if _cyber:
        _end_resizable_card()

_GZO_LISTING_FILTERS = ["All", "Legit", "Modded", "Lootlemon"]
_GZO_CACHE_VERSION = 4
_GZO_CACHE_FILE_NAME = "MattsSDKBoostingTools_gzo_codes.json"
_GZO_BAD_TEXT_TOKENS = (
    "<textarea", "</textarea", "<script", "</script", "const ", "function(",
    "base85.search", "discordurl", "creator\":", "rarity\":", "tacklebox",
    "placeholder=", "submit-base85", "json.parse", "autoUps", "document.",
    "data-", "class=", "id=", "textarea", "script", "onclick", "function",
    "{\"", "\":\"", "\",\"",
)
_GZO_SERIAL_RE = re.compile(r"@U[0-9A-Za-z!#$%&()*+\-;<=>?@^_`{/}~]{12,}")


def _gzo_url_join(base: str, url: str) -> str:
    try:
        return urllib.parse.urljoin(base, str(url or ""))
    except Exception:
        return str(url or "")


def _gzo_fetch_text(url: str, timeout: float = 12.0) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "MattsSDKBoostingTools/1.0 (+BL4 GZO Codes tab)",
            "Accept": "text/html,application/json,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(4_000_000)
    return raw.decode("utf-8", "replace")


def _gzo_entry_id(entry: dict[str, str]) -> str:
    base = "|".join(str(entry.get(k, "")) for k in ("name", "serial", "listing", "source"))
    return str(abs(hash(base)))


def _gzo_cache_candidate_paths() -> list[Path]:
    # Single canonical GZO cache only.
    return [_msbt_cache_path(_GZO_CACHE_FILE_NAME)]

def _gzo_cache_score(path: Path) -> tuple[int, int, int]:
    try:
        if not path.exists():
            return (-1, -1, -1)
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        if not isinstance(payload, dict) or int(payload.get("version", 0) or 0) != _GZO_CACHE_VERSION:
            return (-1, -1, -1)
        entries = payload.get("entries", [])
        if not isinstance(entries, list):
            return (-1, -1, -1)
        valid = 0
        for raw in entries:
            if isinstance(raw, dict) and _gzo_normalize_cached_entry(raw):
                valid += 1
        updated = int(float(payload.get("updated", 0) or 0))
        mtime = int(path.stat().st_mtime)
        return (valid, updated, mtime)
    except Exception:
        return (-1, -1, -1)


def _gzo_cache_path_for_read() -> Path | None:
    path = _msbt_cache_path(_GZO_CACHE_FILE_NAME)
    try:
        return path if _gzo_cache_score(path)[0] >= 0 else None
    except Exception:
        return None


def _gzo_cache_paths_for_write() -> list[Path]:
    path = _msbt_cache_path(_GZO_CACHE_FILE_NAME)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return [path]

def _gzo_cache_path_for_write() -> Path:
    return _gzo_cache_paths_for_write()[0]


def _gzo_normalize_cached_entry(e: dict) -> dict[str, str] | None:
    try:
        serial = str(e.get("serial", "")).strip()
        if not _gzo_is_valid_serial(serial):
            return None
        row = {
            "id": "",
            "name": _gzo_clean_name(str(e.get("name", "GZO Serial"))) or "GZO Serial",
            "serial": serial,
            "listing": _gzo_ascii(str(e.get("listing", "GZO")) or "GZO"),
            "type": _gzo_ascii(str(e.get("type", ""))),
            "rarity": _gzo_ascii(str(e.get("rarity", ""))),
            "manufacturer": _gzo_ascii(str(e.get("manufacturer", ""))),
            "creator": _gzo_ascii(str(e.get("creator", ""))),
            "character_class": _gzo_ascii(str(e.get("character_class", ""))),
            "tags": _gzo_ascii(str(e.get("tags", ""))),
            "extra_tags": _gzo_ascii(str(e.get("extra_tags", ""))),
            "source": _gzo_ascii(str(e.get("source", "GZO Cache")) or "GZO Cache"),
            "mattmab_validator": _gzo_ascii(str(e.get("mattmab_validator", "") or "")),
            "mattmab_validator_detail": _gzo_ascii(str(e.get("mattmab_validator_detail", "") or "")),
            "mattmab_validator_time": _gzo_ascii(str(e.get("mattmab_validator_time", "") or "")),
            "lootlemon_url": str(e.get("lootlemon_url", "") or "").strip(),
            "lootlemon_name": _gzo_ascii(str(e.get("lootlemon_name", "") or "")),
            "lootlemon_category": _gzo_ascii(str(e.get("lootlemon_category", "") or "")),
            "lootlemon_rarity": _gzo_ascii(str(e.get("lootlemon_rarity", "") or "")),
            "lootlemon_manufacturer": _gzo_ascii(str(e.get("lootlemon_manufacturer", "") or "")),
        }
        if _gzo_has_bad_text(" ".join(str(row.get(k, "")) for k in ("name", "type", "rarity", "manufacturer", "creator", "tags"))):
            return None
        row["id"] = _gzo_entry_id(row)
        return row
    except Exception:
        return None


def _gzo_load_cache(silent: bool = False) -> bool:
    global _gzo_entries, _gzo_selected_ids, _gzo_active_id, _gzo_status, _gzo_last_refresh
    try:
        path = _gzo_cache_path_for_read()
        if path is None:
            if not silent:
                _gzo_status = "No BL4 Codes cache found. Click Refresh GZO or Reload Lootlemon Cache."
            return False
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        if not isinstance(payload, dict) or int(payload.get("version", 0) or 0) != _GZO_CACHE_VERSION:
            if not silent:
                _gzo_status = "GZO cache is from an older parser. Click Refresh GZO to rebuild it."
            return False
        entries = payload.get("entries", [])
        if not isinstance(entries, list):
            raise ValueError("cache did not contain an entries list")
        cleaned: list[dict[str, str]] = []
        seen: set[str] = set()
        for raw in entries:
            if not isinstance(raw, dict):
                continue
            row = _gzo_normalize_cached_entry(raw)
            if not row:
                continue
            serial = row.get("serial", "")
            if serial in seen:
                continue
            seen.add(serial)
            cleaned.append(row)
        cleaned, _removed_local = _gzo_strip_previous_lootlemon_local_rows(cleaned)
        cleaned, _appended_local, _local_count = _gzo_merge_lootlemon_local_rows(cleaned)
        cleaned, _removed_replaced = _gzo_prune_replaced_serial_rows(cleaned)
        _gzo_entries = cleaned
        _gzo_clear_view_caches()
        ids = {str(e.get("id", "")) for e in cleaned}
        _gzo_selected_ids = {eid for eid in _gzo_selected_ids if eid in ids}
        if cleaned and (_gzo_active_id not in ids):
            _gzo_active_id = str(cleaned[0].get("id", ""))
        elif not cleaned:
            _gzo_active_id = ""
        try:
            _gzo_last_refresh = float(payload.get("updated", 0)) if isinstance(payload, dict) else 0.0
        except Exception:
            _gzo_last_refresh = 0.0
        extra_bits = []
        if _removed_local:
            extra_bits.append(f"cleared {_removed_local} stale local row(s)")
        if _removed_replaced:
            extra_bits.append(f"removed {_removed_replaced} replaced bad row(s)")
        suffix = ("; " + ", ".join(extra_bits)) if extra_bits else ""
        _gzo_status = f"Loaded {len(cleaned)} merged BL4 code(s) from cache/local Lootlemon JSON{suffix}."
        return bool(cleaned)
    except Exception as exc:
        if not silent:
            _gzo_status = f"GZO cache load failed: {exc}"
        _log(f"GZO cache load failed: {exc!r}")
        return False


def _gzo_save_cache(entries: list[dict[str, str]] | None = None) -> bool:
    rows = list(_gzo_entries if entries is None else entries)
    payload = {
        "version": _GZO_CACHE_VERSION,
        "updated": int(time.time()),
        "source": "GZO BL4",
        "entries": rows,
    }
    paths = _gzo_cache_paths_for_write()
    wrote = 0
    for path in paths:
        try:
            _atomic_json_replace(path, payload)
            wrote += 1
        except Exception as exc:
            _log(f"GZO cache save failed for {path}: {exc!r}")
    _remove_tmp_cache_states(paths, "GZO")
    return wrote > 0


def _gzo_ascii(text: str) -> str:
    """Return UI-safe ASCII text. BLImGui font often renders unicode glyphs as question blocks."""
    try:
        text = html.unescape(str(text or ""))
    except Exception:
        text = str(text or "")
    replacements = {
        "–": "-", "—": "-", "’": "'", "‘": "'", "“": '"', "”": '"',
        "…": "...", "X": "X", "✔": "X", "X": "X", "✕": "X", ">": ">",
        "▷": ">", "*": "*", "◇": "*", "*": "*", "*": "*", "[X]": "[X]", "[ ]": "[ ]",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.encode("ascii", "ignore").decode("ascii")


def _gzo_has_bad_text(text: str) -> bool:
    low = str(text or "").lower()
    return any(tok.lower() in low for tok in _GZO_BAD_TEXT_TOKENS)


def _gzo_is_valid_serial(serial: str) -> bool:
    serial = str(serial or "").strip()
    if not _GZO_SERIAL_RE.fullmatch(serial):
        return False
    # Reject placeholder/demo serials like @Ugxxxxxxxxxxxxx.
    tail = serial[2:].lower()
    if len(set(tail)) <= 2 and ("x" in tail or "0" in tail):
        return False
    return True


def _gzo_clean_name(text: str) -> str:
    text = _gzo_ascii(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -:\t\r\n,.")
    if _gzo_has_bad_text(text) or not text:
        return "GZO Serial"
    # Do not let HTML/JSON fragments become visible rows.
    if re.search(r'[{}<>]|[A-Za-z0-9_]+\s*[:=]\s*["\']', text):
        return "GZO Serial"
    if text.count('"') >= 2 or text.count(',') >= 4:
        return "GZO Serial"
    return text[:96]


def _gzo_json_value(context: str, *keys: str) -> str:
    for key in keys:
        # JSON property near the serial. Allows escaped characters but keeps it simple/safe.
        m = re.search(r'["\']' + re.escape(key) + r'["\']\s*:\s*["\']((?:\\.|[^"\']){1,180})["\']', context, re.I | re.S)
        if m:
            try:
                return _gzo_ascii(json.loads('"' + m.group(1).replace('"', '\"') + '"'))
            except Exception:
                return _gzo_ascii(m.group(1))
    return ""


def _gzo_get_serial_field(obj: dict, *keys: str) -> str:
    """Case-insensitive JSON field helper for Base85 strings without numeric-entity damage."""
    if not isinstance(obj, dict):
        return ""
    lower_map = {str(k).lower(): v for k, v in obj.items()}
    for key in keys:
        val = obj.get(key)
        if val is None:
            val = lower_map.get(str(key).lower())
        if val is not None and not isinstance(val, (dict, list)):
            return _serial_html_unescape_preserve_numeric_entities(str(val)).strip()
    return ""


def _gzo_get_field(obj: dict, *keys: str) -> str:
    """Case-insensitive JSON field helper for the GZO catalog payloads."""
    if not isinstance(obj, dict):
        return ""
    lower_map = {str(k).lower(): v for k, v in obj.items()}
    for key in keys:
        val = obj.get(key)
        if val is None:
            val = lower_map.get(str(key).lower())
        if val is not None and not isinstance(val, (dict, list)):
            return _gzo_ascii(str(val))
    return ""


def _gzo_normalize_listing(*values: str) -> str:
    """Only classify listing as Legit or Modded; do not use item category/type here."""
    joined = " ".join(str(v or "") for v in values).lower()
    # Check Modded first so 'non-legit' never becomes Legit.
    if "modded" in joined or "non-legit" in joined or "nonlegit" in joined or "/modded/" in joined or "listing=modded" in joined:
        return "Modded"
    if "legit" in joined or "/legit/" in joined or "listing=legit" in joined:
        return "Legit"
    return "GZO"


def _gzo_context_listing(source: str, context: str, fallback: str = "") -> str:
    return _gzo_normalize_listing(source, context, fallback)



_GZO_MANUFACTURER_ALIASES = {
    "order": "Order", "jakobs": "Jakobs", "vladof": "Vladof", "ripper": "Ripper", "tediore": "Tediore",
    "torgue": "Torgue", "maliwan": "Maliwan", "daedalus": "Daedalus", "deadlus": "Daedalus",
    "atlas": "Atlas", "hyperion": "Hyperion", "cov": "CoV", "co v": "CoV",
}
_GZO_TYPE_ALIASES = {
    "shield": "Shield", "classmod": "Classmod", "class mod": "Classmod", "class_mod": "Classmod",
    "weapon": "Weapon", "grenade": "Grenade", "gadget": "Gadget", "repkit": "Repkit", "repair kit": "Repkit", "repair_kit": "Repkit",
    "enhancement": "Enhancement", "pistol": "Pistol", "shotgun": "Shotgun", "smg": "SMG", "sniper": "Sniper",
    "assault rifle": "Assault Rifle", "assault_rifle": "Assault Rifle", "assault riffle": "Assault Rifle", "assault_riffle": "Assault Rifle",
    "heavy": "Heavy Weapon", "heavy weapon": "Heavy Weapon",
}
_GZO_RARITY_ALIASES = {"common": "Common", "rare": "Rare", "epic": "Epic", "legendary": "Legendary", "legendr": "Legendary", "legendär": "Legendary", "pearl": "Pearl", "pearlescent": "Pearl", "modded": "Modded"}
_GZO_CLASS_ALIASES = {"siren": "Siren", "paladin": "Paladin", "forgeknight": "Paladin", "gravitar": "Gravitar", "exo soldier": "Exo Soldier", "exo_soldier": "Exo Soldier", "ai": "AI", "c4sh": "C4SH"}


def _gzo_norm_key(text: str) -> str:
    text = html.unescape(str(text or "")).strip().lower()
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def _gzo_tag_values(obj: dict) -> list[str]:
    vals: list[str] = []
    if not isinstance(obj, dict):
        return vals
    for key in ("category", "type", "rarity", "manufacturer", "maker"):
        val = obj.get(key)
        if val is not None and not isinstance(val, (dict, list)):
            vals.append(str(val))
    for key in ("tags", "tag", "labels"):
        val = obj.get(key)
        if isinstance(val, list):
            vals.extend(str(x) for x in val if x is not None and not isinstance(x, (dict, list)))
        elif val is not None and not isinstance(val, dict):
            vals.extend(x.strip() for x in re.split(r"[,|;/]+", str(val)) if x.strip())
    out: list[str] = []
    seen: set[str] = set()
    for v in vals:
        v = _gzo_ascii(str(v)).strip()
        if not v:
            continue
        k = _gzo_norm_key(v)
        if k not in seen:
            seen.add(k); out.append(v)
    return out


def _gzo_classify_tags(tags: list[str]) -> dict[str, str]:
    info = {"manufacturer": "", "type": "", "rarity": "", "character_class": "", "extra_tags": "", "tags": ""}
    extra: list[str] = []
    normalized: list[str] = []
    for raw in tags:
        key = _gzo_norm_key(raw)
        if not key:
            continue
        if key in _GZO_MANUFACTURER_ALIASES:
            val = _GZO_MANUFACTURER_ALIASES[key]
            info["manufacturer"] = info["manufacturer"] or val
            normalized.append(val)
        elif key in _GZO_TYPE_ALIASES:
            val = _GZO_TYPE_ALIASES[key]
            info["type"] = info["type"] or val
            normalized.append(val)
        elif key in _GZO_RARITY_ALIASES:
            val = _GZO_RARITY_ALIASES[key]
            info["rarity"] = info["rarity"] or val
            normalized.append(val)
        elif key in _GZO_CLASS_ALIASES:
            val = _GZO_CLASS_ALIASES[key]
            info["character_class"] = info["character_class"] or val
            normalized.append(val)
        else:
            clean = _gzo_ascii(str(raw)).strip()
            if clean:
                extra.append(clean); normalized.append(clean)
    info["extra_tags"] = ", ".join(extra)
    info["tags"] = ", ".join(normalized)
    return info


def _gzo_is_lootlemon_authored(e: dict[str, str]) -> bool:
    vals = [str(e.get(k, "") or "").strip().lower() for k in ("creator", "source", "tags", "extra_tags")]
    return any(v == "lootlemon" or "lootlemon" in v for v in vals)


def _gzo_clear_view_caches() -> None:
    global _gzo_filter_options_cache_key, _gzo_filter_options_cache, _gzo_filter_cache_key, _gzo_filter_cache_result, _gzo_active_cache_id, _gzo_active_cache_entry
    _gzo_filter_options_cache_key = ()
    _gzo_filter_options_cache = {}
    _gzo_filter_cache_key = ()
    _gzo_filter_cache_result = []
    _gzo_active_cache_id = ""
    _gzo_active_cache_entry = None


def _gzo_item_identity_key(e: dict[str, str]) -> tuple[str, str, str, str, str]:
    """Stable item identity for cache replacement cleanup.

    Serials can change when a creator replaces a bad code.  The old GZO cache
    only deduped by serial, so the old bad serial stayed beside the new serial.
    This key intentionally ignores the serial and uses catalog identity fields.
    """
    def norm(v: object) -> str:
        text = _gzo_ascii(str(v or "")).strip().lower()
        text = re.sub(r"\[[^\]]+\]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text
    return (
        norm(e.get("name", "")),
        norm(e.get("type", "") or e.get("lootlemon_category", "")),
        norm(e.get("manufacturer", "") or e.get("lootlemon_manufacturer", "")),
        norm(e.get("rarity", "") or e.get("lootlemon_rarity", "")),
        norm(e.get("creator", "")),
    )


def _gzo_validator_rank(e: dict[str, str]) -> int:
    status = str(e.get("mattmab_validator", "") or "").strip().upper()
    detail = str(e.get("mattmab_validator_detail", "") or "").strip().lower()
    if status == "PASS":
        return 40
    if status in ("", "UNCHECKED", "UNKNOWN"):
        return 30
    if status == "FAIL":
        return 20
    if status == "ERROR" or "validation error" in detail or "unknown part" in detail:
        return 0
    return 10


def _gzo_is_previous_local_lootlemon_row(e: dict[str, str]) -> bool:
    source = str(e.get("source", "") or "").strip().lower()
    tags = str(e.get("tags", "") or "").strip().lower()
    return source == "local lootlemon cache" or ("local cache" in tags and _gzo_is_lootlemon_authored(e))


def _gzo_strip_previous_lootlemon_local_rows(entries: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    kept: list[dict[str, str]] = []
    removed = 0
    for e in entries:
        if _gzo_is_previous_local_lootlemon_row(e):
            removed += 1
            continue
        kept.append(e)
    return kept, removed


def _gzo_prune_replaced_serial_rows(entries: list[dict[str, str]]) -> tuple[list[dict[str, str]], int]:
    """Drop stale bad serial rows when the same logical item has a better row.

    Keep exact serial dedupe separate.  This only removes lower-ranked rows for
    the same item identity when a PASS/unchecked/replacement row exists, which
    fixes creator replacement cases like old Mattmab ERROR serials lingering
    after a new valid code is loaded.
    """
    groups: dict[tuple[str, str, str, str, str], list[dict[str, str]]] = {}
    for e in entries:
        key = _gzo_item_identity_key(e)
        # Need at least a name and one classifying field; otherwise leave it alone.
        if not key[0] or not any(key[1:]):
            continue
        groups.setdefault(key, []).append(e)

    drop_ids: set[int] = set()
    for key, rows in groups.items():
        if len(rows) < 2:
            continue
        best = max(_gzo_validator_rank(r) for r in rows)
        if best <= 0:
            continue
        for r in rows:
            rank = _gzo_validator_rank(r)
            # Be conservative: only drop rows that are clearly worse, especially ERROR rows.
            if rank < best and (rank <= 0 or best >= 30):
                drop_ids.add(id(r))

    if not drop_ids:
        return entries, 0
    return [e for e in entries if id(e) not in drop_ids], len(drop_ids)


def _gzo_merge_lootlemon_links(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    """Attach Lootlemon links to GZO rows by serial, but only for Lootlemon-authored rows."""
    try:
        ll_by_serial = _lootlemon_serial_link_index()
    except Exception as exc:
        _log(f"GZO/Lootlemon local link merge skipped: {exc!r}")
        return entries
    if not ll_by_serial:
        return entries
    matched = 0
    for e in entries:
        serial = str(e.get("serial", "")).strip()
        ll = ll_by_serial.get(serial)
        if not ll or not _gzo_is_lootlemon_authored(e):
            continue
        e["lootlemon_url"] = str(ll.get("url", "")).strip()
        e["lootlemon_name"] = str(ll.get("name", "")).strip()
        e["lootlemon_category"] = str(ll.get("category", "")).strip()
        e["lootlemon_rarity"] = str(ll.get("rarity", "")).strip()
        e["lootlemon_manufacturer"] = str(ll.get("manufacturer", "")).strip()
        matched += 1
    if matched:
        _log(f"GZO local merge attached {matched} Lootlemon link(s) by serial.")
    return entries


def _gzo_row_from_lootlemon_cache_entry(ll: dict[str, str]) -> dict[str, str] | None:
    """Convert a local Lootlemon cache row into the merged BL4 Codes row shape."""
    try:
        serial = str(ll.get("serial", "")).strip()
        if not _gzo_is_valid_serial(serial):
            return None
        category = _gzo_ascii(str(ll.get("category", "") or "Lootlemon")).strip()
        rarity = _gzo_ascii(str(ll.get("rarity", "") or "")).strip()
        manufacturer = _gzo_ascii(str(ll.get("manufacturer", "") or "")).strip()
        name = _gzo_clean_name(str(ll.get("name", "Lootlemon Serial") or "Lootlemon Serial")) or "Lootlemon Serial"
        row = {
            "id": "",
            "name": name,
            "serial": serial,
            "listing": "Lootlemon",
            "type": category,
            "rarity": rarity,
            "manufacturer": manufacturer,
            "creator": "Lootlemon",
            "character_class": "",
            "tags": "Lootlemon, Local Cache",
            "extra_tags": category,
            "source": "Local Lootlemon Cache",
            "mattmab_validator": _gzo_ascii(str(ll.get("mattmab_validator", "") or "")),
            "mattmab_validator_detail": _gzo_ascii(str(ll.get("mattmab_validator_detail", "") or "")),
            "mattmab_validator_time": _gzo_ascii(str(ll.get("mattmab_validator_time", "") or "")),
            "lootlemon_url": str(ll.get("url", "") or "").strip(),
            "lootlemon_name": name,
            "lootlemon_category": category,
            "lootlemon_rarity": rarity,
            "lootlemon_manufacturer": manufacturer,
        }
        row["id"] = _gzo_entry_id(row)
        return row
    except Exception:
        return None


def _gzo_merge_lootlemon_local_rows(entries: list[dict[str, str]]) -> tuple[list[dict[str, str]], int, int]:
    """Merge local Lootlemon cache into the single BL4 Codes catalog without probing Lootlemon."""
    entries, _removed_previous_local = _gzo_strip_previous_lootlemon_local_rows(entries)
    _gzo_merge_lootlemon_links(entries)
    try:
        local_rows = _lootlemon_local_cache_entries(prefer_user_cache=True)
    except Exception as exc:
        _log(f"GZO/Lootlemon local row merge skipped: {exc!r}")
        return entries, 0, 0
    existing = {str(e.get("serial", "")).strip() for e in entries if str(e.get("serial", "")).strip()}
    appended = 0
    for ll in local_rows:
        serial = str(ll.get("serial", "")).strip()
        if not serial or serial in existing:
            continue
        row = _gzo_row_from_lootlemon_cache_entry(ll)
        if not row:
            continue
        entries.append(row)
        existing.add(serial)
        appended += 1
    if appended:
        _log(f"Merged {appended} local-only Lootlemon code(s) into BL4 Codes.")
    return entries, appended, len(local_rows)

def _gzo_meta_label(e: dict[str, str]) -> str:
    parts = []
    for key, title in (("listing", "Listing"), ("type", "Type"), ("manufacturer", "Manufacturer"), ("rarity", "Rarity"), ("creator", "Creator"), ("character_class", "Class"), ("tags", "Tags"), ("extra_tags", "Extra"), ("lootlemon_url", "Lootlemon")):
        val = _gzo_ascii(str(e.get(key, ""))).strip()
        if val and val != "GZO":
            parts.append(f"{title}: {val}")
    return " | ".join(parts)


def _gzo_add_entry(out: list[dict[str, str]], seen: set[str], name: str, serial: str, listing: str = "", item_type: str = "", rarity: str = "", maker: str = "", creator: str = "", source: str = "", tags: str = "", character_class: str = "", extra_tags: str = "") -> None:
    serial = str(serial or "").strip()
    if not _gzo_is_valid_serial(serial):
        return
    name = _gzo_clean_name(name)
    if _gzo_has_bad_text(name):
        name = "GZO Serial"
    listing = _gzo_normalize_listing(source, listing)
    if listing == "GZO":
        listing = _gzo_ascii(str(listing or "").strip() or "GZO")
    row_data = {
        "name": name,
        "serial": serial,
        "listing": listing,
        "type": _gzo_ascii(str(item_type or "").strip()),
        "rarity": _gzo_ascii(str(rarity or "").strip()),
        "manufacturer": _gzo_ascii(str(maker or "").strip()),
        "creator": _gzo_ascii(str(creator or "").strip()),
        "character_class": _gzo_ascii(str(character_class or "").strip()),
        "tags": _gzo_ascii(str(tags or "").strip()),
        "extra_tags": _gzo_ascii(str(extra_tags or "").strip()),
        "source": _gzo_ascii(str(source or "").strip()),
        "lootlemon_url": "",
        "lootlemon_name": "",
        "lootlemon_category": "",
        "lootlemon_rarity": "",
        "lootlemon_manufacturer": "",
    }
    if serial in seen:
        for row in out:
            if str(row.get("serial", "")).strip() == serial:
                for key, val in row_data.items():
                    val = _gzo_ascii(str(val or "")).strip()
                    old = _gzo_ascii(str(row.get(key, ""))).strip()
                    if val and (not old or old == "GZO" or old == "GZO Serial"):
                        row[key] = val
                break
        return
    seen.add(serial)
    row_data["id"] = ""
    out.append(row_data)


def _gzo_walk_json(obj, out: list[dict[str, str]], seen: set[str], source: str, inherited_listing: str = "") -> None:
    if isinstance(obj, dict):
        raw_listing = _gzo_get_field(obj, "targetListing", "listing", "destination", "bucket", "folder", "legitOrModded", "list")
        listing = _gzo_normalize_listing(source, inherited_listing, raw_listing, _gzo_get_field(obj, "txtPath", "path"))
        serial = _gzo_get_serial_field(obj, "base85", "Base85", "serial", "code", "value")
        if isinstance(serial, str) and _gzo_is_valid_serial(serial):
            name = _gzo_get_field(obj, "name", "displayName", "title", "itemName") or "GZO Serial"
            tags_list = _gzo_tag_values(obj)
            classified = _gzo_classify_tags(tags_list)
            item_type = classified.get("type", "")
            rarity = classified.get("rarity", "")
            maker = classified.get("manufacturer", "")
            character_class = classified.get("character_class", "")
            creator = _gzo_get_field(obj, "creator", "author", "creatorName", "owner")
            # Only use deserialized typeID as a narrow fallback for type/class, never as a manufacturer fallback.
            if (not item_type or not character_class) and _gzo_get_field(obj, "deserialized"):
                dm = re.match(r"\s*(\d+)\s*,", _gzo_get_field(obj, "deserialized"))
                if dm:
                    ti = _gzo_type_info_from_id(int(dm.group(1)))
                    if not item_type and ti.get("type"):
                        item_type = ti["type"]
                    if not character_class and ti.get("character_class"):
                        character_class = ti["character_class"]
            _gzo_add_entry(out, seen, str(name), serial, listing, item_type, rarity, maker, creator, source, classified.get("tags", ""), character_class, classified.get("extra_tags", ""))
        for v in obj.values():
            _gzo_walk_json(v, out, seen, source, listing)
    elif isinstance(obj, list):
        for v in obj:
            _gzo_walk_json(v, out, seen, source, inherited_listing)


def _gzo_parse_embedded_json(text: str, out: list[dict[str, str]], seen: set[str], source: str, listing: str) -> None:
    # Handles pages that embed catalog arrays/objects in JS instead of serving pure JSON.
    for m in re.finditer(r"(?:const|let|var)\s+[A-Za-z0-9_$]*\s*=\s*(\[.*?\]|\{.*?\})\s*;", text, re.S):
        chunk = m.group(1)
        if "@U" not in chunk or len(chunk) > 2_500_000:
            continue
        try:
            _gzo_walk_json(json.loads(chunk), out, seen, source, listing)
        except Exception:
            continue


def _gzo_visible_lines(fragment: str) -> list[str]:
    fragment = re.sub(r"(?i)<br\s*/?>", "\n", fragment)
    fragment = re.sub(r"(?i)</(?:div|p|li|h[1-6]|span|button|article|section|tr|td)\s*>", "\n", fragment)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    fragment = html.unescape(fragment)
    lines = []
    for line in re.split(r"[\r\n]+", fragment):
        line = re.sub(r"\s+", " ", line).strip(" -:\t")
        if line:
            lines.append(line)
    return lines


def _gzo_parse_card_html(text: str, out: list[dict[str, str]], seen: set[str], source: str, fallback_listing: str) -> None:
    """Capture GZO's parent card listing label (LEGIT/MODDED) plus visible metadata."""
    text = _serial_html_unescape_preserve_numeric_entities(text)
    for m in _GZO_SERIAL_RE.finditer(text):
        serial = m.group(0)
        if not _gzo_is_valid_serial(serial):
            continue
        before_start = max(0, m.start() - 9000)
        after_end = min(len(text), m.end() + 2500)
        before = text[before_start:m.start()]
        starts = list(re.finditer(r"(?is)(?:>|\b)(LEGIT|MODDED)(?:<|\b)", before))
        if starts:
            card_start = before_start + starts[-1].start()
            listing = starts[-1].group(1).title()
        else:
            card_start = max(0, m.start() - 2500)
            listing = _gzo_normalize_listing(source, fallback_listing)
        fragment = text[card_start:after_end]
        lines = _gzo_visible_lines(fragment)
        visible_before_serial = []
        for line in lines:
            if serial in line or "@U" in line:
                break
            visible_before_serial.append(line)
        if not visible_before_serial:
            continue
        line_listing = _gzo_normalize_listing(listing, " ".join(visible_before_serial[:3]))
        if line_listing in ("Legit", "Modded"):
            listing = line_listing
        non_label = [ln for ln in visible_before_serial if ln.strip().upper() not in ("LEGIT", "MODDED")]
        name = ""
        rarity = maker = item_type = creator = tags = ""
        for ln in non_label:
            low = ln.lower()
            if low.startswith("by "):
                creator = ln[3:].strip()
                continue
            if ("·" in ln or "|" in ln or " / " in ln) and not serial in ln:
                pieces = [x.strip() for x in re.split(r"\s*(?:·|\||/)\s*", ln) if x.strip()]
                if len(pieces) >= 3:
                    rarity, maker, item_type = pieces[0], pieces[1], pieces[2]
                    continue
            if not name and not _gzo_has_bad_text(ln):
                name = ln
        _gzo_add_entry(out, seen, name or "GZO Serial", serial, listing, item_type, rarity, maker, creator, source, tags)


def _gzo_parse_text(text: str, out: list[dict[str, str]], seen: set[str], source: str, listing: str = "") -> list[str]:
    raw_text = text
    serial_text = _serial_html_unescape_preserve_numeric_entities(text)
    urls: list[str] = []
    for m in re.finditer(r"(?:src|href)=[\"\']([^\"\']+\.(?:js|json|txt|php)(?:\?[^\"\']*)?)[\"\']", raw_text, re.I):
        urls.append(_gzo_url_join(source, m.group(1)))
    for m in re.finditer(r"[\"\']([^\"\']*codes/[^\"\']+\.(?:json|txt|php)(?:\?[^\"\']*)?)[\"\']", raw_text, re.I):
        urls.append(_gzo_url_join(source, m.group(1)))
    try:
        _gzo_walk_json(json.loads(text), out, seen, source, listing)
    except Exception:
        _gzo_parse_embedded_json(text, out, seen, source, listing)
    _gzo_parse_card_html(serial_text, out, seen, source, listing)

    # Last-resort scan, but use JSON/property context and reject HTML/JS noise.
    text = serial_text
    for m in _GZO_SERIAL_RE.finditer(text):
        serial = m.group(0)
        if not _gzo_is_valid_serial(serial):
            continue
        ctx_start = max(0, m.start() - 1800)
        ctx_end = min(len(text), m.end() + 900)
        context = text[ctx_start:ctx_end]
        name = _gzo_json_value(context, "name", "displayName", "title", "itemName")
        item_type = _gzo_json_value(context, "type", "itemType")
        rarity = _gzo_json_value(context, "rarity")
        maker = _gzo_json_value(context, "manufacturer", "maker")
        creator = _gzo_json_value(context, "creator", "author")
        local_listing = _gzo_context_listing(source, context, listing)
        if not name:
            # Plain text fallback: take the nearest clean line before the serial only.
            before = context[:m.start() - ctx_start]
            before = re.sub(r"<[^>]+>", " ", before)
            before = re.sub(r"[@A-Za-z0-9!#$%&()*+\-;<=>?^_`{/}~]{40,}", " ", before)
            bits = [_gzo_clean_name(x) for x in re.split(r"[\r\n|]+", before) if _gzo_clean_name(x)]
            bits = [x for x in bits if not _gzo_has_bad_text(x)]
            name = bits[-1] if bits else "GZO Serial"
        tags = _gzo_json_value(context, "tags", "tag", "notes")
        _gzo_add_entry(out, seen, name, serial, local_listing, item_type, rarity, maker, creator, source, tags)
    return urls


def _gzo_catalog_api_url() -> str:
    """The GZO server exposes a direct JSON catalog endpoint; do not guess/probe endpoints."""
    return _gzo_url_join(_gzo_url, "codes/api.php?action=catalog")


def _gzo_scrape_catalog_worker_body() -> tuple[list[dict[str, str]], list[str]]:
    """Refresh GZO codes from the one supported catalog API endpoint.

    The old implementation guessed many possible JSON/TXT/PHP endpoints and parsed the
    dynamic Codes.html shell. That was slow and brittle. GZO's PHP catalog endpoint
    directly returns the live Legit/Modded JSON with base85 serials, so use only that.
    """
    out: list[dict[str, str]] = []
    seen_serials: set[str] = set()
    errors: list[str] = []
    api_url = _gzo_catalog_api_url()

    _set_gzo_refresh_progress("GZO: fetching catalog API", 0, 1, 0)
    try:
        text = _gzo_fetch_text(api_url, timeout=10.0)
        _set_gzo_refresh_progress("GZO: parsing catalog API", 1, 1, 0)
        _gzo_parse_text(text, out, seen_serials, api_url, "")
    except Exception as exc:
        errors.append(f"catalog API: {exc}")

    _set_gzo_refresh_progress("GZO: validating serials", 1, 1, len(out))
    cleaned: list[dict[str, str]] = []
    cleaned_seen: set[str] = set()
    for e in out:
        serial = str(e.get("serial", "")).strip()
        if not _gzo_is_valid_serial(serial) or serial in cleaned_seen:
            continue
        if _gzo_has_bad_text(" ".join(str(e.get(k, "")) for k in ("name", "type", "rarity", "manufacturer", "creator", "tags"))):
            continue
        e["id"] = _gzo_entry_id(e)
        cleaned.append(e)
        cleaned_seen.add(serial)

    cleaned, _appended_local, _local_count = _gzo_merge_lootlemon_local_rows(cleaned)
    cleaned, _removed_replaced = _gzo_prune_replaced_serial_rows(cleaned)
    _set_gzo_refresh_progress("GZO: exporting merged cache", max(1, len(cleaned)), max(1, len(cleaned)), len(cleaned))
    if not cleaned and not errors:
        errors.append("catalog API returned no valid serials")
    return cleaned, errors


def _gzo_refresh_worker() -> None:
    global _gzo_refresh_result
    try:
        entries, errors = _gzo_scrape_catalog_worker_body()
        result: tuple[list[dict[str, str]] | None, str | None, list[str]] = (entries, None, errors)
    except Exception as exc:
        result = (None, str(exc), [])
        _log(f"GZO background refresh failed: {exc!r}")
    with _async_refresh_lock:
        _gzo_refresh_result = result


def _gzo_refresh_catalog() -> None:
    global _gzo_refresh_thread, _gzo_refresh_result, _gzo_status
    with _async_refresh_lock:
        if _gzo_refresh_thread is not None and _gzo_refresh_thread.is_alive():
            _gzo_status = "GZO refresh is already running in the background..."
            return
        _gzo_refresh_result = None
        _gzo_status = "Refreshing GZO in the background..."
        _set_gzo_refresh_progress("GZO: queued", 0, 0, len(_gzo_entries), True)
        _gzo_refresh_thread = threading.Thread(target=_gzo_refresh_worker, name="MSBT GZO Refresh", daemon=True)
        _gzo_refresh_thread.start()


def _gzo_reload_local_lootlemon_cache() -> None:
    """Re-merge local Lootlemon cache into the visible BL4 Codes tab; never contacts lootlemon.com."""
    global _gzo_entries, _gzo_status, _gzo_active_id, _gzo_filter_cache_key, _gzo_filter_options_cache_key
    if not _gzo_entries:
        _gzo_load_cache(silent=True)
    rows = [dict(e) for e in _gzo_entries]
    rows, removed_local = _gzo_strip_previous_lootlemon_local_rows(rows)
    rows, appended, local_count = _gzo_merge_lootlemon_local_rows(rows)
    rows, removed_replaced = _gzo_prune_replaced_serial_rows(rows)
    _gzo_entries = rows
    if rows and not _gzo_active_id:
        _gzo_active_id = str(rows[0].get("id", ""))
    _gzo_clear_view_caches()
    _gzo_save_cache(rows)
    _gzo_status = f"Reloaded local Lootlemon cache: {local_count} local row(s), {appended} local-only code(s) merged, {removed_local} stale local row(s) cleared, {removed_replaced} replaced bad row(s) removed. Direct lootlemon.com scraping is disabled."
    _log(_gzo_status)


def _poll_gzo_refresh_result() -> None:
    global _gzo_entries, _gzo_status, _gzo_last_refresh, _gzo_active_id, _gzo_selected_ids, _gzo_refresh_result
    _flush_worker_log_lines()
    with _async_refresh_lock:
        result = _gzo_refresh_result
        _gzo_refresh_result = None
    if result is None:
        return
    entries, error, errors = result
    if error is not None:
        _gzo_status = f"GZO refresh failed: {error}"
        _set_gzo_refresh_progress(_gzo_status, 0, 0, 0, False)
        return
    cleaned = list(entries or [])
    cleaned, _removed_replaced = _gzo_prune_replaced_serial_rows(cleaned)
    _gzo_entries = cleaned
    _gzo_clear_view_caches()
    _gzo_selected_ids.clear()
    _gzo_last_refresh = time.time()
    if cleaned:
        _gzo_save_cache()
        _gzo_active_id = str(cleaned[0].get("id", ""))
        _gzo_status = f"Loaded {len(cleaned)} merged BL4 code(s). GZO was refreshed from save-editor.be; local Lootlemon cache rows/links were merged by serial without scraping lootlemon.com."
        _set_gzo_refresh_progress(_gzo_status, len(cleaned), len(cleaned), len(cleaned), False)
    else:
        _gzo_active_id = ""
        _gzo_status = "No valid @U codes found. The site may have changed its catalog endpoint or blocked in-game HTTP. " + ("; ".join(errors) if errors else "")
        _set_gzo_refresh_progress(_gzo_status, 0, 0, 0, False)
    _log(_gzo_status)

def _gzo_filter_options(field: str) -> list[str]:
    global _gzo_filter_options_cache_key, _gzo_filter_options_cache
    key = (id(_gzo_entries), len(_gzo_entries))
    if key != _gzo_filter_options_cache_key:
        cache: dict[str, list[str]] = {}
        for fld in ("type", "manufacturer", "rarity", "creator"):
            vals: set[str] = set()
            for e in _gzo_entries:
                val = _gzo_ascii(str(e.get(fld, ""))).strip()
                if val and val != "GZO":
                    vals.add(val)
            cache[fld] = ["All"] + sorted(vals, key=lambda x: x.lower())
        _gzo_filter_options_cache_key = key
        _gzo_filter_options_cache = cache
    return _gzo_filter_options_cache.get(str(field), ["All"])


def _gzo_filter_value(options: list[str], idx: int) -> str:
    return options[max(0, min(int(idx), len(options) - 1))] if options else "All"


def _gzo_filtered_entries() -> list[dict[str, str]]:
    global _gzo_filter_cache_key, _gzo_filter_cache_result
    filt = _GZO_LISTING_FILTERS[max(0, min(_gzo_listing_index, len(_GZO_LISTING_FILTERS)-1))]
    selected_filters = []
    for field, idx in (("type", _gzo_type_filter_index), ("manufacturer", _gzo_manufacturer_filter_index), ("rarity", _gzo_rarity_filter_index), ("creator", _gzo_creator_filter_index)):
        selected_filters.append((field, _gzo_filter_value(_gzo_filter_options(field), idx)))
    q = (_gzo_search or "").strip().lower()
    matt_filter = _mattmab_filter_value(_gzo_mattmab_filter_index)
    key = (id(_gzo_entries), len(_gzo_entries), filt, tuple(selected_filters), q, matt_filter)
    if key == _gzo_filter_cache_key:
        return _gzo_filter_cache_result
    entries = list(_gzo_entries)
    if filt != "All":
        entries = [e for e in entries if str(e.get("listing", "")).strip().lower() == filt.lower()]
    if matt_filter != "All":
        entries = [e for e in entries if _mattmab_entry_matches_filter(e, matt_filter)]
    for field, val in selected_filters:
        if val != "All":
            entries = [e for e in entries if str(e.get(field, "")).strip().lower() == val.lower()]
    if q:
        entries = [e for e in entries if q in " ".join(str(e.get(k, "")) for k in ("name", "listing", "type", "rarity", "manufacturer", "creator", "character_class", "tags", "extra_tags", "serial")).lower()]
    _gzo_filter_cache_key = key
    _gzo_filter_cache_result = entries
    return entries


def _gzo_active_entry() -> dict[str, str] | None:
    global _gzo_active_cache_id, _gzo_active_cache_entry
    key = f"{id(_gzo_entries)}:{len(_gzo_entries)}:{_gzo_active_id}"
    if key == _gzo_active_cache_id:
        return _gzo_active_cache_entry
    found = None
    for e in _gzo_entries:
        if str(e.get("id", "")) == _gzo_active_id:
            found = e
            break
    if found is None and _gzo_entries:
        found = _gzo_entries[0]
    _gzo_active_cache_id = key
    _gzo_active_cache_entry = found
    return found


def _gzo_selected_entries() -> list[dict[str, str]]:
    return [e for e in _gzo_entries if str(e.get("id", "")) in _gzo_selected_ids]


def _gzo_copy_selected_serials() -> None:
    global _gzo_status
    entries = _gzo_selected_entries()
    if not entries:
        active = _gzo_active_entry()
        entries = [active] if active else []
    count = _copy_serial_list_to_clipboard("selected BL4 serials", entries)
    _gzo_status = f"Copied {count} selected BL4 serial(s) to clipboard." if count else "Select one or more BL4 serials to copy."


def _gzo_select_all_filtered(entries: list[dict[str, str]]) -> None:
    for e in entries:
        eid = str(e.get("id", ""))
        if eid:
            _gzo_selected_ids.add(eid)



def _gzo_import_selected_to_store() -> None:
    """Import selected BL4 Codes entries into Serial Bookmarks without using any non-ASCII UI markers."""
    global _gzo_status, _serial_store_status
    _serial_store_load()
    entries = _gzo_selected_entries()
    if not entries:
        active = _gzo_active_entry()
        entries = [active] if active else []
    valid_entries = []
    existing_serials = {str(e.get("serial", "")).strip() for e in _serial_store_entries}
    for e in entries:
        if not e:
            continue
        serial = str(e.get("serial", "")).strip()
        if not _gzo_is_valid_serial(serial):
            continue
        valid_entries.append(e)
    if not valid_entries:
        _gzo_status = "No selected valid @U BL4 Codes serials to import."
        return
    added = 0
    skipped = 0
    for e in valid_entries:
        serial = str(e.get("serial", "")).strip()
        if serial in existing_serials:
            skipped += 1
            continue
        name = _gzo_clean_name(str(e.get("name", "GZO Serial"))) or "GZO Serial"
        listing = _gzo_ascii(str(e.get("listing", "GZO")) or "GZO")
        rarity = _gzo_ascii(str(e.get("rarity", "")))
        group = "GZO"
        if listing and listing.lower() not in ("gzo", "all"):
            group = "GZO - " + listing
        elif rarity:
            group = "GZO - " + rarity
        _serial_store_entries.append({
            "id": _serial_store_new_id(),
            "name": name,
            "group": group,
            "serial": serial,
        })
        existing_serials.add(serial)
        added += 1
    if added:
        _serial_store_save()
    _gzo_status = f"Imported {added} BL4 Codes serial(s) to Serial Bookmarks" + (f"; skipped {skipped} duplicate(s)." if skipped else ".")
    _serial_store_status = _gzo_status
    _log(_gzo_status)


def _gzo_deliver_selected(mode: str = "selected") -> None:
    """Deliver selected BL4 Codes serials using GiveRewardAllPlayers, then patch requested player package(s)."""
    global _gzo_status
    entries = _gzo_selected_entries()
    if not entries:
        active = _gzo_active_entry()
        entries = [active] if active else []
    serials = []
    for e in entries:
        if not e:
            continue
        serial = str(e.get("serial", "")).strip()
        if _gzo_is_valid_serial(serial):
            serials.append(serial)
    if not serials:
        _gzo_status = "Select one or more valid GZO serials first."
        _log("BL4 Codes: no valid serials selected.")
        return
    serials, changed, error = _serials_with_level_override(serials, _gzo_delivery_override_level, _gzo_delivery_level)
    if error:
        _gzo_status = error
        _log(_gzo_status)
        return
    _gzo_status = _deliver_serials_with_target(serials, mode, "BL4 Codes")
    if changed:
        _gzo_status += f" Level override: {changed} serial(s) set to level {_clamp_int(_gzo_delivery_level, 1, 60)}."
    _log(f"BL4 Codes delivered {len(serials)} serial(s): {_gzo_status}")

def _draw_gzo_codes_tab() -> None:
    global _gzo_search, _gzo_listing_index, _gzo_type_filter_index, _gzo_manufacturer_filter_index, _gzo_rarity_filter_index, _gzo_creator_filter_index, _gzo_mattmab_filter_index, _gzo_player_index, _gzo_active_id, _gzo_cache_autoload_attempted, _gzo_delivery_override_level, _gzo_delivery_level
    imgui = _blimgui.imgui
    opened = _begin_resizable_card("card_gzo", "BL4 Codes", "gold", _tab_card_height(780.0), 320, 1200) if _cyber else True
    if opened:
        if not _gzo_cache_autoload_attempted and not _gzo_entries:
            _gzo_cache_autoload_attempted = True
            _gzo_load_cache(silent=True)
        imgui.text_wrapped("Merged BL4 Codes catalog")
        _muted_wrapped("Single merged codes tab. Refresh GZO updates from save-editor.be. Local Lootlemon JSON is used only as a serial/link cache and local-only fallback rows. This never scrapes lootlemon.com.")
        _draw_mattmab_legit_modded_definition()
        _wrapped_button_row([
            ("Load Cache", _gzo_load_cache, "cyan", 110, 0),
            ("Refresh GZO", _gzo_refresh_catalog, "gold", 130, 0),
            ("Reload Lootlemon Cache", _gzo_reload_local_lootlemon_cache, "gold", 210, 0),
            ("Mattmab Validation", lambda: _catalog_validator_start("GZO"), "green", 180, 0),
            ("Import Selected To Bookmarks", _gzo_import_selected_to_store, "purple", 210, 0),
        ])
        _draw_refresh_progress(_gzo_refresh_progress)
        _draw_catalog_validator_progress("GZO")
        imgui.separator()
        imgui.text_wrapped("Filters")
        _gzo_search = _filter_input("Search", "gzo_search", _gzo_search, 256, width=420.0)
        def _gzo_filter_listing():
            global _gzo_listing_index
            _gzo_listing_index = _filter_combo("Listing", "gzo_listing", _gzo_listing_index, _GZO_LISTING_FILTERS, width=230.0)
        def _gzo_filter_type():
            global _gzo_type_filter_index
            _gzo_type_filter_index = _filter_combo("Type", "gzo_type", _gzo_type_filter_index, _gzo_filter_options("type"), width=230.0)
        def _gzo_filter_manufacturer():
            global _gzo_manufacturer_filter_index
            _gzo_manufacturer_filter_index = _filter_combo("Manufacturer", "gzo_manufacturer", _gzo_manufacturer_filter_index, _gzo_filter_options("manufacturer"), width=230.0)
        def _gzo_filter_rarity():
            global _gzo_rarity_filter_index
            _gzo_rarity_filter_index = _filter_combo("Rarity", "gzo_rarity", _gzo_rarity_filter_index, _gzo_filter_options("rarity"), width=230.0)
        def _gzo_filter_creator():
            global _gzo_creator_filter_index
            _gzo_creator_filter_index = _filter_combo("Creator", "gzo_creator", _gzo_creator_filter_index, _gzo_filter_options("creator"), width=230.0)
        def _gzo_filter_mattmab():
            global _gzo_mattmab_filter_index
            _gzo_mattmab_filter_index = _filter_combo("Mattmab Result", "gzo_mattmab_filter", _gzo_mattmab_filter_index, _MATTMAB_FILTERS, width=230.0)
        _filter_field_row([_gzo_filter_listing, _gzo_filter_type, _gzo_filter_manufacturer])
        _filter_field_row([_gzo_filter_rarity, _gzo_filter_creator, _gzo_filter_mattmab])
        _gzo_mattmab_filter_index = _mattmab_quick_filter_buttons("gzo", _gzo_mattmab_filter_index)
        filtered = _gzo_filtered_entries()
        imgui.text_wrapped(f"{len(filtered)} shown / {len(_gzo_entries)} merged | {len(_gzo_selected_ids)} selected")
        _wrapped_button_row([
            ("Select All", lambda: _gzo_select_all_filtered(filtered), "purple", 110, 0),
            ("Clear", lambda: _gzo_selected_ids.clear(), "pink", 80, 0),
            ("Copy Selected Serials", _gzo_copy_selected_serials, "gold", 185, 0),
        ])
        columns = getattr(imgui, "columns", None); next_column = getattr(imgui, "next_column", None); using_columns = False
        if callable(columns) and callable(next_column):
            try:
                columns(2, "msbt_gzo_codes_columns", True); using_columns = True
            except Exception:
                try: columns(2); using_columns = True
                except Exception: using_columns = False
        imgui.text_wrapped("CODES")
        child_open = _begin_child_region("msbt_gzo_codes_list", _resizable_height("child_gzo_list", "GZO list", 430, 160, 900))
        try:
            if not filtered:
                imgui.text_wrapped("No BL4 codes loaded/matching. Click Load Cache, Refresh GZO, or Reload Lootlemon Cache.")
            visible_filtered = filtered[:240]
            if len(filtered) > len(visible_filtered):
                imgui.text_wrapped(f"Showing first {len(visible_filtered)} row(s); narrow Search/Filters for more. Select All still selects all filtered rows.")
            for e in visible_filtered:
                eid = str(e.get("id", "")); checked = "[X]" if eid in _gzo_selected_ids else "[ ]"; active = "> " if eid == _gzo_active_id else "  "
                listing = str(e.get("listing", "")).strip()
                prefix = f"[{listing.upper()}] " if listing in ("Legit", "Modded") else ""
                meta = " | ".join(x for x in [_mattmab_validator_short(e), str(e.get("type", "")), str(e.get("manufacturer", "")), str(e.get("rarity", "")), str(e.get("character_class", "")), str(e.get("creator", ""))] if x and x != "GZO")
                label = f"{active}{checked} {prefix}{e.get('name','GZO Serial')}    {meta}###gzo_row_{eid}"
                if _selectable_row(label, eid == _gzo_active_id):
                    _gzo_active_id = eid
                    if eid in _gzo_selected_ids: _gzo_selected_ids.discard(eid)
                    else: _gzo_selected_ids.add(eid)
        finally:
            if child_open: _end_child_region()
        if using_columns: next_column()
        imgui.text_wrapped("DETAILS")
        active = _gzo_active_entry()
        if active:
            imgui.text_wrapped(str(active.get("name", "GZO Serial")))
            _muted_wrapped(_mattmab_validator_label(active) + " | " + _gzo_meta_label(active))
            detail = str(active.get("mattmab_validator_detail", "") or "")
            if detail:
                _muted_wrapped(detail)
            _input_text_multiline("Serial###gzo_active_serial", str(active.get("serial", "")), 65536, width=int(_fit_width(620, 24, 220)), height=130)
            imgui.separator()
            imgui.text_wrapped("Parts Breakdown")
            parts_text = _serial_parts_breakdown_for_value_cached(str(active.get("serial", "")))
            _input_text_multiline("###gzo_active_parts_breakdown", parts_text, 65536, width=int(_fit_width(620, 24, 220)), height=120)
            _button("Copy Parts Breakdown", lambda: _copy_text_to_clipboard("GZO parts breakdown", _serial_parts_breakdown_for_value_cached(str(active.get("serial", "")))), "purple", 190, 0)
            imgui.same_line()
            _button("Copy Serial", lambda: _copy_text_to_clipboard("BL4 serial", str(active.get("serial", ""))), "purple", 130, 0)
            if str(active.get("lootlemon_url", "")).strip():
                imgui.same_line(); _button("Open Lootlemon", lambda: _lootlemon_open_url(str(active.get("lootlemon_url", ""))), "gold", 155, 0)
            imgui.same_line(); _button("Bookmark This", lambda: (_gzo_selected_ids.add(str(active.get("id", ""))), _gzo_import_selected_to_store()), "cyan", 120, 0)
        else:
            imgui.text_wrapped("Select a GZO code to preview its serial.")
        if using_columns:
            try: columns(1)
            except Exception: pass
        imgui.separator()
        _draw_inline_target_selector("BL4 Codes Target")
        _gzo_delivery_override_level, _gzo_delivery_level = _draw_catalog_level_override("gzo", _gzo_delivery_override_level, _gzo_delivery_level)
        imgui.text_wrapped(f"{len(_gzo_selected_ids)} selected | Delivery uses GiveRewardAllPlayers, then patches requested target(s)")
        _wrapped_button_row([
            ("Deliver Selected", lambda: _gzo_deliver_selected("selected"), "purple", 165, 0),
            ("Deliver All", lambda: _gzo_deliver_selected("all"), "gold", 135, 0),
            ("Deliver Non-Host", lambda: _gzo_deliver_selected("nonhost"), "cyan", 185, 0),
        ])
        _gzo_preview_entries = _gzo_selected_entries() or ([active] if active else [])
        _gzo_preview_serials = [str(e.get("serial", "")).strip() for e in _gzo_preview_entries if e and _gzo_is_valid_serial(str(e.get("serial", "")).strip())]
        if _gzo_delivery_override_level:
            _gzo_preview_serials, _gzo_preview_changed, _gzo_preview_error = _serials_with_level_override(_gzo_preview_serials, _gzo_delivery_override_level, _gzo_delivery_level)
        _draw_serial_delivery_split_controls(_gzo_preview_serials, "BL4 Codes")
        imgui.text_wrapped(_gzo_status)
    if _cyber:
        _end_resizable_card()

def _draw_serial_store_tab() -> None:
    global _serial_store_name, _serial_store_group, _serial_store_serial, _serial_store_group_filter_index, _serial_store_player_index, _serial_store_search
    imgui = _blimgui.imgui
    _serial_store_load()
    opened = _begin_resizable_card("card_serial_bookmarks", "Serial Bookmarks", "purple", _tab_card_height(760.0), 320, 1200) if _cyber else True
    if opened:
        # Header: task name + obvious new action.
        imgui.text_wrapped("Serial Bookmarks")
        imgui.same_line(); _button("+ New Serial", _serial_store_clear_form, "cyan", 150, 0)
        imgui.same_line(); _button("Import", _serial_store_import_from_tools, "gold", 105, 0)
        _muted_wrapped("Browse saved serials, edit the active entry, then deliver the checked items from the footer.")
        imgui.separator()

        # Toolbar: search + group filter.
        _serial_store_search = _input_text("Search###serial_store_search", _serial_store_search, 256)
        groups = _serial_store_groups()
        _serial_store_group_filter_index = _combo("Groups###serial_store_groups", _serial_store_group_filter_index, groups)
        imgui.separator()

        filtered = _serial_store_filtered_entries()
        search = (_serial_store_search or "").strip().lower()
        if search:
            filtered = [
                e for e in filtered
                if search in str(e.get("name", "")).lower()
                or search in str(e.get("group", "Default")).lower()
                or search in str(e.get("serial", "")).lower()
            ]

        columns = getattr(imgui, "columns", None)
        next_column = getattr(imgui, "next_column", None)
        using_columns = False
        if callable(columns) and callable(next_column):
            try:
                columns(2, "msbt_serial_store_browse_edit_columns", True)
                using_columns = True
            except TypeError:
                try:
                    columns(2)
                    using_columns = True
                except Exception:
                    using_columns = False
            except Exception:
                using_columns = False

        # Left pane: browse/select.
        imgui.text_wrapped("SERIALS")
        selected_count = len(_serial_store_selected_entries())
        imgui.text_wrapped(f"{len(filtered)} shown / {len(_serial_store_entries)} saved | {selected_count} selected")
        _button("Select All", lambda: _serial_store_select_all_filtered(filtered), "purple", 110, 0)
        imgui.same_line(); _button("Clear", lambda: _serial_store_selected_ids.clear(), "pink", 80, 0)
        imgui.same_line(); _button("Copy Selected Serials", _serial_store_copy_selected_serials, "gold", 185, 0)
        child_open = _begin_child_region("msbt_serial_store_browser", _resizable_height("child_serial_bookmarks_list", "Bookmarks list", 405, 160, 900))
        try:
            if not filtered:
                imgui.text_wrapped("No saved serials match this search/group.")
            for e in filtered:
                eid = str(e.get("id", ""))
                checked = "[X]" if eid in _serial_store_selected_ids else "[ ]"
                active = "> " if eid == _serial_store_active_id else "  "
                name = str(e.get("name") or "Serial")
                group = str(e.get("group") or "Default")
                label = f"{active}{checked} {name}        {group}###serial_store_row_{eid}"
                if _selectable_row(label, eid == _serial_store_active_id):
                    _serial_store_set_active(e)
                    if eid in _serial_store_selected_ids:
                        _serial_store_selected_ids.discard(eid)
                    else:
                        _serial_store_selected_ids.add(eid)
        finally:
            if child_open:
                _end_child_region()

        if using_columns:
            next_column()

        # Right pane: edit details only.
        imgui.text_wrapped("DETAILS")
        _serial_store_name = _input_text("Name###serial_store_name", _serial_store_name, 256)
        _serial_store_group = _input_text("Group###serial_store_group", _serial_store_group, 256)
        _serial_store_serial = _input_text_multiline("Serial###serial_store_serial", _serial_store_serial, 65536, width=620, height=190)
        _button("Save", _serial_store_save_form, "cyan", 95, 0)
        imgui.same_line(); _button("Duplicate", _serial_store_duplicate_active, "purple", 115, 0)
        imgui.same_line(); _button("Delete", _serial_store_delete_active, "red", 90, 0)
        imgui.same_line(); _button("Copy", lambda: _copy_text_to_clipboard("stored serial", _serial_store_serial), "gold", 80, 0)
        imgui.spacing()
        imgui.text_wrapped(_serial_store_status)

        if using_columns:
            try:
                columns(1)
            except Exception:
                pass

        # Sticky-style footer: delivery is separated from editing.
        imgui.separator()
        _draw_inline_target_selector("Serial Bookmarks Target")
        selected_count = len(_serial_store_selected_entries())
        imgui.text_wrapped(f"{selected_count} selected")
        imgui.same_line()
        imgui.text_wrapped("Delivery uses GiveRewardAllPlayers, then patches requested target(s)")
        imgui.same_line(); _button("Deliver Selected", lambda: _serial_store_deliver_selected("selected"), "purple", 165, 0)
        imgui.same_line(); _button("Deliver All", lambda: _serial_store_deliver_selected("all"), "gold", 135, 0)
        imgui.same_line(); _button("Deliver Non-Host", lambda: _serial_store_deliver_selected("nonhost"), "cyan", 185, 0)
        _serial_store_preview_entries = _serial_store_selected_entries()
        _serial_store_preview_serials = []
        for _e in _serial_store_preview_entries:
            _serial_store_preview_serials.extend(_parse_serial_text(str(_e.get("serial", "")).strip()))
        _draw_serial_delivery_split_controls(_serial_store_preview_serials, "Serial Bookmarks")
    if _cyber:
        _end_resizable_card()

def _draw_serial_tools_tab() -> None:
    global _serial_tools_input
    imgui = _blimgui.imgui
    opened = _begin_resizable_card("card_serial_tools", "Serial Tools", "cyan", 720, 320, 1200) if _cyber else True
    if opened:
        imgui.text_wrapped("Paste a @U serialized value or deserialized human-readable serial below. The converter returns both formats.")
        new_input = _input_text_multiline("Input###msbt_serial_tools_input", _serial_tools_input, 65536, width=860, height=120)
        if new_input != _serial_tools_input:
            _serial_tools_input = new_input
            _serial_tools_convert()
        _button("Convert", _serial_tools_convert, "cyan", 120, 0)
        imgui.same_line()
        _button("Clear", _clear_serial_tools, "pink", 100, 0)
        imgui.separator()
        imgui.text_wrapped(_serial_tools_status)
        imgui.text_wrapped("Deserialized Output")
        _input_text_multiline("###msbt_serial_tools_deserialized", _serial_tools_deserialized, 65536, width=860, height=150)
        _button("Copy Deserialized", lambda: _copy_text_to_clipboard("deserialized serial", _serial_tools_deserialized), "purple", 190, 0)
        imgui.separator()
        imgui.text_wrapped("Parts Breakdown")
        _input_text_multiline("###msbt_serial_tools_parts", _serial_tools_parts_breakdown, 65536, width=860, height=180)
        _button("Copy Parts Breakdown", lambda: _copy_text_to_clipboard("parts breakdown", _serial_tools_parts_breakdown), "purple", 210, 0)
        imgui.separator()
        imgui.text_wrapped("@U Serialized Output")
        _input_text_multiline("###msbt_serial_tools_serialized", _serial_tools_serialized, 65536, width=860, height=95)
        _button("Copy Serialized", lambda: _copy_text_to_clipboard("serialized @U serial", _serial_tools_serialized), "purple", 170, 0)
    if _cyber:
        _end_resizable_card()


def _clear_serial_tools() -> None:
    global _serial_tools_input, _serial_tools_serialized, _serial_tools_deserialized, _serial_tools_parts_breakdown, _serial_tools_status
    _serial_tools_input = ""
    _serial_tools_serialized = ""
    _serial_tools_deserialized = ""
    _serial_tools_parts_breakdown = ""
    _serial_tools_status = "Paste a @U serial or deserialized serial text above."
    _log("Cleared Serial Tools input/output.")


def _draw_log_card(full_page: bool = False) -> None:
    _flush_worker_log_lines()
    imgui = _blimgui.imgui
    card_height = _tab_card_height(650.0, 58.0) if full_page else 120.0
    opened = _begin_resizable_card("card_activity_log", "Activity Log", "purple", card_height, 260, 1200) if _cyber else True
    if opened:
        if (_cyber_button_safe("Clear Log", "pink")):
            with _log_lock:
                _log_lines.clear()
                _pending_worker_log_lines.clear()
        with _log_lock:
            visible_lines = list(_log_lines if full_page else _log_lines[-4:])
        child_height = max(90.0, card_height - 62.0) if full_page else 0.0
        child_open = _begin_child_region("msbt_activity_log_lines", child_height) if full_page else False
        try:
            for line in visible_lines:
                imgui.text_wrapped(line)
        finally:
            if child_open:
                _end_child_region()
    if _cyber:
        _end_resizable_card()




def _begin_child_region(label: str, height: float, width: float = 0.0) -> bool:
    """Begin a normal mouse-wheel scrollable ImGui child with positive sizes.

    This restores the normal vertical wheel-scroll areas without using the
    experimental horizontal/manual-scroll wrappers.  Width/height are always
    resolved to positive values before calling BLImGui so Size>0 asserts are
    avoided.
    """
    imgui = _blimgui.imgui
    begin_child = getattr(imgui, "begin_child", None)
    if not callable(begin_child):
        return False
    try:
        avail_w = _imgui_available_width(420.0)
    except Exception:
        avail_w = 420.0
    try:
        w = float(width) if float(width or 0.0) > 0.0 else float(avail_w)
    except Exception:
        w = float(avail_w)
    try:
        h = float(height)
    except Exception:
        h = 120.0
    w = max(1.0, min(max(1.0, avail_w), w))
    h = max(1.0, h)
    for args in (
        (str(label), w, h, True),
        (str(label), w, h),
        (str(label), (w, h), True),
        (str(label), (w, h)),
    ):
        try:
            begin_child(*args)
            return True
        except TypeError:
            continue
        except Exception as exc:
            _log(f"begin_child unavailable for {label}: {exc!r}")
            return False
    return False

def _end_child_region() -> None:
    imgui = _blimgui.imgui
    end_child = getattr(imgui, "end_child", None)
    if callable(end_child):
        try:
            end_child()
        except Exception as exc:
            _log(f"end_child failed: {exc!r}")


def _imgui_available_height(default: float = 640.0) -> float:
    """Best-effort available content height for resize-friendly tab panels."""
    imgui = _blimgui.imgui
    for name in ("get_content_region_avail", "get_content_region_available"):
        fn = getattr(imgui, name, None)
        if not callable(fn):
            continue
        try:
            value = fn()
        except Exception:
            continue
        try:
            if isinstance(value, (tuple, list)) and len(value) >= 2:
                return max(220.0, float(value[1]))
            y = getattr(value, "y", None)
            if y is not None:
                return max(220.0, float(y))
        except Exception:
            continue
    return float(default)


def _imgui_available_width(default: float = 1180.0) -> float:
    """Best-effort content width for wrapping button rows."""
    imgui = _blimgui.imgui
    for name in ("get_content_region_avail", "get_content_region_available"):
        fn = getattr(imgui, name, None)
        if not callable(fn):
            continue
        try:
            value = fn()
        except Exception:
            continue
        try:
            if isinstance(value, (tuple, list)) and len(value) >= 1:
                return max(260.0, float(value[0]))
            x = getattr(value, "x", None)
            if x is not None:
                return max(260.0, float(x))
        except Exception:
            continue
    return float(default)


def _wrapped_button_row(buttons: list[tuple[str, Callable[[], None], str, float, float]], max_width: float | None = None) -> None:
    """Draw buttons left-to-right and wrap before they overflow the current region."""
    imgui = _blimgui.imgui
    avail = float(max_width or _imgui_available_width())
    spacing = 8.0
    row_used = 0.0
    for label, fn, accent, width, height in buttons:
        w = float(width or 150.0)
        if row_used > 0.0 and row_used + spacing + w <= avail:
            try:
                imgui.same_line()
            except Exception:
                pass
            row_used += spacing + w
        else:
            row_used = w
        _button(label, fn, accent, width, height)




def _current_content_width(default: float = 520.0, minimum: float = 160.0) -> float:
    return max(float(minimum), float(_imgui_available_width(default)))

def _fit_width(requested: float, pad: float = 24.0, minimum: float = 80.0) -> float:
    return max(float(minimum), min(float(requested), _current_content_width(float(requested), minimum) - float(pad)))

def _card_button_row(buttons: list[tuple[str, Callable[[], None], str, float, float]]) -> None:
    # Give each card a little padding margin so fixed-width action buttons wrap
    # before they clip against the right edge of the card.
    _wrapped_button_row(buttons, max(120.0, _imgui_available_width(420.0) - 12.0))

def _tab_card_height(default: float = 640.0, bottom_padding: float = 28.0) -> float:
    return max(float(default), _imgui_available_height(default) - float(bottom_padding))


def _remaining_child_height(default: float = 300.0, bottom_padding: float = 70.0) -> float:
    return max(float(default), _imgui_available_height(default) - float(bottom_padding))



def _imgui_set_cursor_x(x: float) -> None:
    """Best-effort cursor X setter for BLImGui/imgui variants."""
    imgui = _blimgui.imgui
    for name in ("set_cursor_pos_x", "set_cursor_x"):
        fn = getattr(imgui, name, None)
        if callable(fn):
            try:
                fn(float(x))
                return
            except Exception:
                pass
    # Last resort: move the full cursor position when the binding exposes it.
    get_pos = getattr(imgui, "get_cursor_pos", None)
    set_pos = getattr(imgui, "set_cursor_pos", None)
    if callable(get_pos) and callable(set_pos):
        try:
            pos = get_pos()
            y = pos[1] if isinstance(pos, (tuple, list)) and len(pos) > 1 else getattr(pos, "y", 0.0)
            set_pos((float(x), float(y)))
        except Exception:
            pass


def _draw_handheld_hscroll(tab_index: int, virtual_width: float) -> int:
    """Horizontal view sliders are disabled; use wrapped layouts + vertical wheel scrolling."""
    _ui_hscroll_offsets[int(tab_index)] = 0
    return 0


def _draw_tab_viewport(tab_index: int, draw_fn: Callable[[], None], virtual_width: float = 1180.0) -> None:
    """Draw the active tab without an ImGui child wrapper.

    This is the stability path: no BeginChild, no fake resize child, no negative
    cursor offset.  It prevents the Size>0 crash while preserving all tab
    functionality.
    """
    # The old emergency Reset box sizes button is no longer needed and took up
    # permanent space in every Boosting Tools tab. Keep the reset helper around
    # for manual debugging, but do not render the button.
    draw_fn()


def _selectable_row(label: str, selected: bool) -> bool:
    imgui = _blimgui.imgui
    selectable = getattr(imgui, "selectable", None)
    if callable(selectable):
        for args in ((label, selected), (label,)):
            try:
                result = selectable(*args)
                if isinstance(result, tuple):
                    return bool(result[0])
                return bool(result)
            except TypeError:
                continue
            except Exception:
                break
    # Fallback: button rows. Prefix the active row so older BLImGui builds still show selection.
    return imgui.button(("> " if selected else "  ") + label)


def _draw_three_column_boosting() -> None:
    """Responsive Boosting layout.

    Draw all cards every time.  If the window is too narrow, reduce the column
    count and wrap cards/groups underneath instead of clipping the right side.
    The main ImGui window provides vertical scrolling when the wrapped content
    exceeds the screen height.
    """
    imgui = _blimgui.imgui
    groups = [
        lambda: (_draw_serial_card(), _draw_experience_card()),
        lambda: (_draw_currency_card(), _draw_inventory_size_card(), _draw_rarity_disabler_card()),
        lambda: (_draw_dev_tools_card(), _draw_sdu_card()),
    ]
    avail = _imgui_available_width(1180.0)
    # Keep card columns wide enough that labels/buttons have room to wrap inside
    # their card.  On 720p handhelds this becomes 1 column with vertical scroll.
    min_col_w = 390.0
    if avail >= (min_col_w * 3.0 + 24.0):
        col_count = 3
    elif avail >= (min_col_w * 2.0 + 12.0):
        col_count = 2
    else:
        col_count = 1

    if col_count < 3:
        _muted_wrapped(f"Small-screen layout: {col_count} column(s); cards wrap downward. Scroll vertically to reach the rest.")

    columns = getattr(imgui, "columns", None)
    next_column = getattr(imgui, "next_column", None)
    if callable(columns) and callable(next_column) and col_count > 1:
        try:
            columns(col_count, "msbt_boosting_responsive_columns", False)
            for idx, group in enumerate(groups):
                if idx > 0:
                    next_column()
                group()
                # When we run out of visible columns, reset to the first column
                # on a new row by ending/restarting columns.  This avoids any
                # right-side clipping when more groups are later added.
                if (idx + 1) % col_count == 0 and (idx + 1) < len(groups):
                    columns(1)
                    imgui.spacing()
                    columns(col_count, "msbt_boosting_responsive_columns_2", False)
            columns(1)
            return
        except Exception as exc:
            try:
                columns(1)
            except Exception:
                pass
            _log(f"Responsive columns unavailable; falling back to stacked cards: {exc!r}")

    for idx, group in enumerate(groups):
        if idx:
            imgui.spacing()
            imgui.separator()
        group()

def _set_active_tab(index: int) -> None:
    global _active_tab
    _active_tab = max(0, min(int(index), 9))


def _draw_tabs() -> None:
    labels = ["Boosting", "Serial Tools", "Serial Bookmarks", "BL4 Codes", "Legit Builder", "Validator", "Item Pool Spawning", "Map Travel", "Player Movement", "Activity Log"]
    accents = ["cyan", "cyan", "purple", "gold", "cyan", "cyan", "purple", "pink", "cyan", "cyan"]
    buttons: list[tuple[str, Callable[[], None], str, float, float]] = []
    for index, label in enumerate(labels):
        display = f"[{label}]" if _active_tab == index else label
        width = 180 if index in (3, 5) else (220 if index in (4, 6, 7, 8) else 160)
        buttons.append((display, lambda index=index: _set_active_tab(index), accents[index % len(accents)], float(width), 0.0))
    _wrapped_button_row(buttons)
    _blimgui.imgui.separator()


def _save_favorites() -> None:
    # Keep descriptions only for entries which are still favorited.
    for key in list(_favorite_itempool_descriptions):
        if key not in _favorite_itempools:
            _favorite_itempool_descriptions.pop(key, None)
    for key in list(_favorite_travel_map_descriptions):
        if key not in _favorite_travel_maps:
            _favorite_travel_map_descriptions.pop(key, None)
    for key in list(_favorite_travel_station_descriptions):
        if key not in _favorite_travel_stations:
            _favorite_travel_station_descriptions.pop(key, None)
    save_extra_settings(
        favorite_itempools=sorted(_favorite_itempools),
        favorite_travel_maps=sorted(_favorite_travel_maps),
        favorite_travel_stations=sorted(_favorite_travel_stations),
        favorite_itempool_descriptions=dict(sorted(_favorite_itempool_descriptions.items())),
        favorite_travel_map_descriptions=dict(sorted(_favorite_travel_map_descriptions.items())),
        favorite_travel_station_descriptions=dict(sorted(_favorite_travel_station_descriptions.items())),
        travel_show_all_stations=bool(_travel_show_all_stations),
    )


def _sort_favorites_first(rows: list[dict[str, str]], id_key: str, favorites: set[str]) -> list[dict[str, str]]:
    return sorted(rows, key=lambda row: (0 if str(row.get(id_key, "")) in favorites else 1, str(row.get("display_name", row.get(id_key, ""))).lower()))


def _fav_prefix(value: str, favorites: set[str]) -> str:
    return "[FAV] " if value in favorites else ""


def _fav_description(value: str, descriptions: dict[str, str]) -> str:
    text = str(descriptions.get(str(value), "")).strip()
    return f" - {text}" if text else ""


def _draw_favorite_description_editor(label: str, key: str, favorites: set[str], descriptions: dict[str, str]) -> None:
    if not key or key not in favorites:
        return
    old_text = str(descriptions.get(key, ""))
    new_text = _input_text(label, old_text, 128).strip()
    if new_text != old_text:
        if new_text:
            descriptions[key] = new_text
        else:
            descriptions.pop(key, None)
        _save_favorites()


def _current_itempool_all_results() -> list[dict[str, str]]:
    return _sort_favorites_first(filter_item_pools(_itempool_search, _itempool_category, limit=0), "itempool", _favorite_itempools)

def _current_itempool_results() -> list[dict[str, str]]:
    all_results = _current_itempool_all_results()
    start = max(0, int(_itempool_page)) * _ITEMPOOL_PAGE_SIZE
    return all_results[start:start + _ITEMPOOL_PAGE_SIZE]


def _select_itempool_by_name(pool_name: str) -> None:
    """Keep the same item pool selected after favorite sorting moves it."""
    global _itempool_page, _itempool_selected_index
    if not pool_name:
        return
    all_results = _current_itempool_all_results()
    for absolute_index, row in enumerate(all_results):
        if str(row.get("itempool", "")) == pool_name:
            _itempool_page = absolute_index // _ITEMPOOL_PAGE_SIZE
            _itempool_selected_index = absolute_index % _ITEMPOOL_PAGE_SIZE
            return


def _select_travel_map_by_name(map_name: str) -> None:
    """Keep the same map selected after favorite sorting moves it."""
    global _travel_selected_map_index
    if not map_name:
        return
    results = _current_travel_map_results()
    for index, row in enumerate(results):
        if str(row.get("map", "")) == map_name:
            _travel_selected_map_index = index
            return


def _select_travel_station_by_name(station_name: str) -> None:
    """Keep the same travel station selected after favorite sorting moves it."""
    global _travel_selected_station_index
    if not station_name:
        return
    results = _current_travel_station_results()
    for index, row in enumerate(results):
        if str(row.get("station", "")) == station_name:
            _travel_selected_station_index = index
            return


def _spawn_selected_item_pool() -> None:
    global _itempool_selected_index
    results = _current_itempool_results()
    if not results:
        _log("No item pool selected.")
        return
    _itempool_selected_index = max(0, min(_itempool_selected_index, len(results) - 1))
    entry = results[_itempool_selected_index]
    spawned = spawn_item_pool(entry["itempool"], _itempool_level, _itempool_count)
    _log(f"Spawned {entry['display_name']} ({entry['itempool']}) x{spawned} at level {_itempool_level}.")


def _toggle_selected_itempool_favorite() -> None:
    results = _current_itempool_results()
    if not results:
        _log("No item pool selected to favorite.")
        return
    idx = max(0, min(_itempool_selected_index, len(results) - 1))
    pool = str(results[idx].get("itempool", ""))
    if not pool:
        return
    if pool in _favorite_itempools:
        _favorite_itempools.remove(pool)
        _favorite_itempool_descriptions.pop(pool, None)
        _log(f"Removed item pool favorite: {pool}")
    else:
        _favorite_itempools.add(pool)
        _log(f"Added item pool favorite: {pool}")
    _save_favorites()
    _select_itempool_by_name(pool)


def _toggle_selected_map_favorite() -> None:
    results = _current_travel_map_results()
    if not results:
        _log("No map selected to favorite.")
        return
    idx = max(0, min(_travel_selected_map_index, len(results) - 1))
    name = str(results[idx].get("map", ""))
    if not name:
        return
    if name in _favorite_travel_maps:
        _favorite_travel_maps.remove(name)
        _favorite_travel_map_descriptions.pop(name, None)
        _log(f"Removed map favorite: {name}")
    else:
        _favorite_travel_maps.add(name)
        _log(f"Added map favorite: {name}")
    _save_favorites()
    _select_travel_map_by_name(name)


def _toggle_selected_station_favorite() -> None:
    results = _current_travel_station_results()
    if not results:
        _log("No travel station selected to favorite.")
        return
    idx = max(0, min(_travel_selected_station_index, len(results) - 1))
    station = str(results[idx].get("station", ""))
    if not station:
        return
    if station in _favorite_travel_stations:
        _favorite_travel_stations.remove(station)
        _favorite_travel_station_descriptions.pop(station, None)
        _log(f"Removed travel station favorite: {station}")
    else:
        _favorite_travel_stations.add(station)
        _log(f"Added travel station favorite: {station}")
    _save_favorites()
    _select_travel_station_by_name(station)


def _draw_category_button(label: str, accent: str = "purple") -> None:
    global _itempool_category, _itempool_selected_index, _itempool_page
    def _set() -> None:
        global _itempool_category, _itempool_selected_index, _itempool_page
        _itempool_category = label
        _itempool_selected_index = 0
        _itempool_page = 0
    display = f"[{label}]" if _itempool_category == label else label
    _button(display, _set, accent)



def _legit_pretty_label(value: object) -> str:
    text = str(value or "").strip().replace("_", " ")
    if not text:
        return "Unknown"
    special = {"smg": "SMG", "cov": "COV", "c4sh": "C4SH"}
    low = text.lower().replace(" ", "_")
    if low in special:
        return special[low]
    return text.title()


def _legit_all_buildable_roots() -> list[dict]:
    if _legit_builder is None:
        return []
    cached = _legit_cache.get("roots")
    if cached is not None:
        return list(cached)
    try:
        rows = list(_legit_builder.roots())
        _legit_cache["roots"] = rows
        return list(rows)
    except Exception as exc:
        _log(f"Legit Builder roots load failed: {exc!r}")
        return []


def _legit_type_options() -> list[str]:
    cached = _legit_cache.get("types")
    if cached is not None:
        return list(cached)
    rows = _legit_all_buildable_roots()
    seen: set[str] = set()
    order = ["pistol", "smg", "shotgun", "assault_rifle", "sniper", "shield", "repair_kit", "enhancement", "gadget", "heavy", "class_mod"]
    for r in rows:
        t = str(r.get("item_type", "")).strip()
        if t:
            seen.add(t)
    out = [t for t in order if t in seen] + sorted(seen.difference(order))
    _legit_cache["types"] = out
    return list(out)


def _legit_manufacturer_options(item_type: str) -> list[str]:
    key = str(item_type or "")
    mans_cache = _legit_cache.get("mans", {})
    if key in mans_cache:
        return list(mans_cache[key])
    rows = _legit_all_buildable_roots()
    seen: set[str] = set()
    for r in rows:
        if str(r.get("item_type", "")) != item_type:
            continue
        m = str(r.get("manufacturer", "")).strip()
        if m:
            seen.add(m)
    out = sorted(seen)
    mans_cache[key] = out
    return list(out)


def _legit_root_options() -> list[dict]:
    rows = _legit_all_buildable_roots()
    types = _legit_type_options()
    if not types:
        return []
    t_idx = max(0, min(int(_legit_type_index), len(types) - 1))
    item_type = types[t_idx]
    mans = _legit_manufacturer_options(item_type)
    if not mans:
        return []
    m_idx = max(0, min(int(_legit_manufacturer_index), len(mans) - 1))
    manufacturer = mans[m_idx]
    q = _legit_root_search.strip().lower()
    cache_key = (item_type, manufacturer, q)
    root_options_cache = _legit_cache.get("root_options", {})
    if cache_key in root_options_cache:
        return list(root_options_cache[cache_key])
    out = [r for r in rows if str(r.get("item_type", "")) == item_type and str(r.get("manufacturer", "")) == manufacturer]
    if q:
        out = [r for r in out if q in str(r.get("key", "")).lower() or q in str(r.get("name", "")).lower() or q in str(r.get("inv", "")).lower() or q in str(r.get("manufacturer", "")).lower() or q in str(r.get("item_type", "")).lower() or q in str(r.get("build_label", "")).lower()]
    out = sorted(out, key=lambda r: (int(r.get("serial") or 0), str(r.get("key") or "")))
    root_options_cache[cache_key] = out
    return list(out)


def _legit_selected_root() -> dict | None:
    rows = _legit_root_options()
    if not rows:
        return None
    idx = max(0, min(_legit_root_index, len(rows) - 1))
    return rows[idx]



def _legit_rarity_color(part: dict):
    rarity = str((part or {}).get("rarity") or "").lower()
    # BL pearlescent should read as blue/cyan, not epic-purple.
    if "pearl" in rarity:
        return (0.25, 0.95, 1.00, 1.0)
    if "legend" in rarity:
        return (1.00, 0.62, 0.12, 1.0)
    if "epic" in rarity:
        return (0.72, 0.35, 1.00, 1.0)
    if rarity == "rare":
        return (0.25, 0.55, 1.00, 1.0)
    if "uncommon" in rarity:
        return (0.20, 0.90, 0.35, 1.0)
    if "common" in rarity:
        return (0.82, 0.82, 0.82, 1.0)
    return None

def _legit_selectable_part_row(label: str, selected: bool, part: dict | None = None) -> bool:
    imgui = _blimgui.imgui
    color = _legit_rarity_color(part or {})
    pushed = False
    if color is not None:
        try:
            imgui.push_style_color(imgui.Col_.text, color)
            pushed = True
        except Exception:
            pushed = False
    try:
        return _selectable_row(label, selected)
    finally:
        if pushed:
            try:
                imgui.pop_style_color()
            except Exception:
                pass

def _legit_part_line(part: dict) -> str:
    table = str(part.get("table", "")).strip()
    key = str(part.get("key", "")).strip()
    return f"{table}:{key}" if table else key

def _legit_part_display_label(part: dict) -> str:
    display = str(part.get("display") or part.get("debug") or part.get("internal") or part.get("key") or "").strip()
    names = [str(x).strip() for x in (part.get("name_parts") or part.get("np_names") or []) if str(x).strip()]
    if names and not any(n.lower() in display.lower() for n in names):
        display = f"{display} ({', '.join(names)})" if display else ", ".join(names)
    rarity = str(part.get("rarity") or "").strip()
    key = str(part.get("key") or "").strip()
    serial = str(part.get("serial_token") or ("{" + str(part.get("serial")) + "}")).strip()
    prefix = f"[{rarity.title()}] " if rarity else ""
    inherited = str(part.get("inherited_from") or "").strip()
    suffix = f" from {inherited}" if inherited else ""

    # Put the serial token at the front so users who know the part number by
    # heart can see it before the long display/debug name gets clipped.
    lead = f"{serial} " if serial else ""
    if display and key and display.lower() != key.lower():
        return f"{lead}{prefix}{display} ({key}){suffix}"
    return f"{lead}{prefix}{key or display}{suffix}"


def _legit_describe_line(root_key: str, line: str) -> str:
    raw = str(line or "").strip()
    if not raw or _legit_builder is None:
        return raw
    cache_key = (str(root_key or ""), raw)
    desc_cache = _legit_cache.get("describe", {})
    if cache_key in desc_cache:
        return str(desc_cache[cache_key])
    table = None
    key = raw
    if ":" in raw and not raw.startswith("{"):
        table, key = raw.split(":", 1)
        table = table.strip()
        key = key.strip()
    try:
        desc = _legit_builder.describe_part(root_key, key, table=table)
    except Exception:
        desc = None
    out = raw if not desc else _legit_part_display_label(desc)
    desc_cache[cache_key] = out
    return out


def _legit_selected_parts_lines() -> list:
    out: list = []
    for line in str(_legit_selected_parts_text or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Accept "table:key", "table serial", raw key, or raw serial.
        if ":" in line and not line.startswith("{"):
            table, key = line.split(":", 1)
            out.append({"table": table.strip(), "key": key.strip()})
        else:
            out.append(line)
    return out


def _legit_selected_part_lines_raw() -> list[str]:
    return [l.strip() for l in str(_legit_selected_parts_text or "").splitlines() if l.strip() and not l.strip().startswith("#")]


def _legit_set_selected_part_lines(lines: list[str], *, preserve_duplicates: bool | None = None) -> None:
    global _legit_selected_parts_text, _legit_human, _legit_base85
    if preserve_duplicates is None:
        preserve_duplicates = bool(_legit_unlock_rules)
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        t = str(line or "").strip()
        if not t:
            continue
        # Normal legit mode keeps one copy of a part.  Unlock mode is a true
        # modded builder mode, so every repeated line is intentional and must be
        # preserved all the way into the human/Base85 serial.
        if not preserve_duplicates:
            if t in seen:
                continue
            seen.add(t)
        out.append(t)
    _legit_selected_parts_text = "\n".join(out)
    _legit_clear_dynamic_cache()
    # Force explicit rebuild after edits so stale output is not handed out.
    _legit_human = ""
    _legit_base85 = ""


def _legit_set_part_line_count(line: str, count: int) -> None:
    """Set the total selected quantity for one raw compact part line."""
    line = str(line or "").strip()
    if not line:
        return
    try:
        count = int(count)
    except Exception:
        count = 1
    count = max(0, min(999, count))
    others = [l for l in _legit_selected_part_lines_raw() if l != line]
    _legit_set_selected_part_lines(others + ([line] * count), preserve_duplicates=True)


def _legit_clear_selected_parts() -> None:
    """Clear the in-game legit builder selection and stale build outputs."""
    _legit_set_selected_part_lines([])

def _legit_slot_meta(root_key: str) -> dict[str, dict]:
    if _legit_builder is None:
        return {}
    cache_key = (str(root_key or ""), _legit_selected_signature())
    slot_cache = _legit_cache.get("slot_meta", {})
    if cache_key in slot_cache:
        return dict(slot_cache[cache_key])
    try:
        out = {str(r.get("slot") or "").lower(): r for r in _legit_builder.slot_counts(root_key, _legit_selected_parts_lines())}
        slot_cache[cache_key] = out
        return dict(out)
    except Exception as exc:
        _log(f"Legit slot-count lookup failed: {exc!r}")
        return {}


def _legit_add_part_from_browser(part: dict) -> None:
    line = _legit_part_line(part)
    if not line:
        return
    root = _legit_selected_root()
    table = str(part.get("table") or "").strip()
    lines = _legit_selected_part_lines_raw()

    # Unlock mode is intentionally a true modded-builder mode: allow duplicate
    # copies of the exact same part and ignore all slot-count/type rules.
    if not _legit_unlock_rules:
        if line in lines:
            return
        if root and table and _legit_builder is not None:
            meta = _legit_slot_meta(str(root.get("key") or "")).get(table.lower(), {})
            max_count = meta.get("max")
            if max_count is not None:
                selected_for_slot = _legit_selected_lines_for_slot(table)
                try:
                    m = int(max_count)
                except Exception:
                    m = 99
                if m <= 0:
                    return
                if len(selected_for_slot) >= m:
                    if m == 1:
                        # Slot picker behavior: choosing a different valid part replaces the old one.
                        lines = [l for l in lines if not l.lower().startswith(table.lower() + ":")]
                    else:
                        return
    lines.append(line)
    _legit_set_selected_part_lines(lines)


def _legit_remove_part_line(line: str) -> None:
    line = str(line or "").strip()
    if not line:
        return
    _legit_set_selected_part_lines([l for l in _legit_selected_part_lines_raw() if l != line])


def _legit_remove_part_line_at(line: str, occurrence_index: int = 0) -> None:
    """Remove a single selected occurrence, which matters in Unlock duplicate mode."""
    line = str(line or "").strip()
    if not line:
        return
    occurrence_index = max(0, int(occurrence_index or 0))
    seen = 0
    out: list[str] = []
    removed = False
    for raw in _legit_selected_part_lines_raw():
        if not removed and raw == line:
            if seen == occurrence_index:
                removed = True
                seen += 1
                continue
            seen += 1
        out.append(raw)
    _legit_set_selected_part_lines(out)


def _legit_selected_lines_for_slot(table: str) -> list[str]:
    prefix = str(table or "").strip() + ":"
    return [l for l in _legit_selected_part_lines_raw() if l.startswith(prefix)]


def _legit_selected_without_slot(table: str) -> list:
    prefix = str(table or "").strip().lower() + ":"
    out: list = []
    for item in _legit_selected_parts_lines():
        if isinstance(item, dict) and str(item.get("table", "")).strip().lower() == str(table or "").strip().lower():
            continue
        if isinstance(item, str) and item.lower().startswith(prefix):
            continue
        out.append(item)
    return out


def _legit_allowed_parts_for_slot(root_key: str, table: str, search: str = "", limit: int = 80) -> list[dict]:
    if _legit_builder is None:
        return []
    cache_key = (str(root_key or ""), str(table or "").lower(), str(search or "").strip().lower(), _legit_selected_signature(), int(limit), bool(_legit_unlock_rules))
    allowed_cache = _legit_cache.get("allowed", {})
    if cache_key in allowed_cache:
        return [dict(p) for p in allowed_cache[cache_key]]
    try:
        # For exact-one slots, ignore the existing same-slot part so the picker can
        # show replacements. For multi-select slots, keep existing same-slot parts
        # in the test set so exclusion tags like licensed_topacc correctly hide
        # mutually-exclusive additions.
        selected_full = _legit_selected_parts_lines()
        selected_for_test = selected_full
        try:
            meta = _legit_slot_meta(root_key).get(str(table or "").lower(), {})
            if meta.get("max") is not None and int(meta.get("max")) == 1:
                selected_for_test = _legit_selected_without_slot(table)
        except Exception:
            selected_for_test = selected_full
        candidates = _legit_builder.search_parts(root_key, search, table=table, limit=500)
        out: list[dict] = []
        for part in candidates:
            if _legit_unlock_rules:
                part = dict(part)
                part["reason"] = "Unlocked: rules bypassed"
                out.append(part)
            else:
                ok, reason = _legit_builder.is_part_allowed(root_key, selected_for_test, part.get("key"), table=part.get("table"))
                if ok:
                    part = dict(part)
                    part["reason"] = reason
                    out.append(part)
            if len(out) >= limit:
                break
        allowed_cache[cache_key] = [dict(p) for p in out]
        return out
    except Exception as exc:
        _log(f"Legit allowed-parts failed for {table}: {exc!r}")
        return []


def _legit_draw_slot_box(root_key: str, table: str, slot_idx: int, slot_meta: dict | None = None, slot_width: float = 0.0) -> None:
    global _legit_slot_search
    imgui = _blimgui.imgui
    selected_lines = _legit_selected_lines_for_slot(table)
    slot_meta = slot_meta or {}
    min_count = slot_meta.get("min")
    max_count = slot_meta.get("max")
    src = slot_meta.get("source") or "fallback"
    try:
        mn_s = "?" if min_count is None else str(int(min_count))
        mx_s = "?" if max_count is None else str(int(max_count))
    except Exception:
        mn_s, mx_s = str(min_count), str(max_count)

    # Box each slot in its own real ImGui child.  This is the old/desired
    # three-card layout: normal bordered panels, normal mouse-wheel vertical
    # scrolling, no fake horizontal sliders.  The child is always closed in the
    # finally block below.
    child_open = _begin_child_region(f"msbt_legit_slot_{slot_idx}_{table}", 235.0, max(1.0, float(slot_width or 0.0)))
    try:
        if _legit_unlock_rules:
            imgui.text_wrapped(f"{table}  |  {len(selected_lines)}/∞ selected  |  UNLOCKED rules bypassed")
        else:
            imgui.text_wrapped(f"{table}  |  {len(selected_lines)}/{mx_s} selected  |  min {mn_s}  ({src})")
        if (not _legit_unlock_rules) and max_count is not None:
            try:
                if int(max_count) == 0:
                    _muted_wrapped("Disabled by selected composition.")
            except Exception:
                pass
        if selected_lines:
            if _legit_unlock_rules:
                _count_by_line: dict[str, int] = {}
                _ordered_lines: list[str] = []
                for _line in selected_lines:
                    if _line not in _count_by_line:
                        _ordered_lines.append(_line)
                        _count_by_line[_line] = 0
                    _count_by_line[_line] += 1
                for line in _ordered_lines[:8]:
                    _qty = int(_count_by_line.get(line, 1))
                    _desc_part = None
                    try:
                        _raw = str(line).strip()
                        if ":" in _raw:
                            _tbl, _key = _raw.split(":", 1)
                        else:
                            _tbl, _key = "", _raw
                        _desc_part = _legit_builder.describe_part(root_key, _key, table=_tbl) if _legit_builder else None
                    except Exception:
                        _desc_part = None
                    # X removes one copy.  In Unlock mode we keep the editable
                    # quantity control visually larger so the actual count is
                    # easy to read on crowded slot cards.
                    _button(f"X###legit_rm_{slot_idx}_{line}", lambda line=line: _legit_remove_part_line_at(line, 0), "red", 22, 20)
                    try:
                        imgui.same_line()
                        imgui.text("Qty")
                        imgui.same_line()
                        imgui.push_item_width(92)
                    except Exception:
                        pass
                    _new_qty = _input_int_clamped(f"###legit_qty_{slot_idx}_{line}", _qty, 0, 999)
                    try:
                        imgui.pop_item_width()
                    except Exception:
                        pass
                    if _new_qty != _qty:
                        _legit_set_part_line_count(line, _new_qty)
                    try:
                        imgui.text_disabled(f"Current copies: {_qty}")
                    except Exception:
                        pass
                    _c = _legit_rarity_color(_desc_part or {})
                    _pushed = False
                    if _c is not None:
                        try:
                            imgui.push_style_color(imgui.Col_.text, _c); _pushed = True
                        except Exception:
                            _pushed = False
                    try:
                        imgui.indent(10.0)
                    except Exception:
                        pass
                    try:
                        imgui.text_wrapped(_legit_describe_line(root_key, line))
                    finally:
                        try:
                            imgui.unindent(10.0)
                        except Exception:
                            pass
                        if _pushed:
                            try: imgui.pop_style_color()
                            except Exception: pass
                if len(_ordered_lines) > 8:
                    _muted_wrapped(f"{len(_ordered_lines) - 8} more selected part type(s) hidden in this slot.")
            else:
                _occurrence_counts: dict[str, int] = {}
                for line in selected_lines[:8]:
                    _occ_idx = _occurrence_counts.get(line, 0)
                    _occurrence_counts[line] = _occ_idx + 1
                    _desc_part = None
                    try:
                        _raw = str(line).strip()
                        if ":" in _raw:
                            _tbl, _key = _raw.split(":", 1)
                        else:
                            _tbl, _key = "", _raw
                        _desc_part = _legit_builder.describe_part(root_key, _key, table=_tbl) if _legit_builder else None
                    except Exception:
                        _desc_part = None
                    # Keep remove controls compact: small X on the left, then the
                    # selected part text. This avoids pushing the important serial
                    # number off the right edge.
                    _button(f"X###legit_rm_{slot_idx}_{_occ_idx}_{line}", lambda line=line, _occ_idx=_occ_idx: _legit_remove_part_line_at(line, _occ_idx), "red", 22, 20)
                    try:
                        imgui.same_line()
                    except Exception:
                        pass
                    _c = _legit_rarity_color(_desc_part or {})
                    _pushed = False
                    if _c is not None:
                        try:
                            imgui.push_style_color(imgui.Col_.text, _c); _pushed = True
                        except Exception:
                            _pushed = False
                    try:
                        imgui.text_wrapped(_legit_describe_line(root_key, line))
                    finally:
                        if _pushed:
                            try: imgui.pop_style_color()
                            except Exception: pass
        else:
            _muted_wrapped("No part selected for this slot.")

        # A full slot does not need to spend time rendering candidate rows.
        try:
            full = max_count is not None and int(max_count) >= 0 and len(selected_lines) >= int(max_count)
        except Exception:
            full = False
        if (not _legit_unlock_rules) and full and selected_lines:
            _muted_wrapped("Slot is at max count. Remove a part first, or pick another valid part after removing it.")
            return

        # Do not hard-cap visible part lists anymore.  Compute allowed rows once per change,
        # then put the row list in a child scroll region.  This keeps the menu compact while
        # still letting high-count slots expose every valid candidate.
        allowed_all = _legit_allowed_parts_for_slot(root_key, table, _legit_part_search, limit=1000)
        if not allowed_all:
            _muted_wrapped("No currently allowed parts for this slot. Pick an inv_comp/rarity first or change the filter.")
            return

        search_key = f"{root_key.lower()}::{str(table).lower()}"
        local_search = _legit_slot_search.get(search_key, "")
        if len(allowed_all) > 10:
            try:
                imgui.push_item_width(300)
            except Exception:
                pass
            new_search = _input_text(f"Search slot###legit_slot_search_{slot_idx}_{table}", local_search, 128)
            try:
                imgui.pop_item_width()
            except Exception:
                pass
            if new_search != local_search:
                local_search = new_search
                if local_search.strip():
                    _legit_slot_search[search_key] = local_search
                else:
                    _legit_slot_search.pop(search_key, None)

        if local_search.strip():
            q_words = [w for w in re.split(r"\s+", local_search.strip().lower()) if w]
            def _matches_slot_query(part: dict) -> bool:
                hay = " ".join(str(part.get(k) or "") for k in ("key", "internal", "display", "debug", "row", "rarity", "serial_token"))
                try:
                    hay += " " + " ".join(str(x) for x in (part.get("name_parts") or part.get("np_names") or []))
                except Exception:
                    pass
                hay = hay.lower()
                return all(w in hay for w in q_words)
            allowed = [p for p in allowed_all if _matches_slot_query(p)]
        else:
            allowed = allowed_all

        if not allowed:
            _muted_wrapped("No slot-local search matches.")
            return

        if len(allowed_all) > 10:
            _muted_wrapped(f"{len(allowed)} / {len(allowed_all)} valid part(s). Use mouse wheel to scroll the page.")
        for p in allowed:
            line = _legit_part_line(p)
            already = line in selected_lines
            visible = _legit_part_display_label(p)
            can_add_duplicate = bool(_legit_unlock_rules)
            label_prefix = "+ " if (can_add_duplicate or not already) else "✓ "
            label = label_prefix + f"{visible}###legit_slot_pick_{slot_idx}_{p.get('serial')}_{p.get('key')}"
            if _legit_selectable_part_row(label, already and not can_add_duplicate, p) and (can_add_duplicate or not already):
                _legit_add_part_from_browser(p)
    finally:
        if child_open:
            _end_child_region()


def _legit_passive_base_key(key: str) -> str:
    """Collapse passive_x_y_tier_N into passive_x_y so max tier can replace lower tiers."""
    try:
        return re.sub(r"_tier_\d+$", "", str(key or "").strip().lower())
    except Exception:
        return str(key or "").strip().lower()


def _legit_max_passive_part_lines_for_root(root_key: str) -> tuple[list[str], int]:
    """Return one max-tier passive_points line for every passive available on this class mod root."""
    if _legit_builder is None or not root_key:
        return [], 0
    best: dict[str, tuple[int, str]] = {}
    scanned = 0
    try:
        parts = _legit_builder.search_parts(root_key, "passive_", table="passive_points", limit=2000)
    except Exception as exc:
        _log(f"Legit passive max scan failed for {root_key}: {exc!r}")
        return [], 0
    for part in parts:
        key = str(part.get("key") or part.get("internal") or "").strip()
        if not key.lower().startswith("passive_"):
            continue
        m = re.search(r"_tier_(\d+)$", key.lower())
        if not m:
            continue
        scanned += 1
        try:
            tier = int(m.group(1))
        except Exception:
            tier = 0
        base = _legit_passive_base_key(key)
        line = _legit_part_line(part)
        if not line:
            continue
        old = best.get(base)
        if old is None or tier > old[0]:
            best[base] = (tier, line)
    return [line for _tier, line in sorted(best.values(), key=lambda item: item[1].lower())], scanned


def _legit_apply_max_passive_points() -> None:
    """Unlock-mode helper: replace all selected passive bonuses with every max-tier passive for the selected class mod."""
    global _legit_status
    root = _legit_selected_root()
    if not root:
        _legit_status = "Choose a class mod root first."
        return
    if str(root.get("item_type") or "").lower() != "class_mod":
        _legit_status = "Max passive points is only available for class mods."
        return
    if not _legit_unlock_rules:
        _legit_status = "Turn on Unlock rules for modded gear before adding every passive."
        return
    root_key = str(root.get("key") or "")
    max_lines, scanned = _legit_max_passive_part_lines_for_root(root_key)
    if not max_lines:
        _legit_status = f"No passive_points parts found for {root_key}."
        return
    existing = _legit_selected_part_lines_raw()
    kept = [line for line in existing if not str(line).strip().lower().startswith("passive_points:")]
    _legit_set_selected_part_lines(kept + max_lines, preserve_duplicates=True)
    _legit_status = f"Added {len(max_lines)} max-tier passive point parts for {root.get('build_label') or root_key}. Replaced existing passive_points selections."

def _legit_validate_build(build: bool = False) -> None:
    global _legit_status, _legit_human, _legit_base85, _legit_signature_value
    if _legit_builder is None:
        _legit_status = "Legit builder core is not available."
        return
    root = _legit_selected_root()
    if not root:
        _legit_status = "No matching root selected."
        return
    root_key = str(root.get("key", ""))
    selected = _legit_selected_parts_lines()
    try:
        validation = _legit_builder.validate(root_key, selected)
        if _legit_unlock_rules:
            _legit_status = "Unlocked: rules bypassed for modded gear, including duplicate parts. Verify output against save-editor.be."
        elif not validation.get("ok"):
            _legit_status = "Invalid: " + "; ".join(validation.get("errors") or [])
            if not build:
                return
        else:
            _legit_status = f"Valid compact build: {validation.get('part_count', 0)} part(s)."
        _legit_human = _legit_builder.build_human(root_key, selected, level=int(_legit_level), seed=2, seed2=int(_legit_signature_value))
        _legit_base85 = _human_to_serial(_legit_human)
        if build and validation.get("ok") and not _legit_unlock_rules:
            _legit_status = "Built valid Base85 serial."
        elif build and _legit_unlock_rules:
            _legit_status = "Built unlocked Base85 serial with rules/duplicate checks bypassed. Verify output against save-editor.be."
    except Exception as exc:
        _legit_human = ""
        _legit_base85 = ""
        _legit_status = f"Legit build failed: {exc}"
        _log(f"Legit build failed: {exc!r}")


def _legit_root_key_for_serial(root_serial: int) -> str | None:
    if _legit_builder is None:
        return None
    try:
        rows = list(_legit_builder.all_roots())
    except Exception:
        try:
            rows = list(_legit_builder.roots())
        except Exception:
            rows = []
    for r in rows:
        try:
            if int(r.get("serial") or -1) == int(root_serial):
                return str(r.get("key") or "")
        except Exception:
            continue
    return None


def _legit_human_from_any_serial(text: str) -> str:
    raw = str(text or "").strip()
    if not raw:
        raise ValueError("empty serial")
    if raw.startswith("@U"):
        return _serial_to_human(raw)
    if raw.lower().startswith("decoded serial:"):
        return raw.split(":", 1)[1].strip()
    return raw


def _legit_extract_tokens_from_human(human: str) -> tuple[int, int, list[str]]:
    h = str(human or "").strip()
    m = re.match(r"\s*(\d+)\s*,\s*\d+\s*,\s*\d+\s*,\s*(\d+)\s*\|", h)
    if not m:
        raise ValueError("could not parse root serial/level from decoded serial")
    root_serial = int(m.group(1))
    level = int(m.group(2))
    # Keep exact serialized part tokens, including inherited RootSerial:SubSerial.
    tokens = re.findall(r"\{[^}]+\}", h)
    return root_serial, level, tokens


def _legit_token_list_values(token: str) -> list[int]:
    m = re.match(r"\{\s*\d+(?::\d+)?\s*:\s*\[([^\]]*)\]\s*\}", str(token or ""))
    if not m:
        return []
    vals: list[int] = []
    for part in re.findall(r"-?\d+", m.group(1)):
        try:
            vals.append(int(part))
        except Exception:
            pass
    return vals


def _legit_token_index(token: str) -> str:
    m = re.match(r"\{\s*(\d+)(?:\s*:\s*(?:\[|[-]?\d+))?", str(token or ""))
    return m.group(1) if m else ""


def _legit_cosmetic_selector_count(human: str) -> int:
    # NicNL human serials may end with a cosmetic selector payload such as:
    #   | "c", 70|
    # or:
    #   | "c", "Cosmetics_Weapon_Shiny_Jailbroken"|
    # This is legitimate metadata, not a malformed/modded tail.  The part-token
    # validator ignores it, but the obvious-modded sanity checks must not report
    # it as an extra payload.
    return len(re.findall(r'(?i)(?:^|[|,]\s*)"c"\s*,\s*(?:-?\d+|"(?:\\.|[^"])*")', str(human or "")))


def _legit_obvious_modded_errors(human: str, tokens: list[str]) -> list[str]:
    errors: list[str] = []
    toks = [str(t) for t in (tokens or [])]
    token_count = len(toks)

    # Legit game/catalog serials are compact.  Modded spam serials commonly pack
    # hundreds of parts or giant repeated arrays.  Keep these thresholds high so
    # normal items and cosmetic selector tails stay valid.
    if token_count > 64:
        errors.append(f"obvious modded serial: too many part tokens ({token_count} > 64)")

    from collections import Counter
    exact_counts = Counter(toks)
    dup_token, dup_count = exact_counts.most_common(1)[0] if exact_counts else ("", 0)
    # Serialized part tokens should be a set of selected parts.  Repeating the
    # exact same token is a strong modded/invalid signal and can make reward
    # packages fail on clients even when the loose structural validator can
    # still resolve the remaining parts.
    if dup_count > 1:
        errors.append(f"obvious modded serial: repeated part token {dup_token} x{dup_count}")

    idx_counts = Counter(_legit_token_index(t) for t in toks if _legit_token_index(t))
    idx, idx_count = idx_counts.most_common(1)[0] if idx_counts else ("", 0)
    if idx_count > 48:
        errors.append(f"obvious modded serial: part index {{{idx}}} appears {idx_count} time(s)")

    for t in toks:
        vals = _legit_token_list_values(t)
        if not vals:
            continue
        if len(vals) > 32:
            errors.append(f"obvious modded serial: packed part list {t[:48]}... has {len(vals)} value(s)")
            break
        vc = Counter(vals)
        val, n = vc.most_common(1)[0]
        if n > 1:
            errors.append(f"obvious modded serial: packed part list repeats value {val} x{n}")
            break

    # Do not flag cosmetic selector tails.  They are valid BL4 serial payloads.
    _ = _legit_cosmetic_selector_count(human)
    return errors



def _legit_expanded_token_count(tokens: list[str]) -> int:
    """Count actual part entries after expanding packed decoded tokens.

    This mirrors legit_builder_core._expand_serial_token for the validator UI.
    It lets us detect modded serials where most tokens are unknown/wrong-root
    and would otherwise be silently discarded before structural validation.
    """
    total = 0
    for tok in tokens or []:
        vals = _legit_token_list_values(str(tok))
        total += len(vals) if vals else 1
    return total



def _legit_explicit_root_sub_tokens(tokens: list[str]) -> list[tuple[int, int, str]]:
    out: list[tuple[int, int, str]] = []
    for tok in tokens or []:
        expanded_items = []
        try:
            if _legit_builder is not None and hasattr(_legit_builder, "_expand_serial_token"):
                expanded_items = list(_legit_builder._expand_serial_token(tok))
            else:
                expanded_items = [tok]
        except Exception:
            expanded_items = [tok]
        for expanded in expanded_items:
            m = re.match(r"\{\s*(\d+)\s*:\s*(-?\d+)\s*\}", str(expanded or ""))
            if not m:
                continue
            try:
                out.append((int(m.group(1)), int(m.group(2)), str(expanded)))
            except Exception:
                pass
    return out


def _legit_aux_cross_root_token_allowed(src_serial: int, sub_serial: int) -> bool:
    """Allow known global auxiliary serial roots used by save-editor-valid items.

    Some generated/heavy/ordnance serials legally carry explicit tokens from
    shared auxiliary roots that are not normal basetype ancestors of the item
    root. Examples from save-editor.be include Class Mod firmware
    ({234:79}/{234:84}) on heavy weapons and Grenade gadget element/stat/firmware
    ({245:...}) payloads. These are not cross-root weapon grafts and should not
    be treated like a Jakobs shotgun foregrip grafted onto a Torgue pistol.
    """
    try:
        src_key = _legit_root_key_for_serial(int(src_serial))
        if not src_key or _legit_builder is None:
            return False
        part = _legit_builder.describe_part(src_key, f"{{{int(sub_serial)}}}")
        if not part:
            return False
        src_key_n = str(src_key or "").strip().lower()
        table = str(part.get("table") or "").strip().lower()
        if src_key_n == "classmod" and table == "firmware":
            return True
        if src_key_n in {"grenade_gadget", "gadget"} and table in {"element", "stat_augment", "firmware"}:
            return True
    except Exception:
        return False
    return False

def _legit_unresolved_part_errors(validation: dict, tokens: list[str]) -> list[str]:
    errors: list[str] = []
    expanded = _legit_expanded_token_count(tokens)
    resolved = int((validation or {}).get("part_count") or 0)
    aux_allowed = 0
    for src, sub, _tok in _legit_explicit_root_sub_tokens(tokens):
        if _legit_aux_cross_root_token_allowed(src, sub):
            aux_allowed += 1
    effective_expanded = max(0, expanded - aux_allowed)
    missing = max(0, effective_expanded - resolved)
    # A valid decoded serial should resolve all normal/current-root parts.
    # Known save-editor auxiliary roots are ignored here because the flat legit
    # rules do not index them into every weapon root even though the game accepts
    # those payload tokens.
    if missing > 0:
        errors.append(f"obvious modded serial: {missing} normal part token(s) not found or wrong-root ({resolved}/{effective_expanded} resolved, {aux_allowed} aux ignored)")
    if effective_expanded > 0 and resolved == 0:
        errors.append("obvious modded serial: no serialized normal part tokens resolved")
    return errors


def _legit_allowed_root_serials_for_root(root_key: str) -> set[int]:
    """Root serials that may legally appear in part tokens for this root.

    Current-root tokens are written as {sub}.  Inherited parent inventory parts
    such as Weapon pearl/element slots are written as {ParentRootSerial:sub}.
    Any other explicit root serial is a cross-root graft and should fail bulk
    validation instead of being silently ignored.
    """
    allowed: set[int] = set()
    try:
        root = _legit_builder.get_root(root_key) if _legit_builder is not None else None
        seen: set[str] = set()
        while root:
            key = str(root.get("key") or "").strip().lower()
            if not key or key in seen:
                break
            seen.add(key)
            try:
                allowed.add(int(root.get("serial")))
            except Exception:
                pass
            ref = str(root.get("basetype") or "")
            if ref.lower().startswith("inv'") and "'" in ref[4:]:
                ref = ref.split("'", 2)[1]
            if "." in ref:
                ref = ref.split(".", 1)[0]
            ref = ref.strip().lower()
            if not ref:
                break
            root = _legit_builder.get_root(ref)
    except Exception:
        pass
    return allowed


def _legit_cross_root_token_errors(root_key: str, tokens: list[str]) -> list[str]:
    allowed = _legit_allowed_root_serials_for_root(root_key)
    if not allowed:
        return []
    errors: list[str] = []
    for tok in tokens or []:
        for expanded in (_legit_builder._expand_serial_token(tok) if _legit_builder is not None and hasattr(_legit_builder, "_expand_serial_token") else [tok]):
            m = re.match(r"\{\s*(\d+)\s*:\s*(-?\d+|\[)", str(expanded or ""))
            if not m:
                continue
            try:
                src = int(m.group(1))
                sub_text = str(m.group(2))
                sub = int(sub_text) if sub_text.lstrip("-").isdigit() else None
            except Exception:
                continue
            if src in allowed:
                continue
            if sub is not None and _legit_aux_cross_root_token_allowed(src, sub):
                continue
            errors.append(f"obvious modded serial: cross-root part token {{{src}:...}} is not valid for root {root_key}")
            return errors
    return errors

def _legit_validate_serial_text(text: str, index: int | None = None) -> str:
    prefix = f"#{index}: " if index is not None else ""
    if _legit_builder is None:
        return prefix + "ERROR - legit builder core unavailable"
    try:
        human = _legit_human_from_any_serial(text)
        root_serial, level, tokens = _legit_extract_tokens_from_human(human)
        root_key = _legit_root_key_for_serial(root_serial)
        if not root_key:
            return prefix + f"ERROR - unknown root serial {root_serial}"
        validation = _legit_builder.validate(root_key, tokens, strict_comp=False)
        errs = list(validation.get("errors") or [])
        # Do not promote broad dependency/exclusion warnings to hard failures in
        # the external serial validator.  Save-editor-valid generated/shiny items
        # can carry inherited tags which look conflicting in the flat rules, but
        # still load and deliver in-game.  True hard failures still come from
        # selected-comp disallowed parts, wrong-root/unresolved tokens, duplicates,
        # slot count breaks, and the explicit critical-conflict checks.
        errs.extend(_legit_cross_root_token_errors(root_key, tokens))
        errs.extend(_legit_unresolved_part_errors(validation, tokens))
        errs.extend(_legit_obvious_modded_errors(human, tokens))
        # A trailing cosmetic selector like | "c", 70| is valid metadata and is
        # intentionally ignored by the structural validator.
        status = "LEGIT" if not errs else "MODDED"
        detail = "" if not errs else " - " + "; ".join(str(e) for e in errs[:8])
        if len(errs) > 8:
            detail += f"; +{len(errs) - 8} more"
        return prefix + f"{status} root {root_serial} ({root_key}) level {level} parts {len(tokens)}{detail}"
    except Exception as exc:
        return prefix + f"ERROR - {exc}"


def _validator_set_progress(label: str, done: int = 0, total: int = 0, passed: int = 0, failed: int = 0, running: bool = True) -> None:
    with _validator_lock:
        _validator_progress.update({
            "running": bool(running),
            "label": str(label or ""),
            "done": int(done or 0),
            "total": int(total or 0),
            "passed": int(passed or 0),
            "failed": int(failed or 0),
        })


def _validator_progress_snapshot() -> dict[str, object]:
    with _validator_lock:
        return dict(_validator_progress)


def _draw_validator_progress() -> None:
    imgui = _blimgui.imgui
    progress = _validator_progress_snapshot()
    running = bool(progress.get("running", False))
    done = int(progress.get("done", 0) or 0)
    total = int(progress.get("total", 0) or 0)
    passed = int(progress.get("passed", 0) or 0)
    failed = int(progress.get("failed", 0) or 0)
    label = str(progress.get("label", "") or "Idle")
    if total > 0:
        text = f"{label} ({done}/{total})  legit {passed} / modded {failed}"
        frac = max(0.0, min(1.0, float(done) / float(total)))
    else:
        text = label
        frac = 0.0
    progress_bar = getattr(imgui, "progress_bar", None)
    if callable(progress_bar):
        try:
            progress_bar(frac, (520, 22), text)
        except Exception:
            try:
                progress_bar(frac, text)
            except Exception:
                imgui.text_wrapped(text)
    else:
        imgui.text_wrapped(text)
    if running:
        imgui.same_line()
        _button("Cancel###validator_cancel", _validator_cancel_current, "pink", 100, 0)


def _validator_worker(rows: list[str], mode: str) -> None:
    global _legit_basic_validation_output, _legit_bulk_validation_output, _validator_cancel, _validator_thread
    total = len(rows)
    passed = 0
    failed = 0
    lines: list[str] = []
    _validator_set_progress(f"Validating {mode}", 0, total, 0, 0, True)
    try:
        for i, row in enumerate(rows, 1):
            with _validator_lock:
                cancel = bool(_validator_cancel)
            if cancel:
                lines.append(f"Cancelled after {i - 1}/{total} serials.")
                break
            result = _legit_validate_serial_text(row, i if total != 1 else None)
            lines.append(result)
            if " LEGIT " in result or result.startswith("LEGIT") or result.startswith(f"#{i}: LEGIT"):
                passed += 1
            else:
                failed += 1
            if total == 1:
                _legit_basic_validation_output = result
            else:
                # Publish incremental output every row so the UI feels alive without
                # doing the validation on the render thread.
                _legit_bulk_validation_output = f"Bulk validation running: {passed} legit, {failed} modded/error, {i}/{total} total.\nShowing last 200 result lines only to keep BLImGui stable.\n" + "\n".join(lines[-200:])
            _validator_set_progress(f"Validating {mode}", i, total, passed, failed, True)
            try:
                time.sleep(0.001)
            except Exception:
                pass
        summary = f"{mode.capitalize()} validation: {passed} legit, {failed} modded/error, {min(total, passed + failed)} processed of {total}."
        if total == 1:
            if not lines:
                _legit_basic_validation_output = "Validation cancelled."
            elif bool(_validator_cancel):
                _legit_basic_validation_output = "Validation cancelled.\n" + "\n".join(lines)
            else:
                _legit_basic_validation_output = lines[-1]
        else:
            kept = lines if len(lines) <= 500 else ([f"Showing first 100 and last 400 of {len(lines)} result lines to keep BLImGui stable."] + lines[:100] + ["... output truncated in UI ..."] + lines[-400:])
            _legit_bulk_validation_output = summary + "\n" + "\n".join(kept)
        _validator_set_progress("Validation cancelled" if bool(_validator_cancel) else "Validation complete", passed + failed, total, passed, failed, False)
    except Exception as exc:
        msg = f"Validator thread error: {exc!r}"
        if total == 1:
            _legit_basic_validation_output = msg
        else:
            _legit_bulk_validation_output = msg + ("\n" + "\n".join(lines) if lines else "")
        _validator_set_progress("Validation error", passed + failed, total, passed, failed + 1, False)
        _log(msg)
    finally:
        with _validator_lock:
            _validator_cancel = False
            _validator_thread = None


def _validator_start(rows: list[str], mode: str) -> None:
    global _validator_thread, _validator_cancel
    if not rows:
        return
    with _validator_lock:
        if _validator_thread is not None and _validator_thread.is_alive():
            return
        _validator_cancel = False
        _validator_thread = threading.Thread(target=_validator_worker, args=(list(rows), str(mode or "bulk")), daemon=True)
        _validator_thread.start()


def _validator_cancel_current() -> None:
    global _validator_cancel
    with _validator_lock:
        _validator_cancel = True



def _mattmab_validator_label(e: dict[str, str]) -> str:
    status = str(e.get("mattmab_validator", "") or "").strip().upper()
    if status == "PASS":
        return "Mattmab Validation: Legit"
    if status == "FAIL":
        return "Mattmab Validation: Modded"
    if status == "ERROR":
        return "Mattmab Validation: Error"
    return "Mattmab Validation: not checked"


def _mattmab_validator_short(e: dict[str, str]) -> str:
    status = str(e.get("mattmab_validator", "") or "").strip().upper()
    if status == "PASS":
        return "[Legit]"
    if status == "FAIL":
        return "[Modded]"
    if status == "ERROR":
        return "[Validation Error]"
    return "[Unchecked]"


def _draw_mattmab_legit_modded_definition() -> None:
    _muted_wrapped("Mattmab Validation labels: Legit = the serial structure passed the conservative real-count/rule validator with no hard errors. Modded = the validator found hard structural problems such as wrong-root parts, unresolved parts, disallowed selected components, duplicate/slot-count breaks, or obvious cross-root modded tokens. Error = the serial could not be parsed/validated. This is a tooling classification, not a Gearbox/official authenticity guarantee.")


def _catalog_validator_set_progress(source: str, done: int, total: int, passed: int, failed: int, running: bool = True) -> None:
    with _catalog_validator_lock:
        _catalog_validator_progress.update({
            "running": bool(running),
            "source": str(source or ""),
            "done": int(done or 0),
            "total": int(total or 0),
            "passed": int(passed or 0),
            "failed": int(failed or 0),
        })


def _catalog_validator_snapshot() -> dict[str, object]:
    with _catalog_validator_lock:
        return dict(_catalog_validator_progress)


def _draw_catalog_validator_progress(source: str) -> None:
    imgui = _blimgui.imgui
    progress = _catalog_validator_snapshot()
    if str(progress.get("source", "")) != str(source or ""):
        return
    running = bool(progress.get("running", False))
    done = int(progress.get("done", 0) or 0)
    total = int(progress.get("total", 0) or 0)
    passed = int(progress.get("passed", 0) or 0)
    failed = int(progress.get("failed", 0) or 0)
    if not running and total <= 0:
        return
    text = f"Mattmab validating {source}: {done}/{total}  legit {passed} / modded {failed}" if total else f"Mattmab validating {source}"
    frac = 0.0 if total <= 0 else max(0.0, min(1.0, float(done) / float(total)))
    progress_bar = getattr(imgui, "progress_bar", None)
    if callable(progress_bar):
        try:
            progress_bar(frac, (520, 22), text)
        except Exception:
            try: progress_bar(frac, text)
            except Exception: imgui.text_wrapped(text)
    else:
        imgui.text_wrapped(text)
    if running:
        imgui.same_line(); _button("Cancel###catalog_validator_cancel_" + source, _catalog_validator_cancel_current, "pink", 90, 0)


def _catalog_validator_cancel_current() -> None:
    global _catalog_validator_cancel
    with _catalog_validator_lock:
        _catalog_validator_cancel = True



def _catalog_validator_flush_pending() -> None:
    global _gzo_status, _lootlemon_status
    if not _is_main_thread():
        return
    completed: list[tuple[str, dict[str, object]]] = []
    with _catalog_validator_lock:
        pending_by_source = {
            "GZO": dict(_catalog_validator_pending.get("GZO", {})),
            "Lootlemon": dict(_catalog_validator_pending.get("Lootlemon", {})),
        }
        _catalog_validator_pending["GZO"].clear()
        _catalog_validator_pending["Lootlemon"].clear()
        for src in ("GZO", "Lootlemon"):
            done = _catalog_validator_pending_complete.get(src)
            if done is not None:
                completed.append((src, dict(done)))
                _catalog_validator_pending_complete[src] = None

    for source, pending in pending_by_source.items():
        if not pending:
            continue
        entries = _gzo_entries if source == "GZO" else _lootlemon_entries
        by_id = {str(row.get("id", "")): row for row in entries}
        by_serial = {str(row.get("serial", "")): row for row in entries}
        for _key, patch in pending.items():
            live = by_id.get(str(patch.get("id", ""))) or by_serial.get(str(patch.get("serial", "")))
            if live is None:
                continue
            live["mattmab_validator"] = str(patch.get("status", ""))
            live["mattmab_validator_detail"] = str(patch.get("detail", ""))
            live["mattmab_validator_time"] = str(patch.get("time", ""))

    for source, info in completed:
        passed = int(info.get("passed", 0) or 0)
        failed = int(info.get("failed", 0) or 0)
        total = int(info.get("total", 0) or 0)
        cancelled = bool(info.get("cancelled", False))
        msg = f"Mattmab Validation {'cancelled' if cancelled else 'complete'} for {source}: {passed} legit, {failed} modded/error, {passed + failed}/{total} checked."
        if source == "GZO":
            try: _gzo_save_cache(_gzo_entries)
            except Exception as exc: msg += f" Cache save failed: {exc!r}"
            _gzo_status = msg
        else:
            try: _lootlemon_save_cache(_lootlemon_entries)
            except Exception as exc: msg += f" Cache save failed: {exc!r}"
            _lootlemon_status = msg
        _set_status_pill(msg, "green" if failed == 0 else "gold")
        _log(msg)

def _catalog_entry_validation(serial: str) -> tuple[str, str]:
    """Return (PASS/FAIL/ERROR, detail) using the same real-count validator path.

    Internal cache status stays PASS/FAIL for backwards compatibility, but UI renders
    those as Legit/Modded.
    """
    try:
        result = _legit_validate_serial_text(str(serial or ""), None)
        if result.startswith("LEGIT") or " LEGIT " in result or result.startswith("PASS") or " PASS " in result:
            return "PASS", result
        if result.startswith("MODDED") or " MODDED " in result or result.startswith("FAIL") or " FAIL " in result:
            return "FAIL", result
        return "ERROR", result
    except Exception as exc:
        return "ERROR", f"ERROR - {exc!r}"


def _catalog_validator_worker(source: str) -> None:
    global _catalog_validator_thread, _catalog_validator_cancel, _gzo_status, _lootlemon_status
    source = str(source or "")
    entries = _gzo_entries if source == "GZO" else _lootlemon_entries
    # Snapshot only the immutable data the worker needs.  The UI may draw/filter
    # the live catalog at the same time, so do not iterate/mutate live rows here.
    work = [(str(e.get("id", "")), str(e.get("serial", ""))) for e in list(entries)]
    total = len(work)
    passed = 0; failed = 0
    _catalog_validator_set_progress(source, 0, total, 0, 0, True)
    try:
        for i, (eid, serial) in enumerate(work, 1):
            with _catalog_validator_lock:
                if bool(_catalog_validator_cancel):
                    break
            status, detail = _catalog_entry_validation(serial)
            if status == "PASS":
                passed += 1
            else:
                failed += 1
            # Queue the row update.  _draw_ui flushes it on the game/UI thread.
            with _catalog_validator_lock:
                _catalog_validator_pending.setdefault(source, {})[eid or serial or str(i)] = {
                    "id": eid,
                    "serial": serial,
                    "status": status,
                    "detail": detail,
                    "time": str(int(time.time())),
                }
            _catalog_validator_set_progress(source, i, total, passed, failed, True)
            if i % 25 == 0:
                msg = f"Mattmab Validation running on {source}: {passed} legit, {failed} modded/error, {i}/{total}."
                if source == "GZO": _gzo_status = msg
                else: _lootlemon_status = msg
            try: time.sleep(0.001)
            except Exception: pass
        cancelled = bool(_catalog_validator_cancel)
        with _catalog_validator_lock:
            _catalog_validator_pending_complete[source] = {
                "passed": passed,
                "failed": failed,
                "total": total,
                "cancelled": cancelled,
            }
        _catalog_validator_set_progress(source, passed + failed, total, passed, failed, False)
    except Exception as exc:
        msg = f"Mattmab Validation error for {source}: {exc!r}"
        if source == "GZO": _gzo_status = msg
        else: _lootlemon_status = msg
        _catalog_validator_set_progress(source, passed + failed, total, passed, failed + 1, False)
        _log(msg)
    finally:
        with _catalog_validator_lock:
            _catalog_validator_cancel = False
            _catalog_validator_thread = None

def _catalog_validator_start(source: str) -> None:
    global _catalog_validator_thread, _catalog_validator_cancel, _gzo_status, _lootlemon_status
    source = str(source or "")
    entries = _gzo_entries if source == "GZO" else _lootlemon_entries
    if not entries:
        msg = f"Load {source} codes before running Mattmab Validation."
        if source == "GZO": _gzo_status = msg
        else: _lootlemon_status = msg
        _set_status_pill(msg, "red")
        return
    with _catalog_validator_lock:
        if _catalog_validator_thread is not None and _catalog_validator_thread.is_alive():
            _set_status_pill("Another catalog validation is already running.", "gold")
            return
        _catalog_validator_cancel = False
        _catalog_validator_thread = threading.Thread(target=_catalog_validator_worker, args=(source,), name=f"MSBT {source} Mattmab Validation", daemon=True)
        _catalog_validator_thread.start()
    if source == "GZO": _gzo_status = f"Queued Mattmab Validation for {len(entries)} GZO code(s)."
    else: _lootlemon_status = f"Queued Mattmab Validation for {len(entries)} Lootlemon code(s)."

def _legit_validate_basic_input() -> None:
    global _legit_basic_validation_output
    text = str(_legit_basic_validation_input or "").strip()
    if not text:
        _legit_basic_validation_output = "Paste one @U/Base85 or decoded human serial first."
        return
    _legit_basic_validation_output = "Queued basic validation..."
    _validator_start([text], "basic")


def _legit_validate_bulk_input() -> None:
    global _legit_bulk_validation_output
    rows = _parse_serial_text(_legit_bulk_validation_input)
    if not rows:
        _legit_bulk_validation_output = "Paste one serial per line first."
        return
    _legit_bulk_validation_output = f"Queued {len(rows)} serials for background validation..."
    _validator_start(rows, "bulk")


def _legit_clear_bulk_validator() -> None:
    global _legit_basic_validation_input, _legit_basic_validation_output, _legit_bulk_validation_input, _legit_bulk_validation_output
    _validator_cancel_current()
    _legit_basic_validation_input = ""
    _legit_basic_validation_output = "Paste one @U/Base85 or decoded human serial, then Validate Basic."
    _legit_bulk_validation_input = ""
    _legit_bulk_validation_output = "Paste one serial per line, then Validate Bulk."
    _validator_set_progress("Idle", 0, 0, 0, 0, False)


def _draw_validator_tab() -> None:
    global _legit_basic_validation_input, _legit_bulk_validation_input
    imgui = _blimgui.imgui
    opened = _begin_resizable_card("card_validator", "Validator", "cyan", _tab_card_height(700.0), 320, 1200) if _cyber else True
    if opened:
        _muted_wrapped("Validate one serial or a large pasted list. Validation runs on a background thread so the menu does not stall the game thread. Bulk input expects one serial per line.")
        _draw_mattmab_legit_modded_definition()
        _draw_legit_disclaimer()
        _draw_validator_progress()
        imgui.separator()
        imgui.text_wrapped("Basic validation")
        _legit_basic_validation_input = _input_text_multiline("Basic validation input###legit_basic_validation_input", _legit_basic_validation_input, 65536, width=860, height=80)
        _wrapped_button_row([
            ("Validate Basic###legit_validate_basic", _legit_validate_basic_input, "cyan", 150.0, 0.0),
            ("Clear Validator###legit_clear_validator", _legit_clear_bulk_validator, "pink", 150.0, 0.0),
        ], max_width=_imgui_available_width())
        _input_text_multiline("Basic validation result###legit_basic_validation_output", _legit_basic_validation_output, 65536, width=860, height=90)
        imgui.separator()
        imgui.text_wrapped("Bulk validation")
        _legit_bulk_validation_input = _input_text_multiline("Bulk validator input###legit_bulk_validation_input", _legit_bulk_validation_input, 262144, width=860, height=190)
        _wrapped_button_row([
            ("Validate Bulk###legit_validate_bulk", _legit_validate_bulk_input, "gold", 150.0, 0.0),
            ("Clear Validator###legit_clear_validator2", _legit_clear_bulk_validator, "pink", 150.0, 0.0),
        ], max_width=_imgui_available_width())
        _input_text_multiline("Bulk validation result###legit_bulk_validation_output", _legit_bulk_validation_output, 262144, width=860, height=230)
    if _cyber:
        _end_resizable_card()


def _legit_slots_for_root(root_key: str) -> list[str]:
    if _legit_builder is None:
        return []
    key = str(root_key or "")
    slots_cache = _legit_cache.get("slots", {})
    if key in slots_cache:
        return list(slots_cache[key])
    try:
        out = list(_legit_builder.slots(key))
    except Exception as exc:
        _log(f"Legit slot list failed for {key}: {exc!r}")
        out = []
    slots_cache[key] = out
    return list(out)

def _legit_give_active() -> None:
    global _legit_status
    if not _legit_base85.strip():
        _legit_validate_build(build=True)
    serial = _legit_base85.strip()
    if not serial:
        _legit_status = "No Base85 serial to give."
        return
    _legit_status = _deliver_serials_with_target([serial], "selected", "Legit Builder")


def _legit_give_all_active() -> None:
    global _legit_status
    if not _legit_base85.strip():
        _legit_validate_build(build=True)
    serial = _legit_base85.strip()
    if not serial:
        _legit_status = "No Base85 serial to give."
        return
    _legit_status = _deliver_serials_with_target([serial], "all", "Legit Builder")


def _legit_copy_output(label: str, text: str) -> None:
    global _legit_status
    value = str(text or "").strip()
    if not value:
        _legit_status = f"No {label} to copy. Build or validate first."
        return
    _copy_text_to_clipboard(label, value)
    _legit_status = f"Copied {label}."


def _legit_draw_copyable_output(label: str, text: str, imgui_label: str, height: int) -> None:
    imgui = _blimgui.imgui
    avail_w = max(360.0, _imgui_available_width(860.0))
    button_w = 90.0
    # Put the label and copy action in a compact header row above the text box.
    # Keeping controls out of the right edge prevents the output field from being
    # squeezed and makes the copy button visible on narrow windows.
    header_label = str(imgui_label).split("###", 1)[0].strip() or label
    try:
        imgui.text_wrapped(header_label)
        imgui.same_line()
    except Exception:
        pass
    _button(f"Copy###{imgui_label}_copy", lambda label=label, text=text: _legit_copy_output(label, text), "gold", button_w, 0)
    _input_text_multiline(imgui_label, str(text or ""), 65536, width=int(avail_w), height=height)


def _draw_legit_builder_tab() -> None:
    global _legit_root_search, _legit_root_index, _legit_type_index, _legit_manufacturer_index, _legit_part_search, _legit_part_table_index, _legit_slot_page, _legit_grid_hscroll
    global _legit_selected_parts_text, _legit_level, _legit_seed, _legit_signature_value, _legit_human, _legit_base85, _legit_unlock_rules, _legit_status
    imgui = _blimgui.imgui
    opened = _begin_resizable_card("card_legit_builder", "Stripped Legit Builder", "cyan", _tab_card_height(780.0), 360, 1400) if _cyber else True
    if opened:
        if _legit_builder is None:
            imgui.text_wrapped("Legit builder core did not load.")
            if _cyber: _end_resizable_card()
            return
        _muted_wrapped("Slot-first builder: choose Type first, then Manufacturer. The matching root is selected below, and each slot box shows only parts allowed by the currently active tags/rules. Start with inv_comp/rarity, then fill the remaining slots.")
        _draw_legit_disclaimer()
        old_unlock = bool(_legit_unlock_rules)
        _legit_unlock_rules = _checkbox("Unlock rules for modded gear###legit_unlock_rules", _legit_unlock_rules)
        if _legit_unlock_rules != old_unlock:
            _legit_clear_dynamic_cache()
            _legit_human = ""
            _legit_base85 = ""
            _legit_status = "Unlock enabled: builder will ignore legit part rules and allow duplicate parts." if _legit_unlock_rules else "Unlock disabled: builder is using legit part rules."
        if _legit_unlock_rules:
            _muted_wrapped("Unlock is for modded gear: part dependency, exclusion, slot-count, and duplicate-part rules are bypassed. You can add multiple copies of any part. Verify output against save-editor.be.")
        # Convenience for modded class mods: add one highest-tier passive_points
        # part for every passive available on the selected class mod character.
        # This is shown only in Unlock mode so legit builds are not accidentally
        # flooded with impossible passive bonuses.
        _preview_root = _legit_selected_root()
        if _legit_unlock_rules and _preview_root and str(_preview_root.get("item_type") or "").lower() == "class_mod":
            _button("Add All Max Passives###legit_add_all_max_passives", _legit_apply_max_passive_points, "purple", 220, 0)
            try:
                imgui.same_line()
            except Exception:
                pass
            _muted_wrapped("Adds every max-tier passive_points part for this class mod's character and replaces any currently selected passive_points rows.")
        types = _legit_type_options()
        old_type_index = _legit_type_index
        _legit_type_index = _combo("Type###legit_type_combo", max(0, min(_legit_type_index, max(0, len(types) - 1))), [_legit_pretty_label(t) for t in types] or ["No buildable types"])
        if _legit_type_index != old_type_index:
            _legit_manufacturer_index = 0
            _legit_root_index = 0
            _legit_slot_page = 0
            _legit_grid_hscroll = 0
            _legit_clear_dynamic_cache()
        item_type = types[max(0, min(_legit_type_index, len(types) - 1))] if types else ""
        mans = _legit_manufacturer_options(item_type) if item_type else []
        old_manufacturer_index = _legit_manufacturer_index
        _legit_manufacturer_index = _combo("Manufacturer###legit_manufacturer_combo", max(0, min(_legit_manufacturer_index, max(0, len(mans) - 1))), [_legit_pretty_label(m) for m in mans] or ["No manufacturers"])
        if _legit_manufacturer_index != old_manufacturer_index:
            _legit_root_index = 0
            _legit_slot_page = 0
            _legit_grid_hscroll = 0
            _legit_clear_dynamic_cache()
        old_root_search = _legit_root_search
        _legit_root_search = _input_text("Optional Root Filter###legit_root_search", _legit_root_search, 256)
        if _legit_root_search != old_root_search:
            _legit_root_index = 0
            _legit_clear_dynamic_cache()
        roots = _legit_root_options()
        labels = [f"#{r.get('serial')}  {r.get('build_label') or (r.get('name') or r.get('key'))}  [{r.get('key')}]" for r in roots] or ["No matching root for this type/manufacturer"]
        old_root_index = _legit_root_index
        _legit_root_index = _combo("Root Variant###legit_root_combo", max(0, min(_legit_root_index, max(0, len(labels) - 1))), labels)
        if _legit_root_index != old_root_index:
            _legit_slot_page = 0
            _legit_grid_hscroll = 0
            _legit_clear_dynamic_cache()
        root = _legit_selected_root()
        if root:
            root_key = str(root.get('key'))
            imgui.text_wrapped(f"Root: #{root.get('serial')} {root.get('build_label') or root.get('key')} | {root.get('key')} | total parts {len(root.get('parts') or [])}")
            old_part_search = _legit_part_search
            _legit_part_search = _input_text("Filter Available Parts###legit_part_search", _legit_part_search, 256)
            if _legit_part_search != old_part_search:
                try:
                    _legit_cache.get("allowed", {}).clear()
                except Exception:
                    pass
            base_tables = _legit_slots_for_root(root_key)
            slot_meta_map = _legit_slot_meta(root_key)
            tables = list(base_tables)
            for slot_name in slot_meta_map:
                if slot_name and slot_name not in tables:
                    tables.append(slot_name)
            if not tables:
                _muted_wrapped("No dependency slots were found for this root.")
            else:
                # Restore the desired card grid.  Use explicit same_line rows
                # instead of imgui.columns so each slot remains a bordered child panel.
                avail_w = max(260.0, _imgui_available_width(1180.0))
                if avail_w >= 1080.0:
                    visible_cols = 3
                elif avail_w >= 720.0:
                    visible_cols = 2
                else:
                    visible_cols = 1
                gap = 8.0
                slot_w = max(240.0, (avail_w - (gap * (visible_cols - 1))) / visible_cols - 2.0)
                imgui.text_wrapped(f"Slots 1-{len(tables)} of {len(tables)} | {visible_cols} columns")
                for slot_idx, table in enumerate(tables):
                    if slot_idx % visible_cols != 0:
                        try:
                            imgui.same_line()
                        except Exception:
                            pass
                    _legit_draw_slot_box(root_key, table, slot_idx, slot_meta_map.get(str(table).lower(), {}), slot_w)
        imgui.text_wrapped("Selected compact parts:")
        imgui.same_line()
        _button("Clear Selection###legit_clear_selection", _legit_clear_selected_parts, "pink", 150, 0)
        old_selected_text = _legit_selected_parts_text
        _legit_selected_parts_text = _input_text_multiline("Selected Parts###legit_parts", _legit_selected_parts_text, 65536, width=860, height=85)
        if _legit_selected_parts_text != old_selected_text:
            _legit_clear_dynamic_cache()
            _legit_human = ""
            _legit_base85 = ""
        try:
            imgui.push_item_width(90)
        except Exception:
            pass
        _legit_level = _clamped_int_input("Level###legit_level", _legit_level, 1, 60)
        imgui.same_line()
        old_sig = int(_legit_signature_value)
        _legit_signature_value = _clamped_int_input("Signature###legit_signature", _legit_signature_value, 1, 4095)
        if int(_legit_signature_value) != old_sig:
            save_extra_settings(legit_signature_value=int(_legit_signature_value))
            _legit_human = ""
            _legit_base85 = ""
        try:
            imgui.pop_item_width()
        except Exception:
            pass
        _draw_inline_target_selector("Builder Target")
        _wrapped_button_row([
            ("Validate", lambda: _legit_validate_build(False), "cyan", 120.0, 0.0),
            ("Build Base85", lambda: _legit_validate_build(True), "gold", 150.0, 0.0),
            ("Give Selected", _legit_give_active, "purple", 150.0, 0.0),
            ("Give All", _legit_give_all_active, "purple", 115.0, 0.0),
        ], max_width=_imgui_available_width())
        imgui.text_wrapped(_legit_status)
        _legit_draw_copyable_output("human serial", _legit_human, "Human Serial###legit_human", 70)
        _legit_draw_copyable_output("Base85 serial", _legit_base85, "Base85###legit_base85", 60)
    if _cyber:
        _end_resizable_card()


def _draw_item_pool_tab() -> None:
    global _itempool_search, _itempool_category, _itempool_selected_index, _itempool_count, _itempool_level, _itempool_page
    imgui = _blimgui.imgui
    opened = _begin_resizable_card("card_item_pool", "Item Pool Spawning", "gold", _tab_card_height(700.0), 320, 1200) if _cyber else True
    if opened:
        if _cyber:
            _muted_wrapped("Filter item pools, then spawn the selected pool near the local player. Turrets, terminals, and cosmetics are intentionally excluded.")
        else:
            imgui.text_wrapped("Filter item pools, then spawn the selected pool near the local player. Turrets, terminals, and cosmetics are intentionally excluded.")

        previous_search = _itempool_search
        _itempool_search = _input_text("Search Item Pools", _itempool_search, 256)
        if _itempool_search != previous_search:
            _itempool_page = 0
            _itempool_selected_index = 0

        try:
            imgui.push_item_width(120)
        except Exception:
            pass
        _itempool_level = _input_int_clamped("Level", _itempool_level, 1, 60)
        imgui.same_line()
        _itempool_count = _input_int_clamped("Quantity", _itempool_count, 1, 100)
        try:
            imgui.pop_item_width()
        except Exception:
            pass

        categories = item_pool_categories()
        if _itempool_category not in categories:
            _itempool_category = "All"
        row = 0
        for category in categories:
            accent = "gold" if category == "All" else ("cyan" if category in ("Assault Rifle", "Pistol", "SMG", "Sniper", "Shotgun", "Heavy") else "purple")
            _draw_category_button(category, accent)
            row += 1
            if row % 8 != 0:
                imgui.same_line()
        imgui.spacing()

        all_results = _current_itempool_all_results()
        total = len(all_results)
        max_page = max(0, (total - 1) // _ITEMPOOL_PAGE_SIZE) if total else 0
        _itempool_page = max(0, min(_itempool_page, max_page))
        results = _current_itempool_results()
        if _itempool_selected_index >= len(results):
            _itempool_selected_index = 0

        if results:
            selected = results[max(0, min(_itempool_selected_index, len(results) - 1))]
            start_num = _itempool_page * _ITEMPOOL_PAGE_SIZE + 1
            end_num = _itempool_page * _ITEMPOOL_PAGE_SIZE + len(results)
            status = f"Selected: {selected['itempool']} | Showing {start_num}-{end_num} of {total} | Page {_itempool_page + 1}/{max_page + 1}"
            if _cyber:
                _muted_wrapped(status)
            else:
                imgui.text_wrapped(status)

            def _first_page() -> None:
                global _itempool_page, _itempool_selected_index
                _itempool_page = 0
                _itempool_selected_index = 0
            def _prev_page() -> None:
                global _itempool_page, _itempool_selected_index
                _itempool_page = max(0, _itempool_page - 1)
                _itempool_selected_index = 0
            def _next_page() -> None:
                global _itempool_page, _itempool_selected_index
                _itempool_page = min(max_page, _itempool_page + 1)
                _itempool_selected_index = 0
            def _last_page() -> None:
                global _itempool_page, _itempool_selected_index
                _itempool_page = max_page
                _itempool_selected_index = 0

            _button("First", _first_page, "purple", 70, 0); imgui.same_line()
            _button("Prev", _prev_page, "purple", 70, 0); imgui.same_line()
            _button("Next", _next_page, "purple", 70, 0); imgui.same_line()
            _button("Last", _last_page, "purple", 70, 0)

            child_open = _begin_child_region("msbt_itempool_scroll_list", _resizable_height("child_itempool_list", "Item pool list", _remaining_child_height(360.0, 60.0), 180, 1000))
            visible_rows = results if child_open else results[:18]
            for index, entry in enumerate(visible_rows):
                fav = _fav_prefix(str(entry.get('itempool', '')), _favorite_itempools)
                label = f"{fav}[{entry['category']}] {entry['display_name']}{_fav_description(str(entry.get('itempool', '')), _favorite_itempool_descriptions)}###itempool_{_itempool_page}_{index}"
                if _selectable_row(label, index == _itempool_selected_index):
                    _itempool_selected_index = index
            if child_open:
                _end_child_region()
            elif len(results) > len(visible_rows):
                imgui.text_wrapped(f"Showing first {len(visible_rows)} result(s) on this page; narrow search for more.")
            selected_pool_name = str(selected.get("itempool", ""))
            fav_label = "Unfavorite Selected" if selected_pool_name in _favorite_itempools else "Favorite Selected"
            _button(fav_label, _toggle_selected_itempool_favorite, "purple", 170, 0); imgui.same_line()
            _button("Spawn Selected Item Pool", _spawn_selected_item_pool, "gold", 250, 0)
            _draw_favorite_description_editor("Favorite Description##itempool_fav_desc", selected_pool_name, _favorite_itempools, _favorite_itempool_descriptions)
        else:
            if _cyber:
                _muted_wrapped("No item pools match the current search/category.")
            else:
                imgui.text_wrapped("No item pools match the current search/category.")
    if _cyber:
        _end_resizable_card()



def _current_travel_map_results() -> list[dict[str, str]]:
    return _sort_favorites_first(filter_travel_maps(_travel_map_search, limit=80), "map", _favorite_travel_maps)


def _selected_travel_map_name() -> str:
    results = _current_travel_map_results()
    if not results:
        return ""
    idx = max(0, min(_travel_selected_map_index, len(results) - 1))
    return results[idx]["map"]


def _current_travel_station_results() -> list[dict[str, str]]:
    map_name = "" if _travel_show_all_stations else _selected_travel_map_name()
    return _sort_favorites_first(filter_travel_stations(map_name, _travel_station_search, limit=0), "station", _favorite_travel_stations)


def _travel_to_selected_map() -> None:
    global _travel_selected_map_index
    results = _current_travel_map_results()
    if not results:
        _log("No map selected.")
        return
    _travel_selected_map_index = max(0, min(_travel_selected_map_index, len(results) - 1))
    row = results[_travel_selected_map_index]
    # Server travel tears down HUD/World objects. Forget native HUD pill wrappers
    # before travel and block new HUD-pill writes while the next map loads.
    _hud_suppress_native(18.0)
    _log(travel_to_map(row["map"]))


def _travel_to_selected_station() -> None:
    global _travel_selected_station_index
    results = _current_travel_station_results()
    if not results:
        _log("No travel station selected.")
        return
    _travel_selected_station_index = max(0, min(_travel_selected_station_index, len(results) - 1))
    row = results[_travel_selected_station_index]
    _hud_suppress_native(18.0)
    _log(travel_to_station(row["station"]))



def _travel_visible_row_count(default_rows: int = 12) -> int:
    """Rows to show in safe non-child scroll windows.

    We avoid BeginChild here because this BLImGui build has crashed on child-size
    overloads.  A manual slider gives the same small-screen behavior without
    opening an ImGui child stack.
    """
    try:
        avail = _imgui_available_height(640.0)
        return max(6, min(22, int((float(avail) - 260.0) / 20.0)))
    except Exception:
        return int(default_rows)


def _draw_manual_scrolled_selectable_list(
    title: str,
    rows: list[dict[str, str]],
    selected_index: int,
    offset: int,
    visible_count: int,
    id_prefix: str,
    label_fn: Callable[[dict[str, str], int], str],
) -> tuple[int, int]:
    """Draw one real vertical wheel-scroll area for a travel list.

    Map Travel has two independent scroll regions: one under MAPS and one under
    TRAVEL STATIONS.  Do not use fake horizontal sliders here; ImGui child
    regions provide normal mouse-wheel vertical scrolling for each list.
    """
    imgui = _blimgui.imgui
    total = len(rows)
    if total <= 0:
        return 0, 0
    selected_index = _clamp_int(int(selected_index), 0, total - 1)
    row_h = 20.0
    try:
        # Keep each list compact. The map list is usually short; the station
        # list can be long, so callers pass a larger visible_count.
        height = max(92.0, min(360.0, float(max(4, int(visible_count))) * row_h + 10.0))
    except Exception:
        height = 180.0
    imgui.text_wrapped(f"Showing {total} item(s). Scroll this list with the mouse wheel.")
    child_open = _begin_child_region(f"msbt_{id_prefix}_vertical_scroll", height)
    try:
        for index, entry in enumerate(rows):
            if _selectable_row(label_fn(entry, index), index == selected_index):
                selected_index = index
    finally:
        if child_open:
            _end_child_region()
    return selected_index, 0

def _draw_travel_tab() -> None:
    global _travel_map_search, _travel_station_search, _travel_selected_map_index, _travel_selected_station_index, _travel_map_scroll_offset, _travel_station_scroll_offset, _travel_show_all_stations
    imgui = _blimgui.imgui
    opened = _begin_resizable_card("card_map_travel", "Map Travel", "cyan", _tab_card_height(760.0), 320, 1200) if _cyber else True
    if opened:
        if _cyber:
            _muted_wrapped("Select a map first, then choose a travel station on that map. Travel commands are host-side server travel helpers.")
        else:
            imgui.text_wrapped("Select a map first, then choose a travel station on that map. Travel commands are host-side server travel helpers.")

        old_map_search = _travel_map_search
        _travel_map_search = _input_text("Search Maps", _travel_map_search, 256)
        if old_map_search != _travel_map_search:
            _travel_map_scroll_offset = 0
            _travel_selected_map_index = 0
            _travel_selected_station_index = 0
            _travel_station_scroll_offset = 0
        map_results = _current_travel_map_results()
        if _travel_selected_map_index >= len(map_results):
            _travel_selected_map_index = 0
        selected_map = _selected_travel_map_name()
        if _cyber:
            _cyber.section_header("Maps", "cyan")
        else:
            imgui.separator(); imgui.text("MAPS")
        if map_results:
            selected_row = map_results[max(0, min(_travel_selected_map_index, len(map_results) - 1))]
            if _cyber:
                _muted_wrapped(f"Selected map: {selected_row['map']} | Showing {len(map_results)} map(s).")
            else:
                imgui.text_wrapped(f"Selected map: {selected_row['map']} | Showing {len(map_results)} map(s).")
            def _map_label(entry: dict[str, str], index: int) -> str:
                fav = _fav_prefix(str(entry.get('map', '')), _favorite_travel_maps)
                return f"{fav}{entry['display_name']}{_fav_description(str(entry.get('map', '')), _favorite_travel_map_descriptions)}###travel_map_{index}"
            previous_map_index = _travel_selected_map_index
            _travel_selected_map_index, _travel_map_scroll_offset = _draw_manual_scrolled_selectable_list(
                "Map list",
                map_results,
                _travel_selected_map_index,
                _travel_map_scroll_offset,
                max(6, min(12, _travel_visible_row_count(10))),
                "travel_maps",
                _map_label,
            )
            if previous_map_index != _travel_selected_map_index:
                _travel_selected_station_index = 0
                _travel_station_scroll_offset = 0
            selected_map_name = str(selected_row.get("map", ""))
            map_fav_label = "Unfavorite Map" if selected_map_name in _favorite_travel_maps else "Favorite Map"
            _button(map_fav_label, _toggle_selected_map_favorite, "purple", 140, 0); imgui.same_line()
            _button("Travel to Selected Map", _travel_to_selected_map, "cyan", 240, 0)
            _draw_favorite_description_editor("Favorite Description##travel_map_fav_desc", selected_map_name, _favorite_travel_maps, _favorite_travel_map_descriptions)
        else:
            imgui.text_wrapped("No maps match the current search.")

        imgui.spacing()
        old_station_search = _travel_station_search
        _travel_station_search = _input_text("Search Travel Stations", _travel_station_search, 256)
        if old_station_search != _travel_station_search:
            _travel_station_scroll_offset = 0
            _travel_selected_station_index = 0
        old_show_all = _travel_show_all_stations
        _travel_show_all_stations = _checkbox("Show All Travel Stations", _travel_show_all_stations)
        if old_show_all != _travel_show_all_stations:
            _travel_selected_station_index = 0
            _travel_station_scroll_offset = 0
            save_extra_settings(travel_show_all_stations=bool(_travel_show_all_stations))
        station_results = _current_travel_station_results()
        if _travel_selected_station_index >= len(station_results):
            _travel_selected_station_index = 0
        if _cyber:
            _cyber.section_header("Travel Stations", "gold")
        else:
            imgui.separator(); imgui.text("TRAVEL STATIONS")
        if station_results:
            selected_station = station_results[max(0, min(_travel_selected_station_index, len(station_results) - 1))]
            if _cyber:
                _muted_wrapped(f"Selected station: {selected_station['station']} [{selected_station.get('category','Standard')}] | Showing {len(station_results)} station(s){' across all maps' if _travel_show_all_stations else ' for ' + (selected_map or 'selected map')}.")
            else:
                imgui.text_wrapped(f"Selected station: {selected_station['station']} | Showing {len(station_results)} station(s){' across all maps' if _travel_show_all_stations else ''}.")
            def _station_label(entry: dict[str, str], index: int) -> str:
                fav = _fav_prefix(str(entry.get('station', '')), _favorite_travel_stations)
                return f"{fav}{entry['display_name']}{_fav_description(str(entry.get('station', '')), _favorite_travel_station_descriptions)}###travel_station_{index}"
            _travel_selected_station_index, _travel_station_scroll_offset = _draw_manual_scrolled_selectable_list(
                "Station list",
                station_results,
                _travel_selected_station_index,
                _travel_station_scroll_offset,
                max(8, min(24, _travel_visible_row_count(16))),
                "travel_stations",
                _station_label,
            )
            selected_station_name = str(selected_station.get("station", ""))
            station_fav_label = "Unfavorite Station" if selected_station_name in _favorite_travel_stations else "Favorite Station"
            _button(station_fav_label, _toggle_selected_station_favorite, "purple", 160, 0); imgui.same_line()
            _button("Travel to Selected Station", _travel_to_selected_station, "gold", 260, 0)
            _draw_favorite_description_editor("Favorite Description##travel_station_fav_desc", selected_station_name, _favorite_travel_stations, _favorite_travel_station_descriptions)
        else:
            imgui.text_wrapped("No travel stations match the selected map/search.")
    if _cyber:
        _end_resizable_card()

def _draw_ui() -> None:
    global _UI_THREAD_IDENT, _selected_player_index, _serial_text, _currency_amount, _currency_kind_index, _exp_level, _exp_track_index, _custom_game_title
    if _UI_THREAD_IDENT is None:
        try:
            _UI_THREAD_IDENT = threading.get_ident()
        except Exception:
            pass
    _flush_worker_log_lines()
    _catalog_validator_flush_pending()
    _poll_lootlemon_refresh_result()
    _poll_gzo_refresh_result()
    _poll_serial_delivery_status_for_pill()
    imgui = _blimgui.imgui
    style_count = _cyber.push_cyber_window_style() if _cyber else 0
    try:
        visible, open_state = imgui.begin(WINDOW_TITLE, True)
    finally:
        if style_count:
            imgui.pop_style_color(style_count)

    if open_state is False:
        matts_sdk_boosting_tools_close()
        imgui.end()
        return

    if visible:
        _apply_game_window_title(_custom_game_title)
        if _cyber:
            _cyber.title("Matt's SDK Boosting Tools", "Boost smarter. Not harder.")
            _muted_wrapped("Select a player and apply boosts, rewards, currency, XP, SDUs, and serials.")
        else:
            imgui.text("MATT'S SDK BOOSTING TOOLS")
            imgui.text_wrapped("Boost smarter. Not harder.")
            imgui.text_wrapped("Select a player and apply boosts, rewards, currency, XP, SDUs, and serials.")

        _draw_custom_game_title_control()

        players = _party_players_for_ui()
        labels = [f"[{idx}] {name}" for idx, name in players] or ["No party players found"]

        imgui.separator()
        imgui.text("By Mattmab")
        imgui.text_wrapped("If you like what I do, consider supporting me on Ko-fi.")
        _button(
            "Support on Ko-fi",
            lambda: unrealsdk.find_class("/Script/Engine.KismetSystemLibrary").ClassDefaultObject.LaunchURL("https://ko-fi.com/mattmab"),
            "gold",
            170,
            0,
        )
        imgui.separator()

        _draw_tabs()
        _draw_status_pill()

        def _draw_active_tab_content() -> None:
            if _active_tab == 0:
                _draw_target_bar(players, labels)
                _draw_quick_max()
                _draw_three_column_boosting()
            elif _active_tab == 1:
                _draw_serial_tools_tab()
            elif _active_tab == 2:
                _draw_serial_store_tab()
            elif _active_tab == 3:
                _draw_gzo_codes_tab()
            elif _active_tab == 4:
                _draw_legit_builder_tab()
            elif _active_tab == 5:
                _draw_validator_tab()
            elif _active_tab == 6:
                _draw_item_pool_tab()
            elif _active_tab == 7:
                _draw_travel_tab()
            elif _active_tab == 8:
                _draw_movement_tab()
            else:
                _draw_log_card(full_page=True)

        # Every tab gets a manual horizontal viewport.  This helps 720p/handheld
        # screens reach wide cards, tables, and input fields without relying on
        # platform-specific ImGui horizontal scroll flags.
        _draw_tab_viewport(_active_tab, _draw_active_tab_content, 1180.0)

        if _cyber:
            imgui.separator()
            _muted_wrapped("Matt's SDK Boosting Tools  |  Made for boosters, by a booster")

    imgui.end()


def matts_sdk_boosting_tools_open() -> None:
    try:
        _apply_game_window_title(_custom_game_title)
        _get_blimgui_window_hub().register(WINDOW_TITLE, _draw_ui, width=980, height=760)
    except Exception as exc:
        _log(f"failed to open BLImGui host: {exc!r}")


def matts_sdk_boosting_tools_close() -> None:
    # The HUD status pill is hosted through AddToViewport, not inside the BLImGui
    # window.  Clear it explicitly whenever the SDK Boosting Tools panel closes so
    # no orphan viewport overlay sticks around after the menu is gone.
    try:
        _get_blimgui_window_hub().unregister(WINDOW_TITLE)
    finally:
        try:
            _hud_clear_viewport_pill_overlay()
        except Exception:
            pass


@keybind("Open Matt's SDK Boosting Tools")
def matts_sdk_boosting_tools_toggle() -> None:
    hub = _get_blimgui_window_hub()
    if hub.is_open(WINDOW_TITLE):
        matts_sdk_boosting_tools_close()
    else:
        matts_sdk_boosting_tools_open()


@command("msbt_panel", description="Open Matt's SDK Boosting Tools BLImGui panel.")
def _cmd_msbt_panel(_) -> None:
    matts_sdk_boosting_tools_open()

@command("msbt_imgui_join_safe", description="Toggle Matt's SDK Boosting Tools BLImGui join-safe pause for AMD/OpenGL crashes.")
def _cmd_msbt_imgui_join_safe(_) -> None:
    global _blimgui_join_safe_mode
    _blimgui_join_safe_mode = not bool(_blimgui_join_safe_mode)
    state = "ON" if _blimgui_join_safe_mode else "OFF"
    _log(f"BLImGui join-safe mode {state}")
    _set_status_pill(f"BLImGui join-safe mode {state}", "cyan", 4.0)

@command("msbt_imgui_pause", description="Pause Matt's SDK Boosting Tools BLImGui drawing for a few seconds.")
def _cmd_msbt_imgui_pause(args) -> None:
    global _blimgui_draw_paused_until
    try:
        seconds = float(str(args).strip() or "5")
    except Exception:
        seconds = 5.0
    seconds = max(1.0, min(30.0, seconds))
    _blimgui_draw_paused_until = time.monotonic() + seconds
    _log(f"BLImGui draw paused for {seconds:.1f}s")
    _set_status_pill(f"BLImGui draw paused {seconds:.0f}s", "gold", min(seconds, 6.0))


@command("msbt_hud_pill_test", description="Show a test MattsSDKBoostingTools HUD action pill.")
def _cmd_msbt_hud_pill_test(_) -> None:
    _set_status_pill("BOOSTINGTOOLS HUD PILL TEST", "cyan", 5.0)
    _log("HUD pill test requested")


@command("msbt_hud_pill_reset_original", description="Reset MattsSDKBoostingTools HUD pill cached widgets.")
def _cmd_msbt_hud_pill_reset_original(_) -> None:
    _hud_clear_viewport_pill_overlay()
    _set_status_pill("HUD pill cache reset", "cyan", 5.0)
    _log("HUD pill cache reset requested")


@command("msbt_hud_pill_viewport_reset", description="Reset the AddToViewport HUD pill overlay.")
def _cmd_msbt_hud_pill_viewport_reset(_) -> None:
    _hud_clear_viewport_pill_overlay()
    _log("HUD pill viewport overlay cleared")


@command("msbt_hud_pill_force_clear", description="Immediately remove visible HUD pill widgets and clear the viewport overlay.")
def _cmd_msbt_hud_pill_force_clear(_) -> None:
    _hud_clear_viewport_pill_overlay()
    _log("HUD pill force-cleared")

@command("msbt_hud_pill_viewport_test", description="Show a test using the AddToViewport HUD pill overlay.")
def _cmd_msbt_hud_pill_viewport_test(_) -> None:
    _set_status_pill("AddToViewport HUD pill test", "cyan", 8.0)
    _log("AddToViewport HUD pill test requested")
