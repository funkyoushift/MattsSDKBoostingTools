"""Targeted currency, experience, and SDU point helpers for lobby players."""

from __future__ import annotations

import argparse
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

from mods_base import command
from unrealsdk import find_all, find_class, find_object, logging
from unrealsdk.unreal import FGbxDefPtr, UObject

from .party_helpers import (
    _gbc_find_pc_for_player_state,
    _gbc_is_listen_host_world,
    _gbc_resolve_player_index_for_name_substring,
    _gbc_session_world_and_gamestate,
)

_PREFIX = "[Matts SDK Boosting Tools | Economy]"


def _log(msg: str, *args: Any) -> None:
    logging.info(_PREFIX + " " + (msg % args if args else msg))


def _log_err(msg: str, *args: Any) -> None:
    logging.error(_PREFIX + " " + (msg % args if args else msg))


_CURRENCY_KIND_ALIASES: Dict[str, str] = {
    "cash": "Cash",
    "money": "Cash",
    "eridium": "eridium",
    "vaultcard1": "VaultCard01_Tokens",
    "vaultcard_1": "VaultCard01_Tokens",
    "vc1": "VaultCard01_Tokens",
    "vaultcard2": "VaultCard02_Tokens",
    "vaultcard_2": "VaultCard02_Tokens",
    "vc2": "VaultCard02_Tokens",
    "vaultcard3": "VaultCard03_Tokens",
    "vaultcard_3": "VaultCard03_Tokens",
    "vc3": "VaultCard03_Tokens",
}

# OakPlayerState.ExperienceState fixed slots (aliases → index).
#   0 — Player/character level
#   1 — Specialization level
#   2 — Vault card 01 XP
#   3 — Vault card 02 XP
#   4 — Vault card 03 XP (Raid 3)
# Level changes now go through OakPlayerState.BP_SetExperienceLevel using an
# SDK 03 FGbxDefPtr(name, type) to /Script/GbxGame.GbxExperienceDef. This is much
# safer than writing ExperienceState fields directly, because the engine updates
# related level/XP state itself.
_MAX_PLAYER_LEVEL_ENGINE = 60
_MAX_SPEC_LEVEL_ENGINE = 701
_MAX_VAULT_XP_LEVEL_ENGINE = 9_999_999


def _clamp_engine_experience_level(track_index: int, level: int) -> int:
    lv = max(0, int(level))
    if track_index == 0:
        return min(lv, _MAX_PLAYER_LEVEL_ENGINE)
    if track_index == 1:
        return min(lv, _MAX_SPEC_LEVEL_ENGINE)
    return min(lv, _MAX_VAULT_XP_LEVEL_ENGINE)


_EXPERIENCE_TRACK_ALIASES: Dict[str, int] = {
    "0": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    "4": 4,
    "character": 0,
    "player": 0,
    "main": 0,
    "level": 0,
    "specialization": 1,
    "spec": 1,
    "arsenal": 1,
    "vaultcard_xp_1": 2,
    "vaultcard1_xp": 2,
    "vc1_xp": 2,
    "vaultcard_xp_2": 3,
    "vaultcard2_xp": 3,
    "vc2_xp": 3,
    "vaultcard_xp_3": 4,
    "vaultcard3_xp": 4,
    "vc3_xp": 4,
}


def _normalize_track_key(track_raw: str) -> str:
    """Strip BOM / ZWSP, Unicode-normalize (e.g. fullwidth digits → ASCII), lowercase for alias lookup."""
    s = unicodedata.normalize("NFKC", (track_raw or "").strip())
    for ch in ("\ufeff", "\u200b", "\u200c", "\u200d"):
        s = s.replace(ch, "")
    return s.strip().lower()

_CURRENCY_DEF_SCRIPT_PATHS = (
    "/Script/GbxGame.GbxCurrencyDef",
    "/Script/OakGame.GbxCurrencyDef",
)

_INT32_MAX = 2_147_483_647
_MAX_WALLET_AMOUNT = 2_147_483_647
_SDU_POINTS_POOL_INDEX = 2
_MAX_SDU_POINTS = 3225

