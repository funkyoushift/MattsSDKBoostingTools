"""Best-effort item labels from @U serials + bundled gzo_parts_map.json.

Used by inventory serial reads (bridge / Quick Menu / Electron Inventory tab).
Does not import blimgui.

Display names prefer unique/legendary/pearl composition suffixes from the GZO
parts map (e.g. PRISM, Silver Sliver). Falls back to manufacturer + type.
Rarity is best-effort from composition keys / part-name keywords — not a
pixel-perfect game rarity decode.
"""
from __future__ import annotations

import json
import pkgutil
import re
from typing import Any

_GZO_PARTS_MAP: dict[str, dict[str, str]] | None = None
_GZO_TYPE_ID_INDEX: dict[int, tuple[str, dict[str, str]]] | None = None

_GZO_MAKER_PREFIXES = {
    "DAD": "Daedalus",
    "JAK": "Jakobs",
    "ORD": "Order",
    "TED": "Tediore",
    "TOR": "Torgue",
    "VLA": "Vladof",
    "MAL": "Maliwan",
    "BOR": "Ripper",
    "RIP": "Ripper",
    "COV": "CoV",
    "ATL": "Atlas",
    "HYP": "Hyperion",
    "C4SH": "C4SH",
}

_GZO_TYPE_SUFFIXES = {
    "PS": "Pistol",
    "SG": "Shotgun",
    "AR": "Assault Rifle",
    "SMG": "SMG",
    "SR": "Sniper",
    "HW": "Heavy Weapon",
    "HEAVY": "Heavy Weapon",
    "SHIELD": "Shield",
    "ARMOR_SHIELD": "Shield",
    "ENERGY_SHIELD": "Shield",
    "GADGET": "Ordnance",
    "GRENADE_GADGET": "Ordnance",
    "TURRET_GADGET": "Ordnance",
    "HEAVY_WEAPON_GADGET": "Ordnance",
    "TERMINAL_GADGET": "Ordnance",
    "TERMINAL_BARRIER": "Ordnance",
    "BARRIER": "Ordnance",
    "ORDNANCE": "Ordnance",
    "ENHANCEMENT": "Enhancement",
    "REPAIR_KIT": "Repkit",
    "REPKIT": "Repkit",
    "CLASS_MOD": "Classmod",
    "CLASSMOD": "Classmod",
}

# Extra substring → type when family labels are noisy (e.g. BOR_TERMINAL_BARRIER).
_GZO_TYPE_HINTS: tuple[tuple[str, str], ...] = (
    ("classmod", "Classmod"),
    ("class_mod", "Classmod"),
    ("repair_kit", "Repkit"),
    ("repkit", "Repkit"),
    ("enhancement", "Enhancement"),
    ("grenade_gadget", "Ordnance"),
    ("turret_gadget", "Ordnance"),
    ("heavy_weapon_gadget", "Ordnance"),
    ("terminal_barrier", "Ordnance"),
    ("terminal_gadget", "Ordnance"),
    ("_gadget", "Ordnance"),
    ("energy_shield", "Shield"),
    ("armor_shield", "Shield"),
    ("_shield", "Shield"),
    ("shield", "Shield"),
)

_GZO_CLASS_NAMES = {
    "siren": "Siren",
    "dark_siren": "Siren",
    "forgeknight": "Paladin",
    "paladin": "Paladin",
    "exo_soldier": "Exo Soldier",
    "gravitar": "Gravitar",
    "ai": "AI",
    "c4sh": "C4SH",
}

_GUN_TYPES = frozenset(
    {"Pistol", "Shotgun", "Assault Rifle", "SMG", "Sniper", "Heavy Weapon"}
)

_RARITY_PATTERNS: tuple[tuple[str, str], ...] = (
    ("pearlescent", "Pearlescent"),
    ("pearl", "Pearlescent"),
    ("legendary", "Legendary"),
    ("epic", "Epic"),
    ("uncommon", "Uncommon"),
    ("common", "Common"),
    ("rare", "Rare"),
)

