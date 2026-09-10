"""v1.10 economy/XP routing without loading the game or optional UI."""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"
TEST_PACKAGE = "msbt_update_test"


@pytest.fixture
def sdk_modules(monkeypatch):
    def module(name, **values):
        result = types.ModuleType(name)
        result.__dict__.update(values)
        monkeypatch.setitem(sys.modules, name, result)
        return result

    def decorator(*_args, **_kwargs):
        def apply(fn):
            fn.add_argument = lambda *_a, **_k: None
            return fn
        return apply

    module(TEST_PACKAGE, __path__=[str(PKG)])
    module("mods_base", command=decorator, hook=decorator, get_pc=lambda: None, ENGINE=None)
    module("unrealsdk", find_all=lambda *_a: [], find_class=lambda *_a: None,
           find_object=lambda *_a: None,
           logging=types.SimpleNamespace(info=lambda *_a: None, error=lambda *_a: None, warning=lambda *_a: None))
    module("unrealsdk.unreal", FGbxDefPtr=object, UObject=object, BoundFunction=object, WrappedStruct=object)
    module("unrealsdk.hooks", Type=types.SimpleNamespace(POST=1))
    module(f"{TEST_PACKAGE}.party_helpers",
           _gbc_find_pc_for_player_state=lambda *_a: None,
           _gbc_is_listen_host_world=lambda *_a: True,
           _gbc_resolve_player_index_for_name_substring=lambda *_a: (0, ""),
           _gbc_session_world_and_gamestate=lambda: (None, None))
    module(f"{TEST_PACKAGE}.camera_tick", register=lambda *_a, **_k: None)
    loaded = []

    def load(name):
        full_name = f"{TEST_PACKAGE}.{name}"
        loaded.append(full_name)
        return importlib.import_module(full_name)

    yield load
    for name in list(sys.modules):
        if name.startswith(TEST_PACKAGE + "."):
            sys.modules.pop(name, None)


def row(token, level=1, points=0):
    return types.SimpleNamespace(ExperienceId=types.SimpleNamespace(Name=token),
                                 ExperienceLevel=level, ExperiencePoints=points)


def test_verified_caps_and_vault_card_five_identifiers(sdk_modules):
    economy = sdk_modules("player_economy")
    params = sdk_modules("game_parameters")
    assert params.MAX_PLAYER_LEVEL == params.MAX_ITEM_LEVEL == 70
    assert params.MAX_SPEC_LEVEL == 701
    assert params.MAX_VAULT_CARD_LEVEL == 9999
    assert economy._CURRENCY_KIND_ALIASES["vaultcard5"] == "VaultCard05_Tokens"
    assert economy._EXPERIENCE_TRACK_ALIASES["vaultcard_xp_5"] == 6
    assert params.status_parameters()["experience_tracks"][-1] == "vaultcard_xp_5"


def test_reordered_vault_card_five_is_targeted_by_its_live_token(sdk_modules):
    economy = sdk_modules("player_economy")
    rows = [row("VaultCard05_Experience"), row("Character", level=60)]
    writes = []
    levels = {entry.ExperienceId.Name: entry.ExperienceLevel for entry in rows}

    def set_level(token, level):
        writes.append((token, level))
        levels[token] = level

    ps = types.SimpleNamespace(ExperienceState=rows, BP_GetExperienceLevel=levels.get,
                               BP_SetExperienceLevel=set_level)
    economy._make_experience_def_ptr = lambda token: token
    assert economy._set_experience_level_via_bp(ps, 6, 9_999_999)
    assert writes == [("VaultCard05_Experience", 9999)]
    assert levels["Character"] == 60


def test_missing_card_five_does_not_write_to_an_unrelated_slot(sdk_modules):
    economy = sdk_modules("player_economy")
    writes = []
    ps = types.SimpleNamespace(
        ExperienceState=[row("Character"), row("Specialization"),
                         row("VaultCard01_Experience"), row("VaultCard02_Experience"),
                         row("VaultCard03_Experience"), row("VaultCard04_Experience"), row("UnrelatedTrack")],
        BP_SetExperienceLevel=lambda *args: writes.append(args),
    )
    economy._make_experience_def_ptr = lambda token: token
    assert not economy._set_experience_level_via_bp(ps, 6, 9999)
    assert writes == []


def test_level_write_rejected_by_game_is_not_reported_successful(sdk_modules):
    economy = sdk_modules("player_economy")
    ps = types.SimpleNamespace(ExperienceState=[row("Character", level=60)],
                               BP_GetExperienceLevel=lambda _token: 60,
                               BP_SetExperienceLevel=lambda *_args: None)
    economy._make_experience_def_ptr = lambda token: token
    assert not economy._set_experience_level_via_bp(ps, 0, 70)


