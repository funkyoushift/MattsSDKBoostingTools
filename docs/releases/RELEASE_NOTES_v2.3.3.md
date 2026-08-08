### What's new

**v2.3.3** - Infinite Jump FPS follow-up (idle path no longer spams UE writes).

#### Infinite Jump performance
- Camera checks ~10 Hz (0.1s); heavy party `find_all` every ~3s (or on world change)
- Read jump counters first — skip move resolve and writes when already ready
- Solo/local idle path avoids party walks after local index is cached
- Jump pre-hook no longer falls back to expensive `find_all`
- BLImGui duplicate path aligned; Jump/CanJump prep unchanged so IJ still works

#### Upgrade notes

1. Install `MSBT-Installer-v2.3.3.exe` (or extract the portable ZIP).
2. Run **Install / Update SDK Mod** from the app Updates tab.
3. **Fully restart Borderlands 4** so the bridge and live actions load.
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).
5. Retest Infinite Jump FPS vs IJ OFF (standing/walking idle should stay close).

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.3.3.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.3.3-win-x64.zip`

**Do not manually download these unless you know why**

- latest.json, latest.yml, *.blockmap
