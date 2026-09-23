"""Focused offline regressions; these do not establish guest replication."""
from __future__ import annotations

import ast
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "mod_extracted" / "MattsSDKBoostingTools"


def functions(file, names, **context):
    tree = ast.parse((ROOT / file).read_text(encoding="utf-8-sig"))
    selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(selected) == len(names)
    code = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *selected], type_ignores=[])
    exec(compile(ast.fix_missing_locations(code), file, "exec"), context)
    return context


def xp_context(ps, row, **extra):
    return functions("player_economy.py", ["_set_experience_level_via_bp"],
        experience_row_for_track=lambda rows, track: row,
        _clamp_engine_experience_level=lambda track, level: level,
        _candidate_experience_tokens=lambda track, row: ["Specialization"],
        _make_experience_def_ptr=lambda token: "fallback",
        _log=lambda *_: None, _log_err=lambda *_: None, **extra)


def test_specialization_uses_typed_definition_and_reads_back():
    native = object()
    row = types.SimpleNamespace(ExperienceId=native)
    seen = []
    ps = types.SimpleNamespace(ExperienceState=[row],
        BP_UnlockExperienceType=lambda *_: None,
        BP_SetExperienceLevel=lambda handle, level: seen.append((handle, level)),
        BP_GetExperienceLevel=lambda handle: 701 if handle == "fallback" else 0)
    ctx = xp_context(ps, row)
    assert ctx["_set_experience_level_via_bp"](ps, 1, 701)
    assert seen == [("fallback", 701)]


def test_unreadable_experience_does_not_report_verified_success():
    def unreadable(*_):
        raise RuntimeError("read unavailable")
    row = types.SimpleNamespace(ExperienceId=object())
    ps = types.SimpleNamespace(ExperienceState=[row], BP_SetExperienceLevel=lambda *_: None,
                               BP_UnlockExperienceType=lambda *_: None,
                               BP_GetExperienceLevel=unreadable)
    ctx = xp_context(ps, row)
    assert not ctx["_set_experience_level_via_bp"](ps, 1, 701)


def test_specialization_unlock_precedes_missing_track_lookup():
    calls = []
    row = types.SimpleNamespace(ExperienceId=object())
    ps = types.SimpleNamespace(ExperienceState=[])
    def unlock(handle):
        calls.append("unlock")
        ps.ExperienceState.append(row)
    ps.BP_UnlockExperienceType = unlock
    ps.BP_SetExperienceLevel = lambda *_: calls.append("set")
    ps.BP_GetExperienceLevel = lambda *_: 701
    ctx = xp_context(ps, row)
    ctx["experience_row_for_track"] = lambda rows, track: rows[0] if rows else None
    assert ctx["_set_experience_level_via_bp"](ps, 1, 701)
    assert calls == ["unlock", "set"]


def test_specialization_unlock_failure_does_not_claim_success():
    row = types.SimpleNamespace(ExperienceId=object())
    ps = types.SimpleNamespace(ExperienceState=[row])
    assert not xp_context(ps, row)["_set_experience_level_via_bp"](ps, 1, 701)



def test_reopen_cancels_older_delayed_close_and_missing_chest_fails():
    calls = []
    script = types.SimpleNamespace(Success__OnStateEnabled=lambda *_: calls.append("success"),
                                   Open__OnStateEnabled=lambda *_: calls.append("open"))
    ctx = functions("golden_chest_keybinds.py", ["_open_golden_chest"],
        _find_golden_chest_script=lambda: script, _new_state_key=lambda: object(),
        _pending_close=(123, script), _log=lambda *_: None, _log_err=lambda *_: None)
    def clear():
        ctx["_pending_close"] = None
        calls.append("cancel")
    ctx["clear_pending_closes"] = clear
    assert ctx["_open_golden_chest"]()
    assert calls == ["cancel", "success", "open"]
    assert ctx["_pending_close"] is None
    ctx["_find_golden_chest_script"] = lambda: None
    assert not ctx["_open_golden_chest"]()


