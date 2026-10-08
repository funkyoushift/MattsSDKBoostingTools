"""Borderlands 4 Modding Tools SDK entry point; original project by Mattmab."""

from __future__ import annotations

__version__: str = "2.32.0"
__version_info__: tuple[int, int, int] = (2, 32, 0)

from mods_base import CoopSupport, Game, build_mod

from .golden_chest_keybinds import CLOSE_GOLDEN_CHEST_KEY, OPEN_GOLDEN_CHEST_KEY
from .instant_click_holds import ICH_KEYBINDS
from .third_person_camera import TPC_KEYBINDS
from .player_economy import _cmd_givecurrency, _cmd_giveexperience
from .serial_rewards import _cmd_give_serial
from .runtime_cleanup import clear_travel_caches as _clear_travel_caches
from .guaranteed_drops import clear_runtime_state as _clear_drop_rate
from .inventory_capacity import start_auto_inventory_worker
from .external_bridge import start_bridge
from .external_app_launcher import _cmd_msbt_external_app
from .backend_actions import (
    _cmd_msbt_complete_challenges,
    _cmd_msbt_complete_challenges_cancel,
    _cmd_msbt_fog,
    _cmd_msbt_probe_challenge_apis,
    challenge_api_probe_enabled,
)
from .quick_menu import (
    _cmd_msbt_quick_menu,
    _cmd_msbt_quick_menu_lock,
    _cmd_msbt_quick_menu_pin,
    _cmd_msbt_quick_menu_repeat,
    _cmd_msbt_quick_menu_unstuck,
    quick_menu_toggle,
    quick_menu_unstuck_key,
    start_quick_menu,
)
from .mobile_pairing import (
    _cmd_msbt_mobile_pair,
    mobile_pair_toggle,
    start_mobile_pairing,
)

start_auto_inventory_worker()
start_bridge()
start_quick_menu()
start_mobile_pairing()

_extra_commands = [
    _cmd_msbt_external_app,
    _cmd_msbt_quick_menu,
    _cmd_msbt_quick_menu_pin,
    _cmd_msbt_quick_menu_repeat,
    _cmd_msbt_quick_menu_lock,
    _cmd_msbt_quick_menu_unstuck,
    _cmd_msbt_mobile_pair,
    _cmd_msbt_complete_challenges,
    _cmd_msbt_complete_challenges_cancel,
    _cmd_msbt_fog,
    _cmd_give_serial,
    _cmd_givecurrency,
    _cmd_giveexperience,
]
if challenge_api_probe_enabled():
    _extra_commands.append(_cmd_msbt_probe_challenge_apis)

build_mod(
    name="Borderlands 4 Modding Tools — Powered by Funk",
    author="FunkYouSHiFT; original project by Mattmab (Matt)",
    description=(
        "Boosting-focused SDK mod with a native UMG Quick Menu and external bridge "
        "(no BLImGui required). "
        "Select current party players and run serial rewards, currency, experience, Max SDU, "
        "golden chest helpers, shiny drops, shiny serial reward packages, and inventory capacity tools."
    ),
    supported_games=Game.BL4,
    coop_support=CoopSupport.Unknown,
    keybinds=[
        quick_menu_toggle,
        quick_menu_unstuck_key,
        mobile_pair_toggle,
        OPEN_GOLDEN_CHEST_KEY,
        CLOSE_GOLDEN_CHEST_KEY,
        *ICH_KEYBINDS,
        *TPC_KEYBINDS,
    ],
    commands=_extra_commands,
    on_disable=_clear_drop_rate,
)

