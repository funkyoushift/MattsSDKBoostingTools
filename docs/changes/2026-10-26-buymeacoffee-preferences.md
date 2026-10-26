# Buy Me a Coffee support links and saved choices — 2026-10-26

## Scope and symptoms

Martin requested one FunkYouSHiFT development-donation destination, `https://buymeacoffee.com/funkyoushift`, across his website, GitHub and apps. Subtronics is excluded. Mattmab's Ko-fi belongs to a separate contributor and stays intact. The supplied branded QR was decoded locally with ZXing to exactly the requested URL; an HTTPS GET returned status 200 and a page titled Martin Wenn (FunkYouSHiFT).

The desktop app tour previously marked its current version as seen after every completion or skip, even when “don't auto-show” was unchecked. The mobile-app announcement saved its checkbox only through Not Now; Open Mobile Gateway discarded it, and reopening always showed an unchecked box even when suppression was stored.

## Changes

- `.github/FUNDING.yml`, `electron_poc/renderer.js`, and `mobile_controller/app/src/main/assets/app.js` now use the Buy Me a Coffee URL for FunkYouSHiFT support. The legacy Matt Editor/Ko-fi links and contributor credits are unchanged.
- The app tour stores version suppression only after explicit opt-out and clears it when the user opts back in. A previous dismissed-only walkthrough file no longer silently suppresses the tour.
- Mobile announcement dismissal and Mobile Gateway share one persistence path; manual reopening reflects the stored checkbox so it can be turned off.
- Windows and SDK move to 2.39.9; Android moves to 1.6.6/build 39. The standalone selector receives matching version metadata. The website is published separately from its current main branch.

## Evidence and limits

The focused Electron settings test covers checked/unchecked tour behavior, mobile-announcement opt-out and opt-in, and boot welcome across reloads. The full settings suite checks concurrent settings writes and movement/rarity/announcement restoration across complete app exits and restarts. Android JavaScript syntax and remote-AFK/pairing tests passed. The supplied QR and website source passed local validation. Build, packaged startup, public asset and hosted website checks are recorded in the release verification note once complete.

These are app/website preference and link changes. No live game mission or inventory behavior was changed or requalified. Rollback is the preceding v2.39.8 release and the previous website main commit; local save data is not migrated by this patch.
