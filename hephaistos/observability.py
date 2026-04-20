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

import contextlib
import json as _json
import logging
import os
import platform
import re as _re
import time as _time
import urllib.request as _urllib_request
from typing import Any, Self

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

try:
    from opentelemetry import metrics as _metrics_mod
    from opentelemetry import trace as _trace_mod
    from opentelemetry.sdk.metrics import MeterProvider as _MeterProvider
    from opentelemetry.sdk.metrics.export import (
        PeriodicExportingMetricReader as _PeriodicExportingMetricReader,
    )
    from opentelemetry.sdk.trace import TracerProvider as _TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor as _BatchSpanProcessor

    _OTEL_AVAILABLE: bool = True
except ImportError:  # pragma: no cover
    _trace_mod = None  # type: ignore[assignment]
    _metrics_mod = None  # type: ignore[assignment]
    _TracerProvider = None  # type: ignore[assignment]
    _BatchSpanProcessor = None  # type: ignore[assignment]
    _MeterProvider = None  # type: ignore[assignment]
    _PeriodicExportingMetricReader = None  # type: ignore[assignment]
    _OTEL_AVAILABLE = False

_log = logging.getLogger("hephaistos.observability")


class _NoopSpan:
    """No-op span when OpenTelemetry is not installed."""

    __slots__ = ()

    def set_attribute(self, key: str, value: object) -> _NoopSpan:
        return self

    def end(self, _end_time: float | None = None) -> None:
        pass

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.end()


class _NoopTracer:
    """No-op tracer when OpenTelemetry is not installed."""

    __slots__ = ()

    def start_span(self, name: str, **kwargs: object) -> _NoopSpan:
        return _NoopSpan()

    def start_as_current_span(self, name: str, **kwargs: object) -> _NoopSpan:
        return _NoopSpan()


class _NoopHistogram:
    """No-op histogram when OpenTelemetry is not installed."""

    __slots__ = ()

    def record(self, value: float, _attributes: dict[str, str] | None = None) -> None:
        pass


class _NoopCounter:
    """No-op counter when OpenTelemetry is not installed."""

    __slots__ = ()

    def add(self, value: float, _attributes: dict[str, str] | None = None) -> None:
        pass


class _NoopMeter:
    """No-op meter when OpenTelemetry is not installed."""

    __slots__ = ()

    def create_histogram(self, name: str, **kwargs: object) -> _NoopHistogram:
        return _NoopHistogram()

    def create_counter(self, name: str, **kwargs: object) -> _NoopCounter:
        return _NoopCounter()

    def create_up_down_counter(self, name: str, **kwargs: object) -> _NoopCounter:
        return _NoopCounter()


# -- Sensitive-key detection (mirrors logging.py patterns) --------------------

_SENSITIVE_KEY_PATTERS: list[_re.Pattern[str]] = [
    _re.compile(r"(?i)(api.?key|secret|token(?!s)|password|auth(orization|entication))"),
    _re.compile(r"(?i)(bearer|credential|private.?key)"),
]

_REDACTED = "***REDACTED***"

_ALERT_WEBHOOK_ENV = "ALERT_WEBHOOK_URL"
_ALERT_MIN_LEVEL_ENV = "ALERT_MIN_LEVEL"
_ALERT_MIN_LEVEL_DEFAULT = "ERROR"
_ALERT_COOLDOWN_SECONDS = 300  # 5 minutes
_alert_webhook_url: str | None = None
_alert_min_level: int = logging.ERROR
_alert_timestamps: dict[str, float] = {}


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
    with contextlib.suppress(Exception):
        from importlib.metadata import distribution

        dist = distribution("hephaistos")
        location = str(dist.locate_file("")) if dist else ""
        if "site-packages" in location:
            return "production"
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
    if _SENTRY_AVAILABLE:
        assert sentry_sdk is not None  # narrowed by _SENTRY_AVAILABLE guard
        if context:
            with sentry_sdk.new_scope() as scope:
                for key, value in context.items():
                    scope.set_extra(key, _scrub_value(value))
                event_id = sentry_sdk.capture_exception(exc)
        else:
            event_id = sentry_sdk.capture_exception(exc)
    else:
        event_id = None
    send_alert(logging.ERROR, "unhandled exception", str(exc or "unknown"))
    return event_id


# -- OpenTelemetry tracing ---------------------------------------------------


def init_tracing() -> None:
    """Initialise OpenTelemetry tracing.  No-op when ``opentelemetry-*``
    packages are not installed or ``OTEL_SDK_DISABLED`` is set."""
    if not _OTEL_AVAILABLE:
        return
    assert _trace_mod is not None  # narrowed by _OTEL_AVAILABLE guard
    assert _TracerProvider is not None  # narrowed by _OTEL_AVAILABLE guard
    assert _BatchSpanProcessor is not None  # narrowed by _OTEL_AVAILABLE guard

    import os

    if os.environ.get("OTEL_SDK_DISABLED", "").strip().lower() in ("true", "1"):
        return

    try:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter as _OTLPSpanExporter,
        )

        exporter = _OTLPSpanExporter()
    except Exception:  # pragma: no cover
        return

    provider = _TracerProvider(span_processor=_BatchSpanProcessor(exporter))
    _trace_mod.set_tracer_provider(provider)


