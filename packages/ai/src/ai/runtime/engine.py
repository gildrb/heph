"""Shared LLM communication runtime with streaming support.

Supports any OpenAI-compatible API endpoint, making it LLM-agnostic.
Configure via environment variables:
    HARNESS_API_KEY   - API key override (applies to any provider)
    HARNESS_BASE_URL  - Base URL for the API
    HARNESS_MODEL     - Model name

Streaming error recovery:
    Transient failures (connection drops, timeouts, server errors) are
    retried automatically with exponential backoff.  If a retry fails
    after content has already been streamed to the caller, a
    ``StreamRecoveryError`` is raised carrying the partial response so
    that the caller can decide how to proceed.
"""

from __future__ import annotations

import contextlib
import os
import random
import re
import sys
import threading
import time
from collections.abc import Callable, Generator, Iterator, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, NoReturn, Protocol, cast

from ai.diagnostics import get_meter, get_tracer
from ai.logging import Timer, get_logger, redact_text
from ai.providers.endpoints import provider_uses_keyless_access
from ai.providers.model_support import is_supported_model_for_endpoint
from ai.providers.oauth import load_credentials
from ai.providers.registry import get_registry as get_provider_registry
from ai.runtime._api_types import ApiMessage, ToolCallDelta, UsagePayload
from ai.runtime.codex_backend import (
    codex_backend_auth,
    stream_codex_backend_completion,
)
from ai.runtime.config import ChatConfig, resolve_key
from ai.runtime.conversation import Conversation
from ai.runtime.delta import CompletionDelta
from ai.runtime.errors import (
    EngineError,
    EngineErrorCode,
    RetryConfig,
    StreamRecoveryError,
    _RetryOpenAIStreamError,
)
from ai.runtime.prompt_cache import (
    MetricsLogger as PromptCacheMetricsLogger,
)
from ai.runtime.prompt_cache import PromptCacheRequest, StablePrefixBuilder
from ai.runtime.request_payload import request_kwargs as build_request_kwargs
from ai.runtime.resilience import CircuitBreaker
from ai.runtime.tool_deltas import normalize_tool_calls
from ai.runtime.usage_payload import extract_usage
from ai.types import is_string_mapping

if TYPE_CHECKING:
    from openai import OpenAI, Stream
    from openai.types.chat import ChatCompletionChunk


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


_log = get_logger("ai.runtime.engine")
_COMPAT_EXPORTS = (resolve_key,)
_prompt_cache_builder = StablePrefixBuilder()
_prompt_cache_metrics = PromptCacheMetricsLogger()

_tracer: _TracerProtocol = get_tracer("ai.runtime.engine")  # ty:ignore[invalid-assignment]
_meter: _MeterProtocol = get_meter("ai.runtime.engine")

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
_ACCOUNT_SETUP_HINT = "Configure provider credentials and select an available model."
_PROVIDER_CAPACITY_ERROR_TERMS = ("queue full",)
_PROVIDER_CAPACITY_HINT = (
    "The free model provider is busy or rate-limiting this connection. "
    "Try again shortly, or configure a different provider and model."
)
_CODEX_BACKEND_RESPONSES_URL = "https://chatgpt.com/backend-api/codex/responses"
_CODEX_BACKEND_TIMEOUT_SECONDS = 30
_OPENAI_COMPAT_TIMEOUT_SECONDS = 120.0
_OPENAI_STREAM_PROGRESS_TIMEOUT_SECONDS = 120.0
_PROVIDER_IP_RE = re.compile(r"\bIP:\s*(?:\d{1,3}\.){3}\d{1,3}\b", re.IGNORECASE)
_MAX_PROVIDER_DETAIL_CHARS = 260


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


def _monotonic() -> float:
    return time.monotonic()


@dataclass(slots=True)
class _OpenAIStreamProgress:
    partial_parts: list[str] = field(default_factory=list)
    saw_output: bool = False
    last_useful_delta_at: float = field(default_factory=_monotonic)

    def record(self, delta: CompletionDelta) -> None:
        if delta.content:
            self.partial_parts.append(delta.content)
        # Reasoning deltas are progress only; answer-safe retries are still possible.
        if delta.content or delta.tool_calls:
            self.saw_output = True
            self.last_useful_delta_at = time.monotonic()
        if delta.finish_reason:
            self.last_useful_delta_at = time.monotonic()

    @property
    def partial_content(self) -> str:
        return "".join(self.partial_parts)


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


