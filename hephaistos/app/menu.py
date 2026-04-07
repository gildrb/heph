"""Interactive menu helpers for TTY workflows.

Uses prompt_toolkit for arrow-key navigation in full-screen mode.
Falls back to a numbered prompt when the terminal is not a TTY.
All keybindings are configurable via ``DEFAULT_MENU_KEYBINDINGS``.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from prompt_toolkit.application import Application
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import FormattedTextControl, HSplit, Layout, Window
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.styles import Style as PtStyle

from hephaistos.app.display import BOLD, STYLE_DIM, STYLE_PROMPT, styled, visible_len
from hephaistos.app.keybindings import DEFAULT_MENU_KEYBINDINGS
from hephaistos.app.palette import FORGE_ASH, FORGE_EMBER, FORGE_SMOKE


@dataclass(frozen=True)
class MenuOption:
    label: str
    description: str = ""
    is_current: bool = False


# ---------------------------------------------------------------------------
# prompt_toolkit arrow-key selector (full-screen)
# ---------------------------------------------------------------------------

_MENU_STYLE = PtStyle.from_dict(
    {
        "title": FORGE_ASH,
        "selected": f"bold {FORGE_EMBER}",
        "dim": FORGE_SMOKE,
    }
)


def _add_binding(kb: KeyBindings, keys: str | list[str], handler) -> None:
    """Register a key binding, accepting a single key or a list of aliases."""
    key_list = [keys] if isinstance(keys, str) else keys
    for key in key_list:
        kb.add(*[k.strip() for k in key.split(",")])(handler)


def _select_with_prompt_toolkit(
    title: str,
    options: list[MenuOption],
    keybindings: dict[str, str | list[str]],
) -> int | None:
    """Arrow-key selector using prompt_toolkit (full-screen, alternate buffer)."""
    selected = [0]  # mutable for closure

    def get_text():
        parts: list[tuple[str, str]] = []
        parts.append(("class:title", f"\n  ⚡ Hephaistos — {title}\n\n"))
        for i, opt in enumerate(options):
            if i == selected[0]:
                parts.append(("class:selected", f"  ▸ {opt.label}\n"))
            else:
                parts.append(("", f"    {opt.label}\n"))
            if opt.description:
                parts.append(("class:dim", f"      {opt.description}\n"))
        parts.append(("", "\n"))
        parts.append(("class:dim", "  ↑↓ navigate · Enter select · Esc cancel"))
        return FormattedText(parts)

    kb = KeyBindings()

    @_add_binding(kb, keybindings["navigate_up"])
    def _(event):
        if options:
            selected[0] = (selected[0] - 1) % len(options)

    @_add_binding(kb, keybindings["navigate_down"])
    def _(event):
        if options:
            selected[0] = (selected[0] + 1) % len(options)

    @_add_binding(kb, keybindings["select"])
    def _(event):
        event.app.exit(result=selected[0])

    @_add_binding(kb, keybindings["cancel"])
    def _(event):
        event.app.exit(result=None)

    layout = Layout(
        HSplit(
            [
                Window(height=D(min=1)),
                Window(
                    content=FormattedTextControl(get_text),
                    dont_extend_height=True,
                ),
                Window(height=D(min=1)),
            ]
        )
    )

    app = Application(
        layout=layout,
        key_bindings=kb,
        style=_MENU_STYLE,
        full_screen=True,
    )
    return app.run()


# ---------------------------------------------------------------------------
# Fallback: numbered prompt
# ---------------------------------------------------------------------------


def _select_with_prompt(title: str, options: list[MenuOption]) -> int | None:
    print(styled(title, STYLE_PROMPT))
    for index, option in enumerate(options, start=1):
        label = styled(option.label, BOLD)
        desc = styled(option.description, STYLE_DIM) if option.description else ""
        cur = styled(" *", STYLE_PROMPT) if option.is_current else ""
        if desc:
            max_label = max(visible_len(o.label) for o in options)
            padded = f"  {option.label}{cur}".ljust(max_label + 6)
            print(f"  {index}. {padded}{desc}")
        else:
            print(f"  {index}. {label}{cur}")
    print(f"  {styled('q.', STYLE_DIM)} Cancel")

    while True:
        choice = input("\nSelect option: ").strip().lower()
        if choice in {"q", "quit", "exit"}:
            return None
        try:
            idx = int(choice) - 1
        except ValueError:
            print("Unknown option.")
            continue
        if 0 <= idx < len(options):
            return idx
        print("Unknown option.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def select_option(
    title: str,
    options: list[MenuOption],
    *,
    keybindings: dict[str, str | list[str]] | None = None,
) -> int | None:
    """Return the selected option index or ``None`` when cancelled."""
    if not options:
        return None

    kb = keybindings or DEFAULT_MENU_KEYBINDINGS

    if sys.stdin.isatty() and sys.stdout.isatty():
        try:
            return _select_with_prompt_toolkit(title, options, kb)
        except Exception:
            pass  # fall through to numbered prompt

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
