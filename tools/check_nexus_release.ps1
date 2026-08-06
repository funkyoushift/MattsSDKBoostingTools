param(
    [string]$GameDomain = "borderlands4",
    [int]$ModId = 276,
    [string]$ManifestPath = ".\docs\releases\latest.json"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ResolvedManifestPath = Join-Path $RepoRoot $ManifestPath

if (-not (Test-Path $ResolvedManifestPath)) {
    throw "Release manifest not found: $ResolvedManifestPath"
}

$ApiKey = [Environment]::GetEnvironmentVariable("NEXUSMODS_API_KEY", "Process")
if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    $ApiKey = [Environment]::GetEnvironmentVariable("NEXUSMODS_API_KEY", "User")
}
if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    throw "NEXUSMODS_API_KEY is not set. Create a Nexus Mods API key, then set it with: [Environment]::SetEnvironmentVariable('NEXUSMODS_API_KEY','paste-key-here','User')"
}

$Manifest = Get-Content -Raw $ResolvedManifestPath | ConvertFrom-Json
$ExpectedVersion = [string]$Manifest.package_version
$ExpectedInstaller = [string]$Manifest.electron_installer_name
$ExpectedPortableUrl = [string]$Manifest.manual_zip_download_url
$NexusModUrl = [string]$Manifest.nexus_mod_url
if ([string]::IsNullOrWhiteSpace($NexusModUrl)) {
    $NexusModUrl = "https://www.nexusmods.com/$GameDomain/mods/$ModId"
}
$NexusFilesUrl = [string]$Manifest.nexus_files_url
if ([string]::IsNullOrWhiteSpace($NexusFilesUrl)) {
    $NexusFilesUrl = "https://www.nexusmods.com/$GameDomain/mods/$ModId?tab=files"
}

$Headers = @{
    apikey = $ApiKey
    "Application-Name" = "MattsSDKBoostingTools"
    "Application-Version" = $ExpectedVersion
    "Application-Slug" = "matts-sdk-boosting-tools"
}

$Base = "https://api.nexusmods.com/v3"

function Invoke-NexusGet {
    param([Parameter(Mandatory=$true)][string]$Path)
    $uri = "$Base$Path"
    Invoke-RestMethod -Method Get -Uri $uri -Headers $Headers
}

Write-Host "Checking Nexus mod metadata..."
$Mod = Invoke-NexusGet "/games/$GameDomain/mods/$ModId"
$ModData = $Mod.data
if (-not $ModData) {
    $ModData = $Mod
}
Write-Host "Nexus mod: $($ModData.name) ($NexusModUrl)"

Write-Host "Checking Nexus file list..."
$FilesResponse = Invoke-NexusGet "/mods/$ModId/files"
$Files = @()
if ($FilesResponse.data -and $FilesResponse.data.files) {
    $Files = @($FilesResponse.data.files)
} elseif ($FilesResponse.data -is [System.Array]) {
    $Files = @($FilesResponse.data)
} elseif ($FilesResponse.files) {
    $Files = @($FilesResponse.files)
} elseif ($FilesResponse -is [System.Array]) {
    $Files = @($FilesResponse)
}

if ($Files.Count -eq 0) {
    Write-Warning "No files were returned by the Nexus API. Check the Nexus files page manually: $NexusFilesUrl"
    exit 0
}

$Rows = foreach ($file in $Files) {
    $latestVersion = $file.version
    if ($file.latest_version) {
        $latestVersion = $file.latest_version.version
    } elseif ($file.versions -and $file.versions.Count -gt 0) {
        $latestVersion = @($file.versions)[0].version
    }

    [PSCustomObject]@{
        FileId = $file.id
        GameScopedId = $file.game_scoped_id
        Name = $file.name
        Version = $latestVersion
        Category = $file.file_category
    }
}

$Rows | Select-Object -First 20 | Format-Table -AutoSize

$matchesVersion = @($Files | Where-Object {
    $latestVersion = [string]$_.version
    if ($_.latest_version) {
        $latestVersion = [string]$_.latest_version.version
    } elseif ($_.versions -and $_.versions.Count -gt 0) {
        $latestVersion = [string]@($_.versions)[0].version
    }

    ($latestVersion -eq $ExpectedVersion) -or
    ([string]$_.name -like "*$ExpectedVersion*")
})

Write-Host ""
Write-Host "GitHub manifest version: $ExpectedVersion"
Write-Host "Expected installer asset: $ExpectedInstaller"
Write-Host "Expected portable ZIP URL: $ExpectedPortableUrl"
Write-Host "Nexus files page: $NexusFilesUrl"

if ($matchesVersion.Count -gt 0) {
    Write-Host "Nexus appears to have $($matchesVersion.Count) file(s) matching version $ExpectedVersion." -ForegroundColor Green
} else {
    Write-Warning "Nexus does not appear to have a file matching version $ExpectedVersion yet. Run the GitHub 'Sync Nexus from GitHub Release' workflow or upload the staged files manually, then rerun this check."
}
