"""Focused tests for public-vs-dev backpack drop-all routing."""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "mod_extracted" / "MattsSDKBoostingTools" / "backend_actions.py"


def _load_backpack_functions():
    tree = ast.parse(BACKEND.read_text(encoding="utf-8"))
    wanted = {"chaos_drop_backpack", "chaos_drop_backpack_targeted", "chaos_empty_backpack", "_backpack_target_password_guard"}
    functions = [
        node for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in wanted
    ]
    module = ast.Module(body=functions, type_ignores=[])
    namespace = {"_uvh_obj_addr": lambda pc: id(pc), "_uvh_obj_path": lambda pc: "pc", "_challenge_is_host": lambda: (True, "host")}
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


def test_guest_drop_requires_password_and_does_not_unlock_future_calls():
    funcs = _load_backpack_functions(); host = object(); guest = object(); calls = []
    funcs["get_pc"] = lambda: host
    funcs["_chaos_selected_pc"] = lambda: (guest, "Guest")
    funcs["streamer_chaos"] = SimpleNamespace(drop_backpack_for_pc=lambda pc: calls.append(pc) or "OK", result_ok=lambda _: True)
    for payload in ({}, {"backpack_password": "wrong"}, {"backpack_password": True}, {"host_only": True}):
        assert funcs["chaos_drop_backpack_targeted"](payload)["password_required"]
    assert calls == []
    assert funcs["chaos_drop_backpack_targeted"]({"backpack_password": "funkyou"})["ok"]
    assert calls == [guest]
    assert funcs["chaos_drop_backpack_targeted"]()["password_required"]
    funcs["_chaos_selected_pc"] = lambda: (host, "Host")
    assert funcs["chaos_drop_backpack_targeted"]()["ok"]
    assert calls == [guest, host]


def test_guest_empty_rejected_before_snapshot_or_mutation():
    funcs = _load_backpack_functions(); host = object(); guest = object()
    funcs["get_pc"] = lambda: host
    funcs["_chaos_selected_pc"] = lambda: (guest, "Guest")
    def unexpected(*_): raise AssertionError("No inventory access before password")
    funcs["_capture_deleted_backpack_snapshot"] = unexpected
    funcs["streamer_chaos"] = SimpleNamespace(empty_backpack_for_pc=unexpected)
    assert funcs["chaos_empty_backpack"]()["password_required"]


def test_target_change_and_join_client_do_not_bypass_guard():
    funcs = _load_backpack_functions(); local = object(); guest = object()
    funcs["get_pc"] = lambda: local
    guard = funcs["_backpack_target_password_guard"]
    target = guard(guest)["backpack_target"]
    assert not guard(local, {"backpack_password": "funkyou", "backpack_expected_target": target})["ok"]
    funcs["_challenge_is_host"] = lambda: (False, "client")
    assert guard(local)["password_required"]
    assert guard(guest, {"backpack_password": "funkyou", "backpack_expected_target": target}) is None


def test_dispatch_keeps_public_and_dev_action_ids_separate():
    source = BACKEND.read_text(encoding="utf-8")
    assert 'elif key == "chaos_drop_backpack":\n        result = chaos_drop_backpack(payload)' in source
    assert 'elif key == "chaos_drop_backpack_targeted":\n        result = chaos_drop_backpack_targeted(payload)' in source
