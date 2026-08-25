"""Native AOB / vtable helpers for the vendored BL4 Third Person Camera (Renil)."""
from __future__ import annotations

import ctypes
import struct
from dataclasses import dataclass
from ctypes import wintypes

kernel32 = ctypes.windll.kernel32

kernel32.GetModuleHandleW.argtypes = (wintypes.LPCWSTR,)
kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.VirtualQuery.argtypes = (wintypes.LPCVOID, ctypes.c_void_p, ctypes.c_size_t)
kernel32.VirtualQuery.restype = ctypes.c_size_t
kernel32.VirtualProtect.argtypes = (
    wintypes.LPVOID,
    ctypes.c_size_t,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
)
kernel32.VirtualProtect.restype = wintypes.BOOL
kernel32.VirtualAlloc.argtypes = (
    wintypes.LPVOID,
    ctypes.c_size_t,
    wintypes.DWORD,
    wintypes.DWORD,
)
kernel32.VirtualAlloc.restype = wintypes.LPVOID
kernel32.VirtualFree.argtypes = (wintypes.LPVOID, ctypes.c_size_t, wintypes.DWORD)
kernel32.VirtualFree.restype = wintypes.BOOL

PAGE_EXECUTE_READWRITE = 0x40
PAGE_READWRITE = 0x04
PAGE_EXECUTE = 0x10
PAGE_EXECUTE_READ = 0x20
PAGE_EXECUTE_WRITECOPY = 0x80
MEM_COMMIT = 0x1000
MEM_RELEASE = 0x8000
MEM_RESERVE = 0x2000
MEM_FREE = 0x10000
MEM_IMAGE = 0x1000000
IMAGE_SCN_MEM_EXECUTE = 0x20000000


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wintypes.DWORD),
        ("PartitionId", wintypes.WORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wintypes.DWORD),
        ("Protect", wintypes.DWORD),
        ("Type", wintypes.DWORD),
    ]


class FNameRaw(ctypes.Structure):
    _fields_ = [
        ("comparison_index", ctypes.c_int32),
        ("number", ctypes.c_int32),
    ]


class FVectorRaw(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("z", ctypes.c_double),
    ]


class FRotatorRaw(ctypes.Structure):
    _fields_ = [
        ("pitch", ctypes.c_double),
        ("yaw", ctypes.c_double),
        ("roll", ctypes.c_double),
    ]


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_long),
        ("y", ctypes.c_long),
    ]


@dataclass(slots=True)
class Pose:
    loc_x: float
    loc_y: float
    loc_z: float
    pitch: float
    yaw: float
    roll: float
    fov: float


def module_base() -> int:
    handle = kernel32.GetModuleHandleW(None)
    return int(handle) if handle else 0


def module_size() -> int:
    base = module_base()
    if not base:
        return 0
    header = read_bytes(base, 0x1000)
    if header is None or len(header) < 0x1000:
        return 0
    e_lfanew = struct.unpack_from("<I", header, 0x3C)[0]
    size_of_image = struct.unpack_from("<I", header, e_lfanew + 0x50)[0]
    if 0 < size_of_image < 0x80000000:
        return size_of_image
    return 0


