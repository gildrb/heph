from __future__ import annotations

from hephaistos.providers.config import ProviderConfig, _default_config
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


def test_set_model_rejects_unknown_name() -> None:
    config = _default_config()

    assert not config.set_model("openrouter", "legacy/vendor-model")


def test_model_registry_ignores_unsupported_models() -> None:
    registry = ModelRegistry(
        [
            ModelInfo("legacy/vendor-model", "openrouter", "Legacy", 1, 1, 0.1, 0.2),
            ModelInfo("gpt-5.4", "openai-codex", "GPT-5.4", 1, 1, 0.1, 0.2),
        ]
    )

    assert registry.get("legacy/vendor-model") is None
    assert registry.get("gpt-5.4") is not None
