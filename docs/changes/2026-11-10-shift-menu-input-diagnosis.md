# SHiFT Escape / pause / Tab input investigation — 2026-11-10

## Outcome

Release remains on hold. Martin reported losing gameplay control in pause menus
while SHiFT was minimized, recovering by Show SHiFT followed by Escape. This
investigation captured native state and a distinct Escape close route, but did
not reproduce a usable normal pause/Tab baseline through automated keyboard
input. No production handoff fix or new release package was made from this run.
The existing candidate implementation remains at `9db8b0bedc0b537161158628081aac2706760855`
(documentation head; package implementation stamp `c94f73af`).

## Exact trial identity

The 4090 ran released 2.41.1 desktop, SDK and PAK, with a companion-only observer
derived from the original released companion. This is a baseline investigation,
not native qualification of the 2.41.2 candidate.

| Input | SHA-256 |
| --- | --- |
| BL4 executable | ba75f7c2874b16efb5536a5c0cc28918a03efd3e55d790d2e4db57de0c3a353a |
| Original PAK | 728165a795f7543b9a109604b60a8ae54f70de2c6cf92f4a37c231982a5e617f |
| Original main SDK | 643f07653c3d2eb1ac1042018ea77fb0736bb074661aeaf600b91bc898fa5962 |
| Original companion | 9fc2a823605f1035cf3df8b53ff20b753b2db8798d51b15fbe6fb00f941c8c02 |
| Observer v2 | 56d198d19935118ccb3545581f3bd4251c3917adcf7d61ca94b1501a6732da13 |
| Completed JSONL trace | 3344349edc549f88c70bbd77d319c162a2afef8d4ba20aafaae66206e75103ac |

Evidence root relative to the primary product checkout:
`local/shift-storage-repair/menu-input-diagnostic/`. The trace is
`native-menu-input-v2.jsonl`; the exact deployed observer is
`ShiftManagement-menu-input-v2.sdkmod`, with `build-receipt-v2.json`.
The observer changes only the companion's `__init__.py`; other archive entries
remain byte-identical. It samples state without forcing pause, focus or input,
and caps output at 600 records. Function arguments are names only, not values;
player/pawn identities are hashed. Root reviewed and corrected the delegate's
initial probe to use GameplayStatics.IsGamePaused and side-effect-free status.

## Observed native facts

- Main menu Continue loaded Fortress Indomita. Move/look ignored flags were true
  during loading, then both became false. That transient is not the lockup.
- With background state idle and SHiFT closed, synthetic Escape and Tab did not
  visibly open normal menus. The same limitation remained after desktop Stop.
- Desktop Show opened SHiFT: child visibility `[25,25,25]`, canvas visibility 2,
  game paused, cursor enabled. All seven sampled input contexts remained ordinary
  gameplay contexts, with zero paths matching the existing UI-context predicate.
- Synthetic Escape did close this visible SHiFT page: children became `[2,2,2]`
  and pause false at sequence 239. Cursor remained enabled. **No Close callback
  was logged for this Escape path.** This does not establish who owns cursor focus.
- Desktop Accept opened SHiFT but the observed page still showed accepter stopped.
  Clicking in-game Play while accepting reached active at sequence 291.
- Active state persisted through sequence 402: **111.221 seconds**, visibility
  `[1,1,1]`, ownership true, unpaused, move/look ignored false. Desktop displayed
  auto-accepter running. Synthetic Escape and Tab produced no recorded menu
  function callback or pause transition. This is heartbeat/state evidence, not
  proof of normal gameplay or actual acceptance of a request.
- Desktop Stop produced Close callback records 403/404, then idle at 405,
  hidden children, no ownership, pause false and cursor false. This proves the
  exported Close hook worked in this session; Escape used a route that did not
  enter that hook. No particular alternate native function is established yet.
- Final trace: 447 records: 439 periodic snapshots, four Open callback records,
  two Close callback records and two background transitions. None of the seven
  instrumented menu-function targets emitted an event. Their registration success
  was not separately recorded in v2, so silence alone does not prove non-dispatch.
- No outgoing request or deletion was performed. No new incoming acceptance was
  identified or counted during this trial. AFK boosts were never started.

## Source findings and research

Independent review of `tools/afk_lobby/shift_background.py` confirms
`_check_contexts()` runs at Start only. Active ticks monitor native ownership,
visibility, lease and player/pawn identity; they do not handle ordinary modal
menu transitions. The companion hooks CameraModifier POST and exported SHiFT
Open/Close PRE. Those hooks do not cover the observed Escape close route.
The candidate already has the previous guarded Close-before-Open Show repair;
an initial delegate claim that it lacked this repair was checked and rejected.

Epic's [CommonUI input fundamentals](https://dev.epicgames.com/documentation/unreal-engine/input-fundamentals-for-commonui-in-unreal-engine?lang=en-US)
describe input configuration restoration and stale configurations causing loss
of control. This is a research lead, **not proof BL4's SHiFT implementation uses
CommonUI**. The game evidence above is authoritative for this trial.

The proposed close/reopen handoff is plausible, but ordering matters: calling
Close after another menu has taken focus can itself reset that menu's pause/input
state. A future implementation needs an observed pre-menu transition, explicit
Start intent distinct from the heartbeat lease, truthful suspended status,
one-shot resume, and cancellation on Stop/Show, bridge loss, travel or identity
change. Closing SHiFT can stop page polling, so uninterrupted acceptance must not
be claimed while suspended. No speculative focus-reset loop was added.

## Validation, restoration and remaining work

Observer v2 focused tests: **5 passed**; archive syntax checks completed
before packaging. Existing candidate package checks were not rerun because its
implementation and package bytes did not change.
An independent reviewer recomputed the final trace hash/counts and checked this
note against its transition records; no material inaccuracies were found.
The task-local builder now prepares v3 registration receipts for each hook,
distinguishing explicit True/False from an inconclusive non-error return. Its
expanded five focused tests pass (root rerun: 1.04 seconds). This later diagnostic
was neither packaged nor installed; the deployed v2 archive and trace are unchanged.

