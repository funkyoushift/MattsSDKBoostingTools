# AFK delivery count mismatch — 2026-10-04

## Issue and verified evidence

Matt reported an active AFK lobby showing Random Delivery Size 500 but delivering 70 after password acceptance. Desktop v2.27.0 runs from `%LOCALAPPDATA%/Programs/MSBT/app`. The Steam game was already running.

Read-only live `/status` confirmed `enabled=true`, `loot_mode=random70`, `random_count=70`, `bulk_loot_authorized=false`, 985 pool entries and no guaranteed entries. Recent successful guest results explicitly reported selections and direct delivery of 70/70. A bounded scan of the desktop's persisted localStorage found `random_count:500`. The existing installation unlock file contained schema 1 / unlocked true.

Installed SDK `afk_lobby.py`, `afk_loot.py`, `external_bridge.py` and installed desktop `afk_lobby.js`, `afk_config_upload.js`, `renderer.js` matched the v2.27.0 source checkout. Game startup postdated SDK installation. Work performed in `C:/Users/mwenn/.codex/worktrees/language-settings/working`, branch `codex/language-settings`, base `ef7f069`. The primary desktop checkout is older and heavily dirty; its unrelated source was not overwritten.

## Root cause and limits

Confirmed defect: desktop `render()` applied the SDK configuration only when `running && !loaded`. Once any AFK status had arrived, later running configurations did not update the fields. Thus a saved/editable 500 could remain displayed while the authoritative game configuration was 70. Android used the same first-status-only pattern. A regression test against the original desktop code reproduced exactly this misleading 500 display after an active SDK snapshot of 70; it failed with actual 500 / expected 70.

A second verified code issue: desktop count/amount inputs saved only on `change` (blur); the asynchronous IndexedDB load checked an edit counter that these inputs did not update while typing. A late load could overwrite an in-progress edit. All panel input events now save/update that guard.

The original start request was not retained, so why this particular session originally started at 70 remains unknown. Do not claim the stale display proves which controller or request selected 70. `bulk_loot_authorized=false` for a 70-item session does not prove the installation unlock was lost: `Lobby.start` sets this session flag only if the maximum new selection exceeds 70.

## Verified value and authorization path

1. Desktop `afk_lobby.js:selection` reads the numeric input as `random_count`; localStorage and IndexedDB retain the same property. Android `afk.js:selection` also sends it.
2. `afk_config_upload.js` forwards small payloads unchanged and serializes the whole payload for large transfers; `afk_config_upload.py:consume` verifies count/size/SHA-256 and decodes that object. Password retry spreads the original payload. Remote forwarding preserves the payload.
3. `external_bridge.py` passes the object to `backend_actions.afk_lobby_start`, then `Lobby.start`. `start` validates a positive integer (numeric string accepted), defaults to 70 only if absent, stores it, computes the maximum selected count and calls `Game.authorize_bulk_loot` above 70.
4. Authorization uses `install_authorization.authorized`: the persisted unlock is accepted without resubmitting a password. It does not alter the requested count. Failed authorization rejects start rather than silently truncating to 70.
5. `Game.loot_for_guest` passes the configured count into `afk_loot.select_loot`, caches one selection per guest, applies the existing class restrictions, guaranteed-item rules and available-pool limit.
6. `Game.step('loot')` enforces authorization and passes the full selection plus `bulk_authorized` to `serial_rewards._do_give_serial_to_player_indices`. The direct queue uses 8,192-character chunks, 0.008-second item gaps, 0.75-second chunk pauses and 3-second settlement. No 70-item total cap exists there. Completion waits for the queued sequence; in-flight polling does not resend it.

## Changes and behavior

- `electron_poc/afk_lobby.js`: every valid running SDK snapshot updates the locked controls; idle drafts remain editable. All input edits are saved before blur, protecting them from delayed loading.
- `mobile_controller/app/src/main/assets/afk.js`: active PC settings synchronize on subsequent snapshots, including starts from another controller. No automatic saving of remote snapshots over the phone's idle draft.
- `electron_poc/test_afk_delivery_count.js`: real renderer regression for stale state, repeated active updates, counts 1/35/70/71/500, password retry and secret-free persistence; supports testing a packaged ASAR.
- `electron_poc/test_afk_config_store.js`: verifies count 500 survives actual page reload alongside large lists.
- `electron_poc/test_mobile_afk.js`: adds active 70/500 synchronization checks.
- `tools/tests/test_afk_delivery_count.py`: 12 combinations of 1/35/70/71/85/500 and pools of 40/985; traverses production start, authorization, selection, AFK send boundary and actual paced delivery engine with native insertion stubbed; checks full drain, batching, no resend and no duplicate selection.
- `AGENTS.md`, `.cursor/rules/project-change-notes.mdc`, this entry and the change-note index establish notes-first context and durable evidence for future work. Rule/index/entry mirrored to the primary checkout, without copying unrelated application source.

Random selection still draws without replacement from eligible pool entries. Requesting 500 from fewer than 500 eligible entries does not manufacture duplicates. Guaranteed items retain their existing exception to the target count. No authorization gate, batch limit, pacing, class filter, identity check or game insertion code was removed.

## Validation and local installation