def _failure_message_and_code(
    exc: Exception,
    *,
    stream: bool,
) -> tuple[str, EngineErrorCode | None]:
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
        return (
            _with_hint(f"{account_prefix}: {detail}", _ACCOUNT_SETUP_HINT),
            EngineErrorCode.ACCOUNT_SETUP,
        )
    if _is_provider_capacity_error(exc):
        return (
            _with_hint(f"{capacity_prefix}: {detail}", _PROVIDER_CAPACITY_HINT),
            EngineErrorCode.PROVIDER_CAPACITY,
        )
    return f"{default_prefix}: {detail}", None


def _failure_error(exc: Exception, *, stream: bool) -> EngineError:
    message, code = _failure_message_and_code(exc, stream=stream)
    return EngineError(message, code=code)


def _log_error_summary(exc: Exception) -> str:
    if _is_account_setup_error(exc):
        detail, code = _provider_error_fields(exc)
        return f"{code}: {detail}" if code else detail
    return str(exc)


def build_client(config: ChatConfig) -> OpenAI:
    from openai import OpenAI

    if not config.base_url:
        raise EngineError("No model source configured.", code=EngineErrorCode.MISSING_MODEL_SOURCE)
    if not config.model:
        raise EngineError("No model configured.", code=EngineErrorCode.MISSING_MODEL)
    if not is_supported_model_for_endpoint(config.model, config.base_url):
        raise EngineError(
            f"Model unavailable for endpoint: {config.model}",
            code=EngineErrorCode.MODEL_UNAVAILABLE,
        )
    return OpenAI(
        api_key=_api_key_for_config(config),
        base_url=config.base_url,
        timeout=_openai_compat_timeout_seconds(),
    )


def _positive_env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    with contextlib.suppress(ValueError):
        value = float(raw)
        if value > 0:
            return value
    return default


def _openai_compat_timeout_seconds() -> float:
    return _positive_env_float(
        "HARNESS_OPENAI_TIMEOUT_SECONDS",
        _OPENAI_COMPAT_TIMEOUT_SECONDS,
    )


def _openai_stream_progress_timeout_seconds() -> float:
    return _positive_env_float(
        "HARNESS_STREAM_PROGRESS_TIMEOUT_SECONDS",
        _OPENAI_STREAM_PROGRESS_TIMEOUT_SECONDS,
    )


def _api_key_for_config(config: ChatConfig) -> str:
    if provider_uses_keyless_access(config.provider_slug, config.base_url):
        return "no-key-required"
    if config.resolved_api_key:
        return config.resolved_api_key
    raise EngineError(missing_api_key_message(config), code=EngineErrorCode.MISSING_CREDENTIALS)


def missing_api_key_message(config: ChatConfig) -> str:
    if config.provider_slug == "openai-codex":
        return (
            "OpenAI Codex subscription requires OAuth credentials. "
            "Use the OpenAI API provider for API-key billing."
        )
    model_info = get_provider_registry().get(config.model)
    if model_info is not None and model_info.is_free:
        return (
            f"{config.model} is free-priced, but {model_info.display_name} is served through "
            "a provider that still requires credentials."
        )
    return "No API key found. Configure provider credentials or set an environment variable."


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


def has_configured_access(config: ChatConfig, *, refresh_oauth: bool = True) -> bool:
    if provider_uses_keyless_access(config.provider_slug, config.base_url):
        return True
    if config.provider_slug == "openai-codex":
        return load_credentials("openai-codex", refresh_expired=refresh_oauth) is not None
    return bool(config.resolved_api_key)


