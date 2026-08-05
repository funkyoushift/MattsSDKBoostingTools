$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$SourceDir = Join-Path $RepoRoot "mod_extracted\MattsSDKBoostingTools"
$BuildRoot = Join-Path $RepoRoot "build\sdkmod"
$StageRoot = Join-Path $BuildRoot "stage"
$PackageDir = Join-Path $StageRoot "MattsSDKBoostingTools"
$Output = Join-Path $RepoRoot "MattsSDKBoostingTools.sdkmod"

function Assert-UnderRepo {
    param([string]$Path)
    $resolved = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetFullPath($RepoRoot)
    if (-not $resolved.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to operate outside repo: $resolved"
    }
}

if (-not (Test-Path $SourceDir)) {
    throw "SDK mod source folder not found: $SourceDir"
}

Assert-UnderRepo $BuildRoot
Assert-UnderRepo $Output

Remove-Item -Recurse -Force $BuildRoot -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force $PackageDir | Out-Null

Copy-Item -Recurse -Force (Join-Path $SourceDir "*") $PackageDir

Get-ChildItem -Recurse -Directory $PackageDir -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -File $PackageDir -Include "*.pyc", "*.pyo" | Remove-Item -Force

Remove-Item -Force $Output -ErrorAction SilentlyContinue

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($StageRoot, $Output)

Write-Host "Built SDK mod package:"
Write-Host $Output
