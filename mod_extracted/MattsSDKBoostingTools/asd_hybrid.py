"""ASD hybrid: spawn / despawn live pawns from any catalog name.

Python still owns the catalog/picker name. For every Dev Spawner and hoard
pick this module clones a live match when one exists, otherwise it deferred-
spawns from a resolved UClass. If no UClass is loaded, it uses the proven
FGbxDefPtr + throwaway OakSpawner + PushActorDef path and waits until
GetAliveActors is non-empty. It does not report an empty queue as success.
"""
from __future__ import annotations

import re
import time
from typing import Any

from mods_base import ENGINE, get_pc
import unrealsdk
from unrealsdk import logging

_PREFIX = "[Matts SDK Boosting Tools | ASD Hybrid]"
_SCAN_CLASSES = (
    "OakCharacter",
    "GbxCharacter",
    "OakPawn",
    "OakVehicle",
    "GbxVehicle",
    "OakInteractiveObject",
    "InteractiveObject",
)
_COPY_DATA_FIELDS = ("GbxActorDef", "ActorPartList", "ActorPartSelections", "SpawnDetails")
_COMBAT_COPY_ATTRS = (
    "CombatComponent",
    "OakCombatComponent",
    "GbxCombatComponent",
    "Weapon",
    "ActiveWeapon",
    "CurrentWeapon",
    "EquippedWeapon",
    "PerceptionComponent",
    "AIPerceptionComponent",
    "AggroComponent",
    "TargetSelector",
    "TargetingComponent",
)
_HOSTILE_FLAGS = (
    ("bAlwaysHostile", True),
    ("bIsHostile", True),
    ("bCanAttack", True),
    ("bPassive", False),
    ("bIsPassive", False),
    ("bFriendly", False),
)
_HOSTILE_METHODS = (
    "SetEnemy",
    "SetFocus",
    "EngageTarget",
    "StartCombat",
    "SetTargetActor",
    "SetCombatTarget",
    "NotifyEnemy",
    "SetHostile",
    "SetIsHostile",
    "SetPassive",
)
_CONTROLLER_ATTRS = ("Controller", "AIController", "OakAIController")
_CONTROLLER_CLASS_NAMES = ("OakAIController", "GbxAIController", "AIController")
_TEAM_ATTRS = (
    "Team",
    "TeamComponent",
    "OakTeam",
    "GbxTeam",
    "TeamDef",
    "TeamId",
    "TeamIndex",
    "Allegiance",
)
_FRIENDLY_TOKENS = (
    "vendor",
    "vending",
    "lostloot",
    "lost_loot",
    "bank",
    "shop",
    "merchant",
    "echolog",
    "echo_log",
)
_COMBAT_OVERRIDE_TOKENS = (
    "boss",
    "enemy",
    "combat",
    "raid",
    "killable",
    "badass",
    "prisonbuddy",
    "arjay",
)
_CLASS_LOOKUP_TYPES = (
    "BlueprintGeneratedClass",
    "GbxActorScriptClass",
    "Class",
    "Blueprint",
    "GbxActorDef",
    "OakActorDef",
    "GbxCharacterDef",
    "OakCharacterDef",
    "Object",
)
_SCAN_LOOKUP_TYPES = (
    "GbxActorDef",
    "OakActorDef",
    "GbxCharacterDef",
    "OakCharacterDef",
)
_DEF_CLASS_ATTRS = (
    "GeneratedClass",
    "ActorClass",
    "PawnClass",
    "CharacterClass",
    "DefaultActorClass",
    "NativeClass",
    "Blueprint",
    "GeneratedBlueprint",
    "ActorBlueprint",
    "Class",
    "ClassDefaultObject",
    "DefaultObject",
    "SoftClass",
    "ActorSoftClass",
    "CharacterSoftClass",
)
_COOKED_PATH_RE = re.compile(r"(/Game/[A-Za-z0-9_./]+)")
_GBX_ACTOR_DEF_STRUCT = "/Script/GbxSpawn.GbxActorDef"
_TRACK_TTL_S = 300.0
_NAME_PREFIXES = (
    "Char_NPC_",
    "Char_AI_",
    "Char_",
    "IO_",
    "Vehicle_",
    "VH_",
    "Proj_",
    "Pickup_",
    "ActorDef_",
    "AcctorDef_",
)
_NAME_SUFFIXES = (
    "_RunnableTRUE",
    "_Runnable",
    "_Shared",
    "_SHARED",
    "_TRUE",
    "_True",
    "_Boss",
    "_boss",
    "_Female",
    "_Male",
    "_Base",
    "_C",
)
_SKIP_FOLDER_TOKENS = frozenset(
    {
        "shared",
        "male",
        "female",
        "basic",
        "boss",
        "true",
        "runnable",
        "runnabletrue",
        "npc",
        "char",
        "ai",
        "io",
        "base",
        "add",
        "mini",
        "intro",
        "name",
    }
)
_HINT_PATH_KEYS = (
    "package",
    "class",
    "path",
    "ai_path",
    "asset_path",
    "class_path",
    "actor_path",
    "blueprint",
    "blueprint_path",
)
_HINT_NAME_KEYS = (
    "parent_actor",
    "display_key",
    "balance_row",
    "true_boss_actor",
    "reference_display_name",
)

_tracked: list[dict[str, Any]] = []
_tracked_at = 0.0
_throwaway_spawners: list[Any] = []
_SPAWNER_POLL_TIMEOUT_S = 8.0
_SPAWNER_POLL_INTERVAL_S = 0.05


def _log(msg: str) -> None:
    logging.info(f"{_PREFIX} {msg}")


def normalize_actor_key(name: str) -> str:
    """Compact catalog / live-def name for matching (no package guess)."""
    text = str(name or "").strip()
    if not text:
        return ""
    if "/" in text:
        text = text.rsplit("/", 1)[-1]
    if ":" in text:
        text = text.rsplit(":", 1)[-1]
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    if text.endswith("_C"):
        text = text[:-2]
    low = text.lower()
    for prefix in ("char_npc_", "char_ai_", "char_"):
        if low.startswith(prefix):
            low = low[len(prefix):]
            break
    return low


def is_clearly_friendly(name: str) -> bool:
    """Vendors / machines stay non-combat. Catalog characters (Char_ / NPC / bosses) fight."""
    raw = str(name or "").strip().lower()
    key = normalize_actor_key(name)
    blob = f"{key} {raw}"
    if any(token in blob for token in _COMBAT_OVERRIDE_TOKENS):
        return False
    if raw.startswith("char_") or "char_npc" in raw or "char_ai" in raw:
        return False
    return any(token in blob for token in _FRIENDLY_TOKENS)


def keys_match(wanted: str, candidate: str) -> bool:
    """True when catalog key and a live name/def refer to the same actor."""
    left = normalize_actor_key(wanted)
    right = normalize_actor_key(candidate)
    if not left or not right:
        return False
    if left == right:
        return True
    shorter, longer = (left, right) if len(left) <= len(right) else (right, left)
    if len(shorter) < 4:
        return False
    return shorter in longer


def _unwrap(value: Any) -> Any:
    return value[0] if isinstance(value, (list, tuple)) else value


def _safe_str(obj: Any) -> str:
    try:
        return str(obj)
    except Exception:
        return ""


def _obj_addr(obj: Any) -> int:
    get_addr = getattr(obj, "_get_address", None)
    if not callable(get_addr):
        return 0
    try:
        addr = int(get_addr())
    except Exception:
        return 0
    return addr if addr > 0x10000 else 0


def _actor_def_name(actor: Any) -> str:
    try:
        data = getattr(actor, "GbxActorData", None)
        def_ptr = getattr(data, "GbxActorDef", None) if data is not None else None
    except Exception:
        return ""
    if def_ptr is None:
        return ""
    for attr in ("_experimental_name", "Name"):
        try:
            value = getattr(def_ptr, attr, None)
        except Exception:
            value = None
        if value:
            return str(value)
    return _safe_str(def_ptr)


def _is_default(obj: Any) -> bool:
    text = f"{_safe_str(obj)} {getattr(obj, 'Name', '')}".lower()
    return "default__" in text or "/script/" in text


