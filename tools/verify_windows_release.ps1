param([Parameter(Mandatory=$true)][string]$Version)
$ErrorActionPreference = 'Stop'
$installer = Join-Path $PWD "dist_electron/MSBT-Installer-v$Version.exe"
$portable = Join-Path $PWD "dist_electron/MSBT-Portable-v$Version-win-x64.zip"
foreach ($file in @($installer, $portable)) {
    if (-not (Test-Path -LiteralPath $file) -or (Get-Item -LiteralPath $file).Length -eq 0) { throw "Missing artifact: $file" }
}
$destination = Join-Path $env:RUNNER_TEMP 'MSBT-installed'
$process = Start-Process -FilePath $installer -ArgumentList @('/S', "/D=$destination") -PassThru
if (-not $process.WaitForExit(180000)) { $process.Kill(); throw 'Silent installation timed out' }
if ($process.ExitCode -ne 0) { throw "Silent installation failed: $($process.ExitCode)" }
$unpacked = Join-Path $PWD 'dist_electron/win-unpacked'
foreach ($relative in @('MattsSDKBoostingTools.exe', 'resources/app.asar', 'resources/python/python.exe',
    'resources/setup/MSBT-Setup.exe', 'resources/sdkmod/MattsSDKBoostingTools.sdkmod',
    'resources/sdkmods/ActorScriptDeployer/__init__.py', 'resources/oak2/oak2-sdk.zip',
    'resources/afk_shift/pakchunk90-Windows_90_P.pak', 'resources/releases/latest.json')) {
    $installed = Join-Path $destination $relative
    if (-not (Test-Path -LiteralPath $installed)) { throw "Installed payload missing: $relative" }
    $sourceHash = (Get-FileHash -LiteralPath (Join-Path $unpacked $relative) -Algorithm SHA256).Hash
    if ((Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash -cne $sourceHash) { throw "Installed payload differs: $relative" }
}
$python = Join-Path $destination 'resources/python/python.exe'
& $python -c "import yaml; assert yaml.__version__ == '6.0.3'; assert yaml.compose('x: !native []')"
if ($LASTEXITCODE -ne 0) { throw 'Installed Python/YAML check failed' }
$smoke = Start-Process -FilePath (Join-Path $destination 'MattsSDKBoostingTools.exe') -ArgumentList '--smoke' -PassThru -Wait
if ($smoke.ExitCode -ne 0) { throw 'Installed application smoke failed' }
Get-FileHash -LiteralPath $installer, $portable -Algorithm SHA256 | Format-Table -AutoSize
@('### Windows installer verified', "Source: $env:GITHUB_SHA", 'Silent NSIS install, payload hashes, bundled Python/YAML and installed smoke passed. No game tested.') | Add-Content $env:GITHUB_STEP_SUMMARY
