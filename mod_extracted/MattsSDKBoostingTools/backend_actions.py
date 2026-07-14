"""Bridge-safe backend actions for Matt's SDK Boosting Tools.

This module must not import the optional in-game UI. It owns the small bit of
external-bridge state needed by headless bridge actions.
"""
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import pkgutil
import re
import sys
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
_DEV_SPAWNER_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9_./:-]+$")
_DEV_SPAWNER_SAFE_STATE_LIST = re.compile(r"^[A-Za-z0-9_,./:-]+$")
_ASD_COMMAND_ATTRS = {
    "ASD_status": "_cmd_status",
    "ASD_clear": "_cmd_clear",
    "ASD_activate_last": "_cmd_activate_last",
    "ASD_scriptdump": "_cmd_scriptdump",
    "ASD_cache_status": "_cmd_cache_status",
    "ASD_targets": "_cmd_targets",
    "ASD_spawn": "_cmd_spawn",
    "ASD_lostloot": "_cmd_lostloot",
    "ASD_spawnai": "_cmd_spawnai",
    "ASD_probeai": "_cmd_probeai",
    "ASD_cache": "_cmd_cache",
    "ASD_barrellogo": "_cmd_barrellogo",
    "ASD_logo_options": "_cmd_logo_options",
    "ASD_spawnerdiag": "_cmd_spawnerdiag",
}


def _clamp_int(value: object, min_value: int, max_value: int) -> int:
    return max(int(min_value), min(int(value), int(max_value)))


def _clamp_float(value: object, min_value: float, max_value: float, default: float) -> float:
    try:
        fvalue = float(str(value).replace(",", "").strip())
    except Exception:
        fvalue = default
    return max(min_value, min(max_value, fvalue))


def _dev_spawner_bool(value: object) -> bool:
    return str(value or "").strip().lower() in ("1", "true", "yes", "on", "checked")


def _dev_spawner_token(value: object, field_name: str, *, required: bool = False) -> str:
    text = str(value or "").strip()
    if not text:
        if required:
            raise ValueError(f"{field_name} is required.")
        return ""
    if not _DEV_SPAWNER_SAFE_TOKEN.match(text):
        raise ValueError(f"{field_name} contains unsupported characters for a dev-spawner console argument.")
    return text


def _dev_spawner_state_list(value: object, field_name: str) -> str:
    text = str(value or "").strip().replace(" ", "")
    if not text:
        return ""
    if not _DEV_SPAWNER_SAFE_STATE_LIST.match(text):
        raise ValueError(f"{field_name} contains unsupported characters for a dev-spawner state list.")
    return text


def _dev_spawner_quoted_text(value: object) -> str:
    text = str(value or "").replace("\r\n", "|").replace("\r", "|").replace("\n", "|").strip()
    # Keep this as a single ASD argument. Semicolons are removed to avoid accidental console chaining.
    text = text.replace(";", ",").replace('"', "'")
    return f'"{text}"'


def _run_actor_script_deployer_command(command_line: str) -> tuple[bool, str]:
    """Run an ActorScriptDeployer mods_base command without going through Unreal console text."""
    command_name = str(command_line or "").split(None, 1)[0]
    attr_name = _ASD_COMMAND_ATTRS.get(command_name)
    if not attr_name:
        return False, f"No ActorScriptDeployer mapping for {command_name!r}."
    try:
        asd = importlib.import_module("ActorScriptDeployer")
    except Exception as exc:
        return False, f"ActorScriptDeployer import failed: {exc!r}"
    command_obj = getattr(asd, attr_name, None)
    handle = getattr(command_obj, "_handle_cmd", None)
    if not callable(handle):
        return False, f"ActorScriptDeployer command object {attr_name!r} is unavailable."
    handle(command_line, len(command_name))
    return True, "ActorScriptDeployer command object"


def _actor_script_deployer_command(attr_name: str) -> tuple[Any | None, str]:
    try:
        asd = importlib.import_module("ActorScriptDeployer")
    except Exception as exc:
        return None, f"ActorScriptDeployer import failed: {exc!r}"
    command_obj = getattr(asd, attr_name, None)
    if not callable(command_obj):
        return None, f"ActorScriptDeployer command object {attr_name!r} is unavailable."
    return command_obj, "ActorScriptDeployer direct command object"


