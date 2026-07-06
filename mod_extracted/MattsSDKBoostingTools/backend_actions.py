"""Bridge-safe backend actions for Matt's SDK Boosting Tools.

This module must not import BLImGui or blimgui_panel. It owns the small bit of
external-bridge state needed before the optional in-game panel is available.
"""
from __future__ import annotations

import re
from typing import Any

from mods_base import ENGINE, get_pc

from . import player_economy, serial_rewards
from .golden_chest_keybinds import _close_golden_chest, _open_golden_chest
from .inventory_capacity import (
    auto_apply_inventory_sizes_if_needed,
    clamp_container_size,
    set_inventory_sizes_for_all_party,
    set_inventory_sizes_for_party_index,
)
from .dev_tools import activate_devperk as _activate_devperk
from .dev_tools import teleport_pawn_to_debug_cam as _teleport_pawn_to_debug_cam
from .dev_tools import toggle_debug_cam as _toggle_debug_cam
from .item_pool_spawning import spawn_item_pool
from .movement_adjustments import (
    apply_movement_advanced_to_all_players,
    delete_ground_items,
    pawn_for_controller,
    refresh_jump_counts_all_players,
    reset_movement_advanced_all_players,
    set_infinite_jump_all,
    set_infinite_jump_for_index,
    set_no_target,
    set_noclip,
    set_time_dilation,
    teleport_pawn_to_pawn,
    toggle_infinite_jump_for_index,
    toggle_players_only,
    zero_vault_power_costs_all_players,
)
from .party_helpers import (
    _gbc_find_pc_for_player_state,
    _gbc_session_world_and_gamestate,
    _kick_party_player_by_index,
    _list_party_players,
)
from .serial_converter import human_to_serial as _human_to_serial, serial_to_human as _serial_to_human
from .shinies import DEFAULT_ITEM_LEVEL as _SHINY_DEFAULT_LEVEL, drop_all_shinies
from .travel import _exec_console, travel_to_map as _travel_to_map, travel_to_station as _travel_to_station

CURRENCY_KINDS = ["cash", "eridium", "vaultcard1", "vaultcard2", "vaultcard3"]
EXP_TRACKS = ["player", "specialization", "vaultcard_xp_1", "vaultcard_xp_2", "vaultcard_xp_3"]
MAX_WALLET_AMOUNT = 2147483647
MAX_PLAYER_LEVEL = 60
MAX_SPEC_LEVEL = 701
MAX_VAULT_CARD_LEVEL = 9999999
RARITY_ROWS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("common", "Common", ("CommonModifier",)),
    ("uncommon", "Uncommon", ("UncommonModifier",)),
    ("rare", "Rare", ("RareModifier",)),
    ("epic", "Epic", ("VeryRareModifier", "EpicModifier")),
    ("legendary", "Legendary", ("LegendaryModifier",)),
    ("pearlescent", "Pearlescent", ("PearlModifier", "PearlescentModifier")),
)

