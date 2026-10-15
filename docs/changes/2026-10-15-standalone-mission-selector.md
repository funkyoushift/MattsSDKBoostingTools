# Standalone console mission selector — local preview

Martin requested extracting mission selection from the desktop app into an
independent BL4 SDK mod controlled through the in-game SDK command console.

## Implementation and behavior

`standalone_mission_selector/` provides the `mission_select` command, a private
game-thread transport, a hidden local worker and installation/usage instructions.
`tools/build_standalone_mission_selector.py` builds a single
`BL4MissionSelector.sdkmod`. No separate MSBT, Python or Node installation is
required; the BL4 Python SDK remains a prerequisite. The worker bundles Node
v26.3.0 and the game-side save helpers vendor pure-Python PyYAML6.0.3; redistribution
licenses and existing project credits are included.

The existing production replay transaction and save codec are reused. The
package has an inert private core initializer, narrow host/travel adapters and
its own camera hook identifier. It does not start the full MSBT bridge, desktop,
mobile service or Quick Menu. Commands select a numbered campaign mission/main
objective, start automatic replay, inspect/stop/restore a transaction, save/list/
load bookmarks, and toggle dialogue skipping. Fog defaults unchanged. Save edits
retain equipment/levels and rewind the dependent mission timeline. Existing
solo-host, second-existing-character, original-character identity, account and
native-build guards remain in place.

Data matches the final location build:39 story/DLC missions,506 main sections,
367 preceding-completion coordinate starts and139 native-station fallbacks.
Console objective numbers are1-based visible main sections, mapped to the
original hidden checkpoint indexes; subobjectives are not exposed as selections.

Native operations run on the game thread. Save parsing runs off that thread;
the worker communicates over authenticated loopback with an explicit action
allowlist. Requests that cannot be confirmed are not automatically resent.
Settings, native journals, transaction backups and extracted runtime stay under
SDK settings/`BL4MissionSelector`, separate from full MSBT.

## Compatibility boundary

The full MSBT bridge starts on package import, even when its mod is later
menu-disabled. A menu-disable-only coexistence instruction was rejected during
review. This preview refuses replay/dialogue controls if full MSBT was imported
or remains enabled. Close the game, temporarily move the full
`MattsSDKBoostingTools.sdkmod` out of `sdk_mods`, then install the standalone.
Return to MSBT by closing the game and exchanging those packages. Neither
package's saved settings/backups are deleted. The desktop app can remain installed.

## Validation and limits

- All packaged Python sources compile; archive CRC and bundled runtime file
  hashes pass. Save helpers and their YAML resource import directly from the
  SDK zip, without relying on loose build-machine files.
- `python -m pytest tools/tests/test_standalone_mission_selector.py tools/tests/test_quick_menu_no_blimgui.py -q`:
  **11 passed in31.90s** (6 standalone checks plus5 startup regressions).
- Tests cover all506 visible selections, command routing/confirmation, package
  imports, Windows redirected Documents resolution, authentication/action
  rejection, and enabled/imported-but-disabled full-MSBT conflicts.
- The real bundled Node worker completed a transaction against synthetic
  encrypted Epic-account saves using the actual vendored save helpers/codec.
  Equipment/experience and the exact original encrypted backup were preserved;
  automatic swap/travel/placement used simulated native-game responses.
- This is **offline transport/save proof, not a live BL4 console/gameplay test**.
  The new standalone package is not installed into the game. It retains existing
  Steam/Epic routes but adds no new live Epic proof. Wider generated encounter
  behavior and native-station fallback limitations remain experimental.
- During implementation an import-smoke fixture lacked SDK `ENGINE`/`get_pc` and
  Unreal `find_class`; the fixture was corrected and the full suite rerun. A
  failed multi-target patch validation changed no files and was reapplied cleanly.

Artifact: `output/standalone-mission-selector/BL4MissionSelector.sdkmod`,
40,511,819bytes,187 files. SHA256:
`2562030b5dcf7f08c24e8e18d999469ab7cb4d75ae29d84e5b7665cffc593a26`.
Build receipt: `output/standalone-mission-selector/build-receipt.json`.
Base full SDK SHA256:
`9e32fbb0de09a5be5ce196ed7cc2c0aa6d7b179f26a27d16adeb4f3b760f8777`.

The artifact, README and receipt are also copied to the primary workspace's
matching output directory for a stable local handoff. Existing game-installed
MSBT SDK and desktop candidate are unchanged; the game remains closed. No public
release, tag, upload, app/APK version or main MSBT SemVer change was made.

## Usage

See `standalone_mission_selector/README.md` for installation, rollback and commands.
For example:

```text
mission_select list --campaign fl4k
mission_select objectives --campaign fl4k --mission 3
mission_select play --campaign fl4k --mission 3 --objective 1 --yes
mission_select status
```

