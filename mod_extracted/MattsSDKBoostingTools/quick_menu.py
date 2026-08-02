"""Thin native-UMG Quick Menu for Matt's SDK Boosting Tools.

UIDevelopmentShowcase is optional reference only — this module does not import it.
Actions go through backend_actions so the external bridge stays BLImGui-independent.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

import unrealsdk
from mods_base import command, get_pc, keybind
from unrealsdk import logging
from unrealsdk.hooks import Type

from . import backend_actions
from .inventory_capacity import load_inventory_settings, save_extra_settings

PREFIX = "[Matts SDK Boosting Tools | QuickMenu]"
TICK_PATH = "/Script/Engine.CameraModifier:BlueprintModifyCamera"
HOOK_ID = "matts_sdk_boosting_tools_quick_menu_tick_v1"
DESIGN_W = 1920.0
DESIGN_H = 1080.0
VIEWPORT_Z = 999996
MAX_PAGES = 5
SLOTS_PER_PAGE = 12
GRID_COLS = 4
GRID_ROWS = 3

# Catalog: action id -> basic label + short aliases for customizable labels.
ACTION_CATALOG: dict[str, dict[str, Any]] = {
    "max_all": {"basic": "Max All", "aliases": ["MAX", "MaxAll"]},
    "max_currency": {"basic": "Max Currency", "aliases": ["Cash", "MaxCash"]},
    "max_eridium": {"basic": "Max Eridium", "aliases": ["Eridium", "MaxE"]},
    "max_sdu": {"basic": "Max SDU", "aliases": ["SDU"]},
    "max_player_level": {"basic": "Max Level", "aliases": ["Lvl60", "Level"]},
    "max_spec_level": {"basic": "Max Spec", "aliases": ["Spec"]},
    "open_golden_chest": {"basic": "Open Chest", "aliases": ["OpenGC", "Chest"]},
    "close_golden_chest": {"basic": "Close Chest", "aliases": ["CloseGC"]},
    "open_bank": {"basic": "Open Bank", "aliases": ["Bank"]},
    "drop_all_shinies": {"basic": "Drop Shinies", "aliases": ["Shinies", "DropAll"]},
    "shiny_selected": {"basic": "Shinies Selected", "aliases": ["Shiny Sel"]},
    "shiny_all": {"basic": "Shinies All", "aliases": ["Shiny All"]},
    "shiny_nonhost": {"basic": "Shinies Non-Host", "aliases": ["Shiny NH"]},
    "repeat_last_drop": {"basic": "Repeat Last Drop", "aliases": ["Redo Drop", "RLD"]},
    "uvh_boost_all": {"basic": "UVH Boost All", "aliases": ["UVH"]},
    "movement_delete_ground_items": {"basic": "Clear Ground Loot", "aliases": ["Clear Loot"]},
    "kick_player": {"basic": "Kick Selected", "aliases": ["Kick"]},
    "refresh_players": {"basic": "Refresh Players", "aliases": ["Refresh"]},
}

PICKER_ACTIONS: tuple[str, ...] = (
    "max_all",
    "max_currency",
    "max_eridium",
    "max_sdu",
    "max_player_level",
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
    "refresh_players",
)

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


@dataclass
class ButtonRef:
    widget: Any
    action: Callable[[], None]
    label: str
    enabled: bool = True
    was_pressed: bool = False


@dataclass
class InputSnapshot:
    mouse_cursor: bool | None = None
    mouse_over: bool | None = None
    click_events: bool | None = None
    touch_events: bool | None = None
    block_input: bool | None = None


@dataclass
class QuickMenuState:
    is_open: bool = False
    page: int = 0
    edit_mode: bool = False
    modal: str = ""  # "", "player_pick", "action_pick", "label_edit"
    status: str = "Quick Menu ready."
    pages: list[list[dict[str, Any] | None]] = field(default_factory=list)
    selected_slot: int | None = None
    pending_repeat: bool = False
    layout_w: float = DESIGN_W
    layout_h: float = DESIGN_H
    ui_scale: float = 1.0
    overlay: Any = None
    tree: Any = None
    root: Any = None
    menu_canvas: Any = None
    buttons: list[ButtonRef] = field(default_factory=list)
    input_owner: Any = None
    input_snapshot: InputSnapshot = field(default_factory=InputSnapshot)
    last_input_refresh: float = 0.0
    key_escape: bool = False
    started: bool = False


STATE = QuickMenuState()


def _log(message: str) -> None:
    text = f"{PREFIX} {message}"
    try:
        logging.info(text)
    except Exception:
        print(text)
    STATE.status = str(message)[:180]


def live(obj: Any) -> bool:
    if obj is None:
        return False
    try:
        obj._get_address()
        return True
    except Exception:
        return False


def try_call(obj: Any, name: str, *args: Any) -> bool:
    if obj is None:
        return False
    try:
        getattr(obj, name)(*args)
        return True
    except Exception:
        return False


def class_obj(path: str) -> Any:
    return unrealsdk.find_object("Class", path)


def construct(path: str, outer: Any) -> Any:
    cls = class_obj(path)
    if cls is None:
        raise RuntimeError(f"Unable to resolve class {path}")
    return unrealsdk.construct_object(cls, outer)


def vec2(x: float, y: float) -> Any:
    return unrealsdk.make_struct("Vector2D", X=float(x), Y=float(y))


def color(value: tuple[float, float, float, float]) -> Any:
    r, g, b, a = value
    return unrealsdk.make_struct("LinearColor", R=float(r), G=float(g), B=float(b), A=float(a))


def slate_color(value: tuple[float, float, float, float]) -> Any:
    specified = color(value)
    try:
        return unrealsdk.make_struct("SlateColor", SpecifiedColor=specified, ColorUseRule=0)
    except Exception:
        return specified


def remove_widget(widget: Any) -> None:
    if widget is not None:
        try_call(widget, "RemoveFromParent")


def sx(value: float) -> float:
    return float(value) * (STATE.layout_w / DESIGN_W)


def sy(value: float) -> float:
    return float(value) * (STATE.layout_h / DESIGN_H)


def update_layout_metrics() -> None:
    STATE.layout_w = DESIGN_W
    STATE.layout_h = DESIGN_H
    STATE.ui_scale = 1.0
    try:
        pc = get_pc()
        viewport = getattr(pc, "GetViewportSize", None)
        if callable(viewport):
            size = viewport()
            w = float(getattr(size, "X", 0.0) or 0.0)
            h = float(getattr(size, "Y", 0.0) or 0.0)
            if w > 100 and h > 100:
                STATE.layout_w = w
                STATE.layout_h = h
                STATE.ui_scale = min(w / DESIGN_W, h / DESIGN_H)
    except Exception:
        pass


def _empty_page() -> list[dict[str, Any] | None]:
    return [None for _ in range(SLOTS_PER_PAGE)]


def _normalize_slot(raw: object) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    action = str(raw.get("action") or "").strip()
    if not action:
        return None
    label_mode = str(raw.get("label_mode") or "basic").strip() or "basic"
    custom_label = str(raw.get("custom_label") or "").strip()
    payload = raw.get("payload") if isinstance(raw.get("payload"), dict) else {}
    return {
        "action": action,
        "label_mode": label_mode,
        "custom_label": custom_label,
        "payload": dict(payload),
    }


def _default_pages() -> list[list[dict[str, Any] | None]]:
    pages: list[list[dict[str, Any] | None]] = []
    first = [_normalize_slot(slot) for slot in DEFAULT_PAGE_0]
    while len(first) < SLOTS_PER_PAGE:
        first.append(None)
    pages.append(first[:SLOTS_PER_PAGE])
    for _ in range(MAX_PAGES - 1):
        pages.append(_empty_page())
    return pages


def load_layout() -> None:
    settings = load_inventory_settings()
    raw = settings.get("quick_menu")
    pages = _default_pages()
    page = 0
    edit_mode = False
    if isinstance(raw, dict):
        page = max(0, min(MAX_PAGES - 1, int(raw.get("page", 0) or 0)))
        edit_mode = bool(raw.get("edit_mode", False))
        raw_pages = raw.get("pages")
        if isinstance(raw_pages, list) and raw_pages:
            pages = []
            for idx in range(MAX_PAGES):
                src = raw_pages[idx] if idx < len(raw_pages) else []
                row = _empty_page()
                if isinstance(src, list):
                    for slot_i in range(min(SLOTS_PER_PAGE, len(src))):
                        row[slot_i] = _normalize_slot(src[slot_i])
                pages.append(row)
    STATE.pages = pages
    STATE.page = page
    STATE.edit_mode = edit_mode
    lock = backend_actions.get_drop_player_lock()
    if isinstance(raw, dict) and "drop_lock" in raw and isinstance(raw.get("drop_lock"), dict):
        drop_lock = raw["drop_lock"]
        if drop_lock.get("enabled"):
            backend_actions.set_drop_player_lock(True, drop_lock.get("index", drop_lock.get("name")))
        elif lock.get("enabled") and not drop_lock.get("enabled"):
            backend_actions.set_drop_player_lock(False)


def save_layout() -> None:
    lock = backend_actions.get_drop_player_lock()
    payload = {
        "page": int(STATE.page),
        "edit_mode": bool(STATE.edit_mode),
        "pages": STATE.pages,
        "drop_lock": {
            "enabled": bool(lock.get("enabled")),
            "index": lock.get("index"),
            "name": lock.get("name") or "",
        },
    }
    try:
        save_extra_settings(quick_menu=payload)
    except Exception as exc:
        _log(f"Could not save Quick Menu layout: {exc!r}")


def slot_label(slot: dict[str, Any] | None) -> str:
    if not slot:
        return ""
    action = str(slot.get("action") or "")
    catalog = ACTION_CATALOG.get(action, {})
    basic = str(catalog.get("basic") or action)
    mode = str(slot.get("label_mode") or "basic")
    custom = str(slot.get("custom_label") or "").strip()
    if mode == "custom" and custom:
        return custom
    if mode.startswith("alias"):
        try:
            idx = int(mode.replace("alias", "") or "0")
        except Exception:
            idx = 0
        aliases = list(catalog.get("aliases") or [])
        if aliases:
            return str(aliases[idx % len(aliases)])
    return basic


def cycle_slot_label(slot: dict[str, Any]) -> None:
    action = str(slot.get("action") or "")
    catalog = ACTION_CATALOG.get(action, {})
    aliases = list(catalog.get("aliases") or [])
    mode = str(slot.get("label_mode") or "basic")
    custom = str(slot.get("custom_label") or "").strip()
    options = ["basic"]
    options.extend(f"alias{i}" for i in range(len(aliases)))
    if custom:
        options.append("custom")
    try:
        current = options.index(mode if mode in options else "basic")
    except ValueError:
        current = 0
    slot["label_mode"] = options[(current + 1) % len(options)]


class NativeUMG:
    """Minimal native UMG factory (patterns from UIDevelopmentShowcase reference)."""

    def __init__(self, owner: Any):
        self.owner = owner
        self.tree = owner.WidgetTree

    def widget(self, path: str) -> Any:
        return construct(path, self.tree)

    def add(self, parent: Any, child: Any) -> None:
        if hasattr(parent, "AddChild"):
            parent.AddChild(child)
        else:
            parent.SetContent(child)

    def slot(self, widget: Any, x: float, y: float, w: float, h: float, z: int = 0) -> None:
        slot = getattr(widget, "slot", None)
        if slot is None:
            return
        try_call(slot, "SetPosition", vec2(sx(x), sy(y)))
        try_call(slot, "SetSize", vec2(sx(w), sy(h)))
        try_call(slot, "SetZOrder", int(z))
        try_call(slot, "SetAutoSize", False)

    def border(self, parent: Any, x: float, y: float, w: float, h: float, fill: tuple[float, float, float, float], z: int = 0) -> Any:
        widget = self.widget("/Script/UMG.Border")
        try_call(widget, "SetBrushColor", color(fill))
        try_call(widget, "SetVisibility", 4)
        self.add(parent, widget)
        self.slot(widget, x, y, w, h, z)
        return widget

    def text(
        self,
        parent: Any,
        value: str,
        x: float,
        y: float,
        w: float,
        h: float,
        *,
        scale: float = 0.42,
        z: int = 10,
        center: bool = False,
        tint: tuple[float, float, float, float] = (0.94, 0.97, 1.0, 1.0),
    ) -> Any:
        widget = self.widget("/Script/UMG.TextBlock")
        try_call(widget, "SetText", str(value))
        render_scale = max(0.2, float(scale) * STATE.ui_scale)
        try_call(widget, "SetRenderScale", vec2(render_scale, render_scale))
        try_call(widget, "SetRenderTransformPivot", vec2(0.0, 0.5))
        try_call(widget, "SetJustification", 1 if center else 0)
        try_call(widget, "SetColorAndOpacity", slate_color(tint))
        try_call(widget, "SetVisibility", 4)
        self.add(parent, widget)
        self.slot(widget, x, y, w, h, z)
        return widget

    def button(
        self,
        parent: Any,
        label: str,
        x: float,
        y: float,
        w: float,
        h: float,
        action: Callable[[], None],
        *,
        fill: tuple[float, float, float, float] = (0.16, 0.42, 0.58, 0.94),
        enabled: bool = True,
        z: int = 50,
        scale: float = 0.36,
    ) -> Any:
        base = fill if enabled else (0.35, 0.37, 0.40, 0.90)
        self.border(parent, x, y, w, h, base, z)
        widget = self.widget("/Script/UMG.Button")
        self.add(parent, widget)
        self.slot(widget, x, y, w, h, z + 1)
        try_call(widget, "SetVisibility", 0)
        try_call(widget, "SetIsEnabled", bool(enabled))
        try_call(widget, "SetRenderOpacity", 0.03 if enabled else 0.01)
        self.text(parent, label, x + 4, y + 2, w - 8, h - 4, scale=scale, z=z + 2, center=True)
        STATE.buttons.append(ButtonRef(widget, action, label, enabled, False))
        return widget


def create_overlay() -> Any:
    if live(STATE.overlay) and live(STATE.root):
        return STATE.overlay
    pc = get_pc()
    if pc is None:
        raise RuntimeError("Load into gameplay before opening the Quick Menu")
    update_layout_metrics()
    widget = construct("/Script/UMG.UserWidget", pc)
    widget.WidgetTree = construct("/Script/UMG.WidgetTree", widget)
    root = construct("/Script/UMG.CanvasPanel", widget.WidgetTree)
    widget.WidgetTree.RootWidget = root
    try_call(root, "SetVisibility", 0)
    try_call(root, "SetIsEnabled", True)
    try_call(widget, "SetAlignmentInViewport", vec2(0.0, 0.0))
    try_call(widget, "SetPositionInViewport", vec2(0.0, 0.0), False)
    try_call(widget, "SetDesiredSizeInViewport", vec2(STATE.layout_w, STATE.layout_h))
    try_call(widget, "AddToViewport", VIEWPORT_Z)
    try_call(widget, "SetVisibility", 0)
    try_call(widget, "ForceLayoutPrepass")
    STATE.overlay, STATE.tree, STATE.root = widget, widget.WidgetTree, root
    return widget


def reset_canvas() -> tuple[NativeUMG, Any]:
    overlay = create_overlay()
    update_layout_metrics()
    try_call(overlay, "SetDesiredSizeInViewport", vec2(STATE.layout_w, STATE.layout_h))
    factory = NativeUMG(overlay)
    remove_widget(STATE.menu_canvas)
    STATE.buttons.clear()
    canvas = factory.widget("/Script/UMG.CanvasPanel")
    try_call(canvas, "SetVisibility", 0)
    try_call(canvas, "SetIsEnabled", True)
    factory.add(STATE.root, canvas)
    factory.slot(canvas, 0, 0, DESIGN_W, DESIGN_H, 1)
    STATE.menu_canvas = canvas
    return factory, canvas


def apply_input_mode() -> None:
    pc = get_pc()
    if pc is None or not live(STATE.overlay):
        return
    try:
        lib = class_obj("/Script/UMG.WidgetBlueprintLibrary").ClassDefaultObject
        if not try_call(lib, "SetInputMode_GameAndUIEx", pc, STATE.overlay, 0, False, False):
            try_call(lib, "SetInputMode_GameAndUI", pc, STATE.overlay, False, False)
    except Exception:
        pass


def capture_input() -> None:
    pc = get_pc()
    if pc is None:
        return
    if not live(STATE.input_owner):
        snap = InputSnapshot()
        for state_name, attr in (
            ("mouse_cursor", "bShowMouseCursor"),
            ("mouse_over", "bEnableMouseOverEvents"),
            ("click_events", "bEnableClickEvents"),
            ("touch_events", "bEnableTouchEvents"),
            ("block_input", "bBlockInput"),
        ):
            try:
                setattr(snap, state_name, bool(getattr(pc, attr)))
            except Exception:
                pass
        STATE.input_snapshot = snap
        STATE.input_owner = pc
    for attr, value in (
        ("bShowMouseCursor", True),
        ("bEnableMouseOverEvents", True),
        ("bEnableClickEvents", True),
        ("bEnableTouchEvents", True),
        ("bBlockInput", True),
    ):
        try:
            setattr(pc, attr, value)
        except Exception:
            pass
    apply_input_mode()
    STATE.last_input_refresh = time.monotonic()


def restore_input() -> None:
    pc = STATE.input_owner if live(STATE.input_owner) else get_pc()
    if pc is None:
        STATE.input_owner = None
        return
    try:
        lib = class_obj("/Script/UMG.WidgetBlueprintLibrary").ClassDefaultObject
        try_call(lib, "ClearAllUserFocus", pc)
        if not try_call(lib, "SetInputMode_GameOnly", pc, True):
            try_call(lib, "SetInputMode_GameOnly", pc)
        try_call(lib, "SetFocusToGameViewport")
    except Exception:
        pass
    snap = STATE.input_snapshot
    for attr, value, fallback in (
        ("bShowMouseCursor", snap.mouse_cursor, False),
        ("bEnableMouseOverEvents", snap.mouse_over, False),
        ("bEnableClickEvents", snap.click_events, False),
        ("bEnableTouchEvents", snap.touch_events, False),
        ("bBlockInput", snap.block_input, False),
    ):
        try:
            setattr(pc, attr, fallback if value is None else bool(value))
        except Exception:
            pass
    STATE.input_owner = None
    STATE.input_snapshot = InputSnapshot()


def _set_status_from_result(result: dict[str, Any] | None) -> None:
    if not isinstance(result, dict):
        return
    message = str(result.get("message") or "")
    if message:
        _log(message)


def _run_action(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    catalog = ACTION_CATALOG.get(action, {})
    body = dict(payload or {})
    body.setdefault("_label", str(catalog.get("basic") or action))
    result = backend_actions.run_quick_menu_action(action, body, record=True)
    _set_status_from_result(result)
    return result


def _first_empty_slot(page: int | None = None) -> tuple[int, int] | None:
    page_i = STATE.page if page is None else int(page)
    slots = STATE.pages[page_i]
    for idx, slot in enumerate(slots):
        if slot is None:
            return page_i, idx
    return None


def pin_last_command(slot_index: int | None = None) -> None:
    command = backend_actions.get_last_command()
    if command is None:
        _log("No last command to pin.")
        return
    action = str(command.get("action") or "").strip()
    if not action:
        _log("Last command has no action id.")
        return
    target_page = STATE.page
    target_slot = slot_index
    if target_slot is None:
        if STATE.selected_slot is not None:
            target_slot = STATE.selected_slot
        else:
            found = _first_empty_slot(target_page)
            if found is None:
                _log("No empty slot on this page. Select a slot in Edit mode.")
                return
            target_page, target_slot = found
    label = str(command.get("label") or ACTION_CATALOG.get(action, {}).get("basic") or action)
    STATE.pages[target_page][int(target_slot)] = {
        "action": action,
        "label_mode": "custom" if label else "basic",
        "custom_label": label if label else "",
        "payload": dict(command.get("payload") or {}),
    }
    # Prefer basic catalog label when action is known.
    if action in ACTION_CATALOG:
        STATE.pages[target_page][int(target_slot)]["label_mode"] = "basic"
        STATE.pages[target_page][int(target_slot)]["custom_label"] = ""
    save_layout()
    _log(f"Pinned '{slot_label(STATE.pages[target_page][int(target_slot)])}' to page {target_page + 1} slot {int(target_slot) + 1}.")
    rebuild_ui()


def _begin_player_pick_for_repeat() -> None:
    STATE.modal = "player_pick"
    STATE.pending_repeat = True
    rebuild_ui()


def _finish_repeat_for_player(index: int, name: str) -> None:
    STATE.modal = ""
    STATE.pending_repeat = False
    result = backend_actions.repeat_last_drop(f"{index}|{name}" if name else index)
    _set_status_from_result(result)
    rebuild_ui()


def activate_slot(slot_index: int) -> None:
    slots = STATE.pages[STATE.page]
    if slot_index < 0 or slot_index >= len(slots):
        return
    slot = slots[slot_index]
    if STATE.edit_mode:
        STATE.selected_slot = slot_index
        if slot is None:
            STATE.modal = "action_pick"
        else:
            STATE.modal = "label_edit"
        rebuild_ui()
        return

    if slot is None:
        _log("Empty slot. Enable Edit to assign an action, or use Pin Last Command.")
        return

    action = str(slot.get("action") or "")
    payload = dict(slot.get("payload") or {})
    if action == "repeat_last_drop":
        drop = backend_actions.get_last_drop()
        if drop is None:
            _log("No last drop to repeat.")
            return
        if bool(drop.get("needs_player")) and not backend_actions.get_drop_player_lock().get("enabled"):
            _begin_player_pick_for_repeat()
            return
        result = backend_actions.repeat_last_drop()
        if result.get("needs_player"):
            _begin_player_pick_for_repeat()
            return
        _set_status_from_result(result)
        rebuild_ui()
        return

    result = _run_action(action, payload)
    if result.get("needs_player"):
        _begin_player_pick_for_repeat()
        return
    rebuild_ui()


def clear_selected_slot() -> None:
    if STATE.selected_slot is None:
        return
    STATE.pages[STATE.page][STATE.selected_slot] = None
    STATE.modal = ""
    save_layout()
    _log(f"Cleared slot {STATE.selected_slot + 1}.")
    rebuild_ui()


def assign_action_to_selected(action: str) -> None:
    if STATE.selected_slot is None:
        return
    action_id = str(action or "").strip()
    if action_id not in ACTION_CATALOG and action_id != "repeat_last_drop":
        _log(f"Unknown action: {action_id}")
        return
    STATE.pages[STATE.page][STATE.selected_slot] = {
        "action": action_id,
        "label_mode": "basic",
        "custom_label": "",
        "payload": {},
    }
    STATE.modal = ""
    save_layout()
    _log(f"Assigned {slot_label(STATE.pages[STATE.page][STATE.selected_slot])} to slot {STATE.selected_slot + 1}.")
    rebuild_ui()


def toggle_drop_lock() -> None:
    lock = backend_actions.get_drop_player_lock()
    if lock.get("enabled"):
        result = backend_actions.set_drop_player_lock(False)
    else:
        players = backend_actions.refresh_players()
        if not players:
            _log("No party players to lock.")
            return
        # Prefer currently selected; otherwise open picker to choose lock target.
        if backend_actions.get_selected_player_index() is None:
            STATE.modal = "player_pick"
            STATE.pending_repeat = False
            rebuild_ui()
            _log("Pick a player to lock for repeat-last-drop.")
            return
        result = backend_actions.set_drop_player_lock(True)
    _set_status_from_result(result)
    save_layout()
    rebuild_ui()


def _lock_player_from_pick(index: int, name: str) -> None:
    result = backend_actions.set_drop_player_lock(True, f"{index}|{name}" if name else index)
    STATE.modal = ""
    _set_status_from_result(result)
    save_layout()
    rebuild_ui()


def rebuild_ui() -> None:
    if not STATE.is_open:
        return
    factory, root = reset_canvas()

    # Dim backdrop + panel
    factory.border(root, 0, 0, DESIGN_W, DESIGN_H, (0.02, 0.03, 0.05, 0.55), 1)
    factory.border(root, 220, 90, 1480, 900, (0.07, 0.10, 0.14, 0.96), 2)
    factory.border(root, 220, 90, 1480, 64, (0.12, 0.28, 0.38, 0.98), 3)
    factory.text(root, "MSBT Quick Menu", 240, 102, 700, 40, scale=0.58, z=4)
    mode = "EDIT" if STATE.edit_mode else "RUN"
    lock = backend_actions.get_drop_player_lock()
    lock_txt = f"Lock: {lock.get('name') or 'ON'}" if lock.get("enabled") else "Lock: OFF"
    factory.text(root, f"{mode}  |  Page {STATE.page + 1}/{MAX_PAGES}  |  {lock_txt}", 960, 110, 520, 36, scale=0.34, z=4, center=True)

    factory.button(root, "Close", 1560, 102, 110, 42, close_panel, fill=(0.45, 0.18, 0.18, 0.95), scale=0.34)
    factory.button(
        root,
        "Edit" if not STATE.edit_mode else "Done",
        1420,
        102,
        120,
        42,
        lambda: _toggle_edit(),
        fill=(0.30, 0.34, 0.20, 0.95),
        scale=0.34,
    )

    # Page tabs
    tab_x = 250
    for page_i in range(MAX_PAGES):
        fill = (0.20, 0.55, 0.72, 0.98) if page_i == STATE.page else (0.18, 0.22, 0.28, 0.94)

        def _make_page(i: int = page_i) -> Callable[[], None]:
            return lambda: _set_page(i)

        factory.button(root, f"P{page_i + 1}", tab_x, 170, 70, 40, _make_page(), fill=fill, scale=0.32)
        tab_x += 80

    factory.button(root, "Pin Last Command", 700, 170, 240, 40, lambda: pin_last_command(), fill=(0.55, 0.38, 0.12, 0.96), scale=0.32)
    factory.button(root, "Lock Player", 960, 170, 170, 40, toggle_drop_lock, fill=(0.28, 0.24, 0.45, 0.96), scale=0.32)
    last = backend_actions.get_last_command()
    last_txt = f"Last: {last.get('label')}" if last else "Last: (none)"
    drop = backend_actions.get_last_drop()
    drop_txt = f"Drop: {drop.get('label')}" if drop else "Drop: (none)"
    factory.text(root, f"{last_txt}   |   {drop_txt}", 250, 225, 1400, 30, scale=0.30, z=5, tint=(0.75, 0.82, 0.90, 1.0))

    # Grid 4x3
    grid_x0, grid_y0 = 280, 280
    cell_w, cell_h = 320, 120
    gap_x, gap_y = 24, 20
    slots = STATE.pages[STATE.page]
    for idx in range(SLOTS_PER_PAGE):
        row, col = divmod(idx, GRID_COLS)
        x = grid_x0 + col * (cell_w + gap_x)
        y = grid_y0 + row * (cell_h + gap_y)
        slot = slots[idx]
        selected = STATE.edit_mode and STATE.selected_slot == idx
        if slot is None:
            label = "+ Empty" if STATE.edit_mode else "—"
            fill = (0.22, 0.24, 0.28, 0.90) if STATE.edit_mode else (0.14, 0.16, 0.19, 0.85)
        else:
            label = slot_label(slot)
            fill = (0.18, 0.48, 0.42, 0.95) if not selected else (0.55, 0.42, 0.14, 0.96)

        def _make_slot(i: int = idx) -> Callable[[], None]:
            return lambda: activate_slot(i)

        factory.button(root, label, x, y, cell_w, cell_h, _make_slot(), fill=fill, scale=0.34)

    factory.text(root, STATE.status, 250, 900, 1400, 40, scale=0.32, z=6, tint=(0.85, 0.90, 0.95, 1.0))

    if STATE.modal == "player_pick":
        _render_player_pick(factory, root)
    elif STATE.modal == "action_pick":
        _render_action_pick(factory, root)
    elif STATE.modal == "label_edit":
        _render_label_edit(factory, root)


def _toggle_edit() -> None:
    STATE.edit_mode = not STATE.edit_mode
    STATE.modal = ""
    STATE.selected_slot = None
    save_layout()
    rebuild_ui()


def _set_page(page: int) -> None:
    STATE.page = max(0, min(MAX_PAGES - 1, int(page)))
    STATE.selected_slot = None
    STATE.modal = ""
    save_layout()
    rebuild_ui()


def _render_player_pick(factory: NativeUMG, root: Any) -> None:
    factory.border(root, 420, 200, 1080, 680, (0.05, 0.07, 0.10, 0.97), 80)
    title = "Lock repeat-last-drop to player" if not STATE.pending_repeat else "Select player for repeat last drop"
    factory.text(root, title, 450, 220, 1000, 40, scale=0.48, z=81, center=True)
    players = backend_actions.refresh_players()
    y = 280
    if not players:
        factory.text(root, "No party players found.", 450, 320, 1000, 40, scale=0.40, z=81, center=True)
    for player in players:
        idx = int(player.get("index", -1))
        name = str(player.get("name") or f"Player {idx}")

        def _make_pick(i: int = idx, n: str = name) -> Callable[[], None]:
            if STATE.pending_repeat:
                return lambda: _finish_repeat_for_player(i, n)
            return lambda: _lock_player_from_pick(i, n)

        factory.button(root, f"{idx}: {name}", 520, y, 880, 56, _make_pick(), fill=(0.20, 0.40, 0.55, 0.96), scale=0.36)
        y += 70
        if y > 780:
            break

    def _cancel() -> None:
        STATE.modal = ""
        STATE.pending_repeat = False
        rebuild_ui()

    factory.button(root, "Cancel", 860, 800, 200, 48, _cancel, fill=(0.40, 0.20, 0.20, 0.95), scale=0.34)


def _render_action_pick(factory: NativeUMG, root: Any) -> None:
    factory.border(root, 360, 160, 1200, 760, (0.05, 0.07, 0.10, 0.97), 80)
    factory.text(root, "Assign action to slot", 390, 180, 1140, 40, scale=0.48, z=81, center=True)
    y = 240
    x = 400
    for i, action in enumerate(PICKER_ACTIONS):
        label = str(ACTION_CATALOG.get(action, {}).get("basic") or action)

        def _make_assign(a: str = action) -> Callable[[], None]:
            return lambda: assign_action_to_selected(a)

        factory.button(root, label, x, y, 340, 50, _make_assign(), fill=(0.22, 0.36, 0.48, 0.96), scale=0.30)
        if i % 3 == 2:
            x = 400
            y += 62
        else:
            x += 360
    if backend_actions.get_last_command() is not None:
        factory.button(
            root,
            "Pin Last Command Here",
            700,
            820,
            320,
            48,
            lambda: pin_last_command(STATE.selected_slot),
            fill=(0.55, 0.38, 0.12, 0.96),
            scale=0.32,
        )

    def _cancel() -> None:
        STATE.modal = ""
        rebuild_ui()

    factory.button(root, "Cancel", 1100, 820, 160, 48, _cancel, fill=(0.40, 0.20, 0.20, 0.95), scale=0.34)


def _render_label_edit(factory: NativeUMG, root: Any) -> None:
    if STATE.selected_slot is None:
        return
    slot = STATE.pages[STATE.page][STATE.selected_slot]
    if slot is None:
        return
    factory.border(root, 560, 280, 800, 420, (0.05, 0.07, 0.10, 0.97), 80)
    factory.text(root, f"Edit slot {STATE.selected_slot + 1}", 590, 300, 740, 40, scale=0.46, z=81, center=True)
    factory.text(root, f"Label: {slot_label(slot)}", 590, 360, 740, 36, scale=0.36, z=81, center=True)

    def _cycle() -> None:
        cycle_slot_label(slot)
        save_layout()
        rebuild_ui()

    factory.button(root, "Cycle Label (basic/alias/custom)", 620, 430, 680, 56, _cycle, fill=(0.28, 0.40, 0.52, 0.96), scale=0.32)
    factory.button(root, "Clear Slot", 620, 510, 320, 52, clear_selected_slot, fill=(0.50, 0.22, 0.18, 0.96), scale=0.32)
    factory.button(
        root,
        "Pin Last Over This",
        980,
        510,
        320,
        52,
        lambda: pin_last_command(STATE.selected_slot),
        fill=(0.55, 0.38, 0.12, 0.96),
        scale=0.32,
    )

    def _done() -> None:
        STATE.modal = ""
        rebuild_ui()

    factory.button(root, "Done", 860, 600, 200, 48, _done, fill=(0.20, 0.45, 0.30, 0.96), scale=0.34)


def open_panel() -> None:
    if STATE.is_open:
        _log("Quick Menu already open")
        return
    load_layout()
    restore_input()
    try:
        create_overlay()
    except Exception as exc:
        _log(f"Open failed: {exc}")
        return
    STATE.is_open = True
    STATE.modal = ""
    STATE.pending_repeat = False
    rebuild_ui()
    capture_input()
    _log("Quick Menu opened")


def close_panel() -> None:
    if not STATE.is_open and not live(STATE.overlay):
        return
    STATE.is_open = False
    STATE.modal = ""
    STATE.pending_repeat = False
    STATE.buttons.clear()
    remove_widget(STATE.menu_canvas)
    remove_widget(STATE.overlay)
    STATE.menu_canvas = STATE.overlay = STATE.tree = STATE.root = None
    restore_input()
    _log("Quick Menu closed")


def toggle_panel() -> None:
    close_panel() if STATE.is_open else open_panel()


def poll_buttons() -> None:
    for ref in list(STATE.buttons):
        if not ref.enabled or not live(ref.widget):
            ref.was_pressed = False
            continue
        try:
            pressed = bool(ref.widget.IsPressed())
        except Exception:
            pressed = False
        if pressed and not ref.was_pressed:
            ref.was_pressed = True
        elif ref.was_pressed and not pressed:
            ref.was_pressed = False
            try:
                ref.action()
            except Exception as exc:
                _log(f"Button '{ref.label}' failed: {exc}")
            return


def _key_down(pc: Any, name: str) -> bool:
    if pc is None or not name:
        return False
    try:
        key = unrealsdk.make_struct("Key", KeyName=str(name))
        return bool(pc.IsInputKeyDown(key))
    except Exception:
        try:
            return bool(pc.IsInputKeyDown(str(name)))
        except Exception:
            return False


def process_escape() -> None:
    if not STATE.is_open:
        STATE.key_escape = False
        return
    pc = get_pc()
    down = _key_down(pc, "Escape")
    was = STATE.key_escape
    STATE.key_escape = down
    if down and not was:
        if STATE.modal:
            STATE.modal = ""
            STATE.pending_repeat = False
            rebuild_ui()
        else:
            close_panel()


def tick(_obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    try:
        if not STATE.is_open:
            process_escape()
            return None
        if not live(STATE.overlay):
            STATE.is_open = False
            STATE.menu_canvas = STATE.overlay = STATE.tree = STATE.root = None
            STATE.buttons.clear()
            restore_input()
            return None
        now = time.monotonic()
        if now - STATE.last_input_refresh >= 0.5:
            capture_input()
        process_escape()
        poll_buttons()
    except Exception as exc:
        _log(f"Tick failed: {exc}")
    return None


def install_hook() -> None:
    try:
        unrealsdk.hooks.remove_hook(TICK_PATH, Type.POST, HOOK_ID)
    except Exception:
        pass
    unrealsdk.hooks.add_hook(TICK_PATH, Type.POST, HOOK_ID, tick)


def start_quick_menu() -> None:
    if STATE.started:
        return
    try:
        install_hook()
        STATE.started = True
        _log("Quick Menu tick installed")
    except Exception as exc:
        _log(f"Quick Menu tick not installed yet: {exc!r}")


quick_menu_toggle = keybind(
    "MSBT Quick Menu",
    "F7",
    callback=toggle_panel,
    display_name="MSBT Quick Menu",
    description="Open or close the native UMG Quick Menu (grid pages, pin last command, repeat last drop).",
)


@command("msbt_quick_menu", description="Open or close the MSBT native UMG Quick Menu.")
def _cmd_msbt_quick_menu(_args: Any = None) -> None:
    toggle_panel()


@command("msbt_quick_menu_pin", description="Pin the last MSBT command into the Quick Menu.")
def _cmd_msbt_quick_menu_pin(_args: Any = None) -> None:
    if not STATE.is_open:
        open_panel()
    pin_last_command()
