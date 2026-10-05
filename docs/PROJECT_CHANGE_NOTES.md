# Project change notes — read first

Before re-researching a feature, read its entry below and any linked component notes. Confirm the current checkout, installed artifacts and runtime before reusing conclusions. Historical notes are evidence of that run, not current proof.

## Changes

- [2026-10-04: Expanded item cards and hover previews](changes/2026-10-04-expanded-card-layout.md) — local readable layout for overflowing modded stats/skills, cropped thumbnails, full zoomable preview, compact switch and cached-data redraw after layout updates.
- [2026-10-04: Cached cards during guest sessions](changes/2026-10-04-card-cache-solo-fallback.md) — local exact-serial previous-session fallback and readable unavailable message; generation safeguard retained.

- [2026-10-04: Card helper reopening patch v2.29.1](changes/2026-10-04-card-window-reopen-patch.md) — tray and second launch target the main control panel; installed regular-profile Community Folder and restart checks passed.

- [2026-10-04: Shared native-card release v2.29.0](changes/2026-10-04-shared-native-card-release.md) — published combined delivery/updater release with Community Folders and serial-menu previews, GZO/upload priority, guarded native service and offline snapshots; superseded by the reopening patch.

- [2026-10-04: Updater checked and updated the wrong game installation](changes/2026-10-04-updater-game-target.md) — Steam/Epic target mismatch confirmed in installer receipt; local desktop/updater correction installed, Steam SDK repaired to bundled v2.28.0 with matching hash. Loaded-game identity support is source-only until a future SDK build.

- [2026-10-04: Concurrent manual and AFK delivery methods](changes/2026-10-04-concurrent-delivery-methods.md) — local implementation; independent manual/AFK requests to different targets, shared progress, conversion target snapshots, recovery exclusivity and kick protection. Not installed or published; live mixed-method validation remains open.

- [2026-10-04: AFK concurrent release v2.28.0](changes/2026-10-04-afk-concurrent-release.md) — published; all 11 public asset hashes and public installer/reinstall/rollback checks passed. Permanent concurrent guest default, exclusive cleanup/host-test safeguards, desktop per-guest progress and authoritative count.

- [2026-10-04: Concurrent AFK pacing pilot](changes/2026-10-04-afk-concurrent-pacing.md) — two overlapping live deliveries completed 500 each; both guests confirmed counts and persistence via Matt. Three-guest live validation remains open; see entry for deployment and rollback.
- [2026-10-04: AFK shows 500 but sends 70](changes/2026-10-04-afk-delivery-count.md) — confirmed stale active-state display; desktop fixed and installed locally; active SDK configuration restored to 500 with persisted authorization. Includes data flow, tests, rollback and limits.

## Existing component context

- `AFK_NEXT_WORK.md`: original random-count, guaranteed-item and password requirements; dated historical implementation notes.
- `REMOTE_AFK_PERSISTENCE.md`: bridge discovery, remote action forwarding, pairing and desktop background behavior.
- `AFK_INVENTORY_CAPTURE.md`: inventory capture evidence and limits.
- `LOCAL_FIX_QUEUE_2026-10-02.md`: historical queue, superseded in part by v2.27.0; do not treat all pending entries as current.

## Required entry for every meaningful change

Record issue/symptoms; root cause with evidence (separate unknowns); checkout and relevant version; files/components; exact behavior before/after; validation commands and outcomes; failed/rejected approaches worth preserving; deployment state and rollback; unresolved follow-ups. Link the entry here. Never include passwords, tokens or full user inventories. Keep measured evidence separate from assumptions and offline tests separate from live proof.
