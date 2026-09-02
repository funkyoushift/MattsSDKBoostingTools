"""Authored CoS pad proof (no game). Pad missing / player-only = fail."""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ["ASD_PAD_PROOF_SKIP"] = "1"
os.environ["ASD_SPAWN_VERIFY_SKIP"] = "1"

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
SCRIPT = TOOLS / "asd_pad_spawn_proof.py"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import asd_pad_spawn_proof as proof  # noqa: E402
import asd_spawn_verify as verify  # noqa: E402


def _row(
    uaid: str,
    *,
    alive: int | None = 0,
    spawned: int | None = 0,
    dead: int | None = 0,
    total: int | None = 24,
    mix: str = "Mix_MandolinCos_BasicRanged Char_GruntPistol",
    enabled: str = "True",
    style: str = "RespawnStyle: <ERespawnStyle.Never: 2>",
    xyz: tuple[float, float, float] = (-76525.0, -4075.0, 1850.0),
) -> dict:
    return proof.pad_row(
        uaid=uaid,
        xyz=xyz,
        counts={"alive": alive, "spawned": spawned, "dead": dead, "total": total},
        mix=mix,
        enabled=enabled,
        style=style,
    )


def test_pyexec_contract_no_pump_no_player_clone():
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'if __name__ == "__main__":' in source
    assert "else:\n    main()" in source
    assert "ResetSpawner" in source
    assert "comp.PushActorDef" not in source
    assert "PushActorDef(" not in source
    assert "clone:any-live" not in source
    assert "camera_tick.register" not in source
    assert "PUMP start" not in source
    assert "asd_spawn_verify.start" not in source
    assert "find_all(\"Object\")" not in source
    assert "LineTrace" not in source
    assert "2089963252" in source
    assert "pad_proof.txt" in source
    assert "SPAWN_OK" in source
    assert "SPAWN_FAIL" in source
    assert "penaltybox" in source.lower()
    assert "geyser" in source


def test_spent_and_pick_unused_sibling():
    known_spent = _row(
        proof._TARGET_UAID,
        alive=0,
        spawned=24,
        dead=24,
        total=24,
    )
    sibling = _row(
        "OakSpawner_UAID_025041000001E2D302_2089966253",
        alive=0,
        spawned=0,
        total=25,
        enabled="False",
        xyz=(-76625.0, -4075.0, 1850.0),
    )
    geyser = _row(
        "OakSpawner_UAID_025041000001BCD502_1612106591",
        alive=15,
        spawned=15,
        total=2147483647,
        mix="IO_AmmoGeyser",
        style="RespawnStyle: <ERespawnStyle.Timed: 0>",
        xyz=(-76525.0, -3950.0, 1050.0),
    )
    assert proof.is_spent(known_spent["counts"], known_spent["style"]) is True
    assert proof.is_spent(sibling["counts"], sibling["style"]) is False
    assert geyser["refuse"] or not geyser["combat"]
    picked = proof.pick_pad([known_spent, sibling, geyser])
    assert picked is not None
    assert picked["uaid"] == sibling["uaid"]


def test_run_proof_pad_missing():
    result = proof.run_proof(
        find_fn=lambda: [],
        census_fn=lambda: [],
        wake_fn=lambda _row: (_ for _ in ()).throw(AssertionError("must not wake")),
        filter_fn=lambda rows: rows,
        delta_fn=verify.world_delta,
        log_fn=lambda _m: None,
    )
    assert result["ok"] is False
    assert result["reason"] == "pad missing"
    assert result["verdict"].startswith("SPAWN_FAIL")


def test_run_proof_player_only_census_is_fail():
    player = {
        "name": "VaultHunter_C",
        "class": "OakPlayerCharacter",
        "def": "Char_RoboDealer",
        "addr": 11,
        "xyz": [1.0, 2.0, 3.0],
    }
    pad = _row(proof._TARGET_UAID, alive=0, spawned=0, total=24)
    woken: list[str] = []

    def census() -> list[dict]:
        return [player]

    result = proof.run_proof(
        find_fn=lambda: [pad],
        census_fn=census,
        wake_fn=lambda row: woken.append(row["uaid"]) or "ResetSpawner(True)",
        filter_fn=lambda rows: verify.filter_non_player_rows(rows),
        delta_fn=verify.world_delta,
        log_fn=lambda _m: None,
    )
    assert woken == [proof._TARGET_UAID]
    assert result["ok"] is False
    assert result["reason"] == "only player"
    assert result["new_actors"] == []
    assert "SPAWN_FAIL" in result["verdict"]


def test_run_proof_new_mandolin_is_ok():
    rows: list[dict] = []
    pad = _row(proof._TARGET_UAID, alive=0, spawned=0, total=24)

    def census() -> list[dict]:
        return list(rows)

    def wake(_row: dict) -> str:
        rows.append(
            {
                "name": "Char_Mandolin_SoldierAR_C",
                "class": "OakCharacter",
                "def": "Char_Mandolin_SoldierAR",
                "addr": 99,
                "xyz": [-76525.0, -4075.0, 1850.0],
            }
        )
        return "SetSpawnerEnabled,ResetSpawner(True)"

    result = proof.run_proof(
        find_fn=lambda: [pad],
        census_fn=census,
        wake_fn=wake,
        filter_fn=lambda items: verify.filter_non_player_rows(items),
        delta_fn=verify.world_delta,
        log_fn=lambda _m: None,
    )
    assert result["ok"] is True
    assert result["verdict"].startswith("SPAWN_OK")
    assert result["new_actors"][0]["def"] == "Char_Mandolin_SoldierAR"
    assert result["clone_done"] is False
