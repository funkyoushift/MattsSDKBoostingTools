"""Exercise shared-camera dispatch and UI lifetimes without touching a live game."""
from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parents[2] / "mod_extracted" / "MattsSDKBoostingTools"
TEST_PACKAGE = "msbt_camera_lifecycle_test"


@pytest.fixture
def runtime(monkeypatch):
    def module(name, **values):
        result = types.ModuleType(name)
        result.__dict__.update(values)
        monkeypatch.setitem(sys.modules, name, result)
        return result

    def decorator(*_args, **_kwargs):
        def apply(fn):
            fn.add_argument = lambda *_a, **_k: None
            return fn
        return apply

    clock = types.SimpleNamespace(now=100.0, quiet=False)
    timer = types.SimpleNamespace(monotonic=lambda: clock.now)
    logs, added, removed = [], [], []
    hooks = module("unrealsdk.hooks", Type=types.SimpleNamespace(PRE=0, POST=1),
                   add_hook=lambda *args: added.append(args),
                   remove_hook=lambda *args: removed.append(args))
    module("unrealsdk", hooks=hooks,
           logging=types.SimpleNamespace(info=logs.append, warning=logs.append, error=logs.append))
    module("mods_base", ENGINE=None, get_pc=lambda: None, hook=decorator, command=decorator,
           EInputEvent=types.SimpleNamespace(IE_Pressed=0),
           keybind=lambda *args, **kwargs: types.SimpleNamespace(
               key=args[1] if len(args) > 1 else None, callback=kwargs.get("callback")))
    module(TEST_PACKAGE, __path__=[str(PKG)])
    module(f"{TEST_PACKAGE}.travel_gate", is_travel_quiet=lambda: clock.quiet,
           consume_pending_clear=lambda: False)
    backend = module(f"{TEST_PACKAGE}.backend_actions",
                     get_serial_delivery_progress=lambda: {"active": False},
                     tick_asd_autoclear=lambda: None)
    module(f"{TEST_PACKAGE}.inventory_capacity",
           clamp_container_size=lambda value, default: int(value or default),
           load_inventory_settings=lambda: {}, save_extra_settings=lambda **_k: {})

    def load(name):
        result = importlib.import_module(f"{TEST_PACKAGE}.{name}")
        if hasattr(result, "time"):
            result.time = timer
        return result

    camera = load("camera_tick")
    yield types.SimpleNamespace(load=load, camera=camera, clock=clock, backend=backend,
                                logs=logs, added=added, removed=removed)
    for name in list(sys.modules):
        if name.startswith(TEST_PACKAGE + "."):
            sys.modules.pop(name, None)


def pump(runtime, seconds=0.02):
    runtime.clock.now += seconds
    runtime.camera._pump(None, None, None, None)


def quiet_menu(runtime, monkeypatch):
    menu = runtime.load("quick_menu")
    monkeypatch.setattr(menu, "process_hotkeys", lambda *_: None)
    monkeypatch.setattr(menu, "process_escape", lambda *_: None)
    monkeypatch.setattr(menu, "process_slot_hotkeys", lambda *_: None)
    monkeypatch.setattr(menu, "restore_input", lambda: None)
    monkeypatch.setattr(menu, "_ensure_toast_overlay", lambda *_: None)
    monkeypatch.setattr(menu, "_clear_toast_overlay", lambda: None)
    monkeypatch.setattr(menu, "live", lambda _obj: False)
    menu.STATE.layout_revision = menu.quick_menu_registry.get_layout_revision()
    menu.STATE.pages = [[]]
    menu.STATE.slot_hotkey_cache_revision = -1
    menu.install_hook()
    return menu


def test_idle_features_do_not_run_and_last_request_removes_engine_hook(runtime):
    camera, calls = runtime.camera, []
    camera.register("idle", lambda *_: calls.append("idle"))
    camera.register("active", lambda *_: calls.append("active"))
    camera.set_needed("active", True)
    pump(runtime)
    assert calls == ["active"]
    camera.set_needed("active", False)
    pump(runtime)
    assert calls == ["active"]
    assert not camera._installed
    assert runtime.removed[-1][2] == camera.HOOK_ID


def test_infinite_jump_only_does_not_wake_disabled_dash_or_spam_sync_logs(runtime):
    movement = runtime.load("movement_adjustments")
    movement._INFINITE_JUMP_INDICES = {0}
    movement._INFINITE_JUMP_LOCAL_IDX = 0
    movement._IJ_HOOKS_ARMED = True
    runtime.camera.set_needed("infinite_jump", True)
    runtime.logs.clear()
    for _ in range(100):
        pump(runtime)
    # Before filtering, the actual disabled dash callback produced one line per
    # accepted shared tick through _sync_movement_camera_need().
    assert not any("IJ sync on" in line for line in runtime.logs)
    assert runtime.camera._needed == {"infinite_jump"}


@pytest.mark.parametrize("need_name", ["quick_menu_hotkeys", "quick_menu_toast", "quick_menu_delivery"])
def test_quick_menu_lifetimes_do_not_wake_mobile_pairing(runtime, need_name):
    camera, calls = runtime.camera, []
    camera.register("quick_menu", lambda *_: calls.append("menu"))
    camera.register("quick_menu_mobile_pair", lambda *_: calls.append("pair"))
    camera.set_needed(need_name, True)
    pump(runtime)
    assert calls == ["menu"]
    camera.set_needed(need_name, False)
    camera.set_needed("quick_menu_mobile_pair", True)
    pump(runtime)
    assert calls == ["menu", "pair"]


