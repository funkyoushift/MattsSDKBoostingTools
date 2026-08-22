"""MSBT Extreme Combat XP — multi-track XP multiplier (Character + Spec + Vault).

Port of tools/ExtremeCombatXP for host-side all-player boosting via MSBT UI.
Always processes every live PlayerState (host + drop-ins). Starts OFF until toggled.
"""

from __future__ import annotations

import math
import re
import time
from typing import Any

from mods_base import get_pc, hook
from unrealsdk import find_all, find_object, logging
from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

__version__ = "0.5.0"
__version_info__ = (0, 5, 0)

# At/above this multiplier, one combat kill fills remaining Spec/Vault ranks.
_EXTREME_MULT_ONE_KILL_FILL = 100_000.0

_PREFIX = "[Matts SDK Boosting Tools | CXP]"
_DEFAULT_MULT = 1000.0
_INT32_MAX = 2_147_483_647
_MAX_LEVEL_BY_TRACK = {
    0: 60,  # Character
    1: 701,  # Specialization
    2: 9_999_999,  # Vault cards
    3: 9_999_999,
    4: 9_999_999,
    5: 9_999_999,
}
_TRACK_TOKEN_FALLBACKS: dict[int, tuple[str, ...]] = {
    0: ("Character",),
    1: ("Specialization", "Specialisation"),
    2: ("VaultCard01", "VaultCard1", "VaultCard01_XP", "VaultCard01_Experience"),
    3: ("VaultCard02", "VaultCard2", "VaultCard02_XP", "VaultCard02_Experience"),
    4: ("VaultCard03", "VaultCard3", "VaultCard03_XP", "VaultCard03_Experience"),
    5: ("VaultCard04", "VaultCard4", "VaultCard04_XP", "VaultCard04_Experience"),
}
_EXPERIENCE_DEF_PATHS = (
    "/Script/GbxGame.GbxExperienceDef",
    "/Script/OakGame.GbxExperienceDef",
)

_STABLE_NEED = 60
_GRACE_TICKS = 180

# per-player: key -> state
_player_state: dict[str, dict[str, Any]] = {}
_tick_n = 0
_topups = 0
_attr_writes = 0
_applying = False

# MSBT-controlled state (not mods_base options — toggled from Electron / QM).
_enabled = False
_mult_value = float(_DEFAULT_MULT)
_boost_spec_vault_on_combat = True
_max_levels_value = 701


def _log(msg: str) -> None:
    try:
        logging.info(f"{_PREFIX} {msg}")
    except Exception:
        print(f"{_PREFIX} {msg}")


_HOT_ERROR_INTERVAL_S = 5.0
_hot_error_last_at: dict[str, float] = {}


def _log_hot_error(msg: str) -> None:
    now = time.monotonic()
    if now - _hot_error_last_at.get(msg, 0.0) < _HOT_ERROR_INTERVAL_S:
        return
    _hot_error_last_at[msg] = now
    _log(msg)


def _mult() -> float:
    try:
        return float(_mult_value)
    except Exception:
        return float(_DEFAULT_MULT)


def _max_levels_per_award() -> int:
    try:
        return max(1, min(100_000, int(_max_levels_value)))
    except Exception:
        return 50


def _clamp_gain(current: int, amount: int) -> int:
    if amount <= 0:
        return 0
    room = _INT32_MAX - max(0, int(current))
    return min(int(amount), room)


def _ps_key(ps: Any) -> str:
    try:
        return str(ps)
    except Exception:
        return repr(ps)


def _ps_from_pc(pc: Any) -> Any:
    if pc is None:
        return None
    for attr in ("PlayerState", "OakPlayerState", "AcknowledgedPlayerState"):
        try:
            ps = getattr(pc, attr, None)
        except Exception:
            ps = None
        if ps is not None:
            return ps
    return None


