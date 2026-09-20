### What's new

- The desktop panel keeps its designed dark colors when Windows is in light mode, Contrast, or High Contrast. Button chrome and sidebar rows no longer pick up the system yellow forced-color outline.
- Epic Games Launcher installs are auto-detected. Install SDK Manager and Detect Folder now find Borderlands 4 from Epic default folders, launcher manifests, Legendary, and Heroic, then copy oak2-mod-manager into that game tree. Steam paths are unchanged.
- If auto-detect misses a custom install, browse the game folder, `OakGame\Binaries\Win64`, or `sdk_mods`. The app maps those back to the correct `sdk_mods` path. Errors say whether Steam, Epic, or no game was found.

### Downloads

Choose **MSBT-Installer-v2.12.1.exe**, or extract **MSBT-Portable-v2.12.1-win-x64.zip** for the portable app. The matching SDK mod is bundled and also available separately.

The Android controller remains version 1.1.0. Its existing APKs are included so mobile downloads continue to work.

Requires oak2-mod-manager v0.3. Close Borderlands 4 before installing an SDK mod update.

### Validation

Offline checks cover the appearance lock (file-content asserts), oak2 Epic/Steam locate helpers with fake Epic manifest and Legendary/Heroic layouts, and the existing `npm run check` suite the installer build already runs. Live Epic and Steam installs were not required for those tests.
