"""Inline menu helpers for TTY workflows.

Selection flows render directly into the current terminal stream so they feel
like part of the shell rather than a separate full-screen mode.
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from prompt_toolkit.application import Application
from prompt_toolkit.input.base import Input
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.output.base import Output
from prompt_toolkit.styles import DynamicStyle
from prompt_toolkit.styles import Style as PtStyle

from hephaistos.app.display import (
    STYLE_DIM,
    direct_input,
    direct_print,
    styled,
    visible_len,
)
from hephaistos.app.palette import BOLD, STYLE_PROMPT, browser_style_dict, menu_style_dict

DEFAULT_MENU_KEYBINDINGS: dict[str, str | list[str]] = {
    "navigate_up": "up",
    "navigate_down": "down",
    "select": "enter",
    "cancel": ["c-c", "escape"],
}


@dataclass(frozen=True)
class MenuOption:
    label: str
    description: str = ""
    is_current: bool = False


_MENU_STYLE = DynamicStyle(lambda: PtStyle.from_dict(menu_style_dict()))


def _key_list(keys: str | list[str]) -> list[str]:
    if isinstance(keys, str):
        return [key.strip() for key in keys.split(",") if key.strip()]
    return keys


def _initial_selection(options: list[MenuOption]) -> int:
    for index, option in enumerate(options):
        if option.is_current:
            return index
    return 0


def _terminal_columns(default: int = 80) -> int:
    """Return the current terminal width for inline render surfaces."""
    return max(default, shutil.get_terminal_size(fallback=(default, 24)).columns)


def _pad_line(text: str, width: int) -> str:
    """Pad a rendered line so redraws overwrite the previous frame cleanly."""
    return text + (" " * max(0, width - visible_len(text)))


def _format_menu(title: str, options: list[MenuOption], selected: int):
    max_label = max(visible_len(option.label) for option in options)
    lines: list[int] = [visible_len(title)]
    rendered_rows: list[tuple[str, str, str, str, str]] = []

    for index, option in enumerate(options):
        is_selected = index == selected
        option_style = (
            "class:inline-menu.option.current" if is_selected else "class:inline-menu.option"
        )
        desc_style = (
            "class:inline-menu.description.current"
            if is_selected
            else "class:inline-menu.description"
        )
        label = option.label.ljust(max_label) if option.description else option.label
        desc = f"  {option.description}" if option.description else ""
        badge = "  active" if option.is_current else ""
        line_width = visible_len(f"  {label}{desc}{badge}")
        lines.append(line_width)
        row_label = f"  {label}"
        rendered_rows.append((option_style, desc_style, row_label, desc, badge))

    width = max(_terminal_columns(), *lines)
    fragments: list[tuple[str, str]] = [
        ("class:inline-menu.title", _pad_line(title, width)),
        ("", "\n"),
    ]

    for option_style, desc_style, label, desc, badge in rendered_rows:
        fragments.append((option_style, label))
        if desc:
            fragments.append((desc_style, desc))
        if badge:
            fragments.append((desc_style, badge))
        pad_width = visible_len(label) + visible_len(desc) + visible_len(badge)
        fragments.append((option_style, " " * max(0, width - pad_width)))
        fragments.append(("", "\n"))

    fragments.append(("class:inline-menu.hint", ""))
    return fragments


def _select_with_prompt_toolkit(
    title: str,
    options: list[MenuOption],
    keybindings: dict[str, str | list[str]],
    *,
    input_obj: Input | None = None,
    output_obj: Output | None = None,
) -> int | None:
    selected = _initial_selection(options)
    bindings = KeyBindings()

    @bindings.add(*_key_list(keybindings["navigate_up"]))
    def _(event: KeyPressEvent) -> None:
        nonlocal selected
        selected = (selected - 1) % len(options)
        event.app.invalidate()

    @bindings.add(*_key_list(keybindings["navigate_down"]))
    def _(event: KeyPressEvent) -> None:
        nonlocal selected
        selected = (selected + 1) % len(options)
        event.app.invalidate()

    @bindings.add(*_key_list(keybindings["select"]))
    def _(event: KeyPressEvent) -> None:
        event.app.exit(result=selected)

    def _cancel(event: KeyPressEvent) -> None:
        event.app.exit(result=None)

    for key in _key_list(keybindings["cancel"]):
        bindings.add(key)(_cancel)

    bindings.add("q")(_cancel)

    for index in range(min(len(options), 9)):

        @bindings.add(str(index + 1))
        def _(event: KeyPressEvent, option_index: int = index) -> None:
            event.app.exit(result=option_index)

    control = FormattedTextControl(
        lambda: _format_menu(title, options, selected),
        focusable=True,
        show_cursor=False,
    )
    app: Application[int | None] = Application(
        layout=Layout(Window(content=control, dont_extend_height=True, always_hide_cursor=True)),
        key_bindings=bindings,
        style=_MENU_STYLE,
        full_screen=True,
        erase_when_done=True,
        input=input_obj,
        output=output_obj,
    )
    try:
        return app.run()
    except (KeyboardInterrupt, EOFError):
        return None


def _select_with_prompt(title: str, options: list[MenuOption]) -> int | None:
    direct_print(styled(title, STYLE_PROMPT))
    for option in options:
        label = styled(option.label, BOLD)
        desc = styled(option.description, STYLE_DIM) if option.description else ""
        cur = styled("active", STYLE_PROMPT) if option.is_current else ""
        if desc:
            max_label = max(visible_len(o.label) for o in options)
            padded = f"{option.label}".ljust(max_label)
            suffix = f"  {cur}" if cur else ""
            direct_print(f"  {padded}  {desc}{suffix}")
        else:
            suffix = f"  {cur}" if cur else ""
            direct_print(f"  {label}{suffix}")
    direct_print(f"  {styled('q.', STYLE_DIM)} cancel")

    while True:
        try:
            choice = direct_input("\n  select > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return None
        choice = choice.removeprefix("/")
        if choice in {"q", "quit", "exit"}:
            return None
        try:
            idx = int(choice) - 1
        except ValueError:
            direct_print("Unknown option.")
            continue
        if 0 <= idx < len(options):
            return idx
        direct_print("Unknown option.")


def select_option(
    title: str,
    options: list[MenuOption],
    *,
    keybindings: dict[str, str | list[str]] | None = None,
) -> int | None:
    """Return the selected option index or ``None`` when cancelled."""
    if not options:
        return None

    kb = DEFAULT_MENU_KEYBINDINGS | (keybindings or {})
    if sys.stdin.isatty() and sys.stdout.isatty():
        return _select_with_prompt_toolkit(title, options, kb)

    return _select_with_prompt(title, options)


def confirm(title: str, default: bool = False) -> bool:
    """Show a yes/no confirmation menu.  Returns True for yes."""
    opts = [
        MenuOption("Yes", ""),
        MenuOption("No", "", is_current=not default),
    ]
    if default:
        opts[0] = MenuOption("Yes", "", is_current=True)
        opts[1] = MenuOption("No", "")
    selected = select_option(title, opts)
    return selected == 0


# --- Directory browser -------------------------------------------------------

_BROWSER_STYLE = DynamicStyle(lambda: PtStyle.from_dict(browser_style_dict()))

_DIR_ICON = "\U0001f4c1"  # folder icon
_PARENT_LABEL = "..  (parent)"


def _list_child_dirs(path: Path) -> list[Path]:
    """Return sorted list of child directories, skipping hidden ones."""
    try:
        entries = sorted(path.iterdir())
    except PermissionError:
        return []
    return [e for e in entries if e.is_dir() and not e.name.startswith(".")]


def _format_browser(title: str, current: Path, entries: list[str], selected: int):
    line_widths = [
        visible_len(title),
        visible_len(f"  {current}"),
    ]
    browser_rows: list[tuple[str, str]] = []
    for index, name in enumerate(entries):
        is_selected = index == selected
        is_parent = name == _PARENT_LABEL
        if is_parent:
            style = "class:browser.parent.selected" if is_selected else "class:browser.parent"
        else:
            style = "class:browser.entry.selected" if is_selected else "class:browser.entry"
        icon = "" if is_parent else f"{_DIR_ICON} "
        row = f"  {icon}{name}"
        browser_rows.append((style, row))
        line_widths.append(visible_len(row))

    width = max(_terminal_columns(), *line_widths)
    fragments: list[tuple[str, str]] = [
        ("class:browser.title", _pad_line(title, width)),
        ("", "\n"),
        ("class:browser.path", _pad_line(f"  {current}", width)),
        ("", "\n\n"),
    ]
    for style, row in browser_rows:
        fragments.append((style, _pad_line(row, width)))
        fragments.append(("", "\n"))

    fragments.append(("", "\n"))
    return fragments


def _browse_with_prompt_toolkit(
    title: str,
    start: Path,
    *,
    input_obj: Input | None = None,
    output_obj: Output | None = None,
) -> Path | None:
    current = start.resolve()
    selected = 0

    def _entries() -> list[str]:
        names: list[str] = [_PARENT_LABEL]
        names.extend(child.name for child in _list_child_dirs(current))
        return names

    def _child_path(index: int) -> Path | None:
        real_index = index - 1  # skip parent entry
        children = _list_child_dirs(current)
        if 0 <= real_index < len(children):
            return children[real_index]
        return None

    entries = _entries()
    bindings = KeyBindings()

    @bindings.add("up")
    def _(event: KeyPressEvent) -> None:
        nonlocal selected
        selected = (selected - 1) % len(entries)
        event.app.invalidate()

    @bindings.add("down")
    def _(event: KeyPressEvent) -> None:
        nonlocal selected
        selected = (selected + 1) % len(entries)
        event.app.invalidate()

    @bindings.add("enter")
    def _(event: KeyPressEvent) -> None:
        nonlocal current, selected, entries
        if selected == 0:
            parent = current.parent
            if parent != current and parent.exists():
                current = parent
        else:
            child = _child_path(selected)
            if child is not None:
                current = child
        entries = _entries()
        selected = 0
        event.app.invalidate()

    @bindings.add("c")
    @bindings.add("C")
    def _(event: KeyPressEvent) -> None:
        event.app.exit(result=current)

    @bindings.add("escape")
    @bindings.add("q")
    @bindings.add("c-c")
    def _(event: KeyPressEvent) -> None:
        event.app.exit(result=None)

    control = FormattedTextControl(
        lambda: _format_browser(title, current, entries, selected),
        focusable=True,
        show_cursor=False,
    )
    app: Application[Path | None] = Application(
        layout=Layout(Window(content=control, dont_extend_height=True, always_hide_cursor=True)),
        key_bindings=bindings,
        style=_BROWSER_STYLE,
        full_screen=True,
        erase_when_done=True,
        input=input_obj,
        output=output_obj,
    )
    try:
        return app.run()
    except (KeyboardInterrupt, EOFError):
        return None


def _browse_with_prompt(title: str, start: Path) -> Path | None:
    """Fallback directory browser for non-TTY environments."""
    current = start.resolve()
    while True:
        direct_print(styled(f"{title}: {current}", STYLE_PROMPT))
        entries = [_PARENT_LABEL] + [d.name for d in _list_child_dirs(current)]
        for name in entries:
            direct_print(f"  {name}")
        direct_print(styled("  c. choose this directory  q. cancel", STYLE_DIM))
        try:
            choice = direct_input("  > ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            return None
        if choice in ("q", "quit", "cancel"):
            return None
        if choice in ("c", "choose"):
            return current
        try:
            idx = int(choice) - 1
        except ValueError:
            direct_print("Unknown option.")
            continue
        if idx == 0:
            parent = current.parent
            if parent != current and parent.exists():
                current = parent
        elif 1 <= idx < len(entries):
            children = _list_child_dirs(current)
            child_idx = idx - 1
            if 0 <= child_idx < len(children):
                current = children[child_idx]
        else:
            direct_print("Unknown option.")


def browse_directory(
    title: str = "Select Directory",
    start: Path | None = None,
) -> Path | None:
    """Open an interactive directory browser and return the chosen path.

    Returns ``None`` when the user cancels.
    Falls back to a text prompt when not running in a TTY.
    """
    root = start or Path.home()
    if sys.stdin.isatty() and sys.stdout.isatty():
        return _browse_with_prompt_toolkit(title, root)
    return _browse_with_prompt(title, root)
