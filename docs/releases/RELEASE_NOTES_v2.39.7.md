# v2.39.7 — item cards on the current game build

The Borderlands 4 update made MSBT reject native item-card generation. This
patch restores the game's card pipeline for the exact current Steam and Epic
executables. Steam gameplay produced cards for a weapon, shield and class mod;
a joined player's shotgun also produced a card and rendered correctly in a
three-player lobby. Unknown game builds remain blocked from native generation
and show the original item code instead of invented stats.

The current Steam host item-send path was checked with a joined player: one
duplicate item appeared in that player's backpack, with equipped items
unchanged and delivery completed. The 100% Drop Rate control also activated
and restored its original code in the current Steam build. These checks do not
establish the guest's saved item after leaving and rejoining, actual drop
outcomes, or that every command works during gameplay.

Epic's installed executable was checked against the recovered native code and
exact build identity, but Epic was not launched. Joined-client-local item
delivery remains disabled. Mission replay remains experimental and solo-host
only; Full Game still uses game 1.10 content catalogs, so complete 1.11
coverage and saved 100% completion are not claimed. Android 1.6.5 is reused
unchanged.

## Downloads

- **Windows:** `MSBT-Installer-v2.39.7.exe` or `MSBT-Portable-v2.39.7-win-x64.zip`.
- **Full app SDK:** `MattsSDKBoostingTools.sdkmod`, also bundled with Windows.
- **Standalone selector:** `BL4MissionSelector.sdkmod`; install it instead of the full app SDK, not alongside it.
- **Android:** `MSBT-Mobile-Controller.apk`, version 1.6.5.

Close the game before replacing SDK files. Existing save files and replay
backups stay on the PC.
