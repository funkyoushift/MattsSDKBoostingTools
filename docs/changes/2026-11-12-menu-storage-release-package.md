# 2026-11-12: Combined menu and protected-list release package

Martin requested packaging, explicitly including the do-not-delete list saving
updates. Publishing, tagging and public uploads remain unauthorized.

## Included scope

The isolated 2.41.2 candidate retains the earlier atomic first-save/edit,
read/save race, matching save acknowledgement and protected-list persistence
repairs, plus same-game-process companion access and mobile security changes.
The observed-menu lifecycle adds menu suspension, stable-exit restart and
truthful desktop suspension/resume status. No version increment beyond the
already prepared 2.41.2 is needed for these repairs.

## Evidence

Martin confirmed v12's Escape open/close, W movement, mouse-look and small SHiFT
return. The frozen short-cycle trace confirms an actual native active transition
after the restart command. Martin also reports the requested 2.5-minute test
worked; the available trace does not clearly show that long active-to-suspended
interval, so long dwell is user-confirmed rather than independently trace-proven.
A later trace includes another successful short cycle and an earlier terminal
error of unresolved cause. Sustained operation is not fully qualified.

Protected-list tests against dashboard_controller.js extracted from the actual
candidate PAK pass 13 groups, including saved names, review state, failed saves,
stale reads, reconnect and reopen. The source storage write functions are
unchanged by menu integration. The final Python suite passed 183 tests; the final artifact audit passed all
25 checks, including exact protected-list and menu source in both outputs.

## Installation and cleanup

BL4 was already closed on inspection for this packaging turn; this turn did not
force-close it. The v12 guarded restore and verify completed. Original PAK,
companion, enable file, main SDK and private-settings state match the pre-test
receipt at ../../../menu-observed-v12-trial/installation.json. BL3 was not
controlled. No diagnostic remains installed. Production source and packages
are separate from the normal installation.

## Remaining qualification

Final production integration, independent review, automated regressions, Windows
build and exact bundled source checks are complete and passing.
Final packaged native menu behavior, Tab/gamepad/travel coverage, physical mobile
and Linux/Epic qualification, and final installer upgrade remain unverified.
User-facing readiness will distinguish a packaged candidate from a published or
fully live-qualified release.


## Final source checks before packaging

The final combined Python suite passed 183 tests in 24.58 seconds, with seven
existing import-package deprecation warnings. It includes menu handoff, atomic
protected-list storage, localhost HTTP, background lifecycle/native wrapper,
SDK routing, AFK and Quick Menu checks. Hidden Electron AFK rendering passed;
menu-suspended and resuming labels override a stale running flag. PAK link and
background JS tests passed, including repeated Start/Show and lost-bridge cases.

Independent review found and repaired three production integration defects:
native Open's own pause incorrectly cancelled restart; retry/Stop closure did
not preserve a separately open menu; and a delayed automatic Start token could
survive explicit Stop. All have regression coverage. Desktop presentation is
separate from the native HTTP protocol state, and reports active only after
native activation. Token/instance/process authorization remains enforced.

AST comparison confirms _initialize, _save, _process_save and _load are exactly
unchanged from the existing storage-repair candidate. The final companion
archive is a737e10a4d18e47887581d72be41904983664041e15862ea1665b653d80422ca;
the PAK remains fdb039f13ea24c4b8b30b8cc972a83df7f6c71f20a09e7c5f916aebad6a9b93f.
Both will be audited again inside the actual installer and portable output.

The production adapter adds cancellation/status/retry behavior beyond v12 and
has not received its own final native trial. This is an explicit remaining
qualification gate, not a reason to omit the requested local package.

## Final packaged result

Implementation commit: `cdfd8996a7b02cd5631d98174de283c4ec575556`.
The Windows build passed all invoked checks, including 48 Python dependencies,
3,323 resources and updater packaging. All 25 final artifact checks passed.
Installer and portable ZIP match all 1,497 unpacked application files; bundled
metadata, SDK, PAK and all five companion Python sources match the final source.
The bundled companion has no diagnostic observer injection.

- `MSBT-Installer-v2.41.2.exe`: 320,584,764 bytes; SHA256 `9136b3811a4316fe7c6f653e5cbd6229d3cc3b800b3cf2b320b9fb074d436bc1`.
- `MSBT-Portable-v2.41.2-win-x64.zip`: 381,085,445 bytes; SHA256 `951b415a00630d0bff2feb18cfc1c8e6116ac3b85466df607aa407a0927ba1f4`.
- `app.asar`: 83,409,464 bytes; SHA256 `302a24b947ec45059e6e3cbc1b9c322f366a6d3d3811796d150cfd7abd4defab`.
- `MattsSDKBoostingTools.sdkmod`: 1,925,738 bytes; SHA256 `81287780fe44bf881c98123ed1ea885a67f0a3da39a7a62477f3a36231528b1b`.
- `pakchunk90-Windows_90_P.pak`: 36,257,278 bytes; SHA256 `fdb039f13ea24c4b8b30b8cc972a83df7f6c71f20a09e7c5f916aebad6a9b93f`.
- `ShiftManagement.sdkmod`: 19,706 bytes; SHA256 `a737e10a4d18e47887581d72be41904983664041e15862ea1665b653d80422ca`.
- `manifest.json`: 21,720 bytes; SHA256 `5b5a1e6d2b27bca7d9386a215b5a1759b101251aeac3136e57b1c1581c2e81b9`.

Artifacts are under `dist_electron/`. Full evidence is in
`../release-menu-artifact-audit/audit-results.json` and
`../release-menu-package/validation-summary.json` relative to the candidate root.
The actual final installer upgrade was not run; offline rollback checks and exact
archive identity passed. No new Linux build or public upload was performed.
The bundled public download URLs are draft release metadata, not available
uploaded assets. A fresh post-build restore verification passed: BL4 closed,
original installed files unchanged, real private-settings state preserved.

Readiness: requested Windows package complete; public release remains on hold
for final production native qualification and the remaining platform/installer
checks listed above. No app-access request is pending.
