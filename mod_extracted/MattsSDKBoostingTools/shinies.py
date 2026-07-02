"""Shiny drop and shiny reward-package helpers for Matt's SDK Boosting Tools."""

import math
from collections.abc import Sequence
from typing import Any

import unrealsdk
from mods_base import ENGINE, get_pc
from unrealsdk import logging
from unrealsdk.unreal import UObject

MAX_ITEM_LEVEL = 999999
DEFAULT_ITEM_LEVEL = 60
SPAWN_FORWARD_OFFSET = 90.0
SPAWN_HEIGHT_OFFSET = 45.0

SHINY_ITEMPOOLS: tuple[str, ...] = (
    "itempool_bor_sg_05_legendary_convergence_shiny",
    "itempool_bor_sg_05_legendary_GoldenGod_shiny",
    "itempool_bor_sg_05_legendary_GoreMaster_shiny",
    "itempool_bor_sm_05_legendary_falke_shiny",
    "itempool_bor_sm_05_legendary_hellfire_shiny",
    "itempool_bor_sm_05_legendary_Prince_shiny",
    "itempool_bor_sr_05_legendary_Stray_shiny",
    "itempool_bor_sr_05_legendary_tankbuster_shiny",
    "itempool_bor_sr_05_legendary_Vamoose_shiny",
    "itempool_dad_ar_05_legendary_Lumberjack_shiny",
    "itempool_dad_ar_05_legendary_mercredi_shiny",
    "itempool_dad_ar_05_legendary_om_shiny",
    "itempool_dad_ar_05_legendary_star_helix_shiny",
    "itempool_dad_ps_05_legendary_Rangefinder_shiny",
    "itempool_dad_ps_05_legendary_soulsurvivor_shiny",
    "itempool_dad_ps_05_legendary_Zipgun_shiny",
    "itempool_dad_sg_05_legendary_Bod_shiny",
    "itempool_dad_sg_05_legendary_HeartGun_shiny",
    "itempool_dad_sg_05_legendary_misslaser_shiny",
    "itempool_dad_sm_05_legendary_bloodstarved_shiny",
    "itempool_dad_sm_05_legendary_follower_shiny",
    "itempool_dad_sm_05_legendary_Luty_shiny",
    "itempool_jak_ar_05_legendary_BonnieClyde_shiny",
    "itempool_jak_ar_05_legendary_Rowan_shiny",
    "itempool_jak_ar_05_legendary_rowdy_shiny",
    "itempool_jak_ps_05_legendary_KingsGambit_shiny",
    "itempool_jak_ps_05_legendary_Phantom_Flame_shiny",
    "itempool_jak_ps_05_legendary_QuickDraw_shiny",
    "itempool_jak_ps_05_legendary_seventh_sense_shiny",
    "itempool_jak_ps_05_legendary_Shalashaska_shiny",
    "itempool_jak_sg_05_legendary_Hellwalker_shiny",
    "itempool_jak_sg_05_legendary_RainbowVomit_shiny",
    "itempool_jak_sg_05_legendary_Slugger_shiny",
    "itempool_jak_sg_05_legendary_TKsWave_shiny",
    "itempool_jak_sr_05_legendary_Ballista_shiny",
    "itempool_jak_sr_05_legendary_Boomslang_shiny",
    "itempool_jak_sr_05_legendary_Truck_shiny",
    "itempool_mal_sg_05_legendary_CrazedEarl_shiny",
    "itempool_mal_sg_05_legendary_fearstalker_shiny",
    "itempool_mal_sg_05_legendary_hemorrhage_shiny",
    "itempool_mal_sg_05_legendary_Kaleidosplode_shiny",
    "itempool_mal_sg_05_legendary_jailbroken_shiny",
    "itempool_mal_sg_05_legendary_kickballer_shiny",
    "itempool_mal_sg_05_legendary_mantra_shiny",
    "itempool_mal_sg_05_legendary_rainmaker_shiny",
    "itempool_mal_sg_05_legendary_reminisce_shiny",
    "itempool_mal_sg_05_legendary_roil_shiny",
    "itempool_mal_sg_05_legendary_scootshoot_shiny",
    "itempool_mal_sg_05_legendary_Sweet_Embrace_shiny",
    "itempool_mal_sg_05_legendary_Unstable_shiny",
    "itempool_mal_sm_05_legendary_flashcyclone_shiny",
    "itempool_mal_sm_05_legendary_mercury_shiny",
    "itempool_mal_sm_05_legendary_OhmIGot_shiny",
    "itempool_mal_sm_05_legendary_PlasmaCoil_shiny",
    "itempool_mal_sm_05_legendary_songbird_shiny",
    "itempool_mal_sr_05_legendary_Asher_shiny",
    "itempool_mal_sr_05_legendary_complex_root_shiny",
    "itempool_mal_sr_05_legendary_katagawa_shiny",
    "itempool_ord_ar_05_legendary_GMR_shiny",
    "itempool_ord_ar_05_legendary_Goalkeeper_shiny",
    "itempool_ord_ps_05_legendary_Bully_shiny",
    "itempool_ord_ps_05_legendary_NoisyCricket_shiny",
    "itempool_ord_ps_05_legendary_RocketReload_shiny",
    "itempool_ord_ps_05_legendary_Roulette_shiny",
    "itempool_ord_ps_05_legendary_sunspot_shiny",
    "itempool_ord_sr_05_legendary_Fisheye_shiny",
    "itempool_ord_sr_05_legendary_seamstress_shiny",
    "itempool_ord_sr_05_legendary_Symmetry_shiny",
    "itempool_ted_ar_05_legendary_Chuck_shiny",
    "itempool_ted_ar_05_legendary_DividedFocus_shiny",
    "itempool_ted_ar_05_legendary_laserdisc_shiny",
    "itempool_ted_ar_05_legendary_murder_shiny",
    "itempool_ted_ps_05_legendary_ATLien_shiny",
    "itempool_ted_ps_05_legendary_Inscriber_shiny",
    "itempool_ted_ps_05_legendary_RubysGrasp_shiny",
    "itempool_ted_ps_05_legendary_shammy_shiny",
    "itempool_ted_ps_05_legendary_Sideshow_shiny",
    "itempool_ted_sg_05_legendary_anarchy_shiny",
    "itempool_ted_sg_05_legendary_CommBD_shiny",
    "itempool_ted_sg_05_legendary_HeavyTurret_shiny",
    "itempool_tor_ar_05_legendary_Bugbear_shiny",
    "itempool_tor_ar_05_legendary_ColdShoulder_shiny",
    "itempool_tor_ar_05_legendary_Fleabag_shiny",
    "itempool_tor_ar_05_legendary_lockjaw_shiny",
    "itempool_tor_ar_05_legendary_PotatoThrower_shiny",
    "itempool_tor_PS_05_legendary_Breadth_shiny",
    "itempool_tor_ps_05_legendary_QueensRest_shiny",
    "itempool_tor_ps_05_legendary_Roach_shiny",
    "itempool_tor_sg_05_legendary_arctic_shiny",
    "itempool_tor_sg_05_legendary_Demo_shiny",
    "itempool_tor_sg_05_legendary_Doeshot_shiny",
    "itempool_tor_sg_05_legendary_LeadBalloon_shiny",
    "itempool_tor_sg_05_legendary_Linebacker_shiny",
    "itempool_vla_ar_05_legendary_bubbles_shiny",
    "itempool_vla_ar_05_legendary_DualDamage_shiny",
    "itempool_vla_ar_05_legendary_lasercutter_shiny",
    "itempool_vla_ar_05_legendary_Lucian_shiny",
    "itempool_vla_ar_05_legendary_WF_shiny",
    "itempool_vla_ar_05_legendary_WomboCombo_shiny",
    "itempool_vla_sm_05_legendary_BeeGun_shiny",
    "itempool_vla_sm_05_legendary_KaoSon_shiny",
    "itempool_vla_sm_05_legendary_Onslaught_shiny",
    "itempool_vla_sm_06_pearl_Locust_shiny",
    "itempool_vla_sr_05_legendary_CrowdSourced_shiny",
    "itempool_vla_sr_05_legendary_Finnty_shiny",
    "itempool_vla_sr_05_legendary_StopGap_shiny",
    "itempool_vla_sm_06_pearl_Locust_shiny",
    "itempool_mal_sg_05_legendary_jailbroken_shiny",
    "itempool_tor_ar_05_legendary_lockjaw_shiny",
    "itempool_ted_ps_05_legendary_shammy_shiny",
)


