"""MSBT Third Person Camera — Boosting toggle over Renil's native TPC.

Vendors bl4_tpc (Renil; zip filename credits Epilow). Starts OFF. If the
standalone ``bl4_third_person_camera`` oak2 mod is already loaded, this wrapper
remote-controls that instance instead of installing a second AOB hook.

Remove the standalone zip from sdk_mods while using this toggle — double native
hooks can crash.
"""

from __future__ import annotations

import sys
import time
from typing import Any

from mods_base import EInputEvent, hook, keybind
from unrealsdk import logging
from unrealsdk.hooks import Type

__version__ = "0.1.0"
__version_info__ = (0, 1, 0)

_PREFIX = "[Matts SDK Boosting Tools | TPC]"

_want_enabled = False
_local_controller: Any = None
_hot_error_last_at: dict[str, float] = {}
_last_reapply_at = 0.0
_native_unavailable = False


def _log(msg: str) -> None:
    try:
        logging.info(f"{_PREFIX} {msg}")
    except Exception:
        print(f"{_PREFIX} {msg}")


def _log_hot_error(msg: str) -> None:
    now = time.monotonic()
    if now - _hot_error_last_at.get(msg, 0.0) < 5.0:
        return
    _hot_error_last_at[msg] = now
    _log(msg)


def _standalone_module() -> Any:
    return sys.modules.get("bl4_third_person_camera")


def _standalone_controller() -> Any:
    mod = _standalone_module()
    if mod is None:
        return None
    return getattr(mod, "controller", None)


def _hooks_installed(ctrl: Any) -> bool:
    if ctrl is None:
        return False
    update = getattr(ctrl, "update_hook", None)
    return bool(update is not None and getattr(update, "installed", False))


def _drop_local_if_standalone() -> None:
    global _local_controller
    if _local_controller is None or _standalone_controller() is None:
        return
    try:
        if hasattr(_local_controller, "suspend_hooks"):
            _local_controller.suspend_hooks()
        else:
            _local_controller.disable()
    except Exception as exc:
        _log_hot_error(f"local TPC unload failed: {exc!r}")
    _local_controller = None


def _controller() -> Any:
    global _local_controller
    _drop_local_if_standalone()
    stand = _standalone_controller()
    if stand is not None:
        return stand
    if _local_controller is None:
        from .bl4_tpc.controller import CameraController

        _local_controller = CameraController()
        _log("vendored TPC controller created (standalone zip not loaded)")
    return _local_controller


def _sync_want_from_standalone() -> None:
    global _want_enabled
    ctrl = _standalone_controller()
    if ctrl is None:
        return
    if _hooks_installed(ctrl):
        _want_enabled = True


def _request_third_person(ctrl: Any) -> None:
    """Keep asking Unreal for ThirdPerson even when native AOB hooks miss."""
    try:
        if hasattr(ctrl, "_refresh_runtime_refs"):
            ctrl._refresh_runtime_refs()
        if hasattr(ctrl, "_update_camera_mode_requests"):
            ctrl._update_camera_mode_requests()
    except Exception as exc:
        _log_hot_error(f"CameraTransition request failed: {exc!r}")


def _apply_on(ctrl: Any) -> str:
    global _native_unavailable
    third = getattr(ctrl, "third_person", None)
    ots = getattr(ctrl, "over_shoulder", None)
    if third is not None:
        third.value = True
    if ots is not None:
        ots.value = True
    ctrl.enable()
    _request_third_person(ctrl)
    if _hooks_installed(ctrl):
        _native_unavailable = False
        return "native hooks on"
    _native_unavailable = True
    return "native AOB miss; Unreal CameraTransition fallback"


def _apply_off(ctrl: Any) -> None:
    ctrl.disable()


def set_enabled(enabled: bool) -> str:
    global _want_enabled
    want = bool(enabled)
    _want_enabled = want
    source = "standalone" if _standalone_controller() is not None else "msbt"
    try:
        if not want:
            ctrl = _standalone_controller() or _local_controller
            if ctrl is not None:
                _apply_off(ctrl)
            sync_engine_hooks()
            msg = f"Third Person OFF ({source})"
            _log(msg)
            return msg
        ctrl = _controller()
        detail = _apply_on(ctrl)
        sync_engine_hooks()
        msg = f"Third Person ON ({source}, {detail})"
        if source == "standalone":
            msg += " — disable the standalone TPC zip to avoid double hooks"
        _log(msg)
        return msg
    except Exception as exc:
        _log(f"set_enabled({want}) failed: {exc!r}")
        return f"Third Person failed: {exc!r}"


