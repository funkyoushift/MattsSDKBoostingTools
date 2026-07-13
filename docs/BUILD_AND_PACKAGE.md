# Build and Package Guide

This guide is for developers and users who want to build the standalone EXE themselves.

## Build The External EXE

From the repository root:

```powershell
.\build_external_exe.ps1
```

The script:

- finds Python
- checks that PyInstaller is installed
- builds a one-folder Tkinter app
- copies `resources/` beside the EXE
- verifies Tkinter runtime files are present

Output:

```text
dist/MattsBoostingToolsExternal/MattsBoostingToolsExternal.exe
```

If Python is not found, set:

```powershell
$env:MSBT_PYTHON = "C:\Path\To\python.exe"
```

Install PyInstaller if needed:

```powershell
python -m pip install pyinstaller
```

## Build The SDK Mod Package

From the repository root:

```powershell
.\build_sdkmod.ps1
```

Output:

```text
MattsSDKBoostingTools.sdkmod
```

## Build The Portable Package

Build the EXE first, then run:

```powershell
.\package_external_beta.ps1
```

Output:

```text
MSBT_External_Beta/
MattsSDKBoostingTools-Portable-v<version>.zip
releases/latest.json
```

The package contains:

```text
MSBT_External_Beta/
  Launch_MSBT_External_App.bat
  MattsSDKBoostingTools.sdkmod
  MattsSDKBoostingTools_external/
    MattsBoostingToolsExternal.exe
    resources/
```

## Source Mode

For development, the external app can also run from source:

```powershell
python .\external_app\v22_parts_codes_fixed\matts_external_app_v22.py
```

Source mode requires Python and Tkinter.

## Public Release Recommendation

Do not commit generated EXE/ZIP files to normal source history. Put them on GitHub Releases, then keep source and build scripts in the repository.

After building the installer and portable package, upload them to GitHub Releases:

```powershell
.\publish_github_release.ps1
```

Public releases should use semantic tags and asset names, for example:

```text
https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/v0.2.3-beta.1
MattsSDKBoostingTools-Setup-v0.2.3-beta.1.exe
MattsSDKBoostingTools-Portable-v0.2.3-beta.1.zip
```

See `VERSIONING.md` for the release naming rules.

Before publishing a release, run:

```powershell
python -m py_compile .\external_app\v22_parts_codes_fixed\matts_external_app_v22.py
python -m py_compile .\mod_extracted\MattsSDKBoostingTools\backend_actions.py .\mod_extracted\MattsSDKBoostingTools\external_bridge.py .\mod_extracted\MattsSDKBoostingTools\__init__.py
```
