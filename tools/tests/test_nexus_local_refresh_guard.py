from __future__ import annotations

import hashlib
import json

from tools import refresh_matt_editor_catalogs as refresh


def local_import(tmp_path, monkeypatch):
    monkeypatch.setattr(refresh, "LEGIT", tmp_path)
    monkeypatch.setattr(refresh, "BACKUP_DIR", tmp_path / "backups")
    original = b'{"inv":{"current_game":true}}'
    target = tmp_path / "Nexus-Data-inv4.json"
    target.write_bytes(original)
    provenance = tmp_path / "local_game_data_provenance.json"
    provenance.write_text(json.dumps({
        "game_build": "25234898",
        "imported": [{"file": target.name, "imported_sha256": hashlib.sha256(original).hexdigest()}],
    }), encoding="utf-8")
    return target, provenance


def test_local_import_and_later_local_edits_are_preserved_without_network(tmp_path, monkeypatch):
    target, provenance = local_import(tmp_path, monkeypatch)
    proof = provenance.read_bytes()
    def forbidden_fetch(*args, **kwargs):
        raise AssertionError("protected Nexus tables must not trigger a download")
    monkeypatch.setattr(refresh, "fetch_bytes", forbidden_fetch)
    for content in [target.read_bytes(), b'{"inv":{"curated_local_change":true}}']:
        target.write_bytes(content)
        result = refresh.sync_nexus(["inv4"])
        assert result["preserved_local"] == ["inv4"]
        assert result["ok"] == result["failed"] == []
        assert target.read_bytes() == content
        assert provenance.read_bytes() == proof


def test_explicit_override_fetches_backs_up_and_retains_original_provenance(tmp_path, monkeypatch):
    target, provenance = local_import(tmp_path, monkeypatch)
    original, proof = target.read_bytes(), provenance.read_bytes()
    remote = b'{"inv":{"online_content":true}}'
    calls = []
    def fetch(url, **kwargs):
        calls.append(url)
        return remote
    monkeypatch.setattr(refresh, "fetch_bytes", fetch)
    result = refresh.sync_nexus(["inv4"], replace_local_nexus=True)
    assert result["ok"] == ["inv4"]
    assert result["preserved_local"] == []
    assert len(calls) == 1 and "file=inv4" in calls[0]
    assert target.read_bytes() == remote
    assert next((tmp_path / "backups").glob("*.bak")).read_bytes() == original
    assert provenance.read_bytes() == proof
    assert hashlib.sha256(remote).hexdigest() != json.loads(proof)["imported"][0]["imported_sha256"]


def test_unprotected_or_missing_nexus_file_still_syncs(tmp_path, monkeypatch):
    target, _ = local_import(tmp_path, monkeypatch)
    target.unlink()
    monkeypatch.setattr(refresh, "fetch_bytes", lambda *args, **kwargs: b'{"inv":{}}')
    result = refresh.sync_nexus(["inv4", "inv0"])
    assert result["ok"] == ["inv4", "inv0"]
    assert result["preserved_local"] == []


def test_reconciled_hotfix_layer_is_protected_without_native_source_file(tmp_path, monkeypatch):
    _, provenance = local_import(tmp_path, monkeypatch)
    proof = json.loads(provenance.read_text())
    proof["missing_source_files"] = ["Nexus-Data-inv.json"]
    proof["hotfix_override_comparison"] = {"superseded_same_serial_identity": ["weapon.part"], "preserved_unmatched": []}
    provenance.write_text(json.dumps(proof), encoding="utf-8")
    hotfix = tmp_path / "Nexus-Data-inv.json"
    hotfix.write_bytes(b'{"inv":{"records":[]}}')
    calls = []
    monkeypatch.setattr(refresh, "fetch_bytes", lambda *args, **kwargs: calls.append(args))
    result = refresh.sync_nexus(["inv"])
    assert result["preserved_local"] == ["inv"]
    assert calls == []
    assert hotfix.read_bytes() == b'{"inv":{"records":[]}}'
