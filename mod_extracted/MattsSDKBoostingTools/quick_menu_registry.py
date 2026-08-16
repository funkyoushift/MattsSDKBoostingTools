"""Bridge-safe Quick Menu catalog, validation, and persistence.

This module intentionally has no Unreal, BLImGui, or UI imports. Both the
native UMG menu and the external bridge use it as the single layout source.
"""

from __future__ import annotations

import copy
import re
from typing import Any

from .inventory_capacity import clamp_container_size, load_inventory_settings, save_extra_settings

MAX_PAGES = 5
SLOTS_PER_PAGE = 21  # 3 cols x 7 rows — leaves bottom dock space for rarity controls
GRID_COLS = 3
GRID_ROWS = 7
MAX_CUSTOM_LABEL_LEN = 48
SCHEMA_VERSION = 3
LEGACY_SLOTS_PER_PAGE = 12

WINDOW_SCALE_MIN = 0.6
WINDOW_SCALE_MAX = 1.8
WINDOW_SCALE_STEP = 0.1
WINDOW_SCALE_DEFAULT = 1.0

THEME_IDS: tuple[str, ...] = (
    "msbt_bright",
    "msbt",
    "blackberry",
    "azzy_purple",
    "basic_default",
    "arctic",
    "inferno",
    "void",
    "explosive",
    "healing",
    "fortress",
    "legendary",
    "mystic",
    "scooters",
    "cosmic",
    "midnight",
    "venom",
    "skullmasher",
    "lootlobby",
    "rat_bastard",
    "playas_darkness",
    "halloween",
    "merry_mephisto",
)

THEME_LABELS: dict[str, str] = {
    "msbt_bright": "MSBT Neon (Azzy)",
    "msbt": "MSBT Orange",
    "blackberry": "Blackberry",
    "azzy_purple": "Azzy Purple",
    "basic_default": "Basic Default",
    "arctic": "Arctic Blast",
    "inferno": "Inferno Flame",
    "void": "Void Shadow",
    "explosive": "Explosive Burst",
    "healing": "Healing Spring",
    "fortress": "Fortress Shield",
    "legendary": "Legendary Gold",
    "mystic": "Mystic Vault",
    "scooters": "Scooters Toolbox",
    "cosmic": "Cosmic Plasma",
    "midnight": "Midnight Blue",
    "venom": "Venom",
    "skullmasher": "Skullmasher",
    "lootlobby": "Lootlobby Queen",
    "rat_bastard": "Rat Bastard",
    "playas_darkness": "Playa's Darkness",
    "halloween": "Halloween",
    "merry_mephisto": "Merry Mephisto",
}

DEFAULT_CHROME: dict[str, Any] = {
    # New installs / unset chrome only — existing saved theme_id is preserved.
    "theme_id": "msbt_bright",
    "window_scale": WINDOW_SCALE_DEFAULT,
    "offset_x": 0.0,
    "offset_y": 0.0,
    "panel_opacity": 1.0,
    # F7 rarity slider strip — off until equipped from the ★ QM editor.
    "rarity_panel_equipped": False,
}

# UE KeyName allow-list for per-slot Quick Menu hotkeys (camera-tick polled).
HOTKEY_KEY_NAMES: tuple[str, ...] = (
    *tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
    "Zero",
    "One",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
    "NumPadZero",
    "NumPadOne",
    "NumPadTwo",
    "NumPadThree",
    "NumPadFour",
    "NumPadFive",
    "NumPadSix",
    "NumPadSeven",
    "NumPadEight",
    "NumPadNine",
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F8",
    "F9",
    "F10",
    "F11",
    "F12",
    "Tab",
    "Enter",
    "SpaceBar",
    "BackSpace",
    "Delete",
    "Insert",
    "Home",
    "End",
    "PageUp",
    "PageDown",
    "Left",
    "Right",
    "Up",
    "Down",
    "LeftShift",
    "RightShift",
    "LeftControl",
    "RightControl",
    "LeftAlt",
    "RightAlt",
    "CapsLock",
    "Semicolon",
    "Equals",
    "Comma",
    "Hyphen",
    "Period",
    "Slash",
    "Tilde",
    "LeftBracket",
    "Backslash",
    "RightBracket",
    "Apostrophe",
)

HOTKEY_RESERVED: frozenset[str] = frozenset({"F6", "F7", "Escape"})

HOTKEY_DISPLAY_ALIASES: dict[str, str] = {
    "Zero": "0",
    "One": "1",
    "Two": "2",
    "Three": "3",
    "Four": "4",
    "Five": "5",
    "Six": "6",
    "Seven": "7",
    "Eight": "8",
    "Nine": "9",
    "SpaceBar": "Space",
    "LeftControl": "LCtrl",
    "RightControl": "RCtrl",
    "LeftShift": "LShift",
    "RightShift": "RShift",
    "LeftAlt": "LAlt",
    "RightAlt": "RAlt",
    "NumPadZero": "Num0",
    "NumPadOne": "Num1",
    "NumPadTwo": "Num2",
    "NumPadThree": "Num3",
    "NumPadFour": "Num4",
    "NumPadFive": "Num5",
    "NumPadSix": "Num6",
    "NumPadSeven": "Num7",
    "NumPadEight": "Num8",
    "NumPadNine": "Num9",
}

