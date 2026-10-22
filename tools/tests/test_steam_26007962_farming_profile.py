"""Read-only executable checks for the Steam 26007962 farming profile."""

import bisect
import hashlib
import importlib.util
import struct
from pathlib import Path

import pefile
import pytest

from tools.compare_native_card_builds import decode


ROOT = Path(__file__).parents[2]
SOURCE = Path(r"C:\Program Files\Epic Games\Venus\OakGame\Binaries\Win64\Borderlands4.exe")
TARGET = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Borderlands 4\OakGame\Binaries\Win64\Borderlands4.exe")
HASHES = (
    "764a4bb5403a2619a0be627de5a738e23ea021e8672f7f0e7a536697d4a06719",
    "ba75f7c2874b16efb5536a5c0cc28918a03efd3e55d790d2e4db57de0c3a353a",
)


def _profile():
    path = ROOT / "mod_extracted/MattsSDKBoostingTools/farming_builds.py"
    spec = importlib.util.spec_from_file_location("farming_builds_26007962_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.BUILDS["steam-26007962"]


def _images():
    if not SOURCE.is_file() or not TARGET.is_file():
        pytest.skip("Epic baseline and new Steam executable are not both installed")
    for path, expected in zip((SOURCE, TARGET), HASHES):
        with path.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == expected
    return pefile.PE(str(SOURCE), fast_load=True), pefile.PE(str(TARGET), fast_load=True)


def _function(image, rva):
    directory = image.OPTIONAL_HEADER.DATA_DIRECTORY[3]
    rows = list(struct.iter_unpack("<III", image.get_data(directory.VirtualAddress, directory.Size)))
    starts = [row[0] for row in rows]
    start, end, _ = rows[bisect.bisect_right(starts, rva) - 1]
    assert start <= rva < end
    return start, image.get_data(start, end - start)


def _same_body_layout(old_image, new_image, old_rva, new_rva, size, instructions):
    old_start, old = _function(old_image, old_rva)
    new_start, new = _function(new_image, new_rva)
    assert len(old) == len(new) == size
    old_norm, _, old_refs, old_count = decode(old, old_start)
    new_norm, _, new_refs, new_count = decode(new, new_start)
    assert old_norm == new_norm and old_count == new_count
    if instructions is not None:
        assert old_count == instructions
    assert len(old_refs) == len(new_refs)
    assert all(not old_start <= a["target"] < old_start + size
               or b["target"] - new_start == a["target"] - old_start
               for a, b in zip(old_refs, new_refs) if a["kind"] == "branch")


def test_new_profile_has_exact_identity_and_code_sites():
    old, new = _images()
    profile = _profile()
    assert (profile["timestamp"], profile["image_size"], profile["sha256"]) == (
        4086165580, 652288000, HASHES[1])
    assert new.FILE_HEADER.TimeDateStamp == profile["timestamp"]
    assert new.OPTIONAL_HEADER.SizeOfImage == profile["image_size"]
    for key, old_rva, size, instructions in (
        ("drop", 0x372dc9, 2015, 415),
        ("legendary_roll", 0x3d9e2d2, 495, 144),
    ):
        row = profile[key]
        assert new.get_data(row["rva"], len(row["context"])) == row["context"]
        _same_body_layout(old, new, old_rva, row["rva"], size, instructions)
    assert profile["drop"]["rva"] == 0x371c0b
    assert profile["legendary_roll"]["rva"] == 0x3dac976
    assert profile["legendary_roll"]["original"] == profile["legendary_roll"]["context"][:17]


def test_charge_getter_and_constructor_references_match_new_image():
    old, new = _images()
    row = _profile()["charges"]
    assert new.get_data(row["getter"], len(row["getter_context"])) == row["getter_context"]
    _same_body_layout(old, new, 0x8bb32d6, row["getter"], 57, 13)
    _same_body_layout(old, new, 0x11b947a, 0x11b61cc, 870, None)
    old_ctor = old.get_data(0x11b947a, 870)
    new_ctor = new.get_data(0x11b61cc, 870)
    _, _, old_refs, old_count = decode(old_ctor, 0x11b947a)
    _, _, new_refs, new_count = decode(new_ctor, 0x11b61cc)
    assert old_count == new_count
    assert sum(a["target"] == 0xb40fb50 and b["target"] == row["entry_vtable"]
               for a, b in zip(old_refs, new_refs)) == 2
    assert row["vtable"] == 0xb63f570
    assert row["struct_global"] == 0xcba2a20
