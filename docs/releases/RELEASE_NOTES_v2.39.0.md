# Borderlands 4 Modding Tools v2.39.0 — Powered by Funk

## Mission replay and bookmarks

- One numbered campaign selector covers 39 story/DLC missions and 506 main objective sections, including points beyond the current save.
- Automatic character unload, backed-up inactive-save editing, character reload and map refresh preserve current gear and levels. Solo-host replay requires a second existing loadable character in the same profile.
- Starting placement uses 326 authored preceding-waypoint candidates where collision is usable; 180 sections and unsafe/unloaded coordinates keep the native spawn-station fallback.
- Save and restore a mission-state bookmark without configuring coordinates. Bookmarks restore the captured mission/world timeline with current equipment and levels.
- Dialogue skip uses native conversation completion, with a session toggle. Live completion and retention through map reload passed; some authored timed scenes may still wait.

## Co-op completion and different DLC access

- Full-game completion retains the original bulk mission callbacks. It does not replay every mission scene or run the broken fog-reveal teleport tour.
- Before mission work, request each visitor’s actual entitlement snapshot and wait for the normal server reply. Recheck current game access, continue available work and report blocked content separately. No DLC ownership is granted or changed.
- Repair missing per-player campaign completion credit through the existing verified native once-only mission callback. UVHM runs after its campaign prerequisite; confirmed steps avoid a redundant wait.
- Keep all mission definitions visible. Content the game permits remains eligible; blocked/unknown access is deferred rather than hanging the full run.
- Character upgrades choose a progression-bearing character instead of a possessed vehicle. Native SDU purchase readback verifies all 59 ranks.
- Individual mission/objective completion keeps lobby identity and DLC checks; selected-composite arrival initialization is corrected and remains experimental pending wider gameplay coverage.

## Compatibility and other repairs

Epic native profiles and account save encryption, Shinies credential forwarding, per-guest UVHM verification, desktop navigation/layout repairs and no-BLImGui startup checks are included. The Android app is unchanged at 1.6.2; both the rolling and versioned APKs accompany this release.

## Test results and limits

591 focused Python checks,23 focused Node checks, desktop control tests, responsive replay/mission UI checks and matching packaged-resource audits passed. The release build also runs the standard desktop and installer checks.

A live three-player full run included UDS_Prophet, confirmed by Martin to own only bounty packs. Automatic access refresh passed; available missions completed and the run reached its final recheck without stalling. All three characters had59/59 SDU ranks verified. Native challenges reported 2,574 complete, zero incomplete and 261 unavailable definitions; 60 current vault-card challenges were verified. Campaign credit and all 25 UVHM challenge steps passed native verification. Both visitors confirmed story completion and UVHM 7.

Mission/replay/full-progress tools remain visibly experimental. Blocked DLC, unavailable definitions, unsupported bulk cosmetic/non-base vehicle unlocks and unavailable Mayhem are reported separately. Shared progress changes affect the lobby. Individual encounters and guest own-game save/rejoin persistence are not exhaustively verified. A finished run is not a guarantee of a saved 100% character or every collectible/achievement. Keep backups.

## Install

Choose **MSBT-Installer-v2.39.0.exe** or extract **MSBT-Portable-v2.39.0-win-x64.zip**. Close Borderlands 4 before updating its SDK components. The release also includes **MSBT-Mobile-Controller.apk**, the versioned Android 1.6.2 APK, the standalone SDK mod and update metadata. Existing Android users do not need to reinstall the unchanged APK.

Original contributors retain credit; native dialogue research credit includes [Yeti’s Dialog Skipper](https://github.com/RedxYeti/yeti-bl4-sdk). See the [README](https://github.com/funkyoushift/MattsSDKBoostingTools#readme) for setup, credits and limitations.
