"""Exercise the real settings functions without starting Unreal or its worker."""
import ast
import json
import os
from pathlib import Path
import tempfile
import threading
from typing import Any
from unittest.mock import patch

import pytest


def settings_module(tmp_path):
    source = Path(__file__).parents[2] / "mod_extracted/MattsSDKBoostingTools/inventory_capacity.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    functions = ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef)], type_ignores=[])
    scope = dict(Path=Path, Any=Any, json=json, os=os, tempfile=tempfile, threading=threading,
                 _settings_lock=threading.RLock(), _DEFAULT_SETTINGS={}, _MIN_CONTAINER_SIZE=1,
                 _MAX_CONTAINER_SIZE=9999, _DEFAULT_BACKPACK_SIZE=70, _DEFAULT_BANK_SIZE=500)
    exec(compile(functions, str(source), "exec"), scope)
    paths = [tmp_path / "first" / "settings.json", tmp_path / "second" / "settings.json"]
    scope["_candidate_settings_paths"] = lambda: paths
    scope["_log"] = lambda message: None
    return scope, paths


def test_quick_menu_and_checkboxes_roundtrip(tmp_path):
    scope, paths = settings_module(tmp_path)
    scope["save_extra_settings"](quick_menu={"chrome": {"rarity_panel_equipped": True}})
    scope["save_inventory_settings"](auto_inventory_sizes=True, backpack_size=321)
    reopened, _ = settings_module(tmp_path)
    data = reopened["load_inventory_settings"]()
    assert data["quick_menu"]["chrome"]["rarity_panel_equipped"] is True
    assert data["auto_inventory_sizes"] is True
    assert data["backpack_size"] == 321


def test_failed_replace_preserves_file_and_reports_failure(tmp_path):
    scope, paths = settings_module(tmp_path)
    scope["save_extra_settings"](quick_menu={"page": 2})
    before = paths[0].read_bytes()
    with patch.object(os, "replace", side_effect=PermissionError("locked")):
        with pytest.raises(PermissionError):
            scope["save_extra_settings"](quick_menu={"page": 3})
    assert paths[0].read_bytes() == before
    assert not list(paths[0].parent.glob("*.tmp"))


def test_updates_existing_fallback_instead_of_creating_competing_file(tmp_path):
    scope, paths = settings_module(tmp_path)
    paths[1].parent.mkdir()
    paths[1].write_text('{"quick_menu":{"page":2}}', encoding="utf-8")
    scope["save_inventory_settings"](auto_inventory_sizes=False)
    assert not paths[0].exists()
    assert scope["load_inventory_settings"]()["quick_menu"]["page"] == 2


def test_real_registry_restores_chrome_and_slots_from_disk(tmp_path, monkeypatch):
    from tests.test_quick_menu_registry import _registry
    scope, _ = settings_module(tmp_path)
    registry = _registry()
    monkeypatch.setattr(registry, "load_inventory_settings", scope["load_inventory_settings"])
    monkeypatch.setattr(registry, "save_extra_settings", scope["save_extra_settings"])
    result = registry.set_quick_menu_layout({"page": 2, "edit_mode": True,
        "chrome": {"rarity_panel_equipped": True, "panel_opacity": 0.65}})
    assert result["ok"]
    result = registry.assign_quick_menu_slot({"page": 2, "slot": 4, "action": "max_currency",
        "label_mode": "custom", "custom_label": "Saved test"})
    assert result["ok"]
    reopened, _ = settings_module(tmp_path)
    monkeypatch.setattr(registry, "load_inventory_settings", reopened["load_inventory_settings"])
    layout = registry.load_persisted_layout()
    assert layout["page"] == 2
    assert layout["edit_mode"] is True
    assert layout["chrome"]["rarity_panel_equipped"] is True
    assert layout["chrome"]["panel_opacity"] == 0.65
    assert layout["pages"][2][4]["custom_label"] == "Saved test"
    with patch.object(os, "replace", side_effect=PermissionError("locked")):
        with pytest.raises(PermissionError):
            registry.set_quick_menu_layout({"page": 0})
    assert registry.load_persisted_layout()["page"] == 2
