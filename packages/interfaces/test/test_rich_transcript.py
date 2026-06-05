"""Tests for rich transcript rendering with inline evidence badges."""

from __future__ import annotations

from rag.chunker import Chunk
from rag.context import EvidenceChunk, TurnEvidence
from rich.console import Console
from rich.segment import Segment
from rich.style import Style
from terminal import current_palette
from tui.rich_transcript import (
    enrich_reply,
    evidence_summary_text,
    extract_cited_ids,
    normalize_markdown_tables,
)
from tui.transcript import _EvidenceMarkdown


def _make_chunk(source: str, index: int, text: str) -> Chunk:
    return Chunk(
        source=source,
        index=index,
        text=text,
        char_start=0,
        char_end=len(text),
    )


def _make_evidence(*items: tuple[str, str, int, float, str]) -> TurnEvidence:
    chunks: list[EvidenceChunk] = []
    for eid, source, idx, score, content in items:
        chunks.append(
            EvidenceChunk(
                evidence_id=eid,
                chunk=_make_chunk(source, idx, content),
                score=score,
                content=content,
            )
        )
    return TurnEvidence(tuple(chunks))


def _render_evidence_markdown(markdown_text: str) -> list[Segment]:
    console = Console(width=160)
    return list(
        console.render(
            _EvidenceMarkdown(markdown_text, Style.parse(f"dim {current_palette().text_muted}")),
        )
    )


def _assert_dim_gray(style: Style | None) -> None:
    assert style is not None
    assert style.dim is True
    assert style.color is not None
    color = style.color.get_truecolor()
    expected = current_palette().text_muted.removeprefix("#")
    assert (color.red, color.green, color.blue) == (
        int(expected[0:2], 16),
        int(expected[2:4], 16),
        int(expected[4:6], 16),
    )


def test_enrich_reply_with_no_evidence_returns_text_unchanged() -> None:
    result = enrich_reply("Hello world", None)
    assert result.markdown_text == "Hello world"
    assert result.evidence is None


def test_enrich_reply_with_empty_evidence_returns_text_unchanged() -> None:
    result = enrich_reply("Hello world", TurnEvidence())
    assert result.markdown_text == "Hello world"


def test_normalize_markdown_tables_keeps_compact_tables() -> None:
    markdown = "| Planet | Moons |\n|---|---:|\n| Earth | 1 |\n| Mars | 2 |\n"

    assert normalize_markdown_tables(markdown) == markdown


def test_normalize_markdown_tables_reflows_wide_tables() -> None:
    markdown = (
        "| Abschnitt | Inhalt | Nachgewiesene Quellen |\n"
        "|---|---|---|\n"
        "| Zahlensysteme & Elementare Funktionen | Grundlagen zu Zahlensystemen, "
        "Einführung in elementare Funktionen und sehr lange erklärende Hinweise | "
        "[E1] - Zahlensysteme, [E2] - Elementare Funktionen |\n"
        "| Folgen | Definition einer Folge, Beispiele, Notation | [E3] - Folgen |\n"
    )

    rendered = normalize_markdown_tables(markdown)

    assert "|---|---|---|" not in rendered
    assert "- **Abschnitt:** Zahlensysteme & Elementare Funktionen" in rendered
    assert "  - **Inhalt:** Grundlagen zu Zahlensystemen" in rendered
    assert "  - **Nachgewiesene Quellen:** [E1]" in rendered
    assert "- **Abschnitt:** Folgen" in rendered


def test_normalize_markdown_tables_ignores_code_fences() -> None:
    markdown = (
        "```markdown\n"
        "| Section | Content |\n"
        "|---|---|\n"
        "| A | A very long cell that should remain literal inside the code fence. |\n"
        "```\n"
    )

    assert normalize_markdown_tables(markdown) == markdown


def test_enrich_reply_appends_evidence_panel() -> None:
    evidence = _make_evidence(
        ("E1", "source/algorithms.md", 0, 0.85, "Binary search is O(log n)."),
    )
    result = enrich_reply("The answer is O(log n) [E1].", evidence)

    assert "[E1]" in result.markdown_text
    assert "sources" in result.markdown_text
    assert "algorithms.md" in result.markdown_text
    assert "Details: /evidence" in result.markdown_text
    assert "Binary search is O(log n)" not in result.markdown_text


def test_enrich_reply_with_multiple_evidence_chunks() -> None:
    evidence = _make_evidence(
        ("E1", "source/algorithms.md", 0, 0.90, "First chunk."),
        ("E2", "source/datastructures.md", 1, 0.75, "Second chunk."),
    )
    result = enrich_reply("See [E1] and [E2].", evidence)

    assert "E1" in result.markdown_text
    assert "E2" in result.markdown_text
    assert "algorithms.md" in result.markdown_text
    assert "datastructures.md" in result.markdown_text


