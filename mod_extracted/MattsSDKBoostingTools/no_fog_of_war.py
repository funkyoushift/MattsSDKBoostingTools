"""MSBT No Fog of War — hide big-map fog overlay (SDK port of 000_NoFogofWar_P).

Port of tools/NoFogOfWar. Material opacity edits are process/client-local.
Targeted MSBT actions resolve a party player for messaging / Max All, then apply
fog hide on this machine. Guests still need their own client apply for their map.
"""

from __future__ import annotations

import time
from typing import Any

from mods_base import get_pc, hook
from unrealsdk import find_all, find_object, logging
from unrealsdk.hooks import Type
from unrealsdk.unreal import BoundFunction, UObject, WrappedStruct

__version__ = "0.2.0"
__version_info__ = (0, 2, 0)

_PREFIX = "[Matts SDK Boosting Tools | Fog]"
_OPACITY_PARAMS = (
    "MaxOpacity",
    "Fog",
    "RippleOpacity",
    "Opacity",
    "FogOpacity",
    "FogAmount",
    "Amount",
)

_ORIGINAL: dict[str, dict[str, float]] = {}
_TICK = 0
_LAST_TOUCH_LOG = 0
_LAST_MATERIAL_COUNT = 0
_LAST_MAINTAIN_AT = 0.0
_MAINTAIN_INTERVAL_S = 10.0

_enabled = False


def _log(msg: str) -> None:
    try:
        logging.info(f"{_PREFIX} {msg}")
    except Exception:
        print(f"{_PREFIX} {msg}")


_hot_error_last_at: dict[str, float] = {}


def _log_hot_error(msg: str) -> None:
    now = time.monotonic()
    if now - _hot_error_last_at.get(msg, 0.0) < 5.0:
        return
    _hot_error_last_at[msg] = now
    _log(msg)


def _obj_key(obj: Any) -> str:
    try:
        return str(obj)
    except Exception:
        return repr(obj)


def _looks_like_fog_mat(path: str) -> bool:
    lower = path.lower()
    if "default__" in lower or "/script/" in lower:
        return False
    return any(
        token in lower
        for token in (
            "bigmapfog",
            "mi_bigmapfog",
            "m_bigmapfog",
            "mapfog",
            "fogripple",
            "fog_of_war",
            "fogofwar",
        )
    )


def _iter_fog_materials() -> list[Any]:
    found: list[Any] = []
    seen: set[str] = set()

    def _add(obj: Any) -> None:
        if obj is None:
            return
        key = _obj_key(obj)
        if key in seen:
            return
        if not _looks_like_fog_mat(key):
            # Still allow exact MI path even if filter is picky about formatting.
            if "bigmapfogripple" not in key.lower() and "mapfog" not in key.lower():
                return
        seen.add(key)
        found.append(obj)

    paths = (
        "/Game/GameData/Map/Materials/MI_BigMapFogRipple.MI_BigMapFogRipple",
        "/Game/GameData/Map/Materials/MI_BigMapFogRipple",
        "/Game/GameData/Map/Materials/M_BigMapFogRipple.M_BigMapFogRipple",
        "/Game/GameData/Map/Materials/M_BigMapFogRipple",
    )
    for cls_name in (
        "MaterialInstanceConstant",
        "MaterialInstanceDynamic",
        "MaterialInstance",
        "Material",
        "Object",
    ):
        for path in paths:
            try:
                _add(find_object(cls_name, path))
            except Exception:
                pass

    for class_name in (
        "MaterialInstanceConstant",
        "MaterialInstanceDynamic",
        "MaterialInstance",
        "Material",
    ):
        try:
            objs = list(find_all(class_name, False))
        except TypeError:
            try:
                objs = list(find_all(class_name))
            except Exception:
                objs = []
        except Exception:
            objs = []
        for obj in objs:
            _add(obj)
    return found


