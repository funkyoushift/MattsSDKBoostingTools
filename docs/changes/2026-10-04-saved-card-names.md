# Saved and community item names follow their cards

Local desktop correction after v2.29.1; version unchanged, no publication.

Saved Items and Community Folders previously displayed imported bookmark labels
even after their resolved card showed a different item name. The shared loader
now publishes a name after successfully loading the matching image: native
`widget.Name`, or matched GZO `itemCard.name`. Saved/community tile headings use
that result. No naming algorithm, serial conversion, or stat calculation changed.

The original saved label remains in the heading tooltip and edit form. Folder
paths, creator attribution, selection, imported data, and serials remain unchanged.
Exact serial keys retain case, level, part order, and duplicates. Resolved names
survive list rerenders and join the existing saved-name search for this session.
Stale/different-serial results cannot rename a tile. Screenshot-only items without
reliable name metadata retain their existing label; no OCR guesses or extra card
generation requests are made just to rename them.

Validation: JavaScript syntax checks and real Electron shared-card and community
UI tests passed. Coverage includes native/GZO names, stored-data preservation,
case-sensitive identity, original-label search, rerender/reopen, creator-folder
preservation and unchanged checkbox selection. Existing image source priority,
layout toggles, pagination, import and delivery tests passed.

Local packaging and installed verification receipts: `output/saved-card-names/`.
The packaged asset check passed for 3,243 files. Installed executable and ASAR
hashes match the tested build; the prior pair is backed up in that receipt folder.
The desktop was restarted without touching the game. In the installed Saved
Items view, searching the old label `Zeroed` shows a resolved `Shiny War Paint`
heading matching its card, confirming source-label search and the new heading
together. GZO headings still depend on the catalog's supplied name metadata;
this change does not transcribe text from screenshot pixels. The live bridge
remained healthy and AFK enabled, waiting for guests.
