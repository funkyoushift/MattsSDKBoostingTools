param(
    [switch]$Installer
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ElectronRoot = Join-Path $RepoRoot "electron_poc"
$NodeModules = Join-Path $ElectronRoot "node_modules"
$OutputRoot = Join-Path $RepoRoot "dist_electron"
$ElectronPackageJson = Join-Path $ElectronRoot "package.json"

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

if (-not (Test-Path $NodeModules)) {
    throw "Electron dependencies are missing. Run 'npm.cmd install' inside electron_poc first."
}

$ElectronVersion = Get-ElectronPackageVersion

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

Write-Host "Electron beta build complete."
Write-Host "Electron version: $ElectronVersion"
Write-Host "Output folder: $OutputRoot"