ACTION_CATALOG: dict[str, dict[str, Any]] = {
    "max_all": {"basic": "Max All", "aliases": ["MAX", "MaxAll"]},
    "max_currency": {"basic": "Max Currency", "aliases": ["Cash", "MaxCash"]},
    "max_eridium": {"basic": "Max Eridium", "aliases": ["Eridium", "MaxE"]},
    "max_sdu": {"basic": "Max SDU", "aliases": ["SDU"]},
    "max_player_level": {"basic": "Max Level", "aliases": ["Lvl60", "Level"]},
    "max_spec_level": {"basic": "Max Spec", "aliases": ["Spec"]},
    "give_currency": {"basic": "Give Currency", "aliases": ["Currency"]},
    "set_level": {"basic": "Set Level", "aliases": ["Level"]},
    "open_golden_chest": {"basic": "Open Chest", "aliases": ["OpenGC", "Chest"]},
    "close_golden_chest": {"basic": "Close Chest", "aliases": ["CloseGC"]},
    "open_bank": {"basic": "Open Bank", "aliases": ["Bank"]},
    "drop_all_shinies": {"basic": "Drop Shinies", "aliases": ["Shinies", "DropAll"]},
    "shiny_selected": {"basic": "Shinies Selected", "aliases": ["Shiny Sel"]},
    "shiny_all": {"basic": "Shinies All", "aliases": ["Shiny All"]},
    "shiny_nonhost": {"basic": "Shinies Non-Host", "aliases": ["Shiny NH"]},
    "spawn_itempool": {"basic": "Spawn Item Pool", "aliases": ["Spawn Pool", "ItemPool"]},
    "give_serial_selected": {"basic": "Give Serial Selected", "aliases": ["Serial Sel"]},
    "give_serial_all": {"basic": "Give Serial All", "aliases": ["Serial All"]},
    "give_serial_nonhost": {"basic": "Give Serial Non-Host", "aliases": ["Serial NH"]},
    "read_equipped_serials": {"basic": "Read Equipped Serials", "aliases": ["Read Equip", "Equip Serials"]},
    "read_backpack_serials": {"basic": "Read Backpack Serials", "aliases": ["Read Inv", "Backpack Serials"]},
    "read_inventory": {"basic": "Read Inventory", "aliases": ["Inventory", "Inv Browser"]},
    "repeat_last_drop": {"basic": "Repeat Last Drop", "aliases": ["Redo Drop", "RLD"]},
    "travel_to_map": {"basic": "Travel Map", "aliases": ["Map Travel"]},
    "travel_to_station": {"basic": "Travel Station", "aliases": ["Station"]},
    "location_bookmark_save": {"basic": "Save XYZ Bookmark", "aliases": ["Save Loc"]},
    "location_bookmark_go": {"basic": "Go XYZ Bookmark", "aliases": ["Go Loc"]},
    "location_bookmark_list": {"basic": "List XYZ Bookmarks", "aliases": ["List Loc"]},
    "uvh_boost_all": {"basic": "UVH Boost All", "aliases": ["UVH"]},
    "uvh_boost_cancel": {"basic": "Cancel UVH", "aliases": ["UVH Cancel"]},
    "toggle_debug_cam": {"basic": "Toggle Debug Cam", "aliases": ["Debug Cam"]},
    "teleport_debug_cam": {"basic": "Teleport Debug Cam", "aliases": ["Cam Teleport"]},
    "devperk_0": {"basic": "Give Experience", "aliases": ["XP"]},
    "devperk_1": {"basic": "Give 1M Cash", "aliases": ["1M Cash"]},
    "devperk_2": {"basic": "Give 100k Eridium", "aliases": ["100k E"]},
    "devperk_3": {"basic": "Kill All Enemies", "aliases": ["Kill All"]},
    "devperk_4": {"basic": "All Customs + Hovers", "aliases": ["Customs"]},
    "devperk_5": {"basic": "Infinite Ammo", "aliases": ["Inf Ammo"]},
    "devperk_6": {"basic": "Demigod", "aliases": ["God"]},
    "devperk_7": {"basic": "Spawn Leg/Epic Loot", "aliases": ["Leg Loot"]},
    "dev_spawner_spawnai": {"basic": "Spawn Actor", "aliases": ["Spawn AI", "ASD AI"]},
    "dev_spawner_spawn": {"basic": "Spawn Template", "aliases": ["ASD Spawn"]},
    "dev_spawner_lostloot": {"basic": "Spawn Lost Loot", "aliases": ["Lost Loot"]},
    "dev_spawner_activate_last": {"basic": "Activate Last Spawn", "aliases": ["ASD Activate"]},
    "dev_spawner_clear": {"basic": "Clear ASD Spawns", "aliases": ["ASD Clear"]},
    "dev_spawner_reaggro": {"basic": "Re-Aggro Spawns", "aliases": ["Reaggro"]},
    "hoard_start": {"basic": "Hoard Start", "aliases": ["Start Hoard", "Hoard"]},
    "hoard_stop": {"basic": "Hoard Stop", "aliases": ["Stop Hoard"]},
    "hoard_clear": {"basic": "Hoard Clear", "aliases": ["Clear Hoard"]},
    "movement_apply_all": {"basic": "Apply Movement", "aliases": ["Move Apply"]},
    "movement_reset_all": {"basic": "Reset Movement", "aliases": ["Move Reset"]},
    "movement_preset_fast": {"basic": "Fast Movement", "aliases": ["Fast"]},
    "movement_preset_veryfast": {"basic": "Very Fast Movement", "aliases": ["Very Fast"]},
    "movement_preset_moon": {"basic": "Moon Movement", "aliases": ["Moon"]},
    "movement_preset_wallwalk": {"basic": "Wall Walk", "aliases": ["WallWalk"]},
    "movement_preset_fastglide": {"basic": "Fast Glide", "aliases": ["Glide"]},
    "movement_toggle_no_target": {"basic": "Toggle No Target", "aliases": ["No Target"]},
    "movement_toggle_noclip": {"basic": "Toggle Noclip", "aliases": ["Noclip"]},
    "movement_players_only": {"basic": "Players Only", "aliases": ["Players"]},
    "movement_delete_ground_items": {"basic": "Clear Ground Loot", "aliases": ["Destroy Junk", "Hard Clear"]},
    "movement_hide_ground_loot": {"basic": "Clear Loot (Hide)", "aliases": ["Soft Clear", "Hide Loot"]},
    "movement_pull_ground_loot": {"basic": "Pull Loot Here", "aliases": ["Pull Loot", "TP Loot"]},
    "movement_super_dash": {"basic": "Super Dash (MSBT)", "aliases": ["Dash MSBT", "Dash"]},
    "movement_super_dash_toggle": {"basic": "Super Dash Toggle (MSBT)", "aliases": ["Dash Toggle MSBT"]},
    "movement_azzy_super_dash": {"basic": "Super Dash Fire (Azzy)", "aliases": ["Dash Azzy", "Azzy Dash"]},
    "movement_azzy_super_dash_toggle": {"basic": "Super Dash Toggle (Azzy)", "aliases": ["Dash Toggle Azzy"]},
    "movement_zero_vault": {"basic": "Zero Vault Costs", "aliases": ["Vault0"]},
    "movement_set_time": {"basic": "Set Time", "aliases": ["Time"]},
    "movement_reset_time": {"basic": "Reset Time", "aliases": ["Time 1x"]},
    "movement_infinite_jump_all_on": {"basic": "Inf Jump All ON", "aliases": ["IJ All On"]},
    "movement_infinite_jump_all_off": {"basic": "Inf Jump All OFF", "aliases": ["IJ All Off"]},
    "movement_infinite_jump_selected_on": {"basic": "Inf Jump Sel ON", "aliases": ["IJ Sel On"]},
    "movement_infinite_jump_selected_off": {"basic": "Inf Jump Sel OFF", "aliases": ["IJ Sel Off"]},
    "movement_infinite_jump_toggle_selected": {"basic": "Inf Jump Toggle", "aliases": ["IJ Toggle"]},
    "movement_teleport_to_slot": {"basic": "Teleport To Slot", "aliases": ["TP Slot"]},
    "movement_teleport_selected_to_me": {"basic": "TP Selected To Me", "aliases": ["TP To Me"]},
    "movement_teleport_me_to_selected": {"basic": "TP Me To Selected", "aliases": ["TP To Them"]},
    "movement_teleport_all_to_me": {"basic": "TP All To Me", "aliases": ["TP All"]},
    "combat_tuning_apply": {"basic": "Apply Combat Tuning", "aliases": ["Combat Apply"]},
    "combat_tuning_reapply": {"basic": "Reapply Combat Tuning", "aliases": ["Combat Reapply"]},
    "combat_tuning_reset": {"basic": "Reset Combat Tuning", "aliases": ["Combat Reset"]},
    "vehicle_preset_apply": {"basic": "Vehicle Preset", "aliases": ["Veh Preset"]},
    "vehicle_spawn": {"basic": "Spawn Vehicle", "aliases": ["Veh Spawn"]},
    "vehicle_catalog": {"basic": "Vehicle Catalog", "aliases": ["Veh List"]},
    "complete_challenges_cancel": {"basic": "Cancel Challenges", "aliases": ["Chal Cancel"]},
    "complete_challenges_status": {"basic": "Challenge Status", "aliases": ["Chal Status"]},
    "rarity_apply": {"basic": "Apply Rarity", "aliases": ["Rarity"]},
    "rarity_reset": {"basic": "Reset Rarity", "aliases": ["Rarity Reset"]},
    "rarity_only_legendary": {"basic": "Only Legendary", "aliases": ["Legendary"]},
    "rarity_only_pearlescent": {"basic": "Only Pearlescent", "aliases": ["Pearlescent"]},
    "cxp_on": {"basic": "Combat XP Mult On", "aliases": ["CXP On", "XP Mult On"]},
    "cxp_off": {"basic": "Combat XP Mult Off", "aliases": ["CXP Off"]},
    "cxp_toggle": {"basic": "Combat XP Mult", "aliases": ["CXP", "CombatXP Toggle", "XP Mult"]},
    "cxp_status": {"basic": "Combat XP Status", "aliases": ["CXP Status"]},
    "instant_drops_on": {"basic": "Instant Drops On", "aliases": ["Drops On"]},
    "instant_drops_off": {"basic": "Instant Drops Off", "aliases": ["Drops Off"]},
    "instant_drops_toggle": {"basic": "Instant Drops", "aliases": ["Drops", "ICH"]},
    "instant_drops_status": {"basic": "Instant Drops Status", "aliases": ["Drops Status"]},
    "instant_holds_on": {"basic": "Instant Holds On", "aliases": ["Holds On", "No Holds On"]},
    "instant_holds_off": {"basic": "Instant Holds Off", "aliases": ["Holds Off"]},
    "instant_holds_toggle": {"basic": "Instant Holds", "aliases": ["Holds", "No Holds"]},
    "instant_holds_status": {"basic": "Instant Holds Status", "aliases": ["Holds Status"]},
    "fog_of_war_clear": {"basic": "Clear Fog", "aliases": ["Fog Clear", "NoFog"]},
    "fog_of_war_on": {"basic": "Fog Hide On", "aliases": ["Fog On"]},
    "fog_of_war_off": {"basic": "Fog Hide Off", "aliases": ["Fog Off"]},
    "fog_of_war_toggle": {"basic": "Fog Hide Toggle", "aliases": ["Fog"]},
    "fog_of_war_status": {"basic": "Fog Status", "aliases": ["Fog Status"]},
    "set_backpack_bank_selected": {"basic": "Inv Selected 1k", "aliases": ["Inv Sel"]},
    "set_backpack_bank_all": {"basic": "Inv All Party 1k", "aliases": ["Inv All"]},
    "kick_player": {"basic": "Kick Selected", "aliases": ["Kick"]},
    "refresh_players": {"basic": "Refresh Players", "aliases": ["Refresh"]},
    "chaos_launch": {"basic": "Chaos Launch", "aliases": ["Launch", "Yeet"]},
    "chaos_drop_backpack": {"basic": "Drop All", "aliases": ["Drop Bag", "Drop Backpack", "Spill Bag"]},
    "chaos_empty_backpack": {"basic": "Chaos Empty Bag", "aliases": ["Empty Bag", "Delete Bag"]},
    "chaos_kill": {"basic": "Chaos Kill", "aliases": ["Kill"]},
    "chaos_ffyl": {"basic": "Chaos FFYL", "aliases": ["FFYL", "Down"]},
    "chaos_invert_look": {"basic": "Chaos Invert Look", "aliases": ["Invert"]},
    "chaos_lock_look": {"basic": "Chaos Lock Look", "aliases": ["No Look"]},
    "chaos_lock_move": {"basic": "Chaos Lock Move", "aliases": ["No Move"]},
    "chaos_lock_both": {"basic": "Chaos Lock Both", "aliases": ["Freeze"]},
    "chaos_unlock": {"basic": "Chaos Unlock", "aliases": ["Unlock Input"]},
    "reset_skills": {"basic": "Reset Skill Tree", "aliases": ["Respec", "Reset Skills", "Skill Reset"]},
}

