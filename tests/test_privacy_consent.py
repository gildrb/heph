from __future__ import annotations

import pytest

from hephaistos.parameters import settings as settings_store
from hephaistos.privacy import consent


def _clear_consent_envs(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        consent.ANALYTICS_ENABLED_ENV,
        consent.CRASH_REPORTS_ENABLED_ENV,
        consent.POSTHOG_HOST_ENV,
        consent.POSTHOG_TOKEN_ENV,
        consent.SENTRY_DSN_ENV,
        "POSTHOG_HOST",
        "POSTHOG_PROJECT_TOKEN",
        "SENTRY_DSN",
    ):
        monkeypatch.delenv(name, raising=False)


def test_env_vars_override_release_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_consent_envs(monkeypatch)
    monkeypatch.setattr(consent, "_RELEASE_POSTHOG_HOST", "https://release.example")
    monkeypatch.setattr(consent, "_RELEASE_POSTHOG_PROJECT_TOKEN", "phc_release")
    monkeypatch.setattr(consent, "_RELEASE_SENTRY_DSN", "https://release@example.com/1")
    monkeypatch.setenv(consent.POSTHOG_HOST_ENV, "https://env.example")
    monkeypatch.setenv(consent.POSTHOG_TOKEN_ENV, "phc_env")
    monkeypatch.setenv(consent.SENTRY_DSN_ENV, "https://env@example.com/2")

    assert consent.posthog_host() == "https://env.example"
    assert consent.posthog_project_token() == "phc_env"
    assert consent.sentry_dsn() == "https://env@example.com/2"


def test_safe_stub_has_no_remote_backends(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_consent_envs(monkeypatch)
    monkeypatch.setattr(consent, "_RELEASE_POSTHOG_HOST", None)
    monkeypatch.setattr(consent, "_RELEASE_POSTHOG_PROJECT_TOKEN", None)
    monkeypatch.setattr(consent, "_RELEASE_SENTRY_DSN", None)
    monkeypatch.setattr(consent, "_RELEASE_CHANNEL", None)
    monkeypatch.setattr(consent, "_has_direct_url", lambda: False)

    assert consent.analytics_backend_available() is False
    assert consent.crash_reports_backend_available() is False
    assert consent.is_official_install() is False
    assert consent.release_channel() == "source"


def test_official_install_requires_release_config_and_no_direct_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_consent_envs(monkeypatch)
    monkeypatch.setattr(consent, "_RELEASE_POSTHOG_HOST", "https://release.example")
    monkeypatch.setattr(consent, "_RELEASE_POSTHOG_PROJECT_TOKEN", "phc_release")
    monkeypatch.setattr(consent, "_RELEASE_SENTRY_DSN", None)
    monkeypatch.setattr(consent, "_has_direct_url", lambda: False)

    assert consent.is_official_install() is True

    monkeypatch.setattr(consent, "_has_direct_url", lambda: True)

    assert consent.is_official_install() is False


def test_saved_settings_control_consent_without_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_consent_envs(monkeypatch)
    settings_store.save_setting("analytics_enabled", True)
    settings_store.save_setting("crash_reports_enabled", False)

    assert consent.analytics_enabled() is True
    assert consent.crash_reports_enabled() is False


def test_env_overrides_take_precedence_over_saved_consent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_consent_envs(monkeypatch)
    settings_store.save_setting("analytics_enabled", True)
    settings_store.save_setting("crash_reports_enabled", True)
    monkeypatch.setenv(consent.ANALYTICS_ENABLED_ENV, "false")
    monkeypatch.setenv(consent.CRASH_REPORTS_ENABLED_ENV, "0")

    assert consent.analytics_enabled() is False
    assert consent.crash_reports_enabled() is False


def test_consent_notice_is_shown_once_for_official_installs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_consent_envs(monkeypatch)
    monkeypatch.setattr(consent, "_RELEASE_POSTHOG_HOST", "https://release.example")
    monkeypatch.setattr(consent, "_RELEASE_POSTHOG_PROJECT_TOKEN", "phc_release")
    monkeypatch.setattr(consent, "_RELEASE_SENTRY_DSN", None)
    monkeypatch.setattr(consent, "_has_direct_url", lambda: False)

    assert consent.should_show_privacy_notice() is True

    consent.mark_privacy_notice_seen()

    assert consent.should_show_privacy_notice() is False
