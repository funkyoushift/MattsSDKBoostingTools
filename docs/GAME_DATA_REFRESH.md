# Refresh data from an installed BL4 update

The online editor catalogs can lag a game patch. Use the installed game's NCS
tables for character identifiers, inventory parts, caps, actors, pools and travel.
This workflow only reads the game installation. It does not modify saves or publish.

1. Record the installed Steam `appmanifest_1285190.acf` build ID after the update
   finishes. Install .NET 9 to run the maintainer extractor.
2. Extract into a new, empty scratch directory:

   ```powershell
   dotnet run --project tools/game_data_extract -- '<BL4>/OakGame/Content/Paks' '<scratch>/ncs' '<oodle DLL>' '<build ID>'
   ```

   The extractor uses CUE4Parse 1.2.2 with UE5.5 and selects each path's effective
   archive priority. Do not enumerate all archive values into the same filenames:
   older patch copies would overwrite current data. A SHA-256 manifest is written
   beside the output directory. Use an existing compatible Oodle library, such as
   FModel's `Output/.data/oodle-data-shared.dll`.
3. Decode with the unmodified [NcsParser CLI](https://github.com/Cr4nkSt4r/Borderlands-4.NcsParser):

   ```powershell
   ncs_parser '<scratch>/ncs' --oodle '<oodle DLL>'
   ```

   Use full JSON output. `--minimal` without dependencies discards actual item
   parts and travel stations. Keep the parser, binaries and raw exports local;
   the application does not depend on the parser at runtime.
4. Import editor data with `tools/import_local_ncs_catalogs.py` (see `--help`),
   then preview and apply world catalogs:

   ```powershell
   python tools/refresh_game_world_catalogs.py '<parser>/output/json' --game-build '<build ID>'
   python tools/refresh_game_world_catalogs.py '<parser>/output/json' --game-build '<build ID>' --write
   ```

   Importers preserve backups under `_tmp_catalog_compare`. The world importer
   preserves curated labels/favorites and legacy entries, reads station-only
   dependency records, and merges partial patches without blanking absent fields.
5. Rebuild `docs/data/catalog_manifest.json` with its existing data version using
   `python tools/build_data_catalog_manifest.py`, then run `--check`. Game-derived
   assets carry their verified game build so old remote catalogs cannot replace
   them. Do not mark stale upstream data as extracted from the current game.
6. Run syntax/import checks, focused Python/Electron tests, and serial round trips.
   Build the local SDK package only after those checks pass. Verify `/status` on
   the updated game separately; extracted definitions do not prove live spawning,
   map travel, or DLL compatibility. A public release requires Matt's explicit ask.

September 10, 2026 baseline: game v1.10, Steam build `25234898`. The update notes
are on the [official BL4 site](https://borderlands.2k.com/borderlands-4/update-notes/).
