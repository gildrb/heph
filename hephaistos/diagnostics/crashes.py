from __future__ import annotations

import json
import re as _re
import traceback
import urllib.parse
import urllib.request
import uuid
from collections import deque
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Final, Self

from hephaistos import __version__
from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.logging import get_logger, redact_text
from hephaistos.privacy.consent import (
    crash_reports_backend_available,
    crash_reports_enabled,
    release_channel,
    runtime_context,
    sentry_dsn,
)

_log = get_logger("diagnostics")


class _NoopSpan:
    __slots__ = ()

    def set_attribute(self, _key: str, _value: object) -> object:
        return self

    def end(self, _end_time: float | None = None) -> None:
        pass

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.end()


class _NoopTracer:
    __slots__ = ()

    def start_span(self, _name: str, **_kwargs: object) -> _NoopSpan:
        return _NoopSpan()

    def start_as_current_span(self, _name: str, **_kwargs: object) -> _NoopSpan:
        return _NoopSpan()


class _NoopInstrument:
    __slots__ = ()

    def record(self, value: float, _attributes: dict[str, str] | None = None) -> None:
        pass

    def add(self, value: float, _attributes: dict[str, str] | None = None) -> None:
        pass

    def set(self, value: float, _attributes: dict[str, str] | None = None) -> None:
        pass


_NoopHistogram = _NoopInstrument
_NoopCounter = _NoopInstrument
_NoopGauge = _NoopInstrument


class _NoopMeter:
    __slots__ = ()

    def create_histogram(self, name: str, **_kwargs: object) -> _NoopInstrument:
        del name
        return _NoopInstrument()

    def create_counter(self, name: str, **_kwargs: object) -> _NoopInstrument:
        del name
        return _NoopInstrument()

    create_up_down_counter = create_counter

    def create_gauge(self, name: str, **_kwargs: object) -> _NoopInstrument:
        del name
        return _NoopInstrument()


_SENSITIVE_KEY_PATTERNS: Final[list[_re.Pattern[str]]] = [
    _re.compile(r"(?i)(api.?key|secret|token(?!s)|password|auth(orization|entication))"),
    _re.compile(r"(?i)(bearer|credential|private.?key)"),
]
_REDACTED = "***REDACTED***"
_DROP_KEYS = frozenset({"prompt", "content", "message", "path", "filename", "armory", "text"})
_BREADCRUMBS: deque[dict[str, object]] = deque(maxlen=25)
_SESSION_CONTEXT: dict[str, str] = {}


def _safe_string(key: str, value: str) -> str | None:
    lowered = key.lower()
    if lowered in _DROP_KEYS:
        return None
    if lowered.endswith(("path", "file", "filename")) and value:
        return None
    if len(value) > 160:
        return None
    return redact_text(value)


def _scrub_value(value: object) -> object:
    if is_string_mapping(value):
        cleaned: dict[str, object] = {}
        for key, nested in value.items():
            lowered = key.lower()
            if lowered in _DROP_KEYS or any(p.search(key) for p in _SENSITIVE_KEY_PATTERNS):
                cleaned[key] = _REDACTED
                continue
            if isinstance(nested, str):
                safe = _safe_string(lowered, nested)
                cleaned[key] = safe if safe is not None else _REDACTED
            else:
                cleaned[key] = _scrub_value(nested)
        return cleaned
    if is_object_list(value):
        return [_scrub_value(item) for item in value]
    if isinstance(value, str):
        safe = _safe_string("value", value)
        return safe if safe is not None else _REDACTED
    return value


