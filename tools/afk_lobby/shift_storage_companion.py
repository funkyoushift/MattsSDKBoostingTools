# Derived from ShiftManagement optional companion v4.4; upstream source SHA-256 5c7471473c869ad7361cc3a458b30b0f302b7886eda0d3182ac64e63e7c6263f.
from __future__ import annotations

"""SHiFT settings storage over a same-process loopback service."""

import hashlib
import json
import os
import tempfile
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from mods_base import CoopSupport, Game, SETTINGS_DIR, build_mod
from unrealsdk import logging
from .shift_peer_process import peer_is_game

CONFIG_DIR = Path(SETTINGS_DIR) / "ShiftManagement"
CONFIG_PATH = CONFIG_DIR / "BL4_ShiftManagement_Settings_v1.json"

DEFAULT_DATA: dict[str, Any] = {
    "version": 2,
    "reviewed": False,
    "settings": {
        "friendRequestMode": "accept",
        "gameInviteMode": "decline",
        "pollIntervalSeconds": 5,
        "removalBatchSize": 1,
        "confirmBulkRemoval": True,
        "iconMode": "default",
    },
    "protectedPlayers": [],
}

_data: dict[str, Any] = {}
_storage_valid = False
_storage_state = "unavailable"
_storage_digest = None
_lock = threading.RLock()
_server = None
_server_thread = None
_instance = ""
_background = None
_command_lock = threading.RLock()
_page_command = None
_hooks_installed = False
_disabling = False
_TICK = '/Script/Engine.CameraModifier:BlueprintModifyCamera'
_OPEN = '/Script/ShiftUI.ShiftUIFunctionLibrary:Open'
_CLOSE = '/Script/ShiftUI.ShiftUIFunctionLibrary:Close'
_HOOK_PREFIX = 'ShiftManagement.background'


