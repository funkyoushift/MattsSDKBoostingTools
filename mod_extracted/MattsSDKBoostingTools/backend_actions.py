"""Bridge-safe backend actions for Matt's SDK Boosting Tools.

This module must not import BLImGui or blimgui_panel. It owns the small bit of
external-bridge state needed before the optional in-game panel is available.
"""
from __future__ import annotations

import re
from typing import Any

from mods_base import get_pc

from . import player_economy, serial_rewards
from .golden_chest_keybinds import _close_golden_chest, _open_golden_chest
from .inventory_capacity import (
    clamp_container_size,
    set_inventory_sizes_for_all_party,
    set_inventory_sizes_for_party_index,
)
from .dev_tools import activate_devperk as _activate_devperk
from .dev_tools import teleport_pawn_to_debug_cam as _teleport_pawn_to_debug_cam
from .dev_tools import toggle_debug_cam as _toggle_debug_cam
from .item_pool_spawning import spawn_item_pool
from .movement_adjustments import delete_ground_items, zero_vault_power_costs_all_players
from .party_helpers import _gbc_session_world_and_gamestate, _kick_party_player_by_index, _list_party_players
from .serial_converter import human_to_serial as _human_to_serial, serial_to_human as _serial_to_human
from .shinies import DEFAULT_ITEM_LEVEL as _SHINY_DEFAULT_LEVEL, drop_all_shinies
from .travel import _exec_console, travel_to_map as _travel_to_map, travel_to_station as _travel_to_station

CURRENCY_KINDS = ["cash", "eridium", "vaultcard1", "vaultcard2", "vaultcard3"]
EXP_TRACKS = ["player", "specialization", "vaultcard_xp_1", "vaultcard_xp_2", "vaultcard_xp_3"]
MAX_WALLET_AMOUNT = 2147483647
MAX_PLAYER_LEVEL = 60
MAX_SPEC_LEVEL = 701
MAX_VAULT_CARD_LEVEL = 9999999

_selected_player_index: int | None = None
_selected_player_name: str = ""
_last_refresh_error: str = ""
serial_text: str = ""
serial_tools_input: str = ""
serial_tools_serialized: str = ""
serial_tools_deserialized: str = ""
serial_tools_parts_breakdown: str = ""
serial_tools_status: str = "Paste a @U serial or deserialized serial text above."


def _clamp_int(value: object, min_value: int, max_value: int) -> int:
    return max(int(min_value), min(int(value), int(max_value)))


def _max_level_for_track(track: object) -> int:
    try:
        track_index = int(track)
    except Exception:
        key = str(track or "").strip().lower()
        track_index = EXP_TRACKS.index(key) if key in EXP_TRACKS else 0
    if track_index == 0:
        return MAX_PLAYER_LEVEL
    if track_index == 1:
        return MAX_SPEC_LEVEL
    return MAX_VAULT_CARD_LEVEL


def _kind_from_input(kind_or_index: object) -> str | None:
    raw = str(kind_or_index or "").strip().lower()
    try:
        idx = int(raw)
        if 0 <= idx < len(CURRENCY_KINDS):
            return CURRENCY_KINDS[idx]
    except Exception:
        pass
    if raw in CURRENCY_KINDS:
        return raw
    return None


def _track_from_input(track_or_index: object) -> str | None:
    raw = str(track_or_index or "").strip().lower()
    try:
        idx = int(raw)
        if 0 <= idx < len(EXP_TRACKS):
            return EXP_TRACKS[idx]
    except Exception:
        pass
    if raw in EXP_TRACKS:
        return raw
    return None


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


def give_currency(kind_or_index: object, amount: object) -> dict[str, Any]:
    name = get_selected_player_name()
    if not name:
        return {"ok": False, "message": "No party player selected."}
    kind = _kind_from_input(kind_or_index)
    if kind is None:
        return {"ok": False, "message": f"Unsupported currency kind: {kind_or_index}"}
    try:
        amount_i = _clamp_int(amount, -MAX_WALLET_AMOUNT, MAX_WALLET_AMOUNT)
    except Exception:
        return {"ok": False, "message": "Currency amount must be a number."}
    try:
        player_economy._do_give_currency(kind, amount_i, name)
        return {"ok": True, "message": f"Give {amount_i} {kind} requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Give currency failed: {exc!r}"}


