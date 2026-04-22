"""Inline menu helpers for TTY workflows.

Selection flows render directly into the current terminal stream so they feel
like part of the shell rather than a separate full-screen mode.
"""

from __future__ import annotations

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
    STYLE_PROMPT,
    direct_input,
    direct_print,
    styled,
    visible_len,
)
from hephaistos.app.keybindings import DEFAULT_MENU_KEYBINDINGS
from hephaistos.app.palette import BOLD, browser_style_dict, menu_style_dict


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


def _format_menu(title: str, options: list[MenuOption], selected: int):
    max_label = max(visible_len(option.label) for option in options)
    fragments: list[tuple[str, str]] = [
        ("class:inline-menu.title", title),
        ("", "\n"),
    ]

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
        marker = ">" if is_selected else " "
        label = option.label.ljust(max_label) if option.description else option.label
        fragments.append((option_style, f"  {marker} {index + 1}. {label}"))
        if option.description:
            fragments.append((desc_style, f"  {option.description}"))
        if option.is_current:
            fragments.append(("class:inline-menu.title", "  current"))
        fragments.append(("", "\n"))

    fragments.append(("class:inline-menu.hint", "  up/down choose | enter select | q/esc cancel"))
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
        full_screen=False,
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
    for index, option in enumerate(options, start=1):
        label = styled(option.label, BOLD)
        desc = styled(option.description, STYLE_DIM) if option.description else ""
        cur = styled("current", STYLE_PROMPT) if option.is_current else ""
        if desc:
            max_label = max(visible_len(o.label) for o in options)
            padded = f"{option.label}".ljust(max_label)
            suffix = f"  {cur}" if cur else ""
            direct_print(f"  {index}. {padded}  {desc}{suffix}")
        else:
            suffix = f"  {cur}" if cur else ""
            direct_print(f"  {index}. {label}{suffix}")
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
    fragments: list[tuple[str, str]] = [
        ("class:browser.title", title),
        ("", "\n"),
        ("class:browser.path", f"  {current}"),
        ("", "\n\n"),
    ]
    for index, name in enumerate(entries):
        is_selected = index == selected
        is_parent = name == _PARENT_LABEL
        if is_parent:
            style = "class:browser.parent.selected" if is_selected else "class:browser.parent"
        else:
            style = "class:browser.entry.selected" if is_selected else "class:browser.entry"
        marker = ">" if is_selected else " "
        icon = "" if is_parent else f"{_DIR_ICON} "
        fragments.append((style, f"  {marker} {icon}{name}"))
        fragments.append(("", "\n"))

    fragments.append(("", "\n"))
    fragments.append(
        (
            "class:browser.hint",
            "  up/down navigate | enter open | c choose | q/esc cancel",
        )
    )
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
        full_screen=False,
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
        for i, name in enumerate(entries, start=1):
            prefix = "  " if name == _PARENT_LABEL else f"  {i}. "
            direct_print(f"{prefix}{name}")
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
