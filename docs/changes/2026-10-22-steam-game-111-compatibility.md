# Steam game 1.11 compatibility repair — 2026-10-22

## Symptom and verified cause

Steam updated Borderlands 4 to app build 26007962. The installed executable is
SHA-256 `ba75f7c2874b16efb5536a5c0cc28918a03efd3e55d790d2e4db57de0c3a353a`,
PE timestamp 4086165580, image size 652288000. The public v2.39.5 SDK only
recognized Steam 25372571 and Epic 4845623. Mission commands failed at exact
executable selection before a mission snapshot. Direct inventory, cards, and
farming also had separate old-build gates.

## Change

An isolated `codex/steam-26007962` checkout from public v2.39.5 adds a new
exact-hash mission profile. The [native receipt](../native-missions/STEAM_26007962_PROFILE.json)
records 41 mapped code/data locations and 27 complete function spans against
the installed Epic baseline. Twenty-five bodies match after only relative
branch/RIP relocation normalization. The other two have exactly three reviewed
native field-displacement bytes: challenge definition fields `+0x498→+0x4a0`
and `+0x490→+0x498`, and player DLC access `+0x32c0→+0x32b8`.
Four independent complete-body-matched callers identify the changed challenge
callback. No Python raw access uses these changed offsets. Every runtime
fingerprint is pinned to the new executable. Character-loader and dialogue
profiles add ten unique, complete-body-matched functions; the loader's focused
slot offset is unchanged by those bodies. Automatic character selection on
this build remains unverified and is still reported as such.

The farming profile adds the measured PE identity, exact drop and weighted-roll
contexts, and charge getter/data/vtable mappings. The drop and roll containing
functions have matching complete normalized instruction layouts and branch
destinations. A legacy glide trampoline remains restricted to its original
Steam build. These farming source changes have **not** been installed or
exercised in game.

Full Game preview now warns that its mission, discovery, and challenge catalogs
were extracted from game 1.10. New or changed 1.11 content is not yet covered;
the UI must not claim complete 1.11 coverage from the older catalog.

Save-backed Mission Selector initially rejected `begin` on Steam 26007962
before creating a native lease or editing a save. The desktop records this
known preflight rejection from an older SDK as a closed, retryable failure
instead of leaving an uncertain active replay that would lock mission controls.
A current game-1.11 character save became available after a normal Save/Quit.
Two private copies of the character and profile were backed up outside Git;
the post-exit character copy decrypted, parsed, and re-encrypted with identical
YAML. An authored Mission Selector rewind on a separate copy preserved the
character identity and unrelated data and also survived encrypt/decrypt. A
character-specific temporary SDK then ran that replay in a solo Steam game:
the native lease closed at `ready`, and the game autosaved the selected mission
as `Active` at cursor 0. With this live result, the temporary 1.11 `begin`
block was removed from product source. This validates one character and
mission, not all 1.11 saves or the complete mission catalog. Existing replay
restore remains available for earlier runs. A pre-existing Windows catalog checksum blocker was traced to Git
line-ending conversion: the checked-in practice catalog hashes to
`04de7048793242fcc94e87cea710a97e46b4b94f52337ecc838b77bd10ad5fdb`,
while Windows checkout and packaged CRLF bytes hash to
`40b7d0ad5bac5c42cafe567c90ae11ecd7b8db3810b2d55c6be9b204e90d2347`.
Normalizing only CRLF to LF yields a byte-for-byte match with the committed
catalog. The integrity helper now accepts exact content with either newline
style and rejects other content changes, while preserving the recorded digest
for bookmark identity. The station catalog's recorded digest matches CRLF, so
both newline directions are checked without changing either catalog or its
stored hash. A previously captured bookmark containing the old Windows CRLF
digest is accepted when the current catalog still matches byte-for-byte after
line-ending conversion.

## Validation and limits

