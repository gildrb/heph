"""Rich transcript rendering with inline evidence badges and source panels."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from harness.rag.context import TurnEvidence
from harness.rag.source_mapping import evidence_location_label

try:
    from unicodeit import replace as _unicodeit_replace
except ImportError:  # pragma: no cover - optional display enhancement
    _unicodeit_replace: Callable[[str], str] | None = None

_CITATION_RE = re.compile(r"(?:\[|【)([Ee]\d+(?:\s*[,;]\s*[Ee]\d+)*)(?:\]|】)")
_SINGLE_ID_RE = re.compile(r"[Ee](\d+)")
_LATEX_INLINE_RE = re.compile(r"\\\((.*?)\\\)", re.DOTALL)
_LATEX_BLOCK_RE = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)
_MATH_SPAN_RE = re.compile(r"\$(?!\$)(.+?)(?<!\$)\$", re.DOTALL)
_LATEX_FRACTION_RE = re.compile(r"\\(?:dfrac|tfrac|frac)\{([^{}]+)\}\{([^{}]+)\}")
_LATEX_BRACED_SCRIPT_RE = re.compile(r"([_^])\{([^{}]+)\}")
_LATEX_SUPERSCRIPT_SPACING_RE = re.compile(r"(?<=[A-Za-z\u0370-\u03FF])\s+([⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾])")
_LATEX_BARE_FONT_COMMAND_RE = re.compile(
    r"\\(?P<command>(?:mathbb|mathbf|mathrm|mathit|mathsf|mathtt|mathcal|mathfrak))"
    r"\s+(?P<symbol>[A-Za-z])\b"
)
_LATEX_FONT_COMMAND_RE = re.compile(
    r"\\(?:mathbb|mathbf|mathrm|mathit|mathsf|mathtt|mathcal|mathfrak)\{[^{}]+\}"
)
_LATEX_COMMAND_REPLACEMENTS = {
    r"\displaystyle": "",
    r"\left.": "",
    r"\left": "",
    r"\right": "",
    r"\qquad": " ",
    r"\quad": " ",
    r"\dots": "…",
    r"\,": " ",
    r"\;": " ",
    r"\:": " ",
    r"\!": "",
    r"\lim": "lim",
}
_LATEX_SYMBOL_REPLACEMENTS = {
    r"\cdot": "⋅",
    r"\dots": "…",
    r"\epsilon": "ε",
    r"\varepsilon": "ε",
    r"\delta": "δ",
    r"\geq": "≥",
    r"\ge": "≥",
    r"\in": "∈",
    r"\infty": "∞",
    r"\leq": "≤",
    r"\le": "≤",
    r"\neq": "≠",
    r"\pi": "π",
    r"\phi": "φ",
    r"\varphi": "φ",
    r"\sum": "∑",
    r"\times": "\u00d7",
    r"\to": "→",
}
_LATEX_SIMPLE_SCRIPT_RE = re.compile(r"([_^])([A-Za-z0-9+\-=()])")
_SUBSCRIPT_CHARS = str.maketrans(
    {
        "0": "₀",
        "1": "₁",
        "2": "₂",
        "3": "₃",
        "4": "₄",
        "5": "₅",
        "6": "₆",
        "7": "₇",
        "8": "₈",
        "9": "₉",
        "+": "₊",
        "-": "₋",
        "=": "₌",
        "_": "",
        "(": "₍",
        ")": "₎",
        "n": "ₙ",
        "x": "ₓ",
    }
)
_SUPERSCRIPT_CHARS = str.maketrans("0123456789+-=()n", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿ")
_MARKDOWN_CODE_RE = re.compile(r"```.*?```|~~~.*?~~~|`[^`\n]+`", re.DOTALL)
_MARKDOWN_TABLE_SEPARATOR_RE = re.compile(r":?-{3,}:?")
_MAX_VISIBLE_SOURCE_ITEMS = 3
_READABLE_TABLE_WIDTH = 92
_READABLE_TABLE_CELL_WIDTH = 48


@dataclass(frozen=True, slots=True)
class EnrichedReply:
    markdown_text: str
    evidence: TurnEvidence | None


def _replace_latex_commands(text: str) -> str:
    formatted = _normalize_bare_latex_font_commands(text)
    formatted = _format_latex_font_commands(formatted)
    for latex, replacement in _LATEX_COMMAND_REPLACEMENTS.items():
        formatted = formatted.replace(latex, replacement)
    for latex, replacement in sorted(
        _LATEX_SYMBOL_REPLACEMENTS.items(), key=lambda item: len(item[0]), reverse=True
    ):
        formatted = formatted.replace(latex, replacement)
    formatted = _format_latex_scripts(formatted)
    formatted = _LATEX_BRACED_SCRIPT_RE.sub(
        lambda match: f"{match.group(1)}{match.group(2)}",
        formatted,
    )
    formatted = _LATEX_FRACTION_RE.sub(
        lambda match: f"{match.group(1)}/{match.group(2)}",
        formatted,
    )
    formatted = _LATEX_SUPERSCRIPT_SPACING_RE.sub(lambda match: match.group(1), formatted)
    return re.sub(r"[ \t]{2,}", " ", formatted)


def _normalize_bare_latex_font_commands(text: str) -> str:
    return _LATEX_BARE_FONT_COMMAND_RE.sub(
        lambda match: f"\\{match.group('command')}{{{match.group('symbol')}}}",
        text,
    )


def _format_latex_font_commands(text: str) -> str:
    if _unicodeit_replace is None:
        return text
    unicodeit_replace = _unicodeit_replace
    return _LATEX_FONT_COMMAND_RE.sub(lambda match: unicodeit_replace(match.group(0)), text)


def _format_latex_scripts(text: str) -> str:
    formatted = text
    while True:
        replaced = _LATEX_BRACED_SCRIPT_RE.sub(
            lambda match: _translate_script(match.group(2), subscript=match.group(1) == "_"),
            formatted,
        )
        if replaced == formatted:
            break
        formatted = replaced
    return _LATEX_SIMPLE_SCRIPT_RE.sub(
        lambda match: _translate_script(match.group(2), subscript=match.group(1) == "_"),
        formatted,
    )


def _translate_script(value: str, *, subscript: bool) -> str:
    table = _SUBSCRIPT_CHARS if subscript else _SUPERSCRIPT_CHARS
    translated = value.translate(table)
    if translated == value and not subscript:
        return f"^{value}"
    return translated


def _format_math_expression(expression: str) -> str:
    return _replace_latex_commands(expression.strip())


def _normalize_latex_delimiters(text: str) -> str:
    text = _LATEX_BLOCK_RE.sub(
        lambda match: f"\n{_format_math_expression(match.group(1))}\n",
        text,
    )
    text = _LATEX_INLINE_RE.sub(lambda match: f"${match.group(1).strip()}$", text)
    return _MATH_SPAN_RE.sub(lambda match: _format_math_expression(match.group(1)), text)


def normalize_math_output(text: str) -> str:
    pieces: list[str] = []
    last_end = 0
    for match in _MARKDOWN_CODE_RE.finditer(text):
        pieces.append(
            _replace_latex_commands(_normalize_latex_delimiters(text[last_end : match.start()]))
        )
        pieces.append(match.group(0))
        last_end = match.end()
    pieces.append(_replace_latex_commands(_normalize_latex_delimiters(text[last_end:])))
    return "".join(pieces)


def normalize_markdown_tables(text: str) -> str:
    """Convert wide markdown tables into stacked rows for narrow transcript panes."""
    pieces: list[str] = []
    last_end = 0
    for match in _MARKDOWN_CODE_RE.finditer(text):
        pieces.append(_normalize_markdown_tables_segment(text[last_end : match.start()]))
        pieces.append(match.group(0))
        last_end = match.end()
    pieces.append(_normalize_markdown_tables_segment(text[last_end:]))
    return "".join(pieces)


def _normalize_markdown_tables_segment(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text
    rendered: list[str] = []
    index = 0
    while index < len(lines):
        table_end = _table_block_end(lines, index)
        if table_end is None:
            rendered.append(lines[index])
            index += 1
            continue
        table_lines = lines[index:table_end]
        rendered.extend(_render_readable_table(table_lines))
        index = table_end
    return _restore_trailing_newline(text, "\n".join(rendered))


def _table_block_end(lines: list[str], start: int) -> int | None:
    if start + 1 >= len(lines):
        return None
    header = _split_table_row(lines[start])
    separator = _split_table_row(lines[start + 1])
    if not header or not _is_table_separator(separator) or len(header) != len(separator):
        return None
    end = start + 2
    while end < len(lines):
        cells = _split_table_row(lines[end])
        if not cells:
            break
        end += 1
    return end if end > start + 2 else None


def _split_table_row(line: str) -> tuple[str, ...]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|") or stripped.count("|") < 2:
        return ()
    return tuple(cell.strip() for cell in stripped.strip("|").split("|"))


def _is_table_separator(cells: tuple[str, ...]) -> bool:
    return bool(cells) and all(
        bool(_MARKDOWN_TABLE_SEPARATOR_RE.fullmatch(cell.replace(" ", ""))) for cell in cells
    )


def _render_readable_table(table_lines: list[str]) -> list[str]:
    headers = _split_table_row(table_lines[0])
    rows = [_split_table_row(line) for line in table_lines[2:]]
    if not _table_is_wide(headers, rows):
        return table_lines
    rendered: list[str] = []
    for row_number, row in enumerate(rows, start=1):
        rendered.extend(_render_table_record(headers, row, row_number=row_number))
    return rendered


def _table_is_wide(headers: tuple[str, ...], rows: list[tuple[str, ...]]) -> bool:
    widths = [len(header) for header in headers]
    for row in rows:
        for index, cell in enumerate(row[: len(widths)]):
            widths[index] = max(widths[index], len(cell))
    estimated_width = sum(widths) + (3 * max(0, len(widths) - 1))
    return estimated_width > _READABLE_TABLE_WIDTH or any(
        len(cell) > _READABLE_TABLE_CELL_WIDTH for row in rows for cell in row
    )


def _render_table_record(
    headers: tuple[str, ...],
    row: tuple[str, ...],
    *,
    row_number: int,
) -> list[str]:
    cells = _normalized_table_cells(headers, row)
    title_header, title_value = cells[0]
    title_label = title_header or f"Row {row_number}"
    title = title_value or f"Row {row_number}"
    lines = [f"- **{title_label}:** {title}"]
    for header, value in cells[1:]:
        label = header or "Value"
        lines.append(f"  - **{label}:** {value or 'not specified'}")
    return lines


def _normalized_table_cells(
    headers: tuple[str, ...],
    row: tuple[str, ...],
) -> tuple[tuple[str, str], ...]:
    cells: list[tuple[str, str]] = []
    for index, header in enumerate(headers):
        value = row[index] if index < len(row) else ""
        cells.append((header, value))
    return tuple(cells)


def _restore_trailing_newline(original: str, rendered: str) -> str:
    return f"{rendered}\n" if original.endswith("\n") else rendered


def _render_evidence_panel(evidence: TurnEvidence, cited_ids: list[str]) -> str:
    if not evidence.items:
        return ""
    cited = set(cited_ids)
    if not cited:
        return f"_sources: {_evidence_scope_text(evidence)}. Details: /evidence_"
    items = [item for item in evidence.items if item.evidence_id in cited]
    parts: list[str] = []
    for item in items[:_MAX_VISIBLE_SOURCE_ITEMS]:
        source_name = item.source.rsplit("/", 1)[-1]
        location = evidence_location_label(item.source, item.chunk, None)
        location_parts = [location]
        if item.chunk.heading:
            location_parts.insert(1, f"under {item.chunk.heading}")
        parts.append(f"{item.evidence_id}: {source_name} ({'; '.join(location_parts)})")
    remaining = len(items) - _MAX_VISIBLE_SOURCE_ITEMS
    if remaining > 0:
        parts.append(f"+{remaining} more cited source{'' if remaining == 1 else 's'}")
    return f"_sources: {'; '.join(parts)}. Details: /evidence_"


def evidence_citation_spans(text: str) -> list[tuple[int, int]]:
    return [(match.start(), match.end()) for match in _CITATION_RE.finditer(text)]


def is_evidence_sources_line(text: str) -> bool:
    return text.lstrip().startswith("sources:")


def _evidence_scope_text(evidence: TurnEvidence) -> str:
    item_count = len(evidence.items)
    excerpt = "evidence excerpt" if item_count == 1 else "evidence excerpts"
    sampled_sources = evidence.sampled_source_count or len(
        {item.source for item in evidence.items}
    )
    total_sources = evidence.total_source_count or sampled_sources
    if total_sources > sampled_sources:
        source_text = f"{sampled_sources} of {total_sources} indexed sources"
    else:
        source_text = f"{sampled_sources} source{'' if sampled_sources == 1 else 's'}"
    return f"{item_count} {excerpt} from {source_text}"


def enrich_reply(text: str, evidence: TurnEvidence | None) -> EnrichedReply:
    """Enrich a raw assistant reply with citation badge markup.

    Replaces plain [E1] citations with styled badge markup and appends
    an evidence panel below the reply.
    """
    enriched = normalize_markdown_tables(normalize_math_output(text))
    if not evidence or not evidence.items:
        return EnrichedReply(markdown_text=enriched, evidence=evidence)

    enriched_panel = _render_evidence_panel(evidence, extract_cited_ids(text))

    result = f"{enriched}\n\n{enriched_panel}"
    return EnrichedReply(markdown_text=result, evidence=evidence)


def extract_cited_ids(text: str) -> list[str]:
    seen: set[str] = set()
    ids: list[str] = []
    for match in _CITATION_RE.finditer(text):
        for id_match in _SINGLE_ID_RE.finditer(match.group(1)):
            eid = f"E{id_match.group(1)}"
            if eid not in seen:
                seen.add(eid)
                ids.append(eid)
    return ids


def evidence_summary_text(evidence: TurnEvidence | None) -> str:
    if not evidence or not evidence.items:
        return "no evidence"
    sources = {chunk.source for chunk in evidence.items}
    if len(sources) == 1:
        src = next(iter(sources))
        return f"{len(evidence.items)} evidence item(s) from {src}"
    return f"{len(evidence.items)} evidence item(s) from {len(sources)} source(s)"
