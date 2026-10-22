# v2.39.6 — Steam 1.11 mission compatibility

This patch updates MSBT's mission and replay support for the installed Steam game build 26007962. Mission selection and save-backed replay were qualified on that exact build. One authored replay survived Save/Quit and reload with the selected mission still active. Mission coverage remains partial: Full Game catalogs were extracted from game 1.10, so this release does not claim complete game 1.11 content or achievement coverage.

The current Epic executable hash has a source-qualified mission, character-loader and dialogue profile. Epic was not launched for this qualification, so live Epic behavior is not claimed.

Direct backpack inventory and item-card delivery remain gated on Steam 26007962 while native transaction and card mappings lack safe proof. The app fails closed; no items are sent through those paths on this build.

Full Game now conditionally applies the authored safehouse `Claimed` effect after the corresponding mission record completes. In the observed Abandoned Post check, the safehouse was already `Claimed`, both discovery entries were already discovered, and its map entry was unlocked after Save/Quit and reload. That observation does not establish that the repair caused the unlock. An unclaimed safehouse and guest persistence remain unverified.

Android remains version 1.6.5 and is reused unchanged.

## Downloads

- **Windows:** `MSBT-Installer-v2.39.6.exe` or `MSBT-Portable-v2.39.6-win-x64.zip`.
- **Full app SDK:** `MattsSDKBoostingTools.sdkmod`, also bundled with Windows.
- **Standalone selector:** `BL4MissionSelector.sdkmod`; install it instead of the full app SDK, not alongside it.
- **Android:** `MSBT-Mobile-Controller.apk`, version 1.6.5.

Close the game before replacing SDK files. Existing save files and replay backups stay on the PC.
