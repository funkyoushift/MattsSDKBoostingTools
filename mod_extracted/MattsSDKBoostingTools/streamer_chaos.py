"""Streamer chaos actions for MSBT Dev Tools / Quick Menu (party-targetable).

Verified hooks from TwitchInteractionProbe / StreamerChaos. No equipped-only SpillOut.
"""

from __future__ import annotations

import time
from typing import Any

import unrealsdk
from mods_base import get_pc
from unrealsdk import find_object

_DEFAULT_LAUNCH_Z = 5000.0
_DEFAULT_LOCK_SECS = 5.0
_DEFAULT_INVERT_SECS = 8.0
_SPAWN_PATTERN_TYPE = 49152
_SPAWN_PATTERN_NAME = "spawnpattern_default_loot"

_unlock_deadlines: dict[int, tuple[float, Any]] = {}
_invert_deadlines: dict[int, float] = {}
_invert_backups: dict[int, dict[str, tuple[Any, str, Any]]] = {}
_pending_launch: dict[int, float] = {}


def _inventory_statics() -> Any:
    for cls_name, path in (
        ("OakInventoryStatics", "Default__OakInventoryStatics"),
        ("GbxInventoryStatics", "Default__GbxInventoryStatics"),
        ("InventoryStatics", "Default__InventoryStatics"),
    ):
        try:
            obj = find_object(cls_name, path)
        except Exception:
            obj = None
        if obj is not None:
            return obj
    return None


def _pawn_from_pc(pc: Any) -> Any:
    if pc is None:
        return None
    for attr in ("OakCharacter", "Pawn", "AcknowledgedPawn", "ControlledPawn", "Character"):
        try:
            obj = getattr(pc, attr, None)
        except Exception:
            obj = None
        if obj is not None:
            return obj
    return None


def _movement(character: Any) -> Any:
    if character is None:
        return None
    for attr in ("OakCharacterMovement", "CharacterMovement", "MovementComponent"):
        try:
            move = getattr(character, attr, None)
        except Exception:
            move = None
        if move is not None:
            return move
    return None


def _try_call(obj: Any, name: str, *args: Any) -> bool:
    fn = getattr(obj, name, None) if obj is not None else None
    if not callable(fn):
        return False
    try:
        fn(*args)
        return True
    except TypeError:
        if args:
            try:
                fn()
                return True
            except Exception:
                return False
        return False
    except Exception:
        return False


def _pc_key(pc: Any) -> int:
    try:
        return int(pc._get_address())
    except Exception:
        return id(pc)


def unlock_for_pc(pc: Any) -> str:
    if pc is None:
        return "no PC"
    ok = False
    for name in ("ResetIgnoreLookInput", "ResetIgnoreMoveInput", "ResetIgnoreInputFlags"):
        if _try_call(pc, name):
            ok = True
    return "unlock OK" if ok else "unlock failed"


def _schedule_unlock(pc: Any, seconds: float) -> None:
    key = _pc_key(pc)
    _unlock_deadlines[key] = (time.monotonic() + max(0.5, float(seconds)), pc)


def lock_look_for_pc(pc: Any, seconds: float = _DEFAULT_LOCK_SECS) -> str:
    if pc is None:
        return "no PC"
    ok = _try_call(pc, "SetIgnoreLookInput", True) or _try_call(pc, "SetIgnoreLookInput")
    if ok:
        _schedule_unlock(pc, seconds)
    return f"lock look {'OK' if ok else 'FAILED'} ({seconds}s)"


def lock_move_for_pc(pc: Any, seconds: float = _DEFAULT_LOCK_SECS) -> str:
    if pc is None:
        return "no PC"
    ok = _try_call(pc, "SetIgnoreMoveInput", True) or _try_call(pc, "SetIgnoreMoveInput")
    if ok:
        _schedule_unlock(pc, seconds)
    return f"lock move {'OK' if ok else 'FAILED'} ({seconds}s)"


