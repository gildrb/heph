from __future__ import annotations

import hephaistos.terminal as palette
from hephaistos.parameters.settings import THEME_PRESETS

_AA_NORMAL_TEXT_CONTRAST = 4.5


def _linear_channel(value: int) -> float:
    scaled = value / 255
    if scaled <= 0.04045:
        return scaled / 12.92
    return ((scaled + 0.055) / 1.055) ** 2.4


def _relative_luminance(hex_color: str) -> float:
    color = hex_color.removeprefix("#")
    red = _linear_channel(int(color[0:2], 16))
    green = _linear_channel(int(color[2:4], 16))
    blue = _linear_channel(int(color[4:6], 16))
    return (0.2126 * red) + (0.7152 * green) + (0.0722 * blue)


def _contrast_ratio(first: str, second: str) -> float:
    first_luminance = _relative_luminance(first)
    second_luminance = _relative_luminance(second)
    lighter = max(first_luminance, second_luminance)
    darker = min(first_luminance, second_luminance)
    return (lighter + 0.05) / (darker + 0.05)


def test_ansi_fg_returns_truecolor_escape_sequence() -> None:
    assert palette.ansi_fg("#1C1C1C") == "\033[38;2;28;28;28m"


def test_style_tokens_render_from_current_theme() -> None:
    palette.set_theme("forge")

    assert str(palette.STYLE_PROMPT) == f"{palette.BOLD}{palette.ansi_fg('#C8C8C8')}"
    assert str(palette.STYLE_BRAND) == f"{palette.BOLD}{palette.ansi_fg('#C65050')}"
    assert str(palette.STYLE_ACCENT) == str(palette.STYLE_PROMPT)
    assert str(palette.STYLE_DIM) == f"{palette.DIM}{palette.ansi_fg('#808080')}"
    assert str(palette.STYLE_SHORTCUT) == f"{palette.DIM}{palette.ansi_fg('#808080')}"
    assert str(palette.STYLE_EMBER) == str(palette.STYLE_BRAND)
    assert str(palette.STYLE_EMPHASIS) == str(palette.STYLE_PROMPT)
    assert str(palette.STYLE_ERROR) == f"{palette.BOLD}{palette.ansi_fg('#CC3333')}"
    assert str(palette.STYLE_SUCCESS) == f"{palette.BOLD}{palette.ansi_fg('#66BB6A')}"
    assert str(palette.STYLE_WARNING) == str(palette.STYLE_ACCENT)
    assert str(palette.STYLE_ASSISTANT) == str(palette.STYLE_PROMPT)


def test_high_contrast_keeps_emphasis_neutral_and_accent_for_attention() -> None:
    palette.set_theme("high_contrast")
    p = palette.current_palette()

    assert p.emphasis == p.text
    assert p.shortcut == p.dim
    assert p.emphasis != p.accent
    assert str(palette.STYLE_PROMPT) == f"{palette.BOLD}{palette.ansi_fg(p.emphasis)}"
    assert str(palette.STYLE_ASSISTANT) == str(palette.STYLE_PROMPT)
    assert str(palette.STYLE_ACCENT) == f"{palette.BOLD}{palette.ansi_fg(p.accent)}"
    assert str(palette.STYLE_SHORTCUT) == f"{palette.DIM}{palette.ansi_fg(p.shortcut)}"
    assert str(palette.STYLE_WARNING) == str(palette.STYLE_ACCENT)


def test_set_theme_switches_palette() -> None:
    palette.set_theme("light")

    assert palette.current_theme_name() == "light"
    p = palette.current_palette()
    assert p.text == "#2C241B"
    assert p.configured == "#6D804F"


def test_set_theme_ignores_unknown() -> None:
    palette.set_theme("nonexistent")

    assert palette.current_theme_name() == palette.DEFAULT_THEME


def test_current_palette_returns_forge_by_default() -> None:
    palette.set_theme("forge")
    p = palette.current_palette()

    assert p.name == "forge"
    assert p.brand == "#C65050"
    assert p.accent == "#C8C8C8"
    assert p.emphasis == "#C8C8C8"
    assert p.shortcut == "#808080"
    assert p.selection_background == "#B85A5A"
    assert p.selection_text == "#000000"


def test_all_theme_presets_are_valid_palettes() -> None:
    for theme_name in THEME_PRESETS:
        palette.set_theme(theme_name)
        p = palette.current_palette()
        assert p.name == theme_name
        assert p.text.startswith("#")
        assert p.brand.startswith("#")
        assert p.accent.startswith("#")
        assert p.emphasis.startswith("#")
        assert p.shortcut.startswith("#")
        assert p.highlight.startswith("#")
        assert p.selection_background.startswith("#")
        assert p.selection_text.startswith("#")
        assert p.material_enabled.startswith("#")
        assert p.material_disabled.startswith("#")


def test_interactive_theme_pairs_support_aa_contrast() -> None:
    for theme_name in THEME_PRESETS:
        palette.set_theme(theme_name)
        p = palette.current_palette()
        assert _contrast_ratio(p.brand, "#000000") >= _AA_NORMAL_TEXT_CONTRAST
        assert (
            _contrast_ratio(p.selection_background, p.selection_text) >= _AA_NORMAL_TEXT_CONTRAST
        )
        assert _contrast_ratio(p.material_enabled, p.selection_text) >= _AA_NORMAL_TEXT_CONTRAST
        assert _contrast_ratio(p.material_disabled, p.selection_text) >= _AA_NORMAL_TEXT_CONTRAST
