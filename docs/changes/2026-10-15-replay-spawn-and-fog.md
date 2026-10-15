# Replay station placement and optional saved-map fog — local candidate

Martin reported FL4K replay repeatedly placing the character at the map entrance.
He requested the preceding main objective's completion point, or an appropriate
nearby native respawn/save station, across the replay catalog. He subsequently
requested leave/clear/restore fog options, defaulting to leave unchanged.

## Evidence and changes

- Active source: `C:/Users/mwenn/.codex/worktrees/mission-replay-release/product`.
  Published Windows2.39.1 / Android1.6.3 remain unchanged. No release or version bump
  is authorized by this follow-up request.
- The generator previously selected the alphabetically first station when an
  exact waypoint was missing, and admitted send-only travel stations. It ignored
  useful required hidden substep locations and native station dependencies.
- `tools/mission_lab/replay_spawn_rules.py` and `build_selection_catalog.py` now
  retain exact preceding main completion waypoints first. Fallbacks minimize
  distance to authored section/substep locations using respawn/arrival stations
  only. Optional and persistent later-objective targets do not determine starts.
  Unknown, compound, negative, future or parallel-content station gates are
  excluded. No coordinates are fabricated.
- Packaged `travelstations.json`, `travelmaps_flat.json` and the source-derived
  mission catalog supply the locations. The selection manifest pins the station
  table SHA256; raw Map0 is not present here, so this is extracted-data provenance,
  not an independently re-extracted Map0/executable claim.
- Native mission/objective station dependencies are inserted only when owned by
  the selected past timeline. `mission_selection_state.py` supplies the exact
  completed objective/status and final endstate flag. All other protected save
  data remains checked. It never completes a future objective to unlock a station.
- Examples: The Rescue section6 avoids the FL4K office station, whose EnterOffice
  gate is still future, and selects the accessible fortress start with PlaceHands.
  Section22 uses Harmonica IslandHub with the earlier FL4K-computer gate retained.
- `mission_save_replay.py`, `external_bridge.py` and desktop
  `save_replay_service.js` now wait for a fresh world after travel, including
  same-map reloads. They verify station arrival before reporting readiness; a
  mismatched arrival can receive one grounded/collision-checked correction.
  Missing streamed terrain stops with a visible error rather than claiming ready.
  The 1500-unit arrival tolerance is an operational allowance, not a native rule.
  Lost replies never automatically resend placements.

## Catalog audit

All39 existing story/DLC missions and506 main sections remain.159 fallback station
choices changed;326 exact preceding-completion waypoints remain;180 sections use
native stations.70 sections require owned past objective gates. No section is
blocked for lack of a station. Five map-entry sections lack an exact section
location and explicitly retain their authored map-arrival reference (Cowbell0/0,
Harmonica0/0, Mandolin/0, Shatteredlands3/29, City2/11). These are not proven exact
objective coordinates. This work does not expand save-backed replay to every
side mission in the larger completion catalog.

Internal receipts: `output/replay-spawn-audit/{before,sections,summary}.json`.
Current manifest SHA256:
`a2c0116be7f7e2897d1cabf106a65e38c54afa8337db4254379dad390fe83564`.

## Fog option

The shared desktop/mobile replay panel offers Leave unchanged (default), Clear
all saved map fog, Restore all saved map fog. It applies to mission and bookmark
loads, not captures, completion runs or live resets. It is disabled during a run.

`mission_save_fog.py` edits only `gbx_discovery_pc.foddatas[*].foddata`. Native
records observed across14 maps use dimensioned base64 Zlib byte grids. Clear
fills the existing grids with255; restore fills them with0. The interpretation
  matches observed explored/unexplored grids but has not yet had a native visual
map check in this candidate. Dimensions, tags, codecs, metrics, pins, map icons,
gear and character progression are preserved. Unvisited maps are not fabricated;
the UI states that limitation. The old editor's hardcoded fog stub and its
discovery-metric resets were rejected.

Unsupported/malformed/empty fog records reject opt-in edits before save writing;
Leave unchanged skips fog processing and preserves it exactly. Decompression is
bounded and validates dimensions, EOF and trailing data. A full tagged-save
comparison allows only the intended pixel fields to differ. The desktop persists
the choice across restart/reconciliation and validates it before loading actions.

Read-only validation of the working original save passed all three modes plus
encryption/decryption roundtrips across its five native map grids. The actual SAV
hash remained identical; no game save was written. Private receipts/decoded data
stay under ignored `output/fog-save-audit/`, never packaged or committed.

## Validation and deployment

-608 mission/replay/startup Python checks passed (217 existing import deprecation
  warnings);39 desktop transaction checks passed, including Epic encrypted-save
  roundtrip and fog persistence/bookmark forwarding. Python/JS syntax passed.
- Responsive replay UI checks passed at360/800/1280px, including default fog,
  active-run locking and bookmark forwarding. Mission-view UI suite passed.
- A broader collection attempt encountered two unrelated missing ASD test-helper
  imports; the explicit mission/replay/startup suite above collected and passed.
- Local matched package, installation, mobile parity and live checks are recorded
  below as they complete. No new release is published by this work.

### Local package and installation

- Shared phone workspace parity passed:77 desktop methods,17 responsive routes.
  Updated shared mobile assets are generated locally; no new APK is published.
