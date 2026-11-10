"""LAN pairing auth, persistence, and QR encoder. Does not bind 0.0.0.0."""
from __future__ import annotations

import importlib.util
import io
import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"


def _load_module(name: str, filename: str):
    package = sys.modules.get("MattsSDKBoostingTools")
    if package is None:
        package = types.ModuleType("MattsSDKBoostingTools")
        package.__path__ = [str(PKG)]
        sys.modules["MattsSDKBoostingTools"] = package
    full = f"MattsSDKBoostingTools.{name}"
    sys.modules.pop(full, None)
    spec = importlib.util.spec_from_file_location(full, PKG / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[full] = module
    spec.loader.exec_module(module)
    return module


def _load_lan(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    lan = _load_module("mobile_lan", "mobile_lan.py")
    lan.reset_state()
    lan.set_rebind_callback(None)
    monkeypatch.setattr(lan, "_discover_lan_ipv4", lambda: [])
    return lan


def test_loopback_allowed_without_token(tmp_path, monkeypatch):
    lan = _load_lan(tmp_path, monkeypatch)
    assert lan.is_allowed("127.0.0.1", "") is True
    assert lan.is_allowed("::1", "") is True
    assert lan.bind_host() == "127.0.0.1"


def test_unknown_lan_ip_denied(tmp_path, monkeypatch):
    lan = _load_lan(tmp_path, monkeypatch)
    assert lan.is_allowed("192.168.1.50", "") is False
    assert lan.is_allowed("192.168.1.50", "deadbeef") is False


def test_enroll_then_allow_and_revoke(tmp_path, monkeypatch):
    lan = _load_lan(tmp_path, monkeypatch)
    nonce = lan.arm_enroll()
    result = lan.enroll(nonce, ip="192.168.1.50", token="tok-phone-1", name="Pixel")
    assert result["ok"] is True
    assert lan.lan_enabled() is True
    assert lan.bind_host() == "0.0.0.0"
    assert lan.is_allowed("192.168.1.50", "") is False
    assert lan.is_allowed("10.0.0.9", "tok-phone-1") is True
    assert lan.revoke_phone("tok-phone-1") is True
    assert lan.is_allowed("192.168.1.50", "tok-phone-1") is False


def test_enroll_rejected_when_overlay_closed(tmp_path, monkeypatch):
    lan = _load_lan(tmp_path, monkeypatch)
    result = lan.enroll("ABCD", ip="192.168.1.50", token="tok", name="Phone")
    assert result["ok"] is False


def test_persist_survives_reload(tmp_path, monkeypatch):
    lan = _load_lan(tmp_path, monkeypatch)
    nonce = lan.arm_enroll()
    lan.enroll(nonce, ip="192.168.1.77", token="persist-token", name="Keep")
    lan.disarm_enroll()
    path = lan.persist_path()
    assert path.is_file()
    lan.reset_state()
    assert lan.lan_enabled() is False
    lan.load()
    assert lan.lan_enabled() is True
    assert lan.is_allowed("10.9.9.9", "persist-token") is True


def test_bind_host_string_only_never_opens_socket(tmp_path, monkeypatch):
    lan = _load_lan(tmp_path, monkeypatch)
    lan.set_lan_enabled(True, persist_now=False)
    assert lan.bind_host() == "0.0.0.0"
    lan.set_lan_enabled(False, persist_now=False)
    assert lan.bind_host() == "127.0.0.1"


def _headers(data=None):
    store = {str(k).lower(): v for k, v in (data or {}).items()}

    class Headers:
        def get(self, name, default=""):
            return store.get(str(name).lower(), default)

    return Headers()


def _load_bridge(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    for name in ("unrealsdk", "unrealsdk.unreal", "mods_base"):
        sys.modules.setdefault(name, types.ModuleType(name))
    mods_base = sys.modules["mods_base"]
    mods_base.hook = lambda *args, **kwargs: (lambda func: func)
    mods_base.ENGINE = None
    package = types.ModuleType("MattsSDKBoostingTools")
    package.__path__ = [str(PKG)]
    sys.modules["MattsSDKBoostingTools"] = package
    backend = types.ModuleType("MattsSDKBoostingTools.backend_actions")
    backend.get_status = lambda **_kwargs: {"players": [], "serial_delivery": {}, "diagnostics": {}}
    sys.modules["MattsSDKBoostingTools.backend_actions"] = backend
    registry = types.ModuleType("MattsSDKBoostingTools.quick_menu_registry")
    registry.ASSIGNABLE_ACTIONS = frozenset()
    sys.modules["MattsSDKBoostingTools.quick_menu_registry"] = registry
    sys.modules.pop("MattsSDKBoostingTools.mobile_lan", None)
    sys.modules.pop("MattsSDKBoostingTools.external_bridge", None)
    lan = _load_module("mobile_lan", "mobile_lan.py")
    lan.reset_state()
    lan.set_rebind_callback(None)
    monkeypatch.setattr(lan, "_discover_lan_ipv4", lambda: [])
    spec = importlib.util.spec_from_file_location(
        "MattsSDKBoostingTools.external_bridge", PKG / "external_bridge.py"
    )
    bridge = importlib.util.module_from_spec(spec)
    sys.modules["MattsSDKBoostingTools.external_bridge"] = bridge
    spec.loader.exec_module(bridge)
    bridge.mobile_lan.reset_state()
    bridge.mobile_lan.set_rebind_callback(None)
    return bridge


def _unload_bridge_stubs() -> None:
    sys.modules.pop("MattsSDKBoostingTools.quick_menu_registry", None)
    sys.modules.pop("MattsSDKBoostingTools.external_bridge", None)


@pytest.fixture
def http_bridge(tmp_path, monkeypatch):
    bridge = _load_bridge(tmp_path, monkeypatch)
    try:
        yield bridge
    finally:
        _unload_bridge_stubs()


def test_http_loopback_status_allowed(http_bridge):
    bridge = http_bridge
    bridge._status_snapshot = {"ok": True, "players": [], "queue": 0}
    sent = []

    class Request:
        path = "/status"
        client_address = ("127.0.0.1", 9)
        headers = _headers()

        def _send(self, status, data):
            sent.append((status, data))

    bridge._Handler.do_GET(Request())
    assert sent[0][0] == 200


def test_http_unknown_lan_status_denied(http_bridge):
    bridge = http_bridge
    sent = []

    class Request:
        path = "/status"
        client_address = ("192.168.0.44", 9)
        headers = _headers()

        def _send(self, status, data):
            sent.append((status, data))

    bridge._Handler.do_GET(Request())
    assert sent[0][0] == 401


def test_http_layout_hidden_on_lan(http_bridge):
    bridge = http_bridge
    sent = []

    class Request:
        path = "/layout"
        client_address = ("192.168.0.44", 9)
        headers = _headers({"X-MSBT-Device": "tok"})

        def _send(self, status, data):
            sent.append((status, data))

    bridge._Handler.do_GET(Request())
    assert sent[0][0] == 404


def test_http_enroll_then_status_with_token(http_bridge):
    bridge = http_bridge
    nonce = bridge.mobile_lan.arm_enroll()
    body = json.dumps({"nonce": nonce, "device": "apk-token", "name": "Phone"}).encode("utf-8")
    sent = []

    class Enroll:
        path = "/mobile/enroll"
        client_address = ("192.168.0.44", 9)
        headers = _headers({"Content-Length": str(len(body))})
        rfile = io.BytesIO(body)
        _handle_enroll = bridge._Handler._handle_enroll
        _read_json_body = bridge._Handler._read_json_body

        def _send(self, status, data):
            sent.append((status, data))

    bridge._Handler.do_POST(Enroll())
    assert sent[0][0] == 200
    assert sent[0][1]["ok"] is True
    sent.clear()
    bridge._status_snapshot = {"ok": True, "players": [{"index": 0, "name": "Matt"}]}

    class Status:
        path = "/status"
        client_address = ("10.1.1.8", 9)
        headers = _headers({"X-MSBT-Device": "apk-token"})

        def _send(self, status, data):
            sent.append((status, data))

    bridge._Handler.do_GET(Status())
    assert sent[0][0] == 200


def test_http_ping_unauthenticated_on_lan(http_bridge):
    bridge = http_bridge
    sent = []

    class Request:
        path = "/mobile/ping"
        client_address = ("192.168.0.44", 9)
        headers = _headers()

        def _send(self, status, data):
            sent.append((status, data))

    bridge._Handler.do_GET(Request())
    assert sent[0][0] == 200
    assert sent[0][1]["direct"] is True


def test_qr_finder_patterns():
    qr = _load_module("qr_lite", "qr_lite.py")
    matrix = qr.encode("MSBT")
    size = len(matrix)
    assert size == len(matrix[0])
    assert size % 2 == 1
    assert matrix[0][0] == 1
    assert matrix[0][6] == 1
    assert matrix[6][0] == 1
    assert matrix[6][6] == 1
    assert matrix[1][1] == 0
    compact = qr.encode('{"v":2,"name":"MSBT","hosts":["10.0.0.1"],"port":49774,"n":"ABCD1234"}')
    assert len(compact) >= 21
    # ECC-M mask 0 format string is the masked BCH value 0x5412, stored MSB-first at (8,0).
    assert qr._bch_format(0) == 0x5412
    matrix = [[0] * 21 for _ in range(21)]
    qr._draw_format(matrix, 0)
    assert matrix[8][0] == ((0x5412 >> 14) & 1)


def test_pairing_overlay_stays_isolated_from_bridge():
    pairing = (PKG / "mobile_pairing.py").read_text(encoding="utf-8")
    bridge = (PKG / "external_bridge.py").read_text(encoding="utf-8")
    assert "from .external_bridge" not in pairing
    assert "from . import external_bridge" not in pairing
    assert "blimgui" not in pairing
    assert "mobile_pairing" not in bridge
    assert "blimgui_panel" not in bridge


@pytest.mark.parametrize("offered", ["", "attacker-token", "non-ascii-\u2603"])
def test_known_ip_cannot_authorize_or_replace_token(http_bridge, offered):
    bridge = http_bridge
    lan = bridge.mobile_lan
    nonce = lan.arm_enroll()
    assert lan.enroll(nonce, ip="192.168.0.44", token="original-token", name="Original")["ok"]
    lan.disarm_enroll()
    before = lan.persist_path().read_bytes()
    phones = lan.list_phones()

    class Request:
        path = "/status"
        client_address = ("192.168.0.44", 9)
        headers = _headers({"X-MSBT-Device": offered})

    assert bridge._authorized_request(Request()) == (False, "192.168.0.44")
    assert lan.list_phones() == phones
    assert lan.persist_path().read_bytes() == before
    assert lan.is_allowed("10.1.1.8", "original-token")


def test_token_refresh_cannot_overwrite_another_phone_at_same_ip(http_bridge):
    bridge = http_bridge
    lan = bridge.mobile_lan
    nonce = lan.arm_enroll()
    assert lan.enroll(nonce, ip="192.168.0.44", token="phone-A", name="A")["ok"]
    assert lan.enroll(nonce, ip="192.168.0.55", token="phone-B", name="B")["ok"]
    lan.disarm_enroll()

    class Request:
        path = "/status"
        client_address = ("192.168.0.44", 9)
        headers = _headers({"X-MSBT-Device": "phone-B"})

    assert bridge._authorized_request(Request()) == (True, "192.168.0.44")
    phones = {row["token"]: row for row in lan.list_phones()}
    assert set(phones) == {"phone-A", "phone-B"}
    assert phones["phone-A"]["name"] == "A"
    assert phones["phone-B"]["ip"] == "192.168.0.44"
    assert lan.is_allowed("10.0.0.1", "phone-A")
    assert lan.is_allowed("10.0.0.2", "phone-B")
    assert lan.revoke_phone("phone-B")
    assert not bridge._authorized_request(Request())[0]
    assert lan.is_allowed("192.168.0.44", "phone-A")


def test_legacy_ip_only_record_requires_enrollment(tmp_path, monkeypatch):
    lan = _load_lan(tmp_path, monkeypatch)
    lan.persist_path().write_text(json.dumps({"lan_enabled": True, "phones": [
        {"ip": "192.168.0.44", "name": "Legacy", "enrolled_at": 1.0}
    ]}), encoding="utf-8")
    lan.load()
    assert not lan.is_allowed("192.168.0.44", "")
    assert not lan.is_allowed("192.168.0.44", "new-token")
    assert not lan.enroll("wrong", ip="192.168.0.44", token="new-token")["ok"]
    nonce = lan.arm_enroll()
    assert lan.enroll(nonce, ip="192.168.0.44", token="new-token")["ok"]
    lan.disarm_enroll()
    assert lan.is_allowed("192.168.0.44", "new-token")
    lan.reset_state()
    lan.load()
    assert lan.is_allowed("10.0.0.9", "new-token")
    assert not lan.is_allowed("192.168.0.44", "")


def test_explicit_same_ip_enrollment_does_not_replace_existing_credential(tmp_path, monkeypatch):
    lan = _load_lan(tmp_path, monkeypatch)
    nonce = lan.arm_enroll()
    assert lan.enroll(nonce, ip="192.168.0.44", token="first-token")["ok"]
    assert lan.enroll(nonce, ip="192.168.0.44", token="second-token")["ok"]
    assert {row["token"] for row in lan.list_phones()} == {"first-token", "second-token"}
    assert lan.is_allowed("192.168.0.44", "first-token")
    assert lan.is_allowed("192.168.0.44", "second-token")
    assert not lan.is_allowed("192.168.0.44", "")


def test_legacy_ip_revoke_preserves_enrolled_phones_sharing_address(tmp_path, monkeypatch):
    lan = _load_lan(tmp_path, monkeypatch)
    lan.persist_path().write_text(json.dumps({"lan_enabled": True, "phones": [
        {"ip": "192.168.0.44", "name": "Legacy", "enrolled_at": 1.0}
    ]}), encoding="utf-8")
    lan.load()
    nonce = lan.arm_enroll()
    assert lan.enroll(nonce, ip="192.168.0.44", token="phone-A", name="A")["ok"]
    assert lan.enroll(nonce, ip="192.168.0.44", token="phone-B", name="B")["ok"]

    assert lan.revoke_phone("192.168.0.44")
    phones = lan.list_phones()
    assert len(phones) == 2
    assert {row["token"] for row in phones} == {"phone-A", "phone-B"}
    assert lan.is_allowed("192.168.0.44", "phone-A")
    assert lan.is_allowed("192.168.0.44", "phone-B")

    # The UI passes the enrolled phone's token, which must still revoke only it.
    assert lan.revoke_phone("phone-B")
    assert [row["token"] for row in lan.list_phones()] == ["phone-A"]
    assert lan.is_allowed("192.168.0.44", "phone-A")
    assert not lan.is_allowed("192.168.0.44", "phone-B")
