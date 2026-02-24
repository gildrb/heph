"""Filesystem IO helpers shared across features."""

from __future__ import annotations

from pathlib import Path
import tempfile


def atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write a file atomically using a temp file and rename."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding=encoding,
        dir=path.parent,
        delete=False,
    ) as tmp:
        tmp.write(content)
        temp_path = Path(tmp.name)

    temp_path.replace(path)

