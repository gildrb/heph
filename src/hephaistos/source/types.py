"""Types for source feature."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SourceItem:
    """Represents an input source file."""

    path: Path

