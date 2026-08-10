"""StreamerChaos — local hotkeys + console for verified streamer interaction hooks."""

from __future__ import annotations

import threading
from typing import Any

import unrealsdk
from mods_base import CoopSupport, Game, build_mod, command, get_pc, hook, keybind
from unrealsdk import find_object, logging

__version__ = "0.1.0"

_PREFIX = "[StreamerChaos]"
_DEFAULT_LAUNCH_Z = 5000.0
_DEFAULT_LOCK_SECS = 5.0
_DEFAULT_INVERT_SECS = 8.0
_SPAWN_PATTERN_TYPE = 49152
_SPAWN_PATTERN_NAME = "spawnpattern_default_loot"

_lock = threading.Lock()
_unlock_timer: threading.Timer | None = None
_invert_timer: threading.Timer | None = None
_invert_backup: dict[str, tuple[Any, str, Any]] = {}
_pending_launch_z: float | None = None


def _log(msg: str) -> None:
    try:
        logging.info(f"{_PREFIX} {msg}")
    except Exception:
        print(f"{_PREFIX} {msg}")


def _pc() -> Any:
    try:
        return get_pc()
    except Exception:
        return None


def _pawn(pc: Any = None) -> Any:
    pc = pc or _pc()
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


def _parse_float(args: Any, default: float) -> float:
    try:
        if args is None:
            return default
        raw = getattr(args, "seconds", None)
        if raw is None:
            raw = getattr(args, "z", None)
        if raw is None and hasattr(args, "__iter__") and not isinstance(args, (str, bytes)):
            parts = list(args)
            raw = parts[0] if parts else None
        if raw is None:
            return default
        return float(raw)
    except Exception:
        return default


# ---------------------------------------------------------------------------
# Effects (local PC)
# ---------------------------------------------------------------------------


def do_unlock(pc: Any = None) -> str:
    pc = pc or _pc()
    if pc is None:
        return "no PC"
    ok = False
    for name in (
        "ResetIgnoreLookInput",
        "ResetIgnoreMoveInput",
        "ResetIgnoreInputFlags",
    ):
        if _try_call(pc, name):
            ok = True
    return "unlock OK" if ok else "unlock failed"


def do_lock_look(pc: Any = None, seconds: float = _DEFAULT_LOCK_SECS) -> str:
    pc = pc or _pc()
    if pc is None:
        return "no PC"
    ok = _try_call(pc, "SetIgnoreLookInput", True) or _try_call(pc, "SetIgnoreLookInput")
    if ok:
        _schedule_unlock(float(seconds), pc)
    return f"lock look {'OK' if ok else 'FAILED'} ({seconds}s)"


def do_lock_move(pc: Any = None, seconds: float = _DEFAULT_LOCK_SECS) -> str:
    pc = pc or _pc()
    if pc is None:
        return "no PC"
    ok = _try_call(pc, "SetIgnoreMoveInput", True) or _try_call(pc, "SetIgnoreMoveInput")
    if ok:
        _schedule_unlock(float(seconds), pc)
    return f"lock move {'OK' if ok else 'FAILED'} ({seconds}s)"


def do_lock_both(pc: Any = None, seconds: float = _DEFAULT_LOCK_SECS) -> str:
    pc = pc or _pc()
    if pc is None:
        return "no PC"
    ok_l = _try_call(pc, "SetIgnoreLookInput", True) or _try_call(pc, "SetIgnoreLookInput")
    ok_m = _try_call(pc, "SetIgnoreMoveInput", True) or _try_call(pc, "SetIgnoreMoveInput")
    if ok_l or ok_m:
        _schedule_unlock(float(seconds), pc)
    return f"lock look={'OK' if ok_l else 'FAIL'} move={'OK' if ok_m else 'FAIL'} ({seconds}s)"


def _schedule_unlock(seconds: float, pc: Any) -> None:
    global _unlock_timer

    def _fire() -> None:
        try:
            msg = do_unlock(pc)
            _log(f"auto-unlock: {msg}")
        except Exception as exc:
            _log(f"auto-unlock ERR {exc!r}")

    with _lock:
        if _unlock_timer is not None:
            try:
                _unlock_timer.cancel()
            except Exception:
                pass
        _unlock_timer = threading.Timer(max(0.5, float(seconds)), _fire)
        _unlock_timer.daemon = True
        _unlock_timer.start()


