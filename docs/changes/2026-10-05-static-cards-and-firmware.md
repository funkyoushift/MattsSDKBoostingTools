# Firmware identity and static community cards

Scope clarified by Matt: show each item's firmware identity; equipped firmware
bonuses/counts and language switching are not requirements. Preserve GZO names.
Generate website images locally and serve stored screenshots, with cropped,
zoomable previews. No version bump or public app release in this work.

## Firmware and inline input glyphs

The expanded local cache audit found 2,868 unique widgets, 1,309 with visible
firmware, and 24 firmware identities. None of those visible firmware records had
a blank identity/name. Real Electron rendering checks one actual cached card per
firmware identity for matching text, a visible name and a mapped icon. All 24
passed after the input-glyph correction. This verifies native output transport
and rendering; it is not an independent equipped-loadout simulation.

The audit found Booming Potent Satchel Charge / Risky Boots failing with
`glyphElem.constructor.observedAttributes is not iterable`. Its native description
includes `[glyph]action_gadget[/glyph]`. Extracted `markup_manager.js:324` assumes
the game's `gbx-glyph` component exists. The standalone browser lacked that class.

Read-only Steam build 25372571 extraction, receipt `output/glyph-source-20261005/`:
- `OakGame/Content/uiresources/_shared/js/glyph_element.js:8`, SHA256
  `12146727212df2eb4f250e405d3f3c446d3746371928b9b7a544c3ff0ae69d08`:
  the observed-attribute contract.
- `glyph_manager.js:117-125,230-232`, SHA256
  `8114355ec0d56eb4b7415a30fb3486e6b99b9a576a9ee286744e72e9672317f5`:
  input mappings arrive from engine events and resolve by action name.
- Executable identity remains the hash recorded in NATIVE_WIDGET_FIELD_BINDINGS.

`native_card_adapter.js` now supplies a clearly unresolved static input prompt,
e.g. `[input: action_gadget]`, retaining the game's exact action identifier. It
reports `Input glyph unavailable` and does not invent a key or controller button.
This is MSBT presentation, not recovered input-mapping behavior. Original game
templates/data remain unchanged. The real cached grenade is a regression fixture.

GZO lookup no longer emits saved-title replacement events. Native card names still
replace user labels on non-GZO bookmarks/community items; original labels remain
in tooltips/search/storage. GZO metadata behavior outside that change is retained.
An unavailable GZO screenshot can fall back to a native image without replacing
the GZO title; the shared-view browser regression covers that error path.

## Website export and UI

`tools/export_community_cards.cjs` reads approved public folders, verifies their
canonical digests, and exports only those exact serials. It skips matching GZO
images. Optional `--fill` builds missing widget data one at a time through the
existing game-thread service and caches it in the desktop profile. No NCS calls,
inventory insertions, language changes, or guest-guard bypass. Serial-construction
and string-bound failures have a durable negative ledger; other errors stop new
generation. Existing widgets still render after a stop.

Static output uses exact case-sensitive serial SHA256 keys and content-addressed
PNG files locally. Website staging converts them to lossless WebP, verifying every
decoded image against the original RGBA pixels. It preserves levels/order/duplicates
in source folders. Rendering
resumes from verified image/widget/renderer hashes and checkpoints the manifest.
Only images/index belong in the website; audit/profile/receipt files stay local.
Refresh the public allowlist each export. Images are reusable public snapshots;
there is no automatic live website generation or background upload service.

Website checkout: `C:/Users/mwenn/Documents/GitHub/funkyoushift.github.io`.
`community/media.js` uses uploaded screenshot > GZO > generated snapshot. Only
generated snapshots update non-GZO headings. Shared `item_card_preview.js` gives
cropping, hover, touch/keyboard View card, scrolling and 100-200% zoom. The entire
website path uses static reads and does not need a game or renderer API.

## Multiplayer

The solo guard is our explicit Python policy, not an established engine rule.
The wrapper uses detached identities/models, an initialized default owner and no
player inventory insertion. That is useful source evidence but does not prove
every native callee is independent of party state. A research-only
`allow_multiplayer_trial` argument now permits a bounded test while retaining
thread/build/function hashes, allocation guards and cleanup. It requires a new
evidence file. Production `native_preview_service` never enables it.

Mock tests verify default guest rejection and cleanup with the explicit trial.
No live guest trial has run; the installed SDK and production guard are unchanged.
Next trial must compare exact native widget output and host/guest inventory
multisets before/after, with no active delivery, and verify clean native teardown.

## Validation and local deployment

JavaScript syntax, native expanded-card/glyph regression, shared-card naming,
community folder UI, static website priority/identity/zoom tests passed. Python
syntax checks, 11 probe control-flow tests and four no-BLImGui startup/bridge tests
passed. These do not substitute for a live guest trial.

Desktop package source check: 3,251 files matched. Local desktop EXE/ASAR pair was
backed up under `output/card-followup/installed-backup`, replaced with verified
hashes and restarted. Game and installed SDK were not replaced. Live bridge and
AFK remained enabled. Desktop version is still 2.29.1; no release/tag/upload.

Export totals, failures and remaining serial hashes are recorded separately in
`output/community-card-export/receipt.json` and `generation-failures.json`.

## Completed public-folder batch

The 86 approved public folders contain 2,843 unique exact serials: 2,831 generated
cards, six GZO image matches, and six unresolved serials (four native construction
failures and two widget-string bounds failures). The batch built 2,391 new native
widgets without inserting inventory items. Known failures are not repeatedly sent.

Eight grenade manufacturer icons were checked against original installed-game
PNGs; seven missing files were added and the existing Jakobs file verified.
`electron_poc/native_card_ui/supplemental-manifest.json` records build, source paths
and hashes. The renderer revision now includes this manifest. A repair pass
rerendered affected cards; no missing-image warnings remain. Seven cards still
show the explicit unresolved `action_gadget` input prompt described above.

Website staging contains 2,738 unique images, 429,686,042 bytes, indexed for 2,831
serials. Every staged image's content hash and manifest reference was verified;
there are no extra files. The staged WebP browser test passed screenshot priority,
GZO name preservation, exact serial identity, full view and 200% zoom. Website
validation passed 21 HTML pages and both JavaScript and Python client checks.

Published website commit `e44ff601c0f434e9a6e7a13f2d198d09bdfb7443` passed
GitHub validation and Pages deployment. Verified the public community page's new
preview script, final GZO title guard, all 2,831 live manifest entries with an
exact manifest hash match, and a sampled image's content hash. Receipt:
`output/card-followup/website-live-verification.json`. No app release was created.
