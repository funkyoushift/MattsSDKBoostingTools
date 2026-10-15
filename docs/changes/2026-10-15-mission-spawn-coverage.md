# Mission replay spawn coverage repair — 2026-10-15

## Problem and native evidence

FL4K replay often arrived at a distant map entrance. This phase supersedes the
spawn findings in [the earlier candidate note](2026-10-15-replay-spawn-and-fog.md).
Fog remains a separate optional setting, defaulting to Leave unchanged.

The actor lookup discarded explicit level-instance scopes by searching only Top.
Several objective types also omitted authored completion targets. Optional parent
branches could contaminate required section evidence, while DLC mission beginnings
used the destination map instead of the authored mission giver/departure context.

Extraction now respects explicit submap scopes, reads native hack/carryable/ECHO
targets, and derives optional ancestry separately from native execution flags.
Moving enemy/spawner origins remain scene proximity evidence, never completion
coordinates. Unconditional authored UI departures and mission-giver entry routes
provide station context. The last unique required completion in the preceding
main section can provide a start; it cannot cross a map-travel boundary or use
future/optional/parallel-conflicting progress.

Live native travel proved IslandHub and FTS_FL4K can receive the character without
completing the future computer/office unlock objectives. The before/after save kept
The Chase at checkpoint 16 with UseFlakComputer absent. Thus known same-campaign
future fast-travel UI conditions no longer force a distant arrival station, and
no future completion flags are written. Unknown, negative, compound and cross-pack
conditions remain excluded; DLC ownership/native guards still apply. A native
DestinationOnly UpperCity arrival also succeeded within 236 units of its authored
station. Send-only, generic Level and unreviewed portal types remain excluded.

## Changes and offline validation

- Builders: `tools/mission_lab/build_practice_catalog.py`,
  `build_selection_catalog.py`, and `replay_spawn_rules.py`.
- Regenerated SDK practice/selection/reference data. Native bookmark validation
  accepts listed prior catalog hashes only after unchanged native source hashes
  and timeline compatibility checks; captured mission/objective validation remains.
- 39 supported story/DLC missions / 506 main sections: 365 coordinate starts and
  141 native station starts; 39 additional coordinate starts, 185 station choices
  changed versus published baseline. All sections have authored location context;
  none uses an unresolved generic map-head fallback. This does not mean every
  remaining native station is close enough for every player's preference.
- FL4K: 11 missions / 93 sections, 58 coordinate starts and 35 station starts.
  The Chase hideout fallback now uses IslandHub, about 82 metres from authored
  context instead of about 523 metres. FL4K/Cowbell/Mandolin beginnings use their
  authored main-world entry context.
- 621 focused Python checks plus one independent all-506 source-provenance check
  passed. 39 transaction checks (including Epic encrypted-save roundtrip), both
  responsive desktop UI suites, 48 packaged runtime dependencies and 3,313
  packaged asset checks passed. Archive CRC and all 153 SDK source files match.
  These are offline/package checks, separate from normal encounter gameplay.

Rejected approaches: alphabetical/map-head fallback, pretending a future objective
was complete to unlock a closer station, treating enemy spawn origins as completed
interaction points, and using optional branch points as mandatory starts. The
specialized Bugbot service was unavailable; validation includes own review and
automated checks, not a claimed Bugbot review.

## Installation and live verification

Installed while BL4 was confirmed closed, 2026-10-15 10:03 local. Installed SDK
SHA256 `a98948b8e3becec4104ce5927e02c3f0636e307e12827d2ea6f6cf8abfc40eb2`.
SDK sources, packaged desktop resources and installed bytes agreed for this first install; see the final correction/install below.

Candidate desktop: `output/mission-spawn-candidate-2/win-unpacked/`.
Prior installed SDK is retained at
`output/replay-spawn-audit/installed-before-phase2-20261015-100323.sdkmod`.
Installation/package receipts and private replay journals/backups stay under the
ignored `output/replay-spawn-audit/` directory. Restore SDK only while game closed;
save rollback requires unloading the affected character first.

Practice catalog SHA256:
`d187e117494b3d0c8f6a3cc261f122cc350f521b3c57ebc0208da06adfa240af`.
Selection catalog SHA256:
`c896f2730298b3c2fe8644ab4829da861310fca77cb0ce318d84f9dea513f878`.

Post-install test 1 passed: The Chase/checkpoint 16 completed automatic character
unload, inactive save edit, reload, cross-map travel, IslandHub station arrival,
objective-boundary readback and mission tracking. No placement fallback or future
station-objective flag was used. Native position was within 235 units of the
authored IslandHub station. Preservation checks passed; fog Leave unchanged wrote
zero grids. Receipt: `live-result-Mission_Main_Harmonica2-16-leave.json` under the
ignored audit directory; before/candidate saves remain with its transaction.
Further DLC-entry/coordinate checks follow below.
The whole catalog has source validation, not 506 live gameplay tests. Remaining
encounter/interaction edge cases stay experimental. This repair adds no
Steam-only path assumptions; it is not a new live Epic gameplay test.

