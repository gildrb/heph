"""Single-turn orchestration public surface for chat sessions."""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING

from harness.chat.events import TurnEvent
from harness.chat.message_delivery import send_user_message as _deliver_user_message
from harness.chat.turn_orchestrator import TurnOrchestrator

if TYPE_CHECKING:
    from harness.chat.session import ChatSession


def iter_chat_events(
    session: ChatSession,
    prompt: str,
    *,
    abort: threading.Event | None = None,
) -> Iterator[TurnEvent]:
    """Run a user turn and yield structured chat events."""
    session.mark_activity()
    orchestrator = TurnOrchestrator(session)
    yield from orchestrator.iter_events(prompt, abort=abort)
    session.mark_activity()


def send_user_message(
    session: ChatSession,
    user_input: str,
    *,
    abort: threading.Event | None = None,
    reply_prefix: str = "",
    writer: Callable[[str], None] | None = None,
) -> str:
    """Run a user turn and render events with the session writer."""
    return _deliver_user_message(
        session,
        user_input,
        runner_factory=TurnOrchestrator,
        abort=abort,
        reply_prefix=reply_prefix,
        writer=writer,
    )
