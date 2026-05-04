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
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from hephaistos._types import is_string_mapping
from hephaistos.logging import get_logger
from hephaistos.runtime import ApiMessage, ContentPart, UsagePayload

_log = get_logger("chat.usage")
_MODEL_PRICING: dict[str, tuple[float, float]] = {
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
    # Google (via OpenRouter)
    "google/gemini-3-pro-preview": (0.00125, 0.005),
    "google/gemini-3-flash-preview": (0.000075, 0.0003),
    "google/gemini-3.1-pro-preview": (0.00125, 0.005),
    "google/gemini-3.1-flash-lite-preview": (0.00003, 0.0001),
    "qwen/qwen3.6-plus:free": (0.0, 0.0),
    "qwen/qwen3.5-plus-02-15": (0.0004, 0.0012),
    "qwen/qwen3.5-35b-a3b": (0.0001, 0.0003),
    "glm-5": (0.001, 0.001),
    "glm-5-turbo": (0.0001, 0.0001),
    "glm-4.7": (0.0005, 0.0005),
    "glm-4.5": (0.0003, 0.0003),
    "glm-4.5-flash": (0.00005, 0.00005),
    "z-ai/glm-5": (0.001, 0.001),
    "z-ai/glm-5-turbo": (0.0001, 0.0001),
}
_MODEL_CONTEXT_WINDOWS: dict[str, int] = {
    "gpt-4o": 128_000,
    "gpt-5.4": 128_000,
    "gpt-5.3": 128_000,
    "gpt-5.2": 128_000,
    "gpt-5.1": 128_000,
    "gemini-3": 1_000_000,
    "glm-5": 128_000,
    "glm-4": 128_000,
    "qwen": 32_000,
}

_DEFAULT_CONTEXT_WINDOW = 128_000
_CHARS_PER_TOKEN = 4


@dataclass
class TokenUsage:
    """Token counts from a single API response."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def from_api_response(cls, usage: UsagePayload | None) -> TokenUsage:
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
    per_call: deque[TokenUsage] = field(default_factory=lambda: deque(maxlen=50))

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

        _log.info(
            "usage recorded",
            extra={
                "fields": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "call_cost_usd": round(call_cost, 6),
                    "session_cost_usd": round(self.total_cost_usd, 6),
                    "api_calls": self.api_calls,
                }
            },
        )

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

    def summary(self) -> dict[str, int | float]:
        """Return a summary dict for display."""
        return {
            "api_calls": self.api_calls,
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.total_cost_usd, 6),
        }


def _get_pricing(model: str) -> tuple[float, float]:
    """Get (prompt_price_per_1k, completion_price_per_1k) for a model.

    Checks exact match first, then longest-prefix match.
    """
    if model in _MODEL_PRICING:
        return _MODEL_PRICING[model]
    for key in sorted(_MODEL_PRICING, key=len, reverse=True):
        if model.startswith(key):  # ty:ignore[invalid-argument-type]
            return _MODEL_PRICING[key]  # ty:ignore[invalid-argument-type]
    if "free" in model.lower():
        return (0.0, 0.0)
    return (0.002, 0.008)


def get_context_window(model: str) -> int:
    """Get the context window size for a model.

    Checks exact match, then longest-prefix match, then default.
    """
    if model in _MODEL_CONTEXT_WINDOWS:
        return _MODEL_CONTEXT_WINDOWS[model]

    for key in sorted(_MODEL_CONTEXT_WINDOWS, key=len, reverse=True):
        if model.startswith(key):  # ty:ignore[invalid-argument-type]
            return _MODEL_CONTEXT_WINDOWS[key]  # ty:ignore[invalid-argument-type]

    return _DEFAULT_CONTEXT_WINDOW


def estimate_message_tokens(content: str) -> int:
    """Estimate token count for a message string."""
    return len(content) // _CHARS_PER_TOKEN


def _estimate_content_tokens(content: str | None | list[ContentPart]) -> int:
    if isinstance(content, str):
        return estimate_message_tokens(content)
    if content is None:
        return 0
    total = 0
    for part in content:
        text = part.get("text", "") or part.get("content", "")
        total += estimate_message_tokens(text)
    return total


def estimate_conversation_tokens(messages: Sequence[ApiMessage]) -> int:
    """Estimate total token count for a list of API messages."""
    total = 0
    for msg in messages:
        total += 4
        total += _estimate_content_tokens(msg["content"])
        for tc in msg.get("tool_calls", []):
            function = tc.get("function", {})
            args = function.get("arguments", "")
            if args:
                total += estimate_message_tokens(args)
    return total


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

    def tokens_remaining(self, current_messages: Sequence[ApiMessage]) -> int:
        """How many tokens are left before hitting the context window."""
        used = estimate_conversation_tokens(current_messages)
        return max(0, self.prompt_budget - used)

    def compaction_urgency(self, current_messages: Sequence[ApiMessage]) -> str:
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


_USAGE_DIR = "usage"


def save_usage(
    armory_path: Path,
    session_id: str,
    usage: SessionUsage,
) -> Path | None:
    """Persist session usage to the armory."""
    if armory_path is None:  # ty: ignore
        return None

    # Defense-in-depth: validate session_id has no path traversal.
    if "/" in session_id or "\\" in session_id or ".." in session_id:
        _log.warning(
            "invalid session_id in save_usage",
            extra={"fields": {"session_id": session_id}},
        )
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


def load_usage_summaries(armory_path: Path) -> list[dict[str, int | float | str]]:
    """Load persisted usage summaries for an armory."""
    usage_dir = armory_path / ".hephaistos" / _USAGE_DIR
    if not usage_dir.exists():
        return []

    summaries: list[dict[str, int | float | str]] = []
    for path in sorted(usage_dir.glob("*.json")):
        try:
            raw: object = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if not is_string_mapping(raw):
            continue
        session_id = raw.get("session_id")
        if not isinstance(session_id, str):
            session_id = path.stem
        summaries.append(
            {
                "session_id": session_id,
                "api_calls": _int_value(raw.get("api_calls")),
                "prompt_tokens": _int_value(raw.get("prompt_tokens")),
                "completion_tokens": _int_value(raw.get("completion_tokens")),
                "total_tokens": _int_value(raw.get("total_tokens")),
                "cost_usd": _float_value(raw.get("cost_usd")),
            }
        )
    return summaries


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return 0
    return 0


def _float_value(value: object) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0
