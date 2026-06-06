"""Tests for local harness-attempt learning contracts."""

from __future__ import annotations

from pathlib import Path

import pytest
from ai.runtime import ChatConfig, Conversation
from hephaion.chat.evidence import ResolvedTurnPlan
from hephaion.chat.session import ChatSession
from hephaion.chat.turn_contract import TurnContract
from hephaion.chat.turn_finalization import TurnFinalizationMixin
from hephaion.learning.actions import AttemptAction
from hephaion.learning.environment import ReplayHephEnv
from hephaion.learning.observation import AttemptObservation
from hephaion.learning.policy import StaticAttemptPolicy
from hephaion.learning.policy_artifact import (
    PROMOTED_POLICY_FILE,
    PROMOTION_MANIFEST_FILE,
    ExportedPolicyArtifact,
    load_runtime_policy,
    observation_bucket,
    write_exported_policy,
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
    load_records_from_jsonl,
    train_attempt_policy,
)
from hephaion.rag import Chunk, EvidenceChunk, TurnEvidence
from hephaion.study.policy import EvidenceAssessment
from hephaion.study.prompt_plans import LearningTurnPlan
from hephaion.study.state import LearningAction, LearningPhase


class _FinalizationProbe(TurnFinalizationMixin):
    def __init__(self, session: ChatSession) -> None:
        self.session = session
        self.last_reply = "The note says this [E2]."
        self.last_internal_passes = 0
        self._last_reply_citation_required = True


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
    assert _component_value(reward.components, "citation_validity") == -1.0


def test_correct_abstention_receives_positive_reward_for_weak_evidence() -> None:
    observation = AttemptObservation(
        evidence_count=0,
        evidence_sufficient=False,
        evidence_recommended_action="abstain",
        reply_chars=80,
    )

    reward = score_attempt_reward(observation, accepted=False, abstained=True)

    assert reward.total > 0
    assert _component_value(reward.components, "abstention") > 0


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
    assert abstain_step.reward.total > 0
    assert abstain_step.info["final_outcome"] == "abstained"
    assert abstain_step.terminated


def test_public_synthetic_replay_is_labelled_and_reward_based() -> None:
    records = load_records_from_jsonl(PUBLIC_SYNTHETIC_REPLAY)

    assert {_data_origin(record) for record in records} == {
        "public",
        "synthetic",
    }
    first = records[0]
    assert first.action is AttemptAction.RETRY_EXPAND_EVIDENCE
    assert first.outcome_for(AttemptAction.ABSTAIN).reward.total > first.reward.total


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


def test_training_promotes_only_reward_beating_policy_and_runtime_loads_it(
    tmp_path: Path,
) -> None:
    report = train_attempt_policy(
        armory_path=tmp_path,
        dataset_paths=(PUBLIC_SYNTHETIC_REPLAY,),
        include_local=False,
        promote=True,
    )

    assert report.decision == "promote"
    assert report.trained_metrics.average_reward > report.baseline_metrics.average_reward
    assert report.dataset_counts == {"public": 2, "synthetic": 2}
    assert (tmp_path / ".hephaion" / "learning" / "policies" / PROMOTED_POLICY_FILE).is_file()

    records = load_records_from_jsonl(PUBLIC_SYNTHETIC_REPLAY)
    policy = load_runtime_policy(tmp_path)

    assert policy.choose(records[0].observation) is AttemptAction.ABSTAIN


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
    with pytest.raises(ValueError, match="unknown learning backend: puffer"):
        train_attempt_policy(
            armory_path=tmp_path,
            dataset_paths=(PUBLIC_SYNTHETIC_REPLAY,),
            include_local=False,
            backend="puffer",
        )


def test_failed_promotion_clears_existing_runtime_policy(tmp_path: Path) -> None:
    promoted = train_attempt_policy(
        armory_path=tmp_path,
        dataset_paths=(PUBLIC_SYNTHETIC_REPLAY,),
        include_local=False,
        promote=True,
    )
    records = load_records_from_jsonl(PUBLIC_SYNTHETIC_REPLAY)
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

    assert promoted.decision == "promote"
    assert failed.decision == "keep_fallback"
    assert runtime_policy.choose(records[0].observation) is StaticAttemptPolicy().choose(
        records[0].observation
    )


def test_non_promoting_training_preserves_existing_runtime_policy(tmp_path: Path) -> None:
    promoted = train_attempt_policy(
        armory_path=tmp_path,
        dataset_paths=(PUBLIC_SYNTHETIC_REPLAY,),
        include_local=False,
        promote=True,
    )

    report = train_attempt_policy(
        armory_path=tmp_path,
        dataset_paths=(PUBLIC_SYNTHETIC_REPLAY,),
        include_local=False,
        promote=False,
    )
    records = load_records_from_jsonl(PUBLIC_SYNTHETIC_REPLAY)
    runtime_policy = load_runtime_policy(tmp_path)

    assert promoted.decision == "promote"
    assert report.decision == "keep_fallback"
    assert runtime_policy.choose(records[0].observation) is AttemptAction.ABSTAIN


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
