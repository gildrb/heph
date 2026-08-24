"""Document-event execution mixin for chat turns."""

from __future__ import annotations

import threading
from collections.abc import Generator, Iterator
from typing import TYPE_CHECKING, Protocol

from ai.runtime import THINKING_VISIBILITY_ALL, THINKING_VISIBILITY_MINIMAL, CompletionDelta, Conversation
from ai.runtime.engine import build_client, stream_completion
from ai.runtime.errors import RetryConfig

from harness.agent.dispatch import iter_agent_events
from harness.chat.agent_request import (
    _document_agent_output_from_buffer,
    _document_agent_request,
)
from harness.chat.document_reply import (
    _deterministic_document_reply,
    _empty_document_reply,
    _plain_empty_reply,
    _postprocess_document_reply,
)
from harness.chat.events import (
    AssistantDeltaEvent,
    NoticeEvent,
    ReasoningDeltaEvent,
    TurnCompleteEvent,
    TurnEvent,
)
from harness.chat.evidence import ResolvedTurnPlan
from harness.chat.evidence import evidence_refs as _evidence_refs
from harness.chat.material_state import (
    _tool_result_refreshes_current_armory,
    _writing_notice,
)
from harness.chat.prior_answer import _document_extra_system_prompt
from harness.chat.reply_repair import _should_buffer_document_output
from harness.chat.reply_text import _localize_deterministic_reply
from harness.chat.turn_event_helpers import _final_reply_events, _turn_complete_from_result
from harness.chat.turn_outputs import (
    _DeterministicDocumentReply,
    _DocumentAgentBuffer,
    _DocumentAgentOutput,
)
from harness.documents.controller import apply_turn_result
from harness.documents.prompt_plans import DocumentTurnPlan
from harness.documents.state import RecallState

if TYPE_CHECKING:
    from harness.chat.session import ChatSession


class _LearningReplyEmissionHost(Protocol):
    session: ChatSession
    last_reply: str
    last_internal_passes: int
    _last_reply_citation_required: bool | None

    def _apply_document_reply(
        self,
        original_recall_state: RecallState,
        plan: DocumentTurnPlan,
        reply: str,
        *,
        source_refs: list[str],
    ) -> str: ...

    def _apply_deterministic_reply(
        self,
        original_recall_state: RecallState,
        plan: DocumentTurnPlan,
        reply: str,
        *,
        user_input: str,
        source_refs: list[str] | None = None,
        updates_recall_state: bool,
    ) -> str: ...

    def _append_assistant_message(self, reply: str) -> None: ...

    def _prepare_document_reply_for_emit(
        self,
        resolved: ResolvedTurnPlan,
        final_reply: str,
        *,
        user_input: str,
        latency_ms: float,
    ) -> tuple[ResolvedTurnPlan, str]: ...

    def _restore_recall_state_for_rewritten_reply(
        self,
        original_recall_state: RecallState,
        applied_reply: str,
        final_reply: str,
    ) -> bool: ...

    def _iter_final_document_reply_events(
        self: _LearningReplyEmissionHost,
        plan: DocumentTurnPlan,
        completion_event: TurnCompleteEvent | None,
        *,
        raw_reply: str,
        streamed_reply: str,
        final_reply: str,
    ) -> Iterator[TurnEvent]: ...

    def _iter_empty_document_reply_events(
        self,
        resolved: ResolvedTurnPlan,
        original_recall_state: RecallState,
        *,
        user_input: str,
    ) -> Iterator[TurnEvent]: ...

    def _iter_deterministic_document_reply_events(
        self,
        deterministic_reply: _DeterministicDocumentReply,
        resolved: ResolvedTurnPlan,
        original_recall_state: RecallState,
        plan: DocumentTurnPlan,
        *,
        user_input: str,
    ) -> Iterator[TurnEvent]: ...

    def _iter_document_agent_events(
        self,
        resolved: ResolvedTurnPlan,
        original_recall_state: RecallState,
        *,
        user_input: str,
        abort: threading.Event | None,
    ) -> Generator[TurnEvent, None, _DocumentAgentOutput]: ...

    def _iter_agent_document_reply_events(
        self,
        agent_output: _DocumentAgentOutput,
        resolved: ResolvedTurnPlan,
        original_recall_state: RecallState,
        *,
        user_input: str,
    ) -> Iterator[TurnEvent]: ...


