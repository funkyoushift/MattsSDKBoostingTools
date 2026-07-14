from __future__ import annotations

import argparse
import threading
import unicodedata
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import mods_base as _mods_base
from mods_base import ENGINE, CoopSupport, Game, build_mod, command, get_pc, keybind
from unrealsdk import find_all, find_class, find_object, logging, make_struct

_LOG_PREFIX = "[ActorScriptDeployer]"
_BUILD_TAG = "v29-special-char-support-2026-05-11"

_DEFAULT_DISTANCE = 350.0
_DEFAULT_Z_OFFSET = -100.0
_DEFAULT_SCALE = 1.0
_DEFAULT_DELAY = 1.0
_DEFAULT_ACTIVATE_ENABLE = ("Active", "ActiveIdle_Anim")
_DEFAULT_ACTIVATE_DISABLE = ("IsInUse", "InUse_Anim", "Dispensing_Anim")

# Extra states to try for objects whose script is not the Lost Loot script.
# Unknown states are harmless: SetScriptStateEnabled usually no-ops or raises, and
# failures are logged as warnings. Bank/locker-style objects commonly do not expose
# UpdateAnimState, so these names give ASD_spawn bank a broader activation pass.
_GENERIC_ENABLE_STATES = (
    "Active", "ActiveIdle", "ActiveIdle_Anim", "Enabled", "Enable", "Usable", "Useable",
    "Interactive", "InteractionEnabled", "Available", "Unlocked", "Idle",
    "Open", "Closed", "Bank", "PlayerBank", "Ready",
)
_GENERIC_DISABLE_STATES = (
    "IsInUse", "InUse_Anim", "Dispensing_Anim", "Disabled", "Disable",
    "Inactive", "Locked", "Blocked", "Unavailable",
)
_PRESET_ENABLE_STATES: Dict[str, Tuple[str, ...]] = {
    "bank": ("ActiveIdle", "Unlocked", "Available", "Enabled", "Usable", "Useable", "Interactive", "InteractionEnabled", "Active", "Idle"),
    "playerbank": ("ActiveIdle", "Unlocked", "Available", "Enabled", "Usable", "Useable", "Interactive", "InteractionEnabled", "Active", "Idle"),
    "player_bank": ("ActiveIdle", "Unlocked", "Available", "Enabled", "Usable", "Useable", "Interactive", "InteractionEnabled", "Active", "Idle"),
}
_PRESET_DISABLE_STATES: Dict[str, Tuple[str, ...]] = {
    "bank": ("Locked", "Disabled", "Inactive", "Blocked", "Unavailable", "IsInUse"),
    "playerbank": ("Locked", "Disabled", "Inactive", "Blocked", "Unavailable", "IsInUse"),
    "player_bank": ("Locked", "Disabled", "Inactive", "Blocked", "Unavailable", "IsInUse"),
}

# Known shortcuts. Lost Loot is confirmed from your working one-liner.
# For the other aliases, class_name may be None: the mod will discover a live
# template actor by scanning common actor-ish classes for the keyword.
_ALIASES: Dict[str, Tuple[Optional[str], Tuple[str, ...]]] = {
    "lostloot": ("OakLostLootMachine", ("OakLostLootMachine", "LostLoot", "Lost_Loot")),
    "lostlootmachine": ("OakLostLootMachine", ("OakLostLootMachine", "LostLoot", "Lost_Loot")),
    "lost_loot": ("OakLostLootMachine", ("OakLostLootMachine", "LostLoot", "Lost_Loot")),
    "golden": (None, ("GoldenChest", "Golden_Chest", "GoldChest", "Golden")),
    "goldenchest": (None, ("GoldenChest", "Golden_Chest", "GoldChest", "Golden")),
    "golden_chest": (None, ("GoldenChest", "Golden_Chest", "GoldChest", "Golden")),
    "firmware": (None, ("Firmware",)),
    "bank": (None, ("PlayerBank", "Player_Bank", "Bank")),
    "barrel": (None, ("Barrel", "ExplosiveBarrel", "Explosive_Barrel")),
    "barrels": (None, ("Barrel", "ExplosiveBarrel", "Explosive_Barrel")),
    "playerbank": (None, ("PlayerBank", "Player_Bank", "Bank")),
    "player_bank": (None, ("PlayerBank", "Player_Bank", "Bank")),
}

_CLASS_SCAN_ORDER: Tuple[str, ...] = (
    # Specific / likely deployables first. Missing classes are harmless.
    "OakLostLootMachine",
    "OakInteractiveObject",
    "OakInteractableObject",
    "OakUsableActor",
    "OakUseableActor",
    "OakMissionScriptedActor",
    "OakLootable",
    "OakLootableContainer",
    "OakChest",
    "OakActor",
    # Broad fallback. This can be larger, so it is intentionally last.
    "Actor",
)


@dataclass
class DeployedActor:
    label: str
    source: Any
    actor: Any
    actor_key: str = ""
    class_name: str = ""


_SPAWNED: List[DeployedActor] = []
# Runtime-only cache of FGbxDefPtr values discovered from live actors.
# These pointers cannot be reconstructed from strings in the current SDK, so
# cache while the source actor is loaded, then spawn later in the same session.
_ACTOR_DEF_CACHE: Dict[str, Any] = {}
_ACTOR_DEF_CACHE_SOURCE: Dict[str, str] = {}



def _option_text_value(option: Any, default: str) -> str:
    """Read a text option value across SDK option API variants."""
    if option is None:
        return default
    for attr in ("value", "current_value", "Value", "CurrentValue"):
        try:
            value = getattr(option, attr)
        except Exception:
            continue
        try:
            if callable(value):
                value = value()
        except Exception:
            pass
        if value is not None:
            text = _normalize_logo_row_text(str(value))
            if text:
                return text
    return _normalize_logo_row_text(default)


def _normalize_logo_row_text(text: str) -> str:
    """Normalize mod-menu/console logo text: trim and auto-uppercase."""
    return str(text or "").strip().upper()


def _option_float_value(option: Any, default: float) -> float:
    """Read a numeric option value across SDK option API variants."""
    if option is None:
        return float(default)
    for attr in ("value", "current_value", "Value", "CurrentValue"):
        try:
            value = getattr(option, attr)
        except Exception:
            continue
        try:
            if callable(value):
                value = value()
        except Exception:
            pass
        if value is not None:
            try:
                return float(value)
            except Exception:
                continue
    return float(default)


def _make_float_option(identifier: str, display_name: str, default: float, description: str, *, minimum: float = 0.0, maximum: float = 10000.0, increment: float = 50.0) -> Optional[Any]:
    """Create a persistent mod-menu numeric option when supported by this SDK build."""
    for class_name in ("SliderOption", "FloatOption", "SpinnerOption", "NumberOption", "NumericOption"):
        cls = getattr(_mods_base, class_name, None)
        if cls is None:
            continue
        attempts = (
            lambda: cls(identifier, default, minimum, maximum, increment, display_name=display_name, description=description),
            lambda: cls(identifier, default, min_value=minimum, max_value=maximum, increment=increment, display_name=display_name, description=description),
            lambda: cls(identifier, default, min_value=minimum, max_value=maximum, step=increment, name=display_name, description=description),
            lambda: cls(identifier, display_name, default, minimum, maximum, increment, description=description),
            lambda: cls(display_name, default, minimum, maximum, increment, description=description),
            lambda: cls(identifier, default, minimum, maximum, increment),
            lambda: cls(identifier, default),
        )
        for attempt in attempts:
            try:
                return attempt()
            except TypeError:
                continue
            except Exception:
                continue
    return None

_ValueOptionBase = getattr(_mods_base, "ValueOption", None)

if _ValueOptionBase is not None:
    @dataclass
    class LogoTextOption(_ValueOptionBase):  # type: ignore[misc]
        """Visible free-text mod-menu option for the console mod menu.

        mods_base itself only ships Bool/Slider/Spinner/Dropdown/Keybind/Button.
        There is no stock TextOption, so ASD provides this tiny ValueOption and
        patches console_mod_menu to open a free text input screen for it.
        """
        def _from_json(self, value: Any) -> None:
            self.value = _normalize_logo_row_text(str(value))
else:
    LogoTextOption = None  # type: ignore[assignment,misc]


def _make_text_option(identifier: str, display_name: str, default: str, description: str) -> Optional[Any]:
    """Create a visible free-text option backed by ASD's custom menu screen."""
    if LogoTextOption is None:
        return None
    try:
        return LogoTextOption(
            identifier=identifier,
            value=_normalize_logo_row_text(default),
            display_name=display_name,
            description=description,
        )
    except Exception as exc:
        try:
            logging.warning(f"{_LOG_PREFIX} LogoTextOption create failed for {identifier}: {exc}")
        except Exception:
            pass
        return None


def _install_logo_text_menu_support() -> None:
    """Teach console_mod_menu how to edit LogoTextOption values.

    Keybinds get a custom screen by patching the menu's option handler.  This does
    the same thing for row text: press the row option, type any text, press enter.
    The value is uppercased and saved immediately.
    """
    if LogoTextOption is None:
        return
    try:
        from dataclasses import dataclass as _dataclass, field as _field
        from console_mod_menu.draw import draw as _draw
        from console_mod_menu.option_formatting import draw_option_header as _draw_option_header
        from console_mod_menu.screens import (
            AbstractScreen as _AbstractScreen,
            draw_standard_commands as _draw_standard_commands,
            handle_standard_command_input as _handle_standard_command_input,
            push_screen as _push_screen,
        )
        from console_mod_menu.screens.mod import OptionListScreen as _OptionListScreen
    except Exception as exc:
        try:
            logging.warning(f"{_LOG_PREFIX} console_mod_menu text editor hook unavailable: {exc}")
        except Exception:
            pass
        return

    if getattr(_OptionListScreen, "_asd_logo_text_patched", False):
        return

    @_dataclass
    class _LogoTextOptionScreen(_AbstractScreen):  # type: ignore[misc]
        mod: Any
        option: Any
        name: str = _field(init=False)

        def __post_init__(self) -> None:
            self.name = self.option.display_name

        def draw(self) -> None:  # noqa: D102
            _draw_option_header(self.option)
            _draw("Type the new row text and press Enter.")
            _draw("Text is auto-capitalized. Leave blank to keep current value.")
            _draw("Example: we have been")
            _draw_standard_commands()

        def handle_input(self, line: str) -> bool:  # noqa: D102
            if _handle_standard_command_input(line):
                return True
            text = _normalize_logo_row_text(line)
            if not text:
                return False
            self.option.value = text
            try:
                self.mod.save_settings()
            except Exception as exc:
                try:
                    logging.warning(f"{_LOG_PREFIX} failed saving logo text option: {exc}")
                except Exception:
                    pass
            return True

    _orig_handle_option_input = _OptionListScreen.handle_option_input

    def _asd_handle_option_input(self: Any, line: str) -> bool:
        try:
            option = self.drawn_options[int(line) - 1]
        except (ValueError, IndexError):
            return _orig_handle_option_input(self, line)
        if isinstance(option, LogoTextOption):
            _push_screen(_LogoTextOptionScreen(self.mod, option))
            return True
        return _orig_handle_option_input(self, line)

    _OptionListScreen.handle_option_input = _asd_handle_option_input
    _OptionListScreen._asd_logo_text_patched = True  # type: ignore[attr-defined]




def _make_spinner_option(identifier: str, display_name: str, choices: Sequence[str], default: str, description: str) -> Optional[Any]:
    """Create a persistent dropdown/choice option when this SDK exposes one.

    Some current Oak/BL4 builds do not expose a free-text mod-menu option, which
    is why the row text fields were missing while the numeric distance slider
    worked.  Spinner/dropdown options are much more widely available, so the row
    defaults use these as a reliable in-menu fallback.  Console text remains
    fully free-form via ASD_barrellogo.
    """
    values = tuple(str(v) for v in choices)
    if default not in values:
        values = (default,) + values
    for class_name in (
        "SpinnerOption", "DropdownOption", "DropDownOption", "ChoiceOption",
        "SelectOption", "SelectionOption", "EnumOption",
    ):
        cls = getattr(_mods_base, class_name, None)
        if cls is None:
            continue
        attempts = (
            lambda: cls(identifier, default, values, display_name=display_name, description=description),
            lambda: cls(identifier, default, choices=values, display_name=display_name, description=description),
            lambda: cls(identifier, default, options=values, display_name=display_name, description=description),
            lambda: cls(identifier, default, values=values, display_name=display_name, description=description),
            lambda: cls(identifier, display_name, default, values, description=description),
            lambda: cls(display_name, default, values, description=description),
            lambda: cls(identifier, default, values),
        )
        for attempt in attempts:
            try:
                return attempt()
            except TypeError:
                continue
            except Exception:
                continue
    return None


def _log_info(message: str) -> None:
    logging.info(f"{_LOG_PREFIX} {message}")


def _log_warn(message: str) -> None:
    logging.warning(f"{_LOG_PREFIX} {message}")


def _log_error(message: str) -> None:
    logging.error(f"{_LOG_PREFIX} {message}")


def _unwrap(value: Any) -> Any:
    return value[0] if isinstance(value, (list, tuple)) else value


def _pawn(pc: Any) -> Any:
    for attr in ("OakCharacter", "Pawn", "AcknowledgedPawn"):
        try:
            pawn = getattr(pc, attr, None)
        except Exception:
            pawn = None
        if pawn is not None:
            return pawn
    return None


def _world_from_pc(pc: Any) -> Any:
    try:
        gv = getattr(ENGINE, "GameViewport", None)
        world = getattr(gv, "World", None) if gv is not None else None
        if world is not None:
            return world
    except Exception:
        pass
    try:
        return getattr(pc, "World", None)
    except Exception:
        return None


def _gameplay_statics() -> Any:
    try:
        return find_object("GameplayStatics", "/Script/Engine.Default__GameplayStatics")
    except Exception:
        try:
            return find_class("GameplayStatics").ClassDefaultObject
        except Exception as exc:
            _log_error(f"GameplayStatics lookup failed: {exc}")
            return None


def _spawn_context() -> Tuple[Optional[Any], Optional[Any], Optional[Any], Optional[Any]]:
    pc = get_pc()
    if pc is None:
        _log_error("No PlayerController.")
        return None, None, None, None
    pawn = _pawn(pc)
    if pawn is None:
        _log_error("No Pawn / OakCharacter.")
        return pc, None, None, None
    world = _world_from_pc(pc)
    if world is None:
        _log_error("No World.")
        return pc, pawn, None, None
    gs = _gameplay_statics()
    return pc, pawn, world, gs


def _spawn_transform(pawn: Any, *, distance: float, z_offset: float, scale: float) -> Any:
    return _spawn_transform_for_index(
        pawn,
        index=0,
        count=1,
        distance=distance,
        spacing=0.0,
        z_offset=z_offset,
        scale=scale,
    )


def _spawn_transform_for_index(
    pawn: Any,
    *,
    index: int,
    count: int,
    distance: float,
    spacing: float,
    z_offset: float,
    scale: float,
) -> Any:
    """ADA-style row placement: center multiple spawned actors in front of the player."""
    loc = pawn.K2_GetActorLocation()
    fwd = pawn.GetActorForwardVector()
    total = max(1, int(count))
    offset = (float(index) - (float(total) - 1.0) / 2.0) * float(spacing)
    return make_struct(
        "Transform",
        Rotation=make_struct("Quat", X=0.0, Y=0.0, Z=0.0, W=1.0),
        Translation=make_struct(
            "Vector",
            X=float(loc.X + fwd.X * distance - fwd.Y * offset),
            Y=float(loc.Y + fwd.Y * distance + fwd.X * offset),
            Z=float(loc.Z + z_offset),
        ),
        Scale3D=make_struct("Vector", X=float(scale), Y=float(scale), Z=float(scale)),
    )


