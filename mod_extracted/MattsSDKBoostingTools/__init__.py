"""Matt's SDK Boosting Tools — boosting-focused SDK mod."""

from __future__ import annotations

from mods_base import CoopSupport, Game, build_mod

from .golden_chest_keybinds import CLOSE_GOLDEN_CHEST_KEY, OPEN_GOLDEN_CHEST_KEY
from .player_economy import _cmd_givecurrency, _cmd_giveexperience
from .serial_rewards import _cmd_give_serial
from .inventory_capacity import start_auto_inventory_worker
from .external_bridge import start_bridge

__version__: str = "1.0"
__version_info__: tuple[int, int] = (1, 0)

_panel_keybinds = []
_panel_commands = []
try:
    from .blimgui_panel import (
        _cmd_msbt_panel,
        _cmd_msbt_hud_pill_test,
        _cmd_msbt_imgui_join_safe,
        _cmd_msbt_imgui_pause,
        matts_sdk_boosting_tools_toggle,
    )
    _panel_keybinds.append(matts_sdk_boosting_tools_toggle)
    _panel_commands.extend([
        _cmd_msbt_panel,
        _cmd_msbt_hud_pill_test,
        _cmd_msbt_imgui_join_safe,
        _cmd_msbt_imgui_pause,
    ])
except Exception as exc:
    try:
        from unrealsdk import logging
        logging.warning(
            f"[Matts SDK Boosting Tools] BLImGui panel unavailable; external bridge will still start: {exc!r}"
        )
    except Exception:
        print(f"[Matts SDK Boosting Tools] BLImGui panel unavailable; external bridge will still start: {exc!r}")

start_auto_inventory_worker()
start_bridge()

build_mod(
    name="MattsSDKBoostingTools",
    author="Matt",
    description=(
        "Boosting-focused SDK mod with a custom BLImGui panel. "
        "Select current party players and run serial rewards, currency, experience, Max SDU, "
        "golden chest helpers, shiny drops, shiny serial reward packages, and inventory capacity tools."
    ),
    supported_games=Game.BL4,
    coop_support=CoopSupport.Unknown,
    keybinds=_panel_keybinds + [
        OPEN_GOLDEN_CHEST_KEY,
        CLOSE_GOLDEN_CHEST_KEY,
    ],
    commands=_panel_commands + [
        _cmd_give_serial,
        _cmd_givecurrency,
        _cmd_giveexperience,
    ],
)
