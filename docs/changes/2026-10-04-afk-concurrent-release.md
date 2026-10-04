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
