from __future__ import annotations

import ast
import re
from dataclasses import fields
from pathlib import Path

import hephaistos.terminal as palette
import hephaistos.terminal.palette as theme_tokens
from hephaistos.parameters.settings import THEME_PRESETS

_AA_NORMAL_TEXT_CONTRAST = 4.5
_AA_LARGE_TEXT_CONTRAST = 3.0
_COLOR_HEX_RE = re.compile(r"#[0-9A-Fa-f]{3,8}\b")
_NAMED_COLOR_RE = re.compile(
    r"(?<![A-Za-z])(?:black|white|red|green|blue|yellow|cyan|magenta|transparent)(?![A-Za-z])",
    re.IGNORECASE,
)
_COLOR_TOKEN_SOURCE = Path("hephaistos/terminal/palette.py")


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


def _docstring_positions(tree: ast.AST) -> set[tuple[int, int]]:
    positions: set[tuple[int, int]] = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(body, list) or not body:
            continue
        first = body[0]
        if not isinstance(first, ast.Expr):
            continue
        value = first.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            positions.add((value.lineno, value.col_offset))
    return positions


def _iter_string_literals(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstring_positions = _docstring_positions(tree)
    literals: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        if (node.lineno, node.col_offset) in docstring_positions:
            continue
        literals.append((node.lineno, node.value))
    return literals


def test_ansi_fg_returns_truecolor_escape_sequence() -> None:
    palette.set_theme("forge")
    color = palette.current_palette().bg_raised
    r = int(color[1:3], 16)
    g = int(color[3:5], 16)
    b = int(color[5:7], 16)

    assert palette.ansi_fg(color) == f"\033[38;2;{r};{g};{b}m"


def test_style_tokens_render_from_current_theme() -> None:
    palette.set_theme("forge")
    p = palette.current_palette()

    assert str(palette.STYLE_PROMPT) == f"{palette.BOLD}{palette.ansi_fg(p.text_primary)}"
    assert str(palette.STYLE_BRAND) == f"{palette.BOLD}{palette.ansi_fg(p.brand_primary)}"
    assert str(palette.STYLE_ACCENT) == f"{palette.BOLD}{palette.ansi_fg(p.action_primary_bg)}"
    assert str(palette.STYLE_DIM) == f"{palette.DIM}{palette.ansi_fg(p.text_muted)}"
    assert str(palette.STYLE_CHROME_LABEL) == palette.ansi_fg(p.text_secondary)
    assert str(palette.STYLE_CHROME_DETAIL) == palette.ansi_fg(p.text_muted)
    assert str(palette.STYLE_SHORTCUT) == palette.ansi_fg(p.text_secondary)
    assert str(palette.STYLE_METADATA) == palette.ansi_fg(p.text_secondary)
    assert str(palette.STYLE_SHORTCUT) == str(palette.STYLE_METADATA)
    assert str(palette.STYLE_CHROME_LABEL) == str(palette.STYLE_METADATA)
    assert str(palette.STYLE_EMBER) == str(palette.STYLE_BRAND)
    assert str(palette.STYLE_EMPHASIS) == str(palette.STYLE_PROMPT)
    assert str(palette.STYLE_ERROR) == f"{palette.BOLD}{palette.ansi_fg(p.status_error_text)}"
    assert str(palette.STYLE_SUCCESS) == f"{palette.BOLD}{palette.ansi_fg(p.action_primary_bg)}"
    assert str(palette.STYLE_WARNING) == str(palette.STYLE_ACCENT)
    assert str(palette.STYLE_ASSISTANT) == str(palette.STYLE_PROMPT)


def test_high_contrast_keeps_emphasis_neutral_and_accent_for_attention() -> None:
    palette.set_theme("high_contrast")
    p = palette.current_palette()

    assert p.text_primary != p.action_primary_bg
    assert p.text_secondary == p.text_muted
    assert str(palette.STYLE_PROMPT) == f"{palette.BOLD}{palette.ansi_fg(p.text_primary)}"
    assert str(palette.STYLE_ASSISTANT) == str(palette.STYLE_PROMPT)
    assert str(palette.STYLE_ACCENT) == f"{palette.BOLD}{palette.ansi_fg(p.action_primary_bg)}"
    assert str(palette.STYLE_CHROME_LABEL) == palette.ansi_fg(p.text_secondary)
    assert str(palette.STYLE_CHROME_DETAIL) == palette.ansi_fg(p.text_muted)
    assert str(palette.STYLE_SHORTCUT) == palette.ansi_fg(p.text_secondary)
    assert str(palette.STYLE_WARNING) == str(palette.STYLE_ACCENT)


def test_theme_exposes_only_semantic_colour_roles() -> None:
    assert [field.name for field in fields(theme_tokens.Theme)] == [
        "bg_app",
        "bg_surface",
        "bg_raised",
        "text_primary",
        "text_secondary",
        "text_muted",
        "text_inverse",
        "border_subtle",
        "brand_primary",
        "action_primary_bg",
        "action_primary_text",
        "status_error_text",
    ]


def test_set_theme_switches_palette() -> None:
    palette.set_theme("light")

    assert palette.current_theme_name() == "light"
    p = palette.current_palette()
    assert p == theme_tokens.LIGHT


def test_set_theme_ignores_unknown() -> None:
    palette.set_theme("nonexistent")

    assert palette.current_theme_name() == palette.DEFAULT_THEME


def test_current_palette_returns_forge_by_default() -> None:
    palette.set_theme("forge")

    assert palette.current_palette() == theme_tokens.FORGE_THEME


def test_light_theme_matches_token_contract() -> None:
    assert (
        theme_tokens.Theme(
            bg_app="#f8f9fa",
            bg_surface="#ffffff",
            bg_raised="#ffffff",
            text_primary="#212529",
            text_secondary="#495057",
            text_muted="#868e96",
            text_inverse="#ffffff",
            border_subtle="#dee2e6",
            brand_primary="#e03131",
            action_primary_bg="#228be6",
            action_primary_text="#ffffff",
            status_error_text="#e03131",
        )
        == theme_tokens.LIGHT
    )


def test_all_theme_presets_are_valid_palettes() -> None:
    for theme_name in THEME_PRESETS:
        palette.set_theme(theme_name)
        p = palette.current_palette()
        assert p == theme_tokens.THEMES[theme_name]
        assert p.bg_app == theme_tokens.TRANSPARENT or p.bg_app.startswith("#")
        assert p.bg_surface == theme_tokens.TRANSPARENT or p.bg_surface.startswith("#")
        assert p.bg_raised.startswith("#")
        assert p.text_primary.startswith("#")
        assert p.text_secondary.startswith("#")
        assert p.text_muted.startswith("#")
        assert p.text_inverse.startswith("#")
        assert p.border_subtle.startswith("#")
        assert p.brand_primary.startswith("#")
        assert p.action_primary_bg.startswith("#")
        assert p.action_primary_text.startswith("#")
        assert p.status_error_text.startswith("#")


def test_interactive_theme_pairs_support_readable_contrast() -> None:
    for theme_name in THEME_PRESETS:
        palette.set_theme(theme_name)
        p = palette.current_palette()
        assert (
            _contrast_ratio(p.action_primary_bg, p.action_primary_text) >= _AA_LARGE_TEXT_CONTRAST
        )
        assert _contrast_ratio(p.status_error_text, p.bg_raised) >= _AA_NORMAL_TEXT_CONTRAST


def test_palette_roles_support_aa_contrast_on_theme_surfaces() -> None:
    foreground_roles = (
        "text_primary",
        "text_secondary",
        "brand_primary",
        "status_error_text",
    )

    for theme_name in THEME_PRESETS:
        palette.set_theme(theme_name)
        p = palette.current_palette()
        for foreground_role in foreground_roles:
            foreground = getattr(p, foreground_role)
            assert _contrast_ratio(foreground, p.bg_raised) >= _AA_NORMAL_TEXT_CONTRAST, (
                f"{theme_name}.{foreground_role} on bg_raised lacks AA contrast"
            )
        assert _contrast_ratio(p.text_muted, p.bg_raised) >= _AA_LARGE_TEXT_CONTRAST
        assert _contrast_ratio(p.action_primary_bg, p.bg_raised) >= _AA_LARGE_TEXT_CONTRAST


def test_app_source_has_no_loose_color_literals_outside_theme_tokens() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    allowed_paths = {repo_root / _COLOR_TOKEN_SOURCE}
    failures: list[str] = []

    for path in (repo_root / "hephaistos").rglob("*.py"):
        if path in allowed_paths:
            continue
        for line_number, literal in _iter_string_literals(path):
            if _COLOR_HEX_RE.search(literal) or _NAMED_COLOR_RE.search(literal):
                rel = path.relative_to(repo_root)
                failures.append(f"{rel}:{line_number}: {literal!r}")

    assert failures == []
