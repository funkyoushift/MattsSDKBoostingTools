# Epic farming profiles and party-player controls

Matt asked whether every new control supports Epic and other players, and requested
the missing support. He then instructed completion using game files and available
local evidence without arranging guest/Epic testers. This authorizes a local fix,
not another public release or version bump.

## Evidenced cause and implementation

Public 2.33.0's native chance, weighted-roll and skill-charge paths only accepted
Steam's module fingerprint/addresses. Character controls called local() and held
one host state, so a target selector could not redirect them to guests.

New farming_builds.py contains separate exact Steam 25372571 and Epic 4845623
profiles. guaranteed_drops.py selects the correct chance site; farming_native.py
selects the weighted-roll context; farming_skill_resources.py selects the charge
getter, struct global and both vtables. Header, full site bytes, live ScriptStruct
identity, native/SDK charge readback and array/ownership bounds remain mandatory.
Unknown/modified builds fail closed. Reflected controls do not use storefront RVAs.

Read-only qualification against both installed Win64 executables is recorded in
../native-farming/EPIC_PROFILE.json. Steam SHA256 is
9c3afb7dc6a550a6c2e817846cd2c40ff11e066dc6aefeb819f802e6a4c5c3e0;
Epic SHA256 is
764a4bb5403a2619a0be627de5a738e23ea021e8672f7f0e7a536697d4a06719.
Only branch/RIP displacements were normalized. The chance context is unchanged;
weighted-roll moves from 0x3DA8C3A to 0x3D9E2D2. A unique 870-byte wrapper
construction body maps 0x11BB61E to 0x11B947A and identifies Epic wrapper vtable
0xB40FB50. Ten methods for each wrapper/charge vtable match instruction layouts;
Epic charge vtable is 0xB623800. Generic short methods alone produced ambiguous
candidates and were rejected as identity evidence. No Epic function was executed.
tools/qualify_farming_builds.py repeats the read-only comparison; tests independently
check full EXE hashes and all retained qualification spans.

farming_targets.py resolves current PlayerState/controller/pawn identities for
Local, Named Player, Other Players and All Players. A name-bearing request never
falls back to a reused index or host. Missing/unloaded/ambiguous players fail.
Selection is not mutated by the farming action. Host authority is required.

farming_controls.py now tracks each player's enabled features, readbacks, errors
and original fields independently. Turning one player's control off preserves
another's. Disconnect/respawn disables the old identity; world travel and mod
disable restore all. A transferred object cannot acquire two restoration owners.
Expired/externally changed fields retain the existing cautious restoration rules;
failed restoration keeps its snapshot. Changed reflected fields request native
ForceNetUpdate on their controller, pawn and equipped weapons.

Live reflection marks InfiniteAmmoLock/InfiniteClipLock, fire rate, spread,
accuracy impulse, recoil scale and VaultPowerCost_Glide as CPF_Net. This supports
the replication route but is not guest gameplay proof. God Mode is authoritative
server damage permission; skill resources use existing SDK APIs on the resolved
owned pawn and components. Weighted Loot High Roll and Vendor Refresh remain
explicitly Whole lobby effects, as does 100% Drop Rate; they benefit guests but
cannot promise exclusive loot changes for one selected player.

backend_actions.py routes HTTP and F7 farming actions through the target resolver.
F7 uses the current named target, defaulting to local when none is selected.
renderer.js/html add synchronized target pickers to weapon, character and glide
controls, send explicit scope/name-bearing payloads and display per-player/mixed
On/Off status. Global controls never pretend to be per-player. All 14 controls
remain discoverable through feature search. Android's shared desktop asset build
includes the same changes.

## Validation and local deployment

70 focused tests passed for farming, independent players, transfer ownership,
scope/selection, missing guests, disconnect/respawn, HTTP/F7, Steam/Epic native
roundtrips, corrupted-site refusal, charge bounds/readback, clean SDK import and
no-BLImGui. Five cleanup/status and five Quick Menu tests passed in separate
processes (80 total). Existing cleanup-test stubs leak fake modules into later
tests when mixed in one interpreter; separate runs avoid that unrelated fixture
pollution. Unicorn assertions pass with pytest's faulthandler plugin disabled to
avoid reporting handled native JIT exceptions as fatal Windows diagnostics.
Full SDK compileall passed.