Close the console after starting so the game can process loading. The next
bounded native check is console registration, one catalogue command, one replay
and dialogue enable/disable in a standalone-only session. Do not repeat a
mission-by-mission survey to validate this frontend extraction.

## Standalone installed and live checks — 2026-10-15

Martin explicitly requested disabling MSBT and testing the standalone. With BL4
closed, the installed full SDK was moved intact to
`output/standalone-mission-selector/installation-20261015-113033/MattsSDKBoostingTools.sdkmod`.
Its SHA256 remains9e32fbb0de09a5be5ce196ed7cc2c0aa6d7b179f26a27d16adeb4f3b760f8777.
57 native save files were copied with verified hashes before the test; the
private inventory of backups is retained there. Full MSBT settings were untouched.

The first live startup exposed the installed mod manager's numeric-only version
parser: `2.39.1+local` raised ValueError. The standalone metadata now uses the
unchanged numeric base2.39.1, retains its local-preview title, and a focused
regression verifies the dotted-integer restriction. This is not a public version
bump. The corrected package imported and its enabled command registered normally.

Live console tests in the Steam game, with full MSBT absent:

- `mission_select list --campaign fl4k` listed all11 missions.
- `mission_select objectives --campaign fl4k --mission 3` listed19 main sections.
- A named bookmark of the active FL4K opening saved successfully.
- `mission_select play --campaign fl4k --mission 3 --objective 1 --yes` completed
  the automatic holding/original character swap, inactive save edit, Harmonica
  map travel, nearby station check, coordinate placement and original HUD
  tracking. It reached ready in about34seconds. Native readback and the HUD
  showed The Chase / Soothe Mr. Chew at Chamber Pavilion; Mr. Chew was present.
  The transaction verified its encrypted backup and preserved unowned character
  data. This does not prove completing this interaction/encounter normally.
- Dialogue on/readback showed185 native completion requests and184 observed
  native thread ends. The test made no mission-complete/objective-complete calls.
- Expanded console output is visible by pressing the console key twice.
  A test call through Kismet ExecuteConsoleCommand did not route SDK Python
  commands (it reported unrecognized); actual UI console submissions worked.

The cross-map bookmark return exposed an existing shared transaction ordering
problem. The bookmark snapshot correctly had Harmonica0 / gotoharmonica Active.
Loading that original on Harmonica immediately completed that travel objective;
the subsequent return to World_P then failed strict boundary verification.
The captured snapshot and loaded disk record confirmed Active versus completed;
this was not stale-disk capture. It was not marked ready.

`electron_poc/save_replay_service.js` now applies the existing single inactive
restage cycle after target-map arrival for cross-map bookmarks. Only the initial
wrong-map verification allows early objective progression; final verification
remains strict. Same-map bookmarks retain the shorter sequence. Distinct native
call receipts, exact holding-character guards, encrypted pre-replay backups and
one-time restage backup are retained. Two regression cases simulate native
wrong-map progression and verify corrected progress, unchanged original backup,
and exactly two swaps only when needed.

Validation after the correction:43 Node replay tests passed;11 standalone/startup
checks passed in31.49seconds. The shared source repair is included in the new
standalone bundle; the previously installed full MSBT package/desktop candidate
has not been rebuilt with it. Full-MSBT/public release status is unchanged.

The corrected standalone SHA256 is
7631aa0da63ca7791145a292010a2c1eac1afea376faa0ccc4da07e32f408356
(40,511,907bytes). It was installed with the game closed; final cross-map bookmark
retest is pending in the restarted game. The original full SDK remains outside
the game mod folder for rollback. First-session log and failed bookmark journal
are retained under `output/standalone-mission-selector/`.

## Final installed verification — 2026-10-15 11:49 local

The correction passed in-game. The full MSBT desktop app was closed during the
test and its SDK remained absent. The corrected standalone again loaded The
Chase / Soothe Mr. Chew on Harmonica at its coordinate start. The transaction
reached ready and its journal was saved as `live-forward-replay.json`.

Loading the original bookmark from Harmonica then returned to World_P's saved
Heart of the Mountain station, performed exactly the bounded target-map restage,
and reached ready with the original character, strict live/disk objective
verification and the lease closed. Both `bookmarkMapRestage` and `entryRestaging`
are true in the final journal. The bookmark's captured Harmonica0 travel
objective passed verification after the refresh, instead of remaining completed
as in the failed first attempt. This supersedes the pending-retest statement
above. Final journal: `live-bookmark-reload-corrected.json`; log:
`live-final-session.log`; compact evidence: `live-verification.json`.