def _parse_sentry_dsn(dsn: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(dsn)
    if not parsed.scheme or not parsed.hostname or not parsed.username:
        raise ValueError("Invalid Sentry DSN")
    path_parts = [part for part in parsed.path.split("/") if part]
    if not path_parts:
        raise ValueError("Invalid Sentry DSN")
    project_id = path_parts[-1]
    path_prefix = "/" + "/".join(path_parts[:-1]) if len(path_parts) > 1 else ""
    auth_parts = [
        "Sentry sentry_version=7",
        f"sentry_client=hephaistos/{__version__}",
        f"sentry_key={parsed.username}",
    ]
    if parsed.password:
        auth_parts.append(f"sentry_secret={parsed.password}")
    auth_header = ", ".join(auth_parts)
    endpoint = urllib.parse.urlunparse(
        (
            parsed.scheme,
            parsed.netloc.rsplit("@", 1)[-1],
            f"{path_prefix}/api/{project_id}/store/",
            "",
            "",
            "",
        )
    )
    return endpoint, auth_header


def _exception_payload(
    exc: BaseException,
    context: Mapping[str, object] | None,
) -> dict[str, object]:
    extra: dict[str, object] = {}
    if context:
        scrubbed_context = _scrub_value(dict(context))
        if is_string_mapping(scrubbed_context):
            extra.update(scrubbed_context)

    tb_summary: list[traceback.FrameSummary] = (
        list(traceback.extract_tb(exc.__traceback__)) if exc.__traceback__ is not None else []
    )
    if tb_summary:
        extra["traceback"] = {
            "frame_count": len(tb_summary),
            "functions": [frame.name for frame in tb_summary[-8:]],
        }

    return {
        "event_id": uuid.uuid4().hex,
        "timestamp": datetime.now(UTC).isoformat(),
        "platform": "python",
        "level": "error",
        "logger": "hephaistos",
        "release": f"hephaistos@{__version__}",
        "environment": release_channel(),
        "server_name": "hephaistos-cli",
        "tags": {
            **runtime_context(),
            **_SESSION_CONTEXT,
        },
        "breadcrumbs": {"values": list(_BREADCRUMBS)},
        "exception": {
            "values": [
                {
                    "type": exc.__class__.__name__,
                    "value": _scrub_value(str(exc)),
                }
            ]
        },
        "extra": extra,
    }


def init_sentry() -> None:
    if crash_reports_backend_available():
        _log.debug("crash reporting configured")


def set_session_context(
    *,
    session_id: str = "",
    armory: str = "",
    provider: str = "",
    model: str = "",
) -> None:
    if session_id:
        _SESSION_CONTEXT["session_id"] = session_id
    if armory:
        _SESSION_CONTEXT["armory_state"] = armory
    if provider:
        _SESSION_CONTEXT["provider"] = provider
    if model:
        _SESSION_CONTEXT["model"] = model


def add_breadcrumb(
    category: str,
    message: str,
    *,
    level: str = "info",
    **data: object,
) -> None:
    breadcrumb: dict[str, object] = {
        "timestamp": datetime.now(UTC).isoformat(),
        "category": redact_text(category),
        "message": redact_text(message),
        "level": level,
    }
    if data:
        breadcrumb["data"] = _scrub_value(data)
    _BREADCRUMBS.append(breadcrumb)


def capture_exception(
    exc: BaseException | None = None,
    *,
    context: dict[str, object] | None = None,
) -> str | None:
    if exc is None:
        return None

    fields: dict[str, object] = {
        "error_type": exc.__class__.__name__,
        "error": redact_text(str(exc)),
    }
    if context:
        fields["context"] = _scrub_value(context)
    _log.debug("exception captured", extra={"fields": fields})

    if not crash_reports_backend_available() or not crash_reports_enabled():
        return None

    try:
        endpoint, auth_header = _parse_sentry_dsn(sentry_dsn())
        payload = _exception_payload(exc, context)
        request = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "X-Sentry-Auth": auth_header,
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=5):  # nosec B310
            return str(payload["event_id"])
    except Exception:  # nosec B110 - crash reporting is best effort
        _log.debug("remote crash report failed", exc_info=True)
        return None


def init_tracing() -> None:
    pass


def get_tracer(_name: str) -> _NoopTracer:
    return _NOOP_TRACER


def init_metrics() -> None:
    pass


def get_meter(_name: str) -> _NoopMeter:
    return _NOOP_METER


def init_alerting() -> None:
    pass


def init_diagnostics() -> None:
    init_sentry()


def shutdown_diagnostics() -> None:
    pass


def get_current_trace_id() -> str:
    return ""


def reset_state() -> None:
    _BREADCRUMBS.clear()
    _SESSION_CONTEXT.clear()


_NOOP_TRACER = _NoopTracer()
_NOOP_METER = _NoopMeter()
