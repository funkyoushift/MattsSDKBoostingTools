"""Player movement adjustment helpers for Matt's SDK Boosting Tools.

These helpers intentionally use broad, defensive reflection because BL4 movement
properties vary between pawn/controller/movement-component wrappers.  All writes
are best-effort and skip class defaults.
"""
from __future__ import annotations

import math
import time
from typing import Any

from mods_base import ENGINE, get_pc, hook
import unrealsdk
from unrealsdk import logging

try:
    from unrealsdk.hooks import Block as _UnrealHookBlock
except Exception:  # pragma: no cover - oak2 hook Block is optional
    try:
        from unrealsdk import Block as _UnrealHookBlock
    except Exception:
        _UnrealHookBlock = None

_PREFIX = "[Matts SDK Boosting Tools | Movement]"

# Captured live BL4 player-movement defaults. CDO defaults are not reliable for these.
_JUMP_DEFAULTS = {
    "default": {"height": 198.0, "z": 840.0, "use_h": True, "use_z": False, "clear_apex": False},
    "sprint": {"height": 198.0, "z": 735.0, "use_h": True, "use_z": True, "clear_apex": True},
    "double": {"height": 225.0, "z": 940.0, "use_h": True, "use_z": True, "clear_apex": True},
    # Slide was not separately captured; use Sprint shape unless the user edits it.
    "slide": {"height": 198.0, "z": 735.0, "use_h": True, "use_z": True, "clear_apex": True},
}
_JUMP_FORCE_TAGS = (
    ("default", "Movement.JumpType.DefaultJump"),
    ("sprint", "Movement.JumpType.SprintJump"),
    ("double", "Movement.JumpType.DoubleJump"),
    ("slide", "Movement.JumpType.SlideJump"),
)

# Live CharMoveComp fields we tune.  These names come from reflected BL4 movement
# objects, but the write logic below is custom and defensive.
_SPEED_FLOAT_FIELDS = (
    "MinAnalogWalkSpeed",
    "MaxWalkSpeed",
    "MaxGroundSpeed",
    "MaxGroundSpeedBase",
    "MaxWalkSpeedCrouched",
    "MaxCustomMovementSpeed",
    "MaxSwimSpeed",
    # Older BLImGui movement tuning wrote these names directly.  Keep them in
    # the shared backend so Reset Defaults clears speed boosts on every build.
    "GroundSpeed",
    "RunSpeed",
    "SprintSpeed",
    "MoveSpeed",
)
_SPEED_ATTRIBUTE_FIELDS = (
    "MaxGroundSpeedScale",
    "MovementSpeedScale",
    "PawnMovementSpeedScale",
    "MoveSpeedScale",
    "GroundSpeedScale",
    "SpeedScale",
)
_FLY_SPEED_FIELDS = (
    "MaxFlySpeed",
    "MaxFlyingSpeed",
    "FlySpeed",
    "MaxCustomMovementSpeed",
)
_ACCEL_FIELDS = (
    "MaxAcceleration",
    "BrakingDecelerationWalking",
    "MaxBrakingDecelerationWalking",
    "BrakingDecelerationFalling",
    "MaxBrakingDecelerationFalling",
    "BrakingDecelerationFlying",
    "MaxBrakingDecelerationFlying",
)
_GLIDE_FIELDS = (
    "GlidingAirControl",
    "GlidingSpeed",
    "GlidingSpeedBoost",
    "GlidingAcceleration",
    "GlidingDeceleration",
)
_VAULT_COST_FIELDS = (
    "VaultPowerCost_Dash",
    "VaultPowerCost_DoubleJump",
    "VaultPowerCost_Glide",
    "VaultPowerCost_Grapple",
    "VaultPowerCost_GroundSlam",
    "VaultPower_Forgiveness",
)

_INFINITE_JUMP_INDICES: set[int] = set()
# Cache labels / address signatures only — never keep pawn/move UObject wrappers
# across ticks. Stale wrappers after travel/despawn cause native ACCESS_VIOLATION
# (uncaught by Python try/except).
_INFINITE_JUMP_LABEL_CACHE: dict[int, str] = {}
_INFINITE_JUMP_LABEL_CACHE_TIME: float = 0.0
_INFINITE_JUMP_CAMERA_LAST_APPLY: float = 0.0
# Light checks ~10 Hz; write only when counters are spent / JumpMaxCount not open.
# Heavy find_all scans stay rare (Tobgun1: IJ ON ~76 FPS was per-tick UE spam).
_INFINITE_JUMP_CAMERA_INTERVAL_S: float = 0.1
_INFINITE_JUMP_HEAVY_SCAN_INTERVAL_S: float = 3.0
_INFINITE_JUMP_LAST_HEAVY_SCAN: float = 0.0
_INFINITE_JUMP_WORLD_SIG: tuple[int, int, int, int] | None = None
_INFINITE_JUMP_LOCAL_IDX: int | None = None


def _uobject_addr(obj: Any) -> int:
    """Native UObject address, or 0 if unavailable / dead. Never touches Name/Class."""
    if obj is None:
        return 0
    try:
        get_addr = getattr(obj, "_get_address", None)
        if callable(get_addr):
            addr = int(get_addr())
            if addr in (0, -1):
                return 0
            return addr
    except Exception:
        return 0
    return 0


def _uobject_alive(obj: Any) -> bool:
    """True if the wrapper still looks usable.

    Prefer a live native address. If this SDK build has no ``_get_address``,
    do not treat every pawn as dead — that skipped Infinite Jump and Pull Loot.
    """
    if obj is None:
        return False
    addr = _uobject_addr(obj)
    if addr:
        return True
    get_addr = getattr(obj, "_get_address", None)
    return not callable(get_addr)


def _is_listen_host_safe() -> bool:
    try:
        pc = get_pc()
        if pc is None:
            return False
        try:
            if not bool(pc.HasAuthority()):
                return False
        except Exception:
            pass
        world = None
        for attr in ("World", "GetWorld"):
            try:
                val = getattr(pc, attr, None)
                world = val() if callable(val) else val
                if world is not None:
                    break
            except Exception:
                pass
        if world is not None:
            try:
                from unrealsdk.unreal import ENetMode
                return world.GetNetMode() == ENetMode.NM_ListenServer
            except Exception:
                pass
            try:
                return int(world.GetNetMode()) == 2
            except Exception:
                pass
        return True
    except Exception:
        return False

def _log(msg: str) -> None:
    try:
        logging.info(f"{_PREFIX} {msg}")
    except Exception:
        pass


def _is_default(obj: Any) -> bool:
    """Best-effort CDO skip. Requires a live address — never probe Name/Class on stale wrappers."""
    if obj is None or not _uobject_alive(obj):
        return True
    try:
        # str() is safer than .Name/.Class on live wrappers; still wrapped in try.
        if "Default__" in str(obj):
            return True
    except Exception:
        return True
    return False


def _unique_live_objects(objs: list[Any]) -> list[Any]:
    out: list[Any] = []
    seen: set[int] = set()
    for obj in objs:
        if obj is None or _is_default(obj):
            continue
        try:
            key = id(obj)
        except Exception:
            key = len(seen) + 1
        if key in seen:
            continue
        seen.add(key)
        out.append(obj)
    return out


def live_player_controllers() -> list[Any]:
    objs: list[Any] = []
    try:
        pc = get_pc()
        if pc is not None:
            objs.append(pc)
    except Exception:
        pass
    for cls in ("OakPlayerController", "PlayerController"):
        try:
            objs.extend(list(unrealsdk.find_all(cls, False) or []))
        except Exception:
            pass
    # Prefer controllers with a PlayerState/Pawn/Outer level path; skip CDOs.
    return _unique_live_objects(objs)


def _is_local_player_controller(pc: Any) -> bool:
    if pc is None:
        return False
    try:
        local = get_pc()
        if local is not None and pc is local:
            return True
    except Exception:
        pass
    for attr_name in ("IsLocalPlayerController", "IsPrimaryPlayer", "bIsLocalPlayerController"):
        try:
            attr = getattr(pc, attr_name, None)
            if callable(attr) and bool(attr()):
                return True
            if attr is not None and not callable(attr) and bool(attr):
                return True
        except Exception:
            continue
    return False


def filter_controllers_by_scope(controllers: list[Any], scope: str = "all") -> list[Any]:
    """Filter live controllers by Local / All / Others (SQBT-inspired)."""
    key = str(scope or "all").strip().lower()
    if key in ("", "all", "everyone", "party"):
        return list(controllers)
    out: list[Any] = []
    for pc in controllers:
        is_local = _is_local_player_controller(pc)
        if key == "local" and is_local:
            out.append(pc)
        elif key in ("others", "other", "remote") and not is_local:
            out.append(pc)
    return out


def filter_pawns_by_scope(pawns: list[Any], scope: str = "all") -> list[Any]:
    """Filter pawns whose owning controller matches Local / All / Others."""
    key = str(scope or "all").strip().lower()
    if key in ("", "all", "everyone", "party"):
        return list(pawns)
    local_pc = None
    try:
        local_pc = get_pc()
    except Exception:
        local_pc = None
    local_pawn = pawn_for_controller(local_pc) if local_pc is not None else None
    local_id = id(local_pawn) if local_pawn is not None else None
    out: list[Any] = []
    for pawn in pawns:
        is_local = local_id is not None and id(pawn) == local_id
        if not is_local:
            # Secondary: controller ownership
            try:
                ctrl = getattr(pawn, "Controller", None)
                is_local = _is_local_player_controller(ctrl)
            except Exception:
                pass
        if key == "local" and is_local:
            out.append(pawn)
        elif key in ("others", "other", "remote", "nonhost") and not is_local:
            out.append(pawn)
    return out


def _call0(obj: Any, name: str) -> Any | None:
    try:
        fn = getattr(obj, name, None)
        if callable(fn):
            return fn()
    except Exception:
        pass
    return None


def pawn_for_controller(pc: Any) -> Any | None:
    for attr in ("Pawn", "AcknowledgedPawn", "Character", "ControlledPawn"):
        try:
            pawn = getattr(pc, attr, None)
            if pawn is not None and not _is_default(pawn):
                return pawn
        except Exception:
            pass
    for meth in ("GetPawn", "K2_GetPawn", "GetCharacter"):
        pawn = _call0(pc, meth)
        if pawn is not None and not _is_default(pawn):
            return pawn
    return None


def live_player_pawns() -> list[Any]:
    objs: list[Any] = []
    for pc in live_player_controllers():
        pawn = pawn_for_controller(pc)
        if pawn is not None:
            objs.append(pawn)
    for cls in ("OakCharacter", "GbxCharacter", "Character", "Pawn"):
        try:
            for obj in unrealsdk.find_all(cls, False) or []:
                if obj is None or _is_default(obj):
                    continue
                # Keep only likely player-owned pawns.  Enemy pawns usually do not
                # have a PlayerState-backed Controller.
                ctrl = getattr(obj, "Controller", None)
                ps = getattr(ctrl, "PlayerState", None) if ctrl is not None else getattr(obj, "PlayerState", None)
                if ps is not None:
                    objs.append(obj)
        except Exception:
            pass
    return _unique_live_objects(objs)


def _movement_objects_for_pawn(pawn: Any) -> list[Any]:
    """Return the pawn plus every likely live movement component for it.

    BL4 exposes the same CharMoveComp under several names depending on which
    base class is being reflected: CharacterMovement, OakCharacterMovement,
    GbxCharacterMovement, GbxNavMovement, and GbxEngineMovement.  Earlier builds
    only checked a small subset, which made the UI look like it applied but miss
    the real component on some clients.
    """
    objs: list[Any] = [pawn]
    for attr in (
        "CharacterMovement",
        "MovementComponent",
        "PawnMovementComponent",
        "PawnMovement",
        "Movement",
        "NavMovementComponent",
        "GbxCharacterMovement",
        "OakCharacterMovement",
        "GbxNavMovement",
        "GbxEngineMovement",
    ):
        try:
            comp = getattr(pawn, attr, None)
            if comp is not None:
                objs.append(comp)
        except Exception:
            pass
    for meth in ("GetCharacterMovement", "GetMovementComponent", "GetPawnMovementComponent"):
        comp = _call0(pawn, meth)
        if comp is not None:
            objs.append(comp)
    # Fallback: enumerate live OakCharacterMovementComponent objects and match
    # their OakCharacterOwner back to this pawn.  This is the most reliable path
    # for dumped CharMoveComp objects.
    for cls in ("OakCharacterMovementComponent", "GbxCharacterMovementComponent", "CharacterMovementComponent"):
        try:
            for comp in unrealsdk.find_all(cls, False) or []:
                if comp is None or _is_default(comp):
                    continue
                try:
                    owner = getattr(comp, "OakCharacterOwner", None) or getattr(comp, "CharacterOwner", None) or getattr(comp, "PawnOwner", None)
                except Exception:
                    owner = None
                if owner is pawn or (owner is not None and str(owner) == str(pawn)):
                    objs.append(comp)
        except Exception:
            pass
    return _unique_live_objects(objs)


def _write_attribute_struct(attr: Any, value: float) -> bool:
    """Write GbxAttributeFloat/Integer-style wrapped structs without replacing them."""
    if attr is None:
        return False
    wrote = False
    for field in ("Value", "BaseValue", "CurrentValue", "Base", "Current"):
        try:
            setattr(attr, field, float(value))
            wrote = True
        except Exception:
            pass
    for method_name in ("SetValue", "SetBaseValue", "SetCurrentValue"):
        try:
            method = getattr(attr, method_name, None)
            if callable(method):
                method(float(value))
                wrote = True
        except Exception:
            pass
    return wrote


def _set_attr(obj: Any, name: str, value: float) -> bool:
    try:
        if not hasattr(obj, name):
            return False
        current = getattr(obj, name, None)
        # Many BL4 movement fields in the dump are GbxAttributeFloat structs.
        # Replacing those structs with a raw float is unreliable; write their
        # Value/BaseValue fields first, then fall back to direct assignment for
        # normal FloatProperty fields like GravityScale and JumpZVelocity.
        if _write_attribute_struct(current, value):
            return True
        setattr(obj, name, float(value))
        return True
    except Exception:
        pass
    return False


def _call_setter(obj: Any, name: str, value: float) -> bool:
    try:
        fn = getattr(obj, name, None)
        if callable(fn):
            fn(float(value))
            return True
    except Exception:
        pass
    return False


def _apply_speed_to_obj(obj: Any, speed_scale: float, walk_speed: float) -> int:
    changed = 0
    # Native setters first when present.
    for meth in (
        "SetPawnMovementSpeedScale",
        "SetMovementSpeedScale",
        "SetMoveSpeedScale",
        "SetSpeedScale",
        "ServerSetPawnMovementSpeedScale",
        "ServerSetMovementSpeedScale",
    ):
        if _call_setter(obj, meth, speed_scale):
            changed += 1
    for attr in _SPEED_ATTRIBUTE_FIELDS:
        if _set_attr(obj, attr, speed_scale):
            changed += 1
    # BL4 appears to obey MinAnalogWalkSpeed more consistently than some of the
    # usual MaxWalkSpeed-style names, so keep it in the core absolute speed pass.
    for attr in _SPEED_FLOAT_FIELDS:
        if _set_attr(obj, attr, walk_speed):
            changed += 1
    accel = max(2048.0, min(64000.0, float(walk_speed) * 3.0))
    brake = max(2048.0, min(64000.0, float(walk_speed) * 2.0))
    for attr in _ACCEL_FIELDS:
        val = accel if "Acceleration" in attr else brake
        if _set_attr(obj, attr, val):
            changed += 1
    return changed


