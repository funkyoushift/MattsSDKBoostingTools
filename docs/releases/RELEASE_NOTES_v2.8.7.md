### What's new

**v2.8.7**

- **Matt Editor and Dev Spawner work again** after the v2.8.6 Inventory send-strip layout leaked into the shared tab shell
- **Inventory Send to Game** stays pinned at the bottom of Inventory (Select All Filtered still works)
- Guard test now visits every main tab and fails if Editor/Spawner collapse after opening Inventory

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.8.7.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.8.7-win-x64.zip`

**Do not manually download these unless you know why**

- `latest.json`, `latest.yml`, `*.blockmap`

### Upgrade notes

1. Open Updates → **Install / Update SDK Mod**, or copy the packaged `.sdkmod` into `sdk_mods`.
2. **Fully restart Borderlands 4** after the SDK install.
3. Do not overwrite `MattsSDKBoostingTools.sdkmod` while the game is open — that breaks inventory reads (`ZipImportError`).
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).
