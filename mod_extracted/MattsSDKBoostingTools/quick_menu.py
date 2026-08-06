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
GRID_COLS = quick_menu_registry.GRID_COLS
GRID_ROWS = quick_menu_registry.GRID_ROWS
# Right-pinned dock by default; MOVE / +/- / themes inspired by Azzy UVH booster.
DOCK_W = 700.0
DOCK_X = DESIGN_W - DOCK_W
HEADER_H = 168.0
CELL_W = 210.0
CELL_H = 56.0
CELL_GAP_X = 8.0
CELL_GAP_Y = 6.0
# Strip under the slot grid for live rarity weight sliders + apply controls.
RARITY_RESERVE_H = 230.0
RARITY_SLIDER_KEYS: tuple[tuple[str, str], ...] = (
    ("common", "Com"),
    ("uncommon", "Unc"),
    ("rare", "Rare"),
    ("epic", "Epic"),
    ("legendary", "Leg"),
    ("pearlescent", "Pearl"),
)
BTN_H_HEADER = 44.0
BTN_H_TOOL = 42.0
BTN_H_TAB = 40.0
TEXT_BOOST = 1.15
SCALE_TITLE = 0.68
SCALE_SUBTITLE = 0.36
SCALE_BTN = 0.46
SCALE_BTN_HEADER = 0.42
SCALE_SLOT = 0.38
SCALE_BODY = 0.34
SCALE_HINT = 0.30
SCALE_MODAL_TITLE = 0.48
SCALE_MODAL_BTN = 0.42
C_OUTLINE = (0.02, 0.02, 0.02, 1.0)
# Soft dark-purple halo so white labels stay readable on neon fills (Azzy uses white text).
C_TEXT_OUTLINE = (0.04, 0.02, 0.12, 0.75)
TEXT_OUTLINE_SIZE = 1
TEXT_OUTLINE_OFFSETS: tuple[tuple[float, float], ...] = (
    (-1.0, 0.0),
    (1.0, 0.0),
    (0.0, -1.0),
    (0.0, 1.0),
)
MODAL_BLOCKER_Z = 80
MODAL_PANEL_Z = 81
MODAL_CONTENT_Z = 82
MODAL_BUTTON_Z = 83
ACTION_CATALOG = quick_menu_registry.ACTION_CATALOG
PICKER_ACTIONS = quick_menu_registry.NATIVE_PICKER_ACTIONS
DEFAULT_PAGE_0 = quick_menu_registry.DEFAULT_PAGE_0
WINDOW_SCALE_MIN = quick_menu_registry.WINDOW_SCALE_MIN
WINDOW_SCALE_MAX = quick_menu_registry.WINDOW_SCALE_MAX
WINDOW_SCALE_STEP = quick_menu_registry.WINDOW_SCALE_STEP
THEME_IDS = quick_menu_registry.THEME_IDS
THEME_LABELS = getattr(quick_menu_registry, "THEME_LABELS", {})
MENU_UI_STATE_TAG = "CINEMATIC"
THEME_PICK_THRESHOLD = 8

# Theme packs: (dock, header, edge, btn, gold, danger, muted, slot, slot_sel, slot_empty, text, text_dim)
# Static Azzy hex themes only (no Rainbow/GZO/Cow/Bevey animation).


def _hex(code: str, alpha: float = 0.99) -> tuple[float, float, float, float]:
    code = code.lstrip("#")
    return (
        int(code[0:2], 16) / 255.0,
        int(code[2:4], 16) / 255.0,
        int(code[4:6], 16) / 255.0,
        float(alpha),
    )


def _theme_from_azzy(
    panel: tuple[float, float, float, float],
    accent: tuple[float, float, float, float],
    text_c: tuple[float, float, float, float],
) -> dict[str, tuple[float, float, float, float]]:
    pr, pg, pb, pa = panel
    ar, ag, ab, aa = accent
    tr, tg, tb, ta = text_c
    return {
        "dock": (pr, pg, pb, min(0.98, pa)),
        "header": (ar, ag, ab, aa),
        "edge": (tr, tg, tb, 1.0),
        "btn": (ar * 0.72, ag * 0.72, ab * 0.72, 0.98),
        "gold": (ar, ag, ab, aa),
        "danger": (0.82, 0.10, 0.12, 0.98),
        "muted": (pr * 1.4, pg * 1.4, pb * 1.4, 0.95),
        "slot": (ar * 0.55, ag * 0.55, ab * 0.55, 0.98),
        "slot_sel": (tr, tg, tb, 0.99),
        "slot_empty": (pr * 0.7, pg * 0.7, pb * 0.7, 0.95),
        "text": (tr, tg, tb, ta),
        "text_dim": (tr * 0.78, tg * 0.78, tb * 0.78, 1.0),
        "toast_ok": (0.14, 0.42, 0.22, 1.0),
        "toast_bad": (0.70, 0.14, 0.14, 1.0),
    }


THEMES: dict[str, dict[str, tuple[float, float, float, float]]] = {
    # Default — true Azzy Purple panel (#0A0345) + mixed neon action tiles.
    "msbt_bright": {
        "dock": _hex("0A0345", 0.98),
        "header": _hex("ff2d6f", 1.0),
        "edge": _hex("6ff2ff", 1.0),
        "btn": _hex("00e5ff", 0.99),
        "gold": _hex("ff2d6f", 1.0),
        "danger": _hex("ff1493", 1.0),
        "muted": _hex("2a0a4a", 0.96),
        "slot": _hex("00e5ff", 0.99),
        "slot_sel": _hex("7cff2e", 1.0),
        "slot_empty": _hex("1a0840", 0.95),
        "text": _hex("ffffff", 1.0),
        "text_dim": _hex("6ff2ff", 1.0),
        "toast_ok": _hex("7cff2e", 1.0),
        "toast_bad": _hex("ff2d6f", 1.0),
    },
    "msbt": {
        "dock": (0.05, 0.03, 0.02, 1.0),
        "header": (0.72, 0.14, 0.05, 1.0),
        "edge": (1.0, 0.72, 0.12, 1.0),
        "btn": (0.88, 0.38, 0.06, 1.0),
        "gold": (1.0, 0.78, 0.12, 1.0),
        "danger": (0.82, 0.12, 0.08, 1.0),
        "muted": (0.22, 0.12, 0.08, 1.0),
        "slot": (0.62, 0.24, 0.06, 1.0),
        "slot_sel": (1.0, 0.82, 0.18, 1.0),
        "slot_empty": (0.14, 0.08, 0.05, 1.0),
        "text": (1.0, 0.96, 0.88, 1.0),
        "text_dim": (0.96, 0.84, 0.62, 1.0),
        "toast_ok": (0.55, 0.28, 0.05, 1.0),
        "toast_bad": (0.70, 0.12, 0.10, 1.0),
    },
    "blackberry": _theme_from_azzy(_hex("140428"), _hex("6a1fb0"), _hex("9ef29a")),
    "azzy_purple": {
        "dock": _hex("0A0345", 0.98),
        "header": _hex("ff2d6f", 1.0),
        "edge": _hex("6ff2ff", 1.0),
        "btn": _hex("00e5ff", 0.99),
        "gold": _hex("ff2d6f", 1.0),
        "danger": _hex("ff1493", 1.0),
        "muted": _hex("2a0a4a", 0.96),
        "slot": _hex("00e5ff", 0.99),
        "slot_sel": _hex("7cff2e", 1.0),
        "slot_empty": _hex("1a0840", 0.95),
        "text": _hex("ffffff", 1.0),
        "text_dim": _hex("6ff2ff", 1.0),
        "toast_ok": _hex("7cff2e", 1.0),
        "toast_bad": _hex("ff2d6f", 1.0),
    },
    "basic_default": _theme_from_azzy(_hex("1a1a2e"), _hex("4a90e2"), _hex("cfe4ff")),
    "arctic": _theme_from_azzy(_hex("0a1628"), _hex("4fc3f7"), _hex("e8fbff")),
    "inferno": _theme_from_azzy(_hex("1a0a0a"), _hex("ff6b6b"), _hex("ffd0d0")),
    "void": _theme_from_azzy(_hex("060a15"), _hex("a78bfa"), _hex("ded0ff")),
    "explosive": _theme_from_azzy(_hex("2a1a0a"), _hex("ffa366"), _hex("ffe0c8")),
    "healing": _theme_from_azzy(_hex("0a2a1a"), _hex("66ddd6"), _hex("d6fff8")),
    "fortress": _theme_from_azzy(_hex("1a2a3a"), _hex("7c9cc8"), _hex("dbe7f7")),
    "legendary": _theme_from_azzy(_hex("0a1628"), _hex("ffd700"), _hex("fff3b0")),
    "mystic": _theme_from_azzy(_hex("1a0f2a"), _hex("a569bd"), _hex("e8d4f5")),
    "scooters": _theme_from_azzy(_hex("02030a"), _hex("00f3ff"), _hex("a8ffff")),
    "cosmic": _theme_from_azzy(_hex("0a0014"), _hex("00ffff"), _hex("9fffff")),
    "midnight": _theme_from_azzy(_hex("000033"), _hex("4682b4"), _hex("d4e4ff")),
    "venom": _theme_from_azzy(_hex("0a0a0a"), _hex("00ff00"), _hex("b9ffb9")),
    "skullmasher": _theme_from_azzy(_hex("1a0000"), _hex("ff3300"), _hex("ff8a65")),
    "lootlobby": _theme_from_azzy(_hex("1a0033"), _hex("ff69b4"), _hex("ffe0f5")),
    "rat_bastard": _theme_from_azzy(_hex("120a18"), _hex("6fae3a"), _hex("cfe8a6")),
    "playas_darkness": _theme_from_azzy(_hex("1d0a2e"), _hex("7b3ff2"), _hex("e3b6f5")),
    "halloween": _theme_from_azzy(_hex("120a04"), _hex("ff7518"), _hex("ffd9a0")),
    "merry_mephisto": _theme_from_azzy(_hex("0a0506"), _hex("c1121f"), _hex("f5f0ee")),
}

# Azzy-style mixed neon fills for action slots (lime / pink / cyan / purple — no mustard).
NEON_SLOT_CYCLE: tuple[tuple[float, float, float, float], ...] = (
    _hex("00e5ff", 0.99),
    _hex("7cff2e", 0.99),
    _hex("ff2d6f", 0.99),
    _hex("00d4c8", 0.99),
    _hex("d9a1f8", 0.99),
    _hex("b5fba2", 0.99),
)


