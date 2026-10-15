# Epic mission compatibility, Shinies authorization and UVHM verification

Martin requested the Epic gaps be repaired together with the password and PS5
UVHM feedback in the shared conversation. Primary source is
`C:/src/MSBT-Workspace/product`, HEAD `b0d3120`, with its existing dirty work
preserved. No version bump, release, installation or game restart.

## Evidence and changes

- Downloaded public v2.38.1 SDK SHA256
  `e8df76887625a928df95a4d605c147b6bab58f2d80f88c1e51e02c0074d3f402`
  and primary source accepted only Steam's executable in `MissionRuntime`.
  Raw mission addresses also appeared in completion, reset/replay, objectives,
  discovery, challenge credit, DLC access and SDU readback. A hash-only guard
  removal would have left Steam calls and ownership checks on Epic.
- `tools/qualify_mission_builds.py` performs read-only comparisons of the known
  Steam 25372571 and Epic 4845623 executables. It checks input SHA256, complete
  function instruction layouts, internal branches, RIP correspondence, caller
  identity and recovered vtable slots. Only relative branch/RIP displacements
  are normalized. Generic 18-candidate DLC resolver and two-candidate discovery
  function are resolved from independent callers; no first-match fallback.
  `docs/native-missions/EPIC_PROFILE.json` records 41 address mappings, 27 complete
  function spans and exact fingerprints with no missing mappings/conflicts.
  This includes five newer checkpoint routines used by the other repair branch.
- `mission_native.py` and `mission_build_profiles.json` select a single exact
  executable profile. `native_address(engine, source_rva)` resolves code/data;
  `native_fingerprint(engine, source_rva, source_expected)` translates an existing
  gate only when source evidence matches. Missing profiles/addresses, unknown
  executables and mismatched evidence fail closed. The 168-byte SDU gate is
  preserved. `MissionRuntime.check_build` checks every profile code gate and
  snapshot reports the selected profile. No runtime pattern scanning.
- Routed `mission_runtime`, `mission_progression`, `mission_objectives`,
  `mission_reset`, `mission_execution`, `mission_discovery`, `mission_challenges`,
  `progress_access` and `sdu_progress` through that resolver. Earlier card,
  inventory and farming Epic handling is preserved.
- Both `backend_actions` shared Shinies dispatch and `external_bridge` fallback
  now pass the submitted bulk credential into `deliver_shinies`. That handler
  validates installation authorization before conversion and passes only an
  authorization flag onward. The resolved-count guard still applies. Unlock
  receipts retain no credential; command/history payloads do not retain it.
- Ported only the existing repair branch's eight UVHM queue safety functions:
  world-scoped host discovery, no partial-tail late joins, retained pause work,
  original-player-only resume and explicit uncertainty on failed/disappeared
  targets. Travel drops old wrappers and stops the queue.
- `uvhm_progression.advance` pins the controller/path/player-state identity,
  skips already native-complete challenges, issues each incomplete challenge
  once, and waits for `IsChallengeCompleteForPlayer` before a later step.
  Verification polling retains the existing paced cadence instead of polling and
  logging on every UMG frame. The
  existing 25-challenge plan and pacing remain. Thirty-second verification is
  an operational stop bound, not a recovered game timing rule. Unconfirmed
  completion/uncertain RPCs stop without automatic retry. Manual/full-progress
  and private per-guest AFK runs use the same helper. Native completion and
  saved-rank proof are reported separately; no guessed unlock fields/bit arrays
  are written.
- Primary AFK bookkeeping incorrectly treated the private UVHM sequence as a
  shared success and could skip later ready guests. Only genuinely shared
  challenge runs now share credit; every guest receives and verifies their own
  complete UVHM plan. The newer repair branch already had this correction. A
  real Game/Lobby/per-player-verifier regression covers both guests and confirms
  no shared UVHM credit is recorded.

## Verification

- Primary: 429 mission/native-profile/replay/full-progress/SDU checks passed;
  110 password/authorization/AFK/UVHM checks passed; five no-BLImGui startup and
  bridge regression checks passed in a separate process. Python syntax passed.
- Actual installed Steam/Epic files independently match all recorded SHA256,
  complete function-body hashes and profile fingerprints. Tests execute the
  actual Epic runtime constructor against bounded fake memory and reject a
  damaged code gate before further probing. Mission execution tests run both
  profiles and assert the selected native call addresses.
- Password tests exercise all six shared action aliases and both HTTP routing
  paths with real isolated authorization and delivery guards, including missing,
  invalid and correct credentials, persisted unlock and resolved-count refusal.
  No game operations occur.
- Existing desktop SDK targeting, Epic installer discovery, persistent updater,
  editor account preferences and encrypted-save import checks passed. The
  case-specific account test covers lowercase/uppercase/mixed-case Epic IDs,
  exact folder/preference preservation, encryption/decryption and refusal when
  key-affecting case changes. These are synthetic saves, not customer saves.
- Scoped newer-repair-worktree checks: 132 native-profile/checkpoint/save-replay/
  password/UVHM/AFK checks passed. Its existing 15 desktop save-transaction checks
  and Steam/Epic encrypted-import tests passed; this is offline proof only.
- Initial failures were isolated fixtures without a package/resource loader or
  explicit build profile, and one SDU gate was incorrectly truncated to 32 bytes
  during initial profile generation. Those were corrected without weakening
  production profile selection. Tests now retain the original full SDU gate.

## Candidate, coordination and limits

Primary local SDK:
`C:/src/MSBT-Workspace/local/epic-repair-2026-10-14/MSBT-Epic-Password-UVHM-v2.38.1-local.sdkmod`,
SHA256 `0d74273abd42450da9d0df3e9a516b9aa0f87b7aff9c284988c947969e72b030`.
All 105 Python members compile; all 138 archive members exactly match staged
source/resources and ZIP integrity passes. This is the primary-source repair
candidate, not the other chat's combined replay/dialogue release candidate.

Before coordination arrived, scoped changes were also mirrored into
`C:/Users/mwenn/.codex/worktrees/mission-replay-release/product`, HEAD `9a400d2`.
Later save-backed replay/bookmark source was preserved, including two vtable
reads routed in `mission_save_replay.py`. The owner of that chat now owns all
further writes to save-replay/dialogue files, packaging, installation/restarts and
release preparation; this chat owns the native profile/password/UVHM changes.
No newer replay source was bulk-merged back into primary.

Rollback copies and exact hashes are under
`C:/src/MSBT-Workspace/local/epic-repair-2026-10-14/before` and
`repair-worktree-before`. Restore only these scoped changes after checking for
later edits; never replace another chat's newer files blindly. No runtime rollback
is required because the installed SDK was not changed. BL4 remained running.

Epic live mission execution, actual PS5 saved UVHM unlock after save/quit/rejoin,
and customer attribution to the specific Shinies handler remain unverified.
Native challenge readback removes the false-success/unchecked-pacing defects;
it does not establish the reported PS5 persistence root cause or prove its repair.
Do not claim universal mission playability, native card parity, saved guest rank
or a released fix from these checks. The other chat is separately handling
automatic character loading and dialogue/scripted waits.
