"""Material index availability, operation events, and turn phase notices."""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from harness.chat.events import MaterialOperationEvent, ToolResultEvent, TurnEvent
from harness.chat.turn_contract import TurnContract
from harness.chat.turn_predicates import (
    _count_label,
    _material_label,
    _no_match_request_text,
    _overview_turn,
    _trace_excerpt,
    _visible_turn_evidence,
)
from harness.documents.prompt_plans import DocumentTurnPlan
from harness.documents.state import DocumentAction
from harness.rag.context import TurnEvidence

if TYPE_CHECKING:
    from harness.chat.evidence import ResolvedTurnPlan
    from harness.chat.session import ChatSession
    from harness.rag.index import ArmoryIndex

_EVIDENCE_REQUIRED_ACTIONS = frozenset({DocumentAction.SOURCE_QA, DocumentAction.PRESENT})
_MATERIAL_ANSWER_CONVERSATION_ACTIONS = _EVIDENCE_REQUIRED_ACTIONS


def _missing_indexed_material_reply(session: ChatSession, action: DocumentAction) -> str:
    if not _requires_indexed_material(session, action):
        return ""
    index = session.rag_index
    if index is None:
        return _index_unavailable_reply()
    return _indexed_material_state_reply(session, index)


def _requires_indexed_material(session: ChatSession, action: DocumentAction) -> bool:
    return action in _EVIDENCE_REQUIRED_ACTIONS and session.source_file_count > 0


def _indexed_material_state_reply(session: ChatSession, index: ArmoryIndex) -> str:
    if index.chunk_count > 0:
        if _has_enabled_indexed_material(session, index):
            return ""
        return _all_material_disabled_reply()
    if sources := _enabled_unindexable_sources(session, index):
        materials = _material_list_label(sources)
        reasons = [index.unindexable_files[source] for source in sources]
        return _unindexable_material_reply(materials, reasons)
    return _empty_material_index_reply()


def _has_enabled_indexed_material(session: ChatSession, index: ArmoryIndex) -> bool:
    return any(
        document.source not in session.disabled_source_files and document.chunks
        for document in index.documents
    )


def _enabled_unindexable_sources(session: ChatSession, index: ArmoryIndex) -> list[str]:
    return [
        source
        for source in sorted(index.unindexable_files)
        if source not in session.disabled_source_files
    ]


def _material_list_label(sources: list[str]) -> str:
    labels = [_material_label(source) for source in sources[:3]]
    materials = ", ".join(labels)
    if remaining := len(sources) - len(labels):
        return f"{materials}, and {remaining} more"
    return materials


def _index_unavailable_reply() -> str:
    return (
        "The armory has visible materials, but Heph could not prepare the "
        "searchable materials index for this turn. I cannot answer from outside "
        "knowledge. Check the material files or run `heph index <armory>` to see "
        "the indexing error directly."
    )


def _all_material_disabled_reply() -> str:
    return (
        "The armory has searchable materials, but all indexed material is currently "
        "disabled. Enable at least one material with /materials before asking."
    )


def _empty_material_index_reply() -> str:
    return (
        "The armory has visible materials, but no searchable evidence is indexed yet. "
        "I cannot answer from outside knowledge. Heph prepares the index "
        "automatically when possible; run `heph index <armory>` to inspect the failure."
    )


def _no_matching_indexed_evidence_reply(
    session: ChatSession,
    plan: DocumentTurnPlan,
    contract: TurnContract | None = None,
) -> str:
    index = session.rag_index
    if (
        not _requires_indexed_material(session, plan.action)
        or index is None
        or not plan.retrieval_query
        or not _has_enabled_indexed_material(session, index)
    ):
        return ""
    request_text = _no_match_request_text(contract)
    return (
        "The enabled materials are indexed, but this turn did not retrieve matching evidence "
        f"for the resolved request `{request_text}` using retrieval query "
        f"`{plan.retrieval_query}`."
    )


def _unindexable_material_reply(materials: str, reasons: list[str]) -> str:
    reason_text = [reason.lower() for reason in reasons]
    if _all_reasons_contain(reason_text, "conversion backend unavailable"):
        return (
            f"I can see {materials}, but PDF/document conversion is unavailable in this "
            "installation. I cannot answer from outside knowledge. Update or reinstall "
            "Heph, then ask again or run `heph index <armory>` to verify indexing."
        )
    if _all_reasons_contain(reason_text, "timed out"):
        return (
            f"I can see {materials}, but document conversion timed out before searchable "
            "text was indexed. I cannot answer from outside knowledge. Re-export or "
            "convert the material to text/Markdown, then ask again."
        )
    return (
        f"I can see {materials}, but no searchable text was indexed from it. "
        "I cannot answer from outside knowledge. Convert the material to text or "
        "Markdown, then ask again."
    )


def _all_reasons_contain(reasons: list[str], needle: str) -> bool:
    return bool(reasons) and all(needle in reason for reason in reasons)


def _material_operation_event(
    operation: str,
    message: str,
    **metadata: object,
) -> MaterialOperationEvent:
    return MaterialOperationEvent(
        operation=operation,
        message=message,
        metadata={key: value for key, value in metadata.items() if value not in ("", None)},
    )


