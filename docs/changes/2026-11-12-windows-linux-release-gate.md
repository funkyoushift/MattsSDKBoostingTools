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

Nineteen gate/publisher/Linux-verifier unit tests passed on Windows, plus
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
