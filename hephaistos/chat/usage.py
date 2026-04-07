"""Token usage tracking, cost estimation, and context window budget management.

Tracks prompt/completion tokens per session from API responses, estimates
cost based on model pricing, and manages the context window budget so
the agent knows how much room it has left.

Token counts come from:
  1. The ``usage`` field in OpenAI-compatible streaming chunk responses
     (available on the final chunk with ``finish_reason`` set).
  2. Fallback character-based estimation (4 chars ≈ 1 token).

Cost estimates use a model pricing table that can be extended via env vars.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from hephaistos.logging import get_logger

_log = get_logger("chat.usage")


# ---------------------------------------------------------------------------
# Model pricing (USD per 1K tokens)
# ---------------------------------------------------------------------------

# Prices are approximate and should be updated periodically.
# Format: (prompt_price_per_1k, completion_price_per_1k)
_MODEL_PRICING: dict[str, tuple[float, float]] = {
    # OpenAI
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-5.4": (0.002, 0.008),
    "gpt-5.4-mini": (0.00015, 0.0006),
    "gpt-5.4-pro": (0.005, 0.015),
    "gpt-5.4-nano": (0.00005, 0.0002),
    "gpt-5.3-codex": (0.002, 0.008),
    "gpt-5.2-codex": (0.002, 0.008),
    "gpt-5.2": (0.002, 0.008),
    "gpt-5.1-codex-max": (0.005, 0.015),
    "gpt-5.1-codex-mini": (0.0005, 0.0015),
    "gpt-5.3-codex-spark": (0.001, 0.003),
    # Anthropic (via OpenRouter)
    "anthropic/claude-opus-4.6": (0.015, 0.075),
    "anthropic/claude-sonnet-4.6": (0.003, 0.015),
    "anthropic/claude-sonnet-4.5": (0.003, 0.015),
    "anthropic/claude-haiku-4.5": (0.0008, 0.004),
    # Google (via OpenRouter)
    "google/gemini-3-pro-preview": (0.00125, 0.005),
    "google/gemini-3-flash-preview": (0.000075, 0.0003),
    "google/gemini-3.1-pro-preview": (0.00125, 0.005),
    "google/gemini-3.1-flash-lite-preview": (0.00003, 0.0001),
    # Qwen
    "qwen/qwen3.6-plus:free": (0.0, 0.0),
    "qwen/qwen3.5-plus-02-15": (0.0004, 0.0012),
    "qwen/qwen3.5-35b-a3b": (0.0001, 0.0003),
    # Z.AI / GLM
    "glm-5": (0.001, 0.001),
    "glm-5-turbo": (0.0001, 0.0001),
    "glm-4.7": (0.0005, 0.0005),
    "glm-4.5": (0.0003, 0.0003),
    "glm-4.5-flash": (0.00005, 0.00005),
    "z-ai/glm-5": (0.001, 0.001),
    "z-ai/glm-5-turbo": (0.0001, 0.0001),
}

# Default context window sizes per model family
_MODEL_CONTEXT_WINDOWS: dict[str, int] = {
    "gpt-4o": 128_000,
    "gpt-5.4": 128_000,
    "gpt-5.3": 128_000,
    "gpt-5.2": 128_000,
    "gpt-5.1": 128_000,
    "claude-opus": 200_000,
    "claude-sonnet": 200_000,
    "claude-haiku": 200_000,
    "gemini-3": 1_000_000,
    "glm-5": 128_000,
    "glm-4": 128_000,
    "qwen": 32_000,
}

_DEFAULT_CONTEXT_WINDOW = 128_000
_CHARS_PER_TOKEN = 4


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class TokenUsage:
    """Token counts from a single API response."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def from_api_response(cls, usage: dict[str, Any] | None) -> TokenUsage:
        """Extract token usage from an OpenAI-compatible usage dict."""
        if usage is None:
            return cls()
        return cls(
            prompt_tokens=usage.get("prompt_tokens", 0) or 0,
            completion_tokens=usage.get("completion_tokens", 0) or 0,
            total_tokens=usage.get("total_tokens", 0) or 0,
        )


@dataclass
class SessionUsage:
    """Accumulated token usage and cost for a session."""

    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    api_calls: int = 0
    per_call: list[TokenUsage] = field(default_factory=list)

    def record(self, usage: TokenUsage, model: str) -> None:
        """Record a single API call's usage."""
        self.total_prompt_tokens += usage.prompt_tokens
        self.total_completion_tokens += usage.completion_tokens
        self.total_tokens += usage.total_tokens
        self.api_calls += 1
        self.per_call.append(usage)

        prompt_cost, completion_cost = _get_pricing(model)
        call_cost = (
            usage.prompt_tokens * prompt_cost / 1000
            + usage.completion_tokens * completion_cost / 1000
        )
        self.total_cost_usd += call_cost

        _log.info("usage recorded", extra={"fields": {
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "call_cost_usd": round(call_cost, 6),
            "session_cost_usd": round(self.total_cost_usd, 6),
            "api_calls": self.api_calls,
        }})

    def estimate_from_chars(self, prompt_chars: int, completion_chars: int, model: str) -> None:
        """Fallback estimation when API doesn't report usage."""
        est_prompt = prompt_chars // _CHARS_PER_TOKEN
        est_completion = completion_chars // _CHARS_PER_TOKEN
        self.record(
            TokenUsage(
                prompt_tokens=est_prompt,
                completion_tokens=est_completion,
                total_tokens=est_prompt + est_completion,
            ),
            model,
        )

    def summary(self) -> dict[str, Any]:
        """Return a summary dict for display."""
        return {
            "api_calls": self.api_calls,
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.total_cost_usd, 6),
        }


