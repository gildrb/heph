"""Tests for unified login provider switching behavior."""

from __future__ import annotations

import heph.commands.auth as _commands_auth
import pytest
from ai.providers.config import ProviderConfig
from ai.providers.oauth import OAuthCredentials
from ai.runtime import ChatConfig, Conversation
from harness.chat.session import ChatSession
from heph import commands
from interfaces.terminal import MenuOption


def test_login_menu_uses_label_value_provider_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    visible_options: list[MenuOption] = []

    def capture_options(_title: str, options: list[MenuOption]) -> None:
        visible_options.extend(options)

    monkeypatch.setattr(_commands_auth, "select_option", capture_options)

    commands.LoginCommand().handle(object(), "")

    assert [option.label for option in visible_options] == [
        "CODEX",
        "OPENAI",
        "OPENROUTER",
        "Z.AI",
        "CUSTOM",
        "DEEPSEEK",
    ]
    assert visible_options[0].description == "ACCOUNT chatgpt plus/pro subscription"
    assert visible_options[1].description == "KEY api key"
    assert visible_options[4].description == "ENDPOINT openai-compatible base url  MODEL custom"


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
        lambda _title, _options, **_kw: 0,
    )
    monkeypatch.setattr(
        "ai.providers.oauth.login_openai_codex",
        lambda: fake_creds,
    )
    monkeypatch.setattr(
        "ai.providers.keyring_store.set_volatile",
        lambda _slug, _key: None,
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
        lambda _msg: None,
    )

    result = commands.LoginCommand().handle(session, "")

    assert result.should_exit is False
    assert session.config._provider_slug == "openai-codex"
    assert session.config.base_url == "https://api.openai.com/v1"
    assert session.config.model == "gpt-5.5"
    assert len(saved_configs) == 1
    active = saved_configs[0].get_active()
    assert active is not None
    assert active.slug == "openai-codex"
    assert "test-account-123" in success_msgs[0]
    assert "gpt-5.5" in success_msgs[0]


def test_login_openai_api_key_switches_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = ChatConfig(api_key="", base_url="", model="")
    session = ChatSession(config=cfg, conversation=Conversation(), session_id="test-openai-api")

    monkeypatch.setattr(
        _commands_auth,
        "select_option",
        lambda _title, _options, **_kw: 1,
    )

    stored: list[tuple[str, str]] = []
    monkeypatch.setattr(_commands_auth, "direct_input", lambda _prompt: "sk-openai-test")
    monkeypatch.setattr(_commands_auth, "store_key", lambda slug, key: stored.append((slug, key)))
    monkeypatch.setattr(ProviderConfig, "save", lambda _pc, _path=None: None)
    success_msgs: list[str] = []
    monkeypatch.setattr(_commands_auth, "print_success", success_msgs.append)

    commands.LoginCommand().handle(session, "")

    assert stored == [("openai", "sk-openai-test")]
    assert session.config._provider_slug == "openai"
    assert session.config.base_url == "https://api.openai.com/v1"
    assert session.config.model == "gpt-5.5"
    assert "OpenAI API" in success_msgs[0]


def test_login_openrouter_api_key_switches_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = ChatConfig(api_key="", base_url="", model="")
    session = ChatSession(config=cfg, conversation=Conversation(), session_id="test-openrouter")

    monkeypatch.setattr(
        _commands_auth,
        "select_option",
        lambda _title, _options, **_kw: 2,
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
    assert session.config._provider_slug == "openrouter"
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
        lambda _title, _options, **_kw: 4,
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
    assert session.config._provider_slug == "custom"
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
        lambda _title, _options, **_kw: 0,
    )
    monkeypatch.setattr(
        "ai.providers.oauth.login_openai_codex",
        lambda: (_ for _ in ()).throw(RuntimeError("OAuth failed")),
    )

    error_msgs: list[str] = []
    monkeypatch.setattr(_commands_auth, "print_error", error_msgs.append)
    monkeypatch.setattr(
        _commands_auth,
        "print_success",
        lambda _msg: None,
    )

    commands.LoginCommand().handle(session, "")

    assert session.config._provider_slug == "zai"
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
        lambda _title, _options, **_kw: None,
    )

    commands.LoginCommand().handle(session, "")

    assert session.config._provider_slug == "zai"


def test_login_openai_codex_generic_failure_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    session = ChatSession(
        config=ChatConfig(api_key="", base_url="", model=""),
        conversation=Conversation(),
        session_id="generic-login-failure",
    )
    errors: list[str] = []

    monkeypatch.setattr(
        _commands_auth,
        "select_option",
        lambda _title, _options, **_kw: 0,
    )
    monkeypatch.setattr(
        "ai.providers.oauth.login_openai_codex",
        lambda: (_ for _ in ()).throw(ValueError("boom")),
    )
    monkeypatch.setattr(_commands_auth, "print_error", errors.append)

    commands.LoginCommand().handle(session, "")

    assert errors == ["Login failed: boom"]


