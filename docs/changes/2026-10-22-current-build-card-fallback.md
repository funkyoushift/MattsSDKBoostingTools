# Current-build native card repair and serial fallback

## Current status: Steam native cards verified in game

After the offline qualification below, the SDK was packaged as a local test
candidate (SHA256 `fc82da811ee722a321a8e7076d8ee3ef4d23db80e4bc6fc3d0141e98fbe4bcbe`).
The published v2.39.6 SDK and Steam SaveGames folder were backed up under
`C:\src\MSBT-Workspace\local\steam-card-live-test-20261022` before replacing
the local Steam SDK; the Steam game was exited through its own Quit Game flow.
The relaunched game's bridge reported the candidate SHA and one host player.
In unpaused solo gameplay, `read_equipped_serials` returned nine items and
`native_card_preview` returned a full `native-standalone-widget-v1` for an
equipped sniper, shield and class mod. The shield returned three primary and
three secondary entries; the class mod returned 102 primary and four secondary
entries. The game remained running after all three calls. No serial was added,
removed or sent. This proves these three live Steam card constructions, not
all card types or Epic execution.

The shield's returned widget was captured locally and passed through the
desktop `native_card_capture` renderer. It produced an 819 × 975 PNG with no
renderer warnings; visual inspection showed its name, shield stats, effects,
firmware, red text and price. The widget JSON and PNG are kept only in the
private local test backup directory. `test_live_native_card_capture.js` is a
manual integration utility that accepts a local widget file and writes a PNG;
the package excludes this test script.

After source and renderer checks passed, a local v2.39.6 installer and portable
candidate were built with `tools/build_electron_beta.ps1 -Installer`. Its
packaged runtime audit checked 48 dependency packages, its asset audit checked
3,315 files, and the embedded SDK hash matched the live-tested candidate.
The unpacked desktop executable's `--smoke` check exited 0. These local files
were not published. The plain portable-only build path failed because it did
not produce `resources/app-update.yml`; the installer build produced that
required updater file and passed the full package checks. The installed public
desktop app was not replaced during this pass.

## Native mapping and offline evidence

The missing historical Steam executable was recovered into the isolated local
reference folder and verified against SHA256
`9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0`.
This resolves the historical-binary blocker recorded below. Strict comparison
against each installed current executable recovered all 26 card function spans
uniquely: 9,221 instructions per store match after only branch/RIP relocation
normalization, with 1,541 consistent reference targets and no conflicts.
Model and owner constructors identify their vtables and destructors; the full
20,881-byte final widget consumer matches. No field offsets, constants or
non-relocation instruction bytes were normalized or guessed.

`native_card_builds.py` now maps `steam-26007962` and `epic-6d531d91` through
exact addresses and full-span hashes, while keeping unknown builds closed.
The existing exact executable identity gate in `NativeInventory` remains.
Production detached-widget preview keeps the native constructors, formatting,
copy and cleanup paths. Research-only model export remains restricted to the
historical Steam profile because its FName-pool read is not requalified.
`native_preview_service.py` reports revision `native-card-profiles-20261022`.

The compact checked-in evidence is
[CURRENT_CARD_PROFILES.json](../native-cards/CURRENT_CARD_PROFILES.json).
`tools/verify_native_card_profiles.py --profile steam-26007962` (or
`epic-6d531d91`) independently checks the old reference passed as `--steam` and
current target passed as `--epic`. Each passed all 26 span digests, instruction
and shared-reference equivalence, 52 damaged-gate checks and four constructor
vtable checks. Complete research receipts remain in
`output/testing/current-card-qualification/`.

Final focused offline checks: 47 tests and 250 subtests passed, covering current
profile mappings, rejection before card binding for every damaged gate, mapped
model cleanup, widget success/failure cleanup, price cleanup, and Quick Menu.
The desktop `npm run check`, `npm run test:card-layout`, and
`npm run test:game-update` checks passed after the source changes. Python
compilation passed. The native mapping checks are offline evidence;
the separate Steam live execution above does not establish Epic behavior or
guest-session support. No release was published.

## Initial diagnosis and safe fallback (historical)

