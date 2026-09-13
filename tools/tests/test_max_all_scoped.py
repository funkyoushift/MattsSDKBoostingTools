"""Scoped Max All should boost each player once and apply fog only once."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"


@pytest.fixture
def max_all_env(monkeypatch):
    boost_calls: list[str] = []
    fog_calls: list[str] = []
    reveal_calls: list[str] = []

    ns = {
        "Any": object,
        "_selected_player_index": None,
        "_selected_player_name": "",
        "_players": lambda: [(0, "Host"), (1, "Guest")],
        "refresh_players": lambda: None,
        "_party_controller_for_index": lambda idx: types.SimpleNamespace(name=f"P{idx}"),
    }

    src = (PKG / "backend_actions.py").read_text(encoding="utf-8")
    start = src.index("def _normalize_party_indices(")
    end = src.index("\ndef cxp_set_enabled(")
    exec(src[start:end], ns, ns)  # noqa: S102

    def stub_boost(pc, *, apply_session_fog=True):
        boost_calls.append(f"{getattr(pc, 'name', 'pc')}:fog={apply_session_fog}")
        return True, "boosted"

    def stub_fog(pc):
        fog_calls.append("clear")
        reveal_calls.append(getattr(pc, "name", "pc"))
        return True, "fog once"

    ns["_max_all_for_player_controller"] = stub_boost
    ns["_apply_max_all_session_fog"] = stub_fog

    yield ns, boost_calls, fog_calls, reveal_calls


def test_max_all_for_party_indices_applies_fog_once(max_all_env):
    ns, boost_calls, fog_calls, reveal_calls = max_all_env
    result = ns["max_all_for_party_indices"]([0, 1])
    assert result["ok"] is True
    assert result["ok_count"] == 2
    assert len(boost_calls) == 2
    assert all(":fog=False" in call for call in boost_calls)
    assert fog_calls == ["clear"]
    assert reveal_calls == ["P1"]


def test_normalize_party_indices_dedupes(max_all_env):
    ns, *_rest = max_all_env
    assert ns["_normalize_party_indices"]([0, 0, 1, -1, "2"]) == [0, 1, 2]


def test_max_all_dispatches_party_payload(max_all_env):
    ns, boost_calls, fog_calls, _ = max_all_env
    result = ns["max_all"]({"party_indices": [0, 1]})
    assert result["ok"] is True
    assert boost_calls == ["P0:fog=False", "P1:fog=False"]
    assert fog_calls == ["clear"]


def test_max_all_keeps_selected_player_call(max_all_env):
    ns, boost_calls, fog_calls, _ = max_all_env
    ns["_selected_player_index"] = 1
    ns["_selected_player_name"] = "Guest"
    ns["_selected_player_label"] = lambda idx, name: name
    result = ns["max_all"]({})
    assert result["ok"] is True
    assert boost_calls == ["P1:fog=True"]
    assert fog_calls == []