def _iter_player_states() -> list[Any]:
    out: list[Any] = []
    seen: set[str] = set()
    try:
        local = _ps_from_pc(get_pc())
    except Exception:
        local = None
    if local is not None:
        seen.add(_ps_key(local))
        out.append(local)
    world = None
    try:
        from mods_base import ENGINE

        world = ENGINE.GameViewport.World
    except Exception:
        world = None
    try:
        gs = world.GameState if world is not None else None
        arr = getattr(gs, "PlayerArray", None) if gs is not None else None
    except Exception:
        arr = None
    if arr is None:
        return out
    try:
        n = len(arr)
    except Exception:
        n = 0
    for i in range(n):
        try:
            ps = arr[i]
        except Exception:
            continue
        if ps is None:
            continue
        key = _ps_key(ps)
        if key in seen:
            continue
        seen.add(key)
        out.append(ps)
    return out


def _state_for(ps: Any) -> dict[str, Any]:
    key = _ps_key(ps)
    st = _player_state.get(key)
    if st is None:
        st = {
            "last_points": {},  # track -> int
            "armed": False,
            "stable": 0,
            "grace": _GRACE_TICKS,
            "last_write_ok": False,
        }
        _player_state[key] = st
    return st


def _disarm_player(ps: Any, reason: str) -> None:
    st = _state_for(ps)
    st["armed"] = False
    st["stable"] = 0
    st["last_points"] = {}
    st["grace"] = _GRACE_TICKS
    _log(f"disarm {_ps_key(ps)[-48:]} ({reason})")


def _disarm_all(reason: str) -> None:
    _player_state.clear()
    _log(f"disarm all ({reason})")


def _make_experience_def_ptr(token: str) -> Any:
    try:
        from unrealsdk.unreal import FGbxDefPtr
    except Exception as exc:
        _log(f"FGbxDefPtr import failed: {exc!r}")
        return None
    struct_u = None
    for path in _EXPERIENCE_DEF_PATHS:
        try:
            obj = find_object("ScriptStruct", path)
        except Exception:
            obj = None
        if obj is not None:
            struct_u = obj
            break
    if struct_u is None:
        try:
            for candidate in find_all("ScriptStruct", False) or []:
                if getattr(candidate, "Name", None) == "GbxExperienceDef":
                    struct_u = candidate
                    break
        except Exception:
            pass
    if struct_u is None:
        return None
    tail = (token or "").strip().split("/")[-1]
    if not tail:
        return None
    try:
        return FGbxDefPtr(tail, struct_u)
    except Exception:
        try:
            return FGbxDefPtr(tail, type="GbxExperienceDef")
        except Exception as exc:
            _log(f"FGbxDefPtr({tail!r}) failed: {exc!r}")
            return None


def _token_from_row(row: Any) -> str | None:
    try:
        eid = row.ExperienceId
    except Exception:
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
    # InlineToken Name: 'Character' style from probe
    m = re.search(r"InlineToken.*?Name:\s*'([^']+)'", text, re.DOTALL)
    if m:
        return m.group(1)
    return None


