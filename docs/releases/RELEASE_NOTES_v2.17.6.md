# MSBT v2.17.6

- Auto-kick now proceeds when a guest run ends even if boosts, inventory verification, or report saving failed. Active work, loot settlement, and unfinished split-screen connection members still get time to finish. Failed kick calls retry up to three times.
- Cleanup failures confirmed to occur before deletion now continue selected loot without repeating boosts. Uncertain clear results never trigger this fallback.
- AFK package opening checks the intended guest’s reward manager. Completed delivery is tracked separately from a failed inventory readback afterward.
- Saves per-guest reports, selected loot, and references to original-inventory backups for later repair. Desktop history shows report locations and clearer operation names.
- Prevents duplicate recovery ownership after boost exceptions, bounds waits for unavailable characters, and preserves delivery errors for diagnosis.

The user confirmed the installed candidate works. Automated tests cover queue progress, failed actions, report-write failures, target identity, split-screen completion barriers, recovery and delivery state.

A kick does not certify a guest save or exact item receipt. Serial readback differences and the reported AFK FPS issue remain unresolved. Review saved reports when a player needs assistance.

Donation links and reusable MSBT-Setup.exe remain included. Android is unchanged at 1.4.2.
