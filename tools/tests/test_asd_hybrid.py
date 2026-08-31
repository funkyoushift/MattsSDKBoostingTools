"""ASD hybrid: live OakCharacter clone, not OakSpawner queues (no game)."""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "mod_extracted" / "MattsSDKBoostingTools"


def _text(name: str) -> str:
    return (SDK / name).read_text(encoding="utf-8")


def test_hybrid_module_does_not_use_the_old_queue_path():
    source = _text("asd_hybrid.py")
    assert "BeginDeferredActorSpawnFromClass" in source
    assert "FinishSpawningActor" in source
    assert "find_live_sources" in source
    assert "def spawn_live(" in source
    assert "def despawn_tracked(" in source
    assert "def hide_tracked(" in source
    assert "def arm_combat(" in source
    assert "def set_hostile_to(" in source
    assert "def force_attack_me(" in source
    assert "StartCombat" in source
    assert "SetHostile" in source
    assert "SetEnemy" in source
    assert "attack_me" in source
    assert "K2_DestroyActor" in source
    assert "OakCharacter" in source
    assert "def resolve_spawn_class(" in source
    assert "def guess_load_packages(" in source
    assert "def _spawn_from_actor_def(" in source
    assert "PushActorDef" in source
    assert "GetAliveActors" in source
    assert "_make_actor_def_shell" not in source
    assert "queued_unverified" not in source
    assert "ASD_spawnai" not in source
    assert "blimgui" not in source
    assert "blimgui_panel" not in source


def test_backend_spawnai_calls_hybrid_not_asd_console():
    backend = _text("backend_actions.py")
    start = backend.index("def _run_actor_script_deployer_spawnai_like_debug_menu")
    body = backend[start : backend.index("\ndef _module_available")]
    assert "_asd_hybrid.spawn_live" in body
    assert "_cmd_spawnai" not in body
    assert "import_module(\"ActorScriptDeployer\")" not in body
    assert "from . import asd_hybrid as _asd_hybrid" in backend
    assert "_asd_hybrid.despawn_tracked" in backend
    assert '_apply_aggro_to_tracked(mode="attack_me")' in backend
    assert "extra_loads=tuple(extra_loads or ())" in body
    hoard = _text("hoard_runner.py")
    assert "_run_actor_script_deployer_spawnai_like_debug_menu" in hoard
    assert "_cmd_spawnai" not in hoard


def test_bridge_and_quick_menu_keep_existing_spawnai_action():
    bridge = _text("external_bridge.py")
    registry = _text("quick_menu_registry.py")
    assert "blimgui_panel" not in bridge
    assert "import blimgui" not in bridge
    assert '"dev_spawner_spawnai"' in registry
    assert '"dev_spawner_clear"' in registry


def _load_hybrid():
    unrealsdk = types.ModuleType("unrealsdk")
    unrealsdk.logging = types.SimpleNamespace(
        info=lambda *_a, **_k: None,
        warning=lambda *_a, **_k: None,
        error=lambda *_a, **_k: None,
    )
    unrealsdk.find_all = lambda *_a, **_k: []
    unrealsdk.find_class = lambda *_a, **_k: None
    unrealsdk.find_object = lambda *_a, **_k: None
    unrealsdk.load_package = lambda *_a, **_k: None
    unrealsdk.make_struct = lambda _name, **fields: types.SimpleNamespace(**fields)
    unreal = types.ModuleType("unrealsdk.unreal")

    class _FGbxDefPtr:
        def __init__(self, name, struct=None, type=None):
            self._experimental_name = name
            self._experimental_instance = None
            self.ref = struct
            self.type = type

    unreal.FGbxDefPtr = _FGbxDefPtr
    unrealsdk.unreal = unreal
    sys.modules["unrealsdk.unreal"] = unreal
    sys.modules["unrealsdk"] = unrealsdk

    mods_base = types.ModuleType("mods_base")
    mods_base.ENGINE = None
    mods_base.get_pc = lambda: None
    sys.modules["mods_base"] = mods_base

    pkg = types.ModuleType("MattsSDKBoostingTools")
    pkg.__path__ = [str(SDK)]
    sys.modules["MattsSDKBoostingTools"] = pkg

    helpers = types.ModuleType("MattsSDKBoostingTools.spawn_helpers")
    helpers.note_spawned_actors = lambda *_a, **_k: None
    helpers.clear_tracked = lambda: None
    helpers.apply_aggro_to_tracked = lambda **_k: "Attack-me aggro: ok=1 miss=0 mobs=1."
    helpers._try_set_enemy = lambda *_a, **_k: True
    sys.modules["MattsSDKBoostingTools.spawn_helpers"] = helpers

    sys.modules.pop("MattsSDKBoostingTools.asd_hybrid", None)
    spec = importlib.util.spec_from_file_location(
        "MattsSDKBoostingTools.asd_hybrid", SDK / "asd_hybrid.py"
    )
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "MattsSDKBoostingTools"
    sys.modules["MattsSDKBoostingTools.asd_hybrid"] = module
    spec.loader.exec_module(module)
    return module