The diagnostic game exited normally with Alt+F4. Window inventory and guarded
`tasklist` checks confirmed it closed. `menu-trial/deploy_observer.py restore`
and then `verify` succeeded; receipt `menu-trial/installation.json` records
restored state at **2026-11-10T17:31:58.539568Z**. Original companion and enable
file restored; main SDK and PAK unchanged; private protected-settings file remains
absent as before this trial. The accidentally toggled desktop Target character
level checkbox was restored checked and visually verified. Released desktop
2.41.1 remains open; no diagnostic mod remains installed. No publication occurred.
The receipt now also stores a fresh explicit process/hash verification at
**2026-11-10T17:34:50.688918Z**.

The Windows On-Screen Keyboard alternative timed out at required app access
(`snowy-rain-07465883`, `C:\Windows\System32\osk.exe`); it did not launch and was
not retried. This is a timed-out tool-access request, not a denied game test or a
missing user authorization for the repair. No approval is pending for cleanup.

Next native requirement is a physical-keyboard/menu reproduction on the 4090:
closed baseline Escape/Tab, active background Escape/Tab, menu exit, Show/Escape
recovery and repeated cycles, with the observer capturing actual menu ownership.
Normal gameplay/gamepad, sustained accepting during menus/travel, phone behavior,
and the final message-only installer execution remain unqualified. The existing
2.41.2 installer/portable are retained unchanged and must not be labeled as fixing
this newly investigated menu case.

## Physical comparison and captured failure (23:00 UTC checkpoint)

This supersedes the earlier restored/closed state above. The physical stopped
baseline was reported by Martin as "all steps passed" in the screenshot relayed
by the parent. v3 recorded six paused snapshots and six ordinary UI mapping
contexts, but no instrumented menu-function callback.

A fresh companion-only v4 observer trial began at 20:21:58 UTC. The main SDK,
PAK and desktop remain released 2.41.1; this is not a 2.41.2 candidate pass.
Martin then reported "pressing esc again did not close the menu" in the active
comparison. Root captured the unchanged screen before input: the normal BL4
Systems Menu, Back to Game and Escape/Back visible. Fresh desktop status showed
Auto-accepter running and SHiFT background active.

The v4 trace exhausted its 3600-record limit before the failure. It contains zero
active-paused snapshots, zero UI-context snapshots and zero menu-function events;
its last snapshot is ordinary unpaused active gameplay. It therefore cannot
establish the exact native state at the failed physical keypress. SHA-256:
`1bf7652dd38cf0ffa89ff4da765b2cc6d38c1bb2cc90df8c39c36be5483cc6bb`.
A bounded rolling observer is being prepared so delayed physical handoffs do not
lose the event. Existing v3/v4 artifacts and traces are preserved.

After evidence capture, one desktop Stop accepting friends click was sent.
Fresh status still says active; stopping has NOT been confirmed. The normal
Systems Menu remains after one synthetic Escape, which is inconclusive given
previous synthetic-input limitations. A physical Escape recovery check is
pending. Do not describe a requested stop as successful. The released first-use
command-linking defect and paused-driver delivery remain separate possibilities.

Current game window: 3476666. Observer v4 remains installed; active trial receipt
is `menu-physical-active-trial/installation.json` (observer_installed), not the
older restored receipts. Its helper must restore and verify after normal game
closure. No production menu fix or new release package was made at this checkpoint.

## Recovery verified (follow-up)

Martin reported "it works normally again" after the further physical Escape and
W/mouse-look check. Root screenshot confirms ordinary gameplay. The first
background desktop AX read still contained active text; after raising the desktop,
fresh screenshot and AX both show `SHiFT background: idle` and companion available /
AFK lobby link waiting. Acceptance is now confirmed stopped. The exact moment the
Stop took effect is unavailable; do not infer stalled camera ticks or failed
command delivery from the stale/intermediate desktop text alone. Recovery is not
proof of a repair. No extra Close/Show action was needed in this follow-up.

## v6 diagnostic preparation

The v4 run closed normally and its guarded restoration plus verification passed
at 2026-11-10T23:08:11Z. Original companion/enable/SDK/PAK hashes and the absence
of private protected settings matched the pre-trial backup.

Observer v6 replaces the fixed cap with an atomic latest 1 Hz sample and a
four-file ring of up to 600 events per file. Stable pause, input-context,
blocking, visibility, PC-flag and identity changes are recorded independently
of background-state changes. It adds a read-only IsBlockingEnabled query and
camera POST tick count. Root rerun: 8 tests passed in 13.23 seconds. No production
behavior changed. Archive SHA-256:
`c277ef897499e4ae71a7b6418e5ab95f5e42cc9d7ab5f18c7fdd75be52efe164`.
Only ShiftManagement/__init__.py differs from the pinned released companion.

Fresh trial receipt: `menu-physical-v6-trial/installation.json`; state
observer_installed. The canonical SDK/PAK remain released 2.41.1. Direct launch
initially exposed no window, but read-only tasklist confirms Borderlands4 PID73616
starting; no second launch was issued. Current rollback helper is the one inside
menu-physical-v6-trial and must run after normal closure, followed by verify.

v6 gameplay handoff is now active (PID73616/window9901276), confirmed directly
by the latest observer sample: hidden children[1,1,1], owned=true, unpaused,
seven normal contexts/no UI contexts. The blocking getter is true in closed idle,
visible foreground and hidden active states; it is not a unique failure marker.
Root screenshot confirms gameplay with the tiny view. Physical Escape repeat is
pending. Current handoff and exact initial snapshot are in menu-physical-v6-trial.
No gameplay repair or updated release artifact is claimed from diagnostic work.

