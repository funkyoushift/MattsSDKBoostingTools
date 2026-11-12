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
from collections import deque
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
_page_command_error = ""
_background_terminal_token = None
_menu_handoff = None
_menu_handoff_internal = False
_menu_resume_command_id = None
_menu_resume_token = None
_menu_resume_accepted = False
_revoked_menu_resume_tokens = deque(maxlen=64)
_menu_handoff_last_tick = 0.0
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
            stream.flush()
            os.fsync(stream.fileno())
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
            stream.flush()
            os.fsync(stream.fileno())
        # Windows rename is atomic and refuses an existing destination. Unlike
        # link(), it also works on game drives without hard-link support. Never
        # use replace() for first creation: a late file belongs to another writer.
        if os.name == 'nt':
            os.rename(temp_path, CONFIG_PATH)
        else:
            os.link(temp_path, CONFIG_PATH)
        _data = _normalize(value)
        _storage_digest = hashlib.sha256(content).digest()
        _storage_valid = True
        _storage_state = "valid"
        return True
    except Exception as exc:
        _storage_state = "changed" if CONFIG_PATH.exists() else "missing"
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


def _background_status(*, presentation=False):
    global _page_command, _page_command_error, _menu_resume_token, _menu_resume_command_id, _menu_resume_accepted
    controller = _background
    status = controller.status() if controller is not None else {
        "available": False, "state": "unsupported", "reason": "Background view is unavailable.", "token": None}
    status["native_state"] = status.get("state", "unknown")
    handoff = _menu_handoff
    status.update(handoff.status() if handoff is not None else {"handoff_state": "idle"})
    with _command_lock:
        if _page_command is not None and time.monotonic() >= _page_command["deadline"]:
            if _page_command.get('id') == _menu_resume_command_id:
                if _menu_resume_token is not None:
                    _revoked_menu_resume_tokens.append(hashlib.sha256(_menu_resume_token.encode('ascii')).digest())
                _menu_resume_command_id = _menu_resume_token = None
                _menu_resume_accepted = False
            _page_command_error = 'SHiFT did not confirm the desktop command. Open SHiFT with F10 and check the installed game integration.'
            _page_command = None
        if _page_command is not None:
            status["command"] = {"id": _page_command["id"], "mode": _page_command["mode"]}
            status['command_pending'] = _page_command['mode']
        if (_page_command is not None and _page_command.get('mode') == 'start'
                and _page_command.get('id') == _menu_resume_command_id):
            if _menu_resume_token is None:
                _menu_resume_token = uuid.uuid4().hex
            status['start_token'] = _menu_resume_token
        else:
            status['start_token'] = uuid.uuid4().hex
        if _page_command_error:
            status['command_error'] = _page_command_error
    if presentation and status.get('handoff_state') in ('suspended_menu', 'resuming'):
        # The web page continues to receive native protocol states. Only the
        # desktop presentation gets a logical menu-handoff state.
        phase = status['handoff_state']
        error = status.get('handoff_error')
        if error in ('close_failed', 'resume_failed') or status['native_state'] == 'error' or status.get('command_error'):
            status['state'] = 'error'
            status['reason'] = status.get('command_error') or status.get('reason') or 'SHiFT menu handoff failed. Start again after closing game menus.'
        elif not (phase == 'resuming' and status['native_state'] == 'active'):
            status['state'] = phase
            status['reason'] = ('Waiting for the game menu to close.' if phase == 'suspended_menu'
                                else 'Waiting for SHiFT to confirm background acceptance.')
    return status


def _clear_page_command(mode):
    global _page_command, _page_command_error
    with _command_lock:
        if _page_command is not None and _page_command["mode"] == mode:
            _page_command = None
            _page_command_error = ""


def _ack_page_stop(incoming):
    """The page can stop foreground acceptance without owning a native lease."""
    global _page_command, _page_command_error
    if (set(incoming) != {'mode', 'command_id'} or incoming['mode'] != 'ack_stop'
            or not isinstance(incoming['command_id'], str) or len(incoming['command_id']) != 32):
        raise ValueError('Invalid stop acknowledgement')
    with _command_lock:
        if _page_command is not None:
            if _page_command['id'] != incoming['command_id'] or _page_command['mode'] != 'stop':
                raise ValueError('Stale stop acknowledgement')
            _page_command = None
            _page_command_error = ""


