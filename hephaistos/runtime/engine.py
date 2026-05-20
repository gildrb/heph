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

import contextlib
import json
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol, cast

from hephaistos._types import is_string_mapping
from hephaistos.diagnostics.crashes import get_meter, get_tracer
from hephaistos.logging import Timer, get_logger, redact_text
from hephaistos.providers.endpoints import is_keyless_endpoint
from hephaistos.providers.keyring_store import resolve_key
from hephaistos.providers.model_support import is_supported_model_for_endpoint
from hephaistos.providers.oauth import load_credentials
from hephaistos.providers.registry import get_registry as get_provider_registry
from hephaistos.runtime._api_types import ApiMessage, ToolCallDelta, UsagePayload
from hephaistos.runtime.messages import message_content_text
from hephaistos.runtime.prompt_cache import (
    MetricsLogger as PromptCacheMetricsLogger,
)
from hephaistos.runtime.prompt_cache import (
    PromptCacheRequest,
    StablePrefixBuilder,
    annotate_anthropic_cache_breakpoints,
)
from hephaistos.runtime.resilience import CircuitBreaker

if TYPE_CHECKING:
    from openai import OpenAI, Stream
    from openai.types.chat import ChatCompletionChunk, ChatCompletionMessageParam
    from openai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall


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


def to_chat_completion_messages(messages: list[ApiMessage]) -> list[ChatCompletionMessageParam]:
    return cast("list[ChatCompletionMessageParam]", messages)


def _provider_error_fields(exc: Exception) -> tuple[str, str]:
    body = getattr(exc, "body", None)
    if not is_string_mapping(body):
        response = getattr(exc, "response", None)
        json_fn = getattr(response, "json", None)
        if callable(json_fn):
            try:
                response_body = json_fn()
            except Exception:
                response_body = None
            body = response_body if is_string_mapping(response_body) else None
        else:
            body = None
    code = ""
    message = ""

    if body is not None:
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
    if is_keyless_endpoint(config.base_url):
        api_key = "no-key-required"
    else:
        api_key = config.resolved_api_key
        if not api_key:
            raise EngineError(missing_api_key_message(config))
    return OpenAI(api_key=api_key, base_url=config.base_url)


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


