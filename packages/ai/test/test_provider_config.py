from __future__ import annotations

from pathlib import Path

from ai.providers.config import (
    ProviderConfig,
    default_config,
)
from ai.providers.model_support import is_supported_model_for_endpoint
from ai.providers.registry import ModelInfo, ModelRegistry
from ai.runtime import ChatConfig


def test_default_openrouter_models_match_supported_families() -> None:
    config = default_config()

    assert "openrouter" in config.providers
    assert all(
        model.startswith(
            (
                "openrouter/",
                "openai/",
                "google/",
                "qwen/",
                "stepfun/",
                "minimax/",
                "z-ai/",
                "moonshotai/",
                "xiaomi/",
                "x-ai/",
                "nvidia/",
                "arcee-ai/",
            )
        )
        for model in config.providers["openrouter"].models
    )


def test_default_pollinations_models_match_supported_families() -> None:
    config = default_config()

    assert "pollinations" in config.providers
    assert all(model.startswith(("openai",)) for model in config.providers["pollinations"].models)
    assert config.providers["pollinations"].models == ["openai", "openai-fast"]


def test_default_config_activates_pollinations_as_default() -> None:
    config = default_config()
    chat_config = ChatConfig(base_url="", model="")

    config.apply_to_config(chat_config)

    assert "openai" in config.providers
    assert "gpt-5.5" in config.providers["openai"].models
    assert all(
        model in config.providers["openai-codex"].models
        for model in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna")
    )
    assert "gpt-5.5" in config.providers["openai-codex"].models
    assert config.get_active() is config.providers["pollinations"]
    assert chat_config.base_url == "https://text.pollinations.ai/openai"
    assert chat_config.model == "openai"
    assert chat_config._provider_slug == "pollinations"


def test_load_missing_config_stays_in_memory_until_saved(tmp_path: Path) -> None:
    config_path = tmp_path / "providers.toml"

    loaded = ProviderConfig.load(config_path)

    assert "zai" in loaded.providers
    assert not config_path.exists()


