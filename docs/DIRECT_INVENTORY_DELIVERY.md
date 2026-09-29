# Direct inventory delivery

The app, mobile bridge, native Quick Menu, bookmarks/catalog send buttons, and
AFK selected loot use the shared `serial_rewards._do_give_serial_to_player_indices`
entry point. Its default is now direct backpack insertion. The name remains for
compatibility. Original-inventory **returns** also use direct insertion. The legacy
`delivery_method='rewards'` keyword and old queue entry point are compatibility
aliases for direct insertion. Cleanup still opens game-generated challenge reward
packages before clearing; it does not create packages to send or restore items. This change does not replace the recovery journal or
change the user's selected boosts, class rules, guaranteed pool, or >70 password.

## Timing and completion

- Greedy chunks contain at most 8,192 encoded ASCII serial characters. No item
  count ceiling is imposed on a chunk. Preserve item order, case, and duplicates.
- One native insertion per eligible game-tick callback across the selected
  players, round-robin; at least 8 ms after each insertion before another.
- Each player pauses 0.75 seconds after a chunk. Another player can progress
  during that pause. No sleeps or background-thread Unreal calls.
- Each player settles for 30 seconds after their final insertion. The queue stays
  active through settlement so AFK does not treat an unfinished send as complete.
- Progress means **submitted**, never guest-save verification. A selected guest
  leaving/changing characters fails that target without sending to their replacement.
  Other selected targets continue. A new send cannot replace in-flight delivery.

`%LOCALAPPDATA%/MattsSDKBoostingTools/direct-delivery-reports/` stores an exact
serial-list manifest plus an append-only per-target/index attempt and return log.
An attempt with no returned event is uncertain and must not be blindly replayed.
There is no automatic journal replay or reward fallback after uncertain insertion.
Travel/AFK interruption cancels further mutations and retains the report.

## Native evidence and supported build

Recovered locally from Steam game build **25372571**. Executable SHA-256:
`9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0`.

`direct_inventory.py` checks all bytes of these functions before binding any
native callable. A mismatch refuses direct delivery before mutation. The full
executable is not read/hashed on the game thread.

| Function | RVA | Size | SHA-256 |
|---|---|---|---|
| Serial constructor | `0x88E2A4` | 739 | `b6a8e1ca11d24319a5abb85d175b549e54e83d7dc42d9c66fa5457d481e8bba2` |
| Identity destructor | `0x369D14` | 184 | `69745be40196a35f3df4aa98c5f0453fbd12018fd71925dc5fe0d3d76a91c559` |
| AddInventory thunk | `0x12E8E74` | 22 | `44645cf9f58a57466dd40e044c9d7044acee0700bc6ca3bc23d60b53fda8f66f` |
| AddInventory body | `0x12E8E8A` | 1873 | `a0099f4889e57f7f5e3706d4f1f97a4dabd47053c6f4b835412a2f4f8161ba84` |

Native caller `0x890E40–0x890EA6` initializes the 0xD8-byte identity; constructor
call at `0x890EB5`, destructor on failure at `0x890EC6`. Interface offset is
controller + `0xE38`; vtable slot `0x30` must point to the checked thunk and its
authority byte at interface - `0xCC0` must be 3. Reflected
`EInventoryItemFlags.AllowOverflow` must be 8. Equip flags = -1, state flags = 0.
The detached identity is destroyed after insertion; no backpack resizing,
reward creation, equipment mutation, or inventory deletion is performed here.

## What has and has not been verified

The research run `both-sized-20260928-f` sent 976 codes to each of two guests in
64 chunks (2–29 items/chunk) over about 105 seconds, plus settlement. The user
confirmed own-game totals of 971 backpack + 5 equipped and 967 backpack + 9
equipped, matching 976 for both. Earlier item-count bursts failed guest-save
verification despite complete host readback. Slight item-code normalization also
occurs with direct insertion, and this method does not promise byte-identical saves.

That evidence validates the research method on this build, not every game build,
network condition, or the newly packaged app/AFK integration. The integrated
candidate still needs an installed game test, including cleanup/original returns
and auto-kick after settlement. No release/version change is authorized by this work.


### Unsupported entries in mixed lists

The 8,192-character bound applies to each individual code, not the total delivery.
Queue setup skips entries outside the tested encoded format/size, preserving the
order and duplicates of supported entries. The response and progress explicitly
report skipped counts. The journal manifest retains the entire original request,
with zero-based rejected indices and reasons; the `filtered` event maps queued
indices to original request indices. No code is truncated or automatically
rerouted through rewards. An entirely unsupported request fails before queueing.
Native insertion errors still stop that target without an uncertain retry.

## Epic candidate (2026-09-28)

Installed Epic manifest: `Oak2-RE_Games_Oak2_Patch_Epic-4845623`.
Analyzed `OakGame/Binaries/Win64/Borderlands4.exe`, SHA-256
`764a4bb5403a2619a0be627de5a738e23ea021e8672f7f0e7a536697d4a06719`.
The root-level EXE is a launcher and is not the analyzed executable.

The Epic profile uses constructor RVA `0x88E204` (739 bytes), destructor
`0x369D14` (184 bytes), insertion thunk `0x12E6842` (22 bytes), and insertion
body `0x12E6858` (1873 bytes). Exact gate hashes are in `EPIC_GATES`.
Constructor and insertion body have respectively 189 and 424 instructions,
matching the Steam functions; differences are relative code/data references.
This structural comparison is not a live game or guest-save verification.
The destructor and insertion thunk are byte-identical to Steam. The thunk checks
`[rcx-0xCC0] == 3` then adjusts `rcx` by `-0xE38`, confirming the authority
and controller-interface layout used by the existing code. Runtime vtable slot
`0x30` must still resolve to the selected profile's exact insertion thunk.

Epic native caller `0x890DA0..0x890E2A` (139 bytes) initializes the same identity
fields, calls the constructor at `0x890E15`, and calls the destructor on failure
at `0x890E26`. Its initializer constant at `0x9F1B230` is
`0000000080000000ffffffff00000000`. Both caller and constant are additional
Epic gates. No function is bound unless one complete profile matches; addresses
from different profiles are never combined. Existing Steam gates are unchanged.

Read-only executable validation is reproducible with
`tools/verify_inventory_profiles.py --steam <Steam Win64 EXE> --epic <Epic Win64 EXE>`.
Both actual binaries match, and changing any one gate causes rejection. Queue and
Quick Menu offline regressions pass. Epic live insertion, return/undo, and guest
save persistence still require testing; this is not yet a public compatibility claim.
