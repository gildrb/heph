from __future__ import annotations

import sys
from dataclasses import fields
from pathlib import Path

import interfaces.palette as theme_tokens
from hephaion.parameters.settings import DEFAULT_THEME, THEME_PRESETS

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI_DESIGN_PATH = REPO_ROOT / "cli-design.md"
WEB_DESIGN_PATH = REPO_ROOT / "design.md"


def _normal(value: object) -> str:
    return str(value).strip().lower()


def _split_table_line(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _extract_cli_theme_rows(text: str) -> dict[str, tuple[str, str]]:
    rows: dict[str, tuple[str, str]] = {}
    in_table = False
    for line in text.splitlines():
        cells = _split_table_line(line) if line.startswith("|") else []
        if cells[:4] == ["role", "dark", "light", "intent"]:
            in_table = True
            continue
        if not in_table:
            continue
        if not line.startswith("|"):
            break
        if len(cells) < 4 or set(cells[0]) <= {"-"}:
            continue
        role, dark_value, light_value = cells[:3]
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


def _expected_phrase_present(text: str) -> bool:
    return "Labels are uppercase; values are lowercase" in text


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
        errors.append("cli-design.md theme table does not match interfaces.palette.Theme")
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
    errors.extend(
        f"cli-design.md missing theme preset {theme_name!r}"
        for theme_name in THEME_PRESETS
        if f'  - "{theme_name}"' not in cli_text
    )
    for text, name in ((cli_text, "cli-design.md"), (web_text, "design.md")):
        if not _expected_phrase_present(text):
            errors.append(f"{name} missing label/value system rule")
    if "cli-design.md" not in web_text:
        errors.append("design.md does not reference cli-design.md")
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
