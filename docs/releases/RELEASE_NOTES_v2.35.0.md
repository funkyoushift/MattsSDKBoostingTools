# v2.35.0 - Mayhem unlocks and runtime repairs

## Mayhem 1-20

Choose one named player, enter a rank from 1 to 20, and use Unlock Mayhem.
The action raises that player's Mayhem unlock and enables the Takedown prerequisite
and rank access for the current lobby. It never lowers existing unlocks and does
not change the active Mayhem difficulty. Hardcore requires rank 5 or higher.
Reopen the terminal after applying. Save and quit normally to retain progression.
Guest players should check access in their own lobby.

The shared action is available through the desktop, native Quick Menu catalog,
and mobile action schema. Mayhem is separate from UVH 1-7. This does not complete
all story/side missions or award every mission reward.

## Runtime repairs

- Live bridge actions execute on the game thread. Timed-out requests retain a
  retrievable completion receipt; clients must reconcile before repeating them.
- Shared camera hooks verify registration and retain their fallback lifecycle.
- Party Reveal returns the actual start/failure message.
- Farming status checks resolve current party objects before reading live fields,
  avoiding reads through cached departed-player wrappers.

## Verification

107 focused SDK tests passed, including no-BLImGui startup/bridge checks.
Desktop Mayhem controls passed in workspace and classic layouts. The installed
candidate's desktop button raised the host from 10 to 20 while active difficulty
stayed at 10; Farming ON/status/OFF restored normal damage. Earlier guest feedback
confirmed rank 20, saved progression and Mayhem/Hardcore launch in the guest's own
lobby. These checks do not establish that every possible game crash is fixed.
Android 1.6.2 is unchanged and carried forward from the published release.

## Install

Use MSBT-Installer-v2.35.0.exe or extract MSBT-Portable-v2.35.0-win-x64.zip.
Quit Borderlands 4 normally before updating the SDK archive, then restart the game.
Requires oak2 SDK / mod manager v0.3. Hotkeys remain user-configurable.
