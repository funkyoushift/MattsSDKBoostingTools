"""Offline exact-build qualification for current Epic farming native sites."""

import bisect
import hashlib
import importlib.util
import json
import struct
from pathlib import Path

import pefile

from tools.compare_native_card_builds import decode


ROOT = Path(__file__).parents[2]
STEAM = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Borderlands 4\OakGame\Binaries\Win64\Borderlands4.exe")
EPIC = Path(r"C:\Program Files\Epic Games\Venus\OakGame\Binaries\Win64\Borderlands4.exe")
RECEIPT = json.loads((ROOT / "docs/native-farming/EPIC_6D531D91_PROFILE.json").read_text())


def _builds():
    path = ROOT / "mod_extracted/MattsSDKBoostingTools/farming_builds.py"
    spec = importlib.util.spec_from_file_location("farming_builds_epic_6d531d91_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BUILDS


def _images():
    for path, evidence in zip((STEAM, EPIC), RECEIPT["files"]):
        with path.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == evidence["sha256"]
    return pefile.PE(str(STEAM), fast_load=True), pefile.PE(str(EPIC), fast_load=True)


def _runtime_rows(image):
    directory = image.OPTIONAL_HEADER.DATA_DIRECTORY[3]
    return list(struct.iter_unpack("<III", image.get_data(directory.VirtualAddress, directory.Size)))


def _function(image, rva):
    rows = _runtime_rows(image)
    starts = [row[0] for row in rows]
    index = bisect.bisect_right(starts, rva) - 1
    start, end, _ = rows[index]
    assert start <= rva < end
    return start, end, image.get_data(start, end - start)


def _exact_matches(source, target, source_rva):
    source_start, source_end, body = _function(source, source_rva)
    normalized, masked, references, instruction_count = decode(body, source_start)
    runs = []
    run = 0
    for offset in range(len(body) + 1):
        if offset == len(body) or offset in masked:
            if offset > run:
                runs.append((run, body[run:offset]))
            run = offset + 1
    anchor_offset, anchor = max(runs, key=lambda item: len(item[1]))
    candidates = []
    for section in target.sections:
        if not section.Characteristics & 0x20000000:
            continue
        data = section.get_data()
        position = data.find(anchor)
        while position >= 0:
            start = section.VirtualAddress + position - anchor_offset
            relative = position - anchor_offset
            if relative >= 0 and relative + len(body) <= len(data):
                candidate = data[relative:relative + len(body)]
                try:
                    other, _, other_refs, other_count = decode(candidate, start)
                    same_branches = all(
                        not source_start <= left["target"] < source_end
                        or right["target"] - start == left["target"] - source_start
                        for left, right in zip(references, other_refs)
                        if left["kind"] == "branch"
                    )
                    same_references = [(item["offset"], item["kind"]) for item in references] == [
                        (item["offset"], item["kind"]) for item in other_refs
                    ]
                    if (other == normalized and other_count == instruction_count
                            and same_references and same_branches):
                        candidates.append(start)
                except ValueError:
                    pass
            position = data.find(anchor, position + 1)
    return source_start, source_end, body, candidates


def test_current_epic_drop_and_weighted_roll_have_unique_full_body_matches():
    steam, epic = _images()
    builds = _builds()
    profile = builds["epic-6d531d91"]
    receipt_sites = RECEIPT["qualified_native_sites"]
    assert (profile["timestamp"], profile["image_size"], profile["sha256"]) == (
        257896457, 617152512,
        "6d531d91011ae0d67ac461a3cacabc99993c279bf325dfe70ff1af00ec43c87e",
    )
    assert epic.FILE_HEADER.TimeDateStamp == profile["timestamp"]
    assert epic.OPTIONAL_HEADER.SizeOfImage == profile["image_size"]
    for name, steam_site, evidence in (
        ("drop", 0x371C0B, receipt_sites["drop"]),
        ("legendary_roll", 0x3DAC976, receipt_sites["legendary_roll"]),
    ):
        row = profile[name]
        assert row["rva"] == int(evidence["epic_rva"], 16)
        assert epic.get_data(row["rva"], len(row["context"])) == row["context"]
        if name == "legendary_roll":
            assert row["original"] == row["context"][:17]
        source_start, _, source_body, candidates = _exact_matches(steam, epic, steam_site)
        epic_start, _, epic_body = _function(epic, row["rva"])
        assert candidates == [epic_start]
        assert len(source_body) == evidence["function_size"]
        assert epic_body == epic.get_data(epic_start, len(epic_body))
        assert hashlib.sha256(source_body).hexdigest() == evidence["steam_function_sha256"]
        assert hashlib.sha256(epic_body).hexdigest() == evidence["epic_function_sha256"]
        assert source_start <= steam_site


def test_current_epic_skill_charge_enumeration_remains_unqualified():
    steam, epic = _images()
    profile = _builds()["epic-6d531d91"]
    assert profile["charges"] is None
    _, _, _, getter_candidates = _exact_matches(steam, epic, 0x8BB6592)
    _, _, _, constructor_candidates = _exact_matches(steam, epic, 0x11B61CC)
    assert len(getter_candidates) == 2587
    assert constructor_candidates == [0x11B4048]
    reason = RECEIPT["unqualified_native_features"]["skill_charge_enumeration"]["reason"]
    assert "does not identify the charge-component vtable" in reason
