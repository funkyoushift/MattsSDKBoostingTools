"""Numbered mission picker inside the SDK console mod menu."""

from types import SimpleNamespace

from console_mod_menu.draw import draw
from console_mod_menu.screens import (
    AbstractScreen,
    draw_stack_header,
    draw_standard_commands,
    handle_standard_command_input,
    pop_screen,
    push_screen,
    quit_interactive_menu,
    screen_stack,
)

from . import console

PAGE_SIZE = 10
_fog = "leave"
_bookmarks = []


def _enabled():
    from . import mod

    if not mod.is_enabled:
        console.log("Enable BL4 Mission Selector first.")
        return False
    return True


def _run(operation, **values):
    if not _enabled():
        return
    args = dict(
        operation=operation,
        campaign="story",
        mission="",
        objective=1,
        name="",
        id="",
        value="off",
        fog=_fog,
        yes=True,
    )
    args.update(values)
    console.run(SimpleNamespace(**args))
    quit_interactive_menu()


class Page(AbstractScreen):
    def __init__(self, name, entries, description=""):
        super().__init__(name)
        self.entries = entries
        self.description = description
        self.page = 0

    def rows(self):
        return self.entries() if callable(self.entries) else self.entries

    def draw(self):
        draw_stack_header()
        if self.description:
            draw(self.description)
        rows = self.rows()
        self.page = min(self.page, max(0, (len(rows) - 1) // PAGE_SIZE))
        start = self.page * PAGE_SIZE
        for number, (label, _) in enumerate(rows[start : start + PAGE_SIZE], start + 1):
            if callable(label):
                label = label()
            draw(f"[{number}] {label}")
        if not rows:
            draw("No bookmarks yet. Save one while playing a mission.")
        if len(rows) > PAGE_SIZE:
            draw(f"Page {self.page + 1} of {(len(rows) + PAGE_SIZE - 1) // PAGE_SIZE}")
            if start + PAGE_SIZE < len(rows):
                draw("[N] Next page")
            if self.page:
                draw("[P] Previous page")
        draw_standard_commands()

    def handle_input(self, line):
        if handle_standard_command_input(line):
            return True
        rows = self.rows()
        if line.lower() == "n" and (self.page + 1) * PAGE_SIZE < len(rows):
            self.page += 1
            return True
        if line.lower() == "p" and self.page:
            self.page -= 1
            return True
        try:
            index = int(line) - 1
        except ValueError:
            return False
        start = self.page * PAGE_SIZE
        if not start <= index < min(start + PAGE_SIZE, len(rows)):
            return False
        rows[index][1]()
        return True


def _confirm(label, callback, description, action_label="Start replay"):
    push_screen(Page(label, [(action_label, callback)], description))


def _objectives(campaign, name, row):
    entries = []
    for number, (_, title) in enumerate(console.objective_rows(name, row), 1):

        def select(number=number, title=title):
            _confirm(
                title,
                lambda: _run("play", campaign=campaign, mission=name, objective=number),
                f"{row['title']} / {title}. Keeps gear and levels; rewinds later "
                "mission progress. A backup is saved first. Close the console after starting.",
            )

        entries.append((title, select))
    push_screen(Page(row["title"], entries, "Choose where to begin replay."))


def _missions(campaign, label):
    rows = console.campaign_rows(campaign)
    entries = [
        (row["title"], lambda name=name, row=row: _objectives(campaign, name, row))
        for name, row in rows
    ]
    push_screen(
        Page(label, entries, "Choose a mission. Missions are in playthrough order.")
    )


class BookmarkNameScreen(AbstractScreen):
    def __init__(self):
        super().__init__("Save bookmark")

    def draw(self):
        draw_stack_header()
        draw("Enter a name for this mission-state bookmark (1–80 characters).")
        draw_standard_commands()

    def handle_input(self, line):
        if handle_standard_command_input(line):
            return True
        if not 1 <= len(line.strip()) <= 80:
            return False
        _run("bookmark", name=line.strip())
        return True


class BookmarkPage(Page):
    def __init__(self):
        super().__init__(
            "Load bookmark", self.bookmark_rows, "Loading bookmarks… [R] Refresh"
        )

    def bookmark_rows(self):
        entries = []
        for bookmark in _bookmarks:
            label = bookmark["name"] + " — " + bookmark.get("mission", "Mission")
            label += " (exact position)" if bookmark.get("exactLocation") else " (spawn station)"

            def select(bookmark=bookmark, label=label):
                _confirm(
                    label,
                    lambda: _run("load-bookmark", id=bookmark["id"]),
                    "Restore the captured mission state and saved location, keeping current gear and levels. "
                    "A backup is saved first. Close the console after starting.",
                )

            entries.append((label, select))
        return entries

    def handle_input(self, line):
        if line.lower() == "r":
            console.submit("bookmark_list", {})
            return True
        return super().handle_input(line)


def on_worker_result(result):
    global _bookmarks
    if "bookmarks" not in result:
        return
    _bookmarks = result["bookmarks"]
    if screen_stack and isinstance(screen_stack[-1], BookmarkPage):
        screen = screen_stack[-1]
        screen.description = "Choose a bookmark. [R] Refresh"
        screen.draw()


def _load_bookmarks():
    if not _enabled():
        return
    console.submit("bookmark_list", {})
    push_screen(BookmarkPage())


def _bookmark_menu():
    push_screen(
        Page(
            "Bookmarks",
            [
                (
                    "Save current mission state",
                    lambda: push_screen(BookmarkNameScreen()),
                ),
                ("Load a bookmark", _load_bookmarks),
            ],
        )
    )


def _dialogue_menu():
    push_screen(
        Page(
            "Dialogue skip",
            [
                ("On", lambda: _run("dialogue", value="on")),
                ("Off", lambda: _run("dialogue", value="off")),
            ],
            "Resets when the game restarts. Some timed scenes still have to finish.",
        )
    )


def _set_fog(value):
    global _fog
    _fog = value
    pop_screen()


def _fog_menu():
    push_screen(
        Page(
            "Fog on replay",
            [
                ("Leave unchanged (default)", lambda: _set_fog("leave")),
                ("Clear all fog", lambda: _set_fog("clear")),
                ("Restore all fog", lambda: _set_fog("restore")),
            ],
            "Applies to mission replay and bookmark loading in this session.",
        )
    )


def open_menu():
    if not _enabled():
        return
    entries = [
        (label, lambda campaign=campaign, label=label: _missions(campaign, label))
        for campaign, label in [
            ("story", "Main story"),
            ("fl4k", "FL4K and the Last Resort"),
            ("ellie", "Ellie"),
            ("moxxi", "Moxxi"),
        ]
    ]
    entries.extend(
        [
            ("Bookmarks", _bookmark_menu),
            ("Dialogue skip", _dialogue_menu),
            (lambda: "Fog on replay (" + _fog + ")", _fog_menu),
            ("Replay status", lambda: _run("status")),
            ("Stop replay setup", lambda: _run("stop")),
            (
                "Restore pre-replay backup",
                lambda: _confirm(
                    "Restore backup",
                    lambda: _run("restore"),
                    "Load a different character before restoring. This replaces the original "
                    "character's whole save with its pre-replay backup, including gear and levels.",
                    action_label="Restore backup",
                ),
            ),
        ]
    )
    push_screen(
        Page(
            "Mission replay",
            entries,
            "Choose a campaign or tool. Solo play; second saved character required.",
        )
    )
