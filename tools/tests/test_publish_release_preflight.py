"""Publisher checks use synthetic artifacts and mocked Git/GitHub commands only."""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMMIT = "a" * 40
OTHER = "b" * 40


@pytest.fixture
def release_fixture(tmp_path):
    shell = shutil.which("pwsh") or shutil.which("powershell")
    yaml_module = ROOT / "electron_poc/node_modules/js-yaml"
    if not shell or not shutil.which("node") or not yaml_module.is_dir():
        pytest.skip("PowerShell, Node and Electron dependencies are required")

    def write(relative, content):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content if isinstance(content, bytes) else content.encode())
        return path

    write("tools/publish_github_release.ps1", (ROOT / "tools/publish_github_release.ps1").read_bytes())
    write("electron_poc/package.json", json.dumps({"version": "2.11.0"}))
    shutil.copytree(yaml_module, tmp_path / "electron_poc/node_modules/js-yaml")
    sdk = b"test SDK archive bytes"
    installer = b"test installer bytes"
    manifest = json.dumps({"package_version": "2.11.0", "sdkmod_version": "2.11.0", "mobile_apk_version": "1.1.0"})
    write("MattsSDKBoostingTools.sdkmod", sdk)
    write("dist_electron/win-unpacked/resources/sdkmod/MattsSDKBoostingTools.sdkmod", sdk)
    write("dist_electron/win-unpacked/resources/releases/latest.json", manifest)
    app_update = "provider: github\nowner: funkyoushift\nrepo: MattsSDKBoostingTools\n"
    write("dist_electron/win-unpacked/resources/app-update.yml", app_update)
    write("docs/releases/latest.json", manifest + "\n")
    write("dist_electron/MSBT-Installer-v2.11.0.exe", installer)
    sha512 = base64.b64encode(hashlib.sha512(installer).digest()).decode()
    updater = {"version": "2.11.0", "path": "MSBT-Installer-v2.11.0.exe", "sha512": sha512,
               "files": [{"url": "MSBT-Installer-v2.11.0.exe", "sha512": sha512, "size": len(installer)}]}
    write("dist_electron/latest.yml", json.dumps(updater))
    portable = tmp_path / "dist_electron/MSBT-Portable-v2.11.0-win-x64.zip"
    with zipfile.ZipFile(portable, "w") as archive:
        prefix = "MSBT-Portable-v2.11.0-win-x64/resources/"
        archive.writestr(prefix + "sdkmod/MattsSDKBoostingTools.sdkmod", sdk)
        archive.writestr(prefix + "releases/latest.json", manifest)
        archive.writestr(prefix + "app-update.yml", app_update)
    write("dist_mobile/MSBT-Mobile-Controller.apk", b"apk")
    write("dist_mobile/MSBT-Mobile-Controller-1.1.0.apk", b"apk")
    write("docs/releases/mobile-version.json", json.dumps({"versionName": "1.1.0", "versionCode": 24,
          "apkUrl": "https://example.test/MSBT-Mobile-Controller.apk",
          "apkVersionedUrl": "https://example.test/MSBT-Mobile-Controller-1.1.0.apk"}))
    driver = write("driver.ps1", r'''
function global:git {
    $global:LASTEXITCODE = 0
    if ($args -contains 'ls-remote') {
        # An annotated tag must be compared through its peeled commit, not its object id.
        Write-Output ('cccccccccccccccccccccccccccccccccccccccc' + "`trefs/tags/v2.11.0")
        Write-Output ($env:TEST_REMOTE_SHA + "`trefs/tags/v2.11.0^{}")
    } elseif ($args[-1] -like 'refs/tags/*') { Write-Output $env:TEST_LOCAL_SHA }
    else { Write-Output $env:TEST_HEAD_SHA }
}
function global:gh {
    Add-Content -LiteralPath $env:TEST_GH_LOG -Value (ConvertTo-Json -InputObject @($args) -Compress)
    $global:LASTEXITCODE = 0
    if ($args[1] -eq 'view' -and $env:TEST_EXISTING_RELEASE -ne '1') { $global:LASTEXITCODE = 1 }
}
if ((Get-Command gh).CommandType -ne 'Function' -or (Get-Command git).CommandType -ne 'Function') { throw 'Mocks missing' }
$options = @{}
if ($env:TEST_CHECK_ONLY -eq '1') { $options.CheckOnly = $true }
if ($env:TEST_DRAFT -eq '1') { $options.Draft = $true }
& (Join-Path $PSScriptRoot 'tools/publish_github_release.ps1') @options
''')

    def run(check_only=True, draft=False, existing=False, local=COMMIT, remote=COMMIT, shell_override=None):
        env = dict(os.environ, TEST_HEAD_SHA=COMMIT, TEST_LOCAL_SHA=local, TEST_REMOTE_SHA=remote,
                   TEST_GH_LOG=str(tmp_path / "gh.jsonl"), TEST_CHECK_ONLY=str(int(check_only)),
                   TEST_DRAFT=str(int(draft)), TEST_EXISTING_RELEASE=str(int(existing)),
                   TEMP=str(tmp_path), TMP=str(tmp_path))
        result = subprocess.run([shell_override or shell, "-NoProfile", "-File", str(driver)], text=True,
                                capture_output=True, env=env, timeout=45)
        calls = [json.loads(line) for line in (tmp_path / "gh.jsonl").read_text().splitlines()] if (tmp_path / "gh.jsonl").exists() else []
        return result, calls
    return tmp_path, run


