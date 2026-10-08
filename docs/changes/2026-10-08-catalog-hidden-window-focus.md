# Item Catalog exposes hidden capture window - 2026-10-08

## Symptom and evidence

Matt reports a white box intermittently opening after Item Catalog delivery on installed v2.30.2. It was not present during native inspection; Matt confirmed the failure happens only sometimes. The running panel was delivering 985 items, so no live Send action or restart was performed by this investigation.

The previous password-dialog investigation did not exercise main-process focus IPC because its renderer harness omitted the preload. That left this separate failure uncovered. `restoreBl4SearchFocusAfterConfirm` invokes `app:focusMainWindow` on both confirm and cancel. The handler selected the first live `BrowserWindow.getAllWindows()` entry and called show/focus on it. `native_card_capture.js` also creates hidden, frameless offscreen BrowserWindows. Their presence/order must not determine the focus target.

## Reproduction and change

In the isolated current-release checkout `C:/Users/mwenn/.codex/worktrees/remove-markdown/working`, new `electron_poc/test_catalog_focus_window.js` runs actual main/preload/renderer with a temporary profile, simulated serial data and a stubbed delivery transport. It creates a real hidden offscreen helper and forces helper-first enumeration, then clicks the real Catalog Local and Confirm DOM controls. Before the fix the test failed because the helper became visible. This confirms the code path can expose a hidden frameless window; the exact user's white pixels were not captured.

Changed only the focus handler in `electron_poc/main.js`: resolve the requesting window using `BrowserWindow.fromWebContents(event.sender)`. Reject missing/destroyed/offscreen owners without falling back to an arbitrary window. Existing restore/show/focus behavior remains for the interactive caller. No password gate or delivery logic changed.

## Validation and deployment

The real Catalog Send/Confirm/Cancel IPC test passes after the fix and keeps the hidden renderer hidden. JavaScript syntax passes; five required Quick Menu/no-BLImGui tests pass. No Python source was changed. Tests submit no live game actions. The test is now distinct from renderer-only password tests and should be included in future release validation.

Local source fix only, based on c3f5a6f; no version change, release, installed-file edit or game restart. The installed running app is still v2.30.2. Matt said he will report the next occurrence; no restart was imposed on the active delivery. Rollback is limited to reverting this handler change and removing the added test. Live recurrence/absence after deployment remains to be confirmed.

## Live white-window confirmation

Matt subsequently reported the white window open. Native inspection found a second MSBT window (15732344) alongside the existing main panel (657846). Its screenshot was a blank white, frameless rectangle and its accessibility tree explicitly reported `No content under offscreen mode`. This confirms the live stray window is an offscreen renderer, consistent with the reproduced focus-handler defect, rather than the password dialog. Alt+F4 was sent only to that observed stray window; the main panel and game were not targeted. Source fix remains local and uninstalled; this observation confirms the original symptom but does not constitute live validation of the corrected build.

The stray window remained after Alt+F4. Stopped only processes matching the exact installed MSBT executable path and launched `npm start` from the corrected isolated checkout. This removes the stray window and loads the focus fix for the current desktop session. No game process was stopped, no SDK was replaced, and no items were resent. Installed package remains unchanged; reopening the installed shortcut reverts to its original handler. No release was authorized in this follow-up.

## Subsequent local installation

The later [Android Windows workspace change](2026-10-08-android-windows-workspace.md) installed the current `main.js`, including this focus correction, into the local Windows archive. The installed shortcut now retains the correction. The Catalog focus regression passed again, and the source desktop was restarted normally without stopping Borderlands or AFK. No public release or version bump was performed. Installed archive/backup hashes and exact file comparison are recorded in the linked entry and `output/mobile-windows/install-receipt.json`. Live recurrence after this installation remains unproven; no live Catalog delivery was sent for verification.


## Combined release status - 2026-10-08

Published in normal stable MSBT v2.31.0 with Android 1.6.0 after Matt explicitly approved inclusion of the offline-checked Epic profile with its live test pending. This supersedes the local-only publication status above. All 11 public release assets were downloaded and hash-verified. Packaged smoke/restart checks and Android installed-APK verification passed. See docs/releases/VERIFICATION_v2.31.0.txt for hashes, CI, evidence limits and rollback. Historical test-candidate hashes above identify the earlier local package, not the combined release. Epic live rendering remains unverified; no new guest-save claim.
