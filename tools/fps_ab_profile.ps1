<#
FPS A/B profile switcher for the Borderlands 4 sdk_mods folder.

Why this exists: the mod loader (sdk_mods\__main__.py) imports EVERY directory and
every *.sdkmod in sdk_mods. It only skips entries whose name starts with ".".
An "_disabled_" prefix does nothing. This script flips mods off the way the loader
actually understands, and records what it changed so Restore is exact.

  Baseline        SDK core only (mods_base + console_mod_menu + keybinds). No MSBT.
  MsbtOnly        SDK core + MSBT + blimgui. How Matt normally plays.
  MsbtNoBlimgui   SDK core + MSBT, blimgui off. Isolates the duplicate
                  blimgui_panel Infinite Jump hooks.
  Restore         Undo everything this script disabled.
  Status          Show what currently loads.

Usage (PowerShell, game closed):
  powershell -NoProfile -ExecutionPolicy Bypass -File tools\fps_ab_profile.ps1 -Profile Status
  powershell -NoProfile -ExecutionPolicy Bypass -File tools\fps_ab_profile.ps1 -Profile Baseline
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [ValidateSet('Baseline', 'MsbtOnly', 'MsbtNoBlimgui', 'Restore', 'Status')]
  [string]$Profile,

  [string]$SdkMods = 'C:\Program Files (x86)\Steam\steamapps\common\Borderlands 4\sdk_mods'
)

$ErrorActionPreference = 'Stop'

$OffDirPrefix  = '.abtest_'
$OffFileSuffix = '.abtest_off'
$StateFile     = Join-Path $SdkMods '.abtest_state.json'

# Never touch these - the SDK cannot start without them, and the rest are data.
$CoreDirs  = @('keybinds', 'settings')
$CoreFiles = @('mods_base.sdkmod', 'console_mod_menu.sdkmod')

if (-not (Test-Path -LiteralPath $SdkMods)) { throw "sdk_mods not found: $SdkMods" }

$game = Get-Process -Name 'Borderlands4' -ErrorAction SilentlyContinue
if ($game -and $Profile -ne 'Status') {
  Write-Warning 'Borderlands 4 is RUNNING. Changes only apply on the next launch; close the game first to be safe.'
}

function Get-Disabled {
  $dirs = Get-ChildItem -LiteralPath $SdkMods -Force -Directory |
            Where-Object { $_.Name.StartsWith($OffDirPrefix) }
  $files = Get-ChildItem -LiteralPath $SdkMods -Force -File |
            Where-Object { $_.Name.EndsWith($OffFileSuffix) }
  return @{ Dirs = $dirs; Files = $files }
}

function Show-Status {
  Write-Host ''
  Write-Host "sdk_mods: $SdkMods"
  Write-Host ''
  Write-Host '--- LOADS AT STARTUP ---' -ForegroundColor Green
  Get-ChildItem -LiteralPath $SdkMods -Force |
    Where-Object {
      -not $_.Name.StartsWith('.') -and
      -not $_.Name.EndsWith($OffFileSuffix) -and
      ($_.PSIsContainer -or $_.Extension -eq '.sdkmod')
    } |
    ForEach-Object { '  {0}' -f $_.Name } | Sort-Object

  Write-Host ''
  Write-Host '--- SKIPPED ---' -ForegroundColor DarkGray
  Get-ChildItem -LiteralPath $SdkMods -Force |
    Where-Object {
      ($_.Name.StartsWith('.') -or $_.Name.EndsWith($OffFileSuffix)) -and
      $_.Name -ne '.abtest_state.json'
    } |
    ForEach-Object { '  {0}' -f $_.Name } | Sort-Object
  Write-Host ''
}

function Restore-All {
  $state = Get-Disabled
  $n = 0
  foreach ($d in $state.Dirs) {
    $orig = $d.Name.Substring($OffDirPrefix.Length)
    Rename-Item -LiteralPath $d.FullName -NewName $orig -Force
    Write-Host "  re-enabled dir  $orig"; $n++
  }
  foreach ($f in $state.Files) {
    $orig = $f.Name.Substring(0, $f.Name.Length - $OffFileSuffix.Length)
    Rename-Item -LiteralPath $f.FullName -NewName $orig -Force
    Write-Host "  re-enabled file $orig"; $n++
  }
  Remove-Item -LiteralPath $StateFile -Force -ErrorAction SilentlyContinue
  Write-Host "Restored $n item(s)." -ForegroundColor Green
}

function Disable-AllExcept {
  param([string[]]$KeepDirs, [string[]]$KeepFiles)

  $keepD = @($CoreDirs + $KeepDirs)
  $keepF = @($CoreFiles + $KeepFiles)
  $n = 0

  foreach ($d in (Get-ChildItem -LiteralPath $SdkMods -Force -Directory)) {
    if ($d.Name.StartsWith('.')) { continue }          # already skipped by loader
    if ($keepD -contains $d.Name) { continue }
    Rename-Item -LiteralPath $d.FullName -NewName ($OffDirPrefix + $d.Name) -Force
    Write-Host "  disabled dir  $($d.Name)"; $n++
  }

  foreach ($f in (Get-ChildItem -LiteralPath $SdkMods -Force -File -Filter '*.sdkmod')) {
    if ($keepF -contains $f.Name) { continue }
    Rename-Item -LiteralPath $f.FullName -NewName ($f.Name + $OffFileSuffix) -Force
    Write-Host "  disabled file $($f.Name)"; $n++
  }

  @{ profile = $Profile; at = (Get-Date).ToString('o'); disabled = $n } |
    ConvertTo-Json | Set-Content -LiteralPath $StateFile -Encoding UTF8
  Write-Host "Disabled $n item(s) for profile '$Profile'." -ForegroundColor Yellow
}

switch ($Profile) {
  'Status' { Show-Status; return }

  'Restore' {
    Write-Host 'Restoring every mod this script disabled...'
    Restore-All; Show-Status; return
  }

  'Baseline' {
    Write-Host 'Profile Baseline - SDK core only, no MSBT.'
    Restore-All
    Disable-AllExcept -KeepDirs @() -KeepFiles @()
    Show-Status; return
  }

  'MsbtOnly' {
    Write-Host 'Profile MsbtOnly - SDK core + MSBT + blimgui.'
    Restore-All
    Disable-AllExcept -KeepDirs @('blimgui') -KeepFiles @('MattsSDKBoostingTools.sdkmod')
    Show-Status; return
  }

  'MsbtNoBlimgui' {
    Write-Host 'Profile MsbtNoBlimgui - SDK core + MSBT, blimgui off.'
    Restore-All
    Disable-AllExcept -KeepDirs @() -KeepFiles @('MattsSDKBoostingTools.sdkmod')
    Show-Status; return
  }
}