for _tier in range(1, 8):
    ACTION_CATALOG[f"uvh_boost_tier_{_tier}"] = {
        "basic": f"UVH 1-{_tier}",
        "aliases": [f"UVH {_tier}"],
    }

ASSIGNABLE_ACTIONS: tuple[str, ...] = tuple(sorted(ACTION_CATALOG.keys()))

# Keep the native modal compact; the external editor exposes the full registry.
# Parameterized actions (spawn/travel/serial/rarity/movement apply) stay Electron-first.
NATIVE_PICKER_ACTIONS: tuple[str, ...] = (
    "max_all",
    "max_currency",
    "max_eridium",
    "max_sdu",
    "max_player_level",
    "max_spec_level",
    "open_golden_chest",
    "close_golden_chest",
    "open_bank",
    "drop_all_shinies",
    "shiny_selected",
    "shiny_all",
    "shiny_nonhost",
    "repeat_last_drop",
    "read_equipped_serials",
    "read_backpack_serials",
    "read_inventory",
    "uvh_boost_all",
    "movement_preset_fast",
    "movement_preset_veryfast",
    "movement_delete_ground_items",
    "movement_hide_ground_loot",
    "movement_pull_ground_loot",
    "movement_super_dash",
    "movement_super_dash_toggle",
    "movement_azzy_super_dash",
    "movement_azzy_super_dash_toggle",
    "movement_zero_vault",
    "movement_infinite_jump_all_on",
    "movement_infinite_jump_all_off",
    "rarity_only_legendary",
    "rarity_only_pearlescent",
    "cxp_toggle",
    "cxp_off",
    "instant_drops_toggle",
    "instant_drops_off",
    "instant_holds_toggle",
    "instant_holds_off",
    "fog_of_war_clear",
    "devperk_3",
    "devperk_7",
    "set_backpack_bank_selected",
    "set_backpack_bank_all",
    "kick_player",
    "refresh_players",
)

