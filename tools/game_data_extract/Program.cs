using System.Security.Cryptography;
using System.Text.Json;
using CUE4Parse.FileProvider;
using CUE4Parse.UE4.Versions;

// Maintainer-only, read-only game archive extraction. Never load game code or saves.
if (args.Length != 4)
{
    Console.Error.WriteLine("Usage: game_data_extract <game-Paks-dir> <new-output-dir> <oodle-dll> <Steam-build-id>");
    return 2;
}
var gameDir = Path.GetFullPath(args[0]);
var outputDir = Path.GetFullPath(args[1]);
if (!Directory.Exists(gameDir) || !File.Exists(args[2]))
    throw new ArgumentException("Game Paks directory and Oodle DLL must exist.");
if (Directory.Exists(outputDir) && Directory.EnumerateFileSystemEntries(outputDir).Any())
    throw new ArgumentException("Choose an empty output directory to preserve earlier extractions.");
CUE4Parse.Compression.OodleHelper.Initialize(Path.GetFullPath(args[2]));
using var provider = new DefaultFileProvider(gameDir, SearchOption.TopDirectoryOnly, true, new VersionContainer(EGame.GAME_UE5_5));
provider.Initialize();
provider.Mount();
Directory.CreateDirectory(outputDir);
var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
var files = new List<object>();
foreach (var key in provider.Files.Keys.Distinct(StringComparer.OrdinalIgnoreCase)
             .Where(k => k.EndsWith(".ncs", StringComparison.OrdinalIgnoreCase)).Order())
{
    // Values enumeration includes patch duplicates. The keyed lookup selects the
    // effective archive priority, avoiding an older patch overwriting a newer one.
    var file = provider.Files[key];
    var name = Path.GetFileName(file.Path);
    if (!names.Add(name)) throw new InvalidOperationException($"Duplicate output name: {name}");
    var bytes = file.Read();
    File.WriteAllBytes(Path.Combine(outputDir, name), bytes);
    files.Add(new { path = file.Path, file = name, bytes = bytes.Length,
        sha256 = Convert.ToHexStringLower(SHA256.HashData(bytes)) });
}
var manifest = new { game_build = args[3], extracted_at = DateTimeOffset.UtcNow,
    archive_directory = gameDir, cue4parse_version = "1.2.2", engine_format = "UE5.5",
    file_count = files.Count, files };
// Store beside, not among, NCS input files: NcsParser also treats JSON as input.
File.WriteAllText(outputDir.TrimEnd(Path.DirectorySeparatorChar) + "-manifest.json",
    JsonSerializer.Serialize(manifest, new JsonSerializerOptions { WriteIndented = true }) + "\n");
Console.WriteLine($"Extracted {files.Count} effective NCS files into {outputDir}");
return files.Count > 0 ? 0 : 1;
