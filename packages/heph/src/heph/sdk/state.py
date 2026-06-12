"""Typed SDK state snapshots for native clients."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from heph.sdk.runtime import HephMessage, HephRuntime, HephSession


@dataclass(frozen=True, slots=True)
class HephSdkServiceState:
    prompt_active: bool

    def to_dict(self) -> dict[str, object]:
        return {"prompt_active": self.prompt_active}


@dataclass(frozen=True, slots=True)
class HephSdkRuntimeState:
    armory_path: Path | None
    model: str
    base_url: str
    max_tokens: int
    rag_context_budget: int
    temperature: float | None
    thinking_visibility: str
    feature_flags: tuple[str, ...]

    @classmethod
    def from_runtime(cls, runtime: HephRuntime) -> HephSdkRuntimeState:
        return cls(
            armory_path=runtime.armory_path,
            model=runtime.config.model,
            base_url=runtime.config.base_url,
            max_tokens=runtime.config.max_tokens,
            rag_context_budget=runtime.config.rag_context_budget,
            temperature=runtime.config.temperature,
            thinking_visibility=runtime.config.thinking_visibility,
            feature_flags=tuple(sorted(runtime.config.feature_flags)),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "armory_path": str(self.armory_path) if self.armory_path is not None else None,
            "model": self.model,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "rag_context_budget": self.rag_context_budget,
            "temperature": self.temperature,
            "thinking_visibility": self.thinking_visibility,
            "feature_flags": list(self.feature_flags),
        }


@dataclass(frozen=True, slots=True)
class HephSdkSessionState:
    session_id: str
    title: str
    armory_path: Path | None
    model: str
    is_streaming: bool
    messages: tuple[HephMessage, ...]

    @classmethod
    def from_session(cls, session: HephSession) -> HephSdkSessionState:
        return cls(
            session_id=session.session_id,
            title=session.title,
            armory_path=session.armory_path,
            model=session.model,
            is_streaming=session.is_streaming,
            messages=session.messages,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "title": self.title,
            "armory_path": str(self.armory_path) if self.armory_path is not None else None,
            "model": self.model,
            "is_streaming": self.is_streaming,
            "messages": [message.to_dict() for message in self.messages],
        }


@dataclass(frozen=True, slots=True)
class HephSdkState:
    service: HephSdkServiceState
    runtime: HephSdkRuntimeState
    session: HephSdkSessionState | None

    def to_dict(self) -> dict[str, object]:
        return {
            "service": self.service.to_dict(),
            "runtime": self.runtime.to_dict(),
            "session": self.session.to_dict() if self.session is not None else None,
        }


__all__ = [
    "HephSdkRuntimeState",
    "HephSdkServiceState",
    "HephSdkSessionState",
    "HephSdkState",
]
