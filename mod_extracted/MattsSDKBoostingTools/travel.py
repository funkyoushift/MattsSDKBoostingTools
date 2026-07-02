
"""Map and travel-station helpers for Matt's SDK Boosting Tools.

This intentionally keeps only the travel pieces needed by the BLImGui menu.
"""
from __future__ import annotations

import json
import pkgutil
from typing import Any

from mods_base import ENGINE, get_pc
from unrealsdk import find_class, logging

_PREFIX = "[Matts SDK Boosting Tools | Travel]"
_DEFAULT_MAP_ROWS: list[dict[str, str]] = [
    {"map": "World_P", "display_name": "World_P - Main World"},
    {"map": "Fortress_Grasslands_P", "display_name": "Fortress_Grasslands_P - Fadefields Fortress"},
    {"map": "Vault_Grasslands_P", "display_name": "Vault_Grasslands_P - Fadefields Vault"},
    {"map": "Fortress_Shatteredlands_P", "display_name": "Fortress_Shatteredlands_P - Carcadia Fortress"},
    {"map": "Vault_ShatteredLands_P", "display_name": "Vault_ShatteredLands_P - Carcadia Vault"},
    {"map": "Fortress_Mountains_P", "display_name": "Fortress_Mountains_P - Terminus Range Fortress"},
    {"map": "Vault_Mountains_P", "display_name": "Vault_Mountains_P - Terminus Range Vault"},
    {"map": "UpperCity_P", "display_name": "UpperCity_P - Upper Dominion"},
    {"map": "Raid1_P", "display_name": "Raid1_P - Bloomreaper Raid"},
    {"map": "Raid2_P", "display_name": "Raid2_P - Raid 2"},
    {"map": "Cello_P", "display_name": "Cello_P - Bounty Pack 2"},
    {"map": "Banjo_P", "display_name": "Banjo_P - Bounty Pack 1"},
    {"map": "Cowbell_P", "display_name": "Cowbell_P - Mad Ellie"},
    {"map": "VaultoftheDamned_P", "display_name": "VaultoftheDamned_P - Mad Ellie Vault"},
    {"map": "Elpis_P", "display_name": "Elpis_P - Elpis"},
    {"map": "ElpisElevator_P", "display_name": "ElpisElevator_P - Elpis Elevator"},
    {"map": "Bespoke_VisionQuest", "display_name": "Bespoke_VisionQuest - Vision Quest"},
]

_STATION_CACHE: list[dict[str, str]] | None = None
_MAP_CACHE: list[dict[str, str]] | None = None


def _norm_map_name(value: str) -> str:
    return str(value or '').strip().lower()


def canonical_travel_map_name(map_name: str) -> str:
    """Return the deduped/canonical map name for case-variant map ids."""
    needle = _norm_map_name(map_name)
    if not needle:
        return str(map_name or '').strip()
    for row in load_travel_maps():
        if _norm_map_name(str(row.get('map', ''))) == needle:
            return str(row.get('map', map_name))
    return str(map_name or '').strip()


def _display_with_canonical_map_name(display: str, canonical: str, original: str) -> str:
    display = str(display or canonical).strip()
    original = str(original or '').strip()
    canonical = str(canonical or original).strip()
    if original and canonical and display.startswith(original):
        return canonical + display[len(original):]
    return display


def _log(message: str) -> None:
    logging.info(f"{_PREFIX} {message}")


def _world_context(pc: Any) -> Any:
    try:
        gv = getattr(ENGINE, "GameViewport", None)
        world = getattr(gv, "World", None) if gv is not None else None
        if world is not None:
            return world
    except Exception:
        pass
    try:
        return getattr(pc, "World", None)
    except Exception:
        return None


def _try_call(label: str, fn: Any, cmd: str, pc: Any) -> bool:
    if not callable(fn):
        return False
    for args in ((cmd,), (cmd, True), (cmd, False), (cmd, pc)):
        try:
            fn(*args)
            _log(f"{label} ok: {cmd}")
            return True
        except TypeError:
            continue
        except Exception as exc:
            _log(f"{label} failed ({cmd}): {exc!r}")
            return False
    return False


