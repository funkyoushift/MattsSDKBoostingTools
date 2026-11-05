"""Build-pinned SHiFT native view visibility primitive; no scheduling or hooks."""
from __future__ import annotations
import ctypes
import hashlib
import struct
import threading

EXPECTED_HASH = 'ba75f7c2874b16efb5536a5c0cc28918a03efd3e55d790d2e4db57de0c3a353a'
OWNER_VTABLE = 0xb4ff700
LISTENER_VTABLE = 0xb504990
CANVAS_VTABLE = 0x9f1bc50
SAFE_VTABLE = 0x9f153b0
OVERLAY_VTABLE = 0x9eeed90
BACKGROUND_VTABLE = 0xb506540
SETTER = 0xfe254e
SETTER_BYTES = bytes.fromhex('5657534883ec404889d64889cb488b05de53720b4831e048894424380fb70248')
VISIBILITY_CONSTANTS = ((0xc96b238, 0x19), (0xc96b1e1, 2), (0xc96b23b, 4),
                        (0xc96b23a, 1), (0xc96b23c, 0x11))


class IdentityChanged(RuntimeError):
    """The recorded owner or widgets no longer identify the current view."""


class NativeShiftView:
    def __init__(self, sdk):
        self.sdk = sdk
        self._thread = None
        self._owner = None
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
        self.kernel.GetModuleHandleW.restype = ctypes.c_void_p
        self.kernel.GetModuleFileNameW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint32]
        self.kernel.GetModuleFileNameW.restype = ctypes.c_uint32
        self.kernel.GetCurrentProcess.restype = ctypes.c_void_p
        self.kernel.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                                  ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        self.kernel.ReadProcessMemory.restype = ctypes.c_int
        self.base = int(self.kernel.GetModuleHandleW(None) or 0)
        name = ctypes.create_unicode_buffer(32768)
        length = self.kernel.GetModuleFileNameW(None, name, len(name))
        if not self.base or not length or length >= len(name):
            raise RuntimeError('Executable identity unavailable')
        digest = hashlib.sha256()
        with open(name.value, 'rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(chunk)
        if digest.hexdigest() != EXPECTED_HASH:
            raise RuntimeError('Unsupported executable hash')

    @property
    def owned(self):
        return self._owner is not None

    def bind_thread(self):
        ident = threading.get_ident()
        if self._thread is not None and self._thread != ident:
            raise RuntimeError('Native view is bound to another callback thread')
        self._thread = ident

    def _require_thread(self):
        if self._thread is None or self._thread != threading.get_ident():
            raise RuntimeError('Native mutation requires the bound callback thread')

    def _read(self, address, length):
        if not self.base or not address or length not in (1, 8, len(SETTER_BYTES)):
            raise RuntimeError('Native read guard failed')
        out = (ctypes.c_ubyte * length)()
        count = ctypes.c_size_t()
        if not self.kernel.ReadProcessMemory(self.kernel.GetCurrentProcess(), ctypes.c_void_p(address),
                                             out, length, ctypes.byref(count)) or count.value != length:
            raise RuntimeError('Native read failed')
        return bytes(out)

    def _u64(self, address):
        return struct.unpack('<Q', self._read(address, 8))[0]

    def _inspect(self):
        if self._read(self.base + SETTER, len(SETTER_BYTES)) != SETTER_BYTES:
            raise RuntimeError('Slate setter fingerprint changed')
        for offset, expected in VISIBILITY_CONSTANTS:
            if self._read(self.base + offset, 1)[0] != expected:
                raise RuntimeError('Slate visibility constants changed')
        obj = self.sdk.find_object('ShiftUI', '/Engine/Transient.Gearbox SHiFT UI')
        if obj is None:
            raise IdentityChanged('ShiftUI owner unavailable')
        owner = int(obj._get_address())
        singleton = self._u64(self.base + 0xcb98ab0)
        if not singleton or self._u64(singleton + 0x28) != owner or self._u64(owner) != self.base + OWNER_VTABLE:
            raise IdentityChanged('ShiftUI owner identity mismatch')
        listener = self._u64(owner + 0x188)
        if not listener or self._u64(listener) != self.base + LISTENER_VTABLE:
            raise IdentityChanged('ShiftUI listener identity mismatch')
        canvas = self._u64(listener + 0x50)
        if not canvas or self._u64(canvas) != self.base + CANVAS_VTABLE:
            raise IdentityChanged('ShiftUI canvas identity mismatch')
        canvas_visibility = self._read(canvas + 0x39, 1)[0]
        widgets = []
        for address, expected in ((owner + 0x1a8, SAFE_VTABLE), (owner + 0x1b8, OVERLAY_VTABLE),
                                  (listener + 0x60, BACKGROUND_VTABLE)):
            widget = self._u64(address)
            if not widget or self._u64(widget) != self.base + expected:
                raise IdentityChanged('Slate widget identity mismatch')
            if self._u64(self.base + expected + 0x1c0) != self.base + SETTER:
                raise RuntimeError('Slate setter identity mismatch')
            widgets.append((widget, self._read(widget + 0x39, 1)[0]))
        library = self.sdk.find_object('Class', '/Script/ShiftUI.ShiftUIFunctionLibrary')
        if library is None:
            raise RuntimeError('ShiftUI visibility unavailable')
        visible = library.ClassDefaultObject.IsVisible()
        if type(visible) is not bool:
            raise RuntimeError('Unexpected ShiftUI visibility')
        return (owner, listener, canvas, *(row[0] for row in widgets)), tuple(row[1] for row in widgets), canvas_visibility, visible

    def _current(self):
        try:
            identity, values, canvas, visible = self._inspect()
        except IdentityChanged:
            self._owner = None
            raise
        if self._owner is not None and identity != self._owner:
            self._owner = None
            raise IdentityChanged('ShiftUI lifetime changed')
        return identity, values, canvas, visible

    def inspect(self):
        _, values, canvas, visible = self._current()
        return {'visible': visible, 'visibility': list(values), 'canvas_visibility': canvas, 'owned': self.owned}

    def _set(self, widget, value):
        self._require_thread()
        if value not in (1, 0x19):
            raise ValueError('Unsupported visibility')
        attr = (ctypes.c_ubyte * 24)()
        if ctypes.addressof(attr) % 8:
            raise RuntimeError('Unaligned Slate attribute')
        attr[0], attr[1] = value, 1
        setter = ctypes.WINFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)(self.base + SETTER)
        setter(ctypes.c_void_p(widget), ctypes.cast(attr, ctypes.c_void_p))

    def enter(self):
        self._require_thread()
        if self.owned:
            raise RuntimeError('Native view is already owned')
        identity, values, canvas, visible = self._current()
        if not visible or canvas != 2 or values != (0x19, 0x19, 0x19):
            raise RuntimeError('Expected visible SHiFT with collapsed canvas and visible containers')
        self._owner = identity
        changed = []
        # Retain ownership on any partial failure; driver decides when to restore.
        for index in (2, 0, 1):
            _, now, current_canvas, now_visible = self._current()
            if current_canvas != 2:
                raise RuntimeError('Canvas changed during entry')
            if now != tuple(1 if i in changed else 0x19 for i in range(3)):
                raise RuntimeError('Visibility changed during entry')
            if now_visible != (2 not in changed):
                raise RuntimeError('Unexpected SHiFT visibility predicate')
            self._set(identity[3 + index], 1)
            changed.append(index)
        _, final, _, final_visible = self._current()
        if final != (1, 1, 1) or final_visible:
            raise RuntimeError('Entry verification failed')
        return self.inspect()

    def restore(self):
        self._require_thread()
        if not self.owned:
            raise RuntimeError('Native view is not owned')
        identity, values, _, visible = self._current()
        if not visible and values == (2, 2, 2):
            self._owner = None
            return {'restored': False, 'released_closed': True}
        if any(value not in (1, 0x19) for value in values):
            raise RuntimeError('Visibility changed externally; restore unresolved')
        for index in (0, 1, 2):
            _, now, _, _ = self._current()
            if any(value not in (1, 0x19) for value in now):
                raise RuntimeError('Visibility changed during restore')
            if now[index] == 1:
                self._set(identity[3 + index], 0x19)
        _, final, _, _ = self._current()
        if final != (0x19, 0x19, 0x19):
            raise RuntimeError('Restore verification failed')
        self._owner = None
        return {'restored': True, 'released_closed': False}
