# In-app updater investigation and repair — 2026-11-13

Status: updater repairs implemented and independently reviewed. Windows candidate
handoff and Linux published-client upgrades pass with fixture data preservation.
Both candidate desktop platforms pass packaging/native verification. **Unpublished;
not release-ready under the required live-game gate.** The initial repair kept
SemVer unchanged; subsequent authorized 2.41.3 preparation is recorded below.

## Scope and source

Martin reported that in-app updates had failed for several releases while manual
GitHub installers worked. Work is isolated on `codex/updater-repair-20261113` in
`C:/src/MSBT-Workspace/product/local/updater-repair/product`, based on `39127450`
(released 2.41.2 integration plus release gates). Unrelated primary dirty work,
mobile-security work and the active game session were preserved.

The final packaged implementation is commit
`a9e1f03ceb8d71f6b37099642a86a26d1fef77ee`. Later commits change diagnostics/docs
only. Evidence root: `C:/src/MSBT-Workspace/product/local/updater-repair/evidence`.
Candidate packages: `C:/src/MSBT-Workspace/product/local/updater-repair/candidate-a9e1f03c`.
They retain development version labels 2.41.2 and **differ from published 2.41.2**.
Do not upload them over existing public assets or call them a released update.

## Evidenced causes

| Versions/path | Evidence and effect |
| --- | --- |
| 2.39.9 normal package | Embedded Setup uses GitHub release API and Windows ZIP, but its canonical per-user target can leave older/custom launchers stale. Only fallback electron-updater clients depend on latest.yml; absent YAML is not the normal client's root cause. |
| 2.40.0, 2.40.1, 2.41.0 | Identical updater uses Electron-patched fs.access on physical app.asar. Recorded ENOENT blocks Windows handoff and Linux portable staging. 2.41.1 changed this to original-fs; 2.41.2 retains the repair. |
| Current Windows helper | Native marker-only CI 43349572707 reproduced successful process creation/exit without the detached PowerShell script executing. Direct non-detached spawning also failed parent-exit survival. Hidden Start-Process bootstrap in 43350005042 executed and survived the parent. This correlates with the released-client helper disappearing before installation. |
| Current update check/UI | Main fetched GitHub twice independently. A second check failure could be overwritten by a generic availability message, leaving Download disabled. Real checking events also overwrote downloaded UI state before failed fetches. |
| This PC's launcher | Program Files contained 2.41.2, while the user Start Menu link targeted retained per-user 2.40.1. Desktop/common Start Menu links were current. Running-copy identity was not inferred from installed version labels. |

Historical asset inventory is retained locally in `releases.json`; source notes
include the October 28 unified release and November 5 ASAR repair. Old failing
clients cannot fetch a fix through their own broken local handoff. They need a
one-time manual installer for a future repair release.

## Product changes

- `main.js` and renderer: use one validated release snapshot, retain actionable
  errors, and restore Install only from the updater's current verified download.
  Concurrent newer download generations keep their own state.
- `platform_release_updater.js`: Windows launches an independent hidden helper
  through a hidden PowerShell bootstrap. File logs and PID are retained. The app
  waits for bootstrap **exit**, then a unique readiness nonce, and atomically
  publishes authorization before quitting. Late helpers cannot install without
  authorization. Concurrent Install calls share one operation; pre-authorization
  failures permit retry; post-authorization attempts remain latched. Downloads
  cannot race a handoff. NSIS RunAs, target directory and checksum checks remain.
- `legacy_shortcut_migration.js`: only the known per-user legacy link is eligible,
  with exact installer U+2014 name, verified application identities, strictly newer
  running version, physical-path alias checks, original backup and race checks.
  Custom fields and unknown targets are preserved; old installations/data are not
  deleted. Package configuration and native Electron regressions verify the name.
- Linux activation behavior is unchanged. No SDK/PAK/game implementation changed.

Independent review found and corrected lost downloaded-state controls, duplicate
installer launch risk, authorization-file publication race, Windows short-path
aliases and the exact shortcut-name mismatch. Focused regressions cover these.

## Final validation

| Check | Result and exact evidence |
| --- | --- |
| Candidate Windows + Ubuntu 22.04 packages | PASS, run 43352639786 at a9e1f03c: installer/portable and AppImage/TAR, native desktop/package checks and aggregate gate. Python startup suite included 62 passing checks. |
| Windows repaired handoff, system C: temp | PASS, run 43353972708. Real public 2.41.1 installed; **only updater module replaced with candidate**; actual public 2.41.2 installer downloaded/verified and run with production elevation. Automatic relaunch, two subsequent 2.41.2 launches, LocalStorage/bookmarks/sentinel preservation and exact target ASAR hash pass. |
| Windows repaired handoff, runner D: temp | Same PASS, run 43353975911, including path containing spaces. |
| Linux published-client portable + AppImage | PASS, native Ubuntu 22.04 run 43346634219: **unmodified public** 2.41.1 to public 2.41.2, actual setup/update IPC, exact payload, automatic restart, second-launch 2.41.2, preferences/bookmarks/editor preferences/sentinel hashes, normal closure. |
| Final package download hashes | All four locally downloaded artifacts match the aggregate receipt. `candidate-a9e1f03c/local-artifact-hashes.json`. |
| Packaged Windows code versus tested repair | Exact module SHA256 `40c3fc3b8b87bc3e1bcfe82ceae00f5e0e32a9634df9c60b755771f0b0ff4f19` matches both real upgrade trials and the packaged Windows ZIP. `tested-module-binding.json`. |

