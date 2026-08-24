"""Shared support helpers for the agent model/tool dispatch loop."""

from __future__ import annotations

import threading
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

from ai.logging import Timer, get_logger
from ai.runtime._api_types import ApiMessage, UsagePayload
from ai.runtime.config import ChatConfig
from ai.runtime.conversation import Conversation
from ai.runtime.events import NoticeEvent, TurnCompleteEvent, TurnEvent
from ai.runtime.messages import api_content_text
from ai.runtime.prompt_cache import StablePrefixBuilder
from ai.runtime.usage import ContextBudget, SessionUsage, TokenUsage

from harness.agent.compact import auto_compact, estimate_messages_tokens
from harness.agent.model_stream import ModelStreamState
from harness.agent.steering import Steering
from harness.agent.tool_registry import ToolRegistry
from harness.rag.context import TurnEvidence

_log = get_logger("harness.agent.dispatch")


@dataclass(slots=True)
class AgentLoopState:
    api_messages: list[ApiMessage]
    loop_timer: Timer
    budget: ContextBudget
    tool_call_counts: dict[str, int]


def _sync_conversation(conversation: Conversation, api_messages: list[ApiMessage]) -> None:
    """Rebuild *conversation* messages from the compacted API messages.

    The full ``api_messages`` list stays authoritative for tool messages.
    Tool-call-only assistant turns are mirrored with ``"[tool calls]"``.
    """
    conversation.messages.clear()
    for msg in api_messages:
        if msg.get("role") not in {"system", "user", "assistant", "tool"}:
            continue
        if msg.get("role") == "assistant" and not msg.get("content") and not msg.get("tool_calls"):
            continue
        conversation.add_api_message(msg)


def _inject_turn_context(
    messages: list[ApiMessage],
    turn_evidence: TurnEvidence | None,
    extra_system_prompt: str | None,
) -> list[ApiMessage]:
    """Build a copy of *messages* with ephemeral turn context injected."""
    inserts: list[ApiMessage] = []
    if extra_system_prompt:
        inserts.append({"role": "system", "content": extra_system_prompt})
    if turn_evidence:
        rendered = turn_evidence.render()
        if rendered:
            inserts.append({"role": "system", "content": rendered})
    if not inserts:
        return messages
    msgs = list(messages)
    insert_at = StablePrefixBuilder().build(msgs).message_count
    for pos, insert in enumerate(inserts):
        msgs.insert(insert_at + pos, insert)
    return msgs


def _record_usage(
    usage: SessionUsage | None,
    stream_usage: UsagePayload | None,
    api_messages: list[ApiMessage],
    text: str,
    model: str,
) -> None:
    if usage is None:
        return
    if stream_usage:
        usage.record(TokenUsage.from_api_response(stream_usage), model)
        return
    prompt_chars = sum(len(api_content_text(message["content"])) for message in api_messages)
    usage.estimate_from_chars(prompt_chars, len(text), model)


def _drain_steering_events(
    steering: Steering | None,
    api_messages: list[ApiMessage],
    conversation: Conversation,
    *,
    turn_idx: int | None = None,
) -> Iterator[NoticeEvent]:
    if steering is None:
        return
    for message in steering.drain():
        api_messages.append({"role": "user", "content": message})
        conversation.add("user", message)
        yield NoticeEvent(f"Steering: {message[:100]}", code="steering")
        if turn_idx is not None:
            _log.info(
                "steering message injected",
                extra={"fields": {"message_len": len(message), "turn": turn_idx}},
            )


def _dry_run_events(
    config: ChatConfig,
    api_messages: list[ApiMessage],
    registry: ToolRegistry,
    budget: ContextBudget,
    loop_timer: Timer,
) -> Iterator[TurnEvent]:
    tokens_remaining = budget.tokens_remaining(api_messages)
    yield NoticeEvent(
        (
            "Dry run: skipped model streaming and tool execution "
            f"({len(registry.schemas)} tool schemas available)."
        ),
        code="dry_run",
    )
    yield TurnCompleteEvent(
        full_text="",
        turn_index=0,
        latency_ms=loop_timer.ms,
        finish_reason="dry_run",
        tokens_remaining=tokens_remaining,
    )
    _log.info(
        "agent_loop dry_run complete",
        extra={
            "fields": {
                "model": config.model,
                "message_count": len(api_messages),
                "tool_schema_count": len(registry.schemas),
                "tokens_remaining": tokens_remaining,
            }
        },
    )