def test_check_only_verifies_without_writes_or_github_commands(release_fixture):
    root, run = release_fixture
    manifest = root / "docs/releases/latest.json"
    before = manifest.read_bytes()
    result, calls = run()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "preflight passed" in result.stdout
    assert not calls
    assert manifest.read_bytes() == before
    assert not (root / "msbt_release_notes_v2.11.0.md").exists()


def test_check_only_supports_windows_powershell_5(release_fixture):
    shell = shutil.which("powershell")
    if not shell:
        pytest.skip("Windows PowerShell 5 is unavailable")
    _root, run = release_fixture
    result, calls = run(shell_override=shell)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not calls


@pytest.mark.parametrize("bad", ["portable", "sdkmod", "mobile", "size", "sha512", "embedded", "app_update", "local_tag", "remote_tag"])
def test_preflight_rejects_incomplete_or_mismatched_release(release_fixture, bad):
    root, run = release_fixture
    if bad == "portable": (root / "dist_electron/MSBT-Portable-v2.11.0-win-x64.zip").unlink()
    elif bad == "sdkmod": (root / "MattsSDKBoostingTools.sdkmod").unlink()
    elif bad == "mobile": (root / "dist_mobile/MSBT-Mobile-Controller-1.1.0.apk").unlink()
    elif bad == "embedded": (root / "dist_electron/win-unpacked/resources/sdkmod/MattsSDKBoostingTools.sdkmod").write_bytes(b"stale")
    elif bad == "app_update": (root / "dist_electron/win-unpacked/resources/app-update.yml").unlink()
    elif bad in {"size", "sha512"}:
        path = root / "dist_electron/latest.yml"
        updater = json.loads(path.read_text())
        updater["files"][0][bad] = 999 if bad == "size" else "wrong"
        path.write_text(json.dumps(updater))
    result, calls = run(local=OTHER if bad == "local_tag" else COMMIT, remote=OTHER if bad == "remote_tag" else COMMIT)
    assert result.returncode != 0
    assert not calls


@pytest.mark.parametrize("existing", [False, True])
def test_draft_create_and_edit_keep_badges_and_complete_assets(release_fixture, existing):
    root, run = release_fixture
    result, calls = run(check_only=False, draft=True, existing=existing)
    assert result.returncode == 0, result.stdout + result.stderr
    command = next(call for call in calls if call[1] == ("edit" if existing else "create"))
    assert ("--draft=true" if existing else "--draft") in command
    assert "--latest" not in command
    if not existing:
        assert "--verify-tag" in command
        assert command[command.index("--target") + 1] == COMMIT
    uploaded = next(call for call in calls if call[1] == ("upload" if existing else "create"))
    assert any(str(arg).endswith("MattsSDKBoostingTools.sdkmod") for arg in uploaded)
    assert sum(str(arg).endswith(".apk") for arg in uploaded) == 2
    notes = Path(command[command.index("--notes-file") + 1]).read_text()
    assert "Installer downloads" in notes and "Portable downloads" in notes and "Android APK downloads" in notes