def test_name_matching_normalizes_catalog_and_live_defs():
    hybrid = _load_hybrid()
    assert hybrid.normalize_actor_key("Char_CrazyEarl_Boss") == "crazyearl_boss"
    assert hybrid.normalize_actor_key("/Game/AI/NPC/Char_NPC_Hermes.Char_NPC_Hermes_C") == "hermes"
    assert hybrid.keys_match("Char_Mancubus", "Char_Mancubus_Base")
    assert hybrid.keys_match("mancubus", "Char_Mancubus")
    assert not hybrid.keys_match("ai", "Char_Mancubus")
    assert not hybrid.keys_match("Char_Hermes", "Char_Lilith")


def test_spawn_live_without_world_is_honest_failure():
    hybrid = _load_hybrid()
    result = hybrid.spawn_live("Char_Mancubus", count=1)
    assert result["ok"] is False
    assert result["hybrid"] is True
    assert result["verification_status"] == "no_world"
    assert result["spawn_verified"] is False


def test_guess_load_packages_is_name_generic():
    hybrid = _load_hybrid()
    source = _text("asd_hybrid.py")
    assert 'if "prisonbuddy"' not in source.lower()
    assert 'if "arjay"' not in source.lower()

    arjay = hybrid.guess_load_packages("Char_PrisonBuddyBoss_Shared")
    hermes = hybrid.guess_load_packages("Char_NPC_Hermes")
    mancubus = hybrid.guess_load_packages("Char_Mancubus")
    vendor = hybrid.guess_load_packages("IO_VendingMachine_BlackMarket")
    hover = hybrid.guess_load_packages("Char_Psycho_HovercartRider")

    assert "/Game/AI/NPC/_Unique/PrisonBuddy/_Design/Character/Char_PrisonBuddyBoss_Shared" in arjay
    assert "/Game/Enemies/_Unique/PrisonBuddy/_Design/Character/Char_PrisonBuddyBoss_Shared" in arjay
    assert "/Game/AI/NPC/_Unique/Hermes/_Design/Character/Char_NPC_Hermes" in hermes
    assert "/Game/Enemies/_Unique/Mancubus/_Design/Character/Char_Mancubus" in mancubus
    assert any("InteractiveObjects" in path and "VendingMachine" in path for path in vendor)
    assert any("Hovercart" in path or "HovercartRider" in path for path in hover)

    hinted = hybrid.guess_load_packages(
        "Char_TestDummy",
        extra_loads=("/Game/Custom/FromPayload/Char_TestDummy",),
        hints={
            "parent_actor": "Char_Enemy",
            "display_key": "Name_TestDummy_Stage1",
            "package": "/Game/CatalogRow/TestDummy/Char_TestDummy",
        },
    )
    assert "/Game/Custom/FromPayload/Char_TestDummy" in hinted
    assert "/Game/CatalogRow/TestDummy/Char_TestDummy" in hinted
    assert any("TestDummy" in path for path in hinted)


