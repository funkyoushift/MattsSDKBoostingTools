"""Player movement adjustment helpers for Matt's SDK Boosting Tools.

These helpers intentionally use broad, defensive reflection because BL4 movement
properties vary between pawn/controller/movement-component wrappers.  All writes
are best-effort and skip class defaults.
"""
from __future__ import annotations

import time
from typing import Any

from mods_base import ENGINE, get_pc, hook
import unrealsdk
from unrealsdk import logging

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
    "MaxFlySpeed",
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
_INFINITE_JUMP_CONTEXT_CACHE: list[tuple[int, str, Any, Any | None]] = []
_INFINITE_JUMP_CONTEXT_CACHE_TIME: float = 0.0




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
    if obj is None:
        return True
    try:
        if "Default__" in str(obj):
            return True
    except Exception:
        pass
    try:
        cls = getattr(obj, "Class", None)
        cdo = getattr(cls, "ClassDefaultObject", None) if cls is not None else None
        if cdo is not None and obj is cdo:
            return True
    except Exception:
        pass
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

    controllers = live_player_controllers()
    pawns = live_player_pawns()
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
    msg = f"Applied movement to {len(pawns)} player pawn(s), {len(controllers)} controller(s): speed {speed_scale:.2f}x, walk {walk_speed:.0f}, JumpGoal {jump_goal:.0f}, JumpZ {jump_velocity:.0f}, jump count {jump_count}, gravity {gravity_scale:.2f}, step {max_step_height:.0f}, floor angle {walkable_floor_angle:.1f}, glide {glide_speed:.0f}/{glide_boost:.0f}, vault cost {'unchanged' if vault_cost is None else vault_cost}. Writes: {writes}; jump writes: {jump_writes}."
    _log(msg)
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


_JUMP_REFRESH_OBJECT_CACHE: list[Any] = []
_JUMP_REFRESH_CACHE_TIME: float = 0.0


def _gentle_jump_refresh_objects() -> list[Any]:
    """Cached movement objects for the experimental multi-jump refresher.

    The build where multi-jump worked cleared every live jump counter frequently.
    The frame loss came from doing the expensive pawn/component discovery every
    render tick.  This keeps the same effective writes, but the UI throttles the
    call and this resolver caches targets briefly.
    """
    global _JUMP_REFRESH_OBJECT_CACHE, _JUMP_REFRESH_CACHE_TIME
    now = time.monotonic()
    if _JUMP_REFRESH_OBJECT_CACHE and now - float(_JUMP_REFRESH_CACHE_TIME) < 2.0:
        return [obj for obj in _JUMP_REFRESH_OBJECT_CACHE if obj is not None and not _is_default(obj)]
    try:
        objects = _all_movement_objects()
    except Exception:
        objects = []
    _JUMP_REFRESH_OBJECT_CACHE = objects[:]
    _JUMP_REFRESH_CACHE_TIME = now
    return objects