## v6 physical failure captured before root input

Martin reported another menu exit failure and transient mouse-look requiring
held left click after switching to chat/back. His later correction is: "it is
working normal now. i just cannot exit menus". Mouse capture is therefore a
transient observation, distinct from the persistent reported menu-exit failure.
Root's initial screenshot shows gameplay with Windows Start over it; it does
not show a currently stuck Systems Menu. No root input preceded capture.

Frozen logs are in menu-physical-v6-trial/failure-capture. Events SHA-256:
`f4db4866d2169ea7896f1f51ab67e3ebe21a2e40dee54f4df8ceb55c625e889a`;
latest snapshot SHA-256:
`34c18fcda6f7d1060a58f4be4fdd3d159ead3c735ee0c38ab2d2af134346b8bb`.
At seq398/175332.4077244, background stayed active/owned with hidden[1,1,1],
paused=true, and only context_ui_cursor added to seven gameplay contexts.
At seq455/175389.5816877 pause cleared; camera ticks advanced220954→262252
through that57.174-second interval. This rules out a stalled camera callback
for that observed pause interval. Another pause/unpause occurs468→470.
No exported Close or instrumented menu-function event accompanied these changes.
The stopped baseline's six UI contexts differ, but timing/menu identity are not
fully matched, so this is a useful distinction rather than proof of cause.
Current sample after report is active/unpaused, cursor=false, move/look ignored
false, seven normal contexts. Blocking getter remains true in all these states.

A scoped blocking-flag A/B candidate is being implemented locally: snapshot prior
flag, suppress only while owning the hidden native view, restore prior value on
teardown and retain rollback on partial failure. Existing getter/setter receipts
establish callable native API, not its effect on menu exit. No successful repair
or final-package validation is claimed. Release stays HOLD.

## Recovery and closure status after v6 evidence capture

Root desktop Stop produced directly observed idle, owned=false, hidden[2,2,2],
unpaused, cursor=false, no ignored movement/look. Saved latest snapshot is
menu-physical-v6-trial/stopped-after-failure.json. This confirms the accepter
stopped, separately from menu functionality.

Auto-review rejected Alt+F4 to game window9901276, citing possible unsaved-game
loss and directing in-game closure. The rejected action did not execute and was
not retried. User-message history was checked; no new closure-specific permission
was inferred. Root is following the explicitly suggested safer in-game Quit path.
Synthetic Escape did not open Systems Menu, so a physical Escape-to-open handoff
is pending. Game remains open, v6 observer installed, restoration not yet run.
No force-close, process kill or equivalent indirect workaround occurred.

## Experimental source repair status

The isolated candidate now scopes ShiftUIFunctionLibrary.SetBlockingEnabled(false)
to a validated owned hidden view. It captures the exact prior bool before any
native visibility changes, verifies the setter result, ties rollback to the same
native identity, and restores the prior flag during teardown/externally-closed
cleanup. Partial failures retain ownership for existing bounded retry; replaced
native lifetimes clear stale rollback state. It adds no per-frame focus writes,
new bridge authority, saved settings or released-version changes.

This is an A/B hypothesis pending physical validation, not a resolved defect.
Current released installer/portable hashes predate this source experiment and
must not be described as containing it. The source lives only in the isolated
candidate; primary unrelated dirty work remains preserved.

## Scoped blocking candidate packaged offline

Final focused native/controller/routing/QuickMenu suite:42 passed0.57s.
ExistingHTTPsuite:16 passed8.293s after rerunning outside the Windows socket
sandbox (initial sandbox attempt producedWinError10013, not application failures).
Independentreviewfound prior-false restorationcouldoverwriteexternalenable;
rootcorrected it and added that regression plus write-then-raise rollback coverage.
All Python archive members compile; CRC and exact member readback pass.
LocalA/Barchive ShiftManagement-blocking-trial-v7.sdkmod SHA-256:
`2f7d3a314704db5458c8a32bb59f40dd71c141479cf6723db1e696a74db88493`.
Buildreceipt menu-input-diagnostic/build-receipt-v7.json. NOTinstalled.
It changes the native adapter plus observer log paths against the v6 released
baseline, preserving the other three members. It is not final-release qualification.
Current game still runsv6, accepterstopped; physicalin-gameQuit handoff pending.
Preparedinstall/rollbackinstructions:menu-blocking-v7-trial/HANDOFF.md.

Independent final review found no remaining concrete issue in the native helper
or tests. The reviewer did not rerun tests; execution results above are root's.
Release remains on hold pending physical A/B proof, coherent package rebuild,
remaining acceptance checks and cleanup. No publication occurred.

## v7 deployment after normal in-game closure

Martin's "Ok" was followed by an actual screenshot confirming Systems Menu.
Root clicked Quit Game, then the normal Quit Game confirmation; the game window
closed. V6 guarded restoration and fresh verification passed at23:30:15.930UTC:
original companion, enable, SDK, PAK and absent private-settings state all match.
The earlier Alt+F4 denial was not retried or bypassed.

The reviewed v7 companion was installed at23:30:26.988UTC using a new guarded
backup/receipt in menu-blocking-v7-trial/installation.json. Main SDK, PAK and
real settings remain unchanged. Game launch is in progress; native A/B results
are not yet established. Current cleanup must use the v7 trial helper after
normal game closure, not the already-restored v6 helper.

## v7 native state verification and physical handoff

V7 is installed and BL4 is running in Fortress Indomita on 4090. Two in-game
Play while accepting activations were verified active/owned/hidden [1,1,1],
unpaused, with ShiftUI blocking false. Desktop Stop between them was verified
idle/closed [2,2,2], ownership released and prior blocking true restored.
Evidence: menu-blocking-v7-trial/first-active.json,
first-stop-restored.json and physical-handoff.json. Current state is active for
Martin's physical Escape and Tab comparison. Mouse cursor flag becomes true
after Start despite move/look ignored flags remaining false; no physical
control success is inferred from these flags. No actual friend acceptance or
deletion was established in this unit of work.

