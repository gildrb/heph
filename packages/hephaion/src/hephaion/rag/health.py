"""Generic health checks for indexed material text."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hephaion.rag.index import load_or_build

DEFAULT_EXTRACTION_FORBIDDEN_TEXT: tuple[str, ...] = (
    "formula-not-decoded",
    "Formula-not-decoded",
    "image-not-decoded",
    "Image-not-decoded",
    "table-not-decoded",
    "Table-not-decoded",
    "picture-not-decoded",
    "Picture-not-decoded",
    "figure-not-decoded",
    "Figure-not-decoded",
    "Formula not decoded",
    "Image not decoded",
    "Table not decoded",
    "Picture not decoded",
    "Figure not decoded",
    "<!-- image -->",
    "<!-- table -->",
    "<!-- formula -->",
)


@dataclass(frozen=True, slots=True)
class ExtractionHealthIssue:
    source: str
    forbidden_text_present: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ExtractionHealthReport:
    armory_path: str
    documents: int
    checks: int
    pass_rate: float
    forbidden_text: tuple[str, ...]
    issues: tuple[ExtractionHealthIssue, ...]

    @property
    def passed(self) -> bool:
        return not self.issues


def scan_extraction_health(
    armory_path: Path,
    *,
    forbidden_text: tuple[str, ...] = DEFAULT_EXTRACTION_FORBIDDEN_TEXT,
) -> ExtractionHealthReport:
    """Scan every indexed document for generic extraction poison."""
    index = load_or_build(armory_path)
    forbidden = tuple(item for item in forbidden_text if item.strip())
    issues: list[ExtractionHealthIssue] = []
    for document in sorted(index.documents, key=lambda item: item.source):
        text = " ".join(chunk.text for chunk in document.chunks)
        present = tuple(item for item in forbidden if item in text)
        if present:
            issues.append(
                ExtractionHealthIssue(
                    source=document.source,
                    forbidden_text_present=present,
                )
            )
    checks = len(index.documents) * len(forbidden)
    failure_count = sum(len(issue.forbidden_text_present) for issue in issues)
    return ExtractionHealthReport(
        armory_path=str(armory_path),
        documents=len(index.documents),
        checks=checks,
        pass_rate=(checks - failure_count) / checks if checks else 1.0,
        forbidden_text=forbidden,
        issues=tuple(issues),
    )
