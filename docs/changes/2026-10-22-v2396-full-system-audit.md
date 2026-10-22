# v2.39.6 current-build full-system audit — 2026-10-22

## Scope and checkout

Read-only audit of `C:\Users\mwenn\.codex\worktrees\steam-26007962\product`, release v2.39.6 at publication-record commit `abad9ac`. No game or Epic launch, SDK install, save mutation, package rebuild, version change, or publication was performed. One test fixture was adjusted so its mocked Windows kernel follows the new exact-executable fallback in `direct_inventory.NativeInventory`; this changes no runtime code.

## Current executable gates

The installed Steam executable hash was re-read as `ba75f7c2874b16efb5536a5c0cc28918a03efd3e55d790d2e4db57de0c3a353a`; Epic was re-read as `6d531d91011ae0d67ac461a3cacabc99993c279bf325dfe70ff1af00ec43c87e`. Both matched the profiles already checked into the release source.

| Component | Current-build behavior | Audit result |
|---|---|---|
| Mission native profile | Exact executable digest selects a separate profile; unknown executable is rejected before native operations. | Steam 26007962 and Epic 6d531d91 profile tests pass offline. No Epic runtime proof. |
| Host direct inventory | Requires exact executable digest plus all native code/data gates before binding callbacks. | Both current profiles pass offline checks. Steam host delivery was previously live-tested and recorded in the release receipt; Epic and guest delivery remain unverified/gated. |
| Guest inventory and native item cards | Current guest transaction/card mappings are intentionally unsupported until current-build evidence is recovered. | Unsupported-build card fallback test passes; no current native card or guest claim. |
| Farming controls | Exact profiles exist for current Steam and Epic executables. Epic skill-charge enumeration is explicitly absent (`charges: None`); Steam retains its qualified profile. | Current profile tests pass offline; no Epic launch. |
| Full Game status | On Steam 26007962, status warns that mission, discovery, and challenge catalogs still come from 1.10. This is a coverage limit, not an executable gate. | No false rejection found. |
| Shared game parameters | `game_parameters.status_parameters()` reports the provenance of bundled limits as update 1.10 / extracted build 25234898. Those fields feed status/UI only and do not decide action acceptance. | Stale relative to the installed executable, but accurately describes the older data source; changing it to 1.11 without extracted 1.11 data would overstate coverage. |

## Checks

- `npm run check` from `electron_poc`: passed, including Electron syntax and app-level offline checks.
- `python -m pytest tools/tests/test_quick_menu_no_blimgui.py tools/tests/test_steam_26007962_direct_inventory.py -q`: 8 passed.
- With `PYTHONPATH=tools`, direct-delivery, Steam/Epic mission and farming profiles, current inventory gates, SDK ZIP packaging, and release-import tests: 36 passed, 3 skipped. The three skips need a live runtime and were left skipped.
- `npm run test:game-update`: passed for game-update parameter UI, data-catalog build handling, and current character challenge goals.
- `npm run test:mobile-remote`: passed.
- `npm run test:native-card-render`, `npm run test:native-equipment-cards`, and `npm run test:card-layout`: passed. Card rendering is offline preview evidence only; listed unresolved Shield/Ordnance stats and the “details still being validated” card notice remain.
- `npx --no-install electron test_item_card_unsupported_build.js`: passed; unsupported Steam/Epic card serials use the intended fallback.
- `npm run test:item-cards`: stopped at `test_serial_card_naming.js:39`, where three checked-in game-data hashes differ from `item_naming_provenance.json`. The data and manifest are unchanged from v2.39.5 and trace to the v2.11.4 import; this is a pre-existing provenance/test failure, not a current executable gate. The manifest was left intact because the original importer output was not recovered.
- `npm run test:mobile-parity`: its first two Node checks passed, then Electron could not write `output/reported-issues/mobile-parity-preview.png` because that output directory is absent. This is a test setup failure, not a game-version rejection.
- Broad Python suite, excluding only the two uncollectable ASD test files whose imported source modules are absent from this checkout: 1,554 passed, 18 failed, 7 skipped, 132 subtests passed. Failures are in the same legacy/environment/test-harness families noted by the v2.39.6 release record (AFK concurrency expectation, missing ASD files, test namespace/source assertions, unavailable `unicorn`, and old helper fixtures); no current Steam/Epic profile test failed. The prior recorded baseline was 1,498 passed, 23 skipped, 19 failed, with 17 failures reproduced on clean v2.39.5 and two Epic evidence tests tied to the replaced binary. Counts differ because this audit checkout has additional tests and the current profile fixtures; not every failure was independently rerun on v2.39.5.

## Private local report review

Today’s private AFK reports were summarized locally without copying serials, player names, or raw inventory data. There were 74 reports. The 15:06 report completed 11 actions with one failed loot step; the 16:00 and 16:28 reports completed 11 actions each with no failed steps. The 16:28 report is after the v2.39.6 tag time (16:15). Earlier reports included repeated Vault Card XP readback failures (target 9999, observed values 1–365) and UVHM firmware challenge completion not confirmed, so subsequent steps were correctly withheld. The 15:06 loot step was rejected by the direct-inventory unsupported-build gate; its report lacks executable identity, so the cause cannot be assigned to a bad profile versus a different game session. Since later same-day reports completed without failed steps, this is not evidence of a persistent current-build rejection.

One direct-delivery journal failed because the original player left. The service deliberately refused to retarget a replacement player, so this is the recorded safety behavior. The UI error text says “host readback” in the AFK Vault Card path even though the operation is scoped to its pinned player state; this wording may mislead and the observed under-target values remain unresolved. No entries were present in today’s local failure-report outbox.

## Remaining proof gaps and rollback

Offline tests establish profile selection and fail-closed behavior, not that every control works during gameplay. Complete 1.11 mission/catalog coverage, Epic live execution, current-build guest inventory/card parity, guest-save persistence, safehouse causality, and the AFK Vault Card/UVHM failures remain open. No package was built or installed in this audit. The only audit code edit is the isolated test fixture; reverting that one test hunk restores its prior state.
