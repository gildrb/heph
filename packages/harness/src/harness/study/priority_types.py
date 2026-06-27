"""Priority analysis data contracts and artifact types."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class PriorityChunk(Protocol):
    source: str
    index: int
    char_start: int
    char_end: int
    heading: str
    text: str


@dataclass(frozen=True, slots=True)
class PriorityTopicEvidence:
    source: str
    heading: str
    excerpt: str
    marks: int = 0


@dataclass(frozen=True, slots=True)
class PriorityWebSearchResult:
    title: str
    url: str
    snippet: str


@dataclass(frozen=True, slots=True)
class PriorityWebPrerequisite:
    term: str
    source_title: str
    source_url: str


PriorityWebSearcher = Callable[[str], Iterable[PriorityWebSearchResult]]
PriorityProgressReporter = Callable[[str], None]


@dataclass(frozen=True, slots=True)
class PriorityExamQuestion:
    source: str
    prompt: str
    marks: int
    topics: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PrioritySource:
    source_id: str
    path: str
    role: str


@dataclass(frozen=True, slots=True)
class PriorityTopic:
    topic: str
    score: float
    exam_hits: int
    exam_marks: int
    material_hits: int
    sources: tuple[str, ...]
    exam_source_frequency: int = 0
    supporting_material_coverage: int = 0
    confidence: float = 0.0
    prerequisites: tuple[str, ...] = ()
    web_prerequisites: tuple[PriorityWebPrerequisite, ...] = ()
    evidence: tuple[PriorityTopicEvidence, ...] = ()


@dataclass(frozen=True, slots=True)
class PriorityCheatSheetTopic:
    title: str
    tier: str
    source_ids: tuple[str, ...]
    prerequisites: tuple[str, ...]
    definitions: tuple[str, ...]
    formulas: tuple[str, ...]
    procedures: tuple[str, ...]
    exam_tasks: tuple[str, ...]
    pitfalls: tuple[str, ...]
    uncertainty: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PriorityCheatSheet:
    title: str
    generated_at: str
    focus: str
    sources: tuple[PrioritySource, ...]
    topics: tuple[PriorityCheatSheetTopic, ...]
    exam_questions: tuple[PriorityExamQuestion, ...]
    uncertainties: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PriorityVerificationReport:
    extraction_ok: bool
    priority_ok: bool
    source_support_ok: bool
    latex_ok: bool
    pdf_ok: bool
    anti_regression_ok: bool
    practice_ok: bool
    issues: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return all(
            (
                self.extraction_ok,
                self.priority_ok,
                self.source_support_ok,
                self.latex_ok,
                self.pdf_ok,
                self.anti_regression_ok,
                self.practice_ok,
            )
        )


@dataclass(frozen=True, slots=True)
class _PriorityVerificationChecks:
    extraction_ok: bool
    priority_ok: bool
    source_support_ok: bool
    latex_ok: bool
    pdf_ok: bool
    anti_regression_ok: bool
    practice_ok: bool


@dataclass(frozen=True, slots=True)
class PriorityReport:
    path: Path
    used_model: bool
    topic_count: int
    source_count: int
    tex_path: Path | None = None
    sidecar_path: Path | None = None
    verification: PriorityVerificationReport | None = None


@dataclass(frozen=True, slots=True)
class _PriorityReportArtifacts:
    sheet: PriorityCheatSheet
    tex_text: str
    model_payload: dict[str, object] | None


@dataclass(frozen=True, slots=True)
class _CheatSheetTopicSections:
    definitions: list[str]
    formulas: list[str]
    procedures: list[str]
    exam_tasks: list[str]
    pitfalls: list[str]


class PriorityPdfError(RuntimeError):
    pass


class PriorityPdfCompiler(Protocol):
    def compile(self, tex_path: Path, pdf_path: Path) -> None: ...