def lock_both_for_pc(pc: Any, seconds: float = _DEFAULT_LOCK_SECS) -> str:
    if pc is None:
        return "no PC"
    ok_l = _try_call(pc, "SetIgnoreLookInput", True) or _try_call(pc, "SetIgnoreLookInput")
    ok_m = _try_call(pc, "SetIgnoreMoveInput", True) or _try_call(pc, "SetIgnoreMoveInput")
    if ok_l or ok_m:
        _schedule_unlock(pc, seconds)
    return f"lock look={'OK' if ok_l else 'FAIL'} move={'OK' if ok_m else 'FAIL'} ({seconds}s)"


def invert_look_for_pc(pc: Any, seconds: float = _DEFAULT_INVERT_SECS) -> str:
    if pc is None:
        return "no PC"
    key = _pc_key(pc)
    targets: list[tuple[str, Any]] = [("pc", pc)]
    for attr in ("PlayerInput", "GbxPlayerInput", "EnhancedPlayerInput"):
        try:
            obj = getattr(pc, attr, None)
        except Exception:
            obj = None
        if obj is not None:
            targets.append((attr, obj))

    _restore_invert(key)
    backup: dict[str, tuple[Any, str, Any]] = {}
    flipped: list[str] = []
    for label, obj in targets:
        for name in ("InputYawScale", "InputPitchScale", "LookRightScale", "LookUpScale"):
            if not hasattr(obj, name):
                continue
            try:
                cur = getattr(obj, name)
                if callable(cur) or not isinstance(cur, (int, float)):
                    continue
                bkey = f"{label}.{name}"
                backup[bkey] = (obj, name, cur)
                setattr(obj, name, float(cur) * -1.0)
                flipped.append(bkey)
            except Exception:
                continue

    _invert_backups[key] = backup
    _invert_deadlines[key] = time.monotonic() + max(0.5, float(seconds))

    if not flipped:
        return "invert: nothing flipped"
    return f"invert OK ({seconds}s) {flipped}"


def kill_for_pc(pc: Any) -> str:
    pawn = _pawn_from_pc(pc)
    if pawn is None:
        return "kill: no pawn"
    _try_call(pawn, "SetCanBeDowned", True)
    start = getattr(pawn, "StartDownState", None)
    if not callable(start):
        return "kill: StartDownState missing"
    try:
        start(True)
        return "kill OK"
    except Exception as exc:
        return f"kill ERR {exc!r}"


def ffyl_for_pc(pc: Any) -> str:
    pawn = _pawn_from_pc(pc)
    if pawn is None:
        return "ffyl: no pawn"
    statics = _inventory_statics()
    _try_call(pawn, "SetCanBeDowned", True)
    if statics is not None:
        unblock = getattr(statics, "UnblockCharacterHealth", None)
        if callable(unblock):
            try:
                unblock(pawn)
            except Exception:
                pass
        drain = getattr(statics, "DrainResourcePool", None)
        if callable(drain):
            for resource in (
                "HealthType_Player_Overshield",
                "HealthType_Player_Shield_Armor",
                "HealthType_Player_Health_Flesh",
            ):
                try:
                    drain(pawn, resource, 1.0, 0.0)
                except Exception:
                    pass
    start = getattr(pawn, "StartDownState", None)
    if not callable(start):
        return "ffyl: StartDownState missing"
    try:
        start(False)
        return "ffyl OK"
    except Exception as exc:
        return f"ffyl ERR {exc!r}"


def empty_backpack_for_pc(pc: Any) -> str:
    statics = _inventory_statics()
    if pc is None or statics is None:
        return "empty: missing pc/statics"
    empty_fn = getattr(statics, "EmptyContainer", None)
    if not callable(empty_fn):
        return "empty: EmptyContainer missing"
    try:
        from unrealsdk.unreal import FGbxDefPtr  # type: ignore[import-not-found]

        ptr = FGbxDefPtr("Backpack", type="InventoryContainerDef")
        empty_fn(pc, ptr)
        return "empty backpack OK"
    except Exception as exc:
        return f"empty ERR {exc!r}"


