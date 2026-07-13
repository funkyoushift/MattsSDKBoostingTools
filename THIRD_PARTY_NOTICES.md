# Third-Party Notices

## Mattmab Legit Builder

This repository includes an experimental local integration of Mattmab's Legit Builder / item editor assets under:

- `external_app/v22_parts_codes_fixed/matt_editor/`

Upstream source:

- `https://github.com/mattmab/legit-builder`

The upstream `Application/package.json` declares license `ISC`. No separate upstream `LICENSE` file was present in the reviewed checkout at the time this integration was added.

The MSBT wrapper starts a local Python host for these assets and routes serial conversion through MSBT's standalone serial helpers. The external app must not import SDK/game modules for this editor path.

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
