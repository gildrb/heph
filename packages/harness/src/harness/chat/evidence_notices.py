"""User-visible evidence notices and trace metadata for chat turns."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from harness.chat.document_signals import _trace_task
from harness.chat.evidence import (
    ResolvedTurnPlan,
)
from harness.chat.evidence import (
    evidence_assessment_trace as _evidence_assessment_trace,
)
from harness.chat.evidence import (
    evidence_refs as _evidence_refs,
)
from harness.chat.evidence import (
    evidence_trace_coverage as _evidence_trace_coverage,
)
from harness.chat.evidence import (
    evidence_trace_items as _evidence_trace_items,
)
from harness.chat.evidence import (
    retrieval_audit_metadata as _retrieval_audit_metadata,
)
from harness.chat.turn_predicates import (
    _material_label,
    _overview_turn,
    _plural,
    _readable_material_label,
    _trace_excerpt,
    _visible_turn_evidence,
)
from harness.rag.context import TurnEvidence

if TYPE_CHECKING:
    from harness.chat.session import ChatSession


def _evidence_bullet_lines(evidence: TurnEvidence, *, limit: int = 8) -> tuple[str, ...]:
    return tuple(
        f"- {_readable_material_label(item.source)}: "
        f"{_trace_excerpt(item.content, limit=700)} [{item.evidence_id}]"
        for item in evidence.items[:limit]
    )


def _evidence_notice(resolved: ResolvedTurnPlan) -> str:
    visible_evidence = _visible_turn_evidence(resolved)
    if visible_evidence is None or not visible_evidence.items:
        return ""
    plan = resolved.document_plan
    if plan is not None and _overview_turn(plan):
        notice = _overview_evidence_notice(visible_evidence)
    else:
        notice = _retrieved_evidence_notice(visible_evidence)
    return _append_evidence_assessment_notice(notice, resolved)


def _overview_evidence_notice(evidence: TurnEvidence) -> str:
    sources = list(dict.fromkeys(item.source for item in evidence.items))
    sampled_sources = evidence.sampled_source_count or len(sources)
    total_sources = evidence.total_source_count or sampled_sources
    return (
        f"Using {len(evidence.items)} overview evidence {_plural('excerpt', len(evidence.items))} "
        f"from {sampled_sources} of {total_sources} indexed "
        f"{_plural('source', total_sources)}: {_summarized_material_labels(sources)}"
    )


def _retrieved_evidence_notice(evidence: TurnEvidence) -> str:
    refs = _evidence_refs(evidence)
    return (
        f"Using {len(refs)} retrieved evidence {_plural('excerpt', len(refs))}: "
        f"{_summarized_refs(refs)}"
    )


def _summarized_material_labels(sources: Sequence[str], *, limit: int = 4) -> str:
    labels = ", ".join(_material_label(source) for source in sources[:limit])
    remaining = len(sources) - limit
    suffix = f", and {remaining} more" if remaining > 0 else ""
    return f"{labels}{suffix}"


def _summarized_refs(refs: Sequence[str], *, limit: int = 3) -> str:
    shown = ", ".join(refs[:limit])
    remaining = len(refs) - limit
    suffix = f", and {remaining} more" if remaining > 0 else ""
    return f"{shown}{suffix}"


def _append_evidence_assessment_notice(notice: str, resolved: ResolvedTurnPlan) -> str:
    assessment = resolved.evidence_assessment
    if assessment is None or assessment.sufficient:
        return notice
    action = assessment.recommended_action.replace("_", " ")
    return f"{notice}. Evidence sufficiency: {action} ({assessment.confidence:.0%})."


def _evidence_notice_metadata(
    resolved: ResolvedTurnPlan,
    session: ChatSession | None = None,
) -> dict[str, object]:
    visible_evidence = _visible_turn_evidence(resolved)
    if visible_evidence is None or not visible_evidence.items:
        return {}
    plan = resolved.document_plan
    task = _trace_task(plan)
    metadata: dict[str, object] = {
        "task": task,
        "refs": _evidence_refs(visible_evidence),
        "coverage": _evidence_trace_coverage(visible_evidence),
        "items": _evidence_trace_items(visible_evidence),
        "assessment": _evidence_assessment_trace(resolved.evidence_assessment),
    }
    if session is not None and plan is not None:
        metadata.update(_retrieval_audit_metadata(session, plan, resolved))
    return metadata
