"""Lazy PDFium loading for native PDF text extraction."""

from __future__ import annotations

import importlib
from collections.abc import Iterator
from functools import lru_cache
from typing import TYPE_CHECKING, Protocol, Self, cast

if TYPE_CHECKING:
    import pypdfium2  # noqa: F401


class PdfiumDocument(Protocol):
    def __enter__(self) -> Self: ...

    def __exit__(self, *_args: object) -> None: ...

    def __iter__(self) -> Iterator[PdfiumPage]: ...


class PdfiumPage(Protocol):
    def get_textpage(self) -> PdfiumTextPage: ...


class PdfiumTextPage(Protocol):
    def get_text_range(self) -> str: ...

    def close(self) -> None: ...


class _PdfiumModule(Protocol):
    PdfDocument: type[PdfiumDocument]


@lru_cache(maxsize=1)
def _pypdfium2_module() -> _PdfiumModule:
    return cast("_PdfiumModule", importlib.import_module("pypdfium2"))


def open_pdf_document(path: str) -> PdfiumDocument:
    return _pypdfium2_module().PdfDocument(path)
