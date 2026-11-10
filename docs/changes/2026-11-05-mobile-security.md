# Mobile file authority and LAN token authentication — 2026-11-05

## Scope and ownership

Martin requested incorporating the security repairs into ongoing product updates,
with deployment separate. The SHiFT task confirmed the active source as
`C:/src/MSBT-Workspace/product`, HEAD `b0d31201bd5613e387969c12244d43e43976ed4b`,
and reserved mobile/preference/authentication files for this security work.
Its acknowledgment is in
`C:/Users/mwenn/Documents/Codex/2026-11-05/task-4/MSBT-OWNER-ACKNOWLEDGMENT.txt`.
Existing dirty work was preserved. No SHiFT source, installed package, running
game, real save, version, release artifact or live service was changed.

## Evidence and root causes

- Paired-mobile desktop RPC could call `saveMattEditorPrefs` to change paths used
  by `mobileDesktopFiles` as trusted roots. The original offline reproduction
  denied an outside synthetic file, changed `lastSaveFolder` through the real RPC
  and preference store, then read the same file successfully. Overwrite used that
  same root guard. Account IDs also contributed a path to trusted roots.
- `mobile_lan.is_allowed` accepted a remembered IP without proving its token.
  `external_bridge._authorized_request` then called `remember_phone` with the
  offered token. `remember_phone` matched by IP as well as token, allowing a reused
  address to select another phone's record. Even a legitimately paired second
  phone could select the wrong record when sharing that address.
- Initial discovery looked in the Electron gateway and did not find the second
  path. It is in the SDK LAN module, present in this active checkout. The audited
  upstream commit's absence from local Git history did not mean the code was absent.

## Changes

- `electron_poc/matt_editor_prefs_store.js`: added `writeMobilePrefs`. PC path
  preferences, including aliases, may be echoed unchanged but cannot be changed
  by mobile callers. All supplied path fields are checked before any write.
  Phones can still set/clear valid Steam/Epic IDs. Unknown fields and metadata
  never reach the PC preference write. Desktop preference behavior is unchanged.
- `electron_poc/main.js`: routes mobile preference writes through that policy;
  removes account ID from mobile trusted-root construction; checks the reopen
  path for mobile callers; uses the checked canonical target for mobile overwrite.
  Desktop picker/explicit desktop folder selection retains its existing behavior.
- `mod_extracted/MattsSDKBoostingTools/mobile_lan.py`: LAN authorization requires
  an enrolled token, using constant-time byte comparison. IP is routing/display
  metadata, never authentication or credential-record identity. Refresh matches
  token only. Explicit enrollment can add a distinct phone at the same address.
- `electron_poc/test_mobile_file_authority.js`: real RPC/store/current main.js
  handler tests with temporary synthetic files, temporary home and canceled dialogs.
- `tools/tests/test_mobile_lan.py`: replaces the obsolete IP-only acceptance
  expectation and adds takeover, missing/wrong token, shared-IP, revocation,
  persistence and legacy re-enrollment regressions using the actual bridge auth.

## Validation

All security checks were offline, with synthetic state and no live listener.

- `node --test electron_poc/test_mobile_file_authority.js`: 7 tests pass, including
  path aliases/atomic rejection, valid ID updates, permitted reads/reopen/overwrite,
  traversal/junction escape rejection, account-root isolation and desktop selection.
- Existing `test_mobile_desktop_files.js`, `test_mobile_desktop_api.js` and
  `test_matt_editor_prefs_store.js` pass. Main/store JavaScript syntax checks pass.
- `python -B -m pytest tools/tests/test_mobile_lan.py tools/tests/test_mobile_lan_discovery.py tools/tests/test_quick_menu_no_blimgui.py -q -p no:cacheprovider`:
  31 passed. The actual invocation redirected pytest temporary files into the task
  workspace and disabled bytecode writes. Python AST syntax checks also passed.
- The original independent `verify-security-findings.cjs --expect-fixed` now
  passes both MSBT file-authority and Subtronics quantity expectations.
- Scoped `git diff --check` passes. The current Android source sends
  `X-MSBT-Device` for authenticated routes, so normal token-based pairing remains
  supported across IP changes.
- Initial junction tests hit sandbox `EPERM`; rerunning the two synthetic-file
  tests with approved escalation passed. No runtime or test assertion was weakened.

## Compatibility, release and rollback

Legacy IP-only entries require a fresh pairing scan. Existing enrolled tokens
remain valid across address changes. Phone-local remembered files are handled by
the existing phone shim; PC paths remain desktop-controlled. Already persisted
desktop preference paths are retained; this change does not establish their past
provenance or perform an incident-response cleanup.

No app restart, package build/install, release, tag, push or deployment occurred.
Physical phone/gameplay validation and shipping-artifact verification remain for
the normal update process. No claim of exploited accounts or customer data loss.

Pre-change source bytes and a security-only patch are kept in
`C:/Users/mwenn/Documents/Codex/2026-11-05/task-4`. Roll back only this change's
hunks after checking subsequent edits. Do not restore the whole backed-up dirty
`main.js` or overwrite another worker's newer changes.
