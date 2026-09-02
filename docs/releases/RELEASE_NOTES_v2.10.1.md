### What's new

**v2.10.1** — stabilization patch for Dev Spawner, Hoard Builder, and Clear Spawned Actors.

- **ASD restore:** Default spawn uses original ActorScriptDeployer `_cmd_spawnai`, not `asd_hybrid.spawn_live`. Hybrid is wrap-only (census / clear / seal throwaways).
- **Clear Spawned Actors fix:** `note_after_asd_spawn` polls for delayed ASD pawns; watch labels and reconcile so clear actually destroys tracked enemies.
- **Built-in Python:** Electron `pythonCandidates()` skips missing `.venv` / bundled paths so serial tools and Matt Editor host work when only system Python is available.
- **Safeguards:** `docs/STABILITY_GUARDRAILS.md`, regression tests in `test_asd_spawn_restore.py` / `test_asd_hybrid.py`.

v2.10.0 features (Party Reveal Map, Host Clear Fog, Hide Fog, Late Join experimental) are unchanged. **Replace the `.sdkmod`** after updating — spawn/clear fixes live in the SDK mod.

**Not in this release:** CoS hijack, catalog 951 pump, item cards, guest-grid FoD, memory hybrid as spawn engine.

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.10.1.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.10.1-win-x64.zip`

**Android (phone companion)**

Unchanged. Same Mobile Controller **1.0.0** APK:

- Rolling APK: `MSBT-Mobile-Controller.apk`
- Phone install page: https://www.funkyoushift.com/MattsSDKBoostingTools/mobile-install.html

**Do not manually download these unless you know why**

- `latest.json`, `latest.yml`, `mobile-version.json`, `*.blockmap`

### Upgrade notes

1. Install this desktop update (or extract the portable ZIP). You do **not** need a new phone APK.
2. Open Updates → **Install / Update SDK Mod** (or copy `MattsSDKBoostingTools.sdkmod` into `sdk_mods`).
3. **Fully restart Borderlands 4** after replacing the `.sdkmod`.
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).