NEEDS_PLAYER_ACTIONS = frozenset({
    "max_all",
    "max_currency",
    "max_eridium",
    "max_sdu",
    "max_player_level",
    "max_spec_level",
    "give_currency",
    "set_level",
    "shiny_selected",
    "give_serial_selected",
    "read_equipped_serials",
    "read_backpack_serials",
    "read_inventory",
    "kick_player",
    "set_backpack_bank_selected",
    "fog_of_war_clear",
    "reset_skills",
    "devperk_0",
    "devperk_1",
    "devperk_2",
    "devperk_3",
    "devperk_4",
    "devperk_5",
    "devperk_6",
    "devperk_7",
    "movement_infinite_jump_selected_on",
    "movement_infinite_jump_selected_off",
    "movement_infinite_jump_toggle_selected",
    "movement_teleport_to_slot",
})

_MOVEMENT_APPLY_KEYS = frozenset({
    "movement_speed_scale",
    "movement_walk_speed",
    "movement_jump_height",
    "movement_jump_velocity",
    "movement_gravity_scale",
    "movement_step_height",
    "movement_jump_count",
    "movement_jump_off_z_factor",
    "movement_floor_angle",
    "movement_floor_z",
    "movement_individual_jump_goals",
    "movement_sprint_jump_goal",
    "movement_double_jump_goal",
    "movement_slide_jump_goal",
    "movement_glide_speed",
    "movement_glide_boost",
    "movement_glide_air_control",
    "movement_dash_speed",
    "movement_zero_vault_on_apply",
    "movement_time_dilation",
    "target_player",
    "infinite_jump_target",
    "movement_scope",
    "scope",
})