# Composition rarity keys in gzo_parts_map (prefer over free-text keyword guess).
_COMP_RARITY_RE: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?:^|\.)comp_06_pearl(?:escent)?(?:_|$)", re.I), "Pearlescent"),
    (re.compile(r"(?:^|\.)comp_05_legendary(?:_|$)", re.I), "Legendary"),
    (re.compile(r"(?:^|\.)comp_04_epic(?:_|$)", re.I), "Epic"),
    (re.compile(r"(?:^|\.)comp_03_rare(?:_|$)", re.I), "Rare"),
    (re.compile(r"(?:^|\.)comp_02_uncommon(?:_|$)", re.I), "Uncommon"),
    (re.compile(r"(?:^|\.)comp_01_common(?:_|$)", re.I), "Common"),
)

# Unique lore name on legendary / pearl compositions (guns + most gear).
_UNIQUE_COMP_RE = re.compile(
    r"(?:^|\.)comp_0(?:5_legendary|6_pearl(?:escent)?)_(.+)$",
    re.I,
)

# Some shields/grenades use bare comp_05_<name> without the legendary token.
_COMP05_NAMED_RE = re.compile(
    r"(?:^|\.)comp_05_(?!legendary(?:_|$)|pearl(?:escent)?(?:_|$))(.+)$",
    re.I,
)

# Named barrels sometimes carry the unique slug (e.g. part_barrel_01_prism).
_NAMED_BARREL_RE = re.compile(r"(?:^|\.)part_barrel_\d+_(.+)$", re.I)

# Non-gun unique carriers: shields, enhancements, repkits, ordnance.
_NAMED_PART_RES: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?:^|\.)part_unique_(.+)$", re.I),
    re.compile(r"(?:^|\.)part_firmware_(.+)$", re.I),
    re.compile(r"(?:^|\.)part_core_[a-z0-9]+_(.+)$", re.I),
    re.compile(r"(?:^|\.)part_augment_unique_(.+)$", re.I),
    re.compile(r"(?:^|\.)part_body_armor_(.+)$", re.I),
    # Avoid rarity stubs like part_body_05_legendary / part_body_ele_*.
    re.compile(
        r"(?:^|\.)part_body_(?!ele_|armor(?:_|$)|0?\d+[_\-]?(?:common|uncommon|rare|epic|legendary|pearl))"
        r"(.+)$",
        re.I,
    ),
    re.compile(r"(?:^|\.)leg_body_(.+)$", re.I),
)

_DAMAGE_TYPE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(?:^|[_\.])(?:incendiary|fire)(?:[_\.]|$)", re.I), "Fire"),
    (re.compile(r"(?:^|[_\.])(?:shock|electric)(?:[_\.]|$)", re.I), "Shock"),
    (re.compile(r"(?:^|[_\.])cryo(?:[_\.]|$)", re.I), "Cryo"),
    (re.compile(r"(?:^|[_\.])corrosive(?:[_\.]|$)", re.I), "Corrosive"),
    (re.compile(r"(?:^|[_\.])(?:radiation|rad)(?:[_\.]|$)", re.I), "Radiation"),
    (re.compile(r"(?:^|[_\.])kinetic(?:[_\.]|$)", re.I), "Kinetic"),
)

_WEAK_BARREL_SUFFIXES = frozenset(
    {
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "h",
        "base",
        "body",
        "stock",
        "mag",
        "scope",
        "grip",
        "foregrip",
        "armor",
        "energy",
        "common",
        "uncommon",
        "rare",
        "epic",
        "legendary",
        "pearl",
        "pearlescent",
    }
)

# Class-mod legendary comps often end in 01..06; keep named DLC/raid tokens.
_CLASSMOD_NAMED_TOKENS = frozenset(
    {
        "raid1",
        "raid2",
        "cowbell",
        "tuba",
        "dlc1",
        "dlc2",
    }
)


def _title_from_slug(text: str) -> str:
    text = re.sub(r"[_\-]+", " ", str(text or "")).strip()
    return " ".join(
        w.upper() if w.lower() in ("smg", "ai", "cov") else w.capitalize()
        for w in text.split()
    )


