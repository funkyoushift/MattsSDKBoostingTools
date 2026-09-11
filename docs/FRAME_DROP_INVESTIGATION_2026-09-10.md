# Frame-drop investigation — September 10, 2026

The investigation starts from the published MSBT v2.11.1 source. These changes
are local fixes on `codex/frame-drop-investigation`; the public version remains
unchanged.

## Evidence and limits

- The installed SDK package matches the published v2.11.1 SHA-256:
  `e5ebe1fea306c6c7d51047d4971bfbfa5d4e2ee45b115102aedaeef378575842`.
- The SDK's only changes between v2.11.0 and v2.11.1 are version metadata.
  The editor update did not change these gameplay callbacks.
- Borderlands 4 was closed during this investigation, so no before/after game
  frame times have been measured. Offline reproductions establish code defects,
  not which defect caused the reported session's frame drop.
- The retained SDK log covers September 11, 01:31–01:41 UTC (September 10 local
  time). It contains no shared-camera activation or Infinite Jump sync spam.
  Third Person reports starting off, with no later activation logged. The saved
  Quick Menu layout has no slot hotkeys assigned.
- With the game closed, four installed Electron processes consumed a combined
  0.079 CPU seconds over a 15-second sample. This does not measure their cost
  while connected to a running game.

## Reproduced MSBT defects

### Camera dispatch

The shared camera pump ran every registered callback whenever any subscriber
needed it. With Infinite Jump enabled and Super Dash disabled, 100 accepted
ticks caused 100 unnecessary disabled-dash lifecycle syncs and 100 repeated
Infinite Jump log messages. This can occur up to the shared 120 Hz limit.

Dispatch now honors subscriptions. Quick Menu hotkeys, toast expiry, and pending
delivery completion retain explicit subscriptions. An invalidated Quick Menu
overlay releases its open-menu subscription. The third-person native-hook
fallback also previously requested the camera twice per PlayerTick callback;
it now requests it once.

### Periodic bridge status

Every half-second, the game-thread status snapshot performed LAN hostname and
socket discovery, even with LAN control disabled. A real cold lookup took
6.14 ms in an offline measurement on the affected PC. A controlled 20 ms
resolver delayed each successive snapshot by approximately 20–22 ms.

LAN discovery now runs in one background worker and status reads cached
addresses. The pairing overlay refreshes when addresses become available.
The periodic bridge snapshot also omits debug-camera object enumeration and
bookmark file reads whose results it discarded. Full backend status remains
available to existing callers. Failed snapshots respect the refresh interval
instead of retrying every game tick.

With an injected 20 ms resolver delay, the unchanged status function took
20.52–20.88 ms per call. Cached status took 0.001–0.008 ms while the resolver
worker remained deliberately blocked. These are isolated status-function
timings, not measurements of whole-frame time or FPS. The saved LAN setting on
this PC is enabled.

## Validation

All 49 SDK Python files pass syntax checks. All 59 focused behavioral tests pass,
covering
camera subscriptions, travel gating, toast/delivery expiry, third-person
fallback, cached bridge status, queue limits, LAN authentication, delayed DNS,
stale worker results, retry backoff, and pairing QR refresh. SDK imports are
tested with Unreal stubs; this does not replace live bridge validation.

The broader suite has five failures that also reproduce on the unchanged
v2.11.1 checkout: a missing ASD probe file, two existing startup-import
expectations, an action-audit expectation for guest-grid actions, and a Quick
Menu registry case. Two other ASD test modules cannot collect because their
probe helpers are absent from the released tree. Twelve dependency-dependent
tests are skipped in this clean investigation worktree.

The local test SDK package contains the same 63 entries as v2.11.1. CRC,
source-byte parity, and all 49 Python zip imports pass. Exactly seven source
files have changed content. Package SHA-256:
`e4855b27312ce6188c1bd3341039a676594c83dfd718c3a42d07627eed228902`.
It was installed while the game was closed. The original published package is
retained at
`tools/_tmp_frame_drop/MattsSDKBoostingTools-v2.11.1-original.sdkmod`
in this worktree; restore that verified package with the game closed to undo
the local test. No game process was stopped.

## Remaining live checks

Use the same character, map, view, graphics settings, and foreground window for
comparisons. Allow map streaming to settle and record frame times while idle,
then with the desktop panel connected. Test Infinite Jump alone, close/open the
Quick Menu, travel with it open, and verify toast expiry, slot hotkeys, delivery
completion, and phone pairing. Third-person fallback needs an in-game check
when native hooks are unavailable.

The separately installed MattsBL4ModsMenu also registers an unthrottled camera
callback. Running its actual callback and helper functions against a fake player
controller with the menu closed produced 5,000 `get_pc` calls, 4,000 `IsValid`
calls, 4,000 controller-name reads, and 2,000 cursor-state reads per 1,000 camera
callbacks. This measures call counts, not real Unreal execution time. Azzy's
separate camera callback already has a 20 Hz limit and a reentrancy guard.
The installed archive directory contains no Python initializers and is not a
second loaded copy of MSBT.

MattsBL4ModsMenu's cost is an additional candidate for a controlled comparison;
no other mod was disabled or modified during this investigation. Simply disabling
that mod through its menu may leave the camera callback registered, so a valid
comparison requires it to be excluded before a fresh game launch. Preserve the
original package and restore it after the comparison.

Do not attribute an FPS recovery to these fixes until a comparable live sample
has been collected. Large one-shot boost, discovery, inventory, or spawn actions
should be assessed separately from an ongoing idle frame-time regression.