_RARITY_PERCENT_KEYS = frozenset({
    "rarity_common_percent",
    "rarity_uncommon_percent",
    "rarity_rare_percent",
    "rarity_epic_percent",
    "rarity_legendary_percent",
    "rarity_pearlescent_percent",
})

_SERIAL_PAYLOAD_KEYS = frozenset({"serial_text", "serial_override_level", "serial_level"})

_DEV_SPAWNER_AI_KEYS = frozenset({
    "dev_ai_name",
    "dev_ai_count",
    "dev_ai_distance",
    "dev_ai_spacing",
    "dev_ai_scale",
    "dev_ai_z_offset",
    "dev_ai_load",
    "dev_ai_direct_only",
})

_DEV_SPAWNER_TEMPLATE_KEYS = frozenset({
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
})

# Parameterized pins use one action id + payload (not hundreds of baked slot ids).
ALLOWED_PAYLOAD_KEYS: dict[str, frozenset[str]] = {
    "give_currency": frozenset({"currency_kind", "amount"}),
    "set_level": frozenset({"xp_track", "level"}),
    "set_backpack_bank_selected": frozenset({"backpack_size", "bank_size"}),
    "set_backpack_bank_all": frozenset({"backpack_size", "bank_size"}),
    "spawn_itempool": frozenset({"itempool_name", "itempool_count", "itempool_level"}),
    "give_serial_selected": _SERIAL_PAYLOAD_KEYS,
    "give_serial_all": _SERIAL_PAYLOAD_KEYS,
    "give_serial_nonhost": _SERIAL_PAYLOAD_KEYS,
    "travel_to_map": frozenset({"travel_map"}),
    "travel_to_station": frozenset({"travel_station"}),
    "location_bookmark_save": frozenset({"bookmark_name", "name"}),
    "location_bookmark_go": frozenset({"bookmark_name", "name"}),
    "location_bookmark_delete": frozenset({"bookmark_name", "name"}),
    "movement_apply_all": _MOVEMENT_APPLY_KEYS,
    "movement_set_time": frozenset({"movement_time_dilation"}),
    "movement_infinite_jump_selected_on": frozenset({"target_player", "infinite_jump_target"}),
    "movement_infinite_jump_selected_off": frozenset({"target_player", "infinite_jump_target"}),
    "movement_infinite_jump_toggle_selected": frozenset({"target_player", "infinite_jump_target"}),
    "movement_teleport_to_slot": frozenset({"slot"}),
    "movement_super_dash": frozenset({"dash_strength"}),
    "combat_tuning_apply": frozenset({
        "damage_dealt", "damage_taken", "repair_kit_max", "repair_kit_cooldown",
        "repair_kit_duration", "ammo_regen", "scope", "combat_scope", "sticky", "combat_sticky",
        "DamageDealtMultiplier", "DamageTakenMultiplier", "ammoregenrate",
    }),
    "combat_tuning_reset": frozenset({"scope"}),
    "vehicle_preset_apply": frozenset({"vehicle_preset", "preset", "name", "scope", "vehicle_scope"}),
    "vehicle_spawn": frozenset({"vehicle_id", "name", "alias", "scope", "vehicle_scope"}),
    "dev_spawner_reaggro": frozenset({"aggro_mode", "mode"}),
    "dev_spawner_set_aggro": frozenset({"aggro_mode", "mode"}),
    "dev_spawner_set_anchor": frozenset({"spawn_anchor", "anchor"}),
    "rarity_apply": _RARITY_PERCENT_KEYS,
    "dev_spawner_spawnai": _DEV_SPAWNER_AI_KEYS,
    "dev_spawner_spawn": _DEV_SPAWNER_TEMPLATE_KEYS,
    "dev_spawner_lostloot": _DEV_SPAWNER_TEMPLATE_KEYS,
    "cxp_on": frozenset({"multiplier", "cxp_multiplier"}),
    "cxp_toggle": frozenset({"multiplier", "cxp_multiplier"}),
    "cxp_set_mult": frozenset({"multiplier", "cxp_multiplier"}),
    "fog_of_war_clear": frozenset({"target_player", "name"}),
}

MAX_SERIAL_TEXT_LEN = 250_000
MAX_DESTINATION_LEN = 220
MAX_ITEMPOOL_NAME_LEN = 220
MAX_DEV_SPAWNER_TOKEN_LEN = 180
_DEV_SPAWNER_TOKEN_RE = re.compile(r"^[A-Za-z0-9_./:-]+$")
_DEV_SPAWNER_STATE_RE = re.compile(r"^[A-Za-z0-9_,./:-]+$")

DEFAULT_PAGE_0: list[dict[str, Any] | None] = [
    {"action": "max_all", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "max_currency", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "max_eridium", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "max_sdu", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "drop_all_shinies", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "shiny_selected", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "open_golden_chest", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "close_golden_chest", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "open_bank", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "chaos_drop_backpack", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "repeat_last_drop", "label_mode": "basic", "custom_label": "", "payload": {}},
    None,
    None,
]

_layout_revision = 0


def get_layout_revision() -> int:
    return int(_layout_revision)


def empty_page() -> list[dict[str, Any] | None]:
    return [None for _ in range(SLOTS_PER_PAGE)]


