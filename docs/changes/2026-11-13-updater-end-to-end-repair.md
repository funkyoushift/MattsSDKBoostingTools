# In-app updater end-to-end investigation - 2026-11-13

Martin reports in-app updates have failed across several releases. Work is
isolated from dirty primary source at local/updater-repair/product, based on
39127450 (released2.41.2 implementation plus verified release gates). No version
bump, public release, host installation or game changes are authorized by this
repair. Both Windows/Linux publication gates remain required.

Historical source and public asset inventory establish: 2.39.9 normal packages
use embedded Setup/API/Windows ZIP, with a canonical per-user target that can
leave NSIS/custom launchers stale. Only fallback electron-updater clients depend
on latest.yml, absent from2.40+. Versions2.40.0/2.40.1/2.41.0 have identical
updater code with Electron-patched fs.access(app.asar), whose ENOENT reproduction
was recorded November5. The physical original-fs repair shipped2.41.1 and is
identical in2.41.2. These old clients cannot obtain local handoff fixes through
their own failing path. They do not prove every later failure has the same cause.

Confirmed current check/UI defect: app:checkUpdates fetches GitHub independently
twice. If metadata succeeds and updater check fails, the renderer replaces the
error with generic availability while disabling Download. Repair reuses one
validated updater snapshot and preserves actionable errors/download state. New
deterministic snapshot/state/error tests and JS syntax pass; actual native
packaged repair qualification remains pending.

Real native test harnesses run only on disposable CI runners. They install/launch
actual published2.41.1 files verified against GitHub digests, invoke unchanged
preload update IPC against published2.41.2, observe same-path handoff/relaunch
and check seeded preferences/bookmarks/data across restarts. Windows uses the
actual production RunAs/NSIS handoff, not the prior probe installer. Linux tests
portable and real per-user AppImage setup with isolated HOME/XDG and default
sandbox. Harmless external sentinels are not live game-save proof.

CI pending. Ubuntu26 sandbox startup and actual BL4/Proton remain separately
unqualified. No user desktop/game was launched, closed or changed. Read-only
CIM process inspection was unavailable inside the local sandbox; no process
action depended on it. User-data updater handoff folders were absent in the
primary app-data location. Current Windows registration reports2.41.2; this does
not prove every shortcut or running copy has that version.

## Verified stale local launcher and repair

Read-only archive inspection found ProgramFiles2.41.2 and retained per-user
LOCALAPPDATA/Programs/MSBT/app2.40.1. Both desktop shortcuts and common Start
Menu target the current copy, but the user Start Menu targets the older broken
updater. This is a concrete remaining cause of repeated updater failures despite
a manual new installation; the running process was not inferred.

The one verified stale user Start Menu link was backed up then repointed to the
existing verified2.41.2 executable. No executable/settings/game files were
changed and no app was launched. Receipt/rollback original link:
../evidence/shortcut-backup/receipt.json and user-start-menu.before.lnk under
local/updater-repair. BackupSHA256
5c0f0cf36c8cf23d9e6bce6366fbdef55c4ac521a1402534c6ba3fb484a7acd0;
updatedSHA25688ab7c40509583e0e865fac5cedab3a3b06ff40dab3d99dabeccce0e501df570.
Rollback copies the preserved original link back to the exact receipt path.

Production startup now migrates only that known per-user legacy shortcut when
both ASAR package identities are MSBT, the running copy is strictly newer and
the shortcut still targets the canonical legacy executable. Original bytes and
a receipt are retained; custom fields/unknown targets are preserved; older
installations and user data are never deleted. Unit tests pass; native Electron
shortcut fixture added to Windows candidate verification.

## Actual published upgrade diagnostics

Run43341139220 was cancelled after overly long CDP waits; its always-upload
receipts were recovered. Actual2.41.1 Windows, Linux portable and AppImage
checks and SHA256-verified2.41.2 downloads passed. The app exited during
handoff, but the test continued evaluating a closing renderer; Windows later
run43342551097 exposes the same post-request CDP timeout. Linux automatic
restart detection also failed. These are not enough to label the production
handoff broken or repaired. Test now detaches debugging immediately after the
request and separately observes OS processes, payload replacement, helper
scripts/logs, rollback directories and second restart. Failure snapshots retained.

## Follow-up verification

Independent review found that checking-for-update overwrote the downloaded UI
state before a failed fetch. The catch path now consults the current updater's
verified receipt and generation, retaining Install only for a valid download
and leaving newer transfers alone. Real event-emitting updater regression passes.
Native Windows shortcut fixture exposed Shell expansion of 8.3 paths; migration
now accepts aliases only when both resolve to the same existing physical path.
Unit regressions and syntax checks pass; native CI rerun is required.

Run43343615501 detached CDP before handoff. Windows check and verified download
passed but the same-directory ASAR was not replaced within180seconds. No helper
error file was found. The cause remains unresolved; further bounded process and
IPC-result diagnostics are required. This is not a successful installed upgrade.
