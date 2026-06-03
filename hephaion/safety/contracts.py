"""Small provider-neutral guardrail contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

type GuardrailAction = Literal["allow", "warn", "block"]
type GuardrailStage = Literal["input", "tool_call", "tool_result", "output"]

GUARDRAIL_ACTION_ALLOW: GuardrailAction = "allow"
GUARDRAIL_ACTION_WARN: GuardrailAction = "warn"
GUARDRAIL_ACTION_BLOCK: GuardrailAction = "block"
GUARDRAIL_STAGE_INPUT: GuardrailStage = "input"
GUARDRAIL_STAGE_TOOL_CALL: GuardrailStage = "tool_call"
GUARDRAIL_STAGE_TOOL_RESULT: GuardrailStage = "tool_result"
GUARDRAIL_STAGE_OUTPUT: GuardrailStage = "output"


@dataclass(frozen=True, slots=True)
class GuardrailMessage:
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class GuardrailToolCall:
    call_id: str
    name: str
    arguments: str


@dataclass(frozen=True, slots=True)
class GuardrailDecision:
    stage: GuardrailStage
    action: GuardrailAction = GUARDRAIL_ACTION_ALLOW
    message: str = ""
    replacement_text: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def blocks(self) -> bool:
        return self.action == GUARDRAIL_ACTION_BLOCK

    @property
    def warns(self) -> bool:
        return self.action == GUARDRAIL_ACTION_WARN


def allow_guardrail(stage: GuardrailStage) -> GuardrailDecision:
    return GuardrailDecision(stage=stage)


def warn_guardrail(
    stage: GuardrailStage,
    message: str,
    *,
    metadata: dict[str, object] | None = None,
) -> GuardrailDecision:
    return GuardrailDecision(
        stage=stage,
        action=GUARDRAIL_ACTION_WARN,
        message=message,
        replacement_text="",
        metadata=dict(metadata or {}),
    )


def block_guardrail(
    stage: GuardrailStage,
    message: str,
    *,
    metadata: dict[str, object] | None = None,
) -> GuardrailDecision:
    return GuardrailDecision(
        stage=stage,
        action=GUARDRAIL_ACTION_BLOCK,
        message=message,
        replacement_text="",
        metadata=dict(metadata or {}),
    )
