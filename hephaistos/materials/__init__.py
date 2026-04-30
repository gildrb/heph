"""Study material discovery for armories.

The on-disk armory layout still uses ``source/`` for primary study material
and ``library/`` for reference material. This package owns the domain language
and file-discovery rules so retrieval, sessions, and CLI commands do not each
carry their own idea of what "source" means.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from hephaistos.logging import get_logger

try:
    import pathspec
except ImportError:
    pathspec = None  # type: ignore[assignment]

_log = get_logger("materials")

MaterialKind = Literal["source", "library"]

MATERIAL_DIRS: tuple[MaterialKind, ...] = ("source", "library")
IGNORE_FILE = ".hephaistosignore"
DEFAULT_IGNORE_PATTERNS: tuple[str, ...] = (
    ".git/",
    ".hg/",
    ".svn/",
    ".DS_Store",
    "__pycache__/",
    "*.pyc",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
)


@dataclass(frozen=True, slots=True)
class MaterialFile:
    """A study material file discovered inside an armory."""

    path: Path
    rel_path: str
    kind: MaterialKind


def material_kind(rel_path: str | Path) -> MaterialKind | None:
    """Return the material kind for a relative armory path."""
    first = Path(rel_path).parts[0] if Path(rel_path).parts else ""
    if first == "source":
        return "source"
    if first == "library":
        return "library"
    return None


def iter_materials(armory_path: Path) -> Iterator[MaterialFile]:
    """Yield visible source/library material files using armory ignore rules."""
    ignore_spec = _load_ignore_spec(armory_path)
    for dirname in MATERIAL_DIRS:
        folder = armory_path / dirname
        if not folder.is_dir():
            continue
        for file_path in sorted(folder.rglob("*")):
            if not file_path.is_file():
                continue
            rel_to_material_dir = file_path.relative_to(folder)
            if any(part.startswith(".") for part in rel_to_material_dir.parts):
                continue
            rel = str(file_path.relative_to(armory_path))
            if _matches_ignore(ignore_spec, rel):
                continue
            yield MaterialFile(path=file_path, rel_path=rel, kind=dirname)


def iter_material_files(armory_path: Path) -> Iterator[Path]:
    """Yield visible study material paths in stable order."""
    for material in iter_materials(armory_path):
        yield material.path


def count_material_files(armory_path: Path) -> int:
    """Return the number of visible study material files in an armory."""
    return sum(1 for _material in iter_materials(armory_path))


def material_manifest(armory_path: Path) -> tuple[MaterialFile, ...]:
    """Return all visible study materials with classification metadata."""
    return tuple(iter_materials(armory_path))


def _load_ignore_spec(armory_path: Path) -> object:
    """Load built-in and armory-local material ignore patterns."""
    patterns = list(DEFAULT_IGNORE_PATTERNS)
    ignore_path = armory_path / IGNORE_FILE
    if ignore_path.is_file():
        try:
            patterns.extend(ignore_path.read_text(encoding="utf-8").splitlines())
        except OSError:
            _log.warning("failed to read armory ignore file", exc_info=True)
    if pathspec is not None:
        return pathspec.PathSpec.from_lines(  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
            "gitignore", patterns
        )
    return tuple(pattern for pattern in patterns if pattern and not pattern.startswith("#"))


def _matches_ignore(ignore_spec: object, rel_path: str) -> bool:
    """Return whether *rel_path* is ignored, with a stdlib fallback."""
    match_file = getattr(ignore_spec, "match_file", None)
    if callable(match_file):
        result = match_file(rel_path)
        return bool(result)
    if not isinstance(ignore_spec, tuple):
        return False
    patterns = cast("tuple[object, ...]", ignore_spec)
    for pattern in patterns:
        if not isinstance(pattern, str):
            continue
        normalized = pattern.rstrip("/")
        if pattern.endswith("/") and (
            rel_path == normalized or rel_path.startswith(f"{normalized}/")
        ):
            return True
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(Path(rel_path).name, pattern):
            return True
    return False


__all__ = [
    "DEFAULT_IGNORE_PATTERNS",
    "IGNORE_FILE",
    "MATERIAL_DIRS",
    "MaterialFile",
    "MaterialKind",
    "count_material_files",
    "iter_material_files",
    "iter_materials",
    "material_kind",
    "material_manifest",
]
