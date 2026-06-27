from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from ai.runtime import prompt_cache as prompt_cache_mod
from ai.runtime._api_types import ApiMessage
from ai.runtime.prompt_cache import (
    MetricsLogger,
    PromptCacheRequest,
    StablePrefixBuilder,
)
from harness.agent.dispatch import _inject_turn_context
from harness.rag.chunker import Chunk
from harness.rag.context import EvidenceChunk, TurnEvidence


def _request(messages: list[ApiMessage]) -> PromptCacheRequest:
    return StablePrefixBuilder().build_request(messages)


def test_stable_prefix_hash_ignores_dynamic_tail_changes() -> None:
    base: list[ApiMessage] = [
        {"role": "system", "content": "You are a grounded source-grounded assistant."},
        {"role": "system", "content": "Use citations from the provided material."},
        {"role": "user", "content": "Explain integration by parts."},
    ]
    changed_tail: list[ApiMessage] = [
        {"role": "system", "content": "You are a grounded source-grounded assistant."},
        {"role": "system", "content": "Use citations from the provided material."},
        {"role": "user", "content": "Explain Dijkstra's algorithm."},
        {"role": "assistant", "content": "Dijkstra uses a priority queue [E1]."},
    ]

    first = _request(base)
    second = _request(changed_tail)

    assert first.stable_prefix.fingerprint == second.stable_prefix.fingerprint
    assert first.dynamic_tail.fingerprint != second.dynamic_tail.fingerprint
    assert [message["role"] for message in first.stable_prefix.messages] == [
        "system",
        "system",
    ]


def test_dynamic_tail_keeps_summaries_tools_and_nonleading_system_messages() -> None:
    messages: list[ApiMessage] = [
        {"role": "system", "content": "Stable persona."},
        {"role": "user", "content": "First question."},
        {"role": "system", "content": "[Conversation summary] Earlier work."},
        {"role": "tool", "content": "Observed source text."},
        {"role": "assistant", "content": "Answer [E1]."},
    ]

    request = _request(messages)

    assert request.stable_prefix.message_count == 1
    assert [message["role"] for message in request.dynamic_tail.messages] == [
        "user",
        "system",
        "tool",
        "assistant",
    ]
    assert request.messages == messages


def test_summary_first_message_stays_dynamic() -> None:
    messages: list[ApiMessage] = [
        {"role": "system", "content": "[Conversation summary] Previous thread."},
        {"role": "user", "content": "Continue."},
    ]

    request = _request(messages)

    assert request.stable_prefix.message_count == 0
    assert request.dynamic_tail.message_count == 2


def test_evidence_system_message_after_leading_systems_is_stable() -> None:
    messages: list[ApiMessage] = [
        {"role": "system", "content": "Stable persona."},
        {
            "role": "system",
            "content": "Retrieved evidence for this question:\n\n[E1] notes.md (chunk 0)",
        },
        {"role": "user", "content": "Use the evidence."},
    ]

    request = _request(messages)

    assert request.stable_prefix.message_count == 2
    assert request.stable_prefix.messages[1]["content"] == messages[1]["content"]
    assert request.dynamic_tail.messages == ({"role": "user", "content": "Use the evidence."},)


def test_inject_turn_context_places_evidence_in_stable_prefix_zone() -> None:
    chunk = Chunk(
        text="Python supports functions.",
        source="materials/python.md",
        index=0,
        char_start=0,
        char_end=26,
    )
    evidence = TurnEvidence(
        (
            EvidenceChunk(
                evidence_id="E1",
                chunk=chunk,
                score=0.9,
                content="Python supports functions.",
            ),
        )
    )
    messages: list[ApiMessage] = [
        {"role": "system", "content": "Stable persona."},
        {"role": "system", "content": "Stable citation rules."},
        {"role": "user", "content": "Earlier question."},
        {"role": "assistant", "content": "Earlier answer."},
        {"role": "user", "content": "New question."},
    ]

    injected = _inject_turn_context(messages, evidence, None)
    request = _request(injected)

    assert [message["role"] for message in injected[:4]] == [
        "system",
        "system",
        "system",
        "user",
    ]
    assert str(injected[2]["content"]).startswith("Retrieved evidence for this question:")
    assert request.stable_prefix.message_count == 3


def test_metrics_logger_records_cache_structure_without_prompt_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    info = MagicMock()
    monkeypatch.setattr(prompt_cache_mod._log, "info", info)
    request = _request(
        [
            {"role": "system", "content": "Do not log this literal prompt."},
            {"role": "user", "content": "or this user text"},
        ]
    )

    MetricsLogger().record_request(request, model="gpt-test")
    MetricsLogger().record_usage(request, model="gpt-test", cached_prompt_tokens=128)

    request_fields = info.call_args_list[0].kwargs["extra"]["fields"]
    usage_fields = info.call_args_list[1].kwargs["extra"]["fields"]
    assert request_fields["model"] == "gpt-test"
    assert request_fields["stable_prefix_messages"] == 1
    assert request_fields["dynamic_tail_messages"] == 1
    assert "Do not log" not in str(request_fields)
    assert usage_fields["cached_prompt_tokens"] == 128