def toggle_enabled() -> str:
    _sync_want_from_standalone()
    return set_enabled(not bool(_want_enabled))


def get_status_dict() -> dict[str, Any]:
    _sync_want_from_standalone()
    stand = _standalone_controller() is not None
    ctrl = _standalone_controller() or _local_controller
    hooks = _hooks_installed(ctrl) if ctrl is not None else False
    return {
        "enabled": bool(_want_enabled),
        "hooks": hooks,
        "source": "standalone" if stand else "msbt",
        "scope": "client_local",
        "mode": "native" if hooks else ("unreal" if _want_enabled else "off"),
        "caveat": (
            "Client-local camera. Remove the standalone BL4 Third Person Camera zip "
            "while this toggle is on — double native hooks can crash."
        ),
    }


def status_message() -> str:
    st = get_status_dict()
    return (
        f"Third Person enabled={st['enabled']} hooks={st['hooks']} "
        f"source={st['source']} (client-local)"
    )


def clear_travel_backups() -> None:
    """Uninstall native AOB/vtable hooks across world teardown."""
    ctrl = _standalone_controller() or _local_controller
    if ctrl is None:
        return
    try:
        if hasattr(ctrl, "suspend_hooks"):
            ctrl.suspend_hooks()
        else:
            ctrl.uninstall_post_render_hook()
            ctrl.uninstall_native_hooks()
            if hasattr(ctrl, "_clear_runtime_refs"):
                ctrl._clear_runtime_refs()
            if hasattr(ctrl, "_reset_runtime_state"):
                ctrl._reset_runtime_state()
    except Exception as exc:
        _log_hot_error(f"travel suspend failed: {exc!r}")


def reapply_if_wanted() -> None:
    global _last_reapply_at
    if not _want_enabled:
        return
    ctrl = _controller()
    if _hooks_installed(ctrl):
        return
    if _native_unavailable:
        _request_third_person(ctrl)
        return
    now = time.monotonic()
    if now - _last_reapply_at < 1.0:
        return
    _last_reapply_at = now
    try:
        detail = _apply_on(ctrl)
        _log(f"reapply {detail}")
    except Exception as exc:
        _log_hot_error(f"reapply failed: {exc!r}")


def _toggle_keybind() -> None:
    _log(toggle_enabled())


kb_toggle_third_person = keybind(
    "MSBT Toggle Third Person",
    None,
    callback=_toggle_keybind,
    display_name="MSBT Toggle Third Person",
    description=(
        "Toggle the client-local third-person / over-shoulder camera. "
        "Assign or clear this key in oak2's Mods keybind UI."
    ),
    event_filter=EInputEvent.IE_Pressed,
)

TPC_KEYBINDS = (kb_toggle_third_person,)


@hook(
    "OakGame.OakPlayerController:PlayerTick",
    Type.POST,
    immediately_enable=False,
    hook_identifier="msbt_tpc_ptick_oak_v1",
)
@hook(
    "Engine.PlayerController:PlayerTick",
    Type.POST,
    immediately_enable=False,
    hook_identifier="msbt_tpc_ptick_engine_v1",
)
def _player_tick(*_args: Any, **_kwargs: Any) -> None:
    if not _want_enabled:
        return
    reapply_if_wanted()
    ctrl = _standalone_controller() or _local_controller
    if ctrl is None:
        return
    if not _hooks_installed(ctrl):
        _request_third_person(ctrl)


def sync_engine_hooks() -> None:
    """Keep TPC PlayerTick registered only while On."""
    want = bool(_want_enabled)
    try:
        fn = getattr(_player_tick, "enable" if want else "disable", None)
        if callable(fn):
            fn()
    except Exception:
        pass


_log(f"loaded v{__version__} (MSBT helper, Third Person starts OFF; client-local)")
