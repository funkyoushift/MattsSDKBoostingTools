### What's new

**v2.8.0**

- **Spawn Near** — item pools and Dev Spawner can spawn at you, the named player, another party member, or the nearest NPC
- **Item Pool pacing** — delay, items per tick, and spit direction (forward / left / right / back / around)
- **Challenges** — Ctrl/Shift-select several, then Complete Selected as one bulk run
- **Empty Backpack undo** — Empty captures backpack `@U` serials; Undo gives them to the current target; Clear Deleted Backpack Memory drops the snapshot
- **Smoother frames** — camera-tick work shares one gated pump instead of six Python hooks on every camera modifier
- **Safer SDK installs** — `.sdkmod` is packed with Python zipfile so oak2 zipimport stays valid. Do not replace the file while Borderlands 4 is running
- **Debug Camera** — disable, pull cam to target, copy location, speed, and distance
- **Dev Spawner** — Interactive Objects fold (show IOs, spawn Lost Loot, activate last)

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.8.0.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.8.0-win-x64.zip`

**Do not manually download these unless you know why**

- `latest.json`, `latest.yml`, `*.blockmap`

### Upgrade notes

1. Open Updates → **Install / Update SDK Mod**, or copy the packaged `.sdkmod` into `sdk_mods`.
2. **Fully restart Borderlands 4** after the SDK install.
3. Do not overwrite `MattsSDKBoostingTools.sdkmod` while the game is open — that breaks inventory reads (`ZipImportError`).
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).
