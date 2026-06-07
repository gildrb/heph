"""Tests for local harness-attempt learning contracts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from ai.runtime import ChatConfig, Conversation
from hephaion.agent.citation import VerificationResult
from hephaion.chat.events import AssistantDeltaEvent
from hephaion.chat.evidence import ResolvedTurnPlan
from hephaion.chat.learning_reply import _source_qa_abstain_reply
from hephaion.chat.session import ChatSession
from hephaion.chat.turn_contract import (
    ANSWER_MODE_TRANSFORM_PRIOR,
    RETRIEVAL_STRATEGY_EXPAND_PRIOR,
    RETRIEVAL_STRATEGY_OVERVIEW,
    RETRIEVAL_STRATEGY_REUSE_PRIOR,
    TurnContract,
)
from hephaion.chat.turn_finalization import TurnFinalizationMixin
from hephaion.chat.turn_orchestrator import TurnOrchestrator
from hephaion.chat.turn_outputs import _LearningAgentOutput
from hephaion.learning.actions import AttemptAction
from hephaion.learning.automation import AutoTrainingConfig, maybe_auto_train_attempt_policy
from hephaion.learning.constellation import (
    CONSTELLATION_EXPERIMENTS_PATH,
    export_armory_constellation,
    export_constellation_records,
)
from hephaion.learning.environment import ReplayHephEnv
from hephaion.learning.observation import AttemptObservation, build_attempt_observation
from hephaion.learning.observation_audit import (
    audit_observation_probes,
    randomized_observation_probes,
)
from hephaion.learning.policy import StaticAttemptPolicy
from hephaion.learning.policy_artifact import (
    PROMOTED_POLICY_FILE,
    PROMOTION_MANIFEST_FILE,
    ExportedPolicyArtifact,
    load_runtime_policy,
    observation_bucket,
    write_exported_policy,
)
from hephaion.learning.puffer_backend import (
    masked_observation_features,
    observation_feature_names,
    observation_features,
    randomized_segment_observation,
)
from hephaion.learning.reward import (
    RewardComponent,
    score_action_outcome_reward,
    score_attempt_reward,
)
from hephaion.learning.storage import (
    ActionOutcome,
    AttemptRecord,
    LearningStore,
    ValidationState,
    new_attempt_record,
)
from hephaion.learning.training import (
    PUBLIC_SYNTHETIC_REPLAY,
    PUFFERLIB_BACKEND_NAME,
    _evaluate_actions,
    load_records_from_jsonl,
    train_attempt_policy,
)
from hephaion.rag import Chunk, EvidenceChunk, TurnEvidence
from hephaion.study.policy import EvidenceAssessment
from hephaion.study.prompt_plans import LearningTurnPlan, material_overview_plan
from hephaion.study.state import LearningAction, LearningPhase


class _FinalizationProbe(TurnFinalizationMixin):
    def __init__(self, session: ChatSession) -> None:
        self.session = session
        self.last_reply = "The note says this [E2]."
        self.last_internal_passes = 0
        self._last_reply_citation_required = True
        self._learning_action_override = None
        self._learning_recommended_action_override = None
        self._learning_followup_seed_blocked = False


def test_puffer_backend_import_preserves_process_globals(tmp_path: Path) -> None:
    script = """
from pathlib import Path
import signal
import warnings

warning_filters = list(warnings.filters)
sigint_handler = signal.getsignal(signal.SIGINT)

import_errors = []
def import_from_worker():
    try:
        import hephaion.learning.puffer_backend
    except Exception as exc:
        import_errors.append(repr(exc))

import threading
worker = threading.Thread(target=import_from_worker)
worker.start()
worker.join()
if import_errors:
    raise SystemExit(import_errors[0])
if warnings.filters != warning_filters:
    raise SystemExit("warning filters changed")
if signal.getsignal(signal.SIGINT) != sigint_handler:
    raise SystemExit("sigint handler changed")
if Path("resources").exists():
    raise SystemExit("pufferlib resources leaked into cwd")
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def _chunk(source: str = "notes.md", index: int = 0) -> Chunk:
    return Chunk(
        text="Evidence text",
        source=source,
        index=index,
        char_start=0,
        char_end=13,
    )


def _evidence() -> TurnEvidence:
    return TurnEvidence(
        items=(
            EvidenceChunk(
                evidence_id="E1",
                chunk=_chunk(),
                score=0.9,
                content="Evidence text",
            ),
        ),
        sampled_source_count=1,
        total_source_count=1,
    )


def _turn_evidence_with_content(evidence_id: str, source: str, content: str) -> TurnEvidence:
    return TurnEvidence(
        items=(
            EvidenceChunk(
                evidence_id=evidence_id,
                chunk=Chunk(
                    text=content,
                    source=source,
                    index=0,
                    char_start=0,
                    char_end=len(content),
                ),
                score=0.9,
                content=content,
            ),
        ),
        sampled_source_count=1,
        total_source_count=1,
    )


def _overview_evidence() -> TurnEvidence:
    first = "Sorting procedures compare items and arrange them by key."
    second = "Search trees organize ordered data for lookup operations."
    third = "Counting arguments connect combinations to probability models."
    fourth = "Graph examples describe paths, cycles, and reachability."
    return TurnEvidence(
        items=(
            EvidenceChunk(
                evidence_id="E1",
                chunk=Chunk(
                    text=first,
                    source="materials/algorithms.md",
                    index=0,
                    char_start=0,
                    char_end=len(first),
                ),
                score=1.0,
                content=first,
            ),
            EvidenceChunk(
                evidence_id="E2",
                chunk=Chunk(
                    text=second,
                    source="materials/data-structures.md",
                    index=0,
                    char_start=0,
                    char_end=len(second),
                ),
                score=1.0,
                content=second,
            ),
            EvidenceChunk(
                evidence_id="E3",
                chunk=Chunk(
                    text=third,
                    source="materials/counting.md",
                    index=0,
                    char_start=0,
                    char_end=len(third),
                ),
                score=1.0,
                content=third,
            ),
            EvidenceChunk(
                evidence_id="E4",
                chunk=Chunk(
                    text=fourth,
                    source="materials/graphs.md",
                    index=0,
                    char_start=0,
                    char_end=len(fourth),
                ),
                score=1.0,
                content=fourth,
            ),
        ),
        sampled_source_count=4,
        total_source_count=4,
    )


def _accepted_observation() -> AttemptObservation:
    return AttemptObservation(
        citation_required=True,
        evidence_count=1,
        distinct_source_count=1,
        top_score=0.9,
        evidence_sufficient=True,
        evidence_confidence=0.8,
        evidence_recommended_action="answer",
        has_citations=True,
        citation_count=1,
        all_citations_verified=True,
        reply_chars=120,
        latency_ms=100.0,
    )


def _record(action: AttemptAction = AttemptAction.ACCEPT) -> AttemptRecord:
    observation = _accepted_observation()
    reward = score_attempt_reward(observation, accepted=True, abstained=False)
    return new_attempt_record(
        session_id="session",
        turn_id="session:1",
        action=action,
        observation=observation,
        reward=reward,
        user_input="What does the note say?",
        reply="The note says this [E1].",
        evidence=_evidence(),
        accepted=action is AttemptAction.ACCEPT,
        final_outcome="accepted" if action is AttemptAction.ACCEPT else "retry_succeeded",
        replay_metadata={"data_origin": "local", "dataset_kind": "armory-local"},
    )


