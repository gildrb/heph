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
    STYLE_EMBER,
    STYLE_ERROR,
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
    source_files: tuple[str, ...] = (),
) -> None:
    """Print a compact startup screen with essential status and input hints."""
    api_status = (
        styled("configured", STYLE_SUCCESS) if has_api_key else styled("missing", STYLE_ERROR)
    )
    source_status = (
        styled(_format_source_summary(source_file_count, source_files), STYLE_DIM)
        if source_file_count
        else styled("none", STYLE_DIM)
    )
    armory_style = STYLE_DIM if armory_path != "none" else STYLE_EMBER
    model_text = model or "none"
    model_style = STYLE_SUCCESS if model else STYLE_EMBER

    print(f"{styled('Hephaistos', STYLE_EMBER)} {styled(f'v{version}', STYLE_DIM)}")
    print()
    print(
        "  "
        f"{styled('armory', STYLE_DIM)} {styled(armory_path, armory_style)}"
        "  "
        f"{styled('model', STYLE_DIM)} {styled(model_text, model_style)}"
        "  "
        f"{styled('api', STYLE_DIM)} {api_status}"
        "  "
        f"{styled('source', STYLE_DIM)} {source_status}"
    )
    print(f"  {styled('enter', STYLE_DIM)} send  {styled('tab', STYLE_DIM)} complete")
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
    source_files: tuple[str, ...] = (),
) -> list[tuple[str, str]]:
    """Return FormattedText fragments for the fullscreen header bar."""
    api_status = "configured" if has_api_key else "missing"
    api_style = "class:header.success" if has_api_key else "class:header.error"
    model_text = model or "none"
    model_style = "class:header.configured" if model else "class:header.ember"
    source_text = _format_source_summary(source_file_count, source_files)
    source_style = "class:header.dim" if source_file_count else "class:header.ember"
    armory_style = "class:header.dim" if armory_path != "none" else "class:header.ember"

    fragments: list[tuple[str, str]] = [
        ("class:header.title", "Hephaistos"),
        ("class:header.dim", f" v{version}"),
        ("", "\n"),
        ("class:header.dim", "  armory "),
        (armory_style, armory_path),
        ("class:header.dim", "  model "),
        (model_style, model_text),
        ("class:header.dim", "  api "),
        (api_style, api_status),
        ("class:header.dim", "  source "),
        (source_style, source_text),
        ("", "\n"),
        ("class:header.dim", "  enter "),
        ("class:header.dim", "send  "),
        ("class:header.dim", "tab "),
        ("class:header.dim", "complete  "),
        ("class:header.dim", "ctrl+c "),
        ("class:header.dim", "interrupt  "),
        ("class:header.dim", "ctrl+d "),
        ("class:header.dim", "exit"),
    ]
    if not has_api_key:
        fragments.extend(
            [
                ("", "\n"),
                ("class:header.warning", "  configure api "),
                ("class:header.accent", "/api key <your-key>"),
            ]
        )
    return fragments


def _format_source_summary(source_file_count: int, source_files: tuple[str, ...]) -> str:
    if source_file_count == 0:
        return "none"
    visible = source_files[:3]
    if not visible:
        return f"{source_file_count} file{'s' if source_file_count != 1 else ''}"
    suffix = f" +{source_file_count - len(visible)}" if source_file_count > len(visible) else ""
    return f"{', '.join(visible)}{suffix}"


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
