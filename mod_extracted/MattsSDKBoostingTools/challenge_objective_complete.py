"""Complete challenge UI state on PlayerState without copying GPL Challenge Ticker.

Borderlands 4 keeps a replicated ChallengeObjectiveStates array on PlayerState.
Numeric ServerIncrementChallengeForPlayer calls can leave those bits unset, so the
challenge screen still looks incomplete. This module maxes bits on rows that are
already loaded and, when possible, appends a row for a granted token.

Field names are the game's. The control flow is original to MSBT.
"""
from __future__ import annotations

from typing import Any, Iterable

_IDENTIFIER_ATTRS = (
    "ChallengeIdentifier",
    "Identifier",
    "ChallengeName",
    "ChallengeId",
    "Name",
)


def _log(message: str) -> None:
    try:
        from unrealsdk import logging as _sdk_logging

        _sdk_logging.info(f"[Matts SDK Boosting Tools | Challenges] {message}")
    except Exception:
        pass


def _token_key(value: object) -> str:
    return str(value or "").strip().casefold().replace("-", "_")


def _row_token(row: Any) -> str:
    for attr in _IDENTIFIER_ATTRS:
        try:
            raw = getattr(row, attr, None)
        except Exception:
            raw = None
        if raw in (None, ""):
            continue
        text = str(raw)
        for inner in ("Name", "PathName"):
            try:
                nested = getattr(raw, inner, None)
            except Exception:
                nested = None
            if nested not in (None, ""):
                text = str(nested)
                break
        text = text.strip()
        if text:
            return text
    return ""


def _fill_bit_array(bit_array: Any, *, min_slots: int = 4) -> int:
    """Mark every available completed-objective slot as done."""
    if bit_array is None:
        return 0
    writes = 0
    try:
        length = int(len(bit_array))
    except Exception:
        length = 0
    target = max(length, int(min_slots))
    for index in range(target):
        item = None
        if index < length:
            try:
                item = bit_array[index]
            except Exception:
                item = None
        if item is None:
            for candidate in (0xFFFFFFFF, -1, True, 1):
                try:
                    bit_array.append(candidate)
                    writes += 1
                    break
                except Exception:
                    continue
            continue
        filled = False
        for attr in ("Bits", "BitMask", "Value", "CompletedBits"):
            if not hasattr(item, attr):
                continue
            for candidate in (0xFFFFFFFF, -1):
                try:
                    setattr(item, attr, candidate)
                    filled = True
                    writes += 1
                    break
                except Exception:
                    continue
        if filled:
            continue
        if isinstance(item, (int, bool)):
            for candidate in (0xFFFFFFFF, -1, True):
                try:
                    bit_array[index] = candidate
                    writes += 1
                    break
                except Exception:
                    continue
    return writes


def _complete_row(row: Any) -> int:
    writes = 0
    for attr in ("CompletedObjectives", "CompletedBits", "ObjectivesCompleted"):
        try:
            bits = getattr(row, attr, None)
        except Exception:
            bits = None
        if bits is None:
            continue
        filled = _fill_bit_array(bits)
        if filled:
            try:
                setattr(row, attr, bits)
            except Exception:
                pass
            writes += filled
    for flag in ("bCompleted", "Completed", "bIsComplete"):
        if not hasattr(row, flag):
            continue
        try:
            setattr(row, flag, True)
            writes += 1
        except Exception:
            continue
    return writes


def _player_state(controller: Any) -> Any | None:
    if controller is None:
        return None
    try:
        ps = getattr(controller, "PlayerState", None)
    except Exception:
        ps = None
    return ps


def _objective_rows(player_state: Any) -> Any | None:
    if player_state is None:
        return None
    for attr in ("ChallengeObjectiveStates", "ChallengeObjectives", "CompletedChallengeStates"):
        try:
            rows = getattr(player_state, attr, None)
        except Exception:
            rows = None
        if rows is not None:
            return rows
    return None


def _append_objective_row(rows: Any, token: str) -> bool:
    try:
        import unrealsdk
    except Exception:
        return False
    kwargs = {}
    for key in ("ChallengeIdentifier", "Identifier"):
        kwargs[key] = token
        try:
            row = unrealsdk.make_struct("ChallengeObjectiveState", **kwargs)
        except Exception:
            kwargs.pop(key, None)
            continue
        try:
            _complete_row(row)
            rows.append(row)
            return True
        except Exception:
            kwargs.pop(key, None)
            continue
    return False


def complete_loaded_objective_states(
    controller: Any,
    *,
    tokens: Iterable[str] | None = None,
) -> dict[str, int]:
    """Max completed bits on loaded challenge rows.

    If ``tokens`` is set, only matching rows are touched (and missing tokens are
    appended when the game allows it). An empty token list is a no-op. If
    ``tokens`` is None, every loaded row is marked complete.
    """
    report = {"rows": 0, "writes": 0, "appended": 0}
    if tokens is not None:
        wanted = {_token_key(token) for token in tokens if str(token or "").strip()}
        if not wanted:
            return report
    else:
        wanted = set()
    ps = _player_state(controller)
    rows = _objective_rows(ps)
    if rows is None:
        return report
    try:
        report["rows"] = int(len(rows))
    except Exception:
        report["rows"] = 0
    found: set[str] = set()
    try:
        iterator = list(rows)
    except Exception:
        iterator = []
        try:
            for index in range(int(len(rows))):
                iterator.append(rows[index])
        except Exception:
            iterator = []
    for row in iterator:
        token = _row_token(row)
        key = _token_key(token)
        if wanted:
            if not key or key not in wanted:
                continue
        if key:
            found.add(key)
        report["writes"] += _complete_row(row)
    if wanted:
        for token in tokens or []:
            text = str(token or "").strip()
            if not text or _token_key(text) in found:
                continue
            if _append_objective_row(rows, text):
                report["appended"] += 1
                report["writes"] += 1
    return report


def reconcile_after_bulk(controller: Any, granted_tokens: Iterable[str]) -> str:
    granted = [str(token) for token in granted_tokens if str(token or "").strip()]
    if not granted:
        return "objective reconcile skipped: no granted tokens"
    targeted = complete_loaded_objective_states(controller, tokens=granted)
    msg = (
        f"objective reconcile: granted={len(granted)} writes={targeted['writes']} "
        f"appended={targeted['appended']} loaded_rows={targeted['rows']}"
    )
    _log(msg)
    return msg
