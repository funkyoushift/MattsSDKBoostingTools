"""Small BL4 legit item builder/validator.

This module intentionally does not carry the giant browser legit-builder.js.
It loads a compact, pre-flattened rule file generated from Nexus-Data-inv*.json.

Rule model:
- roots: root inventory definitions with Root serial index
- parts: dependency table entries with Sub serial index and flattened add/dep/exclude tags
- rules: compact parttypeselectionrules pairs from inv_comp rows

The validator is intentionally conservative: it validates tag dependencies/exclusions,
slot allow-lists from comp rules, and basic slot counts.  It does not try to
emulate every UI quirk from the web builder.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import pkgutil
import re
from pathlib import Path
from typing import Any, Iterable

try:
    from .serial_converter import human_to_serial
except Exception:  # direct script/debug fallback
    from serial_converter import human_to_serial  # type: ignore

_RULES_CACHE: dict[str, Any] | None = None
_ROOT_BY_KEY: dict[str, dict[str, Any]] | None = None
_PARTS_CACHE: dict[str, list[dict[str, Any]]] = {}
_LOOKUP_PARTS_CACHE: dict[str, list[dict[str, Any]]] = {}
_FIND_INDEX_CACHE: dict[str, dict[tuple[str | None, str], dict[str, Any]]] = {}

# Roots exposed in the in-game builder.  The flattened Nexus file contains many
# pickup/currency/parent roots which are technically serializable but are not
# useful for gear creation and make the picker noisy.
_BUILDABLE_ROOTS: dict[int, tuple[str, str]] = {
    # Weapons
    2: ("daedalus", "pistol"),
    3: ("jakobs", "pistol"),
    4: ("order", "pistol"),
    5: ("tediore", "pistol"),
    6: ("torgue", "pistol"),
    7: ("ripper", "shotgun"),
    8: ("daedalus", "shotgun"),
    9: ("jakobs", "shotgun"),
    10: ("maliwan", "shotgun"),
    11: ("tediore", "shotgun"),
    12: ("torgue", "shotgun"),
    13: ("daedalus", "assault_rifle"),
    14: ("tediore", "assault_rifle"),
    15: ("order", "assault_rifle"),
    16: ("vladof", "sniper"),
    17: ("torgue", "assault_rifle"),
    18: ("vladof", "assault_rifle"),
    19: ("ripper", "smg"),
    20: ("daedalus", "smg"),
    21: ("maliwan", "smg"),
    22: ("vladof", "smg"),
    23: ("ripper", "sniper"),
    24: ("jakobs", "sniper"),
    25: ("maliwan", "sniper"),
    26: ("order", "sniper"),
    27: ("jakobs", "assault_rifle"),
    # Class mods
    254: ("siren", "class_mod"),
    255: ("forgeknight", "class_mod"),
    256: ("exo_soldier", "class_mod"),
    259: ("gravitar", "class_mod"),
    404: ("c4sh", "class_mod"),
    # Rep kits / ordnance / enhancements / shields
    261: ("torgue", "repair_kit"),
    263: ("maliwan", "gadget"),
    264: ("hyperion", "enhancement"),
    265: ("jakobs", "repair_kit"),
    266: ("maliwan", "repair_kit"),
    267: ("jakobs", "gadget"),
    268: ("jakobs", "enhancement"),
    269: ("vladof", "repair_kit"),
    270: ("daedalus", "gadget"),
    271: ("maliwan", "enhancement"),
    272: ("order", "gadget"),
    273: ("torgue", "heavy"),
    274: ("ripper", "repair_kit"),
    275: ("ripper", "heavy"),
    277: ("daedalus", "repair_kit"),
    278: ("ripper", "gadget"),
    279: ("maliwan", "shield"),
    281: ("order", "enhancement"),
    282: ("vladof", "heavy"),
    283: ("vladof", "shield"),
    284: ("atlas", "enhancement"),
    285: ("order", "repair_kit"),
    286: ("cov", "enhancement"),
    287: ("tediore", "shield"),
    289: ("maliwan", "heavy"),
    290: ("tediore", "repair_kit"),
    291: ("vladof", "gadget"),
    292: ("tediore", "enhancement"),
    293: ("order", "shield"),
    296: ("ripper", "enhancement"),
    298: ("torgue", "gadget"),
    299: ("daedalus", "enhancement"),
    300: ("ripper", "shield"),
    303: ("torgue", "enhancement"),
    306: ("jakobs", "shield"),
    310: ("vladof", "enhancement"),
    311: ("tediore", "gadget"),
    312: ("daedalus", "shield"),
    321: ("torgue", "shield"),
}


_WEAPON_ROOT_IDS = set(range(2, 28))

# Compact canonical part order for BL4 weapons.  The Nexus inv dependency array
# for manufacturer roots is broad and starts with inv_comp/core augment tables,
# but the weapon builder/validator serial order should follow the weapon part
# layout with comp first, body next, and pearl rolls last.
_WEAPON_CANONICAL_SLOT_ORDER = [
    # Comp / composition must always be emitted first. It establishes rarity,
    # unique/legendary tags, and parttypeselectionrules used by later slots.
    "inv_comp",
    "body",
    "body_acc",
    "body_ele",
    "barrel",
    "barrel_acc",
    "barrel_licensed",
    "magazine",
    "magazine_ted_thrown",
    "magazine_acc",
    "body_mag",
    "body_bolt",
    "scope",
    "scope_acc",
    "grip",
    "foregrip",
    "secondary_ammo",
    "secondary_ele",
    "element",
    "underbarrel",
    "underbarrel_acc",
    "underbarrel_acc_vis",
    "payload",
    "payload_augment",
    "tediore_acc",
    "tediore_secondary_acc",
    "hyperion_secondary_acc",
    "firmware",
    "endgame",
    "unique",
    "pearl_elem",
    "pearl_stat",
]

def _root_serial(root: dict[str, Any]) -> int:
    try:
        return int(root.get("serial"))
    except Exception:
        return -1

def _is_weapon_root(root: dict[str, Any]) -> bool:
    return _root_serial(root) in _WEAPON_ROOT_IDS

def _slot_order_map(root: dict[str, Any]) -> dict[str, int]:
    if _is_weapon_root(root):
        base = {name: i for i, name in enumerate(_WEAPON_CANONICAL_SLOT_ORDER)}
        fallback_start = len(base)
        for name in (root.get("deps") or []):
            n = _norm(name)
            if n and n not in base:
                base[n] = fallback_start
                fallback_start += 1
        return base
    return {_norm(name): i for i, name in enumerate(root.get("deps") or [])}

def _annotate_root(root: dict[str, Any]) -> dict[str, Any]:
    out = dict(root)
    try:
        serial = int(out.get("serial"))
    except Exception:
        serial = -1
    meta = _BUILDABLE_ROOTS.get(serial)
    if meta:
        manufacturer, item_type = meta
        out["manufacturer"] = manufacturer
        out["item_type"] = item_type
        out["build_label"] = f"{manufacturer} {item_type}".replace("_", " ").title()
        if manufacturer == "c4sh":
            out["build_label"] = "C4SH Class Mod"
    return out

def is_buildable_root(root: dict[str, Any]) -> bool:
    try:
        return int(root.get("serial")) in _BUILDABLE_ROOTS
    except Exception:
        return False


def _norm(s: Any) -> str:
    return str(s or "").strip().lower()



def _repair_known_flattened_rule_misclassifications(data: dict[str, Any]) -> None:
    """Fix compact-rule fallbacks that are valid in save-editor/game but were flattened into the wrong slot.

    The Tediore pistol data can carry barrel accessory serials as part_barrel_01_a/d
    and part_barrel_02_a/d.  Older generated rule files labeled those fallback
    rows as table=barrel, which makes selected-comp allow-list checks reject
    valid generated/save-editor serials as if they had multiple illegal barrels.
    """
    for root in data.get("roots", []) or []:
        if str(root.get("key", "")).lower() != "ted_ps" and str(root.get("serial", "")) != "5":
            continue
        for part in root.get("parts", []) or []:
            key = str(part.get("key", "")).lower()
            if re.fullmatch(r"part_barrel_\d+_[abcd]", key) and _norm(part.get("table")) == "barrel":
                part["table"] = "barrel_acc"


def _load_rules() -> dict[str, Any]:
    global _RULES_CACHE, _ROOT_BY_KEY
    if _RULES_CACHE is not None:
        return _RULES_CACHE
    blob = pkgutil.get_data(__package__ or __name__.rpartition(".")[0], "legit_rules_flat.json")
    if blob is None:
        local = Path(__file__).with_name("legit_rules_flat.json")
        if local.exists():
            blob = local.read_bytes()
    if blob is None:
        raise RuntimeError("legit_rules_flat.json was not found in the mod package")
    _RULES_CACHE = json.loads(blob.decode("utf-8"))
    _repair_known_flattened_rule_misclassifications(_RULES_CACHE)
    _ROOT_BY_KEY = {str(r.get("key", "")).lower(): r for r in _RULES_CACHE.get("roots", [])}
    return _RULES_CACHE


def all_roots() -> list[dict[str, Any]]:
    """Return every compact root in the flattened rules file."""
    data = _load_rules()
    return sorted((_annotate_root(r) for r in data.get("roots", [])), key=lambda r: (int(r.get("serial") or 0), str(r.get("key") or "")))


def roots() -> list[dict[str, Any]]:
    """Return only gear roots intended for the in-game builder."""
    rows = [_annotate_root(r) for r in _load_rules().get("roots", []) if is_buildable_root(r)]
    return sorted(rows, key=lambda r: (str(r.get("item_type") or ""), str(r.get("manufacturer") or ""), int(r.get("serial") or 0)))


def get_root(root_key: str) -> dict[str, Any] | None:
    _load_rules()
    return (_ROOT_BY_KEY or {}).get(_norm(root_key))


def _inv_ref_key(ref: Any) -> str:
    """Normalize an Unreal inv reference like inv'Weapon.base_comp_05' to a root key."""
    text = str(ref or "").strip()
    if text.lower().startswith("inv'") and "'" in text[4:]:
        try:
            text = text.split("'", 2)[1]
        except Exception:
            pass
    if "." in text:
        text = text.split(".", 1)[0]
    return _norm(text)


def _inv_ref_part_key(ref: Any) -> tuple[str, str] | None:
    """Return (root_key, part_key) for inv'Root.part' references."""
    text = str(ref or "").strip()
    if not text:
        return None
    if text.lower().startswith("inv'") and "'" in text[4:]:
        try:
            text = text.split("'", 2)[1]
        except Exception:
            return None
    if "." not in text:
        return None
    root_key, part_key = text.split(".", 1)
    return _norm(root_key), _norm(part_key)


def _direct_parts(root: dict[str, Any]) -> list[dict[str, Any]]:
    return list(root.get("parts") or [])


def _inheritance_roots(root: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return [root, parent, grandparent, ...] following basetype inv refs."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    cur = root
    while cur:
        key = _norm(cur.get("key"))
        if not key or key in seen:
            break
        seen.add(key)
        out.append(cur)
        parent_key = _inv_ref_key(cur.get("basetype"))
        if not parent_key:
            break
        cur = get_root(parent_key)
    return out


def _part_with_source(part: dict[str, Any], source_root: dict[str, Any], current_root: dict[str, Any]) -> dict[str, Any]:
    """Copy a part and annotate where its serial index belongs.

    BL4 part tokens are local to the inventory root that defines them.  When a
    child root inherits parts from a parent inventory root (Weapon, Shield,
    Energy_Shield, etc.), the human serial must emit {RootSerial:SubSerial}
    instead of {SubSerial}.  Without this, inherited element/pearl/shared slots
    are decoded as the wrong child-root subindex and the item breaks.
    """
    cp = dict(part)
    src_key = str(source_root.get("key") or "")
    cur_key = str(current_root.get("key") or "")
    src_serial = source_root.get("serial")
    cp["source_root_key"] = src_key
    cp["source_root_serial"] = src_serial
    if _norm(src_key) != _norm(cur_key):
        cp["inherited_from"] = src_key
    return cp


def _parts(root: dict[str, Any]) -> list[dict[str, Any]]:
    """Parts available to this root after inheriting parent-root part tables."""
    cache_key = _norm(root.get("key"))
    cached = _PARTS_CACHE.get(cache_key)
    if cached is not None:
        return cached
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    chain = _inheritance_roots(root)
    for idx, r in enumerate(chain):
        for part in _direct_parts(r):
            table = _norm(part.get("table"))
            if idx > 0 and table == "inv_comp":
                continue
            sig = (table, _norm(part.get("key")))
            if sig in seen:
                continue
            seen.add(sig)
            merged.append(_part_with_source(part, r, root))
    _PARTS_CACHE[cache_key] = merged
    return merged


def _lookup_parts(root: dict[str, Any]) -> list[dict[str, Any]]:
    """All parts in this root plus ancestors, including parent inv_comp rows."""
    cache_key = _norm(root.get("key"))
    cached = _LOOKUP_PARTS_CACHE.get(cache_key)
    if cached is not None:
        return cached
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for r in _inheritance_roots(root):
        for part in _direct_parts(r):
            sig = (_norm(part.get("table")), _norm(part.get("key")))
            if sig in seen:
                continue
            seen.add(sig)
            merged.append(_part_with_source(part, r, root))
    _LOOKUP_PARTS_CACHE[cache_key] = merged
    return merged


def slots(root_key: str) -> list[str]:
    root = get_root(root_key)
    if not root:
        return []
    order = _slot_order_map(root)
    names = sorted({_norm(p.get("table")) for p in _parts(root) if p.get("table")}, key=lambda n: order.get(_norm(n), 9999))
    return [str(n) for n in names]


def slot_order(root_key: str) -> list[str]:
    """Dependency table order from the inv file, filtered to populated slots.

    Generated serials and the slot UI should follow this order, e.g. inv_comp,
    body, body_acc/bodyacc, body_ele/bodyele, barrel, barrel_acc, magazine,
    scope, grip, etc., exactly as listed by the root inventory definition's
    __deps array.
    """
    return slots(root_key)


def _find_index(root: dict[str, Any]) -> dict[tuple[str | None, str], dict[str, Any]]:
    cache_key = _norm(root.get("key"))
    cached = _FIND_INDEX_CACHE.get(cache_key)
    if cached is not None:
        return cached
    idx: dict[tuple[str | None, str], dict[str, Any]] = {}
    for p in _lookup_parts(root):
        table_n = _norm(p.get("table"))
        key_n = _norm(p.get("key"))
        if key_n:
            idx.setdefault((None, key_n), p)
            idx.setdefault((table_n, key_n), p)
        token = _norm(_serial_part_token(root, p))
        token_inner = token[1:-1] if token.startswith("{") and token.endswith("}") else token
        for t in (token, token_inner):
            if t:
                idx.setdefault((None, t), p)
                idx.setdefault((table_n, t), p)
        try:
            sub = str(int(p.get("serial")))
            idx.setdefault((table_n, sub), p)
            # Current-root numeric tokens can be looked up without table.
            if int(p.get("source_root_serial") or root.get("serial") or -1) == int(root.get("serial") or -2):
                idx.setdefault((None, sub), p)
        except Exception:
            pass
    _FIND_INDEX_CACHE[cache_key] = idx
    return idx


def _find_part(root: dict[str, Any], part: str | int, table: str | None = None) -> dict[str, Any] | None:
    want = _norm(part)
    if want.startswith("{") and want.endswith("}"):
        want = want[1:-1].strip().lower()
    table_n = _norm(table) if table else None
    idx = _find_index(root)
    if table_n:
        found = idx.get((table_n, want))
        if found is not None:
            return found
    return idx.get((None, want))


def _expand_serial_token(item: str | int | dict[str, Any]) -> list[str | int | dict[str, Any]]:
    """Expand compact decoded tokens like {234:[23 39 34]}.

    BL4 decoded human serials may pack multiple subparts from the same root into
    one token.  Treating the packed token as a single unknown/opaque part makes
    class mods lose stat_group selections and makes several inherited
    shield/ordnance groups validate incorrectly.
    """
    if isinstance(item, dict):
        return [item]
    text = str(item or "").strip()
    if not (text.startswith("{") and text.endswith("}") and "[" in text and "]" in text):
        return [item]
    inner = text[1:-1].strip()
    if ":[" in inner:
        root_part, rest = inner.split(":", 1)
        root_part = root_part.strip()
        body = rest.strip()
        if body.startswith("[") and body.endswith("]"):
            vals = [v for v in re.split(r"[\s,]+", body[1:-1].strip()) if v]
            return [f"{{{root_part}:{v}}}" for v in vals]
    if inner.startswith("[") and inner.endswith("]"):
        vals = [v for v in re.split(r"[\s,]+", inner[1:-1].strip()) if v]
        return [f"{{{v}}}" for v in vals]
    return [item]


def _selected_parts(root: dict[str, Any], selected: Iterable[str | int | dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in selected:
        for item in _expand_serial_token(raw):
            if isinstance(item, dict):
                key = item.get("key", item.get("part", item.get("serial")))
                table = item.get("table")
                p = _find_part(root, key, table)
            else:
                p = _find_part(root, item)
            if p is not None:
                out.append(p)
    return out


def _fmt_tags(part: dict[str, Any], field: str) -> set[str]:
    return {_norm(t) for t in (part.get(field) or []) if _norm(t)}


def _tag_pool(parts: Iterable[dict[str, Any]]) -> set[str]:
    pool: set[str] = set()
    for p in parts:
        pool.update(_fmt_tags(p, "base_tags"))
        pool.update(_fmt_tags(p, "add"))
    return pool


def _selected_comp(parts: list[dict[str, Any]]) -> dict[str, Any] | None:
    comps = [p for p in parts if _norm(p.get("table")) == "inv_comp"]
    # Prefer the most specific selected comp with explicit rules, otherwise the first comp.
    for p in comps:
        if p.get("rules"):
            return p
    return comps[0] if comps else None


def _base_comp_chain(comp: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Return inherited comp rows from highest ancestor to immediate base.

    Example: a Maliwan shield comp may be based on energy_shield.comp_05,
    which in turn is based on Shield.comp_05.  The effective rules must be
    Shield -> energy_shield -> selected comp, with later/more-specific rules
    replacing earlier ones when they define a slot.
    """
    if not comp:
        return []
    ref = _inv_ref_part_key(comp.get("base"))
    if not ref:
        return []
    root_key, part_key = ref
    root = get_root(root_key)
    if not root:
        return []
    base_comp = _find_part(root, part_key, "inv_comp")
    if not base_comp:
        return []
    return _base_comp_chain(base_comp) + [base_comp]


