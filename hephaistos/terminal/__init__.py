"""Shared terminal styling, I/O primitives, and menu helpers."""

from __future__ import annotations

import builtins
import re
import sys
from contextlib import redirect_stdout
from dataclasses import dataclass
from typing import Final, Protocol, runtime_checkable

from hephaistos.parameters.settings import DEFAULT_THEME
from hephaistos.terminal.palette import (
    BOLD,
    DARK,
    DIM,
    HIGH_CONTRAST,
    LIGHT,
    RESET,
    THEMES,
    Theme,
    ansi_fg,
)

__all__ = [
    "BOLD",
    "DARK",
    "DIM",
    "HIGH_CONTRAST",
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
    "print_error",
    "print_info",
    "print_success",
    "select_option",
    "set_theme",
    "styled",
    "visible_len",
]


# ---------------------------------------------------------------------------
# Theme palette
# ---------------------------------------------------------------------------


_PALETTES: Final[dict[str, Theme]] = THEMES

_current_theme_name = DEFAULT_THEME


def set_theme(theme_name: str) -> str:
    global _current_theme_name  # noqa: PLW0603
    normalized = theme_name.strip().lower()
    if normalized not in _PALETTES:
        normalized = DEFAULT_THEME
    _current_theme_name = normalized
    return normalized


def current_theme_name() -> str:
    return _current_theme_name


def current_palette() -> Theme:
    return _PALETTES.get(_current_theme_name, _PALETTES[DEFAULT_THEME])


def style_code(style_name: str) -> str:
    palette = current_palette()
    style_groups: tuple[tuple[set[str], str], ...] = (
        ({"accent", "warning", "success"}, f"{BOLD}{ansi_fg(palette.action_primary_bg)}"),
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


def confirm(title: str, default: bool = False) -> bool:
    opts = [
        MenuOption("Yes", "", is_current=default),
        MenuOption("No", "", is_current=not default),
    ]
    selected = select_option(title, opts)
    return selected == 0
