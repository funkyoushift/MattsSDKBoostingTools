# MSBT 2.40.0 — Windows and Linux

One release now includes both desktop platforms. The app selects Windows or Linux downloads using GitHub release metadata and verifies update packages before installation. Linux AppImage updates replace the same executable; portable-folder updates keep the same launcher path and retain a previous-version backup. Windows downloads the verified matching NSIS installer and installs into the running application’s existing directory, including custom and portable locations; Windows may request administrator approval.

## Six release items

| Platform | Installer / single app | Portable folder | Source |
|---|---|---|---|
| Windows x64 | MSBT-Installer-v2.40.0.exe | MSBT-Portable-v2.40.0-win-x64.zip | GitHub Source code ZIP |
| Linux x64 | Single-file app: MSBT-Installer-v2.40.0-linux-x64.AppImage | Portable folder: MSBT-Portable-v2.40.0-linux-x64.tar.gz | GitHub Source code TAR.GZ |

The two source archives contain the same cross-platform source in different formats; source is not a ready-to-run app. Exactly four binaries are uploaded; GitHub adds its two source links. Updater metadata, build logs and separate SDK files are not extra downloads: the full SDK and runtime are bundled in each app. Android 1.6.6 and the standalone selector remain available from [v2.39.9](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/v2.39.9).

## Install and update

**Windows:** run the EXE installer, or extract the ZIP and launch the app.

**Linux — easiest option: single-file app (AppImage)**

1. Download `MSBT-Installer-v2.40.0-linux-x64.AppImage`.
2. Right-click it → **Properties → Permissions → Allow executing as a program** (wording varies by desktop).
3. Double-click it to run. Keep the file somewhere permanent, such as an Applications folder.

AppImage bundles the app and its runtime into one executable file. It runs directly; it does not use your distribution’s package manager. If your desktop cannot mount it, run it from a terminal with `--appimage-extract-and-run`.

**Linux — portable folder:** download the `.tar.gz`, extract it, and run `msbt` inside the extracted folder. Node.js and Python are included in both Linux options. See the included Linux README for Proton SDK loading and `MSBT_SAVE_ROOT`.

Close Borderlands 4 before replacing its SDK files or applying a desktop update that also installs game components. Linux alpha users install this unified build once; subsequent updates use the new platform-aware updater. Very old Windows clients using the retired electron-updater metadata path should install this EXE once; older bundled Setup clients select the Windows ZIP directly, but custom-location users should run the new installer once to avoid the old helper’s separate installation location.

## Validation and limits

The Linux preview passed actual Steam/Proton startup, exact loaded SDK identity, live bridge and reversible third-person checks. The user confirmed F7/panel/camera checks and additional hands-on controls looked good. The unified desktop adds verified platform downloads, stable-path activation and rollback tests. Both Linux formats include Python and PyYAML. Windows installation/package and Linux package verification results are recorded with this release's build receipts.

Broad gameplay, multiplayer guest/save persistence, exhaustive mission completion and exact item-card parity are not newly claimed. Existing v2.39.9 game qualification limits remain.

## Verified packages

Windows CI completed the native handoff fixture, package audits, silent NSIS install, installed payload hashes, Python/YAML and installed smoke checks. Linux AppImage direct/extraction startup, relocated portable startup, bundled Python imports and packaged/source matching passed. UAC interaction itself is not automated by the fixture.

SHA-256 (also available in GitHub asset details):

```text
3a5614e6bb4ab712db2362801addaea17511ce39099bc8bebba7cc74396779b1  MSBT-Installer-v2.40.0-linux-x64.AppImage
98312afb842aadb910b2a4cb63cf55644c110abf32439de671517f6c048130c6  MSBT-Installer-v2.40.0.exe
1193877d65d086947dda2ed464b5fb62234aefba47f3867c0542493a38a1ac2c  MSBT-Portable-v2.40.0-linux-x64.tar.gz
d687a0b3d5548c1e1ff96380e194d47d8d89e49d78d8aaf39661cb2a4b25d0d8  MSBT-Portable-v2.40.0-win-x64.zip
```
