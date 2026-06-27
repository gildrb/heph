"""Live provider model catalogs with static fallbacks.

This mirrors the Hermes-style provider split: runtime calls stay provider
specific, while model menus can prefer live catalogs when a provider exposes
one.  Failures are intentionally quiet so offline startup keeps using the
built-in provider config.
"""

from __future__ import annotations

import json
import os
import ssl
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlparse

import certifi

from ai.logging import get_logger
from ai.providers.config import Provider, ProviderConfig
from ai.providers.llama_cpp import (
    LLAMA_CPP_PROVIDER_SLUG,
    installed_tool_capable_records,
    model_info_for_record,
)
from ai.providers.model_support import is_supported_model_for_provider
from ai.providers.registry import ModelInfo, get_registry
from ai.types import is_object_list, is_string_mapping

_log = get_logger("ai.providers.catalog")

_CATALOG_TIMEOUT_SECONDS = 2.0
_CATALOG_CACHE_SECONDS = 10 * 60
_DISABLE_LIVE_CATALOG_ENV = "HARNESS_DISABLE_LIVE_MODELS"
_MODELS_DEV_URL = "https://models.dev/api.json"
_OPENAI_REASONING_EFFORTS = ("low", "medium", "high", "xhigh")
_DEEPSEEK_REASONING_EFFORTS = ("high", "xhigh")
_DEFAULT_REASONING_EFFORTS = ("low", "medium", "high")


@dataclass
class LiveProviderCatalog:
    models: list[str]
    metadata: list[ModelInfo]


@dataclass
class _CatalogCacheEntry:
    fetched_at: float
    catalog: LiveProviderCatalog


_catalog_cache: dict[str, _CatalogCacheEntry] = {}
_catalog_refreshing: set[str] = set()
_catalog_lock = threading.Lock()
_models_dev_fetched_at = 0.0
_models_dev_refreshing = False


def hydrate_provider_models(
    config: ProviderConfig,
    *,
    allow_network: bool = False,
    provider_slugs: set[str] | None = None,
) -> None:
    if _provider_selected(LLAMA_CPP_PROVIDER_SLUG, provider_slugs):
        _hydrate_llama_cpp_models(config)

    if _live_catalog_disabled():
        return

    _hydrate_models_dev_metadata(allow_network=allow_network)
    _hydrate_live_provider_models(
        config,
        allow_network=allow_network,
        provider_slugs=provider_slugs,
    )


def _provider_selected(slug: str, provider_slugs: set[str] | None) -> bool:
    return provider_slugs is None or slug in provider_slugs


def _live_catalog_disabled() -> bool:
    return bool(os.environ.get(_DISABLE_LIVE_CATALOG_ENV, "").strip())


def _hydrate_live_provider_models(
    config: ProviderConfig,
    *,
    allow_network: bool,
    provider_slugs: set[str] | None,
) -> None:
    for slug, provider in config.providers.items():
        if not _provider_selected(slug, provider_slugs):
            continue
        if slug == LLAMA_CPP_PROVIDER_SLUG:
            continue
        catalog = _live_catalog_for_provider(
            slug,
            provider.endpoint,
            allow_network=allow_network,
        )
        if catalog is None or not catalog.models:
            continue
        _apply_live_provider_catalog(provider, catalog)


def _apply_live_provider_catalog(provider: Provider, catalog: LiveProviderCatalog) -> None:
    provider.models = catalog.models
    if provider.current_model and provider.current_model not in provider.models:
        provider.current_model = ""
    _register_model_infos(catalog.metadata)


def _register_model_infos(metadata: list[ModelInfo]) -> None:
    registry = get_registry()
    for info in metadata:
        registry.register(info)


def _hydrate_llama_cpp_models(config: ProviderConfig) -> None:
    provider = config.providers.get(LLAMA_CPP_PROVIDER_SLUG)
    if provider is None:
        return
    records = installed_tool_capable_records()
    provider.models = [record.model_id for record in records]
    if records:
        provider.endpoint = records[0].endpoint
    if provider.current_model and provider.current_model not in provider.models:
        provider.current_model = ""
    registry = get_registry()
    for record in records:
        registry.register(model_info_for_record(record))


