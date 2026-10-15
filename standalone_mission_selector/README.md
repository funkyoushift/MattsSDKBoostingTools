# BL4 Mission Selector

Jump back to a mission or main objective, bookmark a section you want to replay,
and toggle dialogue skip from the in-game SDK console. The MSBT desktop app is
not required.

Replay is experimental and supports solo play. It keeps your gear and levels,
but changes mission progress: earlier requirements are filled in and later
dependent progress is cleared. A backup is saved before each replay.

## Install

1. Install the Borderlands 4 Python SDK if you don't already have it.
2. Close the game. If you use MSBT, move `MattsSDKBoostingTools.sdkmod` out of
   `sdk_mods`. Disabling it in the mod menu isn't enough.
3. Copy `BL4MissionSelector.sdkmod` into `sdk_mods` and start the game.
4. Enable **BL4 Mission Selector** in the SDK mod menu, then load a character
   in a solo game.

You need a second working character in the same save profile. The mod switches
characters automatically while editing the save. Python and Node do not need
separate installations.

## Use the console menu

Open the SDK console mod menu, choose **BL4 Mission Selector**, then select
**Mission replay** and press **1** to open the picker.

1. Choose a campaign: Main story, FL4K, Ellie or Moxxi.
2. Choose a numbered mission.
3. Choose its beginning or a main objective.
4. Select **Start replay**, then close the console while it loads.

Enter the number shown beside each choice. **B** goes back, **Q** leaves the
menu, and **N / P** change pages. No mission commands need to be typed.

The main story picker follows the main walkthrough objectives in
[Game8's mission guide](https://game8.co/games/Borderlands-4/archives/550061):
21 missions with 65 sections. Internal steps are played as part of each section.
The 18 supported DLC missions use the same route-level grouping: 61 sections,
covering Ellie, FL4K and A Zane to Kill For. DLC boundaries use native progress
with PowerPyx and FL4K walkthroughs as route references. Switches, pickups and
intermediate fights stay inside their section.

Replay sections include the route from the previous section. For example,
**Crime-scene investigation** in A Zane to Kill For includes reaching the scene,
interviews, scanning, collecting the evidence and returning to place it. The
following section starts beside the finished evidence table for the trip onward.
Use a bookmark when you want an exact point inside a section.

The picker also has **Bookmarks**, **Dialogue skip**, **Fog on replay**,
**Replay status**, **Stop replay setup** and **Restore pre-replay backup**.
Save a bookmark while playing a mission and give it a name; load it later from
the bookmark list. Stand on foot where you want to restart: new bookmarks record
your exact position and saved mission/world state, including internal steps.
Loading keeps your current gear and levels. Older bookmarks marked **spawn station**
keep their original station-based loading. Dialogue skip resets when the game restarts.

Mission beginnings use their authored entry point when available. Later starts
use the previous objective's completion point, with a nearby native spawn station
as the fallback. Boss objectives with a native arena arrival keep that spawn
instead of moving back to an approach trigger outside the arena.
The selected replay mission stays on the HUD across map travel;
choosing another mission manually stops that behavior. Some encounters may still need a
normal interaction or approach to begin. Ten random story starts were checked
in-game: nine used their recorded coordinates; one used a nearby native station.
Those checks covered loading and spawn positions, not full objective completion.

Fog stays unchanged by default. Use **Fog on replay** to clear or restore it
when loading a mission or bookmark.

## Restore a backup

Stop the run and use the game's character picker to load a different character.
Then choose **Restore pre-replay backup** and confirm **Restore backup**.

The mod won't overwrite a character that's currently loaded. Backups and
bookmarks are kept under `sdk_mods/settings/BL4MissionSelector/replay`. A game
restart stops an unfinished run and keeps its backup.

To switch back to MSBT, close the game and swap the two SDK mods. Each keeps
its own settings. Steam and Epic save profiles are supported; the standalone
build's live checks were run on Steam.

## Optional commands

The original commands still work for shortcuts and scripts. Use
`mission_select help` for the full list.

## Credits

Project: FunkYouSHiFT. MSBT and editor foundation: Mattmab (Matt / Galoob).
Save codec: glacierpiece, through Mattmab's editor. BL SDK runtime: apple1417,
Faultz and the BL SDK team. Bundled dependencies: Node.js and PyYAML.
Third-party license notices are included in `licenses/`.
