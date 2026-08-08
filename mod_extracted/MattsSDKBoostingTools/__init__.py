"""Matt's SDK Boosting Tools — boosting-focused SDK mod."""

from __future__ import annotations

from mods_base import CoopSupport, Game, build_mod

from .golden_chest_keybinds import CLOSE_GOLDEN_CHEST_KEY, OPEN_GOLDEN_CHEST_KEY
from .player_economy import _cmd_givecurrency, _cmd_giveexperience
from .serial_rewards import _cmd_give_serial
from .inventory_capacity import start_auto_inventory_worker
from .external_bridge import start_bridge
from .external_app_launcher import _cmd_msbt_external_app
from .backend_actions import (
    _cmd_msbt_complete_challenges,
    _cmd_msbt_complete_challenges_cancel,
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

__version__: str = "2.3.3"
__version_info__: tuple[int, int, int] = (2, 3, 3)

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
            f"[Matts SDK Boosting Tools] Legacy BLImGui panel unavailable; "
            f"native Quick Menu + external bridge continue without it: {exc!r}"
        )
    except Exception:
        print(
            "[Matts SDK Boosting Tools] Legacy BLImGui panel unavailable; "
            f"native Quick Menu + external bridge continue without it: {exc!r}"
        )

start_auto_inventory_worker()
start_bridge()
start_quick_menu()

_extra_commands = [
    _cmd_msbt_external_app,
    _cmd_msbt_quick_menu,
    _cmd_msbt_quick_menu_pin,
    _cmd_msbt_quick_menu_repeat,
    _cmd_msbt_quick_menu_lock,
    _cmd_msbt_quick_menu_unstuck,
    _cmd_msbt_complete_challenges,
    _cmd_msbt_complete_challenges_cancel,
    _cmd_give_serial,
    _cmd_givecurrency,
    _cmd_giveexperience,
]
if challenge_api_probe_enabled():
    _extra_commands.append(_cmd_msbt_probe_challenge_apis)

build_mod(
    name="MattsSDKBoostingTools",
    author="Matt",
    description=(
        "Boosting-focused SDK mod with a native UMG Quick Menu and external bridge "
        "(no BLImGui required). Legacy BLImGui panel remains an optional fallback if installed. "
        "Select current party players and run serial rewards, currency, experience, Max SDU, "
        "golden chest helpers, shiny drops, shiny serial reward packages, and inventory capacity tools."
    ),
    supported_games=Game.BL4,
    coop_support=CoopSupport.Unknown,
    keybinds=_panel_keybinds + [
        quick_menu_toggle,
        quick_menu_unstuck_key,
        OPEN_GOLDEN_CHEST_KEY,
        CLOSE_GOLDEN_CHEST_KEY,
    ],
    commands=_panel_commands + _extra_commands,
)
