"""Tests for default-on agent guardrail checkpoints."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

from ai.logging import Timer
from ai.runtime import ChatConfig, CompletionDelta, Conversation
from harness.agent.dispatch import AgentLoopState, _tool_turn_events, iter_agent_events
from harness.agent.model_stream import (
    ModelStreamState,
    ModelTurnResult,
    _reasoning_delta_event,
)
from harness.agent.tool_execution import ToolCall
from harness.agent.tools import ToolRegistry
from harness.chat.events import GuardrailEvent, ReasoningDeltaEvent, TurnCompleteEvent, TurnEvent
from harness.chat.orchestrator import TurnOrchestrator
from harness.chat.session import ChatSession
from harness.chat.turn_execution import _plain_reasoning_delta_event
from harness.chat.turn_outputs import _LearningAgentBuffer
from harness.chat.usage import ContextBudget


def test_unknown_tool_call_is_blocked_before_execution(tmp_path: Path) -> None:
    conversation = Conversation()
    state = AgentLoopState(
        api_messages=[{"role": "user", "content": "Read my notes."}],
        loop_timer=Timer(),
        budget=ContextBudget("test-model", max_tokens=128, context_window=4096),
        tool_call_counts={},
    )
    stream_state = ModelStreamState("test-model", started_at=0.0, last_progress_at=0.0)
    tool_calls: list[ToolCall] = [
        {
            "id": "call_1",
            "type": "function",
            "function": {"name": "unknown_tool", "arguments": "{}"},
        }
    ]

    with patch("harness.agent.dispatch.execute_tool_calls") as execute_tool_calls:
        events = list(
            _tool_turn_events(
                config=ChatConfig(model="test-model"),
                conversation=conversation,
                workspace=tmp_path,
                registry=ToolRegistry(),
                abort=None,
                usage=None,
                steering=None,
                state=state,
                model_result_text="",
                model_result_tool_calls=tool_calls,
                model_stream_state=stream_state,
                model_turn_timer=Timer(),
                turn_idx=0,
            )
        )

    execute_tool_calls.assert_not_called()
    assert any(isinstance(event, GuardrailEvent) for event in events)
    assert (
        conversation.messages[-1].content
        == "Blocked a tool call that is not registered in this armory."
    )


def test_reasoning_delta_visibility_respects_configured_mode() -> None:
    summary_delta = CompletionDelta(reasoning_summary="short summary")
    raw_delta = CompletionDelta(reasoning="raw thinking")
    combined_delta = CompletionDelta(reasoning="raw thinking", reasoning_summary="short summary")

    assert _reasoning_delta_event(summary_delta, "off") is None
    minimal_event = _reasoning_delta_event(summary_delta, "minimal")
    all_event = _reasoning_delta_event(raw_delta, "all")

    assert minimal_event == ReasoningDeltaEvent("short summary", summary=True)
    assert _reasoning_delta_event(raw_delta, "minimal") is None
    assert all_event == ReasoningDeltaEvent("raw thinking")
    assert _reasoning_delta_event(combined_delta, "all") == ReasoningDeltaEvent("raw thinking")
    assert _plain_reasoning_delta_event(combined_delta, "all") == ReasoningDeltaEvent(
        "raw thinking"
    )


def test_buffered_learning_agent_suppresses_reasoning_events() -> None:
    orchestrator = TurnOrchestrator(
        ChatSession(
            config=ChatConfig(model="test-model"),
            conversation=Conversation(),
            session_id="test-session",
        )
    )
    hidden_reasoning = ReasoningDeltaEvent("hidden source-grounded pass", summary=True)
    visible_reasoning = ReasoningDeltaEvent("visible pass", summary=True)

    hidden_events = list(
        orchestrator._record_learning_agent_event(
            hidden_reasoning,
            _LearningAgentBuffer(),
            buffer_output=True,
        )
    )
    visible_events = list(
        orchestrator._record_learning_agent_event(
            visible_reasoning,
            _LearningAgentBuffer(),
            buffer_output=False,
        )
    )

    assert hidden_events == []
    assert visible_events == [visible_reasoning]


def test_blocked_tool_call_completes_agent_loop(tmp_path: Path) -> None:
    tool_calls: list[ToolCall] = [
        {
            "id": "call_1",
            "type": "function",
            "function": {"name": "unknown_tool", "arguments": "{}"},
        }
    ]
    model_result = ModelTurnResult(
        text="",
        tool_calls=tool_calls,
        stream_state=ModelStreamState("test-model", started_at=0.0, last_progress_at=0.0),
        turn_timer=Timer(),
    )

    def model_turn(**_kwargs: object) -> Generator[TurnEvent, None, ModelTurnResult]:
        yield from ()
        return model_result

    with patch("harness.agent.dispatch.run_model_turn", side_effect=model_turn) as run_model_turn:
        events = list(
            iter_agent_events(
                ChatConfig(model="test-model"),
                Conversation(),
                tmp_path,
                registry=ToolRegistry(),
                tool_schemas=[],
            )
        )

    assert run_model_turn.call_count == 1
    assert any(isinstance(event, TurnCompleteEvent) for event in events)
