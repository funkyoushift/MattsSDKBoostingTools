#!/usr/bin/env python3
"""Export MSBT Quick Menu layout as BL4 SDK Layout Builder presets / scaffold.

BL4_SDK_Layout_Builder opens .sdkmod packages that declare static _button(x,y,w,h)
widgets (Squ1ggs/Azzy BLImGui style). MSBT's in-game F7 Quick Menu is built
procedurally in UMG loops, so the live MattsSDKBoostingTools.sdkmod does not
load usefully in the builder.

This script is self-contained (no mods_base / unrealsdk). It mirrors defaults
from quick_menu_registry / quick_menu layout constants.

Outputs:
  - a Layout Builder preset JSON (File → Load layout preset)
  - a minimal scaffold .sdkmod with static _button() calls (File → Open .sdkmod)

It does not change the in-game F7 Quick Menu.
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DESIGN_W = 1920.0
DESIGN_H = 1080.0
DOCK_W = 700.0
DOCK_X = DESIGN_W - DOCK_W
CELL_W = 210.0
CELL_H = 56.0
CELL_GAP_X = 8.0
CELL_GAP_Y = 6.0
GRID_COLS = 3
GRID_ROWS = 7
SLOTS_PER_PAGE = 21
MAX_PAGES = 5
PANEL_X = DOCK_X
PANEL_Y = 0.0
# Approximate default dock chrome from quick_menu.rebuild_ui (offset_x/y = 0).
GRID_ORIGIN_Y = 322.0

ACTION_LABELS: dict[str, str] = {
    "max_all": "Max All",
    "max_currency": "Max Currency",
    "max_eridium": "Max Eridium",
    "max_sdu": "Max SDU",
    "drop_all_shinies": "Drop All Shinies",
    "shiny_selected": "Shiny Selected",
    "open_golden_chest": "Open Chest",
    "close_golden_chest": "Close Chest",
    "open_bank": "Open Bank",
    "repeat_last_drop": "Repeat Drop",
}

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


def default_pages() -> list[list[dict | None]]:
    first = list(DEFAULT_PAGE_0)
    while len(first) < SLOTS_PER_PAGE:
        first.append(None)
    pages = [first[:SLOTS_PER_PAGE]]
    for _ in range(MAX_PAGES - 1):
        pages.append([None for _ in range(SLOTS_PER_PAGE)])
    return pages


def _slot_label(slot: dict | None, page: int, index: int) -> str:
    if not slot:
        return f"P{page + 1} + Assign"
    action = str(slot.get("action") or "")
    custom = str(slot.get("custom_label") or "").strip()
    if custom:
        return custom[:32]
    return (ACTION_LABELS.get(action) or action or "slot")[:32]


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
) -> dict:
    return {
        "id": wid,
        "kind": kind,
        "label": label,
        "x": float(x),
        "y": float(y),
        "w": float(w),
        "h": float(h),
        "colour": colour if colour is not None else [0.12, 0.55, 0.42, 0.92],
        "text_scale": None,
        "source_span": None,
        "arg_spans": {},
        "locked": False,
        "meta": meta or {},
    }


def build_widgets(pages: list[list[dict | None]]) -> list[dict]:
    widgets: list[dict] = []
    widgets.append(
        _widget(
            wid="qm_panel",
            kind="border",
            label="MSBT Quick Menu dock",
            x=PANEL_X,
            y=PANEL_Y,
            w=DOCK_W,
            h=DESIGN_H,
            colour=[0.08, 0.08, 0.12, 0.85],
            meta={"role": "panel"},
        )
    )
    widgets.append(
        _widget(
            wid="qm_title",
            kind="text",
            label="MSBT Quick Menu",
            x=PANEL_X + 12,
            y=PANEL_Y + 8,
            w=280,
            h=36,
            colour=[1.0, 1.0, 1.0, 1.0],
            meta={"role": "title"},
        )
    )
    for page_i, page in enumerate(pages[:MAX_PAGES]):
        screen = f"QM Page {page_i + 1}"
        slots = list(page)
        while len(slots) < SLOTS_PER_PAGE:
            slots.append(None)
        for idx in range(SLOTS_PER_PAGE):
            row, col = divmod(idx, GRID_COLS)
            x = PANEL_X + 12 + col * (CELL_W + CELL_GAP_X)
            y = GRID_ORIGIN_Y + row * (CELL_H + CELL_GAP_Y)
            slot = slots[idx]
            label = _slot_label(slot, page_i, idx)
            colour = [0.10, 0.62, 0.48, 0.95] if slot else [0.22, 0.22, 0.28, 0.75]
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
                    meta={
                        "screen": screen,
                        "page": page_i,
                        "slot": idx,
                        "action": (slot or {}).get("action") if slot else None,
                        "msbt_role": "quick_menu_slot",
                    },
                )
            )
    return widgets


def build_preset(pages: list[list[dict | None]], *, screen: str = "(all pages)") -> dict:
    return {
        "source_mod": "MSBT_QuickMenu_LayoutBuilder",
        "package": "MSBT_QuickMenu_LayoutBuilder",
        "screen": screen,
        "design_width": DESIGN_W,
        "design_height": DESIGN_H,
        "widgets": build_widgets(pages),
        "notes": (
            "Synthetic MSBT Quick Menu layout for BL4 SDK Layout Builder. "
            "Not the live F7 UMG menu — edit boxes here, then port numbers back manually. "
            "Reference fork for Squ1ggs patterns: https://github.com/funkyoushift/Bl4SDKmods"
        ),
    }


def build_scaffold_py(pages: list[list[dict | None]]) -> str:
    lines = [
        '"""MSBT Quick Menu layout scaffold for BL4 SDK Layout Builder only.',
        "",
        "This file is NOT loaded by the in-game F7 Quick Menu.",
        '"""',
        "",
        "DESIGN_WIDTH = 1920.0",
        "DESIGN_HEIGHT = 1080.0",
        "",
        "",
        "def draw_msbt_quick_menu_layout(_button, _text, _border):",
        "    # Dock chrome",
        f"    _border({PANEL_X:.1f}, {PANEL_Y:.1f}, {DOCK_W:.1f}, {DESIGN_H:.1f})",
        f'    _text("MSBT Quick Menu", {PANEL_X + 12:.1f}, {PANEL_Y + 8:.1f}, 280.0, 36.0)',
        "",
    ]
    for page_i, page in enumerate(pages[:MAX_PAGES]):
        lines.append(f"    # --- QM Page {page_i + 1} ---")
        slots = list(page)
        while len(slots) < SLOTS_PER_PAGE:
            slots.append(None)
        for idx in range(SLOTS_PER_PAGE):
            row, col = divmod(idx, GRID_COLS)
            x = PANEL_X + 12 + col * (CELL_W + CELL_GAP_X)
            y = GRID_ORIGIN_Y + row * (CELL_H + CELL_GAP_Y)
            label = _slot_label(slots[idx], page_i, idx).replace('"', "'")
            lines.append(
                f'    _button("{label}", {x:.1f}, {y:.1f}, {CELL_W:.1f}, {CELL_H:.1f})'
            )
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
        'version = "0.0.1"\n'
        'description = "MSBT Quick Menu scaffold for BL4 SDK Layout Builder"\n'
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        base = f"{package}/"
        zf.writestr(base + "__init__.py", init_py)
        zf.writestr(base + "qm_layout.py", build_scaffold_py(pages))
        zf.writestr(base + "pyproject.toml", pyproject)


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

    print(f"Wrote preset:  {preset_path}")
    print(f"Wrote sdkmod:  {sdkmod_path}")
    print(f"Widgets:       {len(preset['widgets'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
