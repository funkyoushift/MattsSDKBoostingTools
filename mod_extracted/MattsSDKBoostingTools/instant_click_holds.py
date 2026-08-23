"""MSBT Instant Click Holds — turn hold-to-confirm into a simple click.

Port of tools/InstantClickHolds. Enhanced Input holds are client-local; MSBT
toggles apply on the machine running the mod. Guests need their own client apply
(or the standalone InstantClickHolds mod). Starts OFF until toggled from MSBT.

Two independent toggles:
- Instant Drops: drop-item action only (fast path, no full find_all).
- Instant Holds: all allowed UI / skill / world holds (full scan + maintain).
"""

from __future__ import annotations

import time
from typing import Any

from mods_base import EInputEvent, hook, keybind
from unrealsdk import find_all, find_object, logging
from unrealsdk.hooks import Type

__version__ = "0.1.5"
__version_info__ = (0, 1, 5)

_PREFIX = "[Matts SDK Boosting Tools | ICH]"

# Original HoldTimeThreshold keyed by a stable-ish object identity string.
_ORIGINAL: dict[str, float] = {}
# Original bIsOneShot (UI holds are one-shot; that fights drop-spam after reset).
_ORIGINAL_ONESHOT: dict[str, bool] = {}

# Continuous re-apply state (UI recreates/resets holds after each drop).
_TICK = 0
_LAST_REAPPLY_LOG_TICK = 0
_LAST_PATCHED = 0
_LAST_SKIPPED = 0
_LAST_MAINTAIN_REASON = ""

# Tick hooks have overlapping path aliases and can fire more than once per
# frame. Use wall-clock gates so alias/player/viewport frequency cannot turn
# maintenance into repeated global UObject scans.
_FAST_MAINTAIN_INTERVAL_S = 0.5
_FULL_MAINTAIN_INTERVAL_S = 2.0
_LAST_FAST_MAINTAIN_AT = 0.0
_LAST_FULL_MAINTAIN_AT = 0.0

# Known UI drop action — patched first on every maintain (no full scan needed).
_DROP_ACTION_PATHS = (
    "/Game/UI/Data/input/action_ui_drop_item.action_ui_drop_item",
    "GbxEnhancedInputAction'/Game/UI/Data/input/action_ui_drop_item.action_ui_drop_item'",
)

# Independent toggles (both start OFF).
_drops_enabled = False
_holds_enabled = False
_threshold = 0.0
_include_ui = True
_include_skills = True
_include_world = True


def _log(msg: str) -> None:
    try:
        logging.info(f"{_PREFIX} {msg}")
    except Exception:
        print(f"{_PREFIX} {msg}")


_hot_error_last_at: dict[str, float] = {}


def _log_hot_error(msg: str) -> None:
    now = time.monotonic()
    if now - _hot_error_last_at.get(msg, 0.0) < 5.0:
        return
    _hot_error_last_at[msg] = now
    _log(msg)


def _obj_key(obj: Any) -> str:
    try:
        return str(obj)
    except Exception:
        return repr(obj)


def _class_name(obj: Any) -> str:
    try:
        cls = getattr(obj, "Class", None)
        name = getattr(cls, "Name", None) if cls is not None else None
        if name is not None:
            return str(name)
    except Exception:
        pass
    try:
        return str(getattr(obj, "Class", "") or "")
    except Exception:
        return ""


def _read_threshold(obj: Any) -> float | None:
    for attr in ("HoldTimeThreshold", "hold_time_threshold", "HoldDuration", "HoldTime"):
        try:
            value = getattr(obj, attr)
        except Exception:
            continue
        try:
            return float(value)
        except Exception:
            continue
    return None


def _write_threshold(obj: Any, value: float) -> bool:
    for attr in ("HoldTimeThreshold", "hold_time_threshold", "HoldDuration", "HoldTime"):
        try:
            getattr(obj, attr)
        except Exception:
            continue
        try:
            setattr(obj, attr, float(value))
            return True
        except Exception:
            continue
    return False