def default_pages() -> list[list[dict[str, Any] | None]]:
    first = [normalize_slot(slot) for slot in DEFAULT_PAGE_0]
    while len(first) < SLOTS_PER_PAGE:
        first.append(None)
    return [first[:SLOTS_PER_PAGE]] + [empty_page() for _ in range(MAX_PAGES - 1)]


def _safe_int(value: object, fallback: int) -> int:
    try:
        return int(value)
    except Exception:
        return int(fallback)


def _safe_float(value: object, fallback: float) -> float:
    try:
        return float(value)
    except Exception:
        return float(fallback)


def _truthy_payload(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "checked"}


def sanitize_payload(action: str, raw: object) -> dict[str, Any]:
    source = copy.deepcopy(raw) if isinstance(raw, dict) else {}
    allowed = ALLOWED_PAYLOAD_KEYS.get(action, frozenset())
    result: dict[str, Any] = {}
    for key in allowed:
        if key not in source:
            continue
        if key in ("backpack_size", "bank_size"):
            result[key] = clamp_container_size(source[key], 1000)
        elif key == "currency_kind":
            value = str(source[key] or "cash").strip().lower()
            result[key] = value if value in {"cash", "eridium", "vaultcard1", "vaultcard2", "vaultcard3"} else "cash"
        elif key == "amount":
            result[key] = max(0, min(2147483647, _safe_int(source[key], 0)))
        elif key == "xp_track":
            value = str(source[key] or "player").strip().lower()
            allowed_tracks = {"player", "specialization", "vaultcard_xp_1", "vaultcard_xp_2", "vaultcard_xp_3"}
            result[key] = value if value in allowed_tracks else "player"
        elif key == "level":
            result[key] = max(1, min(9999999, _safe_int(source[key], 60)))
        elif key == "itempool_name":
            result[key] = str(source[key] or "").strip()[:MAX_ITEMPOOL_NAME_LEN]
        elif key == "itempool_count":
            result[key] = max(1, min(100, _safe_int(source[key], 1)))
        elif key == "itempool_level":
            result[key] = max(1, min(60, _safe_int(source[key], 60)))
        elif key in ("travel_map", "travel_station"):
            result[key] = str(source[key] or "").strip()[:MAX_DESTINATION_LEN]
        elif key == "serial_text":
            result[key] = str(source[key] or "")[:MAX_SERIAL_TEXT_LEN]
        elif key == "serial_override_level":
            result[key] = _truthy_payload(source[key])
        elif key == "serial_level":
            result[key] = max(1, min(60, _safe_int(source[key], 60)))
        elif key in ("movement_individual_jump_goals", "movement_zero_vault_on_apply"):
            result[key] = _truthy_payload(source[key])
        elif key == "movement_jump_count":
            result[key] = max(1, min(50, _safe_int(source[key], 2)))
        elif key.startswith("movement_") and key.endswith(("_scale", "_speed", "_height", "_velocity", "_factor", "_angle", "_z", "_goal", "_boost", "_control", "_dilation")):
            result[key] = _safe_float(source[key], 0.0)
        elif key in ("target_player", "infinite_jump_target"):
            result[key] = str(source[key] or "").strip()[:80]
        elif key == "slot":
            result[key] = max(0, min(3, _safe_int(source[key], 0)))
        elif key == "dash_strength":
            result[key] = max(100, min(20000, _safe_int(source[key], 1000)))
        elif key in _RARITY_PERCENT_KEYS:
            result[key] = max(0, min(100, _safe_int(source[key], 100)))
        elif key in ("dev_ai_name", "dev_actor_name", "dev_actor_class", "dev_ai_load"):
            text = str(source[key] or "").strip()[:MAX_DEV_SPAWNER_TOKEN_LEN]
            if text and _DEV_SPAWNER_TOKEN_RE.match(text):
                result[key] = text
        elif key in ("dev_actor_enable_states", "dev_actor_disable_states"):
            text = str(source[key] or "").strip().replace(" ", "")[:MAX_DEV_SPAWNER_TOKEN_LEN]
            if text and _DEV_SPAWNER_STATE_RE.match(text):
                result[key] = text
        elif key in ("dev_ai_count", "dev_actor_count"):
            result[key] = max(1, min(12, _safe_int(source[key], 1)))
        elif key in ("dev_ai_distance", "dev_actor_distance"):
            result[key] = max(0.0, min(20000.0, _safe_float(source[key], 350.0)))
        elif key in ("dev_ai_spacing", "dev_actor_spacing"):
            result[key] = max(1.0, min(5000.0, _safe_float(source[key], 125.0)))
        elif key in ("dev_ai_scale", "dev_actor_scale"):
            result[key] = max(0.05, min(20.0, _safe_float(source[key], 1.0)))
        elif key in ("dev_ai_z_offset", "dev_actor_z_offset"):
            result[key] = max(-5000.0, min(5000.0, _safe_float(source[key], 0.0)))
        elif key == "dev_actor_delay":
            result[key] = max(0.0, min(30.0, _safe_float(source[key], 1.0)))
        elif key in ("dev_ai_direct_only", "dev_actor_no_activate", "dev_actor_include_non_generated"):
            result[key] = _truthy_payload(source[key])
        else:
            result[key] = source[key]
    return result


def _label_mode(action: str, raw_mode: object, custom_label: str) -> str:
    mode = str(raw_mode or "basic").strip().lower()
    if mode == "custom" and custom_label:
        return "custom"
    if mode.startswith("alias"):
        try:
            index = int(mode[5:] or "0")
        except Exception:
            index = -1
        aliases = list(ACTION_CATALOG.get(action, {}).get("aliases") or [])
        if 0 <= index < len(aliases):
            return f"alias{index}"
    return "basic"


