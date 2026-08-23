"""Header-only item-level rewrite must work on catalog codes that fail a full parse."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONV = ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "serial_converter.py"
LOOTLEMON = ROOT / "docs" / "data" / "MattsSDKBoostingTools_lootlemon_codes.json"

spec = importlib.util.spec_from_file_location("serial_converter", CONV)
sc = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(sc)

# Lootlemon Avatar class mod; 4th header field is item level 60.
DECODABLE = "@Ug!pHG35E/MO#BCWhq}}cgBoE_Aq}dhLG?}LOzknK+R>my0s"


def _header_level(serial: str) -> int:
    numbers, _leftover = sc._read_header_numbers(serial)
    return int(numbers[3])


def test_rewrite_decodable_matches_human_path() -> None:
    human = sc.serial_to_human(DECODABLE)
    assert human.startswith("254, 0, 1, 60")
    rewritten = sc.rewrite_item_level(DECODABLE, 70)
    assert _header_level(rewritten) == 70
    assert sc.serial_to_human(rewritten).startswith("254, 0, 1, 70")


def test_rewrite_header_only_does_not_need_full_part_parse() -> None:
    numbers, leftover = sc._read_header_numbers(DECODABLE)
    assert numbers[3] == 60
    assert leftover
    rewritten = sc.rewrite_item_level(DECODABLE, 12)
    assert _header_level(rewritten) == 12
    assert rewritten.startswith("@U")
    assert rewritten != DECODABLE


def test_rewrite_lootlemon_catalog_headers() -> None:
    if not LOOTLEMON.is_file():
        return
    raw = json.loads(LOOTLEMON.read_text(encoding="utf-8"))
    items = raw.get("entries") or raw.get("items") or raw.get("codes") or raw
    if isinstance(items, dict):
        rows = list(items.values())
    else:
        rows = list(items)
    serials = []
    for row in rows:
        if isinstance(row, dict):
            serial = str(row.get("serial") or "").strip()
            if serial.startswith("@U"):
                serials.append(serial)
        if len(serials) >= 80:
            break
    assert serials, "expected lootlemon serials"
    failed = []
    for serial in serials:
        try:
            before = _header_level(serial)
            rewritten = sc.rewrite_item_level(serial, 33)
            after = _header_level(rewritten)
            if after != 33 or before < 1:
                failed.append((serial[:40], before, after))
        except Exception as exc:
            failed.append((serial[:40], str(exc)))
    assert not failed, failed[:8]


if __name__ == "__main__":
    test_rewrite_decodable_matches_human_path()
    test_rewrite_header_only_does_not_need_full_part_parse()
    test_rewrite_lootlemon_catalog_headers()
    print("ok")
