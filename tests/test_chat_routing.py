"""Tests for material-chat routing stabilizers."""

from __future__ import annotations

import pytest

from hephaion.chat.orchestrator import _stabilized_intent_for_default_material_plan
from hephaion.chat.turn_contract import (
    RETRIEVAL_STRATEGY_OVERVIEW,
    RETRIEVAL_STRATEGY_RETRIEVE,
    TurnIntentResolution,
)
from hephaion.study import material_overview_plan


@pytest.mark.parametrize("intent", ["", "source_qa"])
def test_contentless_material_query_uses_overview_sampling(intent: str) -> None:
    user_input = "???"
    resolution = TurnIntentResolution(
        intent=intent,
        canonical_request="",
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
        retrieval_query=user_input,
        confidence=0.9,
    )

    stabilized = _stabilized_intent_for_default_material_plan(
        resolution,
        user_input=user_input,
        default_plan=material_overview_plan(user_input, retrieval_query=user_input),
        prior_contract=None,
        index=None,
    )

    assert stabilized.intent == "material_overview"
    assert stabilized.retrieval_strategy == RETRIEVAL_STRATEGY_OVERVIEW
    assert stabilized.retrieval_query == ""
