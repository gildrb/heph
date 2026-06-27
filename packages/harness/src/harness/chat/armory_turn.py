"""Armory-backed chat turn setup."""

from __future__ import annotations

import threading
from collections.abc import Generator, Iterator
from dataclasses import replace
from typing import TYPE_CHECKING, Protocol

import harness.chat.intent_resolution as _intent_resolution
from harness.chat.events import NoticeEvent, TurnEvent
from harness.chat.evidence import ResolvedTurnPlan
from harness.chat.evidence import ensure_rag_index as _ensure_rag_index
from harness.chat.evidence_notices import _evidence_notice, _evidence_notice_metadata
from harness.chat.learning_signals import _learning_practice_context
from harness.chat.material_state import _reading_notice
from harness.chat.turn_contract import TurnContract, turn_contract_from_resolution
from harness.chat.turn_planning import (
    _CONTINUABLE_MATERIAL_INTENTS,
    _apply_turn_contract_to_plan,
    _prior_contract_for_followup_seed,
    _reset_unreplayable_followup_state,
    _turn_contract_with_evidence,
    _turn_contract_with_prior_replay_state,
)
from harness.study.controller import plan_turn
from harness.study.policy import MemoryState, ReviewItem
from harness.study.prompt_plans import LearningTurnPlan
from harness.study.state import LearningState

if TYPE_CHECKING:
    from harness.chat.session import ChatSession


class _ArmoryTurnHost(Protocol):
    session: ChatSession

    def _iter_armory_turn_events(
        self,
        original_learning_state: LearningState,
        user_input: str,
        *,
        abort: threading.Event | None,
    ) -> Generator[TurnEvent, None, ResolvedTurnPlan]: ...

    def _resolve_timed_turn_plan(self, plan: LearningTurnPlan) -> ResolvedTurnPlan: ...

    def _iter_material_operation_events(
        self,
        plan: LearningTurnPlan,
        resolved: ResolvedTurnPlan,
    ) -> Iterator[TurnEvent]: ...

    def _iter_learning_events(
        self,
        resolved: ResolvedTurnPlan,
        original_learning_state: LearningState,
        *,
        user_input: str,
        abort: threading.Event | None,
    ) -> Iterator[TurnEvent]: ...


class ArmoryTurnMixin:
    session: ChatSession

    def _iter_armory_turn_events(
        self: _ArmoryTurnHost,
        original_learning_state: LearningState,
        user_input: str,
        *,
        abort: threading.Event | None,
    ) -> Generator[TurnEvent, None, ResolvedTurnPlan]:
        due_reviews, memory_state = _learning_practice_context(self.session)
        prior_contract = _prior_contract_for_followup_seed(self.session)
        default_plan = _default_turn_plan(
            original_learning_state,
            user_input,
            due_reviews=due_reviews,
            memory_state=memory_state,
        )
        learning_plan, turn_contract = _learning_plan_and_contract(
            self.session,
            original_learning_state,
            user_input,
            default_plan=default_plan,
            prior_contract=prior_contract,
            due_reviews=due_reviews,
            memory_state=memory_state,
        )
        if notice := _reading_notice(learning_plan):
            yield NoticeEvent(notice, code="reading")

        resolved = _resolved_with_turn_contract(
            self._resolve_timed_turn_plan(learning_plan),
            learning_plan,
            turn_contract,
        )
        yield from self._iter_material_operation_events(learning_plan, resolved)
        if notice := _evidence_notice(resolved):
            yield NoticeEvent(
                notice,
                code="evidence",
                metadata=_evidence_notice_metadata(resolved, self.session),
            )
        yield from self._iter_learning_events(
            resolved,
            original_learning_state,
            user_input=user_input,
            abort=abort,
        )
        return resolved


def _default_turn_plan(
    original_learning_state: LearningState,
    user_input: str,
    *,
    due_reviews: tuple[ReviewItem, ...],
    memory_state: MemoryState | None,
) -> LearningTurnPlan:
    return plan_turn(
        original_learning_state,
        user_input,
        intent="",
        due_reviews=due_reviews,
        memory_state=memory_state,
    )


def _learning_plan_and_contract(
    session: ChatSession,
    original_learning_state: LearningState,
    user_input: str,
    *,
    default_plan: LearningTurnPlan,
    prior_contract: TurnContract | None,
    due_reviews: tuple[ReviewItem, ...],
    memory_state: MemoryState | None,
) -> tuple[LearningTurnPlan, TurnContract]:
    intent_resolution = _armory_intent_resolution(
        session,
        user_input,
        default_plan=default_plan,
        prior_contract=prior_contract,
    )
    learning_plan = plan_turn(
        original_learning_state,
        user_input,
        intent=intent_resolution.intent,
        due_reviews=due_reviews,
        memory_state=memory_state,
    )
    turn_contract = turn_contract_from_resolution(user_input, intent_resolution)
    learning_plan, turn_contract = _apply_turn_contract_to_plan(
        learning_plan,
        turn_contract,
        prior_contract=prior_contract,
    )
    turn_contract = _turn_contract_with_prior_replay_state(
        turn_contract,
        prior_contract=prior_contract,
        conversation=session.conversation,
        user_input=user_input,
    )
    return _reset_unreplayable_followup_state(learning_plan, turn_contract)


def _armory_intent_resolution(
    session: ChatSession,
    user_input: str,
    *,
    default_plan: LearningTurnPlan,
    prior_contract: TurnContract | None,
):
    intent_index = session.rag_index
    intent_resolution = _intent_resolution._resolved_user_intent(
        user_input,
        config=session.config,
        conversation=session.conversation,
        prior_intent=session.last_plan_intent,
        prior_contract=prior_contract,
    )
    if (
        intent_index is None
        and session.armory_path is not None
        and intent_resolution.intent in _CONTINUABLE_MATERIAL_INTENTS
    ):
        intent_index = _ensure_rag_index(session)
    intent_resolution = _intent_resolution._stabilized_intent_for_named_material(
        intent_resolution,
        user_input=user_input,
        index=intent_index,
    )
    intent_resolution = _intent_resolution._stabilized_intent_for_default_material_plan(
        intent_resolution,
        user_input=user_input,
        default_plan=default_plan,
        prior_contract=prior_contract,
        index=intent_index,
    )
    return _intent_resolution._unresolved_followup_intent_resolution(
        intent_resolution,
        user_input=user_input,
        default_plan=default_plan,
        prior_contract=prior_contract,
    )


def _resolved_with_turn_contract(
    resolved: ResolvedTurnPlan,
    learning_plan: LearningTurnPlan,
    turn_contract: TurnContract,
) -> ResolvedTurnPlan:
    return replace(
        resolved,
        turn_contract=_turn_contract_with_evidence(
            turn_contract,
            learning_plan,
            resolved.turn_evidence,
        ),
    )
