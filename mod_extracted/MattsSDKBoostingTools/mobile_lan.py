"""LAN pairing state for the in-game SDK bridge.

Loopback stays open for Electron. LAN clients must enroll while the pairing
overlay is open, then present a remembered device token (and/or IP).
Does not import BLImGui or UMG.
"""
from __future__ import annotations

import json
import os
import secrets
import socket
import threading
import time
from pathlib import Path
from typing import Any, Callable

_PORT = 49774
INSTALL_URL = "https://www.funkyoushift.com/MattsSDKBoostingTools/mobile-install.html"
_STATE_NAME = "mobile_lan.json"
_LOCK = threading.RLock()
_rebind_cb: Callable[[], None] | None = None

_lan_enabled = False
_allowlist: list[dict[str, Any]] = []
_enroll_open = False
_enroll_nonce = ""
_enroll_nonce_at = 0.0
_ENROLL_TTL_S = 15 * 60.0


def set_rebind_callback(callback: Callable[[], None] | None) -> None:
    global _rebind_cb
    _rebind_cb = callback


def persist_path() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
    folder = Path(base) / "MattsSDKBoostingTools"
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except Exception:
        folder = Path.home() / "MattsSDKBoostingTools"
        folder.mkdir(parents=True, exist_ok=True)
    return folder / _STATE_NAME


def load() -> None:
    global _lan_enabled, _allowlist
    path = persist_path()
    if not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    if not isinstance(data, dict):
        return
    with _LOCK:
        _lan_enabled = bool(data.get("lan_enabled"))
        phones = data.get("phones") or data.get("allowlist") or []
        cleaned: list[dict[str, Any]] = []
        if isinstance(phones, list):
            for row in phones:
                if not isinstance(row, dict):
                    continue
                token = str(row.get("token") or "").strip()
                ip = str(row.get("ip") or "").strip()
                if not token and not ip:
                    continue
                cleaned.append({
                    "token": token,
                    "ip": ip,
                    "name": str(row.get("name") or "Phone")[:48],
                    "enrolled_at": float(row.get("enrolled_at") or 0.0),
                })
        _allowlist = cleaned


def save() -> None:
    path = persist_path()
    with _LOCK:
        payload = {
            "lan_enabled": bool(_lan_enabled),
            "phones": list(_allowlist),
        }
    try:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except Exception:
        pass


def lan_enabled() -> bool:
    with _LOCK:
        return bool(_lan_enabled)


def bind_host() -> str:
    return "0.0.0.0" if lan_enabled() else "127.0.0.1"


def set_lan_enabled(enabled: bool, *, persist_now: bool = True) -> bool:
    global _lan_enabled
    want = bool(enabled)
    with _LOCK:
        changed = _lan_enabled != want
        _lan_enabled = want
    if persist_now:
        save()
    if changed and _rebind_cb is not None:
        try:
            _rebind_cb()
        except Exception:
            pass
    return want


def enroll_open() -> bool:
    with _LOCK:
        if not _enroll_open:
            return False
        if _enroll_nonce and (time.time() - _enroll_nonce_at) > _ENROLL_TTL_S:
            return False
        return True


def enroll_nonce() -> str:
    with _LOCK:
        return str(_enroll_nonce or "")


def arm_enroll() -> str:
    global _enroll_open, _enroll_nonce, _enroll_nonce_at
    nonce = secrets.token_hex(4).upper()
    with _LOCK:
        _enroll_open = True
        _enroll_nonce = nonce
        _enroll_nonce_at = time.time()
    return nonce


def disarm_enroll() -> None:
    global _enroll_open, _enroll_nonce
    with _LOCK:
        _enroll_open = False
        _enroll_nonce = ""


def list_phones() -> list[dict[str, Any]]:
    with _LOCK:
        return [dict(row) for row in _allowlist]


def revoke_phone(token_or_ip: str) -> bool:
    key = str(token_or_ip or "").strip()
    if not key:
        return False
    with _LOCK:
        before = len(_allowlist)
        _allowlist[:] = [
            row for row in _allowlist
            if str(row.get("token") or "") != key and str(row.get("ip") or "") != key
        ]
        removed = len(_allowlist) != before
    if removed:
        save()
    return removed


def revoke_all() -> None:
    with _LOCK:
        _allowlist.clear()
    save()


def _is_loopback(ip: str) -> bool:
    value = str(ip or "").strip().lower()
    return value in {"127.0.0.1", "::1", "localhost", ""}


