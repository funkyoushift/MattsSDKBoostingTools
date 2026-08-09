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
    assert "blimgui_panel" not in source or filename == "backend_actions.py"
    # backend_actions may mention blimgui_panel only as an optional already-loaded sync target.
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
    ba.get_status = lambda: {
        "players": [],
        "selected_player": "",
        "serial_delivery": {},
        "diagnostics": {},
        "last_command": None,
        "last_drop": None,
        "drop_player_lock": {"enabled": False},
    }
    ba._sdk_diagnostics = lambda: {}
    sys.modules["MattsSDKBoostingTools.backend_actions"] = ba
    bridge = _load_module("MattsSDKBoostingTools.external_bridge", "external_bridge.py")
    source = (PKG / "external_bridge.py").read_text(encoding="utf-8")
    assert "blimgui_panel" not in source
    assert "from .blimgui" not in source
    status = bridge._status()
    assert status["ok"] is True
