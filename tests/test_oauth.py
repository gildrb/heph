"""Tests for the OAuth module."""

from __future__ import annotations

import base64
import hashlib
import json
import ssl
import time
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from hephaistos.commands import LogoutCommand, get_registry
from hephaistos.providers.oauth import (
    OAuthCredentials,
    _ssl_context,  # type: ignore[reportPrivateUsage]
    clear_credentials,
    generate_pkce,
    list_providers,
    load_credentials,
    resolve_oauth_key,
    save_credentials,
)

# --- SSL context ------------------------------------------------------------


def test_ssl_context_has_ca_certs() -> None:
    """The SSL context must contain CA certificates for verification to work.

    This catches the macOS python.org installer case where
    ``create_default_context()`` returns zero certs.
    """
    ctx = _ssl_context()
    assert ctx.get_ca_certs(), "SSL context has zero CA certs — HTTPS will fail"


def test_ssl_context_certifi_fallback_when_no_default_certs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When default context has zero certs, certifi bundle must be loaded."""
    original_create = ssl.create_default_context

    def _empty_context(*, cafile: str | None = None, **_kwargs: object) -> ssl.SSLContext:
        # When cafile is provided (certifi fallback), pass through to the
        # real implementation so the test can verify certs are loaded.
        if cafile:
            return original_create(cafile=cafile)
        # Simulate macOS python.org Python: return context with zero certs
        empty = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        empty.check_hostname = True
        empty.verify_mode = ssl.CERT_REQUIRED
        return empty

    monkeypatch.setattr(ssl, "create_default_context", _empty_context)
    ctx = _ssl_context()
    assert ctx.get_ca_certs(), "certifi fallback should have loaded CA certs"


# --- PKCE -------------------------------------------------------------------


def test_generate_pkce_returns_verifier_and_challenge() -> None:
    verifier, challenge = generate_pkce()
    assert len(verifier) >= 43
    assert len(challenge) >= 43
    # Challenge should be different from verifier
    assert verifier != challenge


def test_generate_pkce_deterministic_challenge() -> None:
    """Same verifier should produce same challenge."""
    verifier, challenge = generate_pkce()
    expected = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest())
        .rstrip(b"=")
        .decode("ascii")
    )
    assert challenge == expected


def test_generate_pkce_unique_each_call() -> None:
    v1, c1 = generate_pkce()
    v2, c2 = generate_pkce()
    assert v1 != v2
    assert c1 != c2


# --- Credential persistence -------------------------------------------------


class TestCredentialPersistence:
    def _make_creds(self, provider: str = "openai-codex") -> OAuthCredentials:
        return OAuthCredentials(
            provider=provider,
            access_token="at_123",
            refresh_token="rt_456",
            expires_at=time.time() * 1000 + 3600_000,  # 1h from now
            account_id="acct_abc",
        )

    @pytest.mark.usefixtures("isolated_auth_dir")
    def test_save_and_load(self) -> None:
        creds = self._make_creds()
        save_credentials(creds)
        loaded = load_credentials("openai-codex")

        assert loaded is not None
        assert loaded.access_token == "at_123"
        assert loaded.refresh_token == "rt_456"
        assert loaded.account_id == "acct_abc"

    @pytest.mark.usefixtures("isolated_auth_dir")
    def test_load_missing_returns_none(self) -> None:
        loaded = load_credentials("nonexistent")

        assert loaded is None

    @pytest.mark.usefixtures("isolated_auth_dir")
    def test_clear_credentials(self) -> None:
        creds = self._make_creds()
        save_credentials(creds)
        assert list_providers() == ["openai-codex"]
        removed = clear_credentials("openai-codex")
        assert removed is True
        assert load_credentials("openai-codex") is None
        assert list_providers() == []

    @pytest.mark.usefixtures("isolated_auth_dir")
    def test_clear_nonexistent_returns_false(self) -> None:
        assert clear_credentials("nope") is False

    @pytest.mark.usefixtures("isolated_auth_dir")
    def test_list_providers(self) -> None:
        creds1 = self._make_creds("openai-codex")
        creds2 = self._make_creds("other-provider")
        save_credentials(creds1)
        save_credentials(creds2)
        providers = list_providers()

        assert set(providers) == {"openai-codex", "other-provider"}

    def test_auth_file_created_with_restricted_permissions(
        self, isolated_auth_dir: SimpleNamespace
    ) -> None:
        creds = self._make_creds()
        save_credentials(creds)
        mode = isolated_auth_dir.auth_file.stat().st_mode & 0o777

        assert mode == 0o600

    def test_auth_json_format(self, isolated_auth_dir: SimpleNamespace) -> None:
        creds = self._make_creds()
        save_credentials(creds)
        data = json.loads(isolated_auth_dir.auth_file.read_text())

        entry = data["openai-codex"]
        assert entry["type"] == "oauth"
        assert entry["access_token"] == "at_123"
        assert entry["refresh_token"] == "rt_456"
        assert entry["account_id"] == "acct_abc"
        assert isinstance(entry["expires_at"], float)

    @pytest.mark.usefixtures("isolated_auth_dir")
    def test_resolve_oauth_key_returns_access_token(self) -> None:
        creds = self._make_creds()
        save_credentials(creds)
        key = resolve_oauth_key("openai-codex")

        assert key == "at_123"

    @pytest.mark.usefixtures("isolated_auth_dir")
    def test_resolve_oauth_key_missing_returns_empty(self) -> None:
        key = resolve_oauth_key("nonexistent")

        assert key == ""

    @pytest.mark.usefixtures("isolated_auth_dir")
    def test_load_auto_refreshes_expired_token(self) -> None:
        expired = OAuthCredentials(
            provider="openai-codex",
            access_token="old_at",
            refresh_token="old_rt",
            expires_at=time.time() * 1000 - 10000,  # expired
            account_id="acct_abc",
        )
        refreshed = OAuthCredentials(
            provider="openai-codex",
            access_token="new_at",
            refresh_token="new_rt",
            expires_at=time.time() * 1000 + 1000 * 60 * 60,
            account_id="acct_abc",
        )

        save_credentials(expired)
        with patch(
            "hephaistos.providers.oauth.refresh_credentials",
            return_value=refreshed,
        ) as mock_refresh:
            loaded = load_credentials("openai-codex")

        mock_refresh.assert_called_once()
        assert loaded is not None
        assert loaded.access_token == "new_at"


# --- LoginCommand / LogoutCommand -------------------------------------------


def test_login_command_registered() -> None:
    registry = get_registry()
    cmd = registry.find("login")
    assert cmd is not None
    assert cmd.name == "login"


def test_logout_command_registered() -> None:
    registry = get_registry()
    cmd = registry.find("logout")
    assert cmd is not None
    assert cmd.name == "logout"


def test_logout_no_sessions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "hephaistos.providers.oauth.list_providers",
        list,
    )
    messages: list[tuple[str, str]] = []

    def _capture_info(msg: str) -> None:
        messages.append(("info", msg))

    monkeypatch.setattr(
        "hephaistos.commands.auth.print_info",
        _capture_info,
    )
    cmd = LogoutCommand()
    result = cmd.handle(None, "")
    assert result.output is None
    assert any("No OAuth sessions" in m for _, m in messages)


def test_logout_single_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "hephaistos.providers.oauth.list_providers",
        lambda: ["openai-codex"],
    )

    def _confirm(*_a: object, **_kw: object) -> bool:
        return True

    monkeypatch.setattr(
        "hephaistos.commands.auth.confirm",
        _confirm,
    )
    cleared: list[str] = []
    monkeypatch.setattr(
        "hephaistos.providers.oauth.clear_credentials",
        cleared.append,
    )
    messages: list[tuple[str, str]] = []

    def _capture_success(msg: str) -> None:
        messages.append(("success", msg))

    monkeypatch.setattr(
        "hephaistos.commands.auth.print_success",
        _capture_success,
    )
    cmd = LogoutCommand()
    result = cmd.handle(None, "")
    assert result.output is None
    assert cleared == ["openai-codex"]
    assert any("Logged out" in m for _, m in messages)