def _read_oneshot(obj: Any) -> bool | None:
    for attr in ("bIsOneShot", "IsOneShot", "is_one_shot"):
        try:
            value = getattr(obj, attr)
        except Exception:
            continue
        try:
            return bool(value)
        except Exception:
            continue
    return None


def _write_oneshot(obj: Any, value: bool) -> bool:
    for attr in ("bIsOneShot", "IsOneShot", "is_one_shot"):
        try:
            getattr(obj, attr)
        except Exception:
            continue
        try:
            setattr(obj, attr, bool(value))
            return True
        except Exception:
            continue
    return False


def _reset_held_duration(obj: Any) -> bool:
    """Clear TimedBase held duration so the next press can re-arm."""
    ok = False
    for attr in ("HeldDuration", "held_duration"):
        try:
            getattr(obj, attr)
        except Exception:
            continue
        try:
            setattr(obj, attr, 0.0)
            ok = True
        except Exception:
            continue
    return ok


def _is_drop_path(path: str) -> bool:
    lower = path.lower()
    return (
        "action_ui_drop_item" in lower
        or "equip.dropitem" in lower
        or "dropitem" in lower and "action_ui_" in lower
    )


def _outer_chain_text(obj: Any, *, depth: int = 6) -> str:
    """Concatenate Outer / OuterMost path hints for drop-action detection."""
    bits: list[str] = []
    cur = obj
    for _ in range(max(1, depth)):
        if cur is None:
            break
        try:
            bits.append(str(cur))
        except Exception:
            pass
        nxt = None
        for attr in ("Outer", "outer", "Owner", "owner"):
            try:
                nxt = getattr(cur, attr, None)
            except Exception:
                nxt = None
            if nxt is not None and nxt is not cur:
                break
        if nxt is None or nxt is cur:
            break
        cur = nxt
    return " ".join(bits)


def _is_drop_trigger(obj: Any) -> bool:
    """True if this InputTriggerHold belongs to the UI drop-item action."""
    if obj is None:
        return False
    path = _obj_key(obj)
    if _is_drop_path(path):
        return True
    return _is_drop_path(_outer_chain_text(obj))


def _path_allowed(path: str) -> bool:
    lower = path.lower()

    # Engine CDOs: allow hold-trigger defaults so reinstanced triggers inherit 0.
    if "default__" in lower:
        return "inputtriggerhold" in lower

    # Skip non-CDO /Script engine objects.
    if "/script/" in lower:
        return False

    is_ui = "/game/ui/" in lower or "action_ui_" in lower
    is_skill = (
        "action_skill_hold" in lower
        or "action_gadgethold" in lower
        or "action_giveup" in lower
        or "gadgethold" in lower
    )
    is_world = (
        "context_sensitive" in lower
        or "action_context_sensitive_prompt" in lower
        or "/gamedata/input/" in lower
    )

    if is_ui:
        return bool(_include_ui)
    if is_skill:
        return bool(_include_skills)
    if is_world:
        return bool(_include_world)
    return bool(_include_ui and _include_skills and _include_world)


def _is_ui_path(path: str) -> bool:
    lower = path.lower()
    return "/game/ui/" in lower or "action_ui_" in lower or "default__inputtriggerhold" in lower


def _find_all_class(class_name: str, *, include_default: bool) -> list[Any]:
    attempts = (True, False) if include_default else (False,)
    for include in attempts:
        try:
            return list(find_all(class_name, include))
        except TypeError:
            try:
                return list(find_all(class_name))
            except Exception:
                return []
        except Exception:
            continue
    return []


def _iter_hold_triggers() -> list[Any]:
    found: list[Any] = []
    seen: set[str] = set()

    def _add(obj: Any) -> None:
        if obj is None:
            return
        key = _obj_key(obj)
        if key in seen:
            return
        seen.add(key)
        found.append(obj)

    for class_name in ("InputTriggerHold", "InputTriggerHoldAndRelease"):
        for obj in _find_all_class(class_name, include_default=True):
            _add(obj)

    for class_name in ("GbxEnhancedInputAction", "InputAction", "EnhancedInputAction"):
        for action in _find_all_class(class_name, include_default=False):
            try:
                triggers = list(getattr(action, "Triggers", []) or [])
            except Exception:
                triggers = []
            for trigger in triggers:
                cls = _class_name(trigger).lower()
                if "hold" in cls:
                    _add(trigger)

    return found


