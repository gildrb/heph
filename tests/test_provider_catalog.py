from __future__ import annotations

import json
from typing import Self

import pytest

from hephaistos.providers import catalog
from hephaistos.providers.catalog import LiveProviderCatalog
from hephaistos.providers.config import default_config
from hephaistos.providers.model_choices import configured_model_choices
from hephaistos.providers.registry import ModelInfo, get_registry


def test_configured_choices_hydrates_openrouter_live_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HEPHAISTOS_DISABLE_LIVE_MODELS", raising=False)
    catalog.invalidate_catalog_cache()

    def fake_fetch(_endpoint: str) -> LiveProviderCatalog:
        return LiveProviderCatalog(
            models=[
                "anthropic/claude-sonnet-latest",
                "poolside/laguna-m.1:free",
            ],
            metadata=[
                ModelInfo(
                    "anthropic/claude-sonnet-latest",
                    "openrouter",
                    "Anthropic Claude Sonnet Latest",
                    1_000_000,
                    128_000,
                    0.003,
                    0.015,
                ),
                ModelInfo(
                    "poolside/laguna-m.1:free",
                    "openrouter",
                    "Poolside Laguna M.1 (free)",
                    131_072,
                    8_192,
                    0.0,
                    0.0,
                    tags=("free",),
                ),
            ],
        )

    monkeypatch.setattr(catalog, "_fetch_openrouter_catalog", fake_fetch)
    config = default_config()
    config.set_active("openrouter")

    choices = configured_model_choices(config)

    assert config.providers["openrouter"].models == [
        "anthropic/claude-sonnet-latest",
        "poolside/laguna-m.1:free",
    ]
    assert choices[0][0] == "openrouter"
    assert choices[0][1] == "poolside/laguna-m.1:free"
    assert get_registry().get("anthropic/claude-sonnet-latest") is not None


def test_live_catalog_failure_keeps_static_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HEPHAISTOS_DISABLE_LIVE_MODELS", raising=False)
    catalog.invalidate_catalog_cache()

    def fail_fetch(_endpoint: str) -> LiveProviderCatalog:
        raise OSError("offline")

    monkeypatch.setattr(catalog, "_fetch_openrouter_catalog", fail_fetch)
    config = default_config()
    static_models = list(config.providers["openrouter"].models)

    configured_model_choices(config)

    assert config.providers["openrouter"].models == static_models


def test_hydrate_provider_models_resets_invalid_current_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HEPHAISTOS_DISABLE_LIVE_MODELS", raising=False)
    config = default_config()
    provider = config.providers["openrouter"]
    provider.current_model = "stale-model"
    model_name = "acme/test-reasoning-model"

    monkeypatch.setattr(
        catalog,
        "_live_catalog_for_provider",
        lambda slug, _endpoint: (
            LiveProviderCatalog(
                models=[model_name],
                metadata=[
                    ModelInfo(
                        model_name,
                        slug,
                        "Acme Test Model",
                        256_000,
                        16_384,
                        0.001,
                        0.002,
                        tags=("reasoning",),
                    )
                ],
            )
            if slug == "openrouter"
            else None
        ),
    )

    catalog.hydrate_provider_models(config)

    assert provider.models == [model_name]
    assert provider.current_model == ""
    assert get_registry().get(model_name) is not None


def test_live_catalog_for_provider_uses_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    cached_catalog = LiveProviderCatalog(models=["cached/model"], metadata=[])
    catalog.invalidate_catalog_cache()
    catalog._catalog_cache["openrouter"] = catalog._CatalogCacheEntry(  # type: ignore[reportPrivateUsage]
        fetched_at=100.0,
        catalog=cached_catalog,
    )
    monkeypatch.setattr(catalog.time, "time", lambda: 101.0)

    assert catalog._live_catalog_for_provider("zai", "https://api.z.ai") is None  # type: ignore[reportPrivateUsage]
    assert (
        catalog._live_catalog_for_provider(  # type: ignore[reportPrivateUsage]
            "openrouter",
            "https://openrouter.ai/api/v1",
        )
        == cached_catalog
    )


class _FakeResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def __enter__(self) -> Self:
        return self

    def __exit__(self, _exc_type: object, _exc: object, _tb: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_fetch_openrouter_catalog_parses_models(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "data": [
            {
                "id": "acme/text-model",
                "name": "Acme Text Model",
                "pricing": {"prompt": "0", "completion": "0"},
                "top_provider": {
                    "context_length": 65_536,
                    "max_completion_tokens": 4_096,
                },
                "supported_parameters": ["reasoning", "tools"],
                "architecture": {"output_modalities": ["text"]},
            },
            {
                "id": "acme/image-model",
                "architecture": {"output_modalities": ["image"]},
            },
            {"name": "missing-id"},
        ]
    }
    monkeypatch.setattr(catalog.certifi, "where", lambda: "/tmp/cacert.pem")
    monkeypatch.setattr(catalog.ssl, "create_default_context", lambda cafile: object())
    monkeypatch.setattr(
        catalog.urllib.request,
        "urlopen",
        lambda request, timeout, context: _FakeResponse(payload),
    )

    result = catalog._fetch_openrouter_catalog("https://openrouter.ai/api/v1/")  # type: ignore[reportPrivateUsage]

    assert result.models == ["acme/text-model"]
    info = result.metadata[0]
    assert info.context_window == 65_536
    assert info.max_output == 4_096
    assert info.prompt_price_per_1k == 0.0
    assert set(info.tags) == {"free", "reasoning", "tools"}


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "OpenRouter catalog response was not an object"),
        ({"data": "invalid"}, "OpenRouter catalog response did not include a model list"),
    ],
)
def test_fetch_openrouter_catalog_rejects_invalid_payload(
    monkeypatch: pytest.MonkeyPatch,
    payload: object,
    message: str,
) -> None:
    monkeypatch.setattr(catalog.certifi, "where", lambda: "/tmp/cacert.pem")
    monkeypatch.setattr(catalog.ssl, "create_default_context", lambda cafile: object())
    monkeypatch.setattr(
        catalog.urllib.request,
        "urlopen",
        lambda request, timeout, context: _FakeResponse(payload),
    )

    with pytest.raises(ValueError, match=message):
        catalog._fetch_openrouter_catalog("https://openrouter.ai/api/v1/")  # type: ignore[reportPrivateUsage]
