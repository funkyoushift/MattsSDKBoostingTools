using System.Diagnostics;
using System.IO.Compression;
using System.Net.Http;
using System.Security.Cryptography;
using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.Win32;

namespace MsbtSetup;

public record Release(string Tag, string Name, string Url, long Size, string Sha256);

public sealed class Engine
{
    public const string Repository = "funkyoushift/MattsSDKBoostingTools";
    public const string Executable = "MattsSDKBoostingTools.exe";
    public static string DefaultRoot => Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "MSBT");
    public string Root { get; }
    public string AppDir => Path.Combine(Root, "app");
    public string Cache => Path.Combine(Root, "cache");
    readonly Action<string> report;
    static readonly HttpClient http = new() { Timeout = TimeSpan.FromMinutes(30) };

    public Engine(string root, Action<string>? report = null)
    {
        Root = Path.GetFullPath(root);
        this.report = report ?? (_ => { });
    }

    public FileStream Lock()
    {
        Directory.CreateDirectory(Root);
        if ((File.GetAttributes(Root) & FileAttributes.ReparsePoint) != 0)
            throw new IOException("The installation directory must not be a junction or symbolic link.");
        return new FileStream(Path.Combine(Root, "setup.lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
    }

    public ProcessStartInfo GameSetupStartInfo(string? gameRoot = null)
    {
        var start = new ProcessStartInfo(Path.Combine(AppDir, Executable)) {
            WorkingDirectory = AppDir, UseShellExecute = false, CreateNoWindow = true,
            RedirectStandardOutput = true, RedirectStandardError = true
        };
        start.ArgumentList.Add("--install-sdkmods-and-exit");
        if (!string.IsNullOrWhiteSpace(gameRoot)) start.ArgumentList.Add("--sdk-mods-path=" + Path.Combine(Path.GetFullPath(gameRoot), "sdk_mods"));
        start.Environment.Remove("ELECTRON_RUN_AS_NODE");
        return start;
    }

    public async Task InstallGameIntegration(string? gameRoot = null)
    {
        report("Installing the MSBT game mod, AFK SHiFT PAK, and missing SDK/mod manager...");
        var start = GameSetupStartInfo(gameRoot);
        using var process = Process.Start(start) ?? throw new IOException("Could not start game setup.");
        var output = process.StandardOutput.ReadToEndAsync();
        var errors = process.StandardError.ReadToEndAsync();
        await process.WaitForExitAsync();
        string stdout = await output, stderr = await errors;
        string receipt = Path.Combine(Root, "game-setup.log");
        await File.WriteAllTextAsync(receipt, DateTimeOffset.UtcNow.ToString("O") + "\nExit: " + process.ExitCode + "\n" + stdout + "\n" + stderr);
        int exitCode = process.ExitCode;
        if (exitCode != 0 && (stdout.Contains("EACCES") || stdout.Contains("EPERM") || stderr.Contains("EACCES") || stderr.Contains("EPERM")))
        {
            report("Windows permission is required to install game files. Please approve the Windows prompt.");
            var elevated = new ProcessStartInfo(start.FileName) { WorkingDirectory = AppDir, UseShellExecute = true, Verb = "runas", WindowStyle = ProcessWindowStyle.Hidden };
            foreach (string argument in start.ArgumentList) elevated.ArgumentList.Add(argument);
            using var retry = Process.Start(elevated) ?? throw new IOException("Could not start elevated game setup.");
            await retry.WaitForExitAsync();
            exitCode = retry.ExitCode;
            await File.AppendAllTextAsync(receipt, "\nElevated retry exit: " + exitCode);
        }
        if (exitCode != 0)
            throw new IOException("The desktop app is installed, but game setup did not finish. Close Borderlands 4 and retry this installer. Details: " + receipt);
    }

    public static Release ParseRelease(string json)
    {
        using var doc = JsonDocument.Parse(json);
        var root = doc.RootElement;
        if (root.GetProperty("draft").GetBoolean() || root.GetProperty("prerelease").GetBoolean())
            throw new InvalidDataException("Only published stable releases are supported.");
        string tag = root.GetProperty("tag_name").GetString() ?? "";
        if (!Regex.IsMatch(tag, @"^v\d+\.\d+\.\d+(\.\d+)?$"))
            throw new InvalidDataException("Unexpected release version.");
        string expected = "MSBT-Portable-" + tag + "-win-x64.zip";
        var matches = root.GetProperty("assets").EnumerateArray().Where(a => a.GetProperty("name").GetString() == expected).ToArray();
        if (matches.Length != 1) throw new InvalidDataException("The latest release must contain exactly one " + expected);
        var asset = matches[0];
        string url = asset.GetProperty("browser_download_url").GetString() ?? "";
        if (url != $"https://github.com/{Repository}/releases/download/{tag}/{expected}")
            throw new InvalidDataException("Unexpected release download address.");
        string digest = asset.TryGetProperty("digest", out var value) ? value.GetString() ?? "" : "";
        if (!Regex.IsMatch(digest, @"^sha256:[a-fA-F0-9]{64}$"))
            throw new InvalidDataException("GitHub did not supply a SHA-256 checksum. Nothing will be installed.");
        long size = asset.GetProperty("size").GetInt64();
        if (size < 1 || size > 4L * 1024 * 1024 * 1024) throw new InvalidDataException("Invalid package size.");
        return new Release(tag, expected, url, size, digest[7..].ToLowerInvariant());
    }

    public async Task<Release> Latest()
    {
        report("Checking the latest MSBT release...");
        using var req = new HttpRequestMessage(HttpMethod.Get, $"https://api.github.com/repos/{Repository}/releases/latest");
        req.Headers.UserAgent.ParseAdd("MSBT-Persistent-Setup/1.0");
        req.Headers.Accept.ParseAdd("application/vnd.github+json");
        using var response = await http.SendAsync(req);
        response.EnsureSuccessStatusCode();
        return ParseRelease(await response.Content.ReadAsStringAsync());
    }

    public static void Verify(string zip, Release release)
    {
        using var stream = File.OpenRead(zip);
        if (stream.Length != release.Size || !Convert.ToHexString(SHA256.HashData(stream)).Equals(release.Sha256, StringComparison.OrdinalIgnoreCase))
            throw new InvalidDataException("The download failed its size or SHA-256 check. Nothing was installed.");
    }

    public async Task Download(Release release)
    {
        Directory.CreateDirectory(Cache);
        string zip = Path.Combine(Cache, "payload.zip");
        if (File.Exists(zip))
        {
            try { Verify(zip, release); SavePending(release); report("Verified download is ready."); return; }
            catch (InvalidDataException) { }
        }
        string partial = Path.Combine(Cache, "payload.partial");
        report("Downloading " + release.Tag + "...");
        try
        {
            using var req = new HttpRequestMessage(HttpMethod.Get, release.Url);
            req.Headers.UserAgent.ParseAdd("MSBT-Persistent-Setup/1.0");
            using var response = await http.SendAsync(req, HttpCompletionOption.ResponseHeadersRead);
            response.EnsureSuccessStatusCode();
            await using (var source = await response.Content.ReadAsStreamAsync())
            await using (var dest = File.Create(partial))
            {
                byte[] buffer = new byte[1024 * 1024];
                long total = 0; int last = -1, count;
                while ((count = await source.ReadAsync(buffer)) > 0)
                {
                    total += count;
                    if (total > release.Size) throw new InvalidDataException("Download exceeds the published size.");
                    await dest.WriteAsync(buffer.AsMemory(0, count));
                    int percent = (int)(100 * total / release.Size);
                    if (percent / 5 != last) { last = percent / 5; report($"Downloading {release.Tag}: {percent}%"); }
                }
            }
            Verify(partial, release);
            File.Move(partial, zip, true);
            SavePending(release);
            report("Download verified. Ready to install.");
        }
        finally { if (File.Exists(partial)) File.Delete(partial); }
    }

    void SavePending(Release release)
    {
        string pending = Path.Combine(Cache, "pending.json");
        File.WriteAllText(pending + ".tmp", JsonSerializer.Serialize(release));
        File.Move(pending + ".tmp", pending, true);
    }

    public Release Pending()
    {
        var pending = JsonSerializer.Deserialize<Release>(File.ReadAllText(Path.Combine(Cache, "pending.json"))) ?? throw new InvalidDataException("No prepared update.");
        if (!Regex.IsMatch(pending.Tag, @"^v\d+\.\d+\.\d+(\.\d+)?$") || !Regex.IsMatch(pending.Sha256, "^[a-f0-9]{64}$"))
            throw new InvalidDataException("Invalid prepared update.");
        return pending;
    }

    public static void Extract(string zipPath, string destination, string tag)
    {
        using var zip = ZipFile.OpenRead(zipPath);
        string prefix = "MSBT-Portable-" + tag + "-win-x64/";
        string root = Path.GetFullPath(destination) + Path.DirectorySeparatorChar;
        var names = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        long expanded = 0;
        // Validate the entire archive before writing any entry.
        foreach (var entry in zip.Entries)
        {
            string name = entry.FullName.Replace('\\', '/');
            if (!name.StartsWith(prefix, StringComparison.Ordinal)) throw new InvalidDataException("Unexpected archive root.");
            string relative = name[prefix.Length..];
            if (relative.Length == 0) continue;
            var parts = relative.TrimEnd('/').Split('/');
            if (parts.Any(p => p.Length == 0 || p is "." or ".." || p.EndsWith('.') || p.EndsWith(' ') || p.IndexOfAny(Path.GetInvalidFileNameChars()) >= 0 || Regex.IsMatch(p, @"^(CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(\.|$)", RegexOptions.IgnoreCase)))
                throw new InvalidDataException("Unsafe archive path.");
            if (((entry.ExternalAttributes >> 16) & 0xF000) == 0xA000 || (entry.ExternalAttributes & 0x400) != 0)
                throw new InvalidDataException("Archive links are not supported.");
            if (!names.Add(relative.TrimEnd('/'))) throw new InvalidDataException("Duplicate archive path.");
            if (!Path.GetFullPath(Path.Combine(destination, relative)).StartsWith(root, StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Archive path escapes the staging folder.");
            expanded += entry.Length;
            if (expanded > 8L * 1024 * 1024 * 1024) throw new InvalidDataException("Expanded package is too large.");
        }
        Directory.CreateDirectory(destination);
        foreach (var entry in zip.Entries)
        {
            string relative = entry.FullName.Replace('\\', '/')[prefix.Length..];
            if (relative.Length == 0) continue;
            string target = Path.Combine(destination, relative);
            if (relative.EndsWith('/')) Directory.CreateDirectory(target);
            else { Directory.CreateDirectory(Path.GetDirectoryName(target)!); entry.ExtractToFile(target, false); }
        }
        foreach (string required in new[] { Executable, "resources/app.asar", "resources/python/python.exe", "resources/sdkmod/MattsSDKBoostingTools.sdkmod", "resources/sdkmods/ActorScriptDeployer/__init__.py", "resources/releases/latest.json", "resources/oak2/oak2-sdk.zip", "resources/afk_shift/manifest.json", "resources/afk_shift/pakchunk90-Windows_90_P.pak" })
            if (!File.Exists(Path.Combine(destination, required))) throw new InvalidDataException("Package is missing " + required);
        using var manifest = JsonDocument.Parse(File.ReadAllText(Path.Combine(destination, "resources/releases/latest.json")));
        if (manifest.RootElement.GetProperty("package_version").GetString() != tag[1..])
            throw new InvalidDataException("Bundled version does not match the release.");
    }

    void RemoveOwnedDirectory(string path)
    {
        string full = Path.GetFullPath(path);
        if (!full.StartsWith(Root + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase)) throw new IOException("Refusing removal outside the installation.");
        if (!Directory.Exists(full)) return;
        RejectLinks(full);
        Directory.Delete(full, true);
    }

    static void RejectLinks(string path)
    {
        if ((File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0) throw new IOException("Unexpected link in installation: " + path);
        foreach (string entry in Directory.EnumerateFileSystemEntries(path))
        {
            if ((File.GetAttributes(entry) & FileAttributes.ReparsePoint) != 0) throw new IOException("Unexpected link in installation: " + entry);
            if (Directory.Exists(entry)) RejectLinks(entry);
        }
    }

    public void Apply(Release release, Action? afterMoveForTest = null)
    {
        Verify(Path.Combine(Cache, "payload.zip"), release);
        string previous = Path.Combine(Root, "previous");
        if (!Directory.Exists(AppDir) && Directory.Exists(previous))
        {
            if (!File.Exists(Path.Combine(previous, ".msbt-managed"))) throw new IOException("Unrecognized rollback folder.");
            Directory.Move(previous, AppDir);
        }
        if (Directory.Exists(AppDir) && !File.Exists(Path.Combine(AppDir, ".msbt-managed")))
            throw new IOException("This app folder is not owned by MSBT Setup. It will not be overwritten.");
        if (Directory.Exists(AppDir) && Version.TryParse(File.ReadAllText(Path.Combine(AppDir, ".msbt-managed")).Trim().TrimStart('v'), out var installed)
            && Version.TryParse(release.Tag.TrimStart('v'), out var incoming) && incoming < installed)
            throw new IOException("The installed version is newer than GitHub's latest release. Downgrades are not automatic.");
        RejectRunningApp();
        // A runner launched by Electron may inherit app/ as its working directory.
        // Windows then locks that directory against the replacement below.
        Directory.CreateDirectory(Root);
        Directory.SetCurrentDirectory(Root);
        string stage = Path.Combine(Root, "stage-" + Guid.NewGuid().ToString("N"));
        try
        {
            report("Unpacking and checking " + release.Tag + "...");
            Extract(Path.Combine(Cache, "payload.zip"), stage, release.Tag);
            File.WriteAllText(Path.Combine(stage, ".msbt-managed"), release.Tag);
            // Retain the previous working app until a fully validated replacement is ready.
            RemoveOwnedDirectory(previous);
            if (Directory.Exists(AppDir)) Directory.Move(AppDir, previous);
            try { afterMoveForTest?.Invoke(); Directory.Move(stage, AppDir); }
            catch { if (!Directory.Exists(AppDir) && Directory.Exists(previous)) Directory.Move(previous, AppDir); throw; }
            report("Installed " + release.Tag + ".");
        }
        finally { RemoveOwnedDirectory(stage); }
    }

    public void RejectRunningApp()
    {
        foreach (var process in Process.GetProcessesByName("MattsSDKBoostingTools"))
        using (process)
        {
            try
            {
                string? location = process.MainModule?.FileName;
                if (location != null && location.StartsWith(AppDir + Path.DirectorySeparatorChar, StringComparison.OrdinalIgnoreCase))
                    throw new IOException("Close MSBT before installing the update, then try again.");
            }
            catch (System.ComponentModel.Win32Exception) { throw new IOException("Could not verify whether MSBT is closed. Close MSBT and retry."); }
        }
    }

    public void Register(string setupExe, string version)
    {
        string localSetup = Path.Combine(Root, "MSBT-Setup.exe");
        if (!Path.GetFullPath(setupExe).Equals(localSetup, StringComparison.OrdinalIgnoreCase))
            File.Copy(setupExe, localSetup, true);
        // COM shell links avoid PowerShell quoting and require no external dependency.
        Type shellType = Type.GetTypeFromProgID("WScript.Shell")!;
        dynamic shell = Activator.CreateInstance(shellType)!;
        foreach (string folder in new[] { Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), Environment.GetFolderPath(Environment.SpecialFolder.Programs) })
        {
            dynamic shortcut = shell.CreateShortcut(Path.Combine(folder, "Matt's SDK Boosting Tools.lnk"));
            shortcut.TargetPath = Path.Combine(AppDir, Executable);
            shortcut.WorkingDirectory = AppDir;
            shortcut.Save();
            System.Runtime.InteropServices.Marshal.FinalReleaseComObject(shortcut);
        }
        System.Runtime.InteropServices.Marshal.FinalReleaseComObject(shell);
        using var key = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\MSBTPersistent");
        key.SetValue("DisplayName", "Matt's SDK Boosting Tools");
        key.SetValue("DisplayVersion", version.TrimStart('v'));
        key.SetValue("Publisher", "FunkYouSHiFT");
        key.SetValue("InstallLocation", Root);
        key.SetValue("DisplayIcon", Path.Combine(AppDir, Executable));
        key.SetValue("UninstallString", "\"" + localSetup + "\" --uninstall");
        key.SetValue("NoModify", 1, RegistryValueKind.DWord);
        key.SetValue("NoRepair", 1, RegistryValueKind.DWord);
    }

    public void Uninstall()
    {
        RejectRunningApp();
        if (Directory.Exists(AppDir) && !File.Exists(Path.Combine(AppDir, ".msbt-managed"))) throw new IOException("Unrecognized installation.");
        RemoveOwnedDirectory(AppDir);
        RemoveOwnedDirectory(Path.Combine(Root, "previous"));
        RemoveOwnedDirectory(Cache);
        Type shellType = Type.GetTypeFromProgID("WScript.Shell")!;
        dynamic shell = Activator.CreateInstance(shellType)!;
        foreach (string folder in new[] { Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory), Environment.GetFolderPath(Environment.SpecialFolder.Programs) })
        {
            string link = Path.Combine(folder, "Matt's SDK Boosting Tools.lnk");
            if (!File.Exists(link)) continue;
            dynamic shortcut = shell.CreateShortcut(link);
            string target = shortcut.TargetPath;
            System.Runtime.InteropServices.Marshal.FinalReleaseComObject(shortcut);
            if (target.Equals(Path.Combine(AppDir, Executable), StringComparison.OrdinalIgnoreCase)) File.Delete(link);
        }
        System.Runtime.InteropServices.Marshal.FinalReleaseComObject(shell);
        Registry.CurrentUser.DeleteSubKeyTree(@"Software\Microsoft\Windows\CurrentVersion\Uninstall\MSBTPersistent", false);
        report("MSBT removed. Saved settings and game mods were kept. The reusable Setup remains available.");
    }
}