def neon_slot_fill(index: int) -> tuple[float, float, float, float]:
    """Rotate neon hues across the action grid like Azzy's per-button colors."""
    if not NEON_SLOT_CYCLE:
        return C_SLOT
    return NEON_SLOT_CYCLE[int(index) % len(NEON_SLOT_CYCLE)]


def action_slot_fill(*, index: int, selected: bool, empty: bool) -> tuple[float, float, float, float]:
    """Filled slots: Azzy neon cycle on neon themes; otherwise solid theme slot color."""
    if empty:
        return C_SLOT_EMPTY
    if selected:
        return C_SLOT_SEL
    if STATE.theme_id in ("msbt_bright", "azzy_purple"):
        return neon_slot_fill(index)
    return C_SLOT

# Active palette (mutated by apply_theme).
C_DOCK = THEMES["msbt_bright"]["dock"]
C_HEADER = THEMES["msbt_bright"]["header"]
C_EDGE = THEMES["msbt_bright"]["edge"]
C_BTN = THEMES["msbt_bright"]["btn"]
C_BTN_GOLD = THEMES["msbt_bright"]["gold"]
C_BTN_DANGER = THEMES["msbt_bright"]["danger"]
C_BTN_MUTED = THEMES["msbt_bright"]["muted"]
C_SLOT = THEMES["msbt_bright"]["slot"]
C_SLOT_SEL = THEMES["msbt_bright"]["slot_sel"]
C_SLOT_EMPTY = THEMES["msbt_bright"]["slot_empty"]
C_TEXT = THEMES["msbt_bright"]["text"]
C_TEXT_DIM = THEMES["msbt_bright"]["text_dim"]
C_TOAST_OK = THEMES["msbt_bright"]["toast_ok"]
C_TOAST_BAD = THEMES["msbt_bright"]["toast_bad"]


@dataclass
class ButtonRef:
    widget: Any
    action: Callable[[], None]
    label: str
    enabled: bool = True
    was_pressed: bool = False
    modal_only: bool = False
    allow_when_modal: bool = False
    rect: tuple[float, float, float, float] | None = None
    manual_was_down: bool = False


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
    modal: str = ""  # "", "player_pick", "action_pick", "label_edit", "theme_pick", "serial_pick", "inv_detail"
    main_tab: str = "actions"  # "actions" | "inventory"
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
    window_scale: float = 1.0
    theme_id: str = "msbt_bright"
    offset_x: float = 0.0
    offset_y: float = 0.0
    placing: bool = False
    place_click_was_down: bool = False
    place_started_at: float = 0.0
    place_mouse0: tuple[float, float] | None = None
    place_offset0: tuple[float, float] = (0.0, 0.0)
    place_last_rebuild: float = 0.0
    place_catcher: Any = None
    overlay: Any = None
    tree: Any = None
    root: Any = None
    menu_canvas: Any = None
    buttons: list[ButtonRef] = field(default_factory=list)
    sliders: list[SliderRef] = field(default_factory=list)
    panel_opacity: float = 1.0
    rarity_panel_equipped: bool = False
    rarity_weights: dict[str, float] = field(
        default_factory=lambda: {key: 1.0 for key, _label in RARITY_SLIDER_KEYS}
    )
    rarity_live_apply_due: float = 0.0
    rarity_local_edit_until: float = 0.0
    rarity_backend_sync_at: float = 0.0
    input_owner: Any = None
    input_snapshot: InputSnapshot = field(default_factory=InputSnapshot)
    last_input_refresh: float = 0.0
    last_layout_check: float = 0.0
    layout_revision: int = 0
    ui_dirty: bool = False
    key_escape: bool = False
    key_f7: bool = False
    key_f6: bool = False
    hotkey_ignore_until: float = 0.0
    started: bool = False
    # NMM-style CINEMATIC UI state + Esc release-gated close.
    pushed_cinematic_tag: bool = False
    escape_pending_close: bool = False
    escape_pending_release_seen_at: float = 0.0
    escape_block_until: float = 0.0
    escape_block_wait_release: bool = False
    escape_defer_ui_pop: bool = False
    # Per-slot hotkey capture (Edit → slot → Bind Hotkey).
    hotkey_listen: bool = False
    hotkey_listen_started_at: float = 0.0
    hotkey_key_state: dict[str, bool] = field(default_factory=dict)
    slot_hotkey_was_down: dict[str, bool] = field(default_factory=dict)
    # Inventory tab (MSBT browser mirror)
    inv_equipped: list[dict[str, Any]] = field(default_factory=list)
    inv_backpack: list[dict[str, Any]] = field(default_factory=list)
    inv_sort: str = "recent"
    inv_sort_dir: str = "desc"
    inv_category: str = "All"
    inv_page: int = 0
    inv_page_size: int = 16
    inv_selected_key: str = ""
    inv_selected_entry: dict[str, Any] | None = None
    inv_give_target: int | None = None
    inv_multiplier: int = 1
    inv_truncated: bool = False
    inv_reading: str = ""


def apply_theme(theme_id: str | None = None) -> str:
    global C_DOCK, C_HEADER, C_EDGE, C_BTN, C_BTN_GOLD, C_BTN_DANGER, C_BTN_MUTED
    global C_SLOT, C_SLOT_SEL, C_SLOT_EMPTY, C_TEXT, C_TEXT_DIM, C_TOAST_OK, C_TOAST_BAD
    tid = str(theme_id or STATE.theme_id or "msbt_bright").strip().lower()
    if tid not in THEMES:
        tid = "msbt_bright"
    STATE.theme_id = tid
    pack = THEMES[tid]
    C_DOCK = pack["dock"]
    C_HEADER = pack["header"]
    C_EDGE = pack["edge"]
    C_BTN = pack["btn"]
    C_BTN_GOLD = pack["gold"]
    C_BTN_DANGER = pack["danger"]
    C_BTN_MUTED = pack["muted"]
    C_SLOT = pack["slot"]
    C_SLOT_SEL = pack["slot_sel"]
    C_SLOT_EMPTY = pack["slot_empty"]
    C_TEXT = pack["text"]
    C_TEXT_DIM = pack["text_dim"]
    C_TOAST_OK = pack["toast_ok"]
    C_TOAST_BAD = pack["toast_bad"]
    return tid


def panel_x() -> float:
    return float(DOCK_X + STATE.offset_x)


def panel_y() -> float:
    return float(STATE.offset_y)


def panel_w() -> float:
    return float(DOCK_W)


def _with_alpha(fill: tuple[float, float, float, float], alpha: float) -> tuple[float, float, float, float]:
    r, g, b, _a = fill
    return (float(r), float(g), float(b), max(0.55, min(1.0, float(alpha))))


STATE = QuickMenuState()

_NEEDS_PLAYER_ACTIONS = quick_menu_registry.NEEDS_PLAYER_ACTIONS


def scaled_rect(x: float, y: float, w: float, h: float) -> tuple[float, float, float, float]:
    """Hit rect in the same space as _mouse_viewport_pos / MOVE placement."""
    return (sx(x), sy(y), sx(w), sy(h))


def rect_contains(rect: Any, x: float, y: float) -> bool:
    try:
        rx, ry, rw, rh = rect
        return float(rx) <= x <= float(rx) + float(rw) and float(ry) <= y <= float(ry) + float(rh)
    except Exception:
        return False


def normalize_ui_state_tag(tag: str) -> str:
    value = str(tag or "").strip()
    if value.startswith("UI.Tag."):
        return value.split(".")[-1]
    return value or MENU_UI_STATE_TAG


def run_kismet_console_command(command_text: str) -> bool:
    command_text = str(command_text or "").strip()
    if not command_text:
        return False
    try:
        ksl = class_obj("/Script/Engine.KismetSystemLibrary").ClassDefaultObject
    except Exception:
        ksl = None
    if ksl is None:
        return False
    pc = None
    try:
        pc = get_pc()
    except Exception:
        pc = None
    world_context = pc
    if world_context is None:
        try:
            world_context = unrealsdk.find_object("Engine", "/Engine/Transient.Engine_0")
        except Exception:
            world_context = None
    if world_context is None:
        return False
    try:
        ksl.ExecuteConsoleCommand(world_context, command_text, pc)
        return True
    except Exception as exc:
        _log(f"Kismet console command failed: {command_text}: {exc}")
        return False


def run_ui_state_console_command(action: str, tag: str) -> bool:
    normalized = normalize_ui_state_tag(tag)
    return run_kismet_console_command(f"gbx.ui.view.{action} {normalized}")


def push_menu_ui_state() -> None:
    if STATE.pushed_cinematic_tag:
        return
    if run_ui_state_console_command("stateadd", MENU_UI_STATE_TAG):
        STATE.pushed_cinematic_tag = True
        _log(f"Pushed UI state {normalize_ui_state_tag(MENU_UI_STATE_TAG)}")


def pop_menu_ui_state() -> None:
    if not STATE.pushed_cinematic_tag:
        return
    try:
        run_ui_state_console_command("stateremove", MENU_UI_STATE_TAG)
        _log(f"Popped UI state {normalize_ui_state_tag(MENU_UI_STATE_TAG)}")
    finally:
        STATE.pushed_cinematic_tag = False


def begin_escape_close_block(duration: float = 1.25) -> None:
    STATE.escape_block_wait_release = True
    STATE.escape_block_until = max(STATE.escape_block_until, time.monotonic() + float(duration))


def update_escape_close_block(pc: Any = None) -> None:
    """Esc release-gated close so pause does not also consume Esc."""
    now = time.monotonic()
    if pc is None:
        try:
            pc = get_pc()
        except Exception:
            pc = None

    if STATE.escape_pending_close:
        released = not _key_down(pc, "Escape")
        if released and STATE.escape_pending_release_seen_at <= 0.0:
            STATE.escape_pending_release_seen_at = now
            STATE.escape_block_until = max(STATE.escape_block_until, now + 0.35)
        if STATE.escape_pending_release_seen_at > 0.0 and now - STATE.escape_pending_release_seen_at >= 0.08:
            STATE.escape_pending_close = False
            STATE.escape_pending_release_seen_at = 0.0
            # Keep CINEMATIC briefly after Esc close so pause does not also dismiss.
            close_panel(defer_ui_state_pop=True)
            STATE.escape_defer_ui_pop = True
            STATE.escape_block_wait_release = True
            STATE.escape_block_until = max(STATE.escape_block_until, now + 0.85)
        return

    if not STATE.escape_block_wait_release:
        return
    released = not _key_down(pc, "Escape")
    timed_out = now >= STATE.escape_block_until
    if released or timed_out:
        STATE.escape_block_wait_release = False
        STATE.escape_block_until = max(STATE.escape_block_until, now + 0.20)
        if STATE.escape_defer_ui_pop:
            STATE.escape_defer_ui_pop = False
            try:
                pop_menu_ui_state()
            except Exception as exc:
                _log(f"Deferred UI state pop skipped: {exc}")



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


