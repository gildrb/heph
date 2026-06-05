"""Internal chat turn output containers."""

from __future__ import annotations

from dataclasses import dataclass, field

from ai.runtime.conversation import Conversation

from hephaion.chat.events import (
    TurnCompleteEvent,
)


@dataclass(frozen=True, slots=True)
class _LearningAgentOutput:
    streamed_reply: str
    raw_reply: str
    visible_reply: str
    completion_event: TurnCompleteEvent | None


@dataclass(slots=True)
class _LearningAgentBuffer:
    raw_parts: list[str] = field(default_factory=list)
    visible_parts: list[str] = field(default_factory=list)
    completion_event: TurnCompleteEvent | None = None

    def add_delta(self, delta: str, *, visible: bool) -> None:
        self.raw_parts.append(delta)
        if visible:
            self.visible_parts.append(delta)

    @property
    def streamed_reply(self) -> str:
        return "".join(self.raw_parts)

    @property
    def visible_streamed_reply(self) -> str:
        return "".join(self.visible_parts)


@dataclass(frozen=True, slots=True)
class _LearningAgentRequest:
    conversation: Conversation
    buffer_output: bool


@dataclass(frozen=True, slots=True)
class _ProcessedLearningReply:
    raw_reply: str
    visible_reply: str
    pass_count: int


@dataclass(frozen=True, slots=True)
class _DeterministicLearningReply:
    reply: str
    source_refs: list[str] | None = None
    internal_passes: int | None = None
    citation_required: bool | None = None
    updates_learning_state: bool = True
