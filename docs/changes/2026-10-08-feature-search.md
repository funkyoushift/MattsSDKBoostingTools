# 2026-10-08: Search individual controls

Matt asked to make everything available in search after reorganizing the local
Farming Lab. The current finder indexed only tabs and panel titles/aliases;
individual features such as God Mode and Repair Kit Cooldown were absent.

`electron_poc/renderer.js` now indexes labeled controls, descriptive buttons,
subheadings, field placeholders and disclosure titles across tabs, including hidden workspace
sections. It excludes live input values/options and generic button names.
Duplicate names within a panel are collapsed. The 14 lab features have a shared
frontend definition for their groups, labels and aliases, so they remain
discoverable before game status creates their rows. Search includes common
ammo, skill, glide, vendor and repair-kit terms. Exact titles/aliases rank
above broad matches, and word order or joined names such as godmode work.

Selecting a result switches tabs, reveals the owning workspace section, opens
ancestor disclosures, scrolls to the actual control and highlights it. It never
presses the game control. A disconnected lab result opens its group; it does
not enable unavailable controls. Existing tab/panel results remain available.

Validation: renderer syntax passed. `test_app_finder_features.js` uses real
Electron DOM/search-result clicks in workspace and classic layouts, without
preload or a game transport. All 14 feature routes are visible/highlighted,
13 queries return results, God Mode and repair-kit aliases rank correctly,
disconnected discovery and collapsed-row reveal pass, and no game action is
executed. The fixture indexes more than 800 feature/control entries per layout.
These are feature/control labels, not an inventory-item or serial search.

The existing Farming Lab button regression also passed. The source desktop was
restarted from the isolated farming-lab checkout without stopping Borderlands.
No production installer/SDK package, version change or public release.

Rollback: revert this finder change and shared frontend feature definitions,
then restart source Electron. There are no new saved preferences or game state
changes to undo. Gameplay limitations in the Farming Lab record are unchanged.


Release follow-up: approved for v2.33.0, including Android 1.6.1. Shared feature
metadata and search navigation tests remain in the release tree. Package/public
results are recorded in ../releases/VERIFICATION_v2.33.0.txt.
