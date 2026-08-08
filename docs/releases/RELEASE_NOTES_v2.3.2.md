### What's new

**v2.3.2** — Remote data catalogs, walkthrough fixes, Infinite Jump / Super Dash harden, Layout Builder QM export.

#### Remote data catalogs
- Data channel (`data-v*`) hotfixes for JSON catalogs without a full app update
- Lootlemon serial truncation fixes in the seed / catalog pipeline

#### Walkthrough
- Spotlights work when layout panels are hidden
- Coach card stays on-screen with a sticky Next footer

#### Movement harden
- Infinite Jump: conditional writes, safer caches, less lag
- Super Dash: game-thread only execution to reduce stack crash risk

#### Layout Builder
- Quick Menu export path for Layout Builder presets

#### Upgrade notes

1. Install `MSBT-Installer-v2.3.2.exe` (or extract the portable ZIP).
2. Run **Install / Update SDK Mod** from the app Updates tab.
3. **Fully restart Borderlands 4** so the bridge and live actions load.
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.3.2.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.3.2-win-x64.zip`

**Do not manually download these unless you know why**

- latest.json, latest.yml, *.blockmap