_selected_player_index: int | None = None
_selected_player_name: str = ""
_last_refresh_error: str = ""
serial_text: str = ""
serial_tools_input: str = ""
serial_tools_serialized: str = ""
serial_tools_deserialized: str = ""
serial_tools_parts_breakdown: str = ""
serial_tools_status: str = "Paste a @U serial or deserialized serial text above."
_movement_no_target_enabled = False
_movement_noclip_enabled = False
_rarity_weights: dict[str, float] = {key: 1.0 for key, _label, _fields in RARITY_ROWS}


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
        if _selected_player_index is not None and any(idx == _selected_player_index for idx, _name in players):
            for idx, name in players:
                if idx == _selected_player_index:
                    _selected_player_name = name
                    break
        else:
            _selected_player_index = None
            _selected_player_name = ""
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
    try:
        delivery_progress = serial_rewards.serial_delivery_progress()
    except Exception as exc:
        delivery_progress = {
            "active": False,
            "message": "",
            "last_error": f"serial delivery progress unavailable: {exc!r}",
        }
    try:
        delivery_status = serial_rewards.serial_delivery_status()
    except Exception:
        delivery_status = ""
    if isinstance(delivery_progress, dict):
        delivery_progress = dict(delivery_progress)
        delivery_progress.setdefault("last_message", delivery_status or delivery_progress.get("message", ""))
        delivery_progress.setdefault("last_error", "")
    else:
        delivery_progress = {"active": False, "message": str(delivery_progress or ""), "last_error": ""}
    return {
        "players": players,
        "selected_player": _selected_player_name,
        "selected_player_index": _selected_player_index,
        "last_refresh_error": _last_refresh_error,
        "serial_delivery": delivery_progress,
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


def auto_apply_inventory_sizes(backpack_size: object, bank_size: object, enabled: object = True) -> dict[str, Any]:
    try:
        is_enabled = str(enabled).strip().lower() not in ("", "0", "false", "off", "no", "none")
        bp = clamp_container_size(int(backpack_size), 1000)
        bank = clamp_container_size(int(bank_size), 1000)
    except Exception:
        return {"ok": False, "message": "Backpack and Bank Size must be numbers."}
    try:
        count = auto_apply_inventory_sizes_if_needed(is_enabled, bp, bank, source="external-bridge")
        if not is_enabled:
            return {"ok": True, "message": "Automatic inventory sizing disabled.", "applied": 0}
        if count:
            return {
                "ok": True,
                "message": f"Auto-applied inventory sizes to {count} party player(s): backpack {bp}, bank {bank}.",
                "applied": count,
            }
        return {"ok": True, "message": "Automatic inventory sizing checked; waiting for loaded party players.", "applied": 0}
    except Exception as exc:
        return {"ok": False, "message": f"Automatic inventory update failed: {exc!r}"}


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


def _selected_player_controller() -> Any | None:
    idx = get_selected_player_index()
    if idx is None:
        return None
    return _party_controller_for_index(idx)


def _party_controller_for_index(idx: int | None) -> Any | None:
    if idx is None:
        return None
    world, gs = _gbc_session_world_and_gamestate()
    pa = getattr(gs, "PlayerArray", None) if gs is not None else None
    if pa is None:
        return get_pc() if idx == 0 else None
    try:
        ps = pa[int(idx)]
    except Exception:
        return get_pc() if idx == 0 else None
    pc = _gbc_find_pc_for_player_state(ps, world)
    return pc or (get_pc() if idx == 0 else None)


def _pawn_for_party_index(idx: int | None) -> Any | None:
    pc = _party_controller_for_index(idx)
    if pc is None:
        return None
    try:
        pawn = pawn_for_controller(pc)
        if pawn is not None:
            return pawn
    except Exception:
        pass
    for attr in ("OakCharacter", "Character", "Pawn", "AcknowledgedPawn"):
        try:
            pawn = getattr(pc, attr, None)
            if pawn is not None:
                return pawn
        except Exception:
            pass
    return None


def max_all() -> dict[str, Any]:
    name = get_selected_player_name()
    if not name:
        return {"ok": False, "message": "No party player selected."}
    try:
        player_economy._do_give_experience("player", MAX_PLAYER_LEVEL, name)
        player_economy._do_give_experience("specialization", MAX_SPEC_LEVEL, name)
        player_economy._do_give_currency("cash", MAX_WALLET_AMOUNT, name)
        player_economy._do_give_currency("eridium", MAX_WALLET_AMOUNT, name)
        player_economy._do_msbt_maxsdu(["name", name])
        vc_msg = ""
        pc = _selected_player_controller()
        if pc is not None:
            try:
                from .vault_card_boost import max_all_vault_cards_for_pc

                vc_ok, vc_detail = max_all_vault_cards_for_pc(pc)
                vc_msg = f" Vault cards {'OK' if vc_ok else 'partial'}: {vc_detail[:120]}"
            except Exception as exc:
                vc_msg = f" Vault-card PC path failed; economy fallback used: {exc!r}"
                pc = None
        if pc is None:
            for vc_kind in ("vaultcard1", "vaultcard2", "vaultcard3"):
                player_economy._do_give_currency(vc_kind, MAX_WALLET_AMOUNT, name)
            for vc_xp in ("vaultcard_xp_1", "vaultcard_xp_2", "vaultcard_xp_3"):
                player_economy._do_give_experience(vc_xp, MAX_VAULT_CARD_LEVEL, name)
            if not vc_msg:
                vc_msg = " Vault cards requested through economy fallback."
        return {
            "ok": True,
            "message": (
                f"Max All requested for {name}: player {MAX_PLAYER_LEVEL}, spec {MAX_SPEC_LEVEL}, "
                f"cash/eridium {MAX_WALLET_AMOUNT:,}, max SDU.{vc_msg}"
            ),
        }
    except Exception as exc:
        return {"ok": False, "message": f"Max All failed: {exc!r}"}


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


def _movement_float(value: object, default: float) -> float:
    raw = str(value if value is not None else "").replace("x", "").replace("X", "").strip()
    if raw == "":
        return float(default)
    return float(raw)


def _truthy(value: object) -> bool:
    return str(value or "").strip().lower() in ("1", "true", "yes", "on", "checked")


def _movement_apply_values(
    *,
    speed_scale: float = 1.0,
    walk_speed: float = 600.0,
    jump_goal: float = 198.0,
    jump_velocity: float = 840.0,
    gravity_scale: float = 1.0,
    max_step_height: float = 45.0,
    jump_count: int = 2,
    jump_off_z_factor: float = 0.5,
    walkable_floor_angle: float = 44.76508331298828,
    walkable_floor_z: float = 0.7099999785423279,
    sprint_jump_goal: float | None = 198.0,
    jump_hold_time: float | None = 0.0,
    glide_speed: float = 1200.0,
    glide_boost: float = 0.0,
    glide_air_control: float = 0.6000000238418579,
    dash_speed: float = 2500.0,
    vault_cost: float | None = None,
    double_jump_goal: float | None = 225.0,
    slide_jump_goal: float | None = 198.0,
    reset_jump_defaults: bool = False,
) -> dict[str, Any]:
    try:
        msg = apply_movement_advanced_to_all_players(
            speed_scale,
            walk_speed,
            jump_goal,
            jump_velocity,
            gravity_scale,
            max_step_height,
            jump_count,
            jump_off_z_factor,
            walkable_floor_angle,
            walkable_floor_z,
            sprint_jump_goal,
            jump_hold_time,
            glide_speed,
            glide_boost,
            glide_air_control,
            dash_speed,
            vault_cost,
            double_jump_goal=double_jump_goal,
            slide_jump_goal=slide_jump_goal,
            sections={"speed", "jump", "gravity", "wall", "glide", "vault", "jump_count"},
            reset_jump_defaults=reset_jump_defaults,
        )
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Apply movement settings failed: {exc!r}"}


def movement_apply_all(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    try:
        jump_goal = _movement_float(payload.get("movement_jump_height"), 198.0)
        floor_angle = _movement_float(payload.get("movement_floor_angle"), 44.76508331298828)
        individual = _truthy(payload.get("movement_individual_jump_goals"))
        return _movement_apply_values(
            speed_scale=_movement_float(payload.get("movement_speed_scale"), 1.0),
            walk_speed=_movement_float(payload.get("movement_walk_speed"), 600.0),
            jump_goal=jump_goal,
            jump_velocity=_movement_float(payload.get("movement_jump_velocity"), 840.0),
            gravity_scale=_movement_float(payload.get("movement_gravity_scale"), 1.0),
            max_step_height=_movement_float(payload.get("movement_step_height"), 45.0),
            jump_count=_clamp_int(payload.get("movement_jump_count") or 2, 1, 50),
            jump_off_z_factor=_movement_float(payload.get("movement_jump_off_z_factor"), 0.5),
            walkable_floor_angle=floor_angle,
            walkable_floor_z=_movement_float(payload.get("movement_floor_z"), 0.7099999785423279),
            sprint_jump_goal=_movement_float(payload.get("movement_sprint_jump_goal"), jump_goal) if individual else jump_goal,
            double_jump_goal=_movement_float(payload.get("movement_double_jump_goal"), jump_goal) if individual else jump_goal,
            slide_jump_goal=_movement_float(payload.get("movement_slide_jump_goal"), jump_goal) if individual else jump_goal,
            glide_speed=_movement_float(payload.get("movement_glide_speed"), 1200.0),
            glide_boost=_movement_float(payload.get("movement_glide_boost"), 0.0),
            glide_air_control=_movement_float(payload.get("movement_glide_air_control"), 0.6000000238418579),
            dash_speed=_movement_float(payload.get("movement_dash_speed"), 2500.0),
            vault_cost=0.0 if _truthy(payload.get("movement_zero_vault_on_apply")) else None,
        )
    except Exception as exc:
        return {"ok": False, "message": f"Movement values must be numeric: {exc!r}"}


def movement_reset_all() -> dict[str, Any]:
    try:
        msg = reset_movement_advanced_all_players()
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Reset movement settings failed: {exc!r}"}


def movement_apply_preset(name: object) -> dict[str, Any]:
    key = str(name or "").strip().lower()
    presets: dict[str, dict[str, Any]] = {
        "fast": {
            "speed_scale": 5.0, "walk_speed": 3200.0, "jump_goal": 560.0, "jump_velocity": 560.0,
            "glide_speed": 2600.0, "glide_boost": 4200.0, "glide_air_control": 6.0, "dash_speed": 3000.0,
            "sprint_jump_goal": 560.0, "double_jump_goal": 560.0, "slide_jump_goal": 560.0,
        },
        "veryfast": {
            "speed_scale": 8.0, "walk_speed": 5200.0, "jump_goal": 700.0, "jump_velocity": 700.0,
            "glide_speed": 3800.0, "glide_boost": 6500.0, "glide_air_control": 10.0, "dash_speed": 5200.0,
            "sprint_jump_goal": 700.0, "double_jump_goal": 700.0, "slide_jump_goal": 700.0,
        },
        "moon": {
            "jump_goal": 1200.0, "jump_velocity": 1200.0, "gravity_scale": 0.45,
            "sprint_jump_goal": 1200.0, "double_jump_goal": 1200.0, "slide_jump_goal": 1200.0,
        },
        "wallwalk": {
            "speed_scale": 5.0, "walk_speed": 3200.0, "jump_goal": 560.0, "jump_velocity": 560.0,
            "max_step_height": 700.0, "walkable_floor_angle": 89.9, "walkable_floor_z": 0.001,
            "sprint_jump_goal": 560.0, "double_jump_goal": 560.0, "slide_jump_goal": 560.0,
        },
        "fastglide": {
            "speed_scale": 5.0, "walk_speed": 3200.0, "jump_goal": 560.0, "jump_velocity": 560.0,
            "glide_speed": 5200.0, "glide_boost": 8500.0, "glide_air_control": 14.0, "dash_speed": 4500.0,
            "sprint_jump_goal": 560.0, "double_jump_goal": 560.0, "slide_jump_goal": 560.0,
        },
    }
    if key not in presets:
        return {"ok": False, "message": f"Unknown movement preset: {name}"}
    result = _movement_apply_values(**presets[key])
    if result.get("ok"):
        result["message"] = f"Applied {key} movement preset. {result.get('message') or ''}".strip()
    return result


def movement_toggle_no_target() -> dict[str, Any]:
    global _movement_no_target_enabled
    _movement_no_target_enabled = not _movement_no_target_enabled
    try:
        msg = set_no_target(_movement_no_target_enabled)
        return {"ok": True, "message": msg}
    except Exception as exc:
        _movement_no_target_enabled = not _movement_no_target_enabled
        return {"ok": False, "message": f"Toggle no target failed: {exc!r}"}


def movement_toggle_noclip() -> dict[str, Any]:
    global _movement_noclip_enabled
    _movement_noclip_enabled = not _movement_noclip_enabled
    try:
        msg = set_noclip(_movement_noclip_enabled)
        return {"ok": True, "message": msg}
    except Exception as exc:
        _movement_noclip_enabled = not _movement_noclip_enabled
        return {"ok": False, "message": f"Toggle noclip failed: {exc!r}"}


def movement_set_time(value: object) -> dict[str, Any]:
    try:
        msg = set_time_dilation(_movement_float(value, 1.0))
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Set time failed: {exc!r}"}


def movement_reset_time() -> dict[str, Any]:
    return movement_set_time(1.0)


def movement_toggle_players_only() -> dict[str, Any]:
    try:
        msg = toggle_players_only()
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Players Only failed: {exc!r}"}


def movement_teleport_selected_to_slot(slot: object) -> dict[str, Any]:
    try:
        slot_idx = _clamp_int(slot, 0, 3)
    except Exception:
        return {"ok": False, "message": "Teleport target slot must be P1, P2, P3, or P4."}
    src_idx = get_selected_player_index()
    if src_idx is None:
        return {"ok": False, "message": "No selected player to teleport. Press Refresh Players and choose a target."}
    if int(src_idx) == int(slot_idx):
        return {"ok": False, "message": f"Selected player is already P{slot_idx + 1}."}
    try:
        src = _pawn_for_party_index(src_idx)
        dst = _pawn_for_party_index(slot_idx)
        if src is None:
            return {"ok": False, "message": "Teleport failed: selected player pawn not found."}
        if dst is None:
            return {"ok": False, "message": f"Teleport failed: P{slot_idx + 1} pawn not found."}
        msg = teleport_pawn_to_pawn(src, dst)
        src_name = get_selected_player_name() or f"P{int(src_idx) + 1}"
        return {"ok": True, "message": f"{msg} {src_name} -> P{slot_idx + 1}."}
    except Exception as exc:
        return {"ok": False, "message": f"Teleport selected player failed: {exc!r}"}


def movement_infinite_jump_refresh() -> dict[str, Any]:
    try:
        msg = refresh_jump_counts_all_players()
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Infinite jump refresh failed: {exc!r}"}


def movement_infinite_jump_all(enabled: bool) -> dict[str, Any]:
    try:
        msg = set_infinite_jump_all(bool(enabled))
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Infinite jump all toggle failed: {exc!r}"}


def movement_infinite_jump_selected(index_or_name: object | None = None) -> dict[str, Any]:
    try:
        idx: int | None
        raw = "" if index_or_name is None else str(index_or_name).strip()
        if raw:
            try:
                idx = int(raw.split("|", 1)[0].strip())
            except Exception:
                result = set_target_player(raw)
                if not result.get("ok"):
                    return result
                idx = get_selected_player_index()
        else:
            idx = get_selected_player_index()
        if idx is None:
            return {"ok": False, "message": "No selected player for Infinite Jump. Press Refresh Players and choose a target."}
        msg = toggle_infinite_jump_for_index(int(idx))
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Infinite jump selected toggle failed: {exc!r}"}


def movement_infinite_jump_set_selected(index_or_name: object | None, enabled: bool) -> dict[str, Any]:
    try:
        result = set_target_player(index_or_name)
        if not result.get("ok"):
            return result
        idx = get_selected_player_index()
        if idx is None:
            return {"ok": False, "message": "No selected player for Infinite Jump. Press Refresh Players and choose a target."}
        msg = set_infinite_jump_for_index(int(idx), bool(enabled))
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "message": f"Infinite jump selected set failed: {exc!r}"}


def _rarity_current_gamestate() -> object | None:
    try:
        viewport = getattr(ENGINE, "GameViewport", None)
        world = getattr(viewport, "World", None) if viewport is not None else None
        return getattr(world, "GameState", None) if world is not None else None
    except Exception:
        return None


def _rarity_state_for_gamestate(gs: object | None) -> object | None:
    if gs is None:
        return None
    for attr in ("RarityState", "RarityModifier", "RarityModifiers", "GameRarityState"):
        try:
            candidate = getattr(gs, attr, None)
            if candidate is not None:
                return candidate
        except Exception:
            pass
    return None


def _rarity_get_modifier(state: object | None, fields: tuple[str, ...]) -> object | None:
    if state is None:
        return None
    for field in fields:
        try:
            mod = getattr(state, field, None)
            if mod is not None:
                return mod
        except Exception:
            pass
    return None


def _rarity_set_float(mod: object | None, value: float) -> int:
    if mod is None:
        return 0
    writes = 0
    value = max(0.0, min(1.0, float(value)))
    for name in ("Value", "CurrentValue", "Current", "BaseValue", "InitialValue", "Base"):
        try:
            if hasattr(mod, name):
                setattr(mod, name, value)
                writes += 1
        except Exception:
            pass
    for name in ("SetValue", "SetBaseValue", "SetCurrentValue"):
        try:
            fn = getattr(mod, name, None)
            if callable(fn):
                fn(value)
                writes += 1
        except Exception:
            pass
    return writes


def _rarity_apply_current() -> dict[str, Any]:
    state = _rarity_state_for_gamestate(_rarity_current_gamestate())
    if state is None:
        return {"ok": False, "message": "No GameState.RarityState found yet. Load into a world and try again."}
    writes = 0
    parts: list[str] = []
    for key, label, fields in RARITY_ROWS:
        target = max(0.0, min(1.0, float(_rarity_weights.get(key, 1.0))))
        writes += _rarity_set_float(_rarity_get_modifier(state, fields), target)
        parts.append(f"{label}={int(round(target * 100.0))}%")
    return {"ok": True, "message": "Rarity drop weights applied: " + ", ".join(parts) + f". Writes: {writes}."}


def rarity_apply(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    for key, _label, _fields in RARITY_ROWS:
        try:
            if key in payload:
                _rarity_weights[key] = max(0.0, min(1.0, float(payload[key])))
            pct_key = f"rarity_{key}_percent"
            if pct_key in payload:
                _rarity_weights[key] = max(0.0, min(1.0, float(payload[pct_key]) / 100.0))
        except Exception:
            return {"ok": False, "message": f"Rarity value for {key} must be numeric."}
    return _rarity_apply_current()


def rarity_reset() -> dict[str, Any]:
    for key, _label, _fields in RARITY_ROWS:
        _rarity_weights[key] = 1.0
    return _rarity_apply_current()


def rarity_only(allowed_key: object) -> dict[str, Any]:
    allowed = str(allowed_key or "").strip().lower()
    valid = {key for key, _label, _fields in RARITY_ROWS}
    if allowed not in valid:
        return {"ok": False, "message": f"Unsupported rarity key: {allowed_key}"}
    for key, _label, _fields in RARITY_ROWS:
        _rarity_weights[key] = 1.0 if key == allowed else 0.0
    return _rarity_apply_current()


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
        return None
    try:
        count = len(pa)
    except Exception:
        return None
    if host_ps is None:
        return None
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
    return None


def _non_host_party_player_indices() -> list[int]:
    all_indices = [int(idx) for idx, _name in _players()]
    host_idx = _host_player_index_value()
    if host_idx is None:
        return []
    return [idx for idx in all_indices if idx != host_idx]


def _serial_delivery_count_note(parsed_count: int | None, resolved_count: int) -> str:
    if parsed_count is None or int(parsed_count) == int(resolved_count):
        return ""
    return f" Parsed {int(parsed_count)} input row(s), resolved {int(resolved_count)} deliverable serial(s)."


def _deliver_serials_with_target(serials: list[str], mode: str, parsed_count: int | None = None) -> dict[str, Any]:
    if not serials:
        return {"ok": False, "message": "No valid serials to deliver."}
    mode_key = str(mode or "selected").lower().strip()
    if mode_key in ("non_host", "all_non_host"):
        mode_key = "nonhost"
    if mode_key not in ("selected", "all", "nonhost"):
        mode_key = "selected"
    total_serials = len(serials)
    chunks = serial_rewards._serial_delivery_chunks(serials, mode_key)
    max_per_chunk = serial_rewards._serial_delivery_max_serials_per_chunk(mode_key)
    delay = serial_rewards._serial_delivery_post_open_delay(mode_key)
    estimated_wait = max(0.0, (len(chunks) - 1) * float(delay or 0.0)) if chunks else 0.0
    split_note = (
        f" Submitting {total_serials} serial(s) in {len(chunks)} chunk(s), "
        f"max {max_per_chunk} serial(s) per chunk, delay {delay:.2f}s."
    ) if chunks else ""
    if estimated_wait >= 10.0:
        split_note += f" Large delivery queued; estimated throttle wait is about {estimated_wait:.0f}s."
    count_note = _serial_delivery_count_note(parsed_count, total_serials)
    try:
        if mode_key == "all":
            indices = [int(idx) for idx, _name in _players()]
            if not indices:
                return {"ok": False, "message": "No party players found."}
            serial_rewards._do_give_serial_to_player_indices(serials, indices, scope_label="all party players", mode=mode_key)
            return {
                "ok": True,
                "message": f"Requested {total_serials} serial(s) for all party players ({len(indices)} target(s)).{split_note}{count_note}",
            }
        if mode_key == "nonhost":
            indices = _non_host_party_player_indices()
            if not indices:
                return {"ok": False, "message": "No non-host party players found."}
            serial_rewards._do_give_serial_to_player_indices(serials, indices, scope_label="all non-host players", mode=mode_key)
            return {
                "ok": True,
                "message": f"Requested {total_serials} serial(s) for all non-host players ({len(indices)} target(s)).{split_note}{count_note}",
            }
        idx = get_selected_player_index()
        name = get_selected_player_name() or "selected player"
        if idx is None:
            return {"ok": False, "message": "No party player selected."}
        serial_rewards._do_give_serial_to_player_indices(serials, [idx], scope_label=f"selected player {idx} {name}", mode=mode_key)
        return {"ok": True, "message": f"Requested {total_serials} serial(s) for {name}.{split_note}{count_note}"}
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
    result = _deliver_serials_with_target(serials, mode, parsed_count=len(expanded))
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
