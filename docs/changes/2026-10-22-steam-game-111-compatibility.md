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

Save-backed Mission Selector now rejects `begin` on Steam 26007962 before
creating a native lease or editing a save. The desktop records this known
preflight rejection as a closed, retryable failure instead of leaving an
uncertain active replay that would lock mission controls. A read-only audit
found only a pre-update Steam save. Its decrypted YAML parsed, and an
encrypt/decrypt roundtrip of a temporary copy preserved the YAML tree, but
that cannot establish 1.11 save-write or reload safety. The original save's
hash was unchanged. Existing replay restore remains available for earlier
runs. A pre-existing Windows catalog checksum blocker was traced to Git
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
(43 tests, 3 historical skips). All 56 desktop replay-service tests passed,
including the new preflight rejection. Python syntax and `.sdkmod` archive
CRC checks passed. Broader
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
with 155 CRC-checked entries. This later build is not yet installed because
the game was running when it was created.

Direct inventory/card delivery stays blocked. The updated insert body changed
from 1,873/424 to 2,330 bytes/540 instructions and two guest-transaction
functions have no complete match; copying old offsets would be unsafe. The
installed 1.11 IoStore content has no local extractor and no full 1.10 asset
baseline, so new mission/map/challenge identities are not yet diffed. A
post-update Steam save and non-destructive copy validation are needed before
reconsidering the replay gate. Do not claim 100%
of game 1.11, save-write safety, guest persistence, or a public release.
