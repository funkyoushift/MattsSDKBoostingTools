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
unchanged by menu integration. The Python fixture suite and final package audit
will be recorded below once complete.

## Installation and cleanup

BL4 was already closed on inspection for this packaging turn; this turn did not
force-close it. The v12 guarded restore and verify completed. Original PAK,
companion, enable file, main SDK and private-settings state match the pre-test
receipt at ../../../menu-observed-v12-trial/installation.json. BL3 was not
controlled. No diagnostic remains installed. Production source and packages
are separate from the normal installation.

## Remaining qualification

Final production companion integration, independent review, full automated
regressions, final Windows build and exact bundled source checks are in progress.
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
