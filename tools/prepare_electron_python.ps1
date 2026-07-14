param(
    [string]$PythonVersion = "3.13.14",
    [string]$Architecture = "amd64"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$VendorRoot = Join-Path $RepoRoot "electron_poc\vendor"
$PythonDir = Join-Path $VendorRoot "python"
$PythonExe = Join-Path $PythonDir "python.exe"
$ZipName = "python-$PythonVersion-embed-$Architecture.zip"
$AlternateZipName = "python-$PythonVersion-embeddable-$Architecture.zip"
$ZipPath = Join-Path $VendorRoot $ZipName
$AlternateZipPath = Join-Path $VendorRoot $AlternateZipName
$DownloadUrl = "https://www.python.org/ftp/python/$PythonVersion/$ZipName"
$ExtractDir = Join-Path $VendorRoot "_python_extract"

function Get-PythonVersionText {
    param([string]$ExePath)
    if (-not (Test-Path $ExePath)) {
        return ""
    }
    try {
        return (& $ExePath --version 2>&1 | Out-String).Trim()
    } catch {
        return ""
    }
}

function Update-EmbeddedPythonPath {
    $PathFile = Get-ChildItem -LiteralPath $PythonDir -Filter "python*._pth" | Select-Object -First 1
    if (-not $PathFile) {
        throw "Could not find embedded Python ._pth file in $PythonDir"
    }

    $ExternalAppRelativePaths = @(
        # Packaged app layout: resources\python -> resources\external_app
        "..\external_app\v22_parts_codes_fixed",
        # Source/dev layout: electron_poc\vendor\python -> external_app
        "..\..\..\external_app\v22_parts_codes_fixed"
    )
    $ObsoleteExternalAppRelativePaths = @(
        "..\..\external_app\v22_parts_codes_fixed"
    )
    $Lines = @(Get-Content -LiteralPath $PathFile.FullName)
    $OriginalLineCount = $Lines.Count
    $Lines = @($Lines | Where-Object { $ObsoleteExternalAppRelativePaths -notcontains $_ })
    $MissingExternalAppPaths = @($ExternalAppRelativePaths | Where-Object { $Lines -notcontains $_ })
    if ($MissingExternalAppPaths.Count -gt 0) {
        $ImportSiteIndex = [array]::IndexOf($Lines, "#import site")
        if ($ImportSiteIndex -ge 0) {
            $Before = @()
            if ($ImportSiteIndex -gt 0) {
                $Before = $Lines[0..($ImportSiteIndex - 1)]
            }
            $After = $Lines[$ImportSiteIndex..($Lines.Count - 1)]
            $Lines = @($Before + $MissingExternalAppPaths + $After)
        } else {
            $Lines = @($Lines + $MissingExternalAppPaths)
        }
    }
    if ($MissingExternalAppPaths.Count -gt 0 -or $Lines.Count -ne $OriginalLineCount) {
        Set-Content -LiteralPath $PathFile.FullName -Value $Lines -Encoding ASCII
    }
}

New-Item -ItemType Directory -Force -Path $VendorRoot | Out-Null

$ExistingVersion = Get-PythonVersionText $PythonExe
if ($ExistingVersion -like "Python $PythonVersion*") {
    Update-EmbeddedPythonPath
    Write-Host "Portable Python already prepared: $ExistingVersion"
    Write-Host "Path: $PythonExe"
    exit 0
}

if (Test-Path $PythonDir) {
    Remove-Item -LiteralPath $PythonDir -Recurse -Force
}
if (Test-Path $ExtractDir) {
    Remove-Item -LiteralPath $ExtractDir -Recurse -Force
}

if (-not (Test-Path $ZipPath) -and (Test-Path $AlternateZipPath)) {
    $ZipPath = $AlternateZipPath
}

if (-not (Test-Path $ZipPath)) {
    Write-Host "Downloading portable Python $PythonVersion from python.org..."
    try {
        Invoke-WebRequest -Uri $DownloadUrl -OutFile $ZipPath
    } catch {
        throw "Could not download portable Python from $DownloadUrl. Download it manually and place it at $ZipPath, then run this script again. Original error: $($_.Exception.Message)"
    }
}

New-Item -ItemType Directory -Force -Path $ExtractDir | Out-Null
Expand-Archive -LiteralPath $ZipPath -DestinationPath $ExtractDir -Force
Move-Item -LiteralPath $ExtractDir -Destination $PythonDir

Update-EmbeddedPythonPath

$PreparedVersion = Get-PythonVersionText $PythonExe
if (-not ($PreparedVersion -like "Python $PythonVersion*")) {
    throw "Portable Python was extracted but did not report the expected version. Reported: $PreparedVersion"
}

& $PythonExe -c "import json, sys; print('portable python ok', sys.version.split()[0])"
if ($LASTEXITCODE -ne 0) {
    throw "Portable Python smoke test failed."
}

Write-Host "Portable Python prepared: $PreparedVersion"
Write-Host "Path: $PythonExe"
