#!/usr/bin/env python3
"""Re-compare local Lootlemon cache serials vs live detail pages.

Uses the same extraction as tools/refresh_matt_editor_catalogs.py.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from refresh_matt_editor_catalogs import (  # noqa: E402
    LOOTLEMON_DETAIL_SLEEP_S,
    extract_serials_from_detail,
    fetch_text,
)

USER_RAIDEN = "@UgwSAs35E/MjJ6DFiRy<sRHE*o!lK5a%A&%c@}NSYMxl10(xK/11{yvx2LJ"
DEFAULT_CACHE = (
    ROOT
    / "external_app"
    / "v22_parts_codes_fixed"
    / "resources"
    / "MattsSDKBoostingTools_lootlemon_codes.json"
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    ap.add_argument("--limit", type=int, default=0, help="Optional URL cap (0=all)")
    ap.add_argument("--out", type=Path, default=ROOT / "_tmp_catalog_compare" / "lootlemon_verify.json")
    args = ap.parse_args()

    data = json.loads(args.cache.read_text(encoding="utf-8"))
    entries = list(data.get("entries") or [])
    by_url: dict[str, list[dict]] = {}
    for e in entries:
        u = str(e.get("url") or "").strip()
        s = str(e.get("serial") or "").strip()
        if u.startswith("http") and s.startswith("@U"):
            by_url.setdefault(u, []).append(e)

    urls = list(by_url.keys())
    if args.limit and args.limit > 0:
        urls = urls[: args.limit]

    raiden = [e for e in entries if str(e.get("name") or "").lower() == "raiden"]
    print("--- RAIDEN ---")
    for e in raiden:
        serial = str(e.get("serial") or "")
        print("cache:", serial)
        print("user :", USER_RAIDEN)
        print("exact_match:", serial == USER_RAIDEN)

    ok = 0
    mismatches: list[dict] = []
    truncations: list[dict] = []
    errors: list[dict] = []
    no_live: list[dict] = []

    for i, url in enumerate(urls, start=1):
        rows = by_url[url]
        name = rows[0].get("name")
        local_serials = [str(e.get("serial") or "").strip() for e in rows]
        try:
            html = fetch_text(url, timeout=60)
            live_serials = extract_serials_from_detail(html)
            time.sleep(LOOTLEMON_DETAIL_SLEEP_S)
        except Exception as exc:
            errors.append({"name": name, "url": url, "error": str(exc)})
            print(f"[{i}/{len(urls)}] ERR {name}: {exc}", flush=True)
            continue

        if not live_serials:
            no_live.append({"name": name, "url": url, "local": local_serials[0]})
            print(f"[{i}/{len(urls)}] NO_LIVE {name}", flush=True)
            continue

        matched = any(ls in live_serials for ls in local_serials)
        if matched:
            ok += 1
            if i == 1 or i % 50 == 0 or i == len(urls):
                print(f"[{i}/{len(urls)}] OK {name}", flush=True)
            continue

        best_live = live_serials[0]
        trunc = False
        for ls in local_serials:
            for lv in live_serials:
                if lv.startswith(ls) and len(lv) > len(ls) + 2:
                    truncations.append({"name": name, "url": url, "local": ls, "live": lv})
                    trunc = True
                    break
            if trunc:
                break
        row = {
            "name": name,
            "url": url,
            "local": local_serials[0],
            "live": best_live,
            "live_candidates": live_serials[:3],
            "likely_truncation": trunc,
        }
        mismatches.append(row)
        tag = "TRUNC" if trunc else "DIFF"
        print(f"[{i}/{len(urls)}] {tag} {name}", flush=True)

    report = {
        "cache": str(args.cache),
        "urls_checked": len(urls),
        "ok": ok,
        "mismatch_count": len(mismatches),
        "truncation_count": len(truncations),
        "error_count": len(errors),
        "no_live_count": len(no_live),
        "truncations": truncations,
        "mismatches": mismatches,
        "errors": errors,
        "no_live": no_live,
        "raiden_ok": bool(raiden) and str(raiden[0].get("serial") or "") == USER_RAIDEN,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"\nok={ok} mismatches={len(mismatches)} truncations={len(truncations)} "
        f"errors={len(errors)} no_live={len(no_live)}"
    )
    print(f"wrote {args.out}")
    return 0 if report["raiden_ok"] and not truncations and not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