def drop_backpack_for_pc(pc: Any) -> str:
    pawn = _pawn_from_pc(pc)
    statics = _inventory_statics()
    if pc is None or pawn is None or statics is None:
        return "drop: missing pc/pawn/statics"
    fn = getattr(statics, "SpillOutItemsInContainer", None)
    if not callable(fn):
        return "drop: SpillOutItemsInContainer missing"
    try:
        from unrealsdk.unreal import FGameDataHandle  # type: ignore[import-not-found]

        handle = FGameDataHandle(_SPAWN_PATTERN_TYPE, _SPAWN_PATTERN_NAME)
    except Exception as exc:
        return f"drop: FGameDataHandle ERR {exc!r}"
    last: Exception | None = None
    for socket in ("None", "", "ROOT"):
        try:
            fn(pc, "Backpack", pawn, handle, socket)
            return f"drop backpack OK socket={socket!r}"
        except Exception as exc:
            last = exc
            continue
    return f"drop ERR {last!r}"


def _fire_launch(pc: Any, z_boost: float) -> str:
    character = _pawn_from_pc(pc)
    if character is None:
        return "launch: no character"
    move = _movement(character)
    if move is None:
        return "launch: no movement"
    vx = vy = vz = 0.0
    try:
        vel = getattr(move, "Velocity", None)
        if vel is not None:
            vx = float(getattr(vel, "X", 0.0) or 0.0)
            vy = float(getattr(vel, "Y", 0.0) or 0.0)
            vz = float(getattr(vel, "Z", 0.0) or 0.0)
    except Exception:
        pass
    impulse_z = vz + float(z_boost)
    try:
        impulse = unrealsdk.make_struct(
            "Vector",
            X=float(vx),
            Y=float(vy),
            Z=float(impulse_z),
        )
        move.AddImpulse(impulse, True)
        return f"launch OK Z={impulse_z:.1f}"
    except Exception as exc:
        return f"launch ERR {exc!r}"


def launch_for_pc(pc: Any, z_boost: float = _DEFAULT_LAUNCH_Z) -> str:
    msg = _fire_launch(pc, float(z_boost))
    if msg.startswith("launch OK"):
        return msg
    if pc is not None:
        _pending_launch[_pc_key(pc)] = float(z_boost)
    return f"{msg}; queued tick retry"


def _tick_pending_launch_hook(*_args: Any, **_kwargs: Any) -> None:
    if not _pending_launch and not _unlock_deadlines and not _invert_deadlines:
        return
    now = time.monotonic()
    for key, (deadline, pc) in list(_unlock_deadlines.items()):
        if now >= deadline:
            _unlock_deadlines.pop(key, None)
            unlock_for_pc(pc)
    for key, deadline in list(_invert_deadlines.items()):
        if now >= deadline:
            _restore_invert(key)
    if not _pending_launch:
        return
    # Flush all pending by resolving local get_pc first, then leave others for next tick.
    local = get_pc()
    if local is None:
        return
    key = _pc_key(local)
    z = _pending_launch.pop(key, None)
    if z is not None:
        _fire_launch(local, z)


try:
    from mods_base import hook as _hook

    _hook(
        "/Script/Engine.CameraModifier:BlueprintModifyCamera",
        immediately_enable=True,
        hook_identifier="msbt_streamer_chaos_launch_v1",
    )(_tick_pending_launch_hook)
except Exception:
    pass


def tick_pending_launches() -> None:
    """Call from a game tick if queued launches remain (optional)."""
    _tick_pending_launch_hook()


def _restore_invert(key: int) -> None:
    backup = _invert_backups.pop(key, {})
    _invert_deadlines.pop(key, None)
    for obj, name, value in backup.values():
        try:
            setattr(obj, name, value)
        except Exception:
            pass


def clear_runtime_state(*, restore: bool = False) -> None:
    """Drop travel-unsafe UObject references; optionally restore before disable."""
    if restore:
        for _deadline, pc in list(_unlock_deadlines.values()):
            unlock_for_pc(pc)
        for key in list(_invert_backups):
            _restore_invert(key)
    _unlock_deadlines.clear()
    _invert_deadlines.clear()
    _invert_backups.clear()
    _pending_launch.clear()


def result_ok(msg: str) -> bool:
    low = str(msg).lower()
    if "err" in low or "fail" in low or "missing" in low or low.startswith("no "):
        return False
    return True
