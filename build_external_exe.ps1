$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$AppSource = Join-Path $RepoRoot "external_app\v22_parts_codes_fixed"
$Entry = Join-Path $AppSource "matts_external_app_v22.py"
$Icon = Join-Path $AppSource "resources\app_icon.ico"
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

& $Python -m PyInstaller --version *> $null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is not available. Install it with: $Python -m pip install pyinstaller"
}

Assert-UnderRepo $BuildRoot
Assert-UnderRepo $DistApp

Remove-Item -Recurse -Force $BuildRoot -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $DistApp -ErrorAction SilentlyContinue

& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --onedir `
    --name $Name `
    --icon $Icon `
    --distpath $DistRoot `
    --workpath $BuildRoot `
    --specpath $BuildRoot `
    $Entry

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

$ResourcesSource = Join-Path $AppSource "resources"
$ResourcesDest = Join-Path $DistApp "resources"
if (-not (Test-Path $ResourcesSource)) {
    throw "Resources folder not found: $ResourcesSource"
}

Remove-Item -Recurse -Force $ResourcesDest -ErrorAction SilentlyContinue
Copy-Item -Recurse -Force $ResourcesSource $ResourcesDest
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
