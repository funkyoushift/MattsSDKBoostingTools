# Readable expanded cards and hover previews

Local desktop update after v2.29.1. Version remains unchanged; no publication.
Matt approved a clearly labeled expanded layout for overflowing modded cards,
with compact layout retained, then requested cropped thumbnails and zoomable
hover previews.

## Evidence and cause

The exact cached native Draupner widget contains nine primary entries: numeric
stats and four enhancement descriptions. The native HTML binds primary values
as plain text, while its CSS requests `coh-font-fit-mode: shrink`. Chromium does
not implement that property. Nine fixed-width cells also exceed the card width.
The earlier independent game comparison records BL4 shrinking similar bracketed
text; see `docs/native-cards/NATIVE_WIDGET_FIELD_BINDINGS.md`.

Steam build 25372571; executable SHA256
`9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0`.
Extracted item_card.html SHA256
`34232b1538d0199ac27e1c2ce3a7e2bd6509f190dc9ed778b6e4b3260649846a`;
item_card.css SHA256
`00ad72dce1288d3bc83d765f143f9724b82d4b372ec89dcde39355e0c5710b59`.
Relevant definitions: HTML primary value binding around line 248; CSS
`.item_card_primary_stat_value` around 208 and
`.item_card_primary_stat_cntr` around 1116. Original files remain unchanged.

## Behavior

- `native_card_adapter.js` measures actual overflow after fonts load. In automatic
  mode only affected primary, skill, or secondary sections use readable rows.
  Every original row, value, order and duplicate is retained. Escaped values use
  the extracted markup resolver. This is explicitly MSBT presentation, not a
  recovered native font-fit rule; the image says “Expanded layout · game data”.
- Compact mode leaves the extracted template bindings intact. The shared card
  loader provides a switch and retains both images. Switching does not rebuild
  an item. Session mismatches are rejected.
- `item_card_preview.js` supplies cropped thumbnails, a larger top-layer hover
  preview, scrolling, 100–200% zoom, Escape/Close, focus restoration and a View
  card button for keyboard/touch. Recycled cards dismiss their stale previews.
  It uses the already loaded image and does not generate another card.
- Shared views cover inventory, catalogs, saved/community folders and serial
  previews. Uploaded/GZO images retain priority and receive the same hover UI.
- `native_preview_client.js` can redraw older validated cached widget data after
  a presentation revision even offline or when the solo guard blocks generation.
  A lazy widget-file index avoids repeated scans and concurrent requests share
  capture. Old-session data stays labeled as a previous-session snapshot.

## Validation

- Read-only local cache audit: 457 unique widget records; 45 representative shapes
  across 12 item types. Six compact layouts had measured overflow; zero automatic
  layouts did after the change. This is sampled layout evidence, not all-item
  or equipped-context parity.
- `npm run test:card-layout`: 16 Node cache/identity/priority tests plus real
  Electron expanded-layout, hover/zoom and shared-view tests passed. Includes
  preserved nine/eleven primary rows and twelve skill rows, normal-card retention,
  compact switching, hostile text escaping, cropped/full views, narrow viewport,
  focus restoration, stale-view cleanup and no regeneration on hover/zoom.
- Existing native rendering and Community Folder UI tests passed, including
  pagination, consent/import, failed-card recovery and responsive layouts.
- The installed UI exposed inherited `pointer-events: none` on inventory card
  visuals. Explicitly restored pointer input on the thumbnail and its two controls;
  regression now uses `invMakeCard` and verifies browser hit testing, not only
  synthetic clicks on a generic container. Existing inventory selection tests
  also pass, preserving Ctrl/Shift selection, tile identity, focus and scroll.
- Packaged graph: 48 dependencies; source/artifact comparison: 3,243 files;
  packaged startup smoke passed. Local build excluded tests and fixtures.

## Deployment and remaining work

Final local build under `output/card-layout/build-final`. Compared 1,447 installed payload
files: only app.asar and the main executable (ASAR integrity) differ. The previous
pair is backed up under `output/card-layout/installed-backup`; both installed
replacement hashes match the tested build. Desktop restarted; game/SDK untouched.
Bridge remained healthy and AFK enabled, waiting for guests after restart.
Final installed UI check opened the equipped sniper's full-size zoom preview
using View card without selecting the inventory tile. Cropped thumbnails and
controls were visible in the real installed profile. Closed the preview and
left Inventory open. The heavily modded layout assertions use the exact cached
widget fixtures and offline Electron captures, not a new game screenshot.
Restore that pair with MSBT closed for rollback; caches preserve the old records.

Still unresolved: exact Cohtml compact font-fit parity, equipped firmware/loadout
and comparison context, new native generation with guests, and wider lifetime
validation. This change does not alter native calculation/selection/naming rules,
does not resume NCS submissions and does not add a website generation service.
Private audit data and screenshots are under `output/card-layout`.
