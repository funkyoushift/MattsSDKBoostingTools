# Mission controls and replay testing

Mission tools now use clearer Complete, Mission selection, Replay and Full game views. Amber experimental notices identify unfinished behavior, and later replay choices carry an Experimental label.

This patch repairs shared objective completion, normal NPC interaction handling, map refresh during replay, movement cleanup and recovery controls. A selected objective uses the same guarded execution as mission completion, including its authored child objectives. Status refresh clears obsolete Continue/Stop controls while preserving recovery records when the connection fails.

Host tests passed mission-opening replay, selected-objective NPC completion, native objective rewind, and a replay checkpoint with a known preceding location. Save comparisons retained inventory, experience, currencies, character progression and map discovery.

## Experimental limitations

- Later checkpoint setup can stop because of scene placement, NPC interaction or mission dependencies. Some doors and encounters may still need normal gameplay or a map reload.
- Missing checkpoint coordinates use normal waypoint navigation; an exact teleport is not promised. Eleven later Heist stages lack a required extracted objective definition and remain unavailable.
- Full-game progress can contain skipped or unverified content, including content the lobby cannot access. A finished run does not guarantee a saved 100% character.
- Complete all-mission playability and guest-owned save/rejoin persistence have not been verified.

Use Stop for a stalled run, inspect its result, and use the offered recovery controls. Changes already applied remain. Please report the mission, selected objective, and result message when something fails.

The newer direct checkpoint-selection shortcut remains under development and is excluded from this release.

## Install or update

Run **MSBT-Installer-v2.38.1.exe**, or extract **MSBT-Portable-v2.38.1-win-x64.zip**. Close Borderlands 4 before replacing its SDK mod, then restart it before testing live actions. The installer, desktop and standalone SDK mod share version 2.38.1.