_JUMP_GOAL_DEF_WRITE_FIELDS = (
    "GoalHeight",
    "InitialZVelocity",
    "bUseGoalHeight",
    "bUseInitialZVelocity",
    "bClearGravityScaleAtApex",
)


def _looks_like_jump_goal_def(obj: Any) -> bool:
    if obj is None:
        return False
    for field in _JUMP_GOAL_DEF_WRITE_FIELDS:
        try:
            if hasattr(obj, field):
                return True
        except Exception:
            pass
    return False


def _jump_goal_def_targets(defptr: Any, depth: int = 0) -> list[Any]:
    """Return concrete JumpGoalDef-like targets from SDK 02/03 wrapper shapes.

    Older builds exposed GetJumpGoalForJumpType results through FGbxDefPtr.instance.
    SDK 03 can hand back a direct reflected object or a differently wrapped struct,
    so do not require the .instance attribute before trying to write the live def.
    """
    if defptr is None or depth > 3:
        return []
    out: list[Any] = []
    seen: set[int] = set()

    def add(obj: Any | None) -> None:
        if obj is None:
            return
        try:
            key = id(obj)
        except Exception:
            key = len(seen) + 1
        if key in seen:
            return
        seen.add(key)
        if _looks_like_jump_goal_def(obj):
            out.append(obj)

    add(defptr)
    for attr in (
        "instance",
        "Instance",
        "resolved",
        "Resolved",
        "object",
        "Object",
        "value",
        "Value",
        "Def",
        "Data",
    ):
        try:
            child = getattr(defptr, attr, None)
        except Exception:
            child = None
        add(child)
        for nested in _jump_goal_def_targets(child, depth + 1):
            add(nested)
    for method_name in ("get", "Get", "resolve", "Resolve", "GetObject", "get_object"):
        try:
            method = getattr(defptr, method_name, None)
            child = method() if callable(method) else None
        except Exception:
            child = None
        add(child)
        for nested in _jump_goal_def_targets(child, depth + 1):
            add(nested)
    return out


def _write_jump_goal_def_instance(
    defptr: Any,
    goal_height: float,
    initial_z_velocity: float,
    *,
    use_goal_height: bool = True,
    use_initial_z_velocity: bool = False,
    clear_gravity_at_apex: bool = False,
) -> int:
    """Mutate a live JumpGoalDef from either FGbxDefPtr or direct SDK 03 objects."""
    if defptr is None:
        return 0
    try:
        if hasattr(defptr, "valid") and not bool(getattr(defptr, "valid")):
            return 0
    except Exception:
        pass
    wrote = 0
    for target in _jump_goal_def_targets(defptr):
        wrote_target = 0
        for field, value in (
            ("GoalHeight", float(goal_height)),
            ("InitialZVelocity", float(initial_z_velocity)),
            ("bUseGoalHeight", bool(use_goal_height)),
            ("bUseInitialZVelocity", bool(use_initial_z_velocity)),
            ("bClearGravityScaleAtApex", bool(clear_gravity_at_apex)),
        ):
            try:
                setattr(target, field, value)
                wrote += 1
                wrote_target += 1
            except Exception:
                pass
        if wrote_target:
            try:
                _log(f"JumpGoalDef write target={target} fields={wrote_target} goal={float(goal_height):.0f} z={float(initial_z_velocity):.0f}")
            except Exception:
                pass
    return wrote


def _clone_jump_type_with_tag(template: Any, tag_name: str) -> Any | None:
    """Return a wrapped GameplayTag shaped like CurrentJump.JumpType.

    GbxCharacterMovementComponent.GetJumpGoalForJumpType requires the same
    wrapped struct type as CurrentJump.JumpType.  Passing a string crashes with
    a C++ cast error, so build/copy a real tag struct and verify the tag stuck.
    """
    def _looks_right(obj: Any) -> bool:
        try:
            return tag_name in str(obj)
        except Exception:
            return False

    # First clone the live struct because this preserves the exact wrapped type.
    for copier in (
        lambda x: x.__copy__(),
        lambda x: x.__deepcopy__({}),
    ):
        try:
            jt = copier(template) if template is not None else None
        except Exception:
            jt = None
        if jt is None:
            continue
        for field in ("TagName", "tagname", "Tag", "Name"):
            try:
                setter = getattr(jt, "_set_field", None)
                if callable(setter):
                    setter(field, tag_name)
                    if _looks_right(jt):
                        return jt
            except Exception:
                pass
            try:
                setattr(jt, field, tag_name)
                if _looks_right(jt):
                    return jt
            except Exception:
                pass

    # Build from the reflected struct type if exposed.
    type_candidates: list[Any] = []
    try:
        t = getattr(template, "_type", None)
        if t is not None:
            type_candidates.append(t)
            type_candidates.append(str(t))
    except Exception:
        pass
    type_candidates.extend(("GameplayTag", "GbxGameplayTag", "GameTag", "Tag"))
    for struct_name in type_candidates:
        for kwargs in (
            {"TagName": tag_name},
            {"tagname": tag_name},
            {"Tag": tag_name},
            {"Name": tag_name},
        ):
            try:
                jt = unrealsdk.make_struct(struct_name, **kwargs)
                if _looks_right(jt):
                    return jt
            except Exception:
                pass
    return None


def _jump_goal_tag_candidates(current_jump_type: Any | None) -> list[tuple[str, str]]:
    """Known BL4 movement jump type tags and tuning bucket.

    These come from Nexus jump goal collections: default, sprint, slide,
    double, ladder, and water jumps are separate JumpGoalDefs.
    """
    candidates: list[tuple[str, str]] = []
    try:
        live_tag = str(getattr(current_jump_type, "TagName", "") or "")
        if live_tag:
            candidates.append((live_tag, "default"))
    except Exception:
        pass
    for tag, kind in (
        ("Movement.JumpType.DefaultJump", "default"),
        ("Movement.JumpType.SprintJump", "sprint"),
        ("Movement.JumpType.SlideJump", "slide"),
        ("Movement.JumpType.DoubleJump", "double"),
        ("Movement.JumpType.UpwardLadderJump", "ladder"),
        ("Movement.JumpType.JumpFromLadder", "ladder"),
        ("Movement.JumpType.JumpFromWater", "water"),
        # Defensive aliases for builds/modded collections that renamed tags.
        ("Movement.JumpType.Jump", "default"),
        ("Movement.JumpType.SprintingJump", "sprint"),
        ("Movement.JumpType.RunJump", "sprint"),
        ("Movement.JumpType.AirJump", "double"),
        ("Movement.JumpType.SecondJump", "double"),
        ("Movement.JumpType.LadderJump", "ladder"),
        ("Movement.JumpType.WaterJump", "water"),
    ):
        if all(existing != tag for existing, _ in candidates):
            candidates.append((tag, kind))
    return candidates


def _write_jump_goal_for_all_known_types(
    obj: Any,
    jump_goal: float,
    jump_velocity: float,
    sprint_jump_goal: float | None = None,
    double_jump_goal: float | None = None,
) -> int:
    """Patch every JumpGoalDef reachable from the active movement component.

    The reliable API is GetJumpGoalForJumpType(real GameplayTagStruct).  This
    function clones CurrentJump.JumpType into the known BL4 jump-type tags and
    edits the resolved FGbxDefPtr.instance for each goal.  As a fallback it also
    temporarily SetCurrentJumpType(tag) and edits CurrentJump.JumpGoal.
    """
    wrote = 0
    get_goal = getattr(obj, "GetJumpGoalForJumpType", None)
    set_type = getattr(obj, "SetCurrentJumpType", None)
    current_jump = None
    current_jump_type = None
    try:
        current_jump = getattr(obj, "CurrentJump", None)
        current_jump_type = getattr(current_jump, "JumpType", None)
    except Exception:
        current_jump = None
        current_jump_type = None
    if not callable(get_goal) and not callable(set_type):
        return 0

    def _goal_for_kind(kind: str) -> float:
        if kind == "sprint" or kind == "slide":
            return float(sprint_jump_goal if sprint_jump_goal is not None else jump_goal)
        if kind == "double":
            return float(double_jump_goal if double_jump_goal is not None else (sprint_jump_goal if sprint_jump_goal is not None else jump_goal))
        # Ladder/water use normal jump height unless the user later wants separate sliders.
        return float(jump_goal)

    seen_defs: set[int] = set()
    built_tags: list[tuple[str, str, Any]] = []
    for tag_name, kind in _jump_goal_tag_candidates(current_jump_type):
        jt = _clone_jump_type_with_tag(current_jump_type, tag_name)
        if jt is not None:
            built_tags.append((tag_name, kind, jt))

    for tag_name, kind, jt in built_tags:
        goal_def = None
        if callable(get_goal):
            try:
                goal_def = get_goal(jt)
            except Exception as ex:
                try:
                    _log(f"JumpGoal lookup skipped {tag_name}: {ex}")
                except Exception:
                    pass
                goal_def = None
        if goal_def is None and callable(set_type):
            try:
                set_type(jt)
                cj = getattr(obj, "CurrentJump", None)
                goal_def = getattr(cj, "JumpGoal", None)
            except Exception:
                goal_def = None
        if goal_def is None:
            continue
        try:
            key = int(getattr(goal_def, "instance_address", 0) or getattr(goal_def, "ref_address", 0) or id(goal_def))
        except Exception:
            key = id(goal_def)
        if key in seen_defs:
            continue
        seen_defs.add(key)
        goal = _goal_for_kind(kind)
        before = str(goal_def)
        wrote_now = _write_jump_goal_def_instance(goal_def, goal, jump_velocity)
        wrote += wrote_now
        if wrote_now:
            try:
                _log(f"JumpGoalDef patched {tag_name}: goal={goal:.0f}, z={float(jump_velocity):.0f}, def={before}")
            except Exception:
                pass

    # Restore the original current jump type if we changed it during fallback probing.
    if callable(set_type) and current_jump_type is not None:
        try:
            set_type(current_jump_type)
        except Exception:
            pass
    return wrote


def _write_current_jump_goal_def(obj: Any, jump_goal: float, jump_velocity: float, sprint_jump_goal: float | None = None, double_jump_goal: float | None = None) -> int:
    """Patch CurrentJump.JumpGoal.instance plus all getter-resolved jump goal defs."""
    wrote = 0
    current_jump = None
    try:
        current_jump = getattr(obj, "CurrentJump", None)
    except Exception:
        current_jump = None
    if current_jump is not None:
        try:
            wrote += _write_jump_goal_def_instance(getattr(current_jump, "JumpGoal", None), jump_goal, jump_velocity)
        except Exception:
            pass
    try:
        get_type = getattr(obj, "GetCurrentJumpType", None)
        get_goal = getattr(obj, "GetJumpGoalForJumpType", None)
        if callable(get_type) and callable(get_goal):
            jt = get_type()
            try:
                goal_def = get_goal(jt)
                wrote += _write_jump_goal_def_instance(goal_def, jump_goal, jump_velocity)
            except Exception:
                pass
    except Exception:
        pass
    wrote += _write_jump_goal_for_all_known_types(obj, jump_goal, jump_velocity, sprint_jump_goal, double_jump_goal)
    return wrote

def _write_scalar_or_vector_value(target: Any, value: float) -> bool:
    """Write a scalar-ish value without replacing native structs when possible."""
    if target is None:
        return False
    wrote = False
    # GbxAttributeFloat / wrapped structs.
    if _write_attribute_struct(target, value):
        wrote = True
    # JumpGoal has shown up as a movement-component field for BL4 testing; on
    # some builds it behaves like a vector/struct rather than a plain float.  In
    # that case we want jump height on Z while leaving X/Y alone.
    for field in ("Z", "z", "Value", "BaseValue", "CurrentValue", "Goal", "Height", "JumpHeight", "TargetHeight"):
        try:
            setattr(target, field, float(value))
            wrote = True
        except Exception:
            pass
    for method_name in ("Set", "SetValue", "SetBaseValue", "SetCurrentValue", "SetGoal", "SetHeight"):
        try:
            method = getattr(target, method_name, None)
            if callable(method):
                # Most pyunrealsdk wrapped setters here take one scalar.
                method(float(value))
                wrote = True
        except Exception:
            pass
    return wrote


def _set_jump_goal_field(obj: Any, value: float) -> bool:
    """Set BL4 CharMoveComp JumpGoal, including nested/vector variants.

    The important path is the live movement component (CharMoveComp /
    OakCharacterMovementComponent).  Earlier builds wrote Pawn.JumpGoal and
    JumpZVelocity fallbacks, but missed cases where JumpGoal is a native field
    or nested struct on the movement component.
    """
    wrote = False
    for attr in (
        "JumpGoal",
        "jumpGoal",
        "jump_goal",
        "JumpHeightGoal",
        "TargetJumpHeight",
    ):
        try:
            current = getattr(obj, attr)
        except Exception:
            current = None
        if current is not None:
            if _write_scalar_or_vector_value(current, value):
                wrote = True
            try:
                setattr(obj, attr, float(value))
                wrote = True
            except Exception:
                # Struct/vector fields may reject replacement; field mutation above
                # is the safer path.
                pass
    # Some movement builds expose active jump info under CurrentJump / JumpData.
    # Probe those containers but keep the writes narrow to jump-goal-ish fields.
    for container_name in (
        "CurrentJump",
        "JumpDetails",
        "JumpData",
        "JumpState",
        "PlayerJumpState",
        "VaultJumpState",
    ):
        try:
            container = getattr(obj, container_name)
        except Exception:
            container = None
        if container is None:
            continue
        if _write_scalar_or_vector_value(container, value):
            # Only count this as a write if the container clearly is jump details.
            wrote = True
        for field in (
            "JumpGoal",
            "Goal",
            "Height",
            "JumpHeight",
            "TargetHeight",
            "GoalHeight",
            "GoalZ",
            "TargetZ",
            "Z",
        ):
            try:
                sub = getattr(container, field)
            except Exception:
                sub = None
            if sub is not None and _write_scalar_or_vector_value(sub, value):
                wrote = True
            try:
                setattr(container, field, float(value))
                wrote = True
            except Exception:
                pass
    return wrote


def _write_jump_detail_struct(target: Any, jump_goal: float, jump_velocity: float, sprint_jump_goal: float | None = None) -> int:
    """Best-effort writer for BL4 JumpDetails/JumpGoal-style structs.

    BL4's reflected GbxCharacterMovementComponent exposes CurrentJump plus
    JumpGoal collection helpers.  Simple JumpZVelocity writes can be ignored
    because the active jump is resolved from JumpDetails.  This writer keeps the
    names broad but only touches jump-height/velocity-looking fields.
    """
    if target is None:
        return 0
    wrote = 0
    goal = float(jump_goal)
    sprint_goal = float(sprint_jump_goal if sprint_jump_goal is not None else jump_goal)
    vel = float(jump_velocity)
    for field, value in (
        ("JumpGoal", goal),
        ("Goal", goal),
        ("GoalHeight", goal),
        ("TargetHeight", goal),
        ("TargetJumpHeight", goal),
        ("JumpHeight", goal),
        ("Height", goal),
        ("GoalZ", goal),
        ("TargetZ", goal),
        ("Z", goal),
        ("SprintJumpGoal", sprint_goal),
        ("SprintGoal", sprint_goal),
        ("SprintGoalHeight", sprint_goal),
        ("SprintJumpHeight", sprint_goal),
        ("JumpZVelocity", vel),
        ("JumpVelocity", vel),
        ("ZVelocity", vel),
        ("UpVelocity", vel),
        ("InitialVelocity", vel),
        ("LaunchVelocity", vel),
    ):
        try:
            sub = getattr(target, field)
        except Exception:
            sub = None
        if sub is not None and _write_scalar_or_vector_value(sub, value):
            wrote += 1
        try:
            setattr(target, field, float(value))
            wrote += 1
        except Exception:
            pass
    return wrote


