# v2.41.2 release candidate - 2026-11-10

Martin requested preparing MSBT for release and explicitly permitted live pending
friend acceptance/addition and deletion for testing. Publishing, public uploads,
tags and metadata PR merges remain unauthorized. Small controlled social tests
are permitted; protected-list safeguards remain mandatory.

## Integrated source

Candidate branch `codex/shift-storage-repair-20261110`, based on verified v2.41.1
integration commit `b83d65b6`. The settings/background repair is combined with the
security-only patch from `C:/Users/mwenn/Documents/Codex/2026-11-05/task-4/MSBT-SECURITY-ONLY.patch`.
The patch applied without code conflicts; its primary-workspace index hunk was
excluded and this candidate's index maintained separately. No wholesale dirty
checkout merge. See the linked November 5 security and November 10 repair notes.

Local candidate versions are 2.41.2, a repair patch. The older resource metadata
was still 2.39.8 in the integration baseline; it is now aligned with Electron,
SDK and release metadata. Public main metadata/PR #18 are untouched.

## Review and validation

Combined main.js review verified distinct mobile and desktop preference paths,
canonical overwrite/reopen targets, account ID removal from trusted-root
construction, and independent installed/loaded SDK and SHiFT pair identity.
Mobile RPC supplies its own `mobile:true` event; caller arguments cannot override
that event. Enrolled tokens authorize LAN requests; IP only supplies routing
metadata. Shared-IP refresh no longer selects another phone's credential record.

SHiFT storage retains its exact same-game-process TCP ownership check, instance
binding, body limit, protected-list review and digest guards. Background state
uses the same companion owner. Review added flush/fsync before first publication
and edits, with injected flush failure checks proving no partial/new replacement
or loss of the old list. This does not claim power-loss durability of directory
metadata on all filesystems.

Independent review follow-ups repaired three additional candidate gaps. Mobile
phone removal now uses the supplied token when available and limits IP fallback
to legacy tokenless records, so removing one enrolled phone cannot remove other
phones that share its DHCP address. AFK status now forwards only bounded,
well-typed pending/error details from the companion. The background lease records
an explicit expiry reason, and its hidden presentation clears the WebView page
background to transparent. The transparent presentation change still needs a
live in-game confirmation because the first native run showed a white full-screen
background.

The SDK `__version_info__` tuple is checked against `__version__`, the SDK
pyproject, Electron package and release resource metadata before SDK packaging.
The artifact audit of the earlier package caught a stale `2.41.1` tuple and an
older `mobile_lan.py`; the tuple and build-time check are repaired, and the PAK /
companion are rebuilt from the pinned upstream archive. Final post-rebuild
installer artifact hashes and audit results are recorded separately below when
available.

- 119 integrated Python tests passed in 25.11s, including startup/import,
  packaging, mobile token/re-enrollment, storage HTTP and background lifecycle.
- Combined mobile JS tests: 10 passed, synthetic filesystem/RPC/store checks.
- Python AST validation: 131 SDK/helper files passed before packaging.
- Follow-up Python tests: 135 focused non-network tests passed; 46 loopback HTTP
  tests passed outside the network-restricted sandbox; 14 SDK packaging/runtime
  identity tests passed. The shared HTTP suite first failed under sandbox policy
  with Windows error 10013 before request handlers ran. Background JS syntax and
  lifecycle tests passed, including 20 repeated start/show cycles.
- Pinned SHiFT upstream archive SHA256
  `3e31ba6dfb91f014627df7cb9c453a34c8d13d2b49e1c6855bb8955f36ded440` was
  verified before rebuilding. The updated PAK SHA256 is
  `e32c9f2727c2e2c5d0c28304e2207540084085e3e1705dab911c72476ac4d1c2` and the
  companion SHA256 is `bfabdc0678608b5fd7911b5c6605dc21e15d0370e25c81f6231cfc73be8bc759`;
  192 payloads round-trip and the manifest records source/archive hashes.
- The initial artifact comparison passed portable and NSIS byte identity and
  resource hashes but preceded the review follow-ups. Its SDK version tuple and
  `mobile_lan.py` mismatches were stale-package findings and are corrected in the
  final package.
