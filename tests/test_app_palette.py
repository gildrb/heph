from __future__ import annotations

import hephaistos.terminal as palette
from hephaistos.parameters.settings import THEME_PRESETS


def test_ansi_fg_returns_truecolor_escape_sequence() -> None:
    assert palette.ansi_fg("#1C1C1C") == "\033[38;2;28;28;28m"


def test_style_tokens_render_from_current_theme() -> None:
    palette.set_theme("forge")

    assert str(palette.STYLE_PROMPT) == f"{palette.BOLD}{palette.ansi_fg('#C8C8C8')}"
    assert str(palette.STYLE_ACCENT) == str(palette.STYLE_PROMPT)
    assert str(palette.STYLE_DIM) == f"{palette.DIM}{palette.ansi_fg('#808080')}"
    assert str(palette.STYLE_EMBER) == f"{palette.BOLD}{palette.ansi_fg('#9B4A2E')}"
    assert str(palette.STYLE_ERROR) == f"{palette.BOLD}{palette.ansi_fg('#CC3333')}"
    assert str(palette.STYLE_SUCCESS) == f"{palette.BOLD}{palette.ansi_fg('#66BB6A')}"
    assert str(palette.STYLE_WARNING) == str(palette.STYLE_PROMPT)
    assert str(palette.STYLE_ASSISTANT) == str(palette.STYLE_PROMPT)


def test_set_theme_switches_palette() -> None:
    palette.set_theme("light")

    assert palette.current_theme_name() == "light"
    p = palette.current_palette()
    assert p.text == "#2C241B"


def test_set_theme_ignores_unknown() -> None:
    palette.set_theme("nonexistent")

    assert palette.current_theme_name() == palette.DEFAULT_THEME


def test_current_palette_returns_forge_by_default() -> None:
    palette.set_theme("forge")
    p = palette.current_palette()

    assert p.name == "forge"
    assert p.accent == "#C8C8C8"


def test_all_theme_presets_are_valid_palettes() -> None:
    for theme_name in THEME_PRESETS:
        palette.set_theme(theme_name)
        p = palette.current_palette()
        assert p.name == theme_name
        assert p.text.startswith("#")
        assert p.accent.startswith("#")
        assert p.highlight.startswith("#")
