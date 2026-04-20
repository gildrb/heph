from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from hephaistos.observability import (
    _REDACTED,  # type: ignore[reportPrivateUsage]
    _detect_environment,  # type: ignore[reportPrivateUsage]
    _parse_traces_rate,  # type: ignore[reportPrivateUsage]
    _redact_event,  # type: ignore[reportPrivateUsage]
    _scrub_value,  # type: ignore[reportPrivateUsage]
    add_breadcrumb,
    capture_exception,
    init_sentry,
    set_session_context,
)


@contextmanager
def _mock_sentry():
    """Patch ``sentry_sdk`` and ``_sentry_available`` so tests can mock attributes.

    When ``sentry-sdk`` is not installed, the module-level ``sentry_sdk`` is
    ``None``, making ``patch("hephaistos.observability.sentry_sdk.init")`` fail
    with ``AttributeError: None has no attribute 'init'``.  This helper
    replaces the module-level ``sentry_sdk`` name with a fresh ``MagicMock``
    and sets ``_sentry_available = True`` so the guard clause is bypassed.
    """
    mock_sdk = MagicMock()
    with (
        patch("hephaistos.observability.sentry_sdk", mock_sdk),
        patch("hephaistos.observability._sentry_available", True),
        patch("hephaistos.observability.LoggingIntegration", MagicMock()),
    ):
        yield mock_sdk


# -- _scrub_value ------------------------------------------------------------


class TestScrubValue:
    def test_redacts_sensitive_keys(self) -> None:
        result = _scrub_value({"api_key": "abc", "safe": "xyz"})
        assert result["api_key"] == _REDACTED  # type: ignore[index]
        assert result["safe"] == "xyz"  # type: ignore[index]

    def test_redacts_nested_sensitive_keys(self) -> None:
        data = {"request": {"headers": {"authorization": "Bearer xyz123"}}}
        result = _scrub_value(data)
        assert result["request"]["headers"]["authorization"] == _REDACTED  # type: ignore[index]

    def test_redacts_sensitive_values(self) -> None:
        result = _scrub_value({"key": "a" * 40})
        assert result["key"] == _REDACTED  # type: ignore[index]

    def test_redacts_bearer_tokens(self) -> None:
        result = _scrub_value({"auth": "Bearer TESTFAKEBEARERTOKENVALUE"})
        assert result["auth"] == _REDACTED  # type: ignore[index]

    def test_redacts_long_hex_strings(self) -> None:
        result = _scrub_value({"token": "a" * 40})
        assert result["token"] == _REDACTED  # type: ignore[index]

    def test_preserves_non_sensitive_data(self) -> None:
        data = {"model": "gpt-4o", "latency_ms": 340, "count": 42}
        result = _scrub_value(data)
        assert result == data

    def test_handles_lists(self) -> None:
        data = [{"api_key": "secret"}, {"safe": "value"}]
        result = _scrub_value(data)
        assert result[0]["api_key"] == _REDACTED  # type: ignore[index]
        assert result[1]["safe"] == "value"  # type: ignore[index]

    def test_handles_non_string_values(self) -> None:
        data = {"count": 42, "rate": 0.1, "flag": True, "none_val": None}
        result = _scrub_value(data)
        assert result == data

    def test_deeply_nested_structure(self) -> None:
        data = {"level1": {"level2": {"level3": {"password": "hunter2"}}}}
        result = _scrub_value(data)
        assert result["level1"]["level2"]["level3"]["password"] == _REDACTED  # type: ignore[index]


# -- _redact_event -----------------------------------------------------------


