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

import contextlib
import hashlib
import importlib
import importlib.util
import io
import re
import shutil
import subprocess
import tempfile
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from html.parser import HTMLParser
from pathlib import Path
from typing import Protocol, cast, runtime_checkable

from hephaistos.logging import get_logger

_log = get_logger("rag.chunker")

_TEXT_EXTENSIONS = frozenset(
    {
        ".txt",
        ".md",
        ".rst",
        ".adoc",
        ".org",
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".java",
        ".kt",
        ".go",
        ".rs",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".rb",
        ".php",
        ".swift",
        ".zig",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".html",
        ".css",
        ".xml",
        ".svg",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".sql",
        ".graphql",
        ".tex",
        ".bib",
        ".csv",
        ".tsv",
        ".log",
    }
)

_DOCLING_EXTENSIONS = frozenset(
    {
        ".pdf",
        ".docx",
        ".pptx",
        ".xlsx",
        ".doc",
        ".ppt",
        ".xls",
        ".odt",
        ".ods",
        ".odp",
        ".rtf",
    }
)

_DEFAULT_CHUNK_SIZE = 500
_DEFAULT_OVERLAP = 100
_MAX_CHUNK_SIZE = 2000
_PDF_TEXT_TIMEOUT_SECONDS = 30
_PDF_OCR_RENDER_TIMEOUT_SECONDS = 60
_PDF_OCR_PAGE_TIMEOUT_SECONDS = 45
_PDF_OCR_DPI = 200
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)
_CODE_FENCE_RE = re.compile(r"^```", re.MULTILINE)
_MISPLACED_DIAERESIS_RE = re.compile(r"¨\s*([AaOoUu])")
_EXTRACTION_PLACEHOLDER_RE = re.compile(
    r"(?i)(?:<!--\s*)?\b(?:formula|image|table|picture|figure)"
    r"[-_ ]+not[-_ ]+decoded\b\.?(?:\s*-->)?"
)
_HTML_EXTRACTION_COMMENT_RE = re.compile(
    r"(?i)<!--\s*(?:image|table|picture|figure|formula)\s*-->"
)
_UMLAUTS = {
    "A": "Ä",
    "O": "Ö",
    "U": "Ü",
    "a": "ä",
    "o": "ö",
    "u": "ü",
}


class _MarkdownExportProtocol(Protocol):
    def export_to_markdown(self) -> str: ...


class _DoclingResultProtocol(Protocol):
    document: _MarkdownExportProtocol


class _DoclingConverterProtocol(Protocol):
    def convert(self, path: str) -> _DoclingResultProtocol: ...


@runtime_checkable
class _ToListProtocol(Protocol):
    def tolist(self) -> object: ...


class _SentenceEncoderProtocol(Protocol):
    def encode(
        self,
        sentences: list[str],
        *,
        convert_to_numpy: bool,
        show_progress_bar: bool,
    ) -> object: ...


class _SentenceTransformerFactory(Protocol):
    def __call__(self, model_name: str) -> _SentenceEncoderProtocol: ...


_OPTIONAL_BACKEND_UNSET = object()
_DocumentConverter: type[_DoclingConverterProtocol] | None | object = _OPTIONAL_BACKEND_UNSET
_SentenceTransformer: _SentenceTransformerFactory | None | object = _OPTIONAL_BACKEND_UNSET


class ChunkStrategy(Enum):
    """Selects which chunking algorithm ``chunk_file`` uses."""

    AUTO = "auto"  # markdown → chunk_markdown, else → semantic → text fallback
    MARKDOWN = "markdown"  # always use chunk_markdown
    SEMANTIC = "semantic"  # always use chunk_semantic (falls back to text internally)
    TEXT = "text"  # always use chunk_text


@dataclass(frozen=True, slots=True)
class Chunk:
    text: str
    source: str  # relative path from armory root
    index: int  # chunk index within the source file
    char_start: int
    char_end: int
    heading: str = ""  # nearest parent heading (hierarchical context)
    heading_level: int = 0  # heading depth (1-6, 0 = no heading)