Installed, built and primary-workspace SDK copies match SHA256
7631aa0da63ca7791145a292010a2c1eac1afea376faa0ccc4da07e32f408356.
The game is left open with the standalone enabled, the original character on
World_P, and the desktop closed. Dialogue defaults off after the last restart;
its earlier live native skip counters are recorded above. Settings, bookmarks,
original SDK and verified character-save backups are retained. No release was
published. Remaining limits are normal encounter progression (including Mr.
Chew), broader mission coverage and new live Epic proof; this test establishes
standalone operation, save loading, placement and bookmark return, not every
mission's gameplay behavior.


## Random ten-objective acceptance run — 2026-10-15

Martin requested ten random main-story objective loading/spawn checks with the
full MSBT disabled. Frozen sample seed:14201549870818586911; uniformly choose ten
distinct story missions, then one visible main objective per mission. Plan and
per-case native observations/journals are in
`output/standalone-mission-selector/random-story-10/`; no rerolls.

The checks independently inspect the loaded original character, native mission
cursor and active objective facts, tracked mission, target world, actual grounded
pawn position versus the authored preceding-completion coordinate and resolved
floor point, closed replay lease, verified backup and unchanged non-mission save
data. Screenshots verify the corresponding HUD/world. These are setup/spawn
checks, not completed playthroughs of every sampled objective.

Two initial attempts hit EPERM replacing active.json. The first test monitor
used Python's default read sharing; it was replaced with a read allowing Windows
read/write/delete sharing. A later EPERM proved that monitor change alone did
not eliminate the transient lock. The exact other reader is not established.
The shared replay service now retries only the identical journal rename on
EPERM/EACCES/EBUSY, bounded to one second. It never retries save replacement or
native mutations. Regression coverage injects two denied journal renames and
checks normal state, unchanged save and retained native lease. All44 Node replay
tests pass;11 standalone/startup Python checks pass. The first invocation with
unittest discovered no tests; the correct pytest runner then passed all11.

The first interruption left the holding character active. A retry on that
character failed the original-identity acceptance check and does not count.
The original was recovered through its known native slot, and the temporary
adapter now refuses any test start unless the original identity is loaded.
Plan Z then passed on the original. No failed attempts were discarded.

A stable original save was backed up before restarting to install the journal
correction. New standalone SHA256:
b40cebe3dd751e2e902d36104ed9079ef5135d7b96742d4e5f2f1feb414b07c2
(40,512,040bytes). Installed hash matches; full MSBT remains disabled. At this
entry, six cases passed and the remaining four are resuming after restart.
Public versions/releases are unchanged.


The restarted game (PID62748) reached its main menu, but Computer Use rejected
the Continue click and the one window-reselection/activation recovery with
`failed to activate captured window`. Martin was asked for one Continue click.
Cases1–6 are passed, cases7–10 remain pending; the ten-case acceptance gate has
not passed. Original character/save remains intact and no sampled mission was
rerolled. Package comparison confirms only worker/replay_service.js and its
worker manifest changed in the correction; game/save/location code is unchanged.


## Completed ten-objective check — 2026-10-15
Martin loaded Continue, and the remaining frozen cases ran through the public
console parser and corrected standalone worker with full MSBT still absent.
All ten reached ready with the original level70 character, the correct active
native objective boundary and tracked HUD, normal grounded movement, verified
pre-replay backup and preserved non-mission save data. Screenshots were inspected
for every case. Nine passed exact-coordinate placement; one used a reviewed
nearby native fallback. The original strict coordinate failure remains unchanged
in07-result.json, with a separate native fallback review receipt.

1. Down and Outbound — Reach Order surveillance center: exact coordinate; 31.98s.
2. Unpaid Tab — Kill rippers: exact coordinate; 32.67s.
3. The Timekeeper's Order — Open tower door: exact coordinate; 31.53s.
4. Plan Z — Reach Ascension chamber: exact coordinate; 33.15s.
5. A Lot to Process — Talk to Zadra: exact coordinate; 32.00s.
6. His Vile Sanctum — Find energy spike: exact coordinate; 32.54s.
7. Another Universe — Melee door: native station fallback; 4.23m from authored start; 40.79s.
8. Shadow of the Mountain — Follow Calder: exact coordinate; 30.47s.
9. Her Flaming Vision — Clear out rippers: exact coordinate; 29.47s.
10. Rising Action — Align dish: exact coordinate; 28.95s.

Elpis / Melee door declined the unsafe exact location before teleport and kept
the native station. The player was grounded2.28m from that station and4.23m from
the source start, in the small starting room with the marked closed melee door
visible. This meets the requested nearby-native-fallback behavior; it does not
count as an exact-coordinate success. The other nine had zero horizontal error
from their authored preceding-completion point and under0.86cm error from the
collision-grounded point.

