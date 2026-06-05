"""Tests for local harness-attempt learning contracts."""

from __future__ import annotations

from pathlib import Path

from ai.runtime import ChatConfig, Conversation
from hephaion.chat.evidence import ResolvedTurnPlan
from hephaion.chat.session import ChatSession
from hephaion.chat.turn_contract import TurnContract
from hephaion.chat.turn_finalization import TurnFinalizationMixin
from hephaion.learning.actions import AttemptAction
from hephaion.learning.environment import ReplayHephEnv
from hephaion.learning.observation import AttemptObservation
from hephaion.learning.policy import StaticAttemptPolicy
from hephaion.learning.reward import RewardComponent, score_attempt_reward
from hephaion.learning.storage import AttemptRecord, LearningStore, new_attempt_record
from hephaion.rag import Chunk, EvidenceChunk, TurnEvidence
from hephaion.study.policy import EvidenceAssessment


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
    )


def test_attempt_record_serializes_observation_reward_and_evidence() -> None:
    record = _record()

    restored = type(record).from_dict(record.to_dict())

    assert restored is not None
    assert restored.action is AttemptAction.ACCEPT
    assert restored.observation.evidence_count == 1
    assert restored.reward.total == record.reward.total
    assert restored.evidence is not None
    assert restored.evidence.items[0].evidence_id == "E1"


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
    records = (_record(), _record(AttemptAction.RETRY_EXPAND_EVIDENCE))
    first = ReplayHephEnv(records)
    second = ReplayHephEnv(records)

    assert first.reset() == second.reset()
    first_step = first.step(AttemptAction.ACCEPT)
    second_step = second.step(AttemptAction.ACCEPT)

    assert first_step.reward == second_step.reward
    assert not first_step.terminated
    mismatch = first.step(AttemptAction.ACCEPT)
    assert mismatch.reward.total == -0.05
    assert mismatch.terminated


def test_finalized_turn_records_accepted_action_when_policy_would_retry(tmp_path: Path) -> None:
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
    assert record.action is AttemptAction.ACCEPT
    assert record.reward.total < 0


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


def _component_value(components: tuple[RewardComponent, ...], name: str) -> float:
    for component in components:
        if component.name == name:
            return component.value
    raise AssertionError(name)
