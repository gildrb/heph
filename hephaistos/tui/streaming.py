"""Streaming turn adapter helpers.

Named after Codex's focused TUI streaming modules: chat/session workflow stays in
`chat`, while this adapter converts chat events into UI callbacks.
"""

from __future__ import annotations

from collections.abc import Callable
from threading import Event
from typing import TYPE_CHECKING

from hephaistos.chat.events import AssistantDeltaEvent, NoticeEvent, ToolCallEvent, ToolResultEvent

if TYPE_CHECKING:
    from hephaistos.chat.session import ChatSession


def run_tui_turn(
    session: ChatSession,
    user_input: str,
    abort_event: Event,
    *,
    on_reply: Callable[[str], None],
    on_notice: Callable[[str], None],
    on_error: Callable[[str], None],
    on_finish: Callable[[], None],
) -> None:
    """Run one chat turn and report UI-ready events through callbacks."""
    from hephaistos.chat.automation import iter_chat_events
    from hephaistos.runtime import (
        EngineError,
        StreamRecoveryError,
        is_network_error,
        offline_message,
    )

    parts: list[str] = []
    try:
        for event in iter_chat_events(session, user_input, abort=abort_event):
            if isinstance(event, AssistantDeltaEvent):
                parts.append(event.delta)
            elif isinstance(event, ToolCallEvent):
                on_notice(event.display)
            elif isinstance(event, ToolResultEvent):
                on_notice(event.summary)
            elif isinstance(event, NoticeEvent):
                on_notice(event.message)
        reply = "".join(parts).strip()
        if reply:
            on_reply(reply)
    except (StreamRecoveryError, EngineError) as exc:
        provider = session.config.provider_slug or "the provider"
        if is_network_error(exc):
            on_notice(offline_message(provider))
        else:
            on_error(str(exc))
    finally:
        on_finish()
