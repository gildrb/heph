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

from hephaistos.app.palette import ThemePalette, current_palette
from hephaistos.armory.storage import MARKER_FILE, initialize

_PARENT_LABEL = "..  (parent)"
_NEW_ARMORY_LABEL = "\u271b New armory..."
_DIR_ICON = "\U0001f4c1 "

_SPECIAL_ENTRIES = (_PARENT_LABEL, _NEW_ARMORY_LABEL)


def _armory_browser_css(p: ThemePalette) -> str:
    """Generate CSS from the active theme palette."""
    bg = "transparent" if p.is_transparent else p.background
    border_color = p.stone
    text_color = p.text
    dim_color = p.dim
    ember_color = p.ember

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


def _inline_styles(p: ThemePalette) -> dict[str, str]:
    """Return theme-driven Rich markup style strings for list rendering."""
    return {
        "selected": f"bold {p.text} on {p.highlight}",
        "normal": p.text,
        "parent": p.dim,
        "parent_sel": f"bold {p.text} on {p.highlight}",
        "new": p.ember,
        "new_sel": f"bold {p.text} on {p.highlight}",
        "badge": p.configured,
        "badge_sel": f"bold {p.configured} on {p.highlight}",
    }


class ArmoryBrowserScreen(ModalScreen[Path | None]):
    """Modal directory browser for selecting or creating an armory.

    Returns the chosen *Path* when the user picks a directory, or *None*
    when cancelled.
    """

    BINDINGS: ClassVar[list[Binding]] = []  # type: ignore[assignment]

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
        self.CSS = _armory_browser_css(current_palette())

    def compose(self) -> ComposeResult:
        p = current_palette()
        with Vertical(id="armory-dialog"):
            title = f"[bold {p.ember}]\u2301 Armory[/bold {p.ember}]"
            yield Static(title, id="armory-title", markup=True)
            yield Static("", id="armory-path")
            yield Static("", id="armory-list", markup=True)
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
        self.focus()

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
        self._render_list()

    def _render_list(self) -> None:
        list_widget = self.query_one("#armory-list", Static)
        entries = self._entries()
        s = _inline_styles(current_palette())
        lines: list[str] = []
        for index, name in enumerate(entries):
            is_sel = index == self._selected

            if name == _PARENT_LABEL:
                style = s["parent_sel"] if is_sel else s["parent"]
                indicator = " \u25b8 " if is_sel else "   "
                lines.append(f"[{style}]{indicator}{name}[/{style}]")

            elif name == _NEW_ARMORY_LABEL:
                style = s["new_sel"] if is_sel else s["new"]
                indicator = " \u25b8 " if is_sel else "   "
                lines.append(f"[{style}]{indicator}{name}[/{style}]")

            else:
                child = self._child_path(index)
                has_badge = child is not None and _is_armory(child)
                if is_sel:
                    indicator = " \u25b8 "
                    badge = (
                        f" [{s['badge_sel']}]\u2713 armory[/{s['badge_sel']}]" if has_badge else ""
                    )
                    lines.append(
                        f"[{s['selected']}]{indicator}{_DIR_ICON}{name}{badge}[/{s['selected']}]"
                    )
                else:
                    badge = f" [{s['badge']}]\u2713 armory[/{s['badge']}]" if has_badge else ""
                    lines.append(f"   [{s['normal']}]{_DIR_ICON}{name}[/{s['normal']}]{badge}")

        list_widget.update("\n".join(lines))

    def _move_cursor(self, delta: int) -> None:
        if self._creating:
            return
        entries = self._entries()
        if not entries:
            return
        self._selected = (self._selected + delta) % len(entries)
        self._render_list()

    def _navigate_parent(self) -> None:
        parent = self._current.parent
        if parent != self._current and parent.exists():
            self._current = parent
            self._selected = 0
            self._refresh()

    def _navigate_into(self) -> None:
        entries = self._entries()
        if not entries:
            return
        name = entries[self._selected]

        if name == _PARENT_LABEL:
            self._navigate_parent()
            return

        if name == _NEW_ARMORY_LABEL:
            self._start_new_armory()
            return

        child = self._child_path(self._selected)
        if child is not None:
            self._current = child
            self._selected = 0
            self._refresh()

    def _choose_current(self) -> None:
        if self._creating:
            return
        self.dismiss(self._current)

    def _cancel(self) -> None:
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
        self.focus()

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
        # Always stop propagation so the parent HephaistosTui.on_key
        # cannot intercept our keys.
        event.stop()
        event.prevent_default()

        # If the new-armory input is active, only handle escape/quit
        if self._creating:
            if event.key in ("escape", "q"):
                self._stop_new_armory()
            # All other keys (including enter) are handled by the Input widget
            return

        if event.key in ("up", "k"):
            self._move_cursor(-1)
        elif event.key in ("down", "j"):
            self._move_cursor(1)
        elif event.key == "enter":
            self._navigate_into()
        elif event.key == "c":
            self._choose_current()
        elif event.key == "n":
            if self._allow_create:
                self._start_new_armory()
        elif event.key in ("escape", "q"):
            self._cancel()
