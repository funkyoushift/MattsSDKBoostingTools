# Matt's SDK Boosting Tools

Matt's SDK Boosting Tools is a Borderlands 4 SDK mod plus a standalone Electron control panel for boosting, serial delivery, item tools, movement tools, travel helpers, and catalog workflows.

**Current release: [v1.2.0](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/v1.2.0)**

Website:
[FunkYouSHiFT.com](https://www.funkyoushift.com/) |
[Tools page](https://www.funkyoushift.com/tools)

## What's New in v1.2.0

Highlights since the v1.0.0 public launch:

- **Serial delivery reliability** — Base85/`@U`/backtick serials stay intact, bad rows are skipped instead of spawning junk, and the bridge queue no longer lets stale commands overwrite an in-progress serial delivery.
- **Copies multiplier (1–50)** — Repeat each selected or pasted serial on Boosting, BL4 Codes, Serial Bookmarks, and the Matt Editor delivery panel.
- **Boost targeting** — Target All Players / Target Non-Host for Quick Max, XP, currency, and inventory actions, plus dedicated UVH Booster controls (Azzy-adapted).
- **BL4 Codes UX** — Sticky delivery side panel while you browse the catalog; larger image-card browsing.
- **Dev Spawner** — Condensed actor rows, collapsible Active Boss list, My Favorites with inline label/note save, and Example List naming.
- **Matt Editor** — Embedded editor polish, part supplements, save/profile YAML fixes, and Copies on the in-editor MSBT delivery panel.
- **Updates / install** — Clearer oak2-mod-manager v0.3 requirement links and fewer false same-version update prompts.

After installing **v1.2.0**, use **Install / Update SDK Mod** (or re-run the installer) and **fully restart Borderlands 4** so the bundled SDK bridge fixes load.

## Required SDK Install

MSBT targets **SDK 03 / oak2-mod-manager v0.3**. Before installing MSBT, update Borderlands 4 to the current SDK/mod manager stack:

[Download oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3)

Older SDK 02 installs are not the target for current MSBT builds.

## Download Latest

Go to the [GitHub Releases page](https://github.com/funkyoushift/MattsSDKBoostingTools/releases) and pick one file:

| What you want | Download this | Notes |
| --- | --- | --- |
| Recommended normal install | `MSBT-Installer-v1.2.0.exe` | Windows installer. Adds app shortcuts and installs the bundled SDK mod plus ActorScriptDeployer into the detected Borderlands 4 `sdk_mods` folder. |
| Manual install / no installer | `MSBT-Portable-v1.2.0-win-x64.zip` | Extract it yourself. Electron app files plus bundled SDK mod/update resources. |
| Source code only | GitHub `Source code (zip)` / `Source code (tar.gz)` | For developers. This is not the ready-to-run app. |

Do **not** manually download `latest.json`, `latest.yml`, or `.blockmap` files. Those are update-system files used by the app/installer.

Older 1.x and beta packages remain available on the Releases page as historical rollback builds.

## Quick Install

1. Install or update to [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).
2. Download the current `MSBT-Installer-v1.2.0.exe` installer from [GitHub Releases](https://github.com/funkyoushift/MattsSDKBoostingTools/releases).
3. Run the installer. It installs the Electron app, `MattsSDKBoostingTools.sdkmod`, and the bundled `ActorScriptDeployer/` dependency.
4. Launch Matt's SDK Boosting Tools. If your Borderlands 4 folder is not in a standard Steam library path, use the Updates tab to browse to `sdk_mods` and run Install / Update SDK Mod.
5. Start Borderlands 4 with the SDK loaded.
6. Use the app's Refresh Status / target controls before sending live actions.

Expected game-side layout after installer or updater:

```text
Borderlands 4/
  sdk_mods/
    ActorScriptDeployer/
      __init__.py
      pyproject.toml
    MattsSDKBoostingTools.sdkmod
```

Manual ZIP users can still extract the portable package and copy `MattsSDKBoostingTools.sdkmod` plus the bundled `ActorScriptDeployer/` folder into `sdk_mods` manually. The Dev Spawner tab needs ActorScriptDeployer.

The current public direction is:

- Keep the original BLImGui panel available when BLImGui is installed.
- Make BLImGui optional.
- Run live game actions through a small SDK bridge.
- Move non-game UI/catalog/serial/build logic into the Electron app.
- Keep the older Tkinter app as legacy/reference code only.
- Package Electron with the bundled SDK mod, ActorScriptDeployer, resources, and a portable Python runtime.

## Package Contents

Current Electron installer/portable packages contain:

```text
Matt's SDK Boosting Tools/
  MattsSDKBoostingTools.exe
  resources/
    sdkmod/
      MattsSDKBoostingTools.sdkmod
    sdkmods/
      ActorScriptDeployer/
    external_app/
    python/
    releases/
```

## Build From Source

Users who do not want to run a prebuilt EXE can build it locally.

Requirements:

- Windows
- Node.js / npm
- Python 3.13

The Electron build bundles a portable Python runtime so normal users do not need Python installed.

Build the Electron app:

```powershell
.\build_electron_beta.ps1
```

Build the Electron Windows installer:

```powershell
.\build_electron_beta.ps1 -Installer
```

Publish release assets to GitHub Releases instead of committing ZIP/EXE files to source:

```powershell
.\publish_github_release.ps1
```

Check the synchronized Nexus Mods file list:

```powershell
.\tools\check_nexus_release.ps1
```

Versioning and asset naming are documented in [VERSIONING.md](VERSIONING.md).
Nexus release sync is documented in [docs/NEXUS_RELEASE_SYNC.md](docs/NEXUS_RELEASE_SYNC.md).

## Repository Layout

```text
mod_extracted/MattsSDKBoostingTools/
  SDK mod source, bridge, backend actions, live game helpers, optional BLImGui UI.

external_app/v22_parts_codes_fixed/
  Standalone Tkinter app, local serial tools, validator, Legit Builder helpers, and resources.

external_app/v22_parts_codes_fixed/matt_editor/
  Vendored Mattmab web editor assets served locally by the standalone app.

external_app/v22_parts_codes_fixed/resources/
  Bundled local resources for BL4 Codes, item pools, travel, legit rules, UI layout, and observed working part options.

docs/
  Developer notes for the BLImGui replacement, packaging, and release checklist.
```

## What Replaced BLImGui

The main user-facing app is now the Electron desktop app. The older Python/Tkinter app remains in the repository as legacy/reference material.

BLImGui-specific code is still kept in the SDK mod as an optional in-game UI. The Electron app does not import BLImGui, `unrealsdk`, `mods_base`, or live SDK modules. It talks to the SDK mod over HTTP for live game actions only.

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

Released under the [PolyForm Noncommercial License 1.0.0](LICENSE).

Commercial use, resale, paid redistribution, or selling packaged builds is not permitted without separate written permission from Matt / FunkYouSHiFT.