def _install_asd_sdk03_actor_def_patch(asd: Any) -> tuple[bool, str]:
    if getattr(asd, "_msbt_sdk03_actor_def_patch", False):
        return True, "ActorScriptDeployer SDK 03 actor-def pointer patch already installed"

    original = getattr(asd, "_make_actor_def_shell", None)
    if not callable(original):
        return True, "ActorScriptDeployer actor-def shell helper not present; SDK 03 patch not needed"

    def _make_actor_def_shell_sdk03(actor_def: str) -> Any:
        name = str(actor_def or "").strip()
        if not name:
            raise ValueError("ActorScriptDeployer SDK 03 actor-def pointer requires a non-empty actor name.")

        try:
            import unrealsdk as _unrealsdk
        except Exception as exc:
            raise RuntimeError(f"ActorScriptDeployer SDK 03 actor-def pointer could not import unrealsdk: {exc!r}") from exc

        struct = None
        find_object_fn = getattr(asd, "find_object", None)
        if callable(find_object_fn):
            for class_name in ("ScriptStruct", "Object"):
                try:
                    struct = find_object_fn(class_name, "/Script/GbxSpawn.GbxActorDef")
                except Exception:
                    struct = None
                if struct is not None:
                    break

        struct_arg = struct or "/Script/GbxSpawn.GbxActorDef"
        try:
            return _unrealsdk.unreal.FGbxDefPtr(name, struct_arg)
        except Exception as exc:
            raise RuntimeError(
                "ActorScriptDeployer SDK 03 actor-def pointer failed: "
                f"FGbxDefPtr({name!r}, {struct_arg!r}) -> {exc!r}"
            ) from exc

    try:
        setattr(asd, "_msbt_original_make_actor_def_shell", original)
        setattr(asd, "_make_actor_def_shell", _make_actor_def_shell_sdk03)
        setattr(asd, "_msbt_sdk03_actor_def_patch", True)
    except Exception as exc:
        return False, f"ActorScriptDeployer SDK 03 actor-def pointer patch failed: {exc!r}"

    return True, "ActorScriptDeployer SDK 03 actor-def pointer patch installed: FGbxDefPtr(name, GbxActorDef)"


def _capture_asd_logs(asd: Any, callback: Any) -> tuple[list[tuple[str, str]], Exception | None]:
    logs: list[tuple[str, str]] = []
    originals = {
        "_log_info": getattr(asd, "_log_info", None),
        "_log_warn": getattr(asd, "_log_warn", None),
        "_log_error": getattr(asd, "_log_error", None),
    }

    def _wrap(level: str, original: Any) -> Any:
        def _logger(message: str) -> None:
            text = str(message)
            logs.append((level, text))
            if callable(original):
                original(message)

        return _logger

    for attr, original in originals.items():
        level = "info"
        if attr.endswith("warn"):
            level = "warning"
        elif attr.endswith("error"):
            level = "error"
        try:
            setattr(asd, attr, _wrap(level, original))
        except Exception:
            pass

    error: Exception | None = None
    try:
        callback()
    except Exception as exc:
        error = exc
    finally:
        for attr, original in originals.items():
            try:
                setattr(asd, attr, original)
            except Exception:
                pass
    return logs, error


