# Matt's SDK Boosting Tools

Matt's SDK Boosting Tools is a Borderlands 4 SDK mod plus a standalone external control panel for boosting, serial delivery, item tools, movement tools, travel helpers, and catalog workflows.

The current public direction is:

- Keep the original BLImGui panel available when BLImGui is installed.
- Make BLImGui optional.
- Run live game actions through a small SDK bridge.
- Move non-game UI/catalog/serial/build logic into a standalone Tkinter app.
- Package the standalone app as an EXE for users who do not have Python installed.

## Beta Install

For normal users, use the packaged release zip from GitHub Releases.

Expected install layout inside the Borderlands 4 `sdk_mods` folder:

```text
sdk_mods/
  MattsSDKBoostingTools.sdkmod
  MattsSDKBoostingTools_external/
    MattsBoostingToolsExternal.exe
    resources/
```

Launch the external app with either:

- `Launch_MSBT_External_App.bat`
- the in-game SDK command `msbt_external_app`
- `MattsBoostingToolsExternal.exe` directly

Python is not required when the packaged EXE is used.

## Build From Source

Users who do not want to run a prebuilt EXE can build it locally.

Requirements:

- Windows
- Python with Tkinter available
- PyInstaller

Build the external app:

```powershell
.\build_external_exe.ps1
```

Build the beta package:

```powershell
.\package_external_beta.ps1
```

The package script creates:

```text
MSBT_External_Beta/
MSBT_External_Beta.zip
```

## Repository Layout

```text
mod_extracted/MattsSDKBoostingTools/
  SDK mod source, bridge, backend actions, live game helpers, optional BLImGui UI.

external_app/v22_parts_codes_fixed/
  Standalone Tkinter app, local serial tools, validator, Legit Builder helpers, and resources.

external_app/v22_parts_codes_fixed/resources/
  Bundled local resources for BL4 Codes, item pools, travel, legit rules, UI layout, and observed working part options.

docs/
  Developer notes for the BLImGui replacement, packaging, and release checklist.
```

## What Replaced BLImGui

The standalone app is not a web app. It is a Python/Tkinter renderer of the working BLImGui workflows.

BLImGui-specific code is still kept in the SDK mod as an optional in-game UI. The external app does not import BLImGui, `unrealsdk`, `mods_base`, or live SDK modules. It talks to the SDK mod over HTTP for live game actions only.

More detail: [BLImGui Replacement Architecture](docs/BLIMGUI_REPLACEMENT_ARCHITECTURE.md).

## Live Game Boundary

The external app owns local tooling such as:

- serial conversion
- serial parts breakdown
- BL4 Codes catalog search/details/bookmarks
- Validator
- Legit Builder UI state, filtering, validation, and serial generation
- item pool and travel browsing

The SDK bridge owns live game actions such as:

- giving serials to selected/all/non-host players
- currency, XP, SDU, inventory size changes
- item pool spawning
- map/station travel
- movement/debug/dev commands
- chest, bank, shiny, and live player actions

## Known Multiplayer Note

Selected-player serial delivery currently uses the game's all-player reward package path, then patches the intended target package. This is a game/API workaround and can create extra base reward behavior for non-target players. Do not delete non-target reward mail unless the package can be identified with high confidence.

## Credits

Created by Matt and contributors.

Special thanks to testers and SDK modders who helped verify multiplayer behavior, item data, serial tools, and BLImGui parity.

This project is not affiliated with Gearbox, 2K, or the Borderlands franchise owners.

## License

A public license has not been selected yet. Choose one before publishing the repository if you want others to legally fork, reuse, or redistribute the code.