Cases1–6 ran before the journal-only repair, cases7–10 after it; binary package
comparison confirms only worker/replay_service.js and its manifest changed.
No native/game/save/location logic changed between those groups. No further
journal lock stopped the remaining four. Initial lock failures and the rejected
holding-character retry remain archived, not counted as successful attempts.
The known holding character's accidental earlier timeline change was restored
from its verified pre-attempt backup while the original remained loaded; the
pre-restoration holding save is retained too. The original is left on Rising
Action / Align dish, beside its marker. Full MSBT remains disabled.

Acceptance scope: ten live loading/spawn checks, nine coordinates plus one
nearby native fallback. This does not prove normal completion of all ten
objectives/encounters, all DLC, co-op or Epic live gameplay. Continue distributing
as an experimental local preview. No release/tag/upload or public version bump.
The installed, worktree and primary-workspace SDK copies match SHA256
b40cebe3dd751e2e902d36104ed9079ef5135d7b96742d4e5f2f1feb414b07c2.


## Text and source cleanup — 2026-10-15

Martin requested more natural wording and readable source for the standalone
SDK. Removed the development-preview suffix from the displayed mod name,
rewrote the help/readme around install, replay, bookmarks, dialogue and restore,
shortened implementation comments and formatted the standalone Python/worker
and package builder. Kept the experimental encounter note and existing license
notices. Replaced vague metadata credit "and contributors" with the named MSBT
foundation credit, and named the SDK team and bundled dependencies in the readme.

Changed source: standalone_mission_selector/{__init__.py,console.py,
runtime_paths.py,worker.cjs,README.md}, tools/build_standalone_mission_selector.py.
Seven package entries changed: those five packaged files, SDK display metadata
and the worker manifest. Native replay/save logic, location data, command names,
version2.39.1 and all five bundled license/notice files are unchanged. No new
human-authorship claim was added.

Validation: Python AST comparison matches the tested package after excluding
only docstrings, help text, one queued-message string and display metadata.
Node's bundled parser confirms the worker's structure matches after normalizing
formatting braces and grouped declarations. Syntax/Black/Ruff checks passed;
11 standalone/startup checks passed, then the final credit-only update passed
the two packaged catalogue/import checks again. No new gameplay run was needed.
Verification receipt: output/standalone-mission-selector/text-cleanup-verification.json.

Rebuilt shareable SDK SHA256:
390980305a6ea4619d3d61fe8f8108858ba67fa9cd7673108f431c7e74d42b63
(40,512,116bytes). Worktree and primary-workspace download copies match. The
currently running game retains the previously tested b40cebe3 build; it was not
closed or modified for this wording/formatting update. The previous artifact is
retained as before-text-cleanup.sdkmod for rollback. Public releases, tags and
versions remain unchanged.


## Console menu picker — 2026-10-15

Martin clarified that mission selection must use the interactive console mod
menu rather than requiring typed mission commands. Added a Mission replay
button to the mod's SDK options. It opens numbered campaign, playthrough-ordered
mission, main-objective and confirmation screens through console_mod_menu's
existing screen stack. Lists page ten entries at a time with N/P and standard
B/Q controls. Starts use the same validated console.run/submit replay path;
no mission/save/location implementation was replaced.

The picker also exposes named bookmark capture and load, dialogue On/Off,
session fog choice (leave by default), status, stop and backup restore. Bookmark
results cross a bounded queue to update the menu on the game thread. Disabled
mods cannot launch menu actions. Restore explicitly warns that the whole earlier
save, including gear/levels, is restored and still requires the original unloaded.

Changed standalone __init__.py/console.py, new menu.py, README and the standalone
fixture/UI tests. Fifteen standalone/startup checks passed, including real bundled
worker/encrypted-save flow, menu-to-native checkpoint routing, paging input
bounds, bookmark identity/fog/confirmation, naming and disabled-mod guards.
Syntax and lint passed before packaging; no BLImGui dependency or public version
change. SDK hash:c9a6c7a2fecf2e94515ae2a9d17de022726e1143d21dbc5b90091d603b289dbc
(40,514,900bytes). Installed after verifying the game had exited, then relaunched.
Previous install is retained as before-console-menu.sdkmod. Native menu flow
inspection remains pending at this entry. Shareable worktree and primary copies
are updated; old text-cleanup verification applies only to the earlier artifact.


Live menu follow-up: Martin navigated the installed native console menu while
Computer Use observed; input injection was stopped when his input was detected.
The real menu displayed Main story, playthrough-ordered paged missions and Wrath
of the Ripper Queen's main objectives, then the Start replay confirmation. His
menu-launched mission_main_shatteredlands1 checkpoint0 transaction reached ready,
closed its lease and verified the backup. The unsafe recorded point retained
its native spawn-station fallback. Journal:live-console-menu-replay.json.
This proves the installed menu-to-replay route, not encounter completion. Menu
bookmark load/paging/disabled guards have offline checks; broader live menu
bookmark interaction remains untested. No need to type mission commands for
normal selection. Game is left loaded for Martin; no additional input sent.


