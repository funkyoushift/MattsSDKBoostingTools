from __future__ import annotations

import json
import mimetypes
import posixpath
import subprocess
import sys
import threading
import urllib.parse
from urllib import request as urlrequest
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from external_app_paths import BASE_DIR
from external_serial_tools import human_to_serial, serial_to_human


EDITOR_DIR = BASE_DIR / "matt_editor"
BRIDGE_URL = "http://127.0.0.1:49774"

NEXUS_FILE_MAP = {
    "inv0": "Nexus-Data-inv0.json",
    "inv4": "Nexus-Data-inv4.json",
    "inv6": "Nexus-Data-inv6.json",
    "inv_name_part0": "Nexus-Data-inv_name_part0.json",
    "inv_name_part4": "Nexus-Data-inv_name_part4.json",
    "inv_name_part6": "Nexus-Data-inv_name_part6.json",
    "inv_stat0": "Nexus-Data-inv_stat0.json",
    "inv_stat4": "Nexus-Data-inv_stat4.json",
    "inv_custom0": "Nexus-Data-inv_custom0.json",
    "inv_custom4": "Nexus-Data-inv_custom4.json",
    "ui_stat0": "Nexus-Data-ui_stat0.json",
    "ui_stat4": "Nexus-Data-ui_stat4.json",
    "ui_stat6": "Nexus-Data-ui_stat6.json",
    "attribute0": "Nexus-Data-attribute0.json",
    "attribute4": "Nexus-Data-attribute4.json",
    "attribute6": "Nexus-Data-attribute6.json",
    "gbx_ue_data_table0": "Nexus-Data-gbx_ue_data_table0.json",
    "gbx_ue_data_table4": "Nexus-Data-gbx_ue_data_table4.json",
    "gbx_ue_data_table6": "Nexus-Data-gbx_ue_data_table6.json",
    "itempool0": "Nexus-Data-itempool0.json",
    "itempool4": "Nexus-Data-itempool4.json",
    "itempool6": "Nexus-Data-itempool6.json",
    "itempoollist0": "Nexus-Data-ItemPoolList0.json",
    "itempoollist4": "Nexus-Data-ItemPoolList4.json",
    "itempoollist6": "Nexus-Data-ItemPoolList6.json",
    "skilltrees_data0": "Nexus-Data-skilltrees_data0.json",
    "skilltrees_data4": "Nexus-Data-skilltrees_data4.json",
    "skilltrees_data6": "Nexus-Data-skilltrees_data6.json",
    "uitooltipdata0": "Nexus-Data-uitooltipdata0.json",
    "uitooltipdata4": "Nexus-Data-uitooltipdata4.json",
    "uitooltipdata6": "Nexus-Data-uitooltipdata6.json",
    "resident0": "Nexus-Data-Resident0.json",
    "resident4": "Nexus-Data-Resident4.json",
    "resident6": "Nexus-Data-Resident6.json",
    "gbxactorpart0": "Nexus-Data-GbxActorPart0.json",
    "gbxactorpart4": "Nexus-Data-GbxActorPart4.json",
    "gbxactorpart6": "Nexus-Data-GbxActorPart6.json",
    "challenge0": "Nexus-Data-challenge0.json",
    "challenge4": "Nexus-Data-challenge4.json",
    "challenge6": "Nexus-Data-challenge6.json",
    "challenge_list4": "Nexus-Data-challenge_list4.json",
    "challenge_list6": "Nexus-Data-challenge_list6.json",
    "gbx_discovery_location_meta_data4": "Nexus-Data-gbx_discovery_location_meta_data4.json",
    "gbx_discovery_location_meta_data6": "Nexus-Data-gbx_discovery_location_meta_data6.json",
    "mission0": "Nexus-Data-Mission0.json",
    "mission4": "Nexus-Data-Mission4.json",
    "mission6": "Nexus-Data-Mission6.json",
    "missionset0": "Nexus-Data-missionset0.json",
    "missionset4": "Nexus-Data-missionset4.json",
    "missionset6": "Nexus-Data-missionset6.json",
    "game_region0": "Nexus-Data-game_region0.json",
    "game_region4": "Nexus-Data-game_region4.json",
    "game_region6": "Nexus-Data-game_region6.json",
    "progress_graph_group0": "Nexus-Data-progress_graph_group0.json",
    "progress_graph_group4": "Nexus-Data-progress_graph_group4.json",
    "progress_graph_group6": "Nexus-Data-progress_graph_group6.json",
    "progress_graph0": "Nexus-Data-progress_graph0.json",
    "progress_graph4": "Nexus-Data-progress_graph4.json",
    "progress_graph6": "Nexus-Data-progress_graph6.json",
}


