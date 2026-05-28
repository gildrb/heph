"""Shared LLM communication runtime with streaming support.

Supports any OpenAI-compatible API endpoint, making it LLM-agnostic.
Configure via environment variables:
    HEPHAION_API_KEY   - API key override (applies to any provider)
    HEPHAION_BASE_URL  - Base URL for the API
    HEPHAION_MODEL     - Model name

Streaming error recovery:
    Transient failures (connection drops, timeouts, server errors) are
    retried automatically with exponential backoff.  If a retry fails
    after content has already been streamed to the caller, a
    ``StreamRecoveryError`` is raised carrying the partial response so
    that the caller can decide how to proceed.
"""

from __future__ import annotations

import contextlib
import json
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Generator, Iterator, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, NoReturn, Protocol, Self, cast

from hephaion._types import is_string_mapping
from hephaion.diagnostics.crashes import get_meter, get_tracer
from hephaion.env import get_env
from hephaion.logging import Timer, get_logger, redact_text
from hephaion.providers.endpoints import is_keyless_endpoint
from hephaion.providers.keyring_store import resolve_key
from hephaion.providers.model_support import is_supported_model_for_endpoint
from hephaion.providers.oauth import load_credentials
from hephaion.providers.reasoning import (
    DEFAULT_REASONING_LEVEL,
    normalize_reasoning_level,
    reasoning_levels_for_model,
)
from hephaion.providers.registry import get_registry as get_provider_registry
from hephaion.runtime._api_types import ApiMessage, ToolCallDelta, UsagePayload
from hephaion.runtime.messages import message_content_text
from hephaion.runtime.prompt_cache import (
    MetricsLogger as PromptCacheMetricsLogger,
)
from hephaion.runtime.prompt_cache import (
    PromptCacheRequest,
    StablePrefixBuilder,
    annotate_anthropic_cache_breakpoints,
)
from hephaion.runtime.resilience import CircuitBreaker

if TYPE_CHECKING:
    from openai import OpenAI, Stream
    from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
    from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall


class _SpanProtocol(Protocol):
    def set_attribute(self, key: str, value: object) -> object: ...

    def end(self, _end_time: float | None = None) -> None: ...


class _TracerProtocol(Protocol):
    def start_span(self, name: str, **kwargs: object) -> _SpanProtocol: ...


class _ByteStreamResponseProtocol(Protocol):
    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object,
    ) -> object: ...

    def __iter__(self) -> Iterator[bytes]: ...


class _CounterProtocol(Protocol):
    def add(self, value: float, _attributes: dict[str, str] | None = None) -> None: ...


class _HistogramProtocol(Protocol):
    def record(self, value: float, _attributes: dict[str, str] | None = None) -> None: ...


class _MeterProtocol(Protocol):
    def create_histogram(self, name: str, **kwargs: object) -> _HistogramProtocol: ...

    def create_counter(self, name: str, **kwargs: object) -> _CounterProtocol: ...


_log = get_logger("runtime.engine")
_prompt_cache_builder = StablePrefixBuilder()
_prompt_cache_metrics = PromptCacheMetricsLogger()

_tracer: _TracerProtocol = get_tracer("runtime.engine")  # ty:ignore[invalid-assignment]
_meter: _MeterProtocol = get_meter("runtime.engine")

_llm_duration_hist = _meter.create_histogram(
    "llm.request.duration",
    unit="ms",
    description="Duration of LLM completion requests",
)
_llm_token_counter = _meter.create_counter(
    "llm.token.usage",
    description="Number of tokens used in LLM requests",
)

_circuit_breaker = CircuitBreaker(name="llm-default")


def reset_provider_circuit_breaker() -> None:
    """Reset the shared provider circuit for diagnostics and retry harnesses."""
    _circuit_breaker.reset()


@dataclass
class ChatConfig:
    """Configuration for the LLM engine.

    API keys are resolved lazily at call time from the OS keychain →
    environment variable → volatile in-memory store.  The ``api_key`` field
    is kept for backward compatibility but should not be used to store raw
    keys persistently.  Use the ``resolved_api_key`` property instead.
    """

    api_key: str = ""
    base_url: str = ""
    model: str = ""
    max_tokens: int = 4096
    rag_context_budget: int = 2000
    reasoning_level: str = DEFAULT_REASONING_LEVEL
    temperature: float | None = 0.0
    feature_flags: frozenset[str] = field(default_factory=frozenset)
    _provider_slug: str = field(default="", repr=False)
    _provider_env: str = field(default="", repr=False)

    def is_feature_enabled(self, flag: str) -> bool:
        return flag in self.feature_flags

    def __post_init__(self) -> None:
        self.reasoning_level = normalize_reasoning_level(self.reasoning_level)
        if self.temperature is not None:
            self.temperature = min(2.0, max(0.0, self.temperature))

    @property
    def provider_slug(self) -> str:
        return self._provider_slug

    @property
    def resolved_api_key(self) -> str:
        if self._provider_slug:
            if not self._provider_env:
                return self.api_key
            return resolve_key(self._provider_slug, self._provider_env)
        return self.api_key

    def apply_provider_reference(self, slug: str, env_var: str) -> None:
        self._provider_slug = slug
        self._provider_env = env_var


class EngineError(Exception):
    pass


class StreamRecoveryError(EngineError):
    """Raised when a streaming response was interrupted.

    Carries the partial content that was already received (and possibly
    displayed) so that callers can preserve it or retry.
    """

    def __init__(self, partial_content: str, last_error: Exception | None = None) -> None:
        self.partial_content = partial_content
        msg = f"Stream interrupted after {len(partial_content)} chars"
        if last_error:
            msg += f": {last_error}"
        super().__init__(msg)
        self.__cause__ = last_error


class _RetryOpenAIStreamError(Exception):
    def __init__(self, cause: Exception) -> None:
        super().__init__(str(cause))
        self.cause = cause


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds


_retryable_types_cache: list[tuple[type[Exception], ...]] = []


def _get_retryable_types() -> tuple[type[Exception], ...]:
    if _retryable_types_cache:
        return _retryable_types_cache[0]
    from openai import (
        APIConnectionError,
        APITimeoutError,
        InternalServerError,
        RateLimitError,
    )

    retryable_types = (
        APIConnectionError,
        APITimeoutError,
        InternalServerError,
        RateLimitError,
    )
    _retryable_types_cache.append(retryable_types)
    return retryable_types


