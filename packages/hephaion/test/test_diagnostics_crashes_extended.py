"""Tests for the local diagnostics shims exposed via diagnostics.crashes."""

from __future__ import annotations

from diagnostics.crashes import (
    _NoopCounter,
    _NoopGauge,
    _NoopHistogram,
    _NoopMeter,
    _NoopSpan,
    _NoopTracer,
    get_current_trace_id,
    get_meter,
    get_tracer,
)


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
        assert isinstance(get_tracer("runtime.engine"), _NoopTracer)

    def test_get_meter_returns_noop_meter(self) -> None:
        assert isinstance(get_meter("runtime.engine"), _NoopMeter)

    def test_get_current_trace_id_is_empty(self) -> None:
        assert get_current_trace_id() == ""
