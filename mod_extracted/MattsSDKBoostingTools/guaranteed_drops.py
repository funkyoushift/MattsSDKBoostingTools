"""Opt-in native chance-roll override; starts off and is never persisted.

Evidence: docs/changes/2026-10-08-trainer-drop-rate.md. This matches the
trainer's zero-roll operation, not a promise to enumerate exclusive pools.
Only the locally inspected executable profile is supported.
"""
from __future__ import annotations

import ctypes
import struct
from ctypes import wintypes

PROFILE_TIMESTAMP = 1789399121
PROFILE_IMAGE_SIZE = 834191360
CONTEXT_RVA = 0x372DC9
CONTEXT = bytes.fromhex(
    "81 e5 ff 7f 00 00 0f 57 c0 f3 0f 2a c5 f3 0f 5e c6 "
    "44 0f 2e c7 76 06 44 0f 2e c0 73 19 49 81 c7 d0 00 00 00 "
    "49 81 c4 30 ff ff ff 0f 85 51 ff ff ff e9 7c 01 00 00"
)
PATCH_OFFSET = 9
ORIGINAL = bytes.fromhex("f3 0f 2a c5")  # cvtsi2ss xmm0, ebp
PATCHED = bytes.fromhex("0f 57 c0 90")   # xorps xmm0, xmm0; nop


class NativeMemory:
    """Current-process access only. No trainer, debugger, or remote process writes."""

    def __init__(self):
        self.pending_protections = {}
        self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        self.api.GetModuleHandleW.argtypes = (wintypes.LPCWSTR,)
        self.api.GetModuleHandleW.restype = wintypes.HMODULE
        self.api.GetCurrentProcess.restype = wintypes.HANDLE
        self.api.ReadProcessMemory.argtypes = (
            wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID,
            ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t),
        )
        self.api.ReadProcessMemory.restype = wintypes.BOOL
        self.api.WriteProcessMemory.argtypes = self.api.ReadProcessMemory.argtypes
        self.api.WriteProcessMemory.restype = wintypes.BOOL
        self.api.VirtualProtect.argtypes = (
            wintypes.LPVOID, ctypes.c_size_t, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
        )
        self.api.VirtualProtect.restype = wintypes.BOOL
        self.api.FlushInstructionCache.argtypes = (wintypes.HANDLE, wintypes.LPCVOID, ctypes.c_size_t)
        self.api.FlushInstructionCache.restype = wintypes.BOOL
        self.process = self.api.GetCurrentProcess()
        self.base = int(self.api.GetModuleHandleW("Borderlands4.exe") or 0)
        if not self.base:
            raise RuntimeError("Borderlands4.exe is not loaded in this process.")

    def read(self, address: int, size: int) -> bytes:
        buffer = ctypes.create_string_buffer(size)
        count = ctypes.c_size_t()
        if not self.api.ReadProcessMemory(self.process, address, buffer, size, ctypes.byref(count)) or count.value != size:
            raise RuntimeError("Could not read the native drop-rate site.")
        return buffer.raw

    def validate(self) -> None:
        header = self.read(self.base, 0x1000)
        pe = struct.unpack_from("<I", header, 0x3C)[0]
        if header[:2] != b"MZ" or not 0x40 <= pe <= 0xF00 or header[pe:pe + 4] != b"PE\0\0":
            raise RuntimeError("Unsupported game module header.")
        machine = struct.unpack_from("<H", header, pe + 4)[0]
        stamp = struct.unpack_from("<I", header, pe + 8)[0]
        size = struct.unpack_from("<I", header, pe + 0x50)[0]
        if (machine, stamp, size) != (0x8664, PROFILE_TIMESTAMP, PROFILE_IMAGE_SIZE):
            raise RuntimeError("This game build has not been qualified for 100% Drop Rate.")

    def write(self, address: int, data: bytes) -> None:
        old = wintypes.DWORD()
        if not self.api.VirtualProtect(address, len(data), 0x40, ctypes.byref(old)):
            raise RuntimeError("Could not unlock the native drop-rate site.")
        key = (address, len(data))
        # Preserve the first protection if a failed restore requires a later retry.
        self.pending_protections.setdefault(key, old.value)
        errors = []
        try:
            count = ctypes.c_size_t()
            buffer = ctypes.create_string_buffer(data)
            if not self.api.WriteProcessMemory(self.process, address, buffer, len(data), ctypes.byref(count)) or count.value != len(data):
                errors.append("Native drop-rate write failed")
            if not self.api.FlushInstructionCache(self.process, address, len(data)):
                errors.append("Instruction-cache flush failed")
        finally:
            try:
                self.restore_protections()
            except RuntimeError as exc:
                errors.append(str(exc))
        if errors:
            raise RuntimeError("; ".join(errors))

    def restore_protections(self) -> None:
        for (address, size), protection in tuple(self.pending_protections.items()):
            previous = wintypes.DWORD()
            if not self.api.VirtualProtect(address, size, protection, ctypes.byref(previous)):
                raise RuntimeError("Native page protection restore failed")
            del self.pending_protections[address, size]