def iter_executable_sections() -> list[tuple[int, int, str]]:
    base = module_base()
    if not base:
        return []

    executable_protects = {
        PAGE_EXECUTE,
        PAGE_EXECUTE_READ,
        PAGE_EXECUTE_READWRITE,
        PAGE_EXECUTE_WRITECOPY,
    }

    sections: list[tuple[int, int, str]] = []
    address = base
    saw_module_region = False
    region_index = 0

    while True:
        mbi = MEMORY_BASIC_INFORMATION()
        queried = kernel32.VirtualQuery(ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not queried:
            break

        region_base = int(mbi.BaseAddress) if mbi.BaseAddress else 0
        region_size = int(mbi.RegionSize)
        allocation_base = int(mbi.AllocationBase) if mbi.AllocationBase else 0

        if region_base <= 0 or region_size <= 0:
            break

        if allocation_base == base:
            saw_module_region = True
            protect = int(mbi.Protect) & 0xFF
            if mbi.State == MEM_COMMIT and protect in executable_protects:
                region_name = f"exec_region_{region_index}"
                if mbi.Type == MEM_IMAGE:
                    region_name = f".text_like_{region_index}"
                sections.append((region_base, region_size, region_name))
                region_index += 1
        elif saw_module_region and region_base > base:
            break

        next_address = region_base + region_size
        if next_address <= address:
            break
        address = next_address

    return sections


def parse_pattern(pattern: str) -> list[int | None]:
    out: list[int | None] = []
    for token in pattern.split():
        if token in {"?", "??"}:
            out.append(None)
        else:
            out.append(int(token, 16))
    return out


def _longest_fixed_run(parsed: list[int | None]) -> tuple[int, int]:
    """Return (start, length) of the longest run of non-wildcard bytes in a pattern."""
    best_start = best_len = 0
    i = 0
    n = len(parsed)
    while i < n:
        if parsed[i] is None:
            i += 1
            continue
        j = i
        while j < n and parsed[j] is not None:
            j += 1
        if j - i > best_len:
            best_len = j - i
            best_start = i
        i = j
    return best_start, best_len


def aob_scan(pattern: str) -> int | None:
    # Anchor on the longest run of fixed bytes and let bytes.find (C speed) jump
    # between candidate positions, instead of comparing every offset from Python.
    # The previous naive per-byte loop took minutes on BL4's ~240MB code section
    # and froze the game on enable; this returns in milliseconds.
    parsed = parse_pattern(pattern)
    needle_len = len(parsed)
    anchor_start, anchor_len = _longest_fixed_run(parsed)
    if anchor_len == 0:
        return None
    anchor = bytes(parsed[anchor_start : anchor_start + anchor_len])

    for section_base, section_size, _ in iter_executable_sections():
        haystack = read_bytes(section_base, section_size)
        if haystack is None or len(haystack) < needle_len:
            continue
        pos = 0
        while True:
            hit = haystack.find(anchor, pos)
            if hit < 0:
                break
            start = hit - anchor_start
            if 0 <= start and start + needle_len <= len(haystack):
                for off, token in enumerate(parsed):
                    if token is not None and haystack[start + off] != token:
                        break
                else:
                    return section_base + start
            pos = hit + 1
    return None


def scan_diagnostics(pattern: str) -> dict[str, object]:
    sections = iter_executable_sections()
    return {
        "module_base": module_base(),
        "module_size": module_size(),
        "pattern": pattern,
        "pattern_len": len(parse_pattern(pattern)),
        "sections": [
            {
                "name": name,
                "base": section_base,
                "size": section_size,
            }
            for section_base, section_size, name in sections
        ],
    }


def is_range_accessible(address: int, size: int, *, write: bool = False) -> bool:
    if address < 0x10000 or size <= 0:
        return False
    mbi = MEMORY_BASIC_INFORMATION()
    queried = kernel32.VirtualQuery(ctypes.c_void_p(address), ctypes.byref(mbi), ctypes.sizeof(mbi))
    if not queried:
        return False
    if mbi.State != MEM_COMMIT or mbi.Protect == 0:
        return False
    region_end = int(mbi.BaseAddress) + int(mbi.RegionSize)
    if address + size > region_end:
        return False
    protect = int(mbi.Protect) & 0xFF
    readable = protect not in (0x01, 0x00)
    writable = protect in (0x04, 0x08, 0x40, 0x80)
    return writable if write else readable


def read_bytes(address: int, size: int) -> bytes | None:
    if not is_range_accessible(address, size):
        return None
    return ctypes.string_at(address, size)


def write_bytes(address: int, data: bytes) -> bool:
    if not data:
        return True
    old_protect = wintypes.DWORD()
    if not kernel32.VirtualProtect(ctypes.c_void_p(address), len(data), PAGE_EXECUTE_READWRITE, ctypes.byref(old_protect)):
        return False
    ctypes.memmove(address, data, len(data))
    restored = wintypes.DWORD()
    kernel32.VirtualProtect(ctypes.c_void_p(address), len(data), old_protect.value, ctypes.byref(restored))
    return True


def alloc_executable(size: int) -> int:
    return int(
        kernel32.VirtualAlloc(
            None,
            size,
            MEM_COMMIT | MEM_RESERVE,
            PAGE_EXECUTE_READWRITE,
        )
    )


def free_executable(address: int) -> None:
    if address:
        kernel32.VirtualFree(ctypes.c_void_p(address), 0, MEM_RELEASE)


def make_abs_jump(target: int) -> bytes:
    return b"\x48\xB8" + struct.pack("<Q", target) + b"\xFF\xE0"


class InlineHook:
    def __init__(self, target: int, callback_ptr: int, length: int) -> None:
        self.target = target
        self.callback_ptr = callback_ptr
        self.length = length
        self.original = b""
        self.trampoline = 0
        self.installed = False

    def install(self) -> bool:
        if self.installed:
            return True
        self.original = read_bytes(self.target, self.length) or b""
        if len(self.original) != self.length:
            return False
        self.trampoline = alloc_executable(self.length + 16)
        if not self.trampoline:
            return False
        trampoline_bytes = self.original + make_abs_jump(self.target + self.length)
        if not write_bytes(self.trampoline, trampoline_bytes):
            free_executable(self.trampoline)
            self.trampoline = 0
            return False
        patch = make_abs_jump(self.callback_ptr)
        patch = patch + (b"\x90" * max(self.length - len(patch), 0))
        if not write_bytes(self.target, patch[: self.length]):
            free_executable(self.trampoline)
            self.trampoline = 0
            return False
        self.installed = True
        return True

    def uninstall(self) -> None:
        if self.installed and self.original:
            write_bytes(self.target, self.original)
        if self.trampoline:
            free_executable(self.trampoline)
        self.trampoline = 0
        self.installed = False

    def original_function(self, restype: ctypes._CData, *argtypes: ctypes._CData):
        return ctypes.CFUNCTYPE(restype, *argtypes)(self.trampoline)


class VTableHook:
    def __init__(self, vtable_entry_address: int, callback_ptr: int) -> None:
        self.vtable_entry_address = vtable_entry_address
        self.callback_ptr = callback_ptr
        self.original = 0
        self.installed = False

    def install(self) -> bool:
        if self.installed:
            return True
        original = read_pointer(self.vtable_entry_address)
        if not original:
            return False
        if not write_pointer(self.vtable_entry_address, self.callback_ptr):
            return False
        self.original = original
        self.installed = True
        return True

    def uninstall(self) -> None:
        if self.installed and self.original:
            write_pointer(self.vtable_entry_address, self.original)
        self.original = 0
        self.installed = False


def read_float(address: int) -> float | None:
    data = read_bytes(address, 4)
    if data is None:
        return None
    return struct.unpack("<f", data)[0]


def write_float(address: int, value: float) -> bool:
    return write_bytes(address, struct.pack("<f", float(value)))


def read_double(address: int) -> float | None:
    data = read_bytes(address, 8)
    if data is None:
        return None
    return struct.unpack("<d", data)[0]


def write_double(address: int, value: float) -> bool:
    return write_bytes(address, struct.pack("<d", float(value)))


def read_pointer(address: int) -> int | None:
    data = read_bytes(address, ctypes.sizeof(ctypes.c_void_p))
    if data is None:
        return None
    return struct.unpack("<Q", data)[0]


def write_pointer(address: int, value: int) -> bool:
    return write_bytes(address, struct.pack("<Q", int(value)))


def read_int32(address: int) -> int | None:
    data = read_bytes(address, 4)
    if data is None:
        return None
    return struct.unpack("<i", data)[0]


def read_fname(address: int) -> FNameRaw | None:
    data = read_bytes(address, ctypes.sizeof(FNameRaw))
    if data is None:
        return None
    return FNameRaw.from_buffer_copy(data)


def write_fname(address: int, value: FNameRaw) -> bool:
    return write_bytes(address, bytes(value))
