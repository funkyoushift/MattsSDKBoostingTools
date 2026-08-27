"""Bounds and lifecycle coverage for the in-game external bridge."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"


def _load_bridge():
    for name in ("unrealsdk", "unrealsdk.unreal", "mods_base"):
        sys.modules.setdefault(name, types.ModuleType(name))
    mods_base = sys.modules["mods_base"]
    mods_base.hook = lambda *args, **kwargs: (lambda func: func)

    package = types.ModuleType("MattsSDKBoostingTools")
    package.__path__ = [str(PKG)]
    sys.modules["MattsSDKBoostingTools"] = package

    backend = types.ModuleType("MattsSDKBoostingTools.backend_actions")
    backend.get_status = lambda: {"players": [], "serial_delivery": {}, "diagnostics": {}}
    sys.modules["MattsSDKBoostingTools.backend_actions"] = backend
    quick_menu_registry = types.ModuleType("MattsSDKBoostingTools.quick_menu_registry")
    quick_menu_registry.ASSIGNABLE_ACTIONS = frozenset()
    sys.modules["MattsSDKBoostingTools.quick_menu_registry"] = quick_menu_registry

    sys.modules.pop("MattsSDKBoostingTools.external_bridge", None)
    spec = importlib.util.spec_from_file_location(
        "MattsSDKBoostingTools.external_bridge", PKG / "external_bridge.py"
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules["MattsSDKBoostingTools.external_bridge"] = bridge
    spec.loader.exec_module(bridge)
    try:
        bridge.mobile_lan.reset_state()
        bridge.mobile_lan.set_rebind_callback(None)
    except Exception:
        pass
    return bridge


def test_result_ttl_and_max_size_are_enforced():
    bridge = _load_bridge()
    bridge._results.clear()

    for index in range(bridge.MAX_RESULTS + 10):
        assert bridge._store_result_locked(
            f"rid-{index}", {"ok": True, "index": index}, now=100.0
        )
    assert len(bridge._results) == bridge.MAX_RESULTS
    assert "rid-0" not in bridge._results

    bridge._results["expired"] = {
        "result": {"ok": True},
        "completed_at": 100.0 - bridge.RESULT_TTL_SECONDS - 1.0,
    }
    bridge._prune_results_locked(now=100.0)
    assert "expired" not in bridge._results


def test_abandoned_result_is_not_retained():
    bridge = _load_bridge()
    bridge._results.clear()
    bridge._abandoned_rids.clear()
    bridge._abandoned_rids.add("gone")

    assert bridge._store_result_locked("gone", {"ok": True}, now=100.0) is False
    assert "gone" not in bridge._results


def test_completed_abandoned_action_discards_its_result():
    bridge = _load_bridge()
    calls = []
    bridge.backend_actions.uvh_boost_tick = lambda: None
    bridge.backend_actions.complete_challenges_tick = lambda: None
    bridge.backend_actions.hoard_tick = lambda: None
    bridge._handle_action = lambda action, payload: calls.append(action) or {"ok": True}
    bridge._queue.append({"id": "gone", "action": "test_action", "payload": {}})
    bridge._abandoned_rids.add("gone")

    bridge._process_pending_actions()

    assert calls == ["test_action"]
    assert "gone" not in bridge._results


def test_stale_tick_generation_does_not_process_queue():
    bridge = _load_bridge()
    bridge._generation = 5
    bridge._queue.append({"id": "stale", "action": "test_action", "payload": {}})

    bridge._process_pending_actions(_callback_generation=4)

    assert bridge._queue[0]["id"] == "stale"
    assert "stale" not in bridge._results


def test_stop_bridge_clears_runtime_state():
    bridge = _load_bridge()
    bridge._started = True
    bridge._tick_registered = True
    bridge._queue.append({"id": "queued"})
    bridge._results["done"] = {"result": {"ok": True}, "completed_at": bridge._now()}
    bridge._abandoned_rids.add("old")
    bridge._waiters["waiting"] = bridge.threading.Event()
    bridge._executing_rid = "running"
    bridge._status_snapshot = {"ok": True}

    bridge.stop_bridge()

    assert bridge._started is False
    assert bridge._tick_registered is False
    assert bridge._server is None
    assert bridge._thread is None
    assert bridge._executing_rid is None
    assert bridge._status_snapshot is None
    assert not bridge._queue
    assert not bridge._results
    assert not bridge._abandoned_rids
    assert not bridge._waiters


def test_start_bridge_can_read_started_flag():
    bridge = _load_bridge()
    bridge._register_tick_hook = lambda: None
    bridge._refresh_status_snapshot = lambda **k: None
    bridge._start_http_listen = lambda: None
    bridge._unregister_tick_hook = lambda: None
    bridge._stop_http_listen = lambda: None
    bridge.start_bridge()
    bridge._started = True
    bridge.start_bridge()


def test_bridge_request_limits_exist():
    bridge = _load_bridge()

    assert bridge.MAX_QUEUE_DEPTH == 64
    assert bridge.MAX_RESULTS == 128
    assert bridge.RESULT_TTL_SECONDS == 60.0
    assert bridge.MAX_BODY_BYTES == 2 * 1024 * 1024
    assert bridge.MAX_CLIENT_TIMEOUT_SECONDS == 30.0
