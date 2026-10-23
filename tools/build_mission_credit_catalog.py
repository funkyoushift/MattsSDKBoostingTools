#!/usr/bin/env python3
"""Build a deterministic mission-credit catalog from the extracted BL4 1.10 data."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


GAME_BUILD = 25234898
SOURCE_GLOB = "Nexus-Data-challenge*.json"
MISSION_TOKEN = re.compile(r"mission'([A-Za-z0-9_]+)'")
PROVENANCE = "Extracted BL4 1.10 challenge source; build 25234898 only."


def _records(path: Path) -> list[tuple[str, dict[str, Any], str]]:
    """Return (challenge key, record, JSON pointer) tuples in authored order."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read challenge source {path.name}: {exc}") from exc

    try:
        groups = document["challenge"]["records"]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"unexpected challenge source structure in {path.name}") from exc
    if not isinstance(groups, list):
        raise ValueError(f"challenge records must be a list in {path.name}")

    found: list[tuple[str, dict[str, Any], str]] = []
    for group_index, group in enumerate(groups):
        entries = group.get("entries") if isinstance(group, dict) else None
        if not isinstance(entries, list):
            raise ValueError(f"entries must be a list in {path.name} at records/{group_index}")
        for entry_index, entry in enumerate(entries):
            if not isinstance(entry, dict) or len(entry) != 1:
                raise ValueError(
                    f"each entry must contain one challenge key in {path.name} "
                    f"at records/{group_index}/entries/{entry_index}"
                )
            challenge, record = next(iter(entry.items()))
            if not isinstance(challenge, str) or not isinstance(record, dict):
                raise ValueError(f"invalid challenge record in {path.name}")
            pointer = (
                f"/challenge/records/{group_index}/entries/{entry_index}/"
                f"{_pointer_escape(challenge)}"
            )
            found.append((challenge, record, pointer))
    return found


def _pointer_escape(value: str) -> str:
    return value.replace("~", "~0").replace("/", "~1")


def build_catalog(source_dir: Path) -> dict[str, Any]:
    """Build and validate the catalog without modifying any source data."""
    paths = sorted(
        path for path in source_dir.glob(SOURCE_GLOB)
        if "challenge_list" not in path.name.lower()
    )
    if not paths:
        raise ValueError(f"no {SOURCE_GLOB} sources found in {source_dir}")

    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        for wrapper, record, pointer in _records(path):
            if not (
                record.get("challengetype") == "Mission"
                and record.get("busecustommissionlist") == "true"
                and record.get("bcompleteeachmissiononce") == "true"
                and record.get("missiondefs")
            ):
                continue
            challenge = record.get('challenge')
            if not isinstance(challenge,str) or not challenge or challenge.casefold()!=wrapper.casefold():
                raise ValueError(f"invalid canonical challenge ID at {pointer}")
            if challenge.casefold() in seen:
                raise ValueError(f"duplicate challenge ID: {challenge}")
            seen.add(challenge.casefold())

            missions = record["missiondefs"]
            if not isinstance(missions, list) or not missions:
                raise ValueError(f"missiondefs must be a nonempty list for {challenge}")
            parsed=[]
            for mission in missions:
                match=MISSION_TOKEN.fullmatch(mission) if isinstance(mission,str) else None
                if not match:
                    raise ValueError(f"invalid mission token for {challenge}: {mission!r}")
                parsed.append(match.group(1))

            entries.append({
                "challenge": challenge,
                "missions": parsed,
                "source": path.name,
                "sha256": digest,
                "pointer": pointer,
                "provenance": PROVENANCE,
            })
    return {"game_build": GAME_BUILD, "entries": entries}


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=project_root / "external_app/v22_parts_codes_fixed/matt_editor/LegitItems",
        help="directory containing extracted Nexus challenge JSON files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=project_root / "mod_extracted/MattsSDKBoostingTools/mission_credit_catalog.json",
        help="catalog output path",
    )
    args = parser.parse_args()
    catalog = build_catalog(args.source_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(catalog['entries'])} entries to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