def _clean_deserialized(data: object) -> str:
    text = str(data or "").strip()
    if text and not text.endswith("|"):
        text += "|"
    while len(text) >= 2 and text[-1] == "|" and text[-2] == "|":
        text = text[:-1]
    return text


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def _bridge_json(method: str, path: str, data: object | None = None, timeout: float = 18.0) -> object:
    body = None
    headers = {"Content-Type": "application/json"}
    if data is not None:
        body = _json_bytes(data)
    req = urlrequest.Request(BRIDGE_URL + path, data=body, headers=headers, method=method)
    with urlrequest.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return json.loads(raw or "{}")


def _editor_bootstrap(origin: str) -> str:
    return f"""
<script>
(function() {{
    window.MSBT_MATT_EDITOR_MODE = true;
    window.IS_ELECTRON_APP = true;
    window.ELECTRON_API_URL = {json.dumps(origin)};
    window.getLocalApiUrl = function() {{ return {json.dumps(origin + "/api.php")}; }};
    window.SAVE_DESERIALIZE_API_BASE_URL = {json.dumps(origin + "/api.php")};
    window.SAVE_DESERIALIZE_API_FALLBACK_URL = {json.dumps(origin + "/api.php")};
    window.SERIALIZE_API_BASE_URL = {json.dumps(origin + "/api.php")};
    window.SERIALIZE_API_FALLBACK_URL = {json.dumps(origin + "/api.php")};
    window.SAVE_API_BASE_URL = {json.dumps(origin + "/blcrypt/api.php")};
    var originalFetch = window.fetch.bind(window);
    window.fetch = function(input, init) {{
        var url = (typeof input === "string") ? input : (input && input.url) || "";
        if (url.indexOf("nexus_data_proxy.php") >= 0) {{
            var query = url.indexOf("?") >= 0 ? url.slice(url.indexOf("?")) : "";
            url = {json.dumps(origin + "/LegitItems/nexus_data_proxy.php")} + query;
        }} else if (
            url.indexOf("save-editor.be/nicnl/api.php") >= 0 ||
            url.indexOf("borderlands.be/nicnl/api.php") >= 0 ||
            url.indexOf("borderlands4-deserializer.nicnl.com") >= 0 ||
            (url.indexOf("/api.php") >= 0 && url.indexOf("/blcrypt/") < 0)
        ) {{
            url = {json.dumps(origin + "/api.php")};
        }} else if (
            url.indexOf("/blcrypt/api.php") >= 0 ||
            url.indexOf("borderlands.be/blcrypt") >= 0 ||
            url.indexOf("save-editor.be/blcrypt") >= 0 ||
            url.indexOf("blcrypt/api.php") >= 0
        ) {{
            url = {json.dumps(origin + "/blcrypt/api.php")};
        }}
        if (typeof input === "string") {{
            return originalFetch(url, init);
        }}
        return originalFetch(new Request(url, input), init);
    }};
}})();
</script>
"""


