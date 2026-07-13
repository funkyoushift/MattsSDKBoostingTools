# Public Repository Checklist

Use this before pushing the repository public or posting it in Discord.

## Required Before Publishing

- Choose a license.
- Confirm no local personal paths are required at runtime.
- Confirm no logs, screenshots, private Discord exports, or local Excel files are tracked.
- Confirm generated folders are ignored: `build/`, `dist/`, `MSBT_External_Beta/`.
- Confirm generated packages are ignored: `*.zip`, `*.sdkmod`.
- Confirm user data is ignored:
  - `external_app/v22_parts_codes_fixed/resources/user_serial_bookmarks.json`
  - `external_app/v22_parts_codes_fixed/resources/MattsSDKBoostingTools_gzo_codes.json`
- Confirm the external app does not import SDK/game modules.
- Confirm the SDK bridge starts without BLImGui installed.

## Recommended GitHub Release Files

Upload these to a GitHub Release instead of committing them to source:

- `MattsSDKBoostingTools-Setup-v<version>.exe`
- `MattsSDKBoostingTools-Portable-v<version>.zip`
- checksums for release files

The normal public beta download link should point users to the release page:

```text
https://github.com/funkyoushift/MattsSDKBoostingTools/releases
```

## Smoke Tests

External app:

- app opens from EXE
- app opens from launcher BAT
- Serial Tools works offline
- Serial Bookmarks load/save works
- BL4 Codes local catalog loads
- Validator works offline
- Legit Builder can build Base85 output

SDK mod:

- mod loads with BLImGui installed
- mod loads with BLImGui absent
- `/status` bridge endpoint works
- `msbt_external_app` launches the external app
- live actions still route through the bridge

Multiplayer:

- Give Selected
- Give All
- Give Non-Host
- leveling another player
- auto backpack/bank checkbox
- item pool spawn
- map travel
- movement presets/reset/infinite jump

## Discord Post Template

```text
Matt's SDK Boosting Tools public beta is available.

Download:
https://github.com/funkyoushift/MattsSDKBoostingTools/releases

Install:
1. Install or update to oak2-mod-manager v0.3.
2. Download the current MattsSDKBoostingTools-Setup installer from GitHub Releases.
3. Run the installer.
4. Use the app Updates tab to install/update the SDK mod.

Please report:
- host or non-host
- lobby size
- exact button clicked
- selected target
- who received the effect
- screenshot/log if possible
```
