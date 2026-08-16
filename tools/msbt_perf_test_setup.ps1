# MSBT optimization test harness (local smoke testing only -- nothing is published).
#
#   -Action Status    show what is installed + live process/bridge metrics (default)
#   -Action Install   rebuild mod_extracted -> .sdkmod and install into sdk_mods (backs up first)
#   -Action Panel     launch the optimized Electron panel from source (npm start)
#   -Action Revert    restore the most recent pre-optimization .sdkmod backup
#
# The packaged panel in "C:\Program Files\MattsSDKBoostingTools" ships an app.asar,
# so it cannot see the optimized renderer/main code. Use -Action Panel to test those.
[CmdletBinding()]
param(
  [ValidateSet("Status", "Install", "Panel", "Revert")]
  [string]$Action = "Status",
  [string]$SdkModsPath = "C:\Program Files (x86)\Steam\steamapps\common\Borderlands 4\sdk_mods",
  [switch]$Profile
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Target = Join-Path $SdkModsPath "MattsSDKBoostingTools.sdkmod"
$BackupDir = Join-Path $SdkModsPath "_msbt_perf_backup"

function Test-GameRunning {
  return [bool](Get-Process -Name "Borderlands4*" -ErrorAction SilentlyContinue)
}

function Show-Status {
  Write-Host "=== Installed MSBT sdkmod ==="
  if (Test-Path $Target) {
    Get-Item $Target | Select-Object Name, Length, LastWriteTime | Format-List
    $repoBuild = Join-Path $RepoRoot "MattsSDKBoostingTools.sdkmod"
    if (Test-Path $repoBuild) {
      $a = (Get-FileHash $repoBuild).Hash
      $b = (Get-FileHash $Target).Hash
      if ($a -eq $b) {
        Write-Host "Installed build MATCHES current repo build."
      } else {
        Write-Host "Installed build DIFFERS from repo build -- run -Action Install."
      }
    }
  } else {
    Write-Host "Not installed."
  }

  Write-Host ""
  Write-Host "=== Borderlands 4 ==="
  $game = Get-Process -Name "Borderlands4*" -ErrorAction SilentlyContinue
  if ($game) {
    $game | Select-Object Name, Id,
      @{N = "WS_GB"; E = { [math]::Round($_.WorkingSet64 / 1GB, 2) } },
      @{N = "CPU"; E = { [math]::Round($_.CPU, 1) } } | Format-Table -AutoSize
  } else {
    Write-Host "Not running."
  }

  Write-Host "=== Panel / helper processes ==="
  $procs = Get-Process -ErrorAction SilentlyContinue |
    Where-Object { $_.ProcessName -match "MattsSDKBoostingTools|electron|python" }
  if ($procs) {
    $total = [math]::Round((($procs | Measure-Object WorkingSet64 -Sum).Sum) / 1MB, 0)
    $procs | Sort-Object WorkingSet64 -Descending | Select-Object -First 12 Name, Id,
      @{N = "WS_MB"; E = { [math]::Round($_.WorkingSet64 / 1MB, 0) } },
      @{N = "CPU"; E = { [math]::Round($_.CPU, 1) } } | Format-Table -AutoSize
    Write-Host "Panel+helper total: $total MB across $($procs.Count) process(es)"
  } else {
    Write-Host "None running."
  }

  Write-Host ""
  Write-Host "=== Bridge /status ==="
  try {
    $resp = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:49774/status" -TimeoutSec 3
    $json = $resp.Content | ConvertFrom-Json
    [PSCustomObject]@{
      ok            = $json.ok
      started       = $json.started
      queue         = $json.queue
      players       = @($json.players).Count
      serial_active = $json.serial_delivery.active
      payload_bytes = $resp.RawContentLength
    } | Format-List
    Write-Host "Compact JSON check: payload should be noticeably smaller than the old indent=2 output."
  } catch {
    Write-Host "Bridge unreachable (expected unless the game is loaded): $($_.Exception.Message)"
  }

  Write-Host ""
  Write-Host "=== Free memory (the earlier FPS culprit) ==="
  $os = Get-CimInstance Win32_OperatingSystem
  $totalMB = [math]::Round($os.TotalVisibleMemorySize / 1KB, 0)
  $freeMB = [math]::Round($os.FreePhysicalMemory / 1KB, 0)
  Write-Host "Free: $freeMB MB of $totalMB MB  (used $([math]::Round((($totalMB - $freeMB) / $totalMB) * 100, 1))%)"
  if ($freeMB -lt 6000) {
    Write-Host "WARNING: under 6 GB free -- paging will still cost frames regardless of mod code."
  }
}

switch ($Action) {
  "Install" {
    if (Test-GameRunning) {
      Write-Host "WARNING: Borderlands 4 is running. The file will be replaced but only takes effect next launch."
    }
    Write-Host "Building .sdkmod from mod_extracted..."
    & (Join-Path $RepoRoot "tools\build_sdkmod.ps1")
    $src = Join-Path $RepoRoot "MattsSDKBoostingTools.sdkmod"
    New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
    if (Test-Path $Target) {
      $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
      Copy-Item -Force $Target (Join-Path $BackupDir "MattsSDKBoostingTools.pre-perf.$stamp.sdkmod")
      Write-Host "Backed up existing build to _msbt_perf_backup."
    }
    Copy-Item -Force $src $Target
    Write-Host "Installed. Relaunch Borderlands 4 to load it."
    Show-Status
  }
  "Panel" {
    $running = Get-Process -Name "MattsSDKBoostingTools" -ErrorAction SilentlyContinue
    if ($running) {
      Write-Host "NOTE: the packaged panel is running and serves OLD code (app.asar)."
      Write-Host "Close it first so the dev build owns the bridge/gateway ports."
    }
    if ($Profile) {
      $env:MSBT_PERF = "1"
      Write-Host "MSBT_PERF=1 (profiling aggregates enabled for this panel run)"
    }
    Push-Location (Join-Path $RepoRoot "electron_poc")
    try { & npm.cmd start } finally { Pop-Location }
  }
  "Revert" {
    if (-not (Test-Path $BackupDir)) { throw "No backup directory at $BackupDir" }
    $latest = Get-ChildItem $BackupDir -Filter "*.sdkmod" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $latest) { throw "No backup .sdkmod found in $BackupDir" }
    Copy-Item -Force $latest.FullName $Target
    Write-Host "Reverted to $($latest.Name). Relaunch Borderlands 4."
  }
  default { Show-Status }
}
