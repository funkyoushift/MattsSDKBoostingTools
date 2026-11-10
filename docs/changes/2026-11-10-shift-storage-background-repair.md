# SHiFT storage and background repair — 2026-11-10

Martin requested fixing settings persistence and completing/testing Play while
accepting. No release/version change or real social transaction is authorized.
Azalea's supplied pair is rejected; its exact review is in
`C:/src/MSBT-Workspace/product/local/reviews/azalea-20261110/REVIEW.txt`.

Work is isolated on `codex/shift-storage-repair-20261110` at
`C:/src/MSBT-Workspace/product/local/shift-storage-repair/product`, based on the
verified v2.41.1 integration commit `b83d65b6`. The primary dirty source and its
unreleased mobile-security work remain untouched. This candidate does not merge
unrelated primary/release differences.

## Evidence and changes

Before diagnostic deployment, the installed SDK/PAK/companion matched the released Windows portable. Tobgun1's
files/runtime are not available; matching visible SemVer is insufficient, and his
later screenshot contains an error sentence absent from Azalea's proposed PAK.
No specific installation mistake on his PC is claimed.

Confirmed source defects repaired:

- `repair_azalea_controller.py`: missing/invalid protected storage returned before
  processing background commands, silently dropping first-use desktop Start/Stop.
  Commands now dispatch independently, while destructive protection guards remain.
- A Save click during a settings GET was rejected. An explicit Save now cancels
  that read, retains the verified service identity and ignores late callbacks.
  Polls prefer the connected port. The new page checks the companion integration
  revision and reports a mismatched pair explicitly.
- `shift_storage_companion.py`: first creation uses same-directory, no-overwrite
  `os.rename` on Windows rather than requiring a hard link. Other platforms retain
  no-overwrite linking. Temporary writes, late-file refusal, corrupt-file
  preservation, review intent and update digest checks remain. Failed publication
  with no destination remains retryable. The same-game-process access check is
  unchanged; one companion owns settings and background control.
- `shift_background.js`: foreground Stop acknowledges desktop intent even without
  a native lease. Failed background entry stops acceptance only when that attempt
  started it; independent manual acceptance survives. Bridge loss restores the
  page and reports an error. The companion reports pending/expired commands and
  the desktop displays those states instead of implying they were applied.
- `pak_install.js`, `main.js`, `renderer.js`: Updates now checks exact PAK and
  companion hashes, enable state and additional numbered/nested PAK copies.
  Conflicts are reported, never deleted. The private protected-list JSON is not
  read by this inventory. Full bundled installation already restores the pair.

New tests cover first-write interruption/publication failure, late destination,
failed edit, first-use commands, Save/read race, stale callbacks, companion
revision, foreground stop acknowledgement, owned-start rollback, repeated
start/show cycles and installation mismatch/conflict reporting.

## Validation checkpoint

- Python syntax passed before archive construction; 192 PAK payloads round-trip.
- 44 storage/background HTTP tests passed outside the network-restricted sandbox,
  including same-process success and child-process rejection with a valid token.
- Initial combined Python run: 47 passed, 38 socket operations denied by Windows
  error 10013. The corrected permitted HTTP run passed; no game HTTP calls were
  made by these tests. Other focused native-lifecycle/startup checks passed in the
  first run. Final complete suite: **85 passed in 23.93 seconds**, receipt
  `../final-python-tests.txt` relative to this worktree. After adding the real HTTP
  acknowledgement-route test, its focused module passed **21 tests** (including
  inherited storage cases), receipt `../final-storage-repair-tests.txt`. Counts
  overlap; they are not 106 distinct tests.
- 25 dashboard automation cases, protection/transport regressions, background
  lifecycle checks including 20 repeat cycles, AFK ownership checks and the new
  two integration-health/Updates guidance tests passed. Steam/Epic SDK target
  selection, ambiguity, missing target and loaded-hash regression checks passed.
- Existing installer fault injection passed backup/private-file preservation,
  rollback at every write for fresh and hard-linked installs, and cleanup errors.
- Hidden Electron: 13 panel DOM checks and five protected-list setup/save checks
  passed. This is not native Cohtml proof.

