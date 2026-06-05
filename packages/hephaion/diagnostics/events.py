"""Lightweight PostHog event capture for official or explicitly configured installs."""

from __future__ import annotations

import contextlib
import json
import urllib.parse
import urllib.request
from collections.abc import Mapping
from typing import Final, TypeGuard

from hephaion.logging import get_logger, redact_text
from hephaion.privacy.consent import (
    analytics_backend_available,
    analytics_enabled,
    install_id,
    posthog_host,
    posthog_project_token,
    runtime_context,
)

_log = get_logger("analytics")

_SENSITIVE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "api_key",
        "authorization",
        "token",
        "secret",
        "password",
        "prompt",
        "content",
        "message",
        "body",
        "path",
        "filename",
        "armory",
        "text",
        "input",
        "output",
    }
)


def _sanitize_properties(properties: Mapping[str, object] | None) -> dict[str, object]:
    cleaned: dict[str, object] = dict(runtime_context())
    if not properties:
        return cleaned
    for key, value in properties.items():
        if (sanitized := _sanitized_property_value(key, value)) is not _SKIP_PROPERTY:
            cleaned[key] = sanitized
    return cleaned


_SKIP_PROPERTY = object()


def _sanitized_property_value(key: str, value: object) -> object:
    lowered = key.strip().lower()
    if _sensitive_property_key(lowered):
        return _SKIP_PROPERTY
    if _safe_scalar_property(value):
        return value
    if _safe_string_property(value):
        return redact_text(value)
    return _SKIP_PROPERTY


def _sensitive_property_key(lowered: str) -> bool:
    return lowered in _SENSITIVE_KEYS or _sensitive_property_name(lowered)


def _sensitive_property_name(lowered: str) -> bool:
    return lowered.endswith(("_path", "path", "filename", "file"))


def _safe_scalar_property(value: object) -> bool:
    return value is None or isinstance(value, bool | int | float)


def _safe_string_property(value: object) -> TypeGuard[str]:
    return isinstance(value, str) and len(value) <= 120


def get_distinct_id() -> str:
    return install_id()


def init_analytics() -> None:
    """No-op retained for CLI symmetry.

    The install ID is warmed lazily on first ``capture()`` call instead of
    at import / startup time, removing blocking file I/O from the startup
    path.
    """


def capture(event: str, properties: Mapping[str, object] | None = None) -> None:
    """Capture an anonymous event when analytics is configured and enabled."""
    if not analytics_backend_available() or not analytics_enabled():
        return

    sanitized_properties = _sanitize_properties(properties)
    payload: dict[str, object] = {
        "api_key": posthog_project_token(),
        "event": event,
        "distinct_id": get_distinct_id(),
        "properties": sanitized_properties,
    }
    sanitized_properties["distinct_id"] = get_distinct_id()
    sanitized_properties["$lib"] = "hephaion"
    sanitized_properties["$lib_version"] = str(sanitized_properties["app_version"])

    data = json.dumps(payload).encode("utf-8")
    capture_url = _capture_url()
    if not capture_url:
        _log.debug(
            "analytics capture skipped: invalid PostHog host",
            extra={"fields": {"event": event}},
        )
        return
    request = urllib.request.Request(
        capture_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with contextlib.suppress(Exception), urllib.request.urlopen(request, timeout=5):  # nosec B310
        return
    _log.debug("analytics capture failed", extra={"fields": {"event": event}})


def shutdown_analytics() -> None:
    """Flush hook retained for CLI symmetry. The HTTP client is stateless."""


def _capture_url() -> str:
    host = posthog_host().rstrip("/")
    parsed = urllib.parse.urlparse(host)
    if parsed.scheme != "https" or not parsed.netloc:
        return ""
    return host + "/capture/"
