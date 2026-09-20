param(
    [string]$Repository = "funkyoushift/MattsSDKBoostingTools",
    [string]$TagName = "",
    [string]$Title = "",
    [switch]$Draft,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ManifestPath = Join-Path $RepoRoot "docs\releases\latest.json"
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

function Assert-ReleaseFile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf) -or (Get-Item -LiteralPath $Path).Length -eq 0) {
        throw "Required release artifact is missing or empty: $Path"
    }
}

function Get-StreamSha256 {
    param([System.IO.Stream]$Stream)
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($algorithm.ComputeHash($Stream))).Replace('-', '').ToLowerInvariant() }
    finally { $algorithm.Dispose() }
}

function Get-ReleaseFileSha256 {
    param([string]$Path)
    $stream = [System.IO.File]::OpenRead($Path)
    try { return Get-StreamSha256 $stream }
    finally { $stream.Dispose() }
}

function Assert-PortableEmbeddedFile {
    param($Archive, [string]$EntryName, [string]$ExpectedSha256)
    $entry = $Archive.GetEntry($EntryName)
    if ($null -eq $entry) { throw "Portable ZIP is missing $EntryName" }
    $stream = $entry.Open()
    try { $actual = Get-StreamSha256 $stream }
    finally { $stream.Dispose() }
    if ($actual -ne $ExpectedSha256) { throw "Portable ZIP has mismatched embedded file: $EntryName" }
}

function Read-UpdaterYaml {
    param([string]$Path)
    $yamlModule = Join-Path $RepoRoot 'electron_poc\node_modules\js-yaml'
    if (-not (Get-Command node -ErrorAction SilentlyContinue) -or -not (Test-Path -LiteralPath $yamlModule)) {
        throw 'Updater verification requires Node and the installed Electron dependencies (npm ci).'
    }
    $parseYaml = "const fs=require('node:fs');const yaml=require(process.argv[1]);process.stdout.write(JSON.stringify(yaml.load(fs.readFileSync(process.argv[2],'utf8'))));"
    $parsed = & node -e $parseYaml $yamlModule $Path
    if ($LASTEXITCODE -ne 0) { throw 'Could not parse latest.yml.' }
    return ($parsed | ConvertFrom-Json)
}

function Get-ElectronSemverVersion {
    if (-not (Test-Path $ElectronPackageJson)) {
        throw "Electron package.json not found: $ElectronPackageJson"
    }
    $pkg = Get-Content -Raw $ElectronPackageJson | ConvertFrom-Json
    $version = [string]$pkg.version
    if (-not ($version -match '^\d+\.\d+\.\d+(-(?:alpha|beta)\.\d+)?$')) {
        throw "Electron package version must use npm SemVer (MAJOR.MINOR.PATCH), got: $version"
    }
    return $version
}

function Get-PublicReleaseVersion {
    if (-not (Test-Path $ElectronPackageJson)) {
        throw "Electron package.json not found: $ElectronPackageJson"
    }
    $pkg = Get-Content -Raw $ElectronPackageJson | ConvertFrom-Json
    $releaseVersion = [string]$pkg.msbtReleaseVersion
    if (-not $releaseVersion) {
        $releaseVersion = [string]$pkg.version
    }
    if (-not ($releaseVersion -match '^\d+\.\d+\.\d+(\.\d+)?(-(?:alpha|beta)\.\d+)?$')) {
        throw "Public release version (msbtReleaseVersion) must use MSBT format, got: $releaseVersion"
    }
    return $releaseVersion
}

function Get-ElectronPackageVersion {
    return Get-PublicReleaseVersion
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
    # Public beta builds still count as latest so old app versions can read
    # /releases/latest/download/latest.json. Alpha builds stay prerelease.
    return [bool]($Version -match '-alpha\.\d+$')
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI 'gh' was not found. Install it and run 'gh auth login', then rerun this script."
}
if ($Repository -notmatch '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$') {
    throw "Repository must be OWNER/REPO: $Repository"
}

$PackageVersion = Get-PublicReleaseVersion
$ElectronSemver = Get-ElectronSemverVersion
$ExpectedTagName = "v$PackageVersion"
$Prerelease = Test-PrereleaseVersion $PackageVersion
$ElectronInstallerName = "MSBT-Installer-v$PackageVersion.exe"

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