def _refresh_jump_runtime_state(obj: Any) -> int:
    """Reset counters / ping native replication callbacks after jump writes."""
    changed = 0
    for attr, value in (
        ("JumpedCount", 0),
        ("JumpCurrentCount", 0),
        ("JumpCurrentCountPreJump", 0),
    ):
        if _set_int_attr(obj, attr, int(value)):
            changed += 1
    for meth in ("OnRep_CurrentJump", "OnRep_bRepInDelayedFall", "ForceReplicationUpdate", "ForceNetUpdate"):
        try:
            fn = getattr(obj, meth, None)
            if callable(fn):
                fn()
                changed += 1
        except Exception:
            pass
    return changed


def _jump_goal_tuple(height: float, z: float | None = None, *, vanilla: dict[str, float | bool] | None = None) -> tuple[float, float, bool, bool, bool]:
    if vanilla is not None:
        return (
            float(vanilla.get("height", height)),
            float(vanilla.get("z", z if z is not None else height)),
            bool(vanilla.get("use_h", True)),
            bool(vanilla.get("use_z", False)),
            bool(vanilla.get("clear_apex", False)),
        )
    # Custom edited jumps should obey the chosen GoalHeight, so disable the
    # vanilla sprint/double InitialZ-only behavior and keep GoalHeight authoritative.
    return float(height), float(z if z is not None else height), True, False, False


def _force_write_jump_states(
    obj: Any,
    *,
    default_goal: float,
    sprint_goal: float | None = None,
    double_goal: float | None = None,
    slide_goal: float | None = None,
    jump_velocity: float | None = None,
    reset_defaults: bool = False,
) -> int:
    """Force Default/Sprint/Double/Slide CurrentJump states once, write their JumpGoalDef, then restore.

    This is the no-watcher path: it does all work during Apply/Reset and leaves
    gameplay idle silent afterward.
    """
    set_type = getattr(obj, "SetCurrentJumpType", None)
    if not callable(set_type):
        return 0
    try:
        current_jump = getattr(obj, "CurrentJump", None)
        current_type = getattr(current_jump, "JumpType", None)
    except Exception:
        current_jump = None
        current_type = None
    if current_type is None:
        return 0
    goals = {
        "default": float(default_goal),
        "sprint": float(sprint_goal if sprint_goal is not None else default_goal),
        "double": float(double_goal if double_goal is not None else (sprint_goal if sprint_goal is not None else default_goal)),
        "slide": float(slide_goal if slide_goal is not None else (sprint_goal if sprint_goal is not None else default_goal)),
    }
    wrote = 0
    for kind, tag in _JUMP_FORCE_TAGS:
        jt = _clone_jump_type_with_tag(current_type, tag)
        if jt is None:
            continue
        try:
            set_type(jt)
            cj = getattr(obj, "CurrentJump", None)
            goal_def = getattr(cj, "JumpGoal", None) if cj is not None else None
        except Exception:
            goal_def = None
        if goal_def is None:
            continue
        if reset_defaults:
            h, z, use_h, use_z, clear_apex = _jump_goal_tuple(goals[kind], None, vanilla=_JUMP_DEFAULTS.get(kind))
        else:
            h = goals[kind]
            z = float(jump_velocity if jump_velocity is not None else h)
            h, z, use_h, use_z, clear_apex = _jump_goal_tuple(h, z)
        wrote += _write_jump_goal_def_instance(
            goal_def, h, z,
            use_goal_height=use_h,
            use_initial_z_velocity=use_z,
            clear_gravity_at_apex=clear_apex,
        )
    try:
        set_type(current_type)
    except Exception:
        pass
    return wrote


def _apply_jump_to_obj(
    obj: Any,
    jump_goal: float,
    jump_velocity: float,
    sprint_jump_goal: float | None = None,
    jump_hold_time: float | None = None,
    double_jump_goal: float | None = None,
    slide_jump_goal: float | None = None,
    reset_jump_defaults: bool = False,
) -> int:
    changed = 0
    changed += _force_write_jump_states(
        obj,
        default_goal=float(jump_goal),
        sprint_goal=sprint_jump_goal,
        double_goal=double_jump_goal,
        slide_goal=slide_jump_goal,
        jump_velocity=jump_velocity,
        reset_defaults=reset_jump_defaults,
    )
    # Narrow fallback: if this object is already in a current jump state but does
    # not expose SetCurrentJumpType, patch only the active CurrentJump.JumpGoal.
    try:
        cj = getattr(obj, "CurrentJump", None)
        gd = getattr(cj, "JumpGoal", None) if cj is not None else None
        if gd is not None:
            changed += _write_jump_goal_def_instance(
                gd, float(jump_goal), float(jump_velocity),
                use_goal_height=True,
                use_initial_z_velocity=False,
                clear_gravity_at_apex=False,
            )
    except Exception:
        pass
    if jump_hold_time is not None:
        for attr in ("JumpMaxHoldTime", "JumpHoldTime", "MaxJumpHoldTime"):
            if _set_attr(obj, attr, max(0.0, float(jump_hold_time))):
                changed += 1
    return changed


def apply_movement_to_all_players(speed_scale: float, walk_speed: float, jump_goal: float, jump_velocity: float) -> str:
    """Apply movement values to all live player controllers/pawns/components.

    Returns a user-visible summary.  The game may only replicate properties which
    are replicated by the native classes; this function deliberately applies on
    server-side live objects when run by the host.
    """
    speed_scale = max(0.05, min(25.0, float(speed_scale)))
    walk_speed = max(50.0, min(10000.0, float(walk_speed)))
    jump_goal = max(0.0, min(10000.0, float(jump_goal)))
    jump_velocity = max(0.0, min(10000.0, float(jump_velocity)))

    controllers = live_player_controllers()
    pawns = live_player_pawns()
    touched = 0
    writes = 0
    jump_writes = 0

    for pc in controllers:
        speed_w = _apply_speed_to_obj(pc, speed_scale, walk_speed)
        jump_w = _apply_jump_to_obj(pc, jump_goal, jump_velocity)
        c = speed_w + jump_w
        if c:
            touched += 1
            writes += c
            jump_writes += jump_w
    for pawn in pawns:
        pawn_writes = 0
        pawn_jump_writes = 0
        for obj in _movement_objects_for_pawn(pawn):
            pawn_writes += _apply_speed_to_obj(obj, speed_scale, walk_speed)
            jump_w = _apply_jump_to_obj(obj, jump_goal, jump_velocity)
            pawn_writes += jump_w
            pawn_jump_writes += jump_w
        if pawn_writes:
            touched += 1
            writes += pawn_writes
            jump_writes += pawn_jump_writes
    msg = f"Applied movement to {len(pawns)} player pawn(s), {len(controllers)} controller(s): speed {speed_scale:.2f}x, walk {walk_speed:.0f}, JumpGoal {jump_goal:.0f}, JumpZ {jump_velocity:.0f}. Writes: {writes}; jump writes: {jump_writes}."
    _log(msg)
    return msg


def reset_movement_all_players() -> str:
    return apply_movement_to_all_players(1.0, 600.0, 420.0, 420.0)


# --- Extended movement / utility helpers (UI-driven; no keybinds) ---

def _all_movement_objects() -> list[Any]:
    objs: list[Any] = []
    for pawn in live_player_pawns():
        objs.extend(_movement_objects_for_pawn(pawn))
    return _unique_live_objects(objs)


def _set_int_attr(obj: Any, name: str, value: int) -> bool:
    try:
        if not hasattr(obj, name):
            return False
        current = getattr(obj, name, None)
        wrote = False
        for field in ("Value", "BaseValue", "CurrentValue", "Base", "Current"):
            try:
                setattr(current, field, int(value))
                wrote = True
            except Exception:
                pass
        for method_name in ("SetValue", "SetBaseValue", "SetCurrentValue"):
            try:
                method = getattr(current, method_name, None)
                if callable(method):
                    method(int(value))
                    wrote = True
            except Exception:
                pass
        if wrote:
            return True
        setattr(obj, name, int(value))
        return True
    except Exception:
        pass
    return False


def _apply_advanced_to_obj(
    obj: Any,
    *,
    gravity_scale: float,
    max_step_height: float,
    jump_count: int,
    jump_off_z_factor: float,
    walkable_floor_angle: float,
    walkable_floor_z: float,
    sprint_jump_goal: float | None = None,
    jump_hold_time: float | None = None,
    glide_speed: float = 2600.0,
    glide_boost: float = 4200.0,
    glide_air_control: float = 6.0,
    dash_speed: float = 3000.0,
    vault_cost: float | None = None,
    sections: set[str] | None = None,
) -> int:
    changed = 0
    sections = set(sections or ("gravity", "wall", "glide", "vault", "jump_count"))
    if "gravity" in sections:
        if _set_attr(obj, "GravityScale", gravity_scale):
            changed += 1
    if "wall" in sections:
        for attr, value in (
            ("MaxStepHeight", max_step_height),
            ("JumpOffJumpZFactor", jump_off_z_factor),
            ("WalkableFloorAngle", walkable_floor_angle),
            ("WalkableFloorZ", walkable_floor_z),
        ):
            if _set_attr(obj, attr, value):
                changed += 1
        for meth, value in (("SetWalkableFloorAngle", walkable_floor_angle), ("SetWalkableFloorZ", walkable_floor_z)):
            try:
                fn = getattr(obj, meth, None)
                if callable(fn):
                    fn(value); changed += 1
            except Exception:
                pass
    if "glide" in sections:
        for attr, value in (
            ("AirControl", glide_air_control),
            ("AirControlBoostMultiplier", max(1.0, glide_air_control)),
            ("FallingLateralFriction", 0.0),
            ("GroundFriction", 8.0),
            ("GlidingSpeed", glide_speed),
            ("GlidingSpeedBoost", glide_boost),
            ("GlidingAirControl", glide_air_control),
            ("GlidingAcceleration", 400.0 if glide_speed <= 1200.0 else max(glide_speed * 2.0, 5000.0)),
            ("GlidingDeceleration", 400.0 if glide_speed <= 1200.0 else max(glide_speed * 0.6, 1600.0)),
            ("DashSpeed", dash_speed),
            ("MaxDashSpeed", dash_speed),
            ("DashInitialSpeed", dash_speed),
            ("DashLaunchSpeed", dash_speed),
            ("DashImpulse", dash_speed),
            ("AirDashSpeed", dash_speed),
        ):
            if _set_attr(obj, attr, value):
                changed += 1
    if "vault" in sections and vault_cost is not None:
        for attr in _VAULT_COST_FIELDS:
            if _set_attr(obj, attr, max(0.0, float(vault_cost))):
                changed += 1
    if "jump_count" in sections:
        if _set_int_attr(obj, "JumpMaxCount", jump_count):
            changed += 1
        try:
            fn = getattr(obj, "SetJumpMaxCount", None)
            if callable(fn):
                fn(jump_count); changed += 1
        except Exception:
            pass
    return changed

def apply_movement_advanced_to_all_players(
    speed_scale: float,
    walk_speed: float,
    jump_goal: float,
    jump_velocity: float,
    gravity_scale: float,
    max_step_height: float,
    jump_count: int,
    jump_off_z_factor: float,
    walkable_floor_angle: float,
    walkable_floor_z: float,
    sprint_jump_goal: float | None = None,
    jump_hold_time: float | None = None,
    glide_speed: float = 2600.0,
    glide_boost: float = 4200.0,
    glide_air_control: float = 6.0,
    dash_speed: float = 3000.0,
    vault_cost: float | None = None,
    *,
    double_jump_goal: float | None = None,
    slide_jump_goal: float | None = None,
    sections: set[str] | None = None,
    reset_jump_defaults: bool = False,
    scope: str = "all",
) -> str:
    if not _is_listen_host_safe():
        msg = "Client mode — movement apply skipped until you are host."
        _log(msg)
        return msg
    speed_scale = max(0.05, min(25.0, float(speed_scale)))
    walk_speed = max(50.0, min(10000.0, float(walk_speed)))
    jump_goal = max(0.0, min(10000.0, float(jump_goal)))
    jump_velocity = max(0.0, min(10000.0, float(jump_velocity)))
    gravity_scale = max(0.0, min(10.0, float(gravity_scale)))
    max_step_height = max(0.0, min(1000.0, float(max_step_height)))
    jump_count = max(1, min(50, int(jump_count)))
    jump_off_z_factor = max(0.0, min(80.0, float(jump_off_z_factor)))
    sprint_jump_goal = max(0.0, min(20000.0, float(sprint_jump_goal if sprint_jump_goal is not None else jump_goal)))
    double_jump_goal = max(0.0, min(20000.0, float(double_jump_goal if double_jump_goal is not None else sprint_jump_goal)))
    slide_jump_goal = max(0.0, min(20000.0, float(slide_jump_goal if slide_jump_goal is not None else sprint_jump_goal)))
    jump_hold_time = max(0.0, min(8.0, float(jump_hold_time if jump_hold_time is not None else 0.0)))
    sections = set(sections or ("speed", "jump", "gravity", "wall", "glide", "vault", "jump_count"))
    walkable_floor_angle = max(0.0, min(89.9, float(walkable_floor_angle)))
    walkable_floor_z = max(0.0, min(1.0, float(walkable_floor_z)))
    glide_speed = max(0.0, min(30000.0, float(glide_speed)))
    glide_boost = max(0.0, min(30000.0, float(glide_boost)))
    glide_air_control = max(0.0, min(50.0, float(glide_air_control)))
    dash_speed = max(0.0, min(30000.0, float(dash_speed)))
    if vault_cost is not None:
        vault_cost = max(0.0, min(500.0, float(vault_cost)))

    controllers = filter_controllers_by_scope(live_player_controllers(), scope)
    pawns = filter_pawns_by_scope(live_player_pawns(), scope)
    writes = 0
    touched = 0
    jump_writes = 0
    for pc in controllers:
        c = 0
        if "speed" in sections:
            c += _apply_speed_to_obj(pc, speed_scale, walk_speed)
        if "jump" in sections:
            jump_w = _apply_jump_to_obj(pc, jump_goal, jump_velocity, sprint_jump_goal, jump_hold_time, double_jump_goal, slide_jump_goal, reset_jump_defaults)
            c += jump_w
            jump_writes += jump_w
        if sections.intersection({"gravity", "wall", "glide", "vault", "jump_count"}):
            c += _apply_advanced_to_obj(pc, gravity_scale=gravity_scale, max_step_height=max_step_height, jump_count=jump_count, jump_off_z_factor=jump_off_z_factor, walkable_floor_angle=walkable_floor_angle, walkable_floor_z=walkable_floor_z, glide_speed=glide_speed, glide_boost=glide_boost, glide_air_control=glide_air_control, dash_speed=dash_speed, vault_cost=vault_cost, sections=sections)
        if c:
            touched += 1; writes += c
    for pawn in pawns:
        pawn_writes = 0
        pawn_jump_writes = 0
        for obj in _movement_objects_for_pawn(pawn):
            if "speed" in sections:
                pawn_writes += _apply_speed_to_obj(obj, speed_scale, walk_speed)
            if "jump" in sections:
                jump_w = _apply_jump_to_obj(obj, jump_goal, jump_velocity, sprint_jump_goal, jump_hold_time, double_jump_goal, slide_jump_goal, reset_jump_defaults)
                pawn_writes += jump_w
                pawn_jump_writes += jump_w
            if sections.intersection({"gravity", "wall", "glide", "vault", "jump_count"}):
                pawn_writes += _apply_advanced_to_obj(obj, gravity_scale=gravity_scale, max_step_height=max_step_height, jump_count=jump_count, jump_off_z_factor=jump_off_z_factor, walkable_floor_angle=walkable_floor_angle, walkable_floor_z=walkable_floor_z, glide_speed=glide_speed, glide_boost=glide_boost, glide_air_control=glide_air_control, dash_speed=dash_speed, vault_cost=vault_cost, sections=sections)
        if pawn_writes:
            touched += 1; writes += pawn_writes
            jump_writes += pawn_jump_writes
    scope_key = str(scope or "all").strip().lower() or "all"
    msg = (
        f"Applied movement (scope={scope_key}) to {len(pawns)} player pawn(s), "
        f"{len(controllers)} controller(s): speed {speed_scale:.2f}x, walk {walk_speed:.0f}, "
        f"JumpGoal {jump_goal:.0f}, JumpZ {jump_velocity:.0f}, jump count {jump_count}, "
        f"gravity {gravity_scale:.2f}, step {max_step_height:.0f}, floor angle {walkable_floor_angle:.1f}, "
        f"glide {glide_speed:.0f}/{glide_boost:.0f}, vault cost {'unchanged' if vault_cost is None else vault_cost}. "
        f"Writes: {writes}; jump writes: {jump_writes}."
    )
    _log(msg)
    if _INFINITE_JUMP_INDICES:
        try:
            reapply_infinite_jump_on_enabled()
            msg += " Infinite Jump re-applied."
        except Exception:
            pass
    return msg