def _load_parts_map() -> dict[str, dict[str, str]]:
    global _GZO_PARTS_MAP, _GZO_TYPE_ID_INDEX
    if _GZO_PARTS_MAP is not None:
        return _GZO_PARTS_MAP
    data: dict[str, dict[str, str]] = {}
    blob: bytes | None = None
    try:
        blob = pkgutil.get_data(__package__ or __name__.rpartition(".")[0], "gzo_parts_map.json")
    except Exception:
        blob = None
    if not blob:
        try:
            from pathlib import Path

            path = Path(__file__).with_name("gzo_parts_map.json")
            if path.is_file():
                blob = path.read_bytes()
        except Exception:
            blob = None
    try:
        if blob:
            raw = json.loads(blob.decode("utf-8", "replace"))
            if isinstance(raw, dict):
                for k, v in raw.items():
                    if isinstance(v, dict):
                        data[str(k)] = {str(pk): str(pv) for pk, pv in v.items()}
    except Exception:
        data = {}
    _GZO_PARTS_MAP = data
    idx: dict[int, tuple[str, dict[str, str]]] = {}
    for key, table in data.items():
        m = re.match(r"\s*(\d+)\s*\|\s*(.+?)\s*$", str(key))
        if m:
            idx[int(m.group(1))] = (m.group(2), table)
    _GZO_TYPE_ID_INDEX = idx
    return data


def _type_id_index() -> dict[int, tuple[str, dict[str, str]]]:
    _load_parts_map()
    return _GZO_TYPE_ID_INDEX or {}


def type_info_from_id(type_id: int) -> dict[str, str]:
    label_table = _type_id_index().get(int(type_id))
    if not label_table:
        return {
            "type_id": str(type_id),
            "set": "",
            "manufacturer": "",
            "type": "",
            "character_class": "",
        }
    label = label_table[0]
    raw = label.strip()
    low = raw.lower()
    info = {
        "type_id": str(type_id),
        "set": raw,
        "manufacturer": "",
        "type": "",
        "character_class": "",
    }
    if "classmod" in low or "class_mod" in low:
        info["type"] = "Classmod"
        tail = low.replace("classmod", "").replace("class_mod", "").strip("_")
        info["character_class"] = (
            _GZO_CLASS_NAMES.get(tail, _title_from_slug(tail)) if tail else ""
        )
        return info
    pieces = re.split(r"[_\s]+", raw)
    if pieces:
        prefix = pieces[0].upper()
        if prefix in _GZO_MAKER_PREFIXES:
            info["manufacturer"] = _GZO_MAKER_PREFIXES[prefix]
        # Prefer longest suffix match (grenade_gadget before gadget).
        for i in range(1, len(pieces)):
            suffix = "_".join(pieces[i:]).upper()
            if suffix in _GZO_TYPE_SUFFIXES:
                info["type"] = _GZO_TYPE_SUFFIXES[suffix]
                break
        if not info["type"]:
            alone = pieces[0].upper()
            if alone in _GZO_TYPE_SUFFIXES:
                info["type"] = _GZO_TYPE_SUFFIXES[alone]
    if not info["type"]:
        for key, val in _GZO_TYPE_HINTS:
            if key in low:
                info["type"] = val
                break
    if not info["manufacturer"] and pieces:
        for piece in pieces:
            pref = piece.upper()
            if pref in _GZO_MAKER_PREFIXES:
                info["manufacturer"] = _GZO_MAKER_PREFIXES[pref]
                break
            if pref.startswith("BOR"):
                info["manufacturer"] = "Ripper"
                break
    return info


def category_for_type(item_type: str) -> str:
    t = str(item_type or "").strip()
    if t in _GUN_TYPES:
        return "Guns"
    if t == "Shield":
        return "Shields"
    if t in ("Ordnance", "Gadget"):
        return "Ordnance"
    if t == "Repkit":
        return "Repkits"
    if t == "Enhancement":
        return "Enhancements"
    if t == "Classmod":
        return "Class Mods"
    return "Other"


def _leaf_part_name(part_name: str) -> str:
    text = str(part_name or "").strip()
    if "." in text:
        return text.rsplit(".", 1)[-1].strip()
    return text


def _humanize_unique_token(token: str) -> str:
    """SilverSliver / soul_survivor / PRISM → display-friendly label."""
    raw = str(token or "").strip()
    if not raw:
        return ""
    # Split CamelCase / acronyms: SilverSliver, NoisyCricket, ATLien, PRISM.
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", raw)
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)
    spaced = spaced.replace("_", " ").replace("-", " ")
    words: list[str] = []
    for word in spaced.split():
        if not word:
            continue
        if word.isupper() and 2 <= len(word) <= 8:
            words.append(word)
        elif word.isupper():
            words.append(word.capitalize())
        elif any(ch.isupper() for ch in word[1:]):
            words.append(word)
        else:
            words.append(word.capitalize())
    return " ".join(words).strip()