def _parse_asd_spawnai_result(
    *,
    name: str,
    requested_count: int,
    mode: str,
    logs: list[tuple[str, str]],
    error: Exception | None = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "ok": False,
        "message": "",
        "mode": mode,
        "requested_count": int(requested_count),
        "verification_status": "unknown",
        "spawn_verified": None,
        "resolved": None,
        "spawned_count": None,
        "alive_count": None,
        "dead_count": None,
        "total_count": None,
        "actor_names": [],
        "warnings": [],
        "asd_log_lines": [message for _level, message in logs],
    }
    if error is not None:
        result["message"] = f"ActorScriptDeployer ASD_spawnai failed: {error!r}"
        return result

    actor_names: list[str] = []
    warnings: list[str] = [
        message
        for level, message in logs
        if level in ("warning", "error")
        or "did not return an actor" in message
        or "no alive actors" in message
        or "resolved=False" in message
    ]
    count_pattern = re.compile(
        r"ASD_spawnai thin-air actor_def=(?P<actor_def>\S+) resolved=(?P<resolved>True|False).*?"
        r"counts=\(alive=(?P<alive>-?\d+), spawned=(?P<spawned>-?\d+), dead=(?P<dead>-?\d+), total=(?P<total>-?\d+)\) "
        r"actors=(?P<actors>\[.*\])"
    )
    complete_pattern = re.compile(r"ASD_spawnai complete:\s*(?P<actor>.+)$")

    for _level, message in logs:
        count_match = count_pattern.search(message)
        if count_match:
            result["resolved"] = count_match.group("resolved") == "True"
            result["alive_count"] = int(count_match.group("alive"))
            result["spawned_count"] = int(count_match.group("spawned"))
            result["dead_count"] = int(count_match.group("dead"))
            result["total_count"] = int(count_match.group("total"))
            actors_text = count_match.group("actors").strip()
            if actors_text and actors_text != "[]":
                actor_names.append(actors_text)
            continue

        complete_match = complete_pattern.search(message)
        if complete_match:
            actor_names.append(complete_match.group("actor").strip())

    result["warnings"] = warnings
    result["actor_names"] = actor_names

    resolved = result.get("resolved")
    alive_count = result.get("alive_count")
    spawned_count = result.get("spawned_count")
    saw_complete = bool(actor_names)
    no_actor_warning = any(
        "did not return an actor" in warning or "no alive actors" in warning
        for warning in warnings
    )

    if resolved is False:
        result["ok"] = True
        result["verification_status"] = "queued_unverified"
        result["message"] = (
            f"ActorScriptDeployer accepted ASD_spawnai for {name}, but the immediate poll did not verify the actor. "
            "Watch the game world; some ActorScriptDeployer spawns finish after this response."
        )
        return result
    if alive_count == 0 and spawned_count == 0:
        result["ok"] = True
        result["verification_status"] = "queued_unverified"
        result["message"] = (
            f"ActorScriptDeployer accepted ASD_spawnai for {name}, but the immediate poll reported 0 spawned/alive actors. "
            "Watch the game world; some ActorScriptDeployer spawns finish after this response."
        )
        return result
    if no_actor_warning and not saw_complete:
        result["ok"] = True
        result["verification_status"] = "queued_unverified"
        result["message"] = (
            f"ActorScriptDeployer accepted ASD_spawnai for {name}, but did not return an actor immediately. "
            "Watch the game world; some ActorScriptDeployer spawns finish after this response."
        )
        return result
    if saw_complete or (resolved is True and (int(alive_count or 0) > 0 or int(spawned_count or 0) > 0)):
        result["ok"] = True
        result["verification_status"] = "verified_spawned"
        result["spawn_verified"] = True
        result["message"] = f"ActorScriptDeployer spawned {name}."
        return result

    result["verification_status"] = "unknown"
    result["message"] = (
        f"ActorScriptDeployer received ASD_spawnai for {name}, but MSBT could not verify a spawned actor from "
        "the immediate command output."
    )
    return result


