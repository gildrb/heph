"""Memory extraction: curate durable armory context from conversation turns."""

from __future__ import annotations

import json
import os
from dataclasses import replace
from typing import TYPE_CHECKING, TypedDict

from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.logging import Timer, get_logger
from hephaistos.memory import MemoryStore, save_memory
from hephaistos.runtime import (
    ChatConfig,
    Conversation,
    build_client,
    stream_reply,
    to_chat_completion_messages,
)

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletion

_log = get_logger("memory.extract")
_EXTRACTION_MODEL_ENV = "HEPHAISTOS_EXTRACTION_MODEL"

_EXTRACTION_SYSTEM_PROMPT = (
    "You curate sparse persistent memory for a local document agent. "
    "Save only durable context that will improve future sessions in this same armory.\n\n"
    "Rules:\n"
    "- Usually return []. Memory is for rare stable facts, not summaries.\n"
    "- Save user preferences, corrections, constraints, and workflow habits.\n"
    "- Save the armory/material purpose when the user states it explicitly.\n"
    "- Save stable document-set intent, e.g. exam prep, thesis review, client research.\n"
    "- If the armory is clearly domain-specific, save that domain/purpose compactly.\n"
    "- If the armory is broad or mixed-topic, save only that it is broad/mixed; "
    "do not favor one topic.\n"
    "- Do NOT save task progress, generic concepts, answer content, or source facts.\n"
    "- Do NOT infer an armory purpose from one retrieved topic unless the user confirms it.\n"
    "- Do NOT save guesses, uncertain inferences, or facts copied from retrieved material.\n"
    "- Each entry must have a short 'topic', compact 'content', and 'source'.\n"
    "- Return ONLY a JSON array, no other text.\n"
    '- Each entry: {"topic": "...", "content": "...", "source": "..."}\n'
    "- Source should be 'conversation' unless the user names a stable "
    "project/document purpose.\n\n"
    "Example output:\n"
    "Example: "
    '[{"topic": "answer style", '
    '"content": "User prefers blunt, concise answers without emoji.", '
    '"source": "conversation"}]'
)

_EXTRACTION_USER_TEMPLATE = (
    "Curate durable armory memory from this exchange:\n\n"
    "User: %s\n\n"
    "Assistant: %s\n\n"
    "Context (sources used): %s\n\n"
    "Return [] unless this contains a stable preference, correction, armory purpose, "
    "or durable material-use intent."
)

_MAX_USER_CHARS = 500
_MAX_ASSISTANT_CHARS = 2000


class ExtractedConcept(TypedDict):
    topic: str
    content: str
    source: str


def _effective_extraction_config(config: ChatConfig) -> ChatConfig:
    extraction_model = os.environ.get(_EXTRACTION_MODEL_ENV, "").strip()
    return replace(config, model=extraction_model) if extraction_model else config


def _extraction_prompt(user_message: str, assistant_message: str, sources: str) -> str:
    return _EXTRACTION_USER_TEMPLATE % (
        user_message[:_MAX_USER_CHARS],
        assistant_message[:_MAX_ASSISTANT_CHARS],
        sources[:200] if sources else "(none)",
    )


def _extraction_conversation(prompt: str) -> Conversation:
    conversation = Conversation()
    conversation.add("system", _EXTRACTION_SYSTEM_PROMPT)
    conversation.add("user", prompt)
    return conversation


def _run_extraction_model(config: ChatConfig, conversation: Conversation, timer: Timer) -> str:
    if config.provider_slug == "openai-codex":
        with timer:
            return "".join(stream_reply(config, conversation)).strip() or "[]"
    client = build_client(config)
    with timer:
        response: ChatCompletion = client.chat.completions.create(
            model=config.model,
            messages=to_chat_completion_messages(conversation.to_api_messages()),
            max_tokens=1000,
            stream=False,
            temperature=0.1,  # deterministic extraction
        )
    message_content = response.choices[0].message.content
    return message_content if isinstance(message_content, str) and message_content else "[]"


def _strip_json_fence(raw: str) -> str:
    stripped = raw.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[-1]
    if stripped.endswith("```"):
        stripped = stripped.rsplit("```", 1)[0]
    return stripped.strip()


def _concept_from_entry(entry: object) -> ExtractedConcept | None:
    if not is_string_mapping(entry):
        return None
    topic = str(entry.get("topic", "")).strip()
    content = str(entry.get("content", "")).strip()
    if not topic or not content:
        return None
    return {
        "topic": topic[:100],
        "content": content[:500],
        "source": str(entry.get("source", "conversation")),
    }


def _parse_extracted_concepts(raw: str) -> list[ExtractedConcept] | None:
    try:
        entries = json.loads(_strip_json_fence(raw))
    except json.JSONDecodeError:
        _log.warning("memory extraction: invalid JSON response")
        return None
    if not is_object_list(entries):
        return []
    return [concept for entry in entries if (concept := _concept_from_entry(entry)) is not None]


def extract_from_exchange(
    config: ChatConfig,
    user_message: str,
    assistant_message: str,
    sources: str = "",
) -> list[ExtractedConcept]:
    timer = Timer()
    effective_config = _effective_extraction_config(config)
    prompt = _extraction_prompt(user_message, assistant_message, sources)
    conversation = _extraction_conversation(prompt)
    try:
        raw = _run_extraction_model(effective_config, conversation, timer)
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

    valid = _parse_extracted_concepts(raw)
    if valid is None:
        return []
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


def extract_and_store(
    config: ChatConfig,
    memory: MemoryStore,
    user_message: str,
    assistant_message: str,
    sources: str = "",
) -> int:
    entries = extract_from_exchange(config, user_message, assistant_message, sources)
    if not entries:
        return 0

    added = memory.add_batch(entries, source="conversation", confidence="discussed")
    if added > 0:
        save_memory(memory)
    return added
