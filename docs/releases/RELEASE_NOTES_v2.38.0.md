# v2.38.0 - Mission progress and replay

- Advance one active objective in a tracked mission or bounty without completing the entire mission. The final objective can finish its mission naturally.
- Replay the last completed ordinary mission objective at its authored checkpoint, reopen a started/completed mission, or reset the campaign to Guns Blazing while retaining equipment, levels, currencies, ranks and map discoveries.
- Reset fixes restore reviewed safehouse switches and 63 activity markers. Added base/DLC activity definitions bring the completion catalog to 251 entries.
- Individual mission completion now includes reviewed travel/unlock requirements and unfinished subordinate missions, using the same shared backend as 100% Game. Completed related work is preserved.
- Mission choices show progress status, with search, sorting and filters. Dropdowns are more visible throughout the desktop app.

Host validation: a full reset cleared 285 ordinary runtime mission records, retained saved character progress and restored Arjay's opening route. The main world did not immediately re-complete old side missions. Objective advancement and checkpoint replay were also verified on the Cowbell DLC map at Crisis Scar Weeping.

Limits: replay preserves earned rewards; it is not a historical reward rollback. Generated bounty replay and the dynamic Ruined Sumplands crawler actor reset remain unsupported/unverified. Broader encounter-specific world effects and new player-two own-save persistence are not universally verified. The previously reported The Chase guest-save issue remains unresolved. The new mission/objective teleport practice selector is in development and is not included.

Practice-selector plan for the next build: use the preceding mission completion location as its start anchor, move the lobby together, and restore the selected mission/objective checkpoint. This remains excluded from v2.38.0.
