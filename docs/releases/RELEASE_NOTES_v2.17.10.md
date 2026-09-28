# MSBT v2.17.10

- AFK original-backpack restoration now uses direct backpack insertion, matching ordinary item delivery, Undo, and missing-item repair.
- Legacy sender calls and the old rewards delivery selector now route to direct delivery. MSBT no longer creates reward packages to deliver or restore serial items.
- Cleanup checks original codes before clearing. If an original code is outside the supported direct-delivery format or size, cleanup is skipped instead of clearing an item it cannot return.
- Updated bridge help to describe direct delivery.

## Validation and limitations

142 focused offline tests passed, including restoration of missing duplicate copies, interrupted deliveries, player identity checks, recovery, and legacy routing. Packaged syntax and source matching were verified. The new direct-restoration path has not yet completed a live guest clear/restore/save round trip.

The game itself can still create reward packages when challenges or UVHM are completed. Cleanup continues opening those existing packages to remove reward clutter. Guest backpack clearing may still fail to persist after rejoining; this release does not claim to fix that separate issue. Host progress does not verify guest saves.

Includes the v2.17.9 updater self-lock fix, persistent password unlock, duplicate-preserving backups, and bundled AFK SHiFT PAK. Close Borderlands and use Settings > Install / update SDK mod after a reusable Setup or portable update. Android remains v1.4.2, unchanged.