def _try_kismet_execute(cmd: str, world: Any, pc: Any) -> bool:
    for path in ("KismetSystemLibrary", "Engine.KismetSystemLibrary"):
        try:
            cls = find_class(path)
        except Exception:
            cls = None
        if cls is None:
            continue
        cdo = getattr(cls, "ClassDefaultObject", None)
        fn = getattr(cdo, "ExecuteConsoleCommand", None) if cdo is not None else None
        if not callable(fn):
            continue
        contexts: list[Any] = []
        if world is not None:
            contexts.append(world)
        if pc is not None:
            contexts.append(pc)
        try:
            gv = getattr(ENGINE, "GameViewport", None)
            if gv is not None:
                contexts.append(gv)
        except Exception:
            pass
        seen: set[int] = set()
        for ctx in contexts:
            if ctx is None or id(ctx) in seen:
                continue
            seen.add(id(ctx))
            for args in ((ctx, cmd, pc), (ctx, cmd)):
                try:
                    fn(*args)
                    _log(f"KismetSystemLibrary.ExecuteConsoleCommand ok: {cmd}")
                    return True
                except TypeError:
                    continue
                except Exception as exc:
                    _log(f"Kismet ExecuteConsoleCommand failed ({cmd}): {exc!r}")
                    return False
    return False


def _try_viewport_console(cmd: str, pc: Any) -> bool:
    try:
        gv = getattr(ENGINE, "GameViewport", None)
        vc = getattr(gv, "ViewportConsole", None) if gv is not None else None
    except Exception:
        vc = None
    if vc is None:
        return False
    for name in ("ConsoleCommand", "SendToConsole"):
        if _try_call(f"ViewportConsole.{name}", getattr(vc, name, None), cmd, pc):
            return True
    return False


def _try_engine_exec(cmd: str, world: Any) -> bool:
    fn = getattr(ENGINE, "Exec", None)
    if not callable(fn):
        return False
    for ctx in (world, getattr(ENGINE, "GameViewport", None), ENGINE):
        if ctx is None:
            continue
        try:
            out = fn(ctx, cmd)
        except TypeError:
            continue
        except Exception as exc:
            _log(f"ENGINE.Exec failed ({cmd}): {exc!r}")
            return False
        if out is False:
            continue
        _log(f"ENGINE.Exec ok: {cmd} (returned {out!r})")
        return True
    return False


def _exec_console(cmd: str) -> bool:
    pc = get_pc()
    if pc is None:
        raise RuntimeError("No PlayerController available.")
    world = _world_context(pc)
    if _try_kismet_execute(cmd, world, pc):
        return True
    if _try_viewport_console(cmd, pc):
        return True
    if _try_engine_exec(cmd, world):
        return True
    if _try_call("PlayerController.ServerExec", getattr(pc, "ServerExec", None), cmd, pc):
        return True
    if str(cmd).lstrip().lower().startswith("gbx.") and _try_call(
        "PlayerController.ServerGbxConsoleCommand",
        getattr(pc, "ServerGbxConsoleCommand", None),
        cmd,
        pc,
    ):
        return True
    for name in ("SendToConsole", "ConsoleCommand"):
        if _try_call(f"PlayerController.{name}", getattr(pc, name, None), cmd, pc):
            return True
    raise RuntimeError("Could not run travel console command.")


