"""Learning-event execution mixin for chat turns."""

from __future__ import annotations

import threading
from collections.abc import Generator, Iterator
from typing import TYPE_CHECKING

from agent.dispatch import iter_agent_events
from runtime.engine import build_client, stream_completion
from runtime.errors import RetryConfig
from study.controller import apply_turn_result
from study.policy import LearningMoveKind
from study.prompt_plans import LearningTurnPlan
from study.schedule import (
    RecallItemState,
    RecallScheduleStore,
    load_recall_schedule,
    save_recall_schedule,
)
from study.state import LearningAction, LearningState

from chat.agent_request import (
    _learning_agent_output_from_buffer,
    _learning_agent_request,
)
from chat.events import AssistantDeltaEvent, NoticeEvent, TurnCompleteEvent, TurnEvent
from chat.evidence import ResolvedTurnPlan
from chat.evidence import evidence_refs as _evidence_refs
from chat.learning_reply import (
    _deterministic_learning_reply,
    _empty_learning_reply,
    _plain_empty_reply,
    _postprocess_learning_reply,
)
from chat.learning_signals import (
    _exam_importance,
    _learning_move_kind,
    _matching_recall_item,
    _policy_outcome_from_review,
    _positive_hint_level,
)
from chat.material_state import (
    _tool_result_refreshes_current_armory,
    _writing_notice,
)
from chat.prior_answer import _learning_extra_system_prompt
from chat.reply_repair import _should_buffer_learning_output
from chat.reply_text import _localize_deterministic_reply
from chat.turn_event_helpers import _final_reply_events, _turn_complete_from_result
from chat.turn_outputs import (
    _DeterministicLearningReply,
    _LearningAgentBuffer,
    _LearningAgentOutput,
)

