"""Non-interactive chat automation services.

This module is deliberately UI-agnostic: callers decide whether events become
plain text, JSONL, logs, or TUI widgets.
"""

from __future__ import annotations

import threading
from collections.abc import Iterator
from dataclasses import asdict

from chat.events import (
    TurnEvent,
)
from chat.orchestrator import TurnOrchestrator
from chat.session import ChatSession


def iter_chat_events(
    session: ChatSession,
    prompt: str,
    *,
    abort: threading.Event | None = None,
) -> Iterator[TurnEvent]:
    session.mark_activity()
    orchestrator = TurnOrchestrator(session)
    yield from orchestrator.iter_events(prompt, abort=abort)
    session.mark_activity()


def event_to_json_object(event: TurnEvent) -> dict[str, object]:
    payload = asdict(event)
    payload["type"] = payload.pop("kind")
    if event.kind == "notice" and not payload.get("metadata"):
        del payload["metadata"]
    return payload
