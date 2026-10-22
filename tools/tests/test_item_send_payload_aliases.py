"""Exercise real bridge alias normalization without game imports or native calls."""
import ast
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[2]


@pytest.mark.parametrize("field", ["serial_text", "bookmark_serial", "code_serial", "serial_input"])
@pytest.mark.parametrize("mode", ["local", "selected", "all", "nonhost"])
@pytest.mark.parametrize("assignable", [False, True])
def test_item_send_aliases_preserve_code_mode_and_authorization(field, mode, assignable):
    source = ROOT / "mod_extracted/MattsSDKBoostingTools/external_bridge.py"
    names = {"_handle_action", "_payload_serial_text", "_normalize_quick_menu_bridge_payload"}
    nodes = [node for node in ast.parse(source.read_text(encoding="utf-8")).body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    action = "give_serial_" + mode
    calls = []
    def quick(key, payload, **kwargs):
        calls.append((key, payload))
        return {"ok": True}
    def give(text, target_mode, override, level, **kwargs):
        calls.append((text, target_mode, override, level, kwargs))
        return {"ok": True}
    env = {"Any": object,
           "quick_menu_registry": SimpleNamespace(ASSIGNABLE_ACTIONS=[action] if assignable else []),
           "backend_actions": SimpleNamespace(full_progress_conflict=lambda _: False,
                                              run_quick_menu_action=quick, give_serials=give)}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), "exec"), env)
    code = "@UAbC`x@Uyz\n@UaBc`x@Uyz"
    payload = {field: code, "serial_override_level": "true", "code_delivery_level": 42,
               "bulk_loot_password": "test-password"}
    assert env["_handle_action"](action, payload)["ok"]
    assert len(calls) == 1
    if assignable:
        key, forwarded = calls[0]
        assert key == action
        assert forwarded["serial_text"] == code
        assert forwarded["serial_override_level"] is True
        assert forwarded["serial_level"] == 42
        assert forwarded["bulk_loot_password"] == "test-password"
    else:
        assert calls[0] == (code, mode, True, 42, {"bulk_loot_password": "test-password"})
