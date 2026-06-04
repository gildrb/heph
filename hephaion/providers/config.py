"""Provider configuration for swappable LLM API backends."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from hephaion._types import is_object_list, is_string_mapping
from hephaion.providers.keyring_store import resolve_key
from hephaion.providers.model_support import filter_supported_models
from hephaion.providers.registry import builtin_models

if TYPE_CHECKING:
    from hephaion.runtime import ChatConfig

_CONFIG_DIR = Path.home() / ".config" / "hephaion"
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
    changed = _merge_provider_defaults(config, defaults)
    changed = _activate_fallback_provider(config) or changed

    if changed:
        return ProviderConfig(providers=config.providers)
    return config


def _merge_provider_defaults(config: ProviderConfig, defaults: ProviderConfig) -> bool:
    changed = False
    for slug, default_provider in defaults.providers.items():
        changed = _merge_provider_default(config, slug, default_provider) or changed
    return changed


def _merge_provider_default(
    config: ProviderConfig,
    slug: str,
    default_provider: Provider,
) -> bool:
    if slug not in config.providers:
        default_provider.active = False
        config.providers[slug] = default_provider
        return True
    if slug == "custom":
        return False
    return _refresh_builtin_provider(config.providers[slug], default_provider)


def _activate_fallback_provider(config: ProviderConfig) -> bool:
    if config.get_active() is not None:
        return False
    config.providers["pollinations"].active = True
    return True


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
        sections = [
            _provider_section_lines(slug, provider) for slug, provider in self.providers.items()
        ]
        content = "\n".join(line for section in sections for line in (*section, ""))
        path.write_text(content + "\n", encoding="utf-8")
        invalidate_provider_cache(self, path=path)

    @classmethod
    def load(cls, path: Path | None = None) -> ProviderConfig:
        path = path or _PROVIDERS_FILE
        cached = _provider_cache(path)
        if cached is not None:
            return cached
        if not path.is_file():
            return _cached_default_config(path)

        cfg = _merge_default_providers(cls(providers=_load_provider_sections(path)))
        invalidate_provider_cache(cfg, path=path)
        return cfg


def providers_dir() -> Path:
    return _CONFIG_DIR


def _cached_default_config(path: Path) -> ProviderConfig:
    config = default_config()
    invalidate_provider_cache(config, path=path)
    return config


def _load_provider_sections(path: Path) -> dict[str, Provider]:
    with path.open("rb") as f:
        data = tomllib.load(f)

    return {
        slug: provider
        for slug, section in data.items()
        if is_string_mapping(section)
        if (provider := _provider_from_section(slug, section)) is not None
    }


def _provider_from_section(slug: str, section: dict[str, object]) -> Provider:
    models = _section_models(slug, section)
    return Provider(
        slug=slug,
        display_name=str(section.get("display_name", slug)),
        endpoint=str(section.get("endpoint", "")),
        api_key_env=str(section.get("api_key_env", "")),
        models=models,
        active=bool(section.get("active", False)),
        current_model=_section_current_model(section, models),
    )


def _provider_section_lines(slug: str, provider: Provider) -> tuple[str, ...]:
    lines = [
        f"[{slug}]",
        f"display_name = {json.dumps(provider.display_name)}",
        f"endpoint = {json.dumps(provider.endpoint)}",
        f"api_key_env = {json.dumps(provider.api_key_env)}",
    ]
    if provider.active:
        lines.append("active = true")
    if provider.current_model:
        lines.append(f"current_model = {json.dumps(provider.current_model)}")
    if provider.models:
        models = ", ".join(json.dumps(model) for model in provider.models)
        lines.append(f"models = [{models}]")
    return tuple(lines)


def _section_models(slug: str, section: dict[str, object]) -> list[str]:
    raw_models = section.get("models", [])
    if not is_object_list(raw_models):
        return []
    return filter_supported_models([str(model) for model in raw_models], slug)


def _section_current_model(section: dict[str, object], models: list[str]) -> str:
    raw_current_model = section.get("current_model", "")
    current_model = str(raw_current_model) if raw_current_model else ""
    if "models" in section and current_model and current_model not in models:
        return ""
    return current_model


def _refresh_builtin_provider(provider: Provider, default: Provider) -> bool:
    return any(
        (
            _refresh_builtin_provider_fields(provider, default),
            _prepend_missing_builtin_models(provider, default),
            _clear_invalid_current_model(provider),
        )
    )


def _refresh_builtin_provider_fields(provider: Provider, default: Provider) -> bool:
    changed = False
    for attr in ("display_name", "endpoint", "api_key_env"):
        if getattr(provider, attr) == getattr(default, attr):
            continue
        setattr(provider, attr, getattr(default, attr))
        changed = True
    return changed


def _prepend_missing_builtin_models(provider: Provider, default: Provider) -> bool:
    if provider.slug not in {"openai", "openai-codex", "deepseek"}:
        return False
    missing_models = [model for model in default.models if model not in provider.models]
    if not missing_models:
        return False
    provider.models = [*missing_models, *provider.models]
    return True


def _clear_invalid_current_model(provider: Provider) -> bool:
    if not provider.current_model or provider.current_model in provider.models:
        return False
    provider.current_model = ""
    return True


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
            "deepseek": Provider(
                slug="deepseek",
                display_name="DeepSeek API",
                endpoint="https://api.deepseek.com",
                api_key_env="DEEPSEEK_API_KEY",
                models=_default_provider_models("deepseek"),
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
