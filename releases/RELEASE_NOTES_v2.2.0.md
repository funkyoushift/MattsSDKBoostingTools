### What's new

**v2.2.0** — Live inventory browser in the app and Quick Menu, MSBT Neon theme, catalog refresh, and safer travel.

#### Inventory (Electron + Quick Menu)
- New **Inventory** tab in the Electron app: party player picker, equipped strip, backpack grid, sort (Recent / Rarity / Type / Level / Manufacturer) with direction toggle, category filters, GZO display names, **Send to Game** with separate **Give-to** target and multiplier (1–50)
- New **INV** tab on the in-game **F7 Quick Menu** — same data as Electron, with equipped strip, sort/filter, pagination, item detail, Give-to, multiplier, and serial copy
- Bridge actions: `read_inventory`, equipped/backpack serial reads, and serial delivery with target player

#### Quick Menu polish
- **MSBT Neon (Azzy)** default theme — deep purple dock with mixed neon slot colors
- Esc / cinematic close handling and click fallback (NativeModsMenu-style)
- P1–P4 / PAll player toggles, slot hotkeys, soft clear loot
- Super Dash fix (tick-safe MSBT **V**; Azzy-style **NumPad0** path preserved)

#### Catalog / Matt Editor
- Resynced GZO parts map, GZO codes, and LootLemon references from save-editor.be
- New maintainer tool: `tools/refresh_matt_editor_catalogs.py`

#### Travel / stability
- Prefer station travel; refuse risky raw `servertravel` when safer paths exist

#### Distribution
- **GitHub Releases only for now.** Nexus Mods uploads are paused until Nexus confirms a listing direction that avoids repeated quarantines. Do not run the Nexus sync workflow for this release.

### Upgrade notes

1. Install `MSBT-Installer-v2.2.0.exe` (or extract the portable ZIP).
2. Run **Install / Update SDK Mod** from the app Updates tab.
3. **Fully restart Borderlands 4** so the new Inventory tab and Quick Menu changes load.
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.2.0.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.2.0-win-x64.zip`

**Do not manually download these unless you know why**

- latest.json, latest.yml, *.blockmap
