### What's new

**v2.2.1** — Panel layout editor, View menu + tutorials, and gameplay polish.

#### Electron layout & View menu
- Drag, resize, overlap, and stack panels into tabs on every main content tab (GridStack)
- Compact to fill gaps; collapse/hide panels and restore from **Panels** or **View → Panels**
- **View** menu: text size (85%–140%), show/hide/reorder main nav tabs, layout reset
- Layouts persist per tab in localStorage

#### Tutorials
- First-run / post-update app overview with optional deep-dives
- Full **Layout editor** and **Quick Menu setup** walkthroughs
- Per-tab **Walkthrough** buttons on layout tabs

#### Matt Editor
- Editor host fills the available panel space more cleanly

#### SDK / Quick Menu / Dev Spawner
- Infinite Jump restored with a calmer camera path
- Quick Menu force-closes on map travel
- ActorScriptDeployer auto-clears spawn batches after a 60s window
- Dev Spawner back to the stable three-column layout

#### Docs / repo
- Release metadata and related folders nested under `docs/` / `tools/` (build + publish paths updated)

### Upgrade notes

1. Install `MSBT-Installer-v2.2.1.exe` (or extract the portable ZIP).
2. Run **Install / Update SDK Mod** from the app Updates tab.
3. **Fully restart Borderlands 4** so Infinite Jump, travel close, and ASD batch clear load.
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.2.1.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.2.1-win-x64.zip`

**Do not manually download these unless you know why**

- latest.json, latest.yml, *.blockmap