def _spawn_actor_deferred(
    gs: Any,
    world: Any,
    cls: Any,
    transform: Any,
    *,
    class_name: str = "Actor",
    source: Optional[Any] = None,
    collision_handling: int = 1,
) -> Optional[Any]:
    """Spawn an actor with the safer ADA deferred-spawn wrapper.

    If a source template is provided, copy its actor data before FinishSpawningActor so
    script/deployable actors initialize with the same data as their live template.
    """
    try:
        raw = gs.BeginDeferredActorSpawnFromClass(world, cls, transform, int(collision_handling), None, 1)
        actor = _unwrap(raw)
    except Exception as exc:
        _log_error(f"BeginDeferredActorSpawnFromClass failed for {class_name}: {exc}")
        return None
    if actor is None:
        _log_error("BeginDeferredActorSpawnFromClass returned None.")
        return None

    if source is not None:
        _copy_actor_data(source, actor)

    try:
        raw2 = gs.FinishSpawningActor(actor, transform, 0)
        return _unwrap(raw2)
    except Exception as exc:
        _log_error(f"FinishSpawningActor failed for {class_name}: {exc}")
        return None



def _actor_mesh(actor: Any) -> Any:
    """ADA-style mesh lookup for non-deployable actors such as OakWeapon."""
    for attr in ("Mesh", "CharacterMesh", "SkeletalMeshComponent", "GbxSkeletalMeshComponent", "MeshComponent"):
        try:
            mesh = getattr(actor, attr, None)
        except Exception:
            mesh = None
        if mesh is not None:
            return mesh
    for cls_path in ("/Script/OakGame.GbxSkeletalMeshComponent", "/Script/Engine.SkeletalMeshComponent"):
        try:
            cls = find_object("Class", cls_path)
            mesh = actor.GetComponentByClass(cls)
        except Exception:
            mesh = None
        if mesh is not None:
            return mesh
    return None


def _mesh_asset_for_kind(mesh: Any) -> Any:
    for attr in ("SkeletalMesh", "SkinnedAsset"):
        try:
            asset = getattr(mesh, attr, None)
        except Exception:
            asset = None
        if asset is not None:
            return asset
    return None


def _set_skeletal_mesh_asset(mesh: Any, mesh_asset: Any) -> None:
    for func_name in ("SetSkeletalMeshAsset", "SetSkeletalMesh"):
        func = getattr(mesh, func_name, None)
        if callable(func):
            func(mesh_asset)
            return
    raise RuntimeError("No skeletal mesh setter found")


def _material_at(comp: Any, index: int) -> Any:
    try:
        return comp.GetMaterial(int(index))
    except Exception:
        return None


def _copy_material_slots(src_mesh: Any, dst_mesh: Any, max_slots: int = 64) -> int:
    copied = 0
    for idx in range(max_slots):
        mat = _material_at(src_mesh, idx)
        if mat is None:
            continue
        try:
            dst_mesh.SetMaterial(idx, mat)
            copied += 1
        except Exception:
            pass
    return copied


def _show_actor_mesh(actor: Any, mesh: Any) -> None:
    try:
        actor.SetActorHiddenInGame(False)
    except Exception:
        pass
    try:
        mesh.SetHiddenInGame(False, True)
    except Exception:
        pass
    try:
        mesh.SetVisibility(True, True)
    except Exception:
        pass


def _refresh_component(component: Any) -> None:
    for func_name in ("RegisterComponent", "RecreatePhysicsState", "UpdateBounds", "MarkRenderDynamicDataDirty"):
        func = getattr(component, func_name, None)
        if callable(func):
            try:
                func()
            except Exception:
                pass


def _spawn_skeletal_mesh_actor(gs: Any, world: Any, transform: Any) -> Optional[Any]:
    try:
        actor_cls = find_object("Class", "/Script/Engine.SkeletalMeshActor")
    except Exception as exc:
        _log_warn(f"SkeletalMeshActor class lookup failed: {exc}")
        return None
    return _spawn_actor_deferred(gs, world, actor_cls, transform, class_name="SkeletalMeshActor", source=None, collision_handling=2)


def _find_generic_skeletal_source(name: str, generated_only: bool = True) -> Optional[Any]:
    """Find any live actor by name that has a skeletal mesh, mirroring ADA's generic source path."""
    needles = [n.lower() for n in _default_class_and_needles(name)[1] if n]
    scan_classes = ("OakWeapon", "OakInventory", "OakActor", "Actor")
    for allow_non_generated in ((not generated_only), True):
        for class_name in scan_classes:
            try:
                actors = list(find_all(class_name, False))
            except TypeError:
                try:
                    actors = list(find_all(class_name))
                except Exception:
                    continue
            except Exception:
                continue
            for actor in actors:
                try:
                    text = str(actor)
                except Exception:
                    continue
                low = text.lower()
                if "/script/" in low or "default__" in low:
                    continue
                if generated_only and not allow_non_generated and "_generated_" not in low:
                    continue
                if needles and not any(n in low for n in needles):
                    continue
                mesh = _actor_mesh(actor)
                if mesh is not None and _mesh_asset_for_kind(mesh) is not None:
                    return actor
    return None


def _spawn_generic_skeletal_duplicate(
    name: str,
    *,
    source: Any,
    distance: float,
    z_offset: float,
    scale: float,
    count: int,
    spacing: float,
) -> Optional[Any]:
    _, pawn, world, gs = _spawn_context()
    if pawn is None or world is None or gs is None:
        return None
    src_mesh = _actor_mesh(source)
    mesh_asset = _mesh_asset_for_kind(src_mesh)
    if src_mesh is None or mesh_asset is None:
        _log_error(f"{name}: generic source has no usable skeletal mesh.")
        return None
    _log_info(f"Using generic skeletal source {source}.")
    total = max(1, int(count))
    first_actor: Optional[Any] = None
    spawned = 0
    for idx in range(total):
        transform = _spawn_transform_for_index(pawn, index=idx, count=total, distance=distance, spacing=spacing, z_offset=z_offset, scale=scale)
        actor = _spawn_skeletal_mesh_actor(gs, world, transform)
        if actor is None:
            continue
        dst_mesh = _actor_mesh(actor)
        if dst_mesh is None:
            _destroy_actor(actor)
            continue
        try:
            _set_skeletal_mesh_asset(dst_mesh, mesh_asset)
            _copy_material_slots(src_mesh, dst_mesh, max_slots=64)
            _show_actor_mesh(actor, dst_mesh)
            _refresh_component(dst_mesh)
        except Exception as exc:
            _destroy_actor(actor)
            _log_warn(f"{name}: generic skeletal setup failed: {exc}")
            continue
        _SPAWNED.append(DeployedActor(label=name, source=source, actor=actor, actor_key=_actor_key(actor), class_name=_class_name(actor)))
        if first_actor is None:
            first_actor = actor
        spawned += 1
        _log_info(f"Spawned {name.lower()} generic skeletal duplicate {idx + 1}/{total}: {actor}")
    if spawned <= 0:
        _log_error(f"{name}: no generic skeletal actors spawned.")
        return None
    _log_info(f"Sampler: spawned {spawned}/{total} type=actor name={name!r} kind=single parts=0 distance={distance:g}uu")
    return first_actor

def _alias_key(name: str) -> str:
    return name.strip().lower().replace(" ", "").replace("-", "_")


def _default_class_and_needles(name: str) -> Tuple[Optional[str], Tuple[str, ...]]:
    key = _alias_key(name)
    if key in _ALIASES:
        return _ALIASES[key]
    return None, (name.strip(),)


def _safe_find_class(class_name: str) -> Optional[Any]:
    try:
        return find_class(class_name)
    except Exception as exc:
        _log_warn(f"Class lookup failed for {class_name!r}: {exc}")
        return None


def _candidate_sources(class_name: str, needles: Sequence[str], generated_only: bool = True) -> List[Any]:
    try:
        found = list(find_all(class_name, False))
    except TypeError:
        try:
            found = list(find_all(class_name))
        except Exception as exc:
            _log_warn(f"find_all({class_name!r}) failed: {exc}")
            return []
    except Exception as exc:
        _log_warn(f"find_all({class_name!r}) failed: {exc}")
        return []

    lowered = [n.lower() for n in needles if n]
    out: List[Any] = []
    for obj in found:
        text = str(obj)
        low = text.lower()
        if generated_only and "_generated_" not in low:
            continue
        if lowered and not any(n in low for n in lowered):
            continue
        if "/script/" in low or "default__" in low:
            continue
        out.append(obj)
    return out


def _class_display_name(cls: Any) -> str:
    try:
        return str(cls).rsplit(".", 1)[-1].strip("'")
    except Exception:
        return repr(cls)


def _source_class(source: Any, fallback_class_name: Optional[str] = None) -> Optional[Any]:
    try:
        cls = getattr(source, "Class", None)
        if cls is not None:
            return cls
    except Exception:
        pass
    if fallback_class_name:
        return _safe_find_class(fallback_class_name)
    return None


def _candidate_sources_multi(class_names: Sequence[str], needles: Sequence[str], generated_only: bool = True) -> List[Tuple[str, Any]]:
    out: List[Tuple[str, Any]] = []
    seen: set[str] = set()
    for class_name in class_names:
        for obj in _candidate_sources(class_name, needles, generated_only=generated_only):
            key = str(obj)
            if key in seen:
                continue
            seen.add(key)
            out.append((class_name, obj))
    return out


def _find_template(name: str, class_override: Optional[str] = None, generated_only: bool = True) -> Tuple[Optional[Any], Optional[Any], Optional[str]]:
    default_class, needles = _default_class_and_needles(name)
    class_name = class_override or default_class

    # Fast path when a class is known or supplied.
    if class_name:
        cls = _safe_find_class(class_name)
        if cls is not None:
            matches = _candidate_sources(class_name, needles, generated_only=generated_only)
            if not matches and generated_only:
                matches = _candidate_sources(class_name, needles, generated_only=False)
            if matches:
                return cls, matches[0], class_name
            _log_warn(f"No live template found in class={class_name!r}; falling back to keyword class scan.")
        else:
            _log_warn(f"Class {class_name!r} is not loaded/valid; falling back to keyword class scan.")

    # Discovery path for things like Golden Chest / Firmware where the class name
    # changes or is not obvious. Spawn with the matched source actor's own Class.
    scan_classes = []
    if class_name:
        scan_classes.append(class_name)
    scan_classes.extend(c for c in _CLASS_SCAN_ORDER if c not in scan_classes)
    matches = _candidate_sources_multi(scan_classes, needles, generated_only=generated_only)
    if not matches and generated_only:
        _log_info("No _Generated_ matches; retrying non-generated keyword scan.")
        matches = _candidate_sources_multi(scan_classes, needles, generated_only=False)
    if not matches:
        _log_error(f"No live template found for name={name!r} needles={needles}. Try ASD_targets {name} --include-non-generated or ASD_spawn {name} --class <known class>.")
        return None, None, class_name

    matched_class_name, source = matches[0]
    cls = _source_class(source, matched_class_name)
    if cls is None:
        _log_error(f"Matched source but could not read/spawn its Class: {source}")
        return None, source, matched_class_name
    _log_info(f"Discovered template via class={matched_class_name!r}: {source}")
    return cls, source, matched_class_name


def _copy_actor_data(source: Any, actor: Any) -> None:
    try:
        src_data = getattr(source, "GbxActorData", None)
        dst_data = getattr(actor, "GbxActorData", None)
    except Exception:
        return
    if src_data is None or dst_data is None:
        return

    # This is the critical line from the console one-liner.  Keep it narrow first.
    for field_name in ("GbxActorDef", "ActorPartList", "ActorPartSelections", "SpawnDetails"):
        try:
            value = getattr(src_data, field_name)
        except Exception:
            continue
        try:
            setattr(dst_data, field_name, value)
            _log_info(f"Copied GbxActorData.{field_name}.")
        except Exception:
            pass



def _destroy_actor(actor: Any) -> None:
    for func_name in ("K2_DestroyActor", "DestroyActor", "Destroy"):
        func = getattr(actor, func_name, None)
        if callable(func):
            try:
                func()
                return
            except Exception:
                pass

def _script_instance(actor: Any) -> Optional[Any]:
    try:
        instances = actor.ScriptData.Instances
    except Exception:
        return None
    try:
        if len(instances):
            return instances[0]
    except Exception:
        pass
    return None


def _unique_states(*groups: Sequence[str]) -> Tuple[str, ...]:
    out: List[str] = []
    seen: set[str] = set()
    for group in groups:
        for state in group:
            if not state or state in seen:
                continue
            seen.add(state)
            out.append(state)
    return tuple(out)




def _source_schema_enable_states(source: Any) -> Tuple[str, ...]:
    """Return script states implied by a template actor's GbxActorDef schema.

    Player bank proved that usability can be gated by a schema state named
    MachineState whose usable value is ActiveIdle.  The normal broad activation
    pass enabled Active/ActiveIdle_Anim, but not ActiveIdle itself.  Keep this
    helper defensive: if any of the experimental fields are missing, it simply
    returns no extra states.
    """
    try:
        gbx_def = source.GbxActorData.GbxActorDef
        schema = gbx_def._experimental_instance.actorstateschema._experimental_instance
        machines = schema.StateMachines
    except Exception:
        return ()

    out: List[str] = []
    for machine in machines:
        try:
            machine_name = str(machine.Name)
            states = [str(state) for state in machine.States]
        except Exception:
            continue
        low_name = machine_name.lower()
        low_states = {state.lower(): state for state in states}
        # PlayerBank: MachineState has Inactive/ActiveIdle, and use responses
        # select on MachineState.  Enabling ActiveIdle makes the normal prompt
        # usable without firing the OnUsed event directly.
        if low_name == "machinestate" and "activeidle" in low_states:
            out.append(low_states["activeidle"])
        # Bool actor-state machines often use FALSE as the non-busy/default
        # state.  This is harmless for scripts that do not expose it.
        if getattr(machine, "bIsBool", False):
            false_state = low_states.get("false")
            if false_state:
                out.append(false_state)
    return tuple(out)


def _script_instances(actor: Any) -> List[Any]:
    try:
        instances = actor.ScriptData.Instances
    except Exception:
        return []
    try:
        return [instances[i] for i in range(len(instances))]
    except Exception:
        try:
            return list(instances)
        except Exception:
            return []


def _call_if_present(obj: Any, names: Sequence[str], *args: Any) -> None:
    for name in names:
        try:
            fn = getattr(obj, name, None)
        except Exception:
            fn = None
        if not callable(fn):
            continue
        try:
            fn(*args)
            _log_info(f"called {name} on {obj}")
        except TypeError:
            # Some Unreal wrappers expose overloads with different signatures.
            try:
                fn()
                _log_info(f"called {name}() on {obj}")
            except Exception as exc:
                _log_warn(f"{name} failed: {exc}")
        except Exception as exc:
            _log_warn(f"{name} failed: {exc}")


def _poke_actor_enabled(actor: Any) -> None:
    for name, args in (
        ("SetActorHiddenInGame", (False,)),
        ("SetActorEnableCollision", (True,)),
        ("SetActorTickEnabled", (True,)),
    ):
        _call_if_present(actor, (name,), *args)
    for comp_name in ("RootComponent", "Mesh", "StaticMeshComponent", "CollisionComponent", "InteractionComponent", "UseComponent"):
        try:
            comp = getattr(actor, comp_name, None)
        except Exception:
            comp = None
        if comp is None:
            continue
        _call_if_present(comp, ("SetHiddenInGame",), False, True)
        _call_if_present(comp, ("SetVisibility",), True, True)
        _call_if_present(comp, ("SetComponentTickEnabled",), True)
        _call_if_present(comp, ("SetCollisionEnabled",), 1)
        _call_if_present(comp, ("SetGenerateOverlapEvents",), True)


