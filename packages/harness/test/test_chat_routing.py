"""Tests for material-chat routing stabilizers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from ai.runtime import ChatConfig, Conversation
from harness.chat.events import (
    AssistantDeltaEvent,
    GuardrailEvent,
    MaterialOperationEvent,
    ToolResultEvent,
    TurnCompleteEvent,
)
from harness.chat.evidence import ResolvedTurnPlan, assess_turn_evidence
from harness.chat.intent_resolution import (
    _intent_normalization_context,
    _stabilized_followup_intent_resolution,
    _stabilized_intent_for_default_material_plan,
)
from harness.chat.orchestrator import TurnOrchestrator
from harness.chat.session import ChatSession
from harness.chat.turn_contract import (
    RETRIEVAL_STRATEGY_NONE,
    RETRIEVAL_STRATEGY_OVERVIEW,
    RETRIEVAL_STRATEGY_RETRIEVE,
    TurnContract,
    TurnIntentResolution,
)
from harness.chat.turn_planning import (
    _turn_contract_can_seed_followup,
)
from harness.safety import GUARDRAIL_STAGE_INPUT, block_guardrail
from harness.study import (
    LearningTurnPlan,
    material_overview_plan,
    material_topic_presentation_plan,
)
from heph.product.context import heph_product_routing_context


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


def test_drifted_direct_source_request_uses_overview_sampling() -> None:
    user_input = "what topics should I focus on for the exam"
    resolution = TurnIntentResolution(
        intent="source_qa",
        canonical_request=user_input,
        retrieval_strategy=RETRIEVAL_STRATEGY_RETRIEVE,
        retrieval_query="broad corpus contents and themes",
        direct_evidence_required=True,
        confidence=0.98,
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
    assert stabilized.retrieval_query == "broad corpus contents and themes"


def test_intent_context_includes_heph_extension_contract_domain() -> None:
    routing_context = heph_product_routing_context()
    context = _intent_normalization_context(
        "How does the harness store memory?",
        Conversation(),
    )

    assert len(routing_context) <= 360
    assert "Heph self-knowledge routing context:" in context
    assert routing_context in context
    assert "Heph Assistant Atlas" not in context
    assert "Core commands:" not in context
    assert "heph_action performs exact app ops" in context
    assert "Current user request:\nHow does the harness store memory?" in context


def test_heph_help_intent_is_stabilized_as_non_material() -> None:
    resolution = _stabilized_followup_intent_resolution(
        TurnIntentResolution(
            intent="heph_help",
            retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
            retrieval_query="current material overview",
            direct_evidence_required=True,
            prior_answer_positions=(1,),
            prior_answer_position_basis="list_items",
            confidence=0.95,
        ),
        user_input="Explain how this harness works.",
        prior_intent="material_overview",
    )

    assert resolution.intent == "heph_help"
    assert resolution.retrieval_strategy == RETRIEVAL_STRATEGY_NONE
    assert resolution.retrieval_query == ""
    assert resolution.direct_evidence_required is False
    assert resolution.prior_answer_positions == ()
    assert resolution.prior_answer_position_basis == ""


def test_heph_action_intent_is_stabilized_as_non_material() -> None:
    resolution = _stabilized_followup_intent_resolution(
        TurnIntentResolution(
            intent="heph_action",
            retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
            retrieval_query="current material overview",
            direct_evidence_required=True,
            prior_answer_positions=(1,),
            prior_answer_position_basis="list_items",
            confidence=0.95,
        ),
        user_input="Import ~/notes.md into bfi-2.",
        prior_intent="material_overview",
    )

    assert resolution.intent == "heph_action"
    assert resolution.retrieval_strategy == RETRIEVAL_STRATEGY_NONE
    assert resolution.retrieval_query == ""
    assert resolution.direct_evidence_required is False
    assert resolution.prior_answer_positions == ()
    assert resolution.prior_answer_position_basis == ""


def test_heph_help_turn_contract_can_seed_product_followups() -> None:
    contract = TurnContract(
        original_user_input="How does provider setup work?",
        resolved_intent="heph_help",
        retrieval_strategy=RETRIEVAL_STRATEGY_NONE,
    )

    assert _turn_contract_can_seed_followup(contract, visible_evidence=None)


def test_heph_action_turn_contract_can_seed_product_followups() -> None:
    contract = TurnContract(
        original_user_input="Import ~/notes.md into bfi-2.",
        resolved_intent="heph_action",
        retrieval_strategy=RETRIEVAL_STRATEGY_NONE,
    )

    assert _turn_contract_can_seed_followup(contract, visible_evidence=None)


def test_blocked_input_is_not_appended_or_traced(monkeypatch: pytest.MonkeyPatch) -> None:
    session = ChatSession(
        config=ChatConfig(api_key="test-key"),
        conversation=Conversation(),
        session_id="blocked-input-session",
    )
    trace = MagicMock()
    object.__setattr__(session, "trace", trace)
    monkeypatch.setattr(
        "harness.chat.turn_lifecycle.check_user_input",
        lambda *_args, **_kwargs: block_guardrail(GUARDRAIL_STAGE_INPUT, "Input blocked."),
    )

    events = list(TurnOrchestrator(session).iter_events("blocked request"))

    assert isinstance(events[0], GuardrailEvent)
    assert session.conversation.messages == []
    trace.record_user_message.assert_not_called()


def test_armory_heph_help_route_does_not_prepare_material_index() -> None:
    session = ChatSession(
        config=ChatConfig(base_url="https://local.test/v1", model="classifier"),
        conversation=Conversation(),
        session_id="test-session",
        armory_path=Path("/tmp/test-armory"),
    )
    object.__setattr__(session, "trace", MagicMock())
    session.source_file_count = 1
    orchestrator = TurnOrchestrator(session)

    def resolve(plan: LearningTurnPlan) -> ResolvedTurnPlan:
        assert plan.retrieval_query is None
        assert "Execute HEPH_HELP" in plan.prompt
        return ResolvedTurnPlan(
            learning_plan=plan,
            turn_evidence=None,
            evidence_assessment=assess_turn_evidence(plan, None),
        )

    with (
        patch(
            "harness.chat.model_text._model_json_payload",
            return_value={
                "intent": "heph_help",
                "canonical_english_request": (
                    "Explain how the local document harness handles provider setup."
                ),
                "retrieval_strategy": "none",
                "retrieval_query": "",
                "confidence": 0.99,
            },
        ),
        patch("harness.chat.armory_turn._ensure_rag_index") as ensure_index,
        patch.object(TurnOrchestrator, "_resolve_timed_turn_plan", side_effect=resolve),
        patch(
            "harness.chat.turn_execution.iter_agent_events",
            return_value=iter(
                [
                    AssistantDeltaEvent("Use /login or /models to configure providers."),
                    TurnCompleteEvent(
                        "Use /login or /models to configure providers.",
                        0,
                        1.0,
                        "stop",
                        100,
                    ),
                ]
            ),
        ),
        patch("harness.chat.turn_finalization.schedule_memory_extraction"),
        patch("harness.chat.turn_finalization.save_usage"),
    ):
        events = list(orchestrator.iter_events("How do I configure provider access here?"))

    ensure_index.assert_not_called()
    assert not any(isinstance(event, MaterialOperationEvent) for event in events)
    assert session.last_plan_intent == "heph_help"
    assert session.last_turn_contract is not None
    assert session.last_turn_contract.resolved_intent == "heph_help"
    assert session.last_turn_contract.retrieval_strategy == RETRIEVAL_STRATEGY_NONE
    assert session.last_turn_contract.evidence_refs == ()


def test_armory_heph_action_route_uses_narrow_setup_tools(tmp_path: Path) -> None:
    armory = tmp_path / "armory"
    (armory / "materials").mkdir(parents=True)
    (armory / ".harness").mkdir()
    (armory / ".harness" / "armory.toml").write_text("version = 2\n", encoding="utf-8")
    imported = armory / "materials" / "notes.md"
    imported.write_text("imported", encoding="utf-8")
    session = ChatSession(
        config=ChatConfig(base_url="https://local.test/v1", model="classifier"),
        conversation=Conversation(),
        session_id="test-session",
        armory_path=armory,
    )
    object.__setattr__(session, "trace", MagicMock())
    orchestrator = TurnOrchestrator(session)

    def resolve(plan: LearningTurnPlan) -> ResolvedTurnPlan:
        assert plan.retrieval_query is None
        assert plan.retrieval_strategy == RETRIEVAL_STRATEGY_NONE
        assert plan.allow_tools is True
        assert plan.allowed_tool_names == (
            "create_named_armory",
            "import_materials",
            "validate_armory",
            "list_files",
        )
        assert "Execute HEPH_ACTION" in plan.prompt
        return ResolvedTurnPlan(
            learning_plan=plan,
            turn_evidence=None,
            evidence_assessment=assess_turn_evidence(plan, None),
        )

    tool_events = iter(
        [
            ToolResultEvent(
                call_id="call-1",
                name="import_materials",
                content="Imported notes.md",
                summary="Imported notes.md",
                success=True,
                metadata={"refresh_current_armory": True},
            ),
            AssistantDeltaEvent("Imported notes.md into the current armory."),
            TurnCompleteEvent(
                "Imported notes.md into the current armory.",
                0,
                1.0,
                "stop",
                100,
            ),
        ]
    )

    with (
        patch(
            "harness.chat.model_text._model_json_payload",
            return_value={
                "intent": "heph_action",
                "canonical_english_request": "Import notes.md into the current armory.",
                "retrieval_strategy": "none",
                "retrieval_query": "",
                "confidence": 0.99,
            },
        ),
        patch("harness.chat.armory_turn._ensure_rag_index") as ensure_index,
        patch.object(TurnOrchestrator, "_resolve_timed_turn_plan", side_effect=resolve),
        patch("harness.chat.turn_execution.iter_agent_events", return_value=tool_events) as agent,
        patch("harness.chat.turn_finalization.schedule_memory_extraction"),
        patch("harness.chat.turn_finalization.save_usage"),
    ):
        events = list(orchestrator.iter_events("Import notes.md here."))

    ensure_index.assert_not_called()
    assert agent.call_args.kwargs["tool_schemas"] is None
    assert agent.call_args.kwargs["allowed_tool_names"] == (
        "create_named_armory",
        "import_materials",
        "validate_armory",
        "list_files",
    )
    assert not any(isinstance(event, MaterialOperationEvent) for event in events)
    assert session.source_files == ("materials/notes.md",)
    assert session.rag_index is None
    assert session.last_plan_intent == "heph_action"
    assert session.last_turn_contract is not None
    assert session.last_turn_contract.resolved_intent == "heph_action"
    assert session.last_turn_contract.retrieval_strategy == RETRIEVAL_STRATEGY_NONE
    assert session.last_turn_contract.evidence_refs == ()


def test_material_topic_presentation_uses_material_read_tools_only() -> None:
    plan = material_topic_presentation_plan("teach me enzymes", retrieval_query="enzymes")

    assert plan.allow_tools is True
    assert plan.allowed_tool_names == ("search_materials", "open_material")