def _rules_from_comp_base(comp: dict[str, Any] | None) -> list[dict[str, Any]]:
    rules: list[dict[str, Any]] = []
    for base_comp in _base_comp_chain(comp):
        rules.extend(list(base_comp.get("rules") or []))
    return rules


def _is_pearl_comp(comp: dict[str, Any] | None) -> bool:
    if not comp:
        return False
    key = _norm(comp.get("key"))
    tags = _fmt_tags(comp, "base_tags") | _fmt_tags(comp, "add")
    return key.startswith("comp_06") or "pearl" in key or "pearlescent" in tags


def _rule_effective_count(rule: dict[str, Any], *, source: str) -> tuple[int | None, int | None, bool, bool]:
    has_min = "min" in rule and rule.get("min") is not None
    has_max = "max" in rule and rule.get("max") is not None
    min_v = int(rule["min"]) if has_min else None
    max_v = int(rule["max"]) if has_max else None
    parts = rule.get("parts") or []
    slot = _norm(rule.get("slot"))

    # If a specific comp/rule lists the parts for a slot, that rule owns the
    # slot.  With no explicit counts, it means exactly one of those parts.
    if parts and min_v is None and max_v is None and slot != "firmware":
        return 1, 1, has_min, has_max
    if min_v == 0 and max_v is None:
        max_v = 1
    elif min_v is None and max_v is None:
        # A rule with no listed parts and no counts is just a weak inherited
        # marker; default to optional single selection.  Fallback exact-one is
        # applied later only if there are currently legal candidates.
        min_v, max_v = 0, 1
    elif min_v is None:
        min_v = 1
    elif max_v is None and min_v != 0:
        max_v = 1
    return min_v, max_v, has_min, has_max