def _abstain_record() -> AttemptRecord:
    observation = AttemptObservation(
        attempt_index=1,
        citation_required=True,
        evidence_recommended_action="abstain",
        evidence_confidence=0.9,
        missing_required_citation_count=1,
        reply_chars=0,
    )
    abstain_reward = score_action_outcome_reward(observation, AttemptAction.ABSTAIN)
    retry_reward = score_attempt_reward(observation, accepted=False, abstained=False)
    return new_attempt_record(
        session_id="session",
        turn_id="episode-abstain",
        action=AttemptAction.RETRY_EXPAND_EVIDENCE,
        observation=observation,
        reward=retry_reward,
        user_input="Missing answer?",
        reply="",
        evidence=None,
        final_outcome="retry_failed",
        failed_validation_states=(
            ValidationState(name="evidence_sufficient", passed=False, detail="abstain"),
        ),
        action_outcomes=(
            ActionOutcome(
                action=AttemptAction.RETRY_EXPAND_EVIDENCE,
                observation=observation,
                reward=retry_reward,
                final_outcome="retry_failed",
                attempts=2,
            ),
            ActionOutcome(
                action=AttemptAction.ABSTAIN,
                observation=observation,
                reward=abstain_reward,
                final_outcome="abstained",
                abstained=True,
                attempts=1,
            ),
        ),
        replay_metadata={"data_origin": "synthetic", "dataset_kind": "synthetic"},
    )


def test_reward_orders_grounded_progress_abstain_and_bad_accepts() -> None:
    good = score_attempt_reward(_accepted_observation(), accepted=True, abstained=False)
    partial = score_attempt_reward(
        AttemptObservation(
            citation_required=True,
            evidence_count=1,
            distinct_source_count=1,
            top_score=0.78,
            evidence_sufficient=False,
            evidence_confidence=0.35,
            evidence_recommended_action="abstain",
            has_citations=True,
            citation_count=1,
            all_citations_verified=True,
            answer_relevance_required=True,
            answer_relevance_score=0.55,
            grounded_partial_progress=True,
            reply_chars=190,
        ),
        accepted=True,
        abstained=False,
    )
    neutral_abstain = score_attempt_reward(
        AttemptObservation(
            citation_required=True,
            evidence_count=0,
            evidence_recommended_action="abstain",
            evidence_confidence=0.9,
            reply_chars=76,
        ),
        accepted=False,
        abstained=True,
    )
    unnecessary_abstain = score_attempt_reward(
        _accepted_observation(),
        accepted=False,
        abstained=True,
    )
    bad_accept = score_attempt_reward(
        AttemptObservation(
            citation_required=True,
            evidence_count=1,
            evidence_sufficient=True,
            evidence_recommended_action="answer",
            unsupported_claim_count=1,
            missing_required_citation_count=1,
            reply_chars=170,
        ),
        accepted=True,
        abstained=False,
    )

    assert good.total > partial.total > neutral_abstain.total
    assert neutral_abstain.total > unnecessary_abstain.total > bad_accept.total
    assert _component_value(partial.components, "grounded_partial_progress") > 0


def test_source_qa_abstain_uses_cited_partial_progress_when_evidence_is_relevant() -> None:
    evidence = _turn_evidence_with_content(
        "E1",
        "topic.md",
        "The material lists polynomial functions together with roots and limits.",
    )
    plan = LearningTurnPlan(
        action=LearningAction.SOURCE_QA,
        phase=LearningPhase.PRESENTING,
        prompt="",
        retrieval_query="polynomial functions",
        original_user_input="What does the material say about polynomial functions?",
    )
    resolved = ResolvedTurnPlan(
        learning_plan=plan,
        turn_evidence=evidence,
        evidence_assessment=EvidenceAssessment(
            sufficient=False,
            confidence=0.35,
            supporting_refs=("E1",),
            missing_information=("full direct explanation",),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="abstain",
        ),
    )

    reply = _source_qa_abstain_reply(plan, resolved)

    assert "polynomial functions" in reply
    assert "[E1]" in reply
    assert "fuller direct source explanation" in reply
    assert reply != (
        "The current evidence does not contain a direct source answer for this request."
    )


def test_attempt_record_serializes_observation_reward_and_evidence() -> None:
    record = new_attempt_record(
        session_id="session",
        turn_id="session:1",
        action=AttemptAction.ACCEPT,
        observation=_accepted_observation(),
        reward=score_attempt_reward(_accepted_observation(), accepted=True, abstained=False),
        user_input="What does the note say?",
        reply="The note says this [E1].",
        evidence=_evidence(),
        accepted=True,
        final_outcome="accepted",
        failed_validation_states=(
            ValidationState(name="citation_verified", passed=True, detail=""),
        ),
        replay_metadata={"data_origin": "local"},
    )

    restored = type(record).from_dict(record.to_dict())

    assert restored is not None
    assert restored.schema_version == 2
    assert restored.action is AttemptAction.ACCEPT
    assert restored.observation.evidence_count == 1
    assert restored.reward.total == record.reward.total
    assert restored.evidence is not None
    assert restored.evidence.items[0].evidence_id == "E1"
    assert restored.final_outcome == "accepted"
    assert restored.replay_metadata == {"data_origin": "local"}


def test_learning_store_writes_only_under_armory_learning_tree(tmp_path: Path) -> None:
    store = LearningStore(tmp_path)

    store.append_attempt(_record())

    assert store.attempts_path.is_relative_to(tmp_path / ".hephaion" / "learning")
    assert store.attempts_path.is_file()
    assert store.policies_dir.is_dir()
    assert store.replay_dir.is_dir()
    assert next(store.iter_attempts()).turn_id == "session:1"


def test_unsupported_citations_dominate_reward_negatively() -> None:
    observation = AttemptObservation(
        citation_required=True,
        evidence_count=1,
        evidence_sufficient=True,
        has_citations=True,
        citation_count=1,
        all_citations_verified=False,
        unverified_citation_count=1,
        reply_chars=120,
    )

    reward = score_attempt_reward(observation, accepted=True, abstained=False)

    assert reward.total < 0
    assert _component_value(reward.components, "bad_accept") == -0.85
    assert _component_value(reward.components, "accepted_invalid_or_unverified_citations") < 0


def test_necessary_abstention_is_neutral_for_weak_evidence() -> None:
    observation = AttemptObservation(
        evidence_count=0,
        evidence_sufficient=False,
        evidence_recommended_action="abstain",
        reply_chars=80,
    )

    reward = score_attempt_reward(observation, accepted=False, abstained=True)

    assert reward.total == 0.0
    assert all(component.name != "correct_abstain" for component in reward.components)


def test_observation_audit_core_signals_drive_policy_and_reward() -> None:
    results = audit_observation_probes(seed=41)
    failures = tuple(
        (
            result.probe.name,
            result.chosen_action.value,
            result.probe.expected_action.value,
            result.reward_margin,
            [(score.action.value, score.reward) for score in result.action_rewards[:3]],
        )
        for result in results
        if not result.passed
    )

    assert not failures


def test_observation_audit_randomizes_probe_order_by_seed() -> None:
    first = tuple(probe.name for probe in randomized_observation_probes(seed=41))
    repeated = tuple(probe.name for probe in randomized_observation_probes(seed=41))
    second = tuple(probe.name for probe in randomized_observation_probes(seed=42))

    assert first == repeated
    assert first != second


