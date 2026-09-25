# Random-70 AFK loot and protected actions

AFK Lobby now offers **Send 70 random items per guest**. Build the loot pool from selected Item Catalog entries, bookmarks, or item codes. Each join draws up to 70 entries without replacing selected entries; repeated codes remain intentional extra copies. Pools smaller than 70 send every entry. The full pool stays available for future guests.

**Send all selected items** remains available. Sending more than 70 items now requires password authorization in AFK and manual bulk serial delivery. AFK authorization lasts for the current run, so the host does not need to enter it for each guest. Stopping and restarting requires authorization again. The password is not stored in settings or repeat-command history.

**Empty Backpack** and **Drop All Backpack** require password authorization when targeting a non-host player. Host targeting remains unrestricted. Checks run in the SDK, and the desktop panel prompts when needed. A target change during the backpack password prompt cancels that attempt.

The AFK walkthrough explains random selection and protected unlimited delivery. Older SDKs are blocked from using the new AFK delivery modes until updated.

The limit applies to items in a delivery, not existing backpack contents or accumulated items across joins. It does not change guest inventory visibility. Installer SDK/manager preservation and the bundled SHiFT PAK remain unchanged. Close Borderlands 4 before updating.

Validation covers password boundaries, guest/host targeting, cancellation, random selection, unlimited authorized delivery, SDK imports, UI behavior, and packaging. This is a shared-password application control, not tamper-proof protection against someone modifying their own SDK code. Guest save persistence remains unverified.
