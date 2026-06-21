from __future__ import annotations

import sys
import tomllib
from dataclasses import fields
from pathlib import Path

import interfaces.palette as theme_tokens
from hephaion.parameters.settings import DEFAULT_THEME, THEME_PRESETS

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_DESIGN_PATH = REPO_ROOT / "cli-design.md"
WEB_DESIGN_PATH = REPO_ROOT / "design.md"
RELEASE_STATE_PATH = REPO_ROOT / "packages/heph/src/heph/state/release.toml"
BANNED_WEB_STACK_RECOMMENDATIONS = (
    "Next.js",
    "shadcn",
    "Radix",
    "Tailwind",
    "React",
    "Vue",
    "Svelte",
    "Astro",
)
EXPECTED_WEB_COLOR_SOURCES: dict[str, str] = {
    "colors.primary": "dark.brand_primary",
    "colors.secondary": "dark.text_secondary",
    "colors.tertiary": "dark.text_muted",
    "colors.accent": "dark.action_primary_bg",
    "colors.accent-foreground": "dark.action_primary_text",
    "colors.background-100": "dark.text_inverse",
    "colors.background-200": "dark.bg_raised",
    "colors.background-300": "dark.bg_surface",
    "colors.border": "dark.border_subtle",
    "colors.success": "dark.status_success_text",
    "colors.error": "dark.status_error_text",
    "colors.light.background-100": "light.bg_app",
    "colors.light.background-200": "light.bg_surface",
    "colors.light.background-300": "light.bg_raised",
    "colors.light.primary": "light.brand_primary",
    "colors.light.secondary": "light.text_secondary",
    "colors.light.tertiary": "light.text_muted",
    "colors.light.accent": "light.action_primary_bg",
    "colors.light.accent-foreground": "light.action_primary_text",
    "colors.light.border": "light.border_subtle",
    "colors.light.success": "light.status_success_text",
    "colors.light.error": "light.status_error_text",
}
EXPECTED_CSS_VARIABLES: dict[str, str] = {
    "--color-background": "#000000",
    "--color-foreground": "#ffffff",
    "--color-surface": "#161616",
    "--color-surface-foreground": "#cfcfcf",
    "--color-primary": "#ffffff",
    "--color-primary-foreground": "#000000",
    "--color-secondary": "#8f8f8f",
    "--color-tertiary": "#6f6f6f",
    "--color-accent": "#d06a4a",
    "--color-accent-foreground": "#000000",
    "--color-error": "#ff6b5a",
    "--color-success": "#57c785",
    "--color-border": "#3d3d3d",
    "--color-focus": "#d06a4a",
}
EXPECTED_LIGHT_CSS_VARIABLES: dict[str, str] = {
    "--color-background": "#fafafa",
    "--color-foreground": "#000000",
    "--color-surface": "#ffffff",
    "--color-surface-foreground": "#000000",
    "--color-primary": "#000000",
    "--color-primary-foreground": "#ffffff",
    "--color-secondary": "#404040",
    "--color-tertiary": "#666666",
    "--color-accent": "#0f7a3a",
    "--color-accent-foreground": "#ffffff",
    "--color-error": "#b00020",
    "--color-success": "#006b32",
    "--color-border": "#d9d9d9",
    "--color-focus": "#0f7a3a",
}


def _normal(value: object) -> str:
    return str(value).strip().lower()


def _extract_fenced_block(text: str, *, heading: str, language: str) -> str:
    lines = text.splitlines()
    in_section = False
    in_block = False
    block_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped == heading:
            in_section = True
            continue
        if in_section and stripped.startswith("## ") and stripped != heading:
            break
        if not in_section:
            continue
        if not in_block and stripped == f"```{language}":
            in_block = True
            continue
        if in_block and stripped == "```":
            return "\n".join(block_lines)
        if in_block:
            block_lines.append(line)
    return ""


