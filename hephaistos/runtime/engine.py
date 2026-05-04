"""Shared LLM communication runtime with streaming support.

Supports any OpenAI-compatible API endpoint, making it LLM-agnostic.
Configure via environment variables:
    HEPHAISTOS_API_KEY   - API key override (applies to any provider)
    HEPHAISTOS_BASE_URL  - Base URL for the API
    HEPHAISTOS_MODEL     - Model name

Streaming error recovery:
    Transient failures (connection drops, timeouts, server errors) are
    retried automatically with exponential backoff.  If a retry fails
    after content has already been streamed to the caller, a
    ``StreamRecoveryError`` is raised carrying the partial response so
    that the caller can decide how to proceed.
"""

from __future__ import annotations

import random
import sys
import threading
import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from typing import Protocol, cast

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
    Stream,
)
from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall

from hephaistos._types import is_string_mapping
from hephaistos.logging import Timer, get_logger, redact_text
from hephaistos.observability import get_meter, get_tracer
from hephaistos.providers.endpoints import is_keyless_endpoint
from hephaistos.providers.keyring_store import resolve_key
from hephaistos.providers.model_support import is_supported_model_for_endpoint
from hephaistos.providers.registry import get_registry as get_provider_registry
from hephaistos.runtime._api_types import ApiMessage, ToolCallDelta, UsagePayload
from hephaistos.runtime.resilience import CircuitBreaker


class _SpanProtocol(Protocol):
    def set_attribute(self, key: str, value: object) -> object: ...

    def end(self, _end_time: float | None = None) -> None: ...


class _TracerProtocol(Protocol):
    def start_span(self, name: str, **kwargs: object) -> _SpanProtocol: ...


class _CounterProtocol(Protocol):
    def add(self, value: float, _attributes: dict[str, str] | None = None) -> None: ...


class _HistogramProtocol(Protocol):
    def record(self, value: float, _attributes: dict[str, str] | None = None) -> None: ...


class _MeterProtocol(Protocol):
    def create_histogram(self, name: str, **kwargs: object) -> _HistogramProtocol: ...

    def create_counter(self, name: str, **kwargs: object) -> _CounterProtocol: ...


_log = get_logger("runtime.engine")

_tracer: _TracerProtocol = get_tracer("runtime.engine")  # type: ignore[reportAssignmentType]
_meter: _MeterProtocol = get_meter("runtime.engine")  # type: ignore[reportAssignmentType]

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
    feature_flags: frozenset[str] = field(default_factory=frozenset)
    _provider_slug: str = field(default="", repr=False)
    _provider_env: str = field(default="", repr=False)

    def is_feature_enabled(self, flag: str) -> bool:
        return flag in self.feature_flags

    @property
    def provider_slug(self) -> str:
        """Public read-only accessor for the active provider slug."""
        return self._provider_slug

    @property
    def resolved_api_key(self) -> str:
        """Resolve the API key via keychain → env → volatile."""
        if self._provider_slug:
            if not self._provider_env:
                return self.api_key
            return resolve_key(self._provider_slug, self._provider_env)
        return self.api_key

    def apply_provider_reference(self, slug: str, env_var: str) -> None:
        self._provider_slug = slug
        self._provider_env = env_var


class EngineError(Exception):
    """Raised when the engine cannot communicate with the LLM."""


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


@dataclass
class RetryConfig:
    """Configuration for automatic retry of transient failures."""

    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds


@dataclass
class _RetryableTypesCache:
    value: tuple[type[Exception], ...] | None = None


_retryable_types_cache = _RetryableTypesCache()


def _get_retryable_types() -> tuple[type[Exception], ...]:
    retryable_types = _retryable_types_cache.value
    if retryable_types is None:
        retryable_types = (
            APIConnectionError,
            APITimeoutError,
            InternalServerError,
            RateLimitError,
        )
        _retryable_types_cache.value = retryable_types
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


@dataclass
class Message:
    """A single message in a conversation."""

    role: str  # "system", "user", or "assistant"
    content: str


