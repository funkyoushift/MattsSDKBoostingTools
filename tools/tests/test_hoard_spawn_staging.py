"""Hoard wave staging / pacing logic without the game.

Covers the regression that made waves silently blow through (arming on an
unverified ASD acceptance), the reentrancy guards around the single ASD spawn
call, and the new multi-node round-robin placement.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "mod_extracted" / "MattsSDKBoostingTools"


def _load_hoard_runner(*, get_pc=None):
    unrealsdk = types.ModuleType("unrealsdk")
    unrealsdk.logging = types.SimpleNamespace(
        info=lambda *_a, **_k: None,
        warning=lambda *_a, **_k: None,
        error=lambda *_a, **_k: None,
    )
    sys.modules["unrealsdk"] = unrealsdk

    mods_base = types.ModuleType("mods_base")
    mods_base.hook = lambda *args, **kwargs: (lambda func: func)
    if get_pc is not None:
        mods_base.get_pc = get_pc
    sys.modules["mods_base"] = mods_base

    package = types.ModuleType("MattsSDKBoostingTools")
    package.__path__ = [str(PKG)]
    sys.modules["MattsSDKBoostingTools"] = package

    spawn_helpers = types.ModuleType("MattsSDKBoostingTools.spawn_helpers")
    spawn_helpers.apply_aggro_to_tracked = lambda: None
    spawn_helpers.get_aggro_mode = lambda: "passive"
    spawn_helpers.note_spawned_actors = lambda _actors: None
    spawn_helpers.set_aggro_mode = lambda _mode: None
    sys.modules["MattsSDKBoostingTools.spawn_helpers"] = spawn_helpers

    asd_hybrid = types.ModuleType("MattsSDKBoostingTools.asd_hybrid")
    asd_hybrid.count_alive = lambda **_k: 0
    asd_hybrid.census_live = lambda **_k: {
        "ok": True,
        "alive": 0,
        "spawners": 0,
        "actors": [],
        "actor_names": [],
        "message": "census stub",
    }
    asd_hybrid.despawn_tracked = lambda **_k: {
        "ok": True,
        "despawned": 0,
        "spawners_destroyed": 0,
        "message": "stub",
    }
    asd_hybrid.clear_world = lambda **_k: {
        "ok": True,
        "despawned": 0,
        "spawners_sealed": 0,
        "alive_count": 0,
        "message": "stub",
    }
    asd_hybrid.note_after_asd_spawn = lambda *_a, **_k: {
        "ok": True,
        "noted": 0,
        "alive": 0,
        "actor_names": [],
        "message": "stub",
    }
    sys.modules["MattsSDKBoostingTools.asd_hybrid"] = asd_hybrid

    sys.modules.pop("MattsSDKBoostingTools.hoard_runner", None)
    spec = importlib.util.spec_from_file_location(
        "MattsSDKBoostingTools.hoard_runner", PKG / "hoard_runner.py"
    )
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "MattsSDKBoostingTools"
    sys.modules["MattsSDKBoostingTools.hoard_runner"] = module
    spec.loader.exec_module(module)
    module._rng.seed(1234)
    return module


def _tick_later(hoard):
    """Tick as if a later frame, past the per-frame gate and the death quiet period.

    Production leans on both gates to keep hoard work away from the frame a wave
    died in. Tests drive ticks back to back, so anything that is not specifically
    testing a gate opens them first.
    """
    hoard._last_tick_at = 0.0
    hoard._last_death_at = 0.0
    hoard.tick()


def _install_fake_backend(hoard, results):
    """Feed _spawn_next_job canned ASD results and record the calls."""
    calls: list[dict] = []
    backend = types.ModuleType("MattsSDKBoostingTools.backend_actions")

    def _spawn(**kwargs):
        calls.append(dict(kwargs))
        return results[min(len(calls) - 1, len(results) - 1)]

    backend._run_actor_script_deployer_spawnai_like_debug_menu = _spawn
    backend._asd_note_spawn_for_autoclear = lambda: None
    backend.run_dev_spawner_action = lambda *_a, **_k: {"ok": True, "message": "cleared"}
    sys.modules["MattsSDKBoostingTools.backend_actions"] = backend
    return calls


@pytest.fixture()
def hoard():
    return _load_hoard_runner()


def test_wave_total_is_no_longer_capped_at_eight(hoard):
    result = hoard.set_plan(
        {"waves": [{"entries": [{"actor_id": "Char_A", "count": 40}, {"actor_id": "Char_B", "count": 15}]}]}
    )
    assert result["ok"], result
    wave = result["waves"][0]
    assert wave["count"] == 55
    assert [e["count"] for e in wave["entries"]] == [40, 15]
    assert result["limits"]["max_wave_total"] == 60


def test_more_than_four_types_per_wave_allowed(hoard):
    entries = [{"actor_id": f"Char_{i}", "count": 2} for i in range(9)]
    result = hoard.set_plan({"waves": [{"entries": entries}]})
    assert result["ok"], result
    assert len(result["waves"][0]["entries"]) == 9


def test_waves_are_effectively_unlimited(hoard):
    waves = [{"entries": [{"actor_id": "Char_A", "count": 1}]} for _ in range(200)]
    result = hoard.set_plan({"waves": waves})
    assert result["ok"], result
    assert result["wave_total"] == 200


def test_loot_cleanup_defaults_off_for_legacy_plans(hoard):
    result = hoard.set_plan({"waves": [{"actor_id": "Char_A", "count": 3}]})
    assert result["waves"][0]["cleanup_loot"] is False


def test_spawn_nodes_are_spread_but_not_a_perfect_ring(hoard):
    nodes = hoard.build_spawn_nodes({"spawn_points": 6, "distance": 900.0})
    assert len(nodes) == 6
    angles = sorted(node["angle"] for node in nodes)
    # Every 60-degree sector is represented...
    assert all(
        int(angle // 60) == index for index, angle in enumerate(angles)
    ), angles
    # ...but neither the angles nor the distances are evenly spaced.
    gaps = [round(angles[i + 1] - angles[i], 2) for i in range(len(angles) - 1)]
    assert len(set(gaps)) > 1, gaps
    assert len({node["distance"] for node in nodes}) > 1


def test_jobs_round_robin_across_nodes_and_types(hoard):
    wave = {"spawn_points": 4, "burst": 2, "distance": 350.0, "spacing": 125.0}
    entries = [{"actor_id": "Char_A", "count": 6}, {"actor_id": "Char_B", "count": 6}]
    nodes = hoard.build_spawn_nodes(wave)
    jobs = hoard.build_spawn_jobs(wave, entries, nodes)

    assert sum(job["count"] for job in jobs) == 12
    # Types alternate so a wave mixes instead of finishing one enemy first.
    assert [job["actor_id"] for job in jobs[:4]] == ["Char_A", "Char_B", "Char_A", "Char_B"]
    # Nodes are visited in order and reused only after every node had a turn.
    assert [job["node"] for job in jobs[:8]] == [0, 1, 2, 3, 0, 1, 2, 3]
    # Bursts alternate 2 then 1 so arrivals do not look mechanical.
    assert [job["count"] for job in jobs[:4]] == [2, 2, 1, 1]
    assert {job["distance"] for job in jobs} == {node["distance"] for node in nodes}


def test_burst_sizes_never_overshoot_the_requested_count(hoard):
    for total in range(1, 20):
        for burst in range(1, 5):
            sizes = hoard._burst_sizes(total, burst)
            assert sum(sizes) == total
            assert all(1 <= size <= burst for size in sizes)


def test_unverified_asd_acceptance_does_not_arm_the_wave(hoard):
    _install_fake_backend(
        hoard,
        [{"ok": True, "verification_status": "queued_unverified"}],
    )
    hoard.set_plan({"waves": [{"entries": [{"actor_id": "Char_A", "count": 2}], "spawn_points": 2}]})
    assert hoard.start()["ok"]
    while hoard._pending_spawn_jobs:
        hoard._spawn_next_at = 0.0
        _tick_later(hoard)
    assert hoard._wave_seen_alive is False
    assert hoard._running is True


def test_verified_spawn_arms_the_wave(hoard):
    _install_fake_backend(
        hoard,
        [{"ok": True, "verification_status": "verified_spawned", "spawn_verified": True}],
    )
    hoard.set_plan({"waves": [{"entries": [{"actor_id": "Char_A", "count": 2}], "spawn_points": 2}]})
    assert hoard.start()["ok"]
    hoard._spawn_next_at = 0.0
    _tick_later(hoard)
    assert hoard._wave_seen_alive is True


def test_only_one_spawn_call_runs_per_step(hoard):
    calls = _install_fake_backend(hoard, [{"ok": True, "verification_status": "queued_unverified"}])
    hoard.set_plan({"waves": [{"entries": [{"actor_id": "Char_A", "count": 6}], "spawn_points": 3}]})
    hoard.start()
    hoard._spawn_next_at = 0.0
    _tick_later(hoard)
    assert len(calls) == 1
    # The step clock was pushed forward, so a later tick is still a no-op.
    _tick_later(hoard)
    assert len(calls) == 1


def test_in_flight_guard_blocks_reentrant_spawns(hoard):
    calls = _install_fake_backend(hoard, [{"ok": True, "verification_status": "queued_unverified"}])
    hoard.set_plan({"waves": [{"entries": [{"actor_id": "Char_A", "count": 4}], "spawn_points": 2}]})
    hoard.start()
    hoard._spawn_in_flight = True
    hoard._spawn_next_at = 0.0
    _tick_later(hoard)
    assert calls == []
    hoard._spawn_in_flight = False
    _tick_later(hoard)
    assert len(calls) == 1


def test_reentrant_spawn_during_asd_call_is_ignored(hoard):
    """A spawn that pumps the engine must not recursively spawn again."""
    calls: list[str] = []
    backend = types.ModuleType("MattsSDKBoostingTools.backend_actions")

    def _spawn(**kwargs):
        calls.append(str(kwargs["name"]))
        # Simulate the engine re-entering the bridge tick mid-spawn. The per-frame
        # gate is opened so this exercises the reentrancy flag, not the gate.
        hoard._spawn_next_at = 0.0
        _tick_later(hoard)
        return {"ok": True, "verification_status": "queued_unverified"}

    backend._run_actor_script_deployer_spawnai_like_debug_menu = _spawn
    backend._asd_note_spawn_for_autoclear = lambda: None
    sys.modules["MattsSDKBoostingTools.backend_actions"] = backend

    hoard.set_plan({"waves": [{"entries": [{"actor_id": "Char_A", "count": 4}], "spawn_points": 2}]})
    hoard.start()
    hoard._spawn_next_at = 0.0
    _tick_later(hoard)
    assert len(calls) == 1


def test_spawn_distance_defaults_far_enough_from_the_player(hoard):
    result = hoard.set_plan({"waves": [{"actor_id": "Char_A", "count": 2}]})
    assert result["waves"][0]["distance"] == 900.0
    # Legacy plans that stored the old melee-range distance get pushed out too.
    close = hoard.set_plan({"waves": [{"actor_id": "Char_A", "count": 2, "distance": 350}]})
    assert close["waves"][0]["distance"] == 600.0


def test_node_jitter_never_lands_inside_the_player(hoard):
    for _ in range(200):
        nodes = hoard.build_spawn_nodes({"spawn_points": 8, "distance": 600.0})
        assert min(node["distance"] for node in nodes) >= 600.0


def test_emergency_clear_defers_the_destructive_pass(hoard):
    calls = []
    backend = types.ModuleType("MattsSDKBoostingTools.backend_actions")
    backend.run_dev_spawner_action = lambda action, _payload=None: (
        calls.append(action) or {"ok": True, "message": "cleared"}
    )
    sys.modules["MattsSDKBoostingTools.backend_actions"] = backend

    result = hoard.clear({})
    assert result["ok"]
    # Nothing destructive in the frame the button was pressed.
    assert calls == []
    assert hoard.cleanup_pending() is True

    hoard._pending_cleanup_at = 0.001
    _tick_later(hoard)
    assert calls == ["dev_spawner_clear"]
    assert hoard.cleanup_pending() is False


def test_emergency_clear_never_fires_the_physics_loot_hide(hoard):
    loot_calls = []
    backend = types.ModuleType("MattsSDKBoostingTools.backend_actions")
    backend.run_dev_spawner_action = lambda *_a, **_k: {"ok": True, "message": "cleared"}
    sys.modules["MattsSDKBoostingTools.backend_actions"] = backend
    movement = types.ModuleType("MattsSDKBoostingTools.movement_adjustments")
    movement.hide_ground_loot = lambda: loot_calls.append("hide") or "hid loot"
    sys.modules["MattsSDKBoostingTools.movement_adjustments"] = movement

    hoard.clear({"cleanup_loot": True})
    hoard._pending_cleanup_at = 0.001
    _tick_later(hoard)
    assert loot_calls == []


def test_deferred_cleanup_waits_for_an_in_flight_spawn(hoard):
    calls = []
    backend = types.ModuleType("MattsSDKBoostingTools.backend_actions")
    backend.run_dev_spawner_action = lambda action, _payload=None: (
        calls.append(action) or {"ok": True, "message": "cleared"}
    )
    sys.modules["MattsSDKBoostingTools.backend_actions"] = backend

    hoard.clear({})
    hoard._pending_cleanup_at = 0.001
    hoard._spawn_in_flight = True
    _tick_later(hoard)
    assert calls == []
    hoard._spawn_in_flight = False
    hoard._pending_cleanup_at = 0.001
    _tick_later(hoard)
    assert calls == ["dev_spawner_clear"]


class FakeComponent:
    def __init__(self):
        self.enabled = True
        self.reset_calls = 0

    def SetSpawnerEnabled(self, value):
        self.enabled = bool(value)

    def SetSpawnPointEnabled(self, value):
        self.enabled = bool(value)

    def SetActive(self, value):
        self.enabled = bool(value)

    def ResetSpawner(self, *_args):
        self.reset_calls += 1

    def GetNumAliveActors(self, *_args):
        return 0


class FakeSpawner:
    def __init__(self):
        self.component = FakeComponent()
        self.destroyed = False
        self.component_reads = 0

    def GetSpawnerComponent(self):
        self.component_reads += 1
        return self.component

    def K2_DestroyActor(self):
        self.destroyed = True


def _run_to_wave_clear(hoard, spawner):
    """Start a one-wave plan, arm it, then let the wave read as cleared."""
    _install_fake_backend(hoard, [{"ok": True, "spawn_verified": True}])
    hoard.set_plan({"waves": [{"entries": [{"actor_id": "Char_A", "count": 1}], "spawn_points": 1}]})
    hoard.start()
    hoard._spawn_next_at = 0.0
    _tick_later(hoard)

    hoard._wave_spawners = [spawner]
    hoard._spawn_grace_until = 0.0
    hoard._wave_seen_alive = True
    _tick_later(hoard)


def test_wave_transition_never_writes_to_a_spawner_in_the_death_frame(hoard):
    """The clearing frame is a Kill All frame; it must not touch the world."""
    spawner = FakeSpawner()
    _run_to_wave_clear(hoard, spawner)

    # Still enabled: the disable was queued, not run alongside the deaths.
    assert spawner.component.enabled is True
    assert spawner.destroyed is False
    assert hoard.cleanup_pending() is True


def test_deferred_cleanup_disables_the_spawner_and_never_destroys_it(hoard):
    """Three crashes in a row came from destroying spawners. We only disable now."""
    spawner = FakeSpawner()
    _run_to_wave_clear(hoard, spawner)

    hoard._pending_cleanup_at = 0.001
    _tick_later(hoard)

    assert spawner.component.enabled is False
    assert spawner.destroyed is False
    assert spawner.component.reset_calls == 0
    assert hoard.cleanup_pending() is False


def test_deferred_cleanup_waits_out_the_post_death_quiet_period(hoard):
    spawner = FakeSpawner()
    _run_to_wave_clear(hoard, spawner)

    # A wave died this instant, so the pass holds off even though it is due.
    hoard._pending_cleanup_at = 0.001
    hoard._last_death_at = hoard.time.monotonic()
    hoard._last_tick_at = 0.0
    hoard.tick()
    assert spawner.component.enabled is True
    assert hoard.cleanup_pending() is True

    hoard._pending_cleanup_at = 0.001
    _tick_later(hoard)
    assert spawner.component.enabled is False


def test_hoard_runner_never_calls_k2_destroyactor():
    """A source-level guard: no destruction may creep back into this module."""
    source = (PKG / "hoard_runner.py").read_text(encoding="utf-8")
    code = "\n".join(
        line for line in source.splitlines() if not line.lstrip().startswith("#")
    )
    assert "K2_DestroyActor" not in code
    assert "_disable_and_destroy_spawner" not in code


def test_tick_collapses_repeat_fires_within_one_frame(hoard):
    """BP_TickWidget fires once per widget, so a frame can call tick() many times."""
    calls = _install_fake_backend(hoard, [{"ok": True, "verification_status": "queued_unverified"}])
    hoard.set_plan({"waves": [{"entries": [{"actor_id": "Char_A", "count": 6}], "spawn_points": 3}]})
    hoard.start()

    for _ in range(20):
        hoard._spawn_next_at = 0.0
        hoard.tick()
    assert len(calls) == 1


def test_next_wave_does_not_spawn_in_the_frame_the_previous_wave_died(hoard):
    calls = _install_fake_backend(hoard, [{"ok": True, "spawn_verified": True}])
    hoard.set_plan(
        {
            "waves": [
                {"entries": [{"actor_id": "Char_A", "count": 1}], "spawn_points": 1},
                {"entries": [{"actor_id": "Char_B", "count": 1}], "spawn_points": 1},
            ]
        }
    )
    hoard.start()
    hoard._spawn_next_at = 0.0
    _tick_later(hoard)
    assert [call["name"] for call in calls] == ["Char_A"]

    hoard._wave_spawners = [FakeSpawner()]
    hoard._spawn_grace_until = 0.0
    hoard._wave_seen_alive = True
    _tick_later(hoard)

    # Wave 2 is staged, but its first burst is held until the corpses settle.
    assert hoard._wave_index == 1
    assert hoard._spawn_phase is True
    assert hoard._spawn_next_at >= hoard._last_death_at + hoard._DEATH_QUIET_S
    hoard._last_tick_at = 0.0
    hoard.tick()
    assert [call["name"] for call in calls] == ["Char_A"]


def test_spawn_bursts_no_longer_request_a_bearing(hoard):
    """Angled placement needed a monkeypatch on ActorScriptDeployer; it is gone."""
    calls = _install_fake_backend(hoard, [{"ok": True, "spawn_verified": True}])
    hoard.set_plan({"waves": [{"entries": [{"actor_id": "Char_A", "count": 1}], "spawn_points": 3}]})
    hoard.start()
    hoard._spawn_next_at = 0.0
    _tick_later(hoard)

    assert calls
    assert "angle_degrees" not in calls[0]


def test_spawns_are_held_while_the_world_is_not_ready():
    hoard = _load_hoard_runner(get_pc=lambda: None)
    calls = _install_fake_backend(hoard, [{"ok": True, "verification_status": "verified_spawned"}])
    hoard.set_plan({"waves": [{"entries": [{"actor_id": "Char_A", "count": 2}], "spawn_points": 2}]})
    hoard.start()
    hoard._spawn_next_at = 0.0
    _tick_later(hoard)
    assert calls == []
    assert hoard._running is True
    assert hoard._pending_spawn_jobs


def test_count_alive_uses_hybrid_census(hoard):
    sys.modules["MattsSDKBoostingTools.asd_hybrid"].count_alive = lambda **_k: 4
    hoard._expected_count = 4
    hoard._spawn_grace_until = 0.0
    assert hoard.count_alive() == 4
    assert hoard._wave_seen_alive is True
    assert hoard._last_alive == 4


def test_hybrid_census_keeps_the_wave_from_advancing(hoard):
    """Leftover live pawns must not look like a cleared wave."""
    sys.modules["MattsSDKBoostingTools.asd_hybrid"].count_alive = lambda **_k: 2
    _install_fake_backend(hoard, [{"ok": True, "spawn_verified": True}])
    hoard.set_plan({"waves": [{"entries": [{"actor_id": "Char_A", "count": 1}], "spawn_points": 1}]})
    hoard.start()
    hoard._spawn_next_at = 0.0
    _tick_later(hoard)
    hoard._spawn_grace_until = 0.0
    hoard._wave_seen_alive = True
    _tick_later(hoard)
    assert hoard._running is True
    assert hoard._complete is False
    assert hoard.cleanup_pending() is False


def test_hoard_count_alive_does_not_peek_spawner_components():
    source = (PKG / "hoard_runner.py").read_text(encoding="utf-8")
    body = source.split("def count_alive", 1)[1].split("def _disable_wave_spawners", 1)[0]
    assert "asd_hybrid" in body
    assert "GetNumAliveActors" not in body
    assert "_count_spawner_alive" not in source or "def _count_spawner_alive" not in source


def _fake_spawner(name: str, x: float, y: float, z: float, *, reset_calls=None):
    loc = types.SimpleNamespace(X=x, Y=y, Z=z)
    calls = reset_calls if reset_calls is not None else []

    class _Spawner:
        Name = name

        def K2_GetActorLocation(self):
            return loc

        def ResetSpawner(self, *_a, **_k):
            calls.append("reset")

        def GetSpawnerComponent(self):
            return types.SimpleNamespace(
                ResetSpawner=lambda *_a, **_k: calls.append("comp_reset"),
                SetSpawnerEnabled=lambda *_a, **_k: calls.append("enable"),
            )

        def __str__(self):
            return name

    return _Spawner()


def test_harvest_reads_location_and_skips_protected(hoard):
    reset_calls = []
    spawners = [
        _fake_spawner("OakSpawner_Combat_A", -192800.0, 308500.0, 5816.0, reset_calls=reset_calls),
        _fake_spawner("OakSpawner_Combat_B", -192200.0, 309000.0, 5820.0, reset_calls=reset_calls),
        _fake_spawner("OakSpawner_Combat_C", -193400.0, 307900.0, 5800.0, reset_calls=reset_calls),
        _fake_spawner("OakSpawner_Combat_D", -191900.0, 308100.0, 5790.0, reset_calls=reset_calls),
        _fake_spawner("OakSpawner_TravelStation", -192000.0, 308000.0, 5810.0, reset_calls=reset_calls),
        _fake_spawner("Default__OakSpawner", 0.0, 0.0, 0.0, reset_calls=reset_calls),
        _fake_spawner("OakSpawner_Mission_Boss", -190000.0, 310000.0, 6000.0, reset_calls=reset_calls),
    ]
    result = hoard.harvest({"spawners": spawners})
    assert result["ok"], result
    assert 4 <= result["harvested_count"] <= 8
    names_ok = all("travel" not in str(p) and "mission" not in str(p) for p in result["harvested_points"])
    assert names_ok
    assert reset_calls == []
    source = (PKG / "hoard_runner.py").read_text(encoding="utf-8")
    harvest_body = source.split("def harvest(", 1)[1].split("def _local_pawn", 1)[0]
    assert "ResetSpawner" not in harvest_body
    assert "SetSpawnerEnabled" not in harvest_body


def test_harvest_mocked_points_become_spawn_xyz(hoard):
    hoard.set_plan(
        {
            "arena_station": "here",
            "harvested_points": [
                {"x": -192799.5, "y": 308498.4, "z": 5816.5},
                {"x": -192200.0, "y": 309000.0, "z": 5820.0},
                {"x": -193400.0, "y": 307900.0, "z": 5800.0},
                {"x": -191900.0, "y": 308100.0, "z": 5790.0},
            ],
            "waves": [{"entries": [{"actor_id": "Char_A", "count": 4}], "spawn_points": 6}],
        }
    )
    nodes = hoard.build_spawn_nodes(hoard._plan[0])
    assert len(nodes) == 4
    assert all(node.get("world_xyz") for node in nodes)
    jobs = hoard.build_spawn_jobs(hoard._plan[0], hoard._plan[0]["entries"], nodes)
    assert jobs
    assert jobs[0]["world_xyz"] == (-192799.5, 308498.4, 5816.5)
    calls = _install_fake_backend(hoard, [{"ok": True, "spawn_verified": True}])
    assert hoard.start()["ok"]
    hoard._spawn_next_at = 0.0
    _tick_later(hoard)
    assert calls
    assert calls[0]["world_xyz"] == (-192799.5, 308498.4, 5816.5)


def test_set_plan_keeps_abandoned_post_station(hoard):
    result = hoard.set_plan(
        {
            "arena_station": "abandoned_post",
            "waves": [{"entries": [{"actor_id": "Char_A", "count": 1}]}],
        }
    )
    assert result["ok"]
    assert result["arena_station"] == "World_P.FT_GRA_BeachTower"
