# Electron UI Editing Guide

MSBT's Electron app is the real design surface. Use this guide when you want to adjust the app without rebuilding it in a separate visual editor.

## Start Here

For visual tuning, edit:

```text
electron_poc/ui-designer.css
```

That file is loaded after the main stylesheet, so it can change common visual choices without digging through the whole app.

Good first edits:

- `--ui-button-height`: makes every normal button taller or shorter.
- `--ui-button-padding-x`: makes buttons wider inside.
- `--ui-panel-padding`: changes how much breathing room each section has.
- `--ui-grid-gap`: changes the space between cards and panels.
- `--ui-bl4-card-min-width`: makes BL4 image cards bigger or smaller.
- `--ui-bl4-card-min-height`: makes BL4 image cards taller or shorter.
- `--ui-title-size`: changes the main app title size.
- `--ui-section-title-size`: changes section heading size.

## Editing Text

Most fixed labels, headings, and button text live in:

```text
electron_poc/renderer.html
```

Examples:

- top app title and support buttons;
- tab names;
- Boosting tab card headings;
- fixed action buttons;
- form labels;
- warning/helper text.

Some generated list text is created in:

```text
electron_poc/renderer.js
```

Use that file for text inside generated rows, cards, browser results, status messages, and catalog details.

## Moving Buttons And Sections

For fixed UI, move the actual HTML block in:

```text
electron_poc/renderer.html
```

This is the safest way to move a real button or section because the app keeps the same button ID and click handler.

General rule:

- Moving a button inside the same tab is usually safe.
- Renaming an `id` is risky because JavaScript may look for that exact ID.
- Removing a `data-action` or `data-*` attribute will usually break the button.

## Changing Layout Without Moving Code

For spacing, density, and broad layout shape, edit:

```text
electron_poc/ui-designer.css
```

If the change is specific to one tab or one card, edit:

```text
electron_poc/styles.css
```

Examples:

- `.grid.two`, `.grid.three`, and `.grid.five` control common column layouts.
- `.panel` controls card-like sections.
- `.button-grid` controls groups of action buttons.
- `.bl4-card-grid` and `.bl4-code-card` control BL4 image cards.
- `.dev-*` classes control Dev Spawner rows and browser sections.

## Do Not Change These Casually

Avoid changing these unless you are intentionally updating behavior:

- `id="..."` values;
- `data-action="..."`;
- `data-bl4-send-mode="..."`;
- `data-bookmark-send-mode="..."`;
- `data-editor-serial-mode="..."`;
- bridge action names;
- file names loaded by scripts.

Those connect the visible UI to real app behavior.

## Quick Test Loop

After visual-only edits:

```powershell
cd electron_poc
npm.cmd run check
npm.cmd start
```

If you only changed CSS, a full package rebuild is not needed for a quick local look.
