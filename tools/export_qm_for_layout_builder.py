#!/usr/bin/env python3
"""Export MSBT Quick Menu layout for BL4 SDK Layout Builder.

Why the old export looked useless
---------------------------------
BL4_SDK_Layout_Builder parses static Azzy-style helpers
(`_button` / `_text` / `_border`) and discovers **screens** from
`_build_ui` + `_UI_TAB_*` branches (or Matt-style `SCREEN_*` +
`rebuild_menu`). The first scaffold dumped all five QM pages into one
function at the **same x/y**, so the editor stacked them; Page 5's
"+ Assign" stubs painted over Page 1's real labels.

This exporter emits builder-native tabbed screens that mirror the live
F7 dock chrome + 3x7 slot grid from `quick_menu.py` /
`quick_menu_registry.py`. It does **not** change the in-game F7 menu.

Outputs:
  - Layout Builder preset JSON (File -> Load preset)
  - Scaffold .sdkmod with Azzy-style `_build_ui` tabs (File -> Open .sdkmod)
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

# --- Geometry mirrors quick_menu.py (offset_x/y = 0) ---
DESIGN_W = 1920.0
DESIGN_H = 1080.0
DOCK_W = 700.0
DOCK_X = DESIGN_W - DOCK_W
HEADER_H = 168.0
CELL_W = 210.0
CELL_H = 56.0
CELL_GAP_X = 8.0
CELL_GAP_Y = 6.0
GRID_COLS = 3
GRID_ROWS = 7
SLOTS_PER_PAGE = 21
MAX_PAGES = 5
RARITY_RESERVE_H = 230.0
BTN_H_HEADER = 44.0
BTN_H_TOOL = 42.0
BTN_H_TAB = 40.0

# Chrome Y positions (py = 0)
CHROME_Y = 68.0
PLAYER_Y = 118.0
TAB_Y = 162.0
TOOL_Y = TAB_Y + 48.0  # 210
INFO_Y = TOOL_Y + 48.0  # 258
GRID_Y0 = INFO_Y + 50.0  # 308 — matches rebuild_ui without empty-page banner

# Colours (RGBA 0-1), approximate MSBT bright theme fills
C_DOCK = (0.08, 0.08, 0.12, 0.92)
C_HEADER = (0.12, 0.10, 0.18, 0.95)
C_EDGE = (0.02, 0.80, 0.70, 1.0)
C_BTN = (0.10, 0.55, 0.48, 0.95)
C_BTN_GOLD = (0.72, 0.55, 0.12, 0.95)
C_BTN_MUTED = (0.22, 0.22, 0.28, 0.85)
C_BTN_DANGER = (0.55, 0.12, 0.16, 0.95)
C_SLOT = (0.10, 0.62, 0.48, 0.95)
C_SLOT_EMPTY = (0.22, 0.22, 0.28, 0.75)
C_TEXT = (1.0, 1.0, 1.0, 1.0)
C_TEXT_DIM = (0.75, 0.78, 0.82, 1.0)
C_OUTLINE = (0.02, 0.02, 0.02, 1.0)

# Labels from quick_menu_registry.ACTION_CATALOG (basic mode).
ACTION_LABELS: dict[str, str] = {
    "max_all": "Max All",
    "max_currency": "Max Currency",
    "max_eridium": "Max Eridium",
    "max_sdu": "Max SDU",
    "max_player_level": "Max Level",
    "max_spec_level": "Max Spec",
    "open_golden_chest": "Open Chest",
    "close_golden_chest": "Close Chest",
    "open_bank": "Open Bank",
    "drop_all_shinies": "Drop Shinies",
    "shiny_selected": "Shinies Selected",
    "shiny_all": "Shinies All",
    "shiny_nonhost": "Shinies Non-Host",
    "repeat_last_drop": "Repeat Last Drop",
    "read_equipped_serials": "Read Equipped Serials",
    "read_backpack_serials": "Read Backpack Serials",
    "read_inventory": "Read Inventory",
    "uvh_boost_all": "UVH Boost All",
    "uvh_boost_cancel": "Cancel UVH",
    "movement_preset_fast": "Fast Movement",
    "movement_preset_veryfast": "Very Fast Movement",
    "movement_preset_moon": "Moon Movement",
    "movement_delete_ground_items": "Clear Ground Loot",
    "movement_hide_ground_loot": "Clear Loot (Hide)",
    "movement_pull_ground_loot": "Pull Loot Here",
    "movement_super_dash": "Super Dash (MSBT)",
    "movement_super_dash_toggle": "Super Dash Toggle (MSBT)",
    "movement_azzy_super_dash": "Super Dash Fire (Azzy)",
    "movement_azzy_super_dash_toggle": "Super Dash Toggle (Azzy)",
    "movement_zero_vault": "Zero Vault Costs",
    "movement_infinite_jump_all_on": "Inf Jump All ON",
    "movement_infinite_jump_all_off": "Inf Jump All OFF",
    "rarity_only_legendary": "Only Legendary",
    "rarity_only_pearlescent": "Only Pearlescent",
    "rarity_apply": "Apply Rarity",
    "rarity_reset": "Reset Rarity",
    "devperk_3": "Kill All Enemies",
    "devperk_7": "Spawn Leg/Epic Loot",
    "set_backpack_bank_selected": "Inv Selected 1k",
    "set_backpack_bank_all": "Inv All Party 1k",
    "kick_player": "Kick Selected",
    "refresh_players": "Refresh Players",
    "travel_to_map": "Travel Map",
    "travel_to_station": "Travel Station",
    "spawn_itempool": "Spawn Item Pool",
}

# Default F7 page 1 (quick_menu_registry.DEFAULT_PAGE_0), then curated extras
# so later pages are editable content — not a wall of blank Assign stubs.
DEFAULT_PAGE_0: list[dict | None] = [
    {"action": "max_all"},
    {"action": "max_currency"},
    {"action": "max_eridium"},
    {"action": "max_sdu"},
    {"action": "drop_all_shinies"},
    {"action": "shiny_selected"},
    {"action": "open_golden_chest"},
    {"action": "close_golden_chest"},
    {"action": "open_bank"},
    {"action": "repeat_last_drop"},
    None,
    None,
]

# Suggested starter pins for pages 2-5 (edit freely in the builder).
SUGGESTED_PAGES: list[list[dict | None]] = [
    # Page 2 — movement / clear loot
    [
        {"action": "movement_preset_fast"},
        {"action": "movement_preset_veryfast"},
        {"action": "movement_super_dash"},
        {"action": "movement_super_dash_toggle"},
        {"action": "movement_azzy_super_dash"},
        {"action": "movement_azzy_super_dash_toggle"},
        {"action": "movement_infinite_jump_all_on"},
        {"action": "movement_infinite_jump_all_off"},
        {"action": "movement_hide_ground_loot"},
        {"action": "movement_delete_ground_items"},
        {"action": "movement_pull_ground_loot"},
        {"action": "movement_zero_vault"},
    ],
    # Page 3 — shinies / serials / inventory helpers
    [
        {"action": "shiny_all"},
        {"action": "shiny_nonhost"},
        {"action": "read_equipped_serials"},
        {"action": "read_backpack_serials"},
        {"action": "read_inventory"},
        {"action": "set_backpack_bank_selected"},
        {"action": "set_backpack_bank_all"},
        {"action": "max_player_level"},
        {"action": "max_spec_level"},
        {"action": "refresh_players"},
        {"action": "kick_player"},
    ],
    # Page 4 — UVH / rarity / travel
    [
        {"action": "uvh_boost_all"},
        {"action": "uvh_boost_cancel"},
        {"action": "rarity_only_legendary"},
        {"action": "rarity_only_pearlescent"},
        {"action": "rarity_apply"},
        {"action": "rarity_reset"},
        {"action": "travel_to_map"},
        {"action": "travel_to_station"},
        {"action": "spawn_itempool"},
        {"action": "devperk_3"},
        {"action": "devperk_7"},
    ],
    # Page 5 — left mostly empty like a fresh F7 page (+ Assign slots)
    [],
]


def default_pages() -> list[list[dict | None]]:
    pages: list[list[dict | None]] = []
    first = list(DEFAULT_PAGE_0)
    while len(first) < SLOTS_PER_PAGE:
        first.append(None)
    pages.append(first[:SLOTS_PER_PAGE])
    for suggested in SUGGESTED_PAGES:
        row = list(suggested)
        while len(row) < SLOTS_PER_PAGE:
            row.append(None)
        pages.append(row[:SLOTS_PER_PAGE])
    while len(pages) < MAX_PAGES:
        pages.append([None for _ in range(SLOTS_PER_PAGE)])
    return pages[:MAX_PAGES]


def _slot_label(slot: dict | None) -> str:
    if not slot:
        return "+ Assign"
    custom = str(slot.get("custom_label") or "").strip()
    if custom:
        return custom[:32]
    action = str(slot.get("action") or "")
    return (ACTION_LABELS.get(action) or action or "+ Assign")[:32]


def _fmt_colour(c: tuple[float, float, float, float]) -> str:
    return f"({c[0]:.2f}, {c[1]:.2f}, {c[2]:.2f}, {c[3]:.2f})"


def _escape_label(label: str) -> str:
    return label.replace("\\", "\\\\").replace('"', '\\"')


def _widget(
    *,
    wid: str,
    kind: str,
    label: str,
    x: float,
    y: float,
    w: float,
    h: float,
    colour: list[float] | None = None,
    meta: dict | None = None,
    text_scale: float | None = None,
) -> dict[str, Any]:
    return {
        "id": wid,
        "kind": kind,
        "label": label,
        "x": float(x),
        "y": float(y),
        "w": float(w),
        "h": float(h),
        "colour": colour if colour is not None else list(C_BTN),
        "text_scale": text_scale,
        "source_span": None,
        "arg_spans": {},
        "locked": False,
        "meta": meta or {},
    }


def _screen_name(page_i: int) -> str:
    return f"QM Page {page_i + 1}"


def _slot_xy(idx: int) -> tuple[float, float]:
    row, col = divmod(idx, GRID_COLS)
    x = DOCK_X + 12 + col * (CELL_W + CELL_GAP_X)
    y = GRID_Y0 + row * (CELL_H + CELL_GAP_Y)
    return x, y


def _chrome_widgets(screen: str) -> list[dict[str, Any]]:
    """Shared dock chrome — duplicated per screen so filtered views stay complete."""
    px, py, pw = DOCK_X, 0.0, DOCK_W
    meta_base = {"screen": screen, "msbt_role": "chrome"}
    widgets: list[dict[str, Any]] = [
        _widget(
            wid=f"{screen}__edge",
            kind="border",
            label="",
            x=px - 6,
            y=py,
            w=6,
            h=DESIGN_H,
            colour=list(C_EDGE),
            meta={**meta_base, "role": "edge"},
        ),
        _widget(
            wid=f"{screen}__dock",
            kind="border",
            label="MSBT Quick Menu",
            x=px,
            y=py,
            w=pw,
            h=DESIGN_H,
            colour=list(C_DOCK),
            meta={**meta_base, "role": "panel"},
        ),
        _widget(
            wid=f"{screen}__header",
            kind="border",
            label="",
            x=px,
            y=py,
            w=pw,
            h=HEADER_H,
            colour=list(C_HEADER),
            meta={**meta_base, "role": "header"},
        ),
        _widget(
            wid=f"{screen}__title",
            kind="text",
            label="MSBT Quick Menu",
            x=px + 12,
            y=py + 8,
            w=280,
            h=36,
            colour=list(C_TEXT),
            text_scale=0.68,
            meta={**meta_base, "role": "title"},
        ),
        _widget(
            wid=f"{screen}__subtitle",
            kind="text",
            label=f"RUN | {screen} | Lock OFF | 1.00x | MSBT Neon",
            x=px + 12,
            y=py + 42,
            w=pw - 24,
            h=24,
            colour=list(C_TEXT_DIM),
            text_scale=0.36,
            meta={**meta_base, "role": "subtitle"},
        ),
    ]

    header_btns = [
        ("MOVE", px + 12, 72, C_BTN),
        ("THEME", px + 90, 84, C_BTN_GOLD),
        ("-", px + 180, 40, C_BTN_MUTED),
        ("1.00x", px + 226, 72, C_BTN_MUTED),
        ("+", px + 304, 40, C_BTN_MUTED),
        ("RESET POS", px + 350, 110, C_BTN),
        ("Edit", px + pw - 236, 100, C_BTN_GOLD),
        ("Close F7", px + pw - 128, 116, C_BTN_DANGER),
    ]
    for i, (label, x, w, colour) in enumerate(header_btns):
        widgets.append(
            _widget(
                wid=f"{screen}__hdr_{i}",
                kind="button",
                label=label,
                x=x,
                y=CHROME_Y,
                w=w,
                h=BTN_H_HEADER,
                colour=list(colour),
                text_scale=0.42,
                meta={**meta_base, "role": "header_btn"},
            )
        )

    slot_w, slot_gap = 74.0, 6.0
    slot_x = px + 12
    for slot_i in range(4):
        widgets.append(
            _widget(
                wid=f"{screen}__p{slot_i}",
                kind="button",
                label=f"P{slot_i + 1}",
                x=slot_x,
                y=PLAYER_Y,
                w=slot_w,
                h=36,
                colour=list(C_SLOT_EMPTY),
                text_scale=0.30,
                meta={**meta_base, "role": "player_slot", "player_slot": slot_i},
            )
        )
        slot_x += slot_w + slot_gap
    widgets.append(
        _widget(
            wid=f"{screen}__pall",
            kind="button",
            label="PAll",
            x=slot_x,
            y=PLAYER_Y,
            w=70,
            h=36,
            colour=list(C_BTN_MUTED),
            text_scale=0.34,
            meta={**meta_base, "role": "player_all"},
        )
    )

    tab_x = px + 12
    for page_i in range(MAX_PAGES):
        active = screen == _screen_name(page_i)
        widgets.append(
            _widget(
                wid=f"{screen}__tab_p{page_i}",
                kind="button",
                label=f"P{page_i + 1}",
                x=tab_x,
                y=TAB_Y,
                w=64,
                h=BTN_H_TAB,
                colour=list(C_BTN_GOLD if active else C_BTN_MUTED),
                text_scale=0.42,
                meta={**meta_base, "role": "page_tab", "page": page_i},
            )
        )
        tab_x += 70
    widgets.append(
        _widget(
            wid=f"{screen}__tab_inv",
            kind="button",
            label="INV",
            x=tab_x,
            y=TAB_Y,
            w=64,
            h=BTN_H_TAB,
            colour=list(C_BTN_GOLD if screen == "QM INV" else C_BTN_MUTED),
            text_scale=0.42,
            meta={**meta_base, "role": "inv_tab"},
        )
    )

    if screen != "QM INV":
        for i, (label, x, w, colour) in enumerate(
            [
                ("Pin Last", px + 12, 130, C_BTN_GOLD),
                ("Lock", px + 150, 90, C_BTN),
                ("Target", px + 248, 100, C_BTN),
                ("Refresh", px + 356, 110, C_BTN_MUTED),
            ]
        ):
            widgets.append(
                _widget(
                    wid=f"{screen}__tool_{i}",
                    kind="button",
                    label=label,
                    x=x,
                    y=TOOL_Y,
                    w=w,
                    h=BTN_H_TOOL,
                    colour=list(colour),
                    text_scale=0.46,
                    meta={**meta_base, "role": "tool_btn"},
                )
            )
        widgets.append(
            _widget(
                wid=f"{screen}__info_target",
                kind="text",
                label="Target: (none)",
                x=px + 12,
                y=INFO_Y,
                w=pw - 24,
                h=22,
                colour=list(C_TEXT_DIM),
                text_scale=0.34,
                meta={**meta_base, "role": "info"},
            )
        )
        widgets.append(
            _widget(
                wid=f"{screen}__info_last",
                kind="text",
                label="Last: (none) | Drop: (none)",
                x=px + 12,
                y=INFO_Y + 22,
                w=pw - 24,
                h=22,
                colour=list(C_TEXT_DIM),
                text_scale=0.34,
                meta={**meta_base, "role": "info"},
            )
        )
    return widgets


def _page_slot_widgets(page_i: int, page: list[dict | None]) -> list[dict[str, Any]]:
    screen = _screen_name(page_i)
    slots = list(page)
    while len(slots) < SLOTS_PER_PAGE:
        slots.append(None)
    widgets: list[dict[str, Any]] = []
    for idx in range(SLOTS_PER_PAGE):
        slot = slots[idx]
        x, y = _slot_xy(idx)
        label = _slot_label(slot)
        colour = list(C_SLOT if slot else C_SLOT_EMPTY)
        widgets.append(
            _widget(
                wid=f"qm_p{page_i}_s{idx}",
                kind="button",
                label=label,
                x=x,
                y=y,
                w=CELL_W,
                h=CELL_H,
                colour=colour,
                text_scale=0.38,
                meta={
                    "screen": screen,
                    "page": page_i,
                    "slot": idx,
                    "action": (slot or {}).get("action") if slot else None,
                    "msbt_role": "quick_menu_slot",
                },
            )
        )
    # Rarity strip placeholders (equipped layout reserve)
    rarity_y = GRID_Y0 + GRID_ROWS * CELL_H + (GRID_ROWS - 1) * CELL_GAP_Y + 10
    widgets.append(
        _widget(
            wid=f"qm_p{page_i}_rarity",
            kind="border",
            label="Rarity panel (optional)",
            x=DOCK_X + 12,
            y=rarity_y,
            w=DOCK_W - 24,
            h=RARITY_RESERVE_H,
            colour=list(C_BTN_MUTED),
            meta={"screen": screen, "page": page_i, "msbt_role": "rarity_panel"},
        )
    )
    for i, label in enumerate(["Apply", "Reset", "Only Leg", "Only Pearl"]):
        widgets.append(
            _widget(
                wid=f"qm_p{page_i}_rarity_btn_{i}",
                kind="button",
                label=label,
                x=DOCK_X + 20 + i * 160,
                y=rarity_y + 36,
                w=150,
                h=40,
                colour=list(C_BTN_GOLD if i == 0 else C_BTN),
                text_scale=0.34,
                meta={"screen": screen, "page": page_i, "msbt_role": "rarity_btn"},
            )
        )
    return widgets


def _inv_widgets() -> list[dict[str, Any]]:
    screen = "QM INV"
    widgets = _chrome_widgets(screen)
    px, pw = DOCK_X, DOCK_W
    body_y = TAB_Y + 48
    widgets.append(
        _widget(
            wid="qm_inv_body",
            kind="border",
            label="Inventory browser",
            x=px + 12,
            y=body_y,
            w=pw - 24,
            h=720,
            colour=list(C_BTN_MUTED),
            meta={"screen": screen, "msbt_role": "inv_body"},
        )
    )
    widgets.append(
        _widget(
            wid="qm_inv_title",
            kind="text",
            label="INV tab (placeholder — live F7 lists backpack serials)",
            x=px + 24,
            y=body_y + 16,
            w=pw - 48,
            h=36,
            colour=list(C_TEXT),
            text_scale=0.42,
            meta={"screen": screen, "msbt_role": "inv_title"},
        )
    )
    for i, label in enumerate(
        ["Refresh Inv", "Give Selected", "Prev Page", "Next Page", "Back to Actions"]
    ):
        row, col = divmod(i, 2)
        widgets.append(
            _widget(
                wid=f"qm_inv_btn_{i}",
                kind="button",
                label=label,
                x=px + 24 + col * 320,
                y=body_y + 80 + row * 56,
                w=300,
                h=48,
                colour=list(C_BTN),
                text_scale=0.40,
                meta={"screen": screen, "msbt_role": "inv_btn"},
            )
        )
    return widgets


def build_widgets(pages: list[list[dict | None]]) -> list[dict[str, Any]]:
    widgets: list[dict[str, Any]] = []
    for page_i, page in enumerate(pages[:MAX_PAGES]):
        screen = _screen_name(page_i)
        widgets.extend(_chrome_widgets(screen))
        widgets.extend(_page_slot_widgets(page_i, page))
    widgets.extend(_inv_widgets())
    return widgets


def build_preset(pages: list[list[dict | None]], *, screen: str = "(all pages)") -> dict[str, Any]:
    return {
        "source_mod": "MSBT_QuickMenu_LayoutBuilder",
        "package": "MSBT_QuickMenu_LayoutBuilder",
        "screen": screen,
        "design_width": DESIGN_W,
        "design_height": DESIGN_H,
        "widgets": build_widgets(pages),
        "notes": (
            "Synthetic MSBT Quick Menu for BL4 SDK Layout Builder. "
            "Use the Screen dropdown (QM Page 1-5 / QM INV). "
            "Not the live F7 UMG menu — port coordinates back manually. "
            "Builder format: Azzy _button/_text/_border + _UI_TAB screens."
        ),
    }


def _py_button(label: str, x: float, y: float, w: float, h: float, colour: tuple[float, ...], *, tab_const: str | None = None, text_scale: float = 0.40) -> str:
    esc = _escape_label(label)
    col = _fmt_colour(colour)  # type: ignore[arg-type]
    if tab_const:
        cb = f"lambda: _set_ui_tab({tab_const})"
    else:
        cb = "lambda: None"
    return (
        f'    _button("{esc}", {x:.1f}, {y:.1f}, {w:.1f}, {h:.1f}, '
        f"{cb}, {col}, text_scale={text_scale:.2f})"
    )


def _py_text(label: str, x: float, y: float, w: float, h: float, colour: tuple[float, ...], text_scale: float = 0.40) -> str:
    esc = _escape_label(label)
    col = _fmt_colour(colour)  # type: ignore[arg-type]
    return (
        f'    _text("{esc}", {x:.1f}, {y:.1f}, {w:.1f}, {h:.1f}, '
        f"{col}, text_scale={text_scale:.2f})"
    )


def _py_border(x: float, y: float, w: float, h: float, colour: tuple[float, ...], radius: int = 4) -> str:
    col = _fmt_colour(colour)  # type: ignore[arg-type]
    return f"    _border({x:.1f}, {y:.1f}, {w:.1f}, {h:.1f}, {col}, {radius})"


def _emit_chrome_py(lines: list[str], *, active_tab: str) -> None:
    px, py, pw = DOCK_X, 0.0, DOCK_W
    lines.append(_py_border(px - 6, py, 6, DESIGN_H, C_EDGE, 1))
    lines.append(_py_border(px, py, pw, DESIGN_H, C_DOCK, 2))
    lines.append(_py_border(px, py, pw, HEADER_H, C_HEADER, 3))
    lines.append(_py_text("MSBT Quick Menu", px + 12, py + 8, 280, 36, C_TEXT, 0.68))
    pretty = {
        "_UI_TAB_P1": "P1/5",
        "_UI_TAB_P2": "P2/5",
        "_UI_TAB_P3": "P3/5",
        "_UI_TAB_P4": "P4/5",
        "_UI_TAB_P5": "P5/5",
        "_UI_TAB_INV": "INV",
    }.get(active_tab, "P1/5")
    lines.append(
        _py_text(
            f"RUN | {pretty} | Lock OFF | 1.00x | MSBT Neon",
            px + 12,
            py + 42,
            pw - 24,
            24,
            C_TEXT_DIM,
            0.36,
        )
    )
    for label, x, w, colour in [
        ("MOVE", px + 12, 72, C_BTN),
        ("THEME", px + 90, 84, C_BTN_GOLD),
        ("-", px + 180, 40, C_BTN_MUTED),
        ("1.00x", px + 226, 72, C_BTN_MUTED),
        ("+", px + 304, 40, C_BTN_MUTED),
        ("RESET POS", px + 350, 110, C_BTN),
        ("Edit", px + pw - 236, 100, C_BTN_GOLD),
        ("Close F7", px + pw - 128, 116, C_BTN_DANGER),
    ]:
        lines.append(_py_button(label, x, CHROME_Y, w, BTN_H_HEADER, colour, text_scale=0.42))

    slot_w, slot_gap = 74.0, 6.0
    slot_x = px + 12
    for slot_i in range(4):
        lines.append(
            _py_button(f"P{slot_i + 1}", slot_x, PLAYER_Y, slot_w, 36, C_SLOT_EMPTY, text_scale=0.30)
        )
        slot_x += slot_w + slot_gap
    lines.append(_py_button("PAll", slot_x, PLAYER_Y, 70, 36, C_BTN_MUTED, text_scale=0.34))

    tab_x = px + 12
    for page_i in range(MAX_PAGES):
        const = f"_UI_TAB_P{page_i + 1}"
        active = active_tab == const
        colour = C_BTN_GOLD if active else C_BTN_MUTED
        lines.append(
            _py_button(
                f"P{page_i + 1}",
                tab_x,
                TAB_Y,
                64,
                BTN_H_TAB,
                colour,
                tab_const=const,
                text_scale=0.42,
            )
        )
        tab_x += 70
    inv_active = active_tab == "_UI_TAB_INV"
    lines.append(
        _py_button(
            "INV",
            tab_x,
            TAB_Y,
            64,
            BTN_H_TAB,
            C_BTN_GOLD if inv_active else C_BTN_MUTED,
            tab_const="_UI_TAB_INV",
            text_scale=0.42,
        )
    )


def _emit_page_body_py(lines: list[str], page_i: int, page: list[dict | None]) -> None:
    px, pw = DOCK_X, DOCK_W
    for label, x, w, colour in [
        ("Pin Last", px + 12, 130, C_BTN_GOLD),
        ("Lock", px + 150, 90, C_BTN),
        ("Target", px + 248, 100, C_BTN),
        ("Refresh", px + 356, 110, C_BTN_MUTED),
    ]:
        lines.append(_py_button(label, x, TOOL_Y, w, BTN_H_TOOL, colour, text_scale=0.46))
    lines.append(_py_text("Target: (none)", px + 12, INFO_Y, pw - 24, 22, C_TEXT_DIM, 0.34))
    lines.append(
        _py_text("Last: (none) | Drop: (none)", px + 12, INFO_Y + 22, pw - 24, 22, C_TEXT_DIM, 0.34)
    )

    slots = list(page)
    while len(slots) < SLOTS_PER_PAGE:
        slots.append(None)
    for idx in range(SLOTS_PER_PAGE):
        slot = slots[idx]
        x, y = _slot_xy(idx)
        label = _slot_label(slot)
        colour = C_SLOT if slot else C_SLOT_EMPTY
        lines.append(_py_button(label, x, y, CELL_W, CELL_H, colour, text_scale=0.38))

    rarity_y = GRID_Y0 + GRID_ROWS * CELL_H + (GRID_ROWS - 1) * CELL_GAP_Y + 10
    lines.append(_py_border(DOCK_X + 12, rarity_y, DOCK_W - 24, RARITY_RESERVE_H, C_BTN_MUTED, 4))
    lines.append(
        _py_text(
            "Rarity panel (optional in live F7)",
            DOCK_X + 20,
            rarity_y + 8,
            DOCK_W - 40,
            24,
            C_TEXT_DIM,
            0.34,
        )
    )
    for i, label in enumerate(["Apply", "Reset", "Only Leg", "Only Pearl"]):
        lines.append(
            _py_button(
                label,
                DOCK_X + 20 + i * 160,
                rarity_y + 36,
                150,
                40,
                C_BTN_GOLD if i == 0 else C_BTN,
                text_scale=0.34,
            )
        )


def _emit_inv_body_py(lines: list[str]) -> None:
    px, pw = DOCK_X, DOCK_W
    body_y = TAB_Y + 48
    lines.append(_py_border(px + 12, body_y, pw - 24, 720, C_BTN_MUTED, 4))
    lines.append(
        _py_text(
            "INV tab (placeholder — live F7 lists backpack serials)",
            px + 24,
            body_y + 16,
            pw - 48,
            36,
            C_TEXT,
            0.42,
        )
    )
    for i, label in enumerate(
        ["Refresh Inv", "Give Selected", "Prev Page", "Next Page", "Back to Actions"]
    ):
        row, col = divmod(i, 2)
        tab = "_UI_TAB_P1" if label == "Back to Actions" else None
        lines.append(
            _py_button(
                label,
                px + 24 + col * 320,
                body_y + 80 + row * 56,
                300,
                48,
                C_BTN,
                tab_const=tab,
                text_scale=0.40,
            )
        )


def build_scaffold_py(pages: list[list[dict | None]]) -> str:
    """Azzy-style _build_ui + _UI_TAB_* so Layout Builder Screen dropdown works.

    Chrome + tab strip are always drawn; only the page/INV body sits behind
    `_ui_active_tab` branches so discover_screens() can compose one page at a time.
    """
    lines: list[str] = [
        '"""MSBT Quick Menu layout scaffold for BL4 SDK Layout Builder only.',
        "",
        "NOT loaded by the in-game F7 Quick Menu.",
        "Open this .sdkmod in BL4_SDK_Layout_Builder, then use Screen filter:",
        "  QM Page 1..5 / INV (from _UI_TAB_* branches below).",
        '"""',
        "",
        "DESIGN_WIDTH = 1920.0",
        "DESIGN_HEIGHT = 1080.0",
        "",
        "# --- BL4 Layout Builder tabs (MSBT Quick Menu) ---",
        '_UI_TAB_P1 = "p1"',
        '_UI_TAB_P2 = "p2"',
        '_UI_TAB_P3 = "p3"',
        '_UI_TAB_P4 = "p4"',
        '_UI_TAB_P5 = "p5"',
        '_UI_TAB_INV = "inv"',
        "_ui_active_tab = _UI_TAB_P1",
        "",
        "",
        "def _set_ui_tab(tab: str) -> None:",
        '    """Switch Layout Builder screen tab."""',
        "    global _ui_active_tab",
        "    _ui_active_tab = tab",
        "",
        "",
        "def _rebuild_ui_if_open() -> None:",
        "    return None",
        "",
        "",
        "def _build_ui(_button, _text, _border):",
        "    # Always-visible dock chrome + P1-P5/INV tab strip.",
        "    # Per-page slot grids live in the _ui_active_tab branches below.",
        "",
    ]

    # Shared chrome once (tab highlight approximates Page 1 active — builder
    # recomposes per-screen views from branches).
    _emit_chrome_py(lines, active_tab="_UI_TAB_P1")
    lines.append("")

    for page_i, page in enumerate(pages[:MAX_PAGES]):
        const = f"_UI_TAB_P{page_i + 1}"
        if page_i == 0:
            lines.append(f"    if _ui_active_tab == {const}:")
        else:
            lines.append(f"    elif _ui_active_tab == {const}:")
        body: list[str] = []
        _emit_page_body_py(body, page_i, page)
        for raw in body:
            lines.append("    " + raw)
        lines.append("        return True")
        lines.append("")

    lines.append("    elif _ui_active_tab == _UI_TAB_INV:")
    body = []
    _emit_inv_body_py(body)
    for raw in body:
        lines.append("    " + raw)
    lines.append("        return True")
    lines.append("")
    lines.append("    return True")
    lines.append("")
    return "\n".join(lines)