def _param_name(entry: Any) -> str:
    for attr in ("ParameterInfo", "Info"):
        try:
            info = getattr(entry, attr, None)
        except Exception:
            info = None
        if info is None:
            continue
        for name_attr in ("Name", "ParameterName"):
            try:
                name = getattr(info, name_attr, None)
            except Exception:
                name = None
            if name is not None:
                return str(name)
    for name_attr in ("ParameterName", "Name"):
        try:
            name = getattr(entry, name_attr, None)
        except Exception:
            name = None
        if name is not None:
            return str(name)
    return ""


def _read_scalars(mat: Any) -> dict[str, float]:
    out: dict[str, float] = {}
    try:
        values = list(getattr(mat, "ScalarParameterValues", []) or [])
    except Exception:
        values = []
    for entry in values:
        name = _param_name(entry)
        if not name:
            continue
        try:
            out[name] = float(getattr(entry, "ParameterValue"))
        except Exception:
            continue
    return out


def _set_scalar(mat: Any, name: str, value: float) -> bool:
    ok = False
    for fn_name in ("SetScalarParameterValue", "SetScalarParameterValueByInfo"):
        fn = getattr(mat, fn_name, None)
        if not callable(fn):
            continue
        try:
            fn(str(name), float(value))
            ok = True
        except Exception:
            try:
                fn(name, float(value))
                ok = True
            except Exception:
                pass

    try:
        values = list(getattr(mat, "ScalarParameterValues", []) or [])
    except Exception:
        values = []
    changed = False
    for entry in values:
        if _param_name(entry) != str(name):
            continue
        try:
            setattr(entry, "ParameterValue", float(value))
            changed = True
            ok = True
        except Exception:
            pass
    if changed:
        try:
            setattr(mat, "ScalarParameterValues", values)
        except Exception:
            pass
    return ok


def apply_no_fog(*, force: bool = True) -> tuple[int, int, list[str]]:
    global _LAST_MATERIAL_COUNT
    mats = _iter_fog_materials()
    _LAST_MATERIAL_COUNT = len(mats)
    touched = 0
    params = 0
    details: list[str] = []
    for mat in mats:
        key = _obj_key(mat)
        current = _read_scalars(mat)
        if key not in _ORIGINAL:
            _ORIGINAL[key] = dict(current)

        targets = [n for n in _OPACITY_PARAMS if n in current]
        if not force and targets and all(abs(float(current[n])) < 1e-6 for n in targets):
            # Already hidden. Avoid setter calls and render cache/recompile work.
            continue
        if not targets:
            targets = list(_OPACITY_PARAMS)

        any_ok = False
        for name in targets:
            if _set_scalar(mat, name, 0.0):
                params += 1
                any_ok = True
        if any_ok:
            touched += 1
            details.append(key)
            for fn_name in (
                "UpdateCachedData",
                "UpdateParameterSet",
                "ForceRecompileForRendering",
                "RecacheUniformExpressions",
            ):
                fn = getattr(mat, fn_name, None)
                if callable(fn):
                    try:
                        fn()
                    except Exception:
                        pass
    return touched, params, details


def restore_fog() -> tuple[int, int]:
    global _LAST_MATERIAL_COUNT
    live = {_obj_key(m): m for m in _iter_fog_materials()}
    _LAST_MATERIAL_COUNT = len(live)
    restored = 0
    params = 0
    for key, original in list(_ORIGINAL.items()):
        mat = live.get(key)
        if mat is None:
            continue
        ok = False
        for name in _OPACITY_PARAMS:
            if name not in original:
                continue
            if _set_scalar(mat, name, float(original[name])):
                params += 1
                ok = True
        if ok:
            restored += 1
    return restored, params



def on_enable() -> None:
    global _enabled, _LAST_MAINTAIN_AT
    _enabled = True
    touched, params, details = apply_no_fog()
    _LAST_MAINTAIN_AT = time.monotonic()
    _log(f"enabled v{__version__} touched={touched} params={params}")
    for d in details[:8]:
        _log(f"  mat {d}")
    if touched == 0:
        _log("WARNING: no BigMap fog materials found yet — open the world map, then re-apply")