def test_masked_puffer_features_zero_inactive_observation_slots() -> None:
    probe = next(
        probe
        for probe in randomized_observation_probes(seed=41)
        if probe.name == "bad_answer_shape"
    )
    feature_names = observation_feature_names()
    features = masked_observation_features(probe.observation, probe.active_feature_names)

    for index, name in enumerate(feature_names):
        if name not in probe.active_feature_names:
            assert features[index] == 0.0
    assert features[feature_names.index("answer_shape_failed")] > 0.0
    assert features[feature_names.index("retrieval_strategy_overview")] > 0.0


def test_puffer_features_include_retrieval_strategy_signal() -> None:
    feature_names = observation_feature_names()
    index = feature_names.index("retrieval_strategy_overview")

    assert observation_features(AttemptObservation(retrieval_strategy="overview"))[index] == 1.0
    assert observation_features(AttemptObservation(retrieval_strategy="targeted"))[index] == -1.0


def test_puffer_segment_features_zero_missing_evidence_slots() -> None:
    observation = AttemptObservation(
        evidence_count=5,
        distinct_source_count=3,
        sampled_source_count=3,
        total_source_count=3,
        top_score=0.8,
        evidence_sufficient=True,
        evidence_confidence=0.9,
    )
    visible = randomized_segment_observation(observation, active_segment_count=2)
    feature_names = observation_feature_names()
    features = observation_features(visible)

    assert visible.evidence_count == 2
    assert visible.distinct_source_count == 2
    assert not visible.evidence_sufficient
    assert features[feature_names.index("evidence_segment_1_mask")] == 1.0
    assert features[feature_names.index("evidence_segment_2_mask")] == 1.0
    assert features[feature_names.index("evidence_segment_3_mask")] == 0.0
    assert features[feature_names.index("source_segment_1_mask")] == 1.0
    assert features[feature_names.index("source_segment_3_mask")] == 0.0
    assert features[feature_names.index("evidence_segment_3_score")] == 0.0


def test_off_topic_accepted_answer_is_rewarded_terribly() -> None:
    evidence = _turn_evidence_with_content(
        "E1",
        "exam.md",
        "Only paper notes are allowed during the exam.",
    )
    observation = build_attempt_observation(
        attempt_index=1,
        intent="material_followup",
        answer_mode="reason_from_prior_evidence",
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        citation_required=True,
        evidence=evidence,
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        citation_result=VerificationResult(
            verified=["E1"],
            unverified=[],
            citation_count=1,
            has_citations=True,
            all_verified=True,
            evidence_present=True,
        ),
        reply="Only paper notes are allowed during the exam [E1].",
        latency_ms=10.0,
        internal_passes=1,
        request_text="Explain selection sort and the product rule from the prior topics.",
        answer_relevance_required=True,
    )

    reward = score_attempt_reward(observation, accepted=True, abstained=False)

    assert observation.off_topic_answer
    assert observation.unsupported_claim_count == 1
    assert reward.total < 0
    assert _component_value(reward.components, "bad_accept") == -0.85
    assert _component_value(reward.components, "accepted_off_topic_answer") < 0
    assert StaticAttemptPolicy().choose(observation) is AttemptAction.ABSTAIN


def test_bad_overview_shape_accepted_answer_is_rewarded_terribly() -> None:
    observation = AttemptObservation(
        intent="material_overview",
        retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
        citation_required=True,
        evidence_count=10,
        distinct_source_count=6,
        sampled_source_count=10,
        total_source_count=10,
        top_score=1.0,
        evidence_sufficient=True,
        evidence_confidence=0.95,
        evidence_recommended_action="answer",
        has_citations=True,
        citation_count=6,
        all_citations_verified=True,
        answer_shape_failed=True,
        reply_chars=350,
        latency_ms=9800.0,
        cost_usd=0.002,
        internal_passes=2,
    )

    reward = score_attempt_reward(observation, accepted=True, abstained=False)
    retry_reward = score_action_outcome_reward(
        observation,
        AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER,
    )
    abstain_reward = score_action_outcome_reward(observation, AttemptAction.ABSTAIN)

    assert reward.total <= -0.9
    assert _component_value(reward.components, "bad_accept") == -0.85
    assert _component_value(reward.components, "accepted_bad_answer_shape") < 0
    assert retry_reward.total > abstain_reward.total
    assert StaticAttemptPolicy().choose(observation) is (
        AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER
    )


def test_answer_relevance_scores_cited_evidence_not_uncited_context() -> None:
    evidence = TurnEvidence(
        items=(
            EvidenceChunk(
                evidence_id="E1",
                chunk=Chunk(
                    text="Gegeben sind n Zahlen x1, ...",
                    source="exercise.md",
                    index=0,
                    char_start=0,
                    char_end=27,
                ),
                score=0.9,
                content="Gegeben sind n Zahlen x1, ...",
            ),
            EvidenceChunk(
                evidence_id="E2",
                chunk=Chunk(
                    text=(
                        "The prior overview covers number systems, polynomial properties, "
                        "limits, continuity, sequences, series, extrema, and group theory."
                    ),
                    source="overview.md",
                    index=1,
                    char_start=0,
                    char_end=120,
                ),
                score=0.8,
                content=(
                    "The prior overview covers number systems, polynomial properties, "
                    "limits, continuity, sequences, series, extrema, and group theory."
                ),
            ),
        ),
        sampled_source_count=2,
        total_source_count=2,
    )
    observation = build_attempt_observation(
        attempt_index=1,
        intent="material_followup",
        answer_mode="reason_from_prior_evidence",
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        citation_required=True,
        evidence=evidence,
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E2",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        citation_result=VerificationResult(
            verified=["E1"],
            unverified=[],
            citation_count=1,
            has_citations=True,
            all_verified=True,
            evidence_present=True,
        ),
        reply="Gegeben sind n Zahlen x1, ... [E1]",
        latency_ms=10.0,
        internal_passes=1,
        request_text=(
            "Explain why the prior overview covers number systems, polynomial properties, "
            "limits, continuity, sequences, series, extrema, and group theory."
        ),
        answer_relevance_required=True,
    )

    reward = score_attempt_reward(observation, accepted=True, abstained=False)

    assert observation.off_topic_answer
    assert observation.answer_relevance_score < 0.12
    assert reward.total < 0


def test_answer_relevance_allows_source_backed_paraphrase() -> None:
    evidence = _turn_evidence_with_content(
        "E1",
        "analysis.md",
        "The derivative measures a function's rate of change.",
    )
    observation = build_attempt_observation(
        attempt_index=1,
        intent="material_followup",
        answer_mode="reason_from_prior_evidence",
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        citation_required=True,
        evidence=evidence,
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        citation_result=VerificationResult(
            verified=["E1"],
            unverified=[],
            citation_count=1,
            has_citations=True,
            all_verified=True,
            evidence_present=True,
        ),
        reply="It is the rate of change for a function [E1].",
        latency_ms=10.0,
        internal_passes=1,
        request_text="What does derivative mean?",
        answer_relevance_required=True,
    )

    reward = score_attempt_reward(observation, accepted=True, abstained=False)

    assert not observation.off_topic_answer
    assert observation.answer_relevance_score >= 0.12
    assert reward.total > 0


