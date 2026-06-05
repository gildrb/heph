"""Tests for token usage tracking, cost estimation, and context budget."""

from __future__ import annotations

from pathlib import Path

import ai.runtime.usage as runtime_usage_module
import chat.usage as usage_module
import pytest
from ai.runtime import ApiMessage, UsagePayload
from chat.usage import (
    ContextBudget,
    SessionUsage,
    TokenUsage,
    _get_pricing,
    estimate_conversation_tokens,
    estimate_message_tokens,
    get_context_window,
    save_usage,
)

# ---------------------------------------------------------------------------
# TokenUsage
# ---------------------------------------------------------------------------


class TestTokenUsage:
    def test_from_api_response_none(self):
        usage = TokenUsage.from_api_response(None)
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_from_api_response_with_data(self):
        payload: UsagePayload = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
        }
        usage = TokenUsage.from_api_response(payload)
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150

    def test_from_api_response_missing_fields(self):
        usage = TokenUsage.from_api_response(UsagePayload())
        assert usage.prompt_tokens == 0
        assert usage.total_tokens == 0

    def test_from_api_response_with_none_values(self):
        payload: UsagePayload = {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
        }
        usage = TokenUsage.from_api_response(payload)
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0


# ---------------------------------------------------------------------------
# SessionUsage
# ---------------------------------------------------------------------------


class TestSessionUsage:
    def test_record_with_usage(self):
        session = SessionUsage()
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        session.record(usage, "gpt-4o-mini")

        assert session.total_prompt_tokens == 100
        assert session.total_completion_tokens == 50
        assert session.total_tokens == 150
        assert session.api_calls == 1
        assert session.total_cost_usd > 0

    def test_record_multiple_calls(self):
        session = SessionUsage()
        session.record(TokenUsage(100, 50, 150), "gpt-4o-mini")
        session.record(TokenUsage(200, 100, 300), "gpt-4o-mini")

        assert session.total_prompt_tokens == 300
        assert session.total_completion_tokens == 150
        assert session.api_calls == 2

    def test_record_free_model(self):
        session = SessionUsage()
        session.record(TokenUsage(1000, 500, 1500), "qwen/qwen3.6-plus:free")
        assert session.total_cost_usd == 0.0

    def test_estimate_from_chars(self):
        session = SessionUsage()
        session.estimate_from_chars(400, 100, "gpt-4o-mini")
        assert session.total_prompt_tokens == 100
        assert session.total_completion_tokens == 25
        assert session.api_calls == 1

    def test_summary(self):
        session = SessionUsage()
        session.record(TokenUsage(100, 50, 150), "gpt-4o-mini")
        s = session.summary()
        assert s["api_calls"] == 1
        assert s["prompt_tokens"] == 100
        assert s["completion_tokens"] == 50
        assert s["total_tokens"] == 150
        assert "cost_usd" in s


# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------


class TestPricing:
    def test_known_model(self):
        prompt, completion = _get_pricing("gpt-4o-mini")
        assert prompt > 0
        assert completion > 0

    def test_free_model(self):
        prompt, completion = _get_pricing("qwen/qwen3.6-plus:free")
        assert prompt == 0.0
        assert completion == 0.0

    def test_unknown_model_returns_default(self):
        prompt, completion = _get_pricing("nonexistent-model-xyz")
        assert prompt > 0
        assert completion > 0

    def test_prefix_match(self):
        prompt, _completion = _get_pricing("gpt-5.4-some-new-variant")
        assert prompt > 0


# ---------------------------------------------------------------------------
# Context window
# ---------------------------------------------------------------------------


class TestContextWindow:
    def test_known_model(self):
        assert get_context_window("gpt-4o") == 128_000

    def test_prefix_match(self):
        cw = get_context_window("gpt-5.4-turbo-extended")
        assert cw >= 128_000

    def test_unknown_model(self):
        cw = get_context_window("totally-unknown-model")
        assert cw == 128_000  # default


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------


class TestTokenEstimation:
    def test_estimate_message_tokens_falls_back_to_char_count(self, monkeypatch):
        monkeypatch.setattr(usage_module, "_encoder", None)

        tokens = estimate_message_tokens("Hello world, this is a test")

        assert tokens == len("Hello world, this is a test") // 4

    def test_estimate_message_tokens_uses_tiktoken_encoder(self, monkeypatch):
        class FakeEncoder:
            def encode(self, content: str) -> list[int]:
                return [1, 2, 3]

        content = "Hello world, this is a test"
        char_estimate = len(content) // 4
        monkeypatch.setattr(usage_module, "_encoder", FakeEncoder())

        tokens = estimate_message_tokens(content)

        assert tokens == 3
        assert tokens != char_estimate

    def test_estimate_message_tokens_matches_tiktoken_when_installed(self):
        if usage_module._encoder is None:
            pytest.skip("tiktoken is not installed")

        content = "antidisestablishmentarianism"

        assert estimate_message_tokens(content) == len(usage_module._encoder.encode(content))
        assert estimate_message_tokens(content) != len(content) // 4

    def test_estimate_conversation_tokens(self):
        messages: list[ApiMessage] = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        tokens = estimate_conversation_tokens(messages)
        # At least the content + overhead per message
        assert tokens > 0

    def test_estimate_conversation_with_tool_calls(self):
        messages: list[ApiMessage] = [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {"function": {"name": "bash", "arguments": '{"command": "ls"}'}},
                ],
            },
            {"role": "tool", "content": "file1.txt\nfile2.txt"},
        ]
        tokens = estimate_conversation_tokens(messages)
        assert tokens > 0


# ---------------------------------------------------------------------------
# ContextBudget
# ---------------------------------------------------------------------------


class TestContextBudget:
    def test_prompt_budget(self):
        budget = ContextBudget(model="gpt-4o", max_tokens=4096)
        assert budget.prompt_budget == budget.context_window - 4096

    def test_tokens_remaining(self):
        budget = ContextBudget(model="gpt-4o", max_tokens=4096)
        messages: list[ApiMessage] = [{"role": "user", "content": "short"}]
        remaining = budget.tokens_remaining(messages)
        assert remaining > 0
        assert remaining < budget.prompt_budget

    def test_compaction_urgency(self, monkeypatch):
        monkeypatch.setattr(runtime_usage_module, "_encoder", None)

        budget = ContextBudget(model="gpt-4o", max_tokens=4096)
        assert budget.compaction_urgency([{"role": "user", "content": "hi"}]) == "none"

        # Push to high urgency (96% of prompt budget in estimated tokens)
        huge = "x" * int(budget.prompt_budget * 4 * 0.96)
        assert budget.compaction_urgency([{"role": "user", "content": huge}]) == "high"


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


class TestUsagePersistence:
    def test_save(self, tmp_path: Path):
        session = SessionUsage()
        session.record(TokenUsage(100, 50, 150), "gpt-4o-mini")

        path = save_usage(tmp_path, "test-session", session)
        assert path is not None
        assert path.exists()