def _iter_drop_triggers() -> list[Any]:
    """Resolve the live drop-item hold trigger(s) without a full class scan."""
    found: list[Any] = []
    seen: set[str] = set()

    def _add(obj: Any) -> None:
        if obj is None:
            return
        key = _obj_key(obj)
        if key in seen:
            return
        seen.add(key)
        found.append(obj)

    for path in _DROP_ACTION_PATHS:
        action = None
        try:
            action = find_object("GbxEnhancedInputAction", path)
        except Exception:
            action = None
        if action is None:
            try:
                action = find_object("Object", path)
            except Exception:
                action = None
        if action is None:
            continue
        try:
            triggers = list(getattr(action, "Triggers", []) or [])
        except Exception:
            triggers = []
        for trigger in triggers:
            cls = _class_name(trigger).lower()
            if "hold" in cls:
                _add(trigger)

    # Named subobject path seen live in Twitch probe dumps.
    for sub in (
        "/Game/UI/Data/input/action_ui_drop_item.action_ui_drop_item:InputTriggerHold_0",
        "InputTriggerHold'/Game/UI/Data/input/action_ui_drop_item.action_ui_drop_item:InputTriggerHold_0'",
    ):
        try:
            obj = find_object("InputTriggerHold", sub)
        except Exception:
            obj = None
        if obj is None:
            try:
                obj = find_object("Object", sub)
            except Exception:
                obj = None
        _add(obj)

    # Fallback: scan live hold triggers whose Outer chain mentions drop-item.
    # Needed when UI recreates the trigger under a new instance path.
    if not found:
        for class_name in ("InputTriggerHold", "InputTriggerHoldAndRelease"):
            for obj in _find_all_class(class_name, include_default=True):
                if _is_drop_trigger(obj):
                    _add(obj)

    # Always include the engine CDO so reinherited UI holds start at 0.
    for class_name in ("InputTriggerHold", "InputTriggerHoldAndRelease"):
        for obj in _find_all_class(class_name, include_default=True):
            path = _obj_key(obj).lower()
            if "default__" in path and "inputtriggerhold" in path:
                _add(obj)

    return found


def _patch_one_trigger(
    trigger: Any,
    *,
    target: float,
    force_ui_oneshot_off: bool,
    reset_held: bool,
    allow_drop_bypass: bool = False,
) -> str:
    """Patch a single trigger. Returns 'patched' | 'rewritten' | 'skipped'."""
    path = _obj_key(trigger)
    # Drop triggers resolved via Outer may look like engine subobjects; still allow.
    if not _path_allowed(path) and not (allow_drop_bypass and _is_drop_trigger(trigger)):
        return "skipped"
    current = _read_threshold(trigger)
    if current is None:
        return "skipped"
    if path not in _ORIGINAL:
        _ORIGINAL[path] = current

    rewritten = False
    if abs(current - float(target)) >= 1e-6:
        if not _write_threshold(trigger, float(target)):
            return "skipped"
        rewritten = True

    if force_ui_oneshot_off and (_is_ui_path(path) or _is_drop_trigger(trigger)):
        oneshot = _read_oneshot(trigger)
        if oneshot is not None:
            if path not in _ORIGINAL_ONESHOT:
                _ORIGINAL_ONESHOT[path] = oneshot
            if oneshot and _write_oneshot(trigger, False):
                rewritten = True

    if reset_held:
        _reset_held_duration(trigger)

    return "rewritten" if rewritten else "patched"


