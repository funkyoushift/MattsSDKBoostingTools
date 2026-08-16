"""Pull Loot lays gear on an outward spiral, not radial lines."""
from __future__ import annotations

import importlib.util
import math
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"


def _load_movement():
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

    sys.modules.pop("MattsSDKBoostingTools.movement_adjustments", None)
    spec = importlib.util.spec_from_file_location(
        "MattsSDKBoostingTools.movement_adjustments", PKG / "movement_adjustments.py"
    )
    movement = importlib.util.module_from_spec(spec)
    sys.modules["MattsSDKBoostingTools.movement_adjustments"] = movement
    spec.loader.exec_module(movement)
    return movement


def test_spiral_starts_clear_of_the_player_and_grows_smoothly():
    movement = _load_movement()
    # First item must not land on top of the player, and loops must stay wider
    # apart than neighbours on the arc or the spiral self-crowds.
    assert movement._LOOT_SPIRAL_START_RADIUS >= 200.0
    assert movement._LOOT_SPIRAL_TURN_GROWTH > movement._LOOT_SPIRAL_ITEM_SPACING

    radii = [math.hypot(*movement._loot_spiral_offset(i)) for i in range(40)]
    assert radii[0] == movement._LOOT_SPIRAL_START_RADIUS
    for previous, current in zip(radii, radii[1:]):
        assert current > previous
        assert current - previous <= movement._LOOT_SPIRAL_ITEM_SPACING


def test_spiral_keeps_neighbours_spaced_and_avoids_stacking():
    movement = _load_movement()
    spots = [movement._loot_spiral_offset(i) for i in range(150)]
    spacing = movement._LOOT_SPIRAL_ITEM_SPACING
    for (ax, ay), (bx, by) in zip(spots, spots[1:]):
        assert abs(math.hypot(bx - ax, by - ay) - spacing) < spacing * 0.25
    for i, (ax, ay) in enumerate(spots):
        for bx, by in spots[i + 1:]:
            assert math.hypot(bx - ax, by - ay) > spacing * 0.85


def test_large_pile_stays_within_walking_reach():
    movement = _load_movement()
    assert math.hypot(*movement._loot_spiral_offset(100)) < 1300.0
    assert math.hypot(*movement._loot_spiral_offset(150)) < 1600.0


def test_spiral_does_not_repeat_a_single_bearing():
    movement = _load_movement()
    bearings = {
        round(math.degrees(math.atan2(y, x)) % 360.0, 1)
        for x, y in (movement._loot_spiral_offset(i) for i in range(24))
    }
    assert len(bearings) >= 20
