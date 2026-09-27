# Matt's SDK Boosting Tools v2.16.0

## AFK and mobile improvements

- Control the AFK lobby away from home through the built-in encrypted remote connection. No VPN app or port forwarding is needed. Keep MSBT and Borderlands 4 running on the PC. Desktop Mobile Gateway → Enable remote AFK shows a private QR for the updated Android app; Disable & revoke invalidates pairing. Remote access is limited to AFK controls and SHiFT open/close.
- Choose the random delivery size instead of always using 70. Guaranteed items count toward the selected total; a larger guaranteed list still delivers all compatible guaranteed items. Sending more than 70 remains password-protected. Character class rules still apply, and each joining player gets a fresh random selection.
- Finished guests wait for other observed players sharing their connection before auto-kick. Unknown connections wait for all current guests. Failed boosts retain players. Real split-screen multiplayer verification is still pending.
- See guest joins for the current AFK session and lifetime. Rejoins count again; split-screen players count individually. Lifetime totals are saved on the host PC.
- Organize serial bookmarks into named folders and subfolders. Create empty folders, move selected bookmarks, and browse a parent folder's contents. Existing saved groups and codes are retained.
- Open walkthroughs from the header in either desktop layout.
- Choose English, Spanish, French, Portuguese, German or Dutch for AFK controls and bookmark-folder actions. Other screens, walkthrough text and game-generated messages remain in English.

## Upgrade and usage

Install the Windows update and bundled game mod with Borderlands 4 closed, then reopen the game. The installer includes the SDK runtime, mod manager and SHiFT PAK and preserves newer SDK/manager versions. Update Android to **1.3.0 (26)** for remote AFK control and language choices. Re-enable remote access after restarting MSBT; pairing stays saved unless revoked.

Auto-accept still requires SHiFT open and captures game input. Closing SHiFT restores controls. Automatic backpack clearing/restoration is **not included or enabled** in this release; existing guest items are not automatically deleted.

## Validation

Desktop regression checks, AFK/bookmark/language UI checks, mobile parity, SDK syntax/import checks and AFK queue tests passed. Remote status was tested from the USB-connected phone with Wi-Fi disabled. Packaging checks verify the bundled SDK, installer, portable ZIP and updater metadata. Offline checks do not establish live split-screen behavior or guest save persistence.