def reset_movement_advanced_all_players() -> str:
    return apply_movement_advanced_to_all_players(
        1.0, 600.0, 198.0, 840.0, 1.0, 45.0, 2, 0.5,
        44.76508331298828, 0.7099999785423279,
        198.0, 0.0, 1200.0, 0.0, 0.6000000238418579, 2500.0, None,
        double_jump_goal=225.0, slide_jump_goal=198.0,
        sections={"speed", "jump", "gravity", "wall", "glide", "vault", "jump_count"},
        reset_jump_defaults=True,
    )

def zero_vault_power_costs_all_players() -> str:
    if not _is_listen_host_safe():
        msg = "Client mode — vault cost write skipped until you are host."
        _log(msg)
        return msg
    pawns = live_player_pawns()
    writes = 0
    for pawn in pawns:
        for obj in _movement_objects_for_pawn(pawn):
            for attr in _VAULT_COST_FIELDS:
                if _set_attr(obj, attr, 0.0):
                    writes += 1
    msg = f"Set vault traversal costs to 0 on {len(pawns)} pawn(s). Writes: {writes}."
    _log(msg)
    return msg



def _movement_obj_is_falling(obj: Any) -> bool:
    for meth in ("IsFalling", "IsFlying"):
        try:
            fn = getattr(obj, meth, None)
            if callable(fn):
                return bool(fn())
        except Exception:
            pass
    try:
        mode = getattr(obj, "MovementMode", None) or getattr(obj, "ReplicatedMovementMode", None)
        # Unreal MOVE_Falling is commonly 3.  Keep this as a weak fallback only.
        if int(mode) == 3:
            return True
    except Exception:
        pass
    return False


_JUMP_REFRESH_OBJECT_CACHE: list[Any] = []  # unused; kept empty — never cache UObjects
_JUMP_REFRESH_CACHE_TIME: float = 0.0


def _gentle_jump_refresh_objects() -> list[Any]:
    """Fresh movement objects for the experimental multi-jump refresher.

    Do not cache UObject wrappers across calls — travel/respawn leaves stale
    pointers that ACCESS_VIOLATE inside pyunrealsdk (Tobgun1).
    """
    global _JUMP_REFRESH_OBJECT_CACHE, _JUMP_REFRESH_CACHE_TIME
    try:
        objects = _all_movement_objects()
    except Exception:
        objects = []
    _JUMP_REFRESH_OBJECT_CACHE = []
    _JUMP_REFRESH_CACHE_TIME = time.monotonic()
    return objects


def refresh_jump_counts_all_players() -> str:
    if not _is_listen_host_safe():
        msg = "Client mode — jump refresh skipped until you are host."
        _log(msg)
        return msg
    """Gentle experimental multi-jump support.

    Clears live jump counters and transient pressed/jumping flags. Callers must
    throttle; this path always re-resolves movement objects.
    """
    objects = _gentle_jump_refresh_objects()
    writes = 0
    for obj in objects:
        for attr in (
            "JumpedCount",
            "JumpCurrentCount",
            "JumpCurrentCountPreJump",
            "CurrentJumpCount",
            "CurrentJumpCountPreJump",
        ):
            try:
                if _set_int_attr(obj, attr, 0):
                    writes += 1
            except Exception:
                pass
        for attr in ("bPressedJump", "bWasJumping", "bProxyIsJumpForceApplied"):
            try:
                if hasattr(obj, attr):
                    setattr(obj, attr, False)
                    writes += 1
            except Exception:
                pass
    return f"Gentle jump refresh cleared counters on {len(objects)} movement object(s). Writes: {writes}."


def _infinite_jump_move_for_pawn(pawn: Any) -> Any | None:
    if pawn is None:
        return None
    for attr in ("OakCharacterMovement", "CharacterMovement", "GbxCharacterMovement", "MovementComponent", "PawnMovement", "Movement"):
        try:
            move = getattr(pawn, attr, None)
            if move is not None and not _is_default(move):
                return move
        except Exception:
            pass
    for meth in ("GetMovementComponent", "GetCharacterMovement"):
        move = _call0(pawn, meth)
        if move is not None and not _is_default(move):
            return move
    return None


def _set_if_needed(obj: Any, attr: str, value: Any) -> bool:
    """Write an int/bool jump field. Do not require hasattr — unrealsdk wrappers lie."""
    if obj is None:
        return False
    try:
        current = getattr(obj, attr, None)
        if current == value:
            return False
    except Exception:
        current = None
    try:
        setattr(obj, attr, value)
        return True
    except Exception:
        return False


def _jump_counters_spent(obj: Any) -> bool:
    """True when jump spend/max on this object still blocks another jump."""
    if obj is None:
        return False
    for attr in (
        "JumpCurrentCount",
        "JumpCurrentCountPreJump",
        "JumpedCount",
        "CurrentJumpCount",
        "CurrentJumpCountPreJump",
    ):
        try:
            cur = getattr(obj, attr, None)
            if cur is not None and int(cur) > 0:
                return True
        except Exception:
            continue
    try:
        max_c = getattr(obj, "JumpMaxCount", None)
        if max_c is None or int(max_c) < 999:
            return True
    except Exception:
        return True
    return False


def _infinite_jump_needs_light_refresh(pawn: Any) -> bool:
    """Spend/threshold check on pawn AND movement component (BL4 spends on CharMoveComp)."""
    if pawn is None or not _uobject_alive(pawn):
        return False
    if _jump_counters_spent(pawn):
        return True
    move = _infinite_jump_move_for_pawn(pawn)
    return bool(move is not None and _jump_counters_spent(move))


def _force_infinite_jump_ready(pawn: Any, move: Any | None = None, *, light: bool = False) -> bool:
    # Hot path: address-only liveness. Avoid str()/CDO probes every camera tick.
    if pawn is None or not _uobject_alive(pawn):
        return False
    if light and not _infinite_jump_needs_light_refresh(pawn):
        return False
    try:
        move = move if (move is not None and _uobject_alive(move)) else None
        if move is None:
            move = _infinite_jump_move_for_pawn(pawn)
            if move is not None and not _uobject_alive(move):
                move = None
    except Exception:
        move = None
    changed = False
    # light=True (camera tick): only open JumpMaxCount and clear spent counters.
    # Full prep (Jump/CanJump) also zeros alternate counter names used by BL4 builds.
    if light:
        pawn_attrs: tuple[tuple[str, Any], ...] = (
            ("JumpMaxCount", 999),
            ("JumpCurrentCount", 0),
            ("JumpCurrentCountPreJump", 0),
        )
        move_attrs = pawn_attrs
    else:
        pawn_attrs = (
            ("JumpMaxCount", 999),
            ("JumpCurrentCount", 0),
            ("JumpCurrentCountPreJump", 0),
            ("JumpedCount", 0),
            ("CurrentJumpCount", 0),
            ("CurrentJumpCountPreJump", 0),
        )
        move_attrs = (
            ("JumpMaxCount", 999),
            ("JumpCurrentCount", 0),
            ("JumpCurrentCountPreJump", 0),
            ("CurrentJumpCount", 0),
            ("CurrentJumpCountPreJump", 0),
        )

    def _apply(obj: Any, pairs: tuple[tuple[str, Any], ...]) -> None:
        nonlocal changed
        for attr, value in pairs:
            if light and attr in ("JumpCurrentCount", "JumpCurrentCountPreJump", "CurrentJumpCount", "CurrentJumpCountPreJump", "JumpedCount"):
                try:
                    cur = getattr(obj, attr, None)
                    if cur is None:
                        continue
                    if int(cur) <= 0:
                        continue
                except Exception:
                    continue
            if _set_if_needed(obj, attr, value):
                changed = True

    _apply(pawn, pawn_attrs)
    if move is not None:
        _apply(move, move_attrs)
    return changed


def _player_label_for_controller(idx: int, pc: Any | None) -> str:
    if pc is None or not _uobject_alive(pc):
        return f"P{int(idx) + 1}"
    try:
        ps = getattr(pc, "PlayerState", None)
        if ps is not None and _uobject_alive(ps):
            for attr in ("PlayerName", "SavedNetworkAddress", "Name"):
                value = getattr(ps, attr, None)
                if value:
                    return str(value)
    except Exception:
        pass
    return f"P{int(idx) + 1}"


def _clear_infinite_jump_runtime_caches() -> None:
    """Drop every long-lived UObject-adjacent cache used by Infinite Jump."""
    global _INFINITE_JUMP_LABEL_CACHE_TIME, _INFINITE_JUMP_CAMERA_LAST_APPLY
    global _INFINITE_JUMP_LAST_HEAVY_SCAN, _INFINITE_JUMP_WORLD_SIG, _INFINITE_JUMP_LOCAL_IDX
    global _JUMP_REFRESH_OBJECT_CACHE, _JUMP_REFRESH_CACHE_TIME
    _INFINITE_JUMP_LABEL_CACHE.clear()
    _INFINITE_JUMP_LABEL_CACHE_TIME = 0.0
    _INFINITE_JUMP_CAMERA_LAST_APPLY = 0.0
    _INFINITE_JUMP_LAST_HEAVY_SCAN = 0.0
    _INFINITE_JUMP_WORLD_SIG = None
    _INFINITE_JUMP_LOCAL_IDX = None
    _JUMP_REFRESH_OBJECT_CACHE = []
    _JUMP_REFRESH_CACHE_TIME = 0.0
    try:
        _disarm_fly_speed_override()
    except Exception:
        pass


def _world_from_pc(pc: Any) -> Any | None:
    if pc is None:
        return None
    for attr in ("World", "GetWorld"):
        try:
            val = getattr(pc, attr, None)
            world = val() if callable(val) else val
            if world is not None:
                return world
        except Exception:
            pass
    return None


def _infinite_jump_world_sig_from(pc: Any, pawn: Any | None = None) -> tuple[int, int, int, int]:
    """Cheap world/controller/pawn/player-state address signature (no find_all)."""
    world = None
    ps = None
    if pc is not None and _uobject_alive(pc):
        if pawn is None:
            try:
                pawn = pawn_for_controller(pc)
            except Exception:
                pawn = None
        try:
            ps = getattr(pc, "PlayerState", None)
        except Exception:
            ps = None
        world = _world_from_pc(pc)
    return (
        _uobject_addr(world),
        _uobject_addr(pc),
        _uobject_addr(pawn),
        _uobject_addr(ps),
    )


def _infinite_jump_world_sig() -> tuple[int, int, int, int]:
    try:
        pc = get_pc()
    except Exception:
        pc = None
    return _infinite_jump_world_sig_from(pc)


def _local_party_index(pc: Any) -> int:
    """Resolve local controller's PlayerArray index without find_all class scans."""
    if pc is None or not _uobject_alive(pc):
        return 0
    try:
        ps = getattr(pc, "PlayerState", None)
    except Exception:
        ps = None
    if ps is None or not _uobject_alive(ps):
        return 0
    world = None
    for attr in ("World", "GetWorld"):
        try:
            val = getattr(pc, attr, None)
            world = val() if callable(val) else val
            if world is not None:
                break
        except Exception:
            pass
    gs = None
    if world is not None and _uobject_alive(world):
        try:
            gs = getattr(world, "GameState", None) or getattr(world, "AuthorityGameMode", None)
        except Exception:
            gs = None
    pa = getattr(gs, "PlayerArray", None) if gs is not None else None
    if pa is None:
        return 0
    try:
        total = len(pa)
    except Exception:
        total = 0
    ps_addr = _uobject_addr(ps)
    for i in range(total):
        try:
            other = pa[i]
        except Exception:
            continue
        if other is ps or (_uobject_addr(other) and _uobject_addr(other) == ps_addr):
            return int(i)
    return 0


def _infinite_jump_contexts_light(pc: Any | None = None, pawn: Any | None = None) -> list[tuple[int, str, Any, Any | None]]:
    """Local resolve via get_pc only — no find_all (Tobgun FPS fix)."""
    global _INFINITE_JUMP_LOCAL_IDX
    contexts: list[tuple[int, str, Any, Any | None]] = []
    if pc is None:
        try:
            pc = get_pc()
        except Exception:
            pc = None
    if pc is None or not _uobject_alive(pc):
        return contexts
    if pawn is None:
        pawn = pawn_for_controller(pc)
    if pawn is None or not _uobject_alive(pawn):
        return contexts
    idx = _INFINITE_JUMP_LOCAL_IDX
    if idx is None:
        idx = _local_party_index(pc)
        _INFINITE_JUMP_LOCAL_IDX = int(idx)
    label = _INFINITE_JUMP_LABEL_CACHE.get(int(idx)) or _player_label_for_controller(idx, pc)
    _INFINITE_JUMP_LABEL_CACHE[int(idx)] = label
    contexts.append((int(idx), label, pawn, None))
    return contexts