_ACCOUNT_SETUP_RATE_LIMIT_CODES = {
    "1113",
    "billing_not_active",
    "insufficient_quota",
    "insufficient_balance",
}
_ACCOUNT_SETUP_ERROR_TERMS = (
    "insufficient balance",
    "insufficient quota",
    "no resource package",
    "please recharge",
    "billing",
    "payment",
    "credit",
    "quota exceeded",
)
_ACCOUNT_SETUP_HINT = "Use /login to connect a subscription or API key, then /models."
_PROVIDER_CAPACITY_ERROR_TERMS = ("queue full",)
_PROVIDER_CAPACITY_HINT = (
    "The free model provider is busy or rate-limiting this connection. "
    "Try again shortly, or use /login to connect your own provider and /models to switch."
)
_CODEX_BACKEND_RESPONSES_URL = "https://chatgpt.com/backend-api/codex/responses"
_CODEX_BACKEND_TIMEOUT_SECONDS = 30
_PROVIDER_IP_RE = re.compile(r"\bIP:\s*(?:\d{1,3}\.){3}\d{1,3}\b", re.IGNORECASE)
_MAX_PROVIDER_DETAIL_CHARS = 260


@dataclass
class Message:
    role: str  # "system", "user", or "assistant"
    content: str


@dataclass
class Conversation:
    messages: list[Message] = field(default_factory=list)
    _api_cache: list[ApiMessage] | None = field(default=None, init=False, repr=False)

    def add(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))
        self._api_cache = None

    def to_api_messages(self) -> list[ApiMessage]:
        if self._api_cache is not None:
            return self._api_cache
        self._api_cache = [{"role": msg.role, "content": msg.content} for msg in self.messages]
        return self._api_cache


@dataclass(frozen=True, slots=True)
class _ProviderErrorDetail:
    message: str
    code: str


@dataclass(frozen=True, slots=True)
class _StreamCompletionRequest:
    api_messages: list[ApiMessage]
    prompt_request: PromptCacheRequest
    message_count: int
    tool_count: int


@dataclass(frozen=True, slots=True)
class _OpenAIStreamAttempt:
    stream: Stream[ChatCompletionChunk]
    timer: Timer


@dataclass(frozen=True, slots=True)
class _OpenAIStartResult:
    attempt: _OpenAIStreamAttempt | None
    error: Exception | None
    should_continue: bool

    @property
    def should_stop(self) -> bool:
        return self.error is not None and not self.should_continue


@dataclass(frozen=True, slots=True)
class _OpenAICompletionAttemptResult:
    done: bool
    retry: bool = False
    error: Exception | None = None


@dataclass(slots=True)
class _OpenAIStreamProgress:
    partial_parts: list[str] = field(default_factory=list)
    saw_output: bool = False

    def record(self, delta: CompletionDelta) -> None:
        if delta.content:
            self.partial_parts.append(delta.content)
        if delta.content or delta.tool_calls:
            self.saw_output = True

    @property
    def partial_content(self) -> str:
        return "".join(self.partial_parts)


def to_chat_completion_messages(messages: list[ApiMessage]) -> list[ChatCompletionMessageParam]:
    return cast("list[ChatCompletionMessageParam]", messages)


def _provider_error_body(exc: Exception) -> dict[str, object] | None:
    body = getattr(exc, "body", None)
    if is_string_mapping(body):
        return body

    response = getattr(exc, "response", None)
    json_fn = getattr(response, "json", None)
    if not callable(json_fn):
        return None

    try:
        response_body = json_fn()
    except Exception:
        return None
    return response_body if is_string_mapping(response_body) else None


def _provider_error_detail_from_body(body: dict[str, object]) -> _ProviderErrorDetail:
    raw_message, raw_code = _message_and_code_from_payload(body)
    return _ProviderErrorDetail(
        message=str(raw_message or "").strip(),
        code=str(raw_code or "").strip(),
    )


def _payload_error_mapping(payload: dict[str, object]) -> dict[str, object] | None:
    error_value = payload.get("error", payload)
    return error_value if is_string_mapping(error_value) else None


def _message_and_code_from_payload(payload: dict[str, object]) -> tuple[object, object]:
    error_value = payload.get("error", payload)
    if error_mapping := _payload_error_mapping(payload):
        return _message_and_code_from_error_mapping(payload, error_mapping)
    return payload.get("message") or error_value, payload.get("code")


def _message_and_code_from_error_mapping(
    payload: dict[str, object],
    error_mapping: dict[str, object],
) -> tuple[object, object]:
    return (
        error_mapping.get("message") or payload.get("message"),
        _error_mapping_code(error_mapping) or payload.get("code"),
    )


def _error_mapping_code(error_mapping: dict[str, object]) -> object:
    return error_mapping.get("code") or error_mapping.get("type")


def _provider_error_fields(exc: Exception) -> tuple[str, str]:
    detail = _provider_error_detail(exc)
    message = detail.message or _exception_message(exc)
    code = detail.code or _exception_code(exc)
    return message or exc.__class__.__name__, code


def _provider_error_detail(exc: Exception) -> _ProviderErrorDetail:
    body = _provider_error_body(exc)
    if body is None:
        return _ProviderErrorDetail(message="", code="")
    return _provider_error_detail_from_body(body)


def _exception_message(exc: Exception) -> str:
    return str(getattr(exc, "message", "") or exc).strip()


def _exception_code(exc: Exception) -> str:
    return str(getattr(exc, "code", "") or "").strip()


def _is_account_setup_error(exc: Exception) -> bool:
    from openai import AuthenticationError, PermissionDeniedError, RateLimitError

    if isinstance(exc, AuthenticationError | PermissionDeniedError):
        return True
    if not isinstance(exc, RateLimitError):
        return False

    message, code = _provider_error_fields(exc)
    message_lower = message.lower()
    code_lower = code.lower()
    return code_lower in _ACCOUNT_SETUP_RATE_LIMIT_CODES or any(
        term in message_lower for term in _ACCOUNT_SETUP_ERROR_TERMS
    )


def _is_provider_capacity_error(exc: Exception) -> bool:
    from openai import RateLimitError

    if not isinstance(exc, RateLimitError):
        return False
    message, code = _provider_error_fields(exc)
    haystack = f"{message} {code}".lower()
    return any(term in haystack for term in _PROVIDER_CAPACITY_ERROR_TERMS)


