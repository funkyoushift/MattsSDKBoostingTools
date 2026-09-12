"""XP/currency boost actions must use the selected party index and honor failures."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"
TEST_PACKAGE = "msbt_economy_target_test"


@pytest.fixture
def backend(monkeypatch):
    def module(name, **values):
        result = types.ModuleType(name)
        result.__dict__.update(values)
        monkeypatch.setitem(sys.modules, name, result)
        return result

    def decorator(*_args, **_kwargs):
        def apply(fn):
            fn.add_argument = lambda *_a, **_k: None
            return fn
        return apply

    module(TEST_PACKAGE, __path__=[str(PKG)])
    module("mods_base", command=decorator, hook=decorator, get_pc=lambda: None, ENGINE=None)
    module(
        "unrealsdk",
        find_all=lambda *_a: [],
        find_class=lambda *_a: None,
        find_object=lambda *_a: None,
        logging=types.SimpleNamespace(
            info=lambda *_a: None, error=lambda *_a: None, warning=lambda *_a: None
        ),
    )
    module(
        "unrealsdk.unreal",
        FGbxDefPtr=object,
        UObject=object,
        BoundFunction=object,
        WrappedStruct=object,
    )
    module("unrealsdk.hooks", Type=types.SimpleNamespace(POST=1))

    # Lightweight stubs for backend_actions heavy imports.
    for name in (
        "player_economy",
        "quick_menu_registry",
        "serial_rewards",
        "golden_chest_keybinds",
        "inventory_capacity",
        "dev_tools",
        "item_pool_spawning",
        "movement_adjustments",
        "party_helpers",
        "travel",
        "travel_gate",
        "vault_card_boost",
        "shinies",
        "streamer_chaos",
        "extreme_combat_xp",
        "instant_click_holds",
        "no_fog_of_war",
        "fod_reveal",
        "fod_party_reveal",
        "fod_guest_grid",
        "third_person_camera",
        "asd_hybrid",
        "camera_tick",
        "spawn_helpers",
        "hoard_runner",
        "challenge_objective_complete",
        "item_serial_reader",
        "legit_builder_core",
        "runtime_cleanup",
        "hook_gate",
        "perf_profile",
        "external_app_launcher",
        "serial_converter",
        "serial_item_meta",
        "vehicle_tuning",
        "combat_tuning",
        "bl4_tpc",
        "bl4_tpc.native",
        "bl4_tpc.controller",
    ):
        module(f"{TEST_PACKAGE}.{name}")

    module(
        f"{TEST_PACKAGE}.game_parameters",
        CURRENCY_KINDS=["cash", "eridium"],
        EXP_TRACKS=["player", "specialization", "vaultcard_xp_1"],
        MAX_ITEM_LEVEL=70,
        MAX_PLAYER_LEVEL=70,
        MAX_SPEC_LEVEL=701,
        MAX_VAULT_CARD_LEVEL=9999,
        status_parameters=lambda: {},
    )
    module(
        f"{TEST_PACKAGE}.party_helpers",
        _gbc_find_pc_for_player_state=lambda *_a: None,
        _gbc_is_listen_host_world=lambda *_a: True,
        _gbc_resolve_player_index_for_name_substring=lambda *_a: (0, ""),
        _gbc_session_world_and_gamestate=lambda: (object(), object()),
        _list_party_players=lambda: [(0, "Host")],
    )

    # Importing backend_actions pulls many siblings; stub missing attrs after load if needed.
    # Prefer loading only the functions under test by constructing a thin stand-in.
    economy = types.SimpleNamespace(
        _CURRENCY_KIND_ALIASES={"cash": "Cash", "eridium": "eridium"},
        _do_give_currency=lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("name path")),
        _do_give_experience=lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("name path")),
        _set_experience_level_via_bp=lambda *_a, **_k: True,
        _give_currency_on_pc=lambda *_a, **_k: True,
        _resolve_target_pc_for_name=lambda *_a, **_k: (None, "unused"),
    )
    monkeypatch.setitem(sys.modules, f"{TEST_PACKAGE}.player_economy", economy)

    # Minimal backend_actions surface: exec the helper block is too heavy.
    # Load the real module with stubs already registered.
    stubs = {
        "inventory_capacity": dict(
            auto_apply_inventory_sizes_if_needed=lambda *_a, **_k: None,
            clamp_container_size=lambda v, *_a, **_k: v,
            load_inventory_settings=lambda: {},
            save_extra_settings=lambda *_a, **_k: None,
            set_inventory_sizes_for_all_party=lambda *_a, **_k: None,
            set_inventory_sizes_for_party_index=lambda *_a, **_k: None,
        ),
        "golden_chest_keybinds": dict(
            _close_golden_chest=lambda: None,
            _open_golden_chest=lambda: None,
        ),
        "dev_tools": dict(
            activate_devperk=lambda *_a, **_k: None,
            reset_skills_for_pc=lambda *_a, **_k: None,
            copy_debug_cam_location=lambda *_a, **_k: None,
            debug_cam_status=lambda: {},
            disable_debug_cam=lambda: None,
            set_debug_cam_distance=lambda *_a, **_k: None,
            set_debug_cam_speed=lambda *_a, **_k: None,
            teleport_debug_cam_to_pawn=lambda *_a, **_k: None,
            teleport_pawn_to_debug_cam=lambda *_a, **_k: None,
            toggle_debug_cam=lambda: None,
        ),
        "item_pool_spawning": dict(
            _normalize_spit_direction=lambda v: v,
            spawn_item_pool=lambda *_a, **_k: None,
        ),
        "movement_adjustments": dict(
            apply_movement_advanced_to_all_players=lambda *_a, **_k: None,
            delete_ground_items=lambda *_a, **_k: None,
        ),
        "serial_rewards": dict(),
        "quick_menu_registry": dict(
            ACTION_CATALOG={},
            sanitize_payload=lambda action, payload: payload or {},
        ),
    }
    for name, values in stubs.items():
        mod = sys.modules[f"{TEST_PACKAGE}.{name}"]
        mod.__dict__.update(values)

    # Fill remaining movement_adjustments exports that backend imports by name.
    ma = sys.modules[f"{TEST_PACKAGE}.movement_adjustments"]
    for attr in (
        "hide_ground_loot",
        "pull_ground_loot",
        "set_time_dilation",
        "infinite_jump_set_all",
        "infinite_jump_set_selected",
        "infinite_jump_toggle",
        "infinite_jump_status",
        "movement_status",
    ):
        if not hasattr(ma, attr):
            setattr(ma, attr, lambda *_a, **_k: {"ok": True, "message": "stub"})

    # Soft-import may still fail on remaining symbols; skip to focused unit under test.
    helpers = types.ModuleType(f"{TEST_PACKAGE}._economy_helpers")
    helpers.__dict__.update(
        {
            "Any": object,
            "MAX_WALLET_AMOUNT": 2147483647,
            "EXP_TRACKS": ["player", "specialization", "vaultcard_xp_1"],
            "MAX_PLAYER_LEVEL": 70,
            "MAX_SPEC_LEVEL": 701,
            "player_economy": economy,
            "get_selected_player_index": lambda: 0,
            "get_selected_player_name": lambda: "Host",
            "refresh_players": lambda: None,
            "_party_controller_for_index": lambda idx: types.SimpleNamespace(
                PlayerState=types.SimpleNamespace(name="ps")
            ),
            "_selected_player_label": lambda idx, name: name or f"party index {idx}",
            "_kind_from_input": lambda v: str(v).lower() if str(v).lower() in ("cash", "eridium") else None,
            "_track_from_input": lambda v: str(v).lower() if str(v).lower() in ("player", "specialization") else None,
            "_max_level_for_track": lambda track: 70 if track == "player" else 701,
            "_clamp_int": lambda value, lo, hi: max(lo, min(hi, int(value))),
        }
    )

    # Execute the real helper/action definitions against the helpers namespace.
    src = (PKG / "backend_actions.py").read_text(encoding="utf-8")
    start = src.index("def _selected_economy_target(")
    end = src.index("\ndef max_sdu(")
    code = src[start:end]
    ns = helpers.__dict__
    exec(code, ns, ns)  # noqa: S102 — test loads production snippet into a sandbox

    yield types.SimpleNamespace(**{k: ns[k] for k in (
        "give_currency",
        "give_experience",
        "max_player_level",
        "max_spec_level",
        "max_currency",
        "max_eridium",
    )}), economy, helpers

    for name in list(sys.modules):
        if name.startswith(TEST_PACKAGE):
            sys.modules.pop(name, None)


def test_set_level_uses_selected_index_not_name_path(backend):
    actions, economy, _helpers = backend
    calls = []
    economy._set_experience_level_via_bp = lambda ps, track_idx, level: calls.append(
        (track_idx, level, ps is not None)
    ) or True
    result = actions.give_experience("player", 70)
    assert result["ok"] is True
    assert "Host" in result["message"]
    assert calls == [(0, 70, True)]
    # Name-based path must not be used when an index controller exists.
    economy._do_give_experience = lambda *_a, **_k: (_ for _ in ()).throw(
        AssertionError("name path should not run")
    )
    assert actions.give_experience("player", 70)["ok"] is True


def test_max_cash_reports_failure_when_give_returns_false(backend):
    actions, economy, _helpers = backend
    economy._give_currency_on_pc = lambda *_a, **_k: False
    result = actions.max_currency()
    assert result["ok"] is False
    assert "failed" in result["message"].lower()


def test_set_spec_701_ignores_player_track_alias(backend):
    actions, economy, _helpers = backend
    calls = []
    economy._set_experience_level_via_bp = lambda ps, track_idx, level: calls.append(
        (track_idx, level)
    ) or True
    result = actions.max_spec_level()
    assert result["ok"] is True
    assert calls == [(1, 701)]
