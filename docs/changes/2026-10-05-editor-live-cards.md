# Live editor cards and multiplayer generation

Matt authorized removing the solo-session precaution and publishing this work,
then requested a live card in the item editor before publication.

The existing manual editor preview tried to read a cross-origin frame directly.
The hosted adapter now sends only generated output from the active editor tab.
It observes direct textarea value updates as well as text output; hidden tabs,
input serials and an in-progress item-editor serialization queue are excluded.
The desktop validates the exact frame and origin, validates serials and renders
one chosen item after 650 ms of settled output. At most one editor render is
active; newer output clears obsolete images and supersedes queued work. The
shared loader retains uploaded/GZO/cache/native priority, zoom and expanded
layouts. Pausing automatic updates, manual refresh and selecting one of several
outputs are supported. Hidden editor pages do not start renders. No delivery or
inventory mutation is part of previewing an item.

`native_sdk_card_probe.run` no longer rejects a party with guests. The prior
research-only multiplayer flag was removed. An active session, game-thread
identity, supported native build/function hashes, bounds checks and cleanup are
still required. Player count remains in evidence reports. Older installed SDKs
that return the solo error now get an update/restart message; cached-image
compatibility with those SDKs is retained.

This changes our application policy, not recovered game arithmetic. Multiplayer
generation has not been validated live; Matt will report runtime issues. Card
output is standalone, not equipped-loadout/comparison parity. Six community
serials previously failed native construction/export, and seven exported cards
still contain explicitly unresolved input prompts. Language switching and
equipped firmware effect calculations are outside this release's scope.

Validation so far: 11 Python probe/cleanup checks, four no-BLImGui checks, 13
preview-cache tests, real Electron expanded-card/glyph tests, editor source and
full-page catalog checks. The live-editor browser test uses the real adapter in
a cross-origin frame and verifies coalescing, stale-result rejection, one active
render, bulk choice, pause/manual refresh, hidden-tab behavior and origin checks.
Package/install/public-release verification is recorded below when completed.

## v2.30.0 packaged verification

The final installer/portable build passed the complete source-check script,
31 persistent-installer checks, 48 runtime dependency checks, 3,252 source-to-package
file comparisons, packaged startup and updater checks. All 3,261 bundled GZO rows
retain image URLs. SDK archive probe/widget/version files match source bytes.

An isolated packaged app loaded the actual bundled editor over its separate
localhost frame. Its normal Parse Code action loaded Vindictive Gatherer, then
Accelerated Nadir Clarity. The live panel followed each item, displayed the
expected name/image, and preserved both exact generated serials. Repeating after
restarting the packaged app reused cached cards. A visual check corrected the
automatic-update checkbox to the standard compact control before the final build.
The first rebuild encountered locked files in the test app; closing only that
isolated app allowed the successful rebuild. Game and regular app were untouched.

Private evidence: `output/release-230-checks/editor-live.json`, `editor-live.png`,
`asset-hashes.json`, and `output/card-followup/release-230-build-final.log`.
Android 1.5.0 APKs are byte-identical to v2.29.1's published assets.

## Publication and local installation

Published stable v2.30.0 at tag commit `e5291962e70985f52642c2eeb56f82aa7a8e5d20`.
Release CI and Pages completed successfully; the reviewed local-build policy
skipped a duplicate CI build. All 11 public asset sizes and GitHub SHA256 digests
match local files. The downloaded public `latest.json` matches the packaged and
installed manifest. The legacy Windows PowerShell publisher could not parse its
UTF-8 punctuation; PowerShell 7 passed preflight and published successfully.

Installed the verified portable payload through the normal installer Engine,
retaining the previous desktop for rollback. Installed executable, ASAR, bundled
SDK and update-manifest hashes match the package. MSBT was restarted and its main
window verified. The game was not restarted or its loaded SDK replaced while
guests were present. Update the game mod and restart BL4 to activate the new
multiplayer policy. Live multiplayer generation remains unverified as agreed.

Private publication/install receipts: `output/release-230-checks/`.
