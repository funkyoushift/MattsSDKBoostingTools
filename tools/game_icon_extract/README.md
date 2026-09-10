# Native editor icon extraction

This maintainer tool exports only textures referenced by the editor's current
Nexus JSON for one `uiresources` subdirectory. It reads the installed game archives
without launching the game or changing game files. Use .NET 9, the game's matching
USMAP, and a locally available Oodle DLL. CUE4Parse 1.2.2 and its compatible
CUE4Parse-Conversion 1.2.1 are pinned external build dependencies, not MSBT runtime
components. The latter package itself requires CUE4Parse 1.2.2.

From the repository root, provide the paths for your installation:

```powershell
dotnet run --project tools/game_icon_extract -- `
  'C:\Program Files (x86)\Steam\steamapps\common\Borderlands 4\OakGame\Content\Paks' `
  'external_app/v22_parts_codes_fixed/matt_editor/LegitItems' `
  'tools/_tmp_loveless_icons' `
  'C:\path\to\oodle-data-shared.dll' `
  'C:\path\to\borderlands.usmap' `
  '25234898' 'corpo_hacker_icons'
```

The output directory must be empty. The tool verifies each encoded PNG by decoding
it again, checking dimensions and nontransparent pixels. It records source asset
paths, build, mapping hash, dimensions and PNG SHA-256 hashes in
`corpo_hacker_icons/native-assets-manifest.json`. A nonzero exit or any manifest
failure means the extraction is incomplete; do not copy partial results into the
editor. Visually inspect an action skill, a passive and the portrait before copying
the complete subtree into `matt_editor/uiresources/`. The September 10, 2026 build
has 130 referenced textures, including tooltip and portrait artwork.

The PNGs remain Gearbox / 2K game artwork. No artwork is generated or recolored.
See `docs/THIRD_PARTY_NOTICES.md` for attribution. Exporter libraries are restored
to the maintainer's NuGet cache and are not added to the desktop or SDK package.
