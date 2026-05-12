"""Study material discovery for armories.

User study files live under ``materials/``. Hephaistos infers the role of files
inside that folder instead of requiring users to classify them into separate
buckets.
"""

from __future__ import annotations

import fnmatch
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from hephaistos.logging import get_logger

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
    "past_exam",
    "reference",
    "slides",
    "textbook",
    "vocabulary",
]

MATERIALS_DIR = "materials"
MATERIAL_DIRS: tuple[MaterialKind, ...] = (MATERIALS_DIR,)
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
_QUESTION_MARKS_RE = re.compile(
    r"\b(?:aufgabe|problem|question|exercise)\s+\d{1,2}[\s\S]{0,240}?"
    r"\b(?:punkte|points?|marks?)\b",
    re.IGNORECASE,
)
_STRUCTURED_QUESTION_PART_RE = re.compile(r"(?:^|\s)[\-\u2013\u2014]?\s*(?:\([a-z]\)|[a-z]\))\s+")
_ACADEMIC_DATE_RE = re.compile(
    r"\b(?:ss|ws|sose|wise)\s*\d{2,4}\b|\b(?:summer|winter)\s+semester\b|\b\d{4}\b",
    re.IGNORECASE,
)
_TASK_DIRECTIVE_RE = re.compile(
    r"\b(?:"
    r"bestimmen|berechnen|beweisen|begründen|entscheiden|erklären|zeigen|"
    r"calculate|compute|determine|decide|explain|prove|show|derive"
    r")\b",
    re.IGNORECASE,
)
_ASSIGNMENT_STRUCTURE_RE = re.compile(
    r"\b(?:"
    r"assignment|due\s+date|exercise\s+sheet|homework|problem\s+set|worksheet|"
    r"abgabe|hausaufgabe|übungsblatt|uebungsblatt|übung\s*\d+|uebung\s*\d+"
    r")\b",
    re.IGNORECASE,
)
_EXERCISE_ITEM_RE = re.compile(
    r"\b(?:exercise|problem|aufgabe|übung|uebung)\s+\d{1,2}\b",
    re.IGNORECASE,
)
_LECTURE_STRUCTURE_RE = re.compile(
    r"\b(?:table of contents|inhaltsverzeichnis|willkommen|vorlesungstermine|"
    r"übungstermine|ubungstermine)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class MaterialFile:
    """A study material file discovered inside an armory."""

    path: Path
    rel_path: str
    kind: MaterialKind
    role: MaterialRole
    confidence: float
    reason: str


def material_kind(rel_path: str | Path) -> MaterialKind | None:
    """Return the material kind for a relative armory path."""
    first = Path(rel_path).parts[0] if Path(rel_path).parts else ""
    if first == MATERIALS_DIR:
        return "materials"
    return None


def infer_material_role(rel_path: str | Path) -> tuple[MaterialRole, float, str]:
    """Infer a study material role from its path.

    This keeps the filesystem simple for users while giving Hephaistos useful
    retrieval/study hints. The heuristic is intentionally transparent and cheap;
    model-assisted classification can refine it later.
    """
    path = Path(rel_path)
    normalized = "/".join(part.lower() for part in path.parts)
    suffix = path.suffix.lower()

    if any(
        token in normalized
        for token in (
            "exam",
            "past-paper",
            "past_paper",
            "mock",
            "klausur",
            "altklausur",
            "nachklausur",
            "pruefung",
            "prüfung",
        )
    ):
        return "past_exam", 0.9, "path suggests an exam or past paper"
    if any(token in normalized for token in ("assignment", "homework", "problem-set", "pset")):
        return "assignment", 0.85, "path suggests assigned problems"
    if any(token in normalized for token in ("vocab", "glossary", "flashcard")):
        return "vocabulary", 0.85, "path suggests vocabulary practice"
    if any(token in normalized for token in ("folie", "folien", "slides")):
        return "slides", 0.9, "path suggests lecture slides"
    if any(token in normalized for token in ("lecture", "seminar", "class-notes")):
        return "lecture", 0.8, "path suggests lecture material"
    if any(token in normalized for token in ("slide", "deck", "presentation")) or suffix in (
        ".ppt",
        ".pptx",
    ):
        return "slides", 0.8, "path or file type suggests slides"
    if any(token in normalized for token in ("book", "textbook", "chapter")):
        return "textbook", 0.8, "path suggests a textbook or chapter"
    if suffix in (".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".h"):
        return "codebase", 0.75, "file extension suggests source code"
    return "reference", 0.5, "default material role"


def infer_material_role_from_text(
    rel_path: str | Path,
    text: str,
) -> tuple[MaterialRole, float, str]:
    """Infer a material role using path hints plus extracted content.

    Filename hints remain the first signal because they are cheap and explicit.
    When the path is generic, indexed text lets the study harness distinguish
    exams from lecture decks without asking the user to classify files manually.
    """
    path_role, path_confidence, path_reason = infer_material_role(rel_path)
    if path_confidence >= 0.75:
        return path_role, path_confidence, path_reason

    normalized = text.lower()
    exam_hits = sum(
        token in normalized
        for token in (
            "klausur",
            "nachklausur",
            "prüfung",
            "pruefung",
            "aufgabe",
            "bearbeitungszeit",
            "hilfsmittel",
            "punkte",
        )
    )
    question_parts = len(_STRUCTURED_QUESTION_PART_RE.findall(text))
    task_directives = len(_TASK_DIRECTIVE_RE.findall(text))
    has_academic_date = bool(_ACADEMIC_DATE_RE.search(f"{rel_path} {text[:500]}"))
    if (
        exam_hits >= 3
        or _QUESTION_MARKS_RE.search(text)
        or (question_parts >= 2 and (has_academic_date or task_directives >= 2))
    ):
        return "past_exam", 0.82, "content contains exam questions or marks"

    assignment_hits = sum(
        token in normalized
        for token in (
            "assignment",
            "due date",
            "exercise sheet",
            "homework",
            "problem set",
            "worksheet",
            "abgabe",
            "hausaufgabe",
            "übungsblatt",
            "uebungsblatt",
        )
    )
    exercise_items = len(_EXERCISE_ITEM_RE.findall(text))
    if assignment_hits >= 1 or exercise_items >= 2 or _ASSIGNMENT_STRUCTURE_RE.search(text):
        return "assignment", 0.8, "content suggests exercises or assigned problems"

    lecture_hits = sum(
        token in normalized
        for token in (
            "vorlesung",
            "folie",
            "folien",
            "table of contents",
            "inhaltsverzeichnis",
            "übungsgruppe",
            "ubungsgruppe",
            "sommersemester",
            "wintersemester",
        )
    )
    if lecture_hits >= 3 or _LECTURE_STRUCTURE_RE.search(text):
        return "slides", 0.78, "content suggests lecture slides"

    return path_role, path_confidence, path_reason


def iter_materials(armory_path: Path) -> Iterator[MaterialFile]:
    """Yield visible material files using armory ignore rules."""
    ignore_spec = _load_ignore_spec(armory_path)
    for dirname in MATERIAL_DIRS:
        folder = armory_path / dirname
        if not folder.is_dir():
            continue
        resolved_folder = _resolve_material_folder(folder)
        if resolved_folder is None:
            continue
        for file_path in sorted(folder.rglob("*")):
            if _unsafe_material_path(file_path, resolved_folder):
                continue
            if not file_path.is_file():
                continue
            rel_to_material_dir = file_path.relative_to(folder)
            if any(part.startswith(".") for part in rel_to_material_dir.parts):
                continue
            rel = str(file_path.relative_to(armory_path))
            if _matches_ignore(ignore_spec, rel):
                continue
            role, confidence, reason = infer_material_role(rel)
            yield MaterialFile(
                path=file_path,
                rel_path=rel,
                kind=dirname,
                role=role,
                confidence=confidence,
                reason=reason,
            )


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
        return pathspec.PathSpec.from_lines(  # ty: ignore
            "gitignore", patterns
        )
    return tuple(pattern for pattern in patterns if pattern and not pattern.startswith("#"))


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


def _unsafe_material_path(file_path: Path, resolved_folder: Path) -> bool:
    if file_path.is_symlink():
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


def _matches_ignore(ignore_spec: object, rel_path: str) -> bool:
    """Return whether *rel_path* is ignored, with a stdlib fallback."""
    match_file = getattr(ignore_spec, "match_file", None)
    if callable(match_file):
        result = match_file(rel_path)
        return bool(result)
    if not isinstance(ignore_spec, tuple):
        return False
    patterns = cast("tuple[object, ...]", ignore_spec)  # ty:ignore[redundant-cast]
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