def prefetch_provider_model_catalogs(
    config: ProviderConfig,
    *,
    provider_slugs: set[str] | None = None,
) -> None:
    if _live_catalog_disabled():
        return

    _schedule_models_dev_refresh()

    for slug, provider in config.providers.items():
        if not _provider_selected(slug, provider_slugs):
            continue
        _schedule_live_catalog_refresh(slug, provider.endpoint)


def invalidate_catalog_cache() -> None:
    global _models_dev_fetched_at, _models_dev_refreshing  # noqa: PLW0603
    with _catalog_lock:
        _catalog_cache.clear()
        _catalog_refreshing.clear()
        _models_dev_fetched_at = 0.0
        _models_dev_refreshing = False


def _live_catalog_for_provider(
    slug: str,
    endpoint: str,
    *,
    allow_network: bool = False,
) -> LiveProviderCatalog | None:
    if slug != "openrouter":
        return None

    cached = _cached_live_catalog(slug)
    if cached is not None:
        return cached

    if not allow_network:
        _schedule_live_catalog_refresh(slug, endpoint)
        return None

    return _fetch_and_cache_live_catalog(slug, endpoint)


def _cached_live_catalog(slug: str) -> LiveProviderCatalog | None:
    now = time.time()
    with _catalog_lock:
        cached = _catalog_cache.get(slug)
        if cached is None or now - cached.fetched_at >= _CATALOG_CACHE_SECONDS:
            return None
        return cached.catalog


def _schedule_live_catalog_refresh(slug: str, endpoint: str) -> None:
    if slug != "openrouter" or _cached_live_catalog(slug) is not None:
        return
    with _catalog_lock:
        if slug in _catalog_refreshing:
            return
        _catalog_refreshing.add(slug)
    thread = threading.Thread(
        target=_refresh_live_catalog,
        args=(slug, endpoint),
        name=f"harness-{slug}-catalog",
        daemon=True,
    )
    thread.start()


def _refresh_live_catalog(slug: str, endpoint: str) -> None:
    try:
        _fetch_and_cache_live_catalog(slug, endpoint)
    finally:
        with _catalog_lock:
            _catalog_refreshing.discard(slug)


def _schedule_models_dev_refresh() -> None:
    global _models_dev_refreshing  # noqa: PLW0603
    if _models_dev_cache_fresh():
        return
    with _catalog_lock:
        if _models_dev_refreshing:
            return
        _models_dev_refreshing = True
    thread = threading.Thread(
        target=_refresh_models_dev_metadata,
        name="harness-models-dev-catalog",
        daemon=True,
    )
    thread.start()


def _refresh_models_dev_metadata() -> None:
    global _models_dev_refreshing  # noqa: PLW0603
    try:
        _hydrate_models_dev_metadata(allow_network=True)
    finally:
        with _catalog_lock:
            _models_dev_refreshing = False


def _models_dev_cache_fresh() -> bool:
    return (
        bool(_models_dev_fetched_at)
        and time.time() - _models_dev_fetched_at < _CATALOG_CACHE_SECONDS
    )


def _hydrate_models_dev_metadata(*, allow_network: bool) -> None:
    global _models_dev_fetched_at  # noqa: PLW0603
    if _models_dev_cache_fresh():
        return
    if not allow_network:
        return
    try:
        payload = _fetch_models_dev_payload()
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        _log.debug("models.dev catalog unavailable", extra={"fields": {"error": str(exc)}})
        return

    registry = get_registry()
    for info in _models_dev_model_infos(payload):
        if is_supported_model_for_provider(info.name, info.provider):
            registry.register(info)
    _models_dev_fetched_at = time.time()


def _fetch_models_dev_payload() -> dict[str, object]:
    request = urllib.request.Request(
        _MODELS_DEV_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "harness-model-catalog",
        },
    )
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(  # nosec B310
        request,
        timeout=_CATALOG_TIMEOUT_SECONDS,
        context=context,
    ) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not is_string_mapping(payload):
        raise ValueError("models.dev catalog response was not an object")
    return payload


