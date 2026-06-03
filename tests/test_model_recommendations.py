from __future__ import annotations

import pytest

from hephaion.providers.config import default_config
from hephaion.providers.model_recommendations import recommended_model_choices
from hephaion.providers.registry import get_registry


def test_openai_api_models_are_tagged_for_provider_native_guardrails() -> None:
    info = get_registry().get("gpt-4o-mini", provider="openai")

    assert info is not None
    assert "provider-native-guardrails" in info.tags


def test_model_recommendations_surface_provider_native_guardrails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    config = default_config()

    recommendations = recommended_model_choices(config, query="gpt-4o-mini", limit=3)

    openai_recommendation = next(item for item in recommendations if item.slug == "openai")
    assert "provider-native guardrails" in openai_recommendation.reasons