def normalize_hotkey(raw: object) -> str:
    key = str(raw or "").strip()
    if not key or key in HOTKEY_RESERVED:
        return ""
    if key not in HOTKEY_KEY_NAMES:
        return ""
    return key


def hotkey_display(key_name: str | None) -> str:
    key = str(key_name or "").strip()
    if not key:
        return ""
    return str(HOTKEY_DISPLAY_ALIASES.get(key) or key)


def normalize_slot(raw: object) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    action = str(raw.get("action") or "").strip()
    if action not in ACTION_CATALOG:
        return None
    custom_label = str(raw.get("custom_label") or "").strip()[:MAX_CUSTOM_LABEL_LEN]
    return {
        "action": action,
        "label_mode": _label_mode(action, raw.get("label_mode"), custom_label),
        "custom_label": custom_label,
        "payload": sanitize_payload(action, raw.get("payload")),
        "hotkey": normalize_hotkey(raw.get("hotkey")),
    }


def validate_slot(raw: object) -> tuple[dict[str, Any] | None, str | None]:
    if raw is None:
        return None, None
    if not isinstance(raw, dict):
        return None, "Slot must be an object or null."
    action = str(raw.get("action") or "").strip()
    if action not in ASSIGNABLE_ACTIONS:
        return None, f"Action is not assignable: {action or '(empty)'}"
    slot = normalize_slot(raw)
    if slot is None:
        return None, f"Invalid Quick Menu slot: {action or '(empty)'}"
    return slot, None


def validate_pages(raw_pages: object) -> tuple[list[list[dict[str, Any] | None]], list[str]]:
    if not isinstance(raw_pages, list):
        return default_pages(), ["pages must be a list."]
    pages: list[list[dict[str, Any] | None]] = []
    errors: list[str] = []
    for page_index in range(MAX_PAGES):
        source = raw_pages[page_index] if page_index < len(raw_pages) else []
        if not isinstance(source, list):
            errors.append(f"Page {page_index + 1} must be a list.")
            source = []
        row = empty_page()
        for slot_index in range(min(SLOTS_PER_PAGE, len(source))):
            slot, error = validate_slot(source[slot_index])
            if error:
                errors.append(f"Page {page_index + 1}, slot {slot_index + 1}: {error}")
            row[slot_index] = slot
        pages.append(row)
    return pages, errors


def sanitize_drop_lock(raw: object) -> dict[str, Any]:
    source = raw if isinstance(raw, dict) else {}
    index = source.get("index")
    if index is not None:
        try:
            index = int(index)
        except Exception:
            index = None
    return {
        "enabled": bool(source.get("enabled", False)),
        "index": index,
        "name": str(source.get("name") or "").strip()[:80],
    }


def sanitize_chrome(raw: object) -> dict[str, Any]:
    source = raw if isinstance(raw, dict) else {}
    theme = str(source.get("theme_id") or DEFAULT_CHROME["theme_id"]).strip().lower()
    if theme not in THEME_IDS:
        theme = str(DEFAULT_CHROME["theme_id"])
    scale = _safe_float(source.get("window_scale"), float(DEFAULT_CHROME["window_scale"]))
    scale = max(WINDOW_SCALE_MIN, min(WINDOW_SCALE_MAX, round(scale, 2)))
    opacity = _safe_float(source.get("panel_opacity"), float(DEFAULT_CHROME["panel_opacity"]))
    opacity = max(0.55, min(1.0, opacity))
    if "rarity_panel_equipped" in source:
        rarity_equipped = _truthy_payload(source.get("rarity_panel_equipped"))
    else:
        rarity_equipped = bool(DEFAULT_CHROME["rarity_panel_equipped"])
    return {
        "theme_id": theme,
        "window_scale": scale,
        "offset_x": max(-800.0, min(800.0, _safe_float(source.get("offset_x"), 0.0))),
        "offset_y": max(-400.0, min(400.0, _safe_float(source.get("offset_y"), 0.0))),
        "panel_opacity": opacity,
        "rarity_panel_equipped": rarity_equipped,
    }


def _layout_from_raw(raw: object) -> dict[str, Any]:
    source = raw if isinstance(raw, dict) else {}
    pages, _errors = validate_pages(source.get("pages", default_pages()))
    page = max(0, min(MAX_PAGES - 1, _safe_int(source.get("page"), 0)))
    chrome_source = source.get("chrome")
    if not isinstance(chrome_source, dict):
        # Migrate pre-v2 opacity if present on the root layout.
        chrome_source = {
            "panel_opacity": source.get("panel_opacity", DEFAULT_CHROME["panel_opacity"]),
        }
    return {
        "version": SCHEMA_VERSION,
        "page": page,
        "edit_mode": bool(source.get("edit_mode", False)),
        "pages": pages,
        "drop_lock": sanitize_drop_lock(source.get("drop_lock")),
        "chrome": sanitize_chrome(chrome_source),
    }


def load_persisted_layout() -> dict[str, Any]:
    settings = load_inventory_settings()
    return _layout_from_raw(settings.get("quick_menu"))


def _save_layout(layout: dict[str, Any]) -> dict[str, Any]:
    global _layout_revision
    normalized = _layout_from_raw(layout)
    save_extra_settings(quick_menu=copy.deepcopy(normalized))
    _layout_revision += 1
    return copy.deepcopy(normalized)


