# Guest inventory ABI recovery — 2026-10-22

## Scope and result

Joined-client inventory transactions remain blocked on Steam 26007962 and Epic
6d531d91. This pass recovered the previously missing constructor and complete
validator from the verified old executable. A second bounded pass proved
serializer control-flow equivalence, all 11 direct serializer callees, and the
Epic server-wrapper virtual-slot identity offline. Transitive indirect/external
targets and live delivery remain outside this proof. `guest_inventory.py` remains unchanged.
No game process was opened, no inventory was changed, and no release was made.

## Executable evidence

Read-only input SHA-256 values:

- Old Steam 25372571: `9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0`.
- Steam 26007962: `ba75f7c2874b16efb5536a5c0cc28918a03efd3e55d790d2e4db57de0c3a353a`.
- Current Epic: `6d531d91011ae0d67ac461a3cacabc99993c279bf325dfe70ff1af00ec43c87e`.

[Machine-readable spans, digests, branch references and validator tables](2026-10-22-guest-abi-recovery.json)
come from `tools/qualify_guest_inventory_abi.py`. The tool rejects a full-file hash
mismatch, compares the full stated spans, and verifies corresponding internal
relative branches. It does not load native code. Its three executable arguments
are `--old-steam`, `--steam`, `--epic`; `--output` selects the receipt.

| Behavior | Old Steam RVA | Current Steam RVA | Current Epic RVA | Bytes |
| --- | --- | --- | --- | --- |
| Transaction initializer | 0x5800cf4 | 0x583e8ce | 0x584fca0 | 176 |
| Identity copy | 0x6ffbee | 0x6fd608 | 0x6ff7c8 | 471 |
| Identity cleanup | 0x369d14 | 0x368b56 | 0x36ad0e | 184 |
| Transaction cleanup | 0x64e12d2 | 0x64e9e1e | 0x64f20c6 | 44 |
| Complete validator | 0x5e09814 | 0x5e36cac | 0x5e41d4c | 909 |
| Initializer defaults tail | 0x5e09686 | 0x5e36b1e | 0x5e41bbe | 107 |
| Operation dispatcher | 0x5e096f2 | 0x5e36b8a | 0x5e41c2a | 290 |

All listed spans have identical instruction bytes after normalizing relative
branch/RIP address operands, with corresponding internal branches. The validator's
15-entry relative dispatch table has identical body offsets for all three EXEs.
This separately supports the operation 6 and 15 validator branch selection.
The initializer/default tail still uses identity offset 0x50, container names
0x128/0x130, slots 0x160/0x161 and zeroes the flags/quantity area at 0x164.
External target equivalence is not implied by this byte normalization.

## Changes and unresolved evidence

The operation-15 body changes `and al,0x97` to `and al,0x93`; MSBT's existing
request sets 0x08 and does not set the removed bit 0x04. The separate native
`and bl,8; shr bl,3` path remains. This explains why the mask difference alone
is not proof that MSBT's existing request layout is wrong.

The serializer moves from 2,095 to 2,098 bytes and reorders cleanup branches.
The recovery tool now follows branch and fallthrough edges from entry instead
of comparing linear instruction order. All 519 instructions participate in a
complete bijection for both old Steam to current Steam and current Steam to
Epic. Moved cleanup blocks preserve their instructions and outgoing edges.
All 11 direct call targets have corresponding complete control-flow proofs.
One old call through jump thunk 0x6819078 now calls the corresponding body
0x572512c directly; resolving the thunk establishes the same 124-byte body.
Transitive external callees, RIP data and indirect-call implementations are not
implied by these instruction/edge comparisons.

The inherited server wrapper has multiple equivalent Epic candidate bodies
(0x5db7342 and 0x87cb352). The selection is now grounded by all three virtual
table occurrences immediately following the uniquely mapped cleanup callback
0x5db7312. They select 0x5db7342 at slots 0xb1c6bc8, 0xb6c6178 and 0xb97eca8.
The duplicate occupies the virtual slot two entries earlier in each table.
The same cleanup-adjacent relationship holds for old and current Steam, and
all 18 wrapper instructions have corresponding control-flow edges. This
resolves the candidate ambiguity without selecting by proximity or first match.

Earlier searches used captured disassembly and PE unwind-table function starts.
The 909-byte validator is a leaf absent from that table; decoding only to its
first return examines just 125 bytes. This pass uses the complete old gate span
and checks its switch table, avoiding that false-negative/incomplete proof.

## Validation and rollback

- Recovery tool passed against all three exact-hash EXEs: 13 span groups; all
  current Steam/Epic bodies matched, including the complete validator.
- 19 focused guest request/reference, direct-inventory and qualification checks
  passed. Rejection tests cover changed branch destinations, changed field
  offsets and incomplete decoding; a reordered-block case verifies edge matching.
- Python syntax compilation passed for the recovery tool and unchanged guest module.
- No live joined-client, host-to-P2 receipt, or save persistence proof was obtained.

Only the offline recovery tool and evidence notes are added. Runtime profiles,
versions, installed SDK and executable files are unchanged; rollback consists of
removing these documentation/research additions. Offline serializer and wrapper
proof is now closed at the stated scope. Runtime profiles remain unchanged;
transitive target qualification and live joined-client receipt/save proof remain
separate follow-ups.
