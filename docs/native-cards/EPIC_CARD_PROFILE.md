# Epic native item-card test profile

Date: 2026-10-08. **Offline-verified candidate; Epic live execution is unverified.**

## Executable evidence

Both files were read directly without loading or executing the game:

- Steam build 25372571: `OakGame/Binaries/Win64/Borderlands4.exe`, SHA256
  `9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0`.
- Epic manifest `Oak2-RE_Games_Oak2_Patch_Epic-4845623`, same relative EXE path,
  SHA256 `764a4bb5403a2619a0be627de5a738e23ea021e8672f7f0e7a536697d4a06719`.
  The root-level Epic EXE is a launcher, not the analyzed game executable.

`native_card_builds.py:EPIC_FUNCTIONS` records every Steam/Epic RVA, exact span
length and both SHA256 digests. These are recovered executable addresses, not
inferred item selection, arithmetic, naming, or formatting rules.

`tools/compare_native_card_builds.py` finds byte-identical instruction layouts
after masking only relative branch and RIP-relative address encodings. Registers,
field offsets, constants and other instruction bytes must match. Internal branches
must preserve their target offset. The final 26 sections contain 9,221 instructions
and 1,541 consistent referenced-address correspondences. The full private discovery
receipt is `output/epic-card-research/comparison.json`.

Tiny deleting destructors match thousands of generic wrappers; the first search
result is not sufficient. Model constructor Steam `56D3CCA` / Epic `56E544A`
references vtable `B99E210` / `B98A050`; slot zero identifies destructor
`8E1AA38` / `8E1FA60`. Owner constructor `58CF8C4` / `58E0C0A` references vtable
`B9B7700` / `B9A3530`; slot zero identifies `575204C` / `57637CC`. The price thunk
`5C4B4F8` / `5C59D5C` is resolved through its already-matched body target.
The formatted-text vtable `9E12790` / `9DFE790` comes from matched RIP references.

`tools/verify_native_card_profiles.py --steam <Win64 EXE> --epic <Win64 EXE>`
independently checks full-file hashes, all 26 span hashes, instruction equivalence,
branch/reference correspondence and constructor vtable slots against the files.
No native game function is executed by either tool. The 52 damaged-span hash
checks supplement runtime control-flow tests; they are not live parity evidence.

## Runtime changes and boundaries

The existing direct-inventory profile detector selects the exact Steam or Epic
build. Card gates are then checked against that profile before any card native
function is bound. Every function address and both ownership-vtable checks are
resolved through a strict mapping; missing entries and unknown builds fail closed.
Steam addresses and hashes remain unchanged. Thread, active-world, serial, bounds,
allocation-guard and cleanup checks remain. Preview does not insert items.

Epic support covers production widget preview (`export_model=False`), including
the empty comparison, price, final widget and cleanup. The separate research-only
model/definition export still references a Steam FName pool, so Epic requests for
that path explicitly fail before construction. It is not used by the editor.

The status action identifies this package as `epic-4845623-trial-20261008`.
This identifier establishes which card service loaded, not successful rendering.
`build_profile` is only set after successful native output and resets on a new
service session. The checker distinguishes installed archive, loaded revision,
and a completed Epic native card; cached desktop images alone are insufficient.

## Validation and test handoff

23 control-flow/cleanup/status tests pass, including Steam/Epic price ownership and
widget cleanup, unknown-build rejection, and all 52 bad-profile-gate cases before
card-function binding. Five profile-mapping tests and five no-BLImGui startup/
bridge tests pass. Python syntax checks pass. These are offline tests.

The local SDK test archive retains public version 2.30.2 and contains only the
four modified/new card runtime modules over that release. No version bump,
GitHub release/upload, game launch or local game-file replacement is
performed by this work. Package comparison and receipt are retained with
`output/epic-card-research/`.

The final SDK SHA256 is
`816602ba8cce115775911e934b492b799d4c5f884d09059a557dbde18bce3669`.
The downloaded public SDK payload was compared byte-for-byte: exactly three
existing card modules change, one profile module is added, and every other entry
is preserved. The initial source-built archive differed only in line endings
outside the intended modules; it was replaced with the exact published baseline
plus the four card modules. All 71 packaged Python modules compile.

DJBP must check his Epic EXE hash, install the candidate while the game is closed,
restart and confirm the loaded revision, then test a known item and a changed
editor serial. Check a weapon, shield, grenade and class mod including firmware,
repeat after changing level, and verify inventory is unchanged by previewing.
Record exact serials, card screenshots and errors. Do not call live compatibility
complete until this succeeds. Rollback restores the previous SDK archive with
the game closed, followed by a restart. No public release has been made.
