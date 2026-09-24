# Settings persistence fixes

- Keep saved rarity sliders when the desktop app first connects to the game.
- Save rapid movement, rarity, and walkthrough preference changes in order, preserving the last selection.
- Restore walkthrough preferences and stop dismissed tours reopening immediately. Tours can still be replayed manually and offered after an update.
- Write Quick Menu and inventory settings atomically, keep reads and writes on the same settings file, and surface write failures.

Validation: real desktop save/exit/reopen tests, checked and unchecked startup preferences, concurrent-save tests, and Quick Menu disk persistence and failure tests. Quick Menu persistence was tested offline; live in-game behavior was not retested for this patch.