## Replay entry points and map-transition tracking — 2026-10-15

Symptoms: Wrath of the Ripper Queen began at Zadra's lab after coordinate
placement fell back; The Rescue / Enter the Volcano Base loaded and placed
correctly, but Martin observed the HUD switch to another mission when entering
the volcano. Other active missions in the journal are not evidence of a failed
save edit and are retained; this repair does not delete unrelated progress.

Source evidence: Wrath's generated first section inherited its prerequisite's
Talk to Zadra completion point, 3,722.1m from Wrath's own authored entry trigger.
The catalogue builder now uses a mission's own authored entry for its first
section when present. Later sections retain the preceding-completion policy.
The station rules preserve this provenance and select the nearest eligible
native station on that map. Wrath now uses its Mountains mission-giver trigger
and World_P.RS_SHA_ZoneTransSHAtoMOU (214.28m from that trigger), rather than
World_P.TS_FFlats_ZadrasLab. Twenty-one mission beginnings changed; eight more
sections gained coordinates. Current catalogue:39 missions,506 main sections,
375 coordinate starts and131 native-station starts. These are source-backed
candidates, not proof that every point can be placed in live gameplay.

The replay worker already tracked the chosen mission at completion, but nothing
retained that selection through a later player-initiated map transition. A
standalone-only session helper now remembers the replay mission, original
character and world. On a new map it validates the mission's active state and
native token before one ServerRequestTrackMission call if tracking changed.
It stops on character change, mission completion, a manual same-map selection,
disable or conflict with full MSBT. Unexpected helper errors are isolated from
the worker queue; an uncertain tracking request is not repeated. Normal
world-loading status now says it is waiting instead of reporting a stopped run.
No additional mission completion, save edit or teleport is performed by tracking.

Changed: tools/mission_lab/{build_selection_catalog.py,replay_spawn_rules.py},
mod_extracted/MattsSDKBoostingTools/{mission_selection_states.json,
mission_save_replay.py}, standalone_mission_selector/{tracking.py,console.py,
README.md}, and the focused spawn/state/provenance/standalone checks.

Validation:169 focused Python checks passed in37.97s, including packaged-worker
save transaction, all-anchor provenance, first-entry choice, once-only HUD
restoration, respecting manual selection and helper-failure isolation. Python
syntax/import/package audits passed. Black was unavailable in the default
Python environment during the final pass; no formatting pass is claimed.
A fresh read-only native inspection confirmed TravelStatus.status is exposed
and zero when settled. Martin's old-build Rescue placement reached ready before
normal travel to VolcanoFortress_P; the new tracking and entry changes are not
yet installed/live verified. Existing ten-start acceptance was setup evidence
and did not catch this semantic first-entry error or subsequent travel switch.

Local SDK SHA256:5009a81fd336aa2b9630437c5fd4ae4126ea435e0063559f44c8a92a2fa01713
(40,517,334bytes;189 entries). Previous installed c9a6c7a2 build is retained as
output/standalone-mission-selector/spawn-errors/before-entry-tracking-fix.sdkmod.
Current game left open while Martin tests. Matching download copy updated in
C:/src/MSBT-Workspace/product/output/standalone-mission-selector. Installation
awaits save/close; narrow Wrath-start and Rescue-map-handoff live checks remain.
Public version2.39.1, tags and GitHub releases are unchanged.


### Native arena arrival correction and installation

Before installation Martin reported A Zane to Kill For / Kill Digi-Zane's murderer
first arrived correctly in the arena, then moved behind an invisible wall. The
old native lease 807629b11ba14bcf8a880ec9fdb72b49 records native travel followed
by place_0 at the preceding murderer-found trigger (-51250,74100), grounded to
Z62061.14. The floor/capsule checks passed but did not prove arena access. The
source objective graph confirms that approach trigger plays the EvilZaneTC
moment and the selected objective references the EvilDigiZane boss fight.

New bounded policy: when the chosen station is native DestinationOnly and the
selected objective has a source-resolved gameplay/bossfight scene reference,
retain native arrival rather than repositioning to the preceding approach
trigger. This covers six boss starts (Digi-Zane, Queen, Earl, DahlFather and two
Timekeeper phases); five change from coordinate placement and one was already
native. Ordinary respawn/fast-travel starts and bookmarks retain existing rules.
Current counts:370 coordinate starts /136 native starts,506 sections total.
The six-source mapping is an operational policy, not six live encounter passes.
No arbitrary offset or point invented from the screenshot.

Validation:171 focused checks pass in38.25s, including positive/negative arena
policy cases and all-six generated-spec checks. Packaged Python syntax/imports
and archive CRC pass. Final SDK SHA256:
44759d4356a5c992f26ba01747e1912beb1eb03cdec970304028f884e483eca2
(40,517,381bytes;189 entries). The earlier5009a81f candidate was superseded before
installation. Matching primary-workspace download, readme and receipt updated.

