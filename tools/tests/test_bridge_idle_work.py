"""Periodic bridge status must not do unused world scans or retry every frame."""
from __future__ import annotations

from test_bridge_perf_bounds import _load_bridge
from test_quick_menu_last_command import _load_backend_actions


def test_failed_snapshot_refresh_keeps_previous_data_and_waits_before_retry():
    bridge = _load_bridge()
    clock = [100.0]
    attempts = []
    bridge._now = lambda: clock[0]
    bridge._status_snapshot = {"ok": True, "players": [{"name": "Last good player"}]}

    def unavailable():
        attempts.append(clock[0])
        raise RuntimeError("transient SDK failure")

    bridge._status = unavailable
    bridge._refresh_status_snapshot()
    for frame in range(1, 29):
        clock[0] = 100.0 + frame / 60
        bridge._refresh_status_snapshot()
    assert attempts == [100.0]
    assert bridge._get_status_snapshot()["players"] == [{"name": "Last good player"}]
    clock[0] = 100.5
    bridge._status = lambda: {"ok": True, "players": [{"name": "Recovered"}]}
    bridge._refresh_status_snapshot()
    assert bridge._get_status_snapshot()["players"] == [{"name": "Recovered"}]


def test_bridge_requests_only_status_fields_it_publishes():
    bridge = _load_bridge()
    calls = []

    def status(*, include_extended=True):
        calls.append(include_extended)
        return {"players": [{"name": "Host"}]}

    bridge.backend_actions.get_status = status
    assert bridge._status()["players"] == [{"name": "Host"}]
    assert calls == [False]


def test_lean_backend_status_skips_camera_scans_and_bookmark_io(monkeypatch):
    backend = _load_backend_actions()
    monkeypatch.setattr(backend._cxp, "get_status_dict", lambda: {}, raising=False)
    monkeypatch.setattr(backend._ich, "get_status_dict", lambda: {}, raising=False)
    monkeypatch.setattr(backend._ich, "get_holds_status_dict", lambda: {}, raising=False)
    monkeypatch.setattr(backend, "_fog_status_dict", lambda: {})
    monkeypatch.setattr(backend, "_sdk_diagnostics", lambda: {})
    calls = []

    def record(name, value):
        def call():
            calls.append(name)
            return value
        return call

    monkeypatch.setattr(backend, "_debug_cam_status", record("camera scan", {"active": False}))
    monkeypatch.setattr(backend, "_list_location_bookmarks", record("bookmark read", []))
    monkeypatch.setattr(backend, "_list_vehicle_catalog", record("vehicle catalog", []))
    for _ in range(5):
        status = backend.get_status(include_extended=False)
        assert status["players"][0]["name"] == "Host"
        assert status["game_parameters"]["player_level_cap"] == 70
        assert "debug_cam" not in status
        assert "location_bookmarks" not in status
    assert calls == []

    # The default public helper keeps its original full response for callers.
    status = backend.get_status()
    assert status["debug_cam"] == {"active": False}
    assert status["location_bookmarks"] == []
    assert calls == ["bookmark read", "vehicle catalog", "camera scan"]
