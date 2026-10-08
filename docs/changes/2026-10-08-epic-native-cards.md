# Epic item-card compatibility candidate

Symptom: DJBP's Epic editor displayed `Game cards are not supported by this game
build`. Released v2.30.2 recognized Epic for inventory delivery but the card probe
explicitly admitted only Steam; its calls and ownership-vtable checks were Steam
addresses. Removing that guard alone would not supply Epic's addresses.

Read [Epic profile evidence](../native-cards/EPIC_CARD_PROFILE.md) for executable
hashes, exact function locations, recovered correspondence, validation and limits.

Changed runtime modules: `native_card_builds.py` (strict profile map),
`native_sdk_card_probe.py` (profile-specific gates/calls and price ownership),
`native_sdk_widget_probe.py` (widget calls/owner identity),
`native_preview_service.py` (test revision in diagnostic status).

Added deterministic read-only comparison/verification tools, profile and cleanup
tests, and `Check-EpicCardBuild.ps1` for DJBP's installed-file/running-revision
diagnosis. All 26 code spans matched, 9,221 normalized instructions, no conflicting
shared references. Never use the first candidate for a generic destructor wrapper;
constructor vtable evidence resolved the ambiguous matches.

23 probe/cleanup/status tests, five profile tests and five startup/bridge tests passed;
syntax and actual-file profile verification passed. Epic has not been booted or
tested live. No guest-save or in-game card parity claim. Research model export
remains Steam-only; production widget preview has the Epic mapping.

Local test packaging retains version 2.30.2 and isolates only card changes. Keep
the previous SDK for rollback. Do not publish this as a verified Epic release
before the live test; no public release or local install was performed.

Final local handoff: `output/epic-card-research/DJBP-Epic-Card-Test-20261008.zip`,
SHA256 `6cc639144aed7598ce2100b599461e8830f762279560da974abfc7ad7448780e`.
Contains the test SDK, read-only build checker, instructions and build receipt.
Compared to the downloaded public SDK, exactly three card modules change and
one is added; all other bytes are preserved. All 71 packaged Python modules
compile. Full receipts: `package-verification.json`, `release-payload-diff.json`,
`verification.json` in the same private output directory.


## Combined release status - 2026-10-08

Published in normal stable MSBT v2.31.0 with Android 1.6.0 after Matt explicitly approved inclusion of the offline-checked Epic profile with its live test pending. This supersedes the local-only publication status above. All 11 public release assets were downloaded and hash-verified. Packaged smoke/restart checks and Android installed-APK verification passed. See docs/releases/VERIFICATION_v2.31.0.txt for hashes, CI, evidence limits and rollback. Historical test-candidate hashes above identify the earlier local package, not the combined release. Epic live rendering remains unverified; no new guest-save claim.
