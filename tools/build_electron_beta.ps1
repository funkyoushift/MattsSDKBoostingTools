param(
    [switch]$Installer
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ElectronRoot = Join-Path $RepoRoot "electron_poc"
$NodeModules = Join-Path $ElectronRoot "node_modules"
$OutputRoot = Join-Path $RepoRoot "dist_electron"
$ElectronPackageJson = Join-Path $ElectronRoot "package.json"
$ReleaseManifest = Join-Path $RepoRoot "docs\releases\latest.json"
$PrepareElectronPython = Join-Path $RepoRoot "tools\prepare_electron_python.ps1"
$SourceGzoCatalog = Join-Path $RepoRoot "external_app\v22_parts_codes_fixed\resources\MattsSDKBoostingTools_gzo_codes.json"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,
        [string[]]$ArgumentList = @()
    )

    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $FilePath $($ArgumentList -join ' ')"
    }
}

function Remove-RepoTreeLongPath {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }
    $resolved = [System.IO.Path]::GetFullPath($Path)
    $root = [System.IO.Path]::GetFullPath($RepoRoot)
    if (-not $resolved.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to remove build tree outside repository: $resolved"
    }
    [System.IO.Directory]::Delete("\\?\$resolved", $true)
}

function Get-ElectronSemverVersion {
    $pkg = Get-Content -Raw $ElectronPackageJson | ConvertFrom-Json
    $version = [string]$pkg.version
    if (-not ($version -match '^\d+\.\d+\.\d+(-(?:alpha|beta)\.\d+)?$')) {
        throw "Electron package version must use npm SemVer (MAJOR.MINOR.PATCH), got: $version"
    }
    return $version
}

function Get-PublicReleaseVersion {
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

function Assert-ReleaseManifestVersion {
    param([Parameter(Mandatory=$true)][string]$ExpectedVersion)

    if (-not (Test-Path $ReleaseManifest)) {
        throw "Release manifest not found: $ReleaseManifest. Update docs\releases\latest.json before building Electron so the app bundles the current update manifest."
    }

    $manifest = Get-Content -Raw $ReleaseManifest | ConvertFrom-Json
    $manifestVersion = [string]$manifest.package_version
    if ($manifestVersion -ne $ExpectedVersion) {
        throw "Release manifest package_version '$manifestVersion' does not match Electron version '$ExpectedVersion'. Update docs\releases\latest.json before .\tools\build_electron_beta.ps1 -Installer."
    }
}

function Assert-GzoCatalogImages {
    param(
        [string]$CatalogPath = $SourceGzoCatalog,
        [string]$Label = "Bundled GZO catalog"
    )

    if (-not (Test-Path $CatalogPath)) {
        throw "$Label not found: $CatalogPath"
    }

    $catalog = Get-Content -Raw $CatalogPath | ConvertFrom-Json
    if ($catalog -is [System.Array]) {
        $entries = @($catalog)
    } elseif ($catalog.entries) {
        $entries = @($catalog.entries)
    } elseif ($catalog.codes) {
        $entries = @($catalog.codes)
    } else {
        $entries = @()
    }

    if ($entries.Count -eq 0) {
        throw "$Label has no rows: $CatalogPath"
    }

    $imageFieldNames = @("image_url", "imageUrl", "image", "thumbnail", "screenshot", "screenshot_url", "photo", "picture")
    $imageCount = 0
    foreach ($entry in $entries) {
        foreach ($fieldName in $imageFieldNames) {
            $property = $entry.PSObject.Properties[$fieldName]
            if ($null -ne $property -and -not [string]::IsNullOrWhiteSpace([string]$property.Value)) {
                $imageCount += 1
                break
            }
        }
    }

    if ($imageCount -eq 0) {
        throw "$Label has $($entries.Count) row(s) but no image URLs. Run 'node .\tools\refresh_gzo_release_catalog.js' before packaging a release."
    }

    Write-Host "${Label}: $($entries.Count) row(s), $imageCount image URL row(s)."
}

if (-not (Test-Path $NodeModules)) {
    throw "Electron dependencies are missing. Run 'npm.cmd install' inside electron_poc first."
}
if (-not (Test-Path $PrepareElectronPython)) {
    throw "Portable Python prep script is missing: $PrepareElectronPython"
}

$ElectronSemver = Get-ElectronSemverVersion
$ElectronVersion = Get-PublicReleaseVersion
Assert-ReleaseManifestVersion $ElectronVersion
Assert-GzoCatalogImages -CatalogPath $SourceGzoCatalog -Label "Source GZO catalog"

Push-Location $RepoRoot
try {
    & (Join-Path $RepoRoot "tools\build_sdkmod.ps1")
} finally {
    Pop-Location
}

$SdkMod = Join-Path $RepoRoot "MattsSDKBoostingTools.sdkmod"
if (-not (Test-Path $SdkMod)) {
    throw "MattsSDKBoostingTools.sdkmod was not produced by tools\build_sdkmod.ps1."
}

Invoke-Checked "powershell.exe" @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $PrepareElectronPython)

