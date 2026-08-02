"""Quick Menu last-command / repeat-last-drop helpers (no game runtime)."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"


def _load_backend_actions():
    for name in ("unrealsdk", "unrealsdk.unreal", "mods_base"):
        sys.modules.setdefault(name, types.ModuleType(name))
    mb = sys.modules["mods_base"]
    mb.ENGINE = None
    mb.get_pc = lambda: None

    pkg = types.ModuleType("MattsSDKBoostingTools")
    pkg.__path__ = [str(PKG)]
    sys.modules["MattsSDKBoostingTools"] = pkg

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
            "set_inventory_sizes_for_all_party": lambda *a, **k: None,
            "set_inventory_sizes_for_party_index": lambda *a, **k: None,
        },
        "MattsSDKBoostingTools.dev_tools": {
            "activate_devperk": lambda *a, **k: "perk",
            "teleport_pawn_to_debug_cam": lambda *a, **k: "tp",
            "toggle_debug_cam": lambda *a, **k: "cam",
        },
        "MattsSDKBoostingTools.item_pool_spawning": {
            "spawn_item_pool": lambda *a, **k: 1,
        },
        "MattsSDKBoostingTools.movement_adjustments": {
            "apply_movement_advanced_to_all_players": lambda *a, **k: None,
            "delete_ground_items": lambda *a, **k: None,
            "pawn_for_controller": lambda *a, **k: None,
            "refresh_jump_counts_all_players": lambda *a, **k: None,
            "reset_movement_advanced_all_players": lambda *a, **k: None,
            "set_infinite_jump_all": lambda *a, **k: None,
            "set_infinite_jump_for_index": lambda *a, **k: None,
            "set_no_target": lambda *a, **k: None,
            "set_noclip": lambda *a, **k: None,
            "set_time_dilation": lambda *a, **k: None,
            "teleport_pawn_to_pawn": lambda *a, **k: None,
            "toggle_infinite_jump_for_index": lambda *a, **k: None,
            "toggle_players_only": lambda *a, **k: None,
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
            "DEFAULT_ITEM_LEVEL": 60,
            "drop_all_shinies": lambda level: 3,
        },
        "MattsSDKBoostingTools.travel": {
            "_exec_console": lambda *a, **k: None,
            "travel_to_map": lambda *a, **k: None,
            "travel_to_station": lambda *a, **k: None,
        },
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
