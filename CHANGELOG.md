# Changelog

## Unreleased

### Added

- Prominent contributor credits and links to original projects in the README.
- A plain-text third-party notices file for desktop, SDK, and Android packages.
- A dedicated Credits tab in the desktop app.
- Community Discord links for GZO, Scooter’s Garage, and Azalea Asvail’s Modding World in the README and desktop app.
- Funk’s Borderlands Trading Hub in the community list and desktop links.
- Restored README download counters for the Windows installer, portable ZIP, and Android APK.

### Changed

- Consolidated in-app contributor acknowledgments, community links, and third-party notices into one Credits tab.

- Excluded Python tests and test caches from desktop packages; ignored local research and capture folders.
- SDK packaging now validates its input and replaces the previous package only after a successful build.

- Clarified vehicle preset instructions and repaired references to removed documentation.
- Corrected attribution for the desktop interface and bridge; retained Squ1ggs’ code and helper credits.
- Expanded Mattmab’s credits to name the original gameplay modules, Python helpers, and retained editor components.
- Narrowed Squ1ggs’ credit to later helper additions and references; added Pyrex’s Bonk Utilities acknowledgment and source link.
- Replaced the README with contributor acknowledgments and brief installation guidance.
- Updated packaging to use the plain-text notices file.

### Removed

- Outdated screenshots and their obsolete capture script.

- Retired BLImGui panel, its startup fallback, and unused panel synchronization code. The native F7 Quick Menu and desktop bridge remain the supported interfaces.
- Superseded Quick Menu preview instructions, legacy Tkinter packaging scripts, internal attribution snapshot, and tracked editor-only guidance.
- Outdated app screenshot embeds from the README.
- The previous Markdown documentation outside the main README, including planning notes, handoffs, feature comparisons, and audit narratives.