def _track_tokens(track: int, row: Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for token in (_token_from_row(row), *(_TRACK_TOKEN_FALLBACKS.get(track, ()))):
        if token and token not in seen:
            seen.add(token)
            out.append(token)
    return out


def _es_len(ps: Any) -> int:
    try:
        return len(ps.ExperienceState)
    except Exception:
        return 0


def _row(ps: Any, track: int) -> Any:
    try:
        return ps.ExperienceState[track]
    except Exception:
        return None


def _read_points(ps: Any, track: int) -> int | None:
    row = _row(ps, track)
    if row is None:
        return None
    try:
        return int(row.ExperiencePoints)
    except Exception:
        return None


def _read_level(ps: Any, track: int) -> int | None:
    row = _row(ps, track)
    if row is not None:
        try:
            return int(row.ExperienceLevel)
        except Exception:
            pass
    get_fn = getattr(ps, "BP_GetExperienceLevel", None)
    if not callable(get_fn) or row is None:
        return None
    for token in _track_tokens(track, row):
        exp_def = _make_experience_def_ptr(token)
        if exp_def is None:
            continue
        try:
            return int(get_fn(exp_def))
        except Exception:
            continue
    return None


def _read_next_req(ps: Any, track: int) -> int | None:
    row = _row(ps, track)
    if row is None:
        return None
    try:
        return int(row.ExperiencePointsRequiredForNextLevel)
    except Exception:
        return None


def _read_prev_req(ps: Any, track: int) -> int | None:
    row = _row(ps, track)
    if row is None:
        return None
    try:
        return int(row.ExperiencePointsRequiredForPreviousLevel)
    except Exception:
        return None


def _max_level(track: int) -> int:
    if track in _MAX_LEVEL_BY_TRACK:
        return _MAX_LEVEL_BY_TRACK[track]
    if track >= 2:
        return 9_999_999
    return 60


def _set_experience_level(ps: Any, track: int, level: int) -> bool:
    set_fn = getattr(ps, "BP_SetExperienceLevel", None)
    if not callable(set_fn):
        return False
    row = _row(ps, track)
    if row is None:
        return False
    lv = max(1, min(int(level), _max_level(track)))
    for token in _track_tokens(track, row):
        exp_def = _make_experience_def_ptr(token)
        if exp_def is None:
            continue
        try:
            set_fn(exp_def, lv)
            return True
        except Exception:
            continue
    return False


def _write_points(ps: Any, track: int, points: int) -> bool:
    row = _row(ps, track)
    if row is None:
        return False
    target = max(0, min(int(points), _INT32_MAX))
    try:
        row.ExperiencePoints = int(target)
        return True
    except Exception:
        try:
            setattr(row, "ExperiencePoints", int(target))
            return True
        except Exception:
            return False


def _clamp_points_into_bar(ps: Any, track: int) -> int | None:
    pts = _read_points(ps, track)
    prev = _read_prev_req(ps, track)
    nxt = _read_next_req(ps, track)
    if pts is None:
        return None
    lo = prev if prev is not None else 0
    hi = (nxt - 1) if (nxt is not None and nxt > lo) else _INT32_MAX
    clamped = max(lo, min(int(pts), hi, _INT32_MAX))
    if clamped != pts:
        _write_points(ps, track, clamped)
    return _read_points(ps, track)


def _cap_target(ps: Any, track: int, target_points: int, max_levels: int) -> int:
    prev = _read_prev_req(ps, track) or 0
    nxt = _read_next_req(ps, track)
    if nxt is None or nxt <= prev:
        return min(target_points, _INT32_MAX)
    span = max(1, nxt - prev)
    ceiling = prev + span * max_levels + (span - 1)
    # Vault spans can be huge; still int32-cap the write.
    return max(0, min(int(target_points), int(ceiling), _INT32_MAX))


def _rank_levels_from_mult(track: int, cur_level: int) -> int:
    """Spec/Vault levels to grant from one Character combat XP signal.

    Does not use ExperiencePoints math — Spec needs ~7.4e9 XP by 701 (past int32).
    Extreme multiplier (≥100k) fills remaining ranks in one kill.
    """
    remain = max(0, _max_level(track) - max(1, int(cur_level)))
    if remain <= 0:
        return 0
    mult = _mult()
    if mult >= _EXTREME_MULT_ONE_KILL_FILL:
        return remain
    # Moderate: jump about `mult` levels, soft-capped by the slider.
    soft = _max_levels_per_award()
    return max(1, min(remain, soft, int(math.ceil(mult))))


def _jump_track_to_level(ps: Any, track: int, new_level: int) -> bool:
    cur = _read_level(ps, track) or 1
    target = max(1, min(int(new_level), _max_level(track)))
    if target <= cur:
        return False
    if not _set_experience_level(ps, track, target):
        return False
    _clamp_points_into_bar(ps, track)
    return True


def _apply_rank_jump_from_combat(ps: Any, track: int) -> bool:
    """Jump Spec/Vault via BP_SetExperienceLevel after a Character combat signal."""
    if track < 1:
        return False
    before_lv = _read_level(ps, track)
    if before_lv is None:
        return False
    jump = _rank_levels_from_mult(track, before_lv)
    if jump <= 0:
        return False
    new_lv = min(_max_level(track), before_lv + jump)
    if not _jump_track_to_level(ps, track, new_lv):
        return False
    after_lv = _read_level(ps, track)
    after_pts = _read_points(ps, track)
    global _topups
    _topups += 1
    _log(
        f"rank-jump #{_topups} track{track}: x{_mult():g} "
        f"lv {before_lv}->{after_lv} (+{jump}) pts={after_pts}"
    )
    return True


def _apply_boost_to_track(ps: Any, track: int, target_points: int, award_hint: int | None = None) -> bool:
    """Character-track point top-up + level-ups. Spec/Vault should use rank jumps instead."""
    max_lv_gain = _max_levels_per_award()
    cur_level = _read_level(ps, track) or 1
    level_cap = min(_max_level(track), cur_level + max_lv_gain)
    before_pts = _read_points(ps, track) or 0
    award = award_hint if award_hint is not None else max(0, int(target_points) - before_pts)
    target_points = _cap_target(ps, track, target_points, max_lv_gain)

    ok_pts = _write_points(ps, track, target_points)
    levels_gained = 0
    for _ in range(min(max_lv_gain, 2000)):
        lv = _read_level(ps, track)
        pts = _read_points(ps, track)
        nxt = _read_next_req(ps, track)
        if lv is None or pts is None or nxt is None:
            break
        if lv >= level_cap or lv >= _max_level(track) or pts < nxt:
            break
        if nxt > _INT32_MAX:
            break
        if not _set_experience_level(ps, track, lv + 1):
            break
        levels_gained += 1
        _write_points(ps, track, target_points)

    # If point math bought nothing useful (huge spans / int32 wall), jump by mult.
    if levels_gained == 0 and award > 0 and track >= 1:
        jump = _rank_levels_from_mult(track, cur_level)
        if jump > 0 and _jump_track_to_level(ps, track, cur_level + jump):
            levels_gained = jump

    _clamp_points_into_bar(ps, track)
    return bool(ok_pts or levels_gained > 0)


def _snapshot_points(ps: Any) -> dict[int, int]:
    snap: dict[int, int] = {}
    n = _es_len(ps)
    for track in range(n):
        pts = _read_points(ps, track)
        if pts is not None:
            snap[track] = pts
    return snap


def _arming_tick(ps: Any, snap: dict[int, int]) -> bool:
    st = _state_for(ps)
    if st["grace"] > 0:
        st["grace"] -= 1
        st["last_points"] = dict(snap)
        st["stable"] = 0
        st["armed"] = False
        return False

    last: dict[int, int] = st["last_points"]
    if not st["armed"]:
        if not last:
            st["last_points"] = dict(snap)
            st["stable"] = 1
            return False
        if snap != last:
            st["last_points"] = dict(snap)
            st["stable"] = 1
            return False
        st["stable"] = int(st["stable"]) + 1
        if st["stable"] >= _STABLE_NEED:
            st["armed"] = True
            _log(f"armed {_ps_key(ps)[-40:]} tracks={sorted(snap.keys())}")
        return False
    return True


def _boost_track_from_delta(ps: Any, track: int, old_pts: int, new_pts: int) -> bool:
    delta = new_pts - old_pts
    if delta <= 0:
        return False
    # Spec/Vault: never rely on int32 point top-ups for rank progress.
    if track >= 1:
        return _apply_rank_jump_from_combat(ps, track)

    prev = _read_prev_req(ps, track) or 0
    nxt = _read_next_req(ps, track)
    span = max(1, (nxt - prev) if nxt is not None and nxt > prev else 2000)
    # Oversized single-frame jump = sync, not combat (except we already armed).
    if delta > span * 8 and track == 0:
        return False

    extra = _clamp_gain(new_pts, int(math.floor(delta * (_mult() - 1.0))))
    if extra <= 0:
        return False
    target = min(new_pts + extra, _INT32_MAX)
    before_lv = _read_level(ps, track)
    ok = _apply_boost_to_track(ps, track, target, award_hint=extra + delta)
    after_pts = _read_points(ps, track)
    after_lv = _read_level(ps, track)
    if ok:
        global _topups
        _topups += 1
        _log(
            f"top-up #{_topups} track{track}: +{delta} x{_mult():g} "
            f"pts {new_pts}->{after_pts} lv {before_lv}->{after_lv}"
        )
    return ok


def _process_player(ps: Any) -> None:
    global _applying
    if ps is None or _applying:
        return
    if not bool(_enabled) or _mult() <= 1.0:
        return

    snap = _snapshot_points(ps)
    if not snap:
        return
    if not _arming_tick(ps, snap):
        return

    st = _state_for(ps)
    last: dict[int, int] = st["last_points"]
    if not last:
        st["last_points"] = dict(snap)
        return

    _applying = True
    try:
        combat_delta = 0
        jumped_ranks: set[int] = set()
        # First: native deltas on each track
        for track, new_pts in sorted(snap.items()):
            old_pts = last.get(track)
            if old_pts is None:
                continue
            if new_pts < old_pts:
                # Engine rewrite / spend — refresh baseline for this track only
                last[track] = new_pts
                continue
            if new_pts == old_pts:
                continue
            if track == 0:
                combat_delta = new_pts - old_pts
            if _boost_track_from_delta(ps, track, old_pts, new_pts) and track >= 1:
                jumped_ranks.add(track)

        # Combat kill signal → Spec/Vault rank jumps (BP_SetExperienceLevel, not int32 XP)
        if combat_delta > 0 and bool(_boost_spec_vault_on_combat):
            n = _es_len(ps)
            for track in range(1, n):
                if track in jumped_ranks:
                    continue
                _apply_rank_jump_from_combat(ps, track)

        # Refresh baselines after writes
        st["last_points"] = _snapshot_points(ps)
        st["last_write_ok"] = True
    finally:
        _applying = False


def _process_all() -> None:
    for ps in _iter_player_states():
        try:
            _process_player(ps)
        except Exception as exc:
            _log_hot_error(f"process err: {exc!r}")


def _try_set_combat_xp_attribute(mult: float) -> int:
    wrote = 0
    needles = ("att_combatxp_multiplier", "combatxp_multiplier", "combatexperience")
    paths = (
        "/Game/GameData/Attributes/Att_CombatXP_Multiplier.Att_CombatXP_Multiplier",
        "/Game/GameData/Attributes/Player/Att_CombatXP_Multiplier.Att_CombatXP_Multiplier",
    )
    objs: list[Any] = []
    for path in paths:
        try:
            objs.append(find_object("Object", path))
        except Exception:
            pass
    for class_name in ("GbxAttributeData", "AttributeDefinition", "GbxAttributeDefinition"):
        try:
            objs.extend(list(find_all(class_name, False) or []))
        except TypeError:
            try:
                objs.extend(list(find_all(class_name) or []))
            except Exception:
                pass
        except Exception:
            pass
    for obj in objs:
        if obj is None:
            continue
        try:
            key = f"{getattr(obj, 'Name', '')} {obj}".lower()
        except Exception:
            continue
        if not any(n in key for n in needles):
            continue
        for attr in ("DefaultValue", "Value", "BaseValue", "CurrentValue", "Constant"):
            try:
                cur = getattr(obj, attr)
            except Exception:
                continue
            if cur is not None and not isinstance(cur, (int, float)):
                for nested in ("Value", "Float", "Constant", "BaseValue"):
                    try:
                        setattr(cur, nested, float(mult))
                        wrote += 1
                    except Exception:
                        pass
            try:
                setattr(obj, attr, float(mult))
                wrote += 1
            except Exception:
                pass
    return wrote


def _refresh_attrs() -> None:
    global _attr_writes
    try:
        m = _mult() if bool(_enabled) else 1.0
        _attr_writes = _try_set_combat_xp_attribute(m)
        _log(f"attribute writes={_attr_writes} mult={m:g}")
    except Exception as exc:
        _log(f"attribute refresh failed: {exc!r}")


def on_enable() -> None:
    global _enabled
    _enabled = True
    _disarm_all("enable")
    try:
        _refresh_attrs()
    except Exception as exc:
        _log(f"enable attr refresh deferred (menu/no world): {exc!r}")
    _log(
        f"enabled v{__version__} x{_mult():g} max_lv/award={_max_levels_per_award()} "
        f"spec_vault_on_combat={bool(_boost_spec_vault_on_combat)} "
        f"one_kill_fill_at>={_EXTREME_MULT_ONE_KILL_FILL:g} (all players; armed)"
    )


def on_disable() -> None:
    global _enabled
    _enabled = False
    _disarm_all("disable")
    try:
        _try_set_combat_xp_attribute(1.0)
    except Exception:
        pass
    _log("disabled")


def set_enabled(enabled: bool) -> str:
    if enabled:
        on_enable()
        return f"Combat XP Mult ARMED x{_mult():g} (all players; active in-session)"
    on_disable()
    return "Combat XP Mult OFF"


def toggle_enabled() -> str:
    return set_enabled(not bool(_enabled))


def set_multiplier(mult: float) -> str:
    global _mult_value
    try:
        val = float(mult)
    except Exception:
        return "Combat XP multiplier must be a number."
    if val <= 0:
        return "Combat XP multiplier must be > 0."
    _mult_value = val
    if bool(_enabled):
        try:
            _disarm_all("mult-change")
            _refresh_attrs()
        except Exception as exc:
            _log(f"mult attr refresh deferred: {exc!r}")
    return f"Combat XP multiplier set to x{_mult():g}" + (" (armed)" if _enabled else " (enable to apply)")


def get_status_dict() -> dict[str, Any]:
    players = _iter_player_states()
    mult = _mult()
    return {
        "enabled": bool(_enabled),
        "multiplier": mult,
        "one_kill_fill": mult >= _EXTREME_MULT_ONE_KILL_FILL,
        "boost_spec_vault": bool(_boost_spec_vault_on_combat),
        "max_levels_per_award": _max_levels_per_award(),
        "players": len(players),
        "topups": int(_topups),
        "ticks": int(_tick_n),
        "attr_writes": int(_attr_writes),
        "scope": "all_players",
    }


def status_message() -> str:
    st = get_status_dict()
    return (
        f"CXP enabled={st['enabled']} mult={st['multiplier']:g} "
        f"one_kill_fill={st['one_kill_fill']} players={st['players']} "
        f"topups={st['topups']} (always all players)"
    )


def reapply() -> str:
    _disarm_all("re-apply")
    _refresh_attrs()
    return status_message()


def _on_tick_frame() -> None:
    global _tick_n
    if not bool(_enabled):
        return
    _tick_n += 1
    if (_tick_n % 3) != 0:
        return
    _process_all()


def _camera_tick(
    _obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _fn: BoundFunction,
) -> None:
    _on_tick_frame()


try:
    from . import camera_tick

    camera_tick.register("cxp", _camera_tick, priority=60)
    _log("camera tick hook registered")
except Exception as exc:
    _log(f"camera tick hook FAILED: {exc!r}")


@hook(
    "OakGame.OakPlayerState:OnRep_ExperienceState",
    Type.POST,
    immediately_enable=True,
    hook_identifier="msbt_cxp_onrep_xp_v1",
)
def _on_rep_experience(obj: UObject, _args: WrappedStruct, _ret: Any, _func: BoundFunction) -> None:
    if bool(_enabled):
        _process_player(obj)


@hook(
    "OakGame.OakPlayerController:ClientTravel",
    Type.POST,
    immediately_enable=True,
    hook_identifier="msbt_cxp_travel_oak_v1",
)
@hook(
    "Engine.PlayerController:ClientTravel",
    Type.POST,
    immediately_enable=True,
    hook_identifier="msbt_cxp_travel_engine_v1",
)
def _travel(*_args: Any, **_kwargs: Any) -> None:
    _disarm_all("travel")
    # Do not write combat-XP attributes during ClientTravel / join.


_log(f"loaded v{__version__} (MSBT helper, starts OFF)")