$ElectronInstaller = Join-Path $ElectronDist $ElectronInstallerName
if (-not (Test-Path $ElectronInstaller)) {
    throw "Electron installer not found: $ElectronInstaller. Run .\tools\build_electron_beta.ps1 -Installer first."
}

$latestYml = Join-Path $ElectronDist "latest.yml"
if (-not (Test-Path $latestYml)) {
    throw "Electron updater manifest not found: $latestYml"
}
$updater = Read-UpdaterYaml $latestYml
if ([string]$updater.version -ne $ElectronSemver) {
    throw "latest.yml version does not match npm package version $ElectronSemver."
}
$installerRows = @($updater.files | Where-Object { [string]$_.url -ceq $ElectronInstallerName })
if ($installerRows.Count -ne 1 -or [string]$updater.path -cne $ElectronInstallerName) {
    throw 'latest.yml must identify exactly the expected installer in files[] and path.'
}
$installerStream = [System.IO.File]::OpenRead($ElectronInstaller)
$sha512 = [System.Security.Cryptography.SHA512]::Create()
try { $installerSha512 = [Convert]::ToBase64String($sha512.ComputeHash($installerStream)) }
finally { $installerStream.Dispose(); $sha512.Dispose() }
if ([string]$installerRows[0].sha512 -cne $installerSha512 -or [string]$updater.sha512 -cne $installerSha512 -or
    [long]$installerRows[0].size -ne (Get-Item -LiteralPath $ElectronInstaller).Length) {
    throw 'Installer SHA512/bytes do not match latest.yml.'
}
if (-not (Test-Path $ManifestPath)) {
    throw "Release update manifest not found: $ManifestPath."
}
$AppUpdateYml = Join-Path $ElectronDist "win-unpacked\resources\app-update.yml"
Assert-ReleaseFile $AppUpdateYml
$appUpdateText = Get-Content -Raw -LiteralPath $AppUpdateYml
if ($appUpdateText -notmatch '(?m)^provider:\s*github\s*$' -or
    $appUpdateText -notmatch '(?m)^owner:\s*funkyoushift\s*$' -or
    $appUpdateText -notmatch '(?m)^repo:\s*MattsSDKBoostingTools\s*$') {
    throw 'Packaged app-update.yml must enable electron-updater against GitHub (funkyoushift/MattsSDKBoostingTools).'
}
$PackagedManifestPath = Join-Path $ElectronDist "win-unpacked\resources\releases\latest.json"
if (-not (Test-Path $PackagedManifestPath)) {
    throw "Packaged Electron release manifest not found: $PackagedManifestPath. Run .\tools\build_electron_beta.ps1 -Installer."
}
$PackagedManifest = Get-Content -Raw $PackagedManifestPath | ConvertFrom-Json
if ([string]$PackagedManifest.package_version -ne $PackageVersion) {
    throw "Packaged Electron release manifest package_version '$($PackagedManifest.package_version)' does not match package version '$PackageVersion'. Run .\tools\build_electron_beta.ps1 -Installer."
}

# Always publish the packaged latest.json so remote update checks match the
# installer-bundled manifest. Post-release git_commit refreshes caused false
# same-version rebuild prompts when they diverged from the baked file.
$Manifest = $PackagedManifest

