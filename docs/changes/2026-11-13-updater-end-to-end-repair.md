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
