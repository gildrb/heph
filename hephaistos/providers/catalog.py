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

from hephaistos._types import is_object_list, is_string_mapping
from hephaistos.logging import get_logger
from hephaistos.providers.config import ProviderConfig
from hephaistos.providers.registry import ModelInfo, get_registry

_log = get_logger("providers.catalog")

_CATALOG_TIMEOUT_SECONDS = 2.0
_CATALOG_CACHE_SECONDS = 10 * 60
_DISABLE_LIVE_CATALOG_ENV = "HEPHAISTOS_DISABLE_LIVE_MODELS"


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


def hydrate_provider_models(
    config: ProviderConfig,
    *,
    allow_network: bool = False,
    provider_slugs: set[str] | None = None,
) -> None:
    """Update provider model lists from cached live catalogs when available.

    The default path never waits on the network. If a live catalog is stale or missing,
    a daemon refresh is scheduled and the caller keeps the static/stale model list.
    Pass ``allow_network=True`` only from a worker or an explicitly blocking command.
    """
    if os.environ.get(_DISABLE_LIVE_CATALOG_ENV, "").strip():
        return

    for slug, provider in config.providers.items():
        if provider_slugs is not None and slug not in provider_slugs:
            continue
        catalog = _live_catalog_for_provider(
            slug,
            provider.endpoint,
            allow_network=allow_network,
        )
        if catalog is None or not catalog.models:
            continue
        provider.models = catalog.models
        if provider.current_model and provider.current_model not in provider.models:
            provider.current_model = ""
        registry = get_registry()
        for info in catalog.metadata:
            registry.register(info)


def prefetch_provider_model_catalogs(
    config: ProviderConfig,
    *,
    provider_slugs: set[str] | None = None,
) -> None:
    """Start live model catalog refreshes without blocking the caller."""
    if os.environ.get(_DISABLE_LIVE_CATALOG_ENV, "").strip():
        return

    for slug, provider in config.providers.items():
        if provider_slugs is not None and slug not in provider_slugs:
            continue
        _schedule_live_catalog_refresh(slug, provider.endpoint)


def invalidate_catalog_cache() -> None:
    """Clear live catalog cache, mostly for tests."""
    with _catalog_lock:
        _catalog_cache.clear()
        _catalog_refreshing.clear()


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
        name=f"hephaistos-{slug}-catalog",
        daemon=True,
    )
    thread.start()


def _refresh_live_catalog(slug: str, endpoint: str) -> None:
    try:
        _fetch_and_cache_live_catalog(slug, endpoint)
    finally:
        with _catalog_lock:
            _catalog_refreshing.discard(slug)


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
            "User-Agent": "hephaistos-model-catalog",
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

    pricing = _mapping_field(raw_model, "pricing")
    top_provider = _mapping_field(raw_model, "top_provider")

    prompt_price = _price_per_1k(pricing.get("prompt") if pricing is not None else None)
    completion_price = _price_per_1k(pricing.get("completion") if pricing is not None else None)
    context_window = _int_field(raw_model, "context_length") or _int_field(
        top_provider, "context_length"
    )
    max_output = _int_field(top_provider, "max_completion_tokens")

    tags: list[str] = []
    if prompt_price == 0.0 and completion_price == 0.0:
        tags.append("free")
    supported_parameters = raw_model.get("supported_parameters")
    if is_object_list(supported_parameters) and "reasoning" in supported_parameters:
        tags.append("reasoning")
    if is_object_list(supported_parameters) and "tools" in supported_parameters:
        tags.append("tools")

    return ModelInfo(
        name=model_id,
        provider="openrouter",
        display_name=_string_field(raw_model, "name") or model_id,
        context_window=context_window or 128_000,
        max_output=max_output or 8_192,
        prompt_price_per_1k=prompt_price,
        completion_price_per_1k=completion_price,
        tags=tuple(tags),
    )


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
    if raw is None:
        return None
    value = raw.get(key)
    return value if is_string_mapping(value) else None


def _string_field(raw: dict[str, object], key: str) -> str:
    value = raw.get(key)
    return value.strip() if isinstance(value, str) else ""


def _int_field(raw: dict[str, object] | None, key: str) -> int:
    if raw is None:
        return 0
    value = raw.get(key)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0


def _price_per_1k(value: object) -> float:
    if isinstance(value, int | float):
        return float(value) * 1000
    if isinstance(value, str):
        try:
            return float(value) * 1000
        except ValueError:
            return 0.0
    return 0.0
