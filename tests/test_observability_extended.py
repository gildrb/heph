"""Tests for extended observability: tracing, metrics, and alerting."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

import hephaistos.observability as _obs_mod
from hephaistos.logging import _get_trace_context
from hephaistos.observability import (
    _NoopCounter,
    _NoopHistogram,
    _NoopMeter,
    _NoopSpan,
    _NoopTracer,
    get_current_trace_id,
    get_meter,
    get_tracer,
    init_alerting,
    init_observability,
    send_alert,
    shutdown_observability,
)

# ---------------------------------------------------------------------------
# No-op OTel classes
# ---------------------------------------------------------------------------


class TestNoopClasses:
    """No-op OTel classes should be transparent."""

    def test_noop_span_context_manager(self) -> None:
        span = _NoopSpan()
        with span as s:
            s.set_attribute("key", "value")
        # Should not raise

    def test_noop_span_end(self) -> None:
        span = _NoopSpan()
        span.end()  # Should not raise

    def test_noop_span_set_attribute_returns_self(self) -> None:
        span = _NoopSpan()
        result = span.set_attribute("key", "value")
        assert result is span

    def test_noop_tracer_start_span(self) -> None:
        tracer = _NoopTracer()
        span = tracer.start_span("test")
        assert isinstance(span, _NoopSpan)

    def test_noop_tracer_start_as_current_span(self) -> None:
        tracer = _NoopTracer()
        span = tracer.start_as_current_span("test")
        assert isinstance(span, _NoopSpan)

    def test_noop_meter_creates_instruments(self) -> None:
        meter = _NoopMeter()
        hist = meter.create_histogram("test")
        counter = meter.create_counter("test")
        ud_counter = meter.create_up_down_counter("test")
        assert isinstance(hist, _NoopHistogram)
        assert isinstance(counter, _NoopCounter)
        assert isinstance(ud_counter, _NoopCounter)

    def test_noop_histogram_record(self) -> None:
        hist = _NoopHistogram()
        hist.record(42.0, {"key": "value"})  # Should not raise

    def test_noop_counter_add(self) -> None:
        counter = _NoopCounter()
        counter.add(10, {"key": "value"})  # Should not raise


# ---------------------------------------------------------------------------
# get_tracer / get_meter
# ---------------------------------------------------------------------------


class TestGetTracerAndMeter:
    """get_tracer/get_meter should return no-op when OTel unavailable."""

    def test_get_tracer_returns_noop_without_otel(self) -> None:
        with patch("hephaistos.observability._OTEL_AVAILABLE", False):
            tracer = get_tracer("test")
            assert isinstance(tracer, _NoopTracer)

    def test_get_meter_returns_noop_without_otel(self) -> None:
        with patch("hephaistos.observability._OTEL_AVAILABLE", False):
            meter = get_meter("test")
            assert isinstance(meter, _NoopMeter)

    def test_get_tracer_span_usable(self) -> None:
        """Tracer (real or noop) should produce usable spans."""
        tracer = get_tracer("test")
        span = tracer.start_span("test")  # type: ignore[union-attr]
        span.set_attribute("key", "value")
        span.end()  # Should not raise

    def test_get_meter_instruments_usable(self) -> None:
        """Meter (real or noop) should produce usable instruments."""
        meter = get_meter("test")
        hist = meter.create_histogram("test")  # type: ignore[union-attr]
        hist.record(1.0)  # Should not raise


# ---------------------------------------------------------------------------
# Alerting
# ---------------------------------------------------------------------------


class TestAlerting:
    """Webhook alerting functionality."""

    @pytest.fixture(autouse=True)
    def _clear_alert_state(self) -> None:
        """Reset module-level alert timestamps between tests."""
        _obs_mod._alert_timestamps.clear()

    def test_send_alert_noop_without_webhook(self) -> None:
        """send_alert is a no-op when ALERT_WEBHOOK_URL is not configured."""
        with patch.dict("os.environ", {}, clear=True):
            init_alerting()
            # Should not raise or make any HTTP requests
            send_alert(logging.ERROR, "test title", "test body")

    def test_send_alert_respects_min_level(self) -> None:
        """send_alert skips alerts below ALERT_MIN_LEVEL."""
        with patch.dict(
            "os.environ",
            {"ALERT_WEBHOOK_URL": "http://localhost:9999", "ALERT_MIN_LEVEL": "CRITICAL"},
            clear=True,
        ):
            init_alerting()
            with patch("hephaistos.observability._urllib_request.urlopen") as mock_urlopen:
                # ERROR < CRITICAL, should be skipped
                send_alert(logging.ERROR, "test", "body")
                mock_urlopen.assert_not_called()

    def test_send_alert_sends_when_level_sufficient(self) -> None:
        """send_alert dispatches when level >= ALERT_MIN_LEVEL."""
        with patch.dict(
            "os.environ",
            {"ALERT_WEBHOOK_URL": "http://localhost:9999", "ALERT_MIN_LEVEL": "WARNING"},
            clear=True,
        ):
            init_alerting()
            with patch("hephaistos.observability._urllib_request.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                mock_urlopen.return_value = mock_response

                send_alert(logging.ERROR, "sufficient-level", "body")
                assert mock_urlopen.call_count == 1

    def test_send_alert_rate_limits(self) -> None:
        """send_alert rate-limits duplicate alerts within cooldown."""
        with patch.dict(
            "os.environ",
            {"ALERT_WEBHOOK_URL": "http://localhost:9999"},
            clear=True,
        ):
            init_alerting()
            with patch("hephaistos.observability._urllib_request.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                mock_urlopen.return_value = mock_response

                send_alert(logging.ERROR, "rate-test", "first")
                assert mock_urlopen.call_count == 1

                # Second call within cooldown should be rate-limited
                send_alert(logging.ERROR, "rate-test", "second")
                assert mock_urlopen.call_count == 1

    def test_send_alert_sends_after_cooldown(self) -> None:
        """send_alert dispatches again after the cooldown window expires."""
        with patch.dict(
            "os.environ",
            {"ALERT_WEBHOOK_URL": "http://localhost:9999"},
            clear=True,
        ):
            init_alerting()
            key = f"{logging.ERROR}:cooldown-test"
            # Simulate a previous alert sent long ago
            _obs_mod._alert_timestamps[key] = (
                _obs_mod._time.monotonic() - _obs_mod._ALERT_COOLDOWN_SECONDS - 1
            )

            with patch("hephaistos.observability._urllib_request.urlopen") as mock_urlopen:
                mock_response = MagicMock()
                mock_response.status = 200
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                mock_urlopen.return_value = mock_response

                send_alert(logging.ERROR, "cooldown-test", "after cooldown")
                assert mock_urlopen.call_count == 1

    def test_send_alert_handles_urlopen_failure(self) -> None:
        """send_alert should not raise when the HTTP request fails."""
        with patch.dict(
            "os.environ",
            {"ALERT_WEBHOOK_URL": "http://localhost:9999"},
            clear=True,
        ):
            init_alerting()
            with patch("hephaistos.observability._urllib_request.urlopen") as mock_urlopen:
                mock_urlopen.side_effect = OSError("connection refused")
                # Should not raise
                send_alert(logging.ERROR, "fail-test", "body")

    def test_init_alerting_reads_env(self) -> None:
        """init_alerting reads ALERT_WEBHOOK_URL and ALERT_MIN_LEVEL from env."""
        with patch.dict(
            "os.environ",
            {"ALERT_WEBHOOK_URL": "http://example.com/webhook", "ALERT_MIN_LEVEL": "WARNING"},
            clear=True,
        ):
            init_alerting()
            assert _obs_mod._alert_webhook_url == "http://example.com/webhook"
            assert _obs_mod._alert_min_level == logging.WARNING

    def test_init_alerting_defaults(self) -> None:
        """init_alerting uses sensible defaults when env vars are unset."""
        with patch.dict("os.environ", {}, clear=True):
            init_alerting()
            assert _obs_mod._alert_webhook_url is None
            assert _obs_mod._alert_min_level == logging.ERROR

    def test_init_alerting_invalid_level_defaults_to_error(self) -> None:
        """init_alerting falls back to ERROR for an unrecognized level name."""
        with patch.dict(
            "os.environ",
            {"ALERT_WEBHOOK_URL": "http://localhost:9999", "ALERT_MIN_LEVEL": "BOGUS"},
            clear=True,
        ):
            init_alerting()
            assert _obs_mod._alert_min_level == logging.ERROR


# ---------------------------------------------------------------------------
# Trace context
# ---------------------------------------------------------------------------


class TestTraceContext:
    """Trace context helpers."""

    def test_get_current_trace_id_empty_without_otel(self) -> None:
        """get_current_trace_id returns empty string when OTel not available."""
        with patch("hephaistos.observability._OTEL_AVAILABLE", False):
            result = get_current_trace_id()
            assert result == ""

    def test_get_current_trace_id_empty_no_active_span(self) -> None:
        """get_current_trace_id returns empty string when no active span."""
        result = get_current_trace_id()
        # Without an active OTel span, returns "" or an empty trace
        assert isinstance(result, str)

    def test_logging_get_trace_context_empty(self) -> None:
        """_get_trace_context returns empty dict when OTel not available."""
        with patch.dict("sys.modules", {"opentelemetry.trace": None}):
            # Force ImportError path
            result = _get_trace_context()
            assert result == {}

    def test_logging_get_trace_context_returns_dict(self) -> None:
        """_get_trace_context always returns a dict type."""
        result = _get_trace_context()
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# init_observability / shutdown_observability
# ---------------------------------------------------------------------------


class TestInitObservability:
    """init_observability and shutdown_observability."""

    def test_init_observability_no_error(self) -> None:
        """init_observability should not raise even without any env vars."""
        with patch.dict("os.environ", {}, clear=True):
            init_observability()

    def test_shutdown_observability_no_error(self) -> None:
        """shutdown_observability should not raise even without OTel."""
        shutdown_observability()

    def test_init_observability_calls_all_inits(self) -> None:
        """init_observability delegates to init_sentry, init_tracing,
        init_metrics, and init_alerting."""
        with (
            patch("hephaistos.observability.init_sentry") as mock_sentry,
            patch("hephaistos.observability.init_tracing") as mock_tracing,
            patch("hephaistos.observability.init_metrics") as mock_metrics,
            patch("hephaistos.observability.init_alerting") as mock_alerting,
        ):
            init_observability()
            mock_sentry.assert_called_once()
            mock_tracing.assert_called_once()
            mock_metrics.assert_called_once()
            mock_alerting.assert_called_once()

    def test_shutdown_observability_noop_without_otel(self) -> None:
        """shutdown_observability is a safe no-op when OTel is not available."""
        with patch("hephaistos.observability._OTEL_AVAILABLE", False):
            shutdown_observability()  # Should not raise