def _with_hint(message: str, hint: str) -> str:
    message = message.rstrip()
    if message and message[-1] not in ".!?":
        message += "."
    return f"{message} {hint}"


def _failure_message(exc: Exception, *, stream: bool) -> str:
    account_prefix, capacity_prefix, default_prefix = (
        ("Provider rejected the stream", "Provider stream is busy", "LLM stream failed")
        if stream
        else ("Provider rejected the request", "Provider is busy", "LLM request failed")
    )
    detail, _code = _provider_error_fields(exc)
    detail = _PROVIDER_IP_RE.sub("this connection", redact_text(detail))
    if len(detail) > _MAX_PROVIDER_DETAIL_CHARS:
        detail = f"{detail[: _MAX_PROVIDER_DETAIL_CHARS - 3].rstrip()}..."
    if _is_account_setup_error(exc):
        return _with_hint(f"{account_prefix}: {detail}", _ACCOUNT_SETUP_HINT)
    if _is_provider_capacity_error(exc):
        return _with_hint(f"{capacity_prefix}: {detail}", _PROVIDER_CAPACITY_HINT)
    return f"{default_prefix}: {detail}"


def _log_error_summary(exc: Exception) -> str:
    if _is_account_setup_error(exc):
        detail, code = _provider_error_fields(exc)
        return f"{code}: {detail}" if code else detail
    return str(exc)


def build_client(config: ChatConfig) -> OpenAI:
    from openai import OpenAI

    if not config.base_url:
        raise EngineError("No model source configured. Use /login, then /models.")
    if not config.model:
        raise EngineError("No model configured. Use /models to select one.")
    if not is_supported_model_for_endpoint(config.model, config.base_url):
        raise EngineError(f"Model unavailable for endpoint: {config.model}")
    return OpenAI(api_key=_api_key_for_config(config), base_url=config.base_url)


def _api_key_for_config(config: ChatConfig) -> str:
    if is_keyless_endpoint(config.base_url):
        return "no-key-required"
    if config.resolved_api_key:
        return config.resolved_api_key
    raise EngineError(missing_api_key_message(config))


def missing_api_key_message(config: ChatConfig) -> str:
    if config.provider_slug == "openai-codex":
        return (
            "OpenAI Codex subscription requires /login OAuth credentials. "
            "Use the OpenAI API provider for OPENAI_API_KEY billing."
        )
    model_info = get_provider_registry().get(config.model)
    if model_info is not None and model_info.is_free:
        return (
            f"{config.model} is free-priced, but {model_info.display_name} is served through "
            "a provider that still requires an API key. Use /login or set an environment "
            "variable."
        )
    return "No API key found. Use /login or set an environment variable."


def is_retryable_error(exc: Exception) -> bool:
    if _is_account_setup_error(exc) or _is_provider_capacity_error(exc):
        return False
    return isinstance(exc, _get_retryable_types())


def _wait_backoff(
    attempt: int,
    config: RetryConfig,
    abort: threading.Event | None = None,
) -> bool:
    delay = min(config.base_delay * (2**attempt), config.max_delay)
    jitter = random.uniform(0, delay * 0.5)
    if abort is not None:
        return not abort.wait(timeout=jitter)
    time.sleep(jitter)
    return True


@dataclass(frozen=True, slots=True)
class CompletionDelta:
    content: str | None = None
    tool_calls: list[ToolCallDelta] | None = None
    finish_reason: str = ""
    usage: UsagePayload | None = None


def _normalize_tool_calls(tool_calls: list[ChoiceDeltaToolCall]) -> list[ToolCallDelta]:
    return [_normalize_tool_call(tool_call) for tool_call in tool_calls]


def _normalize_tool_call(tool_call: ChoiceDeltaToolCall) -> ToolCallDelta:
    result: ToolCallDelta = {"index": tool_call.index}
    _add_optional_tool_call_fields(result, tool_call)
    if tool_call.function is not None:
        result["function"] = {
            "name": tool_call.function.name or "",
            "arguments": tool_call.function.arguments or "",
        }
    return result


def _add_optional_tool_call_fields(
    result: ToolCallDelta,
    tool_call: ChoiceDeltaToolCall,
) -> None:
    if tool_call.id:
        result["id"] = tool_call.id
    if tool_call.type:
        result["type"] = str(tool_call.type)


