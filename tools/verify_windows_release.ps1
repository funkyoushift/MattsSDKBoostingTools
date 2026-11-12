param([Parameter(Mandatory=$true)][string]$Version)
$ErrorActionPreference = 'Stop'
$installer = Join-Path $PWD "dist_electron/MSBT-Installer-v$Version.exe"
$portable = Join-Path $PWD "dist_electron/MSBT-Portable-v$Version-win-x64.zip"
foreach ($file in @($installer, $portable)) {
    if (-not (Test-Path -LiteralPath $file) -or (Get-Item -LiteralPath $file).Length -eq 0) { throw "Missing artifact: $file" }
}
$destination = Join-Path $env:RUNNER_TEMP 'MSBT-installed'
$process = Start-Process -FilePath $installer -ArgumentList @('/S', "/D=$destination") -PassThru -WindowStyle Hidden
if (-not $process.WaitForExit(180000)) { $process.Kill(); throw 'Silent installation timed out' }
if ($process.ExitCode -ne 0) { throw "Silent installation failed: $($process.ExitCode)" }
$unpacked = Join-Path $PWD 'dist_electron/win-unpacked'
$payloadFiles = @(Get-ChildItem -LiteralPath $unpacked -Recurse -File)
if ($payloadFiles.Count -eq 0) { throw 'Unpacked payload is empty' }
foreach ($payloadFile in $payloadFiles) {
    $relative = [IO.Path]::GetRelativePath($unpacked, $payloadFile.FullName)
    $installed = Join-Path $destination $relative
    if (-not (Test-Path -LiteralPath $installed)) { throw "Installed payload missing: $relative" }
    $sourceHash = (Get-FileHash -LiteralPath (Join-Path $unpacked $relative) -Algorithm SHA256).Hash
    if ((Get-FileHash -LiteralPath $installed -Algorithm SHA256).Hash -cne $sourceHash) { throw "Installed payload differs: $relative" }
}
$python = Join-Path $destination 'resources/python/python.exe'
& $python -c "import yaml; assert yaml.__version__ == '6.0.3'; assert yaml.compose('x: !native []')"
if ($LASTEXITCODE -ne 0) { throw 'Installed Python/YAML check failed' }
$smoke = Start-Process -FilePath (Join-Path $destination 'MattsSDKBoostingTools.exe') -ArgumentList '--smoke' -PassThru -WindowStyle Hidden
if (-not $smoke.WaitForExit(120000)) { $smoke.Kill(); throw 'Installed application smoke timed out' }
if ($smoke.ExitCode -ne 0) { throw 'Installed application smoke failed' }
$priorAsar = $env:MSBT_UPDATER_ASAR
try {
    $env:MSBT_UPDATER_ASAR = Join-Path $destination 'resources/app.asar'
    node electron_poc/test_platform_updater_electron_asar.js
    if ($LASTEXITCODE -ne 0) { throw 'Installed updater ASAR regression failed' }
} finally { $env:MSBT_UPDATER_ASAR = $priorAsar }
$env:MSBT_GATE_VERSION = $Version
@'
import json, os, sys, zipfile, hashlib
from pathlib import Path
sys.path.insert(0, str(Path('tools').resolve()))
from release_gate import create_platform_receipt
version = os.environ['MSBT_GATE_VERSION']
root = Path.cwd()
unpacked = root / 'dist_electron/win-unpacked'
portable = root / f'dist_electron/MSBT-Portable-v{version}-win-x64.zip'
prefix = f'MSBT-Portable-v{version}-win-x64/'
files = {p.relative_to(unpacked).as_posix(): p for p in unpacked.rglob('*') if p.is_file()}
with zipfile.ZipFile(portable) as archive:
    entries = [n for n in archive.namelist() if not n.endswith('/')]
    assert len(entries) == len(set(entries)), 'Duplicate ZIP entries'
    assert set(entries) == {prefix + p for p in files}, 'Portable inventory differs'
    for relative, path in files.items():
        assert hashlib.sha256(archive.read(prefix + relative)).digest() == hashlib.sha256(path.read_bytes()).digest(), relative
checks = [{'name': name, 'ok': True} for name in
          ('installed_payload', 'portable_payload', 'bundled_python', 'installed_smoke', 'updater')]
receipt = create_platform_receipt(root, 'win32', version, checks,
    [root / f'dist_electron/MSBT-Installer-v{version}.exe', portable],
    {'kind': 'not_tested', 'detail': 'CI has no BL4 installation; no live game qualification.'})
(root / 'dist_electron/windows-verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
'@ | python -
if ($LASTEXITCODE -ne 0) { throw 'Windows artifact receipt validation failed' }
Get-FileHash -LiteralPath $installer, $portable -Algorithm SHA256 | Format-Table -AutoSize
@('### Windows installer verified', "Source: $env:GITHUB_SHA", 'Silent NSIS install, payload hashes, bundled Python/YAML and installed smoke passed. No game tested.') | Add-Content $env:GITHUB_STEP_SUMMARY
