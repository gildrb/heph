"""Memory workflow helpers used by chat orchestration."""

from __future__ import annotations

import threading

from ai.logging import get_logger
from ai.runtime import ChatConfig

from harness.memory import MemoryStore
from harness.memory.extract import extract_and_store

_log = get_logger("harness.memory.workflow")


def schedule_memory_extraction(
    *,
    config: ChatConfig,
    memory: MemoryStore | None,
    user_input: str,
    reply: str,
    evidence: str,
) -> None:
    if memory is None or not (user_input.strip() or reply.strip()):
        return

    def _bg_extract() -> None:
        try:
            added = extract_and_store(config, memory, user_input, reply, evidence)
            if added:
                _log.info(
                    "memory updated",
                    extra={"fields": {"new_entries": added}},
                )
        except Exception:
            _log.warning("memory extraction failed", exc_info=True)

    try:
        threading.Thread(
            target=_bg_extract,
            name="harness-mem-extract",
            daemon=True,
        ).start()
    except Exception:
        _log.warning("memory extraction failed", exc_info=True)


__all__ = ["schedule_memory_extraction"]
