"""Quick Menu last-command / repeat-last-drop helpers (no game runtime)."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"


def _load_backend_actions():
    for name in ("unrealsdk", "unrealsdk.unreal", "mods_base"):
        sys.modules.setdefault(name, types.ModuleType(name))
    mb = sys.modules["mods_base"]
    mb.ENGINE = None
    mb.get_pc = lambda: None

    def _command(*_args, **_kwargs):
        def decorate(func):
            func.add_argument = lambda *_a, **_k: None
            return func
        return decorate

    mb.command = _command

    pkg = types.ModuleType("MattsSDKBoostingTools")
    pkg.__path__ = [str(PKG)]
    sys.modules["MattsSDKBoostingTools"] = pkg

    settings: dict = {}

    def _load_settings():
        return dict(settings)

    def _save_settings(**extra):
        settings.update(extra)
        return dict(settings)

    stubs = {
        "MattsSDKBoostingTools.player_economy": {},
        "MattsSDKBoostingTools.serial_rewards": {
            "_resolve_give_serial_strings": lambda serials: list(serials),
            "_serial_delivery_chunks": lambda serials, mode: [list(serials)],
            "_serial_delivery_max_serials_per_chunk": lambda mode: 64,
            "_serial_delivery_post_open_delay": lambda mode: 0.0,
            "_do_give_serial_to_player_indices": lambda *a, **k: None,
            "serial_delivery_progress": lambda: {"active": False},
            "serial_delivery_status": lambda: "",
        },
        "MattsSDKBoostingTools.golden_chest_keybinds": {
            "_close_golden_chest": lambda: None,
            "_open_golden_chest": lambda: None,
        },
        "MattsSDKBoostingTools.inventory_capacity": {
            "auto_apply_inventory_sizes_if_needed": lambda *a, **k: None,
            "clamp_container_size": lambda value, default: int(value or default),
            "load_inventory_settings": _load_settings,
            "save_extra_settings": _save_settings,
            "set_inventory_sizes_for_all_party": lambda *a, **k: None,
            "set_inventory_sizes_for_party_index": lambda *a, **k: None,
        },
        "MattsSDKBoostingTools.dev_tools": {
            "activate_devperk": lambda *a, **k: "perk",
            "copy_debug_cam_location": lambda *a, **k: {"ok": True, "text": "0, 0, 0"},
            "debug_cam_status": lambda *a, **k: {"speed": 1.0, "distance": 0.0, "active": False},
            "disable_debug_cam": lambda *a, **k: "off",
            "reset_skills_for_pc": lambda *a, **k: "reset",
            "set_debug_cam_distance": lambda *a, **k: "distance",
            "set_debug_cam_speed": lambda *a, **k: "speed",
            "teleport_debug_cam_to_pawn": lambda *a, **k: "cam-to-pawn",
            "teleport_pawn_to_debug_cam": lambda *a, **k: "tp",
            "toggle_debug_cam": lambda *a, **k: "cam",
        },
        "MattsSDKBoostingTools.item_pool_spawning": {
            "spawn_item_pool": lambda *a, **k: 1,
            "_normalize_spit_direction": lambda direction: str(direction or "forward"),
        },
        "MattsSDKBoostingTools.movement_adjustments": {
            "apply_movement_advanced_to_all_players": lambda *a, **k: None,
            "delete_ground_items": lambda *a, **k: None,
            "fire_super_dash": lambda *a, **k: None,
            "get_azzy_super_dash_state": lambda *a, **k: {},
            "get_super_dash_state": lambda *a, **k: {},
            "hide_ground_loot": lambda *a, **k: None,
            "infinite_jump_status": lambda *a, **k: {"enabled": False},
            "pawn_for_controller": lambda *a, **k: None,
            "pull_ground_loot_here": lambda *a, **k: None,
            "refresh_jump_counts_all_players": lambda *a, **k: None,
            "request_azzy_super_dash": lambda *a, **k: None,
            "reset_movement_advanced_all_players": lambda *a, **k: None,
            "set_force_fly": lambda *a, **k: None,
            "set_infinite_jump_all": lambda *a, **k: None,
            "set_infinite_jump_for_index": lambda *a, **k: None,
            "set_no_target": lambda *a, **k: None,
            "set_noclip": lambda *a, **k: None,
            "set_super_dash_strength": lambda *a, **k: None,
            "set_time_dilation": lambda *a, **k: None,
            "teleport_pawn_to_pawn": lambda *a, **k: None,
            "toggle_azzy_super_dash": lambda *a, **k: None,
            "toggle_infinite_jump_for_index": lambda *a, **k: None,
            "toggle_infinite_jump_for_scope": lambda *a, **k: None,
            "toggle_players_only": lambda *a, **k: None,
            "toggle_super_dash": lambda *a, **k: None,
            "zero_vault_power_costs_all_players": lambda *a, **k: None,
        },
        "MattsSDKBoostingTools.party_helpers": {
            "_gbc_find_pc_for_player_state": lambda *a, **k: None,
            "_gbc_session_world_and_gamestate": lambda: (None, None),
            "_kick_party_player_by_index": lambda *a, **k: False,
            "_list_party_players": lambda: [(0, "Host"), (1, "Buddy")],
        },
        "MattsSDKBoostingTools.serial_converter": {
            "human_to_serial": lambda *a, **k: "",
            "serial_to_human": lambda *a, **k: "",
        },
        "MattsSDKBoostingTools.shinies": {
            "DEFAULT_ITEM_LEVEL": 70,
            "drop_all_shinies": lambda level: 3,
        },
        "MattsSDKBoostingTools.travel": {
            "_exec_console": lambda *a, **k: None,
            "delete_location_bookmark": lambda *a, **k: None,
            "go_location_bookmark": lambda *a, **k: None,
            "list_location_bookmarks": lambda *a, **k: [],
            "save_location_bookmark": lambda *a, **k: None,
            "travel_to_map": lambda *a, **k: None,
            "travel_to_station": lambda *a, **k: None,
        },
        "MattsSDKBoostingTools.combat_tuning": {
            "apply_combat_tuning": lambda *a, **k: None,
            "reapply_combat_tuning": lambda *a, **k: None,
            "reset_combat_tuning": lambda *a, **k: None,
        },
        "MattsSDKBoostingTools.streamer_chaos": {},
        "MattsSDKBoostingTools.hoard_runner": {},
        "MattsSDKBoostingTools.spawn_helpers": {
            "apply_aggro_to_tracked": lambda *a, **k: None,
            "get_aggro_mode": lambda *a, **k: "all",
            "get_spawn_anchor": lambda *a, **k: "player",
            "note_spawned_actors": lambda *a, **k: None,
            "reaggro_tracked": lambda *a, **k: None,
            "resolve_spawn_anchor_actor": lambda *a, **k: None,
            "set_aggro_mode": lambda *a, **k: None,
            "set_spawn_anchor": lambda *a, **k: None,
        },
        "MattsSDKBoostingTools.vehicle_tuning": {
            "apply_vehicle_preset": lambda *a, **k: None,
            "list_vehicle_catalog": lambda *a, **k: [],
            "list_vehicle_presets": lambda *a, **k: [],
            "spawn_personal_vehicle": lambda *a, **k: None,
            "unlock_all_vehicles_for_pc": lambda *a, **k: None,
        },
        "MattsSDKBoostingTools.extreme_combat_xp": {},
        "MattsSDKBoostingTools.instant_click_holds": {},
        "MattsSDKBoostingTools.no_fog_of_war": {},
    }
    for mod_name, attrs in stubs.items():
        mod = types.ModuleType(mod_name)
        for key, value in attrs.items():
            setattr(mod, key, value)
        sys.modules[mod_name] = mod

    spec = importlib.util.spec_from_file_location(
        "MattsSDKBoostingTools.backend_actions", PKG / "backend_actions.py"
    )
    ba = importlib.util.module_from_spec(spec)
    sys.modules["MattsSDKBoostingTools.backend_actions"] = ba
    spec.loader.exec_module(ba)
    return ba


def test_note_last_command_and_drop():
    ba = _load_backend_actions()
    ba._last_command = None
    ba._last_drop = None
    ba.note_last_command("max_all", label="Max All", is_drop=False)
    assert ba.get_last_command()["action"] == "max_all"
    assert ba.get_last_drop() is None
    ba.note_last_command("shiny_selected", label="Shinies Selected", is_drop=True, needs_player=True)
    assert ba.get_last_drop()["action"] == "shiny_selected"
    assert ba.get_last_drop()["needs_player"] is True


def test_repeat_last_drop_requires_player_without_lock():
    ba = _load_backend_actions()
    ba._last_drop = {
        "action": "shiny_selected",
        "label": "Shinies Selected",
        "payload": {},
        "is_drop": True,
        "needs_player": True,
    }
    ba._drop_lock_enabled = False
    result = ba.repeat_last_drop()
    assert result["ok"] is False
    assert result.get("needs_player") is True


def test_ensure_selected_player_auto_picks_host():
    ba = _load_backend_actions()
    ba._selected_player_index = None
    ba._selected_player_name = ""
    ba._host_player_index_value = lambda: 0
    result = ba.ensure_selected_player(prefer_host=True)
    assert result["ok"] is True
    assert result.get("auto_selected") is True
    assert ba.get_selected_player_index() == 0


def test_repeat_last_drop_uses_lock_option_c():
    ba = _load_backend_actions()
    ba._last_drop = {
        "action": "shiny_selected",
        "label": "Shinies Selected",
        "payload": {},
        "is_drop": True,
        "needs_player": True,
    }
    ba._drop_lock_enabled = True
    ba._drop_lock_index = 1
    ba._drop_lock_name = "Buddy"
    ba._selected_player_index = None
    ba._selected_player_name = ""

    calls = []

    def _fake_run(action, payload=None, record=True):
        calls.append((action, dict(payload or {}), record))
        return {"ok": True, "message": "replayed"}

    ba.run_quick_menu_action = _fake_run
    result = ba.repeat_last_drop()
    assert result["ok"] is True
    assert ba.get_selected_player_index() == 1
    assert calls and calls[0][0] == "shiny_selected"


def test_drop_lock_validates_saved_index_and_name_together():
    ba = _load_backend_actions()
    ba._drop_lock_enabled = True
    ba._drop_lock_index = 1
    ba._drop_lock_name = "Buddy"
    targets = []

    def _capture_target(target):
        targets.append(target)
        return {"ok": True, "message": "selected"}

    ba.set_target_player = _capture_target
    assert ba._apply_drop_player_lock_if_needed() is None
    assert targets == ["1|Buddy"]