def _run_actor_script_deployer_spawnai_like_debug_menu(
    *,
    name: str,
    count: int,
    distance: float,
    spacing: float,
    scale: float,
    z_offset: float,
    extra_loads: list[str],
    direct_only: bool,
) -> dict[str, Any]:
    """Run ActorScriptDeployer's native AI spawn command for standard row spawns."""
    try:
        asd = importlib.import_module("ActorScriptDeployer")
    except Exception as exc:
        return {"ok": False, "message": f"ActorScriptDeployer import failed: {exc!r}", "requested_count": count}

    patch_ok, patch_message = _install_asd_sdk03_actor_def_patch(asd)
    if not patch_ok:
        return {"ok": False, "message": patch_message, "requested_count": count}

    spawnai_fn = getattr(asd, "_cmd_spawnai", None)
    if not callable(spawnai_fn):
        return {
            "ok": False,
            "message": "ActorScriptDeployer command object '_cmd_spawnai' is unavailable.",
            "requested_count": count,
        }
    message = f"ActorScriptDeployer direct command object; {patch_message}"

    def _spawn_first() -> None:
        spawnai_fn(
            argparse.Namespace(
                name=name,
                distance=distance,
                count=count,
                spacing=spacing,
                scale=scale,
                z_offset=z_offset,
                zoffset=z_offset,
                load=list(extra_loads),
                direct_only=direct_only,
            )
        )

    logs, error = _capture_asd_logs(asd, _spawn_first)
    result = _parse_asd_spawnai_result(
        name=name,
        requested_count=count,
        mode=message,
        logs=logs,
        error=error,
    )
    return result


def _module_available(name: str) -> bool:
    try:
        if name in sys.modules:
            return True
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


def _module_version(name: str) -> str:
    try:
        module = sys.modules.get(name) or importlib.import_module(name)
    except Exception:
        return ""
    for attr in ("__version__", "VERSION", "version"):
        try:
            value = getattr(module, attr, "")
        except Exception:
            value = ""
        if value:
            return str(value)
    return ""


def _sdk_diagnostics() -> dict[str, Any]:
    """Lightweight SDK/runtime status for the external bridge.

    Keep this best-effort only: diagnostics should never block startup or action
    processing if an optional module is missing or an SDK build hides version
    metadata.
    """
    try:
        py_version = sys.version.split()[0]
    except Exception:
        py_version = ""
    return {
        "msbt_loaded": True,
        "python_version": py_version,
        "mods_base_version": _module_version("mods_base"),
        "unrealsdk_version": _module_version("unrealsdk"),
        "pyunrealsdk_version": _module_version("pyunrealsdk"),
        "blimgui_available": _module_available("blimgui"),
        "actor_script_deployer_available": _module_available("ActorScriptDeployer"),
    }


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
        "diagnostics": _sdk_diagnostics(),
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
        count = drop_all_shinies(_SHINY_DEFAULT_LEVEL)
        return {"ok": True, "message": f"Drop All Shinies requested for {count} shiny itempool(s)."}
    except Exception as exc:
        return {"ok": False, "message": f"Drop All Shinies failed: {exc!r}"}


def _load_shiny_serials() -> list[str]:
    package_name = __package__ or __name__.rpartition(".")[0]
    blob = pkgutil.get_data(package_name, "shiny_serials.json")
    if blob is None:
        raise RuntimeError("Could not load shiny_serials.json from the mod package data.")
    data = json.loads(blob.decode("utf-8"))
    if not isinstance(data, list):
        raise RuntimeError("shiny_serials.json must contain a JSON list.")

    serials: list[str] = []
    for entry in data:
        if not isinstance(entry, dict):
            continue
        serial = str(entry.get("serial", "")).strip()
        if serial:
            serials.append(serial)
    if not serials:
        raise RuntimeError("No serial values found in shiny_serials.json.")
    return serials


def deliver_shinies(mode: str = "selected") -> dict[str, Any]:
    try:
        raw_serials = _load_shiny_serials()
        serials = serial_rewards._resolve_give_serial_strings(raw_serials)
        return _deliver_serials_with_target(serials, mode, parsed_count=len(raw_serials))
    except Exception as exc:
        return {"ok": False, "message": f"Shiny reward delivery failed: {exc!r}"}


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


def _selected_player_label(idx: int | None, name: str) -> str:
    if name:
        return name
    if idx is not None:
        return f"party index {idx}"
    return "selected player"


