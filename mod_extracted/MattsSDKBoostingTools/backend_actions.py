"""Bridge-safe backend actions for Matt's SDK Boosting Tools.

This module must not import BLImGui or blimgui_panel. It owns the small bit of
external-bridge state needed before the optional in-game panel is available.
"""
from __future__ import annotations

from typing import Any

from .party_helpers import _list_party_players

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