- Final Windows build passed installer unit checks (31), Electron package checks,
  48 packaged dependency checks, 3,323 resource checks, startup smoke and updater
  packaging. Artifact audit passed all 21 checks: the 1,497-file portable ZIP and
  1,565-entry NSIS payload exactly match `win-unpacked`; SDK syntax/version,
  mobile LAN fixes, PAK/companion digests and latest.yml SHA512/size all match.
  The first sandboxed build attempt stopped before packaging because .NET could
  not read Windows SDK registry information (MSB4184); the same build passed with
  permitted registry access.
  The reusable audit and full hashes are in
  `../candidate-artifact-audit/audit-results.json`; build output is in
  `../candidate-final-windows-build.txt`.
- Candidate installer SHA256 is
  `16acf4fdf3e2a822d9f2811b1dd96df659c0299f67a2082306b6f8e405a34bb0`
  (320,583,075 bytes); portable ZIP SHA256 is
  `f9576642014462b7b9ad9d8ad820b07d46ae79068ef102dcffec364a14fc7f2d`
  (381,078,919 bytes). The generated latest.yml SHA512 and installer size agree.
  No installer or game deployment was performed for this artifact audit.

## Acceptance and cleanup ledger

Native first Save and edit passed through in-game Save; restart reload remains
pending. The authorized friend acceptance run changed the count from 481 to 484
and pending requests from three to zero. No friend deletions or outgoing requests
occurred. The first native presentation had a white full-screen background;
foreground clicks after Show initially failed, while closing/reopening with F10
restored interaction. The source now clears the page background and reports lease
expiry, but this review follow-up has not been retested in game. Restart reload,
sustained polling/gameplay, menu/travel restoration and physical-phone validation
remain open. Hardware gamepad controls cannot be inferred from mocks.

The game was closed normally after the native candidate trial. The final rebuilt
game integration was briefly staged while closed, but the new launch request did
not execute because its mandatory app-access request timed out. All candidate
game files were then restored to their pre-test bytes. The first-created test
settings file was archived and removed, restoring its original absence; no real
protected-list file existed at the start of this trial. Fresh verification at
2026-11-10 07:13:29 UTC found no Borderlands4 process and exact original hashes
for the PAK, companion, main SDK and enable file. See the task-parent receipts
`candidate-installation.json` and `candidate-restoration-verification.json`.
No release, public upload, tag, merge or public metadata change occurred.

The desktop app itself remains the installed 2.41.1 machine-wide copy at
`C:\Program Files\MattsSDKBoostingTools`; its HKLM uninstall entry is
`{3bb825ae-d21c-574d-9e4d-33e5e736018a}`. The 2.41.2 installer was not executed.
The local upgrade/reinstall/rollback path therefore remains unqualified, separate
from the successful build and payload audit.

## Remaining release gate and exact access blockers

**Not ready to publish.** The final candidate is built and byte-audited but has
not passed its own native restart reload, corrected transparent presentation,
normal keyboard/mouse/gamepad gameplay, desktop Start/Stop, menu/travel cleanup,
or actual installer upgrade/rollback. Mobile authority and token checks passed
offline; a physical phone was not tested. No live deletion was attempted. The
three incoming requests cleared during the initial native candidate runs
(Bruzer, GingerFuchs, YoMumma; friends 481 -> 484, pending 3 -> 0).

The following required Computer Use permissions had no visible user resolution
when checked after timeout; these are tool-access requirements, not additional
implementation permission requests or automatic approval-review rejections:

- Access the installed MSBT desktop window (`MattsSDKBoostingTools.exe`, window
  198718): `broken-bonus-72966088`. The call timed out; no desktop control,
  closure, installer invocation or installed desktop mutation occurred.
- Launch the known Borderlands4.exe path for the corrected candidate retest:
  `muddy-haze-43205456`. The call timed out; both window inventory and a fresh
  tasklist verification established that the launch did not execute.

The parent can resolve those access requests before resuming the remaining live
qualification. Do not reuse the restored installation receipt as a fresh install
receipt: archive it and create a new guarded trial with current-state hashes.
The official 2.41.1 rollback installer is saved in the task parent's
`release-rollback` folder and its SHA256 was verified against GitHub's release
asset digest (`0cee6605cbbe132256caa034dee3e0500aa5a6645ee8d3065fc388a358f9173e`).

