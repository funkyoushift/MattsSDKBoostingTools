"""Console commands and the local save worker.

Unreal calls run on the camera tick; save parsing runs off the game thread.
"""

import hashlib
import hmac
import json
import os
from pathlib import Path, PurePosixPath
from importlib.resources import files
import queue
import secrets
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PREFIX = "[Mission Selector] "
PUMP = "mission_selector_worker"
_server = None
_process = None
_starting = False
_disabled = False
_lock = threading.Lock()
_pending = queue.Queue(maxsize=16)
_logs = queue.Queue(maxsize=128)
_requests = queue.Queue(maxsize=8)
_results = queue.Queue(maxsize=32)
_token = ""

HELP = """Commands (mission and objective numbers start at 1):
mission_select list --campaign fl4k
mission_select objectives --campaign fl4k --mission 3
mission_select play --campaign fl4k --mission 3 --objective 1 --yes
mission_select status
mission_select stop
mission_select bookmark --name "Before the fight"
mission_select bookmarks
mission_select load-bookmark --id BOOKMARK_ID --yes
mission_select restore --yes
mission_select dialogue --value on
Campaigns: story, fl4k, ellie, moxxi.
Experimental. Play solo and keep a second saved character in the same profile.
Replay keeps your gear and levels, but rewinds later mission progress.
Move the full MSBT sdkmod out of sdk_mods before starting the game.
Fog stays unchanged unless you add --fog clear or --fog restore.
To restore a backup, load a different character first."""


def catalogue():
    return json.loads(
        files(__package__)
        .joinpath("core", "mission_selection_states.json")
        .read_text(encoding="utf-8")
    )["missions"]


def campaign_name(name):
    return {"fl4k": "harmonica", "ellie": "cowbell", "moxxi": "mandolin"}.get(
        name.casefold(), name.casefold()
    )


def campaign_rows(campaign):
    return sorted(
        (
            (n, r)
            for n, r in catalogue().items()
            if r["campaign"] == campaign_name(campaign)
        ),
        key=lambda item: item[1]["playthrough"]["number"],
    )


def choose(campaign, mission):
    rows = campaign_rows(campaign)
    matches = [
        (n, r)
        for n, r in rows
        if str(r["playthrough"]["number"]) == mission
        or n.casefold() == mission.casefold()
        or r["title"].casefold() == mission.casefold()
    ]
    if len(matches) != 1:
        raise ValueError(
            "Choose one mission number or exact title from mission_select list."
        )
    return matches[0]


def objective_rows(name, row):
    from .core.mission_selection import main_groups

    data = json.loads(
        files(__package__)
        .joinpath("core", "mission_practice_catalog.json")
        .read_text(encoding="utf-8")
    )["missions"][name]
    return [
        (g["index"], o["title"])
        for g, o in main_groups(name, data)
        if str(g["index"]) in row["sections"]
    ]


def log(message):
    from unrealsdk import logging

    logging.info(PREFIX + str(message))


def _background_log(message):
    try:
        _logs.put_nowait(str(message)[:6000])
    except queue.Full:
        pass


def _main_mod_active():
    # The full mod starts its bridge on import, even if later menu-disabled.
    if "MattsSDKBoostingTools" in sys.modules:
        return True
    from mods_base import get_ordered_mod_list

    return any(
        getattr(m, "is_enabled", False)
        and getattr(m, "settings_file", None) is not None
        and Path(m.settings_file).stem == "MattsSDKBoostingTools"
        for m in get_ordered_mod_list()
    )


def native_action(action, payload):
    if _main_mod_active():
        raise RuntimeError(
            "Move the full MattsSDKBoostingTools.sdkmod out of sdk_mods and restart before standalone replay/dialogue controls."
        )
    if action == "standalone_dialogue":
        from .core import dialogue_controls

        return dialogue_controls.set_enabled(payload["enabled"])
    if not action.startswith("mission_save_replay_"):
        raise ValueError("Unsupported standalone action")
    from .core import mission_save_replay
    from . import tracking

    if action in ("mission_save_replay_begin", "mission_save_replay_restore_guard"):
        tracking.clear()
    result = mission_save_replay.dispatch(action, payload)
    if action == "mission_save_replay_track" and result.get("tracked"):
        try:
            tracking.arm(mission_save_replay._lease["spec"]["mission"])
        except Exception as exc:
            tracking.clear()
            log("Could not retain the replay mission across map travel: " + str(exc))
    return result


def _tick(*_args):
    from . import tracking

    try:
        tracking.tick()
    except Exception as exc:
        tracking.clear()
        log("Stopped following the replay mission: " + str(exc))
    for _ in range(4):
        try:
            result = _results.get_nowait()
        except queue.Empty:
            break
        menu = sys.modules.get(__package__ + ".menu")
        if menu is not None:
            try:
                menu.on_worker_result(result)
            except Exception as exc:
                log("Could not update the menu: " + str(exc))
    for _ in range(4):
        try:
            message = _logs.get_nowait()
        except queue.Empty:
            break
        log(message)
    try:
        ticket = _pending.get_nowait()
    except queue.Empty:
        return
    with ticket["lock"]:
        if ticket["cancelled"]:
            return
        ticket["started"] = True
    try:
        ticket["result"] = native_action(ticket["action"], ticket["payload"])
    except Exception as exc:
        ticket["result"] = dict(ok=False, message=str(exc))
    finally:
        ticket["done"].set()


