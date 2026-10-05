# Native display-row projection, 2026-10-04

Installed Steam build 25372571, Borderlands4.exe SHA256
`9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0`.
These are recovered executable rules. Original-instruction tests execute offline
in Unicorn. The separately guarded SDK probe has also completed eleven live
detached previews; see the live evidence below.

## Function evidence

| RVA span | SHA256 | Role |
| --- | --- | --- |
| E69A30..E69CA9 | ec1f59a0363723667b0d3f99537cafe84f166171ea923ed07e46dabc86e0b593 | Convert E0-byte display rows to 70-byte UI rows |
| E69D1A..E6A157 | 0a8a22ae8ab912bc37dd763440fd0322b20a12884fd804f3765f4a844c971c73 | Copy fields, resolve asset path and comparison style, final value presentation |

Disassembly and hash receipts: research output
`local-card-resume-20261003/native-ui-array-copy/` and `native-ui-row-value/`.
Caller evidence is the existing `stat-collection-discovery/functions/011fc6ba.asm.txt`.

- E69A94 accepts only a row whose first byte equals **1**, preserving iteration
  order. Other byte values are not treated as truthy.
- E69B08..E69C71 counts rows having nonempty label, image, or value. If none
  qualify, E69C34 clears the whole output array. This is not a blanket removal
  of every individually blank row within a nonempty group.
- E69D4A, E69D91 and E69DE0 copy label, value and description independently.
- E69E2F resolves the row's asset reference. E69E7A..E69FB9 obtains the
  comparison enum text and changes it into the native CSS class.
- E6A024..E6A0A0 compares the **formatted string** against UTF-16 `0` at
  RVA 9E1EDFC. Only exact `0` becomes `-` (9E0D19A), with comparison class
  `item_card_compare_nocompare`. It does not change `0.0`, `00`, `-0`, or `0%`.
- 11FD876 calls E69A30 for primary rows; 11FD828 does so for secondary rows,
  with a later owner-defined limit. Other array consumers include tertiary
  and text rows. Singleton headline, type line and redtext use separate paths.

`native_card_model.js` now ports only the proven exact-zero presentation step
for the array fields. It does not infer missing values or change the unresolved
attribute arithmetic. Original cached input objects remain unchanged.

## Original-instruction tests

`serial_token_oracle.py --card-ui-rows` constructs, binds and fills the native
model, invokes E69A30 on each model group, exports bounded immutable rows, frees
the converted array, and runs the model destructor. Conversion of all groups
is diagnostic; it does not claim the UI presents every group as an array.

`native-ui-ten-20261004.json`: ten exact fixture serials, 510 model display rows,
462 converted rows, ten completed model destructors, zero item failures.
These are ten items, **not ten distinct categories** (two are SMGs).
The captured source process was 42580, thread 40096. Runtime pages are saved.
Actual Windows CRT formatting is used, including the exact native color format
and `%d` narrow integer format; unknown formats still fail explicitly.

`--card-ui-boundaries` also executes nine explicit synthetic visibility/value
cases. `native-ui-boundaries-20261004.json` replays saved pages with
`process_access: none`. Six nonempty visible outputs validate the local
presentation port. Invisible, non-boolean and wholly empty cases remain recorded
as converter evidence, not as implemented renderer filtering.

`native_card_model_read.py` bounds maps, chains, arrays, strings, cumulative rows
and total model reads. Fifteen reader tests cover malformed/Unicode/change
detection and singleton/source-field separation in
the reader. Optional header checks reject detected mutation; these do not make
a process-memory read atomic.

## Independent selected-card evidence

After the authorized restart, PID 36312 / SDK game thread 56000 (log `dac0`),
the reflected zero-parameter `OakPlayerController.OpenInventoryMenu` opened the
host inventory. Selecting equipped slot one displayed **Scattering Nadir
Stealth & Seek**, level 70. No item was equipped, inserted or edited by this test.

`live-native-slot-one-20261004.jpg` is the independent UI receipt;
`live-native-slot-one-20261004.json` reads the cached model with VM_READ only.
`native-complete-selected-20261004.json` reconstructs its exact original serial
offline using the **complete 88E2A4 constructor**, followed by model construction,
binding and filling. Passing that same item as the comparison context produces
**exact equality of all 10 exported string properties and all 27 display rows**
(including definition identities, flags and priorities). Receipt:
`selected-card-complete-comparison-20261004.json`.

Empty comparison had identical values but different comparison flags; the self
comparison run resolves that difference using native logic, without overrides.
Visible primary values are `602k x 5`, `84%`, `1.7s`, `8.7/s`, `5,483`;
secondary numeric values `+578%`, `762cm`; headline `26M`; fire text
`273k DMG/s | 40% Chance`. These observations are regression evidence only.

`native-complete-ten-20261004.json` also runs the complete serial constructor
for all ten fixture items: zero failures, 510 display rows, 462 converted rows,
ten completed model destructors. This is still offline original-code execution.

`native_sdk_card_probe.py` is a separate opt-in research probe. It checks the
observed game thread, rejects guests, gates native function hashes, constructs
detached identity/model storage, converts rows, and destroys owned allocations.
It never calls inventory insertion. Additional lifetime receipts in `native-sdk-lifetime/`:
E69CA9..E69D1A SHA256 `bfc0da2a7661a8f5f785a94a6f2ae2d54d5c0d89333506ac802a7b79a0fa67ed`;
20A8..20E8 SHA256 `7b0652ce5487ac59d2d731b69715d6a77a54ebcf2bcd221ea82f7ed66108978f`.

## Live detached SDK evidence

`live-sdk-preview-verification-20261004.json` compares the selected sniper's
live detached preview against the complete offline self-comparison build:
all exported model and converted UI fields match. Both native destructors
completed. The single preview took 36 ms including Python export and repeated
journal writes; this is not a pure-engine timing measurement.

`live-sdk-ten-verification-20261004.json` records ten more live previews with
both destructor completions. All non-comparison fields match the corresponding
offline ten-item build. Comparison fields were explicitly excluded because
the live run uses self comparison and that offline run uses empty comparison.
Individual recorded times were 18–70 ms, including receipt writes.

Before/after bridge reads retain the exact serial multisets and duplicate
counts: seven equipped and 63 backpack items. AFK configuration was restored
after the tests. Five mocked control-flow tests separately cover wrong-thread
and guest rejection, successful cleanup, fill failure and journal failure;
those tests are not ABI or native lifetime proof.

## Still unresolved

Owner-context caps, comparison context, complete firmware/loadout presentation,
all model property-to-UI bindings, sustained allocation/lifetime safety, and
broader independent selected-card parity. Eleven successful live previews are
not a leak or general live-safety proof. There is no production adapter yet.
No full-parity or release claim is justified yet.

Follow-on work in NATIVE_WIDGET_FIELD_BINDINGS.md binds twelve additional
source fields, separates the singleton headline consumer, and completes the
default price formatting/ownership path. A twelfth live detached preview
including price matches the expanded offline export with unchanged inventory.
