"""Focused tests for public-vs-dev backpack drop-all routing."""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "backend_actions.py"


def _load_backpack_functions():
    tree = ast.parse(BACKEND.read_text(encoding="utf-8"))
    wanted = {"chaos_drop_backpack", "chaos_drop_backpack_targeted"}
    functions = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in wanted
    ]
    module = ast.Module(body=functions, type_ignores=[])
    namespace = {}
    exec(compile(module, str(BACKEND), "exec"), namespace)
    return namespace


def test_public_drop_all_backpack_always_uses_host_controller():
    funcs = _load_backpack_functions()
    host_pc = object()
    calls = []
    funcs["get_pc"] = lambda: host_pc
    funcs["streamer_chaos"] = SimpleNamespace(
        drop_backpack_for_pc=lambda pc: calls.append(pc) or "drop ok",
        result_ok=lambda _msg: True,
    )

    result = funcs["chaos_drop_backpack"]()

    assert result["ok"] is True
    assert result["host_only"] is True
    assert calls == [host_pc]


def test_dev_drop_all_backpack_keeps_selected_target_path():
    funcs = _load_backpack_functions()
    runner = object()
    calls = []
    funcs["streamer_chaos"] = SimpleNamespace(drop_backpack_for_pc=runner)
    funcs["_chaos_run"] = lambda label, effect: calls.append((label, effect)) or {"ok": True}

    result = funcs["chaos_drop_backpack_targeted"]()

    assert result["ok"] is True
    assert calls == [("Drop backpack", runner)]


def test_dispatch_keeps_public_and_dev_action_ids_separate():
    source = BACKEND.read_text(encoding="utf-8")
    assert 'elif key == "chaos_drop_backpack":\n        result = chaos_drop_backpack()' in source
    assert 'elif key == "chaos_drop_backpack_targeted":\n        result = chaos_drop_backpack_targeted()' in source
