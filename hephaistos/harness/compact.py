"""Context compaction: three-layer compression for infinite sessions.

Layer 1 (micro_compact): Replace old tool results with placeholders.
    Runs silently before every LLM turn.

Layer 2 (auto_compact): When token count exceeds a threshold, save the
    full transcript to disk and ask the LLM to produce a summary.

Layer 3 (compact tool): The agent explicitly calls the ``compact`` tool,
    which triggers the same summarisation as Layer 2.

Nothing is truly lost — full transcripts are persisted under
``<workspace>/.transcripts/`` as JSONL files.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from hephaistos.chat.engine import ChatConfig, Conversation, _build_client
from hephaistos.harness.rag.context import estimate_tokens
from hephaistos.logging import get_logger

_log = get_logger("harness.compact")

# ---------------------------------------------------------------------------
# Tunables (module-level so tests / callers can override)
# ---------------------------------------------------------------------------

KEEP_RECENT: int = 3  # tool results left untouched by micro_compact
PLACEHOLDER_THRESHOLD: int = 100  # only replace results longer than this (chars)
TOKEN_THRESHOLD: int = 50_000  # auto_compact trigger
TRANSCRIPTS_DIR: str = ".transcripts"


# ---------------------------------------------------------------------------
# Token estimation for message lists
# ---------------------------------------------------------------------------


def estimate_messages_tokens(messages: list[dict]) -> int:
    """Rough token estimate for a list of API-format messages."""
    total = 0
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            # Structured content blocks from multimodal/chat APIs
            for part in content:
                if isinstance(part, dict):
                    text = part.get("text", "") or part.get("content", "")
                    total += estimate_tokens(str(text))
        # tool_calls in assistant messages
        for tc in msg.get("tool_calls", []):
            fn = tc.get("function", {})
            total += estimate_tokens(fn.get("name", ""))
            total += estimate_tokens(fn.get("arguments", ""))
    return total


# ---------------------------------------------------------------------------
# Layer 1: micro_compact
# ---------------------------------------------------------------------------


def micro_compact(messages: list[dict], *, keep_recent: int = KEEP_RECENT) -> int:
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
        content = messages[idx].get("content", "")
        if len(content) > PLACEHOLDER_THRESHOLD:
            tool_name = _find_tool_name(messages, idx)
            messages[idx]["content"] = f"[Previous: used {tool_name}]"
            replaced += 1

    if replaced:
        _log.info("micro_compact", extra={"fields": {"replaced": replaced}})

    return replaced


def _find_tool_name(messages: list[dict], tool_result_idx: int) -> str:
    """Walk backwards to find the tool-call name that produced a result."""
    call_id = messages[tool_result_idx].get("tool_call_id", "")
    for i in range(tool_result_idx - 1, -1, -1):
        for tc in messages[i].get("tool_calls", []):
            if tc.get("id") == call_id:
                return tc.get("function", {}).get("name", "tool")
    return "tool"


# ---------------------------------------------------------------------------
# Layer 2 & 3: auto_compact (also used by the manual compact tool)
# ---------------------------------------------------------------------------


def auto_compact(
    messages: list[dict],
    config: ChatConfig,
    workspace: Path,
) -> list[dict]:
    """Save transcript to disk, summarise via LLM, return compressed list.

    If summarisation fails (network error, API key missing, etc.) the
    original messages are returned unchanged and the error is logged.
    """
    # --- Save full transcript for recovery ---
    _save_transcript(messages, workspace)

    try:
        # --- Build summarisation prompt ---
        serialized = json.dumps(messages, default=str, ensure_ascii=False)
        if len(serialized) > 80_000:
            serialized = serialized[:80_000] + "\n... [truncated]"

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

        client = _build_client(config)
        response = client.chat.completions.create(
            model=config.model,
            messages=temp.to_api_messages(),
            max_tokens=2000,
            stream=False,
        )
        summary = response.choices[0].message.content or "(summary unavailable)"
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

    # --- Build compressed message list ---
    system_msgs = [m for m in messages if m.get("role") == "system"]
    compressed = [*system_msgs, {"role": "user", "content": f"[Compressed]\n\n{summary}"}]

    _log.info(
        "auto_compact complete",
        extra={
            "fields": {
                "before_messages": len(messages),
                "after_messages": len(compressed),
                "before_tokens": estimate_messages_tokens(messages),
                "after_tokens": estimate_messages_tokens(compressed),
                "summary_len": len(summary),
            }
        },
    )

    return compressed


def _save_transcript(messages: list[dict], workspace: Path) -> Path:
    """Persist messages as JSONL under ``<workspace>/.transcripts/``."""
    transcript_dir = workspace / TRANSCRIPTS_DIR
    transcript_dir.mkdir(parents=True, exist_ok=True)
    path = transcript_dir / f"transcript_{int(time.time())}.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        for msg in messages:
            f.write(json.dumps(msg, default=str, ensure_ascii=False) + "\n")
    return path