def _max_all_for_player_controller(pc: Any) -> tuple[bool, str]:
    ps = getattr(pc, "PlayerState", None)
    ok_bits: list[str] = []
    fail_bits: list[str] = []

    if ps is None:
        fail_bits.append("player state")
    else:
        if player_economy._set_experience_level_via_bp(ps, 0, MAX_PLAYER_LEVEL):
            ok_bits.append(f"player {MAX_PLAYER_LEVEL}")
        else:
            fail_bits.append("player level")
        if player_economy._set_experience_level_via_bp(ps, 1, MAX_SPEC_LEVEL):
            ok_bits.append(f"spec {MAX_SPEC_LEVEL}")
        else:
            fail_bits.append("spec level")

    currency_aliases = getattr(player_economy, "_CURRENCY_KIND_ALIASES", {})
    for kind in ("cash", "eridium"):
        token = currency_aliases.get(kind)
        if token and player_economy._give_currency_on_pc(pc, token, MAX_WALLET_AMOUNT):
            ok_bits.append(f"{kind} {MAX_WALLET_AMOUNT:,}")
        else:
            fail_bits.append(kind)

    if player_economy._set_max_sdu_points_on_pc(pc):
        ok_bits.append("max SDU")
    else:
        fail_bits.append("max SDU")

    try:
        from .vault_card_boost import max_all_vault_cards_for_pc

        vc_ok, vc_detail = max_all_vault_cards_for_pc(pc)
        if vc_ok:
            ok_bits.append(f"vault cards: {vc_detail[:120]}")
        else:
            fail_bits.append(f"vault cards partial: {vc_detail[:120]}")
    except Exception as exc:
        fail_bits.append(f"vault cards failed: {exc!r}")

    detail = "; ".join(ok_bits)
    if fail_bits:
        if detail:
            detail += "; "
        detail += "failed: " + ", ".join(fail_bits)
    return not fail_bits, detail or "no writes reported"


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
    refresh_players()
    idx = _selected_player_index
    name = _selected_player_name
    if idx is None and not name:
        return {"ok": False, "message": "No party player selected."}
    try:
        pc = _party_controller_for_index(idx)
        label = _selected_player_label(idx, name)
        if pc is None:
            return {
                "ok": False,
                "message": (
                    f"Max All could not resolve a live player controller for {label}. "
                    "Refresh Players and try again."
                ),
            }
        ok, detail = _max_all_for_player_controller(pc)
        return {
            "ok": ok,
            "message": (
                f"Max All {'completed' if ok else 'partially completed'} for {label}: {detail}."
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


def run_dev_spawner_action(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(payload or {})
    direct_dev_spawner_result: dict[str, Any] | None = None
    try:
        if action == "dev_spawner_status":
            cmd = "ASD_status"
        elif action == "dev_spawner_clear":
            cmd = "ASD_clear"
        elif action == "dev_spawner_activate_last":
            cmd = "ASD_activate_last"
        elif action == "dev_spawner_scriptdump":
            cmd = "ASD_scriptdump"
        elif action == "dev_spawner_cache_status":
            cmd = "ASD_cache_status"
        elif action == "dev_spawner_logo_options":
            cmd = "ASD_logo_options"
        elif action == "dev_spawner_spawnerdiag":
            limit = _clamp_int(payload.get("dev_actor_target_limit") or 20, 1, 200)
            distance = _clamp_float(payload.get("dev_actor_distance"), 0.0, 20000.0, 350.0)
            cmd = f"ASD_spawnerdiag --limit {limit} --distance {distance:g}"
        elif action == "dev_spawner_targets":
            name = _dev_spawner_token(payload.get("dev_actor_name"), "Actor/template name", required=True)
            class_name = _dev_spawner_token(payload.get("dev_actor_class"), "Actor class")
            limit = _clamp_int(payload.get("dev_actor_target_limit") or 20, 1, 200)
            parts = ["ASD_targets", name, "--limit", str(limit)]
            if class_name:
                parts.extend(("--class", class_name))
            if _dev_spawner_bool(payload.get("dev_actor_include_non_generated")):
                parts.append("--include-non-generated")
            cmd = " ".join(parts)
        elif action == "dev_spawner_lostloot":
            class_name = _dev_spawner_token(payload.get("dev_actor_class"), "Actor class")
            count = _clamp_int(payload.get("dev_actor_count") or 1, 1, 50)
            distance = _clamp_float(payload.get("dev_actor_distance"), 0.0, 20000.0, 350.0)
            spacing = _clamp_float(payload.get("dev_actor_spacing"), 0.0, 5000.0, 125.0)
            scale = _clamp_float(payload.get("dev_actor_scale"), 0.01, 20.0, 1.0)
            z_offset = _clamp_float(payload.get("dev_actor_z_offset"), -10000.0, 10000.0, -100.0)
            delay = _clamp_float(payload.get("dev_actor_delay"), 0.0, 30.0, 1.0)
            enable_states = _dev_spawner_state_list(payload.get("dev_actor_enable_states"), "Enable states")
            disable_states = _dev_spawner_state_list(payload.get("dev_actor_disable_states"), "Disable states")
            parts = [
                "ASD_lostloot",
                "--count",
                str(count),
                "--distance",
                f"{distance:g}",
                "--spacing",
                f"{spacing:g}",
                "--scale",
                f"{scale:g}",
                "--z-offset",
                f"{z_offset:g}",
                "--delay",
                f"{delay:g}",
            ]
            if class_name:
                parts.extend(("--class", class_name))
            if enable_states:
                parts.extend(("--enable", enable_states))
            if disable_states:
                parts.extend(("--disable", disable_states))
            if _dev_spawner_bool(payload.get("dev_actor_no_activate")):
                parts.append("--no-activate")
            if _dev_spawner_bool(payload.get("dev_actor_include_non_generated")):
                parts.append("--include-non-generated")
            cmd = " ".join(parts)
        elif action == "dev_spawner_spawn":
            name = _dev_spawner_token(payload.get("dev_actor_name"), "Actor/template name", required=True)
            class_name = _dev_spawner_token(payload.get("dev_actor_class"), "Actor class")
            count = _clamp_int(payload.get("dev_actor_count") or 1, 1, 50)
            distance = _clamp_float(payload.get("dev_actor_distance"), 0.0, 20000.0, 350.0)
            spacing = _clamp_float(payload.get("dev_actor_spacing"), 0.0, 5000.0, 125.0)
            scale = _clamp_float(payload.get("dev_actor_scale"), 0.01, 20.0, 1.0)
            z_offset = _clamp_float(payload.get("dev_actor_z_offset"), -10000.0, 10000.0, -100.0)
            delay = _clamp_float(payload.get("dev_actor_delay"), 0.0, 30.0, 1.0)
            enable_states = _dev_spawner_state_list(payload.get("dev_actor_enable_states"), "Enable states")
            disable_states = _dev_spawner_state_list(payload.get("dev_actor_disable_states"), "Disable states")
            parts = [
                "ASD_spawn",
                name,
                "--count",
                str(count),
                "--distance",
                f"{distance:g}",
                "--spacing",
                f"{spacing:g}",
                "--scale",
                f"{scale:g}",
                "--z-offset",
                f"{z_offset:g}",
                "--delay",
                f"{delay:g}",
            ]
            if class_name:
                parts.extend(("--class", class_name))
            if enable_states:
                parts.extend(("--enable", enable_states))
            if disable_states:
                parts.extend(("--disable", disable_states))
            if _dev_spawner_bool(payload.get("dev_actor_no_activate")):
                parts.append("--no-activate")
            if _dev_spawner_bool(payload.get("dev_actor_include_non_generated")):
                parts.append("--include-non-generated")
            cmd = " ".join(parts)
        elif action in ("dev_spawner_spawnai", "dev_spawner_probeai"):
            name = _dev_spawner_token(payload.get("dev_ai_name"), "AI actor-def name", required=True)
            command = "ASD_spawnai" if action == "dev_spawner_spawnai" else "ASD_probeai"
            parts = [command, name]
            extra_loads: list[str] = []
            if action == "dev_spawner_spawnai":
                count = _clamp_int(payload.get("dev_ai_count") or 1, 1, 12)
                distance = _clamp_float(payload.get("dev_ai_distance"), 0.0, 20000.0, 350.0)
                spacing = _clamp_float(payload.get("dev_ai_spacing"), 1.0, 5000.0, 125.0)
                scale = _clamp_float(payload.get("dev_ai_scale"), 0.05, 20.0, 1.0)
                z_offset = _clamp_float(payload.get("dev_ai_z_offset"), -5000.0, 5000.0, 0.0)
                direct_only = _dev_spawner_bool(payload.get("dev_ai_direct_only"))
                parts.extend(
                    (
                        "--count",
                        str(count),
                        "--distance",
                        f"{distance:g}",
                        "--spacing",
                        f"{spacing:g}",
                        "--scale",
                        f"{scale:g}",
                        "--zoffset",
                        f"{z_offset:g}",
                    )
                )
                if direct_only:
                    parts.append("--direct-only")
            load_path = _dev_spawner_token(payload.get("dev_ai_load"), "AI load path")
            if load_path:
                parts.extend(("--load", load_path))
                extra_loads.append(load_path)
            cmd = " ".join(parts)
            if action == "dev_spawner_spawnai":
                direct_dev_spawner_result = _run_actor_script_deployer_spawnai_like_debug_menu(
                    name=name,
                    count=count,
                    distance=distance,
                    spacing=spacing,
                    scale=scale,
                    z_offset=z_offset,
                    extra_loads=extra_loads,
                    direct_only=direct_only,
                )
        elif action == "dev_spawner_cache":
            name = _dev_spawner_token(payload.get("dev_ai_name"), "AI actor-def/cache name", required=True)
            class_name = _dev_spawner_token(payload.get("dev_ai_class"), "AI source class")
            limit = _clamp_int(payload.get("dev_ai_cache_limit") or 10, 1, 100)
            index = _clamp_int(payload.get("dev_ai_cache_index") or 0, 0, 99)
            parts = ["ASD_cache", name, "--index", str(index), "--limit", str(limit)]
            if class_name:
                parts.extend(("--class", class_name))
            cmd = " ".join(parts)
        elif action == "dev_spawner_barrel_logo":
            text = _dev_spawner_quoted_text(payload.get("dev_logo_text"))
            if text == '""':
                return {"ok": False, "message": "Barrel Logo text is required."}
            actor = _dev_spawner_token(payload.get("dev_logo_actor") or "barrel", "Logo actor")
            distance = _clamp_float(payload.get("dev_logo_distance"), 0.0, 30000.0, 2500.0)
            height = _clamp_float(payload.get("dev_logo_height"), 0.0, 10000.0, 750.0)
            spacing = _clamp_float(payload.get("dev_logo_spacing"), 1.0, 1000.0, 70.0)
            scale = _clamp_float(payload.get("dev_logo_scale"), 0.01, 20.0, 0.45)
            parts = [
                "ASD_barrellogo",
                "--text",
                text,
                "--actor",
                actor,
                "--distance",
                f"{distance:g}",
                "--height",
                f"{height:g}",
                "--spacing",
                f"{spacing:g}",
                "--scale",
                f"{scale:g}",
            ]
            if _dev_spawner_bool(payload.get("dev_logo_include_non_generated")):
                parts.append("--include-non-generated")
            cmd = " ".join(parts)
        else:
            return {"ok": False, "message": f"Unsupported dev spawner action: {action}"}

        if direct_dev_spawner_result is not None:
            result = dict(direct_dev_spawner_result)
            result.setdefault("command", cmd)
            result.setdefault("accepted", bool(result.get("asd_log_lines")))
            result.setdefault("message", "ActorScriptDeployer spawn request processed.")
            return result
        else:
            direct_ok, direct_message = _run_actor_script_deployer_command(cmd)
        if direct_ok:
            return {
                "ok": True,
                "message": (
                    f"Sent {cmd.split()[0]} to ActorScriptDeployer. "
                    "The bridge only confirms ASD received the command; check unrealsdk.log for spawn/result details."
                ),
                "command": cmd,
                "mode": direct_message,
            }

        return {
            "ok": False,
            "message": f"ActorScriptDeployer command was unavailable: {direct_message}",
            "command": cmd,
            "mode": "ActorScriptDeployer direct command unavailable",
        }
    except Exception as exc:
        return {"ok": False, "message": f"Dev spawner action failed: {exc!r}"}


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
