# v2.39.4 — Mission-control recovery

An unfinished save-backed replay setup could silently disable **Complete objective**, **Complete missions**, and **Full game** even after the game session that started it had ended. The mission panel now explains the lock in every mission view and offers **Stop replay setup**. Stopping the old setup immediately refreshes the controls and retains any verified pre-replay backup; it does not restore or edit a save.

The desktop save writer also removes its own temporary file if a save write, sync, or replacement fails. It preserves the original save, verified backup, and uncertain transaction receipt. This repairs a confirmed temporary-file leak; the reported customer save failure has not been reproduced.

This patch changes the Windows desktop panel. The full SDK and standalone selector are rebuilt with matching 2.39.4 version metadata, without new mission behavior. Android remains 1.6.5. Update Windows to 2.39.4 to get the recovery control.

Mission selection and Full Game remain experimental. This patch does not establish complete mission playability, all trophy/unlock coverage, customer crash/save-failure resolution, or guest save persistence. Save-backed replay still requires a solo lobby; live completion is the party path.

## Downloads

- **Windows:** `MSBT-Installer-v2.39.4.exe` or `MSBT-Portable-v2.39.4-win-x64.zip`.
- **Full app SDK:** `MattsSDKBoostingTools.sdkmod`, also bundled with Windows.
- **Standalone selector:** `BL4MissionSelector.sdkmod`; install it instead of the full app SDK, not alongside it.
- **Android:** `MSBT-Mobile-Controller.apk` remains version 1.6.5.

Close the game before replacing SDK files. Existing replay backups remain on the PC.
