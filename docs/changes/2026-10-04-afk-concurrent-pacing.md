# Concurrent AFK pacing pilot — 2026-10-04

## Latest validation outcome

The third test demonstrated two overlapping live guest deliveries, both completing 500/500 host-submitted additions. Matt reported "both players report proper item counts" and then clarified "they did persist. they reported from their games." Two-guest concurrent delivery, correct counts and persistence are therefore guest-confirmed via Matt. Three simultaneous guests and broader reliability are not live-validated. Earlier inconclusive results and lifecycle failures below are retained as history. Matt subsequently explicitly authorized preparing and publishing the release; see the v2.28.0 release entry.

## Request and starting evidence

After confirming 500-item delivery works, Matt proposed that catch-up delays should apply separately to each receiving guest, allowing ready guests to start without waiting for the previous guest. He authorized testing with current live join traffic. This is a local experiment, not release authorization.

Read first: `PROJECT_CHANGE_NOTES.md`, `2026-10-04-afk-delivery-count.md`, and `DIRECT_INVENTORY_DELIVERY.md`. Source work remains in `C:/Users/mwenn/.codex/worktrees/language-settings/working` (base ef7f069), matching the installed v2.27.0 SDK before this experiment. Do not overwrite the older, heavily dirty primary checkout.

The delivery implementation uses fixed timers, **not guest-state acknowledgements**. `direct_delivery.py` applies an 8 ms item gap within each Delivery object, a 0.75 s chunk pause per target and 3 s final settlement per target. AFK nevertheless owned only one current guest, and `_queue_direct_delivery` rejected every second request. Thus independent guest waits could not overlap across AFK-selected lists.

Historical two-guest direct-inventory results in `DIRECT_INVENTORY_DELIVERY.md` support the method, not the new scheduler. Earlier burst tests lost saved items despite complete host readback. Do not equate submitted counts with saved inventory or remove pacing based on host-only results.

## Candidate behavior

- `afk_lobby.py`: opt-in `concurrent_guests` configuration. Advance up to three different ready guests per AFK tick on the game thread. Existing 20-second stable-character/progression readiness remains. Each job retains independent steps, class-filtered random selection, results and exact player identity.
- Started jobs can wait in the queue; stop, world change, departure and 120-second unavailability cancel/report these jobs rather than silently discarding them. Shared challenges/UVHM retain a single owner; unrelated personal steps can advance. Existing split-screen/unknown-connection kick barriers and final settlement remain.
- Pilot admission rejects cleanup and host-test mode. No inventory clearing/restoration is enabled or overlapped by this experiment.
- `serial_rewards.py`: allow up to three explicitly marked AFK direct requests, each with exactly one different target. A manual/legacy send remains exclusive; duplicate targets, fourth concurrent requests and mixing manual sends are rejected. Each Delivery retains its own unchanged timers. Existing sequence processing advances each admitted request once per callback, so a guest's pause does not impose that delay on another guest. Calls remain serial on the game thread, with at most three native insertions per callback for this pilot; no background Unreal calls.
- Per-guest completion messages come from that guest's Delivery, avoiding global status from another guest. Read-only aggregate progress and `active_guests` expose the concurrent work.

## Files and checks

Production candidates: `mod_extracted/MattsSDKBoostingTools/afk_lobby.py`, `serial_rewards.py`. No native insertion or timer constants changed.

Tests: `tools/tests/test_afk_concurrent.py`, `test_afk_concurrent_pilot.py`; the existing `test_afk_delivery_count.py` journal stub now supplies a path required by the real per-delivery progress method. An initial combined run caught the incomplete test stub (12 cases); corrected the stub without weakening production reporting or the assertions.

179 focused Python tests pass: concurrent scheduling/pacing, loader/expiry/rollback, existing AFK behavior, 1/35/70/71/85/500 counts, short pools, class rules, direct insertion, cleanup recovery and Quick Menu no-BLImGui regression. Syntax compilation and diff checks pass. The three-target simulation delivers three independent 500-entry lists with identical per-target timestamp sequences, retaining item gaps, chunk pauses, final settlement and exact no-repeat ordering. An additional integrated test drives three jobs through actual AFK selection, production queuing, Delivery and kick settlement; all three independently submit 500. A failed/departed target does not cancel or retarget another. These are offline results with native insertion stubbed. Five test-loader package/spec deprecation warnings remain.

## Live pilot lifecycle

`tools/afk_concurrent_pilot.py` checks the installed SDK source hashes and requires the existing enabled, host-mode, authorized 500 configuration with cleanup disabled. It compiles only the two class definitions and four reward functions into the loaded module namespaces, preserving the existing lobby/game objects, current job, queues and completed/history state. Existing unmarked in-flight delivery finishes before concurrent requests can be admitted. No AFK stop/start, reboost, game restart or on-disk SDK replacement occurs.

