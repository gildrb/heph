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
import time
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from html.parser import HTMLParser
from pathlib import Path
from typing import Protocol, cast

from hephaion.logging import get_logger
from hephaion.rag.vector import cosine_similarity, embedding_rows

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
_PDF_OCR_TOTAL_TIMEOUT_SECONDS = 120
_PDF_OCR_MAX_PAGES = 25
_PDF_OCR_MAX_RENDERED_BYTES = 100 * 1024 * 1024
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
_COMMON_LATIN_OCR_REPAIRS = (
    (re.compile(r"\bBegriinden\b"), "Begründen"),
    (re.compile(r"\bbegriinden\b"), "begründen"),
    (re.compile(r"\bBegrundung\b"), "Begründung"),
    (re.compile(r"\bbegrundung\b"), "begründung"),
    (re.compile(r"\bfiir\b"), "für"),
    (re.compile(r"\bFiir\b"), "Für"),
)


class _MarkdownExportProtocol(Protocol):
    def export_to_markdown(self) -> str: ...


class _DoclingResultProtocol(Protocol):
    document: _MarkdownExportProtocol


class _DoclingConverterProtocol(Protocol):
    def convert(self, path: str) -> _DoclingResultProtocol: ...


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
_SentenceTransformerModel: _SentenceEncoderProtocol | None | object = _OPTIONAL_BACKEND_UNSET
_SEMANTIC_CHUNKING_MODEL = "all-MiniLM-L6-v2"


class ChunkStrategy(Enum):
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


@dataclass(slots=True)
class _MarkdownChunkBuilder:
    source: str
    next_index: int
    heading: str
    heading_level: int
    char_offset: int
    chunks: list[Chunk] = field(default_factory=list)

    def append(self, text: str) -> None:
        self.chunks.append(
            _markdown_chunk(
                text,
                self.source,
                self.next_index,
                self.char_offset,
                self.heading,
                self.heading_level,
            )
        )
        self.next_index += 1
        self.char_offset += len(text)

    def append_oversized_section(self, text: str, chunk_size: int) -> None:
        current = ""
        for part in _markdown_section_parts(text):
            part = part.strip()
            if not part:
                continue

            current = self._append_markdown_part(current, part, chunk_size)

        if current.strip():
            self.append(current)

    def _append_markdown_part(self, current: str, part: str, chunk_size: int) -> str:
        candidate = f"{current}\n\n{part}" if current else part
        if _markdown_candidate_overflows(candidate, current=current, chunk_size=chunk_size):
            if current:
                self.append(current)
            return part
        return candidate


@dataclass(frozen=True, slots=True)
class _MarkdownSection:
    text: str
    source: str
    first_index: int
    heading: str
    heading_level: int
    char_offset: int

    def chunk(self, text: str) -> Chunk:
        return _markdown_chunk(
            text,
            self.source,
            self.first_index,
            self.char_offset,
            self.heading,
            self.heading_level,
        )

    def builder(self) -> _MarkdownChunkBuilder:
        return _MarkdownChunkBuilder(
            source=self.source,
            next_index=self.first_index,
            heading=self.heading,
            heading_level=self.heading_level,
            char_offset=self.char_offset,
        )


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


def _is_docling_file(path: Path) -> bool:
    return path.suffix.lower() in _DOCLING_EXTENSIONS


def _is_pdf_file(path: Path) -> bool:
    return path.suffix.lower() == ".pdf"


class _HTMLTextExtractor(HTMLParser):
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
    converter_class = _docling_converter_class()
    if converter_class is None:
        return None
    if not _docling_converter:
        _docling_converter.append(converter_class())
    return _docling_converter[0]


def _convert_to_markdown(path: Path) -> str | None:
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
    if not _is_pdf_file(path) or not _is_pdftotext_available():
        return None
    completed = _run_extraction_command(
        path,
        ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
        timeout=_PDF_TEXT_TIMEOUT_SECONDS,
        warning="pdftotext extraction failed",
    )
    if completed is None:
        return None
    text = _normalize_extracted_text(completed.stdout)
    return text if text.strip() else None


def _convert_pdf_with_ocr(path: Path) -> str | None:
    if not _is_pdf_file(path) or not _is_pdf_ocr_available():
        return None

    texts = _extract_pdf_ocr_pages(path)
    if texts is None:
        return None

    text = _normalize_extracted_text("\n\n".join(texts))
    return text if text.strip() else None