# ---------------------------------------------------------------------------
# Cost estimation
# ---------------------------------------------------------------------------


def _get_pricing(model: str) -> tuple[float, float]:
    """Get (prompt_price_per_1k, completion_price_per_1k) for a model.

    Checks exact match first, then prefix match.
    """
    if model in _MODEL_PRICING:
        return _MODEL_PRICING[model]

    # Prefix match for model variants
    for key, pricing in _MODEL_PRICING.items():
        if model.startswith(key) or key.startswith(model):
            return pricing

    # Free models
    if "free" in model.lower():
        return (0.0, 0.0)

    # Unknown model — conservative estimate
    return (0.002, 0.008)


def get_context_window(model: str) -> int:
    """Get the context window size for a model.

    Checks exact match, then prefix match, then default.
    """
    if model in _MODEL_CONTEXT_WINDOWS:
        return _MODEL_CONTEXT_WINDOWS[model]

    for key, size in _MODEL_CONTEXT_WINDOWS.items():
        if model.startswith(key) or key.startswith(model):
            return size

    return _DEFAULT_CONTEXT_WINDOW


def estimate_message_tokens(content: str) -> int:
    """Estimate token count for a message string."""
    return len(content) // _CHARS_PER_TOKEN


def estimate_conversation_tokens(messages: list[dict]) -> int:
    """Estimate total token count for a list of API messages."""
    total = 0
    for msg in messages:
        # Each message has ~4 tokens overhead (role, formatting)
        total += 4
        content = msg.get("content", "")
        if content:
            total += estimate_message_tokens(content)
        # Tool call arguments
        for tc in msg.get("tool_calls", []):
            args = tc.get("function", {}).get("arguments", "")
            if args:
                total += estimate_message_tokens(args)
    return total


# ---------------------------------------------------------------------------
# Budget manager
# ---------------------------------------------------------------------------


@dataclass
class ContextBudget:
    """Tracks how much of the context window is consumed."""

    model: str
    max_tokens: int  # max_tokens config (completion budget)
    context_window: int = 0

    def __post_init__(self) -> None:
        if not self.context_window:
            self.context_window = get_context_window(self.model)

    @property
    def prompt_budget(self) -> int:
        """Tokens available for prompt (context window minus completion budget)."""
        return self.context_window - self.max_tokens

    def tokens_remaining(self, current_messages: list[dict]) -> int:
        """How many tokens are left before hitting the context window."""
        used = estimate_conversation_tokens(current_messages)
        return max(0, self.prompt_budget - used)

    def needs_compaction(self, current_messages: list[dict], threshold: float = 0.8) -> bool:
        """Check if the conversation is consuming too much of the context window."""
        used = estimate_conversation_tokens(current_messages)
        return used > self.prompt_budget * threshold

    def compaction_urgency(self, current_messages: list[dict]) -> str:
        """Return urgency level: 'none', 'low', 'medium', 'high'."""
        used = estimate_conversation_tokens(current_messages)
        ratio = used / max(1, self.prompt_budget)
        if ratio > 0.95:
            return "high"
        if ratio > 0.85:
            return "medium"
        if ratio > 0.75:
            return "low"
        return "none"


# ---------------------------------------------------------------------------
# Usage persistence (per armory, append-only)
# ---------------------------------------------------------------------------


_USAGE_DIR = "usage"


def save_usage(
    armory_path: Path,
    session_id: str,
    usage: SessionUsage,
) -> Path | None:
    """Persist session usage to the armory."""
    if armory_path is None:
        return None

    usage_dir = armory_path / ".hephaistos" / _USAGE_DIR
    usage_dir.mkdir(parents=True, exist_ok=True)
    path = usage_dir / f"{session_id}.json"

    data = {
        "session_id": session_id,
        **usage.summary(),
    }

    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def load_usage(armory_path: Path, session_id: str) -> SessionUsage | None:
    """Load saved usage for a session."""
    path = armory_path / ".hephaistos" / _USAGE_DIR / f"{session_id}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return SessionUsage(
            total_prompt_tokens=data.get("prompt_tokens", 0),
            total_completion_tokens=data.get("completion_tokens", 0),
            total_tokens=data.get("total_tokens", 0),
            total_cost_usd=data.get("cost_usd", 0.0),
            api_calls=data.get("api_calls", 0),
        )
    except (json.JSONDecodeError, KeyError):
        return None