def test_answer_relevance_rejects_unrelated_reply_with_relevant_citation() -> None:
    evidence = _turn_evidence_with_content(
        "E1",
        "algorithms.md",
        "Selection sort repeatedly selects the smallest remaining item.",
    )
    observation = build_attempt_observation(
        attempt_index=1,
        intent="material_followup",
        answer_mode="reason_from_prior_evidence",
        retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
        citation_required=True,
        evidence=evidence,
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        citation_result=VerificationResult(
            verified=["E1"],
            unverified=[],
            citation_count=1,
            has_citations=True,
            all_verified=True,
            evidence_present=True,
        ),
        reply="Only paper notes are allowed during the exam [E1].",
        latency_ms=10.0,
        internal_passes=1,
        request_text="Explain selection sort.",
        answer_relevance_required=True,
    )

    reward = score_attempt_reward(observation, accepted=True, abstained=False)

    assert observation.off_topic_answer
    assert observation.answer_relevance_score < 0.12
    assert reward.total < 0


def test_replay_environment_is_deterministic_from_saved_records() -> None:
    records = (_record(), _abstain_record())
    first = ReplayHephEnv(records)
    second = ReplayHephEnv(records)

    assert first.reset() == second.reset()
    first_step = first.step(AttemptAction.ACCEPT)
    second_step = second.step(AttemptAction.ACCEPT)

    assert first_step.reward == second_step.reward
    assert not first_step.terminated
    abstain_step = first.step(AttemptAction.ABSTAIN)
    assert abstain_step.reward.total == 0
    assert abstain_step.info["final_outcome"] == "abstained"
    assert abstain_step.terminated


def test_public_synthetic_replay_is_labelled_and_reward_based() -> None:
    records = load_records_from_jsonl(PUBLIC_SYNTHETIC_REPLAY)

    assert {_data_origin(record) for record in records} == {
        "public",
        "synthetic",
    }
    first = records[0]
    partial = records[2]
    no_evidence = records[-1]
    assert first.action is AttemptAction.ACCEPT
    assert partial.observation.grounded_partial_progress
    assert no_evidence.action is AttemptAction.ABSTAIN
    assert no_evidence.outcome_for(AttemptAction.ABSTAIN).reward.total <= 0


def test_trajectory_shaping_rewards_progress_and_penalizes_bad_window() -> None:
    partial_observation = AttemptObservation(
        citation_required=True,
        evidence_count=1,
        distinct_source_count=1,
        evidence_sufficient=False,
        evidence_confidence=0.35,
        evidence_recommended_action="abstain",
        has_citations=True,
        citation_count=1,
        all_citations_verified=True,
        grounded_partial_progress=True,
        reply_chars=160,
    )
    partial_reward = score_attempt_reward(
        partial_observation,
        accepted=True,
        abstained=False,
    )
    good_records = tuple(
        new_attempt_record(
            session_id="trajectory",
            turn_id=f"trajectory:{index}",
            action=AttemptAction.ACCEPT,
            observation=partial_observation,
            reward=partial_reward,
            user_input="What does the material say?",
            reply="The material says this much [E1].",
            evidence=_evidence(),
            accepted=True,
            final_outcome="accepted",
        )
        for index in range(1, 8)
    )
    bad_observation = AttemptObservation(
        citation_required=True,
        evidence_count=1,
        evidence_sufficient=True,
        evidence_recommended_action="answer",
        unsupported_claim_count=1,
        missing_required_citation_count=1,
        reply_chars=170,
    )
    bad_reward = score_attempt_reward(bad_observation, accepted=True, abstained=False)
    bad_window = (
        *good_records[:6],
        new_attempt_record(
            session_id="trajectory",
            turn_id="trajectory:7",
            action=AttemptAction.ACCEPT,
            observation=bad_observation,
            reward=bad_reward,
            user_input="What does the material say?",
            reply="Unsupported answer.",
            evidence=_evidence(),
            accepted=True,
            final_outcome="accepted",
        ),
    )

    good_metrics = _evaluate_actions(
        good_records,
        (AttemptAction.ACCEPT,) * len(good_records),
    )
    bad_metrics = _evaluate_actions(
        bad_window,
        (AttemptAction.ACCEPT,) * len(bad_window),
    )
    unshaped_bad_average = ((partial_reward.total * 6) + bad_reward.total) / 7

    assert good_metrics.average_reward > partial_reward.total
    assert good_metrics.grounded_progress_rate == 1.0
    assert bad_metrics.average_reward < unshaped_bad_average
    assert bad_metrics.bad_accept_rate > 0


def test_constellation_export_writes_puffer_numeric_string_shape(tmp_path: Path) -> None:
    output_path = tmp_path / "resources" / "constellation" / "experiments.json"
    records = (_record(), _abstain_record())

    export = export_constellation_records(records, output_path=output_path, env_name="heph-test")

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    group = payload["heph-test"]
    lengths = {
        key: len(value.split(","))
        for key, value in group.items()
        if isinstance(value, str) and value
    }

    assert export.groups == {"heph-test": 2}
    assert group["agent_steps"] == "1,2"
    assert group["env/score"].split(",")[0] == f"{records[0].reward.total:.6g}"
    assert group["train/learning_rate"] == "0.02,0.02"
    assert "tsne1" in group
    assert "heph/evidence_count" in group
    assert set(lengths.values()) == {2}


def test_constellation_export_reads_armory_learning_attempts(tmp_path: Path) -> None:
    LearningStore(tmp_path).append_attempt(_record())

    export = export_armory_constellation(tmp_path)

    output_path = tmp_path / CONSTELLATION_EXPERIMENTS_PATH
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert export.groups == {tmp_path.name: 1}
    assert export.output_path == output_path
    assert payload[tmp_path.name]["env/perf"]


def test_constellation_export_rejects_symlinked_default_output_dir(tmp_path: Path) -> None:
    LearningStore(tmp_path).append_attempt(_record())
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    (tmp_path / CONSTELLATION_EXPERIMENTS_PATH.parent).symlink_to(
        outside,
        target_is_directory=True,
    )

    with pytest.raises(OSError, match="armory state directory must not be a symlink"):
        export_armory_constellation(tmp_path)

    assert not (outside / CONSTELLATION_EXPERIMENTS_PATH.name).exists()


def test_constellation_export_rejects_empty_records(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="no learning attempts available"):
        export_constellation_records(
            (), output_path=tmp_path / "experiments.json", env_name="heph"
        )


def test_finalized_turn_records_accepted_action_when_policy_would_retry(tmp_path: Path) -> None:
    _write_promoted_policy(tmp_path, table={})
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    probe = _FinalizationProbe(session)
    resolved = ResolvedTurnPlan(
        turn_evidence=_evidence(),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.8,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="What does the note say?",
            resolved_intent="answer note",
            citation_required=True,
        ),
    )

    probe._record_learning_attempt(
        resolved,
        _evidence(),
        user_input="What does the note say?",
        latency_ms=10.0,
    )

    record = next(LearningStore(tmp_path).iter_attempts())

    assert StaticAttemptPolicy().choose(record.observation) is (
        AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER
    )
    assert record.replay_metadata is not None
    assert record.replay_metadata["policy_action"] == (
        AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER.value
    )
    assert record.action is AttemptAction.ACCEPT
    assert record.accepted
    assert record.reward.total < 0
    assert len(record.failed_validation_states) == len(set(record.failed_validation_states))


