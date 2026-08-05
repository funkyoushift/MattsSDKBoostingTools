"""In-game Inventory tab for MSBT Quick Menu (mirrors Electron Inventory view)."""

from __future__ import annotations

import time
from typing import Any, Callable

from . import backend_actions

# Lazy imports from quick_menu to avoid circular import at module load.
_STATE = None
_COLORS = None
_UI = None


def _bind_quick_menu() -> None:
    global _STATE, _COLORS, _UI
    if _STATE is not None:
        return
    from . import quick_menu

    _STATE = quick_menu.STATE
    _COLORS = {
        "dock": quick_menu.C_DOCK,
        "header": quick_menu.C_HEADER,
        "btn": quick_menu.C_BTN,
        "gold": quick_menu.C_BTN_GOLD,
        "danger": quick_menu.C_BTN_DANGER,
        "muted": quick_menu.C_BTN_MUTED,
        "slot": quick_menu.C_SLOT,
        "slot_sel": quick_menu.C_SLOT_SEL,
        "slot_empty": quick_menu.C_SLOT_EMPTY,
        "text": quick_menu.C_TEXT,
        "text_dim": quick_menu.C_TEXT_DIM,
    }
    _UI = {
        "with_alpha": quick_menu._with_alpha,
        "rebuild_ui": quick_menu.rebuild_ui,
        "show_toast": quick_menu.show_toast,
        "set_status_from_result": quick_menu._set_status_from_result,
        "panel_x": quick_menu.panel_x,
        "panel_w": quick_menu.panel_w,
        "SCALE_BTN": quick_menu.SCALE_BTN,
        "SCALE_BODY": quick_menu.SCALE_BODY,
        "SCALE_HINT": quick_menu.SCALE_HINT,
        "SCALE_MODAL_TITLE": quick_menu.SCALE_MODAL_TITLE,
        "SCALE_MODAL_BTN": quick_menu.SCALE_MODAL_BTN,
        "MODAL_BLOCKER_Z": quick_menu.MODAL_BLOCKER_Z,
        "MODAL_PANEL_Z": quick_menu.MODAL_PANEL_Z,
        "MODAL_CONTENT_Z": quick_menu.MODAL_CONTENT_Z,
        "MODAL_BUTTON_Z": quick_menu.MODAL_BUTTON_Z,
        "BTN_H_TOOL": quick_menu.BTN_H_TOOL,
    }


EQUIP_SLOTS: tuple[tuple[int, str], ...] = (
    (0, "W1"),
    (1, "W2"),
    (2, "W3"),
    (3, "W4"),
    (4, "Shield"),
    (5, "Ord"),
    (6, "Rep"),
    (7, "Enh"),
    (8, "COM"),
)

SORT_OPTIONS: tuple[tuple[str, str], ...] = (
    ("recent", "Recent"),
    ("rarity", "Rarity"),
    ("type", "Type"),
    ("level", "Level"),
    ("manufacturer", "Mfr"),
)

CATEGORIES: tuple[str, ...] = (
    "All",
    "Guns",
    "Shields",
    "Ordnance",
    "Repkits",
    "Enhancements",
    "Class Mods",
    "Other",
)

RARITY_RANK: dict[str, int] = {
    "Pearlescent": 6,
    "Legendary": 5,
    "Epic": 4,
    "Rare": 3,
    "Uncommon": 2,
    "Common": 1,
}

# Azzy neon rarity tiles — pink / purple / cyan / lime (no mustard/cream).
RARITY_FILL: dict[str, tuple[float, float, float, float]] = {
    "Pearlescent": (0.85, 0.63, 0.97, 0.98),  # soft purple
    "Legendary": (1.0, 0.18, 0.44, 0.98),  # hot pink
    "Epic": (0.55, 0.18, 0.85, 0.98),
    "Rare": (0.0, 0.90, 1.0, 0.98),  # cyan
    "Uncommon": (0.49, 1.0, 0.18, 0.98),  # lime
    "Common": (0.20, 0.10, 0.40, 0.98),  # deep purple
}


def display_name(entry: dict[str, Any] | None) -> str:
    if not entry:
        return "Empty"
    for key in ("display_name", "summary", "label"):
        value = str(entry.get(key) or "").strip()
        if value:
            return value
    return "Item"


def entry_key(entry: dict[str, Any] | None, fallback: str = "") -> str:
    if not entry:
        return fallback
    serial = str(entry.get("serial") or "").strip()
    if serial:
        return serial
    return f"{entry.get('label', '')}:{entry.get('slot', '')}:{fallback}"