def _infinite_jump_contexts_heavy(now: float) -> list[tuple[int, str, Any, Any | None]]:
    """Full controller + player-pawn discovery (expensive). Call rarely."""
    global _INFINITE_JUMP_LABEL_CACHE_TIME, _INFINITE_JUMP_LAST_HEAVY_SCAN, _INFINITE_JUMP_LOCAL_IDX
    contexts: list[tuple[int, str, Any, Any | None]] = []
    controllers = live_player_controllers()
    seen: set[int] = set()
    try:
        local_pc = get_pc()
    except Exception:
        local_pc = None
    local_pc_addr = _uobject_addr(local_pc)
    for idx, pc in enumerate(controllers):
        if pc is None or not _uobject_alive(pc):
            continue
        pawn = pawn_for_controller(pc)
        if pawn is None or not _uobject_alive(pawn):
            continue
        addr = _uobject_addr(pawn)
        if addr in seen:
            continue
        seen.add(addr)
        label = _player_label_for_controller(idx, pc)
        _INFINITE_JUMP_LABEL_CACHE[int(idx)] = label
        contexts.append((idx, label, pawn, None))
        if local_pc_addr and _uobject_addr(pc) == local_pc_addr:
            _INFINITE_JUMP_LOCAL_IDX = int(idx)
    for pawn in live_player_pawns():
        if pawn is None or not _uobject_alive(pawn):
            continue
        addr = _uobject_addr(pawn)
        if addr in seen:
            continue
        idx = len(contexts)
        seen.add(addr)
        contexts.append((idx, f"P{idx + 1}", pawn, None))
    _INFINITE_JUMP_LABEL_CACHE_TIME = now
    _INFINITE_JUMP_LAST_HEAVY_SCAN = now
    return contexts


def _infinite_jump_contexts(now: float | None = None) -> list[tuple[int, str, Any, Any | None]]:
    """Fresh pawn resolve every call — never return cached UObject wrappers.

    Heavy find_all scans run on an interval or when world/controller/pawn identity
    changes. Between scans, reacquire through controllers only.
    """
    global _INFINITE_JUMP_WORLD_SIG, _INFINITE_JUMP_LAST_HEAVY_SCAN, _INFINITE_JUMP_LOCAL_IDX
    try:
        now = time.monotonic() if now is None else float(now)
    except Exception:
        now = 0.0
    try:
        pc = get_pc()
    except Exception:
        pc = None
    pawn = pawn_for_controller(pc) if pc is not None else None
    sig = _infinite_jump_world_sig_from(pc, pawn)
    force_heavy = False
    if _INFINITE_JUMP_WORLD_SIG is None or sig != _INFINITE_JUMP_WORLD_SIG:
        # Travel / respawn / reload — drop labels and force a full rescan.
        _INFINITE_JUMP_LABEL_CACHE.clear()
        _INFINITE_JUMP_LOCAL_IDX = None
        _INFINITE_JUMP_WORLD_SIG = sig
        force_heavy = True
    due = force_heavy or (now - float(_INFINITE_JUMP_LAST_HEAVY_SCAN or 0.0) >= float(_INFINITE_JUMP_HEAVY_SCAN_INTERVAL_S))
    if due:
        return _infinite_jump_contexts_heavy(now)
    return _infinite_jump_contexts_light(pc, pawn)


def _enabled_infinite_jump_names() -> str:
    if not _INFINITE_JUMP_INDICES:
        return "none"
    names: list[str] = []
    for idx in sorted(int(i) for i in _INFINITE_JUMP_INDICES):
        names.append(_INFINITE_JUMP_LABEL_CACHE.get(idx) or f"P{idx + 1}")
    return ", ".join(names)


def _infinite_jump_verify_bits(pawn: Any) -> str:
    bits: list[str] = []
    if pawn is None:
        return "pawn=none"
    try:
        bits.append(f"pawn.JumpMaxCount={getattr(pawn, 'JumpMaxCount', '?')}")
        bits.append(f"pawn.JumpCurrentCount={getattr(pawn, 'JumpCurrentCount', '?')}")
    except Exception:
        bits.append("pawn=unreadable")
    move = _infinite_jump_move_for_pawn(pawn)
    if move is not None:
        try:
            bits.append(f"move.JumpMaxCount={getattr(move, 'JumpMaxCount', '?')}")
            bits.append(f"move.JumpCurrentCount={getattr(move, 'JumpCurrentCount', '?')}")
        except Exception:
            bits.append("move=unreadable")
    else:
        bits.append("move=none")
    return " ".join(bits)


def _hook_arg_to_pawn(obj: Any) -> Any | None:
    if obj is None or not _uobject_alive(obj):
        return None
    for attr in ("Object", "object", "obj", "self", "This", "this", "Caller", "caller", "Context", "context"):
        try:
            inner = getattr(obj, attr, None)
        except Exception:
            inner = None
        if inner is not None and inner is not obj:
            pawn = _hook_arg_to_pawn(inner)
            if pawn is not None:
                return pawn
    for attr in ("OakCharacter", "Pawn", "AcknowledgedPawn", "Character", "ControlledPawn"):
        try:
            pawn = getattr(obj, attr, None)
        except Exception:
            pawn = None
        if pawn is not None and _uobject_alive(pawn):
            return pawn
    # Cheap local match only — never find_all on the jump pre-hook hot path.
    try:
        local_pawn = pawn_for_controller(get_pc())
        if local_pawn is not None and _uobject_addr(local_pawn) and _uobject_addr(obj) == _uobject_addr(local_pawn):
            return obj
    except Exception:
        pass
    # Character/pawn-shaped callers often expose JumpMaxCount directly.
    try:
        if getattr(obj, "JumpMaxCount", None) is not None:
            return obj
    except Exception:
        pass
    return None


def _party_index_for_pawn(pawn: Any) -> int | None:
    if pawn is None or not _uobject_alive(pawn):
        return None
    pawn_addr = _uobject_addr(pawn)
    # Prefer cached local index vs local pawn before any context scan.
    try:
        local_pc = get_pc()
        local_pawn = pawn_for_controller(local_pc) if local_pc is not None else None
        if local_pawn is not None and pawn_addr and _uobject_addr(local_pawn) == pawn_addr:
            if _INFINITE_JUMP_LOCAL_IDX is not None:
                return int(_INFINITE_JUMP_LOCAL_IDX)
            idx = _local_party_index(local_pc)
            return int(idx)
    except Exception:
        pass
    for idx, _name, ctx_pawn, _move in _infinite_jump_contexts():
        try:
            if ctx_pawn is pawn:
                return int(idx)
            if pawn_addr and _uobject_addr(ctx_pawn) == pawn_addr:
                return int(idx)
        except Exception:
            pass
    return None


def _camera_infinite_jump_hook(*args, **kwargs):
    global _INFINITE_JUMP_CAMERA_LAST_APPLY, _INFINITE_JUMP_WORLD_SIG, _INFINITE_JUMP_LOCAL_IDX
    if not _INFINITE_JUMP_INDICES:
        return None
    try:
        now = time.monotonic()
        # Throttle: BlueprintModifyCamera can fire many times per frame.
        if now - float(_INFINITE_JUMP_CAMERA_LAST_APPLY) < float(_INFINITE_JUMP_CAMERA_INTERVAL_S):
            return None
        _INFINITE_JUMP_CAMERA_LAST_APPLY = now

        # Cheapest resolve first: local pc/pawn only (no find_all, no party walk).
        try:
            pc = get_pc()
        except Exception:
            pc = None
        if pc is None or not _uobject_alive(pc):
            return None
        pawn = pawn_for_controller(pc)
        if pawn is None or not _uobject_alive(pawn):
            return None

        sig = _infinite_jump_world_sig_from(pc, pawn)
        force_heavy = False
        if _INFINITE_JUMP_WORLD_SIG is None or sig != _INFINITE_JUMP_WORLD_SIG:
            _INFINITE_JUMP_LABEL_CACHE.clear()
            _INFINITE_JUMP_LOCAL_IDX = None
            _INFINITE_JUMP_WORLD_SIG = sig
            force_heavy = True

        local_idx = _INFINITE_JUMP_LOCAL_IDX
        if local_idx is None:
            local_idx = int(_local_party_index(pc))
            _INFINITE_JUMP_LOCAL_IDX = local_idx

        due_heavy = force_heavy or (
            now - float(_INFINITE_JUMP_LAST_HEAVY_SCAN or 0.0) >= float(_INFINITE_JUMP_HEAVY_SCAN_INTERVAL_S)
        )
        party_needed = due_heavy or any(int(i) != int(local_idx) for i in _INFINITE_JUMP_INDICES)

        # Always re-open local pawn+move when IJ is enabled. Skipping when the
        # pawn looks "open" missed CharMoveComp JumpCurrentCount spend — IJ
        # reported ON but the next jump was still consumed.
        if int(local_idx) in _INFINITE_JUMP_INDICES:
            _force_infinite_jump_ready(pawn, None, light=True)

        if not party_needed:
            return None

        contexts = _infinite_jump_contexts_heavy(now) if due_heavy else _infinite_jump_contexts_light(pc, pawn)
        live_idxs = {int(idx) for idx, _n, ctx_pawn, _m in contexts if ctx_pawn is not None}
        # Drop party slots that no longer resolve (travel / disconnect) — only after heavy.
        if due_heavy:
            stale = [i for i in list(_INFINITE_JUMP_INDICES) if i not in live_idxs]
            for i in stale:
                _INFINITE_JUMP_INDICES.discard(i)
        if not _INFINITE_JUMP_INDICES:
            return None
        touched: set[int] = set()
        local_pawn_addr = _uobject_addr(pawn)
        if local_pawn_addr:
            touched.add(local_pawn_addr)
        for idx, _name, ctx_pawn, _move in contexts:
            if int(idx) not in _INFINITE_JUMP_INDICES:
                continue
            if ctx_pawn is None or not _uobject_alive(ctx_pawn):
                continue
            key = _uobject_addr(ctx_pawn) or id(ctx_pawn)
            if key in touched:
                continue
            touched.add(key)
            _force_infinite_jump_ready(ctx_pawn, None, light=True)
    except Exception:
        pass
    return None


def _infinite_jump_prep_from_hook(*args, **kwargs) -> bool:
    """Reset jump counters for an enabled pawn. True when a live IJ pawn matched."""
    if not _INFINITE_JUMP_INDICES:
        return False
    try:
        for obj in list(args) + list(kwargs.values()):
            pawn = _hook_arg_to_pawn(obj)
            if pawn is None or not _uobject_alive(pawn):
                continue
            idx = _party_index_for_pawn(pawn)
            if idx is not None and int(idx) in _INFINITE_JUMP_INDICES:
                _force_infinite_jump_ready(pawn, None)
                return True
    except Exception:
        pass
    return False


def _jump_gate_hook(*args, **kwargs):
    # CanJump / CanJumpInternal: force True so BL4 allows another jump.
    # Do not use this on Character.Jump — Block there swallows the jump.
    try:
        from .travel_gate import is_travel_quiet

        if is_travel_quiet():
            return None
    except Exception:
        return None
    if not _INFINITE_JUMP_INDICES:
        return None
    matched = _infinite_jump_prep_from_hook(*args, **kwargs)
    if matched and _UnrealHookBlock is not None:
        try:
            return _UnrealHookBlock, True
        except Exception:
            return None
    return None


def _jump_start_hook(*args, **kwargs):
    # Character.Jump must run. Only refresh counters, then let the original through.
    try:
        from .travel_gate import is_travel_quiet

        if is_travel_quiet():
            return None
    except Exception:
        return None
    if not _INFINITE_JUMP_INDICES:
        return None
    _infinite_jump_prep_from_hook(*args, **kwargs)
    return None


def _register_infinite_jump_hooks() -> None:
    try:
        from . import camera_tick

        camera_tick.register("infinite_jump", _camera_infinite_jump_hook, priority=30)
        _log("Backend Infinite Jump camera hook installed.")
    except Exception as exc:
        _log(f"Backend Infinite Jump camera hook skipped: {exc!r}")
    canjump_targets = (
        "/Script/Engine.Character:CanJumpInternal",
        "/Script/Engine.Character:CanJump",
        "/Script/GbxGame.OakCharacter:CanJumpInternal",
        "/Script/GbxGame.OakCharacter:CanJump",
        "/Script/OakGame.OakCharacter:CanJumpInternal",
        "/Script/OakGame.OakCharacter:CanJump",
    )
    jump_targets = (
        "/Script/Engine.Character:Jump",
        "/Script/GbxGame.OakCharacter:Jump",
        "/Script/OakGame.OakCharacter:Jump",
    )
    from .hook_gate import track

    for i, target in enumerate(canjump_targets):
        try:
            track(
                hook(
                    target,
                    immediately_enable=False,
                    hook_identifier=f"matts_sdk_boosting_tools_backend_infinite_jump_canjump_v2_{i}",
                )(_jump_gate_hook)
            )
        except Exception as exc:
            _log(f"Backend Infinite Jump CanJump hook skipped {target}: {exc!r}")
    for i, target in enumerate(jump_targets):
        try:
            track(
                hook(
                    target,
                    immediately_enable=False,
                    hook_identifier=f"matts_sdk_boosting_tools_backend_infinite_jump_jump_v2_{i}",
                )(_jump_start_hook)
            )
        except Exception as exc:
            _log(f"Backend Infinite Jump Jump hook skipped {target}: {exc!r}")


def _restore_normal_jump(pawn: Any) -> None:
    """Put JumpMaxCount back to a normal double-jump so Off actually disables IJ."""
    if pawn is None:
        return
    try:
        move = _infinite_jump_move_for_pawn(pawn)
    except Exception:
        move = None
    pairs = (
        ("JumpMaxCount", 2),
        ("JumpCurrentCount", 0),
        ("JumpCurrentCountPreJump", 0),
    )
    for obj in (pawn, move):
        if obj is None:
            continue
        for attr, value in pairs:
            try:
                _set_if_needed(obj, attr, value)
            except Exception:
                pass


def set_infinite_jump_all(enabled: bool) -> str:
    global _INFINITE_JUMP_LAST_HEAVY_SCAN, _INFINITE_JUMP_CAMERA_LAST_APPLY
    _INFINITE_JUMP_LAST_HEAVY_SCAN = 0.0  # force heavy party resolve on toggle
    contexts = _infinite_jump_contexts()
    if enabled:
        _INFINITE_JUMP_INDICES.clear()
        for idx, _name, pawn, _move in contexts:
            if pawn is not None and _uobject_alive(pawn) and not _is_default(pawn):
                _INFINITE_JUMP_INDICES.add(int(idx))
                _force_infinite_jump_ready(pawn, None)
    else:
        for _idx, _name, pawn, _move in contexts:
            _restore_normal_jump(pawn)
        _INFINITE_JUMP_INDICES.clear()
        _clear_infinite_jump_runtime_caches()
    _INFINITE_JUMP_CAMERA_LAST_APPLY = 0.0
    verify = ""
    try:
        local_pawn = pawn_for_controller(get_pc())
        if local_pawn is not None:
            verify = " " + _infinite_jump_verify_bits(local_pawn)
    except Exception:
        verify = ""
    msg = f"Infinite Jump enabled for: {_enabled_infinite_jump_names()}.{verify}"
    _log(msg)
    _sync_movement_camera_need()
    return msg


