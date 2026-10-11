# Grassroots Campaigner guest credit repair - 2026-10-11

## Symptom and evidence
Cryptic remained at 35/50 after bulk mission completion, including in his own saved game. Grassroots is a base-game challenge with 98 explicit mission definitions and tiers 10, 25, 50, 75, 98; it is not DLC. Shared mission completion did not ensure each player's once-only challenge flags were credited. Native reads matched host 98 and guest 35.

## Implementation
Added mission_challenges.py/json, integrated credit verification into mission_progression.py after completed mission readback, and added a Repair Grassroots mission credit scope in Electron. Repair selects only completed shared missions and credits missing individual flags for each currently bound player; it does not reset/replay missions or arbitrarily assign the counter. Already credited players are skipped. Added two source-defined hidden missions to mission_catalog.json so its coverage includes all 98 challenge entries. mission_runtime.py now respects sparse-map allocation flags, avoiding freed slots seen after guest rejoin.

Native evidence: installed executable SHA256 9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0. Reviewed challenge callback RVA 0xd17c02, mission branch 0xd17edc, per-mission check/set at 0xd181ee/0xd18200, popcount at 0xd1829b. Definition custom mission array +0x328; player challenge credit records +0x1300. Runtime validates build, callback fingerprint, definition ordering, player identity and count/bit agreement. No debugger, patch, raw credit write, or generic IncrementChallengeForPlayer used.

Native counter updates are queued: immediate post-call verification initially observed a new bit with an old counter. That diagnostic issued one call only; later readback confirmed 37. Product waits across ticks, journals before issuing, and requires exactly one new mission flag plus one counter increment. Timeout is uncertain and is not retried. Cancellation waits for an issued credit to verify; recovery reads the receipt and never repeats the callback. Same-session identity is required for recovery.

## Validation
- Pilot Mission_Side_Heist: guest 35 to 36, host unchanged at 98. Martin confirmed guest own-game count 36.
- Duplicate pilot mission skipped without a new native call.
- Product-helper pilot: guest 36 to 37, delayed update confirmed.
- Installed integrated repair job 0bc1d1229e224a868c15eca65df1f123 completed all 98 entries. Fresh native reads: Criptyc_Gamer 98, FunkYouShiFT 98. This repaired 61 further missing credits.
- Martin supplied Cryptic's message confirming challenge completion and achievement unlocked after requesting the final own-game check. Cryptic also reports group-specific side quests remaining; this does not prove every side quest completed.
- 60 offline Python tests passed (one existing fixture import deprecation warning); mission panel tests and JS syntax passed. Archive Python compilation and CRC passed.
- Cancellation/recovery additions are offline checked, not live fault-injection proven. Whole-game completion, other challenges, other executable builds and entitlement behavior are not established by this test.

## Installation and evidence
Local review SDK installed and hotloaded without restarting BL4; version unchanged at 2.36.0. Final archive SHA256 6592e302633fcfc20a81287cafdc9e66d37d04a61b36bd231bfe244ff1e2223a. Source and desktop changes synced selectively to the mission-release review worktree. No public release or remote assets changed. Rollback can restore the published SDK and desktop; earned guest credits are intentionally retained.
Evidence in ../local/mission-preflight-2026-10-10/central-completion, including 3c01739fc8094deeadc8464e0d0e80bf-response.json; pilot receipts under tools/mission_lab/receipts/three-player-fullrun-20261011. Extracted definition provenance is recorded in mission_challenges.json.

Desktop validation: 41 navigation routes, control homes and unique IDs passed with zero game actions. Restarted only the MSBT review desktop to load the new repair selector.
