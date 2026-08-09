# Third-Party Notices

## Mattmab Legit Builder

This repository includes an experimental local integration of Mattmab's Legit Builder / item editor assets under:

- `external_app/v22_parts_codes_fixed/matt_editor/`

Upstream source:

- `https://github.com/mattmab/legit-builder`

The upstream `Application/package.json` declares license `ISC`. No separate upstream `LICENSE` file was present in the reviewed checkout at the time this integration was added.

The MSBT wrapper starts a local Python host for these assets and routes serial conversion through MSBT's standalone serial helpers. The external app must not import SDK/game modules for this editor path.

## ActorScriptDeployer

This repository vendors ActorScriptDeployer under:

- `tools/third_party/sdk_mods/ActorScriptDeployer/`

Author and license:

- Author: Matt
- License: MIT, per `tools/third_party/sdk_mods/ActorScriptDeployer/pyproject.toml`

MSBT bundles ActorScriptDeployer as a folder-form SDK mod dependency for the
Dev Spawner tab. Live game actions still go through the MSBT bridge/backend,
and ActorScriptDeployer remains game-side only.

## oak2-mod-manager (BL4 SDK)

MSBT's Electron app can download and install the official unmodified
`oak2-sdk.zip` release asset for [oak2-mod-manager v0.3](https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3)
into the detected Borderlands 4 game folder. The zip is cached under the app
`userData` folder (`oak2-cache/`) and is not vendored in git.

Upstream:

- Project: https://github.com/bl-sdk/oak2-mod-manager
- Install guide / mod DB: https://bl-sdk.github.io/oak2-mod-db/
- License: LGPL-3.0 (see upstream `LICENSE`; GPL/LGPL texts at https://www.gnu.org/licenses/)

MSBT also writes `sdk_mods/settings/<module>.json` with `"enabled": true` for
required gameplay mods (`MattsSDKBoostingTools`, `ActorScriptDeployer`) so users
do not have to enable them manually in the in-game mods menu. Core oak2
libraries (`mods_base`, console mod menu) ship with the official release and
load as part of the SDK.

## Azzy UVH Booster

MSBT's Boosting tab includes UVH rank-up buttons adapted from Azzy UVH Booster.

Author and license:

- Author: Azalea Asvail
- License: MIT, per the reviewed `AzzyUVHbooster.sdkmod` `pyproject.toml`

The adapted MSBT implementation uses the UVH tier challenge workflow and keeps
the live-game execution inside MSBT's SDK bridge/backend. The reviewed source
credits Pyrex for the UVH6/UVH7 challenge paths.

## Reference Mods Reviewed

MSBT also reviews community BL4 SDK mods as behavior references. Reviewing a mod
does not mean its implementation has been copied into MSBT.

Reference notes:

- `docs/REFERENCE_MOD_NOTES.md`

Reviewed local mods and credits:

- BL4 Player Movement by Squ1ggs, MIT. Useful movement-targeting and movement
  reset patterns may be adapted later with attribution and license notice.
- obj_dump by apple1417, GPL3. Reviewed for object-dump diagnostics. No GPL
  implementation code has been copied into MSBT.
- Dump Ping by Yeti, GPL3. Reviewed for ping-to-object discovery workflow. No
  GPL implementation code has been copied into MSBT.
- Trash Seller by FreepDryer, GPL3. Reviewed for inventory workflow context. No
  GPL implementation code has been copied into MSBT.
- Falling Menus by Yeti, GPL3. Reviewed for menu/movement behavior context. No
  GPL implementation code has been copied into MSBT.
- Grapple Anywhere by Yeti, GPL3. Reviewed for grapple behavior context. No GPL
  implementation code has been copied into MSBT.

Apple/apple1417 is also credited for BL4 SDK ecosystem contributions and object
diagnostic tooling that informs future MSBT debugging work.
