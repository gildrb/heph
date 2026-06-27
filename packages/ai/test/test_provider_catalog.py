from __future__ import annotations

import json
from typing import Self

import pytest
from ai.providers import catalog
from ai.providers.catalog import LiveProviderCatalog
from ai.providers.config import default_config
from ai.providers.llama_cpp import LlamaCppModelRecord
from ai.providers.model_choices import configured_model_choices, model_picker_columns
from ai.providers.reasoning import reasoning_levels_for_model
from ai.providers.registry import ModelInfo, get_registry


def _openrouter_live_catalog() -> LiveProviderCatalog:
    return LiveProviderCatalog(
        models=[
            "google/gemini-3-flash-preview",
            "poolside/laguna-m.1:free",
        ],
        metadata=[
            ModelInfo(
                "google/gemini-3-flash-preview",
                "openrouter",
                "Google Gemini 3 Flash Preview",
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


def test_model_picker_columns_use_readable_labels() -> None:
    assert model_picker_columns(
        slug="openrouter",
        model="openai/gpt-5.4",
        display_name="OpenRouter",
        endpoint="https://openrouter.ai/api/v1",
        is_free=False,
        is_current=False,
    ) == ("OpenAI", "gpt-5.4", "OpenRouter", "")
    assert model_picker_columns(
        slug="pollinations",
        model="gemini-thinking",
        display_name="Pollinations AI (free)",
        endpoint="https://text.pollinations.ai/openai",
        is_free=True,
        is_current=True,
    ) == ("Google", "gemini-thinking", "Pollinations", "free current")
    assert model_picker_columns(
        slug="openai-codex",
        model="gpt-5.5",
        display_name="OpenAI Codex",
        endpoint="https://api.openai.com/v1",
        is_free=False,
        is_current=True,
    ) == ("OpenAI", "gpt-5.5", "OpenAI Codex", "current")
    assert model_picker_columns(
        slug="openrouter",
        model="poolside/laguna-m.1:free",
        display_name="OpenRouter",
        endpoint="https://openrouter.ai/api/v1",
        is_free=True,
        is_current=False,
    ) == ("Poolside", "laguna-m.1:free", "OpenRouter", "free+key")
    assert model_picker_columns(
        slug="llama-cpp",
        model="llama-cpp/acme/model:Q4_K_M",
        display_name="Local llama.cpp",
        endpoint="http://127.0.0.1:18080/v1",
        is_free=True,
        is_current=False,
    ) == ("Local", "model:Q4_K_M", "Local", "local tool-capable free")


def test_configured_choices_uses_cached_openrouter_live_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HARNESS_DISABLE_LIVE_MODELS", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    catalog.invalidate_catalog_cache()
    catalog._catalog_cache["openrouter"] = catalog._CatalogCacheEntry(
        fetched_at=100.0,
        catalog=_openrouter_live_catalog(),
    )
    monkeypatch.setattr(catalog.time, "time", lambda: 101.0)
    config = default_config()
    config.set_active("openrouter")

    choices = configured_model_choices(config)

    assert config.providers["openrouter"].models == [
        "google/gemini-3-flash-preview",
        "poolside/laguna-m.1:free",
    ]
    assert choices[0][0] == "openrouter"
    assert choices[0][1] == "poolside/laguna-m.1:free"
    assert get_registry().get("google/gemini-3-flash-preview") is not None


def test_configured_choices_schedules_refresh_without_waiting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HARNESS_DISABLE_LIVE_MODELS", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    catalog.invalidate_catalog_cache()
    scheduled: list[str] = []

    def fail_fetch(_endpoint: str) -> LiveProviderCatalog:
        raise AssertionError("configured_model_choices must not fetch synchronously")

    monkeypatch.setattr(catalog, "_fetch_openrouter_catalog", fail_fetch)
    monkeypatch.setattr(
        catalog,
        "_schedule_live_catalog_refresh",
        lambda slug, _endpoint: scheduled.append(slug),
    )
    config = default_config()
    config.set_active("openrouter")

    choices = configured_model_choices(config)

    assert any(choice[0] == "openrouter" for choice in choices)
    assert scheduled == ["openrouter"]


def test_configured_choices_include_only_tool_capable_local_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    passing = LlamaCppModelRecord(
        model_id="llama-cpp/acme/pass:Q4_K_M",
        repo_id="acme/pass",
        quant="Q4_K_M",
        tool_capable=True,
        endpoint="http://127.0.0.1:18123/v1",
    )
    monkeypatch.setattr(catalog, "installed_tool_capable_records", lambda: [passing])
    config = default_config()

    choices = configured_model_choices(config)

    assert config.providers["llama-cpp"].models == [passing.model_id]
    assert config.providers["llama-cpp"].endpoint == passing.endpoint
    assert (passing.model_id, "llama-cpp") in {
        (model, slug) for slug, model, _display, _free in choices
    }
    info = get_registry().get(passing.model_id, provider="llama-cpp")
    assert info is not None
    assert info.supports_tools is True
    assert set(info.tags) == {"local", "tools"}


def test_hydrate_provider_models_can_refresh_openrouter_live_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HARNESS_DISABLE_LIVE_MODELS", raising=False)
    catalog.invalidate_catalog_cache()
    monkeypatch.setattr(
        catalog,
        "_fetch_openrouter_catalog",
        lambda _endpoint: _openrouter_live_catalog(),
    )
    config = default_config()
    config.set_active("openrouter")

    catalog.hydrate_provider_models(
        config,
        allow_network=True,
        provider_slugs={"openrouter"},
    )

    assert config.providers["openrouter"].models == [
        "google/gemini-3-flash-preview",
        "poolside/laguna-m.1:free",
    ]
    assert get_registry().get("google/gemini-3-flash-preview") is not None


def test_live_catalog_failure_keeps_static_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HARNESS_DISABLE_LIVE_MODELS", raising=False)
    catalog.invalidate_catalog_cache()

    def fail_fetch(_endpoint: str) -> LiveProviderCatalog:
        raise OSError("offline")

    monkeypatch.setattr(catalog, "_fetch_openrouter_catalog", fail_fetch)
    config = default_config()
    static_models = list(config.providers["openrouter"].models)

    catalog.hydrate_provider_models(
        config,
        allow_network=True,
        provider_slugs={"openrouter"},
    )

    assert config.providers["openrouter"].models == static_models


def test_hydrate_provider_models_resets_invalid_current_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HARNESS_DISABLE_LIVE_MODELS", raising=False)
    config = default_config()
    provider = config.providers["openrouter"]
    provider.current_model = "stale-model"
    model_name = "acme/test-reasoning-model"

    def fake_live_catalog(
        slug: str,
        _endpoint: str,
        *,
        allow_network: bool = False,
    ) -> LiveProviderCatalog | None:
        _ = allow_network
        if slug != "openrouter":
            return None
        return LiveProviderCatalog(
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

    monkeypatch.setattr(catalog, "_live_catalog_for_provider", fake_live_catalog)

    catalog.hydrate_provider_models(config)

    assert provider.models == [model_name]
    assert provider.current_model == ""
    assert get_registry().get(model_name) is not None


def test_live_catalog_for_provider_uses_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    cached_catalog = LiveProviderCatalog(models=["cached/model"], metadata=[])
    catalog.invalidate_catalog_cache()
    catalog._catalog_cache["openrouter"] = catalog._CatalogCacheEntry(
        fetched_at=100.0,
        catalog=cached_catalog,
    )
    monkeypatch.setattr(catalog.time, "time", lambda: 101.0)

    assert catalog._live_catalog_for_provider("zai", "https://api.z.ai") is None
    assert (
        catalog._live_catalog_for_provider(
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

    result = catalog._fetch_openrouter_catalog("https://openrouter.ai/api/v1/")

    assert result.models == ["acme/text-model"]
    info = result.metadata[0]
    assert info.context_window == 65_536
    assert info.max_output == 4_096
    assert info.prompt_price_per_1k == 0.0
    assert set(info.tags) == {"free", "reasoning", "tools"}


def test_models_dev_metadata_registers_openai_xhigh_and_non_openai_standard_reasoning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HARNESS_DISABLE_LIVE_MODELS", raising=False)
    catalog.invalidate_catalog_cache()
    monkeypatch.setattr(catalog, "_models_dev_cache_fresh", lambda: False)
    payload = {
        "openai": {
            "models": {
                "gpt-test-5.5": {
                    "id": "gpt-test-5.5",
                    "name": "GPT-5.5",
                    "reasoning": True,
                    "tool_call": True,
                    "modalities": {"input": ["text", "image"]},
                    "limit": {"context": 1_050_000, "output": 128_000},
                    "cost": {"input": 5, "output": 30},
                }
            }
        },
        "openrouter": {
            "models": {
                "test-lab/reasoning-model": {
                    "id": "test-lab/reasoning-model",
                    "name": "Reasoning Model",
                    "reasoning": True,
                    "tool_call": True,
                    "modalities": {"input": ["text"]},
                    "limit": {"context": 200_000, "output": 32_000},
                    "cost": {"input": 15, "output": 75},
                }
            }
        },
    }
    monkeypatch.setattr(catalog, "_fetch_models_dev_payload", lambda: payload)

    config = default_config()
    catalog.hydrate_provider_models(config, allow_network=True)

    openai_info = get_registry().get("gpt-test-5.5", provider="openai")
    openrouter_info = get_registry().get("test-lab/reasoning-model", provider="openrouter")
    assert openai_info is not None
    assert openai_info.reasoning_efforts == ("low", "medium", "high", "xhigh")
    assert openai_info.input_modalities == ("text", "image")
    assert openai_info.supports_tools is True
    assert openrouter_info is not None
    assert openrouter_info.reasoning_efforts == ("low", "medium", "high")


def test_provider_scoped_model_lookup_does_not_inherit_openai_reasoning() -> None:
    get_registry().register(
        ModelInfo(
            "same-model",
            "openai",
            "OpenAI Same Model",
            128_000,
            8_192,
            0.0,
            0.0,
            tags=("reasoning",),
            reasoning_efforts=("low", "medium", "high", "xhigh"),
        )
    )
    get_registry().register(
        ModelInfo(
            "same-model",
            "custom",
            "Custom Same Model",
            128_000,
            8_192,
            0.0,
            0.0,
            tags=("reasoning",),
            reasoning_efforts=("low", "medium", "high"),
        )
    )

    custom_info = get_registry().get("same-model", provider="custom")

    assert custom_info is not None
    assert custom_info.provider == "custom"
    assert custom_info.reasoning_efforts == ("low", "medium", "high")


def test_provider_scoped_reasoning_does_not_fall_back_to_openai_model() -> None:
    get_registry().register(
        ModelInfo(
            "openai-only-test-model",
            "openai",
            "OpenAI Only Test Model",
            128_000,
            8_192,
            0.0,
            0.0,
            tags=("reasoning",),
            reasoning_efforts=("low", "medium", "high", "xhigh"),
        )
    )

    assert reasoning_levels_for_model("openai-only-test-model", "openai") == (
        "low",
        "medium",
        "high",
        "xhigh",
    )
    assert reasoning_levels_for_model("openai-only-test-model", "openrouter") == ()


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
        catalog._fetch_openrouter_catalog("https://openrouter.ai/api/v1/")
