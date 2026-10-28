# MSBT 2.40.0 — Windows and Linux

One release now includes both desktop platforms. The app selects Windows or Linux downloads using GitHub release metadata and verifies update packages before installation. Linux AppImage updates replace the same executable; portable-folder updates keep the same launcher path and retain a previous-version backup. Windows keeps its bundled Setup updater and verified Windows portable payload.

## Six release items

| Platform | Installer / single app | Portable folder | Source |
|---|---|---|---|
| Windows x64 | MSBT-Installer-v2.40.0.exe | MSBT-Portable-v2.40.0-win-x64.zip | GitHub Source code ZIP |
| Linux x64 | MSBT-Installer-v2.40.0-linux-x64.AppImage | MSBT-Portable-v2.40.0-linux-x64.tar.gz | GitHub Source code TAR.GZ |

The two source archives contain the same cross-platform source in different formats; source is not a ready-to-run app. Exactly four binaries are uploaded; GitHub adds its two source links. Updater metadata, build logs and separate SDK files are not extra downloads: the full SDK and runtime are bundled in each app. Android 1.6.6 and the standalone selector remain available from [v2.39.9](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/v2.39.9).

## Install and update

Windows: run the EXE or extract the ZIP. Linux: mark the AppImage executable and launch it, or extract the TAR.GZ and run ./msbt. If FUSE mounting is unavailable, use AppImage --appimage-extract-and-run. See the included Linux README for Proton SDK loading and MSBT_SAVE_ROOT.

Close Borderlands 4 before replacing its SDK files or applying a desktop update that also installs game components. Linux alpha users install this unified build once; subsequent updates use the new platform-aware updater. Very old Windows clients using the retired electron-updater metadata path should install this EXE once; current bundled Setup clients select the Windows ZIP directly.

## Validation and limits

The Linux preview passed actual Steam/Proton startup, exact loaded SDK identity, live bridge and reversible third-person checks. The user confirmed F7/panel/camera checks and additional hands-on controls looked good. The unified desktop adds verified platform downloads, stable-path activation and rollback tests. Both Linux formats include Python and PyYAML. Windows installation/package and Linux package verification results are recorded with this release's build receipts.

Broad gameplay, multiplayer guest/save persistence, exhaustive mission completion and exact item-card parity are not newly claimed. Existing v2.39.9 game qualification limits remain.
