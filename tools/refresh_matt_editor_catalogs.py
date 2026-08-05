#!/usr/bin/env python3
"""Refresh Matt editor / MSBT catalogs from save-editor.be + live LootLemon.

Steps:
  1) Sync Nexus LegitItems JSON from save-editor.be nexus_data_proxy
  2) Merge live GZO family-data.js part ids into resources/gzo_parts_map.json
  3) Refresh MattsSDKBoostingTools_gzo_codes.json via tools/refresh_gzo_release_catalog.js
  4) Refresh MattsSDKBoostingTools_lootlemon_codes.json (add missing live items + fix encoding)
  5) Mirror updated resource JSONs into mod_extracted when present
  6) Regenerate Matt editor part supplements via tools/audit_matt_editor_modded_parts.py

Safe defaults: backups before overwrite; atomic replace; does not commit.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "external_app" / "v22_parts_codes_fixed"
RESOURCES = APP / "resources"
LEGIT = APP / "matt_editor" / "LegitItems"
MOD_EXTRACTED = ROOT / "mod_extracted" / "MattsSDKBoostingTools"
BACKUP_DIR = ROOT / "_tmp_catalog_compare" / "backups"
REPORT_PATH = ROOT / "_tmp_catalog_compare" / "refresh_report.json"

NEXUS_PROXY = "https://save-editor.be/LegitItems/nexus_data_proxy.php"
GZO_FAMILY_URL = "https://save-editor.be/GZO/Borderlands4/family-data.js?v=master-parts"
UA = "MSBT-catalog-refresh/1.1 (+maintainer catalog sync)"

LOOTLEMON_CACHE_VERSION = 5
LOOTLEMON_CATEGORIES = [
    ("Weapons", "https://www.lootlemon.com/db/borderlands-4/weapons"),
    ("Shields", "https://www.lootlemon.com/db/borderlands-4/shields"),
    ("Ordnance", "https://www.lootlemon.com/db/borderlands-4/ordnance"),
    ("Repkits", "https://www.lootlemon.com/db/borderlands-4/repkits"),
    ("Class Mods", "https://www.lootlemon.com/db/borderlands-4/class-mods"),
    ("Enhancements", "https://www.lootlemon.com/db/borderlands-4/enhancements"),
]

ITEM_HREF_RE = re.compile(
    r'href="((?:https://www\.lootlemon\.com)?/'
    r'(?:weapon|shield|grenade-mod|repkit|class-mod|enhancement|bonus-item)/'
    r'[^"#?]+)"',
    re.I,
)
ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')
SERIAL_RE = re.compile(r"@U[!-~]{10,}")
DB_ITEM_OPEN_RE = re.compile(r"<div\b[^>]*\bdata-name=\"[^\"]+\"[^>]*>", re.I)

# Local PHP whitelist order (must stay in sync with LegitItems/nexus_data_proxy.php).
NEXUS_FILE_MAP: dict[str, str] = {
    "inv0": "Nexus-Data-inv0.json",
    "inv4": "Nexus-Data-inv4.json",
    "inv": "Nexus-Data-inv.json",
    "inv6": "Nexus-Data-inv6.json",
    "inv_custom0": "Nexus-Data-inv_custom0.json",
    "inv_custom4": "Nexus-Data-inv_custom4.json",
    "inv_name_part0": "Nexus-Data-inv_name_part0.json",
    "inv_name_part4": "Nexus-Data-inv_name_part4.json",
    "inv_name_part6": "Nexus-Data-inv_name_part6.json",
    "inv_stat0": "Nexus-Data-inv_stat0.json",
    "inv_stat4": "Nexus-Data-inv_stat4.json",
    "ui_stat0": "Nexus-Data-ui_stat0.json",
    "ui_stat4": "Nexus-Data-ui_stat4.json",
    "ui_stat6": "Nexus-Data-ui_stat6.json",
    "ui_challenge_list0": "Nexus-Data-ui_challenge_list0.json",
    "attribute0": "Nexus-Data-attribute0.json",
    "attribute4": "Nexus-Data-attribute4.json",
    "attribute6": "Nexus-Data-attribute6.json",
    "gbx_ue_data_table0": "Nexus-Data-gbx_ue_data_table0.json",
    "gbx_ue_data_table4": "Nexus-Data-gbx_ue_data_table4.json",
    "gbx_ue_data_table6": "Nexus-Data-gbx_ue_data_table6.json",
    "itempool0": "Nexus-Data-itempool0.json",
    "itempool4": "Nexus-Data-itempool4.json",
    "itempool6": "Nexus-Data-itempool6.json",
    "itempoollist0": "Nexus-Data-ItemPoolList0.json",
    "itempoollist4": "Nexus-Data-ItemPoolList4.json",
    "itempoollist6": "Nexus-Data-ItemPoolList6.json",
    "skilltrees_data0": "Nexus-Data-skilltrees_data0.json",
    "skilltrees_data4": "Nexus-Data-skilltrees_data4.json",
    "skilltrees_data6": "Nexus-Data-skilltrees_data6.json",
    "uitooltipdata0": "Nexus-Data-uitooltipdata0.json",
    "uitooltipdata4": "Nexus-Data-uitooltipdata4.json",
    "uitooltipdata6": "Nexus-Data-uitooltipdata6.json",
    "resident0": "Nexus-Data-Resident0.json",
    "resident4": "Nexus-Data-Resident4.json",
    "resident6": "Nexus-Data-Resident6.json",
    "gbxactorpart0": "Nexus-Data-GbxActorPart0.json",
    "gbxactorpart4": "Nexus-Data-GbxActorPart4.json",
    "gbxactorpart6": "Nexus-Data-GbxActorPart6.json",
    "challenge0": "Nexus-Data-challenge0.json",
    "challenge4": "Nexus-Data-challenge4.json",
    "challenge6": "Nexus-Data-challenge6.json",
    "challenge_list0": "Nexus-Data-challenge_list0.json",
    "challenge_list4": "Nexus-Data-challenge_list4.json",
    "challenge_list6": "Nexus-Data-challenge_list6.json",
    "mission0": "Nexus-Data-Mission0.json",
    "mission4": "Nexus-Data-Mission4.json",
    "mission6": "Nexus-Data-Mission6.json",
    "missionset0": "Nexus-Data-missionset0.json",
    "missionset4": "Nexus-Data-missionset4.json",
    "missionset6": "Nexus-Data-missionset6.json",
    "gbx_discovery_location_meta_data4": "Nexus-Data-gbx_discovery_location_meta_data4.json",
    "gbx_discovery_location_meta_data6": "Nexus-Data-gbx_discovery_location_meta_data6.json",
    "game_region0": "Nexus-Data-game_region0.json",
    "game_region4": "Nexus-Data-game_region4.json",
    "game_region6": "Nexus-Data-game_region6.json",
    "progress_graph_group0": "Nexus-Data-progress_graph_group0.json",
    "progress_graph_group4": "Nexus-Data-progress_graph_group4.json",
    "progress_graph0": "Nexus-Data-progress_graph0.json",
    "progress_graph4": "Nexus-Data-progress_graph4.json",
    "progress_graph6": "Nexus-Data-progress_graph6.json",
    "progress_graph_group6": "Nexus-Data-progress_graph_group6.json",
}

WATCHLIST = [
    "PRISM",
    "Silver Sliver",
    "Overconsumption",
    "Plumb Bob",
    "Divided Glow",
    "Eradication",
    "Stealth & Seek",
    "Hydrowerks",
    "Oxidation",
    "Loiter Sploiter",
    "Pressure Kettle",
    "Kaos",
    "Pachonk",
    "Verce",
    "Filántropo",
    "Reaparición",
    "Lamé",
]


def log(msg: str) -> None:
    print(msg, flush=True)


def fetch_bytes(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_text(url: str, timeout: int = 120) -> str:
    return fetch_bytes(url, timeout=timeout).decode("utf-8", "replace")


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{int(time.time())}")
    tmp.write_text(text, encoding=encoding)
    tmp.replace(path)


def atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{int(time.time())}")
    tmp.write_bytes(data)
    tmp.replace(path)


def backup_file(path: Path) -> Path | None:
    if not path.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = BACKUP_DIR / f"{path.name}.{stamp}.bak"
    shutil.copy2(path, dest)
    return dest


def norm_name(s: str) -> str:
    s = html.unescape(s or "").strip().lower()
    s = s.replace("\u2019", "'").replace("\u2018", "'")
    return re.sub(r"\s+", " ", s)


def fold_name(s: str) -> str:
    # Drop accents/punctuation; also collapse spaces so "Fil ntropo" matches "Filántropo".
    return re.sub(r"[^a-z0-9'&]+", "", norm_name(s))


def parse_attrs(tag_open: str) -> dict[str, str]:
    return {k: html.unescape(v) for k, v in ATTR_RE.findall(tag_open)}


def unescape_serial_fragment(text: str) -> str:
    # Named entities only; keep numeric entities intact for Base85 safety.
    out: list[str] = []
    i = 0
    while i < len(text):
        if text[i] == "&":
            m = re.match(r"&([a-zA-Z][a-zA-Z0-9]*);", text[i:])
            if m:
                out.append(html.unescape(m.group(0)))
                i += len(m.group(0))
                continue
        out.append(text[i])
        i += 1
    return "".join(out)


def trim_serial_tail(serial: str) -> str:
    serial = str(serial or "").strip()
    serial = re.sub(r"(</?[a-zA-Z][^>]*>)+$", "", serial)
    serial = serial.rstrip("\\\"'>")
    return serial


def is_valid_serial(serial: str) -> bool:
    serial = str(serial or "").strip()
    return bool(
        serial.startswith("@U")
        and len(serial) >= 20
        and "xxxx" not in serial.lower()
        and re.fullmatch(r"@[!-~]+", serial)
    )


# ---------------------------------------------------------------------------
# Nexus sync
# ---------------------------------------------------------------------------


def sync_nexus(keys: list[str] | None = None) -> dict[str, Any]:
    wanted = keys or list(NEXUS_FILE_MAP.keys())
    results: dict[str, Any] = {"ok": [], "missing_remote": [], "failed": [], "bytes": {}}
    for key in wanted:
        filename = NEXUS_FILE_MAP[key]
        url = f"{NEXUS_PROXY}?file={urllib.parse.quote(key)}"
        dest = LEGIT / filename
        try:
            data = fetch_bytes(url, timeout=180)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                results["missing_remote"].append(key)
                log(f"  nexus skip (404): {key}")
                continue
            results["failed"].append({"key": key, "error": str(exc)})
            log(f"  nexus FAIL {key}: {exc}")
            continue
        except Exception as exc:
            results["failed"].append({"key": key, "error": str(exc)})
            log(f"  nexus FAIL {key}: {exc}")
            continue

        # Validate JSON before replacing local.
        try:
            json.loads(data.decode("utf-8"))
        except Exception as exc:
            results["failed"].append({"key": key, "error": f"invalid json: {exc}"})
            log(f"  nexus FAIL {key}: invalid JSON ({exc})")
            continue

        if dest.exists():
            backup_file(dest)
        atomic_write_bytes(dest, data)
        results["ok"].append(key)
        results["bytes"][key] = len(data)
        log(f"  nexus synced {key} -> {filename} ({len(data)} bytes)")
    return results


# ---------------------------------------------------------------------------
# GZO parts map merge
# ---------------------------------------------------------------------------


def parse_family_data(text: str) -> tuple[dict[str, Any], dict[str, str]]:
    marker = "window.__FAMILY_DATA__ = "
    if marker not in text:
        raise ValueError("family-data.js missing window.__FAMILY_DATA__")
    start = text.index(marker) + len(marker)
    payload = text[start : text.rfind(";")].strip()
    data = json.loads(payload)
    families = data.get("families") or {}
    display_names = data.get("displayNames") or []
    pairs: dict[str, str] = {}
    for family_id_text, rows in families.items():
        if not str(family_id_text).isdigit() or not isinstance(rows, list):
            continue
        type_id = int(family_id_text)
        for row in rows:
            columns = [part.strip() for part in str(row).split("\t")]
            token_column = columns[0] if columns else str(row)
            for match in re.finditer(r"\{(?:" + str(type_id) + r":)?(-?\d+)\}", token_column):
                part_id = int(match.group(1))
                full_id = f"{type_id}:{part_id}"
                if full_id in pairs:
                    continue
                name = columns[1] if len(columns) > 1 else full_id
                pairs[full_id] = name
    return data, pairs


def load_local_gzo_pairs(data: dict[str, Any]) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for fam, parts in data.items():
        if not isinstance(parts, dict):
            continue
        m = re.match(r"^(\d+)\s*\|", str(fam))
        if not m:
            continue
        tid = int(m.group(1))
        for pid, name in parts.items():
            try:
                pairs[f"{tid}:{int(pid)}"] = str(name)
            except Exception:
                continue
    return pairs


def family_key_for_type(type_id: int, display_names: list[Any], local: dict[str, Any]) -> str:
    for key in local:
        m = re.match(r"^(\d+)\s*\|", str(key))
        if m and int(m.group(1)) == type_id:
            return str(key)
    name = ""
    if 0 <= type_id - 1 < len(display_names):
        name = str(display_names[type_id - 1] or "")
    elif 0 <= type_id < len(display_names):
        name = str(display_names[type_id] or "")
    name = name.strip() or f"Type {type_id}"
    return f"{type_id} | {name}"


def merge_gzo_parts_map() -> dict[str, Any]:
    path = RESOURCES / "gzo_parts_map.json"
    backup_file(path)
    local = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(local, dict):
        raise ValueError("gzo_parts_map.json root must be an object")

    family_text = fetch_text(GZO_FAMILY_URL, timeout=180)
    (ROOT / "gzo_family-data.js").write_text(family_text, encoding="utf-8")
    meta, live_pairs = parse_family_data(family_text)
    local_pairs_before = load_local_gzo_pairs(local)
    display_names = meta.get("displayNames") or []

    added = 0
    for full_id, live_name in live_pairs.items():
        if full_id in local_pairs_before:
            continue
        type_id_text, part_id_text = full_id.split(":", 1)
        type_id = int(type_id_text)
        part_id = int(part_id_text)
        key = family_key_for_type(type_id, display_names, local)
        bucket = local.setdefault(key, {})
        if not isinstance(bucket, dict):
            bucket = {}
            local[key] = bucket
        bucket[str(part_id)] = str(live_name)
        added += 1

    atomic_write_text(path, json.dumps(local, ensure_ascii=False, indent=2) + "\n")
    after_pairs = load_local_gzo_pairs(local)
    return {
        "before_pairs": len(local_pairs_before),
        "after_pairs": len(after_pairs),
        "added": added,
        "live_pairs": len(live_pairs),
        "families": len(local),
        "gzo_meta": {
            "generatedAt": meta.get("generatedAt"),
            "masterGeneratedAt": meta.get("masterGeneratedAt"),
            "maxId": meta.get("maxId"),
            "families_count": len(meta.get("families") or {}),
        },
        "watchlist_hits": {
            name: sorted(
                (fid for fid, label in after_pairs.items() if name.lower() in label.lower()),
                key=lambda x: tuple(int(p) for p in x.split(":")),
            )[:12]
            for name in WATCHLIST
        },
    }


# ---------------------------------------------------------------------------
# LootLemon refresh
# ---------------------------------------------------------------------------


def extract_pagination(html_text: str) -> tuple[str | None, int]:
    m = re.search(r'data-load-pages="(\d+)"', html_text)
    pages = int(m.group(1)) if m else 0
    m2 = re.search(r'id="load-pages"[^>]*href="([^"]+)"', html_text)
    if not m2:
        m2 = re.search(r'href="([^"]+)"[^>]*id="load-pages"', html_text)
    base = m2.group(1) if m2 else None
    return base, pages


def abs_lootlemon(href: str) -> str:
    return urllib.parse.urljoin("https://www.lootlemon.com", href)


def extract_listing_items(html_text: str, category: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for m in DB_ITEM_OPEN_RE.finditer(html_text):
        tag = m.group(0)
        attrs = parse_attrs(tag)
        name = attrs.get("data-name") or ""
        if not name:
            continue
        if "data-rarity" not in attrs and "db_item" not in tag and "w-dyn-item" not in tag:
            continue
        # Find nearest page link in a following window of the item card.
        window = html_text[m.start() : m.start() + 2500]
        href_m = re.search(
            r'aria-label="Page link"[^>]*href="([^"]+)"|href="([^"]+)"[^>]*aria-label="Page link"',
            window,
            re.I,
        )
        href = ""
        if href_m:
            href = href_m.group(1) or href_m.group(2) or ""
        if not href:
            # fallback: first item-like href in window
            for hm in ITEM_HREF_RE.finditer(window):
                href = hm.group(1)
                break
        items.append(
            {
                "name": name,
                "category": category,
                "rarity": (attrs.get("data-rarity") or "").removeprefix("h-").removeprefix("f-"),
                "manufacturer": attrs.get("data-manufacturer") or "",
                "subtype": attrs.get("data-type") or "",
                "content": attrs.get("data-content") or "",
                "url": abs_lootlemon(href) if href else "",
            }
        )
    # Dedup by folded name, prefer rows with urls.
    by_fold: dict[str, dict[str, str]] = {}
    for it in items:
        key = fold_name(it["name"])
        prev = by_fold.get(key)
        if prev is None or (not prev.get("url") and it.get("url")):
            by_fold[key] = it
    return list(by_fold.values())


def page_url_from_load_href(category_url: str, load_href: str, page: int) -> str:
    """Build Webflow collection page URL from load-pages href like ?aa6d804c_page=2."""
    # JS pattern used by LootLemon: n = href.slice(0,-1); fetch(n + pageNum)
    href = (load_href or "").strip()
    if href:
        n = href[:-1]
        return urllib.parse.urljoin(category_url, f"{n}{page}")
    return f"{category_url.split('?', 1)[0]}?aa6d804c_page={page}"


def collect_live_lootlemon() -> list[dict[str, str]]:
    all_items: list[dict[str, str]] = []
    for category, url in LOOTLEMON_CATEGORIES:
        log(f"  lootlemon list {category}")
        html_text = fetch_text(url, timeout=90)
        items = extract_listing_items(html_text, category)
        base, extra_pages = extract_pagination(html_text)
        if extra_pages:
            for page in range(2, extra_pages + 2):
                page_url = page_url_from_load_href(url, base or "", page)
                log(f"    page {page}: {page_url}")
                try:
                    page_html = fetch_text(page_url, timeout=90)
                except Exception as exc:
                    log(f"    page {page} FAIL: {exc}")
                    break
                more = extract_listing_items(page_html, category)
                if not more:
                    break
                seen = {fold_name(x["name"]) for x in items}
                added = 0
                for it in more:
                    k = fold_name(it["name"])
                    if k in seen:
                        continue
                    items.append(it)
                    seen.add(k)
                    added += 1
                if added == 0:
                    break
        log(f"    -> {len(items)} unique")
        all_items.extend(items)
    return all_items


def extract_serials_from_detail(detail_html: str) -> list[str]:
    text = unescape_serial_fragment(detail_html)
    serials: list[str] = []
    for m in SERIAL_RE.finditer(text):
        serial = trim_serial_tail(m.group(0))
        # closing paren after markup
        if serial and not serial.endswith(")"):
            tail = unescape_serial_fragment(detail_html[m.end() : m.end() + 96])
            tail = re.sub(r"^\s*(?:</?[^>]+>\s*)*", "", tail)
            if tail.startswith(")"):
                serial += ")"
        if not is_valid_serial(serial):
            continue
        if serial not in serials:
            serials.append(serial)
    return serials


def title_rarity(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        return ""
    return raw[:1].upper() + raw[1:].lower()


def refresh_lootlemon() -> dict[str, Any]:
    path = RESOURCES / "MattsSDKBoostingTools_lootlemon_codes.json"
    backup_file(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    entries = list(payload.get("entries") or [])
    before = len(entries)

    by_fold: dict[str, dict[str, Any]] = {}
    by_url: dict[str, dict[str, Any]] = {}
    for e in entries:
        if not isinstance(e, dict):
            continue
        fk = fold_name(str(e.get("name") or ""))
        if fk:
            by_fold[fk] = e
        url = str(e.get("url") or "").rstrip("/").lower()
        if url:
            by_url[url] = e

    live_items = collect_live_lootlemon()
    added: list[str] = []
    renamed: list[dict[str, str]] = []
    missing_serial: list[dict[str, str]] = []
    fetched = 0

    for it in live_items:
        name = it["name"]
        fk = fold_name(name)
        url = (it.get("url") or "").rstrip("/")
        existing = by_fold.get(fk) or (by_url.get(url.lower()) if url else None)

        if existing is not None:
            old_name = str(existing.get("name") or "")
            if old_name != name and fold_name(old_name) == fk:
                existing["name"] = name
                renamed.append({"from": old_name, "to": name, "category": it["category"]})
            if url and not existing.get("url"):
                existing["url"] = url
            # keep existing serial
            continue

        if not url:
            missing_serial.append({**it, "reason": "no detail url on listing"})
            continue

        try:
            detail = fetch_text(url, timeout=60)
            fetched += 1
            time.sleep(0.15)
        except Exception as exc:
            missing_serial.append({**it, "reason": f"fetch failed: {exc}"})
            continue

        serials = extract_serials_from_detail(detail)
        if not serials:
            missing_serial.append({**it, "reason": "no @U serial on detail page"})
            continue

        serial = serials[0]
        row = {
            "category": it["category"],
            "id": f"lootlemon:{it['category']}:{name}:0:{abs(hash(serial)) & 0xFFFFFFFFFFFFFFFF}",
            "manufacturer": (it.get("manufacturer") or "").title() if it.get("manufacturer") else "",
            "name": name,
            "rarity": title_rarity(it.get("rarity") or ""),
            "serial": serial,
            "source": "Lootlemon",
            "url": url,
            "content": it.get("content") or "",
        }
        entries.append(row)
        by_fold[fk] = row
        by_url[url.lower()] = row
        added.append(name)
        log(f"    + {it['category']}: {name}")

    # Stable sort by category then name
    entries.sort(key=lambda e: (str(e.get("category") or ""), fold_name(str(e.get("name") or "")), str(e.get("id") or "")))

    out = {
        "entries": entries,
        "source": "Lootlemon BL4",
        "updated": int(time.time()),
        "version": LOOTLEMON_CACHE_VERSION,
    }
    atomic_write_text(path, json.dumps(out, ensure_ascii=False, indent=4) + "\n")
    return {
        "before": before,
        "after": len(entries),
        "added": added,
        "renamed_encoding": renamed,
        "missing_serial": missing_serial,
        "live_unique": len(live_items),
        "detail_fetches": fetched,
        "by_category": dict(Counter(str(e.get("category") or "") for e in entries)),
    }


# ---------------------------------------------------------------------------
# GZO codes + audit + mirror
# ---------------------------------------------------------------------------


def refresh_gzo_codes() -> dict[str, Any]:
    script = ROOT / "tools" / "refresh_gzo_release_catalog.js"
    before_path = RESOURCES / "MattsSDKBoostingTools_gzo_codes.json"
    before = 0
    if before_path.exists():
        data = json.loads(before_path.read_text(encoding="utf-8"))
        before = len(data.get("entries") or [])
        backup_file(before_path)
    proc = subprocess.run(
        ["node", str(script)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"GZO codes refresh failed:\n{proc.stdout}\n{proc.stderr}")
    after_data = json.loads(before_path.read_text(encoding="utf-8"))
    after = len(after_data.get("entries") or [])
    return {"before": before, "after": after, "stdout": proc.stdout.strip()}


def run_audit_supplements() -> dict[str, Any]:
    script = ROOT / "tools" / "audit_matt_editor_modded_parts.py"
    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-2000:],
    }


def mirror_resources() -> list[str]:
    copied: list[str] = []
    if not MOD_EXTRACTED.exists():
        return copied
    for name in (
        "gzo_parts_map.json",
        "MattsSDKBoostingTools_lootlemon_codes.json",
        "MattsSDKBoostingTools_gzo_codes.json",
    ):
        src = RESOURCES / name
        dest = MOD_EXTRACTED / name
        if not src.exists():
            continue
        if dest.exists() or name == "gzo_parts_map.json" or dest.parent.exists():
            # Only overwrite if dest already exists, or for known mirrored files.
            if dest.exists() or name in {"gzo_parts_map.json", "MattsSDKBoostingTools_lootlemon_codes.json"}:
                backup_file(dest) if dest.exists() else None
                shutil.copy2(src, dest)
                copied.append(str(dest.relative_to(ROOT)))
                log(f"  mirrored {name} -> mod_extracted")
    return copied


def verify_watchlist() -> dict[str, Any]:
    ll = json.loads((RESOURCES / "MattsSDKBoostingTools_lootlemon_codes.json").read_text(encoding="utf-8"))
    entries = ll.get("entries") or []
    folds = {fold_name(e.get("name") or ""): e for e in entries}
    gzo = json.loads((RESOURCES / "gzo_parts_map.json").read_text(encoding="utf-8"))
    gzo_pairs = load_local_gzo_pairs(gzo)
    nexus = (LEGIT / "Nexus-Data-inv_name_part4.json").read_text(encoding="utf-8", errors="replace")
    nexus_low = nexus.lower()

    out = {}
    for name in WATCHLIST:
        fk = fold_name(name)
        entry = folds.get(fk)
        gzo_hits = [fid for fid, label in gzo_pairs.items() if name.lower() in label.lower()]
        out[name] = {
            "in_lootlemon": bool(entry),
            "lootlemon_serial": (entry or {}).get("serial", "")[:40] if entry else "",
            "lootlemon_url": (entry or {}).get("url", "") if entry else "",
            "in_nexus_inv_name_part4": name.lower() in nexus_low,
            "gzo_part_hits": len(gzo_hits),
            "gzo_sample": gzo_hits[:5],
        }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-nexus", action="store_true")
    parser.add_argument("--skip-gzo-map", action="store_true")
    parser.add_argument("--skip-gzo-codes", action="store_true")
    parser.add_argument("--skip-lootlemon", action="store_true")
    parser.add_argument("--skip-audit", action="store_true")
    parser.add_argument("--skip-mirror", action="store_true")
    parser.add_argument(
        "--nexus-keys",
        default="",
        help="Comma-separated nexus proxy keys (default: all whitelist keys)",
    )
    args = parser.parse_args()

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "steps": {},
    }

    if not args.skip_nexus:
        log("== Sync Nexus LegitItems ==")
        keys = [k.strip() for k in args.nexus_keys.split(",") if k.strip()] or None
        report["steps"]["nexus"] = sync_nexus(keys)

    if not args.skip_gzo_map:
        log("== Merge GZO parts map ==")
        report["steps"]["gzo_parts_map"] = merge_gzo_parts_map()
        log(
            f"  pairs {report['steps']['gzo_parts_map']['before_pairs']} -> "
            f"{report['steps']['gzo_parts_map']['after_pairs']} "
            f"(+{report['steps']['gzo_parts_map']['added']})"
        )

    if not args.skip_gzo_codes:
        log("== Refresh GZO codes catalog ==")
        report["steps"]["gzo_codes"] = refresh_gzo_codes()
        log(report["steps"]["gzo_codes"]["stdout"])

    if not args.skip_lootlemon:
        log("== Refresh LootLemon codes ==")
        report["steps"]["lootlemon"] = refresh_lootlemon()
        ll = report["steps"]["lootlemon"]
        log(f"  entries {ll['before']} -> {ll['after']} (+{len(ll['added'])})")
        if ll["missing_serial"]:
            log(f"  WARNING: {len(ll['missing_serial'])} live item(s) without serial")
            for row in ll["missing_serial"]:
                log(f"    - {row.get('category')}: {row.get('name')} ({row.get('reason')})")

    if not args.skip_mirror:
        log("== Mirror resources ==")
        report["steps"]["mirrored"] = mirror_resources()

    if not args.skip_audit:
        log("== Regenerate Matt editor supplements ==")
        report["steps"]["audit"] = run_audit_supplements()
        if not report["steps"]["audit"]["ok"]:
            log("  audit FAILED")
            log(report["steps"]["audit"]["stderr"] or report["steps"]["audit"]["stdout"])
        else:
            log("  audit OK")
            # keep short tail
            for line in (report["steps"]["audit"]["stdout"] or "").splitlines()[-20:]:
                log("    " + line)

    log("== Verify watchlist ==")
    report["verify_watchlist"] = verify_watchlist()
    for name, info in report["verify_watchlist"].items():
        log(
            f"  {name}: lootlemon={info['in_lootlemon']} "
            f"nexus={info['in_nexus_inv_name_part4']} gzo_hits={info['gzo_part_hits']}"
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(f"Wrote {REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
