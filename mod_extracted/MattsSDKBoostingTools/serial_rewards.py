"""Loyalty reward grant + serial injection (formerly Matt's Serial Reward Adder)."""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, List, Optional, Tuple

import unrealsdk
from mods_base import command, get_pc, hook
from unrealsdk import find_all, find_class, find_object, make_struct

from .party_helpers import (
    _gbc_find_pc_for_player_state,
    _gbc_resolve_player_index_for_name_substring,
    _gbc_run_session_timer_from_give_serial,
    _gbc_session_world_and_gamestate,
)
from unrealsdk.unreal import FGbxDefPtr, UObject
from unrealsdk import logging

# Default reward def (edit here). Same id as Nexus rewards'ChallengeReward_Loyalty_Jakobs'.
DEFAULT_REWARD_DEF_NAME = "ChallengeReward_Loyalty_Jakobs"

# Generic manufacturer loyalty packages (Nexus ids). Order matches in-game "Loyalty Reward" list;
# Ripper uses ChallengeReward_Loyalty_Borg in Nexus data. Each successful Give_Serial advances to the next.
LOYALTY_REWARD_DEF_NAMES: Tuple[str, ...] = (
    "ChallengeReward_Loyalty_Daedalus",
    "ChallengeReward_Loyalty_Jakobs",
    "ChallengeReward_Loyalty_Maliwan",
    "ChallengeReward_Loyalty_Order",
    "ChallengeReward_Loyalty_Borg",  # Ripper (UI)
    "ChallengeReward_Loyalty_Tediore",
    "ChallengeReward_Loyalty_Torgue",
    "ChallengeReward_Loyalty_Vladof",
)

# In-memory only; resets when the game restarts.
_loyalty_rotation_index: int = 0

# ScriptStruct paths for FGbxDefPtr.ref (same as bl4_reward_generator when find_object cannot resolve by name).
REWARDS_DEF_SCRIPT_PATHS = (
    "/Script/GbxGame.GbxRewardsDef",
    "/Script/OakGame.GbxRewardsDef",
)

_PATCH_RETRY_ATTEMPTS = 5
_PATCH_RETRY_DELAY_SEC = 0.08
_TICK_PATCH_MAX_ATTEMPTS = 180
_TICK_PATCH_LOG_EVERY = 30
# Keep reward SerialNumbers payloads comfortably below the observed client-delivery failure boundary.
# Remote clients have shown unreliable delivery around ~30k+ raw Base85 chars per reward package,
# so hard-cap each serial reward package at a much smaller 20k estimated payload budget.
_MAX_SERIAL_DELIVERY_CHARS = 20000
_SERIAL_DELIVERY_SAFE_CHARS = 20000
_SERIAL_DELIVERY_SAFE_SERIALS_SELECTED = 30
_SERIAL_DELIVERY_SAFE_SERIALS_MULTI = 25
_SERIAL_DELIVERY_PER_SERIAL_OVERHEAD_CHARS = 16
# Automatic chunk delivery pacing.  Keep this main-thread/tick driven; no sleeps.
_SERIAL_DELIVERY_PRE_OPEN_DELAY_SEC = 1.00
_SERIAL_DELIVERY_POST_OPEN_DELAY_SEC = 2.00
_SERIAL_DELIVERY_SELECTED_POST_OPEN_DELAY_SEC = 2.00
_SERIAL_DELIVERY_MULTI_POST_OPEN_DELAY_SEC = 2.50
_SERIAL_DELIVERY_PATCH_MAX_ATTEMPTS = 120
_SERIAL_DELIVERY_PATCH_LOG_EVERY = 30
_SERIAL_DELIVERY_BACKPACK_HEADROOM = 100

def _clamp_serial_delivery_delay(value: float) -> float:
    try:
        return max(0.0, min(5.0, float(value)))
    except Exception:
        return 0.0


def set_serial_delivery_timing(pre_open_delay: float | None = None, post_open_delay: float | None = None) -> tuple[float, float]:
    """Set automatic chunk-delivery delays. Values are clamped to 0..5 seconds."""
    global _SERIAL_DELIVERY_PRE_OPEN_DELAY_SEC, _SERIAL_DELIVERY_POST_OPEN_DELAY_SEC
    if pre_open_delay is not None:
        _SERIAL_DELIVERY_PRE_OPEN_DELAY_SEC = _clamp_serial_delivery_delay(pre_open_delay)
    if post_open_delay is not None:
        _SERIAL_DELIVERY_POST_OPEN_DELAY_SEC = _clamp_serial_delivery_delay(post_open_delay)
    return (_SERIAL_DELIVERY_PRE_OPEN_DELAY_SEC, _SERIAL_DELIVERY_POST_OPEN_DELAY_SEC)


def serial_delivery_timing() -> tuple[float, float]:
    """Return current automatic chunk-delivery delays: post-delivery, post-open."""
    return (_SERIAL_DELIVERY_PRE_OPEN_DELAY_SEC, _SERIAL_DELIVERY_POST_OPEN_DELAY_SEC)


def _serial_delivery_mode_key(mode: str | None) -> str:
    key = str(mode or "selected").strip().lower().replace("-", "_")
    if key in ("all", "party", "all_party"):
        return "all"
    if key in ("nonhost", "non_host", "all_non_host"):
        return "nonhost"
    return "selected"


def _serial_delivery_max_serials_per_chunk(mode: str | None = None) -> int:
    key = _serial_delivery_mode_key(mode)
    if key in ("all", "nonhost"):
        return _SERIAL_DELIVERY_SAFE_SERIALS_MULTI
    return _SERIAL_DELIVERY_SAFE_SERIALS_SELECTED


def _serial_delivery_post_open_delay(mode: str | None = None) -> float:
    key = _serial_delivery_mode_key(mode)
    if key in ("all", "nonhost"):
        return _SERIAL_DELIVERY_MULTI_POST_OPEN_DELAY_SEC
    return _SERIAL_DELIVERY_SELECTED_POST_OPEN_DELAY_SEC


# Same contract as Legit Builder SERIAL_API_URL (POST JSON {"deserialized": "…"} → {"serial_b85": "…"}).
_DEFAULT_GENIE_SERIALIZE_API_URL = "https://save-editor.be/nicnl/api.php"
_BASE85_TOKEN_RE = re.compile(r"^@[!-~]+$")
# BL4-style deserialized human line: leading root tuple then first pipe (e.g. "7, 0, 1, 60| …").
_DESERIALIZED_HUMAN_HEAD_RE = re.compile(r"^\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\|")


def _genie_serialize_api_url() -> str:
    raw = os.environ.get("GENIE_SERIALIZE_API_URL", "").strip()
    return raw or _DEFAULT_GENIE_SERIALIZE_API_URL


def _genie_serialize_enabled() -> bool:
    raw = os.environ.get("GENIE_SERIALIZE_ENABLED", "").strip().lower()
    if not raw:
        return True
    return raw not in ("0", "false", "no", "off")


def _looks_like_base85(s: str) -> bool:
    t = (s or "").strip()
    return len(t) >= 10 and bool(_BASE85_TOKEN_RE.match(t))


def _looks_like_deserialized_human(s: str) -> bool:
    t = (s or "").strip()
    if not t or _looks_like_base85(t):
        return False
    if "|" not in t:
        return False
    return bool(_DESERIALIZED_HUMAN_HEAD_RE.match(t))


def _normalize_serial_b85(b85: str) -> str:
    b = b85.strip()
    if not b:
        return b
    return b if b.startswith("@") else f"@{b}"


def _expand_serial_token(p: str) -> List[str]:
    """One token -> one or more serial strings without corrupting Base85.

    BL4 Base85 serials can contain punctuation, so do not split a token on
    commas/semicolons. If multiple serials were accidentally pasted into one
    token, split only at the next @U prefix.
    """
    t = p.strip()
    if not t:
        return []
    if _looks_like_deserialized_human(t):
        return [t]
    starts = [m.start() for m in re.finditer(r"(?=@U)", t)]
    if len(starts) > 1:
        starts.append(len(t))
        return [t[starts[i]:starts[i + 1]].strip() for i in range(len(starts) - 1) if t[starts[i]:starts[i + 1]].strip()]
    return [t]


