# Matt's SDK Boosting Tools v2.41.2

Local release candidate; not published.

- Fix saving and reloading the SHiFT do-not-delete (protected players) list.
  First creation and later edits use atomic writes. Failed or interrupted writes
  preserve the existing list, and stale reads cannot overwrite newer edits.
- Keep the reviewed-list and matching save-acknowledgement checks before friend
  deletion. An unavailable or conflicting companion cannot falsely confirm a save.
- Suspend the background SHiFT view while a normal game menu is open, then resume
  acceptance after that menu closes. Long menu sessions no longer expire the
  resume request. Show, Stop and disconnect still cancel automatic restart.
- Display menu suspension and restart separately from confirmed active acceptance.
- Keep desktop Start/Stop, SDK companion, PAK and updater identities consistent;
  visible matching version labels alone do not establish matching loaded files.
- Retain the mobile security repairs: enrolled tokens authorize LAN access,
  shared IP addresses cannot select another phone's pairing, and paired phones
  cannot expand the desktop's trusted file paths.

Install the desktop and bundled game integration together, then restart BL4.
Existing token pairings remain valid when addresses change. Legacy IP-only
entries require pairing again. The mobile APK is unchanged.

Qualification and exact artifact hashes are recorded in
`docs/changes/2026-11-12-menu-storage-release-package.md`. Native checks on the
v12 diagnostic are distinct from validation of the final packaged integration.
No blanket gamepad, Linux/Epic, travel or final installer-upgrade claim is made.
