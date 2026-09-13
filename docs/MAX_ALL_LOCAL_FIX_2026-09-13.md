# Local Max All compatibility fix

Follow-up button fix: Local and Named Player now send explicit `party_indices`,
like All/Other Players, instead of a separate shared-target request or a cached
selection followed by an empty payload. This avoids target changes between those
steps and uses the batch timeout for single-player boosts too. The button disables
while its request runs, rejects duplicate sends, and displays rejected connection
errors. Missing result counts stay unknown, rather than becoming zero via `Number(null)`.
`npm run test:max-all` exercises the real click handler in Electron with a fake
bridge for all four scopes, missing targets, duplicate calls, queue acceptance,
and connection failure. No in-game action is executed by that test.

The source panel batches All Players / Other Players with `party_indices`.
The installed 2.10.1 archive still discarded that payload and called selected-only
`max_all()`. The source batch implementation existed but was not packaged.

The local workspace and installed sdkmod now contain a focused port of that
implementation: the backend's Max All functions and the bridge's payload forwarding.
All other archive entries are byte-for-byte unchanged. No version or release changed.
The selected-player call still works with an empty payload; batch calls run each
requested controller once and apply session fog once.

Validation: every packaged Python module compiles; archive integrity passes;
four selected/batch routing tests pass against the staged archive's backend.
These stub tests do not establish in-game unlock completion. Borderlands 4 was
closed during installation, so live Max All validation remains outstanding.

Installed/workspace SHA256:
`3d8f13fd543f07b6b6bf0169d6e30d5ec5462670067293813653f81675e577d1`

Backups: `_tmp_max_all_fix/backup_20260913_033451/` contains separate original
workspace and installed copies, both originally SHA256
`95fdfac9c400ca6152eaadfc06c59dd11072ac2670ba25da13da6ede73abaa3f`.