def _serialize_deserialized_to_b85(deserialized: str) -> str:
    url = _genie_serialize_api_url()
    payload = json.dumps({"deserialized": deserialized}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        # HTTPError subclasses URLError; handle before URLError.
        detail = ""
        try:
            detail = e.read().decode("utf-8", errors="replace")[:400]
        except Exception:
            pass
        raise RuntimeError(f"HTTP {e.code} from serialize API: {detail}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Serialize API network error: {e}") from e

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Serialize API returned invalid JSON: {e}") from e
    if not isinstance(data, dict):
        raise RuntimeError("Serialize API returned non-object JSON")
    err = data.get("error")
    if err:
        raise RuntimeError(str(err))
    b85 = data.get("serial_b85")
    if not isinstance(b85, str) or not b85.strip():
        raise RuntimeError("Serialize API response missing serial_b85")
    return _normalize_serial_b85(b85)


def _resolve_give_serial_strings(raw_serials: List[str]) -> Optional[List[str]]:
    """Convert deserialized human lines to Base85 via HTTP; abort whole command on first failure."""
    out: List[str] = []
    for idx, s in enumerate(raw_serials):
        t = s.strip()
        if not t:
            continue
        if _looks_like_base85(t):
            out.append(t)
            continue
        if _looks_like_deserialized_human(t):
            if not _genie_serialize_enabled():
                _log_error(
                    "Give_Serial: deserialized human serial detected but GENIE_SERIALIZE_ENABLED is off "
                    "(unset or set to 1/true to allow HTTP serialize)."
                )
                return None
            try:
                b85 = _serialize_deserialized_to_b85(t)
            except Exception as e:
                _log_error(f"Give_Serial: serialize failed for serial #{idx + 1}: {e}")
                return None
            out.append(b85)
            continue
        out.append(t)
    return out


def _log_info(message: str) -> None:
    logging.info(f"[Matts SDK Boosting Tools | Serial] {message}")


def _log_warning(message: str) -> None:
    logging.warning(f"[Matts SDK Boosting Tools | Serial] {message}")


def _log_error(message: str) -> None:
    logging.error(f"[Matts SDK Boosting Tools | Serial] {message}")


def _normalize_nexus_reward_def_arg(s: str) -> str:
    t = (s or "").strip()
    low = t.lower()
    if low.startswith("rewards'") and t.endswith("'") and len(t) > len("rewards'x'"):
        return t[len("rewards'") : -1].strip()
    if low.startswith('rewards"') and t.endswith('"') and len(t) > len('rewards"x"'):
        return t[len('rewards"') : -1].strip()
    return t


def _safe_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(float(text))
        except Exception:
            return None
    return None


def _is_fgbx_def_ptr(o: Any) -> bool:
    if o is None:
        return False
    try:
        from unrealsdk.unreal import FGbxDefPtr as _FG

        return isinstance(o, _FG)
    except Exception:
        return type(o).__name__ == "FGbxDefPtr"


def _coerce_make_gbx_reward_ref_result(o: Any, depth: int = 0) -> Optional[Any]:
    if o is None or depth > 4:
        return None
    if _is_fgbx_def_ptr(o):
        return o
    for attr in (
        "RewardsDef",
        "RewardDef",
        "Reward",
        "Def",
        "DefPtr",
        "GbxDefPtr",
        "value",
        "Value",
    ):
        try:
            v = getattr(o, attr, None)
        except Exception:
            v = None
        if v is None:
            continue
        c = _coerce_make_gbx_reward_ref_result(v, depth + 1)
        if c is not None:
            return c
    if type(o).__name__ == "WrappedStruct" or "Struct" in type(o).__name__:
        try:
            for name in dir(o):
                if name.startswith("_"):
                    continue
                try:
                    v = getattr(o, name, None)
                except Exception:
                    continue
                if v is None or callable(v):
                    continue
                if _is_fgbx_def_ptr(v):
                    return v
                c = _coerce_make_gbx_reward_ref_result(v, depth + 1)
                if c is not None:
                    return c
        except Exception:
            pass
    return None


def _try_make_gbx_reward_ref(lib: Any, pc: Any, mgr: Optional[Any], path: str) -> Optional[Any]:
    mk = getattr(lib, "MakeGbxRewardRef", None)
    if not callable(mk):
        return None
    world = getattr(pc, "World", None)
    owner = None
    for attr in ("GbxRewardsOwner", "RewardsOwner", "RewardOwner"):
        try:
            owner = getattr(pc, attr, None)
            if owner is not None:
                break
        except Exception:
            pass
    tail = path.split("/")[-1]
    seen_id: set = set()
    uniq_ids: List[str] = []
    for s in (path, path.strip(), "rewards'" + tail + "'", "rewards'" + path + "'"):
        if s and s not in seen_id:
            seen_id.add(s)
            uniq_ids.append(s)

    def _try_mk_pair(a: Any, b: Any) -> Optional[Any]:
        try:
            r = mk(a, b)
        except TypeError:
            return None
        except Exception:
            return None
        for candidate in (r, b):
            c = _coerce_make_gbx_reward_ref_result(candidate)
            if c is not None:
                return c
        return None

    struct_names = (
        "RewardRef",
        "GbxRewardRef",
        "FGbxRewardRef",
        "GbxRewardsRewardRef",
        "OakRewardRef",
    )
    for rid in uniq_ids:
        for sn in struct_names:
            try:
                blank = make_struct(sn)
            except Exception:
                continue
            for _label, a, b in (
                ("rid+outStruct", rid, blank),
                ("outStruct+rid", blank, rid),
            ):
                c = _try_mk_pair(a, b)
                if c is not None:
                    return c

        for ctx in (
            pc,
            mgr,
            world,
            owner,
            getattr(pc, "PlayerState", None),
            getattr(pc, "GameInstance", None),
        ):
            if ctx is None:
                continue
            for a, b in ((rid, ctx), (ctx, rid)):
                c = _try_mk_pair(a, b)
                if c is not None:
                    return c

    return None


def _get_gbx_rewards_blueprint_library() -> Optional[Any]:
    try:
        cls = find_class("GbxRewards_BlueprintFunctions")
        if cls is not None:
            cdo = getattr(cls, "ClassDefaultObject", None)
            if cdo is not None:
                return cdo
    except Exception:
        pass
    try:
        objs = find_all("GbxRewards_BlueprintFunctions", False) or []
        if objs:
            return objs[-1]
    except Exception:
        pass
    return None


def _find_rewards_manager_on_pc(pc: Any) -> Tuple[Optional[Any], Optional[str]]:
    for name in (
        "GbxRewardsManager",
        "RewardsManager",
        "RewardManager",
        "MyRewardsManager",
    ):
        try:
            m = getattr(pc, name, None)
            if m is not None:
                return (m, name)
        except Exception:
            pass
    try:
        for name in dir(pc):
            if name.startswith("_") or "reward" not in name.lower():
                continue
            try:
                m = getattr(pc, name, None)
            except Exception:
                continue
            if m is None or callable(m):
                continue
            cls = getattr(m, "Class", None)
            cname = str(getattr(cls, "Name", "") or "")
            if "Reward" in cname:
                return (m, name)
    except Exception:
        pass
    return (None, None)



def _pc_for_player_index(player_index: int) -> Optional[Any]:
    world, gs = _gbc_session_world_and_gamestate()
    if world is None or gs is None:
        return None
    pa = getattr(gs, "PlayerArray", None)
    if pa is None:
        return None
    try:
        if player_index < 0 or player_index >= len(pa):
            return None
        ps = pa[player_index]
    except Exception:
        return None
    if ps is None:
        return None
    return _gbc_find_pc_for_player_state(ps, world)


def _manager_for_player_index(player_index: int) -> Optional[Any]:
    pc = _pc_for_player_index(player_index)
    if pc is None:
        return None
    mgr, _ = _find_rewards_manager_on_pc(pc)
    return mgr


def _package_count(mgr: Any) -> int:
    try:
        pkgs = getattr(mgr, "packages", None)
        return len(pkgs) if pkgs is not None else 0
    except Exception:
        return 0


def _snapshot_player_package_counts(player_indices: List[int]) -> dict[int, int]:
    out: dict[int, int] = {}
    for idx in player_indices:
        mgr = _manager_for_player_index(idx)
        if mgr is not None:
            out[int(idx)] = _package_count(mgr)
    return out

def _find_rewards_def_struct() -> Optional[Any]:
    """Resolve the GbxRewardsDef ScriptStruct for FGbxDefPtr.ref (bl4_reward_generator path)."""
    for class_name in ("ScriptStruct", "Object"):
        for object_path in REWARDS_DEF_SCRIPT_PATHS:
            try:
                resolved = find_object(class_name, object_path)
            except Exception:
                resolved = None
            if isinstance(resolved, UObject):
                return resolved
    try:
        for candidate in find_all("ScriptStruct", False) or []:
            if getattr(candidate, "Name", None) == "GbxRewardsDef":
                return candidate
    except Exception:
        pass
    return None


def _assign_fgbx_def_ptr_fields(ptr: Any, name: str, ref: Any) -> bool:
    """
    pyunrealsdk builds differ: some expose FGbxDefPtr as .name/.ref, others as _experimental_* only.
    Try both so the same mod works across SDK drops (e.g. Apple vs Cr4nk DLL sets).
    """
    for name_attr, ref_attr in (("name", "ref"), ("_experimental_name", "_experimental_ref")):
        try:
            setattr(ptr, name_attr, name)
            setattr(ptr, ref_attr, ref)
            return True
        except Exception:
            continue
    return False


def _make_reward_def_ptr(reward_name: str) -> Optional[FGbxDefPtr]:
    """Build FGbxDefPtr from reward id string when UObject resolution fails (matches bl4_reward_generator)."""
    rewards_def_struct = _find_rewards_def_struct()
    if rewards_def_struct is None:
        return None
    tail = (reward_name or "").strip().split("/")[-1]
    if not tail:
        return None
    try:
        reward_def = FGbxDefPtr()
    except Exception:
        return None
    if not _assign_fgbx_def_ptr_fields(reward_def, tail, rewards_def_struct):
        _log_warning("FGbxDefPtr: could not set name/ref on this pyunrealsdk build.")
        return None
    return reward_def


def _resolve_def_for_give(pc: Any, lib: Any, def_path: str) -> Optional[Any]:
    path = _normalize_nexus_reward_def_arg(def_path)
    if not path:
        return None
    mgr_for_ref, _ = _find_rewards_manager_on_pc(pc)
    resolved = _try_make_gbx_reward_ref(lib, pc, mgr_for_ref, path)
    if resolved is None:
        resolved = _make_reward_def_ptr(path)
        if resolved is not None:
            _log_info(f"Resolved reward def via FGbxDefPtr(name={path!r}, GbxRewardsDef struct).")
    return resolved


def _give_reward_def(def_path: str, all_players: bool) -> bool:
    pc = get_pc()
    if pc is None:
        _log_error("No player controller.")
        return False
    lib = _get_gbx_rewards_blueprint_library()
    if lib is None:
        _log_error("GbxRewards_BlueprintFunctions not found.")
        return False

    def_u = _resolve_def_for_give(pc, lib, def_path)
    if def_u is None:
        _log_error(f"Could not resolve reward def '{def_path}'.")
        return False

    mgr, mgr_attr = _find_rewards_manager_on_pc(pc)
    world = getattr(pc, "World", None)

    if all_players:
        ptr_all: List[Any] = []
        if isinstance(def_u, FGbxDefPtr):
            ptr_all.append(def_u)
        else:
            try:
                ptr_all.append(FGbxDefPtr(def_u))
            except Exception as e:
                _log_warning(f"FGbxDefPtr(def) failed ({e}); will try raw def.")
            ptr_all.append(def_u)

        def _all_players_arg_variants(ptr: Any) -> List[Tuple[str, Tuple[Any, ...]]]:
            vs: List[Tuple[str, Tuple[Any, ...]]] = [
                ("ptr", (ptr,)),
                ("ptr_pc", (ptr, pc)),
                ("pc_ptr", (pc, ptr)),
            ]
            if mgr is not None:
                vs += [
                    ("ptr_mgr", (ptr, mgr)),
                    ("mgr_ptr", (mgr, ptr)),
                ]
            if world is not None:
                vs += [
                    ("ptr_world", (ptr, world)),
                    ("world_ptr", (world, ptr)),
                ]
            return vs

        give_all = getattr(lib, "GiveRewardAllPlayers", None)
        if not callable(give_all):
            _log_error("GiveRewardAllPlayers not callable.")
            return False
        for ptr in ptr_all:
            for order_name, args in _all_players_arg_variants(ptr):
                try:
                    give_all(*args)
                    _log_info(f"GiveRewardAllPlayers OK ({order_name}).")
                    return True
                except TypeError as e:
                    _log_warning(f"GiveRewardAllPlayers {order_name} TypeError: {e}")
                except Exception as e:
                    _log_warning(f"GiveRewardAllPlayers {order_name}: {e}")
                    return False
        _log_error("GiveRewardAllPlayers: all variants failed.")
        return False

    give_fn = getattr(lib, "GiveReward", None)
    if not callable(give_fn):
        _log_error("GiveReward not callable on library.")
        return False

    contexts: List[Any] = [pc]
    if mgr is not None:
        contexts.append(mgr)

    ptr_candidates: List[Any] = []
    if isinstance(def_u, FGbxDefPtr):
        ptr_candidates.append(def_u)
    else:
        try:
            ptr_candidates.append(FGbxDefPtr(def_u))
        except Exception as e:
            _log_warning(f"FGbxDefPtr(def) failed ({e}); will try raw def UObject.")
        ptr_candidates.append(def_u)

    for ptr in ptr_candidates:
        for ctx in contexts:
            ctx_label = "PC" if ctx is pc else ("PC.%s" % (mgr_attr or "manager"))
            for order_name, args in (
                ("RewardDef_then_OwnerContext", (ptr, ctx)),
                ("swapped_OwnerContext_first", (ctx, ptr)),
            ):
                try:
                    give_fn(*args)
                    _log_info(f"GiveReward OK: {order_name} {ctx_label}")
                    return True
                except TypeError as e:
                    _log_warning(f"GiveReward {order_name} {ctx_label} TypeError: {e}")
                except Exception as e:
                    _log_warning(f"GiveReward {order_name} {ctx_label}: {e}")
                    return False
    _log_error("GiveReward: all argument orderings failed.")
    return False


def _unique_gbx_rewards_managers() -> List[Any]:
    try:
        raw = list(unrealsdk.find_all("GbxRewardsManager", False) or [])
    except Exception as e:
        _log_warning(f"find_all GbxRewardsManager: {e}")
        return []
    seen: set[int] = set()
    out: List[Any] = []
    for obj in raw:
        if obj is None:
            continue
        oid = id(obj)
        if oid in seen:
            continue
        seen.add(oid)
        out.append(obj)
    return out




def _live_gbx_rewards_managers() -> List[Any]:
    """Only real in-world reward managers. Never return the class default object."""
    out: List[Any] = []
    seen: set[int] = set()
    for rm in _unique_gbx_rewards_managers():
        text = str(rm)
        if "Default__" in text:
            continue
        outer = getattr(rm, "Outer", None)
        if "OakPlayerController" not in str(outer):
            continue
        oid = id(rm)
        if oid in seen:
            continue
        seen.add(oid)
        out.append(rm)
    return out


def _open_all_live_reward_packages() -> int:
    """Probe helper: call Server_OpenAllPackages only on live controller-owned managers."""
    opened = 0
    for rm in _live_gbx_rewards_managers():
        try:
            fn = getattr(rm, "Server_OpenAllPackages", None)
            if callable(fn):
                fn()
                opened += 1
        except Exception as exc:
            _log_warning(f"Server_OpenAllPackages failed on live manager {rm}: {exc!r}")
    if opened:
        _log_info(f"Forced open rewards on {opened} live GbxRewardsManager instance(s).")
    else:
        _log_warning("No live GbxRewardsManager instances were available to force-open packages.")
    return opened


def _ensure_backpack_capacity_for_indices(player_indices: List[int], serial_count: int) -> int:
    """Make sure targeted players have enough backpack space before opening reward mail."""
    if not player_indices:
        return 0
    try:
        from .inventory_capacity import (
            clamp_container_size,
            get_player_state_by_party_index,
            set_backpack_size_for_player_state,
        )
    except Exception as exc:
        _log_warning(f"Could not import inventory capacity helpers before serial delivery: {exc!r}")
        return 0
    target_size = clamp_container_size(int(serial_count or 0) + _SERIAL_DELIVERY_BACKPACK_HEADROOM, 9999)
    changed = 0
    for idx in player_indices:
        try:
            ps = get_player_state_by_party_index(int(idx))
            if ps is None:
                continue
            cur = 0
            try:
                bp = getattr(getattr(ps, "BackpackContainer", None), "MaxSize", None)
                cur = max(int(getattr(bp, "Value", 0) or 0), int(getattr(bp, "BaseValue", 0) or 0))
            except Exception:
                cur = 0
            if cur < target_size:
                set_backpack_size_for_player_state(ps, target_size)
                changed += 1
        except Exception as exc:
            _log_warning(f"Backpack pre-size failed for player index {idx}: {exc!r}")
    if changed:
        _log_info(f"Prepared backpack capacity for {changed} target player(s), size >= {target_size}.")
    return changed


def _serial_delivery_char_count(serials: List[str]) -> int:
    return sum(len(str(s or "").strip()) for s in serials if str(s or "").strip())


def _serial_delivery_estimated_payload_chars(serials: List[str]) -> int:
    # The engine stores SerialNumbers as an array, not just one concatenated string.
    # Count a little overhead per entry so a package with many small serials does
    # not land close to the real client replication limit.
    total = 0
    for raw in serials:
        text = str(raw or "").strip()
        if text:
            total += len(text) + _SERIAL_DELIVERY_PER_SERIAL_OVERHEAD_CHARS
    return total


def _chunk_serials_for_delivery(
    serials: List[str],
    max_chars: int = _SERIAL_DELIVERY_SAFE_CHARS,
    max_serials: int | None = None,
) -> List[List[str]]:
    """Split serials into reward-package sized chunks.

    BL4 remote reward-package delivery becomes unreliable when a single
    SerialNumbers payload gets too large. Keep each package under a 20k
    estimated payload budget and below the per-package serial count cap.
    Individual serials are never split.
    """
    chunks: List[List[str]] = []
    current: List[str] = []
    current_chars = 0
    limit = max(1, int(max_chars or _SERIAL_DELIVERY_SAFE_CHARS))
    try:
        serial_limit = max(1, int(max_serials)) if max_serials is not None else 0
    except Exception:
        serial_limit = 0
    for raw in serials:
        text = str(raw or "").strip()
        if not text:
            continue
        n = len(text) + _SERIAL_DELIVERY_PER_SERIAL_OVERHEAD_CHARS
        if current and (current_chars + n > limit or (serial_limit and len(current) >= serial_limit)):
            chunks.append(current)
            current = []
            current_chars = 0
        # If one serial alone exceeds the budget, keep it alone.  We cannot
        # split an individual Base85 serial without corrupting it, but logging
        # makes the impossible case visible instead of silently dropping it.
        raw_n = len(text)
        if raw_n > _MAX_SERIAL_DELIVERY_CHARS:
            _log_warning(
                f"Single serial is {raw_n} raw chars, exceeding {_MAX_SERIAL_DELIVERY_CHARS}; "
                "delivering it alone because individual serials cannot be split."
            )
        current.append(text)
        current_chars += n
    if current:
        chunks.append(current)
    return chunks


def _serial_delivery_chunks(serials: List[str], mode: str | None = None) -> List[List[str]]:
    """Public-ish helper for the UI: preview exactly how delivery will split."""
    return _chunk_serials_for_delivery(
        serials,
        max_serials=_serial_delivery_max_serials_per_chunk(mode),
    )


def _serial_delivery_chunk_stats(serials: List[str], mode: str | None = None) -> List[dict[str, int]]:
    """Return per-package stats for display without exposing engine objects."""
    out: List[dict[str, int]] = []
    for i, chunk in enumerate(_serial_delivery_chunks(serials, mode), 1):
        out.append({
            "index": i,
            "serials": len(chunk),
            "raw_chars": _serial_delivery_char_count(chunk),
            "estimated_chars": _serial_delivery_estimated_payload_chars(chunk),
        })
    return out


def _serial_delivery_chunks_desc(chunks: List[List[str]]) -> str:
    if len(chunks) <= 1:
        return f"1 package, {_serial_delivery_char_count(chunks[0]) if chunks else 0} chars"
    sizes = [f"{_serial_delivery_char_count(c)} raw/{_serial_delivery_estimated_payload_chars(c)} est" for c in chunks]
    return f"{len(chunks)} packages, char payloads: " + ", ".join(sizes[:8]) + (", ..." if len(sizes) > 8 else "")

def _read_package_serials(package: Any) -> List[str]:
    out: List[str] = []
    contents = getattr(package, "contents", None)
    if contents is None:
        return out
    try:
        rows = list(contents)
    except Exception:
        return out
    for entry in rows:
        nums = getattr(entry, "SerialNumbers", None)
        if nums is None:
            continue
        try:
            for value in nums:
                text = str(value or "").strip()
                if text:
                    out.append(text)
        except Exception:
            continue
    return out


def _verify_package_serials(package: Any, serials: List[str]) -> Tuple[bool, int, int]:
    actual = _read_package_serials(package)
    expected = [str(s or "").strip() for s in serials if str(s or "").strip()]
    got = set(actual)
    want = set(expected)
    missing = want - got
    return (not missing and len(got) >= len(want), len(got), len(missing))


def _apply_serials_to_package(package: Any, serials: List[str]) -> int:
    if not serials:
        return 0
    contents = getattr(package, "contents", None)
    if contents is None:
        return 0
    try:
        n_contents = len(contents)
    except Exception:
        return 0
    if n_contents == 0:
        return 0

    if n_contents == 1:
        entry = contents[0]
        serial_numbers = getattr(entry, "SerialNumbers", None)
        if serial_numbers is None:
            return 0
        try:
            if hasattr(serial_numbers, "clear"):
                serial_numbers.clear()
            for s in serials:
                if hasattr(serial_numbers, "append"):
                    serial_numbers.append(s)
            ok, got, missing = _verify_package_serials(package, serials)
            if not ok:
                _log_warning(f"Serial verify after write failed: package has {got}, missing {missing}.")
                return 0
            return 1
        except Exception as e:
            _log_warning(f"SerialNumbers write (single content row): {e}")
            return 0

    applied = 0
    for content_entry in contents:
        ri = _safe_int(getattr(content_entry, "RewardsDataIndex", None))
        if ri is None or ri < 0 or ri >= len(serials):
            continue
        text = serials[ri]
        if not text:
            continue
        serial_numbers = getattr(content_entry, "SerialNumbers", None)
        if serial_numbers is None:
            continue
        try:
            if hasattr(serial_numbers, "clear"):
                serial_numbers.clear()
            if hasattr(serial_numbers, "append"):
                serial_numbers.append(text)
                applied += 1
        except Exception as e:
            _log_warning(f"SerialNumbers write (index {ri}): {e}")
    if applied > 0:
        ok, got, missing = _verify_package_serials(package, serials[:applied] if applied < len(serials) else serials)
        if not ok:
            _log_warning(f"Serial verify after indexed write incomplete: package has {got}, missing {missing}.")
    return applied


def _patch_manager_package_since(mgr: Any, serials: List[str], before_count: int, package_offset: int = 0) -> bool:
    pkgs = getattr(mgr, "packages", None)
    if pkgs is None:
        return False
    try:
        n_pkg = len(pkgs)
    except Exception:
        return False
    if n_pkg <= before_count:
        return False
    start = max(0, int(before_count))
    # Chunked deliveries may create several reward packages before the tick job
    # sees them.  Use package_offset to map chunk 0 -> first new package,
    # chunk 1 -> second new package, etc., instead of every job overwriting the
    # newest package.
    preferred = start + max(0, int(package_offset or 0))
    candidate_indices: List[int] = []
    if preferred < n_pkg:
        candidate_indices.append(preferred)
    # Fallback: newest first, but only among packages created after snapshot.
    for i in range(n_pkg - 1, start - 1, -1):
        if i not in candidate_indices:
            candidate_indices.append(i)
    for i in candidate_indices:
        try:
            package = pkgs[i]
        except Exception:
            continue
        if _apply_serials_to_package(package, serials) > 0:
            ok, got, missing = _verify_package_serials(package, serials)
            if ok:
                return True
            _log_warning(f"Patched package {i}, but verify has {got} serial(s), missing {missing}.")
    return False

def _patch_all_managers_last_package(serials: List[str]) -> Tuple[int, int]:
    """Returns (managers_with_patch, total_managers)."""
    managers = _unique_gbx_rewards_managers()
    if not managers:
        return (0, 0)
    patched = 0
    for mgr in managers:
        pkgs = getattr(mgr, "packages", None)
        if pkgs is None:
            continue
        try:
            n = len(pkgs)
        except Exception:
            continue
        if n <= 0:
            continue
        try:
            package = pkgs[n - 1]
        except Exception:
            continue
        if _apply_serials_to_package(package, serials) > 0:
            patched += 1
    return (patched, len(managers))


def _patch_single_player_index_last_package(serials: List[str], player_index: int) -> Tuple[int, int]:
    """Patch last package on the GbxRewardsManager for PlayerArray[player_index]. Returns (patched, 1)."""
    mgr = _manager_for_player_index(player_index)
    if mgr is None:
        _log_error(f"Give_Serial: index patch: no GbxRewardsManager for player index {player_index}.")
        return (0, 0)
    pkgs = getattr(mgr, "packages", None)
    if pkgs is None:
        return (0, 1)
    try:
        n_pkg = len(pkgs)
    except Exception:
        return (0, 1)
    if n_pkg <= 0:
        return (0, 1)
    try:
        package = pkgs[n_pkg - 1]
    except Exception:
        return (0, 1)
    if _apply_serials_to_package(package, serials) > 0:
        return (1, 1)
    return (0, 1)


def _patch_player_indices_since_counts(serials: List[str], before_counts: dict[int, int], package_offset: int = 0) -> Tuple[int, int]:
    if not before_counts:
        return (0, 0)
    patched = 0
    for idx, before in list(before_counts.items()):
        mgr = _manager_for_player_index(int(idx))
        if mgr is None:
            continue
        if _patch_manager_package_since(mgr, serials, int(before), package_offset):
            patched += 1
    return (patched, len(before_counts))

def _patch_player_indices_last_package(serials: List[str], player_indices: List[int]) -> Tuple[int, int]:
    """Patch last reward package for specific PlayerArray indices. Returns (patched_count, target_count)."""
    seen: set[int] = set()
    targets: List[int] = []
    for idx in player_indices:
        try:
            i = int(idx)
        except Exception:
            continue
        if i in seen:
            continue
        seen.add(i)
        targets.append(i)
    if not targets:
        return (0, 0)
    patched = 0
    total = 0
    for idx in targets:
        p, t = _patch_single_player_index_last_package(serials, idx)
        total += max(1, t)
        if p > 0:
            patched += 1
    return (patched, len(targets))


_pending_serial_patch_jobs: List[dict[str, Any]] = []


def _queue_serial_patch_job(serials: List[str], before_counts: dict[int, int], scope_label: str, package_offset: int = 0) -> None:
    if not before_counts:
        _log_warning(f"Serial patch queue: no target package counts captured ({scope_label}).")
        return
    _pending_serial_patch_jobs.append({
        "serials": list(serials),
        "before_counts": dict(before_counts),
        "scope_label": scope_label,
        "package_offset": int(package_offset or 0),
        "attempts": 0,
        "created": time.time(),
    })
    _log_info(f"Queued serial verification patch for {len(before_counts)} target(s), {len(serials)} serial(s), {_serial_delivery_char_count(list(serials))} raw chars / {_serial_delivery_estimated_payload_chars(list(serials))} est chars ({scope_label}, package offset {int(package_offset or 0)}).")


def _process_pending_serial_patch_jobs() -> None:
    if not _pending_serial_patch_jobs:
        return
    remaining: List[dict[str, Any]] = []
    for job in list(_pending_serial_patch_jobs):
        serials = list(job.get("serials") or [])
        before_counts = dict(job.get("before_counts") or {})
        scope_label = str(job.get("scope_label") or "targeted players")
        attempts = int(job.get("attempts") or 0) + 1
        package_offset = int(job.get("package_offset") or 0)
        patched, total = _patch_player_indices_since_counts(serials, before_counts, package_offset)
        if patched >= total and total > 0:
            _log_info(f"Verified serial delivery on {patched}/{total} target(s) ({scope_label}, tick attempt {attempts}).")
            continue
        if attempts >= _TICK_PATCH_MAX_ATTEMPTS:
            _log_warning(f"Serial delivery verify timed out on {patched}/{total} target(s) ({scope_label}). Try a smaller batch or reopen rewards UI.")
            continue
        if attempts % _TICK_PATCH_LOG_EVERY == 0:
            _log_info(f"Waiting for reward packages: patched {patched}/{total} target(s) ({scope_label}, tick attempt {attempts}).")
        job["attempts"] = attempts
        remaining.append(job)
    _pending_serial_patch_jobs[:] = remaining


def _tick_cb(*_args: Any, **_kwargs: Any) -> None:
    # Idle path must be free: this hook fires from the game HUD tick.
    if not _pending_serial_patch_jobs and not _pending_serial_delivery_sequences:
        return
    try:
        _process_pending_serial_patch_jobs()
        _process_pending_serial_delivery_sequences()
    except Exception as exc:
        _log_warning(f"Serial delivery tick failed: {exc!r}")


try:
    hook(
        "/Script/GbxUIUMG.GbxUIUMGTickWidget:BP_TickWidget",
        immediately_enable=True,
        hook_identifier="matts_sdk_boosting_tools_serial_delivery_tick_v1",
    )(_tick_cb)
except Exception as exc:
    _log_warning(f"Could not install serial delivery tick hook: {exc!r}")



_pending_serial_delivery_sequences: List[dict[str, Any]] = []
_serial_delivery_status_message: str = "Idle"
_serial_delivery_status_until: float = 0.0


def _set_serial_delivery_status(message: str, *, hold_sec: float = 30.0, log: bool = False) -> None:
    global _serial_delivery_status_message, _serial_delivery_status_until
    text = str(message or "").strip() or "Idle"
    _serial_delivery_status_message = text
    try:
        _serial_delivery_status_until = time.time() + max(1.0, float(hold_sec))
    except Exception:
        _serial_delivery_status_until = time.time() + 30.0
    if log:
        _log_info(text)


def serial_delivery_status() -> str:
    """Lightweight UI/HUD poller for the active chunked delivery state."""
    prog = serial_delivery_progress()
    if prog.get("active"):
        return str(prog.get("message") or "")
    if _serial_delivery_status_message and time.time() <= float(_serial_delivery_status_until or 0.0):
        return _serial_delivery_status_message
    return ""


def serial_delivery_progress() -> dict[str, Any]:
    """Return active chunked-delivery progress for menu/HUD rendering.

    fraction is 0..1 across the whole multi-package delivery.  This is intentionally
    read-only so UI polling never mutates the delivery state machine.
    """
    if not _pending_serial_delivery_sequences:
        return {"active": False, "fraction": 0.0, "message": "", "label": "", "index": 0, "total": 0}
    seq = _pending_serial_delivery_sequences[0]
    chunks = list(seq.get("chunks") or [])
    total = len(chunks)
    idx = max(0, int(seq.get("index") or 0))
    stage = str(seq.get("stage") or "deliver")
    scope = str(seq.get("scope_label") or "targeted players")
    if total <= 0:
        return {"active": False, "fraction": 0.0, "message": "", "label": "", "index": 0, "total": 0}
    idx = min(idx, total - 1)
    now = time.time()

    stage_start = {
        "deliver": 0.00,
        "patch": 0.08,
        "pre_open_wait": 0.18,
        "open": 0.52,
        "post_open_wait": 0.64,
        "wait": 0.64,
    }.get(stage, 0.0)
    stage_end = {
        "deliver": 0.08,
        "patch": 0.18,
        "pre_open_wait": 0.52,
        "open": 0.64,
        "post_open_wait": 1.00,
        "wait": 1.00,
    }.get(stage, stage_start)

    wait_remaining = 0.0
    if stage in ("pre_open_wait", "post_open_wait", "wait"):
        wait_until = float(seq.get("wait_until") or 0.0)
        wait_remaining = max(0.0, wait_until - now)
        duration = _SERIAL_DELIVERY_PRE_OPEN_DELAY_SEC
        if stage != "pre_open_wait":
            duration = seq.get("post_open_delay")
            if duration is None:
                duration = _serial_delivery_post_open_delay(seq.get("mode"))
        try:
            duration = max(0.001, float(duration))
        except Exception:
            duration = 1.0
        elapsed_frac = max(0.0, min(1.0, 1.0 - (wait_remaining / duration)))
        chunk_frac = stage_start + ((stage_end - stage_start) * elapsed_frac)
    else:
        chunk_frac = stage_start

    whole = max(0.0, min(1.0, (idx + max(0.0, min(1.0, chunk_frac))) / float(total)))
    pct = int(round(whole * 100.0))
    friendly = {
        "deliver": "sending package",
        "patch": "patching serials",
        "pre_open_wait": f"opening in {wait_remaining:.1f}s",
        "open": "opening rewards",
        "post_open_wait": f"next package in {wait_remaining:.1f}s",
        "wait": f"waiting {wait_remaining:.1f}s",
    }.get(stage, stage)
    message = f"Serial delivery {idx + 1}/{total}: {friendly} ({pct}%)"
    label = f"{idx + 1}/{total} · {pct}%"
    return {
        "active": True,
        "fraction": whole,
        "percent": pct,
        "message": message,
        "label": label,
        "stage": stage,
        "index": idx + 1,
        "total": total,
        "scope": scope,
        "wait_remaining": wait_remaining,
    }


def _next_loyalty_reward_name() -> Tuple[str, int, int]:
    global _loyalty_rotation_index
    n = len(LOYALTY_REWARD_DEF_NAMES)
    if n:
        idx = _loyalty_rotation_index % n
        name = LOYALTY_REWARD_DEF_NAMES[idx]
        _loyalty_rotation_index = (_loyalty_rotation_index + 1) % n
        return name, idx + 1, n
    return DEFAULT_REWARD_DEF_NAME, 1, 1


def _queue_serial_delivery_sequence(serials: List[str], player_indices: List[int], *, scope_label: str, mode: str | None = None) -> None:
    mode_key = _serial_delivery_mode_key(mode)
    max_serials = _serial_delivery_max_serials_per_chunk(mode_key)
    post_open_delay = _clamp_serial_delivery_delay(_serial_delivery_post_open_delay(mode_key))
    chunks = _serial_delivery_chunks(serials, mode_key)
    if not chunks:
        _log_error("No serial strings after delivery chunking.")
        return
    targets: List[int] = []
    seen: set[int] = set()
    for idx in player_indices:
        try:
            i = int(idx)
        except Exception:
            continue
        if i in seen:
            continue
        seen.add(i)
        targets.append(i)
    if not targets:
        _log_error("Give_Serial: no target player indices to patch.")
        return

    _ensure_backpack_capacity_for_indices(targets, len(serials))
    _gbc_run_session_timer_from_give_serial()
    if len(chunks) > 1:
        _log_info(
            f"Auto-sequencing {len(serials)} serial(s) for {scope_label}: "
            f"{_serial_delivery_chunks_desc(chunks)}. Max {max_serials} serial(s) per package; "
            f"{post_open_delay:.2f}s post-open delay. Each package will be opened before the next delivery."
        )
    else:
        _log_info(f"Serial delivery queued for {scope_label}: 1 package, {len(serials)} serial(s).")
    _set_serial_delivery_status(f"Serial delivery queued: {len(chunks)} part(s), {len(serials)} serial(s) to {scope_label}", log=True)
    _pending_serial_delivery_sequences.append({
        "serials": list(serials),
        "chunks": chunks,
        "targets": targets,
        "scope_label": scope_label,
        "index": 0,
        "stage": "deliver",
        "attempts": 0,
        "before_counts": {},
        "wait_until": 0.0,
        "mode": mode_key,
        "post_open_delay": post_open_delay,
    })
    _process_pending_serial_delivery_sequences()


def _process_pending_serial_delivery_sequences() -> None:
    if not _pending_serial_delivery_sequences:
        return
    remaining: List[dict[str, Any]] = []
    now = time.time()
    for seq in list(_pending_serial_delivery_sequences):
        try:
            chunks = list(seq.get("chunks") or [])
            targets = list(seq.get("targets") or [])
            scope_label = str(seq.get("scope_label") or "targeted players")
            idx = int(seq.get("index") or 0)
            stage = str(seq.get("stage") or "deliver")
            if idx >= len(chunks):
                msg = f"Serial delivery submitted and opened reward packages for {scope_label} ({len(chunks)} package part(s))."
                _set_serial_delivery_status(msg, hold_sec=20.0, log=True)
                continue

            if stage in ("pre_open_wait", "post_open_wait", "wait"):
                if now < float(seq.get("wait_until") or 0.0):
                    remaining.append(seq)
                    continue
                if stage == "pre_open_wait":
                    seq["stage"] = "open"
                    stage = "open"
                else:
                    # post-open delay finished; advance to next package.
                    seq["index"] = idx + 1
                    seq["stage"] = "deliver"
                    seq["attempts"] = 0
                    if idx + 1 >= len(chunks):
                        msg = f"Serial delivery submitted and opened reward packages for {scope_label} ({len(chunks)} package part(s))."
                        _set_serial_delivery_status(msg, hold_sec=20.0, log=True)
                        continue
                    idx = idx + 1
                    stage = "deliver"

            if stage == "deliver":
                chunk = chunks[idx]
                reward_name, slot, n = _next_loyalty_reward_name()
                msg = (
                    f"Delivering serial package {idx + 1}/{len(chunks)} to {scope_label}: "
                    f"{len(chunk)} serial(s), {_serial_delivery_char_count(chunk)} raw chars / "
                    f"{_serial_delivery_estimated_payload_chars(chunk)} est chars, reward {reward_name} ({slot}/{n})."
                )
                _set_serial_delivery_status(f"Serial delivery {idx + 1}/{len(chunks)}: delivering package to {scope_label}", hold_sec=30.0, log=True)
                _log_info(msg)
                before_counts = _snapshot_player_package_counts(targets)
                if not before_counts:
                    _set_serial_delivery_status(f"Serial delivery stopped: no reward managers found for {scope_label}", hold_sec=20.0, log=True)
                    continue
                if not _give_reward_def(reward_name, True):
                    _set_serial_delivery_status(f"Serial delivery stopped: GiveRewardAllPlayers failed on {idx + 1}/{len(chunks)}", hold_sec=20.0, log=True)
                    continue
                seq["before_counts"] = before_counts
                seq["stage"] = "patch"
                seq["attempts"] = 0
                remaining.append(seq)
                continue

            if stage == "patch":
                chunk = chunks[idx]
                attempts = int(seq.get("attempts") or 0) + 1
                before_counts = dict(seq.get("before_counts") or {})
                patched, total = _patch_player_indices_since_counts(chunk, before_counts, 0)
                if patched >= total and total > 0:
                    _set_serial_delivery_status(
                        f"Serial delivery {idx + 1}/{len(chunks)}: patched {patched}/{total}; waiting {_SERIAL_DELIVERY_PRE_OPEN_DELAY_SEC:.2f} sec before opening",
                        hold_sec=30.0,
                        log=True,
                    )
                    seq["stage"] = "pre_open_wait"
                    seq["wait_until"] = time.time() + _SERIAL_DELIVERY_PRE_OPEN_DELAY_SEC
                    seq["attempts"] = 0
                    remaining.append(seq)
                    continue
                if attempts >= _SERIAL_DELIVERY_PATCH_MAX_ATTEMPTS:
                    _set_serial_delivery_status(
                        f"Serial delivery {idx + 1}/{len(chunks)}: patch timeout {patched}/{total}; waiting {_SERIAL_DELIVERY_PRE_OPEN_DELAY_SEC:.2f} sec before forced open",
                        hold_sec=30.0,
                        log=True,
                    )
                    seq["stage"] = "pre_open_wait"
                    seq["wait_until"] = time.time() + _SERIAL_DELIVERY_PRE_OPEN_DELAY_SEC
                    seq["attempts"] = 0
                    remaining.append(seq)
                    continue
                if attempts % _SERIAL_DELIVERY_PATCH_LOG_EVERY == 0:
                    _set_serial_delivery_status(
                        f"Serial delivery {idx + 1}/{len(chunks)}: patching {patched}/{total} target(s)",
                        hold_sec=30.0,
                        log=True,
                    )
                seq["attempts"] = attempts
                remaining.append(seq)
                continue

            if stage == "open":
                _set_serial_delivery_status(f"Serial delivery {idx + 1}/{len(chunks)}: opening reward packages", hold_sec=30.0, log=True)
                _open_all_live_reward_packages()
                post_open_delay = seq.get("post_open_delay")
                if post_open_delay is None:
                    post_open_delay = _serial_delivery_post_open_delay(seq.get("mode"))
                post_open_delay = _clamp_serial_delivery_delay(post_open_delay)
                seq["stage"] = "post_open_wait"
                seq["wait_until"] = time.time() + post_open_delay
                seq["attempts"] = 0
                remaining.append(seq)
                continue

            _set_serial_delivery_status(f"Serial delivery dropped: unknown stage {stage!r}", hold_sec=20.0, log=True)
        except Exception as exc:
            _set_serial_delivery_status(f"Serial delivery sequence tick failed: {exc!r}", hold_sec=20.0, log=True)
    _pending_serial_delivery_sequences[:] = remaining


def _do_give_serial_to_player_indices(
    serials: List[str],
    player_indices: List[int],
    *,
    scope_label: str = "selected players",
    mode: str | None = None,
) -> None:
    """
    Hybrid party-safe serial delivery.

    This intentionally uses the older working delivery model for each package:
    snapshot -> GiveRewardAllPlayers -> patch the target players' newest package.

    The newer reliability pieces are kept:
    - large serial sets are split into safe chunks;
    - each chunk is force-opened after the serials are patched;
    - a short post-open gap is kept before the next chunk so remote clients can
      actually consume the previous reward mail before another package arrives.

    This avoids the newer delayed-open state machine, which could leave chunks
    waiting in the queue and make serial mail unreliable for remote players.
    """
    if not serials:
        _log_error("No serial strings after parsing (comma-separated non-empty segments).")
        return

    targets: List[int] = []
    seen: set[int] = set()
    for idx in player_indices:
        try:
            i = int(idx)
        except Exception:
            continue
        if i in seen:
            continue
        seen.add(i)
        targets.append(i)
    if not targets:
        _log_error("Give_Serial: no target player indices to patch.")
        return

    mode_key = _serial_delivery_mode_key(mode)
    max_serials = _serial_delivery_max_serials_per_chunk(mode_key)
    gap = _clamp_serial_delivery_delay(_serial_delivery_post_open_delay(mode_key))
    chunks = _chunk_serials_for_delivery(serials, max_serials=max_serials)
    if not chunks:
        _log_error("No serial strings after delivery chunking.")
        return

    # Disable any unfinished delayed sequence from the newer state-machine path;
    # this hybrid path is synchronous and should be the single source of delivery.
    try:
        _pending_serial_delivery_sequences.clear()
    except Exception:
        pass

    _ensure_backpack_capacity_for_indices(targets, len(serials))
    _gbc_run_session_timer_from_give_serial()
    mode_label = "selected" if mode_key == "selected" else ("all non-host" if mode_key == "nonhost" else "all-player")
    _set_serial_delivery_status(
        f"Submitting {len(serials)} serial(s) in {len(chunks)} chunk(s), max {max_serials} serial(s) per chunk, delay {gap:.2f}s ({scope_label})",
        hold_sec=30.0,
        log=True,
    )
    _log_info(
        f"Throttled {mode_label} serial delivery starting: {len(serials)} serial(s), "
        f"{len(chunks)} chunk(s), max {max_serials}/chunk, delay {gap:.2f}s ({scope_label})."
    )
    if len(chunks) > 1:
        _log_info(
            f"Throttled chunk plan for {scope_label}: {len(serials)} serial(s), "
            f"{_serial_delivery_chunks_desc(chunks)}. Max {max_serials} serial(s) per chunk; "
            f"{gap:.2f}s post-open delay. Each chunk uses immediate delivery + forced open."
        )

    for chunk_index, chunk in enumerate(chunks, 1):
        reward_name, slot, n = _next_loyalty_reward_name()
        _set_serial_delivery_status(
            f"Serial delivery {chunk_index}/{len(chunks)}: sending {len(chunk)} serial(s) to {scope_label}",
            hold_sec=30.0,
            log=True,
        )
        _log_info(
            f"Throttled serial package {chunk_index}/{len(chunks)} for {scope_label}: "
            f"{len(chunk)} serial(s), {_serial_delivery_char_count(chunk)} raw chars / "
            f"{_serial_delivery_estimated_payload_chars(chunk)} est chars, reward {reward_name} ({slot}/{n})."
        )

        # Critical old behavior: remote party members reliably receive the package
        # through GiveRewardAllPlayers; then only target package SerialNumbers are patched.
        before_counts = _snapshot_player_package_counts(targets)
        if not before_counts:
            _set_serial_delivery_status(
                f"Serial delivery stopped: no reward managers found for {scope_label}",
                hold_sec=20.0,
                log=True,
            )
            return
        if not _give_reward_def(reward_name, True):
            _set_serial_delivery_status(
                f"Serial delivery stopped: GiveRewardAllPlayers failed on part {chunk_index}/{len(chunks)}",
                hold_sec=20.0,
                log=True,
            )
            return

        patched = 0
        total = len(before_counts)
        max_attempts = max(int(_PATCH_RETRY_ATTEMPTS or 0), 12)
        for attempt in range(max_attempts):
            patched, total = _patch_player_indices_since_counts(chunk, before_counts, 0)
            if patched >= total and total > 0:
                _log_info(
                    f"Serial delivery {chunk_index}/{len(chunks)} patched {patched}/{total} target(s) "
                    f"({scope_label}, attempt {attempt + 1})."
                )
                break
            if attempt + 1 < max_attempts:
                time.sleep(_PATCH_RETRY_DELAY_SEC)

        if patched <= 0:
            _log_warning(
                f"Serial delivery {chunk_index}/{len(chunks)}: no target packages patched after {max_attempts} attempts; "
                "forcing open anyway to avoid stuck reward mail."
            )
        elif patched < total:
            _log_warning(
                f"Serial delivery {chunk_index}/{len(chunks)}: patched {patched}/{total} target(s); "
                "forcing open for available packages."
            )

        _set_serial_delivery_status(
            f"Serial delivery {chunk_index}/{len(chunks)}: force-opening reward packages",
            hold_sec=30.0,
            log=True,
        )
        _open_all_live_reward_packages()

        if chunk_index < len(chunks):
            if gap > 0:
                _set_serial_delivery_status(
                    f"Serial delivery {chunk_index}/{len(chunks)} opened; next part in {gap:.2f}s",
                    hold_sec=30.0,
                    log=True,
                )
                time.sleep(gap)

    _set_serial_delivery_status(
        f"Throttled serial delivery queue complete for {scope_label} ({len(chunks)} chunk(s), {len(serials)} serial(s)).",
        hold_sec=20.0,
        log=True,
    )

def _all_party_player_indices_for_serial_delivery() -> List[int]:
    try:
        _world, gs = _gbc_session_world_and_gamestate()
        pa = getattr(gs, "PlayerArray", None) if gs is not None else None
        if pa is None:
            return []
        return [i for i in range(len(pa))]
    except Exception:
        return []


def _do_give_serial(
    serials: List[str],
    all_players: bool,
    *,
    serial_only_player_index: Optional[int] = None,
) -> None:
    """Give serial rewards, splitting large SerialNumbers payloads over packages."""
    if not serials:
        _log_error("No serial strings after parsing/chunking.")
        return
    if all_players:
        if serial_only_player_index is not None:
            _do_give_serial_to_player_indices(
                serials,
                [int(serial_only_player_index)],
                scope_label=f"player index {int(serial_only_player_index)} via all-player reward",
                mode="selected",
            )
            return
        indices = _all_party_player_indices_for_serial_delivery()
        if indices:
            _do_give_serial_to_player_indices(serials, indices, scope_label="all party players", mode="all")
            return
    # Local fallback keeps old behavior, but still opens live packages after each chunk.
    chunks = _chunk_serials_for_delivery(serials)
    if not chunks:
        _log_error("No serial strings after parsing/chunking.")
        return
    if len(chunks) > 1:
        _log_info(
            f"Splitting {len(serials)} serial(s) for local player: {_serial_delivery_chunks_desc(chunks)}."
        )
    for i, chunk in enumerate(chunks):
        if len(chunks) > 1:
            _log_info(f"Starting local serial delivery chunk {i + 1}/{len(chunks)} ({len(chunk)} serials).")
        _do_give_serial_chunk(chunk, all_players, serial_only_player_index=serial_only_player_index)
        _open_all_live_reward_packages()


def _do_give_serial_chunk(
    serials: List[str],
    all_players: bool,
    *,
    serial_only_player_index: Optional[int] = None,
) -> None:
    global _loyalty_rotation_index
    if not serials:
        _log_error("No serial strings after parsing (comma-separated non-empty segments).")
        return

    _gbc_run_session_timer_from_give_serial()

    n = len(LOYALTY_REWARD_DEF_NAMES)
    if n:
        reward_name = LOYALTY_REWARD_DEF_NAMES[_loyalty_rotation_index % n]
        slot = _loyalty_rotation_index % n + 1
        _log_info(f"Loyalty rotation: using {reward_name} ({slot}/{n}).")
    else:
        reward_name = DEFAULT_REWARD_DEF_NAME
        _log_info(f"Loyalty rotation list empty; using default {reward_name}.")

    if not _give_reward_def(reward_name, all_players):
        return

    if n:
        _loyalty_rotation_index = (_loyalty_rotation_index + 1) % n

    if all_players and serial_only_player_index is not None:
        scope = f"all players (serials on gbc_players index {serial_only_player_index} only)"
        patch_fn = lambda: _patch_single_player_index_last_package(serials, serial_only_player_index)
    else:
        scope = "all players" if all_players else "local player"

        def patch_fn() -> Tuple[int, int]:
            return _patch_all_managers_last_package(serials)

    for attempt in range(_PATCH_RETRY_ATTEMPTS):
        patched, total = patch_fn()
        if patched > 0:
            if all_players and serial_only_player_index is not None:
                _log_info(
                    f"Serials applied to last package for player index {serial_only_player_index} "
                    f"({scope}, attempt {attempt + 1})."
                )
            else:
                _log_info(
                    f"Serials applied to last package on {patched} / {total} GbxRewardsManager instance(s) "
                    f"({scope}, attempt {attempt + 1})."
                )
            return
        if attempt + 1 < _PATCH_RETRY_ATTEMPTS:
            time.sleep(_PATCH_RETRY_DELAY_SEC)

    _log_warning(
        "Serial override pending: no SerialNumbers were written on the target package(s). "
        "Run Give_Serial again after the reward appears in the mail UI."
    )


@command(
    "Give_Serial",
    description=(
        "Grant the next generic loyalty reward package (rotates Daedalus→Jakobs→…→Vladof; Ripper uses Borg id), "
        "then set serial(s) on the newest reward package (each GbxRewardsManager, or one player with index/name). "
        "Base85 @U… tokens may be comma-separated or separate args. Deserialized human lines (digits, 0,1,60|…) "
        "must be one double-quoted token each; they are converted to Base85 via HTTP (GENIE_SERIALIZE_API_URL). "
        "Usage: Give_Serial serial … [all] | Give_Serial … index N all | Give_Serial … name <substring> all "
        "(unique match on gbc_players display name)"
    ),
)
def _cmd_give_serial(args: argparse.Namespace) -> None:
    parts: List[str] = list(getattr(args, "parts", None) or [])
    all_players = False
    if parts and parts[-1].lower() == "all":
        all_players = True
        parts = parts[:-1]
    serial_only_index: Optional[int] = None
    name_i: Optional[int] = None
    for i, tok in enumerate(parts):
        if tok.lower() == "name":
            name_i = i
            break
    if name_i is not None:
        name_sub = " ".join(parts[name_i + 1:]).strip()
        parts = parts[:name_i]
        if not name_sub:
            _log_error("Give_Serial: name keyword requires a substring after it (example: … name Dunkie all).")
            return
        _, gs = _gbc_session_world_and_gamestate()
        if gs is None:
            _log_error("Give_Serial: no GameState (cannot resolve name).")
            return
        idx, err = _gbc_resolve_player_index_for_name_substring(gs, name_sub)
        if err:
            _log_error(f"Give_Serial: {err}")
            return
        serial_only_index = idx
    elif len(parts) >= 2 and parts[-2].lower() == "index":
        idx_val = _safe_int(parts[-1])
        if idx_val is None:
            _log_error("Give_Serial: expected integer after index (example: … index 2 all).")
            return
        serial_only_index = idx_val
        parts = parts[:-2]
    if serial_only_index is not None and not all_players:
        _log_error(
            "Give_Serial: index or name targeting requires trailing all "
            "(GiveRewardAllPlayers + serials on one gbc_players player only)."
        )
        return
    if not parts:
        _log_error(
            "Usage: Give_Serial <serial>[,serial…] [all]  —  optional … index N or … name <substring> before all. "
            "Deserialized human serials: wrap each line in double quotes (shlex); requires network serialize."
        )
        return
    expanded: List[str] = []
    for p in parts:
        expanded.extend(_expand_serial_token(p))
    if not expanded:
        _log_error("No serial strings after parsing (use commas between Base85 serials or quoted human lines).")
        return
    serials = _resolve_give_serial_strings(expanded)
    if serials is None:
        return
    if not serials:
        _log_error("No serial strings after resolving (empty list).")
        return
    _do_give_serial(serials, all_players, serial_only_player_index=serial_only_index)


_cmd_give_serial.add_argument(
    "parts",
    nargs="+",
    help="Base85 serial(s) and/or quoted deserialized line(s); optional … index N all or … name substring all",
)