def apply_holds(
    *,
    target: float | None = None,
    quiet: bool = False,
    fast_only: bool = False,
    reset_held: bool = False,
) -> tuple[int, int]:
    """Apply hold threshold. Returns (patched, skipped)."""
    global _LAST_PATCHED, _LAST_SKIPPED
    if target is None:
        if not (_drops_enabled or _holds_enabled):
            return restore_holds()
        target = float(_threshold)

    patched = 0
    skipped = 0
    rewritten = 0

    triggers = _iter_drop_triggers() if fast_only else _iter_hold_triggers()
    if not fast_only:
        # Always include drop triggers even if find_all missed nested ones.
        for t in _iter_drop_triggers():
            key = _obj_key(t)
            if all(_obj_key(x) != key for x in triggers):
                triggers.append(t)

    for trigger in triggers:
        result = _patch_one_trigger(
            trigger,
            target=float(target),
            force_ui_oneshot_off=bool(_include_ui),
            reset_held=reset_held,
            allow_drop_bypass=bool(fast_only or _is_drop_trigger(trigger)),
        )
        if result == "skipped":
            skipped += 1
        elif result == "rewritten":
            patched += 1
            rewritten += 1
        else:
            patched += 1

    _LAST_PATCHED = patched
    _LAST_SKIPPED = skipped
    if rewritten and not quiet:
        _log(f"rewrote {rewritten} hold threshold(s) → {float(target):.3f}s")
    return patched, skipped


def restore_holds() -> tuple[int, int]:
    """Restore backed-up stock thresholds / one-shot flags. Returns (restored, missing)."""
    restored = 0
    missing = 0
    live = {_obj_key(obj): obj for obj in _iter_hold_triggers()}
    for path, original in list(_ORIGINAL.items()):
        obj = live.get(path)
        if obj is None:
            missing += 1
            continue
        ok = _write_threshold(obj, float(original))
        if path in _ORIGINAL_ONESHOT:
            ok = _write_oneshot(obj, bool(_ORIGINAL_ONESHOT[path])) or ok
        if ok:
            restored += 1
        else:
            missing += 1
    return restored, missing


def _restore_drop_triggers() -> tuple[int, int]:
    """Restore known drop triggers only (no full find_all)."""
    restored = 0
    missing = 0
    try:
        for trigger in _iter_drop_triggers():
            key = _obj_key(trigger)
            if key not in _ORIGINAL:
                missing += 1
                continue
            ok = _write_threshold(trigger, float(_ORIGINAL[key]))
            if key in _ORIGINAL_ONESHOT:
                ok = _write_oneshot(trigger, bool(_ORIGINAL_ONESHOT[key])) or ok
            if ok:
                restored += 1
            else:
                missing += 1
    except Exception as exc:
        _log(f"fast drop restore failed (menu/no world ok): {exc!r}")
    return restored, missing


def _restore_non_drop_holds(*, also_restore_drops: bool) -> tuple[int, int]:
    """Restore backed-up non-drop holds; optionally drops too when Instant Drops is OFF."""
    restored = 0
    missing = 0
    try:
        live = {_obj_key(obj): obj for obj in _iter_hold_triggers()}
    except Exception as exc:
        _log(f"non-drop restore deferred (menu/no world): {exc!r}")
        return 0, 0
    for path, original in list(_ORIGINAL.items()):
        if _is_drop_path(path) and not also_restore_drops:
            continue
        obj = live.get(path)
        if obj is None:
            missing += 1
            continue
        ok = _write_threshold(obj, float(original))
        if path in _ORIGINAL_ONESHOT:
            ok = _write_oneshot(obj, bool(_ORIGINAL_ONESHOT[path])) or ok
        if ok:
            restored += 1
        else:
            missing += 1
    return restored, missing


def _should_maintain() -> bool:
    if not bool(_drops_enabled or _holds_enabled):
        return False
    try:
        from .travel_gate import is_travel_quiet

        if is_travel_quiet():
            return False
    except Exception:
        pass
    return True


def _maintain_holds(
    *,
    force_log: bool = False,
    reason: str = "",
    fast_only: bool = False,
    reset_held: bool = False,
) -> None:
    """Re-scan and force thresholds while Instant Drops and/or Instant Holds is ON."""
    global _LAST_REAPPLY_LOG_TICK, _LAST_MAINTAIN_REASON, _TICK
    if not _should_maintain():
        return
    _LAST_MAINTAIN_REASON = reason or _LAST_MAINTAIN_REASON
    patched, skipped = apply_holds(quiet=True, fast_only=fast_only, reset_held=reset_held)
    if force_log or (_TICK - _LAST_REAPPLY_LOG_TICK) >= 600:
        _LAST_REAPPLY_LOG_TICK = _TICK
        suffix = f" ({reason})" if reason else ""
        mode = "fast" if fast_only else "full"
        _log(f"maintain{suffix} [{mode}] — patched={patched} skipped={skipped}")