def _tool_result_refreshes_current_armory(event: TurnEvent) -> bool:
    return (
        isinstance(event, ToolResultEvent)
        and event.name == "import_materials"
        and event.success
        and event.metadata.get("refresh_current_armory") is True
    )


def _material_operation_events(
    session: ChatSession,
    plan: DocumentTurnPlan,
    resolved: ResolvedTurnPlan,
) -> Iterator[MaterialOperationEvent]:
    if not (plan.retrieval_query or plan.use_expected_source_refs or resolved.turn_evidence):
        return

    evidence = _visible_turn_evidence(resolved)
    index_counts = _enabled_index_counts(session)
    yield from _index_ready_events(*index_counts)
    yield from _material_operation_start_events(session, plan, evidence, index_counts)
    yield from _material_evidence_events(plan, evidence, index_counts)


def _enabled_index_counts(session: ChatSession) -> tuple[int, int]:
    if session.rag_index is None:
        return 0, 0
    enabled_documents = [
        document
        for document in session.rag_index.documents
        if document.source not in session.disabled_source_files and document.chunks
    ]
    return len(enabled_documents), sum(len(document.chunks) for document in enabled_documents)


def _index_ready_events(
    indexed_sources: int,
    indexed_chunks: int,
) -> Iterator[MaterialOperationEvent]:
    if not (indexed_sources or indexed_chunks):
        return
    yield _material_operation_event(
        "index_ready",
        (
            "Material index ready: "
            f"{_count_label(indexed_sources, 'enabled source')}, "
            f"{_count_label(indexed_chunks, 'chunk')}."
        ),
        indexed_sources=indexed_sources,
        indexed_chunks=indexed_chunks,
    )


def _material_operation_start_events(
    session: ChatSession,
    plan: DocumentTurnPlan,
    evidence: TurnEvidence | None,
    index_counts: tuple[int, int],
) -> Iterator[MaterialOperationEvent]:
    indexed_sources, indexed_chunks = index_counts
    if _overview_turn(plan):
        yield _overview_sampling_event(plan, evidence, indexed_sources)
        return
    if plan.use_expected_source_refs and session.recall_state.expected_source_refs:
        yield _material_operation_event(
            "open_stored_evidence",
            (
                "Opening stored material evidence from the current recall item: "
                + ", ".join(session.recall_state.expected_source_refs[:3])
            ),
            refs=list(session.recall_state.expected_source_refs),
        )
        return
    if plan.retrieval_query:
        yield _material_operation_event(
            "search_index",
            f"Searching indexed materials for: {plan.retrieval_query}",
            query=plan.retrieval_query,
            indexed_sources=indexed_sources,
            indexed_chunks=indexed_chunks,
        )


def _overview_sampling_event(
    plan: DocumentTurnPlan,
    evidence: TurnEvidence | None,
    indexed_sources: int,
) -> MaterialOperationEvent:
    sampled_sources = evidence.sampled_source_count if evidence else 0
    total_sources = evidence.total_source_count if evidence else indexed_sources
    evidence_blocks = len(evidence.items) if evidence else 0
    return _material_operation_event(
        "sample_overview",
        (
            f"Sampling corpus overview: {_count_label(evidence_blocks, 'excerpt')} "
            f"from {sampled_sources} of {_count_label(total_sources, 'indexed source')}."
        ),
        query=plan.retrieval_query,
        evidence_blocks=evidence_blocks,
        sampled_sources=sampled_sources,
        total_sources=total_sources,
    )


def _material_evidence_events(
    plan: DocumentTurnPlan,
    evidence: TurnEvidence | None,
    index_counts: tuple[int, int],
) -> Iterator[MaterialOperationEvent]:
    indexed_sources, indexed_chunks = index_counts
    if evidence is not None and evidence.items:
        for item in evidence.items[:3]:
            yield _material_operation_event(
                "read_excerpt",
                (
                    f"Opened {item.source}#chunk={item.chunk_index}: "
                    f"{_trace_excerpt(item.content, limit=180)}"
                ),
                evidence_id=item.evidence_id,
                ref=f"{item.source}#chunk={item.chunk_index}",
                source=item.source,
                chunk=item.chunk_index,
                score=round(item.score, 4),
                text_excerpt=_trace_excerpt(item.content, limit=240),
            )
        return
    if plan.retrieval_query:
        yield _material_operation_event(
            "search_result",
            "Material search returned no matching indexed evidence.",
            query=plan.retrieval_query,
            indexed_sources=indexed_sources,
            indexed_chunks=indexed_chunks,
        )


def _reading_notice(plan: DocumentTurnPlan) -> str:
    if _overview_turn(plan):
        return "Preparing the material index and reading enabled evidence for a corpus overview."
    if plan.retrieval_query or plan.use_expected_source_refs:
        return "Preparing the material index and reading relevant evidence."
    return ""


def _writing_notice(plan: DocumentTurnPlan) -> str:
    if _overview_turn(plan):
        return "Writing a grounded corpus overview."
    if plan.action is DocumentAction.CHAT and not (
        plan.retrieval_query or plan.use_expected_source_refs
    ):
        return "Writing a response."
    return "Writing a grounded response."


def _should_use_material_answer_conversation_window(
    plan: DocumentTurnPlan,
    _contract: TurnContract | None,
) -> bool:
    return (
        plan.action in _MATERIAL_ANSWER_CONVERSATION_ACTIONS
    )