def test_resolve_spawn_class_is_name_generic():
    hybrid = _load_hybrid()
    classes: dict[str, object] = {}

    def fake_find_class(name):
        key = str(name)
        if key.endswith("_C"):
            key = key[:-2]
        if key in ("Char_Mancubus", "Char_NPC_Hermes", "IO_VendingMachine_BlackMarket"):
            cls = types.SimpleNamespace(Name=f"{key}_C")
            classes[key] = cls
            return cls
        return None

    sys.modules["unrealsdk"].find_class = fake_find_class
    for wanted in ("Char_Mancubus", "Char_NPC_Hermes", "IO_VendingMachine_BlackMarket"):
        cls, how = hybrid.resolve_spawn_class(wanted)
        assert cls is classes[wanted]
        assert how.startswith("find_class")
        assert "queued_unverified" not in how

    hinted_cls = types.SimpleNamespace(Name="Char_Hinted_C")

    def fake_hint_class(name):
        if str(name) in ("Char_Hinted", "Char_Hinted_C"):
            return hinted_cls
        return None

    sys.modules["unrealsdk"].find_class = fake_hint_class
    cls, how = hybrid.resolve_spawn_class(
        "Display Only",
        hints={"class": "Char_Hinted_C"},
    )
    assert cls is hinted_cls
    assert "Char_Hinted" in how


def test_resolve_spawn_class_uses_native_gbx_def_ptr():
    hybrid = _load_hybrid()
    spawn_cls = types.SimpleNamespace(Name="Char_Mancubus_C")
    cooked = "/Game/Enemies/_Unique/Mancubus/_Design/Character/Char_Mancubus.Char_Mancubus"

    class _Inst:
        def __str__(self):
            return f"GbxActorDef'{cooked}'"

        GeneratedClass = spawn_cls

    class _Ptr:
        def __init__(self, name, struct=None, type=None):
            self._experimental_name = name
            self._experimental_instance = _Inst() if "Mancubus" in str(name) else None

    sys.modules["unrealsdk.unreal"].FGbxDefPtr = _Ptr
    cls, how = hybrid.resolve_spawn_class("Char_Mancubus")
    assert cls is spawn_cls
    assert "native" in how
    assert "queued_unverified" not in how

    path_cls = types.SimpleNamespace(Name="Char_NPC_Hermes_C")
    hermes_path = "/Game/AI/NPC/_Unique/Hermes/Char_NPC_Hermes.Char_NPC_Hermes"

    class _PathInst:
        def __str__(self):
            return f"GbxActorDef'{hermes_path}'"

    class _PathPtr:
        def __init__(self, name, struct=None, type=None):
            self._experimental_name = name
            self._experimental_instance = _PathInst() if "Hermes" in str(name) else None

    loaded: list[str] = []

    def fake_find_class(name):
        if loaded and str(name) in ("Char_NPC_Hermes", "Char_NPC_Hermes_C"):
            return path_cls
        return None

    def fake_load(package, *a, **k):
        loaded.append(package)
        return True

    sys.modules["unrealsdk.unreal"].FGbxDefPtr = _PathPtr
    sys.modules["unrealsdk"].find_class = fake_find_class
    sys.modules["unrealsdk"].load_package = fake_load
    cls, how = hybrid.resolve_spawn_class("Char_NPC_Hermes")
    assert cls is path_cls
    assert "native path" in how
    assert any("Hermes" in path for path in loaded)


def test_arjay_is_combat_not_friendly():
    hybrid = _load_hybrid()
    assert hybrid.is_clearly_friendly("Char_NPC_PrisonBuddy") is False
    assert hybrid.is_clearly_friendly("Char_PrisonBuddyBoss_Shared") is False
    assert hybrid.is_clearly_friendly("Arjay") is False
    assert hybrid.is_clearly_friendly("Char_NPC_Hermes") is False
    assert hybrid.is_clearly_friendly("IO_VendingMachine_BlackMarket") is True
    assert hybrid.is_clearly_friendly("lostloot") is True
    assert hybrid.is_clearly_friendly("Char_TargetDummy") is False


def test_set_hostile_to_fires_combat_and_attack_me():
    hybrid = _load_hybrid()
    calls: list[str] = []

    class _Ctrl:
        def SetEnemy(self, target):
            calls.append("set_enemy")

        def StartCombat(self, target):
            calls.append("start_combat")

        def SetHostile(self, value):
            calls.append(f"set_hostile={value}")

    clone = types.SimpleNamespace(Name="OakCharacter_Clone", Controller=_Ctrl(), CombatComponent=None)
    player = types.SimpleNamespace(Name="OakCharacter_Player")
    hits = hybrid.set_hostile_to(clone, player)
    assert "SetEnemy" in hits
    assert "StartCombat" in hits
    assert "SetHostile" in hits
    assert "attack_me" in hits
    assert "set_enemy" in calls
    assert "start_combat" in calls


