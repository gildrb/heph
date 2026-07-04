"""Armory-backed chat turn setup."""

from __future__ import annotations

import threading
from collections.abc import Generator, Iterator
from dataclasses import replace
from typing import TYPE_CHECKING, Protocol

import harness.chat.intent_resolution as _intent_resolution
from harness.chat.document_signals import _recall_practice_context
from harness.chat.events import NoticeEvent, TurnEvent
from harness.chat.evidence import ResolvedTurnPlan
from harness.chat.evidence import ensure_rag_index as _ensure_rag_index
from harness.chat.evidence_notices import _evidence_notice, _evidence_notice_metadata
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
from harness.documents.controller import plan_turn
from harness.documents.policy import MemoryState, ReviewItem
from harness.documents.prompt_plans import DocumentTurnPlan
from harness.documents.state import RecallState

if TYPE_CHECKING:
    from harness.chat.session import ChatSession


class _ArmoryTurnHost(Protocol):
    session: ChatSession

    def _iter_armory_turn_events(
        self,
        original_recall_state: RecallState,
        user_input: str,
        *,
        abort: threading.Event | None,
    ) -> Generator[TurnEvent, None, ResolvedTurnPlan]: ...

    def _resolve_timed_turn_plan(self, plan: DocumentTurnPlan) -> ResolvedTurnPlan: ...

    def _iter_material_operation_events(
        self,
        plan: DocumentTurnPlan,
        resolved: ResolvedTurnPlan,
    ) -> Iterator[TurnEvent]: ...

    def _iter_document_events(
        self,
        resolved: ResolvedTurnPlan,
        original_recall_state: RecallState,
        *,
        user_input: str,
        abort: threading.Event | None,
    ) -> Iterator[TurnEvent]: ...


class ArmoryTurnMixin:
    session: ChatSession

    def _iter_armory_turn_events(
        self: _ArmoryTurnHost,
        original_recall_state: RecallState,
        user_input: str,
        *,
        abort: threading.Event | None,
    ) -> Generator[TurnEvent, None, ResolvedTurnPlan]:
        due_reviews, memory_state = _recall_practice_context(self.session)
        prior_contract = _prior_contract_for_followup_seed(self.session)
        default_plan = _default_turn_plan(
            original_recall_state,
            user_input,
            due_reviews=due_reviews,
            memory_state=memory_state,
        )
        document_plan, turn_contract = _document_plan_and_contract(
            self.session,
            original_recall_state,
            user_input,
            default_plan=default_plan,
            prior_contract=prior_contract,
            due_reviews=due_reviews,
            memory_state=memory_state,
        )
        if notice := _reading_notice(document_plan):
            yield NoticeEvent(notice, code="reading")

        resolved = _resolved_with_turn_contract(
            self._resolve_timed_turn_plan(document_plan),
            document_plan,
            turn_contract,
        )
        yield from self._iter_material_operation_events(document_plan, resolved)
        if notice := _evidence_notice(resolved):
            yield NoticeEvent(
                notice,
                code="evidence",
                metadata=_evidence_notice_metadata(resolved, self.session),
            )
        yield from self._iter_document_events(
            resolved,
            original_recall_state,
            user_input=user_input,
            abort=abort,
        )
        return resolved


def _default_turn_plan(
    original_recall_state: RecallState,
    user_input: str,
    *,
    due_reviews: tuple[ReviewItem, ...],
    memory_state: MemoryState | None,
) -> DocumentTurnPlan:
    return plan_turn(
        original_recall_state,
        user_input,
        intent="",
        due_reviews=due_reviews,
        memory_state=memory_state,
    )


def _document_plan_and_contract(
    session: ChatSession,
    original_recall_state: RecallState,
    user_input: str,
    *,
    default_plan: DocumentTurnPlan,
    prior_contract: TurnContract | None,
    due_reviews: tuple[ReviewItem, ...],
    memory_state: MemoryState | None,
) -> tuple[DocumentTurnPlan, TurnContract]:
    intent_resolution = _armory_intent_resolution(
        session,
        user_input,
        default_plan=default_plan,
        prior_contract=prior_contract,
    )
    document_plan = plan_turn(
        original_recall_state,
        user_input,
        intent=intent_resolution.intent,
        due_reviews=due_reviews,
        memory_state=memory_state,
    )
    turn_contract = turn_contract_from_resolution(user_input, intent_resolution)
    document_plan, turn_contract = _apply_turn_contract_to_plan(
        document_plan,
        turn_contract,
        prior_contract=prior_contract,
    )
    turn_contract = _turn_contract_with_prior_replay_state(
        turn_contract,
        prior_contract=prior_contract,
        conversation=session.conversation,
        user_input=user_input,
    )
    return _reset_unreplayable_followup_state(document_plan, turn_contract)


def _armory_intent_resolution(
    session: ChatSession,
    user_input: str,
    *,
    default_plan: DocumentTurnPlan,
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
    document_plan: DocumentTurnPlan,
    turn_contract: TurnContract,
) -> ResolvedTurnPlan:
    return replace(
        resolved,
        turn_contract=_turn_contract_with_evidence(
            turn_contract,
            document_plan,
            resolved.turn_evidence,
        ),
    )
