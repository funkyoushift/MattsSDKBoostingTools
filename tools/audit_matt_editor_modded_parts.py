"""Audit modded BL4 catalog serials against Matt editor part availability.

This is intentionally read-only. It compares known modded item serials from the
local BL4 Codes resources to the part ids the bundled Matt editor can describe.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
APP_DIR = ROOT / "external_app" / "v22_parts_codes_fixed"
RESOURCES = APP_DIR / "resources"
MATT_EDITOR = APP_DIR / "matt_editor"
REPORT_PATH = ROOT / "MATT_EDITOR_MODDED_PART_GAP_REPORT.md"
SUPPLEMENT_PATH = (
    MATT_EDITOR
    / "js"
    / "item-editor"
    / "data"
    / "observed-modded-part-supplement.js"
)
GZO_FAMILY_SUPPLEMENT_PATH = (
    MATT_EDITOR
    / "js"
    / "item-editor"
    / "data"
    / "gzo-family-part-supplement.js"
)
GZO_FAMILY_DATA_URL = "https://save-editor.be/GZO/Borderlands4/family-data.js?v=master-parts"

sys.path.insert(0, str(APP_DIR))

from external_serial_tools import serial_to_human  # noqa: E402


TOKEN_RE = re.compile(r"\{([^{}]+)\}")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def entries_from_resource(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    if isinstance(data, dict):
        entries = data.get("entries") or data.get("items") or []
    elif isinstance(data, list):
        entries = data
    else:
        entries = []
    return [entry for entry in entries if isinstance(entry, dict)]


def is_modded(entry: dict[str, Any]) -> bool:
    tags = entry.get("tags") or []
    tags_text = " ".join(str(tag) for tag in tags).lower()
    fields_text = " ".join(
        str(entry.get(key) or "")
        for key in (
            "listing",
            "classification",
            "mattmab_result",
            "mattmab_validator",
            "source",
            "category",
            "notes",
        )
    ).lower()
    return "modded" in tags_text or "modded" in fields_text


def serial_or_human(entry: dict[str, Any]) -> tuple[str, str | None]:
    serial = str(entry.get("serial") or entry.get("base85") or "").strip()
    human = str(entry.get("deserialized") or entry.get("human") or "").strip()
    if human:
        return human, None
    if not serial:
        return "", "missing serial"
    try:
        return serial_to_human(serial), None
    except Exception as exc:  # pragma: no cover - audit wants exact error text
        return "", str(exc)


def parse_root_type_id(human: str) -> int | None:
    prefix = human.split("|", 1)[0]
    match = re.match(r"\s*(\d+)\s*,", prefix)
    if not match:
        return None
    return int(match.group(1))


def parse_part_refs(human: str) -> list[dict[str, Any]]:
    root_type_id = parse_root_type_id(human)
    refs: list[dict[str, Any]] = []
    for raw in TOKEN_RE.findall(human):
        token = raw.strip()
        if not token:
            continue
        if ":[" in token and token.endswith("]"):
            type_text, values_text = token.split(":[", 1)
            type_id = int(type_text.strip())
            values = [int(v) for v in re.findall(r"-?\d+", values_text)]
            refs.append({"kind": "array", "type_id": type_id, "values": values, "token": token})
        elif ":" in token:
            type_text, value_text = token.split(":", 1)
            refs.append(
                {
                    "kind": "typed",
                    "type_id": int(type_text.strip()),
                    "value": int(value_text.strip()),
                    "token": token,
                }
            )
        else:
            if root_type_id is None:
                refs.append({"kind": "simple", "type_id": None, "value": int(token), "token": token})
            else:
                refs.append({"kind": "simple", "type_id": root_type_id, "value": int(token), "token": token})
    return refs


def display_entry(entry: dict[str, Any]) -> str:
    name = str(entry.get("name") or "Unnamed")
    source = str(entry.get("source") or "")
    creator = str(entry.get("creator") or "")
    return " | ".join(part for part in (name, source, creator) if part)


def load_editor_known_parts() -> tuple[set[str], dict[str, str], dict[int, str]]:
    game_data = load_json(MATT_EDITOR / "game_data_export.json")
    id_index = game_data.get("id_index") or {}
    known: set[str] = set()
    paths: dict[str, str] = {}
    if isinstance(id_index, dict):
        for key, value in id_index.items():
            if re.fullmatch(r"\d+:\d+", str(key)):
                known.add(str(key))
                if isinstance(value, dict):
                    paths[str(key)] = str(value.get("path") or "")
                else:
                    paths[str(key)] = str(value or "")

    type_names: dict[int, str] = {}
    for top_key in ("characters", "weapons", "gadgets"):
        section = game_data.get(top_key) or {}
        if not isinstance(section, dict):
            continue
        walk_for_type_names(section, type_names)
    return known, paths, type_names


def load_editor_selectable_parts() -> set[str]:
    game_data = load_json(MATT_EDITOR / "game_data_export.json")
    parts_by_id = game_data.get("parts_by_id") or {}
    if not isinstance(parts_by_id, dict):
        return set()
    return {str(key) for key in parts_by_id if re.fullmatch(r"\d+:\d+", str(key))}


def walk_for_type_names(node: Any, type_names: dict[int, str], trail: tuple[str, ...] = ()) -> None:
    if isinstance(node, dict):
        type_id = node.get("type_id")
        name = node.get("name") or node.get("display_name") or (trail[-1] if trail else None)
        if isinstance(type_id, int) and name:
            type_names.setdefault(type_id, str(name))
        for key, value in node.items():
            walk_for_type_names(value, type_names, trail + (str(key),))
    elif isinstance(node, list):
        for value in node:
            walk_for_type_names(value, type_names, trail)


def load_gzo_part_metadata() -> dict[str, dict[str, str]]:
    labels: dict[str, dict[str, str]] = {}
    raw = load_json(RESOURCES / "gzo_parts_map.json")
    if not isinstance(raw, dict):
        return labels
    for type_label, parts in raw.items():
        match = re.match(r"\s*(\d+)\s*\|?\s*(.*)", str(type_label))
        if not match or not isinstance(parts, dict):
            continue
        type_id = int(match.group(1))
        type_name = match.group(2).strip()
        for value, name in parts.items():
            if str(value).isdigit():
                label = str(name)
                if type_name:
                    label = f"{label} ({type_name})"
                labels[f"{type_id}:{int(value)}"] = {
                    "name": label,
                    "type_label": type_name or f"Type {type_id}",
                }
    return labels


def load_gzo_part_labels() -> dict[str, str]:
    return {key: value["name"] for key, value in load_gzo_part_metadata().items()}


def key_for_ref(ref: dict[str, Any], value: int | None = None) -> str | None:
    type_id = ref.get("type_id")
    if type_id is None:
        return None
    part_value = value if value is not None else ref.get("value")
    if part_value is None:
        return None
    return f"{int(type_id)}:{int(part_value)}"


def source_label_for_type(type_label: str) -> str:
    lowered = type_label.lower()
    if "classmod" in lowered or "class mod" in lowered:
        return "Class Mod"
    if "shield" in lowered:
        return "Shield"
    if "grenade" in lowered:
        return "Grenade"
    if "ord" in lowered:
        return "Ordnance"
    if "rep" in lowered:
        return "Repkit"
    if "enhancement" in lowered:
        return "Enhancement"
    if "_" in type_label:
        prefix = type_label.split("_", 1)[0].upper()
        if prefix in {"DAD", "JAK", "MAL", "RIP", "TED", "TOR", "VLA"}:
            return "Weapon"
    return "Part"


def category_for_gzo_family_part(item_type: str, family_name: str, part_type: str) -> str:
    text = " ".join((item_type, family_name, part_type)).lower()
    if "classmod" in text or "class mod" in text:
        return "Class Mod"
    if "repkit" in text or "repair kit" in text:
        return "Repkit"
    if "shield" in text:
        return "Shield"
    if "enhancement" in text:
        return "Enhancement"
    if "grenade" in text:
        return "Grenade"
    if "ordnance" in text or "heavy weapon" in text or "gadget" in text:
        return "Ordnance"
    if item_type in {"Pistol", "Shotgun", "Assault Rifle", "SMG", "Sniper"}:
        return "Weapon"
    return "Part"


def load_gzo_family_data_js() -> str:
    local_candidates = [
        ROOT / "gzo_family-data.js",
        ROOT / "family-data.js",
        Path("C:/tmp/gzo_family-data.js"),
    ]
    for path in local_candidates:
        if path.exists():
            return path.read_text(encoding="utf-8")

    with urllib.request.urlopen(GZO_FAMILY_DATA_URL, timeout=30) as response:
        return response.read().decode("utf-8")


def parse_gzo_family_data() -> dict[str, dict[str, Any]]:
    text = load_gzo_family_data_js()
    marker = "window.__FAMILY_DATA__ = "
    if marker not in text:
        raise ValueError("GZO family-data.js does not contain window.__FAMILY_DATA__")
    start = text.index(marker) + len(marker)
    payload = text[start : text.rfind(";")].strip()
    data = json.loads(payload)
    families = data.get("families") or {}
    display_names = data.get("displayNames") or []

    parts: dict[str, dict[str, Any]] = {}
    for family_id_text, rows in families.items():
        if not str(family_id_text).isdigit() or not isinstance(rows, list):
            continue
        type_id = int(family_id_text)
        family_name = ""
        if 0 <= type_id - 1 < len(display_names):
            family_name = str(display_names[type_id - 1] or "")
        elif 0 <= type_id < len(display_names):
            family_name = str(display_names[type_id] or "")

        for row in rows:
            columns = [part.strip() for part in str(row).split("\t")]
            token_column = columns[0] if columns else str(row)
            for match in re.finditer(r"\{(?:" + str(type_id) + r":)?(-?\d+)\}", token_column):
                part_id = int(match.group(1))
                full_id = f"{type_id}:{part_id}"
                if full_id in parts:
                    continue
                name = columns[1] if len(columns) > 1 else full_id
                manufacturer = columns[2] if len(columns) > 2 else ""
                item_type = columns[3] if len(columns) > 3 else ""
                part_type = columns[4] if len(columns) > 4 else ""
                description = columns[5] if len(columns) > 5 else ""
                source_name = name or full_id
                parts[full_id] = {
                    "fullId": full_id,
                    "typeId": type_id,
                    "partId": part_id,
                    "name": source_name,
                    "sourceName": source_name,
                    "spawnCode": source_name,
                    "typeLabel": family_name or f"Type {type_id}",
                    "manufacturer": manufacturer or None,
                    "itemType": item_type or None,
                    "partType": part_type or None,
                    "category": category_for_gzo_family_part(item_type, family_name, part_type),
                    "description": description,
                    "source": "GZO Parts family-data.js",
                }
    return parts


def class_mod_slot_key_for_gzo_part(part: dict[str, Any]) -> str | None:
    if int(part.get("typeId") or 0) != 234:
        return None
    text = " ".join(
        str(part.get(key) or "")
        for key in ("sourceName", "spawnCode", "name", "partType", "description")
    ).lower()
    if "classmod.stat3_" in text or "stat3_" in text:
        return "stat_group3"
    if "classmod.stat2_" in text or "stat2_" in text:
        return "stat_group2"
    if "classmod.firmware" in text or "firmware" in text:
        return "firmware"
    if "statspecial_" in text or "classmod.statspecial" in text:
        return "statspecial"
    if "classmod.stat_" in text or "stat_" in text:
        return "stat_group1"
    return None


def search_aliases_for_gzo_part(part: dict[str, Any]) -> list[str]:
    aliases = {
        str(part.get("fullId") or ""),
        str(part.get("sourceName") or ""),
        str(part.get("spawnCode") or ""),
        str(part.get("name") or ""),
        str(part.get("description") or ""),
        str(part.get("partType") or ""),
    }
    slot_key = class_mod_slot_key_for_gzo_part(part)
    if slot_key:
        aliases.add(slot_key)
        aliases.add(slot_key.replace("_", " "))
    text = " ".join(aliases).lower()
    if "movement" in text or "movespeed" in text or "speed" in text:
        aliases.update(["move", "movement", "movement speed", "speed"])
    if "reload" in text:
        aliases.update(["reload", "reload speed"])
    return sorted(alias for alias in aliases if alias)


def write_gzo_family_supplement(known_parts: set[str]) -> int:
    gzo_family_parts = parse_gzo_family_data()
    for full_id, meta in load_gzo_part_metadata().items():
        if full_id in gzo_family_parts:
            existing = gzo_family_parts[full_id]
            mapped_name = meta.get("name")
            if mapped_name and (
                not existing.get("name")
                or re.fullmatch(r"stat_group\d+", str(existing.get("name") or ""))
            ):
                existing.setdefault("sourceName", existing.get("name") or full_id)
                existing.setdefault("spawnCode", existing.get("sourceName") or full_id)
                existing["name"] = mapped_name
                existing["description"] = (
                    str(existing.get("description") or "").strip()
                    or f"Mapped label: {mapped_name}"
                )
            continue
        type_id_text, part_id_text = full_id.split(":", 1)
        type_label = meta.get("type_label") or f"Type {type_id_text}"
        part_name = meta.get("name") or full_id
        gzo_family_parts[full_id] = {
            "fullId": full_id,
            "typeId": int(type_id_text),
            "partId": int(part_id_text),
            "name": part_name,
            "sourceName": part_name,
            "spawnCode": part_name,
            "typeLabel": type_label,
            "manufacturer": None,
            "itemType": None,
            "partType": "Class Mod Stat" if "classmod" in type_label.lower() else None,
            "category": source_label_for_type(type_label),
            "description": "",
            "source": "GZO Parts map",
        }
    for part in gzo_family_parts.values():
        slot_key = class_mod_slot_key_for_gzo_part(part)
        if slot_key:
            part["slotKey"] = slot_key
        aliases = search_aliases_for_gzo_part(part)
        if aliases:
            part["searchAliases"] = aliases
    entries = [
        part
        for full_id, part in sorted(
            gzo_family_parts.items(),
            key=lambda item: tuple(int(piece) for piece in item[0].split(":", 1)),
        )
        if full_id not in known_parts
    ]

    GZO_FAMILY_SUPPLEMENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(entries, ensure_ascii=False, indent=2)
    GZO_FAMILY_SUPPLEMENT_PATH.write_text(
        "// Generated by tools/audit_matt_editor_modded_parts.py.\n"
        "// Adds GZO Parts family-data ids missing from Matt editor game_data_export.json.\n"
        "// Source: https://save-editor.be/GZO/Borderlands4/Parts.html / family-data.js?v=master-parts\n"
        f"window.MSBT_GZO_FAMILY_PART_SUPPLEMENT = {payload};\n",
        encoding="utf-8",
    )
    return len(entries)


def write_supplement(
    missing_keys: Counter[str],
    gzo_metadata: dict[str, dict[str, str]],
    examples: dict[str, list[str]],
) -> int:
    entries: list[dict[str, Any]] = []
    for full_id, uses in missing_keys.most_common():
        meta = gzo_metadata.get(full_id)
        if not meta:
            continue
        type_id_text, part_id_text = full_id.split(":", 1)
        type_label = meta.get("type_label") or f"Type {type_id_text}"
        entries.append(
            {
                "fullId": full_id,
                "typeId": int(type_id_text),
                "partId": int(part_id_text),
                "name": meta.get("name") or full_id,
                "typeLabel": type_label,
                "category": source_label_for_type(type_label),
                "uses": int(uses),
                "examples": examples.get(full_id, [])[:3],
                "source": "GZO/custom modded catalog",
            }
        )

    SUPPLEMENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(entries, ensure_ascii=False, indent=2)
    SUPPLEMENT_PATH.write_text(
        "// Generated by tools/audit_matt_editor_modded_parts.py.\n"
        "// Adds labeled part ids observed in local modded BL4 Codes resources but missing from game_data_export.json.\n"
        f"window.MSBT_OBSERVED_MODDED_PART_SUPPLEMENT = {payload};\n",
        encoding="utf-8",
    )
    return len(entries)


def main() -> int:
    known_parts, editor_paths, type_names = load_editor_known_parts()
    selectable_parts = load_editor_selectable_parts()
    gzo_metadata = load_gzo_part_metadata()
    gzo_labels = {key: value["name"] for key, value in gzo_metadata.items()}

    catalog_files = [
        RESOURCES / "MattsSDKBoostingTools_gzo_codes.json",
        RESOURCES / "custom_bl4_codes.json",
    ]
    entries: list[dict[str, Any]] = []
    for path in catalog_files:
        for entry in entries_from_resource(path):
            if is_modded(entry):
                entry = dict(entry)
                entry["_catalog_file"] = path.name
                entries.append(entry)

    decoded_failures: list[tuple[str, str]] = []
    all_keys: Counter[str] = Counter()
    missing_keys: Counter[str] = Counter()
    array_keys: Counter[str] = Counter()
    per_item_repeats: Counter[str] = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    array_examples: dict[str, list[str]] = defaultdict(list)
    repeated_examples: dict[str, list[str]] = defaultdict(list)
    root_type_counts: Counter[int] = Counter()

    for entry in entries:
        human, error = serial_or_human(entry)
        if error:
            decoded_failures.append((display_entry(entry), error))
            continue
        root_type_id = parse_root_type_id(human)
        if root_type_id is not None:
            root_type_counts[root_type_id] += 1

        per_item_counter: Counter[str] = Counter()
        try:
            refs = parse_part_refs(human)
        except Exception as exc:
            decoded_failures.append((display_entry(entry), f"token parse failed: {exc}"))
            continue

        for ref in refs:
            if ref["kind"] == "array":
                for value in ref["values"]:
                    key = key_for_ref(ref, value)
                    if not key:
                        continue
                    all_keys[key] += 1
                    array_keys[key] += 1
                    per_item_counter[key] += 1
                    if key not in known_parts:
                        missing_keys[key] += 1
                    if len(array_examples[key]) < 3:
                        array_examples[key].append(display_entry(entry))
            else:
                key = key_for_ref(ref)
                if not key:
                    continue
                all_keys[key] += 1
                per_item_counter[key] += 1
                if key not in known_parts:
                    missing_keys[key] += 1
                    if len(examples[key]) < 3:
                        examples[key].append(display_entry(entry))

        for key, count in per_item_counter.items():
            if count > 1:
                per_item_repeats[key] = max(per_item_repeats[key], count)
                if len(repeated_examples[key]) < 3:
                    repeated_examples[key].append(f"{display_entry(entry)} ({count}x)")

    lines: list[str] = []
    lines.append("# Matt Editor Modded Part Gap Report")
    lines.append("")
    lines.append("Generated from local GZO/custom BL4 Codes resources against the bundled Matt editor `game_data_export.json`.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Modded catalog entries scanned: {len(entries)}")
    lines.append(f"- Decode/parse failures: {len(decoded_failures)}")
    lines.append(f"- Unique part ids used by modded entries: {len(all_keys)}")
    lines.append(f"- Editor-known unique part ids: {len(known_parts)}")
    lines.append(f"- Unique modded-used ids missing from editor data: {len(missing_keys)}")
    lines.append(
        f"- Labeled missing ids emitted to Matt editor supplement: "
        f"{len([key for key in missing_keys if key in gzo_labels])}"
    )
    lines.append(f"- Unique ids used inside array parts: {len(array_keys)}")
    lines.append(f"- Unique ids repeated more than once in a single item: {len(per_item_repeats)}")
    lines.append("")
    lines.append("## Most Common Missing Part IDs")
    lines.append("")
    lines.append("| Part ID | Uses | GZO label if known | Examples |")
    lines.append("| --- | ---: | --- | --- |")
    for key, count in missing_keys.most_common(40):
        label = gzo_labels.get(key, "")
        ex = "<br>".join(examples.get(key, [])[:3])
        lines.append(f"| `{key}` | {count} | {label or 'Not labeled in gzo_parts_map.json'} | {ex} |")
    if not missing_keys:
        lines.append("| None | 0 |  |  |")
    lines.append("")
    lines.append("## Most Repeated Part IDs In A Single Item")
    lines.append("")
    lines.append("| Part ID | Max repeat in one item | Editor known | GZO label if known | Examples |")
    lines.append("| --- | ---: | --- | --- | --- |")
    for key, count in per_item_repeats.most_common(40):
        label = gzo_labels.get(key, "")
        known = "yes" if key in known_parts else "no"
        ex = "<br>".join(repeated_examples.get(key, [])[:3])
        lines.append(f"| `{key}` | {count} | {known} | {label or 'Not labeled'} | {ex} |")
    if not per_item_repeats:
        lines.append("| None | 0 |  |  |  |")
    lines.append("")
    lines.append("## Most Common Array Part Usage")
    lines.append("")
    lines.append("| Part ID | Array uses | Editor known | GZO label if known | Examples |")
    lines.append("| --- | ---: | --- | --- | --- |")
    for key, count in array_keys.most_common(40):
        label = gzo_labels.get(key, "")
        known = "yes" if key in known_parts else "no"
        ex = "<br>".join(array_examples.get(key, [])[:3])
        lines.append(f"| `{key}` | {count} | {known} | {label or 'Not labeled'} | {ex} |")
    if not array_keys:
        lines.append("| None | 0 |  |  |  |")
    lines.append("")
    lines.append("## Root Type IDs Seen In Modded Catalog")
    lines.append("")
    lines.append("| Type ID | Items | Editor type label if known |")
    lines.append("| ---: | ---: | --- |")
    for type_id, count in root_type_counts.most_common():
        lines.append(f"| {type_id} | {count} | {type_names.get(type_id, '')} |")
    lines.append("")
    lines.append("## Decode Or Parse Failures")
    lines.append("")
    if decoded_failures:
        for name, error in decoded_failures[:50]:
            lines.append(f"- {name}: `{error}`")
        if len(decoded_failures) > 50:
            lines.append(f"- ... {len(decoded_failures) - 50} more")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- `Editor known` means the part id exists in `matt_editor/game_data_export.json` `id_index`.")
    lines.append("- Missing ids may still be valid in-game; this report only proves they are absent from the editor data source.")
    lines.append("- Repeated and array usage shows constructions the builder UI must support without collapsing or rejecting duplicates.")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    supplement_count = write_supplement(missing_keys, gzo_metadata, examples)
    gzo_family_supplement_count = write_gzo_family_supplement(selectable_parts)
    print(f"Wrote {REPORT_PATH}")
    print(f"Wrote {SUPPLEMENT_PATH}")
    print(f"Wrote {GZO_FAMILY_SUPPLEMENT_PATH}")
    print(f"modded_entries={len(entries)}")
    print(f"decode_failures={len(decoded_failures)}")
    print(f"unique_used={len(all_keys)}")
    print(f"unique_missing={len(missing_keys)}")
    print(f"supplement_labeled_missing={supplement_count}")
    print(f"gzo_family_missing_from_editor={gzo_family_supplement_count}")
    print(f"unique_arrays={len(array_keys)}")
    print(f"unique_repeated={len(per_item_repeats)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