def test_arm_combat_possesses_and_sets_enemy():
    hybrid = _load_hybrid()
    calls: list[str] = []

    class _Ctrl:
        Class = object()

        def Possess(self, pawn):
            calls.append("possess")
            self.Pawn = pawn

        def SetEnemy(self, target):
            calls.append("set_enemy")
            self.Enemy = target

    class _Pawn:
        def __init__(self, name: str):
            self.Name = name
            self.Class = object()
            self.Controller = None
            self.AIControllerClass = _Ctrl
            self.Team = "enemy"

        def SpawnDefaultController(self):
            calls.append("spawn_default")
            self.Controller = _Ctrl()

    source = _Pawn("OakCharacter_Source")
    source.Controller = _Ctrl()
    clone = _Pawn("OakCharacter_Clone")
    player = _Pawn("OakCharacter_Player")
    hits = hybrid.arm_combat(clone, source, player, None, None, None, wanted="Char_PrisonBuddyBoss_Shared")
    assert "SpawnDefaultController" in hits
    assert "hostile" in hits
    assert "spawn_default" in calls
    assert "set_enemy" in calls
    assert "friendly_skip_hostility" not in hits


def test_despawn_tracked_is_safe_when_empty():
    hybrid = _load_hybrid()
    result = hybrid.despawn_tracked()
    assert result["ok"] is True
    assert result["despawned"] == 0
    assert result["hybrid"] is True


def test_spawn_live_clones_through_gameplay_statics():
    hybrid = _load_hybrid()
    calls: list[str] = []

    class _Def:
        _experimental_name = "Char_Mancubus"

    class _Data:
        GbxActorDef = _Def()

    class _Actor:
        def __init__(self, name: str, addr: int):
            self.Name = name
            self.Class = object()
            self.GbxActorData = _Data()
            self._addr = addr

        def _get_address(self):
            return self._addr

        def K2_GetActorLocation(self):
            return types.SimpleNamespace(X=10.0, Y=20.0, Z=30.0)

        def GetActorForwardVector(self):
            return types.SimpleNamespace(X=1.0, Y=0.0, Z=0.0)

        def K2_GetActorRotation(self):
            return object()

        def K2_TeleportTo(self, _dest, _rot):
            calls.append("place")
            return True

        def SetActorHiddenInGame(self, hidden):
            calls.append(f"hidden={hidden}")

        def SetActorEnableCollision(self, enabled):
            calls.append(f"collide={enabled}")

        def SetActorTickEnabled(self, enabled):
            calls.append(f"tick={enabled}")

        def K2_DestroyActor(self):
            calls.append("destroy")

        def SpawnDefaultController(self):
            calls.append("spawn_default")
            self.Controller = types.SimpleNamespace(
                SetEnemy=lambda _t: calls.append("set_enemy"),
                Possess=lambda _p: calls.append("possess"),
            )

    source = _Actor("OakCharacter_Source", 0x300000)
    clone = _Actor("OakCharacter_Clone", 0x300100)
    player = _Actor("OakCharacter_Player", 0x400000)

    class _GS:
        def BeginDeferredActorSpawnFromClass(self, *_a, **_k):
            calls.append("begin")
            return clone

        def FinishSpawningActor(self, *_a, **_k):
            calls.append("finish")
            return clone

    hybrid.find_live_sources = lambda _name: [source]
    hybrid._anchor_pawn = lambda: (player, "local")
    hybrid._world_from_pc = lambda _pc: object()
    hybrid._gameplay_statics = lambda: _GS()

    helpers = types.ModuleType("MattsSDKBoostingTools.spawn_helpers")
    helpers.note_spawned_actors = lambda _actors: calls.append("noted")
    helpers.clear_tracked = lambda: None
    helpers.apply_aggro_to_tracked = lambda **_k: calls.append("attack_me") or "Attack-me aggro: ok=1 miss=0 mobs=1."
    helpers._try_set_enemy = lambda *_a, **_k: True
    sys.modules["MattsSDKBoostingTools.spawn_helpers"] = helpers

    result = hybrid.spawn_live("Char_Mancubus", count=1, distance=200.0)
    assert result["ok"] is True
    assert result["verification_status"] == "verified_spawned"
    assert result["spawn_verified"] is True
    assert result["spawned_count"] == 1
    assert "begin" in calls and "finish" in calls
    assert "place" in calls
    assert "hidden=False" in calls
    assert "spawn_default" in calls
    assert "set_enemy" in calls
    assert "noted" in calls
    assert "attack_me" in calls
    assert "hostile" in result.get("combat") or []

    cleared = hybrid.despawn_tracked()
    assert cleared["despawned"] == 1
    assert "destroy" in calls


