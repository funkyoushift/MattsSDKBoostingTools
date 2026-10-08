"""Travel cleanup releases UObject-adjacent caches without needing unrealsdk."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"


def _install_stubs():
    unrealsdk = types.ModuleType("unrealsdk")
    unrealsdk.logging = types.SimpleNamespace(warning=lambda *_a, **_k: None)
    hooks = types.ModuleType("unrealsdk.hooks")
    hooks.Type = types.SimpleNamespace(POST="POST", PRE="PRE")
    unrealsdk.hooks = hooks
    sys.modules["unrealsdk"] = unrealsdk
    sys.modules["unrealsdk.hooks"] = hooks

    mods_base = types.ModuleType("mods_base")
    mods_base.hook = lambda *args, **kwargs: (lambda func: func)
    sys.modules["mods_base"] = mods_base


def test_clear_travel_caches_calls_known_cleaners():
    _install_stubs()
    package = types.ModuleType("MattsSDKBoostingTools")
    package.__path__ = [str(PKG)]
    package.__name__ = "MattsSDKBoostingTools"
    sys.modules["MattsSDKBoostingTools"] = package

    called: list[str] = []

    def _mod(name: str, attrs: dict):
        module = types.ModuleType(f"MattsSDKBoostingTools.{name}")
        for key, value in attrs.items():
            setattr(module, key, value)
        sys.modules[f"MattsSDKBoostingTools.{name}"] = module
        return module

    _mod("backend_actions", {"clear_uobject_caches": lambda: called.append("backend")})
    _mod("spawn_helpers", {"clear_tracked": lambda: called.append("spawns")})
    _mod("hoard_runner", {"clear_travel_state": lambda: called.append("hoard")})
    _mod("streamer_chaos", {"clear_runtime_state": lambda: called.append("streamer")})
    _mod("golden_chest_keybinds", {"clear_pending_closes": lambda: called.append("chest")})
    _mod("serial_rewards", {"clear_delivery_state": lambda: called.append("serial")})
    _mod(
        "movement_adjustments",
        {"_clear_infinite_jump_runtime_caches": lambda: called.append("movement")},
    )
    _mod("instant_click_holds", {"clear_travel_backups": lambda: called.append("holds")})
    _mod("no_fog_of_war", {"clear_travel_backups": lambda: called.append("fog")})
    _mod("third_person_camera", {"clear_travel_backups": lambda: called.append("tpc")})
    _mod("guaranteed_drops", {"clear_runtime_state": lambda: called.append("drops")})

    sys.modules.pop("MattsSDKBoostingTools.runtime_cleanup", None)
    spec = importlib.util.spec_from_file_location(
        "MattsSDKBoostingTools.runtime_cleanup", PKG / "runtime_cleanup.py"
    )
    cleanup = importlib.util.module_from_spec(spec)
    cleanup.__package__ = "MattsSDKBoostingTools"
    sys.modules["MattsSDKBoostingTools.runtime_cleanup"] = cleanup
    spec.loader.exec_module(cleanup)

    cleanup.clear_travel_caches()

    assert called == [
        "backend",
        "spawns",
        "hoard",
        "streamer",
        "chest",
        "serial",
        "movement",
        "holds",
        "fog",
        "tpc",
        "drops",
    ]


def test_drop_rate_travel_hooks_restore_without_world_or_join_gate(monkeypatch):
    _install_stubs()
    package = types.ModuleType("_drop_cleanup_test")
    package.__path__ = [str(PKG)]
    monkeypatch.setitem(sys.modules, package.__name__, package)
    registrations = []
    def register(target, kind, **options):
        def decorate(callback):
            registrations.append((target, kind, options, callback))
            return callback
        return decorate
    monkeypatch.setattr(sys.modules["mods_base"], "hook", register)
    for name, attrs in {
        "hook_gate": {"disable_join_hooks": lambda: None,
                      "request_arm_when_pawn_ready": lambda *_: None,
                      "try_arm_from_controller": lambda *_: None},
        "travel_gate": {"mark_menu": lambda: None, "mark_travel": lambda: None},
    }.items():
        mod = types.ModuleType(package.__name__ + "." + name)
        mod.__dict__.update(attrs)
        monkeypatch.setitem(sys.modules, mod.__name__, mod)
    spec = importlib.util.spec_from_file_location(package.__name__ + ".guaranteed_drops", PKG / "guaranteed_drops.py")
    native = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, native)
    spec.loader.exec_module(native)
    class Memory:
        base = 0
        def __init__(self): self.code = bytearray(native.CONTEXT)
        def validate(self): pass
        def read(self, address, size):
            offset = address - native.CONTEXT_RVA
            return bytes(self.code[offset:offset+size])
        def write(self, address, value):
            offset = address - native.CONTEXT_RVA
            self.code[offset:offset+len(value)] = value
    memory = Memory()
    native.override = native.DropRateOverride(lambda: memory)
    spec = importlib.util.spec_from_file_location(package.__name__ + ".runtime_cleanup", PKG / "runtime_cleanup.py")
    cleanup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cleanup)
    handlers = [row for row in registrations if row[2]["hook_identifier"].startswith("msbt_drop_rate_travel_")]
    assert {row[0] for row in handlers} == {"Engine.PlayerController:ClientTravel", "OakGame.OakPlayerController:ClientTravel"}
    for _, kind, options, callback in handlers:
        assert kind == "PRE" and options["immediately_enable"] is True
        assert native.override.set_enabled(True)["ok"]
        callback(None, None, None)
        assert not native.override.status()["active"]
        assert bytes(memory.code) == native.CONTEXT