Martin saved and closed the game. Verified no Borderlands4.exe process, backed
up the installed c9a6c7a2 artifact, installed the final SDK and verified its hash;
full MSBT remains absent. Rollback:
output/standalone-mission-selector/spawn-errors/before-installed-spawn-fixes.sdkmod.
Installation receipt:spawn-errors/install-receipt.json. Game relaunched through
its verified Steam app ID1285190. New-build live arena/entry/handoff checks remain
pending; no claim of encounter or travel-fix live proof yet. No public publish,
tag or version bump.


## Live three-fix recheck and missing opening objective — 2026-10-15

Martin asked the agent to run the three checks without his controller input.
A temporary, fixed three-case adapter calls the production console.submit path
and reads fresh native cursor/objective/tracking/position data. It does not
replace production code or complete an objective. Evidence is kept privately in
output/standalone-mission-selector/spawn-errors/recheck; no save files included
in the shareable package.

Installed44759d43 build: Digi-Zane checkpoint37 reached ready, preserved the
original character/unowned save data and verified the backup. The native travel
initially arrived away from the destination; one existing station correction
placed the character in the arena. No place_0/approach-trigger placement followed.
Three native observations over15 seconds and a later screenshot showed the
active fight and character still in the arena. Movement from enemy attacks was
observed; the pawn settled on foot with gravity1. Full fight completion was not
tested. Journal94c77526df2f486da771e852e19f9646.

The Rescue checkpoint5 reached its previous-completion location exactly in XY,
kept a stable grounded position across15 seconds, then travelled through the
native station route to VolcanoFortress_P. Cursor advanced naturally5->6 and
The Rescue remained tracked, shown on the HUD as Rescue FL4K / Kill Tediore.
A later settled native read confirmed tracking remained armed/unreleased and
normal movement. No objective-completion request was issued. The game retained
tracking in this run, so the conditional native re-track call was not exercised.
Journalb0e7d3a6bf9741439a024318549099f5; map-arrival/map-settled receipts retained.

Wrath checkpoint0 initially failed: correct map/nearby station, original
character and cursor0 loaded, but no active objective record existed. Setup
waited at boundary_wait, then timed out with backup retained. Stopped/closed it
through the public console command. This is a failed check, not a location pass.
The existing explicit current-objective restore was restricted to DLC openings
with travel_map. Generalized it to all cursor-zero sections using their own
authored mission entry. Only the selected initial objective is made Active;
future/parallel objectives remain excluded by the save helper's existing guards.
The existing inactive restage after native map arrival is reused. Tests now
verify every generated entry edit, including Wrath, instead of exactly3 DLCs.

Changed build_selection_catalog.py, generated mission_selection_states.json
and test_mission_selection_state.py.107 focused save/catalog/provenance checks
pass; final packaged171-check set passes in39.37s. No change to the tested arena
or tracking implementation. New local SDK SHA256:
00c8b6e33b783263a0021d0a2097ab1c8c26269c52d55091ad5944febe9d11a9
(40,517,603bytes). Safely quit via the game's normal Quit Game dialog, verified
process exit, backed up44759d43, installed matching new SDK, verified hash and
relaunched. Primary download/receipt match. Rollback and install receipt:
spawn-errors/recheck/{before-opening-state.sdkmod,install-opening-state.json}.
Wrath new-build replay is the remaining live check at this entry. Public versions
and releases unchanged.


## Wrath follow-up: chained-set cursor and post-refresh station check — 2026-10-15

The generalized initial Active-objective restore above did not resolve Wrath.
Its selected mission set retained cursorposition=1, pointing at its chained later
mission, even though the selected mission cursor was zero. The selection helper
now removes only the selected set cursor, while preserving every parallel mission
record and unrelated metadata. Added a focused preservation regression. Candidate
and before-save decrypts independently confirmed cursor removal, Active selected
mission and empty final flags. This proves the disk edit, not a playable encounter.

A read-only source inspection found two authored entry routes: Mountains has a
Mountains1 completion condition, and Grasslands uses an alternate opening. A
bounded pilot filling that condition and its known ancestors still failed; that
extra completion was rejected and is not in production data.

The entry character refresh restored the Grasslands-side position, far from the
selected Mountains station. Initial boundary readiness was transient, followed by
no active objective and unsafe/unloaded placement. Fixed save_replay_service.js
so both initial and post-refresh unsafe generated waypoints recheck the selected
native station instead of blindly claiming arrival or timing out at the final
gate. Existing once-only correction/receipt reconciliation applies; uncertain
placements are never retried. Added three worker regressions (post-refresh good
station, one correction after drift, lost correction reply). All47 worker checks
pass;167 focused Python checks plus5 no-BLImGui checks pass. Syntax/import compile
and archive audit passed. The fallback pilot correctly stopped when the selected
station itself was unloaded; it did not claim a successful Wrath replay.

