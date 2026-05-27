"""Material discovery and role inference for armories."""

from __future__ import annotations

import fnmatch
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast

from hephaion.logging import get_logger

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
type MaterialRoleInference = tuple[MaterialRole, float, str]

MATERIALS_DIR = "materials"
MATERIAL_DIRS: tuple[MaterialKind, ...] = (MATERIALS_DIR,)
IGNORE_FILE = ".hephaionignore"
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
    r"\b(?:table of contents|inhaltsverzeichnis|willkommen)\b",
    re.IGNORECASE,
)
_PUBLIC_TEXTBOOK_RE = re.compile(
    r"(?:/~[^\"'\s<>]+/textbook/|/textbook/|online textbook|textbook section)",
    re.IGNORECASE,
)
_PUBLIC_COURSE_NOTES_RE = re.compile(
    r"(?:course materials and notes|introductory lecture|lecture video|youtube-wrapper|"
    r"course overview\s*\+|nav-link[^>]*>\s*lectures\s*<)",
    re.IGNORECASE,
)
_NUMBERED_TEXTBOOK_SECTION_RE = re.compile(
    r"\b\d{1,2}\.\d{1,2}\s+[A-Z][^|\n]{2,80}\s+\|\s+[A-Z]",
    re.IGNORECASE,
)
_PATH_ROLE_RULES: tuple[tuple[tuple[str, ...], MaterialRoleInference], ...] = (
    (
        (
            "exam",
            "past-paper",
            "past_paper",
            "mock",
            "klausur",
            "altklausur",
            "nachklausur",
            "pruefung",
            "prüfung",
        ),
        ("past_exam", 0.9, "path suggests an exam or past paper"),
    ),
    (
        ("assignment", "homework", "problem-set", "pset"),
        ("assignment", 0.85, "path suggests assigned problems"),
    ),
    (
        ("vocab", "glossary", "flashcard"),
        ("vocabulary", 0.85, "path suggests vocabulary practice"),
    ),
    (("folie", "folien", "slides"), ("slides", 0.9, "path suggests lecture slides")),
    (("lecture", "seminar", "class-notes"), ("lecture", 0.8, "path suggests lecture material")),
    (("slide", "deck", "presentation"), ("slides", 0.8, "path or file type suggests slides")),
    (("book", "textbook", "chapter"), ("textbook", 0.8, "path suggests a textbook or chapter")),
)
_CODE_SUFFIXES = frozenset((".py", ".js", ".ts", ".java", ".go", ".rs", ".cpp", ".c", ".h"))
_SLIDE_SUFFIXES = frozenset((".ppt", ".pptx"))
_EXAM_TEXT_TOKENS = (
    "klausur",
    "nachklausur",
    "prüfung",
    "pruefung",
    "aufgabe",
    "bearbeitungszeit",
    "punkte",
)
_ASSIGNMENT_TEXT_TOKENS = (
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
_LECTURE_TEXT_TOKENS = (
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


def _path_has(normalized: str, tokens: tuple[str, ...]) -> bool:
    return any(token in normalized for token in tokens)


def _token_hits(text: str, tokens: tuple[str, ...]) -> int:
    return sum(token in text for token in tokens)


def _path_rule_match(normalized: str) -> MaterialRoleInference | None:
    for tokens, inference in _PATH_ROLE_RULES:
        if _path_has(normalized, tokens):
            return inference
    return None


def infer_material_role(rel_path: str | Path) -> MaterialRoleInference:
    """Infer a material role from its path.

    This keeps the filesystem simple for users while giving Heph useful
    retrieval and learning hints. The heuristic is intentionally transparent and cheap;
    model-assisted classification can refine it later.
    """
    path = Path(rel_path)
    normalized = _normalized_path(path)

    if path.stem.lower() in {"summary", "reference"}:
        return "reference", 0.76, "path suggests a summary or reference page"
    if (inference := _path_rule_match(normalized)) is not None:
        return inference
    if path.suffix.lower() in _SLIDE_SUFFIXES:
        return "slides", 0.8, "path or file type suggests slides"
    if path.suffix.lower() in _CODE_SUFFIXES:
        return "codebase", 0.75, "file extension suggests source code"
    return "reference", 0.5, "default material role"


def _normalized_path(path: Path) -> str:
    return "/".join(part.lower() for part in path.parts)


def _public_material_role(role_hint_text: str) -> MaterialRoleInference | None:
    if _PUBLIC_TEXTBOOK_RE.search(role_hint_text):
        return "textbook", 0.84, "content suggests a public textbook section"
    if _NUMBERED_TEXTBOOK_SECTION_RE.search(role_hint_text):
        return "textbook", 0.8, "content suggests a numbered textbook section"
    if _PUBLIC_COURSE_NOTES_RE.search(role_hint_text):
        return "lecture", 0.82, "content suggests public course notes or lectures"
    return None


def _exam_material_role(
    rel_path: str | Path,
    text: str,
    normalized: str,
) -> MaterialRoleInference | None:
    question_parts = len(_STRUCTURED_QUESTION_PART_RE.findall(text))
    task_directives = len(_TASK_DIRECTIVE_RE.findall(text))
    has_academic_date = bool(_ACADEMIC_DATE_RE.search(f"{rel_path} {text[:500]}"))
    if _has_exam_signals(normalized, text, question_parts, task_directives, has_academic_date):
        return "past_exam", 0.82, "content contains exam questions or marks"
    return None


def _has_exam_signals(
    normalized: str,
    text: str,
    question_parts: int,
    task_directives: int,
    has_academic_date: bool,
) -> bool:
    return (
        _token_hits(normalized, _EXAM_TEXT_TOKENS) >= 3
        or bool(_QUESTION_MARKS_RE.search(text))
        or (question_parts >= 2 and (has_academic_date or task_directives >= 2))
    )


def _assignment_material_role(text: str, normalized: str) -> MaterialRoleInference | None:
    exercise_items = len(_EXERCISE_ITEM_RE.findall(text))
    if (
        _token_hits(normalized, _ASSIGNMENT_TEXT_TOKENS) >= 1
        or exercise_items >= 2
        or _ASSIGNMENT_STRUCTURE_RE.search(text)
    ):
        return "assignment", 0.8, "content suggests exercises or assigned problems"
    return None


def _lecture_material_role(text: str, normalized: str) -> MaterialRoleInference | None:
    if _token_hits(normalized, _LECTURE_TEXT_TOKENS) >= 3 or _LECTURE_STRUCTURE_RE.search(text):
        return "slides", 0.78, "content suggests lecture slides"
    return None


def infer_material_role_from_text(
    rel_path: str | Path,
    text: str,
) -> MaterialRoleInference:
    """Infer a material role using path hints plus extracted content.

    Filename hints remain the first signal because they are cheap and explicit.
    When the path is generic, indexed text lets the study harness distinguish
    exams from lecture decks without asking the user to classify files manually.
    """
    path_role, path_confidence, path_reason = infer_material_role(rel_path)
    if path_confidence >= 0.75:
        return path_role, path_confidence, path_reason

    role_hint_text = f"{rel_path}\n{text[:8000]}"
    if (public_role := _public_material_role(role_hint_text)) is not None:
        return public_role

    normalized = text.lower()
    for classifier in (
        lambda: _exam_material_role(rel_path, text, normalized),
        lambda: _assignment_material_role(text, normalized),
        lambda: _lecture_material_role(text, normalized),
    ):
        if (inference := classifier()) is not None:
            return inference

    return path_role, path_confidence, path_reason


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
