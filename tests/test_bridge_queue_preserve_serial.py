"""Bridge queue policy: other commands must not cancel waiting Give_Serial."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"


def _load_bridge():
    for name in ("unrealsdk", "unrealsdk.unreal", "mods_base"):
        sys.modules.setdefault(name, types.ModuleType(name))
    mb = sys.modules["mods_base"]
    mb.hook = lambda *a, **k: (lambda f: f)

    pkg = types.ModuleType("MattsSDKBoostingTools")
    pkg.__path__ = [str(PKG)]
    sys.modules["MattsSDKBoostingTools"] = pkg

    ba = types.ModuleType("MattsSDKBoostingTools.backend_actions")
    ba.get_status = lambda: {"players": [], "selected_player": "", "serial_delivery": {}}
    ba._sdk_diagnostics = lambda: {}
    sys.modules["MattsSDKBoostingTools.backend_actions"] = ba

    spec = importlib.util.spec_from_file_location(
        "MattsSDKBoostingTools.external_bridge", PKG / "external_bridge.py"
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules["MattsSDKBoostingTools.external_bridge"] = bridge
    spec.loader.exec_module(bridge)
    return bridge


def test_non_serial_command_preserves_pending_give_serial():
    bridge = _load_bridge()
    bridge._queue.clear()
    bridge._abandoned_rids.clear()
    bridge._queue.append({"id": "serial1", "action": "give_serial_selected", "payload": {}})
    bridge._queue.append({"id": "spawn1", "action": "dev_spawner_spawnai", "payload": {}})

    dropped = bridge._prepare_queue_for_enqueue_locked("max_currency")

    assert dropped == 1
    assert len(bridge._queue) == 1
    assert bridge._queue[0]["id"] == "serial1"
    assert "spawn1" in bridge._abandoned_rids
    assert "serial1" not in bridge._abandoned_rids


def test_new_give_serial_clears_pending_serial_and_spawn():
    bridge = _load_bridge()
    bridge._queue.clear()
    bridge._abandoned_rids.clear()
    bridge._queue.append({"id": "serial1", "action": "give_serial_all", "payload": {}})
    bridge._queue.append({"id": "spawn1", "action": "dev_spawner_spawnai", "payload": {}})

    dropped = bridge._prepare_queue_for_enqueue_locked("give_serial_selected")

    assert dropped == 2
    assert len(bridge._queue) == 0
    assert "serial1" in bridge._abandoned_rids
    assert "spawn1" in bridge._abandoned_rids


def test_preserving_actions_leave_queue_alone():
    bridge = _load_bridge()
    bridge._queue.clear()
    bridge._abandoned_rids.clear()
    bridge._queue.append({"id": "spawn1", "action": "dev_spawner_spawnai", "payload": {}})

    dropped = bridge._prepare_queue_for_enqueue_locked("auto_inventory_sizes")

    assert dropped == 0
    assert len(bridge._queue) == 1
    assert bridge._queue[0]["id"] == "spawn1"
