"""Structural reward calculation for Heph harness attempts."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from hephaion._types import is_object_list, is_string_mapping
from hephaion.learning.actions import AttemptAction
from hephaion.learning.observation import AttemptObservation

_MIN_ABSTENTION_REWARD = 0.45
_MAX_REWARD = 1.0
_MIN_REWARD = -1.0
type RetryValueScorer = Callable[[AttemptObservation], float]


@dataclass(frozen=True, slots=True)
class RewardComponent:
    name: str
    value: float

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "value": self.value}

    @classmethod
    def from_dict(cls, payload: object) -> RewardComponent | None:
        if not is_string_mapping(payload):
            return None
        name = payload.get("name")
        value = payload.get("value")
        if not isinstance(name, str) or not isinstance(value, int | float):
            return None
        return cls(name=name, value=float(value))


@dataclass(frozen=True, slots=True)
class AttemptReward:
    total: float
    components: tuple[RewardComponent, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "total": self.total,
            "components": [component.to_dict() for component in self.components],
        }

    @classmethod
    def from_dict(cls, payload: object) -> AttemptReward:
        if not is_string_mapping(payload):
            return cls(total=0.0, components=())
        total = payload.get("total")
        raw_components = payload.get("components")
        components: tuple[RewardComponent, ...] = ()
        if is_object_list(raw_components):
            components = tuple(
                component
                for raw_component in raw_components
                if (component := RewardComponent.from_dict(raw_component)) is not None
            )
        return cls(
            total=_clamp_reward(float(total)) if isinstance(total, int | float) else 0.0,
            components=components,
        )


def score_attempt_reward(
    observation: AttemptObservation,
    *,
    accepted: bool,
    abstained: bool,
    max_attempt_failure: bool = False,
) -> AttemptReward:
    components: list[RewardComponent] = []
    _add(components, "non_empty_answer", 0.10 if observation.reply_chars > 0 else -0.35)
    _add_citation_components(components, observation)
    _add_evidence_components(components, observation)
    _add_cost_components(components, observation)
    if accepted:
        _add_accept_decision_components(components, observation)
    elif abstained:
        _add_abstain_decision_components(components, observation)
    _add_terminal_components(
        components,
        observation,
        accepted=accepted,
        abstained=abstained,
        max_attempt_failure=max_attempt_failure,
    )
    total = _clamp_reward(sum(component.value for component in components))
    return AttemptReward(total=total, components=tuple(components))


def score_action_outcome_reward(
    observation: AttemptObservation,
    action: AttemptAction,
    *,
    final_outcome: str = "",
) -> AttemptReward:
    """Score a structural policy decision without imitating a logged action."""
    components: list[RewardComponent] = []
    accepted = action is AttemptAction.ACCEPT
    abstained = action is AttemptAction.ABSTAIN
    _add_citation_components(components, observation)
    _add_evidence_components(components, observation)
    _add_cost_components(components, observation)
    _add_policy_action_components(components, observation, action)
    _add_terminal_components(
        components,
        observation,
        accepted=accepted,
        abstained=abstained,
        max_attempt_failure=final_outcome == "max_attempt_failure",
    )
    return AttemptReward(
        total=_clamp_reward(sum(component.value for component in components)),
        components=tuple(components),
    )


def _add_citation_components(
    components: list[RewardComponent],
    observation: AttemptObservation,
) -> None:
    if observation.citation_required:
        _add(components, "citation_present", 0.15 if observation.has_citations else -0.35)
        _add(
            components,
            "citation_validity",
            0.25 if observation.all_citations_verified else -1.00,
        )
    elif observation.unverified_citation_count:
        _add(components, "unneeded_invalid_citation", -0.40)


def _add_evidence_components(
    components: list[RewardComponent],
    observation: AttemptObservation,
) -> None:
    if observation.evidence_count:
        _add(components, "evidence_available", 0.10)
    if observation.evidence_sufficient:
        _add(components, "evidence_sufficient", 0.25)
    elif observation.evidence_recommended_action == "abstain":
        _add(components, "thin_evidence", -0.20)
    if observation.confident_thin_evidence:
        _add(components, "confident_thin_evidence", -0.65)
    if observation.answer_relevance_required and not observation.off_topic_answer:
        _add(components, "answer_relevance", 0.10 * observation.answer_relevance_score)
    if observation.distinct_source_count >= 2:
        _add(components, "source_diversity", 0.15)


def _add_cost_components(
    components: list[RewardComponent],
    observation: AttemptObservation,
) -> None:
    if observation.internal_passes > 1:
        _add(components, "retry_cost", -0.05 * (observation.internal_passes - 1))
    if observation.latency_ms > 0:
        _add(components, "latency_cost", -min(0.15, observation.latency_ms / 120_000))
    if observation.cost_usd > 0:
        _add(components, "money_cost", -min(0.15, observation.cost_usd / 0.10))


def _add_policy_action_components(
    components: list[RewardComponent],
    observation: AttemptObservation,
    action: AttemptAction,
) -> None:
    if action is AttemptAction.ACCEPT:
        _add_accept_decision_components(components, observation)
        return
    if action is AttemptAction.ABSTAIN:
        _add_abstain_decision_components(components, observation)
        return
    _add_retry_decision_components(components, observation, action)


def _add_accept_decision_components(
    components: list[RewardComponent],
    observation: AttemptObservation,
) -> None:
    if observation.off_topic_answer:
        _add(components, "accepted_off_topic_answer", -1.00)
    if observation.unsupported_claim_count:
        _add(components, "accepted_unsupported_claims", -0.90)
    if observation.missing_required_citation_count:
        _add(components, "accepted_missing_required_citations", -0.75)
    if observation.confident_thin_evidence:
        _add(components, "accepted_confident_thin_evidence", -0.75)
    if observation.citation_required and not observation.has_citations:
        _add(components, "accepted_uncited_required_answer", -0.70)
    if observation.unverified_citation_count:
        _add(components, "accepted_invalid_citations", -0.90)
    if _grounded_accept(observation):
        _add(components, "grounded_accept", 0.55)


def _add_abstain_decision_components(
    components: list[RewardComponent],
    observation: AttemptObservation,
) -> None:
    if _should_abstain(observation):
        _add(components, "correct_abstain", 0.65)
    elif _grounded_accept(observation):
        _add(components, "unnecessary_abstain", -0.45)
    else:
        _add(components, "defensive_abstain", 0.10)


def _add_retry_decision_components(
    components: list[RewardComponent],
    observation: AttemptObservation,
    action: AttemptAction,
) -> None:
    _add(components, "retry_attempt_cost", -0.08)
    component = _RETRY_FIT_COMPONENTS.get(action)
    if component is None:
        return
    name, scorer = component
    _add(components, name, scorer(observation))


def _strict_grounded_retry_value(observation: AttemptObservation) -> float:
    return 0.35 if _needs_grounded_retry(observation) else -0.10


def _expand_evidence_retry_value(observation: AttemptObservation) -> float:
    return 0.30 if observation.evidence_count == 0 else 0.05


def _diversify_sources_retry_value(observation: AttemptObservation) -> float:
    return 0.30 if 0 < observation.distinct_source_count < 2 else -0.10


def _neighbor_chunks_retry_value(observation: AttemptObservation) -> float:
    if observation.evidence_count > 0 and not observation.evidence_sufficient:
        return 0.20
    return -0.10


def _shorter_answer_retry_value(observation: AttemptObservation) -> float:
    return 0.20 if observation.reply_chars > 1200 else -0.10


def _overview_sampling_retry_value(observation: AttemptObservation) -> float:
    return 0.25 if observation.retrieval_strategy != "overview" else -0.10


def _rewrite_query_retry_value(observation: AttemptObservation) -> float:
    return 0.20 if observation.top_score < 0.35 else -0.05


_RETRY_FIT_COMPONENTS: Mapping[AttemptAction, tuple[str, RetryValueScorer]] = {
    AttemptAction.RETRY_STRICTER_GROUNDED_ANSWER: (
        "retry_stricter_grounded_fit",
        _strict_grounded_retry_value,
    ),
    AttemptAction.RETRY_EXPAND_EVIDENCE: (
        "retry_expand_evidence_fit",
        _expand_evidence_retry_value,
    ),
    AttemptAction.RETRY_DIVERSIFY_SOURCES: (
        "retry_diversify_sources_fit",
        _diversify_sources_retry_value,
    ),
    AttemptAction.RETRY_NEIGHBOR_CHUNKS: (
        "retry_neighbor_chunks_fit",
        _neighbor_chunks_retry_value,
    ),
    AttemptAction.RETRY_SHORTER_ANSWER: (
        "retry_shorter_answer_fit",
        _shorter_answer_retry_value,
    ),
    AttemptAction.RETRY_OVERVIEW_SAMPLING: (
        "retry_overview_sampling_fit",
        _overview_sampling_retry_value,
    ),
    AttemptAction.RETRY_REWRITE_QUERY: (
        "retry_rewrite_query_fit",
        _rewrite_query_retry_value,
    ),
}


def _add_terminal_components(
    components: list[RewardComponent],
    observation: AttemptObservation,
    *,
    accepted: bool,
    abstained: bool,
    max_attempt_failure: bool,
) -> None:
    if abstained:
        _add(
            components,
            "abstention",
            _MIN_ABSTENTION_REWARD
            if observation.evidence_recommended_action == "abstain"
            else -0.25,
        )
    if accepted:
        _add(components, "accepted_terminal", 0.25)
    if max_attempt_failure:
        _add(components, "max_attempt_failure", -0.60)


def _grounded_accept(observation: AttemptObservation) -> bool:
    if observation.reply_chars <= 0:
        return False
    if observation.unsupported_claim_count or observation.missing_required_citation_count:
        return False
    if observation.citation_required and not observation.has_citations:
        return False
    return bool(observation.all_citations_verified and observation.evidence_sufficient)


def _should_abstain(observation: AttemptObservation) -> bool:
    return bool(
        observation.off_topic_answer
        or observation.evidence_recommended_action == "abstain"
        or (observation.evidence_count == 0 and observation.citation_required)
    )


def _needs_grounded_retry(observation: AttemptObservation) -> bool:
    return bool(
        observation.evidence_count > 0
        and (
            not observation.has_citations
            or not observation.all_citations_verified
            or observation.unsupported_claim_count
            or observation.missing_required_citation_count
        )
    )


def _add(components: list[RewardComponent], name: str, value: float) -> None:
    components.append(RewardComponent(name=name, value=value))


def _clamp_reward(value: float) -> float:
    return max(_MIN_REWARD, min(_MAX_REWARD, round(value, 4)))