def _script_debug(inst: Any, limit: int = 60) -> None:
    names = []
    for name in dir(inst):
        low = name.lower()
        if any(token in low for token in ("state", "enable", "active", "usable", "use", "interact", "bank", "anim", "open", "lock")):
            names.append(name)
    _log_info(f"script={inst} useful_attrs={names[:limit]}")


def _set_script_states(actor: Any, enable: Sequence[str], disable: Sequence[str], *, debug: bool = False) -> None:
    instances = _script_instances(actor)
    _log_info(f"scripts={len(instances)} actor={actor}")
    _poke_actor_enabled(actor)
    if not instances:
        _log_warn("No ScriptData.Instances found; actor spawned but was not script-activated.")
        return
    for inst in instances:
        if debug:
            _script_debug(inst)
        for state in disable:
            try:
                inst.SetScriptStateEnabled(state, False)
                _log_info(f"disabled script state {state!r}")
            except Exception as exc:
                _log_warn(f"disable {state!r} failed: {exc}")
        for state in enable:
            try:
                inst.SetScriptStateEnabled(state, True)
                _log_info(f"enabled script state {state!r}")
            except Exception as exc:
                _log_warn(f"enable {state!r} failed: {exc}")
        _call_if_present(inst, (
            "UpdateAnimState", "UpdateState", "RefreshState", "Refresh",
            "Activate", "Enable", "SetEnabled", "SetUsable", "SetUseable",
            "SetInteractionEnabled", "SetInteractive",
        ), True)


def _split_states(value: Optional[str], defaults: Sequence[str]) -> Tuple[str, ...]:
    if value is None:
        return tuple(defaults)
    return tuple(part.strip() for part in value.split(",") if part.strip())



def _actor_def_name(def_ptr: Any) -> str:
    """Best-effort stable display name for an FGbxDefPtr."""
    for attr in ("_experimental_name", "Name", "name"):
        try:
            value = getattr(def_ptr, attr, None)
        except Exception:
            value = None
        if value:
            return str(value)
    try:
        text = str(def_ptr)
        if "FGbxDefPtr(" in text and "'" in text:
            return text.split("'", 2)[1]
        return text
    except Exception:
        return ""


def _candidate_actor_def_sources(query: str, *, class_override: Optional[str] = None) -> List[Any]:
    """Find live objects with GbxActorData.GbxActorDef matching a query.

    This is intentionally broader than _find_template: AI actor defs often live
    on OakCharacter sources that are not _Generated_ and may have display names
    such as Char_NPC_Mancubus.
    """
    needles = [query.lower()]
    key = _alias_key(query)
    if key in _ALIASES:
        needles.extend(n.lower() for n in _ALIASES[key][1] if n)
    classes: List[str] = []
    if class_override:
        classes.append(class_override)
    for cls_name in ("OakCharacter", "OakPawn", "OakActor", "Actor"):
        if cls_name not in classes:
            classes.append(cls_name)
    out: List[Any] = []
    seen: set[str] = set()
    for cls_name in classes:
        try:
            objects = list(find_all(cls_name, False))
        except TypeError:
            try:
                objects = list(find_all(cls_name))
            except Exception:
                continue
        except Exception:
            continue
        for obj in objects:
            text = str(obj).lower()
            if "default__" in text or "/script/" in text:
                continue
            try:
                def_ptr = obj.GbxActorData.GbxActorDef
            except Exception:
                continue
            def_name = _actor_def_name(def_ptr).lower()
            haystack = text + " " + def_name
            if needles and not any(n in haystack for n in needles):
                continue
            key_obj = str(obj)
            if key_obj in seen:
                continue
            seen.add(key_obj)
            out.append(obj)
    return out


def _cache_actor_def(alias: str, source: Any) -> bool:
    try:
        def_ptr = source.GbxActorData.GbxActorDef
    except Exception as exc:
        _log_error(f"{source} does not expose GbxActorData.GbxActorDef: {exc}")
        return False
    cache_key = _alias_key(alias)
    _ACTOR_DEF_CACHE[cache_key] = def_ptr
    _ACTOR_DEF_CACHE_SOURCE[cache_key] = str(source)
    _log_info(f"cached actor def {cache_key!r}: {_actor_def_name(def_ptr)} from {source}")
    return True


def _cache_actor_def_from_spawned_actor(alias: str, actor: Any) -> bool:
    """Cache the real GbxActorDef from a successfully spawned actor.

    Direct shell-based spawns can work once, but later calls may fail because the
    synthetic shell no longer resolves cleanly.  A live spawned actor contains the
    real GbxActorData.GbxActorDef, so save it immediately for future calls.
    """
    if actor is None:
        return False
    if _is_spawner_like(actor):
        _log_warn(f"auto-cache skipped spawner-like delta object for {alias!r}: {actor}")
        return False
    try:
        def_ptr = actor.GbxActorData.GbxActorDef
    except Exception as exc:
        _log_warn(f"auto-cache failed for {alias!r}: spawned actor has no GbxActorData.GbxActorDef: {exc}")
        return False

    if def_ptr is None:
        _log_warn(f"auto-cache failed for {alias!r}: spawned actor GbxActorDef is None")
        return False

    cache_key = _alias_key(alias)
    _ACTOR_DEF_CACHE[cache_key] = def_ptr
    _ACTOR_DEF_CACHE_SOURCE[cache_key] = f"auto-spawned:{actor}"
    _log_info(f"auto-cached actor def {cache_key!r}: {_actor_def_name(def_ptr)} from spawned actor {actor}")
    return True



def _nearest_oak_spawners(pawn: Any, limit: int = 8) -> List[Any]:
    try:
        pl = pawn.K2_GetActorLocation()
    except Exception:
        pl = None
    spawners: List[Tuple[float, Any]] = []
    try:
        objects = list(find_all("OakSpawner", False))
    except TypeError:
        try:
            objects = list(find_all("OakSpawner"))
        except Exception as exc:
            _log_error(f"find_all('OakSpawner') failed: {exc}")
            return []
    except Exception as exc:
        _log_error(f"find_all('OakSpawner') failed: {exc}")
        return []
    for sp in objects:
        low = str(sp).lower()
        if "default__" in low or "/script/" in low:
            continue
        dist = 0.0
        if pl is not None:
            try:
                loc = sp.K2_GetActorLocation()
                dx, dy, dz = float(loc.X - pl.X), float(loc.Y - pl.Y), float(loc.Z - pl.Z)
                dist = (dx * dx + dy * dy + dz * dz) ** 0.5
            except Exception:
                dist = 999999999.0
        spawners.append((dist, sp))
    spawners.sort(key=lambda item: item[0])
    return [sp for _, sp in spawners[: max(1, int(limit))]]


def _alive_actors_for_spawner_component(comp: Any) -> List[Any]:
    for args in ((0, False), (0, True)):
        try:
            actors = comp.GetAliveActors(*args)
            try:
                return [actors[i] for i in range(len(actors))]
            except Exception:
                return list(actors)
        except Exception:
            continue
    return []


def _poll_spawner_for_alive_actors(
    comp: Any,
    *,
    timeout: float = 3.0,
    interval: float = 0.15,
) -> List[Any]:
    """Poll a spawner after ResetSpawner because BL4/Oak spawning can be async.

    Some valid actor defs report resolved=True immediately, but GetAliveActors()
    is still empty for a few frames. The old ASD_spawnai path checked once and
    falsely reported failure. This waits briefly for the spawner to finish.
    """
    deadline = time.monotonic() + max(0.0, float(timeout))
    last_actors: List[Any] = []

    while True:
        actors = _alive_actors_for_spawner_component(comp)
        if actors:
            return actors
        last_actors = actors

        try:
            if int(comp.GetNumAliveActors(0)) > 0:
                actors = _alive_actors_for_spawner_component(comp)
                if actors:
                    return actors
        except Exception:
            pass

        if time.monotonic() >= deadline:
            return last_actors

        time.sleep(max(0.01, float(interval)))


def _spawner_counts(comp: Any) -> Tuple[int, int, int, int]:
    """Best-effort OakSpawner count tuple: alive, spawned, dead, total."""
    out: List[int] = []
    for fn_name in ("GetNumAliveActors", "GetNumSpawnedActors", "GetNumDeadActors", "GetNumTotalActors"):
        try:
            out.append(int(getattr(comp, fn_name)(0)))
        except Exception:
            out.append(-1)
    return out[0], out[1], out[2], out[3]



def _apply_spawnai_actor_transform(actor: Any, transform: Any, pawn: Any, *, scale: float, z_offset: float) -> bool:
    """Apply ASD_spawnai placement directly inside ASD.

    OakSpawner thin-air spawns sometimes return actors at a native row location
    instead of respecting the duplicated spawner transform.  This makes --zoffset
    and --scale deterministic for returned actors while keeping the placement
    logic inside ActorScriptDeployer rather than in the debug menu.
    """
    if actor is None:
        return False
    try:
        loc = transform.Translation
    except Exception:
        loc = None
    try:
        rot = pawn.K2_GetActorRotation()
    except Exception:
        rot = None

    moved = False
    if loc is not None and rot is not None:
        moved = _try_teleport_actor(actor, loc, rot)
    elif loc is not None:
        try:
            actor.K2_SetActorLocation(loc, False, None, True)
            moved = True
        except Exception:
            try:
                actor.SetActorLocation(loc, False, None, True)
                moved = True
            except Exception:
                moved = False

    scaled = False
    if float(scale) != 1.0:
        try:
            actor.SetActorScale3D(make_struct("Vector", X=float(scale), Y=float(scale), Z=float(scale)))
            scaled = True
        except Exception as exc:
            _log_warn(f"ASD_spawnai SetActorScale3D failed for {actor}: {exc}")

    if moved or scaled:
        _log_info(f"ASD_spawnai applied transform actor={actor} moved={moved} scale={scale:g} z_offset={z_offset:g}")
    return moved or scaled


def _try_teleport_actor(actor: Any, loc: Any, rot: Any) -> bool:
    moved = False
    try:
        moved = bool(actor.K2_TeleportTo(loc, rot))
    except Exception:
        moved = False
    if not moved:
        try:
            actor.RootComponent.RelativeLocation = loc
            moved = True
        except Exception:
            pass
    try:
        cm = getattr(actor, "CharacterMovement", None)
        if cm is not None and hasattr(cm, "StopMovementImmediately"):
            cm.StopMovementImmediately()
    except Exception:
        pass
    return moved




def _duplicate_oak_spawner_at(source_spawner: Any, transform: Any, *, index: int = 0) -> Optional[Any]:
    """Duplicate/spawn a fresh OakSpawner actor near the target transform.

    Existing world spawners can be encounter-owned, exhausted, cooldown-blocked,
    or otherwise unsuitable after one use. For --count N, fresh spawner actors give
    each requested spawn its own isolated spawner state.
    """
    if source_spawner is None:
        return None

    _pc, _pawn, world, gs = _spawn_context()
    if world is None or gs is None:
        return None

    try:
        cls = getattr(source_spawner, "Class", None)
    except Exception:
        cls = None
    if cls is None:
        try:
            cls = find_class("OakSpawner")
        except Exception as exc:
            _log_warn(f"duplicate spawner {index}: OakSpawner class lookup failed: {exc}")
            return None

    spawner = _spawn_actor_deferred(
        gs,
        world,
        cls,
        transform,
        class_name="OakSpawner",
        source=source_spawner,
        collision_handling=2,
    )
    if spawner is None:
        _log_warn(f"duplicate spawner {index}: spawn failed")
        return None

    # Ensure the duplicate is usable and not hidden/disabled.
    _poke_actor_enabled(spawner)

    try:
        comp = spawner.GetSpawnerComponent()
        for fn_name, args in (
            ("SetSpawnerEnabled", (True,)),
            ("SetSpawnPointEnabled", (True,)),
        ):
            try:
                getattr(comp, fn_name)(*args)
            except Exception:
                pass
    except Exception as exc:
        _log_warn(f"duplicate spawner {index}: component prep failed: {exc}")

    _log_info(f"duplicated OakSpawner {index}: source={source_spawner} duplicate={spawner}")
    return spawner


def _spawners_for_direct_count(
    pawn: Any,
    *,
    count: int,
    distance: float,
    spacing: float,
) -> List[Any]:
    """Return count isolated spawners by duplicating nearest OakSpawner when possible."""
    total = max(1, int(count))
    source_spawners = _nearest_oak_spawners(pawn, limit=max(1, min(8, total)))
    if not source_spawners:
        return []

    out: List[Any] = []
    source = source_spawners[0]

    for idx in range(total):
        transform = _spawn_transform_for_index(
            pawn,
            index=idx,
            count=total,
            distance=distance,
            spacing=spacing,
            z_offset=0.0,
            scale=1.0,
        )
        dup = _duplicate_oak_spawner_at(source, transform, index=idx + 1)
        if dup is not None:
            out.append(dup)

    if len(out) < total:
        _log_warn(
            f"duplicated {len(out)}/{total} OakSpawners; falling back to existing spawners for remaining slots"
        )
        existing = _nearest_oak_spawners(pawn, limit=total)
        for sp in existing:
            if len(out) >= total:
                break
            out.append(sp)

    return out[:total]





def _is_spawner_like(obj: Any) -> bool:
    """Return True for OakSpawner / spawn helper actors that must not count as spawned AI."""
    try:
        cls = getattr(obj, "Class", None)
        cls_text = str(cls or "")
    except Exception:
        cls_text = ""
    try:
        obj_text = str(obj or "")
    except Exception:
        obj_text = ""

    low = (cls_text + " " + obj_text).lower()
    return (
        "oakspawner" in low
        or ".spawner" in low
        or "spawner_" in low
        or "spawnpoint" in low
    )


def _has_actor_def_data(obj: Any) -> bool:
    """Best-effort check for actors that can expose a real GbxActorDef."""
    try:
        return getattr(obj.GbxActorData, "GbxActorDef", None) is not None
    except Exception:
        return False

def _actor_location(actor: Any) -> Optional[Any]:
    try:
        return actor.K2_GetActorLocation()
    except Exception:
        return None


def _distance_sq(a: Any, b: Any) -> float:
    try:
        dx = float(a.X - b.X)
        dy = float(a.Y - b.Y)
        dz = float(a.Z - b.Z)
        return dx * dx + dy * dy + dz * dz
    except Exception:
        return 999999999999.0


def _world_actor_snapshot() -> set[str]:
    """Snapshot currently loaded non-default actors for world-delta spawn detection."""
    seen: set[str] = set()
    for cls_name in ("OakCharacter", "OakPawn", "OakActor", "Actor"):
        try:
            objs = list(find_all(cls_name, False))
        except TypeError:
            try:
                objs = list(find_all(cls_name))
            except Exception:
                continue
        except Exception:
            continue
        for obj in objs:
            low = str(obj).lower()
            if "default__" in low or "/script/" in low:
                continue
            if _is_spawner_like(obj):
                continue
            seen.add(str(obj))
    return seen


def _find_new_world_actors_near(
    before: set[str],
    loc: Any,
    *,
    radius: float = 4000.0,
    expected_name: str = "",
) -> List[Any]:
    """Find actors that appeared after spawn but were not reported by GetAliveActors.

    Some OakSpawner paths spawn valid actors but do not attach them to the spawner's
    alive list. This catches those actors by scanning the world after spawning.
    """
    radius_sq = float(radius) * float(radius)
    needles = [n.lower() for n in _default_class_and_needles(expected_name)[1] if n]
    out: List[Any] = []
    seen: set[str] = set()

    for cls_name in ("OakCharacter", "OakPawn", "OakActor", "Actor"):
        try:
            objs = list(find_all(cls_name, False))
        except TypeError:
            try:
                objs = list(find_all(cls_name))
            except Exception:
                continue
        except Exception:
            continue

        for obj in objs:
            key = str(obj)
            if key in before or key in seen:
                continue
            low = key.lower()
            if "default__" in low or "/script/" in low:
                continue
            if _is_spawner_like(obj):
                continue

            obj_loc = _actor_location(obj)
            if obj_loc is not None and loc is not None:
                if _distance_sq(obj_loc, loc) > radius_sq:
                    continue

            # Prefer matching names, but do not require it because generated actors
            # may use generic runtime names.
            if needles and any(n in low for n in needles):
                out.insert(0, obj)
            else:
                out.append(obj)
            seen.add(key)

    out.sort(key=lambda actor: 0 if _has_actor_def_data(actor) else 1)
    return out

