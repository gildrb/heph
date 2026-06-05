"""ChatGPT Codex backend streaming transport."""

from __future__ import annotations

import contextlib
import json
import os
import threading
import urllib.error
import urllib.request
from collections.abc import Callable, Generator, Iterator
from dataclasses import dataclass
from typing import Protocol, Self

from hephaion._types import is_string_mapping
from hephaion.logging import redact_text
from hephaion.providers.oauth import load_credentials
from hephaion.runtime._api_types import ApiMessage, UsagePayload
from hephaion.runtime.config import ChatConfig
from hephaion.runtime.delta import CompletionDelta
from hephaion.runtime.errors import EngineError
from hephaion.runtime.messages import message_content_text
from hephaion.runtime.prompt_cache import PromptCacheRequest
from hephaion.runtime.request_payload import model_reasoning_effort
from hephaion.runtime.usage_payload import cached_prompt_tokens_from_usage

_CODEX_BACKEND_RESPONSES_URL = "https://chatgpt.com/backend-api/codex/responses"
_CODEX_BACKEND_TIMEOUT_SECONDS = 30


class _SpanProtocol(Protocol):
    def set_attribute(self, key: str, value: object) -> object: ...

    def end(self, _end_time: float | None = None) -> None: ...


class _ByteStreamResponseProtocol(Protocol):
    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: object,
    ) -> object: ...

    def __iter__(self) -> Iterator[bytes]: ...


class _RecordUsageFn(Protocol):
    def __call__(
        self,
        usage: UsagePayload,
        model: str,
        span: _SpanProtocol,
        *,
        prompt_request: PromptCacheRequest | None = None,
    ) -> None: ...


type _CodexEventHandler = Callable[
    [
        dict[str, object],
        ChatConfig,
        _SpanProtocol,
        PromptCacheRequest | None,
        _RecordUsageFn,
    ],
    CompletionDelta | None,
]


@dataclass(frozen=True, slots=True)
class _CodexEventDelta:
    delta: CompletionDelta | None
    done: bool


def codex_backend_auth(config: ChatConfig) -> tuple[str, str] | None:
    if config.provider_slug != "openai-codex":
        return None
    creds = load_credentials("openai-codex")
    if creds is None:
        return None
    return creds.access_token, creds.account_id or ""


def stream_codex_backend_completion(
    config: ChatConfig,
    api_messages: list[ApiMessage],
    auth: tuple[str, str],
    *,
    abort: threading.Event | None,
    span: _SpanProtocol,
    prompt_request: PromptCacheRequest | None = None,
    record_usage: _RecordUsageFn,
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
                record_usage=record_usage,
            )
            if done:
                return


def _completion_aborted(abort: threading.Event | None) -> bool:
    return abort is not None and abort.is_set()


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
    if reasoning_effort := model_reasoning_effort(config):
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
    cached_prompt_tokens = cached_prompt_tokens_from_usage(usage)
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


def _message_and_code_from_payload(payload: dict[str, object]) -> tuple[object, object]:
    error_value = payload.get("error", payload)
    if error_mapping := _payload_error_mapping(payload):
        return _message_and_code_from_error_mapping(payload, error_mapping)
    return payload.get("message") or error_value, payload.get("code")


def _payload_error_mapping(payload: dict[str, object]) -> dict[str, object] | None:
    error_value = payload.get("error", payload)
    return error_value if is_string_mapping(error_value) else None


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


def _codex_done_delta(
    _event: dict[str, object],
    _config: ChatConfig,
    _span: _SpanProtocol,
    _prompt_request: PromptCacheRequest | None,
    _record_usage: _RecordUsageFn,
) -> CompletionDelta | None:
    return None


def _codex_output_text_delta(
    event: dict[str, object],
    _config: ChatConfig,
    _span: _SpanProtocol,
    _prompt_request: PromptCacheRequest | None,
    _record_usage: _RecordUsageFn,
) -> CompletionDelta | None:
    delta = event.get("delta")
    return CompletionDelta(content=delta) if isinstance(delta, str) and delta else None


def _codex_completed_delta(
    event: dict[str, object],
    config: ChatConfig,
    span: _SpanProtocol,
    prompt_request: PromptCacheRequest | None,
    record_usage: _RecordUsageFn,
) -> CompletionDelta:
    usage = _codex_usage(event)
    if usage is None:
        return CompletionDelta(finish_reason="stop")
    record_usage(usage, config.model, span, prompt_request=prompt_request)
    return CompletionDelta(finish_reason="stop", usage=usage)


def _codex_failed_delta(
    event: dict[str, object],
    _config: ChatConfig,
    _span: _SpanProtocol,
    _prompt_request: PromptCacheRequest | None,
    _record_usage: _RecordUsageFn,
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
    record_usage: _RecordUsageFn,
) -> CompletionDelta | None:
    event_type = event.get("type")
    handler = _CODEX_EVENT_HANDLERS.get(event_type) if isinstance(event_type, str) else None
    if handler is None:
        return None
    return handler(event, config, span, prompt_request, record_usage)


def _iter_codex_stream_step(
    raw_line: bytes,
    config: ChatConfig,
    span: _SpanProtocol,
    *,
    prompt_request: PromptCacheRequest | None,
    record_usage: _RecordUsageFn,
) -> Generator[CompletionDelta, None, bool]:
    step = _codex_stream_step(
        raw_line,
        config,
        span,
        prompt_request=prompt_request,
        record_usage=record_usage,
    )
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
    record_usage: _RecordUsageFn,
) -> _CodexEventDelta | None:
    event_delta = _codex_event_delta(
        raw_line,
        config,
        span,
        prompt_request=prompt_request,
        record_usage=record_usage,
    )
    if event_delta is None:
        return None
    return event_delta


def _codex_event_delta(
    raw_line: bytes,
    config: ChatConfig,
    span: _SpanProtocol,
    *,
    prompt_request: PromptCacheRequest | None,
    record_usage: _RecordUsageFn,
) -> _CodexEventDelta | None:
    event = _codex_event_payload(raw_line)
    if event is None:
        return None
    delta = _codex_delta_from_event(
        event,
        config,
        span,
        prompt_request=prompt_request,
        record_usage=record_usage,
    )
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
        if detail == "ChatGPT Codex backend request failed":
            detail = f"HTTP {exc.code} {exc.reason}: {detail}"
        raise EngineError(f"ChatGPT Codex request failed: {detail}") from exc
    except urllib.error.URLError as exc:
        raise EngineError(f"ChatGPT Codex request failed: {redact_text(str(exc.reason))}") from exc


def _codex_backend_timeout_seconds() -> float:
    raw = os.environ.get("HEPHAION_CODEX_TIMEOUT_SECONDS", "").strip()
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


__all__ = ["codex_backend_auth", "stream_codex_backend_completion"]