def give_experience(track_or_index: object, level: object) -> dict[str, Any]:
    name = get_selected_player_name()
    if not name:
        return {"ok": False, "message": "No party player selected."}
    track = _track_from_input(track_or_index)
    if track is None:
        return {"ok": False, "message": f"Unsupported XP track: {track_or_index}"}
    try:
        level_i = _clamp_int(level, 0, _max_level_for_track(track))
    except Exception:
        return {"ok": False, "message": "Level must be a number."}
    try:
        player_economy._do_give_experience(track, level_i, name)
        return {"ok": True, "message": f"Set {track} level {level_i} requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Set level failed: {exc!r}"}


def max_player_level() -> dict[str, Any]:
    name = get_selected_player_name()
    if not name:
        return {"ok": False, "message": "No party player selected."}
    try:
        player_economy._do_give_experience("player", MAX_PLAYER_LEVEL, name)
        return {"ok": True, "message": "Max player level requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Max player level failed: {exc!r}"}


def max_spec_level() -> dict[str, Any]:
    name = get_selected_player_name()
    if not name:
        return {"ok": False, "message": "No party player selected."}
    try:
        player_economy._do_give_experience("specialization", MAX_SPEC_LEVEL, name)
        return {"ok": True, "message": "Max specialization requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Max specialization failed: {exc!r}"}


def max_currency() -> dict[str, Any]:
    name = get_selected_player_name()
    if not name:
        return {"ok": False, "message": "No party player selected."}
    try:
        player_economy._do_give_currency("cash", MAX_WALLET_AMOUNT, name)
        return {"ok": True, "message": "Max cash requested for selected player."}
    except Exception as exc:
        return {"ok": False, "message": f"Max cash failed: {exc!r}"}


def max_eridium() -> dict[str, Any]:
    name = get_selected_player_name()
    if not name:
        return {"ok": False, "message": "No party player selected."}
    try:
        player_economy._do_give_currency("eridium", MAX_WALLET_AMOUNT, name)
        return {"ok": True, "message": "Max eridium requested for selected player."}
    except Exception as exc:
        return {"ok": False, "message": f"Max eridium failed: {exc!r}"}


def max_sdu() -> dict[str, Any]:
    name = get_selected_player_name()
    if not name:
        return {"ok": False, "message": "No party player selected."}
    try:
        player_economy._do_msbt_maxsdu(["name", name])
        return {"ok": True, "message": "Max SDU requested."}
    except Exception as exc:
        return {"ok": False, "message": f"Max SDU failed: {exc!r}"}


def toggle_debug_cam() -> dict[str, Any]:
    idx = get_selected_player_index()
    try:
        message = _toggle_debug_cam(idx)
        return {"ok": True, "message": message}
    except Exception as exc:
        return {"ok": False, "message": f"Toggle Debug Cam failed: {exc!r}"}


def teleport_debug_cam() -> dict[str, Any]:
    idx = get_selected_player_index()
    try:
        message = _teleport_pawn_to_debug_cam(idx)
        return {"ok": True, "message": message}
    except Exception as exc:
        return {"ok": False, "message": f"Teleport Pawn to Debug Cam failed: {exc!r}"}


def activate_devperk(perk: object) -> dict[str, Any]:
    idx = get_selected_player_index()
    try:
        label = _activate_devperk(int(perk), idx)
        return {"ok": True, "message": f"Dev perk {int(perk)} requested.", "label": label}
    except Exception as exc:
        return {"ok": False, "message": f"Dev perk failed: {exc!r}"}


def spawn_itempool(pool_name: object, count: object, level: object) -> dict[str, Any]:
    name = str(pool_name or "").strip()
    if not name:
        return {"ok": False, "message": "No item pool selected."}
    try:
        spawned = spawn_item_pool(name, int(level), int(count))
        return {"ok": True, "message": f"Spawned item pool {name} x{spawned} at level {int(level)}."}
    except Exception as exc:
        return {"ok": False, "message": f"Spawn item pool failed: {exc!r}"}


