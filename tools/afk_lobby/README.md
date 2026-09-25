# AFK Lobby local test

Source: isolated `codex/afk-boost-lobby` branch based on the installed 2.13.1 source.
No version bump or public release. The build preserves all other installed SDK
members and all other entries in the supplied SHiFT PAK.

## Test flow

1. Exit Borderlands 4. Run `install_test.ps1` in this folder. It verifies the
   source/test hashes before installing and refuses to overwrite an unknown build.
2. Launch the game, host a joinable lobby, and open the SHiFT menu.
3. In the test Electron panel, choose **Boosting > AFK Lobby**.
4. Select boosts, optionally add bookmarks or paste item codes, then Start.
   Check that the SHiFT status reports connected and auto-accepter running.
5. Optionally select **Auto-kick when finished** before Start. It defaults off and only requests a kick after every selected queue completes successfully. Errors keep the guest in the lobby.
6. Join with a guest. Watch the per-player log and check the guest's results.
7. Leave and rejoin: the same selections must run again. Stop cancels unfinished
   work; it cannot undo boosts already applied.

Existing guests are included when Start is pressed. The host is excluded. There
are no progress/need checks. SDUs use the existing fixed 3,225 helper. Keys are
the existing five vault-card token currencies. Challenges use the existing
non-UVHM catalog and are scoped to one guest. Loot uses existing serial delivery;
codes retain their levels and repeated lines request additional copies.

Settings are saved locally, but a new game session starts with AFK disabled.
The SDK queue continues if the panel closes; use Stop to end AFK mode.

## Restore

Exit the game and run `install_test.ps1 -Restore`. Original files and hashes are
under `output/afk-lobby/originals` and `output/afk-lobby/manifest.json`.

## Validation boundary

24 focused Python checks passed, plus Electron AFK button/bookmark checks,
SHiFT-link simulation, Python/JavaScript syntax checks, and the existing panel
check suite (including 480 responsive measurements). All 192 PAK entries verified;
only the dashboard controller payload changed. These are offline checks.
Actual SHiFT Cohtml HTTP access and guest boost results still require the test
flow above; a successful command submission is not proof of a saved guest result.

Current auto-kick validation: 24 focused Python tests passed, including completion gating, failure/disconnect handling, and player-slot reordering. Electron checkbox/payload tests passed. Guest receipt and live kicking are not yet verified. Background SHiFT acceptance is still under investigation; the reflected SDK exposes open/close but no direct friend-accept call.


SHiFT-link repair: the original dashboard ends in an array expression without a
semicolon. The appended IIFE now has a leading semicolon; the link test includes
that preceding array so this integration failure cannot pass unnoticed again.
The repaired PAK has all 192 entries verified. Live connectivity and closed-menu
operation remain pending verification after the restart.

Reliability test update: live history showed 5 SDU failures in 12 completed runs;
logs reported an empty progression pool. AFK now waits for five seconds of pawn
readiness, retries SDUs every two seconds for at most 30 seconds, and checks XP
again two seconds after setting it (bounded retries). Auto-kick rechecks confirmed
XP after loot. AFK loot spacing is at least three seconds, with no total item cap;
a patch timeout stops AFK loot instead of force-opening it. Thirty focused tests
pass. Host readback is not proof of guest replication or a saved result. Party-wide
reward creation remains an existing limitation and the reported lag is unproven.

Floating SHiFT test: the dashboard opens at 42% size over a transparent HTML
background. Drag its toolbar to move it; Full menu restores the normal dashboard.
The toolbar uses the existing accepter start/stop functions. Native compositor
transparency and game input capture still require in-game testing.
After successful loot delivery AFK now waits 15 seconds before requesting a kick,
with a countdown in the AFK status. This is settling time, not a guest-save ACK.

Direct SHiFT input experiment: from gameplay (not the Pause menu), F10 invokes
the reflected ShiftUIFunctionLibrary.Open(0) directly and restores GameOnly input
using the Quick Menu recovery helper on three startup ticks. F10 closes SHiFT;
F11 requests gameplay input without closing it. No continuous focus override is
used. These temporary test hotkeys are F10/F11; avoid assigning those same keys to
Quick Menu slots while testing. Actual movement/look/fire and accepter heartbeat
must be checked together; successful Open or input mode calls do not prove them.

Challenge audit: 3,286 catalog entries; all 371 UI references in the stored
extraction are present. Twenty-five UI references are excluded by the UVH filter.
Catalog extraction build 25234898 differs from installed build 25372571; current
native coverage is unverified. Live AFK ran 3,250 queued rows. Sending/reconciling
these rows is not proof of guest completion. Per-player success tracking, bounded
failed-target retries, and four-row / 100ms pacing replace aggregate success and
64-row bursts. Reconciliation now receives only that player's successful tokens.

Capture diagnosis: the live UnrealWindow affinity changed 1 -> 0 -> 1 with SHiFT
open -> closed -> reopened. The custom overlay now clears WDA_MONITOR within the
game process, only for its unique UnrealWindow. Original affinity is restored
before native close or mod shutdown. This does not release native SHiFT input.
Outside-game dashboard loading is insufficient: request-list/accept operations
are native engine.call bindings, not standalone HTTP APIs in the page source.
