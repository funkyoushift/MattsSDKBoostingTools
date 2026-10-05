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