def _is_player_pawn(actor: Any) -> bool:
    cls = str(getattr(getattr(actor, "Class", None), "Name", "") or "").lower()
    name = str(getattr(actor, "Name", "") or "").lower()
    path = _safe_str(actor).lower()
    blob = f"{cls} {name} {path}"
    return any(token in blob for token in ("oakplayer", "playercontroller", "bp_player", "playercharacter"))


def _matches_wanted(actor: Any, wanted: str) -> bool:
    if keys_match(wanted, _actor_def_name(actor)):
        return True
    if keys_match(wanted, str(getattr(actor, "Name", "") or "")):
        return True
    return keys_match(wanted, _safe_str(actor))


def find_live_sources(name: str) -> list[Any]:
    """Loaded OakCharacter / GbxCharacter pawns that match the catalog name."""
    wanted = str(name or "").strip()
    if not wanted:
        return []
    found: list[Any] = []
    seen: set[int] = set()
    for class_name in _SCAN_CLASSES:
        try:
            objects = unrealsdk.find_all(class_name, False) or []
        except TypeError:
            try:
                objects = unrealsdk.find_all(class_name) or []
            except Exception:
                continue
        except Exception:
            continue
        for actor in objects:
            if actor is None or _is_default(actor) or _is_player_pawn(actor):
                continue
            key = _obj_addr(actor) or id(actor)
            if key in seen:
                continue
            if not _matches_wanted(actor, wanted):
                continue
            seen.add(key)
            found.append(actor)
    return found


def _core_asset_name(actor_def: str) -> str:
    name = str(actor_def or "").strip()
    for prefix in _NAME_PREFIXES:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    if name.endswith("_C"):
        name = name[:-2]
    if name.lower().endswith("_boss"):
        name = name[:-5]
    return name or str(actor_def or "").strip()


def _strip_known_suffixes(name: str) -> str:
    text = str(name or "").strip()
    changed = True
    while text and changed:
        changed = False
        for suffix in _NAME_SUFFIXES:
            if text.endswith(suffix) and len(text) > len(suffix) + 2:
                text = text[: -len(suffix)]
                changed = True
                break
    return text


def _camel_prefixes(text: str) -> tuple[str, ...]:
    chunks = re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]+|[a-z]+|[0-9]+", str(text or ""))
    if not chunks:
        return ()
    out: list[str] = []
    acc = ""
    for chunk in chunks:
        acc += chunk
        if len(acc) >= 4:
            out.append(acc)
    return tuple(out)


def _folder_tokens(*parts: str) -> tuple[str, ...]:
    """Folder-ish names derived from a catalog key or catalog hint field."""
    out: list[str] = []
    seen: set[str] = set()

    def _add(value: str) -> None:
        value = str(value or "").strip()
        if not value:
            return
        if "/" in value or "\\" in value or "." in value:
            value = value.replace("\\", "/").rsplit("/", 1)[-1]
            value = value.split(".", 1)[0]
        value = value.replace(" ", "").replace("-", "_")
        if value.endswith("_C"):
            value = value[:-2]
        key = value.lower()
        if not value or key in seen or key in _SKIP_FOLDER_TOKENS:
            return
        if len(value) < 4:
            return
        seen.add(key)
        out.append(value)

    for raw in parts:
        text = str(raw or "").strip()
        if not text:
            continue
        _add(text)
        _add(_core_asset_name(text))
        stripped = _strip_known_suffixes(_core_asset_name(text))
        _add(stripped)
        for piece in re.split(r"[_\s]+", stripped or text):
            _add(piece)
            for prefix in _camel_prefixes(piece):
                _add(prefix)
        for prefix in _camel_prefixes(stripped or text):
            _add(prefix)
    return tuple(out)


def _core_name_variants(actor_def: str) -> tuple[str, ...]:
    """Folder-ish names for package guesses (any catalog key, not one boss)."""
    return _folder_tokens(actor_def)


def _package_root(path: str) -> str:
    path = str(path or "").strip()
    if not path:
        return ""
    if "." in path:
        path = path.split(".", 1)[0]
    if path.endswith("_C"):
        path = path[:-2]
    return path


