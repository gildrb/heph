"""Fast structural guardrails that are always available."""

from __future__ import annotations

from collections.abc import Sequence

from hephaion.safety.contracts import (
    GUARDRAIL_STAGE_INPUT,
    GUARDRAIL_STAGE_TOOL_CALL,
    GuardrailDecision,
    GuardrailMessage,
    GuardrailToolCall,
    allow_guardrail,
    block_guardrail,
)


def check_user_input(
    user_input: str,
    *,
    conversation: Sequence[GuardrailMessage],
) -> GuardrailDecision:
    del user_input, conversation
    return allow_guardrail(GUARDRAIL_STAGE_INPUT)


def check_tool_call_names(
    tool_calls: Sequence[GuardrailToolCall],
    *,
    allowed_tool_names: frozenset[str],
) -> GuardrailDecision:
    unknown_names = tuple(
        tool_call.name for tool_call in tool_calls if tool_call.name not in allowed_tool_names
    )
    if not unknown_names:
        return allow_guardrail(GUARDRAIL_STAGE_TOOL_CALL)
    return block_guardrail(
        GUARDRAIL_STAGE_TOOL_CALL,
        "Blocked a tool call that is not registered in this armory.",
        metadata={"tool_names": list(unknown_names)},
    )
