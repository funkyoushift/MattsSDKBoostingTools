# MSBT v2.41.3 - In-app updater repair

Release candidate: publication authorized by Martin on November 13, 2026, but blocked pending the required Windows and Linux/Proton live-game qualification. These notes do not assert publication or completed live testing.

- Repair Windows update installation when the helper previously disappeared without running. The app now confirms that the independent installer helper is ready before exiting; repeated Install clicks share one operation.
- Use one update-check result, show actionable errors, and preserve the Install action for the current verified download.
- Repair the known stale per-user Start Menu shortcut when it points to an older MSBT copy, with identity checks and a rollback backup. Custom shortcuts and existing user data are retained.
- Preserve the SHiFT do-not-delete list saving, menu handling and mobile authorization fixes from 2.41.2. No SDK/PAK gameplay logic changes in this patch.

## Installing the repair

Existing clients whose updater is broken need **one manual installation** of this repair from GitHub. A new release cannot repair the old client's local installation helper before that helper runs. Keep the existing user-data folder; do not uninstall or delete settings to update. Close BL4 before updating bundled game integration, and restart it afterward.

Planned packages:

- Windows installer: `MSBT-Installer-v2.41.3.exe`
- Windows portable: `MSBT-Portable-v2.41.3-win-x64.zip`
- Linux guided installer: `MSBT-Installer-v2.41.3-linux-x64.AppImage`
- Linux portable: `MSBT-Portable-v2.41.3-linux-x64.tar.gz`

GitHub source ZIP/TAR downloads are source archives, not ready-to-run applications. The Android APK is unchanged.

## Verification and remaining limits

On the preceding repair candidate, actual Windows 2.41.1-to-2.41.2 installer trials passed on C: and D: after replacing only the old client's updater module with the repaired module. Automatic restart, two subsequent launches, seeded preferences/bookmarks and exact target payload checks passed. This is not an unmodified published Windows client pass. Unmodified published Linux AppImage and portable 2.41.1-to-2.41.2 updates passed on Ubuntu 22.04 with seeded data preservation.

Both desktop platforms passed native package checks at the preceding candidate source commit. The newly versioned 2.41.3 packages require their own exact-source receipts; those results will be recorded separately. Fixtures do not establish real protected-list or guest-save preservation.

Live BL4/Proton qualification tied to this candidate is incomplete on both platforms. No Linux BL4 host is currently available. Ubuntu 26 sandbox startup failed in earlier qualification. Arbitrarily long Windows installation paths and human standard-user UAC/cancellation remain unqualified. The required publication gate must pass before this candidate is released; disclosure alone does not waive it.