def _extract_pdf_ocr_pages(path: Path) -> list[str] | None:
    try:
        with tempfile.TemporaryDirectory(prefix="heph-pdf-ocr-") as temp_dir:
            page_paths = _render_pdf_pages(path, Path(temp_dir))
            if not page_paths:
                return None
            deadline = time.monotonic() + _PDF_OCR_TOTAL_TIMEOUT_SECONDS
            return _ocr_pdf_pages(path, page_paths, deadline)
    except (OSError, subprocess.SubprocessError) as exc:
        _log_extraction_warning(path, "pdf OCR extraction failed", exc)
        return None


def _render_pdf_pages(path: Path, temp_dir: Path) -> list[Path]:
    output_prefix = str(temp_dir / "page")
    render = _run_extraction_command(
        path,
        [
            "pdftoppm",
            "-r",
            str(_PDF_OCR_DPI),
            "-f",
            "1",
            "-l",
            str(_PDF_OCR_MAX_PAGES),
            "-png",
            str(path),
            output_prefix,
        ],
        timeout=_PDF_OCR_RENDER_TIMEOUT_SECONDS,
        warning="pdf OCR render failed",
    )
    if render is None:
        return []
    return _bounded_pdf_ocr_page_paths(path, temp_dir)


def _bounded_pdf_ocr_page_paths(path: Path, temp_dir: Path) -> list[Path]:
    page_paths = sorted(temp_dir.glob("page-*.png"))
    if len(page_paths) > _PDF_OCR_MAX_PAGES:
        _log_extraction_failure(
            path,
            "pdf OCR render exceeded page limit",
            f"{len(page_paths)} page(s) rendered, limit is {_PDF_OCR_MAX_PAGES}",
        )
        return []

    total_bytes = 0
    for page_path in page_paths:
        total_bytes += page_path.stat().st_size
        if total_bytes > _PDF_OCR_MAX_RENDERED_BYTES:
            _log_extraction_failure(
                path,
                "pdf OCR render exceeded size limit",
                f"{total_bytes} byte(s) rendered, limit is {_PDF_OCR_MAX_RENDERED_BYTES}",
            )
            return []
    return page_paths


def _ocr_pdf_pages(path: Path, page_paths: Sequence[Path], deadline: float) -> list[str]:
    texts: list[str] = []
    for page_path in page_paths:
        remaining_seconds = deadline - time.monotonic()
        if remaining_seconds <= 0:
            _log_extraction_failure(
                path,
                "pdf OCR total deadline exceeded",
                f"limit is {_PDF_OCR_TOTAL_TIMEOUT_SECONDS} second(s)",
                fields={"page": page_path.name},
            )
            break
        page_timeout = min(_PDF_OCR_PAGE_TIMEOUT_SECONDS, remaining_seconds)
        page = _ocr_pdf_page(path, page_path, page_timeout)
        if page is not None:
            texts.append(page)
    return texts


def _ocr_pdf_page(path: Path, page_path: Path, timeout: float) -> str | None:
    page = _run_extraction_command(
        path,
        ["tesseract", str(page_path), "stdout", "-l", "eng"],
        timeout=timeout,
        warning="pdf OCR page failed",
        fields={"page": page_path.name},
    )
    return page.stdout if page is not None else None


def _run_extraction_command(
    path: Path,
    command: Sequence[str],
    *,
    timeout: float,
    warning: str,
    fields: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str] | None:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        _log_extraction_warning(path, warning, exc, fields=fields)
        return None
    if completed.returncode == 0:
        return completed

    detail = completed.stderr.strip() or f"exit status {completed.returncode}"
    _log_extraction_failure(path, warning, detail, fields=fields)
    return None


def _log_extraction_warning(
    path: Path,
    warning: str,
    exc: BaseException,
    *,
    fields: Mapping[str, str] | None = None,
) -> None:
    detail = str(exc).strip() or type(exc).__name__
    _log_extraction_failure(path, warning, detail, fields=fields)


def _log_extraction_failure(
    path: Path,
    warning: str,
    detail: str,
    *,
    fields: Mapping[str, str] | None = None,
) -> None:
    _log.warning(
        warning,
        extra={"fields": {"path": str(path), **dict(fields or {}), "error": detail}},
    )


def _convert_binary_to_indexable_text(path: Path) -> str | None:
    pdf_text = (
        _first_nonempty_conversion(path, _convert_pdf_to_text, _convert_pdf_with_ocr)
        if _is_pdf_file(path)
        else None
    )
    if pdf_text is not None:
        return pdf_text
    if not _is_docling_available():
        return None
    return _nonempty_text(_convert_to_markdown(path))


def _first_nonempty_conversion(
    path: Path,
    *converters: Callable[[Path], str | None],
) -> str | None:
    for converter in converters:
        if text := _nonempty_text(converter(path)):
            return text
    return None


def _nonempty_text(text: str | None) -> str | None:
    return text if text and text.strip() else None


