param([string]$GameRoot, [string]$OutputFile = (Join-Path $PSScriptRoot 'Epic-card-check.json'))
$ErrorActionPreference = 'Stop'
$expectedExe = '764a4bb5403a2619a0be627de5a738e23ea021e8672f7f0e7a536697d4a06719'
$expectedRevision = 'native-card-profiles-20261008'
# Read-only inspection. Never installs files, launches the game, or requests a card.
if (-not $GameRoot) {
    $manifestDir = Join-Path $env:ProgramData 'Epic/EpicGamesLauncher/Data/Manifests'
    $matches = @(Get-ChildItem -LiteralPath $manifestDir -Filter '*.item' | ForEach-Object {
        $manifest = Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json
        if ($manifest.DisplayName -match 'Borderlands.*4' -and $manifest.InstallLocation) { $manifest }
    })
    if ($matches.Count -ne 1) { throw 'Could not select one Epic installation. Run with -GameRoot and its installation folder.' }
    $GameRoot = $matches[0].InstallLocation
}
$exe = Join-Path $GameRoot 'OakGame/Binaries/Win64/Borderlands4.exe'
$sdk = Join-Path $GameRoot 'sdk_mods/MattsSDKBoostingTools.sdkmod'
$exeHash = (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
$sdkHash = if (Test-Path -LiteralPath $sdk) { (Get-FileHash -LiteralPath $sdk -Algorithm SHA256).Hash.ToLowerInvariant() } else { $null }
$bundled = Join-Path $PSScriptRoot 'MattsSDKBoostingTools.sdkmod'
$candidateHash = if (Test-Path -LiteralPath $bundled) { (Get-FileHash -LiteralPath $bundled -Algorithm SHA256).Hash.ToLowerInvariant() } else { $null }
$revision = $null
$buildCount = $null
$buildProfile = $null
$bridgeError = $null
try {
    $body = @{ action='native_card_preview_status'; payload=@{}; timeout=5 } | ConvertTo-Json -Compress
    $status = Invoke-RestMethod -Uri 'http://127.0.0.1:49774/action' -Method Post -ContentType 'application/json' -Body $body -TimeoutSec 8
    $revision = $status.profile_revision
    $buildCount = $status.builds
    $buildProfile = $status.build_profile
} catch { $bridgeError = 'No readable running card service; start MSBT and the game to check the loaded revision.' }
$result = [ordered]@{
    executable_sha256 = $exeHash
    analyzed_epic_build_matches = ($exeHash -eq $expectedExe)
    installed_sdk_sha256 = $sdkHash
    packaged_sdk_sha256 = $candidateHash
    installed_candidate_matches = [bool]($sdkHash -and $candidateHash -and $sdkHash -eq $candidateHash)
    running_card_revision = $revision
    running_card_revision_matches = ($revision -eq $expectedRevision)
    native_cards_built_this_session = $buildCount
    running_card_build_profile = $buildProfile
    epic_native_card_completed = ($buildProfile -eq 'epic-4845623' -and $buildCount -gt 0)
    bridge_note = $bridgeError
    live_card_render_tested = $false
}
$result | ConvertTo-Json | Set-Content -LiteralPath $OutputFile -Encoding UTF8
$result | ConvertTo-Json
Write-Host "Saved $OutputFile"
