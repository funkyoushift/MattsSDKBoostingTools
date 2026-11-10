# Matt's SDK Boosting Tools v2.41.2

Local release candidate; not published.

- Fix SHiFT first-use settings saves, read/save races and desktop Start/Stop
  delivery before protected-player storage has been initialized.
- Keep first creation and edits atomic, flush temporary data before publication,
  preserve protected players on failed writes and reject stale storage ownership.
- Improve Play while accepting cleanup and desktop command acknowledgements.
- Check the bundled SHiFT PAK, companion, enable state and conflicting PAK copies
  independently of visible version numbers.
- Require enrolled device tokens for LAN access. Remembered IP addresses no
  longer authorize requests or select a different phone's pairing record.
- Keep PC file-authority preferences desktop-controlled; paired phones may update
  valid account IDs but cannot expand trusted desktop file roots.

Existing token pairings remain valid when addresses change. Legacy IP-only
entries require pairing again. Update the desktop app and complete bundled game
integration together, then restart Borderlands 4 before testing live actions.

Release qualification is recorded separately in
`docs/changes/2026-11-10-v2412-release-candidate.md`. A release must not be described
as fully qualified until its outstanding native/platform checks are resolved.