class TestRedactEvent:
    def test_redacts_event_with_sensitive_data(self) -> None:
        event = {
            "extra": {"api_key": "a" * 40},
            "tags": {"provider": "openrouter"},
        }
        result = _redact_event(event, {})
        assert result is not None
        assert result["extra"]["api_key"] == _REDACTED  # type: ignore[index]
        assert result["tags"]["provider"] == "openrouter"  # type: ignore[index]

    def test_preserves_sentry_internal_fields(self) -> None:
        event = {
            "event_id": "aabbccddeeff00112233445566778899",
            "platform": "python",
            "release": "hephaistos@0.1.0",
            "environment": "development",
            "extra": {"safe": "value"},
        }
        result = _redact_event(event, {})
        assert result is not None
        assert result["event_id"] == "aabbccddeeff00112233445566778899"
        assert result["platform"] == "python"
        assert result["release"] == "hephaistos@0.1.0"
        assert result["environment"] == "development"

    def test_scrubs_contexts_section(self) -> None:
        event = {
            "event_id": "aabbccddeeff00112233445566778899",
            "contexts": {"app": {"api_key": "b" * 40}},
        }
        result = _redact_event(event, {})
        assert result is not None
        assert result["event_id"] == "aabbccddeeff00112233445566778899"
        assert result["contexts"]["app"]["api_key"] == _REDACTED  # type: ignore[index]


# -- init_sentry -------------------------------------------------------------


class TestInitSentry:
    def test_noop_without_dsn(self) -> None:
        with (
            _mock_sentry() as mock_sdk,
            patch.dict(os.environ, {}, clear=True),
        ):
            init_sentry()
            mock_sdk.init.assert_not_called()

    def test_initializes_with_dsn(self) -> None:
        with (
            _mock_sentry() as mock_sdk,
            patch.dict(os.environ, {"SENTRY_DSN": "https://key@sentry.io/123"}),
        ):
            init_sentry()
            mock_sdk.init.assert_called_once()
            call_kwargs = mock_sdk.init.call_args[1]
            assert call_kwargs["dsn"] == "https://key@sentry.io/123"
            assert "release" in call_kwargs
            assert call_kwargs["before_send"] is _redact_event

    def test_uses_custom_environment(self) -> None:
        with (
            _mock_sentry() as mock_sdk,
            patch.dict(
                os.environ,
                {"SENTRY_DSN": "https://key@sentry.io/123", "SENTRY_ENVIRONMENT": "staging"},
            ),
        ):
            init_sentry()
            call_kwargs = mock_sdk.init.call_args[1]
            assert call_kwargs["environment"] == "staging"

    def test_auto_detects_environment(self) -> None:
        env = {"SENTRY_DSN": "https://key@sentry.io/123"}
        with (
            _mock_sentry() as mock_sdk,
            patch.dict(os.environ, env, clear=False),
            patch("hephaistos.observability._detect_environment", return_value="development"),
        ):
            os.environ.pop("SENTRY_ENVIRONMENT", None)
            init_sentry()
            call_kwargs = mock_sdk.init.call_args[1]
            assert call_kwargs["environment"] == "development"

    def test_sets_platform_tag(self) -> None:
        with (
            _mock_sentry() as mock_sdk,
            patch.dict(os.environ, {"SENTRY_DSN": "https://key@sentry.io/123"}),
        ):
            init_sentry()
            mock_sdk.set_tag.assert_any_call("platform", "cli")

    def test_logging_integration_configured(self) -> None:
        li_mock = MagicMock()
        with (
            _mock_sentry() as mock_sdk,
            patch.dict(os.environ, {"SENTRY_DSN": "https://key@sentry.io/123"}),
            patch("hephaistos.observability.LoggingIntegration", li_mock),
        ):
            init_sentry()
            call_kwargs = mock_sdk.init.call_args[1]
            integrations = call_kwargs["integrations"]
            assert len(integrations) == 1
            li_mock.assert_called_once_with(
                level=logging.INFO,
                event_level=logging.CRITICAL,
            )


# -- _detect_environment -----------------------------------------------------


class TestDetectEnvironment:
    def test_returns_development_by_default(self) -> None:
        with patch("importlib.metadata.distribution", side_effect=Exception):
            assert _detect_environment() == "development"


# -- _parse_traces_rate ------------------------------------------------------


