from __future__ import annotations

from types import SimpleNamespace

from hephaistos.providers.config import ProviderConfig, _default_config
from hephaistos.providers.model_support import is_supported_model_for_endpoint
from hephaistos.providers.registry import ModelInfo, ModelRegistry


def test_default_openrouter_models_match_supported_families() -> None:
    config = _default_config()

    assert "openrouter" in config.providers
    assert all(
        model.startswith(
            (
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


def test_load_filters_unsupported_models(tmp_path) -> None:
    config_path = tmp_path / "providers.toml"
    config_path.write_text(
        """
[openrouter]
display_name = "OpenRouter"
endpoint = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"
active = true
current_model = "legacy/vendor-model"
models = [
  "legacy/vendor-model",
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


def test_load_clears_current_model_when_all_models_are_filtered_out(tmp_path) -> None:
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

    assert provider.models == []
    assert provider.current_model == ""


def test_load_preserves_current_model_without_models_list(tmp_path) -> None:
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
    config = SimpleNamespace(base_url="", model="")

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


def test_model_registry_ignores_unsupported_models() -> None:
    registry = ModelRegistry(
        [
            ModelInfo("legacy/vendor-model", "openrouter", "Legacy", 1, 1, 0.1, 0.2),
            ModelInfo("gpt-5.4", "openai-codex", "GPT-5.4", 1, 1, 0.1, 0.2),
        ]
    )

    assert registry.get("legacy/vendor-model") is None
    assert registry.get("gpt-5.4") is not None
