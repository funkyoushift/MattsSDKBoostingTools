# v2.39.6 — game 1.11 compatibility and host backpack repair

This patch updates mission and replay support for the installed Steam game build 26007962. Mission selection and save-backed replay were qualified on that exact build; one replay survived Save/Quit and reload with the selected mission active. Full Game catalogs still come from game 1.10, so complete game 1.11 mission or achievement coverage is not claimed.

The current Epic executable has source-qualified mission, character-loader and dialogue profiles. Drop Rate and Weighted Loot High Roll also have exact current-build native profiles. Epic was not launched, so live behavior is unverified. Epic skill-charge enumeration remains gated.

Steam 26007962 and the current Epic executable now have exact-hash host backpack delivery profiles. On Steam, six supplied item codes each appeared once in the live host backpack, increasing its count from 620 to 626. The character was not reloaded afterward, so item persistence is unverified. Sending to another player has not been tested with a guest; locally joined-client delivery and native item cards remain gated on the current builds.

Full Game now conditionally applies the authored safehouse `Claimed` effect after the corresponding mission record completes. In the observed Abandoned Post check, the safehouse was already `Claimed`, both discovery entries were already discovered, and its map entry was unlocked after Save/Quit and reload. That observation does not establish that the repair caused the unlock. An unclaimed safehouse and guest persistence remain unverified.

Item-send actions and trainer-derived controls were audited for current-build routing and native gates. Static checks do not prove every command in gameplay. The two unreliable Guest Grid fog-of-war experiments were removed; Party Reveal Map remains. Android remains version 1.6.5 and is reused unchanged.

## Downloads

- **Windows:** `MSBT-Installer-v2.39.6.exe` or `MSBT-Portable-v2.39.6-win-x64.zip`.
- **Full app SDK:** `MattsSDKBoostingTools.sdkmod`, also bundled with Windows.
- **Standalone selector:** `BL4MissionSelector.sdkmod`; install it instead of the full app SDK, not alongside it.
- **Android:** `MSBT-Mobile-Controller.apk`, version 1.6.5.

Close the game before replacing SDK files. Existing save files and replay backups stay on the PC.