def _is_weak_unique_token(token: str) -> bool:
    t = str(token or "").strip().lower()
    if not t or len(t) <= 1:
        return True
    if re.fullmatch(r"\d+", t):
        return True
    # Class-mod numbered slots (01..06) lack inv_name_part in GZO alone.
    if re.fullmatch(r"0?\d{1,2}", t):
        return True
    if re.fullmatch(
        r"(?:0?\d+[_\-]?)?(?:common|uncommon|rare|epic|legendary|pearl|pearlescent)",
        t,
    ):
        return True
    if t in _WEAK_BARREL_SUFFIXES:
        return True
    if t.startswith("ele_"):
        return True
    return False


def _token_from_named_patterns(leaf: str) -> str:
    for pattern in (
        _UNIQUE_COMP_RE,
        _COMP05_NAMED_RE,
        _NAMED_BARREL_RE,
        *_NAMED_PART_RES,
    ):
        m = pattern.search(leaf)
        if not m:
            continue
        token = str(m.group(1) or "").strip()
        if not token:
            continue
        low = token.lower()
        # Allow known class-mod DLC/raid lore tokens that look "weak" otherwise.
        if low in _CLASSMOD_NAMED_TOKENS:
            return token
        if _is_weak_unique_token(token):
            continue
        if token.lower().startswith("ele_"):
            continue
        return token
    return ""


def _unique_display_from_part_names(names: list[str]) -> str:
    """Prefer legendary/pearl comps, then other unique carriers across all item types."""
    # Pass 1: legendary / pearl composition suffixes (highest signal).
    for name in names:
        leaf = _leaf_part_name(name)
        m = _UNIQUE_COMP_RE.search(leaf)
        if m:
            token = str(m.group(1) or "").strip()
            low = token.lower()
            if low in _CLASSMOD_NAMED_TOKENS or (
                token and not _is_weak_unique_token(token)
            ):
                return _humanize_unique_token(token)
    # Pass 2: bare comp_05_<name>, barrels, firmware/body/unique/core/augment.
    for name in names:
        leaf = _leaf_part_name(name)
        if _UNIQUE_COMP_RE.search(leaf):
            continue
        token = _token_from_named_patterns(leaf)
        if token:
            return _humanize_unique_token(token)
    return ""


def _guess_rarity_from_part_names(names: list[str]) -> str:
    for name in names:
        leaf = _leaf_part_name(name)
        for pattern, label in _COMP_RARITY_RE:
            if pattern.search(leaf):
                return label
        # Named bare comp_05_* (Momento / Supernova style) → Legendary.
        if _COMP05_NAMED_RE.search(leaf):
            return "Legendary"
        if re.search(r"(?:^|\.)part_unique_", leaf, re.I):
            return "Legendary"
    hay = " ".join(names).lower()
    if not hay:
        return ""
    for needle, label in _RARITY_PATTERNS:
        if needle in hay:
            return label
    return ""


def _guess_damage_type_from_part_names(names: list[str]) -> str:
    """Best-effort elemental tag from part names (not a full game decode)."""
    for name in names:
        leaf = _leaf_part_name(name)
        for pattern, label in _DAMAGE_TYPE_PATTERNS:
            if pattern.search(leaf):
                return label
    return ""


def _part_names_from_human(human: str, *, limit: int = 64) -> list[str]:
    idx = _type_id_index()
    names: list[str] = []
    refs = re.findall(r"\{\s*(\d+)(?:\s*:\s*(\d+))?\s*\}", human)
    m = re.match(r"\s*(\d+)\s*,", human)
    default_set = int(m.group(1)) if m else 0
    for raw_set, raw_part in refs[: max(1, int(limit))]:
        part_set = int(raw_set) if raw_part else default_set
        part_id = int(raw_part or raw_set)
        label_table = idx.get(part_set)
        if not label_table:
            continue
        part_name = label_table[1].get(str(part_id), "")
        if part_name:
            names.append(str(part_name))
    return names


