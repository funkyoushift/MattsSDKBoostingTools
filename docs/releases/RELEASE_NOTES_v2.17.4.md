# MSBT v2.17.4

- Integrates Azalea's complete native Quick Menu layout and inventory UI improvements with current MSBT hotkey and delivery wiring.
- Updates the bundled SHiFT menu with Customize and protected-player controls. Fixes Mini Panel visibility in floating mode and keeps AFK acceptance separate from manual request preferences.
- If a guest backpack cannot be captured safely, reward cleanup is skipped and selected boosts and loot continue. Original inventory is not cleared; the run reports the skipped cleanup.
- Retries package opening when no live reward manager accepted the request. A timeout leaves delivery incomplete and prevents auto-kick instead of advancing.

- Tracks successful shared challenge and UVHM runs separately for guests ready and present throughout, avoiding duplicate runs for those guests. Late joiners still get their own run.
- Keeps the AFK queue moving after unresolved inventory recovery, with saved original/selected item lists and a manual repair report. Unverified guests remain in the lobby.
- Avoids automatic deficit resends when unexpected items make the readback ambiguous, reducing duplicate delivery risk. Clear deficits still receive bounded retries.

## Known issues

- A substantial FPS drop during AFK/SHiFT use has been reported. Its cause is unresolved and this release does not claim to fix performance.
- SHiFT Customize settings use session fallback; the optional external persistence companion is not included or verified.
- A completed host-side request does not prove every item is saved on a guest. Further reports of partial deliveries and serial readback differences remain under investigation. Shared completion tracking uses host-side run evidence, not guest-save confirmation.

The updated Quick Menu, Mini Panel and AFK fallback were user-tested in game. Automated checks cover package integrity, UI controls, queue behavior and preservation of current wiring. Android remains at 1.4.1 with no mobile changes in this release.
