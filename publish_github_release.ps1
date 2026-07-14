param(
    [string]$Repository = "funkyoushift/MattsSDKBoostingTools",
    [string]$TagName = "",
    [string]$Title = "",
    [switch]$Draft
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ManifestPath = Join-Path $RepoRoot "releases\latest.json"
$ElectronDist = Join-Path $RepoRoot "dist_electron"
$ElectronPackageJson = Join-Path $RepoRoot "electron_poc\package.json"

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

function Get-ReleaseTitle {
    param([Parameter(Mandatory=$true)][string]$Version)
    if ($Version -match '^(\d+\.\d+\.\d+)-beta\.(\d+)$') {
        return "Matt's SDK Boosting Tools v$($Matches[1]) Beta $($Matches[2])"
    }
    if ($Version -match '^(\d+\.\d+\.\d+)-alpha\.(\d+)$') {
        return "Matt's SDK Boosting Tools v$($Matches[1]) Alpha $($Matches[2])"
    }
    return "Matt's SDK Boosting Tools v$Version"
}

function Test-PrereleaseVersion {
    param([Parameter(Mandatory=$true)][string]$Version)
    # Public beta builds should be treated as the latest release so the app can
    # read /releases/latest/download/latest.json. Alpha builds stay prerelease.
    return [bool]($Version -match '-alpha\.\d+$')
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI 'gh' was not found. Install it and run 'gh auth login', then rerun this script."
}

$PackageVersion = Get-ElectronPackageVersion
$ExpectedTagName = "v$PackageVersion"
$Prerelease = Test-PrereleaseVersion $PackageVersion
$ZipName = "MattsSDKBoostingTools-Legacy-Tkinter-Portable-v$PackageVersion.zip"
$ZipPath = Join-Path $RepoRoot $ZipName
$ElectronInstallerName = "MattsSDKBoostingTools-Setup-v$PackageVersion.exe"

if ($TagName -and $TagName -ne $ExpectedTagName) {
    throw "TagName '$TagName' does not match electron_poc\package.json version '$ExpectedTagName'."
}
if (-not $TagName) {
    $TagName = $ExpectedTagName
}
if (-not $Title) {
    $Title = Get-ReleaseTitle $PackageVersion
}
if ($Title -match '\d{8,}|beta-[0-9a-f]{6,}|run|workflow|commit') {
    throw "Release title must not be generated from timestamps, run IDs, or commit hashes: $Title"
}

if (-not (Test-Path $ZipPath)) {
    throw "Portable ZIP not found: $ZipPath. Run .\package_external_beta.ps1 first."
}

$ElectronInstaller = Join-Path $ElectronDist $ElectronInstallerName
if (-not (Test-Path $ElectronInstaller)) {
    throw "Electron installer not found: $ElectronInstaller. Run .\build_electron_beta.ps1 -Installer first."
}

$latestYml = Join-Path $ElectronDist "latest.yml"
if (-not (Test-Path $latestYml)) {
    throw "Electron updater manifest not found: $latestYml"
}
$latestYmlText = Get-Content -Raw $latestYml
if ($latestYmlText -notmatch "(?m)^version:\s*$([regex]::Escape($PackageVersion))\s*$") {
    throw "latest.yml version does not match package version $PackageVersion."
}
if (-not (Test-Path $ManifestPath)) {
    throw "Release update manifest not found: $ManifestPath. Run .\package_external_beta.ps1 first."
}
$PackagedManifestPath = Join-Path $ElectronDist "win-unpacked\resources\releases\latest.json"
if (-not (Test-Path $PackagedManifestPath)) {
    throw "Packaged Electron release manifest not found: $PackagedManifestPath. Run .\package_external_beta.ps1, then .\build_electron_beta.ps1 -Installer."
}
$PackagedManifest = Get-Content -Raw $PackagedManifestPath | ConvertFrom-Json
if ([string]$PackagedManifest.package_version -ne $PackageVersion) {
    throw "Packaged Electron release manifest package_version '$($PackagedManifest.package_version)' does not match package version '$PackageVersion'. Run .\package_external_beta.ps1, then .\build_electron_beta.ps1 -Installer."
}

$ElectronAssets = @($ElectronInstaller)
$blockMap = "$ElectronInstaller.blockmap"
if (Test-Path $blockMap) {
    $ElectronAssets += $blockMap
}
$ElectronAssets += $latestYml
$ElectronAssets += $ManifestPath
$ElectronUnpackedZipName = "MattsSDKBoostingTools-Electron-Portable-v$PackageVersion-win-x64.zip"
$ElectronUnpackedZip = Join-Path $ElectronDist $ElectronUnpackedZipName
if (Test-Path $ElectronUnpackedZip) {
    $ElectronAssets += $ElectronUnpackedZip
}

$shortCommit = ""
try {
    $shortCommit = (& git -C $RepoRoot rev-parse --short HEAD).Trim()
} catch {
    $shortCommit = [DateTime]::UtcNow.ToString("yyyyMMddHHmm")
}
$BuiltAtUtc = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")

$Manifest = $null
if (Test-Path $ManifestPath) {
    $Manifest = Get-Content -Raw $ManifestPath | ConvertFrom-Json
    if ($Manifest.package_version -and [string]$Manifest.package_version -ne $PackageVersion) {
        throw "releases\latest.json package_version '$($Manifest.package_version)' does not match package version '$PackageVersion'. Run .\package_external_beta.ps1."
    }
}

$notes = @"
### What's new

Electron beta build for Matt's SDK Boosting Tools.

### Fixed

See the repository commit history for fixes included in this build.

### Known issues

Electron is still a beta replacement path. Keep the legacy/Tkinter package available as a rollback while beta testing continues.

### Download: pick ONE

**Recommended for almost everyone**

Download and run:
- $ElectronInstallerName

This is the Windows installer. It installs the Electron app, adds shortcuts, and includes the bundled SDK mod/update resources.

**Manual install / portable Electron app**

Download and extract:
- $ElectronUnpackedZipName

Use this if you want the Electron app without running the installer. It contains the Electron app files plus bundled SDK mod/update resources.

**Legacy rollback ZIP**

- $ZipName

This is the older Tkinter/manual package kept as a rollback while Electron beta testing continues.

**Do not manually download these unless you know why**

- latest.json
- latest.yml
- *.blockmap

These are update-system files used by the app/installer.

**Source code**

GitHub's automatic Source code ZIP/TAR files are for developers. They are not the ready-to-run app.

### Upgrade notes

Requires SDK 03 / oak2-mod-manager v0.3:
https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3

### Build information

- Version: $PackageVersion
- Commit: $shortCommit
- Build date: $BuiltAtUtc
"@

$NotesPath = Join-Path ([System.IO.Path]::GetTempPath()) "msbt_release_notes_$TagName.md"
Write-Utf8NoBom $NotesPath $notes

$releaseExists = $false
$previousErrorActionPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = "Continue"
    & gh release view $TagName --repo $Repository 1>$null 2>$null
    if ($LASTEXITCODE -eq 0) {
        $releaseExists = $true
    }
} finally {
    $ErrorActionPreference = $previousErrorActionPreference
}

if ($releaseExists) {
    $assets = @($ZipPath) + $ElectronAssets
    & gh release upload $TagName @assets --repo $Repository --clobber
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload assets to existing GitHub Release $TagName."
    }
    $editArgs = @("release", "edit", $TagName, "--repo", $Repository, "--title", $Title, "--notes-file", $NotesPath)
    if ($Prerelease) {
        $editArgs += "--prerelease"
    } else {
        $editArgs += "--latest"
    }
    & gh @editArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to update GitHub Release $TagName metadata."
    }
} else {
    $assets = @($ZipPath) + $ElectronAssets
    $ghArgs = @("release", "create", $TagName) + $assets + @("--repo", $Repository, "--title", $Title, "--notes-file", $NotesPath)
    if ($Draft) {
        $ghArgs += "--draft"
    }
    if ($Prerelease) {
        $ghArgs += "--prerelease"
    } else {
        $ghArgs += "--latest"
    }
    & gh @ghArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create GitHub Release $TagName."
    }
}

Write-Host "Published beta assets to GitHub Release:"
Write-Host "https://github.com/$Repository/releases/tag/$TagName"
