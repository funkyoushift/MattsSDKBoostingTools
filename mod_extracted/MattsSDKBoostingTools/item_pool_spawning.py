"""Generic item pool spawning helpers for Matt's SDK Boosting Tools."""
from __future__ import annotations

import json
import pkgutil
from collections.abc import Sequence

from unrealsdk import logging

from .shinies import DEFAULT_ITEM_LEVEL, _get_pool_store, _get_runtime_pc, _get_spawn_transform, _get_world, _get_player_pose, _spawn_pool, _spawn_pose

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


def spawn_item_pool(pool_name: str, level: int = DEFAULT_ITEM_LEVEL, count: int = 1) -> int:
    pool_name = str(pool_name or '').strip()
    if not pool_name:
        raise RuntimeError('No item pool selected.')
    count = max(1, min(int(count), 100))
    level = max(1, int(level))

    world = _get_world()
    pc = _get_runtime_pc()
    if world is None or pc is None:
        raise RuntimeError('Player or world is not available.')

    transform = _get_spawn_transform(pc)
    player_pose = _get_player_pose(pc)
    if transform is None or player_pose is None:
        raise RuntimeError('Could not derive a spawn transform.')

    config = _get_pool_store()
    player_location, player_rotation = player_pose
    for index in range(count):
        location, rotation = _spawn_pose(player_location, player_rotation, index)
        _spawn_pool(config, world, transform, level, pool_name, location, rotation)
    _log_info(f"Spawned item pool {pool_name} x{count} at level {level}.")
    return count
