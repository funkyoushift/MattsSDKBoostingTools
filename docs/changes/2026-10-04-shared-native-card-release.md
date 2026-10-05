# Shared desktop item cards and combined release candidate

User-authorized combined release from `codex/concurrent-delivery-methods` f3f100d, integrating its AFK/manual delivery and updater changes with the local native-card trial. Isolated worktree: `native-cards-release/working`. Version 2.29.0; local release validation completed before publication.

## Problem and behavior

The prior native preview required a temporary bridge patch and only Inventory used it. Community Folders explicitly stopped at “No screenshot available”; saved cards depended on the older heuristic decoder identifying the item first. Inventory refresh submitted metadata for every slot even when their cards were hidden.

- Package the detached native service with relative imports. Only the registered SDK tick hook establishes its game-thread identity. Backend actions route preview/status without changing delivery targets or cancelling delivery queues. Exact Steam build/function hash gates and the no-guests construction guard remain.
- Shared lazy desktop cards prefer verified uploaded screenshots, then GZO exact/equivalent encoded serial images, then cached/native game cards. Original serials are never replaced. Scalar/list encoding equivalence preserves header/level, part order, duplicates and bare parts; it is not an item-name match.
- Community Folder previews, imported folders, saved cards, catalogs, Inventory and GZO submission previews use the shared loader. Delivery inputs, serial tools, validators, AFK selected/guaranteed item lists and the embedded editor expose expandable card views. Lists render in groups and only visible cards request images.
- Eight active preview jobs maximum; duplicate native requests share work. Native widget data and image revisions cache separately. Old-session cached images can be viewed offline with an explicit label; a connected game uses its own session. No NCS API calls or API key are part of this feature.
- Image loading timeouts and obsolete-view guards prevent stalled or changed views from blocking later cards. Failed screenshots fall through to the next source. Long cards scroll within folder tiles; whole screenshot capture retains the trial's tiled native pixels.
- Fresh startup exposed a pre-existing updater identity-order bug: `runtime_identity` imported before `__version__` was set. Version initialization now precedes imports, with a regression test and the version tuple aligned.

## Evidence and boundaries

Steam 25372571 executable SHA256 `9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0`. The SDK source contains exact native function RVAs/span hashes; historical recovered-code and live trial receipts are documented in `docs/native-cards/`. Extracted UI files and textures retain paths/hashes in `electron_poc/native_card_ui/manifest.json`. No inferred arithmetic or naming rules from the older offline renderer were added to the native path.

This is standalone card output, not equipped-loadout/comparison parity. New native generation remains limited to the supported solo game context. Missing artwork is labeled. Chromium/Cohtml font-fit differences, extreme modded skill layouts, multiplayer generation and broad lifetime safety remain unresolved. Historical 818/818 image coverage is a trial result, not proof of perfect visual parity or every possible item.

## Validation

- Focused native cache, identity and priority tests pass, including duplicate demand, case/level distinctions, renderer-only cache invalidation, offline snapshots and changed sessions. The actual serial decoder test covers firmware, scalar/list equivalence, header changes, ordering and duplicates.
- Real Electron shared-view test passes for uploaded/GZO/native priority, missing Community images, mismatched screenshot hashes, stale responses and serial-menu coverage. Community browse/search/pagination/import/consent/selection tests and responsive layouts pass.
- Native render/capture and GZO submission UI tests pass. Concurrent delivery/AFK progress tests pass. 38 AFK/runtime tests, nine native guard/cleanup tests, and startup/no-BLImGui checks pass. These are offline tests, not new guest-save evidence.
- Final installer/portable build passed the full source check, 48 packaged runtime dependency checks and 3,242 packaged asset comparisons. All 3,261 catalog rows retain image URLs. The initial audit caught Python bytecode caches; explicit packaging exclusions fixed the mismatch before the successful build. All 31 persistent-installer checks passed.
- Live normal startup (without a research monkeypatch) enabled the packaged service. The final source, embedded, installed and loaded SDK all match SHA256 `a5f1467c5f052addfdd0aa27218408af887e08dc69822fc0f8ec707781709372`, and the game reports 2.29.0 with BLImGui unavailable. Exact serial multisets for nine equipped and 865 backpack slots are unchanged after restarts and previews.
- The actual packaged app in an isolated profile matched 503 of 818 unique inventory serials to GZO. A missing item produced an 819x897 native card. GZO and native images both populated the shared Community Folder view and were visually inspected there. This injected test view did not publish or modify remote folders.
- Packaged close/reopen preserved the cached image and returned identical pixels. Game-side native builds remained at one throughout the packaged repeat/restart checks. Private receipts and screenshots are under `output/native-release-checks/` and are not release assets.
- Android source and APK remain unchanged at 1.5.0; both APK filenames match the prior public asset digest. No new Android device test is claimed.

## Deployment and rollback

The game was restarted only after both AFK guests had left, using prior user authorization. AFK was paused; its exact prior configuration and inventory are saved privately under `output/native-release-checks/`. The original Steam SDK archive is backed up there. The final SDK is installed and loaded locally. AFK was restored after testing, with every saved configuration field verified equal; deliveries were not replayed. Restore the original archive only with the game closed if rollback is needed. Generated cards in this change are local desktop cache, not a new website rendering service; no website deployment is included.
