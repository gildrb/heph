"""Text chunking for RAG indexing.

Splits text files into overlapping chunks with metadata preservation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass(frozen=True, slots=True)
class Chunk:
    text: str
    source: str  # relative path from armory root
    index: int  # chunk index within the source file
    char_start: int
    char_end: int


@dataclass
class ChunkedDocument:
    source: str
    chunks: list[Chunk] = field(default_factory=list)
    content_hash: str = ""


def _is_text_file(path: Path) -> bool:
    if path.suffix.lower() in _TEXT_EXTENSIONS:
        return True
    try:
        sample = path.read_bytes()[:8192]
        return b"\x00" not in sample
    except OSError:
        return False


def chunk_text(
    text: str,
    source: str,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    overlap: int = _DEFAULT_OVERLAP,
) -> list[Chunk]:
    """Split *text* into overlapping chunks.

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


def _find_boundary(text: str, target: int, search_back: int) -> int:
    """Look backwards from *target* for a good break point."""
    start = max(target - search_back, 0)
    window = text[start:target]

    for sep in ("\n\n", "\n", ". ", "! ", "? ", "; ", ", "):
        idx = window.rfind(sep)
        if idx >= 0:
            return start + idx + len(sep)

    return target


def chunk_file(
    path: Path,
    armory_root: Path,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    overlap: int = _DEFAULT_OVERLAP,
) -> ChunkedDocument | None:
    """Read and chunk a single file. Returns None for binary/skipped files."""
    if not _is_text_file(path):
        return None

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None

    rel = str(path.relative_to(armory_root))
    chunks = chunk_text(text, rel, chunk_size, overlap)

    import hashlib
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    return ChunkedDocument(
        source=rel,
        chunks=chunks,
        content_hash=content_hash,
    )
