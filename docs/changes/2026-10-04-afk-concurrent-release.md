# AFK concurrent release v2.28.0 — 2026-10-04

## Scope and evidence

Matt explicitly authorized preparation and publication after two guests reported correct persistent 500-item counts. Read the [pilot evidence](2026-10-04-afk-concurrent-pacing.md) and [count-display fix](2026-10-04-afk-delivery-count.md) first. Release work is isolated at `C:/Users/mwenn/.codex/worktrees/afk-concurrent-release/working`, based on published v2.27.0 (ef7f069); unrelated dirty checkouts are preserved.

The old AFK scheduler owned one current guest, and the serial queue rejected a second request even though direct-delivery timing was already per target. The released scheduler defaults ordinary guest runs to concurrency, with up to three independently targeted deliveries. The underlying insertion/chunk/settlement timers are unchanged. Existing readiness, authorization, class filtering, cancellation and connection-aware kick protections remain. Shared challenges/UVHM retain one owner. Cleanup and host-test modes automatically remain sequential, with explicit incompatible concurrency requests rejected; callers can also explicitly select sequential behavior. Manual deliveries stay exclusive.

The desktop renders separate active-guest rows and authoritative running configuration. It excludes started jobs from the waiting label and does not interpret submitted counts as guest-save acknowledgements. Starting AFK after stopping uses concurrent mode automatically; the release includes no pilot loader, expiry or console activation requirement. Runtime pilot scripts and private experiment receipts are excluded from this release.

## Files

Production: `afk_lobby.py`, `serial_rewards.py`, `electron_poc/afk_lobby.js`. Focused tests cover concurrent default/Stop-Start, manual exclusion, three-target queuing, departures/world changes, shared operations, exact independently selected counts, smaller/short pools and desktop status/storage. Coordinated desktop/SDK/resource version holders and release metadata move to 2.28.0. Durable notes and the notes-first project rule are included.

The phone-side stale-count source fix remains in the prior development checkout. No Android device was connected for a new install/launch check, so this release carries forward the exact already-published 1.5.0 APK and unchanged mobile source. Existing phone AFK starts use the new SDK's default concurrency; the phone UI does not gain per-player progress in this release.

## Validation before packaging

- 204 focused Python checks passed, including release imports and publisher preflight, startup/Quick Menu no-BLImGui, concurrent and sequential counts (1/35/70/71/85/500), cleanup recovery, shared steps and kick settlement. Five package/spec warnings originate in test loaders.
- Actual Electron count/authentication and per-guest display tests passed; large AFK lists survive reload; settings survive two complete exits/restarts, including unchecked values.
- Mobile source UI tests passed during preparation, but this does not replace Android device evidence and the new mobile source is excluded as above.
- Syntax compilation passed before SDK packaging. First count-suite failures were an incomplete test stub missing the new queue-admission helper; coverage was expanded to both modes and the stub corrected. The release build correctly rejected shared node_modules; removed only the verified junction and installed independent locked dependencies with npm ci.
- Two live guests simultaneously receiving different counts were observed, then both completed 500/500 and confirmed counts and persistence from their games via Matt. Three simultaneous guests have offline coverage only.

## Deployment and follow-up

Packaging, installer checks and publication verification will be recorded below. Keep the existing active lobby until it finishes; updating the installed SDK requires a later game restart to load the permanent release. Rolling back uses v2.27.0 desktop/SDK together. No inventory rollback/replay is performed. Remaining work: Android display fix with device validation, live three-guest validation and broader long-session observation.

## Final pre-publication checks

Final v2.28.0 installer and portable build passed: 31 installer checks; bundled runtime graph (48 packages); 2,984 packaged asset comparisons; real offline SDK-install preservation/partial-install/PAK verification; packaged startup smoke and updater integrity. Re-ran count/auth, per-guest UI, large-list reload and complete settings exit/restart against the final app.asar successfully. All AFK test files passed (227 checks). Additional guest/serial/bridge tests passed (20), and all four settings-disk checks passed in a separate process. Combining settings with unrelated tests exposed cached registry stubs; isolated execution resolved the test-only collision without production changes. The earlier targeted 204 checks overlap these suites and must not be added as a distinct total.

Build metadata references source commit 103c134596858081e57cb74aff1f28e6f3c9fc50. A final rebuild embeds that exact metadata; do not stamp git_commit after packaging. Android 1.5.0 rolling/versioned files both match the prior public SHA256 391d9e4d531f998e90564eda9e8c417721cd7222f6ee104f1d5d968e49955b34. Publication assets and individual hashes are recorded in work/release-v2.28/assets.json and SHA256SUMS.txt.

## Published and independently downloaded

Published stable, non-draft [v2.28.0](https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/v2.28.0), tagged at 47153ffa8c4c6eef22c17e4f765743336ad1dd07 and selected as GitHub Latest. Main and codex/afk-concurrent-release were pushed. Publisher preflight passed for all 11 assets. Downloaded every public asset; all 11 matched local bytes/size, local SHA256 and GitHub's asset digest. The downloaded portable SHA256 is 8446b2e11d57d144b80638dbb6ec2f8c166d70206f31c57674a4091782019bab. Public receipts are stored at work/release-v2.28/public-verification.json.

`dotnet run --project installer/Tests.csproj --configuration Release -- --live` downloaded v2.28.0 through the actual Latest endpoint and passed 33 checks, including official-payload startup smoke, reinstall and rollback retention, in a temporary installation. [CI run 37235092353](https://github.com/funkyoushift/MattsSDKBoostingTools/actions/runs/37235092353) succeeded: release-policy passed and duplicate cloud rebuilding/publishing was intentionally skipped for reviewed local artifacts. No source/build discrepancy is hidden by this skip; local packaged checks and public download verification are recorded above.

The user's running game and installed SDK were not replaced during publication. At 17:13 Eastern, AFK was stopped by the operator and the existing third pilot still had approximately 12 minutes remaining; publication did not restart it. The permanent feature loads when the published SDK is installed and the game next starts. This documentation-only verification update does not change the release tag, artifacts or bundled version metadata.