def _optional_int_value(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _cached_tokens_from_usage_details(details: object) -> int | None:
    if is_string_mapping(details):
        return _optional_int_value(details.get("cached_tokens"))
    return _optional_int_value(getattr(details, "cached_tokens", None))


def _cached_prompt_tokens_from_usage(usage: object) -> int | None:
    for details in _usage_detail_sources(usage):
        cached_tokens = _cached_tokens_from_usage_details(details)
        if cached_tokens is not None:
            return cached_tokens
    return None


def _usage_detail_sources(usage: object) -> Iterator[object]:
    names = ("prompt_tokens_details", "input_tokens_details")
    for name in names:
        yield getattr(usage, name, None)
    if is_string_mapping(usage):
        for name in names:
            yield usage.get(name)


def _extract_usage(chunk: object) -> UsagePayload | None:
    usage = getattr(chunk, "usage", None)
    if not usage:
        return None
    payload = _base_usage_payload(usage)
    cached_prompt_tokens = _cached_prompt_tokens_from_usage(usage)
    if cached_prompt_tokens is not None:
        payload["cached_prompt_tokens"] = cached_prompt_tokens
    return payload


def _base_usage_payload(usage: object) -> UsagePayload:
    return {
        "prompt_tokens": (getattr(usage, "prompt_tokens", 0) or 0),
        "completion_tokens": (getattr(usage, "completion_tokens", 0) or 0),
        "total_tokens": (getattr(usage, "total_tokens", 0) or 0),
    }


def _record_usage(
    usage: UsagePayload,
    model: str,
    span: _SpanProtocol,
    *,
    prompt_request: PromptCacheRequest | None = None,
) -> None:
    prompt = usage.get("prompt_tokens", 0) or 0
    completion = usage.get("completion_tokens", 0) or 0
    cached_prompt_tokens = usage.get("cached_prompt_tokens")
    span.set_attribute("gen_ai.response.prompt_tokens", prompt)
    span.set_attribute("gen_ai.response.completion_tokens", completion)
    if cached_prompt_tokens is not None:
        span.set_attribute("gen_ai.response.cached_prompt_tokens", cached_prompt_tokens)
    _llm_token_counter.add(prompt, {"model": model, "type": "prompt"})
    _llm_token_counter.add(completion, {"model": model, "type": "completion"})
    if cached_prompt_tokens:
        _llm_token_counter.add(cached_prompt_tokens, {"model": model, "type": "cached_prompt"})
    _prompt_cache_metrics.record_usage(
        prompt_request,
        model=model,
        cached_prompt_tokens=cached_prompt_tokens,
    )


def _mark_span_error(span: _SpanProtocol, error_type: str) -> None:
    span.set_attribute("error", True)
    span.set_attribute("error.type", error_type)


def _codex_backend_auth(config: ChatConfig) -> tuple[str, str] | None:
    if config.provider_slug != "openai-codex":
        return None
    creds = load_credentials("openai-codex")
    if creds is None:
        return None
    return creds.access_token, creds.account_id or ""


def has_configured_access(config: ChatConfig, *, refresh_oauth: bool = True) -> bool:
    if is_keyless_endpoint(config.base_url):
        return True
    if config.provider_slug == "openai-codex":
        return load_credentials("openai-codex", refresh_expired=refresh_oauth) is not None
    return bool(config.resolved_api_key)


def _codex_input_item(role: str, text: str) -> dict[str, object]:
    item_type = "output_text" if role == "assistant" else "input_text"
    item_role = "assistant" if role == "assistant" else "user"
    return {
        "role": item_role,
        "content": [{"type": item_type, "text": text}],
    }


def _append_codex_message(
    message: ApiMessage,
    instructions: list[str],
    inputs: list[dict[str, object]],
) -> None:
    role = message["role"]
    text = message_content_text(message.get("content"))
    if not text:
        return
    if role == "system":
        instructions.append(text)
        return
    if role in {"user", "assistant"}:
        inputs.append(_codex_input_item(role, text))
        return
    inputs.append(_codex_input_item("user", f"{role} result:\n{text}"))


def _codex_payload_messages(
    api_messages: list[ApiMessage],
) -> tuple[list[str], list[dict[str, object]]]:
    instructions: list[str] = []
    inputs: list[dict[str, object]] = []
    for message in api_messages:
        _append_codex_message(message, instructions, inputs)
    return instructions, inputs


def _codex_payload(
    config: ChatConfig,
    api_messages: list[ApiMessage],
) -> dict[str, object]:
    instructions, inputs = _codex_payload_messages(api_messages)
    payload: dict[str, object] = {
        "model": config.model,
        "instructions": "\n\n".join(instructions)
        or "You are a concise source-grounded assistant.",
        "input": inputs,
        "store": False,
        "stream": True,
    }
    if reasoning_effort := _model_reasoning_effort(config):
        payload["reasoning"] = {"effort": reasoning_effort}
    return payload


def _int_value(value: object) -> int:
    return value if isinstance(value, int) else 0


def _codex_usage(payload: dict[str, object]) -> UsagePayload | None:
    response = payload.get("response")
    if not is_string_mapping(response):
        return None
    usage = response.get("usage")
    if not is_string_mapping(usage):
        return None
    prompt_tokens = _int_value(usage.get("input_tokens"))
    completion_tokens = _int_value(usage.get("output_tokens"))
    result: UsagePayload = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": _int_value(usage.get("total_tokens")) or prompt_tokens + completion_tokens,
    }
    cached_prompt_tokens = _cached_prompt_tokens_from_usage(usage)
    if cached_prompt_tokens is not None:
        result["cached_prompt_tokens"] = cached_prompt_tokens
    return result


def _codex_failure_detail(payload: dict[str, object]) -> str:
    response = payload.get("response")
    if is_string_mapping(response):
        message, _code = _message_and_code_from_payload(response)
        if message:
            return redact_text(str(message))
    detail = payload.get("detail")
    if isinstance(detail, str) and detail:
        return redact_text(detail)
    return "ChatGPT Codex backend request failed"


def _codex_http_error_detail(exc: urllib.error.HTTPError) -> str:
    body = exc.read(1000).decode("utf-8", "replace")
    with contextlib.suppress(json.JSONDecodeError):
        payload = json.loads(body)
        if is_string_mapping(payload):
            return _codex_failure_detail(payload)
    return redact_text(body.strip() or str(exc))


def _codex_event_payload(raw_line: bytes) -> dict[str, object] | None:
    data = _codex_event_data(raw_line)
    if data is None:
        return None
    if data == "[DONE]":
        return {"type": "response.done"}
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError:
        return None
    return parsed if is_string_mapping(parsed) else None


def _codex_event_data(raw_line: bytes) -> str | None:
    line = raw_line.decode("utf-8", "replace").strip()
    if not line.startswith("data:"):
        return None
    data = line.removeprefix("data:").strip()
    return data or None


type _CodexEventHandler = Callable[
    [dict[str, object], ChatConfig, _SpanProtocol, PromptCacheRequest | None],
    CompletionDelta | None,
]


def _codex_done_delta(
    _event: dict[str, object],
    _config: ChatConfig,
    _span: _SpanProtocol,
    _prompt_request: PromptCacheRequest | None,
) -> CompletionDelta | None:
    return None


def _codex_output_text_delta(
    event: dict[str, object],
    _config: ChatConfig,
    _span: _SpanProtocol,
    _prompt_request: PromptCacheRequest | None,
) -> CompletionDelta | None:
    delta = event.get("delta")
    return CompletionDelta(content=delta) if isinstance(delta, str) and delta else None


def _codex_completed_delta(
    event: dict[str, object],
    config: ChatConfig,
    span: _SpanProtocol,
    prompt_request: PromptCacheRequest | None,
) -> CompletionDelta:
    usage = _codex_usage(event)
    if usage is None:
        return CompletionDelta(finish_reason="stop")
    _record_usage(usage, config.model, span, prompt_request=prompt_request)
    return CompletionDelta(finish_reason="stop", usage=usage)


def _codex_failed_delta(
    event: dict[str, object],
    _config: ChatConfig,
    _span: _SpanProtocol,
    _prompt_request: PromptCacheRequest | None,
) -> CompletionDelta | None:
    raise EngineError(f"ChatGPT Codex request failed: {_codex_failure_detail(event)}")