The new native diagnostic retains real background/desktop routing, blocks the
identified social mutation routes in both dashboard and notification contexts,
uses isolated browser keys and `BL4_ShiftManagement_Settings_MSBTRepair20261110.json`,
and records only counters/storage state/background state. It never writes the
real protected-player JSON. Its guard has an offline mutation-blocking test.
The installed executable still matches the native adapter's pinned SHA256
`ba75f7c2874b16efb5536a5c0cc28918a03efd3e55d790d2e4db57de0c3a353a`.

## Deployment, rollback and remaining qualification

**Final cleanup status:** Following Martin's explicit instruction to close the
instance opened for this task, the Borderlands app-access call completed, normal
Alt+F4 closure succeeded, and fresh unrestricted tasklist reported no matching
game process. No force termination was used. The guarded rollback restored all
three original files; `../native-installation.json` now records
`released_pair_restored`. Independent fresh hash verification is recorded in
`../rollback-verification.json`: PAK, companion and enable file exactly match
their backups, the released main SDK hash is unchanged, and the real protected
settings remain absent as before the test. No diagnostic is left installed.

The first post-close rollback stopped without writes because the SDK had
normalized its enable JSON back to the exact original backup bytes. After
verifying that hash, the guard was narrowly extended to accept either the exact
diagnostic enable hash or exact original enable hash. PAK/companion checks stayed
strict. The next rollback and independent verification succeeded.

No cleanup approval remains necessary. Earlier Borderlands/steamwebhelper test
access requests are obsolete; no tool to cancel those parent approval cards was
available here. Do not reopen the game while Martin is away without checking
with him first. Repair source and offline evidence remain ready; native
qualification is still unfinished. The paragraphs below preserve deployment
and blocker history, superseded by this cleanup receipt.

The diagnostic pair was installed with verified backups using the approved local
deployment operation. The exact receipt is `../native-installation.json` and
backups are in `../native-backup/`. The released main SDK remained unchanged at
SHA256 `643f07653c3d2eb1ac1042018ea77fb0736bb074661aeaf600b91bc898fa5962`;
the real protected-settings JSON remained absent. The desktop app was not
replaced. Installation/restore is restricted to PAK, companion and enable file
with exact hashes, game-closed checks and in-place writes preserving hard links.
Rollback: from the parent task folder run `python -B install_diagnostic.py restore`
with permitted game-directory writes after confirming BL4 is closed. It validates
current diagnostic and backup bytes, restores the three original files, and
archives/removes only the isolated diagnostic settings file if one exists.
No production deployment, version bump or publication has occurred.

Exact SHA256 values (PAK / companion):

- Functional candidate: `995bcbc7c09fe920315477bfdc39db4f0b43afb0600ab8b5d6e011e5f65fbdfa`
  / `a7d64ca76946b27636757b1843a6dbab311364a3ce6e857c4038524d95a951e9`.
- Installed diagnostic: `37b50d3f7f65c41793e70a28b6a1f34575eac085ffc243c81e954cfb3a4c1ce7`
  / `0b5cc716541f87a5d3fcd664e857d521665a4bb94e06b60e97b45a645333608a`.
- Original released pair: `728165a795f7543b9a109604b60a8ae54f70de2c6cf92f4a37c231982a5e617f`
  / `9fc2a823605f1035cf3df8b53ff20b753b2db8798d51b15fbe6fb00f941c8c02`.

Native computer-use approval is **pending**, not denied. The Steam launch request
did not expose a targetable Borderlands window; the follow-up app snapshot did
not succeed. The parent explicitly instructed keeping game interaction pending.
The sandbox Get-Process check showed no process, but this was not reliable:
an approved rollback attempt's unrestricted game-closed guard detected a running
game and stopped **before all writes**. An unrestricted read-only tasklist check
then confirmed `Borderlands4.exe`, PID **44728**. The diagnostic therefore remains
installed, and rollback is pending until the game can be closed normally. No
diagnostic event log exists at this checkpoint. A sandbox tasklist attempt also
returned a credential error; it did not prove game state. Do not infer a closed
game from restricted process inventory. No native acceptance result is claimed.
The pending approvals are Borderlands 4 and
steamwebhelper computer use; this is not an automatic-review rejection.

Native first Save/edit/restart reload, desktop and in-game Start/Stop, repeated
toggles, sustained polling/background lifetime, menu/travel cleanup and physical
keyboard/mouse/gamepad controls still require that approval and qualification.
Physical gamepad availability is unconfirmed. No current live
friend acceptance/decline, guest-save or Linux/Epic result is claimed. Previous
v2.41.1 Steam controls evidence is historical, not proof of this candidate.