def test_finalized_turn_applies_promoted_abstain_policy(tmp_path: Path) -> None:
    train_attempt_policy(
        armory_path=tmp_path,
        dataset_paths=(PUBLIC_SYNTHETIC_REPLAY,),
        include_local=False,
        promote=True,
    )
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    probe = _FinalizationProbe(session)
    probe.last_reply = "The current evidence does not contain a direct source answer."
    probe._last_reply_citation_required = False
    resolved = _abstain_resolved_turn()

    probe._record_learning_attempt(
        resolved,
        None,
        user_input="What does the source say about the missing topic?",
        latency_ms=5.0,
    )

    record = next(LearningStore(tmp_path).iter_attempts())

    assert record.action is AttemptAction.ABSTAIN
    assert record.abstained
    assert record.final_outcome == "abstained"


def test_promoted_abstain_replaces_reply_before_learning_persistence(tmp_path: Path) -> None:
    train_attempt_policy(
        armory_path=tmp_path,
        dataset_paths=(PUBLIC_SYNTHETIC_REPLAY,),
        include_local=False,
        promote=True,
    )
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    probe = _FinalizationProbe(session)
    probe.last_reply = "I can answer this without evidence."
    session.conversation.add("user", "What does the source say about the missing topic?")
    session.conversation.add("assistant", probe.last_reply)

    probe._finalize_successful_turn(
        "What does the source say about the missing topic?",
        _abstain_resolved_turn(citation_required=True),
        latency_ms=5.0,
    )

    record = next(LearningStore(tmp_path).iter_attempts())

    assert "does not contain a direct source answer" in probe.last_reply
    assert session.conversation.messages[-1].content == probe.last_reply
    assert record.action is AttemptAction.ABSTAIN
    assert record.replay_metadata is not None
    assert record.replay_metadata["policy_action"] == AttemptAction.ABSTAIN.value


def test_structural_relevance_guard_replaces_off_topic_prior_followup(tmp_path: Path) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    session.conversation.add("user", "What is the material about?")
    session.conversation.add("assistant", "It covers selection sort and the product rule [E1].")
    session.conversation.add("user", "What do these topics mean and do?")
    session.conversation.add("assistant", "Only paper notes are allowed during the exam [E1].")
    probe = _FinalizationProbe(session)
    probe.last_reply = "Only paper notes are allowed during the exam [E1]."
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.SOURCE_QA,
            phase=LearningPhase.PRESENTING,
            prompt="",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "exam.md",
            "Only paper notes are allowed during the exam.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="What do these topics mean and do?",
            resolved_intent="material_overview",
            canonical_request="Explain selection sort and the product rule.",
            retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
            retrieval_query="selection sort product rule",
            citation_required=True,
            prior_answer_reference=True,
            prior_answer_excerpt="It covers selection sort and the product rule.",
        ),
    )
    session.last_turn_evidence = resolved.turn_evidence

    probe._finalize_successful_turn(
        "What do these topics mean and do?",
        resolved,
        latency_ms=10.0,
    )
    record = next(LearningStore(tmp_path).iter_attempts())

    assert "does not contain a direct source answer" in probe.last_reply
    assert "paper notes" not in session.conversation.messages[-1].content
    assert session.last_turn_evidence is None
    assert session.last_turn_contract is None
    assert record.action is AttemptAction.ABSTAIN
    assert record.observation.off_topic_answer
    assert record.reward.total <= 0
    assert any(
        state.name == "answer_relevance" and not state.passed
        for state in record.failed_validation_states
    )


def test_finalized_material_overview_records_bad_answer_shape(tmp_path: Path) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    reply = (
        "The material is mainly about computing concepts, especially: 1. "
        "**Algorithms** such as sorting and lookup procedures [E1][E2]\n\n"
        "2. **Discrete structures**, including counting arguments and graph examples [E3][E4]."
    )
    session.conversation.add("user", "What is the material about?")
    session.conversation.add("assistant", reply)
    probe = _FinalizationProbe(session)
    probe.last_reply = reply
    evidence = _overview_evidence()
    resolved = ResolvedTurnPlan(
        learning_plan=material_overview_plan("What is the material about?"),
        turn_evidence=evidence,
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.95,
            supporting_refs=("E1", "E2", "E3", "E4"),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="What is the material about?",
            resolved_intent="material_overview",
            canonical_request="Give a compact overview of the material corpus.",
            retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
            citation_required=True,
        ),
    )

    probe._finalize_successful_turn("What is the material about?", resolved, latency_ms=10.0)
    record = next(LearningStore(tmp_path).iter_attempts())

    assert record.action is AttemptAction.ACCEPT
    assert record.observation.answer_shape_failed
    assert record.reward.total < 0
    assert any(
        state.name == "answer_shape" and not state.passed
        for state in record.failed_validation_states
    )
    assert record.replay_metadata is not None
    assert record.replay_metadata["policy_action"] == (
        AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER.value
    )


def test_structural_relevance_guard_does_not_seed_rejected_prior_transform(
    tmp_path: Path,
) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    session.conversation.add("user", "What is the material about?")
    session.conversation.add("assistant", "It covers selection sort and the product rule [E1].")
    session.conversation.add("user", "What does that mean?")
    session.conversation.add("assistant", "Only paper notes are allowed during the exam [E1].")
    probe = _FinalizationProbe(session)
    probe.last_reply = "Only paper notes are allowed during the exam [E1]."
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.SOURCE_QA,
            phase=LearningPhase.PRESENTING,
            prompt="",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "exam.md",
            "Only paper notes are allowed during the exam.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="What does that mean?",
            resolved_intent="material_followup",
            canonical_request="Explain selection sort and the product rule in simpler terms.",
            retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
            retrieval_query="",
            citation_required=True,
            prior_answer_reference=True,
            prior_answer_excerpt="It covers selection sort and the product rule.",
            answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
        ),
    )
    session.last_turn_evidence = resolved.turn_evidence

    probe._finalize_successful_turn("What does that mean?", resolved, latency_ms=10.0)

    assert "does not contain a direct source answer" in probe.last_reply
    assert session.last_turn_evidence is None
    assert session.last_turn_contract is None
    assert session.turn_history[-1].evidence is None
    assert session.turn_history[-1].contract is None


def test_structural_validation_guard_replaces_uncited_required_answer(
    tmp_path: Path,
) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    session.conversation.add("user", "What is the material about?")
    session.conversation.add(
        "assistant",
        "I could not produce a grounded material overview from the current model output.",
    )
    probe = _FinalizationProbe(session)
    probe.last_reply = "I could not produce a grounded material overview from the current output."
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.PRIORITY,
            phase=LearningPhase.PRESENTING,
            prompt="",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "overview.md",
            "The material covers polynomial roots and continuity.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="What is the material about?",
            resolved_intent="material_overview",
            canonical_request="Provide a compact overview of the material contents.",
            retrieval_strategy=RETRIEVAL_STRATEGY_OVERVIEW,
            citation_required=True,
        ),
    )
    session.last_turn_evidence = resolved.turn_evidence

    probe._finalize_successful_turn(
        "What is the material about?",
        resolved,
        latency_ms=10.0,
    )
    record = next(LearningStore(tmp_path).iter_attempts())

    assert "verifiable citations" in probe.last_reply
    assert session.last_turn_evidence is None
    assert session.last_turn_contract is None
    assert record.action is AttemptAction.ABSTAIN
    assert record.replay_metadata["policy_action"] == (
        AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER.value
    )
    assert any(
        state.name == "citation_present" and not state.passed
        for state in record.failed_validation_states
    )


