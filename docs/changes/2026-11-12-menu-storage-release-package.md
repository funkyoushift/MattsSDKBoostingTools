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

## Authorized release preparation and final checks

Martin explicitly authorized publication: "finish the release prep then release it."
Windows/Linux CI43189250665 passed at0b3d8c39, including Windows actual
installation and installed-updater ASAR tests. Linux output hashes match CI logs,
and its portable payload passes11 source/identity checks.

The final local Windows installer exited0 and upgraded2.41.1 to2.41.2. All1497
application files match the audited output; only the normal uninstaller is extra.
The entire recorded user-data tree and named preferences were unchanged. Shortcut
targets/arguments/work directories are unchanged; shortcut binary timestamps and
expected version/size registration fields changed. SDK, companion and PAK match
the packaged hashes; protected JSON remains absent as before. Receipt paths:
`../release-final-install/compare-after-candidate.json`,
`../release-final-install/final-installed-payload-audit.json`, and
`../release-final-native/receipt.json`, relative to candidate root.

Final native execution: supported Start queued and reached confirmedactive on
2026-11-12 at09:20:14UTC. Polling observed active until Show at09:23:18UTC,
then foreground/connected/running. A physical Escape press interrupted Computer
Use; it does not establish a successful final menu cycle. Automated Escape also
failed to open the menu with acceptance stopped, so synthetic keyboard evidence
is inconclusive. A fresh read at09:24:42UTC confirms the game remains open and
foreground acceptance running; this active session is being preserved as directed.
No diagnostic payload or test protected-name was installed for this final trial.
No newly identified friend acceptance/deletion is claimed from this run.

Release judgment: installer preservation, exact payload identity, CI,183 offline
regressions, prior native storage proof and user-confirmed v12 menu tests support
shipping this repair. The interrupted final physical Escape test and unqualified
gamepad/Tab/travel/Linux/Epic coverage are disclosed in public notes rather than
claimed as passes. These verification limits do not block the authorized release.
No further game control is required to publish the already verified artifacts.

## Published and verified

Stable/latest2.41.2 published2026-11-12T09:28:36Z at
https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/v2.41.2.
Tag d21713364770b2082272f49a4a02dc8a59dabe72 contains only documentation
changes after CI-tested0b3d8c39; implementation remainscdfd8996. Tag CI
43191444533 passed. Allfour public assets were fully downloaded and SHA256/size
verified against the tested local packages; GitHub expanded assets contains
exactlyfour binaries plus the two automatic source archives. Receipt:
`../release-final-ci/public-download-verification.json`. Linux AppImageSHA256
4aff76ac8697b9612fdf8d2423a3a8887bfd6daf7873f6f1891e54d18359791e;
Linux portableSHA2564881ec5bc42a6ba2bf52c4583e0c7340547c6af53c727b0cfcb3207955fd6f6a.

The normal installed desktop and game integration are the final released2.41.2,
not temporary diagnostics. Fresh SDK/PAK/companion hashes match the public
package; private protected-settings state is unchanged. The game session was
preserved after physicalEscape interrupted Computer Use, per the subsequent
instruction not to disturb an active session; latest read showed foreground
SHiFT acceptance running. No force-close, input workaround or rollback occurred.
Backups remain in release-final-native/backup and release-final-install/backups.
The interrupted final physical test and platform limits remain public disclosures.

Default-branch metadata promotion completed through normal PR19 merge at
f29e818d68a4db15573b9c48cdf79f619ff27e73. Public raw README/latest.json verify
allfour2.41.2 desktop URLs and retained Android1.6.6/v2.39.9 and selector links.
Receipt: `../release-final-ci/public-main-metadata-verification.json`. Historical
PR18 was not merged or modified. No release blocker remains; disclosed native
and platform validation limits remain follow-up coverage.
