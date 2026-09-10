using System.Security.Cryptography;
using System.Text.Json;
using System.Text.RegularExpressions;
using CUE4Parse.FileProvider;
using CUE4Parse.MappingsProvider;
using CUE4Parse.UE4.Assets.Exports.Texture;
using CUE4Parse.UE4.Versions;
using CUE4Parse_Conversion.Textures;
using SkiaSharp;

// Maintainer-only archive reader. Never starts the game or changes installed assets.
if (args.Length != 7)
{
    Console.Error.WriteLine("Usage: game_icon_extract <Paks-dir> <editor-LegitItems-dir> <new-output-dir> <oodle-dll> <usmap> <Steam-build-id> <uiresources-subdirectory>");
    return 2;
}
var gameDir = Path.GetFullPath(args[0]);
var dataDir = Path.GetFullPath(args[1]);
var outputDir = Path.GetFullPath(args[2]);
var resourceName = args[6];
if (!Regex.IsMatch(resourceName, @"\A[A-Za-z0-9_-]+\z") ||
    !Regex.IsMatch(args[5], @"\A[1-9][0-9]*\z"))
    throw new ArgumentException("Use one resource subdirectory name and a positive decimal Steam build id.");
if (!Directory.Exists(gameDir) || !Directory.Exists(dataDir) || !File.Exists(args[3]) || !File.Exists(args[4]))
    throw new ArgumentException("Paks, editor data, Oodle DLL and USMAP must exist.");
if (Directory.Exists(outputDir) && Directory.EnumerateFileSystemEntries(outputDir).Any())
    throw new ArgumentException("Choose an empty output directory to preserve earlier extractions.");

var marker = "/uiresources/" + resourceName + "/";
var references = new SortedSet<string>(StringComparer.OrdinalIgnoreCase);
foreach (var file in Directory.EnumerateFiles(dataDir, "*.json"))
{
    using var document = JsonDocument.Parse(File.ReadAllText(file));
    CollectReferences(document.RootElement, marker, references);
}
if (references.Count == 0) throw new InvalidOperationException("No matching editor asset references found.");

CUE4Parse.Compression.OodleHelper.Initialize(Path.GetFullPath(args[3]));
using var provider = new DefaultFileProvider(gameDir, SearchOption.TopDirectoryOnly, true, new VersionContainer(EGame.GAME_UE5_5));
provider.MappingsContainer = new FileUsmapTypeMappingsProvider(Path.GetFullPath(args[4]));
provider.Initialize();
provider.Mount();
var files = new List<object>();
var failures = new List<string>();
var outputNames = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
foreach (var asset in references)
{
    try
    {
        var packagePath = asset.Split('.')[0];
        var package = "OakGame/Content/" + packagePath["/Game/".Length..] + ".uasset";
        var relativePng = packagePath[(packagePath.LastIndexOf("/uiresources/", StringComparison.OrdinalIgnoreCase) + "/uiresources/".Length)..] + ".png";
        var outputPath = Path.GetFullPath(Path.Combine(outputDir, relativePng));
        if (!outputPath.StartsWith(outputDir + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase) ||
            !outputNames.Add(relativePng))
            throw new InvalidOperationException("Unsafe or duplicate output path: " + relativePng);
        var texture = provider.LoadPackageObject<UTexture2D>(package, Path.GetFileNameWithoutExtension(package));
        using var bitmap = texture.Decode(ETexturePlatform.DesktopMobile);
        if (bitmap is null) throw new InvalidOperationException("Texture decoder returned no bitmap.");
        using var png = bitmap.Encode(SKEncodedImageFormat.Png, 100);
        var bytes = png.ToArray();
        using var verified = SKBitmap.Decode(bytes);
        if (verified is null || verified.Width != bitmap.Width || verified.Height != bitmap.Height ||
            !verified.Pixels.Any(pixel => pixel.Alpha != 0))
            throw new InvalidOperationException("PNG failed dimensions/content verification.");
        Directory.CreateDirectory(Path.GetDirectoryName(outputPath)!);
        File.WriteAllBytes(outputPath, bytes);
        files.Add(new { asset, package = provider.Files[package].Path, relative_png = relativePng,
            width = bitmap.Width, height = bitmap.Height, bytes = bytes.Length,
            sha256 = Convert.ToHexStringLower(SHA256.HashData(bytes)) });
    }
    catch (Exception error)
    {
        failures.Add(asset + ": " + error.Message);
        Console.Error.WriteLine(failures[^1]);
    }
}
var manifestDirectory = Path.Combine(outputDir, resourceName);
Directory.CreateDirectory(manifestDirectory);
File.WriteAllText(Path.Combine(manifestDirectory, "native-assets-manifest.json"), JsonSerializer.Serialize(new
{
    game_build = args[5], source = "Installed Borderlands 4 game assets (Gearbox / 2K)",
    extracted_at = DateTimeOffset.UtcNow, cue4parse_version = "1.2.2", conversion_version = "1.2.1",
    engine_format = "UE5.5", mapping_sha256 = Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(args[4]))),
    expected_count = references.Count, file_count = files.Count, files, failures
}, new JsonSerializerOptions { WriteIndented = true }) + "\n");
Console.WriteLine($"Exported and verified {files.Count}/{references.Count} PNGs; {failures.Count} failures.");
return failures.Count == 0 ? 0 : 1;

static void CollectReferences(JsonElement value, string marker, ISet<string> references)
{
    if (value.ValueKind == JsonValueKind.Object)
        foreach (var property in value.EnumerateObject()) CollectReferences(property.Value, marker, references);
    else if (value.ValueKind == JsonValueKind.Array)
        foreach (var item in value.EnumerateArray()) CollectReferences(item, marker, references);
    else if (value.ValueKind == JsonValueKind.String)
    {
        var text = value.GetString()?.Trim() ?? "";
        if (text.StartsWith("Asset'", StringComparison.OrdinalIgnoreCase) && text.EndsWith('\'')) text = text[6..^1];
        if (text.StartsWith("/Game/", StringComparison.OrdinalIgnoreCase) && text.Contains(marker, StringComparison.OrdinalIgnoreCase))
            references.Add(text);
    }
}