def do_invert_look(pc: Any = None, seconds: float = _DEFAULT_INVERT_SECS) -> str:
    global _invert_backup, _invert_timer
    pc = pc or _pc()
    if pc is None:
        return "no PC"

    targets: list[tuple[str, Any]] = [("pc", pc)]
    for attr in ("PlayerInput", "GbxPlayerInput", "EnhancedPlayerInput"):
        try:
            obj = getattr(pc, attr, None)
        except Exception:
            obj = None
        if obj is not None:
            targets.append((attr, obj))

    flipped: list[str] = []
    _invert_backup = {}
    scale_names = ("InputYawScale", "InputPitchScale", "LookRightScale", "LookUpScale")

    for label, obj in targets:
        for name in scale_names:
            if not hasattr(obj, name):
                continue
            try:
                cur = getattr(obj, name)
                if callable(cur):
                    continue
                key = f"{label}.{name}"
                _invert_backup[key] = (obj, name, cur)
                if isinstance(cur, (int, float)):
                    setattr(obj, name, float(cur) * -1.0)
                    flipped.append(key)
            except Exception:
                continue

    def _restore() -> None:
        for key, triple in list(_invert_backup.items()):
            obj, name, cur = triple
            try:
                setattr(obj, name, cur)
            except Exception:
                pass
        _log("invert restored")

    with _lock:
        if _invert_timer is not None:
            try:
                _invert_timer.cancel()
            except Exception:
                pass
        _invert_timer = threading.Timer(max(0.5, float(seconds)), _restore)
        _invert_timer.daemon = True
        _invert_timer.start()

    if not flipped:
        return "invert: nothing flipped"
    return f"invert OK {flipped} ({seconds}s)"


def do_kill(pc: Any = None) -> str:
    pawn = _pawn(pc)
    if pawn is None:
        return "kill: no pawn"
    _try_call(pawn, "SetCanBeDowned", True)
    start = getattr(pawn, "StartDownState", None)
    if not callable(start):
        return "kill: StartDownState missing"
    try:
        start(True)
        return "kill OK StartDownState(True)"
    except Exception as exc:
        return f"kill ERR {exc!r}"


def do_ffyl(pc: Any = None) -> str:
    pawn = _pawn(pc)
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
        return "ffyl OK StartDownState(False)"
    except Exception as exc:
        return f"ffyl ERR {exc!r}"


def do_empty_backpack(pc: Any = None) -> str:
    pc = pc or _pc()
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
        return "empty backpack OK (deleted)"
    except Exception as exc:
        return f"empty ERR {exc!r}"


def do_drop_backpack(pc: Any = None) -> str:
    pc = pc or _pc()
    pawn = _pawn(pc)
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
    for socket in ("None", "", "ROOT"):
        try:
            fn(pc, "Backpack", pawn, handle, socket)
            return f"drop backpack OK socket={socket!r}"
        except Exception as exc:
            last = exc
            continue
    return f"drop ERR {last!r}"


def _fire_launch_impulse(z_boost: float, pc: Any = None) -> str:
    pc = pc or _pc()
    character = _pawn(pc)
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
        return f"launch OK Z={impulse_z:.1f} (boost={z_boost})"
    except Exception as exc:
        return f"launch ERR {exc!r}"


def do_launch(pc: Any = None, z_boost: float = _DEFAULT_LAUNCH_Z) -> str:
    global _pending_launch_z
    msg = _fire_launch_impulse(float(z_boost), pc)
    if msg.startswith("launch OK"):
        return msg
    # Retry on camera tick (same as Super Dash / probe).
    _pending_launch_z = float(z_boost)
    return f"{msg}; queued camera-tick retry"


def _tick_pending_launch(*_args: Any, **_kwargs: Any) -> None:
    global _pending_launch_z
    if _pending_launch_z is None:
        return
    z = float(_pending_launch_z)
    _pending_launch_z = None
    _log(_fire_launch_impulse(z))


try:
    hook(
        "/Script/Engine.CameraModifier:BlueprintModifyCamera",
        immediately_enable=True,
        hook_identifier="streamer_chaos_launch_v1",
    )(_tick_pending_launch)
except Exception as exc:
    _log(f"launch camera hook skipped: {exc!r}")


# ---------------------------------------------------------------------------
# Console
# ---------------------------------------------------------------------------


@command("sc_help", description="List StreamerChaos commands and default hotkeys.")
def sc_help(_args: Any = None) -> None:
    for line in (
        "sc_launch [z] / NumPad5",
        "sc_drop_backpack / NumPad6 — SpillOut whole backpack",
        "sc_empty_backpack / NumPad7 — DELETE backpack",
        "sc_ffyl / NumPad8",
        "sc_kill / NumPad9",
        "sc_invert [sec] / NumPad4",
        "sc_lock_look [sec] / NumPad1",
        "sc_lock_move [sec] / NumPad2",
        "sc_lock_both [sec] / NumPad3",
        "sc_unlock / NumPad0",
        "Hotkeys rebindable in oak2 options. Local player only.",
    ):
        _log(line)


@command("sc_unlock", description="Reset ignore look/move.")
def sc_unlock(_args: Any = None) -> None:
    _log(do_unlock())


@command("sc_lock_look", description="Ignore look input for N seconds (default 5).")
def sc_lock_look(args: Any = None) -> None:
    _log(do_lock_look(seconds=_parse_float(args, _DEFAULT_LOCK_SECS)))


sc_lock_look.add_argument("seconds", nargs="?", default="5")


@command("sc_lock_move", description="Ignore move input for N seconds (default 5).")
def sc_lock_move(args: Any = None) -> None:
    _log(do_lock_move(seconds=_parse_float(args, _DEFAULT_LOCK_SECS)))


sc_lock_move.add_argument("seconds", nargs="?", default="5")


