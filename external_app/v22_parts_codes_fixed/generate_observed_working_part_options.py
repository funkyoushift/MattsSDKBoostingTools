from __future__ import annotations

import json
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

import external_legit_builder as builder
from external_app_paths import BASE_DIR, RESOURCE_DIR
from external_serial_tools import serial_to_human


SOURCE_FILES = [
    ("GZO", RESOURCE_DIR / "MattsSDKBoostingTools_gzo_codes.json"),
    ("Lootlemon", RESOURCE_DIR / "MattsSDKBoostingTools_lootlemon_codes.json"),
    ("Custom Static", RESOURCE_DIR / "custom_bl4_codes.json"),
]
OUTPUT_PATH = RESOURCE_DIR / "observed_working_part_options.json"
REPORT_PATH = BASE_DIR.parent.parent / "BUILDER_OBSERVED_PART_OPTIONS_REPORT.md"
TOKEN_RE = re.compile(r"\{[^{}]+\}")
ROOT_RE = re.compile(r"^\s*(\d+)\s*,")


def _load_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    entries = data.get("entries") if isinstance(data, dict) else None
    return [x for x in (entries or []) if isinstance(x, dict)]


def _entry_serial(entry: dict[str, Any]) -> str:
    for key in ("serial", "code", "base85", "value"):
        value = str(entry.get(key) or "").strip()
        if value:
            return value
    return ""


def _entry_meta(entry: dict[str, Any], source_name: str) -> dict[str, str]:
    return {
        "name": str(entry.get("name") or entry.get("title") or "Unnamed").strip()[:120],
        "source": str(entry.get("source") or source_name or "").strip()[:80],
        "listing": str(entry.get("listing") or entry.get("category") or "").strip()[:80],
        "creator": str(entry.get("creator") or "").strip()[:80],
        "type": str(entry.get("type") or entry.get("category") or "").strip()[:80],
    }


