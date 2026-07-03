"""Standalone Mattmab-style serial validator for the external app.

This module mirrors the pure validator behavior from blimgui_panel.py without
importing BLImGui, unrealsdk, the SDK bridge, or live-game modules.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Iterable
import re
import time

import external_legit_builder as _legit_builder
from external_serial_tools import human_to_serial, serial_to_human


STATUS_LEGIT = "LEGIT"
STATUS_MODDED = "MODDED"
STATUS_ERROR = "ERROR"


def parse_serial_text(raw: str) -> list[str]:
    """Parse pasted serial input the same way the BLImGui validator does."""
    tokens: list[str] = []
    for line in (raw or "").splitlines():
        text = line.strip()
        if not text:
            continue

        # Human-readable serials contain spaces and pipes. Preserve the full
        # line instead of splitting on punctuation used by the serial grammar.
        if "|" in text:
            tokens.append(text)
            continue

        # If multiple Base85 values were pasted onto one line, split only at a
        # new @U prefix. Base85 itself may contain commas, braces, and symbols.
        starts = [m.start() for m in re.finditer(r"(?=@U)", text)]
        if len(starts) > 1:
            starts.append(len(text))
            for i in range(len(starts) - 1):
                part = text[starts[i]:starts[i + 1]].strip()
                if part:
                    tokens.append(part)
            continue

        tokens.append(text)
    return tokens


def mattmab_validator_label(entry: dict[str, Any]) -> str:
    status = str(entry.get("mattmab_validator", "") or entry.get("status", "")).strip().upper()
    if status in {"PASS", STATUS_LEGIT}:
        return "Mattmab Validation: Legit"
    if status in {"FAIL", STATUS_MODDED}:
        return "Mattmab Validation: Modded"
    if status == STATUS_ERROR:
        return "Mattmab Validation: Error"
    return "Mattmab Validation: not checked"


def mattmab_validator_short(entry: dict[str, Any]) -> str:
    status = str(entry.get("mattmab_validator", "") or entry.get("status", "")).strip().upper()
    if status in {"PASS", STATUS_LEGIT}:
        return "[Legit]"
    if status in {"FAIL", STATUS_MODDED}:
        return "[Modded]"
    if status == STATUS_ERROR:
        return "[Validation Error]"
    return "[Unchecked]"


def validator_definition() -> str:
    return (
        "Mattmab Validation labels: Legit = the serial structure passed the "
        "conservative real-count/rule validator with no hard errors. Modded = "
        "the validator found hard structural problems such as wrong-root parts, "
        "unresolved parts, disallowed selected components, duplicate/slot-count "
        "breaks, or obvious cross-root modded tokens. Error = the serial could "
        "not be parsed/validated. This is a tooling classification, not a "
        "Gearbox/official authenticity guarantee."
    )


def _root_key_for_serial(root_serial: int) -> str | None:
    try:
        rows = list(_legit_builder.roots())
    except Exception:
        rows = []
    for row in rows:
        try:
            if int(row.get("serial") or -1) == int(root_serial):
                return str(row.get("key") or "")
        except Exception:
            continue
    return None


def _human_from_any_serial(text: str) -> str:
    raw = str(text or "").strip()
    if not raw:
        raise ValueError("empty serial")
    if raw.startswith("@U"):
        return serial_to_human(raw)
    if raw.lower().startswith("decoded serial:"):
        return raw.split(":", 1)[1].strip()
    return raw


def _extract_tokens_from_human(human: str) -> tuple[int, int, list[str]]:
    h = str(human or "").strip()
    match = re.match(r"\s*(\d+)\s*,\s*\d+\s*,\s*\d+\s*,\s*(\d+)\s*\|", h)
    if not match:
        raise ValueError("could not parse root serial/level from decoded serial")
    root_serial = int(match.group(1))
    level = int(match.group(2))
    tokens = re.findall(r"\{[^}]+\}", h)
    return root_serial, level, tokens


def _token_list_values(token: str) -> list[int]:
    match = re.match(r"\{\s*\d+(?::\d+)?\s*:\s*\[([^\]]*)\]\s*\}", str(token or ""))
    if not match:
        return []
    vals: list[int] = []
    for part in re.findall(r"-?\d+", match.group(1)):
        try:
            vals.append(int(part))
        except Exception:
            pass
    return vals


def _token_index(token: str) -> str:
    match = re.match(r"\{\s*(\d+)(?:\s*:\s*(?:\[|[-]?\d+))?", str(token or ""))
    return match.group(1) if match else ""


def _cosmetic_selector_count(human: str) -> int:
    return len(re.findall(r'(?i)(?:^|[|,]\s*)"c"\s*,\s*(?:-?\d+|"(?:\\.|[^"])*")', str(human or "")))


def _obvious_modded_errors(human: str, tokens: list[str]) -> list[str]:
    errors: list[str] = []
    toks = [str(t) for t in (tokens or [])]
    token_count = len(toks)

    if token_count > 64:
        errors.append(f"obvious modded serial: too many part tokens ({token_count} > 64)")

    exact_counts = Counter(toks)
    dup_token, dup_count = exact_counts.most_common(1)[0] if exact_counts else ("", 0)
    if dup_count > 1:
        errors.append(f"obvious modded serial: repeated part token {dup_token} x{dup_count}")

    idx_counts = Counter(_token_index(t) for t in toks if _token_index(t))
    idx, idx_count = idx_counts.most_common(1)[0] if idx_counts else ("", 0)
    if idx_count > 48:
        errors.append(f"obvious modded serial: part index {{{idx}}} appears {idx_count} time(s)")

    for tok in toks:
        vals = _token_list_values(tok)
        if not vals:
            continue
        if len(vals) > 32:
            errors.append(f"obvious modded serial: packed part list {tok[:48]}... has {len(vals)} value(s)")
            break
        counts = Counter(vals)
        val, count = counts.most_common(1)[0]
        if count > 1:
            errors.append(f"obvious modded serial: packed part list repeats value {val} x{count}")
            break

    _ = _cosmetic_selector_count(human)
    return errors


def _expanded_token_count(tokens: list[str]) -> int:
    total = 0
    for tok in tokens or []:
        vals = _token_list_values(str(tok))
        total += len(vals) if vals else 1
    return total


def _expanded_token_items(token: str) -> list[Any]:
    try:
        expand = getattr(_legit_builder, "_expand_serial_token", None)
        if callable(expand):
            return list(expand(token))
    except Exception:
        pass
    return [token]


def _explicit_root_sub_tokens(tokens: list[str]) -> list[tuple[int, int, str]]:
    out: list[tuple[int, int, str]] = []
    for tok in tokens or []:
        for expanded in _expanded_token_items(tok):
            match = re.match(r"\{\s*(\d+)\s*:\s*(-?\d+)\s*\}", str(expanded or ""))
            if not match:
                continue
            try:
                out.append((int(match.group(1)), int(match.group(2)), str(expanded)))
            except Exception:
                pass
    return out


def _aux_cross_root_token_allowed(src_serial: int, sub_serial: int) -> bool:
    try:
        src_key = _root_key_for_serial(int(src_serial))
        if not src_key:
            return False
        part = _legit_builder.describe_part(src_key, f"{{{int(sub_serial)}}}")
        if not part:
            return False
        src_key_n = str(src_key or "").strip().lower()
        table = str(part.get("table") or "").strip().lower()
        if src_key_n == "classmod" and table == "firmware":
            return True
        if src_key_n in {"grenade_gadget", "gadget"} and table in {"element", "stat_augment", "firmware"}:
            return True
    except Exception:
        return False
    return False


def _unresolved_part_errors(validation: dict[str, Any], tokens: list[str]) -> list[str]:
    errors: list[str] = []
    expanded = _expanded_token_count(tokens)
    resolved = int((validation or {}).get("part_count") or 0)
    aux_allowed = 0
    for src, sub, _tok in _explicit_root_sub_tokens(tokens):
        if _aux_cross_root_token_allowed(src, sub):
            aux_allowed += 1
    effective_expanded = max(0, expanded - aux_allowed)
    missing = max(0, effective_expanded - resolved)
    if missing > 0:
        errors.append(
            "obvious modded serial: "
            f"{missing} normal part token(s) not found or wrong-root "
            f"({resolved}/{effective_expanded} resolved, {aux_allowed} aux ignored)"
        )
    if effective_expanded > 0 and resolved == 0:
        errors.append("obvious modded serial: no serialized normal part tokens resolved")
    return errors


def _allowed_root_serials_for_root(root_key: str) -> set[int]:
    allowed: set[int] = set()
    try:
        root = _legit_builder.get_root(root_key)
        seen: set[str] = set()
        while root:
            key = str(root.get("key") or "").strip().lower()
            if not key or key in seen:
                break
            seen.add(key)
            try:
                allowed.add(int(root.get("serial")))
            except Exception:
                pass
            ref = str(root.get("basetype") or "")
            if ref.lower().startswith("inv'") and "'" in ref[4:]:
                ref = ref.split("'", 2)[1]
            if "." in ref:
                ref = ref.split(".", 1)[0]
            ref = ref.strip().lower()
            if not ref:
                break
            root = _legit_builder.get_root(ref)
    except Exception:
        pass
    return allowed


def _cross_root_token_errors(root_key: str, tokens: list[str]) -> list[str]:
    allowed = _allowed_root_serials_for_root(root_key)
    if not allowed:
        return []
    errors: list[str] = []
    for tok in tokens or []:
        for expanded in _expanded_token_items(tok):
            match = re.match(r"\{\s*(\d+)\s*:\s*(-?\d+|\[)", str(expanded or ""))
            if not match:
                continue
            try:
                src = int(match.group(1))
                sub_text = str(match.group(2))
                sub = int(sub_text) if sub_text.lstrip("-").isdigit() else None
            except Exception:
                continue
            if src in allowed:
                continue
            if sub is not None and _aux_cross_root_token_allowed(src, sub):
                continue
            errors.append(f"obvious modded serial: cross-root part token {{{src}:...}} is not valid for root {root_key}")
            return errors
    return errors


def _safe_serial_from_human(human: str) -> str:
    try:
        return human_to_serial(human)
    except Exception:
        return ""


def _message_for_result(result: dict[str, Any], index: int | None = None) -> str:
    prefix = f"#{index}: " if index is not None else ""
    status = str(result.get("status") or STATUS_ERROR)
    if status == STATUS_ERROR:
        errors = result.get("errors") or []
        detail = str(errors[0]) if errors else str(result.get("message") or "validation error")
        return prefix + f"{STATUS_ERROR} - {detail}"

    root_serial = result.get("root_serial")
    root_key = result.get("root_key") or ""
    level = result.get("level")
    part_count = int(result.get("part_count") or 0)
    errors = [str(e) for e in (result.get("errors") or [])]
    detail = "" if not errors else " - " + "; ".join(errors[:8])
    if len(errors) > 8:
        detail += f"; +{len(errors) - 8} more"
    return prefix + f"{status} root {root_serial} ({root_key}) level {level} parts {part_count}{detail}"


def validate_serial_text(text: str, index: int | None = None) -> dict[str, Any]:
    """Validate one Base85 or human-readable serial and return structured data."""
    raw = str(text or "").strip()
    result: dict[str, Any] = {
        "input": raw,
        "status": STATUS_ERROR,
        "result": STATUS_ERROR,
        "label": STATUS_ERROR,
        "mattmab_validator": "ERROR",
        "message": "",
        "human": "",
        "serial": "",
        "root_serial": None,
        "root_key": "",
        "root_info": None,
        "level": None,
        "part_count": 0,
        "errors": [],
        "warnings": [],
    }
    try:
        human = _human_from_any_serial(raw)
        root_serial, level, tokens = _extract_tokens_from_human(human)
        root_key = _root_key_for_serial(root_serial)
        if not root_key:
            raise ValueError(f"unknown root serial {root_serial}")

        validation = _legit_builder.validate(root_key, tokens, strict_comp=False)
        errs = [str(e) for e in (validation.get("errors") or [])]
        errs.extend(_cross_root_token_errors(root_key, tokens))
        errs.extend(_unresolved_part_errors(validation, tokens))
        errs.extend(_obvious_modded_errors(human, tokens))

        status = STATUS_LEGIT if not errs else STATUS_MODDED
        result.update({
            "status": status,
            "result": status,
            "label": status,
            "mattmab_validator": "PASS" if status == STATUS_LEGIT else "FAIL",
            "human": human,
            "serial": raw if raw.startswith("@U") else _safe_serial_from_human(human),
            "root_serial": root_serial,
            "root_key": root_key,
            "root_info": _legit_builder.get_root(root_key),
            "level": level,
            "part_count": len(tokens),
            "errors": errs,
            "warnings": [str(w) for w in (validation.get("warnings") or [])],
            "validation": validation,
        })
    except Exception as exc:
        result["errors"] = [str(exc)]
    result["message"] = _message_for_result(result, index)
    return result


def format_validation_result(result: dict[str, Any], index: int | None = None) -> str:
    """Return the BLImGui-style one-line validation summary."""
    if result.get("message") and index is None:
        return str(result["message"])
    return _message_for_result(result, index)


def validate_many(
    text_or_list: str | Iterable[str],
    cancel_check: Callable[[], bool] | None = None,
    progress_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Validate a list of serials with optional cancellation/progress hooks."""
    if isinstance(text_or_list, str):
        rows = parse_serial_text(text_or_list)
    else:
        rows = [str(row or "").strip() for row in text_or_list if str(row or "").strip()]

    total = len(rows)
    results: list[dict[str, Any]] = []
    passed = 0
    failed = 0
    cancelled = False

    if total <= 0:
        return {
            "ok": False,
            "cancelled": False,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "results": [],
            "summary": "No serial tokens found.",
            "output": "No serial tokens found.",
        }

    for i, row in enumerate(rows, 1):
        if cancel_check is not None and cancel_check():
            cancelled = True
            break

        result = validate_serial_text(row, i if total != 1 else None)
        results.append(result)
        if result.get("status") == STATUS_LEGIT:
            passed += 1
        else:
            failed += 1

        if progress_callback is not None:
            progress_callback({
                "running": True,
                "label": "Validating bulk" if total != 1 else "Validating basic",
                "done": i,
                "total": total,
                "passed": passed,
                "failed": failed,
            })
        try:
            time.sleep(0.001)
        except Exception:
            pass

    processed = passed + failed
    mode = "Basic" if total == 1 else "Bulk"
    summary = f"{mode} validation: {passed} legit, {failed} modded/error, {processed} processed of {total}."
    if cancelled:
        summary = f"Validation cancelled after {processed}/{total} serials."

    lines = [format_validation_result(r) for r in results]
    output_lines = lines
    if len(lines) > 500:
        output_lines = [f"Showing first 100 and last 400 of {len(lines)} result lines."] + lines[:100] + ["... output truncated ..."] + lines[-400:]

    if progress_callback is not None:
        progress_callback({
            "running": False,
            "label": "Validation cancelled" if cancelled else "Validation complete",
            "done": processed,
            "total": total,
            "passed": passed,
            "failed": failed,
        })

    payload = {
        "ok": not cancelled,
        "cancelled": cancelled,
        "total": total,
        "passed": passed,
        "failed": failed,
        "processed": processed,
        "results": results,
        "summary": summary,
        "output": summary + ("\n" + "\n".join(output_lines) if output_lines else ""),
    }
    if total == 1 and results:
        payload.update({
            "status": results[0].get("status"),
            "result": results[0].get("result"),
            "label": results[0].get("label"),
            "message": results[0].get("message"),
        })
    return payload


def validate_basic_input(text: str) -> dict[str, Any]:
    if not str(text or "").strip():
        return {
            "ok": False,
            "cancelled": False,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "results": [],
            "summary": "Paste one @U/Base85 or decoded human serial first.",
            "output": "Paste one @U/Base85 or decoded human serial first.",
        }
    rows = parse_serial_text(text)
    return validate_many(rows[:1])


def validate_bulk_input(text: str, cancel_check: Callable[[], bool] | None = None, progress_callback: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
    rows = parse_serial_text(text)
    if not rows:
        return {
            "ok": False,
            "cancelled": False,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "results": [],
            "summary": "Paste one serial per line first.",
            "output": "Paste one serial per line first.",
        }
    return validate_many(rows, cancel_check=cancel_check, progress_callback=progress_callback)
