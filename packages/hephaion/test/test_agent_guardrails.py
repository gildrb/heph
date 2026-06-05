"""Tests for default-on agent guardrail checkpoints."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

from ai.logging import Timer
from ai.runtime import ChatConfig, Conversation
from hephaion.agent.dispatch import AgentLoopState, _tool_turn_events, iter_agent_events
from hephaion.agent.model_stream import ModelStreamState, ModelTurnResult
from hephaion.agent.tool_execution import ToolCall
from hephaion.agent.tools import ToolRegistry
from hephaion.chat.events import GuardrailEvent, TurnCompleteEvent, TurnEvent
from hephaion.chat.usage import ContextBudget


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

    with patch("hephaion.agent.dispatch.execute_tool_calls") as execute_tool_calls:
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

    with patch("hephaion.agent.dispatch.run_model_turn", side_effect=model_turn) as run_model_turn:
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
