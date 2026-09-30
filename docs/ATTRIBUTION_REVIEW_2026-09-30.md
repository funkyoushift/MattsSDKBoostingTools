# MSBT attribution corrections — September 30, 2026

This review corrects the scope claims in the September 10 audits. It separates
path discoveries, existing MSBT code, later adaptations, interface inspiration,
and integration work. It is not an exhaustive authorship or license audit.

## Contribution map

| Contributor | Credit in MSBT | Evidence / public reference |
| --- | --- | --- |
| Mattmab / Matt | Original toolset and editor foundation; challenge-path discoveries | [Original MSBT repository](https://github.com/mattmab/MattsSDKBoostingTools). Challenge-path discovery credit was clarified by MSBT maintainer FunkYouSHiFT on September 30; the repository link is a project reference, not independent proof of each discovery. |
| Matt / Actor Script Deployer | Standard Dev Spawner backend | [Bundled author metadata](../tools/third_party/sdk_mods/ActorScriptDeployer/pyproject.toml) names Matt. MSBT bundled ASD in commit `bc85e4e` (July 14). `backend_actions.py` routes standard spawning to ASD `_cmd_spawnai`; MSBT adds integration and runtime fixes. |
| PyrexBLJ | Discovery of earlier UVHM paths | Maintainer clarification on September 30. [Public profile and projects](https://github.com/PyrexBLJ); this is a reference link, not a claim that the profile documents those paths. Do not restrict this credit to UVHM6/7 based on the earlier notice. |
| Azalea Asvail | Azzy UVH Booster workflow, with assistance from FunkYouSHiFT | [Public project, download and license](https://github.com/AzaleaAsvailAMW/amw-Uvhbooster). MSBT already identifies Azzy as its UVH workflow source. Assistance credit is maintainer-provided history. |
| RDP / Squ1ggs | Public code/patterns used in movement/teleport and combat/resource/vehicle tuning; inspiration for location bookmarks and compact Dev Spawner layout | [Public mods](https://github.com/Squ1ggs/Bl4SDKmods), MSBT commit [`a956860`](https://github.com/funkyoushift/MattsSDKBoostingTools/commit/a956860286f8fe3417da7532b3de8967c1b24fda), and [implementation notes](SQBT_INSPIRED_TEST_NOTES.md). The notes explicitly retain the ASD backend. This does not establish authorship of all matching helper code or the entire spawner. |
| FunkYouSHiFT / MSBT development | Desktop/bridge integration, SDK migration, subsequent AFK and community-folder workflows, save imports, translations, packaging, testing and fixes | MSBT commit history. This is maintenance/development credit, not a claim that every underlying component was independently authored. |

Other existing contributor, data-provider, framework and library credits remain
in [Third-party notices](THIRD_PARTY_NOTICES.md). Copyright notices are unchanged.

## Why the September 10 conclusion was too broad

The older audit compared matching blocks against later upstream snapshots but
did not subtract code already present in the earlier MSBT baseline. Such a
comparison identifies overlap, not its original author or direction of reuse.

A September 30 check compared MSBT's July baseline `1f91a73b09`, current
MSBT `bcee5b1`, and Squ1ggs' packaged SDK at `832db287f8`. After trimming lines
and excluding blank/comment-only lines, every matching block of at least 12
lines in the following modules was also present in the July MSBT baseline:
`legit_builder_core.py`, `serial_converter.py`, `movement_adjustments.py`,
`party_helpers.py`, `inventory_capacity.py`, `travel.py`, `shinies.py`,
`vault_card_boost.py`, and `golden_chest_keybinds.py`.

That finding invalidates using those matches alone to label the modules as
later Squ1ggs-derived additions. It does not establish the authorship of every
line in the July baseline. Smaller matches, rewritten code, and catalog/data
origins require separate tracing; no percentage of original authorship is claimed.

## Boundaries for future credits

- Preserve applicable licenses and copyright notices; this correction does not
  relicense or remove third-party material.
- Credit path discovery separately from implementation, integration or release.
- Credit ASD separately from UI inspiration and separately from catalog data.
- Do not infer exclusive authorship from a filename, feature name or matching code.
- Do not publish private correspondence or claims about another project's origin.
- Keep maintainer-provided history distinguishable from independently verified
  public evidence. Public profile links are not proof of specific discoveries.
- The old audits remain as dated records with a prominent correction, not as
  current authority for the withdrawn module/data-origin claims.