The current Steam/Epic host inventory profiles do not qualify native item-card
construction. `native_card_builds.py` still admits only Steam 25372571 and Epic
4845623. `native_sdk_card_probe.run` rejects the newer profiles before binding
card functions or constructing detached card data. This is an explicit safety
gate, not a desktop rendering failure. No native gate was removed by this repair.

The shared desktop item-card view now explains this particular unsupported-build
error and displays the original serial as selectable text. Case and characters
are preserved with `textContent`; the fallback produces no name, artwork or
stats. Existing catalog screenshots and successful native/cache responses keep
their existing paths. This is a usable serial fallback, not restored card parity.

Changed: `electron_poc/item_card_view.js`, its view regression, a focused
`test_item_card_unsupported_build.js`, and `tools/tests/test_native_card_probe.py`.
Offline probe/profile checks passed: 29 tests and 132 subtests. Python compilation
and JavaScript syntax checks passed. The focused real Electron renderer test
passed for both current build identifiers with mocked unsupported responses,
including serial case and markup preservation and no invented name/image.
The existing broader `test_item_card_views.js` initially stopped at `missing preview
boostSerialText` because the AFK handoff inserted a control between the serial
field and its preview. The preview existed; the test assumed direct adjacency.
The preview now has an exact field marker, and the full Electron card-view test
passes. No game was launched,
inventory changed, package deployed, or version changed by this work.

The initial diagnosis below is superseded by the recovered native mapping and
Steam live check above. At the time, native qualification needed recovered
current-build implementations for
the 26 old gated spans (including the 20,881-byte final widget routine), their
referenced functions/data, allocation layout and ownership cleanup. The existing
read-only comparison tool requires the historical Steam Win64 executable hash
`9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0`.
The historical Epic equivalent is
`764a4bb5403a2619a0be627de5a738e23ea021e8672f7f0e7a536697d4a06719`.
Hashes and addresses alone cannot recover changed instructions. See the older
[native profile evidence](../native-cards/EPIC_CARD_PROFILE.md). No inferred
selection/arithmetic/formatting rules were introduced. Live Steam/Epic cards
remain unverified and unsupported on these current profiles.

Rollback restores the previous desktop view; native support remains gated in
either version. This change is source-only until separately packaged/deployed.

## Follow-up read-only qualification

`output/testing/current-card-qualification/blocker.json` verifies the installed
Steam SHA256 `ba75f7c2874b16efb5536a5c0cc28918a03efd3e55d790d2e4db57de0c3a353a`
and Epic SHA256 `6d531d91011ae0d67ac461a3cacabc99993c279bf325dfe70ff1af00ec43c87e`.
All 26 historical card spans differ at their prior RVAs in each executable.
This establishes that old mappings cannot be reused, not that equivalent
functions do not exist elsewhere in the new executables.

The historical Epic comparison receipt survives in the `epic-native-cards`
worktree output and records old instruction reference offsets/targets and
hashes, but no raw instruction bytes. The old `item-cards-v2-13-0` research
worktree directory contains only its name marker. A preserved integration
runtime capture has 2,688 data pages and zero complete historical card code
spans. The preserved offline replay tools load original code from the old
executable; they do not embed those instructions. These artifacts cannot
establish current model/owner allocation layouts, widget field ABI or price
ownership lifetime. Requalification requires either recovering the historical
bodies for comparison or independently recovering the current native pipeline.
No pattern-derived address or changed native gate was installed.

Independent current-Steam extraction subsequently recovered the generated
`OakWidgetData_ItemCard` registration at RVA `0xb8a77d8`, its 78 descriptor
entries at `0xb8a7550`, and declared size `0x608`. Raw bytes and current hash are
in `output/testing/current-card-qualification/current-widget-metadata.json`.
Key non-boolean destination offsets match the historical documented widget:
Name `0x238`, Level `0x190`, ManufacturerName `0x280`, primary/secondary/tertiary
arrays `0x338/0x358/0x378`, and Price `0x570`. This is extracted destination
metadata, not proof of the current model constructor or consumer ABI.
The current `ItemCardData` property belongs to `OakUIRewardDisplay`; it does
not establish an inventory-card access path. A reflected already-built widget
would still require an observed owner instance and exact serial association.
