"""Keep the replay mission on the HUD when the player crosses into another map."""

import struct
import time
from dataclasses import dataclass

_selection = None
_next_at = 0.0


@dataclass
class Selection:
    mission: str
    guid: str
    world: int
    released: bool = False
    settle_until: float = 0.0

    def update(self, guid, world, active, tracked, restore, now):
        if self.released:
            return
        if guid != self.guid or not active:
            self.released = True
            return
        if world == self.world:
            # Respect a deliberate mission change during ordinary gameplay.
            if not tracked and now >= self.settle_until:
                self.released = True
            return
        self.world = world
        self.settle_until = now + 5.0
        if not tracked:
            # One request per arrival. Never repeat a call whose result is unknown.
            try:
                restore()
            except Exception:
                self.released = True
                raise


def clear():
    global _selection
    _selection = None


def arm(mission):
    global _selection
    from .core.mission_save_replay import _host, _world_address

    _, _, guid, _ = _host()
    _selection = Selection(mission, guid, _world_address())


def tick():
    global _next_at
    if _selection is None or _selection.released or time.monotonic() < _next_at:
        return
    now = time.monotonic()
    _next_at = now + 1.0
    from . import console
    from .core import mission_progression as missions
    from .core.mission_save_replay import _host, _world_address

    if console._main_mod_active():
        clear()
        return
    try:
        pc, engine, guid, _ = _host()
        if int(pc.TravelStatus.status) != 0:
            return
        world = _world_address()
        snapshot = engine.snapshot()
        row = missions._row(snapshot, _selection.mission)
    except (RuntimeError, ValueError):
        return  # No action while the pawn/world/mission is still loading.

    def restore():
        import unrealsdk

        token = unrealsdk.make_struct(
            "/Script/CoreUObject.SToken",
            Hash=struct.unpack("<i", bytes.fromhex(row["token"])[:4])[0],
            Name=_selection.mission,
        )
        if engine.read(token._get_address(), 12).hex() != row["token"]:
            raise RuntimeError("Replay tracking identity differs")
        pc.ServerRequestTrackMission(token, int(pc.PlayerState.StableIndex))
        console.log("Restored the replay mission on the HUD after map travel.")

    try:
        _selection.update(
            guid,
            world,
            missions._state(row) in ("active", "accepted"),
            row["token"] in snapshot["tracked"],
            restore,
            now,
        )
    except Exception as exc:
        console.log("Could not restore the replay mission on the HUD: " + str(exc))
