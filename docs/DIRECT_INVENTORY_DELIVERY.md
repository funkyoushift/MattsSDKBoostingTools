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
