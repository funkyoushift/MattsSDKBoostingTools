import json
from pathlib import Path

import pytest

from tools.import_local_ncs_catalogs import build_challenges, compact_part, normalize, prune_superseded_overrides
from tools import build_data_catalog_manifest as manifest


def test_normalize_preserves_dependency_tables_and_part_ids() -> None:
    raw = {"inv": {"__deps": ["inv_comp"], "__metadata": "discard", "records": [{"entries": [{
        "__op": 2,
        "classmod_corpohacker": {"__typeFlags": 515, "value": {"serialindex": {"__typeFlags": 515, "value": {"index": "402"}}}},
        "__dep_entries": [{"depTableName": "inv_comp", "comp": {"__typeFlags": 515, "value": {"serialindex": {"index": "7", "_scope": "Sub"}}}}],
    }]}]}}
    data = normalize(raw)
    wrapper = data["inv"]["records"][0]["entries"][0]
    assert data["inv"]["__deps"] == ["inv_comp"]
    assert "__metadata" not in data["inv"] and "__op" not in wrapper
    assert wrapper["classmod_corpohacker"]["serialindex"]["index"] == "402"
    assert wrapper["__dep_entries"][0]["comp"]["serialindex"]["index"] == "7"


def test_comp_rules_keep_zero_bounds_and_base_inheritance() -> None:
    raw = {
        "serialindex": {"index": "7"}, "inv_comp": "Comp_Hacker", "basecomposition": "inv'ClassMod.comp_05_legendary'",
        "parttypeselectionrules": {"pairs": {"a": {"key": "class_mod_body", "value": {"partcount": {"min": "0", "max": "0"}}}, "b": {"key": "passive_points"}}},
        "parttagselectionrules": [{"tags": [{"classmod_passive": "ClassMod_Passive"}], "max": "4"}],
    }
    result = compact_part("comp_hacker", raw, {"depTableName": "inv_comp", "depTableId": 2, "depIndex": 0}, {})
    assert result["base"] == "inv'ClassMod.comp_05_legendary'"
    assert result["rules"] == [{"slot": "class_mod_body", "min": 0, "max": 0}, {"slot": "passive_points"}]
    assert result["tag_rules"] == [{"tags": ["classmod_passive"], "max": 4}]


def test_manifest_game_build_requires_matching_derived_hash(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(manifest, "ROOT", tmp_path)
    path = tmp_path / "gzo_parts_map.json"
    path.write_text('{"402 | Loveless": {"1": "Body"}}', encoding="utf-8")
    provenance = tmp_path / "external_app/v22_parts_codes_fixed/matt_editor/LegitItems/local_game_data_provenance.json"
    provenance.parent.mkdir(parents=True)
    provenance.write_text(json.dumps({"derived_catalogs": {path.name: {"game_build": "25234898", "sha256": "known"}}}), encoding="utf-8")
    assert manifest.catalog_game_build(path, "different") is None
    assert manifest.catalog_game_build(path, "known") == "25234898"


@pytest.mark.parametrize("payload", [{"game_data": {"game_build": "25234898"}}, [{"game_build": "25234898"}]])
def test_manifest_reads_game_build_from_world_catalog(tmp_path, monkeypatch, payload) -> None:
    monkeypatch.setattr(manifest, "ROOT", tmp_path)
    path = tmp_path / "world.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert manifest.catalog_game_build(path, "unused") == "25234898"


def test_hotfix_pruning_retains_unmatched_custom_parts() -> None:
    def dep(key, serial):
        return {"depTableName": "barrel", key: {"serialindex": {"index": str(serial), "_scope": "Sub"}}}

    old = {"inv": {"__deps": ["barrel"], "records": [{"entries": [{"weapon": None, "__dep_entries": [dep("existing", 1), dep("custom", 2)]}]}]}}
    fresh = {"inv": {"records": [{"entries": [{"weapon": None, "__dep_entries": [dep("existing", 1)]}]}]}}
    empty = {"inv": {"records": []}}
    result, report = prune_superseded_overrides(old, {"Nexus-Data-inv0.json": fresh, "Nexus-Data-inv4.json": empty, "Nexus-Data-inv6.json": empty})
    kept = result["inv"]["records"][0]["entries"][0]["__dep_entries"]
    assert kept == [dep("custom", 2)]
    assert report == {"superseded_same_serial_identity": ["weapon.existing"], "preserved_unmatched": ["weapon.custom"]}


def test_challenge_goals_inherit_from_parent_and_keep_legacy_ids() -> None:
    payload = {"challenge": {"records": [{"entries": [
        {"parent": {"challenge": "Parent", "challengetiers": [{"goalvalue": "10"}, {"goalvalue": "30"}]}},
        {"vc5_child": {"challenge": "VC5_Child", "parent": "challenge'Parent'"}},
        {"alias": {"ref": "parent"}},
    ]}]}}
    empty = {"challenge": {"records": []}}
    result, report = build_challenges({"Nexus-Data-challenge0.json": payload, "Nexus-Data-challenge4.json": empty, "Nexus-Data-challenge6.json": empty}, {"entries": [{"id": "Legacy", "amount": 5}]}, "25234898")
    assert {row["id"]: row["amount"] for row in result["entries"]} == {"Legacy": 5, "Parent": 30, "VC5_Child": 30}
    assert report["vc5_count"] == 1
