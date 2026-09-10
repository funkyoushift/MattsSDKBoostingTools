#!/usr/bin/env python3
"""Import decoded local BL4 NCS tables without fetching or publishing anything.

Input is the unmodified NcsParser's full JSON output (not --minimal). The
parser itself is a separate local tool; this importer only reads its output.
Existing catalog files are backed up before replacement. Public/data versions
are untouched. World/spawner catalogs and the manifest are handled separately.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "external_app/v22_parts_codes_fixed"
LEGIT = APP / "matt_editor/LegitItems"
RESOURCES = APP / "resources"
MOD = ROOT / "mod_extracted/MattsSDKBoostingTools"


def normalize(value: Any) -> Any:
    """Unwrap parser metadata while preserving editor dependency topology."""
    if isinstance(value, list):
        return [normalize(v) for v in value]
    if not isinstance(value, dict):
        return value
    if "__typeFlags" in value and "value" in value:
        return normalize(value["value"])
    return {
        key: normalize(item)
        for key, item in value.items()
        if not key.startswith("__") or key in {"__deps", "__dep_entries"}
    }


def entries(payload: dict, table: str):
    for record in payload.get(table, {}).get("records", []):
        yield from record.get("entries", [])


def rows(payload: dict, table: str):
    for wrapper in entries(payload, table):
        for key, value in wrapper.items():
            if not key.startswith("__") and isinstance(value, dict):
                yield key, value


def text_label(value: Any) -> str:
    text = str(value or "")
    return text.split(",", 2)[-1].strip() if re.match(r"^[^,]+,\s*[0-9A-Fa-f]{32},", text) else text


def tags(value: Any) -> list[str]:
    result = []
    for row in value or []:
        for tag in (row.values() if isinstance(row, dict) else [row]):
            if str(tag).lower() not in result:
                result.append(str(tag).lower())
    return result


def ref_key(value: Any) -> str:
    text = str(value or "")
    return (text.split("'", 2)[1] if "'" in text else text).lower()


def selection_rules(part: dict) -> list[dict] | None:
    source = part.get("parttypeselectionrules", {}).get("pairs")
    if not isinstance(source, dict):
        return None
    result = []
    for pair in source.values():
        if not isinstance(pair, dict) or not pair.get("key"):
            continue
        row = {"slot": str(pair["key"]).lower()}
        value = pair.get("value") or {}
        for key in ("min", "max"):
            count = (value.get("partcount") or {}).get(key)
            if count is not None:
                row[key] = int(float(count))
        if "parts" in value:
            row["parts"] = [str(p["part"]).lower() for p in value["parts"] if isinstance(p, dict) and p.get("part")]
        result.append(row)
    return result


def compact_part(key: str, part: dict, wrapper: dict, names: dict, previous: dict | None = None) -> dict:
    result = dict(previous or {})
    serial = int(part["serialindex"]["index"])
    table = wrapper["depTableName"]
    name_keys, name_labels, gestalt = [], [], []
    row_name = ""
    for aspect in part.get("aspects") or []:
        if not isinstance(aspect, dict):
            continue
        row_name = aspect.get("datatablerowname") or row_name
        for name_ref in aspect.get("titlepartlist") or []:
            name_key = ref_key(name_ref)
            name_keys.append(name_key)
            if name_key in names:
                name_labels.append(names[name_key])
        for field in ("gestaltpart", "gestaltpartname"):
            if aspect.get(field):
                gestalt.append(aspect[field])
    readable = text_label(part.get("debugdisplayname") or part.get("uiname") or "")
    if not readable:
        readable = " / ".join(dict.fromkeys(name_labels)) or result.get("display") or key.replace("_", " ").title()
    result.update({
        "key": key, "serial": serial, "table": table,
        "table_id": wrapper.get("depTableId"), "dep_index": wrapper.get("depIndex"),
        "add": tags(part.get("addtags")), "dep": tags(part.get("dependencytags")),
        "exclude": tags(part.get("excludetags")),
        "base": part.get("basecomposition") or part.get("basepart"),
        "base_tags": tags(part.get("basetags")), "rules": selection_rules(part),
        "display": readable, "debug": text_label(part.get("debugdisplayname") or ""),
        "internal": part.get(table) or key, "row": row_name, "gestalt": gestalt,
        "np_keys": name_keys, "np_names": name_labels,
        "rarity": next((r for r in ("pearlescent", "legendary", "epic", "rare", "uncommon", "common") if r in key or r in tags(part.get("basetags"))), ""),
    })
    tag_rules = part.get("parttagselectionrules")
    result.pop("tag_rules", None)
    if isinstance(tag_rules, list):
        result["tag_rules"] = []
        for raw in tag_rules:
            if not isinstance(raw, dict):
                continue
            rule = {"tags": tags(raw.get("tags") or raw.get("parttags"))}
            for bound in ("min", "max"):
                count = raw.get(bound, (raw.get("partcount") or {}).get(bound))
                if count is not None:
                    rule[bound] = int(float(count))
            result["tag_rules"].append(rule)
    return result


def build_inventory(payloads: dict[str, dict], previous: dict) -> tuple[dict, dict]:
    name_parts = {}
    for name, payload in payloads.items():
        if name.startswith("Nexus-Data-inv_name_part"):
            name_parts.update({key: text_label(value.get("partname")) for key, value in rows(payload, "inv_name_part")})
    raw_roots, raw_parts, root_deps = {}, {}, {}
    for suffix in ("0", "4", "6"):
        payload = payloads[f"Nexus-Data-inv{suffix}.json"]
        if not payload["inv"].get("__deps"):
            raise ValueError(f"inv{suffix} lacks __deps; decode full JSON before import")
        for wrapper in entries(payload, "inv"):
            keys = [key for key in wrapper if not key.startswith("__")]
            if len(keys) != 1:
                raise ValueError(f"Expected exactly one inventory root per wrapper: {keys}")
            key = keys[0]
            if isinstance(wrapper[key], dict):
                raw_roots.setdefault(key, {}).update(wrapper[key])
            root_deps.setdefault(key, [])
            for dep in payload["inv"]["__deps"]:
                if dep not in root_deps[key]:
                    root_deps[key].append(dep)
            for dep_wrapper in wrapper.get("__dep_entries") or []:
                for part_key, part in dep_wrapper.items():
                    if part_key in {"depTableName", "depTableId", "depIndex"} or part_key.startswith("__") or not isinstance(part, dict):
                        continue
                    if part.get("serialindex", {}).get("_scope") != "Sub":
                        continue
                    raw_parts.setdefault(key, {})[part_key] = (part, dep_wrapper)
    if not raw_parts.get("classmod_corpohacker"):
        raise ValueError("Fresh Loveless class-mod dependencies missing; do not import metadata-only JSON")
    old_by_key = {row["key"]: row for row in previous["roots"]}
    roots = []
    for key, raw in raw_roots.items():
        serial = raw.get("serialindex") or {}
        if serial.get("_scope") != "Root" or serial.get("status") != "Active":
            continue
        old_root = old_by_key.get(key, {})
        old_parts = {str(p["key"]): p for p in old_root.get("parts", [])}
        parts = []
        for part_key, (part, wrapper) in raw_parts.get(key, {}).items():
            if part["serialindex"].get("status") != "Active":
                continue
            parts.append(compact_part(part_key, part, wrapper, name_parts, old_parts.get(part_key)))
        by_part_key = {p["key"]: p for p in parts}
        for part in parts:
            if part["table"] != "inv_comp" or part["np_names"]:
                continue
            referenced_names = []
            for rule in part.get("rules") or []:
                for selected in rule.get("parts") or []:
                    referenced_names.extend(by_part_key.get(selected, {}).get("np_names") or [])
            if referenced_names:
                part["np_names"] = list(dict.fromkeys(referenced_names))
                if part["key"] not in old_parts:
                    part["display"] = " / ".join(part["np_names"])
        parts.sort(key=lambda p: (p["dep_index"] if p["dep_index"] is not None else 999, p["serial"], p["key"]))
        roots.append({
            "key": key, "name": raw.get("itembasename") or raw.get("inv") or key,
            "serial": int(serial["index"]), "inv": raw.get("inv") or key,
            "basetype": raw.get("basetype"), "manufacturer": raw.get("manufacturer"),
            "deps": root_deps[key], "parts": parts,
        })
    roots.sort(key=lambda r: (r["serial"], r["key"]))
    return {"version": "local_ncs_game_build_25234898", "roots": roots}, raw_roots


def update_parts_map(previous: dict, rules: dict) -> tuple[dict, int]:
    result = json.loads(json.dumps(previous))
    family_keys = {int(key.split("|", 1)[0].strip()): key for key in result if "|" in key}
    added = 0
    for root in rules["roots"]:
        family_key = family_keys.get(root["serial"], f"{root['serial']} | {root['inv']}")
        parts = result.setdefault(family_key, {})
        for part in root["parts"]:
            serial = str(part["serial"])
            if serial not in parts:
                parts[serial] = part["display"]
                added += 1
    return result, added


def build_editor_supplement(rules: dict) -> list[dict]:
    result = []
    for root in rules["roots"]:
        label = "Loveless Class Mod" if root["serial"] == 402 else text_label(root["name"])
        category = "Class Mod" if "classmod" in root["key"] else "Weapon" if root["serial"] in range(1, 28) else "Part"
        for part in root["parts"]:
            result.append({
                "fullId": f"{root['serial']}:{part['serial']}", "typeId": root["serial"], "partId": part["serial"],
                "name": part["display"], "typeLabel": label, "category": category,
                "partType": part["table"], "slotKey": part["table"],
                "spawnCode": f"{root['inv']}.{part['internal']}", "sourceName": part["internal"],
                "context": "Loveless" if root["serial"] == 402 else None,
                "source": "Local Borderlands 4 NCS data",
            })
    return result


def add_loveless_to_editor(previous: dict, rules: dict) -> dict:
    result = json.loads(json.dumps(previous))
    root = next(r for r in rules["roots"] if r["serial"] == 402)
    sections = {}
    for part in root["parts"]:
        section = {"class_mod_body": "Body", "inv_comp": "Rarity", "passive_points": "Passive Points", "action_skill_mod": "Action Skill Mod"}.get(part["table"], part["table"].replace("_", " ").title())
        bucket = sections.setdefault(section, {"type_id": 402, "parts": []})
        index = len(bucket["parts"])
        full_id = f"402:{part['serial']}"
        bucket["parts"].append({"id": full_id, "name": part["display"], "spawn_code": f"classmod_corpohacker.{part['internal']}", "type": section, "dlc": True, "dlc_name": "Harmonica"})
        result.setdefault("id_index", {})[full_id] = {"path": f"characters.Loveless.class_mods.{section}.parts[{index}]"}
    result.setdefault("characters", {})["Loveless"] = {"class_mods": sections}
    return result


def prune_superseded_overrides(override: dict, payloads: dict[str, dict]) -> tuple[dict, dict]:
    """Retain custom/hotfix parts unless this build supplies the same serial identity."""
    fresh = {}
    for suffix in ("0", "4", "6"):
        for wrapper in entries(payloads[f"Nexus-Data-inv{suffix}.json"], "inv"):
            root_key = next((key for key in wrapper if not key.startswith("__")), "")
            for dep in wrapper.get("__dep_entries") or []:
                for key, value in dep.items():
                    if isinstance(value, dict) and value.get("serialindex"):
                        fresh[(root_key, dep.get("depTableName"), key)] = value
    kept_wrappers, superseded, unmatched = [], [], []
    for wrapper in entries(override, "inv"):
        root_key = next((key for key in wrapper if not key.startswith("__")), "")
        kept = {key: value for key, value in wrapper.items() if key != "__dep_entries"}
        kept_deps = []
        for dep in wrapper.get("__dep_entries") or []:
            relevant = [(key, value) for key, value in dep.items() if isinstance(value, dict)]
            can_replace = bool(relevant)
            for key, value in relevant:
                current = fresh.get((root_key, dep.get("depTableName"), key))
                serial = value.get("serialindex") or {}
                if not current or not serial or current.get("serialindex") != serial:
                    can_replace = False
            names = [f"{root_key}.{key}" for key, _ in relevant]
            if can_replace:
                superseded.extend(names)
            else:
                kept_deps.append(dep)
                unmatched.extend(names)
        if kept_deps:
            kept["__dep_entries"] = kept_deps
        # Non-null root records can carry deliberate custom overrides.
        if kept_deps or isinstance(kept.get(root_key), dict):
            kept_wrappers.append(kept)
    result = {key: value for key, value in override.items() if key != "inv"}
    result["inv"] = {"__deps": override.get("inv", {}).get("__deps", []), "records": [{"entries": kept_wrappers}] if kept_wrappers else []}
    return result, {"superseded_same_serial_identity": superseded, "preserved_unmatched": unmatched}


def build_challenges(payloads: dict[str, dict], previous: dict, game_build: str) -> tuple[dict, dict]:
    definitions = {}
    for suffix in ("0", "4", "6"):
        for key, value in rows(payloads[f"Nexus-Data-challenge{suffix}.json"], "challenge"):
            definitions.setdefault(key, {}).update(value)

    def tier_goals(key: str, seen: set[str]) -> list[int]:
        if key in seen or key not in definitions:
            return []
        seen = seen | {key}
        value = definitions[key]
        if "challengetiers" not in value:
            return tier_goals(ref_key(value.get("parent")), seen)
        goals = []
        for tier in value.get("challengetiers") or []:
            if isinstance(tier, dict):
                try:
                    goal = int(float(tier.get("goalvalue", 0)))
                    if goal > 0:
                        goals.append(goal)
                except (ValueError, TypeError, OverflowError):
                    pass
        return goals

    merged = {entry["id"].lower(): dict(entry) for entry in previous["entries"]}
    added = []
    for key, value in definitions.items():
        identity = str(value.get("challenge") or "").strip()
        if not identity:
            continue  # Alias/ref-only records are not new challenge definitions.
        if identity.lower() not in merged:
            added.append(identity)
        merged[identity.lower()] = {"id": identity, "amount": max(tier_goals(key, set()) or [1])}
    result = {
        "source": "Locally extracted game challenge identifiers and highest inherited tier goal; existing catalog-only identifiers retained.",
        "game_data": {"game_build": game_build}, "count": len(merged),
        "entries": sorted(merged.values(), key=lambda entry: entry["id"].lower()),
    }
    return result, {"before": len(previous["entries"]), "after": len(merged), "added": added, "case_duplicates_removed": len(previous["entries"]) - len({e["id"].lower() for e in previous["entries"]}), "vc5_count": sum(entry["id"].lower().startswith("vc5_") for entry in merged.values())}


def build_shinies(payloads: dict[str, dict], rules: dict, previous: list, canonical_codes: dict, game_build: str) -> tuple[list, dict]:
    """Pair extracted shiny customization names with existing canonical gear codes."""
    sys.path.insert(0, str(APP))
    from external_serial_tools import human_to_serial, rewrite_item_level, serial_to_human

    definitions = {}
    for suffix in ("0", "4"):
        for key, value in rows(payloads[f"Nexus-Data-inv_custom{suffix}.json"], "inv_custom"):
            if key.startswith("cosmetics_weapon_shiny_"):
                definitions.setdefault(key, {}).update(value)
    roots = {r["key"]: r for r in rules["roots"]}
    canonical_by_comp = {}
    for entry in canonical_codes["entries"]:
        if entry.get("category") != "Weapons":
            continue
        human = serial_to_human(entry["serial"])
        root_id = int(human.split(",", 1)[0])
        first_part = re.search(r"\{(\d+)\}", human)
        if first_part:
            canonical_by_comp.setdefault((root_id, int(first_part.group(1))), (entry, human))
    result, covered, releveled = [], set(), 0
    for entry in previous:
        updated = dict(entry)
        old_human = serial_to_human(entry["serial"])
        custom = re.search(r'"c",\s*"([^"]+)"', old_human)
        if custom:
            covered.add(custom.group(1).lower())
        updated["serial"] = rewrite_item_level(entry["serial"], 70)
        new_human = serial_to_human(updated["serial"])
        assert new_human.split("|", 1)[1] == old_human.split("|", 1)[1], "Level rewrite changed item parts/customization"
        assert new_human.split("|", 1)[0].strip().endswith(", 70")
        releveled += updated["serial"] != entry["serial"]
        updated["game_build"] = game_build
        result.append(updated)
    added, missing = [], []
    for key, value in definitions.items():
        if key in covered:
            continue
        reference = ref_key((value.get("filterdata") or {}).get("item"))
        if "." not in reference:
            missing.append(key)
            continue
        root_key, part_key = reference.split(".", 1)
        root = roots.get(root_key)
        part = next((p for p in (root or {}).get("parts", []) if p["key"] == part_key), None)
        source = canonical_by_comp.get((root["serial"], part["serial"])) if root and part else None
        if not source:
            missing.append(key)
            continue
        canonical, human = source
        human = "|".join(human.split("|")[:4]) + '| "c", ' + json.dumps(value["inv_custom"]) + '|'
        serial = rewrite_item_level(human_to_serial(human), 70)
        decoded = serial_to_human(serial)
        assert value["inv_custom"] in decoded and decoded.split("|", 1)[0].strip().endswith(", 70")
        assert decoded.split("|")[3].strip() == human.split("|")[3].strip(), "Shiny attachment changed item parts"
        assert human_to_serial(decoded) == serial, "Generated shiny did not round-trip"
        result.append({
            "id": "local_shiny_" + key.removeprefix("cosmetics_weapon_shiny_"),
            "display_name": canonical["name"], "serial": serial, "game_build": game_build,
            "source": "Existing Lootlemon gear serial plus extracted shiny customization definition",
            "source_url": canonical.get("url", ""), "customization": value["inv_custom"],
            "validation": "Serializer round-trip verified; not live-spawn tested",
        })
        covered.add(key)
        added.append(canonical["name"])
    return result, {"before": len(previous), "after": len(result), "added": added, "releveled": releveled, "missing_canonical_base_serial": missing, "definition_count": len(definitions)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Directory containing full Nexus-Data-*.json")
    parser.add_argument("--game-build", required=True)
    parser.add_argument("--write", action="store_true", help="Write files; otherwise validate and report only")
    args = parser.parse_args()
    source = args.source.resolve()
    targets = {p.name for p in LEGIT.glob("Nexus-Data-*.json")}
    # This is a documented editor load key but the old remote proxy returned 404.
    targets.add("Nexus-Data-skilltrees_data0.json")
    payloads, imported, missing = {}, [], []
    for name in sorted(targets):
        path = source / name
        if not path.exists():
            missing.append(name)
            continue
        raw = path.read_bytes()
        payload = normalize(json.loads(raw))
        if not any(isinstance(v, dict) and "records" in v for v in payload.values()):
            raise ValueError(f"No table records in {name}")
        payloads[name] = payload
        imported.append({"file": name, "source_sha256": hashlib.sha256(raw).hexdigest(), "rows": sum(1 for table in payload for _ in rows(payload, table))})
    previous_rules = json.loads((RESOURCES / "legit_rules_flat.json").read_text(encoding="utf-8"))
    challenges, challenge_report = build_challenges(payloads, json.loads((MOD / "challenge_catalog.json").read_text(encoding="utf-8")), args.game_build)
    rules, raw_roots = build_inventory(payloads, previous_rules)
    rules["version"] = f"local_ncs_game_build_{args.game_build}"
    shinies, shiny_report = build_shinies(payloads, rules, json.loads((MOD / "shiny_serials.json").read_text(encoding="utf-8")), json.loads((RESOURCES / "MattsSDKBoostingTools_lootlemon_codes.json").read_text(encoding="utf-8")), args.game_build)
    previous_parts = json.loads((RESOURCES / "gzo_parts_map.json").read_text(encoding="utf-8"))
    part_map, added_parts = update_parts_map(previous_parts, rules)
    old_root_keys = {r["key"] for r in previous_rules["roots"]}
    old_comps = {(r["key"], p["key"]) for r in previous_rules["roots"] for p in r["parts"] if p["table"] == "inv_comp"}
    new_roots = [r for r in rules["roots"] if r["key"] not in old_root_keys]
    report = {
        "game_build": args.game_build, "checked_at": datetime.now(timezone.utc).isoformat(),
        "source": "Locally installed Borderlands 4 NCS data, decoded using a separate unmodified NcsParser utility",
        "input_directory": "NcsParser/output/json", "imported": imported, "missing_source_files": missing,
        "roots_before": len(previous_rules["roots"]), "roots_after": len(rules["roots"]),
        "parts_before": sum(len(r["parts"]) for r in previous_rules["roots"]),
        "parts_after": sum(len(r["parts"]) for r in rules["roots"]),
        "new_root_keys": [r["key"] for r in new_roots], "parts_map_added": added_parts,
        "loveless_class_mod": next({"root_id": r["serial"], "parts": len(r["parts"])} for r in rules["roots"] if r["key"] == "classmod_corpohacker"),
        "new_compositions": [{"root": r["key"], "root_id": r["serial"], "part": p["key"], "part_id": p["serial"], "name": p["display"]} for r in rules["roots"] for p in r["parts"] if p["table"] == "inv_comp" and (r["key"], p["key"]) not in old_comps],
        "challenges": challenge_report,
        "shinies": shiny_report,
    }
    print(json.dumps({k: v for k, v in report.items() if k not in {"imported", "new_compositions", "challenges"}}, ensure_ascii=True, indent=2))
    print(f"New item compositions: {len(report['new_compositions'])}")
    if not args.write:
        return 0
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = ROOT / "_tmp_catalog_compare" / f"local_ncs_import_{stamp}"

    def write(path: Path, payload: dict) -> None:
        if path.exists():
            target = backup / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        temp.replace(path)

    for name, payload in payloads.items():
        write(LEGIT / name, payload)
    for record in report["imported"]:
        record["imported_sha256"] = hashlib.sha256((LEGIT / record["file"]).read_bytes()).hexdigest()
    if "Nexus-Data-inv.json" in missing:
        override_path = LEGIT / "Nexus-Data-inv.json"
        override, override_report = prune_superseded_overrides(json.loads(override_path.read_text(encoding="utf-8")), payloads)
        write(override_path, override)
        report["hotfix_override_comparison"] = override_report
    for path in (RESOURCES / "legit_rules_flat.json", MOD / "legit_rules_flat.json"):
        write(path, rules)
    for path in (RESOURCES / "gzo_parts_map.json", MOD / "gzo_parts_map.json", ROOT / "docs/data/gzo_parts_map.json"):
        write(path, part_map)
    for path in (MOD / "challenge_catalog.json", ROOT / "docs/data/challenge_catalog.json"):
        write(path, challenges)
    for path in (MOD / "shiny_serials.json", ROOT / "docs/data/shiny_serials.json"):
        write(path, shinies)
    report["derived_catalogs"] = {
        "gzo_parts_map.json": {
            "game_build": args.game_build,
            "sha256": hashlib.sha256((RESOURCES / "gzo_parts_map.json").read_bytes()).hexdigest(),
        }
    }
    editor_path = APP / "matt_editor/game_data_export.json"
    write(editor_path, add_loveless_to_editor(json.loads(editor_path.read_text(encoding="utf-8")), rules))
    supplement_path = APP / "matt_editor/js/item-editor/data/local-game-part-supplement.js"
    supplement_path.write_text(
        "// Generated by tools/import_local_ncs_catalogs.py from locally installed game data.\n"
        + f"// Game build: {args.game_build}. Part IDs are extracted; spawning is not live-tested.\n"
        + "window.MSBT_LOCAL_GAME_PART_SUPPLEMENT = "
        + json.dumps(build_editor_supplement(rules), ensure_ascii=False, indent=2) + ";\n", encoding="utf-8", newline="\n"
    )
    write(LEGIT / "local_game_data_provenance.json", report)
    print(f"Imported {len(imported)} tables; backup: {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
