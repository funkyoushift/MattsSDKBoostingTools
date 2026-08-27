"""In-game Phone Pairing overlay (native UMG).

Does not import BLImGui. Does not import the HTTP bridge module (LAN state lives
in mobile_lan; the bridge registers a rebind callback). Same tick family as F7.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable

import unrealsdk
from mods_base import command, get_pc, keybind
from unrealsdk import logging

from . import mobile_lan, qr_lite

PREFIX = "[Matts SDK Boosting Tools | Pairing]"
DESIGN_W = 1920.0
DESIGN_H = 1080.0
VIEWPORT_Z = 999997
C_TEXT = (1.0, 1.0, 1.0, 1.0)
C_DIM = (0.44, 0.95, 1.0, 1.0)
C_OUTLINE = (0.02, 0.02, 0.02, 1.0)
C_DOCK = (0.04, 0.01, 0.27, 0.98)
C_HEADER = (1.0, 0.18, 0.44, 1.0)
C_BTN = (0.0, 0.90, 1.0, 0.99)
C_DANGER = (0.82, 0.10, 0.12, 0.98)
C_MUTED = (0.16, 0.04, 0.29, 0.96)


@dataclass
class ButtonRef:
    widget: Any
    action: Callable[[], None]
    label: str
    was_pressed: bool = False


@dataclass
class PairingState:
    started: bool = False
    is_open: bool = False
    overlay: Any = None
    tree: Any = None
    root: Any = None
    canvas: Any = None
    buttons: list[ButtonRef] = field(default_factory=list)
    input_owner: Any = None
    key_escape: bool = False
    last_input_refresh: float = 0.0
    ui_dirty: bool = True
    status: str = "Phone Pairing"


STATE = PairingState()


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


class PairUMG:
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
        try_call(slot, "SetPosition", vec2(x, y))
        try_call(slot, "SetSize", vec2(w, h))
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
        tint: tuple[float, float, float, float] = C_TEXT,
    ) -> Any:
        widget = self.widget("/Script/UMG.TextBlock")
        try_call(widget, "SetText", str(value))
        try_call(widget, "SetRenderScale", vec2(scale, scale))
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
        z: int = 50,
        scale: float = 0.40,
    ) -> Any:
        self.border(parent, x - 2, y - 2, w + 4, h + 4, C_OUTLINE, z)
        self.border(parent, x, y, w, h, fill, z)
        widget = self.widget("/Script/UMG.Button")
        self.add(parent, widget)
        self.slot(widget, x, y, w, h, z + 1)
        try_call(widget, "SetVisibility", 0)
        try_call(widget, "SetIsEnabled", True)
        try_call(widget, "SetRenderOpacity", 0.03)
        self.text(parent, label, x + 8, y + 8, w - 16, h - 14, scale=scale, z=z + 2, center=True)
        STATE.buttons.append(ButtonRef(widget, action, label))
        return widget


def _create_overlay() -> Any:
    if live(STATE.overlay) and live(STATE.root):
        return STATE.overlay
    pc = get_pc()
    if pc is None:
        raise RuntimeError("Load into gameplay before opening Phone Pairing")
    widget = construct("/Script/UMG.UserWidget", pc)
    widget.WidgetTree = construct("/Script/UMG.WidgetTree", widget)
    root = construct("/Script/UMG.CanvasPanel", widget.WidgetTree)
    widget.WidgetTree.RootWidget = root
    try_call(root, "SetVisibility", 0)
    try_call(root, "SetIsEnabled", True)
    try_call(widget, "SetAlignmentInViewport", vec2(0.0, 0.0))
    try_call(widget, "SetPositionInViewport", vec2(0.0, 0.0), False)
    try_call(widget, "SetDesiredSizeInViewport", vec2(DESIGN_W, DESIGN_H))
    try_call(widget, "AddToViewport", VIEWPORT_Z)
    try_call(widget, "SetVisibility", 0)
    try_call(widget, "ForceLayoutPrepass")
    STATE.overlay, STATE.tree, STATE.root = widget, widget.WidgetTree, root
    return widget


def _apply_input_mode() -> None:
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
    _apply_input_mode()
    STATE.last_input_refresh = time.monotonic()


def restore_input() -> None:
    pc = STATE.input_owner if live(STATE.input_owner) else get_pc()
    STATE.input_owner = None
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


def _draw_qr(factory: PairUMG, parent: Any, matrix: list[list[int]], x: float, y: float, box: float, z: int) -> None:
    if not matrix:
        return
    n = len(matrix)
    cell = box / float(n)
    # Phone cameras need a real quiet zone. Overlap modules so UMG subpixel gaps
    # do not split finder patterns into unreadable stripes.
    quiet = max(18.0, cell * 4.0)
    overlap = max(1.25, cell * 0.22)
    factory.border(parent, x - quiet, y - quiet, box + quiet * 2.0, box + quiet * 2.0, (1.0, 1.0, 1.0, 1.0), z)
    for row_i, row in enumerate(matrix):
        col = 0
        while col < n:
            if not row[col]:
                col += 1
                continue
            start = col
            while col < n and row[col]:
                col += 1
            factory.border(
                parent,
                x + start * cell,
                y + row_i * cell,
                (col - start) * cell + overlap,
                cell + overlap,
                (0.0, 0.0, 0.0, 1.0),
                z + 1,
            )


def rebuild_ui() -> None:
    overlay = _create_overlay()
    factory = PairUMG(overlay)
    remove_widget(STATE.canvas)
    STATE.buttons.clear()
    canvas = factory.widget("/Script/UMG.CanvasPanel")
    try_call(canvas, "SetVisibility", 0)
    try_call(canvas, "SetIsEnabled", True)
    factory.add(STATE.root, canvas)
    factory.slot(canvas, 0, 0, DESIGN_W, DESIGN_H, 0)
    STATE.canvas = canvas

    px, py, pw, ph = 220.0, 36.0, 1480.0, 1008.0
    factory.border(canvas, px - 4, py - 4, pw + 8, ph + 8, C_HEADER, 1)
    factory.border(canvas, px, py, pw, ph, C_DOCK, 2)
    factory.text(canvas, "Phone Pairing", px + 24, py + 16, 700, 48, scale=0.72, z=10)
    factory.text(
        canvas,
        "Scan Install or Pair. LAN stay-on after a phone pairs until you turn it off. Console: msbt_mobile_pair",
        px + 24,
        py + 68,
        pw - 48,
        36,
        scale=0.32,
        z=10,
        tint=C_DIM,
    )

    pair_text = mobile_lan.pairing_payload_text()
    install_text = mobile_lan.install_payload_text()
    payload = mobile_lan.pairing_payload()
    hosts = payload.get("hosts") or []
    nonce = str(payload.get("n") or "")
    port = payload.get("port") or 49774
    qr_box = 400.0
    left_x = px + 40.0
    right_x = px + 760.0
    qr_y = py + 120.0
    factory.text(canvas, "Install APK", left_x, qr_y - 28, 400, 28, scale=0.38, z=10, tint=C_DIM)
    factory.text(canvas, "Pair to game", right_x, qr_y - 28, 400, 28, scale=0.38, z=10, tint=C_DIM)
    try:
        _draw_qr(factory, canvas, qr_lite.encode(install_text), left_x, qr_y, qr_box, 20)
    except Exception as exc:
        factory.text(canvas, f"Install QR failed: {exc}", left_x, qr_y, qr_box, 40, scale=0.28, z=21)
    try:
        _draw_qr(factory, canvas, qr_lite.encode(pair_text), right_x, qr_y, qr_box, 20)
    except Exception as exc:
        factory.text(canvas, f"Pair QR failed: {exc}", right_x, qr_y, qr_box, 40, scale=0.28, z=21)

    host_line = ", ".join(str(h) for h in hosts) or "(no LAN IPv4 found)"
    factory.text(
        canvas,
        f"IP {host_line}  ·  port {port}  ·  nonce {nonce}",
        px + 40,
        qr_y + qr_box + 40,
        pw - 80,
        32,
        scale=0.30,
        z=10,
        tint=C_DIM,
    )
    factory.text(
        canvas,
        "Windows Firewall may ask on first LAN listen — allow private networks.",
        px + 40,
        qr_y + qr_box + 72,
        pw - 80,
        28,
        scale=0.28,
        z=10,
        tint=C_DIM,
    )

    lan_on = mobile_lan.lan_enabled()
    by = qr_y + qr_box + 114
    factory.button(
        canvas,
        "LAN On" if lan_on else "LAN Off",
        px + 40,
        by,
        220,
        48,
        _toggle_lan,
        fill=C_BTN if lan_on else C_MUTED,
    )
    factory.button(canvas, "Revoke phones", px + 280, by, 240, 48, _revoke_all, fill=C_DANGER)
    factory.button(canvas, "Close", px + pw - 220, by, 180, 48, close_panel, fill=C_HEADER)

    phones = mobile_lan.list_phones()
    factory.text(
        canvas,
        f"Remembered phones: {len(phones)}" if phones else "No phones remembered yet.",
        px + 40,
        by + 64,
        pw - 80,
        28,
        scale=0.32,
        z=10,
        tint=C_DIM,
    )
    row_y = by + 100
    for phone in phones[:6]:
        label = f"{phone.get('name') or 'Phone'}  {phone.get('ip') or ''}"
        factory.text(canvas, label, px + 40, row_y, 900, 28, scale=0.30, z=10)
        token = str(phone.get("token") or phone.get("ip") or "")
        factory.button(
            canvas,
            "Revoke",
            px + 980,
            row_y - 6,
            140,
            36,
            (lambda key=token: _revoke_one(key)),
            fill=C_DANGER,
            scale=0.32,
        )
        row_y += 42

    factory.text(canvas, STATE.status, px + 40, py + ph - 48, pw - 80, 32, scale=0.30, z=10, tint=C_DIM)
    STATE.ui_dirty = False


def _toggle_lan() -> None:
    nxt = not mobile_lan.lan_enabled()
    mobile_lan.set_lan_enabled(nxt)
    STATE.status = "LAN listen on." if nxt else "LAN listen off. Pairing enroll still open until you close this overlay."
    STATE.ui_dirty = True


def _revoke_all() -> None:
    mobile_lan.revoke_all()
    STATE.status = "All remembered phones revoked."
    STATE.ui_dirty = True


def _revoke_one(key: str) -> None:
    if mobile_lan.revoke_phone(key):
        STATE.status = "Phone revoked."
    else:
        STATE.status = "Could not revoke that phone."
    STATE.ui_dirty = True


def _sync_camera_need() -> None:
    try:
        from . import camera_tick
    except Exception:
        return
    camera_tick.set_needed("quick_menu_mobile_pair", bool(STATE.is_open))


def open_panel() -> None:
    if STATE.is_open:
        return
    mobile_lan.arm_enroll()
    mobile_lan.set_lan_enabled(True)
    STATE.is_open = True
    STATE.ui_dirty = True
    STATE.status = "Scan Pair QR on the phone. Closing this overlay stops new enrolls."
    try:
        rebuild_ui()
        capture_input()
    except Exception as exc:
        STATE.is_open = False
        mobile_lan.disarm_enroll()
        _log(f"Open failed: {exc!r}")
        return
    _sync_camera_need()
    _log("Phone Pairing open — Install QR is the download page; Pair QR is this session.")


def close_panel() -> None:
    if not STATE.is_open and not live(STATE.overlay):
        return
    STATE.is_open = False
    mobile_lan.disarm_enroll()
    STATE.buttons.clear()
    remove_widget(STATE.canvas)
    STATE.canvas = None
    if live(STATE.overlay):
        try_call(STATE.overlay, "RemoveFromViewport")
        try_call(STATE.overlay, "RemoveFromParent")
    STATE.overlay = STATE.tree = STATE.root = None
    restore_input()
    _sync_camera_need()
    _log("Phone Pairing closed")


def toggle_panel() -> None:
    if STATE.is_open:
        close_panel()
    else:
        open_panel()


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


def poll_buttons() -> None:
    for ref in list(STATE.buttons):
        if not live(ref.widget):
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


def tick(_obj: Any = None, _args: Any = None, _ret: Any = None, _func: Any = None) -> None:
    if not STATE.is_open:
        return None
    try:
        pc = get_pc()
        now = time.monotonic()
        if now - STATE.last_input_refresh >= 0.5:
            capture_input()
        down = _key_down(pc, "Escape")
        was = STATE.key_escape
        STATE.key_escape = down
        if down and not was:
            close_panel()
            return None
        poll_buttons()
        if STATE.is_open and STATE.ui_dirty:
            rebuild_ui()
    except Exception as exc:
        _log(f"Tick failed: {exc}")
    return None


def start_mobile_pairing() -> None:
    if STATE.started:
        return
    try:
        from . import camera_tick

        camera_tick.register("quick_menu_mobile_pair", tick, priority=12)
        _sync_camera_need()
        STATE.started = True
        _log("Phone Pairing tick registered")
    except Exception as exc:
        _log(f"Phone Pairing tick not installed yet: {exc!r}")


mobile_pair_toggle = keybind(
    "MSBT Phone Pairing",
    None,
    callback=toggle_panel,
    display_name="MSBT Phone Pairing",
    description=(
        "Open the in-game phone pairing overlay (install QR, pair QR, LAN listen). "
        "Unbound by default because F8 opens the golden chest. Bind a key in oak2, "
        "or run msbt_mobile_pair."
    ),
)


@command("msbt_mobile_pair", description="Open or close the MSBT in-game phone pairing overlay.")
def _cmd_msbt_mobile_pair(_args: Any = None) -> None:
    toggle_panel()
