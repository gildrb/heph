"""Lightweight steering slot for mid-turn user input."""

from __future__ import annotations

import threading

from ai.logging import get_logger

_log = get_logger("hephaion.agent.steering")


class Steering:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._message: str | None = None

    def enqueue(self, message: str) -> None:
        if not message.strip():
            return
        with self._lock:
            self._message = message
        _log.info(
            "steering message stored",
            extra={
                "fields": {
                    "message_len": len(message),
                }
            },
        )

    def drain(self) -> list[str]:
        with self._lock:
            if self._message is None:
                return []
            message = self._message
            self._message = None
        return [message]


SteeringQueue = Steering

__all__ = ["Steering", "SteeringQueue"]
