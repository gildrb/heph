"""Tests for the local diagnostics shims exposed via hephaistos.diagnostics.crashes."""

from __future__ import annotations

from hephaistos.diagnostics.crashes import (
    _NoopCounter,  # type: ignore[reportPrivateUsage]
    _NoopGauge,  # type: ignore[reportPrivateUsage]
    _NoopHistogram,  # type: ignore[reportPrivateUsage]
    _NoopMeter,  # type: ignore[reportPrivateUsage]
    _NoopSpan,  # type: ignore[reportPrivateUsage]
    _NoopTracer,  # type: ignore[reportPrivateUsage]
    get_current_trace_id,
    get_meter,
    get_tracer,
)
from hephaistos.logging import _get_trace_context  # type: ignore[reportPrivateUsage]


class TestNoopClasses:
    def test_noop_span_context_manager(self) -> None:
        span = _NoopSpan()
        with span as current:
            current.set_attribute("key", "value")

    def test_noop_tracer_returns_noop_span(self) -> None:
        tracer = _NoopTracer()
        assert isinstance(tracer.start_span("test"), _NoopSpan)
        assert isinstance(tracer.start_as_current_span("test"), _NoopSpan)

    def test_noop_meter_creates_instruments(self) -> None:
        meter = _NoopMeter()
        assert isinstance(meter.create_histogram("duration"), _NoopHistogram)
        assert isinstance(meter.create_counter("tokens"), _NoopCounter)
        assert isinstance(meter.create_up_down_counter("count"), _NoopCounter)
        assert isinstance(meter.create_gauge("state"), _NoopGauge)

    def test_instruments_are_usable(self) -> None:
        _NoopHistogram().record(1.0, {"kind": "test"})
        _NoopCounter().add(1.0, {"kind": "test"})
        _NoopGauge().set(1.0, {"kind": "test"})


class TestAccessors:
    def test_get_tracer_returns_noop_tracer(self) -> None:
        assert isinstance(get_tracer("chat.engine"), _NoopTracer)

    def test_get_meter_returns_noop_meter(self) -> None:
        assert isinstance(get_meter("chat.engine"), _NoopMeter)

    def test_get_current_trace_id_is_empty(self) -> None:
        assert get_current_trace_id() == ""

    def test_logging_trace_context_is_empty(self) -> None:
        assert _get_trace_context() == {}
