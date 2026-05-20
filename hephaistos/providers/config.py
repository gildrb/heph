"""Provider configuration for swappable LLM API backends."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.providers.keyring_store import resolve_key
from hephaistos.providers.model_support import filter_supported_models
from hephaistos.providers.registry import builtin_models

if TYPE_CHECKING:
    from hephaistos.runtime import ChatConfig

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
    if _provider_cache_ref.config is None or _provider_cache_ref.path != path:
        return None
    if _provider_cache_ref.stamp != _provider_file_stamp(path):
        return None
    return _provider_cache_ref.config


def _merge_default_providers(config: ProviderConfig) -> ProviderConfig:
    defaults = default_config()
    changed = False
    for slug, provider in defaults.providers.items():
        if slug not in config.providers:
            provider.active = False
            config.providers[slug] = provider
            changed = True
            continue
        if slug == "custom":
            continue
        changed = _refresh_builtin_provider(config.providers[slug], provider) or changed

    if config.get_active() is None:
        config.providers["pollinations"].active = True
        changed = True

    if changed:
        return ProviderConfig(providers=config.providers)
    return config


def invalidate_provider_cache(
    replacement: ProviderConfig | None = None, *, path: Path | None = None
) -> None:
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
            raw_models = section.get("models", [])
            models = (
                filter_supported_models([str(model) for model in raw_models], slug)
                if is_object_list(raw_models)
                else []
            )
            raw_current_model = section.get("current_model", "")
            current_model = str(raw_current_model) if raw_current_model else ""
            if "models" in section and current_model and current_model not in models:
                current_model = ""
            providers[slug] = Provider(
                slug=slug,
                display_name=str(section.get("display_name", slug)),
                endpoint=str(section.get("endpoint", "")),
                api_key_env=str(section.get("api_key_env", "")),
                models=models,
                active=bool(section.get("active", False)),
                current_model=current_model,
            )
        cfg = _merge_default_providers(cls(providers=providers))
        invalidate_provider_cache(cfg, path=path)
        return cfg


def providers_dir() -> Path:
    return _CONFIG_DIR


def _refresh_builtin_provider(provider: Provider, default: Provider) -> bool:
    changed = False
    for attr in ("display_name", "endpoint", "api_key_env"):
        if getattr(provider, attr) != getattr(default, attr):
            setattr(provider, attr, getattr(default, attr))
            changed = True

    if provider.slug in {"openai", "openai-codex"}:
        missing_models = [model for model in default.models if model not in provider.models]
        if missing_models:
            provider.models = [*missing_models, *provider.models]
            changed = True

    if provider.current_model and provider.current_model not in provider.models:
        provider.current_model = ""
        changed = True

    return changed


def _default_provider_models(provider: str) -> list[str]:
    return [model.name for model in builtin_models() if model.provider == provider]


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
                    "openai-fast",
                ],
            ),
            "openrouter": Provider(
                slug="openrouter",
                display_name="OpenRouter",
                endpoint="https://openrouter.ai/api/v1",
                api_key_env="OPENROUTER_API_KEY",
                models=_default_provider_models("openrouter"),
            ),
            "openai": Provider(
                slug="openai",
                display_name="OpenAI API",
                endpoint="https://api.openai.com/v1",
                api_key_env="OPENAI_API_KEY",
                models=_default_provider_models("openai"),
            ),
            "openai-codex": Provider(
                slug="openai-codex",
                display_name="OpenAI Codex",
                endpoint="https://api.openai.com/v1",
                api_key_env="",
                models=_default_provider_models("openai-codex"),
            ),
            "zai": Provider(
                slug="zai",
                display_name="Z.AI / GLM",
                endpoint="https://api.z.ai/api/paas/v4/",
                api_key_env="ZAI_API_KEY",
                models=_default_provider_models("zai"),
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