def _bump_tick_and_maintain(reason: str, *, prefer_full: bool = False) -> None:
    global _TICK, _LAST_FAST_MAINTAIN_AT, _LAST_FULL_MAINTAIN_AT
    if not _should_maintain():
        return
    _TICK += 1
    now = time.monotonic()

    if _holds_enabled:
        # PlayerTick requests full coverage, but it must not bypass the wall-clock
        # gate. UpdateState and explicit key/menu hooks handle immediate changes.
        if prefer_full and now - _LAST_FULL_MAINTAIN_AT >= _FULL_MAINTAIN_INTERVAL_S:
            _LAST_FULL_MAINTAIN_AT = now
            try:
                _maintain_holds(reason=reason, fast_only=False)
            except Exception as exc:
                _log_hot_error(f"{reason} full maintain failed: {exc!r}")
        elif _drops_enabled and now - _LAST_FAST_MAINTAIN_AT >= _FAST_MAINTAIN_INTERVAL_S:
            _LAST_FAST_MAINTAIN_AT = now
            try:
                _maintain_holds(reason=reason, fast_only=True)
            except Exception as exc:
                _log_hot_error(f"{reason} fast maintain failed: {exc!r}")
        return

    if _drops_enabled and now - _LAST_FAST_MAINTAIN_AT >= _FAST_MAINTAIN_INTERVAL_S:
        _LAST_FAST_MAINTAIN_AT = now
        try:
            _maintain_holds(reason=reason, fast_only=True)
        except Exception as exc:
            _log_hot_error(f"{reason} fast maintain failed: {exc!r}")


# ---------------------------------------------------------------------------
# Instant Drops (drop-item fast path) — public API used by backend_actions
# ---------------------------------------------------------------------------

def on_enable() -> None:
    """Enable Instant Drops (drop-item only). Leaves Instant Holds alone."""
    global _drops_enabled, _TICK, _LAST_REAPPLY_LOG_TICK, _LAST_FAST_MAINTAIN_AT
    _drops_enabled = True
    _TICK = 0
    _LAST_REAPPLY_LOG_TICK = 0
    _LAST_FAST_MAINTAIN_AT = time.monotonic()
    patched = 0
    skipped = 0
    try:
        patched, skipped = apply_holds(fast_only=True, quiet=True)
    except Exception as exc:
        _log(f"drops enable apply deferred (menu/no world): {exc!r}")
    _log(
        f"Instant Drops enabled v{__version__} — armed; fast patched={patched} skipped={skipped} "
        f"(holds_enabled={bool(_holds_enabled)})"
    )


def on_disable() -> None:
    """Disable Instant Drops. Leaves Instant Holds alone."""
    global _drops_enabled
    _drops_enabled = False
    if _holds_enabled:
        # Instant Holds still owns full scan (including drop UI); do not restore drops.
        _log("Instant Drops disabled — Instant Holds still ON; drop restore skipped")
        return
    restored, missing = _restore_drop_triggers()
    _log(f"Instant Drops disabled — fast restored={restored} missing={missing}")


def set_enabled(enabled: bool) -> str:
    if enabled:
        on_enable()
        return (
            f"Instant drops ARMED threshold={float(_threshold):.3f}s "
            "(applies in-session when holds exist; client-local)"
        )
    on_disable()
    return "Instant drops OFF"


def toggle_enabled() -> str:
    return set_enabled(not bool(_drops_enabled))


def set_threshold(seconds: float) -> str:
    global _threshold
    try:
        val = float(seconds)
    except Exception:
        return "Hold threshold must be a number."
    _threshold = max(0.0, min(2.0, val))
    if _drops_enabled:
        apply_holds(fast_only=True, quiet=True)
    elif _holds_enabled:
        apply_holds(fast_only=False, quiet=True)
    return f"Hold threshold set to {float(_threshold):.3f}s"


