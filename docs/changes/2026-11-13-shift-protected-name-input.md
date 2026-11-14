# Protected SHiFT name input repair — 2026-11-13

## Symptom and evidenced cause
Martin could not add revcashmoney in Customize. His screenshot places the name in the left search field. The pinned upstream HTML puts Search first and Add second with placeholder-only labels; those placeholders are absent in his native screenshot. Add reads only the second field and silently ignores blank/duplicate input. A previous search can also hide a successfully added name.

## Change
Isolated branch `codex/shift-name-input-20261113`, based on a2cbdb7b, preserves the primary dirty checkout and existing release worktrees. `tools/afk_lobby/repair_shift_protected_inputs.py` adds persistent labels, puts Add before a separate Search row, supports Enter, and displays blank/unavailable/duplicate/success feedback as text. Successful additions and duplicate lookups clear the filter so the name is visible. The existing review and explicit Save requirement is unchanged. `build_azalea_pak.py` applies the checked HTML/controller transformations and records the changed HTML. `electron_poc/test_shift_mini_panel.js` exercises the actual rendered fields/buttons/keyboard, filtered additions, duplicate handling, safe text and existing Save flow.

## Validation
The new renderer regression fails against the baseline (Add field follows Search), then passes against both the repaired branch build and the exact installed-version repair: 25 DOM checks plus 5 storage-flow checks. Each controller passes JS syntax, protection suite and 25 lifecycle cases. Python compile checks and 5 no-BLImGui tests pass. All 192 PAK entries round-trip; only dashboard.html and js/dashboard/dashboard_controller.js differ from each respective baseline. These are offline Electron/mocked engine checks, not native Cohtml or real social-action proof.

## Installation and rollback
Martin explicitly closed BL4 and authorized installation. Process absence was checked immediately before replacement. The local installation was patched from its exact existing PAK, not replaced by the newer branch's complete integration. Installed SHA256: `4b748dd8e7cf2a0172921997a121e40adb1026d232b431f86341f274d78e1f78`.
Original SHA256: `fdb039f13ea24c4b8b30b8cc972a83df7f6c71f20a09e7c5f916aebad6a9b93f`.
Backup: `C:/src/MSBT-Workspace/local/shift-name-input/backup/pakchunk90-Windows_90_P.pak`.
Target: `C:/Program Files (x86)/Steam/steamapps/common/Borderlands 4/OakGame/Content/Paks/pakchunk90-Windows_90_P.pak`.
Rollback with BL4 closed: restore that backup to the exact target and verify the original hash. 190 other payloads, existing background code, SDK companion, settings and character/profile saves were not changed. No names were prepopulated. BL4 remains closed; no version bump, publication, tag or Electron installation change. A later official mod reinstall may replace this local PAK; integrate the source repair into a future authorized candidate.

## Tobgun attachments and remaining checks
The two message text files are third-party diagnosis/request material, not Martin's instruction to adopt GenieBot, 25 seconds or disable confirmations. His PAK90/91 conflict is plausible for his described setup but not established locally: no pakchunk91 exists in Martin's Paks tree; among 5 parsed v3 PAKs only 90 contains the dashboard replacement. 363 other-format PAKs were not audited for overlaps, and runtime load priority is not proven. A standalone HTTP GET received 403 from port47991, consistent with the documented same-process guard; this is not evidence of broken storage. Native loading, visual labels, typing/Add/Enter and Save/restart persistence still need in-game confirmation. No real friendships/invites/removal actions were tested.

Evidence: `C:/src/MSBT-Workspace/local/shift-name-input/installed-candidate/manifest.json`, `installed-renderer/mini-panel-test.json`, `installation-audit.json`, baseline/fixed/installed renderer stdout/stderr and `payload-comparison.json`.
