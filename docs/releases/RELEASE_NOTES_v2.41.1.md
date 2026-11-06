## Fixes

- Fixed the updater's false `app.asar` ENOENT error before installer launch.
- Registered SHiFT F10/F11 controls at SDK startup so they no longer depend on a desktop UI tick.
- Fixed "Play while accepting" being blocked by an unsaved/unreviewed protection list. Incoming acceptance can start immediately; **Remove all still requires reviewed, saved protection settings**.

## Background play

Return to normal gameplay, close other menus, press **F10**, then select **Play while accepting**. SHiFT shrinks while walking and normal mouse look remain available. Use the existing Show/Stop controls to return to the menu or stop accepting. Pause-menu entry is not qualified for background play.

The updated local install passed a user control check and 30 consecutive active status samples after activation through 60 seconds. The native background path remains limited to its supported game executable profile; other builds fail closed. Linux packages were built and inspected, but Linux live gameplay was not retested.

## Updating

If the old updater reports ENOENT, close MSBT and BL4, then run the Windows installer below once. That installs the repaired updater for future updates. Install the bundled game files through MSBT with BL4 closed.

Windows/Linux CI passed. Windows validation includes an actual installer install and an Electron regression against the installed updater. Both portable payloads were checked for SDK identity and exact SHiFT PAK/companion hashes. Android is unchanged.
