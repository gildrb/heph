"""Observation signal diagnostics for structural answer-attempt guards."""

from __future__ import annotations

import random
from dataclasses import dataclass

from hephaion.learning.actions import AttemptAction
from hephaion.learning.observation import AttemptObservation
from hephaion.learning.policy import StaticAttemptPolicy

OBSERVATION_AUDIT_SEED = 13


@dataclass(frozen=True, slots=True)
class ObservationProbe:
    name: str
    observation: AttemptObservation
    expected_action: AttemptAction
    active_feature_names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ObservationAuditResult:
    probe: ObservationProbe
    chosen_action: AttemptAction

    @property
    def passed(self) -> bool:
        return self.chosen_action is self.probe.expected_action


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
    """Check that core observations drive the static policy in the expected direction."""

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
    return ObservationAuditResult(
        probe=probe,
        chosen_action=policy.choose(probe.observation),
    )


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