def get_status_dict() -> dict[str, Any]:
    return {
        "enabled": bool(_drops_enabled),
        "threshold": float(_threshold),
        # Avoid find_all on /status — it races the bridge game tick.
        "triggers": int(_LAST_PATCHED + _LAST_SKIPPED) if (_LAST_PATCHED or _LAST_SKIPPED) else len(_ORIGINAL),
        "backed_up": len(_ORIGINAL),
        "ui": bool(_include_ui),
        "skills": bool(_include_skills),
        "world": bool(_include_world),
        "ticks": int(_TICK),
        "last_patched": int(_LAST_PATCHED),
        "last_reason": str(_LAST_MAINTAIN_REASON),
        "scope": "client_local",
        "mode": "drops_fast",
        "caveat": "Enhanced Input holds are client-local; guests need MSBT/InstantClickHolds on their machine.",
    }


def clear_travel_backups() -> None:
    """Forget originals belonging to the unloaded world."""
    _ORIGINAL.clear()
    _ORIGINAL_ONESHOT.clear()


def status_message() -> str:
    st = get_status_dict()
    return (
        f"Instant drops enabled={st['enabled']} threshold={st['threshold']:.3f}s "
        f"last_patched={st['last_patched']} (client-local; guests need own apply)"
    )


def reapply() -> str:
    if _holds_enabled:
        patched, skipped = apply_holds(fast_only=False)
    else:
        patched, skipped = apply_holds(fast_only=True)
    return f"Instant drops re-apply patched={patched} skipped={skipped}. {status_message()}"


# ---------------------------------------------------------------------------
# Instant Holds (UI / skill / world full scan) — separate toggle
# ---------------------------------------------------------------------------

def on_holds_enable() -> None:
    """Enable Instant Holds (all allowed hold triggers). Leaves Instant Drops alone."""
    global _holds_enabled, _TICK, _LAST_REAPPLY_LOG_TICK, _LAST_FULL_MAINTAIN_AT
    _holds_enabled = True
    _TICK = 0
    _LAST_REAPPLY_LOG_TICK = 0
    _LAST_FULL_MAINTAIN_AT = time.monotonic()
    patched = 0
    skipped = 0
    try:
        patched, skipped = apply_holds(fast_only=False, quiet=True)
    except Exception as exc:
        _log(f"holds enable apply deferred (menu/no world): {exc!r}")
    _log(
        f"Instant Holds enabled v{__version__} — armed; full patched={patched} skipped={skipped} "
        f"(drops_enabled={bool(_drops_enabled)})"
    )


def on_holds_disable() -> None:
    """Disable Instant Holds. Leaves Instant Drops alone."""
    global _holds_enabled
    _holds_enabled = False
    also_drops = not bool(_drops_enabled)
    restored, missing = _restore_non_drop_holds(also_restore_drops=also_drops)
    _log(
        f"Instant Holds disabled — restored={restored} missing={missing} "
        f"(also_drops={also_drops}; drops_enabled={bool(_drops_enabled)})"
    )


def set_holds_enabled(enabled: bool) -> str:
    if enabled:
        on_holds_enable()
        return (
            f"Instant holds ARMED threshold={float(_threshold):.3f}s "
            "(UI/skill/world; applies in-session; client-local)"
        )
    on_holds_disable()
    return "Instant holds OFF"


def toggle_holds_enabled() -> str:
    return set_holds_enabled(not bool(_holds_enabled))


def get_holds_status_dict() -> dict[str, Any]:
    return {
        "enabled": bool(_holds_enabled),
        "threshold": float(_threshold),
        "triggers": int(_LAST_PATCHED + _LAST_SKIPPED) if (_LAST_PATCHED or _LAST_SKIPPED) else len(_ORIGINAL),
        "backed_up": len(_ORIGINAL),
        "ui": bool(_include_ui),
        "skills": bool(_include_skills),
        "world": bool(_include_world),
        "ticks": int(_TICK),
        "last_patched": int(_LAST_PATCHED),
        "last_reason": str(_LAST_MAINTAIN_REASON),
        "scope": "client_local",
        "mode": "holds_full",
        "caveat": "Enhanced Input holds are client-local; guests need MSBT/InstantClickHolds on their machine.",
    }


