"""Bridge-safe backend actions for Matt's SDK Boosting Tools.

This module must not import BLImGui or blimgui_panel. It owns the small bit of
external-bridge state needed before the optional in-game panel is available.
"""
from __future__ import annotations

from typing import Any

from .golden_chest_keybinds import _close_golden_chest, _open_golden_chest
from .inventory_capacity import (
    clamp_container_size,
    set_inventory_sizes_for_all_party,
    set_inventory_sizes_for_party_index,
)
from .party_helpers import _kick_party_player_by_index, _list_party_players
from .shinies import DEFAULT_ITEM_LEVEL as _SHINY_DEFAULT_LEVEL, drop_all_shinies
from .travel import _exec_console

_selected_player_index: int | None = None
_selected_player_name: str = ""
_last_refresh_error: str = ""


def _players() -> list[tuple[int, str]]:
    try:
        return [(int(idx), str(name)) for idx, name in _list_party_players()]
    except Exception as exc:
        global _last_refresh_error
        _last_refresh_error = repr(exc)
        return []


def refresh_players() -> list[dict[str, Any]]:
    """Refresh and return the current party player list."""
    global _selected_player_index, _selected_player_name, _last_refresh_error
    _last_refresh_error = ""
    players = _players()
    if players:
        if _selected_player_index is None or all(idx != _selected_player_index for idx, _name in players):
            _selected_player_index, _selected_player_name = players[0]
        else:
            for idx, name in players:
                if idx == _selected_player_index:
                    _selected_player_name = name
                    break
    else:
        _selected_player_index = None
        _selected_player_name = ""
    return [{"index": idx, "name": name} for idx, name in players]


def get_selected_player_index() -> int | None:
    refresh_players()
    return _selected_player_index


def get_selected_player_name() -> str:
    refresh_players()
    return _selected_player_name


def set_target_player(index_or_name: object) -> dict[str, Any]:
    """Set selected target by party index, "index|name" payload, or name text."""
    global _selected_player_index, _selected_player_name
    raw = str(index_or_name or "").strip()
    if "|" in raw:
        raw = raw.split("|", 1)[0].strip()
    if not raw:
        return {"ok": False, "message": "No target player was selected."}

    players = _players()
    wanted_index: int | None = None
    try:
        wanted_index = int(raw)
    except Exception:
        wanted_index = None

    if wanted_index is not None:
        for idx, name in players:
            if idx == wanted_index:
                _selected_player_index = idx
                _selected_player_name = name
                return {
                    "ok": True,
                    "message": f"Target player set to {idx}: {name}",
                    "selected_player": name,
                    "selected_player_index": idx,
                }
        return {
            "ok": False,
            "message": f"Could not find party player index {wanted_index}. Press Refresh Players and try again.",
        }

    needle = raw.lower()
    matches = [(idx, name) for idx, name in players if needle in name.lower()]
    if not matches:
        return {
            "ok": False,
            "message": f"Could not find party player matching {raw!r}. Press Refresh Players and try again.",
        }
    if len(matches) > 1:
        labels = ", ".join(f"{idx}: {name}" for idx, name in matches[:5])
        return {"ok": False, "message": f"Target player {raw!r} is ambiguous: {labels}"}

    idx, name = matches[0]
    _selected_player_index = idx
    _selected_player_name = name
    return {
        "ok": True,
        "message": f"Target player set to {idx}: {name}",
        "selected_player": name,
        "selected_player_index": idx,
    }


def get_status() -> dict[str, Any]:
    players = refresh_players()
    return {
        "players": players,
        "selected_player": _selected_player_name,
        "selected_player_index": _selected_player_index,
        "last_refresh_error": _last_refresh_error,
    }


def kick_selected_player() -> dict[str, Any]:
    idx = get_selected_player_index()
    name = get_selected_player_name()
    if idx is None or not name:
        return {"ok": False, "message": "No party player selected."}
    ok = _kick_party_player_by_index(idx, "Kicked by host")
    if not ok:
        return {"ok": False, "message": f"Kick selected player failed for {idx}: {name}."}
    return {"ok": True, "message": "Kick selected player requested."}


def open_golden_chest() -> dict[str, Any]:
    try:
        _open_golden_chest()
        return {"ok": True, "message": "Open Golden Chest requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Open Golden Chest failed: {exc!r}"}


def close_golden_chest() -> dict[str, Any]:
    try:
        _close_golden_chest()
        return {"ok": True, "message": "Close Golden Chest requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Close Golden Chest failed: {exc!r}"}


def drop_all_shinies_selected() -> dict[str, Any]:
    try:
        drop_all_shinies(_SHINY_DEFAULT_LEVEL)
        return {"ok": True, "message": "Drop All Shinies requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Drop All Shinies failed: {exc!r}"}


def open_bank_anywhere() -> dict[str, Any]:
    try:
        _exec_console("gbx.ui.view.stateadd MENU_BANK")
        return {"ok": True, "message": "Open Bank Anywhere requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Open Bank Anywhere failed: {exc!r}"}


def set_inventory_sizes_selected(backpack_size: object, bank_size: object) -> dict[str, Any]:
    idx = get_selected_player_index()
    if idx is None:
        return {"ok": False, "message": "No party player selected."}
    try:
        bp = clamp_container_size(int(backpack_size), 1000)
        bank = clamp_container_size(int(bank_size), 1000)
    except Exception:
        return {"ok": False, "message": "Backpack and Bank Size must be numbers."}
    try:
        name = set_inventory_sizes_for_party_index(idx, bp, bank)
        return {"ok": True, "message": f"Set inventory sizes for {name}: backpack {bp}, bank {bank}."}
    except Exception as exc:
        return {"ok": False, "message": f"Set backpack/bank size for selected player failed: {exc!r}"}


def set_inventory_sizes_all_party(backpack_size: object, bank_size: object) -> dict[str, Any]:
    try:
        bp = clamp_container_size(int(backpack_size), 1000)
        bank = clamp_container_size(int(bank_size), 1000)
    except Exception:
        return {"ok": False, "message": "Backpack and Bank Size must be numbers."}
    try:
        count = set_inventory_sizes_for_all_party(bp, bank)
        return {"ok": True, "message": f"Set inventory sizes for {count} party player(s): backpack {bp}, bank {bank}."}
    except Exception as exc:
        return {"ok": False, "message": f"Set backpack/bank size for all party players failed: {exc!r}"}