Offline: 8 mission-profile checks passed; 3 historical executable tests skip
because Steam replaced its older executable. Two new farming profile checks
passed against the installed binaries. The Quick Menu/no-BLImGui suite passed
(5 tests). The focused new-build, catalog, and replay-runtime suite passed
(44 tests, 3 historical skips). All 56 desktop replay-service tests passed,
including the new preflight rejection. Python syntax and `.sdkmod` archive
CRC checks passed. The Electron mission replay panel's UI test passed with
stubbed actions; no live save operation was made. Broader
farming tests had 60 passes, one historical executable skip, and six unrelated
environment/fixture failures (missing `unicorn`; old bridge stubs lack
`full_progress_conflict`). These do not prove native farming execution.

Live Steam: a temporary SDK built **before** the farming and Full Game warning
edits was installed while the game was closed. The installed archive SHA-256 is
`9d202b5e4fd88d8d42086a68100a461af688cb80fc663017c2589a18b74e2d66`.
The game loaded, the bridge reported that exact archive, and read-only mission
calls succeeded: 21 story missions previewed, 14 DLC pack access reports,
Full Game preview allowed in a solo lobby, and a three-section practice
preview with no blocked sections. A current-mission preview correctly reported
that no single shared mission was tracked. No mission completion, replay, save
edit, item delivery, or native farming patch was issued. This is host/read-only
proof, not complete mission playthrough, guest-save proof, or crash resolution.
The operator's input was detected while opening the pause menu; UI control
stopped and the game was left running.

## Deployment, rollback, and follow-up

The pre-test installed SDK was copied to
`C:\src\MSBT-Workspace\local\steam-26007962-before-test.sdkmod` with matching
SHA-256 `6fd71cc4075a16496c5f439a874d4dfe0db8df903bf5d7f4ec57ae701571c1af`.
Martin closed the game for installation. The revised candidate was built,
CRC-checked (155 entries), and installed at the Steam `sdk_mods` path with
matching SHA-256 `b1afc396ecfe01986a6276aa53eeb7c2b20368b141727807fc7995a4527aa03c`.
The previous temporary candidate is saved at
`C:\src\MSBT-Workspace\local\steam-26007962-mission-only-live.sdkmod`.
The source changes remain isolated and unpublished. Restore the backup if
needed. Steam was launched again for the final read-only smoke test; its
bridge loaded the installed SDK and reported an empty player roster at the
title screen; no character-level command was run on this restart. A subsequent
local build includes old Windows bookmark compatibility and has SHA-256
`f398656cc37c9cbd209f6a9f188d4537859551372f7c3be94a93a93a0d43c241`,
with 155 CRC-checked entries. Martin closed the game again and this final
candidate was installed with matching SHA-256. He later opened a Steam
character, loading the final package. Read-only bridge
calls on the final package returned a ready solo roster, 21 story mission
preview entries, Full Game preview `allowed=true` with the explicit 1.11
catalog limit, and save-replay status loaded with no active lease. No mission
write, save edit, farming patch, or Full Game run was issued. The installed
v2.39.5 desktop process was closed normally and a local Electron session was started from this isolated
worktree with its updated replay-service handling; its renderer reported the
worktree app path. This is a local development session, not an installed
desktop update or public release.

