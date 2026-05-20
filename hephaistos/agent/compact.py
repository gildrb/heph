"""Context compaction: three-layer compression for infinite sessions.

Layer 1 (micro_compact): Replace old tool results with placeholders.
    Runs silently before every LLM turn.

Layer 2 (auto_compact): When token count exceeds a threshold, save the
    full transcript to disk and ask the LLM to produce a summary.

Layer 3 (compact tool): The agent explicitly calls the ``compact`` tool,
    which triggers the same summarisation as Layer 2.

Nothing is truly lost — full transcripts are persisted under
``<workspace>/.hephaistos/transcripts/`` as JSONL files.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.logging import get_logger
from hephaistos.rag.context import estimate_tokens
from hephaistos.runtime import (
    ApiMessage,
    ChatConfig,
    Conversation,
    build_client,
    to_chat_completion_messages,
)

if TYPE_CHECKING:
    from openai.types.chat import ChatCompletion

_log = get_logger("agent.compact")

KEEP_RECENT: int = 3  # tool results left untouched by micro_compact
KEEP_RECENT_EXCHANGES: int = 2  # complete exchanges preserved verbatim by auto_compact
PLACEHOLDER_THRESHOLD: int = 100  # only replace results longer than this (chars)
TOKEN_THRESHOLD: int = 50_000  # auto_compact trigger
TRANSCRIPTS_DIR: str = ".hephaistos/transcripts"
_COMPACTION_CACHE_DIR: str = ".hephaistos/compaction_cache"


def estimate_messages_tokens(messages: list[ApiMessage]) -> int:
    total = 0
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif is_object_list(content):
            for part in content:
                if not is_string_mapping(part):
                    continue
                text = part.get("text", "") or part.get("content", "")
                total += estimate_tokens(str(text))
        for tc in msg.get("tool_calls", []):
            fn = tc.get("function", {})
            total += estimate_tokens(fn.get("name", ""))
            total += estimate_tokens(fn.get("arguments", ""))
    return total


def micro_compact(messages: list[ApiMessage], *, keep_recent: int = KEEP_RECENT) -> int:
    """Replace old tool results with short placeholders.

    Operates **in-place** on *messages*.  Returns the number of results
    that were replaced.
    """
    tool_result_indices = [i for i, msg in enumerate(messages) if msg.get("role") == "tool"]

    if len(tool_result_indices) <= keep_recent:
        return 0

    to_replace = tool_result_indices[:-keep_recent]
    replaced = 0

    for idx in to_replace:
        content = messages[idx]["content"]
        if isinstance(content, str) and len(content) > PLACEHOLDER_THRESHOLD:
            call_id = messages[idx].get("tool_call_id", "")
            tool_name = "tool"
            found_tool_name = False
            for previous in range(idx - 1, -1, -1):
                for tool_call in messages[previous].get("tool_calls", []):
                    if tool_call.get("id") == call_id:
                        tool_name = tool_call.get("function", {}).get("name", "tool")
                        found_tool_name = True
                        break
                if found_tool_name:
                    break
            messages[idx]["content"] = f"[Previous: used {tool_name}]"
            replaced += 1

    if replaced:
        _log.info("micro_compact", extra={"fields": {"replaced": replaced}})

    return replaced


def auto_compact(
    messages: list[ApiMessage],
    config: ChatConfig,
    workspace: Path,
    *,
    keep_recent_exchanges: int = KEEP_RECENT_EXCHANGES,
) -> list[ApiMessage]:
    """Save transcript to disk, summarise older turns, keep recent ones verbatim.

    The most recent N exchanges (user + assistant + tool messages) are
    preserved verbatim so the LLM can still reference them precisely.
    Only older turns are summarized via a separate LLM call.

    If summarisation fails (network error, API key missing, etc.) the
    original messages are returned unchanged and the error is logged.
    """
    transcript_dir = workspace / TRANSCRIPTS_DIR
    transcript_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = transcript_dir / f"transcript_{int(time.time())}.jsonl"
    with transcript_path.open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(msg, default=str, ensure_ascii=False) + "\n" for msg in messages)

    system_msgs = [m for m in messages if m.get("role") == "system"]
    non_system = [m for m in messages if m.get("role") != "system"]

    user_indices = [i for i, m in enumerate(non_system) if m.get("role") == "user"]

    keep_from = 0
    if len(user_indices) > keep_recent_exchanges:
        keep_from = user_indices[-keep_recent_exchanges]

    old_messages = non_system[:keep_from]
    recent_messages = non_system[keep_from:]

    if not old_messages:
        return messages

    serialized = json.dumps(old_messages, default=str, ensure_ascii=False, sort_keys=True)
    messages_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    cache_path = workspace / _COMPACTION_CACHE_DIR / f"{messages_hash}.txt"
    summary = cache_path.read_text(encoding="utf-8") if cache_path.is_file() else None

    try:
        if summary is None:
            prompt_serialized = serialized
            if len(prompt_serialized) > 80_000:
                # Truncate at the last newline boundary to avoid splitting
                # mid-escape-sequence (e.g. "\u00" -> "\u0").
                cut = prompt_serialized.rfind("\n", 0, 80_000)
                if cut == -1:
                    cut = 80_000
                prompt_serialized = prompt_serialized[:cut] + "\n... [truncated]"

            summary_prompt = (
                "Summarize the following conversation for continuity. "
                "Preserve key facts, decisions, file paths, code changes, "
                "and any context needed to continue working.\n\n"
                f"{prompt_serialized}"
            )

            temp = Conversation()
            temp.add(
                "system",
                "You are a helpful assistant that summarizes conversations concisely.",
            )
            temp.add("user", summary_prompt)

            client = build_client(config)
            response: ChatCompletion = client.chat.completions.create(
                model=config.model,
                messages=to_chat_completion_messages(temp.to_api_messages()),
                max_tokens=2000,
                stream=False,
            )
            message_content = response.choices[0].message.content
            if isinstance(message_content, str) and message_content.strip():
                summary = message_content
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(summary, encoding="utf-8")
            else:
                summary = "(summary unavailable)"
    except Exception as exc:
        _log.error(
            "auto_compact summarisation failed",
            extra={
                "fields": {
                    "error": str(exc),
                }
            },
        )
        return messages

    compressed: list[ApiMessage] = [
        *system_msgs,
        {"role": "user", "content": f"[Earlier conversation summary]\n\n{summary}"},
        *recent_messages,
    ]

    _log.info(
        "auto_compact complete",
        extra={
            "fields": {
                "before_messages": len(messages),
                "after_messages": len(compressed),
                "before_tokens": estimate_messages_tokens(messages),
                "after_tokens": estimate_messages_tokens(compressed),
                "summary_len": len(summary),
                "kept_exchanges": len(user_indices[-keep_recent_exchanges:])
                if len(user_indices) > keep_recent_exchanges
                else len(user_indices),
            }
        },
    )

    return compressed