Public Windows 2.39.1 and Android 1.6.3 remain unchanged. No release/version bump
was performed during this phase.

## DLC opening correction and second install

The first production Harmonica0/0 attempt reached the correct main-world station
but failed objective-boundary verification: the native record had no GoToHarmonica
objective. It stopped and retained its backup. A bounded, separately recorded test
restoring the native saved `Active` status for that current objective passed the
full automatic transaction. This is not a future objective completion.

The builder now explicitly declares `restore_active_objectives` for the three
source-map DLC travel openings (Harmonica0, Cowbell0, Mandolin). The save editor
accepts this only at cursor zero, on an authored entry, within the selected
initial objectives and disjoint from past progress. Other selection edits retain
their existing initialization. Two added tests cover all three declarations and
rejection of invalid/future state. 85 targeted Python checks, five startup checks
and all 39 transaction checks passed after this correction.

The Chase/checkpoint 18 also passed the normal production automatic transaction:
character unload/edit/reload, map/station arrival, placement at the previous
UseFlakComputer completion (8299.392416,-29614.358372,27259.809649), grounded normal
movement verification, tracking and readiness. No fallback was needed. This is
one of the newly recovered coordinates, distinct from the native station test.
No objective was completed for either Chase test.

Final desktop is `output/mission-spawn-candidate-3/win-unpacked/`. Both package
audits passed again (48 dependencies; 3,313 assets); all 153 SDK sources and the
packaged SDK/helper match. Final SDK SHA256:
`93e08c2aec28cbec03eba67a04e44df38952497d2fe450b9603a74d71107c33c`.
Final selection SHA256:
`737398949c744b98a4ede39be65b0fa3c81ea681e6c782826d6322464375f801`.
Practice catalog and location counts are unchanged.

Installed at 10:13 local after Martin confirmed normal save/close and the game
process check confirmed it was stopped. Prior phase2 SDK retained at
`output/replay-spawn-audit/installed-before-phase3-20261015-101334.sdkmod`.
The initial combined install/restart command was blocked by automatic approval;
the separate checked SDK copy succeeded and the prior desktop was closed through
its normal window controls. Post-install production DLC-opening check follows.

## Final cross-map proof and desktop package

Two further native cases narrowed the entry failure: BL4 may omit an empty
objective list before its source map is loaded, and loading on the DLC destination
can naturally complete the travel opening before the requested source-map travel.
The desktop reader now treats an absent list as empty, never as active proof.
Only the preliminary check for the three declared DLC travel openings permits a
changed cursor/status; character identity remains mandatory. After station arrival,
the service performs one second automatic unload/edit/reload on the correct source
map. It regenerates the edit from the then-current inactive save (retaining current
gear), writes separate pre-refresh/candidate backups, and preserves the original
pre-replay backup/hash. All final disk/native objective checks remain strict.
No action is automatically retried after an uncertain outcome.

This final production-service check passed from Harmonica to World_P, including
both automatically bound character swaps, source-map restaging, strict objective
boundary, HUD tracking and ready/lease release. It restored Harmonica0/checkpoint0
at Sanctuary with Travel to Providence active. Private receipt:
`live-result-Mission_Main_Harmonica0-0-leave.json`, final job
`4ec8f954b5884ab187311d6b947dc90c`; original backup hash verified, separate refresh
backup retained. No manual picker input or temporary edit override was used.

Final desktop is now `output/mission-spawn-candidate-4/win-unpacked/`, replacing
candidate3. Packaged replay service bytes match the production source used by the
live check; packaged SDK/helper bytes match source, and installed SDK remains
`93e08c2aec28cbec03eba67a04e44df38952497d2fe450b9603a74d71107c33c`.
The reader/service-only follow-up required no further game restart. 41 transaction
checks pass, including source-map restaging with changed interim progress, current
gear retention, exact original rollback and loaded-character replacement rejection.
69 current selection/helper checks pass, with an added omitted-objective-list case.
Selection generation remains byte-repeatable; syntax and whitespace checks pass.

The three representative installed paths are verified: closer FL4K native station,
new preceding-completion coordinate, and cross-map DLC opening. Broader normal
combat/interaction coverage remains experimental; this is not proof of all506
encounters. Public Windows/Android versions and downloads are unchanged.

