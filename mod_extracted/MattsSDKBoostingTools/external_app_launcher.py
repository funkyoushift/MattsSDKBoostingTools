"""SDK console command for opening the standalone MSBT external app."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from mods_base import command

APP_FOLDER_NAME = "MattsSDKBoostingTools_external"
APP_ENTRY_NAMES = (
    "MattsBoostingToolsExternal.exe",
    "matts_external_app_v22.pyw",
    "matts_external_app_v22.py",
    "Launch_MattsBoostingTools_External.bat",
)
ENV_PATH_NAME = "MSBT_EXTERNAL_APP_PATH"

_external_app_process: subprocess.Popen[object] | None = None


def _log_info(message: str) -> None:
    _log("info", message)


def _log_warning(message: str) -> None:
    _log("warning", message)


def _log_error(message: str) -> None:
    _log("error", message)


def _log(level: str, message: str) -> None:
    text = f"[Matts SDK Boosting Tools] {message}"
    try:
        from unrealsdk import logging  # type: ignore

        log_fn = getattr(logging, level, None) or logging.info
        log_fn(text)
    except Exception:
        print(text)


def _candidate_entries_from_path(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    for name in APP_ENTRY_NAMES:
        yield path / name


def _sdk_mods_candidate_dirs() -> list[Path]:
    candidates: list[Path] = []
    here = Path(__file__).resolve()

    for parent in [here.parent, *here.parents]:
        if parent.name == APP_FOLDER_NAME:
            continue
        if parent.suffix.lower() == ".sdkmod":
            candidates.append(parent.parent / APP_FOLDER_NAME)
        candidates.append(parent / APP_FOLDER_NAME)

    return candidates


def _dedupe_paths(paths: Iterable[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def _resolve_external_app() -> tuple[Path | None, list[Path]]:
    searched_entries: list[Path] = []
    candidate_dirs: list[Path] = []

    env_raw = os.environ.get(ENV_PATH_NAME, "").strip().strip('"')
    if env_raw:
        env_path = Path(env_raw).expanduser()
        for entry in _candidate_entries_from_path(env_path):
            searched_entries.append(entry)
            if entry.is_file():
                return entry, _dedupe_paths(searched_entries)

    candidate_dirs.extend(_sdk_mods_candidate_dirs())

    for folder in _dedupe_paths(candidate_dirs):
        for entry in _candidate_entries_from_path(folder):
            searched_entries.append(entry)
            if entry.is_file():
                return entry, _dedupe_paths(searched_entries)

    return None, _dedupe_paths(searched_entries)


def _python_launcher(prefer_windowed: bool) -> str | None:
    names = (
        ("pyw.exe", "pyw", "pythonw.exe", "pythonw", "py.exe", "py", "python.exe", "python")
        if prefer_windowed
        else ("py.exe", "py", "python.exe", "python", "pyw.exe", "pyw", "pythonw.exe", "pythonw")
    )
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def _popen_target(target: Path) -> subprocess.Popen[object] | None:
    cwd = str(target.parent)
    suffix = target.suffix.lower()
    creationflags = 0
    if sys.platform == "win32":
        creationflags = (
            getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            | getattr(subprocess, "DETACHED_PROCESS", 0)
            | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        )

    if suffix == ".exe":
        return subprocess.Popen([str(target)], cwd=cwd, creationflags=creationflags)

    if suffix in {".py", ".pyw"}:
        launcher = _python_launcher(prefer_windowed=True)
        if launcher:
            return subprocess.Popen([launcher, "-B", str(target)], cwd=cwd, creationflags=creationflags)
        return None

    if suffix in {".bat", ".cmd"}:
        return subprocess.Popen([str(target)], cwd=cwd, creationflags=creationflags)

    return None


def _launch_external_app(target: Path) -> bool:
    global _external_app_process

    process = _popen_target(target)
    if process is not None:
        _external_app_process = process
        _log_info(f"External app launched: {target}")
        return True

    if sys.platform == "win32":
        try:
            os.startfile(str(target))  # type: ignore[attr-defined]
            _external_app_process = None
            _log_info(f"External app launched: {target}")
            return True
        except Exception as exc:
            _log_error(f"External app launch failed: {exc!r}")
            return False

    _log_error("External app launch failed: no Python launcher found.")
    return False


def _searched_paths_message(paths: list[Path]) -> str:
    if not paths:
        return "(no paths searched)"
    return "\n".join(f"  - {path}" for path in paths)


@command("msbt_external_app", description="Launch Matt's SDK Boosting Tools standalone external app.")
def _cmd_msbt_external_app(_) -> None:
    global _external_app_process

    if _external_app_process is not None and _external_app_process.poll() is None:
        _log_info("External app is already running from this game session.")
        return

    _external_app_process = None
    target, searched = _resolve_external_app()
    if target is None:
        _log_error(
            "External app not found. Place the MattsSDKBoostingTools_external folder next to "
            "MattsSDKBoostingTools.sdkmod in sdk_mods. Searched paths:\n"
            f"{_searched_paths_message(searched)}"
        )
        return

    try:
        _launch_external_app(target)
    except Exception as exc:
        _external_app_process = None
        _log_error(f"External app launch failed: {exc!r}")