def _apply_text_outline(widget: Any) -> None:
    """Best-effort UMG TextBlock outline + drop shadow (FontOutlineSettings)."""
    outline_c = color(C_TEXT_OUTLINE)
    try:
        font = widget.Font
        try:
            settings = unrealsdk.make_struct(
                "FontOutlineSettings",
                OutlineSize=int(TEXT_OUTLINE_SIZE),
                bSeparateFillAlpha=False,
                bApplyOutlineToDropShadows=False,
                OutlineColor=outline_c,
            )
            font.OutlineSettings = settings
        except Exception:
            try:
                outline_settings = font.OutlineSettings
                outline_settings.OutlineSize = int(TEXT_OUTLINE_SIZE)
                outline_settings.OutlineColor = outline_c
            except Exception:
                pass
        if not try_call(widget, "SetFont", font):
            try:
                widget.Font = font
            except Exception:
                pass
    except Exception:
        pass
    # Single-direction shadow still helps when OutlineSettings is ignored.
    try_call(widget, "SetShadowOffset", vec2(1.0, 1.0))
    try_call(widget, "SetShadowColorAndOpacity", outline_c)


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
    return float(value) * STATE.scale_x * float(STATE.window_scale or 1.0)


def sy(value: float) -> float:
    return float(value) * STATE.scale_y * float(STATE.window_scale or 1.0)


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
    base = max(0.5, min(3.0, min(STATE.scale_x, STATE.scale_y)))
    STATE.ui_scale = max(0.4, min(3.5, base * float(STATE.window_scale or 1.0)))


def _empty_page() -> list[dict[str, Any] | None]:
    return quick_menu_registry.empty_page()


def _normalize_slot(raw: object) -> dict[str, Any] | None:
    return quick_menu_registry.normalize_slot(raw)


def _default_pages() -> list[list[dict[str, Any] | None]]:
    return quick_menu_registry.default_pages()


def _apply_chrome(chrome: dict[str, Any] | None) -> None:
    data = quick_menu_registry.sanitize_chrome(chrome or {})
    STATE.theme_id = str(data.get("theme_id") or "msbt_bright")
    STATE.window_scale = float(data.get("window_scale") or 1.0)
    STATE.offset_x = float(data.get("offset_x") or 0.0)
    STATE.offset_y = float(data.get("offset_y") or 0.0)
    STATE.panel_opacity = float(data.get("panel_opacity") or 1.0)
    STATE.rarity_panel_equipped = bool(data.get("rarity_panel_equipped", False))
    apply_theme(STATE.theme_id)
    update_layout_metrics()


def _chrome_payload() -> dict[str, Any]:
    return {
        "theme_id": STATE.theme_id,
        "window_scale": float(STATE.window_scale),
        "offset_x": float(STATE.offset_x),
        "offset_y": float(STATE.offset_y),
        "panel_opacity": float(STATE.panel_opacity),
        "rarity_panel_equipped": bool(STATE.rarity_panel_equipped),
    }


def load_layout() -> None:
    layout = quick_menu_registry.load_persisted_layout()
    STATE.pages = layout["pages"]
    STATE.page = int(layout["page"])
    STATE.edit_mode = bool(layout["edit_mode"])
    STATE.layout_revision = quick_menu_registry.get_layout_revision()
    _apply_chrome(layout.get("chrome"))
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
        "chrome": _chrome_payload(),
    }
    try:
        result = quick_menu_registry.set_quick_menu_layout(payload)
        if not result.get("ok"):
            raise RuntimeError(result.get("message") or "Quick Menu layout validation failed.")
        STATE.pages = result["layout"]["pages"]
        _apply_chrome(result["layout"].get("chrome"))
        STATE.layout_revision = quick_menu_registry.get_layout_revision()
    except Exception as exc:
        _log(f"Could not save Quick Menu layout: {exc!r}")


def slot_label(slot: dict[str, Any] | None) -> str:
    return quick_menu_registry.slot_label(slot)


