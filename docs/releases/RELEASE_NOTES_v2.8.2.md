### What's new

**v2.8.2**

- **Join / travel crash fix** — joining another player's session no longer scans or writes Unreal objects while the world is unloading
- Fog hide, Instant Holds/Drops, and Combat XP stay quiet during `ClientTravel`; they re-apply after the new map is up
- Quick Menu and camera-tick work skip that window
- BLImGui join-safe pause is armed again when party membership or travel happens

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.8.2.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.8.2-win-x64.zip`

**Do not manually download these unless you know why**

- `latest.json`, `latest.yml`, `*.blockmap`

### Upgrade notes

1. Open Updates → **Install / Update SDK Mod**, or copy the packaged `.sdkmod` into `sdk_mods`.
2. **Fully restart Borderlands 4** after the SDK install.
3. Do not overwrite `MattsSDKBoostingTools.sdkmod` while the game is open — that breaks inventory reads (`ZipImportError`).
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).