@dataclass
class Conversation:
    """An ordered list of messages forming a conversation."""

    messages: list[Message] = field(default_factory=list)
    _api_cache: list[ApiMessage] | None = field(default=None, init=False, repr=False)

    def add(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))
        self._api_cache = None

    def to_api_messages(self) -> list[ApiMessage]:
        """Convert to the format expected by the OpenAI client."""
        if self._api_cache is not None:
            return self._api_cache
        self._api_cache = [{"role": msg.role, "content": msg.content} for msg in self.messages]
        return self._api_cache


def to_chat_completion_messages(messages: list[ApiMessage]) -> list[ChatCompletionMessageParam]:
    """Cast validated local API messages to the SDK request type."""
    return cast("list[ChatCompletionMessageParam]", messages)


def _provider_error_fields(exc: Exception) -> tuple[str, str]:
    """Return a short provider error message and code without SDK noise."""
    body = getattr(exc, "body", None)
    code = ""
    message = ""

    if is_string_mapping(body):
        data = body
        error_val = data.get("error", data)
        if is_string_mapping(error_val):
            raw_code = error_val.get("code") or error_val.get("type") or data.get("code")
            raw_message = error_val.get("message") or data.get("message")
        else:
            raw_code = data.get("code")
            raw_message = data.get("message") or error_val
        code = str(raw_code or "").strip()
        message = str(raw_message or "").strip()

    if not message:
        message = str(getattr(exc, "message", "") or exc).strip()
    if not code:
        code = str(getattr(exc, "code", "") or "").strip()
    return message or exc.__class__.__name__, code


def _is_account_setup_error(exc: Exception) -> bool:
    """Return True when retrying cannot fix the provider/account state."""
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


def _with_hint(message: str, hint: str) -> str:
    message = message.rstrip()
    if message and message[-1] not in ".!?":
        message += "."
    return f"{message} {hint}"


def _request_failure_message(exc: Exception) -> str:
    """Build a user-facing request failure message."""
    detail, _code = _provider_error_fields(exc)
    detail = redact_text(detail)
    if _is_account_setup_error(exc):
        return _with_hint(f"Provider rejected the request: {detail}", _ACCOUNT_SETUP_HINT)
    return f"LLM request failed: {detail}"


def _stream_failure_message(exc: Exception) -> str:
    """Build a user-facing streaming failure message."""
    detail, _code = _provider_error_fields(exc)
    detail = redact_text(detail)
    if _is_account_setup_error(exc):
        return _with_hint(f"Provider rejected the stream: {detail}", _ACCOUNT_SETUP_HINT)
    return f"LLM stream failed: {detail}"


def _log_error_summary(exc: Exception) -> str:
    """Return a compact log summary for expected provider setup failures."""
    if _is_account_setup_error(exc):
        detail, code = _provider_error_fields(exc)
        return f"{code}: {detail}" if code else detail
    return str(exc)


def build_client(config: ChatConfig) -> OpenAI:
    """Create an OpenAI client from the given config."""
    if not config.base_url:
        raise EngineError("No model source configured. Use /login, then /models.")
    if not config.model:
        raise EngineError("No model configured. Use /models to select one.")
    if not is_supported_model_for_endpoint(config.model, config.base_url):
        raise EngineError(f"Model unavailable for endpoint: {config.model}")
    if is_keyless_endpoint(config.base_url):
        api_key = "no-key-required"
    else:
        api_key = config.resolved_api_key
        if not api_key:
            raise EngineError(missing_api_key_message(config))
    return OpenAI(api_key=api_key, base_url=config.base_url)


def missing_api_key_message(config: ChatConfig) -> str:
    """Return a precise missing-key message for the active provider/model."""
    model_info = get_provider_registry().get(config.model)
    if model_info is not None and model_info.is_free:
        return (
            f"{config.model} is free-priced, but {model_info.display_name} is served through "
            "a provider that still requires an API key. Use /login or set an environment "
            "variable."
        )
    return "No API key found. Use /login or set an environment variable."


def is_retryable_error(exc: Exception) -> bool:
    """Return True if *exc* is a transient error worth retrying."""
    if _is_account_setup_error(exc):
        return False
    return isinstance(exc, _get_retryable_types())


