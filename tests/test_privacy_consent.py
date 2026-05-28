from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from hephaion.parameters import settings as settings_store
from hephaion.privacy import consent


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


def test_legacy_hephaistos_env_vars_override_release_stub(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_consent_envs(monkeypatch)
    monkeypatch.setattr(consent, "_RELEASE_POSTHOG_HOST", "https://release.example")
    monkeypatch.setattr(consent, "_RELEASE_POSTHOG_PROJECT_TOKEN", "phc_release")
    monkeypatch.setattr(consent, "_RELEASE_SENTRY_DSN", "https://release@example.com/1")
    monkeypatch.setenv("HEPHAISTOS_POSTHOG_HOST", "https://legacy.example")
    monkeypatch.setenv("HEPHAISTOS_POSTHOG_PROJECT_TOKEN", "phc_legacy")
    monkeypatch.setenv("HEPHAISTOS_SENTRY_DSN", "https://legacy@example.com/2")

    assert consent.posthog_host() == "https://legacy.example"
    assert consent.posthog_project_token() == "phc_legacy"
    assert consent.sentry_dsn() == "https://legacy@example.com/2"


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


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits are not portable on Windows")
def test_install_id_writes_private_permissions(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "config"
    install_id_path = config_dir / "install_id.json"
    monkeypatch.setattr(consent, "_INSTALL_ID_PATH", install_id_path)

    value = consent.install_id()

    assert value.startswith("heph_")
    assert stat.S_IMODE(config_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(install_id_path.stat().st_mode) == 0o600


def test_install_id_migrates_legacy_hephaistos_file(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    install_id_path = tmp_path / "hephaion" / "install_id.json"
    legacy_install_id_path = tmp_path / "hephaistos" / "install_id.json"
    legacy_install_id_path.parent.mkdir(parents=True)
    legacy_install_id_path.write_text('{"install_id": "heph_legacy"}\n', encoding="utf-8")
    monkeypatch.setattr(consent, "_INSTALL_ID_PATH", install_id_path)
    monkeypatch.setattr(consent, "_LEGACY_INSTALL_ID_PATH", legacy_install_id_path)

    assert consent.install_id() == "heph_legacy"
    assert install_id_path.read_text(encoding="utf-8") == '{"install_id": "heph_legacy"}\n'


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
