from __future__ import annotations

from hephaistos.providers.config import ProviderConfig, _default_config
from hephaistos.providers.registry import ModelInfo, ModelRegistry


def test_default_openrouter_models_exclude_anthropic() -> None:
    config = _default_config()

    assert "openrouter" in config.providers
    assert all(
        "anthropic" not in model.lower() and "claude" not in model.lower()
        for model in config.providers["openrouter"].models
    )


def test_load_filters_blocked_models(tmp_path) -> None:
    config_path = tmp_path / "providers.toml"
    config_path.write_text(
        """
[openrouter]
display_name = "OpenRouter"
endpoint = "https://openrouter.ai/api/v1"
api_key_env = "OPENROUTER_API_KEY"
active = true
current_model = "anthropic/claude-sonnet-4.6"
models = [
  "anthropic/claude-sonnet-4.6",
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


def test_set_model_rejects_blocked_name() -> None:
    config = _default_config()

    assert not config.set_model("openrouter", "anthropic/claude-sonnet-4.6")


def test_model_registry_ignores_blocked_models() -> None:
    registry = ModelRegistry(
        [
            ModelInfo("anthropic/claude-sonnet-4.6", "openrouter", "Claude", 1, 1, 0.1, 0.2),
            ModelInfo("gpt-5.4", "openai-codex", "GPT-5.4", 1, 1, 0.1, 0.2),
        ]
    )

    assert registry.get("anthropic/claude-sonnet-4.6") is None
    assert registry.get("gpt-5.4") is not None
