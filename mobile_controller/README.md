# MSBT Mobile Controller

Android companion controller for Matt's SDK Boosting Tools.

Package ID: `com.funkyoushift.msbt.mobile`

Current beta: `0.1.0-beta.13` (recommended closed beta)

## Phone download (static link)

Bookmark this on your phone — it always points at the latest closed-beta APK from CI:

https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/mobile-beta/MSBT-Mobile-Controller.apk

Prerelease page: https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/mobile-beta

Install/update over the previous beta (same package ID + signing) so bookmarks / Quick Menu / connection settings survive.

The mobile app is a **live cheat/controller companion**, not a mobile save editor.

Included controller areas:

- Home/status
- Boosting + serial sender
- BL4 Codes (filters, multi-select, delivery)
- Quick Menu (Pull From PC + tap-to-fire)
- Serial Bookmarks (desktop pull)
- Inventory browse / send
- Map Travel (maps + stations)
- Player Movement
- Dev Spawner (experimental; risk checkbox + Enable)
- Item Pools
- Connection setup / activity / feedback

Intentionally omitted:

- Matt Editor
- save/profile editing
- Legit Builder
- deep item construction/editing
- desktop installer/update administration

## Offline-first behavior

Useful without a PC connection:

- current GZO/Lootlemon/MSBT catalog snapshots are copied into the APK at build time;
- catalog search/filter/multi-select work offline;
- Serial Bookmarks persist locally;
- Movement presets persist locally;
- Quick Menu edits persist locally;
- PC connection settings persist locally.

## Live pairing (select beta)

Desktop MSBT on this branch starts a **Mobile Gateway** on LAN port `49775` that proxies to the localhost SDK bridge (`127.0.0.1:49774`). The in-game bridge is not opened to all interfaces.

1. PC: run desktop MSBT + Borderlands 4 with MSBT loaded.
2. PC: **Activity → Mobile Gateway** — show the QR (or note LAN IP + pairing code).
3. Phone: **More → Connection Settings** → **Scan QR to pair** (manual entry still works) → Connect.
4. Live Boost / serial / rarity / movement Apply unlock when the gateway is reachable.

See `BETA_TESTING.md` for the short tester path.

## Quick Menu sync rule

Phone edits are never silently discarded.

When desktop MSBT and the phone have both changed since the last sync, the mobile client must ask the user to:

1. Merge changes
2. Keep phone layout
3. Keep PC layout
4. Decide later

Merge behavior:

- match commands by stable command identity, not visible label;
- apply phone renames to matching commands;
- preserve PC-only commands;
- append phone-only/new commands to open slots at the end of the current layout;
- do not silently delete either side's unsynced work.

The offline beta already stores the local layout with dirty/revision state so the eventual gateway can use this policy.

## Catalog plan

Baseline APK contains snapshots from the desktop MSBT resources:

- GZO
- Lootlemon
- MSBT/custom static codes

Future refresh behavior:

- GZO refreshes from its online catalog and image URLs;
- refreshed data/images are cached locally;
- failed refresh leaves the last known-good cache intact;
- MSBT-only/static codes can update from the repository/catalog manifest or an app update;
- desktop MSBT does not need to stream the entire catalog to the phone during normal use.

## Distribution

Do not bundle the Android APK inside the Windows MSBT installer.

Closed beta distribution is through Discord using either direct files or a GitHub Actions/Release link.

Build workflow outputs two separate artifacts:

- `MSBT-Mobile-Controller-0.1.0-beta.13.apk`
- `MSBT-Mobile-Beta-Test-Kit-0.1.0-beta.13.zip`

See `BETA_TESTING.md` and the `test_kit/` folder for tester instructions, checklist, and Discord DM feedback format.

## Build

The GitHub Actions workflow `.github/workflows/mobile-beta-build.yml` builds the Android beta from the `mobile-controller-prototype` branch.

The APK catalog assets are generated from the same checked-in resources used by desktop MSBT so the multi-megabyte source catalogs are not duplicated under `mobile_controller/`.
