"""Opt-in profiling helpers stay bounded and quiet when disabled."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"


def _load_perf():
    sys.modules.pop("MattsSDKBoostingTools.perf_profile", None)
    spec = importlib.util.spec_from_file_location(
        "MattsSDKBoostingTools.perf_profile", PKG / "perf_profile.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["MattsSDKBoostingTools.perf_profile"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_disabled_by_default_and_records_nothing():
    perf = _load_perf()
    perf.set_enabled(False)
    perf.reset_stats()
    perf.record_call("bridge.tick", 12.5)
    perf.set_counter("bridge.queue_size", 3)
    stats = perf.get_stats()
    assert stats["enabled"] is False
    assert stats["calls"] == {}
    assert stats["counters"] == {}


def test_enabled_records_and_bounds_keys():
    perf = _load_perf()
    perf.set_enabled(True)
    perf.reset_stats()
    for index in range(perf.MAX_KEYS + 20):
        perf.record_call(f"call-{index}", float(index))
    stats = perf.get_stats()
    assert stats["enabled"] is True
    assert len(stats["calls"]) == perf.MAX_KEYS
    assert "call-0" not in stats["calls"]
    row = stats["calls"]["call-20"]
    assert row["count"] == 1
    assert row["avg_ms"] == 20.0
    perf.record_bridge_sizes(4, 7)
    counters = perf.get_stats()["counters"]
    assert counters["bridge.queue_size"] == 4
    assert counters["bridge.results_size"] == 7
