# Electron Roadmap

MSBT's current user-facing app is the Electron desktop app. The older Tkinter app remains in the repository as legacy/reference material and as a rollback package when needed, but new user-facing work should target Electron first.

## Current Direction

- Keep the original BLImGui panel optional for users who still want it in-game.
- Keep the SDK mod focused on live game actions and the HTTP bridge.
- Keep local catalog, serial, bookmark, editor, validation, and UI workflows in Electron.
- Preserve user data across installs and updates.
- Publish stable releases with Semantic Versioning and clear installer/portable download names.

## Current Checkpoint

- Boosting, Serial Tools, Serial Bookmarks, BL4 Codes, Validator, Item Pool Spawning, Map Travel, Movement, Activity Log, Report, Updates, Dev Spawner, and Matt Editor tabs are present in Electron.
- The installer bundles the Electron app, the SDK mod, ActorScriptDeployer, resources, and a portable Python runtime.
- The update flow checks GitHub Releases and can warn users when the app package or bundled SDK mod is newer.
- Dev Spawner uses the verified SDK 03 bridge path for `ASD_spawnai`.
- Matt Editor is hosted inside Electron through the local helper and routes save/profile conversion plus MSBT delivery through the embedded workflow.

## Active Priorities

1. Verify user data preservation across real updates:
   - bookmarks
   - movement presets
   - Dev Spawner favorites
   - future app settings
   - window size and opacity
   - rarity presets
2. Verify and polish Matt Editor integration:
   - embedded save/profile conversion is routed through the bundled local helper
   - item editor delivery path remains clear and reliable
   - real save-file conversion and serial parsing issues are visible and recoverable
3. Continue Dev Spawner parity:
   - source-of-truth rebuild from SDK Debug Menu / ActorScriptDeployer UX
   - remove/despawn workflow
   - better actor workflow
   - barrel logo improvements
4. Finish settings/preset polish:
   - rarity presets
   - option to disable saved rarity presets
   - do not force legendary/pearl-only rates unless the user chooses that preset
5. Improve public project presentation:
   - release assets named clearly
   - README screenshots and clearer install path
   - FunkYouSHiFT tools-page links
   - credits/third-party notices when source links are finalized
6. Research live player-data access:
   - levels, currency, vault/spec rank
   - inventory and equipped item serials
   - ground item serials where possible
   - mission state and objective progress

## Release Blockers

Block a release only for issues such as:

- app cannot install or launch
- packaged resources are missing
- bundled SDK mod cannot load on the current SDK stack
- bridge actions silently report success after failure
- user data is likely to be deleted during update
- serial delivery commonly targets the wrong player
- update flow points to missing or mismatched assets
- secrets or credentials are embedded in the build

## Release Checklist

Before publishing a stable release:

1. Confirm `electron_poc/package.json`, `releases/latest.json`, and release asset names use the same SemVer version.
2. Build the SDK mod and Electron installer/portable package from the current source.
3. Install from the freshly built installer on the test machine.
4. Confirm the installed SDK mod and ActorScriptDeployer are copied to `sdk_mods`.
5. Confirm the app launches without a system Python install.
6. Confirm core bridge status and at least one safe live action.
7. Confirm update metadata reports the correct current version.
8. Confirm user-data folders are not inside the app install folder.
9. Upload installer, portable ZIP, `latest.yml`, blockmap, and `latest.json` to GitHub Releases.
10. Keep legacy/Tkinter packages clearly labeled as rollback only.

## Known Open Work

- Full save-editor polish in Matt Editor.
- Deeper Dev Spawner parity and safer advanced actions.
- Send shinies to target and final Drop All Shinies verification.
- Full app-wide settings persistence audit.
- GitHub/website presentation pass.
- Live player-data research.