def test_structural_validation_guard_is_not_overwritten_by_relevance_guard(
    tmp_path: Path,
) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    session.conversation.add("user", "Explain selection sort.")
    session.conversation.add("assistant", "Selection sort selects the smallest item [E1].")
    session.conversation.add("user", "What does that mean?")
    probe = _FinalizationProbe(session)
    probe.last_reply = "Selection sort repeatedly picks the smallest remaining item."
    session.conversation.add("assistant", probe.last_reply)
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.SOURCE_QA,
            phase=LearningPhase.PRESENTING,
            prompt="",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "sorting.md",
            "Selection sort repeatedly selects the smallest remaining item.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="What does that mean?",
            resolved_intent="material_followup",
            canonical_request="Explain selection sort in simpler terms.",
            retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
            retrieval_query="selection sort",
            citation_required=True,
            prior_answer_reference=True,
        ),
    )

    probe._finalize_successful_turn("What does that mean?", resolved, latency_ms=10.0)
    record = next(LearningStore(tmp_path).iter_attempts())

    assert "verifiable citations" in probe.last_reply
    assert "does not contain a direct source answer" not in probe.last_reply
    assert session.conversation.messages[-1].content == probe.last_reply
    assert record.action is AttemptAction.ABSTAIN
    assert record.replay_metadata is not None
    assert record.replay_metadata["policy_action"] == (
        AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER.value
    )
    assert any(
        state.name == "citation_present" and not state.passed
        for state in record.failed_validation_states
    )


def test_structural_relevance_guard_replaces_reply_before_emit(tmp_path: Path) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    session.conversation.add("user", "What is the material about?")
    session.conversation.add("assistant", "It covers selection sort and the product rule [E1].")
    session.conversation.add("user", "What do these topics mean and do?")
    bad_reply = "Only paper notes are allowed during the exam [E1]."
    orchestrator = TurnOrchestrator(session)
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.SOURCE_QA,
            phase=LearningPhase.PRESENTING,
            prompt="",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "exam.md",
            "Only paper notes are allowed during the exam.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="What do these topics mean and do?",
            resolved_intent="material_overview",
            canonical_request="Explain selection sort and the product rule.",
            retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
            retrieval_query="selection sort product rule",
            citation_required=True,
            prior_answer_reference=True,
        ),
    )

    events = list(
        orchestrator._iter_agent_learning_reply_events(
            _LearningAgentOutput(
                streamed_reply=bad_reply,
                raw_reply=bad_reply,
                visible_reply=bad_reply,
                completion_event=None,
            ),
            resolved,
            session.learning_state.clone(),
            user_input="What do these topics mean and do?",
        )
    )

    first_delta = next(event for event in events if isinstance(event, AssistantDeltaEvent))
    assert "does not contain a direct source answer" in first_delta.delta
    assert "paper notes" not in first_delta.delta
    assert session.conversation.messages[-1].content == first_delta.delta


def test_structural_relevance_guard_keeps_learning_state_on_rewrite(
    tmp_path: Path,
) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    original_state = session.learning_state.clone()
    session.conversation.add("user", "Teach me selection sort.")
    bad_reply = "Only paper notes are allowed during the exam [E1]."
    orchestrator = TurnOrchestrator(session)
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.PRESENT,
            phase=LearningPhase.PRESENTING,
            prompt="",
            retrieval_query="selection sort",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "exam.md",
            "Only paper notes are allowed during the exam.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="Teach me selection sort.",
            resolved_intent="topic_presentation",
            canonical_request="Teach selection sort.",
            retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
            retrieval_query="selection sort",
            citation_required=True,
        ),
    )

    events = list(
        orchestrator._iter_agent_learning_reply_events(
            _LearningAgentOutput(
                streamed_reply=bad_reply,
                raw_reply=bad_reply,
                visible_reply=bad_reply,
                completion_event=None,
            ),
            resolved,
            original_state,
            user_input="Teach me selection sort.",
        )
    )

    first_delta = next(event for event in events if isinstance(event, AssistantDeltaEvent))
    assert "does not contain a direct source answer" in first_delta.delta
    assert session.learning_state.to_dict() == original_state.to_dict()


def test_structural_relevance_guard_allows_concise_prior_transform(tmp_path: Path) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    long_prior = " ".join(
        (
            "selection sort product rule continuity sequences series extrema group theory",
            "number systems polynomial roots limits subgroups cyclic groups definitions",
        )
        * 12
    )
    session.conversation.add("user", "What is the material about?")
    session.conversation.add("assistant", f"{long_prior} [E1].")
    session.conversation.add("user", "Rewrite selection sort in one sentence.")
    concise_reply = "Selection sort repeatedly selects the smallest remaining item [E1]."
    session.conversation.add("assistant", concise_reply)
    probe = _FinalizationProbe(session)
    probe.last_reply = concise_reply
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.SOURCE_QA,
            phase=LearningPhase.PRESENTING,
            prompt="",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "overview.md",
            "Selection sort repeatedly selects the smallest remaining item.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="Rewrite selection sort in one sentence.",
            resolved_intent="material_followup",
            canonical_request="Rewrite selection sort as one sentence.",
            retrieval_strategy=RETRIEVAL_STRATEGY_EXPAND_PRIOR,
            retrieval_query="selection sort",
            citation_required=True,
            prior_answer_reference=True,
            prior_answer_excerpt=long_prior,
        ),
    )

    probe._finalize_successful_turn(
        "Rewrite selection sort in one sentence.",
        resolved,
        latency_ms=10.0,
    )
    record = next(LearningStore(tmp_path).iter_attempts())

    assert probe.last_reply == concise_reply
    assert record.action is AttemptAction.ACCEPT
    assert not record.observation.off_topic_answer
    assert record.reward.total > 0


def test_structural_relevance_guard_allows_vague_prior_transform(tmp_path: Path) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    prior_reply = "Selection sort repeatedly selects the smallest remaining item [E1]."
    session.conversation.add("user", "What is selection sort?")
    session.conversation.add("assistant", prior_reply)
    session.conversation.add("user", "What does that mean?")
    concise_reply = "Selection sort repeatedly picks the smallest remaining item [E1]."
    session.conversation.add("assistant", concise_reply)
    probe = _FinalizationProbe(session)
    probe.last_reply = concise_reply
    resolved = ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.SOURCE_QA,
            phase=LearningPhase.PRESENTING,
            prompt="",
        ),
        turn_evidence=_turn_evidence_with_content(
            "E1",
            "overview.md",
            "Selection sort repeatedly selects the smallest remaining item.",
        ),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.9,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="What does that mean?",
            resolved_intent="material_followup",
            canonical_request="Explain the prior answer in simpler terms.",
            answer_mode=ANSWER_MODE_TRANSFORM_PRIOR,
            retrieval_strategy=RETRIEVAL_STRATEGY_REUSE_PRIOR,
            citation_required=True,
            prior_answer_reference=True,
            prior_answer_excerpt=prior_reply,
        ),
    )

    probe._finalize_successful_turn("What does that mean?", resolved, latency_ms=10.0)
    record = next(LearningStore(tmp_path).iter_attempts())

    assert probe.last_reply == concise_reply
    assert record.action is AttemptAction.ACCEPT
    assert not record.observation.off_topic_answer
    assert record.observation.answer_relevance_score >= 0.12


