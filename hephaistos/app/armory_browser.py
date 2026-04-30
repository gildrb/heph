# pylint: disable=duplicate-code
# pyright: reportMissingImports=false, reportUnknownArgumentType=false, reportUnknownMemberType=false
# pyright: reportUntypedBaseClass=false, reportGeneralTypeIssues=false
# pyright: reportUnknownVariableType=false, reportInvalidTypeArguments=false, reportInvalidTypeForm=false
# pyright: reportOptionalCall=false, reportUnknownParameterType=false
"""Inline Textual armory browser screen.

A ModalScreen that uses an OptionList for native keyboard-driven directory
navigation, following the GHUI pattern for modal list selection.  All
interaction is keyboard-first: up/down to navigate, enter to drill into
directories, c to choose the current directory, n to create a new armory,
and escape/q to cancel.

All Textual imports are guarded so the module can be imported safely in
environments where Textual is not installed.
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

try:
    from textual import events
    from textual.app import ComposeResult
    from textual.binding import Binding
    from textual.containers import Vertical
    from textual.screen import ModalScreen
    from textual.widgets import Input, OptionList, Static
except ImportError:
    events = None  # type: ignore[assignment]
    ComposeResult = None  # type: ignore[assignment,misc]
    Binding = None  # type: ignore[assignment,misc]
    Vertical = None  # type: ignore[assignment,misc]
    ModalScreen = object  # type: ignore[assignment,misc]
    Input = None  # type: ignore[assignment,misc]
    OptionList = None  # type: ignore[assignment,misc]
    Static = None  # type: ignore[assignment,misc]

from hephaistos.app.palette import ThemePalette, current_palette
from hephaistos.armory.storage import MARKER_FILE, initialize

_PARENT_LABEL = "..  (parent)"
_NEW_ARMORY_LABEL = "\u271b New armory..."
_DIR_ICON = "\U0001f4c1 "
_ARMORY_BADGE = "  \u2713 armory"


def _armory_browser_css(p: ThemePalette) -> str:
    """Generate CSS from the active theme palette."""
    bg = "transparent" if p.is_transparent else p.background
    border_color = p.stone
    text_color = p.text
    dim_color = p.dim
    ember_color = p.ember
    highlight_color = p.highlight

    return f"""
