# AFK inventory capture: unreleased groundwork

v2.16.0 does not include this prototype. `afk_inventory_capture.py` is a read-only precursor, not a cleanup implementation. It now has an explicit bridge action and runs on the existing game tick. It is not wired to AFK start or any inventory-changing action. The first read-only build was installed for the guest test; the expanded reflection diagnostic and recovery core are local and pending installation.

## Implemented

- Capture exact `OakPlayerState.BackpackItems.items` rows using a pinned player state, without selected-party-slot fallback.
- Preserve duplicate serials and their case. There is no 2,000-item truncation.
- Record native handle, instance ID, quantity, inventory flags, item-state flags, equip slot, slot lock, slot maximum quantity and slot type separately from the serial.
- Read at most 16 rows per step, at most four times per second on the game tick. Only an explicitly started audit runs; normal AFK work does not start a capture.
- Require a second matching read pass. A changed count, changed row, unavailable container, unreadable field/serial or departed/replaced player invalidates the capture. No partial snapshot is returned as complete.
- Always report `cleanup_allowed=false` and `restoration_verified=false`, even for two matching passes or an empty container.

Twenty-nine capture/action tests plus fourteen recovery tests pass; the combined run including existing AFK and startup/import checks passes 88 tests. The audit requires stopped AFK boosting, waits for character readiness, tracks slot reordering by player state and cancels on departure, world change, loading, timeout or boosting restart. Polling preserves unrelated queued actions and never changes the shared manual target. These tests do not establish live guest replication completeness, serial round-trip fidelity or a safe restore.

## Read-only comparison workflow

After installing the diagnostic SDK with the game closed, load a guest and stop AFK boosting. Run `python tools/afk_lobby/capture_inventory_audit.py --player-index INDEX` using the explicit guest index from the bridge roster. The saved local JSON includes the audit ID, exact rows and native inventory API names. API discovery invokes no inventory methods. An unreadable native field is identified by its field path without printing item codes.

After a separately authorized reward test, run `python tools/afk_lobby/capture_inventory_audit.py --compare AUDIT_ID`. This captures the same guest again and reports added, missing and changed rows by the observed native handle and instance ID. Duplicate identities reject the comparison. Repeat comparisons keep the original baseline and save separate files. Disconnects, world changes and SDK restarts require a new baseline.

This matching is observational: native IDs have not been proven suitable for persistent identity or removal. Added items are not automatically classified as challenge rewards. Every result continues to report `cleanup_allowed=false`; comparison never empties, removes, restores or delivers items. Capture files contain item serials and remain local.

## Native field evidence

Inspected local `sdk-control-lab/tmp/body-usmap-schema.json`, SHA-256 `b75eee943c1cdca78fd2ef692c3df398b1ddbbdc2850e6c5c4a9cb3a58ba5afe`:

- OakPlayerState.BackpackItems -> GbxItemSlotsContainer, file offset 2103285.
- GbxItemSlotsContainer.items -> array of GbxItemContainerSlot, offset 1800593.
- GbxItemContainerSlot.InventoryItem (1800345), type (1800357), MaxQuantity (1800369), IsLocked (1800377).
- InventoryItem.item (1845277), Handle (1845289), Flags (1845301), EquipSlot (1845314).
- InventoryItemHandle.Handle (1845406).
- GbxItem.data (1800232), State (1800244).
- GbxItemData.InstanceId (1800397), Identity (1800405).
- GbxItemState.Quantity (1800618), Flags (1800626).

These are offsets in the extracted schema file, not runtime memory offsets. The installed Steam manifest currently reports build 25372571; the schema's linkage to that exact executable build has not been re-established. Serial extraction reuses the existing item_serial_reader memory reader and remains separately runtime-unverified here. Flag meanings, slot-type restoration, empty-slot representation and preservation of handles across reconnects are not inferred.

## First live guest validation

The diagnostic SDK was installed after closing the game on 2026-09-27, with a hash-verified backup. A guest capture returned 168 rows: 159 with equip slot -1 and nine with other equip-slot values. Matt confirmed these counts. All 168 native identity pairs were distinct; 161 serials were unique, so repeated codes were retained. Two full captures matched with zero additions, missing rows or changes. Local evidence is under `output/inventory-audits/802b60ffb1c94f43a68563d48ce1ac17-*`.

