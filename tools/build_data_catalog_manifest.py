#!/usr/bin/env python3
"""Rebuild docs/data/catalog_manifest.json from files in docs/data/.

Does not bump the public Electron/SDK SemVer. Only the data_version field
inside the manifest is versioned (data-vX.Y.Z).

Usage:
  python tools/build_data_catalog_manifest.py
  python tools/build_data_catalog_manifest.py --data-version 1.0.1
  python tools/build_data_catalog_manifest.py --bump patch
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "docs" / "data"
MANIFEST_PATH = DATA_DIR / "catalog_manifest.json"

# Hosted raw URLs (main). Releases/latest/download is tried first by the app.
RAW_BASE = (
    "https://raw.githubusercontent.com/funkyoushift/MattsSDKBoostingTools/"
    "main/docs/data"
)
RELEASE_MANIFEST_URL = (
    "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/latest/"
    "download/catalog_manifest.json"
)

# Stable file registry: order is intentional (Phase 1 first, then Phase 2).
FILE_SPECS: list[dict[str, Any]] = [
    {
        "id": "lootlemon",
        "filename": "MattsSDKBoostingTools_lootlemon_codes.json",
        "schema_version": 1,
        "notes": "Lootlemon BL4 serials catalog",
    },
    {
        "id": "custom_bl4_codes",
        "filename": "custom_bl4_codes.json",
        "schema_version": 1,
        "notes": "Custom / static BL4 codes",
    },
    {
        "id": "gzo_codes",
        "filename": "MattsSDKBoostingTools_gzo_codes.json",
        "schema_version": 1,
        "notes": (
            "GZO snapshot fallback. Live primary remains save-editor.be; "
            "GitHub cache is offline / fallback only."
        ),
        "primary": "https://save-editor.be/GZO/Borderlands4/codes/api.php?action=catalog",
    },
    {
        "id": "travelstations",
        "filename": "travelstations.json",
        "schema_version": 1,
        "notes": "Travel station catalog",
    },
    {
        "id": "travelmaps",
        "filename": "travelmaps_flat.json",
        "schema_version": 1,
        "notes": "Travel map flat list",
    },
    {
        "id": "item_pools",
        "filename": "item_pools.json",
        "schema_version": 1,
        "notes": "Item pool spawn catalog",
    },
    {
        "id": "gzo_parts_map",
        "filename": "gzo_parts_map.json",
        "schema_version": 1,
        "notes": "GZO part id → label map",
    },
    {
        "id": "shiny_serials",
        "filename": "shiny_serials.json",
        "schema_version": 1,
        "notes": "Shiny serial delivery list (SDK)",
    },
    {
        "id": "challenge_catalog",
        "filename": "challenge_catalog.json",
        "schema_version": 1,
        "notes": "Challenge catalog (SDK)",
    },
]

SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_semver(value: str) -> tuple[int, int, int]:
    match = SEMVER_RE.match(value.strip())
    if not match:
        raise ValueError(f"Invalid SemVer: {value!r}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def bump_semver(value: str, part: str) -> str:
    major, minor, patch = parse_semver(value)
    if part == "major":
        return f"{major + 1}.0.0"
    if part == "minor":
        return f"{major}.{minor + 1}.0"
    if part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unknown bump part: {part}")


def load_existing_data_version() -> str:
    if not MANIFEST_PATH.exists():
        return "1.0.0"
    try:
        payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        raw = str(payload.get("data_version") or "1.0.0").strip()
        raw = raw.removeprefix("data-v").removeprefix("v")
        parse_semver(raw)
        return raw
    except Exception:
        return "1.0.0"


def build_manifest(data_version: str, min_app_version: str) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    missing: list[str] = []
    for spec in FILE_SPECS:
        path = DATA_DIR / spec["filename"]
        if not path.is_file():
            missing.append(spec["filename"])
            continue
        digest = sha256_file(path)
        entry: dict[str, Any] = {
            "id": spec["id"],
            "path": spec["filename"],
            "url": f"{RAW_BASE}/{spec['filename']}",
            "sha256": digest,
            "bytes": path.stat().st_size,
            "schema_version": int(spec["schema_version"]),
        }
        if spec.get("primary"):
            entry["primary_url"] = spec["primary"]
        if spec.get("notes"):
            entry["notes"] = spec["notes"]
        files.append(entry)

    if missing:
        raise FileNotFoundError(
            "Missing docs/data files required for manifest:\n  - " + "\n  - ".join(missing)
        )

    return {
        "schema_version": 1,
        "data_version": data_version,
        "data_version_label": f"data-v{data_version}",
        "published_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "min_app_version": min_app_version,
        "manifest_urls": {
            "release": RELEASE_MANIFEST_URL,
            "raw_main": f"{RAW_BASE}/catalog_manifest.json",
        },
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-version",
        default="",
        help="Explicit data SemVer (e..g. 1.0.0). Default: keep existing or 1.0.0",
    )
    parser.add_argument(
        "--bump",
        choices=("major", "minor", "patch"),
        default="",
        help="Bump existing data_version instead of --data-version",
    )
    parser.add_argument(
        "--min-app-version",
        default="2.3.0",
        help="Minimum Electron app SemVer that understands this manifest",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify existing manifest hashes match files (no write)",
    )
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if args.check:
        if not MANIFEST_PATH.exists():
            print("FAIL: catalog_manifest.json missing", file=sys.stderr)
            return 2
        current = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        errors = 0
        for entry in current.get("files") or []:
            rel = entry.get("path") or ""
            path = DATA_DIR / rel
            if not path.is_file():
                print(f"FAIL: missing {rel}")
                errors += 1
                continue
            digest = sha256_file(path)
            size = path.stat().st_size
            if digest != entry.get("sha256"):
                print(f"FAIL: sha256 mismatch {rel}")
                errors += 1
            elif size != int(entry.get("bytes") or -1):
                print(f"FAIL: bytes mismatch {rel}")
                errors += 1
            else:
                print(f"OK  {rel}  {digest[:12]}…  {size} bytes")
        if errors:
            print(f"FAIL: {errors} error(s)", file=sys.stderr)
            return 1
        print(f"OK  manifest data_version={current.get('data_version_label') or current.get('data_version')}")
        return 0

    if args.bump and args.data_version:
        print("Use only one of --bump or --data-version", file=sys.stderr)
        return 2

    if args.bump:
        data_version = bump_semver(load_existing_data_version(), args.bump)
    elif args.data_version:
        data_version = args.data_version.strip().removeprefix("data-v").removeprefix("v")
        parse_semver(data_version)
    else:
        data_version = load_existing_data_version()

    manifest = build_manifest(data_version, args.min_app_version.strip())
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {MANIFEST_PATH.relative_to(ROOT)}")
    print(f"  data_version: data-v{data_version}")
    print(f"  files: {len(manifest['files'])}")
    for entry in manifest["files"]:
        print(f"  - {entry['id']}: {entry['bytes']} bytes  sha256={entry['sha256'][:12]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
