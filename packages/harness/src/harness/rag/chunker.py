"""Text chunking for RAG indexing.

Splits text files into chunks with metadata preservation.

Chunking strategies (selectable via ``ChunkStrategy``):

- **AUTO** (default): picks the best strategy per file - Markdown files get
  structure-aware chunking, all other text files use semantic chunking when
  ``sentence-transformers`` is available, falling back to fixed-window.
- **MARKDOWN**: structure-aware - respects ``#`` headers, splits oversized
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
import shutil
import subprocess
import tempfile
import time
import unicodedata
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Protocol, cast
from zipfile import BadZipFile, ZipFile

import pypdfium2
from ai.logging import get_logger
from defusedxml import ElementTree

from harness.rag.file_safety import (
    open_file_exceeds_limit,
    regular_file_content_hash,
    regular_file_reader,
    temporary_regular_file_copy,
)
from harness.rag.html_text import extract_html_text

_log = get_logger("harness.rag.chunker")


class _XmlElement(Protocol):
    tag: str
    text: str | None
    attrib: Mapping[str, str]

    def __iter__(self) -> Iterator[_XmlElement]: ...

    def iter(self) -> Iterator[_XmlElement]: ...

    def itertext(self) -> Iterator[str]: ...


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

_DOCUMENT_EXTENSIONS = frozenset(
    {
        ".pdf",
        ".docx",
        ".pptx",
        ".xlsx",
        ".odt",
        ".ods",
    }
)
_DOCLING_EXTENSIONS = _DOCUMENT_EXTENSIONS
_UNSUPPORTED_DOCUMENT_EXTENSIONS = frozenset({".doc", ".ppt", ".xls", ".odp", ".rtf"})

_DEFAULT_CHUNK_SIZE = 500
_DEFAULT_OVERLAP = 100
_MAX_CHUNK_SIZE = 2000
_PDF_TEXT_TIMEOUT_SECONDS = 30
_PDF_OCR_RENDER_TIMEOUT_SECONDS = 60
_PDF_OCR_PAGE_TIMEOUT_SECONDS = 45
_PDF_OCR_TOTAL_TIMEOUT_SECONDS = 120
_PDF_INFO_TIMEOUT_SECONDS = 10
_PDF_OCR_MAX_PAGES = 25
_PDF_OCR_MAX_RENDERED_BYTES = 100 * 1024 * 1024
_PDF_OCR_MAX_SOURCE_BYTES = 50 * 1024 * 1024
_PDF_OCR_DPI = 200
_MAX_INDEXABLE_TEXT_BYTES = 5 * 1024 * 1024
_MAX_DOCUMENT_SOURCE_BYTES = 50 * 1024 * 1024
_MAX_ARCHIVE_MEMBERS = 2000
_MAX_ARCHIVE_MEMBER_BYTES = 20 * 1024 * 1024
_MAX_ARCHIVE_TOTAL_BYTES = 100 * 1024 * 1024
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


class ChunkStrategy(Enum):
    AUTO = "auto"  # markdown → chunk_markdown, else → fixed-window text
    MARKDOWN = "markdown"  # always use chunk_markdown
    SEMANTIC = "semantic"  # compatibility alias for fixed-window text
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


def _is_text_file(path: Path, *, root: Path | None = None) -> bool:
    if path.suffix.lower() in _TEXT_EXTENSIONS:
        return True
    if path.suffix.lower() in _DOCUMENT_EXTENSIONS:
        return False
    with regular_file_reader(path, root=root) as file:
        if file is None or open_file_exceeds_limit(file, _MAX_INDEXABLE_TEXT_BYTES):
            return False
        sample = file.read(8192)
        return b"\x00" not in sample


def _is_document_file(path: Path) -> bool:
    return path.suffix.lower() in _DOCUMENT_EXTENSIONS


def _is_pdf_file(path: Path) -> bool:
    return path.suffix.lower() == ".pdf"


def _read_indexable_text(path: Path, *, root: Path | None = None) -> str:
    with regular_file_reader(path, root=root) as file:
        if file is None:
            return ""
        if open_file_exceeds_limit(file, _MAX_INDEXABLE_TEXT_BYTES):
            _log_extraction_failure(
                path,
                "text file exceeded indexable size limit",
                f"limit is {_MAX_INDEXABLE_TEXT_BYTES} byte(s)",
            )
            return ""
        text = file.read().decode("utf-8")
    if path.suffix.lower() not in {".html", ".htm"}:
        return text
    return extract_html_text(text)


def _is_pdftotext_available() -> bool:
    return shutil.which("pdftotext") is not None


def _is_pdf_ocr_available() -> bool:
    return shutil.which("pdftoppm") is not None and shutil.which("tesseract") is not None


def _can_convert_binary_file(path: Path) -> bool:
    return _is_document_file(path)


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


def _archive_members(path: Path) -> dict[str, bytes] | None:
    try:
        with ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > _MAX_ARCHIVE_MEMBERS:
                raise ValueError("archive contains too many members")
            members: dict[str, bytes] = {}
            total = 0
            for info in infos:
                name = Path(info.filename)
                if name.is_absolute() or ".." in name.parts:
                    raise ValueError("archive contains a traversal path")
                if info.file_size > _MAX_ARCHIVE_MEMBER_BYTES:
                    raise ValueError("archive member exceeds size limit")
                total += info.file_size
                if total > _MAX_ARCHIVE_TOTAL_BYTES:
                    raise ValueError("archive exceeds expanded size limit")
                members[info.filename] = archive.read(info)
            return members
    except (BadZipFile, OSError, ValueError) as exc:
        _log_extraction_failure(path, "document archive rejected", str(exc))
        return None


def _xml_member(members: dict[str, bytes], name: str) -> _XmlElement | None:
    raw = members.get(name)
    if raw is None:
        return None
    try:
        return cast("_XmlElement", ElementTree.fromstring(raw))
    except (ElementTree.ParseError, ValueError) as exc:
        raise ValueError(f"invalid XML member {name}: {exc}") from exc


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _xml_text(element: object) -> str:
    return "".join(str(text) for text in cast("_XmlElement", element).itertext())


def _extract_docx(path: Path, members: dict[str, bytes]) -> str:
    root = _xml_member(members, "word/document.xml")
    if root is None:
        raise ValueError("DOCX document.xml is missing")
    lines: list[str] = []
    for element in root.iter():
        name = _local_name(element.tag)
        if name == "t" and element.text:
            lines.append(element.text)
        elif name == "tab":
            lines.append("\t")
        elif name in {"p", "tr"}:
            lines.append("\n")
    return "".join(lines)


def _extract_pptx(path: Path, members: dict[str, bytes]) -> str:
    slide_names = sorted(
        (
            name
            for name in members
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        ),
        key=lambda name: int(Path(name).stem.removeprefix("slide")),
    )
    slides: list[str] = []
    for name in slide_names:
        root = _xml_member(members, name)
        if root is None:
            continue
        slides.append(
            "\n".join(
                element.text or "" for element in root.iter() if _local_name(element.tag) == "t"
            )
        )
    return "\n\n".join(slides)


def _extract_xlsx(path: Path, members: dict[str, bytes]) -> str:
    shared = _xlsx_shared_strings(members)
    sheet_names = sorted(
        (
            name
            for name in members
            if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
        ),
        key=lambda name: int(Path(name).stem.removeprefix("sheet")),
    )
    sheets: list[str] = []
    for name in sheet_names:
        root = _xml_member(members, name)
        if root is None:
            continue
        sheets.append("\n".join(_xlsx_rows(root, shared)))
    return "\n\n".join(sheets)


def _xlsx_shared_strings(members: dict[str, bytes]) -> list[str]:
    root = _xml_member(members, "xl/sharedStrings.xml")
    if root is None:
        return []
    return [_xml_text(element) for element in root.iter() if _local_name(element.tag) == "si"]


def _xlsx_rows(root: object, shared: list[str]) -> list[str]:
    root = cast("_XmlElement", root)
    rows: list[str] = []
    for row in (element for element in root.iter() if _local_name(element.tag) == "row"):
        values = [_xlsx_cell_value(cell, shared) for cell in row if _local_name(cell.tag) == "c"]
        if values:
            rows.append("\t".join(values))
    return rows


def _xlsx_cell_value(cell: object, shared: list[str]) -> str:
    cell = cast("_XmlElement", cell)
    kind = cell.attrib.get("t", "")
    if kind == "inlineStr":
        return _xml_text(cell)
    value_element = next((element for element in cell if _local_name(element.tag) == "v"), None)
    value = value_element.text if value_element is not None else ""
    if kind == "s" and value:
        return shared[int(value)]
    return value or ""


def _extract_odf(path: Path, members: dict[str, bytes]) -> str:
    root = _xml_member(members, "content.xml")
    if root is None:
        raise ValueError("ODF content.xml is missing")
    lines: list[str] = []
    table_repeat = "{urn:oasis:names:tc:opendocument:xmlns:table:1.0}number-columns-repeated"

    def visit(element: object, *, in_table: bool = False) -> None:
        element = cast("_XmlElement", element)
        name = _local_name(element.tag)
        if name == "table-row":
            values: list[str] = []
            for cell in element:
                if _local_name(cell.tag) != "table-cell":
                    continue
                text = " ".join(_xml_text(cell).split())
                repeat = int(cell.attrib.get(table_repeat, "1"))
                values.extend([text] * min(repeat, _MAX_ARCHIVE_MEMBERS))
            if values:
                lines.append("\t".join(values))
            return
        if name in {"p", "h"} and not in_table:
            text = " ".join(_xml_text(element).split())
            if text:
                lines.append(text)
            return
        for child in element:
            visit(child, in_table=in_table or name == "table-cell")

    visit(root)
    return "\n".join(lines)


def _convert_native_document(path: Path) -> str | None:
    if _file_exceeds_limit(path, _MAX_DOCUMENT_SOURCE_BYTES):
        _log_extraction_failure(
            path,
            "document exceeded conversion source size limit",
            f"limit is {_MAX_DOCUMENT_SOURCE_BYTES} byte(s)",
        )
        return None
    members = _archive_members(path)
    if members is None:
        return None
    try:
        suffix = path.suffix.lower()
        if suffix == ".docx":
            text = _extract_docx(path, members)
        elif suffix == ".pptx":
            text = _extract_pptx(path, members)
        elif suffix == ".xlsx":
            text = _extract_xlsx(path, members)
        else:
            text = _extract_odf(path, members)
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        _log_extraction_failure(path, "document extraction failed", str(exc))
        return None
    return _normalize_extracted_text(text)


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


def _convert_pdf_with_pdfium(path: Path) -> str | None:
    if not _is_pdf_file(path):
        return None
    try:
        document = pypdfium2.PdfDocument(str(path))
        text = "\n".join(page.get_textpage().get_text_range() for page in document)
    except (ImportError, OSError, RuntimeError, ValueError) as exc:
        _log_extraction_warning(path, "pypdfium2 extraction failed", exc)
        return None
    normalized = _normalize_extracted_text(text)
    return normalized if normalized.strip() else None


def _convert_pdf_with_ocr(path: Path) -> str | None:
    if not _is_pdf_file(path) or not _is_pdf_ocr_available():
        return None
    if _file_exceeds_limit(path, _PDF_OCR_MAX_SOURCE_BYTES):
        _log_extraction_failure(
            path,
            "pdf OCR source exceeded size limit",
            f"limit is {_PDF_OCR_MAX_SOURCE_BYTES} byte(s)",
        )
        return None

    texts = _extract_pdf_ocr_pages(path)
    if texts is None:
        return None

    text = _normalize_extracted_text("\n\n".join(texts))
    return text if text.strip() else None


def _extract_pdf_ocr_pages(path: Path) -> list[str] | None:
    try:
        with tempfile.TemporaryDirectory(prefix="heph-pdf-ocr-") as temp_dir:
            deadline = time.monotonic() + _PDF_OCR_TOTAL_TIMEOUT_SECONDS
            page_paths = _render_pdf_pages(path, Path(temp_dir), deadline)
            if not page_paths:
                return None
            return _ocr_pdf_pages(path, page_paths, deadline)
    except (OSError, subprocess.SubprocessError) as exc:
        _log_extraction_warning(path, "pdf OCR extraction failed", exc)
        return None


def _render_pdf_pages(path: Path, temp_dir: Path, deadline: float) -> list[Path]:
    page_paths: list[Path] = []
    total_bytes = 0
    page_count = _pdf_page_count(path)
    page_limit = min(page_count or _PDF_OCR_MAX_PAGES, _PDF_OCR_MAX_PAGES)
    for page_number in range(1, page_limit + 1):
        remaining_seconds = deadline - time.monotonic()
        if remaining_seconds <= 0:
            _log_extraction_failure(
                path,
                "pdf OCR total deadline exceeded during render",
                f"limit is {_PDF_OCR_TOTAL_TIMEOUT_SECONDS} second(s)",
            )
            return []
        rendered_pages = _render_pdf_page(
            path,
            temp_dir,
            page_number,
            timeout=min(_PDF_OCR_RENDER_TIMEOUT_SECONDS, remaining_seconds),
            log_failure=page_count is not None or not page_paths,
        )
        if not rendered_pages:
            break
        page_paths.extend(rendered_pages)
        total_bytes += sum(page_path.stat().st_size for page_path in rendered_pages)
        if total_bytes > _PDF_OCR_MAX_RENDERED_BYTES:
            _log_extraction_failure(
                path,
                "pdf OCR render exceeded size limit",
                f"{total_bytes} byte(s) rendered, limit is {_PDF_OCR_MAX_RENDERED_BYTES}",
            )
            return []
    return page_paths


def _render_pdf_page(
    path: Path,
    temp_dir: Path,
    page_number: int,
    *,
    timeout: float,
    log_failure: bool,
) -> list[Path]:
    output_prefix = temp_dir / f"page-{page_number:03d}"
    render = _run_extraction_command(
        path,
        [
            "pdftoppm",
            "-r",
            str(_PDF_OCR_DPI),
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            "-png",
            str(path),
            str(output_prefix),
        ],
        timeout=timeout,
        warning="pdf OCR render failed",
        fields={"page": str(page_number)},
        log_failure=log_failure,
    )
    if render is None:
        return []
    return sorted(temp_dir.glob(f"{output_prefix.name}*.png"))


def _pdf_page_count(path: Path) -> int | None:
    if shutil.which("pdfinfo") is None:
        return None
    completed = _run_extraction_command(
        path,
        ["pdfinfo", str(path)],
        timeout=_PDF_INFO_TIMEOUT_SECONDS,
        warning="pdf page count failed",
        log_failure=False,
    )
    if completed is None:
        return None
    for line in completed.stdout.splitlines():
        key, separator, raw_value = line.partition(":")
        if separator and key.strip() == "Pages":
            return _parse_positive_int(raw_value.strip())
    return None


def _parse_positive_int(value: str) -> int | None:
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


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
    log_failure: bool = True,
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
    if not log_failure:
        return None

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


def _file_exceeds_limit(path: Path, limit: int) -> bool:
    try:
        return path.stat().st_size > limit
    except OSError:
        return True


def _convert_binary_to_indexable_text(path: Path) -> str | None:
    pdf_text = (
        _first_nonempty_conversion(
            path,
            _convert_pdf_to_text,
            _convert_pdf_with_pdfium,
            _convert_pdf_with_ocr,
        )
        if _is_pdf_file(path)
        else None
    )
    if pdf_text is not None:
        return pdf_text
    if path.suffix.lower() in _UNSUPPORTED_DOCUMENT_EXTENSIONS:
        _log_extraction_failure(
            path,
            "unsupported document format",
            "convert to .docx, .pptx, .xlsx, PDF, or plain text",
        )
        return None
    return _nonempty_text(_convert_native_document(path))


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


def chunk_semantic(
    text: str,
    source: str,
    chunk_size: int = _DEFAULT_CHUNK_SIZE,
    overlap: int = _DEFAULT_OVERLAP,
    *,
    similarity_threshold: float = 0.5,
    min_chunk: int = 100,
) -> list[Chunk]:
    """Compatibility entry point using the lexical fixed-window chunker."""
    del similarity_threshold, min_chunk
    return chunk_text(text, source, chunk_size, overlap)


def _resolve_strategy(
    strategy: ChunkStrategy, path: Path
) -> Callable[[str, str, int, int], list[Chunk]]:
    if strategy == ChunkStrategy.AUTO:
        if path.suffix.lower() in (".md", ".mdown", ".markdown"):
            return chunk_markdown
        return chunk_text
    if strategy == ChunkStrategy.MARKDOWN:
        return chunk_markdown
    if strategy == ChunkStrategy.SEMANTIC:
        return chunk_text
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
    if not _is_text_file(path, root=armory_root):
        return _chunk_binary_file(
            path,
            rel,
            root=armory_root,
            chunk_size=chunk_size,
            overlap=overlap,
        )

    text = _read_normalized_text_file(path, root=armory_root)
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
    root: Path | None,
    chunk_size: int,
    overlap: int,
) -> ChunkedDocument | None:
    if not _can_convert_binary_file(path):
        return None
    with temporary_regular_file_copy(
        path,
        root=root,
        max_bytes=_MAX_DOCUMENT_SOURCE_BYTES,
        on_limit_exceeded=lambda: _log_extraction_failure(
            path,
            "document exceeded conversion source size limit",
            f"limit is {_MAX_DOCUMENT_SOURCE_BYTES} byte(s)",
        ),
    ) as snapshot_path:
        if snapshot_path is None:
            return None
        text = _nonempty_text(_convert_binary_to_indexable_text(snapshot_path))
        content_hash = regular_file_content_hash(snapshot_path)
    if text is None:
        return None
    if content_hash is None:
        return None
    return ChunkedDocument(
        source=rel,
        chunks=chunk_markdown(text, rel, chunk_size, overlap),
        content_hash=content_hash,
    )


def _read_normalized_text_file(path: Path, *, root: Path | None = None) -> str | None:
    try:
        text = _read_indexable_text(path, root=root)
    except (UnicodeDecodeError, OSError):
        return None
    text = _nonempty_text(text)
    if text is None:
        return None
    return _nonempty_text(_normalize_extracted_text(text))


def _text_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
