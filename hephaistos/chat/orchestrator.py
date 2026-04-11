"""Single-turn orchestration for chat sessions."""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from hephaistos.chat.engine import (
    RetryConfig,
    StreamRecoveryError,
    _build_client,
    stream_completion,
)
from hephaistos.chat.events import AssistantDeltaEvent, NoticeEvent, TurnEvent
from hephaistos.chat.usage import ContextBudget, save_usage
from hephaistos.harness.citation import verify_response
from hephaistos.harness.dispatch import SteeringQueue, iter_agent_events
from hephaistos.harness.rag import (
    ArmoryIndex,
    ScoredChunk,
    TurnEvidence,
    build_turn_evidence,
    load_or_build,
    retrieve,
)
from hephaistos.logging import Timer, get_logger
from hephaistos.study import StudyTurnPlan, apply_turn_result, plan_turn

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession

_log = get_logger("chat.orchestrator")
_RAG_MIN_SCORE = 0.1


@dataclass(frozen=True, slots=True)
class ResolvedTurnPlan:
    """A controller plan plus any retrieved turn evidence."""

    study_plan: StudyTurnPlan | None = None
    turn_evidence: TurnEvidence | None = None


@dataclass(slots=True)
class TurnOrchestrator:
    """Own one user turn end-to-end."""

    session: ChatSession
    retry: RetryConfig | None = None
    last_reply: str = field(default="", init=False)

    def iter_events(
        self,
        user_input: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]:
        session = self.session
        original_messages = list(session.conversation.messages)
        original_study_state = session.study_state.clone()
        timer = Timer()
        self.last_reply = ""

        session.conversation.add("user", user_input)
        session.trace.record_user_message(user_input)
        _log.info(
            "user message",
            extra={
                "fields": {
                    "session_id": session.session_id,
                    "input_len": len(user_input),
                    "message_count": len(session.conversation.messages),
                    "study_phase": session.study_state.phase.value,
                }
            },
        )

        resolved = ResolvedTurnPlan()
        try:
            with timer:
                if session.armory_path is not None:
                    resolved = self._resolve_turn_plan(user_input)
                    for event in self._iter_study_events(
                        resolved,
                        original_study_state,
                        abort=abort,
                    ):
                        yield event
                else:
                    for event in self._iter_plain_events(abort=abort):
                        yield event

            notice = self._finalize_successful_turn(user_input, resolved, latency_ms=timer.ms)
            if notice:
                yield NoticeEvent(notice, code="verification")
        except StreamRecoveryError as rec:
            _log.warning(
                "stream interrupted, rolling back",
                extra={
                    "fields": {
                        "session_id": session.session_id,
                        "partial_len": len(rec.partial_content),
                        "latency_ms": timer.ms,
                    }
                },
            )
            session.conversation.messages = original_messages
            session.study_state = original_study_state
            session.dirty = True
            raise
        except Exception:
            _log.error(
                "turn orchestration failed",
                extra={
                    "fields": {
                        "session_id": session.session_id,
                        "latency_ms": timer.ms,
                    }
                },
                exc_info=True,
            )
            session.conversation.messages = original_messages
            session.study_state = original_study_state
            raise

    def _iter_plain_events(self, *, abort: threading.Event | None) -> Iterator[TurnEvent]:
        session = self.session
        for delta in stream_completion(
            session.config,
            session.conversation,
            abort=abort,
            retry=self.retry,
            client_factory=_build_client,
        ):
            if not delta.content:
                continue
            self.last_reply += delta.content
            yield AssistantDeltaEvent(delta.content)

        if self.last_reply and (
            not session.conversation.messages
            or session.conversation.messages[-1].role != "assistant"
        ):
            session.conversation.add("assistant", self.last_reply)

    def _iter_study_events(
        self,
        resolved: ResolvedTurnPlan,
        original_study_state,
        *,
        abort: threading.Event | None,
    ) -> Iterator[TurnEvent]:
        session = self.session
        assert session.armory_path is not None
        plan = resolved.study_plan
        assert plan is not None

        raw_reply = ""
        for event in iter_agent_events(
            session.config,
            session.conversation,
            session.armory_path,
            abort=abort,
            retry=self.retry,
            usage=session.usage,
            steering=session.steering if isinstance(session.steering, SteeringQueue) else None,
            turn_evidence=resolved.turn_evidence,
            extra_system_prompt=plan.prompt,
            tool_schemas=None if plan.allow_tools else [],
            registry=session._tool_registry,
        ):
            if isinstance(event, AssistantDeltaEvent):
                raw_reply += event.delta
                if not plan.buffer_response:
                    self.last_reply += event.delta
            yield event

        if raw_reply:
            session.study_state, final_reply = apply_turn_result(
                original_study_state,
                plan,
                raw_reply,
                _evidence_refs(resolved.turn_evidence),
            )
        else:
            session.study_state = original_study_state
            final_reply = raw_reply

        if final_reply and (
            not session.conversation.messages
            or session.conversation.messages[-1].role != "assistant"
        ):
            session.conversation.add("assistant", final_reply)
        elif final_reply and raw_reply != final_reply:
            self._replace_last_assistant_message(final_reply)

        self.last_reply = final_reply
        if plan.buffer_response and final_reply:
            yield AssistantDeltaEvent(final_reply)

    def _resolve_turn_plan(self, user_input: str) -> ResolvedTurnPlan:
        plan = plan_turn(self.session.study_state, user_input)
        return ResolvedTurnPlan(
            study_plan=plan,
            turn_evidence=_resolve_turn_evidence(self.session, plan),
        )

    def _finalize_successful_turn(
        self,
        user_input: str,
        resolved: ResolvedTurnPlan,
        *,
        latency_ms: float,
    ) -> str:
        session = self.session
        notice = verify_response(self.last_reply, resolved.turn_evidence)

        if not session.title:
            from hephaistos.chat.session import _derive_title

            session.title = _derive_title(session.conversation)
        session.dirty = True

        _log.info(
            "reply complete",
            extra={
                "fields": {
                    "session_id": session.session_id,
                    "reply_len": len(self.last_reply),
                    "latency_ms": latency_ms,
                    "study_phase": session.study_state.phase.value,
                    "study_feedback": session.study_state.last_feedback_type.value,
                    "evidence_blocks": (
                        len(resolved.turn_evidence.items) if resolved.turn_evidence else 0
                    ),
                }
            },
        )
        session.trace.record_session_event(
            "reply",
            latency_ms=round(latency_ms, 1),
            reply_len=len(self.last_reply),
            study_phase=session.study_state.phase.value,
            study_feedback=session.study_state.last_feedback_type.value,
        )

        if session._memory is not None and len(self.last_reply) >= 100:
            try:
                from hephaistos.memory.extract import extract_and_store

                added = extract_and_store(
                    session.config,
                    session._memory,
                    user_input,
                    self.last_reply,
                    ", ".join(_evidence_refs(resolved.turn_evidence)),
                )
                if added:
                    _log.info(
                        "memory updated",
                        extra={"fields": {"new_entries": added}},
                    )
            except Exception:
                _log.warning("memory extraction failed", exc_info=True)

        if session.armory_path is not None:
            with contextlib.suppress(Exception):
                save_usage(session.armory_path, session.session_id, session.usage)

        return notice

    def _replace_last_assistant_message(self, content: str) -> None:
        for message in reversed(self.session.conversation.messages):
            if message.role == "assistant":
                message.content = content
                return


