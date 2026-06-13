"""Typed SDK state snapshots for native clients."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from ai.providers.reasoning import DEFAULT_REASONING_LEVEL


class _RuntimeConfigSource(Protocol):
    @property
    def provider_slug(self) -> str: ...

    @property
    def model(self) -> str: ...

    @property
    def base_url(self) -> str: ...

    @property
    def max_tokens(self) -> int: ...

    @property
    def rag_context_budget(self) -> int: ...

    @property
    def temperature(self) -> float | None: ...

    @property
    def thinking_visibility(self) -> str: ...

    @property
    def feature_flags(self) -> frozenset[str]: ...

    @property
    def reasoning_level(self) -> str: ...


class _RuntimeStateSource(Protocol):
    @property
    def armory_path(self) -> Path | None: ...

    @property
    def config(self) -> _RuntimeConfigSource: ...


class _SessionStateSource(Protocol):
    @property
    def session_id(self) -> str: ...

    @property
    def title(self) -> str: ...

    @property
    def armory_path(self) -> Path | None: ...

    @property
    def provider_slug(self) -> str: ...

    @property
    def model(self) -> str: ...

    @property
    def thinking_visibility(self) -> str: ...

    @property
    def live_tokens_visible(self) -> bool: ...

    @property
    def live_cost_visible(self) -> bool: ...

    @property
    def is_streaming(self) -> bool: ...

    @property
    def messages(self) -> tuple[HephMessage, ...]: ...

    @property
    def source_file_count(self) -> int: ...

    @property
    def source_files(self) -> tuple[str, ...]: ...

    @property
    def disabled_source_files(self) -> frozenset[str]: ...

    @property
    def enabled_source_files(self) -> tuple[str, ...]: ...

    @property
    def has_unsaved_changes(self) -> bool: ...

    @property
    def is_disposed(self) -> bool: ...


@dataclass(frozen=True, slots=True)
class HephSdkServiceState:
    prompt_active: bool
    active_operation: str | None = None
    is_busy: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "is_busy",
            self.is_busy or self.prompt_active or self.active_operation is not None,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "prompt_active": self.prompt_active,
            "active_operation": self.active_operation,
            "is_busy": self.is_busy,
        }


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
    reasoning_level: str = DEFAULT_REASONING_LEVEL
    provider_slug: str = ""

    @classmethod
    def from_runtime(cls, runtime: _RuntimeStateSource) -> HephSdkRuntimeState:
        return cls(
            armory_path=runtime.armory_path,
            provider_slug=runtime.config.provider_slug,
            model=runtime.config.model,
            base_url=runtime.config.base_url,
            max_tokens=runtime.config.max_tokens,
            rag_context_budget=runtime.config.rag_context_budget,
            temperature=runtime.config.temperature,
            thinking_visibility=runtime.config.thinking_visibility,
            feature_flags=tuple(sorted(runtime.config.feature_flags)),
            reasoning_level=runtime.config.reasoning_level,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "armory_path": str(self.armory_path) if self.armory_path is not None else None,
            "provider_slug": self.provider_slug,
            "model": self.model,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "rag_context_budget": self.rag_context_budget,
            "temperature": self.temperature,
            "reasoning_level": self.reasoning_level,
            "thinking_visibility": self.thinking_visibility,
            "feature_flags": list(self.feature_flags),
        }


@dataclass(frozen=True, slots=True)
class HephMessage:
    role: str
    content: str

    def to_dict(self) -> dict[str, object]:
        return {"role": self.role, "content": self.content}


@dataclass(frozen=True, slots=True)
class HephSdkSessionState:
    session_id: str
    title: str
    armory_path: Path | None
    model: str
    is_streaming: bool
    messages: tuple[HephMessage, ...]
    provider_slug: str = ""
    thinking_visibility: str = ""
    live_tokens_visible: bool = False
    live_cost_visible: bool = False
    source_file_count: int = 0
    source_files: tuple[str, ...] = ()
    disabled_source_files: frozenset[str] = frozenset()
    enabled_source_files: tuple[str, ...] = ()
    has_unsaved_changes: bool = False
    is_disposed: bool = False

    @classmethod
    def from_session(cls, session: _SessionStateSource) -> HephSdkSessionState:
        return cls(
            session_id=session.session_id,
            title=session.title,
            armory_path=session.armory_path,
            provider_slug=session.provider_slug,
            model=session.model,
            thinking_visibility=session.thinking_visibility,
            live_tokens_visible=session.live_tokens_visible,
            live_cost_visible=session.live_cost_visible,
            is_streaming=session.is_streaming,
            messages=session.messages,
            source_file_count=session.source_file_count,
            source_files=session.source_files,
            disabled_source_files=session.disabled_source_files,
            enabled_source_files=session.enabled_source_files,
            has_unsaved_changes=session.has_unsaved_changes,
            is_disposed=session.is_disposed,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "session_id": self.session_id,
            "title": self.title,
            "armory_path": str(self.armory_path) if self.armory_path is not None else None,
            "provider_slug": self.provider_slug,
            "model": self.model,
            "thinking_visibility": self.thinking_visibility,
            "live_tokens_visible": self.live_tokens_visible,
            "live_cost_visible": self.live_cost_visible,
            "is_streaming": self.is_streaming,
            "is_disposed": self.is_disposed,
            "source_file_count": self.source_file_count,
            "source_files": list(self.source_files),
            "disabled_source_files": sorted(self.disabled_source_files),
            "enabled_source_files": list(self.enabled_source_files),
            "has_unsaved_changes": self.has_unsaved_changes,
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
    "HephMessage",
    "HephSdkRuntimeState",
    "HephSdkServiceState",
    "HephSdkSessionState",
    "HephSdkState",
]
