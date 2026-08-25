### What's new

**v2.8.4**

- **Matt Editor remembers Steam ID and save/profile folders** across launches (the editor iframe no longer forgets them)
- **Opening a .sav from your game SaveGames folder fills Steam ID** from the path, then decrypts
- **Saves actually open** after Choose File / Reopen last save (no second picker, no false “No file selected”)
- **View menu** drops in front of docked panels instead of behind them
- **Give Serial Local** plus Quick Menu picker coverage for Hoard, XYZ auto-name, UVH, and more movement/fog verbs

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.8.4.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.8.4-win-x64.zip`

**Do not manually download these unless you know why**

- `latest.json`, `latest.yml`, `*.blockmap`

### Upgrade notes

1. Open Updates → **Install / Update SDK Mod**, or copy the packaged `.sdkmod` into `sdk_mods`.
2. **Fully restart Borderlands 4** after the SDK install.
3. Do not overwrite `MattsSDKBoostingTools.sdkmod` while the game is open — that breaks inventory reads (`ZipImportError`).
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).