def test_extract_cited_ids_finds_single_citation() -> None:
    ids = extract_cited_ids("The answer is [E1].")
    assert ids == ["E1"]


def test_extract_cited_ids_finds_multiple_in_one_bracket() -> None:
    ids = extract_cited_ids("See [E1, E2] for details.")
    assert ids == ["E1", "E2"]


def test_extract_cited_ids_deduplicates() -> None:
    ids = extract_cited_ids("[E1] and again [E1]")
    assert ids == ["E1"]


def test_extract_cited_ids_handles_lowercase() -> None:
    ids = extract_cited_ids("See [e3].")
    assert ids == ["E3"]


def test_extract_cited_ids_handles_fullwidth_brackets() -> None:
    ids = extract_cited_ids("See 【E1, E2】.")
    assert ids == ["E1", "E2"]


def test_extract_cited_ids_returns_empty_for_no_citations() -> None:
    ids = extract_cited_ids("No citations here.")
    assert ids == []


def test_evidence_summary_text_with_no_evidence() -> None:
    assert evidence_summary_text(None) == "no evidence"
    assert evidence_summary_text(TurnEvidence()) == "no evidence"


def test_evidence_summary_text_with_single_source() -> None:
    evidence = _make_evidence(
        ("E1", "source/algorithms.md", 0, 0.9, "chunk1"),
        ("E2", "source/algorithms.md", 1, 0.8, "chunk2"),
    )
    summary = evidence_summary_text(evidence)
    assert "2 evidence item(s)" in summary
    assert "algorithms.md" in summary


def test_evidence_summary_text_with_multiple_sources() -> None:
    evidence = _make_evidence(
        ("E1", "source/algorithms.md", 0, 0.9, "chunk1"),
        ("E2", "source/datastructures.md", 0, 0.8, "chunk2"),
    )
    summary = evidence_summary_text(evidence)
    assert "2 evidence item(s)" in summary
    assert "2 source(s)" in summary


def test_evidence_panel_omits_chunk_preview_content() -> None:
    long_text = "A" * 500
    evidence = _make_evidence(("E1", "source/long.md", 0, 0.5, long_text))
    result = enrich_reply("See [E1].", evidence)

    assert "long.md" in result.markdown_text
    assert "Details: /evidence" in result.markdown_text
    assert long_text not in result.markdown_text


def test_evidence_panel_keeps_diagnostic_details_out_of_visible_reply() -> None:
    evidence = _make_evidence(
        ("E1", "materials/week-02-slides.pdf", 2, 0.5, "slide content"),
        ("E2", "materials/past-exam.pdf", 4, 0.4, "exam content"),
    )
    result = enrich_reply("See [E1] and [E2].", evidence)

    assert "score " not in result.markdown_text
    assert "open: /evidence" not in result.markdown_text
    assert "materials/week-02-slides.pdf" not in result.markdown_text
    assert "materials/past-exam.pdf" not in result.markdown_text


def test_evidence_panel_uses_reader_friendly_location_labels() -> None:
    evidence = _make_evidence(
        ("E1", "materials/week-02-slides.pdf", 2, 0.5, "slide content"),
    )
    result = enrich_reply("See [E1].", evidence)

    assert "slide/deck excerpt 3" in result.markdown_text
    assert "chars " not in result.markdown_text
    assert "chunk" not in result.markdown_text.lower()


def test_enrich_reply_formats_common_latex_inline_math() -> None:
    evidence = _make_evidence(("E1", "source/math.md", 0, 0.5, "math"))
    result = enrich_reply(
        r"Every $N\ge 2$ has examples $24 = 2^3\cdot3$ [E1].",
        evidence,
    )

    assert r"$N\ge 2$" not in result.markdown_text
    assert "N≥ 2" in result.markdown_text
    assert "2³⋅3" in result.markdown_text


def test_enrich_reply_formats_bare_latex_font_math() -> None:
    result = enrich_reply(
        r"Sequences are maps \mathbb N \to M and often use \mathbb R or \mathbb C.",
        None,
    )

    assert r"\mathbb" not in result.markdown_text
    assert "\u2115 \u2192 M" in result.markdown_text
    assert "\u211d or \u2102" in result.markdown_text


def test_enrich_reply_does_not_mangle_markdown_table_separators_or_words() -> None:
    result = enrich_reply(
        r"""| Topic | Content |
|---|---|
| Limit | \lim_{x\to x_0} f(x)=f(x_0) |

Rechen- und Beweisaufgaben.""",
        None,
    )

    assert "|---|---|" in result.markdown_text
    assert "Rechen- und Beweisaufgaben" in result.markdown_text
    assert "łim" not in result.markdown_text
    assert "limₓ→ ₓ₀ f(x)=f(x₀)" in result.markdown_text


