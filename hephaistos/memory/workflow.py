"""Memory workflow helpers used by chat orchestration."""

from __future__ import annotations

import threading

from hephaistos.logging import get_logger
from hephaistos.memory import MemoryStore
from hephaistos.memory.extract import extract_and_store
from hephaistos.runtime import ChatConfig

_log = get_logger("memory.workflow")


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
            name="hephaistos-mem-extract",
            daemon=True,
        ).start()
    except Exception:
        _log.warning("memory extraction failed", exc_info=True)


__all__ = ["schedule_memory_extraction"]
