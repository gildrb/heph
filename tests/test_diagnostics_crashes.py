from __future__ import annotations

from hephaistos.diagnostics.crashes import (
    _REDACTED,
    _redact_event,
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


class TestRedactEvent:
    def test_redacts_user_sections_only(self) -> None:
        event = {
            "event_id": "evt_123",
            "extra": {"api_key": "a" * 40},
            "contexts": {"runtime": {"provider": "openrouter"}},
        }
        result = _redact_event(event, {})
        assert result is not None
        assert result["event_id"] == "evt_123"
        assert result["extra"]["api_key"] == _REDACTED  # ty:ignore[not-subscriptable]
        assert result["contexts"]["runtime"]["provider"] == "openrouter"  # ty:ignore[not-subscriptable]


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