This validates the observed counts and stable reads for one guest/session, not restore fidelity or persistence. Native API-name discovery found container operations but no verified individual-item removal function. The manual complete-all challenge action discovers all live controllers; it must not be treated as guest-only merely because the UI target selects a guest.

Matt subsequently authorized Complete ALL challenges for both players. The queue sent all 3,250 steps with zero reported sending failures; guest completion remains unverified. Before packages were opened, a further capture still matched all 168 original rows. After Matt reported that the tester opened the packages, capture `802b60ffb1c94f43a68563d48ce1ac17-1790488029182222100.json` returned 176 rows: eight additions, zero missing originals and zero changed originals. All eight additions were quantity one and equip slot -1. This is evidence of additions following package opening, not independently verified reward provenance or proof of safe removal. No items were deleted, restored or intentionally delivered, and AFK remained stopped.

## Next work

1. Compare the explicit read-only diagnostic capture with a guest's original inventory. Do not equate a replicated empty container with a fully loaded empty backpack.
2. Determine whether native per-item removal can target only rewards generated by the selected challenge/UVHM actions. Verify stable item identity and distinguish those rewards from intentional drops and the guest's own inventory changes.
3. If full clear/restore is required, implement durable recovery tied to verified guest identity, restore metadata/duplicates/quantities and verify all originals before allowing auto-kick. Keep equipped items protected.
4. Exercise interruption, slot reuse, split-screen and return-to-own-game persistence before enabling any deletion.

## Clear-and-restore workflow requested after the live capture

Matt clarified that cleanup should clear the whole backpack, deliver the intended
loot and then return the original items, rather than selectively deleting reward
items. Local `afk_inventory_recovery.py` implements the transaction core for that
sequence. It writes an atomic, checksummed recovery record before submitting each
operation, retains original rows including duplicates, pins the guest/world,
submits each operation once, and requires final verification before `can_kick`
becomes true. Restarted transactions are inspectable but cannot automatically
replay a clear or resend. Failed or uncertain operations retain the backup and
block completion. Native handles may change on recreation; verification compares
serial multiplicity and captured metadata rather than requiring old handles.

Fourteen recovery tests plus existing capture, AFK and startup/import checks pass
(88 combined, including two additional reflection checks). These use fake native adapters. The recovery core is not yet wired
to AFK or installed, has no enabled native adapter and has not cleared the tester's
inventory. Its kick decision is not yet integrated into the shared-connection
barrier. Existing serial delivery does not restore equipped slots or item flags;
Matt explicitly requires restoring equipped slots and flags as well as the items.
A read-only `restore_apis` audit mode now inspects reflected function signatures
for OakInventoryStatics, OakPlayerState and OakPlayerController. It uses the
SDK UStruct/UFunction metadata interfaces and invokes no game inventory methods.
The updated diagnostic package is built, but needs a restart to install. Clear scope and live round-trip verification remain required before
enabling this transaction in normal AFK work.

### Second diagnostic installation and returning guest

Installed expanded diagnostics after an authorized restart, SHA-256
`2f80af3f07ac427b94f9364df52330ca292f392b580d393266c3b03ee725c69e`.
Live `restore_apis` returned reflection metadata without errors; evidence is
`output/inventory-audits/restoration-api-schema.json`. The player controller
exposes ExecuteInventoryTransactionOnServer/Client with a Transaction struct
parameter. This signature alone does not establish how to equip or set flags.
The extracted GbxInventoryTransaction schema only supplies four owner interfaces
(SourceContainerOwner, TargetContainerOwner, SourceEquippedSlotOwner,
TargetEquippedSlotOwner); it does not provide the operation/item/flag fields
needed to construct a proven restore transaction. Do not invent those fields.
OakCharacter owns EquippedInventorySlots in the extracted schema and is a
further inspection target; this diagnostic only inspected inventory statics,
player state and controller classes.

Returning-guest capture `308014ea852b4e4e9d5e2024446cd2ba-1790488794789775100.json`
contains 168 entries. Comparing by serial, multiplicity and all recorded metadata
(excluding recreated native IDs) matches the original 168 entries exactly.
The eight previously observed additions are absent after rejoining; the cause
is not established, so package opening must not be treated as persistence proof.
The new audit ID pins this new session; the old audit is evidence only and must
not be used to target a guest after restarting. No destructive test has run.


### Item-only restoration approved

