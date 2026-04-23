"""ANSI terminal helpers: styling, prompt rendering."""

from __future__ import annotations

import re
import sys
from typing import Protocol, runtime_checkable

from hephaistos.app import palette
from hephaistos.app.palette import (
    RESET,
    STYLE_ACCENT,
    STYLE_DIM,
    STYLE_ERROR,
    STYLE_PROMPT,
    STYLE_SUCCESS,
    STYLE_WARNING,
)

STYLE_ASSISTANT = palette.STYLE_ASSISTANT


def styled(text: str, style: object) -> str:
    return f"{style!s}{text}{RESET}"


_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


@runtime_checkable
class _StdoutProxy(Protocol):
    original_stdout: object


@runtime_checkable
class _TextOutput(Protocol):
    def write(self, text: str, /) -> object: ...

    def flush(self) -> object: ...


def visible_len(text: str) -> int:
    """Return the visible (non-ANSI) character count of a string."""
    return len(_ANSI_RE.sub("", text))


def print_error(msg: str) -> None:
    print(f"{styled('error:', STYLE_ERROR)} {msg}")


def print_info(msg: str) -> None:
    print(f"{styled('info:', STYLE_DIM)} {msg}")


def print_success(msg: str) -> None:
    print(f"{styled(msg, STYLE_SUCCESS)}")


def print_shell_intro(
    version: str,
    armory_path: str,
    source_file_count: int,
    model: str,
    has_api_key: bool,
) -> None:
    """Print a compact startup screen with essential status and input hints."""
    api_status = (
        styled("configured", STYLE_SUCCESS) if has_api_key else styled("missing", STYLE_ERROR)
    )
    source_status = (
        styled(f"{source_file_count} file{'s' if source_file_count != 1 else ''}", STYLE_ACCENT)
        if source_file_count
        else styled("none", STYLE_DIM)
    )
    armory_style = STYLE_ACCENT if armory_path != "none" else STYLE_DIM

    print(f"{styled('Hephaistos', STYLE_ACCENT)} {styled(f'v{version}', STYLE_DIM)}")
    print()
    print(
        "  "
        f"{styled('armory', STYLE_DIM)} {styled(armory_path, armory_style)}"
        "  "
        f"{styled('model', STYLE_DIM)} {styled(model, STYLE_PROMPT)}"
        "  "
        f"{styled('api', STYLE_DIM)} {api_status}"
        "  "
        f"{styled('source', STYLE_DIM)} {source_status}"
    )
    print(
        "  "
        f"{styled('enter', STYLE_DIM)} send"
        "  "
        f"{styled('alt+enter', STYLE_DIM)} newline"
        "  "
        f"{styled('tab', STYLE_DIM)} complete"
    )
    print(
        "  "
        f"{styled('ctrl+c', STYLE_DIM)} interrupt"
        "  "
        f"{styled('ctrl+d', STYLE_DIM)} exit"
        "  "
        f"{styled('/help', STYLE_ACCENT)} commands"
        "  "
        f"{styled('/settings', STYLE_ACCENT)} settings"
        "  "
        f"{styled('/armory', STYLE_ACCENT)} workspace"
        "  "
        f"{styled('!', STYLE_ACCENT)} shell"
    )
    if not has_api_key:
        print(
            "  "
            f"{styled('configure api', STYLE_WARNING)} "
            f"{styled('/api key <your-key>', STYLE_ACCENT)}"
        )
    print()


def format_shell_header(
    version: str,
    armory_path: str,
    source_file_count: int,
    model: str,
    has_api_key: bool,
) -> list[tuple[str, str]]:
    """Return ``FormattedText``-compatible fragments for the fullscreen header.

    Mirrors :func:`print_shell_intro` but emits ``(style_class, text)`` tuples
    using prompt_toolkit style classes (``class:header.*``) so the header bar
    in the fullscreen shell renders with the same information as the classic
    intro banner.
    """
    has_armory = armory_path != "none"
    armory_label = armory_path if has_armory else "none"
    armory_style = "class:header.accent" if has_armory else "class:header.dim"

    if source_file_count:
        source_label = f"{source_file_count} file{'s' if source_file_count != 1 else ''}"
        source_style = "class:header.accent"
    else:
        source_label = "none"
        source_style = "class:header.dim"

    api_label = "configured" if has_api_key else "missing"
    api_style = "class:header.success" if has_api_key else "class:header.error"

    fragments: list[tuple[str, str]] = [
        ("class:header.title", "Hephaistos"),
        ("class:header", " "),
        ("class:header.dim", f"v{version}"),
        ("class:header", "\n  "),
        ("class:header.dim", "armory"),
        ("class:header", " "),
        (armory_style, armory_label),
        ("class:header", "  "),
        ("class:header.dim", "model"),
        ("class:header", " "),
        ("class:header.accent", model or "none"),
        ("class:header", "  "),
        ("class:header.dim", "api"),
        ("class:header", " "),
        (api_style, api_label),
        ("class:header", "  "),
        ("class:header.dim", "source"),
        ("class:header", " "),
        (source_style, source_label),
        ("class:header", "\n  "),
        ("class:header.dim", "enter"),
        ("class:header", " send  "),
        ("class:header.dim", "alt+enter"),
        ("class:header", " newline  "),
        ("class:header.dim", "tab"),
        ("class:header", " complete  "),
        ("class:header.dim", "ctrl+c"),
        ("class:header", " interrupt  "),
        ("class:header.dim", "ctrl+d"),
        ("class:header", " exit  "),
        ("class:header.accent", "/help"),
        ("class:header", " commands  "),
        ("class:header.accent", "!"),
        ("class:header", " shell"),
    ]
    if not has_api_key:
        fragments.extend(
            [
                ("class:header", "\n  "),
                ("class:header.error", "configure api"),
                ("class:header", " "),
                ("class:header.accent", "/api key <your-key>"),
            ]
        )
    return fragments


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