def is_allowed(ip: str, token: str = "") -> bool:
    if _is_loopback(ip):
        return True
    tok = str(token or "").strip()
    addr = str(ip or "").strip()
    with _LOCK:
        for row in _allowlist:
            if tok and str(row.get("token") or "") == tok:
                return True
            if addr and str(row.get("ip") or "") == addr:
                return True
    return False


def remember_phone(*, ip: str, token: str, name: str = "Phone") -> dict[str, Any]:
    global _lan_enabled
    addr = str(ip or "").strip()
    tok = str(token or "").strip() or secrets.token_hex(16)
    label = str(name or "Phone").strip()[:48] or "Phone"
    now = time.time()
    with _LOCK:
        found = None
        for row in _allowlist:
            if tok and str(row.get("token") or "") == tok:
                found = row
                break
            if addr and str(row.get("ip") or "") == addr:
                found = row
                break
        if found is None:
            found = {"token": tok, "ip": addr, "name": label, "enrolled_at": now}
            _allowlist.append(found)
        else:
            found["token"] = tok or str(found.get("token") or "")
            if addr:
                found["ip"] = addr
            found["name"] = label
            found["enrolled_at"] = now
        was_lan = bool(_lan_enabled)
        _lan_enabled = True
        snapshot = dict(found)
    save()
    if not was_lan and _rebind_cb is not None:
        try:
            _rebind_cb()
        except Exception:
            pass
    return snapshot


def enroll(nonce: str, *, ip: str, token: str, name: str = "Phone") -> dict[str, Any]:
    offered = str(nonce or "").strip().upper()
    with _LOCK:
        expected = str(_enroll_nonce or "").strip().upper()
        open_now = bool(_enroll_open) and bool(expected)
        stale = (time.time() - _enroll_nonce_at) > _ENROLL_TTL_S
    if not open_now or stale:
        return {"ok": False, "message": "Open the in-game Phone Pairing overlay to enroll this phone."}
    if not offered or offered != expected:
        return {"ok": False, "message": "Enroll nonce does not match the open pairing overlay."}
    phone = remember_phone(ip=ip, token=token, name=name)
    return {
        "ok": True,
        "message": "Phone remembered. LAN listen stays on after restart until you turn it off in-game.",
        "phone": phone,
        "port": _PORT,
        "lan_enabled": True,
    }


def list_lan_ipv4() -> list[str]:
    addresses: list[str] = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET, socket.SOCK_STREAM):
            ip = str(info[4][0] if info and info[4] else "")
            if _usable_lan_ip(ip) and ip not in addresses:
                addresses.append(ip)
    except Exception:
        pass
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect(("8.8.8.8", 80))
            ip = str(probe.getsockname()[0] or "")
            if _usable_lan_ip(ip) and ip not in addresses:
                addresses.insert(0, ip)
        finally:
            probe.close()
    except Exception:
        pass
    if not addresses:
        try:
            ip = socket.gethostbyname(socket.gethostname())
            if _usable_lan_ip(ip):
                addresses.append(ip)
        except Exception:
            pass
    return addresses


def _usable_lan_ip(ip: str) -> bool:
    value = str(ip or "").strip()
    if not value or _is_loopback(value):
        return False
    if value.startswith("169.254."):
        return False
    parts = value.split(".")
    if len(parts) != 4:
        return False
    try:
        nums = [int(part) for part in parts]
    except Exception:
        return False
    return all(0 <= num <= 255 for num in nums)


def pairing_payload() -> dict[str, Any]:
    nonce = enroll_nonce() or arm_enroll()
    hosts = list_lan_ipv4()
    return {
        "v": 2,
        "name": "MSBT",
        "hosts": hosts,
        "port": _PORT,
        "n": nonce,
    }


def pairing_payload_text() -> str:
    return json.dumps(pairing_payload(), separators=(",", ":"))


def install_payload_text() -> str:
    return INSTALL_URL


def status_dict() -> dict[str, Any]:
    with _LOCK:
        return {
            "lan_enabled": bool(_lan_enabled),
            "bind_host": bind_host(),
            "port": _PORT,
            "enroll_open": enroll_open(),
            "hosts": list_lan_ipv4(),
            "phones": [
                {"name": row.get("name"), "ip": row.get("ip")}
                for row in _allowlist
            ],
        }


def reset_state(*, persist: bool = False) -> None:
    """Clear in-memory pairing state. Tests only; does not bind sockets."""
    global _lan_enabled, _allowlist, _enroll_open, _enroll_nonce, _enroll_nonce_at
    with _LOCK:
        _lan_enabled = False
        _allowlist = []
        _enroll_open = False
        _enroll_nonce = ""
        _enroll_nonce_at = 0.0
    if persist:
        save()


load()
