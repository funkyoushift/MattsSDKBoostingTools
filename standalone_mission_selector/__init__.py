"""Mission replay commands for the BL4 SDK console."""

from mods_base import ButtonOption, CoopSupport, Game, build_mod, command
from . import console


@command(
    "mission_select",
    description="Standalone mission/objective replay. Run mission_select help.",
)
def mission_select(args):
    console.run(args)


mission_select.add_argument(
    "operation",
    nargs="?",
    default="help",
    choices=(
        "help",
        "list",
        "objectives",
        "play",
        "status",
        "stop",
        "restore",
        "bookmark",
        "bookmarks",
        "load-bookmark",
        "dialogue",
    ),
)
mission_select.add_argument("--campaign", default="story")
mission_select.add_argument("--mission", default="")
mission_select.add_argument("--objective", type=int, default=1)
mission_select.add_argument("--name", default="")
mission_select.add_argument("--id", default="")
mission_select.add_argument("--value", choices=("on", "off"), default="off")
mission_select.add_argument(
    "--fog", choices=("leave", "clear", "restore"), default="leave"
)
mission_select.add_argument("--yes", action="store_true")


def open_selector(_option):
    from .menu import open_menu

    open_menu()


mod = build_mod(
    name="BL4 Mission Selector",
    author="FunkYouSHiFT; MSBT foundation by Mattmab",
    version="2.39.7",
    supported_games=Game.BL4,
    coop_support=CoopSupport.Unknown,
    description="Open Mission replay below to choose a campaign, mission and objective. Experimental; solo play with a second saved character required.",
    options=[
        ButtonOption(
            "mission_replay_menu",
            display_name="Mission replay",
            description="Press 1 to open the mission picker. No commands needed.",
            on_press=open_selector,
        )
    ],
    commands=[mission_select],
    on_disable=console.disable,
)