def test_learning_attempt_records_turn_cost_delta(tmp_path: Path) -> None:
    session = ChatSession(
        config=ChatConfig(),
        conversation=Conversation(),
        session_id="session",
        armory_path=tmp_path,
    )
    probe = _FinalizationProbe(session)
    resolved = _accepted_resolved_turn()

    session.usage.total_cost_usd = 0.03
    probe._record_learning_attempt(
        resolved,
        _evidence(),
        user_input="What does the note say?",
        latency_ms=10.0,
    )
    session.usage.total_cost_usd = 0.05
    probe._record_learning_attempt(
        resolved,
        _evidence(),
        user_input="What else does the note say?",
        latency_ms=10.0,
    )

    records = list(LearningStore(tmp_path).iter_attempts())

    assert records[0].cost_usd == 0.03
    assert records[1].cost_usd == 0.02


def test_static_policy_chooses_retry_action_for_failed_citation_validation() -> None:
    observation = AttemptObservation(
        citation_required=True,
        evidence_count=1,
        evidence_sufficient=True,
        has_citations=True,
        citation_count=1,
        all_citations_verified=False,
        unverified_citation_count=1,
        reply_chars=120,
    )

    action = StaticAttemptPolicy().choose(observation)

    assert action is AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER


def test_training_promotes_when_trained_policy_beats_static_on_balanced_fixture(
    tmp_path: Path,
) -> None:
    report = train_attempt_policy(
        armory_path=tmp_path,
        dataset_paths=(PUBLIC_SYNTHETIC_REPLAY,),
        include_local=False,
        promote=True,
    )

    assert report.decision == "promote"
    assert report.backend == PUFFERLIB_BACKEND_NAME
    assert report.trained_metrics.average_reward > report.baseline_metrics.average_reward
    assert report.reasons == ()
    manifest = json.loads(report.manifest_path.read_text(encoding="utf-8"))
    assert manifest["backend_metadata"]["algorithm"] == "ppo"
    assert manifest["backend_metadata"]["trainer"] == "pufferlib.pufferl.PuffeRL"
    assert manifest["backend_metadata"]["export"] == "ppo_reward_checked_bucket_table"
    assert report.dataset_counts == {"public": 3, "synthetic": 5}
    assert manifest["trajectory_window_size"] == 7
    assert report.artifact_path.is_file()
    assert (tmp_path / ".hephaion" / "learning" / "policies" / PROMOTED_POLICY_FILE).exists()

    records = load_records_from_jsonl(PUBLIC_SYNTHETIC_REPLAY)
    policy = load_runtime_policy(tmp_path)

    assert policy.choose(records[0].observation) is AttemptAction.ACCEPT


def test_training_keeps_fallback_when_promote_gate_fails(tmp_path: Path) -> None:
    record = _record()
    LearningStore(tmp_path).append_attempt(record)
    empty_dataset = tmp_path / "empty.jsonl"
    empty_dataset.write_text("", encoding="utf-8")

    report = train_attempt_policy(
        armory_path=tmp_path,
        dataset_paths=(empty_dataset,),
        include_local=True,
        promote=True,
    )

    assert report.decision == "keep_fallback"
    assert not (tmp_path / ".hephaion" / "learning" / "policies" / PROMOTED_POLICY_FILE).exists()


def test_training_rejects_missing_explicit_dataset(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="learning replay dataset not found"):
        train_attempt_policy(
            armory_path=tmp_path,
            dataset_paths=(tmp_path / "missing.jsonl",),
            include_local=False,
            promote=True,
        )