def travel_to_map(map_name: object) -> dict[str, Any]:
    try:
        msg = _travel_to_map(str(map_name or "").strip())
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Travel to map failed: {exc!r}"}


def travel_to_station(station_name: object) -> dict[str, Any]:
    try:
        msg = _travel_to_station(str(station_name or "").strip())
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Travel to station failed: {exc!r}"}


def movement_delete_ground_items() -> dict[str, Any]:
    try:
        msg = delete_ground_items()
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Delete ground items failed: {exc!r}"}


def movement_zero_vault() -> dict[str, Any]:
    try:
        msg = zero_vault_power_costs_all_players()
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Zero vault cooldown failed: {exc!r}"}


def clear_serials() -> dict[str, Any]:
    global serial_text
    serial_text = ""
    return {"ok": True, "message": "Cleared boosting serial input in the backend state."}


def clear_serial_tools() -> dict[str, Any]:
    global serial_tools_input, serial_tools_serialized, serial_tools_deserialized, serial_tools_parts_breakdown, serial_tools_status
    serial_tools_input = ""
    serial_tools_serialized = ""
    serial_tools_deserialized = ""
    serial_tools_parts_breakdown = ""
    serial_tools_status = "Paste a @U serial or deserialized serial text above."
    return {"ok": True, "message": "Cleared Serial Tools state."}


def _parse_serial_text(raw: object) -> list[str]:
    tokens: list[str] = []
    for line in str(raw or "").strip().splitlines():
        text = line.strip()
        if not text:
            continue
        if "|" in text:
            tokens.append(text)
            continue
        starts = [m.start() for m in re.finditer(r"(?=@U)", text)]
        if len(starts) > 1:
            starts.append(len(text))
            for i in range(len(starts) - 1):
                part = text[starts[i]:starts[i + 1]].strip()
                if part:
                    tokens.append(part)
            continue
        tokens.append(text)
    return tokens


def _serial_with_level_override(serial: str, level: int) -> str:
    raw = str(serial or "").strip()
    if not raw:
        return raw
    level_i = _clamp_int(level, 1, 60)
    human = _serial_to_human(raw) if raw.startswith("@U") else raw
    new_human, count = re.subn(r"^(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*)\d+", rf"\g<1>{level_i}", human, count=1)
    if count <= 0:
        raise ValueError("could not find leading item level in serial")
    return _human_to_serial(new_human)


def _serials_with_level_override(serials: list[str], enabled: bool, level: int) -> tuple[list[str], int, str | None]:
    if not enabled:
        return list(serials), 0, None
    level_i = _clamp_int(level, 1, 60)
    out: list[str] = []
    changed = 0
    for i, serial in enumerate(str(s or "").strip() for s in serials):
        if not serial:
            continue
        try:
            out.append(_serial_with_level_override(serial, level_i))
            changed += 1
        except Exception as exc:
            return list(serials), changed, f"Level override failed on serial #{i + 1}: {exc}"
    return out, changed, None


def _host_player_index_value() -> int | None:
    try:
        pc = get_pc()
    except Exception:
        pc = None
    host_ps = getattr(pc, "PlayerState", None) if pc is not None else None
    _world, gs = _gbc_session_world_and_gamestate()
    pa = getattr(gs, "PlayerArray", None) if gs is not None else None
    if pa is None:
        return 0
    try:
        count = len(pa)
    except Exception:
        return 0
    host_name = ""
    try:
        host_name = str(getattr(host_ps, "PlayerName", "") or getattr(host_ps, "SavedNetworkAddress", "") or "")
    except Exception:
        host_name = ""
    for i in range(count):
        try:
            ps = pa[i]
        except Exception:
            ps = None
        if ps is None:
            continue
        if host_ps is not None and ps is host_ps:
            return i
        try:
            if host_ps is not None and getattr(ps, "Name", None) == getattr(host_ps, "Name", None):
                return i
        except Exception:
            pass
        if host_name:
            try:
                pn = str(getattr(ps, "PlayerName", "") or getattr(ps, "SavedNetworkAddress", "") or "")
                if pn and pn == host_name:
                    return i
            except Exception:
                pass
    return 0


def _non_host_party_player_indices() -> list[int]:
    all_indices = [int(idx) for idx, _name in _players()]
    host_idx = _host_player_index_value()
    return [idx for idx in all_indices if host_idx is None or idx != host_idx]


