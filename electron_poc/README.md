# MSBT Electron App

This folder contains the Electron desktop app for Matt's SDK Boosting Tools. It replaces the older Tkinter app while keeping the same SDK bridge boundary: Electron talks to the game only through the local MSBT HTTP bridge.

Current Electron priorities are tracked in [../docs/ELECTRON_ROADMAP.md](../docs/ELECTRON_ROADMAP.md).

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
MSBT-Installer-v1.0.0.exe
```

## Updates

The Electron app includes a GitHub Releases update foundation:

- current app/package/SDK/resource versions are visible in the app;
- Check Updates reads the public release manifest and, in packaged builds, asks `electron-updater` to check the GitHub release feed;
- downloads and restart/install are user-triggered;
- there is no embedded GitHub token;
- user data remains in Electron's `app.getPath("userData")` location across updates.

Production update testing requires a GitHub Release containing the Electron builder artifacts such as the installer, `latest.yml`, and block map files. The app does not auto-publish those files. Release/version rules are documented in [../VERSIONING.md](../VERSIONING.md).

## SDK Mod Install

Installer builds bundle the current `MattsSDKBoostingTools.sdkmod` and `ActorScriptDeployer/`. The NSIS installer runs a silent install helper after app install/update so the normal installer and Electron updater both copy the required SDK-side files into the auto-detected Borderlands 4 `sdk_mods` folder.

Because the normal Steam game folder lives under `Program Files (x86)`, installer builds run per-machine and request elevation. If auto-detection fails, the Updates tab still provides an explicit Install / Update SDK Mod action that:

- copies `MattsSDKBoostingTools.sdkmod`;
- copies the bundled `ActorScriptDeployer` folder required by the Dev Spawner tab;
- preserves unrelated mods;
- refuses to run while `Borderlands4.exe` is open;
- supports auto-detecting the common Steam `sdk_mods` folder or pasting another `sdk_mods` path.

BLImGui remains optional. ActorScriptDeployer is bundled as a folder-form SDK mod dependency so Dev Spawner can import it after install/update.

## Current Local Features

- Boosting tab bridge actions.
- Serial Tools local conversion and parts breakdown.
- Serial Bookmarks local browser and bridge delivery.
- BL4 Codes local catalog/search/details/bookmarks/advisory validation and bridge delivery.
- Validator local basic/bulk checks.
- Item Pool and Map Travel local resource browsers with bridge actions.
- Dev Spawner character workflow through the verified SDK 03 bridge path.
- Matt editor hosted inside Electron through the existing Python helper.

## Current Limits

- The Electron build bundles a portable Python runtime for local serial, validator, and Matt editor helper code.
- Installer/update behavior is release-backed, but every new update should still be tested from GitHub Releases before announcing it broadly.
- Some deep editor and Dev Spawner workflows are still being polished in Electron.
