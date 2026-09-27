using System.Diagnostics;
using System.Text.Json;

namespace MsbtSetup;

static class Program
{
    [STAThread]
    static int Main(string[] args)
    {
        ApplicationConfiguration.Initialize();
        // Machine-readable operations never open a window or alter the installed app.
        if (args.Length == 1 && args[0] is "--check" or "--download")
        {
            try
            {
                var engine = new Engine(Engine.DefaultRoot);
                using var gate = engine.Lock();
                var release = engine.Latest().GetAwaiter().GetResult();
                if (args[0] == "--download") engine.Download(release).GetAwaiter().GetResult();
                Console.WriteLine(JsonSerializer.Serialize(new { ok = true, version = release.Tag[1..] }));
                return 0;
            }
            catch (Exception error) { Console.Error.WriteLine(error.Message); return 1; }
        }
        bool apply = args.Length == 3 && args[0] == "--apply" && args[1] == "--wait-pid" && int.TryParse(args[2], out _);
        bool uninstall = args.SequenceEqual(new[] { "--uninstall" });
        if (args.Length != 0 && !apply && !uninstall) return 2;
        using var form = new SetupForm(apply ? int.Parse(args[2]) : null, uninstall);
        Application.Run(form);
        return form.Result;
    }
}

sealed class SetupForm : Form
{
    readonly Label status = new() { AutoSize = false, Dock = DockStyle.Fill, Padding = new Padding(20), Text = "Install or update MSBT from the latest official GitHub release.\n\nYour saved settings are kept. Borderlands 4 is never stopped.\n\nInstallation: " + Engine.DefaultRoot };
    readonly Button install = new() { Text = "Install / Update", AutoSize = true };
    readonly Button launch = new() { Text = "Open MSBT", AutoSize = true, Enabled = false };
    readonly int? waitPid;
    readonly bool uninstall;
    bool busy;
    public int Result { get; private set; }
    public SetupForm(int? waitPid, bool uninstall)
    {
        this.waitPid = waitPid; this.uninstall = uninstall;
        Text = "MSBT Setup"; Width = 610; Height = 290; StartPosition = FormStartPosition.CenterScreen;
        MinimumSize = Size;
        var buttons = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 60, Padding = new Padding(15) };
        buttons.Controls.Add(install); buttons.Controls.Add(launch);
        Controls.Add(status); Controls.Add(buttons);
        if (uninstall) { install.Text = "Uninstall MSBT"; status.Text = "Remove the MSBT app? Saved settings and installed game mods will be kept."; }
        install.Click += async (_, _) => await Run();
        launch.Click += (_, _) => { Process.Start(new ProcessStartInfo(Path.Combine(Engine.DefaultRoot, "app", Engine.Executable)) { UseShellExecute = true }); Close(); };
        Shown += async (_, _) => { if (waitPid.HasValue) await Run(); };
        FormClosing += (_, e) => { if (busy) e.Cancel = true; };
    }

    void Report(string text) { if (InvokeRequired) BeginInvoke(() => status.Text = text); else status.Text = text; }
    async Task Run()
    {
        busy = true; install.Enabled = false; launch.Enabled = false;
        try
        {
            var engine = new Engine(Engine.DefaultRoot, Report);
            using var gate = engine.Lock();
            if (waitPid.HasValue)
            {
                Report("Waiting for MSBT to close...");
                Process? parent = null;
                try { parent = Process.GetProcessById(waitPid.Value); } catch (ArgumentException) { }
                if (parent != null)
                {
                    using (parent)
                    using (var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(90)))
                        await parent.WaitForExitAsync(timeout.Token);
                }
            }
            if (uninstall) engine.Uninstall();
            else
            {
                var release = waitPid.HasValue ? engine.Pending() : await engine.Latest();
                if (!waitPid.HasValue) await engine.Download(release);
                await Task.Run(() => engine.Apply(release));
                engine.Register(Environment.ProcessPath!, release.Tag);
                Report("MSBT " + release.Tag + " is installed. Use Open MSBT to continue.\n\nIf game mods need updating, use the app's SDK mod install action.\nYour saved settings are kept.");
                launch.Enabled = true;
            }
            Result = 0;
        }
        catch (Exception error) { Result = 1; Report("Setup could not finish: " + error.Message + "\n\nYou can retry with this same installer."); }
        finally { busy = false; install.Enabled = true; }
    }
}