def set_quick_menu_layout(payload: object) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    if isinstance(source.get("layout"), dict):
        source = source["layout"]
    current = load_persisted_layout()
    pages_source = source.get("pages", current["pages"])
    pages, errors = validate_pages(pages_source)
    if errors:
        return {"ok": False, "message": errors[0], "errors": errors}
    chrome_source = source.get("chrome", current.get("chrome"))
    if "panel_opacity" in source and not isinstance(source.get("chrome"), dict):
        chrome_source = dict(current.get("chrome") or {})
        chrome_source["panel_opacity"] = source.get("panel_opacity")
    elif isinstance(chrome_source, dict) and isinstance(current.get("chrome"), dict):
        # Partial chrome updates from the editor (e.g. equip toggles) keep other prefs.
        merged = dict(current.get("chrome") or {})
        merged.update(chrome_source)
        chrome_source = merged
    layout = {
        "version": SCHEMA_VERSION,
        "page": max(0, min(MAX_PAGES - 1, _safe_int(source.get("page"), current["page"]))),
        "edit_mode": bool(source.get("edit_mode", current["edit_mode"])),
        "pages": pages,
        "drop_lock": sanitize_drop_lock(source.get("drop_lock", current["drop_lock"])),
        "chrome": sanitize_chrome(chrome_source),
    }
    saved = _save_layout(layout)
    return {"ok": True, "message": "Quick Menu layout saved.", "layout": saved}


def assign_quick_menu_slot(payload: object) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    page = _safe_int(source.get("page"), -1)
    slot_index = _safe_int(source.get("slot"), -1)
    if not (0 <= page < MAX_PAGES):
        return {"ok": False, "message": f"Page must be 0 to {MAX_PAGES - 1}."}
    if not (0 <= slot_index < SLOTS_PER_PAGE):
        return {"ok": False, "message": f"Slot must be 0 to {SLOTS_PER_PAGE - 1}."}

    layout = load_persisted_layout()
    action = str(source.get("action") or "").strip()
    if not action:
        new_slot = None
    else:
        raw_slot = {
            "action": action,
            "label_mode": source.get("label_mode", "basic"),
            "custom_label": source.get("custom_label", ""),
            "payload": source.get("command_payload", source.get("payload", {})),
        }
        new_slot, error = validate_slot(raw_slot)
        if error:
            return {"ok": False, "message": error}
    layout["pages"][page][slot_index] = new_slot
    layout["page"] = page
    _save_layout(layout)
    return {
        "ok": True,
        "message": f"Quick Menu page {page + 1}, slot {slot_index + 1} updated.",
        "layout": layout,
        "slot": copy.deepcopy(new_slot),
    }


def clear_quick_menu_page(payload: object) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    page = _safe_int(source.get("page"), -1)
    if not (0 <= page < MAX_PAGES):
        return {"ok": False, "message": f"Page must be 0 to {MAX_PAGES - 1}."}
    layout = load_persisted_layout()
    layout["pages"][page] = empty_page()
    layout["page"] = page
    _save_layout(layout)
    return {
        "ok": True,
        "message": f"Quick Menu page {page + 1} cleared.",
        "layout": layout,
    }


def slot_label(slot: dict[str, Any] | None) -> str:
    if not slot:
        return ""
    action = str(slot.get("action") or "")
    catalog = ACTION_CATALOG.get(action, {})
    basic = str(catalog.get("basic") or action)
    custom = str(slot.get("custom_label") or "").strip()
    mode = str(slot.get("label_mode") or "basic")
    if mode == "custom" and custom:
        return custom
    if mode.startswith("alias"):
        try:
            index = int(mode[5:] or "0")
        except Exception:
            index = -1
        aliases = list(catalog.get("aliases") or [])
        if 0 <= index < len(aliases):
            return str(aliases[index])
    return basic


def cycle_slot_label(slot: dict[str, Any]) -> None:
    action = str(slot.get("action") or "")
    aliases = list(ACTION_CATALOG.get(action, {}).get("aliases") or [])
    custom = str(slot.get("custom_label") or "").strip()
    options = ["basic"] + [f"alias{i}" for i in range(len(aliases))]
    if custom:
        options.append("custom")
    mode = str(slot.get("label_mode") or "basic")
    try:
        current = options.index(mode)
    except ValueError:
        current = 0
    slot["label_mode"] = options[(current + 1) % len(options)]


def get_quick_menu_snapshot() -> dict[str, Any]:
    catalog: dict[str, Any] = {}
    for action, metadata in ACTION_CATALOG.items():
        entry = copy.deepcopy(metadata)
        entry["assignable"] = action in ASSIGNABLE_ACTIONS
        entry["needs_player"] = action in NEEDS_PLAYER_ACTIONS
        entry["payload_keys"] = sorted(ALLOWED_PAYLOAD_KEYS.get(action, frozenset()))
        catalog[action] = entry
    return {
        "ok": True,
        "version": SCHEMA_VERSION,
        "revision": get_layout_revision(),
        "limits": {
            "max_pages": MAX_PAGES,
            "slots_per_page": SLOTS_PER_PAGE,
            "grid_cols": GRID_COLS,
            "grid_rows": GRID_ROWS,
            "themes": list(THEME_IDS),
            "theme_labels": dict(THEME_LABELS),
            "window_scale_min": WINDOW_SCALE_MIN,
            "window_scale_max": WINDOW_SCALE_MAX,
            "window_scale_step": WINDOW_SCALE_STEP,
        },
        "catalog": catalog,
        "assignable_actions": list(ASSIGNABLE_ACTIONS),
        "layout": load_persisted_layout(),
    }
