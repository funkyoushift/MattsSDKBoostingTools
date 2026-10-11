# Serial copy quantity — 2026-10-11

## Report and evidence

Mario reported Give Items by Serial delivers one item even with 5 or 10 copies selected. The report does not identify the UI entry point or serial format; those details were requested. Inspection confirmed two frontend defects: `quickMenuSerialPayload` omitted copy expansion, and `expandSerialTextCopies` expanded only Base85 matches, leaving readable numeric codes unchanged. The latter also deduplicated explicit repeated codes. The desktop Base85 button path already expands copies; the reporter's exact case remains unconfirmed.

## Changes

- `electron_poc/renderer.js`: Quick Menu serial payloads honor the copies control. Dedicated delivery-row parsing preserves readable codes, case, punctuation, ordering and duplicates. Editor-only serial discovery/deduplication remains unchanged. One-copy submissions retain their original text, including already-expanded background deliveries.
- `electron_poc/test_serial_copies.js`: checks real outgoing desktop payloads for every recipient mode and Quick Menu payloads at 1/5/10 copies, readable and Base85 inputs, repeated rows, case, embedded Base85 punctuation, whitespace-separated codes and limits.

## Verification and limits

`node --check electron_poc/renderer.js`, `node electron_poc/test_serial_copies.js`, and `python tools/tests/test_quick_menu_no_blimgui.py` passed. Backend parsing/resolution/queue inspection preserves duplicate serial entries; no native insertion defect was established. These are offline payload checks, not live inventory proof. No test items were delivered.

Local source only: no version bump, packaged install or release. Rollback consists of reverting the quantity helper and Quick Menu payload edits, preserving unrelated renderer changes. If Mario used desktop Base85 delivery, inspect delivery receipts/native insertion results before claiming his exact problem is fixed.


## Reporter follow-up and authorized release

Martin supplied a follow-up screenshot showing desktop Give Items by Serial with readable numeric input, consistent with the verified expansion defect, then explicitly requested the fix and release. Isolated release checkout carries only the quantity changes over v2.37.0. Source commit 603194f. Version 2.37.1; Android unchanged 1.6.2. Desktop full check suite, serial payload regression, Python compile, Quick Menu check and 14 pytest release/import checks passed. An initial unittest invocation discovered zero tests and was replaced with the successful pytest run. Packaging/publication verification follows. No live inventory result is claimed.

Packaged verification passed: quantity regression executed against renderer extracted from app.asar, runtime dependency checks, 3259 asset checks, startup smoke and updater packaging. Installer and portable produced successfully; 11 release asset hashes recorded locally. No live inventory mutation.
