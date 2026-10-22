using System.Text.Json;

namespace MsbtSetup;

internal sealed record ReportingChoice(int Version, bool Enabled, bool IncludeDumps, string EnabledAt);

internal static class ReportingPreferences
{
    private static string FilePath => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
        "matts-sdk-boosting-tools", "failure_reporting.json");

    public static ReportingChoice Read()
    {
        try
        {
            var value = JsonSerializer.Deserialize<ReportingChoice>(File.ReadAllText(FilePath),
                new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            if (value?.Version == 1) return value;
        }
        catch (IOException) { }
        catch (JsonException) { }
        catch (UnauthorizedAccessException) { }
        return new ReportingChoice(1, false, false, "");
    }

    public static void Write(bool enabled, bool includeDumps)
    {
        var previous = Read();
        var choice = new { version = 1, enabled,
            includeDumps = enabled && includeDumps,
            enabledAt = enabled ? (previous.Enabled && !string.IsNullOrWhiteSpace(previous.EnabledAt)
                ? previous.EnabledAt : DateTimeOffset.UtcNow.ToString("O")) : "" };
        var folder = Path.GetDirectoryName(FilePath)!;
        Directory.CreateDirectory(folder);
        var temporary = Path.Combine(folder, "failure_reporting." + Guid.NewGuid().ToString("N") + ".tmp");
        try
        {
            File.WriteAllText(temporary, JsonSerializer.Serialize(choice));
            File.Move(temporary, FilePath, true);
        }
        finally { if (File.Exists(temporary)) File.Delete(temporary); }
        if (!enabled)
        {
            try
            {
                var outbox = Path.Combine(folder, "failure-report-outbox");
                if (Directory.Exists(outbox) &&
                    (new DirectoryInfo(outbox).Attributes & FileAttributes.ReparsePoint) == 0)
                    foreach (var report in Directory.EnumerateFiles(outbox, "*.json", SearchOption.TopDirectoryOnly))
                        if (Guid.TryParse(Path.GetFileNameWithoutExtension(report), out _)) File.Delete(report);
            }
            catch (IOException) { /* Disabled consent still prevents any upload. */ }
            catch (UnauthorizedAccessException) { /* Disabled consent still prevents any upload. */ }
        }
    }
}