def _models_dev_model_infos(payload: dict[str, object]) -> list[ModelInfo]:
    return [
        info
        for provider_slug in ("openai", "openai-codex", "deepseek", "openrouter")
        for info in _models_dev_provider_infos(payload, provider_slug)
        if is_supported_model_for_provider(info.name, info.provider)
    ]


def _models_dev_provider_infos(payload: dict[str, object], provider_slug: str) -> list[ModelInfo]:
    source_slug = "openai" if provider_slug == "openai-codex" else provider_slug
    provider_payload = payload.get(source_slug)
    if not is_string_mapping(provider_payload):
        return []
    raw_models = provider_payload.get("models")
    if not is_string_mapping(raw_models):
        return []
    return [
        info
        for raw_model in raw_models.values()
        if (info := _models_dev_model_info(raw_model, provider_slug)) is not None
    ]


def _models_dev_model_info(raw_model: object, provider_slug: str) -> ModelInfo | None:
    if not is_string_mapping(raw_model):
        return None
    model_id = _string_field(raw_model, "id")
    if not model_id:
        return None
    context_window, max_output = _models_dev_limits(raw_model)
    prompt_price, completion_price = _models_dev_prices(raw_model)
    tags = _models_dev_tags(raw_model, prompt_price, completion_price)
    return ModelInfo(
        name=model_id,
        provider=provider_slug,
        display_name=_string_field(raw_model, "name") or model_id,
        context_window=context_window or 128_000,
        max_output=max_output or 8_192,
        prompt_price_per_1k=prompt_price,
        completion_price_per_1k=completion_price,
        tags=tags,
        reasoning_efforts=_models_dev_reasoning_efforts(provider_slug, tags),
        input_modalities=_models_dev_modalities(raw_model),
        supports_tools=bool(raw_model.get("tool_call")),
    )


def _models_dev_reasoning_efforts(
    provider_slug: str,
    tags: tuple[str, ...],
) -> tuple[str, ...]:
    if "reasoning" not in tags:
        return ()
    if provider_slug in {"openai", "openai-codex"}:
        return _OPENAI_REASONING_EFFORTS
    if provider_slug == "deepseek":
        return _DEEPSEEK_REASONING_EFFORTS
    return _DEFAULT_REASONING_EFFORTS


def _models_dev_limits(raw_model: dict[str, object]) -> tuple[int, int]:
    limits = _mapping_field(raw_model, "limit") or {}
    return _int_field(limits, "context") or _int_field(limits, "input"), _int_field(
        limits,
        "output",
    )


def _models_dev_prices(raw_model: dict[str, object]) -> tuple[float, float]:
    cost = _mapping_field(raw_model, "cost") or {}
    return _models_dev_price_per_1k(cost.get("input")), _models_dev_price_per_1k(
        cost.get("output")
    )


def _models_dev_tags(
    raw_model: dict[str, object],
    prompt_price: float,
    completion_price: float,
) -> tuple[str, ...]:
    tags: list[str] = []
    if prompt_price == 0.0 and completion_price == 0.0:
        tags.append("free")
    if raw_model.get("reasoning") is True:
        tags.append("reasoning")
    if raw_model.get("tool_call") is True:
        tags.append("tools")
    return tuple(tags)


def _models_dev_modalities(raw_model: dict[str, object]) -> tuple[str, ...]:
    modalities = _mapping_field(raw_model, "modalities") or {}
    inputs = modalities.get("input")
    if not is_object_list(inputs):
        return ()
    return tuple(item for item in inputs if isinstance(item, str))


def _models_dev_price_per_1k(value: object) -> float:
    try:
        price_per_million = float(value) if isinstance(value, str | int | float) else 0.0
    except ValueError:
        return 0.0
    return price_per_million / 1000


def _fetch_and_cache_live_catalog(slug: str, endpoint: str) -> LiveProviderCatalog | None:
    try:
        catalog = _fetch_openrouter_catalog(endpoint)
    except (OSError, urllib.error.URLError, json.JSONDecodeError, ValueError) as exc:
        _log.debug(
            "live provider catalog unavailable",
            extra={"fields": {"provider": slug, "error": str(exc)}},
        )
        return None

    with _catalog_lock:
        _catalog_cache[slug] = _CatalogCacheEntry(fetched_at=time.time(), catalog=catalog)
    return catalog