def _dedupe_names(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    if not isinstance(values, list):
        return out
    for raw in values:
        name = str(raw or "").strip()
        key = name.casefold()
        if name and key not in seen:
            seen.add(key)
            out.append(name)
    return out


def _normalize(raw: Any) -> dict[str, Any]:
    base = json.loads(json.dumps(DEFAULT_DATA))
    if not isinstance(raw, dict):
        return base

    # Accept compact payload emitted by the PAK.
    if isinstance(raw.get("s"), dict):
        compact = raw["s"]
        raw = {
            "version": raw.get("v", 2),
            "reviewed": raw.get("reviewed") is True,
            "settings": {
                "friendRequestMode": compact.get("f"),
                "gameInviteMode": compact.get("g"),
                "pollIntervalSeconds": compact.get("p"),
                "removalBatchSize": compact.get("b"),
                "confirmBulkRemoval": bool(compact.get("c", 1)),
                "iconMode": compact.get("i"),
            },
            "protectedPlayers": raw.get("n", []),
        }

    settings = raw.get("settings") if isinstance(raw.get("settings"), dict) else {}
    fr = str(settings.get("friendRequestMode", base["settings"]["friendRequestMode"]))
    gi = str(settings.get("gameInviteMode", base["settings"]["gameInviteMode"]))
    icon = str(settings.get("iconMode", base["settings"]["iconMode"]))
    if fr in ("accept", "decline", "ignore"):
        base["settings"]["friendRequestMode"] = fr
    if gi in ("accept", "decline", "ignore"):
        base["settings"]["gameInviteMode"] = gi
    if icon in ("default", "switch", "xbox", "playstation"):
        base["settings"]["iconMode"] = icon
    try:
        base["settings"]["pollIntervalSeconds"] = max(2, min(10, int(settings.get("pollIntervalSeconds", 5))))
    except Exception:
        pass
    try:
        base["settings"]["removalBatchSize"] = max(1, min(10, int(settings.get("removalBatchSize", 1))))
    except Exception:
        pass
    base["settings"]["confirmBulkRemoval"] = bool(settings.get("confirmBulkRemoval", True))
    if isinstance(raw.get("protectedPlayers"), list):
        base["protectedPlayers"] = _dedupe_names(raw["protectedPlayers"])
    base["version"] = 2
    base["reviewed"] = raw.get("reviewed") is True
    return base


def _load() -> None:
    global _data, _storage_valid, _storage_digest, _storage_state
    _storage_state = "unavailable"
    _data = {}
    _storage_valid = False
    _storage_digest = None
    try:
        if not CONFIG_PATH.exists():
            _storage_state = "missing"
            return
        if not CONFIG_PATH.is_file():
            _storage_state = "invalid"
            return
        content = CONFIG_PATH.read_bytes()
        raw = json.loads(content.decode("utf-8"))
        if (not isinstance(raw, dict) or not isinstance(raw.get("settings"), dict)
                or not isinstance(raw.get("protectedPlayers"), list)
                or not all(isinstance(name, str) for name in raw["protectedPlayers"])):
            raise ValueError("Invalid persistent settings structure")
        _data = _normalize(raw)
        _storage_digest = hashlib.sha256(content).digest()
        _storage_valid = True
        _storage_state = "valid"
    except Exception as exc:
        _storage_state = "invalid"
        pass


def _save() -> bool:
    global _storage_valid, _storage_digest, _storage_state
    temp_path = None
    try:
        if not _storage_valid or _storage_digest is None:
            return False
        content = json.dumps(_normalize(_data), indent=2, sort_keys=True).encode("utf-8")
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix=".shift-save-", suffix=".tmp", dir=CONFIG_DIR)
        temp_path = Path(name)
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
        try:
            unchanged = hashlib.sha256(CONFIG_PATH.read_bytes()).digest() == _storage_digest
        except OSError:
            unchanged = False
        if not unchanged:
            _storage_valid = False
            _storage_state = "changed"
            _storage_digest = None
            return False
        os.replace(temp_path, CONFIG_PATH)
        _storage_digest = hashlib.sha256(content).digest()
        return True
    except Exception:
        return False
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _initialize(value: Any) -> bool:
    """Create only after explicit review; never replace an existing file."""
    global _data, _storage_valid, _storage_state, _storage_digest
    if _storage_state != "missing":
        return False
    temp_path = None
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        content = json.dumps(_normalize(value), indent=2, sort_keys=True).encode("utf-8")
        fd, name = tempfile.mkstemp(prefix=".shift-init-", suffix=".tmp", dir=CONFIG_DIR)
        temp_path = Path(name)
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
        os.link(temp_path, CONFIG_PATH)  # Atomic creation; fails if any file appeared.
        _data = _normalize(value)
        _storage_digest = hashlib.sha256(content).digest()
        _storage_valid = True
        _storage_state = "valid"
        return True
    except Exception as exc:
        _storage_state = "changed" if CONFIG_PATH.exists() else "unavailable"
        return False
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


def _state_payload():
    global _storage_valid, _storage_digest, _storage_state
    if _storage_valid:
        try:
            unchanged = hashlib.sha256(CONFIG_PATH.read_bytes()).digest() == _storage_digest
        except OSError:
            unchanged = False
        if not unchanged:
            _storage_valid = False
            _storage_state = "changed"
            _storage_digest = None
    payload = dict(_data) if _storage_valid else {}
    payload.update(storageValid=_storage_valid, storageState=_storage_state)
    return payload


def _process_save(incoming):
    global _data
    if not isinstance(incoming, dict):
        raise ValueError("JSON object required")
    names = incoming.get("n") if "s" in incoming else incoming.get("protectedPlayers")
    if not isinstance(names, list) or not all(isinstance(name, str) for name in names):
        raise ValueError("Invalid protected list")
    _state_payload()
    if not _storage_valid:
        if incoming.get("initialize") is not True or incoming.get("reviewed") is not True or not _initialize(incoming):
            raise ValueError("Storage unavailable or initialization not authorized")
        return
    previous = _data
    _data = _normalize(incoming)
    if not _save():
        _data = previous
        raise ValueError("Storage changed or save failed")