Final candidate4 packaged runtime (48 dependencies) and asset (3,313 files) audits passed. Desktop window identity verified as candidate4; game left loaded at the tested FL4K travel opening.

## Final location-only pass — gameplay testing stopped at Martin's request

Martin clarified that the method was proven and remaining effort should go to
location data. No further mission loads, character swaps or encounter tests were
performed in this pass.

The audit covered all 506 supported main sections, including the 141 remaining
native-station starts. Only three initial fallbacks exceeded 250 metres from
their authored reference. A bounded scan of all serialized waypoint records and
nested target fields found additional authored route markers; a proposed global
cross-mission actor fallback was unnecessary and was not introduced.

Data extraction now uses the explicit conversation node when one is authored,
rather than conflicting default locations for a moving NPC. This recovers the
Mr. Chew SootheChew and PlaceChewCollar completion points and hence the following
main-objective starts. Unconditional additional UI markers, including finite
display-radius settings, now supply scene context even when the primary marker
is not hidden. These are proximity evidence, never completion coordinates.

The first serialized MissionObjectiveAspect_Breadcrumbs route marker can select
a nearby native station when a preceding completion coordinate is missing. Its
explicit waypoint override is respected; multiple conflicting aspects or unknown
marker conditions stay excluded. Exact preceding-completion placement retains
priority. This provides approach context rather than defaulting to a section's
far-away end target. Twelve station-based starts use this source rule.

The station compiler also understands an OR of individually known, owned, positive
completed entry-route conditions. It retains authored branch order and supplies
only a supported prior branch, never future or unknown/negative facts. Mixed
AND/negative/unknown expressions remain excluded. This makes several closer
Shatteredlands entry/respawn stations available without changing replay execution.

Net changes versus candidate4's first data set: 28 section location choices
improved (27 station identities changed and two new coordinate starts; one section
has both). Coverage remains 39 missions /506 main sections: 367 coordinate starts,
139 native station starts. FL4K's 93 sections now contain 60 coordinate starts and
33 native fallbacks. No section lacks authored location context or uses a generic
unresolved map-head fallback. Remaining native fallbacks are intentional when the
previous completion has no unique static point. Rail-depot/1 and spatial-
accelerator/10 retain the nearest eligible native stations at about387m/289m from
their current references; the closer rail-depot station has an unreviewed mixed
negative condition, and no closer eligible spatial-accelerator station is present
in these source tables. No coordinate or condition result was invented to hide
those limitations.

Validation was limited to data consistency, source provenance, syntax/startup and
packaging:124 source/location checks and five startup checks passed. The all-506
provenance check matches every generated station reference/start coordinate to
its original hashed native JSON record and confirms past-progress ownership.
No new gameplay claim is made for these location-only changes. Full receipts:
`output/replay-spawn-audit/final-location-data-pass.json` and
`location-pass-final-receipt.json`. Previous data/SDK are preserved as
`pre-final-location-pass.json` and `pre-final-location-pass.sdkmod` there.

Final location SDK SHA256:
`9e32fbb0de09a5be5ce196ed7cc2c0aa6d7b179f26a27d16adeb4f3b760f8777`.
Practice catalog SHA256:
`04de7048793242fcc94e87cea710a97e46b4b94f52337ecc838b77bd10ad5fdb`.
Selection catalog SHA256:
`cf0d75c56c8995f63b12305e20017763303502e41aed3ac7092ca262fec5c29d`.
Candidate4's embedded SDK is updated to these exact bytes; desktop service,
character loader, fog, mobile APIs and public release versions remain unchanged.
Installation of this final location data is pending normal game closure; it must
not overwrite the SDK archive used by the running game.

## Final location update installed — 2026-10-15 11:00 local

Martin authorized unattended completion and game closure. The normal game pause
key did not respond. The current on-disk character save was copied and its hash
verified before requesting the game's ordinary window close (Alt+F4). The window
closed and the game process exited normally; no forced termination was used.
This was not an observed in-game Save & Quit operation. The save backup and its
receipt are retained privately under `output/replay-spawn-audit/`.

After confirming the game process was absent, the final location SDK was installed
and verified against the checked package/hash:
`9e32fbb0de09a5be5ce196ed7cc2c0aa6d7b179f26a27d16adeb4f3b760f8777`.
The prior installed SDK remains at
`output/replay-spawn-audit/installed-before-final-locations-20261015-110051.sdkmod`.
Receipt: `output/replay-spawn-audit/final-location-install.json`.

This supersedes the pending-install status above. The source package, candidate4
embedded package and game-installed SDK now agree. The matching desktop is
restarted; game remains closed. No further gameplay tests or public release were
performed. Location-data work and local installation are complete, with the
explicit native-fallback/normal-encounter limitations documented above.
