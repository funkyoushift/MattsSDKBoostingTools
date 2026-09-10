"""A clean release must import its backend without unpublished research modules."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_backend_and_bridge_import_without_experimental_modules():
    # Run fresh to avoid the many runtime stubs cached by unrelated SDK tests.
    script = r'''
import builtins
import importlib
import pathlib
import sys
from tests.test_quick_menu_last_command import _load_backend_actions

sdk = pathlib.Path.cwd().parent / "mod_extracted" / "MattsSDKBoostingTools"
for name in ("fod_guest_grid", "spawn_tools"):
    assert not (sdk / (name + ".py")).exists(), name

original_import = builtins.__import__
def reject_research(name, globals=None, locals=None, fromlist=(), level=0):
    parts = set(name.split(".")) | set(fromlist or ())
    assert not parts.intersection({"fod_guest_grid", "spawn_tools"}), name
    return original_import(name, globals, locals, fromlist, level)
builtins.__import__ = reject_research

backend = _load_backend_actions()
bridge = importlib.import_module("MattsSDKBoostingTools.external_bridge")
registry = importlib.import_module("MattsSDKBoostingTools.quick_menu_registry")
assert callable(backend.run_quick_menu_action)
assert bridge._safe_status_stub()["game_parameters"]["player_level_cap"] == 70
for name in ("fod_guest_grid", "spawn_tools"):
    assert "MattsSDKBoostingTools." + name not in sys.modules
assert not hasattr(backend, "guest_grid_try")
assert not hasattr(backend, "guest_grid_dump")
assert "guest_grid_try" not in registry.ASSIGNABLE_ACTIONS
'''
    result = subprocess.run([sys.executable, "-c", script], cwd=ROOT / "tools",
                            text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
