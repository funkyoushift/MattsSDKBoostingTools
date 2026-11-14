"""Experimental direct SHiFT overlay; no pause-menu navigation."""
import time
import itertools
import sys
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
_capture_active = False
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



def _background_owns_view():
    """Do not duplicate cleanup while the companion owns native visibility."""
    companion = sys.modules.get("ShiftManagement")
    controller = getattr(companion, "_background", None)
    native = getattr(controller, "native", None)
    return bool(getattr(controller, "_ownership", False) or getattr(native, "owned", False))


def _other_ui_context_active(pc):
    """Read only this player's input contexts; unknown must not steal UI focus.

    Pause alone cannot distinguish SHiFT's own asynchronous transition from a
    different menu. The installed game's menu contexts do, while the cursor-only
    context used by SHiFT is deliberately excluded.
    """
    try:
        import unrealsdk as sdk
        if pc is None or getattr(pc, "Player", None) is None or getattr(pc, "Pawn", None) is None:
            return None
        subs = list(itertools.islice(sdk.find_all("EnhancedInputLocalPlayerSubsystem", False), 129))
        if len(subs) > 128:
            return None
        local = [item for item in subs if not str(item.Name).startswith("Default__") and item.Outer == pc.Player]
        if len(local) != 1:
            return None
        interface = sdk.find_class("/Script/EnhancedInput.EnhancedInputSubsystemInterface")
        fn = sdk.find_object("Function", "/Script/EnhancedInput.EnhancedInputSubsystemInterface:HasMappingContext")
        if interface is None or fn is None or not local[0].Class._implements(interface):
            return None
        contexts = list(itertools.islice((item for item in sdk.find_all("InputMappingContext", False)
                                         if not str(item.Name).startswith("Default__")), 129))
        if len(contexts) > 128:
            return None
        bound = sdk.unreal.BoundFunction(fn, local[0])
        for context in contexts:
            result = bound(context, 0)
            if (not isinstance(result, tuple) or len(result) != 2
                    or type(result[0]) is not bool or type(result[1]) is not int):
                return None
            if not result[0]:
                continue
            path = context._path_name()
            if not isinstance(path, str):
                return None
            normalized = path.casefold()
            if "/ui/" in normalized and "context_ui_cursor." not in normalized:
                return True
        return False if get_pc() == pc and local[0].Outer == pc.Player else None
    except Exception:
        return None


def release():
    from . import quick_menu
    if quick_menu.STATE.is_open:
        raise RuntimeError("Close the Quick Menu before releasing SHiFT input.")
    quick_menu._force_game_only_input()


def _restore_capture():
    global _capture_active
    # Recording support must never prevent the native menu from closing.
    try:
        from . import shift_capture
        _capture_status.clear()
        _capture_status.update(shift_capture.restore() or {})
    except Exception as exc:
        _capture_status["error"] = str(exc)


def control(mode="toggle"):
    global _last_action, _owner, _release_at, _message, _closing, _seen_visible, _capture_active
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
            _capture_active = True
            lib.Close()
            _restore_capture()
            _owner = pc
            _closing = True
            _release_at = [now + .25, now + .75, now + 1.5]
            release()
            _message = "SHiFT closing; restoring game input after shutdown."
        elif mode in ("toggle", "open"):
            _capture_active = True
            lib.Open(0)
            _owner = pc
            _closing = False
            _seen_visible = False
            # UI activation may apply its input mode on a following frame.
            _release_at = [now + .25, now + .75, now + 1.5]
            _message = "SHiFT opened directly; restoring gameplay input."
        elif mode == "record":
            _capture_active = True
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


def _record_visible_menu():
    """Recording is independent of F10 ownership and player input restoration."""
    global _capture_next, _capture_active
    now = time.monotonic()
    if now < _capture_next:
        return
    _capture_next = now + .25
    try:
        # Once SHiFT has been used, continue checking the owned game window.
        # Native open/close may apply exclusion after the visibility transition.
        if not _capture_active:
            _capture_active = bool(library().IsVisible())
        if _capture_active:
            from . import shift_capture
            result = shift_capture.enable()
            _capture_status.clear()
            _capture_status.update(result)
    except Exception as exc:
        _capture_status["error"] = str(exc)


def start():
    """Register controls without waiting for a visible UI widget to tick."""
    if not _bindings:
        try:
            for name, key, mode in (("MSBT SHiFT overlay", "F10", "toggle"),
                                    ("MSBT SHiFT release input", "F11", "release")):
                bind = keybind(name, key, callback=lambda mode=mode: control(mode), is_hidden=True, is_rebindable=False)
                _bindings.append(bind)
                bind.enable()
        except Exception:
            for bind in _bindings:
                bind.disable()
            _bindings.clear()
            raise


def tick():
    global _release_at, _owner, _message, _capture_next, _closing, _seen_visible
    start()
    if _owner is not None and get_pc() != _owner:
        _release_at = []; _owner = None
        _closing = False; _seen_visible = False
        _restore_capture()
    if _owner is not None and _background_owns_view():
        # Hidden native widgets are expected in background mode. That controller
        # now owns restoration; this foreground helper must not infer Back/Close.
        _release_at = []; _owner = None
        _closing = False; _seen_visible = False
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
    _record_visible_menu()
    if not _release_at:
        return
    if get_pc() != _owner:
        _release_at = []; _owner = None
        return
    now = time.monotonic()
    if now >= _release_at[0]:
        if _other_ui_context_active(_owner) is not False:
            # A newer menu (or an unreadable context) wins. Do not leave an old
            # timer capable of taking focus later; explicit F11 remains available.
            _release_at = []; _owner = None
            _closing = False; _seen_visible = False
            _message = "Deferred input restoration cancelled to preserve current menu focus."
            return
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
    global _release_at, _owner, _closing, _seen_visible, _capture_active
    if _capture_active:
        _restore_capture()
    _capture_active = False
    for binding in _bindings:
        binding.disable()
    _bindings.clear()
    _release_at = []; _owner = None
    _closing = False; _seen_visible = False