`tools/afk_concurrent_live.py` invokes the loader through the SDK console. The 600-second pilot loaded successfully at **16:11:29 America/New_York**. SHiFT was briefly closed to access the console, then reopened; status confirmed connected and auto-accept running. The running game remained available.

After expiry, the pilot disables new concurrent admissions, drains started jobs and deliveries, then restores the original class/function references. `work/afk-concurrent-pilot/STOP` requests the same graceful rollback early. The expiry and STOP paths are offline-tested. Do not blindly rerun if a pilot or STOP marker exists.

`tools/monitor_afk_concurrent.py` samples `/status` every two seconds for a bounded interval. It saves counts, stage, report IDs and hashed guest labels to `work/afk-concurrent-pilot/samples.jsonl`; it does not mutate inventory or save plaintext guest names. Runtime source hashes and lifecycle state are in `pilot-runtime.json`. No source changes were made after those hashes were loaded.

## Current limits

Guest-side saved totals/lag feedback have been requested but are not available. Do not claim validated multiplayer reliability from host submissions alone. No new desktop/Android build, SDK installation, version bump, public release or default-on concurrency change has been made.

## Final live result and rollback

### Later operator display follow-up

Matt supplied a screenshot of arranging guest testers after 16:26 and reported seeing one-at-a-time delivery. A fresh bridge read confirmed `concurrent_guests: false`, no pilot and one current loot job. The pilot had ended at 16:21:30, before this recruitment; this was real sequential operation, not evidence that the candidate scheduler serialized guests. The screenshot's reported 972 items is uncorrelated to a particular run/starting inventory and is not proof of the new scheduler's saved counts.

`electron_poc/afk_lobby.js` now renders an explicit stopped/sequential/concurrent mode plus separate named progress rows from SDK `active_guests`, retaining distinct submitted/total values, settlement/error wording and the guest-save limitation. Started jobs parked in the queue are excluded from the waiting display. Old SDKs show the current guest/stage without inventing per-guest counts; stopped/disconnected state clears stale rows. Names use textContent. No runtime scheduler configuration changes were made for this display follow-up.

`electron_poc/test_afk_guest_progress.js` passed against the actual hidden Electron renderer with three unequal counts (120/500, 430/500, 500/500), settlement, queue deduplication, markup-like guest names, legacy sequential fallback and stopped-state clearing. Existing count/authentication UI regression also passed. Syntax and diff checks passed. This display change is source-only in the release worktree; it has not replaced the installed desktop UI. A prior automatic approval review rejected restarting the installed Electron app; this follow-up did not bypass that restriction. The running application therefore still has the old display, and concurrency remains disabled until another explicit bounded test is activated.

The 600-second pilot expired and restored the original class/function references at approximately **16:21:30 America/New_York**. `pilot-runtime.json` records phase `restored` and `restored: true`. Final read-only bridge verification confirmed AFK enabled, random_count 500, bulk authorization true, concurrency disabled, pilot status absent, and SHiFT connected with auto-accept running. Current traffic continues under the original scheduler.

The monitor collected 266 samples with zero status failures. Maximum simultaneously active guest jobs and item deliveries was **one**. Native-call journal intervals also show no overlaps. Three pilot deliveries submitted 411, 318 and 462 of their requested 500 items before cancellation; AFK history records guest departures. No duplicate item-index attempts were recorded. There was no completed 500-item pilot delivery and no guest-save proof. Cancellation/departure also occurred in pre-pilot traffic; the test does not establish a cause for departures or a performance improvement/regression.

Matt chose to let current traffic continue rather than arranging two guests. The bounded pilot was allowed to expire normally; no unattended concurrency remained enabled. Live overlap remains **inconclusive**, not passed. A future bounded test needs two ready guests remaining through delivery and guest-side saved-count/lag feedback. Do not enable concurrency by default or remove pacing based on these results.

Reproduce the offline check with `python -m pytest -q --tb=short tools/tests/test_afk_concurrent_pilot.py tools/tests/test_afk_concurrent.py tools/tests/test_afk_lobby.py tools/tests/test_afk_delivery_count.py tools/tests/test_direct_delivery.py tools/tests/test_afk_loot_classes.py tools/tests/test_afk_inventory_recovery.py tools/tests/test_quick_menu_no_blimgui.py` (179 passed). The read-only analyzer `tools/analyze_afk_concurrent.py` writes `work/afk-concurrent-pilot/analysis.json`, bounded by the recorded pilot start and final monitor timestamp so later traffic is not counted as pilot evidence. These receipts contain hashed guest labels, not credentials or inventories.

## Second live test activated after explicit restart request