def background_control(mode):
    """Game-thread entry point for the MSBT panel; never sends social actions."""
    global _page_command, _page_command_error
    if mode not in ("status", "show", "start", "stop"):
        return {"ok": False, "background": _background_status(), "message": "Invalid background command."}
    if mode == "status":
        return {"ok": True, "background": _background_status(presentation=True), "message": "Background status."}
    handoff = _menu_handoff
    if handoff is not None and not _menu_handoff_internal:
        if mode == "start":
            # Revoke the previous automatic Start before queueing a new user
            # command; rearm again after native Open's synchronous hook below.
            handoff.on_start()
        elif mode == "stop":
            handoff.on_stop()
        elif mode == "show":
            handoff.on_show()
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
                _page_command_error = ""
                _page_command = {"id": uuid.uuid4().hex, "mode": mode, "deadline": time.monotonic() + 10.0}
        result = {"ok": True, "background": _background_status(), "message": "SHiFT command queued." if mode != "show" else "SHiFT opened."}
        if mode == "start" and handoff is not None and not _menu_handoff_internal:
            handoff.on_start()
        return result
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
    global _menu_handoff_last_tick
    if _background is None:
        return
    try:
        handoff = _menu_handoff
        if handoff is not None:
            now = time.monotonic()
            if now - _menu_handoff_last_tick >= 0.05:
                _menu_handoff_last_tick = now
                try:
                    handoff.tick()
                except Exception as exc:
                    logging.warning('[ShiftManagement] Menu handoff: %s', type(exc).__name__)
        _background.tick()
        if _disabling and _background.quiescent:
            _remove_background_hooks()
    except Exception as exc:
        logging.warning('[ShiftManagement] Background lifecycle: %s', str(exc)[:300])


def _before_open(*_args):
    if _background is None:
        return
    if (_menu_handoff is not None and not _menu_handoff_internal
            and not _background._tick_running and not _background._closing):
        _menu_handoff.on_show()
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
    if (_menu_handoff is not None and not _menu_handoff_internal
            and not _background._tick_running and not _background._closing):
        _menu_handoff.on_show()
    try:
        if _background.before_close():
            return
    except Exception as exc:
        logging.warning('[ShiftManagement] Background close guard: %s', str(exc)[:300])
    from unrealsdk.hooks import Block
    return Block


def _cancel_menu_resume():
    """Revoke only the still-owned automatic resume command/session."""
    global _menu_resume_command_id, _menu_resume_token, _menu_resume_accepted, _background_terminal_token
    global _page_command, _page_command_error
    with _command_lock:
        command_id = _menu_resume_command_id
        token = _menu_resume_token
        accepted = _menu_resume_accepted
        _menu_resume_command_id = None
        _menu_resume_token = None
        _menu_resume_accepted = False
        if token is not None:
            _revoked_menu_resume_tokens.append(hashlib.sha256(token.encode('ascii')).digest())
        if (command_id is not None and _page_command is not None
                and _page_command.get('id') == command_id and _page_command.get('mode') == 'start'):
            _page_command = None
            _page_command_error = ''
    controller = _background
    if token is None or controller is None or not accepted:
        return
    try:
        current = controller.status()
        if (current.get('token') == token and current.get('state') in ('pending', 'active')):
            result = controller.request({'mode': 'stop', 'token': token})
            if result.get('ok'):
                with _command_lock:
                    if _background_terminal_token == token:
                        _background_terminal_token = None
    except Exception:
        # Cancellation stays conservative: the stale/other token is never used.
        pass


