"""Vendored BL4 Third Person Camera controller (Renil; zip credits Epilow).

MSBT owns enable/disable via Boosting toggle. Do not call build_mod() here —
a second oak2 mod plus this copy would double-install native AOB hooks.
"""
from __future__ import annotations

import ctypes
import math
import time
import traceback
from dataclasses import dataclass

from mods_base import (
    BoolOption,
    Game,
    GroupedOption,
    SliderOption,
    get_pc,
)
from unrealsdk import find_enum, logging, make_struct
from unrealsdk.unreal import WeakPointer

from .native import (
    InlineHook,
    Pose,
    VTableHook,
    read_int32,
    aob_scan,
    read_pointer,
    scan_diagnostics,
    read_double,
    read_float,
    write_pointer,
    write_double,
    write_float,
)

if True:
    assert __import__("mods_base").__version_info__ >= (1, 11), "Please update mods_base"
    assert __import__("unrealsdk").__version_info__ >= (1, 3, 0), "Please update unrealsdk"
    assert Game.get_current() == Game.BL4, "This mod only supports Borderlands 4"

__author__ = "Renil"
__version__ = "0.1.0"

NATIVE_CAMERA_UPDATE_SIG = (
    "41 57 41 56 41 54 56 57 53 48 81 EC ? ? ? ? 66 44 0F 29 BC 24 ? ? ? ? "
    "66 44 0F 29 B4 24 ? ? ? ? 66 44 0F 29 AC 24 ? ? ? ? 66 44 0F 29 A4 24 ? ? ? ? "
    "66 44 0F 29 9C 24 ? ? ? ? 66 44 0F 29 94 24 ? ? ? ? 66 44 0F 29 8C 24 ? ? ? ? "
    "66 44 0F 29 84 24 ? ? ? ? 66 0F 29 BC 24 ? ? ? ? 0F 29 B4 24 ? ? ? ? 66 0F 28 F2"
)
NATIVE_CAMERA_MODE_COMMIT_SIG = "41 57 41 56 41 54 56 57 55 53 48 83 EC 50 0F 29 74 24 40 0F 28 F3 4C 89 C7 49 89 ? 48 89 CE"
NATIVE_CAMERA_HOOK_LEN = 26
NATIVE_CAMERA_MODE_HOOK_LEN = 19

CURRENT_CACHE_LOC_OFFSET = 1088
CURRENT_CACHE_ROT_OFFSET = 1112
CURRENT_CACHE_FOV_OFFSET = 1136
LAST_FRAME_CACHE_LOC_OFFSET = 12032
LAST_FRAME_CACHE_ROT_OFFSET = 12056
LAST_FRAME_CACHE_FOV_OFFSET = 12080
VIEWTARGET_LOC_OFFSET = 14640
VIEWTARGET_ROT_OFFSET = 14664
VIEWTARGET_FOV_OFFSET = 14688
HUD_CANVAS_OFFSET = 0x3E0
HUD_DEBUG_CANVAS_OFFSET = 0x3E8
CANVAS_ORG_X_OFFSET = 0x28
CANVAS_ORG_Y_OFFSET = 0x2C
CANVAS_CLIP_X_OFFSET = 0x30
CANVAS_CLIP_Y_OFFSET = 0x34
CANVAS_SIZE_X_OFFSET = 0x40
CANVAS_SIZE_Y_OFFSET = 0x44

OTS_MAX_WORLD_COORD = 2_000_000.0
CAMERA_TRANSITION_MIN_INTERVAL = 0.05
VIEWPORT_POST_RENDER_VTABLE_INDEX = 0x6D

try:
    VT_BLEND_LINEAR = find_enum("EViewTargetBlendFunction").VTBlend_Linear
except Exception:
    VT_BLEND_LINEAR = 0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _enum_name(value: object) -> str:
    if value is None:
        return ""
    if hasattr(value, "name"):
        return str(getattr(value, "name"))
    return str(value)


def _normalize_enum_name(value: object) -> str:
    name = _enum_name(value).strip()
    if "::" in name:
        name = name.rsplit("::", 1)[-1]
    if "." in name:
        name = name.rsplit(".", 1)[-1]
    return name


def _now() -> float:
    return time.monotonic()


@dataclass(slots=True)
class NativeOtsState:
    should_apply: bool = False
    offset_x: float = 0.0
    offset_y: float = 0.0
    offset_z: float = 0.0
    target_fov: float = 90.0