def holds_status_message() -> str:
    st = get_holds_status_dict()
    return (
        f"Instant holds enabled={st['enabled']} threshold={st['threshold']:.3f}s "
        f"last_patched={st['last_patched']} (client-local; guests need own apply)"
    )


def _on_drop_key_pressed() -> None:
    if _drops_enabled:
        # reset_held: inventory recreates/resets holds between presses
        _maintain_holds(reason="drop-key", fast_only=True, reset_held=True)
    elif _holds_enabled:
        _maintain_holds(reason="drop-key", fast_only=True, reset_held=True)


def _toggle_drops_keybind() -> None:
    _log(toggle_enabled())


def _toggle_holds_keybind() -> None:
    _log(toggle_holds_enabled())


kb_toggle_drops = keybind(
    "MSBT Toggle Instant Drops",
    None,
    callback=_toggle_drops_keybind,
    display_name="MSBT Toggle Instant Drops",
    description="Toggle the client-local Instant Drops fast path. Assign or clear this key in oak2's Mods keybind UI.",
    event_filter=EInputEvent.IE_Pressed,
)

kb_toggle_holds = keybind(
    "MSBT Toggle Instant Holds",
    None,
    callback=_toggle_holds_keybind,
    display_name="MSBT Toggle Instant Holds",
    description="Toggle client-local Instant Holds for UI, skill, and world interactions. Assign or clear this key in oak2's Mods keybind UI.",
    event_filter=EInputEvent.IE_Pressed,
)


kb_maintain_r = keybind(
    "MSBT ICH maintain on R",
    "R",
    callback=_on_drop_key_pressed,
    display_name="MSBT ICH maintain on R",
    description="Internal: re-apply drop hold threshold on R press (works in inventory).",
    is_hidden=True,
    is_rebindable=False,
    event_filter=EInputEvent.IE_Pressed,
)

kb_maintain_gamepad = keybind(
    "MSBT ICH maintain on gamepad drop",
    "Gamepad_FaceButton_Top",
    callback=_on_drop_key_pressed,
    display_name="MSBT ICH maintain on gamepad drop",
    description="Internal: re-apply drop hold threshold on Y / Triangle press.",
    is_hidden=True,
    is_rebindable=False,
    event_filter=EInputEvent.IE_Pressed,
)


@hook("/Script/EnhancedInput.InputTriggerHold:UpdateState", Type.PRE, immediately_enable=False, hook_identifier="msbt_ich_hold_update_v1")
@hook("/Script/EnhancedInput.InputTriggerHoldAndRelease:UpdateState", Type.PRE, immediately_enable=False, hook_identifier="msbt_ich_holdrel_update_v1")
@hook("EnhancedInput.InputTriggerHold:UpdateState", Type.PRE, immediately_enable=False, hook_identifier="msbt_ich_hold_update_alt_v1")
@hook("EnhancedInput.InputTriggerHoldAndRelease:UpdateState", Type.PRE, immediately_enable=False, hook_identifier="msbt_ich_holdrel_update_alt_v1")
@hook("/Script/EnhancedInput.InputTrigger:UpdateState", Type.PRE, immediately_enable=False, hook_identifier="msbt_ich_trigger_update_v1")
def _before_trigger_update(obj: Any, *_args: Any, **_kwargs: Any) -> None:
    if not _should_maintain():
        return
    # Instant Drops only: patch this trigger if it belongs to drop-item (Outer-aware).
    # Instant Holds: patch any allowed hold.
    if _holds_enabled:
        allow = True
        drop_bypass = False
    elif _drops_enabled:
        allow = _is_drop_trigger(obj)
        drop_bypass = True
    else:
        return
    if not allow:
        return
    target = float(_threshold)
    _patch_one_trigger(
        obj,
        target=target,
        force_ui_oneshot_off=bool(_include_ui),
        reset_held=False,
        allow_drop_bypass=drop_bypass,
    )


