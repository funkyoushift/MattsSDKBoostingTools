"""Small opt-in runtime profiling helpers for MSBT.

Profiling is disabled by default and deliberately keeps only bounded aggregate
state so it is safe to leave imported in the in-game runtime.
"""
from __future__ import annotations

import os
import threading
from collections import OrderedDict
from typing import Any

ENABLED = str(os.environ.get("MSBT_PERF", "")).strip().lower() in ("1", "true", "yes", "on")
MAX_KEYS = 256

_lock = threading.RLock()
_calls: OrderedDict[str, dict[str, float | int]] = OrderedDict()
_counters: OrderedDict[str, int | float] = OrderedDict()


def set_enabled(enabled: object) -> None:
    """Enable or disable collection at runtime."""
    global ENABLED
    ENABLED = bool(enabled)


def _bounded_set(mapping: OrderedDict[str, Any], key: str, value: Any) -> None:
    if key in mapping:
        mapping.move_to_end(key)
    mapping[key] = value
    while len(mapping) > MAX_KEYS:
        mapping.popitem(last=False)


def record_call(name: object, duration_ms: object) -> None:
    """Record aggregate timing for one named operation."""
    if not ENABLED:
        return
    key = str(name or "unknown")
    try:
        duration = max(0.0, float(duration_ms))
    except Exception:
        return
    with _lock:
        previous = _calls.get(key)
        if previous is None:
            stats: dict[str, float | int] = {
                "count": 1,
                "total_ms": duration,
                "min_ms": duration,
                "max_ms": duration,
                "last_ms": duration,
            }
        else:
            count = int(previous.get("count", 0)) + 1
            total = float(previous.get("total_ms", 0.0)) + duration
            stats = {
                "count": count,
                "total_ms": total,
                "min_ms": min(float(previous.get("min_ms", duration)), duration),
                "max_ms": max(float(previous.get("max_ms", duration)), duration),
                "last_ms": duration,
            }
        _bounded_set(_calls, key, stats)


def set_counter(name: object, value: object) -> None:
    """Set a bounded numeric gauge such as bridge queue/result size."""
    if not ENABLED:
        return
    key = str(name or "unknown")
    try:
        numeric: int | float = int(value)
    except Exception:
        try:
            numeric = float(value)
        except Exception:
            return
    with _lock:
        _bounded_set(_counters, key, numeric)


def record_bridge_sizes(queue_size: object, results_size: object) -> None:
    set_counter("bridge.queue_size", queue_size)
    set_counter("bridge.results_size", results_size)


def get_stats() -> dict[str, Any]:
    """Return a detached snapshot of timings and counters."""
    with _lock:
        calls: dict[str, dict[str, float | int]] = {}
        for name, values in _calls.items():
            row = dict(values)
            count = max(1, int(row.get("count", 1)))
            row["avg_ms"] = float(row.get("total_ms", 0.0)) / count
            calls[name] = row
        return {
            "enabled": ENABLED,
            "calls": calls,
            "counters": dict(_counters),
        }


def reset_stats() -> None:
    with _lock:
        _calls.clear()
        _counters.clear()