Independent source review identified a plausible foreground handoff gap:
background entry forces GameOnly input; Show restores native widget visibility
in the pre-open hook before invoking the native Open body. The first live Show
made the page visible but clicks initially did not respond, whereas F10 close /
reopen restored interaction. An early-return inside native Open is a hypothesis,
not recovered executable evidence. Do not change native setter ordering on that
assumption alone. Compare the two transitions live and fix the demonstrated
handoff before qualification. The transparency repair remains source/test
validated only because the follow-up launch was blocked.

Windows native process ownership and the executable adapter are platform-specific.
Linux/Epic qualification must be stated separately; Windows mocks do not qualify
them. No public release readiness claim is made at this checkpoint.

## Resumed investigation, 2026-11-10

Resumed from clean `ebc0dad5` without changing production implementation or
rebuilding the already-audited packages. A fresh desktop access request,
`little-shape-91732408`, timed out; the parent subsequently cancelled it and
directed live app work to be deferred while the user is unavailable. The older
requests above are historical expired requests, not reusable permissions. No
game launch, installer execution or live social operation occurred in this
resumed phase. Fresh verification at 09:06:44 UTC again confirmed no game process,
all four original game-file hashes and original settings-file absence.

The bounded native review reconfirmed the installed executable SHA256
`ba75f7c2874b16efb5536a5c0cc28918a03efd3e55d790d2e4db57de0c3a353a`.
The referenced shipping PDB is not installed. Available prior artifacts contain
reflection results and visibility snapshots, not recovered native Open logic.
In particular, an immediate Open sample and a later sample disagree on
IsVisible, so they cannot establish an early-return condition. The Show input
failure remains unresolved; no native setter-order change was made from that
unconfirmed theory.

Installer preparation now includes a task-local guarded snapshot/comparison/
helper-restoration script. Independent review found missing-backup versus
original-absence ambiguity, incomplete preflight validation and path validation
gaps in its initial draft. That draft was never executed against the installation.
The official rollback installer remains a required part of the planned desktop
rollback; restoring helper files alone is not a complete desktop rollback.

Independent work completed before deferring the live steps:

- Task-parent `show-input-diagnostic/README.md` documents the bounded observer.
  Its current uninstalled archive is
  `ShiftManagement-show-input-diagnostic-rlock.sdkmod`, SHA256
  `94e7014add6f48ac9fd1d013e9f4a254886f340fbfcb8d262151428675c70362`.
  Exact original companion/source hashes remain pinned; documentation-only
  descendant commits are allowed. It observes Show/pre-open/pre-close and the
  next two ticks, stops probing after 64 records, and records only visibility
  and input booleans. Native probes do not run under the file-log lock. Five
  synthetic tests passed, including reentrant callbacks and unchanged original
  return/exception behavior; syntax checks passed. The compiled native JSONL
  log remains empty. This observer is not a release asset or native test pass.
- Task-parent `installer-trial/installer_trial.ps1` and `PREPARED.md` now contain
  the reviewed trial workflow. Complete backup hashes/inventory are preflighted
  before any mutation; paths and file/folder types are checked. Comparison
  canonicalizes maps and includes user-data fingerprints. Six isolated fixtures
  passed: corrupt backup, missing backup, file-target obstruction, actor-folder
  obstruction, restoring original absence, and byte-exact helper/preferences
  recovery while preserving the PAK and unknown preference files. Both scripts
  passed PowerShell parsing; independent review cleared offline preparation.
  No live baseline backup, installer, registry change, or installed helper-file
  restoration occurred in this resumed phase.

Production source and Windows package bytes remain the previously audited
candidate. No rebuild was needed for these task-local diagnostics/recovery tools
or the updated durable notes. The installer SHA256 remains
`16acf4fdf3e2a822d9f2811b1dd96df659c0299f67a2082306b6f8e405a34bb0`;
portable SHA256 remains
`f9576642014462b7b9ad9d8ad820b07d46ae79068ef102dcffec364a14fc7f2d`.
Final fresh verification at 09:21:52 UTC again confirmed a closed game and the
original four hashes/settings absence in `candidate-restoration-verification.json`.

