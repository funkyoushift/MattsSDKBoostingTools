"""Explicit mobile targets are checked in the same action dispatch as the write."""
import ast
from pathlib import Path
from typing import Any

SOURCE = Path(__file__).resolve().parents[2] / "mod_extracted/MattsSDKBoostingTools/backend_actions.py"


def test_invalid_explicit_target_prevents_boost():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_quick_menu_action")
    calls = []
    namespace = {"Any": Any, "set_target_player": lambda target: {"ok": False, "message": "Player left"},
                 "max_spec_level": lambda: calls.append("boost")}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(SOURCE), "exec"), namespace)
    assert namespace[fn.name]("max_spec_level", {"target_player": "1|Gone"})["ok"] is False
    assert calls == []


def test_target_is_selected_before_boost():
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_quick_menu_action")
    calls = []
    class StopAfterBoost(Exception):
        pass
    def select(target):
        calls.append(target)
        return {"ok": True}
    def boost():
        calls.append("boost")
        raise StopAfterBoost()
    namespace = {"Any": Any, "set_target_player": select, "max_spec_level": boost}
    exec(compile(ast.Module(body=[fn], type_ignores=[]), str(SOURCE), "exec"), namespace)
    try:
        namespace[fn.name]("max_spec_level", {"target_player": "1|Guest"})
    except StopAfterBoost:
        pass
    assert calls == ["1|Guest", "boost"]
