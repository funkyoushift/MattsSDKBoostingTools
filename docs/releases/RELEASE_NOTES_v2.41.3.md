# MSBT v2.41.3 - Updater and SHiFT controls repairs

Candidate preparation in progress; this release has not been published.

- Repair Windows update installation when the helper previously disappeared without running. The app confirms that the independent installer helper is ready before exiting; repeated Install clicks share one operation.
- Use one update-check result, show actionable errors, and preserve the Install action for the current verified download.
- Repair the known stale per-user Start Menu shortcut when it points to an older MSBT copy, with identity checks and a rollback backup. Custom shortcuts and existing user data are retained.
- Confirm repeated SHiFT Start commands while background acceptance is already active, preventing a false desktop timeout. Renew the owned lease immediately after each confirmation so frequent Start commands cannot postpone heartbeats. Keep the existing session ownership checks, native lease duration and initial rendering delay.
- Label and separate protected-name Add and Search fields; support Enter and show feedback for blank, duplicate and added names. Clear the search after adding so the name remains visible.
- Open the protected list from the native Friends screen and add **Protect player** to the selected SHiFT player's profile menu. Keep Save in the editor header and size its controls for the Friends view. Stage the selected SHiFT name in the shared list with explicit review/Save; platform aliases are excluded and this action does not send a social request or remove a friend.
- Preserve do-not-delete list saving, menu handling and mobile authorization fixes from 2.41.2.

## Installing the repair

Existing clients whose updater is broken need **one manual installation** from GitHub. A new release cannot repair an old client's local installer handoff before it has been installed. Windows installer/portable and Linux AppImage/portable packages will be released together.

## Qualification status

The previous 2.41.3 candidate at dbedd839a2 passed Windows and Linux package verification, native installation and updater/rollback trials. Windows native protected-list first Save, edit/restart reload, failed-write preservation/recovery and reviewed empty-list saving passed; the owner reported the requested Escape/movement/mouse-look/SHiFT-return case passed. Linux/Proton bridge operation and real AppImage/portable updates with isolated profile preservation and busy-game deferral were verified. Local-artifact updater trials are not a published GitHub download-button test; the repaired old-Windows-client trial replaced its updater module and is not an unmodified broken-client pass.

Subsequent Windows testing found and repaired a missing repeated-Start acknowledgment; that repair's native retest passed. Later source review found a separate heartbeat-starvation case: new Start acknowledgments could continually postpone renewal. The elapsed-time regression fails on the old client and passes the immediate-heartbeat repair, including later Stop and token/readiness safeguards. The historical trialE expiry after Close/reopen remains unexplained; this source finding is not proof of its cause or a native pass for the new client.

The protected-name input repair has offline form/storage regressions and native Windows label/list/disk observation. The added native Friends/profile access has six VM regressions, 26 renderer DOM checks and five save-flow checks; 46 focused Python checks also pass. Native Cohtml execution of those new paths remains unqualified. Renderer screenshots are not native-game proof.

Martin confirmed that Linux Start/Stop/Show, keyboard/mouse/controller and Escape/Tab return/menu-dwell checks were already completed. His later Windows reply, “Yes, those Windows checks were done too,” additionally confirms Tab, controller movement/look and return after menu dwell. These are user-reported results on the previously tested candidates, alongside the earlier Windows physical confirmation; no repeat of those controls tests is required. Linux protected-name Save/edit/restart remains to be checked. Exact final rebuilt-package verification and focused native checks of Friends/profile protection and repeated-Start heartbeat renewal remain distinct from retained earlier tests. No guest-save proof is claimed.

Final rebuilt artifact hashes and publication results will be recorded after verification through the required release workflow.