if TYPE_CHECKING:
    from chat.session import ChatSession


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
        for delta in stream_completion(
            session.config,
            session.conversation,
            abort=abort,
            retry=self.retry,
            client_factory=build_client,
        ):
            if not delta.content:
                continue
            parts.append(delta.content)
            yield AssistantDeltaEvent(delta.content)

        if parts:
            self.last_reply = "".join(parts)
        else:
            self.last_reply = _plain_empty_reply(user_input, session.config)
            yield AssistantDeltaEvent(self.last_reply)

        self._append_assistant_message(self.last_reply)
        self.last_internal_passes = 1
        yield _turn_complete_from_result(None, self.last_reply)

    def _iter_learning_agent_events(
        self,
        resolved: ResolvedTurnPlan,
        original_learning_state: LearningState,
        *,
        user_input: str,
        abort: threading.Event | None,
    ) -> Generator[TurnEvent, None, _LearningAgentOutput]:
        session = self.session
        assert session.armory_path is not None
        plan = resolved.learning_plan
        assert plan is not None
        buffer = _LearningAgentBuffer()
        request = _learning_agent_request(
            plan,
            original_learning_state,
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
            extra_system_prompt=_learning_extra_system_prompt(
                session,
                plan,
                resolved,
                user_input=user_input,
            ),
            tool_schemas=None if plan.allow_tools else [],
            allowed_tool_names=plan.allowed_tool_names if plan.allow_tools else (),
            registry=session.tool_registry,
        ):
            yield from self._record_learning_agent_event(
                event,
                buffer,
                buffer_output=request.buffer_output,
            )

        if buffer.visible_parts:
            self.last_reply = buffer.visible_streamed_reply
        return _learning_agent_output_from_buffer(plan, buffer)

    def _record_learning_agent_event(
        self,
        event: TurnEvent,
        buffer: _LearningAgentBuffer,
        *,
        buffer_output: bool,
    ) -> Iterator[TurnEvent]:
        if isinstance(event, AssistantDeltaEvent):
            buffer.add_delta(event.delta, visible=not buffer_output)
            if not buffer_output:
                yield event
            return
        if isinstance(event, TurnCompleteEvent):
            buffer.completion_event = event
            return
        if _tool_result_refreshes_current_armory(event):
            self.session.refresh_armory_sources()
        yield event

    def _iter_empty_learning_reply_events(
        self,
        resolved: ResolvedTurnPlan,
        original_learning_state: LearningState,
        *,
        user_input: str,
    ) -> Iterator[TurnEvent]:
        session = self.session
        plan = resolved.learning_plan
        assert plan is not None
        fallback_reply = _empty_learning_reply(
            plan,
            resolved,
            user_input=user_input,
            config=session.config,
        )
        final_reply = self._apply_learning_reply(
            original_learning_state,
            plan,
            fallback_reply,
            source_refs=_evidence_refs(resolved.turn_evidence),
        )
        yield from _final_reply_events(final_reply)

    def _iter_final_learning_reply_events(
        self,
        plan: LearningTurnPlan,
        completion_event: TurnCompleteEvent | None,
        *,
        raw_reply: str,
        streamed_reply: str,
        final_reply: str,
    ) -> Iterator[TurnEvent]:
        self._persist_final_learning_reply(raw_reply, final_reply)
        self.last_reply = final_reply
        yield from self._final_learning_delta_events(plan, streamed_reply, final_reply)
        yield _turn_complete_from_result(completion_event, final_reply)

    def _persist_final_learning_reply(self, raw_reply: str, final_reply: str) -> None:
        if not final_reply:
            return
        if self._should_append_final_learning_reply():
            self._append_assistant_message(final_reply)
            return
        if raw_reply != final_reply:
            self._replace_last_assistant_message(final_reply)

    def _should_append_final_learning_reply(self) -> bool:
        return (
            not self.session.conversation.messages
            or self.session.conversation.messages[-1].role != "assistant"
        )

    def _replace_last_assistant_message(self, final_reply: str) -> None:
        for message in reversed(self.session.conversation.messages):
            if message.role == "assistant":
                message.content = final_reply
                return

    def _final_learning_delta_events(
        self,
        plan: LearningTurnPlan,
        streamed_reply: str,
        final_reply: str,
    ) -> Iterator[AssistantDeltaEvent]:
        if final_reply and (_should_buffer_learning_output(plan) or not streamed_reply):
            yield AssistantDeltaEvent(final_reply)
            return
        if final_reply == streamed_reply:
            return
        suffix = final_reply.removeprefix(streamed_reply)
        if suffix:
            yield AssistantDeltaEvent(suffix)

    def _iter_learning_events(
        self,
        resolved: ResolvedTurnPlan,
        original_learning_state: LearningState,
        *,
        user_input: str,
        abort: threading.Event | None,
    ) -> Iterator[TurnEvent]:
        session = self.session
        assert session.armory_path is not None
        plan = resolved.learning_plan
        assert plan is not None

        if deterministic_reply := _deterministic_learning_reply(session, plan, resolved):
            yield from self._iter_deterministic_learning_reply_events(
                deterministic_reply,
                original_learning_state,
                plan,
                user_input=user_input,
            )
            return

        if notice := _writing_notice(plan):
            yield NoticeEvent(notice, code="writing")

        agent_output = yield from self._iter_learning_agent_events(
            resolved,
            original_learning_state,
            user_input=user_input,
            abort=abort,
        )
        yield from self._iter_agent_learning_reply_events(
            agent_output,
            resolved,
            original_learning_state,
            user_input=user_input,
        )

    def _iter_deterministic_learning_reply_events(
        self,
        deterministic_reply: _DeterministicLearningReply,
        original_learning_state: LearningState,
        plan: LearningTurnPlan,
        *,
        user_input: str,
    ) -> Iterator[TurnEvent]:
        if deterministic_reply.internal_passes is not None:
            self.last_internal_passes = deterministic_reply.internal_passes
        self._last_reply_citation_required = deterministic_reply.citation_required
        final_reply = self._apply_deterministic_reply(
            original_learning_state,
            plan,
            deterministic_reply.reply,
            user_input=user_input,
            source_refs=deterministic_reply.source_refs,
            updates_learning_state=deterministic_reply.updates_learning_state,
        )
        yield from _final_reply_events(final_reply)

    def _iter_agent_learning_reply_events(
        self,
        agent_output: _LearningAgentOutput,
        resolved: ResolvedTurnPlan,
        original_learning_state: LearningState,
        *,
        user_input: str,
    ) -> Iterator[TurnEvent]:
        session = self.session
        plan = resolved.learning_plan
        assert plan is not None
        streamed_reply = agent_output.streamed_reply
        raw_reply = agent_output.raw_reply
        visible_reply = agent_output.visible_reply
        completion_event = agent_output.completion_event

        if not raw_reply:
            yield from self._iter_empty_learning_reply_events(
                resolved,
                original_learning_state,
                user_input=user_input,
            )
            return

        processed_reply = _postprocess_learning_reply(
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
            final_reply = self._apply_learning_reply(
                original_learning_state,
                plan,
                visible_reply,
                source_refs=source_refs,
            )
            self._record_learning_review_if_needed(
                original_learning_state,
                plan,
                source_refs,
            )
        else:
            session.learning_state = original_learning_state
            final_reply = raw_reply

        yield from self._iter_final_learning_reply_events(
            plan,
            completion_event,
            raw_reply=raw_reply,
            streamed_reply=streamed_reply,
            final_reply=final_reply,
        )

    def _apply_deterministic_reply(
        self,
        original_learning_state: LearningState,
        plan: LearningTurnPlan,
        reply: str,
        *,
        user_input: str,
        source_refs: list[str] | None = None,
        updates_learning_state: bool,
    ) -> str:
        localized_reply = _localize_deterministic_reply(
            reply,
            user_input=user_input,
            config=self.session.config,
        )
        if not updates_learning_state:
            self.last_reply = localized_reply
            self._append_assistant_message(localized_reply)
            return localized_reply
        return self._apply_learning_reply(
            original_learning_state,
            plan,
            localized_reply,
            source_refs=source_refs or [],
        )

    def _apply_learning_reply(
        self,
        original_learning_state: LearningState,
        plan: LearningTurnPlan,
        reply: str,
        *,
        source_refs: list[str],
    ) -> str:
        self.session.learning_state, final_reply = apply_turn_result(
            original_learning_state,
            plan,
            reply,
            source_refs,
        )
        self.last_reply = final_reply
        self._append_assistant_message(final_reply)
        return final_reply

    def _append_assistant_message(self, reply: str) -> None:
        if reply and (
            not self.session.conversation.messages
            or self.session.conversation.messages[-1].role != "assistant"
        ):
            self.session.conversation.add("assistant", reply)

    def _record_learning_review_if_needed(
        self,
        original_learning_state: LearningState,
        plan: LearningTurnPlan,
        source_refs: list[str],
    ) -> None:
        if not self._should_record_learning_review(plan):
            return
        armory_path = self.session.armory_path
        if armory_path is None:
            return
        store = load_recall_schedule(armory_path)
        previous = _matching_recall_item(
            store.item_list,
            item=original_learning_state.current_item,
            retrieval_query=original_learning_state.retrieval_query,
        )
        intervention = _learning_move_kind(plan)
        reviewed_state = self._record_learning_review(
            store,
            original_learning_state.current_item,
            concept=original_learning_state.retrieval_query,
            retrieval_query=original_learning_state.retrieval_query,
            source_refs=source_refs or original_learning_state.expected_source_refs,
            hint_level_needed=_positive_hint_level(original_learning_state),
            intervention=intervention,
            exam_importance=_exam_importance(original_learning_state),
        )
        self._record_learning_policy_outcome(
            store,
            original_learning_state=original_learning_state,
            previous=previous,
            state=reviewed_state,
            intervention=intervention,
        )
        save_recall_schedule(store)

    def _should_record_learning_review(self, plan: LearningTurnPlan) -> bool:
        return (
            self.session.armory_path is not None
            and plan.action is LearningAction.ASSESS
            and self.session.learning_state.last_recall_rating.value != "none"
        )

    def _record_learning_review(
        self,
        store: RecallScheduleStore,
        item: str,
        *,
        concept: str,
        retrieval_query: str,
        source_refs: list[str],
        hint_level_needed: int | None,
        intervention: LearningMoveKind,
        exam_importance: float,
    ) -> RecallItemState:
        state = self.session.learning_state
        return store.record_review(
            item,
            concept=concept,
            retrieval_query=retrieval_query,
            source_refs=source_refs,
            rating=state.last_recall_rating,
            elapsed_seconds=state.last_recall_seconds,
            confidence=state.last_confidence,
            hint_level_needed=hint_level_needed,
            error_type=state.last_feedback_type.value,
            intervention=intervention,
            exam_importance=exam_importance,
        )

    def _record_learning_policy_outcome(
        self,
        store: RecallScheduleStore,
        *,
        original_learning_state: LearningState,
        previous: RecallItemState | None,
        state: RecallItemState,
        intervention: LearningMoveKind,
    ) -> None:
        outcome = _policy_outcome_from_review(
            original_learning_state,
            self.session.learning_state,
            state,
            previous,
            intervention,
        )
        store.record_policy_outcome(
            intervention,
            success=state.last_correct,
            mastery_delta=outcome.mastery_delta,
            confidence_delta=outcome.confidence_delta,
            time_cost_seconds=outcome.time_cost_seconds,
            frustration_signal=outcome.frustration_signal,
        )
        self.session.trace.record_session_event(
            "policy_outcome",
            move_type=outcome.move_type,
            topic=outcome.topic,
            correctness_delta=round(outcome.correctness_delta, 3),
            confidence_delta=round(outcome.confidence_delta, 3),
            mastery_delta=round(outcome.mastery_delta, 3),
            time_cost_seconds=outcome.time_cost_seconds,
            frustration_signal=outcome.frustration_signal,
            score=round(outcome.score, 3),
        )
