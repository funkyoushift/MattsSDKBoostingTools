# MSBT Electron Beta

This folder contains the Electron beta shell for Matt's SDK Boosting Tools. The goal is to replace the older Tkinter beta app while keeping the same SDK bridge boundary: Electron talks to the game only through the local MSBT HTTP bridge.

Current beta replacement priorities are tracked in [../docs/ELECTRON_BETA_ROADMAP.md](../docs/ELECTRON_BETA_ROADMAP.md).

## Run From Source

From this folder:

```powershell
npm.cmd install
npm.cmd run smoke
npm.cmd start
```

If Electron says it failed to install correctly, approve its install script and rebuild it:

```powershell
npm.cmd approve-scripts electron
npm.cmd rebuild electron
```

## Build Locally

From the repository root:

```powershell
.\build_electron_beta.ps1
```

This rebuilds `MattsSDKBoostingTools.sdkmod`, runs Electron syntax checks, and creates an unpacked Electron app under `dist_electron`.

To build the Windows installer:

```powershell
.\build_electron_beta.ps1 -Installer
```

Installer builds use `electron-builder` with NSIS. They do not publish to GitHub automatically.

Installer filenames are derived from `electron_poc/package.json`, for example:

```text
MattsSDKBoostingTools-Setup-v0.2.3-beta.1.exe
```

## Updates

The Electron beta includes a GitHub Releases update foundation:

- current app/package/SDK/resource versions are visible in the app;
- Check Updates reads the public release manifest and, in packaged builds, asks `electron-updater` to check the GitHub release feed;
- downloads and restart/install are user-triggered;
- there is no embedded GitHub token;
- user data remains in Electron's `app.getPath("userData")` location across updates.

Production update testing requires a GitHub Release containing the Electron builder artifacts such as the installer, `latest.yml`, and block map files. The app does not auto-publish those files. Release/version rules are documented in [../VERSIONING.md](../VERSIONING.md).

## SDK Mod Install

Installer builds bundle the current `MattsSDKBoostingTools.sdkmod`. The Updates tab provides an explicit Install / Update SDK Mod action that:

- copies `MattsSDKBoostingTools.sdkmod`;
- copies the bundled `ActorScriptDeployer` folder required by the Dev Spawner tab;
- preserves unrelated mods;
- refuses to run while `Borderlands4.exe` is open;
- supports auto-detecting the common Steam `sdk_mods` folder or pasting another `sdk_mods` path.

BLImGui remains optional. ActorScriptDeployer is bundled as a folder-form SDK mod dependency so Dev Spawner can import it after the SDK install/update action runs.

## Current Local Features

- Boosting tab bridge actions.
- Serial Tools local conversion and parts breakdown.
- Serial Bookmarks local browser and bridge delivery.
- BL4 Codes local catalog/search/details/bookmarks/advisory validation and bridge delivery.
- Validator local basic/bulk checks.
- Item Pool and Map Travel local resource browsers with bridge actions.
- Dev Spawner character workflow through the verified SDK 03 bridge path.
- Matt editor hosted inside Electron through the existing Python helper.

## Known Beta Limits

- The Electron build bundles a portable Python runtime for local serial, validator, and Matt editor helper code.
- The Electron installer/update path is a foundation, not a published release flow. Do not claim update delivery is production-proven until it is tested against a controlled GitHub Release.
- Electron is still catching up to every Tkinter tab and workflow.
