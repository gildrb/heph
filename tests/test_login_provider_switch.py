"""Tests for unified login provider switching behavior."""

from __future__ import annotations

import pytest

import hephaistos.app.commands.auth as _commands_auth
from hephaistos.app import commands
from hephaistos.chat.engine import ChatConfig, Conversation
from hephaistos.chat.session import ChatSession
from hephaistos.providers.config import ProviderConfig
from hephaistos.providers.oauth import OAuthCredentials


def test_login_switches_active_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """After /login succeeds, the active provider should switch to openai-codex."""
    cfg = ChatConfig(
        api_key="",
        base_url="https://api.z.ai/api/paas/v4/",
        model="glm-5",
        _provider_slug="zai",
        _provider_env="ZAI_API_KEY",
    )
    session = ChatSession(
        config=cfg,
        conversation=Conversation(),
        session_id="test-login",
    )

    fake_creds = OAuthCredentials(
        provider="openai-codex",
        access_token="test-access-token",
        refresh_token="test-refresh-token",
        expires_at=9999999999999.0,
        account_id="test-account-123",
    )

    monkeypatch.setattr(
        _commands_auth,
        "select_option",
        lambda _title, _options, **_kw: 0,  # type: ignore[reportUnknownLambdaType]
    )
    monkeypatch.setattr(
        "hephaistos.providers.oauth.login_openai_codex",
        lambda: fake_creds,
    )
    monkeypatch.setattr(
        "hephaistos.providers.keyring_store.set_volatile",
        lambda _slug, _key: None,  # type: ignore[reportUnknownLambdaType]
    )

    saved_configs: list[ProviderConfig] = []

    def _fake_save(pc: ProviderConfig, _path: str | None = None) -> None:
        saved_configs.append(pc)

    monkeypatch.setattr(ProviderConfig, "save", _fake_save)

    success_msgs: list[str] = []
    monkeypatch.setattr(_commands_auth, "print_success", success_msgs.append)
    monkeypatch.setattr(
        _commands_auth,
        "print_error",
        lambda _msg: None,  # type: ignore[reportUnknownLambdaType]
    )

    result = commands.LoginCommand().handle(session, "")

    assert result.should_exit is False
    assert session.config._provider_slug == "openai-codex"  # type: ignore[reportPrivateUsage]
    assert session.config.base_url == "https://api.openai.com/v1"
    assert session.config.model == "gpt-5.4"
    assert len(saved_configs) == 1
    active = saved_configs[0].get_active()
    assert active is not None
    assert active.slug == "openai-codex"
    assert "test-account-123" in success_msgs[0]
    assert "gpt-5.4" in success_msgs[0]


def test_login_openrouter_api_key_switches_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = ChatConfig(api_key="", base_url="", model="")
    session = ChatSession(config=cfg, conversation=Conversation(), session_id="test-openrouter")

    monkeypatch.setattr(
        _commands_auth,
        "select_option",
        lambda _title, _options, **_kw: 1,  # type: ignore[reportUnknownLambdaType]
    )

    def _direct_input(_prompt: str) -> str:
        return "sk-or-test"

    stored: list[tuple[str, str]] = []

    def _store_key(slug: str, key: str) -> None:
        stored.append((slug, key))

    def _save_config(_pc: ProviderConfig, _path: object = None) -> None:
        return None

    monkeypatch.setattr(_commands_auth, "direct_input", _direct_input)
    monkeypatch.setattr(_commands_auth, "store_key", _store_key)
    monkeypatch.setattr(ProviderConfig, "save", _save_config)
    success_msgs: list[str] = []
    monkeypatch.setattr(_commands_auth, "print_success", success_msgs.append)

    commands.LoginCommand().handle(session, "")

    assert stored == [("openrouter", "sk-or-test")]
    assert session.config._provider_slug == "openrouter"  # type: ignore[reportPrivateUsage]
    assert session.config.base_url == "https://openrouter.ai/api/v1"
    assert session.config.model
    assert "OpenRouter" in success_msgs[0]


def test_login_custom_endpoint_switches_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = ChatConfig(api_key="", base_url="", model="")
    session = ChatSession(config=cfg, conversation=Conversation(), session_id="test-custom")
    values = iter(["https://example.test/v1/", "custom-model", "sk-custom"])

    monkeypatch.setattr(
        _commands_auth,
        "select_option",
        lambda _title, _options, **_kw: 3,  # type: ignore[reportUnknownLambdaType]
    )

    def _direct_input(_prompt: str) -> str:
        return next(values)

    stored: list[tuple[str, str]] = []

    def _store_key(slug: str, key: str) -> None:
        stored.append((slug, key))

    saved_configs: list[ProviderConfig] = []

    def _save_config(pc: ProviderConfig, _path: object = None) -> None:
        saved_configs.append(pc)

    monkeypatch.setattr(_commands_auth, "direct_input", _direct_input)
    monkeypatch.setattr(_commands_auth, "store_key", _store_key)
    monkeypatch.setattr(ProviderConfig, "save", _save_config)

    commands.LoginCommand().handle(session, "")

    assert stored == [("custom", "sk-custom")]
    assert session.config._provider_slug == "custom"  # type: ignore[reportPrivateUsage]
    assert session.config.base_url == "https://example.test/v1"
    assert session.config.model == "custom-model"
    custom = saved_configs[0].providers["custom"]
    assert custom.endpoint == "https://example.test/v1"
    assert custom.models == ["custom-model"]


def test_login_failure_does_not_switch_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """If OAuth fails, the active provider should remain unchanged."""
    cfg = ChatConfig(
        api_key="test-key",
        base_url="https://api.z.ai/api/paas/v4/",
        model="glm-5",
        _provider_slug="zai",
        _provider_env="ZAI_API_KEY",
    )
    session = ChatSession(
        config=cfg,
        conversation=Conversation(),
        session_id="test-login-fail",
    )

    monkeypatch.setattr(
        _commands_auth,
        "select_option",
        lambda _title, _options, **_kw: 0,  # type: ignore[reportUnknownLambdaType]
    )
    monkeypatch.setattr(
        "hephaistos.providers.oauth.login_openai_codex",
        lambda: (_ for _ in ()).throw(RuntimeError("OAuth failed")),
    )

    error_msgs: list[str] = []
    monkeypatch.setattr(_commands_auth, "print_error", error_msgs.append)
    monkeypatch.setattr(
        _commands_auth,
        "print_success",
        lambda _msg: None,  # type: ignore[reportUnknownLambdaType]
    )

    commands.LoginCommand().handle(session, "")

    assert session.config._provider_slug == "zai"  # type: ignore[reportPrivateUsage]
    assert "OAuth failed" in error_msgs[0]


def test_login_cancel_does_not_switch_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """If user cancels the login menu, no provider switch happens."""
    cfg = ChatConfig(
        api_key="test-key",
        base_url="https://api.z.ai/api/paas/v4/",
        model="glm-5",
        _provider_slug="zai",
        _provider_env="ZAI_API_KEY",
    )
    session = ChatSession(
        config=cfg,
        conversation=Conversation(),
        session_id="test-login-cancel",
    )

    monkeypatch.setattr(
        _commands_auth,
        "select_option",
        lambda _title, _options, **_kw: None,  # type: ignore[reportUnknownLambdaType]
    )

    commands.LoginCommand().handle(session, "")

    assert session.config._provider_slug == "zai"  # type: ignore[reportPrivateUsage]
