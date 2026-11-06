# Updater repair and v2.41.1 preparation — 2026-11-05

The desktop updater's packaged-file check is being repaired after an Electron 44.3.0 ASAR fixture showed that `fs/promises.access(app.asar)` returned `ENOENT` while `original-fs.promises.access(app.asar)` succeeded. The repair uses `original-fs` for the physical ASAR checks in Windows update handoff and Linux portable download validation. Existing v2.41.0 installs need one manual update to receive the fixed updater. The repair and regression coverage target Windows and Linux. This is fixture-level evidence; reproduction of the reported end-user failure remains pending. No Android build/version change and no live game/device trial are in scope.

Release metadata is prepared at v2.41.1 across Electron, SDK metadata and the bundled release manifest. Release CI/package validation, four asset hashes, publication status and updater behavior remain pending. See [release notes](../releases/RELEASE_NOTES_v2.41.1.md).

## Release hold and SHiFT startup trial

Martin reported that Play while accepting blocks movement/mouse look from the pause menu; F10 then did nothing from gameplay. Cached SDK status showed companion available/idle, not direct native input proof. He closed the game himself. Publication is held pending resolution.

F10/F11 registration was deferred to `shift_overlay.tick()`, reached through the desktop bridge UI-widget tick. Candidate adds explicit SDK startup registration with idempotent fallback and rollback of partially enabled bindings. Native pause-menu input behavior remains unverified. Never move native operations into the HTTP worker.

Validation: 16 overlay/startup/import checks, five SDK ZIP checks, and syntax pass. ZIP checks initially failed collection without PYTHONPATH, then passed with the required tools path. The 156-member SDK differs from installed v2.41.0 only in `__init__.py`, `pyproject.toml`, and `shift_overlay.py` after normalizing line endings. Electron source/synthetic-package regression and existing platform/handoff checks passed; installed-package CI pending.

With BL4 closed, installed candidate SDK SHA-256 `37da08bbf16428dd08e943e15622b0432ab3c3823c40578ee306ad42757f52f3`, backing up the prior SDK to `C:/src/MSBT-Workspace/local/shift-friends-audit-20261105/v2411-startup-trial/MattsSDKBoostingTools.before.sdkmod`, then launched Steam app 1285190. PAK, companion and protected settings unchanged. Martin confirmed F10 now opens SHiFT in the fresh session. Asked for a manual Play while accepting control check, explicitly stating that this enables ordinary incoming-request acceptance; no social action was issued by tools. Pause-menu support and full control remain pending. Restore the SDK backup only with BL4 closed if rollback is required; do not restore the original broken PAK.

One delegated worker reached its usage limit. Local-offload extraction returned ConnectError, zero cloud calls; no retry loops or savings claim. Worktree is uncommitted/unpublished; metadata PR #18 remains separate and unmerged.


## Current v2.41.1 candidate and release hold

The source candidate now includes the Electron ASAR check repair, explicit SDK startup registration for F10/F11, and a correction that lets ordinary acceptance proceed without a reviewed protected-list prerequisite. The existing Remove All guard remains. The package uses candidate PAK SHA-256 `728165a795f7543b9a109604b60a8ae54f70de2c6cf92f4a37c231982a5e617f` and companion SDK SHA-256 `9fc2a823605f1035cf3df8b53ff20b753b2db8798d51b15fbe6fb00f941c8c02`. Martin confirmed F10 opens SHiFT in a fresh session.

The native controller-input path is unchanged. Martin reported that Play while accepting blocked movement and mouse look from the pause menu; that live behavior remains unresolved. No social action was issued by tools, and publication remains held pending a supervised check. Android remains 1.6.6/build 39, unchanged.

Root-reported offline evidence: 38 focused Python background/storage tests and JavaScript background/protection/automation checks passed. The updater's Electron ASAR source and synthetic-package regression passed; installed-package CI remains pending. Windows/Linux builds, exact four-asset hashes and publication are pending. See [release notes](../releases/RELEASE_NOTES_v2.41.1.md).
