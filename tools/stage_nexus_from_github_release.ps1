param(
    [string]$ManifestPath = ".\docs\releases\latest.json",
    [string]$OutputRoot = ".\_nexus_upload",
    [switch]$OpenFolder
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ResolvedManifestPath = Join-Path $RepoRoot $ManifestPath
if (-not (Test-Path $ResolvedManifestPath)) {
    throw "Release manifest not found: $ResolvedManifestPath"
}

$Manifest = Get-Content -Raw $ResolvedManifestPath | ConvertFrom-Json
$Version = [string]$Manifest.package_version
$InstallerName = [string]$Manifest.electron_installer_name
$InstallerUrl = [string]$Manifest.electron_installer_download_url
$PortableUrl = [string]$Manifest.manual_zip_download_url

if ([string]::IsNullOrWhiteSpace($Version)) {
    throw "Manifest is missing package_version."
}
if ([string]::IsNullOrWhiteSpace($InstallerName) -or [string]::IsNullOrWhiteSpace($InstallerUrl)) {
    throw "Manifest is missing Electron installer name/download URL."
}
if ([string]::IsNullOrWhiteSpace($PortableUrl)) {
    throw "Manifest is missing manual ZIP download URL."
}

$ResolvedOutputRoot = Join-Path $RepoRoot $OutputRoot
$StageDir = Join-Path $ResolvedOutputRoot "MSBT-v$Version"
$InstallerPath = Join-Path $StageDir $InstallerName
$PortableName = Split-Path -Leaf ([System.Uri]$PortableUrl).LocalPath
$PortablePath = Join-Path $StageDir $PortableName
$ReadmePath = Join-Path $StageDir "NEXUS_UPLOAD_NOTES.txt"

New-Item -ItemType Directory -Force -Path $StageDir | Out-Null

function Save-ReleaseAsset {
    param(
        [Parameter(Mandatory=$true)][string]$Url,
        [Parameter(Mandatory=$true)][string]$Path
    )
    Write-Host "Downloading $Url"
    Invoke-WebRequest -Uri $Url -OutFile $Path
    if (-not (Test-Path $Path)) {
        throw "Download failed: $Path"
    }
}

Save-ReleaseAsset -Url $InstallerUrl -Path $InstallerPath
Save-ReleaseAsset -Url $PortableUrl -Path $PortablePath

$Notes = @"
MSBT Nexus upload staging

Version: $Version
GitHub release: $($Manifest.release_url)

Upload these two files to Nexus Mods:

1. $InstallerName
   Display name: MSBT Installer v$Version
   Category: Main
   Description: Recommended download for most users. Installs the MSBT Electron app, bundled SDK mod, ActorScriptDeployer support files, and required runtime files.

2. $PortableName
   Display name: Portable ZIP - MSBT v$Version
   Category: Main
   Description: Optional manual portable package. Use this if you do not want to run the installer. Extract the ZIP and run the app manually.

Do not upload latest.json, latest.yml, blockmap files, build folders, source snapshots, or old legacy packages to Nexus.

After Nexus upload finishes, run:
powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\check_nexus_release.ps1
"@

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($ReadmePath, $Notes, $utf8NoBom)

Write-Host "Nexus upload staging complete:"
Write-Host $StageDir

if ($OpenFolder) {
    Invoke-Item $StageDir
}
