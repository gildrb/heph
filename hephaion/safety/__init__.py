"""Default-on safety and quality guardrails for Heph turns."""

from hephaion.safety.contracts import (
    GUARDRAIL_ACTION_ALLOW,
    GUARDRAIL_ACTION_BLOCK,
    GUARDRAIL_ACTION_WARN,
    GUARDRAIL_STAGE_INPUT,
    GUARDRAIL_STAGE_OUTPUT,
    GUARDRAIL_STAGE_TOOL_CALL,
    GUARDRAIL_STAGE_TOOL_RESULT,
    GuardrailDecision,
    GuardrailMessage,
    GuardrailToolCall,
    allow_guardrail,
    block_guardrail,
    warn_guardrail,
)
from hephaion.safety.local import check_tool_call_names, check_user_input
from hephaion.safety.openai_adapter import (
    check_openai_input,
    check_openai_output,
    check_openai_tool_calls,
    check_openai_tool_results,
    reset_openai_guardrails_runner_factory,
    set_openai_guardrails_runner_factory,
    should_buffer_openai_output,
)

__all__ = [
    "GUARDRAIL_ACTION_ALLOW",
    "GUARDRAIL_ACTION_BLOCK",
    "GUARDRAIL_ACTION_WARN",
    "GUARDRAIL_STAGE_INPUT",
    "GUARDRAIL_STAGE_OUTPUT",
    "GUARDRAIL_STAGE_TOOL_CALL",
    "GUARDRAIL_STAGE_TOOL_RESULT",
    "GuardrailDecision",
    "GuardrailMessage",
    "GuardrailToolCall",
    "allow_guardrail",
    "block_guardrail",
    "check_openai_input",
    "check_openai_output",
    "check_openai_tool_calls",
    "check_openai_tool_results",
    "check_tool_call_names",
    "check_user_input",
    "reset_openai_guardrails_runner_factory",
    "set_openai_guardrails_runner_factory",
    "should_buffer_openai_output",
    "warn_guardrail",
]
