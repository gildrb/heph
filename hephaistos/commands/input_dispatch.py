"""Compatibility adapter for shell-style input dispatch."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from hephaistos.chat.session import ChatSession
from hephaistos.input_history import InputHistory
from hephaistos.shell_input import handle_input, run_shell_command


@dataclass(frozen=True, slots=True)
class InputDispatchResult:
    """Result of dispatching one shell-style input."""

    session: ChatSession
    should_continue: bool = True


def dispatch_input(
    session: ChatSession,
    user_input: str,
    history: InputHistory,
    *,
    streaming: bool = False,
    shell_runner: Callable[[str], None] = run_shell_command,
) -> InputDispatchResult:
    """Process one shell-style input through the canonical shell dispatcher."""
    if shell_runner is not run_shell_command and user_input.startswith("!"):
        cmd = user_input[1:].strip()
        if cmd:
            history.add(user_input)
            shell_runner(cmd)
        return InputDispatchResult(session)
    next_session, should_continue = handle_input(
        session,
        user_input,
        history,
        streaming=streaming,
    )
    return InputDispatchResult(next_session, should_continue=should_continue)
