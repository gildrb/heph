"""Runtime LLM configuration."""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import cast

from heph_ai.providers.keyring_store import resolve_key as _resolve_key
from heph_ai.providers.reasoning import DEFAULT_REASONING_LEVEL, normalize_reasoning_level


def resolve_key(slug: str, env_var: str = "") -> str:
    """Resolve provider keys while honoring the old runtime.engine monkeypatch target."""

    engine_module = sys.modules.get("heph_ai.runtime.engine")
    engine_resolver = getattr(engine_module, "resolve_key", None)
    if callable(engine_resolver) and engine_resolver is not resolve_key:
        resolver = cast("Callable[[str, str], str]", engine_resolver)
        return resolver(slug, env_var)
    return _resolve_key(slug, env_var)


@dataclass
class ChatConfig:
    """Configuration for the LLM engine.

    API keys are resolved lazily at call time from the OS keychain →
    environment variable → volatile in-memory store.  The ``api_key`` field
    is kept for backward compatibility but should not be used to store raw
    keys persistently.  Use the ``resolved_api_key`` property instead.
    """

    api_key: str = ""
    base_url: str = ""
    model: str = ""
    max_tokens: int = 4096
    rag_context_budget: int = 2000
    reasoning_level: str = DEFAULT_REASONING_LEVEL
    temperature: float | None = 0.0
    feature_flags: frozenset[str] = field(default_factory=frozenset)
    _provider_slug: str = field(default="", repr=False)
    _provider_env: str = field(default="", repr=False)

    def is_feature_enabled(self, flag: str) -> bool:
        return flag in self.feature_flags

    def __post_init__(self) -> None:
        self.reasoning_level = normalize_reasoning_level(self.reasoning_level)
        if self.temperature is not None:
            self.temperature = min(2.0, max(0.0, self.temperature))

    @property
    def provider_slug(self) -> str:
        return self._provider_slug

    @property
    def resolved_api_key(self) -> str:
        if self._provider_slug:
            if not self._provider_env:
                return self.api_key
            return resolve_key(self._provider_slug, self._provider_env)
        return self.api_key

    def apply_provider_reference(self, slug: str, env_var: str) -> None:
        self._provider_slug = slug
        self._provider_env = env_var
