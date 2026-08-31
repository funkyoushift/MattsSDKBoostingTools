"""Party Reveal Map — teleport remotes so guest FoD tiles commit.

Host-only. Overlay hide and the host +0xB0 grid do not paint guests.
Uses the shared camera_tick pump. No line traces on that tick.
After a death, wait until the guest is a playable pawn at the host.
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path
from typing import Any

from mods_base import ENGINE, get_pc
from unrealsdk import find_all, logging, make_struct

_LOG = "[Matts SDK Boosting Tools | PartyReveal]"
_DWELL_S = 0.8
_WAIT_S = 12.0
_SIT_S = 3.0
_HOME_R = 25000.0
_HOPS_NAME = "fod_party_hops.json"

_PTS: tuple[tuple[int, int, int], ...] = ()
_state: dict[str, Any] = {"done": True, "idx": 0}
_registered = False


def _log(msg: str) -> None:
    logging.info(f"{_LOG} {msg}")


def _load_pts() -> tuple[tuple[int, int, int], ...]:
    global _PTS
    if _PTS:
        return _PTS
    text = ""
    try:
        from importlib import resources

        text = resources.files(__package__).joinpath(_HOPS_NAME).read_text(encoding="utf-8")
    except Exception:
        path = Path(__file__).with_name(_HOPS_NAME)
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            text = ""
    if not text:
        return ()
    try:
        raw = json.loads(text)
    except Exception:
        return ()
    hops: list[tuple[int, int, int]] = []
    for row in raw:
        try:
            hops.append((int(row[0]), int(row[1]), int(row[2])))
        except Exception:
            continue
    _PTS = tuple(hops)
    return _PTS


def last_status() -> dict[str, Any]:
    pts = _load_pts()
    running = not bool(_state.get("done", True))
    idx = int(_state.get("idx") or 0)
    guests = len(list(_state.get("targets") or []))
    if running:
        msg = f"Party Reveal hop {idx + 1}/{len(pts)} guests={guests}"
    elif idx > 0 and idx >= len(pts):
        msg = f"Party Reveal done hops={len(pts)} guests={guests}"
    else:
        msg = "Party Reveal idle."
    return {
        "running": running,
        "hop": idx + 1 if running and pts else idx,
        "total": len(pts),
        "guests": guests,
        "message": msg,
    }


def _s(obj: Any) -> str:
    try:
        return str(obj)
    except Exception:
        return type(obj).__name__


def _cls(obj: Any) -> str:
    try:
        return type(obj).__name__
    except Exception:
        return "?"


def _find_cls(name: str) -> list[Any]:
    try:
        objs = list(find_all(name, False) or [])
    except Exception:
        objs = []
    return [o for o in objs if o is not None and "Default__" not in _s(o)]


def _ps_name(ps: Any) -> str:
    for attr in ("PlayerNamePrivate", "PlayerName"):
        try:
            val = getattr(ps, attr, None)
        except Exception:
            val = None
        if val:
            return str(val)
    return "?"


def _loc(pawn: Any) -> Any:
    try:
        return pawn.K2_GetActorLocation()
    except Exception:
        return None


def _xyz(loc: Any) -> tuple[float, float, float]:
    if loc is None:
        return (0.0, 0.0, 0.0)
    try:
        return (float(loc.X), float(loc.Y), float(loc.Z))
    except Exception:
        return (0.0, 0.0, 0.0)


def _is_spectator(pawn: Any) -> bool:
    if pawn is None:
        return True
    if "Spectator" in _cls(pawn):
        return True
    try:
        if bool(getattr(pawn, "bIsSpectator", False)):
            return True
    except Exception:
        pass
    return False


def _pawn_of(pc: Any, ps: Any) -> Any | None:
    found: list[Any] = []
    for root, names in (
        (pc, ("OakCharacter", "AcknowledgedPawn", "Pawn")),
        (ps, ("PawnPrivate", "Pawn", "OwnerPawn")),
    ):
        if root is None:
            continue
        for name in names:
            try:
                pawn = getattr(root, name, None)
            except Exception:
                pawn = None
            if pawn is None or _is_spectator(pawn):
                continue
            found.append(pawn)
    for pawn in found:
        if "Oak" in _cls(pawn):
            return pawn
    return found[0] if found else None


def _resolve_pc(ps: Any, host_ps: Any) -> Any | None:
    owner = getattr(ps, "Owner", None)
    if owner is not None and "PlayerController" in type(owner).__name__:
        return owner
    for obj in _find_cls("OakPlayerController"):
        if getattr(obj, "PlayerState", None) is ps:
            return obj
    return owner


def _alive(pawn: Any) -> bool:
    if pawn is None or _is_spectator(pawn):
        return False
    for name in ("IsDead", "IsPendingKill", "IsPendingKillOrUnreachable"):
        fn = getattr(pawn, name, None)
        if callable(fn):
            try:
                if bool(fn()):
                    return False
            except Exception:
                pass
    for name in ("bDead", "bIsDead"):
        try:
            if bool(getattr(pawn, name, False)):
                return False
        except Exception:
            pass
    for name in ("GetHealth", "GetCurrentHealth"):
        fn = getattr(pawn, name, None)
        if callable(fn):
            try:
                if float(fn()) <= 0.0:
                    return False
            except Exception:
                pass
    return True


def _teleport(pawn: Any, x: float, y: float, z: float, require_alive: bool = True) -> bool:
    if require_alive and not _alive(pawn):
        return False
    dest = make_struct("Vector", X=float(x), Y=float(y), Z=float(z) + 80.0)
    rot = None
    try:
        rot = pawn.K2_GetActorRotation()
    except Exception:
        rot = None
    try:
        pawn.SetActorEnableCollision(False)
    except Exception:
        pass
    ok = False
    try:
        ok = bool(pawn.K2_TeleportTo(dest, rot))
    except Exception:
        try:
            ok = bool(pawn.K2_SetActorLocation(dest, False, None, False))
        except Exception:
            ok = False
    try:
        pawn.SetActorEnableCollision(True)
    except Exception:
        pass
    return ok


def _refresh_pawns() -> list[Any]:
    host_ps = _state.get("host_ps")
    fresh: list[Any] = []
    for ps in list(_state.get("targets") or []):
        pawn = _pawn_of(_resolve_pc(ps, host_ps), ps)
        if pawn is not None:
            fresh.append(pawn)
    _state["pawns"] = fresh
    return fresh


def _near_host(pawn: Any) -> bool:
    hx, hy, _hz = _state.get("host") or (0.0, 0.0, 0.0)
    ax, ay, _az = _xyz(_loc(pawn))
    return math.hypot(ax - hx, ay - hy) <= _HOME_R


def _guest_ready() -> bool:
    pawns = _refresh_pawns()
    return bool(pawns) and all(_alive(p) and _near_host(p) for p in pawns)


def _pull_home() -> None:
    host = _state.get("host") or (0.0, 0.0, 0.0)
    hx, hy, hz = host
    for pawn in list(_state.get("pawns") or []):
        try:
            _teleport(pawn, hx, hy, hz, require_alive=False)
        except Exception:
            pass


def _set_needed(needed: bool) -> None:
    try:
        from . import camera_tick

        camera_tick.set_needed("party_reveal", bool(needed))
    except Exception:
        pass


def abort(*, pull: bool = True) -> dict[str, Any]:
    _state["done"] = True
    _set_needed(False)
    if pull:
        try:
            _refresh_pawns()
            _pull_home()
        except Exception:
            pass
    _log("aborted")
    status = last_status()
    return {"ok": True, "message": "Party Reveal aborted. Guests pulled to host.", **status}


def _finish() -> None:
    _pull_home()
    _state["done"] = True
    _set_needed(False)
    _log(f"sweep done hops={len(_load_pts())}")


def _tick(_obj: Any, _args: Any, _ret: Any, _func: Any) -> None:
    if _state.get("done"):
        return
    try:
        from . import travel_gate

        if travel_gate.is_travel_quiet():
            _log("travel quiet — aborting sweep")
            abort(pull=True)
            return
    except Exception:
        pass
    now = time.monotonic()
    if now - float(_state.get("last") or 0.0) < _DWELL_S:
        return
    _state["last"] = now
    pts = _load_pts()
    if _state.get("wait_alive"):
        waited = now - float(_state.get("wait_since") or 0.0)
        if now - float(_state.get("wait_log") or 0.0) >= 5.0:
            _state["wait_log"] = now
            _log(f"waiting standup at host ({waited:.0f}s)")
            _pull_home()
        if waited < _WAIT_S:
            return
        if _guest_ready():
            sit_since = float(_state.get("sit_since") or 0.0)
            if sit_since <= 0.0:
                _state["sit_since"] = now
                _log("guest at host, sitting")
                return
            if now - sit_since < _SIT_S:
                return
            _log("guest stood up at host, continuing")
            _state["wait_alive"] = False
            _state["sit_since"] = 0.0
        else:
            _state["sit_since"] = 0.0
            return
    idx = int(_state.get("idx") or 0)
    pawns = _refresh_pawns()
    if idx >= len(pts):
        _finish()
        return
    if not pawns:
        _state["wait_alive"] = True
        _state["wait_since"] = now
        _state["wait_log"] = now
        _state["sit_since"] = 0.0
        _pull_home()
        _log("no playable pawn, holding")
        return
    x, y, z = pts[idx]
    dead = False
    moved = 0
    for pawn in pawns:
        try:
            if _teleport(pawn, x, y, z):
                moved += 1
        except Exception:
            pass
        if not _alive(pawn):
            dead = True
    if dead:
        _pull_home()
        _state["wait_alive"] = True
        _state["wait_since"] = now
        _state["wait_log"] = now
        _state["sit_since"] = 0.0
        _log(f"DEAD hop={idx + 1}/{len(pts)} dest=({x},{y},{z})")
        return
    if moved <= 0:
        _log(f"no teleport hop={idx + 1}/{len(pts)}")
        _state["wait_alive"] = True
        _state["wait_since"] = now
        _state["sit_since"] = 0.0
        _pull_home()
        return
    if idx % 25 == 0:
        _log(f"sweep {idx + 1}/{len(pts)} at=({x},{y},{z})")
    _state["idx"] = idx + 1


def _ensure_registered() -> None:
    global _registered
    if _registered:
        return
    from . import camera_tick

    camera_tick.register("party_reveal", _tick, priority=70)
    _registered = True


def start() -> dict[str, Any]:
    pts = _load_pts()
    if not pts:
        return {"ok": False, "message": "Party Reveal hops file is missing.", **last_status()}
    abort(pull=False)
    _ensure_registered()
    pc_local = get_pc()
    host_ps = getattr(pc_local, "PlayerState", None) if pc_local is not None else None
    host_pawn = _pawn_of(pc_local, host_ps)
    hx, hy, hz = _xyz(_loc(host_pawn))
    try:
        pa = ENGINE.GameViewport.World.GameState.PlayerArray
        n = int(len(pa))
    except Exception:
        pa = None
        n = 0
    pawns: list[Any] = []
    targets: list[Any] = []
    for i in range(n):
        try:
            ps = pa[i]
        except Exception:
            continue
        if ps is host_ps:
            continue
        pawn = _pawn_of(_resolve_pc(ps, host_ps), ps)
        if not _alive(pawn):
            _log(f"skip {_ps_name(ps)!r} not alive")
            continue
        pawns.append(pawn)
        targets.append(ps)
        ax, ay, az = _xyz(_loc(pawn))
        _log(f"sweep target {_ps_name(ps)!r} at=({ax:.0f},{ay:.0f},{az:.0f})")
    if not pawns:
        return {
            "ok": False,
            "message": "Party Reveal needs a live guest in this session.",
            **last_status(),
        }
    _state.update(
        {
            "idx": 0,
            "last": 0.0,
            "pawns": pawns,
            "targets": targets,
            "host": (hx, hy, hz),
            "host_ps": host_ps,
            "wait_alive": True,
            "wait_since": time.monotonic() - _WAIT_S,
            "wait_log": 0.0,
            "sit_since": 0.0,
            "done": False,
        }
    )
    if _guest_ready():
        _state["wait_alive"] = False
    _set_needed(True)
    _log(f"armed hops={len(pts)} guests={len(pawns)} dwell={_DWELL_S}s")
    status = last_status()
    return {
        "ok": True,
        "message": (
            f"Party Reveal started for {len(pawns)} guest(s), {len(pts)} hops. "
            "Abort pulls them back to you."
        ),
        **status,
    }
