# MSBT 2.31.0 — Epic item cards and full Android workspace

- Added native item-card generation for Epic build 4845623, including live Item Editor previews. The selected game's function checks remain enforced.
- Added **All Windows tools** on Android: the shared workspace, Saved Items, Item Catalog, community folders, and the bundled item/save editor use the existing PC pairing.
- The phone now retains unchanged large status lists between workspace sessions, reducing repeated transfers while players, AFK progress and command results remain current.
- Enabled normal phone commands and player selection during AFK, with existing delivery conflict checks preserved.
- Fixed Item Catalog confirmations exposing the hidden item-card rendering window.
- Improved AFK host-test error reporting and vault-card readback by track identity.

Includes Android **1.6.0**. Update both the desktop and phone for the shared workspace changes, and update the game mod and restart Borderlands 4 to load the Epic card support.

Verification: Epic addresses and layouts were checked against the installed executable, with offline guard and cleanup tests. Live Epic card confirmation is still pending. The separate vault-card rank-setting issue is not claimed fixed by the readback change.
