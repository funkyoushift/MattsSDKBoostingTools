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

The game was closed normally after the native candidate trial. Candidate PAK,
companion and SDK files remain temporarily installed while the parent task owner
handles restoration from fresh backups; `../candidate-installation.json` records
the original and candidate digests. The earlier diagnostic phase was fully rolled
back, with its receipt in `../rollback-verification.json`. No release, version
publication, or public metadata change has occurred.

Windows native process ownership and the executable adapter are platform-specific.
Linux/Epic qualification must be stated separately; Windows mocks do not qualify
them. No public release readiness claim is made at this checkpoint.
