"""Thin native-UMG Quick Menu for Matt's SDK Boosting Tools.

Does not import or use BLImGui. UIDevelopmentShowcase is reference-only and is not imported.
Actions go through backend_actions (same path as the external bridge).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

import unrealsdk
from mods_base import command, get_pc, keybind
from unrealsdk import logging
from unrealsdk.hooks import Type

from . import backend_actions, quick_menu_registry

PREFIX = "[Matts SDK Boosting Tools | QuickMenu]"
TICK_PATH = "/Script/Engine.CameraModifier:BlueprintModifyCamera"
HOOK_ID = "matts_sdk_boosting_tools_quick_menu_tick_v1"
DESIGN_W = 1920.0
DESIGN_H = 1080.0
VIEWPORT_Z = 999996
MAX_PAGES = quick_menu_registry.MAX_PAGES
SLOTS_PER_PAGE = quick_menu_registry.SLOTS_PER_PAGE
# Right-side dock layout (leaves most of the world view clear).
DOCK_W = 640.0
DOCK_X = DESIGN_W - DOCK_W
GRID_COLS = 2
GRID_ROWS = 6
MODAL_BLOCKER_Z = 80
MODAL_PANEL_Z = 81
MODAL_CONTENT_Z = 82
MODAL_BUTTON_Z = 83
ACTION_CATALOG = quick_menu_registry.ACTION_CATALOG
PICKER_ACTIONS = quick_menu_registry.NATIVE_PICKER_ACTIONS
DEFAULT_PAGE_0 = quick_menu_registry.DEFAULT_PAGE_0

# Borderlands / MSBT reds, oranges, golds (fully opaque by default).
C_DOCK = (0.08, 0.05, 0.03, 1.0)
C_HEADER = (0.62, 0.12, 0.05, 1.0)
C_EDGE = (1.0, 0.55, 0.08, 1.0)
C_BTN = (0.78, 0.30, 0.05, 1.0)
C_BTN_GOLD = (0.92, 0.62, 0.08, 1.0)
C_BTN_DANGER = (0.72, 0.14, 0.10, 1.0)
C_BTN_MUTED = (0.28, 0.16, 0.10, 1.0)
C_SLOT = (0.52, 0.20, 0.06, 1.0)
C_SLOT_SEL = (0.98, 0.72, 0.12, 1.0)
C_SLOT_EMPTY = (0.20, 0.12, 0.08, 1.0)
C_TEXT = (1.0, 0.93, 0.78, 1.0)
C_TEXT_DIM = (0.92, 0.78, 0.55, 1.0)
C_TOAST_OK = (0.55, 0.28, 0.05, 1.0)
C_TOAST_BAD = (0.70, 0.12, 0.10, 1.0)


@dataclass
class ButtonRef:
    widget: Any
    action: Callable[[], None]
    label: str
    enabled: bool = True
    was_pressed: bool = False
    modal_only: bool = False
    allow_when_modal: bool = False


@dataclass
class SliderRef:
    widget: Any
    key: str
    value: float
    label_widget: Any = None


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
    player_pick_purpose: str = ""  # "repeat" | "lock" | "target" | "action"
    pending_action: dict[str, Any] | None = None
    swap_armed_slot: int | None = None
    toast: str = ""
    toast_until: float = 0.0
    toast_ok: bool = True
    toast_overlay: Any = None
    toast_root: Any = None
    delivery_was_active: bool = False
    viewport_w: float = DESIGN_W
    viewport_h: float = DESIGN_H
    dpi_scale: float = 1.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    layout_w: float = DESIGN_W
    layout_h: float = DESIGN_H
    ui_scale: float = 1.0
    overlay: Any = None
    tree: Any = None
    root: Any = None
    menu_canvas: Any = None
    buttons: list[ButtonRef] = field(default_factory=list)
    sliders: list[SliderRef] = field(default_factory=list)
    panel_opacity: float = 1.0
    input_owner: Any = None
    input_snapshot: InputSnapshot = field(default_factory=InputSnapshot)
    last_input_refresh: float = 0.0
    last_layout_check: float = 0.0
    layout_revision: int = 0
    ui_dirty: bool = False
    key_escape: bool = False
    started: bool = False


def _with_alpha(fill: tuple[float, float, float, float], alpha: float) -> tuple[float, float, float, float]:
    r, g, b, _a = fill
    return (float(r), float(g), float(b), max(0.55, min(1.0, float(alpha))))


STATE = QuickMenuState()

_NEEDS_PLAYER_ACTIONS = quick_menu_registry.NEEDS_PLAYER_ACTIONS


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


def _button_layer(z: int, modal_only: bool, allow_when_modal: bool) -> int:
    if modal_only or allow_when_modal:
        return max(int(z), MODAL_BUTTON_Z)
    return int(z)


def remove_widget(widget: Any) -> None:
    if widget is not None:
        try_call(widget, "RemoveFromParent")


def _vec2_xy(value: Any) -> tuple[float, float] | None:
    try:
        x = float(getattr(value, "X", None))
        y = float(getattr(value, "Y", None))
        return x, y
    except Exception:
        pass
    try:
        seq = list(value)
        if len(seq) >= 2:
            return float(seq[0]), float(seq[1])
    except Exception:
        pass
    return None


def sx(value: float) -> float:
    return float(value) * STATE.scale_x


def sy(value: float) -> float:
    return float(value) * STATE.scale_y


def update_layout_metrics() -> None:
    """Match UIDevelopmentShowcase DPI math: layout = viewport / dpi, then scale design space."""
    raw_w, raw_h, dpi = DESIGN_W, DESIGN_H, 1.0
    pc = get_pc()
    if pc is not None:
        try:
            lib = class_obj("/Script/UMG.WidgetLayoutLibrary").ClassDefaultObject
            xy = _vec2_xy(lib.GetViewportSize(pc))
            if xy and xy[0] >= 800 and xy[1] >= 450:
                raw_w, raw_h = xy
            candidate = float(lib.GetViewportScale(pc) or 1.0)
            if 0.05 <= candidate <= 8.0:
                dpi = candidate
        except Exception:
            try:
                viewport = getattr(pc, "GetViewportSize", None)
                if callable(viewport):
                    xy = _vec2_xy(viewport())
                    if xy and xy[0] >= 800 and xy[1] >= 450:
                        raw_w, raw_h = xy
            except Exception:
                pass
    STATE.viewport_w, STATE.viewport_h, STATE.dpi_scale = raw_w, raw_h, dpi
    STATE.layout_w = max(1.0, raw_w / dpi)
    STATE.layout_h = max(1.0, raw_h / dpi)
    STATE.scale_x = max(0.1, min(8.0, STATE.layout_w / DESIGN_W))
    STATE.scale_y = max(0.1, min(8.0, STATE.layout_h / DESIGN_H))
    STATE.ui_scale = max(0.5, min(3.0, min(STATE.scale_x, STATE.scale_y)))


def _empty_page() -> list[dict[str, Any] | None]:
    return quick_menu_registry.empty_page()


def _normalize_slot(raw: object) -> dict[str, Any] | None:
    return quick_menu_registry.normalize_slot(raw)


def _default_pages() -> list[list[dict[str, Any] | None]]:
    return quick_menu_registry.default_pages()


def load_layout() -> None:
    layout = quick_menu_registry.load_persisted_layout()
    STATE.pages = layout["pages"]
    STATE.page = int(layout["page"])
    STATE.edit_mode = bool(layout["edit_mode"])
    STATE.layout_revision = quick_menu_registry.get_layout_revision()
    lock = backend_actions.get_drop_player_lock()
    drop_lock = layout["drop_lock"]
    if drop_lock.get("enabled"):
        lock_index = drop_lock.get("index")
        lock_name = str(drop_lock.get("name") or "").strip()
        if lock_index is not None and lock_name:
            lock_target: object = f"{lock_index}|{lock_name}"
        elif lock_index is not None:
            lock_target = lock_index
        else:
            lock_target = lock_name
        backend_actions.set_drop_player_lock(True, lock_target)
    elif lock.get("enabled"):
        backend_actions.set_drop_player_lock(False)


def save_layout() -> None:
    lock = backend_actions.get_drop_player_lock()
    if len(STATE.pages) == MAX_PAGES:
        pages = STATE.pages
    else:
        # Commands such as msbt_quick_menu_lock may save before F7 has ever
        # initialized STATE. Preserve the persisted/default grid in that case.
        pages = quick_menu_registry.load_persisted_layout()["pages"]
    payload = {
        "page": int(STATE.page),
        "edit_mode": bool(STATE.edit_mode),
        "pages": pages,
        "drop_lock": {
            "enabled": bool(lock.get("enabled")),
            "index": lock.get("index"),
            "name": lock.get("name") or "",
        },
    }
    try:
        result = quick_menu_registry.set_quick_menu_layout(payload)
        if not result.get("ok"):
            raise RuntimeError(result.get("message") or "Quick Menu layout validation failed.")
        STATE.pages = result["layout"]["pages"]
        STATE.layout_revision = quick_menu_registry.get_layout_revision()
    except Exception as exc:
        _log(f"Could not save Quick Menu layout: {exc!r}")


def slot_label(slot: dict[str, Any] | None) -> str:
    return quick_menu_registry.slot_label(slot)


def cycle_slot_label(slot: dict[str, Any]) -> None:
    quick_menu_registry.cycle_slot_label(slot)


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

    def modal_blocker(self, parent: Any) -> Any:
        """Dock-local hit-test layer so the open world view stays clear."""
        widget = self.widget("/Script/UMG.Border")
        try_call(widget, "SetBrushColor", color((0.0, 0.0, 0.0, 0.55)))
        try_call(widget, "SetVisibility", 0)
        try_call(widget, "SetIsEnabled", True)
        self.add(parent, widget)
        self.slot(widget, DOCK_X, 0, DOCK_W, DESIGN_H, MODAL_BLOCKER_Z)
        return widget

    def slider(
        self,
        parent: Any,
        key: str,
        value: float,
        x: float,
        y: float,
        w: float,
        h: float,
        *,
        z: int = 40,
    ) -> Any:
        widget = self.widget("/Script/UMG.Slider")
        try_call(widget, "SetMinValue", 0.55)
        try_call(widget, "SetMaxValue", 1.0)
        try_call(widget, "SetStepSize", 0.01)
        try_call(widget, "SetValue", float(value))
        try_call(widget, "SetVisibility", 0)
        try_call(widget, "SetIsEnabled", True)
        self.add(parent, widget)
        self.slot(widget, x, y, w, h, z)
        STATE.sliders.append(SliderRef(widget, key, float(value)))
        return widget

    def scroll_box(self, parent: Any, x: float, y: float, w: float, h: float, *, z: int = 20) -> Any:
        widget = self.widget("/Script/UMG.ScrollBox")
        try_call(widget, "SetVisibility", 0)
        try_call(widget, "SetIsEnabled", True)
        try_call(widget, "SetAlwaysShowScrollbar", True)
        try_call(widget, "SetAlwaysShowScrollbarTrack", True)
        try_call(widget, "SetAnimateWheelScrolling", False)
        try_call(widget, "SetWheelScrollMultiplier", 1.0)
        try_call(widget, "SetConsumeMouseWheel", 1)
        try_call(widget, "SetAllowRightClickDragScrolling", False)
        try_call(widget, "SetScrollBarThickness", vec2(sx(14.0), sy(14.0)))
        self.add(parent, widget)
        self.slot(widget, x, y, w, h, z)
        return widget

    def scroll_row(self, scroll: Any, w: float, h: float) -> Any:
        size = self.widget("/Script/UMG.SizeBox")
        try_call(size, "SetWidthOverride", sx(w))
        try_call(size, "SetHeightOverride", sy(h))
        try_call(size, "SetMinDesiredWidth", sx(w))
        try_call(size, "SetMinDesiredHeight", sy(h))
        self.add(scroll, size)
        row = self.widget("/Script/UMG.CanvasPanel")
        try_call(row, "SetVisibility", 0)
        try_call(row, "SetIsEnabled", True)
        self.add(size, row)
        return row

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
        tint: tuple[float, float, float, float] = C_TEXT,
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
        fill: tuple[float, float, float, float] = C_BTN,
        enabled: bool = True,
        z: int = 50,
        scale: float = 0.36,
        modal_only: bool = False,
        allow_when_modal: bool = False,
    ) -> Any:
        # Modal backdrops render below MODAL_BUTTON_Z. Keep every modal button
        # (including global Close when a modal is active)
        # its hit target and label) above that layer; otherwise the modal title
        # is visible while player/action rows appear as a blank screen.
        layer = _button_layer(z, modal_only, allow_when_modal)
        base = fill if enabled else C_BTN_MUTED
        self.border(parent, x, y, w, h, base, layer)
        widget = self.widget("/Script/UMG.Button")
        self.add(parent, widget)
        self.slot(widget, x, y, w, h, layer + 1)
        try_call(widget, "SetVisibility", 0)
        try_call(widget, "SetIsEnabled", bool(enabled))
        try_call(widget, "SetRenderOpacity", 0.03 if enabled else 0.01)
        self.text(
            parent,
            label,
            x + 4,
            y + 2,
            w - 8,
            h - 4,
            scale=scale,
            z=layer + 2,
            center=True,
        )
        STATE.buttons.append(
            ButtonRef(widget, action, label, enabled, False, modal_only, allow_when_modal)
        )
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
    STATE.sliders.clear()
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


def show_toast(message: str, *, ok: bool = True, seconds: float = 2.6) -> None:
    """Show a short delivery/action toast (menu banner and/or non-blocking overlay)."""
    text = str(message or "").strip()
    if not text:
        return
    STATE.toast = text[:160]
    STATE.toast_ok = bool(ok)
    STATE.toast_until = time.monotonic() + max(0.8, float(seconds))
    STATE.status = STATE.toast
    _log(STATE.toast)
    if STATE.is_open:
        STATE.ui_dirty = True
        return
    try:
        _ensure_toast_overlay(STATE.toast, STATE.toast_ok)
    except Exception as exc:
        _log(f"Toast overlay failed: {exc!r}")


def _set_status_from_result(result: dict[str, Any] | None) -> None:
    if not isinstance(result, dict):
        return
    message = str(result.get("message") or "")
    if message:
        show_toast(message, ok=bool(result.get("ok", True)))


def _force_game_only_input() -> None:
    """Hard restore GameOnly input even if Quick Menu state is corrupted."""
    pc = get_pc()
    if pc is None:
        return
    try:
        lib = class_obj("/Script/UMG.WidgetBlueprintLibrary").ClassDefaultObject
        try_call(lib, "ClearAllUserFocus", pc)
        if not try_call(lib, "SetInputMode_GameOnly", pc, True):
            try_call(lib, "SetInputMode_GameOnly", pc)
        try_call(lib, "SetFocusToGameViewport")
    except Exception:
        pass
    for attr, value in (
        ("bShowMouseCursor", False),
        ("bEnableMouseOverEvents", False),
        ("bEnableClickEvents", False),
        ("bEnableTouchEvents", False),
        ("bBlockInput", False),
    ):
        try:
            setattr(pc, attr, value)
        except Exception:
            pass
    try_call(pc, "ResetIgnoreLookInput")
    try_call(pc, "ResetIgnoreMoveInput")
    try_call(pc, "ResetIgnoreInputFlags")


def unstuck() -> None:
    """Emergency close Quick Menu overlays and restore gameplay input."""
    try:
        close_panel()
    except Exception:
        STATE.is_open = False
        STATE.buttons.clear()
        STATE.sliders.clear()
        try:
            remove_widget(STATE.menu_canvas)
        except Exception:
            pass
        try:
            remove_widget(STATE.overlay)
        except Exception:
            pass
        STATE.menu_canvas = STATE.overlay = STATE.tree = STATE.root = None
    try:
        _clear_toast_overlay()
    except Exception:
        pass
    try:
        restore_input()
    except Exception:
        pass
    _force_game_only_input()
    STATE.modal = ""
    STATE.pending_repeat = False
    STATE.player_pick_purpose = ""
    STATE.swap_armed_slot = None
    STATE.input_owner = None
    STATE.input_snapshot = InputSnapshot()
    _log("Quick Menu unstuck complete (GameOnly restored).")


def _ensure_toast_overlay(message: str, ok: bool) -> None:
    """Non-interactive toast when the menu is closed (no input capture)."""
    pc = get_pc()
    if pc is None:
        return
    update_layout_metrics()
    _clear_toast_overlay()
    widget = construct("/Script/UMG.UserWidget", pc)
    widget.WidgetTree = construct("/Script/UMG.WidgetTree", widget)
    root = construct("/Script/UMG.CanvasPanel", widget.WidgetTree)
    widget.WidgetTree.RootWidget = root
    try_call(root, "SetVisibility", 0)
    try_call(widget, "SetAlignmentInViewport", vec2(0.0, 0.0))
    try_call(widget, "SetPositionInViewport", vec2(0.0, 0.0), False)
    try_call(widget, "SetDesiredSizeInViewport", vec2(STATE.layout_w, STATE.layout_h))
    try_call(widget, "AddToViewport", VIEWPORT_Z + 2)
    # HitTestInvisible so gameplay input is not stolen.
    try_call(widget, "SetVisibility", 3)
    STATE.toast_overlay, STATE.toast_root = widget, root
    factory = NativeUMG(widget)
    fill = (0.10, 0.42, 0.24, 0.94) if ok else (0.48, 0.16, 0.14, 0.94)
    factory.border(root, 460, 40, 1000, 64, fill, 10)
    factory.text(root, message, 480, 52, 960, 40, scale=0.36, z=11, center=True)


def _clear_toast_overlay() -> None:
    remove_widget(STATE.toast_overlay)
    STATE.toast_overlay = None
    STATE.toast_root = None


def _poll_delivery_toasts() -> None:
    """Surface serial-delivery start/finish as toasts for Quick Menu / bridge drops."""
    try:
        progress = backend_actions.get_serial_delivery_progress()
    except Exception:
        return
    if not isinstance(progress, dict):
        return
    active = bool(progress.get("active"))
    message = str(progress.get("last_message") or progress.get("message") or "").strip()
    error = str(progress.get("last_error") or "").strip()
    if active and not STATE.delivery_was_active:
        STATE.delivery_was_active = True
        show_toast(message or "Serial delivery started…", ok=True, seconds=2.0)
    elif (not active) and STATE.delivery_was_active:
        STATE.delivery_was_active = False
        if error:
            show_toast(error, ok=False, seconds=3.2)
        else:
            show_toast(message or "Serial delivery finished.", ok=True, seconds=2.8)


def _page_filled_count(page: int | None = None) -> int:
    page_i = STATE.page if page is None else int(page)
    return sum(1 for slot in STATE.pages[page_i] if slot is not None)


def _ensure_target_for_action(action: str, payload: dict[str, Any] | None = None) -> bool:
    """Return True if action can run. Opens player picker when a target is required but missing."""
    if action not in _NEEDS_PLAYER_ACTIONS:
        return True
    ensured = backend_actions.ensure_selected_player(prefer_host=True)
    if ensured.get("ok"):
        if ensured.get("auto_selected"):
            show_toast(str(ensured.get("message") or "Target auto-selected."), ok=True, seconds=2.0)
        return True
    STATE.pending_action = {"action": action, "payload": dict(payload or {})}
    show_toast("Select a target player first.", ok=False, seconds=2.4)
    _begin_player_pick("action")
    return False


def _run_action(action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    catalog = ACTION_CATALOG.get(action, {})
    body = dict(payload or {})
    body.setdefault("_label", str(catalog.get("basic") or action))
    if not _ensure_target_for_action(action, body):
        return {"ok": False, "message": "Select a target player first.", "needs_player": True}
    result = backend_actions.run_quick_menu_action(action, body, record=True)
    if (not result.get("ok")) and "No party player selected" in str(result.get("message") or ""):
        STATE.pending_action = {"action": action, "payload": body}
        _begin_player_pick("action")
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
    if action not in quick_menu_registry.ASSIGNABLE_ACTIONS:
        show_toast(
            f"{action} is not available as a Quick Menu slot.",
            ok=False,
            seconds=3.0,
        )
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
    basic = str(ACTION_CATALOG.get(action, {}).get("basic") or action)
    label = str(command.get("label") or basic)
    payload = quick_menu_registry.sanitize_payload(action, command.get("payload") or {})
    # Keep payload-specific labels (spawn pool name, travel dest, etc.).
    use_custom = bool(label) and label not in {basic, action}
    STATE.pages[target_page][int(target_slot)] = {
        "action": action,
        "label_mode": "custom" if use_custom else "basic",
        "custom_label": (label[:48] if use_custom else ""),
        "payload": payload,
    }
    save_layout()
    _log(f"Pinned '{slot_label(STATE.pages[target_page][int(target_slot)])}' to page {target_page + 1} slot {int(target_slot) + 1}.")
    rebuild_ui()


def _begin_player_pick(purpose: str) -> None:
    STATE.modal = "player_pick"
    STATE.player_pick_purpose = str(purpose or "target")
    STATE.pending_repeat = STATE.player_pick_purpose == "repeat"
    rebuild_ui()


def _finish_repeat_for_player(index: int, name: str) -> None:
    STATE.modal = ""
    STATE.pending_repeat = False
    STATE.player_pick_purpose = ""
    result = backend_actions.repeat_last_drop(f"{index}|{name}" if name else index)
    _set_status_from_result(result)
    rebuild_ui()


def _set_target_from_pick(index: int, name: str) -> None:
    result = backend_actions.set_target_player(f"{index}|{name}" if name else index)
    purpose = STATE.player_pick_purpose
    pending = dict(STATE.pending_action) if isinstance(STATE.pending_action, dict) else None
    STATE.modal = ""
    STATE.player_pick_purpose = ""
    STATE.pending_action = None
    _set_status_from_result(result)
    if purpose == "action" and result.get("ok") and pending:
        action = str(pending.get("action") or "")
        payload = pending.get("payload") if isinstance(pending.get("payload"), dict) else {}
        if action:
            _run_action(action, payload)
    rebuild_ui()


def _swap_slots(a: int, b: int) -> None:
    page = STATE.pages[STATE.page]
    if a < 0 or b < 0 or a >= len(page) or b >= len(page) or a == b:
        return
    page[a], page[b] = page[b], page[a]
    STATE.selected_slot = b
    STATE.swap_armed_slot = None
    STATE.modal = ""
    save_layout()
    _log(f"Swapped slots {a + 1} and {b + 1}.")
    rebuild_ui()


def arm_swap_selected() -> None:
    if STATE.selected_slot is None:
        _log("Select a slot before starting a swap.")
        return
    STATE.swap_armed_slot = int(STATE.selected_slot)
    STATE.modal = ""
    _log(f"Swap armed on slot {STATE.swap_armed_slot + 1}. Tap another slot.")
    rebuild_ui()


def reset_current_page() -> None:
    if STATE.page == 0:
        row = [_normalize_slot(slot) for slot in DEFAULT_PAGE_0]
        while len(row) < SLOTS_PER_PAGE:
            row.append(None)
        STATE.pages[0] = row[:SLOTS_PER_PAGE]
    else:
        STATE.pages[STATE.page] = _empty_page()
    STATE.selected_slot = None
    STATE.swap_armed_slot = None
    STATE.modal = ""
    save_layout()
    _log(f"Reset page {STATE.page + 1}.")
    rebuild_ui()


def reset_all_pages() -> None:
    STATE.pages = _default_pages()
    STATE.page = 0
    STATE.selected_slot = None
    STATE.swap_armed_slot = None
    STATE.modal = ""
    save_layout()
    _log("Reset all Quick Menu pages to defaults.")
    rebuild_ui()


def activate_slot(slot_index: int) -> None:
    slots = STATE.pages[STATE.page]
    if slot_index < 0 or slot_index >= len(slots):
        return
    slot = slots[slot_index]
    if STATE.edit_mode:
        if STATE.swap_armed_slot is not None:
            _swap_slots(int(STATE.swap_armed_slot), int(slot_index))
            return
        STATE.selected_slot = slot_index
        if slot is None:
            STATE.modal = "action_pick"
        else:
            STATE.modal = "label_edit"
        rebuild_ui()
        return

    if slot is None:
        # Don't trap users on an emptied page — jump straight into assign flow.
        STATE.edit_mode = True
        STATE.selected_slot = slot_index
        STATE.modal = "action_pick"
        show_toast("Empty slot — pick an action to assign.", ok=True, seconds=2.0)
        rebuild_ui()
        return

    action = str(slot.get("action") or "")
    payload = dict(slot.get("payload") or {})
    if action == "repeat_last_drop":
        drop = backend_actions.get_last_drop()
        if drop is None:
            _log("No last drop to repeat.")
            return
        if bool(drop.get("needs_player")) and not backend_actions.get_drop_player_lock().get("enabled"):
            _begin_player_pick("repeat")
            return
        result = backend_actions.repeat_last_drop()
        if result.get("needs_player"):
            _begin_player_pick("repeat")
            return
        _set_status_from_result(result)
        rebuild_ui()
        return

    result = _run_action(action, payload)
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
            show_toast("No party players found. Load into a session, then Refresh.", ok=False, seconds=3.0)
            if STATE.is_open:
                rebuild_ui()
            return
        # Prefer currently selected; otherwise open picker to choose lock target.
        if backend_actions.get_selected_player_index() is None:
            _begin_player_pick("lock")
            _log("Pick a player to lock for repeat-last-drop.")
            return
        result = backend_actions.set_drop_player_lock(True)
    _set_status_from_result(result)
    save_layout()
    rebuild_ui()


def _lock_player_from_pick(index: int, name: str) -> None:
    result = backend_actions.set_drop_player_lock(True, f"{index}|{name}" if name else index)
    STATE.modal = ""
    STATE.player_pick_purpose = ""
    STATE.pending_repeat = False
    _set_status_from_result(result)
    save_layout()
    rebuild_ui()


def rebuild_ui() -> None:
    if not STATE.is_open:
        return
    STATE.ui_dirty = False
    factory, root = reset_canvas()
    STATE.sliders.clear()
    opacity = max(0.55, min(1.0, float(STATE.panel_opacity or 1.0)))

    # Right-side opaque dock only — no centered fullscreen pastel panel.
    factory.border(root, DOCK_X - 6, 0, 6, DESIGN_H, _with_alpha(C_EDGE, 1.0), 1)
    factory.border(root, DOCK_X, 0, DOCK_W, DESIGN_H, _with_alpha(C_DOCK, opacity), 2)
    factory.border(root, DOCK_X, 0, DOCK_W, 70, _with_alpha(C_HEADER, opacity), 3)
    factory.text(root, "MSBT Quick Menu", DOCK_X + 16, 16, 380, 40, scale=0.50, z=4)
    mode = "EDIT" if STATE.edit_mode else "RUN"
    lock = backend_actions.get_drop_player_lock()
    lock_txt = f"Lock {lock.get('name') or 'ON'}" if lock.get("enabled") else "Lock OFF"
    factory.text(
        root,
        f"{mode} | P{STATE.page + 1}/{MAX_PAGES} | {lock_txt}",
        DOCK_X + 16,
        48,
        420,
        22,
        scale=0.26,
        z=4,
        tint=C_TEXT_DIM,
    )

    factory.button(
        root,
        "Close",
        DOCK_X + DOCK_W - 118,
        14,
        100,
        42,
        close_panel,
        fill=_with_alpha(C_BTN_DANGER, opacity),
        scale=0.32,
        allow_when_modal=True,
    )
    factory.button(
        root,
        "Edit" if not STATE.edit_mode else "Done",
        DOCK_X + DOCK_W - 238,
        14,
        110,
        42,
        lambda: _toggle_edit(),
        fill=_with_alpha(C_BTN_GOLD, opacity),
        scale=0.32,
    )

    tab_x = DOCK_X + 16
    for page_i in range(MAX_PAGES):
        fill = C_BTN_GOLD if page_i == STATE.page else C_BTN_MUTED

        def _make_page(i: int = page_i) -> Callable[[], None]:
            return lambda: _set_page(i)

        factory.button(
            root,
            f"P{page_i + 1}",
            tab_x,
            84,
            56,
            36,
            _make_page(),
            fill=_with_alpha(fill, opacity),
            scale=0.28,
        )
        tab_x += 62

    factory.button(
        root,
        "Pin Last",
        DOCK_X + 16,
        128,
        140,
        36,
        lambda: pin_last_command(),
        fill=_with_alpha(C_BTN_GOLD, opacity),
        scale=0.26,
    )
    factory.button(
        root,
        "Lock",
        DOCK_X + 164,
        128,
        90,
        36,
        toggle_drop_lock,
        fill=_with_alpha(C_BTN, opacity),
        scale=0.26,
    )
    factory.button(
        root,
        "Target",
        DOCK_X + 262,
        128,
        100,
        36,
        lambda: _begin_player_pick("target"),
        fill=_with_alpha(C_BTN, opacity),
        scale=0.26,
    )

    def _refresh_ui() -> None:
        _run_action("refresh_players")
        rebuild_ui()

    factory.button(
        root,
        "Refresh",
        DOCK_X + 370,
        128,
        110,
        36,
        _refresh_ui,
        fill=_with_alpha(C_BTN_MUTED, opacity),
        scale=0.26,
    )

    selected_name = backend_actions.get_selected_player_name() or "(none)"
    selected_idx = backend_actions.get_selected_player_index()
    target_txt = f"Target: {selected_idx}: {selected_name}" if selected_idx is not None else "Target: (none)"
    last = backend_actions.get_last_command()
    last_txt = f"Last: {last.get('label')}" if last else "Last: (none)"
    drop = backend_actions.get_last_drop()
    drop_txt = f"Drop: {drop.get('label')}" if drop else "Drop: (none)"
    factory.text(root, target_txt, DOCK_X + 16, 172, DOCK_W - 32, 22, scale=0.24, z=5, tint=C_TEXT_DIM)
    factory.text(root, f"{last_txt} | {drop_txt}", DOCK_X + 16, 194, DOCK_W - 32, 22, scale=0.24, z=5, tint=C_TEXT_DIM)

    filled = _page_filled_count()
    if filled == 0:
        factory.border(root, DOCK_X + 16, 220, DOCK_W - 32, 36, _with_alpha(C_BTN_GOLD, opacity), 8)
        factory.text(
            root,
            "Empty page — tap + Assign or Reset.",
            DOCK_X + 24,
            226,
            DOCK_W - 48,
            26,
            scale=0.24,
            z=9,
            center=True,
        )

    grid_x0 = DOCK_X + 16
    grid_y0 = 266.0
    cell_w, cell_h = 292.0, 78.0
    gap_x, gap_y = 12.0, 10.0
    slots = STATE.pages[STATE.page]
    for idx in range(SLOTS_PER_PAGE):
        row, col = divmod(idx, GRID_COLS)
        x = grid_x0 + col * (cell_w + gap_x)
        y = grid_y0 + row * (cell_h + gap_y)
        slot = slots[idx]
        selected = STATE.edit_mode and STATE.selected_slot == idx
        if slot is None:
            label = "+ Assign"
            fill = C_SLOT_EMPTY
        else:
            label = slot_label(slot)
            fill = C_SLOT_SEL if selected else C_SLOT

        def _make_slot(i: int = idx) -> Callable[[], None]:
            return lambda: activate_slot(i)

        factory.button(
            root,
            label,
            x,
            y,
            cell_w,
            cell_h,
            _make_slot(),
            fill=_with_alpha(fill, opacity),
            scale=0.28,
        )

    factory.text(root, STATE.status, DOCK_X + 16, 820, DOCK_W - 32, 36, scale=0.26, z=6, tint=C_TEXT_DIM)

    # Opaque opacity slider (keeps dock readable; default fully opaque).
    factory.text(
        root,
        f"Opacity {int(opacity * 100)}%",
        DOCK_X + 16,
        858,
        200,
        24,
        scale=0.24,
        z=6,
        tint=C_TEXT_DIM,
    )
    factory.border(root, DOCK_X + 16, 886, DOCK_W - 32, 28, _with_alpha(C_BTN_MUTED, 1.0), 6)
    factory.slider(root, "panel_opacity", opacity, DOCK_X + 20, 888, DOCK_W - 40, 24, z=7)

    if STATE.edit_mode or filled == 0:
        if filled == 0 and STATE.page > 0:
            recovery_label = "Go Page 1"
            recovery_action = lambda: _set_page(0)
        else:
            recovery_label = "Reset Page"
            recovery_action = reset_current_page
        factory.button(
            root,
            recovery_label,
            DOCK_X + 16,
            930,
            180,
            40,
            recovery_action,
            fill=_with_alpha(C_BTN, opacity),
            scale=0.26,
        )
        factory.button(
            root,
            "Reset All",
            DOCK_X + 208,
            930,
            160,
            40,
            reset_all_pages,
            fill=_with_alpha(C_BTN_DANGER, opacity),
            scale=0.26,
        )

    if STATE.toast and time.monotonic() < STATE.toast_until:
        fill = C_TOAST_OK if STATE.toast_ok else C_TOAST_BAD
        factory.border(root, DOCK_X + 20, 980, DOCK_W - 40, 48, _with_alpha(fill, 1.0), 90)
        factory.text(root, STATE.toast, DOCK_X + 28, 990, DOCK_W - 56, 30, scale=0.28, z=91, center=True)

    if STATE.modal == "player_pick":
        _render_player_pick(factory, root)
    elif STATE.modal == "action_pick":
        _render_action_pick(factory, root)
    elif STATE.modal == "label_edit":
        _render_label_edit(factory, root)



def _toggle_edit() -> None:
    leaving_edit = bool(STATE.edit_mode)
    STATE.edit_mode = not STATE.edit_mode
    STATE.modal = ""
    STATE.selected_slot = None
    STATE.swap_armed_slot = None
    save_layout()
    if leaving_edit and _page_filled_count() == 0:
        show_toast("This page is empty. Tap a slot to assign, or Reset Page.", ok=False, seconds=3.0)
    rebuild_ui()


def _set_page(page: int) -> None:
    STATE.page = max(0, min(MAX_PAGES - 1, int(page)))
    STATE.selected_slot = None
    STATE.swap_armed_slot = None
    STATE.modal = ""
    save_layout()
    rebuild_ui()


def _render_player_pick(factory: NativeUMG, root: Any) -> None:
    factory.modal_blocker(root)
    factory.border(root, DOCK_X + 12, 120, DOCK_W - 24, 780, _with_alpha(C_DOCK, 1.0), MODAL_PANEL_Z)
    factory.border(root, DOCK_X + 12, 120, DOCK_W - 24, 56, _with_alpha(C_HEADER, 1.0), MODAL_CONTENT_Z)
    purpose = STATE.player_pick_purpose or ("repeat" if STATE.pending_repeat else "lock")
    title = {
        "repeat": "Select player for repeat last drop",
        "lock": "Lock repeat-last-drop to player",
        "target": "Select target player",
        "action": "Select target player for this action",
    }.get(purpose, "Select player")
    factory.text(root, title, DOCK_X + 24, 132, DOCK_W - 48, 36, scale=0.34, z=MODAL_CONTENT_Z + 1, center=True)
    players = backend_actions.refresh_players()
    scroll = factory.scroll_box(root, DOCK_X + 24, 190, DOCK_W - 48, 620, z=MODAL_CONTENT_Z)
    if not players:
        row = factory.scroll_row(scroll, DOCK_W - 64, 48)
        factory.text(row, "No party players found.", 8, 8, DOCK_W - 80, 32, scale=0.30, z=1, center=True)
    for player in players:
        idx = int(player.get("index", -1))
        name = str(player.get("name") or f"Player {idx}")

        def _make_pick(i: int = idx, n: str = name, p: str = purpose) -> Callable[[], None]:
            if p == "repeat":
                return lambda: _finish_repeat_for_player(i, n)
            if p in ("target", "action"):
                return lambda: _set_target_from_pick(i, n)
            return lambda: _lock_player_from_pick(i, n)

        row = factory.scroll_row(scroll, DOCK_W - 64, 58)
        factory.button(
            row,
            f"{idx}: {name}",
            0,
            4,
            DOCK_W - 72,
            50,
            _make_pick(),
            fill=C_BTN,
            scale=0.30,
            modal_only=True,
            z=1,
        )

    def _cancel() -> None:
        STATE.modal = ""
        STATE.pending_repeat = False
        STATE.player_pick_purpose = ""
        STATE.pending_action = None
        rebuild_ui()

    factory.button(
        root,
        "Cancel",
        DOCK_X + (DOCK_W - 180) / 2,
        830,
        180,
        44,
        _cancel,
        fill=C_BTN_DANGER,
        scale=0.30,
        modal_only=True,
    )


def _render_action_pick(factory: NativeUMG, root: Any) -> None:
    factory.modal_blocker(root)
    factory.border(root, DOCK_X + 12, 100, DOCK_W - 24, 820, _with_alpha(C_DOCK, 1.0), MODAL_PANEL_Z)
    factory.border(root, DOCK_X + 12, 100, DOCK_W - 24, 52, _with_alpha(C_HEADER, 1.0), MODAL_CONTENT_Z)
    factory.text(root, "Assign action to slot", DOCK_X + 24, 112, DOCK_W - 48, 32, scale=0.34, z=MODAL_CONTENT_Z + 1, center=True)
    scroll = factory.scroll_box(root, DOCK_X + 24, 164, DOCK_W - 48, 640, z=MODAL_CONTENT_Z)
    for action in PICKER_ACTIONS:
        label = str(ACTION_CATALOG.get(action, {}).get("basic") or action)

        def _make_assign(a: str = action) -> Callable[[], None]:
            return lambda: assign_action_to_selected(a)

        row = factory.scroll_row(scroll, DOCK_W - 64, 52)
        factory.button(
            row,
            label,
            0,
            2,
            DOCK_W - 72,
            46,
            _make_assign(),
            fill=C_BTN,
            scale=0.28,
            modal_only=True,
            z=1,
        )
    if backend_actions.get_last_command() is not None:
        factory.button(
            root,
            "Pin Last Here",
            DOCK_X + 24,
            820,
            220,
            44,
            lambda: pin_last_command(STATE.selected_slot),
            fill=C_BTN_GOLD,
            scale=0.28,
            modal_only=True,
        )

    def _cancel() -> None:
        STATE.modal = ""
        rebuild_ui()

    factory.button(
        root,
        "Cancel",
        DOCK_X + DOCK_W - 196,
        820,
        160,
        44,
        _cancel,
        fill=C_BTN_DANGER,
        scale=0.28,
        modal_only=True,
    )


def _render_label_edit(factory: NativeUMG, root: Any) -> None:
    if STATE.selected_slot is None:
        return
    slot = STATE.pages[STATE.page][STATE.selected_slot]
    if slot is None:
        return
    factory.modal_blocker(root)
    factory.border(root, DOCK_X + 20, 220, DOCK_W - 40, 520, _with_alpha(C_DOCK, 1.0), MODAL_PANEL_Z)
    factory.border(root, DOCK_X + 20, 220, DOCK_W - 40, 52, _with_alpha(C_HEADER, 1.0), MODAL_CONTENT_Z)
    factory.text(root, f"Edit slot {STATE.selected_slot + 1}", DOCK_X + 32, 232, DOCK_W - 64, 32, scale=0.34, z=MODAL_CONTENT_Z + 1, center=True)
    factory.text(root, f"Label: {slot_label(slot)}", DOCK_X + 32, 290, DOCK_W - 64, 30, scale=0.28, z=MODAL_CONTENT_Z, center=True)

    def _cycle() -> None:
        cycle_slot_label(slot)
        save_layout()
        rebuild_ui()

    factory.button(
        root,
        "Cycle Label",
        DOCK_X + 40,
        340,
        DOCK_W - 80,
        48,
        _cycle,
        fill=C_BTN,
        scale=0.28,
        modal_only=True,
    )
    factory.button(
        root,
        "Clear Slot",
        DOCK_X + 40,
        404,
        (DOCK_W - 96) / 2,
        44,
        clear_selected_slot,
        fill=C_BTN_DANGER,
        scale=0.28,
        modal_only=True,
    )
    factory.button(
        root,
        "Swap With…",
        DOCK_X + 40 + (DOCK_W - 96) / 2 + 16,
        404,
        (DOCK_W - 96) / 2,
        44,
        arm_swap_selected,
        fill=C_BTN_GOLD,
        scale=0.28,
        modal_only=True,
    )
    if backend_actions.get_last_command() is not None:
        factory.button(
            root,
            "Pin Last Over This",
            DOCK_X + 40,
            464,
            DOCK_W - 80,
            44,
            lambda: pin_last_command(STATE.selected_slot),
            fill=C_BTN_GOLD,
            scale=0.28,
            modal_only=True,
        )

    def _done() -> None:
        STATE.modal = ""
        STATE.swap_armed_slot = None
        rebuild_ui()

    factory.button(
        root,
        "Done",
        DOCK_X + (DOCK_W - 180) / 2,
        540,
        180,
        44,
        _done,
        fill=C_BTN,
        scale=0.30,
        modal_only=True,
    )


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
    STATE.player_pick_purpose = ""
    STATE.pending_action = None
    STATE.swap_armed_slot = None
    _clear_toast_overlay()
    try:
        ensured = backend_actions.ensure_selected_player(prefer_host=True)
        if ensured.get("auto_selected"):
            STATE.status = str(ensured.get("message") or STATE.status)
    except Exception:
        pass
    rebuild_ui()
    capture_input()
    _log(
        f"Quick Menu opened (viewport={int(STATE.viewport_w)}x{int(STATE.viewport_h)} "
        f"dpi={STATE.dpi_scale:.3f} layout={int(STATE.layout_w)}x{int(STATE.layout_h)})"
    )


def close_panel() -> None:
    if not STATE.is_open and not live(STATE.overlay):
        return
    STATE.is_open = False
    STATE.modal = ""
    STATE.pending_repeat = False
    STATE.player_pick_purpose = ""
    STATE.pending_action = None
    STATE.swap_armed_slot = None
    STATE.buttons.clear()
    STATE.sliders.clear()
    remove_widget(STATE.menu_canvas)
    remove_widget(STATE.overlay)
    STATE.menu_canvas = STATE.overlay = STATE.tree = STATE.root = None
    restore_input()
    _log("Quick Menu closed")


def toggle_panel() -> None:
    close_panel() if STATE.is_open else open_panel()



def poll_sliders() -> None:
    changed = False
    for ref in list(STATE.sliders):
        widget = ref.widget
        if not live(widget):
            continue
        try:
            value = float(widget.GetValue())
        except Exception:
            continue
        value = max(0.55, min(1.0, value))
        if abs(value - float(ref.value)) < 0.005:
            continue
        ref.value = value
        if ref.key == "panel_opacity":
            STATE.panel_opacity = value
            changed = True
    if changed:
        STATE.ui_dirty = True


def poll_buttons() -> None:
    modal_active = bool(STATE.modal)
    for ref in list(STATE.buttons):
        if modal_active and not ref.modal_only and not ref.allow_when_modal:
            ref.was_pressed = False
            continue
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
            STATE.player_pick_purpose = ""
            STATE.pending_action = None
            STATE.swap_armed_slot = None
            rebuild_ui()
        else:
            close_panel()


def _expire_toast() -> None:
    if not STATE.toast:
        return
    if time.monotonic() < STATE.toast_until:
        return
    STATE.toast = ""
    _clear_toast_overlay()
    if STATE.is_open:
        STATE.ui_dirty = True


def _refresh_layout_if_changed() -> None:
    before = (
        STATE.viewport_w,
        STATE.viewport_h,
        STATE.dpi_scale,
        STATE.layout_w,
        STATE.layout_h,
    )
    update_layout_metrics()
    after = (
        STATE.viewport_w,
        STATE.viewport_h,
        STATE.dpi_scale,
        STATE.layout_w,
        STATE.layout_h,
    )
    if any(abs(float(a) - float(b)) > 0.01 for a, b in zip(before, after)):
        STATE.ui_dirty = True


def tick(_obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    try:
        _poll_delivery_toasts()
        _expire_toast()
        if not STATE.is_open:
            process_escape()
            return None
        if not live(STATE.overlay):
            STATE.is_open = False
            STATE.menu_canvas = STATE.overlay = STATE.tree = STATE.root = None
            STATE.buttons.clear()
            STATE.sliders.clear()
            restore_input()
            return None
        if quick_menu_registry.get_layout_revision() != STATE.layout_revision:
            STATE.modal = ""
            STATE.pending_repeat = False
            STATE.player_pick_purpose = ""
            STATE.pending_action = None
            STATE.selected_slot = None
            STATE.swap_armed_slot = None
            load_layout()
            STATE.ui_dirty = True
        now = time.monotonic()
        if now - STATE.last_input_refresh >= 0.5:
            _refresh_layout_if_changed()
            capture_input()
        process_escape()
        poll_sliders()
        poll_buttons()
        if STATE.is_open and STATE.ui_dirty:
            rebuild_ui()
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

quick_menu_unstuck_key = keybind(
    "MSBT Quick Menu Unstuck",
    "F6",
    callback=unstuck,
    display_name="MSBT Quick Menu Unstuck",
    description="Emergency close Quick Menu and restore GameOnly input if the cursor/input gets stuck.",
)


@command("msbt_quick_menu", description="Open or close the MSBT native UMG Quick Menu.")
def _cmd_msbt_quick_menu(_args: Any = None) -> None:
    toggle_panel()


@command("msbt_quick_menu_pin", description="Pin the last MSBT command into the Quick Menu.")
def _cmd_msbt_quick_menu_pin(_args: Any = None) -> None:
    if not STATE.is_open:
        open_panel()
    pin_last_command()


@command("msbt_quick_menu_unstuck", description="Emergency close Quick Menu and restore GameOnly input.")
def _cmd_msbt_quick_menu_unstuck(_args: Any = None) -> None:
    unstuck()


@command("msbt_quick_menu_repeat", description="Repeat the last MSBT drop/delivery (needs player unless lock-to-player is on).")
def _cmd_msbt_quick_menu_repeat(_args: Any = None) -> None:
    target = None
    try:
        raw = str(getattr(_args, "player", "") or "").strip()
        if raw:
            target = raw
    except Exception:
        target = None
    result = backend_actions.repeat_last_drop(target)
    if result.get("needs_player") and STATE.is_open:
        _begin_player_pick("repeat")
        return
    _set_status_from_result(result)
    if STATE.is_open:
        rebuild_ui()


try:
    _cmd_msbt_quick_menu_repeat.add_argument("player", nargs="?", help="Optional player index, name, or index|name")
except Exception:
    pass


@command("msbt_quick_menu_lock", description="Enable/disable Quick Menu lock-to-player for repeat last drop.")
def _cmd_msbt_quick_menu_lock(_args: Any = None) -> None:
    mode = ""
    target = None
    try:
        mode = str(getattr(_args, "mode", "") or "").strip().lower()
        target = str(getattr(_args, "player", "") or "").strip() or None
    except Exception:
        mode = ""
    if mode in ("off", "0", "false", "clear", "disable"):
        result = backend_actions.set_drop_player_lock(False)
    elif mode in ("on", "1", "true", "enable") or target:
        result = backend_actions.set_drop_player_lock(True, target)
    else:
        lock = backend_actions.get_drop_player_lock()
        result = backend_actions.set_drop_player_lock(not bool(lock.get("enabled")), target)
    _set_status_from_result(result)
    save_layout()
    if STATE.is_open:
        rebuild_ui()


try:
    _cmd_msbt_quick_menu_lock.add_argument("mode", nargs="?", help="on/off/toggle")
    _cmd_msbt_quick_menu_lock.add_argument("player", nargs="?", help="Optional player index/name when enabling")
except Exception:
    pass
