"""Tests for chat engine (LLM communication)."""

from __future__ import annotations

import io
import json
import urllib.error
from email.message import Message as HttpHeaders
from types import SimpleNamespace
from typing import Never, Self

import pytest
from ai.providers.registry import ModelInfo, get_registry
from ai.runtime import (
    ChatConfig,
    CompletionDelta,
    Conversation,
    EngineError,
    Message,
    RetryConfig,
    build_client,
    codex_backend,
    missing_api_key_message,
)
from ai.runtime import engine as runtime_engine
from ai.runtime.request_payload import request_kwargs


class _Span:
    def __init__(self) -> None:
        self.attributes: dict[str, object] = {}

    def set_attribute(self, key: str, value: object) -> object:
        self.attributes[key] = value
        return value

    def end(self, _end_time: float | None = None) -> None:
        return None


class _StreamingResponse:
    def __init__(self, lines: list[str]) -> None:
        self.lines = lines
        self.closed = False

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.closed = True

    def __iter__(self) -> object:
        for line in self.lines:
            yield line.encode()
        raise AssertionError("stream was not stopped after completion")


def _record_usage(*_args: object, **_kwargs: object) -> None:
    return None


def _payload_mapping(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    return {str(key): item for key, item in value.items()}


def test_build_client_allows_pollinations_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HEPHAION_API_KEY", raising=False)
    config = ChatConfig(
        api_key="",
        base_url="https://text.pollinations.ai/openai",
        model="openai",
    )

    client = build_client(config)

    assert client.api_key == "no-key-required"


def test_build_client_raises_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HEPHAION_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    config = ChatConfig(api_key="", base_url="http://localhost/v1", model="test")
    with pytest.raises(EngineError, match="No API key found"):
        build_client(config)


def test_keyless_provider_does_not_resolve_key(monkeypatch: pytest.MonkeyPatch) -> None:
    config = ChatConfig(base_url="https://text.pollinations.ai/openai", model="openai")
    config.apply_provider_reference("pollinations", "")

    def fail_resolve(_slug: str, _env: str = "") -> str:
        raise AssertionError("resolved key")

    monkeypatch.setattr(
        "ai.runtime.engine.resolve_key",
        fail_resolve,
    )

    assert config.resolved_api_key == ""
    client = build_client(config)
    assert str(client.base_url) == "https://text.pollinations.ai/openai/"


def test_local_llama_cpp_provider_does_not_resolve_key(monkeypatch: pytest.MonkeyPatch) -> None:
    config = ChatConfig(
        base_url="http://127.0.0.1:18080/v1",
        model="llama-cpp/local-test",
    )
    config.apply_provider_reference("llama-cpp", "")

    def fail_resolve(_slug: str, _env: str = "") -> str:
        raise AssertionError("resolved key")

    monkeypatch.setattr(
        "ai.runtime.engine.resolve_key",
        fail_resolve,
    )

    assert config.resolved_api_key == ""
    client = build_client(config)
    assert client.api_key == "no-key-required"


def test_missing_api_key_message_explains_free_openrouter_auth() -> None:
    config = ChatConfig(
        api_key="",
        base_url="https://openrouter.ai/api/v1",
        model="arcee-ai/trinity-large-preview:free",
    )

    message = missing_api_key_message(config)

    assert "free-priced" in message
    assert "still requires an API key" in message
    assert "/login" in message


def test_build_client_rejects_unavailable_model_for_known_endpoint() -> None:
    config = ChatConfig(
        api_key="test-key",
        base_url="https://openrouter.ai/api/v1",
        model="legacy-model",
    )
    with pytest.raises(EngineError, match="Model unavailable for endpoint"):
        build_client(config)


def test_conversation_add_and_convert() -> None:
    conv = Conversation()
    conv.add("system", "You are helpful.")
    conv.add("user", "Hello")

    assert len(conv.messages) == 2
    assert conv.messages[0].role == "system"
    assert conv.messages[1].content == "Hello"

    api_msgs = conv.to_api_messages()
    assert len(api_msgs) == 2
    assert api_msgs[0]["role"] == "system"
    assert api_msgs[1]["role"] == "user"
    assert api_msgs[1]["content"] == "Hello"


def test_message_dataclass() -> None:
    msg = Message(role="user", content="test")
    assert msg.role == "user"
    assert msg.content == "test"


def test_is_feature_enabled() -> None:
    config = ChatConfig(feature_flags=frozenset({"alpha", "beta"}))
    assert config.is_feature_enabled("alpha")
    assert config.is_feature_enabled("beta")
    assert not config.is_feature_enabled("gamma")


def test_is_feature_enabled_default_empty() -> None:
    config = ChatConfig()
    assert not config.is_feature_enabled("anything")


def test_chat_config_defaults_to_low_reasoning() -> None:
    config = ChatConfig()

    assert config.reasoning_level == "low"


def test_chat_config_defaults_to_hidden_thinking() -> None:
    config = ChatConfig()

    assert config.thinking_visibility == "off"


def test_chat_config_defaults_to_deterministic_temperature() -> None:
    config = ChatConfig()

    assert config.temperature == 0.0


def test_request_kwargs_include_reasoning_for_reasoning_models() -> None:
    config = ChatConfig(
        base_url="https://api.openai.com/v1",
        model="gpt-5.5",
        reasoning_level="high",
    )
    config.apply_provider_reference("openai", "OPENAI_API_KEY")

    kwargs = request_kwargs(
        config,
        [{"role": "user", "content": "hello"}],
        tools=None,
        tool_choice=None,
    )

    assert kwargs["reasoning_effort"] == "high"
    assert kwargs["temperature"] == 0.0


def test_request_kwargs_can_omit_temperature() -> None:
    config = ChatConfig(
        base_url="https://api.openai.com/v1",
        model="plain-model",
        temperature=None,
    )

    kwargs = request_kwargs(
        config,
        [{"role": "user", "content": "hello"}],
        tools=None,
        tool_choice=None,
    )

    assert "temperature" not in kwargs


def test_codex_payload_omits_unsupported_temperature() -> None:
    config = ChatConfig(
        base_url="https://api.openai.com/v1",
        model="gpt-5.4-mini",
    )

    payload = codex_backend._codex_payload(
        config,
        [{"role": "user", "content": "hello"}],
    )

    assert "temperature" not in payload


def test_codex_payload_requests_reasoning_summary_when_thinking_visible() -> None:
    config = ChatConfig(
        base_url="https://api.openai.com/v1",
        model="gpt-5.4-mini",
        thinking_visibility="minimal",
    )

    payload = codex_backend._codex_payload(
        config,
        [{"role": "user", "content": "hello"}],
    )

    reasoning = _payload_mapping(payload["reasoning"])
    assert reasoning["summary"] == "auto"


def test_codex_backend_timeout_can_be_lowered_for_stress_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HEPHAION_CODEX_TIMEOUT_SECONDS", "12.5")

    assert codex_backend._codex_backend_timeout_seconds() == 12.5


def test_codex_backend_default_timeout_fails_fast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HEPHAION_CODEX_TIMEOUT_SECONDS", raising=False)

    assert codex_backend._codex_backend_timeout_seconds() == 30


def test_request_kwargs_clamp_reasoning_to_supported_tiers() -> None:
    get_registry().register(
        ModelInfo(
            "non-openai-reasoning",
            "custom",
            "Non-OpenAI Reasoning",
            128_000,
            8_192,
            0.0,
            0.0,
            tags=("reasoning",),
            reasoning_efforts=("low", "medium", "high"),
        )
    )
    config = ChatConfig(
        base_url="https://example.com/v1",
        model="non-openai-reasoning",
        reasoning_level="xhigh",
    )
    config.apply_provider_reference("custom", "CUSTOM_API_KEY")

    kwargs = request_kwargs(
        config,
        [{"role": "user", "content": "hello"}],
        tools=None,
        tool_choice=None,
    )

    assert kwargs["reasoning_effort"] == "low"


def test_request_kwargs_omit_reasoning_for_non_reasoning_models() -> None:
    get_registry().register(
        ModelInfo(
            "plain-model",
            "custom",
            "Plain Model",
            128_000,
            8_192,
            0.0,
            0.0,
        )
    )
    config = ChatConfig(
        base_url="https://example.com/v1",
        model="plain-model",
        reasoning_level="high",
    )
    config.apply_provider_reference("custom", "CUSTOM_API_KEY")

    kwargs = request_kwargs(
        config,
        [{"role": "user", "content": "hello"}],
        tools=None,
        tool_choice=None,
    )

    assert "reasoning_effort" not in kwargs


def test_completion_delta_extracts_provider_reasoning_fields() -> None:
    raw_delta = SimpleNamespace(
        content=None,
        reasoning_content="raw thinking",
        reasoning_summary="short summary",
        tool_calls=None,
    )

    delta = runtime_engine._completion_delta_from_choice(
        raw_delta,
        finish_reason="",
        usage=None,
    )

    assert delta.reasoning == "raw thinking"
    assert delta.reasoning_summary == "short summary"
    assert delta.content is None


def test_reasoning_only_stream_error_keeps_retry_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    progress = runtime_engine._OpenAIStreamProgress()
    progress.record(CompletionDelta(reasoning_summary="considering"))

    monkeypatch.setattr(runtime_engine, "is_retryable_error", lambda _exc: True)

    with pytest.raises(runtime_engine._RetryOpenAIStreamError, match="temporary failure"):
        runtime_engine._handle_openai_stream_error(
            RuntimeError("temporary failure"),
            progress,
            attempt=0,
            retry=RetryConfig(max_retries=1, base_delay=0, max_delay=0),
            span=_Span(),
            timer=runtime_engine.Timer(),
        )


def test_codex_http_error_detail_redacts_sensitive_text() -> None:
    token = "Bearer " + ("a" * 32)
    body = json.dumps({"detail": f"upstream echoed {token}"})
    exc = urllib.error.HTTPError(
        "https://chatgpt.com/backend-api/codex/responses",
        401,
        "Unauthorized",
        HttpHeaders(),
        io.BytesIO(body.encode()),
    )

    detail = codex_backend._codex_http_error_detail(exc)

    assert token not in detail
    assert "***REDACTED***" in detail


def test_codex_backend_stream_redacts_http_error_detail(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret = "sk-" + ("a" * 24)
    body = json.dumps({"response": {"error": {"message": f"bad credential {secret}"}}})
    error = urllib.error.HTTPError(
        "https://chatgpt.com/backend-api/codex/responses",
        401,
        "Unauthorized",
        HttpHeaders(),
        io.BytesIO(body.encode()),
    )

    def raise_error(*_args: object, **_kwargs: object) -> object:
        raise error

    monkeypatch.setattr(codex_backend.urllib.request, "urlopen", raise_error)
    config = ChatConfig(base_url="https://api.openai.com/v1", model="gpt-5.4-mini")

    with pytest.raises(EngineError) as exc_info:
        list(
            codex_backend.stream_codex_backend_completion(
                config,
                [{"role": "user", "content": "hello"}],
                ("access-token", "account-id"),
                abort=None,
                span=_Span(),
                record_usage=_record_usage,
            )
        )

    message = str(exc_info.value)
    assert secret not in message
    assert "***REDACTED***" in message


def test_codex_backend_stream_stops_after_response_completed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    completed = {
        "type": "response.completed",
        "response": {"usage": {"input_tokens": 3, "output_tokens": 2, "total_tokens": 5}},
    }
    response = _StreamingResponse(
        [
            'data: {"type": "response.output_text.delta", "delta": "done"}\n',
            f"data: {json.dumps(completed)}\n",
        ]
    )
    monkeypatch.setattr(
        codex_backend.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: response,
    )
    config = ChatConfig(base_url="https://api.openai.com/v1", model="gpt-5.4-mini")

    deltas = list(
        codex_backend.stream_codex_backend_completion(
            config,
            [{"role": "user", "content": "hello"}],
            ("access-token", "account-id"),
            abort=None,
            span=_Span(),
            record_usage=_record_usage,
        )
    )

    assert [delta.content for delta in deltas] == ["done", None]
    assert deltas[-1].finish_reason == "stop"
    assert deltas[-1].usage == {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}
    assert response.closed is True


def test_codex_backend_stream_emits_reasoning_summary_delta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    completed = {"type": "response.completed", "response": {}}
    response = _StreamingResponse(
        [
            'data: {"type": "response.reasoning_summary_text.delta", "delta": "considering"}\n',
            f"data: {json.dumps(completed)}\n",
        ]
    )
    monkeypatch.setattr(
        codex_backend.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: response,
    )
    config = ChatConfig(base_url="https://api.openai.com/v1", model="gpt-5.4-mini")

    deltas = list(
        codex_backend.stream_codex_backend_completion(
            config,
            [{"role": "user", "content": "hello"}],
            ("access-token", "account-id"),
            abort=None,
            span=_Span(),
            record_usage=_record_usage,
        )
    )

    assert deltas[0].reasoning_summary == "considering"
    assert deltas[-1].finish_reason == "stop"


def test_codex_provider_requires_oauth_instead_of_api_key_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runtime_engine, "load_credentials", lambda _provider: None)

    def fail_client_factory(_config: ChatConfig) -> Never:
        raise AssertionError("OpenAI SDK fallback should not be used for Codex OAuth")

    config = ChatConfig(
        base_url="https://api.openai.com/v1",
        model="gpt-5.5",
        _provider_slug="openai-codex",
    )

    with pytest.raises(EngineError, match="requires /login OAuth credentials"):
        list(
            runtime_engine.stream_completion(
                config,
                [{"role": "user", "content": "hello"}],
                client_factory=fail_client_factory,
            )
        )