Real Electron DOM tests passed the target request payloads, shared pickers,
individual/mixed status, global labels, ordinary buttons and category placement.
Feature search passed all 14 routes/13 queries in Workspace and Classic.
Hidden test renderers emit nonfatal GPU shutdown diagnostics after assertions.

The local candidate was loaded using the existing MSBTFarmingLab game-thread
bridge, without restarting Borderlands PID 5604. Candidate copies match shipping
source except decorated travel hooks omitted from the copied controls: the existing
add-on owns travel callbacks/pump. An adapter delegates HTTP actions to the new
resolver/controls; no arbitrary execution endpoint was added. All 14 controls
passed On/status/Off/restored checks through the actual /action HTTP route, and
an explicit missing guest was rejected. All controls finished OFF with zero owned
scalar fields. Independent read-only Windows memory checks confirmed weighted
native original -> jump -> original restoration.

Useful failed probe: the old file bridge's direct set operation drops target
fields and calls set_feature locally. The initial missing-guest check therefore
exercised that old helper, not the production route. The trial was corrected to
HTTP; missing guests are refused there. No production fallback was introduced.

The source desktop was restarted after stopping only MSBT Electron; native window
inventory confirmed the candidate panel. The installed stable desktop/game SDK
were not overwritten. Game SDK remains 2.32.0 with the candidate local adapter;
public v2.33.0 and all its downloads remain unchanged. No new tag/version/release.

Local SDK artifact: work/artifacts/MattsSDKBoostingTools-epic-party-local.sdkmod,
SHA256 2780ef4be3806914ccdf5404b32bedf853c7f2bbf4d7b38f25a91510e2e39f75.
All 79 Python files match source and the archive passes ZIP integrity checks.
Local Android assembleRelease/lintRelease passed; APK signature verified using
the existing certificate. renderer.js/workspace.js match source; renderer.html
has only the expected generated mobile shim injection. APK:
work/artifacts/MSBT-Mobile-epic-party-local.apk, SHA256
9bccfe8628bcf2c44848a9020c5d4c9f224c7503186d591413445e546dc2489e.
No physical phone installation or new Android native UI proof is claimed.

Epic live execution and actual guest gameplay/replication remain unverified.
Local API activation/restoration is not gameplay proof for duration/weapon effects.
The earlier owner gameplay confirmation applies to the earlier host-local build.

Rollback: All Off through the existing bridge, restore local add-on engine.py from
work/party-candidate-rollback/engine.py and reload it with controls OFF. Close the
source desktop and launch the unchanged managed desktop. Remove the candidate
subfolder only while the add-on/game is not using it. Preserve the native allocation
until process exit; do not free it while callers may still return through it.
The dirty primary checkout was preserved; work is isolated on codex/epic-player-farming.

Release authorization and packaging: Matt subsequently requested "release it as a
finished product" after the limitations above were reported. Prepared integrated
v2.34.0 / Android 1.6.2 (code35), source identity 351b42e. Windows builder/full npm
checks, packaged farming/party/drop-rate/search and three-process settings restart
checks passed. All 79 SDK Python files match source; bundled SDK/manifest identities
match. Android build/lint/signature/source checks and owned read-only emulator
install/launch passed. No physical phone, Epic live or actual guest gameplay proof
is claimed. Release/public/deployment details are tracked in
../releases/VERIFICATION_v2.34.0.txt. Borderlands was observed closed during release
packaging, permitting normal SDK deployment after public verification.

Publication/deployment complete: v2.34.0 stable, 11 public asset hashes verified,
release-policy/Pages checks passed. Verified public portable installed through
managed installer; desktop reopened and installed identities/startup passed.
Game was closed; normal Steam SDK integration completed and its hash matches the
public SDK. Separate local lab and loader archived outside sdk_mods under
work/installed-farming-lab-before-v2.34.0, preserving rollback. Previous desktop
and game SDK also retained. Launch Borderlands normally for integrated controls;
no console bootstrap is needed. No game restart/live guest/Epic claim is made.
