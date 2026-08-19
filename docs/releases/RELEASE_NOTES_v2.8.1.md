### What's new

**v2.8.1**

- **Spawn Black Market** now uses Squiggs' working spawn (`oak_dual` twice) so Maurice's shop actually appears
- **Empty Backpack undo** restores equipped weapons as well as backpack items
- Undo no longer brings back leftover items from an earlier empty — each empty replaces that player's snapshot, and undo clears it after restore

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.8.1.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.8.1-win-x64.zip`

**Do not manually download these unless you know why**

- `latest.json`, `latest.yml`, `*.blockmap`

### Upgrade notes

1. Open Updates → **Install / Update SDK Mod**, or copy the packaged `.sdkmod` into `sdk_mods`.
2. **Fully restart Borderlands 4** after the SDK install.
3. Do not overwrite `MattsSDKBoostingTools.sdkmod` while the game is open — that breaks inventory reads (`ZipImportError`).
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).
