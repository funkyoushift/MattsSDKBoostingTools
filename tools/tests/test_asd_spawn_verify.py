"""One-at-a-time ASD spawn verify pipeline (no game)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

os.environ["ASD_SPAWN_VERIFY_SKIP"] = "1"

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
SCRIPT = TOOLS / "asd_spawn_verify.py"
CATALOG = ROOT / "electron_poc" / "dev_spawner_catalog.json"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import asd_spawn_verify as verify  # noqa: E402


def _tiny_catalog() -> dict:
    return {
        "categories": {
            "Characters": [
                "Char_ArmyBandit_SHARED",
                "Char_ScavGunToterAssault",
                "Char_NPC_NudgeCouncil04",
                "Char_Gadget_AutoTurret_Base",
                "IO_VendingMachine_Munitions",
                "Char_AI",
            ],
            "Interactive Objects": ["IO_VendingMachine_Munitions"],
        },
        "display_names": {
            "Char_ArmyBandit_SHARED": "Army Bandit",
            "Char_ScavGunToterAssault": "Scav Junker",
            "IO_VendingMachine_Munitions": "Vending machine",
        },
        "actor_metadata": {
            "Char_ArmyBandit_SHARED": {"is_boss": False},
            "Char_ScavGunToterAssault": {"is_boss": False},
            "Char_NPC_NudgeCouncil04": {"is_boss": False},
        },
    }


def test_pyexec_auto_main_and_uses_hybrid_only():
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in source
    assert "else:\n    main()" in source
    assert "spawn_live" in source
    assert "despawn_tracked" in source
    assert "apply_aggro_to_tracked" in source
    assert "AsdSpawnVerify" in source
    assert "queued_unverified" in source
    assert 'find_all("Object")' not in source
    assert "find_all('Object')" not in source
    assert "sdk_mods" not in source or "do not copy sdk_mods" in source
    assert "process_one" in source
    assert "spawn_name_attempts" in source
    assert "ensure_name_queue" in source
    assert "patch_hybrid_for_verify" in source
    assert "_SPAWNER_POLL_TIMEOUT_S" in source
    assert "VERIFY start" in source
    assert "VERIFY end" in source
    assert "aggro unchecked" in source
    assert "def start(" in source
    assert "def abort(" in source
    assert "def step(" in source
    assert "camera_tick.register" in source
    assert "enable_shared_hook" in source
    assert "force_in_world" in source
    assert "PUMP start" in source
    assert "PUMP abort" in source
    assert "_STEP_INTERVAL_S" in source
    assert "world_delta" in source
    assert "census_world_pawns" in source
    assert "_CENSUS_CLASSES" in source
    assert "_spawn_and_place" in source
    assert "spawned_as" in source
    assert "hold pawn until next step" in source
    assert "clone:any-live" not in source
    assert "is_player_census_row" in source
    assert "cleanup_player_clones" in source
    assert "K2_LineTrace" not in source
    assert "LineTraceSingle" not in source


def test_enemy_filter_matches_dev_spawner_keep_drop():
    catalog = _tiny_catalog()
    assert verify.is_enemy_actor("Char_ArmyBandit_SHARED", catalog) is True
    assert verify.is_enemy_actor("Char_ScavGunToterAssault", catalog) is True
    assert verify.is_enemy_actor("Char_NPC_NudgeCouncil04", catalog) is False
    assert verify.is_enemy_actor("Char_Gadget_AutoTurret_Base", catalog) is False
    assert verify.is_enemy_actor("artillery_payload", catalog) is False
    assert verify.is_vendor_skip("IO_VendingMachine_Munitions", catalog) is True
    queue = verify.build_queue(catalog)
    assert queue == ["Char_ArmyBandit_SHARED", "Char_ScavGunToterAssault"]


def test_real_catalog_queue_is_enemies_not_vendors():
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    queue = verify.build_queue(catalog)
    assert "Char_ScavGunToterAssault" in queue
    assert "Char_ArmyBandit_SHARED" in queue
    assert queue[0] == "Char_ArmyBandit_SHARED" or queue[0].startswith("Char_")
    assert all(not verify.is_vendor_skip(name, catalog) for name in queue)
    assert "IO_VendingMachine_Munitions" not in queue
    assert "Char_NPC_NudgeCouncil04" not in queue
    assert len(queue) > 400
    assert len(queue) < 4000


def _snap(name: str, addr: int, *, cls: str = "OakCharacter") -> dict:
    return {
        "name": f"{name}_C" if not name.endswith("_C") else name,
        "class": cls,
        "def": name.replace("_C", ""),
        "addr": addr,
        "xyz": [10.0, 20.0, 30.0],
    }


def _world_box() -> tuple[list[dict], callable, callable, callable]:
    """Shared mock world: spawn appends a pawn, despawn pops, census snapshots."""
    rows: list[dict] = []

    def census() -> list[dict]:
        return list(rows)

    def spawn(name: str, count: int = 1) -> dict:
        rows.append(_snap(name, 1000 + len(rows)))
        return _ok_spawn(name, count)

    def despawn() -> dict:
        if rows:
            rows.pop()
        return {"ok": True, "message": "cleared 1"}

    return rows, census, spawn, despawn


def test_world_delta_uses_addr_then_name():
    before = [_snap("Char_Old", 1)]
    after = [_snap("Char_Old", 1), _snap("Char_New", 2)]
    new = verify.world_delta(before, after)
    assert len(new) == 1
    assert new[0]["def"] == "Char_New"
    assert verify.world_delta(after, after) == []
    assert verify.prepend_known_good(["Char_ArmyBandit_SHARED"])[0] == "Char_Mandolin_SoldierAR"


def test_spawn_attempts_try_plain_then_class_suffix():
    assert verify.spawn_name_attempts("Char_ScavGunToterAssault") == [
        ("Char_ScavGunToterAssault", "spawn_live"),
        ("Char_ScavGunToterAssault_C", "spawn_live_C"),
    ]
    assert verify.spawn_name_attempts("Char_Foo_C") == [("Char_Foo_C", "spawn_live")]


def test_verify_rejects_queued_unverified():
    assert verify.spawn_is_verified({"ok": True, "verification_status": "queued_unverified"}) is False
    assert verify.spawn_is_verified(
        {"ok": True, "verification_status": "verified_spawned", "spawn_verified": True, "alive_count": 1}
    ) is True
    assert verify.has_aggro({"has_controller": True, "Enemy": "OakPlayer"}) is True
    assert verify.has_aggro({"has_controller": True}) is False
    assert verify.has_aggro({"has_controller": False, "Enemy": "x"}) is False


def test_one_at_a_time_success_then_next(tmp_path: Path):
    catalog = _tiny_catalog()
    _rows, census, spawn, despawn = _world_box()
    calls: list[str] = []

    def spawn_wrap(name: str, count: int = 1) -> dict:
        calls.append(f"spawn:{name}:{count}")
        return spawn(name, count)

    def despawn_wrap() -> dict:
        calls.append("despawn")
        return despawn()

    first = verify.process_one(
        tmp_path,
        catalog,
        spawn_fn=spawn_wrap,
        despawn_fn=despawn_wrap,
        census_world_fn=census,
        combat_dump_fn=lambda _a: {"has_controller": True, "Enemy": "OakPlayer"},
        tracked_actors_fn=lambda: [object()],
        log_fn=lambda _m: None,
    )
    assert first["ok"] is True
    assert first["name"] == "Char_ArmyBandit_SHARED"
    assert first["method"] == "oak-spawner"
    assert first["aggro"] is True
    assert first["despawned"] is False
    assert first["before_n"] == 0
    assert first["after_n"] == 1
    assert first["spawned_as"]
    assert calls.count("despawn") == 0
    assert calls[0].startswith("spawn:Char_ArmyBandit_SHARED:")
    success = json.loads((tmp_path / "success.json").read_text(encoding="utf-8"))
    assert success[0]["name"] == "Char_ArmyBandit_SHARED"
    assert success[0]["method"] == "oak-spawner"
    assert success[0]["aggro"] == "yes"
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["next_index"] == 1
    assert state["held"] is True

    second = verify.process_one(
        tmp_path,
        catalog,
        spawn_fn=spawn_wrap,
        despawn_fn=despawn_wrap,
        census_world_fn=census,
        combat_dump_fn=lambda _a: {"has_controller": True, "Enemy": "OakPlayer"},
        tracked_actors_fn=lambda: [object()],
        log_fn=lambda _m: None,
    )
    assert second["name"] == "Char_ScavGunToterAssault"
    assert second["ok"] is True
    assert calls.count("despawn") == 1
    state_after = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state_after["next_index"] == 2
    assert state_after["done"] is True
    assert state_after["held"] is True
    assert len(json.loads((tmp_path / "success.json").read_text(encoding="utf-8"))) == 2
    assert "Char_ScavGunToterAssault" in (tmp_path / "success.txt").read_text(encoding="utf-8")


def test_failed_plain_name_retries_class_suffix(tmp_path: Path):
    catalog = _tiny_catalog()
    seen: list[str] = []
    rows: list[dict] = []

    def spawn(name: str, count: int = 1) -> dict:
        seen.append(name)
        if name.endswith("_C"):
            rows.append(_snap(name, 7))
            return {
                "ok": True,
                "mode": "asd_hybrid_class",
                "verification_status": "verified_spawned",
                "spawn_verified": True,
                "spawned_count": 1,
                "alive_count": 1,
                "source_path": "class:find_class Char_ArmyBandit_SHARED_C",
            }
        return {"ok": False, "verification_status": "no_pawn", "alive_count": 0, "spawned_count": 0}

    result = verify.process_one(
        tmp_path,
        catalog,
        spawn_fn=spawn,
        despawn_fn=lambda: {"ok": True, "message": "cleared"},
        census_world_fn=lambda: list(rows),
        combat_dump_fn=lambda _a: {"has_controller": False},
        tracked_actors_fn=lambda: [object()],
        aggro_fn=lambda: "Attack-me aggro: ok=1 miss=0 mobs=1.",
        log_fn=lambda _m: None,
    )
    assert seen == ["Char_ArmyBandit_SHARED", "Char_ArmyBandit_SHARED_C"]
    assert result["ok"] is True
    assert result["method"] == "thin-air"
    assert result["spawned_as"]


def test_no_pawn_is_fail_and_still_despawns(tmp_path: Path):
    catalog = _tiny_catalog()
    despawns = {"n": 0}

    def spawn(name: str, count: int = 1) -> dict:
        return {
            "ok": False,
            "verification_status": "no_pawn",
            "spawn_verified": False,
            "alive_count": 0,
            "message": "GetAliveActors stayed empty",
        }

    result = verify.process_one(
        tmp_path,
        catalog,
        spawn_fn=spawn,
        despawn_fn=lambda: despawns.__setitem__("n", despawns["n"] + 1) or {"ok": True},
        census_world_fn=lambda: [],
        log_fn=lambda _m: None,
    )
    assert result["ok"] is False
    assert result["name"] == "Char_ArmyBandit_SHARED"
    assert result["despawned"] is True
    assert result["before_n"] == 0
    assert result["after_n"] == 0
    assert "empty world delta" in result["message"]
    assert despawns["n"] >= 1
    fail = json.loads((tmp_path / "fail.json").read_text(encoding="utf-8"))
    assert fail[0]["name"] == "Char_ArmyBandit_SHARED"
    assert fail[0]["method"] == "none"
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["next_index"] == 1
    assert state["last_ok"] is False


def test_missing_aggro_runs_combat_arm(tmp_path: Path):
    catalog = _tiny_catalog()
    dumps = [
        {"has_controller": True},
        {"has_controller": True, "Enemy": "OakPlayer"},
    ]
    aggro_calls = {"n": 0}

    def dump(_actor: object) -> dict:
        return dumps.pop(0) if dumps else {"has_controller": True, "Enemy": "OakPlayer"}

    rows: list[dict] = []

    def spawn(name: str, count: int = 1) -> dict:
        rows.append(_snap(name, 11))
        return {
            "ok": True,
            "mode": "asd_hybrid_clone",
            "verification_status": "verified_spawned",
            "spawn_verified": True,
            "spawned_count": 1,
            "alive_count": 1,
            "source_path": "cloned",
        }

    result = verify.process_one(
        tmp_path,
        catalog,
        spawn_fn=spawn,
        despawn_fn=lambda: {"ok": True},
        aggro_fn=lambda: aggro_calls.__setitem__("n", aggro_calls["n"] + 1) or "Attack-me aggro: ok=1 miss=0 mobs=1.",
        combat_dump_fn=dump,
        tracked_actors_fn=lambda: [object()],
        census_world_fn=lambda: list(rows),
        log_fn=lambda _m: None,
    )
    assert result["ok"] is True
    assert result["method"] == "cloned"
    assert result["aggro"] is True
    assert aggro_calls["n"] == 1


def test_process_one_uses_names_not_full_catalog(tmp_path: Path):
    catalog = {
        "categories": {"Characters": [f"Char_SkipMe_{i}" for i in range(80)]},
        "display_names": {},
        "actor_metadata": {},
    }
    seen: list[str] = []

    rows: list[dict] = []

    def spawn(name: str, count: int = 1) -> dict:
        seen.append(name)
        rows.append(_snap(name, 21))
        return {
            "ok": True,
            "mode": "asd_hybrid_spawner",
            "verification_status": "verified_spawned",
            "spawn_verified": True,
            "spawned_count": 1,
            "alive_count": 1,
            "source_path": f"PushActorDef:{name}",
        }

    result = verify.process_one(
        tmp_path,
        catalog,
        names=["Char_OnlyThisOne"],
        spawn_fn=spawn,
        despawn_fn=lambda: {"ok": True},
        census_world_fn=lambda: list(rows),
        combat_dump_fn=lambda _a: {"has_controller": True, "Enemy": "OakPlayer"},
        tracked_actors_fn=lambda: [object()],
        log_fn=lambda _m: None,
    )
    assert seen == ["Char_OnlyThisOne"]
    assert result["name"] == "Char_OnlyThisOne"
    assert result["total"] == 1
    assert result["ok"] is True
    assert "Char_SkipMe_0" not in seen


def test_process_one_does_not_spawn_whole_queue(tmp_path: Path):
    catalog = _tiny_catalog()
    seen: list[str] = []

    rows: list[dict] = []

    def spawn(name: str, count: int = 1) -> dict:
        seen.append(name)
        rows.append(_snap(name, 31))
        return {
            "ok": True,
            "mode": "asd_hybrid_class",
            "verification_status": "verified_spawned",
            "spawn_verified": True,
            "spawned_count": 1,
            "alive_count": 1,
            "source_path": "class:x",
        }

    first = verify.process_one(
        tmp_path,
        catalog,
        spawn_fn=spawn,
        despawn_fn=lambda: {"ok": True},
        census_world_fn=lambda: list(rows),
        combat_dump_fn=lambda _a: {"has_controller": True, "Enemy": "OakPlayer"},
        tracked_actors_fn=lambda: [object()],
        log_fn=lambda _m: None,
    )
    assert first["name"] == "Char_ArmyBandit_SHARED"
    assert seen == ["Char_ArmyBandit_SHARED"]
    assert "Char_ScavGunToterAssault" not in seen


def test_ensure_name_queue_caches_and_skips_rebuild(tmp_path: Path):
    loads = {"n": 0}

    def loader() -> dict:
        loads["n"] += 1
        return _tiny_catalog()

    first = verify.ensure_name_queue(tmp_path, catalog_loader=loader)
    assert first == ["Char_ArmyBandit_SHARED", "Char_ScavGunToterAssault"]
    assert loads["n"] == 1
    assert (tmp_path / "catalog.json").is_file()

    second = verify.ensure_name_queue(tmp_path, catalog_loader=loader)
    assert second == first
    assert loads["n"] == 1


def test_hybrid_verify_patch_zeroes_poll_timeout():
    class FakeHybrid:
        _SPAWNER_POLL_TIMEOUT_S = 8.0

        def find_live_sources(self, name: str) -> list:
            return ["scan-all"]

        def find_hostile_team_donor(self, *a, **k):
            return "donor"

        def _iter_world_pawns(self) -> list:
            return []

        def _matches_wanted(self, actor, name) -> bool:
            return False

    hybrid = FakeHybrid()
    restored = verify.patch_hybrid_for_verify(hybrid)
    assert hybrid._SPAWNER_POLL_TIMEOUT_S == 0.0
    assert hybrid.find_live_sources("Char_X") == []
    assert hybrid.find_hostile_team_donor() is None
    verify.restore_hybrid(hybrid, restored)
    assert hybrid._SPAWNER_POLL_TIMEOUT_S == 8.0
    assert hybrid.find_live_sources("Char_X") == ["scan-all"]
    assert hybrid.find_hostile_team_donor() == "donor"


def test_aggro_unchecked_after_one_peek_and_attack(tmp_path: Path):
    dumps = [{"has_controller": True}, {"has_controller": True}]
    aggro_calls = {"n": 0}

    def dump(_actor: object) -> dict:
        return dumps.pop(0) if dumps else {"has_controller": True}

    rows: list[dict] = []

    def spawn(name: str, count: int = 1) -> dict:
        rows.append(_snap(name, 41))
        return {
            "ok": True,
            "mode": "asd_hybrid_spawner",
            "verification_status": "verified_spawned",
            "spawn_verified": True,
            "spawned_count": 1,
            "alive_count": 1,
            "source_path": "PushActorDef:x",
        }

    result = verify.process_one(
        tmp_path,
        _tiny_catalog(),
        spawn_fn=spawn,
        despawn_fn=lambda: {"ok": True},
        aggro_fn=lambda: aggro_calls.__setitem__("n", aggro_calls["n"] + 1) or "Attack-me",
        combat_dump_fn=dump,
        tracked_actors_fn=lambda: [object()],
        census_world_fn=lambda: list(rows),
        log_fn=lambda _m: None,
    )
    assert result["ok"] is True
    assert result["aggro"] is None
    assert aggro_calls["n"] == 1
    assert "aggro unchecked" in result["message"]
    success = json.loads((tmp_path / "success.json").read_text(encoding="utf-8"))
    assert success[0]["aggro"] == "unchecked"


def _ok_spawn(name: str, count: int = 1) -> dict:
    return {
        "ok": True,
        "mode": "asd_hybrid_spawner",
        "verification_status": "verified_spawned",
        "spawn_verified": True,
        "spawned_count": 1,
        "alive_count": 1,
        "source_path": f"PushActorDef:{name}",
        "combat_state": {"has_controller": True, "Enemy": "OakPlayer"},
    }


def test_start_arms_runner_without_processing(tmp_path: Path):
    verify.abort(despawn=False)
    _rows, census, spawn, despawn = _world_box()
    seen: list[str] = []

    def spawn_wrap(name: str, count: int = 1) -> dict:
        seen.append(name)
        return spawn(name, count)

    armed = verify.start(
        tmp_path,
        names=["Char_One", "Char_Two", "Char_Three"],
        spawn_fn=spawn_wrap,
        despawn_fn=despawn,
        census_world_fn=census,
        combat_dump_fn=lambda _a: {"has_controller": True, "Enemy": "OakPlayer"},
        tracked_actors_fn=lambda: [object()],
        attach_camera=False,
        log_fn=lambda _m: None,
    )
    assert armed["ok"] is True
    assert armed["running"] is True
    assert verify.is_running() is True
    assert seen == []
    assert not (tmp_path / "success.json").is_file()
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["next_index"] == 0
    assert state["pump"] == "running"
    verify.abort(despawn=False)


def test_one_step_processes_exactly_one_row_and_advances(tmp_path: Path):
    verify.abort(despawn=False)
    seen: list[str] = []
    names = ["Char_One", "Char_Two", "Char_Three"]
    _rows, census, spawn, despawn = _world_box()

    def spawn_wrap(name: str, count: int = 1) -> dict:
        seen.append(name)
        return spawn(name, count)

    verify.start(
        tmp_path,
        names=names,
        spawn_fn=spawn_wrap,
        despawn_fn=despawn,
        census_world_fn=census,
        combat_dump_fn=lambda _a: {"has_controller": True, "Enemy": "OakPlayer"},
        tracked_actors_fn=lambda: [object()],
        attach_camera=False,
        log_fn=lambda _m: None,
    )
    first = verify.step(now=1000.0)
    assert first is not None
    assert first["name"] == "Char_One"
    assert first["ok"] is True
    assert seen == ["Char_One"]
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["next_index"] == 1
    assert verify.is_running() is True

    skipped = verify.step(now=1000.1)
    assert skipped is None
    assert seen == ["Char_One"]
    assert json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))["next_index"] == 1

    second = verify.step(now=1002.1)
    assert second is not None
    assert second["name"] == "Char_Two"
    assert seen == ["Char_One", "Char_Two"]
    assert json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))["next_index"] == 2
    verify.abort(despawn=False)


def test_abort_clears_runner_and_leaves_next_index(tmp_path: Path):
    verify.abort(despawn=False)
    despawns = {"n": 0}
    _rows, census, spawn, _despawn = _world_box()

    verify.start(
        tmp_path,
        names=["Char_One", "Char_Two"],
        spawn_fn=spawn,
        despawn_fn=lambda: despawns.__setitem__("n", despawns["n"] + 1) or {"ok": True},
        census_world_fn=census,
        combat_dump_fn=lambda _a: {"has_controller": True, "Enemy": "OakPlayer"},
        tracked_actors_fn=lambda: [object()],
        attach_camera=False,
        log_fn=lambda _m: None,
    )
    verify.step(now=1000.0)
    assert verify.is_running() is True
    stopped = verify.abort()
    assert stopped["ok"] is True
    assert stopped["running"] is False
    assert stopped["was_running"] is True
    assert verify.is_running() is False
    assert verify.step(now=2000.0) is None
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["next_index"] == 1
    assert state["pump"] == "idle"
    assert despawns["n"] >= 1


def test_step_does_not_walk_full_catalog(tmp_path: Path):
    verify.abort(despawn=False)
    names = [f"Char_Row_{i}" for i in range(20)]
    seen: list[str] = []

    _rows, census, spawn, despawn = _world_box()
    verify.start(
        tmp_path,
        names=names,
        spawn_fn=lambda name, count=1: seen.append(name) or spawn(name, count),
        despawn_fn=despawn,
        census_world_fn=census,
        combat_dump_fn=lambda _a: {"has_controller": True, "Enemy": "OakPlayer"},
        tracked_actors_fn=lambda: [object()],
        attach_camera=False,
        log_fn=lambda _m: None,
    )
    verify.step(now=1.0)
    assert seen == ["Char_Row_0"]
    assert json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))["next_index"] == 1
    assert verify.is_running() is True
    verify.abort(despawn=False)


def test_start_resumes_existing_next_index(tmp_path: Path):
    verify.abort(despawn=False)
    (tmp_path / "state.json").write_text(
        json.dumps({"next_index": 1, "total": 2, "done": False}),
        encoding="utf-8",
    )
    seen: list[str] = []
    _rows, census, spawn, despawn = _world_box()
    verify.start(
        tmp_path,
        names=["Char_ArmyBandit_SHARED", "Char_ArmyDahl", "Char_Three"],
        spawn_fn=lambda name, count=1: seen.append(name) or spawn(name, count),
        despawn_fn=despawn,
        census_world_fn=census,
        combat_dump_fn=lambda _a: {"has_controller": True, "Enemy": "OakPlayer"},
        tracked_actors_fn=lambda: [object()],
        attach_camera=False,
        log_fn=lambda _m: None,
    )
    result = verify.step(now=50.0)
    assert result is not None
    assert result["name"] == "Char_ArmyDahl"
    assert seen == ["Char_ArmyDahl"]
    verify.abort(despawn=False)


def test_hybrid_ok_empty_world_delta_is_fail(tmp_path: Path):
    """spawn_live claiming success is not enough — empty census is fail."""
    result = verify.process_one(
        tmp_path,
        _tiny_catalog(),
        spawn_fn=lambda name, count=1: _ok_spawn(name, count),
        despawn_fn=lambda: {"ok": True},
        census_world_fn=lambda: [],
        log_fn=lambda _m: None,
    )
    assert result["ok"] is False
    assert result["new_actors"] == []
    assert "empty world delta" in result["message"]
    latest = (tmp_path / "latest.txt").read_text(encoding="utf-8")
    assert "before_n=0" in latest
    assert "after_n=0" in latest


def test_world_delta_any_new_pawn_is_success(tmp_path: Path):
    """A new hostile/AI pawn counts even when spawn_live says no_pawn."""
    rows: list[dict] = []

    def spawn(name: str, count: int = 1) -> dict:
        rows.append(_snap("Char_Mandolin_SoldierAR", 99))
        return {"ok": False, "verification_status": "no_pawn", "alive_count": 0, "spawned_count": 0}

    result = verify.process_one(
        tmp_path,
        _tiny_catalog(),
        spawn_fn=spawn,
        despawn_fn=lambda: {"ok": True},
        census_world_fn=lambda: list(rows),
        combat_dump_fn=lambda _a: {"has_controller": True, "Enemy": "OakPlayer"},
        tracked_actors_fn=lambda: [object()],
        log_fn=lambda _m: None,
    )
    assert result["ok"] is True
    assert result["spawned_as"] == "Char_Mandolin_SoldierAR"
    assert result["despawned"] is False
    assert result["before_n"] == 0
    assert result["after_n"] == 1
    success = json.loads((tmp_path / "success.json").read_text(encoding="utf-8"))
    assert success[0]["spawned_as"] == "Char_Mandolin_SoldierAR"


class _FakeCls:
    def __init__(self, name: str) -> None:
        self.Name = name


class _FakePawn:
    def __init__(self, name: str, cls: str, *, addr: int = 1, defn: str = "") -> None:
        self.Name = name
        self.Class = _FakeCls(cls)
        self._addr = addr
        self._defn = defn
        self.is_player = "player" in cls.lower() or "vaulthunter" in name.lower()


def test_player_census_row_is_excluded():
    player = {
        "name": "VaultHunter_C",
        "class": "OakPlayerCharacter",
        "def": "Char_VaultHunter",
        "addr": 11,
    }
    ai = {
        "name": "Char_Mandolin_SoldierAR_C",
        "class": "OakCharacter",
        "def": "Char_Mandolin_SoldierAR",
        "addr": 22,
    }
    assert verify.is_player_census_row(player) is True
    assert verify.is_player_census_row(ai) is False
    assert verify.filter_non_player_rows([player, ai]) == [ai]
    clone = {
        "name": "OakCharacter_99",
        "class": "OakCharacter",
        "def": "FGbxDefPtr('Char_RoboDealer', 'GbxActorDef')",
        "addr": 33,
    }
    assert verify.is_player_census_row(clone, local_defs={"Char_RoboDealer"}) is True
    assert verify.is_player_census_row(clone) is False


def test_clone_live_player_only_does_not_clone():
    player = _FakePawn("OakCharacter_1", "OakCharacter", addr=7, defn="Char_RoboDealer")

    class FakeHybrid:
        def _iter_world_pawns(self, force: bool = False) -> list:
            return [player]

        def _matches_wanted(self, actor, name) -> bool:
            return False

        def _is_player_pawn(self, actor) -> bool:
            return actor is player

        def _obj_addr(self, actor) -> int:
            return int(getattr(actor, "_addr", 0) or 0)

        def _actor_def_name(self, actor) -> str:
            return str(getattr(actor, "_defn", "") or "")

        def _anchor_pawn(self):
            return player, "local"

        def _clone_live(self, *a, **k):
            raise AssertionError("must not clone the player pawn")

        def is_live_actor(self, actor) -> bool:
            return actor is not None

    result = verify._try_clone_live(FakeHybrid(), "Char_Mandolin_SoldierAR")
    assert result is not None
    assert result.get("ok") is False
    assert "player" in str(result.get("message") or "").lower() or "no matching live AI" in str(
        result.get("message") or ""
    )


def test_clone_live_skips_player_even_when_name_matches():
    player = _FakePawn("Char_Mandolin_SoldierAR_C", "OakPlayerCharacter", addr=3, defn="Char_Mandolin_SoldierAR")

    class FakeHybrid:
        def _iter_world_pawns(self, force: bool = False) -> list:
            return [player]

        def _matches_wanted(self, actor, name) -> bool:
            return True

        def _is_player_pawn(self, actor) -> bool:
            return True

        def _obj_addr(self, actor) -> int:
            return 3

        def _actor_def_name(self, actor) -> str:
            return "Char_Mandolin_SoldierAR"

        def _anchor_pawn(self):
            return player, "local"

        def _clone_live(self, *a, **k):
            raise AssertionError("must not clone a player even on name match")

        def is_live_actor(self, actor) -> bool:
            return True

    result = verify._try_clone_live(FakeHybrid(), "Char_Mandolin_SoldierAR")
    assert result.get("ok") is False


def test_world_delta_player_pawn_is_not_success(tmp_path: Path):
    rows: list[dict] = []

    def spawn(name: str, count: int = 1) -> dict:
        rows.append(
            {
                "name": "VaultHunter_C",
                "class": "OakPlayerCharacter",
                "def": "Char_VaultHunter",
                "addr": 77,
                "xyz": [1.0, 2.0, 3.0],
            }
        )
        return {
            "ok": True,
            "mode": "asd_hybrid_clone",
            "verification_status": "verified_spawned",
            "spawn_verified": True,
            "spawned_count": 1,
            "alive_count": 1,
            "source_path": "clone:any-live",
            "spawned_as": "VaultHunter_C",
        }

    result = verify.process_one(
        tmp_path,
        _tiny_catalog(),
        spawn_fn=spawn,
        despawn_fn=lambda: {"ok": True},
        census_world_fn=lambda: list(rows),
        log_fn=lambda _m: None,
    )
    assert result["ok"] is False
    assert result["new_actors"] == []
    assert result["despawned"] is True
    assert "player" in result["message"].lower()
    fail = json.loads((tmp_path / "fail.json").read_text(encoding="utf-8"))
    assert fail[0]["name"] == "Char_ArmyBandit_SHARED"


def test_census_world_pawns_skips_player():
    player = _FakePawn("FunkYouShiFT", "OakPlayerCharacter", addr=1, defn="Char_RoboDealer")
    ai = _FakePawn("Char_Mandolin_SoldierAR_C", "OakCharacter", addr=2, defn="Char_Mandolin_SoldierAR")

    class FakeHybrid:
        def _iter_world_pawns(self, force: bool = False) -> list:
            return [player, ai]

        def _is_player_pawn(self, actor) -> bool:
            return actor is player

        def _obj_addr(self, actor) -> int:
            return int(getattr(actor, "_addr", 0) or 0)

        def _actor_def_name(self, actor) -> str:
            return str(getattr(actor, "_defn", "") or "")

        def _actor_location(self, actor):
            return None

        def _anchor_pawn(self):
            return player, "local"

        def is_live_actor(self, actor) -> bool:
            return True

    rows = verify.census_world_pawns(hybrid=FakeHybrid())
    assert len(rows) == 1
    assert rows[0]["def"] == "Char_Mandolin_SoldierAR"


def test_start_and_abort_sweep_player_clones(tmp_path: Path):
    verify.abort(despawn=False)
    cleaned: list[str] = []

    def despawn() -> dict:
        cleaned.append("despawn")
        return {"ok": True, "message": "cleared"}

    armed = verify.start(
        tmp_path,
        names=["Char_One"],
        spawn_fn=lambda name, count=1: {"ok": False, "verification_status": "no_pawn"},
        despawn_fn=despawn,
        census_world_fn=lambda: [],
        attach_camera=False,
        log_fn=lambda _m: None,
    )
    assert armed["ok"] is True
    assert "despawn" in cleaned
    verify.abort()
    assert cleaned.count("despawn") >= 2