def test_login_custom_endpoint_requires_model(monkeypatch: pytest.MonkeyPatch) -> None:
    session = ChatSession(
        config=ChatConfig(api_key="", base_url="", model=""),
        conversation=Conversation(),
        session_id="custom-model-required",
    )
    values = iter(["https://example.test/v1/", "", "sk-custom"])
    errors: list[str] = []

    monkeypatch.setattr(
        _commands_auth,
        "select_option",
        lambda _title, _options, **_kw: 4,
    )
    monkeypatch.setattr(_commands_auth, "direct_input", lambda _prompt: next(values))
    monkeypatch.setattr(_commands_auth, "print_error", errors.append)

    commands.LoginCommand().handle(session, "")

    assert errors == ["Model name is required."]


def test_login_api_key_falls_back_to_volatile_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    session = ChatSession(
        config=ChatConfig(api_key="", base_url="", model=""),
        conversation=Conversation(),
        session_id="volatile-openrouter",
    )
    volatile: list[tuple[str, str]] = []
    success: list[str] = []

    monkeypatch.setattr(
        _commands_auth,
        "select_option",
        lambda _title, _options, **_kw: 2,
    )
    monkeypatch.setattr(_commands_auth, "direct_input", lambda _prompt: "sk-or-test")
    monkeypatch.setattr(
        _commands_auth,
        "store_key",
        lambda _slug, _key: (_ for _ in ()).throw(RuntimeError("keychain unavailable")),
    )
    monkeypatch.setattr(
        _commands_auth,
        "set_volatile",
        lambda slug, key: volatile.append((slug, key)),
    )
    monkeypatch.setattr(ProviderConfig, "save", lambda _pc, _path=None: None)
    monkeypatch.setattr(_commands_auth, "print_success", success.append)

    commands.LoginCommand().handle(session, "")

    assert volatile == [("openrouter", "sk-or-test")]
    assert "this session only" in success[0]


def test_logout_reports_environment_only_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    messages: list[str] = []

    monkeypatch.setattr("ai.providers.oauth.list_providers", list)
    monkeypatch.setattr("heph.commands.auth.keyring_store.retrieve_key", lambda _slug: None)
    monkeypatch.setattr(_commands_auth, "get_volatile", lambda _slug: None)
    monkeypatch.setattr(_commands_auth, "print_info", messages.append)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    commands.LogoutCommand().handle(None, "")

    assert any("Environment-provided keys" in message for message in messages)


def test_logout_single_provider_cancelled(monkeypatch: pytest.MonkeyPatch) -> None:
    messages: list[str] = []

    monkeypatch.setattr("ai.providers.oauth.list_providers", lambda: ["openai-codex"])
    monkeypatch.setattr("heph.commands.auth.keyring_store.retrieve_key", lambda _slug: None)
    monkeypatch.setattr(_commands_auth, "confirm", lambda *_a, **_kw: False)
    monkeypatch.setattr(_commands_auth, "print_info", messages.append)

    commands.LogoutCommand().handle(None, "")

    assert messages == ["Cancelled."]


def test_logout_all_providers_clears_everything(monkeypatch: pytest.MonkeyPatch) -> None:
    cleared: list[tuple[str, str]] = []
    success: list[str] = []

    monkeypatch.setattr(
        _commands_auth,
        "_logout_targets",
        lambda: [
            ("openai-codex", "oauth", "OpenAI Codex subscription"),
            ("openrouter", "api_key", "OpenRouter API key"),
        ],
    )
    monkeypatch.setattr(_commands_auth, "_env_only_targets", list)
    monkeypatch.setattr(
        _commands_auth,
        "select_option",
        lambda _title, _options, **_kw: 2,
    )
    monkeypatch.setattr(
        _commands_auth,
        "_clear_logout_target",
        lambda slug, kind: cleared.append((slug, kind)),
    )
    monkeypatch.setattr(_commands_auth, "print_success", success.append)

    commands.LogoutCommand().handle(None, "")

    assert cleared == [("openai-codex", "oauth"), ("openrouter", "api_key")]
    assert success == ["Logged out of all stored providers."]


def test_logout_menu_uses_label_value_provider_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    visible_options: list[MenuOption] = []

    monkeypatch.setattr(
        _commands_auth,
        "_logout_targets",
        lambda: [
            ("openai-codex", "oauth", "ACCOUNT subscription"),
            ("openrouter", "api_key", "KEY api key  SOURCE keychain"),
        ],
    )
    monkeypatch.setattr(_commands_auth, "_env_only_targets", list)

    def capture_options(_title: str, options: list[MenuOption]) -> None:
        visible_options.extend(options)

    monkeypatch.setattr(_commands_auth, "select_option", capture_options)

    commands.LogoutCommand().handle(None, "")

    assert [option.label for option in visible_options] == ["CODEX", "OPENROUTER", "ALL"]
    assert visible_options[0].description == "ACCOUNT subscription"
    assert visible_options[1].description == "KEY api key  SOURCE keychain"
    assert visible_options[2].description == "ACTION clear stored"