def _wait_backoff(
    attempt: int,
    config: RetryConfig,
    abort: threading.Event | None = None,
) -> bool:
    """Sleep with exponential backoff + jitter.  Returns False if aborted."""
    delay = min(config.base_delay * (2**attempt), config.max_delay)
    jitter = random.uniform(0, delay * 0.5)
    if abort is not None:
        return not abort.wait(timeout=jitter)
    time.sleep(jitter)
    return True


@dataclass(frozen=True, slots=True)
class CompletionDelta:
    """A streamed completion delta from the model."""

    content: str | None = None
    tool_calls: list[ToolCallDelta] | None = None
    finish_reason: str = ""
    usage: UsagePayload | None = None


def _normalize_tool_calls(tool_calls: list[ChoiceDeltaToolCall]) -> list[ToolCallDelta]:
    """Convert SDK tool-call delta objects to plain typed dicts."""
    result: list[ToolCallDelta] = []
    for tc in tool_calls:
        tool_call: ToolCallDelta = {}
        tool_call["index"] = tc.index
        if tc.id:
            tool_call["id"] = tc.id
        if tc.type:
            tool_call["type"] = str(tc.type)
        if tc.function is not None:
            tool_call["function"] = {
                "name": tc.function.name or "",
                "arguments": tc.function.arguments or "",
            }
        result.append(tool_call)
    return result


def _extract_usage(chunk: object) -> UsagePayload | None:
    usage = getattr(chunk, "usage", None)
    if not usage:
        return None
    return {
        "prompt_tokens": (getattr(usage, "prompt_tokens", 0) or 0),
        "completion_tokens": (getattr(usage, "completion_tokens", 0) or 0),
        "total_tokens": (getattr(usage, "total_tokens", 0) or 0),
    }


