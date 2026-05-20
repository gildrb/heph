"""Shell input dispatch for workspace chat sessions."""

from __future__ import annotations

import subprocess  # nosec B404
import threading
from collections.abc import Callable
from typing import TYPE_CHECKING, Protocol

from hephaistos.chat.session import no_armory_guidance_reply
from hephaistos.diagnostics.crashes import capture_exception
from hephaistos.diagnostics.events import capture as capture_analytics
from hephaistos.runtime import has_configured_access
from hephaistos.study import plan_turn
from hephaistos.terminal.display import (
    STYLE_ASSISTANT,
    STYLE_DIM,
    STYLE_ERROR,
    print_error,
    print_info,
    styled,
)
from hephaistos.terminal.history import InputHistory

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession


class CommandResultProtocol(Protocol):
    should_exit: bool
    new_session: ChatSession | None
    output: str | None


class CommandProtocol(Protocol):
    def handle(self, session: object, args: str) -> CommandResultProtocol: ...


class CommandRegistryProtocol(Protocol):
    def find(self, name: str) -> CommandProtocol | None: ...


_command_registry_fn: Callable[[], CommandRegistryProtocol] | None = None


def set_command_registry_fn(fn: Callable[[], CommandRegistryProtocol]) -> None:
    global _command_registry_fn  # noqa: PLW0603
    _command_registry_fn = fn


def _get_command_registry() -> CommandRegistryProtocol:
    if _command_registry_fn is None:
        msg = "Command registry not initialized"
        raise RuntimeError(msg)
    return _command_registry_fn()


def run_shell_command(cmd: str) -> None:
    print(styled(f"$ {cmd}", STYLE_DIM))
    try:
        subprocess.run(cmd, shell=True, capture_output=False, text=True, check=False)  # nosec B602
    except Exception as exc:
        print_error(str(exc))


def _preflight_config_check(session: ChatSession) -> str | None:
    if not session.config.base_url:
        return "No model source configured. Use /login, then /models."
    if not session.config.model:
        return "No model configured. Use /models to select one."
    if not has_configured_access(session.config):
        from hephaistos.runtime import missing_api_key_message

        return missing_api_key_message(session.config)
    return None


def _report_engine_error(
    exc: BaseException,
    session: ChatSession,
) -> None:
    from hephaistos.runtime import (
        StreamRecoveryError,
        is_network_error,
        offline_message,
    )

    provider = session.config.provider_slug or "the provider"
    context: dict[str, object] = {
        "provider": provider,
        "model": session.config.model,
    }
    kind = "engine_error"

    if isinstance(exc, StreamRecoveryError):
        kind = "stream_recovery"
        context["partial_content_length"] = len(exc.partial_content)
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
    elif is_network_error(exc):
        print(offline_message(provider))
    else:
        print_error(str(exc))
    capture_exception(exc, context=context)
    capture_analytics("request_failed", {**context, "kind": kind})


def handle_input(
    session: ChatSession,
    user_input: str,
    history: InputHistory,
    streaming: bool = False,
) -> tuple[ChatSession, bool]:
    if not user_input.strip():
        return session, True
    if streaming:
        session.steering.enqueue(user_input)
        return session, True
    if user_input.startswith("!"):
        cmd = user_input[1:].strip()
        if cmd:
            history.add(user_input)
            run_shell_command(cmd)
        return session, True
    if user_input.startswith("/"):
        return _handle_slash_input(session, user_input, history)
    history.add(user_input)
    return _send_message(session, user_input), True


def _handle_slash_input(
    session: ChatSession,
    user_input: str,
    history: InputHistory,
) -> tuple[ChatSession, bool]:
    history.add(user_input)
    stripped = user_input.strip()
    if stripped == "/":
        registry = _get_command_registry()
        cmd = registry.find("help")
        if cmd:
            cmd.handle(session, "")
        return session, True
    cmd_name, _, cmd_args = stripped[1:].partition(" ")
    cmd_name = cmd_name.lower()
    cmd_args = cmd_args.strip()

    registry = _get_command_registry()
    cmd = registry.find(cmd_name)
    if cmd is None:
        print_error(f"Unknown command: {stripped}")
        print_info("Type /help for available commands.")
        return session, True

    result = cmd.handle(session, cmd_args)
    if result.should_exit:
        return session, False
    if result.new_session is not None:
        session = result.new_session
    if result.output and not result.output.startswith("__RESEND__:"):
        print(result.output)
    if result.output and result.output.startswith("__RESEND__:"):
        new_input = result.output[len("__RESEND__:") :]
        history.add(new_input)
        session = _send_message(session, new_input)
    return session, True


def _send_message(session: ChatSession, user_input: str) -> ChatSession:
    from hephaistos.chat.session import send_user_message
    from hephaistos.runtime import EngineError, StreamRecoveryError

    can_reply_without_model = plan_turn(session.study_state, user_input).direct_reply is not None
    if session.armory_path is None and not can_reply_without_model:
        reply = no_armory_guidance_reply()
        session.conversation.add("user", user_input)
        session.conversation.add("assistant", reply)
        print(styled(reply, STYLE_ASSISTANT))
        return session
    config_error = None if can_reply_without_model else _preflight_config_check(session)
    if config_error:
        print_error(config_error)
        return session
    abort = threading.Event()
    try:
        send_user_message(session, user_input, abort=abort, reply_prefix="")
    except (StreamRecoveryError, EngineError) as exc:
        _report_engine_error(exc, session)
    return session
