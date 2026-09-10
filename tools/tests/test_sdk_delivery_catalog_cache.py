"""An SDK-only upgrade must not be downgraded by an older Electron data cache."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from tests.test_quick_menu_last_command import _load_backend_actions

SDK = Path(__file__).resolve().parents[2] / "mod_extracted" / "MattsSDKBoostingTools"
FILES = ("challenge_catalog.json", "shiny_serials.json")


def payload(name, build=None):
    if name == "challenge_catalog.json":
        return {"game_data": {"game_build": build}, "entries": [{"id": "Challenge_Test", "amount": 2}]}
    return [{"serial": "@test-serial", "game_build": build}]


def cache(directory, name, data, build=None, digest=None):
    directory.mkdir(parents=True, exist_ok=True)
    blob = json.dumps(data).encode()
    path = directory / name
    path.write_bytes(blob)
    descriptor = {"path": name, "game_build": build, "sha256": digest or hashlib.sha256(blob).hexdigest()}
    (directory / "catalog_manifest.json").write_text(json.dumps({"files": [descriptor]}))
    return path, blob


@pytest.mark.parametrize("name", FILES)
def test_sdk_only_upgrade_ignores_legacy_cache_and_keeps_complete_bundled_data(tmp_path, monkeypatch, name):
    backend = _load_backend_actions()
    packaged = (SDK / name).read_bytes()
    path, _ = cache(tmp_path, name, payload(name))
    monkeypatch.setattr(backend, "_electron_msbt_data_candidates", lambda _: [str(path)])
    blob, source = backend._read_json_bytes_prefer_electron_cache(name, packaged)
    assert source == "packaged"
    assert blob == packaged


@pytest.mark.parametrize("name", FILES)
@pytest.mark.parametrize("build", ["25234898", "25234899"])
def test_current_and_future_verified_catalogs_are_used(tmp_path, monkeypatch, name, build):
    backend = _load_backend_actions()
    path, cached = cache(tmp_path, name, payload(name, build), build)
    monkeypatch.setattr(backend, "_electron_msbt_data_candidates", lambda _: [str(path)])
    assert backend._read_json_bytes_prefer_electron_cache(name, (SDK / name).read_bytes()) == (cached, str(path))


@pytest.mark.parametrize("bad", ["older", "hash", "malformed", "shape", "missing_manifest", "oversized"])
def test_bad_first_cache_falls_through_to_next_verified_candidate(tmp_path, monkeypatch, bad):
    backend = _load_backend_actions()
    name = "challenge_catalog.json"
    build = "25234897" if bad == "older" else "25234898"
    first, _ = cache(tmp_path / "first", name, [] if bad == "shape" else payload(name, build), build,
                     digest="0" * 64 if bad == "hash" else None)
    if bad == "malformed": first.write_bytes(b"{invalid json")
    elif bad == "oversized": first.write_bytes(b" " * (backend._DELIVERY_CATALOG_MAX_BYTES + 1))
    elif bad == "missing_manifest": (first.parent / "catalog_manifest.json").unlink()
    second, expected = cache(tmp_path / "second", name, payload(name, "25234899"), "25234899")
    monkeypatch.setattr(backend, "_electron_msbt_data_candidates", lambda _: [str(first), str(second)])
    assert backend._read_json_bytes_prefer_electron_cache(name, (SDK / name).read_bytes()) == (expected, str(second))


def test_untagged_legacy_bundles_keep_valid_legacy_cache_preference(tmp_path, monkeypatch):
    backend = _load_backend_actions()
    name = "shiny_serials.json"
    path, expected = cache(tmp_path, name, payload(name))
    monkeypatch.setattr(backend, "_electron_msbt_data_candidates", lambda _: [str(path)])
    assert backend._read_json_bytes_prefer_electron_cache(name, b'[{"serial":"@old"}]') == (expected, str(path))
