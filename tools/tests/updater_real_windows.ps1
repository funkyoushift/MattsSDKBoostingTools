param([string]$ReceiptDirectory = (Join-Path $env:RUNNER_TEMP 'msbt real upgrade receipts'))
$ErrorActionPreference = 'Stop'
if ($env:GITHUB_ACTIONS -ne 'true' -or !$env:RUNNER_TEMP -or $env:RUNNER_OS -ne 'Windows') { throw 'This installer test runs only on a disposable GitHub Windows runner.' }
$root = Join-Path $env:RUNNER_TEMP ('MSBT real upgrade ' + [Guid]::NewGuid().ToString('N'))
$install = Join-Path $root 'Installation with spaces'
New-Item -ItemType Directory -Path $root,$ReceiptDirectory -Force | Out-Null
$receipt = [ordered]@{ source='2.41.1'; target='2.41.2'; started=(Get-Date).ToUniversalTime().ToString('o'); install=$install; ok=$false; limitation='Disposable desktop fixture. No live BL4, Proton, guest saves, or production data proof.' }
$helper = Join-Path $PSScriptRoot 'updater_cdp.js'
$exe = Join-Path $install 'MattsSDKBoostingTools.exe'
function Launch-Probe([string]$mode,[int]$port) {
  $process = Start-Process -FilePath $exe -ArgumentList @('--remote-debugging-address=127.0.0.1',"--remote-debugging-port=$port") -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $ReceiptDirectory "$mode-$port-stdout.log") -RedirectStandardError (Join-Path $ReceiptDirectory "$mode-$port-stderr.log")
  & node $helper $port $mode (Join-Path $ReceiptDirectory "$mode-$port.json")
  if ($LASTEXITCODE -ne 0) { throw "Released renderer $mode probe failed; see receipt." }
  return $process
}
function Close-Owned {
  Get-Process MattsSDKBoostingTools -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $exe } | ForEach-Object { if ($_.MainWindowHandle -ne 0) { [void]$_.CloseMainWindow() } }
  for($i=0;$i -lt 30;$i++) { if (!(Get-Process MattsSDKBoostingTools -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $exe })) { return }; Start-Sleep -Seconds 1 }
  throw 'Owned app did not close normally; no unrelated processes were terminated.'
}
function Capture-HandoffDiagnostics([string]$label) {
  $diagnostic=[ordered]@{at=(Get-Date).ToUniversalTime().ToString('o');label=$label}
  try {
    $diagnostic.processes=@(Get-CimInstance Win32_Process | Where-Object {
      $_.ExecutablePath -eq $exe -or
      ($_.CommandLine -and ($_.CommandLine.Contains($root) -or
      ($receipt.userData -and $_.CommandLine.Contains($receipt.userData))))
    } | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine,CreationDate)
  } catch {$diagnostic.processError=$_.Exception.Message}
  try {
    # Same native query used by the unmodified production game-running guard.
    $diagnostic.gameGuardOutput=(& tasklist.exe /FI 'IMAGENAME eq Borderlands4.exe' /FO CSV /NH 2>&1 | Out-String)
    $diagnostic.gameGuardExit=$LASTEXITCODE
  } catch {$diagnostic.gameGuardError=$_.Exception.Message}
  if($receipt.userData){
    $diagnostic.files=@()
    foreach($sub in @('update-handoff-*','updates')) {
      Get-ChildItem -Path (Join-Path $receipt.userData $sub) -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object {
        $item=[ordered]@{path=$_.FullName;size=$_.Length;written=$_.LastWriteTimeUtc.ToString('o')}
        if($_.Extension -in @('.ps1','.txt','.log')){$item.text=Get-Content -LiteralPath $_.FullName -Raw -ErrorAction SilentlyContinue}
        if($_.Extension -eq '.exe'){$item.sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}
        $diagnostic.files+= $item
      }
    }
  }
  $diagnostic | ConvertTo-Json -Depth 12 | Set-Content (Join-Path $ReceiptDirectory "handoff-diagnostics-$label.json")
  try { & node $helper 19412 diagnose (Join-Path $ReceiptDirectory "handoff-renderer-$label.json") }
  catch { Write-Warning "Bounded renderer diagnostic unavailable: $_" }
  # A vanished renderer is expected during successful quit. Preserve the receipt
  # without converting diagnostic unavailability into an upgrade verdict.
  $global:LASTEXITCODE=0
}
try {
  $release = Invoke-RestMethod 'https://api.github.com/repos/funkyoushift/MattsSDKBoostingTools/releases/tags/v2.41.1'
  $asset = @($release.assets | Where-Object name -eq 'MSBT-Installer-v2.41.1.exe')
  if($asset.Count -ne 1 -or $asset[0].digest -notmatch '^sha256:[a-f0-9]{64}$') { throw 'Missing authoritative installer digest.' }
  $url='https://github.com/funkyoushift/MattsSDKBoostingTools/releases/download/v2.41.1/MSBT-Installer-v2.41.1.exe'
  if($asset[0].browser_download_url -ne $url) { throw 'Unexpected installer URL.' }
  $installer=Join-Path $root 'released installer.exe'
  Write-Host 'Downloading published old Windows installer'
  Invoke-WebRequest $url -OutFile $installer
  $hash=(Get-FileHash -LiteralPath $installer -Algorithm SHA256).Hash.ToLowerInvariant()
  if(('sha256:'+$hash) -ne $asset[0].digest -or (Get-Item $installer).Length -ne $asset[0].size) { throw 'Published installer hash/size mismatch.' }
  $receipt.installer=@{url=$url;sha256=$hash;size=$asset[0].size}
  $initial=Start-Process -FilePath $installer -ArgumentList "/S /D=$install" -WindowStyle Hidden -PassThru
  if(!$initial.WaitForExit(180000)){throw 'Initial released installer exceeded 180 seconds; no process was force-terminated.'}
  $receipt.initialInstallerExit=$initial.ExitCode
  if($initial.ExitCode -ne 0) { throw 'Initial released installer failed.' }
  [void](Launch-Probe 'seed' 19411)
  Close-Owned
  $seed=Get-Content (Join-Path $ReceiptDirectory 'seed-19411.json') -Raw | ConvertFrom-Json
  if(($seed.stages | Where-Object name -eq 'version').result.appVersion -ne '2.41.1'){throw 'Initial released app version is not 2.41.1.'}
  $data=($seed.stages | Where-Object name -eq 'userData').result.path
  if(!$data) { throw 'Released IPC did not identify userData.' }
  $receipt.userData=$data
  $sentinel=Join-Path $data 'updater-preservation-sentinel.txt'
  Set-Content -LiteralPath $sentinel -Value 'harmless persistent upgrade sentinel' -NoNewline
  $mock=Join-Path $root 'outside app mock save and protected list.txt'
  Set-Content -LiteralPath $mock -Value 'Not live game data. Must remain unchanged.' -NoNewline
  $tracked=@($sentinel,(Join-Path $data 'serial_bookmarks.json'),$mock)
  $before=@{};foreach($file in $tracked){$before[$file]=(Get-FileHash -LiteralPath $file).Hash}
  $receipt.before=$before
  $asar=Join-Path $install 'resources/app.asar'
  $oldHash=(Get-FileHash -LiteralPath $asar).Hash
  [void](Launch-Probe 'update' 19412)
  Capture-HandoffDiagnostics 'requested'
  # The production helper waits for app exit and performs actual RunAs elevation.
  # Do not alter its payload or replace it with a probe installer.
  for($i=0;$i -lt 180;$i++){Start-Sleep -Seconds 1;if($i -eq 9){Capture-HandoffDiagnostics 'after-10-seconds'};if((Get-FileHash -LiteralPath $asar -ErrorAction SilentlyContinue).Hash -ne $oldHash){break}}
  if((Get-FileHash -LiteralPath $asar).Hash -eq $oldHash){Capture-HandoffDiagnostics 'unchanged-asar';throw 'Actual handoff did not replace same-directory ASAR within 180s (inspect handoff diagnostics and renderer IPC result).'}
  $restarted=$false
  for($i=0;$i -lt 90;$i++) {
    $owned=@(Get-Process MattsSDKBoostingTools -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $exe -and $_.MainWindowHandle -ne 0 })
    if($owned.Count){$receipt.helperRestartPids=@($owned.Id);$restarted=$true;break}
    Start-Sleep -Seconds 1
  }
  if(!$restarted){throw 'Installer changed ASAR but actual production helper did not relaunch a main window in the same directory.'}
  Close-Owned
  foreach($port in @(19413,19414)) {
    [void](Launch-Probe 'verify' $port)
    Close-Owned
    $probe=Get-Content (Join-Path $ReceiptDirectory "verify-$port.json") -Raw | ConvertFrom-Json
    $version=($probe.stages | Where-Object name -eq 'version').result
    if($version.appVersion -ne '2.41.2'){throw ('Restart version mismatch: '+($version|ConvertTo-Json -Depth 8))}
    foreach($file in $tracked){if((Get-FileHash -LiteralPath $file).Hash -ne $before[$file]){throw "Preservation mismatch: $file"}}
  }
  $receipt.afterAsarSha256=(Get-FileHash -LiteralPath $asar).Hash
  $receipt.ok=$true
} catch { $receipt.error=$_.Exception.ToString(); throw }
finally {
  if($receipt.userData){Get-ChildItem -LiteralPath $receipt.userData -Filter 'install-error.txt' -Recurse -ErrorAction SilentlyContinue | ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $ReceiptDirectory ('handoff-'+$_.Directory.Name+'.txt')) }}
  $receipt.finished=(Get-Date).ToUniversalTime().ToString('o')
  $receipt | ConvertTo-Json -Depth 14 | Set-Content (Join-Path $ReceiptDirectory 'result.json')
  try { Close-Owned } catch { Write-Warning $_ }
}
