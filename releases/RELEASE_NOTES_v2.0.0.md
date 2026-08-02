### What's new

**v2.0.0** — native in-game Quick Menu launch, BLImGui-optional bridge, and full external Quick Menu editor.

#### Native Quick Menu (F7)
- In-game UMG Quick Menu with up to 5 pages × 12 slots
- Pin Last Command, Repeat Last Drop, and optional Lock Player
- Target / Refresh party from menu chrome
- Edit mode: assign, clear, Swap With…, Reset Page / Reset All
- F6 unstuck restores GameOnly input if the cursor sticks
- Borderlands-styled right-side dock with opacity control
- Serial delivery start/finish toasts while drops run
- Works without BLImGui; BLImGui remains an optional fallback panel only

#### External Quick Menu editor
- New ★ Quick Menu tab in the Electron app
- Live layout sync through `GET /quick_menu`
- `+ QM` buttons on supported Boosting, Travel, Movement, Rarity, Spawnables, Dev Spawner, and Debug actions
- Gold `+ QM Selected / All / Non-Host` on Serial Bookmarks and BL4 Codes delivery
- Electron serial-delivery progress bar for chunked batches

#### Architecture
- Shared bridge-safe action registry and `backend_actions` handlers
- External bridge no longer depends on BLImGui for live commands
- Vault Card 4 support from v1.2.1 retained

### Upgrade notes

1. Install `MSBT-Installer-v2.0.0.exe` (or extract the portable ZIP).
2. Run **Install / Update SDK Mod** from the app Updates tab.
3. **Fully restart Borderlands 4** so the new SDK bridge and Quick Menu load.
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).
5. BLImGui is optional. Quick Menu and the external bridge do not require it.

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.0.0.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.0.0-win-x64.zip`

**Do not manually download these unless you know why**

- latest.json, latest.yml, *.blockmap

**Source code**

GitHub's automatic Source code ZIP/TAR files are for developers. They are not the ready-to-run app.
