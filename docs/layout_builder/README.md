# MSBT Quick Menu → BL4 SDK Layout Builder

Matt: the live F7 Quick Menu will **not** open usefully in `BL4_SDK_Layout_Builder.exe` because that tool parses **static** `_button(x, y, w, h)` / BLImGui-style Python inside a `.sdkmod`. MSBT builds the QM procedurally in UMG (`quick_menu.py` loops).

This folder is a **Layout-Builder-compatible export** of the default QM dock + slot grid. Editing it does **not** change in-game F7 until you port numbers back by hand (or extend the exporter later).

Reference only (not vendored): [funkyoushift/Bl4SDKmods](https://github.com/funkyoushift/Bl4SDKmods) (Squ1ggs fork) for spawner/layout-builder ecosystem patterns.

## Files

| File | Open how |
| --- | --- |
| [`MSBT_QuickMenu_LayoutBuilder.sdkmod`](./MSBT_QuickMenu_LayoutBuilder.sdkmod) | In Layout Builder: **File → Open .sdkmod** (or “Open BL4 mod”) |
| [`msbt_quick_menu.layout_preset.json`](./msbt_quick_menu.layout_preset.json) | **Load layout preset** / open `*.json` preset dialog |

Tool path on Matt’s machine: `C:\Users\mwenn\Desktop\BL4_SDK_Layout_Builder.exe`

## How to open

1. Launch `BL4_SDK_Layout_Builder.exe`.
2. Prefer **File → Open .sdkmod** and choose  
   `docs/layout_builder/MSBT_QuickMenu_LayoutBuilder.sdkmod`.
3. Or use **Load layout preset** and choose  
   `docs/layout_builder/msbt_quick_menu.layout_preset.json`.
4. You should see the right-side dock chrome plus Page 1–5 slot boxes (default actions filled on page 1; empty pages show assign placeholders).

## Regenerate after QM defaults change

```bash
python tools/export_qm_for_layout_builder.py
```

Optional: `--out-dir path\to\folder`

## What this is not

- Not loaded by Borderlands 4 / F7.
- Not a replacement for `quick_menu_registry` persistence.
- Not a copy of Squ1ggs Boosting Tools — scaffold only so Layout Builder can open MSBT’s QM geometry.