ArmoryBrowserScreen {{
    align: center middle;
}}
#armory-dialog {{
    width: 60;
    max-width: 90%;
    height: auto;
    max-height: 80%;
    padding: 1 2;
    background: {bg};
    border: round {border_color};
    color: {text_color};
}}
#armory-title {{
    text-style: bold;
    color: {ember_color};
    width: 100%;
    margin-bottom: 0;
}}
#armory-path {{
    color: {dim_color};
    width: 100%;
    margin-bottom: 1;
}}
#armory-list {{
    width: 100%;
    height: auto;
    max-height: 16;
    background: transparent;
    border: none;
    padding: 0;
    color: {text_color};
    scrollbar-size: 0 0;
}}
#armory-list > .option-list--option {{
    background: transparent;
    color: {text_color};
    padding: 0;
}}
#armory-list > .option-list--option-highlighted {{
    background: {highlight_color};
    color: {text_color};
    padding: 0;
}}
#armory-list:focus > .option-list--option-highlighted {{
    background: {highlight_color};
    color: {text_color};
    padding: 0;
}}
#armory-hint {{
    color: {dim_color};
    width: 100%;
    margin-top: 0;
}}
#armory-new-input-container {{
    height: auto;
    width: 100%;
    padding: 0 1;
    display: none;
    background: transparent;
}}
#armory-new-input-container.active {{
    display: block;
}}
#armory-new-input {{
    height: 1;
    width: 100%;
    background: {bg};
    color: {text_color};
    border: none;
}}
"""


def _list_child_dirs(path: Path) -> list[Path]:
    """Return sorted child directories, skipping hidden ones."""
    try:
        entries = sorted(path.iterdir())
    except PermissionError:
        return []
    return [e for e in entries if e.is_dir() and not e.name.startswith(".")]


def _is_armory(path: Path) -> bool:
    return (path / MARKER_FILE).exists()


class _DirEntry:
    """Lightweight wrapper pairing a display label with a Path or action."""

    __slots__ = ("is_create", "is_parent", "label", "path")

    def __init__(
        self,
        label: str,
        path: Path | None = None,
        *,
        is_parent: bool = False,
        is_create: bool = False,
    ) -> None:
        self.label = label
        self.path = path
        self.is_parent = is_parent
        self.is_create = is_create


def _build_entries(
    current: Path,
    allow_create: bool,
) -> list[_DirEntry]:
    """Build the ordered list of browser entries."""
    entries: list[_DirEntry] = [_DirEntry(_PARENT_LABEL, is_parent=True)]
    if allow_create:
        entries.append(_DirEntry(_NEW_ARMORY_LABEL, is_create=True))
    for child in _list_child_dirs(current):
        badge = _ARMORY_BADGE if _is_armory(child) else ""
        entries.append(_DirEntry(f"{_DIR_ICON}{child.name}{badge}", path=child))
    return entries


def _format_entry(entry: _DirEntry) -> str:
    """Return the display string for an OptionList option."""
    return entry.label


class ArmoryBrowserScreen(ModalScreen[Path | None]):
    """Modal directory browser for selecting or creating an armory.

    Keyboard-first interaction using an OptionList with native navigation.
    Returns the chosen *Path* when the user picks a directory, or *None*
    when cancelled.
    """

    BINDINGS: ClassVar[list[Binding]] = [  # type: ignore[assignment]
        Binding("escape", "cancel", "Cancel"),
        Binding("q", "cancel", "Cancel", show=False),
        Binding("c", "choose", "Choose"),
        Binding("n", "new_armory", "New"),
        Binding("enter", "activate", "Open", show=False),
    ]

    def __init__(
        self,
        start: Path | None = None,
        *,
        allow_create: bool = True,
    ) -> None:
        super().__init__()
        self._current = (start or Path.cwd()).resolve()
        self._allow_create = allow_create
        self._creating = False
        self._entries: list[_DirEntry] = []
        self.CSS = _armory_browser_css(current_palette())

    def compose(self) -> ComposeResult:
        p = current_palette()
        title = f"[bold {p.ember}]\u2301 Armory[/bold {p.ember}]"
        with Vertical(id="armory-dialog"):
            yield Static(title, id="armory-title", markup=True)
            yield Static("", id="armory-path")
            yield OptionList(id="armory-list")
            with Vertical(id="armory-new-input-container"):
                yield Input(
                    placeholder="Armory name...",
                    id="armory-new-input",
                )
            yield Static(
                "\u2191\u2193 navigate  enter open  c choose  n new  esc cancel",
                id="armory-hint",
            )

    def on_mount(self) -> None:
        self._refresh()
        self._focus_list()

    def _focus_list(self) -> None:
        ol = self.query_one("#armory-list", OptionList)
        ol.focus()

    def _refresh(self) -> None:
        self._entries = _build_entries(self._current, self._allow_create)
        path_widget = self.query_one("#armory-path", Static)
        path_widget.update(str(self._current))

        ol = self.query_one("#armory-list", OptionList)
        ol.clear_options()
        for entry in self._entries:
            ol.add_option(_format_entry(entry))
        if self._entries:
            ol.highlighted = 0

    def _highlighted_entry(self) -> _DirEntry | None:
        ol = self.query_one("#armory-list", OptionList)
        idx = ol.highlighted
        if idx is None or idx < 0 or idx >= len(self._entries):
            return None
        return self._entries[idx]

    def _navigate_parent(self) -> None:
        parent = self._current.parent
        if parent != self._current and parent.exists():
            self._current = parent
            self._refresh()

    def _navigate_into(self, entry: _DirEntry) -> None:
        if entry.is_parent:
            self._navigate_parent()
        elif entry.is_create:
            self._start_new_armory()
        elif entry.path is not None:
            self._current = entry.path
            self._refresh()

    def action_activate(self) -> None:
        """Enter key: drill into directory or activate special entry."""
        if self._creating:
            return
        entry = self._highlighted_entry()
        if entry is not None:
            self._navigate_into(entry)

    def action_choose(self) -> None:
        """c key: choose the current directory as the armory."""
        if self._creating:
            return
        self.dismiss(self._current)

    def action_cancel(self) -> None:
        """escape/q: cancel or stop creating."""
        if self._creating:
            self._stop_new_armory()
            return
        self.dismiss(None)

    def action_new_armory(self) -> None:
        """n key: start creating a new armory."""
        if self._creating:
            return
        if self._allow_create:
            self._start_new_armory()

    def on_option_list_option_selected(
        self,
        event: OptionList.OptionSelected,
    ) -> None:
        if event.option_list.id != "armory-list":
            return
        event.stop()
        idx = event.option_list.highlighted
        if idx is not None and 0 <= idx < len(self._entries):
            self._navigate_into(self._entries[idx])

    def _start_new_armory(self) -> None:
        self._creating = True
        container = self.query_one("#armory-new-input-container", Vertical)
        container.add_class("active")
        inp = self.query_one("#armory-new-input", Input)
        inp.value = ""
        inp.focus()
        hint = self.query_one("#armory-hint", Static)
        hint.update("enter confirm  esc cancel")

    def _stop_new_armory(self) -> None:
        self._creating = False
        container = self.query_one("#armory-new-input-container", Vertical)
        container.remove_class("active")
        hint = self.query_one("#armory-hint", Static)
        hint.update("\u2191\u2193 navigate  enter open  c choose  n new  esc cancel")
        self._focus_list()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "armory-new-input":
            return
        name = event.value.strip()
        if not name:
            self._stop_new_armory()
            return
        armory_path = self._current / name
        try:
            initialize(armory_path)
        except OSError:
            self._stop_new_armory()
            return
        self.dismiss(armory_path)

    def on_key(self, event: events.Key) -> None:  # type: ignore[override]
        # When creating, only intercept escape; let the Input handle the rest.
        if self._creating:
            if event.key == "escape":
                self._stop_new_armory()
                event.prevent_default()
                event.stop()
            # All other keys go to the Input widget naturally.
            return

        # Let OptionList handle up/down/enter natively for list navigation.
        # We only intercept our custom action keys here if the OptionList
        # doesn't already handle them via BINDINGS.
        if event.key in ("c", "n", "q"):
            # These are handled by BINDINGS -> action_* methods.
            # But we need to stop propagation so the parent TUI doesn't
            # intercept them.
            event.stop()
            return

        if event.key == "escape":
            event.stop()
            event.prevent_default()
            return

        # All other keys (up, down, enter, etc.) flow to OptionList naturally.
