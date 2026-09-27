# MSBT v2.17.4

- Integrates Azalea's complete native Quick Menu layout and inventory UI improvements with current MSBT hotkey and delivery wiring.
- Updates the bundled SHiFT menu with Customize and protected-player controls. Fixes Mini Panel visibility in floating mode and keeps AFK acceptance separate from manual request preferences.
- If a guest backpack cannot be captured safely, reward cleanup is skipped and selected boosts and loot continue. Original inventory is not cleared; the run reports the skipped cleanup.
- Retries package opening when no live reward manager accepted the request. A timeout leaves delivery incomplete and prevents auto-kick instead of advancing.

## Known issues

- A substantial FPS drop during AFK/SHiFT use has been reported. Its cause is unresolved and this release does not claim to fix performance.
- SHiFT Customize settings use session fallback; the optional external persistence companion is not included or verified.
- A completed host-side request does not prove every item is saved on a guest. Further reports of partial deliveries remain under investigation.

The updated Quick Menu, Mini Panel and AFK fallback were user-tested in game. Automated checks cover package integrity, UI controls, queue behavior and preservation of current wiring. Android remains at 1.4.1 with no mobile changes in this release.