class _MattEditorHandler(BaseHTTPRequestHandler):
    server_version = "MSBTMattEditor/1.0"

    def log_message(self, _fmt: str, *_args: object) -> None:
        return

    def _origin(self) -> str:
        host, port = self.server.server_address[:2]
        return f"http://{host}:{port}"

    def _send(self, status: int, body: bytes, content_type: str = "application/json; charset=UTF-8") -> None:
        self.send_response(status)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, value: object) -> None:
        self._send(status, _json_bytes(value))

    def do_OPTIONS(self) -> None:
        self._send(204, b"")

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path or "/"
        if path == "/msbt/status":
            self._handle_msbt_status()
            return
        if self._is_nexus_proxy_path(path):
            self._handle_nexus_proxy(parsed)
            return
        if path in ("/", "/index.html"):
            self._serve_index()
            return
        self._serve_static(path)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path or "/"
        if path in ("/api.php", "/nicnl/api.php", "/api2.php", "/nicnl/api2.php"):
            self._handle_api()
            return
        if path == "/msbt/deliver":
            self._handle_msbt_deliver()
            return
        if path == "/msbt/target":
            self._handle_msbt_target()
            return
        if path == "/blcrypt/api.php" or path.endswith("/blcrypt/api.php"):
            self._send_json(501, {"error": "Save encryption is not enabled in the MSBT local editor host yet."})
            return
        self._send_json(404, {"error": "Not found"})

    def _is_nexus_proxy_path(self, path: str) -> bool:
        clean = path.replace("\\", "/").lower()
        return clean.endswith("/legititems/nexus_data_proxy.php") or clean.endswith("/nexus_data_proxy.php")

    def _handle_nexus_proxy(self, parsed: urllib.parse.ParseResult) -> None:
        params = urllib.parse.parse_qs(parsed.query or "")
        key = (params.get("file") or [""])[0]
        filename = NEXUS_FILE_MAP.get(key)
        if not filename:
            self._send_json(404, {"error": f"Unknown file key: {key}"})
            return
        file_path = EDITOR_DIR / "LegitItems" / filename
        if not file_path.exists():
            self._send_json(404, {"error": f"Missing local LegitItems file: {filename}"})
            return
        self._send(200, file_path.read_bytes(), "application/json; charset=UTF-8")

    def _serve_index(self) -> None:
        index_path = EDITOR_DIR / "index.html"
        if not index_path.exists():
            self._send_json(404, {"error": f"Matt editor assets not found at {EDITOR_DIR}"})
            return
        html = index_path.read_text(encoding="utf-8", errors="replace")
        bootstrap = _editor_bootstrap(self._origin())
        if "</head>" in html:
            html = html.replace("</head>", bootstrap + "\n</head>", 1)
        else:
            html = bootstrap + html
        if "</body>" in html:
            html = html.replace("</body>", '<script src="/matt_editor_adapter.js"></script>\n</body>', 1)
        self._send(200, html.encode("utf-8"), "text/html; charset=UTF-8")

    def _serve_static(self, path: str) -> None:
        if path == "/matt_editor_adapter.js":
            file_path = BASE_DIR / "matt_editor_adapter.js"
        else:
            normalized = posixpath.normpath(urllib.parse.unquote(path)).lstrip("/")
            if normalized.startswith("../"):
                self._send_json(403, {"error": "Forbidden"})
                return
            file_path = (EDITOR_DIR / normalized).resolve()
            try:
                file_path.relative_to(EDITOR_DIR.resolve())
            except ValueError:
                self._send_json(403, {"error": "Forbidden"})
                return
        if not file_path.exists() or not file_path.is_file():
            self._send_json(404, {"error": "Not found"})
            return
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        if file_path.suffix.lower() == ".js":
            content_type = "application/javascript; charset=UTF-8"
        elif file_path.suffix.lower() == ".css":
            content_type = "text/css; charset=UTF-8"
        self._send(200, file_path.read_bytes(), content_type)

    def _handle_api(self) -> None:
        try:
            length = int(self.headers.get("Content-Length") or "0")
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            data = json.loads(raw or "{}")
        except Exception as exc:
            self._send_json(400, {"error": f"Invalid JSON: {exc}"})
            return

        try:
            if isinstance(data.get("serials"), list):
                results = {}
                for serial in data["serials"]:
                    serial_text = str(serial or "").strip()
                    try:
                        results[serial_text] = {
                            "success": True,
                            "deserialized": serial_to_human(serial_text),
                        }
                    except Exception as exc:
                        results[serial_text] = {"success": False, "error": str(exc)}
                results["_metadata"] = {"total_input": len(data["serials"]), "processed": len(data["serials"])}
                self._send_json(200, {"results": results})
                return

            if isinstance(data.get("deserialized_strings"), list):
                output = []
                for human in data["deserialized_strings"]:
                    try:
                        output.append(human_to_serial(_clean_deserialized(human)))
                    except Exception:
                        output.append("")
                self._send_json(200, output)
                return

            if data.get("serial_b85"):
                human = serial_to_human(str(data.get("serial_b85") or "").strip())
                self._send_json(200, {"deserialized": human, "bitstream": ""})
                return

            if data.get("deserialized"):
                serial = human_to_serial(_clean_deserialized(data.get("deserialized")))
                self._send_json(200, {"serial_b85": serial})
                return
        except Exception as exc:
            self._send_json(400, {"error": str(exc)})
            return

        self._send_json(400, {"error": "Invalid request format"})

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        data = json.loads(raw or "{}")
        return data if isinstance(data, dict) else {}

    def _handle_msbt_status(self) -> None:
        try:
            status = _bridge_json("GET", "/status", timeout=5.0)
        except Exception as exc:
            self._send_json(503, {"ok": False, "message": f"SDK bridge offline: {exc}"})
            return
        self._send_json(200, {"ok": True, "status": status})

    def _set_bridge_target(self, target_player: str) -> dict:
        result = _bridge_json(
            "POST",
            "/action",
            {"action": "set_target_player", "payload": {"target_player": target_player}, "timeout": 10.0},
            timeout=10.0,
        )
        return result if isinstance(result, dict) else {"ok": True, "message": str(result)}

    def _handle_msbt_target(self) -> None:
        try:
            data = self._read_json_body()
        except Exception as exc:
            self._send_json(400, {"ok": False, "message": f"Invalid JSON: {exc}"})
            return

        target_player = str(data.get("target_player") or data.get("target") or "").strip()
        if not target_player:
            self._send_json(400, {"ok": False, "message": "Select a target player first."})
            return

        try:
            result = self._set_bridge_target(target_player)
            if result.get("ok"):
                try:
                    status = _bridge_json("GET", "/status", timeout=5.0)
                    if isinstance(status, dict):
                        result["status"] = status
                except Exception:
                    pass
        except Exception as exc:
            self._send_json(503, {"ok": False, "message": f"Target update failed: {exc}"})
            return

        self._send_json(200 if result.get("ok") else 400, result)

    def _handle_msbt_deliver(self) -> None:
        try:
            data = self._read_json_body()
        except Exception as exc:
            self._send_json(400, {"ok": False, "message": f"Invalid JSON: {exc}"})
            return

        mode = str(data.get("mode") or "selected").strip().lower()
        action = {
            "selected": "give_serial_selected",
            "all": "give_serial_all",
            "nonhost": "give_serial_nonhost",
        }.get(mode)
        if not action:
            self._send_json(400, {"ok": False, "message": f"Unknown delivery mode: {mode}"})
            return

        serial = str(data.get("serial") or "").strip()
        if "\n" in serial or "\r" in serial or serial.count("@U") != 1 or not serial.startswith("@U"):
            self._send_json(400, {"ok": False, "message": "No single confirmed @U serial was received from the Mattmab editor."})
            return

        if mode == "selected":
            target_player = str(data.get("target_player") or data.get("target") or "").strip()
            if not target_player:
                self._send_json(400, {"ok": False, "message": "Select a target player first."})
                return
            try:
                target_result = self._set_bridge_target(target_player)
            except Exception as exc:
                self._send_json(503, {"ok": False, "message": f"Target update failed: {exc}"})
                return
            if not target_result.get("ok"):
                self._send_json(400, target_result)
                return

        try:
            level = int(str(data.get("level") or "60").replace(",", "").strip())
        except Exception:
            level = 60
        level = max(1, min(60, level))
        payload = {"serial_text": serial, "serial_override_level": False, "serial_level": level}
        try:
            result = _bridge_json("POST", "/action", {"action": action, "payload": payload, "timeout": 10.0}, timeout=30.0)
        except Exception as exc:
            self._send_json(503, {"ok": False, "message": f"Delivery failed: {exc}"})
            return
        if isinstance(result, dict):
            self._send_json(200, result)
        else:
            self._send_json(200, {"ok": True, "message": str(result)})


