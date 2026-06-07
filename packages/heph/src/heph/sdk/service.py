"""Stateful service facade for transport adapters."""

from __future__ import annotations

import threading
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

from ai.runtime import ChatConfig

from heph.sdk.events import event_to_dict
from heph.sdk.runtime import HephRuntime, HephSdkError, HephSession

type ServicePayload = dict[str, object]
type ServiceStream = Iterator[ServicePayload]


@dataclass(slots=True)
class HephService:
    """JSON-ready state facade for native clients and future RPC adapters."""

    runtime: HephRuntime
    session: HephSession | None = None

    @classmethod
    def plain(cls, *, config: ChatConfig | None = None) -> HephService:
        return cls(runtime=HephRuntime.plain(config=config))

    @classmethod
    def open_armory(
        cls,
        path: str | Path,
        *,
        config: ChatConfig | None = None,
    ) -> HephService:
        return cls(runtime=HephRuntime.open_armory(path, config=config))

    @classmethod
    def create_armory(
        cls,
        path: str | Path,
        *,
        config: ChatConfig | None = None,
    ) -> HephService:
        return cls(runtime=HephRuntime.create_armory(path, config=config))

    def state(self) -> dict[str, object]:
        return {
            "runtime": self._runtime_state(),
            "session": self.session.to_dict() if self.session is not None else None,
        }

    def call(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
    ) -> ServicePayload:
        parameters = params or {}
        if method == "state":
            return self.state()
        if method == "use_plain_runtime":
            return self.use_plain_runtime()
        if method == "open_armory":
            return self.open_runtime_armory(_required_str(parameters, "path"))
        if method == "create_armory":
            return self.create_runtime_armory(_required_str(parameters, "path"))
        if method == "list_armories":
            return self.list_armories()
        if method == "new_session":
            return self.new_session()
        if method == "resume_session":
            return self.resume_session(_required_str(parameters, "session_id"))
        if method == "fork_session":
            return self.fork_session(_required_str(parameters, "turn_id"))
        if method == "list_sessions":
            return self.list_sessions()
        if method == "save_session":
            return self.save_session()
        if method == "messages":
            return self.messages()
        if method == "ask":
            return self.ask(_required_str(parameters, "text"))
        if method == "abort":
            return self.abort()
        if method == "list_materials":
            return self.list_materials()
        if method == "import_materials":
            return self.import_materials(_required_str(parameters, "source"))
        if method == "build_index":
            return self.build_index()
        if method == "scan_extraction_health":
            return self.scan_extraction_health()
        if method == "update_config":
            return self.update_config(parameters)
        raise HephSdkError(f"Unknown SDK service method: {method}")

    def stream(
        self,
        method: str,
        params: Mapping[str, object] | None = None,
    ) -> ServiceStream:
        parameters = params or {}
        if method != "prompt":
            raise HephSdkError(f"Unknown SDK service stream method: {method}")
        yield from self.prompt(_required_str(parameters, "text"))

    def use_plain_runtime(self) -> dict[str, object]:
        self._replace_runtime(HephRuntime.plain(config=self.runtime.config))
        return self.state()

    def open_runtime_armory(self, path: str | Path) -> dict[str, object]:
        self._replace_runtime(HephRuntime.open_armory(path, config=self.runtime.config))
        return self.state()

    def create_runtime_armory(self, path: str | Path) -> dict[str, object]:
        self._replace_runtime(HephRuntime.create_armory(path, config=self.runtime.config))
        return self.state()

    def list_armories(self) -> dict[str, object]:
        return {"armories": [armory.to_dict() for armory in HephRuntime.list_armories()]}

    def new_session(self) -> dict[str, object]:
        self._replace_session(self.runtime.new_session())
        return self._session_payload()

    def resume_session(self, session_id: str) -> dict[str, object]:
        self._replace_session(self.runtime.resume_session(session_id))
        return self._session_payload()

    def fork_session(self, turn_id: str) -> dict[str, object]:
        self._replace_session(self.runtime.fork_session(self._require_session(), turn_id))
        return self._session_payload()

    def list_sessions(self) -> dict[str, object]:
        return {"sessions": [session.to_dict() for session in self.runtime.list_sessions()]}

    def save_session(self) -> dict[str, object]:
        saved_path = self._require_session().save()
        return {"path": str(saved_path), "session": self._require_session().to_dict()}

    def messages(self) -> dict[str, object]:
        return {"messages": [message.to_dict() for message in self._require_session().messages]}

    def prompt(
        self,
        text: str,
        *,
        abort: threading.Event | None = None,
    ) -> Iterator[dict[str, object]]:
        for event in self._require_session().prompt(text, abort=abort):
            yield event_to_dict(event)

    def ask(self, text: str) -> dict[str, object]:
        return {"text": self._require_session().ask(text), "session": self._session_dict()}

    def abort(self) -> dict[str, object]:
        self._require_session().abort()
        return {"aborted": True, "session": self._session_dict()}

    def update_config(self, params: Mapping[str, object]) -> dict[str, object]:
        if value := _optional_str(params, "base_url"):
            self.runtime.config.base_url = value
        if value := _optional_str(params, "model"):
            self.runtime.config.model = value
        if "max_tokens" in params:
            max_tokens = _optional_int(params, "max_tokens")
            if max_tokens is not None:
                self.runtime.config.max_tokens = max_tokens
        if "rag_context_budget" in params:
            rag_context_budget = _optional_int(params, "rag_context_budget")
            if rag_context_budget is not None:
                self.runtime.config.rag_context_budget = rag_context_budget
        if "temperature" in params:
            self.runtime.config.temperature = _optional_float(params, "temperature")
        return {"runtime": self._runtime_state()}

    def list_materials(self) -> dict[str, object]:
        return {"materials": [material.to_dict() for material in self.runtime.list_materials()]}

    def import_materials(self, source: str | Path) -> dict[str, object]:
        summary = self.runtime.import_materials(source)
        if self.session is not None and summary.imported:
            self.session.refresh_materials()
        return {"import": summary.to_dict()}

    def build_index(self) -> dict[str, object]:
        return {"index": self.runtime.build_index().to_dict()}

    def scan_extraction_health(self) -> dict[str, object]:
        return {"health": self.runtime.scan_extraction_health().to_dict()}

    def _runtime_state(self) -> dict[str, object]:
        return {
            "armory_path": (
                str(self.runtime.armory_path) if self.runtime.armory_path is not None else None
            ),
            "model": self.runtime.config.model,
            "base_url": self.runtime.config.base_url,
            "max_tokens": self.runtime.config.max_tokens,
            "rag_context_budget": self.runtime.config.rag_context_budget,
            "temperature": self.runtime.config.temperature,
            "feature_flags": sorted(self.runtime.config.feature_flags),
        }

    def _session_payload(self) -> dict[str, object]:
        return {"session": self._session_dict(), "runtime": self._runtime_state()}

    def _session_dict(self) -> dict[str, object]:
        return self._require_session().to_dict()

    def _require_session(self) -> HephSession:
        if self.session is None:
            raise HephSdkError("No active SDK session.")
        return self.session

    def _replace_runtime(self, runtime: HephRuntime) -> None:
        old_session = self.session
        self.runtime = runtime
        self.session = None
        if old_session is not None:
            old_session.dispose()

    def _replace_session(self, session: HephSession) -> None:
        old_session = self.session
        self.session = session
        if old_session is not None and old_session is not session:
            old_session.dispose()


def _required_str(params: Mapping[str, object], key: str) -> str:
    value = params.get(key)
    if not isinstance(value, str) or not value.strip():
        raise HephSdkError(f"SDK service parameter '{key}' must be a non-empty string.")
    return value


def _optional_str(params: Mapping[str, object], key: str) -> str | None:
    value = params.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise HephSdkError(f"SDK service parameter '{key}' must be a string.")
    return value


def _optional_int(params: Mapping[str, object], key: str) -> int | None:
    value = params.get(key)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise HephSdkError(f"SDK service parameter '{key}' must be an integer.")
    return value


def _optional_float(params: Mapping[str, object], key: str) -> float | None:
    value = params.get(key)
    if value is None:
        return None
    if isinstance(value, int | float) and not isinstance(value, bool):
        return min(2.0, max(0.0, float(value)))
    raise HephSdkError(f"SDK service parameter '{key}' must be a number or null.")


__all__ = [
    "HephService",
    "ServicePayload",
    "ServiceStream",
]
