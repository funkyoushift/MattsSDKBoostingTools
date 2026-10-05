# Visible contributor credits — October 5, 2026

## Issue and evidence

Matt requested a check of current GitHub attribution and consideration of credits
inside the tools. GitHub main was verified at `114e830` (v2.30.0). The README
Credits table and THIRD_PARTY_NOTICES already credit RDP / Squ1ggs. The September
30 review (`c9ef75d`, `docs/ATTRIBUTION_REVIEW_2026-09-30.md`) corrects the broad
September 10 overlap audit: overlap alone did not establish authorship or reuse
direction. The older primary working directory still contains those superseded
claims; it was not used as the attribution baseline.

The current desktop renderer only explicitly named Squiggs in a Black Market
tooltip. Feature attribution was therefore much harder to find in the UI than
on GitHub. This change follows the existing corrected contribution map; it is
not a new exhaustive authorship audit.

## Change

In the existing native-cards-release worktree at `114e830`, renderer.html adds
visible credit beside movement, player teleport, XYZ bookmarks, combat/resource
tuning, vehicle tuning and the compact spawner layout. Wording distinguishes
adapted code/patterns from workflow/layout inspiration. Matt's ASD backend and
mattmab's vehicle presets retain separate credit. Support gains an RDP / Squ1ggs
public-mods/source button; renderer.js routes it through the existing external
browser handler. No donation destination was invented.

Matt clarified that the existing README credit was negligible and difficult to
find. README.md now acknowledges community contributions immediately below the
product branding, before the donation link, with a prominent Squ1ggs paragraph
and links to the full credits and evidence. Other principal contributors remain
acknowledged. A persistent Contributor Credits header button opens the GitHub
credits anchor, independently of the Support dropdown.

## Validation and limits

- `node --check electron_poc/renderer.js`: passed.
- `git diff --check`: passed (normal CRLF normalization warnings).
- Electron `test_walkthrough_targets.js`: passed 107 highlighted steps and
  AFK launch plus all 12 workspace steps.
- `python -m pytest tools/tests/test_quick_menu_no_blimgui.py -q`: 4 passed.
- No SDK behavior changed; no live game actions or guest-save validation.
- New strings remain English unless subsequently added to the translation catalog.

## Deployment and rollback

Desktop changes are source-only and local: not installed, pushed, packaged or
released. The README draft described above was superseded by the complete rewrite
in [the community-first README review](2026-10-05-community-first-readme.md),
which is published separately with these documentation notes. Versions
unchanged. Roll back only the added attribution paragraphs/button and its handler
entry; preserve unrelated work in this worktree. Do not reinstate the withdrawn
blanket attribution from the September 10 audit.