def _record_usage(usage: UsagePayload, model: str, span: _SpanProtocol) -> None:
    """Record token usage metrics and span attributes."""
    prompt = usage.get("prompt_tokens", 0) or 0
    completion = usage.get("completion_tokens", 0) or 0
    span.set_attribute("gen_ai.response.prompt_tokens", prompt)
    span.set_attribute("gen_ai.response.completion_tokens", completion)
    _llm_token_counter.add(prompt, {"model": model, "type": "prompt"})
    _llm_token_counter.add(completion, {"model": model, "type": "completion"})


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
    """Stream raw completion deltas with shared retry/recovery handling."""
    span = _tracer.start_span("llm.completion")
    span.set_attribute("gen_ai.system", config.provider_slug or "unknown")
    span.set_attribute("gen_ai.request.model", config.model)
    span.set_attribute("gen_ai.request.max_tokens", config.max_tokens)
    retry = retry or RetryConfig()
    client_factory = client_factory or build_client
    api_messages = messages.to_api_messages() if isinstance(messages, Conversation) else messages
    msg_count = len(api_messages)
    _log.debug(
        "stream_completion start",
        extra={
            "fields": {
                "model": config.model,
                "message_count": msg_count,
                "max_tokens": config.max_tokens,
                "max_retries": retry.max_retries,
                "tool_count": len(tools or []),
            }
        },
    )

    client = client_factory(config)
    last_error: Exception | None = None

    for attempt in range(retry.max_retries + 1):
        if abort is not None and abort.is_set():
            span.end()
            return

        if not _circuit_breaker.allow_request():
            raise EngineError("LLM provider circuit breaker is open — too many recent failures")

        timer = Timer()
        request_kwargs: dict[str, object] = {
            "model": config.model,
            "messages": to_chat_completion_messages(api_messages),
            "max_tokens": config.max_tokens,
            "stream": True,
        }
        if tools:
            request_kwargs["tools"] = list(tools)
            if tool_choice is not None:
                request_kwargs["tool_choice"] = tool_choice

        try:
            with timer:
                stream = cast(
                    "Stream[ChatCompletionChunk]",
                    client.chat.completions.create(**request_kwargs),  # type: ignore[call-overload]
                )
        except Exception as exc:
            last_error = exc
            if is_retryable_error(exc):
                _circuit_breaker.record_failure()
            log = (
                _log.info
                if is_retryable_error(exc) and attempt < retry.max_retries
                else _log.warning
            )
            log(
                "stream_completion request failed (attempt %d/%d)",
                attempt + 1,
                retry.max_retries + 1,
                extra={"fields": {"error": _log_error_summary(exc), "latency_ms": timer.ms}},
            )
            if is_retryable_error(exc) and attempt < retry.max_retries:
                if not _wait_backoff(attempt, retry, abort):
                    return
                continue
            span.set_attribute("error", True)
            span.set_attribute("error.type", type(exc).__name__)
            span.end()
            raise EngineError(_request_failure_message(exc)) from exc

        partial_parts: list[str] = []
        saw_output = False
        try:
            for chunk in stream:
                if abort is not None and abort.is_set():
                    stream.close()
                    _log.info(
                        "stream_completion aborted",
                        extra={
                            "fields": {
                                "model": config.model,
                                "latency_ms": timer.ms,
                            }
                        },
                    )
                    span.end()
                    return

                usage = _extract_usage(chunk)
                if not chunk.choices:
                    if usage is not None:
                        _record_usage(usage, config.model, span)
                        yield CompletionDelta(usage=usage)
                    continue

                choice = chunk.choices[0]
                delta = choice.delta
                finish_reason = choice.finish_reason or ""
                if delta.content:
                    partial_parts.append(delta.content)
                if delta.content or delta.tool_calls:
                    saw_output = True
                if delta.content or delta.tool_calls or finish_reason or usage is not None:
                    if usage is not None:
                        _record_usage(usage, config.model, span)
                    yield CompletionDelta(
                        content=delta.content or None,
                        tool_calls=(
                            _normalize_tool_calls(delta.tool_calls) if delta.tool_calls else None
                        ),
                        finish_reason=finish_reason,
                        usage=usage,
                    )
        except Exception as exc:
            partial_content = "".join(partial_parts)
            log = (
                _log.info
                if is_retryable_error(exc) and not saw_output and attempt < retry.max_retries
                else _log.error
            )
            log(
                "stream_completion mid-stream failure (attempt %d/%d, %d chars received)",
                attempt + 1,
                retry.max_retries + 1,
                len(partial_content),
                extra={"fields": {"error": _log_error_summary(exc), "latency_ms": timer.ms}},
            )
            if saw_output:
                span.set_attribute("error", True)
                span.set_attribute("error.type", "StreamRecoveryError")
                span.end()
                raise StreamRecoveryError(partial_content, exc) from exc
            last_error = exc
            if is_retryable_error(exc):
                _circuit_breaker.record_failure()
            if is_retryable_error(exc) and attempt < retry.max_retries:
                if not _wait_backoff(attempt, retry, abort):
                    return
                continue
            span.set_attribute("error", True)
            span.set_attribute("error.type", type(exc).__name__)
            span.end()
            raise EngineError(_stream_failure_message(exc)) from exc

        _log.info(
            "stream_completion complete",
            extra={
                "fields": {
                    "model": config.model,
                    "latency_ms": timer.ms,
                    "message_count": msg_count,
                    "tool_count": len(tools or []),
                }
            },
        )
        _circuit_breaker.record_success()
        span.set_attribute("gen_ai.response.latency_ms", timer.ms)
        _llm_duration_hist.record(timer.ms, {"model": config.model})
        span.end()
        return

    span.set_attribute("error", True)
    span.end()
    raise EngineError(
        _request_failure_message(last_error)
        if last_error is not None
        else f"LLM request failed after {retry.max_retries + 1} attempts"
    ) from last_error


def stream_reply(
    config: ChatConfig,
    conversation: Conversation,
    *,
    abort: threading.Event | None = None,
    retry: RetryConfig | None = None,
) -> Iterator[str]:
    """Send the conversation to the LLM and yield response chunks."""
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
    """Send the conversation and return the full reply as a string.

    Also prints streamed chunks to stdout in real time.
    On :class:`StreamRecoveryError` the partial text is preserved in the
    exception for the caller to inspect.
    """
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
