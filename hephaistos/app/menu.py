"""Inline menu helpers for TTY workflows.

Selection flows render directly into the current terminal stream so they feel
like part of the shell rather than a separate full-screen mode.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
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
from hephaistos.app.palette import BOLD, FORGE_ASH, FORGE_EMBER, FORGE_PANEL, FORGE_SMOKE


@dataclass(frozen=True)
class MenuOption:
    label: str
    description: str = ""
    is_current: bool = False


_MENU_STYLE = PtStyle.from_dict(
    {
        "menu.title": f"bold {FORGE_EMBER}",
        "menu.option": FORGE_ASH,
        "menu.option.current": f"bg:{FORGE_PANEL} fg:{FORGE_ASH} bold",
        "menu.description": FORGE_SMOKE,
        "menu.hint": FORGE_SMOKE,
    }
)


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
        ("class:menu.title", title),
        ("", "\n"),
    ]

    for index, option in enumerate(options):
        is_selected = index == selected
        option_style = "class:menu.option.current" if is_selected else "class:menu.option"
        marker = ">" if is_selected else " "
        label = option.label.ljust(max_label) if option.description else option.label
        fragments.append((option_style, f"  {marker} {index + 1}. {label}"))
        if option.description:
            fragments.append(("class:menu.description", f"  {option.description}"))
        if option.is_current:
            fragments.append(("class:menu.title", "  current"))
        fragments.append(("", "\n"))

    fragments.append(("class:menu.hint", "  up/down choose | enter select | q/esc cancel"))
    return fragments


def _select_with_prompt_toolkit(
    title: str,
    options: list[MenuOption],
    keybindings: dict[str, str | list[str]],
    *,
    input_obj=None,
    output_obj=None,
) -> int | None:
    selected = _initial_selection(options)
    bindings = KeyBindings()

    @bindings.add(*_key_list(keybindings["navigate_up"]))
    def _(event):
        nonlocal selected
        selected = (selected - 1) % len(options)
        event.app.invalidate()

    @bindings.add(*_key_list(keybindings["navigate_down"]))
    def _(event):
        nonlocal selected
        selected = (selected + 1) % len(options)
        event.app.invalidate()

    @bindings.add(*_key_list(keybindings["select"]))
    def _(event):
        event.app.exit(result=selected)

    @bindings.add(*_key_list(keybindings["cancel"]))
    @bindings.add("q")
    def _(event):
        event.app.exit(result=None)

    for index in range(min(len(options), 9)):

        @bindings.add(str(index + 1))
        def _(event, option_index=index):
            event.app.exit(result=option_index)

    control = FormattedTextControl(
        lambda: _format_menu(title, options, selected),
        focusable=True,
        show_cursor=False,
    )
    app = Application(
        layout=Layout(Window(content=control, dont_extend_height=True, always_hide_cursor=True)),
        key_bindings=bindings,
        style=_MENU_STYLE,
        full_screen=False,
        erase_when_done=False,
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
