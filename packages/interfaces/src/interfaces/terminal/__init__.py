"""Shared terminal styling, I/O primitives, and menu helpers."""

from __future__ import annotations

import builtins
import re
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from harness.parameters.settings import DEFAULT_THEME

from interfaces.palette import (
    BOLD,
    DARK,
    DIM,
    LIGHT,
    RESET,
    Theme,
    ansi_fg,
)
from interfaces.terminal.theme_state import (
    current_palette,
    current_theme_name,
    set_theme,
)

__all__ = [
    "BOLD",
    "DARK",
    "DEFAULT_THEME",
    "DIM",
    "LIGHT",
    "RESET",
    "STYLE_ACCENT",
    "STYLE_ASSISTANT",
    "STYLE_BRAND",
    "STYLE_CHROME_DETAIL",
    "STYLE_CHROME_LABEL",
    "STYLE_DIM",
    "STYLE_EMBER",
    "STYLE_EMPHASIS",
    "STYLE_ERROR",
    "STYLE_METADATA",
    "STYLE_PROMPT",
    "STYLE_SHORTCUT",
    "STYLE_SUCCESS",
    "STYLE_WARNING",
    "MenuOption",
    "Theme",
    "ansi_fg",
    "confirm",
    "current_palette",
    "current_theme_name",
    "direct_input",
    "direct_print",
    "menu_label_value",
    "print_error",
    "print_info",
    "print_success",
    "select_option",
    "set_theme",
    "styled",
    "visible_len",
]


def style_code(style_name: str) -> str:
    palette = current_palette()
    style_groups: tuple[tuple[set[str], str], ...] = (
        ({"accent", "warning"}, f"{BOLD}{ansi_fg(palette.action_primary_bg)}"),
        ({"success"}, f"{BOLD}{ansi_fg(palette.status_success_text)}"),
        ({"prompt", "assistant", "emphasis"}, f"{BOLD}{ansi_fg(palette.text_primary)}"),
        ({"brand", "ember"}, f"{BOLD}{ansi_fg(palette.brand_primary)}"),
        ({"chrome_label", "shortcut", "metadata"}, ansi_fg(palette.text_secondary)),
        ({"chrome_detail"}, ansi_fg(palette.text_muted)),
        ({"dim"}, f"{DIM}{ansi_fg(palette.text_muted)}"),
        ({"error"}, f"{BOLD}{ansi_fg(palette.status_error_text)}"),
    )
    return next((code for names, code in style_groups if style_name in names), "")


class _StyleToken:
    __slots__ = ("_style_name",)

    def __init__(self, style_name: str) -> None:
        self._style_name = style_name

    def __str__(self) -> str:
        return style_code(self._style_name)

    def __repr__(self) -> str:
        return f"_StyleToken({self._style_name!r})"


STYLE_PROMPT = _StyleToken("prompt")
STYLE_BRAND = _StyleToken("brand")
STYLE_ACCENT = _StyleToken("accent")
STYLE_CHROME_LABEL = _StyleToken("chrome_label")
STYLE_CHROME_DETAIL = _StyleToken("chrome_detail")
STYLE_SHORTCUT = _StyleToken("shortcut")
STYLE_METADATA = _StyleToken("metadata")
STYLE_DIM = _StyleToken("dim")
STYLE_EMBER = _StyleToken("ember")
STYLE_EMPHASIS = _StyleToken("emphasis")
STYLE_ERROR = _StyleToken("error")
STYLE_SUCCESS = _StyleToken("success")
STYLE_WARNING = _StyleToken("warning")
STYLE_ASSISTANT = _StyleToken("assistant")


# ---------------------------------------------------------------------------
# Styling helpers
# ---------------------------------------------------------------------------


def styled(text: str, style: object) -> str:
    return f"{style!s}{text}{RESET}"


_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def visible_len(text: str) -> int:
    return len(_ANSI_RE.sub("", text))


def print_error(msg: str) -> None:
    print(f"{styled('error:', STYLE_ERROR)} {msg}")


def print_info(msg: str) -> None:
    print(f"{styled('info:', STYLE_DIM)} {msg}")


def print_success(msg: str) -> None:
    print(styled(msg, STYLE_SUCCESS))


def menu_label_value(label: str, value: object) -> str:
    label_text = label.strip().upper()
    value_text = str(value).strip().casefold()
    if not value_text:
        return label_text
    return f"{label_text} {value_text}"


# ---------------------------------------------------------------------------
# Terminal I/O
# ---------------------------------------------------------------------------


@runtime_checkable
class _StdoutProxy(Protocol):
    original_stdout: object


@runtime_checkable
class _TextOutput(Protocol):
    def write(self, text: str, /) -> int: ...

    def flush(self) -> None: ...


def _real_stdout() -> _TextOutput:
    out: object = sys.stdout
    while isinstance(out, _StdoutProxy):
        out = out.original_stdout
    if not isinstance(out, _TextOutput):
        raise TypeError("stdout proxy did not unwrap to a text stream")
    return out


def direct_print(text: str, end: str = "\n") -> None:
    out = _real_stdout()
    out.write(text + end)
    out.flush()


def direct_input(prompt: str = "") -> str:
    with redirect_stdout(_real_stdout()):
        return builtins.input(prompt)


# ---------------------------------------------------------------------------
# Menu helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MenuOption:
    label: str
    description: str = ""
    is_current: bool = False


def select_option(title: str, options: list[MenuOption]) -> int | None:
    if not options:
        return None

    _print_options(title, options)

    while True:
        choice = _read_menu_choice()
        if choice is None or choice in {"q", "quit", "exit"}:
            return None
        idx = _choice_index(choice)
        if 0 <= idx < len(options):
            return idx
        direct_print(menu_label_value("state", "unknown option"))


def _print_options(title: str, options: list[MenuOption]) -> None:
    direct_print(styled(menu_label_value("menu", title), STYLE_PROMPT))
    max_label = max(visible_len(option.label) for option in options)
    index_width = len(f"{len(options)}.")
    for index, option in enumerate(options, start=1):
        direct_print(
            _option_line(option, index=index, index_width=index_width, max_label=max_label)
        )
    direct_print(f"  {styled('q.'.rjust(index_width), STYLE_DIM)} CANCEL")


def _option_line(option: MenuOption, *, index: int, index_width: int, max_label: int) -> str:
    prefix = styled(f"{index}.".rjust(index_width), STYLE_DIM)
    active = styled("STATE current", STYLE_PROMPT) if option.is_current else ""
    suffix = f"  {active}" if active else ""
    if not option.description:
        return f"  {prefix} {styled(option.label, BOLD)}{suffix}"
    description = styled(option.description, STYLE_DIM)
    return f"  {prefix} {option.label.ljust(max_label)}  {description}{suffix}"


def _read_menu_choice() -> str | None:
    try:
        return direct_input("\n  SELECT > ").strip().lower().removeprefix("/")
    except (KeyboardInterrupt, EOFError):
        return None


def _choice_index(choice: str) -> int:
    try:
        return int(choice) - 1
    except ValueError:
        return -1


def confirm(title: str, default: bool = False) -> bool:
    opts = [
        MenuOption("YES", "", is_current=default),
        MenuOption("NO", "", is_current=not default),
    ]
    selected = select_option(title, opts)
    return selected == 0
