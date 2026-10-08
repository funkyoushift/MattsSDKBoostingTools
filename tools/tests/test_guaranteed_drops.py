"""Exercise patch ownership, restoration, and fail-closed compatibility offline."""
import importlib.util
import sys
import types
import struct
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
package = types.ModuleType('guaranteed_drops_test');package.__path__=[str(ROOT/'mod_extracted/MattsSDKBoostingTools')]
sys.modules['guaranteed_drops_test']=package
SPEC = importlib.util.spec_from_file_location('guaranteed_drops_test.guaranteed_drops',ROOT/'mod_extracted/MattsSDKBoostingTools/guaranteed_drops.py')
drops = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(drops)


@pytest.mark.parametrize('name',['steam-25372571','epic-4845623'])
def test_native_memory_selects_exact_build_header(name):
    profile=drops.BUILDS[name];header=bytearray(0x1000)
    header[:2]=b'MZ';struct.pack_into('<I',header,0x3c,0x80);header[0x80:0x84]=b'PE\0\0'
    struct.pack_into('<H',header,0x84,0x8664);struct.pack_into('<I',header,0x88,profile['timestamp'])
    struct.pack_into('<I',header,0xd0,profile['image_size'])
    memory=drops.NativeMemory.__new__(drops.NativeMemory);memory.base=0x140000000;memory.read=lambda a,n:bytes(header)
    memory.validate();assert memory.build==name
    header[0x88]^=1
    with pytest.raises(RuntimeError,match='qualified'):memory.validate()


def test_epic_drop_rate_preserves_original_and_foreign_patch_guard():
    memory=Memory();memory.build='epic-4845623'
    override=drops.DropRateOverride(lambda:memory)
    assert override.set_enabled(True)['active'] and override.profile is drops.BUILDS['epic-4845623']['drop']
    assert override.set_enabled(False)['ok'] and bytes(memory.code)==drops.CONTEXT


class Memory:
    base = 0x140000000

    def __init__(self):
        self.code = bytearray(drops.CONTEXT)
        self.writes = []
        self.compatible = True
        self.fail = None

    def validate(self):
        if not self.compatible:
            raise RuntimeError("unsupported build")

    def read(self, address, size):
        start = address - self.base - drops.CONTEXT_RVA
        return bytes(self.code[start:start + size])

    def write(self, address, data):
        if self.fail == "before":
            raise RuntimeError("write failed")
        start = address - self.base - drops.CONTEXT_RVA
        self.code[start:start + len(data)] = data
        self.writes.append(data)
        if self.fail == "after":
            self.fail = None
            raise RuntimeError("flush failed")


def test_repeated_on_off_restores_exact_original():
    memory = Memory()
    override = drops.DropRateOverride(lambda: memory)
    assert not override.status()["active"]
    assert override.set_enabled(True)["active"]
    assert override.set_enabled(True)["active"]
    assert memory.writes == [drops.PATCHED]
    assert override.set_enabled(False)["ok"]
    assert not override.status()["owned"]
    assert bytes(memory.code) == drops.CONTEXT
    assert override.set_enabled(False)["ok"]
    assert memory.writes == [drops.PATCHED, drops.ORIGINAL]


@pytest.mark.parametrize("kind", ["build", "context", "foreign_patch"])
def test_mismatch_never_writes(kind):
    memory = Memory()
    if kind == "build":
        memory.compatible = False
    elif kind == "context":
        memory.code[-1] ^= 1
    else:
        memory.code[drops.PATCH_OFFSET:drops.PATCH_OFFSET + 4] = drops.PATCHED
    override = drops.DropRateOverride(lambda: memory)
    assert not override.set_enabled(True)["ok"]
    assert not override.status()["owned"]
    assert not memory.writes


def test_foreign_edit_after_enable_is_never_overwritten():
    memory = Memory()
    override = drops.DropRateOverride(lambda: memory)
    override.set_enabled(True)
    memory.code[drops.PATCH_OFFSET] = 0xCC
    assert override.status()["conflict"]
    assert not override.set_enabled(False)["ok"]
    assert memory.writes == [drops.PATCHED]
    assert override.status()["owned"]


@pytest.mark.parametrize("failure", ["before", "after"])
def test_failed_enable_rolls_back_when_original_or_owned_bytes_remain(failure):
    memory = Memory()
    memory.fail = failure
    override = drops.DropRateOverride(lambda: memory)
    result = override.set_enabled(True)
    assert not result["ok"]
    assert not result["owned"]
    assert not result["active"]
    assert bytes(memory.code) == drops.CONTEXT
    assert result["last_error"]


def test_status_and_off_do_not_load_native_apis():
    def unavailable():
        raise AssertionError("must stay lazy")
    override = drops.DropRateOverride(unavailable)
    assert not override.status()["active"]
    assert override.set_enabled(False)["ok"]


def test_owned_enable_cannot_hide_pending_page_restore_failure():
    memory = Memory()
    override = drops.DropRateOverride(lambda: memory)
    assert override.set_enabled(True)["ok"]
    def fail_restore():
        raise RuntimeError("page protection restore failed")
    memory.restore_protections = fail_restore
    result = override.set_enabled(True)
    assert not result["ok"] and result["owned"]
    assert "page protection" in result["last_error"]
    memory.restore_protections = lambda: None
    assert override.set_enabled(False)["ok"]


