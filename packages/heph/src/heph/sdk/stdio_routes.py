"""Explicit JSONL call routes for the SDK stdio transport."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from heph.sdk.service import HephService, ServicePayload
from heph.sdk.stdio_requests import RequestId


class _JsonlCallServer(Protocol):
    service: HephService

    def _abort_active_stream(self) -> ServicePayload: ...

    def _state_with_transport_busy(self) -> ServicePayload: ...

    def _write_call_response(
        self,
        request_id: RequestId,
        method: str,
        result: ServicePayload,
        *,
        translate_state_streams: bool = True,
    ) -> None: ...


type _JsonlCallHandler = Callable[[_JsonlCallServer, RequestId, dict[str, object]], None]


@dataclass(frozen=True, slots=True)
class _JsonlCallRoute:
    handler: _JsonlCallHandler

    def dispatch(
        self,
        server: _JsonlCallServer,
        request_id: RequestId,
        params: dict[str, object],
    ) -> None:
        self.handler(server, request_id, params)


def _write_jsonl_abort_call(
    server: _JsonlCallServer,
    request_id: RequestId,
    params: dict[str, object],
) -> None:
    _ = params
    server._write_call_response(
        request_id,
        "abort",
        server._abort_active_stream(),
        translate_state_streams=False,
    )


def _write_jsonl_state_call(
    server: _JsonlCallServer,
    request_id: RequestId,
    params: dict[str, object],
) -> None:
    _ = params
    server._write_call_response(
        request_id,
        "state",
        server._state_with_transport_busy(),
        translate_state_streams=False,
    )


def _write_jsonl_capabilities_call(
    server: _JsonlCallServer,
    request_id: RequestId,
    params: dict[str, object],
) -> None:
    _ = params
    server._write_call_response(request_id, "capabilities", server.service.capabilities())


def _write_jsonl_settings_call(
    server: _JsonlCallServer,
    request_id: RequestId,
    params: dict[str, object],
) -> None:
    _ = params
    server._write_call_response(request_id, "settings", server.service.settings())


_JSONL_CALL_ROUTES: dict[str, _JsonlCallRoute] = {
    "abort": _JsonlCallRoute(_write_jsonl_abort_call),
    "state": _JsonlCallRoute(_write_jsonl_state_call),
    "capabilities": _JsonlCallRoute(_write_jsonl_capabilities_call),
    "settings": _JsonlCallRoute(_write_jsonl_settings_call),
}