class MattEditorHost:
    def __init__(self) -> None:
        self._server: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None
        self._webview_process: subprocess.Popen | None = None
        self.url = ""

    def start(self) -> str:
        if self._server and self._thread and self._thread.is_alive():
            return self.url
        if not (EDITOR_DIR / "index.html").exists():
            raise FileNotFoundError(f"Matt editor assets not found at {EDITOR_DIR}")
        self._server = ThreadingHTTPServer(("127.0.0.1", 0), _MattEditorHandler)
        host, port = self._server.server_address[:2]
        self.url = f"http://{host}:{port}/"
        self._thread = threading.Thread(target=self._server.serve_forever, name="MSBTMattEditorHost", daemon=True)
        self._thread.start()
        return self.url

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._server.server_close()
        self._server = None
        self._thread = None
        self.url = ""

    def open(self) -> str:
        url = self.start()
        webbrowser.open(url, new=2)
        return url

    def open_embedded(self) -> tuple[str, bool, str]:
        url = self.start()
        try:
            import webview  # type: ignore
        except Exception as exc:
            webbrowser.open(url, new=2)
            return url, False, f"Embedded WebView is not available; opened in browser instead. {exc}"

        if self._webview_process and self._webview_process.poll() is None:
            return url, True, "Mattmab item editor WebView is already open."

        if getattr(sys, "frozen", False):
            cmd = [sys.executable, "--msbt-matt-editor-webview", url]
        else:
            app_entry = BASE_DIR / "matts_external_app_v22.py"
            cmd = [sys.executable, str(app_entry), "--msbt-matt-editor-webview", url]

        try:
            self._webview_process = subprocess.Popen(
                cmd,
                cwd=str(BASE_DIR),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        except Exception as exc:
            webbrowser.open(url, new=2)
            return url, False, f"Embedded WebView failed to launch; opened in browser instead. {exc}"
        return url, True, "Mattmab item editor opened in a native WebView window owned by the external app."


def run_webview_window(url: str) -> int:
    try:
        import webview  # type: ignore
        webview.create_window("Mattmab Item Editor - MSBT", url, width=1600, height=920)
        webview.start()
        return 0
    except Exception:
        webbrowser.open(url, new=2)
        return 1


_HOST = MattEditorHost()


def start_editor_host() -> str:
    return _HOST.start()


def stop_editor_host() -> None:
    _HOST.stop()


def open_editor() -> str:
    return _HOST.open()


def open_editor_embedded() -> tuple[str, bool, str]:
    return _HOST.open_embedded()