def _background_status():
    global _page_command
    controller = _background
    status = controller.status() if controller is not None else {
        "available": False, "state": "unsupported", "reason": "Background view is unavailable.", "token": None}
    status["start_token"] = uuid.uuid4().hex
    with _command_lock:
        if _page_command is not None and time.monotonic() >= _page_command["deadline"]:
            _page_command = None
        if _page_command is not None:
            status["command"] = {"id": _page_command["id"], "mode": _page_command["mode"]}
    return status


def _clear_page_command(mode):
    global _page_command
    with _command_lock:
        if _page_command is not None and _page_command["mode"] == mode:
            _page_command = None


def background_control(mode):
    """Game-thread entry point for the MSBT panel; never sends social actions."""
    global _page_command
    if mode not in ("status", "show", "start", "stop"):
        return {"ok": False, "background": _background_status(), "message": "Invalid background command."}
    if mode == "status":
        return {"ok": True, "background": _background_status(), "message": "Background status."}
    if _background is None or not _background_status()["available"] or _disabling:
        return {"ok": False, "background": _background_status(), "message": "Background view is unavailable."}
    try:
        if mode in ("show", "start"):
            import unrealsdk
            cls = unrealsdk.find_class('/Script/ShiftUI.ShiftUIFunctionLibrary')
            if cls is None or cls.ClassDefaultObject is None:
                raise RuntimeError('SHiFT is unavailable.')
            library = cls.ClassDefaultObject
            status = _background_status()
            if mode == "show" or (status["state"] not in ("active", "pending") and not library.IsVisible()):
                library.Open(0)
        if mode in ("start", "stop"):
            with _command_lock:
                _page_command = {"id": uuid.uuid4().hex, "mode": mode, "deadline": time.monotonic() + 10.0}
        return {"ok": True, "background": _background_status(), "message": "SHiFT command queued." if mode != "show" else "SHiFT opened."}
    except Exception as exc:
        return {"ok": False, "background": _background_status(), "message": str(exc)[:300]}


def _remove_background_hooks():
    global _hooks_installed
    if not _hooks_installed:
        return
    import unrealsdk
    for target, typ, suffix in ((_TICK, unrealsdk.hooks.Type.POST, '.tick'),
                                (_OPEN, unrealsdk.hooks.Type.PRE, '.open'),
                                (_CLOSE, unrealsdk.hooks.Type.PRE, '.close')):
        try:
            unrealsdk.hooks.remove_hook(target, typ, _HOOK_PREFIX + suffix)
        except Exception:
            pass
    _hooks_installed = False


def _background_tick(*_args):
    if _background is None:
        return
    try:
        _background.tick()
        if _disabling and _background.quiescent:
            _remove_background_hooks()
    except Exception as exc:
        logging.warning('[ShiftManagement] Background lifecycle: %s', str(exc)[:300])


def _before_open(*_args):
    if _background is None:
        return
    try:
        if _background.before_open():
            return
    except Exception as exc:
        logging.warning('[ShiftManagement] Background open guard: %s', str(exc)[:300])
    from unrealsdk.hooks import Block
    return Block


def _before_close(*_args):
    if _background is None:
        return
    try:
        if _background.before_close():
            return
    except Exception as exc:
        logging.warning('[ShiftManagement] Background close guard: %s', str(exc)[:300])
    from unrealsdk.hooks import Block
    return Block


def _setup_background():
    global _background, _hooks_installed, _disabling
    _disabling = False
    try:
        import mods_base
        import unrealsdk
        from .shift_background import BackgroundController
        from .shift_background_native import NativeShiftView
        _background = BackgroundController(NativeShiftView(unrealsdk), unrealsdk, mods_base.get_pc)
        _hooks_installed = True
        for target, typ, suffix, callback in ((_TICK, unrealsdk.hooks.Type.POST, '.tick', _background_tick),
                (_OPEN, unrealsdk.hooks.Type.PRE, '.open', _before_open),
                (_CLOSE, unrealsdk.hooks.Type.PRE, '.close', _before_close)):
            unrealsdk.hooks.add_hook(target, typ, _HOOK_PREFIX + suffix, callback)
        _hooks_installed = True
    except Exception as exc:
        _remove_background_hooks()
        _background = None
        logging.warning('[ShiftManagement] Background view unavailable: %s', str(exc)[:300])



