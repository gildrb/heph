"""Typed SDK state snapshots for native clients."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ai.providers.reasoning import DEFAULT_REASONING_LEVEL

from heph.sdk.runtime import HephRuntime, HephSdkSessionState


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
    reasoning_level: str = DEFAULT_REASONING_LEVEL

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
            reasoning_level=runtime.config.reasoning_level,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "armory_path": str(self.armory_path) if self.armory_path is not None else None,
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