def set_infinite_jump_for_index(idx: int, enabled: bool) -> str:
    global _INFINITE_JUMP_LAST_HEAVY_SCAN, _INFINITE_JUMP_CAMERA_LAST_APPLY
    idx = int(idx)
    if enabled:
        _INFINITE_JUMP_INDICES.add(idx)
    else:
        _INFINITE_JUMP_INDICES.discard(idx)
        if not _INFINITE_JUMP_INDICES:
            _clear_infinite_jump_runtime_caches()
    _INFINITE_JUMP_LAST_HEAVY_SCAN = 0.0
    _INFINITE_JUMP_CAMERA_LAST_APPLY = 0.0
    verify = ""
    for ctx_idx, _name, pawn, _move in _infinite_jump_contexts():
        if int(ctx_idx) != idx:
            continue
        if enabled:
            _force_infinite_jump_ready(pawn, None)
        else:
            _restore_normal_jump(pawn)
        try:
            verify = " " + _infinite_jump_verify_bits(pawn)
        except Exception:
            verify = ""
        break
    msg = f"Infinite Jump enabled for: {_enabled_infinite_jump_names()}.{verify}"
    _log(msg)
    _sync_movement_camera_need()
    return msg


def toggle_infinite_jump_for_index(idx: int) -> str:
    idx = int(idx)
    return set_infinite_jump_for_index(idx, idx not in _INFINITE_JUMP_INDICES)


def toggle_infinite_jump_for_scope(scope: str = "all") -> tuple[str, bool]:
    """Toggle Infinite Jump for Local / All / Others. Returns (message, enabled)."""
    global _INFINITE_JUMP_LAST_HEAVY_SCAN
    contexts = _infinite_jump_contexts()
    live = [int(idx) for idx, _name, pawn, _move in contexts if pawn is not None]
    if not live:
        _INFINITE_JUMP_LAST_HEAVY_SCAN = 0.0
        try:
            contexts = _infinite_jump_contexts_heavy(time.monotonic())
        except Exception:
            contexts = _infinite_jump_contexts()
        live = [int(idx) for idx, _name, pawn, _move in contexts if pawn is not None]
    local_idx = _INFINITE_JUMP_LOCAL_IDX
    if local_idx is None:
        local_idx = 0
    key = str(scope or "all").strip().lower() or "all"
    if key in ("local", "me"):
        target = [i for i in live if i == int(local_idx)]
        if not target and live:
            target = [int(local_idx)]
        if not target:
            target = [int(local_idx)]
    elif key in ("others", "other", "remote", "nonhost"):
        target = [i for i in live if i != int(local_idx)]
    else:
        target = list(live)
        if not target:
            target = [int(local_idx)]
    if not target:
        return (f"Infinite Jump skipped: no pawns for scope={key}.", False)
    currently_on = bool(target) and all(i in _INFINITE_JUMP_INDICES for i in target)
    enable = not currently_on
    for idx in target:
        set_infinite_jump_for_index(int(idx), enable)
    state = "On" if enable else "Off"
    msg = (
        f"Infinite Jump {state} for {len(target)} player(s) (scope={key}). "
        f"Enabled: {_enabled_infinite_jump_names()}."
    )
    _log(msg)
    return msg, enable


def infinite_jump_status() -> dict[str, Any]:
    local_idx = _INFINITE_JUMP_LOCAL_IDX
    indices = sorted(int(i) for i in _INFINITE_JUMP_INDICES)
    enabled_local = local_idx is not None and int(local_idx) in _INFINITE_JUMP_INDICES
    return {
        "enabled": bool(enabled_local if local_idx is not None else bool(indices)),
        "enabled_local": bool(enabled_local),
        "count": len(indices),
        "names": _enabled_infinite_jump_names(),
    }


def reapply_infinite_jump_on_enabled() -> None:
    """Movement apply writes JumpMaxCount=2; re-open IJ on still-enabled pawns."""
    if not _INFINITE_JUMP_INDICES:
        return
    for idx, _name, pawn, _move in _infinite_jump_contexts():
        if int(idx) in _INFINITE_JUMP_INDICES:
            _force_infinite_jump_ready(pawn, None)


_register_infinite_jump_hooks()

def set_time_dilation(value: float) -> str:
    value = max(0.01, min(64.0, float(value)))
    try:
        ws = ENGINE.GameViewport.World.PersistentLevel.WorldSettings
        ws.TimeDilation = value
        return f"Game speed set to {value:.2f}x."
    except Exception as exc:
        return f"Game speed failed: {exc!r}"


def _ensure_cheat_manager(pc: Any) -> Any | None:
    """Return/create the controller CheatManager without registering keybinds."""
    if pc is None:
        return None
    try:
        cm = getattr(pc, "CheatManager", None)
        if cm is not None:
            return cm
    except Exception:
        pass
    # Some builds expose EnableCheats; try it first because it lets the game
    # allocate the correct native cheat manager class.
    for name in ("EnableCheats", "ServerEnableCheats"):
        try:
            fn = getattr(pc, name, None)
            if callable(fn):
                try:
                    fn()
                except TypeError:
                    fn("")
                cm = getattr(pc, "CheatManager", None)
                if cm is not None:
                    return cm
        except Exception:
            pass
    # Fallback: construct the native CheatClass as a child of the controller.
    try:
        cheat_class = getattr(pc, "CheatClass", None)
        if cheat_class is not None:
            cm = unrealsdk.construct_object(cheat_class, pc, "OakCheatManager_MattsSDKBoostingTools")
            pc.CheatManager = cm
            return cm
    except Exception:
        pass
    return None


def toggle_players_only() -> str:
    try:
        pc = get_pc()
        cm = _ensure_cheat_manager(pc)
        fn = getattr(cm, "PlayersOnly", None) if cm is not None else None
        if callable(fn):
            fn()
            return "Toggled Players Only / world freeze through CheatManager."
        return f"PlayersOnly unavailable on CheatManager: pc={pc} cm={cm}."
    except Exception as exc:
        return f"PlayersOnly failed: {exc!r}"


def set_no_target(enabled: bool) -> str:
    try:
        lib = unrealsdk.find_class("GbxTargetingFunctionLibrary").ClassDefaultObject
        lib.LockTargetableByAI(get_pc(), "msbt_no_target", bool(enabled), bool(enabled))
        return "No Target On." if enabled else "No Target Off."
    except Exception as exc:
        return f"No Target failed: {exc!r}"


_LOOT_RADIUS_MIN_M = 10
_LOOT_RADIUS_MAX_M = 500
_LOOT_RADIUS_DEFAULT_M = 150
# Far XY pocket at the item's own Z. The old Z=-1e9 dump left falling physics
# bodies that Pull/Hide would keep rediscovering.
_LOOT_HIDE_POCKET_XY = (2500000.0, 2500000.0)
_LOOT_HIDE_AWAY = (_LOOT_HIDE_POCKET_XY[0], _LOOT_HIDE_POCKET_XY[1], 0.0)
_LOOT_HIDE_VOID_Z = -100000000.0


def _loot_xyz(actor: Any) -> tuple[float, float, float] | None:
    loc = _actor_location(actor)
    if loc is None:
        return None
    try:
        return (float(loc.X), float(loc.Y), float(loc.Z))
    except Exception:
        return None


def _clamp_loot_radius_m(value: object) -> float:
    try:
        radius = float(value)
    except Exception:
        return 0.0
    if radius <= 0:
        return 0.0
    return max(float(_LOOT_RADIUS_MIN_M), min(float(_LOOT_RADIUS_MAX_M), radius))


def loot_scope_origins(scope: str = "local", selected_pawn: Any = None) -> list[tuple[float, float, float]]:
    """World positions used to decide which ground loot is in range."""
    key = str(scope or "local").strip().lower()
    if key in ("selected", "named"):
        xyz = _loot_xyz(selected_pawn)
        if xyz is not None:
            return [xyz]
        key = "local"
    pawns = live_player_pawns()
    if key in ("all", "everyone", "party"):
        out = [xyz for pawn in pawns if (xyz := _loot_xyz(pawn)) is not None]
        return out or loot_scope_origins("local")
    if key in ("nonhost", "others", "other", "remote"):
        return [xyz for pawn in filter_pawns_by_scope(pawns, "others") if (xyz := _loot_xyz(pawn)) is not None]
    pawn = None
    try:
        pawn = pawn_for_controller(get_pc())
    except Exception:
        pawn = None
    xyz = _loot_xyz(pawn)
    return [xyz] if xyz is not None else []


def filter_loot_by_origins(
    items: list[Any],
    origins: list[tuple[float, float, float]],
    radius_m: object,
) -> list[Any]:
    """Keep pickups within radius_m of any origin. radius_m <= 0 means no limit."""
    rows = [item for item in (items or []) if item]
    if not rows:
        return []
    radius = _clamp_loot_radius_m(radius_m)
    if radius <= 0:
        return rows
    if not origins:
        return []
    radius_cm = radius * 100.0
    out: list[Any] = []
    for inv in rows:
        xyz = _loot_xyz(inv)
        if xyz is None:
            continue
        if any(math.dist(xyz, origin) <= radius_cm for origin in origins):
            out.append(inv)
    return out


def _is_hidden_away(xyz: tuple[float, float, float] | None) -> bool:
    if xyz is None:
        return False
    if xyz[2] <= _LOOT_HIDE_VOID_Z:
        return True
    return math.hypot(xyz[0] - _LOOT_HIDE_POCKET_XY[0], xyz[1] - _LOOT_HIDE_POCKET_XY[1]) < 80000.0


def _loot_vector(x: float, y: float, z: float) -> Any:
    try:
        vec = unrealsdk.make_struct("Vector", X=float(x), Y=float(y), Z=float(z))
        if vec is not None:
            return vec
    except Exception:
        pass
    return type("LootVec", (), {"X": float(x), "Y": float(y), "Z": float(z)})()


def _set_pickup_physics(inv: Any, enabled: bool) -> None:
    for name in ("RootPrimitiveComponent", "RootComponent"):
        root = getattr(inv, name, None)
        if root is None:
            continue
        fn = getattr(root, "SetSimulatePhysics", None)
        if callable(fn):
            try:
                fn(bool(enabled))
            except Exception:
                pass
        if enabled:
            continue
        zero = _loot_vector(0.0, 0.0, 0.0)
        for vel_name in ("SetPhysicsLinearVelocity", "SetAllPhysicsLinearVelocity"):
            vel = getattr(root, vel_name, None)
            if not callable(vel):
                continue
            try:
                vel(zero, False)
            except TypeError:
                try:
                    vel(zero)
                except Exception:
                    pass
            except Exception:
                pass


def _pickup_near(inv: Any, x: float, y: float, z: float, slack: float = 400.0) -> bool:
    xyz = _loot_xyz(inv)
    if xyz is None:
        return False
    return math.dist(xyz, (float(x), float(y), float(z))) <= slack


def _move_pickup(inv: Any, x: float, y: float, z: float) -> bool:
    """Move a pickup with physics off. Teleport-while-simulating is a no-op in BL4."""
    _set_pickup_physics(inv, False)
    dest = _loot_vector(x, y, z)
    ignore = _loot_ignore_rotator()
    tele = getattr(inv, "K2_TeleportTo", None) or getattr(inv, "TeleportTo", None)
    if callable(tele):
        try:
            tele(dest, ignore)
        except TypeError:
            try:
                tele(dest)
            except Exception:
                pass
        except Exception:
            pass
        if _pickup_near(inv, x, y, z):
            return True
    setter = getattr(inv, "K2_SetActorLocation", None) or getattr(inv, "SetActorLocation", None)
    if callable(setter):
        for args in ((dest, False, None, True), (dest, False, None), (dest, False), (dest,)):
            try:
                setter(*args)
                break
            except TypeError:
                continue
            except Exception:
                break
        if _pickup_near(inv, x, y, z):
            return True
    return _pickup_near(inv, x, y, z)


def _iter_ground_loot(scope: str, radius_m: object, selected_pawn: Any = None) -> list[Any]:
    loot = _sorted_ground_loot(wake_physics=False)
    items = list(loot.get("Pickups") or []) + list(loot.get("Gear") or [])
    origins = loot_scope_origins(scope, selected_pawn)
    return filter_loot_by_origins(items, origins, radius_m)


def _loot_ignore_rotator() -> Any:
    try:
        return unrealsdk.make_struct("Rotator")
    except Exception:
        return None


def _destroy_pickup(inv: Any) -> bool:
    for name in ("K2_DestroyActor", "Destroy"):
        try:
            fn = getattr(inv, name, None)
            if callable(fn):
                fn()
                return True
        except Exception:
            continue
    return False


def _destroy_junk_around(origins: list[tuple[float, float, float]], radius_m: object) -> int:
    try:
        jsfl = unrealsdk.find_class("JunkSystemFunctionLibrary").ClassDefaultObject
    except Exception:
        return 0
    radius = _clamp_loot_radius_m(radius_m)
    half = 1000000.0 if radius <= 0 else max(800.0, radius * 100.0)
    boxes = origins or [(0.0, 0.0, 0.0)]
    cleared = 0
    for ox, oy, oz in boxes:
        try:
            box = unrealsdk.make_struct(
                "Box",
                MIN=unrealsdk.make_struct("Vector", X=ox - half, Y=oy - half, Z=oz - half),
                MAX=unrealsdk.make_struct("Vector", X=ox + half, Y=oy + half, Z=oz + half),
            )
        except Exception:
            continue
        controllers = live_player_controllers() or [get_pc()]
        for pc in controllers:
            if pc is None:
                continue
            try:
                jsfl.DestroyJunkWithinBounds(pc, box)
                cleared += 1
            except Exception:
                continue
    return cleared


def delete_ground_items(
    radius_m: object = 0,
    scope: str = "all",
    selected_pawn: Any = None,
) -> str:
    """Destroy ground loot near the scoped players. Host-only junk wipe is not enough in co-op."""
    origins = loot_scope_origins(scope, selected_pawn)
    if not origins and str(scope or "").strip().lower() in ("selected", "named"):
        return "Delete Ground Items: choose a named player first."
    junk_calls = _destroy_junk_around(origins, radius_m)
    removed = 0
    for inv in _iter_ground_loot(scope, radius_m, selected_pawn):
        if _destroy_pickup(inv):
            removed += 1
    if removed:
        return f"Ground items deleted: {removed} pickup(s) around {scope}."
    if junk_calls:
        return f"Ground items deleted (junk wipe around {scope})."
    return "Delete Ground Items: no ground loot found."


