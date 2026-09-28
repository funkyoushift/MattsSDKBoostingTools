"""Build-gated native inventory insertion. Call only from the game thread.

Recovered against Steam build 25372571; see docs/DIRECT_INVENTORY_DELIVERY.md.
Never use these offsets without all four full-function byte gates passing.
"""
from __future__ import annotations

import ctypes as C
import hashlib
import struct


GATES = (
    (0x88E2A4, 739, 'b6a8e1ca11d24319a5abb85d175b549e54e83d7dc42d9c66fa5457d481e8bba2'),
    (0x369D14, 184, '69745be40196a35f3df4aa98c5f0453fbd12018fd71925dc5fe0d3d76a91c559'),
    (0x12E8E74, 22, '44645cf9f58a57466dd40e044c9d7044acee0700bc6ca3bc23d60b53fda8f66f'),
    (0x12E8E8A, 1873, 'a0099f4889e57f7f5e3706d4f1f97a4dabd47053c6f4b835412a2f4f8161ba84'),
)


class FString(C.Structure):
    _fields_ = [('data', C.c_void_p), ('num', C.c_int32), ('max', C.c_int32)]


class MemoryInfo(C.Structure):
    _fields_ = [('BaseAddress', C.c_void_p), ('AllocationBase', C.c_void_p),
                ('AllocationProtect', C.c_ulong), ('PartitionId', C.c_ushort),
                ('RegionSize', C.c_size_t), ('State', C.c_ulong),
                ('Protect', C.c_ulong), ('Type', C.c_ulong)]


class NativeInventory:
    def __init__(self):
        if not hasattr(C, 'WinDLL') or C.sizeof(C.c_void_p) != 8:
            raise RuntimeError('Direct inventory delivery requires the supported Windows x64 game build.')
        kernel = C.WinDLL('kernel32', use_last_error=True)
        kernel.GetModuleHandleW.argtypes = [C.c_wchar_p]
        kernel.GetModuleHandleW.restype = C.c_void_p
        self.base = kernel.GetModuleHandleW(None)
        kernel.VirtualQuery.argtypes = [C.c_void_p, C.POINTER(MemoryInfo), C.c_size_t]
        kernel.VirtualQuery.restype = C.c_size_t
        self.query = kernel.VirtualQuery
        for rva, size, digest in GATES:
            if hashlib.sha256(self.read(self.base + rva, size)).hexdigest() != digest:
                raise RuntimeError('This game build is not supported by direct inventory delivery; no items sent.')
        import unrealsdk
        self.flags = int(unrealsdk.find_enum('EInventoryItemFlags').AllowOverflow)
        if self.flags != 8:
            raise RuntimeError('Native inventory flags changed; no items sent.')
        self.construct = C.CFUNCTYPE(C.c_bool, C.c_void_p, C.POINTER(FString))(self.base + 0x88E2A4)
        self.destroy = C.CFUNCTYPE(None, C.c_void_p)(self.base + 0x369D14)
        self.insert = C.CFUNCTYPE(None, C.c_void_p, C.c_void_p, C.c_int32, C.c_int32, C.c_int32)(self.base + 0x12E8E74)

    def read(self, ptr, size):
        info = MemoryInfo()
        if not ptr or not 0 <= size <= 1048576 or not self.query(ptr, C.byref(info), C.sizeof(info)):
            raise ValueError('Invalid native memory range')
        if info.State != 0x1000 or info.Protect & 0x101 or ptr + size > info.BaseAddress + info.RegionSize:
            raise ValueError('Unreadable native memory range')
        return C.string_at(ptr, size)

    def u64(self, ptr):
        return struct.unpack('<Q', self.read(ptr, 8))[0]

    def validate_controller(self, pc):
        interface = int(pc._get_address()) + 0xE38
        if self.u64(self.u64(interface) + 0x30) != self.base + 0x12E8E74:
            raise RuntimeError('Inventory owner interface changed')
        if self.read(interface - 0xCC0, 1) != b'\x03':
            raise RuntimeError('Direct inventory delivery requires host authority')
        return interface

    def add(self, pc, serial):
        interface = self.validate_controller(pc)
        if not serial.startswith('@U') or not serial.isascii() or len(serial) > 8192:
            raise ValueError('Serial is outside the tested direct-delivery format or size')
        storage = C.create_string_buffer(0xD8)
        address = C.addressof(storage)
        if address % 16:
            raise RuntimeError('Inventory identity is not 16-byte aligned')
        C.memmove(address + 0x68, bytes.fromhex('0000000080000000ffffffff00000000'), 16)
        C.c_uint64.from_address(address + 0xB8).value = 15
        C.c_uint16.from_address(address + 0xC0).value = 1
        text = C.create_unicode_buffer(serial)
        value = FString(C.addressof(text), len(serial) + 1, len(serial) + 1)
        try:
            built = self.construct(address, C.byref(value))
            count = struct.unpack('<i', self.read(address + 0x18, 4))[0]
            if not built or not 0 < count <= 8192:
                raise RuntimeError('Item did not resolve into a native inventory identity')
            parts = self.u64(address + 0x10)
            if any(not self.u64(parts + i * 8) for i in range(count)):
                raise RuntimeError('Item contains an unresolved native part')
            length, capacity = self.u64(address + 0xB0), self.u64(address + 0xB8)
            if not 0 < length <= 8192:
                raise RuntimeError('Constructed serial length is invalid')
            ptr = address + 0xA0 if capacity <= 15 else self.u64(address + 0xA0)
            if self.read(ptr, length).rstrip(b'\0').decode('ascii') != serial:
                raise RuntimeError('Constructed serial differs from requested serial')
            # Native call copies the identity. No reward creation, inventory clear,
            # equipment rewrite, or backpack-capacity modification is involved.
            self.insert(interface, address, self.flags, -1, 0)
        finally:
            self.destroy(address)
