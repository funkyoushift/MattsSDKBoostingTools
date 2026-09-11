"""Slow DNS cannot hold the bridge/game tick or multiply discovery threads."""
from __future__ import annotations

import ast
import threading
import types
from typing import Any

import pytest

from test_mobile_lan import PKG, _load_lan


def test_disabled_status_does_not_discover_addresses(tmp_path, monkeypatch):
    lan = _load_lan(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(lan, "_discover_lan_ipv4", lambda: calls.append(True) or [])
    for _ in range(10):
        assert lan.status_dict()["hosts"] == []
    assert calls == []
    assert lan._hosts_worker is None


def test_slow_discovery_does_not_block_status_or_pairing_and_has_one_worker(tmp_path, monkeypatch):
    lan = _load_lan(tmp_path, monkeypatch)
    started = threading.Event()
    release = threading.Event()
    returned = threading.Event()
    calls = []

    def discover():
        calls.append(threading.current_thread())
        started.set()
        assert release.wait(3)
        return ["192.168.1.20"]

    monkeypatch.setattr(lan, "_discover_lan_ipv4", discover)
    lan.set_lan_enabled(True, persist_now=False)
    worker = lan._hosts_worker
    try:
        assert started.wait(1)

        def read_status():
            for _ in range(10):
                assert lan.status_dict()["hosts"] == []
                assert lan.pairing_payload()["hosts"] == []
            returned.set()

        caller = threading.Thread(target=read_status, daemon=True)
        caller.start()
        assert returned.wait(1), "status waited for the blocked OS resolver"
        caller.join(1)
        assert calls == [worker]
        assert worker is not threading.current_thread()
    finally:
        release.set()
        worker.join(1)
    assert lan.status_dict()["hosts"] == ["192.168.1.20"]
    # A caller cannot mutate the cached address list.
    lan.list_lan_ipv4().clear()
    assert lan.pairing_payload()["hosts"] == ["192.168.1.20"]


def test_disable_enable_does_not_duplicate_stalled_worker_or_publish_stale_result(tmp_path, monkeypatch):
    lan = _load_lan(tmp_path, monkeypatch)
    started = threading.Event()
    release = threading.Event()

    def discover():
        started.set()
        assert release.wait(3)
        return ["192.168.1.20"]

    monkeypatch.setattr(lan, "_discover_lan_ipv4", discover)
    lan.set_lan_enabled(True, persist_now=False)
    worker = lan._hosts_worker
    try:
        assert started.wait(1)
        for _ in range(5):
            lan.set_lan_enabled(False, persist_now=False)
            lan.set_lan_enabled(True, persist_now=False)
            assert lan.status_dict()["hosts"] == []
            assert lan._hosts_worker is worker
    finally:
        release.set()
        worker.join(1)
    assert lan._hosts_cache == []
    assert lan._hosts_worker is None
    monkeypatch.setattr(lan, "_discover_lan_ipv4", lambda: ["10.0.0.20"])
    lan.list_lan_ipv4()
    replacement = lan._hosts_worker
    if replacement is not None:
        replacement.join(1)
    assert lan.list_lan_ipv4() == ["10.0.0.20"]


@pytest.mark.parametrize("fails", [False, True])
def test_empty_or_failed_discovery_waits_until_refresh_deadline(tmp_path, monkeypatch, fails):
    lan = _load_lan(tmp_path, monkeypatch)
    calls = []
    clock = [100.0]
    monkeypatch.setattr(lan.time, "monotonic", lambda: clock[0])
    def discover():
        calls.append(True)
        if fails:
            raise OSError("adapter unavailable")
        return []

    monkeypatch.setattr(lan, "_discover_lan_ipv4", discover)
    lan.set_lan_enabled(True, persist_now=False)
    worker = lan._hosts_worker
    if worker is not None:
        worker.join(1)
    for _ in range(10):
        assert lan.status_dict()["hosts"] == []
    assert len(calls) == 1
    clock[0] += lan._HOSTS_REFRESH_SECONDS
    lan.list_lan_ipv4()
    worker = lan._hosts_worker
    if worker is not None:
        worker.join(1)
    assert len(calls) == 2


def test_pairing_without_lan_enabled_starts_background_discovery(tmp_path, monkeypatch):
    lan = _load_lan(tmp_path, monkeypatch)
    calls = []
    monkeypatch.setattr(lan, "_discover_lan_ipv4", lambda: calls.append(threading.current_thread()) or ["10.0.0.5"])
    nonce = lan.arm_enroll()
    worker = lan._hosts_worker
    if worker is not None:
        worker.join(1)
    assert lan.lan_enabled() is False
    assert lan.pairing_payload()["hosts"] == ["10.0.0.5"]
    assert lan.pairing_payload()["n"] == nonce
    assert len(calls) == 1
    assert calls[0] is not threading.current_thread()


def test_pairing_tick_refreshes_qr_once_after_addresses_arrive():
    # Run the real UI tick against a fake widget surface; no Unreal runtime needed.
    tree = ast.parse((PKG / "mobile_pairing.py").read_text(encoding="utf-8"))
    tick = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "tick")
    clock = [100.0]
    hosts = []
    rebuilt = []
    state = types.SimpleNamespace(is_open=True, last_input_refresh=0.0, hosts=(),
                                  key_escape=False, ui_dirty=False)

    def rebuild():
        rebuilt.append(threading.current_thread())
        state.hosts = tuple(hosts)
        state.ui_dirty = False

    namespace = {
        "Any": Any, "STATE": state, "time": types.SimpleNamespace(monotonic=lambda: clock[0]),
        "mobile_lan": types.SimpleNamespace(list_lan_ipv4=lambda: list(hosts)),
        "get_pc": lambda: None, "_key_down": lambda *_args: False,
        "capture_input": lambda: setattr(state, "last_input_refresh", clock[0]),
        "poll_buttons": lambda: None, "rebuild_ui": rebuild,
        "_log": lambda message: (_ for _ in ()).throw(AssertionError(message)),
    }
    exec(compile(ast.Module(body=[tick], type_ignores=[]), "mobile_pairing.py", "exec"), namespace)
    namespace["tick"]()
    assert rebuilt == []
    hosts.append("192.168.1.20")
    clock[0] += 0.5
    namespace["tick"]()
    assert rebuilt == [threading.current_thread()]
    clock[0] += 0.5
    namespace["tick"]()
    assert len(rebuilt) == 1
