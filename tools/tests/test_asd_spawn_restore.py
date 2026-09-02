"""Default spawn is original ASD_spawnai. Hybrid is world census/clear only."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "mod_extracted" / "MattsSDKBoostingTools"
PROBE = ROOT / "tools" / "asd_spawn_restore_probe.py"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_probe_uses_asd_then_census():
    source = _text(PROBE)
    assert "else:" in source
    assert "main()" in source
    assert "_cmd_spawnai" in source
    assert "hybrid spawn engine" in source
    assert "Char_PrisonBuddyBoss_Shared" in source
    assert 'find_all("Object")' not in source
    assert "find_all('Object')" not in source
    assert "time.sleep" not in source
    assert "Never clone" in source or "Does not clone" in source


def test_backend_default_spawn_is_asd_not_hybrid_engine():
    backend = _text(SDK / "backend_actions.py")
    start = backend.index("def _run_actor_script_deployer_spawnai_like_debug_menu")
    body = backend[start : backend.index("\ndef _module_available")]
    assert "_cmd_spawnai" in body
    assert "_parse_asd_spawnai_result" in body
    assert "note_after_asd_spawn" in body
    assert "if use_hybrid:" in body
    hybrid_only = body[body.index("if use_hybrid:") : body.index("try:")]
    assert "_asd_hybrid.spawn_live" in hybrid_only
    assert "_asd_hybrid.spawn_live" not in body[body.index("try:") :]
    assert "clear_world" in backend
    assert "_clear_spawned_actors_hybrid(payload)" in backend


def test_hoard_runner_does_not_opt_into_hybrid_spawn():
    hoard = _text(SDK / "hoard_runner.py")
    start = hoard.index("_run_actor_script_deployer_spawnai_like_debug_menu(")
    body = hoard[start : hoard.index("def ", start + 1)]
    assert "use_hybrid" not in body
    assert "dev_ai_hybrid" not in body


def test_dev_spawner_spawnai_hybrid_is_payload_opt_in():
    backend = _text(SDK / "backend_actions.py")
    start = backend.index('if action == "dev_spawner_spawnai":')
    body = backend[start : backend.index("elif action ==", start + 1)]
    assert "use_hybrid=_dev_spawner_bool" in body
    assert "dev_ai_hybrid" in body


def test_parse_queued_unverified_is_ok():
    backend = _text(SDK / "backend_actions.py")
    start = backend.index("def _parse_asd_spawnai_result")
    end = backend.index("\ndef _parse_payload_world_xyz")
    ns: dict[str, Any] = {"re": re, "Any": Any}
    exec(backend[start:end], ns)
    parse = ns["_parse_asd_spawnai_result"]
    queued = parse(
        name="Char_PrisonBuddyBoss_Shared",
        requested_count=1,
        mode="test",
        logs=[
            (
                "info",
                "ASD_spawnai thin-air actor_def=Char_PrisonBuddyBoss_Shared resolved=False "
                "poll=nonblocking spawner=OakSpawner_1 loc=(0,0,0) "
                "counts=(alive=0, spawned=0, dead=0, total=0) actors=[]",
            )
        ],
    )
    assert queued["ok"] is True
    assert queued["verification_status"] == "queued_unverified"
    assert queued.get("hybrid") is not True