class DropRateOverride:
    def __init__(self, memory_factory=NativeMemory):
        self.memory_factory = memory_factory
        self.memory = None
        self.owned = False
        self.last_error = ""

    def status(self) -> dict:
        active = False
        conflict = False
        if self.owned and self.memory is not None:
            try:
                current = self.memory.read(self.memory.base + CONTEXT_RVA + PATCH_OFFSET, len(ORIGINAL))
                active = current == PATCHED
                conflict = current != PATCHED
            except Exception as exc:
                conflict = True
                self.last_error = str(exc)
        return {"active": active, "owned": self.owned, "conflict": conflict,
                "last_error": self.last_error, "persisted": False}

    def set_enabled(self, enabled: bool) -> dict:
        acquired = False
        try:
            if enabled:
                if self.owned:
                    if not self.status()["active"]:
                        raise RuntimeError("Drop-rate site changed; refusing to overwrite another patch.")
                    restore = getattr(self.memory, "restore_protections", None)
                    if callable(restore):
                        restore()
                else:
                    memory = self.memory_factory()
                    memory.validate()
                    if memory.read(memory.base + CONTEXT_RVA, len(CONTEXT)) != CONTEXT:
                        raise RuntimeError("Drop-rate code differs from the inspected build (possibly another trainer/mod).")
                    self.memory = memory
                    # Retain ownership even if a partial write/readback fails, for explicit recovery.
                    self.owned = True
                    acquired = True
                    memory.write(memory.base + CONTEXT_RVA + PATCH_OFFSET, PATCHED)
                    if not self.status()["active"]:
                        raise RuntimeError("Drop-rate patch readback failed.")
            elif self.owned:
                address = self.memory.base + CONTEXT_RVA + PATCH_OFFSET
                current = self.memory.read(address, len(PATCHED))
                if current not in (PATCHED, ORIGINAL):
                    raise RuntimeError("Drop-rate site changed; original code was not restored over another patch.")
                if current == PATCHED:
                    self.memory.write(address, ORIGINAL)
                if self.memory.read(address, len(ORIGINAL)) != ORIGINAL:
                    raise RuntimeError("Drop-rate restoration readback failed.")
                restore = getattr(self.memory, "restore_protections", None)
                if callable(restore):
                    restore()
                self.owned = False
            self.last_error = ""
            message = ("100% Drop Rate ON: eligible positive-chance rolls are forced to zero. "
                       "Pool selection and eligibility still apply." if enabled else
                       "100% Drop Rate OFF: original chance-roll code restored.")
            return {"ok": True, "message": message, **self.status()}
        except Exception as exc:
            error = str(exc)
            if acquired:
                restored = self.set_enabled(False)
                if not restored["ok"]:
                    error += "; rollback: " + restored["message"]
            self.last_error = error
            return {"ok": False, "message": self.last_error, **self.status()}


override = DropRateOverride()


def clear_runtime_state() -> None:
    result = override.set_enabled(False)
    if not result["ok"]:
        raise RuntimeError(result["message"])
