"""Structural reward calculation for Heph harness attempts."""

from __future__ import annotations

from dataclasses import dataclass

from hephaion._types import is_object_list, is_string_mapping
from hephaion.learning.observation import AttemptObservation

_MIN_ABSTENTION_REWARD = 0.45
_MAX_REWARD = 1.0
_MIN_REWARD = -1.0


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
    _add_terminal_components(
        components,
        observation,
        accepted=accepted,
        abstained=abstained,
        max_attempt_failure=max_attempt_failure,
    )
    total = _clamp_reward(sum(component.value for component in components))
    return AttemptReward(total=total, components=tuple(components))


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


def _add(components: list[RewardComponent], name: str, value: float) -> None:
    components.append(RewardComponent(name=name, value=value))


def _clamp_reward(value: float) -> float:
    return max(_MIN_REWARD, min(_MAX_REWARD, round(value, 4)))
