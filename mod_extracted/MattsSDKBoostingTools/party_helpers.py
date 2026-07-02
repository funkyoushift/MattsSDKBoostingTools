"""Shared party/player helpers for Matt's SDK Boosting Tools.

This intentionally excludes GenieBotControl's lobby/session kick timers and lobby control commands.
"""
from __future__ import annotations

from typing import Any, List, Optional, Tuple

from mods_base import ENGINE, get_pc
from unrealsdk import find_all, logging

_PREFIX = "[Matts SDK Boosting Tools]"


def _log(msg: str, *args: Any) -> None:
    logging.info(_PREFIX + " " + (msg % args if args else msg))


def _is_obj_cdo(obj: Any) -> bool:
    cls = getattr(obj, "Class", None)
    if cls is None:
        return False
    cdo = getattr(cls, "ClassDefaultObject", None)
    return cdo is not None and obj is cdo


def _gbc_net_driver(world: Any) -> Optional[Any]:
    if world is None:
        return None
    nd = getattr(world, "NetDriver", None)
    if nd is not None:
        return nd
    gnd = getattr(world, "GetNetDriver", None)
    if callable(gnd):
        try:
            return gnd()
        except Exception:
            pass
    return None


def _gbc_pc_has_listen_authority() -> bool:
    pc = get_pc()
    if pc is None:
        return False
    try:
        return bool(pc.HasAuthority())
    except Exception:
        return True


def _gbc_is_listen_host_world(world: Any) -> bool:
    if world is None:
        return False
    if not _gbc_pc_has_listen_authority():
        return False
    try:
        from unrealsdk.unreal import ENetMode
        if world.GetNetMode() == ENetMode.NM_ListenServer:
            return True
    except Exception:
        pass
    try:
        return int(world.GetNetMode()) == 2
    except Exception:
        return True


def _gbc_session_world_and_gamestate() -> Tuple[Optional[Any], Optional[Any]]:
    try:
        w = getattr(ENGINE.GameViewport, "World", None)
    except Exception:
        w = None
    if w is None:
        return None, None
    return w, getattr(w, "GameState", None)


def _gbc_resolve_player_display_name(ps: Any) -> str:
    if ps is None:
        return "(no ps)"
    gpn = getattr(ps, "GetPlayerName", None)
    if callable(gpn):
        try:
            s = gpn()
            if s is not None:
                return str(s)[:200]
        except Exception:
            pass
    for attr in ("PlayerName", "PlayerNamePrivate", "CachedPlayerName"):
        raw = getattr(ps, attr, None)
        if raw is None:
            continue
        if isinstance(raw, str):
            return raw[:200] if raw else "(no name)"
        if callable(raw):
            try:
                s = raw()
                if s is not None:
                    return str(s)[:200]
            except Exception:
                continue
            continue
        return str(raw)[:200]
    try:
        return str(getattr(ps, "PlayerId", None) or ps)[:80]
    except Exception:
        return "(unknown)"


def _gbc_resolve_player_index_for_name_substring(gs: Any, name_sub: str) -> Tuple[Optional[int], str]:
    t = (name_sub or "").strip()
    if not t:
        return None, "empty name substring"
    pa = getattr(gs, "PlayerArray", None)
    if pa is None:
        return None, "PlayerArray missing"
    try:
        n = len(pa)
    except Exception:
        return None, "could not read PlayerArray length"
    key = t.lower()
    matches: List[int] = []
    for i in range(n):
        try:
            ps = pa[i]
        except Exception:
            continue
        if ps is None:
            continue
        nm = _gbc_resolve_player_display_name(ps)
        if key in nm.lower():
            matches.append(i)
    if not matches:
        return None, "no name contains %r — refresh the GUI player list" % t
    if len(matches) > 1:
        return None, "ambiguous %r — indices %s" % (t, matches)
    return matches[0], ""


def _gbc_find_pc_for_player_state(ps: Any, world: Optional[Any] = None) -> Optional[Any]:
    if ps is None:
        return None
    if world is not None:
        nd = _gbc_net_driver(world)
        conns = getattr(nd, "ClientConnections", None) if nd is not None else None
        if conns is not None:
            try:
                n = len(conns)
            except Exception:
                n = 0
            for i in range(n):
                try:
                    c = conns[i]
                except Exception:
                    continue
                if c is None:
                    continue
                if getattr(c, "PlayerState", None) is ps:
                    rpc = getattr(c, "PlayerController", None)
                    if rpc is not None:
                        return rpc
    gpc = getattr(ps, "GetPlayerController", None)
    if callable(gpc):
        try:
            c = gpc()
            if c is not None:
                return c
        except Exception:
            pass
    owner = getattr(ps, "Owner", None)
    if owner is not None:
        for meth in ("GetOwnerController", "GetController", "GetPlayerController"):
            m = getattr(owner, meth, None)
            if callable(m):
                try:
                    c = m()
                    if c is not None and getattr(c, "PlayerState", None) is ps:
                        return c
                except Exception:
                    pass
    for cls in ("OakPlayerController", "PlayerController"):
        try:
            objs = find_all(cls, False) or []
        except Exception:
            objs = []
        for obj in objs:
            if obj is None or _is_obj_cdo(obj):
                continue
            if getattr(obj, "PlayerState", None) is ps:
                return obj
    return None