Local candidate58e4dc63e2bc8bdf8c38c11d2c966c1ca26e998a11413d888ab1b8daac9317ed
contains that worker and cursor repair (40,517,730bytes). The installed archive
remains00c8b6e3; exact new worker/helper functions were loaded for bounded live
pilots without replacing the running game archive. Temporary pilots and receipts
are private under tools/selector_recheck and output/.../recheck. The next pilot
removes the redundant non-travel opening refresh, retaining the cursor repair.
Arena and natural cross-map tracking passes above remain valid; Wrath remains
unpassed at this entry. Windows rejected all agent keyboard input after a PIN
prompt (foreground window did not report a process id), so Martin entered only
the prepared pyexec loader commands; character swaps/travel/checks stayed automatic.
No public release/version change or full-MSBT reenable.


## Final three-fix result and installed SDK — 2026-10-15 19:42 UTC

All three requested setup checks passed. Wrath job518b34367e4742e1b263ceb75a3148ab
used the packaged selected-set cursor repair, the new worker, and the production
catalogue with only Wrath's unnecessary restore_active_objectives flag removed.
No additional Mountains1 completion was applied (receipt: four original ancestors,
zero station-objective overrides). Automatic original/holding reload and native
map travel reached the own-entry waypoint. All three observations at0/5/15seconds
reported the exact same position(51071.5955,-164754.4654,15093.6912), grounded true,
cursor0, both native route-opening objectives Active, Wrath tracked and lease
closed. Screenshot independently showed Wrath of the Ripper Queen / Reach
Carcadia Burn at Stoneblood Forest. This proves setup/stable spawn, not completion
of that mission. It used no second character refresh and no objective-completion
request. The first authored entry condition hypothesis did not need extra progress.

Removed the earlier unsuccessful generalized opening restore from the generator.
Only the original three cross-map DLC travel openings retain that special
restage. Rebuilt all506 section records and packaging. Final172 focused Python
checks (including5 no-BLImGui) and47 Node transaction checks pass. Source compiles;
all189 archive entries passed syntax/archive validation. Arena/tracking production
code remains the same as the earlier successful live checks. Conditional
re-tracking still has offline rather than forced live-branch proof.

Final SDK SHA256 f43fd658c6600dea4f9d5db67437276598df0d48b82fc3141f6b6a866611dc13,
40,517,508bytes. Martin saved/closed the game; process absence was verified before
replacement. Installed final archive and primary workspace download hash match.
Rollback: output/standalone-mission-selector/spawn-errors/recheck/before-final-recheck.sdkmod
(previous00c8b6e3). Install receipt install-final.json; aggregate summary.json and
entry-journal/entry-observations retain exact results. Final archive was installed
after these exact-component live pilots; no further boot/playthrough was claimed.
Game left closed; full MSBT sdkmod remains outside sdk_mods. Public versions,
GitHub releases and contributor names unchanged. No public publication.


## Evidence-table locked-door fallback — 2026-10-15 (verification pending)

Martin's next manual replay exposed a separate failure: A Zane to Kill For,
checkpoint8 / Place bottle evidence. Journalc88d22c61b1d49c1887e909e52b81ee2
was ready with native stationMandolin1_P.RS_Mandolin_Central, but Martin confirmed
that a locked door blocked the evidence table. This was not a regression in the
three previously checked starts; the nearest station did not establish a usable
route. Live readback and screenshot showed the active three placement objectives
at the station-side approach. No objective completion was issued for inspection.

The preceding collection section has three unordered authored pickup positions,
so it cannot provide a unique final point. Its own beginning is the earlier
crime-scene Echo-4 scan. All three following placement targets return within15m
of that point. Added a bounded collection-return rule in build_selection_catalog.py:
only after a multi-subobjective collection, only when every required following
waypoint is in the same small source area, the retained point belongs strictly to
past progress, and no map travel intervenes. It reuses the exact authored earlier
scan position(-52005.222252,-45277.645714,46305), not invented coordinates.15m is
an operational area-match bound, not native navigation proof. This changes only
Mandolin checkpoint8 in the current506-section catalogue (371coordinate/135native).
Native station fallback is disabled for this return-area start: an unsafe waypoint
must not silently send the player back across the reported locked door.

