# pyright: reportMissingImports=false, reportUnknownArgumentType=false, reportUnknownMemberType=false
# pyright: reportUntypedBaseClass=false, reportGeneralTypeIssues=false
# pyright: reportUnknownVariableType=false, reportInvalidTypeArguments=false, reportInvalidTypeForm=false
# pyright: reportOptionalCall=false, reportUnknownParameterType=false
"""Inline Textual armory browser screen.

A ModalScreen that renders a directory browser inside the TUI, inspired by
ghui's navigable list UX.  Users browse directories, see which ones are
already valid armories, create new armories inline, and pick a target path.

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
    from textual.widgets import Input, Static
except ImportError:
    events = None  # type: ignore[assignment]
    ComposeResult = None  # type: ignore[assignment,misc]
    Binding = None  # type: ignore[assignment,misc]
    Vertical = None  # type: ignore[assignment,misc]
    ModalScreen = object  # type: ignore[assignment,misc]
    Input = None  # type: ignore[assignment,misc]
    Static = None  # type: ignore[assignment,misc]

from hephaistos.armory.storage import MARKER_FILE, initialize

_PARENT_LABEL = "..  (parent)"
_NEW_ARMORY_LABEL = "\u271b New armory..."
_DIR_ICON = "\U0001f4c1 "
_ARMORY_BADGE = "  \u2713 armory"

_ARMORY_BROWSER_CSS = """
ArmoryBrowserScreen {
    align: center middle;
    layout: vertical;
}
#armory-dialog {
    width: 60;
    max-width: 90%;
    height: auto;
    max-height: 80%;
    padding: 1 2;
    background: #1C1C1C;
    border: round #555555;
    color: #E0E0E0;
}
#armory-title {
    text-style: bold;
    color: #9B4A2E;
    width: 100%;
    margin-bottom: 0;
}
#armory-path {
    color: #808080;
    width: 100%;
    margin-bottom: 1;
}
#armory-list {
    width: 100%;
    height: auto;
    max-height: 16;
    background: transparent;
}
#armory-list:focus {
    background: transparent;
}
.armory-entry {
    height: 1;
    width: 100%;
    padding: 0 1;
    background: transparent;
    color: #E0E0E0;
}
.armory-entry.highlighted {
    background: #333333;
    color: #FFFFFF;
    text-style: bold;
}
.armory-entry.parent-entry {
    color: #808080;
}
.armory-entry.parent-entry.highlighted {
    background: #333333;
    color: #FFFFFF;
    text-style: bold;
}
.armory-entry.new-armory {
    color: #9B4A2E;
}
.armory-entry.new-armory.highlighted {
    background: #333333;
    color: #FFFFFF;
    text-style: bold;
}
.armory-badge {
    color: #7F9A6A;
}
#armory-hint {
    color: #808080;
    width: 100%;
    margin-top: 0;
}
#armory-new-input-container {
    height: auto;
    width: 100%;
    padding: 0 1;
    display: none;
    background: transparent;
}
#armory-new-input-container.active {
    display: block;
}
#armory-new-input {
    height: 1;
    width: 100%;
    background: #1C1C1C;
    color: #FFFFFF;
    border: none;
}
"""

_SPECIAL_ENTRIES = (_PARENT_LABEL, _NEW_ARMORY_LABEL)


def _list_child_dirs(path: Path) -> list[Path]:
    """Return sorted child directories, skipping hidden ones."""
    try:
        entries = sorted(path.iterdir())
    except PermissionError:
        return []
    return [e for e in entries if e.is_dir() and not e.name.startswith(".")]


def _is_armory(path: Path) -> bool:
    return (path / MARKER_FILE).exists()


class ArmoryBrowserScreen(ModalScreen[Path | None]):
    """Modal directory browser for selecting or creating an armory.

    Returns the chosen *Path* when the user picks a directory, or *None*
    when cancelled.
    """

    CSS = _ARMORY_BROWSER_CSS

    BINDINGS: ClassVar[list[Binding]] = [  # type: ignore[assignment]
        Binding("up", "cursor_up", "Up", show=False),
        Binding("down", "cursor_down", "Down", show=False),
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("enter", "select", "Select"),
        Binding("c", "choose_current", "Choose"),
        Binding("n", "new_armory", "New"),
        Binding("escape", "cancel", "Cancel"),
        Binding("q", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        start: Path | None = None,
        *,
        allow_create: bool = True,
    ) -> None:
        super().__init__()
        self._current = (start or Path.cwd()).resolve()
        self._selected = 0
        self._allow_create = allow_create
        self._creating = False

    def compose(self) -> ComposeResult:
        with Vertical(id="armory-dialog"):
            yield Static("Armory Browser", id="armory-title")
            yield Static("", id="armory-path")
            yield Static("", id="armory-list")
            with Vertical(id="armory-new-input-container"):
                yield Input(
                    placeholder="Armory name...",
                    id="armory-new-input",
                )
            yield Static(
                "\u2191\u2193 navigate  enter open  c choose  n new  q cancel",
                id="armory-hint",
            )

    def on_mount(self) -> None:
        self._refresh()

    def _entries(self) -> list[str]:
        names: list[str] = [_PARENT_LABEL]
        if self._allow_create:
            names.append(_NEW_ARMORY_LABEL)
        names.extend(child.name for child in _list_child_dirs(self._current))
        return names

    def _child_path(self, index: int) -> Path | None:
        """Return the child dir for a given entry index (skipping specials)."""
        offset = 2 if self._allow_create else 1
        real_index = index - offset
        children = _list_child_dirs(self._current)
        if 0 <= real_index < len(children):
            return children[real_index]
        return None

    def _refresh(self) -> None:
        entries = self._entries()
        self._selected = min(self._selected, max(0, len(entries) - 1))

        path_widget = self.query_one("#armory-path", Static)
        path_widget.update(str(self._current))

        lines: list[str] = []
        for index, name in enumerate(entries):
            if name in _SPECIAL_ENTRIES:
                lines.append(name)
            else:
                child = self._child_path(index)
                badge = _ARMORY_BADGE if child is not None and _is_armory(child) else ""
                lines.append(f"{_DIR_ICON}{name}{badge}")

        rendered = "\n".join(lines)
        list_widget = self.query_one("#armory-list", Static)
        list_widget.update(rendered)

    def _move_cursor(self, delta: int) -> None:
        if self._creating:
            return
        entries = self._entries()
        if not entries:
            return
        self._selected = (self._selected + delta) % len(entries)
        self._highlight()

    def _highlight(self) -> None:
        list_widget = self.query_one("#armory-list", Static)
        entries = self._entries()
        lines: list[str] = []
        for index, name in enumerate(entries):
            is_sel = index == self._selected
            if name == _PARENT_LABEL:
                cls = "highlighted" if is_sel else ""
                prefix = "parent-entry "
                lines.append(f"[{prefix}{cls}]{name}[/{prefix}{cls}]")
            elif name == _NEW_ARMORY_LABEL:
                cls = "highlighted" if is_sel else ""
                prefix = "new-armory "
                lines.append(f"[{prefix}{cls}]{name}[/{prefix}{cls}]")
            else:
                child = self._child_path(index)
                badge = (
                    "  [armory-badge]\u2713 armory[/armory-badge]"
                    if child is not None and _is_armory(child)
                    else ""
                )
                if is_sel:
                    lines.append(f"[highlighted]{_DIR_ICON}{name}{badge}[/highlighted]")
                else:
                    lines.append(f"{_DIR_ICON}{name}{badge}")
        list_widget.update("\n".join(lines))

    def action_cursor_up(self) -> None:
        self._move_cursor(-1)

    def action_cursor_down(self) -> None:
        self._move_cursor(1)

    def action_select(self) -> None:
        if self._creating:
            return
        entries = self._entries()
        if not entries:
            return
        name = entries[self._selected]

        if name == _PARENT_LABEL:
            parent = self._current.parent
            if parent != self._current and parent.exists():
                self._current = parent
                self._selected = 0
                self._refresh()
            return

        if name == _NEW_ARMORY_LABEL:
            self._start_new_armory()
            return

        child = self._child_path(self._selected)
        if child is not None:
            self._current = child
            self._selected = 0
            self._refresh()

    def action_choose_current(self) -> None:
        """Choose the currently displayed directory as the armory path."""
        if self._creating:
            return
        self.dismiss(self._current)

    def action_new_armory(self) -> None:
        if not self._allow_create:
            return
        self._start_new_armory()

    def action_cancel(self) -> None:
        if self._creating:
            self._stop_new_armory()
            return
        self.dismiss(None)

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
        hint.update("\u2191\u2193 navigate  enter open  c choose  n new  q cancel")

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
        # Block regular list navigation while the new-armory input is active
        if self._creating and event.key in ("q", "escape"):
            self._stop_new_armory()
            event.prevent_default()
            event.stop()