def _extract_cli_theme_rows(text: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    block = _extract_fenced_block(text, heading="## CLI Theme Tokens", language="toml")
    if not block:
        return rows

    parsed = tomllib.loads(block)
    tokens = parsed.get("cli_theme_tokens")
    if not isinstance(tokens, dict):
        return rows
    for role, payload in tokens.items():
        if not isinstance(role, str) or not isinstance(payload, dict):
            continue
        dark_value = payload.get("dark")
        light_value = payload.get("light")
        if not isinstance(dark_value, str) or not isinstance(light_value, str):
            continue
        rows[role] = (_normal(dark_value), _normal(light_value))
    return rows


def _theme_rows_from_code() -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    for field in fields(theme_tokens.Theme):
        rows[field.name] = (
            _normal(getattr(theme_tokens.DARK, field.name)),
            _normal(getattr(theme_tokens.LIGHT, field.name)),
        )
    return rows


def _extract_web_color_sources(text: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    block = _extract_fenced_block(text, heading="## Source Mapping", language="toml")
    if not block:
        return rows

    parsed = tomllib.loads(block)
    colors = parsed.get("web_colors")
    if not isinstance(colors, dict):
        return rows
    for name, payload in colors.items():
        if not isinstance(name, str) or not isinstance(payload, dict):
            continue
        value = payload.get("value")
        cli_source = payload.get("cli_source")
        if not isinstance(value, str) or not isinstance(cli_source, str):
            continue
        rows[name] = (_normal(value), cli_source)
    return rows


def _source_value(source: str) -> str:
    theme_name, _, role = source.partition(".")
    if theme_name == "dark":
        return _normal(getattr(theme_tokens.DARK, role))
    if theme_name == "light":
        return _normal(getattr(theme_tokens.LIGHT, role))
    raise ValueError(f"unknown web color source {source!r}")


def _expected_web_color_rows() -> dict[str, tuple[str, str]]:
    return {
        name: (_source_value(source), source)
        for name, source in EXPECTED_WEB_COLOR_SOURCES.items()
    }


def _extract_css_variables(text: str, selector: str) -> dict[str, str]:
    block = _extract_fenced_block(text, heading="## CSS Token Contract", language="css")
    if not block:
        return {}
    marker = f"{selector} {{"
    start = block.find(marker)
    if start < 0:
        return {}
    body_start = start + len(marker)
    end = block.find("\n}", body_start)
    if end < 0:
        return {}

    rows: dict[str, str] = {}
    for line in block[body_start:end].splitlines():
        stripped = line.strip()
        if not stripped.startswith("--") or ":" not in stripped:
            continue
        name, _, value = stripped.rstrip(";").partition(":")
        rows[name.strip()] = _normal(value)
    return rows


def _expected_phrase_present(text: str) -> bool:
    return "Labels are uppercase; values are lowercase" in text


def _has_markdown_table_rows(text: str) -> bool:
    return any(line.startswith("|") for line in text.splitlines())


def _release_version() -> str:
    parsed = tomllib.loads(RELEASE_STATE_PATH.read_text(encoding="utf-8"))
    version = parsed.get("version")
    if not isinstance(version, str):
        raise TypeError("release state is missing version")
    return version


def _only_keys(rows: dict[str, str], expected: dict[str, str]) -> dict[str, str]:
    return {key: rows[key] for key in expected if key in rows}


def design_doc_errors() -> list[str]:
    errors: list[str] = []
    if not CLI_DESIGN_PATH.is_file():
        errors.append("missing cli-design.md")
        return errors
    if not WEB_DESIGN_PATH.is_file():
        errors.append("missing design.md")
        return errors

    cli_text = CLI_DESIGN_PATH.read_text(encoding="utf-8")
    web_text = WEB_DESIGN_PATH.read_text(encoding="utf-8")
    expected_rows = _theme_rows_from_code()
    documented_rows = _extract_cli_theme_rows(cli_text)

    if documented_rows != expected_rows:
        errors.append("cli-design.md theme token contract does not match interfaces.palette.Theme")
        missing = sorted(set(expected_rows) - set(documented_rows))
        extra = sorted(set(documented_rows) - set(expected_rows))
        if missing:
            errors.append(f"missing theme roles: {', '.join(missing)}")
        if extra:
            errors.append(f"extra theme roles: {', '.join(extra)}")
        errors.extend(
            (f"{role}: documented {documented_rows[role]!r}, expected {expected_rows[role]!r}")
            for role in sorted(set(expected_rows) & set(documented_rows))
            if expected_rows[role] != documented_rows[role]
        )

    if f'default_theme: "{DEFAULT_THEME}"' not in cli_text:
        errors.append("cli-design.md default_theme does not match DEFAULT_THEME")
    release_version = _release_version()
    for text, name in ((cli_text, "cli-design.md"), (web_text, "design.md")):
        if f'version: "{release_version}"' not in text:
            errors.append(f"{name} version does not match release state")
    errors.extend(
        f"cli-design.md missing theme preset {theme_name!r}"
        for theme_name in THEME_PRESETS
        if f'  - "{theme_name}"' not in cli_text
    )
    for text, name in ((cli_text, "cli-design.md"), (web_text, "design.md")):
        if not _expected_phrase_present(text):
            errors.append(f"{name} missing label/value system rule")
        if _has_markdown_table_rows(text):
            errors.append(f"{name} should use readable blocks instead of markdown tables")
    if "cli-design.md" not in web_text:
        errors.append("design.md does not reference cli-design.md")
    web_rows = _extract_web_color_sources(web_text)
    expected_web_rows = _expected_web_color_rows()
    if web_rows != expected_web_rows:
        errors.append("design.md web color mapping does not match interfaces.palette.Theme")
        missing = sorted(set(expected_web_rows) - set(web_rows))
        extra = sorted(set(web_rows) - set(expected_web_rows))
        if missing:
            errors.append(f"missing web colors: {', '.join(missing)}")
        if extra:
            errors.append(f"extra web colors: {', '.join(extra)}")
        errors.extend(
            f"{name}: documented {web_rows[name]!r}, expected {expected_web_rows[name]!r}"
            for name in sorted(set(expected_web_rows) & set(web_rows))
            if expected_web_rows[name] != web_rows[name]
        )
    css_variables = _extract_css_variables(web_text, ":root")
    if _only_keys(css_variables, EXPECTED_CSS_VARIABLES) != EXPECTED_CSS_VARIABLES:
        errors.append("design.md dark CSS variables do not match web color contract")
    light_css_variables = _extract_css_variables(web_text, ':root[data-theme="light"]')
    if (
        _only_keys(light_css_variables, EXPECTED_LIGHT_CSS_VARIABLES)
        != EXPECTED_LIGHT_CSS_VARIABLES
    ):
        errors.append("design.md light CSS variables do not match web color contract")
    errors.extend(
        f"design.md contains framework-specific stack recommendation: {phrase}"
        for phrase in BANNED_WEB_STACK_RECOMMENDATIONS
        if phrase in web_text
    )
    return errors


def main() -> int:
    errors = design_doc_errors()
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 1
    print("design docs match current CLI theme tokens")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