def test_spawn_live_thin_air_from_resolved_class():
    hybrid = _load_hybrid()
    calls: list[str] = []

    class _Actor:
        def __init__(self, name: str, addr: int):
            self.Name = name
            self.Class = object()
            self._addr = addr
            self.GbxActorData = None

        def _get_address(self):
            return self._addr

        def K2_GetActorLocation(self):
            return types.SimpleNamespace(X=10.0, Y=20.0, Z=30.0)

        def GetActorForwardVector(self):
            return types.SimpleNamespace(X=1.0, Y=0.0, Z=0.0)

        def K2_GetActorRotation(self):
            return object()

        def K2_TeleportTo(self, _dest, _rot):
            calls.append("place")
            return True

        def SetActorHiddenInGame(self, hidden):
            calls.append(f"hidden={hidden}")

        def SetActorEnableCollision(self, enabled):
            calls.append(f"collide={enabled}")

        def SetActorTickEnabled(self, enabled):
            calls.append(f"tick={enabled}")

        def SpawnDefaultController(self):
            calls.append("spawn_default")
            self.Controller = types.SimpleNamespace(
                SetEnemy=lambda _t: calls.append("set_enemy"),
                Possess=lambda _p: calls.append("possess"),
            )

    spawn_cls = types.SimpleNamespace(Name="Char_PrisonBuddyBoss_Shared_C", ClassDefaultObject=None)
    clone = _Actor("OakCharacter_Arjay", 0x300100)
    player = _Actor("OakCharacter_Player", 0x400000)

    class _GS:
        def BeginDeferredActorSpawnFromClass(self, _world, cls, *_a, **_k):
            calls.append("begin")
            assert cls is spawn_cls
            return clone

        def FinishSpawningActor(self, *_a, **_k):
            calls.append("finish")
            return clone

    hybrid.find_live_sources = lambda _name: []
    hybrid.resolve_spawn_class = lambda _name, extra_loads=(), hints=None: (
        spawn_cls,
        f"find_class {_name}",
    )
    hybrid._anchor_pawn = lambda: (player, "local")
    hybrid._world_from_pc = lambda _pc: object()
    hybrid._gameplay_statics = lambda: _GS()

    helpers = types.ModuleType("MattsSDKBoostingTools.spawn_helpers")
    helpers.note_spawned_actors = lambda _actors: calls.append("noted")
    helpers.clear_tracked = lambda: None
    helpers.apply_aggro_to_tracked = lambda **_k: calls.append("attack_me") or "Attack-me aggro: ok=1 miss=0 mobs=1."
    helpers._try_set_enemy = lambda *_a, **_k: True
    sys.modules["MattsSDKBoostingTools.spawn_helpers"] = helpers

    result = hybrid.spawn_live("Char_PrisonBuddyBoss_Shared", count=1, distance=200.0)
    assert result["ok"] is True
    assert result["verification_status"] == "verified_spawned"
    assert result["mode"] == "asd_hybrid_class"
    assert result["spawned_count"] == 1
    assert "thin-air" in result["message"]
    assert "begin" in calls and "finish" in calls
    assert "place" in calls
    assert "spawn_default" in calls
    assert "attack_me" in calls
    assert "queued_unverified" not in result["message"]


