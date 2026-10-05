# Large native inventory trial

Scope: local-native-cards worktree, opt-in v2.27.0 trial; no public release or SDK installation change.

## Evidence and root causes

The user expanded the backpack. The saved and live inventory contains 865 backpack slots and 9 equipped slots, 818 exact distinct serials. The native renderer submitted every metadata request concurrently into a 512-request guard. The prior 70-slot trial could not expose that mismatch. Some native-referenced artwork was absent from the bundled assets. Missing images caused the complete card capture to fail. Native output also contains literal `missingicon` references for some modded class mods; these cannot be mapped to verified artwork. One offscreen capture returned Chromium UnknownVizError during the full 818-item pass.

## Changes

- native_inventory_preview.js and renderer.js: eight pending metadata requests maximum; exact serial deduplication; preserve slots/order/duplicates; progress and final failure count. Queue guard remains intact. renderer.html loads the helper.
- native_card_ui/manifest.json: 171 additional verified installed-game PNGs, including Cowbell skills/markup/portraits and one decoded Bofor texture. Game build 25372571. Exact source paths and SHA-256 hashes are in output/native-card-large-inventory/imported-artwork.json; decoded texture receipt records its asset/package and mapping hash. The attempted missing_icon extraction failed because that package does not exist; no replacement artwork was fabricated.
- native_card_adapter.js, native_widget_card_model.js, native_card_capture.js: missing artwork becomes explicit image warnings, with intact native text/stats. Structural or unresolved card-data failures remain errors. Strict adapter validation is still the default; image capture opts into incomplete-artwork handling. The app visibly labels incomplete artwork. The longest native name in this inventory has 11,371 characters and yields 11,360 CSS pixels of height. At 1.5x display scaling this needs 17,040 physical pixels: a single Chromium surface returned UnknownVizError. A fresh-window retry alone did not fix it. Capture now uses 2,048-CSS-pixel strips and stitches their original pixels; the exact same long card succeeds at 819 by 17,040 pixels in a standalone Electron test. One bounded retry still handles transient UnknownVizError, without requesting new native data.
- native_preview_client.js: cache validated native data independently of image revision. Layout changes and capture retries reuse game data. Metadata-only reads use the lightweight widget cache and omit PNG payloads from IPC. Session, exact serial and schema isolation remain; artwork changes still invalidate images. Existing trial records were migrated only after checking identical native payloads for matching session/serial.

## Validation

13 focused JavaScript tests passed, including 874 distinct slots, bounded concurrency, duplicates, case separation, error recovery, renderer-only cache invalidation, session changes, and incomplete-artwork reporting. JavaScript syntax checks passed. No Python source changed.

Live: 874/874 inventory slots resolved native metadata after the update. First complete image pass: 813/818 succeeded; four unmapped images and one UnknownVizError. Second pass: 817/818 succeeded, exposing the GPU surface size limit. Final tiled pass: 818/818 distinct images succeeded in 135.19 seconds; 10 images explicitly warn about unavailable native artwork (13 warning occurrences). The second request pass reused 818/818 images in 1,464 ms. Native builds stayed at 883 throughout final capture, repeat reads and the final app restart. All 2,953 image-cache records retained identical contents and timestamps across the final restart. Exact inventory multisets remained 9 equipped and 865 backpack. The debug listener was closed. These timings are observed on this machine, not a performance guarantee. Artifacts are in output/native-card-large-inventory/.

## Deployment and rollback

Restarted only the isolated local trial with its existing profile. Public app remains separate. Temporary localhost diagnostics were closed; the final trial was restarted without the debug port. No NCS API requests, inventory mutations, game restart, version bump, package or publication performed. Undo this entry's changes to roll back; source/native cache remains available. Preserve other pre-existing dirty worktree changes.

## Remaining boundaries

These are transport/coverage fixes, not proof of perfect BL4 visual parity. Native font fitting in Cohtml, oversized class-mod layout, equipped firmware context, cross-game-session identity, multiplayer lifetime coverage and integration with the newer community/GZO branch remain unfinished. Screenshots do not establish native arithmetic or selection rules.
