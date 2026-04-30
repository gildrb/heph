"""RAG evidence resolution for chat turns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from hephaistos.chat.usage import ContextBudget
from hephaistos.logging import Timer, get_logger
from hephaistos.rag import (
    ArmoryIndex,
    ScoredChunk,
    TransformStrategy,
    TurnEvidence,
    build_turn_evidence,
    load_or_build,
    retrieve,
)
from hephaistos.rag.query_transform import PromptFn
from hephaistos.rag.retrieval_types import EvidenceReference
from hephaistos.runtime import (
    ChatConfig,
    Conversation,
    build_client,
    to_chat_completion_messages,
)
from hephaistos.study import StudyTurnPlan

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession

_log = get_logger("chat.evidence")
_RAG_MIN_SCORE = 0.1


@dataclass(frozen=True, slots=True)
class ResolvedTurnPlan:
    """A controller plan plus any retrieved turn evidence."""

    study_plan: StudyTurnPlan | None = None
    turn_evidence: TurnEvidence | None = None


def evidence_refs(turn_evidence: TurnEvidence | None) -> list[str]:
    """Return stable source/chunk references for turn evidence."""
    if not turn_evidence:
        return []
    return [
        EvidenceReference(item.source, item.chunk_index).render() for item in turn_evidence.items
    ]


def parse_source_ref(ref: str) -> tuple[str, int] | None:
    """Parse ``path#chunk=N`` evidence references."""
    parsed = EvidenceReference.parse(ref)
    if parsed is None:
        return None
    return parsed.source, parsed.chunk_index


_FLAG_STRATEGY_MAP: dict[str, TransformStrategy] = {
    "rag_expansion": TransformStrategy.EXPANSION,
    "rag_hyde": TransformStrategy.HYDE,
    "rag_multi_query": TransformStrategy.MULTI_QUERY,
}


def resolve_transform_strategy(config: ChatConfig) -> TransformStrategy:
    """Resolve RAG query-transform strategy from feature flags."""
    for flag, strategy in _FLAG_STRATEGY_MAP.items():
        if config.is_feature_enabled(flag):
            return strategy
    return TransformStrategy.EXPANSION


def build_prompt_fn(config: ChatConfig) -> PromptFn:
    """Build a prompt function for LLM-based query transforms."""

    def _prompt(prompt_text: str) -> str:
        conv = Conversation()
        conv.add("user", prompt_text)
        client = build_client(config)
        messages = to_chat_completion_messages(conv.to_api_messages())
        resp = client.chat.completions.create(
            model=config.model,
            messages=messages,
            max_tokens=500,
            stream=False,
        )
        content = resp.choices[0].message.content
        return content if isinstance(content, str) else ""

    return _prompt


def ensure_rag_index(session: ChatSession) -> ArmoryIndex | None:
    """Load and cache the armory RAG index on the session."""
    if session.armory_path is None:
        return None
    if session.rag_index is None:
        session.rag_index = load_or_build(session.armory_path)
    return session.rag_index


def adaptive_rag_budget(session: ChatSession) -> int:
    """Allocate a bounded retrieval context budget for the current session."""
    budget = ContextBudget(model=session.config.model, max_tokens=session.config.max_tokens)
    api_msgs = session.conversation.to_api_messages()
    remaining = budget.tokens_remaining(api_msgs)  # type: ignore[arg-type]
    return min(session.config.rag_context_budget, max(200, int(remaining * 0.3)))


def build_turn_evidence_from_query(session: ChatSession, query: str) -> TurnEvidence | None:
    """Retrieve and build evidence for a free-text query."""
    if session.armory_path is None:
        return None
    try:
        timer = Timer()
        index = ensure_rag_index(session)
        if index is None:
            return None

        strategy = resolve_transform_strategy(session.config)
        prompt_fn: PromptFn | None = None
        if strategy in (TransformStrategy.HYDE, TransformStrategy.MULTI_QUERY):
            prompt_fn = build_prompt_fn(session.config)

        with timer:
            scored = retrieve(
                query,
                index,
                top_k=5,
                min_score=_RAG_MIN_SCORE,
                transform_strategy=strategy,
                prompt_fn=prompt_fn,
            )
        if not scored:
            _log.info(
                "rag retrieve: no relevant results",
                extra={
                    "fields": {
                        "query_len": len(query),
                        "latency_ms": timer.ms,
                        "min_score": _RAG_MIN_SCORE,
                    }
                },
            )
            return None

        scores = [sc.score for sc in scored]
        _log.info(
            "rag retrieve",
            extra={
                "fields": {
                    "query_len": len(query),
                    "retrieved": len(scored),
                    "top_score": round(scores[0], 4) if scores else 0,
                    "latency_ms": round(timer.ms, 1),
                }
            },
        )
        session.trace.record_rag_retrieve(
            query=query,
            top_k=5,
            retrieved=len(scored),
            scores=scores,
            latency_ms=timer.ms,
        )
        return build_turn_evidence(scored, max_tokens=adaptive_rag_budget(session))
    except Exception:
        _log.warning("turn evidence build failed", exc_info=True)
        return None


def build_turn_evidence_from_refs(session: ChatSession, refs: list[str]) -> TurnEvidence | None:
    """Rebuild evidence from persisted source/chunk references."""
    try:
        index = ensure_rag_index(session)
        if index is None or not refs:
            return None

        by_key = {(chunk.source, chunk.index): chunk for chunk in index.all_chunks}
        scored: list[ScoredChunk] = []
        total = len(refs)
        for pos, ref in enumerate(refs):
            parsed = parse_source_ref(ref)
            if parsed is None:
                continue
            chunk = by_key.get(parsed)
            if chunk is None:
                continue
            scored.append(ScoredChunk(chunk=chunk, score=float(total - pos)))
        if not scored:
            return None
        return build_turn_evidence(scored, max_tokens=adaptive_rag_budget(session))
    except Exception:
        _log.warning("turn evidence rebuild from refs failed", exc_info=True)
        return None


def resolve_turn_evidence(session: ChatSession, plan: StudyTurnPlan) -> TurnEvidence | None:
    """Resolve the best evidence for a study turn plan."""
    if plan.use_expected_source_refs and session.study_state.expected_source_refs:
        turn_evidence = build_turn_evidence_from_refs(
            session,
            session.study_state.expected_source_refs,
        )
        if turn_evidence:
            return turn_evidence
    if plan.retrieval_query:
        return build_turn_evidence_from_query(session, plan.retrieval_query)
    return None


__all__ = [
    "ResolvedTurnPlan",
    "adaptive_rag_budget",
    "build_prompt_fn",
    "build_turn_evidence_from_query",
    "build_turn_evidence_from_refs",
    "ensure_rag_index",
    "evidence_refs",
    "parse_source_ref",
    "resolve_transform_strategy",
    "resolve_turn_evidence",
]
