# MSBT Mobile Controller — AI Handoff Brief

Use this file as the source-of-truth handoff for GPT/Cursor continuing the Android mobile controller work.

## Repository

- Repo: `funkyoushift/MattsSDKBoostingTools`
- Local Windows workspace expected: `C:\Users\mwenn\Desktop\MSBT_Codex_Work\working`
- Active mobile branch: `mobile-controller-prototype`
- Android project: `mobile_controller/`
- Do not merge to `main` or publish a release without Martin's explicit approval.

## Product Direction

App name: **MSBT Mobile Controller**

Android package ID:

`com.funkyoushift.msbt.mobile`

This is a focused live cheat/controller companion for desktop MSBT and Borderlands 4. It is not intended to recreate every desktop feature.

Keep/prioritize:
- Home/status
- PC/MSBT pairing
- Player targeting
- Boosting
- Boost serial sender
- Serial Bookmarks
- BL4 Codes
- Quick Menu
- Inventory controller functionality
- Map Travel
- Player Movement
- Dev Spawner
- Item Pool Spawning
- Activity/results
- Settings

Do not prioritize:
- Matt Editor
- save/profile editing
- Legit Builder
- deep item creation/building
- desktop installer/updater controls
- desktop panel-layout editing

Primary navigation:
- Home
- Boost
- Codes
- Control
- More

Visual identity should strongly match desktop MSBT: dark UI, cyan/purple/gold accents, rarity colors, recognizable MSBT styling, large mobile touch targets. Portrait-first; Quick Menu must also work well in landscape.

## Current Beta State

The first Android beta was built successfully and installed on Martin's phone.

Approximate version:

`0.1.0-beta.1`

Preserve package ID and signing identity so future APKs install as updates without wiping local app data.

Current GitHub Actions workflow:

`.github/workflows/mobile-beta-build.yml`

## Immediate Known Bug — BL4 Codes

BL4 Codes currently shows no records in the installed APK. Pressing Refresh also does not load anything.

Current mobile JS attempts to load bundled assets with calls like:

```js
fetch('MattsSDKBoostingTools_gzo_codes.json')
fetch('MattsSDKBoostingTools_lootlemon_codes.json')
fetch('custom_bl4_codes.json')
```

The app runs in Android WebView from roughly:

`file:///android_asset/index.html`

The Gradle build copies desktop catalog files into Android assets, but the phone still displays zero records.

### Fix this first

Audit rather than guessing:
1. Confirm the expected JSON files are actually inside the APK.
2. Confirm their exact APK paths.
3. Confirm their JSON structure.
4. Inspect WebView/Logcat errors.
5. Fix local asset loading robustly.

Possible clean solutions include:
- correct Android asset URLs
- `WebViewAssetLoader`
- a narrow native Android asset-read bridge
- another proper WebView-safe local-resource mechanism

Do not rely on a fragile `file://` fetch behavior if it is the root cause.

The bundled catalog must work offline.

Add explicit error reporting instead of silently showing zero results, e.g.:

`Bundled catalog unavailable: <reason>`

Show real counts for:
- Total
- GZO
- Lootlemon
- MSBT/custom

## BL4 Codes Requirements

The mobile Codes screen should support:
- GZO
- Lootlemon
- MSBT/custom/static codes
- additional desktop-supported sources where practical
- free-text search
- source filter
- type/category filter
- manufacturer filter
- rarity filter
- useful creator/source metadata where present
- one-item selection
- multi-select
- Select All Filtered
- Clear Selection
- selected count
- eventual batch send once connected

The phone should be able to browse/search codes while completely offline.

Catalog strategy:

**bundled baseline + latest cached online data**

GZO:
- keep current GZO-backed catalog/data model
- support images
- allow refresh
- cache refreshed records/images
- failed refresh must never erase a working cache
- show last successful refresh time

Lootlemon:
- include/use existing current/static records
- allow updating if the desktop architecture already exposes a clean source

MSBT/custom:
- bundle a baseline static catalog
- later may refresh from GitHub
- do not require a full APK update for every custom-code addition if a clean catalog-sync design is practical

Do not require the phone to pull the entire catalog through the PC every time.

## Serial Bookmarks

Mirror the current desktop bookmark schema as closely as practical.

Expected fields:
- id
- name
- group
- serial
- created_at
- updated_at
- metadata

Support:
- add
- edit
- delete
- search
- group filtering
- copy
- validate
- eventual send selected/all/non-host

Keep the mobile data shape compatible enough for future PC/phone sync.

## Quick Menu — Data Safety Is Critical

The complete Quick Menu must remain available:
- up to 5 pages
- full 3 x 7 slots per page

Do not reduce slot count just because it is mobile.

Portrait must remain usable via scrolling/scaling as needed.
Landscape should feel like a dedicated controller.

Offline editing is allowed.

### Never silently discard offline Quick Menu changes

When the phone later reconnects and both phone and PC layouts have changed, offer conflict resolution:
- Merge
- Keep Phone
- Keep PC
- Decide Later

