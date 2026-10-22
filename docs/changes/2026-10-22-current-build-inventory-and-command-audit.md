# Current-build inventory and command audit — 2026-10-22

## Symptom and cause

After BL4 game 1.11, direct inventory delivery rejected the new Steam executable before sending an item. Mission commands had a separate obsolete game-build gate. Existing native card and joined-client inventory profiles also reject the current executable. The two desktop Guest Grid developer buttons had no backend handlers even in v2.39.5.

## Change

`direct_inventory.py` now admits only the exact installed Steam 26007962 and Epic 6d531d91 executable hashes with seven native code/data gates each. The current native caller establishes the host item identity constructor, insertion interface/arguments and destructor lifetime. Host delivery remains fail-closed if the full executable identity or any gate differs. The shared direct-delivery queue handles local, selected, all and nonhost destinations; bookmark, code, Shiny and AFK sends feed that queue. Bridge alias tests cover the four serial payload fields across destinations. The unrelated, unreliable Guest Grid fog-of-war experiments and their unused desktop wiring were removed at Martin's request; Party Reveal Map remains available.

`guest_inventory.py` and native cards remain gated on the current builds. Current guest transaction code changed its flag mask and serializer, and a safe constructor/validator mapping has not been recovered. An authority-controlled P2 target may use the host direct path, but no guest was available to verify P2 delivery or saved progress. Locally joined-client Give Local is not enabled by the new host profile.

## Validation and limits

Offline: 48 focused direct-inventory checks and 130 subtests passed. Thirty-two bridge alias combinations passed. An action-route audit found 72 HTML references (62 distinct), plus 25 literal JavaScript calls (21 distinct), with handlers for all except intentional pattern-based UVH tier dispatch. The broad Python run had 1,498 passes, 23 skips and 19 failures; all 17 historical failures reproduced on clean v2.39.5, while two new evidence tests require an older Epic binary that is no longer installed. These results do not prove gameplay execution of every command. Electron `npm run check` passed after the pinned, byte-matched bundled SDK archive was staged locally.

Live Steam: a private pretest copy of slot 16 and profile was made before installing a local v2.39.6 candidate. A single existing item code sent to the host appeared as an additional backpack row while the original equipped item remained. Six more user-supplied codes then each increased by one in the full live inventory; backpack count rose from 620 to 626, with no truncation and no game crash. The game was then closed at Martin's request. No Save/Quit/reload persistence proof was obtained for these items. No Epic process was launched. No P2 lobby was available.

The first capped Backpack read showed only one matching serial after a send; that was an incomplete diagnostic because its 48-item cap includes equipped rows and deduplicates serials. The full Inventory read showed the equipped original and the appended backpack copy. A native `returned` event alone is not proof of receipt; the full inventory readback is the evidence used here.

## Later Steam 1.11 trainer-control check

With the current-build card candidate loaded in a solo Steam game session, the
bridge's `drop_rate_on` action returned `active=true`, `owned=true` and
`conflict=false`. The immediately following `drop_rate_off` returned
`active=false`, `owned=false` and `conflict=false`, confirming the native patch
was accepted and its original bytes restored. The game remained running.
This is a live activation/restoration check for the FLiNG-derived 100% Drop Rate
control, not a loot-outcome or probability test. No other trainer-derived
effect was inferred from it.

## Deployment and follow-up

The local Steam SDK was backed up outside Git before installing the candidate. Release packaging and publication status are recorded in `docs/releases/VERIFICATION_v2.39.6.txt`. If this candidate causes problems, restore the previous SDK backup or reinstall the prior public release. Joined-client delivery, host-to-P2 receipt and guest-save persistence, native item cards, and complete current-build command execution remain open. Do not claim those paths work from the host test.
