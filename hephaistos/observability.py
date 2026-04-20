"""Sentry-powered error tracking and observability for Hephaistos.

Provides centralized error capture, breadcrumbs, and structured context
that will serve both the CLI today and the planned mobile app tomorrow.
All data is redacted before transmission to prevent API-key leaks.

**sentry-sdk is an optional dependency.**  Install via ``uv sync --extra sentry``.
When the package is absent, every public call in this module is a safe no-op —
the application continues normally without telemetry.

Configuration (environment variables):
    SENTRY_DSN                - Sentry project DSN (required for tracking).
                                 When unset, all calls are no-ops.
    SENTRY_ENVIRONMENT        - ``"production"`` / ``"development"`` etc.
                                 Auto-detected when unset.
    SENTRY_TRACES_SAMPLE_RATE - Float 0.0-1.0, default 0.1.
"""

from __future__ import annotations

import logging
import os
import platform
import re as _re
from typing import Any

try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration

    _SENTRY_AVAILABLE: bool = True
except ImportError:  # pragma: no cover
    sentry_sdk = None  # type: ignore[assignment]
    LoggingIntegration = None  # type: ignore[assignment,misc]
    _SENTRY_AVAILABLE = False


from hephaistos import __version__
from hephaistos.logging import redact_value

# -- Sensitive-key detection (mirrors logging.py patterns) --------------------

_SENSITIVE_KEY_PATTERS: list[_re.Pattern[str]] = [
    _re.compile(r"(?i)(api.?key|secret|token(?!s)|password|auth(orization|entication))"),
    _re.compile(r"(?i)(bearer|credential|private.?key)"),
]

_REDACTED = "***REDACTED***"


def _is_sensitive_key(key: str) -> bool:
    return any(p.search(key) for p in _SENSITIVE_KEY_PATTERS)


# -- Recursive redaction ------------------------------------------------------


def _scrub_value(value: object) -> object:
    """Recursively redact sensitive keys and values from nested data."""
    if isinstance(value, dict):
        return {
            k: _REDACTED if _is_sensitive_key(k) else _scrub_value(v) for k, v in value.items()
        }
    if isinstance(value, list):
        return [_scrub_value(item) for item in value]
    if isinstance(value, str):
        return redact_value(value)
    return value


# Sections of a Sentry event that may contain user-provided sensitive data.
# Internal Sentry fields (event_id, platform, release, etc.) are never scrubbed.
_SCRUB_SECTIONS = frozenset({"extra", "tags", "contexts", "breadcrumbs", "request", "user"})


def _redact_event(event: dict[str, Any], _hint: dict[str, Any]) -> dict[str, Any] | None:
    """``before_send`` hook: scrub sensitive data in user-facing sections only."""
    for section in _SCRUB_SECTIONS:
        if section in event:
            event[section] = _scrub_value(event[section])
    return event


# -- Environment detection ----------------------------------------------------


_DSN_ENV = "SENTRY_DSN"
_ENV_ENV = "SENTRY_ENVIRONMENT"
_TRACES_ENV = "SENTRY_TRACES_SAMPLE_RATE"
_DEFAULT_TRACES_RATE = 0.1


def _detect_environment() -> str:
    """Heuristic: *production* when installed via pip, else *development*."""
    try:
        from importlib.metadata import distribution

        dist = distribution("hephaistos")
        location = str(dist.locate_file("")) if dist else ""
        if "site-packages" in location:
            return "production"
    except Exception:
        pass
    return "development"


def _parse_traces_rate() -> float:
    raw = os.environ.get(_TRACES_ENV, "")
    try:
        return max(0.0, min(1.0, float(raw)))
    except ValueError:
        return _DEFAULT_TRACES_RATE


# -- Public API ---------------------------------------------------------------


def init_sentry() -> None:
    """Initialise the Sentry SDK.  No-op when ``SENTRY_DSN`` is not set or
    ``sentry-sdk`` is not installed."""
    if not _SENTRY_AVAILABLE:
        return
    assert sentry_sdk is not None  # narrowed by _SENTRY_AVAILABLE guard
    assert LoggingIntegration is not None  # narrowed by _SENTRY_AVAILABLE guard
    dsn = os.environ.get(_DSN_ENV, "").strip()
    if not dsn:
        return

    environment = os.environ.get(_ENV_ENV, _detect_environment())
    traces_rate = _parse_traces_rate()

    sentry_sdk.init(
        dsn=dsn,
        release=f"hephaistos@{__version__}",
        environment=environment,
        traces_sample_rate=traces_rate,
        before_send=_redact_event,  # type: ignore[arg-type]
        before_send_transaction=_redact_event,  # type: ignore[arg-type]
        integrations=[
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.CRITICAL,
            ),
        ],
    )
    sentry_sdk.set_tag("platform", "cli")
    sentry_sdk.set_context(
        "runtime",
        {
            "python_version": platform.python_version(),
            "os": platform.system(),
            "os_version": platform.release(),
        },
    )


def set_session_context(
    *,
    session_id: str = "",
    armory: str = "",
    provider: str = "",
    model: str = "",
) -> None:
    """Set tags that persist for the current Sentry scope (session-level).
    No-op when ``sentry-sdk`` is not installed."""
    if not _SENTRY_AVAILABLE:
        return
    assert sentry_sdk is not None  # narrowed by _SENTRY_AVAILABLE guard
    if session_id:
        sentry_sdk.set_tag("session_id", session_id)
    if armory:
        sentry_sdk.set_tag("armory", armory)
    if provider:
        sentry_sdk.set_tag("provider", provider)
    if model:
        sentry_sdk.set_tag("model", model)


def add_breadcrumb(
    category: str,
    message: str,
    *,
    level: str = "info",
    **data: Any,
) -> None:
    """Add a breadcrumb to the current Sentry scope.
    No-op when ``sentry-sdk`` is not installed."""
    if not _SENTRY_AVAILABLE:
        return
    assert sentry_sdk is not None  # narrowed by _SENTRY_AVAILABLE guard
    sentry_sdk.add_breadcrumb(
        category=category,
        message=message,
        level=level,
        data=_scrub_value(data) if data else None,  # type: ignore[arg-type]
    )


def capture_exception(
    exc: BaseException | None = None,
    *,
    context: dict[str, Any] | None = None,
) -> str | None:
    """Capture an exception to Sentry.  Returns the Sentry event ID.
    Returns ``None`` when ``sentry-sdk`` is not installed."""
    if not _SENTRY_AVAILABLE:
        return None
    assert sentry_sdk is not None  # narrowed by _SENTRY_AVAILABLE guard
    if context:
        with sentry_sdk.new_scope() as scope:
            for key, value in context.items():
                scope.set_extra(key, _scrub_value(value))
            return sentry_sdk.capture_exception(exc)
    return sentry_sdk.capture_exception(exc)
