"""Bounded Docling conversion worker for RAG indexing."""

from __future__ import annotations

import contextlib
import io
import sys
from pathlib import Path
from typing import Protocol, cast


class _MarkdownExport(Protocol):
    def export_to_markdown(self) -> str: ...


class _DoclingResult(Protocol):
    document: _MarkdownExport


class _DoclingConverter(Protocol):
    def convert(self, path: str) -> _DoclingResult: ...


class _DoclingConverterClass(Protocol):
    def __call__(self) -> _DoclingConverter: ...


EXIT_ERROR = 1
EXIT_UNAVAILABLE = 2
EXIT_OUTPUT_LIMIT = 3
EXIT_USAGE = 64


def _document_converter_class() -> _DoclingConverterClass | None:
    try:
        from docling.document_converter import DocumentConverter
    except ImportError:
        return None
    return cast("_DoclingConverterClass", DocumentConverter)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        return EXIT_USAGE
    path = Path(args[0])
    try:
        output_limit = int(args[1])
    except ValueError:
        return EXIT_USAGE
    document_converter = _document_converter_class()
    if document_converter is None:
        return EXIT_UNAVAILABLE
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = document_converter().convert(str(path))
            markdown = result.document.export_to_markdown()
    except Exception as exc:
        sys.stderr.write(str(exc).strip() or type(exc).__name__)
        return EXIT_ERROR
    if len(markdown) > output_limit:
        return EXIT_OUTPUT_LIMIT
    sys.stdout.write(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
