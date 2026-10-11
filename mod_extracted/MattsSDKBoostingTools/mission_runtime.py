"""Build-pinned native mission reads; game-thread calls only.
Evidence: docs/changes/2026-10-10-mission-test-preflight.md.
No BL4Introspection, developer paths, replay calls or raw memory writes.
"""
import ctypes as C
import hashlib
import json
import os
import struct
import threading
import time
from pathlib import Path
from importlib.resources import files
import unrealsdk
from mods_base import ENGINE, get_pc

class MissionRuntime:
    def __init__(self):
        self.manifest = json.loads(files(__package__).joinpath("mission_build.json").read_text())
        self.world_address = None
        self.thread = threading.get_ident()
        self.k = C.WinDLL("kernel32", use_last_error=True)
        self.k.GetModuleHandleW.argtypes = [C.c_wchar_p]
        self.k.GetModuleHandleW.restype = C.c_void_p
        self.k.GetModuleFileNameW.argtypes = [C.c_void_p, C.c_wchar_p, C.c_uint32]
        self.k.GetModuleFileNameW.restype = C.c_uint32
        self.k.GetCurrentProcess.restype = C.c_void_p
        self.k.ReadProcessMemory.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p,
                                            C.c_size_t, C.POINTER(C.c_size_t)]
        self.k.ReadProcessMemory.restype = C.c_bool
        self.base = self.k.GetModuleHandleW(None)
        path = C.create_unicode_buffer(32768)
        length = self.k.GetModuleFileNameW(self.base, path, len(path))
        if not 0 < length < len(path):
            raise RuntimeError("Could not resolve the running executable")
        with Path(path.value).open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        if digest != self.manifest["sha256"]:
            raise RuntimeError("Unsupported executable; no snapshot taken")
        self.check_build()
        self.names = {}
        for item in json.loads(files(__package__).joinpath("mission_names.json").read_text()):
            token = unrealsdk.make_struct("/Script/CoreUObject.SToken", Name=item["name"])
            self.names[self.read(token._get_address() + 4, 8).hex()] = item
        self.status_names = {}
        for name in ("None", "locked", "available", "active", "completed", "failed"):
            token = unrealsdk.make_struct("/Script/CoreUObject.SToken", Name=name)
            self.status_names[self.read(token._get_address() + 4, 8).hex()] = name
        self.status_names[self.read(self.base + 0xcb80808, 8).hex()] = "accepted"

    def read(self, address, size):
        if not 0x10000 < address < 0x800000000000 or not 0 < size <= 16384:
            raise ValueError("Invalid bounded read")
        buffer = C.create_string_buffer(size)
        got = C.c_size_t()
        if not self.k.ReadProcessMemory(self.k.GetCurrentProcess(), address,
                                        buffer, size, C.byref(got)) or got.value != size:
            raise OSError("Unreadable runtime address")
        return buffer.raw

    def u64(self, address):
        return struct.unpack("<Q", self.read(address, 8))[0]

    def array(self, address, maximum):
        data, count, capacity = struct.unpack("<Qii", self.read(address, 16))
        if not 0 <= count <= capacity <= maximum or (count and not data):
            raise ValueError("Unexpected array bounds")
        return data, count

    def check_build(self):
        for rva, expected in self.manifest["fingerprints"].items():
            expected = bytes.fromhex(expected)
            if self.read(self.base + int(rva, 16), len(expected)) != expected:
                raise RuntimeError("Native code fingerprint mismatch: " + rva)

    def variant(self, address):
        """Raw fact variant. Tag 3 embeds FName at +4 (native 3a18c8)."""
        raw = self.read(address, 16)
        return {"tag": raw[0], "raw": raw.hex(),
                "known_status": self.status_names.get(raw[4:12].hex()) if raw[0] == 3 else None,
                "fname": raw[4:12].hex() if raw[0] == 3 else None}

    def fact(self, storage, offset):
        if not storage:
            return None
        fields = self.u64(storage + 8)
        value = self.u64(fields + offset) if fields else 0
        return self.variant(value + 0x38) if value else None

    def ensure_world(self):
        # Fail before enumerating old world objects or following shared-shard
        # pointers after host exit. This run is bound to the observed World_P.
        world = getattr(getattr(ENGINE, "GameViewport", None), "World", None)
        if world is None or world._path_name() != "/Game/Maps/WorldLevels/World_P.World_P":
            raise RuntimeError("Mission run stopped: gameplay world left or changing")
        pc = get_pc()
        if pc is None or getattr(pc, "Pawn", None) is None or getattr(pc, "PlayerState", None) is None:
            raise RuntimeError("Mission run stopped: no possessed gameplay controller")
        if not pc._path_name().startswith(world._path_name() + ":"):
            raise RuntimeError("Mission run stopped: controller belongs to another world")
        current_world = world._get_address()
        if self.world_address is not None and current_world != self.world_address:
            raise RuntimeError("Mission run stopped: world instance changed; explicit reload required")
        self.world_address = current_world

    def snapshot(self):
        if threading.get_ident() != self.thread:
            raise RuntimeError("Probe must run on its loading/game thread")
        self.check_build()
        self.ensure_world()
        instances = list(unrealsdk.find_all("OakGameInstance"))
        instances = [x for x in instances
                     if "Default__" not in x._path_name()
                     and self.u64(x._get_address()) == self.base + 0xb752920
                     and self.u64(x._get_address() + 0x518)]
        if len(instances) != 1:
            raise RuntimeError("Expected exactly one live OakGameInstance")
        gi = instances[0]._get_address()
        singletons = self.u64(gi + 0x518)
        shard = self.u64(singletons + 0x38)
        if self.u64(shard) != self.base + 0xb7dc120:
            raise RuntimeError("Unexpected shared shard")
        context = self.u64(shard + 0x180)
        interface = self.u64(context + 0xe0)
        if self.u64(interface) != self.base + 0xb975980:
            raise RuntimeError("Unexpected mission interface")
        data, count = self.array(interface + 0x60, 2000)
        from .mission_challenges import sparse_entries
        live_entries = sparse_entries(self, interface + 0x60, 32, 2000)
        rows = []
        unsupported = []
        for address in live_entries:
            entry = self.read(address, 32)
            record = struct.unpack_from("<Q", entry, 16)[0]
            if not record:
                continue
            if self.u64(record) != self.base + 0xb973820:
                unsupported.append({"token": entry[:12].hex(), "record": hex(record),
                                    "vtable_rva": hex(self.u64(record) - self.base)})
                continue
            definition = self.u64(record + 0xa0)
            storage = self.u64(record + 0xa8)
            exits, exit_count = self.array(definition + 0x70, 100)
            rows.append({"token": entry[:12].hex(), "source_identity": self.names.get(entry[4:12].hex()), "record": hex(record),
                         "definition": hex(definition), "storage": hex(storage),
                         "replication_type": self.read(definition + 0x538, 1)[0],
                         "generated": self.read(definition + 0x750, 1)[0],
                         "ownership": self.read(definition + 0x751, 1)[0],
                         "status_fact": self.fact(storage, 0x20),
                         "exit_fact": self.fact(storage, 0x68),
                         "exit_names": [self.read(exits + i * 0x60, 8).hex()
                                        for i in range(exit_count)]})
        tracked = []
        state = self.u64(interface + 0x188)
        if state:
            tokens, token_count = self.array(state + 0x160, 100)
            tracked = [self.read(tokens + i * 12, 12).hex() for i in range(token_count)]
        controllers = [{"path": pc._path_name(), "address": hex(pc._get_address())}
                       for pc in unrealsdk.find_all("OakPlayerController")
                       if "Default__" not in pc._path_name()]
        result = {"time": time.time(), "pid": os.getpid(), "base": hex(self.base),
                  "sha256": self.manifest["sha256"], "thread": self.thread,
                  "scope": "shared shard only; guest ownership is not established",
                  "controllers": controllers, "tracked": tracked, "missions": rows,
                  "unsupported_records": unsupported}
        return result