def on_disable() -> None:
    global _enabled
    _enabled = False
    restored, params = restore_fog()
    _log(f"disabled restored={restored} params={params}")


def set_enabled(enabled: bool) -> str:
    if enabled:
        on_enable()
        return "Fog hide ON (client-local map materials)"
    on_disable()
    return "Fog hide OFF (restored backups where possible)"


def toggle_enabled() -> str:
    return set_enabled(not bool(_enabled))


def clear_fog(*, force: bool = True) -> str:
    """Apply fog hide once (used by Max All / targeted clear). Enables maintain mode."""
    global _enabled, _LAST_TOUCH_LOG, _LAST_MAINTAIN_AT
    _enabled = True
    touched, params, details = apply_no_fog(force=force)
    _LAST_MAINTAIN_AT = time.monotonic()
    _LAST_TOUCH_LOG = _TICK
    msg = f"Fog clear touched={touched} params={params}"
    if touched == 0:
        msg += " (open world map then retry if still foggy)"
    _log(msg)
    for d in details[:6]:
        _log(f"  {d}")
    return msg


def get_status_dict() -> dict[str, Any]:
    return {
        "enabled": bool(_enabled),
        # Status is polled by Electron; never run global material scans here.
        "materials": int(_LAST_MATERIAL_COUNT),
        "backups": len(_ORIGINAL),
        "ticks": int(_TICK),
        "scope": "client_local",
        "caveat": "Big-map fog materials are client-local; guests need their own clear for their map view.",
    }


def clear_travel_backups() -> None:
    """Forget material wrappers and originals belonging to the unloaded world."""
    global _LAST_MATERIAL_COUNT, _LAST_MAINTAIN_AT
    _ORIGINAL.clear()
    _LAST_MATERIAL_COUNT = 0
    _LAST_MAINTAIN_AT = 0.0


def status_message() -> str:
    st = get_status_dict()
    return (
        f"Fog hide enabled={st['enabled']} materials={st['materials']} "
        f"backups={st['backups']} (client-local)"
    )


@hook(
    "OakGame.OakPlayerController:PlayerTick",
    Type.POST,
    immediately_enable=True,
    hook_identifier="msbt_nfow_ptick_oak_v1",
)
@hook(
    "Engine.PlayerController:PlayerTick",
    Type.POST,
    immediately_enable=True,
    hook_identifier="msbt_nfow_ptick_engine_v1",
)
def _tick(_obj: UObject, _args: WrappedStruct, _ret: Any, _func: BoundFunction) -> None:
    global _TICK, _LAST_TOUCH_LOG, _LAST_MAINTAIN_AT
    if not bool(_enabled):
        return
    _TICK += 1
    now = time.monotonic()
    if now - _LAST_MAINTAIN_AT < _MAINTAIN_INTERVAL_S:
        return
    try:
        local = get_pc()
        if local is not None and _obj is not local:
            return
    except Exception:
        pass
    _LAST_MAINTAIN_AT = now
    try:
        touched, params, _details = apply_no_fog(force=False)
    except Exception as exc:
        _log_hot_error(f"periodic re-apply failed: {exc!r}")
        return
    if touched and _TICK - _LAST_TOUCH_LOG > 600:
        _LAST_TOUCH_LOG = _TICK
        _log(f"periodic re-apply touched={touched} params={params}")


@hook(
    "OakGame.OakPlayerController:ClientTravel",
    Type.POST,
    immediately_enable=True,
    hook_identifier="msbt_nfow_travel_oak_v1",
)
@hook(
    "Engine.PlayerController:ClientTravel",
    Type.POST,
    immediately_enable=True,
    hook_identifier="msbt_nfow_travel_engine_v1",
)
def _travel(*_args: Any, **_kwargs: Any) -> None:
    if bool(_enabled):
        try:
            touched, params, _details = apply_no_fog()
            _log(f"travel re-apply touched={touched} params={params}")
        except Exception as exc:
            _log_hot_error(f"travel re-apply failed: {exc!r}")


_log(f"loaded v{__version__} (MSBT helper, starts OFF)")
