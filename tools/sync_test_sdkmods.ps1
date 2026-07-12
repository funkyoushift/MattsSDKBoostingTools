[CmdletBinding()]
param(
    [string]$SdkModsPath = "C:\Program Files (x86)\Steam\steamapps\common\Borderlands 4\sdk_mods",
    [switch]$BuildSdkMod,
    [switch]$InstallComparisonMods,
    [bool]$ArchiveDevLeftovers = $true,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$ArchiveName = Get-Date -Format "yyyyMMdd_HHmmss"

$script:CopiedItems = New-Object System.Collections.Generic.List[string]
$script:SkippedItems = New-Object System.Collections.Generic.List[string]
$script:ArchivedItems = New-Object System.Collections.Generic.List[string]
$script:PreservedItems = New-Object System.Collections.Generic.List[string]
$script:EnabledItems = New-Object System.Collections.Generic.List[string]
$script:Warnings = New-Object System.Collections.Generic.List[string]

function FullPath {
    param([string]$Path)
    return [System.IO.Path]::GetFullPath($Path)
}

function Normalize-RelativePath {
    param([string]$Path)
    return ($Path -replace '/', '\').TrimStart('\').ToLowerInvariant()
}

function Get-RelativePathCompat {
    param(
        [string]$Root,
        [string]$Path
    )
    $resolvedRootNoSlash = (FullPath $Root).TrimEnd('\')
    $resolvedRoot = $resolvedRootNoSlash + '\'
    $resolvedPath = FullPath $Path
    if ([string]::Equals($resolvedPath.TrimEnd('\'), $resolvedRootNoSlash, [System.StringComparison]::OrdinalIgnoreCase)) {
        return "."
    }
    if (-not $resolvedPath.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is not under root: $resolvedPath"
    }
    return $resolvedPath.Substring($resolvedRoot.Length)
}

function Assert-UnderPath {
    param(
        [string]$Path,
        [string]$Root,
        [string]$Label
    )
    $resolvedPath = FullPath $Path
    $resolvedRootNoSlash = (FullPath $Root).TrimEnd('\')
    $resolvedRoot = $resolvedRootNoSlash + '\'
    if ([string]::Equals($resolvedPath.TrimEnd('\'), $resolvedRootNoSlash, [System.StringComparison]::OrdinalIgnoreCase)) {
        return
    }
    if (-not $resolvedPath.StartsWith($resolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to operate outside ${Label}: $resolvedPath"
    }
}

function Write-Step {
    param([string]$Message)
    if ($DryRun) {
        Write-Host "[dry-run] $Message"
    } else {
        Write-Host $Message
    }
}

function Add-Warning {
    param([string]$Message)
    $script:Warnings.Add($Message) | Out-Null
    Write-Host "WARNING: $Message"
}

function Ensure-Directory {
    param([string]$Path)
    Assert-UnderPath $Path $SdkModsPath "sdk_mods"
    if ($DryRun) {
        Write-Step "ensure directory $Path"
        return
    }
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Get-FileHashString {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Test-SameFile {
    param(
        [string]$Source,
        [string]$Destination
    )
    if (-not (Test-Path -LiteralPath $Source) -or -not (Test-Path -LiteralPath $Destination)) {
        return $false
    }
    $sourceItem = Get-Item -LiteralPath $Source
    $destinationItem = Get-Item -LiteralPath $Destination
    if ($sourceItem.Length -ne $destinationItem.Length) {
        return $false
    }
    return (Get-FileHashString $Source) -eq (Get-FileHashString $Destination)
}

function New-ExcludeMap {
    param([string[]]$RelativeFiles)
    $map = @{}
    foreach ($relative in $RelativeFiles) {
        if ([string]::IsNullOrWhiteSpace($relative)) {
            continue
        }
        $map[(Normalize-RelativePath $relative)] = $true
    }
    return $map
}

function Get-DirectoryFingerprint {
    param(
        [string]$Path,
        [string[]]$ExcludeRelativeFiles = @()
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        return ""
    }

    $exclude = New-ExcludeMap $ExcludeRelativeFiles
    $items = New-Object System.Collections.Generic.List[string]
    foreach ($file in (Get-ChildItem -LiteralPath $Path -Recurse -Force -File)) {
        $relative = Get-RelativePathCompat $Path $file.FullName
        $normalized = Normalize-RelativePath $relative
        if ($normalized -like "*\__pycache__\*" -or $file.Extension -in ".pyc", ".pyo") {
            continue
        }
        if ($exclude.ContainsKey($normalized)) {
            continue
        }
        $hash = Get-FileHashString $file.FullName
        $items.Add("$normalized|$($file.Length)|$hash") | Out-Null
    }

    $sorted = $items | Sort-Object
    return ($sorted -join "`n")
}

function Archive-ExistingPath {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    Assert-UnderPath $Path $SdkModsPath "sdk_mods"
    $relative = Get-RelativePathCompat $SdkModsPath $Path

    $archiveRoot = Join-Path $SdkModsPath "_msbt_test_archive\$ArchiveName"
    $destination = Join-Path $archiveRoot $relative
    $destinationParent = Split-Path -Parent $destination

    if ($DryRun) {
        Write-Step "archive $Path -> $destination"
        return
    }

    New-Item -ItemType Directory -Force -Path $destinationParent | Out-Null
    Move-Item -Force -LiteralPath $Path -Destination $destination
    $script:ArchivedItems.Add($relative) | Out-Null
}

function Save-PreservedFiles {
    param(
        [string]$Destination,
        [string[]]$RelativeFiles
    )
    $saved = New-Object System.Collections.Generic.List[object]
    if (-not (Test-Path -LiteralPath $Destination)) {
        return $saved
    }

    $preserveRoot = Join-Path $RepoRoot "build\sync_sdkmods\preserve\$ArchiveName"
    Assert-UnderPath $preserveRoot $RepoRoot "repo"

    foreach ($relative in $RelativeFiles) {
        if ([string]::IsNullOrWhiteSpace($relative)) {
            continue
        }
        $source = Join-Path $Destination $relative
        if (-not (Test-Path -LiteralPath $source)) {
            continue
        }
        $target = Join-Path $preserveRoot (Join-Path (Split-Path -Leaf $Destination) $relative)
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
        Copy-Item -Force -LiteralPath $source -Destination $target
        $saved.Add([pscustomobject]@{
            Relative = $relative
            TempPath = $target
        }) | Out-Null
        $script:PreservedItems.Add("$Destination\$relative") | Out-Null
    }

    return $saved
}

function Restore-PreservedFiles {
    param(
        [string]$Destination,
        [System.Collections.Generic.List[object]]$SavedFiles
    )
    foreach ($saved in $SavedFiles) {
        $target = Join-Path $Destination $saved.Relative
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
        Copy-Item -Force -LiteralPath $saved.TempPath -Destination $target
    }
}

function Copy-FileToSdkMods {
    param(
        [string]$Source,
        [string]$RelativeDestination
    )
    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Source file not found: $Source"
    }
    $destination = Join-Path $SdkModsPath $RelativeDestination
    Assert-UnderPath $destination $SdkModsPath "sdk_mods"

    if (Test-SameFile $Source $destination) {
        Write-Step "unchanged file $RelativeDestination"
        $script:SkippedItems.Add($RelativeDestination) | Out-Null
        return
    }

    Archive-ExistingPath $destination
    if ($DryRun) {
        Write-Step "copy file $Source -> $destination"
        return
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
    Copy-Item -Force -LiteralPath $Source -Destination $destination
    $script:CopiedItems.Add($RelativeDestination) | Out-Null
}

function Copy-DirectoryToSdkMods {
    param(
        [string]$Source,
        [string]$RelativeDestination,
        [string[]]$PreserveRelativeFiles = @()
    )
    $destination = Join-Path $SdkModsPath $RelativeDestination
    Assert-UnderPath $destination $SdkModsPath "sdk_mods"

    if ($DryRun) {
        Write-Step "copy directory $Source -> $destination"
        if ($PreserveRelativeFiles.Count -gt 0) {
            Write-Step "preserve relative files in $RelativeDestination`: $($PreserveRelativeFiles -join ', ')"
        }
        return
    }

    if (-not (Test-Path -LiteralPath $Source)) {
        throw "Source directory not found: $Source"
    }

    $sourceFingerprint = Get-DirectoryFingerprint $Source $PreserveRelativeFiles
    $destinationFingerprint = Get-DirectoryFingerprint $destination $PreserveRelativeFiles
    if ((Test-Path -LiteralPath $destination) -and $sourceFingerprint -eq $destinationFingerprint) {
        Write-Step "unchanged directory $RelativeDestination"
        $script:SkippedItems.Add($RelativeDestination) | Out-Null
        return
    }

    $saved = Save-PreservedFiles $destination $PreserveRelativeFiles
    Archive-ExistingPath $destination

    New-Item -ItemType Directory -Force -Path $destination | Out-Null
    & robocopy $Source $destination /E /COPY:DAT /DCOPY:DAT /R:2 /W:1 /NFL /NDL /NP | Out-Host
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy failed with exit code $LASTEXITCODE while copying $Source"
    }
    Get-ChildItem -LiteralPath $Source -Force -File | ForEach-Object {
        Copy-Item -Force -LiteralPath $_.FullName -Destination (Join-Path $destination $_.Name)
    }
    Get-ChildItem -Recurse -Directory -LiteralPath $destination -Filter "__pycache__" -ErrorAction SilentlyContinue |
        Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -File -LiteralPath $destination -ErrorAction SilentlyContinue |
        Where-Object { $_.Extension -in ".pyc", ".pyo" } |
        Remove-Item -Force -ErrorAction SilentlyContinue

    Restore-PreservedFiles $destination $saved
    $script:CopiedItems.Add($RelativeDestination) | Out-Null
}

function Write-Launcher {
    param(
        [string]$RelativeDestination,
        [string[]]$Lines
    )
    $destination = Join-Path $SdkModsPath $RelativeDestination
    Assert-UnderPath $destination $SdkModsPath "sdk_mods"

    $content = ($Lines -join [Environment]::NewLine) + [Environment]::NewLine
    if ((Test-Path -LiteralPath $destination) -and ((Get-Content -Raw -LiteralPath $destination) -eq $content)) {
        Write-Step "unchanged launcher $RelativeDestination"
        $script:SkippedItems.Add($RelativeDestination) | Out-Null
        return
    }

    Archive-ExistingPath $destination
    if ($DryRun) {
        Write-Step "write launcher $destination"
        return
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
    Set-Content -LiteralPath $destination -Value $Lines -Encoding ASCII
    $script:CopiedItems.Add($RelativeDestination) | Out-Null
}

function Expand-ZipToWorkTemp {
    param([string]$ZipPath)
    if (-not (Test-Path -LiteralPath $ZipPath)) {
        throw "Zip not found: $ZipPath"
    }
    $tempRoot = Join-Path $RepoRoot "build\sync_sdkmods"
    Assert-UnderPath $tempRoot $RepoRoot "repo"
    if (-not $DryRun) {
        New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
    }
    $name = [System.IO.Path]::GetFileNameWithoutExtension($ZipPath) -replace '[^\w.-]', '_'
    $destination = Join-Path $tempRoot $name
    if ($DryRun) {
        Write-Step "expand $ZipPath -> $destination"
        return $destination
    }
    Remove-Item -Recurse -Force -LiteralPath $destination -ErrorAction SilentlyContinue
    Expand-Archive -LiteralPath $ZipPath -DestinationPath $destination -Force
    return $destination
}

function Ensure-ModEnabledSetting {
    param(
        [string]$SettingsFile,
        [string]$DisplayName
    )
    $settingsDir = Join-Path $SdkModsPath "settings"
    Ensure-Directory $settingsDir
    $path = Join-Path $settingsDir $SettingsFile
    Assert-UnderPath $path $SdkModsPath "sdk_mods"

    if ($DryRun) {
        Write-Step "ensure $DisplayName is enabled via settings\$SettingsFile"
        return
    }

    $settings = $null
    if (Test-Path -LiteralPath $path) {
        try {
            $settings = Get-Content -Raw -LiteralPath $path | ConvertFrom-Json
        } catch {
            Add-Warning "Could not parse settings\$SettingsFile; archiving malformed settings before rewriting."
            Archive-ExistingPath $path
        }
    }

    if ($null -eq $settings) {
        $settings = [pscustomobject]@{}
    }

    $enabledProperty = $settings.PSObject.Properties["enabled"]
    if ($enabledProperty) {
        if ($enabledProperty.Value -eq $true) {
            Write-Step "$DisplayName already enabled"
            $script:SkippedItems.Add("settings\$SettingsFile") | Out-Null
            return
        }
        $enabledProperty.Value = $true
    } else {
        $settings | Add-Member -NotePropertyName "enabled" -NotePropertyValue $true
    }

    $settings | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $path -Encoding UTF8
    Write-Step "enabled $DisplayName via settings\$SettingsFile"
    $script:EnabledItems.Add($DisplayName) | Out-Null
}

function Install-ActorScriptDeployer {
    $zip = "C:\Users\mwenn\Desktop\ActorScriptDeployer.zip"
    if (-not (Test-Path -LiteralPath $zip)) {
        Add-Warning "ActorScriptDeployer.zip not found; keeping existing install if present."
        return
    }
    $temp = Expand-ZipToWorkTemp $zip
    $source = Join-Path $temp "ActorScriptDeployer"
    Copy-DirectoryToSdkMods $source "ActorScriptDeployer"
    Ensure-ModEnabledSetting "ActorScriptDeployer.json" "ActorScriptDeployer"
}

function Install-SdkDebugMenu {
    $sources = @(
        "C:\Users\mwenn\Downloads\SDK_Debug_Menu_v35_menu_only (1).zip",
        "C:\Users\mwenn\Downloads\SDK_Debug_Menu_v35_menu_only.zip",
        "C:\Users\mwenn\Downloads\SDK_Debug_Menu.sdkmod",
        "C:\Users\mwenn\Desktop\SDK_Debug_Menu.sdkmod"
    )
    $availableSources = @($sources | Where-Object { Test-Path -LiteralPath $_ })
    $source = $availableSources | Select-Object -First 1
    if (-not $source) {
        Add-Warning "SDK Debug Menu source not found; skipping."
        return
    }

    if ($availableSources.Count -gt 1) {
        $hashes = @{}
        foreach ($candidate in $availableSources) {
            if (Test-Path -LiteralPath $candidate -PathType Leaf) {
                $hashes[(Get-FileHashString $candidate)] = $true
            }
        }
        if ($hashes.Keys.Count -eq 1) {
            Write-Step "Multiple SDK_Debug_Menu sources found with identical hash; using $source"
        } else {
            Add-Warning "Multiple SDK_Debug_Menu sources found with different hashes; using first source: $source"
        }
    }

    if ($source.EndsWith(".zip", [System.StringComparison]::OrdinalIgnoreCase)) {
        $temp = Expand-ZipToWorkTemp $source
        $folder = Join-Path $temp "sdk_mods\SDK_Debug_Menu"
        if (-not $DryRun -and -not (Test-Path -LiteralPath $folder)) {
            throw "SDK Debug Menu folder not found in $source"
        }
        Copy-DirectoryToSdkMods $folder "SDK_Debug_Menu" @("data\favorites.json")
    } else {
        Copy-FileToSdkMods $source "SDK_Debug_Menu.sdkmod"
    }
    Ensure-ModEnabledSetting "SDK_Debug_Menu.json" "SDK_Debug_Menu"
}

function Install-Blimgui {
    $folderSource = "C:\Users\mwenn\Desktop\blimgui"
    if (Test-Path -LiteralPath $folderSource) {
        Copy-DirectoryToSdkMods $folderSource "blimgui"
        if (Test-Path -LiteralPath (Join-Path $SdkModsPath "blimgui.zip")) {
            Write-Step "Leaving existing blimgui.zip untouched; SDK 03 importable install is sdk_mods\blimgui."
        }
        return
    }

    $zipSource = "C:\Users\mwenn\Desktop\blimgui.zip"
    if (Test-Path -LiteralPath $zipSource) {
        Add-Warning "Only blimgui.zip source was found. Folder install is preferred for SDK 03."
        Copy-FileToSdkMods $zipSource "blimgui.zip"
        return
    }

    Add-Warning "No BLImGui source found; SDK_Debug_Menu may fail to import."
}

function Test-InstalledPath {
    param(
        [string]$RelativePath,
        [string]$Label
    )
    $path = Join-Path $SdkModsPath $RelativePath
    if (Test-Path -LiteralPath $path) {
        Write-Host "[ok] $Label`: $RelativePath"
        return $true
    }
    Write-Host "[missing] $Label`: $RelativePath"
    $script:Warnings.Add("Missing $Label at $RelativePath") | Out-Null
    return $false
}

$SdkModsPath = FullPath $SdkModsPath
if (-not (Test-Path -LiteralPath $SdkModsPath)) {
    throw "sdk_mods folder not found: $SdkModsPath"
}

Write-Host "Repo: $RepoRoot"
Write-Host "sdk_mods: $SdkModsPath"
Write-Host "Archive bucket: _msbt_test_archive\$ArchiveName"

if ($BuildSdkMod) {
    $builder = Join-Path $RepoRoot "build_sdkmod.ps1"
    if (-not (Test-Path -LiteralPath $builder)) {
        throw "build_sdkmod.ps1 not found: $builder"
    }
    if ($DryRun) {
        Write-Step "build current MattsSDKBoostingTools.sdkmod"
    } else {
        & $builder
    }
}

$sdkmodSource = Join-Path $RepoRoot "MattsSDKBoostingTools.sdkmod"
if (-not (Test-Path -LiteralPath $sdkmodSource)) {
    $sdkmodSource = Join-Path $RepoRoot "MSBT_External_Beta\MattsSDKBoostingTools.sdkmod"
}
Copy-FileToSdkMods $sdkmodSource "MattsSDKBoostingTools.sdkmod"
Ensure-ModEnabledSetting "MattsSDKBoostingTools.json" "MattsSDKBoostingTools"

$externalSource = Join-Path $RepoRoot "MSBT_External_Beta\MattsSDKBoostingTools_external"
if (-not (Test-Path -LiteralPath $externalSource)) {
    throw "Packaged external app folder not found: $externalSource"
}
Copy-DirectoryToSdkMods $externalSource "MattsSDKBoostingTools_external" @(
    "resources\user_serial_bookmarks.json",
    "resources\custom_bl4_codes.json"
)

$tkLauncher = @(
    "@echo off",
    "setlocal",
    "set ""APP_DIR=%~dp0MattsSDKBoostingTools_external""",
    "if exist ""%APP_DIR%\MattsBoostingToolsExternal.exe"" start ""Matts SDK Boosting Tools"" ""%APP_DIR%\MattsBoostingToolsExternal.exe"" & exit /b 0",
    "if exist ""%APP_DIR%\matts_external_app_v22.pyw"" start ""Matts SDK Boosting Tools"" ""%APP_DIR%\matts_external_app_v22.pyw"" & exit /b 0",
    "if exist ""%APP_DIR%\matts_external_app_v22.py"" start ""Matts SDK Boosting Tools"" pythonw ""%APP_DIR%\matts_external_app_v22.py"" & exit /b 0",
    "echo Matts Boosting Tools external app was not found.",
    "pause",
    "exit /b 1"
)
Write-Launcher "Launch_MSBT_External_App.bat" $tkLauncher
Write-Launcher "Launch_MSBT_Tkinter_App.bat" $tkLauncher

$electronDir = Join-Path $RepoRoot "electron_poc"
$electronLauncher = @(
    "@echo off",
    "setlocal",
    "cd /d ""$electronDir""",
    "if not exist ""package.json"" echo Electron POC folder not found. & pause & exit /b 1",
    "call npm.cmd start",
    "exit /b %ERRORLEVEL%"
)
Write-Launcher "Launch_MSBT_Electron_POC.bat" $electronLauncher

if ($InstallComparisonMods) {
    Install-Blimgui
    Install-ActorScriptDeployer
    Install-SdkDebugMenu
}

if ($ArchiveDevLeftovers) {
    $leftovers = @(
        "node_modules",
        "package.json",
        "package-lock.json",
        "lootlemon_add_missing_items.js",
        "lootlemon_bl4_scraper.js",
        "lootlemon_bl4_added_missing.json",
        "lootlemon_bl4_missing_urls.json",
        "lootlemon_bl4_new_entries_partial.json",
        "standalone.zip"
    )
    foreach ($item in $leftovers) {
        Archive-ExistingPath (Join-Path $SdkModsPath $item)
    }
}

Write-Host ""
Write-Host "Post-sync checks:"
Test-InstalledPath "MattsSDKBoostingTools.sdkmod" "MSBT SDK mod" | Out-Null
Test-InstalledPath "MattsSDKBoostingTools_external\MattsBoostingToolsExternal.exe" "Tkinter packaged app" | Out-Null
Test-InstalledPath "Launch_MSBT_External_App.bat" "Tkinter launcher" | Out-Null
Test-InstalledPath "Launch_MSBT_Electron_POC.bat" "Electron launcher" | Out-Null
Test-InstalledPath "settings\MattsSDKBoostingTools.json" "MSBT enabled setting" | Out-Null

if ($InstallComparisonMods) {
    Test-InstalledPath "blimgui\__init__.py" "BLImGui importable folder" | Out-Null
    Test-InstalledPath "blimgui\pyproject.toml" "BLImGui metadata" | Out-Null
    Test-InstalledPath "ActorScriptDeployer\pyproject.toml" "ActorScriptDeployer folder install" | Out-Null
    Test-InstalledPath "ActorScriptDeployer\__init__.py" "ActorScriptDeployer code" | Out-Null
    Test-InstalledPath "settings\ActorScriptDeployer.json" "ActorScriptDeployer enabled setting" | Out-Null
    Test-InstalledPath "SDK_Debug_Menu\pyproject.toml" "SDK_Debug_Menu folder install" | Out-Null
    Test-InstalledPath "SDK_Debug_Menu\__init__.py" "SDK_Debug_Menu code" | Out-Null
    Test-InstalledPath "SDK_Debug_Menu\data\sdk_debug_commands.json" "SDK_Debug_Menu command data" | Out-Null
    Test-InstalledPath "settings\SDK_Debug_Menu.json" "SDK_Debug_Menu enabled setting" | Out-Null
}

Write-Host ""
Write-Host "Sync complete."
Write-Host "Launchers available in sdk_mods:"
Write-Host "  Launch_MSBT_External_App.bat"
Write-Host "  Launch_MSBT_Tkinter_App.bat"
Write-Host "  Launch_MSBT_Electron_POC.bat"
if ($InstallComparisonMods) {
    Write-Host "Comparison installs checked: blimgui folder, ActorScriptDeployer, SDK_Debug_Menu"
}

Write-Host ""
Write-Host "Summary:"
Write-Host "  Copied/updated: $($script:CopiedItems.Count)"
Write-Host "  Skipped unchanged: $($script:SkippedItems.Count)"
Write-Host "  Archived replaced paths: $($script:ArchivedItems.Count)"
Write-Host "  Preserved user files: $($script:PreservedItems.Count)"
Write-Host "  Enabled settings updated: $($script:EnabledItems.Count)"
Write-Host "  Warnings: $($script:Warnings.Count)"

if ($script:Warnings.Count -gt 0) {
    Write-Host ""
    Write-Host "Warnings:"
    $script:Warnings | ForEach-Object { Write-Host "  - $_" }
}
