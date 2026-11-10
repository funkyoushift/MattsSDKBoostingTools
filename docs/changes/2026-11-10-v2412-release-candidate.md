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
