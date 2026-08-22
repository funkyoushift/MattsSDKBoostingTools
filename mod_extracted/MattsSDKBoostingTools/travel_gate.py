"""Tiny travel/join gate. No hooks and no other MSBT imports.

Hot paths (camera tick, Instant Holds, fog, Quick Menu) must import this
module only. Importing runtime_cleanup from a live hook deadlocks oak2 while
MattsSDKBoostingTools is still loading.
"""
from __future__ import annotations

import time

_QUIET_SECONDS = 20.0
_QUIET_UNTIL = 0.0
_PENDING_CLEAR = False


def mark_travel(seconds: float = _QUIET_SECONDS) -> None:
    """Silence UObject scans/writes while the world is tearing down or joining."""
    global _QUIET_UNTIL, _PENDING_CLEAR
    try:
        hold = max(1.0, float(seconds))
    except Exception:
        hold = _QUIET_SECONDS
    _QUIET_UNTIL = max(float(_QUIET_UNTIL or 0.0), time.monotonic() + hold)
    _PENDING_CLEAR = True


def is_travel_quiet() -> bool:
    """True during ClientTravel / join. Hot paths must not find_all or write UObjects."""
    try:
        return time.monotonic() < float(_QUIET_UNTIL or 0.0)
    except Exception:
        return False


def consume_pending_clear() -> bool:
    """True once after travel quiet expires, so caches can drop old-world wrappers."""
    global _PENDING_CLEAR
    if not _PENDING_CLEAR or is_travel_quiet():
        return False
    _PENDING_CLEAR = False
    return True
