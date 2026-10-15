# Main-objective replay and exact bookmarks — 2026-10-15

Martin clarified that speedrun sections must include travel from the preceding
objective, with internal checklist steps played normally. Smaller practice points
belong in bookmarks. This applies to both the app and standalone SDK.

## Main sections

Read the supplied Game8 mission index and all21 linked walkthroughs. The index
covers the base story, not the newer DLC. Mapped its65 main headings to explicit,
checked native mission/objective identities in mission_replay_sections.json.
The guide supplies section scope/labels; coordinates, native states and progression
still come from extracted game data. Downloaded guide HTML and source hashes are
private under output/mission-guide, not included in SDK/app packages.

mission_selection.main_groups now uses this reviewed map for the21 story missions.
It verifies ascending native checkpoints and the selected native objective at each
boundary. A mismatched definition fails instead of silently selecting another
step. Full native mission groups remain intact for execution and bookmarking.
Sections expose their ending range, so build_selection_catalog finds the final
required completion in the preceding section rather than using that section's
first interaction as the next spawn. For example, Her Flaming Vision now has three
main choices at native0/8/22, including the full Drilldozer sequence and the journey
through Mudmouth to the Queen, rather than separate internal fight/switch choices.
The existing source-guarded Mandolin crime-scene section remains as agreed.

Generated selector data:39 missions,276 default choices:65 guide-aligned base-story
sections plus211 existing DLC choices. Existing DLC boundaries were preserved;
no claim that those211 are guide-reviewed. All underlying objectives remain in
mission_practice_catalog.json. Bookmarks may target internal checkpoints that do
not appear in the main picker. Legacy reviewed Mudmouth/Queen save routes retain
their mission-wide fallback prerequisites independently of picker visibility.

## Bookmarks

New captures read the possessed player's full-precision XYZ and current native
mission checkpoint/active-objective identities, requiring standing on foot and
finite coordinates. The shared save helper captures the matching saved missions,
world_state and timed_facts timeline. Existing autosave/capture-change guards stay
in place; a moving or changed character does not produce a misleading bookmark.

Loading uses placement=exact with no waypoint ground projection or station fallback.
The native placement check uses a10-Unreal-unit (10cm operational tolerance) arrival
bound for exact bookmarks, versus150units for general waypoint starts. It never
retries an uncertain teleport. Current gear, levels and other unowned character
fields are preserved. This is a saved mission/world timeline plus exact position,
not a claim of a bit-for-bit running-world/NPC snapshot.

Old native-station bookmarks still load as before and are labelled spawn station;
new captures show exact position in both UIs. No invented coordinates are added to
old bookmarks. Desktop controls/text, standalone menu and bundled README were
updated together. The native bookmark handler, placement and section definitions
are shared between the full app SDK and standalone package.

## Changed components

- mod_extracted/MattsSDKBoostingTools/{mission_selection.py,mission_replay_sections.json,
  mission_selection_states.json,mission_save_replay.py,mission_recorded_placement.py}
- tools/mission_lab/build_selection_catalog.py
- electron_poc/{renderer.html,save_replay_service.js,save_replay_panel.js}
- standalone_mission_selector/{menu.py,README.md}; root README local-update note
- Relevant selection, bookmark capture, placement, worker and package tests

## Validation and deployment

152 focused Python checks,49 Node worker checks,21 packaged standalone/save checks,
1 backend/bridge import check, and the Electron replay-panel check pass. The UI
check uses stubbed actions. Tests include complete native-graph preservation,
source-boundary mismatch rejection, precise XYZ capture, movement rejection,
cross-map exact bookmark reload retaining later gear, old station bookmarks, and
stricter exact-position arrival checking. Initial test failures were stale expected
internal menu indices and using Node instead of Electron for the panel test; those
were corrected. All Python sources compiled before packaging.

Both archives passed integrity/content checks. Windows app.asar UI/worker, bundled
save helpers and bundled full SDK were compared directly with current source.
No new native/live gameplay test was run for these65 sections or the new exact
bookmark round trip. The earlier live evidence-table spawn and Martin's normal
three-item placement/advancement confirmation remain recorded separately.

Standalone316f3a949f6cb6d56465718b16975cee0391cc5ea1ad7bb41bc6c4198b4c2927
(40,483,836bytes) is installed and matches the primary workspace's shareable
output/standalone-mission-selector/BL4MissionSelector.sdkmod. Verified game process
absence before replacement; game left closed. Rollback is the exact prior installed
f43fd658 archive at output/mission-guide/before-guide-bookmarks.sdkmod. Receipt:
output/mission-guide/install-guide-bookmarks.json. Full MSBT remains outside the
game's sdk_mods while standalone is enabled.

Full app SDK0142d03e8858b69d01ef78faf307002afe1daeec5da3990a14aea0de12003c60 is
bundled in the matching local Windows build at dist_electron/win-unpacked in this
implementation worktree and copied to the primary output/mission-selector-updates
folder. The Windows build is packaged, not installed over Martin's desktop app.
Implementation root: C:/Users/mwenn/.codex/worktrees/mission-replay-release/product.
The primary source checkout's unrelated dirty work was preserved. Public versions
remain2.39.1; no release, tag, upload or APK/version update was made.

Remaining: live exact-bookmark save/move/reload check; guide/confirmed main-section
boundaries for DLC rather than guessing them from checklist labels. Preserve the
main-objective scope instead of returning to per-switch or per-wave selectors.


## Follow-up completed

DLC grouping and both live exact-bookmark checks are completed in
[the follow-up entry](2026-10-15-dlc-main-sections-and-bookmark-verification.md). The installed standalone is now 064d52c8;
its matching Windows build is packaged. This supersedes the pending items above.
