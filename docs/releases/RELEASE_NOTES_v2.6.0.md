### What's new

**v2.6.0**

- **Hoard Builder** — staggered multi-point pacing, higher caps, adjustable spawn distance, and reusable favorites
- **Hoard safety** — deferred disable and post-clear quiet windows avoid destructive actor teardown; normal Hoards persist until **Emergency Clear**, with loot cleanup remaining opt-in
- **Hoard tradeoff** — multi-point enemies spawn forward of the player rather than at true surrounding bearings
- **Runtime stability** — bounded bridge work, game-thread status snapshots, travel cleanup, throttled Quick Menu/holds/fog work, and optional performance profiling
- **Electron responsiveness** — adaptive polling, lazy catalogs, a persistent Python worker, on-demand Mobile Gateway work, and serial conversion off the game thread
- **Pull Loot Here** — loot now lands in an Archimedean spiral (starting around 240 cm with roughly 155 cm spacing) instead of overlapping 8-spoke rings
- **Other fixes** — safer golden-chest and Streamer Chaos tick deadlines, faster infinite-jump early returns, and related hot-path cleanup

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.6.0.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.6.0-win-x64.zip`

**Do not manually download these unless you know why**

- latest.json, latest.yml, *.blockmap

### Upgrade notes

1. Install `MSBT-Installer-v2.6.0.exe` (or extract the portable ZIP).
2. Open Updates → **Install / Update SDK Mod** if needed (also refreshes bundled ActorScriptDeployer).
3. **Fully restart Borderlands 4** after the SDK install so the SDK and bridge load.
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3) (installable from MSBT Updates).