def get_tracer(name: str) -> _NoopTracer | object:
    """Return a tracer for the given instrumentation scope.
    No-op when OpenTelemetry is not installed."""
    if not _OTEL_AVAILABLE:
        return _NoopTracer()
    assert _trace_mod is not None  # narrowed by _OTEL_AVAILABLE guard
    return _trace_mod.get_tracer(name)


# -- OpenTelemetry metrics ---------------------------------------------------


def init_metrics() -> None:
    """Initialise OpenTelemetry metrics.  No-op when ``opentelemetry-*``
    packages are not installed or ``OTEL_SDK_DISABLED`` is set."""
    if not _OTEL_AVAILABLE:
        return
    assert _metrics_mod is not None  # narrowed by _OTEL_AVAILABLE guard
    assert _PeriodicExportingMetricReader is not None  # narrowed by _OTEL_AVAILABLE guard
    assert _MeterProvider is not None  # narrowed by _OTEL_AVAILABLE guard

    import os

    if os.environ.get("OTEL_SDK_DISABLED", "").strip().lower() in ("true", "1"):
        return

    try:
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
            OTLPMetricExporter as _OTLPMetricExporter,
        )

        reader = _PeriodicExportingMetricReader(_OTLPMetricExporter())
    except Exception:  # pragma: no cover
        return

    provider = _MeterProvider(metric_readers=[reader])
    _metrics_mod.set_meter_provider(provider)


def get_meter(name: str) -> _NoopMeter | object:
    """Return a meter for the given instrumentation scope.
    No-op when OpenTelemetry is not installed."""
    if not _OTEL_AVAILABLE:
        return _NoopMeter()
    assert _metrics_mod is not None  # narrowed by _OTEL_AVAILABLE guard
    return _metrics_mod.get_meter(name)


# -- Webhook alerting --------------------------------------------------------


def init_alerting() -> None:
    """Initialise webhook alerting.  No-op when ``ALERT_WEBHOOK_URL`` is not set."""
    global _alert_webhook_url, _alert_min_level  # noqa: PLW0603
    url = os.environ.get(_ALERT_WEBHOOK_ENV, "").strip()
    _alert_webhook_url = url or None
    level_name = os.environ.get(_ALERT_MIN_LEVEL_ENV, _ALERT_MIN_LEVEL_DEFAULT).upper()
    _alert_min_level = getattr(logging, level_name, logging.ERROR)


def send_alert(level: int, title: str, body: str) -> None:
    """Send an alert via the configured webhook.  Rate-limited to one alert
    per key per 5 minutes.  No-op when ``ALERT_WEBHOOK_URL`` is not set or
    the level is below ``ALERT_MIN_LEVEL``."""
    if _alert_webhook_url is None:
        return
    if level < _alert_min_level:
        return
    key = f"{level}:{title}"
    now = _time.monotonic()
    last_sent = _alert_timestamps.get(key, 0.0)
    if now - last_sent < _ALERT_COOLDOWN_SECONDS:
        return
    _alert_timestamps[key] = now

    from datetime import UTC, datetime

    payload = _json.dumps(
        {
            "level": logging.getLevelName(level),
            "title": title,
            "body": body,
            "source": "hephaistos",
            "version": __version__,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    ).encode("utf-8")

    try:
        req = _urllib_request.Request(
            _alert_webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _urllib_request.urlopen(req, timeout=10) as resp:
            _log.debug("alert sent", extra={"fields": {"status": resp.status}})
    except Exception:  # nosec B110 — alert delivery is best-effort
        _log.debug("alert delivery failed", exc_info=True)


# -- Convenience init --------------------------------------------------------


def init_observability() -> None:
    """Initialise all observability subsystems (Sentry, OTel, alerting)."""
    init_sentry()
    init_tracing()
    init_metrics()
    init_alerting()


def shutdown_observability() -> None:
    """Flush and shut down observability subsystems."""
    if _OTEL_AVAILABLE and _trace_mod is not None:
        with contextlib.suppress(Exception):
            provider = _trace_mod.get_tracer_provider()
            if hasattr(provider, "force_flush"):
                provider.force_flush()  # type: ignore[union-attr]
            if hasattr(provider, "shutdown"):
                provider.shutdown()  # type: ignore[union-attr]
    if _OTEL_AVAILABLE and _metrics_mod is not None:
        with contextlib.suppress(Exception):
            provider = _metrics_mod.get_meter_provider()
            if hasattr(provider, "force_flush"):
                provider.force_flush()  # type: ignore[union-attr]
            if hasattr(provider, "shutdown"):
                provider.shutdown()  # type: ignore[union-attr]


# -- Trace context helper ----------------------------------------------------


def get_current_trace_id() -> str:
    """Return the current OTel trace ID (hex), or empty string if unavailable."""
    if not _OTEL_AVAILABLE:
        return ""
    assert _trace_mod is not None  # narrowed by _OTEL_AVAILABLE guard
    span = _trace_mod.get_current_span()
    ctx = span.get_span_context()
    if ctx.is_valid:
        return format(ctx.trace_id, "032x")
    return ""
