"""Evidence sufficiency types for grounded document answers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

EvidenceAction = Literal[
    "answer",
    "retrieve_more",
    "ask_clarifying_question",
    "abstain",
    "give_partial_answer",
]


@dataclass(frozen=True, slots=True)
class EvidenceAssessment:
    sufficient: bool
    confidence: float
    supporting_refs: tuple[str, ...]
    missing_information: tuple[str, ...]
    conflicts: tuple[str, ...]
    source_diversity_score: float
    recommended_action: EvidenceAction


def assess_evidence(
    refs: tuple[str, ...],
    *,
    source_only: bool = False,
    missing_hint: str = "more targeted indexed source evidence",
) -> EvidenceAssessment:
    if not refs:
        return EvidenceAssessment(
            sufficient=False,
            confidence=0.0,
            supporting_refs=(),
            missing_information=(missing_hint,),
            conflicts=(),
            source_diversity_score=0.0,
            recommended_action="abstain" if source_only else "retrieve_more",
        )
    diversity = _source_diversity_score(refs)
    if len(refs) == 1:
        return EvidenceAssessment(
            sufficient=not source_only,
            confidence=0.48 if source_only else 0.58,
            supporting_refs=refs,
            missing_information=("corroborating source span",),
            conflicts=(),
            source_diversity_score=diversity,
            recommended_action="give_partial_answer" if source_only else "answer",
        )
    return EvidenceAssessment(
        sufficient=True,
        confidence=min(0.95, 0.62 + 0.1 * len(refs) + 0.1 * diversity),
        supporting_refs=refs,
        missing_information=(),
        conflicts=(),
        source_diversity_score=diversity,
        recommended_action="answer",
    )


def _source_diversity_score(refs: tuple[str, ...]) -> float:
    sources = {ref.split("#chunk=", maxsplit=1)[0] for ref in refs}
    return min(1.0, len(sources) / 3) if refs else 0.0
