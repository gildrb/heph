"""Route primitives for the SDK service facade."""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass

from heph.sdk.config import (
    SdkConfigUpdate,
    SdkConfigUpdateName,
    SdkConfigUpdateValue,
)
from heph.sdk.methods import SdkMethodParameter
from heph.sdk.state import HephSdkMethodAvailability

type ServicePayload = dict[str, object]
type ServiceStream = Iterator[ServicePayload]
type _ServiceCallArgumentDecoder = Callable[[Mapping[str, object], str], object]
type _ServiceCallHandler = Callable[..., ServicePayload]
type _ServiceStreamHandler = Callable[..., ServiceStream]
type _ServiceConfigParamDecoder = Callable[
    [Mapping[str, object], str],
    SdkConfigUpdateValue | None,
]


@dataclass(frozen=True, slots=True)
class _ServiceCallArgument:
    name: str
    decoder: _ServiceCallArgumentDecoder
    value_type: str
    required: bool = True
    choices: tuple[str, ...] = ()

    def value_from(self, params: Mapping[str, object]) -> object:
        return self.decoder(params, self.name)


@dataclass(frozen=True, slots=True)
class _ServiceCallRoute:
    method: str
    handler: _ServiceCallHandler
    arguments: tuple[_ServiceCallArgument, ...] = ()
    keyword_arguments: tuple[_ServiceCallArgument, ...] = ()
    params_as_argument: bool = False
    parameter_contracts: tuple[SdkMethodParameter, ...] = ()

    def dispatch(self, params: Mapping[str, object]) -> ServicePayload:
        if self.params_as_argument:
            return self.handler(params)
        keywords = {
            argument.name: argument.value_from(params) for argument in self.keyword_arguments
        }
        return self.handler(
            *(argument.value_from(params) for argument in self.arguments),
            **keywords,
        )


@dataclass(frozen=True, slots=True)
class _ServiceStreamRoute:
    method: str
    handler: _ServiceStreamHandler
    arguments: tuple[_ServiceCallArgument, ...] = ()

    def dispatch(self, params: dict[str, object]) -> ServiceStream:
        return self.handler(*(argument.value_from(params) for argument in self.arguments))


@dataclass(frozen=True, slots=True)
class _ServiceConfigParam:
    name: SdkConfigUpdateName
    decoder: _ServiceConfigParamDecoder
    value_type: str
    choices: tuple[str, ...] = ()
    keep_none: bool = False

    def update_from(self, params: Mapping[str, object]) -> SdkConfigUpdate | None:
        if self.name not in params:
            return None
        value = self.decoder(params, self.name)
        if value is None and not self.keep_none:
            return None
        return SdkConfigUpdate(self.name, value)


@dataclass(frozen=True, slots=True)
class _RouteAvailability:
    available: bool
    unavailable_reason: str | None = None

    def to_sdk(self, method: str) -> HephSdkMethodAvailability:
        return HephSdkMethodAvailability(
            method=method,
            available=self.available,
            unavailable_reason=self.unavailable_reason,
        )