def refresh_jump_counts_all_players() -> str:
    if not _is_listen_host_safe():
        msg = "Client mode — jump refresh skipped until you are host."
        _log(msg)
        return msg
    """Gentle experimental multi-jump support.

    This intentionally mirrors the earlier working behavior: clear live jump
    counters and transient pressed/jumping flags.  The performance fix is not to
    weaken the writes; it is to call this from a low-frequency gate and cache
    resolved movement components.
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
    try:
        if obj is None or not hasattr(obj, attr):
            return False
        try:
            if getattr(obj, attr) == value:
                return False
        except Exception:
            pass
        setattr(obj, attr, value)
        return True
    except Exception:
        return False


def _force_infinite_jump_ready(pawn: Any, move: Any | None = None) -> bool:
    if pawn is None or _is_default(pawn):
        return False
    try:
        move = move or _infinite_jump_move_for_pawn(pawn)
    except Exception:
        pass
    changed = False
    for attr, value in (
        ("JumpCurrentCount", 0),
        ("JumpCurrentCountPreJump", 0),
        ("JumpedCount", 0),
        ("CurrentJumpCount", 0),
        ("CurrentJumpCountPreJump", 0),
        ("JumpMaxCount", 999),
        ("JumpMaxCountPreJump", 999),
        ("bProxyIsJumpForceApplied", False),
        ("JumpKeyHoldTime", 0.0),
        ("JumpForceTimeRemaining", 0.0),
    ):
        if _set_if_needed(pawn, attr, value):
            changed = True
    if move is not None and not _is_default(move):
        for attr, value in (
            ("JumpedCount", 0),
            ("JumpCurrentCount", 0),
            ("JumpCurrentCountPreJump", 0),
            ("CurrentJumpCount", 0),
            ("CurrentJumpCountPreJump", 0),
            ("JumpMaxCount", 999),
            ("JumpMaxCountPreJump", 999),
        ):
            if _set_if_needed(move, attr, value):
                changed = True
    return changed


def _player_label_for_controller(idx: int, pc: Any | None) -> str:
    try:
        ps = getattr(pc, "PlayerState", None) if pc is not None else None
        for attr in ("PlayerName", "SavedNetworkAddress", "Name"):
            value = getattr(ps, attr, None) if ps is not None else None
            if value:
                return str(value)
    except Exception:
        pass
    return f"P{int(idx) + 1}"


def _infinite_jump_contexts(now: float | None = None) -> list[tuple[int, str, Any, Any | None]]:
    global _INFINITE_JUMP_CONTEXT_CACHE, _INFINITE_JUMP_CONTEXT_CACHE_TIME
    try:
        now = time.monotonic() if now is None else float(now)
    except Exception:
        now = 0.0
    try:
        if _INFINITE_JUMP_CONTEXT_CACHE and now - float(_INFINITE_JUMP_CONTEXT_CACHE_TIME) < 1.0:
            return [(idx, name, pawn, move) for idx, name, pawn, move in _INFINITE_JUMP_CONTEXT_CACHE if pawn is not None and not _is_default(pawn)]
    except Exception:
        pass
    contexts: list[tuple[int, str, Any, Any | None]] = []
    controllers = live_player_controllers()
    seen: set[str] = set()
    for idx, pc in enumerate(controllers):
        pawn = pawn_for_controller(pc)
        if pawn is None or _is_default(pawn):
            continue
        key = str(pawn)
        seen.add(key)
        contexts.append((idx, _player_label_for_controller(idx, pc), pawn, _infinite_jump_move_for_pawn(pawn)))
    for pawn in live_player_pawns():
        if pawn is None or _is_default(pawn):
            continue
        key = str(pawn)
        if key in seen:
            continue
        idx = len(contexts)
        seen.add(key)
        contexts.append((idx, f"P{idx + 1}", pawn, _infinite_jump_move_for_pawn(pawn)))
    _INFINITE_JUMP_CONTEXT_CACHE = list(contexts)
    _INFINITE_JUMP_CONTEXT_CACHE_TIME = now
    return contexts


def _enabled_infinite_jump_names() -> str:
    contexts = _infinite_jump_contexts()
    names = [name for idx, name, _pawn, _move in contexts if int(idx) in _INFINITE_JUMP_INDICES]
    return ", ".join(names) if names else "none"


def _hook_arg_to_pawn(obj: Any) -> Any | None:
    if obj is None or _is_default(obj):
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
        if pawn is not None and not _is_default(pawn):
            return pawn
    return obj if obj in live_player_pawns() else None


def _party_index_for_pawn(pawn: Any) -> int | None:
    if pawn is None:
        return None
    pawn_s = str(pawn)
    for idx, _name, ctx_pawn, _move in _infinite_jump_contexts():
        try:
            if ctx_pawn is pawn or str(ctx_pawn) == pawn_s:
                return int(idx)
        except Exception:
            pass
    return None


def _camera_infinite_jump_hook(*args, **kwargs):
    try:
        if not _INFINITE_JUMP_INDICES:
            return None
        touched: set[str] = set()
        for idx, _name, pawn, move in _infinite_jump_contexts():
            if int(idx) not in _INFINITE_JUMP_INDICES or pawn is None or _is_default(pawn):
                continue
            key = str(pawn)
            if key in touched:
                continue
            touched.add(key)
            _force_infinite_jump_ready(pawn, move)
    except Exception:
        pass
    return None


def _jump_pre_hook(*args, **kwargs):
    try:
        for obj in list(args) + list(kwargs.values()):
            pawn = _hook_arg_to_pawn(obj)
            if pawn is None:
                continue
            idx = _party_index_for_pawn(pawn)
            if idx is not None and int(idx) in _INFINITE_JUMP_INDICES:
                _force_infinite_jump_ready(pawn, _infinite_jump_move_for_pawn(pawn))
                break
    except Exception:
        pass
    return None


def _register_infinite_jump_hooks() -> None:
    try:
        hook(
            "/Script/Engine.CameraModifier:BlueprintModifyCamera",
            immediately_enable=True,
            hook_identifier="matts_sdk_boosting_tools_backend_infinite_jump_camera_v1",
        )(_camera_infinite_jump_hook)
        _log("Backend Infinite Jump camera hook installed.")
    except Exception as exc:
        _log(f"Backend Infinite Jump camera hook skipped: {exc!r}")
    targets = (
        "/Script/Engine.Character:CanJumpInternal",
        "/Script/Engine.Character:CanJump",
        "/Script/Engine.Character:Jump",
        "/Script/GbxGame.OakCharacter:CanJumpInternal",
        "/Script/GbxGame.OakCharacter:CanJump",
        "/Script/GbxGame.OakCharacter:Jump",
        "/Script/OakGame.OakCharacter:CanJumpInternal",
        "/Script/OakGame.OakCharacter:CanJump",
        "/Script/OakGame.OakCharacter:Jump",
    )
    for i, target in enumerate(targets):
        try:
            hook(
                target,
                immediately_enable=True,
                hook_identifier=f"matts_sdk_boosting_tools_backend_infinite_jump_gate_v1_{i}",
            )(_jump_pre_hook)
        except Exception as exc:
            _log(f"Backend Infinite Jump hook skipped {target}: {exc!r}")


def set_infinite_jump_all(enabled: bool) -> str:
    global _INFINITE_JUMP_CONTEXT_CACHE_TIME
    contexts = _infinite_jump_contexts(0.0)
    if enabled:
        _INFINITE_JUMP_INDICES.clear()
        for idx, _name, pawn, move in contexts:
            if pawn is not None and not _is_default(pawn):
                _INFINITE_JUMP_INDICES.add(int(idx))
                _force_infinite_jump_ready(pawn, move)
    else:
        _INFINITE_JUMP_INDICES.clear()
    _INFINITE_JUMP_CONTEXT_CACHE_TIME = 0.0
    msg = f"Infinite Jump enabled for: {_enabled_infinite_jump_names()}."
    _log(msg)
    return msg


def set_infinite_jump_for_index(idx: int, enabled: bool) -> str:
    global _INFINITE_JUMP_CONTEXT_CACHE_TIME
    idx = int(idx)
    if enabled:
        _INFINITE_JUMP_INDICES.add(idx)
    else:
        _INFINITE_JUMP_INDICES.discard(idx)
    _INFINITE_JUMP_CONTEXT_CACHE_TIME = 0.0
    for ctx_idx, _name, pawn, move in _infinite_jump_contexts(0.0):
        if int(ctx_idx) == idx and enabled:
            _force_infinite_jump_ready(pawn, move)
            break
    msg = f"Infinite Jump enabled for: {_enabled_infinite_jump_names()}."
    _log(msg)
    return msg


def toggle_infinite_jump_for_index(idx: int) -> str:
    idx = int(idx)
    return set_infinite_jump_for_index(idx, idx not in _INFINITE_JUMP_INDICES)


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


def delete_ground_items() -> str:
    try:
        jsfl = unrealsdk.find_class("JunkSystemFunctionLibrary").ClassDefaultObject
        box = unrealsdk.make_struct(
            "Box",
            MIN=unrealsdk.make_struct("Vector", X=-1000000.0, Y=-1000000.0, Z=-1000000.0),
            MAX=unrealsdk.make_struct("Vector", X=1000000.0, Y=1000000.0, Z=1000000.0),
        )
        jsfl.DestroyJunkWithinBounds(get_pc(), box)
        return "Ground items deleted."
    except Exception as exc:
        return f"Delete ground items failed: {exc!r}"


def set_noclip(enabled: bool) -> str:
    try:
        pc = get_pc()
        pawn = pawn_for_controller(pc) or getattr(pc, "OakCharacter", None) or getattr(pc, "Pawn", None)
        move = None
        if pawn is not None:
            for obj in _movement_objects_for_pawn(pawn):
                if "Movement" in type(obj).__name__ or "Movement" in str(obj):
                    move = obj; break
        if pawn is None or move is None:
            return "Noclip failed: no pawn/movement component found."
        if enabled:
            try: setattr(pawn, "bCanBeDamaged", False)
            except Exception: pass
            try: setattr(pawn, "bActorEnableCollision", False)
            except Exception: pass
            try:
                move.SetMovementMode(5, 0)  # MOVE_Flying
            except Exception:
                pass
            return "Noclip On."
        try: setattr(pawn, "bActorEnableCollision", True)
        except Exception: pass
        try:
            move.SetMovementMode(1, 0)  # MOVE_Walking
        except Exception:
            pass
        try: setattr(pawn, "bCanBeDamaged", True)
        except Exception: pass
        return "Noclip Off."
    except Exception as exc:
        return f"Noclip failed: {exc!r}"


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