if (Test-Path $OutputRoot) {
    Remove-RepoTreeLongPath $OutputRoot
}

Push-Location $ElectronRoot
try {
    Invoke-Checked "npm.cmd" @("run", "check")
    if ($Installer) {
        Invoke-Checked "npm.cmd" @("run", "dist:win")
    } else {
        Invoke-Checked "npm.cmd" @("run", "pack")
    }
} finally {
    Pop-Location
}

if ($Installer) {
    $BuiltInstallerPath = Join-Path $OutputRoot "MSBT-Installer-v$ElectronSemver.exe"
    $InstallerPath = Join-Path $OutputRoot "MSBT-Installer-v$ElectronVersion.exe"
    $LatestYml = Join-Path $OutputRoot "latest.yml"
    if (-not (Test-Path $BuiltInstallerPath)) {
        throw "Expected installer was not produced: $BuiltInstallerPath"
    }
    if ($BuiltInstallerPath -ne $InstallerPath) {
        if (Test-Path $InstallerPath) {
            Remove-Item -LiteralPath $InstallerPath -Force
        }
        Rename-Item -LiteralPath $BuiltInstallerPath -NewName (Split-Path -Leaf $InstallerPath)
        $builtBlockMap = "$BuiltInstallerPath.blockmap"
        $releaseBlockMap = "$InstallerPath.blockmap"
        if (Test-Path $builtBlockMap) {
            if (Test-Path $releaseBlockMap) {
                Remove-Item -LiteralPath $releaseBlockMap -Force
            }
            Rename-Item -LiteralPath $builtBlockMap -NewName (Split-Path -Leaf $releaseBlockMap)
        }
    }
    if (-not (Test-Path $InstallerPath)) {
        throw "Expected installer was not produced: $InstallerPath"
    }
    if (-not (Test-Path $LatestYml)) {
        throw "Expected Electron update manifest was not produced: $LatestYml"
    }
    $LatestText = Get-Content -Raw $LatestYml
    if ($LatestText -notmatch "(?m)^version:\s*$([regex]::Escape($ElectronSemver))\s*$") {
        throw "latest.yml version does not match npm package version $ElectronSemver."
    }
}

$PortableRootName = "MSBT-Portable-v$ElectronVersion-win-x64"
$PortableStageRoot = Join-Path $OutputRoot "_portable"
$PortableStageDir = Join-Path $PortableStageRoot $PortableRootName
$PortableZipPath = Join-Path $OutputRoot "$PortableRootName.zip"
$UnpackedRoot = Join-Path $OutputRoot "win-unpacked"
if (-not (Test-Path $UnpackedRoot)) {
    throw "Expected Electron unpacked output was not produced: $UnpackedRoot"
}
$RequiredPackageFiles = @(
    "resources\python\python.exe",
    "resources\sdkmod\MattsSDKBoostingTools.sdkmod",
    "resources\sdkmods\ActorScriptDeployer\__init__.py",
    "resources\releases\latest.json",
    "resources\external_app\v22_parts_codes_fixed\resources\ui_layout.json",
    "resources\external_app\v22_parts_codes_fixed\resources\MattsSDKBoostingTools_gzo_codes.json"
)
foreach ($relativePath in $RequiredPackageFiles) {
    $fullPath = Join-Path $UnpackedRoot $relativePath
    if (-not (Test-Path $fullPath)) {
        throw "Electron package is missing required runtime file: $relativePath"
    }
}
$PackagedGzoCatalog = Join-Path $UnpackedRoot "resources\external_app\v22_parts_codes_fixed\resources\MattsSDKBoostingTools_gzo_codes.json"
Assert-GzoCatalogImages -CatalogPath $PackagedGzoCatalog -Label "Packaged GZO catalog"
Remove-Item -LiteralPath $PortableStageRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $PortableZipPath -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $PortableStageRoot | Out-Null
try {
    # Avoid duplicating the deeply nested editor resources into another long
    # staging path. Windows Copy-Item can exceed MAX_PATH here; tar can safely
    # follow a short junction while preserving the desired portable root name.
    New-Item -ItemType Junction -Path $PortableStageDir -Target $UnpackedRoot | Out-Null
    Invoke-Checked "tar.exe" @("-h", "-a", "-c", "-f", $PortableZipPath, "-C", $PortableStageRoot, $PortableRootName)
} finally {
    if ([System.IO.Directory]::Exists($PortableStageDir)) {
        [System.IO.Directory]::Delete($PortableStageDir, $false)
    }
    if ([System.IO.Directory]::Exists($PortableStageRoot)) {
        [System.IO.Directory]::Delete($PortableStageRoot, $false)
    }
}

Write-Host "Electron build complete."
Write-Host "Electron semver: $ElectronSemver"
Write-Host "Public release version: $ElectronVersion"
Write-Host "Output folder: $OutputRoot"
Write-Host "Portable zip: $PortableZipPath"
