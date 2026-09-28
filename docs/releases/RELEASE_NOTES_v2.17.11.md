# MSBT v2.17.11

## Changes
- Desktop AFK starts transfer large loot lists in verified chunks instead of failing at the 2 MB request limit. Large saved desktop lists use IndexedDB. No new item-count cap; existing delivery authorization and pacing remain.
- Bookmarks support bulk code paste, duplicate preservation, multi-item deletion, folder/subfolder deletion, and existing-folder dropdowns. AFK can browse bookmark folders and add a whole folder to either loot list.
- Blank bookmark titles use catalog matches and the existing inventory item-name resolver. Fill missing item names repairs generated placeholders while preserving custom titles. Unresolved items keep explicit fallback names.
- Bookmarks display the existing inventory-style item card and can save PNG card screenshots. This reuses the existing resolver; it does not establish new native item-card accuracy claims.
- SHiFT no longer restores a saved capture-blocking flag on close. After SHiFT is used, MSBT continues checking the owned game window for capture exclusion.
- SHiFT has a remembered Compact / Medium / Regular size selector.

## Update and validation
Update the bundled SDK and SHiFT PAK with Borderlands closed, then restart the game. Desktop tests cover large-list persistence, bulk bookmarks, folder operations, name resolution and screenshots. Offline SDK tests cover capture cleanup and delayed close behavior; PAK payloads were verified after rebuilding. The user confirmed the installed test update during release preparation, including the requested live SHiFT check. Host-side tests do not verify guest save persistence.

The Android controller remains v1.4.2; the new large-list transfer is a desktop feature. Existing game-generated challenge/UVHM rewards and unresolved guest backpack-clear persistence are unchanged.