Physical test pending: Escape, wait 3 seconds, Escape; if successful repeat;
then Tab and Escape; check W and free mouse-look with buttons released, and
switch away/back. Stop at first failure and preserve screen for inspection.
Release HOLD. Existing installer/portable do not contain this repair. V7
cleanup remains pending until this physical handoff ends; backups intact.
No app approval is currently blocking this handoff.

## 2026-11-11 v7 failed physical Escape; lifecycle experiment

Martin reports Escape still did not exit pause menu. The blocking-flag A/B is
rejected as a solution. Root captured live state before changing it: background
active/owned, blocking false, unpaused, no UI contexts; screen already gameplay
with tiny SHiFT view (not a currently visible stuck Systems Menu). Frozen latest
and event log are in menu-blocking-v7-trial/failed-*. Full ring audit follows.
Root then used desktop Stop: observer confirms idle/closed, unowned, blocking
true, no ignored movement/look. V7 remains installed pending normal game Quit.
Synthetic Escape did not open Systems Menu; physical menu-open request pending.

Next experiment is task-local, not production: non-consuming Escape/Tab input
callbacks close native SHiFT before original game InputKey, then detect actual
menu entry/exit via paused state plus EnhancedInput UI mappings and queue one
fresh acceptance start. Explicit Stop/Show/disable, lost identity/service,
unknown observation, or timeout cancel resumption. Installed keybinds API
supports this callback; upstream oak2-mod-manager/src/keybinds/keybinds.cpp
lines84-98 skip cursor-visible UI; lines143-153 invoke callbacks before original
InputKey. This is a research lead requiring installed-runtime qualification.
Reference: https://github.com/bl-sdk/oak2-mod-manager/blob/master/src/keybinds/keybinds.cpp
No per-frame input-mode enforcement or binding override planned. Rebound keys,
gamepad and other menu-entry paths remain outside the scoped first experiment.
Release HOLD. No new installer or public artifacts; cleanup not yet complete.


## v8 prepared checkpoint

The v7 state-edge trace shows paused+active+owned+blocking false at seq8805,
then unpaused at8910, 105.246 seconds later; camera ticks advanced77,745.
No exact Escape event was captured. Full frozen evidence is in
menu-blocking-v7-trial/failure-capture/AUDIT.md. The failed native blocking
implementation and tests were archived in rejected-v7-source.patch and removed
from isolated candidate source; only documentation differs from HEAD9db8b0be.
Installed v7 remains until normal Quit and guarded restoration.

A separate task-local v8 diagnostic is built, NOT installed. Archive:
menu-lifecycle-v8-trial/ShiftManagement-menu-lifecycle-v8.sdkmod
SHA256 be91bde861b6af165dbb5fbf8bb52fc147f5f74b65a4306546e891e4bd04b073.
Python syntax, six-member ZIP CRC/readback passed. Final root unittest discovery
passed24tests in0.065s (13 pure lifecycle +11 mocked native wrapper tests).
One earlier run intersected delegate fixture edits and failed7 of21; final
fixtures model inactive after Close and all final tests pass. Independent
review found no remaining concrete code blocker; native key dispatch/thread,
menu behavior and fresh-page resume still require actual game evidence.

Current fresh hashes are in menu-blocking-v7-trial/current-state-after-failure.json:
v7 companion installed; released SDK, PAK, enable file and absent private
settings unchanged. Game open, accepter confirmed idle/unowned/closed. Physical
Escape to open Systems Menu is requested because synthetic Escape did not open
it. No app approval pending. V7 restoration and v8 native tests are pending,
not denied or completed. Release HOLD; no release build/publication this unit.


## 2026-11-11 v8 installed: first live checkpoint

Normal in-game Quit succeeded. V7 restoration and fresh verification completed
at 20:54:11 UTC; v8 companion installed at 20:54:21 UTC. Installation receipt is
`menu-lifecycle-v8-trial/installation.json`; original SDK, PAK, enable file and
private-settings absence are preserved by the guarded deployment. Current archive
SHA256: be91bde861b6af165dbb5fbf8bb52fc147f5f74b65a4306546e891e4bd04b073.

BL4 relaunched on the 4090 into Fortress Indomita. Released desktop 2.41.1 is
running. Desktop Accept friends while playing opened SHiFT but did not establish
active acceptance; in-game Play while accepting did establish active at observer
seq206 (at1147.4083649), hidden [1,1,1], owned, unpaused, cursor false, seven
gameplay contexts and no UI contexts. At seq207, 0.706 seconds later, cursor
returned true while active/unpaused/owned and contexts remained unchanged.

A synthetic Escape did not open Systems Menu and did not reach the registered
v8 key handler. Only handoff_keys_registered is recorded. This is not a physical
Escape failure/pass. SDK upstream key dispatch skips cursor-visible controllers;
physical focus/input is needed to distinguish cursor state from synthetic input
limitations. Screen also showed a small SHiFT page at upper left despite native
hidden flags; rendered invisibility is not established by those flags.

Frozen first observations: menu-lifecycle-v8-trial/first-live-checkpoint/.
Physical test requested: focus BL4, check free mouse-look, press Escape once and
leave resulting state for inspection. No new live friend acceptance/deletion is
claimed. No app approval pending. Game remains open and v8 remains installed for
this test; cleanup is pending, NOT completed. After normal Quit use v8
`deploy_observer.py restore`, then `verify` (not v7 helper). Release HOLD.


## 2026-11-12 physical Escape: v8 failed menu entry

