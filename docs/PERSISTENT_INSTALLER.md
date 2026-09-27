# Reusable MSBT installer

`MSBT-Setup.exe` is a standalone Windows x64 installer. Keep the same file and run
it whenever you want to install, repair, or update MSBT. It asks GitHub for the
latest published stable release, selects that release's portable ZIP, checks its
published byte count and SHA-256 digest, and installs the app. No separately
installed .NET runtime, Python, Node, GitHub CLI, or token is required.

The installer itself is unversioned. App payloads still have versions. Rebuilding
the setup program is only necessary when its code or bundled runtime changes;
it contains no fixed app version or payload URL.

## Installation and updates

- Install location: `%LOCALAPPDATA%\Programs\MSBT\app`.
- The retained previous app is in the adjacent `previous` directory. The downloaded
  ZIP stays in `cache` for verified retries. These folders are replaced by later updates.
- Setup adds desktop and Start menu shortcuts and a Windows Installed Apps entry.
- Saved Electron settings remain in their existing user data folder.
- Game files are not modified by Setup. Open MSBT and use its bundled SDK mod
  installation action to install or refresh game mods. Setup never stops a game.
- Uninstall removes the managed app, cache, previous app and its own shortcuts;
  saved settings, game mods and the reusable installer are kept.
- Existing NSIS installations are left intact. The new per-user installation uses
  the same app settings. Its shortcuts point to the new app. Do not uninstall a
  legacy copy during a running update; rerun Setup if an old uninstaller removes
  shared shortcuts.

The new Electron integration uses Setup for its existing update controls: Download
Update prepares a verified ZIP, and Restart to Install runs Setup outside the app
directory and waits for that specific MSBT process to exit. It never kills processes.
The setup window offers Open MSBT after completion. A new app package containing
this integration must be shipped before existing users get these controls.
Releases before v2.17.5 retain their previous updater. Version 2.17.5 bundles Setup.

Failed downloads leave the installed app untouched. Extraction rejects traversal,
links, duplicate paths and malformed packages. A failed directory replacement
restores the previous app. An interrupted swap is recovered on the next run.
Setup refuses unowned app folders, concurrent installers and automatic downgrades.
The EXE is not Authenticode signed; Windows may show an unsigned-app prompt.

## Build and test

From the repository root, using .NET SDK 8 or newer:

```powershell
.\tools\build_persistent_installer.ps1
node .\electron_poc\test_persistent_updater.js
dotnet run --project .\installer\Tests.csproj --configuration Release -- --live
```

The first command runs isolated installer tests and builds `dist_setup/MSBT-Setup.exe`.
It also copies the same executable into Electron's packaging resources. The live
test downloads the official latest ZIP to a disposable folder, verifies and installs
it twice, and runs the packaged app's `--smoke` check. It does not register shortcuts,
change the current installation, install game mods or start the game.

`tools/build_electron_beta.ps1` builds Setup before packaging Electron. Without
`-Installer`, it builds the portable payload without producing a versioned NSIS
installer. `-Installer` additionally produces the old installer for compatibility.

## Release contract

Each public stable release needs exactly one
`MSBT-Portable-v<VERSION>-win-x64.zip`, containing the same-named root directory.
The release tag, portable name and bundled `resources/releases/latest.json`
`package_version` must agree. GitHub must report the asset's SHA-256 digest; setup
fails closed if it is absent. Required files include the Electron executable and
app archive, embedded Python, SDK mod and ActorScriptDeployer.

Both existing publishers now include `MSBT-Setup.exe`. Re-uploading the unchanged
binary keeps the future `releases/latest/download/MSBT-Setup.exe` link usable.
The existing versioned NSIS assets and update metadata remain in those publishers
during migration so older installations can still update. New Setup users only
consume the portable ZIP. Retiring legacy updater assets is a separate rollout
decision after users receive the new integrated app.

First bundled with MSBT v2.17.5.
