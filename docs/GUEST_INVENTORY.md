# Local guest backpack delivery and drop

Included in v2.24.0. Guest native transactions are restricted to the local controller on Steam build 25372571 and Epic build 4845623. Epic is mapped from installed executable code, not live-tested. Existing host insertion and spill paths remain unchanged.

## Native evidence

Borderlands4.exe SHA-256: 9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0.
Recovered transaction initialization RVA 5800cf4, identity copy 6ffbee, cleanup 64e12d2, validation 5e09814, network serialization 6231364, add operation 15 handler 3db6018. Function byte hashes are gated in guest_inventory.py before binding. Drop operation 6 handler 1570e22 reads quantity and spawn-before-remove, calling 62592e7 to spawn before removing inventory. The test used quantity one; stacked rows are rejected before any drop submission. Equipped items are excluded.

The SDK process_event export is used because reflected WrappedStruct copying loses unreflected transaction fields. Native cleanup is followed by zeroing the transaction to prevent double cleanup. No authority checks are patched.

## Live evidence, September 30 2026

Consenting Riverduck87 host, FunkYouShiFT guest, throwaway character, fresh The Howl map. Research evidence lives in the primary workspace output/guest-inventory-test.

- 979 unique requested codes; all 979 received with the production Delivery scheduler: 64 size-bounded chunks, 8192-character budget, 0.75-second chunk pause, 8-ms minimum item interval, 3-second final settle.
- All 979 drop requests submitted in one invocation (0.202 seconds submission time). Backpack subsequently confirmed empty, still Role 2 and connected.
- Immediate ground count preceded pickup replication. Independent later read found 1039 new pickup actors. This is not exact per-item accounting: an item may create more than one actor, and other lobby activity is not isolated. No claim of exactly 979 ground pickups.
- 657 received codes exactly matched inputs; 322 differed, matching the previous run. At least one prior comparison showed a removed part. Exact serial preservation and the cause of transformations remain unresolved.
- Integrated source helper independently passed a live 0 -> 1 -> 0 backpack check using NativeInventory.add and GuestInventory.drop_backpack.
- No new reload/persistence test was performed in this round. Desktop button-to-bridge execution and packaged installation still need validation; helper live tests are not full app validation.

## Routing and limits

Delivery keeps the existing queue, cancellation, target tokens, and bulk authorization. Guest delivery rejects other controllers. Public Drop My Backpack uses local controller only; remote target and empty-backpack password rules are unchanged. Dropping submits requests together and reports submission, not server confirmation. No automatic mutation retry. Offline tests cover local-only guard, unsupported or mismatched build, full snapshot preflight, and existing host routing.


## Epic mapping

Epic executable SHA-256: 764a4bb5403a2619a0be627de5a738e23ea021e8672f7f0e7a536697d4a06719. Each function matched the Steam instruction sequence after masking relative branch/call addresses and RIP-relative relocation fields. Transaction offsets, operation constants, and non-relative immediates were preserved. The duplicate implementation signature was resolved using three vtables with the verified validation function followed by the same implementation. The mapped drop handler calls the mapped pickup spawn routine. Full function byte hashes gate the separate Epic profile. See epic-guest-mapping.json for exact RVAs, sizes, hashes, and vtable evidence. This is recovered static code evidence; Epic was not launched and runtime success is not established.