Physical Escape DID reach the v8 callback on the bound game thread, and native
Close succeeded. No pause/menu was observed; after 3 seconds the restart intent
was cancelled, leaving idle/closed/unowned gameplay. Frozen exact sequence and
hashes: `menu-lifecycle-v8-trial/physical-escape-failure/AUDIT.md`.
This supersedes the prior lack of physical key evidence. Native Close during
InputKey may change routing, but this is an inference; no verified Systems Menu
call is established. Do not invoke Pause/OpenStatusMenu by name as a guessed fix.

A bounded passive input-binding/schema probe is being prepared under
`menu-route-v9-trial`; v8 remains installed, game open, accepter idle. Physical
second Escape requested to open normal Systems Menu and leave it for normal
Quit. No app-access approval pending; this is a physical-input/qualification
blocker, not a denial. Normal closure and guarded v8 restoration remain pending.
Release HOLD; no new release build or production repair claimed.


## Built checkpoint 2026-11-12

Root full unittest discovery: 34 passed in0.095 seconds (24 inherited v8,
4 probe, 6 wrapper). All packaged Python compiled before ZIP creation;
7-member ZIP CRC/readback passed. Five non-init v8 members are byte-identical;
new passive probe plus observer/init instrumentation are the only differences.

Archive: ShiftManagement-menu-lifecycle-v9.sdkmod
SHA256: 53e5370c48a99475671341833cb4020e7fed937a0f61cba3c20ea937efdc67cc
Not installed; no native success or production fix claimed. Build receipt and
validation.json record exact source/member identity. Current installed v8 and
original main SDK/PAK/enable/private state freshly hash-verified at00:53:37UTC.

Remaining immediate action: physical Escape once with v8 now idle/SHiFT closed,
leave Systems Menu open. Synthetic Escape did not open it. Then normal Quit,
v8 restore/verify, and v9 install/launch/baseline trace. No approval is pending.


## 2026-11-12 v9 installed and native baseline captured

Martin reported “i clicked it and the systems menu is open”; do not classify
that report as physical Escape success. CUA confirmed Systems Menu. First Quit
confirmation was interrupted by detected user input; a fresh screenshot showed
Systems Menu again. Normal Quit then succeeded and window/process absence was
verified by the guarded rollback. V8 restored and freshly verified01:12:42UTC.
V9 installed01:12:52UTC. Launch initially returned no targetable window, but
process inspection showed loading; no duplicate launch occurred. Main menu
Continue loaded Fortress Indomita on the4090.

The passive probe executed successfully: gameplay_ready metadata sample, no
error, local PC component plus active context bindings. Native game assets map
Escape to /Game/GameData/Input/EnhancedInput/Action_PauseMenu.Action_PauseMenu
in Context_Player_Base_Gameplay and Context_PlayerController_Default. Tab maps
to Action_StatusMenu and a context-sensitive prompt action in base gameplay.
This establishes asset mappings, not which handler ran or how to invoke it.
BoundActionHandlerList was empty in the sampled direct local component.

Current native baseline: controller idle, SHiFT closed[2,2,2]/unowned,
unpaused, cursor false, move/look ignored false. Game is open for physical
Escape/open then Escape/close baseline test. No active-accepter/menu-cycle
pass claimed; no friend actions initiated. V9 remains installed; its cleanup
is pending. Use menu-route-v9-trial/deploy_observer.py restore then verify
ONLY AFTER normal Quit. Original SDK/PAK/enable/private absence freshly
hash-verified. Evidence: menu-route-v9-trial/baseline-capture/receipt.json.
No app approval pending. Release HOLD. No production code or release changes.

# V10 deferred menu-action experiment — 2026-11-12

Release remains HOLD. V10 is built, not installed or live qualified.

## Evidence and design

Martin reports the v9 physical Escape test "it opened and closed". Frozen evidence
is in ../menu-route-v9-trial/physical-baseline-pass. Events 712–717 show the
unmanaged Escape, paused=true, then paused=false with the accepter idle and SHiFT
closed. This passes only the stopped-accepter baseline. The seven older native
menu hooks were silent even on this successful baseline, so their silence cannot
establish that no menu action ran.

V8's active-accepter Escape closed SHiFT but did not open the pause menu within
three seconds. Changing input routing during the original key callback is a
hypothesis, not a proved engine cause. V10 consumes only a managed menu press
after successfully closing SHiFT, waits at least 50 ms and confirms quiescence,
then requests the mapped menu action once. It resumes a fresh acceptance lease
only after observed menu entry and stable exit. Stop, Show, identity changes,
disconnect and timeouts cancel the handoff. No-menu timeout precedes dispatch.

The dispatcher checks active game mappings, local player/subsystem ownership,
and the exact reflected InjectInputVectorForAction signature before a single
game-thread call. Escape maps to Action_PauseMenu and Tab to Action_StatusMenu
in the observed BL4 assets. The generic Epic API documentation supports this
experiment but does not prove the BL4 invocation works:
https://dev.epicgames.com/documentation/unreal-engine/BlueprintAPI/Input/InjectInputVectorforAction?lang=en-US

## Offline validation

- 51 unittest checks passed in 0.099 s: 20 lifecycle, 8 dispatch, 13 native wrapper,
  4 probe and 6 probe wrapper checks.
- 5 Quick Menu/no-BLImGui pytest checks passed in 0.29 s.
- All packaged Python compiled before archive creation; eight-member archive
  CRC/readback and individual member hashes are in build-receipt.json.
- Independent delegate review found no concrete blocker; live signature,
  menu entry/exit, resume and controls remain unverified.
- Initial four wrapper failures reflected the changed managed-key Block return;
  assertions now distinguish managed consumption from unmanaged passthrough.

## Exact candidate and installation plan

Companion ShiftManagement-menu-lifecycle-v10.sdkmod:
7cedc9640658745bf02993af8fcb5150e697661c251a1d0adfaadbc66fc0dabc

