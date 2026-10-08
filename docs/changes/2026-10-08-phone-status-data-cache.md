# Repeated phone tool-data downloads — 2026-10-08

## Symptom and evidenced cause

Matt reported the full Android workspace constantly displaying Downloading tool data and asked whether the phone can hold its data locally. The workspace/editor assets already ship inside the APK. The repeated transfer was live `/status`: the measured response was 1,981,831 JSON bytes, dominated by copies of the previous serial text, read/drop results, and AFK loot configuration. The five-second status cache reduced call frequency but still resent these unchanged lists. Generic multi-part transport labeled any large response as tool data, making status updates look like repeated installation.

## Change

Source remains the isolated current-release checkout `C:/Users/mwenn/.codex/worktrees/remove-markdown/working`.

- `electron_poc/mobile_desktop_api.js`: opt-in status compaction for paired mobile `bridgeRequest(GET /status)`. Long strings and large arrays become SHA256 references. Identical content is sent once, and a phone advertising a cached hash receives references only. All dynamic status fields continue to be read from the game; desktop responses and other commands remain unchanged. No game action is cached or replayed by this mechanism.
- `mobile_controller/app/src/main/assets/desktop/desktop_shim.js`: reconstruct the original status shape before giving it to the Windows renderer. Verify incoming content hashes and store the large strings/serialized arrays in phone IndexedDB. Cache is bounded to 64 entries/16 MiB and reused after workspace reloads. Changed lists receive a new hash. Existing five-second status coalescing and hidden-workspace behavior remain. Older PC companions returning ordinary status remain compatible.
- `mobile_controller/app/src/main/assets/desktop_mobile.js`: remaining genuine data transfers display Syncing PC data, rather than implying tools are being downloaded. The change in transfer behavior comes from caching, not the label.
- `test_mobile_desktop_api.js`, `test_mobile_windows_workspace.js`: duplicate list handling, unchanged/changed data, live player/AFK field changes, string/array reconstruction, and IndexedDB reuse after a real iframe reload.

The phone still requests live players, AFK progress and command results. Catalog/community refreshes, newly selected files, or changed lists may still require data transfer. This fix specifically eliminates retransmitting unchanged large status lists; it is not a claim that all PC files and online catalogs are permanently mirrored offline.

## Validation

API and actual shared-workspace regressions pass, including all 17 tabs, original imports/editor/file routes, delayed uploads, and persistent cache reopening. An initial persistence assertion observed the old iframe before navigation completed; waiting for its actual load event fixed the test. An initial request-inspection assertion checked the downstream bridge helper, which intentionally destructures ordinary bridge arguments; the corrected assertion inspects actual mobile transport calls. These were test-observation errors, not evidence of a working persistent cache until corrected.

Measured against the live status snapshot: first compact synchronization 1,002,756 JSON bytes; later synchronization with the two unchanged lists already held by the phone 18,061 bytes. These are application JSON sizes before compression/encryption, not measured network traffic or hosted-token savings. AFK enabled and Borderlands PID 71280 remained running. No manual item/progression action was sent. JavaScript/Python syntax, five required Quick Menu/no-BLImGui checks, Android build and lint pass.

Native phone checks after installation retained remote pairing, reached the live host target in the full workspace and returned to Connected remotely after initial synchronization. Some initial data transfers were still observed; these are not proof of completely transfer-free catalog/editor startup. Persistent reopening and unchanged-status reconstruction are proven by the shared-renderer regression, rather than claimed from native pixels alone. Phone controls were left available for Matt; no additional manual gameplay test was sent.

## Local deployment and rollback

Installed the locally built signed APK without clearing app pairing/data. Pulled-phone APK SHA256 matches the build: `4c2fda6d62b3ad20c12f4448009be2936f4190511864dd3fe47d6273858ae540` (28,079,930 bytes). Installed desktop archive SHA256: `a2386cb7c47f53c0bb0ae3aae03eb303e9ec212079f4e3c6349795239674cb1f`. Only `mobile_desktop_api.js` differs from the preceding installed archive. Full comparison against the original workspace backup still finds exactly the six intended workspace files changed, with all other entries including SDK resources unchanged.

Backup `output/mobile-windows/app.asar.before-status-cache` has SHA256 `4579cd9a4f49c8be66d7a0fc17fc0e217a0da70a537d70f73fab6e152f3fe213`; restore while MSBT is closed to roll back PC compaction. The preceding local APK hash is recorded in the workspace entry; source/build history can regenerate it. The newer phone remains compatible with that older PC response shape. Receipts and native XML are in `output/mobile-windows/`. Desktop was closed normally and restarted by this task. The native phone initially showed SHiFT disconnected after that restart; Open SHiFT restored the pre-existing helper connection, confirmed by live readback. AFK itself stayed enabled throughout. No release, version bump, SDK replacement, or relay deployment.
