"""Current host delivery requires identity; guest/card builds remain blocked.

Reads the executable as data only; never loads game code or opens a process.
"""
import hashlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pefile
import pytest


ROOT = Path(__file__).parents[2]
SDK = ROOT / "mod_extracted/MattsSDKBoostingTools"
TARGET = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Borderlands 4\OakGame\Binaries\Win64\Borderlands4.exe")
TARGET_HASH = "ba75f7c2874b16efb5536a5c0cc28918a03efd3e55d790d2e4db57de0c3a353a"
BUILD = "steam-26007962"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SDK / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_installed_new_steam_missing_identity_rejected_before_native_binding(monkeypatch):
    if not TARGET.is_file():
        pytest.skip("New Steam executable not installed")
    with TARGET.open("rb") as stream:
        if hashlib.file_digest(stream, "sha256").hexdigest() != TARGET_HASH:
            pytest.skip("Installed executable is another build")
    native = load("direct_inventory")
    image = pefile.PE(str(TARGET), fast_load=True)
    try:
        # Exercise the actual constructor through its profile gate. Binding is
        # a failure even if no native function is subsequently called.
        kernel = SimpleNamespace(GetModuleHandleW=lambda _: 0x140000000,
                                 VirtualQuery=lambda *args: 1,
                                 GetModuleFileNameW=lambda *args: 0)
        monkeypatch.setattr(native.C, "WinDLL", lambda *args, **kwargs: kernel, raising=False)
        monkeypatch.setattr(native.NativeInventory, "read",
                            lambda self, ptr, size: image.get_data(ptr - self.base, size))
        def forbidden(*args):
            pytest.fail("Unsupported executable reached native function binding")
        monkeypatch.setattr(native.C, "CFUNCTYPE", forbidden)
        with pytest.raises(RuntimeError, match="Cannot identify game executable; no items sent"):
            native.NativeInventory()
    finally:
        image.close()


def test_new_steam_guest_rejected_before_memory_access_or_binding(monkeypatch):
    guest = load("guest_inventory")
    def forbidden(*args):
        pytest.fail("Unsupported guest profile accessed memory or bound native code")
    monkeypatch.setattr(guest.C, "CFUNCTYPE", forbidden)
    with pytest.raises(RuntimeError, match="not supported"):
        guest.GuestInventory(SimpleNamespace(profile=BUILD, read=forbidden))


def test_new_steam_card_mapping_stays_blocked():
    cards = load("native_card_builds")
    for call in (lambda: cards.require_card_profile(BUILD),
                 lambda: cards.card_rva(BUILD, 0x56D3CCA),
                 lambda: cards.card_gates(BUILD, ())):
        with pytest.raises(RuntimeError, match="not supported"):
            call()