Candidate PAK from ../product/dist_electron/win-unpacked/resources/afk_shift:
fdb039f13ea24c4b8b30b8cc972a83df7f6c71f20a09e7c5f916aebad6a9b93f

The PAK pair is needed to test candidate desktop command/resume behavior; the
released PAK opened the page without completing candidate Start. Main SDK is
preserved. V10 deploy_trial.py backs up companion, PAK and enable file, requires
the game closed and known original bytes, and records installation.json. Restore
and verify with this same helper after normal Quit. Real private settings must
remain unchanged. Do not use the v9 helper to restore a v10 installation.

Current state at preparation: v9 companion installed, released SDK/PAK intact,
BL4 running in gameplay, accepter idle, SHiFT closed. Physical Escape/open is
requested so normal in-game Quit can precede v9 restore/verify and v10 install.
No app-access approval is pending. No friend actions were initiated in this unit.

Next tests: runtime action schema, physical Escape/open-close with accepting
active, Tab/open-close, repeated cycles, W/mouse after each exit, desktop Stop
during handoff, resumed acceptance, and final normal closure/verified rollback.
Production integration and final package rebuild must wait for native results.


## V10 installed checkpoint — 2026-11-12 01:40 UTC

Normal in-game Quit completed after CUA verified Systems Menu. V9 restored and
verified before v10 deployment. V10 companion and coherent candidate PAK were
installed at01:38:16UTC; exact fresh hashes/unchanged main SDK, enable file and
private-settings absence are in menu-action-v10-trial/installed-baseline/receipt.json.
Launch initially returned no targetable window; process5244 was loading and
subsequently exposed window1902932. Continue loaded Fortress Indomita.

The v10 observer is executing. Desktop Accept friends while playing produced
idle-to-active at monotonic18034, with native ownership, tiny SHiFT view and
7 gameplay/0 UI contexts. This establishes Start, not menu handoff or actual
friend acceptance. Cursor became visible while desktop was focused; physical
focus/control behavior remains to be checked. No actual friend change is proved.

Martin is asked to focus BL4 and press Escape ONCE, leave the result visible,
and report whether Systems Menu opens on the first press. V10 remains installed
and game remains open for this physical test. No required approval is pending.
Rollback remains pending until normal Quit, then v10 deploy_trial.py restore
and verify. Do not use the restored v9 helper for this paired v10 installation.
Release HOLD; no production integration, final rebuild or publication claimed.

## Physical first Escape — 2026-11-12

Martin reports "it opened". CUA confirms Systems Menu open. Event148 at
18122.8503759 (monotonic time) changed
to paused=true/UI contexts=1 while background remained active/owned. There are
NO handoff_key, Close, or action-dispatch records for this press. Therefore the
first-press menu entry succeeded, but the v10 deferred-action repair did not run
and is NOT validated. Cursor had become true atseq60 while unpaused and stayed
true through entry. The SDK upstream cursor-visible callback gate is consistent
with this missing callback; exact installed native cause remains unproved.
Frozen trace: menu-action-v10-trial/first-escape-open.

Next physical step requested: with BL4 focused press Escape once more. If menu
closes, check W movement and mouse-look without holding a mouse button. If it
stays open, leave it for inspection. No further UI input sent by the agent.
Game remains open, accepter active, v10 pair installed; rollback pending.
Release HOLD. No app-access approval pending.

# V11 observed-menu trial checkpoint — 2026-11-12

Release HOLD. V11r2 is built and uninstalled. V10 remains installed, BL4 open,
accepter now stopped, SHiFT closed; Systems Menu remains visible for physical
exit-after-Stop testing. No required app-access approval is pending.

## Observed failure and controlled Stop

Martin: "esc did nto close the menu" on the v10 second physical Escape.
Frozen pre-mutation trace: ../menu-action-v10-trial/physical-exit-failure.
Events SHA256 dad8fe02c91c652a2a1df8cf9583923e8b44c2238c0d17c7dabe9d04457bdf5c.
Latest SHA256 e1b08534ba2514540d66b78f9eda047ce5bcf8db4084e2dd9b286d97d748dc2d.
SHiFT remained active/owned while paused with only context_ui_cursor among UI
contexts; no handoff key/close/action was logged. CUA confirmed Systems Menu.

Root clicked desktop Stop accepting friends, not Start AFK Lobby. Native Close
PRE/POST atseq1062/1063 (~19037.31 monotonic), idle/unpaused/cursorFalse at1064,
and five UI contexts at1065: menu_base_pc, news, cursor, menu_main, lobby_info.
Screen remained Systems Menu, with normal Back/Options hints restored. This
shows four missing UI mappings returned after SHiFT closed. It does not yet
prove physical exit or controls recover. After-Stop trace is in
../menu-action-v10-trial/after-stop-menu. No friend change was proved in this unit.

Current request to Martin: focus BL4, press Escape once; if it closes check W
and mouse-look without holding a mouse button. Physical result pending.

## Implemented experiment

V11 observes genuine menu state on the existing bound game tick, independent
of the SDK key callback and cursor flag. It closes an owned active SHiFT once,
preserves pre-close pause/cursor on unchanged PC/Pawn after exact closed and
quiescent checks, waits for a stable real menu exit, and starts a fresh lease.
Cursor-only context without pause does not count as a menu. Physical keys pass
through and no action injection module is packaged. Failed closes/cancellations
latch until a known menu exit or explicit Start; unknown state never rearms.

Root review plus independent delegate review completed. Additional regression
caught Start rearm being cancelled by synchronous native Open; corrected rearm
to follow successful original Start. Authenticated page requests rearm/cancel
only after the controller returns ok. Initial v11 archive is retained as
superseded evidence; use v11r2 only. No product implementation changed yet.

