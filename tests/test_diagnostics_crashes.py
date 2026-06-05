from __future__ import annotations

import pytest
from hephaion.diagnostics.crashes import (
    _REDACTED,
    _parse_sentry_dsn,
    _scrub_value,
    add_breadcrumb,
    capture_exception,
    init_alerting,
    init_diagnostics,
    init_metrics,
    init_sentry,
    init_tracing,
    set_session_context,
    shutdown_diagnostics,
)


class TestScrubValue:
    def test_redacts_sensitive_keys(self) -> None:
        result = _scrub_value({"api_key": "secret", "safe": "value"})
        assert result["api_key"] == _REDACTED  # ty:ignore[not-subscriptable]
        assert result["safe"] == "value"  # ty:ignore[not-subscriptable]

    def test_redacts_nested_sensitive_values(self) -> None:
        result = _scrub_value({"request": {"authorization": "Bearer TESTTOKEN"}})
        assert result["request"]["authorization"] == _REDACTED  # ty:ignore[not-subscriptable]

    def test_handles_lists(self) -> None:
        result = _scrub_value([{"token": "a" * 40}, {"safe": "ok"}])
        assert result[0]["token"] == _REDACTED  # ty:ignore[not-subscriptable]
        assert result[1]["safe"] == "ok"  # ty:ignore[not-subscriptable]

    def test_redacts_provider_key_formats_in_safe_string_fields(self) -> None:
        result = _scrub_value({"detail": "key sk-or-v1-" + "a" * 32})

        assert result["detail"] == f"key {_REDACTED}"  # ty:ignore[not-subscriptable]


class TestLocalNoops:
    def test_init_helpers_are_noops(self) -> None:
        init_sentry()
        init_tracing()
        init_metrics()
        init_alerting()
        init_diagnostics()
        shutdown_diagnostics()

    def test_set_session_context_is_noop(self) -> None:
        set_session_context(session_id="abc", armory="armory", provider="openai", model="gpt-5")

    def test_add_breadcrumb_is_noop(self) -> None:
        add_breadcrumb("chat", "message sent", level="info", model="gpt-5")

    def test_capture_exception_returns_none(self) -> None:
        exc = RuntimeError("boom")
        result = capture_exception(exc, context={"api_key": "a" * 40, "model": "gpt-5"})
        assert result is None

    def test_capture_exception_none_returns_none(self) -> None:
        assert capture_exception(None) is None


def test_sentry_dsn_requires_https() -> None:
    with pytest.raises(ValueError, match="Invalid Sentry DSN"):
        _parse_sentry_dsn("http://public@example.com/1")
