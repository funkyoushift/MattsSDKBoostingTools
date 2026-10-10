# Desktop layout release 2.35.1

Martin explicitly requested release of the layout work. Isolated release branch starts from published 2.35.0; selected desktop files were integrated without copying the dirty product backend. Includes navigation/control clarity, inline targeting, AFK handoffs and passive hover-card repair. Full workspace targeting replaces loading the narrow Mayhem-only selector module. Existing Mayhem controls and runtime repairs remain.

Source validation: 40-route navigation/control preservation, five AFK handoff routes with duplicate/order preservation and atomic rejection, running edit lock, named-target payloads, Classic/workspace control clarity and Mayhem actions, hover click-through/pinned/zoom/scroll/narrow tests, and search pass. Python compileall and six startup/import checks pass. Full npm check passed after updating the existing walkthrough-copy assertion to the revised control homes; no runtime behavior was changed to satisfy the assertion.

Build/publication verification pending. Android unchanged. No live gameplay retest claimed or needed for this desktop-only change. Shiny combat-area issue and mission-completion research excluded. Rollback: reinstall 2.35.0. Original product checkout and other pending work preserved.

Final build passed: 31 installer checks, packaged runtime and 3251 assets, executable smoke, updater, and final app.asar navigation/handoff/Mayhem tests. Initial build was rejected for metadata identity drift and fully rebuilt. Publication verification pending.
