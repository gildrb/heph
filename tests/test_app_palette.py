from __future__ import annotations

from hephaistos.app import palette


def test_ansi_fg_returns_truecolor_escape_sequence() -> None:
    assert palette.ansi_fg("#1C1C1C") == "\033[38;2;28;28;28m"


def test_style_constants_are_composed_from_palette_values() -> None:
    assert f"{palette.BOLD}{palette.ansi_fg(palette.FORGE_EMBER)}" == palette.STYLE_PROMPT
    assert palette.STYLE_ACCENT == palette.STYLE_PROMPT
    assert f"{palette.DIM}{palette.ansi_fg(palette.FORGE_SMOKE)}" == palette.STYLE_DIM
    assert f"{palette.BOLD}{palette.ansi_fg(palette.FORGE_IRON)}" == palette.STYLE_ERROR
    assert f"{palette.BOLD}{palette.ansi_fg(palette.FORGE_GREEN)}" == palette.STYLE_SUCCESS
    assert palette.STYLE_WARNING == palette.STYLE_PROMPT
    assert palette.STYLE_ASSISTANT == palette.STYLE_PROMPT