def _paths_from_hints(hints: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(hints, dict):
        return ()
    out: list[str] = []
    seen: set[str] = set()
    for key in _HINT_PATH_KEYS:
        value = str(hints.get(key) or "").strip()
        if not value:
            continue
        if "/Game/" in value:
            value = "/Game/" + value.split("/Game/", 1)[-1]
        path = _package_root(value)
        if path.startswith("/Game/") and path not in seen:
            seen.add(path)
            out.append(path)
    return tuple(out)


def _tokens_from_hints(actor_def: str, hints: dict[str, Any] | None = None) -> tuple[str, ...]:
    parts = [actor_def]
    if isinstance(hints, dict):
        for key in _HINT_NAME_KEYS:
            parts.append(str(hints.get(key) or ""))
    return _folder_tokens(*parts)


def _folder_templates(actor_def: str, token: str) -> tuple[str, ...]:
    """Package guesses for one folder token. Prefix picks extra roots, not a special-case enemy."""
    low = str(actor_def or "").lower()
    templates = [
        f"/Game/AI/{actor_def}",
        f"/Game/AI/{token}/{actor_def}",
        f"/Game/AI/NPC/{token}/{actor_def}",
        f"/Game/AI/NPC/_Unique/{token}/{actor_def}",
        f"/Game/AI/NPC/_Unique/{token}/_Design/Character/{actor_def}",
        f"/Game/AI/NPC/_Unique/{token}/_Design/Character/Char_{token}",
        f"/Game/AI/Bosses/{token}/{actor_def}",
        f"/Game/AI/Bosses/{token}/Character/{actor_def}",
        f"/Game/Enemies/{token}/{actor_def}",
        f"/Game/Enemies/{actor_def}/{actor_def}",
        f"/Game/Enemies/_Unique/{token}/{actor_def}",
        f"/Game/Enemies/_Unique/{token}/_Design/Character/{actor_def}",
        f"/Game/Enemies/Bosses/{token}/{actor_def}",
        f"/Game/Enemies/Bosses/{actor_def}/{actor_def}",
        f"/Game/NonPlayerCharacters/{token}/{actor_def}",
        f"/Game/NonPlayerCharacters/_Unique/{token}/{actor_def}",
        f"/Game/Characters/{token}/{actor_def}",
        f"/Game/OakGame/AI/{token}/{actor_def}",
        f"/Game/Missions/Main/{token}/{actor_def}",
        f"/Game/Missions/Main/{token}/Characters/{actor_def}",
        f"/Game/Missions/Main/{token}/_Design/Character/{actor_def}",
        f"/Game/DLC/Cowbell/AI/Bosses/{token}/{actor_def}",
        f"/Game/DLC/Cowbell/AI/Bosses/{token}/Character/{actor_def}",
        f"/Game/AI/NPC/_Gestalt/{token}/{actor_def}",
        f"/Game/AI/NPC/_Gestalt/{token}/_Design/Character/{actor_def}",
        f"/Game/AI/NPC/_Gestalt/Custom/{token}/{actor_def}",
        f"/Game/AI/NPC/_Gestalt/Custom/{token}/_Design/Character/{actor_def}",
        f"/Game/AI/NPC/_Gestalt/Custom/{token}/_Design/Character/Char_{token}",
    ]
    if low.startswith("io_") or low.startswith("pickup_") or low.startswith("actordef_"):
        templates.extend(
            (
                f"/Game/InteractiveObjects/{token}/{actor_def}",
                f"/Game/InteractiveObjects/OakInteractiveObjects/{token}/{actor_def}",
                f"/Game/InteractiveObjects/OakInteractiveObjects/{actor_def}/{actor_def}",
                f"/Game/Pickups/{token}/{actor_def}",
            )
        )
    if low.startswith("vehicle_") or low.startswith("vh_") or "vehicle" in low:
        templates.extend(
            (
                f"/Game/Vehicles/{token}/{actor_def}",
                f"/Game/Vehicles/{actor_def}/{actor_def}",
                f"/Game/OakGame/Vehicles/{token}/{actor_def}",
            )
        )
    if low.startswith("proj_"):
        templates.extend(
            (
                f"/Game/Projectiles/{token}/{actor_def}",
                f"/Game/Projectiles/{actor_def}/{actor_def}",
            )
        )
    templates.extend(
        (
            f"/Game/InteractiveObjects/OakInteractiveObjects/{token}/{actor_def}",
        )
    )
    return tuple(templates)


def guess_load_packages(
    actor_def: str,
    extra_loads: tuple[str, ...] = (),
    hints: dict[str, Any] | None = None,
) -> tuple[str, ...]:
    """Package paths to load so any catalog name can resolve to a UClass.

    Uses ActorScriptDeployer's guess list when that mod is present, plus
    name-derived Enemies/Bosses/NPC/IO/vehicle folders and any catalog-row
    package/path fields (current catalog rows have names, not cooked paths).
    """
    actor_def = str(actor_def or "").strip()
    if not actor_def:
        return ()
    guesses: list[str] = []
    try:
        asd = __import__("ActorScriptDeployer")
        extra_fn = getattr(asd, "_spawnai_guess_load_packages", None)
        if callable(extra_fn):
            guesses.extend(str(p) for p in (extra_fn(actor_def, extra_loads) or ()))
    except Exception:
        pass
    for token in _tokens_from_hints(actor_def, hints):
        guesses.extend(_folder_templates(actor_def, token))
    guesses.extend(_paths_from_hints(hints))
    for extra in extra_loads:
        extra = str(extra or "").strip()
        if extra:
            guesses.append(extra)
    out: list[str] = []
    seen: set[str] = set()
    for path in guesses:
        path = _package_root(path)
        if not path or path in seen:
            continue
        seen.add(path)
        out.append(path)
    return tuple(out)


def load_catalog_packages(
    actor_def: str,
    extra_loads: tuple[str, ...] = (),
    hints: dict[str, Any] | None = None,
) -> list[str]:
    """Hot-load guessed packages. Returns paths that load_package accepted."""
    loaded: list[str] = []
    for package in guess_load_packages(actor_def, extra_loads, hints):
        result = _try_load_package(package)
        if result:
            loaded.append(package)
    return loaded


def _object_paths_for_package(actor_def: str, package: str) -> tuple[str, ...]:
    package = _package_root(package)
    if not package:
        return ()
    asset = package.rsplit("/", 1)[-1]
    names = (asset, actor_def, f"{asset}_C", f"{actor_def}_C")
    out: list[str] = []
    seen: set[str] = set()
    for name in names:
        path = f"{package}.{name}"
        if path not in seen:
            seen.add(path)
            out.append(path)
    return tuple(out)


def _as_spawn_class(obj: Any) -> Any | None:
    """Turn a loaded UObject into something BeginDeferredActorSpawnFromClass accepts."""
    if obj is None:
        return None
    inst = getattr(obj, "_experimental_instance", None)
    if inst is not None and inst is not obj:
        nested = _as_spawn_class(inst)
        if nested is not None:
            return nested
    for attr in _DEF_CLASS_ATTRS:
        try:
            child = getattr(obj, attr, None)
        except Exception:
            child = None
        if child is None or child is obj:
            continue
        if attr in ("ClassDefaultObject", "DefaultObject"):
            cls = getattr(child, "Class", None)
            if cls is not None:
                return cls
            continue
        if attr in ("SoftClass", "ActorSoftClass", "CharacterSoftClass"):
            cls = _class_from_soft_path(child)
            if cls is not None:
                return cls
            continue
        child_type = str(getattr(getattr(child, "Class", None), "Name", "") or type(child).__name__)
        child_name = str(getattr(child, "Name", "") or "")
        if attr == "Class":
            if getattr(obj, "GbxActorData", None) is not None:
                return child
            if child_name.endswith("_C") or "BlueprintGenerated" in child_type:
                return child
            continue
        if attr == "GeneratedClass" or attr.endswith("Class") or "Class" in child_type:
            if child_name in ("GbxActorDef", "OakActorDef", "GbxCharacterDef", "ScriptStruct"):
                continue
            return child
    type_name = type(obj).__name__
    class_name = str(getattr(getattr(obj, "Class", None), "Name", "") or "")
    if "Class" in type_name or "BlueprintGenerated" in type_name or "Class" in class_name:
        return obj
    return None


def _cooked_paths_from_text(text: str) -> tuple[str, ...]:
    out: list[str] = []
    seen: set[str] = set()
    for match in _COOKED_PATH_RE.findall(str(text or "")):
        path = match.rstrip("',)\"")
        if path and path not in seen:
            seen.add(path)
            out.append(path)
    return tuple(out)


def _class_from_soft_path(value: Any) -> Any | None:
    texts = [_safe_str(value)]
    for attr in ("AssetPathName", "AssetPath", "ObjectPath", "Path", "Name"):
        try:
            texts.append(str(getattr(value, attr, "") or ""))
        except Exception:
            continue
    for text in texts:
        for path in _cooked_paths_from_text(text):
            cls = _class_from_cooked_path(path)
            if cls is not None:
                return cls
    return None


def _try_load_package(package: str) -> Any:
    loader = getattr(unrealsdk, "load_package", None)
    if not callable(loader) or not package:
        return None
    for args in ((package,), (package, True), (package, 0)):
        try:
            result = loader(*args)
        except TypeError:
            continue
        except Exception as exc:
            _log(f"load_package {package} failed: {exc!r}")
            return None
        _log(f"load_package {package} -> {result}")
        return result
    return None


def _class_from_cooked_path(path: str) -> Any | None:
    path = str(path or "").strip().strip("'\"")
    if not path.startswith("/Game/"):
        return None
    package = _package_root(path)
    asset = path.rsplit(".", 1)[-1] if "." in path else path.rsplit("/", 1)[-1]
    _try_load_package(package)
    cls = _find_class_by_name(asset)
    if cls is not None:
        return cls
    finder = getattr(unrealsdk, "find_object", None)
    if not callable(finder):
        return None
    object_path = path if "." in path else f"{package}.{asset}"
    for type_name in _CLASS_LOOKUP_TYPES:
        try:
            obj = finder(type_name, object_path)
        except Exception:
            obj = None
        cls = _as_spawn_class(obj)
        if cls is not None:
            return cls
        try:
            obj = finder(type_name, f"{object_path}_C")
        except Exception:
            obj = None
        cls = _as_spawn_class(obj)
        if cls is not None:
            return cls
    return None


def _find_gbx_actor_def_struct() -> Any | None:
    finder = getattr(unrealsdk, "find_object", None)
    if callable(finder):
        for type_name in ("ScriptStruct", "Object"):
            try:
                obj = finder(type_name, _GBX_ACTOR_DEF_STRUCT)
            except Exception:
                obj = None
            if obj is not None:
                return obj
    return None


def _make_gbx_actor_def_ptr(name: str) -> Any | None:
    """Same native name lookup OakSpawner uses (FGbxDefPtr), without spawning."""
    try:
        from unrealsdk.unreal import FGbxDefPtr
    except Exception:
        FGbxDefPtr = getattr(getattr(unrealsdk, "unreal", None), "FGbxDefPtr", None)
    if FGbxDefPtr is None:
        return None
    struct = _find_gbx_actor_def_struct()
    attempts: list[Any] = []
    if struct is not None:
        attempts.append((name, struct))
    attempts.append((name,))
    for args in attempts:
        try:
            return FGbxDefPtr(*args)
        except Exception:
            continue
    try:
        return FGbxDefPtr(name, type="GbxActorDef")
    except Exception:
        return None


def _iter_named_objects(wanted: str) -> list[Any]:
    found: list[Any] = []
    seen: set[int] = set()

    def _add(obj: Any) -> None:
        if obj is None:
            return
        key = id(obj)
        if key in seen:
            return
        seen.add(key)
        found.append(obj)

    _add(_make_gbx_actor_def_ptr(wanted))
    inst = getattr(found[0], "_experimental_instance", None) if found else None
    _add(inst)
    finder = getattr(unrealsdk, "find_object", None)
    names = [wanted, f"{wanted}_C"]
    if callable(finder):
        for type_name in _CLASS_LOOKUP_TYPES:
            for name in names:
                try:
                    _add(finder(type_name, name))
                except Exception:
                    continue
    return found


def _class_from_named_objects(wanted: str) -> tuple[Any | None, str]:
    """Resolve a catalog name through the native Gbx def table / FindObject."""
    for obj in _iter_named_objects(wanted):
        cls = _as_spawn_class(obj)
        if cls is not None:
            return cls, f"native def {wanted}"
        texts = [_safe_str(obj)]
        for attr in ("PathName", "Name"):
            try:
                texts.append(str(getattr(obj, attr, "") or ""))
            except Exception:
                continue
        for text in texts:
            for path in _cooked_paths_from_text(text):
                cls = _class_from_cooked_path(path)
                if cls is not None:
                    return cls, f"native path {path}"
    return None, ""


def _asset_registry_class(wanted: str) -> tuple[Any | None, str]:
    """Ask the engine AssetRegistry for the cooked object path of this name."""
    try:
        helpers = unrealsdk.find_class("AssetRegistryHelpers")
        cdo = getattr(helpers, "ClassDefaultObject", None) if helpers is not None else None
        registry = cdo.GetAssetRegistry() if cdo is not None else None
    except Exception:
        registry = None
    if registry is None:
        return None, ""
    assets = None
    for method_name in ("GetAssetsByName", "K2_GetAssetsByName"):
        method = getattr(registry, method_name, None)
        if not callable(method):
            continue
        try:
            assets = method(wanted)
            break
        except TypeError:
            try:
                assets = method(wanted, True)
                break
            except Exception:
                continue
        except Exception:
            continue
    if not assets:
        return None, ""
    try:
        rows = list(assets)
    except Exception:
        rows = [assets]
    for row in rows:
        texts = [_safe_str(row)]
        for attr in (
            "ObjectPath",
            "PackageName",
            "AssetName",
            "SoftObjectPath",
            "PackagePath",
        ):
            try:
                texts.append(str(getattr(row, attr, "") or ""))
            except Exception:
                continue
        for text in texts:
            for path in _cooked_paths_from_text(text):
                cls = _class_from_cooked_path(path)
                if cls is not None:
                    return cls, f"asset registry {path}"
            if "/Game/" not in text:
                package = str(text or "").strip()
                if package.startswith("/Game/"):
                    cls = _class_from_cooked_path(f"{package}.{wanted}")
                    if cls is not None:
                        return cls, f"asset registry {package}"
    return None, ""


def _find_class_by_name(wanted: str) -> Any | None:
    names = [wanted]
    if not wanted.endswith("_C"):
        names.append(f"{wanted}_C")
    finder = getattr(unrealsdk, "find_object", None)
    for name in names:
        try:
            cls = unrealsdk.find_class(name)
        except Exception:
            cls = None
        if cls is not None:
            return cls
        if not callable(finder):
            continue
        for type_name in ("BlueprintGeneratedClass", "Class", "GbxActorScriptClass"):
            try:
                obj = finder(type_name, name)
            except Exception:
                obj = None
            cls = _as_spawn_class(obj)
            if cls is not None:
                return cls
    return None


def _object_name_candidates(obj: Any) -> tuple[str, ...]:
    return (
        str(getattr(obj, "Name", "") or ""),
        _safe_str(obj),
        _actor_def_name(obj),
    )


def _scan_loaded_spawn_class(wanted: str) -> Any | None:
    """Match an already-loaded def without scanning every UObject in GObjects."""
    wanted_key = normalize_actor_key(wanted)
    if not wanted_key:
        return None
    fuzzy: Any | None = None
    for type_name in _SCAN_LOOKUP_TYPES:
        try:
            objects = unrealsdk.find_all(type_name, False) or []
        except TypeError:
            try:
                objects = unrealsdk.find_all(type_name) or []
            except Exception:
                continue
        except Exception:
            continue
        for obj in objects:
            if obj is None or _is_default(obj):
                continue
            names = _object_name_candidates(obj)
            exact = any(normalize_actor_key(cand) == wanted_key for cand in names if cand)
            if not exact and not any(keys_match(wanted, cand) for cand in names if cand):
                continue
            cls = _as_spawn_class(obj)
            if cls is None:
                cls = _find_class_by_name(str(getattr(obj, "Name", "") or wanted))
            if cls is None:
                continue
            if exact:
                return cls
            if fuzzy is None:
                fuzzy = cls
    return fuzzy


def resolve_spawn_class(
    name: str,
    extra_loads: tuple[str, ...] = (),
    hints: dict[str, Any] | None = None,
) -> tuple[Any | None, str]:
    """Resolve any catalog actor-def to a UClass, loading packages if needed."""
    wanted = str(name or "").strip()
    if not wanted:
        return None, "empty name"
    class_hint = ""
    if isinstance(hints, dict):
        class_hint = str(
            hints.get("class")
            or hints.get("class_name")
            or hints.get("uclass")
            or ""
        ).strip()
        if class_hint.startswith("/"):
            cls = _class_from_cooked_path(class_hint)
            if cls is not None:
                return cls, f"hint path {class_hint}"
            class_hint = class_hint.rsplit(".", 1)[-1].rsplit("/", 1)[-1]
    for candidate in (wanted, class_hint):
        if not candidate:
            continue
        cls = _find_class_by_name(candidate)
        if cls is not None:
            return cls, f"find_class {candidate}"
        cls, how = _class_from_named_objects(candidate)
        if cls is not None:
            return cls, how
        cls, how = _asset_registry_class(candidate)
        if cls is not None:
            return cls, how
    cls = _scan_loaded_spawn_class(wanted)
    if cls is not None:
        return cls, f"loaded class scan {wanted}"
    for extra in extra_loads:
        _try_load_package(str(extra or "").strip())
    cls = _find_class_by_name(wanted)
    if cls is not None:
        return cls, f"find_class after extra_loads"
    cls, how = _class_from_named_objects(wanted)
    if cls is not None:
        return cls, how or "native def after extra_loads"
    return None, "class not loaded"


def _pawn_for_pc(pc: Any) -> Any | None:
    if pc is None:
        return None
    for attr in ("OakCharacter", "Pawn", "AcknowledgedPawn"):
        try:
            pawn = getattr(pc, attr, None)
        except Exception:
            pawn = None
        if pawn is not None:
            return pawn
    return None


def _anchor_pawn() -> tuple[Any | None, str]:
    try:
        from .spawn_helpers import resolve_spawn_anchor_actor

        actor, label = resolve_spawn_anchor_actor()
        if actor is not None:
            return actor, str(label or "anchor")
    except Exception:
        pass
    pawn = _pawn_for_pc(get_pc())
    return pawn, "local"


def _world_from_pc(pc: Any) -> Any | None:
    try:
        viewport = getattr(ENGINE, "GameViewport", None)
        world = getattr(viewport, "World", None) if viewport is not None else None
        if world is not None:
            return world
    except Exception:
        pass
    try:
        return getattr(pc, "World", None)
    except Exception:
        return None


def _gameplay_statics() -> Any | None:
    try:
        found = unrealsdk.find_object("GameplayStatics", "/Script/Engine.Default__GameplayStatics")
        if found is not None:
            return found
    except Exception:
        pass
    try:
        cls = unrealsdk.find_class("GameplayStatics")
        return getattr(cls, "ClassDefaultObject", None) if cls is not None else None
    except Exception:
        return None


def _make_struct(name: str, **fields: Any) -> Any:
    fn = getattr(unrealsdk, "make_struct", None)
    if not callable(fn):
        raise RuntimeError("unrealsdk.make_struct is unavailable")
    return fn(name, **fields)


def _spawn_transform(pawn: Any, *, index: int, count: int, distance: float, spacing: float, z_offset: float, scale: float) -> Any:
    loc = pawn.K2_GetActorLocation()
    fwd = pawn.GetActorForwardVector()
    total = max(1, int(count))
    offset = (float(index) - (float(total) - 1.0) / 2.0) * float(spacing)
    return _make_struct(
        "Transform",
        Rotation=_make_struct("Quat", X=0.0, Y=0.0, Z=0.0, W=1.0),
        Translation=_make_struct(
            "Vector",
            X=float(loc.X + fwd.X * distance - fwd.Y * offset),
            Y=float(loc.Y + fwd.Y * distance + fwd.X * offset),
            Z=float(loc.Z + z_offset),
        ),
        Scale3D=_make_struct("Vector", X=float(scale), Y=float(scale), Z=float(scale)),
    )


def _copy_actor_data(source: Any, actor: Any) -> list[str]:
    hits: list[str] = []
    try:
        src_data = getattr(source, "GbxActorData", None)
        dst_data = getattr(actor, "GbxActorData", None)
    except Exception:
        return hits
    if src_data is None or dst_data is None:
        return hits
    for field_name in _COPY_DATA_FIELDS:
        try:
            setattr(dst_data, field_name, getattr(src_data, field_name))
            hits.append(field_name)
        except Exception:
            continue
    return hits


def _call(obj: Any, names: tuple[str, ...], *args: Any) -> str:
    if obj is None:
        return ""
    for name in names:
        fn = getattr(obj, name, None)
        if not callable(fn):
            continue
        try:
            fn(*args)
            return name
        except TypeError:
            try:
                fn(*args[:1]) if args else fn()
                return name
            except Exception:
                continue
        except Exception:
            continue
    return ""


def _controller_of(actor: Any) -> Any | None:
    if actor is None:
        return None
    for attr in _CONTROLLER_ATTRS:
        try:
            ctrl = getattr(actor, attr, None)
        except Exception:
            ctrl = None
        if ctrl is None or _is_default(ctrl):
            continue
        return ctrl
    return None


def dump_combat_state(actor: Any) -> dict[str, Any]:
    """Controller / team / hostility snapshot for probes and logs."""
    ctrl = _controller_of(actor)
    info: dict[str, Any] = {
        "actor": _safe_str(actor)[:160],
        "name": str(getattr(actor, "Name", "") or "") if actor is not None else "",
        "def": _actor_def_name(actor) if actor is not None else "",
        "controller": _safe_str(ctrl)[:160],
        "controller_class": str(getattr(getattr(ctrl, "Class", None), "Name", "") or "") if ctrl is not None else "",
        "has_controller": ctrl is not None,
        "team": {},
    }
    for attr in _TEAM_ATTRS:
        try:
            value = getattr(actor, attr, None) if actor is not None else None
        except Exception:
            value = None
        if value is not None and not callable(value):
            info["team"][attr] = _safe_str(value)[:80]
        if ctrl is not None:
            try:
                cval = getattr(ctrl, attr, None)
            except Exception:
                cval = None
            if cval is not None and not callable(cval):
                info["team"][f"ctrl.{attr}"] = _safe_str(cval)[:80]
    for attr in ("Enemy", "Focus", "CombatTarget", "TargetActor", "CurrentEnemy"):
        try:
            value = getattr(ctrl, attr, None) if ctrl is not None else None
        except Exception:
            value = None
        if value is not None and not callable(value):
            info[attr] = _safe_str(value)[:80]
    if ctrl is not None:
        fn = getattr(ctrl, "GetEnemy", None)
        if callable(fn) and not info.get("Enemy"):
            try:
                value = fn()
            except Exception:
                value = None
            if value is not None:
                info["Enemy"] = _safe_str(value)[:80]
    return info


def _bind_controller(clone: Any, ctrl: Any) -> list[str]:
    hits: list[str] = []
    if clone is None or ctrl is None:
        return hits
    if _call(ctrl, ("Possess", "K2_Possess"), clone):
        hits.append("Possess")
    if _call(clone, ("PossessedBy",), ctrl):
        hits.append("PossessedBy")
    for attr in _CONTROLLER_ATTRS:
        try:
            setattr(clone, attr, ctrl)
            hits.append(f"clone.{attr}")
        except Exception:
            pass
    for attr in ("Pawn", "Character", "OakCharacter"):
        try:
            setattr(ctrl, attr, clone)
            hits.append(f"ctrl.{attr}")
        except Exception:
            pass
    return hits


def _find_controller_class(source: Any) -> Any | None:
    src_ctrl = _controller_of(source)
    if src_ctrl is not None:
        cls = getattr(src_ctrl, "Class", None)
        if cls is not None:
            return cls
    if source is not None:
        for attr in ("AIControllerClass", "ControllerClass"):
            try:
                cls = getattr(source, attr, None)
            except Exception:
                cls = None
            if cls is not None:
                return cls
    for class_name in _CONTROLLER_CLASS_NAMES:
        try:
            cls = unrealsdk.find_class(class_name)
        except Exception:
            cls = None
        if cls is not None:
            return cls
    return None


def _spawn_controller(cls: Any, gs: Any, world: Any, transform: Any) -> Any | None:
    if cls is None or gs is None or world is None:
        return None
    try:
        raw = gs.BeginDeferredActorSpawnFromClass(world, cls, transform, 1, None, 1)
        ctrl = _unwrap(raw)
    except Exception as exc:
        _log(f"AI controller deferred spawn failed: {exc!r}")
        return None
    if ctrl is None:
        return None
    try:
        finished = _unwrap(gs.FinishSpawningActor(ctrl, transform, 0))
    except Exception:
        finished = None
    spawned = finished or ctrl
    if spawned is None or _is_default(spawned):
        return None
    return spawned


def ensure_controller(clone: Any, source: Any, gs: Any, world: Any, transform: Any) -> tuple[Any | None, list[str]]:
    """Give the clone a live AI controller the game can run.

    Prefer APawn.SpawnDefaultController (game owns the brain). Fall back to
    spawning the source controller class / OakAIController and Possess.
    """
    hits: list[str] = []
    existing = _controller_of(clone)
    if existing is not None:
        hits.append("existing")
        return existing, hits

    ctrl_cls = _find_controller_class(source)
    if ctrl_cls is not None:
        for attr in ("AIControllerClass", "ControllerClass"):
            try:
                setattr(clone, attr, ctrl_cls)
                hits.append(attr)
            except Exception:
                pass
    if _call(clone, ("SpawnDefaultController", "SpawnController")):
        hits.append("SpawnDefaultController")
        spawned = _controller_of(clone)
        if spawned is not None:
            return spawned, hits

    ctrl = _spawn_controller(ctrl_cls, gs, world, transform)
    if ctrl is None:
        return None, hits
    hits.append("spawned_controller")
    hits.extend(_bind_controller(clone, ctrl))
    return _controller_of(clone) or ctrl, hits


def copy_combat_state(source: Any, clone: Any) -> list[str]:
    """Copy live combat / weapon / perception handles onto the moving clone."""
    hits: list[str] = []
    if source is None or clone is None:
        return hits
    for attr in _COMBAT_COPY_ATTRS:
        try:
            value = getattr(source, attr, None)
        except Exception:
            value = None
        if value is None or callable(value):
            continue
        try:
            setattr(clone, attr, value)
            hits.append(attr)
        except Exception:
            continue
    src_ctrl = _controller_of(source)
    dst_ctrl = _controller_of(clone)
    if src_ctrl is not None and dst_ctrl is not None:
        for attr in _COMBAT_COPY_ATTRS:
            try:
                value = getattr(src_ctrl, attr, None)
            except Exception:
                value = None
            if value is None or callable(value):
                continue
            try:
                setattr(dst_ctrl, attr, value)
                hits.append(f"ctrl.{attr}")
            except Exception:
                continue
    return hits


def find_hostile_team_donor(exclude: Any = None, player: Any = None) -> Any | None:
    """A loaded enemy pawn whose team we can steal if the Arjay source is allied."""
    skip = {_obj_addr(exclude) or id(exclude), _obj_addr(player) or id(player)}
    for class_name in _SCAN_CLASSES:
        try:
            objects = unrealsdk.find_all(class_name, False) or []
        except TypeError:
            try:
                objects = unrealsdk.find_all(class_name) or []
            except Exception:
                continue
        except Exception:
            continue
        for actor in objects:
            if actor is None or _is_default(actor) or _is_player_pawn(actor):
                continue
            key = _obj_addr(actor) or id(actor)
            if key in skip:
                continue
            label = f"{_actor_def_name(actor)} {_safe_str(actor)}"
            if is_clearly_friendly(label):
                continue
            low = label.lower()
            combatish = any(token in low for token in _COMBAT_OVERRIDE_TOKENS)
            has_team = False
            for attr in _TEAM_ATTRS:
                try:
                    value = getattr(actor, attr, None)
                except Exception:
                    value = None
                if value is not None and not callable(value):
                    has_team = True
                    break
            if combatish or has_team:
                return actor
    return None


def copy_team(source: Any, clone: Any) -> list[str]:
    """Copy live team/allegiance onto the clone pawn and its controller."""
    hits: list[str] = []
    if source is None or clone is None:
        return hits
    src_ctrl = _controller_of(source)
    dst_ctrl = _controller_of(clone)
    for attr in _TEAM_ATTRS:
        try:
            value = getattr(source, attr, None)
        except Exception:
            value = None
        if value is None and src_ctrl is not None:
            try:
                value = getattr(src_ctrl, attr, None)
            except Exception:
                value = None
        if value is None or callable(value):
            continue
        try:
            setattr(clone, attr, value)
            hits.append(attr)
        except Exception:
            pass
        if dst_ctrl is not None:
            try:
                setattr(dst_ctrl, attr, value)
                hits.append(f"ctrl.{attr}")
            except Exception:
                pass
        if _call(clone, ("SetTeam", "SetTeamId", "ChangeTeam", "AssignTeam"), value):
            hits.append("SetTeam")
        if dst_ctrl is not None and _call(
            dst_ctrl, ("SetTeam", "SetTeamId", "ChangeTeam", "AssignTeam"), value
        ):
            hits.append("ctrl.SetTeam")
    return hits


def set_hostile_to(clone: Any, target: Any) -> list[str]:
    """Fire every game hostility/target call on pawn, controller, and combat comps.

    A moving healthy clone already has a controller. The miss is target selection:
    SetEnemy alone can no-op on an allied PrisonBuddy team. Try StartCombat /
    SetHostile / Attack-Me methods on every combat object we can see.
    """
    hits: list[str] = []
    if clone is None or target is None:
        return hits
    objects: list[Any] = []
    ctrl = _controller_of(clone)
    if ctrl is not None:
        objects.append(ctrl)
    objects.append(clone)
    for attr in _COMBAT_COPY_ATTRS:
        try:
            comp = getattr(clone, attr, None)
        except Exception:
            comp = None
        if comp is not None and not callable(comp):
            objects.append(comp)
    seen: set[int] = set()
    for obj in objects:
        key = _obj_addr(obj) or id(obj)
        if key in seen:
            continue
        seen.add(key)
        for attr, value in _HOSTILE_FLAGS:
            try:
                setattr(obj, attr, value)
                hits.append(attr)
            except Exception:
                pass
        for meth in _HOSTILE_METHODS:
            fn = getattr(obj, meth, None)
            if not callable(fn):
                continue
            arg_sets: list[tuple[Any, ...]]
            if meth in ("SetHostile", "SetIsHostile"):
                arg_sets = ((True,), (target, True), (target,))
            elif meth == "SetPassive":
                arg_sets = ((False,),)
            else:
                arg_sets = ((target,), (target, True), (target, 1.0))
            for args in arg_sets:
                try:
                    fn(*args)
                    hits.append(meth)
                    break
                except TypeError:
                    continue
                except Exception:
                    continue
    try:
        from .spawn_helpers import _try_set_enemy

        if _try_set_enemy(clone, target):
            hits.append("attack_me")
    except Exception:
        pass
    return hits


def force_attack_me(clones: list[Any]) -> str:
    """Same Attack Me path that already works on live map enemies."""
    try:
        from .spawn_helpers import apply_aggro_to_tracked, note_spawned_actors

        note_spawned_actors(clones)
        return apply_aggro_to_tracked(mode="attack_me")
    except Exception as exc:
        return f"Attack Me failed: {exc!r}"


def arm_combat(
    clone: Any,
    source: Any,
    player: Any,
    gs: Any,
    world: Any,
    transform: Any,
    *,
    wanted: str = "",
) -> list[str]:
    """Make a moving, healthy clone actually fight the player."""
    hits: list[str] = []
    _ctrl, ctrl_hits = ensure_controller(clone, source, gs, world, transform)
    hits.extend(ctrl_hits)
    hits.extend(copy_combat_state(source, clone))
    donor = find_hostile_team_donor(exclude=clone, player=player)
    source_is_self = source is None or source is clone
    if donor is not None:
        hits.extend(copy_team(donor, clone))
        hits.append("team_from_hostile")
        if source_is_self:
            extra = copy_combat_state(donor, clone)
            if extra:
                hits.extend(extra)
                hits.append("combat_from_hostile")
    elif source is not None and source is not clone:
        hits.extend(copy_team(source, clone))
    source_label = _actor_def_name(source) or _safe_str(source) if source is not None else ""
    if is_clearly_friendly(wanted) and is_clearly_friendly(source_label):
        hits.append("friendly_skip_hostility")
        _log(f"combat arm (friendly): {','.join(hits) or 'none'}")
        return hits
    hostile = set_hostile_to(clone, player)
    hits.extend(hostile)
    hits.append("hostile" if hostile else "hostile_miss")
    state = dump_combat_state(clone)
    needs_rearm = not state.get("Enemy")
    team_blob = " ".join(str(v).lower() for v in (state.get("team") or {}).values())
    if any(tok in team_blob for tok in ("player", "friendly", "ally", "allied", "neutral")):
        needs_rearm = True
    if needs_rearm:
        if donor is not None:
            hits.extend(copy_team(donor, clone))
            hits.append("resteal_team")
        hits.extend(set_hostile_to(clone, player))
        hits.append("rearm_enemy")
        state = dump_combat_state(clone)
    _log(
        f"combat arm: {','.join(hits) or 'none'} "
        f"has_controller={state.get('has_controller')} "
        f"ctrl={state.get('controller_class') or state.get('controller')!r} "
        f"team={state.get('team')} enemy={state.get('Enemy')}"
    )
    return hits


def wake_actor(actor: Any) -> list[str]:
    """Unhide / collide / tick a live pawn the game already owns."""
    hits: list[str] = []
    for name, args in (
        ("SetActorHiddenInGame", (False,)),
        ("SetActorEnableCollision", (True,)),
        ("SetActorTickEnabled", (True,)),
    ):
        if _call(actor, (name,), *args):
            hits.append(name)
    for attr, value in (("bHidden", False), ("bHiddenEd", False)):
        try:
            setattr(actor, attr, value)
            hits.append(attr)
        except Exception:
            pass
    root = getattr(actor, "RootComponent", None) or getattr(actor, "Mesh", None)
    if root is not None:
        if _call(root, ("SetHiddenInGame",), False, True):
            hits.append("Root.SetHiddenInGame")
        if _call(root, ("SetVisibility",), True, True):
            hits.append("Root.SetVisibility")
        if _call(root, ("SetComponentTickEnabled",), True):
            hits.append("Root.SetComponentTickEnabled")
    return hits


def hide_actor(actor: Any) -> list[str]:
    hits: list[str] = []
    if _call(actor, ("SetActorHiddenInGame",), True):
        hits.append("SetActorHiddenInGame")
    if _call(actor, ("SetActorEnableCollision",), False):
        hits.append("SetActorEnableCollision")
    if _call(actor, ("SetActorTickEnabled",), False):
        hits.append("SetActorTickEnabled")
    try:
        actor.bHidden = True
        hits.append("bHidden")
    except Exception:
        pass
    return hits


def place_actor(actor: Any, transform: Any, pawn: Any) -> bool:
    """Move the live clone in front of the anchor. Game methods first."""
    dest = getattr(transform, "Translation", None)
    if dest is None:
        return False
    rot = None
    for name in ("K2_GetActorRotation", "GetActorRotation"):
        fn = getattr(pawn, name, None)
        if callable(fn):
            try:
                rot = fn()
                break
            except Exception:
                rot = None
    for name in ("K2_TeleportTo", "TeleportTo"):
        fn = getattr(actor, name, None)
        if not callable(fn):
            continue
        if rot is not None:
            try:
                if bool(fn(dest, rot)):
                    return True
            except TypeError:
                pass
            except Exception:
                pass
        try:
            if bool(fn(dest)):
                return True
        except Exception:
            pass
    fn = getattr(actor, "K2_SetActorLocation", None)
    if callable(fn):
        try:
            if bool(fn(dest, False, None, True)):
                return True
        except Exception:
            try:
                if bool(fn(dest)):
                    return True
            except Exception:
                pass
    return False


def destroy_actor(actor: Any) -> bool:
    ctrl = _controller_of(actor)
    ok = bool(_call(actor, ("K2_DestroyActor", "DestroyActor", "Destroy")))
    if ctrl is not None:
        _call(ctrl, ("K2_DestroyActor", "DestroyActor", "Destroy"))
    return ok


def _clone_live(source: Any, gs: Any, world: Any, transform: Any) -> Any | None:
    cls = getattr(source, "Class", None)
    if cls is None or gs is None or world is None:
        return None
    try:
        raw = gs.BeginDeferredActorSpawnFromClass(world, cls, transform, 1, None, 1)
        actor = _unwrap(raw)
    except Exception as exc:
        _log(f"BeginDeferredActorSpawnFromClass failed: {exc!r}")
        return None
    if actor is None:
        _log("BeginDeferredActorSpawnFromClass returned None")
        return None
    copied = _copy_actor_data(source, actor)
    try:
        finished = _unwrap(gs.FinishSpawningActor(actor, transform, 0))
    except Exception as exc:
        _log(f"FinishSpawningActor failed: {exc!r}")
        finished = None
    spawned = finished or actor
    if spawned is None or _is_default(spawned):
        return None
    _log(
        f"cloned {_safe_str(source)[:120]} -> {_safe_str(spawned)[:120]} "
        f"gbx={','.join(copied) or 'none'}"
    )
    return spawned


def _spawn_from_class(cls: Any, gs: Any, world: Any, transform: Any) -> Any | None:
    """Thin-air pawn from a resolved UClass. Same deferred spawn as a live clone."""
    if cls is None or gs is None or world is None:
        return None
    try:
        raw = gs.BeginDeferredActorSpawnFromClass(world, cls, transform, 1, None, 1)
        actor = _unwrap(raw)
    except Exception as exc:
        _log(f"thin-air BeginDeferredActorSpawnFromClass failed: {exc!r}")
        return None
    if actor is None:
        _log("thin-air BeginDeferredActorSpawnFromClass returned None")
        return None
    cdo = getattr(cls, "ClassDefaultObject", None)
    copied = _copy_actor_data(cdo, actor) if cdo is not None else []
    try:
        finished = _unwrap(gs.FinishSpawningActor(actor, transform, 0))
    except Exception as ext:
        _log(f"thin-air FinishSpawningActor failed: {ext!r}")
        finished = None
    spawned = finished or actor
    if spawned is None or _is_default(spawned):
        return None
    _log(
        f"thin-air class={_safe_str(cls)[:120]} -> {_safe_str(spawned)[:120]} "
        f"gbx={','.join(copied) or 'none'}"
    )
    return spawned


def _oak_spawner_class() -> Any | None:
    """Prefer Class from a live map OakSpawner (ASD's proven template), then find_class."""
    try:
        objects = unrealsdk.find_all("OakSpawner", False) or []
    except TypeError:
        try:
            objects = unrealsdk.find_all("OakSpawner") or []
        except Exception:
            objects = []
    except Exception:
        objects = []
    for spawner in objects:
        if spawner is None or _is_default(spawner):
            continue
        cls = getattr(spawner, "Class", None)
        if cls is not None:
            return cls
    return _find_class_by_name("OakSpawner")


def _alive_actors_for_comp(comp: Any) -> list[Any]:
    if comp is None:
        return []
    for args in ((0, False), (0, True), (0,), ()):
        try:
            actors = comp.GetAliveActors(*args)
        except TypeError:
            continue
        except Exception:
            continue
        try:
            return [actors[i] for i in range(len(actors))]
        except Exception:
            try:
                return list(actors)
            except Exception:
                return []
    return []


def _poll_alive_actors(comp: Any, wanted: str = "") -> list[Any]:
    """Wait until GetAliveActors is non-empty. Runs on the bridge thread, not a game tick."""
    deadline = time.monotonic() + _SPAWNER_POLL_TIMEOUT_S
    while True:
        actors = _alive_actors_for_comp(comp)
        if actors:
            return actors
        try:
            if int(comp.GetNumAliveActors(0)) > 0:
                actors = _alive_actors_for_comp(comp)
                if actors:
                    return actors
        except Exception:
            pass
        if wanted:
            found = find_live_sources(wanted)
            if found:
                _log(f"world scan found {wanted!r} while OakSpawner poll waited")
                return found
        if time.monotonic() >= deadline:
            return []
        time.sleep(_SPAWNER_POLL_INTERVAL_S)


def _disable_spawner(spawner: Any) -> None:
    if spawner is None:
        return
    try:
        comp = spawner.GetSpawnerComponent()
    except Exception:
        comp = None
    if comp is not None:
        try:
            comp.SetSpawnerEnabled(False)
        except Exception:
            pass
    destroy_actor(spawner)


def _remember_spawner(spawner: Any) -> None:
    global _throwaway_spawners
    if spawner is None:
        return
    _throwaway_spawners.append(spawner)
    if len(_throwaway_spawners) > 16:
        extra = _throwaway_spawners[:-16]
        _throwaway_spawners = _throwaway_spawners[-16:]
        for old in extra:
            _disable_spawner(old)


def _spawn_from_actor_def(
    wanted: str,
    gs: Any,
    world: Any,
    transform: Any,
    extra_loads: tuple[str, ...] = (),
) -> Any | None:
    """Proven thin-air path: FGbxDefPtr + throwaway OakSpawner + PushActorDef.

    Success only when GetAliveActors returns a pawn. Does not report an empty
    queue as ok.
    """
    _log(f"oak-spawner PushActorDef for {wanted!r}")
    for extra in extra_loads:
        extra = str(extra or "").strip()
        if extra:
            _try_load_package(extra)
    cls = _oak_spawner_class()
    if cls is None or gs is None or world is None:
        _log("OakSpawner class/world missing")
        return None
    try:
        raw = gs.BeginDeferredActorSpawnFromClass(world, cls, transform, 1, None, 1)
        spawner = _unwrap(raw)
    except Exception as exc:
        _log(f"OakSpawner BeginDeferredActorSpawnFromClass failed: {exc!r}")
        return None
    if spawner is None:
        return None
    try:
        finished = _unwrap(gs.FinishSpawningActor(spawner, transform, 0))
    except Exception:
        finished = None
    spawner = finished or spawner
    if spawner is None or _is_default(spawner):
        return None
    _remember_spawner(spawner)
    try:
        comp = spawner.GetSpawnerComponent()
    except Exception as exc:
        _log(f"GetSpawnerComponent failed: {exc!r}")
        return None
    d = _make_gbx_actor_def_ptr(wanted)
    if d is None:
        _log(f"FGbxDefPtr failed for {wanted!r}")
        return None
    try:
        comp.SetSpawnerEnabled(True)
    except Exception:
        pass
    try:
        comp.SetSpawnPointEnabled(True)
    except Exception:
        pass
    try:
        comp.PushActorDef("MSBT", d, True)
    except Exception as exc:
        _log(f"PushActorDef failed for {wanted!r}: {exc!r}")
        return None
    try:
        comp.ResetSpawner(True)
    except TypeError:
        try:
            comp.ResetSpawner()
        except Exception as exc:
            _log(f"ResetSpawner failed: {exc!r}")
            return None
    except Exception as exc:
        _log(f"ResetSpawner failed: {exc!r}")
        return None
    actors = _poll_alive_actors(comp, wanted)
    if not actors:
        actors = find_live_sources(wanted)
    if not actors:
        _log(f"PushActorDef {wanted!r} produced no alive pawn after {_SPAWNER_POLL_TIMEOUT_S:.1f}s")
        return None
    actor = actors[0]
    # Leave the throwaway spawner enabled. Disabling it here can despawn the pawn.
    # despawn_tracked() disables/destroys remembered spawners.
    _log(f"oak-spawner pawn {_safe_str(actor)[:120]}")
    return actor


def _remember(actor: Any, *, label: str, source: Any) -> None:
    global _tracked, _tracked_at
    _tracked.append(
        {
            "actor": actor,
            "addr": _obj_addr(actor),
            "name": str(getattr(actor, "Name", "") or "") or _safe_str(actor),
            "label": label,
            "source": _safe_str(source),
            "at": time.monotonic(),
        }
    )
    _tracked_at = time.monotonic()
    if len(_tracked) > 64:
        _tracked = _tracked[-64:]


def _prune_tracked() -> list[dict[str, Any]]:
    global _tracked, _tracked_at
    if _tracked_at and time.monotonic() - _tracked_at > _TRACK_TTL_S:
        _tracked = []
        _tracked_at = 0.0
        return []
    live: list[dict[str, Any]] = []
    for row in _tracked:
        actor = row.get("actor")
        if actor is None or _is_default(actor):
            continue
        try:
            name = str(getattr(actor, "Name", "") or "")
        except Exception:
            continue
        if not name:
            continue
        live.append(row)
    _tracked = live
    return list(_tracked)


def tracked_status() -> dict[str, Any]:
    rows = _prune_tracked()
    return {
        "ok": True,
        "hybrid": True,
        "tracked": len(rows),
        "actors": [str(row.get("name") or "") for row in rows],
        "message": f"ASD hybrid tracking {len(rows)} live clone(s).",
    }


def hide_tracked() -> dict[str, Any]:
    hidden = 0
    for row in _prune_tracked():
        if hide_actor(row.get("actor")):
            hidden += 1
    return {
        "ok": True,
        "hybrid": True,
        "hidden": hidden,
        "message": f"Hid {hidden} ASD hybrid clone(s).",
    }


def despawn_tracked() -> dict[str, Any]:
    """Destroy clones we spawned. World templates stay put."""
    global _tracked, _tracked_at, _throwaway_spawners
    rows = _prune_tracked()
    destroyed = 0
    hidden = 0
    for row in rows:
        actor = row.get("actor")
        if destroy_actor(actor):
            destroyed += 1
            continue
        if hide_actor(actor):
            hidden += 1
    _tracked = []
    _tracked_at = 0.0
    for spawner in list(_throwaway_spawners):
        _disable_spawner(spawner)
    _throwaway_spawners = []
    try:
        from .spawn_helpers import clear_tracked

        clear_tracked()
    except Exception:
        pass
    return {
        "ok": True,
        "hybrid": True,
        "despawned": destroyed,
        "hidden": hidden,
        "message": f"Despawned {destroyed} ASD hybrid clone(s)"
        + (f", hid {hidden} more" if hidden else "")
        + ".",
    }


def spawn_live(
    name: str,
    *,
    count: int = 1,
    distance: float = 350.0,
    spacing: float = 125.0,
    scale: float = 1.0,
    z_offset: float = 0.0,
    extra_loads: tuple[str, ...] | list[str] = (),
    hints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Spawn a catalog actor in front of the spawn anchor.

    Clone a live match when one exists. Else deferred-spawn from a UClass.
    If no UClass can be resolved, use the proven FGbxDefPtr + throwaway
    OakSpawner + PushActorDef path and wait until GetAliveActors is non-empty.
    """
    wanted = str(name or "").strip()
    requested = max(1, int(count))
    extra = tuple(str(p).strip() for p in (extra_loads or ()) if str(p).strip())
    result: dict[str, Any] = {
        "ok": False,
        "hybrid": True,
        "mode": "asd_hybrid_clone",
        "requested_count": requested,
        "verification_status": "unknown",
        "spawn_verified": False,
        "spawned_count": 0,
        "alive_count": 0,
        "actor_names": [],
        "source_path": "",
        "combat": [],
        "message": "",
    }
    if not wanted:
        result["message"] = "ASD hybrid needs an actor-def / catalog name."
        result["verification_status"] = "no_name"
        return result

    _log(f"spawn_live {wanted!r} count={requested}")
    pawn, anchor_label = _anchor_pawn()
    pc = get_pc()
    world = _world_from_pc(pc)
    gs = _gameplay_statics()
    if pawn is None or world is None or gs is None:
        result["verification_status"] = "no_world"
        result["message"] = "ASD hybrid needs a live pawn, world, and GameplayStatics."
        _log(result["message"])
        return result

    sources = find_live_sources(wanted)
    spawn_cls, class_how = (None, "")
    if not sources:
        spawn_cls, class_how = resolve_spawn_class(wanted, extra, hints)

    source = sources[0] if sources else None
    spawned: list[Any] = []
    names: list[str] = []
    combat_hits: list[str] = []
    mode_label = "cloned"
    result["source_path"] = _safe_str(source) if source is not None else ""
    for idx in range(requested):
        try:
            transform = _spawn_transform(
                pawn,
                index=idx,
                count=requested,
                distance=float(distance),
                spacing=float(spacing),
                z_offset=float(z_offset),
                scale=float(scale),
            )
        except Exception as exc:
            result["message"] = f"ASD hybrid spawn transform failed: {exc!r}"
            result["verification_status"] = "clone_failed"
            return result
        actor = None
        if source is not None:
            actor = _clone_live(source, gs, world, transform)
            mode_label = "cloned"
            result["source_path"] = _safe_str(source)
        if actor is None and spawn_cls is not None:
            actor = _spawn_from_class(spawn_cls, gs, world, transform)
            if actor is not None:
                mode_label = "thin-air"
                result["source_path"] = f"class:{class_how}"
        if actor is None:
            actor = _spawn_from_actor_def(wanted, gs, world, transform, extra)
            if actor is not None:
                mode_label = "oak-spawner"
                result["source_path"] = f"PushActorDef:{wanted}"
        if actor is None:
            continue
        place_actor(actor, transform, pawn)
        wake_actor(actor)
        combat_hits.extend(
            arm_combat(
                actor,
                source if source is not None else actor,
                pawn,
                gs,
                world,
                transform,
                wanted=wanted,
            )
        )
        if float(scale) != 1.0:
            try:
                actor.SetActorScale3D(
                    _make_struct("Vector", X=float(scale), Y=float(scale), Z=float(scale))
                )
            except Exception:
                pass
        _remember(actor, label=wanted, source=source if source is not None else spawn_cls or wanted)
        spawned.append(actor)
        names.append(str(getattr(actor, "Name", "") or "") or _safe_str(actor))

    if not spawned:
        delayed = find_live_sources(wanted)
        if delayed:
            actor = delayed[0]
            _log(f"delayed pawn after empty GetAliveActors: {_safe_str(actor)[:120]}")
            try:
                transform = _spawn_transform(
                    pawn,
                    index=0,
                    count=1,
                    distance=float(distance),
                    spacing=float(spacing),
                    z_offset=float(z_offset),
                    scale=float(scale),
                )
            except Exception:
                transform = None
            if transform is not None:
                place_actor(actor, transform, pawn)
            wake_actor(actor)
            combat_hits.extend(
                arm_combat(actor, actor, pawn, gs, world, transform, wanted=wanted)
            )
            _remember(actor, label=wanted, source=wanted)
            spawned.append(actor)
            names.append(str(getattr(actor, "Name", "") or "") or _safe_str(actor))
            mode_label = "oak-spawner"
            result["source_path"] = f"delayed:{wanted}"

    if not spawned:
        result["verification_status"] = "no_pawn"
        result["message"] = (
            f"No live {wanted} pawn after clone/class/OakSpawner+PushActorDef "
            f"(class={class_how or 'n/a'}). GetAliveActors stayed empty."
        )
        _log(result["message"])
        return result

    attack_msg = force_attack_me(spawned)
    if attack_msg:
        combat_hits.append(attack_msg)

    result.update(
        {
            "ok": True,
            "verification_status": "verified_spawned",
            "spawn_verified": True,
            "spawned_count": len(spawned),
            "alive_count": len(spawned),
            "actor_names": names,
            "combat": combat_hits,
            "mode": (
                "asd_hybrid_clone"
                if mode_label == "cloned"
                else "asd_hybrid_class"
                if mode_label == "thin-air"
                else "asd_hybrid_spawner"
            ),
            "message": (
                f"ASD hybrid {mode_label} {len(spawned)} {wanted} "
                f"at {anchor_label} from {result['source_path'][:80]}"
                + (f" combat={','.join(combat_hits)}" if combat_hits else "")
                + "."
            ),
        }
    )
    _log(result["message"])
    return result
