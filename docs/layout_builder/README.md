# MSBT Quick Menu → BL4 SDK Layout Builder (UMG-only)

## Open this file

```
docs/layout_builder/MSBT_QuickMenu_UMG_Only.sdkmod
```

Tool: `C:\Users\mwenn\Desktop\BL4_SDK_Layout_Builder.exe` → **File → Open .sdkmod**

Then use the **Screen** dropdown (not “(all pages)” if grids look stacked):

| Screen | What you should see |
| --- | --- |
| **QM Page 1** | Real F7 defaults: Max All, Max Currency, Max Eridium, … |
| **QM Page 2–4** | Suggested starter pins (movement / shinies / UVH) |
| **QM Page 5** | Mostly empty `+ Assign` slots (like a fresh F7 page) |
| **QM INV** | Inventory tab placeholder |

Compat alias (same contents, old name): `MSBT_QuickMenu_LayoutBuilder.sdkmod`

## Why full MSBT.sdkmod will not open (expected)

Layout Builder rejects packages that ship **Dear ImGui / blimgui**. The live gameplay archive `MattsSDKBoostingTools.sdkmod` still includes optional `blimgui_panel.py`, so File → Open on that package fails with “UI is Dear ImGui / blimgui… not UMG”.

That does **not** mean F7 is ImGui. Live F7 Quick Menu is native UMG (`quick_menu.py` + `quick_menu_registry.py`). The builder just cannot edit the full mixed package.

## What this pack is

A **UMG-only** Layout Builder scaffold:

- Absolute `_button(x,y,w,h)` / `_text` / `_border` boxes (Azzy patterns)
- `_build_ui` + `_UI_TAB_*` screens so the Screen dropdown works
- Labels from live `quick_menu_registry.ACTION_CATALOG` / `DEFAULT_PAGE_0`
- Dock chrome mirrored from `quick_menu.py` geometry (offset 0)
- **Zero** `blimgui_panel.py`, `blimgui` imports, or Dear ImGui draw calls

Editing here does **not** change in-game F7 until you port numbers back by hand.

## Regenerate (stays UMG-only)

```bash
python tools/export_qm_for_layout_builder.py
```

Optional: `--out-dir path\to\folder`

The exporter refuses to finish if the zip contains blimgui files/imports, lacks `_build_ui` / `_UI_TAB_*`, or regresses to the old “P5 + Assign” wall.

## Verify unzip by hand

```bash
python -c "import zipfile; z=zipfile.ZipFile(r'docs/layout_builder/MSBT_QuickMenu_UMG_Only.sdkmod'); print('\n'.join(z.namelist()))"
```

Expected members only:

- `MSBT_QuickMenu_UMG_Only/__init__.py`
- `MSBT_QuickMenu_UMG_Only/qm_layout.py`
- `MSBT_QuickMenu_UMG_Only/pyproject.toml`
- `MSBT_QuickMenu_UMG_Only/README_LAYOUT.txt`

No `blimgui_panel.py`.

## What the builder can / can’t represent

| Can | Can’t / won’t match live F7 |
| --- | --- |
| Dock geometry, slot grid 3×7, chrome button boxes | Live UMG rebuild, themes, opacity, window scale |
| Per-page Screens via `_UI_TAB_*` | Runtime player names / Lock / Last-drop text |
| Slot labels from `ACTION_CATALOG` basics | Payload-bearing pins as real data |
| Drag boxes, rebuild `.sdkmod`, save preset | INV serial browser contents |
| Rarity strip **placeholder** boxes | Live rarity sliders wired to backend |

Reference fork (patterns only, not vendored): [funkyoushift/Bl4SDKmods](https://github.com/funkyoushift/Bl4SDKmods).

## What this is not

- Not loaded by Borderlands 4 / F7.
- Not a replacement for `quick_menu_registry` persistence.
- Not Squ1ggs Boosting Tools — scaffold only so Layout Builder can edit MSBT QM geometry.
