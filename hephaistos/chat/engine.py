"""LLM communication engine with streaming support.

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
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
)
from openai.types.chat import ChatCompletionMessageParam

from hephaistos.logging import Timer, get_logger
from hephaistos.providers.model_support import is_supported_model_for_endpoint

_log = get_logger("chat.engine")


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
    def resolved_api_key(self) -> str:
        """Resolve the API key via keychain → env → volatile."""
        if self._provider_slug:
            from hephaistos.providers.keyring_store import resolve_key

            return resolve_key(self._provider_slug, self._provider_env)
        return self.api_key


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


_RETRYABLE_TYPES = (APIConnectionError, APITimeoutError, InternalServerError, RateLimitError)
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
_ACCOUNT_SETUP_HINT = (
    "Configure a valid API key with /api key <your-key>, switch provider with /provider, "
    "or authenticate with /login."
)


@dataclass
class Message:
    """A single message in a conversation."""

    role: str  # "system", "user", or "assistant"
    content: str


@dataclass
class Conversation:
    """An ordered list of messages forming a conversation."""

    messages: list[Message] = field(default_factory=list)

    def add(self, role: str, content: str) -> None:
        self.messages.append(Message(role=role, content=content))

    def to_api_messages(self) -> list[ChatCompletionMessageParam]:
        """Convert to the format expected by the OpenAI client."""
        return [
            {"role": msg.role, "content": msg.content}  # type: ignore[misc]
            for msg in self.messages
        ]


def _provider_error_fields(exc: Exception) -> tuple[str, str]:
    """Return a short provider error message and code without SDK noise."""
    body = getattr(exc, "body", None)
    code = ""
    message = ""

    if isinstance(body, dict):
        error = body.get("error", body)
        if isinstance(error, dict):
            raw_code = error.get("code") or error.get("type") or body.get("code")
            raw_message = error.get("message") or body.get("message")
        else:
            raw_code = body.get("code")
            raw_message = body.get("message") or error
        code = str(raw_code or "").strip()
        message = str(raw_message or "").strip()

    if not message:
        message = str(getattr(exc, "message", "") or exc).strip()
    if not code:
        code = str(getattr(exc, "code", "") or "").strip()
    return message or exc.__class__.__name__, code


def _is_account_setup_error(exc: Exception) -> bool:
    """Return True when retrying cannot fix the provider/account state."""
    if isinstance(exc, (AuthenticationError, PermissionDeniedError)):
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
    if _is_account_setup_error(exc):
        return _with_hint(f"Provider rejected the request: {detail}", _ACCOUNT_SETUP_HINT)
    return f"LLM request failed: {detail}"


def _stream_failure_message(exc: Exception) -> str:
    """Build a user-facing streaming failure message."""
    detail, _code = _provider_error_fields(exc)
    if _is_account_setup_error(exc):
        return _with_hint(f"Provider rejected the stream: {detail}", _ACCOUNT_SETUP_HINT)
    return f"LLM stream failed: {detail}"


def _log_error_summary(exc: Exception) -> str:
    """Return a compact log summary for expected provider setup failures."""
    if _is_account_setup_error(exc):
        detail, code = _provider_error_fields(exc)
        return f"{code}: {detail}" if code else detail
    return str(exc)


def _build_client(config: ChatConfig) -> OpenAI:
    """Create an OpenAI client from the given config."""
    if not config.base_url:
        raise EngineError("No provider configured. Use /provider use <slug> to select one.")
    if not config.model:
        raise EngineError("No model configured. Use /model to select one.")
    if not is_supported_model_for_endpoint(config.model, config.base_url):
        raise EngineError(f"Model unavailable for endpoint: {config.model}")
    api_key = config.resolved_api_key
    if not api_key:
        raise EngineError(
            "No API key found. Configure one via /api key, environment variable, "
            "or OAuth (/login)."
        )
    return OpenAI(api_key=api_key, base_url=config.base_url)


def is_retryable_error(exc: Exception) -> bool:
    """Return True if *exc* is a transient error worth retrying."""
    if _is_account_setup_error(exc):
        return False
    return isinstance(exc, _RETRYABLE_TYPES)


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
    tool_calls: list[dict] | None = None
    finish_reason: str = ""
    usage: dict[str, int] | None = None


def _normalize_tool_calls(tool_calls: list[object]) -> list[dict]:
    """Convert Pydantic tool-call delta objects to plain dicts."""
    result: list[dict] = []
    for tc in tool_calls:
        if isinstance(tc, dict):
            result.append(tc)
            continue
        # OpenAI SDK returns Pydantic v2 models; .model_dump() gives plain dicts.
        tc_dict: dict = tc.model_dump(exclude_none=True)  # type: ignore[union-attr]
        fn = tc_dict.get("function")
        if fn is not None and not isinstance(fn, dict):
            tc_dict["function"] = fn.model_dump(exclude_none=True)  # type: ignore[union-attr]
        result.append(tc_dict)
    return result


def _extract_usage(chunk: object) -> dict[str, int] | None:
    usage = getattr(chunk, "usage", None)
    if not usage:
        return None
    return {
        "prompt_tokens": (getattr(usage, "prompt_tokens", 0) or 0),
        "completion_tokens": (getattr(usage, "completion_tokens", 0) or 0),
        "total_tokens": (getattr(usage, "total_tokens", 0) or 0),
    }


def stream_completion(
    config: ChatConfig,
    messages: Conversation | list[ChatCompletionMessageParam],
    *,
    tools: list[dict] | None = None,
    abort: threading.Event | None = None,
    retry: RetryConfig | None = None,
    client_factory: Callable[[ChatConfig], OpenAI] | None = None,
) -> Iterator[CompletionDelta]:
    """Stream raw completion deltas with shared retry/recovery handling."""
    retry = retry or RetryConfig()
    client_factory = client_factory or _build_client
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
            return

        timer = Timer()
        request_kwargs = {
            "model": config.model,
            "messages": api_messages,
            "max_tokens": config.max_tokens,
            "stream": True,
        }
        if tools:
            request_kwargs["tools"] = tools  # type: ignore[assignment]

        try:
            with timer:
                stream = client.chat.completions.create(**request_kwargs)  # type: ignore[call-overload]
        except Exception as exc:
            last_error = exc
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
            raise EngineError(_request_failure_message(exc)) from exc

        partial_content = ""
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
                    return

                usage = _extract_usage(chunk)
                if not chunk.choices:
                    if usage is not None:
                        yield CompletionDelta(usage=usage)
                    continue

                choice = chunk.choices[0]
                delta = choice.delta
                finish_reason = choice.finish_reason or ""
                if delta.content:
                    partial_content += delta.content
                if delta.content or delta.tool_calls:
                    saw_output = True
                if delta.content or delta.tool_calls or finish_reason or usage is not None:
                    yield CompletionDelta(
                        content=delta.content or None,
                        tool_calls=(
                            _normalize_tool_calls(delta.tool_calls) if delta.tool_calls else None
                        ),
                        finish_reason=finish_reason,
                        usage=usage,
                    )
        except Exception as exc:
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
                raise StreamRecoveryError(partial_content, exc) from exc
            last_error = exc
            if is_retryable_error(exc) and attempt < retry.max_retries:
                if not _wait_backoff(attempt, retry, abort):
                    return
                continue
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
        return

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
        client_factory=_build_client,
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
