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
