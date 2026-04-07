"""Text chunking for RAG indexing.

Splits text files into chunks with metadata preservation.

Chunking strategies (selectable via ``ChunkStrategy``):

- **AUTO** (default): picks the best strategy per file — Markdown files get
  structure-aware chunking, all other text files use semantic chunking when
  ``sentence-transformers`` is available, falling back to fixed-window.
- **MARKDOWN**: structure-aware — respects ``#`` headers, splits oversized
  sections at paragraph boundaries.  Each chunk carries ``heading`` +
  ``heading_level`` for hierarchical context.
- **SEMANTIC**: splits into sentences, embeds each, then merges into chunks
  at cosine-similarity breakpoints.  Falls back to fixed-window when
  ``sentence-transformers`` is unavailable.
- **TEXT**: fixed-window with paragraph → newline → sentence → hard-cut
  boundary detection.

Hierarchical metadata (``heading``, ``heading_level``) is preserved so
retrieval can return heading context alongside matched subsections.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

_TEXT_EXTENSIONS = frozenset({
    ".txt", ".md", ".rst", ".adoc", ".org",
    ".py", ".js", ".ts", ".tsx", ".jsx",
    ".java", ".kt", ".go", ".rs", ".c", ".cpp", ".h", ".hpp",
    ".rb", ".php", ".swift", ".zig",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".html", ".css", ".xml", ".svg",
    ".sh", ".bash", ".zsh", ".fish",
    ".sql", ".graphql",
    ".tex", ".bib",
    ".csv", ".tsv",
    ".log",
})

_DEFAULT_CHUNK_SIZE = 500
_DEFAULT_OVERLAP = 100
_MAX_CHUNK_SIZE = 2000
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
_CODE_FENCE_RE = re.compile(r"^```", re.MULTILINE)


# ---------------------------------------------------------------------------
# Chunking strategy enum
# ---------------------------------------------------------------------------


class ChunkStrategy(Enum):
    """Selects which chunking algorithm ``chunk_file`` uses."""

    AUTO = "auto"          # markdown → chunk_markdown, else → semantic → text fallback
    MARKDOWN = "markdown"  # always use chunk_markdown
    SEMANTIC = "semantic"  # always use chunk_semantic (falls back to text internally)
    TEXT = "text"          # always use chunk_text


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Chunk:
    text: str
    source: str  # relative path from armory root
    index: int  # chunk index within the source file
    char_start: int
    char_end: int
    heading: str = ""  # nearest parent heading (hierarchical context)
    heading_level: int = 0  # heading depth (1–6, 0 = no heading)


@dataclass
class ChunkedDocument:
    source: str
    chunks: list[Chunk] = field(default_factory=list)
    content_hash: str = ""


# ---------------------------------------------------------------------------
# File-type detection
# ---------------------------------------------------------------------------


def _is_text_file(path: Path) -> bool:
    if path.suffix.lower() in _TEXT_EXTENSIONS:
        return True
    try:
        sample = path.read_bytes()[:8192]
        return b"\x00" not in sample
    except OSError:
        return False


def _is_markdown(path: Path) -> bool:
    return path.suffix.lower() in (".md", ".mdown", ".markdown")


# ---------------------------------------------------------------------------
# Markdown structure-aware chunking
# ---------------------------------------------------------------------------


def _parse_sections(text: str) -> list[tuple[str, int, int, int]]:
    """Split text into sections at heading boundaries.

    Returns list of (heading_title, heading_level, char_start, char_end).
    Sections include their heading line in the text span.
    """
    sections: list[tuple[str, int, int, int]] = []
    matches = list(_HEADING_RE.finditer(text))

    if not matches:
        # No headings — entire file is one section
        if text.strip():
            sections.append(("", 0, 0, len(text)))
        return sections

    # Content before first heading
    if matches[0].start() > 0:
        preamble = text[:matches[0].start()]
        if preamble.strip():
            sections.append(("", 0, 0, matches[0].start()))

    for i, m in enumerate(matches):
        level = len(m.group(1))
        title = m.group(2).strip()
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections.append((title, level, start, end))

    return sections


def _chunk_markdown_section(
    text: str,
    source: str,
    idx_start: int,
    heading: str,
    heading_level: int,
    char_offset: int,
    chunk_size: int,
    overlap: int,
) -> list[Chunk]:
    """Chunk a single markdown section, possibly splitting large sections."""
    text = text.strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [Chunk(
            text=text,
            source=source,
            index=idx_start,
            char_start=char_offset,
            char_end=char_offset + len(text),
            heading=heading,
            heading_level=heading_level,
        )]

    # Section is too large — split by paragraph boundaries
    parts = re.split(r"\n\n+", text)
    chunks: list[Chunk] = []
    current = ""
    chunk_idx = idx_start

    for part in parts:
        part = part.strip()
        if not part:
            continue

        candidate = f"{current}\n\n{part}" if current else part

        if len(candidate) > chunk_size and current:
            # Flush current
            chunks.append(Chunk(
                text=current.strip(),
                source=source,
                index=chunk_idx,
                char_start=char_offset,
                char_end=char_offset + len(current),
                heading=heading,
                heading_level=heading_level,
            ))
            chunk_idx += 1
            char_offset += len(current)
            current = part
        else:
            current = candidate

    if current.strip():
        chunks.append(Chunk(
            text=current.strip(),
            source=source,
            index=chunk_idx,
            char_start=char_offset,
            char_end=char_offset + len(current),
            heading=heading,
            heading_level=heading_level,
        ))

    return chunks


def chunk_markdown(
    text: str,
    source: str,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    overlap: int = _DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Structure-aware Markdown chunking.

    Splits on heading boundaries first, then by paragraphs within sections
    that exceed *chunk_size*.  Each chunk carries its nearest parent heading
    as ``heading`` metadata for hierarchical context.
    """
    if not text or not text.strip():
        return []

    sections = _parse_sections(text)
    chunks: list[Chunk] = []
    idx = 0

    for heading_title, heading_level, start, end in sections:
        section_text = text[start:end]
        new_chunks = _chunk_markdown_section(
            section_text, source, idx, heading_title, heading_level,
            start, chunk_size, overlap,
        )
        chunks.extend(new_chunks)
        idx += len(new_chunks)

    return chunks


