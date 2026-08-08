#!/usr/bin/env python3
"""Publish an MSBT data-only GitHub release (no app SemVer bump).

Rebuilds docs/data/catalog_manifest.json hashes, optionally bumps data SemVer,
and can create a GitHub Release tagged data-vX.Y.Z with catalog assets attached.

Requires `gh` authenticated for --create-release.

Usage:
  python tools/publish_data_release.py --bump patch --dry-run
  python tools/publish_data_release.py --bump patch --create-release
  python tools/publish_data_release.py --data-version 1.0.1 --create-release
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "docs" / "data"
MANIFEST_PATH = DATA_DIR / "catalog_manifest.json"
BUILD_SCRIPT = ROOT / "tools" / "build_data_catalog_manifest.py"


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("+", " ".join(cmd))
    return subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, check=check)


def ensure_gh() -> None:
    if shutil.which("gh") is None:
        raise SystemExit("gh CLI not found on PATH. Install GitHub CLI or skip --create-release.")
    status = run(["gh", "auth", "status"], check=False)
    if status.returncode != 0:
        sys.stderr.write(status.stderr or status.stdout or "gh auth status failed\n")
        raise SystemExit("gh is not authenticated. Run: gh auth login")


def build_manifest(args: argparse.Namespace) -> dict:
    cmd = [sys.executable, str(BUILD_SCRIPT)]
    if args.bump:
        cmd.extend(["--bump", args.bump])
    elif args.data_version:
        cmd.extend(["--data-version", args.data_version])
    if args.min_app_version:
        cmd.extend(["--min-app-version", args.min_app_version])
    proc = run(cmd)
    sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)
    if not MANIFEST_PATH.is_file():
        raise SystemExit("Manifest was not written.")
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def check_manifest() -> None:
    proc = run([sys.executable, str(BUILD_SCRIPT), "--check"])
    sys.stdout.write(proc.stdout)
    if proc.stderr:
        sys.stderr.write(proc.stderr)


def create_github_release(manifest: dict, *, draft: bool, title: str, prerelease: bool) -> str:
    ensure_gh()
    label = str(manifest.get("data_version_label") or f"data-v{manifest.get('data_version')}")
    tag = label if label.startswith("data-v") else f"data-v{label}"
    published = str(manifest.get("published_at") or "")
    file_count = len(manifest.get("files") or [])
    notes = "\n".join(
        [
            f"MSBT **data-only** release `{tag}`.",
            "",
            "Does **not** change Electron/SDK app SemVer.",
            "Marked as a **prerelease** on purpose so it does not become GitHub `releases/latest` (app update channel).",
            f"Published: {published or 'n/a'}",
            f"Files: {file_count}",
            "",
            "Manifest URL:",
            f"`https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/{tag}/catalog_manifest.json`",
            "",
            "Durable fallback:",
            "`https://raw.githubusercontent.com/funkyoushift/MattsSDKBoostingTools/main/docs/data/catalog_manifest.json`",
            "",
            "Included catalogs:",
            *[f"- `{entry.get('id')}` → `{entry.get('path')}`" for entry in (manifest.get("files") or [])],
        ]
    )

    with tempfile.TemporaryDirectory(prefix="msbt-data-release-") as tmp:
        tmp_path = Path(tmp)
        staged: list[Path] = []
        for name in ("catalog_manifest.json",):
            src = DATA_DIR / name
            dst = tmp_path / name
            shutil.copy2(src, dst)
            staged.append(dst)
        for entry in manifest.get("files") or []:
            rel = entry.get("path") or ""
            src = DATA_DIR / rel
            if src.is_file():
                dst = tmp_path / Path(rel).name
                shutil.copy2(src, dst)
                staged.append(dst)

        cmd = [
            "gh",
            "release",
            "create",
            tag,
            "--title",
            title or tag,
            "--notes",
            notes,
        ]
        if draft:
            cmd.append("--draft")
        if prerelease:
            cmd.append("--prerelease")
        cmd.extend(str(path) for path in staged)
        proc = run(cmd)
        sys.stdout.write(proc.stdout)
        if proc.stderr:
            sys.stderr.write(proc.stderr)

    view = run(["gh", "release", "view", tag, "--json", "url", "-q", ".url"], check=False)
    url = (view.stdout or "").strip()
    return url or f"https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/{tag}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bump", choices=("major", "minor", "patch"), default="")
    parser.add_argument("--data-version", default="")
    parser.add_argument("--min-app-version", default="2.3.0")
    parser.add_argument("--create-release", action="store_true", help="Create GitHub release via gh")
    parser.add_argument("--draft", action="store_true", help="Create release as draft")
    parser.add_argument(
        "--prerelease",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Mark data release as prerelease (default: true, keeps app /latest intact)",
    )
    parser.add_argument("--title", default="", help="Optional release title")
    parser.add_argument("--dry-run", action="store_true", help="Rebuild + check only; no gh release")
    args = parser.parse_args()

    if args.bump and args.data_version:
        print("Use only one of --bump or --data-version", file=sys.stderr)
        return 2

    manifest = build_manifest(args)
    check_manifest()
    label = manifest.get("data_version_label") or manifest.get("data_version")
    print(f"Ready: {label} ({len(manifest.get('files') or [])} files)")

    if args.dry_run or not args.create_release:
        if not args.create_release:
            print("Skipping GitHub release (pass --create-release to publish).")
        return 0

    url = create_github_release(
        manifest,
        draft=args.draft,
        title=args.title,
        prerelease=bool(args.prerelease),
    )
    print(f"Published: {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
