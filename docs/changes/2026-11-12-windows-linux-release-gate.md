# Windows and Linux required release gate - 2026-11-12

Martin requires Linux support for releases. The old unified workflow built both
platforms, but Linux only packaged outputs: it did not execute native desktop,
installer or updater verification. No aggregate job prevented a missing/skipped
platform being mistaken for a releasable result. Manual publishing could proceed
without both native qualification records.

The new unified workflow requires Windows and Linux native platform verification
and an aggregate four-artifact/receipt check. Windows now hashes every installed
file, checks ZIP parity, executes installed updater checks and writes a source/
version/hash receipt. Linux extracts AppImage and relocates TAR, compares contents,
modes and symlinks, verifies source/SDK/PAK/companion identities, runs real bundled
Python and desktop smoke, a real temporary-HOME installer and native updater/
rollback plus Proton discovery/setup fixtures. CI prereqs are installed only on
its disposable runner; no package manager was invoked on the user's computer.

A stale Linux setup-service test omitted the SHiFT companion now required by the
installer. Its fixture now contains the real companion contract/hash and checks
installation/enabling, missing/tampered bundle handling and preservation of old
PAK/companion/settings. This is a test repair, not proof of an installed-game bug.

The common gate rejects missing platforms/checks, stale commits/versions, wrong
formats/names, missing or altered artifacts and mismatched live-evidence hashes.
The new publisher defaults to check-only and additionally requires both native
BL4/Proton evidence records, successful exact-commit CI jobs and matching tags.
It verifies a draft's four remote digests before publication. The legacy Windows-only
publisher now refuses mutation and points to the required gate. No new release or
version bump is authorized by this work. Published 2.41.2 assets remain unchanged.

Local instructions and Cursor mirrors now require both OSes; public policy is in
docs/RELEASE_GATE.md. Live evidence is an attestation referencing actual reports,
not a claim that JSON proves gameplay. Owner privileges on GitHub remain unchanged.

## Validation and environment

Twenty-two gate/publisher/Linux-verifier unit tests passed on Windows, plus
Python syntax, PowerShell parsing and diff checks. Linux-specific desktop/setup
execution requires CI Linux; current workstation is Windows 4090 with no WSL.
A read-only integration review passed four Node suites and 29 mocked background/
menu tests. Broader HTTP attempts encountered sandbox loopback denial and are not
recorded as runtime passes. Linux/POSIX fixtures skipped or failed on Windows as
expected; actual Linux results will be appended after CI.

Linux BL4/Proton same-process companion TCP authorization, first-save/restart,
background/menu controls, travel and social effects remain live-unqualified for
2.41.2. Windows APIs within Proton-hosted Windows Python were not proven broken;
this environment cannot establish their live behavior. Setup preserves backups
and pending/retry status but is not a transaction spanning SDK, PAK and enabling
stages; failure recovery needs native qualification. These are explicit future
publication gates, not silently waived platform support claims.

No game/desktop control, installed-game modifications, host software install,
public asset replacement or release publishing occurred. Work is isolated under
local/linux-release-gate/product; existing dirty work is preserved. Rollback is
reverting the scoped tooling/policy/fixture commit; runtime implementation and
installed 2.41.2 are unchanged.

## First native CI and default-branch enforcement

Run 43302271379 built both Linux packages and confirmed all 6046 staged files
matched the extracted AppImage/portable, then rejected an incorrect verifier
comparison: SDK staging intentionally replaces LICENSE and notices from project
root/docs. The verifier now reproduces those deterministic inputs and requires
exact ZIP inventory; tests reject stale legal text, tampered code and extra files.
Windows runtime/regression checks reached the desktop test, which raced a splash
element removed by the real nosplash path after 280 ms. Optional removal repairs
that fixture while preserving AFK visibility assertions. Neither fix changes
production runtime. The aggregate gate correctly failed the run.

Default-branch policy PR #20 merged at cd9ed8f92ce8a3e3e7f497ac7520e19f68edc456
after both OS policy suites passed. Its former tag workflow could automatically
publish Windows-only assets; it is now read-only metadata verification. The
legacy mutating publisher is blocked. Main runtime is actually 2.39.9 despite
2.41.2 download metadata; copying the full native workflow there would require
unrelated runtime integration. The scoped policy documents this and points to
the released-source verification branch. No runtime source was bulk-merged.