def load_travel_stations() -> list[dict[str, str]]:
    global _STATION_CACHE
    if _STATION_CACHE is not None:
        return list(_STATION_CACHE)
    blob = pkgutil.get_data(__package__ or __name__.rpartition('.')[0], 'travelstations.json')
    if blob is None:
        raise RuntimeError('Could not load travelstations.json from package data.')
    data = json.loads(blob.decode('utf-8'))
    rows = data.get('stations') if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise RuntimeError('travelstations.json must contain a stations list.')
    out: list[dict[str, str]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        station = str(row.get('station', '')).strip()
        world = str(row.get('world', '')).strip()
        if not station:
            continue
        if not world and '.' in station:
            world = station.split('.', 1)[0]
        display = str(row.get('display_name') or (station.split('.', 1)[1] if '.' in station else station)).strip()
        category = str(row.get('category') or 'Standard').strip()
        out.append({'station': station, 'world': world, 'display_name': display, 'category': category, 'typedef': str(row.get('typedef', '')).strip(), 'dest': str(row.get('dest', '')).strip()})
    _STATION_CACHE = out
    return list(out)


def load_travel_maps() -> list[dict[str, str]]:
    global _MAP_CACHE
    if _MAP_CACHE is not None:
        return list(_MAP_CACHE)

    # Dedupe maps case-insensitively. Some station data uses different
    # capitalization than the manually curated default list, e.g.
    # Elpiselevator_P vs ElpisElevator_P. Prefer the capitalization from
    # travelstations.json when present so station filtering and travel commands
    # use the map id the game data actually exposes, while keeping the friendly
    # default description.
    default_by_norm: dict[str, dict[str, str]] = {}
    preferred_norms: list[str] = []
    for row in _DEFAULT_MAP_ROWS:
        name = str(row.get('map', '')).strip()
        if not name:
            continue
        norm = _norm_map_name(name)
        if norm not in default_by_norm:
            preferred_norms.append(norm)
            default_by_norm[norm] = {'map': name, 'display_name': str(row.get('display_name', name))}

    station_world_by_norm: dict[str, str] = {}
    for st in load_travel_stations():
        world = str(st.get('world', '')).strip()
        if not world:
            continue
        station_world_by_norm.setdefault(_norm_map_name(world), world)

    merged: dict[str, dict[str, str]] = {}
    for norm, row in default_by_norm.items():
        original = row['map']
        canonical = station_world_by_norm.get(norm, original)
        merged[norm] = {
            'map': canonical,
            'display_name': _display_with_canonical_map_name(row['display_name'], canonical, original),
        }

    for norm, canonical in station_world_by_norm.items():
        if norm not in merged:
            merged[norm] = {'map': canonical, 'display_name': canonical}

    ordered: list[dict[str, str]] = []
    seen: set[str] = set()
    for norm in preferred_norms:
        row = merged.get(norm)
        if row is not None:
            ordered.append(row)
            seen.add(norm)
    for norm in sorted(n for n in merged if n not in seen):
        ordered.append(merged[norm])

    _MAP_CACHE = ordered
    return list(ordered)


def filter_travel_maps(search: str = '', limit: int = 80) -> list[dict[str, str]]:
    needle = (search or '').strip().lower()
    results: list[dict[str, str]] = []
    for row in load_travel_maps():
        hay = f"{row['map']} {row['display_name']}".lower()
        if needle and needle not in hay:
            continue
        results.append(row)
        if limit > 0 and len(results) >= limit:
            break
    return results


def filter_travel_stations(map_name: str = '', search: str = '', limit: int = 125) -> list[dict[str, str]]:
    needle = (search or '').strip().lower()
    map_name = (map_name or '').strip()
    map_norm = _norm_map_name(map_name)
    show_all = not map_name or map_name == '__ALL__'
    results: list[dict[str, str]] = []
    for row in load_travel_stations():
        if not show_all and _norm_map_name(str(row.get('world', ''))) != map_norm:
            continue
        hay = f"{row.get('station','')} {row.get('display_name','')} {row.get('world','')} {row.get('category','')} {row.get('typedef','')} {row.get('dest','')}".lower()
        if needle and needle not in hay:
            continue
        results.append(row)
        if limit > 0 and len(results) >= limit:
            break
    return results


def travel_to_map(map_name: str) -> str:
    map_name = str(map_name or '').strip()
    if not map_name:
        raise RuntimeError('No map selected.')
    _exec_console(f"servertravel {map_name}")
    return f"Requested travel to map {map_name}."


def travel_to_station(station: str) -> str:
    station = str(station or '').strip()
    if not station:
        raise RuntimeError('No travel station selected.')
    _exec_console(f"gbx.servertraveltostation {station}")
    return f"Requested travel to station {station}."