class TestParseTracesRate:
    def test_parses_valid_rate(self) -> None:
        with patch.dict(os.environ, {"SENTRY_TRACES_SAMPLE_RATE": "0.5"}):
            assert _parse_traces_rate() == 0.5

    def test_clamps_to_max(self) -> None:
        with patch.dict(os.environ, {"SENTRY_TRACES_SAMPLE_RATE": "2.0"}):
            assert _parse_traces_rate() == 1.0

    def test_clamps_to_min(self) -> None:
        with patch.dict(os.environ, {"SENTRY_TRACES_SAMPLE_RATE": "-0.5"}):
            assert _parse_traces_rate() == 0.0

    def test_defaults_on_invalid(self) -> None:
        with patch.dict(os.environ, {"SENTRY_TRACES_SAMPLE_RATE": "invalid"}):
            assert _parse_traces_rate() == 0.1

    def test_defaults_on_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            assert _parse_traces_rate() == 0.1


# -- set_session_context -----------------------------------------------------


class TestSetSessionContext:
    def test_sets_tags(self) -> None:
        with _mock_sentry() as mock_sdk:
            set_session_context(
                session_id="abc",
                armory="my-armory",
                provider="openrouter",
                model="gpt-4o",
            )
            assert mock_sdk.set_tag.call_count == 4

    def test_skips_empty_tags(self) -> None:
        with _mock_sentry() as mock_sdk:
            set_session_context(session_id="abc")
            assert mock_sdk.set_tag.call_count == 1


# -- add_breadcrumb ----------------------------------------------------------


class TestAddBreadcrumb:
    def test_adds_breadcrumb(self) -> None:
        with _mock_sentry() as mock_sdk:
            add_breadcrumb("auth", "user logged in")
            mock_sdk.add_breadcrumb.assert_called_once()
            call_kwargs = mock_sdk.add_breadcrumb.call_args[1]
            assert call_kwargs["category"] == "auth"
            assert call_kwargs["message"] == "user logged in"

    def test_scrubs_breadcrumb_data(self) -> None:
        with _mock_sentry() as mock_sdk:
            add_breadcrumb("api", "request sent", api_key="c" * 40)
            call_kwargs = mock_sdk.add_breadcrumb.call_args[1]
            assert call_kwargs["data"]["api_key"] == _REDACTED


# -- capture_exception -------------------------------------------------------


class TestCaptureException:
    def test_captures_exception(self) -> None:
        with _mock_sentry() as mock_sdk:
            exc = RuntimeError("test")
            capture_exception(exc)
            mock_sdk.capture_exception.assert_called_once_with(exc)

    def test_captures_with_context(self) -> None:
        with _mock_sentry() as mock_sdk:
            scope_instance = MagicMock()
            mock_sdk.new_scope.return_value.__enter__ = MagicMock(return_value=scope_instance)
            mock_sdk.new_scope.return_value.__exit__ = MagicMock(return_value=False)
            capture_exception(RuntimeError("test"), context={"model": "gpt-4o"})
            scope_instance.set_extra.assert_called_once()


# -- no-sentry fallback ------------------------------------------------------


class TestNoSentryFallback:
    """Verify every public function is a safe no-op when sentry_sdk is absent."""

    def test_init_sentry_noop(self) -> None:
        with patch("hephaistos.observability._sentry_available", False):
            init_sentry()  # should not raise

    def test_set_session_context_noop(self) -> None:
        with patch("hephaistos.observability._sentry_available", False):
            set_session_context(session_id="abc", armory="x", provider="y", model="z")

    def test_add_breadcrumb_noop(self) -> None:
        with patch("hephaistos.observability._sentry_available", False):
            add_breadcrumb("cat", "msg", extra_key="val")

    def test_capture_exception_noop(self) -> None:
        with patch("hephaistos.observability._sentry_available", False):
            result = capture_exception(RuntimeError("boom"))
            assert result is None

    def test_capture_exception_with_context_noop(self) -> None:
        with patch("hephaistos.observability._sentry_available", False):
            result = capture_exception(RuntimeError("boom"), context={"model": "gpt-4o"})
            assert result is None
