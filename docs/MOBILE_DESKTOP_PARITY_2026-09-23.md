# Mobile / desktop release-candidate review

Reviewed candidate 338aa33 on September 23, 2026. This is an active-development
source and isolated UI review, not a certification of live phone/game actions.
No progression, inventory, or party mutations were sent during this review.

## Fix before releasing the updated mobile APK

1. **Named-player identity can fall back to a different occupant.**
   `mobile_controller/app/src/main/assets/app.js:53` resolves a saved `index|name`
   by name, then falls back to the index even when the named player is gone.
   An isolated UI probe resolved `1|Departed` to `1|Replacement`. Clear a departed
   named target; permit index-only resolution only for explicitly index-only inputs.
   Also protect pending phone selections from older status replies.

2. **Code/inventory/bookmark sends inherit hidden Boost level settings.**
   `app.js:1502` builds all three delivery payloads, but at `app.js:1533` reads
   `boostOverride` and `boostSerialLevel` regardless of the source screen.
   The Codes delivery panel only shows copies and player (`index.html:120`).
   A probe set Boost override to level 10, then built a Codes send: the payload
   contained override=true, level=10. Put effective level settings beside each
   delivery control, or make shared settings explicitly visible before sending.

3. **Status polling replaces player dropdown options even when unchanged.**
   `app.js:854` assigns innerHTML on every player select; `applyStatus` calls it
   and the poll runs every five seconds. A focused-select probe confirmed that
   an unchanged roster replaced option nodes. Port the desktop roster reconciliation
   behavior and test joins, departures, moved slots, and focused native pickers.
   The Android picker disruption itself still needs a phone check after repair.

## Feature gaps, in recommended order

- **Live player readback:** mobile ignores the SDK's `player_readback` status
  field. Add level, specialization, cash, Eridium, and all five vault-card key
  balances, with the desktop identity/freshness/unavailable rules. Card ranks
  must retain the active/inactive distinction; inactive ranks do not imply missing keys.
- **GZO browsing/submission:** pagination is now present, but mobile lacks the
  desktop DLC and item-level filters and the new submission form. Its catalog
  normalization is separate from desktop's new form/catalog helpers. Submission
  screenshot/autofill depends on desktop services and needs a deliberate mobile
  implementation, not a copied Electron IPC call.
- **Boost scope:** mobile Max All and most boosts operate on one selected player;
  desktop offers Local / All / Other / Named scope. The SDK implementation is
  shared, so the recent specialization fix already applies to mobile's selected
  player. Mobile needs scope controls and correct payloads, not duplicate boost logic.
- **Direct controls:** mobile has no dedicated Black Market, Firmware Transfer,
  UVH Resume, or challenge-management controls matching desktop. Imported Quick
  Menu slots may expose some commands; missing direct buttons are not proof that
  the backend action is absent. Add only supported, tested backend actions.

## Shared correctness issue discovered

Both catalog implementations lowercase serials for identity/deduplication:
mobile `app.js:282,287,331`; desktop `bl4_codes_catalog.js:319,334,471`.
Base85 serial identity is case-sensitive. Distinct serials differing only by
case can collide. Fix both paths and test with distinct case-sensitive entries;
this is a shared defect rather than a mobile parity gap. No claim is made here
that the current bundled catalog contains such a collision.

## Keep intentionally desktop-only

The mobile README explicitly excludes save/profile editing, Matt Editor,
Legit Builder/deep item construction, and desktop installer administration.
These are not release-blocking parity gaps. Unfinished native card rendering
also remains outside this parity pass.

## Evidence and limits

- Previously completed checks: mobile catalog UI (699 pools, six Pearl pools,
  14 fixture pages); desktop responsive suite; eight catalog/startup Python tests.
- New isolated Electron probe used the actual mobile HTML/JS, blocked HTTP(S),
  and inspected target resolution, option identity, and delivery payloads without
  calling a game action. Receipt: `output/reported-issues/mobile-parity-probe.json`.
- USB installation and launch on the Pixel succeeded in the preceding task;
  that does not validate every live mobile action.
- No production code changed as part of this review. Recommendation: repair the
  three behavioral issues and serial identity first, then add readback and the
  chosen direct-control/filter parity features before another phone test.


## Implementation follow-up

The three behavioral fixes and case-sensitive catalog identity are implemented.
Mobile now has live selected-player stats, host/all/other/named boost scope,
Black Market controls, Firmware Transfer, chest spawn, UVH Resume, host skill
reset, challenge selection/category/all/status/cancel, DLC and item-level filters,
and shared GZO search aliases. Codes, Inventory and Bookmarks each expose their
own level override. Named payloads are validated within the same SDK dispatch as
the action, avoiding a separate-selection race.

GZO submission uses authenticated desktop gateway prepare/submit endpoints. The
phone includes the shared mapping/DLC helpers via the Android build, preserves
manual edits, rejects stale decoding results, blocks duplicate pending submits,
and clears the accepted serial. It supports generated screenshots and Android's
image chooser. The desktop rejects phone-provided local file paths by accepting
only an explicit field whitelist. GZO preparation requires the desktop gateway
and its pairing code; ordinary live controls can still use direct SDK pairing.
The existing card renderer is reused; unfinished card research remains excluded.

Validation: 24 focused Python tests; catalog/case-identity tests; authenticated
GZO gateway tests; mocked submission transport; mobile parity and catalog UI;
desktop player roster and readback regression suites. Mobile layout checked at
480 CSS pixels. Android release build and desktop package/smoke pass, versions
unchanged. Actual desktop gateway preparation decoded a fixture and returned an
819 x 2063 PNG; no public GZO submission was made. The updated SDK dispatch and
item-pool filter functions were loaded into the running game without progression
writes or a restart, and live readback remains available.

The Pixel disconnected before the new APK could be installed. The new APK is at
`mobile_controller/app/build/outputs/apk/release/app-release.apk`; installation
and actual phone interaction are pending USB reconnection. No publication or
dirty-worktree cleanup has occurred.

USB follow-up: the Pixel 10 Pro XL reconnected. The parity APK installed
successfully with `adb install -r` (app data retained), and Android confirmed
MSBT's MainActivity opened with a running process. User phone testing remains
pending; installation is no longer blocked.
