# Cached cards while guests are present

Local desktop fix after v2.29.1; no version bump or public release.

When the connected game's preview builder refuses new cards because guests are
present, the desktop now falls back to an exact-serial cached image from a prior
session. The existing schema and renderer revision checks still apply, and the
image remains labeled as a previous-session snapshot. Identity mismatch and
unrelated failures do not trigger this fallback.

If no matching screenshot or cached image exists, the shared card component shows
a readable solo-session explanation instead of a Python RuntimeError. This shared
component serves the catalog and other serial views, including community folders.

## Evidence and limitations

- Sampled Custom Static catalog variants are not all equivalent to similarly
  named GZO items. One Waterfall pair differs by an additional encoded
  `{255:12}` part in the GZO item. Its meaning was not established here.
- None of the 11 sampled custom variants had an exact cached card among the 421
  cached serials inspected. These items still require supported solo generation
  or an appropriate imported image. No name-only image matching was introduced.
- No game extraction, arithmetic, rendering rules, SDK code, or inventory changes.
- The solo generation safeguard remains intact.

## Validation

- 15 Node tests passed, including fallback, case-sensitive identity, metadata-only
  requests, mismatch rejection, deduplicated requests, and catalog image priority.
- Electron shared-card view tests passed, including the readable unavailable
  message and six serial-menu surfaces.
- Packaged dependency graph: 48 packages; packaged asset comparison: 3,242 files.
- Packaged startup smoke passed with version 2.29.1.
- Compared 1,447 local build files with the installed application: only the main
  executable (ASAR integrity) and app.asar differed. Backed up and replaced that
  pair, then verified hashes and restarted only MSBT Electron.
- Installed desktop reopened with item cards visible. Live bridge remained
  connected and AFK lobby enabled, waiting for guests. The unavailable-cache
  branch was verified by regression tests, not by introducing a live guest.
