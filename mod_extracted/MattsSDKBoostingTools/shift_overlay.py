"""Experimental direct SHiFT overlay; no pause-menu navigation."""
import time
from mods_base import get_pc, keybind
from unrealsdk import find_object

_bindings = []
_release_at = []
_last_action = -10.0
_owner = None
_closing = False
_seen_visible = False
_capture_next = 0.0
_capture_status = {}
_message = "F10: toggle SHiFT overlay. F11: release game input."


def library():
    return find_object("Class", "/Script/ShiftUI.ShiftUIFunctionLibrary").ClassDefaultObject


def status():
    pc = get_pc()
    try:
        visible = bool(library().IsVisible())
        initialized = bool(library().IsInitialized())
    except Exception:
        visible, initialized = False, False
    def read_call(name):
        try: return bool(getattr(pc, name)())
        except Exception: return None
    return {"visible": visible, "initialized": initialized, "message": _message,
            "capture": dict(_capture_status), "block_input": getattr(pc, "bBlockInput", None),
            "ignore_move": read_call("IsMoveInputIgnored"), "ignore_look": read_call("IsLookInputIgnored")}


def release():
    from . import quick_menu
    if quick_menu.STATE.is_open:
        raise RuntimeError("Close the Quick Menu before releasing SHiFT input.")
    quick_menu._force_game_only_input()


def _restore_capture():
    # Recording support must never prevent the native menu from closing.
    try:
        from . import shift_capture
        shift_capture.restore()
    except Exception as exc:
        _capture_status["error"] = str(exc)


def control(mode="toggle"):
    global _last_action, _owner, _release_at, _message, _closing, _seen_visible
    try:
        now = time.monotonic()
        if mode == "toggle" and now - _last_action < .35:
            return {"ok": True, **status()}
        pc = get_pc()
        if pc is None:
            raise RuntimeError("Load your character first.")
        from . import quick_menu
        if quick_menu.STATE.is_open:
            raise RuntimeError("Close the Quick Menu first.")
        lib = library()
        if mode == "close" or (mode == "toggle" and lib.IsVisible()):
            _restore_capture()
            lib.Close()
            _owner = pc
            _closing = True
            _release_at = [now + .25, now + .75, now + 1.5]
            release()
            _message = "SHiFT closing; restoring game input after shutdown."
        elif mode in ("toggle", "open"):
            lib.Open(0)
            _owner = pc
            _closing = False
            _seen_visible = False
            # UI activation may apply its input mode on a following frame.
            _release_at = [now + .25, now + .75, now + 1.5]
            _message = "SHiFT opened directly; restoring gameplay input."
        elif mode == "record":
            from . import shift_capture
            _capture_status.update(shift_capture.enable())
            _message = "Game window recording enabled."
        elif mode == "release":
            release()
            _message = "Requested gameplay input with SHiFT still visible."
        else:
            raise ValueError("Unknown SHiFT overlay control.")
        _last_action = now
        return {"ok": True, **status()}
    except Exception as exc:
        _message = str(exc)
        return {"ok": False, "message": _message}


def tick():
    global _release_at, _owner, _message, _capture_next, _closing, _seen_visible
    if not _bindings:
        for name, key, mode in (("MSBT SHiFT overlay", "F10", "toggle"),
                                ("MSBT SHiFT release input", "F11", "release")):
            bind = keybind(name, key, callback=lambda mode=mode: control(mode), is_hidden=True, is_rebindable=False)
            bind.enable()
            _bindings.append(bind)
    if _owner is not None and get_pc() != _owner:
        _release_at = []; _owner = None
        _closing = False; _seen_visible = False
        _restore_capture()
    if _owner is not None:
        try:
            visible = bool(library().IsVisible())
            if visible:
                _seen_visible = True
            elif _seen_visible and not _closing:
                # Escape/native Back bypasses control("close").
                _restore_capture()
                _closing = True
                now = time.monotonic()
                _release_at = [now, now + .25, now + .75, now + 1.5]
        except Exception:
            pass
    if _owner is not None and time.monotonic() >= _capture_next:
        _capture_next = time.monotonic() + 1.0
        try:
            if not _closing and library().IsVisible():
                from . import shift_capture
                _capture_status.update(shift_capture.enable())
        except Exception as exc:
            _capture_status["error"] = str(exc)
    if not _release_at:
        return
    if get_pc() != _owner:
        _release_at = []; _owner = None
        return
    now = time.monotonic()
    if now >= _release_at[0]:
        _release_at.pop(0)
        try:
            release()
            _message = "SHiFT closed; game input restored." if _closing else "Gameplay input requested; SHiFT remains open."
        except Exception as exc:
            _release_at = []
            _message = str(exc)
        if _closing and not _release_at:
            _owner = None
            _closing = False
            _seen_visible = False


def stop():
    global _release_at, _owner, _closing, _seen_visible
    _restore_capture()
    for binding in _bindings:
        binding.disable()
    _bindings.clear()
    _release_at = []; _owner = None
    _closing = False; _seen_visible = False
