### What's new

**v2.3.4** - Fix F6 Unstuck still firing after you unbind it.

#### Quick Menu keybinds
- Unbinding **MSBT Quick Menu Unstuck** (default F6) now truly disables it
- The in-menu tick poller was still hardcoded to F6/F7 even after mods_base cleared the bind
- Poller now follows the live keybind assignment (unbound = no-op; rebound key works under UI capture)
- Same path applied to **MSBT Quick Menu** (default F7) close-while-open polling
- Golden Chest F8/F9 were keybind-only (no poller) and did not need this fix

#### Upgrade notes

1. Install `MSBT-Installer-v2.3.4.exe` (or extract the portable ZIP).
2. Run **Install / Update SDK Mod** from the app Updates tab.
3. **Fully restart Borderlands 4** so the bridge and live actions load.
4. Requires [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3).
5. Retest: bind F6 Unstuck → works; set Unbound → F6 does nothing; rebind → works again.

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- `MSBT-Installer-v2.3.4.exe`

**Manual install / portable Electron app**

Download and extract:
- `MSBT-Portable-v2.3.4-win-x64.zip`

**Do not manually download these unless you know why**

- latest.json, latest.yml, *.blockmap
