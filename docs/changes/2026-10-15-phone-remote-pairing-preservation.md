# Phone remote pairing preservation

## Symptom and evidence

After v2.39.2 publication, Martin reported the phone would not connect. Fresh
readback verified the installed full SDK2.39.2/f6bca3d0 was running with one player
on49774, with the installed desktop app on49775. The desktop Mobile Pairing page
reported Remote AFK connected. The phone showed SAVED, the remote PC label,
address `Remote AFK`, and a fallback LAN port; Connect produced the Wi-Fi error.
No credentials or private QR payloads are recorded here.

## Root cause and correction

Android `saveConnectionFields()` rebuilt a LAN-only object and discarded the
`remote` credential object even when saving an unchanged remote setup. Its
placeholder address survived, so later connection attempts probed invalid LAN
addresses. This is a source-backed reproducible failure path; the exact earlier
user click that caused the phone state was not observed.

`mobile_controller/app/src/main/assets/app.js` now preserves a remote setup on
Save Setup, disables its irrelevant manual LAN fields, and explains that scanning
a local QR switches connection type. A missing remote object with the old
placeholder address is no longer marked paired; Connect requests a fresh Remote
AFK scan rather than probing ports. Existing missing secrets require a new scan;
the fix cannot recreate them from a label.

## Validation and deployment

`electron_poc/test_mobile_afk.js` exercises the actual page: save/reload retains
remote credentials, Connect uses remote transport, the broken old entry gives
specific recovery guidance, and LAN fields unlock when leaving remote setup.
That suite and test_phone_reconnect.js pass. JavaScript syntax passes. Android
assembleRelease/lintRelease passed. Local candidate7437dca9 installed in place
on the attached phone; its assets match source and archive integrity passes.
Current badge correctly shows OFFLINE for the damaged placeholder entry. Scanner
opened to restore the missing credentials from the desktop upper Remote AFK QR.
Martin confirmed "Connected now" after the fresh remote QR scan. No version bump, tag,
release asset replacement or publication is authorized by this repair alone.
The published Android1.6.4 artifact remains unchanged for rollback. Windows/game
processes and the active AFK lobby are preserved.

## Phone confirmation

Martin confirmed the phone connected after scanning the upper Remote AFK QR with
the corrected local APK installed. This verifies restored phone connectivity;
no new gameplay mutation or full mission replay was performed for this repair.
The local fix is not included in the published v2.39.2 / Android1.6.4 assets.

## Published inclusion

Martin explicitly requested "include it" after confirming phone connection.
Released Windows/full and standaloneSDK2.39.3 plus Android1.6.5/build38.
All13 release assets, rolling updater metadata, actual publicAPK and README
verified; CI passed. The finalAPK pairing JavaScript byte-matches the confirmed
local candidate. Phone was detached during the version-only rebuild, so a fresh
physical1.6.5 installation is not claimed. See [verification](../releases/VERIFICATION_v2.39.3.txt).
Public download: https://github.com/funkyoushift/MattsSDKBoostingTools/releases/tag/v2.39.3
