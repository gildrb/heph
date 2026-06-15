"""Markdown table helpers for overview replies."""

from __future__ import annotations

import re
from collections.abc import Sequence

from hephaion.chat.citation_patterns import _OVERVIEW_CITATION_ID_RE
from hephaion.chat.overview_validation import (
    _MARKDOWN_TABLE_SEPARATOR_LINE_RE,
    _OVERVIEW_MAX_TABLE_ROWS,
)
from hephaion.rag.context import EvidenceChunk


def _overview_markdown_table_block(reply: str) -> str:
    lines = reply.splitlines()
    for index, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        if index + 1 >= len(lines) or not _MARKDOWN_TABLE_SEPARATOR_LINE_RE.match(
            lines[index + 1]
        ):
            continue
        end = index + 2
        while end < len(lines) and lines[end].strip().startswith("|"):
            end += 1
        return "\n".join(line.rstrip() for line in lines[index:end]).strip()
    return ""


def _overview_pipe_table_as_markdown(reply: str) -> str:
    rows = _overview_pipe_table_rows(reply)
    if len(rows) < 2:
        return ""
    width = max(len(row) for row in rows)
    normalized_rows = [(*row, *("",) * (width - len(row))) for row in rows]
    first_row = normalized_rows[0]
    if any(_OVERVIEW_CITATION_ID_RE.search(cell) for cell in first_row):
        header = tuple(f"Column {index}" for index in range(1, width + 1))
        data_rows = normalized_rows
    else:
        header = first_row
        data_rows = normalized_rows[1:]
    separator = tuple("---" for _ in range(width))
    rendered_rows = (header, separator, *data_rows[: max(1, _OVERVIEW_MAX_TABLE_ROWS - 2)])
    return "\n".join(_render_markdown_table_row(row) for row in rendered_rows)


def _overview_pipe_table_rows(reply: str) -> tuple[tuple[str, ...], ...]:
    rows: list[tuple[str, ...]] = []
    for line in reply.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.count("|") < 2:
            continue
        rows.extend(_overview_pipe_table_line_rows(stripped))
    return tuple(rows)


def _overview_pipe_table_line_rows(line: str) -> tuple[tuple[str, ...], ...]:
    if _MARKDOWN_TABLE_SEPARATOR_LINE_RE.match(line):
        return ()
    cells = tuple(cell.strip() for cell in line.strip("|").split("|"))
    if len(cells) < 2:
        return ()
    if "" not in cells:
        return _overview_pipe_table_content_rows((cells,))
    return _overview_pipe_table_content_rows(_collapsed_pipe_table_rows(cells))


def _collapsed_pipe_table_rows(cells: Sequence[str]) -> tuple[tuple[str, ...], ...]:
    rows: list[tuple[str, ...]] = []
    current: list[str] = []
    for cell in cells:
        if cell:
            current.append(cell)
            continue
        _append_pipe_table_row(rows, current)
        current = []
    _append_pipe_table_row(rows, current)
    return tuple(rows)


def _append_pipe_table_row(rows: list[tuple[str, ...]], cells: Sequence[str]) -> None:
    if len(cells) >= 2:
        rows.append(tuple(cells))


def _overview_pipe_table_content_rows(
    rows: Sequence[tuple[str, ...]],
) -> tuple[tuple[str, ...], ...]:
    content_rows: list[tuple[str, ...]] = []
    for row in rows:
        if _markdown_separator_cells(row):
            continue
        content_rows.append(row)
    return tuple(content_rows)


def _markdown_separator_cells(row: Sequence[str]) -> bool:
    return all(re.fullmatch(r":?-{3,}:?", cell) for cell in row)


def _render_markdown_table_row(row: Sequence[str]) -> str:
    return "| " + " | ".join(_escape_markdown_table_cell(cell) for cell in row) + " |"


def _deterministic_overview_table(items: Sequence[tuple[EvidenceChunk, str]]) -> str:
    lines = [
        "| Source | Grounded excerpt |",
        "|---|---|",
    ]
    for item, cue_text in items:
        source = _escape_markdown_table_cell(item.source)
        cue = _escape_markdown_table_cell(cue_text)
        lines.append(f"| {source} | {cue} [{item.evidence_id}] |")
    return "\n".join(lines)


def _escape_markdown_table_cell(text: str) -> str:
    return text.replace("|", "\\|")
