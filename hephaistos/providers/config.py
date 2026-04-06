"""Provider configuration: multi-provider LLM API management.

Stores provider definitions (endpoint, API key env var, models) in a TOML file
at ``~/.config/hephaistos/providers.toml``.  API keys are resolved at runtime
from the OS keychain → environment variable → volatile in-memory store, and
are **never** written to config files or persisted inside ChatConfig objects.
"""

from __future__ import annotations

import json
import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

_CONFIG_DIR = Path.home() / ".config" / "hephaistos"
_PROVIDERS_FILE = _CONFIG_DIR / "providers.toml"


@dataclass
class Provider:
    slug: str
    display_name: str
    endpoint: str
    api_key_env: str
    models: list[str] = field(default_factory=list)
    active: bool = False
    current_model: str = ""

    @property
    def is_authenticated(self) -> bool:
        """Check if a key is available via any resolution path."""
        from hephaistos.providers.keyring_store import resolve_key
        return bool(resolve_key(self.slug, self.api_key_env))

    @property
    def api_key(self) -> str:
        """Resolve the API key from keychain → env var → volatile store."""
        from hephaistos.providers.keyring_store import resolve_key
        return resolve_key(self.slug, self.api_key_env)

    @property
    def resolved_model(self) -> str:
        if self.current_model:
            return self.current_model
        if self.models:
            return self.models[0]
        return ""


@dataclass
class ProviderConfig:
    providers: dict[str, Provider] = field(default_factory=dict)

    def get_active(self) -> Provider | None:
        for p in self.providers.values():
            if p.active:
                return p
        return None

    def set_active(self, slug: str) -> bool:
        if slug not in self.providers:
            return False
        for p in self.providers.values():
            p.active = False
        self.providers[slug].active = True
        return True

    def set_model(self, slug: str, model: str) -> bool:
        if slug not in self.providers:
            return False
        p = self.providers[slug]
        if model not in p.models:
            return False
        p.current_model = model
        return True

    def apply_to_config(self, config: object) -> None:
        """Apply the active provider settings to a ChatConfig instance.

        Sets base_url and model directly, but stores only a *reference*
        (provider slug) for the API key so the raw key is not held in
        the config object.  The engine resolves the key lazily at call time.
        """
        active = self.get_active()
        if active is None:
            return
        config.base_url = active.endpoint
        config.model = active.resolved_model
        # Store provider reference for lazy key resolution instead of
        # copying the raw key into the config object.
        config._provider_slug = active.slug
        config._provider_env = active.api_key_env

    def save(self, path: Path | None = None) -> None:
        path = path or _PROVIDERS_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        lines: list[str] = []
        for slug, p in self.providers.items():
            lines.append(f"[{slug}]")
            lines.append(f"display_name = {json.dumps(p.display_name)}")
            lines.append(f"endpoint = {json.dumps(p.endpoint)}")
            lines.append(f"api_key_env = {json.dumps(p.api_key_env)}")
            if p.active:
                lines.append("active = true")
            if p.current_model:
                lines.append(f"current_model = {json.dumps(p.current_model)}")
            if p.models:
                models_str = ", ".join(json.dumps(m) for m in p.models)
                lines.append(f"models = [{models_str}]")
            lines.append("")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: Path | None = None) -> ProviderConfig:
        path = path or _PROVIDERS_FILE
        if not path.is_file():
            cfg = _default_config()
            cfg.save(path)
            return cfg

        with open(path, "rb") as f:
            data = tomllib.load(f)

        providers: dict[str, Provider] = {}
        for slug, section in data.items():
            if not isinstance(section, dict):
                continue
            providers[slug] = Provider(
                slug=slug,
                display_name=section.get("display_name", slug),
                endpoint=section.get("endpoint", ""),
                api_key_env=section.get("api_key_env", ""),
                models=section.get("models", []),
                active=section.get("active", False),
                current_model=section.get("current_model", ""),
            )
        return cls(providers=providers)


def providers_dir() -> Path:
    return _CONFIG_DIR


def _default_config() -> ProviderConfig:
    return ProviderConfig(
        providers={
            "openrouter": Provider(
                slug="openrouter",
                display_name="OpenRouter",
                endpoint="https://openrouter.ai/api/v1",
                api_key_env="OPENROUTER_API_KEY",
                models=[
                    "anthropic/claude-opus-4.6",
                    "anthropic/claude-sonnet-4.6",
                    "anthropic/claude-sonnet-4.5",
                    "anthropic/claude-haiku-4.5",
                    "qwen/qwen3.6-plus:free",
                    "openai/gpt-5.4",
                    "openai/gpt-5.4-mini",
                    "openai/gpt-5.4-pro",
                    "openai/gpt-5.4-nano",
                    "openai/gpt-5.3-codex",
                    "google/gemini-3-pro-preview",
                    "google/gemini-3-flash-preview",
                    "google/gemini-3.1-pro-preview",
                    "google/gemini-3.1-flash-lite-preview",
                    "qwen/qwen3.5-plus-02-15",
                    "qwen/qwen3.5-35b-a3b",
                    "stepfun/step-3.5-flash",
                    "minimax/minimax-m2.7",
                    "minimax/minimax-m2.5",
                    "z-ai/glm-5",
                    "z-ai/glm-5-turbo",
                    "moonshotai/kimi-k2.5",
                    "xiaomi/mimo-v2-pro",
                    "x-ai/grok-4.20-beta",
                    "nvidia/nemotron-3-super-120b-a12b",
                    "nvidia/nemotron-3-super-120b-a12b:free",
                    "arcee-ai/trinity-large-preview:free",
                ],
            ),
            "openai-codex": Provider(
                slug="openai-codex",
                display_name="OpenAI Codex",
                endpoint="https://api.openai.com/v1",
                api_key_env="OPENAI_API_KEY",
                models=[
                    "gpt-5.4",
                    "gpt-5.4-mini",
                    "gpt-5.3-codex",
                    "gpt-5.2-codex",
                    "gpt-5.2",
                    "gpt-5.1-codex-max",
                    "gpt-5.1-codex-mini",
                    "gpt-5.3-codex-spark",
                ],
            ),
            "zai": Provider(
                slug="zai",
                display_name="Z.AI / GLM",
                endpoint="https://api.z.ai/api/paas/v4/",
                api_key_env="ZAI_API_KEY",
                active=True,
                current_model="glm-5-turbo",
                models=[
                    "glm-5",
                    "glm-5-turbo",
                    "glm-4.7",
                    "glm-4.5",
                    "glm-4.5-flash",
                ],
            ),
            "custom": Provider(
                slug="custom",
                display_name="Custom",
                endpoint="https://api.z.ai/api/coding/paas/v4",
                api_key_env="CUSTOM_API_KEY",
                models=[],
            ),
        }
    )
