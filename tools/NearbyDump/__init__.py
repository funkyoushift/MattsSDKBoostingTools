"""Dump nearby / map-wide live objects by name needle — for DLC collectables ping can't target."""
from __future__ import annotations

import math
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from mods_base import CoopSupport, Game, build_mod, command, get_pc
from unrealsdk import find_all, logging

__version__ = "0.4.0"

_MOD_DIR = Path(__file__).resolve().parent
_LOG = "[NearbyDump]"

# Prefer interactive/collectible classes — avoid find_all("Actor") (40k+) when needle is set.
# LootableObject early: Mandolin red coin-chests report as LootableObject'...' under OakInteractiveObject.
# OakSpawner: Mandolin arcade coins are mission-spawned (OakSpawner_Token_1..15), not PersistentLevel UAIDs.
_CLASS_TRIES: tuple[str, ...] = (
    "LootableObject",
    "OakLootableObject",
    "OakInteractiveObject",
    "OakInteractableObject",
    "InteractiveObject",
    "GbxInteractiveObject",
    "OakCollectible",
    "Collectible",
    "OakMissionPickup",
    "MissionPickup",
    "InventoryPickup",
    "OakInventoryPickup",
    "UsableObject",
    "OakUsableObject",
    "OakUsableActor",
    "OakUseableActor",
    "OakLootable",
    "OakLootableContainer",
    "OakSpawner",
    "Spawner",
    "OakMissionScriptedActor",
    "StaticMeshActor",
    "Actor",  # last resort only: nearby + empty needle; never world-wide
)

_ACTOR_HARD_CAP = 8000
_PER_CLASS_MATCH_CAP = 250
_OUTPUT_HIT_CAP = 200
# Soft upper bound for explicit radii (map-scale). 0 = unlimited / no distance filter.
_RADIUS_SOFT_MAX = 500_000.0


def _loc(obj: Any) -> tuple[float, float, float] | None:
    try:
        t = getattr(obj, "K2_GetActorLocation", None)
        if callable(t):
            v = t()
            return float(v.X), float(v.Y), float(v.Z)
    except Exception:
        pass
    try:
        root = getattr(obj, "RootComponent", None) or getattr(obj, "CapsuleComponent", None)
        if root is None:
            return None
        loc = getattr(root, "RelativeLocation", None) or getattr(root, "K2_GetComponentLocation", None)
        if callable(loc):
            v = loc()
            return float(v.X), float(v.Y), float(v.Z)
        if loc is not None:
            return float(loc.X), float(loc.Y), float(loc.Z)
    except Exception:
        pass
    return None


def _pc_loc() -> tuple[float, float, float] | None:
    pc = get_pc()
    if pc is None:
        return None
    try:
        pawn = getattr(pc, "Pawn", None) or getattr(pc, "AcknowledgedPawn", None)
        if pawn is not None:
            return _loc(pawn)
    except Exception:
        pass
    return _loc(pc)