_CODEX_EVENT_HANDLERS: dict[str, _CodexEventHandler] = {
    "response.done": _codex_done_delta,
    "response.output_text.delta": _codex_output_text_delta,
    "response.completed": _codex_completed_delta,
    "response.failed": _codex_failed_delta,
}


def _codex_delta_from_event(
    event: dict[str, object],
    config: ChatConfig,
    span: _SpanProtocol,
    *,
    prompt_request: PromptCacheRequest | None,
) -> CompletionDelta | None:
    event_type = event.get("type")
    handler = _CODEX_EVENT_HANDLERS.get(event_type) if isinstance(event_type, str) else None
    if handler is None:
        return None
    return handler(event, config, span, prompt_request)


def _stream_codex_backend_completion(
    config: ChatConfig,
    api_messages: list[ApiMessage],
    auth: tuple[str, str],
    *,
    abort: threading.Event | None,
    span: _SpanProtocol,
    prompt_request: PromptCacheRequest | None = None,
) -> Iterator[CompletionDelta]:
    response = _open_codex_backend_response(config, api_messages, auth)
    with response:
        for raw_line in response:
            if _completion_aborted(abort):
                return
            done = yield from _iter_codex_stream_step(
                raw_line,
                config,
                span,
                prompt_request=prompt_request,
            )
            if done:
                return


def _completion_aborted(abort: threading.Event | None) -> bool:
    return abort is not None and abort.is_set()


def _iter_codex_stream_step(
    raw_line: bytes,
    config: ChatConfig,
    span: _SpanProtocol,
    *,
    prompt_request: PromptCacheRequest | None,
) -> Generator[CompletionDelta, None, bool]:
    step = _codex_stream_step(raw_line, config, span, prompt_request=prompt_request)
    if step is None:
        return False
    if step.delta is not None:
        yield step.delta
    return step.done


def _codex_stream_step(
    raw_line: bytes,
    config: ChatConfig,
    span: _SpanProtocol,
    *,
    prompt_request: PromptCacheRequest | None,
) -> _CodexEventDelta | None:
    event_delta = _codex_event_delta(raw_line, config, span, prompt_request=prompt_request)
    if event_delta is None:
        return None
    return event_delta


@dataclass(frozen=True, slots=True)
class _CodexEventDelta:
    delta: CompletionDelta | None
    done: bool


def _codex_event_delta(
    raw_line: bytes,
    config: ChatConfig,
    span: _SpanProtocol,
    *,
    prompt_request: PromptCacheRequest | None,
) -> _CodexEventDelta | None:
    event = _codex_event_payload(raw_line)
    if event is None:
        return None
    delta = _codex_delta_from_event(event, config, span, prompt_request=prompt_request)
    return _CodexEventDelta(
        delta=delta,
        done=event.get("type") in {"response.done", "response.completed"},
    )


def _open_codex_backend_response(
    config: ChatConfig,
    api_messages: list[ApiMessage],
    auth: tuple[str, str],
) -> _ByteStreamResponseProtocol:
    request = _codex_backend_request(config, api_messages, auth)
    try:
        return urllib.request.urlopen(  # nosec B310
            request,
            timeout=_codex_backend_timeout_seconds(),
        )
    except urllib.error.HTTPError as exc:
        detail = _codex_http_error_detail(exc)
        raise EngineError(f"ChatGPT Codex request failed: {detail}") from exc
    except urllib.error.URLError as exc:
        raise EngineError(f"ChatGPT Codex request failed: {redact_text(str(exc.reason))}") from exc


def _codex_backend_timeout_seconds() -> float:
    raw = get_env("HEPHAION_CODEX_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return _CODEX_BACKEND_TIMEOUT_SECONDS
    with contextlib.suppress(ValueError):
        value = float(raw)
        if value > 0:
            return value
    return _CODEX_BACKEND_TIMEOUT_SECONDS


def _codex_backend_request(
    config: ChatConfig,
    api_messages: list[ApiMessage],
    auth: tuple[str, str],
) -> urllib.request.Request:
    return urllib.request.Request(
        _CODEX_BACKEND_RESPONSES_URL,
        data=json.dumps(_codex_payload(config, api_messages)).encode("utf-8"),
        headers=_codex_backend_headers(auth),
        method="POST",
    )


def _codex_backend_headers(auth: tuple[str, str]) -> dict[str, str]:
    access_token, account_id = auth
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "User-Agent": "hephaion-cli",
    }
    if account_id:
        headers["ChatGPT-Account-ID"] = account_id
    return headers


def _stream_codex_completion(
    config: ChatConfig,
    api_messages: list[ApiMessage],
    auth: tuple[str, str],
    *,
    abort: threading.Event | None,
    span: _SpanProtocol,
    prompt_request: PromptCacheRequest,
    message_count: int,
    tool_count: int,
) -> Iterator[CompletionDelta]:
    if not _circuit_breaker.allow_request():
        span.end()
        raise EngineError("LLM provider circuit breaker is open — too many recent failures")

    timer = Timer()
    try:
        with timer:
            yield from _stream_codex_backend_completion(
                config,
                api_messages,
                auth,
                abort=abort,
                span=span,
                prompt_request=prompt_request,
            )
    except EngineError as exc:
        _circuit_breaker.record_failure()
        _mark_span_error(span, type(exc).__name__)
        span.end()
        raise
    except Exception as exc:
        _circuit_breaker.record_failure()
        _mark_span_error(span, type(exc).__name__)
        span.end()
        raise EngineError(f"ChatGPT Codex request failed: {redact_text(str(exc))}") from exc

    _log.info(
        "stream_completion complete",
        extra={
            "fields": {
                "model": config.model,
                "latency_ms": timer.ms,
                "message_count": message_count,
                "tool_count": tool_count,
                "transport": "chatgpt-codex",
            }
        },
    )
    _circuit_breaker.record_success()
    span.set_attribute("gen_ai.response.latency_ms", timer.ms)
    _llm_duration_hist.record(timer.ms, {"model": config.model})
    span.end()