def test_travel_still_allows_open_menu_but_suspends_gameplay_callbacks(runtime):
    camera, calls = runtime.camera, []
    for name in ("quick_menu", "infinite_jump"):
        camera.register(name, lambda *_, name=name: calls.append(name))
        camera.set_needed(name, True)
    runtime.clock.quiet = True
    pump(runtime)
    assert calls == ["quick_menu"]
    camera.set_needed("quick_menu", False)
    pump(runtime)
    assert calls == ["quick_menu"]
    runtime.clock.quiet = False
    pump(runtime)
    assert calls == ["quick_menu", "infinite_jump"]


def test_callback_can_cancel_later_work_in_the_same_pump(runtime):
    camera, calls = runtime.camera, []
    camera.register("first", lambda *_: camera.set_needed("second", False), priority=1)
    camera.register("second", lambda *_: calls.append("second"), priority=2)
    camera.set_needed("first", True)
    camera.set_needed("second", True)
    pump(runtime)
    assert calls == []


@pytest.mark.parametrize("hotkey", ["", "F9"])
def test_dead_menu_overlay_releases_only_its_own_request(runtime, monkeypatch, hotkey):
    menu = quiet_menu(runtime, monkeypatch)
    menu.STATE.pages = [[{"hotkey": hotkey, "action": "test", "payload": {}}]]
    menu.STATE.slot_hotkey_cache_revision = -1
    menu.STATE.is_open = True
    menu._sync_camera_need()
    runtime.removed.clear()
    pump(runtime, 0.04)
    assert not menu.STATE.is_open
    assert runtime.camera._needed == ({"quick_menu_hotkeys"} if hotkey else set())
    assert runtime.camera._installed is bool(hotkey)
    if hotkey:
        assert runtime.removed == []  # no remove/reinstall during the handoff


def test_already_closed_menu_reconciles_stale_camera_request(runtime, monkeypatch):
    menu = quiet_menu(runtime, monkeypatch)
    runtime.camera.set_needed("quick_menu", True)
    menu.close_panel()
    assert not runtime.camera._needed
    assert not runtime.camera._installed


def test_closed_menu_toast_expires_without_an_unrelated_feature(runtime, monkeypatch):
    menu = quiet_menu(runtime, monkeypatch)
    menu.show_toast("Done", seconds=1.0)
    assert runtime.camera._needed == {"quick_menu_toast"}
    pump(runtime, 0.5)
    assert menu.STATE.toast == "Done"
    pump(runtime, 0.6)
    assert menu.STATE.toast == ""
    assert not runtime.camera._needed
    assert not runtime.camera._installed


def test_delivery_polling_outlives_start_toast_then_releases_after_completion(runtime, monkeypatch):
    menu = quiet_menu(runtime, monkeypatch)
    progress = {"active": True, "message": "Delivering"}
    runtime.backend.get_serial_delivery_progress = lambda: progress
    menu._poll_delivery_toasts()
    assert runtime.camera._needed == {"quick_menu_toast", "quick_menu_delivery"}
    pump(runtime, 2.1)
    assert menu.STATE.toast == ""
    assert runtime.camera._needed == {"quick_menu_delivery"}
    progress.update(active=False, message="Delivered")
    pump(runtime, 0.1)
    assert menu.STATE.toast == "Delivered"
    assert runtime.camera._needed == {"quick_menu_toast"}
    pump(runtime, 3.0)
    assert not runtime.camera._needed


def test_third_person_native_miss_requests_fallback_once_per_player_tick(runtime, monkeypatch):
    tpc = runtime.load("third_person_camera")
    requests = []
    ctrl = types.SimpleNamespace(update_hook=None)
    monkeypatch.setattr(tpc, "_controller", lambda: ctrl)
    monkeypatch.setattr(tpc, "_request_third_person", lambda value: requests.append(value))
    tpc._local_controller = ctrl
    tpc._want_enabled = True
    tpc._native_unavailable = True
    tpc._player_tick()
    assert requests == [ctrl]
    tpc._want_enabled = False
    tpc._player_tick()
    assert requests == [ctrl]
    tpc._want_enabled = True
    ctrl.update_hook = types.SimpleNamespace(installed=True)
    tpc._player_tick()
    assert requests == [ctrl]


def test_third_person_first_native_miss_does_not_duplicate_apply_on_request(runtime, monkeypatch):
    tpc = runtime.load("third_person_camera")
    requests, enabled = [], []
    ctrl = types.SimpleNamespace(update_hook=None, enable=lambda: enabled.append(True))
    monkeypatch.setattr(tpc, "_controller", lambda: ctrl)
    monkeypatch.setattr(tpc, "_request_third_person", lambda value: requests.append(value))
    tpc._local_controller = ctrl
    tpc._want_enabled = True
    tpc._native_unavailable = False
    tpc._player_tick()
    assert enabled == [True]
    assert requests == [ctrl]
    tpc._player_tick()
    assert enabled == [True]
    assert requests == [ctrl, ctrl]