def _persist_agent_tool_history(
    target: Conversation,
    source: Conversation,
    user_input: str,
    completion_event: TurnCompleteEvent | None,
) -> bool:
    if target is source:
        return False
    start = -1
    for index, message in enumerate(source.messages):
        if message.role == "user" and message.content == user_input:
            start = index
    if start < 0:
        return False
    failed = completion_event is not None and completion_event.finish_reason in {
        "aborted",
        "length",
        "max_turns",
    }
    changed = False
    for message in source.messages[start + 1 :]:
        has_tool_calls = bool(message.metadata.get("tool_calls"))
        is_partial = failed and message.role == "assistant" and bool(message.content)
        if not (message.role == "tool" or has_tool_calls or is_partial):
            continue
        target.add_api_message(message.to_api_message())
        changed = True
    return changed


def _plain_reasoning_delta_event(
    delta: CompletionDelta,
    thinking_visibility: str,
) -> ReasoningDeltaEvent | None:
    if delta.reasoning and thinking_visibility == THINKING_VISIBILITY_ALL:
        return ReasoningDeltaEvent(delta.reasoning)
    if delta.reasoning_summary and thinking_visibility in {
        THINKING_VISIBILITY_MINIMAL,
        THINKING_VISIBILITY_ALL,
    }:
        return ReasoningDeltaEvent(delta.reasoning_summary, summary=True)
    return None