$ElectronAssets = @($ElectronInstaller)
$blockMap = "$ElectronInstaller.blockmap"
if (Test-Path $blockMap) {
    $ElectronAssets += $blockMap
}
$ElectronAssets += $latestYml
$ElectronAssets += $PackagedManifestPath
$ElectronUnpackedZipName = "MSBT-Portable-v$PackageVersion-win-x64.zip"
$ElectronUnpackedZip = Join-Path $ElectronDist $ElectronUnpackedZipName
Assert-ReleaseFile $ElectronUnpackedZip
$ElectronAssets += $ElectronUnpackedZip
$SdkMod = Join-Path $RepoRoot 'MattsSDKBoostingTools.sdkmod'
$EmbeddedSdkMod = Join-Path $ElectronDist 'win-unpacked\resources\sdkmod\MattsSDKBoostingTools.sdkmod'
Assert-ReleaseFile $SdkMod
Assert-ReleaseFile $EmbeddedSdkMod
$sdkSha256 = Get-ReleaseFileSha256 $SdkMod
if ((Get-ReleaseFileSha256 $EmbeddedSdkMod) -ne $sdkSha256) {
    throw 'Installer staging contains a different SDK mod than the standalone release artifact.'
}
if ([string]$PackagedManifest.sdkmod_version -ne $PackageVersion) {
    throw 'Packaged latest.json SDK version does not match the release version.'
}
Add-Type -AssemblyName System.IO.Compression.FileSystem
$portableArchive = [System.IO.Compression.ZipFile]::OpenRead($ElectronUnpackedZip)
try {
    $portableRoot = "MSBT-Portable-v$PackageVersion-win-x64/resources/"
    Assert-PortableEmbeddedFile $portableArchive ($portableRoot + 'sdkmod/MattsSDKBoostingTools.sdkmod') $sdkSha256
    $manifestSha256 = Get-ReleaseFileSha256 $PackagedManifestPath
    Assert-PortableEmbeddedFile $portableArchive ($portableRoot + 'releases/latest.json') $manifestSha256
    $appUpdateSha256 = Get-ReleaseFileSha256 $AppUpdateYml
    Assert-PortableEmbeddedFile $portableArchive ($portableRoot + 'app-update.yml') $appUpdateSha256
} finally { $portableArchive.Dispose() }
$ElectronAssets += $SdkMod
$MobileVersionJson = Join-Path $RepoRoot "docs\releases\mobile-version.json"
Assert-ReleaseFile $MobileVersionJson
$MobileVersion = Get-Content -Raw $MobileVersionJson | ConvertFrom-Json
if ([string]$MobileVersion.versionName -notmatch '^\d+\.\d+\.\d+$' -or [int]$MobileVersion.versionCode -lt 1) {
    throw 'mobile-version.json requires a versionName and positive versionCode.'
}
$rollingApkName = 'MSBT-Mobile-Controller.apk'
$versionedApkName = "MSBT-Mobile-Controller-$($MobileVersion.versionName).apk"
if ([IO.Path]::GetFileName(([Uri]$MobileVersion.apkUrl).AbsolutePath) -cne $rollingApkName -or
    [IO.Path]::GetFileName(([Uri]$MobileVersion.apkVersionedUrl).AbsolutePath) -cne $versionedApkName -or
    [string]$Manifest.mobile_apk_version -ne [string]$MobileVersion.versionName) {
    throw 'Mobile APK names/version do not match mobile-version.json and packaged latest.json.'
}
$ElectronAssets += $MobileVersionJson
$MobileApkDir = Join-Path $RepoRoot "dist_mobile"
$rollingApk = Join-Path $MobileApkDir $rollingApkName
$versionedApk = Join-Path $MobileApkDir $versionedApkName
Assert-ReleaseFile $rollingApk
Assert-ReleaseFile $versionedApk
if ((Get-ReleaseFileSha256 $rollingApk) -ne (Get-ReleaseFileSha256 $versionedApk)) {
    throw 'Rolling and versioned Android APKs differ.'
}
$ElectronAssets += @($rollingApk, $versionedApk)
$ChecksumFile = Join-Path $RepoRoot 'SHA256SUMS.txt'
if (Test-Path -LiteralPath $ChecksumFile) { $ElectronAssets += $ChecksumFile }

$HeadCommit = [string](& git -C $RepoRoot rev-parse --verify 'HEAD^{commit}')
if ($LASTEXITCODE -ne 0 -or $HeadCommit -notmatch '^[0-9a-f]{40}$') { throw 'Could not resolve exact HEAD commit.' }
$LocalTagCommit = [string](& git -C $RepoRoot rev-parse --verify "refs/tags/$TagName^{commit}")
if ($LASTEXITCODE -ne 0 -or $LocalTagCommit -cne $HeadCommit) { throw 'Local release tag must point to exact HEAD.' }
$remoteRefs = @(& git -C $RepoRoot ls-remote "https://github.com/$Repository.git" "refs/tags/$TagName" "refs/tags/$TagName^{}")
if ($LASTEXITCODE -ne 0) { throw 'Could not verify the remote release tag.' }
$tagObjects = @{}
foreach ($line in $remoteRefs) {
    if ($line -match '^([0-9a-f]{40})\s+(.+)$') { $tagObjects[$Matches[2]] = $Matches[1] }
}
$RemoteTagCommit = $tagObjects["refs/tags/$TagName^{}"]
if (-not $RemoteTagCommit) { $RemoteTagCommit = $tagObjects["refs/tags/$TagName"] }
if ($RemoteTagCommit -cne $HeadCommit) { throw 'Remote release tag must dereference to exact HEAD.' }
$shortCommit = $HeadCommit.Substring(0, 12)
$BuiltAtUtc = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")

