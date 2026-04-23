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

import json
import time
from pathlib import Path

from openai.types.chat import ChatCompletion

from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.chat._api_types import ApiMessage
from hephaistos.chat.engine import (
    ChatConfig,
    Conversation,
    build_client,
    to_chat_completion_messages,
)
from hephaistos.harness.rag.context import estimate_tokens
from hephaistos.logging import get_logger

_log = get_logger("harness.compact")

KEEP_RECENT: int = 3  # tool results left untouched by micro_compact
KEEP_RECENT_EXCHANGES: int = 2  # complete exchanges preserved verbatim by auto_compact
PLACEHOLDER_THRESHOLD: int = 100  # only replace results longer than this (chars)
TOKEN_THRESHOLD: int = 50_000  # auto_compact trigger
TRANSCRIPTS_DIR: str = ".hephaistos/transcripts"


def estimate_messages_tokens(messages: list[ApiMessage]) -> int:
    """Rough token estimate for a list of API-format messages."""
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
            tool_name = _find_tool_name(messages, idx)
            messages[idx]["content"] = f"[Previous: used {tool_name}]"
            replaced += 1

    if replaced:
        _log.info("micro_compact", extra={"fields": {"replaced": replaced}})

    return replaced


def _find_tool_name(messages: list[ApiMessage], tool_result_idx: int) -> str:
    """Walk backwards to find the tool-call name that produced a result."""
    call_id = messages[tool_result_idx].get("tool_call_id", "")
    for i in range(tool_result_idx - 1, -1, -1):
        for tc in messages[i].get("tool_calls", []):
            if tc.get("id") == call_id:
                return tc.get("function", {}).get("name", "tool")
    return "tool"


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
    _save_transcript(messages, workspace)

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

    try:
        serialized = json.dumps(old_messages, default=str, ensure_ascii=False)
        if len(serialized) > 80_000:
            # Truncate at the last newline boundary to avoid splitting
            # mid-escape-sequence (e.g. "\u00" -> "\u0").
            cut = serialized.rfind("\n", 0, 80_000)
            if cut == -1:
                cut = 80_000
            serialized = serialized[:cut] + "\n... [truncated]"

        summary_prompt = (
            "Summarize the following conversation for continuity. "
            "Preserve key facts, decisions, file paths, code changes, "
            "and any context needed to continue working.\n\n"
            f"{serialized}"
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
        summary = (
            message_content
            if isinstance(message_content, str) and message_content
            else ("(summary unavailable)")
        )
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


def _save_transcript(messages: list[ApiMessage], workspace: Path) -> Path:
    """Persist messages as JSONL under ``<workspace>/.transcripts/``."""
    transcript_dir = workspace / TRANSCRIPTS_DIR
    transcript_dir.mkdir(parents=True, exist_ok=True)
    path = transcript_dir / f"transcript_{int(time.time())}.jsonl"
    with path.open("w", encoding="utf-8") as f:
        f.writelines(json.dumps(msg, default=str, ensure_ascii=False) + "\n" for msg in messages)
    return path
