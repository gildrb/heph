from __future__ import annotations

import pytest

from hephaistos import telemetry
from hephaistos.parameters import settings as settings_store


def _clear_telemetry_envs(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        telemetry.ANALYTICS_ENABLED_ENV,
        telemetry.CRASH_REPORTS_ENABLED_ENV,
        telemetry.POSTHOG_HOST_ENV,
        telemetry.POSTHOG_TOKEN_ENV,
        telemetry.SENTRY_DSN_ENV,
        "POSTHOG_HOST",
        "POSTHOG_PROJECT_TOKEN",
        "SENTRY_DSN",
    ):
        monkeypatch.delenv(name, raising=False)


def test_env_vars_override_release_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_telemetry_envs(monkeypatch)
    monkeypatch.setattr(telemetry, "_RELEASE_POSTHOG_HOST", "https://release.example")
    monkeypatch.setattr(telemetry, "_RELEASE_POSTHOG_PROJECT_TOKEN", "phc_release")
    monkeypatch.setattr(telemetry, "_RELEASE_SENTRY_DSN", "https://release@example.com/1")
    monkeypatch.setenv(telemetry.POSTHOG_HOST_ENV, "https://env.example")
    monkeypatch.setenv(telemetry.POSTHOG_TOKEN_ENV, "phc_env")
    monkeypatch.setenv(telemetry.SENTRY_DSN_ENV, "https://env@example.com/2")

    assert telemetry.posthog_host() == "https://env.example"
    assert telemetry.posthog_project_token() == "phc_env"
    assert telemetry.sentry_dsn() == "https://env@example.com/2"


def test_safe_stub_has_no_remote_backends(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_telemetry_envs(monkeypatch)
    monkeypatch.setattr(telemetry, "_RELEASE_POSTHOG_HOST", None)
    monkeypatch.setattr(telemetry, "_RELEASE_POSTHOG_PROJECT_TOKEN", None)
    monkeypatch.setattr(telemetry, "_RELEASE_SENTRY_DSN", None)
    monkeypatch.setattr(telemetry, "_RELEASE_CHANNEL", None)
    monkeypatch.setattr(telemetry, "_has_direct_url", lambda: False)

    assert telemetry.analytics_backend_available() is False
    assert telemetry.crash_reports_backend_available() is False
    assert telemetry.is_official_install() is False
    assert telemetry.release_channel() == "source"


def test_official_install_requires_release_config_and_no_direct_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_telemetry_envs(monkeypatch)
    monkeypatch.setattr(telemetry, "_RELEASE_POSTHOG_HOST", "https://release.example")
    monkeypatch.setattr(telemetry, "_RELEASE_POSTHOG_PROJECT_TOKEN", "phc_release")
    monkeypatch.setattr(telemetry, "_RELEASE_SENTRY_DSN", None)
    monkeypatch.setattr(telemetry, "_has_direct_url", lambda: False)

    assert telemetry.is_official_install() is True

    monkeypatch.setattr(telemetry, "_has_direct_url", lambda: True)

    assert telemetry.is_official_install() is False


def test_saved_settings_control_consent_without_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_telemetry_envs(monkeypatch)
    settings_store.save_setting("analytics_enabled", True)
    settings_store.save_setting("crash_reports_enabled", False)

    assert telemetry.analytics_enabled() is True
    assert telemetry.crash_reports_enabled() is False


def test_env_overrides_take_precedence_over_saved_consent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_telemetry_envs(monkeypatch)
    settings_store.save_setting("analytics_enabled", True)
    settings_store.save_setting("crash_reports_enabled", True)
    monkeypatch.setenv(telemetry.ANALYTICS_ENABLED_ENV, "false")
    monkeypatch.setenv(telemetry.CRASH_REPORTS_ENABLED_ENV, "0")

    assert telemetry.analytics_enabled() is False
    assert telemetry.crash_reports_enabled() is False


def test_telemetry_notice_is_shown_once_for_official_installs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_telemetry_envs(monkeypatch)
    monkeypatch.setattr(telemetry, "_RELEASE_POSTHOG_HOST", "https://release.example")
    monkeypatch.setattr(telemetry, "_RELEASE_POSTHOG_PROJECT_TOKEN", "phc_release")
    monkeypatch.setattr(telemetry, "_RELEASE_SENTRY_DSN", None)
    monkeypatch.setattr(telemetry, "_has_direct_url", lambda: False)

    assert telemetry.should_show_telemetry_notice() is True

    telemetry.mark_telemetry_notice_seen()

    assert telemetry.should_show_telemetry_notice() is False
