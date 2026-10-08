# MSBT 2.32.0 — 100% Drop Rate farming control

- Added **100% Drop Rate On / Off** to **Rarity Weights**. Enable it while playing solo or hosting a farming lobby; it affects the host's native drop-chance routine across the lobby.
- Added both controls to the assignable native **F7 Quick Menu** actions.
- Shows live On/Off status and refuses unqualified game builds or conflicting code changes.
- Starts off each game session and restores normal chance rolls on travel or when MSBT is disabled. Re-enable after traveling to your farming location.
- Rarity presets remain separate: turning this on or off preserves your unsaved rarity sliders and does not save an automatic activation preference.

Matt confirmed the local farming trial works. The implementation forces eligible positive-chance rolls to pass; item-pool selection, eligibility and exclusive choices still apply. It does not promise every possible item on each kill.

Currently qualified for Steam build **25372571**. Other builds, including Epic, refuse activation until separately qualified. Existing Epic item-card support remains included.

Update the desktop app and game mod, then restart Borderlands 4 to load the integrated controls. Android **1.6.0** is carried forward unchanged; this release adds the desktop and F7 farming controls.

Credit to **FLiNG** for the trainer research lead. No trainer executable or injection script is included.