def _deliver_serials_with_target(serials: list[str], mode: str) -> dict[str, Any]:
    if not serials:
        return {"ok": False, "message": "No valid serials to deliver."}
    mode_key = str(mode or "selected").lower().strip()
    chunks = serial_rewards._serial_delivery_chunks(serials)
    split_note = f" Split into {len(chunks)} package part(s)." if chunks else ""
    try:
        if mode_key == "all":
            serial_rewards._do_give_serial(serials, True)
            return {"ok": True, "message": f"Requested {len(serials)} serial(s) for all party players.{split_note}"}
        if mode_key in ("nonhost", "non_host", "all_non_host"):
            indices = _non_host_party_player_indices()
            if not indices:
                return {"ok": False, "message": "No non-host party players found."}
            serial_rewards._do_give_serial_to_player_indices(serials, indices, scope_label="all non-host players")
            return {
                "ok": True,
                "message": f"Requested {len(serials)} serial(s) for all non-host players ({len(indices)} target(s)).{split_note}",
            }
        idx = get_selected_player_index()
        name = get_selected_player_name() or "selected player"
        if idx is None:
            return {"ok": False, "message": "No party player selected."}
        serial_rewards._do_give_serial_to_player_indices(serials, [idx], scope_label=f"selected player {idx} {name}")
        return {"ok": True, "message": f"Requested {len(serials)} serial(s) for {name}.{split_note}"}
    except Exception as exc:
        return {"ok": False, "message": f"Serial delivery failed: {exc!r}"}


def give_serials(text: object, mode: str = "selected", override_level: object = False, level: object = 60) -> dict[str, Any]:
    global serial_text
    serial_text = str(text or "")
    if not serial_text.strip():
        return {"ok": False, "message": "Paste at least one Base85 serial first."}
    expanded = _parse_serial_text(serial_text)
    try:
        serials = serial_rewards._resolve_give_serial_strings(expanded)
    except Exception as exc:
        return {"ok": False, "message": f"Serial resolve failed: {exc!r}"}
    if not serials:
        return {"ok": False, "message": "No valid serials after parsing/resolving."}
    try:
        level_i = _clamp_int(level, 1, 60)
    except Exception:
        level_i = 60
    serials, changed, error = _serials_with_level_override(serials, bool(override_level), level_i)
    if error:
        return {"ok": False, "message": error}
    result = _deliver_serials_with_target(serials, mode)
    if result.get("ok") and changed:
        result["message"] = f"{result.get('message', '')} Level override: {changed} serial(s) set to level {level_i}."
    return result


def serial_convert(text: object) -> dict[str, Any]:
    global serial_tools_input, serial_tools_serialized, serial_tools_deserialized, serial_tools_parts_breakdown, serial_tools_status
    serial_tools_input = str(text or "").strip()
    if not serial_tools_input:
        serial_tools_serialized = ""
        serial_tools_deserialized = ""
        serial_tools_parts_breakdown = ""
        serial_tools_status = "Paste a @U serial or deserialized serial text above."
        return {
            "ok": False,
            "message": serial_tools_status,
            "serialized": "",
            "deserialized": "",
            "breakdown": "",
        }
    try:
        if serial_tools_input.startswith("@U"):
            human = _serial_to_human(serial_tools_input)
            serial = _human_to_serial(human)
        else:
            serial = _human_to_serial(serial_tools_input)
            human = _serial_to_human(serial)
        serial_tools_serialized = serial
        serial_tools_deserialized = human
        serial_tools_parts_breakdown = ""
        serial_tools_status = "Converted successfully."
        return {
            "ok": True,
            "message": serial_tools_status,
            "serialized": serial_tools_serialized,
            "deserialized": serial_tools_deserialized,
            "breakdown": serial_tools_parts_breakdown,
        }
    except Exception as exc:
        serial_tools_serialized = ""
        serial_tools_deserialized = ""
        serial_tools_parts_breakdown = ""
        serial_tools_status = f"Conversion failed: {exc}"
        return {
            "ok": False,
            "message": serial_tools_status,
            "serialized": "",
            "deserialized": "",
            "breakdown": "",
        }
