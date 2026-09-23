# September 23 reported issues: fixes and validation

Worktree: `reported-issues-20260923`, branch `codex/reported-issues-20260923`, base `ac323cc`.
Version remains 2.12.2. No release, tag, upload, or game restart.
Original `working` checkout was preserved.

## Changes and evidence

- **Save overwrite:** embedded editor detection now selects the desktop file bridge.
  A failed desktop write remains an error instead of silently downloading a copy.
  Computer Use opened a COPY of an actual encrypted save, changed level 50 to 51,
  overwrote that same path, and reopened it successfully in Electron. Independent
  decryption found exactly two semantic differences: level 50 to 51 and character
  points 49 to 50. The original game save hash was unchanged.
  Evidence: `output/reported-issues/save-roundtrip/result.json`.
- **Serial delivery:** reread generated output at send time, prevent concurrent
  sends, clear the selection/preview after success, retain selection on failure.
  Regression checks cover consecutive different codes and write/delivery failures.
  No claim of two real item deliveries from the editor UI is made.
- **Delivery panel:** persistent Minimize/Expand, shorter labels, draggable header,
  scrollable body. Minimize was verified in the actual Electron window.
- **Assigned hotkeys:** SDK key events replace unreliable camera-frame polling.
  Removed assignments unregister; native keys cannot also fire through polling;
  menu, travel, disabled-mod and capture guards remain. Desktop layout changes
  register even when the camera callback is idle. A temporary Zero assignment
  dispatched twice with F7 closed, then was removed without saving the test layout.
- **Startup readiness:** a missed initial travel event previously left hooks off
  despite a possessed gameplay pawn. Recover only after a stable pawn and roster
  identity; do not bypass an observed travel. This also restores delayed chest work.
- **Golden chest:** cancel an older pending close when reopening the same chest;
  propagate missing-chest/handler failures to callers. Three full live cycles
  generated fresh loot: InventoryPickup count 16 to 22 to 30 to 36. Rapid
  close/reopen remained open after the delay. Rapid reopen did not generate another
  batch; it verifies cancellation, not extra loot. Evidence: `chest-repeat-candidate.json`.
- **Black Market:** a fresh MSBT-owned native Spawner initializes the actual
  `IO_VendingMachine_BlackMarket` definition. Its real script is activated after
  loading; only the newly created spawn point is disabled afterward. No existing
  world spawner is reset or reused. Live machine was fully visible, contained eight
  stock entries, and opened its native shop through
  `ClientCallVendingMachineUsabilityFunction(machine, OpenVendorMenu)`.
  Automated E presses did not reliably open it, so ordinary-key interaction is
  not independently verified. Evidence: `market-production.json`, `market-open.json`.
- **Max All specialization:** initialize specialization with native
  `BP_UnlockExperienceType` before setting rank and require exact native readback.
  Two actual Electron Max All tests raised specialization 1 to 701, including the
  final candidate. Final post-install readback remained 701. The reported
  intermittent failure itself was not reproduced; an initially locked character
  and guest replication remain unverified. Do not claim those cases are proven.
  Partial failure wording now distinguishes successful steps from failed ones.

## Still unresolved

- **Customs/hover immediate refresh:** the game accepts `ServerActivateDevPerk(4)`;
  the examined Azzy donor uses the same route. No supported immediate client
  refresh was identified. There was no guest in the live session. This is not fixed.
- **Separate vehicle unlock helper:** current native `ClientUnlockUnlockable`
  requires two structured SName identifiers. Existing string/pointer attempts
  fail (0/15 in Max All). No reliable native identifier constructor was found;
  guessed hashes and unrelated reward grants were not added. This remains broken.
- **Vault-card steps in Max All:** tracks 1-3 did not reach the requested rank.
  Other successful Max All stages must not hide that failure. No unrelated DLC
  unlock workaround was added.
- **Faster/instant cooldowns:** native ActionSkill GetCooldown and
  RefillCooldownByValue accept an OakCharacter. A call succeeded with cooldown
  already zero, which does not establish active cooldown behavior. Extracted
  class-specific pool attributes do not prove a universal control. Not implemented.
- **Higher enemy levels:** native game-stage getters and extracted attributes were
  located, but no supported setter was established. Not implemented.

## Local installation and rollback