@command("sc_lock_both", description="Ignore look+move for N seconds (default 5).")
def sc_lock_both(args: Any = None) -> None:
    _log(do_lock_both(seconds=_parse_float(args, _DEFAULT_LOCK_SECS)))


sc_lock_both.add_argument("seconds", nargs="?", default="5")


@command("sc_invert", description="Invert look scales for N seconds (default 8).")
def sc_invert(args: Any = None) -> None:
    _log(do_invert_look(seconds=_parse_float(args, _DEFAULT_INVERT_SECS)))


sc_invert.add_argument("seconds", nargs="?", default="8")


@command("sc_kill", description="Instant kill via StartDownState(True).")
def sc_kill(_args: Any = None) -> None:
    _log(do_kill())


@command("sc_ffyl", description="FFYL via StartDownState(False).")
def sc_ffyl(_args: Any = None) -> None:
    _log(do_ffyl())


@command("sc_empty_backpack", description="DELETE backpack via EmptyContainer.")
def sc_empty_backpack(_args: Any = None) -> None:
    _log(do_empty_backpack())


@command("sc_drop_backpack", description="DROP backpack to ground via SpillOut.")
def sc_drop_backpack(_args: Any = None) -> None:
    _log(do_drop_backpack())


@command("sc_launch", description="Launch via AddImpulse (default Z boost 5000).")
def sc_launch(args: Any = None) -> None:
    _log(do_launch(z_boost=_parse_float(args, _DEFAULT_LAUNCH_Z)))


sc_launch.add_argument("z", nargs="?", default="5000")


# ---------------------------------------------------------------------------
# Keybinds (assignable in oak2 / mods_base options)
# ---------------------------------------------------------------------------


def _kb(msg_fn: Any) -> Any:
    def _run() -> None:
        _log(msg_fn())

    return _run


kb_unlock = keybind(
    "StreamerChaos: Unlock",
    "NumPadZero",
    callback=_kb(do_unlock),
    display_name="StreamerChaos Unlock",
    description="Reset ignore look/move input.",
)
kb_lock_look = keybind(
    "StreamerChaos: Lock Look",
    "NumPadOne",
    callback=_kb(do_lock_look),
    display_name="StreamerChaos Lock Look",
    description="Ignore look input for 5 seconds.",
)
kb_lock_move = keybind(
    "StreamerChaos: Lock Move",
    "NumPadTwo",
    callback=_kb(do_lock_move),
    display_name="StreamerChaos Lock Move",
    description="Ignore move input for 5 seconds.",
)
kb_lock_both = keybind(
    "StreamerChaos: Lock Both",
    "NumPadThree",
    callback=_kb(do_lock_both),
    display_name="StreamerChaos Lock Both",
    description="Ignore look+move for 5 seconds.",
)
kb_invert = keybind(
    "StreamerChaos: Invert Look",
    "NumPadFour",
    callback=_kb(do_invert_look),
    display_name="StreamerChaos Invert Look",
    description="Negate look scales for 8 seconds.",
)
kb_launch = keybind(
    "StreamerChaos: Launch",
    "NumPadFive",
    callback=_kb(do_launch),
    display_name="StreamerChaos Launch",
    description="AddImpulse Z launch (boost 5000).",
)
kb_drop = keybind(
    "StreamerChaos: Drop Backpack",
    "NumPadSix",
    callback=_kb(do_drop_backpack),
    display_name="StreamerChaos Drop Backpack",
    description="SpillOut whole backpack to ground.",
)
kb_empty = keybind(
    "StreamerChaos: Empty Backpack",
    "NumPadSeven",
    callback=_kb(do_empty_backpack),
    display_name="StreamerChaos Empty Backpack",
    description="DELETE backpack via EmptyContainer.",
)
kb_ffyl = keybind(
    "StreamerChaos: FFYL",
    "NumPadEight",
    callback=_kb(do_ffyl),
    display_name="StreamerChaos FFYL",
    description="StartDownState(False) Fight For Your Life.",
)
kb_kill = keybind(
    "StreamerChaos: Kill",
    "NumPadNine",
    callback=_kb(do_kill),
    display_name="StreamerChaos Kill",
    description="StartDownState(True) instant kill.",
)


build_mod(
    name="StreamerChaos",
    author="MSBT",
    description="Verified streamer chaos: launch, drop/empty bag, kill/FFYL, invert, lock input.",
    supported_games=Game.BL4,
    coop_support=CoopSupport.ClientSide,
    keybinds=[
        kb_unlock,
        kb_lock_look,
        kb_lock_move,
        kb_lock_both,
        kb_invert,
        kb_launch,
        kb_drop,
        kb_empty,
        kb_ffyl,
        kb_kill,
    ],
    commands=[
        sc_help,
        sc_unlock,
        sc_lock_look,
        sc_lock_move,
        sc_lock_both,
        sc_invert,
        sc_kill,
        sc_ffyl,
        sc_empty_backpack,
        sc_drop_backpack,
        sc_launch,
    ],
)

_log(f"loaded v{__version__} — sc_help / NumPad hotkeys")