# ---------------------------------------------------------------------------
# Fixed-window chunking
# ---------------------------------------------------------------------------


def _find_boundary(text: str, target: int, search_back: int) -> int:
    """Look backwards from *target* for a good break point."""
    start = max(target - search_back, 0)
    window = text[start:target]

    for sep in ("\n\n", "\n", ". ", "! ", "? ", "; ", ", "):
        idx = window.rfind(sep)
        if idx >= 0:
            return start + idx + len(sep)

    return target


def chunk_text(
    text: str,
    source: str,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    overlap: int = _DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Split *text* into overlapping chunks (fixed-window).

    Tries to break on paragraph boundaries (double newlines) for readability.
    Falls back to sentence boundaries (single newline or period+space) and
    finally to hard character cuts.
    """
    if not text:
        return []

    chunks: list[Chunk] = []
    pos = 0
    idx = 0

    while pos < len(text):
        end = min(pos + chunk_size, len(text))

        if end < len(text):
            boundary = _find_boundary(text, end, chunk_size // 4)
            if boundary > pos:
                end = boundary

        chunk_text_str = text[pos:end].strip()
        if chunk_text_str:
            chunks.append(Chunk(
                text=chunk_text_str,
                source=source,
                index=idx,
                char_start=pos,
                char_end=end,
            ))
            idx += 1

        advance = end - pos
        if advance <= overlap:
            break
        pos = end - overlap

    return chunks


# ---------------------------------------------------------------------------
# Semantic chunking (requires sentence-transformers, optional)
# ---------------------------------------------------------------------------


def _is_st_available() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        return True
    except ImportError:
        return False


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def chunk_semantic(
    text: str,
    source: str,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    overlap: int = _DEFAULT_OVERLAP,
    *,
    similarity_threshold: float = 0.5,
    min_chunk: int = 100,
) -> list[Chunk]:
    """Semantic chunking: split on embedding similarity boundaries.

    Splits text into sentences, embeds each, then merges adjacent sentences
    into chunks by finding natural "drops" in cosine similarity between
    consecutive sentence embeddings.

    Falls back to ``chunk_text()`` if ``sentence-transformers`` is not
    available.
    """
    if not text or not text.strip():
        return []

    if not _is_st_available():
        return chunk_text(text, source, chunk_size, overlap)

    from sentence_transformers import SentenceTransformer

    # Split into sentences
    sentences = _split_sentences(text)
    if len(sentences) <= 1:
        return [Chunk(text=text.strip(), source=source, index=0,
                       char_start=0, char_end=len(text))]

    # Encode sentences
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(sentences, convert_to_numpy=True, show_progress_bar=False)
    emb_lists = [row.tolist() for row in embeddings]

    # Find breakpoints: where similarity drops below threshold
    breakpoints: list[int] = [0]
    for i in range(1, len(emb_lists)):
        sim = _cosine_sim(emb_lists[i - 1], emb_lists[i])
        if sim < similarity_threshold:
            breakpoints.append(i)
    breakpoints.append(len(sentences))

    # Build chunks from sentence groups
    chunks: list[Chunk] = []
    char_pos = 0
    idx = 0

    for bp_idx in range(len(breakpoints) - 1):
        start_sent = breakpoints[bp_idx]
        end_sent = breakpoints[bp_idx + 1]
        chunk_sentences = sentences[start_sent:end_sent]
        chunk_str = " ".join(chunk_sentences).strip()

        if not chunk_str:
            continue

        # Skip very small chunks — merge with previous
        if len(chunk_str) < min_chunk and chunks:
            prev = chunks[-1]
            merged = f"{prev.text} {chunk_str}"
            chunks[-1] = Chunk(
                text=merged,
                source=source,
                index=prev.index,
                char_start=prev.char_start,
                char_end=char_pos + len(chunk_str),
            )
            char_pos += len(chunk_str) + 1
            continue

        chunks.append(Chunk(
            text=chunk_str,
            source=source,
            index=idx,
            char_start=char_pos,
            char_end=char_pos + len(chunk_str),
        ))
        idx += 1
        char_pos += len(chunk_str) + 1

    return chunks if chunks else chunk_text(text, source, chunk_size, overlap)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences for semantic chunking."""
    # Split on sentence-ending punctuation followed by whitespace
    parts = re.split(r'(?<=[.!?])\s+', text)
    # Also split on newlines for code-like text
    result: list[str] = []
    for part in parts:
        sub = part.split('\n')
        for s in sub:
            s = s.strip()
            if s:
                result.append(s)
    return result


# ---------------------------------------------------------------------------
# Strategy resolver
# ---------------------------------------------------------------------------


def _resolve_strategy(strategy: ChunkStrategy, path: Path) -> Callable:
    """Map a ``ChunkStrategy`` + file path to the actual chunking function.

    AUTO picks the best algorithm for the file type:
    - ``.md`` files → ``chunk_markdown``
    - everything else → ``chunk_semantic`` (which internally falls back to
      ``chunk_text`` when *sentence-transformers* is unavailable)
    """
    if strategy == ChunkStrategy.AUTO:
        if _is_markdown(path):
            return chunk_markdown
        return chunk_semantic
    if strategy == ChunkStrategy.MARKDOWN:
        return chunk_markdown
    if strategy == ChunkStrategy.SEMANTIC:
        return chunk_semantic
    return chunk_text


# ---------------------------------------------------------------------------
# File-level entry point
# ---------------------------------------------------------------------------


def chunk_file(
    path: Path,
    armory_root: Path,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    overlap: int = _DEFAULT_OVERLAP,
    *,
    strategy: ChunkStrategy = ChunkStrategy.AUTO,
) -> ChunkedDocument | None:
    """Read and chunk a single file. Returns None for binary/skipped files.

    *strategy* controls which algorithm is used:

    - ``ChunkStrategy.AUTO`` (default): Markdown files → structure-aware,
      other text → semantic (with fixed-window fallback).
    - ``ChunkStrategy.MARKDOWN``: always use heading-aware chunking.
    - ``ChunkStrategy.SEMANTIC``: always use embedding-based chunking
      (falls back to fixed-window when *sentence-transformers* is absent).
    - ``ChunkStrategy.TEXT``: always use fixed-window chunking.
    """
    if not _is_text_file(path):
        return None

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None

    if not text.strip():
        return None

    rel = str(path.relative_to(armory_root))

    # Select and run the chunking function
    chunk_fn = _resolve_strategy(strategy, path)
    chunks = chunk_fn(text, rel, chunk_size, overlap)

    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    return ChunkedDocument(
        source=rel,
        chunks=chunks,
        content_hash=content_hash,
    )