def test_spawn_live_oak_spawner_waits_for_alive_pawn():
    hybrid = _load_hybrid()
    hybrid._SPAWNER_POLL_TIMEOUT_S = 0.2
    hybrid._SPAWNER_POLL_INTERVAL_S = 0.01
    calls: list[str] = []

    class _Actor:
        def __init__(self, name: str, addr: int):
            self.Name = name
            self.Class = object()
            self._addr = addr
            self.GbxActorData = None

        def _get_address(self):
            return self._addr

        def K2_GetActorLocation(self):
            return types.SimpleNamespace(X=10.0, Y=20.0, Z=30.0)

        def GetActorForwardVector(self):
            return types.SimpleNamespace(X=1.0, Y=0.0, Z=0.0)

        def K2_GetActorRotation(self):
            return object()

        def K2_TeleportTo(self, _dest, _rot):
            calls.append("place")
            return True

        def SetActorHiddenInGame(self, hidden):
            calls.append(f"hidden={hidden}")

        def SetActorEnableCollision(self, enabled):
            calls.append(f"collide={enabled}")

        def SetActorTickEnabled(self, enabled):
            calls.append(f"tick={enabled}")

        def SpawnDefaultController(self):
            calls.append("spawn_default")
            self.Controller = types.SimpleNamespace(
                SetEnemy=lambda _t: calls.append("set_enemy"),
                Possess=lambda _p: calls.append("possess"),
            )

        def K2_DestroyActor(self):
            calls.append("destroy")

    pawn_out = _Actor("OakCharacter_Arjay", 0x500100)
    player = _Actor("OakCharacter_Player", 0x400000)
    spawner_cls = types.SimpleNamespace(Name="OakSpawner")

    class _Comp:
        def __init__(self):
            self._alive = []
            self.enabled = False

        def SetSpawnerEnabled(self, value):
            calls.append(f"enabled={value}")
            self.enabled = value

        def PushActorDef(self, tag, _def, reset):
            calls.append(f"push:{tag}:{reset}")
            self._alive = [pawn_out]

        def ResetSpawner(self, *_a, **_k):
            calls.append("reset")

        def GetAliveActors(self, *_a, **_k):
            calls.append("get_alive")
            return list(self._alive)

        def GetNumAliveActors(self, *_a, **_k):
            return len(self._alive)

    comp = _Comp()
    spawner = types.SimpleNamespace(
        Name="OakSpawner_Throwaway",
        Class=spawner_cls,
        GetSpawnerComponent=lambda: comp,
        K2_DestroyActor=lambda: calls.append("spawner_destroy"),
    )

    class _GS:
        def BeginDeferredActorSpawnFromClass(self, _world, cls, *_a, **_k):
            calls.append("begin")
            assert cls is spawner_cls
            return spawner

        def FinishSpawningActor(self, *_a, **_k):
            calls.append("finish")
            return spawner

    hybrid.find_live_sources = lambda _name: []
    hybrid.resolve_spawn_class = lambda *_a, **_k: (None, "class not loaded")
    hybrid._oak_spawner_class = lambda: spawner_cls
    hybrid._make_gbx_actor_def_ptr = lambda _name: object()
    hybrid._anchor_pawn = lambda: (player, "local")
    hybrid._world_from_pc = lambda _pc: object()
    hybrid._gameplay_statics = lambda: _GS()

    helpers = types.ModuleType("MattsSDKBoostingTools.spawn_helpers")
    helpers.note_spawned_actors = lambda _actors: calls.append("noted")
    helpers.clear_tracked = lambda: None
    helpers.apply_aggro_to_tracked = lambda **_k: calls.append("attack_me") or "Attack-me aggro: ok=1 miss=0 mobs=1."
    helpers._try_set_enemy = lambda *_a, **_k: True
    sys.modules["MattsSDKBoostingTools.spawn_helpers"] = helpers

    result = hybrid.spawn_live("Char_PrisonBuddyBoss_Shared", count=1)
    assert result["ok"] is True
    assert result["verification_status"] == "verified_spawned"
    assert result["mode"] == "asd_hybrid_spawner"
    assert result["spawn_verified"] is True
    assert "oak-spawner" in result["message"]
    assert "push:MSBT:True" in calls
    assert "get_alive" in calls
    assert "attack_me" in calls
    assert "queued_unverified" not in result["message"]