Merge principles:
- match by stable command ID when possible
- preserve command identity through renames
- preserve phone renames when appropriate
- do not delete phone additions just because new PC commands appeared
- phone-only/new commands should go into available slots or be appended toward the end
- do not overwrite dirty local edits without explicit user choice
- retain local/base revision metadata
- persist offline changes across app restarts

Before changing sync logic, inspect current mobile Quick Menu persistence/merge code and current desktop Quick Menu implementation.

## Movement

Movement must not be a stripped-down placeholder.

Audit the current desktop Electron Movement feature and mirror the useful live controls with mobile-friendly cards/sliders/toggles/presets.

Known current mobile fields include:
- Speed Scale
- Walk Speed
- Jump Height
- Gravity Scale
- Step Height
- Floor Angle
- Glide Speed
- Glide Boost
- Glide Air Control
- Dash Speed
- Time Dilation
- Sprint Jump
- Double Jump
- Slide Jump
- individual jump goals
- Zero Vault on Apply

Do not assume that list is complete. Compare against desktop.

Persist mobile presets locally.

## Boost

Audit current desktop MSBT and preserve useful live controller features such as:
- target player
- Quick Max
- cash/currency
- Eridium/other supported currencies
- XP/level
- spec/skill-related boosting
- backpack/bank/SDU controls where supported
- rarity controls
- serial sender
- copies
- level override
- validate
- confirm
- selected/all/non-host delivery

Do not recreate deep serial editing tools.

## Connection Architecture

Current game-side bridge historically binds only to:

`127.0.0.1:49774`

Do **not** simply expose it to `0.0.0.0`.

Do not expose an unauthenticated game-control API directly to the LAN.

Preferred architecture:

```text
Android
   |
authenticated LAN connection
   |
Desktop MSBT / Electron Mobile Gateway
   |
localhost bridge
   |
MSBT SDK mod
   |
Borderlands 4
```

Desktop Electron should own the mobile gateway.

Gateway requirements later:
- explicit Enable Mobile Controller switch
- LAN-only by default
- paired-device authentication
- pairing code and/or QR
- revocable tokens
- status/capability reporting
- rate limiting
- command allowlist
- no arbitrary bridge/action exposure
- connected-device list on desktop
- revoke device support
- stable versioned API contract

Mobile Connection screen should support:
- PC name
- PC IP
- gateway port
- pairing code
- Test Connection
- Find MSBT on Network later
- QR pairing later
- forget/re-pair
- clear PC/Desktop/SDK/Game statuses

Do not fake successful live actions while disconnected.

## Android Local Development Setup

Set this Windows PC up so builds can run locally instead of relying only on GitHub Actions.

Audit first:
- git status/branch/log
- Java/JDK
- Android SDK
- adb/platform-tools
- Android build-tools/platforms
- Gradle / wrapper
- Android environment variables
- Node/npm if relevant
- Python if relevant
- connected Android device
- USB debugging authorization

Prefer Java 17 unless the actual project requires otherwise.
Prefer repo-local/user-local tooling and minimal system changes.

Useful scripts may be added if consistent with repo conventions, e.g.:
- `tools/mobile_build.ps1`
- `tools/mobile_install.ps1`
- `tools/mobile_logcat.ps1`
- `tools/mobile_screenshot.ps1`
- `tools/mobile_test.ps1`

Goal: one-command build/install/launch/log workflow.

## ADB Workflow

Once the phone is connected and authorized:
- `adb devices`
- build APK
- install/update with `adb install -r`
- launch app
- collect filtered Logcat/WebView output
- capture screenshots from PC

After the BL4 Codes fix:
1. build next beta version
2. install over existing beta without wiping data
3. launch
4. confirm bundled catalog count is nonzero
5. confirm GZO/Lootlemon/MSBT counts
6. test search/filters
7. test multi-select
8. test Select All Filtered/Clear
9. turn Wi-Fi off
10. relaunch and confirm catalog still works offline
11. turn Wi-Fi on
12. test Refresh
13. failed refresh must preserve last working cache

## Android/WebView Security

Audit `AndroidManifest.xml` and WebView settings.

The app will eventually need:
- Internet for catalog refresh/images
- LAN access for desktop gateway

Be conscious of:
- `INTERNET` permission
- cleartext LAN HTTP during beta if needed
- Android Network Security Config
- WebView local-origin restrictions
- mixed content
- CORS
- asset access
- external URL handling
- any JavaScript bridge exposure

Do not create an overly permissive WebView.
If `addJavascriptInterface` is used, expose only narrow explicit methods.

## Signing

A stable beta signing identity was created for the first APK.

Find and preserve it.

Do not generate a new signing key unless the existing key is unusable and Martin explicitly approves replacing it.

Future APKs must update over:

`com.funkyoushift.msbt.mobile`

without wiping:
- Serial Bookmarks
- Quick Menu edits
- Movement presets
- connection settings

## Versioning

Installed first beta is approximately:

`0.1.0-beta.1`

Bump `versionCode` and `versionName` for every build.
Use the next available version after auditing source history, likely `0.1.0-beta.2` if no newer build exists.

## Beta Distribution

The APK is a separate product artifact.

Do not package the APK inside the Windows MSBT installer.