def _request_kwargs(
    config: ChatConfig,
    api_messages: list[ApiMessage],
    *,
    tools: Sequence[object] | None,
    tool_choice: object | None,
) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "model": config.model,
        "messages": to_chat_completion_messages(api_messages),
        "max_tokens": config.max_tokens,
        "stream": True,
    }
    if tools:
        kwargs["tools"] = list(tools)
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
    if config.temperature is not None:
        kwargs["temperature"] = config.temperature
    if reasoning_effort := _model_reasoning_effort(config):
        kwargs["reasoning_effort"] = reasoning_effort
    return kwargs


def _model_supports_reasoning(config: ChatConfig) -> bool:
    return bool(reasoning_levels_for_model(config.model, config.provider_slug or None))


def _model_reasoning_effort(config: ChatConfig) -> str | None:
    levels = reasoning_levels_for_model(config.model, config.provider_slug or None)
    if not levels:
        return None
    normalized = normalize_reasoning_level(config.reasoning_level)
    return normalized if normalized in levels else levels[0]


def _usage_delta_from_chunk(
    chunk: ChatCompletionChunk,
    config: ChatConfig,
    span: _SpanProtocol,
    *,
    prompt_request: PromptCacheRequest,
) -> CompletionDelta | None:
    usage = _extract_usage(chunk)
    if usage is None:
        return None
    _record_usage(usage, config.model, span, prompt_request=prompt_request)
    return CompletionDelta(usage=usage)


def _choice_delta_from_chunk(
    chunk: ChatCompletionChunk,
    config: ChatConfig,
    span: _SpanProtocol,
    *,
    prompt_request: PromptCacheRequest,
) -> CompletionDelta | None:
    choice = chunk.choices[0]
    delta = choice.delta
    finish_reason = choice.finish_reason or ""
    usage = _extract_usage(chunk)
    if usage is not None:
        _record_usage(usage, config.model, span, prompt_request=prompt_request)
    if _empty_choice_delta(delta, finish_reason=finish_reason, usage=usage):
        return None
    return _completion_delta_from_choice(delta, finish_reason=finish_reason, usage=usage)


def _completion_delta_from_choice(
    delta: object,
    *,
    finish_reason: str,
    usage: UsagePayload | None,
) -> CompletionDelta:
    return CompletionDelta(
        content=_choice_delta_content(delta),
        tool_calls=_choice_delta_tool_calls(delta),
        finish_reason=finish_reason,
        usage=usage,
    )


def _choice_delta_content(delta: object) -> str | None:
    content = getattr(delta, "content", None)
    return content or None if isinstance(content, str) else None


def _choice_delta_tool_calls(delta: object) -> list[ToolCallDelta] | None:
    tool_calls = getattr(delta, "tool_calls", None)
    return _normalize_tool_calls(tool_calls) if tool_calls else None


def _empty_choice_delta(
    delta: object,
    *,
    finish_reason: str,
    usage: UsagePayload | None,
) -> bool:
    return not (
        getattr(delta, "content", None)
        or getattr(delta, "tool_calls", None)
        or finish_reason
        or usage is not None
    )


def _completion_delta_from_chunk(
    chunk: ChatCompletionChunk,
    config: ChatConfig,
    span: _SpanProtocol,
    *,
    prompt_request: PromptCacheRequest,
) -> CompletionDelta | None:
    if not chunk.choices:
        return _usage_delta_from_chunk(
            chunk,
            config,
            span,
            prompt_request=prompt_request,
        )
    return _choice_delta_from_chunk(chunk, config, span, prompt_request=prompt_request)


def _abort_openai_stream(
    stream: Stream[ChatCompletionChunk],
    config: ChatConfig,
    *,
    span: _SpanProtocol,
    timer: Timer,
) -> None:
    stream.close()
    _log.info(
        "stream_completion aborted",
        extra={"fields": {"model": config.model, "latency_ms": timer.ms}},
    )
    span.end()


def _handle_openai_stream_error(
    exc: Exception,
    progress: _OpenAIStreamProgress,
    *,
    attempt: int,
    retry: RetryConfig,
    span: _SpanProtocol,
    timer: Timer,
) -> None:
    partial_content = progress.partial_content
    retryable = is_retryable_error(exc)
    can_retry = retryable and not progress.saw_output and attempt < retry.max_retries
    _log_openai_stream_error(
        exc,
        partial_content=partial_content,
        attempt=attempt,
        retry=retry,
        timer=timer,
        can_retry=can_retry,
    )
    if progress.saw_output:
        _raise_stream_recovery_error(partial_content, exc, span=span)
    if can_retry:
        _record_retryable_stream_failure()
        raise _RetryOpenAIStreamError(exc) from exc
    _raise_openai_stream_engine_error(exc, retryable=retryable, span=span)


def _raise_stream_recovery_error(
    partial_content: str,
    exc: Exception,
    *,
    span: _SpanProtocol,
) -> NoReturn:
    _mark_span_error(span, "StreamRecoveryError")
    span.end()
    raise StreamRecoveryError(partial_content, exc) from exc


def _record_retryable_stream_failure() -> None:
    _circuit_breaker.record_failure()


def _raise_openai_stream_engine_error(
    exc: Exception,
    *,
    retryable: bool,
    span: _SpanProtocol,
) -> NoReturn:
    if retryable:
        _circuit_breaker.record_failure()
    _mark_span_error(span, type(exc).__name__)
    span.end()
    raise EngineError(_failure_message(exc, stream=True)) from exc


def _log_openai_stream_error(
    exc: Exception,
    *,
    partial_content: str,
    attempt: int,
    retry: RetryConfig,
    timer: Timer,
    can_retry: bool,
) -> None:
    log = _log.info if can_retry else _log.error
    log(
        "stream_completion mid-stream failure (attempt %d/%d, %d chars received)",
        attempt + 1,
        retry.max_retries + 1,
        len(partial_content),
        extra={"fields": {"error": _log_error_summary(exc), "latency_ms": timer.ms}},
    )


def _iter_openai_stream_deltas(
    stream: Stream[ChatCompletionChunk],
    config: ChatConfig,
    *,
    abort: threading.Event | None,
    span: _SpanProtocol,
    prompt_request: PromptCacheRequest,
    timer: Timer,
    attempt: int,
    retry: RetryConfig,
) -> Iterator[CompletionDelta]:
    progress = _OpenAIStreamProgress()
    try:
        for chunk in stream:
            if _completion_aborted(abort):
                _abort_openai_stream(stream, config, span=span, timer=timer)
                return

            delta = _openai_stream_delta(
                chunk,
                config,
                span,
                prompt_request=prompt_request,
            )
            if delta is None:
                continue
            progress.record(delta)
            yield delta
    except Exception as exc:
        _handle_openai_stream_error(
            exc,
            progress,
            attempt=attempt,
            retry=retry,
            span=span,
            timer=timer,
        )


