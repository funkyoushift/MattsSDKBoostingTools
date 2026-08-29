# Electron tutorials

Coach-mark tours in the desktop app. Copy lives in a structured map in [`electron_poc/renderer.js`](../electron_poc/renderer.js) (`TUTORIAL_TOURS` + `TAB_TUTORIALS`).

The tour overlay stays lightly dimmed so the highlighted control and active tab stay readable; the spotlight ring/pulse carries attention. On each step the engine scrolls the target into view (`.tab-shell` / panels) and repositions the coach-mark card so it does not cover small targets like **+ QM**.

## Main overview (first-run / post-update)

Auto-opens when `localStorage` `msbt.lastSeenVersion` is missing or differs from the current app version. Finishing or skipping sets `msbt.lastSeenVersion` and `msbt.tutorial.mainSeen` to that version.

**Content (first-run order):** Welcome (SDK + download) → Bridge & status → Boosting → Serial Tools → Hoard Builder → Map Travel → Player Movement → Quick Menu → Updates (header Updates / Find; tab is hidden by default) → Activity Log → Layout tip (auto-enables the layout toolbar) → deep-dive chooser. Each step highlights the control or panel it describes. Update notification banner / startup update modal stay suppressed while any tour is open, then restore when the tour closes.

Chooser options:

- Full **Layout editor** walkthrough
- Full **Quick Menu setup** walkthrough (covers the ★ Quick Menu tab and in-game dock — there is no separate QM-tab-only tour)
- Per-tab walkthroughs (each main tab except Quick Menu, which redirects to Quick Menu setup)
- **I'm done** (footer button; checkbox: don’t auto-show until the next update)

Walkthroughs started from this chooser return to the chooser when finished or skipped, so the user can take several in one sitting. Tours started from **View** or a tab **Walkthrough** button end normally and do not reopen the chooser.

Replay: ★ Quick Menu → **App Walkthrough**, or **View → App overview**.

## Layout editor (full)

Always reachable from the main chooser or **View → Layout walkthrough**. The tour turns the layout toolbar on (it is hidden by default). Covers drag/overlap/click-to-front, center-drop stack, detach, Compact, Reset, Panels restore, View text size + hide/reorder tabs.

## Quick Menu setup (full)

Always reachable from the main chooser, **View → Quick Menu setup**, or the ★ Quick Menu tab **Walkthrough** button. Covers in-game Quick Menu (F7) open/close, Esc/F6, MOVE/THEME, 5×21 pages + INV, Electron slot editor, + QM pinning (highlights a real + QM on Boosting), rarity modules, travel closing QM, and how Electron complements the dock.

## Per-tab Walkthrough buttons

Each layout tab toolbar has **Walkthrough** — short steps on real controls/workflows for that tab (not layout-only filler). One layout tip step appears where useful.

**★ Quick Menu** Walkthrough launches **Quick Menu setup** (same full tour), not a shorter duplicate.

**Matt Editor** stays short: full save editor + item creator (own host port, not Mobile Gateway), plus a Ko-fi support link for Mattmab (`https://ko-fi.com/mattmab` via `openExternal`).

**Hoard Builder** covers wave composition, actor picking, automatic advancement, reusable favorites, and Emergency Clear. Its inline first-run guide remains a separate, dismissible three-step workflow summary above the builder.

Bundled remote-copy overlays in [`docs/data/tutorial_copy.json`](data/tutorial_copy.json) may replace only step titles and body text. Their numeric indices must be updated when the main-tour order changes; selectors, links, and actions always remain local.

## Force replay

From DevTools:

- `msbtResetTutorials()` — clears gating keys and starts the main overview
- Dev launch: `npm start -- --force-tour` (same reset after load)
- `msbtStartMainTutorial({ force: true })`
- `msbtStartLayoutTutorial()`
- `msbtStartQuickMenuSetupTutorial()`
- `msbtStartTabTutorial("boosting")` (any tab id; `"quick-menu"` starts Quick Menu setup)

Or clear `msbt.lastSeenVersion` / `msbt.tutorial.mainSeen` and restart.

## Future (not built)

Per-button hover descriptions / rich tooltips are a possible later idea. Do not implement a hover-tooltip system until explicitly requested.
