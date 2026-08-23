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
    unrealsdk.make_struct = lambda _name, **kwargs: types.SimpleNamespace(**kwargs)
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


def teardown_module(_module=None):
    for name in list(sys.modules):
        if name == "unrealsdk" or name == "mods_base" or name.startswith("MattsSDKBoostingTools"):
            sys.modules.pop(name, None)


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


class _Loc:
    def __init__(self, x, y, z):
        self.X = x
        self.Y = y
        self.Z = z


class _Pickup:
    def __init__(self, x, y, z):
        self._loc = _Loc(x, y, z)

    def K2_GetActorLocation(self):
        return self._loc


def test_radius_clamp_and_distance_filter():
    movement = _load_movement()
    assert movement._clamp_loot_radius_m(0) == 0.0
    assert movement._clamp_loot_radius_m(-5) == 0.0
    assert movement._clamp_loot_radius_m(5) == movement._LOOT_RADIUS_MIN_M
    assert movement._clamp_loot_radius_m(9999) == movement._LOOT_RADIUS_MAX_M
    near = _Pickup(400.0, 0.0, 0.0)
    far = _Pickup(40000.0, 0.0, 0.0)
    kept = movement.filter_loot_by_origins([near, far], [(0.0, 0.0, 0.0)], 10)
    assert kept == [near]
    assert movement.filter_loot_by_origins([near, far], [(0.0, 0.0, 0.0)], 0) == [near, far]


def test_hidden_away_marker():
    movement = _load_movement()
    assert movement._is_hidden_away(movement._LOOT_HIDE_AWAY) is True
    assert movement._is_hidden_away((0.0, 0.0, 0.0)) is False
    assert movement._is_hidden_away((100000.0, 100000.0, -1000000000.0)) is True


class _TrackedPickup:
    def __init__(self, x, y, z):
        self._loc = _Loc(x, y, z)
        self.physics = False
        self.hidden = False
        self.collision = True
        self.RootPrimitiveComponent = self
        self.Class = types.SimpleNamespace(ClassDefaultObject=object())

    def K2_GetActorLocation(self):
        return self._loc

    def SetSimulatePhysics(self, on):
        self.physics = bool(on)

    def SetPhysicsLinearVelocity(self, *_a, **_k):
        return None

    def K2_TeleportTo(self, dest, _rot=None):
        if self.physics:
            return False
        self._loc = _Loc(float(dest.X), float(dest.Y), float(dest.Z))
        return True

    def K2_SetActorLocation(self, dest, *_a, **_k):
        self._loc = _Loc(float(dest.X), float(dest.Y), float(dest.Z))
        return True

    def SetActorHiddenInGame(self, hidden):
        self.hidden = bool(hidden)

    def SetActorEnableCollision(self, on):
        self.collision = bool(on)


def test_hide_parks_in_pocket_not_the_void():
    movement = _load_movement()
    pickup = _TrackedPickup(100.0, 200.0, 300.0)
    movement.get_pc = lambda: object()
    movement._iter_ground_loot = lambda *_a, **_k: [pickup]
    msg = movement.hide_ground_loot()
    assert "moved 1" in msg.lower()
    assert pickup._loc.Z == 300.0
    assert pickup._loc.Z > movement._LOOT_HIDE_VOID_Z
    assert movement._is_hidden_away((pickup._loc.X, pickup._loc.Y, pickup._loc.Z))
    assert pickup.physics is False


def test_spiral_does_not_repeat_a_single_bearing():
    movement = _load_movement()
    bearings = {
        round(math.degrees(math.atan2(y, x)) % 360.0, 1)
        for x, y in (movement._loot_spiral_offset(i) for i in range(24))
    }
    assert len(bearings) >= 20
