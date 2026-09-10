"""The HTTP status endpoint must never perform live SDK status work."""
from __future__ import annotations

from test_bridge_perf_bounds import _load_bridge


def test_get_status_uses_cached_snapshot_not_backend():
    bridge = _load_bridge()
    bridge._status_snapshot = {
        "ok": True,
        "players": [{"index": 0, "name": "Cached Player"}],
        "queue": 99,
    }
    bridge.backend_actions.get_status = lambda: (_ for _ in ()).throw(
        AssertionError("HTTP thread called live backend status")
    )
    sent = []

    class Request:
        path = "/status"

        def _send(self, status, data):
            sent.append((status, data))

    bridge._Handler.do_GET(Request())

    assert sent[0][0] == 200
    assert sent[0][1]["players"][0]["name"] == "Cached Player"
    assert sent[0][1]["queue"] == 0


def test_http_snapshot_keeps_backend_game_parameters():
    bridge = _load_bridge()
    parameters = {"player_level_cap": 70, "vault_card_count": 5, "extracted_game_build": "25234898"}
    bridge.backend_actions.get_status = lambda: {"game_parameters": parameters}
    bridge._refresh_status_snapshot(force=True)
    bridge.backend_actions.get_status = lambda: (_ for _ in ()).throw(
        AssertionError("HTTP thread called live backend status")
    )
    assert bridge._get_status_snapshot()["game_parameters"] == parameters
    assert bridge._get_status_snapshot()["snapshot_ready"] is True


def test_pre_tick_status_includes_bundled_game_parameters():
    bridge = _load_bridge()
    bridge._status_snapshot = None
    snapshot = bridge._get_status_snapshot()
    assert snapshot["snapshot_ready"] is False
    assert snapshot["game_parameters"]["player_level_cap"] == 70
    assert snapshot["game_parameters"]["vault_card_count"] == 5
