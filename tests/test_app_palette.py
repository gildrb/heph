from __future__ import annotations

import pytest
from prompt_toolkit.styles import Style, merge_styles
from prompt_toolkit.styles.defaults import default_ui_style

from hephaistos.app import palette


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

    style_rules = palette.shell_style_dict()
    menu_style = palette.menu_style_dict()

    assert palette.current_theme_name() == "light"
    assert style_rules[""] == "bg:#F6F2EA fg:#2C241B"
    assert style_rules["composer"] == "bg:#F6F2EA fg:#2C241B"
    assert style_rules["header.title"] == "bg:#F6F2EA bold fg:#8E4A32"
    assert style_rules["header.configured"] == "bg:#F6F2EA fg:#687A4B"
    assert style_rules["header.success"] == style_rules["header.configured"]
    assert style_rules["toolbar-error"] == "noreverse bg:#F6F2EA bold fg:#B03A2E"
    assert menu_style[""] == "bg:#F6F2EA fg:#2C241B"


def test_menu_style_dict_uses_theme_background_instead_of_prompt_toolkit_default() -> None:
    palette.set_theme("light")

    merged_style = merge_styles([default_ui_style(), Style.from_dict(palette.menu_style_dict())])

    for style_name in (
        "inline-menu.title",
        "inline-menu.option",
        "inline-menu.option.current",
        "inline-menu.description",
        "inline-menu.description.current",
        "inline-menu.hint",
    ):
        attrs = merged_style.get_attrs_for_style_str(f"class:{style_name}")
        assert attrs.bgcolor == "F6F2EA"


_TOOLBAR_STYLES: tuple[str, ...] = (
    "bottom-toolbar",
    "bottom-toolbar.text",
    "toolbar-location",
    "toolbar-accent",
    "toolbar-error",
)

_MENU_STYLES: tuple[str, ...] = (
    "inline-menu.title",
    "inline-menu.option",
    "inline-menu.option.current",
    "inline-menu.description",
    "inline-menu.description.current",
    "inline-menu.hint",
)

_BROWSER_STYLES: tuple[str, ...] = (
    "browser.title",
    "browser.path",
    "browser.entry",
    "browser.entry.selected",
    "browser.parent",
    "browser.parent.selected",
    "browser.hint",
)


@pytest.mark.parametrize("theme", ["forge", "light", "high_contrast"])
def test_all_toolbar_styles_have_theme_background(theme: str) -> None:
    palette.set_theme(theme)
    expected_bg = palette.current_palette().panel.lstrip("#")
    merged = merge_styles([default_ui_style(), Style.from_dict(palette.shell_style_dict())])
    for style_name in _TOOLBAR_STYLES:
        attrs = merged.get_attrs_for_style_str(f"class:{style_name}")
        assert attrs.bgcolor == expected_bg, f"{style_name} bgcolor mismatch for theme {theme}"


@pytest.mark.parametrize("theme", ["forge", "light", "high_contrast"])
def test_all_menu_styles_have_theme_background(theme: str) -> None:
    palette.set_theme(theme)
    expected_bg = palette.current_palette().panel.lstrip("#")
    merged = merge_styles([default_ui_style(), Style.from_dict(palette.menu_style_dict())])
    for style_name in _MENU_STYLES:
        attrs = merged.get_attrs_for_style_str(f"class:{style_name}")
        assert attrs.bgcolor == expected_bg, f"{style_name} bgcolor mismatch for theme {theme}"


@pytest.mark.parametrize("theme", ["forge", "light", "high_contrast"])
def test_all_browser_styles_have_theme_background(theme: str) -> None:
    palette.set_theme(theme)
    expected_bg = palette.current_palette().panel.lstrip("#")
    merged = merge_styles([default_ui_style(), Style.from_dict(palette.browser_style_dict())])
    for style_name in _BROWSER_STYLES:
        attrs = merged.get_attrs_for_style_str(f"class:{style_name}")
        assert attrs.bgcolor == expected_bg, f"{style_name} bgcolor mismatch for theme {theme}"