def _completion_aborted(abort: threading.Event | None) -> bool:
    return abort is not None and abort.is_set()


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
        raise EngineError(
            "LLM provider circuit breaker is open - too many recent failures",
            code=EngineErrorCode.CIRCUIT_OPEN,
        )

    timer = Timer()
    try:
        with timer:
            yield from stream_codex_backend_completion(
                config,
                api_messages,
                auth,
                abort=abort,
                span=span,
                prompt_request=prompt_request,
                record_usage=_record_usage,
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


def _usage_delta_from_chunk(
    chunk: ChatCompletionChunk,
    config: ChatConfig,
    span: _SpanProtocol,
    *,
    prompt_request: PromptCacheRequest,
) -> CompletionDelta | None:
    usage = extract_usage(chunk)
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
    usage = extract_usage(chunk)
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
        reasoning=_choice_delta_reasoning(delta),
        reasoning_summary=_choice_delta_reasoning_summary(delta),
        tool_calls=_choice_delta_tool_calls(delta),
        finish_reason=finish_reason,
        usage=usage,
    )


def _choice_delta_content(delta: object) -> str | None:
    return _first_string_attr(delta, ("content",))


def _choice_delta_reasoning(delta: object) -> str | None:
    return _first_string_attr(delta, ("reasoning_content", "reasoning"))


def _choice_delta_reasoning_summary(delta: object) -> str | None:
    return _first_string_attr(delta, ("reasoning_summary",))


def _first_string_attr(delta: object, names: tuple[str, ...]) -> str | None:
    for name in names:
        value = getattr(delta, name, None)
        if isinstance(value, str) and value:
            return value
    return None


def _choice_delta_tool_calls(delta: object) -> list[ToolCallDelta] | None:
    tool_calls = getattr(delta, "tool_calls", None)
    return normalize_tool_calls(tool_calls) if tool_calls else None


def _empty_choice_delta(
    delta: object,
    *,
    finish_reason: str,
    usage: UsagePayload | None,
) -> bool:
    return not (
        _choice_delta_content(delta)
        or _choice_delta_reasoning(delta)
        or _choice_delta_reasoning_summary(delta)
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
    raise _failure_error(exc, stream=True) from exc


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
    progress_timeout = _openai_stream_progress_timeout_seconds()
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
                _raise_if_openai_stream_stalled(
                    progress,
                    progress_timeout=progress_timeout,
                )
                continue
            progress.record(delta)
            yield delta
            _raise_if_openai_stream_stalled(
                progress,
                progress_timeout=progress_timeout,
            )
    except Exception as exc:
        _handle_openai_stream_error(
            exc,
            progress,
            attempt=attempt,
            retry=retry,
            span=span,
            timer=timer,
        )


def _raise_if_openai_stream_stalled(
    progress: _OpenAIStreamProgress,
    *,
    progress_timeout: float,
) -> None:
    elapsed = time.monotonic() - progress.last_useful_delta_at
    if elapsed < progress_timeout:
        return
    raise EngineError(
        "LLM stream stalled without answer or tool-call progress "
        f"for {progress_timeout:g} second(s)."
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
    raise _failure_error(exc, stream=False) from exc


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
        raise EngineError(
            "LLM provider circuit breaker is open - too many recent failures",
            code=EngineErrorCode.CIRCUIT_OPEN,
        )
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
    kwargs = build_request_kwargs(
        config,
        request.api_messages,
        tools=tools,
        tool_choice=tool_choice,
    )
    with timer:
        stream = cast(
            "Stream[ChatCompletionChunk]",
            client.chat.completions.create(**kwargs),  # ty:ignore[no-matching-overload]
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
    if last_error is not None:
        raise _failure_error(last_error, stream=False) from last_error
    raise EngineError(f"LLM request failed after {retry.max_retries + 1} attempts")


def _stream_completion_request(
    config: ChatConfig,
    messages: Conversation | list[ApiMessage],
    tools: Sequence[object] | None,
) -> _StreamCompletionRequest:
    raw_api_messages = (
        messages.to_api_messages() if isinstance(messages, Conversation) else messages
    )
    prompt_request = _prompt_cache_builder.build_request(raw_api_messages)
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

    codex_auth = codex_backend_auth(config)
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
            "OpenAI Codex subscription requires OAuth credentials. "
            "Use the OpenAI API provider for API-key billing.",
            code=EngineErrorCode.MISSING_CREDENTIALS,
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
