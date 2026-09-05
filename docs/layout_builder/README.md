# MSBT Quick Menu → BL4 SDK Layout Builder

Matt: the live F7 Quick Menu will **not** open usefully as `MattsSDKBoostingTools.sdkmod` because Layout Builder parses **static** Azzy-style `_button(x,y,w,h)` / `_text` / `_border` calls (and discovers **Screens** from `_build_ui` + `_UI_TAB_*` branches). MSBT builds F7 procedurally in UMG loops (`quick_menu.py`).

This folder is a **Layout-Builder-compatible scaffold** of the default QM dock: real page labels, chrome (MOVE / THEME / P1–P4 / INV / rarity reserve), and separate Screens per page.

Editing here does **not** change in-game F7 until you port numbers back by hand.

## Why the first export looked empty

The v1 scaffold put all five pages’ 21-slot grids at the **same coordinates** in one function. Layout Builder stacked them; Page 5’s `+ Assign` stubs covered Page 1’s “Max All” / “Max Currency” / … labels. That’s what the “P5 + Assign” screenshot was.

## Files

| File | Open how |
| --- | --- |
| [`MSBT_QuickMenu_LayoutBuilder.sdkmod`](./MSBT_QuickMenu_LayoutBuilder.sdkmod) | **File → Open .sdkmod** (preferred) |
| [`msbt_quick_menu.layout_preset.json`](./msbt_quick_menu.layout_preset.json) | **Load preset** |

Tool path: `C:\Users\mwenn\Desktop\BL4_SDK_Layout_Builder.exe`

## How to open

1. Launch `BL4_SDK_Layout_Builder.exe`.
2. **File → Open .sdkmod** →  
   `docs/layout_builder/MSBT_QuickMenu_LayoutBuilder.sdkmod`
3. Use the **Screen** dropdown (not “(all pages)” if grids look stacked):
   - **QM Page 1** — default F7 pins (Max All, Max Currency, …)
   - **QM Page 2–4** — suggested starter pins (movement / shinies / UVH)
   - **QM Page 5** — mostly empty `+ Assign` slots (like a fresh F7 page)
   - **QM INV** — inventory tab placeholder
4. Or **Load preset** → `msbt_quick_menu.layout_preset.json` and filter by Screen the same way.

You should see labeled actions on Page 1 (not a wall of Assign stubs).

## Regenerate after QM defaults change

```bash
python tools/export_qm_for_layout_builder.py
```

Optional: `--out-dir path\to\folder`

## What the builder can / can’t represent

| Can | Can’t / won’t match live F7 |
| --- | --- |
| Dock geometry, slot grid 3×7, chrome button boxes | Live UMG rebuild, themes, opacity, window scale |
| Per-page Screens via `_UI_TAB_*` | Runtime player names / Lock / Last-drop text |
| Slot labels from `ACTION_CATALOG` basics | Payload-bearing pins (serial text, travel map, …) as real data |
| Drag boxes, rebuild `.sdkmod`, save preset | INV serial browser contents |
| Rarity strip **placeholder** boxes | Live rarity sliders wired to backend |

Reference fork (patterns only, not vendored): [funkyoushift/Bl4SDKmods](https://github.com/funkyoushift/Bl4SDKmods).

## What this is not

- Not loaded by Borderlands 4 / F7.
- Not a replacement for `quick_menu_registry` persistence.
- Not Squ1ggs Boosting Tools — scaffold only so Layout Builder can edit MSBT QM geometry.
