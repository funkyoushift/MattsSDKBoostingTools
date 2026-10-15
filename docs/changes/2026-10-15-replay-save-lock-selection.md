# Replay save-read lock and hidden mission selection

Martin reported that FL4K replay stayed on the original map and that later mission choices became stuck on "Choose one mission first".

## Evidence and cause

- Installed v2.39.0 desktop journal `f6c3faa810344fbe9318c1ad12290537` failed with Windows `EBUSY` reading the original save after automatic character reload. The target was `Mission_Main_Harmonica4`, checkpoint22, `Harmonica_P.FT_Harmonica_IslandHub`. Both character-selection receipts returned; no travel receipt was issued. This establishes a failure before travel, not a defective cross-map travel call.
- Martin's screenshot shows two selected missions, one hidden by the campaign filter. The mission list uses single selection for replay, but its change handler retained hidden entries in its shared selection Set. The objective preview then correctly refused multiple missions, displaying an unhelpful generic prompt.

## Changes

- `electron_poc/save_replay_service.js`: classify `EBUSY`, `EACCES`, and `EPERM` only around read-only save decoding in `checkDisk`. Reuse the existing ten-second autosave verification wait in supported post-reload phases. Persistent locks still fail, preserving backup. No write, native character selection, travel, or placement request is retried.
- `electron_poc/mission_panel.js`: single replay selection replaces all previous selections; replay filters remove hidden selections and refresh objective choices. Completion mode retains its intentional multiple and hidden selections.
- `electron_poc/save_replay_panel.js`: explain the solo-lobby/second-character requirement beside the replay action, distinguish missing mission selection from unavailable map data, and surface failed/uncertain/interrupted run messages beside Start with Stop setup guidance.
- Regression coverage in `test_save_replay_service.js` and `test_mission_views.js` includes transient and persistent file locks, a different starting map, one travel receipt, unchanged installed save bytes, campaign switching, replacement selection and completion-mode preservation.

## Validation and delivery

- 28 Node replay-service checks passed, including the existing encrypted Epic-account transaction and six new lock cases.
- Electron mission-view and save-replay-panel tests passed with all game actions stubbed; responsive checks included.
- Five no-BLImGui/startup checks passed. Changed JavaScript syntax and diff checks passed.
- Bundled Python imported the current source save helper. Current live bridge returned HTTP200, ok/started.
- Local desktop preview is intended for the next live retry; SDK gameplay code is unchanged and does not need replacement or game restart. Public v2.39.0 assets/version remain unchanged. Local preview can be rolled back by closing it and reopening the installed app.
- Existing failed replay retains its backup and lease until Stop setup closes it. Do not repeat its character or save actions outside the service. Retest solo: close the failed run with Stop setup, choose one FL4K mission/objective and start again. The new live DLC map transition remains unverified until that retry succeeds.

No release published. These are desktop-only local repairs.

## Authorized combined patch release

Martin subsequently confirmed the placement was correct and retracted the missing-objective report. No new waypoint or objective-data change was made. He explicitly requested publication of the Windows fixes and a newly updated APK.

- Preparing Windows2.39.1 and Android1.6.3/build36. Previous release included unchanged Android1.6.2/build35, explaining the absent phone update.
- Generated desktop method contract now includes saveReplay. Paired mobile requests use the same PC-owned replay service instead of being rejected; native solo-host, current identity, acknowledgement and transaction guards remain. No save is copied to the phone.
- New actual-handler/mobile-transport regression verifies start/bookmark routing, acknowledgement forwarding, unknown-action rejection and duplicate-call deduplication. Existing mobile API regression passes. Android build, device installation and publication checks are in progress; do not claim completion yet.
- Initial Android build selected Android Studio's Java25, which this Gradle version rejects. Switched to the existing JDK17; no application code change was needed. USB phone was initially unauthorized; asked Martin to approve its debugging prompt while independent builds continue.
