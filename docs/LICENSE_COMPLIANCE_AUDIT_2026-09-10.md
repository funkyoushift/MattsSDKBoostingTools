# MSBT License and Source-Provenance Audit

Date: 2026-09-10

Status: **Core corrections implemented and verified in local artifacts.**

This is an engineering provenance review, not legal advice.

## Confirmed facts

- Mattmab is Galoob. The supplied correspondence records that Mattmab no
  longer maintains the repository, recognizes FunkYouSHiFT as the maintainer,
  and asked that MSBT use MIT.
- The maintainer reports direct permission from Mattmab/Galoob and the owners
  of GZO and Lootlemon to use the material incorporated into MSBT.
- The earlier 59-file Nexus snapshot under `matt_editor/LegitItems/` carried
  Dominic/Cr4nkSt4r's `__copyright` metadata and parser link. The supplied
  correspondence provides his exact 2026 MIT notice. The current numbered
  tables are fresh local game extracts; the prior notice remains with retained
  source material and is not applied to the newly extracted Gearbox / 2K data.
- Azzy UVH Booster's reviewed metadata declares MIT.

## Corrections made

- Restored the complete original MSBT MIT license from repository history.
- Changed SDK mod metadata from the incorrect GPL3 declaration to MIT.
- Added Dominic/Cr4nkSt4r's exact MIT notice beside the earlier data snapshot.
- Preserved glacierpiece's complete upstream MIT notice beside the adapted
  save/profile crypto wrapper; the desktop includes this external-app tree.
- Reworked `docs/THIRD_PARTY_NOTICES.md` into a source-to-file map that
  distinguishes open-source licenses from direct permission grants.
- Added full adjacent notices for the custom editor browser bundle, the
  vendored GridStack files, and ActorScriptDeployer.
- Cross-checked all oak2 Mod Database entries and linked source repositories.
- Added Squ1ggs' exact MIT notice and corrected stale documents that had
  incorrectly classified the full Squ1ggsBoostingTools package as GPL.
- Configured desktop, SDK mod, and Android builds to carry applicable notices.

## Verification performed

- Python compilation completed successfully for the SDK mod source.
- The rebuilt `.sdkmod` contains `LICENSE`, `THIRD_PARTY_NOTICES.md`, and MIT
  package metadata.
- An unpacked Electron build completed and contains the MSBT license,
  consolidated notice, Dominic notice, editor browser-library notices, and
  ActorScriptDeployer notice.
- An Android debug build completed and contains MSBT's MIT text, the
  consolidated notice, and the complete Apache License 2.0 text under
  `assets/licenses/`.

## Important scope boundaries

- MSBT's MIT license covers MSBT-owned code; it does not automatically
  relicense third-party code, GZO/Lootlemon catalogs, game-derived datasets,
  or artwork.
- Direct permission is recorded as permission, not described as an open-source
  license.
- Cr4nkSt4r's current public NCS parser may use different terms. MSBT preserves
  the MIT grant supplied for the copies it received rather than claiming that
  every current upstream revision is MIT.
- GPL projects listed in the reference notes remain reference-only. A
  normalized source comparison found no material copied blocks from their
  current linked repositories; this is strong engineering evidence, not a
  legal conclusion.

## Remaining maintenance work

- Keep the original permission messages and attachments in the maintainer's
  durable records; the repository notice is not a substitute for that evidence.
- Re-run artifact-content checks whenever packaging changes or dependencies are
  upgraded.
- Generate a lockfile-derived dependency inventory in CI and flag new or
  unknown licenses before release.