def _openai_stream_delta(
    chunk: ChatCompletionChunk,
    config: ChatConfig,
    span: _SpanProtocol,
    *,
    prompt_request: PromptCacheRequest,
) -> CompletionDelta | None:
    return _completion_delta_from_chunk(chunk, config, span, prompt_request=prompt_request)


def _handle_openai_request_error(
    exc: Exception,
    *,
    attempt: int,
    retry: RetryConfig,
    abort: threading.Event | None,
    span: _SpanProtocol,
    timer: Timer,
) -> bool:
    retryable = is_retryable_error(exc)
    can_retry = retryable and attempt < retry.max_retries
    if retryable:
        _circuit_breaker.record_failure()
    _log_openai_request_error(exc, attempt=attempt, retry=retry, timer=timer, can_retry=can_retry)
    if can_retry:
        return _wait_backoff(attempt, retry, abort)
    _mark_span_error(span, type(exc).__name__)
    span.end()
    raise EngineError(_failure_message(exc, stream=False)) from exc


def _log_openai_request_error(
    exc: Exception,
    *,
    attempt: int,
    retry: RetryConfig,
    timer: Timer,
    can_retry: bool,
) -> None:
    log = _log.info if can_retry else _log.warning
    log(
        "stream_completion request failed (attempt %d/%d)",
        attempt + 1,
        retry.max_retries + 1,
        extra={"fields": {"error": _log_error_summary(exc), "latency_ms": timer.ms}},
    )


def _openai_request_allowed(abort: threading.Event | None, span: _SpanProtocol) -> bool:
    if abort is not None and abort.is_set():
        span.end()
        return False
    if not _circuit_breaker.allow_request():
        raise EngineError("LLM provider circuit breaker is open — too many recent failures")
    return True


def _start_openai_stream_attempt(
    client: OpenAI,
    config: ChatConfig,
    request: _StreamCompletionRequest,
    *,
    tools: Sequence[object] | None,
    tool_choice: object | None,
    timer: Timer,
) -> _OpenAIStreamAttempt:
    request_kwargs = _request_kwargs(
        config,
        request.api_messages,
        tools=tools,
        tool_choice=tool_choice,
    )
    with timer:
        stream = cast(
            "Stream[ChatCompletionChunk]",
            client.chat.completions.create(**request_kwargs),  # ty:ignore[no-matching-overload]
        )
    return _OpenAIStreamAttempt(stream=stream, timer=timer)


def _try_start_openai_stream_attempt(
    client: OpenAI,
    config: ChatConfig,
    request: _StreamCompletionRequest,
    *,
    tools: Sequence[object] | None,
    tool_choice: object | None,
    attempt: int,
    abort: threading.Event | None,
    retry: RetryConfig,
    span: _SpanProtocol,
) -> _OpenAIStartResult:
    timer = Timer()
    try:
        stream_attempt = _start_openai_stream_attempt(
            client,
            config,
            request,
            tools=tools,
            tool_choice=tool_choice,
            timer=timer,
        )
    except Exception as exc:
        should_continue = _handle_openai_request_error(
            exc,
            attempt=attempt,
            retry=retry,
            abort=abort,
            span=span,
            timer=timer,
        )
        return _OpenAIStartResult(attempt=None, error=exc, should_continue=should_continue)
    return _OpenAIStartResult(attempt=stream_attempt, error=None, should_continue=False)


def _required_openai_stream_attempt(result: _OpenAIStartResult) -> _OpenAIStreamAttempt:
    if result.attempt is None:
        raise EngineError("LLM stream failed before provider stream was created")
    return result.attempt


def _retry_openai_stream(
    retry_stream: _RetryOpenAIStreamError,
    *,
    attempt: int,
    retry: RetryConfig,
    abort: threading.Event | None,
) -> Exception | None:
    if _wait_backoff(attempt, retry, abort):
        return retry_stream.cause
    return None


def _raise_openai_attempts_failed(
    retry: RetryConfig,
    last_error: Exception | None,
    span: _SpanProtocol,
) -> None:
    _mark_span_error(span, "EngineError")
    span.end()
    message = (
        _failure_message(last_error, stream=False)
        if last_error is not None
        else f"LLM request failed after {retry.max_retries + 1} attempts"
    )
    raise EngineError(message) from last_error


def _stream_completion_request(
    config: ChatConfig,
    messages: Conversation | list[ApiMessage],
    tools: Sequence[object] | None,
) -> _StreamCompletionRequest:
    raw_api_messages = (
        messages.to_api_messages() if isinstance(messages, Conversation) else messages
    )
    prompt_request = _prompt_cache_builder.build_request(raw_api_messages)
    prompt_request = annotate_anthropic_cache_breakpoints(prompt_request, config.model)
    _prompt_cache_metrics.record_request(prompt_request, model=config.model)
    return _StreamCompletionRequest(
        api_messages=prompt_request.messages,
        prompt_request=prompt_request,
        message_count=len(prompt_request.messages),
        tool_count=len(tools or []),
    )


def _configure_completion_span(
    span: _SpanProtocol,
    config: ChatConfig,
    request: _StreamCompletionRequest,
) -> None:
    span.set_attribute("gen_ai.system", config.provider_slug or "unknown")
    span.set_attribute("gen_ai.request.model", config.model)
    span.set_attribute("gen_ai.request.max_tokens", config.max_tokens)
    span.set_attribute(
        "gen_ai.request.stable_prefix_hash",
        request.prompt_request.stable_prefix.fingerprint,
    )
    span.set_attribute(
        "gen_ai.request.stable_prefix_messages",
        request.prompt_request.stable_prefix.message_count,
    )
    span.set_attribute(
        "gen_ai.request.dynamic_tail_messages",
        request.prompt_request.dynamic_tail.message_count,
    )


def _log_stream_completion_start(
    config: ChatConfig,
    request: _StreamCompletionRequest,
    retry: RetryConfig,
) -> None:
    _log.debug(
        "stream_completion start",
        extra={
            "fields": {
                "model": config.model,
                "message_count": request.message_count,
                "max_tokens": config.max_tokens,
                "max_retries": retry.max_retries,
                "tool_count": request.tool_count,
            }
        },
    )


