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

Both newly versioned 2.41.3 desktop platforms and the aggregate package gate passed [CI43357300583](https://github.com/funkyoushift/MattsSDKBoostingTools/actions/runs/43357300583) at source `dbedd839a2fd64e1a978fe311cfd96a55be87d2c`. All four locally downloaded packages match the exact CI sizes and SHA256 receipts. Windows actual installation and Linux per-user installation passed. Fixtures do not establish real protected-list or guest-save preservation.

Live BL4/Proton qualification tied to this candidate is incomplete on both platforms. No Linux BL4 host is currently available. Ubuntu 26 sandbox startup failed in earlier qualification. Arbitrarily long Windows installation paths and human standard-user UAC/cancellation remain unqualified. The required publication gate must pass before this candidate is released; disclosure alone does not waive it.

## Candidate SHA256 receipts

These are unpublished candidate artifacts.

```text
51a458d41cb6863ab45085947a03ce544e9f55ce0468bdf0f0b89b85a954496a  MSBT-Installer-v2.41.3.exe
c28225de17832add03c070278caf089bf0929c3e39dd12afbec4b311a5bf72f9  MSBT-Portable-v2.41.3-win-x64.zip
1b3afedb73f80b40b2c95ac424693fb16f6c3cfdd0251e95302b07e6d65e8f24  MSBT-Installer-v2.41.3-linux-x64.AppImage
7bc4ac02e1309ac2a400415c8fcecbbfb32fcd028e7cc04193398ea6895f4647  MSBT-Portable-v2.41.3-linux-x64.tar.gz
```