65 unittest checks pass in0.107s:57 relevant checks plus8 retained tests for the
unused v10 action dispatcher. Five Quick Menu/no-BLImGui regressions pass0.23s.
All seven packaged members pass compile/ZIP CRC/readback; build-receipt.json
records exact member hashes and sourceHEAD. Native trial remains unqualified.

Current candidate: ShiftManagement-menu-lifecycle-v11r2.sdkmod
SHA256 83ad774a4985560a429edb4a9f64f9ef59d20340e5dfda5c0156639d703adb83
Matching PAK SHA256 fdb039f13ea24c4b8b30b8cc972a83df7f6c71f20a09e7c5f916aebad6a9b93f.

Before installation: normal Quit, run v10 deploy_trial.py restore then verify.
Then use this directory's deploy_trial.py to install v11r2+candidatePAK with
backups; after trial normal Quit, restore and verify with v11's own helper.
Main SDK, real private settings and enable baseline remain preserved.

Remaining: physical exit-afterStop; v11 native pause/cursor preservation, menu
exit, normal controls, repeated Escape/Tab cycles, restart/bridge loss, resumed
actual acceptance and final package build/qualification. Desktop Stop and an
original-controller failed-Close retry still bypass preservation; this is a
recorded limitation to resolve before production integration/release. No
blanket control or release-ready claim is supported. Nothing published.

## Recovery confirmation — 2026-11-12

Martin reports "movement was restored" after the stopped-accepter test. He did
not explicitly confirm mouse-look. CUA now shows gameplay with no Systems Menu.
Frozen evidence: menu-action-v10-trial/physical-movement-recovery. Event5119 is
an unmanaged Escape while idle with five UI mappings; event5124 removes all
five UI mappings. This plus screen/user evidence confirms menu exit and
movement recovery after stopping SHiFT, not full control qualification.

Agent attempted one automated Escape to open normal Quit menu; it logged at
5574 but did not open Systems Menu. No repeat input sent. Requested Martin to
confirm mouse-look without holding a button, then press Escape once and leave
Systems Menu open. Once visible: normal Quit, v10 restore/verify, then install
v11r2 companion+candidatePAK and resume physical active-accepter tests.
Current game open/gameplay, accepter idle, SHiFT closed, v10 pair still installed.
V11r2 unchanged/uninstalled. No required approval pending. Release HOLD.


## V11r2 live setup - 2026-11-12 03:30 UTC

Martin's "ready" was followed by actual CUA verification of Systems Menu;
mouse-look remains explicitly unconfirmed. Normal in-game Quit succeeded.
V10 restore/verify passed at 03:24:21.188469 UTC; its final trace/receipt is
preserved in menu-action-v10-trial/closed-final. V11r2 companion and matching
candidate PAK were installed at 03:24:38.546023 UTC. Fresh installed-hashes.json
confirms companion 83ad774a4985560a429edb4a9f64f9ef59d20340e5dfda5c0156639d703adb83
and PAK fdb039f13ea24c4b8b30b8cc972a83df7f6c71f20a09e7c5f916aebad6a9b93f.
Released main SDK and enable-file hashes are unchanged; real private settings
file remains absent. Rollback is recorded in menu-observed-v11-trial/installation.json.

BL4 restarted once (PID6648), Continue loaded gameplay. Desktop Accept friends
while playing was clicked without starting AFK boosts. V11 observer seq234 at
24617.3282098 confirms idle -> active, owned/minimized SHiFT, unpaused with seven
gameplay mappings and zero UI mappings. Later cursor=true alone did not trigger
menu close, as intended; screen still shows gameplay. No actual friend action
has been established in this run. Game remains open with v11r2 pair installed
and accepter active for Martin's physical Escape-entry test. No required app
approval pending. Next: physical Escape once, inspect actual menu/close trace,
then physical exit, controls and automatic-resume tests. Release HOLD.

After live test: normal Quit, run menu-observed-v11-trial/deploy_trial.py restore
then verify; do not use the v10 helper for v11. Final production integration,
rebuild, package qualification and broader acceptance coverage remain pending.


## V11 physical menu entry - 2026-11-12
Martin reports one Escape opened the menu; CUA confirms Systems Menu remains
visible with Esc Back hint. V11 trace seq545 records menu_state_preserved,
seq547 close_succeeded at24923.0098348. SHiFT is closed/unowned, background idle,
pause and cursor remain true. Seq549 restores five UI mappings (from one).
Frozen trace/installation hashes: menu-observed-v11-trial/physical-menu-entry.
This qualifies observed-menu detection/close and pause preservation for this
entry only. Next physical Escape exit, W and mouse-look without holding buttons
remain unverified, as does automatic resume. V11 remains installed/game open
for physical handoff. 120-second handoff timeout may expire during chat delay;
if so resume requires a fresh short-cycle test. Release HOLD.


## V11 exit passes; V12 timeout repair prepared - 2026-11-12
Martin explicitly confirms Escape exited Systems Menu, W movement and mouse-look
without a held button all worked. Auto-accepter did not resume. Frozen trace
in menu-observed-v11-trial/physical-exit-timeout confirms menu observed at
24922.923931, intent cancelled at25042.9232416 (120.0s), and actual menu exit at
25096.0651928 (173.14s after entry). Source has unconditional120s overall timeout;
no restart was attempted. This is diagnostic timeout behavior, not evidence
that the native restart command itself failed.

V12 removes the arbitrary menu dwell expiry, retaining fresh same-player,
connection, known-menu and explicit Stop/Show/disable cancellation, plus the
3s never-appeared deadline and stable250ms exit. Separate delegate supplied
36 passing lifecycle tests including8h dwell, delayed first exit sample,
long-dwell cancellation/unknown state. Root combined suite64 tests PASS0.119s
(36lifecycle,18wrapper,4probe,6probe integration). Packaged Python compile,
seven-member ZIP CRC and exact readback pass. No redundant Quick Menu rerun:
existing5 passed and startup/bridge implementation unchanged.

