"""SDK value objects for armory materials and indexes."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True, slots=True)
class MaterialSummary:
    path: Path
    rel_path: str
    kind: Literal["materials"]
    role: str
    confidence: float
    reason: str

    @property
    def display_name(self) -> str:
        return self.rel_path.removeprefix("materials/")

    def to_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "rel_path": self.rel_path,
            "display_name": self.display_name,
            "kind": self.kind,
            "role": self.role,
            "confidence": self.confidence,
            "reason": self.reason,
        }


@dataclass(frozen=True, slots=True)
class ImportMaterialsSummary:
    imported: tuple[str, ...]
    considered: int
    skipped_duplicates: int
    skipped_unsupported: int

    @property
    def skipped(self) -> int:
        return self.skipped_duplicates + self.skipped_unsupported

    def to_dict(self) -> dict[str, object]:
        return {
            "imported": list(self.imported),
            "considered": self.considered,
            "skipped": self.skipped,
            "skipped_duplicates": self.skipped_duplicates,
            "skipped_unsupported": self.skipped_unsupported,
        }


@dataclass(frozen=True, slots=True)
class IndexProgressEvent:
    action: str
    detail: str

    def to_dict(self) -> dict[str, object]:
        return {"action": self.action, "detail": self.detail}


@dataclass(frozen=True, slots=True)
class IndexSummary:
    documents: int
    chunks: int
    progress: tuple[IndexProgressEvent, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "documents": self.documents,
            "chunks": self.chunks,
            "progress": [event.to_dict() for event in self.progress],
        }


@dataclass(frozen=True, slots=True)
class ExtractionHealthIssueSummary:
    source: str
    forbidden_text_present: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "forbidden_text_present": list(self.forbidden_text_present),
        }


@dataclass(frozen=True, slots=True)
class ExtractionHealthSummary:
    armory_path: Path
    documents: int
    checks: int
    pass_rate: float
    forbidden_text: tuple[str, ...]
    issues: tuple[ExtractionHealthIssueSummary, ...]

    @property
    def passed(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, object]:
        return {
            "armory_path": str(self.armory_path),
            "documents": self.documents,
            "checks": self.checks,
            "pass_rate": self.pass_rate,
            "passed": self.passed,
            "forbidden_text": list(self.forbidden_text),
            "issues": [issue.to_dict() for issue in self.issues],
        }


__all__ = [
    "ExtractionHealthIssueSummary",
    "ExtractionHealthSummary",
    "ImportMaterialsSummary",
    "IndexProgressEvent",
    "IndexSummary",
    "MaterialSummary",
]