def test_native_header_validation_rejects_unqualified_build():
    import struct
    header = bytearray(0x1000)
    header[:2] = b"MZ"
    struct.pack_into("<I", header, 0x3C, 0x100)
    header[0x100:0x104] = b"PE\0\0"
    struct.pack_into("<H", header, 0x104, 0x8664)
    struct.pack_into("<I", header, 0x108, drops.PROFILE_TIMESTAMP)
    struct.pack_into("<I", header, 0x150, drops.PROFILE_IMAGE_SIZE)
    native = object.__new__(drops.NativeMemory)
    native.base = Memory.base
    native.read = lambda *_: bytes(header)
    native.validate()
    header[0x108] ^= 1
    with pytest.raises(RuntimeError, match="not been qualified"):
        native.validate()


@pytest.mark.parametrize("authority", [False, None])
def test_backend_requires_verified_host_before_enable(monkeypatch, authority):
    from tests.test_quick_menu_last_command import _load_backend_actions
    import types
    backend = _load_backend_actions()
    called = []
    monkeypatch.setattr(backend.guaranteed_drops, "override", types.SimpleNamespace(
        set_enabled=lambda value: called.append(value) or {"ok": True}, status=lambda: {"active": False},
    ))
    monkeypatch.setattr(backend, "get_pc", lambda: None if authority is None else types.SimpleNamespace(HasAuthority=lambda: authority))
    monkeypatch.setattr(backend, "_rarity_current_gamestate", lambda: object())
    assert not backend.drop_rate_action("drop_rate_on")["ok"]
    assert not called
    # Off must remain reachable after leaving the host world.
    assert backend.drop_rate_action("drop_rate_off")["ok"]
    assert called == [False]


def test_backend_host_dispatch_and_quick_menu_assignment(monkeypatch):
    from tests.test_quick_menu_last_command import _load_backend_actions
    import types
    backend = _load_backend_actions()
    called = []
    monkeypatch.setattr(backend.guaranteed_drops, "override", types.SimpleNamespace(
        set_enabled=lambda value: called.append(value) or {"ok": True, "message": "test"},
        status=lambda: {"active": False},
    ))
    monkeypatch.setattr(backend, "get_pc", lambda: types.SimpleNamespace(HasAuthority=lambda: True))
    monkeypatch.setattr(backend, "_rarity_current_gamestate", lambda: object())
    for action in ("drop_rate_on", "drop_rate_off"):
        assigned = backend.quick_menu_registry.assign_quick_menu_slot({"page": 0, "slot": 2, "action": action})
        assert assigned["ok"]
        result = backend.run_quick_menu_action(action, {})
        assert result["ok"]
    assert called == [True, False]


def test_http_dispatch_and_cached_status_keep_drop_rate():
    from test_bridge_perf_bounds import _load_bridge
    bridge = _load_bridge()
    called = []
    bridge.backend_actions.drop_rate_action = lambda action: called.append(action) or {"ok": True}
    for action in ("drop_rate_on", "drop_rate_off", "drop_rate_status"):
        assert bridge._handle_action(action, {})["ok"]
    assert called == ["drop_rate_on", "drop_rate_off", "drop_rate_status"]
    bridge.backend_actions.get_status = lambda **_kwargs: {"drop_rate": {"active": True, "owned": True}}
    bridge._refresh_status_snapshot(force=True)
    assert bridge._get_status_snapshot()["drop_rate"]["active"]


@pytest.mark.skipif(__import__("os").name != "nt", reason="Windows native API qualification")
def test_native_writer_roundtrip_in_isolated_scratch_page():
    import ctypes
    from ctypes import wintypes
    native = object.__new__(drops.NativeMemory)
    # Initialization configures APIs before refusing this non-game test process.
    with pytest.raises(RuntimeError, match="not loaded"):
        native.__init__()
    native.api.VirtualAlloc.argtypes = (wintypes.LPVOID, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD)
    native.api.VirtualAlloc.restype = wintypes.LPVOID
    native.api.VirtualFree.argtypes = (wintypes.LPVOID, ctypes.c_size_t, wintypes.DWORD)
    page = native.api.VirtualAlloc(None, 4096, 0x3000, 0x04)
    assert page
    try:
        # Use the same offset alignment as the actual game instruction.
        address = page + 2
        native.write(address, drops.ORIGINAL)
        assert native.read(address, 4) == drops.ORIGINAL
        native.write(address, drops.PATCHED)
        assert native.read(address, 4) == drops.PATCHED
        native.write(address, drops.ORIGINAL)
        assert native.read(address, 4) == drops.ORIGINAL
        old = wintypes.DWORD()
        assert native.api.VirtualProtect(page, 4096, 0x04, ctypes.byref(old))
        assert old.value == 0x04, "writer must restore scratch-page permissions"
    finally:
        native.api.VirtualFree(page, 0, 0x8000)