- Local desktop: `output/replay-spawn-fog-candidate/win-unpacked/` (public
  `dist_electron/` remains intact). Packaged dependency graph passed48 packages;
  source/resource audit passed3313 files. SDK CRC and153 source files passed,
  allowing the builder's documented LICENSE/THIRD_PARTY_NOTICES copies.
- SDK installed with game confirmed closed. SHA256:
  `7691fa0976a4048669fad6d7f86655c04af7124255ab832797ab9c6c84ef8937`.
  Prior installed SDK retained in
  `output/replay-spawn-audit/installed-before-20261015-085249.sdkmod`, hash
  `105f1735ca5fc2c0ac8dbfa7e926c3c1af2cc26a075aa5601a777db3cdf0a111`.
  Published2.39.1 root SDK separately preserved under
  `output/preserved-v2.39.1-sdk/`. Install receipt: `output/replay-spawn-audit/install.json`.
- Initial strict archive comparison flagged the builder's notice override;
  comparison against the documented builder inputs passed. No code/resource mismatch
  remained. Initial direct GUI-executable audit calls returned without output;
  waited processes with explicit log receipts confirmed both package checks.

### Native checks after installation

Priority correction: Martin clarified that fog was an additional request, not the
end of the main task. Continue the FL4K/catalog replay-spawn work; do not restart
fog work or treat its implementation as completion of the spawn audit.

- Fresh game PID21788, replay session `a1dd4a9c71cd4fd5b408de147136b78b` loaded
  the exact candidate SDK hash above. Solo lobby and no active replay lease were
  checked before each run. These IDs are historical evidence, never reusable
  live handles.
- Production service with packaged Python/codec completed automatic unload,
  backed-up inactive edit, original reload, same-map refresh, station arrival and
  mission-state checks for The Rescue/22 (Talk to FL4K). It naturally arrived at
  `Harmonica_P.FT_Harmonica_IslandHub`; no station correction was necessary.
  HUD showed Talk to FL4K at Providence Island.
- Second run completed The Rescue/6 (Rescue FL4K) with cross-map travel to
  `VolcanoFortress_P.FTS_VolcanoFortress_Start`. No station correction was needed.
  HUD showed Rescue FL4K / Kill Tediore in Tediore FOB Bravo Lima4.2. This proves
  two setup/arrival paths, not normal fight completion or all506 encounters.
- First run explicitly selected Clear fog: five native grids were edited, and
  post-load disk readback retained all16384 pixels at255 in each. The runtime fog
  material overlay and teleport reveal tour were both disabled. Second run used
  Leave unchanged and recorded zero fog edits. Save backups remain per run.
  Fog pixel interpretation still needs a native map visual check: M/Tab input
  did not open the map during this bounded attempt. No visual success is claimed.
- The private integration journal and original backups are under
  `output/replay-spawn-audit/live-transaction/`. Both runs reached ready and
  automatically released their leases. A post-ready station query was rejected
  because its lease was already closed; this was not a replay failure. Its
  diagnostic may remain as the bridge's last-error string until a later action.
- Game left loaded at the second section; no objectives completed by automation.
  The clear-fog test remains applied to the five existing map grids, with original
  pre-test fog retained in the first run's `before.sav`. Gear/progression protected
  checks passed during both edits. The user can choose Restore fog on a later
  replay, or restore the pre-test backup while that character is inactive.

### Resumed spawn work

- Distance/provenance audit now separately covers all 11 FL4K missions /93 main
  sections:52 preceding-completion coordinate starts,22 selected-target station
  references,12 required-section references,6 earlier-section references and one
  unresolved exact-location map-arrival fallback. Internal full-catalog receipt:
  `output/replay-spawn-audit/distance-audit.json`.
- Some nearest eligible stations remain far from the authored target, including
  The Chase's hideout sections. The closer IslandHub station requires the still
  future UseFlakComputer objective there. Do not fake that future completion just
  to select a closer station. These remain candidates for better previous-start
  data; a valid source-backed station is not proof of an ideal practice start.
- Third native run: The Rescue/13 passed automatic save reload, native RS_Crane
  arrival, grounded placement at the preceding ReachOffice completion coordinate
  (56519.337908,33095.523487,1548.353534), movement verification, mission tracking
  and readiness. No station or placement fallback was used. Fog was explicitly
  Leave unchanged (zero edits). This checks the coordinate path in addition to
  the two native-station paths above. No combat completion is claimed.
- Receipt: `output/replay-spawn-audit/live-result-13-leave.json`; the private
  production-service journal and pre-edit save backup remain under
  `output/replay-spawn-audit/live-transaction/`. Its lease released normally.
  Game is now left at this third section, superseding the earlier location note.

## Remaining proof and rollback

The whole506-section catalog has source/data validation, not506 live encounter
tests. Representative FL4K native-station and prior-waypoint loads, encounter
progression and fog visual/save/reload checks remain required for gameplay claims.
Epic platform paths remain in the existing tested implementation; these changes
add no Steam-only save/path assumptions. Offline codec parity is not a new Epic
gameplay test. Preserve the prior SDK and published build artifacts; restore the
SDK backup only while the game is closed. Replay save backups retain pre-edit fog
as well as mission/character data.

## Superseding spawn repair

The later [mission spawn coverage repair](2026-10-15-mission-spawn-coverage.md) supersedes the earlier distance/gate findings above, with 365 coordinate and 141 native-station starts and the closer same-campaign native-arrival policy. See that note for current installation and proof status.