def _gbc_find_remote_pc_name_fallback(ps: Any, host_ps: Any, display_name: str, log_prefix: str) -> Optional[Any]:
    """Fallback resolver: scan OakPlayerController/PlayerController by PlayerState display name."""
    wanted = (display_name or _gbc_resolve_player_display_name(ps) or "").strip().lower()
    if not wanted:
        return None
    host_name = _gbc_resolve_player_display_name(host_ps).strip().lower() if host_ps is not None else ""
    for cls in ("OakPlayerController", "PlayerController"):
        try:
            objs = find_all(cls, False) or []
        except Exception:
            objs = []
        for obj in objs:
            if obj is None or _is_obj_cdo(obj):
                continue
            ops = getattr(obj, "PlayerState", None)
            if ops is None or ops is host_ps:
                continue
            nm = _gbc_resolve_player_display_name(ops).strip().lower()
            if not nm:
                continue
            if nm == wanted or wanted in nm or nm in wanted:
                if host_name and nm == host_name:
                    continue
                return obj
    return None


def _gbc_resolve_remote_pc_for_party_kick(
    ps: Any,
    world: Any,
    host_ps: Any,
    display_name: str,
    log_prefix: str,
) -> Optional[Any]:
    """Same resolution path for manual kick: NetDriver -> PS -> find_all, then name fallback."""
    rpc = _gbc_find_pc_for_player_state(ps, world)
    if rpc is not None and getattr(rpc, "PlayerState", None) is not host_ps:
        try:
            pc_path = str(getattr(rpc, "PathName", rpc))[:160]
        except Exception:
            pc_path = str(rpc)[:160]
        _log("%s: resolved remote pc via PlayerState match for %s -> %s", log_prefix, display_name, pc_path)
        return rpc
    _log(
        "%s: PlayerState match failed for %s; trying OakPlayerController PlayerName match",
        log_prefix,
        display_name,
    )
    rpc = _gbc_find_remote_pc_name_fallback(ps, host_ps, display_name, log_prefix)
    if rpc is None:
        _log("%s: no remote OakPlayerController found for %s", log_prefix, display_name)
    return rpc


def _gbc_party_kick_remote_pc(remote_pc: Any, reason: str) -> bool:
    """Call ClientPartyKick(reason). reason must be a Python str (wide string binding)."""
    fn = getattr(remote_pc, "ClientPartyKick", None)
    if not callable(fn):
        _log("gbc_party_kick_remote_pc: ClientPartyKick not callable on %s", type(remote_pc).__name__)
        return False
    try:
        fn(str(reason))
        return True
    except Exception as e:
        _log("gbc_party_kick_remote_pc: ClientPartyKick failed: %s", e)
        return False


def _kick_party_player_by_index(player_index: int, reason: str = "Kicked by host") -> bool:
    """Kick the selected remote party member by GameState.PlayerArray index."""
    world, gs = _gbc_session_world_and_gamestate()
    if world is None or gs is None:
        _log("Kick Player: no active world/game state.")
        return False
    if not _gbc_is_listen_host_world(world):
        _log("Kick Player: only the listen host can kick party players.")
        return False
    pa = getattr(gs, "PlayerArray", None)
    if pa is None:
        _log("Kick Player: GameState.PlayerArray missing.")
        return False
    try:
        ps = pa[int(player_index)]
    except Exception:
        _log("Kick Player: invalid party player index %s.", player_index)
        return False
    host_pc = get_pc()
    host_ps = getattr(host_pc, "PlayerState", None) if host_pc is not None else None
    display_name = _gbc_resolve_player_display_name(ps)
    if ps is None:
        _log("Kick Player: selected PlayerState is missing.")
        return False
    if host_ps is not None and ps is host_ps:
        _log("Kick Player: refusing to kick the local host (%s).", display_name)
        return False
    remote_pc = _gbc_resolve_remote_pc_for_party_kick(ps, world, host_ps, display_name, "Kick Player")
    if remote_pc is None:
        return False
    ok = _gbc_party_kick_remote_pc(remote_pc, reason)
    if ok:
        _log("Kick Player: requested party kick for %s.", display_name)
    return ok

def _list_party_players() -> List[Tuple[int, str]]:
    _, gs = _gbc_session_world_and_gamestate()
    pa = getattr(gs, "PlayerArray", None) if gs is not None else None
    if pa is None:
        return []
    try:
        n = len(pa)
    except Exception:
        return []
    out: List[Tuple[int, str]] = []
    for i in range(n):
        try:
            ps = pa[i]
        except Exception:
            ps = None
        if ps is not None:
            out.append((i, _gbc_resolve_player_display_name(ps)))
    return out


def _gbc_run_session_timer_from_give_serial() -> None:
    # GenieBotControl used this to trigger its lobby/session kick timer. Removed on purpose.
    return None
