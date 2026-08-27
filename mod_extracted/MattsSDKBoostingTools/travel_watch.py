"""Boot-safe travel gate. No feature imports.

Only PRE ClientTravel is installed at boot so feature hooks can be dropped
before the world dies. Do not add pawn/world inspection here.
"""
from __future__ import annotations

from typing import Any

from mods_base import hook
from unrealsdk.hooks import Type

from .hook_gate import disable_join_hooks
from .travel_gate import mark_travel

_PREFIX = "[Matts SDK Boosting Tools | Travel]"


def _quiet(reason: str) -> None:
    mark_travel()
    try:
        disable_join_hooks()
    except Exception:
        pass
    try:
        from unrealsdk import logging

        logging.info(f"{_PREFIX} {reason}")
    except Exception:
        pass


@hook(
    "OakGame.OakPlayerController:ClientTravel",
    Type.PRE,
    immediately_enable=True,
    hook_identifier="msbt_travel_watch_pre_oak_v1",
)
@hook(
    "Engine.PlayerController:ClientTravel",
    Type.PRE,
    immediately_enable=True,
    hook_identifier="msbt_travel_watch_pre_engine_v1",
)
def _pre_travel(*_args: Any, **_kwargs: Any) -> None:
    _quiet("hooks off (ClientTravel PRE)")
