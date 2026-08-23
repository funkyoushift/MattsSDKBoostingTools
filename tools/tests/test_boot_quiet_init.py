"""MSBT __init__ must not import hook modules at boot."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INIT = ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "__init__.py"


def test_init_does_not_import_hook_modules_at_module_level():
    source = INIT.read_text(encoding="utf-8")
    top = "\n".join(line for line in source.splitlines() if line and not line.startswith((" ", "\t")))
    forbidden = (
        "from .instant_click_holds import",
        "from .movement_adjustments import",
        "from .extreme_combat_xp import",
        "from .runtime_cleanup import",
        "from .quick_menu import",
        "from .backend_actions import",
        "from .serial_rewards import",
        "from .golden_chest_keybinds import",
        "from .blimgui_panel import",
        "start_quick_menu()",
        "start_auto_inventory_worker()",
        "start_bridge()",
        "@command",
    )
    for needle in forbidden:
        assert needle not in top, f"boot import is not quiet: {needle}"


def test_bridge_does_not_import_backend_at_module_level():
    source = (
        ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "external_bridge.py"
    ).read_text(encoding="utf-8")
    assert "from . import backend_actions, perf_profile" not in source
    assert "class _BackendProxy" in source
    assert "def ensure_gameplay_modules" in source
    watch = (ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "travel_watch.py").read_text(encoding="utf-8")
    assert "Type.PRE" in watch
    assert "from .hook_gate import disable_join_hooks" in watch