def _optional_int_value(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _cached_tokens_from_usage_details(details: object) -> int | None:
    if is_string_mapping(details):
        return _optional_int_value(details.get("cached_tokens"))
    return _optional_int_value(getattr(details, "cached_tokens", None))


def _cached_prompt_tokens_from_usage(usage: object) -> int | None:
    for name in ("prompt_tokens_details", "input_tokens_details"):
        cached_tokens = _cached_tokens_from_usage_details(getattr(usage, name, None))
        if cached_tokens is not None:
            return cached_tokens
    if is_string_mapping(usage):
        for name in ("prompt_tokens_details", "input_tokens_details"):
            cached_tokens = _cached_tokens_from_usage_details(usage.get(name))
            if cached_tokens is not None:
                return cached_tokens
    return None


def _extract_usage(chunk: object) -> UsagePayload | None:
    usage = getattr(chunk, "usage", None)
    if not usage:
        return None
    payload: UsagePayload = {
        "prompt_tokens": (getattr(usage, "prompt_tokens", 0) or 0),
        "completion_tokens": (getattr(usage, "completion_tokens", 0) or 0),
        "total_tokens": (getattr(usage, "total_tokens", 0) or 0),
    }
    cached_prompt_tokens = _cached_prompt_tokens_from_usage(usage)
    if cached_prompt_tokens is not None:
        payload["cached_prompt_tokens"] = cached_prompt_tokens
    return payload


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


def _codex_payload(
    config: ChatConfig,
    api_messages: list[ApiMessage],
) -> dict[str, object]:
    instructions: list[str] = []
    inputs: list[dict[str, object]] = []
    for message in api_messages:
        role = message["role"]
        text = message_content_text(message.get("content"))
        if not text:
            continue
        if role == "system":
            instructions.append(text)
        elif role in {"user", "assistant"}:
            inputs.append(_codex_input_item(role, text))
        else:
            inputs.append(_codex_input_item("user", f"{role} result:\n{text}"))
    return {
        "model": config.model,
        "instructions": "\n\n".join(instructions)
        or "You are a concise source-grounded assistant.",
        "input": inputs,
        "store": False,
        "stream": True,
    }


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
        error = response.get("error")
        if is_string_mapping(error):
            message = error.get("message")
            if isinstance(message, str) and message:
                return redact_text(message)
        if error:
            return redact_text(str(error))
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


def _stream_codex_backend_completion(
    config: ChatConfig,
    api_messages: list[ApiMessage],
    auth: tuple[str, str],
    *,
    abort: threading.Event | None,
    span: _SpanProtocol,
    prompt_request: PromptCacheRequest | None = None,
) -> Iterator[CompletionDelta]:
    access_token, account_id = auth
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
        "User-Agent": "hephaistos-cli",
    }
    if account_id:
        headers["ChatGPT-Account-ID"] = account_id
    request = urllib.request.Request(
        _CODEX_BACKEND_RESPONSES_URL,
        data=json.dumps(_codex_payload(config, api_messages)).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        response = urllib.request.urlopen(request, timeout=120)  # nosec B310
    except urllib.error.HTTPError as exc:
        detail = _codex_http_error_detail(exc)
        raise EngineError(f"ChatGPT Codex request failed: {detail}") from exc
    except urllib.error.URLError as exc:
        raise EngineError(f"ChatGPT Codex request failed: {redact_text(str(exc.reason))}") from exc

    with response:
        for raw_line in response:
            if abort is not None and abort.is_set():
                return
            line = raw_line.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            data = line.removeprefix("data:").strip()
            if not data:
                continue
            if data == "[DONE]":
                return
            try:
                parsed = json.loads(data)
            except json.JSONDecodeError:
                continue
            if not is_string_mapping(parsed):
                continue
            event_type = parsed.get("type")
            if event_type == "response.output_text.delta":
                delta = parsed.get("delta")
                if isinstance(delta, str) and delta:
                    yield CompletionDelta(content=delta)
            elif event_type == "response.completed":
                usage = _codex_usage(parsed)
                if usage is not None:
                    _record_usage(
                        usage,
                        config.model,
                        span,
                        prompt_request=prompt_request,
                    )
                    yield CompletionDelta(finish_reason="stop", usage=usage)
                return
            elif event_type == "response.failed":
                raise EngineError(f"ChatGPT Codex request failed: {_codex_failure_detail(parsed)}")


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
    return kwargs


def _completion_delta_from_chunk(
    chunk: ChatCompletionChunk,
    config: ChatConfig,
    span: _SpanProtocol,
    *,
    prompt_request: PromptCacheRequest,
) -> CompletionDelta | None:
    usage = _extract_usage(chunk)
    if not chunk.choices:
        if usage is not None:
            _record_usage(usage, config.model, span, prompt_request=prompt_request)
            return CompletionDelta(usage=usage)
        return None

    choice = chunk.choices[0]
    delta = choice.delta
    finish_reason = choice.finish_reason or ""
    if usage is not None:
        _record_usage(usage, config.model, span, prompt_request=prompt_request)
    if not (delta.content or delta.tool_calls or finish_reason or usage is not None):
        return None
    return CompletionDelta(
        content=delta.content or None,
        tool_calls=_normalize_tool_calls(delta.tool_calls) if delta.tool_calls else None,
        finish_reason=finish_reason,
        usage=usage,
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
    partial_parts: list[str] = []
    saw_output = False
    try:
        for chunk in stream:
            if abort is not None and abort.is_set():
                stream.close()
                _log.info(
                    "stream_completion aborted",
                    extra={"fields": {"model": config.model, "latency_ms": timer.ms}},
                )
                span.end()
                return

            delta = _completion_delta_from_chunk(
                chunk,
                config,
                span,
                prompt_request=prompt_request,
            )
            if delta is None:
                continue
            if delta.content:
                partial_parts.append(delta.content)
            if delta.content or delta.tool_calls:
                saw_output = True
            yield delta
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
            _mark_span_error(span, "StreamRecoveryError")
            span.end()
            raise StreamRecoveryError(partial_content, exc) from exc
        if is_retryable_error(exc):
            _circuit_breaker.record_failure()
            if attempt < retry.max_retries:
                raise _RetryOpenAIStreamError(exc) from exc
        _mark_span_error(span, type(exc).__name__)
        span.end()
        raise EngineError(_failure_message(exc, stream=True)) from exc


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
    if retryable:
        _circuit_breaker.record_failure()
    log = _log.info if retryable and attempt < retry.max_retries else _log.warning
    log(
        "stream_completion request failed (attempt %d/%d)",
        attempt + 1,
        retry.max_retries + 1,
        extra={"fields": {"error": _log_error_summary(exc), "latency_ms": timer.ms}},
    )
    if retryable and attempt < retry.max_retries:
        return _wait_backoff(attempt, retry, abort)
    _mark_span_error(span, type(exc).__name__)
    span.end()
    raise EngineError(_failure_message(exc, stream=False)) from exc


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
    span.set_attribute("gen_ai.system", config.provider_slug or "unknown")
    span.set_attribute("gen_ai.request.model", config.model)
    span.set_attribute("gen_ai.request.max_tokens", config.max_tokens)
    retry = retry or RetryConfig()
    client_factory = client_factory or build_client
    raw_api_messages = (
        messages.to_api_messages() if isinstance(messages, Conversation) else messages
    )
    prompt_request = _prompt_cache_builder.build_request(raw_api_messages)
    prompt_request = annotate_anthropic_cache_breakpoints(prompt_request, config.model)
    _prompt_cache_metrics.record_request(prompt_request, model=config.model)
    api_messages = prompt_request.messages
    msg_count = len(api_messages)
    span.set_attribute(
        "gen_ai.request.stable_prefix_hash",
        prompt_request.stable_prefix.fingerprint,
    )
    span.set_attribute(
        "gen_ai.request.stable_prefix_messages",
        prompt_request.stable_prefix.message_count,
    )
    span.set_attribute(
        "gen_ai.request.dynamic_tail_messages",
        prompt_request.dynamic_tail.message_count,
    )
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

    codex_auth = _codex_backend_auth(config)
    if codex_auth is not None:
        yield from _stream_codex_completion(
            config,
            api_messages,
            codex_auth,
            abort=abort,
            span=span,
            prompt_request=prompt_request,
            message_count=msg_count,
            tool_count=len(tools or []),
        )
        return
    if config.provider_slug == "openai-codex":
        span.end()
        raise EngineError(
            "OpenAI Codex subscription requires /login OAuth credentials. "
            "Use the OpenAI API provider for OPENAI_API_KEY billing."
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
        request_kwargs = _request_kwargs(
            config,
            api_messages,
            tools=tools,
            tool_choice=tool_choice,
        )

        try:
            with timer:
                stream = cast(
                    "Stream[ChatCompletionChunk]",
                    client.chat.completions.create(**request_kwargs),  # ty:ignore[no-matching-overload]
                )
        except Exception as exc:
            last_error = exc
            if _handle_openai_request_error(
                exc,
                attempt=attempt,
                retry=retry,
                abort=abort,
                span=span,
                timer=timer,
            ):
                continue
            return

        try:
            yield from _iter_openai_stream_deltas(
                stream,
                config,
                abort=abort,
                span=span,
                prompt_request=prompt_request,
                timer=timer,
                attempt=attempt,
                retry=retry,
            )
        except _RetryOpenAIStreamError as retry_stream:
            last_error = retry_stream.cause
            if not _wait_backoff(attempt, retry, abort):
                return
            continue

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

    _mark_span_error(span, "EngineError")
    span.end()
    raise EngineError(
        _failure_message(last_error, stream=False)
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
