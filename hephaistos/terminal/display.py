"""ANSI terminal helpers: styling, prompt rendering."""

from __future__ import annotations

from hephaistos.parameters.settings import load_app_settings
from hephaistos.terminal import (  # re-export shared terminal primitives
    STYLE_ACCENT,
    STYLE_ASSISTANT,
    STYLE_CHROME_DETAIL,
    STYLE_CHROME_LABEL,
    STYLE_DIM,
    STYLE_ERROR,
    STYLE_METADATA,
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
    "STYLE_CHROME_DETAIL",
    "STYLE_CHROME_LABEL",
    "STYLE_METADATA",
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
    print(styled(msg, STYLE_SUCCESS))


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
    if has_api_key and not is_keyless:
        api_status = styled("configured", STYLE_SUCCESS)
    elif is_keyless:
        api_status = styled("free", STYLE_DIM)
    else:
        api_status = styled("missing", STYLE_ERROR)
    visible_sources = source_files[:3]
    if not source_file_count:
        source_text = "none"
    elif not visible_sources:
        source_text = f"{source_file_count} file{'s' if source_file_count != 1 else ''}"
    else:
        suffix = (
            f" +{source_file_count - len(visible_sources)}"
            if source_file_count > len(visible_sources)
            else ""
        )
        source_text = f"{', '.join(visible_sources)}{suffix}"
    source_status = styled(source_text, STYLE_DIM)
    armory_style = STYLE_CHROME_DETAIL if armory_path != "none" else STYLE_WARNING
    model_text = model or "none"
    model_style = STYLE_CHROME_DETAIL if model else STYLE_WARNING

    settings = load_app_settings()
    hints = [
        f"{styled('enter', STYLE_CHROME_LABEL)} {styled('send', STYLE_CHROME_DETAIL)}  "
        f"{styled('tab', STYLE_CHROME_LABEL)} {styled('complete', STYLE_CHROME_DETAIL)}",
        f"{styled('ctrl+c', STYLE_CHROME_LABEL)} {styled('interrupt', STYLE_CHROME_DETAIL)}"
        f"  {styled('ctrl+d', STYLE_CHROME_LABEL)} {styled('exit', STYLE_CHROME_DETAIL)}"
        f"  {styled('/help', STYLE_ACCENT)} {styled('commands', STYLE_CHROME_DETAIL)}",
    ]
    if settings.session_count >= 3:
        hints.append(
            f"{styled('/vocab', STYLE_ACCENT)} drill"
            f"  {styled('/models', STYLE_ACCENT)} model"
            f"  {styled('/theme', STYLE_ACCENT)} theme"
        )
    if settings.session_count >= 5:
        hints.append(
            f"{styled('!', STYLE_ACCENT)} shell  "
            f"{styled('\\', STYLE_CHROME_LABEL)} {styled('continuation', STYLE_CHROME_DETAIL)}"
        )

    print(ascii_logo())
    print()
    print(separator_line(60))
    print()
    print(
        f"{wordmark()} {styled(f'v{version}', STYLE_DIM)}"
        f"  {styled('\u2502', STYLE_DIM)}  "
        f"{styled('armory', STYLE_CHROME_LABEL)} {styled(armory_path, armory_style)}"
        f" {styled('\u00b7', STYLE_DIM)} "
        f"{styled('model', STYLE_CHROME_LABEL)} {styled(model_text, model_style)}"
        f" {styled('\u00b7', STYLE_DIM)} "
        f"{styled('api', STYLE_METADATA)} {api_status}"
        f" {styled('\u00b7', STYLE_DIM)} "
        f"{styled('materials', STYLE_CHROME_LABEL)} {source_status}"
    )
    for hint_line in hints:
        print(f"  {hint_line}")
    if not has_api_key and not is_keyless:
        print(
            f"  {styled('connect model access', STYLE_WARNING)} {styled('/login', STYLE_ACCENT)}"
        )
    print()
