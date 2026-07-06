$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = Join-Path $RepoRoot "MSBT_External_Beta"
$ExternalFolder = Join-Path $PackageRoot "MattsSDKBoostingTools_external"
$ExeBuildFolder = Join-Path $RepoRoot "dist\MattsBoostingToolsExternal"
$AppSource = Join-Path $RepoRoot "external_app\v22_parts_codes_fixed"
$ResourcesSource = Join-Path $AppSource "resources"
$SdkMod = Join-Path $RepoRoot "MattsSDKBoostingTools.sdkmod"
$SdkBuildScript = Join-Path $RepoRoot "build_sdkmod.ps1"
$ZipPath = Join-Path $RepoRoot "MSBT_External_Beta.zip"

function Assert-UnderRepo {
    param([string]$Path)
    $resolved = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetFullPath($RepoRoot)
    if (-not $resolved.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to operate outside repo: $resolved"
    }
}

if (-not (Test-Path (Join-Path $ExeBuildFolder "MattsBoostingToolsExternal.exe"))) {
    throw "External exe not found. Run .\build_external_exe.ps1 first."
}
$TkinterRuntime = Join-Path $ExeBuildFolder "_internal\_tkinter.pyd"
$TclInit = Join-Path $ExeBuildFolder "_internal\_tcl_data\init.tcl"
if (-not (Test-Path $TkinterRuntime) -or -not (Test-Path $TclInit)) {
    throw "External exe build is missing Tkinter/Tcl runtime files. Rebuild it with a Python install where Tkinter works before packaging."
}
if (Test-Path $SdkBuildScript) {
    & $SdkBuildScript
}
if (-not (Test-Path $SdkMod)) {
    throw "SDK mod package not found: $SdkMod"
}
if (-not (Test-Path $ResourcesSource)) {
    throw "Current external app resources folder not found: $ResourcesSource"
}

Assert-UnderRepo $PackageRoot
Assert-UnderRepo $ZipPath

Remove-Item -Recurse -Force $PackageRoot -ErrorAction SilentlyContinue
Remove-Item -Force $ZipPath -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force $ExternalFolder | Out-Null
Copy-Item -Recurse -Force (Join-Path $ExeBuildFolder "*") $ExternalFolder
Remove-Item -Recurse -Force (Join-Path $ExternalFolder "resources") -ErrorAction SilentlyContinue
Copy-Item -Recurse -Force $ResourcesSource (Join-Path $ExternalFolder "resources")
Copy-Item -Force $SdkMod (Join-Path $PackageRoot "MattsSDKBoostingTools.sdkmod")
Copy-Item -Force (Join-Path $RepoRoot "Launch_MSBT_External_App.bat") (Join-Path $PackageRoot "Launch_MSBT_External_App.bat")

@"
Matt's SDK Boosting Tools external beta

Install:
1. Copy MattsSDKBoostingTools.sdkmod into your Borderlands 4 sdk_mods folder.
2. Copy the MattsSDKBoostingTools_external folder into the same sdk_mods folder.
3. Launch the external app with Launch_MSBT_External_App.bat or the in-game command msbt_external_app.

Python is not required when MattsBoostingToolsExternal.exe is present.
The resources folder stays beside the exe so bookmarks/cache files remain writable.
"@ | Set-Content -Encoding UTF8 (Join-Path $PackageRoot "README_FIRST.txt")

Get-ChildItem -Recurse -Directory $PackageRoot -Filter "__pycache__" | Remove-Item -Recurse -Force

tar.exe -a -c -f $ZipPath -C $RepoRoot "MSBT_External_Beta"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create beta zip: $ZipPath"
}

Write-Host "Packaged beta folder:"
Write-Host $PackageRoot
Write-Host "Packaged beta zip:"
Write-Host $ZipPath
