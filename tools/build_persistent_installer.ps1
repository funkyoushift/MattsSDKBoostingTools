param([switch]$SkipTests)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$project = Join-Path $repo 'installer\MSBT.Setup.csproj'
$output = Join-Path $repo 'dist_setup'
if (-not $SkipTests) {
    & dotnet run --project (Join-Path $repo 'installer\Tests.csproj') --configuration Release
    if ($LASTEXITCODE -ne 0) { throw 'Persistent installer tests failed.' }
}
& dotnet publish $project --configuration Release --output $output
if ($LASTEXITCODE -ne 0) { throw 'Persistent installer build failed.' }
$exe = Join-Path $output 'MSBT-Setup.exe'
if (-not (Test-Path -LiteralPath $exe)) { throw 'MSBT-Setup.exe was not produced.' }
$destination = Join-Path $repo 'electron_poc\vendor\setup'
New-Item -ItemType Directory -Force -Path $destination | Out-Null
Copy-Item -LiteralPath $exe -Destination (Join-Path $destination 'MSBT-Setup.exe') -Force
Get-FileHash -LiteralPath $exe -Algorithm SHA256
Write-Host "Reusable installer ready: $exe"