class TurnExecutionMixin:
    session: ChatSession
    retry: RetryConfig | None
    last_reply: str
    last_internal_passes: int
    _last_reply_citation_required: bool | None

    def _iter_plain_events(
        self,
        *,
        user_input: str,
        abort: threading.Event | None,
    ) -> Iterator[TurnEvent]:
        session = self.session
        parts: list[str] = []
        finish_reason = "stop"
        for delta in stream_completion(
            session.config,
            session.conversation,
            abort=abort,
            retry=self.retry,
            client_factory=build_client,
        ):
            if delta.finish_reason:
                finish_reason = delta.finish_reason
            if reasoning_event := _plain_reasoning_delta_event(
                delta,
                session.config.thinking_visibility,
            ):
                yield reasoning_event
            if not delta.content:
                continue
            parts.append(delta.content)
            yield AssistantDeltaEvent(delta.content)

        if abort is not None and abort.is_set():
            finish_reason = "aborted"
        if finish_reason in {"aborted", "length", "max_turns"}:
            self.turn_status = "failed"
            if parts:
                self._append_assistant_message("".join(parts))
            notice = "Turn cancelled." if finish_reason == "aborted" else "Turn ended before completion."
            yield NoticeEvent(notice, code=finish_reason)
            yield TurnCompleteEvent(
                full_text="".join(parts),
                turn_index=0,
                latency_ms=0.0,
                finish_reason=finish_reason,
                tokens_remaining=0,
            )
            return
        if parts:
            self.last_reply = "".join(parts)
        else:
            self.last_reply = _plain_empty_reply(user_input, session.config)
            yield AssistantDeltaEvent(self.last_reply)

        self._append_assistant_message(self.last_reply)
        self.last_internal_passes = 1
        self.turn_status = "success"
        yield _turn_complete_from_result(None, self.last_reply)

    def _iter_document_agent_events(
        self,
        resolved: ResolvedTurnPlan,
        original_recall_state: RecallState,
        *,
        user_input: str,
        abort: threading.Event | None,
    ) -> Generator[TurnEvent, None, _DocumentAgentOutput]:
        session = self.session
        assert session.armory_path is not None
        plan = resolved.document_plan
        assert plan is not None
        buffer = _DocumentAgentBuffer()
        request = _document_agent_request(
            plan,
            original_recall_state,
            user_input,
            session,
            resolved.turn_contract,
        )
        for event in iter_agent_events(
            session.config,
            request.conversation,
            session.armory_path,
            abort=abort,
            retry=self.retry,
            usage=session.usage,
            steering=session.steering,
            turn_evidence=resolved.turn_evidence,
            extra_system_prompt=_document_extra_system_prompt(
                session,
                plan,
                resolved,
                user_input=user_input,
            ),
            tool_schemas=None if plan.allow_tools else [],
            allowed_tool_names=plan.allowed_tool_names if plan.allow_tools else (),
            registry=session.tool_registry,
        ):
            yield from self._record_document_agent_event(
                event,
                buffer,
                buffer_output=request.buffer_output,
            )

        if _persist_agent_tool_history(
            session.conversation,
            request.conversation,
            user_input,
            buffer.completion_event,
        ):
            session.dirty = True
            from harness.chat.session_persistence import save_dirty_session_if_needed

            save_dirty_session_if_needed(session)
        if buffer.visible_parts:
            self.last_reply = buffer.visible_streamed_reply
        return _document_agent_output_from_buffer(plan, buffer)

    def _record_document_agent_event(
        self,
        event: TurnEvent,
        buffer: _DocumentAgentBuffer,
        *,
        buffer_output: bool,
    ) -> Iterator[TurnEvent]:
        if isinstance(event, AssistantDeltaEvent):
            buffer.add_delta(event.delta, visible=not buffer_output)
            if not buffer_output:
                yield event
            return
        if isinstance(event, ReasoningDeltaEvent) and buffer_output:
            return
        if isinstance(event, TurnCompleteEvent):
            buffer.completion_event = event
            return
        if _tool_result_refreshes_current_armory(event):
            self.session.refresh_armory_sources()
        yield event

    def _iter_empty_document_reply_events(
        self: _LearningReplyEmissionHost,
        resolved: ResolvedTurnPlan,
        original_recall_state: RecallState,
        *,
        user_input: str,
    ) -> Iterator[TurnEvent]:
        session = self.session
        plan = resolved.document_plan
        assert plan is not None
        fallback_reply = _empty_document_reply(
            plan,
            resolved,
            user_input=user_input,
            config=session.config,
        )
        final_reply = self._apply_document_reply(
            original_recall_state,
            plan,
            fallback_reply,
            source_refs=_evidence_refs(resolved.turn_evidence),
        )
        applied_reply = final_reply
        _, final_reply = self._prepare_document_reply_for_emit(
            resolved,
            final_reply,
            user_input=user_input,
            latency_ms=0.0,
        )
        self._restore_recall_state_for_rewritten_reply(
            original_recall_state,
            applied_reply,
            final_reply,
        )
        yield from _final_reply_events(final_reply)

    def _iter_final_document_reply_events(
        self,
        plan: DocumentTurnPlan,
        completion_event: TurnCompleteEvent | None,
        *,
        raw_reply: str,
        streamed_reply: str,
        final_reply: str,
    ) -> Iterator[TurnEvent]:
        _persist_final_document_reply(self, raw_reply, final_reply)
        self.last_reply = final_reply
        yield from _final_document_delta_events(plan, streamed_reply, final_reply)
        yield _turn_complete_from_result(completion_event, final_reply)

    def _iter_document_events(
        self: _LearningReplyEmissionHost,
        resolved: ResolvedTurnPlan,
        original_recall_state: RecallState,
        *,
        user_input: str,
        abort: threading.Event | None,
    ) -> Iterator[TurnEvent]:
        session = self.session
        assert session.armory_path is not None
        plan = resolved.document_plan
        assert plan is not None

        if deterministic_reply := _deterministic_document_reply(session, plan, resolved):
            yield from self._iter_deterministic_document_reply_events(
                deterministic_reply,
                resolved,
                original_recall_state,
                plan,
                user_input=user_input,
            )
            return

        if notice := _writing_notice(plan):
            yield NoticeEvent(notice, code="writing")

        agent_output = yield from self._iter_document_agent_events(
            resolved,
            original_recall_state,
            user_input=user_input,
            abort=abort,
        )
        yield from self._iter_agent_document_reply_events(
            agent_output,
            resolved,
            original_recall_state,
            user_input=user_input,
        )

    def _iter_deterministic_document_reply_events(
        self: _LearningReplyEmissionHost,
        deterministic_reply: _DeterministicDocumentReply,
        resolved: ResolvedTurnPlan,
        original_recall_state: RecallState,
        plan: DocumentTurnPlan,
        *,
        user_input: str,
    ) -> Iterator[TurnEvent]:
        if deterministic_reply.internal_passes is not None:
            self.last_internal_passes = deterministic_reply.internal_passes
        self._last_reply_citation_required = deterministic_reply.citation_required
        final_reply = self._apply_deterministic_reply(
            original_recall_state,
            plan,
            deterministic_reply.reply,
            user_input=user_input,
            source_refs=deterministic_reply.source_refs,
            updates_recall_state=deterministic_reply.updates_recall_state,
        )
        applied_reply = final_reply
        if deterministic_reply.updates_recall_state:
            _, final_reply = self._prepare_document_reply_for_emit(
                resolved,
                final_reply,
                user_input=user_input,
                latency_ms=0.0,
            )
            self._restore_recall_state_for_rewritten_reply(
                original_recall_state,
                applied_reply,
                final_reply,
            )
        self.turn_status = "success"
        yield from _final_reply_events(final_reply)

    def _iter_agent_document_reply_events(
        self: _LearningReplyEmissionHost,
        agent_output: _DocumentAgentOutput,
        resolved: ResolvedTurnPlan,
        original_recall_state: RecallState,
        *,
        user_input: str,
    ) -> Iterator[TurnEvent]:
        session = self.session
        plan = resolved.document_plan
        assert plan is not None
        streamed_reply = agent_output.streamed_reply
        raw_reply = agent_output.raw_reply
        visible_reply = agent_output.visible_reply
        completion_event = agent_output.completion_event
        if completion_event is not None and completion_event.finish_reason in {
            "aborted", "length", "max_turns"
        }:
            self.turn_status = "failed"
            yield from _final_reply_events("", completion_event)
            return

        if not raw_reply:
            yield from self._iter_empty_document_reply_events(
                resolved,
                original_recall_state,
                user_input=user_input,
            )
            return

        processed_reply = _postprocess_document_reply(
            plan,
            raw_reply,
            visible_reply,
            resolved,
            user_input=user_input,
            config=session.config,
        )
        raw_reply = processed_reply.raw_reply
        visible_reply = processed_reply.visible_reply
        self.last_internal_passes = processed_reply.pass_count

        if raw_reply:
            source_refs = _evidence_refs(resolved.turn_evidence)
            final_reply = self._apply_document_reply(
                original_recall_state,
                plan,
                visible_reply,
                source_refs=source_refs,
            )
        else:
            source_refs = []
            session.recall_state = original_recall_state
            final_reply = raw_reply

        applied_reply = final_reply
        resolved, final_reply = self._prepare_document_reply_for_emit(
            resolved,
            final_reply,
            user_input=user_input,
            latency_ms=(completion_event.latency_ms if completion_event is not None else 0.0),
        )
        self._restore_recall_state_for_rewritten_reply(
            original_recall_state,
            applied_reply,
            final_reply,
        )
        self.turn_status = "success"
        yield from self._iter_final_document_reply_events(
            plan,
            completion_event,
            raw_reply=raw_reply,
            streamed_reply=streamed_reply,
            final_reply=final_reply,
        )

    def _apply_deterministic_reply(
        self,
        original_recall_state: RecallState,
        plan: DocumentTurnPlan,
        reply: str,
        *,
        user_input: str,
        source_refs: list[str] | None = None,
        updates_recall_state: bool,
    ) -> str:
        localized_reply = _localize_deterministic_reply(
            reply,
            user_input=user_input,
            config=self.session.config,
        )
        if not updates_recall_state:
            self.last_reply = localized_reply
            self._append_assistant_message(localized_reply)
            return localized_reply
        return self._apply_document_reply(
            original_recall_state,
            plan,
            localized_reply,
            source_refs=source_refs or [],
        )

    def _apply_document_reply(
        self,
        original_recall_state: RecallState,
        plan: DocumentTurnPlan,
        reply: str,
        *,
        source_refs: list[str],
    ) -> str:
        self.session.recall_state, final_reply = apply_turn_result(
            original_recall_state,
            plan,
            reply,
            source_refs,
        )
        self.last_reply = final_reply
        self._append_assistant_message(final_reply)
        return final_reply

    def _restore_recall_state_for_rewritten_reply(
        self,
        original_recall_state: RecallState,
        applied_reply: str,
        final_reply: str,
    ) -> bool:
        if final_reply == applied_reply:
            return False
        self.session.recall_state = original_recall_state.clone()
        return True

    def _append_assistant_message(self, reply: str) -> None:
        if reply and (
            not self.session.conversation.messages
            or self.session.conversation.messages[-1].role != "assistant"
        ):
            self.session.conversation.add("assistant", reply)



def _persist_final_document_reply(
    host: TurnExecutionMixin,
    raw_reply: str,
    final_reply: str,
) -> None:
    if not final_reply:
        return
    if _should_append_final_document_reply(host.session):
        host._append_assistant_message(final_reply)
        return
    if raw_reply != final_reply:
        _replace_last_assistant_message(host.session, final_reply)


def _should_append_final_document_reply(session: ChatSession) -> bool:
    return (
        not session.conversation.messages or session.conversation.messages[-1].role != "assistant"
    )


def _replace_last_assistant_message(session: ChatSession, final_reply: str) -> None:
    for message in reversed(session.conversation.messages):
        if message.role == "assistant":
            message.content = final_reply
            return


def _final_document_delta_events(
    plan: DocumentTurnPlan,
    streamed_reply: str,
    final_reply: str,
) -> Iterator[AssistantDeltaEvent]:
    if final_reply and (_should_buffer_document_output(plan) or not streamed_reply):
        yield AssistantDeltaEvent(final_reply)
        return
    if final_reply == streamed_reply:
        return
    suffix = final_reply.removeprefix(streamed_reply)
    if suffix:
        yield AssistantDeltaEvent(suffix)
