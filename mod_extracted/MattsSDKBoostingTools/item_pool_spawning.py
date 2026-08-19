"""Generic item pool spawning helpers for Matt's SDK Boosting Tools."""
from __future__ import annotations

import json
import math
import pkgutil
from collections.abc import Sequence

from unrealsdk import logging

from .shinies import (
    DEFAULT_ITEM_LEVEL,
    SPAWN_FORWARD_OFFSET,
    SPAWN_GRID_COLUMNS,
    SPAWN_HEIGHT_OFFSET,
    SPAWN_ROW_SPACING,
    SPAWN_SIDE_SPACING,
    _get_player_pose,
    _get_pool_store,
    _get_runtime_pc,
    _get_spawn_transform,
    _get_world,
    _make_rotator,
    _make_vector,
    _spawn_pool,
    _spawn_pose,
)

ITEM_POOL_SPIT_DIRECTIONS = ("forward", "left", "right", "back", "around")

_ITEM_POOL_CACHE: list[dict[str, str]] | None = None


def _log_info(message: str) -> None:
    logging.info(f"[Matts SDK Boosting Tools | Item Pools] {message}")


def load_item_pools() -> list[dict[str, str]]:
    global _ITEM_POOL_CACHE
    if _ITEM_POOL_CACHE is not None:
        return list(_ITEM_POOL_CACHE)
    blob = pkgutil.get_data(__package__ or __name__.rpartition('.')[0], 'item_pools.json')
    if blob is None:
        raise RuntimeError('Could not load item_pools.json from package data.')
    data = json.loads(blob.decode('utf-8'))
    if not isinstance(data, list):
        raise RuntimeError('item_pools.json must contain a JSON list.')
    pools: list[dict[str, str]] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        pool = str(entry.get('itempool', '')).strip()
        display = str(entry.get('display_name', pool)).strip() or pool
        category = str(entry.get('category', 'Other')).strip() or 'Other'
        low = pool.lower()
        cat_low = category.lower()
        disp_low = display.lower()
        if (
            not pool
            or 'turret' in low
            or 'terminal' in low
            or cat_low == 'cosmetic'
            or low.startswith('cosmetics')
            or low.startswith('cosmetic')
            or disp_low.startswith('cosmetic')
        ):
            continue
        pools.append({'display_name': display, 'itempool': pool, 'category': category})
    _ITEM_POOL_CACHE = pools
    return list(pools)


def item_pool_categories() -> list[str]:
    preferred = ['All', 'Assault Rifle', 'Pistol', 'SMG', 'Sniper', 'Shotgun', 'Heavy', 'Class Mod', 'Shield', 'Ordnance', 'Repkit', 'Ammo', 'Currency', 'Shiny', 'Other']
    found = {entry['category'] for entry in load_item_pools()}
    ordered = [category for category in preferred if category == 'All' or category in found]
    for category in sorted(found):
        if category not in ordered:
            ordered.append(category)
    return ordered


def filter_item_pools(search: str = '', category: str = 'All', limit: int = 100) -> list[dict[str, str]]:
    needle = (search or '').strip().lower()
    category = category or 'All'
    results: list[dict[str, str]] = []
    for entry in load_item_pools():
        if category != 'All' and entry['category'] != category:
            continue
        if needle and needle not in entry['display_name'].lower() and needle not in entry['itempool'].lower():
            continue
        results.append(entry)
        if limit > 0 and len(results) >= limit:
            break
    return results


def _normalize_spit_direction(direction: str) -> str:
    key = str(direction or "forward").strip().lower()
    aliases = {
        "front": "forward",
        "ahead": "forward",
        "behind": "back",
        "circle": "around",
        "ring": "around",
    }
    key = aliases.get(key, key)
    return key if key in ITEM_POOL_SPIT_DIRECTIONS else "forward"


def item_pool_spit_offsets(direction: str, index: int, count: int) -> tuple[float, float]:
    """Return (forward_cm, side_cm) for one spit index. Pure helper for tests."""
    key = _normalize_spit_direction(direction)
    idx = max(0, int(index))
    total = max(1, int(count))
    column = idx % SPAWN_GRID_COLUMNS
    row = idx // SPAWN_GRID_COLUMNS
    centered = (column - ((SPAWN_GRID_COLUMNS - 1) / 2.0)) * SPAWN_SIDE_SPACING
    depth = SPAWN_FORWARD_OFFSET + (row * SPAWN_ROW_SPACING)
    if key == "left":
        return centered, -depth
    if key == "right":
        return centered, depth
    if key == "back":
        return -depth, centered
    if key == "around":
        angle = (2.0 * math.pi * float(idx)) / float(total)
        radius = SPAWN_FORWARD_OFFSET + 40.0
        return math.cos(angle) * radius, math.sin(angle) * radius
    return depth, centered


def _anchor_player_pose(pc: object) -> tuple[object, object] | None:
    try:
        from .spawn_helpers import actor_location, resolve_spawn_anchor_actor

        actor, _label = resolve_spawn_anchor_actor()
        loc = actor_location(actor) if actor is not None else None
        rot = None
        if actor is not None:
            getter = getattr(actor, "K2_GetActorRotation", None)
            if callable(getter):
                rot = getter()
        if loc is not None and rot is not None:
            return loc, rot
    except Exception:
        pass
    return _get_player_pose(pc)


def _directed_spawn_pose(player_location: object, player_rotation: object, index: int, count: int, direction: str):
    key = _normalize_spit_direction(direction)
    if key == "forward":
        return _spawn_pose(player_location, player_rotation, index)
    yaw_rad = math.radians(float(getattr(player_rotation, "Yaw", 0.0) or 0.0))
    forward_x = math.cos(yaw_rad)
    forward_y = math.sin(yaw_rad)
    right_x = -forward_y
    right_y = forward_x
    forward_offset, side_offset = item_pool_spit_offsets(key, index, count)
    new_x = float(player_location.X) + forward_x * forward_offset + right_x * side_offset
    new_y = float(player_location.Y) + forward_y * forward_offset + right_y * side_offset
    new_z = float(player_location.Z) + SPAWN_HEIGHT_OFFSET
    location = _make_vector(new_x, new_y, new_z)
    return location, _make_rotator(0.0, float(getattr(player_rotation, "Yaw", 0.0) or 0.0), 0.0)


def spawn_item_pool(
    pool_name: str,
    level: int = DEFAULT_ITEM_LEVEL,
    count: int = 1,
    *,
    direction: str = "forward",
    start_index: int = 0,
) -> int:
    pool_name = str(pool_name or '').strip()
    if not pool_name:
        raise RuntimeError('No item pool selected.')
    count = max(1, min(int(count), 100))
    level = max(1, int(level))
    spit = _normalize_spit_direction(direction)
    origin = max(0, int(start_index))

    world = _get_world()
    pc = _get_runtime_pc()
    if world is None or pc is None:
        raise RuntimeError('Player or world is not available.')

    transform = _get_spawn_transform(pc)
    player_pose = _anchor_player_pose(pc)
    if transform is None or player_pose is None:
        raise RuntimeError('Could not derive a spawn transform.')

    config = _get_pool_store()
    player_location, player_rotation = player_pose
    layout_count = max(count, origin + count)
    for index in range(count):
        location, rotation = _directed_spawn_pose(
            player_location,
            player_rotation,
            origin + index,
            layout_count,
            spit,
        )
        _spawn_pool(config, world, transform, level, pool_name, location, rotation)
    _log_info(f"Spawned item pool {pool_name} x{count} at level {level} spit={spit}.")
    return count