def _normalize_extracted_text(text: str) -> str:
    normalized = unicodedata.normalize("NFC", text)
    repaired = _MISPLACED_DIAERESIS_RE.sub(
        lambda match: _UMLAUTS[match.group(1)],
        normalized,
    )
    for pattern, replacement in _COMMON_LATIN_OCR_REPAIRS:
        repaired = pattern.sub(replacement, repaired)
    without_placeholders = _EXTRACTION_PLACEHOLDER_RE.sub("", repaired)
    return _HTML_EXTRACTION_COMMENT_RE.sub("", without_placeholders)


def _parse_sections(text: str) -> list[tuple[str, int, int, int]]:
    matches = list(_HEADING_RE.finditer(text))

    if not matches:
        return _plain_text_sections(text)

    return [*_preamble_sections(text, matches[0]), *_heading_sections(text, matches)]


def _plain_text_sections(text: str) -> list[tuple[str, int, int, int]]:
    return [("", 0, 0, len(text))] if text.strip() else []


def _preamble_sections(text: str, first_heading: re.Match[str]) -> list[tuple[str, int, int, int]]:
    if first_heading.start() <= 0:
        return []
    preamble = text[: first_heading.start()]
    return [("", 0, 0, first_heading.start())] if preamble.strip() else []


def _heading_sections(
    text: str,
    matches: list[re.Match[str]],
) -> list[tuple[str, int, int, int]]:
    return [_heading_section(text, matches, index) for index in range(len(matches))]


def _heading_section(
    text: str,
    matches: list[re.Match[str]],
    index: int,
) -> tuple[str, int, int, int]:
    match = matches[index]
    end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
    return match.group(2).strip(), len(match.group(1)), match.start(), end


def _markdown_chunk(
    text: str,
    source: str,
    index: int,
    char_start: int,
    heading: str,
    heading_level: int,
) -> Chunk:
    return Chunk(
        text=text.strip(),
        source=source,
        index=index,
        char_start=char_start,
        char_end=char_start + len(text),
        heading=heading,
        heading_level=heading_level,
    )


def _chunk_markdown_section(
    section: _MarkdownSection,
    chunk_size: int,
) -> list[Chunk]:
    text = section.text.strip()
    if not text:
        return []

    if len(text) <= chunk_size:
        return [section.chunk(text)]
    builder = section.builder()
    builder.append_oversized_section(text, chunk_size)
    return builder.chunks


def _markdown_section_parts(text: str) -> list[str]:
    return re.split(r"\n\n+", text)


def _markdown_candidate_overflows(
    candidate: str,
    *,
    current: str,
    chunk_size: int,
) -> bool:
    return bool(current) and len(candidate) > chunk_size


def chunk_markdown(
    text: str,
    source: str,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    _overlap: int = _DEFAULT_OVERLAP,
) -> list[Chunk]:
    if not text or not text.strip():
        return []

    sections = _parse_sections(text)
    chunks: list[Chunk] = []
    idx = 0

    for heading_title, heading_level, start, end in sections:
        section_text = text[start:end]
        new_chunks = _chunk_markdown_section(
            _MarkdownSection(
                text=section_text,
                source=source,
                first_index=idx,
                heading=heading_title,
                heading_level=heading_level,
                char_offset=start,
            ),
            chunk_size,
        )
        chunks.extend(new_chunks)
        idx += len(new_chunks)

    return chunks


def _find_boundary(text: str, target: int, search_back: int) -> int:
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
    if not text:
        return []

    chunks: list[Chunk] = []
    pos = 0

    while pos < len(text):
        end = _text_chunk_end(text, pos=pos, chunk_size=chunk_size)
        chunk = _text_chunk(text, source=source, index=len(chunks), pos=pos, end=end)
        if chunk is not None:
            chunks.append(chunk)
        if _text_chunk_stalled(pos=pos, end=end, overlap=overlap):
            break
        pos = end - overlap

    return chunks


