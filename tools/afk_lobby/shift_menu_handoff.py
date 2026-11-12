"""Observed game-menu handoff for the SHiFT background view.

This module has no Unreal imports. The companion supplies a game-thread
snapshot plus close/resume callbacks; intent never carries a page token.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import itertools
import threading
from typing import Any, Callable, Mapping


def probe_menu_state(sdk: Any, pc: Any) -> bool | None:
    """Return a menu state only when pause and local UI contexts are readable.

    This mirrors the existing background-entry guard and deliberately treats
    an incomplete/ambiguous SDK scan as unknown rather than as gameplay.
    """
    try:
        if pc is None or getattr(pc, "Player", None) is None or getattr(pc, "Pawn", None) is None:
            return None
        stats_class = sdk.find_class("GameplayStatics")
        stats = getattr(stats_class, "ClassDefaultObject", None)
        paused = stats.IsGamePaused(pc) if stats is not None else None
        if type(paused) is not bool:
            return None

        subsystems = list(itertools.islice(
            sdk.find_all("EnhancedInputLocalPlayerSubsystem", False), 129))
        if len(subsystems) > 128:
            return None
        local = [item for item in subsystems
                 if not str(item.Name).startswith("Default__") and item.Outer == pc.Player]
        if len(local) != 1:
            return None
        interface = sdk.find_class("/Script/EnhancedInput.EnhancedInputSubsystemInterface")
        fn = sdk.find_object("Function", "/Script/EnhancedInput.EnhancedInputSubsystemInterface:HasMappingContext")
        if interface is None or fn is None or not local[0].Class._implements(interface):
            return None
        contexts = list(itertools.islice(
            (item for item in sdk.find_all("InputMappingContext", False)
             if not str(item.Name).startswith("Default__")), 129))
        if len(contexts) > 128:
            return None
        bound = sdk.unreal.BoundFunction(fn, local[0])
        has_ui_context = False
        for context in contexts:
            result = bound(context, 0)
            if (not isinstance(result, tuple) or len(result) != 2
                    or type(result[0]) is not bool or type(result[1]) is not int):
                return None
            if not result[0]:
                continue
            path_fn = getattr(context, "_path_name", None)
            path = path_fn() if callable(path_fn) else None
            if not isinstance(path, str):
                return None
            normalized = path.casefold()
            if "/ui/" in normalized and "context_ui_cursor." not in normalized:
                has_ui_context = True
        return paused or has_ui_context
    except Exception:
        return None


@dataclass(frozen=True)
class MenuSnapshot:
    active: bool
    identity: tuple[Any, ...] | None
    menu: bool | None
    connected: bool
    native_state: str = "unknown"
    native_closed: bool = False


class MenuHandoff:
    """Close on a newly observed menu; queue a fresh Start after it closes."""

    CLOSE_STABLE_SECONDS = 0.25

    def __init__(self, snapshot: Callable[[], MenuSnapshot | Mapping[str, Any]],
                 close: Callable[[], bool], resume: Callable[[], bool],
                 clock: Callable[[], float], cancel_resume: Callable[[], None] | None = None):
        self._snapshot_cb = snapshot
        self._close_cb = close
        self._resume_cb = resume
        self._cancel_resume_cb = cancel_resume or (lambda: None)
        self._clock_cb = clock
        self._lock = threading.RLock()
        self._identity: tuple[Any, ...] | None = None
        self._phase = "idle"
        self._menu_false_since: float | None = None
        self._latched = False
        self._close_error = ""
        self._last_clock: float | None = None

    def status(self) -> dict[str, str]:
        """Return presentation metadata only; native state/token stay external."""
        with self._lock:
            result = {"handoff_state": self._phase}
            if self._close_error:
                result["handoff_error"] = self._close_error
            return result

    def tick(self) -> None:
        with self._lock:
            now = self._now()
            if now is None:
                self._cancel_locked(latch=True)
                return
            sample = self._snapshot()
            if sample is None:
                self._cancel_locked(latch=True)
                return

            if self._phase == "idle":
                if sample.menu is False:
                    self._latched = False
                    return
                if (sample.menu is not True or self._latched or not sample.active
                        or not self._valid_identity(sample.identity) or not sample.connected):
                    return
                # Record intent/latch before the callback. A re-entrant explicit
                # Stop/Show/disable must not be overwritten by callback return.
                self._identity = sample.identity
                self._phase = "suspended_menu"
                self._latched = True
                self._menu_false_since = None
                self._close_error = ""
                try:
                    succeeded = self._close_cb() is True
                except Exception:
                    succeeded = False
                if self._phase == "suspended_menu" and self._identity == sample.identity and not succeeded:
                    # BackgroundController owns its bounded stop retries. This
                    # state machine never repeats native Close itself.
                    self._close_error = "close_pending"
                return

            if (sample.identity != self._identity or not sample.connected or sample.menu is None):
                self._cancel_locked(latch=True)
                return

            if self._phase == "resuming" and sample.active and sample.native_state == "active":
                self._identity = None
                self._phase = "idle"
                self._menu_false_since = None
                self._close_error = ""
                self._latched = False
                return
            if self._phase == "suspended_menu":
                if sample.menu:
                    self._menu_false_since = None
                    # A native Close failure may be retried by the controller;
                    # do not start while it remains non-idle or visible.
                    if sample.native_state == "idle" and sample.native_closed:
                        self._close_error = ""
                    elif sample.native_state == "error":
                        self._close_error = "close_failed"
                    return
                if sample.native_state == "error":
                    self._close_error = "close_failed"
                    return
                if sample.native_state != "idle" or not sample.native_closed:
                    self._menu_false_since = None
                    self._close_error = "close_pending"
                    return
                if self._menu_false_since is None:
                    self._menu_false_since = now
                    return
                if now - self._menu_false_since < self.CLOSE_STABLE_SECONDS:
                    return
                # Retain intent until real activation. The callback queues a
                # fresh page command; success here is not activation evidence.
                self._phase = "resuming"
                self._close_error = ""
                try:
                    if self._resume_cb() is not True:
                        self._close_error = "resume_failed"
                except Exception:
                    self._close_error = "resume_failed"
                return

            if self._phase == "resuming":
                # Opening SHiFT for the queued Start temporarily pauses the
                # game. This is expected, not evidence of a new user menu.
                # Native entry checks reject genuine overlapping UI contexts.
                # Explicit Stop/Show, identity and connection checks still cancel.
                if sample.native_state == "error":
                    self._close_error = "resume_failed"

    def on_start(self) -> None:
        """A successful explicit Start is the only operation that rearms."""
        with self._lock:
            self._cancel_locked(latch=False)
            self._latched = False

    def on_stop(self) -> None:
        with self._lock:
            self._cancel_locked(latch=True)

    def on_show(self) -> None:
        with self._lock:
            self._cancel_locked(latch=True)

    def on_disabled(self) -> None:
        with self._lock:
            self._cancel_locked(latch=True)

    def cancel(self) -> None:
        with self._lock:
            self._cancel_locked(latch=True)

    def _cancel_locked(self, *, latch: bool) -> None:
        if self._phase == "resuming":
            self._cancel_resume_locked()
        self._identity = None
        self._phase = "idle"
        self._menu_false_since = None
        self._close_error = ""
        self._latched = latch

    def _cancel_resume_locked(self) -> None:
        try:
            self._cancel_resume_cb()
        except Exception:
            pass

    def _now(self) -> float | None:
        try:
            value = float(self._clock_cb())
        except Exception:
            return None
        if not math.isfinite(value) or (self._last_clock is not None and value < self._last_clock):
            return None
        self._last_clock = value
        return value

    def _snapshot(self) -> MenuSnapshot | None:
        try:
            raw = self._snapshot_cb()
            if isinstance(raw, MenuSnapshot):
                value = raw
            elif isinstance(raw, Mapping):
                value = MenuSnapshot(**raw)
            else:
                return None
        except Exception:
            return None
        if (type(value.active) is not bool or type(value.connected) is not bool
                or (value.menu is not None and type(value.menu) is not bool)
                or (value.native_closed is not True and value.native_closed is not False)
                or not isinstance(value.native_state, str)):
            return None
        if value.identity is not None and not isinstance(value.identity, tuple):
            return None
        return value

    @staticmethod
    def _valid_identity(identity: tuple[Any, ...] | None) -> bool:
        return isinstance(identity, tuple) and bool(identity) and all(part is not None for part in identity)
