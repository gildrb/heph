"""Plan grounded chat turns without study-session state machines."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from harness.documents.prompt_plans import (
    DocumentTurnPlan,
    _open_material_plan_for_intent,
    heph_action_plan,
    heph_help_plan,
    material_overview_plan,
    plain_chat_plan,
)


def plan_turn(
    _state: Any,
    user_input: str,
    *,
    intent: str = "",
    **_legacy_options: object,
) -> DocumentTurnPlan:
    if intent == "heph_action":
        return heph_action_plan(user_input)
    if intent == "heph_help":
        return heph_help_plan(user_input)
    if intent == "chat":
        return plain_chat_plan(user_input)
    if intent in {"material_overview", "source_qa", "topic_presentation"}:
        return _open_material_plan_for_intent(user_input, intent)
    return material_overview_plan(user_input, retrieval_query=user_input.strip() or None)


def apply_turn_result(
    state: Any,
    _plan: DocumentTurnPlan,
    reply: str,
    _source_refs: list[str],
    *,
    now: datetime | None = None,
) -> tuple[Any, str]:
    """Keep the legacy call boundary while turns no longer mutate study state."""
    del now
    return state, reply