def _evidence_refs(turn_evidence: TurnEvidence | None) -> list[str]:
    if not turn_evidence:
        return []
    return [f"{item.source}#chunk={item.chunk_index}" for item in turn_evidence.items]


def _parse_source_ref(ref: str) -> tuple[str, int] | None:
    source, sep, suffix = ref.partition("#chunk=")
    if not sep:
        return None
    try:
        return source, int(suffix)
    except ValueError:
        return None


def _ensure_rag_index(session: ChatSession) -> ArmoryIndex | None:
    if session.armory_path is None:
        return None
    if session._rag_index is None:
        session._rag_index = load_or_build(session.armory_path)
    return session._rag_index


def _adaptive_rag_budget(session: ChatSession) -> int:
    budget = ContextBudget(model=session.config.model, max_tokens=session.config.max_tokens)
    api_msgs = session.conversation.to_api_messages()
    remaining = budget.tokens_remaining(api_msgs)  # type: ignore[arg-type]
    return min(session.config.rag_context_budget, max(200, int(remaining * 0.3)))


def _build_turn_evidence_from_query(session: ChatSession, query: str) -> TurnEvidence | None:
    if session.armory_path is None:
        return None
    try:
        timer = Timer()
        index = _ensure_rag_index(session)
        if index is None:
            return None

        with timer:
            scored = retrieve(
                query,
                index,
                top_k=5,
                min_score=_RAG_MIN_SCORE,
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
        return build_turn_evidence(scored, max_tokens=_adaptive_rag_budget(session))
    except Exception:
        _log.warning("turn evidence build failed", exc_info=True)
        return None


def _build_turn_evidence_from_refs(session: ChatSession, refs: list[str]) -> TurnEvidence | None:
    try:
        index = _ensure_rag_index(session)
        if index is None or not refs:
            return None

        by_key = {(chunk.source, chunk.index): chunk for chunk in index.all_chunks}
        scored: list[ScoredChunk] = []
        total = len(refs)
        for pos, ref in enumerate(refs):
            parsed = _parse_source_ref(ref)
            if parsed is None:
                continue
            chunk = by_key.get(parsed)
            if chunk is None:
                continue
            scored.append(ScoredChunk(chunk=chunk, score=float(total - pos)))
        if not scored:
            return None
        return build_turn_evidence(scored, max_tokens=_adaptive_rag_budget(session))
    except Exception:
        _log.warning("turn evidence rebuild from refs failed", exc_info=True)
        return None


def _resolve_turn_evidence(session: ChatSession, plan: StudyTurnPlan) -> TurnEvidence | None:
    if plan.use_expected_source_refs and session.study_state.expected_source_refs:
        turn_evidence = _build_turn_evidence_from_refs(
            session,
            session.study_state.expected_source_refs,
        )
        if turn_evidence:
            return turn_evidence
    if plan.retrieval_query:
        return _build_turn_evidence_from_query(session, plan.retrieval_query)
    return None
