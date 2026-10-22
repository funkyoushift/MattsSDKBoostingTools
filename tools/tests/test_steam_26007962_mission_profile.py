"""Offline evidence for the Steam 26007962 mission native profile.

The installed executables are optional in CI. This checks native correspondence,
not live game behavior or multiplayer persistence.
"""

import hashlib
import json
from pathlib import Path

import pefile
import pytest

from tools.compare_native_card_builds import decode


ROOT = Path(__file__).parents[2]
EVIDENCE = json.loads((ROOT / "docs/native-missions/STEAM_26007962_PROFILE.json").read_text())
OLD = json.loads((ROOT / "docs/native-missions/EPIC_PROFILE.json").read_text())
PROFILES = json.loads((ROOT / "mod_extracted/MattsSDKBoostingTools/mission_build_profiles.json").read_text())
KEY = "steam-26007962"


def test_profile_is_complete_and_changed_layout_is_explicit():
    profile = PROFILES[KEY]
    assert profile["sha256"] == EVIDENCE["target"]["sha256"]
    assert EVIDENCE["baseline"]["sha256"] == OLD["files"][1]["sha256"]
    assert EVIDENCE["missing"] == [] and EVIDENCE["conflicts"] == {}
    assert len(EVIDENCE["addresses"]) == 41 and len(EVIDENCE["spans"]) == 27
    assert profile["addresses"] == EVIDENCE["addresses"]
    assert profile["fingerprints"] == {
        row["source_steam_rva"]: row["target_fingerprint"] for row in EVIDENCE["spans"]
    }
    assert set(profile["addresses"]) == set(PROFILES["steam-25372571"]["addresses"])
    assert set(profile["fingerprints"]) == set(PROFILES["steam-25372571"]["fingerprints"])
    assert EVIDENCE["layout_changes"] == {
        "0xd17c02": [{"offset": 620, "old": 152, "new": 160},
                       {"offset": 635, "old": 144, "new": 152}],
        "0x125f73e": [{"offset": 35, "old": 192, "new": 184}],
    }


def _installed_images():
    paths = [Path(EVIDENCE[key]["path"]) for key in ("baseline", "target")]
    if not all(path.is_file() for path in paths):
        pytest.skip("Qualified Epic and Steam executables are not both installed")
    for key, path in zip(("baseline", "target"), paths):
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if key == "baseline" and digest != EVIDENCE[key]["sha256"]:
            pytest.skip("Historical Epic baseline was replaced; current Epic has separate evidence")
        assert digest == EVIDENCE[key]["sha256"]
    return pefile.PE(str(paths[0]), fast_load=True), pefile.PE(str(paths[1]), fast_load=True)


def _differences(old, new):
    assert len(old) == len(new)
    return [{"offset": i, "old": a, "new": b}
            for i, (a, b) in enumerate(zip(old, new)) if a != b]


def test_complete_bodies_fingerprints_and_internal_branches_match_installed_files():
    baseline, target = _installed_images()
    for row in EVIDENCE["spans"]:
        old_rva = int(row["baseline_body_rva"], 16)
        new_rva = int(row["target_body_rva"], 16)
        old = baseline.get_data(old_rva, row["size"])
        new = target.get_data(new_rva, row["size"])
        assert hashlib.sha256(old).hexdigest() == row["baseline_sha256"]
        assert hashlib.sha256(new).hexdigest() == row["target_sha256"]
        old_norm, _, old_refs, old_count = decode(old, old_rva)
        new_norm, _, new_refs, new_count = decode(new, new_rva)
        assert [old_count, new_count] == row["instructions"]
        assert _differences(old_norm, new_norm) == row["normalized_byte_differences"]
        assert len(old_refs) == len(new_refs)
        assert all(not old_rva <= a["target"] < old_rva + len(old)
                   or b["target"] - new_rva == a["target"] - old_rva
                   for a, b in zip(old_refs, new_refs) if a["kind"] == "branch")
        source = row["source_steam_rva"]
        new_site = int(EVIDENCE["addresses"][source], 16)
        size = len(bytes.fromhex(row["target_fingerprint"]))
        assert target.get_data(new_site, size).hex() == row["target_fingerprint"]


def test_independent_callers_identify_changed_challenge_callback():
    baseline, target = _installed_images()
    assert len(EVIDENCE["callback_independent_callers"]) == 4
    for caller in EVIDENCE["callback_independent_callers"]:
        assert len(caller["matches"]) == 1
        match = caller["matches"][0]
        old_rva, new_rva = int(caller["old_epic_rva"], 16), int(match["rva"], 16)
        old = baseline.get_data(old_rva, caller["size"])
        new = target.get_data(new_rva, caller["size"])
        assert hashlib.sha256(old).hexdigest() == caller["old_sha256"]
        assert hashlib.sha256(new).hexdigest() == match["sha256"]
        old_norm, _, old_refs, old_count = decode(old, old_rva)
        new_norm, _, new_refs, new_count = decode(new, new_rva)
        assert old_norm == new_norm and old_count == new_count == caller["instructions"]
        assert any(a["target"] == int(ref["old_target"], 16)
                   and b["target"] == int(ref["new_target"], 16)
                   for ref in match["callback_references"]
                   for a, b in zip(old_refs, new_refs)
                   if a["kind"] == b["kind"] == "branch")
        assert all(int(ref["old_target"], 16) == 0xd1a212
                   and int(ref["new_target"], 16) == 0xd1c8e8
                   for ref in match["callback_references"])


def test_loader_and_dialogue_profiles_match_complete_installed_bodies():
    baseline, target = _installed_images()
    sdk = ROOT / "mod_extracted/MattsSDKBoostingTools"
    loader = json.loads((sdk / "mission_loader_builds.json").read_text())
    dialogue = json.loads((sdk / "dialogue_native_builds.json").read_text())
    rows = EVIDENCE["loader_dialogue_spans"]
    assert len(rows) == 10
    assert loader["profiles"][KEY]["rva"] == "0x5fda108"
    assert loader["direct"][KEY]["read_saves"]["rva"] == "0x5afa3b6"
    assert loader["direct"][KEY]["select_slot"]["rva"] == "0x8e39172"
    assert dialogue["profiles"][KEY]["rva"] == "0x3171d0"
    for row in rows:
        old_rva = int(row["baseline_epic_rva"], 16)
        new_rva = int(row["target_steam_rva"], 16)
        old = baseline.get_data(old_rva, row["size"])
        new = target.get_data(new_rva, row["size"])
        assert hashlib.sha256(old).hexdigest() == row["baseline_epic_sha256"]
        assert hashlib.sha256(new).hexdigest() == row["target_steam_sha256"]
        old_norm, _, old_refs, old_count = decode(old, old_rva)
        new_norm, _, new_refs, new_count = decode(new, new_rva)
        assert old_norm == new_norm and old_count == new_count == row["instructions"]
        assert len(old_refs) == len(new_refs)
        assert all(not old_rva <= a["target"] < old_rva + len(old)
                   or b["target"] - new_rva == a["target"] - old_rva
                   for a, b in zip(old_refs, new_refs) if a["kind"] == "branch")
        assert target.get_data(new_rva, 32).hex() == row["target_fingerprint"]
