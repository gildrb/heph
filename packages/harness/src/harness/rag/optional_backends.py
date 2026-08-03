"""Cheap runtime capability probes for document extraction."""

from __future__ import annotations

import importlib.util
import shutil
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BackendCapability:
    name: str
    available: bool
    enables: str
    fallback: str


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def capabilities() -> tuple[BackendCapability, ...]:
    """Return cheap, built-in capability status without importing backends."""
    return (
        BackendCapability(
            name="pdftotext",
            available=shutil.which("pdftotext") is not None,
            enables="layout-aware PDF text extraction",
            fallback="bundled pypdfium2 extraction remains available",
        ),
        BackendCapability(
            name="documents",
            available=True,
            enables="DOCX, PPTX, XLSX, ODT, and ODS extraction",
            fallback="DOC, PPT, XLS, ODP, and RTF require conversion",
        ),
        BackendCapability(
            name="retrieval",
            available=_module_available("harness"),
            enables="stdlib BM25 and TF-IDF lexical retrieval",
            fallback="none",
        ),
    )
