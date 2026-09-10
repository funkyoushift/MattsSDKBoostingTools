"""Merge installed-game NCS exports into world catalogs, preserving curated entries.

Input: full JSON exports from Borderlands-4.NcsParser (not *_minimal.json).
No game process, saves, versions, or published assets are modified.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "external_app/v22_parts_codes_fixed/resources"
MOD = ROOT / "mod_extracted/MattsSDKBoostingTools"
DOCS = ROOT / "docs/data"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def unwrap(value):
    if isinstance(value, dict):
        if "__typeFlags" in value and "value" in value:
            return unwrap(value["value"])
        return {k: unwrap(v) for k, v in value.items()}
    if isinstance(value, list):
        return [unwrap(v) for v in value]
    return value


def merge_fields(target: dict, incoming: dict) -> None:
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            merge_fields(target[key], value)
        else:
            target[key] = copy.deepcopy(value)


def token(value: object) -> str:
    text = str(value or "")
    match = re.fullmatch(r"[^']+'([^']+)'", text)
    return match.group(1) if match else text


def localized(value: object) -> str:
    text = str(value or "")
    parts = text.split(",", 2)
    if len(parts) == 3 and re.fullmatch(r"\s*[0-9A-Fa-f]{32}\s*", parts[1]):
        return parts[2].strip()
    return text


def table_files(folder: Path, table: str) -> list[Path]:
    pattern = re.compile(rf"Nexus-Data-{re.escape(table)}(\d+)\.json", re.I)
    shards = [(int(match.group(1)), p) for p in folder.glob("Nexus-Data-*.json")
              if (match := pattern.fullmatch(p.name))]
    return [p for _, p in sorted(shards, key=lambda item: (item[0], item[1].name.casefold()))]


def load_table(folder: Path, table: str) -> tuple[dict, dict, list]:
    """Read root definitions and dependency-only records (whose root is null)."""
    definitions, sources, records, aliases = {}, {}, [], {}
    paths = table_files(folder, table)
    if not paths:
        raise ValueError(f"Missing full {table} NCS exports in {folder}")
    for path in paths:
        document = unwrap(read_json(path))
        data = next((v for k, v in document.items() if k.casefold() == table.casefold()), {})
        for record in data.get("records", []):
            for entry in record.get("entries", []):
                for key, row in entry.items():
                    if key.startswith("__"):
                        continue
                    records.append((key.casefold(), entry.get("__dep_entries", []), path.name))
                    if not isinstance(row, dict):
                        continue
                    name = row.get(table.casefold()) or row.get(table) or key
                    canonical = str(name).casefold()
                    aliases[key.casefold()] = canonical
                    merge_fields(definitions.setdefault(canonical, {}), row)
                    sources[canonical] = path.name
    return definitions, sources, [(aliases.get(key, key), deps, source) for key, deps, source in records]


def inherited(rows: dict, key: str, field: str):
    seen = set()
    while key and key not in seen:
        seen.add(key)
        row = rows.get(key, {})
        if field in row:
            return row[field]
        key = token(row.get("parent")).casefold()
    return None


def actor_category(type_name: str, name: str) -> str:
    rules = [("SpawnGroup", "Spawn Groups"), ("CharacterStandIn", "Deco & Cinematic"),
             ("DecoCharacter", "Deco & Cinematic"), ("CharacterDef", "Characters"),
             ("Pickup", "Pickups"), ("Grenade", "Grenades"), ("Projectile", "Projectiles"),
             ("Lootable", "Lootables"), ("Damageable", "Damageables"),
             ("Carryable", "Carryables"), ("Door", "Doors & Switches"),
             ("Switch", "Doors & Switches"), ("Station", "Travel & Stations"),
             ("Vehicle", "Vehicles & Mounts"), ("Drone", "Drones & Turrets"),
             ("Turret", "Drones & Turrets"), ("Grapple", "Climbables & Grapple"),
             ("Zipline", "Climbables & Grapple"), ("Mission", "Mission & Quest"),
             ("DangerZone", "Danger Zones"), ("Placeable", "Placeables & World Props"),
             ("Interactive", "Interactive Objects")]
    for fragment, category in rules:
        if fragment.lower() in type_name.lower():
            return category
    return "Other / Uncategorized"


def merge_actors(current: dict, actors: dict, sources: dict, displays: dict, provenance: dict):
    out = copy.deepcopy(current)
    categories = out.setdefault("categories", {})
    old_names = set(categories.get("All", []))
    names = set(old_names)
    metadata = out.setdefault("actor_metadata", {})
    display_names = out.setdefault("display_names", {})
    for key, actor in actors.items():
        name = actor.get("gbxactor")
        if not name:
            continue
        names.add(name)
        type_name = str(inherited(actors, key, "type") or "")
        if name not in old_names:
            categories.setdefault(actor_category(type_name, name), []).append(name)
        display_key = token(inherited(actors, key, "uxdisplayname"))
        label = localized(inherited(displays, display_key.casefold(), "text"))
        if label:
            display_names[name] = label
        meta = metadata.setdefault(name, {})
        meta.update({"game_data_source_file": sources[key], "game_build": provenance["game_build"],
                     "definition_type": token(type_name)})
        if actor.get("parent"):
            meta["parent_actor"] = token(actor["parent"])
        if label:
            meta.update({"reference_display_name": label, "display_key": display_key})
        for field, dest in [("bisboss", "is_boss"), ("bistrueboss", "is_true_boss")]:
            value = inherited(actors, key, field)
            if value is not None:
                meta[dest] = str(value).lower() == "true"
        dlc = token(inherited(actors, key, "dlc"))
        if dlc:
            meta["dlc_definition"] = dlc
        for dlc_name in ("Harmonica", "Viola"):
            if dlc.lower() == f"dlcdef_{dlc_name.lower()}":
                categories.setdefault(f"{dlc_name} DLC", []).append(name)
    categories["All"] = sorted(names, key=str.casefold)
    for key, values in categories.items():
        categories[key] = sorted(set(values), key=str.casefold)
    out["actor_count"] = len(names)
    out["game_data"] = provenance
    return out, sorted(names - old_names)


def pool_category(name: str) -> str:
    low = name.lower()
    for part, category in [("classmod", "Class Mod"), ("cosmetic", "Cosmetic"),
                           ("ammo", "Ammo"), ("currency", "Currency"),
                           ("eridium", "Currency"), ("shield", "Shield"),
                           ("repkit", "Repkit"), ("ordnance", "Ordnance")]:
        if part in low:
            return category
    for part, category in [("ar", "Assault Rifle"), ("ps", "Pistol"), ("sg", "Shotgun"),
                           ("sr", "Sniper"), ("sm", "SMG"), ("hw", "Heavy")]:
        if f"_{part}_" in low:
            return category
    return "Other"


def merge_pools(current: list, pools: dict, sources: dict, provenance: dict):
    out = copy.deepcopy(current)
    present = {str(row.get("itempool", "")).casefold() for row in out}
    added = []
    for key, pool in pools.items():
        name = pool.get("itempool")
        if not name or key in present:
            continue
        label = re.sub(r"^itempool_?", "", name, flags=re.I).replace("_", " ")
        out.append({"display_name": label, "itempool": name, "category": pool_category(name),
                    "source_file": sources[key], "game_build": provenance["game_build"]})
        present.add(key)
        added.append(name)
    return sorted(out, key=lambda row: (row.get("category", ""), row.get("display_name", "").casefold())), added


def merge_travel(current_maps: dict, current_stations: dict, maps: dict, sources: dict,
                 records: list, provenance: dict):
    maps_out, stations_out = copy.deepcopy(current_maps), copy.deepcopy(current_stations)
    existing_maps = {x["map"].casefold(): x for x in maps_out["maps"]}
    old_maps = set(existing_maps)
    for key, row in maps.items():
        name = row.get("map", key)
        info = row.get("auto_save_infos") or {}
        default = token(info.get("defaultstation"))
        if key not in existing_maps:
            if (not name.endswith("_P") or name == "FrontEnd_P" or
                    str(info.get("canbecooked")).lower() != "true" or "." not in default):
                continue
            existing_maps[key] = {"map": name, "display_name": name, "category": "DLC" if "/DLC/" in str(row.get("mappath") or "") else "Playable", "synthetic": False}
        target = existing_maps[key]
        target.update({"map_key": key, "source_file": sources[key]})
        if "mappath" in row:
            target["mappath"] = row["mappath"]
        if "defaultstation" in info:
            target["defaultstation"] = default
        if "canbecooked" in info:
            target["canbecooked"] = str(info["canbecooked"]).lower() == "true"
        if name == "Harmonica_P":
            target["display_name"] = "Harmonica_P - Providence"
    maps_out["maps"] = list(existing_maps.values())
    maps_out.update(count=len(existing_maps), game_data=provenance)
    stations = {row["station"].casefold(): row for row in stations_out["stations"]}
    old_stations = set(stations)
    # Patch shards may contribute only some fields for a station. Merge their
    # definitions before applying them; absence is not a request to erase a field.
    station_definitions = {}
    for key, deps, source in records:
        if key not in existing_maps:
            continue
        world = existing_maps[key]["map"]
        for dep in deps:
            if str(dep.get("depTableName", "")).lower() != "station":
                continue
            for depkey, row in dep.items():
                if not isinstance(row, dict) or not row.get("station"):
                    continue
                name = row["station"]
                identity = f"{world}.{name}"
                combined = station_definitions.setdefault(identity.casefold(), {"row": {}})
                merge_fields(combined["row"], row)
                combined.update(key=key, world=world, identity=identity, depkey=depkey, source=source)
    for identity_key, combined in station_definitions.items():
        row = combined["row"]
        key, world = combined["key"], combined["world"]
        name = row["station"]
        loc, rot = row.get("loc") or {}, row.get("rot") or {}
        target = stations.setdefault(identity_key, {})
        game_data = row.get("gamespecificdata") or {}
        target.update({"station": combined["identity"], "world": world,
                       "display_name": localized(row.get("displayname")) or target.get("display_name") or name,
                       "station_key": combined["depkey"], "station_name": name,
                       "source_file": combined["source"]})
        if "displayname" in row:
            target["display_name_raw"] = row["displayname"]
        if "typedef" in row:
            target["typedef"] = token(row["typedef"])
        target["category"] = ("Raid" if world.startswith("Raid") else "DLC" if "/DLC/" in str(existing_maps[key].get("mappath") or "") else target.get("category", "Standard"))
        for field in ("dest", "dest_options", "zonehandle", "previousstation"):
            if field in row:
                target[field] = token(row[field])
        if "mainmenustation" in game_data:
            target["mainmenustation"] = token(game_data["mainmenustation"])
        if "missiondependency" in row:
            target["dependency"] = json.dumps(row["missiondependency"], separators=(",", ":")) if row["missiondependency"] else ""
        for field in ("x", "y", "z"):
            if field in loc:
                target[field] = str(loc[field])
        for field in ("pitch", "yaw", "roll"):
            if field in rot:
                target[field] = str(rot[field])
    stations_out["stations"] = sorted(stations.values(), key=lambda x: x["station"].casefold())
    stations_out.update(count=len(stations), categories=dict(Counter(x["category"] for x in stations.values())), game_data=provenance)
    return maps_out, stations_out, sorted(set(existing_maps) - old_maps), sorted(set(stations) - old_stations)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export_dir", type=Path)
    parser.add_argument("--game-build", required=True)
    parser.add_argument("--write", action="store_true", help="Write catalogs; default is a read-only report")
    args = parser.parse_args()
    provenance = {"game_version": "1.10", "game_build": args.game_build, "source": "Local installed-game NCS extraction", "live_spawn_tested": False}
    actors, actor_sources, _ = load_table(args.export_dir, "gbxactor")
    displays, _, _ = load_table(args.export_dir, "display_data")
    pools, pool_sources, _ = load_table(args.export_dir, "itempool")
    maps, map_sources, records = load_table(args.export_dir, "map")
    actor_out, new_actors = merge_actors(read_json(ROOT / "electron_poc/dev_spawner_catalog.json"), actors, actor_sources, displays, provenance)
    pool_out, new_pools = merge_pools(read_json(RES / "item_pools.json"), pools, pool_sources, provenance)
    map_out, station_out, new_maps, new_stations = merge_travel(read_json(RES / "travelmaps_flat.json"), read_json(RES / "travelstations.json"), maps, map_sources, records, provenance)
    report = {**provenance, "actors_added": len(new_actors), "actor_count": actor_out["actor_count"], "pools_added": len(new_pools), "pool_count": len(pool_out), "maps_added": new_maps, "map_count": map_out["count"], "stations_added": len(new_stations), "station_count": station_out["count"]}
    if args.write:
        backup = ROOT / "_tmp_catalog_compare" / f"world-before-{args.game_build}"
        outputs = [(ROOT / "electron_poc/dev_spawner_catalog.json", actor_out)]
        outputs += [(RES / name, data) for name, data in [("item_pools.json", pool_out), ("travelmaps_flat.json", map_out), ("travelstations.json", station_out)]]
        for path, data in outputs:
            targets = [path, DOCS / path.name]
            if (MOD / path.name).is_file():
                targets.append(MOD / path.name)
            for target in targets:
                saved = backup / target.relative_to(ROOT)
                if target.exists() and not saved.exists():
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, saved)
                temporary = target.with_suffix(target.suffix + ".tmp")
                temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                temporary.replace(target)
        report["source_sha256"] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for table in ("gbxactor", "display_data", "itempool", "map") for p in table_files(args.export_dir, table)}
        report_path = ROOT / "_tmp_catalog_compare" / f"world-refresh-{args.game_build}.json"
        report_path.write_text(json.dumps({**report, "new_actors": new_actors, "new_pools": new_pools, "new_stations": new_stations}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
