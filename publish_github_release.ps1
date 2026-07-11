param(
    [string]$Repository = "funkyoushift/MattsSDKBoostingTools",
    [string]$TagName = "",
    [string]$Title = "",
    [switch]$Draft
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ZipPath = Join-Path $RepoRoot "MSBT_External_Beta.zip"
$ManifestPath = Join-Path $RepoRoot "releases\latest.json"

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Text
    )
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI 'gh' was not found. Install it and run 'gh auth login', then rerun this script."
}

if (-not (Test-Path $ZipPath)) {
    throw "Beta ZIP not found: $ZipPath. Run .\build_external_exe.ps1 and .\package_external_beta.ps1 first."
}

$shortCommit = ""
try {
    $shortCommit = (& git -C $RepoRoot rev-parse --short HEAD).Trim()
} catch {
    $shortCommit = [DateTime]::UtcNow.ToString("yyyyMMddHHmm")
}

$packageVersion = if ($shortCommit) { "beta-$shortCommit" } else { "beta" }
if (Test-Path $ManifestPath) {
    try {
        $manifest = Get-Content -Raw $ManifestPath | ConvertFrom-Json
        if ($manifest.package_version) {
            $packageVersion = [string]$manifest.package_version
        }
    } catch {
        Write-Warning "Could not read releases\latest.json; using commit-based release name."
    }
}

if (-not $TagName) {
    $TagName = $packageVersion
}
if (-not $Title) {
    $Title = "MSBT External Beta $packageVersion"
}

$notes = @"
Matt's SDK Boosting Tools external beta package.

Requires SDK 03 / oak2-mod-manager v0.3:
https://github.com/bl-sdk/oak2-mod-manager/releases/tag/v0.3

Download MSBT_External_Beta.zip from this release, extract it, then copy the SDK mod and external app folder into your Borderlands 4 sdk_mods folder.
"@

$NotesPath = Join-Path ([System.IO.Path]::GetTempPath()) "msbt_release_notes_$TagName.md"
Write-Utf8NoBom $NotesPath $notes

$releaseExists = $false
& gh release view $TagName --repo $Repository *> $null
if ($LASTEXITCODE -eq 0) {
    $releaseExists = $true
}

if ($releaseExists) {
    & gh release upload $TagName $ZipPath --repo $Repository --clobber
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload ZIP to existing GitHub Release $TagName."
    }
    & gh release edit $TagName --repo $Repository --title $Title --notes-file $NotesPath --latest
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to update GitHub Release $TagName metadata."
    }
} else {
    $ghArgs = @("release", "create", $TagName, $ZipPath, "--repo", $Repository, "--title", $Title, "--notes-file", $NotesPath, "--latest")
    if ($Draft) {
        $ghArgs += "--draft"
    }
    & gh @ghArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create GitHub Release $TagName."
    }
}

Write-Host "Published beta ZIP to GitHub Release:"
Write-Host "https://github.com/$Repository/releases/tag/$TagName"