def _dist(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def _safe_find(cls: str) -> list[Any]:
    try:
        objs = list(find_all(cls, False) or [])
        if objs:
            return objs
    except Exception:
        pass
    try:
        return list(find_all(cls) or [])
    except Exception:
        return []


def _parse_radius(args: Any, default: float = 2000.0) -> float:
    """Parse radius. 0 (or negative) = no distance filter (world / map-wide)."""
    raw = getattr(args, "radius", default)
    if raw is None or (isinstance(raw, str) and not str(raw).strip()):
        return default
    try:
        radius = float(raw)
    except Exception:
        return default
    if radius <= 0:
        return 0.0
    return min(radius, _RADIUS_SOFT_MAX)


def _candidate_dump_dirs() -> list[Path]:
    """sdk_mods path first, then always %LOCALAPPDATA%\\NearbyDump\\dumps (writable fallback)."""
    dirs: list[Path] = [_MOD_DIR / "dumps"]
    local_app = (os.environ.get("LOCALAPPDATA") or "").strip()
    if local_app:
        dirs.append(Path(local_app) / "NearbyDump" / "dumps")
    # De-dupe while preserving order
    out: list[Path] = []
    seen: set[str] = set()
    for d in dirs:
        key = str(d).lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(d)
    return out


def _write_dump_files(lines: list[str]) -> list[Path]:
    """Write stamped + latest under every writable dump dir. Returns paths written."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    text = "\n".join(lines) + "\n"
    written: list[Path] = []
    for dump_dir in _candidate_dump_dirs():
        try:
            dump_dir.mkdir(parents=True, exist_ok=True)
            stamped = dump_dir / f"nearby_dump_{stamp}.txt"
            latest = dump_dir / "nearby_dump_latest.txt"
            stamped.write_text(text, encoding="utf-8")
            latest.write_text(text, encoding="utf-8")
            written.append(stamped)
            written.append(latest)
            logging.info(f"{_LOG} wrote dump: {stamped}")
            logging.info(f"{_LOG} wrote latest: {latest}")
        except Exception as exc:
            logging.error(f"{_LOG} failed to write under {dump_dir}: {exc!r}")
    return written


def _emit(line: str, lines: list[str]) -> None:
    lines.append(line)
    logging.info(line)


def _scan(
    *,
    needle: str,
    radius: float,
    origin: tuple[float, float, float],
    lines: list[str],
    class_list: tuple[str, ...] | None = None,
) -> list[tuple[float, str, str]]:
    """Scan preferred classes; radius 0 = no distance filter. Skip Actor when unsafe."""
    hits: list[tuple[float, str, str]] = []
    seen: set[str] = set()
    needle_l = needle.strip().lower()
    unlimited = radius <= 0
    classes = class_list if class_list is not None else _CLASS_TRIES

    for cls in classes:
        # Never world-scan Actor; never Actor when filtering by name (prefer IO classes).
        if cls == "Actor" and (unlimited or needle_l):
            _emit(
                f"{_LOG} skip find_all(Actor) "
                f"(unlimited={unlimited} needle={bool(needle_l)})",
                lines,
            )
            continue

        objs = _safe_find(cls)
        if not objs:
            continue
        if cls == "Actor" and len(objs) > _ACTOR_HARD_CAP:
            _emit(f"{_LOG} skip huge find_all(Actor) count={len(objs)}", lines)
            continue

        matched = 0
        for obj in objs:
            key = str(obj)
            if key in seen:
                continue
            low = key.lower()
            if needle_l and needle_l not in low:
                try:
                    cname = type(obj).__name__.lower()
                except Exception:
                    cname = ""
                if needle_l not in cname:
                    continue
            loc = _loc(obj)
            # Spawners / CDOs may lack a world location — still list them when unlimited.
            if loc is None:
                if unlimited:
                    seen.add(key)
                    hits.append((999_999.0, cls, key))
                    matched += 1
                    if matched >= _PER_CLASS_MATCH_CAP:
                        break
                continue
            d = _dist(origin, loc)
            if not unlimited and d > radius:
                continue
            seen.add(key)
            hits.append((d, cls, key))
            matched += 1
            if matched >= _PER_CLASS_MATCH_CAP:
                break
        kept_label = "kept_all" if unlimited else "kept_near"
        _emit(f"{_LOG} class={cls} scanned={len(objs)} {kept_label}={matched}", lines)
        if cls == "Actor":
            break

    hits.sort(key=lambda row: row[0])
    return hits


def _run_dump(
    *,
    needle: str,
    radius: float,
    mode: str,
    class_list: tuple[str, ...] | None = None,
) -> None:
    origin = _pc_loc()
    if origin is None:
        logging.error(f"{_LOG} No player location.")
        return

    radius_desc = "unlimited (no distance filter)" if radius <= 0 else f"{radius:g}"
    class_note = (
        f"classes={list(class_list)}" if class_list is not None else "classes=default"
    )
    lines: list[str] = [
        f"{_LOG} mode={mode} version={__version__}",
        f"{_LOG} origin={origin} needle={needle!r} radius={radius_desc}",
        f"{_LOG} {class_note}",
        f"{_LOG} mod_dir={_MOD_DIR}",
        f"{_LOG} dump_dirs={[str(p) for p in _candidate_dump_dirs()]}",
    ]
    hits = _scan(
        needle=needle,
        radius=radius,
        origin=origin,
        lines=lines,
        class_list=class_list,
    )
    shown = hits[:_OUTPUT_HIT_CAP]
    _emit(f"{_LOG} === {len(hits)} hit(s) (showing {len(shown)}/{_OUTPUT_HIT_CAP} max) ===", lines)
    for d, cls, key in shown:
        _emit(f"{_LOG} d={d:.0f} cls={cls} {key}", lines)

    if len(hits) > _OUTPUT_HIT_CAP:
        tip_more = f"{_LOG} truncated: {len(hits) - _OUTPUT_HIT_CAP} more hit(s) not listed"
        lines.append(tip_more)
        logging.warning(tip_more)

    if not hits:
        tip = (
            f"{_LOG} No hits. Try: find_dump CoinToken | find_dump_class LootableObject CoinToken | "
            "find_dump_class OakSpawner Token | find_dump Interactable | nearby_dump coin 50000"
        )
        lines.append(tip)
        logging.warning(tip)

    written = _write_dump_files(lines)
    if not written:
        logging.error(f"{_LOG} no dump files written (all paths failed)")
    else:
        # Append write paths into each successfully written file for copy/paste.
        footer = "\n".join(f"{_LOG} wrote: {p}" for p in written) + "\n"
        for path in written:
            try:
                with path.open("a", encoding="utf-8") as fh:
                    fh.write(footer)
            except Exception:
                pass


@command(
    "nearby_dump",
    description=(
        "List live objects by name needle. Usage: nearby_dump [needle] [radius]. "
        "radius 0 = map-wide (no distance filter). Example: nearby_dump CoinToken 0"
    ),
)
def nearby_dump(args: Any = None) -> None:
    needle = str(getattr(args, "needle", "") or "").strip() or "coin"
    radius = _parse_radius(args, 2000.0)
    _run_dump(needle=needle, radius=radius, mode="nearby_dump")


nearby_dump.add_argument("needle", nargs="?", default="coin", help="Substring to match in object path/name.")
nearby_dump.add_argument(
    "radius",
    nargs="?",
    default=2000,
    help="Search radius (uu). 0 = no distance filter (list all matches sorted by distance).",
)


@command(
    "find_dump",
    description=(
        "Map-wide dump: scan matching live objects with NO distance filter. "
        "Usage: find_dump [needle]. Example: find_dump CoinToken"
    ),
)
def find_dump(args: Any = None) -> None:
    needle = str(getattr(args, "needle", "") or "").strip() or "CoinToken"
    _run_dump(needle=needle, radius=0.0, mode="find_dump")


find_dump.add_argument(
    "needle",
    nargs="?",
    default="CoinToken",
    help="Substring to match (default CoinToken). Scans OakInteractiveObject etc., no Actor dump.",
)


@command(
    "find_dump_class",
    description=(
        "Map-wide dump for ONE Unreal class + optional name needle. "
        "Usage: find_dump_class <ClassName> [needle]. "
        "Example: find_dump_class LootableObject CoinToken | find_dump_class OakSpawner Token"
    ),
)
def find_dump_class(args: Any = None) -> None:
    cls = str(getattr(args, "cls", "") or "").strip()
    needle = str(getattr(args, "needle", "") or "").strip()
    if not cls:
        logging.error(f"{_LOG} Usage: find_dump_class <ClassName> [needle]")
        return
    _run_dump(
        needle=needle,
        radius=0.0,
        mode="find_dump_class",
        class_list=(cls,),
    )


find_dump_class.add_argument("cls", help="Unreal class to find_all (e.g. LootableObject, OakSpawner).")
find_dump_class.add_argument(
    "needle",
    nargs="?",
    default="",
    help="Optional substring filter (empty = list all instances of the class).",
)


@command(
    "nearby_dump_all",
    description=(
        "List nearby interactive/collectible-ish objects (empty needle). "
        "Usage: nearby_dump_all [radius]. radius 0 = unlimited on preferred classes only. "
        "Example: nearby_dump_all 2500"
    ),
)
def nearby_dump_all(args: Any = None) -> None:
    radius = _parse_radius(args, 2000.0)
    _run_dump(needle="", radius=radius, mode="nearby_dump_all")


nearby_dump_all.add_argument(
    "radius",
    nargs="?",
    default=2000,
    help="Search radius (uu). 0 = no distance filter on preferred classes (skips Actor).",
)

build_mod(
    name="NearbyDump",
    author="MSBT helper",
    description=(
        "Dump nearby or map-wide live objects by name needle (DLC collectables). "
        "Commands: nearby_dump [needle] [radius], find_dump [needle], "
        "find_dump_class <Class> [needle], nearby_dump_all [radius]. "
        "radius 0 / find_dump = no distance filter. Writes dumps under mod dumps/ and "
        "%LOCALAPPDATA%\\NearbyDump\\dumps\\."
    ),
    supported_games=Game.BL4,
    coop_support=CoopSupport.ClientSide,
    commands=[nearby_dump, find_dump, find_dump_class, nearby_dump_all],
)
