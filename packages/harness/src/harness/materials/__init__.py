"""Material discovery and role inference for armories."""

from __future__ import annotations

import fnmatch
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from ai.logging import get_logger

try:
    import pathspec as _pathspec
except ImportError:
    pathspec: object | None = None
else:
    pathspec = _pathspec

_log = get_logger("materials")

MaterialKind = Literal["materials"]
MaterialRole = Literal[
    "assignment",
    "codebase",
    "lecture",
    "reference",
    "slides",
    "textbook",
]
type MaterialRoleInference = tuple[MaterialRole, float, str]

MATERIALS_DIR = "materials"
MATERIAL_DIRS: tuple[MaterialKind, ...] = (MATERIALS_DIR,)
IGNORE_FILE = ".harnessignore"
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
_CODE_SUFFIXES = frozenset((".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".h"))
_SLIDE_SUFFIXES = frozenset((".ppt", ".pptx"))
_TOKEN_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+")
_QUESTION_LINE_RE = re.compile(
    r"(?i)\b(?:question|problem|exercise|aufgabe)\s*\d+\b|[-*]\s*\([a-z]\)"
)
_DUE_RE = re.compile(r"(?i)\b(?:due\s+date|deadline|abgabe)\b")
_NUMBERED_SECTION_RE = re.compile(r"\b\d+(?:\.\d+){1,3}\b")
_CANONICAL_TEXTBOOK_RE = re.compile(r"(?i)<link[^>]+rel=[\"']canonical[\"'][^>]+textbook")


@dataclass(frozen=True, slots=True)
class MaterialFile:
    path: Path
    rel_path: str
    kind: MaterialKind
    role: MaterialRole
    confidence: float
    reason: str


def material_kind(rel_path: str | Path) -> MaterialKind | None:
    first = Path(rel_path).parts[0] if Path(rel_path).parts else ""
    if first == MATERIALS_DIR:
        return "materials"
    return None


def material_display_name(rel_path: str | Path) -> str:
    return str(rel_path).removeprefix(f"{MATERIALS_DIR}/")


def infer_material_role(rel_path: str | Path) -> MaterialRoleInference:
    """Infer a material role from structural path and file-format signals."""
    path = Path(rel_path)
    if path.suffix.lower() in _SLIDE_SUFFIXES:
        return "slides", 0.8, "file extension identifies a slide document"
    if path.suffix.lower() in _CODE_SUFFIXES:
        return "codebase", 0.75, "file extension identifies source code"
    tokens = _path_tokens(rel_path)
    if _has_any_token(tokens, "homework", "assignment", "assignments", "sheet", "sheets"):
        return "assignment", 0.76, "path identifies assignment material"
    if _has_any_token(tokens, "übungsblatt", "uebungsblatt", "exercise", "exercises"):
        return "assignment", 0.78, "path identifies exercise material"
    if _has_any_token(tokens, "slides", "deck", "folien"):
        return "slides", 0.78, "path identifies slide material"
    if _has_any_token(tokens, "lecture", "lectures", "vorlesung", "vorlesungen"):
        return "lecture", 0.76, "path identifies lecture material"
    if _has_any_token(tokens, "book", "textbook", "chapter"):
        return "textbook", 0.78, "path identifies textbook material"
    return "reference", 0.5, "default material role"


def infer_material_role_from_text(
    rel_path: str | Path,
    text: str,
) -> MaterialRoleInference:
    """Infer a material role from structural path and document-shape signals."""
    path_role = infer_material_role(rel_path)
    normalized = _normalized_text(text)
    if not normalized:
        return path_role
    if _looks_like_textbook_summary(rel_path, normalized):
        return "reference", 0.78, "summary page rather than primary textbook content"
    if _looks_like_textbook(rel_path, normalized):
        return "textbook", 0.85, "numbered textbook structure"
    if _looks_like_assignment(normalized):
        return "assignment", 0.8, "exercises sheet structure"
    if _looks_like_slides(normalized):
        return "slides", 0.8, "lecture slides structure"
    if _looks_like_course_notes(normalized):
        return "lecture", 0.82, "course notes or lectures structure"
    return path_role


def _path_tokens(rel_path: str | Path) -> set[str]:
    return {
        token.casefold()
        for token in _TOKEN_RE.findall(str(rel_path).replace("_", " ").replace("-", " "))
    }


def _has_any_token(tokens: set[str], *candidates: str) -> bool:
    return any(candidate.casefold() in tokens for candidate in candidates)


def _normalized_text(text: str) -> str:
    return " ".join(text.casefold().split())


def _looks_like_textbook_summary(rel_path: str | Path, text: str) -> bool:
    return "summary" in _path_tokens(rel_path) or bool(
        _NUMBERED_SECTION_RE.search(text) and " summary " in f" {text} "
    )


def _looks_like_textbook(rel_path: str | Path, text: str) -> bool:
    tokens = _path_tokens(rel_path)
    if "textbook" in tokens and _NUMBERED_SECTION_RE.search(text):
        return True
    if _CANONICAL_TEXTBOOK_RE.search(text):
        return True
    section_count = len(_NUMBERED_SECTION_RE.findall(text))
    return section_count >= 3 and "skip to main content" in text


def _looks_like_assignment(text: str) -> bool:
    question_count = len(_QUESTION_LINE_RE.findall(text))
    has_assignment_header = any(
        marker in text
        for marker in ("exercise sheet", "übungsblatt", "uebungsblatt", "assignment")
    )
    return (has_assignment_header and question_count >= 1) or (
        question_count >= 3 and bool(_DUE_RE.search(text))
    )


def _looks_like_slides(text: str) -> bool:
    has_contents = "table of contents" in text or "inhaltsverzeichnis" in text
    has_slide_shape = any(marker in text for marker in ("slides", "folien", "slide deck"))
    has_lecture_schedule = "lecture schedule" in text or "tutorial sessions" in text
    has_lecture_outline = "lecture goals" in text or "vorlesung overview" in text
    return any(
        (
            has_contents and (has_slide_shape or has_lecture_schedule or has_lecture_outline),
            "lecture notes" in text and has_contents and has_lecture_schedule,
        )
    )


def _looks_like_course_notes(text: str) -> bool:
    if "youtube-wrapper" in text and "lectures" in text:
        return True
    has_course_notes = "course materials and notes" in text or "course notes" in text
    return has_course_notes or ("table of contents" in text and "lecture" in text)


def iter_materials(armory_path: Path) -> Iterator[MaterialFile]:
    """Yield visible material files using armory ignore rules."""
    ignore_spec = _load_ignore_spec(armory_path)
    for file_path, rel, kind in _iter_visible_material_paths(armory_path, ignore_spec):
        role, confidence, reason = infer_material_role(rel)
        yield MaterialFile(
            path=file_path,
            rel_path=rel,
            kind=kind,
            role=role,
            confidence=confidence,
            reason=reason,
        )


def _iter_visible_material_paths(
    armory_path: Path,
    ignore_spec: object,
) -> Iterator[tuple[Path, str, MaterialKind]]:
    for dirname in MATERIAL_DIRS:
        folder = armory_path / dirname
        if not folder.is_dir():
            continue
        resolved_folder = _resolve_material_folder(folder)
        if resolved_folder is None:
            continue
        yield from _iter_visible_material_folder(
            armory_path,
            folder,
            resolved_folder,
            dirname,
            ignore_spec,
        )


def _iter_visible_material_folder(
    armory_path: Path,
    folder: Path,
    resolved_folder: Path,
    kind: MaterialKind,
    ignore_spec: object,
) -> Iterator[tuple[Path, str, MaterialKind]]:
    for file_path in sorted(folder.rglob("*")):
        if not _visible_material_file(file_path, folder, resolved_folder):
            continue
        rel = str(file_path.relative_to(armory_path))
        if not _matches_ignore(ignore_spec, rel):
            yield file_path, rel, kind


def _visible_material_file(
    file_path: Path,
    folder: Path,
    resolved_folder: Path,
) -> bool:
    if _unsafe_material_path(file_path, folder, resolved_folder):
        return False
    if not file_path.is_file():
        return False
    rel_to_material_dir = file_path.relative_to(folder)
    return not any(part.startswith(".") for part in rel_to_material_dir.parts)


def iter_material_files(armory_path: Path) -> Iterator[Path]:
    yield from (material.path for material in iter_materials(armory_path))


def count_material_files(armory_path: Path) -> int:
    return sum(1 for _material in iter_materials(armory_path))


def material_manifest(armory_path: Path) -> tuple[MaterialFile, ...]:
    return tuple(iter_materials(armory_path))


def _load_ignore_spec(armory_path: Path) -> object:
    """Load built-in and armory-local material ignore patterns."""
    patterns = _ignore_patterns(armory_path)
    if pathspec is not None:
        return pathspec.PathSpec.from_lines(  # ty:ignore[unresolved-attribute]
            "gitignore", patterns
        )
    return tuple(pattern for pattern in patterns if pattern and not pattern.startswith("#"))


def _ignore_patterns(armory_path: Path) -> list[str]:
    patterns = list(DEFAULT_IGNORE_PATTERNS)
    ignore_path = armory_path / IGNORE_FILE
    if not ignore_path.is_file():
        return patterns
    try:
        patterns.extend(ignore_path.read_text(encoding="utf-8").splitlines())
    except OSError:
        _log.warning("failed to read armory ignore file", exc_info=True)
    return patterns


def _resolve_material_folder(folder: Path) -> Path | None:
    if folder.is_symlink():
        _log.warning(
            "skipping symlinked material directory",
            extra={"fields": {"path": str(folder)}},
        )
        return None
    try:
        return folder.resolve(strict=True)
    except OSError:
        _log.warning(
            "failed to resolve material directory", extra={"fields": {"path": str(folder)}}
        )
        return None


def _unsafe_material_path(file_path: Path, folder: Path, resolved_folder: Path) -> bool:
    if _material_path_has_symlink(file_path, folder):
        _log.warning("skipping symlinked material", extra={"fields": {"path": str(file_path)}})
        return True
    try:
        resolved_path = file_path.resolve(strict=True)
    except OSError:
        return True
    if not resolved_path.is_relative_to(resolved_folder):
        _log.warning(
            "skipping material outside material directory",
            extra={"fields": {"path": str(file_path)}},
        )
        return True
    return False


def _material_path_has_symlink(file_path: Path, folder: Path) -> bool:
    try:
        rel_parts = file_path.relative_to(folder).parts
    except ValueError:
        return True
    current = folder
    for part in rel_parts:
        current /= part
        if current.is_symlink():
            return True
    return False


def _matches_ignore(ignore_spec: object, rel_path: str) -> bool:
    """Return whether *rel_path* is ignored, with a stdlib fallback."""
    match_file = getattr(ignore_spec, "match_file", None)
    if callable(match_file):
        result = match_file(rel_path)
        return bool(result)
    if not isinstance(ignore_spec, tuple):
        return False
    patterns = cast("tuple[object, ...]", ignore_spec)  # ty:ignore[redundant-cast]
    return any(
        _fallback_ignore_pattern_matches(pattern, rel_path)
        for pattern in patterns
        if isinstance(pattern, str)
    )


def _fallback_ignore_pattern_matches(pattern: str, rel_path: str) -> bool:
    if _directory_ignore_pattern_matches(pattern, rel_path):
        return True
    return fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(Path(rel_path).name, pattern)


def _directory_ignore_pattern_matches(pattern: str, rel_path: str) -> bool:
    if not pattern.endswith("/"):
        return False
    normalized = pattern.rstrip("/")
    return rel_path == normalized or rel_path.startswith(f"{normalized}/")


__all__ = [
    "DEFAULT_IGNORE_PATTERNS",
    "IGNORE_FILE",
    "MATERIALS_DIR",
    "MATERIAL_DIRS",
    "MaterialFile",
    "MaterialKind",
    "MaterialRole",
    "count_material_files",
    "infer_material_role",
    "infer_material_role_from_text",
    "iter_material_files",
    "iter_materials",
    "material_kind",
    "material_manifest",
]
