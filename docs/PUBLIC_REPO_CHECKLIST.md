# Public Repository Checklist

Use this before pushing the repository public or posting it in Discord.

## Required Before Publishing

- Choose a license.
- Confirm no local personal paths are required at runtime.
- Confirm no logs, private Discord exports, or local Excel files are tracked.
- Confirm generated folders are ignored: `build/`, `dist/`, `dist_electron/`, `MSBT_External_Beta/`.
- Confirm generated packages are ignored: `*.zip`, `*.sdkmod` (except intentional `releases/` metadata).
- Confirm probe/staging dirs are ignored: `_loot_probe_*`, `_explore_*`, `_install_stage/`, `_pack_stage_*`, etc.
- Confirm user data is ignored under `external_app/v22_parts_codes_fixed/resources/`.
- Confirm Electron helpers under `external_app/` do not import SDK/game modules.
- Confirm the SDK bridge starts without BLImGui installed (`/status` + `tools/tests/test_quick_menu_no_blimgui.py`).

## Recommended GitHub Release Files

Upload these to a GitHub Release instead of committing them to source:

- `MSBT-Installer-v<version>.exe`
- `MSBT-Portable-v<version>-win-x64.zip`
- checksums for release files (optional)

Do **not** commit installers or portable ZIPs into `releases/` in git. Keep `releases/latest.json` + `RELEASE_NOTES_v*.md` (+ Discord media if desired).

Public download page:

```text
https://github.com/funkyoushift/MattsSDKBoostingTools/releases
```

## Smoke Tests

Electron app:

- app opens from installer / portable build
- Serial Tools works offline
- Serial Bookmarks load/save works
- BL4 Codes local catalog loads
- Matt Editor host loads
- Updates tab can detect `sdk_mods` and Install / Update SDK Mod
- Quick Menu editor loads; F7 Quick Menu works in-game after mod install

SDK mod:

- mod loads with BLImGui installed
- mod loads with BLImGui absent
- `/status` bridge endpoint works
- live actions route through the bridge / `backend_actions`
- Quick Menu (F7) opens without BLImGui

Multiplayer (spot-check):

- Give Selected / All / Non-Host
- leveling another player
- inventory size helpers
- item pool spawn
- map travel
- movement presets / infinite jump

## Discord Post Template

```text
Matt's SDK Boosting Tools is available.

Download:
https://github.com/funkyoushift/MattsSDKBoostingTools/releases

Install:
1. Install or update to oak2-mod-manager v0.3.
2. Download the current MSBT-Installer from GitHub Releases.
3. Run the installer.
4. Use the app Updates tab to install/update the SDK mod.
5. Fully restart Borderlands 4.

Please report:
- host or non-host
- lobby size
- exact button clicked
- selected target
- who received the effect
- screenshot/log if possible
```