NATIVE_SUFFIXES = frozenset(
    (
        "status",
        "begin",
        "capture",
        "restore_guard",
        "close",
        "loader_bind",
        "loader_refresh",
        "loader_select",
        "loader_inspect",
        "loader_pulse",
        "picker",
        "travel",
        "station_check",
        "station_place",
        "station_placement_status",
        "check",
        "placement_ready",
        "place",
        "placement_status",
        "refresh",
        "track",
    )
)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def do_POST(self):
        try:
            if not hmac.compare_digest(
                self.headers.get("Authorization", ""), "Bearer " + _token
            ):
                self.send_error(403)
                return
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 80 * 1024 * 1024:
                raise ValueError("Invalid request size")
            self.connection.settimeout(30)
            value = json.loads(self.rfile.read(length))
            if self.path == "/helper":
                if value.get("action") not in (
                    "identity",
                    "edit",
                    "inspect",
                    "bookmark_capture",
                ):
                    raise ValueError("Unsupported save helper")
                from .save_tools.mission_save_replay import dispatch

                result = dispatch(value)
            elif self.path == "/native":
                action = value.get("action", "")
                if (
                    action != "standalone_dialogue"
                    and action.removeprefix("mission_save_replay_")
                    not in NATIVE_SUFFIXES
                ):
                    raise ValueError("Unsupported native action")
                ticket = dict(
                    action=action,
                    payload=value.get("payload", {}),
                    done=threading.Event(),
                    cancelled=False,
                    started=False,
                    lock=threading.Lock(),
                )
                _pending.put_nowait(ticket)
                if not ticket["done"].wait(22):
                    with ticket["lock"]:
                        ticket["cancelled"] = True
                    raise RuntimeError(
                        "Game-thread request unconfirmed; no automatic resend"
                    )
                result = ticket["result"]
            else:
                raise ValueError("Unknown local route")
        except Exception as exc:
            result = dict(ok=False, message=str(exc))
        data = json.dumps(result).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass


def documents_path():
    """Use Windows Known Folders, including redirected OneDrive Documents."""
    import ctypes as c
    import uuid

    guid = (c.c_ubyte * 16).from_buffer_copy(
        uuid.UUID("FDD39AD0-238F-46AF-ADB4-6C85480369C7").bytes_le
    )
    result = c.c_wchar_p()
    fn = c.windll.shell32.SHGetKnownFolderPath
    fn.argtypes = [c.c_void_p, c.c_uint32, c.c_void_p, c.POINTER(c.c_wchar_p)]
    fn.restype = c.c_long
    if fn(c.byref(guid), 0, None, c.byref(result)) != 0:
        raise RuntimeError("Could not resolve the Windows Documents folder")
    try:
        return Path(result.value)
    finally:
        c.windll.ole32.CoTaskMemFree.argtypes = [c.c_void_p]
        c.windll.ole32.CoTaskMemFree(c.cast(result, c.c_void_p))


def _worker_files():
    from mods_base import SETTINGS_DIR

    manifest_bytes = files(__package__).joinpath("worker_manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    root = (
        Path(SETTINGS_DIR)
        / "BL4MissionSelector"
        / "runtime"
        / hashlib.sha256(manifest_bytes).hexdigest()[:24]
    )
    root.mkdir(parents=True, exist_ok=True)
    for name, digest in manifest["files"].items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or ".." in relative.parts or len(relative.parts) != 1:
            raise RuntimeError("Invalid bundled worker path")
        target = root / name
        if (
            target.is_file()
            and hashlib.sha256(target.read_bytes()).hexdigest() == digest
        ):
            continue
        data = files(__package__).joinpath("worker", name).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise RuntimeError("Bundled worker checksum differs")
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(data)
        temporary.replace(target)
    return root


def _read_worker(process):
    try:
        for line in process.stdout:
            try:
                result = json.loads(line)
                try:
                    _results.put_nowait(result)
                except queue.Full:
                    pass
                if result.get("bookmarks"):
                    for b in result["bookmarks"]:
                        _background_log(
                            b["id"] + " | " + b["name"] + " | " + b.get("mission", "")
                        )
                _background_log(result.get("message") or json.dumps(result))
            except (ValueError, KeyError):
                _background_log("Worker returned an invalid response.")
    finally:
        _background_log(
            "Local replay worker stopped. Backups/journal are retained; inspect status before another replay."
        )


