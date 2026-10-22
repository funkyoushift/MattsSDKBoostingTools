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
        bool apply = (args.Length == 3 || (args.Length == 5 && args[3] == "--game-root" && Path.IsPathFullyQualified(args[4])))
            && args[0] == "--apply" && args[1] == "--wait-pid" && int.TryParse(args[2], out _);
        bool uninstall = args.SequenceEqual(new[] { "--uninstall" });
        if (args.Length != 0 && !apply && !uninstall) return 2;
        using var form = new SetupForm(apply ? int.Parse(args[2]) : null, uninstall, apply && args.Length == 5 ? args[4] : null);
        Application.Run(form);
        return form.Result;
    }
}

sealed class SetupForm : Form
{
    readonly Label status = new() { AutoSize = false, Dock = DockStyle.Fill, Padding = new Padding(20), Text = "Install or update Borderlands 4 Modding Tools from the latest official GitHub release.\n\nYour saved settings are kept. Borderlands 4 is never stopped.\n\nInstallation: " + Engine.DefaultRoot };
    readonly Button install = new() { Text = "Install / Update", AutoSize = true };
    readonly Button launch = new() { Text = "Open Borderlands 4 Modding Tools", AutoSize = true, Enabled = false };
    readonly Button gameFolder = new() { Text = "Choose game folder", AutoSize = true };
    readonly CheckBox reportingEnabled = new() { Text = "Send redacted failure and crash reports automatically", AutoSize = true };
    readonly CheckBox reportingDumps = new() { Text = "Also send crash memory dumps (may contain private data)", AutoSize = true };
    string? selectedGameRoot;
    readonly int? waitPid;
    readonly bool uninstall;
    bool busy;
    public int Result { get; private set; }
    public SetupForm(int? waitPid, bool uninstall, string? gameRoot = null)
    {
        this.waitPid = waitPid; this.uninstall = uninstall;
        selectedGameRoot = gameRoot;
        Text = "Borderlands 4 Modding Tools — Powered by Funk — Setup"; Width = 800; Height = 455; StartPosition = FormStartPosition.CenterScreen;
        MinimumSize = Size;
        var buttons = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 60, Padding = new Padding(15) };
        buttons.Controls.Add(install); buttons.Controls.Add(launch); buttons.Controls.Add(gameFolder);
        gameFolder.Visible = !uninstall;
        gameFolder.Click += (_, _) => {
            using var picker = new FolderBrowserDialog { Description = "Choose the Borderlands 4 folder containing OakGame", UseDescriptionForTitle = true };
            if (picker.ShowDialog(this) == DialogResult.OK) {
                selectedGameRoot = picker.SelectedPath;
                Report("Game folder selected: " + selectedGameRoot + "\n\nUse Install / Update to complete app and game setup.");
            }
        };
        var reportChoice = new FlowLayoutPanel { Dock = DockStyle.Bottom, Height = 101, Padding = new Padding(15, 0, 15, 0), FlowDirection = FlowDirection.TopDown, WrapContents = false };
        reportChoice.Controls.Add(new Label { AutoSize = false, Width = 740, Height = 38,
            Text = "Optional: private Cloudflare reports include limited redacted logs and crash context, never saves or command inputs. Reports are scheduled for deletion after seven days." });
        var savedReporting = ReportingPreferences.Read();
        reportingEnabled.Checked = savedReporting.Enabled;
        reportingDumps.Checked = savedReporting.IncludeDumps;
        reportingDumps.Enabled = reportingEnabled.Checked;
        reportingEnabled.CheckedChanged += (_, _) => { reportingDumps.Enabled = reportingEnabled.Checked; if (!reportingEnabled.Checked) reportingDumps.Checked = false; };
        reportChoice.Controls.Add(reportingEnabled); reportChoice.Controls.Add(reportingDumps);
        reportChoice.Visible = !uninstall && !waitPid.HasValue;
        Controls.Add(status); Controls.Add(reportChoice); Controls.Add(buttons);
        if (uninstall) { install.Text = "Uninstall Borderlands 4 Modding Tools"; status.Text = "Remove the Borderlands 4 Modding Tools app? Saved settings and installed game mods will be kept."; }
        install.Click += async (_, _) => await Run();
        launch.Click += (_, _) => {
            try {
                string appDir = Path.Combine(Engine.DefaultRoot, "app");
                Process.Start(new ProcessStartInfo(Path.Combine(appDir, Engine.Executable)) { UseShellExecute = true, WorkingDirectory = appDir });
                Close();
            } catch (Exception error) { Report("Borderlands 4 Modding Tools was installed, but could not reopen: " + error.Message); }
        };
        Shown += async (_, _) => { if (waitPid.HasValue) await Run(); };
        FormClosing += (_, e) => { if (busy) e.Cancel = true; };
    }

    void Report(string text) { if (InvokeRequired) BeginInvoke(() => status.Text = text); else status.Text = text; }
    async Task Run()
    {
        busy = true; install.Enabled = false; launch.Enabled = false; gameFolder.Enabled = false;
        try
        {
            var engine = new Engine(Engine.DefaultRoot, Report);
            using var gate = engine.Lock();
            if (waitPid.HasValue)
            {
                Report("Waiting for Borderlands 4 Modding Tools to close...");
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
                await engine.InstallGameIntegration(selectedGameRoot);
                if (!waitPid.HasValue) ReportingPreferences.Write(reportingEnabled.Checked, reportingDumps.Checked);
                Report("Borderlands 4 Modding Tools " + release.Tag + " and its game integration are installed. Use Open Borderlands 4 Modding Tools to continue.\n\nExisting SDK/mod-manager installations and your saved settings are kept.");
                launch.Enabled = true;
            }
            Result = 0;
        }
        catch (Exception error) { Result = 1; Report("Setup could not finish: " + error.Message + "\n\nYou can retry with this same installer."); }
        finally { busy = false; install.Enabled = true; gameFolder.Enabled = true; }
        // Restart-and-install is a complete handoff; interactive Setup still offers Open Borderlands 4 Modding Tools.
        if (Result == 0 && waitPid.HasValue && !uninstall && launch.Enabled) launch.PerformClick();
    }
}
