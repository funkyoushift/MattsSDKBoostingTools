"""Idle-path constants and spawn TTL pruning without a live game."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"


def test_quick_menu_closed_tick_is_30hz_or_slower():
    for name in ("unrealsdk", "unrealsdk.unreal", "mods_base"):
        sys.modules.setdefault(name, types.ModuleType(name))
    mods_base = sys.modules["mods_base"]
    mods_base.hook = lambda *a, **k: (lambda f: f)
    mods_base.Keybind = object
    mods_base.command = lambda *a, **k: (lambda f: f)

    package = types.ModuleType("MattsSDKBoostingTools")
    package.__path__ = [str(PKG)]
    sys.modules["MattsSDKBoostingTools"] = package

    # Minimal stubs for quick_menu imports.
    for stub_name in (
        "quick_menu_registry",
        "quick_menu_inventory",
        "backend_actions",
        "serial_rewards",
    ):
        mod = types.ModuleType(f"MattsSDKBoostingTools.{stub_name}")
        if stub_name == "quick_menu_registry":
            mod.get_layout = lambda: {"pages": []}
            mod.get_layout_revision = lambda: 0
            mod.ASSIGNABLE_ACTIONS = frozenset()
        sys.modules[f"MattsSDKBoostingTools.{stub_name}"] = mod

    # Import only the interval constants via exec of the top of the file is fragile;
    # instead read the module source for the constant after a safe partial load attempt.
    source = (PKG / "quick_menu.py").read_text(encoding="utf-8")
    assert "TICK_INTERVAL_CLOSED_S = 1.0 / 30.0" in source
    assert "TICK_INTERVAL_OPEN_S = 1.0 / 120.0" in source


def test_spawn_prune_enforces_ttl_on_read():
    unrealsdk = types.ModuleType("unrealsdk")
    unrealsdk.find_all = lambda *_a, **_k: []
    unrealsdk.find_class = lambda *_a, **_k: None
    unrealsdk.logging = types.SimpleNamespace(info=lambda *_a, **_k: None)
    sys.modules["unrealsdk"] = unrealsdk
    sys.modules.setdefault("unrealsdk.unreal", types.ModuleType("unrealsdk.unreal"))
    mods_base = types.ModuleType("mods_base")
    mods_base.get_pc = lambda: None
    sys.modules["mods_base"] = mods_base

    package = types.ModuleType("MattsSDKBoostingTools")
    package.__path__ = [str(PKG)]
    sys.modules["MattsSDKBoostingTools"] = package
    party = types.ModuleType("MattsSDKBoostingTools.party_helpers")
    party.get_pc = lambda: None
    sys.modules["MattsSDKBoostingTools.party_helpers"] = party
    movement = types.ModuleType("MattsSDKBoostingTools.movement_adjustments")
    movement.live_player_controllers = lambda: []
    movement.pawn_for_controller = lambda *_a, **_k: None
    sys.modules["MattsSDKBoostingTools.movement_adjustments"] = movement

    sys.modules.pop("MattsSDKBoostingTools.spawn_helpers", None)
    spec = importlib.util.spec_from_file_location(
        "MattsSDKBoostingTools.spawn_helpers", PKG / "spawn_helpers.py"
    )
    spawn = importlib.util.module_from_spec(spec)
    sys.modules["MattsSDKBoostingTools.spawn_helpers"] = spawn
    spec.loader.exec_module(spawn)

    sentinel = object()
    spawn._tracked_mobs = [sentinel]
    spawn._tracked_at = 0.0  # far in the past relative to monotonic
    pruned = spawn._prune_tracked()
    assert pruned == []
    assert spawn._tracked_mobs == []