def hide_ground_loot(
    radius_m: object = 0,
    scope: str = "local",
    selected_pawn: Any = None,
) -> str:
    """One-way soft clear: park loot in a far XY pocket. Not reversible."""
    pc = get_pc()
    if pc is None:
        return "Clear Loot (Hide): load into a character first."
    if str(scope or "").strip().lower() in ("selected", "named") and selected_pawn is None:
        return "Clear Loot (Hide): choose a named player first."
    removed = 0
    for inv in _iter_ground_loot(scope, radius_m, selected_pawn):
        xyz = _loot_xyz(inv)
        if xyz is None or _is_hidden_away(xyz):
            continue
        spread = removed % 32
        away_x = _LOOT_HIDE_POCKET_XY[0] + (spread % 8) * 120.0
        away_y = _LOOT_HIDE_POCKET_XY[1] + (spread // 8) * 120.0
        if not _move_pickup(inv, away_x, away_y, xyz[2]):
            continue
        removed += 1
    if removed:
        return f"Clear Loot (Hide): moved {removed} item(s) out of play."
    return "Clear Loot (Hide): no ground loot found."


# Pulled gear lands on an Archimedean spiral growing away from the player.
# Fixed-count rings put every ring's first item on the same bearing, which read
# in-game as long lines shooting away from you.
# Spacing is tuned to BL4 pickup footprints: turn growth stays above item
# spacing so neighbouring loops never crowd tighter than neighbours on the arc.
_LOOT_SPIRAL_START_RADIUS = 240.0
_LOOT_SPIRAL_ITEM_SPACING = 155.0
_LOOT_SPIRAL_TURN_GROWTH = 230.0
_LOOT_PICKUP_MATERIALS = ("Ammo", "Cash", "Eridium", "Health", "Shield", "Grenade")
_SUPER_DASH_MIN = 100
_SUPER_DASH_MAX = 20000
_SUPER_DASH_COOLDOWN_S = 0.12
_SUPER_DASH_STOP_JUMP_DELAY_S = 0.015
_super_dash_enabled = False
_super_dash_strength = 1000
_super_dash_key_was_down = False
# MSBT dash key (edge-triggered). LeftShift conflicts with sprint/walk in BL4,
# so default to V — still distinct from Azzy NumPadZero.
_MSBT_SUPER_DASH_KEY = "V"
# Azzy-style Super Dash (separate from MSBT).
# Impulse must run on the camera/game tick — never from a daemon Thread.
_AZZY_SUPER_DASH_KEY = "NumPadZero"
_azzy_super_dash_enabled = False
_azzy_super_dash_strength = 1000
_azzy_super_dash_key_was_down = False
_pending_msbt_super_dash = False
_pending_azzy_super_dash = False
_pending_dash_stop_jump_at = 0.0
_dash_cooldown_until = 0.0


def _live_actor(obj: Any) -> bool:
    return _uobject_alive(obj)


def _loot_spiral_offset(index: int) -> tuple[float, float]:
    """Return (forward, right) offsets in cm for the index-th pulled item.

    Archimedean spiral ``r = a + b*theta`` stepped by arc length, so neighbours
    stay roughly _LOOT_SPIRAL_ITEM_SPACING apart while the radius keeps growing
    away from the player.
    """
    growth = _LOOT_SPIRAL_TURN_GROWTH / (2.0 * math.pi)
    arc = max(0, int(index)) * _LOOT_SPIRAL_ITEM_SPACING
    radius = math.sqrt(_LOOT_SPIRAL_START_RADIUS ** 2 + 2.0 * growth * arc)
    angle = (radius - _LOOT_SPIRAL_START_RADIUS) / growth
    return math.cos(angle) * radius, math.sin(angle) * radius


def _iter_all_pickups() -> list[Any]:
    try:
        pickups = unrealsdk.find_all("InventoryPickup", False) or []
    except Exception:
        return []
    out: list[Any] = []
    for inv in pickups:
        if not inv:
            continue
        try:
            if inv == inv.Class.ClassDefaultObject:
                continue
        except Exception:
            pass
        out.append(inv)
    return out


def _sorted_ground_loot(*, wake_physics: bool = True) -> dict[str, list[Any]]:
    loot: dict[str, list[Any]] = {"Pickups": [], "Gear": []}
    for inv in _iter_all_pickups():
        try:
            root = getattr(inv, "RootPrimitiveComponent", None) or getattr(inv, "RootComponent", None)
            if wake_physics and root is not None:
                try:
                    root.SetSimulatePhysics(True)
                except Exception:
                    pass
            body = str(getattr(inv, "BodyData", "") or "")
            if "Pickups" in body:
                loot["Pickups"].append(inv)
                continue
            if not getattr(inv, "BodyData", None):
                usable = False
                if root is not None:
                    try:
                        count = int(root.GetNumMaterials())
                    except Exception:
                        count = 0
                    for index in range(count):
                        try:
                            material = root.GetMaterial(index)
                        except Exception:
                            material = None
                        if not material:
                            continue
                        name = str(getattr(material, "Name", "") or "")
                        if any(tag in name for tag in _LOOT_PICKUP_MATERIALS):
                            usable = True
                            break
                if usable:
                    loot["Pickups"].append(inv)
                else:
                    loot["Gear"].append(inv)
                continue
            loot["Gear"].append(inv)
        except Exception:
            continue
    return loot


def pull_ground_loot_here(
    radius_m: object = 0,
    scope: str = "local",
    selected_pawn: Any = None,
) -> str:
    """Teleport nearby ground loot to the local player (Azzy-style Pull Loot)."""
    return _teleport_ground_loot_layout(radius_m=radius_m, scope=scope, selected_pawn=selected_pawn)


def _teleport_ground_loot_layout(
    *,
    verb: str = "Pull Loot",
    radius_m: object = 0,
    scope: str = "local",
    selected_pawn: Any = None,
) -> str:
    """Teleport ground loot onto an Archimedean spiral around the local pawn."""
    pc = get_pc()
    pawn = None
    if pc is not None:
        pawn = pawn_for_controller(pc)
        if pawn is None:
            try:
                pawn = getattr(pc, "OakCharacter", None) or getattr(pc, "Pawn", None)
            except Exception:
                pawn = None
    if pawn is None:
        return "Pull Loot: load into a character first."
    if str(scope or "").strip().lower() in ("selected", "named") and selected_pawn is None:
        return "Pull Loot: choose a named player first."
    try:
        where = pawn.K2_GetActorLocation()
        where.Z -= 40
    except Exception as exc:
        return f"Pull Loot failed: {exc!r}"
    ignore = _loot_ignore_rotator()
    loot = _sorted_ground_loot()
    origins = loot_scope_origins(scope, selected_pawn)
    pickups = [
        inv for inv in filter_loot_by_origins(list(loot.get("Pickups") or []), origins, radius_m)
        if not _is_hidden_away(_loot_xyz(inv))
    ]
    gear = [
        inv for inv in filter_loot_by_origins(list(loot.get("Gear") or []), origins, radius_m)
        if not _is_hidden_away(_loot_xyz(inv))
    ]
    moved = 0
    for inv in pickups:
        try:
            inv.K2_TeleportTo(where, ignore)
            moved += 1
        except Exception:
            continue
    try:
        yaw = math.radians(float(pawn.K2_GetActorRotation().Yaw))
    except Exception:
        yaw = 0.0
    forward_x, forward_y = math.cos(yaw), math.sin(yaw)
    right_x, right_y = -math.sin(yaw), math.cos(yaw)
    for index, inv in enumerate(gear):
        try:
            ahead, side = _loot_spiral_offset(index)
            x = float(where.X) + forward_x * ahead + right_x * side
            y = float(where.Y) + forward_y * ahead + right_y * side
            z = float(where.Z)
            spot = None
            try:
                spot = unrealsdk.make_struct("Vector", X=x, Y=y, Z=z)
            except Exception:
                spot = None
            if spot is None:
                spot = pawn.K2_GetActorLocation()
                spot.X = x
                spot.Y = y
                spot.Z = z
            inv.K2_TeleportTo(spot, ignore)
            moved += 1
        except Exception:
            continue
    if moved:
        limit = "all loaded" if _clamp_loot_radius_m(radius_m) <= 0 else f"{int(_clamp_loot_radius_m(radius_m))}m"
        return f"{verb}: moved {moved} item(s) from {scope} ({limit})."
    return f"{verb}: no ground loot found."


def set_super_dash_strength(value: int) -> int:
    global _super_dash_strength
    _super_dash_strength = max(_SUPER_DASH_MIN, min(_SUPER_DASH_MAX, int(value)))
    return _super_dash_strength


def get_super_dash_state() -> dict[str, Any]:
    return {
        "enabled": bool(_super_dash_enabled),
        "strength": int(_super_dash_strength),
        "min": _SUPER_DASH_MIN,
        "max": _SUPER_DASH_MAX,
        "key": _MSBT_SUPER_DASH_KEY,
        "variant": "msbt",
        "pending": bool(_pending_msbt_super_dash),
    }


def toggle_super_dash(enabled: bool | None = None) -> str:
    global _super_dash_enabled
    if enabled is None:
        _super_dash_enabled = not _super_dash_enabled
    else:
        _super_dash_enabled = bool(enabled)
    state = "ON" if _super_dash_enabled else "OFF"
    _sync_movement_camera_need()
    return (
        f"Super Dash (MSBT) {state} (strength {_super_dash_strength}). "
        f"Press {_MSBT_SUPER_DASH_KEY} while enabled (camera tick)."
    )


def _dash_character(pc: Any) -> Any:
    if pc is None:
        return None
    character = getattr(pc, "OakCharacter", None)
    if character is None:
        character = getattr(pc, "Pawn", None)
    return character if _live_actor(character) else None


def _dash_forward_xy(pc: Any, character: Any) -> tuple[float, float]:
    """Horizontal look/move direction. Pitch must not shrink dash strength."""
    forward = None
    for obj in (pc, character):
        if obj is None:
            continue
        getter = getattr(obj, "GetActorForwardVector", None)
        if not callable(getter):
            continue
        try:
            forward = getter()
            if forward is not None:
                break
        except Exception:
            forward = None
    fx = fy = 0.0
    if forward is not None:
        try:
            fx = float(getattr(forward, "X", 0.0) or 0.0)
            fy = float(getattr(forward, "Y", 0.0) or 0.0)
        except Exception:
            fx = fy = 0.0
    length = math.sqrt(fx * fx + fy * fy)
    if length < 1e-4:
        try:
            rot = character.K2_GetActorRotation() if character is not None else None
            yaw = math.radians(float(getattr(rot, "Yaw", 0.0) or 0.0))
            fx, fy = math.cos(yaw), math.sin(yaw)
            length = 1.0
        except Exception:
            return 1.0, 0.0
    return fx / length, fy / length


def _fire_super_dash_impulse(strength: float) -> str:
    """Jump + horizontal AddImpulse. StopJumping is deferred on camera tick."""
    pc = get_pc()
    character = _dash_character(pc)
    if character is None:
        return "Super Dash: load into a character first."
    try:
        try:
            character.Jump()
        except Exception:
            pass
        fx, fy = _dash_forward_xy(pc, character)
        impulse = unrealsdk.make_struct(
            "Vector",
            X=float(fx) * float(strength),
            Y=float(fy) * float(strength),
            Z=10.0,
        )
        move = getattr(character, "OakCharacterMovement", None) or getattr(character, "CharacterMovement", None)
        if move is None:
            return "Super Dash failed: no movement component."
        move.AddImpulse(impulse, True)
        return f"Super Dash fired ({int(strength)})."
    except Exception as exc:
        return f"Super Dash failed: {exc!r}"


def _schedule_dash_stop_jump(now: float) -> None:
    global _pending_dash_stop_jump_at
    _pending_dash_stop_jump_at = float(now) + _SUPER_DASH_STOP_JUMP_DELAY_S


def _tick_dash_stop_jump(now: float) -> None:
    global _pending_dash_stop_jump_at
    if not _pending_dash_stop_jump_at or now < _pending_dash_stop_jump_at:
        return
    _pending_dash_stop_jump_at = 0.0
    character = _dash_character(get_pc())
    if character is None:
        return
    try:
        character.StopJumping()
    except Exception:
        pass


def _execute_super_dash(strength: float, *, label: str) -> str:
    """Game-thread dash: impulse now, StopJumping a few ms later (Azzy timing)."""
    global _dash_cooldown_until
    now = time.monotonic()
    if now < float(_dash_cooldown_until or 0.0):
        return f"{label}: cooling down."
    msg = _fire_super_dash_impulse(strength)
    if "fired" in msg.lower():
        _schedule_dash_stop_jump(now)
        _dash_cooldown_until = now + _SUPER_DASH_COOLDOWN_S
        return f"{label} fired ({int(strength)})."
    return msg.replace("Super Dash", label, 1)


def fire_super_dash(strength: int | None = None) -> str:
    """Queue MSBT dash for the camera tick (safe from bridge/HTTP threads)."""
    global _pending_msbt_super_dash
    if strength is not None:
        set_super_dash_strength(int(strength))
    if get_pc() is None:
        return "Super Dash (MSBT): load into a character first."
    _pending_msbt_super_dash = True
    _sync_movement_camera_need()
    return f"Super Dash (MSBT) queued ({_super_dash_strength})."


def set_azzy_super_dash_strength(value: int) -> int:
    global _azzy_super_dash_strength
    _azzy_super_dash_strength = max(_SUPER_DASH_MIN, min(_SUPER_DASH_MAX, int(value)))
    return _azzy_super_dash_strength


def get_azzy_super_dash_state() -> dict[str, Any]:
    return {
        "enabled": bool(_azzy_super_dash_enabled),
        "strength": int(_azzy_super_dash_strength),
        "min": _SUPER_DASH_MIN,
        "max": _SUPER_DASH_MAX,
        "key": _AZZY_SUPER_DASH_KEY,
        "variant": "azzy",
        "pending": bool(_pending_azzy_super_dash),
    }


def toggle_azzy_super_dash(enabled: bool | None = None) -> str:
    global _azzy_super_dash_enabled
    if enabled is None:
        _azzy_super_dash_enabled = not _azzy_super_dash_enabled
    else:
        _azzy_super_dash_enabled = bool(enabled)
    state = "ON" if _azzy_super_dash_enabled else "OFF"
    _sync_movement_camera_need()
    return (
        f"Super Dash (Azzy) {state} (strength {_azzy_super_dash_strength}). "
        f"Press {_AZZY_SUPER_DASH_KEY} while enabled (camera tick)."
    )


def request_azzy_super_dash(strength: int | None = None) -> str:
    """Queue an Azzy-style dash for the next camera tick (never Thread)."""
    global _pending_azzy_super_dash
    if get_pc() is None:
        return "Super Dash (Azzy): load into a character first."
    if strength is not None:
        set_azzy_super_dash_strength(int(strength))
    _pending_azzy_super_dash = True
    _sync_movement_camera_need()
    return f"Super Dash (Azzy) queued ({_azzy_super_dash_strength})."


def _input_key_down(pc: Any, key_name: str) -> bool:
    if pc is None or not key_name:
        return False
    try:
        key = unrealsdk.make_struct("Key", KeyName=str(key_name))
        return bool(pc.IsInputKeyDown(key))
    except Exception:
        try:
            return bool(pc.IsInputKeyDown(str(key_name)))
        except Exception:
            return False


def _tick_pending_super_dashes(now: float) -> None:
    global _pending_msbt_super_dash, _pending_azzy_super_dash
    if _pending_msbt_super_dash:
        _pending_msbt_super_dash = False
        _execute_super_dash(_super_dash_strength, label="Super Dash (MSBT)")
    if _pending_azzy_super_dash:
        _pending_azzy_super_dash = False
        _execute_super_dash(_azzy_super_dash_strength, label="Super Dash (Azzy)")
    _tick_dash_stop_jump(now)


def _super_dash_camera_hook(*_args: Any, **_kwargs: Any) -> None:
    global _super_dash_key_was_down, _azzy_super_dash_key_was_down
    # BlueprintModifyCamera fires once per active CameraModifier, several times a
    # frame. get_pc() plus two IsInputKeyDown calls is too much to pay when no
    # dash feature is armed and nothing is queued, so bail before any SDK lookup.
    if (
        not _super_dash_enabled
        and not _azzy_super_dash_enabled
        and not _pending_msbt_super_dash
        and not _pending_azzy_super_dash
        and not _pending_dash_stop_jump_at
    ):
        _super_dash_key_was_down = False
        _azzy_super_dash_key_was_down = False
        _sync_movement_camera_need()
        return

    now = time.monotonic()
    _tick_pending_super_dashes(now)

    pc = get_pc()
    if _super_dash_enabled and pc is not None:
        down = _input_key_down(pc, _MSBT_SUPER_DASH_KEY)
        if down and not _super_dash_key_was_down:
            _execute_super_dash(_super_dash_strength, label="Super Dash (MSBT)")
        _super_dash_key_was_down = down
    else:
        _super_dash_key_was_down = False

    if _azzy_super_dash_enabled and pc is not None:
        down = _input_key_down(pc, _AZZY_SUPER_DASH_KEY)
        if down and not _azzy_super_dash_key_was_down:
            _execute_super_dash(_azzy_super_dash_strength, label="Super Dash (Azzy)")
        _azzy_super_dash_key_was_down = down
    else:
        _azzy_super_dash_key_was_down = False


# Fly speed is applied on the button click only. Do not hook GetMaxSpeed /
# PhysFlying / camera tick to "hold" it — those run every frame and hitch BL4.
_DEFAULT_FLY_SPEED = 2400.0
_MSBT_FLYING = False
_saved_ground_speed: dict[int, float] = {}


def _sync_movement_camera_need() -> None:
    try:
        from . import camera_tick
    except Exception:
        return
    camera_tick.set_needed("infinite_jump", bool(_INFINITE_JUMP_INDICES))
    camera_tick.set_needed(
        "super_dash",
        bool(
            _super_dash_enabled
            or _azzy_super_dash_enabled
            or _pending_msbt_super_dash
            or _pending_azzy_super_dash
            or _pending_dash_stop_jump_at
        ),
    )


def _register_super_dash_hook() -> None:
    try:
        from . import camera_tick

        camera_tick.register("super_dash", _super_dash_camera_hook, priority=20)
    except Exception as exc:
        _log(f"Super Dash camera hook skipped: {exc!r}")


_register_super_dash_hook()


def _pawn_addr_key(pawn: Any) -> int:
    try:
        return int(pawn._get_address())
    except Exception:
        return id(pawn)


def _read_numeric_attr(obj: Any, name: str) -> float | None:
    try:
        if not hasattr(obj, name):
            return None
        current = getattr(obj, name, None)
        if current is None:
            return None
        for field in ("Value", "BaseValue", "CurrentValue"):
            try:
                val = getattr(current, field, None)
                if val is not None:
                    return float(val)
            except Exception:
                pass
        return float(current)
    except Exception:
        return None


def _current_ground_speed(pawn: Any) -> float:
    for obj in _movement_objects_for_pawn(pawn):
        for attr in ("MinAnalogWalkSpeed", "MaxWalkSpeed", "MaxGroundSpeed"):
            val = _read_numeric_attr(obj, attr)
            if val is not None and val > 1.0:
                return val
    return 600.0


def _remember_ground_speed(pawn: Any) -> None:
    key = _pawn_addr_key(pawn)
    if key not in _saved_ground_speed:
        _saved_ground_speed[key] = _current_ground_speed(pawn)


def _restore_ground_speed(pawn: Any) -> int:
    saved = _saved_ground_speed.pop(_pawn_addr_key(pawn), None)
    if saved is None:
        return 0
    wrote = 0
    for obj in _movement_objects_for_pawn(pawn):
        wrote += _apply_speed_to_obj(obj, 1.0, saved)
    return wrote


def _move_comp_for_pawn(pawn: Any) -> Any | None:
    if pawn is None:
        return None
    for obj in _movement_objects_for_pawn(pawn):
        try:
            name = type(obj).__name__
        except Exception:
            name = ""
        try:
            text = str(obj)
        except Exception:
            text = ""
        if "Movement" in name or "Movement" in text:
            return obj
    return None


def _clamp_fly_speed(speed: float | None) -> float:
    raw = _DEFAULT_FLY_SPEED if speed is None else float(speed)
    return max(100.0, min(20000.0, raw))


def _write_fly_numeric(obj: Any, name: str, value: float) -> bool:
    """One-shot Gbx/float write. Never used from a tick hook."""
    try:
        if not hasattr(obj, name):
            return False
        current = getattr(obj, name, None)
    except Exception:
        return False
    wrote = False
    if current is not None:
        for field in (
            "Value",
            "BaseValue",
            "CurrentValue",
            "Base",
            "Current",
            "BaseValueConstant",
        ):
            try:
                setattr(current, field, float(value))
                wrote = True
            except Exception:
                pass
        for field in ("BaseValueScale", "ValueScale", "Scale"):
            try:
                setattr(current, field, 1.0)
                wrote = True
            except Exception:
                pass
        for method_name in ("SetValue", "SetBaseValue", "SetCurrentValue"):
            try:
                method = getattr(current, method_name, None)
                if callable(method):
                    method(float(value))
                    wrote = True
            except Exception:
                pass
    if wrote:
        return True
    try:
        setattr(obj, name, float(value))
        return True
    except Exception:
        return False


def _dump_fly_move(pawn: Any) -> None:
    move = _move_comp_for_pawn(pawn)
    if move is None:
        _log("fly dump: no movement component")
        return
    bits: list[str] = []
    try:
        bits.append(f"cls={type(move).__name__}")
    except Exception:
        bits.append("cls=?")
    try:
        bits.append(f"mode={int(move.MovementMode)}")
    except Exception:
        bits.append("mode=?")
    for name in (
        "MaxFlySpeed",
        "MaxFlyingSpeed",
        "FlySpeed",
        "MaxWalkSpeed",
        "MinAnalogWalkSpeed",
        "MaxCustomMovementSpeed",
        "MaxAcceleration",
        "BrakingDecelerationFlying",
        "AirControl",
        "GravityScale",
    ):
        val = _read_numeric_attr(move, name)
        if val is not None:
            bits.append(f"{name}={val:.1f}")
    try:
        fn = getattr(move, "GetMaxSpeed", None)
        if callable(fn):
            bits.append(f"GetMaxSpeed()={float(fn()):.1f}")
    except Exception:
        bits.append("GetMaxSpeed=err")
    try:
        bits.append(f"IsFlying={bool(move.IsFlying())}")
    except Exception:
        pass
    _log("fly dump: " + " ".join(bits))


def _disarm_fly_speed_override() -> None:
    global _MSBT_FLYING
    _MSBT_FLYING = False


def _write_fly_speed_to_pawn(pawn: Any, speed: float) -> int:
    """Write fly/walk/accel fields once. Do not re-apply from a frame hook."""
    target = _clamp_fly_speed(speed)
    wrote = 0
    for obj in _movement_objects_for_pawn(pawn):
        wrote += _apply_speed_to_obj(obj, 1.0, target)
        for attr in _FLY_SPEED_FIELDS:
            if _write_fly_numeric(obj, attr, target):
                wrote += 1
        for meth in ("SetMaxFlySpeed", "SetMaxFlyingSpeed", "SetMaxCustomMovementSpeed"):
            if _call_setter(obj, meth, target):
                wrote += 1
        if _write_fly_numeric(obj, "AirControl", 1.0):
            wrote += 1
        if _write_fly_numeric(obj, "AirControlBoostMultiplier", 4.0):
            wrote += 1
    _dump_fly_move(pawn)
    return wrote


def _apply_flight_to_pawn(
    pawn: Any,
    *,
    flying: bool,
    noclip: bool,
    fly_speed: float | None = None,
) -> bool:
    move = _move_comp_for_pawn(pawn)
    if pawn is None:
        return False
    wrote_speed = 0
    if flying and fly_speed is not None:
        _remember_ground_speed(pawn)
        wrote_speed = _write_fly_speed_to_pawn(pawn, fly_speed)
    if flying:
        if noclip:
            try:
                setattr(pawn, "bCanBeDamaged", False)
            except Exception:
                pass
            try:
                setattr(pawn, "bActorEnableCollision", False)
            except Exception:
                pass
        else:
            try:
                setattr(pawn, "bActorEnableCollision", True)
            except Exception:
                pass
        try:
            setattr(pawn, "bCheatFlying", True)
        except Exception:
            pass
        if move is not None:
            try:
                move.SetMovementMode(5, 0)  # MOVE_Flying
            except Exception:
                pass
        return move is not None or wrote_speed > 0
    try:
        setattr(pawn, "bActorEnableCollision", True)
    except Exception:
        pass
    try:
        setattr(pawn, "bCheatFlying", False)
    except Exception:
        pass
    if move is not None:
        try:
            move.SetMovementMode(1, 0)  # MOVE_Walking
        except Exception:
            pass
    try:
        setattr(pawn, "bCanBeDamaged", True)
    except Exception:
        pass
    _restore_ground_speed(pawn)
    return True


def set_noclip(enabled: bool, scope: str = "all", fly_speed: float | None = None) -> str:
    """Toggle flying + no-collision for Local / All / Others."""
    global _MSBT_FLYING
    speed = _clamp_fly_speed(fly_speed)
    pawns = filter_pawns_by_scope(live_player_pawns(), scope)
    if not pawns:
        return f"Noclip skipped: no pawns for scope={scope}."
    ok = 0
    writes = 0
    for pawn in pawns:
        if _apply_flight_to_pawn(pawn, flying=bool(enabled), noclip=True, fly_speed=speed):
            ok += 1
            writes += _write_fly_speed_to_pawn(pawn, speed) if enabled else 0
    _MSBT_FLYING = bool(enabled)
    state = "On" if enabled else "Off"
    msg = f"Noclip {state} for {ok}/{len(pawns)} pawn(s) (scope={scope}, speed={speed:.0f}, writes={writes})."
    _log(msg)
    return msg


def set_force_fly(enabled: bool, scope: str = "all", fly_speed: float | None = None) -> str:
    """Toggle flying with collision left on (fun fly, not ghost). Honors movement scope."""
    global _MSBT_FLYING
    speed = _clamp_fly_speed(fly_speed)
    pawns = filter_pawns_by_scope(live_player_pawns(), scope)
    if not pawns:
        return f"Force fly skipped: no pawns for scope={scope}."
    ok = 0
    writes = 0
    for pawn in pawns:
        if _apply_flight_to_pawn(pawn, flying=bool(enabled), noclip=False, fly_speed=speed):
            ok += 1
            writes += _write_fly_speed_to_pawn(pawn, speed) if enabled else 0
    _MSBT_FLYING = bool(enabled)
    state = "On" if enabled else "Off"
    msg = f"Force fly {state} for {ok}/{len(pawns)} pawn(s) (scope={scope}, speed={speed:.0f}, writes={writes})."
    _log(msg)
    return msg


def set_fly_speed(scope: str = "all", fly_speed: float | None = None) -> str:
    """Write fly speed once. Works while already flying (MSBT or Bonk noclip)."""
    speed = _clamp_fly_speed(fly_speed)
    pawns = filter_pawns_by_scope(live_player_pawns(), scope)
    if not pawns:
        return f"Fly speed skipped: no pawns for scope={scope}."
    ok = 0
    writes = 0
    for pawn in pawns:
        _remember_ground_speed(pawn)
        n = _write_fly_speed_to_pawn(pawn, speed)
        writes += n
        if n:
            ok += 1
    msg = f"Fly speed {speed:.0f} written for {ok}/{len(pawns)} pawn(s) (scope={scope}, writes={writes})."
    _log(msg)
    return msg


def _actor_location(actor: Any) -> Any | None:
    if actor is None:
        return None
    for meth in ("K2_GetActorLocation", "GetActorLocation"):
        try:
            fn = getattr(actor, meth, None)
            if callable(fn):
                loc = fn()
                if loc is not None:
                    return loc
        except Exception:
            pass
    try:
        root = getattr(actor, "RootComponent", None)
        if root is not None:
            for meth in ("K2_GetComponentLocation", "GetComponentLocation"):
                try:
                    fn = getattr(root, meth, None)
                    if callable(fn):
                        loc = fn()
                        if loc is not None:
                            return loc
                except Exception:
                    pass
            for attr in ("ComponentLocation", "RelativeLocation"):
                try:
                    loc = getattr(root, attr, None)
                    if loc is not None:
                        return loc
                except Exception:
                    pass
    except Exception:
        pass
    for attr in ("ActorLocation", "Location"):
        try:
            loc = getattr(actor, attr, None)
            if loc is not None and not callable(loc):
                return loc
        except Exception:
            pass
    return None


def _actor_rotation(actor: Any) -> Any | None:
    if actor is None:
        return None
    for meth in ("K2_GetActorRotation", "GetActorRotation"):
        try:
            fn = getattr(actor, meth, None)
            if callable(fn):
                rot = fn()
                if rot is not None:
                    return rot
        except Exception:
            pass
    try:
        root = getattr(actor, "RootComponent", None)
        if root is not None:
            for attr in ("ComponentRotation", "RelativeRotation"):
                try:
                    rot = getattr(root, attr, None)
                    if rot is not None:
                        return rot
                except Exception:
                    pass
    except Exception:
        pass
    return None

def teleport_pawn_to_pawn(source_pawn: Any, target_pawn: Any) -> str:
    if source_pawn is None or target_pawn is None:
        return "Teleport failed: missing source or target pawn."
    loc = _actor_location(target_pawn)
    if loc is None:
        return "Teleport failed: target location unavailable."
    rot = _actor_rotation(target_pawn)

    collision_was_enabled = None
    try:
        collision_was_enabled = bool(getattr(source_pawn, "bActorEnableCollision"))
    except Exception:
        pass
    try:
        try:
            source_pawn.SetActorEnableCollision(False)
        except Exception:
            try:
                source_pawn.bActorEnableCollision = False
            except Exception:
                pass

        # Prefer native teleport; it is the same style used by the debug-camera
        # teleport path and does not require a writable Location property.
        for call in ("K2_TeleportTo", "TeleportTo"):
            try:
                fn = getattr(source_pawn, call, None)
                if callable(fn):
                    if rot is not None:
                        ok = fn(loc, rot)
                    else:
                        ok = fn(loc, _actor_rotation(source_pawn))
                    return f"Teleported selected player via {call}; ok={ok}."
            except Exception:
                pass

        for call in ("K2_SetActorLocation", "SetActorLocation"):
            try:
                fn = getattr(source_pawn, call, None)
                if callable(fn):
                    try:
                        ok = fn(loc, False, None, False)
                    except TypeError:
                        try:
                            ok = fn(loc, False, None)
                        except TypeError:
                            ok = fn(loc)
                    if rot is not None:
                        try:
                            rfn = getattr(source_pawn, "K2_SetActorRotation", None) or getattr(source_pawn, "SetActorRotation", None)
                            if callable(rfn):
                                try:
                                    rfn(rot, False)
                                except TypeError:
                                    rfn(rot)
                        except Exception:
                            pass
                    return f"Teleported selected player via {call}; ok={ok}."
            except Exception:
                pass

        root = getattr(source_pawn, "RootComponent", None)
        if root is not None:
            for attr in ("ComponentLocation", "RelativeLocation"):
                try:
                    setattr(root, attr, loc)
                    return f"Teleported selected player by RootComponent.{attr}."
                except Exception:
                    pass
        return "Teleport failed: no usable teleport/location setter on source pawn."
    finally:
        try:
            if collision_was_enabled is not None:
                source_pawn.SetActorEnableCollision(collision_was_enabled)
        except Exception:
            try:
                if collision_was_enabled is not None:
                    source_pawn.bActorEnableCollision = collision_was_enabled
            except Exception:
                pass
