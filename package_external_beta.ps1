$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = Join-Path $RepoRoot "MSBT_External_Beta"
$ExternalFolder = Join-Path $PackageRoot "MattsSDKBoostingTools_external"
$ExeBuildFolder = Join-Path $RepoRoot "dist\MattsBoostingToolsExternal"
$AppSource = Join-Path $RepoRoot "external_app\v22_parts_codes_fixed"
$ResourcesSource = Join-Path $AppSource "resources"
$MattEditorSource = Join-Path $AppSource "matt_editor"
$MattEditorAdapter = Join-Path $AppSource "matt_editor_adapter.js"
$SdkMod = Join-Path $RepoRoot "MattsSDKBoostingTools.sdkmod"
$SdkBuildScript = Join-Path $RepoRoot "build_sdkmod.ps1"
$LegacyZipPath = Join-Path $RepoRoot "MSBT_External_Beta.zip"
$ZipPath = $LegacyZipPath
$ReleasesFolder = Join-Path $RepoRoot "releases"
$LatestManifestPath = Join-Path $ReleasesFolder "latest.json"
$ElectronPackageJson = Join-Path $RepoRoot "electron_poc\package.json"

function Assert-UnderRepo {
    param([string]$Path)
    $resolved = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetFullPath($RepoRoot)
    if (-not $resolved.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to operate outside repo: $resolved"
    }
}

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Text
    )
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
}

function Get-ElectronPackageVersion {
    if (-not (Test-Path $ElectronPackageJson)) {
        throw "Electron package.json not found: $ElectronPackageJson"
    }
    $pkg = Get-Content -Raw $ElectronPackageJson | ConvertFrom-Json
    $version = [string]$pkg.version
    if (-not ($version -match '^\d+\.\d+\.\d+(-(?:alpha|beta)\.\d+)?$')) {
        throw "Electron package version must use public SemVer format, got: $version"
    }
    return $version
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
if (-not (Test-Path (Join-Path $MattEditorSource "index.html"))) {
    throw "Current Mattmab editor assets folder not found: $MattEditorSource"
}
if (-not (Test-Path $MattEditorAdapter)) {
    throw "Current Mattmab editor adapter not found: $MattEditorAdapter"
}

Assert-UnderRepo $PackageRoot
Assert-UnderRepo $ReleasesFolder

$ElectronVersion = Get-ElectronPackageVersion
$PackageVersion = $ElectronVersion
$ReleaseTag = "v$PackageVersion"
$PortableZipName = "MattsSDKBoostingTools-Portable-v$PackageVersion.zip"
$ZipPath = Join-Path $RepoRoot $PortableZipName
Assert-UnderRepo $ZipPath

Remove-Item -Recurse -Force $PackageRoot -ErrorAction SilentlyContinue
Remove-Item -Force $ZipPath -ErrorAction SilentlyContinue
Remove-Item -Force $LegacyZipPath -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force $ExternalFolder | Out-Null
Copy-Item -Recurse -Force (Join-Path $ExeBuildFolder "*") $ExternalFolder
Remove-Item -Recurse -Force (Join-Path $ExternalFolder "resources") -ErrorAction SilentlyContinue
Copy-Item -Recurse -Force $ResourcesSource (Join-Path $ExternalFolder "resources")
Remove-Item -Recurse -Force (Join-Path $ExternalFolder "matt_editor") -ErrorAction SilentlyContinue
Copy-Item -Recurse -Force $MattEditorSource (Join-Path $ExternalFolder "matt_editor")
Copy-Item -Force $MattEditorAdapter (Join-Path $ExternalFolder "matt_editor_adapter.js")
Copy-Item -Force $SdkMod (Join-Path $PackageRoot "MattsSDKBoostingTools.sdkmod")
Copy-Item -Force (Join-Path $RepoRoot "Launch_MSBT_External_App.bat") (Join-Path $PackageRoot "Launch_MSBT_External_App.bat")

$GitCommit = ""
$ShortCommit = ""
try {
    $GitCommit = (& git -C $RepoRoot rev-parse HEAD).Trim()
    $ShortCommit = (& git -C $RepoRoot rev-parse --short HEAD).Trim()
} catch {
    $GitCommit = ""
    $ShortCommit = ""
}
$BuiltAtUtc = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
$SdkHash = (Get-FileHash -Algorithm SHA256 $SdkMod).Hash.ToLowerInvariant()
$ExePath = Join-Path $ExternalFolder "MattsBoostingToolsExternal.exe"
$ExeHash = (Get-FileHash -Algorithm SHA256 $ExePath).Hash.ToLowerInvariant()
$UiLayoutPath = Join-Path $ExternalFolder "resources\ui_layout.json"
$ResourcesHash = if (Test-Path $UiLayoutPath) { (Get-FileHash -Algorithm SHA256 $UiLayoutPath).Hash.ToLowerInvariant() } else { "" }
$DownloadUrl = "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/$ReleaseTag/$PortableZipName"
$LatestManifestUrl = "https://raw.githubusercontent.com/funkyoushift/MattsSDKBoostingTools/main/releases/latest.json"
$ReleaseUrl = "https://github.com/funkyoushift/MattsSDKBoostingTools/releases"
$ElectronInstallerName = "MattsSDKBoostingTools-Setup-v$ElectronVersion.exe"
$ElectronDownloadUrl = "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/$ReleaseTag/$ElectronInstallerName"
$ElectronUpdaterManifestUrl = "https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/$ReleaseTag/latest.yml"

$VersionInfo = [ordered]@{
    package_version = $PackageVersion
    app_version = $PackageVersion
    sdkmod_version = $PackageVersion
    resources_version = $PackageVersion
    git_commit = $GitCommit
    built_at_utc = $BuiltAtUtc
    sdk_required = "oak2-mod-manager v0.3"
    sdk_required_url = "https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3"
    download_url = $DownloadUrl
    manual_zip_download_url = $DownloadUrl
    electron_version = $ElectronVersion
    electron_installer_name = $ElectronInstallerName
    electron_installer_download_url = $ElectronDownloadUrl
    electron_updater_manifest_url = $ElectronUpdaterManifestUrl
    release_url = $ReleaseUrl
    latest_manifest_url = $LatestManifestUrl
    external_exe_sha256 = $ExeHash
    sdkmod_sha256 = $SdkHash
    ui_layout_sha256 = $ResourcesHash
}
Write-Utf8NoBom (Join-Path $ExternalFolder "resources\version_info.json") ($VersionInfo | ConvertTo-Json -Depth 4)

$ReadmeText = @"
Matt's SDK Boosting Tools external beta

Package version:
$PackageVersion

Requires SDK 03 / oak2-mod-manager v0.3:
https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3

Install:
1. Install or update to oak2-mod-manager v0.3.
2. Copy MattsSDKBoostingTools.sdkmod into your Borderlands 4 sdk_mods folder.
3. Copy the MattsSDKBoostingTools_external folder into the same sdk_mods folder.
4. Launch the external app with Launch_MSBT_External_App.bat or the in-game command msbt_external_app.

Python is not required when MattsBoostingToolsExternal.exe is present.
The resources folder stays beside the exe so bookmarks/cache files remain writable.
The matt_editor folder stays beside the exe so the embedded/local Mattmab item editor can run without internet, Electron, or Node.
"@
Write-Utf8NoBom (Join-Path $PackageRoot "README_FIRST.txt") $ReadmeText

Get-ChildItem -Recurse -Directory $PackageRoot -Filter "__pycache__" | Remove-Item -Recurse -Force

tar.exe -a -c -f $ZipPath -C $RepoRoot "MSBT_External_Beta"
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create beta zip: $ZipPath"
}