def _text_chunk_end(text: str, *, pos: int, chunk_size: int) -> int:
    end = min(pos + chunk_size, len(text))
    if end >= len(text):
        return end
    boundary = _find_boundary(text, end, chunk_size // 4)
    return boundary if boundary > pos else end


def _text_chunk(
    text: str,
    *,
    source: str,
    index: int,
    pos: int,
    end: int,
) -> Chunk | None:
    chunk_text_str = text[pos:end].strip()
    if not chunk_text_str:
        return None
    return Chunk(
        text=chunk_text_str,
        source=source,
        index=index,
        char_start=pos,
        char_end=end,
    )


def _text_chunk_stalled(*, pos: int, end: int, overlap: int) -> bool:
    return end - pos <= overlap


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


def _sentence_transformer_model() -> _SentenceEncoderProtocol | None:
    global _SentenceTransformerModel  # noqa: PLW0603
    if _SentenceTransformerModel is _OPTIONAL_BACKEND_UNSET:
        transformer_factory = _sentence_transformer_factory()
        _SentenceTransformerModel = (
            None if transformer_factory is None else transformer_factory(_SEMANTIC_CHUNKING_MODEL)
        )
    if _SentenceTransformerModel is None:
        return None
    return cast("_SentenceEncoderProtocol", _SentenceTransformerModel)


def chunk_semantic(
    text: str,
    source: str,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    overlap: int = _DEFAULT_OVERLAP,
    *,
    similarity_threshold: float = 0.5,
    min_chunk: int = 100,
) -> list[Chunk]:
    if not text or not text.strip():
        return []

    chunks = _try_chunk_semantic(
        text,
        source,
        similarity_threshold=similarity_threshold,
        min_chunk=min_chunk,
    )
    return chunks or chunk_text(text, source, chunk_size, overlap)


def _try_chunk_semantic(
    text: str,
    source: str,
    *,
    similarity_threshold: float,
    min_chunk: int,
) -> list[Chunk]:
    model = _sentence_transformer_model()
    if model is None:
        return []

    sentences = _split_sentences(text)
    if len(sentences) <= 1:
        return [_single_text_chunk(text, source)]

    emb_lists = _semantic_sentence_embeddings(model, sentences)
    if emb_lists is None:
        return []

    return _semantic_chunks_from_breakpoints(
        sentences,
        _semantic_breakpoints(emb_lists, similarity_threshold),
        source=source,
        min_chunk=min_chunk,
    )


def _single_text_chunk(text: str, source: str) -> Chunk:
    return Chunk(text=text.strip(), source=source, index=0, char_start=0, char_end=len(text))


def _semantic_sentence_embeddings(
    model: _SentenceEncoderProtocol,
    sentences: list[str],
) -> list[list[float]] | None:
    emb_lists = embedding_rows(
        model.encode(sentences, convert_to_numpy=True, show_progress_bar=False)
    )
    return emb_lists if len(emb_lists) == len(sentences) else None


def _semantic_breakpoints(
    emb_lists: list[list[float]],
    similarity_threshold: float,
) -> list[int]:
    breakpoints = [0]
    for index in range(1, len(emb_lists)):
        sim = cosine_similarity(emb_lists[index - 1], emb_lists[index])
        if sim < similarity_threshold:
            breakpoints.append(index)
    breakpoints.append(len(emb_lists))
    return breakpoints


def _semantic_chunks_from_breakpoints(
    sentences: list[str],
    breakpoints: list[int],
    *,
    source: str,
    min_chunk: int,
) -> list[Chunk]:
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

    return chunks


def _split_sentences(text: str) -> list[str]:
    return [
        sentence
        for part in re.split(r"(?<=[.!?])\s+", text)
        for sentence in (line.strip() for line in part.split("\n"))
        if sentence
    ]


def _resolve_strategy(
    strategy: ChunkStrategy, path: Path
) -> Callable[[str, str, int, int], list[Chunk]]:
    if strategy == ChunkStrategy.AUTO:
        if path.suffix.lower() in (".md", ".mdown", ".markdown"):
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
    if _resolved_path_within_armory(path, armory_root) is None:
        return None

    rel = str(path.relative_to(armory_root))
    if not _is_text_file(path):
        return _chunk_binary_file(path, rel, chunk_size=chunk_size, overlap=overlap)

    text = _read_normalized_text_file(path)
    if text is None:
        return None

    chunk_fn = _resolve_strategy(strategy, path)
    chunks: list[Chunk] = chunk_fn(text, rel, chunk_size, overlap)

    return ChunkedDocument(
        source=rel,
        chunks=chunks,
        content_hash=_text_content_hash(text),
    )


def _chunk_binary_file(
    path: Path,
    rel: str,
    *,
    chunk_size: int,
    overlap: int,
) -> ChunkedDocument | None:
    if not _can_convert_binary_file(path):
        return None
    text = _nonempty_text(_convert_binary_to_indexable_text(path))
    if text is None:
        return None
    return ChunkedDocument(
        source=rel,
        chunks=chunk_markdown(text, rel, chunk_size, overlap),
        content_hash=hashlib.sha256(path.read_bytes()).hexdigest()[:16],
    )


def _read_normalized_text_file(path: Path) -> str | None:
    try:
        text = _read_indexable_text(path)
    except (UnicodeDecodeError, OSError):
        return None
    text = _nonempty_text(text)
    if text is None:
        return None
    return _nonempty_text(_normalize_extracted_text(text))


def _text_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
