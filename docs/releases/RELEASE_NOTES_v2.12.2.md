### What's new

- Installer and portable Check Updates actually load electron-updater. v2.12.1 packaged `electron-updater` but omitted its runtime packages (`builder-util-runtime`, `js-yaml`, `lazy-val`, and friends), so GitHub installer users saw "Electron updater is not available in this build." That line is unpackaged `npm start` only; packaged failures now show the real module/GitHub error.
- Windows appearance lock and Epic SDK-manager auto-locate from v2.12.1 are unchanged.

### Downloads

Choose **MSBT-Installer-v2.12.2.exe**, or extract **MSBT-Portable-v2.12.2-win-x64.zip** for the portable app. The matching SDK mod is bundled and also available separately.

The Android controller remains version 1.1.0. Its existing APKs are included so mobile downloads continue to work.

Requires oak2-mod-manager v0.3. Close Borderlands 4 before installing an SDK mod update.

### Validation

Offline checks cover the updater gate (unpackaged-only copy), packaged asar presence of electron-updater plus its runtime graph, `app-update.yml` GitHub provider, publisher preflight for portable `app-update.yml`, the appearance lock, oak2 Epic/Steam locate helpers, and `npm run check`. No live GitHub updater call is required for those tests.
