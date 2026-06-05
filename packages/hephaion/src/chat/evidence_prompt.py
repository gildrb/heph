"""Evidence assessment prompt formatting for chat turns."""

from __future__ import annotations

from study.policy import EvidenceAssessment
from study.state import LearningAction

from chat.evidence import ResolvedTurnPlan


def _append_evidence_assessment_prompt(
    prompt: str,
    resolved: ResolvedTurnPlan,
) -> str:
    if not _needs_evidence_assessment_prompt(prompt, resolved):
        return prompt
    assessment = resolved.evidence_assessment
    if assessment is None:
        return prompt
    return f"{prompt}\n\n{_evidence_assessment_prompt_line(assessment)}"


def _needs_evidence_assessment_prompt(prompt: str, resolved: ResolvedTurnPlan) -> bool:
    plan = resolved.learning_plan
    assessment = resolved.evidence_assessment
    if not prompt or plan is None or assessment is None:
        return False
    return plan.action not in {LearningAction.CHAT, LearningAction.CALIBRATE} and not (
        assessment.sufficient
    )


def _evidence_assessment_prompt_line(assessment: EvidenceAssessment) -> str:
    missing = ", ".join(assessment.missing_information) or "missing supporting evidence"
    refs = ", ".join(assessment.supporting_refs) or "none"
    action = assessment.recommended_action.replace("_", " ")
    return (
        "Evidence gate: "
        f"partial/insufficient ({assessment.confidence:.0%}); action={action}; "
        f"refs={refs}; missing={missing}. "
        "Do not fill gaps; scope any answer to cited evidence. If action=abstain, say the "
        "direct cited answer is missing for the resolved request; do not claim whole-corpus "
        "absence unless the current turn exhaustively checked the corpus."
    )