def _context_warning_events(
    budget: ContextBudget,
    api_messages: list[ApiMessage],
    *,
    turn_idx: int,
) -> Iterator[NoticeEvent]:
    urgency = budget.compaction_urgency(api_messages)
    if urgency not in ("medium", "high"):
        return
    remaining = budget.tokens_remaining(api_messages)
    yield NoticeEvent(
        (
            f"Warning: context window {remaining} tokens remaining "
            f"({urgency} urgency). Consider /compact."
        ),
        code="context_warning",
    )
    _log.warning(
        "context budget low",
        extra={
            "fields": {
                "remaining": remaining,
                "urgency": urgency,
                "turn": turn_idx,
            }
        },
    )


def _final_response_events(
    *,
    config: ChatConfig,
    conversation: Conversation,
    api_messages: list[ApiMessage],
    collected_text: str,
    stream_state: ModelStreamState,
    budget: ContextBudget,
    loop_timer: Timer,
    turn_idx: int,
    usage: SessionUsage | None,
    steering: Steering | None,
) -> Iterator[TurnEvent]:
    _record_usage(usage, stream_state.stream_usage, api_messages, collected_text, config.model)
    api_messages.append({"role": "assistant", "content": collected_text})
    conversation.add("assistant", collected_text)
    tokens_remaining = budget.tokens_remaining(api_messages)
    yield from _drain_steering_events(steering, api_messages, conversation)
    _log.info(
        "agent_loop complete",
        extra={
            "fields": {
                "model": config.model,
                "turn": turn_idx,
                "latency_ms": loop_timer.ms,
                "text_len": len(collected_text),
                "finish_reason": stream_state.finish_reason,
                "tokens_remaining": tokens_remaining,
            }
        },
    )
    yield TurnCompleteEvent(
        full_text=collected_text,
        turn_index=turn_idx,
        latency_ms=loop_timer.ms,
        finish_reason=stream_state.finish_reason,
        tokens_remaining=tokens_remaining,
    )


def _prepare_llm_messages(
    *,
    config: ChatConfig,
    conversation: Conversation,
    workspace: Path,
    api_messages: list[ApiMessage],
    budget: ContextBudget,
    turn_evidence: TurnEvidence | None,
    extra_system_prompt: str | None,
) -> tuple[list[ApiMessage], NoticeEvent | None]:
    llm_messages = _inject_turn_context(api_messages, turn_evidence, extra_system_prompt)
    compaction_threshold = int(budget.prompt_budget * 0.75)
    if estimate_messages_tokens(llm_messages) <= compaction_threshold:
        return llm_messages, None
    notice = NoticeEvent(
        "Auto-compacting conversation (context threshold reached)...",
        code="auto_compact",
    )
    api_messages[:] = auto_compact(api_messages, config, workspace)
    _sync_conversation(conversation, api_messages)
    return _inject_turn_context(api_messages, turn_evidence, extra_system_prompt), notice


def _new_loop_state(config: ChatConfig, conversation: Conversation) -> AgentLoopState:
    api_messages = list(conversation.to_api_messages())
    return AgentLoopState(
        api_messages=api_messages,
        loop_timer=Timer(),
        budget=ContextBudget(model=config.model, max_tokens=config.max_tokens),
        tool_call_counts={},
    )


def _restricted_tool_registry(
    registry: ToolRegistry,
    allowed_names: Sequence[str] | None,
) -> ToolRegistry:
    if allowed_names is None:
        return registry
    allowed = frozenset(allowed_names)
    restricted = ToolRegistry()
    for spec in registry.specs:
        if spec.name in allowed:
            restricted.register(spec)
    return restricted


def _log_agent_loop_start(config: ChatConfig, state: AgentLoopState, max_turns: int) -> None:
    _log.info(
        "agent_loop start",
        extra={
            "fields": {
                "model": config.model,
                "message_count": len(state.api_messages),
                "max_turns": max_turns,
                "context_window": state.budget.context_window,
                "prompt_budget": state.budget.prompt_budget,
                "tokens_remaining": state.budget.tokens_remaining(state.api_messages),
            }
        },
    )


def _abort_requested(
    abort: threading.Event | None,
    *,
    turn_idx: int,
    loop_timer: Timer,
) -> bool:
    if abort is None or not abort.is_set():
        return False
    _log.info(
        "agent_loop aborted",
        extra={
            "fields": {
                "turn": turn_idx,
                "latency_ms": loop_timer.ms,
            }
        },
    )
    return True