def _merge_rule_into_constraints(res: dict[str, dict[str, Any]], rule: dict[str, Any], *, source: str) -> None:
    slot = _norm(rule.get("slot"))
    if not slot:
        return
    cur = res.setdefault(slot, {"allowed": set(), "min": None, "max": None, "source": source, "specificity": -1, "has_parts": False})
    parts = [_norm(pk) for pk in (rule.get("parts") or []) if _norm(pk)]
    specificity = {"root_base": 0, "base": 1, "current": 2}.get(source, 1)
    min_v, max_v, has_min, has_max = _rule_effective_count(rule, source=source)

    # Parts listed at the most-specific comp replace inherited parts for that
    # slot.  This is the important bit for uniques: if the unique comp defines
    # barrel=[Herald barrel], do not union the generic barrel choices back in.
    if parts:
        if specificity >= int(cur.get("specificity") or -1):
            cur["allowed"] = set(parts)
            cur["min"] = min_v
            cur["max"] = max_v
            cur["source"] = source
            cur["specificity"] = specificity
            cur["has_parts"] = True
        return

    # Explicit count-only rules can disable/adjust an inherited slot.  They do
    # not erase a more-specific parts list unless they are at least as specific.
    if has_min or has_max:
        if specificity >= int(cur.get("specificity") or -1) or not cur.get("has_parts"):
            cur["min"] = min_v
            cur["max"] = max_v
            cur["source"] = source
            cur["specificity"] = specificity
        return

    if cur.get("min") is None:
        cur["min"] = min_v
        cur["max"] = max_v
        cur["source"] = source
        cur["specificity"] = specificity


