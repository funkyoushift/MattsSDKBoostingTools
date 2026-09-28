# MSBT v2.17.8

- Item delivery now adds directly to backpacks, without reward packages. Multiple selected players receive paced delivery concurrently, with a final settling wait. Original-inventory returns in AFK cleanup retain their existing reward-based path.
- Unsupported oversized codes are skipped and reported instead of blocking an entire mixed list. Reports retain the original requested codes; codes are never shortened.
- Enter the action password once per local installation to unlock bulk deliveries, Undo, guest Empty/Drop Backpack actions, and AFK bulk loot across restarts and updates. The password itself is not stored.
- Fixed Undo ignoring the supplied password for restores over 70 items. Backups now retain identical copies, save to disk before clearing, and remain available after delivery is queued. Repeated clicks do not automatically resend a queued restoration; changed player sessions require manual recovery from the backup.
- Inventory snapshots preserve identical equipped and backpack items instead of merging equal codes. Empty live reads no longer fall back to stale desktop rows.

## Validation and remaining limitations

The direct-delivery research test was confirmed with 976 items per guest after loading their own games. Current source passed 209 focused Python tests, AFK/password desktop checks, full settings restart checks, and bundled game-install checks. The latest duplicate-reader correction has offline coverage; a new guest clear/Undo/save round trip is still needed.

Empty Backpack can still appear cleared and have items return after the guest rejoins. This release does not claim that persistence issue is fixed. A successful native call or host inventory read is not proof of a guest save. Some modded item codes change when processed by the game; delivery reports retain unverified results. Direct native delivery checks the supported game build before calling game code.

## Installation

The versioned Windows installer installs the bundled AFK SHiFT PAK, SDK mod, and missing SDK/mod manager when game integration succeeds. With MSBT-Setup.exe or the portable package, use Settings > Install / update SDK mod to install the bundled game files. Close Borderlands before updating game integration. Existing newer SDK/mod-manager versions are preserved. Android remains v1.4.2, unchanged.