def test_load_restores_missing_builtin_providers(tmp_path: Path) -> None:
    config_path = tmp_path / "providers.toml"
    config_path.write_text(
        """
[openrouter]
display_name = "OpenRouter"
endpoint = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"
active = true
current_model = "qwen/qwen3.6-plus:free"
models = ["qwen/qwen3.6-plus:free"]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    loaded = ProviderConfig.load(config_path)
    active = loaded.get_active()

    assert "pollinations" in loaded.providers
    assert loaded.providers["pollinations"].models
    assert loaded.providers["pollinations"].active is False
    assert active is not None
    assert active.slug == "openrouter"


def test_load_legacy_config_activates_pollinations_when_no_active(tmp_path: Path) -> None:
    config_path = tmp_path / "providers.toml"
    config_path.write_text(
        """
[openrouter]
display_name = "OpenRouter"
endpoint = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"
models = ["openrouter/free"]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    loaded = ProviderConfig.load(config_path)
    config = ChatConfig(base_url="", model="")

    loaded.apply_to_config(config)

    assert "pollinations" in loaded.providers
    assert loaded.get_active() is loaded.providers["pollinations"]
    assert config.base_url == "https://text.pollinations.ai/openai"
    assert config.model == "openai"
    assert config.provider_slug == "pollinations"


def test_load_refreshes_when_provider_path_changes(tmp_path: Path) -> None:
    first_path = tmp_path / "first-providers.toml"
    first_path.write_text(
        """
[openai-codex]
display_name = "OpenAI Codex"
endpoint = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"
active = true
current_model = "gpt-5.4"
models = ["gpt-5.4"]
""".strip()
        + "\n",
        encoding="utf-8",
    )
    second_path = tmp_path / "second-providers.toml"
    second_path.write_text(
        """
[custom]
display_name = "Custom"
endpoint = "https://example.com/v1"
api_key_env = "CUSTOM_API_KEY"
active = true
current_model = "custom-model"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    first = ProviderConfig.load(first_path)
    second = ProviderConfig.load(second_path)
    first_active = first.get_active()
    second_active = second.get_active()

    assert first_active is not None
    assert first_active.slug == "openai-codex"
    assert second_active is not None
    assert second_active.slug == "custom"


def test_load_filters_unsupported_models(tmp_path: Path) -> None:
    config_path = tmp_path / "providers.toml"
    config_path.write_text(
        """
[openrouter]
display_name = "OpenRouter"
endpoint = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"
active = true
current_model = "legacy-model"
models = [
  "legacy-model",
  "openai/gpt-5.4",
  "google/gemini-3-flash-preview",
]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    loaded = ProviderConfig.load(config_path)
    provider = loaded.providers["openrouter"]

    assert provider.models == [
        "openai/gpt-5.4",
        "google/gemini-3-flash-preview",
    ]
    assert provider.current_model == ""


def test_load_clears_current_model_when_all_models_are_filtered_out(tmp_path: Path) -> None:
    config_path = tmp_path / "providers.toml"
    config_path.write_text(
        """
[openai-codex]
display_name = "OpenAI Codex"
endpoint = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"
active = true
current_model = "legacy-model"
models = [
  "legacy-model",
]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    loaded = ProviderConfig.load(config_path)
    provider = loaded.providers["openai-codex"]

    assert provider.api_key_env == ""
    assert provider.models[0] == "gpt-5.6-sol"
    assert provider.current_model == ""


def test_load_preserves_current_model_without_models_list(tmp_path: Path) -> None:
    config_path = tmp_path / "providers.toml"
    config_path.write_text(
        """
[custom]
display_name = "Custom"
endpoint = "https://example.com/v1"
api_key_env = "CUSTOM_API_KEY"
active = true
current_model = "my-custom-model"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    loaded = ProviderConfig.load(config_path)
    provider = loaded.providers["custom"]
    config = ChatConfig(base_url="", model="")

    loaded.apply_to_config(config)

    assert provider.models == []
    assert provider.current_model == "my-custom-model"
    assert config.model == "my-custom-model"


def test_supported_model_for_zai_endpoint_accepts_trailing_slash_variants() -> None:
    assert is_supported_model_for_endpoint("glm-5-turbo", "https://api.z.ai/api/paas/v4")
    assert is_supported_model_for_endpoint("glm-5-turbo", "https://api.z.ai/api/paas/v4/")
    assert not is_supported_model_for_endpoint(
        "gpt-5.4",
        "https://api.z.ai/api/paas/v4/",
    )


def test_load_refreshes_legacy_openai_codex_model_catalog(tmp_path: Path) -> None:
    config_path = tmp_path / "providers.toml"
    config_path.write_text(
        """
[openai-codex]
display_name = "OpenAI Codex"
endpoint = "https://api.openai.com/v1"
api_key_env = "OPENAI_API_KEY"
active = true
current_model = "gpt-5.4-mini"
models = ["gpt-5.4", "gpt-5.4-mini"]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    loaded = ProviderConfig.load(config_path)
    provider = loaded.providers["openai-codex"]

    assert provider.api_key_env == ""
    assert provider.models[:2] == ["gpt-5.6-sol", "gpt-5.6-terra"]
    assert provider.current_model == "gpt-5.4-mini"


def test_model_registry_ignores_unsupported_models() -> None:
    registry = ModelRegistry(
        [
            ModelInfo("legacy-model", "openrouter", "Legacy", 1, 1, 0.1, 0.2),
            ModelInfo("gpt-5.4", "openai-codex", "GPT-5.4", 1, 1, 0.1, 0.2),
            ModelInfo("gpt-5.4", "openai", "GPT-5.4 API", 1, 1, 0.1, 0.2),
        ]
    )

    assert registry.get("legacy-model") is None
    assert registry.get("gpt-5.4") is not None
    assert registry.get("gpt-5.4", provider="openai") is not None
    assert registry.list_models(provider="openai")