class CameraController:
    def __init__(self) -> None:
        self.third_person = BoolOption("third_person", True, display_name="Third Person")
        self.over_shoulder = BoolOption("over_shoulder", True, display_name="Over Shoulder")
        self.right_shoulder = BoolOption("right_shoulder", True, display_name="Right Shoulder")
        self.enable_fov = BoolOption("enable_fov", False, display_name="Enable FOV")
        self.fov = SliderOption("fov", 100.0, 60.0, 180.0, step=1.0, is_integer=False, display_name="FOV")
        self.ads_fov_scale = SliderOption(
            "ads_fov_scale",
            0.7,
            0.2,
            1.0,
            step=0.01,
            is_integer=False,
            display_name="ADS FOV Scale",
        )
        self.enable_viewmodel_fov = BoolOption("enable_viewmodel_fov", False, display_name="Enable ViewModel FOV")
        self.viewmodel_fov = SliderOption(
            "viewmodel_fov",
            90.0,
            60.0,
            150.0,
            step=1.0,
            is_integer=False,
            display_name="ViewModel FOV",
        )
        self.third_person_ads_first_person = BoolOption(
            "third_person_ads_first_person",
            True,
            display_name="ADS Uses First Person",
        )
        self.ots_x = SliderOption("ots_x", -150.0, -500.0, 500.0, step=1.0, is_integer=False, display_name="OTS Offset X")
        self.ots_y = SliderOption("ots_y", 60.0, -200.0, 200.0, step=1.0, is_integer=False, display_name="OTS Offset Y")
        self.ots_z = SliderOption("ots_z", 50.0, -200.0, 200.0, step=1.0, is_integer=False, display_name="OTS Offset Z")
        self.ots_ads_override = BoolOption("ots_ads_override", True, display_name="OTS ADS Override")
        self.ots_ads_first_person = BoolOption("ots_ads_first_person", False, display_name="OTS ADS First Person")
        self.ots_ads_x = SliderOption("ots_ads_x", -120.0, -500.0, 500.0, step=1.0, is_integer=False, display_name="OTS ADS X")
        self.ots_ads_y = SliderOption("ots_ads_y", 60.0, -200.0, 200.0, step=1.0, is_integer=False, display_name="OTS ADS Y")
        self.ots_ads_z = SliderOption("ots_ads_z", 50.0, -200.0, 200.0, step=1.0, is_integer=False, display_name="OTS ADS Z")
        self.ots_ads_fov = SliderOption("ots_ads_fov", 80.0, 20.0, 180.0, step=1.0, is_integer=False, display_name="OTS ADS FOV")
        self.ots_ads_blend_time = SliderOption(
            "ots_ads_blend_time",
            0.10,
            0.01,
            1.0,
            step=0.01,
            is_integer=False,
            display_name="OTS ADS Blend Time",
        )
        self.third_person_ads_crosshair = BoolOption(
            "third_person_ads_crosshair",
            True,
            display_name="Third Person ADS Crosshair",
        )
        self.crosshair_size = SliderOption(
            "crosshair_size",
            8.0,
            2.0,
            32.0,
            step=1.0,
            is_integer=False,
            display_name="Crosshair Size",
        )
        self.crosshair_thickness = SliderOption(
            "crosshair_thickness",
            2.0,
            1.0,
            8.0,
            step=1.0,
            is_integer=False,
            display_name="Crosshair Thickness",
        )

        @self.over_shoulder
        def _over_shoulder_changed(_: BoolOption, value: bool) -> None:
            if value:
                self.third_person.value = True

        self.smoothed_ots_ads_blend = 0.0
        self.native_ots_blend_alpha = 0.0
        self.last_transition_time = 0.0
        self.last_desired_third_person = False
        self.last_zooming = False
        self.requested_first_person = False
        self.requested_third_person = False
        self.override_temporarily_blocked = False
        self.commit_hook_suspended_for_block = False
        self.update_hook: InlineHook | None = None
        self.commit_hook: InlineHook | None = None
        self.update_callback = None
        self.commit_callback = None
        self.update_original = None
        self.commit_original = None
        self.pc_ref: WeakPointer | None = None
        self.character_ref: WeakPointer | None = None
        self.camera_manager_ref: WeakPointer | None = None
        self.post_render_hook: VTableHook | None = None
        self.post_render_callback = None
        self.post_render_original = None
        self.post_render_vtable_entry = 0
        self.last_post_render_validate_time = 0.0

    def options(self) -> list[object]:
        camera_core = GroupedOption(
            "Camera",
            [
                self.third_person,
                self.over_shoulder,
                self.right_shoulder,
                self.third_person_ads_first_person,
                self.enable_fov,
                self.fov,
                self.ads_fov_scale,
                self.enable_viewmodel_fov,
                self.viewmodel_fov,
                self.third_person_ads_crosshair,
                self.crosshair_size,
                self.crosshair_thickness,
            ],
        )
        ots = GroupedOption(
            "Over Shoulder",
            [
                self.ots_x,
                self.ots_y,
                self.ots_z,
                self.ots_ads_override,
                self.ots_ads_first_person,
                self.ots_ads_x,
                self.ots_ads_y,
                self.ots_ads_z,
                self.ots_ads_fov,
                self.ots_ads_blend_time,
            ],
        )
        return [camera_core, ots]

    def enable(self) -> None:
        self._refresh_runtime_refs()
        self.install_native_hooks()
        self.install_post_render_hook()

    def disable(self) -> None:
        self.third_person.value = False
        self.over_shoulder.value = False
        self.requested_first_person = False
        self.requested_third_person = False
        self.uninstall_post_render_hook()
        self.uninstall_native_hooks()
        self._best_effort_force_first_person()
        self._clear_runtime_refs()
        self._reset_runtime_state()

    def suspend_hooks(self) -> None:
        """Travel teardown: drop native hooks without flipping camera options."""
        self.uninstall_post_render_hook()
        self.uninstall_native_hooks()
        self._clear_runtime_refs()
        self._reset_runtime_state()

    def _reset_runtime_state(self) -> None:
        self.smoothed_ots_ads_blend = 0.0
        self.native_ots_blend_alpha = 0.0
        self.last_desired_third_person = False
        self.last_zooming = False
        self.requested_first_person = False
        self.requested_third_person = False
        self.override_temporarily_blocked = False
        self.commit_hook_suspended_for_block = False

    def _refresh_runtime_refs(self) -> None:
        pc = get_pc(possibly_loading=True)
        self.pc_ref = WeakPointer(pc) if pc is not None else None

        character = None
        camera_manager = None
        if pc is not None:
            for name in ("Pawn", "AcknowledgedPawn"):
                try:
                    candidate = getattr(pc, name)
                    if candidate is not None:
                        character = candidate
                        break
                except Exception:
                    continue
            try:
                camera_manager = pc.PlayerCameraManager
            except Exception:
                camera_manager = None

        self.character_ref = WeakPointer(character) if character is not None else None
        self.camera_manager_ref = WeakPointer(camera_manager) if camera_manager is not None else None

    def _clear_runtime_refs(self) -> None:
        self.pc_ref = None
        self.character_ref = None
        self.camera_manager_ref = None

    def install_post_render_hook(self) -> None:
        if self.post_render_hook is not None and self.post_render_hook.installed:
            return
        viewport_client = self._get_viewport_client()
        if viewport_client is None:
            logging.warning("[BL4 Third Person Camera] PostRender hook skipped: viewport client unavailable")
            return

        try:
            viewport_addr = int(viewport_client._get_address())
        except Exception:
            viewport_addr = 0
        if viewport_addr < 0x10000:
            logging.warning("[BL4 Third Person Camera] PostRender hook skipped: invalid viewport client address")
            return

        vtable_ptr = read_pointer(viewport_addr)
        if not vtable_ptr:
            logging.warning("[BL4 Third Person Camera] PostRender hook skipped: viewport client vtable unavailable")
            return

        entry_addr = vtable_ptr + (VIEWPORT_POST_RENDER_VTABLE_INDEX * ctypes.sizeof(ctypes.c_void_p))
        original = read_pointer(entry_addr)
        if not original:
            logging.warning("[BL4 Third Person Camera] PostRender hook skipped: original PostRender entry unavailable")
            return

        callback_type = ctypes.WINFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)

        def post_render_callback(viewport_this: int, canvas_ptr: int) -> None:
            try:
                if self.post_render_original is not None:
                    self.post_render_original(viewport_this, canvas_ptr)
                self._on_post_render(viewport_this, canvas_ptr)
            except Exception:
                logging.dev_warning("[BL4 Third Person Camera] PostRender callback failed")
                logging.dev_warning(traceback.format_exc())
                if self.post_render_original is not None:
                    try:
                        self.post_render_original(viewport_this, canvas_ptr)
                    except Exception:
                        pass

        self.post_render_callback = callback_type(post_render_callback)
        self.post_render_hook = VTableHook(entry_addr, ctypes.cast(self.post_render_callback, ctypes.c_void_p).value)
        if not self.post_render_hook.install():
            self.post_render_hook = None
            self.post_render_callback = None
            logging.warning("[BL4 Third Person Camera] PostRender hook install failed")
            return

        self.post_render_original = callback_type(original)
        self.post_render_vtable_entry = entry_addr
        logging.warning(
            "[BL4 Third Person Camera] PostRender hook installed "
            f"viewport=0x{viewport_addr:X} vtable_entry=0x{entry_addr:X} original=0x{original:X}"
        )

    def uninstall_post_render_hook(self) -> None:
        if self.post_render_hook is not None:
            self.post_render_hook.uninstall()
        self.post_render_hook = None
        self.post_render_callback = None
        self.post_render_original = None
        self.post_render_vtable_entry = 0

    def _get_post_render_callback_ptr(self) -> int:
        if self.post_render_callback is None:
            return 0
        try:
            return int(ctypes.cast(self.post_render_callback, ctypes.c_void_p).value or 0)
        except Exception:
            return 0

    def _ensure_post_render_hook(self) -> None:
        current_time = _now()
        if current_time - self.last_post_render_validate_time < 1.0:
            return
        self.last_post_render_validate_time = current_time

        callback_ptr = self._get_post_render_callback_ptr()
        if self.post_render_vtable_entry and callback_ptr:
            current_ptr = read_pointer(self.post_render_vtable_entry) or 0
            if current_ptr == callback_ptr:
                return
            logging.warning(
                "[BL4 Third Person Camera] PostRender hook lost, reinstalling "
                f"current=0x{current_ptr:X} expected=0x{callback_ptr:X}"
            )
            self.uninstall_post_render_hook()

        if self.third_person.value or self.over_shoulder.value:
            self.install_post_render_hook()

    def install_native_hooks(self) -> None:
        if self.update_hook and self.update_hook.installed and self.commit_hook and self.commit_hook.installed:
            return

        update_target = aob_scan(NATIVE_CAMERA_UPDATE_SIG)
        commit_target = aob_scan(NATIVE_CAMERA_MODE_COMMIT_SIG)
        if update_target is None or commit_target is None:
            update_diag = scan_diagnostics(NATIVE_CAMERA_UPDATE_SIG)
            commit_diag = scan_diagnostics(NATIVE_CAMERA_MODE_COMMIT_SIG)
            logging.error(
                "[BL4 Third Person Camera] AOB scan failed "
                f"update={update_target} commit={commit_target} "
                f"module_base=0x{int(update_diag['module_base']):X} "
                f"module_size=0x{int(update_diag['module_size']):X}"
            )
            return

        update_cb_type = ctypes.WINFUNCTYPE(ctypes.c_longlong, ctypes.c_longlong, ctypes.c_longlong, ctypes.c_float)
        commit_cb_type = ctypes.WINFUNCTYPE(
            ctypes.c_longlong,
            ctypes.c_longlong,
            ctypes.c_longlong,
            ctypes.c_longlong,
            ctypes.c_float,
            ctypes.c_int,
            ctypes.c_ubyte,
        )

        def update_callback(camera_ctx: int, arg2: int, delta: float) -> int:
            try:
                self._ensure_post_render_hook()
                override_blocked = self._is_camera_override_blocked()
                self._set_commit_hook_suspended_for_block(override_blocked)
                self._update_camera_mode_requests()
                result = self.update_original(camera_ctx, arg2, delta) if self.update_original else 0
                if not override_blocked:
                    self._apply_native_post_update(camera_ctx, float(delta))
                return int(result)
            except Exception:
                logging.error("[BL4 Third Person Camera] NativeCameraUpdate callback failed")
                logging.dev_warning(traceback.format_exc())
                return self.update_original(camera_ctx, arg2, delta) if self.update_original else 0

        def commit_callback(a1: int, mode_ptr: int, transition_ptr: int, a4: int, a5: int, a6: int) -> int:
            try:
                if mode_ptr and (not self._is_camera_override_blocked()) and self._should_hold_third_person():
                    return 0
                return int(self.commit_original(a1, mode_ptr, transition_ptr, a4, a5, a6)) if self.commit_original else 0
            except Exception:
                return int(self.commit_original(a1, mode_ptr, transition_ptr, a4, a5, a6)) if self.commit_original else 0

        self.update_callback = update_cb_type(update_callback)
        self.commit_callback = commit_cb_type(commit_callback)
        self.update_hook = InlineHook(update_target, ctypes.cast(self.update_callback, ctypes.c_void_p).value, NATIVE_CAMERA_HOOK_LEN)
        self.commit_hook = InlineHook(commit_target, ctypes.cast(self.commit_callback, ctypes.c_void_p).value, NATIVE_CAMERA_MODE_HOOK_LEN)

        if not self.update_hook.install():
            self.update_hook = None
            return
        if not self.commit_hook.install():
            self.update_hook.uninstall()
            self.update_hook = None
            self.commit_hook = None
            return

        self.update_original = self.update_hook.original_function(ctypes.c_longlong, ctypes.c_longlong, ctypes.c_longlong, ctypes.c_float)
        self._refresh_commit_original()

    def _refresh_commit_original(self) -> None:
        if self.commit_hook is None or not self.commit_hook.trampoline:
            self.commit_original = None
            return
        self.commit_original = self.commit_hook.original_function(
            ctypes.c_longlong,
            ctypes.c_longlong,
            ctypes.c_longlong,
            ctypes.c_longlong,
            ctypes.c_float,
            ctypes.c_int,
            ctypes.c_ubyte,
        )

    def uninstall_native_hooks(self) -> None:
        if self.commit_hook:
            self.commit_hook.uninstall()
        if self.update_hook:
            self.update_hook.uninstall()
        self.commit_hook = None
        self.update_hook = None
        self.update_original = None
        self.commit_original = None
        self.commit_hook_suspended_for_block = False

    def _set_commit_hook_suspended_for_block(self, should_suspend: bool) -> None:
        if self.commit_hook is None:
            self.commit_hook_suspended_for_block = False
            return

        if should_suspend:
            if self.commit_hook.installed:
                self.commit_hook.uninstall()
                self.commit_original = None
            self.commit_hook_suspended_for_block = True
            return

        if not self.commit_hook_suspended_for_block:
            return

        if self.commit_hook.install():
            self._refresh_commit_original()
            self.commit_hook_suspended_for_block = False
        else:
            self.commit_original = None

    def _wrapped_camera_transition(self, pc, new_mode: str, transition: str = "Default", blend_time: float = 0.15, arg4: bool = False, arg5: bool = False) -> None:
        was_installed = False
        if self.commit_hook is not None and self.commit_hook.installed:
            self.commit_hook.uninstall()
            self.commit_original = None
            was_installed = True

        try:
            pc.CameraTransition(new_mode, transition, blend_time, arg4, arg5)
        except Exception:
            pass
        finally:
            if was_installed and self.commit_hook is not None:
                if self.commit_hook.install():
                    self._refresh_commit_original()
                else:
                    self.commit_original = None

    def _best_effort_force_first_person(self) -> None:
        pc = self._get_pc()
        if pc is None:
            return
        self._wrapped_camera_transition(pc, "FirstPerson", "Default", 0.15, False, False)

    def _get_pc(self):
        if self.pc_ref is not None:
            pc = self.pc_ref()
            if pc is not None:
                return pc
        self._refresh_runtime_refs()
        return self.pc_ref() if self.pc_ref is not None else None

    def _get_character(self):
        if self.character_ref is not None:
            character = self.character_ref()
            if character is not None:
                return character
        self._refresh_runtime_refs()
        return self.character_ref() if self.character_ref is not None else None

    def _get_camera_manager(self):
        if self.camera_manager_ref is not None:
            camera_manager = self.camera_manager_ref()
            if camera_manager is not None:
                return camera_manager
        self._refresh_runtime_refs()
        return self.camera_manager_ref() if self.camera_manager_ref is not None else None

    def _get_camera_base_fov(self) -> float:
        return _clamp(self.fov.value, 20.0, 180.0) if self.enable_fov.value else 90.0

    def _is_zooming_now(self) -> bool:
        character = self._get_character()
        if character is None:
            return False
        try:
            state_name = _normalize_enum_name(character.ZoomState.State)
            normalized = state_name.lower()
            if normalized in {"zoomingin", "zoomed", "zoomedin", "aimingin", "aimed"}:
                return True
            if "zoom" in normalized:
                return not any(token in normalized for token in ("not", "none", "out", "unzoom"))
        except Exception:
            pass

        try:
            zoom_state = getattr(character, "ZoomState", None)
        except Exception:
            zoom_state = None

        for owner in (zoom_state, character):
            if owner is None:
                continue
            for attr_name in (
                "bWantsToZoom",
                "bIsZooming",
                "bIsZoomed",
                "bIsAiming",
                "bIsAimingDownSights",
                "bIsADS",
            ):
                if self._is_truthy_attr(owner, attr_name):
                    return True
        return False

    def _ads_should_use_first_person(self, is_zooming: bool) -> bool:
        if not (self.third_person.value and is_zooming):
            return False
        if self.over_shoulder.value:
            return self.ots_ads_override.value and self.ots_ads_first_person.value
        return self.third_person_ads_first_person.value

    def _should_draw_ads_crosshair(self) -> bool:
        if not self.third_person_ads_crosshair.value:
            return False
        if not self.third_person.value:
            return False
        if not self._is_zooming_now():
            return False
        if self._is_camera_override_blocked():
            return False
        return not self._ads_should_use_first_person(True)

    def _draw_center_crosshair(self, hud, center_x: float, center_y: float) -> None:
        half_len = _clamp(self.crosshair_size.value, 2.0, 64.0)
        thickness = _clamp(self.crosshair_thickness.value, 1.0, 12.0)
        color = make_struct("LinearColor", R=1.0, G=1.0, B=1.0, A=1.0)

        hud.DrawLine(float(center_x - half_len), float(center_y), float(center_x + half_len), float(center_y), color, thickness)
        hud.DrawLine(float(center_x), float(center_y - half_len), float(center_x), float(center_y + half_len), color, thickness)

    def _draw_center_crosshair_in_post_render(self, hud, center_x: float, center_y: float, canvas_ptr: int) -> None:
        if canvas_ptr < 0x10000:
            self._draw_center_crosshair(hud, center_x, center_y)
            return

        try:
            hud_addr = int(hud._get_address())
        except Exception:
            hud_addr = 0
        if hud_addr < 0x10000:
            self._draw_center_crosshair(hud, center_x, center_y)
            return

        canvas_addr = hud_addr + HUD_CANVAS_OFFSET
        debug_canvas_addr = hud_addr + HUD_DEBUG_CANVAS_OFFSET
        old_canvas = read_pointer(canvas_addr) or 0
        old_debug_canvas = read_pointer(debug_canvas_addr) or 0

        if not write_pointer(canvas_addr, int(canvas_ptr)):
            self._draw_center_crosshair(hud, center_x, center_y)
            return

        wrote_debug_canvas = False
        if old_debug_canvas != int(canvas_ptr):
            wrote_debug_canvas = write_pointer(debug_canvas_addr, int(canvas_ptr))

        try:
            self._draw_center_crosshair(hud, center_x, center_y)
        finally:
            write_pointer(canvas_addr, old_canvas)
            if wrote_debug_canvas:
                write_pointer(debug_canvas_addr, old_debug_canvas)

    def _get_canvas_draw_space(self, pc, canvas_ptr: int) -> dict[str, float] | None:
        # PostRender canvas coordinates can differ from viewport/display resolution when
        # dynamic resolution, DLSS, or TSR are active. Use the canvas clip rect as the
        # primary draw space so the crosshair stays centered in the actual render target.
        if canvas_ptr >= 0x10000:
            org_x = read_float(int(canvas_ptr) + CANVAS_ORG_X_OFFSET)
            org_y = read_float(int(canvas_ptr) + CANVAS_ORG_Y_OFFSET)
            clip_x = read_float(int(canvas_ptr) + CANVAS_CLIP_X_OFFSET)
            clip_y = read_float(int(canvas_ptr) + CANVAS_CLIP_Y_OFFSET)
            size_x = read_int32(int(canvas_ptr) + CANVAS_SIZE_X_OFFSET)
            size_y = read_int32(int(canvas_ptr) + CANVAS_SIZE_Y_OFFSET)
            if (
                org_x is not None
                and org_y is not None
                and clip_x is not None
                and clip_y is not None
                and clip_x > 0.0
                and clip_y > 0.0
            ):
                return {
                    "org_x": float(org_x),
                    "org_y": float(org_y),
                    "clip_x": float(clip_x),
                    "clip_y": float(clip_y),
                    "size_x": float(size_x or 0),
                    "size_y": float(size_y or 0),
                    "center_x": float(org_x + (clip_x * 0.5)),
                    "center_y": float(org_y + (clip_y * 0.5)),
                }

        try:
            result = pc.GetViewportSize()
            if isinstance(result, tuple) and len(result) >= 2:
                size_x = int(result[0] or 0)
                size_y = int(result[1] or 0)
            elif isinstance(result, list) and len(result) >= 2:
                size_x = int(result[0] or 0)
                size_y = int(result[1] or 0)
            else:
                size_x = 0
                size_y = 0
            if size_x > 0 and size_y > 0:
                return {
                    "org_x": 0.0,
                    "org_y": 0.0,
                    "clip_x": float(size_x),
                    "clip_y": float(size_y),
                    "size_x": float(size_x),
                    "size_y": float(size_y),
                    "center_x": float(size_x) * 0.5,
                    "center_y": float(size_y) * 0.5,
                }
        except Exception:
            pass

        return None

    def _on_post_render(self, _viewport_this: int, canvas_ptr: int) -> None:
        try:
            pc = self._get_pc()
            hud = getattr(pc, "myHUD", None) if pc is not None else None
            should_draw = self._should_draw_ads_crosshair()
            draw_space = self._get_canvas_draw_space(pc, int(canvas_ptr)) if pc is not None else None
            if pc is None or hud is None:
                return
            if not should_draw or draw_space is None:
                return
            self._draw_center_crosshair_in_post_render(
                hud,
                float(draw_space["center_x"]),
                float(draw_space["center_y"]),
                int(canvas_ptr),
            )
        except Exception:
            logging.dev_warning("[BL4 Third Person Camera] PostRender crosshair draw failed")
            logging.dev_warning(traceback.format_exc())

    def _get_viewport_client(self):
        pc = self._get_pc()
        if pc is None:
            return None
        try:
            player = pc.Player
        except Exception:
            player = None
        if player is not None:
            try:
                viewport = player.ViewportClient
                if viewport is not None:
                    return viewport
            except Exception:
                pass
        try:
            game_instance = pc.OwningGameInstance
        except Exception:
            game_instance = None
        if game_instance is not None:
            try:
                local_players = game_instance.LocalPlayers
            except Exception:
                local_players = None
            if local_players:
                try:
                    viewport = local_players[0].ViewportClient
                    if viewport is not None:
                        return viewport
                except Exception:
                    pass
        return None

    def _has_non_none_attr(self, obj: object, attr_name: str) -> bool:
        try:
            return getattr(obj, attr_name) is not None
        except Exception:
            return False

    def _is_truthy_attr(self, obj: object, attr_name: str) -> bool:
        try:
            return bool(getattr(obj, attr_name))
        except Exception:
            return False

    def _get_pawn(self):
        pc = self._get_pc()
        if pc is None:
            return None
        for attr_name in ("Pawn", "AcknowledgedPawn"):
            try:
                pawn = getattr(pc, attr_name)
                if pawn is not None:
                    return pawn
            except Exception:
                continue
        return None

    def _is_forced_first_person_state(self) -> bool:
        character = self._get_character()
        if character is None:
            return False

        for method_name in ("InDownState", "IsInjured"):
            try:
                method = getattr(character, method_name)
            except Exception:
                continue

            try:
                if callable(method) and bool(method()):
                    return True
            except Exception:
                continue

        return False

    def _is_camera_override_blocked(self) -> bool:
        pc = self._get_pc()
        pawn = self._get_pawn()
        character = self._get_character()
        camera_manager = self._get_camera_manager()

        if pc is None or character is None or camera_manager is None:
            return True

        if self._is_forced_first_person_state():
            return True

        try:
            if camera_manager.ViewTarget.target != character:
                return True
        except Exception:
            return True

        if pawn is not None:
            try:
                if getattr(getattr(pawn, "Class", None), "Name", "") != "OakCharacter":
                    return True
            except Exception:
                pass

        if self._is_truthy_attr(pc, "bDrivingVehicle"):
            return True

        try:
            player_state = pc.PlayerState
        except Exception:
            player_state = None
        if player_state is not None and self._is_truthy_attr(player_state, "bDrivingVehicle"):
            return True

        for attr_name in ("DrivenVehicle", "Vehicle"):
            if self._has_non_none_attr(pc, attr_name):
                return True
            if player_state is not None and self._has_non_none_attr(player_state, attr_name):
                return True
            if pawn is not None and self._has_non_none_attr(pawn, attr_name):
                return True
            if self._has_non_none_attr(character, attr_name):
                return True

        try:
            if bool(getattr(character, "bIsAttachedToVehicle")):
                return True
        except Exception:
            pass

        if pawn is not None:
            if self._is_truthy_attr(pawn, "bIsAttachedToVehicle"):
                return True
            if self._is_truthy_attr(pawn, "bDrivingVehicle"):
                return True

        return False

    def _get_shoulder_sign(self) -> float:
        return 1.0 if self.right_shoulder.value else -1.0

    def _apply_shoulder_side(self, lateral_offset: float) -> float:
        return abs(lateral_offset) * self._get_shoulder_sign()

    def _should_hold_third_person(self) -> bool:
        if (
            not self.third_person.value
            or self.requested_first_person
            or self._is_camera_override_blocked()
        ):
            return False
        camera_manager = self._get_camera_manager()
        character = self._get_character()
        if camera_manager is None or character is None:
            return False
        try:
            if camera_manager.ViewTarget.target != character:
                return False
        except Exception:
            return False
        if self._ads_should_use_first_person(self._is_zooming_now()):
            return False
        return True

    def _can_apply_native_ots(self) -> bool:
        if (
            not self.third_person.value
            or not self.over_shoulder.value
            or self._is_camera_override_blocked()
        ):
            return False

        camera_manager = self._get_camera_manager()
        character = self._get_character()
        if camera_manager is None or character is None:
            return False

        try:
            return camera_manager.ViewTarget.target == character
        except Exception:
            return False

    def _get_current_ots_ads_blend(self) -> float:
        if not self.ots_ads_override.value:
            return 0.0
        return self.smoothed_ots_ads_blend

    def _get_blended_ots_state(self, blend_alpha: float) -> tuple[float, float, float, float]:
        base = (
            self.ots_x.value,
            self._apply_shoulder_side(self.ots_y.value),
            self.ots_z.value,
            self._get_camera_base_fov(),
        )
        if not self.ots_ads_override.value:
            return base
        ads = (
            self.ots_ads_x.value,
            self._apply_shoulder_side(self.ots_ads_y.value),
            self.ots_ads_z.value,
            _clamp(self.ots_ads_fov.value, 20.0, 180.0),
        )
        return tuple(base[idx] + ((ads[idx] - base[idx]) * blend_alpha) for idx in range(4))

    def _get_applied_fov(self, for_ots: bool) -> float:
        if for_ots:
            fov = self._get_blended_ots_state(self._get_current_ots_ads_blend())[3]
        else:
            fov = self.fov.value if self.enable_fov.value else 90.0
        if self._is_zooming_now() and (not for_ots) and self.enable_fov.value:
            fov *= _clamp(self.ads_fov_scale.value, 0.2, 1.0)
        return _clamp(fov, 20.0, 180.0)

    def _update_smoothed_blend(self, current: float, should_zoom: bool, delta: float) -> float:
        duration = _clamp(self.ots_ads_blend_time.value, 0.01, 2.0)
        target = 1.0 if should_zoom else 0.0
        alpha = _clamp(delta / duration, 0.0, 1.0)
        return current + ((target - current) * alpha)

    def _build_desired_native_ots_state(self, delta: float) -> NativeOtsState:
        state = NativeOtsState()
        if not self._can_apply_native_ots():
            self.native_ots_blend_alpha = 0.0
            return state
        if self.ots_ads_override.value and self.ots_ads_first_person.value and self._is_zooming_now():
            self.native_ots_blend_alpha = 0.0
            return state
        should_zoom = self._is_zooming_now() and self.ots_ads_override.value
        self.native_ots_blend_alpha = self._update_smoothed_blend(self.native_ots_blend_alpha, should_zoom, delta)
        self.smoothed_ots_ads_blend = self.native_ots_blend_alpha
        blended = self._get_blended_ots_state(self.native_ots_blend_alpha)
        state.should_apply = True
        state.offset_x = blended[0]
        state.offset_y = blended[1]
        state.offset_z = blended[2]
        state.target_fov = blended[3] if self.ots_ads_override.value else self._get_camera_base_fov()
        return state

    def _make_offset(self, desired: NativeOtsState, pitch: float, yaw: float) -> tuple[float, float, float]:
        forward = self._rotator_to_vector(pitch, yaw)
        right = self._rotator_to_vector(0.0, yaw + 90.0)
        return (
            (forward[0] * desired.offset_x) + (right[0] * desired.offset_y),
            (forward[1] * desired.offset_x) + (right[1] * desired.offset_y),
            (forward[2] * desired.offset_x) + (right[2] * desired.offset_y) + desired.offset_z,
        )

    def _rotator_to_vector(self, pitch: float, yaw: float) -> tuple[float, float, float]:
        pitch_rad = math.radians(pitch)
        yaw_rad = math.radians(yaw)
        cp = math.cos(pitch_rad)
        sp = math.sin(pitch_rad)
        cy = math.cos(yaw_rad)
        sy = math.sin(yaw_rad)
        return (cp * cy, cp * sy, sp)

    def _read_pose(self, base: int, loc_offset: int, rot_offset: int, fov_offset: int) -> Pose | None:
        values = (
            read_double(base + loc_offset),
            read_double(base + loc_offset + 8),
            read_double(base + loc_offset + 16),
            read_double(base + rot_offset),
            read_double(base + rot_offset + 8),
            read_double(base + rot_offset + 16),
            read_float(base + fov_offset),
        )
        if any(value is None or not math.isfinite(value) for value in values):
            return None
        return Pose(*[float(value) for value in values])

    def _write_pose(self, base: int, loc_offset: int, rot_offset: int, fov_offset: int, pose: Pose) -> bool:
        return all(
            (
                write_double(base + loc_offset, pose.loc_x),
                write_double(base + loc_offset + 8, pose.loc_y),
                write_double(base + loc_offset + 16, pose.loc_z),
                write_double(base + rot_offset, pose.pitch),
                write_double(base + rot_offset + 8, pose.yaw),
                write_double(base + rot_offset + 16, pose.roll),
                write_float(base + fov_offset, pose.fov),
            )
        )

    def _apply_offset_to_pose(self, pose: Pose, desired: NativeOtsState) -> Pose:
        off_x, off_y, off_z = self._make_offset(desired, pose.pitch, pose.yaw)
        return Pose(
            pose.loc_x + off_x,
            pose.loc_y + off_y,
            pose.loc_z + off_z,
            pose.pitch,
            pose.yaw,
            pose.roll,
            _clamp(desired.target_fov, 20.0, 180.0),
        )

    def _is_reasonable_world_location(self, pose: Pose) -> bool:
        return (
            abs(pose.loc_x) <= OTS_MAX_WORLD_COORD
            and abs(pose.loc_y) <= OTS_MAX_WORLD_COORD
            and abs(pose.loc_z) <= OTS_MAX_WORLD_COORD
        )

    def _mirror_pose_to_sdk(self, pose: Pose) -> None:
        camera_manager = self._get_camera_manager()
        pc = self._get_pc()
        if camera_manager is None or pc is None:
            return
        self._set_pov(camera_manager.ViewTarget.POV, pose)
        for cache_name in ("PendingViewTarget",):
            try:
                cache = getattr(camera_manager, cache_name)
                if cache.target == camera_manager.ViewTarget.target:
                    self._set_pov(cache.POV, pose)
            except Exception:
                continue
        for cache_name in ("CameraCachePrivate", "LastFrameCameraCachePrivate"):
            try:
                self._set_pov(getattr(camera_manager, cache_name).POV, pose)
            except Exception:
                continue
        self._apply_runtime_camera_fov(pose.fov)

    def _set_pov(self, pov, pose: Pose) -> None:
        pov.Location.X = pose.loc_x
        pov.Location.Y = pose.loc_y
        pov.Location.Z = pose.loc_z
        pov.Rotation.Pitch = pose.pitch
        pov.Rotation.Yaw = pose.yaw
        pov.Rotation.Roll = pose.roll
        pov.fov = pose.fov

    def _apply_runtime_camera_fov(self, target_fov: float) -> None:
        camera_manager = self._get_camera_manager()
        pc = self._get_pc()
        if camera_manager is None or pc is None:
            return
        try:
            pc.fov(target_fov)
        except Exception:
            pass
        try:
            camera_manager.DefaultFOV = target_fov
        except Exception:
            pass
        try:
            self._set_pov(camera_manager.ViewTarget.POV, Pose(
                camera_manager.ViewTarget.POV.Location.X,
                camera_manager.ViewTarget.POV.Location.Y,
                camera_manager.ViewTarget.POV.Location.Z,
                camera_manager.ViewTarget.POV.Rotation.Pitch,
                camera_manager.ViewTarget.POV.Rotation.Yaw,
                camera_manager.ViewTarget.POV.Rotation.Roll,
                target_fov,
            ))
        except Exception:
            pass

    def _apply_viewmodel_fov(self) -> None:
        if not self.enable_viewmodel_fov.value:
            return
        camera_manager = self._get_camera_manager()
        if camera_manager is None:
            return
        try:
            state = camera_manager.CameraModeState
            if state is not None:
                state.SetViewModelFOV(_clamp(self.viewmodel_fov.value, 60.0, 150.0), True)
        except Exception:
            pass

    def _update_camera_mode_requests(self) -> None:
        pc = self._get_pc()
        camera_manager = self._get_camera_manager()
        character = self._get_character()
        if pc is None or camera_manager is None or character is None:
            return

        if self._is_camera_override_blocked():
            self.smoothed_ots_ads_blend = 0.0
            self.native_ots_blend_alpha = 0.0
            self.requested_first_person = False
            self.requested_third_person = False
            self.last_desired_third_person = False
            self.last_zooming = False
            if not getattr(self, "override_temporarily_blocked", False):
                self._best_effort_force_first_person()
            self.override_temporarily_blocked = True
            return

        self.override_temporarily_blocked = False

        is_zooming = self._is_zooming_now()
        use_ots = self.third_person.value and self.over_shoulder.value
        should_be_third_person = self.third_person.value and not self._ads_should_use_first_person(is_zooming)
        ads_state_changed = is_zooming != self.last_zooming

        if use_ots and should_be_third_person:
            self.smoothed_ots_ads_blend = self._update_smoothed_blend(self.smoothed_ots_ads_blend, is_zooming, 1.0 / 60.0)
        else:
            self.smoothed_ots_ads_blend = 0.0

        try:
            if camera_manager.ViewTarget.target != character:
                pc.SetViewTargetWithBlend(character, 0.15, VT_BLEND_LINEAR, 0.0, False)
        except Exception:
            pass

        changed = should_be_third_person != self.last_desired_third_person
        can_transition = ads_state_changed or (_now() - getattr(self, "last_transition_time", 0.0) > CAMERA_TRANSITION_MIN_INTERVAL)

        if changed and can_transition:
            self._wrapped_camera_transition(pc, "ThirdPerson" if should_be_third_person else "FirstPerson", "Default", 0.15, False, False)
            self.last_transition_time = _now()
            self.requested_third_person = should_be_third_person
            self.requested_first_person = not should_be_third_person
            self.last_desired_third_person = should_be_third_person
        elif not changed:
            self.requested_third_person = False
            self.requested_first_person = False

        self.last_zooming = is_zooming

    def _apply_native_post_update(self, camera_ctx: int, delta: float) -> None:
        if camera_ctx < 0x10000:
            return
        current_view = self._read_pose(camera_ctx, VIEWTARGET_LOC_OFFSET, VIEWTARGET_ROT_OFFSET, VIEWTARGET_FOV_OFFSET)
        if current_view is None:
            return

        desired = self._build_desired_native_ots_state(delta)
        if desired.should_apply:
            adjusted = self._apply_offset_to_pose(current_view, desired)
            self._write_pose(camera_ctx, VIEWTARGET_LOC_OFFSET, VIEWTARGET_ROT_OFFSET, VIEWTARGET_FOV_OFFSET, adjusted)
            current_cache = self._read_pose(camera_ctx, CURRENT_CACHE_LOC_OFFSET, CURRENT_CACHE_ROT_OFFSET, CURRENT_CACHE_FOV_OFFSET)
            if current_cache is None:
                current_cache = adjusted
            else:
                current_cache = self._apply_offset_to_pose(current_cache, desired)
                self._write_pose(camera_ctx, CURRENT_CACHE_LOC_OFFSET, CURRENT_CACHE_ROT_OFFSET, CURRENT_CACHE_FOV_OFFSET, current_cache)
            self._mirror_pose_to_sdk(current_cache)
            self._apply_viewmodel_fov()
            return

        if self.enable_fov.value:
            target_fov = self._get_applied_fov(False)
            write_float(camera_ctx + VIEWTARGET_FOV_OFFSET, target_fov)
            write_float(camera_ctx + CURRENT_CACHE_FOV_OFFSET, target_fov)
            self._apply_runtime_camera_fov(target_fov)
        self._apply_viewmodel_fov()