@hook("/Script/Engine.GameViewportClient:Tick", Type.POST, immediately_enable=False, hook_identifier="msbt_ich_viewport_v1")
@hook("/Script/OakGame.OakGameViewportClient:Tick", Type.POST, immediately_enable=False, hook_identifier="msbt_ich_viewport_oak_v1")
@hook("Engine.GameViewportClient:Tick", Type.POST, immediately_enable=False, hook_identifier="msbt_ich_viewport_alt_v1")
@hook("OakGame.OakGameViewportClient:Tick", Type.POST, immediately_enable=False, hook_identifier="msbt_ich_viewport_oak_alt_v1")
def _viewport_tick(*_args: Any, **_kwargs: Any) -> None:
    _bump_tick_and_maintain("viewport", prefer_full=False)


@hook("OakGame.OakPlayerController:ClientTravel", Type.POST, immediately_enable=False, hook_identifier="msbt_ich_travel_oak_v1")
@hook("Engine.PlayerController:ClientTravel", Type.POST, immediately_enable=False, hook_identifier="msbt_ich_travel_engine_v1")
def _after_travel(*_args: Any, **_kwargs: Any) -> None:
    # ClientTravel is world teardown. Forget old wrappers; do not find_all here.
    clear_travel_backups()


@hook("OakGame.OakPlayerController:PlayerTick", Type.POST, immediately_enable=False, hook_identifier="msbt_ich_ptick_oak_v1")
@hook("Engine.PlayerController:PlayerTick", Type.POST, immediately_enable=False, hook_identifier="msbt_ich_ptick_engine_v1")
def _player_tick(*_args: Any, **_kwargs: Any) -> None:
    _bump_tick_and_maintain("player", prefer_full=True)


@hook("/Game/UI/Scripts/ui_script_backpack.ui_script_backpack_C:DropItem", Type.PRE, immediately_enable=False, hook_identifier="msbt_ich_drop_bp_pre_v1")
@hook("/Game/UI/Scripts/ui_script_backpack.ui_script_backpack_C:DropItem", Type.POST, immediately_enable=False, hook_identifier="msbt_ich_drop_bp_post_v1")
@hook("/Script/OakGame.OakUIScript_Backpack:DropItem", Type.PRE, immediately_enable=False, hook_identifier="msbt_ich_drop_oak_pre_v1")
@hook("/Script/OakGame.OakUIScript_Backpack:DropItem", Type.POST, immediately_enable=False, hook_identifier="msbt_ich_drop_oak_post_v1")
@hook("OakGame.OakUIScript_Backpack:DropItem", Type.PRE, immediately_enable=False, hook_identifier="msbt_ich_drop_oak2_pre_v1")
@hook("OakGame.OakUIScript_Backpack:DropItem", Type.POST, immediately_enable=False, hook_identifier="msbt_ich_drop_oak2_post_v1")
def _around_backpack_drop(*_args: Any, **_kwargs: Any) -> None:
    if _drops_enabled or _holds_enabled:
        _maintain_holds(reason="drop", fast_only=True, reset_held=True)


@hook("OakGame.OakPlayerController:OpenInventoryMenu", Type.POST, immediately_enable=False, hook_identifier="msbt_ich_inv_oak_v1")
@hook("Engine.PlayerController:OpenInventoryMenu", Type.POST, immediately_enable=False, hook_identifier="msbt_ich_inv_engine_v1")
def _after_open_inventory(*_args: Any, **_kwargs: Any) -> None:
    if _holds_enabled:
        _maintain_holds(force_log=True, reason="inventory-open", fast_only=False, reset_held=True)
    elif _drops_enabled:
        _maintain_holds(force_log=True, reason="inventory-open", fast_only=True, reset_held=True)


ICH_KEYBINDS = (
    kb_toggle_drops,
    kb_toggle_holds,
    kb_maintain_r,
    kb_maintain_gamepad,
)

_log(f"loaded v{__version__} (MSBT helper, Instant Drops + Instant Holds start OFF; client-local)")