New-Item -ItemType Directory -Force $ReleasesFolder | Out-Null
$ZipHash = (Get-FileHash -Algorithm SHA256 $ZipPath).Hash.ToLowerInvariant()
$LatestManifest = [ordered]@{
    package_version = $PackageVersion
    app_version = $PackageVersion
    sdkmod_version = $PackageVersion
    resources_version = $PackageVersion
    git_commit = $GitCommit
    built_at_utc = $BuiltAtUtc
    sdk_required = "oak2-mod-manager v0.3"
    sdk_required_url = "https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3"
    download_url = $DownloadUrl
    manual_zip_download_url = $DownloadUrl
    electron_version = $ElectronVersion
    electron_installer_name = $ElectronInstallerName
    electron_installer_download_url = $ElectronDownloadUrl
    electron_updater_manifest_url = $ElectronUpdaterManifestUrl
    release_url = $ReleaseUrl
    latest_manifest_url = $LatestManifestUrl
    external_exe_sha256 = $ExeHash
    sdkmod_sha256 = $SdkHash
    ui_layout_sha256 = $ResourcesHash
    beta_zip_sha256 = $ZipHash
}
Write-Utf8NoBom $LatestManifestPath ($LatestManifest | ConvertTo-Json -Depth 4)

Write-Host "Packaged beta folder:"
Write-Host $PackageRoot
Write-Host "Packaged beta zip:"
Write-Host $ZipPath
Write-Host "Latest update manifest:"
Write-Host $LatestManifestPath
Write-Host "Publish the ZIP to GitHub Releases with:"
Write-Host ".\publish_github_release.ps1"