- Original UI regression: FAILED as expected (displayed 500 when active config was 70).
- Corrected UI regression: PASS against source and the rebuilt installed-package candidate, including password retry preserving 500.
- Existing desktop AFK UI, Android AFK UI, large-list transport, and IndexedDB/page-reload tests: PASS.
- `python -m pytest -q tools/tests/test_afk_delivery_count.py tools/tests/test_afk_lobby.py tools/tests/test_afk_loot_classes.py tools/tests/test_direct_delivery.py tools/tests/test_afk_config_upload.py tools/tests/test_quick_menu_no_blimgui.py`: **133 passed**, two pre-existing test import deprecation warnings.
- Python compilation, changed JavaScript syntax and `git diff --check`: PASS.
- Local desktop ASAR compared file-by-file: 2,199 files checked; only `afk_lobby.js` differed. Original SHA-256 `3c3ce1ed899a32142f41d3968e1ed5942da369f959b9a9975b0da196eab2ac39`; installed corrected SHA-256 `ff5614535ae0041babdfb83ab8d135421cab0d0ad5febbefe4a8e3413013e86c`. Version remains 2.27.0. Borderlands left running. Desktop restart remains unconfirmed/blocked as detailed below; installed package tests passed, but do not claim the existing renderer loaded the fix.
- At 15:52:47 America/New_York, waited for a guest-free boundary (one roster entry, no current/queued AFK job and no active delivery), preserved the old status, then stopped/restarted AFK with the same selections and `random_count=500`. SDK confirmed enabled / 500 / authorization true / 985 pool entries, without a password or forged authorization flag.

## Rollback and unresolved follow-ups

Task workspace: `C:/Users/mwenn/Documents/Codex/2026-10-04/referenced-chatgpt-conversation-this-is-an-2`.
Local original desktop package: `work/app-before-afk-count-fix.asar`; installation receipt: `work/afk-package-receipt.json`; old live snapshot: `work/afk-before-count-restore.json`; restored config receipt: `work/afk-restored-receipt.json`. To roll back, close only the installed desktop app, restore its original ASAR and restart it; leave Borderlands running. An app reinstall/update can replace the local fix until these source changes ship.

Android source is corrected and UI-tested, but no new APK was built/installed. No SDK edit/build/install was needed. No version bump, commit, tag or public release was made. Guest save persistence is not proved by submitted insertion counts. Live completion evidence, if obtained, is appended below.

The initial desktop restart command matched no processes because its forward-slash string did not equal the native backslash executable path; launching again merely focused the single existing instance. Readback caught the unchanged process creation time. A corrected, exact-path stop/relaunch was blocked by automatic approval review with only `blocked by policy` supplied. No attempt was made to bypass that block. The installed UI fix needs a normal desktop quit/relaunch; the active game count correction is already effective. The app's ordinary close can hide it to the remote-AFK tray, so closing the window alone is not proof of a restart.

`AGENTS.md` and `.cursor/` are intentionally ignored by this repository. The local notes-first rules exist in both worktrees; the durable documentation/index and regression tests are visible source additions. No unrelated ignore policy or Git staging was changed.

## Live delivery result

After restoring the active count, the live engine selected 500. One guest left after 283/500 submitted additions; the identity guard stopped rather than targeting a replacement. A subsequent guest completed **500/500 submitted item additions**, observed in live `/status` with `total_serials=500` and `active=false`. This proves the configured 500 reaches and completes the real insertion loop, including the existing pacing. It does not independently verify the guest's saved inventory. The lobby remains enabled at 500 with authorization true.

Matt subsequently confirmed: "the app is currently sending 500 instead of 70 so it is working."

## Follow-up: overlapping ready guests (investigated, not implemented)

This section records the initial investigation. The subsequent opt-in implementation and bounded experiment are documented in [Concurrent AFK pacing pilot](2026-10-04-afk-concurrent-pacing.md); live overlap remains unproven and the pilot restored the original runtime.

Matt asked whether direct-to-backpack allows a new ready target to begin without waiting for the previous joiner's entire AFK run. Source inspection supports feasibility, but the current scheduling still serializes runs:

- `Lobby.tick` owns one `self.current` job; ready guests are selected only when it is empty. `Game.roster` requires loaded progression containers and the same controller/pawn stable for 20 seconds. Keep this readiness protection until separate live evidence supports reducing it.
- `Game.step('loot')` waits on the global delivery-busy flag. `serial_rewards._queue_direct_delivery` rejects a new list whenever another sequence/patch job exists. Simply adding more AFK current jobs will not permit overlapping loot deliveries.
- `direct_delivery.Delivery` already round-robins multiple targets within ONE request, at most one insertion per callback. However, those targets share the same serial list and are fixed at construction. AFK guests need independent, class-filtered random selections and join-time admission. Reusing one shared list would change existing AFK semantics.
- Safe design direction: per-guest AFK state, fair cooperative advancement on the game thread, independently selected loot jobs sharing one global insertion/pacing budget, and per-guest identity/cancel/completion reports. A slow/leaving guest must not block or redirect another guest's work. Do not bypass throttles or create uncontrolled parallel Unreal calls.
- Challenges use a global `_challenge_queue`; challenges/UVHM also have shared-run bookkeeping. Inventory cleanup/recovery uses singleton/background ownership and may clear/restore inventories. Preserve explicit resource coordination for these operations rather than overlapping them indiscriminately.
- Keep shared-connection/split-screen kick barriers and final settlement. Add multi-guest join/loading/leave/rejoin, class-selection, simultaneous manual-delivery, cleanup and cancellation tests before enabling concurrency, then validate with actual guests. No concurrent AFK implementation or live concurrency test was performed in this change.

Rejected approaches: removing password checks or raising batching limits would not address an active config of 70; inventing an item cap/root cause was rejected. Did not replace the dirty primary checkout, rewrite game insertion, fill small pools with repeats, or restart AFK while a guest was processing.