def test_spawn_live_recovers_delayed_pawn_and_attacks():
    hybrid = _load_hybrid()
    hybrid._SPAWNER_POLL_TIMEOUT_S = 0.2
    hybrid._SPAWNER_POLL_INTERVAL_S = 0.02
    calls: list[str] = []
    scans = {"n": 0}

    class _Actor:
        def __init__(self, name: str, addr: int):
            self.Name = name
            self.Class = object()
            self._addr = addr
            self.GbxActorData = None
            self.Controller = None

        def _get_address(self):
            return self._addr

        def K2_GetActorLocation(self):
            return types.SimpleNamespace(X=10.0, Y=20.0, Z=30.0)

        def GetActorForwardVector(self):
            return types.SimpleNamespace(X=1.0, Y=0.0, Z=0.0)

        def K2_GetActorRotation(self):
            return object()

        def K2_TeleportTo(self, _dest, _rot):
            calls.append("place")
            return True

        def SetActorHiddenInGame(self, hidden):
            calls.append(f"hidden={hidden}")

        def SetActorEnableCollision(self, enabled):
            calls.append(f"collide={enabled}")

        def SetActorTickEnabled(self, enabled):
            calls.append(f"tick={enabled}")

        def SpawnDefaultController(self):
            calls.append("spawn_default")
            self.Controller = types.SimpleNamespace(
                SetEnemy=lambda _t: calls.append("set_enemy"),
                Possess=lambda _p: calls.append("possess"),
            )

        def K2_DestroyActor(self):
            calls.append("destroy")

    pawn_out = _Actor("OakCharacter_Arjay", 0x500100)
    player = _Actor("OakCharacter_Player", 0x400000)
    spawner_cls = types.SimpleNamespace(Name="OakSpawner")

    class _Comp:
        def SetSpawnerEnabled(self, value):
            calls.append(f"enabled={value}")

        def SetSpawnPointEnabled(self, value):
            calls.append(f"spawn_point={value}")

        def PushActorDef(self, tag, _def, reset):
            calls.append(f"push:{tag}:{reset}")

        def ResetSpawner(self, *_a, **_k):
            calls.append("reset")

        def GetAliveActors(self, *_a, **_k):
            calls.append("get_alive")
            return []

        def GetNumAliveActors(self, *_a, **_k):
            return 0

    comp = _Comp()
    spawner = types.SimpleNamespace(
        Name="OakSpawner_Throwaway",
        Class=spawner_cls,
        GetSpawnerComponent=lambda: comp,
        K2_DestroyActor=lambda: calls.append("spawner_destroy"),
    )

    class _GS:
        def BeginDeferredActorSpawnFromClass(self, _world, cls, *_a, **_k):
            calls.append("begin")
            return spawner

        def FinishSpawningActor(self, *_a, **_k):
            calls.append("finish")
            return spawner

    def fake_live(_name):
        scans["n"] += 1
        return [] if scans["n"] < 2 else [pawn_out]

    hybrid.find_live_sources = fake_live
    hybrid.resolve_spawn_class = lambda *_a, **_k: (None, "class not loaded")
    hybrid._oak_spawner_class = lambda: spawner_cls
    hybrid._make_gbx_actor_def_ptr = lambda _name: object()
    hybrid._anchor_pawn = lambda: (player, "local")
    hybrid._world_from_pc = lambda _pc: object()
    hybrid._gameplay_statics = lambda: _GS()

    helpers = types.ModuleType("MattsSDKBoostingTools.spawn_helpers")
    helpers.note_spawned_actors = lambda _actors: calls.append("noted")
    helpers.clear_tracked = lambda: None
    helpers.apply_aggro_to_tracked = lambda **_k: calls.append("attack_me") or "Attack-me aggro: ok=1 miss=0 mobs=1."
    helpers._try_set_enemy = lambda *_a, **_k: True
    sys.modules["MattsSDKBoostingTools.spawn_helpers"] = helpers

    result = hybrid.spawn_live("Char_PrisonBuddyBoss_Shared", count=1)
    assert result["ok"] is True
    assert result["verification_status"] == "verified_spawned"
    assert result["spawn_verified"] is True
    assert "attack_me" in calls
    assert "friendly_skip_hostility" not in result.get("combat", [])
    assert "queued_unverified" not in result["message"]