Matt subsequently waived restoring equipped slots and item flags. The current
experimental native adapter returns original serials to the backpack, preserves
case and duplicate quantities, and does not re-equip or remark items. Current
live-test eligibility requires quantity one per captured row; stacked quantities
are rejected before clearing until their native restoration is verified.

The explicit `afk_inventory_audit` mode `recovery_start` requires the current
completed audit ID and `backpack_password`. It rechecks the original guest/world,
AFK stopped, host authority, no competing boosts/delivery and a fresh capture
containing every original before invoking the existing EmptyContainer helper.
It writes a persistent recovery record under LOCALAPPDATA/MattsSDKBoostingTools/
inventory-recovery before mutation. It reads back the container after clearing;
any original entries retained by the game are subtracted from the resend list.
The returned original copies use the existing tick-driven serial delivery queue
with player-state pinning and then a fresh full inventory capture. Item-only
verification compares exact serial multiplicities/quantities, ignoring equip and
flag metadata. Failed or uncertain recovery blocks AFK start, including after a
process restart. Records are never automatically replayed or removed.

First test mode intentionally delivers no new loot and never kicks. Full AFK
capture/boost/open/clear/new-loot/restore wiring is still pending the live
round-trip and persistence check. `recovery_status` returns phase, backup path,
verification and kick eligibility without item codes. 95 offline tests pass,
including the native adapter with fake game operations. This is not live proof
that clear/restore or guest save persistence works. Nothing is published.

### First destructive round-trip test

The authorized guest test captured 168 original rows in current-session audit
`dfd339f16bff49759145581af382cc9e`. Recovery journal
`e8dc83de7a0f46c4bf1471201384208f.json` was durably written before clear. After
EmptyContainer, the strict reader failed with "Item serial unavailable;
empty-slot interpretation is unverified". The sequence blocked before restoring
and kept auto-kick disabled. A separate legacy read also reported no readable
serials; it did not constitute proof of a complete empty inventory.

To recover immediately, the saved 168 serials (including duplicate copies) were
submitted through give_serial_selected with level override off and password
authorization. Five package chunks completed. Fresh capture
`dfd339f16bff49759145581af382cc9e-1790489566300112300.json` returned 168 rows, with
exactly the original serial multiplicities and quantities: zero missing, zero
extra, 161 unique serials, nine rows with equip-slot values. That is a live
item-return result, not proof that equipment metadata was intentionally restored
or that the guest save persisted. Evidence is in manual-recovery-verification.json.

The source now continues original-item restoration after a successful clear call
whose readback encounters unreadable empty slots. It explicitly records that
clear readback was NOT verified and still requires exact final item counts; it
does not skip unreadable rows in ordinary captures or claim they are empty.
97 offline tests pass, including no kick on unexpected duplicates after this
fallback. This fix is not installed yet. The live recovery journal remains
blocked and retained; AFK start remains blocked pending reconciliation and the
guest's return-to-own-game check. Do not replay the clear or resend the originals.


### Recovery confirmation and corrected build

Matt confirmed the items were back. The saved journal was reconciled against the
fresh 168-entry capture (zero missing/extra serial quantities), while preserving
an exact copy of the blocked journal in output/inventory-audits. Its resolution
records manual return plus capture verification and user confirmation; it does
not relabel the original automatic run as successful. The corrected SDK was
installed with a verified backup and the game restarted, SHA-256
4465edb2dc0e420e4cb0cd6025ebf9702c0570743b13a3c5316128ac64a7f180.
The process-local blocked state clears on restart and the completed on-disk
record no longer blocks AFK start. Automatic cleanup remains off. 98 offline
checks pass, including the native adapter's dead-slot fallback; a fresh live
round-trip without manual intervention is still required before AFK integration.


### Corrected automatic round-trip passed live

On Matt's explicit "run it", fresh audit 4b508e73fecc497282b33ebe8c111d67
captured 168 rows. Recovery e6344a964d83451a882ba96a475180da progressed through
clear, delivery (no new loot), restore and verification automatically. Final
verification reported zero missing and zero unexpected serial quantities, with
no manual resend needed. The clear readback remained unverified as expected
because of the empty-slot decoding issue; success was based on the final full
inventory capture, not inferred from the clear call. AFK remained stopped, the
guest remained present and no kick was issued. Evidence is in
output/inventory-audits/corrected-recovery-receipt.json and the durable journal.
This proves the original-only automatic round-trip in this session. New-loot
composition, automatic AFK integration and persistence after this particular
run are not yet verified.