def write_scaffold_sdkmod(path: Path, pages: list[list[dict | None]]) -> None:
    package = "MSBT_QuickMenu_LayoutBuilder"
    init_py = (
        '"""Layout-Builder-only scaffold package. Not a gameplay mod."""\n'
        "from . import qm_layout\n\n"
        "def build_mod(*_args, **_kwargs):\n"
        "    return None\n"
    )
    pyproject = (
        "[project]\n"
        f'name = "{package}"\n'
        'version = "0.0.2"\n'
        'description = "MSBT Quick Menu scaffold for BL4 SDK Layout Builder"\n'
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        base = f"{package}/"
        zf.writestr(base + "__init__.py", init_py)
        zf.writestr(base + "qm_layout.py", build_scaffold_py(pages))
        zf.writestr(base + "pyproject.toml", pyproject)


def _verify_not_all_assign(sdkmod_path: Path) -> dict[str, int]:
    """Sanity-check scaffold contents for the Matt-visible failure mode."""
    counts = {"max_all": 0, "assign": 0, "p5_assign": 0, "ui_tabs": 0, "buttons": 0}
    with zipfile.ZipFile(sdkmod_path, "r") as zf:
        text = zf.read(f"{sdkmod_path.stem}/qm_layout.py").decode("utf-8")
    counts["max_all"] = text.count('"Max All"')
    counts["assign"] = text.count('"+ Assign"')
    counts["p5_assign"] = text.count('"P5 + Assign"')
    counts["ui_tabs"] = text.count("_UI_TAB_P")
    counts["buttons"] = text.count("_button(")
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "docs" / "layout_builder",
        help="Output directory for preset + scaffold sdkmod",
    )
    args = parser.parse_args()
    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    pages = default_pages()
    preset_path = out_dir / "msbt_quick_menu.layout_preset.json"
    sdkmod_path = out_dir / "MSBT_QuickMenu_LayoutBuilder.sdkmod"
    preset = build_preset(pages)
    preset_path.write_text(json.dumps(preset, indent=2) + "\n", encoding="utf-8")
    write_scaffold_sdkmod(sdkmod_path, pages)

    labels = [w["label"] for w in preset["widgets"] if w["kind"] == "button"]
    unique_sample = sorted({lab for lab in labels if lab not in {"+ Assign", "P1", "P2", "P3", "P4", "P5", "INV"}})[:12]
    verify = _verify_not_all_assign(sdkmod_path)

    print(f"Wrote preset:  {preset_path}")
    print(f"Wrote sdkmod:  {sdkmod_path}")
    print(f"Widgets:       {len(preset['widgets'])}")
    print(f"Screens:       QM Page 1-5 + QM INV")
    print(f"Sample labels: {', '.join(unique_sample)}")
    print(f"Verify:        {verify}")
    if verify["p5_assign"]:
        raise SystemExit("Export still contains P5 + Assign — aborting")
    if verify["max_all"] < 1:
        raise SystemExit("Export missing Max All — aborting")
    if verify["ui_tabs"] < 5:
        raise SystemExit("Export missing _UI_TAB page constants — aborting")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
