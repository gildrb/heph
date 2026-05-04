from __future__ import annotations

import pytest

from hephaistos.chat.engine import ChatConfig
from hephaistos.chat.session import create_plain_session
from hephaistos.commands.input_dispatch import dispatch_input
from hephaistos.input_history import InputHistory


def test_dispatch_prints_command_result_output(capsys: pytest.CaptureFixture[str]) -> None:
    session = create_plain_session(ChatConfig(api_key="test-key"))
    history = InputHistory()

    result = dispatch_input(session, "/status", history)

    assert result.should_continue is True
    assert result.session is session
    assert "Model:" in capsys.readouterr().out
