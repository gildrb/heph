"""Structural reward calculation for Heph harness attempts."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from hephaion._types import is_object_list, is_string_mapping
from hephaion.learning.actions import AttemptAction
from hephaion.learning.observation import AttemptObservation

_MIN_REWARD = -1.0
_MAX_REWARD = 1.0

_GOOD_ACCEPT_REWARD = 0.85
_BAD_ACCEPT_REWARD = -0.85
_CORRECT_ABSTAIN_REWARD = 0.55
_UNNECESSARY_ABSTAIN_REWARD = -0.55
_DEFENSIVE_ABSTAIN_REWARD = -0.05
_MAX_ATTEMPT_FAILURE_REWARD = -0.75
_RETRY_COST = -0.04
_MAX_RETRY_FIT_REWARD = 0.06

_MAX_QUALITY_SHAPING = 0.15
_EMPTY_REPLY_PENALTY = -0.10
_NON_EMPTY_REPLY_REWARD = 0.03

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
    """Score an observed attempt outcome."""

    components: list[RewardComponent] = []
    _add_reply_component(components, observation)
    _add_quality_shaping(components, observation)

    if accepted:
        _add_accept_outcome(components, observation)
    elif abstained:
        _add_abstain_outcome(components, observation)

    _add_cost_components(components, observation)
    if max_attempt_failure:
        _add(components, "max_attempt_failure", _MAX_ATTEMPT_FAILURE_REWARD)

    return _finish(components)


def score_action_outcome_reward(
    observation: AttemptObservation,
    action: AttemptAction,
    *,
    final_outcome: str = "",
) -> AttemptReward:
    """Score the policy decision, not imitation of the logged decision."""

    components: list[RewardComponent] = []
    _add_reply_component(components, observation)
    _add_quality_shaping(components, observation)
    _add_cost_components(components, observation)

    if action is AttemptAction.ACCEPT:
        _add_accept_outcome(components, observation)
    elif action is AttemptAction.ABSTAIN:
        _add_abstain_outcome(components, observation)
    else:
        _add_retry_outcome(components, observation, action)

    if final_outcome == "max_attempt_failure":
        _add(components, "max_attempt_failure", _MAX_ATTEMPT_FAILURE_REWARD)

    return _finish(components)


def _add_reply_component(
    components: list[RewardComponent],
    observation: AttemptObservation,
) -> None:
    _add(
        components,
        "reply_present",
        _NON_EMPTY_REPLY_REWARD if observation.reply_chars > 0 else _EMPTY_REPLY_PENALTY,
    )


def _add_quality_shaping(
    components: list[RewardComponent],
    observation: AttemptObservation,
) -> None:
    quality = _answer_quality(observation)
    if quality != 0.0:
        _add(components, "answer_quality_shaping", _MAX_QUALITY_SHAPING * quality)


def _answer_quality(observation: AttemptObservation) -> float:
    """Return a bounded quality proxy in [-1, 1]."""

    if (hard_score := _hard_answer_quality_score(observation)) is not None:
        return hard_score

    score = 0.0
    if observation.evidence_count:
        score += 0.15
    if observation.evidence_sufficient:
        score += 0.35
    elif observation.evidence_recommended_action == "abstain":
        score -= 0.25

    if observation.answer_relevance_required:
        score += 0.20 * _clamp01(observation.answer_relevance_score)

    if observation.distinct_source_count >= 2:
        score += 0.10

    score += _citation_quality_score(observation)
    score -= min(0.50, 0.12 * observation.unsupported_claim_count)
    score -= min(0.50, 0.15 * observation.missing_required_citation_count)
    if observation.confident_thin_evidence:
        score -= 0.45

    return max(-1.0, min(1.0, score))


def _hard_answer_quality_score(observation: AttemptObservation) -> float | None:
    if observation.off_topic_answer or observation.answer_shape_failed:
        return -1.0
    if observation.reply_chars <= 0:
        return -0.5
    return None


def _citation_quality_score(observation: AttemptObservation) -> float:
    if not observation.citation_required:
        return -0.30 if observation.unverified_citation_count else 0.0
    if not observation.has_citations:
        return -0.40
    if observation.all_citations_verified:
        return 0.25
    return -0.55


def _add_accept_outcome(
    components: list[RewardComponent],
    observation: AttemptObservation,
) -> None:
    if _grounded_accept(observation):
        _add(components, "good_accept", _GOOD_ACCEPT_REWARD)
        return

    _add(components, "bad_accept", _BAD_ACCEPT_REWARD)
    _add_bad_accept_components(components, observation)


def _add_bad_accept_components(
    components: list[RewardComponent],
    observation: AttemptObservation,
) -> None:
    if observation.off_topic_answer:
        _add(components, "accepted_off_topic_answer", -0.15)
    if observation.answer_shape_failed:
        _add(components, "accepted_bad_answer_shape", -0.15)
    if observation.unsupported_claim_count:
        _add(components, "accepted_unsupported_claims", -0.10)
    if observation.missing_required_citation_count:
        _add(components, "accepted_missing_required_citations", -0.10)
    if observation.citation_required and not observation.has_citations:
        _add(components, "accepted_uncited_required_answer", -0.10)
    if observation.unverified_citation_count or not observation.all_citations_verified:
        _add(components, "accepted_invalid_or_unverified_citations", -0.10)
    if observation.confident_thin_evidence:
        _add(components, "accepted_confident_thin_evidence", -0.10)


def _add_abstain_outcome(
    components: list[RewardComponent],
    observation: AttemptObservation,
) -> None:
    if _should_abstain(observation):
        _add(components, "correct_abstain", _CORRECT_ABSTAIN_REWARD)
    elif _grounded_accept(observation):
        _add(components, "unnecessary_abstain", _UNNECESSARY_ABSTAIN_REWARD)
    else:
        _add(components, "defensive_abstain", _DEFENSIVE_ABSTAIN_REWARD)


def _add_retry_outcome(
    components: list[RewardComponent],
    observation: AttemptObservation,
    action: AttemptAction,
) -> None:
    _add(components, "retry_cost", _RETRY_COST)

    if _grounded_accept(observation):
        _add(components, "retry_when_accept_ready", -0.12)
        return
    if _should_abstain(observation):
        _add(components, "retry_when_abstain_ready", -0.08)
        return

    component = _RETRY_FIT_COMPONENTS.get(action)
    if component is None:
        _add(components, "unknown_retry_action", -0.08)
        return

    name, scorer = component
    _add(components, name, scorer(observation))


def _add_cost_components(
    components: list[RewardComponent],
    observation: AttemptObservation,
) -> None:
    if observation.internal_passes > 1:
        _add(
            components,
            "internal_pass_cost",
            -min(0.12, 0.03 * (observation.internal_passes - 1)),
        )
    if observation.latency_ms > 0:
        _add(components, "latency_cost", -min(0.08, observation.latency_ms / 180_000))
    if observation.cost_usd > 0:
        _add(components, "money_cost", -min(0.08, observation.cost_usd / 0.20))


def _strict_grounded_retry_value(observation: AttemptObservation) -> float:
    return _MAX_RETRY_FIT_REWARD if _needs_grounded_retry(observation) else -0.04


def _expand_evidence_retry_value(observation: AttemptObservation) -> float:
    if observation.evidence_count == 0 and not observation.off_topic_answer:
        return _MAX_RETRY_FIT_REWARD
    return -0.04


def _diversify_sources_retry_value(observation: AttemptObservation) -> float:
    if observation.evidence_count > 0 and observation.distinct_source_count < 2:
        return 0.05
    return -0.04


def _neighbor_chunks_retry_value(observation: AttemptObservation) -> float:
    if observation.evidence_count > 0 and not observation.evidence_sufficient:
        return 0.04
    return -0.04


def _shorter_answer_retry_value(observation: AttemptObservation) -> float:
    if observation.reply_chars > 1200 and observation.unsupported_claim_count:
        return 0.04
    return -0.04


def _overview_sampling_retry_value(observation: AttemptObservation) -> float:
    if observation.retrieval_strategy != "overview" and observation.top_score < 0.45:
        return 0.04
    return -0.04


def _rewrite_query_retry_value(observation: AttemptObservation) -> float:
    if observation.top_score < 0.35 and not observation.evidence_sufficient:
        return 0.05
    return -0.04


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


def _grounded_accept(observation: AttemptObservation) -> bool:
    if observation.reply_chars <= 0 or observation.off_topic_answer:
        return False
    if observation.answer_shape_failed:
        return False
    if observation.unsupported_claim_count or observation.missing_required_citation_count:
        return False
    if observation.citation_required and not observation.has_citations:
        return False
    if observation.unverified_citation_count or not observation.all_citations_verified:
        return False
    return bool(observation.evidence_sufficient)


def _should_abstain(observation: AttemptObservation) -> bool:
    return bool(
        observation.off_topic_answer or observation.evidence_recommended_action == "abstain"
    )


def _needs_grounded_retry(observation: AttemptObservation) -> bool:
    return bool(
        observation.evidence_count > 0
        and not observation.off_topic_answer
        and (
            not observation.has_citations
            or not observation.all_citations_verified
            or observation.unsupported_claim_count
            or observation.answer_shape_failed
            or observation.missing_required_citation_count
        )
    )


def _finish(components: list[RewardComponent]) -> AttemptReward:
    return AttemptReward(
        total=_clamp_reward(sum(component.value for component in components)),
        components=tuple(components),
    )


def _add(components: list[RewardComponent], name: str, value: float) -> None:
    if value != 0.0:
        components.append(RewardComponent(name=name, value=round(float(value), 4)))


def _clamp_reward(value: float) -> float:
    return max(_MIN_REWARD, min(_MAX_REWARD, round(value, 4)))


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))
