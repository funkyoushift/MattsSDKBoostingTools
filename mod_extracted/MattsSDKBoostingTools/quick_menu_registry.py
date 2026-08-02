"""Bridge-safe Quick Menu catalog, validation, and persistence.

This module intentionally has no Unreal, BLImGui, or UI imports. Both the
native UMG menu and the external bridge use it as the single layout source.
"""

from __future__ import annotations

import copy
from typing import Any

from .inventory_capacity import clamp_container_size, load_inventory_settings, save_extra_settings

MAX_PAGES = 5
SLOTS_PER_PAGE = 12
MAX_CUSTOM_LABEL_LEN = 48
SCHEMA_VERSION = 1

ACTION_CATALOG: dict[str, dict[str, Any]] = {
    "max_all": {"basic": "Max All", "aliases": ["MAX", "MaxAll"]},
    "max_currency": {"basic": "Max Currency", "aliases": ["Cash", "MaxCash"]},
    "max_eridium": {"basic": "Max Eridium", "aliases": ["Eridium", "MaxE"]},
    "max_sdu": {"basic": "Max SDU", "aliases": ["SDU"]},
    "max_player_level": {"basic": "Max Level", "aliases": ["Lvl60", "Level"]},
    "max_spec_level": {"basic": "Max Spec", "aliases": ["Spec"]},
    "give_currency": {"basic": "Give Currency", "aliases": ["Currency"]},
    "set_level": {"basic": "Set Level", "aliases": ["Level"]},
    "open_golden_chest": {"basic": "Open Chest", "aliases": ["OpenGC", "Chest"]},
    "close_golden_chest": {"basic": "Close Chest", "aliases": ["CloseGC"]},
    "open_bank": {"basic": "Open Bank", "aliases": ["Bank"]},
    "drop_all_shinies": {"basic": "Drop Shinies", "aliases": ["Shinies", "DropAll"]},
    "shiny_selected": {"basic": "Shinies Selected", "aliases": ["Shiny Sel"]},
    "shiny_all": {"basic": "Shinies All", "aliases": ["Shiny All"]},
    "shiny_nonhost": {"basic": "Shinies Non-Host", "aliases": ["Shiny NH"]},
    "repeat_last_drop": {"basic": "Repeat Last Drop", "aliases": ["Redo Drop", "RLD"]},
    "uvh_boost_all": {"basic": "UVH Boost All", "aliases": ["UVH"]},
    "uvh_boost_cancel": {"basic": "Cancel UVH", "aliases": ["UVH Cancel"]},
    "toggle_debug_cam": {"basic": "Toggle Debug Cam", "aliases": ["Debug Cam"]},
    "teleport_debug_cam": {"basic": "Teleport Debug Cam", "aliases": ["Cam Teleport"]},
    "movement_reset_all": {"basic": "Reset Movement", "aliases": ["Move Reset"]},
    "movement_preset_fast": {"basic": "Fast Movement", "aliases": ["Fast"]},
    "movement_preset_veryfast": {"basic": "Very Fast Movement", "aliases": ["Very Fast"]},
    "movement_preset_moon": {"basic": "Moon Movement", "aliases": ["Moon"]},
    "movement_preset_wallwalk": {"basic": "Wall Walk", "aliases": ["WallWalk"]},
    "movement_preset_fastglide": {"basic": "Fast Glide", "aliases": ["Glide"]},
    "movement_toggle_no_target": {"basic": "Toggle No Target", "aliases": ["No Target"]},
    "movement_toggle_noclip": {"basic": "Toggle Noclip", "aliases": ["Noclip"]},
    "movement_players_only": {"basic": "Players Only", "aliases": ["Players"]},
    "movement_delete_ground_items": {"basic": "Clear Ground Loot", "aliases": ["Clear Loot"]},
    "movement_zero_vault": {"basic": "Zero Vault Costs", "aliases": ["Vault0"]},
    "rarity_reset": {"basic": "Reset Rarity", "aliases": ["Rarity Reset"]},
    "rarity_only_legendary": {"basic": "Only Legendary", "aliases": ["Legendary"]},
    "rarity_only_pearlescent": {"basic": "Only Pearlescent", "aliases": ["Pearlescent"]},
    "set_backpack_bank_selected": {"basic": "Inv Selected 1k", "aliases": ["Inv Sel"]},
    "set_backpack_bank_all": {"basic": "Inv All Party 1k", "aliases": ["Inv All"]},
    "kick_player": {"basic": "Kick Selected", "aliases": ["Kick"]},
    "refresh_players": {"basic": "Refresh Players", "aliases": ["Refresh"]},
}

