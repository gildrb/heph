"""Shared material import helpers."""

from __future__ import annotations

import filecmp
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_IMPORT_SUFFIXES = frozenset(
    (
        ".bash",
        ".bib",
        ".c",
        ".cfg",
        ".cpp",
        ".csv",
        ".css",
        ".doc",
        ".docx",
        ".fish",
        ".go",
        ".graphql",
        ".h",
        ".hpp",
        ".html",
        ".ini",
        ".java",
        ".json",
        ".kt",
        ".log",
        ".md",
        ".mdown",
        ".markdown",
        ".odp",
        ".ods",
        ".odt",
        ".pdf",
        ".php",
        ".ppt",
        ".pptx",
        ".py",
        ".rb",
        ".rst",
        ".rtf",
        ".rs",
        ".sh",
        ".sql",
        ".svg",
        ".swift",
        ".tex",
        ".toml",
        ".ts",
        ".tsv",
        ".txt",
        ".xls",
        ".xlsx",
        ".xml",
        ".yaml",
        ".yml",
        ".zig",
        ".zsh",
    )
)


@dataclass(frozen=True, slots=True)
class ImportMaterialsResult:
    imported: tuple[str, ...]
    considered: int
    skipped_duplicates: int = 0
    skipped_unsupported: int = 0

    @property
    def skipped(self) -> int:
        return self.skipped_duplicates + self.skipped_unsupported


def resolve_import_source(raw: str) -> Path:
    source = Path(raw).expanduser()
    if source.exists():
        return source.resolve()

    try:
        parts = shlex.split(raw)
    except ValueError:
        return source.resolve()

    if len(parts) == 1:
        return Path(parts[0]).expanduser().resolve()
    return source.resolve()


def import_material_files(source: Path, dest_dir: Path) -> ImportMaterialsResult:
    dest_dir.mkdir(parents=True, exist_ok=True)
    candidates = _import_candidates(source)
    targets = [target for target in candidates if _supported_import_target(target, source)]
    imported: list[str] = []
    skipped_duplicates = 0
    for target in targets:
        dest = _next_import_destination(target, dest_dir)
        if dest is None:
            skipped_duplicates += 1
            continue
        shutil.copy2(target, dest)
        imported.append(dest.name)
    return ImportMaterialsResult(
        imported=tuple(imported),
        considered=len(candidates),
        skipped_duplicates=skipped_duplicates,
        skipped_unsupported=len(candidates) - len(targets),
    )


def _import_candidates(source: Path) -> list[Path]:
    if source.is_symlink():
        return [source]
    return sorted(source.rglob("*")) if source.is_dir() else [source]


def import_targets(source: Path) -> tuple[Path, ...]:
    return tuple(
        target for target in _import_candidates(source) if _supported_import_target(target, source)
    )


def _supported_import_target(target: Path, source: Path) -> bool:
    if target.is_symlink() or not target.is_file():
        return False
    if source.is_dir() and _path_has_hidden_part(target, source):
        return False
    return target.suffix.lower() in SUPPORTED_IMPORT_SUFFIXES


def _path_has_hidden_part(target: Path, source: Path) -> bool:
    try:
        parts = target.relative_to(source).parts
    except ValueError:
        return True
    return any(part.startswith(".") for part in parts)


def _next_import_destination(target: Path, dest_dir: Path) -> Path | None:
    dest = dest_dir / target.name
    if not dest.exists():
        return dest
    if _same_file_content(target, dest):
        return None

    stem = target.stem
    suffix = target.suffix
    for index in range(2, 10_000):
        candidate = dest_dir / f"{stem}-{index}{suffix}"
        if not candidate.exists():
            return candidate
        if _same_file_content(target, candidate):
            return None

    msg = f"Could not find a free filename for {target.name}"
    raise RuntimeError(msg)


def _same_file_content(left: Path, right: Path) -> bool:
    try:
        return filecmp.cmp(left, right, shallow=False)
    except OSError:
        return False