if ($Manifest.package_version -and [string]$Manifest.package_version -ne $PackageVersion) {
    throw "docs\releases\latest.json package_version '$($Manifest.package_version)' does not match package version '$PackageVersion'."
}

$InstallerDownloadsBadge = "https://img.shields.io/github/downloads/$Repository/$TagName/$ElectronInstallerName`?label=Installer%20downloads&color=2ea44f"
$PortableDownloadsBadge = "https://img.shields.io/github/downloads/$Repository/$TagName/$ElectronUnpackedZipName`?label=Portable%20downloads&color=0969da"
$ApkDownloadsBadge = "https://img.shields.io/github/downloads/$Repository/$TagName/MSBT-Mobile-Controller.apk`?label=Android%20APK%20downloads&color=e8a23a"
$InstallerDownloadUrl = "https://github.com/$Repository/releases/download/$TagName/$ElectronInstallerName"
$PortableDownloadUrl = "https://github.com/$Repository/releases/download/$TagName/$ElectronUnpackedZipName"
$ApkDownloadUrl = "https://github.com/$Repository/releases/download/$TagName/MSBT-Mobile-Controller.apk"

$ReleaseNotesFile = Join-Path $RepoRoot "docs\releases\RELEASE_NOTES_v$PackageVersion.md"
if (Test-Path $ReleaseNotesFile) {
    $notesBody = (Get-Content -Raw $ReleaseNotesFile).TrimEnd()
} else {
    $notesBody = @"
### What's new

See the repository commit history for changes included in this build.

### Download: pick ONE

Download and run:
- $ElectronInstallerName

Or extract the portable ZIP:
- $ElectronUnpackedZipName

**Do not manually download these unless you know why**

- latest.json, latest.yml, *.blockmap

### Upgrade notes

Requires SDK 03 / oak2-mod-manager v0.3:
https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3
"@.TrimEnd()
}

$notes = @"
$notesBody

[![Installer downloads]($InstallerDownloadsBadge)]($InstallerDownloadUrl)
[![Portable downloads]($PortableDownloadsBadge)]($PortableDownloadUrl)
[![Android APK downloads]($ApkDownloadsBadge)]($ApkDownloadUrl)

Counts track the installer, portable ZIP, and Android APK (not update-check files).

### Build information

- Version: $PackageVersion
- Commit: $shortCommit
- Build date: $BuiltAtUtc
"@

$NotesPath = Join-Path ([System.IO.Path]::GetTempPath()) "msbt_release_notes_$TagName.md"
if ($CheckOnly) {
    Write-Host "Release preflight passed for $TagName at $HeadCommit ($($ElectronAssets.Count) assets)."
    $ElectronAssets | ForEach-Object { Write-Host "  $([IO.Path]::GetFileName($_))" }
    Write-Host 'CheckOnly: no files, tags, or GitHub releases were changed.'
    return
}
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
    $assets = @()
    $assets += $ElectronAssets
    & gh release upload $TagName @assets --repo $Repository --clobber
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload assets to existing GitHub Release $TagName."
    }
    $editArgs = @("release", "edit", $TagName, "--repo", $Repository, "--title", $Title, "--notes-file", $NotesPath,
        "--draft=$($Draft.IsPresent.ToString().ToLowerInvariant())", "--prerelease=$($Prerelease.ToString().ToLowerInvariant())")
    if (-not $Prerelease -and -not $Draft) {
        $editArgs += "--latest"
    }
    & gh @editArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to update GitHub Release $TagName metadata."
    }
} else {
    $assets = @()
    $assets += $ElectronAssets
    $ghArgs = @("release", "create", $TagName) + $assets + @("--repo", $Repository, "--title", $Title, "--notes-file", $NotesPath,
        "--verify-tag", "--target", $HeadCommit)
    if ($Draft) {
        $ghArgs += "--draft"
    }
    if ($Prerelease) {
        $ghArgs += "--prerelease"
    } elseif (-not $Draft) {
        $ghArgs += "--latest"
    }
    & gh @ghArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create GitHub Release $TagName."
    }
}

Write-Host "Uploaded release assets (draft=$($Draft.IsPresent)) to GitHub Release:"
Write-Host "https://github.com/$Repository/releases/tag/$TagName"