def _finish_successful_stream_completion(
    config: ChatConfig,
    request: _StreamCompletionRequest,
    *,
    timer: Timer,
    span: _SpanProtocol,
) -> None:
    _log.info(
        "stream_completion complete",
        extra={
            "fields": {
                "model": config.model,
                "latency_ms": timer.ms,
                "message_count": request.message_count,
                "tool_count": request.tool_count,
            }
        },
    )
    _circuit_breaker.record_success()
    span.set_attribute("gen_ai.response.latency_ms", timer.ms)
    _llm_duration_hist.record(timer.ms, {"model": config.model})
    span.end()


def _iter_openai_completion_attempts(
    config: ChatConfig,
    request: _StreamCompletionRequest,
    *,
    tools: Sequence[object] | None,
    abort: threading.Event | None,
    retry: RetryConfig,
    client_factory: Callable[[ChatConfig], OpenAI],
    tool_choice: object | None,
    span: _SpanProtocol,
) -> Iterator[CompletionDelta]:
    client = client_factory(config)
    last_error: Exception | None = None

    for attempt in range(retry.max_retries + 1):
        attempt_result = yield from _iter_openai_completion_attempt(
            client,
            config,
            request,
            tools=tools,
            tool_choice=tool_choice,
            attempt=attempt,
            abort=abort,
            retry=retry,
            span=span,
        )
        last_error = attempt_result.error or last_error
        if attempt_result.retry:
            continue
        if attempt_result.done:
            return

    _raise_openai_attempts_failed(retry, last_error, span)


def _iter_openai_completion_attempt(
    client: OpenAI,
    config: ChatConfig,
    request: _StreamCompletionRequest,
    *,
    tools: Sequence[object] | None,
    tool_choice: object | None,
    attempt: int,
    abort: threading.Event | None,
    retry: RetryConfig,
    span: _SpanProtocol,
) -> Generator[CompletionDelta, None, _OpenAICompletionAttemptResult]:
    if not _openai_request_allowed(abort, span):
        return _OpenAICompletionAttemptResult(done=True)

    start_result = _try_start_openai_stream_attempt(
        client,
        config,
        request,
        tools=tools,
        tool_choice=tool_choice,
        attempt=attempt,
        abort=abort,
        retry=retry,
        span=span,
    )
    if start_result.should_continue:
        return _OpenAICompletionAttemptResult(done=False, retry=True, error=start_result.error)
    if start_result.should_stop:
        return _OpenAICompletionAttemptResult(done=True, error=start_result.error)

    stream_attempt = _required_openai_stream_attempt(start_result)
    try:
        yield from _iter_started_openai_stream_attempt(
            stream_attempt,
            config,
            request,
            abort=abort,
            span=span,
            attempt=attempt,
            retry=retry,
        )
    except _RetryOpenAIStreamError as retry_stream:
        error = _retry_openai_stream(retry_stream, attempt=attempt, retry=retry, abort=abort)
        return _OpenAICompletionAttemptResult(
            done=error is None,
            retry=error is not None,
            error=error,
        )

    _finish_successful_stream_completion(config, request, timer=stream_attempt.timer, span=span)
    return _OpenAICompletionAttemptResult(done=True)


def _iter_started_openai_stream_attempt(
    stream_attempt: _OpenAIStreamAttempt,
    config: ChatConfig,
    request: _StreamCompletionRequest,
    *,
    abort: threading.Event | None,
    span: _SpanProtocol,
    attempt: int,
    retry: RetryConfig,
) -> Iterator[CompletionDelta]:
    yield from _iter_openai_stream_deltas(
        stream_attempt.stream,
        config,
        abort=abort,
        span=span,
        prompt_request=request.prompt_request,
        timer=stream_attempt.timer,
        attempt=attempt,
        retry=retry,
    )


def stream_completion(
    config: ChatConfig,
    messages: Conversation | list[ApiMessage],
    *,
    tools: Sequence[object] | None = None,
    abort: threading.Event | None = None,
    retry: RetryConfig | None = None,
    client_factory: Callable[[ChatConfig], OpenAI] | None = None,
    tool_choice: object | None = None,
) -> Iterator[CompletionDelta]:
    span = _tracer.start_span("llm.completion")
    retry = retry or RetryConfig()
    client_factory = client_factory or build_client
    request = _stream_completion_request(config, messages, tools)
    _configure_completion_span(span, config, request)
    _log_stream_completion_start(config, request, retry)

    codex_auth = _codex_backend_auth(config)
    if codex_auth is not None:
        yield from _stream_codex_completion(
            config,
            request.api_messages,
            codex_auth,
            abort=abort,
            span=span,
            prompt_request=request.prompt_request,
            message_count=request.message_count,
            tool_count=request.tool_count,
        )
        return
    if config.provider_slug == "openai-codex":
        span.end()
        raise EngineError(
            "OpenAI Codex subscription requires /login OAuth credentials. "
            "Use the OpenAI API provider for OPENAI_API_KEY billing."
        )

    yield from _iter_openai_completion_attempts(
        config,
        request,
        tools=tools,
        abort=abort,
        retry=retry,
        client_factory=client_factory,
        tool_choice=tool_choice,
        span=span,
    )


def stream_reply(
    config: ChatConfig,
    conversation: Conversation,
    *,
    abort: threading.Event | None = None,
    retry: RetryConfig | None = None,
) -> Iterator[str]:
    for delta in stream_completion(
        config,
        conversation,
        abort=abort,
        retry=retry,
        client_factory=build_client,
    ):
        if delta.content:
            yield delta.content


def get_reply(
    config: ChatConfig,
    conversation: Conversation,
    *,
    abort: threading.Event | None = None,
    retry: RetryConfig | None = None,
) -> str:
    parts: list[str] = []
    try:
        for chunk in stream_reply(config, conversation, abort=abort, retry=retry):
            sys.stdout.write(chunk)
            sys.stdout.flush()
            parts.append(chunk)
    except StreamRecoveryError:
        if parts:
            sys.stdout.write("\n")
            sys.stdout.flush()
        raise
    sys.stdout.write("\n")
    sys.stdout.flush()
    return "".join(parts)