def _setup_menu_handoff(MenuHandoff, MenuSnapshot, probe_menu_state, sdk):
    global _menu_handoff, _menu_resume_command_id, _menu_resume_token, _menu_resume_accepted
    _menu_resume_command_id = None
    _menu_resume_token = None
    _menu_resume_accepted = False
    controller = _background

    def snapshot():
        c = _background
        if c is None or c._thread is None or c._thread != threading.get_ident():
            return MenuSnapshot(False, None, None, False)
        try:
            pc = c.get_pc()
            pawn = getattr(pc, 'Pawn', None)
            player = getattr(pc, 'Player', None)
            menu = probe_menu_state(sdk, pc)
            state = c.status()
            identity = ((pc, pawn, player, getattr(pawn, 'Outer', None), _instance)
                        if pc is not None and pawn is not None and player is not None and _instance else None)
            native_closed = False
            if (_menu_handoff is not None and _menu_handoff.status()['handoff_state'] != 'idle'
                    and state.get('state') == 'idle' and c.quiescent):
                _, values, _canvas, _visible = c.native._inspect()
                native_closed = (list(values) == [2, 2, 2] and not c.native.owned)
            connected = bool(_server is not None and _server_thread is not None
                             and _server_thread.is_alive() and not _disabling and bool(_instance))
            return MenuSnapshot(
                active=(state.get('state') == 'active' and c._owned()),
                identity=identity, menu=menu, connected=connected,
                native_state=('error' if (_page_command_error and _menu_handoff is not None
                              and _menu_handoff.status()['handoff_state'] == 'resuming')
                              else state.get('state', 'unknown')), native_closed=native_closed)
        except Exception:
            return MenuSnapshot(False, None, None, False)

    def close_for_menu():
        global _menu_handoff_internal
        c = _background
        if c is None:
            return False
        c._bind()
        with c._lock:
            if c._tick_running or c.status().get('state') != 'active' or not c._owned():
                return False
            pc = c.get_pc()
            pawn = getattr(pc, 'Pawn', None)
            player = getattr(pc, 'Player', None)
            if pc is None or pawn is None or player is None or probe_menu_state(sdk, pc) is not True:
                return False
            stats_cls = sdk.find_class('GameplayStatics')
            stats = getattr(stats_cls, 'ClassDefaultObject', None)
            paused = stats.IsGamePaused(pc) if stats is not None else None
            cursor = getattr(pc, 'bShowMouseCursor', None)
            if type(paused) is not bool or type(cursor) is not bool:
                return False

            _menu_handoff_internal = True
            try:
                closed = c._stop_attempt() and c.quiescent
            finally:
                _menu_handoff_internal = False

            # Native SHiFT Close can unpause and hide the cursor. Restore only
            # these captured menu-facing values, after proving the same player
            # still owns the controller. No input mode or mapping is changed.
            if c.get_pc() != pc or getattr(pc, 'Pawn', None) != pawn or getattr(pc, 'Player', None) != player:
                return False
            try:
                current_paused = stats.IsGamePaused(pc)
                if current_paused is not paused:
                    stats.SetGamePaused(pc, paused)
                pc.bShowMouseCursor = cursor
                if stats.IsGamePaused(pc) is not paused or pc.bShowMouseCursor is not cursor:
                    return False
            except Exception:
                return False
            if not closed:
                return False
            _, values, _canvas, _visible = c.native._inspect()
            return list(values) == [2, 2, 2] and not c.native.owned and c.quiescent

    # Every controller-driven close (including Stop, disable and a retry) must
    # preserve a separately open game menu, not only the first handoff close.
    original_stop = getattr(controller, '_stop_attempt', None)

    def preserve_menu_stop(*args, **kwargs):
        c = controller
        c._bind()
        captured = None
        if c._owned() or c._closing:
            pc = c.get_pc()
            if probe_menu_state(sdk, pc) is True:
                stats_cls = sdk.find_class('GameplayStatics')
                stats = getattr(stats_cls, 'ClassDefaultObject', None)
                paused = stats.IsGamePaused(pc) if stats is not None else None
                cursor = getattr(pc, 'bShowMouseCursor', None)
                if type(paused) is bool and type(cursor) is bool:
                    captured = (pc, pc.Pawn, pc.Player, stats, paused, cursor)
        try:
            return original_stop(*args, **kwargs)
        finally:
            if captured is not None:
                pc, pawn, player, stats, paused, cursor = captured
                if c.get_pc() == pc and getattr(pc, 'Pawn', None) == pawn and getattr(pc, 'Player', None) == player:
                    if stats.IsGamePaused(pc) is not paused:
                        stats.SetGamePaused(pc, paused)
                    pc.bShowMouseCursor = cursor
                    if stats.IsGamePaused(pc) is not paused or pc.bShowMouseCursor is not cursor:
                        raise RuntimeError('Menu state restoration incomplete')

    if callable(getattr(controller, '_stop_attempt', None)):
        controller._stop_attempt = preserve_menu_stop

    original_control = background_control

    def resume_after_menu():
        global _menu_handoff_internal, _menu_resume_command_id, _menu_resume_token
        c = _background
        if c is None:
            return False
        c._bind()
        _menu_handoff_internal = True
        try:
            # Hold the command lock across queueing and ID capture. A fast page
            # poll cannot consume the new start before we can own its ID.
            with _command_lock:
                _menu_resume_command_id = None
                _menu_resume_token = None
                result = original_control('start')
                if (isinstance(result, dict) and result.get('ok') is True
                        and _page_command is not None and _page_command.get('mode') == 'start'):
                    _menu_resume_command_id = _page_command.get('id')
                    return _menu_resume_command_id is not None
                return False
        finally:
            _menu_handoff_internal = False

    _menu_handoff = MenuHandoff(snapshot, close_for_menu, resume_after_menu,
                                clock=time.monotonic, cancel_resume=_cancel_menu_resume)
    original_request = controller.request

    def tracked_request(payload):
        global _menu_resume_command_id, _menu_resume_token, _menu_resume_accepted
        mode = payload.get('mode') if isinstance(payload, dict) else None
        automatic = False
        with _command_lock:
            if mode == 'start' and isinstance(payload.get('token'), str):
                digest = hashlib.sha256(payload['token'].encode('ascii', errors='ignore')).digest()
                if digest in _revoked_menu_resume_tokens:
                    return {'ok': False, 'error': 'Cancelled background start.'}
            result = original_request(payload)
            if not isinstance(payload, dict) or result.get('ok') is not True:
                return result
            if mode == 'start':
                if (_menu_resume_command_id is not None and _page_command is not None
                        and _page_command.get('id') == _menu_resume_command_id
                        and _page_command.get('mode') == 'start'):
                    _menu_resume_token = payload.get('token')
                    _menu_resume_command_id = None
                    _menu_resume_accepted = True
                    automatic = True
            elif mode == 'stop':
                if _menu_resume_token is not None and payload.get('token') == _menu_resume_token:
                    _revoked_menu_resume_tokens.append(hashlib.sha256(_menu_resume_token.encode('ascii')).digest())
                _menu_resume_command_id = None
                _menu_resume_token = None
                _menu_resume_accepted = False
        if mode == 'start' and not automatic and not _menu_handoff_internal:
            _menu_handoff.on_start()
        elif mode == 'stop':
            _menu_handoff.on_stop()
        return result

    controller.request = tracked_request


