"""Infinite Jump wiring plus a static live-action audit (no BL4 session)."""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "mod_extracted" / "MattsSDKBoostingTools"
ELECTRON = ROOT / "electron_poc"
MOBILE = ROOT / "mobile_controller" / "app" / "src" / "main" / "assets"

IJ_ACTIONS = (
    "movement_infinite_jump_toggle",
    "movement_infinite_jump_all_on",
    "movement_infinite_jump_all_off",
    "movement_infinite_jump_selected_on",
    "movement_infinite_jump_selected_off",
    "movement_infinite_jump_toggle_selected",
)

# Desktop / phone buttons that must keep a backend or assignable handler.
LIVE_ACTIONS = IJ_ACTIONS + (
    "movement_toggle_force_fly",
    "movement_toggle_noclip",
    "movement_apply_fly_speed",
    "movement_apply_all",
    "movement_super_dash",
    "movement_super_dash_toggle",
    "movement_azzy_super_dash",
    "movement_azzy_super_dash_toggle",
    "instant_drops_toggle",
    "instant_holds_toggle",
    "third_person_toggle",
    "cxp_toggle",
    "fog_of_war_clear",
    "fog_of_war_toggle",
    "party_reveal_start",
    "party_reveal_abort",
    "shiny_selected",
    "shiny_all",
    "drop_all_shinies",
    "travel_to_map",
    "travel_to_station",
    "spawn_itempool",
    "hoard_start",
    "set_backpack_bank_selected",
    "uvh_boost_all",
    "max_all",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_infinite_jump_resolves_oak_character_and_prejump():
    movement = _text(SDK / "movement_adjustments.py")
    assert '"OakCharacter"' in movement
    assert "for attr in (\"OakCharacter\", \"Pawn\"" in movement
    assert '("JumpMaxCountPreJump", 999)' in movement
    assert "def _infinite_jump_contexts_heavy" in movement
    assert "def _infinite_jump_contexts_light" in movement
    assert "def toggle_infinite_jump_for_scope" in movement
    camera = _text(SDK / "camera_tick.py")
    assert "Infinite Jump" in camera
    assert "Super Dash" in camera


def test_infinite_jump_unregisters_hooks_when_off():
    movement = _text(SDK / "movement_adjustments.py")
    camera = _text(SDK / "camera_tick.py")
    assert "def _enable_infinite_jump_engine_hooks" in movement
    assert "def _disable_infinite_jump_engine_hooks" in movement
    assert "_disable_infinite_jump_engine_hooks()" in movement
    assert "CanJump" in movement
    assert 'camera_tick.register("infinite_jump"' in movement
    assert "Party Reveal" in camera


def test_infinite_jump_ui_sends_scope_and_backend_handles_it():
    html = _text(ELECTRON / "renderer.html")
    js = _text(ELECTRON / "renderer.js")
    backend = _text(SDK / "backend_actions.py")
    registry = _text(SDK / "quick_menu_registry.py")
    mobile_html = _text(MOBILE / "index.html")
    mobile_js = _text(MOBILE / "app.js")

    assert 'data-movement-action="movement_infinite_jump_toggle"' in html
    assert 'id="infiniteJumpToggleBtn"' in html
    assert "movement_scope: getValue(els.movementScope)" in js
    assert "movement_infinite_jump_toggle" in js
    assert "def movement_infinite_jump_toggle" in backend
    assert 'elif key == "movement_infinite_jump_toggle"' in backend
    for action in IJ_ACTIONS:
        assert f'"{action}"' in registry
        assert action in backend
    assert 'data-action="movement_infinite_jump_all_on"' in mobile_html
    assert 'data-action="movement_infinite_jump_selected_on"' in mobile_html
    assert "infinite_jump_target:currentTarget()" in mobile_js.replace(" ", "")


def test_live_boost_actions_still_have_handlers():
    backend = _text(SDK / "backend_actions.py")
    registry = _text(SDK / "quick_menu_registry.py")
    bridge = _text(SDK / "external_bridge.py")
    assert "import blimgui" not in bridge
    assert "blimgui_panel" not in bridge
    for action in IJ_ACTIONS:
        assert f'"{action}"' in bridge
    assert "_IMMEDIATE_LIVE_MOD_ACTIONS" in bridge
    for action in LIVE_ACTIONS:
        assert f'"{action}"' in registry, action
        assert action in backend, action


def test_electron_and_mobile_live_buttons_are_known_actions():
    html = _text(ELECTRON / "renderer.html")
    mobile_html = _text(MOBILE / "index.html")
    backend = _text(SDK / "backend_actions.py")
    registry = _text(SDK / "quick_menu_registry.py")
    catalog = set(re.findall(r'"([a-z][a-z0-9_]+)"\s*:\s*\{"basic"', registry))
    handled = set(re.findall(r'key == "([a-z][a-z0-9_]+)"', backend))
    handled.update(re.findall(r'key in \("([a-z][a-z0-9_]+)"', backend))
    known = catalog | handled
    local_only = {
        "movement_save_preset",
        "movement_load_saved",
        "clear_external_log",
    }
    electron_actions = set(re.findall(r'data-(?:action|movement-action|rarity-action)="([a-z][a-z0-9_]+)"', html))
    mobile_actions = set(re.findall(r'data-action="([a-z][a-z0-9_]+)"', mobile_html))
    missing = (electron_actions | mobile_actions) - known - local_only
    # Prefix families dispatched by startswith in the runner.
    missing = {
        action
        for action in missing
        if not action.startswith(("movement_preset_", "uvh_boost_tier_", "devperk_", "cxp_", "dev_spawner_"))
    }
    assert not missing, f"UI actions with no backend/registry handler: {sorted(missing)}"


def test_mobile_gateway_and_matt_editor_ports_stay_split():
    gateway = _text(ELECTRON / "mobile_gateway.js")
    host = _text(ROOT / "external_app" / "v22_parts_codes_fixed" / "matt_editor_host.py")
    assert "const DEFAULT_PORT = 49775" in gateway
    assert "PREFERRED_PORT = 49776" in host
    assert "MOBILE_GATEWAY_PORT = 49775" in host
    assert "49775" in _text(MOBILE / "app.js")


def test_toggle_scope_helper_defaults_and_returns_tuple():
    source = ast.parse(_text(SDK / "movement_adjustments.py"))
    found = False
    for node in source.body:
        if isinstance(node, ast.FunctionDef) and node.name == "toggle_infinite_jump_for_scope":
            found = True
            assert node.args.defaults
    assert found
    backend = ast.parse(_text(SDK / "backend_actions.py"))
    fn = next(
        node
        for node in backend.body
        if isinstance(node, ast.FunctionDef) and node.name == "movement_infinite_jump_toggle"
    )
    text = ast.get_source_segment(_text(SDK / "backend_actions.py"), fn) or ""
    assert "toggle_infinite_jump_for_scope" in text
    assert "movement_scope" in text
