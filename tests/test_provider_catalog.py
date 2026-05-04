from __future__ import annotations

import pytest

from hephaistos.commands.model_picker import configured_model_choices
from hephaistos.providers import catalog
from hephaistos.providers.catalog import LiveProviderCatalog
from hephaistos.providers.config import default_config
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
