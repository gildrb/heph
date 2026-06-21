from __future__ import annotations

from scripts.check_design_docs import (
    _extract_cli_theme_rows,
    _extract_css_variables,
    _has_markdown_table_rows,
    design_doc_errors,
)


def test_design_docs_match_current_theme_tokens() -> None:
    assert design_doc_errors() == []


def test_cli_theme_contract_parser_reads_documented_roles() -> None:
    text = """
## CLI Theme Tokens

```toml
[cli_theme_tokens.bg_app]
dark = "transparent"
light = "#fafafa"
intent = "Root."

[cli_theme_tokens.text_primary]
dark = "#cfcfcf"
light = "#000000"
intent = "Text."
```

## Next Section
""".lstrip()

    assert _extract_cli_theme_rows(text) == {
        "bg_app": ("transparent", "#fafafa"),
        "text_primary": ("#cfcfcf", "#000000"),
    }


def test_markdown_table_detector_flags_pipe_rows() -> None:
    assert _has_markdown_table_rows("| token | value |")
    assert not _has_markdown_table_rows("- token\n  - value: 1")


def test_css_variable_parser_reads_selected_contract_block() -> None:
    text = """
## CSS Token Contract

```css
:root {
  --color-background: #000000;
  --color-primary: #ffffff;
}

:root[data-theme="light"] {
  --color-background: #fafafa;
}
```
""".lstrip()

    assert _extract_css_variables(text, ":root") == {
        "--color-background": "#000000",
        "--color-primary": "#ffffff",
    }
    assert _extract_css_variables(text, ':root[data-theme="light"]') == {
        "--color-background": "#fafafa",
    }
