"""The packaged builder must preserve the September update's level-70 header."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "external_app" / "v22_parts_codes_fixed"))
import external_legit_builder as builder
from external_serial_tools import serial_to_human


def test_level_70_roundtrip_and_boundaries() -> None:
    # A small explicit unlocked part set tests serialization without depending
    # on any particular legendary's evolving dependency rules.
    for requested, expected in [(1, 1), (60, 60), (61, 61), (70, 70), (71, 70), (0, 1), ("invalid", 70)]:
        result = builder.build_base85_external(2, ["part_body"], True, requested)
        assert result["ok"]
        assert result["level"] == expected
        decoded = serial_to_human(result["base85"])
        assert decoded.startswith(f"2, 0, 1, {expected}|"), decoded


def test_default_build_uses_updated_cap() -> None:
    result = builder.build_base85_external(2, ["part_body"], True)
    assert serial_to_human(result["base85"]).startswith("2, 0, 1, 70|")


def test_loveless_root_from_installed_game_roundtrips() -> None:
    root = next(row for row in builder.roots() if row["serial"] == 402)
    assert root["key"] == "classmod_corpohacker"
    assert root["build_label"] == "Loveless Class Mod"
    result = builder.build_base85_external(402, ["comp_01_common", "leg_body_06"], True, 70)
    assert serial_to_human(result["base85"]) == result["human"]
    assert result["human"].startswith("402, 0, 1, 70|")


def test_lower_level_builder_entry_points_use_current_cap() -> None:
    root = next(row for row in builder.roots() if row["serial"] == 402)
    for requested, expected in [(1, 1), (70, 70), (72, 70), (0, 1)]:
        human = builder.build_human(root["key"], [], level=requested)
        serial = builder.build_base85(root["key"], [], level=requested, validate_first=False)
        assert human.startswith(f"402, 0, 1, {expected}|")
        assert serial_to_human(serial).startswith(f"402, 0, 1, {expected}|")
    assert builder.build_human(root["key"], []).startswith("402, 0, 1, 70|")


if __name__ == "__main__":
    test_level_70_roundtrip_and_boundaries()
    test_default_build_uses_updated_cap()
    test_loveless_root_from_installed_game_roundtrips()
    print("external builder level-cap tests passed")