def _spawn_cached_actor_def(
    name: str,
    *,
    distance: float,
    z_offset: float = 0.0,
    scale: float = 1.0,
    count: int = 1,
    spacing: float = 125.0,
) -> Optional[Any]:
    cache_key = _alias_key(name)
    def_ptr = _ACTOR_DEF_CACHE.get(cache_key)
    if def_ptr is None:
        return None
    _log_info(f"using cached actor def {cache_key!r}: {_actor_def_name(def_ptr)}")
    _, pawn, _world, _gs = _spawn_context()
    if pawn is None:
        return None
    spawners = _nearest_oak_spawners(pawn, limit=max(3, int(count) + 1))
    if not spawners:
        _log_error(f"No live OakSpawner found for cached actor-def spawn {name!r}.")
        return None

    # v10 direct path spawner duplication is applied in ASD_spawnai direct function.

    first_actor: Optional[Any] = None
    total_spawned = 0
    for idx in range(max(1, int(count))):
        sp = spawners[idx % len(spawners)]
        try:
            comp = sp.GetSpawnerComponent()
        except Exception as exc:
            _log_warn(f"{sp}: GetSpawnerComponent failed: {exc}")
            continue
        before = set()
        for actor in _alive_actors_for_spawner_component(comp):
            before.add(str(actor))
        world_before = _world_actor_snapshot()
        try:
            comp.DestroyAllActors()
        except Exception:
            pass
        try:
            comp.PushActorDef("ASD", def_ptr, True)
        except Exception as exc:
            _log_error(f"PushActorDef failed for cached {cache_key!r} ({_actor_def_name(def_ptr)}): {exc}")
            return None
        for fn_name, args in (("SetSpawnerEnabled", (True,)), ("SetSpawnPointEnabled", (True,))):
            try:
                getattr(comp, fn_name)(*args)
            except Exception as exc:
                _log_warn(f"{fn_name} failed on {comp}: {exc}")
        try:
            comp.ResetSpawner(True)
        except TypeError:
            try:
                comp.ResetSpawner()
            except Exception as exc:
                _log_warn(f"ResetSpawner failed on {comp}: {exc}")
                continue
        except Exception as exc:
            _log_warn(f"ResetSpawner failed on {comp}: {exc}")
            continue

        actors = [a for a in _alive_actors_for_spawner_component(comp) if str(a) not in before] or _alive_actors_for_spawner_component(comp)
        target_transform = _spawn_transform_for_index(pawn, index=idx, count=max(1, int(count)), distance=distance, spacing=spacing, z_offset=z_offset, scale=scale)
        loc = target_transform.Translation
        try:
            rot = pawn.K2_GetActorRotation()
        except Exception:
            rot = None
        for actor in actors:
            if rot is not None:
                moved = _try_teleport_actor(actor, loc, rot)
            else:
                moved = False
            if float(scale) != 1.0:
                try:
                    actor.SetActorScale3D(make_struct("Vector", X=float(scale), Y=float(scale), Z=float(scale)))
                except Exception as exc:
                    _log_warn(f"cached ASD_spawnai SetActorScale3D failed for {actor}: {exc}")
            try:
                actor_loc = actor.K2_GetActorLocation()
            except Exception:
                actor_loc = None
            try:
                scripts = len(actor.ScriptData.Instances)
            except Exception:
                scripts = -1
            _SPAWNED.append(DeployedActor(label=name, source=sp, actor=actor, actor_key=_actor_key(actor), class_name=_class_name(actor)))
            _log_info(f"cached spawn {idx + 1}/{max(1, int(count))}: actor={actor} loc={actor_loc} moved={moved} scripts={scripts} spawner={sp}")
            if first_actor is None:
                first_actor = actor
            total_spawned += 1
    if total_spawned <= 0:
        _log_error(f"Cached actor def {cache_key!r} was found, but no alive actors were returned by spawners.")
        return None
    return first_actor

def _spawn_deployed_actor(
    name: str,
    *,
    class_override: Optional[str],
    distance: float,
    z_offset: float,
    scale: float,
    delay: float,
    enable: Sequence[str],
    disable: Sequence[str],
    generated_only: bool,
    activate: bool,
    count: int = 1,
    spacing: float = 125.0,
) -> Optional[Any]:
    _, pawn, world, gs = _spawn_context()
    if pawn is None or world is None or gs is None:
        return None

    cls, source, class_name = _find_template(name, class_override, generated_only=generated_only)
    if cls is None or source is None:
        generic_source = _find_generic_skeletal_source(name, generated_only=generated_only)
        if generic_source is not None:
            return _spawn_generic_skeletal_duplicate(
                name,
                source=generic_source,
                distance=distance,
                z_offset=z_offset,
                scale=scale,
                count=count,
                spacing=spacing,
            )
        return None

    # If the matched source is not a deployable/OakCharacter-style actor but does
    # have a skeletal mesh, use ADA's generic SkeletalMeshActor duplicate path.
    if _actor_mesh(source) is not None and _mesh_asset_for_kind(_actor_mesh(source)) is not None:
        low_class = str(class_name or _class_name(source)).lower()
        if "oakweapon" in low_class or "skeletal" in str(source).lower():
            return _spawn_generic_skeletal_duplicate(
                name,
                source=source,
                distance=distance,
                z_offset=z_offset,
                scale=scale,
                count=count,
                spacing=spacing,
            )

    total = max(1, int(count))
    first_actor: Optional[Any] = None
    spawned = 0
    for idx in range(total):
        transform = _spawn_transform_for_index(
            pawn,
            index=idx,
            count=total,
            distance=distance,
            spacing=spacing,
            z_offset=z_offset,
            scale=scale,
        )
        actor = _spawn_actor_deferred(gs, world, cls, transform, class_name=class_name, source=source, collision_handling=1)
        if actor is None:
            continue

        _SPAWNED.append(DeployedActor(label=name, source=source, actor=actor, actor_key=_actor_key(actor), class_name=_class_name(actor)))
        _log_info(f"spawned {idx + 1}/{total} name={name!r} class={class_name} actor={actor} source={source}")
        if first_actor is None:
            first_actor = actor
        spawned += 1

        if activate:
            key = _alias_key(name)
            final_enable = _unique_states(enable, _PRESET_ENABLE_STATES.get(key, ()), _source_schema_enable_states(source), _GENERIC_ENABLE_STATES)
            final_disable = _unique_states(disable, _PRESET_DISABLE_STATES.get(key, ()), _GENERIC_DISABLE_STATES)
            threading.Timer(
                max(0.0, float(delay)),
                lambda actor=actor: _set_script_states(actor, final_enable, final_disable, debug=True),
            ).start()

    if spawned <= 0:
        _log_error(f"{name}: no actors spawned.")
        return None
    return first_actor


def _spawn_from_args(args: argparse.Namespace, name: Optional[str] = None) -> None:
    target = name or str(getattr(args, "name", "") or "").strip()
    if not target:
        _log_error("Usage: ASD_spawn <name> [--class ClassName]")
        return
    actor = _spawn_deployed_actor(
        target,
        class_override=getattr(args, "class_name", None),
        distance=float(getattr(args, "distance", _DEFAULT_DISTANCE)),
        z_offset=float(getattr(args, "z_offset", _DEFAULT_Z_OFFSET)),
        scale=float(getattr(args, "scale", _DEFAULT_SCALE)),
        delay=float(getattr(args, "delay", _DEFAULT_DELAY)),
        enable=_split_states(getattr(args, "enable", None), _DEFAULT_ACTIVATE_ENABLE),
        disable=_split_states(getattr(args, "disable", None), _DEFAULT_ACTIVATE_DISABLE),
        generated_only=not bool(getattr(args, "include_non_generated", False)),
        activate=not bool(getattr(args, "no_activate", False)),
        count=int(getattr(args, "count", 1)),
        spacing=float(getattr(args, "spacing", 125.0)),
    )
    if actor is not None:
        _log_info(f"Deployment complete: {actor}")


