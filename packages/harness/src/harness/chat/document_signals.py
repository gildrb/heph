"""Small trace helpers for grounded document turns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from harness.chat.turn_predicates import _overview_turn
from harness.documents.state import DocumentAction

if TYPE_CHECKING:
    from harness.chat.evidence import ResolvedTurnPlan
    from harness.documents.prompt_plans import DocumentTurnPlan

_TRACE_TASK_BY_ACTION = {
    DocumentAction.SOURCE_QA: "source-qa",
    DocumentAction.PRESENT: "material-overview",
    DocumentAction.CHAT: "chat",
}


def _trace_task(plan: DocumentTurnPlan | None) -> str:
    if plan is None:
        return ""
    if _overview_turn(plan):
        return "material-overview"
    return _TRACE_TASK_BY_ACTION.get(plan.action, plan.action.value)


def _trace_turn_retrieval_query(resolved: ResolvedTurnPlan) -> str:
    if resolved.turn_contract is not None:
        return resolved.turn_contract.retrieval_query
    if resolved.document_plan is None or resolved.document_plan.retrieval_query is None:
        return ""
    return resolved.document_plan.retrieval_query
