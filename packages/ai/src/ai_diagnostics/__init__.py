from __future__ import annotations

from typing import Self


class NoopSpan:
    __slots__ = ()

    def set_attribute(self, key: str, value: object) -> object:
        del key, value
        return self

    def end(self, end_time: float | None = None) -> None:
        del end_time

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: object) -> None:
        self.end()


class NoopTracer:
    __slots__ = ()

    def start_span(self, name: str, **kwargs: object) -> NoopSpan:
        del name, kwargs
        return NoopSpan()

    def start_as_current_span(self, name: str, **kwargs: object) -> NoopSpan:
        del name, kwargs
        return NoopSpan()


class NoopInstrument:
    __slots__ = ()

    def record(self, value: float, _attributes: dict[str, str] | None = None) -> None:
        del value, _attributes

    def add(self, value: float, _attributes: dict[str, str] | None = None) -> None:
        del value, _attributes

    def set(self, value: float, _attributes: dict[str, str] | None = None) -> None:
        del value, _attributes


class NoopMeter:
    __slots__ = ()

    def create_histogram(self, name: str, **kwargs: object) -> NoopInstrument:
        del name, kwargs
        return NoopInstrument()

    def create_counter(self, name: str, **kwargs: object) -> NoopInstrument:
        del name, kwargs
        return NoopInstrument()

    create_up_down_counter = create_counter

    def create_gauge(self, name: str, **kwargs: object) -> NoopInstrument:
        del name, kwargs
        return NoopInstrument()


_NOOP_TRACER = NoopTracer()
_NOOP_METER = NoopMeter()


def get_tracer(name: str) -> NoopTracer:
    del name
    return _NOOP_TRACER


def get_meter(name: str) -> NoopMeter:
    del name
    return _NOOP_METER
