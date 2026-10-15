# v2.39.2 — Mission replay and exact bookmarks

Mission replay now offers whole main objectives, including the route and interactions within each section. The picker covers 65 sections across 21 base-story missions and 61 sections across 18 supported DLC missions. Smaller practice points belong in bookmarks instead of a long list of switches, pickups and dialogue steps.

- New bookmarks record your exact position and saved mission/world progress in both the app and standalone SDK. Loading rewinds that timeline while preserving your current gear and levels. Older station-based bookmarks keep their original behavior.
- Corrected distant station fallbacks and mission entry points. Native boss-arena arrivals stay inside the arena; replay no longer moves you behind its barrier afterward.
- The selected mission stays tracked through map changes. Choosing another mission manually ends that tracking.
- Fixed a placement failure where the game returned false even though it had moved the character successfully. Exact readback and grounding checks still have to pass.
- The standalone **BL4 Mission Selector** runs through the SDK console mod menu, with numbered campaigns, missions and main objectives, bookmarks, dialogue skip, replay status and backup restoration. No desktop app is required.
- Android **1.6.4** carries the matching mission interface. Update the paired Windows app to **2.39.2**; saves and backups remain on the PC.

## Downloads

- **Windows:** `MSBT-Installer-v2.39.2.exe`, or extract `MSBT-Portable-v2.39.2-win-x64.zip`. `MSBT-Setup.exe` is the reusable installer.
- **Android:** `MSBT-Mobile-Controller.apk` or the identical versioned `MSBT-Mobile-Controller-1.6.4.apk`.
- **Standalone in-game selector:** `BL4MissionSelector.sdkmod`. Read the [installation and console menu guide](https://github.com/funkyoushift/MattsSDKBoostingTools/blob/main/standalone_mission_selector/README.md). Use it **instead of** the full MSBT SDK; close the game and move `MattsSDKBoostingTools.sdkmod` out of `sdk_mods` first.
- **Full app SDK:** `MattsSDKBoostingTools.sdkmod`, also bundled with Windows.

## Requirements and limits

Replay requires solo hosting and a second working character in the same save profile. Steam and Epic save handling remain included. Close the game before replacing SDK files. A pre-replay backup is retained.

Generated replay states and encounters remain experimental. Starts use the previous section's completion point or a nearby native station where possible; unavailable or unsafe coordinates retain native placement. Bookmarks restore saved mission/world data and position, not an exact snapshot of every live NPC. Not every section has been played end to end, and new Epic live checks are not claimed.

Both standalone and the real Windows app passed live bookmark capture, movement, automatic character reload and exact-position restoration checks, with matching objective state and protected gear. Source, worker, package and startup checks are recorded in the repository verification receipt. Android packaging checks are separate from phone gameplay evidence.

Existing mixed-DLC full-game completion and dialogue skip remain available. The broken teleporting fog-reveal tour remains excluded. A finished bulk run does not guarantee every achievement, collectible or saved 100% character.

Credits remain with the original contributors, including Mattmab's MSBT foundation and Yeti's dialogue-skip research; see the README and bundled notices.
