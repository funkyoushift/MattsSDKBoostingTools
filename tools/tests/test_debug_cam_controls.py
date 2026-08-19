"""Debug camera speed/distance clamps and status helpers (no game runtime)."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"


def _load_dev_tools():
    unrealsdk = types.ModuleType("unrealsdk")
    unrealsdk.logging = types.SimpleNamespace(
        info=lambda *_a, **_k: None,
        warning=lambda *_a, **_k: None,
    )
    unrealsdk.find_all = lambda *_a, **_k: []
    unrealsdk.make_struct = lambda *_a, **_k: None
    sys.modules["unrealsdk"] = unrealsdk
    sys.modules["unrealsdk.logging"] = unrealsdk.logging

    mods_base = types.ModuleType("mods_base")
    mods_base.ENGINE = None
    mods_base.get_pc = lambda: None
    mods_base.hook = lambda *_a, **_k: (lambda func: func)
    sys.modules["mods_base"] = mods_base

    package = types.ModuleType("MattsSDKBoostingTools")
    package.__path__ = [str(PKG)]
    sys.modules["MattsSDKBoostingTools"] = package

    player_economy = types.ModuleType("MattsSDKBoostingTools.player_economy")
    player_economy._resolve_target_pc_for_index = lambda *_a, **_k: (None, "none")
    sys.modules["MattsSDKBoostingTools.player_economy"] = player_economy

    party_helpers = types.ModuleType("MattsSDKBoostingTools.party_helpers")
    party_helpers._gbc_is_listen_host_world = lambda *_a, **_k: True
    party_helpers._gbc_session_world_and_gamestate = lambda *_a, **_k: (None, None)
    sys.modules["MattsSDKBoostingTools.party_helpers"] = party_helpers

    sys.modules.pop("MattsSDKBoostingTools.dev_tools", None)
    spec = importlib.util.spec_from_file_location(
        "MattsSDKBoostingTools.dev_tools", PKG / "dev_tools.py"
    )
    dev_tools = importlib.util.module_from_spec(spec)
    sys.modules["MattsSDKBoostingTools.dev_tools"] = dev_tools
    spec.loader.exec_module(dev_tools)
    return dev_tools


def teardown_module(_module=None):
    for name in list(sys.modules):
        if name == "unrealsdk" or name == "mods_base" or name.startswith("MattsSDKBoostingTools"):
            sys.modules.pop(name, None)


def test_clamp_debug_speed_bounds():
    dev = _load_dev_tools()
    assert dev.clamp_debug_speed(1) == 1.0
    assert dev.clamp_debug_speed(0) == 0.05
    assert dev.clamp_debug_speed(999) == 50.0
    assert dev.clamp_debug_speed("nope") == 1.0


def test_clamp_debug_distance_allows_zero_default():
    dev = _load_dev_tools()
    assert dev.clamp_debug_distance(0) == 0.0
    assert dev.clamp_debug_distance(-10) == 0.0
    assert dev.clamp_debug_distance(25000) == 20000.0
    assert dev.clamp_debug_distance("nope") == 0.0


def test_zero_distance_skips_live_field_writes():
    dev = _load_dev_tools()
    dummy = types.SimpleNamespace(CameraDistance=123.0)
    assert dev._apply_debug_distance_to_controller(dummy, 0) == 0
    assert dummy.CameraDistance == 123.0
    assert dev._apply_debug_distance_to_controller(dummy, 400.0) >= 1
    assert dummy.CameraDistance == 400.0


def test_debug_cam_status_reports_stored_speed_and_distance():
    dev = _load_dev_tools()
    status = dev.debug_cam_status()
    assert status["speed"] == 1.0
    assert status["distance"] == 0.0
    assert status["active"] is False
    message = dev.set_debug_cam_distance(0)
    assert "default" in message.lower()
