"""Provider configuration: multi-provider LLM API management.

Stores provider definitions (endpoint, API key env var, models) in a TOML file
at ``~/.config/hephaistos/providers.toml``.  API keys are resolved at runtime
from the OS keychain → environment variable → volatile in-memory store, and
are **never** written to config files or persisted inside ChatConfig objects.
"""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.providers.keyring_store import resolve_key
from hephaistos.providers.model_support import filter_supported_models

if TYPE_CHECKING:
    from hephaistos.chat.engine import ChatConfig

_CONFIG_DIR = Path.home() / ".config" / "hephaistos"
_PROVIDERS_FILE = _CONFIG_DIR / "providers.toml"


@dataclass
class _ProviderConfigCache:
    path: Path | None = None
    stamp: tuple[bool, int | None, int | None] | None = None
    config: ProviderConfig | None = None


_provider_cache_ref = _ProviderConfigCache()


def _provider_file_stamp(path: Path) -> tuple[bool, int | None, int | None]:
    try:
        stat = path.stat()
    except OSError:
        return (False, None, None)
    return (True, stat.st_mtime_ns, stat.st_size)


def _provider_cache(path: Path) -> ProviderConfig | None:
    """Return the cached ProviderConfig for a path, if the file is unchanged."""
    if _provider_cache_ref.config is None or _provider_cache_ref.path != path:
        return None
    if _provider_cache_ref.stamp != _provider_file_stamp(path):
        return None
    return _provider_cache_ref.config


def invalidate_provider_cache(
    replacement: ProviderConfig | None = None, *, path: Path | None = None
) -> None:
    """Update or clear the in-process provider config cache."""
    if replacement is None:
        _provider_cache_ref.path = None
        _provider_cache_ref.stamp = None
        _provider_cache_ref.config = None
        return
    cache_path = path or _PROVIDERS_FILE
    _provider_cache_ref.path = cache_path
    _provider_cache_ref.stamp = _provider_file_stamp(cache_path)
    _provider_cache_ref.config = replacement


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
    def api_key(self) -> str:
        """Resolve the API key from keychain → env var → volatile store."""
        return resolve_key(self.slug, self.api_key_env)

    @property
    def resolved_model(self) -> str:
        if self.current_model:
            return self.current_model
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

    def apply_to_config(self, config: ChatConfig) -> None:
        """Apply the active provider settings to a ChatConfig instance.

        Sets base_url and model directly, but stores only a *reference*
        (provider slug) for the API key so the raw key is not held in
        the config object.  The engine resolves the key lazily at call time.

        Does nothing if no provider is active.
        """
        active = self.get_active()
        if active is None:
            return
        config.base_url = active.endpoint
        config.model = active.resolved_model
        config.apply_provider_reference(active.slug, active.api_key_env)

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
        invalidate_provider_cache(self, path=path)

    @classmethod
    def load(cls, path: Path | None = None) -> ProviderConfig:
        path = path or _PROVIDERS_FILE
        cached = _provider_cache(path)
        if cached is not None:
            return cached
        if not path.is_file():
            cfg = default_config()
            invalidate_provider_cache(cfg, path=path)
            return cfg

        with path.open("rb") as f:
            data = tomllib.load(f)

        providers: dict[str, Provider] = {}
        for slug, section in data.items():
            if not is_string_mapping(section):
                continue
            providers[slug] = _sanitize_provider(slug, section)
        cfg = cls(providers=providers)
        invalidate_provider_cache(cfg, path=path)
        return cfg


def providers_dir() -> Path:
    return _CONFIG_DIR


def default_config() -> ProviderConfig:
    return ProviderConfig(
        providers={
            "pollinations": Provider(
                slug="pollinations",
                display_name="Pollinations AI (free)",
                endpoint="https://text.pollinations.ai/openai",
                api_key_env="",
                active=True,
                current_model="openai",
                models=[
                    "openai",
                    "openai-large",
                    "openai-reasoning",
                    "openai-fast",
                    "mistral",
                    "mistral-large",
                    "mistral-reasoning",
                    "qwen-coder",
                    "deepseek-reasoning",
                    "deepseek",
                    "llama",
                    "llama-scaleway",
                    "gemini",
                    "gemini-thinking",
                ],
            ),
            "openrouter": Provider(
                slug="openrouter",
                display_name="OpenRouter",
                endpoint="https://openrouter.ai/api/v1",
                api_key_env="OPENROUTER_API_KEY",
                models=[
                    "openrouter/free",
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


def _sanitize_provider(
    slug: str,
    section: dict[str, object],
) -> Provider:
    has_models_catalog = "models" in section
    raw_models = section.get("models", [])
    models = (
        filter_supported_models([str(model) for model in raw_models], slug)
        if is_object_list(raw_models)
        else []
    )
    raw_current_model = section.get("current_model", "")
    current_model = str(raw_current_model) if raw_current_model else ""
    if has_models_catalog and current_model and current_model not in models:
        current_model = ""
    raw_active = section.get("active", False)
    return Provider(
        slug=slug,
        display_name=str(section.get("display_name", slug)),
        endpoint=str(section.get("endpoint", "")),
        api_key_env=str(section.get("api_key_env", "")),
        models=models,
        active=bool(raw_active),
        current_model=current_model,
    )
