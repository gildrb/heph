"""Tests for OAuth login provider switching behavior."""

from __future__ import annotations

from hephaistos.app import commands
from hephaistos.chat.engine import ChatConfig, Conversation
from hephaistos.chat.session import ChatSession
from hephaistos.providers.config import ProviderConfig
from hephaistos.providers.oauth import OAuthCredentials


def test_login_switches_active_provider(monkeypatch) -> None:
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
        commands,
        "select_option",
        lambda _title, _options, **_kw: 0,
    )
    monkeypatch.setattr(
        "hephaistos.providers.oauth.login_openai_codex",
        lambda: fake_creds,
    )
    monkeypatch.setattr(
        "hephaistos.providers.keyring_store.set_volatile",
        lambda _slug, _key: None,
    )

    saved_configs: list[ProviderConfig] = []

    def _fake_save(pc: ProviderConfig, _path=None) -> None:
        saved_configs.append(pc)

    monkeypatch.setattr(ProviderConfig, "save", _fake_save)

    success_msgs: list[str] = []
    monkeypatch.setattr(commands, "print_success", success_msgs.append)
    monkeypatch.setattr(commands, "print_error", lambda msg: None)

    result = commands.LoginCommand().handle(session, "")

    assert result.should_exit is False
    assert session.config._provider_slug == "openai-codex"
    assert session.config.base_url == "https://api.openai.com/v1"
    assert session.config.model == "gpt-5.4"
    assert len(saved_configs) == 1
    active = saved_configs[0].get_active()
    assert active is not None
    assert active.slug == "openai-codex"
    assert "test-account-123" in success_msgs[0]
    assert "gpt-5.4" in success_msgs[0]


def test_login_failure_does_not_switch_provider(monkeypatch) -> None:
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
        commands,
        "select_option",
        lambda _title, _options, **_kw: 0,
    )
    monkeypatch.setattr(
        "hephaistos.providers.oauth.login_openai_codex",
        lambda: (_ for _ in ()).throw(RuntimeError("OAuth failed")),
    )

    error_msgs: list[str] = []
    monkeypatch.setattr(commands, "print_error", error_msgs.append)
    monkeypatch.setattr(commands, "print_success", lambda msg: None)

    commands.LoginCommand().handle(session, "")

    assert session.config._provider_slug == "zai"
    assert "OAuth failed" in error_msgs[0]


def test_login_cancel_does_not_switch_provider(monkeypatch) -> None:
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
        commands,
        "select_option",
        lambda _title, _options, **_kw: None,
    )

    commands.LoginCommand().handle(session, "")

    assert session.config._provider_slug == "zai"