All live acceptance gates listed above remain open. Fresh MSBT and Borderlands
app access is needed when the user is available; do not repeatedly create prompts
or imply native tests are running while access is deferred.

## Actual candidate upgrade and native diagnostic, 2026-11-10 15:58 UTC

The user resumed live qualification while available. Fresh CUA access succeeded.
The correctly escaped BL4 executable path launched on 9800x3d4090; earlier
malformed path requests are not permissions and should not be reused. A separate
Borderlands 3 process was already present on the 4090 and was left untouched.

The pinned 2.41.2 installer ran `/S`, exit 0. Before/after snapshots in task-parent
`installer-trial` confirm app/registration 2.41.1 -> 2.41.2, all nine named
preferences and all 27,358 user-data files unchanged. All six captured shortcuts
remain; the machine-wide link still points to the Program Files app. Three
pre-existing legacy user shortcuts were unchanged. Helper changes are recorded
explicitly: candidate PAK/SDK/companion, three enabled mod settings, and
ActorScriptDeployer inventory 4 -> 3 files. The exact candidate unpacked tree
matches all 1,497 installed payload files by path/length/SHA256; only the expected
NSIS uninstaller is extra. The initial audit against an unrelated stale October
`product/dist_electron` tree was corrected and superseded.

A fresh guarded native receipt is task-parent `live-qualification/installation.json`.
It supersedes the earlier restored trial receipt for current installation state.
At this checkpoint the 2.41.2 desktop/game files are temporarily installed, with
the reviewed diagnostic companion substituted. BL4 PID 48548 was closed normally
via Alt+F4 and process absence checked. The desktop candidate remains open. No
forced game termination occurred. Original backup hashes are preserved in the
fresh receipt; cleanup and actual desktop rollback are still required.

The observer run established:
- First Save created the previously absent private JSON with the synthetic
  protected name `MSBT_Release_Test_20261110`, reviewed=true. SHA256
  `c4052eca900fd04c950a55cac7036b369d982f4fd80c782e30844c03e69ad0f9`.
  The UI confirmed connected persistent JSON storage.
- An edit to iconMode=switch persisted, SHA256
  `b52a86fa2c409890d663c8aaa9c91bfd04af5ece69be52c806a029c6f8ee5b7f`.
- The white background repair passed visually: only a tiny SHiFT panel remains
  opaque, with gameplay visible everywhere else.
- Show still fails input. After Show, a Manage SHiFT click passed through and
  fired one round (19 -> 18). A normal F10 close/open then allowed the same
  Manage click to open its dialog. Observer seq6-21 captures the transition:
  Show restores container visibility while canvas remains2; a native reopen
  goes through canvas25. This is transition evidence, not recovered Open code.
- W/Space/Tab short synthetic taps in background gave no immediate visible
  change; keyboard gameplay remains inconclusive, not passed.
- Bridge samples show active/running=true and foreground/running=true after
  Show. No new social effect was identified in this run. Historical three
  accepted requests remain separate evidence.

Receipts: `live-qualification/diagnostic-result.json`,
`live-qualification/background-diagnostic.jsonl`,
`live-qualification/installed-payload-audit.json`,
`installer-trial/compare-after-candidate.json`, and
`show-input-diagnostic/native-show-input-rlock.jsonl` in the task parent.
Source repair and final native/package requalification remain in progress.

The narrow Show handoff repair now calls the existing guarded native Close path
from `BackgroundController.before_open()` after restoring its owned widgets,
then permits the original Open. This applies to both desktop Show and direct
F10 Open. A pending failed Close must complete before another Open can continue.
No native canvas setter, raw-memory layout, access-control or settings-format
change was made. Root reviewed the source and the immediate-retry failure case.
Seventeen lifecycle tests pass (three new transition/failure cases); the combined
lifecycle/native/startup/routing run passes 34 tests in 0.50s. Python syntax and
`git diff --check` pass. A delegate's broader storage test attempt encountered
sandbox WinError10013 on localhost binding; it is not a product regression.
Production native retesting and refreshed packages are still pending.