Closed beta distribution is through Discord DMs for now.

Closed-beta feedback goes directly to FunkYouSHiFT in Discord DMs.
Do not build a public feedback system yet.

Artifacts should stay separate:
- `MSBT-Mobile-Controller-<version>.apk`
- optional `MSBT-Mobile-Beta-Test-Kit-<version>.zip`

The test kit should not contain desktop MSBT.

Tester feedback template:

```text
MSBT MOBILE BETA FEEDBACK

Phone make/model:
Android version:
MSBT Mobile version:
Desktop MSBT version if connected:

Screen/feature:
What I expected:
What happened:
Steps to reproduce:
Does it happen every time? Yes / No / Sometimes

Screenshots attached: Yes / No
Anything else:
```

Requested screenshots:
- Home portrait
- BL4 Codes results
- BL4 Codes multi-select
- Quick Menu portrait
- Quick Menu landscape
- Movement
- Connection Settings
- any broken/clipped screen

## Desktop Architecture Rules

Do not make Android directly depend on/import:
- `unrealsdk`
- `mods_base`
- `BLImGui`
- `blimgui_panel`
- `backend_actions`
- `external_bridge`

The game-side SDK owns live game interaction.
External clients use network/API boundaries.
BLImGui remains optional.
Do not break desktop Electron while building mobile support.

## Repository Safety

Before meaningful edits:
- inspect actual files
- inspect git status
- inspect diffs
- inspect recent commits

Do not guess.

Do not touch/commit:
- `_inspect/`
- `_install_backups/`
- generated APK/build output
- local Android SDK installs
- temporary logs/screenshots
- unrelated generated folders

Be especially careful with signing secrets/keystores.

Do not merge the mobile branch to `main` without Martin's approval.
Do not publish a GitHub Release without Martin's approval.
Do not rewrite history destructively.

## Work Style

Work in coherent, testable slices:
1. Audit
2. Briefly report what was found
3. Implement
4. Build
5. Validate
6. Install/test on device where possible
7. Collect logs
8. Commit cleanly
9. Report exact outcome

Martin will do visual and physical-device testing.
Do not make him manually copy/paste lots of code if the agent can edit files directly.

## Immediate Task Order

### Stage 1 — Audit

Run/inspect:
- `git status`
- `git branch`
- `git log --oneline -20`

Then inspect:
- `mobile_controller/`
- `.github/workflows/mobile-beta-build.yml`
- desktop BL4 Codes implementation
- desktop Movement implementation
- desktop Boost implementation
- desktop Quick Menu implementation
- desktop Serial Bookmarks implementation
- desktop gateway/bridge code

### Stage 2 — Local Android Toolchain

Make local Android builds work reliably.
Verify:
- `java -version`
- `adb version`
- `adb devices`
- Android SDK path
- required platform/build tools
- Gradle/wrapper

Install only what is missing.

### Stage 3 — Fix BL4 Codes

Find the exact root cause of zero catalog records.
Inspect APK contents, generated assets, JSON formats, WebView requests, and Logcat.
Fix it robustly.

### Stage 4 — Build Next Beta

Bump version.
Build signed APK.
Install with `adb install -r`.
Verify existing app data survives.
Verify catalog works offline.

### Stage 5 — Mobile Feature Parity Audit

Compare mobile UI against desktop live-controller features:
- Boost
- Movement
- Quick Menu
- Codes
- Serial Bookmarks
- Travel
- Inventory
- Dev Spawner
- Item Pool

Identify missing important controller features.
Do not add Matt Editor/save editor/Legit Builder.

### Stage 6 — Quick Menu Safety Tests

Where practical, add tests for:
- offline rename persists
- new phone command persists
- incoming PC layout cannot silently overwrite dirty phone layout
- same-command rename merges correctly
- new PC command retained
- new phone command retained
- no-free-slot case does not silently destroy entries

### Stage 7 — Connection Gateway

After the catalog fix is stable, inspect desktop Electron and design/implement the authenticated mobile gateway in an isolated, safe way.

Do not change the in-game localhost bridge to public LAN binding.

## Final Report Expected From the Next Agent

Report:

1. Audit
- branch
- repo status
- relevant recent commits

2. Local environment
- JDK
- Android SDK
- adb
- Gradle
- connected phone model/Android version

3. BL4 Codes bug
- exact root cause
- files changed
- fix
- asset paths
- catalog counts

4. Build
- app version/versionCode
- exact APK path
- signing status
- APK size

5. Device test
- adb install result
- launch result
- data preservation
- Logcat result
- offline catalog result

6. Mobile parity audit
- important missing features
- beta blockers
- non-blocking polish

7. Commits
- hashes/messages

8. Git status
- exact remaining modified/untracked files

9. Martin's next test
- short exact physical-phone checklist

## First thing to do now

Do not immediately rewrite files.

Audit the repository and local environment first.

Then report:
- current branch
- current git status
- current mobile version
- whether the BL4 JSON assets are really in the APK
- whether `adb` sees Martin's phone
- most likely cause of the zero-code BL4 screen

Then proceed with the fix unless something destructive or ambiguous is discovered.
