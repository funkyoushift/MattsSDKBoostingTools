# Build and Package Guide

Prefer the **Electron** app for shipping. Tkinter packaging is legacy and lives under [`docs/reference/legacy_tkinter/`](reference/legacy_tkinter/).

Repo layout: [`PROJECT_MAP.md`](PROJECT_MAP.md). Versioning: [`VERSIONING.md`](VERSIONING.md).

## Build The Electron App (recommended)

From the repository root:

```powershell
.\tools\build_electron_beta.ps1 -Installer
```

This builds the installer, portable ZIP, and packages the bundled SDK mod / ActorScriptDeployer resources used by the Updates tab and NSIS install helper.

Output typically lands under `dist_electron/` (gitignored).

## Build The SDK Mod Package

From the repository root:

```powershell
.\tools\build_sdkmod.ps1
```

Output:

```text
MattsSDKBoostingTools.sdkmod
```

Keep the SDK `__version__` / `pyproject.toml` SemVer aligned with `electron_poc/package.json` when cutting a public release.

## Publish A GitHub Release

After building installer + portable assets:

```powershell
.\tools\publish_github_release.ps1
```

Or push a matching `v*` tag and let `.github/workflows/electron-release.yml` publish.

**Important:** `tools/publish_github_release.ps1` and CI append download-count badges to the release body. If you later run `gh release edit --notes-file` with notes-only content, you will wipe those badges — re-run the publisher notes assembly or append the badge block again.

## Build The Legacy Tkinter EXE (reference only)

```powershell
.\docs\reference\legacy_tkinter\build_external_exe.ps1
.\docs\reference\legacy_tkinter\package_external_beta.ps1
```

Output (gitignored):

```text
dist/MattsBoostingToolsExternal/...
MSBT_External_Beta/
MattsSDKBoostingTools-Legacy-Tkinter-Portable-v<version>.zip
```

If Python is not found:

```powershell
$env:MSBT_PYTHON = "C:\Path\To\python.exe"
```

## Public Release Recommendation

Do not commit generated EXE/ZIP files to normal source history. Put them on GitHub Releases.

The Electron NSIS installer bundles the app, `MattsSDKBoostingTools.sdkmod`, and folder-form `ActorScriptDeployer/`. Non-standard game installs can still be repaired from the app's Updates tab.

Example assets:

```text
MSBT-Installer-v2.2.1.exe
MSBT-Portable-v2.2.1-win-x64.zip
```

## Preflight Syntax Checks

```powershell
python -m py_compile .\mod_extracted\MattsSDKBoostingTools\backend_actions.py .\mod_extracted\MattsSDKBoostingTools\external_bridge.py .\mod_extracted\MattsSDKBoostingTools\__init__.py .\mod_extracted\MattsSDKBoostingTools\quick_menu.py
```
