"""Tests for providers/model_support: model filtering by provider and endpoint."""

from __future__ import annotations

from heph_ai.providers.model_support import (
    filter_supported_models,
    is_supported_model_for_endpoint,
    is_supported_model_for_provider,
)

# isort: split


# ---------------------------------------------------------------------------
# filter_supported_models
# ---------------------------------------------------------------------------


class TestFilterSupportedModels:
    def test_openrouter_keeps_matching_prefixes(self) -> None:
        models = [
            "openai/gpt-5.4",
            "google/gemini-3-flash-preview",
            "qwen/qwen3-72b",
            "anthropic/claude-sonnet-latest",
            "not-a-provider-model",
        ]
        result = filter_supported_models(models, "openrouter")
        assert "openai/gpt-5.4" in result
        assert "google/gemini-3-flash-preview" in result
        assert "qwen/qwen3-72b" in result
        assert "anthropic/claude-sonnet-latest" in result
        assert "not-a-provider-model" not in result

    def test_openai_codex_keeps_gpt_prefix(self) -> None:
        models = ["gpt-5.4", "gpt-5.4-mini", "glm-5", "random-model"]
        result = filter_supported_models(models, "openai-codex")
        assert result == ["gpt-5.4", "gpt-5.4-mini"]

    def test_openai_api_keeps_openai_model_families(self) -> None:
        models = ["gpt-5.5", "o3", "glm-5", "random-model"]
        result = filter_supported_models(models, "openai")
        assert result == ["gpt-5.5", "o3"]

    def test_zai_keeps_glm_prefix(self) -> None:
        models = ["glm-5", "glm-5-plus", "gpt-5.4", "other"]
        result = filter_supported_models(models, "zai")
        assert result == ["glm-5", "glm-5-plus"]

    def test_unknown_provider_returns_all(self) -> None:
        models = ["anything", "goes", "here"]
        result = filter_supported_models(models, "custom")
        assert result == models

    def test_empty_list(self) -> None:
        assert filter_supported_models([], "openrouter") == []

    def test_pollinations_keeps_matching_prefixes(self) -> None:
        models = [
            "openai",
            "openai-fast",
            "openai-large",
            "mistral",
            "gpt-5.4",
            "glm-5",
        ]
        result = filter_supported_models(models, "pollinations")
        assert result == ["openai", "openai-fast"]


# ---------------------------------------------------------------------------
# is_supported_model_for_provider
# ---------------------------------------------------------------------------


class TestIsSupportedModelForProvider:
    def test_openrouter_matching_prefix(self) -> None:
        assert is_supported_model_for_provider("openai/gpt-5.4", "openrouter") is True

    def test_openrouter_non_matching_prefix(self) -> None:
        assert is_supported_model_for_provider("glm-5", "openrouter") is False

    def test_openai_codex_matching(self) -> None:
        assert is_supported_model_for_provider("gpt-5.4", "openai-codex") is True

    def test_openai_api_matching(self) -> None:
        assert is_supported_model_for_provider("gpt-5.5", "openai") is True

    def test_zai_matching(self) -> None:
        assert is_supported_model_for_provider("glm-5-plus", "zai") is True

    def test_unknown_provider_always_true(self) -> None:
        assert is_supported_model_for_provider("anything", "custom") is True

    def test_empty_model_name(self) -> None:
        assert is_supported_model_for_provider("", "openrouter") is False


# ---------------------------------------------------------------------------
# is_supported_model_for_endpoint
# ---------------------------------------------------------------------------


class TestIsSupportedModelForEndpoint:
    def test_openrouter_endpoint(self) -> None:
        assert (
            is_supported_model_for_endpoint("openai/gpt-5.4", "https://openrouter.ai/api/v1")
            is True
        )
        assert is_supported_model_for_endpoint("glm-5", "https://openrouter.ai/api/v1") is False

    def test_openai_endpoint(self) -> None:
        assert is_supported_model_for_endpoint("gpt-5.5", "https://api.openai.com/v1") is True
        assert is_supported_model_for_endpoint("gpt-5.4", "https://api.openai.com/v1") is True
        assert is_supported_model_for_endpoint("glm-5", "https://api.openai.com/v1") is False

    def test_zai_endpoint(self) -> None:
        assert is_supported_model_for_endpoint("glm-5", "https://api.z.ai/api/paas/v4/") is True
        assert is_supported_model_for_endpoint("gpt-5.4", "https://api.z.ai/api/paas/v4/") is False

    def test_zai_endpoint_without_trailing_slash(self) -> None:
        assert is_supported_model_for_endpoint("glm-5", "https://api.z.ai/api/paas/v4") is True

    def test_unknown_endpoint_always_true(self) -> None:
        assert is_supported_model_for_endpoint("anything", "https://custom.example.com/v1") is True

    def test_endpoint_with_extra_whitespace(self) -> None:
        assert is_supported_model_for_endpoint("gpt-5.4", "  https://api.openai.com/v1  ") is True

    def test_pollinations_endpoint(self) -> None:
        assert (
            is_supported_model_for_endpoint("openai", "https://text.pollinations.ai/openai")
            is True
        )
        assert (
            is_supported_model_for_endpoint("openai-fast", "https://text.pollinations.ai/openai")
            is True
        )
        assert (
            is_supported_model_for_endpoint("openai-large", "https://text.pollinations.ai/openai")
            is False
        )
        assert (
            is_supported_model_for_endpoint("mistral", "https://text.pollinations.ai/openai")
            is False
        )