# --- Cumulative total XP (ExperiencePoints) vs level — from workspace `xp.md` (BL4 / Oak) ---
# Under-shooting total XP for a level causes HUD counter glitches; use documented curves + margin.
_CHAR_XP_ANCHOR_L50 = 3_430_227
_CHAR_XP_ANCHOR_L60 = 5_714_893
_SPEC_XP_ANCHOR_L701 = 7_431_910_510
# Vault XP (tracks 2–3): no xp.md curve. One OakPlayerState sample had this pair; used only
# when we cannot scale from the row's prior ExperienceLevel/ExperiencePoints (cold start).
_VAULT_XP_ANCHOR_LEVEL = 9_999
_VAULT_XP_ANCHOR_POINTS = 15_609_777_137_452


def _char_segment1_total_xp(level: float) -> float:
    """Total cumulative XP for character levels 11–50 (polynomial from xp.md)."""
    return (
        20.435970 * level**3
        + 445.422020 * level**2
        + -5301.029340 * level
        + 27953.516161
    )


def _spec_segment1_total_xp(level: float) -> float:
    """Specialization total XP, levels 11–31."""
    return (
        83.390778 * level**3
        + -2314.676389 * level**2
        + 41061.771085 * level
        + -216525.913214
    )


def _spec_segment2_total_xp(level: float) -> float:
    """Specialization total XP, levels 32–200."""
    return (
        20.903278 * level**3
        + 1701.317660 * level**2
        + -74334.753724 * level
        + 1403361.683375
    )


def _spec_segment3_total_xp(level: float) -> float:
    """Specialization total XP, levels 250–450."""
    return (
        16.708444 * level**3
        + 4297.272805 * level**2
        + -645890.804295 * level
        + 46158303.367444
    )


def _spec_segment4_total_xp(level: float) -> float:
    """Specialization total XP, levels 500–701."""
    return (
        14.960904 * level**3
        + 6708.446543 * level**2
        + -1773218.961259 * level
        + 224787945.740717
    )


