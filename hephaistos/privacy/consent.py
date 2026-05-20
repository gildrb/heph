"""Shared privacy and diagnostics configuration and consent helpers."""

from __future__ import annotations

import contextlib
import json
import os
import platform
import uuid
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path
from typing import Final

from hephaistos import __version__
from hephaistos._types import is_string_mapping
from hephaistos.parameters.settings import load_app_settings, load_raw_settings, save_raw_settings
from hephaistos.privacy.release import (
    POSTHOG_HOST as _RELEASE_POSTHOG_HOST,
)
from hephaistos.privacy.release import (
    POSTHOG_PROJECT_TOKEN as _RELEASE_POSTHOG_PROJECT_TOKEN,
)
from hephaistos.privacy.release import (
    RELEASE_CHANNEL as _RELEASE_CHANNEL,
)
from hephaistos.privacy.release import (
    RELEASE_VERSION as _RELEASE_VERSION,
)
from hephaistos.privacy.release import (
    SENTRY_DSN as _RELEASE_SENTRY_DSN,
)

_INSTALL_ID_PATH: Final[Path] = Path.home() / ".config" / "hephaistos" / "install_id.json"

ANALYTICS_ENABLED_ENV: Final[str] = "HEPHAISTOS_ANALYTICS_ENABLED"
CRASH_REPORTS_ENABLED_ENV: Final[str] = "HEPHAISTOS_CRASH_REPORTS_ENABLED"
POSTHOG_TOKEN_ENV: Final[str] = "HEPHAISTOS_POSTHOG_PROJECT_TOKEN"
POSTHOG_HOST_ENV: Final[str] = "HEPHAISTOS_POSTHOG_HOST"
SENTRY_DSN_ENV: Final[str] = "HEPHAISTOS_SENTRY_DSN"

_LEGACY_POSTHOG_TOKEN_ENV: Final[str] = "POSTHOG_PROJECT_TOKEN"
_LEGACY_POSTHOG_HOST_ENV: Final[str] = "POSTHOG_HOST"
_LEGACY_SENTRY_DSN_ENV: Final[str] = "SENTRY_DSN"

_TRUE_VALUES: Final[frozenset[str]] = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES: Final[frozenset[str]] = frozenset({"0", "false", "no", "off"})


@dataclass(frozen=True)
class PrivacyReleaseConfig:
    posthog_host: str = ""
    posthog_project_token: str = ""
    sentry_dsn: str = ""
    release_channel: str = ""
    release_version: str = ""


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _env_bool(name: str) -> bool | None:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return None
    if raw in _TRUE_VALUES:
        return True
    if raw in _FALSE_VALUES:
        return False
    return None


def release_config() -> PrivacyReleaseConfig:
    return PrivacyReleaseConfig(
        posthog_host=_clean(_RELEASE_POSTHOG_HOST),
        posthog_project_token=_clean(_RELEASE_POSTHOG_PROJECT_TOKEN),
        sentry_dsn=_clean(_RELEASE_SENTRY_DSN),
        release_channel=_clean(_RELEASE_CHANNEL),
        release_version=_clean(_RELEASE_VERSION) or __version__,
    )


def posthog_host() -> str:
    return (
        _clean(os.environ.get(POSTHOG_HOST_ENV))
        or _clean(os.environ.get(_LEGACY_POSTHOG_HOST_ENV))
        or release_config().posthog_host
    )


def posthog_project_token() -> str:
    return (
        _clean(os.environ.get(POSTHOG_TOKEN_ENV))
        or _clean(os.environ.get(_LEGACY_POSTHOG_TOKEN_ENV))
        or release_config().posthog_project_token
    )


def sentry_dsn() -> str:
    return (
        _clean(os.environ.get(SENTRY_DSN_ENV))
        or _clean(os.environ.get(_LEGACY_SENTRY_DSN_ENV))
        or release_config().sentry_dsn
    )


def analytics_env_override() -> bool:
    return _env_bool(ANALYTICS_ENABLED_ENV) is not None


def crash_reports_env_override() -> bool:
    return _env_bool(CRASH_REPORTS_ENABLED_ENV) is not None


def analytics_backend_available() -> bool:
    return bool(posthog_project_token() and posthog_host())


def crash_reports_backend_available() -> bool:
    return bool(sentry_dsn())


def analytics_enabled() -> bool:
    env = _env_bool(ANALYTICS_ENABLED_ENV)
    if env is not None:
        return env
    return load_app_settings().analytics_enabled


def crash_reports_enabled() -> bool:
    env = _env_bool(CRASH_REPORTS_ENABLED_ENV)
    if env is not None:
        return env
    return load_app_settings().crash_reports_enabled


def release_channel() -> str:
    config = release_config()
    return config.release_channel or "source"


def release_version() -> str:
    return release_config().release_version or __version__


def _has_direct_url() -> bool:
    with contextlib.suppress(PackageNotFoundError, FileNotFoundError, OSError, KeyError):
        dist = distribution("hephaistos")
        direct_url = dist.read_text("direct_url.json")
        return bool(direct_url)
    return False


def is_official_install() -> bool:
    config = release_config()
    has_release_diagnostics = bool(config.posthog_project_token or config.sentry_dsn)
    return has_release_diagnostics and not _has_direct_url()


def install_id() -> str:
    _INSTALL_ID_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _INSTALL_ID_PATH.exists():
        with contextlib.suppress(Exception):
            raw = json.loads(_INSTALL_ID_PATH.read_text(encoding="utf-8"))
            if is_string_mapping(raw):
                existing = str(raw.get("install_id", "")).strip()
                if existing:
                    return existing
    value = f"heph_{uuid.uuid4().hex}"
    with contextlib.suppress(Exception):
        _INSTALL_ID_PATH.write_text(json.dumps({"install_id": value}) + "\n", encoding="utf-8")
    return value


def runtime_context() -> dict[str, str]:
    return {
        "app": "hephaistos",
        "app_version": __version__,
        "release_channel": release_channel(),
        "release_version": release_version(),
        "official_install": str(is_official_install()).lower(),
        "platform": platform.system().lower() or "unknown",
        "python_version": platform.python_version(),
    }


def should_show_privacy_notice() -> bool:
    settings = load_app_settings()
    return is_official_install() and not settings.privacy_notice_seen


def mark_privacy_notice_seen() -> None:
    settings = load_raw_settings()
    settings["privacy_notice_seen"] = True
    save_raw_settings(settings)