def _human_for_serial(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if text.startswith("@U"):
        return serial_to_human(text)
    if "|" in text and "{" in text:
        return text
    return ""


def _root_serial_from_human(human: str) -> int | None:
    match = ROOT_RE.search(human or "")
    if not match:
        return None
    try:
        return int(match.group(1))
    except Exception:
        return None


def _token_parts(token: str, current_root_serial: int) -> tuple[int, int] | None:
    body = str(token or "").strip()
    if body.startswith("{") and body.endswith("}"):
        body = body[1:-1].strip()
    if ":" in body:
        root_s, sub_s = body.split(":", 1)
    else:
        root_s, sub_s = str(current_root_serial), body
    try:
        return int(str(root_s).strip()), int(str(sub_s).strip())
    except Exception:
        return None


def _normal_part_signatures(root_key: str, table: str) -> set[str]:
    sigs: set[str] = set()
    for row in builder.search_parts(root_key, "", table=table, limit=10000):
        row_table = str(row.get("table") or table or "").strip()
        key = str(row.get("key") or "").strip()
        token = str(row.get("serial_token") or "").strip()
        if row_table and key:
            sigs.add(f"{row_table}:{key}".lower())
        if row_table and token:
            sigs.add(f"{row_table}:{token}".lower())
            if token.startswith("{") and token.endswith("}"):
                sigs.add(f"{row_table}:{token[1:-1]}".lower())
    return sigs


def _observed_option(
    *,
    current_root: dict[str, Any],
    source_part: dict[str, Any],
    source_root: dict[str, Any],
    token: str,
    meta: dict[str, str],
) -> dict[str, Any]:
    table = str(source_part.get("table") or "").strip()
    line = f"{table}:{token}"
    source_root_serial = int(source_root.get("serial") or 0)
    token_pair = _token_parts(token, int(current_root.get("serial") or 0))
    sub_serial = token_pair[1] if token_pair else source_part.get("serial")
    normal_sigs = _normal_part_signatures(str(current_root.get("key") or ""), table)
    already = line.lower() in normal_sigs or f"{table}:{source_part.get('key')}".lower() in normal_sigs
    return {
        "table": table,
        "key": source_part.get("key") or str(sub_serial),
        "line": line,
        "serial": sub_serial,
        "source_root_serial": source_root_serial,
        "source_root_key": source_root.get("key") or source_part.get("source_root_key") or "",
        "serial_token": token,
        "display": source_part.get("display") or source_part.get("debug") or source_part.get("internal") or source_part.get("key") or "",
        "debug": source_part.get("debug") or "",
        "internal": source_part.get("internal") or source_part.get("key") or "",
        "row": source_part.get("row") or "",
        "rarity": source_part.get("rarity") or "",
        "np_names": source_part.get("np_names") or source_part.get("name_parts") or [],
        "add": source_part.get("add") or [],
        "dep": source_part.get("dep") or [],
        "exclude": source_part.get("exclude") or [],
        "already_in_builder": already,
        "observed_count": 1,
        "examples": [meta],
    }


def generate() -> tuple[dict[str, Any], str]:
    # Generation must compare against the base builder rules only.  If a prior
    # observed-options file exists, do not let runtime observed lookup feed back
    # into the next generated resource.
    builder._OBSERVED_OPTIONS_CACHE = {"version": 1, "roots": {}}
    builder._OBSERVED_PART_INDEX_CACHE.clear()

    roots_by_serial: dict[int, dict[str, Any]] = {}
    for root in builder.all_roots():
        try:
            roots_by_serial[int(root.get("serial") or -1)] = root
        except Exception:
            pass
    buildable_by_serial: dict[int, dict[str, Any]] = {}
    for root in builder.roots():
        try:
            buildable_by_serial[int(root.get("serial") or -1)] = root
        except Exception:
            pass

    summary: Counter[str] = Counter()
    sources_seen: list[dict[str, Any]] = []
    roots: dict[str, dict[str, Any]] = {}
    unmapped_roots: Counter[int] = Counter()
    unmapped_tokens: Counter[str] = Counter()

    for source_name, path in SOURCE_FILES:
        entries = _load_entries(path)
        sources_seen.append({"source": source_name, "path": str(path), "entries": len(entries)})
        for entry in entries:
            summary["entries_scanned"] += 1
            value = _entry_serial(entry)
            if not value:
                summary["missing_serial"] += 1
                continue
            try:
                human = _human_for_serial(value)
            except Exception:
                summary["decode_failed"] += 1
                continue
            if not human:
                summary["decode_failed"] += 1
                continue
            summary["decoded"] += 1
            root_serial = _root_serial_from_human(human)
            if root_serial is None:
                summary["unknown_root"] += 1
                continue
            current_root = buildable_by_serial.get(root_serial)
            if not current_root:
                unmapped_roots[root_serial] += 1
                summary["unmapped_root"] += 1
                continue
            root_key = str(current_root.get("key") or "").lower()
            root_row = roots.setdefault(root_key, {
                "root_key": root_key,
                "root_serial": root_serial,
                "item_type": current_root.get("item_type") or "",
                "manufacturer": current_root.get("manufacturer") or "",
                "observed_parts": {},
                "unmapped_tokens": {},
            })
            meta = _entry_meta(entry, source_name)
            tokens: list[str] = []
            for token in TOKEN_RE.findall(human):
                for expanded in builder._expand_serial_token(token):
                    text = str(expanded or "").strip()
                    if text.startswith("{") and text.endswith("}"):
                        tokens.append(text)
            for token in tokens:
                summary["part_tokens"] += 1
                token_pair = _token_parts(token, root_serial)
                if not token_pair:
                    root_row["unmapped_tokens"][token] = root_row["unmapped_tokens"].get(token, 0) + 1
                    unmapped_tokens[token] += 1
                    continue
                source_serial, sub_serial = token_pair
                part = builder.describe_part(root_key, token)
                source_root = current_root
                if not part:
                    source_root = roots_by_serial.get(source_serial) or {}
                    source_key = str(source_root.get("key") or "").strip()
                    if source_key:
                        part = builder.describe_part(source_key, f"{{{sub_serial}}}")
                if not part:
                    root_row["unmapped_tokens"][token] = root_row["unmapped_tokens"].get(token, 0) + 1
                    unmapped_tokens[token] += 1
                    continue
                table = str(part.get("table") or "").strip()
                if not table:
                    root_row["unmapped_tokens"][token] = root_row["unmapped_tokens"].get(token, 0) + 1
                    unmapped_tokens[token] += 1
                    continue
                option = _observed_option(
                    current_root=current_root,
                    source_part=part,
                    source_root=source_root or current_root,
                    token=token,
                    meta=meta,
                )
                sig = option["line"].lower()
                existing = root_row["observed_parts"].get(sig)
                if existing:
                    existing["observed_count"] = int(existing.get("observed_count") or 0) + 1
                    if len(existing.get("examples") or []) < 6:
                        existing.setdefault("examples", []).append(meta)
                else:
                    root_row["observed_parts"][sig] = option
                if option.get("already_in_builder"):
                    summary["already_in_builder"] += 1
                else:
                    summary["extra_observed_options"] += 1

    final_roots: dict[str, Any] = {}
    for root_key, row in sorted(roots.items()):
        all_parts = list(row["observed_parts"].values())
        parts = sorted((p for p in all_parts if not p.get("already_in_builder")), key=lambda p: (str(p.get("table")), str(p.get("line"))))
        unmapped = [{"token": token, "count": count} for token, count in sorted(row["unmapped_tokens"].items())[:80]]
        final_roots[root_key] = {
            **{k: v for k, v in row.items() if k not in ("observed_parts", "unmapped_tokens")},
            "observed_parts": parts,
            "unmapped_tokens": unmapped,
            "observed_part_count": len(all_parts),
            "already_in_builder_part_count": sum(1 for p in all_parts if p.get("already_in_builder")),
            "extra_observed_part_count": len(parts),
        }

    summary["unique_observed_options"] = sum(int(r.get("observed_part_count") or 0) for r in final_roots.values())
    summary["unique_already_in_builder_options"] = sum(int(r.get("already_in_builder_part_count") or 0) for r in final_roots.values())
    summary["unique_extra_observed_options"] = sum(int(r.get("extra_observed_part_count") or 0) for r in final_roots.values())

    result = {
        "version": 1,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "description": "Generated observed-working selectable part options for unlocked/modded Legit Builder mode.",
        "sources": sources_seen,
        "summary": dict(summary),
        "unmapped_roots": [{"root_serial": serial, "count": count} for serial, count in unmapped_roots.most_common(30)],
        "unmapped_tokens_top": [{"token": token, "count": count} for token, count in unmapped_tokens.most_common(40)],
        "roots": final_roots,
    }
    return result, _build_report(result)


def _build_report(data: dict[str, Any]) -> str:
    summary = data.get("summary") or {}
    roots = data.get("roots") or {}
    top_roots = sorted(roots.values(), key=lambda r: int(r.get("extra_observed_part_count") or 0), reverse=True)[:20]
    lines = [
        "# Builder Observed Part Options Report",
        "",
        "This report summarizes generated selectable part options for unlocked/modded Legit Builder mode.",
        "",
        "Normal Legit Builder mode remains strict and does not use this observed option list.",
        "",
        "## Summary",
        "",
    ]
    for key in (
        "entries_scanned",
        "decoded",
        "decode_failed",
        "part_tokens",
        "already_in_builder",
        "extra_observed_options",
        "unique_observed_options",
        "unique_already_in_builder_options",
        "unique_extra_observed_options",
        "unmapped_root",
    ):
        lines.append(f"- {key}: {summary.get(key, 0)}")
    lines.extend(["", "## Top Roots With Extra Observed Options", ""])
    if top_roots:
        for row in top_roots:
            lines.append(
                f"- {row.get('root_key')} ({row.get('manufacturer')} {row.get('item_type')}): "
                f"{row.get('extra_observed_part_count', 0)} extra / {row.get('observed_part_count', 0)} observed"
            )
    else:
        lines.append("- none")
    lines.extend(["", "## Unmapped Roots", ""])
    unmapped_roots = data.get("unmapped_roots") or []
    if unmapped_roots:
        for row in unmapped_roots[:20]:
            lines.append(f"- root serial {row.get('root_serial')}: {row.get('count')}")
    else:
        lines.append("- none")
    lines.extend(["", "## Top Unmapped Part Tokens", ""])
    unmapped_tokens = data.get("unmapped_tokens_top") or []
    if unmapped_tokens:
        for row in unmapped_tokens[:20]:
            lines.append(f"- {row.get('token')}: {row.get('count')}")
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Runtime Use",
        "",
        "- Strict mode: uses only normal legit rule options.",
        "- Unlock/modded mode: merges extra observed options into existing slot cards.",
        "- No experimental checker UI, warning panel, or visible observed-working label is added.",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    data, report = generate()
    OUTPUT_PATH.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    REPORT_PATH.write_text(report, encoding="utf-8")
    summary = data.get("summary") or {}
    print(
        "observed options generated: "
        f"{summary.get('extra_observed_options', 0)} extra part observations, "
        f"{len(data.get('roots') or {})} roots"
    )
    print(f"resource: {OUTPUT_PATH}")
    print(f"report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
