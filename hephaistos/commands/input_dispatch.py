"""UI-neutral dispatch for shell-style user input.

This is the adapter-level command harness shared by TUI and command-oriented
frontends. Rendering still goes through app display helpers for now, but input
classification and slash-command dispatch no longer live in the TUI workspace.
"""

from __future__ import annotations

import subprocess  # nosec B404
import threading
from collections.abc import Callable
from dataclasses import dataclass

from hephaistos.analytics import capture as capture_analytics
from hephaistos.chat.session import ChatSession, send_user_message
from hephaistos.commands.harness import dispatch_slash_command
from hephaistos.input_history import InputHistory
from hephaistos.observability import capture_exception
from hephaistos.runtime import (
    EngineError,
    StreamRecoveryError,
    is_keyless_endpoint,
    is_network_error,
    missing_api_key_message,
    offline_message,
)
from hephaistos.terminal_display import (
    STYLE_ASSISTANT,
    STYLE_DIM,
    STYLE_ERROR,
    print_error,
    print_info,
    styled,
)


@dataclass(frozen=True, slots=True)
class InputDispatchResult:
    """Result of dispatching one shell-style input."""

    session: ChatSession
    should_continue: bool = True


def run_shell_command(cmd: str) -> None:
    """Execute a user-requested shell escape and stream output to the terminal."""
    print(styled(f"$ {cmd}", STYLE_DIM))
    try:
        subprocess.run(cmd, shell=True, capture_output=False, text=True, check=False)  # nosec B602
    except Exception as exc:
        print_error(str(exc))


def preflight_config_check(session: ChatSession) -> str | None:
    """Return an error message if the session config is unusable, else None."""
    if not session.config.base_url:
        return "No provider configured. Use /provider use <slug> to select one."
    if not session.config.model:
        return "No model configured. Use /models to select one."
    if not is_keyless_endpoint(session.config.base_url) and not session.config.resolved_api_key:
        return missing_api_key_message(session.config)
    return None


def report_engine_error(exc: EngineError | StreamRecoveryError, session: ChatSession) -> None:
    """Display an engine error and capture local diagnostic context."""
    provider = session.config.provider_slug or "the provider"

    if isinstance(exc, StreamRecoveryError):
        if is_network_error(exc):
            print(offline_message(provider))
        else:
            msg = (
                f"{styled('warning:', STYLE_ERROR)} "
                f"Stream interrupted — connection lost after partial reply."
            )
            if exc.partial_content:
                msg += f" ({len(exc.partial_content)} chars received)"
            print(msg)
        capture_exception(
            exc,
            context={
                "provider": provider,
                "model": session.config.model,
                "partial_content_length": len(exc.partial_content),
            },
        )
        capture_analytics(
            "request_failed",
            {
                "provider": provider,
                "model": session.config.model,
                "kind": "stream_recovery",
                "partial_content_length": len(exc.partial_content),
            },
        )
        return

    if is_network_error(exc):
        print(offline_message(provider))
    else:
        print_error(str(exc))
    capture_exception(
        exc,
        context={
            "provider": provider,
            "model": session.config.model,
        },
    )
    capture_analytics(
        "request_failed",
        {
            "provider": provider,
            "model": session.config.model,
            "kind": "engine_error",
        },
    )


def dispatch_input(
    session: ChatSession,
    user_input: str,
    history: InputHistory,
    *,
    streaming: bool = False,
    shell_runner: Callable[[str], None] = run_shell_command,
) -> InputDispatchResult:
    """Process one shell-style input without depending on the TUI."""
    if not user_input or not user_input.strip():
        return InputDispatchResult(session)
    if streaming:
        session.steering.enqueue(user_input)
        return InputDispatchResult(session)
    if user_input.startswith("!"):
        cmd = user_input[1:].strip()
        if cmd:
            history.add(user_input)
            shell_runner(cmd)
        return InputDispatchResult(session)
    if user_input.startswith("/"):
        return _dispatch_slash_command(session, user_input, history)
    return _dispatch_user_message(session, user_input, history)


def _dispatch_slash_command(
    session: ChatSession,
    user_input: str,
    history: InputHistory,
) -> InputDispatchResult:
    history.add(user_input)
    dispatch = dispatch_slash_command(session, user_input)
    if not dispatch.found:
        print_error(f"Unknown command: {dispatch.invocation.raw}")
        print_info("Type /help for available commands.")
        return InputDispatchResult(session)

    result = dispatch.result
    if result is None:
        return InputDispatchResult(session)
    if result.should_exit:
        return InputDispatchResult(session, should_continue=False)

    next_session = result.new_session or session
    if result.output:
        if result.output.startswith("__RESEND__:"):
            new_input = result.output[len("__RESEND__:") :]
            history.add(new_input)
            _send_checked_user_message(next_session, new_input)
        else:
            print(result.output)
    return InputDispatchResult(next_session)


def _dispatch_user_message(
    session: ChatSession,
    user_input: str,
    history: InputHistory,
) -> InputDispatchResult:
    history.add(user_input)
    _send_checked_user_message(session, user_input)
    return InputDispatchResult(session)


def _send_checked_user_message(session: ChatSession, user_input: str) -> None:
    config_error = preflight_config_check(session)
    if config_error:
        print_error(config_error)
        return
    abort = threading.Event()
    reply_prefix = f"\r{styled('Hephaistos:', STYLE_ASSISTANT)} "
    try:
        send_user_message(session, user_input, abort=abort, reply_prefix=reply_prefix)
    except (StreamRecoveryError, EngineError) as exc:
        report_engine_error(exc, session)
