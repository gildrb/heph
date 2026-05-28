"""Token usage, cost estimation, and context window budgeting."""

from __future__ import annotations

import json
from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeGuard

try:
    import tiktoken
except Exception:
    _encoder = None
else:
    try:
        _encoder = tiktoken.get_encoding("cl100k_base")
    except Exception:
        _encoder = None

from hephaion._types import is_object_list, is_string_mapping
from hephaion.logging import get_logger
from hephaion.providers.registry import ModelInfo, builtin_models, get_registry
from hephaion.runtime import ApiMessage, UsagePayload
from hephaion.state_paths import existing_state_path, state_path

_log = get_logger("chat.usage")
_MODEL_CONTEXT_WINDOWS: dict[str, int] = {
    "gpt-5.3": 128_000,
    "gpt-5.1": 128_000,
    "gemini-3": 1_000_000,
    "glm-4": 128_000,
    "qwen": 32_000,
}

_CHARS_PER_TOKEN = 4


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    @classmethod
    def from_api_response(cls, usage: UsagePayload | None) -> TokenUsage:
        if usage is None:
            return cls()
        return cls(
            prompt_tokens=usage.get("prompt_tokens", 0) or 0,
            completion_tokens=usage.get("completion_tokens", 0) or 0,
            total_tokens=usage.get("total_tokens", 0) or 0,
        )


@dataclass
class SessionUsage:
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    api_calls: int = 0
    per_call: deque[TokenUsage] = field(default_factory=lambda: deque(maxlen=50))

    def record(self, usage: TokenUsage, model: str) -> None:
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
        return {
            "api_calls": self.api_calls,
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_usd": round(self.total_cost_usd, 6),
        }


def _builtin_model_match(model: str) -> ModelInfo | None:
    return next(
        (
            info
            for info in sorted(builtin_models(), key=lambda info: len(info.name), reverse=True)
            if model.startswith(info.name)
        ),
        None,
    )


def _get_pricing(model: str) -> tuple[float, float]:
    if "free" in model.lower():
        return (0.0, 0.0)
    info = get_registry().get(model) or _builtin_model_match(model)
    if info is None:
        return (0.002, 0.008)
    return (info.prompt_price_per_1k, info.completion_price_per_1k)


def get_context_window(model: str) -> int:
    info = get_registry().get(model) or _builtin_model_match(model)
    if info is not None:
        return info.context_window
    for prefix, context_window in sorted(
        _MODEL_CONTEXT_WINDOWS.items(), key=lambda item: len(item[0]), reverse=True
    ):
        if model.startswith(prefix):
            return context_window
    return 128_000


def estimate_message_tokens(content: str) -> int:
    if _encoder is not None:
        return len(_encoder.encode(content))
    return len(content) // _CHARS_PER_TOKEN


def estimate_conversation_tokens(messages: Sequence[ApiMessage]) -> int:
    return sum(_api_message_token_estimate(message) for message in messages)


def _api_message_token_estimate(message: ApiMessage) -> int:
    return (
        4
        + _content_token_estimate(message["content"])
        + sum(_tool_call_token_estimate(tool_call) for tool_call in message.get("tool_calls", []))
    )


def _content_token_estimate(content: object) -> int:
    if isinstance(content, str):
        return estimate_message_tokens(content)
    return sum(
        estimate_message_tokens(text)
        for part in _content_parts(content)
        if (text := _part_text(part))
    )


def _content_parts(content: object) -> list[object]:
    return content if is_object_list(content) else []


def _part_text(part: object) -> str:
    if not is_string_mapping(part):
        return ""
    text = part.get("text", "") or part.get("content", "")
    return text if isinstance(text, str) else ""


def _tool_call_token_estimate(tool_call: object) -> int:
    if not is_string_mapping(tool_call):
        return 0
    function = tool_call.get("function", {})
    if not is_string_mapping(function):
        return 0
    args = function.get("arguments", "")
    return estimate_message_tokens(args) if isinstance(args, str) and args else 0


@dataclass
class ContextBudget:
    model: str
    max_tokens: int  # max_tokens config (completion budget)
    context_window: int = 0

    def __post_init__(self) -> None:
        if not self.context_window:
            self.context_window = get_context_window(self.model)

    @property
    def prompt_budget(self) -> int:
        return self.context_window - self.max_tokens

    def tokens_remaining(self, current_messages: Sequence[ApiMessage]) -> int:
        used = estimate_conversation_tokens(current_messages)
        return max(0, self.prompt_budget - used)

    def compaction_urgency(self, current_messages: Sequence[ApiMessage]) -> str:
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
    if armory_path is None:
        return None

    # Defense-in-depth: validate session_id has no path traversal.
    if "/" in session_id or "\\" in session_id or ".." in session_id:
        _log.warning(
            "invalid session_id in save_usage",
            extra={"fields": {"session_id": session_id}},
        )
        return None

    usage_dir = state_path(armory_path, _USAGE_DIR)
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
    usage_dir = existing_state_path(armory_path, _USAGE_DIR)
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
        summaries.append(_usage_summary_from_payload(raw, fallback_session_id=path.stem))
    return summaries


def _usage_summary_from_payload(
    raw: dict[str, object],
    *,
    fallback_session_id: str,
) -> dict[str, int | float | str]:
    session_id = raw.get("session_id")
    return {
        "session_id": session_id if isinstance(session_id, str) else fallback_session_id,
        "api_calls": _number_value(raw.get("api_calls")),
        "prompt_tokens": _number_value(raw.get("prompt_tokens")),
        "completion_tokens": _number_value(raw.get("completion_tokens")),
        "total_tokens": _number_value(raw.get("total_tokens")),
        "cost_usd": _number_value(raw.get("cost_usd"), as_float=True),
    }


def _number_value(value: object, *, as_float: bool = False) -> int | float:
    default = 0.0 if as_float else 0
    if _is_number_value(value):
        return float(value) if as_float else int(value)
    if isinstance(value, str):
        return _number_from_string(value, default=default, as_float=as_float)
    return default


def _is_number_value(value: object) -> TypeGuard[int | float]:
    return not isinstance(value, bool) and isinstance(value, int | float)


def _number_from_string(value: str, *, default: float, as_float: bool) -> int | float:
    try:
        return float(value) if as_float else int(value)
    except ValueError:
        return default
