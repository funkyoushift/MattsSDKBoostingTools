param([switch]$Restore)
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$testFolder = Join-Path $taskRoot 'output/afk-lobby'
$manifest = Get-Content -LiteralPath (Join-Path $testFolder 'manifest.json') -Raw | ConvertFrom-Json
if (Get-Process -Name Borderlands4 -ErrorAction SilentlyContinue) {
    throw 'Close Borderlands 4 before installing the AFK test. This installer will not close the game.'
}
foreach ($file in $manifest.files) {
    $currentHash = (Get-FileHash -LiteralPath $file.source -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($currentHash -notin @($file.original_sha256, $file.test_sha256, $file.previous_test_sha256)) {
        throw "Installed file changed since the test was built: $($file.source)"
    }
    $replacement = if ($Restore) { Join-Path $testFolder ('originals/' + [IO.Path]::GetFileName($file.source)) } else { $file.built }
    $expected = if ($Restore) { $file.original_sha256 } else { $file.test_sha256 }
    if ((Get-FileHash -LiteralPath $replacement -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
        throw "Test or backup hash mismatch: $replacement"
    }
}
foreach ($file in $manifest.files) {
    $replacement = if ($Restore) { Join-Path $testFolder ('originals/' + [IO.Path]::GetFileName($file.source)) } else { $file.built }
    Copy-Item -LiteralPath $replacement -Destination $file.source -Force
    $expected = if ($Restore) { $file.original_sha256 } else { $file.test_sha256 }
    if ((Get-FileHash -LiteralPath $file.source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
        throw "Installed hash mismatch: $($file.source)"
    }
}
$message = if ($Restore) { 'Original SDK and SHiFT PAK restored.' } else { 'AFK test installed. Launch Borderlands 4, host a lobby, open SHiFT, then use Boosting > AFK Lobby in the test panel.' }
Write-Host $message
$message | Set-Content -LiteralPath (Join-Path $testFolder 'installation.txt')