For the save-write probe, the final installed archive was copied to
`C:\src\MSBT-Workspace\local\steam-26007962-final-installed.sdkmod`.
A temporary archive changed only `mission_save_replay.py` and allowed `begin`
for the backed-up character GUID; its SHA-256 was
`92ceb78738c1c438ea89f4e6c914bdb3b4311b86136ba5d8ff6b961fccddc526`.
Martin closed the game, this local archive was installed, and he loaded the
same character. The live bridge reported that exact archive and solo
`world_p` state. An automatic replay of `Mission_Main_Grasslands1` checkpoint
0 reached `ready` with a verified pre-edit backup in
`C:\src\MSBT-Workspace\local\steam-111-replay-service-probe` and a closed
native lease. The game then autosaved the character; a read-only copy of that
autosave parsed with the same GUID, selected mission `Active`, cursor 0, and
initial travel objective active. The candidate bytes had changed because the
game itself autosaved. Martin then used normal Save/Quit and reloaded the same
character. The live mission preview still read `active`; a new post-rejoin save
copy decrypted with the same GUID, `Active` mission, cursor 0, and active
initial travel objective. The reload also reactivated
`mission_main_shatteredlands1b`, a later mission already listed among this
selection's 36 future missions. The first game-written autosave had only the
selected mission active; after normal exit/rejoin there were two active story
missions. The selector therefore does **not** meet the requested rule that only
the selected mission be available. No guest was present. The character-specific
archive is a private test artifact and must not be published.

The staged save showed the exact reactivation path: its
`missionset_main_shatteredlands1` record had no missions but retained
`cursorposition: 1`. On the first game load, the first future sibling was
recreated as completed; after normal exit/rejoin, the second sibling became
active. `mission_selection_state.py` now removes the stale cursor when a
future-owned set becomes empty and removes that set if no other metadata
remains. A synthetic chained-set regression and a new edit of the backed-up
1.11 character copy passed: the future set was absent, unrelated fields and
character identity were preserved, and fog stayed unchanged. A second,
character-specific live replay reached `ready` with a verified backup and a
closed lease. Its first game-written save contained only
`mission_main_grasslands1` active and no
`missionset_main_shatteredlands1`. After Martin used normal Save/Quit and
reloaded that character, live preview still read the selected mission as
active. The next save copy had a different SHA-256 from the first autosave,
still had exactly one active mission, and still omitted the future set. This
fix passed the specific reload regression seen in the first probe. It does
not prove all mission branches or all available side content are cleared.

The source guard removal and its replacement standard-lease test passed 63
focused replay/selection/catalog tests, 9 Quick Menu/native-profile checks,
and Python syntax. A rebuilt archive has 155 CRC-checked entries and SHA-256
`17b0c6acfa9833c91f4843bd04d47f5ca017b15805020c43c590170a590358d0`.
It has exactly the same members as the prior final candidate, with only
`mission_save_replay.py` content changed. After the game closed, the exact
service backup from before replay was checked against its recorded SHA-256 and
same character identity. A private copy of the changed save was retained,
and the pre-test character save was restored byte-for-byte while the game was
closed. The profile save was not manually edited. The unrestricted rebuilt
archive was briefly installed but never launched; the character-specific
probe archive was reinstalled after the second active mission was found.
After the successful second reload, Martin closed the game. The second probe's
pre-edit character backup matched its journal hash; the post-reload save was
retained privately, and that pre-edit backup was restored byte-for-byte while
the game was closed. The profile was not manually edited. The unrestricted
Steam candidate was then installed from this checkout with its expected SHA-256
`17b0c6acfa9833c91f4843bd04d47f5ca017b15805020c43c590170a590358d0`;
the private character-specific probe was archived outside Git. The game
remains closed. The desktop change is available in the local worktree Electron
session but has not been installed as a public desktop update. There is no
public release.

Direct inventory/card delivery stays blocked. The updated insert body changed
from 1,873/424 to 2,330 bytes/540 instructions and two guest-transaction
functions have no complete match; copying old offsets would be unsafe. The
installed 1.11 IoStore content has no local extractor and no full 1.10 asset
baseline, so new mission/map/challenge identities are not yet diffed. The
current-save copy and the second live save-write/reload passed the observed
future-mission regression. Broader mission coverage, Epic behavior, and guest
persistence remain unverified. Do not claim 100% of game 1.11 or a public
release.

The final focused checkout checks passed: 65 Python replay/selection/Quick
Menu tests, Python syntax, 56 desktop replay-service tests, two Electron
replay-panel tests, the phone replay-route test, and archive CRC for all 155
SDK members. The local Electron session still runs from this checkout. An
installed desktop build was not replaced: this checkout does not contain the
bundled setup and Python resources required by its normal packager.

