from __future__ import annotations

from ai.providers.api_profiles import (
    reasoning_payload_for_profile,
    request_profile_for_config,
)
from ai.providers.config import default_config
from ai.providers.model_support import (
    filter_supported_models,
    is_supported_model_for_endpoint,
)
from ai.providers.reasoning import reasoning_levels_for_model
from ai.runtime.config import ChatConfig
from ai.runtime.request_payload import request_kwargs


def _provider_config(slug: str, base_url: str, model: str, reasoning_level: str) -> ChatConfig:
    config = ChatConfig(
        base_url=base_url,
        model=model,
        reasoning_level=reasoning_level,
        temperature=0.7,
    )
    config.apply_provider_reference(slug, "")
    return config


def test_default_config_includes_official_deepseek_api_provider() -> None:
    provider = default_config().providers["deepseek"]

    assert provider.endpoint == "https://api.deepseek.com"
    assert provider.api_key_env == "DEEPSEEK_API_KEY"
    assert "deepseek-v4-pro" in provider.models
    assert "deepseek-v4-flash" in provider.models


def test_deepseek_model_filter_accepts_only_deepseek_models() -> None:
    models = filter_supported_models(
        ["deepseek-v4-pro", "gpt-5.5", "deepseek-reasoner"],
        "deepseek",
    )

    assert models == ["deepseek-v4-pro", "deepseek-reasoner"]
    assert is_supported_model_for_endpoint("deepseek-v4-flash", "https://api.deepseek.com")
    assert not is_supported_model_for_endpoint("gpt-5.5", "https://api.deepseek.com")


def test_deepseek_reasoning_levels_are_vendor_specific() -> None:
    assert reasoning_levels_for_model("deepseek-v4-pro", "deepseek") == ("high", "xhigh")


def test_deepseek_request_payload_enables_thinking_and_omits_temperature() -> None:
    config = _provider_config(
        "deepseek",
        "https://api.deepseek.com",
        "deepseek-v4-pro",
        "low",
    )

    kwargs = request_kwargs(config, [], tools=None, tool_choice=None)

    assert kwargs["extra_body"] == {"thinking": {"type": "enabled"}}
    assert kwargs["reasoning_effort"] == "high"
    assert "temperature" not in kwargs


def test_deepseek_xhigh_reasoning_maps_to_max_effort() -> None:
    config = _provider_config(
        "deepseek",
        "https://api.deepseek.com",
        "deepseek-v4-pro",
        "xhigh",
    )

    kwargs = request_kwargs(config, [], tools=None, tool_choice=None)

    assert kwargs["extra_body"] == {"thinking": {"type": "enabled"}}
    assert kwargs["reasoning_effort"] == "max"
    assert "temperature" not in kwargs


def test_openai_reasoning_payload_stays_openai_compatible() -> None:
    config = _provider_config(
        "openai",
        "https://api.openai.com/v1",
        "gpt-5.5",
        "high",
    )

    kwargs = request_kwargs(config, [], tools=None, tool_choice=None)

    assert kwargs["reasoning_effort"] == "high"
    assert kwargs["temperature"] == 0.7
    assert "extra_body" not in kwargs


def test_custom_provider_does_not_receive_vendor_reasoning_fields() -> None:
    config = _provider_config(
        "custom",
        "https://example.invalid/v1",
        "gpt-5.5",
        "high",
    )

    kwargs = request_kwargs(config, [], tools=None, tool_choice=None)

    assert "reasoning_effort" not in kwargs
    assert "extra_body" not in kwargs
    assert kwargs["temperature"] == 0.7


def test_openrouter_profile_uses_nested_reasoning_effort_payload() -> None:
    config = _provider_config(
        "openrouter",
        "https://openrouter.ai/api/v1",
        "deepseek/deepseek-r1",
        "medium",
    )
    profile = request_profile_for_config(config)

    payload = reasoning_payload_for_profile(profile, "medium", ("low", "medium", "high"))

    assert payload == {"extra_body": {"reasoning": {"effort": "medium"}}}
