# AFK flow reliability candidate

Developed from v2.17.5 and included in v2.17.6 after user confirmation of the installed candidate. Automated checks are not guest-save proof.

## Intended sequence

1. Observe each guest identity; wait for a stable character and loaded progression.
2. If cleanup is selected, save originals before shared challenge rewards begin.
3. Apply selected boosts. Credit challenges and UVHM separately only for ready
   guests present throughout the successful shared run. Rejoins get fresh work.
4. Open the intended guest's reward packages, then perform cleanup if safe.
   Failure before deletion skips cleanup and continues selected loot without
   repeating completed boosts. An uncertain clear never triggers this fallback.
5. Deliver the per-guest selection, return originals and compare stable readback.
   Retry clear deficits only. Missing plus unexpected serials remain ambiguous;
   retain evidence instead of sending duplicate copies.
6. Save a per-guest report. Continue the queue on failure. All ended runs qualify for auto-kick, including failed boosts, unresolved inventory
   checks and report-write failures, after settlement and the connection-group barrier.
   Failed kick calls get at most three attempts, five seconds apart. Changed level/spec readback does not block auto-kick.

## Changes and checks

- Cleanup failures before deletion no longer omit selected loot.
- AFK package opening checks the intended guest manager, not any live manager.
- A failed boost no longer hands the lobby-owned recovery to a background runner.
- A current guest unready for 120 seconds gets a saved failure and releases the queue.
- Missing class identification on normal loot delivery expires after 30 seconds.
- Delivery exceptions, departure and unknown stages carry explicit failure state.
- Completion, interrupted runs and kick attempts write durable reports under
  `%LOCALAPPDATA%/MattsSDKBoostingTools/afk-run-reports`.
- Recovery originals remain under `inventory-recovery`; reports link the backup.
- Desktop history shows the report path and distinguishes skipped cleanup from failure.
- Status messages describe the current operation rather than internal step names.

158 AFK tests passed in separate file runs. Separate startup/no-BLImGui checks,
serial backpack-size checks, syntax checks, packaged module comparisons and the
Electron AFK UI check passed. Candidate receipt is under output/afk-flow-reliability.

## Live acceptance

- One tester: selected level/spec/SDUs/currencies, challenges and UVHM, cosmetics,
  guaranteed loot plus random fill, originals returned, then kick. Check inventory
  again in the guest's own game. Do not equate host readback with saved progress.
- Two ready guests: both backed up before shared rewards; second skips only completed
  shared categories and still receives individual boosts, own loot and originals.
- Split-screen: neither member is kicked while the other is receiving/returning items.
- Unreadable/pre-clear failure: no deletion, selected boosts/loot continue, report retained.
- Disconnect or stopped run: original backup and unfinished-step report remain;
  replacement guests cannot become targets of the old operation.

Exact native serial equivalence remains unresolved. Do not normalize away part order,
duplicates or unknown fields merely to make verification pass. FPS was not measured.
