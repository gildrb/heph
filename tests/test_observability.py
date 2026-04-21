from __future__ import annotations

from hephaistos.observability import (
    _REDACTED,  # type: ignore[reportPrivateUsage]
    _redact_event,  # type: ignore[reportPrivateUsage]
    _scrub_value,  # type: ignore[reportPrivateUsage]
    add_breadcrumb,
    capture_exception,
    init_alerting,
    init_metrics,
    init_observability,
    init_sentry,
    init_tracing,
    set_session_context,
    shutdown_observability,
)


class TestScrubValue:
    def test_redacts_sensitive_keys(self) -> None:
        result = _scrub_value({"api_key": "secret", "safe": "value"})
        assert result["api_key"] == _REDACTED  # type: ignore[index]
        assert result["safe"] == "value"  # type: ignore[index]

    def test_redacts_nested_sensitive_values(self) -> None:
        result = _scrub_value({"request": {"authorization": "Bearer TESTTOKEN"}})
        assert result["request"]["authorization"] == _REDACTED  # type: ignore[index]

    def test_handles_lists(self) -> None:
        result = _scrub_value([{"token": "a" * 40}, {"safe": "ok"}])
        assert result[0]["token"] == _REDACTED  # type: ignore[index]
        assert result[1]["safe"] == "ok"  # type: ignore[index]


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
        assert result["extra"]["api_key"] == _REDACTED  # type: ignore[index]
        assert result["contexts"]["runtime"]["provider"] == "openrouter"  # type: ignore[index]


class TestLocalNoops:
    def test_init_helpers_are_noops(self) -> None:
        init_sentry()
        init_tracing()
        init_metrics()
        init_alerting()
        init_observability()
        shutdown_observability()

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
