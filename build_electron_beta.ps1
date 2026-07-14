param(
    [switch]$Installer
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ElectronRoot = Join-Path $RepoRoot "electron_poc"
$NodeModules = Join-Path $ElectronRoot "node_modules"
$OutputRoot = Join-Path $RepoRoot "dist_electron"
$ElectronPackageJson = Join-Path $ElectronRoot "package.json"
$ReleaseManifest = Join-Path $RepoRoot "releases\latest.json"
$PrepareElectronPython = Join-Path $RepoRoot "tools\prepare_electron_python.ps1"

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

function Get-ElectronPackageVersion {
    $pkg = Get-Content -Raw $ElectronPackageJson | ConvertFrom-Json
    $version = [string]$pkg.version
    if (-not ($version -match '^\d+\.\d+\.\d+(-(?:alpha|beta)\.\d+)?$')) {
        throw "Electron package version must use public SemVer format, got: $version"
    }
    return $version
}

function Assert-ReleaseManifestVersion {
    param([Parameter(Mandatory=$true)][string]$ExpectedVersion)

    if (-not (Test-Path $ReleaseManifest)) {
        throw "Release manifest not found: $ReleaseManifest. Run .\package_external_beta.ps1 before building Electron so the app bundles the current update manifest."
    }

    $manifest = Get-Content -Raw $ReleaseManifest | ConvertFrom-Json
    $manifestVersion = [string]$manifest.package_version
    if ($manifestVersion -ne $ExpectedVersion) {
        throw "Release manifest package_version '$manifestVersion' does not match Electron version '$ExpectedVersion'. Run .\package_external_beta.ps1 before .\build_electron_beta.ps1 -Installer."
    }
}

if (-not (Test-Path $NodeModules)) {
    throw "Electron dependencies are missing. Run 'npm.cmd install' inside electron_poc first."
}
if (-not (Test-Path $PrepareElectronPython)) {
    throw "Portable Python prep script is missing: $PrepareElectronPython"
}

$ElectronVersion = Get-ElectronPackageVersion
Assert-ReleaseManifestVersion $ElectronVersion

Push-Location $RepoRoot
try {
    & (Join-Path $RepoRoot "build_sdkmod.ps1")
} finally {
    Pop-Location
}

$SdkMod = Join-Path $RepoRoot "MattsSDKBoostingTools.sdkmod"
if (-not (Test-Path $SdkMod)) {
    throw "MattsSDKBoostingTools.sdkmod was not produced by build_sdkmod.ps1."
}

Invoke-Checked "powershell.exe" @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $PrepareElectronPython)

if (Test-Path $OutputRoot) {
    Remove-Item -LiteralPath $OutputRoot -Recurse -Force
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
    $InstallerPath = Join-Path $OutputRoot "MattsSDKBoostingTools-Setup-v$ElectronVersion.exe"
    $LatestYml = Join-Path $OutputRoot "latest.yml"
    if (-not (Test-Path $InstallerPath)) {
        throw "Expected installer was not produced: $InstallerPath"
    }
    if (-not (Test-Path $LatestYml)) {
        throw "Expected Electron update manifest was not produced: $LatestYml"
    }
    $LatestText = Get-Content -Raw $LatestYml
    if ($LatestText -notmatch "(?m)^version:\s*$([regex]::Escape($ElectronVersion))\s*$") {
        throw "latest.yml version does not match package version $ElectronVersion."
    }
}

$PortableRootName = "MattsSDKBoostingTools-Electron-Portable-v$ElectronVersion-win-x64"
$PortableStageRoot = Join-Path $OutputRoot "_portable"
$PortableStageDir = Join-Path $PortableStageRoot $PortableRootName
$PortableZipPath = Join-Path $OutputRoot "$PortableRootName.zip"
$UnpackedRoot = Join-Path $OutputRoot "win-unpacked"
if (-not (Test-Path $UnpackedRoot)) {
    throw "Expected Electron unpacked output was not produced: $UnpackedRoot"
}
Remove-Item -LiteralPath $PortableStageRoot -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $PortableZipPath -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force -Path $PortableStageDir | Out-Null
Copy-Item -Recurse -Force (Join-Path $UnpackedRoot "*") $PortableStageDir
Invoke-Checked "tar.exe" @("-a", "-c", "-f", $PortableZipPath, "-C", $PortableStageRoot, $PortableRootName)
Remove-Item -LiteralPath $PortableStageRoot -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "Electron beta build complete."
Write-Host "Electron version: $ElectronVersion"
Write-Host "Output folder: $OutputRoot"
Write-Host "Portable zip: $PortableZipPath"