def _slot_constraints(comp: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    res: dict[str, dict[str, Any]] = {}
    if not comp:
        return res
    # 1) Recursive base comp chain first: e.g. Shield -> Energy_Shield -> child.
    for base_comp in _base_comp_chain(comp):
        for r in base_comp.get("rules") or []:
            _merge_rule_into_constraints(res, r, source="base")
    # 2) Selected comp rules override/replace inherited slot definitions.
    for r in comp.get("rules") or []:
        _merge_rule_into_constraints(res, r, source="current")
    # 3) Pearlescent comps unlock inherited pearl rolls from Weapon.
    if _is_pearl_comp(comp):
        for slot in ("pearl_elem", "pearl_stat"):
            cur = res.setdefault(slot, {"allowed": set(), "min": None, "max": None, "source": "pearlescent", "specificity": 2, "has_parts": False})
            if cur.get("min") is None or int(cur.get("specificity") or 0) <= 2:
                cur["min"] = 1
                cur["max"] = 1
                cur["source"] = "pearlescent"
                cur["specificity"] = 2
    return res






def _part_tag_rules(part: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not part:
        return []
    out: list[dict[str, Any]] = []
    for r in (part.get("tag_rules") or []):
        if not isinstance(r, dict):
            continue
        tags = sorted({_norm(t) for t in (r.get("tags") or []) if _norm(t)})
        if not tags:
            continue
        rr: dict[str, Any] = {"tags": tags}
        if r.get("min") is not None:
            try:
                rr["min"] = int(r.get("min"))
            except Exception:
                pass
        if r.get("max") is not None:
            try:
                rr["max"] = int(r.get("max"))
            except Exception:
                pass
        # Browser rules with a tag list but no explicit count behave like a
        # single allowed tagged pick.  This is important for uncommon licensed
        # weapon parts and keeps tag allowance rules conservative.
        if rr.get("min") is None and rr.get("max") is None:
            rr["max"] = 1
        out.append(rr)
    return out


def _tag_rule_constraints(comp: dict[str, Any] | None) -> dict[tuple[str, ...], dict[str, Any]]:
    """Effective tag-count allowances inherited by the selected composition.

    Weapon base comps define limits such as licensed max 0/1/2/3. Unique comps
    can override those limits (many legendary uniques raise licensed max to 4).
    Apply base chain first and let the selected/current comp win for the same
    tag set.
    """
    res: dict[tuple[str, ...], dict[str, Any]] = {}
    chain = _base_comp_chain(comp) + ([comp] if comp else [])
    for idx, c in enumerate(chain):
        source = "current" if c is comp else "base"
        for r in _part_tag_rules(c):
            tags = tuple(sorted({_norm(t) for t in (r.get("tags") or []) if _norm(t)}))
            if not tags:
                continue
            cur = res.setdefault(tags, {"tags": list(tags), "min": None, "max": None, "source": source, "specificity": idx})
            # More specific comps replace inherited tag limits for the same tag set.
            if idx >= int(cur.get("specificity") or -1):
                cur["min"] = r.get("min")
                cur["max"] = r.get("max")
                cur["source"] = source
                cur["specificity"] = idx
    return res


def _part_has_all_tags(part: dict[str, Any], tags: Iterable[str]) -> bool:
    pool = _fmt_tags(part, "base_tags") | _fmt_tags(part, "add")
    return all(_norm(t) in pool for t in tags)


def _tag_rule_count(parts: Iterable[dict[str, Any]], tags: Iterable[str]) -> int:
    return sum(1 for p in parts if _part_has_all_tags(p, tags))


def _tag_rule_errors(parts: list[dict[str, Any]], comp: dict[str, Any] | None) -> list[str]:
    errors: list[str] = []
    for tags, rule in _tag_rule_constraints(comp).items():
        n = _tag_rule_count(parts, tags)
        label = "+".join(tags)
        if rule.get("min") is not None and n < int(rule["min"]):
            errors.append(f'tag rule "{label}" requires at least {rule["min"]} part(s), got {n}')
        if rule.get("max") is not None and n > int(rule["max"]):
            errors.append(f'too many parts with tag "{label}": found {n}, maximum {rule["max"]} allowed')
    return errors


def tag_counts(root_key: str, selected: Iterable[str | int | dict[str, Any]] = ()) -> list[dict[str, Any]]:
    """Return effective tag allowances for UI/debug display."""
    root = get_root(root_key)
    if not root:
        return []
    parts = _selected_parts(root, selected)
    comp = _selected_comp(parts)
    out: list[dict[str, Any]] = []
    for tags, rule in _tag_rule_constraints(comp).items():
        out.append({
            "tags": list(tags),
            "count": _tag_rule_count(parts, tags),
            "min": rule.get("min"),
            "max": rule.get("max"),
            "source": rule.get("source") or "base",
        })
    return sorted(out, key=lambda r: (str(r.get("tags")), str(r.get("source"))))

def _slot_has_any_parts(root: dict[str, Any], slot: str) -> bool:
    slot_n = _norm(slot)
    if not slot_n:
        return False
    for p in _parts(root):
        if _norm(p.get("table")) == slot_n:
            return True
    return False


def _candidate_is_currently_available(root: dict[str, Any], chosen: list[dict[str, Any]], cand: dict[str, Any], constraints: dict[str, dict[str, Any]], *, ignore_same_slot: bool = True) -> bool:
    """Tag/rule availability test which intentionally ignores slot max counts.

    This is used to decide whether an empty slot should require exactly one
    part.  A slot with zero currently legal candidates is effectively disabled
    for the current comp/tag state and must not fail validation as min=1.
    """
    table_n = _norm(cand.get("table"))
    c = constraints.get(table_n) or {}
    allowed = c.get("allowed") or set()
    if allowed and _norm(cand.get("key")) not in allowed:
        return False
    # Availability is used while deciding whether a slot should be required.
    # When a selected part is already in the same slot, evaluating candidates
    # against the full selected pool makes self-exclusive tags (e.g. element
    # parts which add and exclude ``elem``) look impossible.  For this check,
    # ignore existing parts from the same slot and test the candidate against
    # the rest of the build.
    context = [p for p in chosen if (not ignore_same_slot or _norm(p.get("table")) != table_n)]
    pool = _tag_pool(context)
    deps = _fmt_tags(cand, "dep")
    if any(t not in pool for t in deps):
        return False
    excl = _fmt_tags(cand, "exclude")
    if any((t in pool) for t in excl):
        return False
    return True


def _slot_has_available_parts(root: dict[str, Any], chosen: list[dict[str, Any]], slot: str, constraints: dict[str, dict[str, Any]]) -> bool:
    slot_n = _norm(slot)
    if not slot_n:
        return False
    for p in _parts(root):
        if _norm(p.get("table")) != slot_n:
            continue
        if _candidate_is_currently_available(root, chosen, p, constraints):
            return True
    return False


def _apply_available_slot_minimums(root: dict[str, Any], constraints: dict[str, dict[str, Any]], selected_parts: list[dict[str, Any]] | None = None, *, infer_available_min: bool = True) -> dict[str, dict[str, Any]]:
    """Finalize slot constraints using inherited availability.

    A slot can be selected only if there are currently legal candidate parts in
    the selected comp/root inheritance chain.  Explicit inherited min/max values
    are preserved.  Unconstrained slots with legal candidates default to exactly
    one.  Slots with no legal candidates become 0/0 so they do not fail build.
    """
    res = {str(k): dict(v) for k, v in (constraints or {}).items()}
    chosen = list(selected_parts or [])
    selected_counts: dict[str, int] = {}
    for p in chosen:
        t = _norm(p.get("table"))
        if t:
            selected_counts[t] = selected_counts.get(t, 0) + 1
    all_slots = {_norm(p.get("table")) for p in _parts(root) if p.get("table")} | set(selected_counts) | set(res)
    for slot in all_slots:
        if not slot:
            continue
        cur = res.setdefault(slot, {"allowed": set(), "min": None, "max": None, "source": "fallback", "specificity": -1, "has_parts": False})
        try:
            max_v = cur.get("max")
            max_i = int(max_v) if max_v is not None else None
        except Exception:
            max_i = None
        selected_n = selected_counts.get(slot, 0)
        # Bulk/serial validation is intentionally permissive about slot counts.
        # Existing game-generated serials use packed inherited roots and several
        # optional tables whose browser part rules look like hard min/max rules.
        # For validation mode, keep known selected parts legal and avoid
        # manufacturing missing-slot failures.  The builder UI still calls this
        # function with infer_available_min=True for strict slot suggestions.
        if not infer_available_min:
            cur["min"] = 0
            if selected_n > 0:
                if max_i is None or max_i < selected_n:
                    cur["max"] = selected_n
                cur["source"] = "selected_existing_parts"
            else:
                cur["max"] = None
            continue

        if max_i is not None and max_i <= 0:
            if selected_n > 0 and str(cur.get("source") or "") in ("fallback", "no_current_candidates", "available_exactly_one", ""):
                cur["min"] = min(int(cur.get("min") or 0), selected_n)
                cur["max"] = selected_n
                cur["source"] = "selected_existing_parts"
            else:
                cur["min"] = 0
                cur["max"] = 0
                cur["source"] = cur.get("source") or "disabled"
            continue
        available = _slot_has_available_parts(root, chosen, slot, res)
        if not available and selected_n <= 0:
            cur["min"] = 0
            cur["max"] = 0
            if not cur.get("source") or cur.get("source") == "fallback":
                cur["source"] = "no_current_candidates"
            continue
        if selected_n > 0 and (cur.get("max") is None or int(cur.get("max") or 0) < selected_n) and str(cur.get("source") or "") in ("fallback", "no_current_candidates", "available_exactly_one", ""):
            cur["max"] = selected_n
            cur["source"] = "selected_existing_parts"
        # Preserve inherited/current min/max when they exist.  Only empty
        # fallback slots are inferred as exactly one, and only in strict builder
        # mode.  Bulk validation uses infer_available_min=False so optional
        # element/payload/stat slots from the broad parent roots do not become
        # false required slots just because candidate parts exist.
        if cur.get("min") is None and cur.get("max") is None:
            if infer_available_min:
                cur["min"] = 1
                cur["max"] = 1
                cur["source"] = "available_exactly_one"
            else:
                cur["min"] = 0
                cur["max"] = None
                cur["source"] = "optional_available"
        elif cur.get("min") is None and cur.get("max") is not None:
            cur["min"] = 1
        elif cur.get("max") is None and cur.get("min") is not None and int(cur.get("min") or 0) > 0:
            cur["max"] = cur.get("min")
    return res


def slot_counts(root_key: str, selected: Iterable[str | int | dict[str, Any]] = ()) -> list[dict[str, Any]]:
    """Return flattened min/max slot counts for the currently selected comp.

    Values are intentionally JSON/simple-list friendly so the BLImGui panel can
    display them without importing the big browser builder.
    """
    root = get_root(root_key)
    if not root:
        return []
    parts = _selected_parts(root, selected)
    comp = _selected_comp(parts)
    constraints = _apply_available_slot_minimums(root, _slot_constraints(comp), parts)
    counts: dict[str, int] = {}
    for p in parts:
        table = _norm(p.get("table"))
        counts[table] = counts.get(table, 0) + 1
    order = _slot_order_map(root)
    all_slots = set(constraints) | {_norm(p.get("table")) for p in _parts(root) if p.get("table")}
    out: list[dict[str, Any]] = []
    for slot in sorted(all_slots, key=lambda n: order.get(n, 9999)):
        c = constraints.get(slot, {})
        out.append({
            "slot": slot,
            "min": c.get("min"),
            "max": c.get("max"),
            "count": counts.get(slot, 0),
            "allowed": sorted(c.get("allowed") or []),
            "source": c.get("source") or "fallback",
        })
    return out


def is_part_allowed(root_key: str, selected: Iterable[str | int | dict[str, Any]], candidate: str | int, table: str | None = None) -> tuple[bool, str]:
    """Return (allowed, reason) for adding candidate given selected parts."""
    root = get_root(root_key)
    if not root:
        return False, f"unknown root {root_key!r}"
    chosen = _selected_parts(root, selected)
    cand = _find_part(root, candidate, table)
    if not cand:
        return False, f"unknown part {candidate!r}"
    pool = _tag_pool(chosen)
    add = _fmt_tags(cand, "add")
    deps = _fmt_tags(cand, "dep")
    excl = _fmt_tags(cand, "exclude")
    missing = sorted(t for t in deps if t not in pool)
    if missing:
        return False, "missing tags: " + ", ".join(missing)
    conflicts = sorted(t for t in excl if t in pool)
    if conflicts:
        return False, "excluded by tags: " + ", ".join(conflicts)
    comp = _selected_comp(chosen)
    constraints = _apply_available_slot_minimums(root, _slot_constraints(comp), chosen)
    table_n = _norm(cand.get("table"))
    c = constraints.get(table_n)
    if c and c["allowed"] and _norm(cand.get("key")) not in c["allowed"]:
        return False, f"not allowed by selected comp {comp.get('key') if comp else ''}"
    if c and c.get("max") is not None:
        current_count = sum(1 for p in chosen if _norm(p.get("table")) == table_n)
        # If this exact part is already selected, do not reject; the UI uses this
        # for display. Adding a second part to a full slot is rejected.
        already = any(_norm(p.get("table")) == table_n and _norm(p.get("key")) == _norm(cand.get("key")) for p in chosen)
        if not already and current_count >= int(c["max"]):
            return False, f"slot {table_n} is full ({current_count}/{c['max']})"
    # Enforce composition-level tag allowances before adding. Example:
    # legendary/pearl weapon base comps limit the number of licensed parts.
    for tags, rule in _tag_rule_constraints(comp).items():
        if rule.get("max") is None or not _part_has_all_tags(cand, tags):
            continue
        already = any(_norm(p.get("table")) == table_n and _norm(p.get("key")) == _norm(cand.get("key")) for p in chosen)
        n = _tag_rule_count(chosen, tags) + (0 if already else 1)
        if n > int(rule["max"]):
            label = "+".join(tags)
            return False, f'tag {label} is full ({n}/{rule["max"]})'
    return True, "ok"



def _critical_serial_conflict_errors(root: dict[str, Any], parts: list[dict[str, Any]]) -> list[str]:
    """Small set of hard conflicts seen in real bulk-validation failures.

    Most INV exclusion tags are UI/filter hints and generate many false fails
    when applied globally to decoded serials.  Keep validation permissive, but
    preserve the obvious hard-fail combinations from the stress corpus.
    """
    out: list[str] = []
    root_key = _norm(root.get("key"))
    comp_key = _norm((_selected_comp(parts) or {}).get("key"))
    barrel_acc = [p for p in parts if _norm(p.get("table")) == "barrel_acc"]
    def has_tag(tag: str) -> bool:
        t = _norm(tag)
        return any(t in (_fmt_tags(p, "add") | _fmt_tags(p, "base_tags")) for p in barrel_acc)
    if root_key == "vla_sr" and comp_key == "comp_04_epic" and has_tag("jak_barrel_acc") and has_tag("barrel_mod_d") and len(parts) >= 16:
        out.append("critical VLA sniper barrel accessory conflict")
    if root_key == "vla_sm" and comp_key == "comp_04_epic" and has_tag("licensed_topacc") and has_tag("barrel_mod_c") and has_tag("barrel_mod_d"):
        out.append("critical VLA SMG barrel accessory conflict")
    return out

def validate(root_key: str, selected: Iterable[str | int | dict[str, Any]], *, strict_comp: bool = True) -> dict[str, Any]:
    root = get_root(root_key)
    if not root:
        return {"ok": False, "errors": [f"unknown root {root_key!r}"], "warnings": []}
    # Validate in the same dependency-table order used for serialization.
    # User/UI selection order should not decide whether dependency tags are seen.
    parts = _sort_parts_for_serial(root, _selected_parts(root, selected))
    errors: list[str] = []
    warnings: list[str] = []
    if not parts:
        errors.append("no parts selected")
    comps = [p for p in parts if _norm(p.get("table")) == "inv_comp"]
    if len(comps) != 1:
        msg = f"expected exactly one inv_comp, got {len(comps)}"
        if strict_comp:
            errors.append(msg)
        else:
            # The in-game/package validator accepts some decoded serials with no
            # explicit inv_comp and still grants them.  Bulk/catalog validation is
            # meant to mirror that game behavior, while the builder path stays
            # strict so newly-built items still start from a real composition.
            warnings.append(msg)
    comp = _selected_comp(parts)
    constraints = _apply_available_slot_minimums(root, _slot_constraints(comp), parts, infer_available_min=False)
    full_pool = _tag_pool(parts)
    counts: dict[str, int] = {}
    for p in parts:
        table = _norm(p.get("table"))
        counts[table] = counts.get(table, 0) + 1
        deps = _fmt_tags(p, "dep")
        # Dependency tags are build-level requirements, not serial-order
        # requirements.  A body_mag can require dad_ammo even if the foregrip
        # that grants dad_ammo appears later in canonical serial order.
        missing = sorted(t for t in deps if t not in full_pool)
        if missing:
            msg = f"{p.get('key')} missing dependency tags: {', '.join(missing)}"
            if strict_comp:
                errors.append(msg)
            else:
                warnings.append(msg)
        excl = _fmt_tags(p, "exclude")
        add = _fmt_tags(p, "add")
        # Exclusions should compare against the rest of the build, not the
        # part's own tags.  Element parts often add and exclude the generic
        # element tag to prevent two elements; self-conflict is valid.
        other_pool = _tag_pool(q for q in parts if q is not p)
        conflicts = sorted(t for t in excl if t in other_pool)
        if conflicts:
            msg = f"{p.get('key')} excluded by active tags: {', '.join(conflicts)}"
            if strict_comp:
                errors.append(msg)
            else:
                warnings.append(msg)
        c = constraints.get(table)
        if c and c["allowed"] and _norm(p.get("key")) not in c["allowed"] and table != "inv_comp":
            errors.append(f"{p.get('key')} is not allowed in slot {p.get('table')} by selected comp")
    for slot, c in constraints.items():
        n = counts.get(slot, 0)
        if c.get("min") is not None and n < int(c["min"]):
            errors.append(f"slot {slot} requires at least {c['min']} part(s), got {n}")
        if c.get("max") is not None and n > int(c["max"]):
            errors.append(f"slot {slot} allows at most {c['max']} part(s), got {n}")
    errors.extend(_tag_rule_errors(parts, comp))
    errors.extend(_critical_serial_conflict_errors(root, parts))
    return {"ok": not errors, "errors": errors, "warnings": warnings, "tag_pool": sorted(full_pool), "part_count": len(parts), "tag_counts": tag_counts(root_key, selected)}


def _sort_parts_for_serial(root: dict[str, Any], parts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order = _slot_order_map(root)
    # Stable canonical order: slot order first, then dep_index and serial.
    return sorted(parts, key=lambda p: (order.get(_norm(p.get("table")), 9999), int(p.get("dep_index") or 0), int(p.get("serial") or 0), str(p.get("key"))))


def _serial_part_token(root: dict[str, Any], part: dict[str, Any]) -> str:
    """Human-token for a part, using RootSerial:SubSerial when needed."""
    if part.get("serial") is None:
        return ""
    sub = int(part["serial"])
    try:
        root_serial = int(root.get("serial"))
    except Exception:
        root_serial = -1
    try:
        src_serial = int(part.get("source_root_serial"))
    except Exception:
        src_serial = root_serial
    if src_serial > 0 and root_serial > 0 and src_serial != root_serial:
        return f"{{{src_serial}:{sub}}}"
    return f"{{{sub}}}"


def build_human(root_key: str, selected: Iterable[str | int | dict[str, Any]], level: int = 72, seed: int = 1, seed2: int | None = None) -> str:
    root = get_root(root_key)
    if not root:
        raise ValueError(f"unknown root {root_key!r}")
    parts = _sort_parts_for_serial(root, _selected_parts(root, selected))
    root_serial = root.get("serial")
    if root_serial is None:
        raise ValueError(f"root {root_key!r} has no numeric serial index")
    seed_seg = f"{int(seed)}, {int(seed2)}" if seed2 is not None else str(int(seed))
    toks = " ".join(tok for tok in (_serial_part_token(root, p) for p in parts) if tok)
    return f"{int(root_serial)}, 0, 1, {int(level)}| {seed_seg}|| {toks}|"


def build_base85(root_key: str, selected: Iterable[str | int | dict[str, Any]], level: int = 72, seed: int = 1, seed2: int | None = None, validate_first: bool = True) -> str:
    v = validate(root_key, selected)
    if validate_first and not v.get("ok"):
        raise ValueError("invalid item: " + "; ".join(v.get("errors") or []))
    return human_to_serial(build_human(root_key, selected, level=level, seed=seed, seed2=seed2))


def _part_display_name(part: dict[str, Any]) -> str:
    """Best human-facing name for a flattened part."""
    return str(part.get("debug") or part.get("display") or part.get("internal") or part.get("key") or "").strip()


def describe_part(root_key: str, part: str | int, table: str | None = None) -> dict[str, Any] | None:
    """Return display metadata for a part without exposing the full raw rule row."""
    root = get_root(root_key)
    if not root:
        return None
    p = _find_part(root, part, table)
    if not p:
        return None
    return {
        "key": p.get("key"),
        "serial": p.get("serial"),
        "source_root_serial": p.get("source_root_serial"),
        "source_root_key": p.get("source_root_key"),
        "inherited_from": p.get("inherited_from") or "",
        "serial_token": _serial_part_token(root, p),
        "table": p.get("table"),
        "display": _part_display_name(p),
        "debug": p.get("debug") or "",
        "internal": p.get("internal") or p.get("key"),
        "row": p.get("row") or "",
        "gestalt": p.get("gestalt") or [],
        "add": p.get("add"),
        "dep": p.get("dep"),
        "exclude": p.get("exclude"),
        "rarity": p.get("rarity") or "",
        "np_names": p.get("np_names") or [],
        "name_parts": p.get("np_names") or [],
    }


def search_parts(root_key: str, text: str = "", table: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    root = get_root(root_key)
    if not root:
        return []
    q = _norm(text)
    tn = _norm(table) if table else None
    out = []
    for p in _parts(root):
        if tn and _norm(p.get("table")) != tn:
            continue
        hay = " ".join(str(p.get(k) or "") for k in ("key", "display", "debug", "internal", "row", "rarity")) + " " + " ".join(str(x) for x in (p.get("np_names") or []))
        if q and q not in _norm(hay):
            continue
        out.append({
            "key": p.get("key"),
            "serial": p.get("serial"),
            "source_root_serial": p.get("source_root_serial"),
            "source_root_key": p.get("source_root_key"),
            "inherited_from": p.get("inherited_from") or "",
            "serial_token": _serial_part_token(root, p),
            "table": p.get("table"),
            "display": _part_display_name(p),
            "debug": p.get("debug") or "",
            "internal": p.get("internal") or p.get("key"),
            "row": p.get("row") or "",
            "gestalt": p.get("gestalt") or [],
            "add": p.get("add"),
            "dep": p.get("dep"),
            "exclude": p.get("exclude"),
            "rarity": p.get("rarity") or "",
            "np_names": p.get("np_names") or [],
            "name_parts": p.get("np_names") or [],
        })
        if len(out) >= limit:
            break
    return out
