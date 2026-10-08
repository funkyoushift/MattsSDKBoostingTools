# Phone commands while AFK runs — 2026-10-08

## Report and confirmed causes

Matt initially reported the AFK host-test button doing nothing and Android refusing player selection. His saved desktop draft had Send selected loot enabled with both loot lists empty. The SDK rejected that start, but the desktop's next status poll replaced the error. Matt subsequently clarified that the priority was using ordinary phone commands while AFK remains active.

The connected Pixel 10 Pro XL was using encrypted Remote AFK pairing. That mode unconditionally disabled regular phone buttons and every player selector. Independently, the desktop relay accepted only AFK start/stop and SHiFT overlay open/close, and its status response omitted selected-player identity, host index, player readback and live-command state. AFK being active was not the UI restriction. Repeated writes to the native select value were another picker stability problem; the new regression failed against the original source and passes with the guarded write.

Work is based on c3f5a6f, Electron 2.30.2 and Android 1.5.1 (code 32), in `C:/Users/mwenn/.codex/worktrees/remove-markdown/working`. The primary checkout is older and dirty; its unrelated work was preserved. The isolated checkout also contains an independently authorized Catalog focus fix in main.js; the installed archive update below does not copy that unrelated diff.

## Behavior and components

- `electron_poc/remote_commands.js` explicitly lists the actions exposed by the phone and whitelists required status fields. `remote_afk.js` forwards those actions, Quick Menu reads and desktop bookmark reads. `main.js` supplies the same bookmark source used by the LAN gateway. Pairing, encryption, authentication, replay rejection, request expiry, reconnect and revocation remain in the existing path. Unknown routes/actions and malformed payloads are rejected. The bounded eight-second SDK wait fits the existing relay deadline; long actions retain the SDK's queued/still-running response and are never retried automatically.
- Mobile `app.js` enables normal controls and player selection when the desktop advertises `remote_commands_supported`. Older desktops retain their AFK-only lock with an explanatory message. `remote.js` permits the supported read routes and updates connection guidance. Commands carry existing explicit target identities; SDK queue and shared-operation admission checks still apply. This does not add concurrent manual item deliveries.
- Player dropdowns preserve existing option objects, avoid assigning unchanged values/disabled states, and exclude live player names from translation. An unchanged status poll no longer rewrites an open native picker.
- Desktop `afk_lobby.js` validates empty selected loot before dispatch and keeps a command error visible across status polls until the next command attempt. The retry button stays usable.
- Tests changed/added: `test_remote_commands.js`, `test_mobile_afk.js`, `test_mobile_parity.js`, `test_afk_lobby.js`.

## Validation

Offline/source: 81 Python checks passed across AFK, explicit mobile-target dispatch and Quick Menu/no-BLImGui startup/bridge suites; two existing loader deprecation warnings. Python compilation and changed JavaScript syntax checks passed. Actual Electron AFK, mobile parity and mobile AFK tests passed. Tests exercise remote AFK-active controls, explicit target forwarding, selected-player/readback status, bookmark/Quick Menu reads, unchanged AFK config/progress, propagated SDK busy rejection, unknown-command rejection, replay/expiry and offline/manual-busy locks. Remote persistence/background tests and all three real Electron close/quit modes passed. Earlier delivery-count and guest-progress checks also passed.

The existing encrypted relay integration test passed against the deployed relay using a separate temporary room and mocked game bridge, then revoked that room. This checked encryption, replay rejection, authentication and revocation without using Matt's pairing or issuing game writes. No server deployment was needed.

Native phone/game: release APK signed by the existing beta certificate built successfully and installed with `adb install -r`, preserving saved pairing and app data. Pulled the installed APK back from the phone; its SHA256 exactly matched the local build (`0537b6caf5ddb9b66261eb1fd9bbe5b091a27ac0299ed141056481cb2b772a7c`). The phone received the new remote capability and enabled regular controls. The native player picker stayed open through multiple polls and a third player joining. Selecting host `0 | FunkYouShiFT` reached the live SDK (`set_target_player`) and live player stats appeared. Tapping UVH Status on the phone reached `uvh_boost_status`; the phone displayed the SDK's successful status reply. AFK was enabled before and after both commands. These checks read status/select a target; no manual loot or progression command was sent by this validation. They do not prove every action or guest-save persistence.

Native XML evidence and compact receipts are under primary `output/afk-target-fix/`, particularly `phone-picker.xml`, `phone-picker-after-polls.xml`, `phone-target-selected.xml`, `phone-live-success.xml` and `verification.json`. Do not add full profiles, pairing credentials or inventory contents to notes.

## Local deployment and rollback

Installed desktop `AppData/Local/Programs/MSBT/app/resources/app.asar` was backed up before each local patch. First patch changed only afk_lobby.js. Second patch changed only remote_afk.js, new remote_commands.js and the bookmark callback in main.js, compared byte-for-byte across archive entries. Final installed SHA256: `8a9766165d86fbfcf9d5c41ec7e4d14996b7cf77e9534dd71503d5021f39cc30`. Installed controller modules match tested source. Original backup: primary `output/afk-target-fix/app.asar.before-afk-fix`; intermediate backup: `app.asar.before-remote-commands`. Restoring the appropriate archive while the desktop is closed rolls back these local patches; reinstalling the official signed Android 1.5.1 APK rolls back phone code while retaining app data.

Both desktop copies were closed normally and the corrected source desktop restarted with npm start. That current session also carries the independent Catalog focus fix. The installed shortcut carries this AFK/remote update. Borderlands 4 and its AFK session were not restarted. One earlier attempt to forcibly stop installed desktop processes was blocked by automatic approval review without a reason; normal close was used instead. A verification one-liner failed from shell quoting and was replaced by a saved verification script. No versions, release tags, public assets or relay deployment changed.

## Separate readback investigation and remaining limits

During Matt's own subsequent host test, vault-card rank verification reported 25 where 9999 was requested, and intentionally retained the host in the lobby. No automatic replay was performed. Source `Game.experience_level` in `afk_lobby.py` was made consistent with the setter's identity-based row lookup, with a reordered/missing-row regression in `test_afk_lobby.py`. A bounded live replacement changed only that read method while AFK/delivery was stopped and saved the original in `Game._readback_before_20261008`. The actual player's experience rows were in normal order; before and after readings were identical (first three cards 25, last two 9999). This robustness fix does not resolve the reported rank-setter failure. A read-only definition probe did not resolve the live pointer fields. Investigation stopped when Matt clarified the phone/AFK priority.

No SDK archive was built/replaced. The source readback change remains available for review; the live read-only method replacement lasts until game reload and can be restored from the saved class method. No inventory/XP writes were made by these readback probes. Vault rank setting, manual delivery during AFK, every remote command, long-session use and new guest-save proof remain outside the successful live checks above. GZO submission still requires the local desktop gateway, as before.


## Combined release status - 2026-10-08

Published in normal stable MSBT v2.31.0 with Android 1.6.0 after Matt explicitly approved inclusion of the offline-checked Epic profile with its live test pending. This supersedes the local-only publication status above. All 11 public release assets were downloaded and hash-verified. Packaged smoke/restart checks and Android installed-APK verification passed. See docs/releases/VERIFICATION_v2.31.0.txt for hashes, CI, evidence limits and rollback. Historical test-candidate hashes above identify the earlier local package, not the combined release. Epic live rendering remains unverified; no new guest-save claim.
