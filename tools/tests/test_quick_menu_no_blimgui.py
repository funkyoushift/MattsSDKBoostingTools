"""Quick Menu / bridge path must not import or require BLImGui."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"

_FORBIDDEN = ("blimgui", "blimgui_panel", "MattsSDKBoostingTools.blimgui_panel")


def _install_base_stubs() -> types.ModuleType:
    sys.modules.pop("MattsSDKBoostingTools.quick_menu_registry", None)
    for name in ("unrealsdk", "unrealsdk.unreal", "unrealsdk.hooks", "mods_base"):
        sys.modules.setdefault(name, types.ModuleType(name))

    unrealsdk = sys.modules["unrealsdk"]
    unrealsdk.logging = types.SimpleNamespace(info=lambda *a, **k: None, warning=lambda *a, **k: None, error=lambda *a, **k: None)
    unrealsdk.find_object = lambda *a, **k: None
    unrealsdk.construct_object = lambda *a, **k: None
    unrealsdk.make_struct = lambda *a, **k: types.SimpleNamespace()
    unrealsdk.hooks = types.SimpleNamespace(
        add_hook=lambda *a, **k: None,
        remove_hook=lambda *a, **k: None,
        Type=types.SimpleNamespace(POST="POST"),
    )
    sys.modules["unrealsdk.hooks"].Type = unrealsdk.hooks.Type

    mb = sys.modules["mods_base"]
    mb.ENGINE = None
    mb.get_pc = lambda: None
    mb.hook = lambda *a, **k: (lambda f: f)
    mb.command = lambda *a, **k: (lambda f: f)
    mb.keybind = lambda *a, **k: types.SimpleNamespace(key=k.get("key") if isinstance(k, dict) else None, callback=None)

    def _keybind(*args, **kwargs):
        return types.SimpleNamespace(key=kwargs.get("key") or (args[1] if len(args) > 1 else None), callback=kwargs.get("callback"))

    def _command(*args, **kwargs):
        def deco(fn):
            fn.add_argument = lambda *a, **k: None
            return fn
        return deco

    mb.keybind = _keybind
    mb.command = _command

    pkg = types.ModuleType("MattsSDKBoostingTools")
    pkg.__path__ = [str(PKG)]
    sys.modules["MattsSDKBoostingTools"] = pkg
    return pkg


def _load_module(fullname: str, filename: str, *, extra_stubs: dict[str, dict] | None = None):
    for mod_name, attrs in (extra_stubs or {}).items():
        mod = types.ModuleType(mod_name)
        for key, value in attrs.items():
            setattr(mod, key, value)
        sys.modules[mod_name] = mod

    # Poison forbidden modules so any import attempt fails loudly.
    for forbidden in _FORBIDDEN:
        if forbidden not in sys.modules:
            sys.modules[forbidden] = types.ModuleType(forbidden)

    before = {name for name in sys.modules if any(tok in name for tok in ("blimgui",))}
    spec = importlib.util.spec_from_file_location(fullname, PKG / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[fullname] = module
    spec.loader.exec_module(module)
    after = {name for name in sys.modules if any(tok in name for tok in ("blimgui",))}
    # Loading our modules must not create new blimgui imports beyond the poison stubs.
    assert "blimgui" not in getattr(module, "__dict__", {})
    source = (PKG / filename).read_text(encoding="utf-8", errors="replace")
    assert "import blimgui" not in source
    assert "blimgui_panel" not in source
    if filename == "backend_actions.py":
        assert "import blimgui" not in source
        assert "from .blimgui_panel" not in source
        assert "importlib.import_module" not in source or "blimgui" not in source
    newly = after - before
    assert not any(name == "blimgui" or name.endswith(".blimgui_panel") for name in newly if sys.modules.get(name) and getattr(sys.modules[name], "__file__", None))
    return module


def test_quick_menu_source_and_load_without_blimgui():
    _install_base_stubs()
    # Inventory settings helpers used by quick_menu.
    stubs = {
        "MattsSDKBoostingTools.backend_actions": {
            "get_last_command": lambda: None,
            "get_last_drop": lambda: None,
            "get_drop_player_lock": lambda: {"enabled": False},
            "set_drop_player_lock": lambda *a, **k: {"ok": True},
            "repeat_last_drop": lambda *a, **k: {"ok": True},
            "run_quick_menu_action": lambda *a, **k: {"ok": True},
            "refresh_players": lambda: [],
            "get_selected_player_index": lambda: None,
            "get_selected_player_name": lambda: "",
            "set_target_player": lambda *a, **k: {"ok": True},
            "get_serial_delivery_progress": lambda: {"active": False},
            "get_status": lambda: {},
        },
        "MattsSDKBoostingTools.inventory_capacity": {
            "clamp_container_size": lambda value, default: int(value or default),
            "load_inventory_settings": lambda: {},
            "save_extra_settings": lambda **k: {},
        },
    }
    module = _load_module("MattsSDKBoostingTools.quick_menu", "quick_menu.py", extra_stubs=stubs)
    assert hasattr(module, "toggle_panel")
    assert hasattr(module, "unstuck")
    assert hasattr(module, "process_hotkeys")
    qm_src = (PKG / "quick_menu.py").read_text(encoding="utf-8")
    assert "Close F7" in qm_src
    assert "F6 unstuck" in qm_src
    assert "process_hotkeys" in qm_src
    assert "_bound_keybind_name" in qm_src
    assert ' _edge_key(pc, "F6", "key_f6")' not in qm_src
    assert "blimgui" not in sys.modules["MattsSDKBoostingTools.quick_menu"].__dict__


def test_process_hotkeys_skips_unbound_f6_unstuck():
    """Unbinding MSBT Quick Menu Unstuck must stop the tick poller from firing F6."""
    _install_base_stubs()
    stubs = {
        "MattsSDKBoostingTools.backend_actions": {
            "get_last_command": lambda: None,
            "get_last_drop": lambda: None,
            "get_drop_player_lock": lambda: {"enabled": False},
            "set_drop_player_lock": lambda *a, **k: {"ok": True},
            "repeat_last_drop": lambda *a, **k: {"ok": True},
            "run_quick_menu_action": lambda *a, **k: {"ok": True},
            "refresh_players": lambda: [],
            "get_selected_player_index": lambda: None,
            "get_selected_player_name": lambda: "",
            "set_target_player": lambda *a, **k: {"ok": True},
            "get_serial_delivery_progress": lambda: {"active": False},
            "get_status": lambda: {},
        },
        "MattsSDKBoostingTools.inventory_capacity": {
            "clamp_container_size": lambda value, default: int(value or default),
            "load_inventory_settings": lambda: {},
            "save_extra_settings": lambda **k: {},
        },
    }
    module = _load_module("MattsSDKBoostingTools.quick_menu", "quick_menu.py", extra_stubs=stubs)

    calls: list[str] = []
    module.unstuck = lambda: calls.append("unstuck")
    module.close_panel = lambda: calls.append("close")
    module._key_down = lambda pc, name: name in ("F6", "F7")
    module.get_pc = lambda: object()

    # Unbound: poller must not treat hardcoded F6 as active.
    module.quick_menu_unstuck_key.key = None
    module.quick_menu_toggle.key = "F7"
    module.STATE.is_open = False
    module.STATE.key_f6 = False
    module.STATE.key_f7 = False
    module.process_hotkeys()
    assert calls == []

    # Bound again: F6 edge should fire unstuck even when menu is closed.
    module.quick_menu_unstuck_key.key = "F6"
    module.STATE.key_f6 = False
    module.process_hotkeys()
    assert calls == ["unstuck"]


def test_quick_menu_modal_layers_and_blockers_are_consistent():
    _install_base_stubs()
    stubs = {
        "MattsSDKBoostingTools.backend_actions": {
            "get_last_command": lambda: None,
            "get_last_drop": lambda: None,
            "get_drop_player_lock": lambda: {"enabled": False},
            "set_drop_player_lock": lambda *a, **k: {"ok": True},
            "repeat_last_drop": lambda *a, **k: {"ok": True},
            "run_quick_menu_action": lambda *a, **k: {"ok": True},
            "refresh_players": lambda: [],
            "ensure_selected_player": lambda **k: {"ok": False},
            "get_selected_player_index": lambda: None,
            "get_selected_player_name": lambda: "",
            "set_target_player": lambda *a, **k: {"ok": True},
            "get_serial_delivery_progress": lambda: {"active": False},
            "get_status": lambda: {},
        },
        "MattsSDKBoostingTools.inventory_capacity": {
            "clamp_container_size": lambda value, default: int(value or default),
            "load_inventory_settings": lambda: {},
            "save_extra_settings": lambda **k: {},
        },
    }
    module = _load_module("MattsSDKBoostingTools.quick_menu", "quick_menu.py", extra_stubs=stubs)
    assert (
        module.MODAL_BLOCKER_Z
        < module.MODAL_PANEL_Z
        < module.MODAL_CONTENT_Z
        < module.MODAL_BUTTON_Z
    )
    assert module._button_layer(50, False, False) == 50
    assert module._button_layer(50, True, False) == module.MODAL_BUTTON_Z
    assert module._button_layer(50, False, True) == module.MODAL_BUTTON_Z
    source = (PKG / "quick_menu.py").read_text(encoding="utf-8")
    assert source.count("factory.modal_blocker(root)") == 5


def test_external_bridge_does_not_import_blimgui_panel():
    _install_base_stubs()
    ba = types.ModuleType("MattsSDKBoostingTools.backend_actions")
    ba.get_status = lambda **_kwargs: {
        "players": [],
        "selected_player": "",
        "serial_delivery": {},
        "diagnostics": {},
        "last_command": None,
        "last_drop": None,
        "drop_player_lock": {"enabled": False},
    }
    ba._sdk_diagnostics = lambda: {}
    ba.afk_lobby_status = lambda: {"enabled": False}
    sys.modules["MattsSDKBoostingTools.backend_actions"] = ba
    bridge = _load_module("MattsSDKBoostingTools.external_bridge", "external_bridge.py")
    source = (PKG / "external_bridge.py").read_text(encoding="utf-8")
    assert "blimgui_panel" not in source
    assert "from .blimgui" not in source
    status = bridge._status()
    assert status["ok"] is True


def test_sdk_entrypoint_starts_supported_interfaces_without_legacy_panel(monkeypatch):
    import builtins

    package = "_msbt_startup_test"
    started = []
    registrations = []
    forbidden_attempts = []
    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if "blimgui" in name:
            forbidden_attempts.append(name)
            raise ImportError(name)
        return original_import(name, *args, **kwargs)

    def install(name, **attrs):
        module = types.ModuleType(name)
        module.__dict__.update(attrs)
        monkeypatch.setitem(sys.modules, name, module)

    install("mods_base", Game=types.SimpleNamespace(BL4=4),
            CoopSupport=types.SimpleNamespace(Unknown=0),
            build_mod=lambda **kwargs: registrations.append(kwargs))
    siblings = {
        "golden_chest_keybinds": ["CLOSE_GOLDEN_CHEST_KEY", "OPEN_GOLDEN_CHEST_KEY"],
        "instant_click_holds": ["ICH_KEYBINDS"],
        "third_person_camera": ["TPC_KEYBINDS"],
        "player_economy": ["_cmd_givecurrency", "_cmd_giveexperience"],
        "serial_rewards": ["_cmd_give_serial"],
        "runtime_cleanup": ["clear_travel_caches"],
        "inventory_capacity": ["start_auto_inventory_worker"],
        "external_bridge": ["start_bridge"],
        "external_app_launcher": ["_cmd_msbt_external_app"],
        "backend_actions": ["_cmd_msbt_complete_challenges", "_cmd_msbt_complete_challenges_cancel",
                            "_cmd_msbt_fog", "_cmd_msbt_probe_challenge_apis", "challenge_api_probe_enabled"],
        "quick_menu": ["_cmd_msbt_quick_menu", "_cmd_msbt_quick_menu_lock", "_cmd_msbt_quick_menu_pin",
                       "_cmd_msbt_quick_menu_repeat", "_cmd_msbt_quick_menu_unstuck",
                       "quick_menu_toggle", "quick_menu_unstuck_key", "start_quick_menu"],
        "mobile_pairing": ["_cmd_msbt_mobile_pair", "mobile_pair_toggle", "start_mobile_pairing"],
    }
    for sibling, names in siblings.items():
        attrs = {}
        for name in names:
            if name.startswith("start_"):
                attrs[name] = lambda name=name: started.append(name)
            elif name == "challenge_api_probe_enabled":
                attrs[name] = lambda: False
            elif name.endswith("KEYBINDS"):
                attrs[name] = [name]
            else:
                attrs[name] = name
        install(f"{package}.{sibling}", **attrs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    spec = importlib.util.spec_from_file_location(package, PKG / "__init__.py",
                                                 submodule_search_locations=[str(PKG)])
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, package, module)
    spec.loader.exec_module(module)
    assert forbidden_attempts == []
    assert started == ["start_auto_inventory_worker", "start_bridge", "start_quick_menu", "start_mobile_pairing"]
    assert len(registrations) == 1
    registration = registrations[0]
    native = sys.modules[f"{package}.guaranteed_drops"]
    calls = []
    monkeypatch.setattr(native.override, "set_enabled", lambda value: calls.append(value) or {"ok": True})
    registration["on_disable"]()
    assert calls == [False]
    assert registration["keybinds"] == ["quick_menu_toggle", "quick_menu_unstuck_key", "mobile_pair_toggle",
                                         "OPEN_GOLDEN_CHEST_KEY", "CLOSE_GOLDEN_CHEST_KEY", "ICH_KEYBINDS", "TPC_KEYBINDS"]
    assert len(registration["commands"]) == 13
    assert "_cmd_msbt_quick_menu" in registration["commands"]
    assert "_cmd_msbt_mobile_pair" in registration["commands"]
    assert not (PKG / "blimgui_panel.py").exists()
