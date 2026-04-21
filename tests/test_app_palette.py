from __future__ import annotations

from hephaistos.app import palette


def test_ansi_fg_returns_truecolor_escape_sequence() -> None:
    assert palette.ansi_fg("#1C1C1C") == "\033[38;2;28;28;28m"


def test_style_tokens_render_from_current_theme() -> None:
    palette.set_theme("forge")

    assert str(palette.STYLE_PROMPT) == f"{palette.BOLD}{palette.ansi_fg('#C8C8C8')}"
    assert str(palette.STYLE_ACCENT) == str(palette.STYLE_PROMPT)
    assert str(palette.STYLE_DIM) == f"{palette.DIM}{palette.ansi_fg('#808080')}"
    assert str(palette.STYLE_ERROR) == f"{palette.BOLD}{palette.ansi_fg('#CC3333')}"
    assert str(palette.STYLE_SUCCESS) == f"{palette.BOLD}{palette.ansi_fg('#66BB6A')}"
    assert str(palette.STYLE_WARNING) == str(palette.STYLE_PROMPT)
    assert str(palette.STYLE_ASSISTANT) == str(palette.STYLE_PROMPT)


def test_set_theme_switches_palette() -> None:
    palette.set_theme("light")

    style_rules = palette.shell_style_dict()

    assert palette.current_theme_name() == "light"
    assert style_rules["composer"] == "bg:#F6F2EA fg:#2C241B"
    assert style_rules["toolbar-error"] == "noreverse bold fg:#B03A2E"
