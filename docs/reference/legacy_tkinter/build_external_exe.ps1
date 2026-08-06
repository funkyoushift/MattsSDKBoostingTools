param(
    [switch]$SkipDependencyInstall
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppSource = Join-Path $RepoRoot "external_app\v22_parts_codes_fixed"
$Entry = Join-Path $AppSource "matts_external_app_v22.py"
$Icon = Join-Path $AppSource "resources\app_icon.ico"
$BuildRequirements = Join-Path $RepoRoot "requirements-external-build.txt"
$BuildRoot = Join-Path $RepoRoot "build\external_exe"
$DistRoot = Join-Path $RepoRoot "dist"
$Name = "MattsBoostingToolsExternal"
$DistApp = Join-Path $DistRoot $Name
$Python = $env:MSBT_PYTHON

function Assert-UnderRepo {
    param([string]$Path)
    $resolved = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetFullPath($RepoRoot)
    if (-not $resolved.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to operate outside repo: $resolved"
    }
}

if (-not (Test-Path $Entry)) {
    throw "External app entry file not found: $Entry"
}
if (-not (Test-Path $Icon)) {
    throw "External app icon not found: $Icon"
}

if (-not $Python) {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        $Python = $PythonCommand.Source
    }
}
if (-not $Python) {
    throw "Python is not available. Set MSBT_PYTHON to a Python executable with PyInstaller installed."
}
if (-not (Test-Path $BuildRequirements)) {
    throw "Build requirements file not found: $BuildRequirements"
}

if (-not $SkipDependencyInstall) {
    & $Python -m pip --version *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "pip is not available for this Python. Use a Python install with pip, or set MSBT_PYTHON to one."
    }
    & $Python -m pip install --upgrade -r $BuildRequirements
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install external app build requirements from: $BuildRequirements"
    }
}

& $Python -m PyInstaller --version *> $null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is not available. Run without -SkipDependencyInstall or install requirements from: $BuildRequirements"
}
& $Python -c "import webview; print(getattr(webview, '__version__', 'pywebview'))" *> $null
if ($LASTEXITCODE -ne 0) {
    throw "pywebview is not available. Run without -SkipDependencyInstall or install requirements from: $BuildRequirements"
}

Assert-UnderRepo $BuildRoot
Assert-UnderRepo $DistApp

Remove-Item -Recurse -Force $BuildRoot -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $DistApp -ErrorAction SilentlyContinue

$WebViewPyInstallerArgs = @(
    "--collect-all", "webview",
    "--hidden-import", "webview",
    "--hidden-import", "webview.platforms.edgechromium",
    "--hidden-import", "webview.platforms.winforms",
    "--hidden-import", "webview.platforms.mshtml",
    "--hidden-import", "clr",
    "--hidden-import", "pythonnet"
)
Write-Host "pywebview detected; embedded Mattmab editor support will be bundled."

$PyInstallerArgs = @(
    "--noconfirm",
    "--clean",
    "--windowed",
    "--onedir",
    "--name", $Name,
    "--icon", $Icon,
    "--distpath", $DistRoot,
    "--workpath", $BuildRoot,
    "--specpath", $BuildRoot
) + $WebViewPyInstallerArgs + @($Entry)

& $Python -m PyInstaller @PyInstallerArgs

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

$ResourcesSource = Join-Path $AppSource "resources"
$ResourcesDest = Join-Path $DistApp "resources"
if (-not (Test-Path $ResourcesSource)) {
    throw "Resources folder not found: $ResourcesSource"
}
$MattEditorSource = Join-Path $AppSource "matt_editor"
$MattEditorDest = Join-Path $DistApp "matt_editor"
$MattEditorAdapter = Join-Path $AppSource "matt_editor_adapter.js"
if (-not (Test-Path (Join-Path $MattEditorSource "index.html"))) {
    throw "Mattmab editor assets not found: $MattEditorSource"
}
if (-not (Test-Path $MattEditorAdapter)) {
    throw "Mattmab editor adapter not found: $MattEditorAdapter"
}

Remove-Item -Recurse -Force $ResourcesDest -ErrorAction SilentlyContinue
Copy-Item -Recurse -Force $ResourcesSource $ResourcesDest
Remove-Item -Recurse -Force $MattEditorDest -ErrorAction SilentlyContinue
Copy-Item -Recurse -Force $MattEditorSource $MattEditorDest
Copy-Item -Force $MattEditorAdapter (Join-Path $DistApp "matt_editor_adapter.js")
Copy-Item -Force (Join-Path $RepoRoot "Launch_MSBT_External_App.bat") (Join-Path $DistApp "Launch_MSBT_External_App.bat")
Copy-Item -Force (Join-Path $AppSource "Launch_MattsBoostingTools_External.bat") (Join-Path $DistApp "Launch_MattsBoostingTools_External.bat")

Get-ChildItem -Recurse -Directory $DistApp -Filter "__pycache__" | Remove-Item -Recurse -Force

$TkinterRuntime = Join-Path $DistApp "_internal\_tkinter.pyd"
$TclInit = Join-Path $DistApp "_internal\_tcl_data\init.tcl"
if (-not (Test-Path $TkinterRuntime) -or -not (Test-Path $TclInit)) {
    throw "Built external exe is missing Tkinter/Tcl runtime files. Rebuild with a Python install where Tkinter can create a Tk root."
}

Write-Host "Built external app:"
Write-Host (Join-Path $DistApp "$Name.exe")
Write-Host "Resources copied beside the exe:"
Write-Host $ResourcesDest
Write-Host "Mattmab editor assets copied beside the exe:"
Write-Host $MattEditorDest