Windows target ASAR SHA256 is
`302a24b947ec45059e6e3cbc1b9c322f366a6d3d3811796d150cfd7abd4defab`, independently
matched against the ASAR extracted from the digest-verified public Windows ZIP
(SHA256 `951b415a00630d0bff2feb18cfc1c8e6116ac3b85466df607aa407a0927ba1f4`).
The modified Windows diagnostic is **not** an unmodified published-client pass.
Preserved sentinels are fixtures, not live protected-list or guest-save proof.
Actual protected-list/game persistence repairs remain in the integration baseline.

## Useful failed approaches and limits

- A spawn event did not prove PowerShell execution. execFile completion could wait
  for inherited streams; a benign exact-bootstrap probe took 3556 ms versus 279 ms
  for bootstrap exit. Production now observes exit and readiness separately.
- CDP queries against a closing renderer hung. HTTP and WebSocket startup are now
  bounded; handoff is observed externally. Missing/partial app.asar during normal
  uninstall/copy is expected; the test now waits for readable new package identity,
  automatic restart and final reference hashes instead of treating absence as success.
- Linux's relaunched Electron main rewrote its environment/argv. A HOME-only
  detector missed the actual new app, then collided with its single-instance lock.
  Isolated ancestry/path detection fixed the test; raw snapshots retain proof.
- Native shortcut fixtures need actual ASAR files and cleanup after Electron exits
  (its archive cache holds files open). A Node parent performs guarded cleanup.
- Early long temporary-directory trials captured NSIS old-uninstaller exit 2 and
  “Failed to uninstall old application files.” The numeric code does not identify
  a Win32 error. Excessive path lengths and hash-poll interference were leads,
  not proven causes. Final realistic short C:/D: paths pass; arbitrary long install
  paths remain unqualified. No uninstaller logic was changed speculatively.
- UAC uses production RunAs on a disposable Windows runner. Human standard-user
  UAC approval/cancellation was not physically exercised; probe failure recovery
  is distinct from that. No live BL4, Proton, real friend actions or real saves
  were used for this updater task. Ubuntu 26 sandbox startup remains an earlier
  qualification failure; Ubuntu 22.04 is the verified native Linux environment.

## Local deployment, rollback and release plan

Only the verified stale user Start Menu shortcut was repaired on Martin's PC.
It now targets `C:/Program Files/MattsSDKBoostingTools/MattsSDKBoostingTools.exe`.
Fresh readback matched updated SHA256
`88ab7c40509583e0e865fac5cedab3a3b06ff40dab3d99dabeccce0e501df570`.
Original backup SHA256 is
`5c0f0cf36c8cf23d9e6bce6366fbdef55c4ac521a1402534c6ba3fb484a7acd0`.
`shortcut-backup/receipt.json` names the exact U+2014 path; rollback copies
`user-start-menu.before.lnk` back to that path. No real app/game was closed,
installed or restarted, and real settings/protected lists were not modified.
Windowless fixture/helper experiments ran only against temporary test files.
Installed MSBT remains published 2.41.2; the candidate repair is not deployed.

A future repair is a patch release, normally 2.41.3, after explicit approval.
Preserve published versions, bump all lockstep metadata together, rebuild both
platforms at the release commit and retain exact receipts. The mandatory gate
also requires actual Windows and Linux/Proton BL4 evidence tied to that candidate;
there is no available Linux BL4 host here. `publication_ready` is false. Do not
bypass the verified publisher or claim headless fixtures establish live gameplay.
No tag, release, public asset replacement or merge was performed for this task.

## Authorized 2.41.3 preparation

Martin subsequently requested "release it." This authorizes the patch release;
the required dual-platform live-game gate still applies. Public latest was freshly
verified as v2.41.2. Prepared lockstep 2.41.3 metadata and explicit release notes,
preserving Android pins and all protected-list repairs. No game implementation
changed. Both platforms are being rebuilt at the release-candidate commit; prior
2.41.2-labelled candidate hashes are not 2.41.3 qualification. Publication remains
blocked by absent exact-candidate Windows/Linux-Proton live evidence, with no
Linux BL4 host available. No release tag, draft or public asset was created.

Independent release-metadata review caught the SDK __version_info__ tuple still
at 2.41.2. Corrected to (2, 41, 3); the dedicated lockstep checker now passes.
Superseded CI 43357060149 was cancelled; no pass is claimed for that run.

Final 2.41.3 packaging/native desktop verification PASS: CI43357300583 at
`dbedd839a2fd64e1a978fe311cfd96a55be87d2c`. Both platform jobs and aggregate
package gate passed. All four downloaded artifacts independently match their
size/SHA256 receipts. See [2.41.3 verification](../releases/VERIFICATION_v2.41.3.txt).
Candidate directory: `C:/src/MSBT-Workspace/product/local/updater-repair/candidate-v2.41.3`.
Evidence: `../evidence/release-v2.41.3` relative to the isolated checkout.
The required publisher dry run returned exit1, `Publication stopped: win32:
native live evidence required`. The honest live-qualification file records both
platforms NOT_TESTED. Linux BL4/Proton remains unavailable; fresh WSL inventory
confirms WSL is not installed. No publication, draft, tag, real application/game
restart or user-data change occurred during this release-preparation turn.
Latest public release remains v2.41.2; exact public2.41.3 links cannot be verified
because that release does not exist. User release authorization is recorded;
remaining work requires actual platform/game qualification, not another generic
release-permission question.