for _tier in range(1, 8):
    ACTION_CATALOG[f"uvh_boost_tier_{_tier}"] = {
        "basic": f"UVH 1-{_tier}",
        "aliases": [f"UVH {_tier}"],
    }

ASSIGNABLE_ACTIONS: tuple[str, ...] = (
    "max_all",
    "max_currency",
    "max_eridium",
    "max_sdu",
    "max_player_level",
    "max_spec_level",
    "give_currency",
    "set_level",
    "open_golden_chest",
    "close_golden_chest",
    "open_bank",
    "drop_all_shinies",
    "shiny_selected",
    "shiny_all",
    "shiny_nonhost",
    "repeat_last_drop",
    "uvh_boost_all",
    "uvh_boost_tier_1",
    "uvh_boost_tier_2",
    "uvh_boost_tier_3",
    "uvh_boost_tier_4",
    "uvh_boost_tier_5",
    "uvh_boost_tier_6",
    "uvh_boost_tier_7",
    "uvh_boost_cancel",
    "toggle_debug_cam",
    "teleport_debug_cam",
    "movement_reset_all",
    "movement_preset_fast",
    "movement_preset_veryfast",
    "movement_preset_moon",
    "movement_preset_wallwalk",
    "movement_preset_fastglide",
    "movement_toggle_no_target",
    "movement_toggle_noclip",
    "movement_players_only",
    "movement_delete_ground_items",
    "movement_zero_vault",
    "rarity_reset",
    "rarity_only_legendary",
    "rarity_only_pearlescent",
    "set_backpack_bank_selected",
    "set_backpack_bank_all",
    "kick_player",
    "refresh_players",
)

# Keep the native modal compact; the external editor exposes the full registry.
NATIVE_PICKER_ACTIONS: tuple[str, ...] = (
    "max_all",
    "max_currency",
    "max_eridium",
    "max_sdu",
    "max_player_level",
    "max_spec_level",
    "open_golden_chest",
    "close_golden_chest",
    "open_bank",
    "drop_all_shinies",
    "shiny_selected",
    "shiny_all",
    "shiny_nonhost",
    "repeat_last_drop",
    "uvh_boost_all",
    "movement_delete_ground_items",
    "movement_zero_vault",
    "set_backpack_bank_selected",
    "set_backpack_bank_all",
    "kick_player",
    "refresh_players",
)

NEEDS_PLAYER_ACTIONS = frozenset({
    "max_all",
    "max_currency",
    "max_eridium",
    "max_sdu",
    "max_player_level",
    "max_spec_level",
    "give_currency",
    "set_level",
    "shiny_selected",
    "kick_player",
    "set_backpack_bank_selected",
})

# Loot-pool and serial payload pinning intentionally remain out of this registry.
ALLOWED_PAYLOAD_KEYS: dict[str, frozenset[str]] = {
    "give_currency": frozenset({"currency_kind", "amount"}),
    "set_level": frozenset({"xp_track", "level"}),
    "set_backpack_bank_selected": frozenset({"backpack_size", "bank_size"}),
    "set_backpack_bank_all": frozenset({"backpack_size", "bank_size"}),
}

DEFAULT_PAGE_0: list[dict[str, Any] | None] = [
    {"action": "max_all", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "max_currency", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "max_eridium", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "max_sdu", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "drop_all_shinies", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "shiny_selected", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "open_golden_chest", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "close_golden_chest", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "open_bank", "label_mode": "basic", "custom_label": "", "payload": {}},
    {"action": "repeat_last_drop", "label_mode": "basic", "custom_label": "", "payload": {}},
    None,
    None,
]

_layout_revision = 0


def get_layout_revision() -> int:
    return int(_layout_revision)


def empty_page() -> list[dict[str, Any] | None]:
    return [None for _ in range(SLOTS_PER_PAGE)]


def default_pages() -> list[list[dict[str, Any] | None]]:
    first = [normalize_slot(slot) for slot in DEFAULT_PAGE_0]
    while len(first) < SLOTS_PER_PAGE:
        first.append(None)
    return [first[:SLOTS_PER_PAGE]] + [empty_page() for _ in range(MAX_PAGES - 1)]


def _safe_int(value: object, fallback: int) -> int:
    try:
        return int(value)
    except Exception:
        return int(fallback)


