# v2.39.5 — Optional private failure reporting

Windows users can choose automatic failure reporting during installation or later in the desktop Report tab. New installations start with both choices off. When enabled, the app sends failed game commands, desktop errors, and newly found Borderlands 4 crash context to a private report inbox with bounded, redacted log excerpts. A separate choice is required to include game crash dumps. Turning reporting off stops future uploads and clears queued reports.

This release helps us diagnose failures; it does not claim to fix the reported Steam/Epic crashes or save errors. Reporting works while the desktop app is open, with a crash-folder scan on its next start. The daily private review is active, but a real customer report and installed-game failure have not yet been verified. Save files and command inputs are not uploaded.

The mission tools remain experimental. Mission replay still requires a solo host, and a completed Full Game run does not yet prove every achievement or guest save completion. This release does not include the unfinished mission overhaul.

## Downloads

- **Windows:** `MSBT-Installer-v2.39.5.exe` or `MSBT-Portable-v2.39.5-win-x64.zip`.
- **Full app SDK:** `MattsSDKBoostingTools.sdkmod`, also bundled with Windows.
- **Standalone selector:** `BL4MissionSelector.sdkmod`; install it instead of the full app SDK, not alongside it.
- **Android:** `MSBT-Mobile-Controller.apk` remains version 1.6.5.

Close the game before replacing SDK files. Existing save files and replay backups stay on the PC.
