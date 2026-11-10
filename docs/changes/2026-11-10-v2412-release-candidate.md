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

- 119 integrated Python tests passed in 25.11s, including startup/import,
  packaging, mobile token/re-enrollment, storage HTTP and background lifecycle.
- Combined mobile JS tests: 10 passed, synthetic filesystem/RPC/store checks.
- Python AST validation: 131 SDK/helper files passed before packaging.
- SHiFT PAK: 192 payloads round-trip; manifest records source/archive hashes.
- Remaining JS, packaged and native results will be appended as executed.

## Acceptance and cleanup ledger

No live friend action has occurred in this candidate phase yet. Native first
save/edit/restart, Start/Stop from both surfaces, sustained polling/gameplay,
menu/travel restoration, controlled social effects and physical-phone validation
remain pending. Hardware gamepad controls cannot be inferred from mocks.

The previous diagnostic session was closed normally and fully rolled back;
`../rollback-verification.json` relative to the candidate worktree records that
receipt. New candidate deployment must use fresh backups and restore normal
state on completion. No game has been reopened in this candidate phase yet.

Windows native process ownership and the executable adapter are platform-specific.
Linux/Epic qualification must be stated separately; Windows mocks do not qualify
them. No public release readiness claim is made at this checkpoint.
