# Mission completion release candidate

Based on published v2.35.2; only mission-specific modules, routes, desktop controls
and tests integrated. Guest persistence confirmed by Martin for Rev and Bubbah
following the 200-mission run. Two unavailable definitions display separately;
three nonpersistent replayable entries excluded. Unsupported objective/undo/full
reset controls remain disabled. Map/station coverage has separate proof boundaries.

Validation: 35 focused Python checks, release SDK import test, JS coverage/step
checks, 41-route Electron navigation with zero game actions, offline SDK installation,
packaged dependency graph and packaged asset hashes. See mission-build-verification.json.
Initial build using a shared dependency junction omitted transitive libraries.
Resolved with a local npm ci and rebuilt; no dependency versions changed. Copied
vendor resources at their required roots; nested staging copy retained outside the
packaged app. Local worktree helper junction/copy are not source changes.

No public version bump, tag, upload or publication. Current candidate metadata is
2.35.2 for local validation only, not a replacement public release. New user-facing
mission capability calls for a minor release when explicitly authorized. Public
installer/portable packaging follows lockstep versioning. Preserve the active
product checkout and running discovery job. Rollback UI/code through published
version; completed gameplay progress is not undone by replacing the package.
