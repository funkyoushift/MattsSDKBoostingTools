# v2.39.9 — Support destination and saved choices

- Route FunkYouSHiFT development support in Windows, Android and GitHub funding to Buy Me a Coffee while retaining Mattmab's separate Ko-fi credit.
- Honor the desktop app tour's “don't auto-show” checkbox: leaving it unchecked offers the tour again on the next launch; checking it suppresses the current version until an update.
- Save the mobile announcement checkbox when the user closes the announcement or opens Mobile Gateway; reopening it lets users change that choice.

# v2.39.8 — Full Game recovery

- Keep an uncertain mission challenge callback attached to its original receipt and allow an interrupted Full Game run to close only its matching mission job.
- Continue other independent missions after a recorded failed operation, and expose explicit Run anyway recovery for a stopped run.
- Show current Epic users the same 1.10 catalog coverage warning as current Steam users. Live Epic gameplay and saved 100% completion remain unverified.

# v2.39.0 — Mission selection and co-op progress

- Repair solo save-backed replay with a unified, numbered selector for39 story/DLC missions and 506 main objective sections, including later points in a playthrough. Native character swaps are automatic; a second existing character in the same profile is required.
- Preserve current gear and levels while backing up/editing inactive mission state, reloading the character/map and placing the host using326 authored preceding-waypoint candidates or native-station fallback. Individual encounters remain experimental.
- Add mission-state bookmarks that restore the captured mission/world timeline and native respawn station without coordinate setup.
- Use native dialogue completion for the dialogue-skip toggle. Live conversation completion and map-reload retention passed; authored timed scenes may still wait.
- Preserve the original bulk100% mission callbacks. Do not run individual mission scenes or the broken fog-reveal teleport tour during full completion.
- Refresh visitors' actual entitlement snapshots before full completion; continue native-accessible content and report blocked packs without changing ownership. Automatic refresh and a complete mixed-DLC run passed live testing.
- Repair per-visitor campaign completion credit through the existing build-pinned once-only mission callback. Campaign unlock and all 25 UVHM challenge steps passed native checks for a three-player lobby; guest own-save verification remains separate.
- Put ordinary challenges before UVHM, remove a redundant wait after verified UVHM steps, retain no-retry uncertainty guards and check progression-bearing characters instead of vehicle pawns for upgrades.
- Include Epic compatibility/account-codec repairs, Shinies credential forwarding and the reviewed desktop layout/control repairs.
- Keep mission/replay/full-progress tools visibly experimental. Both visitors confirmed story completion and UVHM 7 after the mixed-DLC run; no guaranteed saved 100% claim.
- See [implementation and validation](docs/changes/2026-10-14-mission-repair-plan.md).

# v2.38.1 — Mission controls and experimental replay

- Repair shared objective completion, NPC/map handling and movement cleanup.
- Rename Practice to Mission selection and clarify the four mission views.
- Mark unfinished mission behavior and later checkpoints in amber with explicit Experimental labels.
- Refresh stale job controls and retain recovery records when a connection fails.
- Disclose scene/dependency failures, unavailable content and incomplete 100%/guest verification.

# v2.37.2


Progress-run speed, shared scoped processing, recovery and bridge queue coexistence repairs. See docs/releases/RELEASE_NOTES_v2.37.2.md.

# v2.35.0

Mayhem 1-20 selected-player and optional AFK guest unlock controls and tested bridge, camera, Party Reveal, and Farming status repairs. See docs/releases/RELEASE_NOTES_v2.35.0.md.

# Changelog

## 2.31.0 - 2026-10-08

- Epic build 4845623 native item cards and Item Editor previews, with exact build/function checks.
- Android 1.6.0 includes the shared Windows workspace, editor and file tools through existing pairing.
- Persistent phone caching of unchanged large status lists; live players, AFK and command updates remain fresh.
- Phone player selection and ordinary commands remain usable during AFK while delivery conflict checks remain enforced.
- Item Catalog focus no longer exposes hidden card-rendering windows.
- AFK host-test errors remain visible; vault-card readback follows track identity. Rank-setting failure remains a separate issue.
- Epic passed executable comparison and offline validation; live Epic confirmation is pending.

## 2.30.2 - 2026-10-06

- Replaced Saved Items' native delivery confirmation with an in-app confirmation to avoid the previously observed native-dialog keyboard-focus failure path.
- Added explicit theme colors and bounded sizing to delivery and password dialogs.
- Verified Saved Items and Item Catalog password input, cancellation and authorization in Workspace and Classic layouts with simulated delivery responses. The originally reported blank-white popup was not reproduced.
- Android remains 1.5.1; no gameplay behavior changes.

## 2.30.1 — 2026-10-05

### Added

- Prominent contributor credits and links to original projects in the README.
- A plain-text third-party notices file for desktop, SDK, and Android packages.
- A dedicated Credits tab in the desktop app.
- Community Discord links for GZO, Scooter’s Garage, and Azalea Asvail’s Modding World in the README and desktop app.
- Funk’s Borderlands Trading Hub in the community list and desktop links.
- Restored README download counters for the Windows installer, portable ZIP, and Android APK.

### Changed

- Consolidated in-app contributor acknowledgments, community links, and third-party notices into one Credits tab.

- Excluded Python tests and test caches from desktop packages; ignored local research and capture folders.
- SDK packaging now validates its input and replaces the previous package only after a successful build.

- Clarified vehicle preset instructions and repaired references to removed documentation.
- Corrected attribution for the desktop interface and bridge; retained Squ1ggs’ code and helper credits.
- Expanded Mattmab’s credits to name the original gameplay modules, Python helpers, and retained editor components.
- Narrowed Squ1ggs’ credit to later helper additions and references; added Pyrex’s Bonk Utilities acknowledgment and source link.
- Replaced the README with contributor acknowledgments and brief installation guidance.
- Updated packaging to use the plain-text notices file.

### Removed

- Outdated screenshots and their obsolete capture script.

- Retired BLImGui panel, its startup fallback, and unused panel synchronization code. The native F7 Quick Menu and desktop bridge remain the supported interfaces.
- Superseded Quick Menu preview instructions, legacy Tkinter packaging scripts, internal attribution snapshot, and tracked editor-only guidance.
- Outdated app screenshot embeds from the README.
- The previous Markdown documentation outside the main README, including planning notes, handoffs, feature comparisons, and audit narratives.