The game SDK archive was backed up and updated. The local archive preserves the
pre-existing native-card diagnostic module and its two bridge entry points;
those unrelated additions are not included in the clean source candidate.
`importlib.invalidate_caches()` ran in the current game session after replacement.
The game was not restarted, so cold-start/travel validation is still required.
Live bridge diagnostics report `blimgui_available: false`, one local player, and
no bridge error. Session tests took place in World_P at Crimson Resistance HQ.

Windows denied writes to the desktop installation under Program Files. Its files
remain unchanged. Use the local build at:
`dist_electron/win-unpacked/MattsSDKBoostingTools.exe`.
The active source preview uses this worktree's editor fixes. Backups and hashes:
`output/reported-issues/install-backup/` and `install-receipt.json`.
The clean source archive is `output/reported-issues/MattsSDKBoostingTools-source.sdkmod`. The local desktop bundles match the installed archive, including the preserved diagnostic overlay.

## Verification

- 32 focused Python tests passed (economy target selection, startup/camera lifetime,
  configured input, chest ordering, world-change/duplicate spawn guards, no BLImGui).
- All SDK Python sources and packaged Python entries compile; archive CRC passes.
- Both changed JavaScript files pass syntax checks.
- Reported editor regression: four save routing cases, exact temporary-file overwrite
  and failure preservation, consecutive codes, and collapse persistence passed.
- Local desktop was rebuilt with the lockfile's Electron 44.3.0 dependencies;
  packaged smoke exits 0, updater dependencies load, and no update check was run.
- Native cooldown/unlock details and exploratory scripts are local evidence under
  `output/reported-issues`; they are not mod entry points or release assets.

This is a partially verified local repair, not a claim that every reported issue
is fixed or that guest behavior is release-ready.

Additional validation: `npm run test:editor-update` passed browser-asset, native
lookup, and save-update checks, but its final page smoke timed out waiting for
Loveless class-mod UI. Its catalog loaded 58 files/515 roots; the harness reported
missing Nexus-Data-skilltrees_data6.json and blocked external Monaco/resources.
This broader page test is not counted as passed or established as pre-existing.
The targeted reported-issues test and actual encrypted save UI roundtrip passed.


## Follow-up: live player readback

The desktop Connection & Scope panel now displays a read-only summary of the
selected player: character level, specialization, cash, Eridium, and keys for
all five vault cards. Expand Vault-card ranks for active/inactive track values.
Snapshots are collected on the existing game-thread status tick; the HTTP handler
serves copied JSON. The UI rejects stale or mismatched readings and shows missing
values as unavailable. No progression or currency setter is used.

Validated against a live guest (Iced_life97): level 70, specialization 701,
cash 2,147,483,646, Eridium and all five key balances 2,147,483,647. The restarted
source desktop preview displayed those values. Nine focused Python tests passed;
the Electron readback test passed identity, stale/offline, missing-value, and key
balance cases. No release/version change.

Correction to earlier vault-card assessment: Matt clarified that a player must
activate a card before its rank can be set. TauntingRoss's live CurrencyManager
showed 2,147,483,647 keys for each of cards 1-5, including inactive cards. Those
key grants are confirmed; inactive ranks alone are not evidence of a broken grant.
Matt also confirmed building and sending two different editor codes successfully.

## Follow-up: completed GZO search and submission integration

Selectively imported the completed search/submission work from
`working/_release_check/gzo-codes-align` (branch `fix/gzo-codes-search-submit`,
uncommitted changes over ac323cc). Includes the highlighted submission button,
manufacturer/creator/type/DLC filters, Legit/Modded selection, pagination,
submission field mapping and autofill, screenshot attachment, and explicit
server-acceptance handling. Manual form edits survive autofill, stale serial
results are rejected, and repeated clicks cannot submit the same pending request.

The in-progress card model, adapter, protocol, assets, resolver, naming, stat
calculation, and item-pool changes were excluded. Screenshot attachment uses the
existing release-candidate renderer through a small capture wrapper; its success
is not a claim that unfinished card rendering is complete.

Validation: catalog, form mapping, DLC contract, transport, Electron form, screenshot
capture, live-player readback, and roster regression tests passed. Transport tests
mock the server and do not publish submissions. The app was restarted and the
updated catalog controls and form visually checked. Local packaging succeeded.
Version remains 2.12.2; no release was published.