def _fetch_openrouter_catalog(endpoint: str) -> LiveProviderCatalog:
    url = f"{endpoint.strip().rstrip('/')}/models"
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("OpenRouter catalog URL must use https")
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "harness-model-catalog",
        },
    )
    context = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(  # nosec B310
        request,
        timeout=_CATALOG_TIMEOUT_SECONDS,
        context=context,
    ) as response:
        payload = json.loads(response.read().decode("utf-8"))

    if not is_string_mapping(payload):
        raise ValueError("OpenRouter catalog response was not an object")

    raw_models = payload.get("data")
    if not is_object_list(raw_models):
        raise ValueError("OpenRouter catalog response did not include a model list")

    models: list[str] = []
    metadata: list[ModelInfo] = []
    for raw_model in raw_models:
        info = _openrouter_model_info(raw_model)
        if info is None:
            continue
        if not is_supported_model_for_provider(info.name, info.provider):
            continue
        models.append(info.name)
        metadata.append(info)

    return LiveProviderCatalog(models=models, metadata=metadata)


def _openrouter_model_info(raw_model: object) -> ModelInfo | None:
    if not is_string_mapping(raw_model):
        return None

    model_id = _string_field(raw_model, "id")
    if not model_id:
        return None
    if not _is_text_output_model(raw_model):
        return None

    prompt_price, completion_price = _openrouter_prices(raw_model)
    context_window, max_output = _openrouter_limits(raw_model)

    return ModelInfo(
        name=model_id,
        provider="openrouter",
        display_name=_string_field(raw_model, "name") or model_id,
        context_window=context_window or 128_000,
        max_output=max_output or 8_192,
        prompt_price_per_1k=prompt_price,
        completion_price_per_1k=completion_price,
        tags=_openrouter_tags(raw_model, prompt_price, completion_price),
    )


def _openrouter_prices(raw_model: dict[str, object]) -> tuple[float, float]:
    pricing = _mapping_field(raw_model, "pricing") or {}
    return _price_per_1k(pricing.get("prompt")), _price_per_1k(pricing.get("completion"))


def _openrouter_limits(raw_model: dict[str, object]) -> tuple[int, int]:
    top_provider = _mapping_field(raw_model, "top_provider") or {}
    context_window = _int_field(raw_model, "context_length") or _int_field(
        top_provider, "context_length"
    )
    return context_window, _int_field(top_provider, "max_completion_tokens")


def _openrouter_tags(
    raw_model: dict[str, object],
    prompt_price: float,
    completion_price: float,
) -> tuple[str, ...]:
    tags: list[str] = []
    if prompt_price == 0.0 and completion_price == 0.0:
        tags.append("free")
    supported_parameters = raw_model.get("supported_parameters")
    if is_object_list(supported_parameters):
        tags.extend(tag for tag in ("reasoning", "tools") if tag in supported_parameters)
    return tuple(tags)


def _is_text_output_model(raw_model: dict[str, object]) -> bool:
    architecture = _mapping_field(raw_model, "architecture")
    if architecture is not None:
        output_modalities = architecture.get("output_modalities")
        if is_object_list(output_modalities):
            return "text" in output_modalities
        modality = architecture.get("modality")
        if isinstance(modality, str):
            return modality.endswith("->text") or "->text+" in modality
    return True


def _mapping_field(raw: dict[str, object] | None, key: str) -> dict[str, object] | None:
    value = raw.get(key) if raw is not None else None
    return value if is_string_mapping(value) else None


def _string_field(raw: dict[str, object], key: str) -> str:
    value = raw.get(key)
    return value.strip() if isinstance(value, str) else ""


def _int_field(raw: dict[str, object], key: str) -> int:
    value = raw.get(key)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0


def _price_per_1k(value: object) -> float:
    if isinstance(value, str):
        try:
            return float(value) * 1000
        except ValueError:
            return 0.0
    return float(value) * 1000 if isinstance(value, int | float) else 0.0