Changed generator, generated selection states, and two test files.112 focused
selection/rule/provenance checks and5 no-BLImGui checks pass. Three negative cases
reject distant, different-map or reused/future points. Packaged archive/syntax
checks pass; candidate8ff19d1d55497f024e8886395e92bd8a1f6080c0a87869b028d147e2d1ba428a,
40,517,592bytes. No running game archive replaced. Installed/primary shared SDK
stillf43fd658 until the pending live test/install. Temporary bottle.py loads only
this exact catalogue and a fixed readback/start adapter for a bounded pilot.
Windows still rejects agent keyboard input; Martin was asked to run that loader.
Door approach/interaction live proof and final install are pending at this entry.


### Crime-scene return-point live placement — 2026-10-15 16:13 local

The exact candidate catalogue was loaded through the temporary bottle adapter;
production native replay code stayed unchanged. Job94f97dcad26d4bdea3f983e8a5cd8aae
completed automatic original/holding save reload, native map travel and one
waypoint placement. Backup and unowned-data preservation verified; fog stayed
unchanged. Native observations0/5/15seconds were identical at
(-52005.222252,-45277.645714,46084.54869152588), grounded true, cursor8,
all three placement objectives Active, selected mission tracked and lease closed.
The grounded Z adjustment used the existing native placement check. Screenshot
showed the evidence table directly beside the character at Zane's Arcade with
no door between them, instead of the old Private Dick/central-station approach.
This proves the corrected placement/side of the door. Martin was asked to place
all three items normally; interaction/advancement confirmation remains pending.

Primary shareable BL4MissionSelector.sdkmod and build-receipt.json now match
8ff19d1d55497f024e8886395e92bd8a1f6080c0a87869b028d147e2d1ba428a.
The game archive remainsf43fd658 during this live session; the exact new catalogue
is active for this pilot. Prior downloadable SDK retained privately as
spawn-errors/recheck/before-crime-scene-return.sdkmod for rollback. Final archive
installation still requires a safely closed game. No public release/version bump.


### Normal interaction confirmed; replay section scope clarified — 2026-10-15

Martin confirmed all three evidence items could be placed normally and the
objective advanced. This supplies the hands-on playability result missing from
the placement-only check above. The shareable8ff19d1d package includes the tested
crime-scene return point; final game archive installation is still pending while
Borderlands4 remains running.

Martin clarified the speedrun requirement: a replay section includes the travel
from the previous completed section, rather than starting at each internal button
or checklist step. Evidence placement is the end of the investigation/collection
section, not a useful default replay beginning. The following section should
start at the finished table and include the journey onward. The existing grouping
helper already supports source-guarded larger vehicle/office sections. Investigate
this same mechanism for the evidence sequence, retaining the full execution graph
and exact bookmarks. Asked whether its start should include entry/interviews/scan
or begin with gathering evidence; no new grouping or broad inferred boundaries
have been applied pending that preference. Do not blindly place every future
section directly at its current task marker or collapse unrelated stages by title.


## Speedrun investigation section — 2026-10-15

Martin chose entry into the crime scene, including interviews and scanning, as
the larger replay beginning. Implemented a source-identity-guarded Mandolin range
in mission_selection.main_groups: native checkpoint4 / Reach crime scene is now
labelled Crime-scene investigation; internal checkpoints5..8 no longer appear as
separate default choices. Full native mission groups/objectives and execution
remain intact. This includes the approach from the preceding NOR entry, interviews,
scan, travel to all evidence pickups, return and placement. Bookmarks can still
capture exact internal mission states; their native catalog identity is unchanged.
No new automatic aggregation has been guessed for other missions.

The following native checkpoint9 / Find Digi-Zane's murderer starts at the
finished crime-scene table area, using the exact authored scan approach already
proven grounded and playable in the bottle test. The previous section exposes its
end-area anchor explicitly, so the builder does not incorrectly use the beginning
of its collapsed range as the next section's beginning. Fallback to the central
station across the door is disabled for that return-area start. Default catalogue
now has502 larger choices across39 missions (367coordinate/135native); this removes
four menu choices, not gameplay or mission coverage.

Changed mission_selection.py, build_selection_catalog.py, generated selection
states, standalone README and grouping/catalogue/package regression tests.
147 selection, provenance, anchor and startup checks passed; the121 selection/
provenance subset also passed after the final fallback guard. All16 packaged
standalone checks pass (real bundled runtime and synthetic encrypted saves).
Python sources compiled and189-entry archive audit passed. The user-confirmed
three-item placement/advancement test above remains the live encounter proof;
the new larger section is offline/menu/data validated, not a fresh full-route run.

Grouped SDK SHA2568a04ad1b197c7250176a41a933335888683b41b95ae687b03e3e73b582c99321,
40,517,638bytes. Primary shareable SDK, README and build receipt updated. Previous
8ff19d1d download retained privately as before-grouped-investigation.sdkmod.
The game remains open on installedf43fd658 with the8ff catalogue pilot active;
asked Martin to save/close for permanent grouped-SDK installation. No version bump,
public upload/tag/release, desktop launch or MSBT reenable.