@dataclass
class ChunkedDocument:
    source: str
    chunks: list[Chunk] = field(default_factory=list)
    content_hash: str = ""


def _is_text_file(path: Path) -> bool:
    if path.suffix.lower() in _TEXT_EXTENSIONS:
        return True
    if path.suffix.lower() in _DOCLING_EXTENSIONS:
        return False
    try:
        sample = path.read_bytes()[:8192]
        return b"\x00" not in sample
    except OSError:
        return False


def _is_markdown(path: Path) -> bool:
    return path.suffix.lower() in (".md", ".mdown", ".markdown")


def _is_docling_file(path: Path) -> bool:
    return path.suffix.lower() in _DOCLING_EXTENSIONS


def _is_pdf_file(path: Path) -> bool:
    return path.suffix.lower() == ".pdf"


class _HTMLTextExtractor(HTMLParser):
    """Extract readable text from HTML without adding a parser dependency."""

    _BLOCK_TAGS = frozenset(
        {
            "address",
            "article",
            "aside",
            "blockquote",
            "br",
            "dd",
            "div",
            "dl",
            "dt",
            "figcaption",
            "footer",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "header",
            "li",
            "main",
            "nav",
            "ol",
            "p",
            "pre",
            "section",
            "table",
            "td",
            "th",
            "tr",
            "ul",
        }
    )
    _SKIPPED_TAGS = frozenset({"script", "style", "noscript", "template", "svg"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        normalized = tag.casefold()
        if normalized in self._SKIPPED_TAGS:
            self._skip_depth += 1
            return
        if normalized in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.casefold()
        if normalized in self._SKIPPED_TAGS and self._skip_depth:
            self._skip_depth -= 1
            return
        if normalized in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        text = " ".join(data.split())
        if text:
            self._parts.append(text)
            self._parts.append(" ")

    def text(self) -> str:
        lines = (" ".join(line.split()) for line in "".join(self._parts).splitlines())
        return "\n".join(line for line in lines if line)


def _read_indexable_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() not in {".html", ".htm"}:
        return text
    extractor = _HTMLTextExtractor()
    extractor.feed(text)
    extractor.close()
    return extractor.text()


def _is_pdftotext_available() -> bool:
    return shutil.which("pdftotext") is not None


def _is_pdf_ocr_available() -> bool:
    return shutil.which("pdftoppm") is not None and shutil.which("tesseract") is not None


def _can_convert_binary_file(path: Path) -> bool:
    if not _is_docling_file(path):
        return False
    if _is_pdf_file(path) and (_is_pdftotext_available() or _is_pdf_ocr_available()):
        return True
    return _is_docling_available()


def _is_docling_available() -> bool:
    if _DocumentConverter is None:
        return False
    if _DocumentConverter is not _OPTIONAL_BACKEND_UNSET:
        return True
    try:
        return importlib.util.find_spec("docling") is not None
    except (ImportError, AttributeError, ValueError):
        return False


def _resolved_path_within_armory(path: Path, armory_root: Path) -> Path | None:
    if path.is_symlink():
        _log.warning(
            "skipping symlinked material",
            extra={"fields": {"path": str(path), "armory": str(armory_root)}},
        )
        return None
    try:
        resolved_root = armory_root.resolve(strict=True)
        resolved_path = path.resolve(strict=True)
    except OSError:
        return None
    if not resolved_path.is_relative_to(resolved_root):
        _log.warning(
            "skipping material outside armory",
            extra={"fields": {"path": str(path), "armory": str(armory_root)}},
        )
        return None
    return resolved_path


_docling_converter: list[_DoclingConverterProtocol] = []


def _docling_converter_class() -> type[_DoclingConverterProtocol] | None:
    global _DocumentConverter  # noqa: PLW0603
    if _DocumentConverter is _OPTIONAL_BACKEND_UNSET:
        try:
            module = importlib.import_module("docling.document_converter")
            raw_converter = getattr(module, "DocumentConverter", None)
        except ImportError:
            raw_converter = None
        _DocumentConverter = (
            None
            if raw_converter is None
            else cast("type[_DoclingConverterProtocol]", raw_converter)
        )
    if _DocumentConverter is None:
        return None
    return cast("type[_DoclingConverterProtocol]", _DocumentConverter)


def _get_docling_converter() -> _DoclingConverterProtocol | None:
    """Return a lazily-initialised, cached ``DocumentConverter``."""
    converter_class = _docling_converter_class()
    if converter_class is None:
        return None
    if not _docling_converter:
        _docling_converter.append(converter_class())
    return _docling_converter[0]


def _convert_to_markdown(path: Path) -> str | None:
    """Convert a binary document to Markdown via Docling.

    Returns the markdown text, or ``None`` on failure.
    """
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            converter = _get_docling_converter()
            if converter is None:
                return None
            result = converter.convert(str(path))
            return _normalize_extracted_text(result.document.export_to_markdown())
    except Exception as exc:
        detail = str(exc).strip() or type(exc).__name__
        _log.warning(
            "docling conversion failed",
            extra={"fields": {"path": str(path), "error": detail}},
        )
        return None


def _convert_pdf_to_text(path: Path) -> str | None:
    """Extract plain PDF text with the local ``pdftotext`` binary when available."""
    if not _is_pdf_file(path) or not _is_pdftotext_available():
        return None
    try:
        completed = subprocess.run(
            ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
            check=False,
            capture_output=True,
            text=True,
            timeout=_PDF_TEXT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        detail = str(exc).strip() or type(exc).__name__
        _log.warning(
            "pdftotext extraction failed",
            extra={"fields": {"path": str(path), "error": detail}},
        )
        return None
    if completed.returncode != 0:
        detail = completed.stderr.strip() or f"exit status {completed.returncode}"
        _log.warning(
            "pdftotext extraction failed",
            extra={"fields": {"path": str(path), "error": detail}},
        )
        return None
    text = _normalize_extracted_text(completed.stdout)
    return text if text.strip() else None


def _convert_pdf_with_ocr(path: Path) -> str | None:
    """Extract image-only PDF text through local Poppler + Tesseract when available."""
    if not _is_pdf_file(path) or not _is_pdf_ocr_available():
        return None
    try:
        with tempfile.TemporaryDirectory(prefix="heph-pdf-ocr-") as temp_dir:
            output_prefix = str(Path(temp_dir) / "page")
            render = subprocess.run(
                [
                    "pdftoppm",
                    "-r",
                    str(_PDF_OCR_DPI),
                    "-png",
                    str(path),
                    output_prefix,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=_PDF_OCR_RENDER_TIMEOUT_SECONDS,
            )
            if render.returncode != 0:
                detail = render.stderr.strip() or f"exit status {render.returncode}"
                _log.warning(
                    "pdf OCR render failed",
                    extra={"fields": {"path": str(path), "error": detail}},
                )
                return None
            page_paths = sorted(Path(temp_dir).glob("page-*.png"))
            texts: list[str] = []
            for page_path in page_paths:
                page = subprocess.run(
                    ["tesseract", str(page_path), "stdout", "-l", "eng"],
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=_PDF_OCR_PAGE_TIMEOUT_SECONDS,
                )
                if page.returncode != 0:
                    detail = page.stderr.strip() or f"exit status {page.returncode}"
                    _log.warning(
                        "pdf OCR page failed",
                        extra={
                            "fields": {
                                "path": str(path),
                                "page": page_path.name,
                                "error": detail,
                            }
                        },
                    )
                    continue
                texts.append(page.stdout)
    except (OSError, subprocess.SubprocessError) as exc:
        detail = str(exc).strip() or type(exc).__name__
        _log.warning(
            "pdf OCR extraction failed",
            extra={"fields": {"path": str(path), "error": detail}},
        )
        return None
    text = _normalize_extracted_text("\n\n".join(texts))
    return text if text.strip() else None


def _convert_binary_to_indexable_text(path: Path) -> str | None:
    """Convert a supported binary material to indexable text."""
    if _is_pdf_file(path):
        pdf_text = _convert_pdf_to_text(path)
        if pdf_text and pdf_text.strip():
            return pdf_text
        ocr_text = _convert_pdf_with_ocr(path)
        if ocr_text and ocr_text.strip():
            return ocr_text
    docling_text = _convert_to_markdown(path) if _is_docling_available() else None
    if docling_text and docling_text.strip():
        return docling_text
    return None


def _normalize_extracted_text(text: str) -> str:
    """Normalize common PDF extraction artifacts before indexing."""
    normalized = unicodedata.normalize("NFC", text)
    repaired = _MISPLACED_DIAERESIS_RE.sub(
        lambda match: _UMLAUTS[match.group(1)],
        normalized,
    )
    without_placeholders = _EXTRACTION_PLACEHOLDER_RE.sub("", repaired)
    return _HTML_EXTRACTION_COMMENT_RE.sub("", without_placeholders)


def _parse_sections(text: str) -> list[tuple[str, int, int, int]]:
    """Split text into sections at heading boundaries.

    Returns list of (heading_title, heading_level, char_start, char_end).
    Sections include their heading line in the text span.
    """
    sections: list[tuple[str, int, int, int]] = []
    matches = list(_HEADING_RE.finditer(text))

    if not matches:
        if text.strip():
            sections.append(("", 0, 0, len(text)))
        return sections
    if matches[0].start() > 0:
        preamble = text[: matches[0].start()]
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
) -> list[Chunk]:
    """Chunk a single markdown section, possibly splitting large sections."""
    text = text.strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [
            Chunk(
                text=text,
                source=source,
                index=idx_start,
                char_start=char_offset,
                char_end=char_offset + len(text),
                heading=heading,
                heading_level=heading_level,
            )
        ]
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
            chunks.append(
                Chunk(
                    text=current.strip(),
                    source=source,
                    index=chunk_idx,
                    char_start=char_offset,
                    char_end=char_offset + len(current),
                    heading=heading,
                    heading_level=heading_level,
                )
            )
            chunk_idx += 1
            char_offset += len(current)
            current = part
        else:
            current = candidate

    if current.strip():
        chunks.append(
            Chunk(
                text=current.strip(),
                source=source,
                index=chunk_idx,
                char_start=char_offset,
                char_end=char_offset + len(current),
                heading=heading,
                heading_level=heading_level,
            )
        )

    return chunks


def chunk_markdown(
    text: str,
    source: str,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    _overlap: int = _DEFAULT_OVERLAP,
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
            section_text,
            source,
            idx,
            heading_title,
            heading_level,
            start,
            chunk_size,
        )
        chunks.extend(new_chunks)
        idx += len(new_chunks)

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
            chunks.append(
                Chunk(
                    text=chunk_text_str,
                    source=source,
                    index=idx,
                    char_start=pos,
                    char_end=end,
                )
            )
            idx += 1

        advance = end - pos
        if advance <= overlap:
            break
        pos = end - overlap

    return chunks


def _is_st_available() -> bool:
    return _sentence_transformer_factory() is not None


def _sentence_transformer_factory() -> _SentenceTransformerFactory | None:
    global _SentenceTransformer  # noqa: PLW0603
    if _SentenceTransformer is _OPTIONAL_BACKEND_UNSET:
        try:
            module = importlib.import_module("sentence_transformers")
            raw_transformer = getattr(module, "SentenceTransformer", None)
        except ImportError:
            raw_transformer = None
        _SentenceTransformer = (
            None
            if raw_transformer is None
            else cast("_SentenceTransformerFactory", raw_transformer)
        )
    if _SentenceTransformer is None:
        return None
    return cast("_SentenceTransformerFactory", _SentenceTransformer)


def _embedding_row(row: object) -> list[float] | None:
    if isinstance(row, _ToListProtocol):
        row = row.tolist()
    if not isinstance(row, list):
        return None
    values: list[float] = []
    typed_row = cast("list[object]", row)
    for item in typed_row:
        if not isinstance(item, int | float):
            return None
        values.append(float(item))
    return values


def _embedding_rows(matrix: object) -> list[list[float]]:
    if isinstance(matrix, _ToListProtocol):
        matrix = matrix.tolist()
    if not isinstance(matrix, list):
        return []
    rows: list[list[float]] = []
    typed_matrix = cast("list[object]", matrix)
    for row in typed_matrix:
        typed_row = _embedding_row(row)
        if typed_row is not None:
            rows.append(typed_row)
    return rows


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
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

    transformer_factory = _sentence_transformer_factory()
    if transformer_factory is None:
        return chunk_text(text, source, chunk_size, overlap)

    sentences = _split_sentences(text)
    if len(sentences) <= 1:
        return [Chunk(text=text.strip(), source=source, index=0, char_start=0, char_end=len(text))]
    model = transformer_factory("all-MiniLM-L6-v2")
    emb_lists = _embedding_rows(
        model.encode(sentences, convert_to_numpy=True, show_progress_bar=False)
    )
    if len(emb_lists) != len(sentences):
        return chunk_text(text, source, chunk_size, overlap)
    breakpoints: list[int] = [0]
    for i in range(1, len(emb_lists)):
        sim = _cosine_sim(emb_lists[i - 1], emb_lists[i])
        if sim < similarity_threshold:
            breakpoints.append(i)
    breakpoints.append(len(sentences))
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

        chunks.append(
            Chunk(
                text=chunk_str,
                source=source,
                index=idx,
                char_start=char_pos,
                char_end=char_pos + len(chunk_str),
            )
        )
        idx += 1
        char_pos += len(chunk_str) + 1

    return chunks or chunk_text(text, source, chunk_size, overlap)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences for semantic chunking."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    result: list[str] = []
    for part in parts:
        sub = part.split("\n")
        for s in sub:
            s = s.strip()
            if s:
                result.append(s)
    return result


def _resolve_strategy(
    strategy: ChunkStrategy, path: Path
) -> Callable[[str, str, int, int], list[Chunk]]:
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

    Binary documents (PDF, DOCX, PPTX, XLSX, etc.) are converted to
    Markdown via *docling* when the optional ``docling`` extra is installed,
    then chunked with heading-aware chunking.
    """
    if _resolved_path_within_armory(path, armory_root) is None:
        return None

    if not _is_text_file(path):
        if _can_convert_binary_file(path):
            return _chunk_docling_file(path, armory_root, chunk_size, overlap)
        return None

    try:
        text = _read_indexable_text(path)
    except (UnicodeDecodeError, OSError):
        return None

    if not text.strip():
        return None
    text = _normalize_extracted_text(text)
    if not text.strip():
        return None

    rel = str(path.relative_to(armory_root))
    chunk_fn = _resolve_strategy(strategy, path)
    chunks: list[Chunk] = chunk_fn(text, rel, chunk_size, overlap)

    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    return ChunkedDocument(
        source=rel,
        chunks=chunks,
        content_hash=content_hash,
    )


def _chunk_docling_file(
    path: Path,
    armory_root: Path,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    overlap: int = _DEFAULT_OVERLAP,
) -> ChunkedDocument | None:
    """Convert a binary document to text, then chunk it."""
    if _resolved_path_within_armory(path, armory_root) is None:
        return None

    text = _convert_binary_to_indexable_text(path)
    if not text or not text.strip():
        return None

    rel = str(path.relative_to(armory_root))
    chunks = chunk_markdown(text, rel, chunk_size, overlap)
    content_hash = hashlib.sha256(path.read_bytes()).hexdigest()[:16]

    return ChunkedDocument(
        source=rel,
        chunks=chunks,
        content_hash=content_hash,
    )
