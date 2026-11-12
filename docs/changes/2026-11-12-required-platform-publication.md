# Required Windows/Linux publication policy - 2026-11-12

Martin requires Linux support and platform verification for releases. The default
branch's tag workflow could publish Windows-only assets, and the legacy publisher
could overwrite existing release assets without Linux verification.

The tag workflow now has read-only permissions and only validates coordinated
tag/version/platform metadata. The legacy publisher refuses mutation and retains
its explicitly nonqualifying audit mode. The supported publisher requires exact
Windows/Linux artifacts and receipts, native game evidence for both platforms,
matching tags and successful exact-commit CI platform and aggregate jobs. It
stages four artifacts in a draft, verifies remote digests and publishes only after
validation. Existing releases cannot be overwritten. Owner GitHub privileges
remain unchanged; this is tooling/policy enforcement, not a server-side ban.

The default branch has package 2.39.9 source despite 2.41.2 download metadata; full
native verification lives on codex/linux-release-gate-20261112 over the released
implementation. Copying its build workflow onto this older source would require
unrelated runtime integration, so that is deliberately excluded from this scoped
policy repair. See docs/RELEASE_GATE.md.

Validation: 14 gate/publisher mocked unit tests pass locally. New policy CI repeats
them on Windows and Linux. No runtime changes, game input, package publication,
version bumps or existing asset changes. Native Linux BL4/Proton gameplay remains
unqualified; package/fixture results cannot substitute for it. Rollback is revert
of the scoped policy commit, though doing so would remove the requested gate.

## Follow-up verification

PR #20 merged at cd9ed8f92ce8a3e3e7f497ac7520e19f68edc456; default-branch policy
CI 43303009983 passed on both OSes. The publisher now compares local artifact
digests with the actual CI aggregate receipt, preventing a same-commit rebuild
from being mistaken for CI-tested bytes. Nine publisher tests and seven common
gate tests pass. README/Linux docs now expose native Ubuntu 22 desktop PASS,
Ubuntu 26 sandbox startup FAIL and actual Linux game coverage NOT TESTED; see
docs/RELEASE_GATE.md for evidence links. No release assets or runtime changed.
