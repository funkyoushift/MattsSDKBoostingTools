using MsbtSetup;
using System.IO.Compression;
using System.Security.Cryptography;
using System.Text.Json;

if (args.Contains("--install-sdkmods-and-exit"))
{
    bool fail = File.Exists(Path.Combine(AppContext.BaseDirectory, "simulate-failure"));
    Console.WriteLine(fail ? "Simulated game setup failure" : "Simulated game setup success");
    Environment.Exit(fail ? 2 : 0);
    return;
}

string originalDirectory = Environment.CurrentDirectory;
int passed = 0;
void Check(bool value, string name) { if (!value) throw new Exception(name); passed++; Console.WriteLine("PASS " + name); }
void Reject(Action action, string name) { try { action(); } catch (Exception ex) when (ex is InvalidDataException or IOException) { passed++; Console.WriteLine("PASS " + name); return; } throw new Exception("Expected rejection: " + name); }
string temp = Path.Combine(Path.GetTempPath(), "MSBT-Setup-tests-" + Guid.NewGuid().ToString("N"));
Directory.CreateDirectory(temp);
try
{
    if (args.Contains("--live"))
    {
        var live = new Engine(Path.Combine(temp, "live"), Console.WriteLine);
        using var liveLock = live.Lock();
        var release = await live.Latest();
        await live.Download(release);
        live.Apply(release);
        Console.WriteLine("LIVE verified/extracted: " + release.Tag + " SHA256 " + release.Sha256);
        var info = new System.Diagnostics.ProcessStartInfo(Path.Combine(live.AppDir, Engine.Executable), "--smoke") { UseShellExecute = false, RedirectStandardOutput = true, RedirectStandardError = true, CreateNoWindow = true };
        info.Environment.Remove("ELECTRON_RUN_AS_NODE");
        using var smoke = System.Diagnostics.Process.Start(info)!;
        var stdout = smoke.StandardOutput.ReadToEndAsync();
        var stderr = smoke.StandardError.ReadToEndAsync();
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(60));
        await smoke.WaitForExitAsync(timeout.Token);
        Console.WriteLine(await stdout); Console.WriteLine(await stderr);
        Check(smoke.ExitCode == 0, "official payload packaged smoke");
        // Test real Windows directory replacement after the packaged app has exited.
        live.Apply(release);
        Check(Directory.Exists(Path.Combine(live.Root, "previous")), "real payload reinstall and rollback retention");
    }
    string Metadata(string digest = "sha256:" + "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", string url = "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/v2.15.0/MSBT-Portable-v2.15.0-win-x64.zip") => JsonSerializer.Serialize(new { draft = false, prerelease = false, tag_name = "v2.15.0", assets = new[] { new { name = "MSBT-Portable-v2.15.0-win-x64.zip", browser_download_url = url, size = 123, digest } } });
    Check(Engine.ParseRelease(Metadata()).Tag == "v2.15.0", "select published portable payload");
    Reject(() => Engine.ParseRelease(Metadata("")), "missing digest fails closed");
    Reject(() => Engine.ParseRelease(Metadata(url: "https://example.org/payload.zip")), "foreign download rejected");
    Reject(() => Engine.ParseRelease(Metadata().Replace("\"prerelease\":false", "\"prerelease\":true")), "prerelease rejected");
    var engine = new Engine(Path.Combine(temp, "install"));
    var gameSetup = engine.GameSetupStartInfo();
    Check(gameSetup.FileName == Path.Combine(engine.AppDir, Engine.Executable) && gameSetup.ArgumentList.SequenceEqual(new[] { "--install-sdkmods-and-exit" }), "installer invokes bundled game setup");
    Check(!gameSetup.UseShellExecute && gameSetup.CreateNoWindow && gameSetup.RedirectStandardOutput && gameSetup.RedirectStandardError && !gameSetup.Environment.ContainsKey("ELECTRON_RUN_AS_NODE"), "game setup runs as Electron with captured diagnostics");
    using var gate = engine.Lock();
    Reject(() => { using var second = engine.Lock(); }, "concurrent install rejected");
    Directory.CreateDirectory(engine.Cache);
    string zip = Path.Combine(engine.Cache, "payload.zip");
    Release Fixture(string version, string? bad = null)
    {
        if (File.Exists(zip)) File.Delete(zip);
        using (var archive = ZipFile.Open(zip, ZipArchiveMode.Create))
        {
            string root = "MSBT-Portable-v" + version + "-win-x64/";
            foreach (string required in new[] { Engine.Executable, "resources/app.asar", "resources/python/python.exe", "resources/sdkmod/MattsSDKBoostingTools.sdkmod", "resources/sdkmods/ActorScriptDeployer/__init__.py", "resources/releases/latest.json", "resources/oak2/oak2-sdk.zip", "resources/afk_shift/manifest.json", "resources/afk_shift/pakchunk90-Windows_90_P.pak" })
            {
                using var writer = new StreamWriter(archive.CreateEntry(root + required).Open());
                writer.Write(required.EndsWith("latest.json") ? JsonSerializer.Serialize(new { package_version = version }) : version);
            }
            if (bad != null) { using var writer = new StreamWriter(archive.CreateEntry(root + bad).Open()); writer.Write("bad"); }
        }
        return new Release("v" + version, "test", "test", new FileInfo(zip).Length, Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(zip))).ToLowerInvariant());
    }
    var first = Fixture("2.15.0");
    engine.Apply(first);
    Check(File.ReadAllText(Path.Combine(engine.AppDir, Engine.Executable)) == "2.15.0", "fresh install");
    var next = Fixture("2.15.1");
    Reject(() => engine.Apply(next, () => throw new IOException("simulated rename failure")), "failed replacement reports failure");
    Check(File.ReadAllText(Path.Combine(engine.AppDir, Engine.Executable)) == "2.15.0", "failed replacement restores old app");
    Directory.SetCurrentDirectory(engine.AppDir);
    engine.Apply(next);
    Check(Environment.CurrentDirectory == engine.Root, "inherited app working directory released before replacement");
    Check(File.ReadAllText(Path.Combine(engine.AppDir, Engine.Executable)) == "2.15.1", "update swaps in new app");
    Check(File.ReadAllText(Path.Combine(engine.Root, "previous", Engine.Executable)) == "2.15.0", "previous version retained");
    File.AppendAllText(zip, "corrupt");
    Reject(() => engine.Apply(next), "corrupt payload rejected before replacement");
    Check(File.ReadAllText(Path.Combine(engine.AppDir, Engine.Executable)) == "2.15.1", "corrupt download leaves installed version intact");
    foreach (string bad in new[] { "../escape", "resources/../../escape", "C:/escape", "resources/file:stream", "resources/CON", "resources/app.asar" })
    {
        var evil = Fixture("2.15.2", bad);
        Reject(() => engine.Apply(evil), "unsafe archive rejected: " + bad);
    }
    Check(File.ReadAllText(Path.Combine(engine.AppDir, Engine.Executable)) == "2.15.1", "unsafe archives preserve app");
    var older = Fixture("2.15.0");
    Reject(() => engine.Apply(older), "accidental downgrade rejected");
    Directory.Delete(Path.Combine(engine.Root, "previous"), true);
    Directory.Move(engine.AppDir, Path.Combine(engine.Root, "previous"));
    var recovery = Fixture("2.15.1");
    engine.Apply(recovery);
    Check(File.Exists(Path.Combine(engine.AppDir, Engine.Executable)), "recover interrupted directory swap");
    File.Delete(Path.Combine(engine.AppDir, ".msbt-managed"));
    var valid = Fixture("2.15.2");
    Reject(() => engine.Apply(valid), "unowned installation preserved");
    var helperEngine = new Engine(Path.Combine(temp, "helper-test"));
    Directory.CreateDirectory(helperEngine.AppDir);
    foreach (string name in new[] { "SetupTests.dll", "SetupTests.deps.json", "SetupTests.runtimeconfig.json" })
        File.Copy(Path.Combine(AppContext.BaseDirectory, name), Path.Combine(helperEngine.AppDir, name));
    File.Copy(Path.Combine(AppContext.BaseDirectory, "SetupTests.exe"), Path.Combine(helperEngine.AppDir, Engine.Executable));
    await helperEngine.InstallGameIntegration();
    Check(File.ReadAllText(Path.Combine(helperEngine.Root, "game-setup.log")).Contains("Simulated game setup success"), "real helper subprocess completion recorded");
    File.WriteAllText(Path.Combine(helperEngine.AppDir, "simulate-failure"), "1");
    bool failed = false;
    try { await helperEngine.InstallGameIntegration(); } catch (IOException) { failed = true; }
    Check(failed && File.ReadAllText(Path.Combine(helperEngine.Root, "game-setup.log")).Contains("Exit: 2"), "failed game helper cannot report setup success");
    Console.WriteLine($"{passed} installer checks passed.");
}
finally { Directory.SetCurrentDirectory(originalDirectory); Directory.Delete(temp, true); }
