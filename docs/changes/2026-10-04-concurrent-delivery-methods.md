# Concurrent manual and AFK delivery methods — 2026-10-04

## Request and baseline

Matt requested extending the successful AFK overlap to all ways of sending loot to other players without ending an earlier delivery. His two AFK testers already confirmed correct 500-item counts and persistence from their own games. That is evidence for the previous AFK path; it does not prove every new mixed manual/AFK combination live.

Source branch: `codex/concurrent-delivery-methods`, based on `63b5237`, in `C:/Users/mwenn/.codex/worktrees/afk-concurrent-release/working`. The original dirty main checkout and prior development checkout are preserved. Public v2.28.0 is unchanged.

## Root cause and route map

`serial_rewards._queue_direct_delivery` only admitted overlapping requests marked `afk_concurrent`, all targeting one guest. A normal manual request rejected any existing sequence. The underlying tick processor already advanced each independent Delivery; there was no need to replace jobs, remove chunk waits, introduce threads or restore reward-package delivery.

- Desktop, phone and native Quick Menu serial actions route through backend actions / `give_serials` / `_finish_give_serials` / `_deliver_serials_with_target` and the common serial queue. Selected, local, all-party and non-host targeting now use the same admission rules. Saved-list/editor sends using these actions inherit the behavior.
- Shiny serial sends use `_deliver_serials_with_target`; manual backpack undo uses it too.
- `_do_give_serial`, `_do_give_serial_chunk` and compatibility `_queue_serial_delivery_sequence` reach the same direct queue. The legacy `delivery_method='rewards'` keyword still routes directly to backpacks, as before.
- AFK loot uses the common queue and retains its own sequence reference for completion and cancellation.
- Inventory recovery/retry and sequential AFK explicitly request an exclusive sequence. Destructive inventory recovery is not ordinary loot delivery.
- Item-pool ground spawning, shiny ground spawning and physical inventory drops are separate world operations, not serial backpack deliveries. They do not use this global serial admission gate; their world-spawn pacing/queues are unchanged. No inference is made that the guest backpack test validates concurrent world mutation.

Two additional concurrency hazards were found: asynchronous conversion selected players at completion rather than request time, and manual undo obtained its report from global progress. Both are fixed by retaining original target identities and returning each request's own report path.

## Behavior and files

- `serial_rewards.py`: admit independent direct jobs regardless of manual/AFK source. Reserve at most four total target slots (host plus three guests), disallow duplicate target identities, and reject a request atomically if any selected target already has an active/reserved delivery. Existing jobs are never replaced or cancelled by a new request. A conflicting all-party request sends nothing; select free players or wait. Same-player backlog/replay is deliberately not introduced.
- Per-request Delivery engine timing is unchanged: 8192-character batches, 0.008-second insertion gap, 0.75-second chunk pauses and 3-second settlement. Multi-target requests retain their existing round-robin insertion behavior; independent requests advance on the same game thread, bounded to at most four insertions per callback. Password authorization, original serials/duplicates/order, controller/world identity checks and no retry of uncertain mutations remain.
- `backend_actions.py`: pin original world/controller/player-state/pawn identities before asynchronous conversion; re-resolve current indices when it finishes, failing without queuing if an original target has changed. Forward explicit request receipts so undo retains its own report.
- `afk_lobby.py`: AFK waits for a manual delivery to its own guest while free guests can advance. Sequential mode marks its delivery exclusive. Auto-kick defers while a manual delivery is reserved for that guest or a shared connection; unknown connection grouping uses a lobby-wide barrier. Deferred kicks do not consume retry attempts, and recheck after a further 15-second wait.
- `afk_inventory_native_recovery.py`: recovery and repair sends explicitly remain exclusive in both admission directions.
- `electron_poc/renderer.js`, `poll_coordinator.js`: general delivery progress renders one safe text/progress row per target, including settlement and individual errors. Poll fingerprints include player progress and stages. Direct delivery uses batch terminology. Aggregate status includes every active direct job; a single job keeps its existing progress shape.
- Tests: new `test_concurrent_delivery_methods.py` and real Electron `test_concurrent_delivery_progress.js`; adjusted AFK admission/count/kick fixtures and undo receipt coverage. Added `npm run test:concurrent-delivery`.

## Validation

The initial focused run passed 240 Python checks (five existing test-loader package warnings). Tests cover exact manual/AFK counts 1/35/70/71/85/500, legacy reward keyword, independently selected 500-item AFK lists, all target modes, atomic overlapping-party rejection, authorization, target changes/departures, recovery exclusivity, original targets after conversion and slot reorder, request-specific reports and kick protection. Python compilation and whitespace checks passed. Actual hidden Electron windows passed general per-player progress and AFK progress tests, including hostile player names, settlement, individual failure and clearing stale rows. Poll coordinator tests passed.

The combined all-AFK and related regression run passed **302 checks**, with the same five test-loader warnings. Final review extended target pinning to console `Give_Serial` background conversion as well. After that change, **47 focused checks** passed (including the new console test), full SDK syntax compilation passed, and `npm --prefix electron_poc run test:concurrent-delivery` passed both actual renderer tests and poll coordinator checks. Counts overlap and must not be added together.

Initial wider testing exposed three stale password test harness failures: absent installation-authorization stubs and a test still expecting the removed reward-package queue. Updated these tests to model the current auth adapter and exercise the actual direct queue. No production password policy changed. Unchanged direct-engine pacing and recovery protections were preferred over removing global checks indiscriminately.

## Deployment, rollback and unresolved work

Local source only; no version bump, public assets, SDK install, game restart, live inventory mutation or running desktop replacement in this turn. A new release was not requested in this message. Use this branch for the next test/build; do not mistake the currently installed/released v2.28.0 for these additional changes. Rollback is the parent source state; no queued items are replayed as part of rollback.

Remaining evidence: live overlap of manual plus AFK, two manual sources, a multi-target request alongside an independent target, and host-plus-three guests. New behavior has offline/renderer evidence, not additional guest-save proof. Phone/native menus inherit backend behavior when this SDK is installed; this change adds per-target rows to desktop only and does not ship a new Android build.