# 5x7 pixel font for barrel-logo spawning.  # marks spawn cells.
_FONT_5X7: Dict[str, Tuple[str, ...]] = {
    "A": (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    "C": (" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"),
    "D": ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    "F": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    "G": (" ####", "#    ", "#    ", "#  ##", "#   #", "#   #", " ####"),
    "H": ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "I": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"),
    "J": ("#####", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "),
    "K": ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    "L": ("#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"),
    "M": ("#   #", "## ##", "# # #", "#   #", "#   #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"),
    "O": (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "P": ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    "Q": (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    "R": ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    "S": (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "V": ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "W": ("#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"),
    "X": ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    "Y": ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
    "0": (" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "),
    "1": ("  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", "#####"),
    "2": (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    "3": ("#### ", "    #", "    #", " ### ", "    #", "    #", "#### "),
    "4": ("#   #", "#   #", "#   #", "#####", "    #", "    #", "    #"),
    "5": ("#####", "#    ", "#    ", "#### ", "    #", "    #", "#### "),
    "6": (" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "),
    "7": ("#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "),
    "8": (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    "9": (" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "),
    
    ".": (" ", " ", " ", " ", " ", "##", "##"),
    ",": (" ", " ", " ", " ", "##", "##", "# "),
    "!": (" # ", " # ", " # ", " # ", " # ", "   ", " # "),
    "?": ("###", "   #", "  # ", " #  ", " #  ", "    ", " #  "),
    ":": (" ", "##", "##", " ", "##", "##", " "),
    ";": (" ", "##", "##", " ", "##", "##", "# "),
    "-": ("     ", "     ", "     ", "#####", "     ", "     ", "     "),
    "_": ("     ", "     ", "     ", "     ", "     ", "     ", "#####"),
    "+": ("     ", "  #  ", "  #  ", "#####", "  #  ", "  #  ", "     "),
    "/": ("    #", "   # ", "   # ", "  #  ", " #   ", " #   ", "#    "),
    "\\": ("#    ", " #   ", " #   ", "  #  ", "   # ", "   # ", "    #"),
    "@": (" ### ", "#   #", "# ###", "# # #", "# ###", "#    ", " ####"),
    "#": (" # # ", "#####", " # # ", " # # ", "#####", " # # ", "     "),
    "$": (" ### ", "# #  ", "# #  ", " ### ", "  # #", "  # #", " ### "),
    "%": ("##  #", "## # ", "  #  ", " #   ", "# ## ", "#  ##", "     "),
    "&": (" ##  ", "#  # ", "# #  ", " ## #", "#  # ", "#  # ", " ## #"),
    "(": ("  ##", " #  ", "#   ", "#   ", "#   ", " #  ", "  ##"),
    ")": ("##  ", "  # ", "   #", "   #", "   #", "  # ", "##  "),
    "[": ("####", "#   ", "#   ", "#   ", "#   ", "#   ", "####"),
    "]": ("####", "   #", "   #", "   #", "   #", "   #", "####"),
    "*": ("     ", "# # #", " ### ", "#####", " ### ", "# # #", "     "),
    "=": ("     ", "#####", "     ", "#####", "     ", "     ", "     "),
    "<": ("   ##", "  #  ", " #   ", "#    ", " #   ", "  #  ", "   ##"),
    ">": ("##   ", "  #  ", "   # ", "    #", "   # ", "  #  ", "##   "),
" ": ("   ", "   ", "   ", "   ", "   ", "   ", "   "),
}
_LOGO_TEXT = "JOIN|GZO|DISCORD"
_LOGO_ROW1_DEFAULT = "JOIN"
_LOGO_ROW2_DEFAULT = "GZO"
_LOGO_ROW3_DEFAULT = "DISCORD"
_LOGO_DISTANCE_DEFAULT = 1400.0
_LOGO_ACTOR_DEFAULT = "barrel"
_LOGO_ROW_CHOICES: Tuple[str, ...] = (
    "", "JOIN", "GZO", "DISCORD",
    "WE HAVE BEEN", "TRYING TO REACH YOU", "ABOUT YOUR CARS EXTENDED WARRENTY",
    "ABOUT YOUR CARS EXTENDED WARRANTY", "SUBSCRIBE", "LIKE AND FOLLOW", "WELCOME",
)
_LOGO_ROW1_OPTION = _make_text_option(
    "asd_logo_row_1",
    "Logo Text Row 1",
    _LOGO_ROW1_DEFAULT,
    "Free-text first row used by the ASD Spawn Barrel Logo keybind. Input is auto-capitalized.",
)
_LOGO_ROW2_OPTION = _make_text_option(
    "asd_logo_row_2",
    "Logo Text Row 2",
    _LOGO_ROW2_DEFAULT,
    "Free-text second row used by the ASD Spawn Barrel Logo keybind. Input is auto-capitalized.",
)
_LOGO_ROW3_OPTION = _make_text_option(
    "asd_logo_row_3",
    "Logo Text Row 3",
    _LOGO_ROW3_DEFAULT,
    "Free-text third row used by the ASD Spawn Barrel Logo keybind. Input is auto-capitalized.",
)
_LOGO_DISTANCE_OPTION = _make_float_option(
    "asd_logo_distance",
    "Barrel Logo Distance",
    _LOGO_DISTANCE_DEFAULT,
    "Permanent forward distance used by the ASD Spawn Barrel Logo keybind and by ASD_barrellogo when --distance is omitted.",
    minimum=100.0,
    maximum=5000.0,
    increment=50.0,
)
_LOGO_ACTOR_OPTION = _make_text_option(
    "asd_logo_actor",
    "Logo Actor Override",
    _LOGO_ACTOR_DEFAULT,
    "Free-text template keyword used by the ASD Spawn Barrel Logo keybind. Examples: barrel, goldenchest, firmware, bank. Blank/default uses barrel.",
)
_LOGO_OPTIONS = [
    opt for opt in (
        _LOGO_ROW1_OPTION, _LOGO_ROW2_OPTION, _LOGO_ROW3_OPTION,
        _LOGO_DISTANCE_OPTION, _LOGO_ACTOR_OPTION,
    ) if opt is not None
]
_LOGO_COLORS: Tuple[Tuple[float, float, float, float], ...] = (
    (0.0, 0.75, 1.0, 1.0),   # cyan/blue
    (1.0, 0.0, 1.0, 1.0),    # magenta
    (1.0, 0.16, 0.05, 1.0),  # red/orange
    (1.0, 0.55, 0.0, 1.0),   # orange
)


def _vector(x: float, y: float, z: float) -> Any:
    return make_struct("Vector", X=float(x), Y=float(y), Z=float(z))


def _transform_at(x: float, y: float, z: float, scale: float) -> Any:
    return make_struct(
        "Transform",
        Rotation=make_struct("Quat", X=0.0, Y=0.0, Z=0.0, W=1.0),
        Translation=_vector(x, y, z),
        Scale3D=_vector(scale, scale, scale),
    )


def _text_pixels(text: str) -> Tuple[List[Tuple[int, int, int]], int, int]:
    pixels: List[Tuple[int, int, int]] = []
    cursor = 0
    height = 7

    # Normalize unicode characters into a closest ASCII representation
    normalized_text = unicodedata.normalize("NFKD", text or "")
    normalized_text = normalized_text.encode("ascii", "ignore").decode("ascii")

    for char_index, char in enumerate(normalized_text.upper()):
        glyph = _FONT_5X7.get(char, _FONT_5X7.get("?", _FONT_5X7[" "]))
        width = max(len(row) for row in glyph)
        if char == " ":
            cursor += width + 2
            continue
        for y, row in enumerate(glyph):
            for x, cell in enumerate(row):
                if cell != " ":
                    pixels.append((cursor + x, y, char_index))
        cursor += width + 1
    return pixels, max(0, cursor - 1), height


def _logo_text_from_options() -> str:
    row1 = _option_text_value(_LOGO_ROW1_OPTION, _LOGO_ROW1_DEFAULT)
    row2 = _option_text_value(_LOGO_ROW2_OPTION, _LOGO_ROW2_DEFAULT)
    row3 = _option_text_value(_LOGO_ROW3_OPTION, _LOGO_ROW3_DEFAULT)
    rows = [row.strip() for row in (row1, row2, row3) if row and row.strip()]
    return "|".join(rows) if rows else _LOGO_TEXT


def _logo_distance_from_options() -> float:
    return _option_float_value(_LOGO_DISTANCE_OPTION, _LOGO_DISTANCE_DEFAULT)


def _logo_actor_from_options() -> str:
    actor = _option_text_value(_LOGO_ACTOR_OPTION, _LOGO_ACTOR_DEFAULT)
    return actor.strip() or _LOGO_ACTOR_DEFAULT


def _stacked_text_pixels(text: str) -> Tuple[List[Tuple[int, int, int]], int, int]:
    # Render stacked rows, centered to the widest row.  If the user explicitly
    # separates lines with |, honor that.  Also force the default phrase into
    # three rows even if a saved command/config passes it as spaces.
    normalized = (text or "").strip()
    if normalized.upper() == "JOIN GZO DISCORD":
        normalized = "JOIN|GZO|DISCORD"
    raw_lines = [part.strip() for part in normalized.split("|") if part.strip()]
    lines = raw_lines if raw_lines else [part.strip() for part in normalized.split() if part.strip()]
    if not lines:
        lines = [text.strip() or _LOGO_TEXT]

    rendered: List[Tuple[List[Tuple[int, int, int]], int, int, int]] = []
    max_width = 0
    line_gap = 2
    total_height = 0
    char_base = 0
    for line in lines:
        line_pixels, width, height = _text_pixels(line)
        rendered.append((line_pixels, width, height, char_base))
        max_width = max(max_width, width)
        total_height += height
        char_base += len(line) + 1
    total_height += max(0, len(lines) - 1) * line_gap

    pixels: List[Tuple[int, int, int]] = []
    y_offset = 0
    for line_pixels, width, height, char_base in rendered:
        x_offset = int(round((max_width - width) / 2.0))
        for x, y, char_index in line_pixels:
            pixels.append((x + x_offset, y + y_offset, char_index + char_base))
        y_offset += height + line_gap
    return pixels, max_width, total_height


def _first_component(actor: Any) -> Optional[Any]:
    for attr in ("Mesh", "StaticMeshComponent", "SkeletalMeshComponent", "BankMesh_SK", "RootComponent"):
        try:
            comp = getattr(actor, attr, None)
        except Exception:
            comp = None
        if comp is not None:
            return comp
    for class_name in ("PrimitiveComponent", "StaticMeshComponent", "SkeletalMeshComponent"):
        try:
            cls = find_class(class_name)
            comp = actor.GetComponentByClass(cls) if hasattr(actor, "GetComponentByClass") else None
        except Exception:
            comp = None
        if comp is not None:
            return comp
    return None


def _freeze_visual_actor(actor: Any) -> None:
    try:
        actor.SetActorEnableCollision(False)
    except Exception:
        pass
    try:
        actor.SetActorTickEnabled(False)
    except Exception:
        pass
    for comp in (getattr(actor, "RootComponent", None), _first_component(actor)):
        if comp is None:
            continue
        for name, args in (
            ("SetCollisionEnabled", (0,)),
            ("SetGenerateOverlapEvents", (False,)),
            ("SetSimulatePhysics", (False,)),
            ("SetEnableGravity", (False,)),
            ("SetComponentTickEnabled", (False,)),
            ("SetVisibility", (True, True)),
            ("SetHiddenInGame", (False, True)),
        ):
            try:
                getattr(comp, name)(*args)
            except Exception:
                pass


def _prepare_logo_barrel(actor: Any) -> None:
    """Keep logo barrels visible/floating, but still damageable/explosive.

    The old logo path used _freeze_visual_actor(), which disabled actor collision,
    component collision, overlap events, and tick.  That made the barrel pixels
    nice and static but also stopped explosive barrel gameplay logic from being
    hit/damaged normally.  This path keeps gameplay collision/tick alive while
    only trying to stop physics/gravity drift.
    """
    try:
        actor.SetActorHiddenInGame(False)
    except Exception:
        pass
    try:
        actor.SetActorEnableCollision(True)
    except Exception:
        pass
    try:
        actor.SetActorTickEnabled(True)
    except Exception:
        pass
    seen: set[str] = set()
    comps: List[Any] = []
    for comp in (getattr(actor, "RootComponent", None), _first_component(actor)):
        if comp is None:
            continue
        key = str(comp)
        if key in seen:
            continue
        seen.add(key)
        comps.append(comp)
    for comp in comps:
        for name, args in (
            ("SetHiddenInGame", (False, True)),
            ("SetVisibility", (True, True)),
            ("SetComponentTickEnabled", (True,)),
            ("SetCollisionEnabled", (1,)),
            ("SetGenerateOverlapEvents", (True,)),
        ):
            try:
                getattr(comp, name)(*args)
            except Exception:
                pass
        # Keep the sign suspended, but don't disable collision/tick.  Some
        # components don't expose these methods; failures are harmless.
        for name, args in (
            ("SetEnableGravity", (False,)),
            ("SetSimulatePhysics", (False,)),
        ):
            try:
                getattr(comp, name)(*args)
            except Exception:
                pass


def _tint_actor(actor: Any, rgba: Tuple[float, float, float, float]) -> None:
    comp = _first_component(actor)
    if comp is None:
        return
    color = make_struct("LinearColor", R=rgba[0], G=rgba[1], B=rgba[2], A=rgba[3])
    # Try material parameter paths common to UE components.  Failures are fine;
    # some barrel materials will ignore tint and keep their native color.
    for fn_name in ("SetVectorParameterValueOnMaterials",):
        fn = getattr(comp, fn_name, None)
        if not callable(fn):
            continue
        for param in ("Color", "BaseColor", "Tint", "EmissiveColor", "GlowColor"):
            try:
                fn(param, color)
            except Exception:
                pass
    for idx in range(4):
        try:
            mid = comp.CreateAndSetMaterialInstanceDynamic(idx)
        except Exception:
            mid = None
        if mid is None:
            continue
        for param in ("Color", "BaseColor", "Tint", "EmissiveColor", "GlowColor"):
            try:
                mid.SetVectorParameterValue(param, color)
            except Exception:
                pass


def _spawn_barrel_logo(
    *,
    barrel_name: str = "barrel",
    text: str = _LOGO_TEXT,
    distance: float = 1400.0,
    height: float = 750.0,
    spacing: float = 70.0,
    scale: float = 0.45,
    generated_only: bool = True,
) -> int:
    _, pawn, world, gs = _spawn_context()
    if pawn is None or world is None or gs is None:
        return 0
    cls, source, class_name = _find_template(barrel_name, None, generated_only=generated_only)
    if cls is None or source is None:
        _log_error("No logo actor template found. Try ASD_targets <keyword> --include-non-generated, then ASD_barrellogo --actor <keyword>.")
        return 0

    loc = pawn.K2_GetActorLocation()
    fwd = pawn.GetActorForwardVector()
    # Horizontal screen-space right vector perpendicular to the player forward.
    rx, ry = -float(fwd.Y), float(fwd.X)
    mag = max((rx * rx + ry * ry) ** 0.5, 0.0001)
    rx, ry = rx / mag, ry / mag
    fx, fy = float(fwd.X), float(fwd.Y)

    pixels, width, rows = _stacked_text_pixels(text)
    center_x = (float(width) - 1.0) / 2.0
    center_y = (float(rows) - 1.0) / 2.0
    base_x = float(loc.X + fx * distance)
    base_y = float(loc.Y + fy * distance)
    base_z = float(loc.Z + height)

    spawned = 0
    for x, y, char_index in pixels:
        px = base_x + rx * ((float(x) - center_x) * spacing)
        py = base_y + ry * ((float(x) - center_x) * spacing)
        pz = base_z - ((float(y) - center_y) * spacing)
        transform = _transform_at(px, py, pz, scale)
        actor = _spawn_actor_deferred(gs, world, cls, transform, class_name=class_name, source=source, collision_handling=1)
        if actor is None:
            _log_warn(f"barrel logo spawn failed at {x},{y}")
            continue
        _prepare_logo_barrel(actor)
        _tint_actor(actor, _LOGO_COLORS[char_index % len(_LOGO_COLORS)])
        _SPAWNED.append(DeployedActor(label="barrel_logo", source=source, actor=actor, actor_key=_actor_key(actor), class_name=_class_name(actor)))
        spawned += 1
    _log_info(f"Barrel logo spawned {spawned} actors for text={text!r} using actor={barrel_name!r} class={class_name} source={source}")
    return spawned


# Direct SpawnAI support: build a GbxActorDef shell from an actor-def name, load
# likely actor/script/model packages, spawn a fresh OakSpawner in front of the
# player, then PushActorDef + ResetSpawner. This is the path proven with
# Char_CrazyEarl_Boss and is useful for unique actors whose live template is not
# already nearby.
_KNOWN_SPAWNAI_LOADS: Dict[str, Tuple[str, ...]] = {
    "char_crazyearl_boss": (
        "/Game/DLC/Cowbell/AI/Bosses/CrazyEarl/Char_CrazyEarl_Boss",
        "/Game/DLC/Cowbell/AI/Bosses/CrazyEarl/Character/Char_CrazyEarl_Boss",
        "/Game/DLC/Cowbell/AI/Bosses/CrazyEarl/Animation/BPAnim_CrazyEarl",
    ),
    "char_targetdummy": (
        "/Game/InteractiveObjects/OakInteractiveObjects/TargetDummy/Char_TargetDummy",
        "/Game/InteractiveObjects/OakInteractiveObjects/TargetDummy/Script_TargetPracticeDummy",
        "/Game/InteractiveObjects/OakInteractiveObjects/TargetDummy/Model/Rig/SK_TargetDummy",
    ),
    "targetdummy": (
        "/Game/InteractiveObjects/OakInteractiveObjects/TargetDummy/Char_TargetDummy",
        "/Game/InteractiveObjects/OakInteractiveObjects/TargetDummy/Script_TargetPracticeDummy",
        "/Game/InteractiveObjects/OakInteractiveObjects/TargetDummy/Model/Rig/SK_TargetDummy",
    ),
    "char_npc_hermes": (
        "/Game/AI/NPC/_Unique/Hermes/Char_NPC_Hermes",
        "/Game/AI/NPC/_Unique/Hermes/Script_NPC_Hermes",
        "/Game/AI/NPC/_Unique/Hermes/Script_Hermes",
        "/Game/AI/NPC/_Unique/Hermes/Model/Rig/SK_Hermes",
    ),
    # Confirmed from char_actor_paths: FullPhoenix exposes only a Body package.
    # It must be paired with an FGbxDefPtr shell named Char_NPC_Lilith_FullPhoenix.
    "char_npc_lilith_fullphoenix": (
        "/Game/AI/NPC/_Unique/Lilith/_Design/Character/Body_NPC_Lilith_FullPhoenix",
        "/Game/AI/NPC/_Unique/Lilith/_Design/Character/Script_NPC_Lilith",
        "/Game/AI/NPC/_Unique/Lilith/_Design/Character/Body_NPC_Lilith",
    ),
    "lilith_fullphoenix": (
        "/Game/AI/NPC/_Unique/Lilith/_Design/Character/Body_NPC_Lilith_FullPhoenix",
        "/Game/AI/NPC/_Unique/Lilith/_Design/Character/Script_NPC_Lilith",
        "/Game/AI/NPC/_Unique/Lilith/_Design/Character/Body_NPC_Lilith",
    ),
}



def _spawnai_core_name(actor_def: str) -> str:
    """Return a compact content-folder-ish name from a Gbx actor def."""
    name = str(actor_def or "").strip()
    for prefix in ("Char_NPC_", "Char_AI_", "Char_"):
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    if name.endswith("_C"):
        name = name[:-2]
    # Char_CrazyEarl_Boss lives in a CrazyEarl folder, not CrazyEarl_Boss.
    if name.lower().endswith("_boss"):
        name = name[:-5]
    return name or str(actor_def or "").strip()


def _spawnai_path_package(path: str) -> str:
    """Normalize /Game/Foo.Asset_C into /Game/Foo for load_package."""
    path = str(path or "").strip()
    if not path:
        return ""
    if "." in path:
        path = path.split(".", 1)[0]
    if path.endswith("_C"):
        path = path[:-2]
    return path


def _spawnai_sibling_packages(actor_def: str, package: str) -> Tuple[str, ...]:
    """Guess nearby Char_/Script_/Body_ assets based on a user supplied --load path."""
    package = _spawnai_path_package(package)
    if not package or "/" not in package:
        return ()
    folder, asset = package.rsplit("/", 1)
    core = _spawnai_core_name(actor_def)
    names = (
        actor_def,
        f"Char_{core}",
        f"Char_NPC_{core}",
        f"Script_{core}",
        f"Script_NPC_{core}",
        f"Body_{core}",
        f"Body_NPC_{core}",
        asset,
    )
    folders = [folder]
    # If the user points at .../_Design/Character/Asset, also try the parent and nearby conventional folders.
    if folder.endswith("/_Design/Character"):
        parent = folder[: -len("/_Design/Character")]
        folders.extend((parent, f"{parent}/_Design/Character"))
    if folder.endswith("/Scripts"):
        parent = folder[: -len("/Scripts")]
        folders.extend((parent, f"{parent}/_Design/Character", f"{parent}/Character"))
    out=[]
    seen=set()
    for f in folders:
        for n in names:
            p=f"{f}/{n}"
            if p not in seen:
                seen.add(p); out.append(p)
    return tuple(out)


def _spawnai_guess_load_packages(actor_def: str, extra_loads: Sequence[str] = ()) -> Tuple[str, ...]:
    """Guess actor/script/model packages to hot-load for an actor def."""
    actor_def = str(actor_def or "").strip()
    key = _alias_key(actor_def)
    core = _spawnai_core_name(actor_def)
    guesses: List[str] = []

    guesses.extend(_KNOWN_SPAWNAI_LOADS.get(key, ()))

    guesses.extend((
        f"/Game/AI/{actor_def}",
        f"/Game/AI/{core}/{actor_def}",
        f"/Game/AI/{core}/Script_{core}",
        f"/Game/AI/NPC_{core}/{actor_def}",
        f"/Game/AI/NPC_{core}/Script_NPC_{core}",
        f"/Game/AI/NPC/{core}/{actor_def}",
        f"/Game/AI/NPC/{core}/Script_NPC_{core}",
        f"/Game/AI/NPC/{core}/Script_{core}",
        f"/Game/AI/NPC/_Unique/{core}/{actor_def}",
        f"/Game/AI/NPC/_Unique/{core}/_Design/Character/{actor_def}",
        f"/Game/AI/NPC/_Unique/{core}/_Design/Character/Char_{core}",
        f"/Game/AI/NPC/_Unique/{core}/_Design/Character/Char_NPC_{core}",
        f"/Game/AI/NPC/_Unique/{core}/_Design/Character/Body_NPC_{core}",
        f"/Game/AI/NPC/_Unique/{core}/Script_NPC_{core}",
        f"/Game/AI/NPC/_Unique/{core}/Script_{core}",
        f"/Game/AI/NPC/_Unique/{core}/Model/Rig/SK_{core}",
        f"/Game/AI/NPC/_Unique/{core}/Animation/BPAnim_{core}",
        f"/Game/AI/NPC/_Gestalt/Custom/{core}/_Design/Character/{actor_def}",
        f"/Game/AI/NPC/_Gestalt/Custom/{core}/_Design/Character/Char_{core}",
        f"/Game/AI/NPC/_Gestalt/Custom/{core}/_Design/Character/Char_NPC_{core}",
        f"/Game/AI/NPC/_Gestalt/Custom/{core}/_Design/Character/Body_NPC_{core}",
        f"/Game/AI/NPC/_Gestalt/Custom/{core}/_Design/Character/Script_NPC_{core}",
    ))

    if "target" in key and "dummy" in key:
        guesses.extend(_KNOWN_SPAWNAI_LOADS["char_targetdummy"])

    for extra in extra_loads:
        extra = str(extra or "").strip()
        if not extra:
            continue
        guesses.append(extra)
        guesses.extend(_spawnai_sibling_packages(actor_def, extra))

    out: List[str] = []
    seen: set[str] = set()
    for path in guesses:
        path = _spawnai_path_package(path)
        if not path or path in seen:
            continue
        seen.add(path)
        out.append(path)
    return tuple(out)


def _spawnai_load_packages(actor_def: str, extra_loads: Sequence[str] = ()) -> None:
    for package in _spawnai_guess_load_packages(actor_def, extra_loads):
        try:
            result = unrealsdk_load_package(package)
        except NameError:
            # Keep unrealsdk import local so this file still loads in SDK builds
            # where only selected symbols were imported at module top.
            try:
                import unrealsdk as _unrealsdk
                result = _unrealsdk.load_package(package)
            except Exception as exc:
                _log_warn(f"load_package {package} failed: {exc}")
                continue
        except Exception as exc:
            _log_warn(f"load_package {package} failed: {exc}")
            continue
        _log_info(f"load_package {package} -> {result}")


def _make_actor_def_shell(actor_def: str) -> Any:
    import unrealsdk as _unrealsdk
    shell = _unrealsdk.unreal.FGbxDefPtr()
    shell._experimental_name = str(actor_def).strip()
    shell._experimental_ref = find_object("ScriptStruct", "/Script/GbxSpawn.GbxActorDef")
    return shell


def _find_resolved_actor_def_by_name(actor_def: str) -> Optional[Any]:
    wanted = str(actor_def or "").strip()
    if not wanted:
        return None
    # Prefer live OakCharacters with a resolved instance.
    for cls_name in ("OakCharacter", "OakPawn", "OakActor", "Actor"):
        try:
            objects = list(find_all(cls_name, False))
        except TypeError:
            try:
                objects = list(find_all(cls_name))
            except Exception:
                continue
        except Exception:
            continue
        for obj in objects:
            low = str(obj).lower()
            if "default__" in low or "/script/" in low:
                continue
            try:
                d = obj.GbxActorData.GbxActorDef
            except Exception:
                continue
            try:
                if getattr(d, "_experimental_name", None) == wanted and getattr(d, "_experimental_instance", None):
                    return d
            except Exception:
                continue
    return None


def _spawnai_object_paths_for_package(actor_def: str, package: str) -> Tuple[str, ...]:
    package = _spawnai_path_package(package)
    if not package:
        return ()
    asset = package.rsplit("/", 1)[-1]
    names = (asset, actor_def, f"{asset}_C", f"{actor_def}_C")
    out=[]; seen=set()
    for name in names:
        p=f"{package}.{name}"
        if p not in seen:
            seen.add(p); out.append(p)
    return tuple(out)


def _spawnai_find_loaded_objects(actor_def: str, extra_loads: Sequence[str] = ()) -> List[Any]:
    """Return loaded UObject candidates for the guessed packages."""
    classes = (
        "GbxActorDef", "OakActorDef", "GbxCharacterDef", "OakCharacterDef",
        "BlueprintGeneratedClass", "GbxActorScriptClass", "Class", "Blueprint",
    )
    out=[]; seen=set()
    for package in _spawnai_guess_load_packages(actor_def, extra_loads):
        for path in _spawnai_object_paths_for_package(actor_def, package):
            for cls_name in classes:
                try:
                    obj = find_object(cls_name, path)
                except Exception:
                    continue
                if obj is None:
                    continue
                key=str(obj)
                if key in seen:
                    continue
                seen.add(key); out.append(obj)
                _log_info(f"resolved loaded actor object {path} class={cls_name}")
    return out


def _spawnai_real_def_from_object(obj: Any, depth: int = 0, seen: Optional[set[str]] = None) -> Optional[Any]:
    """Walk an object/class/default object and return a real exposed GbxActorDef pointer."""
    if obj is None or depth > 4:
        return None
    if seen is None:
        seen = set()
    try:
        key = str(obj)
    except Exception:
        key = repr(obj)
    if key in seen:
        return None
    seen.add(key)

    # Direct actor data on instances/default objects.
    try:
        d = obj.GbxActorData.GbxActorDef
        if d is not None:
            return d
    except Exception:
        pass

    # Some loaded actor-def-like objects are already the instance behind a pointer,
    # but do not create or mutate FGbxDefPtr here; this SDK has read-only internals.
    for attr in (
        "ClassDefaultObject", "GeneratedClass", "ParentClass", "Class",
        "DefaultObject", "ObjectArchetype", "_experimental_instance",
    ):
        try:
            child = getattr(obj, attr, None)
        except Exception:
            child = None
        if child is None or child is obj:
            continue
        d = _spawnai_real_def_from_object(child, depth + 1, seen)
        if d is not None:
            return d
    return None


def _spawnai_resolve_real_actor_def(actor_def: str, extra_loads: Sequence[str] = ()) -> Optional[Any]:
    d = _find_resolved_actor_def_by_name(actor_def) or _ACTOR_DEF_CACHE.get(_alias_key(actor_def))
    if d is not None:
        return d
    for obj in _spawnai_find_loaded_objects(actor_def, extra_loads):
        d = _spawnai_real_def_from_object(obj)
        if d is not None:
            _log_info(f"loaded object {obj} exposed real GbxActorData.GbxActorDef: {_actor_def_name(d)}")
            return d
        _log_warn(f"loaded object {obj} did not expose GbxActorData.GbxActorDef")
    return None


def _spawnai_probe(actor_def: str, extra_loads: Sequence[str] = ()) -> None:
    _log_info(f"ASD_probeai build={_BUILD_TAG} actor_def={actor_def!r} loads={tuple(extra_loads)}")
    _spawnai_load_packages(actor_def, extra_loads)
    found = False
    for obj in _spawnai_find_loaded_objects(actor_def, extra_loads):
        found = True
        d = _spawnai_real_def_from_object(obj)
        if d is not None:
            _log_info(f"PROBE OK object={obj} def={_actor_def_name(d)} ptr={d}")
        else:
            _log_warn(f"PROBE NO_DEF object={obj} type={type(obj)}")
    if not found:
        _log_warn("PROBE found no loaded UObject candidates. The package path may be wrong or the asset name may not match the package name.")




def _safe_set_attr(obj: Any, attr: str, value: Any) -> bool:
    try:
        if not hasattr(obj, attr):
            return False
        setattr(obj, attr, value)
        return True
    except Exception:
        return False


def _bump_attribute_initializer(param: Any, multiplier: int) -> int:
    """BL3-style helper for AttributeInitializationData-backed spawn params."""
    changed = 0
    if param is None:
        return changed

    # Direct range/value fields seen in BL3 BunchList examples.
    for chain in (
        ("Range", "Value"),
        ("Range", "BaseValue"),
        ("Range", "Constant"),
    ):
        try:
            target = param
            for attr in chain[:-1]:
                target = getattr(target, attr)
            setattr(target, chain[-1], multiplier)
            changed += 1
        except Exception:
            pass

    # BL3 pattern:
    # param.AttributeInitializationData.BaseValueScale = multiplier
    # param.AttributeInitializationData.BaseValueConstant = multiplier
    try:
        aid = param.AttributeInitializationData
        for field in ("BaseValueScale", "BaseValueConstant", "BaseValue", "Value"):
            try:
                setattr(aid, field, multiplier)
                changed += 1
            except Exception:
                pass
    except Exception:
        pass

    # Some BL4 structs may expose the same fields directly.
    for field in ("BaseValueScale", "BaseValueConstant", "BaseValue", "Value"):
        if _safe_set_attr(param, field, multiplier):
            changed += 1

    return changed


def _overdrive_spawn_style_object(style: Any, multiplier: int) -> int:
    """Apply BL3-style spawn multiplier edits to a style/SpawnDetails object."""
    if style is None:
        return 0

    changed = 0

    # Common BL3/Oak style knobs.
    for attr in ("SpawnDelay", "WaveDelay", "Cooldown", "SpawnCooldown", "RespawnCooldown", "InitialDelay"):
        if _safe_set_attr(style, attr, 0):
            changed += 1

    for attr in ("bInfinite", "bUnlimitedSpawns", "bAllowRespawn", "bRespawnEnabled", "bEnabled"):
        if _safe_set_attr(style, attr, True):
            changed += 1

    # Params from your BL3 script and likely BL4 equivalents.
    for attr in (
        "NumActorsParam",
        "NumAliveActorsParam",
        "MaxAliveActorsWhenPassive",
        "MaxAliveActorsWhenThreatened",
        "MaxActiveActors",
        "MaxAliveActors",
        "MaxSpawnedActors",
        "SpawnCount",
        "ActorCount",
        "WaveSize",
        "Population",
        "DesiredPopulation",
    ):
        try:
            changed += _bump_attribute_initializer(getattr(style, attr), multiplier)
        except Exception:
            pass

    # BunchList / Encounter-like nested content.
    for seq_attr in ("bunches", "Bunches", "waves", "Waves", "SpawnOptions", "spawnOptions"):
        try:
            seq = getattr(style, seq_attr)
        except Exception:
            continue
        try:
            for item in seq:
                changed += _overdrive_spawn_style_object(item, multiplier)
                for nested_attr in ("SpawnerStyle", "SpawnStyle", "style"):
                    try:
                        changed += _overdrive_spawn_style_object(getattr(item, nested_attr), multiplier)
                    except Exception:
                        pass
        except Exception:
            pass

    return changed


def _overdrive_spawn_manager(multiplier: int) -> int:
    """Raise global spawn caps similar to the old BL3 SpawnCap hook."""
    changed = 0
    for cls_name in ("SpawnManager", "OakSpawnManager"):
        try:
            managers = list(find_all(cls_name, False))
        except TypeError:
            try:
                managers = list(find_all(cls_name))
            except Exception:
                continue
        except Exception:
            continue

        for mgr in managers:
            for field, value in (
                ("MaxSpawnCost", 2147483647),
                ("MaxActorsSpawnedPerFrame", 2147483647),
                ("MaxSpawnedActors", 2147483647),
                ("MaxAliveActors", 2147483647),
                ("SpawnBudget", 2147483647),
            ):
                if _safe_set_attr(mgr, field, value):
                    changed += 1

    if changed:
        _log_info(f"spawn manager overdrive changed_fields={changed}")
    return changed


def _construct_extra_spawn_points_for_component(comp: Any, multiplier: int, spacing: float = 250.0) -> int:
    """Create additional OakSpawnPoint objects like the BL3 multiplier script.

    This is best-effort and only runs when the component exposes SpawnPoints.
    """
    try:
        points = comp.SpawnPoints
    except Exception:
        try:
            points = comp.spawnpoints
        except Exception:
            return 0

    try:
        current_len = len(points)
    except Exception:
        return 0

    if current_len >= max(2, multiplier):
        return 0

    try:
        import unrealsdk as _unrealsdk
        world_outer = ENGINE.GameViewport.World.CurrentLevel.OwningWorld.PersistentLevel
    except Exception:
        return 0

    # Source point to copy action/stretch data from, if available.
    try:
        source_point = points[0] if current_len > 0 else None
    except Exception:
        source_point = None

    created = 0
    offsets = [
        (spacing, 0, 0), (-spacing, 0, 0), (0, spacing, 0), (0, -spacing, 0),
        (spacing, spacing, 0), (-spacing, spacing, 0), (spacing, -spacing, 0), (-spacing, -spacing, 0),
        (spacing * 2, 0, 0), (-spacing * 2, 0, 0), (0, spacing * 2, 0), (0, -spacing * 2, 0),
    ]

    for idx in range(max(0, multiplier - current_len)):
        try:
            oak_spawn_point = _unrealsdk.construct_object("OakSpawnPoint", outer=world_outer)
            off = offsets[idx % len(offsets)]
            try:
                oak_spawn_point.SpawnPointComponent.RelativeLocation = _unrealsdk.make_struct(
                    "Vector", X=float(off[0]), Y=float(off[1]), Z=float(off[2])
                )
            except Exception:
                pass

            if source_point is not None:
                for attr in ("SpawnAction", "SpawnStretchType", "StretchyPoint"):
                    try:
                        setattr(oak_spawn_point.SpawnPointComponent, attr, getattr(source_point.SpawnPointComponent, attr))
                    except Exception:
                        pass

            try:
                points.append(oak_spawn_point)
            except Exception:
                try:
                    comp.spawnpoints.append(oak_spawn_point)
                except Exception:
                    continue

            created += 1
        except Exception as exc:
            _log_warn(f"extra spawnpoint creation failed: {exc}")
            break

    if created:
        _safe_set_attr(comp, "SpawnPointUseType", 1)
        _log_info(f"created {created} extra OakSpawnPoint(s) for {comp}")

    return created


def _overdrive_spawner_component(comp: Any, multiplier: int) -> int:
    """Apply BL3-inspired spawner multiplier changes to a BL4 OakSpawnerComponent."""
    desired = max(1, int(multiplier))
    changed = 0

    _overdrive_spawn_manager(desired)

    # Direct component and owner flags/caps.
    targets: List[Any] = [comp]
    for attr in ("OakSpawner", "SpawnDetails", "Activation", "SpawnerStyle", "SpawnerStyleOverride"):
        try:
            sub = getattr(comp, attr)
            if sub is not None:
                targets.append(sub)
        except Exception:
            pass

    try:
        spawner = comp.OakSpawner
        if spawner is not None:
            targets.append(spawner)
            for attr in ("SpawnerComponent", "SpawnPointComponent", "SpawnerStyle", "SpawnerStyleOverride"):
                try:
                    sub = getattr(spawner, attr)
                    if sub is not None:
                        targets.append(sub)
                except Exception:
                    pass
    except Exception:
        pass

    for target in targets:
        for field in (
            "bSpawnerEnabled", "bSpawnPointEnabled", "bEnabled", "bActive", "bCanSpawn",
            "bAllowSpawn", "bAllowRespawn", "bRespawnEnabled", "bInfinite", "bUnlimitedSpawns",
        ):
            if _safe_set_attr(target, field, True):
                changed += 1

        for field in (
            "Count", "SpawnCount", "NumActors", "NumActorsToSpawn", "NumToSpawn",
            "MaxActors", "MaxActorCount", "MaxSpawnCount", "MaxSpawns",
            "MaxAliveActors", "MaxActiveActors", "MaxSpawnedActors",
            "SpawnLimit", "ActorLimit", "PopulationLimit", "DesiredPopulation",
            "WaveCount", "WaveSize", "InitialSpawnCount",
        ):
            if _safe_set_attr(target, field, desired):
                changed += 1

        changed += _overdrive_spawn_style_object(target, desired)

    # Public enable methods.
    for fn_name, args in (
        ("SetSpawnerEnabled", (True,)),
        ("SetSpawnPointEnabled", (True,)),
        ("SetActive", (True,)),
        ("Activate", (True,)),
    ):
        try:
            getattr(comp, fn_name)(*args)
            changed += 1
        except TypeError:
            try:
                getattr(comp, fn_name)()
                changed += 1
            except Exception:
                pass
        except Exception:
            pass

    changed += _construct_extra_spawn_points_for_component(comp, desired)

    _log_info(f"spawner style overdrive multiplier={desired} changed={changed} comp={comp}")
    return changed

def _spawnai_fresh_spawner_direct(
    actor_def: str,
    *,
    distance: float,
    z_offset: float = 0.0,
    scale: float = 1.0,
    count: int = 1,
    spacing: float = 125.0,
    extra_loads: Sequence[str] = (),
) -> Optional[Any]:
    """Spawn an actor-def through a throwaway OakSpawner placed in front of the player.

    v16 intentionally mirrors the proven console path:
      load package(s) -> build FGbxDefPtr shell -> spawn OakSpawner from class ->
      PushActorDef(..., True) -> ResetSpawner(True).

    Important: a console-spawned OakSpawner is not a fully-authored map spawner.
    BL4/Oak keeps its real spawn-row table in native SpawnerStyleDef data that is
    not rebuildable from Python. This path is therefore a reliable disposable
    one-spawn helper, not a true unlimited population spawner. Diagnostics are
    logged so we can see when a duplicate collapses to total=1 or 0.
    """
    _, pawn, world, gs = _spawn_context()
    if pawn is None or world is None or gs is None:
        return None

    actor_def = str(actor_def or "").strip()
    if not actor_def:
        return None

    _spawnai_load_packages(actor_def, extra_loads)

    # Prefer nearby enabled real spawners only as a class/template source. Do not
    # PushActorDef into real map spawners: testing showed it destroys their native
    # spawn rows and GetNumTotalActors collapses to zero.
    try:
        candidates = [
            o for o in find_all("OakSpawner", False)
            if "default__" not in str(o).lower() and "/script/" not in str(o).lower()
        ]
    except TypeError:
        candidates = [
            o for o in find_all("OakSpawner")
            if "default__" not in str(o).lower() and "/script/" not in str(o).lower()
        ]
    except Exception as exc:
        _log_error(f"find_all('OakSpawner') failed for ASD_spawnai direct path: {exc}")
        return None

    if not candidates:
        _log_error("ASD_spawnai direct path failed: no OakSpawner template loaded. Move near a spawner first.")
        return None

    def _score_spawner(sp: Any) -> Tuple[int, float]:
        total = 0
        try:
            total = int(sp.GetSpawnerComponent().GetNumTotalActors(0))
        except Exception:
            pass
        try:
            pl = pawn.K2_GetActorLocation()
            sl = sp.K2_GetActorLocation()
            dist = _distance_sq(pl, sl)
        except Exception:
            dist = 999999999999.0
        # Sort descending by map-spawner total, ascending by distance.
        return total, -dist

    candidates.sort(key=_score_spawner, reverse=True)
    base = candidates[0]
    _log_info(
        f"ASD_spawnai thin-air source={base} source_counts="
        f"{_spawner_counts(base.GetSpawnerComponent()) if hasattr(base, 'GetSpawnerComponent') else None}"
    )

    first_actor: Optional[Any] = None
    total_alive = 0
    total = max(1, int(count))

    for idx in range(total):
        d = _spawnai_resolve_real_actor_def(actor_def, extra_loads) or _make_actor_def_shell(actor_def)
        transform = _spawn_transform_for_index(
            pawn,
            index=idx,
            count=total,
            distance=distance,
            spacing=spacing,
            z_offset=z_offset,
            scale=scale,
        )
        scan_loc = transform.Translation
        world_before = _world_actor_snapshot()

        try:
            cls = base.Class
        except Exception:
            try:
                cls = find_class("OakSpawner")
            except Exception as exc:
                _log_error(f"OakSpawner class lookup failed: {exc}")
                return first_actor

        spawner = _spawn_actor_deferred(gs, world, cls, transform, class_name="OakSpawner", source=None, collision_handling=1)
        if spawner is None:
            continue
        try:
            comp = spawner.GetSpawnerComponent()
        except Exception as exc:
            _log_warn(f"ASD_spawnai direct path: GetSpawnerComponent failed on {spawner}: {exc}")
            continue

        # Best-effort prep. The important proven bits are PushActorDef(..., True)
        # and ResetSpawner(True); do not use False here because it clears rows on
        # real spawners and can under-initialize duplicates.
        _overdrive_spawner_component(comp, max(1, int(count)))
        try:
            comp.SetSpawnerEnabled(True)
        except Exception:
            pass
        try:
            comp.SetSpawnPointEnabled(True)
        except Exception:
            pass
        try:
            comp.PushActorDef("ASD", d, True)
        except Exception as exc:
            _log_error(f"ASD_spawnai thin-air PushActorDef failed for {actor_def!r} using {d}: {exc}")
            continue
        try:
            comp.ResetSpawner(True)
        except TypeError:
            try:
                comp.ResetSpawner()
            except Exception as exc:
                _log_warn(f"ResetSpawner failed on {comp}: {exc}")
        except Exception as exc:
            _log_warn(f"ResetSpawner failed on {comp}: {exc}")

        resolved = bool(getattr(d, "_experimental_instance", None))
        poll_timeout = 3.0 if resolved else 0.75
        actors = _poll_spawner_for_alive_actors(comp, timeout=poll_timeout, interval=0.15)
        if not actors:
            actors = _find_new_world_actors_near(
                world_before,
                scan_loc,
                radius=max(2000.0, float(spacing) * 3.0),
                expected_name=actor_def,
            )
            if actors:
                _log_info(f"world-delta detected {len(actors)} spawned actor(s) for {actor_def}: {actors}")

        alive_count, spawned_count, dead_count, total_count = _spawner_counts(comp)
        _log_info(
            f"ASD_spawnai thin-air actor_def={actor_def} resolved={resolved} "
            f"poll={poll_timeout:g}s spawner={spawner} loc={spawner.K2_GetActorLocation()} "
            f"counts=(alive={alive_count}, spawned={spawned_count}, dead={dead_count}, total={total_count}) "
            f"actors={actors}"
        )
        for actor in actors:
            _apply_spawnai_actor_transform(actor, transform, pawn, scale=scale, z_offset=z_offset)
            _SPAWNED.append(DeployedActor(label=actor_def, source=spawner, actor=actor, actor_key=_actor_key(actor), class_name=_class_name(actor)))
            _cache_actor_def_from_spawned_actor(actor_def, actor)
            if first_actor is None:
                first_actor = actor
            total_alive += 1

    if total_alive <= 0:
        _log_warn(
            f"ASD_spawnai thin-air queued {actor_def!r}, but no alive actors were returned. "
            "This usually means the actor package was not enough to resolve the FGbxDefPtr or the native spawner rows collapsed."
        )
    return first_actor



def _safe_component_field_dump(comp: Any, needles: Sequence[str]) -> List[Tuple[str, str, Any]]:
    """Return guarded component fields matching needles without tripping bad property wrappers."""
    out: List[Tuple[str, str, Any]] = []
    lowered = tuple(n.lower() for n in needles)
    for name in dir(comp):
        if lowered and not any(n in name.lower() for n in lowered):
            continue
        try:
            value = getattr(comp, name)
            if callable(value):
                continue
            out.append((name, type(value).__name__, value))
        except Exception as exc:
            out.append((name, "ERR", str(exc)))
    return out


@command("ASD_spawnerdiag", description="Log OakSpawner/OakSpawnerComponent diagnostics, including duplicate-spawner row collapse.")
def _cmd_spawnerdiag(args: argparse.Namespace) -> None:
    limit = max(1, int(getattr(args, "limit", 20)))
    try:
        spawners = [o for o in find_all("OakSpawner", False) if "default__" not in str(o).lower() and "/script/" not in str(o).lower()]
    except TypeError:
        spawners = [o for o in find_all("OakSpawner") if "default__" not in str(o).lower() and "/script/" not in str(o).lower()]
    except Exception as exc:
        _log_error(f"ASD_spawnerdiag find_all OakSpawner failed: {exc}")
        return

    rows: List[Tuple[int, Tuple[int, int, int, int], bool, bool, Any]] = []
    for idx, sp in enumerate(spawners):
        try:
            comp = sp.GetSpawnerComponent()
            counts = _spawner_counts(comp)
            enabled = bool(comp.IsSpawnerEnabled())
            active = bool(comp.IsActive())
        except Exception:
            continue
        rows.append((idx, counts, enabled, active, sp))
    rows.sort(key=lambda item: item[1][3], reverse=True)
    _log_info(f"ASD_spawnerdiag loaded_spawners={len(spawners)} showing={min(limit, len(rows))}")
    for idx, counts, enabled, active, sp in rows[:limit]:
        _log_info(f"  idx={idx} counts(alive,spawned,dead,total)={counts} enabled={enabled} active={active} spawner={sp}")

    if not rows:
        return

    # Create one duplicate and compare totals. This is intentionally diagnostic
    # and proves whether the build can synthesize a full native row table from a
    # spawned OakSpawner actor.
    _, pawn, world, gs = _spawn_context()
    if pawn is None or world is None or gs is None:
        return
    src = rows[0][4]
    transform = _spawn_transform_for_index(pawn, index=0, count=1, distance=float(getattr(args, "distance", _DEFAULT_DISTANCE)), spacing=0.0, z_offset=0.0, scale=1.0)
    dup = _spawn_actor_deferred(gs, world, src.Class, transform, class_name="OakSpawner", source=None, collision_handling=1)
    if dup is None:
        return
    try:
        src_comp = src.GetSpawnerComponent()
        dup_comp = dup.GetSpawnerComponent()
        _log_info(f"  source counts={_spawner_counts(src_comp)} fields={_safe_component_field_dump(src_comp, ('SpawnPoint', 'SpawnerStyle', 'SpawnDetails'))[:12]}")
        _log_info(f"  duplicate counts={_spawner_counts(dup_comp)} fields={_safe_component_field_dump(dup_comp, ('SpawnPoint', 'SpawnerStyle', 'SpawnDetails'))[:12]}")
    except Exception as exc:
        _log_warn(f"ASD_spawnerdiag duplicate compare failed: {exc}")


_cmd_spawnerdiag.add_argument("--limit", type=int, default=20, help="How many loaded OakSpawners to log. Default 20.")
_cmd_spawnerdiag.add_argument("--distance", type=float, default=_DEFAULT_DISTANCE, help="Where to place the diagnostic duplicate. Default 350.")




@command("ASD_cache", description="Cache a live actor's GbxActorDef for later AI-capable ASD_spawnai. Usage: ASD_cache mancubus [--class OakCharacter]")
def _cmd_cache(args: argparse.Namespace) -> None:
    name = str(getattr(args, "name", "") or "").strip()
    if not name:
        _log_error("Usage: ASD_cache <name> [--class ClassName]")
        return
    class_override = getattr(args, "class_name", None)
    matches = _candidate_actor_def_sources(name, class_override=class_override)
    if not matches:
        _log_error(f"No live actor-def source found for {name!r}. Move near the actor first, then run ASD_cache {name}.")
        return
    limit = max(1, int(getattr(args, "limit", 10)))
    _log_info(f"actor-def cache candidates for {name!r}: {min(len(matches), limit)}/{len(matches)}")
    for idx, obj in enumerate(matches[:limit]):
        try:
            def_name = _actor_def_name(obj.GbxActorData.GbxActorDef)
        except Exception:
            def_name = "<unreadable>"
        _log_info(f"  {idx:02d}: def={def_name} obj={obj}")
    pick = max(0, int(getattr(args, "index", 0)))
    if pick >= len(matches):
        _log_error(f"--index {pick} out of range; only {len(matches)} candidates.")
        return
    _cache_actor_def(name, matches[pick])


_cmd_cache.add_argument("name", help="Cache key / search term, e.g. mancubus. Later use ASD_spawnai mancubus.")
_cmd_cache.add_argument("--class", dest="class_name", default=None, help="Optional class to search first, e.g. OakCharacter.")
_cmd_cache.add_argument("--index", type=int, default=0, help="Candidate index to cache. Default 0.")
_cmd_cache.add_argument("--limit", type=int, default=10, help="How many candidates to log. Default 10.")


@command("ASD_cache_status", description="List runtime actor-def cache entries created by ASD_cache.")
def _cmd_cache_status(_: argparse.Namespace) -> None:
    if not _ACTOR_DEF_CACHE:
        _log_info("actor-def cache is empty. Use ASD_cache <name> while near a source actor.")
        return
    for key, def_ptr in _ACTOR_DEF_CACHE.items():
        _log_info(f"cache {key!r}: def={_actor_def_name(def_ptr)} source={_ACTOR_DEF_CACHE_SOURCE.get(key, '<unknown>')}")





@command("ASD_spawnoverdrive", description="Best-effort BL3-style multiplier patch on loaded OakSpawnerComponents.")
def _cmd_spawnoverdrive(args: Namespace) -> None:
    mult = max(1, int(getattr(args, "multiplier", 10)))
    changed_total = 0
    count = 0
    for cls_name in ("OakSpawnerComponent", "SpawnerComponent"):
        try:
            comps = list(find_all(cls_name, False))
        except TypeError:
            try:
                comps = list(find_all(cls_name))
            except Exception:
                continue
        except Exception:
            continue
        for comp in comps:
            count += 1
            changed_total += _overdrive_spawner_component(comp, mult)
    _log_info(f"ASD_spawnoverdrive multiplier={mult} components={count} changed_total={changed_total}")

_cmd_spawnoverdrive.add_argument("multiplier", nargs="?", default=10, type=int)

@command("ASD_probeai", description="Probe ASD_spawnai load paths and report whether they expose a real GbxActorData.GbxActorDef.")
def _cmd_probeai(args: argparse.Namespace) -> None:
    name = str(getattr(args, "name", "") or "").strip()
    if not name:
        _log_error("Usage: ASD_probeai <actor-def-name> [--load /Game/...]")
        return
    _spawnai_probe(name, tuple(getattr(args, "load", ()) or ()))


_cmd_probeai.add_argument("name", help="Actor-def name to probe, e.g. Char_Robo_Totem_Base.")
_cmd_probeai.add_argument("--load", action="append", default=[], help="Extra package/object path to load/probe. Can be used more than once.")


@command("ASD_spawnai", description="Spawn an actor def through a fresh OakSpawner. Supports cached defs and direct names like Char_CrazyEarl_Boss, Char_TargetDummy, Char_NPC_Hermes.")
def _cmd_spawnai(args: argparse.Namespace) -> None:
    name = str(getattr(args, "name", "") or "").strip()
    if not name:
        _log_error("Usage: ASD_spawnai <actor-def-name>")
        return
    distance = float(getattr(args, "distance", _DEFAULT_DISTANCE))
    count = max(1, int(getattr(args, "count", 1)))
    spacing = float(getattr(args, "spacing", 125.0))
    z_offset = float(getattr(args, "z_offset", getattr(args, "zoffset", 0.0)))
    scale = float(getattr(args, "scale", _DEFAULT_SCALE))
    extra_loads = tuple(getattr(args, "load", ()) or ())

    actor: Optional[Any] = None
    # Keep the old cache path for live/cached actors, unless explicitly skipped.
    if not bool(getattr(args, "direct_only", False)):
        actor = _spawn_cached_actor_def(name, distance=distance, z_offset=z_offset, scale=scale, count=count, spacing=spacing)
    if actor is None:
        actor = _spawnai_fresh_spawner_direct(name, distance=distance, z_offset=z_offset, scale=scale, count=count, spacing=spacing, extra_loads=extra_loads)
    if actor is None:
        _log_warn(f"ASD_spawnai {name!r} did not return an actor immediately. If it queued/compiled assets, run it again or add --load /Game/.../Script_Asset.")
        return
    _log_info(f"ASD_spawnai complete: {actor}")


def _add_spawnai_args(cmd: Any) -> None:
    cmd.add_argument("name", help="Actor-def name or cache key, e.g. Char_CrazyEarl_Boss, Char_TargetDummy, Char_NPC_Hermes, mancubus.")
    cmd.add_argument("--distance", type=float, default=_DEFAULT_DISTANCE, help="Spawn a fresh OakSpawner this far in front. Default 350.")
    cmd.add_argument("--zoffset", "--z-offset", type=float, default=0.0, dest="z_offset", help="Vertical offset added to the spawn transform. Default 0.")
    cmd.add_argument("--scale", type=float, default=_DEFAULT_SCALE, help="Uniform spawn scale. Default 1.")
    cmd.add_argument("--count", type=int, default=1, help="Number of AI actors to request. Default 1.")
    cmd.add_argument("--spacing", type=float, default=125.0, help="Spacing between requested AI actors. Default 125.")
    cmd.add_argument("--load", action="append", default=[], help="Extra package to load before spawning. Can be used more than once, e.g. --load /Game/AI/NPC/_Unique/Hermes/Script_NPC_Hermes")
    cmd.add_argument("--direct-only", action="store_true", help="Skip old ASD_cache path and use the fresh-spawner direct path only.")


_add_spawnai_args(_cmd_spawnai)

@command("ASD_lostloot", description="Spawn and activate a Lost Loot machine in front of you.")
def _cmd_lostloot(args: argparse.Namespace) -> None:
    _spawn_from_args(args, "lostloot")


@command("ASD_spawn", description="Spawn/duplicate a deployable or generic skeletal actor from a live template. Usage: ASD_spawn lostloot|goldenchest|firmware|OakWeapon_2147480142 [--class ClassName]")
def _cmd_spawn(args: argparse.Namespace) -> None:
    _spawn_from_args(args)


def _add_spawn_args(cmd: Any, *, include_name: bool) -> None:
    if include_name:
        cmd.add_argument("name", help="Alias, substring, or exact live actor name, e.g. lostloot, golden, firmware, OakWeapon_2147480142.")
    cmd.add_argument("--class", dest="class_name", default=None, help="Override Unreal class, e.g. OakLostLootMachine.")
    cmd.add_argument("--distance", type=float, default=_DEFAULT_DISTANCE, help="Forward spawn distance. Default 350.")
    cmd.add_argument("--z-offset", type=float, default=_DEFAULT_Z_OFFSET, dest="z_offset", help="Vertical offset. Default -100.")
    cmd.add_argument("--scale", type=float, default=_DEFAULT_SCALE, help="Uniform spawn scale. Default 1.")
    cmd.add_argument("--delay", type=float, default=_DEFAULT_DELAY, help="Seconds before script-state activation. Default 1.")
    cmd.add_argument("--enable", default=None, help="Comma-separated script states to enable. Default Active,ActiveIdle_Anim.")
    cmd.add_argument("--disable", default=None, help="Comma-separated script states to disable. Default IsInUse,InUse_Anim,Dispensing_Anim.")
    cmd.add_argument("--no-activate", action="store_true", help="Spawn only; do not toggle ScriptData states.")
    cmd.add_argument("--include-non-generated", action="store_true", help="Allow template actors without _Generated_ in the object name.")
    cmd.add_argument("--count", type=int, default=1, help="Number of actors to spawn. Default 1.")
    cmd.add_argument("--spacing", type=float, default=125.0, help="Spacing between multiple spawned actors. Default 125.")


_add_spawn_args(_cmd_lostloot, include_name=False)
_add_spawn_args(_cmd_spawn, include_name=True)


@command("ASD_targets", description="List live template actors matching an alias/class. Usage: ASD_targets lostloot [--class OakLostLootMachine]")
def _cmd_targets(args: argparse.Namespace) -> None:
    name = str(getattr(args, "name", "") or "").strip()
    class_override = getattr(args, "class_name", None)
    generated_only = not bool(getattr(args, "include_non_generated", False))
    default_class, needles = _default_class_and_needles(name)
    class_name = class_override or default_class
    if class_name:
        matches2 = [(class_name, obj) for obj in _candidate_sources(class_name, needles, generated_only=generated_only)]
        if not matches2 and generated_only:
            _log_info("No _Generated_ matches in requested/default class; retrying non-generated search for visibility.")
            matches2 = [(class_name, obj) for obj in _candidate_sources(class_name, needles, generated_only=False)]
        if not matches2:
            _log_info("No matches in requested/default class; scanning common actor classes by keyword.")
            scan_classes = [class_name] + [c for c in _CLASS_SCAN_ORDER if c != class_name]
            matches2 = _candidate_sources_multi(scan_classes, needles, generated_only=generated_only)
            if not matches2 and generated_only:
                matches2 = _candidate_sources_multi(scan_classes, needles, generated_only=False)
    else:
        matches2 = _candidate_sources_multi(_CLASS_SCAN_ORDER, needles, generated_only=generated_only)
        if not matches2 and generated_only:
            _log_info("No _Generated_ matches; retrying non-generated keyword scan for visibility.")
            matches2 = _candidate_sources_multi(_CLASS_SCAN_ORDER, needles, generated_only=False)
    limit = max(1, int(getattr(args, "limit", 20)))
    class_label = class_name if class_name else "<keyword scan>"
    _log_info(f"targets name={name!r} class={class_label!r} needles={needles}: {min(len(matches2), limit)}/{len(matches2)}")
    for idx, (matched_class, obj) in enumerate(matches2[:limit]):
        _log_info(f"  {idx:02d}: class={matched_class} actor_class={_class_display_name(_source_class(obj, matched_class))} obj={obj}")


_cmd_targets.add_argument("name", help="Alias or substring to search, e.g. lostloot, golden, goldenchest, firmware.")
_cmd_targets.add_argument("--class", dest="class_name", default=None, help="Override Unreal class name.")
_cmd_targets.add_argument("--limit", type=int, default=20, help="Maximum matches to log.")
_cmd_targets.add_argument("--include-non-generated", action="store_true", help="Show templates without _Generated_ in the object name.")


@command("ASD_barrellogo", description="Spawn pipe-separated barrel text. Example: ASD_barrellogo WE HAVE BEEN|TRYING TO REACH YOU|ABOUT YOUR CARS EXTENDED WARRENTY")
def _cmd_barrellogo(args: argparse.Namespace) -> None:
    # Console supports either:
    #   ASD_barrellogo WE HAVE BEEN|TRYING TO REACH YOU|ABOUT YOUR CARS EXTENDED WARRENTY
    #   ASD_barrellogo --text WE HAVE BEEN|TRYING TO REACH YOU|ABOUT YOUR CARS EXTENDED WARRENTY
    # argparse splits on spaces, so join positional text_parts back together.
    text = str(getattr(args, "text", "") or "").strip()
    parts = getattr(args, "text_parts", None) or []
    if not text and parts:
        text = " ".join(str(part) for part in parts).strip()
    if not text:
        text = _logo_text_from_options()
    _spawn_barrel_logo(
        barrel_name=str(getattr(args, "actor", None) or getattr(args, "barrel", None) or _logo_actor_from_options()),
        text=text,
        distance=(float(getattr(args, "distance")) if getattr(args, "distance", None) is not None else _logo_distance_from_options()),
        height=float(getattr(args, "height", 750.0)),
        spacing=float(getattr(args, "spacing", 70.0)),
        scale=float(getattr(args, "scale", 0.45)),
        generated_only=not bool(getattr(args, "include_non_generated", False)),
    )


_cmd_barrellogo.add_argument("text_parts", nargs="*", help="Optional text to render. Use | for rows, e.g. WE HAVE BEEN|TRYING TO REACH YOU|ABOUT YOUR CARS EXTENDED WARRENTY.")
_cmd_barrellogo.add_argument("--actor", default=None, help="Template keyword to use for each pixel/letter block. Overrides mod-menu Logo Actor Override. Example: --actor goldenchest")
_cmd_barrellogo.add_argument("--barrel", dest="actor", default=None, help="Backward-compatible alias for --actor.")
_cmd_barrellogo.add_argument("--text", default="", help="Text to render. Use | to force line breaks. If omitted, keybind/mod-menu rows are used.")
_cmd_barrellogo.add_argument("--distance", type=float, default=None, help="Forward distance from player. If omitted, uses the permanent mod-menu Barrel Logo Distance option.")
_cmd_barrellogo.add_argument("--height", type=float, default=750.0, help="Height above player.")
_cmd_barrellogo.add_argument("--spacing", type=float, default=70.0, help="Barrel spacing in Unreal units.")
_cmd_barrellogo.add_argument("--scale", type=float, default=0.45, help="Uniform barrel scale.")
_cmd_barrellogo.add_argument("--include-non-generated", action="store_true", help="Allow non-_Generated_ barrel templates.")


@keybind("ASD Spawn Barrel Logo")
def _keybind_barrellogo() -> None:
    _spawn_barrel_logo(text=_logo_text_from_options(), distance=_logo_distance_from_options(), barrel_name=_logo_actor_from_options())




@command("ASD_logo_options", description="Log barrel logo mod-menu option status and current keybind rows.")
def _cmd_logo_options(_: argparse.Namespace) -> None:
    _log_info(f"row1_option={_LOGO_ROW1_OPTION} value={_option_text_value(_LOGO_ROW1_OPTION, _LOGO_ROW1_DEFAULT)!r}")
    _log_info(f"row2_option={_LOGO_ROW2_OPTION} value={_option_text_value(_LOGO_ROW2_OPTION, _LOGO_ROW2_DEFAULT)!r}")
    _log_info(f"row3_option={_LOGO_ROW3_OPTION} value={_option_text_value(_LOGO_ROW3_OPTION, _LOGO_ROW3_DEFAULT)!r}")
    _log_info(f"distance_option={_LOGO_DISTANCE_OPTION} value={_logo_distance_from_options():.0f}")
    _log_info(f"actor_option={_LOGO_ACTOR_OPTION} value={_logo_actor_from_options()!r}")


@command("ASD_status", description="Log actors spawned by ActorScriptDeployer.")
def _cmd_status(_: argparse.Namespace) -> None:
    _log_info(f"spawned={len(_SPAWNED)}")
    for idx, item in enumerate(_SPAWNED):
        _log_info(f"  {idx:02d}: label={item.label!r} actor={item.actor} source={item.source}")


def _safe_actor_key(actor: Any) -> str:
    try:
        return str(actor)
    except Exception:
        return ""


def _actor_key(actor: Any) -> str:
    return _safe_actor_key(actor)


def _class_name(actor: Any) -> str:
    try:
        cls = getattr(actor, "Class", None)
        name = getattr(cls, "Name", None)
        if name:
            return str(name)
        text = str(cls)
        if "'" in text:
            return text.split("'")[-2].rsplit(".", 1)[-1]
        return text.rsplit(".", 1)[-1].strip("'> ")
    except Exception:
        return ""


def _find_live_spawned_actor(item: DeployedActor) -> Optional[Any]:
    """Return the current live UObject for a tracked actor, or None if it already died.

    Exploded barrels often leave stale Python wrappers behind. Calling K2_DestroyActor
    on those stale wrappers can crash the game, so clear only destroys actors that
    can still be found in the live object table.
    """
    key = item.actor_key or _safe_actor_key(item.actor)
    if not key:
        return None

    class_names: List[str] = []
    if item.class_name:
        class_names.append(item.class_name)
    try:
        source_cls = _class_name(item.source)
        if source_cls and source_cls not in class_names:
            class_names.append(source_cls)
    except Exception:
        pass
    if not class_names:
        class_names.extend(("OakInteractiveObject", "OakLostLootMachine", "Actor"))

    for class_name in class_names:
        try:
            candidates = list(find_all(class_name, False))
        except Exception:
            continue
        for actor in candidates:
            if _safe_actor_key(actor) == key:
                return actor
    return None


def _clear_spawned_actors() -> int:
    destroyed = 0
    skipped_dead = 0
    survivors: List[DeployedActor] = []
    for item in list(_SPAWNED):
        actor = _find_live_spawned_actor(item)
        if actor is None:
            skipped_dead += 1
            continue
        try:
            if bool(getattr(actor, "bActorIsBeingDestroyed", False)):
                skipped_dead += 1
                continue
        except Exception:
            pass
        try:
            actor.K2_DestroyActor()
            destroyed += 1
        except Exception as exc:
            survivors.append(item)
            _log_warn(f"clear skipped live actor {item.actor_key or item.actor}: {exc}")
    _SPAWNED.clear()
    _SPAWNED.extend(survivors)
    if skipped_dead:
        _log_info(f"clear ignored {skipped_dead} actor references that were already gone/exploded.")
    return destroyed


@command("ASD_clear", description="Destroy actors spawned by ActorScriptDeployer.")
def _cmd_clear(_: argparse.Namespace) -> None:
    destroyed = _clear_spawned_actors()
    _log_info(f"cleared {destroyed} spawned actors.")


@keybind("ASD Clear Spawned Actors")
def _keybind_clear_spawned() -> None:
    destroyed = _clear_spawned_actors()
    _log_info(f"cleared {destroyed} spawned actors from keybind.")


@command("ASD_activate_last", description="Rerun the broad activation pass on the most recently spawned ActorScriptDeployer actor.")
def _cmd_activate_last(args: argparse.Namespace) -> None:
    if not _SPAWNED:
        _log_warn("No spawned actors to activate.")
        return
    item = _SPAWNED[-1]
    key = _alias_key(item.label)
    enable = _unique_states(
        _split_states(getattr(args, "enable", None), _DEFAULT_ACTIVATE_ENABLE),
        _PRESET_ENABLE_STATES.get(key, ()),
        _GENERIC_ENABLE_STATES,
    )
    disable = _unique_states(
        _split_states(getattr(args, "disable", None), _DEFAULT_ACTIVATE_DISABLE),
        _PRESET_DISABLE_STATES.get(key, ()),
        _GENERIC_DISABLE_STATES,
    )
    _log_info(f"Re-activating last spawned actor label={item.label!r}: {item.actor}")
    _set_script_states(item.actor, enable, disable, debug=True)


_cmd_activate_last.add_argument("--enable", default=None, help="Comma-separated script states to enable first.")
_cmd_activate_last.add_argument("--disable", default=None, help="Comma-separated script states to disable first.")


@command("ASD_scriptdump", description="Dump useful script/method names for the most recently spawned ActorScriptDeployer actor.")
def _cmd_scriptdump(_: argparse.Namespace) -> None:
    if not _SPAWNED:
        _log_warn("No spawned actors to inspect.")
        return
    item = _SPAWNED[-1]
    _log_info(f"script dump for label={item.label!r} actor={item.actor}")
    for inst in _script_instances(item.actor):
        _script_debug(inst, limit=200)


_install_logo_text_menu_support()

_BUILD_MOD_KWARGS: Dict[str, Any] = {
    "name": "ActorScriptDeployer",
    "author": "Matt",
    "description": (
        "Spawn deployable scripted actors from live templates. "
        "Commands: ASD_cache <name>, ASD_cache_status, ASD_probeai <name>, ASD_spawnai <cached-name>, ASD_spawnerdiag, ASD_lostloot, ASD_spawn <name>, ASD_barrellogo [text|rows], ASD_targets <name>, ASD_status, ASD_clear. "
        "Keybinds: ASD Spawn Barrel Logo, ASD Clear Spawned Actors. Mod menu free-text rows, Barrel Logo Distance, and Logo Actor Override configure keybind defaults."
    ),
    "supported_games": Game.BL4,
    "coop_support": CoopSupport.ClientSide,
    "keybinds": [_keybind_barrellogo, _keybind_clear_spawned],
    "commands": [_cmd_cache, _cmd_cache_status, _cmd_probeai, _cmd_spawnai, _cmd_spawnerdiag, _cmd_lostloot, _cmd_spawn, _cmd_barrellogo, _cmd_targets, _cmd_logo_options, _cmd_status, _cmd_clear, _cmd_activate_last, _cmd_scriptdump],
}
if _LOGO_OPTIONS:
    _BUILD_MOD_KWARGS["options"] = _LOGO_OPTIONS
_log_info(f"loaded build={_BUILD_TAG}; ASD_probeai command registered")
build_mod(**_BUILD_MOD_KWARGS)