def test_live_pawn_readiness_can_release_boot_gate_without_client_travel():
    clock = types.SimpleNamespace(now=100)
    ctx = {"__name__": "test_travel"}
    exec(compile((ROOT / "travel_gate.py").read_text(), "travel_gate.py", "exec"), ctx)
    ctx["time"] = types.SimpleNamespace(monotonic=lambda: clock.now)
    assert ctx["is_travel_quiet"]()
    ctx["schedule_in_world"](2)
    assert ctx["is_travel_quiet"]()  # an unconfirmed load does not release boot
    ctx["mark_pawn_ready"](2)
    assert ctx["is_travel_quiet"]()
    clock.now += 3
    assert not ctx["is_travel_quiet"]()
    ctx["mark_travel"]()
    assert ctx["is_travel_quiet"]()


def test_boot_recovery_requires_stable_possessed_pawn_and_never_bypasses_travel(monkeypatch):
    import sys
    clock = types.SimpleNamespace(now=100)
    ps = object()
    pc = types.SimpleNamespace(Name="PC", PlayerState=ps)
    pawn = types.SimpleNamespace(Name="Pawn", Controller=pc)
    pc.Pawn = pawn
    world = types.SimpleNamespace(Name="World_P", GameState=types.SimpleNamespace(PlayerArray=[ps]))
    travel = types.SimpleNamespace(travel=False)
    travel.saw_travel = lambda: travel.travel
    monkeypatch.setitem(sys.modules, "test_boot", types.SimpleNamespace(travel_gate=travel))
    monkeypatch.setitem(sys.modules, "test_boot.runtime_cleanup", types.SimpleNamespace(_looks_like_gameplay=lambda name: name == "World_P"))
    monkeypatch.setitem(sys.modules, "mods_base", types.SimpleNamespace(get_pc=lambda: pc, ENGINE=types.SimpleNamespace(GameViewport=types.SimpleNamespace(World=world))))
    calls = []
    ctx = functions("hook_gate.py", ["recover_missed_boot_ready"],
        __package__="test_boot", _ENABLED=False, _PENDING_ARM=False,
        _BOOT_READY_KEY=None, _BOOT_READY_SINCE=0, _BOOT_CHECK_AT=0,
        time=types.SimpleNamespace(monotonic=lambda: clock.now),
        request_arm_when_pawn_ready=lambda delay: calls.append(delay))
    def arm(obj):
        assert obj is pc
        ctx["_ENABLED"] = True
    ctx["try_arm_from_controller"] = arm
    def recover():
        clock.now += 0.6
        return ctx["recover_missed_boot_ready"]()
    assert not recover()
    clock.now += 1
    assert not recover()
    pawn.Controller = None
    clock.now += 2
    assert not recover()
    pawn.Controller = pc
    assert not recover()
    clock.now += 3
    world.GameState.PlayerArray = []
    assert not recover()
    world.GameState.PlayerArray = [ps]
    assert not recover()
    clock.now += 3
    travel.travel = True
    assert not recover()
    assert calls == []
    travel.travel = False
    world.Name = "MainMenu"
    assert not recover()
    world.Name = "World_P"
    assert not recover()
    clock.now += 3
    assert recover()
    assert calls == [1.0]
    assert not recover()  # already enabled; no repeated activation


def test_market_world_change_discards_old_actor_without_access():
    class OldSpawner:
        def GetAliveActors(self, *_):
            raise AssertionError('must not dereference old-world actor')
    sync = []
    ctx = functions('backend_actions.py', ['_bm_camera_tick'],
        _bm_pending_until=100, _bm_owned_spawner=OldSpawner(), _bm_spawn_world='old',
        get_pc=lambda: types.SimpleNamespace(Pawn=object()), _bm_obj_path=lambda _: 'new:Pawn',
        _bm_log=lambda _: None, _sync_bm_camera_need=lambda: sync.append(True))
    ctx['_bm_camera_tick'](None,None,None,None)
    assert ctx['_bm_owned_spawner'] is None
    assert ctx['_bm_pending_until'] == 0
    assert sync == [True]


def test_market_pending_spawn_does_not_create_duplicates():
    def create(*_):
        raise AssertionError('pending click must not create another spawner')
    ctx = functions('backend_actions.py', ['spawn_black_market'],
        _bm_pending_until=100, time=types.SimpleNamespace(monotonic=lambda: 50),
        _challenge_is_host=lambda: (True,''), _new_black_market_spawner=create)
    result = ctx['spawn_black_market']()
    assert result['pending'] is True
    assert 'loading' in result['message']
