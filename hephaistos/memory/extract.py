"""Memory extraction: pull learned concepts from conversation turns.

After each exchange, this module uses the LLM to extract key concepts
and facts that the user has learned or discussed.  The extracted items
are stored in the armory's memory store to prevent repetition.

Extraction is deliberately conservative:
- Only extract when there's substantial content (not greetings, corrections)
- Only extract facts and concepts, not opinions or guesses
- Always attribute to the source (document name, conversation, etc.)
"""

from __future__ import annotations

import json

from hephaistos.chat.engine import ChatConfig, Conversation, _build_client
from hephaistos.logging import Timer, get_logger
from hephaistos.memory import MemoryStore, save_memory

_log = get_logger("memory.extract")

# Minimum characters in the assistant's response before we bother extracting
_MIN_CONTENT_LENGTH = 100

# Prompt for extraction
_EXTRACTION_SYSTEM_PROMPT = (
    "You are a knowledge extraction assistant. Your job is to identify "
    "concepts, facts, and definitions that the user has learned or discussed "
    "in the conversation below.\n\n"
    "Rules:\n"
    "- Only extract concrete facts, concepts, and definitions.\n"
    "- Do NOT extract opinions, guesses, or uncertain information.\n"
    "- Each entry must have a 'topic' (short label) and 'content' (the fact).\n"
    "- If the conversation doesn't contain substantive learning, return an empty list.\n"
    "- Return ONLY a JSON array, no other text.\n"
    '- Each entry: {"topic": "...", "content": "...", "source": "..."}\n'
    "- Source should be the document name or 'conversation'.\n\n"
    "Example output:\n"
    "Example: "
    '[{"topic": "TCP handshake", '
    '"content": "TCP uses a 3-way handshake: SYN, SYN-ACK, ACK", '
    '"source": "networking_notes.md"}]'
)

_EXTRACTION_USER_TEMPLATE = (
    "Extract learned concepts from this exchange:\n\n"
    "User: {user_message}\n\n"
    "Assistant: {assistant_message}\n\n"
    "Context (sources used): {sources}\n\n"
    "Return a JSON array of learned concepts, or [] if nothing substantive."
)

_MAX_USER_CHARS = 500
_MAX_ASSISTANT_CHARS = 2000


def extract_from_exchange(
    config: ChatConfig,
    user_message: str,
    assistant_message: str,
    sources: str = "",
) -> list[dict[str, str]]:
    """Extract learned concepts from a single exchange.

    Returns a list of dicts with keys: topic, content, source.
    Returns empty list if nothing substantive was found.
    """
    if len(assistant_message) < _MIN_CONTENT_LENGTH:
        return []

    prompt = _EXTRACTION_USER_TEMPLATE.format(
        user_message=user_message[:_MAX_USER_CHARS],
        assistant_message=assistant_message[:_MAX_ASSISTANT_CHARS],
        sources=sources[:200] if sources else "(none)",
    )

    temp = Conversation()
    temp.add("system", _EXTRACTION_SYSTEM_PROMPT)
    temp.add("user", prompt)

    timer = Timer()
    try:
        client = _build_client(config)
        with timer:
            response = client.chat.completions.create(
                model=config.model,
                messages=temp.to_api_messages(),
                max_tokens=1000,
                stream=False,
                temperature=0.1,  # deterministic extraction
            )
        raw = response.choices[0].message.content or "[]"
    except Exception as exc:
        _log.warning(
            "memory extraction failed",
            extra={
                "fields": {
                    "error": str(exc),
                    "latency_ms": timer.ms,
                }
            },
        )
        return []
    try:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
        if raw.endswith("```"):
            raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()

        entries = json.loads(raw)
        if not isinstance(entries, list):
            return []
        valid: list[dict[str, str]] = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            topic = entry.get("topic", "").strip()
            content = entry.get("content", "").strip()
            if not topic or not content:
                continue
            valid.append(
                {
                    "topic": topic[:100],
                    "content": content[:500],
                    "source": entry.get("source", "conversation"),
                }
            )

        _log.info(
            "memory extracted",
            extra={
                "fields": {
                    "entries": len(valid),
                    "latency_ms": timer.ms,
                }
            },
        )
        return valid

    except json.JSONDecodeError:
        _log.warning("memory extraction: invalid JSON response")
        return []


def extract_and_store(
    config: ChatConfig,
    memory: MemoryStore,
    user_message: str,
    assistant_message: str,
    sources: str = "",
) -> int:
    """Extract concepts from an exchange and store them in memory.

    Returns the number of new entries actually added.
    """
    entries = extract_from_exchange(config, user_message, assistant_message, sources)
    if not entries:
        return 0

    added = memory.add_batch(entries, source="conversation", confidence="discussed")
    if added > 0:
        save_memory(memory)
    return added