def rarity_fill(entry: dict[str, Any] | None, default: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    rarity = str((entry or {}).get("rarity") or "").strip()
    if rarity in RARITY_FILL:
        return RARITY_FILL[rarity]
    key = rarity.lower()
    for name, fill in RARITY_FILL.items():
        if name.lower() in key or key in name.lower():
            return fill
    return default


def _compare(a: dict[str, Any], b: dict[str, Any]) -> int:
    _bind_quick_menu()
    st = _STATE
    sort = str(st.inv_sort or "recent")
    desc = str(st.inv_sort_dir or "desc") != "asc"
    cmp = 0
    if sort == "rarity":
        ra = RARITY_RANK.get(str(a.get("rarity") or ""), 0)
        rb = RARITY_RANK.get(str(b.get("rarity") or ""), 0)
        cmp = ra - rb
    elif sort == "type":
        ta = str(a.get("item_type") or a.get("category") or "")
        tb = str(b.get("item_type") or b.get("category") or "")
        cmp = (ta > tb) - (ta < tb)
    elif sort == "level":
        la = a.get("level")
        lb = b.get("level")
        na = float(la) if la is not None else -1.0
        nb = float(lb) if lb is not None else -1.0
        cmp = (na > nb) - (na < nb)
    elif sort == "manufacturer":
        ma = str(a.get("manufacturer") or "")
        mb = str(b.get("manufacturer") or "")
        cmp = (ma > mb) - (ma < mb)
    else:
        ia = a.get("backpack_index")
        ib = b.get("backpack_index")
        na = float(ia) if ia is not None else 1e9
        nb = float(ib) if ib is not None else 1e9
        cmp = (na > nb) - (na < nb)
    if cmp and desc:
        cmp = -cmp
    if cmp:
        return cmp
    da = display_name(a)
    db = display_name(b)
    return (da > db) - (da < db)


def filtered_backpack() -> list[dict[str, Any]]:
    _bind_quick_menu()
    st = _STATE
    category = str(st.inv_category or "All")
    items: list[dict[str, Any]] = []
    for entry in list(st.inv_backpack or []):
        if category != "All" and str(entry.get("category") or "Other") != category:
            continue
        items.append(dict(entry))
    from functools import cmp_to_key

    return sorted(items, key=cmp_to_key(_compare))


def apply_inventory_result(result: dict[str, Any]) -> None:
    _bind_quick_menu()
    st = _STATE
    inv = dict(result.get("inventory") or {})
    st.inv_equipped = [dict(e) for e in list(inv.get("equipped") or [])]
    st.inv_backpack = [dict(e) for e in list(inv.get("backpack") or [])]
    st.inv_truncated = bool(inv.get("truncated"))
    st.inv_page = 0
    st.inv_reading = str(result.get("reading") or result.get("message") or "")[:120]
    if st.inv_give_target is None:
        idx = backend_actions.get_selected_player_index()
        if idx is not None:
            st.inv_give_target = int(idx)


def refresh_inventory() -> None:
    _bind_quick_menu()
    result = backend_actions.read_inventory(None)
    _UI["set_status_from_result"](result)
    if result.get("ok"):
        apply_inventory_result(result)
        _UI["show_toast"](str(result.get("message") or "Inventory refreshed.")[:140], ok=True, seconds=2.0)
    _UI["rebuild_ui"]()


def open_inventory_tab(*, refresh: bool = False) -> None:
    _bind_quick_menu()
    st = _STATE
    st.main_tab = "inventory"
    if refresh or (not st.inv_equipped and not st.inv_backpack):
        result = backend_actions.read_inventory(None)
        if result.get("ok"):
            apply_inventory_result(result)
        _UI["set_status_from_result"](result)
    _UI["rebuild_ui"]()


def select_entry(entry: dict[str, Any]) -> None:
    _bind_quick_menu()
    st = _STATE
    st.inv_selected_key = entry_key(entry)
    st.inv_selected_entry = dict(entry)
    st.modal = "inv_detail"
    _UI["rebuild_ui"]()


def _give_selected_entry() -> None:
    _bind_quick_menu()
    st = _STATE
    entry = dict(st.inv_selected_entry or {})
    serial = str(entry.get("serial") or "").strip()
    if not serial.startswith("@U"):
        _UI["show_toast"]("No @U serial on selected item.", ok=False, seconds=2.0)
        return
    give_idx = st.inv_give_target
    if give_idx is None:
        _UI["show_toast"]("Pick a Give-to player first.", ok=False, seconds=2.0)
        return
    copies = max(1, min(50, int(st.inv_multiplier or 1)))
    view_idx = backend_actions.get_selected_player_index()
    players = backend_actions.refresh_players()
    match = next((p for p in players if int(p.get("index", -1)) == int(give_idx)), None)
    if match is None:
        _UI["show_toast"](f"P{int(give_idx) + 1} not in party.", ok=False, seconds=2.0)
        return
    backend_actions.set_target_player(f"{give_idx}|{match.get('name') or ''}")
    payload = "\n".join([serial] * copies)
    result = backend_actions.give_serials(payload, mode="selected")
    if view_idx is not None and int(view_idx) != int(give_idx):
        view_match = next((p for p in players if int(p.get("index", -1)) == int(view_idx)), None)
        if view_match is not None:
            backend_actions.set_target_player(f"{view_idx}|{view_match.get('name') or ''}")
    _UI["set_status_from_result"](result)
    name = display_name(entry)
    if result.get("ok"):
        _UI["show_toast"](f"Sent {copies}× {name} to P{int(give_idx) + 1}.", ok=True, seconds=2.5)
    st.modal = ""
    _UI["rebuild_ui"]()


def _copy_selected_serial() -> None:
    _bind_quick_menu()
    st = _STATE
    entry = dict(st.inv_selected_entry or {})
    serial = str(entry.get("serial") or "").strip()
    if not serial.startswith("@U"):
        _UI["show_toast"]("No @U serial.", ok=False, seconds=2.0)
        return
    from . import item_serial_reader

    ok = bool(item_serial_reader.write_clipboard_text(serial))
    backend_actions.serial_text = serial
    _UI["show_toast"](
        "Copied serial." if ok else "Serial in serial_text (clipboard unavailable).",
        ok=True,
        seconds=2.0,
    )


def render_tab(factory: Any, root: Any, px: float, py: float, pw: float, opacity: float) -> float:
    """Render inventory body; returns footer_y."""
    _bind_quick_menu()
    st = _STATE
    c = _COLORS
    ui = _UI
    alpha = ui["with_alpha"]
    tab_y = py + 162
    y = tab_y + 48

    def _btn(label: str, x: float, y0: float, w: float, h: float, action: Callable[[], None], fill: tuple, scale: float = ui["SCALE_BTN"]) -> None:
        factory.button(root, label, x, y0, w, h, action, fill=alpha(fill, opacity), scale=scale)

    _btn("Refresh", px + 12, y, 110, ui["BTN_H_TOOL"], refresh_inventory, c["gold"])
    _btn("Actions", px + 130, y, 100, ui["BTN_H_TOOL"], lambda: _switch_actions(), c["muted"])
    reading = st.inv_reading or _reading_label()
    factory.text(root, reading[:70], px + 240, y + 4, pw - 252, 22, scale=ui["SCALE_HINT"], z=5, tint=c["text_dim"])
    y += 50

    # Equipped strip
    factory.text(root, "Equipped", px + 12, y, 120, 20, scale=ui["SCALE_BODY"], z=5, tint=c["gold"])
    y += 24
    by_slot: dict[int, dict[str, Any]] = {}
    for entry in list(st.inv_equipped or []):
        try:
            slot_i = int(entry.get("slot"))
            if slot_i >= 0:
                by_slot[slot_i] = entry
        except Exception:
            pass
    ex = px + 12
    for slot_i, slot_label in EQUIP_SLOTS:
        entry = by_slot.get(slot_i)
        label = display_name(entry)[:14] if entry else slot_label
        fill = rarity_fill(entry, c["slot_empty"] if entry is None else c["slot"])
        if entry and entry_key(entry) == st.inv_selected_key:
            fill = c["slot_sel"]

        def _pick(e: dict[str, Any] | None = entry) -> Callable[[], None]:
            return lambda: select_entry(e) if e else ui["rebuild_ui"]()

        _btn(label, ex, y, 78, 44, _pick(), fill, scale=0.28)
        ex += 82
        if ex > px + pw - 90:
            ex = px + 12
            y += 48
    y += 52

    # Sort + category
    dir_label = "↓" if str(st.inv_sort_dir or "desc") != "asc" else "↑"

    def _toggle_dir() -> None:
        st.inv_sort_dir = "asc" if str(st.inv_sort_dir or "desc") != "asc" else "desc"
        st.inv_page = 0
        ui["rebuild_ui"]()

    _btn(dir_label, px + 12, y, 36, 34, _toggle_dir, c["muted"], scale=0.36)
    sx = px + 54
    for sort_key, sort_label in SORT_OPTIONS:
        active = str(st.inv_sort or "recent") == sort_key

        def _set_sort(k: str = sort_key) -> Callable[[], None]:
            def _go() -> None:
                st.inv_sort = k
                st.inv_page = 0
                ui["rebuild_ui"]()

            return _go

        _btn(sort_label, sx, y, 72, 34, _set_sort(), c["gold"] if active else c["btn"], scale=0.26)
        sx += 76
    y += 40
    sx = px + 12
    for cat in CATEGORIES:
        active = str(st.inv_category or "All") == cat
        w = 62 if cat != "Enhancements" else 78
        label = cat.replace("Enhancements", "Enh").replace("Class Mods", "COM")

        def _set_cat(cn: str = cat) -> Callable[[], None]:
            def _go() -> None:
                st.inv_category = cn
                st.inv_page = 0
                ui["rebuild_ui"]()

            return _go

        _btn(label, sx, y, w, 32, _set_cat(), c["gold"] if active else c["muted"], scale=0.24)
        sx += w + 4
        if sx > px + pw - 70:
            sx = px + 12
            y += 36
    y += 38

    filtered = filtered_backpack()
    page_size = max(1, int(st.inv_page_size or 10))
    max_page = max(0, (len(filtered) - 1) // page_size) if filtered else 0
    if st.inv_page > max_page:
        st.inv_page = max_page
    start = st.inv_page * page_size
    page_items = filtered[start : start + page_size]
    trunc = " capped" if st.inv_truncated else ""
    factory.text(
        root,
        f"Filter: {len(filtered)} · {len(st.inv_backpack or [])} backpack · {len(st.inv_equipped or [])} equipped{trunc}",
        px + 12,
        y,
        pw - 24,
        20,
        scale=ui["SCALE_HINT"],
        z=5,
        tint=c["text_dim"],
    )
    y += 22

    scroll = factory.scroll_box(root, px + 12, y, pw - 24, 320, z=5)
    if not page_items:
        row = factory.scroll_row(scroll, pw - 64, 56)
        msg = "No items — Refresh Inventory." if not st.inv_backpack else "No items match filters."
        factory.text(row, msg, 8, 10, pw - 80, 36, scale=ui["SCALE_BTN"], z=1, center=True)
    for entry in page_items:
        name = display_name(entry)[:28]
        meta_bits = []
        rarity = str(entry.get("rarity") or "")
        if rarity:
            meta_bits.append(rarity[:8])
        level = entry.get("level")
        if level is not None:
            meta_bits.append(f"L{level}")
        mfr = str(entry.get("manufacturer") or "")[:10]
        if mfr:
            meta_bits.append(mfr)
        meta = " · ".join(meta_bits)
        label = f"{name}\n{meta}" if meta else name
        fill = rarity_fill(entry, c["slot"])
        if entry_key(entry) == st.inv_selected_key:
            fill = c["slot_sel"]

        def _pick(e: dict[str, Any] = entry) -> Callable[[], None]:
            return lambda: select_entry(e)

        row = factory.scroll_row(scroll, pw - 64, 62)
        factory.button(row, label, 0, 2, pw - 72, 56, _pick(), fill=fill, scale=0.26, z=1)

    y += 328
    prev_disabled = st.inv_page <= 0
    next_disabled = start + page_size >= len(filtered)

    def _prev() -> None:
        st.inv_page = max(0, int(st.inv_page) - 1)
        ui["rebuild_ui"]()

    def _next() -> None:
        st.inv_page = min(max_page, int(st.inv_page) + 1)
        ui["rebuild_ui"]()

    _btn("Prev", px + 12, y, 80, ui["BTN_H_TOOL"], _prev, c["muted"] if not prev_disabled else c["slot_empty"])
    factory.text(
        root,
        f"Page {st.inv_page + 1}/{max_page + 1}",
        px + 100,
        y + 6,
        120,
        24,
        scale=ui["SCALE_HINT"],
        z=5,
        center=True,
    )
    _btn("Next", px + 230, y, 80, ui["BTN_H_TOOL"], _next, c["muted"] if not next_disabled else c["slot_empty"])
    return y + 52


def _reading_label() -> str:
    idx = backend_actions.get_selected_player_index()
    name = backend_actions.get_selected_player_name() or ""
    if idx is None:
        return "Reading: (pick P1–P4)"
    short = str(name)[:12] if name else "?"
    return f"Reading: {short} (P{int(idx) + 1})"


def _switch_actions() -> None:
    _bind_quick_menu()
    _STATE.main_tab = "actions"
    _UI["rebuild_ui"]()


def render_detail_modal(factory: Any, root: Any) -> None:
    _bind_quick_menu()
    st = _STATE
    c = _COLORS
    ui = _UI
    entry = dict(st.inv_selected_entry or {})
    if not entry:
        st.modal = ""
        return
    px = ui["panel_x"]()
    pw = ui["panel_w"]()
    factory.modal_blocker(root)
    factory.border(root, px + 12, 120, pw - 24, 780, ui["with_alpha"](c["dock"], 1.0), ui["MODAL_PANEL_Z"])
    factory.border(root, px + 12, 120, pw - 24, 64, ui["with_alpha"](c["header"], 1.0), ui["MODAL_CONTENT_Z"])
    title = display_name(entry)
    factory.text(
        root,
        title[:48],
        px + 24,
        130,
        pw - 48,
        44,
        scale=ui["SCALE_MODAL_TITLE"],
        z=ui["MODAL_CONTENT_Z"] + 1,
        center=True,
    )
    meta_bits = [
        str(entry.get("rarity") or ""),
        f"L{entry.get('level')}" if entry.get("level") is not None else "",
        str(entry.get("item_type") or entry.get("category") or ""),
        str(entry.get("manufacturer") or ""),
    ]
    meta = " · ".join(b for b in meta_bits if b)
    factory.text(root, meta[:80], px + 24, 188, pw - 48, 24, scale=ui["SCALE_BODY"], z=ui["MODAL_CONTENT_Z"] + 1, tint=c["text_dim"])
    serial = str(entry.get("serial") or "")
    short = serial if len(serial) <= 36 else (serial[:16] + "…" + serial[-14:])
    factory.text(root, short, px + 24, 218, pw - 48, 48, scale=0.22, z=ui["MODAL_CONTENT_Z"] + 1)

    factory.text(root, "Give to", px + 24, 280, 80, 22, scale=ui["SCALE_BODY"], z=ui["MODAL_CONTENT_Z"] + 1)
    party = backend_actions.refresh_players()
    gx = px + 24
    for p in party:
        try:
            idx = int(p.get("index", -1))
        except Exception:
            continue
        if idx < 0:
            continue
        label = f"P{idx + 1}"
        nm = str(p.get("name") or "")[:5]
        if nm:
            label = f"P{idx + 1}:{nm}"
        active = st.inv_give_target is not None and int(st.inv_give_target) == idx

        def _set_give(i: int = idx) -> Callable[[], None]:
            def _go() -> None:
                st.inv_give_target = i
                ui["rebuild_ui"]()

            return _go

        factory.button(
            root,
            label,
            gx,
            304,
            74,
            36,
            _set_give(),
            fill=c["gold"] if active else c["btn"],
            scale=0.26,
            modal_only=True,
        )
        gx += 78

    factory.text(root, f"Multiplier: {int(st.inv_multiplier or 1)}", px + 24, 352, 160, 22, scale=ui["SCALE_BODY"], z=ui["MODAL_CONTENT_Z"] + 1)

    def _mul(delta: int) -> Callable[[], None]:
        def _go() -> None:
            st.inv_multiplier = max(1, min(50, int(st.inv_multiplier or 1) + delta))
            ui["rebuild_ui"]()

        return _go

    factory.button(root, "-", px + 190, 348, 40, 36, _mul(-1), fill=c["muted"], scale=0.36, modal_only=True)
    factory.button(root, "+", px + 236, 348, 40, 36, _mul(1), fill=c["muted"], scale=0.36, modal_only=True)
    factory.button(root, "x5", px + 282, 348, 44, 36, lambda: _set_mul(5), fill=c["btn"], scale=0.30, modal_only=True)
    factory.button(root, "x10", px + 332, 348, 48, 36, lambda: _set_mul(10), fill=c["btn"], scale=0.30, modal_only=True)

    def _set_mul(v: int) -> None:
        st.inv_multiplier = max(1, min(50, int(v)))
        ui["rebuild_ui"]()

    factory.button(
        root,
        "Send to Game",
        px + 24,
        400,
        pw - 48,
        52,
        _give_selected_entry,
        fill=c["gold"],
        scale=ui["SCALE_MODAL_BTN"],
        modal_only=True,
    )
    factory.button(
        root,
        "Copy Serial",
        px + 24,
        462,
        (pw - 64) / 2,
        48,
        _copy_selected_serial,
        fill=c["btn"],
        scale=ui["SCALE_MODAL_BTN"],
        modal_only=True,
    )

    def _close() -> None:
        st.modal = ""
        ui["rebuild_ui"]()

    factory.button(
        root,
        "Close",
        px + 24 + (pw - 64) / 2 + 16,
        462,
        (pw - 64) / 2,
        48,
        _close,
        fill=c["danger"],
        scale=ui["SCALE_MODAL_BTN"],
        modal_only=True,
    )