New archive menu-observed-v12-trial/ShiftManagement-menu-lifecycle-v12.sdkmod
SHA256 deea23445833cfe69313f3ba48c16bf07705e6cdde56b59446763729c924f8eb.
MatchingPAK remains fdb039f13ea24c4b8b30b8cc972a83df7f6c71f20a09e7c5f916aebad6a9b93f.
V12 adds bounded reason/error diagnostic codes; never logs object identities/tokens.
V12 is NOT installed. V11 remains installed, game open in gameplay, SHiFT
closed/unowned and accepter idle. Released desktop2.41.1 AX still displayed
active despite native idle; status integration remains a release requirement.
User asked to pressEscape and leave SystemsMenu open for normalQuit; actual
latest CUA screen remains gameplay. No new live input or friend action issued.
After menu visible: normalQuit, v11 restore/verify, v12 install using its own
helper and exacthash, restart, test short and >120s menu dwell exit/resume plus
physicalcontrols. After trial normalQuit/v12restore/verify. Release HOLD.


## V12 deployment - 2026-11-12 05:21 UTC
CUA verified Systems Menu and normalQuit completed; no force-close used.
V11 restore/verify passed at05:21:01.433962UTC. V11 closed-final preserves
finaltrace and restorationreceipt. V12 installed at05:21:12.834300UTC; fresh
installed-hashes.json at05:21:52 confirms companion deea23445833cfe69313f3ba48c16bf07705e6cdde56b59446763729c924f8eb,
matchingPAK fdb039f13ea24c4b8b30b8cc972a83df7f6c71f20a09e7c5f916aebad6a9b93f,
unchangedmainSDK643f07653c3d2eb1ac1042018ea77fb0736bb074661aeaf600b91bc898fa5962,
enable1fc1cbce776047ccc54b0d40b36d3fb5ebca6b43bbfb775c74dc89c9c9b0c654,
andabsentprivatefile unchanged. BL4 launchedonce viaregisteredSteamapp;
startupwindow49220022 appeared after initiallaunchwindowdelay. Mainmenu
brieflydisplayedoffline; Continue clicked. NoConnect action or BL3 input issued.
BL3 runningwindow12455198 leftuntouched. V12liveobserverloaded; gameplay
andactiveaccepterqualification follows. ReleaseHOLD; normalQuit/v12restore
andverifyrequiredaftertrial, usingmenu-observed-v12-trial/deploy_trial.py.


## V12 active physical-test handoff - 2026-11-12 05:24 UTC
Gameplay loaded; desktop Start accepter succeeded, AFK boosts not started.
Observerseq134 at31506.294903 confirms idle->active, owned/minimizedSHiFT,
unpaused, seven gameplay/zeroUI mappings. Gameopen withv12pair installed;
physical Escape shortcycle and >120s dwell/resume remain untested. No real
friend acceptance/deletion outcome established in this unit.

FirstStartclick was denied by automaticapprovalreview for alleged missing
friendtestingauthorization; noinputexecuted. Read trusteduserhistory message
Sentinel_93433899230481918db7350001d9ece5 dated2026-11-10T05:58:23.590526UTC,
confirming requestedMSBTreleaseprep plus pendingfriendrequest/deletiontests.
One retry of samebutton afterfreshscreenshot succeeded; no approvalpending.
No workaround/indirectinput used. BL3untouched.

Correction: earlier staleactiveAX was fromhidden/occludeddesktop. Raising
MSBT refreshed to correctidle beforeStart. Independentreadonlyreview found
no foregroundpollingbug: currentcompanionstatus ->SDK0.5s snapshot ->Electron
4svisible/8shiddenpoll, immediatevisibilitypoll. Do notclaim provenstatusbug.
Production stillneeds explicitmenu-suspended/resumingpresentation rather
than presentingnativeidlealone; activeonlyafterconfirmednativeactivation.

Nextphysicaltest: Escapeopen, wait5s, Escapeclose, wait5s, checkW/mouselook
and minimizedSHiFTreturn; theninspecttraceforresumecommandandactualactive.
V12rollback remains pendingaftertest: normalQuit thenv12deploy restore/verify.
ReleaseHOLD.


## V12 short physical cycle PASS - 2026-11-12
Martin reports "that worked perfectly" for Escape entry/exit, W, mouse-look and
smallSHiFTviewreturn. Frozen physical-short-cycle-pass trace confirms observed
menu31606.2888365; close succeeded31606.394021; menu exit observed31613.9180912;
resume requested31614.2121504; command queued31614.2613338; actualnativeactive
31615.4277349. The queued success event alone is not activation proof; the
separate active transition provides it. Latesttrace staysactive/unpaused with
ownedminimizedSHiFT. No actualfriendchange proven in this cycle.

Long menu dwell >120s, Tab and repeatedcycles stillneedphysicalcoverage. User
asked for2.5min menudwell thenexit/control/resumeresult; no secondmenuobserved
yet. Gameleftopen,v12installed,accepteractive forphysicaltest.

Productionintegration started in isolatedproduct (notinstalled). Root added
companionbuilder entry fornewshift_menu_handoff module, boundednative_state
forwarding in mainSDK, and desktop paused-for-menu/resuming labels (overrides
staleAFK running flag duringhandoff). Root88 AFK/QuickMenu pytest PASS0.63s,
JSsyntaxpass, hiddenElectron AFK regression PASS. InitialsandboxElectron
launch exited1 withoutdiagnostic; escalationhiddenrunpassed. Independent
lifecycle/companionintegration and reviewdelegates active; finalproduction
companionbuild/review/livequalification/packages remainpending. Versions
unchanged; releaseHOLD. V12restore/verifyafterfinalnormalQuit stillrequired.