def sanitize_payload(action: str, raw: object) -> dict[str, Any]:
    source = copy.deepcopy(raw) if isinstance(raw, dict) else {}
    allowed = ALLOWED_PAYLOAD_KEYS.get(action, frozenset())
    result: dict[str, Any] = {}
    for key in allowed:
        if key not in source:
            continue
        if key in ("backpack_size", "bank_size"):
            result[key] = clamp_container_size(source[key], 1000)
        elif key == "currency_kind":
            value = str(source[key] or "cash").strip().lower()
            result[key] = value if value in {"cash", "eridium", "vaultcard1", "vaultcard2", "vaultcard3"} else "cash"
        elif key == "amount":
            result[key] = max(0, min(2147483647, _safe_int(source[key], 0)))
        elif key == "xp_track":
            value = str(source[key] or "player").strip().lower()
            allowed_tracks = {"player", "specialization", "vaultcard_xp_1", "vaultcard_xp_2", "vaultcard_xp_3"}
            result[key] = value if value in allowed_tracks else "player"
        elif key == "level":
            result[key] = max(1, min(9999999, _safe_int(source[key], 60)))
        else:
            result[key] = source[key]
    return result


def _label_mode(action: str, raw_mode: object, custom_label: str) -> str:
    mode = str(raw_mode or "basic").strip().lower()
    if mode == "custom" and custom_label:
        return "custom"
    if mode.startswith("alias"):
        try:
            index = int(mode[5:] or "0")
        except Exception:
            index = -1
        aliases = list(ACTION_CATALOG.get(action, {}).get("aliases") or [])
        if 0 <= index < len(aliases):
            return f"alias{index}"
    return "basic"


def normalize_slot(raw: object) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    action = str(raw.get("action") or "").strip()
    if action not in ACTION_CATALOG:
        return None
    custom_label = str(raw.get("custom_label") or "").strip()[:MAX_CUSTOM_LABEL_LEN]
    return {
        "action": action,
        "label_mode": _label_mode(action, raw.get("label_mode"), custom_label),
        "custom_label": custom_label,
        "payload": sanitize_payload(action, raw.get("payload")),
    }


def validate_slot(raw: object) -> tuple[dict[str, Any] | None, str | None]:
    if raw is None:
        return None, None
    if not isinstance(raw, dict):
        return None, "Slot must be an object or null."
    action = str(raw.get("action") or "").strip()
    if action not in ASSIGNABLE_ACTIONS:
        return None, f"Action is not assignable: {action or '(empty)'}"
    slot = normalize_slot(raw)
    if slot is None:
        return None, f"Invalid Quick Menu slot: {action or '(empty)'}"
    return slot, None


def validate_pages(raw_pages: object) -> tuple[list[list[dict[str, Any] | None]], list[str]]:
    if not isinstance(raw_pages, list):
        return default_pages(), ["pages must be a list."]
    pages: list[list[dict[str, Any] | None]] = []
    errors: list[str] = []
    for page_index in range(MAX_PAGES):
        source = raw_pages[page_index] if page_index < len(raw_pages) else []
        if not isinstance(source, list):
            errors.append(f"Page {page_index + 1} must be a list.")
            source = []
        row = empty_page()
        for slot_index in range(min(SLOTS_PER_PAGE, len(source))):
            slot, error = validate_slot(source[slot_index])
            if error:
                errors.append(f"Page {page_index + 1}, slot {slot_index + 1}: {error}")
            row[slot_index] = slot
        pages.append(row)
    return pages, errors


def sanitize_drop_lock(raw: object) -> dict[str, Any]:
    source = raw if isinstance(raw, dict) else {}
    index = source.get("index")
    if index is not None:
        try:
            index = int(index)
        except Exception:
            index = None
    return {
        "enabled": bool(source.get("enabled", False)),
        "index": index,
        "name": str(source.get("name") or "").strip()[:80],
    }


def _layout_from_raw(raw: object) -> dict[str, Any]:
    source = raw if isinstance(raw, dict) else {}
    pages, _errors = validate_pages(source.get("pages", default_pages()))
    page = max(0, min(MAX_PAGES - 1, _safe_int(source.get("page"), 0)))
    return {
        "page": page,
        "edit_mode": bool(source.get("edit_mode", False)),
        "pages": pages,
        "drop_lock": sanitize_drop_lock(source.get("drop_lock")),
    }


def load_persisted_layout() -> dict[str, Any]:
    settings = load_inventory_settings()
    return _layout_from_raw(settings.get("quick_menu"))


def _save_layout(layout: dict[str, Any]) -> dict[str, Any]:
    global _layout_revision
    save_extra_settings(quick_menu=copy.deepcopy(layout))
    _layout_revision += 1
    return copy.deepcopy(layout)


