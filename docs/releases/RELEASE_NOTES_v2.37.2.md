# v2.37.2 — Progress-run repairs

- Scoped mission, story, side-mission, DLC, map discovery and travel actions now use the same fast processing loop as 100% Game. Scoped mission runs also skip dialogue through the same helper.
- Restored normal Accepted-state mission completion and removed fixed transition waits while retaining native result and applicable guest challenge-credit checks.
- Other bridge commands no longer cancel waiting progress requests. Temporary connection failures recover the same job rather than restarting completed work.
- Repair and continue preserves the current stage. Failed vehicle unlocks and inactive vault cards are reported without preventing remaining stages.
- Final recheck still picks up later unlocks without resetting completed work.

Limits: unavailable content remains listed separately. Generic objective completion, undo and reset-all remain unavailable. The Chase guest-save issue remains unresolved for one reported character. Failed vehicle unlocks are reported, not claimed repaired. Verify guest progress in each player's own game; these release checks are offline and do not establish a new multiplayer persistence result.

Dialogue native-call research credit: Yeti's Dialog Skipper.
