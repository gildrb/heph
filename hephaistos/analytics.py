"""Lightweight PostHog event capture for official or explicitly configured installs."""

from __future__ import annotations

import contextlib
import json
import urllib.request
from collections.abc import Mapping
from typing import Final

from hephaistos.logging import get_logger, redact_text
from hephaistos.telemetry import (
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


def _is_safe_scalar(value: object) -> bool:
    return value is None or isinstance(value, bool | int | float)


def _sanitize_string(key: str, value: str) -> str | None:
    if key in _SENSITIVE_KEYS:
        return None
    if len(value) > 120:
        return None
    if key.endswith(("_path", "path", "filename", "file")) and value:
        return None
    return redact_text(value)


def _sanitize_properties(properties: Mapping[str, object] | None) -> dict[str, object]:
    cleaned: dict[str, object] = dict(runtime_context())
    if not properties:
        return cleaned
    for key, value in properties.items():
        lowered = key.strip().lower()
        if lowered in _SENSITIVE_KEYS:
            continue
        if _is_safe_scalar(value):
            cleaned[key] = value
            continue
        if isinstance(value, str):
            safe_value = _sanitize_string(lowered, value)
            if safe_value is not None:
                cleaned[key] = safe_value
    return cleaned


def get_distinct_id() -> str:
    return install_id()


def init_analytics() -> None:
    """Warm the stable anonymous install ID when analytics are possible."""
    if analytics_backend_available():
        install_id()


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
    sanitized_properties["$lib"] = "hephaistos"
    sanitized_properties["$lib_version"] = str(sanitized_properties["app_version"])

    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        posthog_host().rstrip("/") + "/capture/",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with contextlib.suppress(Exception), urllib.request.urlopen(request, timeout=5):  # nosec B310
        return
    _log.debug("analytics capture failed", extra={"fields": {"event": event}})


def shutdown_analytics() -> None:
    """Flush hook retained for CLI symmetry. The HTTP client is stateless."""
