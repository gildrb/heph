"""Shared terminal utilities: styling, I/O primitives, and menu helpers.

This module is the single source of truth for low-level terminal interaction
used by adapter packages and leaf packages like ``vocab``. No code in this
module may import from CLI, command, or TUI adapters.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol, runtime_checkable

from hephaistos.palette import BOLD, DIM, RESET, ansi_fg
from hephaistos.parameters.settings import DEFAULT_THEME

__all__ = [
    "BOLD",
    "DIM",
    "RESET",
    "STYLE_ACCENT",
    "STYLE_ASSISTANT",
    "STYLE_DIM",
    "STYLE_EMBER",
    "STYLE_ERROR",
    "STYLE_PROMPT",
    "STYLE_SUCCESS",
    "STYLE_WARNING",
    "MenuOption",
    "ThemePalette",
    "ansi_fg",
    "browse_directory",
    "confirm",
    "current_palette",
    "current_theme_name",
    "direct_input",
    "direct_print",
    "select_option",
    "set_theme",
    "styled",
    "visible_len",
]


# ---------------------------------------------------------------------------
# Theme palette
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ThemePalette:
    name: str
    panel: str
    stone: str
    text: str
    dim: str
    accent: str
    ember: str
    configured: str
    error: str
    success: str
    highlight: str
    is_transparent: bool = True
    background: str = "transparent"


_PALETTES: Final[dict[str, ThemePalette]] = {
    "forge": ThemePalette(
        name="forge",
        panel="#1C1C1C",
        stone="#555555",
        text="#E0E0E0",
        dim="#808080",
        accent="#C8C8C8",
        ember="#9B4A2E",
        configured="#7F9A6A",
        error="#CC3333",
        success="#66BB6A",
        highlight="#333333",
        is_transparent=True,
        background="transparent",
    ),
    "light": ThemePalette(
        name="light",
        panel="#EDE8DC",
        stone="#C4B8A6",
        text="#2C241B",
        dim="#7A7068",
        accent="#8A5A2B",
        ember="#8E4A32",
        configured="#687A4B",
        error="#B03A2E",
        success="#2E8B57",
        highlight="#D4C9B8",
        is_transparent=False,
        background="#F6F2EA",
    ),
    "high_contrast": ThemePalette(
        name="high_contrast",
        panel="#1A1A1A",
        stone="#2E2E2E",
        text="#FFFFFF",
        dim="#C0C0C0",
        accent="#FFD400",
        ember="#E08050",
        configured="#A9C97A",
        error="#FF4D4D",
        success="#00FF88",
        highlight="#404040",
        is_transparent=False,
        background="#000000",
    ),
}

_current_theme_name = DEFAULT_THEME


def set_theme(theme_name: str) -> str:
    """Set the active theme and return the normalized preset name."""
    global _current_theme_name  # noqa: PLW0603
    normalized = theme_name.strip().lower()
    if normalized not in _PALETTES:
        normalized = DEFAULT_THEME
    _current_theme_name = normalized
    return normalized


def current_theme_name() -> str:
    return _current_theme_name


def current_palette() -> ThemePalette:
    return _PALETTES.get(_current_theme_name, _PALETTES[DEFAULT_THEME])


def style_code(style_name: str) -> str:
    palette = current_palette()
    if style_name in {"prompt", "accent", "warning", "assistant"}:
        return f"{BOLD}{ansi_fg(palette.accent)}"
    if style_name == "ember":
        return f"{BOLD}{ansi_fg(palette.ember)}"
    if style_name == "dim":
        return f"{DIM}{ansi_fg(palette.dim)}"
    if style_name == "error":
        return f"{BOLD}{ansi_fg(palette.error)}"
    if style_name == "success":
        return f"{BOLD}{ansi_fg(palette.success)}"
    return ""


class _StyleToken:
    __slots__ = ("_style_name",)

    def __init__(self, style_name: str) -> None:
        self._style_name = style_name

    def __str__(self) -> str:
        return style_code(self._style_name)

    def __repr__(self) -> str:
        return f"_StyleToken({self._style_name!r})"


STYLE_PROMPT = _StyleToken("prompt")
STYLE_ACCENT = _StyleToken("accent")
STYLE_DIM = _StyleToken("dim")
STYLE_EMBER = _StyleToken("ember")
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
    """Return the visible (non-ANSI) character count of a string."""
    return len(_ANSI_RE.sub("", text))


# ---------------------------------------------------------------------------
# Terminal I/O
# ---------------------------------------------------------------------------


@runtime_checkable
class _StdoutProxy(Protocol):
    original_stdout: object


@runtime_checkable
class _TextOutput(Protocol):
    def write(self, text: str, /) -> object: ...

    def flush(self) -> object: ...


def _real_stdout() -> _TextOutput:
    """Return the real terminal stdout, bypassing any ``patch_stdout`` proxy."""
    out: object = sys.stdout
    while isinstance(out, _StdoutProxy):
        out = out.original_stdout
    if not isinstance(out, _TextOutput):
        raise TypeError("stdout proxy did not unwrap to a text stream")
    return out


def direct_print(text: str, end: str = "\n") -> None:
    """Write directly to the real terminal, bypassing ``patch_stdout``."""
    out = _real_stdout()
    out.write(text + end)
    out.flush()


def direct_input(prompt: str = "") -> str:
    """Read a line from stdin, bypassing any ``patch_stdout`` proxy."""
    original = sys.stdout
    sys.stdout = _real_stdout()
    try:
        return input(prompt)
    finally:
        sys.stdout = original


# ---------------------------------------------------------------------------
# Menu helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MenuOption:
    label: str
    description: str = ""
    is_current: bool = False


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
    """Return the selected option index or ``None`` when cancelled.

    *keybindings* is accepted for API compatibility but is no longer used;
    selection always goes through the plain-text prompt.
    """
    if not options:
        return None

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


# ---------------------------------------------------------------------------
# Directory browser
# ---------------------------------------------------------------------------

_PARENT_LABEL = "..  (parent)"


def _list_child_dirs(path: Path) -> list[Path]:
    """Return sorted list of child directories, skipping hidden ones."""
    try:
        entries = sorted(path.iterdir())
    except PermissionError:
        return []
    return [e for e in entries if e.is_dir() and not e.name.startswith(".")]


def _browse_with_prompt(title: str, start: Path) -> Path | None:
    """Directory browser using a plain-text prompt."""
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
    """
    root = start or Path.home()
    return _browse_with_prompt(title, root)
