# v2.39.8 — Full Game recovery

This patch repairs Full Game runs that stopped on an uncertain mission operation and could not be resumed or restarted. A failed independent mission is recorded as unverified and deferred while the bound lobby continues through other work. An already-issued challenge credit keeps its original receipt; it is never repeated or silently attributed to the next mission. The desktop panel offers Run anyway for a stopped run and Close for its matching interrupted receipt, with the applied progress retained.

The current Steam test build reached all nine Full Game stages in a shared lobby without stalling. The result was **partial**, not 100%: 241 of 245 eligible mission entries verified, and the challenge readback found 2 incomplete and 166 unavailable player/definition checks. Mayhem/Takedown access was not confirmed for the whole lobby. The app reports those limits instead of claiming a platinum trophy or saved completion.

The installed current Epic executable matches the offline-qualified mission, farming, host-inventory and item-card profiles. Epic now receives the same warning as Steam that the mission, discovery and challenge catalogs still originate from game 1.10. Epic gameplay was not launched, and joined-client-local inventory on the current Epic build remains gated. Neither platform has verified guest saved progress or trophy awards from this patch. The host WSW Bridge save rollback, Fuel Siphon parent challenge and unavailable challenge definitions remain unresolved.

Android 1.6.5 is unchanged. The standalone Mission Selector is repackaged with matching version metadata; it remains separate from the full-app SDK.

## Downloads

- **Windows:** `MSBT-Installer-v2.39.8.exe` or `MSBT-Portable-v2.39.8-win-x64.zip`.
- **Full app SDK:** `MattsSDKBoostingTools.sdkmod`, also bundled with Windows.
- **Standalone selector:** `BL4MissionSelector.sdkmod`; install it instead of the full app SDK, not alongside it.
- **Android:** `MSBT-Mobile-Controller.apk`, version 1.6.5.

Close Borderlands 4 before replacing SDK files. Existing save files and replay backups stay on the PC.