def test_training_rejects_unknown_backend(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown learning backend: mystery"):
        train_attempt_policy(
            armory_path=tmp_path,
            dataset_paths=(PUBLIC_SYNTHETIC_REPLAY,),
            include_local=False,
            backend="mystery",
        )


def test_pufferlib_training_smoke_trains_exports_loads_and_infers(tmp_path: Path) -> None:
    report = train_attempt_policy(
        armory_path=tmp_path,
        dataset_paths=(PUBLIC_SYNTHETIC_REPLAY,),
        include_local=False,
        backend=PUFFERLIB_BACKEND_NAME,
        promote=True,
    )
    records = load_records_from_jsonl(PUBLIC_SYNTHETIC_REPLAY)
    loaded_policy = load_runtime_policy(tmp_path)

    assert report.decision == "promote"
    assert report.backend == PUFFERLIB_BACKEND_NAME
    assert report.artifact_path.is_file()
    assert report.reasons == ()
    assert loaded_policy.choose(records[0].observation) is AttemptAction.ACCEPT


def test_training_rejects_symlinked_policies_dir(tmp_path: Path) -> None:
    store = LearningStore(tmp_path)
    store.root.mkdir(parents=True)
    outside = tmp_path / "outside-policies"
    outside.mkdir()
    try:
        store.policies_dir.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are not supported on this filesystem")

    with pytest.raises(OSError, match="must not be a symlink"):
        train_attempt_policy(
            armory_path=tmp_path,
            dataset_paths=(PUBLIC_SYNTHETIC_REPLAY,),
            include_local=False,
            backend=PUFFERLIB_BACKEND_NAME,
            promote=True,
        )

    assert list(outside.iterdir()) == []


def test_auto_training_waits_for_enough_local_attempts(tmp_path: Path) -> None:
    LearningStore(tmp_path).append_attempt(_record())

    decision = maybe_auto_train_attempt_policy(
        tmp_path,
        config=AutoTrainingConfig(min_total_attempts=2, min_new_attempts=1),
    )

    assert decision.status == "skipped"
    assert decision.reason == "not enough local attempts"
    assert not LearningStore(tmp_path).automation_state_path.exists()


def test_auto_training_runs_once_for_new_attempt_digest(tmp_path: Path) -> None:
    LearningStore(tmp_path).append_attempt(_record())

    first = maybe_auto_train_attempt_policy(
        tmp_path,
        config=AutoTrainingConfig(min_total_attempts=1, min_new_attempts=1),
    )
    second = maybe_auto_train_attempt_policy(
        tmp_path,
        config=AutoTrainingConfig(min_total_attempts=1, min_new_attempts=1),
    )

    store = LearningStore(tmp_path)
    assert first.status == "trained"
    assert first.report is not None
    assert first.report.backend == PUFFERLIB_BACKEND_NAME
    assert store.automation_state_path.is_file()
    assert store.automation_events_path.is_file()
    event_text = store.automation_events_path.read_text(encoding="utf-8")
    assert str(tmp_path) not in event_text
    assert "artifact_path" not in event_text
    assert "manifest_path" not in event_text
    assert second.status == "skipped"
    assert second.reason == "local attempts unchanged"


def test_auto_training_rejects_symlinked_state_file(tmp_path: Path) -> None:
    store = LearningStore(tmp_path)
    store.append_attempt(_record())
    outside = tmp_path / "outside-state.json"
    outside.write_text("outside\n", encoding="utf-8")
    try:
        store.automation_state_path.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are not supported on this filesystem")

    with pytest.raises(OSError, match="must not be a symlink"):
        maybe_auto_train_attempt_policy(
            tmp_path,
            config=AutoTrainingConfig(min_total_attempts=1, min_new_attempts=1),
        )

    assert outside.read_text(encoding="utf-8") == "outside\n"


def test_auto_training_rejects_valid_symlinked_state_before_skip(
    tmp_path: Path,
) -> None:
    store = LearningStore(tmp_path)
    store.append_attempt(_record())
    config = AutoTrainingConfig(min_total_attempts=1, min_new_attempts=1)
    first = maybe_auto_train_attempt_policy(tmp_path, config=config)
    assert first.status == "trained"

    outside = tmp_path / "outside-state.json"
    outside.write_text(store.automation_state_path.read_text(encoding="utf-8"), encoding="utf-8")
    store.automation_state_path.unlink()
    try:
        store.automation_state_path.symlink_to(outside)
    except OSError:
        pytest.skip("symlinks are not supported on this filesystem")

    with pytest.raises(OSError, match="must not be a symlink"):
        maybe_auto_train_attempt_policy(tmp_path, config=config)


def test_auto_training_no_public_fixture_uses_local_records_only(tmp_path: Path) -> None:
    LearningStore(tmp_path).append_attempt(_record())

    decision = maybe_auto_train_attempt_policy(
        tmp_path,
        config=AutoTrainingConfig(
            min_total_attempts=1,
            min_new_attempts=1,
            include_public_fixture=False,
        ),
    )

    assert decision.status == "trained"
    assert decision.report is not None
    assert decision.report.dataset_counts == {"local": 1}


def test_auto_training_retrains_when_corpus_config_changes(tmp_path: Path) -> None:
    LearningStore(tmp_path).append_attempt(_record())

    first = maybe_auto_train_attempt_policy(
        tmp_path,
        config=AutoTrainingConfig(min_total_attempts=1, min_new_attempts=1),
    )
    second = maybe_auto_train_attempt_policy(
        tmp_path,
        config=AutoTrainingConfig(
            min_total_attempts=1,
            min_new_attempts=1,
            include_public_fixture=False,
        ),
    )

    assert first.status == "trained"
    assert second.status == "trained"
    assert second.report is not None
    assert second.report.dataset_counts == {"local": 1}


def test_auto_training_failed_promotion_preserves_existing_runtime_policy(
    tmp_path: Path,
) -> None:
    records = load_records_from_jsonl(PUBLIC_SYNTHETIC_REPLAY)
    _write_promoted_policy(
        tmp_path,
        table={observation_bucket(records[0].observation): AttemptAction.ACCEPT},
    )
    LearningStore(tmp_path).append_attempt(_record())

    decision = maybe_auto_train_attempt_policy(
        tmp_path,
        config=AutoTrainingConfig(
            min_total_attempts=1,
            min_new_attempts=1,
            include_public_fixture=False,
        ),
    )
    runtime_policy = load_runtime_policy(tmp_path)

    assert decision.report is not None
    assert decision.report.decision == "keep_fallback"
    assert runtime_policy.choose(records[0].observation) is AttemptAction.ACCEPT


def test_failed_promotion_clears_existing_runtime_policy(tmp_path: Path) -> None:
    records = load_records_from_jsonl(PUBLIC_SYNTHETIC_REPLAY)
    _write_promoted_policy(
        tmp_path,
        table={observation_bucket(records[3].observation): AttemptAction.ACCEPT},
    )
    empty_dataset = tmp_path / "empty.jsonl"
    empty_dataset.write_text("", encoding="utf-8")
    LearningStore(tmp_path).append_attempt(_record())

    failed = train_attempt_policy(
        armory_path=tmp_path,
        dataset_paths=(empty_dataset,),
        include_local=True,
        promote=True,
    )
    runtime_policy = load_runtime_policy(tmp_path)

    assert failed.decision == "keep_fallback"
    assert runtime_policy.choose(records[3].observation) is StaticAttemptPolicy().choose(
        records[3].observation
    )


def test_non_promoting_training_preserves_existing_runtime_policy(tmp_path: Path) -> None:
    records = load_records_from_jsonl(PUBLIC_SYNTHETIC_REPLAY)
    _write_promoted_policy(
        tmp_path,
        table={observation_bucket(records[3].observation): AttemptAction.ACCEPT},
    )

    report = train_attempt_policy(
        armory_path=tmp_path,
        dataset_paths=(PUBLIC_SYNTHETIC_REPLAY,),
        include_local=False,
        promote=False,
    )
    runtime_policy = load_runtime_policy(tmp_path)

    assert report.decision == "keep_fallback"
    assert runtime_policy.choose(records[3].observation) is AttemptAction.ACCEPT


def test_runtime_policy_reads_legacy_bucket_keys(tmp_path: Path) -> None:
    observation = AttemptObservation(
        citation_required=True,
        evidence_count=3,
        distinct_source_count=1,
        evidence_sufficient=True,
        evidence_recommended_action="answer",
        has_citations=True,
        all_citations_verified=True,
        reply_chars=80,
    )
    _write_promoted_policy(
        tmp_path,
        table={
            "citation_ok|evidence_ok|single_source|normal|targeted": (
                AttemptAction.RETRY_EXPAND_EVIDENCE
            )
        },
    )
    runtime_policy = load_runtime_policy(tmp_path)

    assert runtime_policy.choose(observation) is AttemptAction.RETRY_EXPAND_EVIDENCE


def test_observation_bucket_is_structural_not_textual() -> None:
    first = AttemptObservation(
        citation_required=True,
        evidence_count=0,
        evidence_recommended_action="abstain",
    )
    second = AttemptObservation(
        citation_required=True,
        evidence_count=0,
        evidence_recommended_action="abstain",
        intent="different words",
    )

    assert observation_bucket(first) == observation_bucket(second)


def _component_value(components: tuple[RewardComponent, ...], name: str) -> float:
    for component in components:
        if component.name == name:
            return component.value
    raise AssertionError(name)


def _data_origin(record: AttemptRecord) -> object:
    assert record.replay_metadata is not None
    return record.replay_metadata["data_origin"]


def _write_promoted_policy(
    armory_path: Path,
    *,
    table: dict[str, AttemptAction],
) -> None:
    policies_dir = LearningStore(armory_path).policies_dir
    artifact = ExportedPolicyArtifact(
        policy_id="test-policy",
        created_at="2026-06-06T00:00:00+00:00",
        table=table,
        manifest={"decision": "promote", "policy_id": "test-policy"},
    )
    write_exported_policy(policies_dir / PROMOTED_POLICY_FILE, artifact)
    (policies_dir / PROMOTION_MANIFEST_FILE).write_text(
        '{"decision":"promote","policy_id":"test-policy"}\n',
        encoding="utf-8",
    )


def _accepted_resolved_turn() -> ResolvedTurnPlan:
    return ResolvedTurnPlan(
        turn_evidence=_evidence(),
        evidence_assessment=EvidenceAssessment(
            sufficient=True,
            confidence=0.8,
            supporting_refs=("E1",),
            missing_information=(),
            conflicts=(),
            source_diversity_score=1.0,
            recommended_action="answer",
        ),
        turn_contract=TurnContract(
            original_user_input="What does the note say?",
            resolved_intent="answer note",
            citation_required=True,
        ),
    )


def _abstain_resolved_turn(*, citation_required: bool = False) -> ResolvedTurnPlan:
    return ResolvedTurnPlan(
        learning_plan=LearningTurnPlan(
            action=LearningAction.SOURCE_QA,
            phase=LearningPhase.PRESENTING,
            prompt="",
        ),
        turn_evidence=None,
        evidence_assessment=EvidenceAssessment(
            sufficient=False,
            confidence=0.9,
            supporting_refs=(),
            missing_information=("missing topic",),
            conflicts=(),
            source_diversity_score=0.0,
            recommended_action="abstain",
        ),
        turn_contract=TurnContract(
            original_user_input="What does the source say about the missing topic?",
            resolved_intent="fixture abstention",
            citation_required=citation_required,
        ),
    )
