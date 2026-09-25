"""Allow recording of the game's own window during the custom SHiFT overlay."""
import ctypes
from ctypes import wintypes
import os

_saved = {}


def _api():
    api = ctypes.WinDLL("user32", use_last_error=True)
    callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    api.EnumWindows.argtypes = [callback, wintypes.LPARAM]
    api.EnumWindows.restype = wintypes.BOOL
    api.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    api.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    api.GetWindowDisplayAffinity.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    api.GetWindowDisplayAffinity.restype = wintypes.BOOL
    api.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
    api.SetWindowDisplayAffinity.restype = wintypes.BOOL
    return api, callback


def enable():
    api, callback = _api()
    windows = []
    def visit(hwnd, _):
        pid = wintypes.DWORD()
        api.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == os.getpid():
            name = ctypes.create_unicode_buffer(128)
            api.GetClassNameW(hwnd, name, len(name))
            if name.value == "UnrealWindow": windows.append(hwnd)
        return True
    api.EnumWindows(callback(visit), 0)
    if len(windows) != 1:
        raise RuntimeError(f"Expected one game window, found {len(windows)}")
    hwnd = windows[0]
    previous = wintypes.DWORD()
    if not api.GetWindowDisplayAffinity(hwnd, ctypes.byref(previous)):
        raise ctypes.WinError(ctypes.get_last_error())
    if previous.value:
        _saved.setdefault(hwnd, previous.value)
        if not api.SetWindowDisplayAffinity(hwnd, 0):
            raise ctypes.WinError(ctypes.get_last_error())
    current = wintypes.DWORD()
    if not api.GetWindowDisplayAffinity(hwnd, ctypes.byref(current)) or current.value != 0:
        raise RuntimeError("Recording flag did not clear")
    return {"window": hwnd, "capture_affinity": current.value}


def restore():
    if not _saved: return
    api, _ = _api()
    for hwnd, previous in list(_saved.items()):
        pid = wintypes.DWORD()
        api.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value == os.getpid(): api.SetWindowDisplayAffinity(hwnd, previous)
    _saved.clear()
