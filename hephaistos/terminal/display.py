"""ANSI terminal helpers: styling, prompt rendering."""

from __future__ import annotations

from hephaistos.parameters.settings import load_app_settings
from hephaistos.terminal import (  # re-export shared terminal primitives
    STYLE_ACCENT,
    STYLE_ASSISTANT,
    STYLE_DIM,
    STYLE_EMBER,
    STYLE_ERROR,
    STYLE_SUCCESS,
    STYLE_WARNING,
    direct_input,
    direct_print,
    styled,
    visible_len,
)
from hephaistos.terminal.banner import ascii_logo, separator_line, wordmark

__all__ = [
    "STYLE_ASSISTANT",
    "direct_input",
    "direct_print",
    "print_error",
    "print_info",
    "print_shell_intro",
    "print_success",
    "styled",
    "visible_len",
]


def print_error(msg: str) -> None:
    print(f"{styled('error:', STYLE_ERROR)} {msg}")


def print_info(msg: str) -> None:
    print(f"{styled('info:', STYLE_DIM)} {msg}")


def print_success(msg: str) -> None:
    print(f"{styled(msg, STYLE_SUCCESS)}")


def _progressive_hints(session_count: int) -> list[str]:
    """Return keybind hint lines that evolve with user experience.

    Tier 0 (new):     enter, tab, ctrl+c, ctrl+d, /help
    Tier 1 (3+):      + /vocab, /models, /theme
    Tier 2 (5+):      + ! shell, \\ continuation
    Always:           /help
    """
    parts: list[str] = [f"{styled('enter', STYLE_DIM)} send  {styled('tab', STYLE_DIM)} complete"]
    essentials = (
        f"{styled('ctrl+c', STYLE_DIM)} interrupt"
        f"  {styled('ctrl+d', STYLE_DIM)} exit"
        f"  {styled('/help', STYLE_ACCENT)} commands"
    )
    parts.append(essentials)
    if session_count >= 3:
        tier1 = (
            f"{styled('/vocab', STYLE_ACCENT)} drill"
            f"  {styled('/models', STYLE_ACCENT)} model"
            f"  {styled('/theme', STYLE_ACCENT)} theme"
        )
        parts.append(tier1)
    if session_count >= 5:
        tier2 = f"{styled('!', STYLE_ACCENT)} shell  {styled('\\', STYLE_DIM)} continuation"
        parts.append(tier2)
    return parts


def print_shell_intro(
    version: str,
    armory_path: str,
    source_file_count: int,
    model: str,
    has_api_key: bool,
    source_files: tuple[str, ...] = (),
    *,
    is_keyless: bool = False,
) -> None:
    """Print a compact startup screen with essential status and input hints."""
    if has_api_key and not is_keyless:
        api_status = styled("configured", STYLE_SUCCESS)
    elif is_keyless:
        api_status = styled("free", STYLE_DIM)
    else:
        api_status = styled("missing", STYLE_ERROR)
    source_status = (
        styled(_format_source_summary(source_file_count, source_files), STYLE_DIM)
        if source_file_count
        else styled("none", STYLE_DIM)
    )
    armory_style = STYLE_DIM if armory_path != "none" else STYLE_EMBER
    model_text = model or "none"
    model_style = STYLE_SUCCESS if model else STYLE_EMBER

    settings = load_app_settings()
    hints = _progressive_hints(settings.session_count)

    print(ascii_logo())
    print()
    print(separator_line(60))
    print()
    print(
        f"{wordmark()} {styled(f'v{version}', STYLE_DIM)}"
        f"  {styled('\u2502', STYLE_DIM)}  "
        f"{styled('armory', STYLE_DIM)} {styled(armory_path, armory_style)}"
        f" {styled('\u00b7', STYLE_DIM)} "
        f"{styled('model', STYLE_DIM)} {styled(model_text, model_style)}"
        f" {styled('\u00b7', STYLE_DIM)} "
        f"{styled('api', STYLE_DIM)} {api_status}"
        f" {styled('\u00b7', STYLE_DIM)} "
        f"{styled('materials', STYLE_DIM)} {source_status}"
    )
    for hint_line in hints:
        print(f"  {hint_line}")
    if not has_api_key and not is_keyless:
        print(
            f"  {styled('connect model access', STYLE_WARNING)} {styled('/login', STYLE_ACCENT)}"
        )
    print()


def format_shell_header(
    version: str,
    armory_path: str,
    source_file_count: int,
    model: str,
    has_api_key: bool,
    source_files: tuple[str, ...] = (),
    *,
    is_keyless: bool = False,
) -> list[tuple[str, str]]:
    """Return FormattedText fragments for the fullscreen header bar."""
    if has_api_key and not is_keyless:
        api_status = "configured"
        api_style = "class:header.success"
    elif is_keyless:
        api_status = "free"
        api_style = "class:header.dim"
    else:
        api_status = "missing"
        api_style = "class:header.error"
    model_text = model or "none"
    model_style = "class:header.configured" if model else "class:header.ember"
    source_text = _format_source_summary(source_file_count, source_files)
    source_style = "class:header.dim" if source_file_count else "class:header.ember"
    armory_style = "class:header.dim" if armory_path != "none" else "class:header.ember"

    fragments: list[tuple[str, str]] = [
        ("class:header.title", "\u2301 Hephaistos"),
        ("class:header.dim", f" v{version}"),
        ("class:header.dim", "  \u2502  "),
        ("class:header.dim", "armory "),
        (armory_style, armory_path),
        ("class:header.dim", " \u00b7 "),
        ("class:header.dim", "model "),
        (model_style, model_text),
        ("class:header.dim", " \u00b7 "),
        ("class:header.dim", "api "),
        (api_style, api_status),
        ("class:header.dim", " \u00b7 "),
        ("class:header.dim", "materials "),
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
    if not has_api_key and not is_keyless:
        fragments.extend(
            [
                ("", "\n"),
                ("class:header.warning", "  connect model access "),
                ("class:header.accent", "/login"),
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