def _log_info(message: str) -> None:
    logging.info(f"[Matts SDK Boosting Tools | Shinies] {message}")


def _log_warning(message: str) -> None:
    logging.warning(f"[Matts SDK Boosting Tools | Shinies] {message}")


def _make_vector(x: float, y: float, z: float) -> Any:
    return unrealsdk.make_struct("Vector", X=x, Y=y, Z=z)


def _make_rotator(pitch: float, yaw: float, roll: float = 0.0) -> Any:
    return unrealsdk.make_struct("Rotator", Pitch=pitch, Yaw=yaw, Roll=roll)


def _get_world() -> UObject | None:
    viewport = getattr(ENGINE, "GameViewport", None)
    world = getattr(viewport, "World", None)
    if world is not None:
        return world

    for class_name in ("OakPlayerController", "PlayerController"):
        try:
            objects = unrealsdk.find_all(class_name, False) or []
        except Exception:
            continue
        for obj in objects:
            if obj is None:
                continue
            candidate = getattr(obj, "World", None)
            if candidate is not None:
                return candidate
            pawn = getattr(obj, "Pawn", None)
            candidate = getattr(pawn, "World", None) if pawn is not None else None
            if candidate is not None:
                return candidate
    return None


def _get_runtime_pc() -> UObject | None:
    pc = get_pc()
    if pc is not None:
        return pc

    for class_name in ("OakPlayerController", "PlayerController"):
        try:
            objects = unrealsdk.find_all(class_name, False) or []
        except Exception:
            continue
        for obj in objects:
            if obj is not None:
                return obj
    return None


