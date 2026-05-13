from __future__ import annotations

import pytest

from hephaistos.chat.engine import ChatConfig
from hephaistos.chat.session import create_plain_session
from hephaistos.commands.input_dispatch import dispatch_input
from hephaistos.terminal.history import InputHistory


def test_dispatch_prints_command_result_output(capsys: pytest.CaptureFixture[str]) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    history = InputHistory()

    result = dispatch_input(session, "/status", history)

    assert result.should_continue is True
    assert result.session is session
    assert "Model:" in capsys.readouterr().out


def test_dispatch_plain_greeting_bypasses_missing_model_config(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig())
    history = InputHistory()

    result = dispatch_input(session, "hey", history)

    out = capsys.readouterr().out
    assert result.should_continue is True
    assert "Hey." in out
    assert "No model" not in out


def test_dispatch_no_armory_question_uses_local_guardrail(
    capsys: pytest.CaptureFixture[str],
) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    history = InputHistory()

    result = dispatch_input(session, "What is 2+2?", history)

    out = capsys.readouterr().out
    assert result.should_continue is True
    assert "No armory is attached" in out
    assert "/armory" in out
    assert "Hephaistos:" not in out
    assert session.conversation.messages[-1].role == "assistant"
