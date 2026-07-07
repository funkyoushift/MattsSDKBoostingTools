"""Experimental known-working modded-pattern classifier.

This helper is intentionally analysis-only. It does not build serials, generate
Base85 output, deliver items, or change the stable Legit Builder behavior.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import json
import re

from external_app_paths import RESOURCE_DIR


PATTERNS_PATH = RESOURCE_DIR / "known_working_modded_patterns.json"

RESULT_LEGIT = "legit"
RESULT_PATTERN_MATCH = "working_modded_pattern_match"
RESULT_RISKY_UNKNOWN = "risky_unknown_modded"
RESULT_UNSUPPORTED_UNKNOWN = "unsupported_unknown"
RESULT_INSUFFICIENT_DATA = "insufficient_data"

_PATTERN_CATEGORY_ALIASES: dict[str, tuple[str, ...]] = {
    "missing_or_omitted_inv_comp": (
        "omitted_inv_comp",
        "missing_or_omitted_inv_comp",
        "missing_inv_comp",
    ),
    "weapon_accessory_without_expected_parent_dependency": (
        "weapon_accessory_without_parent_dependency",
        "accessory_without_parent",
        "barrel",
        "accessory parent",
    ),
    "licensed_or_cross_manufacturer_exclusion_tolerated": (
        "licensed_or_cross_manufacturer_exclusion_tolerated",
        "licensed",
        "licensed_topacc",
        "cross_manufacturer",
    ),
    "element_or_secondary_element_rule_violation": (
        "element_or_secondary_element_rule_violation",
        "body_acc_ele",
        "secondary_element",
        "secondary_ele",
        "elem",
    ),
    "pearlescent_part_dependency_violation": (
        "pearlescent_part_dependency_violation",
        "pearlescent",
        "pearl_",
    ),
    "class_mod_legendary_or_passive_rule_violation": (
        "classmod_legendary_or_passive_rule_violation",
        "class_mod_legendary_or_passive_rule_violation",
        "class mod",
        "classmod",
        "passive",
        "uni_classmod",
        "leg_body",
    ),
    "ordnance_child_or_mirv_part_without_parent": (
        "ordnance_child_or_mirv_without_parent",
        "ordnance_child_or_mirv_part_without_parent",
        "mirv",
        "child part",
    ),
    "unknown_or_new_root": (
        "unknown_ai_or_new_root",
        "unknown_or_new_root",
        "unknown root",
        "not present in local buildable roots",
    ),
    "decode_failure_but_known_working": (
        "decode_failed_but_known_working",
        "decode_failure_but_known_working",
        "parser false negative",
        "unknown part subtype",
        "could not parse",
    ),
}

_ERROR_MATCHERS: dict[str, tuple[str, ...]] = {
    "missing_or_omitted_inv_comp": (
        r"expected exactly one\s+inv_comp",
        r"slot\s+inv_comp\s+requires",
        r"inv_comp.*got\s+0",
        r"composition/rarity",
    ),
    "weapon_accessory_without_expected_parent_dependency": (
        r"missing dependency tags?:.*barrel",
        r"missing dependency tags?:.*accessory",
        r"missing dependency tags?:.*underbarrel",
        r"parent dependency",
        r"accessory parent",
    ),
    "licensed_or_cross_manufacturer_exclusion_tolerated": (
        r"excluded by active tags?:.*licensed",
        r"licensed_topacc",
        r"cross[-_\s]?manufacturer",
    ),
    "element_or_secondary_element_rule_violation": (
        r"missing dependency tags?:.*body_acc_ele",
        r"missing dependency tags?:.*secondary",
        r"excluded by active tags?:.*elem",
        r"element",
    ),
    "pearlescent_part_dependency_violation": (
        r"pearlescent",
        r"pearl[_\s-]",
    ),
    "class_mod_legendary_or_passive_rule_violation": (
        r"uni_classmod",
        r"leg_body",
        r"passive",
        r"legendary class mod",
        r"class\s*mod",
        r"classmod",
    ),
    "ordnance_child_or_mirv_part_without_parent": (
        r"missing dependency tags?:.*mirv",
        r"child part parent",
        r"ordnance",
        r"mirv",
    ),
    "unknown_or_new_root": (
        r"unknown root",
        r"unknown/new root",
        r"not present in local buildable roots",
        r"no buildable root",
    ),
    "decode_failure_but_known_working": (
        r"decode fail",
        r"could not parse",
        r"unknown part subtype",
        r"parser false negative",
    ),
}


def _safe_str(value: Any) -> str:
    return str(value or "").strip()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _normalize_pattern(pattern: dict[str, Any]) -> dict[str, Any]:
    pattern_id = _safe_str(pattern.get("pattern_id")) or "unknown_pattern"
    lower_id = pattern_id.lower()
    category = lower_id
    for canonical, aliases in _PATTERN_CATEGORY_ALIASES.items():
        if any(alias.lower() in lower_id for alias in aliases):
            category = canonical
            break

    try:
        observed_count = int(pattern.get("observed_count") or 0)
    except Exception:
        observed_count = 0

    return {
        "pattern_id": pattern_id,
        "category": category,
        "observed_count": observed_count,
        "confidence": _safe_str(pattern.get("confidence")) or "unknown",
        "rule_signal": _safe_str(pattern.get("rule_signal")),
        "builder_recommendation": _safe_str(pattern.get("builder_recommendation")),
        "notes": _safe_str(pattern.get("notes")),
        "working_status": _safe_str(pattern.get("working_status")),
        "legit_status": _safe_str(pattern.get("legit_status")),
        "common_types": [str(v) for v in _as_list(pattern.get("common_types")) if _safe_str(v)],
        "observed_listings": dict(pattern.get("observed_listings") or {}),
    }


def load_known_working_patterns(resource_path: str | Path | None = None) -> dict[str, Any]:
    """Load and normalize the known-working modded pattern resource.

    Missing or malformed data is reported in the returned warnings list instead
    of raising, so the external app can remain usable without this optional
    experimental resource.
    """
    path = Path(resource_path) if resource_path is not None else PATTERNS_PATH
    warnings: list[str] = []

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {
            "ok": False,
            "path": str(path),
            "metadata": {},
            "patterns": [],
            "pattern_count": 0,
            "warnings": [f"Known-working modded pattern resource is missing: {path}"],
        }
    except Exception as exc:
        return {
            "ok": False,
            "path": str(path),
            "metadata": {},
            "patterns": [],
            "pattern_count": 0,
            "warnings": [f"Known-working modded pattern resource could not be loaded: {exc}"],
        }

    raw_patterns = raw.get("patterns", []) if isinstance(raw, dict) else raw if isinstance(raw, list) else []
    if not isinstance(raw_patterns, list):
        raw_patterns = []
        warnings.append("Known-working modded pattern resource has no usable patterns list.")

    patterns = [_normalize_pattern(p) for p in raw_patterns if isinstance(p, dict)]
    if not patterns:
        warnings.append("Known-working modded pattern resource is empty.")

    metadata = {k: v for k, v in raw.items() if k != "patterns"} if isinstance(raw, dict) else {}
    return {
        "ok": bool(patterns),
        "path": str(path),
        "metadata": metadata,
        "patterns": patterns,
        "pattern_count": len(patterns),
        "warnings": warnings,
    }


def _flatten_messages(value: Any) -> list[str]:
    messages: list[str] = []
    if value is None:
        return messages
    if isinstance(value, str):
        if value.strip():
            messages.append(value.strip())
        return messages
    if isinstance(value, dict):
        for key in ("errors", "warnings", "reasons", "messages", "status", "message"):
            messages.extend(_flatten_messages(value.get(key)))
        nested = value.get("validation")
        if isinstance(nested, dict):
            messages.extend(_flatten_messages(nested))
        return messages
    if isinstance(value, Iterable):
        for item in value:
            messages.extend(_flatten_messages(item))
    return messages


def _legit_result_from_validation(legit_validation_result: Any) -> str:
    if legit_validation_result is None:
        return "unknown"
    if isinstance(legit_validation_result, bool):
        return "valid" if legit_validation_result else "invalid"
    if isinstance(legit_validation_result, str):
        text = legit_validation_result.strip().lower()
        if text in {"valid", "legit", "pass", "passed", "ok"}:
            return "valid"
        if text in {"invalid", "modded", "fail", "failed"}:
            return "invalid"
        if "error" in text:
            return "error"
        return "unknown"
    if isinstance(legit_validation_result, dict):
        status_text = " ".join(_flatten_messages({
            "status": legit_validation_result.get("status"),
            "message": legit_validation_result.get("message"),
            "result": legit_validation_result.get("result"),
            "label": legit_validation_result.get("label"),
        })).lower()
        if "error" in status_text:
            return "error"
        if legit_validation_result.get("ok") is True or legit_validation_result.get("valid") is True:
            return "valid"
        if legit_validation_result.get("ok") is False or legit_validation_result.get("valid") is False:
            return "invalid"
        if status_text in {"valid", "legit", "pass", "passed"}:
            return "valid"
        if status_text in {"invalid", "modded", "fail", "failed"}:
            return "invalid"
        if _flatten_messages(legit_validation_result.get("errors")):
            return "invalid"
    return "unknown"


def _selected_parts_text(selected_parts: Any) -> str:
    if selected_parts is None:
        return ""
    if isinstance(selected_parts, str):
        return selected_parts
    parts: list[str] = []
    for part in _as_list(selected_parts):
        if isinstance(part, dict):
            table = _safe_str(part.get("table"))
            key = _safe_str(part.get("key") or part.get("internal") or part.get("line"))
            parts.append(f"{table}:{key}" if table and key else key or table)
        else:
            parts.append(str(part))
    return "\n".join(p for p in parts if p.strip())


def _category_matches(category: str, text: str, pattern: dict[str, Any]) -> bool:
    text_l = text.lower()
    pattern_id = str(pattern.get("pattern_id") or "").lower()
    rule_signal = str(pattern.get("rule_signal") or "").lower()
    aliases = _PATTERN_CATEGORY_ALIASES.get(category, ())
    if any(alias.lower() in text_l for alias in aliases):
        return True
    if pattern_id and pattern_id in text_l:
        return True
    if rule_signal and rule_signal in text_l:
        return True
    for regex in _ERROR_MATCHERS.get(category, ()):
        if re.search(regex, text_l):
            return True
    return False


def _dedupe_patterns(patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for pattern in patterns:
        key = str(pattern.get("pattern_id") or pattern.get("category") or "")
        if key in seen:
            continue
        seen.add(key)
        out.append(pattern)
    return out


def _matches_from_context(patterns: list[dict[str, Any]], context_text: str) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for pattern in patterns:
        category = str(pattern.get("category") or "")
        if category and _category_matches(category, context_text, pattern):
            matches.append(pattern)
    return _dedupe_patterns(matches)


def _root_looks_unknown(root_key: Any, context_text: str) -> bool:
    root = _safe_str(root_key).lower()
    if root in {"unknown", "unknown_root", "new_root", "ai"}:
        return True
    return bool(re.search(r"unknown root|unknown/new root|not present in local buildable roots|no buildable root", context_text.lower()))


def classify_modded_candidate(
    root_key: Any = None,
    selected_parts: Any = None,
    legit_validation_result: Any = None,
    item_type: Any = None,
    manufacturer: Any = None,
    rarity: Any = None,
    context: Any = None,
) -> dict[str, Any]:
    """Classify a candidate against observed known-working modded patterns.

    The returned result is guidance only. A pattern match means "similar to a
    known-working category", not guaranteed valid, not legit, and not approved
    for generation or delivery.
    """
    pattern_data = load_known_working_patterns()
    patterns = list(pattern_data.get("patterns") or [])
    data_warnings = list(pattern_data.get("warnings") or [])

    legit_result = _legit_result_from_validation(legit_validation_result)
    messages = _flatten_messages(legit_validation_result)
    messages.extend(_flatten_messages(context))
    selected_text = _selected_parts_text(selected_parts)
    context_text = "\n".join(
        [
            _safe_str(root_key),
            _safe_str(item_type),
            _safe_str(manufacturer),
            _safe_str(rarity),
            selected_text,
            "\n".join(messages),
        ]
    )

    warnings: list[str] = list(data_warnings)
    strong_warnings: list[str] = []
    recommendations: list[str] = []
    matched_patterns = _matches_from_context(patterns, context_text) if patterns else []
    pattern_data_available = bool(pattern_data.get("ok"))
    has_candidate = bool(_safe_str(root_key) or selected_text or messages)

    if not pattern_data_available:
        experimental_result = RESULT_INSUFFICIENT_DATA
        warnings.append("Known-working pattern data is unavailable, so experimental modded guidance cannot be produced.")
        recommendations.append("Keep using stable Legit Builder validation until the pattern resource is available.")
    elif _root_looks_unknown(root_key, context_text):
        experimental_result = RESULT_UNSUPPORTED_UNKNOWN
        root_matches = [p for p in matched_patterns if p.get("category") == "unknown_or_new_root"]
        matched_patterns = root_matches or matched_patterns
        strong_warnings.append("This appears to use an unknown/new root. Keep it catalog-only until local root rules exist.")
        recommendations.append("Do not expose this root for building yet; add local root/rule data first.")
    elif legit_result == "valid":
        experimental_result = RESULT_LEGIT
        warnings.append("Current local legit validation reports this candidate as valid.")
        recommendations.append("Use the stable Legit Builder path for legit output.")
    elif legit_result in {"invalid", "error"} and matched_patterns:
        experimental_result = RESULT_PATTERN_MATCH
        warnings.append(
            "This violates current legit rules but matches one or more categories observed in known-working item codes."
        )
        warnings.append("A known-working pattern match is evidence-based guidance only, not a guarantee.")
        if legit_result == "error":
            strong_warnings.append("The normal validator reported an error; decoder/parser issues should be fixed before builder exposure.")
        recommendations.extend(
            [
                str(p.get("builder_recommendation") or "")
                for p in matched_patterns
                if str(p.get("builder_recommendation") or "").strip()
            ]
        )
        if not recommendations:
            recommendations.append("Allow only in a clearly labeled experimental modded workflow after manual testing.")
    elif legit_result in {"invalid", "error"}:
        experimental_result = RESULT_RISKY_UNKNOWN
        strong_warnings.append(
            "This violates current legit rules and does not match the observed known-working modded pattern categories."
        )
        recommendations.append("Do not build or share this candidate until it has been manually validated in-game.")
    elif not has_candidate:
        experimental_result = RESULT_INSUFFICIENT_DATA
        warnings.append("No root, selected parts, or validation result was provided.")
        recommendations.append("Choose a candidate build and run normal validation before experimental classification.")
    elif matched_patterns:
        experimental_result = RESULT_PATTERN_MATCH
        warnings.append("Candidate text matches known-working modded pattern signals, but normal validation status is unknown.")
        recommendations.append("Run stable validation first, then use this experimental guidance as secondary evidence.")
    else:
        experimental_result = RESULT_INSUFFICIENT_DATA
        warnings.append("Insufficient validation detail to classify this candidate.")
        recommendations.append("Pass the normal Legit Builder validation result, including error text, for a stronger classification.")

    matched_out = [
        {
            "pattern_id": p.get("pattern_id"),
            "category": p.get("category"),
            "observed_count": p.get("observed_count"),
            "confidence": p.get("confidence"),
            "rule_signal": p.get("rule_signal"),
            "builder_recommendation": p.get("builder_recommendation"),
        }
        for p in matched_patterns
    ]

    return {
        "legit_result": legit_result,
        "experimental_result": experimental_result,
        "matched_patterns": matched_out,
        "warnings": _dedupe_text(warnings),
        "strong_warnings": _dedupe_text(strong_warnings),
        "recommendations": _dedupe_text(recommendations),
        "pattern_data_available": pattern_data_available,
        "pattern_count": int(pattern_data.get("pattern_count") or 0),
        "pattern_resource_path": pattern_data.get("path"),
        "root_key": _safe_str(root_key),
        "item_type": _safe_str(item_type),
        "manufacturer": _safe_str(manufacturer),
        "rarity": _safe_str(rarity),
    }


def _dedupe_text(values: Iterable[Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        text = _safe_str(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def summarize_modded_result(result: dict[str, Any]) -> str:
    """Render a concise human-readable summary for a future UI panel."""
    experimental_result = _safe_str(result.get("experimental_result")) or RESULT_INSUFFICIENT_DATA
    title = experimental_result.replace("_", " ").title()
    lines = [f"Experimental result: {title}."]

    legit_result = _safe_str(result.get("legit_result"))
    if legit_result:
        lines.append(f"Stable legit validation: {legit_result}.")

    matches = list(result.get("matched_patterns") or [])
    if matches:
        lines.append("Matched known-working pattern categories:")
        for pattern in matches:
            pattern_id = _safe_str(pattern.get("pattern_id"))
            count = pattern.get("observed_count")
            confidence = _safe_str(pattern.get("confidence"))
            suffix = []
            if count not in (None, ""):
                suffix.append(f"observed {count}")
            if confidence:
                suffix.append(f"confidence {confidence}")
            detail = f" ({', '.join(suffix)})" if suffix else ""
            lines.append(f"- {pattern_id}{detail}")

    warnings = list(result.get("warnings") or [])
    if warnings:
        lines.append("Warnings:")
        lines.extend(f"- {text}" for text in warnings)

    strong_warnings = list(result.get("strong_warnings") or [])
    if strong_warnings:
        lines.append("Strong warnings:")
        lines.extend(f"- {text}" for text in strong_warnings)

    recommendations = list(result.get("recommendations") or [])
    if recommendations:
        lines.append("Recommendations:")
        lines.extend(f"- {text}" for text in recommendations)

    if experimental_result == RESULT_PATTERN_MATCH:
        lines.append(
            "This is experimental/modded guidance only. It does not guarantee every variation works and it does not make the item legit."
        )
    elif experimental_result == RESULT_RISKY_UNKNOWN:
        lines.append("This is outside the observed known-working pattern set; treat it as high risk.")
    elif experimental_result == RESULT_UNSUPPORTED_UNKNOWN:
        lines.append("Unknown roots should stay catalog-only until local rules/root data exist.")

    return "\n".join(lines)