def test_enrich_reply_formats_math_without_evidence() -> None:
    result = enrich_reply(
        r"Euler gives \(\sum_{n=1}^{\infty}\frac{1}{n^{2}}=\frac{\pi ^{2}}{6}\).",
        None,
    )

    assert r"\sum" not in result.markdown_text
    assert r"\frac" not in result.markdown_text
    assert "∑ₙ₌₁^∞1/n²=π²/6" in result.markdown_text


def test_enrich_reply_formats_undelimited_latex_math() -> None:
    result = enrich_reply(
        r"""Let

[ a_n=\frac{1}{n^{2}}, \qquad n=1,2,\dots ]

The infinite series

[ S=\sum_{n=1}^{\infty}\frac{1}{n^{2}} ]

converges and its value is closed-form:

[ S=\frac{\pi ^{2}}{6}. ]

A demonstration uses \left.\frac{d^{2}}{dx^{2}}x^{2}\right|_{x=0}.""",
        None,
    )

    assert r"\frac" not in result.markdown_text
    assert r"\sum" not in result.markdown_text
    assert r"\pi" not in result.markdown_text
    assert r"\qquad" not in result.markdown_text
    assert r"\dots" not in result.markdown_text
    assert "≤ft" not in result.markdown_text
    assert "aₙ=1/n²" in result.markdown_text
    assert "n=1,2,…" in result.markdown_text
    assert "S=∑ₙ₌₁^∞1/n²" in result.markdown_text
    assert "S=π²/6" in result.markdown_text
    assert "d²/dx²x²|ₓ₌₀" in result.markdown_text


def test_enrich_reply_preserves_code_while_formatting_raw_math() -> None:
    result = enrich_reply(
        r"""Keep inline code `x_1 = \left` unchanged.

```python
x_1 = "\left"
```

But format math: \sum_{n=1}^{\infty}\frac{1}{n^{2}}.""",
        None,
    )

    assert r"`x_1 = \left`" in result.markdown_text
    assert 'x_1 = "\\left"' in result.markdown_text
    assert "∑ₙ₌₁^∞1/n²" in result.markdown_text


def test_evidence_footer_shows_only_cited_evidence_when_available() -> None:
    evidence = _make_evidence(
        ("E1", "source/a.md", 0, 0.5, "a"),
        ("E2", "source/b.md", 1, 0.5, "b"),
    )
    result = enrich_reply("See [E2].", evidence)

    assert "E2: b.md" in result.markdown_text
    assert "E1: a.md" not in result.markdown_text


def test_evidence_footer_summarizes_uncited_evidence() -> None:
    evidence = _make_evidence(
        ("E1", "source/a.md", 0, 0.5, "a"),
        ("E2", "source/b.md", 1, 0.5, "b"),
    )
    result = enrich_reply("No citations in this answer.", evidence)

    assert "2 evidence excerpts from 2 sources" in result.markdown_text
    assert "E1: a.md" not in result.markdown_text
    assert "E2: b.md" not in result.markdown_text
    assert "Details: /evidence" in result.markdown_text


def test_evidence_footer_caps_many_cited_sources() -> None:
    evidence = _make_evidence(
        ("E1", "source/a.md", 0, 0.5, "a"),
        ("E2", "source/b.md", 1, 0.5, "b"),
        ("E3", "source/c.md", 2, 0.5, "c"),
        ("E4", "source/d.md", 3, 0.5, "d"),
    )
    result = enrich_reply("See [E1], [E2], [E3], and [E4].", evidence)

    assert "E1: a.md" in result.markdown_text
    assert "E3: c.md" in result.markdown_text
    assert "E4: d.md" not in result.markdown_text
    assert "+1 more cited source" in result.markdown_text


def test_evidence_markdown_dims_inline_citations() -> None:
    segments = _render_evidence_markdown("See [E1] and [E2].\n\n_sources: E1: a.md (excerpt 1)._")
    citation_segments = [segment for segment in segments if segment.text in {"[E1]", "[E2]"}]

    assert len(citation_segments) == 2
    for segment in citation_segments:
        _assert_dim_gray(segment.style)


def test_evidence_markdown_dims_sources_footer() -> None:
    segments = _render_evidence_markdown(
        "See [E1].\n\n_sources: E1: a.md (excerpt 1); +1 more cited source. Details: /evidence_"
    )
    source_segments = [
        segment
        for segment in segments
        if "sources:" in segment.text or "+1 more" in segment.text or "/evidence" in segment.text
    ]

    assert source_segments
    for segment in source_segments:
        _assert_dim_gray(segment.style)
