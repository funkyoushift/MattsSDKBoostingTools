# Electron panel layout

Tabs marked with `data-msbt-layout-tab` use **GridStack** docking (every main content tab with panels).

## What you can do

- **Drag freely** — panels may **overlap** (no shove-aside while dragging); **click** a panel to bring it to the front
- **Resize** from panel edges / corner
- **Stack as tabs** — drop a panel onto the **center** of another (dashed highlight). Use tab buttons to switch; **drag a tab name** to detach that panel; **⧉** also pops the active tab
- **Compact** — packs panels, fills gaps, and clears overlaps
- **Collapse / hide** from the panel chrome; restore from **Panels** (toolbar) or **View → Panels** (checkbox list). After hide, a one-time toast points you there.
- **Reset layout** restores the default arrangement for that tab
- **View** menu (header): text size (A− / A+ / slider, 85%–140%), show/hide/reorder main nav tabs

Layouts persist in `localStorage` under `msbt.panelLayout.v2.<tabId>`. Text scale: `msbt.uiTextScale`. Nav tabs: `msbt.navTabs.v1`.

Post-update / first-run overview, layout editor tour, Quick Menu setup tour, and per-tab Walkthrough buttons: see [`TUTORIALS.md`](TUTORIALS.md).

## Enabled tabs

Boosting, Quick Menu, Serial Tools, Inventory, BL4 Codes, Matt Editor, Item Pool, Dev Spawner, Map Travel, Player Movement, Activity Log, Report, Updates.

## Files

- [`electron_poc/panel_layout.js`](../electron_poc/panel_layout.js)
- [`gridstack`](https://github.com/gridstack/gridstack.js) (npm dependency)
- Markers on sections in [`electron_poc/renderer.html`](../electron_poc/renderer.html)