Matt explicitly requested restarting everything to test. On 2026-10-04 at 16:39 Eastern, restarted the exact installed MSBT executable and installed the per-guest UI archive. Verified all 2,199 packaged files: only afk_lobby.js differs, version remains 2.27.0. Installed archive SHA256: e77c000c44ad518977367b00e8122160b6102f54def85842afba465fa0ecd562. Backup: work/afk-concurrent-pilot-second/app-before-progress.asar. Fresh process creation times confirmed restart; the earlier approval restriction did not recur after explicit authorization. Actual visible installed AFK page confirms Concurrent AFK and countdown. UI count/auth regression passed against the installed archive; guest-row rendering regression and pilot lifecycle tests passed.

Because guests were active, reloaded AFK runtime components via the SDK console rather than terminating Borderlands. The game process/world and existing lobby state were preserved. tools/afk_concurrent_live_second.py activated the same tested scheduler at 16:39:51.758 Eastern (20:39:51.758Z), for 1,800 seconds: new admissions end approximately 17:09:52 Eastern, followed by graceful drain and original-runtime restoration. This is an active experiment, not permanent/default-on installation. Fresh status confirms enabled, concurrent true, 500, SHiFT auto-accept running. Guest rows appear when ready jobs start; an empty guest list is not concurrent delivery proof. The global serial banner can retain the last cancelled delivery; use the new AFK rows to identify active guests.

Second-run receipts are isolated in work/afk-concurrent-pilot-second, preserving the original pilot. tools/monitor_afk_concurrent_second.py records read-only samples for this run (bounded to 35 minutes), with hashed guest labels and STOP on repeated bridge failures. work/afk-concurrent-pilot-second/STOP requests graceful early restoration. Initial monitor history is preexisting and must not be counted as second-run completions. At handoff, the pilot was running with no active guest jobs; live overlap/save validation remains pending. No game executable restart, public release, or version bump occurred.

### Second test ended early when AFK stopped

At 16:52:24 Eastern, Matt reported the UI reading Sequential AFK. Fresh bridge state confirmed enabled at 500, no concurrency flag/pilot/active_guests, one current guest and another queued. The second pilot receipt says restored after 580.14 seconds, well before the 1,800-second deadline. Monitor samples show concurrent mode active at 16:49:31, then AFK disabled and the pilot absent at 16:49:33. No STOP file exists. The pilot tick intentionally treats disabled AFK as a rollback trigger; a later normal AFK start therefore uses the installed sequential SDK. The initiator of the stop is not proven by these receipts. This is actual sequential operation, not a misleading UI or timeout. The current panel Start does not enable a new pilot. Do not promise the test stays concurrent across Stop/Start; that lifecycle needs explicit implementation or reactivation after stopping. No runtime settings were changed during this diagnosis.

## Third test: Stop/Start persistence fixed, live overlap observed

Matt confirmed he had stopped AFK and explicitly requested a properly configured restart with two guests already present. Changed tools/afk_concurrent_pilot.py: admission may use the validated stopped configuration; ordinary AFK Stop halts delivery but keeps the experiment loaded until its deadline. Wrapped Start injects concurrent_guests only while the experiment is active and before expiry/STOP marker; existing password, cleanup and host-test checks remain. Expiry/dedicated STOP still drain and restore. The deadline does not reset on ordinary Start. The initial extended lifecycle test needed its synthetic STOP time advanced past the existing one-second control polling interval; no production timer was weakened. Fourteen lifecycle and concurrency checks passed, plus syntax and diff checks.

Loaded tools/afk_concurrent_live_third.py into the running game at approximately 16:55:23 Eastern on 2026-10-04, then restarted the user's stopped AFK with its existing selections and serial pool, using normal persisted password authorization. SHiFT reopened; AFK enabled at 500 and concurrent true. Third-run deadline is approximately 17:25:23 Eastern, followed by graceful drain. No game or desktop restart was required. Runtime receipts and hashed monitoring samples are isolated in work/afk-concurrent-pilot-third; monitor tools/monitor_afk_concurrent_third.py remains bounded and a STOP marker in that directory requests rollback.

At roughly 16:56:07 Eastern, the live monitor observed TWO simultaneous native direct deliveries: report 413434b78e524efa8c5e2b5129428df7 at 473/500 and report 3ce342787bd9487298c250bf3d95a5da at 126/500, both active and without reported errors. This establishes real overlapping send loops. It does not yet establish both final saved guest inventories. Per-player progress in the installed UI reads this same active_guests data. Guest-save proof remains separate and pending.

Subsequent live bridge history confirmed BOTH third-run guests completed 500/500 submitted additions with loot ok=true, while the pilot remained enabled (1,728 seconds remaining). This is host-side completion after observed overlap; guest saved inventories remain unverified.
