# MSBT v2.41.3 - Updater and SHiFT command repairs

Candidate preparation in progress; this release has not been published.

- Repair Windows update installation when the helper previously disappeared without running. The app confirms that the independent installer helper is ready before exiting; repeated Install clicks share one operation.
- Use one update-check result, show actionable errors, and preserve the Install action for the current verified download.
- Repair the known stale per-user Start Menu shortcut when it points to an older MSBT copy, with identity checks and a rollback backup. Custom shortcuts and existing user data are retained.
- Confirm repeated SHiFT Start commands while background acceptance is already active, preventing a false desktop timeout. Keep the existing session ownership checks and initial rendering delay.
- Preserve do-not-delete list saving, menu handling and mobile authorization fixes from 2.41.2.

## Installing the repair

Existing clients whose updater is broken need **one manual installation** from GitHub. A new release cannot repair an old client's local installer handoff before it has been installed. Windows installer/portable and Linux AppImage/portable packages will be released together.

## Qualification status

The previous 2.41.3 candidate at dbedd839a2 passed Windows and Linux package verification, native installation and updater/rollback trials. Windows native protected-list first Save, edit/restart reload, failed-write preservation/recovery and reviewed empty-list saving passed; the owner reported the requested Escape/movement/mouse-look/SHiFT-return case passed. Linux/Proton bridge operation and real AppImage/portable updates with isolated profile preservation and busy-game deferral were verified. Local-artifact updater trials are not a published GitHub download-button test; the repaired old-Windows-client trial replaced its updater module and is not an unmodified broken-client pass.

Subsequent Windows native rapid-command testing found the missing Start acknowledgement repaired here. Previous artifact hashes do not qualify the rebuilt packages. Fresh dual-platform builds and the fixed native path must be verified before publication. Outstanding itemized platform cases remain in the native qualification ledger; missing tests are not reported as passed. Synthetic Tab events were inconclusive, and there is no controller qualification. Full Linux native storage/menu/lifecycle/social coverage remains incomplete. No guest-save proof is claimed.

Final rebuilt artifact hashes and publication results will be recorded after verification through the required release workflow.
