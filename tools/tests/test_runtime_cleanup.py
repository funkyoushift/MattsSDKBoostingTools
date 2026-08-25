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
    ]