## Epic installation inventory, read-only

The completed Epic installation is at `C:\Program Files\Epic Games\Venus`.
Its launcher manifest has no build-version value, so no Epic patch number was
inferred. The Epic main game executable is 612,202,784 bytes, SHA-256
`6d531d91011ae0d67ac461a3cacabc99993c279bf325dfe70ff1af00ec43c87e`,
which differs from the installed Steam executable. The checked Epic and Steam
`unrealsdk.dll` files match byte-for-byte (SHA-256
`d9936cbe3da434743a93e0dadc2f6a5cc82102936c1c249db014a3081fdb4433`),
as do the checked `pyunrealsdk.dll` files (SHA-256
`a12534c6b8b411a176c62ed9d7226031b0039727112dce175bcc71c691761a54`).
This was only a file inventory; Epic was not launched or modified.

## Current Steam and Epic release qualification

The current Epic executable now has an exact-hash mission, character-loader,
and dialogue profile. [The qualification receipt](../native-missions/EPIC_6D531D91_PROFILE.json)
and reproducible comparison mapped 51 native locations against current Steam
26007962; 37 complete function bodies match after only relative branch/RIP
relocation normalization, with no missing or conflicting references. Exact
executable selection and runtime fingerprints remain required. Fourteen focused
mission/dialogue/Quick Menu checks passed and six historical baseline checks
were skipped because the old installed Epic executable was replaced. Epic was
not launched; its live missions, saves, and multiplayer remain unverified.

Direct inventory, guest item transactions, and native card mapping remain
gated on Steam 26007962. Read-only comparison of the installed game found all
four reviewed direct-inventory spans and all six reviewed Epic-derived gate
spans mismatched; no safe native port was inferred. Focused tests confirmed the
actual Steam executable is rejected before native callback binding or memory
access: 57 tests and 130 subtests passed. A bounded search of local receipts,
managed worktrees, and game staging locations found no older complete game
executable for a fresh full-body comparison. No item is sent on this build.

The separate safehouse capture repair was integrated into this Steam branch.
It applies the authored `Claimed` PoA effect through live native world state
after a safehouse mission reads completed; it does not edit the save or travel.
Integration checks passed: 40 focused tests, six historical skips, and Python
syntax. The Steam test SDK with this change was installed while the game was
closed; the prior SDK was backed up outside Git. A targeted solo job then
observed Abandoned Post's loaded PoA actor already `Claimed`, its two discovery
entries already discovered, and its travel requirement already `Completed`;
no state write was issued. Martin observed the map/fast-travel entry unlocked,
including after Save/Quit and reload. The repair's causal effect on an
unclaimed safehouse remains unproven, as does guest persistence. The game was
closed after this check. This is not a public release.

## Official 1.11 notes checked

The [October 22 update notes](https://store.steampowered.com/news/app/1285190/view/705534727891717219?l=english)
describe changes directly relevant to mission testing: first-time Story Pack 2
multiplayer start, objective progression when enemies die or areas are reached
early, mission state after save/load, door/elevator interactions, fast travel,
discoveries, and challenge progression. Bounty Pack 5 also changes a second
fast-travel unlock. These are reasons to requalify the mission catalog and
guest behavior; the notes do not establish that MSBT caused a reported save
failure or that the Abandoned Post console is fixed. The patch notes were
retrieved from the official Steam news API when the linked store page returned
an access error.

The separate `codex/safehouse-full-progress` candidate handles the authored
PoA `Claimed` effect omitted by bulk mission completion. It is not merged into
this installed Steam candidate: current 1.11 PoA state, map unlock, and guest
save effects have not been observed live, and the patch notes confirm other
mission state and fast-travel changes. Its offline evidence remains in
[the safehouse repair note](2026-10-22-full-progress-safehouse-claim.md).