class _StorageHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *_args):
        pass

    def _reply(self, status, payload):
        body = json.dumps(payload, separators=(",", ":"), allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-MSBT-Shift-Instance")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self):
        if not peer_is_game(self.client_address, self.server.server_port):
            self.close_connection = True
            self._reply(403, {"ok": False, "error": "forbidden"})
            return False
        return True

    def _identity(self):
        return {"ok": True, "service": "msbt-shift-storage", "protocol": 1, "instance": _instance}

    def do_OPTIONS(self):
        if not self._authorized(): return
        if self.path not in ("/shift-settings", "/shift-background"):
            self._reply(404, {"ok": False}); return
        self._reply(200, self._identity())

    def do_GET(self):
        if not self._authorized(): return
        if self.path not in ("/shift-settings", "/shift-background"):
            self._reply(404, {"ok": False}); return
        with _lock:
            result = {**self._identity(), **_state_payload()}
        result["background"] = _background_status()
        self._reply(200, result)

    def do_POST(self):
        if not self._authorized(): return
        if self.path not in ("/shift-settings", "/shift-background"):
            self.close_connection = True; self._reply(404, {"ok": False}); return
        if self.headers.get("X-MSBT-Shift-Instance") != _instance:
            self.close_connection = True; self._reply(403, {"ok": False, "error": "instance"}); return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError:
            length = -1
        if not 0 < length <= 65536 or self.headers.get("Transfer-Encoding"):
            self.close_connection = True; self._reply(413, {"ok": False, "error": "size"}); return
        try:
            incoming = json.loads(self.rfile.read(length).decode("utf-8"))
            if self.path == "/shift-background":
                with _lock:
                    state = _state_payload()
                    ready = state.get("storageValid") is True and state.get("reviewed") is True
                controller = _background
                if controller is None:
                    raise ValueError("Background unavailable")
                outcome = controller.request(incoming, ready)
                if not outcome.get("ok"):
                    background = _background_status()
                    if (isinstance(incoming, dict) and incoming.get("mode") == "heartbeat"
                            and background.get("state") == "foreground"):
                        self._reply(409, {**self._identity(), "ok": False, "background": background})
                        return
                    raise ValueError("Background request denied")
                _clear_page_command(incoming.get("mode"))
                result = {**self._identity(), "background": _background_status()}
            else:
                with _lock:
                    _process_save(incoming)
                    result = {**self._identity(), **_state_payload(), "saved": True}
                result["background"] = _background_status()
            self._reply(200, result)
        except (ValueError, UnicodeError, json.JSONDecodeError):
            self._reply(400, {"ok": False, "error": "invalid_or_unavailable"})


def _start_server():
    global _server, _server_thread, _instance
    _instance = uuid.uuid4().hex
    for port in (47991, 47992, 47993):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), _StorageHandler)
            server.daemon_threads = True
            worker = threading.Thread(target=server.serve_forever, name="ShiftStorage", daemon=True)
            worker.start()
            _server, _server_thread = server, worker
            return True
        except OSError:
            continue
    _instance = ""
    return False


def _enable():
    if _server is not None:
        return
    if _disabling and _hooks_installed:
        logging.warning('[ShiftManagement] Background cleanup is still pending.')
        return
    with _lock:
        _load()
    _setup_background()
    if not _start_server():
        logging.warning("[ShiftManagement] Storage service could not bind a loopback port.")


def _disable():
    global _server, _server_thread, _instance, _page_command, _disabling
    _disabling = True
    with _command_lock:
        _page_command = None
    if _background is not None:
        _background.shutdown()
    server, worker = _server, _server_thread
    _server = _server_thread = None
    _instance = ""
    if server is not None:
        server.shutdown()
        server.server_close()
    if worker is not None:
        worker.join(timeout=2)


MOD = build_mod(
    name="Shift Management Storage Companion",
    author="Shift Management",
    description="Same-process loopback storage for SHiFT settings; no friend actions.",
    supported_games=Game.BL4,
    coop_support=CoopSupport.Unknown,
    on_enable=_enable,
    on_disable=_disable,
)
