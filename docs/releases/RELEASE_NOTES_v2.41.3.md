# MSBT v2.41.3 - Updater and SHiFT controls repairs

Candidate preparation in progress; this release has not been published.

- Repair Windows update installation when the helper previously disappeared without running. The app confirms that the independent installer helper is ready before exiting; repeated Install clicks share one operation.
- Use one update-check result, show actionable errors, and preserve the Install action for the current verified download.
- Repair the known stale per-user Start Menu shortcut when it points to an older MSBT copy, with identity checks and a rollback backup. Custom shortcuts and existing user data are retained.
- Confirm repeated SHiFT Start commands while background acceptance is already active, preventing a false desktop timeout. Keep the existing session ownership checks and initial rendering delay.
- Label and separate protected-name Add and Search fields; support Enter and show feedback for blank, duplicate and added names. Clear the search after adding so the name remains visible.
- Preserve do-not-delete list saving, menu handling and mobile authorization fixes from 2.41.2.

## Installing the repair

Existing clients whose updater is broken need **one manual installation** from GitHub. A new release cannot repair an old client's local installer handoff before it has been installed. Windows installer/portable and Linux AppImage/portable packages will be released together.

## Qualification status

The previous 2.41.3 candidate at dbedd839a2 passed Windows and Linux package verification, native installation and updater/rollback trials. Windows native protected-list first Save, edit/restart reload, failed-write preservation/recovery and reviewed empty-list saving passed; the owner reported the requested Escape/movement/mouse-look/SHiFT-return case passed. Linux/Proton bridge operation and real AppImage/portable updates with isolated profile preservation and busy-game deferral were verified. Local-artifact updater trials are not a published GitHub download-button test; the repaired old-Windows-client trial replaced its updater module and is not an unmodified broken-client pass.

Subsequent Windows testing found and repaired a missing repeated-Start acknowledgement; its native retest passed. The final candidate also includes the protected-name input repair, with offline form/storage regressions and native Windows label/list/disk observation. Martin confirmed that the Linux Start/Stop/Show, keyboard/mouse/controller and Escape/Tab return/menu-dwell checks were already completed; those results are retained as user-reported evidence for the tested candidate. Linux protected-name Save/edit/restart remains to be checked. Exact rebuilt-package verification and focused changed-path checks remain distinct from the retained earlier tests. No guest-save proof is claimed.

Final rebuilt artifact hashes and publication results will be recorded after verification through the required release workflow.
