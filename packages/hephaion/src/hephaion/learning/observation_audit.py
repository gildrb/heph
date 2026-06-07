"""Observation signal diagnostics for local attempt-policy learning."""

from __future__ import annotations

import random
from dataclasses import dataclass

from hephaion.learning.actions import AttemptAction
from hephaion.learning.observation import AttemptObservation
from hephaion.learning.policy import StaticAttemptPolicy
from hephaion.learning.reward import score_action_outcome_reward

OBSERVATION_AUDIT_SEED = 13


@dataclass(frozen=True, slots=True)
class ObservationProbe:
    name: str
    observation: AttemptObservation
    expected_action: AttemptAction
    active_feature_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ActionRewardScore:
    action: AttemptAction
    reward: float


@dataclass(frozen=True, slots=True)
class ObservationAuditResult:
    probe: ObservationProbe
    chosen_action: AttemptAction
    expected_reward: float
    best_competing_reward: float
    action_rewards: tuple[ActionRewardScore, ...]

    @property
    def reward_margin(self) -> float:
        return round(self.expected_reward - self.best_competing_reward, 4)

    @property
    def passed(self) -> bool:
        return self.chosen_action is self.probe.expected_action and self.reward_margin > 0


def randomized_observation_probes(
    *,
    seed: int = OBSERVATION_AUDIT_SEED,
) -> tuple[ObservationProbe, ...]:
    """Return core observation probes in deterministic randomized order."""

    probes = list(_OBSERVATION_PROBES)
    random.Random(seed).shuffle(probes)
    return tuple(probes)


def audit_observation_probes(
    *,
    seed: int = OBSERVATION_AUDIT_SEED,
) -> tuple[ObservationAuditResult, ...]:
    """Check that core observations drive policy and reward in the expected direction."""

    policy = StaticAttemptPolicy()
    return tuple(
        _audit_observation_probe(probe, policy=policy)
        for probe in randomized_observation_probes(seed=seed)
    )


def _audit_observation_probe(
    probe: ObservationProbe,
    *,
    policy: StaticAttemptPolicy,
) -> ObservationAuditResult:
    action_rewards = tuple(
        ActionRewardScore(
            action=action,
            reward=score_action_outcome_reward(probe.observation, action).total,
        )
        for action in AttemptAction
    )
    expected_reward = _reward_for_action(action_rewards, probe.expected_action)
    competing_rewards = tuple(
        score.reward for score in action_rewards if score.action is not probe.expected_action
    )
    return ObservationAuditResult(
        probe=probe,
        chosen_action=policy.choose(probe.observation),
        expected_reward=expected_reward,
        best_competing_reward=max(competing_rewards, default=-1.0),
        action_rewards=tuple(
            sorted(
                action_rewards, key=lambda score: (score.reward, score.action.value), reverse=True
            )
        ),
    )


def _reward_for_action(
    action_rewards: tuple[ActionRewardScore, ...],
    action: AttemptAction,
) -> float:
    for score in action_rewards:
        if score.action is action:
            return score.reward
    return -1.0


_OBSERVATION_PROBES: tuple[ObservationProbe, ...] = (
    ObservationProbe(
        name="grounded_answer",
        observation=AttemptObservation(
            citation_required=True,
            evidence_count=1,
            evidence_sufficient=True,
            has_citations=True,
            citation_count=1,
            all_citations_verified=True,
            reply_chars=120,
        ),
        expected_action=AttemptAction.ACCEPT,
        active_feature_names=(
            "citation_required",
            "evidence_count",
            "evidence_sufficient",
            "has_citations",
            "citation_count",
            "all_citations_verified",
            "reply_chars",
        ),
    ),
    ObservationProbe(
        name="no_evidence",
        observation=AttemptObservation(
            citation_required=True,
            evidence_count=0,
            reply_chars=120,
        ),
        expected_action=AttemptAction.RETRY_EXPAND_EVIDENCE,
        active_feature_names=("citation_required", "evidence_count", "reply_chars"),
    ),
    ObservationProbe(
        name="missing_citation",
        observation=AttemptObservation(
            citation_required=True,
            evidence_count=1,
            evidence_sufficient=True,
            has_citations=False,
            missing_required_citation_count=1,
            reply_chars=120,
        ),
        expected_action=AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER,
        active_feature_names=(
            "citation_required",
            "evidence_count",
            "evidence_sufficient",
            "has_citations",
            "missing_required_citation_count",
            "reply_chars",
        ),
    ),
    ObservationProbe(
        name="invalid_citation",
        observation=AttemptObservation(
            citation_required=True,
            evidence_count=1,
            evidence_sufficient=True,
            has_citations=True,
            citation_count=1,
            all_citations_verified=False,
            unverified_citation_count=1,
            reply_chars=120,
        ),
        expected_action=AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER,
        active_feature_names=(
            "citation_required",
            "evidence_count",
            "evidence_sufficient",
            "has_citations",
            "citation_count",
            "all_citations_verified",
            "unverified_citation_count",
            "reply_chars",
        ),
    ),
    ObservationProbe(
        name="bad_answer_shape",
        observation=AttemptObservation(
            retrieval_strategy="overview",
            citation_required=True,
            evidence_count=1,
            evidence_sufficient=True,
            has_citations=True,
            citation_count=1,
            all_citations_verified=True,
            answer_shape_failed=True,
            reply_chars=120,
        ),
        expected_action=AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER,
        active_feature_names=(
            "retrieval_strategy_overview",
            "citation_required",
            "evidence_count",
            "evidence_sufficient",
            "has_citations",
            "citation_count",
            "all_citations_verified",
            "answer_shape_failed",
            "reply_chars",
        ),
    ),
    ObservationProbe(
        name="off_topic_answer",
        observation=AttemptObservation(
            citation_required=True,
            evidence_count=1,
            evidence_sufficient=True,
            has_citations=True,
            citation_count=1,
            all_citations_verified=True,
            off_topic_answer=True,
            unsupported_claim_count=1,
            reply_chars=120,
        ),
        expected_action=AttemptAction.ABSTAIN,
        active_feature_names=(
            "citation_required",
            "evidence_count",
            "evidence_sufficient",
            "has_citations",
            "citation_count",
            "all_citations_verified",
            "off_topic_answer",
            "unsupported_claim_count",
            "reply_chars",
        ),
    ),
    ObservationProbe(
        name="weak_evidence",
        observation=AttemptObservation(
            attempt_index=2,
            evidence_count=1,
            evidence_sufficient=False,
            evidence_recommended_action="abstain",
            reply_chars=120,
        ),
        expected_action=AttemptAction.ABSTAIN,
        active_feature_names=(
            "attempt_index",
            "evidence_count",
            "evidence_sufficient",
            "evidence_recommended_abstain",
            "reply_chars",
        ),
    ),
)