def set_quick_menu_layout(payload: object) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    if isinstance(source.get("layout"), dict):
        source = source["layout"]
    current = load_persisted_layout()
    pages_source = source.get("pages", current["pages"])
    pages, errors = validate_pages(pages_source)
    if errors:
        return {"ok": False, "message": errors[0], "errors": errors}
    layout = {
        "page": max(0, min(MAX_PAGES - 1, _safe_int(source.get("page"), current["page"]))),
        "edit_mode": bool(source.get("edit_mode", current["edit_mode"])),
        "pages": pages,
        "drop_lock": sanitize_drop_lock(source.get("drop_lock", current["drop_lock"])),
    }
    _save_layout(layout)
    return {"ok": True, "message": "Quick Menu layout saved.", "layout": layout}


def assign_quick_menu_slot(payload: object) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    page = _safe_int(source.get("page"), -1)
    slot_index = _safe_int(source.get("slot"), -1)
    if not (0 <= page < MAX_PAGES):
        return {"ok": False, "message": f"Page must be 0 to {MAX_PAGES - 1}."}
    if not (0 <= slot_index < SLOTS_PER_PAGE):
        return {"ok": False, "message": f"Slot must be 0 to {SLOTS_PER_PAGE - 1}."}

    layout = load_persisted_layout()
    action = str(source.get("action") or "").strip()
    if not action:
        new_slot = None
    else:
        raw_slot = {
            "action": action,
            "label_mode": source.get("label_mode", "basic"),
            "custom_label": source.get("custom_label", ""),
            "payload": source.get("command_payload", source.get("payload", {})),
        }
        new_slot, error = validate_slot(raw_slot)
        if error:
            return {"ok": False, "message": error}
    layout["pages"][page][slot_index] = new_slot
    layout["page"] = page
    _save_layout(layout)
    return {
        "ok": True,
        "message": f"Quick Menu page {page + 1}, slot {slot_index + 1} updated.",
        "layout": layout,
        "slot": copy.deepcopy(new_slot),
    }


def clear_quick_menu_page(payload: object) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}
    page = _safe_int(source.get("page"), -1)
    if not (0 <= page < MAX_PAGES):
        return {"ok": False, "message": f"Page must be 0 to {MAX_PAGES - 1}."}
    layout = load_persisted_layout()
    layout["pages"][page] = empty_page()
    layout["page"] = page
    _save_layout(layout)
    return {
        "ok": True,
        "message": f"Quick Menu page {page + 1} cleared.",
        "layout": layout,
    }


def slot_label(slot: dict[str, Any] | None) -> str:
    if not slot:
        return ""
    action = str(slot.get("action") or "")
    catalog = ACTION_CATALOG.get(action, {})
    basic = str(catalog.get("basic") or action)
    custom = str(slot.get("custom_label") or "").strip()
    mode = str(slot.get("label_mode") or "basic")
    if mode == "custom" and custom:
        return custom
    if mode.startswith("alias"):
        try:
            index = int(mode[5:] or "0")
        except Exception:
            index = -1
        aliases = list(catalog.get("aliases") or [])
        if 0 <= index < len(aliases):
            return str(aliases[index])
    return basic


def cycle_slot_label(slot: dict[str, Any]) -> None:
    action = str(slot.get("action") or "")
    aliases = list(ACTION_CATALOG.get(action, {}).get("aliases") or [])
    custom = str(slot.get("custom_label") or "").strip()
    options = ["basic"] + [f"alias{i}" for i in range(len(aliases))]
    if custom:
        options.append("custom")
    mode = str(slot.get("label_mode") or "basic")
    try:
        current = options.index(mode)
    except ValueError:
        current = 0
    slot["label_mode"] = options[(current + 1) % len(options)]


def get_quick_menu_snapshot() -> dict[str, Any]:
    catalog: dict[str, Any] = {}
    for action, metadata in ACTION_CATALOG.items():
        entry = copy.deepcopy(metadata)
        entry["assignable"] = action in ASSIGNABLE_ACTIONS
        entry["needs_player"] = action in NEEDS_PLAYER_ACTIONS
        entry["payload_keys"] = sorted(ALLOWED_PAYLOAD_KEYS.get(action, frozenset()))
        catalog[action] = entry
    return {
        "ok": True,
        "version": SCHEMA_VERSION,
        "revision": get_layout_revision(),
        "limits": {"max_pages": MAX_PAGES, "slots_per_page": SLOTS_PER_PAGE},
        "catalog": catalog,
        "assignable_actions": list(ASSIGNABLE_ACTIONS),
        "layout": load_persisted_layout(),
    }