def _launch():
    global _server, _process, _starting, _token
    try:
        root = _worker_files()
        from mods_base import SETTINGS_DIR

        save_root = (
            documents_path() / "My Games" / "Borderlands 4" / "Saved" / "SaveGames"
        )
        if not save_root.is_dir():
            raise RuntimeError(
                "Native Borderlands 4 save folder not found under Documents."
            )
        _token = secrets.token_urlsafe(32)
        _server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        _server.daemon_threads = True
        threading.Thread(target=_server.serve_forever, daemon=True).start()
        env = os.environ.copy()
        env["MSBT_SELECTOR_TOKEN"] = _token
        env["MSBT_SELECTOR_ENDPOINT"] = "http://127.0.0.1:" + str(_server.server_port)
        env["MSBT_SELECTOR_SAVE_ROOT"] = str(save_root)
        env["MSBT_SELECTOR_STORAGE"] = str(
            Path(SETTINGS_DIR) / "BL4MissionSelector" / "replay"
        )
        env["MSBT_SELECTOR_PARENT_PID"] = str(os.getpid())
        if _disabled:
            return
        process = subprocess.Popen(
            [str(root / "node.exe"), str(root / "worker.cjs")],
            cwd=root,
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        _process = process
        threading.Thread(target=_read_worker, args=(process,), daemon=True).start()
        while not _disabled:
            try:
                request = _requests.get(timeout=0.2)
            except queue.Empty:
                if process.poll() is not None:
                    break
                continue
            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()
    except Exception as exc:
        _background_log("Worker startup failed: " + str(exc))
    finally:
        if _server:
            _server.shutdown()
            _server.server_close()
        with _lock:
            while not _requests.empty():
                try:
                    _requests.get_nowait()
                except queue.Empty:
                    break
            _starting = False


def submit(action, payload):
    global _starting, _disabled
    if _main_mod_active():
        raise RuntimeError(
            "Move the full MattsSDKBoostingTools.sdkmod out of sdk_mods and restart before standalone replay."
        )
    from .core import camera_tick, travel_gate

    # Start the tick here because this mod has no Quick Menu to start it.
    travel_gate.force_in_world()
    camera_tick.register(PUMP, _tick, priority=80)
    camera_tick.set_needed(PUMP, True)
    with _lock:
        _disabled = False
        if not _starting:
            if _process and _process.poll() is None:
                raise RuntimeError(
                    "Worker state needs inspection; restart the game before another operation."
                )
            _starting = True
            threading.Thread(target=_launch, daemon=True).start()
        _requests.put_nowait(dict(action=action, payload=payload))
    log(
        "Close the console to let replay load. Use mission_select status to check progress."
    )


def run(args):
    try:
        operation = args.operation
        if operation == "help":
            log(HELP)
            return
        if operation == "list":
            rows = campaign_rows(args.campaign)
            if not rows:
                raise ValueError(
                    "Unknown campaign. Choose story, fl4k, ellie or moxxi."
                )
            for _, row in rows:
                log(str(row["playthrough"]["number"]) + ". " + row["title"])
            return
        if operation in ("objectives", "play"):
            name, row = choose(args.campaign, args.mission)
            objectives = objective_rows(name, row)
            if operation == "objectives":
                for index, (_, title) in enumerate(objectives, 1):
                    log(str(index) + ". " + title)
                return
            if not args.yes:
                raise ValueError(
                    "Replay rewinds later progress and keeps a backup. Add --yes to start."
                )
            if not 1 <= args.objective <= len(objectives):
                raise ValueError(
                    "Choose an objective number from mission_select objectives."
                )
            payload = dict(
                mission=name,
                checkpoint=objectives[args.objective - 1][0],
                automatic=True,
                acknowledge_shared_progress=True,
                fog_mode=args.fog,
            )
            submit("start", payload)
            return
        if operation in ("restore", "load-bookmark") and not args.yes:
            raise ValueError("Add --yes to apply the backed-up save operation.")
        if operation == "dialogue":
            from .core import travel_gate

            travel_gate.force_in_world()
            result = native_action(
                "standalone_dialogue", dict(enabled=args.value == "on")
            )
            log(result.get("message", str(result)))
            return
        actions = {
            "status": "status",
            "stop": "stop",
            "restore": "restore",
            "bookmark": "bookmark_save",
            "bookmarks": "bookmark_list",
            "load-bookmark": "bookmark_start",
        }
        payload = dict(
            name=args.name,
            id=args.id,
            automatic=True,
            acknowledge_shared_progress=True,
            fog_mode=args.fog,
        )
        submit(actions[operation], payload)
    except Exception as exc:
        log(str(exc))


def disable():
    global _disabled
    _disabled = True
    from . import tracking

    tracking.clear()
    process = _process
    if process and process.poll() is None:
        try:
            process.stdin.close()
        except OSError:
            pass
    if _server:
        threading.Thread(target=_server.shutdown, daemon=True).start()
    from .core import camera_tick, dialogue_controls, mission_save_replay

    try:
        state = mission_save_replay.dispatch("mission_save_replay_status", {})
        if state.get("lease"):
            mission_save_replay.dispatch(
                "mission_save_replay_close",
                dict(id=state["lease"], session=state["session"]),
            )
    finally:
        dialogue_controls.clear_runtime_state()
        camera_tick.set_needed(PUMP, False)
