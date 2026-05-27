from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hephaion.materials import infer_material_role_from_text
from hephaion.rag.chunker import Chunk


class SourceMappingError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class SourceLineSpan:
    start_line: int
    end_line: int


def resolve_source_path(armory_path: Path, source: str) -> Path:
    base = armory_path.expanduser().resolve()
    source_path = Path(source)
    if source_path.is_absolute():
        raise SourceMappingError(f"Evidence source is not relative: {source}")
    resolved = (base / source_path).resolve()
    if not resolved.is_relative_to(base):
        raise SourceMappingError(f"Evidence source escapes armory: {source}")
    return resolved


def read_source_text(path: Path) -> str:
    data = path.read_bytes()
    if b"\x00" in data[:8192]:
        raise SourceMappingError(f"Source is not a text file: {path}")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace")


def char_to_line(text: str, offset: int) -> int:
    clamped = min(max(offset, 0), len(text))
    return text.count("\n", 0, clamped) + 1


def chunk_line_span(path: Path, chunk: Chunk) -> SourceLineSpan | None:
    try:
        text = read_source_text(path)
    except (OSError, SourceMappingError):
        return None
    start_offset = min(max(chunk.char_start, 0), len(text))
    end_offset = min(max(chunk.char_end, start_offset), len(text))
    end_line_offset = end_offset - 1 if end_offset > start_offset else start_offset
    return SourceLineSpan(
        start_line=char_to_line(text, start_offset),
        end_line=char_to_line(text, end_line_offset),
    )


def line_label(span: SourceLineSpan | None) -> str:
    if span is None:
        return "line unknown"
    if span.start_line == span.end_line:
        return f"line {span.start_line}"
    return f"lines {span.start_line}-{span.end_line}"


def evidence_location_label(source: str, chunk: Chunk, span: SourceLineSpan | None) -> str:
    if span is not None:
        return line_label(span)

    role, _confidence, _reason = infer_material_role_from_text(source, chunk.text)
    ordinal = chunk.index + 1
    if role == "slides":
        return f"slide/deck excerpt {ordinal}"
    if role == "past_exam":
        return f"exam excerpt {ordinal}"
    return f"source excerpt {ordinal}"


def source_excerpt(
    path: Path,
    chunk: Chunk,
    *,
    context_lines: int = 2,
    max_chars: int = 2400,
) -> str:
    try:
        text = read_source_text(path)
    except (OSError, SourceMappingError):
        return chunk.text[:max_chars].rstrip()

    lines = text.splitlines()
    if not lines:
        return ""

    span = chunk_line_span(path, chunk)
    if span is None:
        return chunk.text[:max_chars].rstrip()

    first_line = max(1, span.start_line - context_lines)
    last_line = min(len(lines), span.end_line + context_lines)
    width = len(str(last_line))
    rendered: list[str] = []
    for line_no in range(first_line, last_line + 1):
        marker = ">" if span.start_line <= line_no <= span.end_line else " "
        rendered.append(f"{marker} {line_no:{width}} │ {lines[line_no - 1]}")

    excerpt = "\n".join(rendered)
    if len(excerpt) <= max_chars:
        return excerpt
    return f"{excerpt[: max_chars - 13].rstrip()}\n[truncated]"
