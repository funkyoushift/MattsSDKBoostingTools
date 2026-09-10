from __future__ import annotations

import importlib.util
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("world_refresh", ROOT / "tools/refresh_game_world_catalogs.py")
world = importlib.util.module_from_spec(spec)
spec.loader.exec_module(world)


def test_all_numeric_shards_are_loaded_in_numeric_order(tmp_path):
    for name in ["Map10", "Map1", "Map0", "Map4", "Map6", "Map2", "Map1_minimal", "Map1_metadata", "Map"]:
        (tmp_path / f"Nexus-Data-{name}.json").write_text("{}", encoding="utf-8")
    assert [p.name for p in world.table_files(tmp_path, "map")] == [
        f"Nexus-Data-Map{number}.json" for number in [0, 1, 2, 4, 6, 10]
    ]


def test_full_ncs_unwrap_preserves_real_value_fields_and_station_only_records(tmp_path):
    data = {"map": {"records": [{"entries": [
        {"zone_p": {"__typeFlags": 515, "value": {"map": {"__typeFlags": 513, "value": "Zone_P"}}}},
        {"zone_p": None, "__dep_entries": [{"depTableName": "station", "fast": {
            "__typeFlags": 515, "value": {"station": "Fast", "loc": {"x": "10", "y": "20", "z": "30"}}
        }}]},
    ]}]}}
    (tmp_path / "Nexus-Data-Map0.json").write_text(json.dumps(data), encoding="utf-8")
    rows, _, records = world.load_table(tmp_path, "map")
    assert rows["zone_p"]["map"] == "Zone_P"
    assert records[1][1][0]["fast"]["loc"]["z"] == "30"
    assert world.unwrap({"value": {"type": "Bool", "value": "false"}}) == {"value": {"type": "Bool", "value": "false"}}


def test_new_actors_inherit_category_and_display_without_losing_favorites():
    before = {"categories": {"All": ["Old"], "Characters": ["Old"]}, "favorites": ["Old"], "commands": ["keep"]}
    actors = {"base": {"gbxactor": "Base", "type": "Asset'/Script/OakGame.OakCharacterDef'", "uxdisplayname": "display_data'name_base'"},
              "new": {"gbxactor": "New", "parent": "gbxactor'Base'"}}
    display = {"name_base": {"text": "enemies, " + "A" * 32 + ", New Enemy"}}
    result, added = world.merge_actors(before, actors, {"base": "a.json", "new": "a.json"}, display, {"game_build": "123"})
    assert set(added) == {"Base", "New"}
    assert result["favorites"] == ["Old"] and result["commands"] == ["keep"]
    assert result["display_names"]["New"] == "New Enemy"
    assert "New" in result["categories"]["Characters"]
    assert before["categories"]["All"] == ["Old"]
    assert world.inherited({"a": {"parent": "b"}, "b": {"parent": "a"}}, "a", "type") is None


def test_travel_dependency_only_entries_keep_correct_world_and_coordinates():
    rows = {name.lower(): {"map": name, "mappath": f"Asset'/Game/DLC/Test/{name}.{name}'",
                           "auto_save_infos": {"canbecooked": "true", "defaultstation": f"map'{name}.Fast'"}}
            for name in ["One_P", "Two_P", "FrontEnd_P"]}
    records = [(name.lower(), [{"depTableName": "station", "fast": {"station": "Fast", "loc": {"x": str(index), "y": "2", "z": "3"}}}], "Nexus-Data-Map0.json") for index, name in enumerate(rows)]
    maps, stations, _, _ = world.merge_travel({"maps": []}, {"stations": []}, rows, {key: "map.json" for key in rows}, records, {"game_build": "123"})
    assert {row["map"] for row in maps["maps"]} == {"One_P", "Two_P"}
    assert {row["station"] for row in stations["stations"]} == {"One_P.Fast", "Two_P.Fast"}
    assert {row["x"] for row in stations["stations"]} == {"0", "1"}


def test_pool_merge_preserves_curated_names_and_is_idempotent():
    before = [{"itempool": "Pool_Old", "display_name": "Curated", "category": "Other"}]
    incoming = {"pool_old": {"itempool": "POOL_OLD"}, "itempool_new_sg_item": {"itempool": "itempool_new_sg_item"}}
    result, added = world.merge_pools(before, incoming, {key: "pool.json" for key in incoming}, {"game_build": "123"})
    assert added == ["itempool_new_sg_item"]
    assert any(row["display_name"] == "Curated" for row in result)
    assert world.merge_pools(result, incoming, {}, {"game_build": "123"}) == (result, [])


def test_partial_station_patch_preserves_existing_travel_values():
    before_maps = {"maps": [{"map": "Zone_P", "mappath": "old-path", "defaultstation": "Zone_P.Fast", "canbecooked": True}]}
    before_stations = {"stations": [{"station": "Zone_P.Fast", "world": "Zone_P", "display_name": "Station", "category": "Standard", "dest": "Else_P.Entry", "x": "1", "y": "2", "z": "3"}]}
    records = [("zone_p", [{"depTableName": "station", "fast": {"station": "Fast", "loc": {"z": "4"}}}], "patch.json")]
    maps, stations, _, _ = world.merge_travel(before_maps, before_stations, {"zone_p": {"map": "Zone_P"}}, {"zone_p": "patch.json"}, records, {"game_build": "123"})
    assert maps["maps"][0]["defaultstation"] == "Zone_P.Fast"
    assert maps["maps"][0]["canbecooked"] is True
    assert stations["stations"][0]["dest"] == "Else_P.Entry"
    assert stations["stations"][0]["x"] == "1"
    assert stations["stations"][0]["z"] == "4"