Run 43302963095 at corrected source 08d6eb68 passed Windows completely: startup/
SHiFT regressions, installer build/audit, all installed-file hashes, portable ZIP
parity, bundled Python, installed smoke and installed updater. Linux payloads,
source identities, bundled Python and read-only library probe passed, then native
AppRun aborted 133 at Chromium sandbox initialization. Runner log identifies
Ubuntu 26.04.1 / image 20261111.196.1. AppArmor user-namespace restrictions are the
leading explanation, not proven without the denied-operation host audit. This is
a real compatibility limitation for similarly configured hosts; not waved away
as an innocuous CI failure. Aggregate gate failed as intended.

A separate Ubuntu 22.04 compatibility run 43303801032 at 24a9f0b2 preserves all
sandbox behavior and records host environment. It cannot waive the newer-host
failure or native game qualification. Current source and docs expose the limit;
no global namespace changes, root-owned sandbox installation or no-sandbox flags
were used.

## Ubuntu 22 baseline results

All 13 native Linux checks passed on Ubuntu 22.04.5, kernel 6.8.0-1070-azure,
non-root runner UID 1001. Host policy was recorded unchanged:
apparmor_restrict_unprivileged_userns=0, unprivileged_userns_clone=1,
user.max_user_namespaces=63862. This is a different tested configuration from
the failed Ubuntu 26 host, not a workaround applied to it.

PASS: AppImage extraction; 6046-file/mode/link payload parity; exact packaged
source/SDK/legal/companion identities; bundled Python; library probes; actual
AppImage/relocated-portable smoke with updater enabled; real installer UI,
AppImage copy, receipt, menu shortcuts and installed launcher in temporary HOME.
Proton discovery/setup/status and updater download/activation/rollback fixtures
passed on Linux; they do not constitute actual Proton game or public updater
upgrade proof. Benign headless DBus/font messages were present in the successful
installer output. The verifier retained the complete result.

Rebuilt diagnostic artifacts (not uploaded to public releases):
- AppImage 281611185 bytes, SHA256 65939051089cc91993203b380d25957f2aa71fc3ebc98be64621a7e6c7f3e386.
- TAR 301759729 bytes, SHA256 d7883fb24266f7b854207d2caa4e2f991e9275f27a99cce5092c1374c7a98db5.

Local evidence: ../review/run-43303801032/linux-platform-verification.json and
linux-host.txt, relative to the enclosing local/linux-release-gate directory.
The Ubuntu 26 failure receipt/log are under ../review/run-43302963095.

Publisher review additionally bound local files to the exact CI aggregate
receipt's four hashes/sizes, not just its successful source SHA. Nine publisher,
seven common gate and six verifier helper tests pass. Native coverage remains
separately required. Follow-up policy/documentation PR #21 merged at 65193cc99d422a6667acc018d8717e3e5cd7fdfa after both OS policy suites passed.

## Final outcome

Run 43303801032 completed SUCCESS: Windows, Ubuntu 22.04 Linux and the aggregate
four-artifact gate all passed for 24a9f0b283e1bd06e61eb1e9d67460fcc4a26d8b.
The aggregate receipt correctly says publication_ready=false because actual
Windows/Linux native qualification records were not supplied. The publisher's
new exact-run artifact provenance lookup also passed against this real CI receipt
(read-only; no preparation/publish call or release mutation).

Windows CI includes 62 Python regression tests, SHiFT browser/controller tests,
update handoff and actual package install/ZIP/runtime/updater verification. The
Linux regression stage ran 7 gate + 7 publisher + 6 verifier + 18 bootstrap tests
at this candidate; later publisher hardening has 9 passing tests on both policy
CI operating systems. There are 13 native Linux verification records.

Final aggregate receipt is at
C:/src/MSBT-Workspace/product/local/linux-release-gate/review/run-43303801032/release-verification.json
and includes exact four artifact sizes/SHA256s. These are diagnostic rebuilt
packages, NOT replacements for published 2.41.2. Existing release digests were
read back unchanged. No installed-game, desktop-session or user settings changes.

The requested release gate is established on main through PR #20/PR #21 and in local
workspace/Cursor instructions. Complete runtime verification remains on the
isolated released-source branch; main's older runtime was not bulk-merged.
Remaining release blockers: Ubuntu 26.04 sandbox startup compatibility and actual
BL4/Proton game qualification (same-process storage authorization, protected-list
Save/edit/restart, background Start/Stop, menu/keyboard/mouse/gamepad behavior,
travel and observed social effects). No Linux game host was available. No
app-access approval is pending and none is needed for the completed CI work.
