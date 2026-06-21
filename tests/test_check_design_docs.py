from __future__ import annotations

from scripts.check_design_docs import _extract_cli_theme_rows, design_doc_errors


def test_design_docs_match_current_theme_tokens() -> None:
    assert design_doc_errors() == []


def test_cli_theme_table_parser_reads_documented_roles() -> None:
    text = """
## CLI Theme Tokens

| role | dark | light | intent |
|---|---|---|---|
| bg_app | transparent | #fafafa | Root. |
| text_primary | #cfcfcf | #000000 | Text. |

## Next Section
""".lstrip()

    assert _extract_cli_theme_rows(text) == {
        "bg_app": ("transparent", "#fafafa"),
        "text_primary": ("#cfcfcf", "#000000"),
    }