def _setup_background():
    global _background, _hooks_installed, _disabling, _menu_handoff
    _disabling = False
    try:
        import mods_base
        import unrealsdk
        from .shift_background import BackgroundController
        from .shift_background_native import NativeShiftView
        from .shift_menu_handoff import MenuHandoff, MenuSnapshot, probe_menu_state
        _background = BackgroundController(NativeShiftView(unrealsdk), unrealsdk, mods_base.get_pc)
        _menu_handoff = None
        try:
            _setup_menu_handoff(MenuHandoff, MenuSnapshot, probe_menu_state, unrealsdk)
        except Exception as handoff_exc:
            _menu_handoff = None
            logging.warning('[ShiftManagement] Menu handoff unavailable: %s', type(handoff_exc).__name__)
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
        return {"ok": True, "service": "msbt-shift-storage", "protocol": 1, "instance": _instance,
                "integration": "msbt-shift-20261110"}

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
        global _background_terminal_token
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
                if isinstance(incoming, dict) and incoming.get('mode') == 'ack_stop':
                    _ack_page_stop(incoming)
                    self._reply(200, {**self._identity(), 'background': _background_status()})
                    return
                controller = _background
                if controller is None:
                    raise ValueError("Background unavailable")
                outcome = controller.request(incoming)
                if not outcome.get("ok"):
                    background = _background_status()
                    if (isinstance(incoming, dict) and incoming.get("mode") == "heartbeat"
                            and background.get("state") == "foreground"):
                        self._reply(409, {**self._identity(), "ok": False, "background": background})
                        return
                    with _command_lock:
                        owns_terminal = (isinstance(incoming, dict)
                                         and incoming.get("mode") == "heartbeat"
                                         and isinstance(incoming.get("token"), str)
                                         and _background_terminal_token is not None
                                         and incoming["token"] == _background_terminal_token)
                    if owns_terminal and background.get("state") == "error":
                        self._reply(409, {**self._identity(), "ok": False,
                                          "terminal": "owned-error", "background": background})
                        return
                    raise ValueError("Background request denied")
                if isinstance(incoming, dict) and incoming.get("mode") in ("start", "stop"):
                    with _command_lock:
                        if incoming["mode"] == "start":
                            token_digest = hashlib.sha256(incoming["token"].encode("ascii", errors="ignore")).digest()
                            if token_digest not in _revoked_menu_resume_tokens:
                                _background_terminal_token = incoming["token"]
                        elif incoming.get("token") == _background_terminal_token:
                            _background_terminal_token = None
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
    global _server, _server_thread, _instance, _page_command, _page_command_error, _background_terminal_token, _disabling
    global _menu_handoff, _menu_resume_command_id, _menu_resume_token, _menu_resume_accepted
    _disabling = True
    if _menu_handoff is not None:
        _menu_handoff.on_disabled()
    with _command_lock:
        _page_command = None
        _page_command_error = ""
        _background_terminal_token = None
        _menu_resume_command_id = None
        _menu_resume_token = None
        _menu_resume_accepted = False
        _revoked_menu_resume_tokens.clear()
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
    _menu_handoff = None


MOD = build_mod(
    name="Shift Management Storage Companion",
    author="Shift Management",
    description="Same-process loopback storage for SHiFT settings; no friend actions.",
    supported_games=Game.BL4,
    coop_support=CoopSupport.Unknown,
    on_enable=_enable,
    on_disable=_disable,
)