@pytest.mark.parametrize("native_failure", [False, True])
def test_character_level_seventy_preserves_native_xp_without_estimated_fallback(sdk_modules, native_failure):
    economy = sdk_modules("player_economy")
    character = row("Character", level=60, points=123456)
    character.ExperiencePointsRequiredForPreviousLevel = 120000
    character.ExperiencePointsRequiredForNextLevel = 130000
    initial = vars(character).copy()

    def native_set_level(_token, level):
        if native_failure:
            raise RuntimeError("native XP setter unavailable")
        character.ExperienceLevel = level
        # Deliberately unlike the old curve so any estimated overwrite is visible.
        character.ExperiencePoints = 87654321
        character.ExperiencePointsRequiredForPreviousLevel = 87654321
        character.ExperiencePointsRequiredForNextLevel = 88765432

    ps = types.SimpleNamespace(ExperienceState=[character],
                               BP_GetExperienceLevel=lambda _: character.ExperienceLevel,
                               BP_SetExperienceLevel=native_set_level)
    economy._make_experience_def_ptr = lambda token: token
    assert economy._set_experience_level_via_bp(ps, 0, 70) is (not native_failure)
    if native_failure:
        assert vars(character) == initial
    else:
        assert character.ExperienceLevel == 70
        assert character.ExperiencePoints == character.ExperiencePointsRequiredForPreviousLevel == 87654321
        assert character.ExperiencePointsRequiredForNextLevel == 88765432

    for level in range(61, 71):
        assert economy._character_cumulative_total_xp(level) is None
        assert economy._cumulative_floor_for_track(0, level, 60, 123456) is None
        assert economy._cumulative_next_floor_for_track(0, level - 1, 60, 123456) is None


def test_legacy_unreadable_tokens_keep_existing_slot_fallback(sdk_modules):
    params = sdk_modules("game_parameters")
    rows = [types.SimpleNamespace() for _ in range(7)]
    assert params.experience_row_for_track(rows, 4) is rows[4]
    assert params.experience_row_for_track(rows, 6) is None


def test_combat_xp_tracks_reordered_fifth_card_and_ignores_unknown_rows(sdk_modules):
    cxp = sdk_modules("extreme_combat_xp")
    ps = types.SimpleNamespace(ExperienceState=[row("VaultCard05_Experience", points=234),
                                                row("UnrelatedTrack", points=567),
                                                row("Character", points=89)])
    assert cxp._snapshot_points(ps) == {0: 89, 6: 234}
    assert cxp._max_level(6) == 9999


def test_max_vault_cards_includes_fifth_card_at_verified_cap(sdk_modules):
    economy = sdk_modules("player_economy")
    boost = sdk_modules("vault_card_boost")
    writes = []
    economy._give_currency_on_pc = lambda _pc, token, amount: writes.append(("currency", token, amount)) or True
    economy._set_experience_level_via_bp = lambda _ps, track, level: writes.append(("xp", track, level)) or True
    ok, _ = boost._economy_max_vault_cards(types.SimpleNamespace(PlayerState=object()), log=lambda _: None)
    assert ok
    assert len(writes) == 10
    assert ("currency", "VaultCard05_Tokens", 2147483647) in writes
    assert ("xp", 6, 9999) in writes


def test_loveless_root_is_buildable_and_serial_level_stays_within_game_cap(sdk_modules):
    builder = sdk_modules("legit_builder_core")
    root = {"key": "classmod_corpohacker", "serial": 402, "deps": []}
    assert builder.is_buildable_root(root)
    assert builder._annotate_root(root)["build_label"] == "Loveless Class Mod"
    builder.get_root = lambda _key: root
    builder._selected_parts = lambda _root, _selected: []
    assert builder.build_human(root["key"], []).startswith("402, 0, 1, 70|")
    assert builder.build_human(root["key"], [], level=72).startswith("402, 0, 1, 70|")


def test_loveless_item_metadata_uses_character_name(sdk_modules):
    metadata = sdk_modules("serial_item_meta")
    metadata._type_id_index = lambda: {402: ("classmod_corpohacker", {})}
    info = metadata.type_info_from_id(402)
    assert info["type"] == "Classmod"
    assert info["character_class"] == "Loveless"


def test_drop_all_shinies_adds_new_catalog_pools_but_explicit_subsets_stay_narrow(sdk_modules, monkeypatch):
    import json
    shinies = sdk_modules("shinies")
    catalog = [{"itempool": "itempool_Old_shiny"}, {"itempool": "itempool_New_shiny"}, {"itempool": "itempool_ordinary"}]
    monkeypatch.setattr(shinies.pkgutil, "get_data", lambda *_: json.dumps(catalog).encode())
    shinies.SHINY_ITEMPOOLS = ("itempool_old_shiny", "itempool_old_shiny")
    shinies._get_world = shinies._get_runtime_pc = shinies._get_pool_store = lambda: object()
    shinies._get_spawn_transform = lambda _: object()
    shinies._get_player_pose = lambda _: (object(), object())
    shinies._spawn_pose = lambda *_: (object(), object())
    spawned = []
    shinies._spawn_pool = lambda _c, _w, _t, _l, pool, *_pose: spawned.append(pool)
    assert shinies.drop_all_shinies() == 2
    assert spawned == ["itempool_Old_shiny", "itempool_New_shiny"]
    spawned.clear()
    assert shinies._spawn_all_shinies(70, pools=["itempool_old_shiny"]) == 1
    assert spawned == ["itempool_Old_shiny"]
    spawned.clear()
    assert shinies._spawn_all_shinies(70, pools=[]) == 0
    assert spawned == []
