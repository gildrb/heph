"""Rendered chat-message delivery through a supplied turn runner."""

from __future__ import annotations

import sys
import threading
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Protocol

from ai.runtime.errors import RetryConfig

from harness.chat.events import TurnEvent, render_turn_event
from harness.chat.session_persistence import save_dirty_session_if_needed

if TYPE_CHECKING:
    from harness.chat.session import ChatSession


class TurnRunner(Protocol):
    last_reply: str

    def iter_events(
        self,
        user_input: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[TurnEvent]: ...


class TurnRunnerFactory(Protocol):
    def __call__(self, session: ChatSession, retry: RetryConfig | None = None) -> TurnRunner: ...


def send_user_message(
    session: ChatSession,
    user_input: str,
    *,
    runner_factory: TurnRunnerFactory,
    abort: threading.Event | None = None,
    reply_prefix: str = "",
    writer: Callable[[str], None] | None = None,
) -> str:
    """Run one user turn and mirror rendered events to a writer."""
    session.mark_activity()
    runner = runner_factory(session)
    write = _session_writer(writer)
    _write_rendered_turn_events(
        runner.iter_events(user_input, abort=abort),
        reply_prefix=reply_prefix,
        write=write,
    )
    if runner.last_reply:
        write("\n")
    session.mark_activity()
    save_dirty_session_if_needed(session)
    return runner.last_reply


def _write_rendered_turn_events(
    events: Iterator[TurnEvent],
    *,
    reply_prefix: str,
    write: Callable[[str], None],
) -> None:
    printed_prefix = False
    for event in events:
        rendered = render_turn_event(event)
        if not rendered:
            continue
        if reply_prefix and not printed_prefix:
            write(reply_prefix)
            printed_prefix = True
        write(rendered)


def _session_writer(writer: Callable[[str], None] | None) -> Callable[[str], None]:
    if writer is not None:
        return writer

    def _write_stdout(text: str) -> None:
        sys.stdout.write(text)
        sys.stdout.flush()

    return _write_stdout