def slot_button_label(slot: dict[str, Any] | None) -> str:
    base = slot_label(slot)
    if slot is None:
        return base
    hot = quick_menu_registry.hotkey_display(str(slot.get("hotkey") or ""))
    if not hot:
        return base
    return f"{base} [{hot}]"


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
        self.slot(widget, panel_x(), panel_y(), panel_w(), DESIGN_H, MODAL_BLOCKER_Z)
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
        min_value: float = 0.55,
        max_value: float = 1.0,
        step: float = 0.01,
        label_widget: Any = None,
    ) -> Any:
        widget = self.widget("/Script/UMG.Slider")
        lo = float(min_value)
        hi = float(max_value)
        if hi <= lo:
            hi = lo + 0.01
        clamped = max(lo, min(hi, float(value)))
        try_call(widget, "SetMinValue", lo)
        try_call(widget, "SetMaxValue", hi)
        try_call(widget, "SetStepSize", float(step))
        try_call(widget, "SetValue", clamped)
        try_call(widget, "SetVisibility", 0)
        try_call(widget, "SetIsEnabled", True)
        self.add(parent, widget)
        self.slot(widget, x, y, w, h, z)
        STATE.sliders.append(SliderRef(widget, key, clamped, label_widget))
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

    def _text_block(
        self,
        parent: Any,
        value: str,
        x: float,
        y: float,
        w: float,
        h: float,
        *,
        scale: float,
        z: int,
        center: bool,
        tint: tuple[float, float, float, float],
        outline: bool,
    ) -> Any:
        widget = self.widget("/Script/UMG.TextBlock")
        try_call(widget, "SetText", str(value))
        render_scale = max(0.2, float(scale) * STATE.ui_scale * TEXT_BOOST)
        try_call(widget, "SetRenderScale", vec2(render_scale, render_scale))
        try_call(widget, "SetRenderTransformPivot", vec2(0.0, 0.5))
        try_call(widget, "SetJustification", 1 if center else 0)
        try_call(widget, "SetColorAndOpacity", slate_color(tint))
        try_call(widget, "SetVisibility", 4)
        if outline:
            _apply_text_outline(widget)
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
        scale: float = 0.60,
        z: int = 10,
        center: bool = False,
        tint: tuple[float, float, float, float] = C_TEXT,
    ) -> Any:
        # Dual-pass cardinal halo so labels stay readable even when native
        # FontOutlineSettings is ignored; fill pass also gets SetFont outline.
        for ox, oy in TEXT_OUTLINE_OFFSETS:
            self._text_block(
                parent,
                value,
                x + ox,
                y + oy,
                w,
                h,
                scale=scale,
                z=z,
                center=center,
                tint=C_TEXT_OUTLINE,
                outline=False,
            )
        return self._text_block(
            parent,
            value,
            x,
            y,
            w,
            h,
            scale=scale,
            z=z + 1,
            center=center,
            tint=tint,
            outline=True,
        )

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
        scale: float = SCALE_BTN,
        modal_only: bool = False,
        allow_when_modal: bool = False,
    ) -> Any:
        # Modal backdrops render below MODAL_BUTTON_Z. Keep every modal button
        # (including global Close when a modal is active)
        # its hit target and label) above that layer; otherwise the modal title
        # is visible while player/action rows appear as a blank screen.
        layer = _button_layer(z, modal_only, allow_when_modal)
        base = fill if enabled else C_BTN_MUTED
        # Near-black outline behind the fill so buttons read clearly on dark docks.
        self.border(parent, x - 2, y - 2, w + 4, h + 4, C_OUTLINE, layer)
        self.border(parent, x, y, w, h, base, layer + 0)
        widget = self.widget("/Script/UMG.Button")
        self.add(parent, widget)
        self.slot(widget, x, y, w, h, layer + 1)
        try_call(widget, "SetVisibility", 0)
        try_call(widget, "SetIsEnabled", bool(enabled))
        try_call(widget, "SetRenderOpacity", 0.03 if enabled else 0.01)
        # Azzy pads labels ~8/10 inside the hit rect so larger type stays readable.
        self.text(
            parent,
            label,
            x + 8,
            y + 8,
            w - 16,
            h - 14,
            scale=scale,
            z=layer + 2,
            center=True,
        )
        STATE.buttons.append(
            ButtonRef(
                widget,
                action,
                label,
                enabled,
                False,
                modal_only,
                allow_when_modal,
                rect=scaled_rect(x, y, w, h),
                manual_was_down=False,
            )
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
    """Force-close the Quick Menu and restore normal game mouse/look/move input.

    Use this when the cursor stays stuck on screen after the menu, or camera/
    movement input feels locked. Safer than only pressing Close if UI input
    capture failed partway through.
    """
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
    STATE.key_escape = False
    STATE.key_f7 = False
    STATE.key_f6 = False
    STATE.escape_pending_close = False
    STATE.escape_defer_ui_pop = False
    try:
        pop_menu_ui_state()
    except Exception:
        pass
    _log("Quick Menu unstuck complete (GameOnly restored).")
    show_toast("Unstuck: menu closed, game input restored.", ok=True, seconds=2.4)


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
    factory.text(root, message, 480, 52, 960, 40, scale=SCALE_BTN, z=11, center=True)


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
    if result.get("open_serial_pick") and STATE.is_open:
        STATE.modal = "serial_pick"
    if action == "read_inventory" and result.get("ok"):
        from . import quick_menu_inventory

        quick_menu_inventory.apply_inventory_result(result)
        STATE.main_tab = "inventory"
    return result


def _sync_rarity_weights_from_backend() -> None:
    weights = backend_actions.get_rarity_weights()
    for key, _label in RARITY_SLIDER_KEYS:
        try:
            STATE.rarity_weights[key] = max(0.0, min(1.0, float(weights.get(key, 1.0))))
        except Exception:
            STATE.rarity_weights[key] = 1.0


def _rarity_payload_from_state() -> dict[str, float]:
    return {
        f"rarity_{key}_percent": float(round(max(0.0, min(1.0, float(STATE.rarity_weights.get(key, 1.0)))) * 100.0, 1))
        for key, _label in RARITY_SLIDER_KEYS
    }


def _qm_rarity_apply() -> None:
    STATE.rarity_live_apply_due = 0.0
    STATE.rarity_local_edit_until = time.monotonic() + 0.45
    result = backend_actions.rarity_apply(_rarity_payload_from_state())
    _sync_rarity_weights_from_backend()
    _set_status_from_result(result)
    STATE.ui_dirty = True


def _qm_rarity_reset() -> None:
    STATE.rarity_live_apply_due = 0.0
    STATE.rarity_local_edit_until = time.monotonic() + 0.45
    result = backend_actions.rarity_reset()
    _sync_rarity_weights_from_backend()
    _set_status_from_result(result)
    STATE.ui_dirty = True


def _qm_rarity_only(key: str) -> None:
    STATE.rarity_live_apply_due = 0.0
    STATE.rarity_local_edit_until = time.monotonic() + 0.45
    result = backend_actions.rarity_only(key)
    _sync_rarity_weights_from_backend()
    _set_status_from_result(result)
    STATE.ui_dirty = True


def _render_rarity_controls(factory: NativeUMG, root: Any, px: float, rarity_y: float, pw: float, opacity: float) -> None:
    factory.border(root, px + 12, rarity_y, pw - 24, RARITY_RESERVE_H, C_OUTLINE, 4)
    factory.border(root, px + 15, rarity_y + 3, pw - 30, RARITY_RESERVE_H - 6, _with_alpha(C_BTN_MUTED, opacity), 4)
    factory.text(
        root,
        "Rarity weights (100% = normal, 0% = off)",
        px + 20,
        rarity_y + 8,
        pw - 40,
        24,
        scale=SCALE_BODY,
        z=6,
        tint=C_BTN_GOLD,
    )
    btn_y = rarity_y + 36
    btn_h = 34.0
    factory.button(
        root, "Apply", px + 18, btn_y, 100, btn_h,
        _qm_rarity_apply, fill=_with_alpha(C_BTN_GOLD, opacity), scale=SCALE_HINT,
    )
    factory.button(
        root, "Reset", px + 126, btn_y, 90, btn_h,
        _qm_rarity_reset, fill=_with_alpha(C_BTN, opacity), scale=SCALE_HINT,
    )
    factory.button(
        root, "Leg Only", px + 224, btn_y, 110, btn_h,
        lambda: _qm_rarity_only("legendary"), fill=_with_alpha(C_BTN, opacity), scale=SCALE_HINT,
    )
    factory.button(
        root, "Pearl Only", px + 342, btn_y, 120, btn_h,
        lambda: _qm_rarity_only("pearlescent"), fill=_with_alpha(C_BTN, opacity), scale=SCALE_HINT,
    )

    cols = 3
    col_w = (pw - 48) / cols
    row0 = rarity_y + 80
    for idx, (key, short) in enumerate(RARITY_SLIDER_KEYS):
        row, col = divmod(idx, cols)
        x0 = px + 20 + col * col_w
        y0 = row0 + row * 68
        weight = max(0.0, min(1.0, float(STATE.rarity_weights.get(key, 1.0))))
        pct = int(round(weight * 100.0))
        label = factory.text(
            root,
            f"{short} {pct}%",
            x0,
            y0,
            col_w - 16,
            22,
            scale=SCALE_HINT,
            z=6,
            tint=C_TEXT,
        )
        factory.border(root, x0, y0 + 24, col_w - 20, 24, C_OUTLINE, 5)
        factory.border(root, x0 + 2, y0 + 26, col_w - 24, 20, _with_alpha(C_SLOT_EMPTY, opacity), 5)
        factory.slider(
            root,
            f"rarity_{key}",
            weight,
            x0 + 4,
            y0 + 26,
            col_w - 28,
            20,
            z=7,
            min_value=0.0,
            max_value=1.0,
            step=0.01,
            label_widget=label,
        )


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
        "hotkey": "",
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
    cancel_hotkey_listen()
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
    cancel_hotkey_listen()
    STATE.pages[STATE.page][STATE.selected_slot] = None
    STATE.modal = ""
    save_layout()
    _log(f"Cleared slot {STATE.selected_slot + 1}.")
    rebuild_ui()


def begin_hotkey_listen() -> None:
    if STATE.selected_slot is None:
        return
    slot = STATE.pages[STATE.page][STATE.selected_slot]
    if slot is None:
        show_toast("Assign an action before binding a hotkey.", ok=False, seconds=2.0)
        return
    STATE.hotkey_listen = True
    STATE.hotkey_listen_started_at = time.monotonic()
    STATE.hotkey_key_state = {key: False for key in quick_menu_registry.HOTKEY_KEY_NAMES}
    # Snapshot currently held keys so releasing them does not bind.
    pc = get_pc()
    for key in quick_menu_registry.HOTKEY_KEY_NAMES:
        STATE.hotkey_key_state[key] = _key_down(pc, key)
    show_toast("Press a key to bind (Esc clears).", ok=True, seconds=2.0)
    rebuild_ui()


def cancel_hotkey_listen() -> None:
    STATE.hotkey_listen = False
    STATE.hotkey_listen_started_at = 0.0
    STATE.hotkey_key_state.clear()


def clear_selected_hotkey() -> None:
    cancel_hotkey_listen()
    if STATE.selected_slot is None:
        return
    slot = STATE.pages[STATE.page][STATE.selected_slot]
    if slot is None:
        return
    slot["hotkey"] = ""
    save_layout()
    show_toast("Hotkey cleared.", ok=True, seconds=1.4)
    rebuild_ui()


def _clear_hotkey_conflicts(key_name: str, *, keep_page: int, keep_slot: int) -> None:
    key = str(key_name or "").strip()
    if not key:
        return
    for page_i, page in enumerate(STATE.pages):
        for slot_i, slot in enumerate(page):
            if slot is None:
                continue
            if page_i == keep_page and slot_i == keep_slot:
                continue
            if str(slot.get("hotkey") or "") == key:
                slot["hotkey"] = ""


def finish_hotkey_bind(key_name: str) -> None:
    raw = str(key_name or "").strip()
    if STATE.selected_slot is None:
        cancel_hotkey_listen()
        return
    slot = STATE.pages[STATE.page][STATE.selected_slot]
    if slot is None:
        cancel_hotkey_listen()
        return
    if raw in ("Escape", "Esc") or raw in quick_menu_registry.HOTKEY_RESERVED:
        slot["hotkey"] = ""
        cancel_hotkey_listen()
        save_layout()
        show_toast("Hotkey cleared.", ok=True, seconds=1.4)
        rebuild_ui()
        return
    normalized = quick_menu_registry.normalize_hotkey(raw)
    if not normalized:
        show_toast(f"Key not allowed: {raw}", ok=False, seconds=1.8)
        cancel_hotkey_listen()
        rebuild_ui()
        return
    _clear_hotkey_conflicts(normalized, keep_page=STATE.page, keep_slot=int(STATE.selected_slot))
    slot["hotkey"] = normalized
    cancel_hotkey_listen()
    save_layout()
    show_toast(f"Bound {quick_menu_registry.hotkey_display(normalized)}", ok=True, seconds=1.6)
    rebuild_ui()


def poll_hotkey_listen() -> None:
    """Capture a key while Edit → slot Bind Hotkey is active (camera tick)."""
    if not STATE.hotkey_listen or not STATE.is_open:
        return
    if STATE.modal != "label_edit":
        cancel_hotkey_listen()
        return
    # Ignore the click that opened listen for a short grace window.
    if time.monotonic() < float(STATE.hotkey_listen_started_at or 0.0) + 0.18:
        pc = get_pc()
        for key in quick_menu_registry.HOTKEY_KEY_NAMES:
            STATE.hotkey_key_state[key] = _key_down(pc, key)
        return
    pc = get_pc()
    if pc is None:
        return
    # Esc clears even though it is reserved for runtime hotkeys.
    esc_down = _key_down(pc, "Escape")
    esc_was = bool(STATE.hotkey_key_state.get("Escape", False))
    STATE.hotkey_key_state["Escape"] = esc_down
    if esc_down and not esc_was:
        finish_hotkey_bind("Escape")
        return
    for key_name in quick_menu_registry.HOTKEY_KEY_NAMES:
        down = _key_down(pc, key_name)
        was = bool(STATE.hotkey_key_state.get(key_name, False))
        STATE.hotkey_key_state[key_name] = down
        if down and not was:
            finish_hotkey_bind(key_name)
            return


def process_slot_hotkeys() -> None:
    """Fire assigned slot hotkeys while Quick Menu is closed (camera tick)."""
    if STATE.is_open or STATE.hotkey_listen:
        STATE.slot_hotkey_was_down.clear()
        return
    if time.monotonic() < float(STATE.hotkey_ignore_until or 0.0):
        return
    pc = get_pc()
    if pc is None:
        STATE.slot_hotkey_was_down.clear()
        return
    seen: set[str] = set()
    for page in STATE.pages:
        for slot in page:
            if slot is None:
                continue
            key = str(slot.get("hotkey") or "").strip()
            if not key or key in seen:
                continue
            seen.add(key)
            down = _key_down(pc, key)
            was = bool(STATE.slot_hotkey_was_down.get(key, False))
            STATE.slot_hotkey_was_down[key] = down
            if down and not was:
                action = str(slot.get("action") or "")
                payload = dict(slot.get("payload") or {})
                try:
                    _run_action(action, payload)
                except Exception as exc:
                    _log(f"Slot hotkey '{key}' failed: {exc!r}")
                return
    # Drop stale key edges no longer bound.
    stale = [k for k in STATE.slot_hotkey_was_down if k not in seen]
    for key in stale:
        STATE.slot_hotkey_was_down.pop(key, None)


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
        "hotkey": "",
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


def _toggle_header_player_slot(index: int) -> None:
    """Azzy-style P1-P4: select that party slot as the MSBT target (single-select backend)."""
    players = backend_actions.refresh_players()
    match = next((p for p in players if int(p.get("index", -1)) == int(index)), None)
    if match is None:
        show_toast(f"P{index + 1}: no player in that slot", ok=False, seconds=1.8)
        rebuild_ui()
        return
    current = backend_actions.get_selected_player_index()
    if current is not None and int(current) == int(index):
        show_toast(f"Target already P{index + 1}: {match.get('name')}", ok=True, seconds=1.4)
        rebuild_ui()
        return
    result = backend_actions.set_target_player(f"{index}|{match.get('name') or ''}")
    _set_status_from_result(result)
    rebuild_ui()


def _toggle_header_player_all() -> None:
    """PAll: prefer host/auto target via ensure_selected_player (backend is single-select)."""
    result = backend_actions.ensure_selected_player(prefer_host=True)
    if not result.get("ok"):
        players = backend_actions.refresh_players()
        if players:
            first = players[0]
            result = backend_actions.set_target_player(
                f"{int(first.get('index', 0))}|{first.get('name') or ''}"
            )
    _set_status_from_result(result)
    rebuild_ui()


def rebuild_ui() -> None:
    if not STATE.is_open:
        return
    STATE.ui_dirty = False
    factory, root = reset_canvas()
    STATE.sliders.clear()
    opacity = max(0.55, min(1.0, float(STATE.panel_opacity or 1.0)))
    px = panel_x()
    py = panel_y()
    pw = panel_w()

    factory.border(root, px - 6, py, 6, DESIGN_H, _with_alpha(C_EDGE, 1.0), 1)
    factory.border(root, px, py, pw, DESIGN_H, _with_alpha(C_DOCK, opacity), 2)
    factory.border(root, px, py, pw, HEADER_H, _with_alpha(C_HEADER, opacity), 3)
    factory.text(root, "MSBT Quick Menu", px + 12, py + 8, 280, 36, scale=SCALE_TITLE, z=4)
    mode = "EDIT" if STATE.edit_mode else "RUN"
    lock = backend_actions.get_drop_player_lock()
    lock_txt = f"Lock {lock.get('name') or 'ON'}" if lock.get("enabled") else "Lock OFF"
    tab_label = "INV" if STATE.main_tab == "inventory" else f"P{STATE.page + 1}/{MAX_PAGES}"
    factory.text(
        root,
        f"{mode} | {tab_label} | {lock_txt} | {STATE.window_scale:.2f}x | {theme_label(STATE.theme_id)}",
        px + 12,
        py + 42,
        pw - 24,
        24,
        scale=SCALE_SUBTITLE,
        z=4,
        tint=C_TEXT_DIM,
    )

    chrome_y = py + 68
    factory.button(root, "MOVE", px + 12, chrome_y, 72, BTN_H_HEADER, begin_move_placement, fill=_with_alpha(C_BTN, opacity), scale=SCALE_BTN_HEADER, allow_when_modal=True)
    factory.button(root, "THEME", px + 90, chrome_y, 84, BTN_H_HEADER, cycle_theme, fill=_with_alpha(C_BTN_GOLD, opacity), scale=SCALE_BTN_HEADER)
    factory.button(root, "-", px + 180, chrome_y, 40, BTN_H_HEADER, lambda: adjust_window_scale(-WINDOW_SCALE_STEP), fill=_with_alpha(C_BTN_MUTED, opacity), scale=0.70)
    factory.button(root, f"{STATE.window_scale:.2f}x", px + 226, chrome_y, 72, BTN_H_HEADER, reset_window_scale, fill=_with_alpha(C_BTN_MUTED, opacity), scale=0.34)
    factory.button(root, "+", px + 304, chrome_y, 40, BTN_H_HEADER, lambda: adjust_window_scale(WINDOW_SCALE_STEP), fill=_with_alpha(C_BTN_MUTED, opacity), scale=0.70)
    factory.button(root, "RESET POS", px + 350, chrome_y, 110, BTN_H_HEADER, reset_panel_position, fill=_with_alpha(C_BTN, opacity), scale=0.34)
    factory.button(root, "Edit" if not STATE.edit_mode else "Done", px + pw - 236, chrome_y, 100, BTN_H_HEADER, lambda: _toggle_edit(), fill=_with_alpha(C_BTN_GOLD, opacity), scale=SCALE_BTN_HEADER)
    factory.button(root, "Close F7", px + pw - 128, chrome_y, 116, BTN_H_HEADER, close_panel, fill=_with_alpha(C_BTN_DANGER, opacity), scale=SCALE_BTN_HEADER, allow_when_modal=True)

    # Always-visible P1-P4 / PAll target toggles (single-select backend).
    player_y = py + 118
    party = backend_actions.refresh_players()
    party_by_index = {int(p.get("index", -1)): p for p in party}
    selected_idx = backend_actions.get_selected_player_index()
    slot_w = 74.0
    slot_gap = 6.0
    slot_x = px + 12
    for slot_i in range(4):
        present = slot_i in party_by_index
        selected = selected_idx is not None and int(selected_idx) == slot_i
        if selected:
            fill = C_SLOT_SEL
        elif present:
            fill = C_BTN
        else:
            fill = C_SLOT_EMPTY
        label = f"P{slot_i + 1}"
        if present:
            name = str(party_by_index[slot_i].get("name") or "")[:6]
            if name:
                label = f"P{slot_i + 1}:{name}"

        def _make_p(i: int = slot_i) -> Callable[[], None]:
            return lambda: _toggle_header_player_slot(i)

        factory.button(
            root,
            label,
            slot_x,
            player_y,
            slot_w,
            36,
            _make_p(),
            fill=_with_alpha(fill, opacity),
            scale=0.30,
            enabled=present,
        )
        slot_x += slot_w + slot_gap
    factory.button(
        root,
        "PAll",
        slot_x,
        player_y,
        70,
        36,
        _toggle_header_player_all,
        fill=_with_alpha(C_BTN_GOLD if selected_idx is not None else C_BTN_MUTED, opacity),
        scale=0.34,
    )

    tab_y = py + 162
    tab_x = px + 12
    for page_i in range(MAX_PAGES):
        fill = C_BTN_GOLD if STATE.main_tab == "actions" and page_i == STATE.page else C_BTN_MUTED

        def _make_page(i: int = page_i) -> Callable[[], None]:
            return lambda: _set_page(i)

        factory.button(root, f"P{page_i + 1}", tab_x, tab_y, 64, BTN_H_TAB, _make_page(), fill=_with_alpha(fill, opacity), scale=SCALE_BTN_HEADER)
        tab_x += 70

    inv_fill = C_BTN_GOLD if STATE.main_tab == "inventory" else C_BTN_MUTED
    factory.button(
        root,
        "INV",
        tab_x,
        tab_y,
        64,
        BTN_H_TAB,
        lambda: _open_inventory_tab(refresh=False),
        fill=_with_alpha(inv_fill, opacity),
        scale=SCALE_BTN_HEADER,
    )

    if STATE.main_tab == "inventory":
        from . import quick_menu_inventory

        footer_y = quick_menu_inventory.render_tab(factory, root, px, py, pw, opacity)
    else:
        tool_y = tab_y + 48
        factory.button(root, "Pin Last", px + 12, tool_y, 130, BTN_H_TOOL, lambda: pin_last_command(), fill=_with_alpha(C_BTN_GOLD, opacity), scale=SCALE_BTN)
        factory.button(root, "Lock", px + 150, tool_y, 90, BTN_H_TOOL, toggle_drop_lock, fill=_with_alpha(C_BTN, opacity), scale=SCALE_BTN)
        factory.button(root, "Target", px + 248, tool_y, 100, BTN_H_TOOL, lambda: _begin_player_pick("target"), fill=_with_alpha(C_BTN, opacity), scale=SCALE_BTN)

        def _refresh_ui() -> None:
            _run_action("refresh_players")
            rebuild_ui()

        factory.button(root, "Refresh", px + 356, tool_y, 110, BTN_H_TOOL, _refresh_ui, fill=_with_alpha(C_BTN_MUTED, opacity), scale=SCALE_BTN)

        selected_name = backend_actions.get_selected_player_name() or "(none)"
        selected_idx = backend_actions.get_selected_player_index()
        target_txt = f"Target: {selected_idx}: {selected_name}" if selected_idx is not None else "Target: (none)"
        last = backend_actions.get_last_command()
        last_txt = f"Last: {last.get('label')}" if last else "Last: (none)"
        drop = backend_actions.get_last_drop()
        drop_txt = f"Drop: {drop.get('label')}" if drop else "Drop: (none)"
        info_y = tool_y + 48
        factory.text(root, target_txt, px + 12, info_y, pw - 24, 22, scale=SCALE_BODY, z=5, tint=C_TEXT_DIM)
        factory.text(root, f"{last_txt} | {drop_txt}", px + 12, info_y + 22, pw - 24, 22, scale=SCALE_BODY, z=5, tint=C_TEXT_DIM)

        filled = _page_filled_count()
        banner_h = 0.0
        grid_y0 = info_y + 50
        if filled == 0:
            factory.border(root, px + 12, grid_y0, pw - 24, 34, _with_alpha(C_BTN_GOLD, opacity), 8)
            factory.text(
                root,
                "Empty page. Tap a slot to assign, or use + QM in the desktop app.",
                px + 18,
                grid_y0 + 4,
                pw - 36,
                26,
                scale=SCALE_BODY,
                z=9,
                center=True,
            )
            banner_h = 40.0
        grid_y0 = grid_y0 + banner_h
        cell_w, cell_h = CELL_W, CELL_H
        gap_x, gap_y = CELL_GAP_X, CELL_GAP_Y
        slots = STATE.pages[STATE.page]
        for idx in range(SLOTS_PER_PAGE):
            row, col = divmod(idx, GRID_COLS)
            x = px + 12 + col * (cell_w + gap_x)
            y = grid_y0 + row * (cell_h + gap_y)
            slot = slots[idx] if idx < len(slots) else None
            selected = STATE.edit_mode and STATE.selected_slot == idx
            if slot is None:
                label = "+ Assign"
                fill = action_slot_fill(index=idx, selected=False, empty=True)
            else:
                label = slot_button_label(slot)
                fill = action_slot_fill(index=idx, selected=selected, empty=False)

            def _make_slot(i: int = idx) -> Callable[[], None]:
                return lambda: activate_slot(i)

            factory.button(root, label, x, y, cell_w, cell_h, _make_slot(), fill=_with_alpha(fill, opacity), scale=SCALE_SLOT)

        grid_bottom = grid_y0 + GRID_ROWS * cell_h + (GRID_ROWS - 1) * gap_y
        if STATE.rarity_panel_equipped:
            rarity_y = grid_bottom + 10
            _render_rarity_controls(factory, root, px, rarity_y, pw, opacity)
            footer_y = rarity_y + RARITY_RESERVE_H + 12
        else:
            footer_y = grid_bottom + 16
    hint = (
        "F7 close · INV tab · tap item · Give-to separate from P1–P4 view"
        if STATE.main_tab == "inventory"
        else "F7 close · Esc release-close · F6 unstuck · Dash: V=MSBT / Num0=Azzy · Soft Clear hides loot"
    )
    factory.text(
        root,
        hint,
        px + 12,
        footer_y,
        pw - 24,
        24,
        scale=SCALE_HINT,
        z=6,
        tint=C_TEXT_DIM,
    )
    factory.text(root, STATE.status, px + 12, footer_y + 26, pw - 24, 32, scale=SCALE_BODY, z=6, tint=C_TEXT_DIM)
    if STATE.main_tab != "inventory":
        factory.text(root, f"Opacity {int(opacity * 100)}%", px + 12, footer_y + 58, 220, 22, scale=SCALE_HINT, z=6, tint=C_TEXT_DIM)
        factory.border(root, px + 12, footer_y + 82, pw - 24, 28, _with_alpha(C_BTN_MUTED, 1.0), 6)
        factory.slider(root, "panel_opacity", opacity, px + 16, footer_y + 84, pw - 32, 24, z=7)

        if STATE.edit_mode or filled == 0:
            if filled == 0 and STATE.page > 0:
                recovery_label = "Go Page 1"
                recovery_action = lambda: _set_page(0)
            else:
                recovery_label = "Reset Page"
                recovery_action = reset_current_page
            factory.button(root, recovery_label, px + 12, footer_y + 120, 180, BTN_H_TOOL, recovery_action, fill=_with_alpha(C_BTN, opacity), scale=SCALE_BTN)
            factory.button(root, "Reset All", px + 204, footer_y + 120, 150, BTN_H_TOOL, reset_all_pages, fill=_with_alpha(C_BTN_DANGER, opacity), scale=SCALE_BTN)

    if STATE.toast and time.monotonic() < STATE.toast_until:
        fill = C_TOAST_OK if STATE.toast_ok else C_TOAST_BAD
        factory.border(root, px + 16, footer_y + 170, pw - 32, 40, _with_alpha(fill, 1.0), 90)
        factory.text(root, STATE.toast, px + 24, footer_y + 176, pw - 48, 28, scale=SCALE_BTN, z=91, center=True)

    if STATE.placing:
        catcher = factory.widget("/Script/UMG.Button")
        factory.add(root, catcher)
        factory.slot(catcher, 0, 0, DESIGN_W, DESIGN_H, 200)
        try_call(catcher, "SetVisibility", 0)
        try_call(catcher, "SetIsEnabled", True)
        try_call(catcher, "SetRenderOpacity", 0.02)
        STATE.place_catcher = catcher
        factory.text(root, "MOVE: slide mouse, click to place (Esc cancels)", px + 12, py + HEADER_H + 4, pw - 24, 28, scale=SCALE_BODY, z=201, center=True, tint=C_BTN_GOLD)
    else:
        STATE.place_catcher = None

    if STATE.modal == "player_pick":
        _render_player_pick(factory, root)
    elif STATE.modal == "action_pick":
        _render_action_pick(factory, root)
    elif STATE.modal == "theme_pick":
        _render_theme_pick(factory, root)
    elif STATE.modal == "label_edit":
        _render_label_edit(factory, root)
    elif STATE.modal == "serial_pick":
        _render_serial_pick(factory, root)
    elif STATE.modal == "inv_detail":
        from . import quick_menu_inventory

        quick_menu_inventory.render_detail_modal(factory, root)



def _toggle_edit() -> None:
    leaving_edit = bool(STATE.edit_mode)
    cancel_hotkey_listen()
    STATE.edit_mode = not STATE.edit_mode
    STATE.modal = ""
    STATE.selected_slot = None
    STATE.swap_armed_slot = None
    save_layout()
    if leaving_edit and _page_filled_count() == 0:
        show_toast("This page is empty. Tap a slot to assign, or Reset Page.", ok=False, seconds=3.0)
    rebuild_ui()


def theme_label(theme_id: str) -> str:
    tid = str(theme_id or "").strip().lower()
    return str(THEME_LABELS.get(tid) or tid or "msbt_bright")


def open_theme_pick() -> None:
    STATE.modal = "theme_pick"
    rebuild_ui()


def apply_theme_choice(theme_id: str) -> None:
    apply_theme(theme_id)
    STATE.modal = ""
    save_layout()
    show_toast(f"Theme: {theme_label(STATE.theme_id)}", ok=True, seconds=1.5)
    rebuild_ui()


def cycle_theme() -> None:
    # With a large static theme pack, open a scroll picker instead of cycling.
    if len(THEME_IDS) > THEME_PICK_THRESHOLD:
        open_theme_pick()
        return
    ids = list(THEME_IDS)
    try:
        idx = ids.index(STATE.theme_id)
    except ValueError:
        idx = 0
    apply_theme(ids[(idx + 1) % len(ids)])
    save_layout()
    show_toast(f"Theme: {theme_label(STATE.theme_id)}", ok=True, seconds=1.5)
    rebuild_ui()


def adjust_window_scale(delta: float) -> None:
    value = round(float(STATE.window_scale) + float(delta), 2)
    STATE.window_scale = max(WINDOW_SCALE_MIN, min(WINDOW_SCALE_MAX, value))
    update_layout_metrics()
    save_layout()
    show_toast(f"Window size {STATE.window_scale:.2f}x", ok=True, seconds=1.2)
    rebuild_ui()


def reset_window_scale() -> None:
    STATE.window_scale = float(quick_menu_registry.WINDOW_SCALE_DEFAULT)
    update_layout_metrics()
    save_layout()
    show_toast("Window size reset to 1.00x", ok=True, seconds=1.2)
    rebuild_ui()


def reset_panel_position() -> None:
    STATE.offset_x = 0.0
    STATE.offset_y = 0.0
    STATE.placing = False
    STATE.place_mouse0 = None
    STATE.place_catcher = None
    save_layout()
    show_toast("Panel re-pinned to the right", ok=True, seconds=1.5)
    rebuild_ui()


def begin_move_placement() -> None:
    # Azzy-style click-to-place: pick up on MOVE, follow mouse by delta, click to drop.
    STATE.placing = True
    STATE.place_click_was_down = True
    STATE.place_started_at = time.monotonic()
    STATE.place_mouse0 = None
    STATE.place_offset0 = (float(STATE.offset_x), float(STATE.offset_y))
    STATE.place_last_rebuild = 0.0
    STATE.modal = ""
    _log("MOVE: slide mouse, click to place (Esc cancels).")
    rebuild_ui()


def cancel_move_placement(*, toast: bool = True) -> None:
    if not STATE.placing:
        return
    STATE.placing = False
    STATE.place_mouse0 = None
    STATE.place_catcher = None
    if toast:
        show_toast("MOVE cancelled", ok=False, seconds=1.2)
    rebuild_ui()


def _mouse_viewport_pos() -> tuple[float, float] | None:
    pc = get_pc()
    if pc is None:
        return None
    # Prefer PC.GetMousePosition — same path Azzy uses (more reliable under GameAndUI).
    try:
        for args in ((0.0, 0.0), (0, 0), ()):
            try:
                res = pc.GetMousePosition(*args) if args else pc.GetMousePosition()
            except TypeError:
                continue
            except Exception:
                continue
            if isinstance(res, tuple):
                vals = list(res)
                if len(vals) >= 3 and bool(vals[0]):
                    return float(vals[1]), float(vals[2])
                if len(vals) >= 2:
                    return float(vals[0]), float(vals[1])
            xy = _vec2_xy(res)
            if xy:
                return xy
    except Exception:
        pass
    try:
        lib = class_obj("/Script/UMG.WidgetLayoutLibrary").ClassDefaultObject
        xy = _vec2_xy(lib.GetMousePositionOnViewport())
        if xy:
            return xy
    except Exception:
        pass
    return None


def _left_mouse_down() -> bool:
    return _key_down(get_pc(), "LeftMouseButton")


def poll_move_placement() -> bool:
    """Click-to-place: MOVE arms placement; panel follows cursor until click.

    Returns True while placing so the caller skips normal button polling.
    Does not rebuild every tick (that destroyed the catcher and froze MOVE).
    """
    if not STATE.placing or not STATE.is_open:
        return False

    mouse = _mouse_viewport_pos()
    if mouse is not None:
        mx, my = mouse
        if STATE.place_mouse0 is None:
            STATE.place_mouse0 = (mx, my)
            STATE.place_offset0 = (float(STATE.offset_x), float(STATE.offset_y))
        else:
            sx_div = max(0.001, float(STATE.scale_x) * float(STATE.window_scale or 1.0))
            sy_div = max(0.001, float(STATE.scale_y) * float(STATE.window_scale or 1.0))
            dx = (mx - STATE.place_mouse0[0]) / sx_div
            dy = (my - STATE.place_mouse0[1]) / sy_div
            new_x = max(-800.0, min(800.0, STATE.place_offset0[0] + dx))
            new_y = max(-400.0, min(400.0, STATE.place_offset0[1] + dy))
            moved = abs(new_x - STATE.offset_x) > 0.5 or abs(new_y - STATE.offset_y) > 0.5
            STATE.offset_x = new_x
            STATE.offset_y = new_y
            now = time.monotonic()
            # Throttled rebuild so the panel visibly follows without thrashing widgets.
            if moved and (now - float(STATE.place_last_rebuild or 0.0)) >= 0.05:
                STATE.place_last_rebuild = now
                rebuild_ui()

    pressed = False
    catcher = STATE.place_catcher
    if live(catcher):
        try:
            pressed = bool(catcher.IsPressed())
        except Exception:
            pressed = False
    if not pressed:
        pressed = _left_mouse_down()

    just_clicked = bool(pressed) and not bool(STATE.place_click_was_down)
    STATE.place_click_was_down = bool(pressed)

    # Drop on a fresh click, debounced so the MOVE button press can't place instantly.
    if just_clicked and (time.monotonic() - float(STATE.place_started_at)) > 0.25:
        STATE.placing = False
        STATE.place_mouse0 = None
        STATE.place_catcher = None
        save_layout()
        show_toast("Panel placed", ok=True, seconds=1.2)
        rebuild_ui()
        return True
    return True


def _set_page(page: int) -> None:
    STATE.main_tab = "actions"
    STATE.page = max(0, min(MAX_PAGES - 1, int(page)))
    STATE.selected_slot = None
    STATE.swap_armed_slot = None
    STATE.modal = ""
    save_layout()
    rebuild_ui()


def _open_inventory_tab(*, refresh: bool = False) -> None:
    from . import quick_menu_inventory

    quick_menu_inventory.open_inventory_tab(refresh=refresh)


def _render_player_pick(factory: NativeUMG, root: Any) -> None:
    factory.modal_blocker(root)
    factory.border(root, panel_x() + 12, 120, panel_w() - 24, 780, _with_alpha(C_DOCK, 1.0), MODAL_PANEL_Z)
    factory.border(root, panel_x() + 12, 120, panel_w() - 24, 64, _with_alpha(C_HEADER, 1.0), MODAL_CONTENT_Z)
    purpose = STATE.player_pick_purpose or ("repeat" if STATE.pending_repeat else "lock")
    title = {
        "repeat": "Select player for repeat last drop",
        "lock": "Lock repeat-last-drop to player",
        "target": "Select target player",
        "action": "Select target player for this action",
    }.get(purpose, "Select player")
    factory.text(
        root,
        title,
        panel_x() + 24,
        130,
        panel_w() - 48,
        44,
        scale=SCALE_MODAL_TITLE,
        z=MODAL_CONTENT_Z + 1,
        center=True,
    )
    players = backend_actions.refresh_players()
    scroll = factory.scroll_box(root, panel_x() + 24, 200, panel_w() - 48, 600, z=MODAL_CONTENT_Z)
    if not players:
        row = factory.scroll_row(scroll, panel_w() - 64, 56)
        factory.text(row, "No party players found.", 8, 10, panel_w() - 80, 36, scale=SCALE_BTN, z=1, center=True)
    for player in players:
        idx = int(player.get("index", -1))
        name = str(player.get("name") or f"Player {idx}")

        def _make_pick(i: int = idx, n: str = name, p: str = purpose) -> Callable[[], None]:
            if p == "repeat":
                return lambda: _finish_repeat_for_player(i, n)
            if p in ("target", "action"):
                return lambda: _set_target_from_pick(i, n)
            return lambda: _lock_player_from_pick(i, n)

        row = factory.scroll_row(scroll, panel_w() - 64, 68)
        factory.button(
            row,
            f"{idx}: {name}",
            0,
            4,
            panel_w() - 72,
            58,
            _make_pick(),
            fill=C_BTN,
            scale=SCALE_MODAL_BTN,
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
        panel_x() + (panel_w() - 200) / 2,
        820,
        200,
        52,
        _cancel,
        fill=C_BTN_DANGER,
        scale=SCALE_MODAL_BTN,
        modal_only=True,
    )


def _render_serial_pick(factory: NativeUMG, root: Any) -> None:
    """Copyable list of the last equipped / backpack serial read."""
    factory.modal_blocker(root)
    factory.border(root, panel_x() + 12, 120, panel_w() - 24, 780, _with_alpha(C_DOCK, 1.0), MODAL_PANEL_Z)
    factory.border(root, panel_x() + 12, 120, panel_w() - 24, 64, _with_alpha(C_HEADER, 1.0), MODAL_CONTENT_Z)
    bundle = backend_actions.get_last_read_serials()
    title = str(bundle.get("title") or "Read serials")
    entries = list(bundle.get("entries") or [])
    factory.text(
        root,
        f"{title} — tap to copy",
        panel_x() + 24,
        130,
        panel_w() - 48,
        44,
        scale=SCALE_MODAL_TITLE,
        z=MODAL_CONTENT_Z + 1,
        center=True,
    )
    scroll = factory.scroll_box(root, panel_x() + 24, 200, panel_w() - 48, 540, z=MODAL_CONTENT_Z)
    if not entries:
        row = factory.scroll_row(scroll, panel_w() - 64, 56)
        factory.text(row, "No serials cached.", 8, 10, panel_w() - 80, 36, scale=SCALE_BTN, z=1, center=True)
    for idx, entry in enumerate(entries):
        summary = str(entry.get("summary") or entry.get("label") or f"Item {idx + 1}")
        serial = str(entry.get("serial") or "")
        short = serial if len(serial) <= 28 else (serial[:12] + "…" + serial[-12:])
        label = f"{summary}  {short}"

        def _make_copy(i: int = idx) -> Callable[[], None]:
            def _copy() -> None:
                result = backend_actions.copy_read_serial(i)
                _set_status_from_result(result)
                rebuild_ui()

            return _copy

        row = factory.scroll_row(scroll, panel_w() - 64, 68)
        factory.button(
            row,
            label,
            0,
            4,
            panel_w() - 72,
            58,
            _make_copy(),
            fill=C_BTN,
            scale=SCALE_MODAL_BTN,
            modal_only=True,
            z=1,
        )

    def _copy_all() -> None:
        result = backend_actions.copy_all_read_serials()
        _set_status_from_result(result)
        rebuild_ui()

    def _close() -> None:
        STATE.modal = ""
        rebuild_ui()

    factory.button(
        root,
        "Copy All",
        panel_x() + 24,
        760,
        (panel_w() - 64) / 2,
        52,
        _copy_all,
        fill=C_BTN_GOLD,
        scale=SCALE_MODAL_BTN,
        modal_only=True,
    )
    factory.button(
        root,
        "Close",
        panel_x() + 24 + (panel_w() - 64) / 2 + 16,
        760,
        (panel_w() - 64) / 2,
        52,
        _close,
        fill=C_BTN_DANGER,
        scale=SCALE_MODAL_BTN,
        modal_only=True,
    )


def _render_action_pick(factory: NativeUMG, root: Any) -> None:
    factory.modal_blocker(root)
    factory.border(root, panel_x() + 12, 100, panel_w() - 24, 820, _with_alpha(C_DOCK, 1.0), MODAL_PANEL_Z)
    factory.border(root, panel_x() + 12, 100, panel_w() - 24, 60, _with_alpha(C_HEADER, 1.0), MODAL_CONTENT_Z)
    factory.text(
        root,
        "Assign action to slot",
        panel_x() + 24,
        110,
        panel_w() - 48,
        40,
        scale=SCALE_MODAL_TITLE,
        z=MODAL_CONTENT_Z + 1,
        center=True,
    )
    scroll = factory.scroll_box(root, panel_x() + 24, 174, panel_w() - 48, 620, z=MODAL_CONTENT_Z)
    for action in PICKER_ACTIONS:
        label = str(ACTION_CATALOG.get(action, {}).get("basic") or action)

        def _make_assign(a: str = action) -> Callable[[], None]:
            return lambda: assign_action_to_selected(a)

        row = factory.scroll_row(scroll, panel_w() - 64, 62)
        factory.button(
            row,
            label,
            0,
            2,
            panel_w() - 72,
            56,
            _make_assign(),
            fill=C_BTN,
            scale=SCALE_MODAL_BTN,
            modal_only=True,
            z=1,
        )
    if backend_actions.get_last_command() is not None:
        factory.button(
            root,
            "Pin Last Here",
            panel_x() + 24,
            812,
            240,
            52,
            lambda: pin_last_command(STATE.selected_slot),
            fill=C_BTN_GOLD,
            scale=SCALE_MODAL_BTN,
            modal_only=True,
        )

    def _cancel() -> None:
        STATE.modal = ""
        rebuild_ui()

    factory.button(
        root,
        "Cancel",
        panel_x() + panel_w() - 210,
        812,
        180,
        52,
        _cancel,
        fill=C_BTN_DANGER,
        scale=SCALE_MODAL_BTN,
        modal_only=True,
    )



def _render_theme_pick(factory: NativeUMG, root: Any) -> None:
    factory.modal_blocker(root)
    factory.border(root, panel_x() + 12, 100, panel_w() - 24, 820, _with_alpha(C_DOCK, 1.0), MODAL_PANEL_Z)
    factory.border(root, panel_x() + 12, 100, panel_w() - 24, 60, _with_alpha(C_HEADER, 1.0), MODAL_CONTENT_Z)
    factory.text(
        root,
        "Choose theme",
        panel_x() + 24,
        110,
        panel_w() - 48,
        40,
        scale=SCALE_MODAL_TITLE,
        z=MODAL_CONTENT_Z + 1,
        center=True,
    )
    scroll = factory.scroll_box(root, panel_x() + 24, 174, panel_w() - 48, 620, z=MODAL_CONTENT_Z)
    for tid in THEME_IDS:
        label = theme_label(tid)
        selected = tid == STATE.theme_id
        fill = C_BTN_GOLD if selected else C_BTN

        def _make_theme(t: str = tid) -> Callable[[], None]:
            return lambda: apply_theme_choice(t)

        row = factory.scroll_row(scroll, panel_w() - 64, 62)
        factory.button(
            row,
            label,
            0,
            2,
            panel_w() - 72,
            56,
            _make_theme(),
            fill=fill,
            scale=SCALE_MODAL_BTN,
            modal_only=True,
            z=1,
        )

    def _cancel() -> None:
        STATE.modal = ""
        rebuild_ui()

    factory.button(
        root,
        "Cancel",
        panel_x() + (panel_w() - 200) / 2,
        812,
        200,
        52,
        _cancel,
        fill=C_BTN_DANGER,
        scale=SCALE_MODAL_BTN,
        modal_only=True,
    )


def _render_label_edit(factory: NativeUMG, root: Any) -> None:
    if STATE.selected_slot is None:
        return
    slot = STATE.pages[STATE.page][STATE.selected_slot]
    if slot is None:
        return
    factory.modal_blocker(root)
    factory.border(root, panel_x() + 20, 160, panel_w() - 40, 640, _with_alpha(C_DOCK, 1.0), MODAL_PANEL_Z)
    factory.border(root, panel_x() + 20, 160, panel_w() - 40, 60, _with_alpha(C_HEADER, 1.0), MODAL_CONTENT_Z)
    factory.text(
        root,
        f"Edit slot {STATE.selected_slot + 1}",
        panel_x() + 32,
        172,
        panel_w() - 64,
        40,
        scale=SCALE_MODAL_TITLE,
        z=MODAL_CONTENT_Z + 1,
        center=True,
    )
    factory.text(
        root,
        f"Label: {slot_label(slot)}",
        panel_x() + 32,
        236,
        panel_w() - 64,
        32,
        scale=SCALE_BTN,
        z=MODAL_CONTENT_Z,
        center=True,
    )
    hot = quick_menu_registry.hotkey_display(str(slot.get("hotkey") or ""))
    if STATE.hotkey_listen:
        hot_txt = "Press a key… (Esc clears · Cancel exits)"
    elif hot:
        hot_txt = f"Hotkey: {hot}  (fires when menu closed)"
    else:
        hot_txt = "Hotkey: (none)"
    factory.text(
        root,
        hot_txt,
        panel_x() + 32,
        272,
        panel_w() - 64,
        28,
        scale=SCALE_BODY,
        z=MODAL_CONTENT_Z,
        center=True,
        tint=C_BTN_GOLD if STATE.hotkey_listen else C_TEXT_DIM,
    )

    def _cycle() -> None:
        cancel_hotkey_listen()
        cycle_slot_label(slot)
        save_layout()
        rebuild_ui()

    factory.button(
        root,
        "Cycle Label",
        panel_x() + 40,
        316,
        panel_w() - 80,
        52,
        _cycle,
        fill=C_BTN,
        scale=SCALE_MODAL_BTN,
        modal_only=True,
    )

    bind_label = "Cancel Bind" if STATE.hotkey_listen else "Bind Hotkey"
    factory.button(
        root,
        bind_label,
        panel_x() + 40,
        380,
        (panel_w() - 96) / 2,
        52,
        (cancel_hotkey_listen if STATE.hotkey_listen else begin_hotkey_listen),
        fill=C_BTN_GOLD,
        scale=SCALE_MODAL_BTN,
        modal_only=True,
    )
    factory.button(
        root,
        "Clear Hotkey",
        panel_x() + 40 + (panel_w() - 96) / 2 + 16,
        380,
        (panel_w() - 96) / 2,
        52,
        clear_selected_hotkey,
        fill=C_BTN_MUTED,
        scale=SCALE_MODAL_BTN,
        modal_only=True,
    )

    factory.button(
        root,
        "Clear Slot",
        panel_x() + 40,
        448,
        (panel_w() - 96) / 2,
        52,
        clear_selected_slot,
        fill=C_BTN_DANGER,
        scale=SCALE_MODAL_BTN,
        modal_only=True,
    )
    factory.button(
        root,
        "Swap With…",
        panel_x() + 40 + (panel_w() - 96) / 2 + 16,
        448,
        (panel_w() - 96) / 2,
        52,
        arm_swap_selected,
        fill=C_BTN_GOLD,
        scale=SCALE_MODAL_BTN,
        modal_only=True,
    )
    if backend_actions.get_last_command() is not None:
        factory.button(
            root,
            "Pin Last Over This",
            panel_x() + 40,
            516,
            panel_w() - 80,
            52,
            lambda: pin_last_command(STATE.selected_slot),
            fill=C_BTN_GOLD,
            scale=SCALE_MODAL_BTN,
            modal_only=True,
        )

    def _done() -> None:
        cancel_hotkey_listen()
        STATE.modal = ""
        STATE.swap_armed_slot = None
        rebuild_ui()

    factory.button(
        root,
        "Done",
        panel_x() + (panel_w() - 200) / 2,
        588,
        200,
        52,
        _done,
        fill=C_BTN,
        scale=SCALE_MODAL_BTN,
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
    STATE.escape_pending_close = False
    STATE.escape_pending_release_seen_at = 0.0
    STATE.escape_defer_ui_pop = False
    # Ignore the still-held open key so the poller does not close instantly.
    STATE.key_f7 = True
    STATE.key_escape = False
    push_menu_ui_state()
    _clear_toast_overlay()
    try:
        ensured = backend_actions.ensure_selected_player(prefer_host=True)
        if ensured.get("auto_selected"):
            STATE.status = str(ensured.get("message") or STATE.status)
    except Exception:
        pass
    _sync_rarity_weights_from_backend()
    rebuild_ui()
    capture_input()
    _log(
        f"Quick Menu opened (viewport={int(STATE.viewport_w)}x{int(STATE.viewport_h)} "
        f"dpi={STATE.dpi_scale:.3f} layout={int(STATE.layout_w)}x{int(STATE.layout_h)})"
    )


def close_panel(defer_ui_state_pop: bool = False) -> None:
    if not STATE.is_open and not live(STATE.overlay):
        return
    STATE.is_open = False
    STATE.modal = ""
    cancel_hotkey_listen()
    STATE.pending_repeat = False
    STATE.player_pick_purpose = ""
    STATE.pending_action = None
    STATE.swap_armed_slot = None
    STATE.escape_pending_close = False
    STATE.buttons.clear()
    STATE.sliders.clear()
    if not defer_ui_state_pop:
        try:
            pop_menu_ui_state()
        except Exception as exc:
            _log(f"UI state pop skipped: {exc}")
    remove_widget(STATE.menu_canvas)
    remove_widget(STATE.overlay)
    STATE.menu_canvas = STATE.overlay = STATE.tree = STATE.root = None
    # Prevent same-frame keybind + poller from reopening immediately.
    STATE.hotkey_ignore_until = time.monotonic() + 0.35
    restore_input()
    _log("Quick Menu closed")


def toggle_panel() -> None:
    if time.monotonic() < float(STATE.hotkey_ignore_until or 0.0):
        return
    close_panel() if STATE.is_open else open_panel()



def poll_sliders() -> None:
    changed_opacity = False
    rarity_changed = False
    label_map = {key: short for key, short in RARITY_SLIDER_KEYS}
    for ref in list(STATE.sliders):
        widget = ref.widget
        if not live(widget):
            continue
        try:
            value = float(widget.GetValue())
        except Exception:
            continue
        key = str(ref.key or "")
        if key.startswith("rarity_"):
            value = max(0.0, min(1.0, value))
            if abs(value - float(ref.value)) < 0.005:
                continue
            ref.value = value
            rarity_key = key[len("rarity_") :]
            STATE.rarity_weights[rarity_key] = value
            short = label_map.get(rarity_key, rarity_key[:3].title())
            if live(ref.label_widget):
                try_call(ref.label_widget, "SetText", f"{short} {int(round(value * 100.0))}%")
            rarity_changed = True
            continue
        if key == "panel_opacity":
            value = max(0.55, min(1.0, value))
            if abs(value - float(ref.value)) < 0.005:
                continue
            ref.value = value
            STATE.panel_opacity = value
            changed_opacity = True
    if rarity_changed:
        # Match BLImGui: slider drags write GameState (throttled while dragging).
        now = time.monotonic()
        STATE.rarity_local_edit_until = now + 0.45
        STATE.rarity_live_apply_due = now + 0.18
    if STATE.rarity_live_apply_due and time.monotonic() >= float(STATE.rarity_live_apply_due):
        STATE.rarity_live_apply_due = 0.0
        try:
            result = backend_actions.rarity_apply(_rarity_payload_from_state())
            _set_status_from_result(result)
        except Exception as exc:
            show_toast(f"Rarity apply failed: {exc}", ok=False, seconds=2.4)
    if changed_opacity:
        save_layout()
        STATE.ui_dirty = True


def _sync_rarity_from_backend_if_idle() -> None:
    """Pull Boosting/Electron weight changes into F7 when the user is not dragging."""
    if not STATE.rarity_panel_equipped:
        return
    now = time.monotonic()
    if now < float(STATE.rarity_local_edit_until or 0.0):
        return
    if now < float(STATE.rarity_backend_sync_at or 0.0) + 0.5:
        return
    STATE.rarity_backend_sync_at = now
    before = {key: float(STATE.rarity_weights.get(key, 1.0)) for key, _label in RARITY_SLIDER_KEYS}
    _sync_rarity_weights_from_backend()
    for key, _label in RARITY_SLIDER_KEYS:
        if abs(float(STATE.rarity_weights.get(key, 1.0)) - float(before.get(key, 1.0))) > 0.004:
            STATE.ui_dirty = True
            break


def poll_buttons() -> None:
    modal_active = bool(STATE.modal)
    mouse = _mouse_viewport_pos()
    ok_mouse = mouse is not None
    mx = my = 0.0
    if ok_mouse:
        mx, my = mouse
    mouse_down = _left_mouse_down()

    for ref in list(STATE.buttons):
        if modal_active and not ref.modal_only and not ref.allow_when_modal:
            ref.was_pressed = False
            ref.manual_was_down = False
            continue
        if not ref.enabled or not live(ref.widget):
            ref.was_pressed = False
            ref.manual_was_down = False
            continue
        action_fired = False
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
                action_fired = True
            except Exception as exc:
                _log(f"Button '{ref.label}' failed: {exc}")
            return

        if action_fired:
            ref.manual_was_down = False
            continue

        # NMM fallback: raw mouse + stored scaled rect when IsPressed is unreliable.
        if ok_mouse and ref.rect is not None:
            over = rect_contains(ref.rect, mx, my)
            if ref.manual_was_down and (not mouse_down) and over:
                ref.manual_was_down = False
                try:
                    ref.action()
                except Exception as exc:
                    _log(f"Button '{ref.label}' failed: {exc}")
                return
            ref.manual_was_down = bool(mouse_down and over)
        else:
            ref.manual_was_down = False


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
    pc = get_pc()
    update_escape_close_block(pc)
    if not STATE.is_open:
        STATE.key_escape = False
        return
    down = _key_down(pc, "Escape")
    was = STATE.key_escape
    STATE.key_escape = down
    if down and not was:
        if STATE.hotkey_listen:
            # poll_hotkey_listen owns Escape while binding (clear vs cancel).
            pass
        elif STATE.placing:
            cancel_move_placement()
        elif STATE.modal:
            cancel_hotkey_listen()
            STATE.modal = ""
            STATE.pending_repeat = False
            STATE.player_pick_purpose = ""
            STATE.pending_action = None
            STATE.swap_armed_slot = None
            rebuild_ui()
        elif not STATE.escape_pending_close:
            # Wait for Esc release before teardown so pause does not also close.
            STATE.escape_pending_close = True
            STATE.escape_pending_release_seen_at = 0.0
            begin_escape_close_block(duration=3.0)
            _log("Esc close pending until release")


def _edge_key(pc: Any, name: str, state_attr: str) -> bool:
    """Return True on key-down edge. Keeps working while UMG owns UI focus."""
    down = _key_down(pc, name)
    was = bool(getattr(STATE, state_attr, False))
    setattr(STATE, state_attr, down)
    return bool(down and not was)


def process_hotkeys() -> None:
    """Poll F7/F6 while open so toggles still work under GameAndUI capture.

    mods_base keybinds often do not fire while the Quick Menu owns UI input,
    which made F7 open-only from the player's point of view.
    """
    pc = get_pc()
    if pc is None:
        STATE.key_f7 = False
        STATE.key_f6 = False
        return

    # F6 always available as emergency restore, even if STATE.is_open is wrong.
    if _edge_key(pc, "F6", "key_f6"):
        unstuck()
        return

    if not STATE.is_open:
        STATE.key_f7 = False
        return

    if _edge_key(pc, "F7", "key_f7"):
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
        try:
            backend_actions.tick_asd_autoclear()
        except Exception:
            pass
        _poll_delivery_toasts()
        _expire_toast()
        # Hotkeys first so F6 can recover even if overlay state is inconsistent.
        process_hotkeys()
        if not STATE.is_open:
            process_escape()
            process_slot_hotkeys()
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
            cancel_hotkey_listen()
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
        # Escape before bind poll so listen-mode still owns Esc this frame.
        process_escape()
        poll_hotkey_listen()
        if poll_move_placement():
            # Follow/rebuild is handled inside poll_move_placement (throttled).
            return None
        poll_sliders()
        _sync_rarity_from_backend_if_idle()
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
    description="Open or close the native UMG Quick Menu. Also polled while open so F7 can close under UI focus.",
)

quick_menu_unstuck_key = keybind(
    "MSBT Quick Menu Unstuck",
    "F6",
    callback=unstuck,
    display_name="MSBT Quick Menu Unstuck",
    description=(
        "Force-close Quick Menu and restore normal mouse/look/move input if the cursor "
        "gets stuck on screen after the menu."
    ),
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
