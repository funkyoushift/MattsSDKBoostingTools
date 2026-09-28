# MSBT v2.17.9

Fixes Setup failing with “The process cannot access the file because it is being used by another process” during an in-app update. The update helper now launches outside the app folder. Setup also moves its working directory outside that folder before replacing the app, avoiding the self-lock even when launched by an older version.

Installer regression tests cover an inherited app working directory, rollback, archive verification and version protection. Includes all v2.17.8 delivery, persistent password unlock, and duplicate-preserving Undo backup changes.

## Updating from an older version

If the old in-app updater already shows this error, close that Setup window and download/run **MSBT-Setup.exe** from this release. Older installed apps carry their older updater, so they cannot receive this fix until the new version is installed.

The versioned installer also includes the AFK SHiFT PAK and game-integration installer. With reusable Setup or portable installs, use Settings > Install / update SDK mod with Borderlands closed to update game files. Android remains v1.4.2, unchanged.

## Known limitation

Guest backpack clearing may still fail to persist after rejoining. This release fixes installation, not that game-save issue. See v2.17.8 notes for delivery validation and remaining inventory limitations.