def _fallback_display_name(
    manufacturer: str,
    item_type: str,
    character_class: str,
    set_label: str,
) -> str:
    if item_type == "Classmod":
        pieces = [p for p in (character_class, "Class Mod") if p]
        display = " ".join(pieces).strip()
        if display:
            return display
    pieces = [p for p in (manufacturer, item_type or character_class) if p]
    display = " ".join(pieces).strip()
    if display:
        return display
    return str(set_label or "").replace("_", " ").strip()


def meta_from_serial(serial: str) -> dict[str, Any]:
    """Decode manufacturer / type / category / rarity / lore name from an @U serial."""
    out: dict[str, Any] = {
        "type_id": "",
        "set": "",
        "manufacturer": "",
        "item_type": "",
        "type": "",
        "character_class": "",
        "category": "Other",
        "rarity": "",
        "damage_type": "",
        "display_name": "",
        "unique_name": "",
        "part_names": [],
        "dps": None,
        "value": None,
        "meta_ok": False,
    }
    text = str(serial or "").strip()
    if not text.startswith("@U"):
        return out
    try:
        from . import serial_converter

        human = serial_converter.serial_to_human(text)
    except Exception:
        return out
    m = re.match(r"\s*(\d+)\s*,", human)
    if not m:
        return out
    type_id = int(m.group(1))
    info = type_info_from_id(type_id)
    item_type = str(info.get("type") or "")
    manufacturer = str(info.get("manufacturer") or "")
    character_class = str(info.get("character_class") or "")
    category = category_for_type(item_type)
    part_names: list[str] = []
    rarity = ""
    unique_name = ""
    damage_type = ""
    try:
        part_names = _part_names_from_human(human, limit=64)
        rarity = _guess_rarity_from_part_names(part_names)
        unique_name = _unique_display_from_part_names(part_names)
        damage_type = _guess_damage_type_from_part_names(part_names)
    except Exception:
        part_names = []
        rarity = ""
        unique_name = ""
        damage_type = ""
    # Enhancements: bare firmware without rarity comps still deserves a rarity tag.
    if not rarity and any(
        re.search(r"(?:^|\.)part_firmware_", _leaf_part_name(n), re.I) for n in part_names
    ):
        rarity = "Legendary"
    fallback = _fallback_display_name(
        manufacturer, item_type, character_class, str(info.get("set") or "")
    )
    display = unique_name or fallback
    out.update(
        {
            "type_id": str(type_id),
            "set": str(info.get("set") or ""),
            "manufacturer": manufacturer,
            "item_type": item_type,
            "type": item_type,
            "character_class": character_class,
            "category": category,
            "rarity": rarity,
            "damage_type": damage_type,
            "display_name": display,
            "unique_name": unique_name,
            "part_names": part_names[:24],
            "dps": None,
            "value": None,
            "meta_ok": True,
        }
    )
    return out


def enrich_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Mutate/return an inventory entry with decoded meta fields."""
    if not isinstance(entry, dict):
        return entry
    serial = str(entry.get("serial") or "")
    meta = meta_from_serial(serial)
    entry["type_id"] = meta.get("type_id") or entry.get("type_id") or ""
    entry["set"] = meta.get("set") or ""
    entry["manufacturer"] = meta.get("manufacturer") or ""
    entry["item_type"] = meta.get("item_type") or ""
    entry["type"] = meta.get("type") or entry.get("item_type") or ""
    entry["character_class"] = meta.get("character_class") or ""
    entry["category"] = meta.get("category") or "Other"
    entry["rarity"] = meta.get("rarity") or ""
    entry["damage_type"] = meta.get("damage_type") or ""
    # DPS / vendor value are not encoded in @U / GZO parts — keep explicit nulls.
    entry["dps"] = meta.get("dps")
    entry["value"] = meta.get("value")
    unique = str(meta.get("unique_name") or "").strip()
    if unique:
        entry["unique_name"] = unique
    display = str(meta.get("display_name") or "").strip()
    if display:
        entry["display_name"] = display
    else:
        entry["display_name"] = str(entry.get("label") or "Item")
    level = int(entry.get("level") or -1)
    base = entry["display_name"]
    # When we only have manufacturer+type, keep level in the summary line.
    if level >= 0:
        entry["summary"] = f"{base} L{level}"
    else:
        entry["summary"] = base
    entry["meta_ok"] = bool(meta.get("meta_ok"))
    return entry