def _xp_safety_margin(total: int) -> int:
    """Small headroom above the fitted floor to avoid underflow in in-game counters (xp.md)."""
    if total <= 0:
        return 0
    return max(512, min(total // 400, 250_000))


def _character_cumulative_total_xp(level: int) -> int | None:
    """
    Cumulative total XP for OakPlayerState ExperienceState slot 0 (character level).
    Anchors L50 / L60 from xp.md; polynomial segment for 11–50; linear bridge 50–60; extrapolate past 60.
    """
    if level <= 1:
        return 0
    L = float(level)
    if level < 11:
        # xp.md: levels 1–10 are manually tuned — ramp toward segment-1 at 11 instead of mis-fitting the cubic.
        t = (level - 1) / 10.0
        base = _char_segment1_total_xp(11.0)
        return max(0, int(round(base * t)))
    if level <= 50:
        est = int(round(_char_segment1_total_xp(L)))
        if level == 50:
            return max(est, _CHAR_XP_ANCHOR_L50)
        return max(0, est)
    if level <= 60:
        t = (level - 50) / 10.0
        return int(round(_CHAR_XP_ANCHOR_L50 + t * (_CHAR_XP_ANCHOR_L60 - _CHAR_XP_ANCHOR_L50)))
    per = (_CHAR_XP_ANCHOR_L60 - _CHAR_XP_ANCHOR_L50) / 10.0
    return int(round(_CHAR_XP_ANCHOR_L60 + (level - 60) * per))


def _specialization_cumulative_total_xp(level: int) -> int | None:
    """
    Cumulative total XP for ExperienceState slot 1 (specialization).
    Piecewise curves + linear bridges in gaps (201–249, 451–499) from xp.md; anchor near 701.
    """
    if level <= 1:
        return 0
    L = float(level)
    if level < 11:
        t = (level - 1) / 10.0
        base = _spec_segment1_total_xp(11.0)
        return max(0, int(round(base * t)))
    if level <= 31:
        return max(0, int(round(_spec_segment1_total_xp(L))))
    if level <= 200:
        return max(0, int(round(_spec_segment2_total_xp(L))))
    if level < 250:
        y200 = _spec_segment2_total_xp(200.0)
        y250 = _spec_segment3_total_xp(250.0)
        t = (L - 200.0) / 50.0
        return max(0, int(round(y200 + t * (y250 - y200))))
    if level <= 450:
        return max(0, int(round(_spec_segment3_total_xp(L))))
    if level < 500:
        y450 = _spec_segment3_total_xp(450.0)
        y500 = _spec_segment4_total_xp(500.0)
        t = (L - 450.0) / 50.0
        return max(0, int(round(y450 + t * (y500 - y450))))
    if level <= 701:
        est = int(round(_spec_segment4_total_xp(L)))
        if level == 701:
            return max(est, _SPEC_XP_ANCHOR_L701)
        return max(0, est)
    # Past 701 (e.g. RequiredForNextLevel at cap uses lvl+1 == 702): extrapolate segment 4.
    return max(0, int(round(_spec_segment4_total_xp(L))))


def _vault_track_cumulative_total_xp(level: int, prior_level: int, prior_points: int) -> int:
    """
    Lifetime ExperiencePoints for vault-card tracks (2–3) at ExperienceLevel ``level``.

    Prefer scaling from the row's previous level/points so we keep a consistent ratio when
    the host edits level in place. If prior level is unknown (0), use a linear floor from
    a single high-level save sample (coarse; better than copying
    ExperiencePointsRequiredForPreviousLevel, which is not the same as total XP).
    """
    lvl = max(0, min(int(level), _MAX_VAULT_XP_LEVEL_ENGINE))
    if lvl <= 0:
        return 0
    pl = max(0, int(prior_level))
    pp = max(0, int(prior_points))
    if pl > 0 and pp > 0:
        return int(round(pp * (float(lvl) / float(pl))))
    rate = _VAULT_XP_ANCHOR_POINTS / float(_VAULT_XP_ANCHOR_LEVEL)
    return max(0, int(round(rate * lvl)))


def _cumulative_floor_for_track(track_index: int, level: int, prior_lvl: int, prior_pts: int) -> int:
    """Minimum lifetime ExperiencePoints to sit at ``level`` with an empty bar (HUD thresholds)."""
    lv = max(0, int(level))
    if track_index == 0:
        return int(_character_cumulative_total_xp(lv))
    if track_index == 1:
        return int(_specialization_cumulative_total_xp(lv))
    return _vault_track_cumulative_total_xp(lv, prior_lvl, prior_pts)


def _cumulative_next_floor_for_track(track_index: int, level: int, prior_lvl: int, prior_pts: int) -> int:
    """
    Cumulative lifetime XP threshold to finish ``level`` and reach ``level + 1`` at 0 bar.
    Used for ExperiencePointsRequiredForNextLevel.
    """
    lv = max(0, int(level))
    if track_index == 0:
        return int(_character_cumulative_total_xp(lv + 1))
    if track_index == 1:
        return int(_specialization_cumulative_total_xp(lv + 1))
    if lv >= _MAX_VAULT_XP_LEVEL_ENGINE:
        cur = _vault_track_cumulative_total_xp(lv, prior_lvl, prior_pts)
        prev1 = _vault_track_cumulative_total_xp(max(0, lv - 1), prior_lvl, prior_pts)
        step = max(1, cur - prev1)
        return cur + step
    return _vault_track_cumulative_total_xp(lv + 1, prior_lvl, prior_pts)


def _coerce_experience_requirement_pair(req_prev: int, req_next: int) -> tuple[int, int]:
    """Keep Next strictly above Prev so UI / logic never sees an inverted range."""
    rp = max(0, int(req_prev))
    rn = max(0, int(req_next))
    if rn <= rp:
        rn = rp + max(1, rp // 1_000_000 or 1)
    return rp, rn


_EXPERIENCE_DEF_SCRIPT_PATHS = (
    "/Script/GbxGame.GbxExperienceDef",
    "/Script/OakGame.GbxExperienceDef",
)

_EXPERIENCE_TRACK_TOKEN_FALLBACKS: Dict[int, Tuple[str, ...]] = {
    0: ("Character",),
    1: ("Specialization", "Specialisation"),
    2: ("VaultCard01", "VaultCard1", "VaultCard01_XP", "VaultCard01_Experience"),
    3: ("VaultCard02", "VaultCard2", "VaultCard02_XP", "VaultCard02_Experience"),
    4: ("VaultCard03", "VaultCard3", "VaultCard03_XP", "VaultCard03_Experience"),
}


def _find_experience_def_struct() -> Optional[Any]:
    for object_path in _EXPERIENCE_DEF_SCRIPT_PATHS:
        try:
            resolved = find_object("ScriptStruct", object_path)
        except Exception:
            resolved = None
        if isinstance(resolved, UObject):
            return resolved
    try:
        for candidate in find_all("ScriptStruct", False) or []:
            if getattr(candidate, "Name", None) == "GbxExperienceDef" or str(candidate).endswith("GbxExperienceDef'"):
                return candidate
    except Exception:
        pass
    return None


def _make_experience_def_ptr(token_name: str) -> Optional[FGbxDefPtr]:
    struct_u = _find_experience_def_struct()
    if struct_u is None:
        _log_err("Could not resolve GbxExperienceDef ScriptStruct.")
        return None
    tail = (token_name or "").strip().split("/")[-1]
    if not tail:
        return None
    try:
        return FGbxDefPtr(tail, struct_u)
    except Exception as e:
        _log_err("FGbxDefPtr(name, GbxExperienceDef) failed for experience token %r: %s", tail, e)
        return None


def _experience_state_token_name(row: Any) -> Optional[str]:
    """Best-effort extraction of the SName token shown as Name: 'Character' in runtime dumps."""
    try:
        eid = getattr(row, "ExperienceId", None)
    except Exception:
        eid = None
    if eid is None:
        return None
    for attr in ("Name", "name"):
        try:
            value = getattr(eid, attr)
            if isinstance(value, str) and value:
                return value
        except Exception:
            pass
    try:
        text = str(eid)
    except Exception:
        return None
    m = re.search(r"Name:\s*'([^']+)'", text)
    if m:
        return m.group(1)
    m = re.search(r'Name:\s*"([^"]+)"', text)
    if m:
        return m.group(1)
    return None


def _candidate_experience_tokens(track_index: int, row: Any) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for token in (_experience_state_token_name(row), *(_EXPERIENCE_TRACK_TOKEN_FALLBACKS.get(track_index, ()))):
        if token and token not in seen:
            seen.add(token)
            out.append(token)
    return out


def _find_currency_def_struct() -> Optional[Any]:
    for class_name in ("ScriptStruct", "Object"):
        for object_path in _CURRENCY_DEF_SCRIPT_PATHS:
            try:
                resolved = find_object(class_name, object_path)
            except Exception:
                resolved = None
            if isinstance(resolved, UObject):
                return resolved
    try:
        for candidate in find_all("ScriptStruct", False) or []:
            if getattr(candidate, "Name", None) == "GbxCurrencyDef":
                return candidate
    except Exception:
        pass
    return None


def _make_currency_def_ptr(token_tail: str) -> Optional[FGbxDefPtr]:
    struct_u = _find_currency_def_struct()
    if struct_u is None:
        _log_err("Could not resolve GbxCurrencyDef ScriptStruct.")
        return None
    tail = (token_tail or "").strip().split("/")[-1]
    if not tail:
        return None
    try:
        return FGbxDefPtr(tail, struct_u)
    except Exception as e:
        _log_err("FGbxDefPtr(name, GbxCurrencyDef) failed for currency token %r: %s", tail, e)
        return None


def _get_currency_function_library() -> Optional[Any]:
    try:
        cls = find_class("GbxCurrencyFunctionLibrary")
        if cls is not None:
            cdo = getattr(cls, "ClassDefaultObject", None)
            if cdo is not None:
                return cdo
    except Exception:
        pass
    try:
        objs = find_all("GbxCurrencyFunctionLibrary", False) or []
        if objs:
            return objs[-1]
    except Exception:
        pass
    return None


def _safe_int(tok: str) -> Optional[int]:
    t = (tok or "").strip().replace(",", "")
    if not t or t[0] not in "-0123456789":
        return None
    try:
        return int(t)
    except ValueError:
        try:
            return int(float(t))
        except ValueError:
            return None


def _parse_name_suffix(parts: List[str]) -> Tuple[List[str], str]:
    """Split [... tokens before `name` ...] and name substring (joined)."""
    low = [p.lower() for p in parts]
    try:
        ni = low.index("name")
    except ValueError:
        return parts, ""
    head = parts[:ni]
    tail = " ".join(parts[ni + 1 :]).strip()
    return head, tail


def _resolve_target_pc_for_name(name_sub: str) -> Tuple[Optional[Any], str]:
    world, gs = _gbc_session_world_and_gamestate()
    if world is None or gs is None:
        return None, "no world or GameState"
    if not _gbc_is_listen_host_world(world):
        return None, "listen host only (open console on host)"
    pa = getattr(gs, "PlayerArray", None)
    if pa is None:
        return None, "PlayerArray missing"
    idx, err = _gbc_resolve_player_index_for_name_substring(gs, name_sub)
    if err:
        return None, err
    try:
        ps = pa[idx]
    except Exception as e:
        return None, "PlayerArray read failed: %s" % e
    if ps is None:
        return None, "null PlayerState at index %s" % idx
    pc = _gbc_find_pc_for_player_state(ps, world)
    if pc is None:
        return None, "no PlayerController for that player — run gbc_players"
    return pc, ""


def _resolve_target_pc_for_index(player_index: int) -> Tuple[Optional[Any], str]:
    world, gs = _gbc_session_world_and_gamestate()
    if world is None or gs is None:
        return None, "no world or GameState"
    if not _gbc_is_listen_host_world(world):
        return None, "listen host only (open console on host)"
    pa = getattr(gs, "PlayerArray", None)
    if pa is None:
        return None, "PlayerArray missing"
    try:
        n_pa = len(pa)
    except Exception as e:
        return None, "PlayerArray length failed: %s" % e
    if player_index < 0 or player_index >= n_pa:
        return None, "player index %s out of range (0..%s)" % (player_index, max(0, n_pa - 1))
    try:
        ps = pa[player_index]
    except Exception as e:
        return None, "PlayerArray[%s] read failed: %s" % (player_index, e)
    if ps is None:
        return None, "null PlayerState at index %s" % player_index
    pc = _gbc_find_pc_for_player_state(ps, world)
    if pc is None:
        return None, "no PlayerController for player index %s — run gbc_players" % player_index
    return pc, ""


def _resolve_target_pc_from_parts(parts: List[str], command_name: str) -> Tuple[Optional[Any], str]:
    if not parts:
        return None, "Usage: %s name <substring> | %s index N" % (command_name, command_name)
    head, name_sub = _parse_name_suffix(parts)
    if name_sub:
        return _resolve_target_pc_for_name(name_sub)
    if len(parts) == 2 and parts[0].lower() == "index":
        idx = _safe_int(parts[1])
        if idx is None:
            return None, "%s: expected integer after index" % command_name
        return _resolve_target_pc_for_index(idx)
    return None, "Usage: %s name <substring> | %s index N" % (command_name, command_name)


def _give_currency_on_pc(target_pc: Any, currency_token: str, amount: int) -> bool:
    lib = _get_currency_function_library()
    if lib is None:
        _log_err("GbxCurrencyFunctionLibrary not found.")
        return False
    give = getattr(lib, "GiveCurrency", None)
    if not callable(give):
        _log_err("GiveCurrency not callable.")
        return False
    ptr = _make_currency_def_ptr(currency_token)
    if ptr is None:
        return False
    mgr = getattr(target_pc, "CurrencyManager", None)
    trials: List[Tuple[str, Tuple[Any, ...]]] = [
        ("OwnerContext_pc", (target_pc, ptr, amount)),
    ]
    if mgr is not None:
        trials.append(("OwnerContext_mgr", (mgr, ptr, amount)))
    for label, args in trials:
        try:
            give(*args)
            _log("GiveCurrency OK (%s) token=%s amount=%s", label, currency_token, amount)
            return True
        except TypeError as e:
            _log("GiveCurrency %s TypeError: %s", label, e)
        except Exception as e:
            _log_err("GiveCurrency %s failed: %s", label, e)
            return False
    return False


def _target_character_for_pc(target_pc: Any) -> Optional[Any]:
    for attr in ("Pawn", "AcknowledgedPawn", "Character", "MyCharacter"):
        try:
            obj = getattr(target_pc, attr, None)
        except Exception:
            obj = None
        if obj is not None:
            return obj
    try:
        ps = getattr(target_pc, "PlayerState", None)
    except Exception:
        ps = None
    if ps is not None:
        for attr in ("PawnPrivate", "Pawn", "Character"):
            try:
                obj = getattr(ps, attr, None)
            except Exception:
                obj = None
            if obj is not None:
                return obj
    return None


def _set_max_sdu_points_on_pc(target_pc: Any) -> bool:
    character = _target_character_for_pc(target_pc)
    if character is None:
        _log_err("msbt_maxsdu: could not resolve target character/pawn from PlayerController.")
        return False
    try:
        mgr = getattr(character, "GbxProgressionManager", None)
    except Exception as e:
        _log_err("msbt_maxsdu: reading GbxProgressionManager failed: %s", e)
        return False
    if mgr is None:
        _log_err("msbt_maxsdu: target character has no GbxProgressionManager.")
        return False
    try:
        container = getattr(mgr, "ProgressPointsContainer", None)
        pools = getattr(container, "PointsAcquiredPerPool", None) if container is not None else None
    except Exception as e:
        _log_err("msbt_maxsdu: reading PointsAcquiredPerPool failed: %s", e)
        return False
    if pools is None:
        _log_err("msbt_maxsdu: ProgressPointsContainer.PointsAcquiredPerPool missing.")
        return False
    try:
        n_pools = len(pools)
    except Exception as e:
        _log_err("msbt_maxsdu: PointsAcquiredPerPool length failed: %s", e)
        return False
    if _SDU_POINTS_POOL_INDEX < 0 or _SDU_POINTS_POOL_INDEX >= n_pools:
        _log_err(
            "msbt_maxsdu: pool index %s out of range (length %s).",
            _SDU_POINTS_POOL_INDEX,
            n_pools,
        )
        return False
    try:
        old_value = int(pools[_SDU_POINTS_POOL_INDEX])
    except Exception:
        old_value = 0
    try:
        pools[_SDU_POINTS_POOL_INDEX] = _MAX_SDU_POINTS
    except Exception as e:
        _log_err("msbt_maxsdu: direct PointsAcquiredPerPool write failed: %s", e)
        return False
    try:
        setattr(mgr, "ProgressGraphsArrayDirty", 3)
    except Exception:
        pass
    _log(
        "msbt_maxsdu: set PointsAcquiredPerPool[%s] %s -> %s.",
        _SDU_POINTS_POOL_INDEX,
        old_value,
        _MAX_SDU_POINTS,
    )
    return True


def _set_experience_level_via_bp(ps: Any, track_index: int, level: int) -> bool:
    es = getattr(ps, "ExperienceState", None)
    if es is None:
        _log_err("PlayerState has no ExperienceState array.")
        return False
    try:
        n = len(es)
    except Exception as e:
        _log_err("ExperienceState length: %s", e)
        return False
    if track_index < 0 or track_index >= n:
        _log_err("Experience track index %s out of range (0..%s).", track_index, max(0, n - 1))
        return False

    requested = max(0, int(level))
    lvl = _clamp_engine_experience_level(track_index, requested)
    if lvl != requested:
        _log(
            "ExperienceState[%s]: clamped requested level %s to %s (engine cap for this track).",
            track_index,
            requested,
            lvl,
        )

    try:
        row = es[track_index]
    except Exception as e:
        _log_err("ExperienceState[%s] read failed: %s", track_index, e)
        return False

    candidates = _candidate_experience_tokens(track_index, row)
    if not candidates:
        _log_err("ExperienceState[%s]: could not determine experience token name.", track_index)
        return False

    last_error: Optional[Exception] = None
    for token in candidates:
        xp_def = _make_experience_def_ptr(token)
        if xp_def is None:
            continue
        try:
            before = ps.BP_GetExperienceLevel(xp_def)
        except Exception:
            before = None
        try:
            ps.BP_SetExperienceLevel(xp_def, lvl)
        except Exception as e:
            last_error = e
            continue
        try:
            after = ps.BP_GetExperienceLevel(xp_def)
        except Exception:
            after = None
        if after == lvl or before != after or token == candidates[-1]:
            _log(
                "ExperienceState[%s]: BP_SetExperienceLevel token=%r level %s -> %s (requested %s).",
                track_index,
                token,
                before,
                after,
                requested,
            )
            return True

    if last_error is not None:
        _log_err("BP_SetExperienceLevel failed for ExperienceState[%s]: %s", track_index, last_error)
    else:
        _log_err("BP_SetExperienceLevel failed for ExperienceState[%s].", track_index)
    return False


def _do_give_currency(kind_raw: str, amount: int, name_sub: str) -> None:
    if not name_sub:
        _log_err("Usage: givecurrency <kind> <amount> name <substring>  — kinds: cash, eridium, vaultcard1, vaultcard2, vaultcard3")
        return
    key = (kind_raw or "").strip().lower()
    token = _CURRENCY_KIND_ALIASES.get(key)
    if not token:
        _log_err("Unknown currency kind %r — use cash, eridium, vaultcard1, vaultcard2, vaultcard3.", kind_raw)
        return
    if amount == 0:
        _log_err("Amount must be non-zero.")
        return
    if amount < -_INT32_MAX:
        _log_err("Negative amount out of int32 range.")
        return
    if amount > _MAX_WALLET_AMOUNT:
        _log_err("Amount above supported max wallet/int32 limit (%s).", _MAX_WALLET_AMOUNT)
        return
    pc, err = _resolve_target_pc_for_name(name_sub)
    if pc is None:
        _log_err("givecurrency: %s", err)
        return

    # GiveCurrency takes a 32-bit integer amount in current SDK builds, so large
    # wallet targets are delivered in int32-safe chunks.
    remaining = int(amount)
    if remaining < 0:
        if not _give_currency_on_pc(pc, token, remaining):
            _log_err("givecurrency failed for token=%s amount=%s.", token, remaining)
        return

    chunks = 0
    while remaining > 0:
        chunk = min(remaining, _INT32_MAX)
        if not _give_currency_on_pc(pc, token, chunk):
            _log_err("givecurrency failed for token=%s chunk=%s remaining=%s.", token, chunk, remaining)
            return
        remaining -= chunk
        chunks += 1
    if chunks > 1:
        _log("GiveCurrency delivered %s total to token=%s in %s chunks.", amount, token, chunks)


def _do_give_experience(track_raw: str, level: int, name_sub: str) -> None:
    if not name_sub:
        _log_err(
            "Usage: giveexperience <track> <level> name <substring>  — slots: 0 player level, 1 specialization, "
            "2 vault card 01, 3 vault card 02 (or aliases character/player, specialization, vaultcard_xp_1/2), "
            "or digit 0..3."
        )
        return
    tkey = _normalize_track_key(track_raw)
    if tkey not in _EXPERIENCE_TRACK_ALIASES:
        _log_err(
            "Unknown track %r — use slots 0..3 or character/player, specialization, vaultcard_xp_1, vaultcard_xp_2.",
            track_raw,
        )
        return
    if level < 0:
        _log_err("Level must be non-negative.")
        return
    world, gs = _gbc_session_world_and_gamestate()
    if world is None or gs is None:
        _log_err("giveexperience: no world or GameState")
        return
    if not _gbc_is_listen_host_world(world):
        _log_err("giveexperience: listen host only")
        return
    player_idx, err = _gbc_resolve_player_index_for_name_substring(gs, name_sub)
    if err:
        _log_err("giveexperience: %s", err)
        return
    pa = getattr(gs, "PlayerArray", None)
    if pa is None:
        _log_err("giveexperience: PlayerArray missing")
        return
    try:
        ps = pa[player_idx]
    except Exception as e:
        _log_err("giveexperience: could not read PlayerState: %s", e)
        return
    if ps is None:
        _log_err("giveexperience: null PlayerState")
        return
    es = getattr(ps, "ExperienceState", None)
    try:
        es_n = len(es) if es is not None else 0
    except Exception:
        es_n = 0
    track_idx = _EXPERIENCE_TRACK_ALIASES[tkey]
    if track_idx < 0 or track_idx >= es_n:
        _log_err(
            "giveexperience: slot %s for track %r out of range (ExperienceState length %s).",
            track_idx,
            track_raw,
            es_n,
        )
        return
    if not _set_experience_level_via_bp(ps, track_idx, level):
        _log_err("giveexperience: BP_SetExperienceLevel failed.")


def _do_msbt_maxsdu(parts: List[str]) -> None:
    pc, err = _resolve_target_pc_from_parts(parts, "msbt_maxsdu")
    if pc is None:
        _log_err("msbt_maxsdu: %s", err)
        return
    if not _set_max_sdu_points_on_pc(pc):
        _log_err("msbt_maxsdu: failed.")


@command(
    "givecurrency",
    description=(
        "Listen host: GbxCurrencyFunctionLibrary.GiveCurrency for one player. "
        "Usage: givecurrency <kind> <amount> name <substring>  — kinds: cash, eridium, vaultcard1, vaultcard2, vaultcard3. "
        "Verify in-game: client wallet updates; ambiguous name → gbc_players."
    ),
)
def _cmd_givecurrency(args: argparse.Namespace) -> None:
    parts = [str(p) for p in (getattr(args, "parts", None) or [])]
    head, name_sub = _parse_name_suffix(parts)
    if len(head) < 2:
        _log_err("Usage: givecurrency <kind> <amount> name <substring>")
        return
    kind_raw = head[0]
    amt = _safe_int(head[1])
    if amt is None:
        _log_err("givecurrency: expected integer amount after kind, got %r", head[1])
        return
    _do_give_currency(kind_raw, amt, name_sub)


_cmd_givecurrency.add_argument(
    "parts",
    nargs="+",
    help="kind amount name substring (multi-word name after name)",
)


@command(
    "giveexperience",
    description=(
        "Listen host: set one player's experience level via OakPlayerState.BP_SetExperienceLevel "
        "using a GbxExperienceDef FGbxDefPtr. Slots: 0 player, 1 specialization, "
        "2 vault 01, 3 vault 02. Character uses token 'Character'; other tracks reuse "
        "their ExperienceState token when available. Usage: giveexperience <track> <level> name <substring>."
    ),
)
def _cmd_giveexperience(args: argparse.Namespace) -> None:
    parts = [str(p) for p in (getattr(args, "parts", None) or [])]
    head, name_sub = _parse_name_suffix(parts)
    if len(head) < 2:
        _log_err("Usage: giveexperience <track> <level> name <substring>")
        return
    track_raw = head[0]
    lvl = _safe_int(head[1])
    if lvl is None:
        _log_err("giveexperience: expected integer level, got %r", head[1])
        return
    _do_give_experience(track_raw, lvl, name_sub)


_cmd_giveexperience.add_argument(
    "parts",
    nargs="+",
    help="track level name substring",
)
