"""Source feature use-cases."""

from __future__ import annotations

from hephaistos.shared.paths import normalize_path
from hephaistos.source.types import SourceItem


def add_source(file_arg: str) -> str:
    """Placeholder source add flow."""
    source_path = normalize_path(file_arg)
    item = SourceItem(path=source_path)
    return f"[todo] source add {item.path}"


def list_sources() -> str:
    """Placeholder source list flow."""
    return "[todo] source list"


def reindex_sources() -> str:
    """Placeholder source reindex flow."""
    return "[todo] source reindex"

