# DLC main sections and live bookmark checks — 2026-10-15

Martin asked for the same complete-route grouping in the DLC picker and live
exact-position bookmark checks in both the app and standalone SDK.

## Replay sections

The 18 DLC main missions already supported by save-backed selection now expose
61 main sections instead of 211 internal choices. Together with the 65 base-story
sections, the shared catalog contains 126 sections across 39 missions: 79 authored
coordinate candidates and 47 native station starts. All native execution groups
remain intact. This does not add previously unsupported bounty/side missions.

Boundaries are explicit native checkpoint/objective identities in
`mod_extracted/MattsSDKBoostingTools/mission_replay_sections.json`. PowerPyx's five
Ellie walkthroughs and the FL4K walkthroughs inform route scope, rather than being
used as game-state specifications. References and downloaded source hashes are
kept privately in `output/mission-guide/dlc/references.json`.

Examples include the full crime-scene investigation, escape-pod search, engine
restart, tower approach, sauna sequence and fortress assault. Switches, pickups,
intermediate enemies and return travel stay inside these routes. Bookmarks still
capture internal checkpoints that are absent from the main picker.

`mission_selection.py` applies the same reviewed boundaries for app and SDK. It
checks native identities, order and section ranges without changing definitions.
The investigation retains the previously tested evidence-table return anchor and
guards all interviews/scanning/collection/placement source identities. The FL4K
opener begins at Exit pod, after its hidden automatic arrival initializer; a rule
cannot skip a visible opening step. Generated station prerequisites only use
progress already before the selected boundary.

## Live bookmark defect and correction

The first standalone round trip restored the saved mission and reached the exact
recorded XYZ, but stopped as uncertain because K2_TeleportTo returned false.
Fresh native readback showed the requested position, unchanged objective states,
walking mode and gravity. No uncertain teleport was retried.

`mission_recorded_placement.py` now reconciles a returned false through a fresh
position readback within 10 Unreal units. It then performs the existing delayed
grounding and stability verification. A false result away from the target or an
exception still stops without another placement. Existing movement restoration
and pawn/component identity checks remain in force. Regression tests cover false
arrival, false rejection, exceptions and grounding/stability requirements.

## Live results

Both checks ran on the existing level-70 original character in solo Steam play,
A Zane to Kill For, native checkpoint 9. Each captured full-precision XYZ plus
the matching saved mission/world timeline, moved the character 500 cm away and
confirmed that displacement before initiating automatic reload.

- Standalone SDK: its real worker saved and loaded the bookmark. It selected the
  holding/original characters automatically, rebuilt the map, returned ready and
  released the lease. Five-second arrival error was approximately 0.00000131 cm.
- Windows app: the production renderer's Save/Load buttons, preload, IPC, save
  helper and full SDK bridge performed the round trip. Actions were not stubbed.
  The temporary driver used a separate app profile to preserve Martin's settings.
  Five-second arrival error was approximately 0.00000185 cm.
- Both matched the original character GUID and complete native objective-state
  hash, retained normal walking/gravity and verified the protected current save
  fields, including gear/levels. Both native receipts exercised the returned-false
  reconciliation and then passed grounding verification.

These are two live capture/move/reload checks at one checkpoint, not every
mission's playability proof or a live test of every possible progress rewind.
The saved timeline is not a bit-for-bit running NPC/world snapshot. Offline
worker/helper tests separately cover altered later progress and retaining gear
earned after a bookmark. Steam live evidence does not establish Epic live proof.

Private evidence is under `output/mission-guide/bookmark-live/`: sdk-fixed-result,
app-result, corresponding journals/native receipts, before/moved/after readbacks
and the final deployment receipt. Test controls are not packaged in either mod.

## Checks, packages and cleanup

- 140 focused Python checks pass, including startup/Quick Menu/no-BLImGui guards.
- 49 save-worker checks pass; 22 packaged/import checks pass.
- Electron panel checks pass with stubbed actions separately from the real live
  app check above. The packaged Windows renderer/worker and bundled SDK match
  the tested source/archive. Both SDK archives pass integrity checks.
- Updated standalone SHA256:
  `064d52c8715b6b0c797fc7f1a1f68ae93086e52468bcae3b523139ac6c1e0606`.
- Matching full-app SDK SHA256:
  `ec3abd387412123741246b34236f8df75a6aea84b1f5e36ff2e9811e5a8fea2d`.

With the game confirmed closed, restored standalone-only installation and updated
the primary workspace's `output/standalone-mission-selector/BL4MissionSelector.sdkmod`
and README. The full SDK is outside the active game's sdk_mods again. Temporary
probe controls and the two generated SDK test bookmarks were moved to the private
evidence folder; user bookmarks were preserved. The temporary app was closed and
the game was left closed. The prior installed 316f3a94 archive is retained at
`output/mission-guide/bookmark-live/before-dlc-bookmark-fix.sdkmod` for rollback.

Matching Windows output is `dist_electron/win-unpacked` in this implementation
worktree, with the full SDK also copied to the primary workspace's
`output/mission-selector-updates/MattsSDKBoostingTools.sdkmod`. Implementation root:
`C:/Users/mwenn/.codex/worktrees/mission-replay-release/product`, branch
`codex/mission-repair-dialogue-uvhm`. Primary checkout source was not bulk-merged.

Versions remain 2.39.1. No tag, GitHub release, upload, APK update or version bump
was performed. Ready for release preparation within the stated experimental
coverage; DLC encounters still have not each been played end to end.

## Published update

Martin requested publication. Released v2.39.2 with Windows/full SDK, standalone
SDK and Android1.6.4/build37. All13 published assets match local SHA256/size;
public rolling updater downloads and main README verified. See
[release verification](../releases/VERIFICATION_v2.39.2.txt) for source/package,
phone, CI and rollback evidence. Native replay behavior remains bounded by the
live checks above. The installed standalone and primary shareable copy now match
the released cc3d4856 archive; full SDK f6bca3d0 stays outside active sdk_mods.