def _get_spawn_transform(pc: UObject) -> Any | None:
    pawn = getattr(pc, "Pawn", None)
    if pawn is None:
        return None

    player_location = pawn.K2_GetActorLocation()
    for getter_name in ("K2_GetActorTransform", "GetActorTransform", "GetTransform"):
        getter = getattr(pawn, getter_name, None)
        if not callable(getter):
            continue
        try:
            transform = getter()
            setattr(transform, "Translation", _make_vector(player_location.X, player_location.Y, player_location.Z))
            return transform
        except Exception:
            continue
    return None


def _get_player_pose(pc: UObject) -> tuple[Any, Any] | None:
    pawn = getattr(pc, "Pawn", None)
    if pawn is None:
        return None
    return pawn.K2_GetActorLocation(), pawn.K2_GetActorRotation()


def _spawn_pose(player_location: Any, player_rotation: Any, _index: int) -> tuple[Any, Any]:
    yaw_rad = math.radians(player_rotation.Yaw)
    forward_x = math.cos(yaw_rad)
    forward_y = math.sin(yaw_rad)

    new_x = player_location.X + forward_x * SPAWN_FORWARD_OFFSET
    new_y = player_location.Y + forward_y * SPAWN_FORWARD_OFFSET
    new_z = player_location.Z + SPAWN_HEIGHT_OFFSET
    location = _make_vector(new_x, new_y, new_z)

    return location, _make_rotator(0.0, player_rotation.Yaw, 0.0)


def _get_pool_store() -> UObject:
    configs = unrealsdk.find_all("NexusConfigStoreItemPool", False)
    if not configs:
        raise RuntimeError("NexusConfigStoreItemPool not found.")
    return list(configs)[-1]


def _spawn_pool(config: UObject, world: UObject, transform: Any, level: int, pool_name: str, location: Any, rotation: Any) -> None:
    try:
        setattr(transform, "Translation", location)
        setattr(transform, "Rotation", rotation)
    except Exception:
        pass

    config.SpawnInventoryFromItemPool(world, transform, level, pool_name)


def _spawn_all_shinies(level: int, pools: Sequence[str] = SHINY_ITEMPOOLS) -> None:
    world = _get_world()
    pc = _get_runtime_pc()
    if world is None or pc is None:
        raise RuntimeError("Player or world is not available.")

    transform = _get_spawn_transform(pc)
    player_pose = _get_player_pose(pc)
    if transform is None or player_pose is None:
        raise RuntimeError("Could not derive a spawn transform.")

    config = _get_pool_store()
    player_location, player_rotation = player_pose
    spawned = 0
    failed: list[str] = []

    _log_info(f"Spawning {len(pools)} shiny itempools at level {level}.")
    for index, pool_name in enumerate(pools):
        location, rotation = _spawn_pose(player_location, player_rotation, index)
        try:
            _spawn_pool(config, world, transform, level, pool_name, location, rotation)
            spawned += 1
        except Exception as exc:
            failed.append(pool_name)
            _log_warning(f"Failed to spawn {pool_name}: {exc}")

    if failed:
        _log_warning(f"Spawned {spawned}/{len(pools)} shiny itempools. Failed: {', '.join(failed)}")
    else:
        _log_info(f"Spawned all {spawned} shiny itempools.")


def drop_all_shinies(level: int = DEFAULT_ITEM_LEVEL) -> None:
    """Spawn every embedded shiny itempool near the local player."""
    level = max(1, min(MAX_ITEM_LEVEL, int(level)))
    _spawn_all_shinies(level)
