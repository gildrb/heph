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
import os
from dataclasses import replace
from typing import TypedDict

from openai.types.chat import ChatCompletion

from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.chat.engine import (
    ChatConfig,
    Conversation,
    build_client,
    to_chat_completion_messages,
)
from hephaistos.logging import Timer, get_logger
from hephaistos.memory import MemoryStore, save_memory
from hephaistos.memory.supermemory import SupermemoryStore

_log = get_logger("memory.extract")
_EXTRACTION_MODEL_ENV = "HEPHAISTOS_EXTRACTION_MODEL"

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
    "User: %s\n\n"
    "Assistant: %s\n\n"
    "Context (sources used): %s\n\n"
    "Return a JSON array of learned concepts, or [] if nothing substantive."
)

_MAX_USER_CHARS = 500
_MAX_ASSISTANT_CHARS = 2000


class ExtractedConcept(TypedDict):
    topic: str
    content: str
    source: str


def extract_from_exchange(
    config: ChatConfig,
    user_message: str,
    assistant_message: str,
    sources: str = "",
) -> list[ExtractedConcept]:
    """Extract learned concepts from a single exchange.

    Returns a list of dicts with keys: topic, content, source.
    Returns empty list if nothing substantive was found.
    """
    if len(assistant_message) < _MIN_CONTENT_LENGTH:
        return []
    extraction_model = os.environ.get(_EXTRACTION_MODEL_ENV, "").strip()
    effective_config = replace(config, model=extraction_model) if extraction_model else config

    prompt = _EXTRACTION_USER_TEMPLATE % (
        user_message[:_MAX_USER_CHARS],
        assistant_message[:_MAX_ASSISTANT_CHARS],
        sources[:200] if sources else "(none)",
    )

    temp = Conversation()
    temp.add("system", _EXTRACTION_SYSTEM_PROMPT)
    temp.add("user", prompt)

    timer = Timer()
    try:
        client = build_client(effective_config)
        with timer:
            response: ChatCompletion = client.chat.completions.create(
                model=effective_config.model,
                messages=to_chat_completion_messages(temp.to_api_messages()),
                max_tokens=1000,
                stream=False,
                temperature=0.1,  # deterministic extraction
            )
        message_content = response.choices[0].message.content
        raw = message_content if isinstance(message_content, str) and message_content else "[]"
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
        if not is_object_list(entries):
            return []
        valid: list[ExtractedConcept] = []
        for entry in entries:
            if not is_string_mapping(entry):
                continue
            topic = str(entry.get("topic", "")).strip()
            content = str(entry.get("content", "")).strip()
            if not topic or not content:
                continue
            valid.append(
                {
                    "topic": topic[:100],
                    "content": content[:500],
                    "source": str(entry.get("source", "conversation")),
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
    if isinstance(memory, SupermemoryStore):
        memory.add_batch_to_profile(entries, source="conversation", confidence="discussed")
    if added > 0:
        save_memory(memory)
    return added
