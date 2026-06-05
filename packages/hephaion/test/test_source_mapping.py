from __future__ import annotations

from pathlib import Path

import pytest
from rag.chunker import Chunk
from rag.source_mapping import (
    SourceMappingError,
    chunk_line_span,
    resolve_source_path,
    source_excerpt,
)


def test_resolve_source_path_rejects_absolute_paths(tmp_path: Path) -> None:
    with pytest.raises(SourceMappingError):
        resolve_source_path(tmp_path, str(tmp_path / "materials" / "notes.md"))


def test_resolve_source_path_rejects_armory_escape(tmp_path: Path) -> None:
    with pytest.raises(SourceMappingError):
        resolve_source_path(tmp_path, "../outside.md")


def test_chunk_line_span_and_excerpt_mark_exact_lines(tmp_path: Path) -> None:
    source = tmp_path / "materials" / "notes.md"
    source.parent.mkdir()
    text = "one\nbefore\ntarget line\nsecond target\nend\n"
    source.write_text(text, encoding="utf-8")
    start = text.index("target")
    chunk_text = "target line\nsecond target"
    chunk = Chunk(
        text=chunk_text,
        source="materials/notes.md",
        index=0,
        char_start=start,
        char_end=start + len(chunk_text),
    )

    span = chunk_line_span(source, chunk)
    excerpt = source_excerpt(source, chunk, context_lines=1)

    assert span is not None
    assert span.start_line == 3
    assert span.end_line == 4
    assert "> 3 │ target line" in excerpt
    assert "> 4 │ second target" in excerpt
    assert "  2 │ before" in excerpt


def test_source_excerpt_falls_back_to_chunk_for_binary_file(tmp_path: Path) -> None:
    source = tmp_path / "materials" / "binary.bin"
    source.parent.mkdir()
    source.write_bytes(b"\x00\x01\x02")
    chunk = Chunk(
        text="fallback content",
        source="materials/binary.bin",
        index=0,
        char_start=0,
        char_end=3,
    )

    assert chunk_line_span(source, chunk) is None
    assert source_excerpt(source, chunk) == "fallback content"
