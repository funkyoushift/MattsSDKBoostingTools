"""Tiny travel/join gate. No hooks and no other MSBT imports.

Hot paths must import this module only. Default is quiet from boot: title,
join dialog, and ClientTravel all happen before a stable in-world pawn exists.
Quiet lifts only after a real world-load event that followed a ClientTravel.
"""
from __future__ import annotations

import time

_PENDING_CLEAR = False
_SAW_TRAVEL = False
# 0 = stay quiet. >0 = release after this monotonic timestamp.
_RELEASE_AT = 0.0


def mark_travel(seconds: float = 20.0) -> None:
    """Force quiet through title/join/teardown. Does not touch Unreal objects."""
    global _RELEASE_AT, _PENDING_CLEAR, _SAW_TRAVEL
    _SAW_TRAVEL = True
    _RELEASE_AT = 0.0
    _PENDING_CLEAR = True


def mark_menu() -> None:
    """Stay quiet on the title/main menu. Next gameplay load can wake hooks."""
    global _RELEASE_AT, _SAW_TRAVEL
    _SAW_TRAVEL = False
    _RELEASE_AT = 0.0


def saw_travel() -> bool:
    return bool(_SAW_TRAVEL)


def schedule_in_world(delay: float = 8.0) -> None:
    """Allow hot paths after a world-load event that followed ClientTravel."""
    global _RELEASE_AT
    if not _SAW_TRAVEL:
        return
    try:
        wait = max(2.0, float(delay))
    except Exception:
        wait = 8.0
    when = time.monotonic() + wait
    if _RELEASE_AT <= 0.0:
        _RELEASE_AT = when
    else:
        _RELEASE_AT = max(float(_RELEASE_AT), when)


def force_in_world() -> None:
    """Lift boot-stuck quiet so an explicit in-world action can run.

    Quiet stays true until mark_travel + schedule_in_world. A long session
    that never got that pair (or never ClientTravel'd) leaves the camera pump
    off. Party Reveal is a user click in a live world — release immediately.
    Does not clear an in-progress ClientTravel (_PENDING_CLEAR still set).
    """
    global _RELEASE_AT, _SAW_TRAVEL
    _SAW_TRAVEL = True
    try:
        now = time.monotonic()
    except Exception:
        now = 0.0
    if _RELEASE_AT <= 0.0:
        _RELEASE_AT = now
    elif _RELEASE_AT > now:
        _RELEASE_AT = now


def is_travel_quiet() -> bool:
    """True from boot until an in-world release, and again after ClientTravel."""
    try:
        if _RELEASE_AT <= 0.0:
            return True
        return time.monotonic() < float(_RELEASE_AT)
    except Exception:
        return True


def consume_pending_clear() -> bool:
    """True once after quiet ends, so caches can drop old-world wrappers."""
    global _PENDING_CLEAR
    if not _PENDING_CLEAR or is_travel_quiet():
        return False
    _PENDING_CLEAR = False
    return True
