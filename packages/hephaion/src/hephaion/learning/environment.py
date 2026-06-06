"""Local live and replay environments for Heph harness-policy learning."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from hephaion.learning.actions import AttemptAction
from hephaion.learning.observation import AttemptObservation
from hephaion.learning.reward import AttemptReward
from hephaion.learning.storage import AttemptRecord, LearningStore, ValidationState


@dataclass(frozen=True, slots=True)
class EnvironmentStep:
    observation: AttemptObservation
    reward: AttemptReward
    terminated: bool
    info: Mapping[str, object]


class LiveHephEnv:
    """Armory-local live environment surface for recording real attempts."""

    def __init__(self, armory_path: Path) -> None:
        self.store = LearningStore(armory_path)
        self._validation_states: list[ValidationState] = []
        self._chosen_actions: list[AttemptAction] = []
        self._retry_outcomes: list[str] = []

    def validator_failure(self, name: str, detail: str = "") -> None:
        self._validation_states.append(ValidationState(name=name, passed=False, detail=detail))

    def choose_action(
        self,
        observation: AttemptObservation,
        policy_action: AttemptAction,
    ) -> AttemptAction:
        self._chosen_actions.append(policy_action)
        return policy_action

    def record_retry(self, action: AttemptAction, outcome: str) -> None:
        self._chosen_actions.append(action)
        self._retry_outcomes.append(outcome)

    def finalize(self, record: AttemptRecord) -> AttemptRecord:
        enriched = record
        if self._validation_states or self._retry_outcomes:
            enriched = AttemptRecord(
                schema_version=record.schema_version,
                created_at=record.created_at,
                session_id=record.session_id,
                turn_id=record.turn_id,
                episode_id=record.episode_id,
                attempt_index=record.attempt_index,
                action=record.action,
                observation=record.observation,
                reward=record.reward,
                user_input=record.user_input,
                reply=record.reply,
                evidence=record.evidence,
                accepted=record.accepted,
                abstained=record.abstained,
                final_outcome=record.final_outcome,
                failed_validation_states=(
                    *record.failed_validation_states,
                    *tuple(self._validation_states),
                ),
                evidence_validation=record.evidence_validation,
                citation_validation=record.citation_validation,
                retry_outcomes=(*record.retry_outcomes, *tuple(self._retry_outcomes)),
                action_outcomes=record.action_outcomes,
                latency_ms=record.latency_ms,
                cost_usd=record.cost_usd,
                replay_metadata=record.replay_metadata,
            )
        self.record(enriched)
        return enriched

    def record(self, record: AttemptRecord) -> None:
        self.store.append_attempt(record)


class ReplayHephEnv:
    """Deterministic replay environment over saved local attempt records."""

    def __init__(self, records: Sequence[AttemptRecord]) -> None:
        self._records = tuple(records)
        self._index = 0

    @classmethod
    def from_armory(cls, armory_path: Path) -> ReplayHephEnv:
        return cls(tuple(LearningStore(armory_path).iter_attempts()))

    def reset(self) -> AttemptObservation:
        self._index = 0
        return self._current_observation()

    def step(self, action: AttemptAction) -> EnvironmentStep:
        if not self._records:
            return EnvironmentStep(
                observation=AttemptObservation(),
                reward=AttemptReward(total=0.0, components=()),
                terminated=True,
                info={"empty": True},
            )
        record = self._records[self._index]
        outcome = record.outcome_for(action)
        self._index += 1
        terminated = self._index >= len(self._records)
        observation = record.observation if terminated else self._current_observation()
        return EnvironmentStep(
            observation=observation,
            reward=outcome.reward,
            terminated=terminated,
            info={
                "recorded_action": record.action.value,
                "chosen_action": action.value,
                "matched_record": action == record.action,
                "final_outcome": outcome.final_outcome,
                "attempts": outcome.attempts,
                "latency_ms": outcome.latency_ms,
                "cost_usd": outcome.cost_usd,
            },
        )

    def _current_observation(self) -> AttemptObservation:
        if not self._records:
            return AttemptObservation()
        return self._records[self._index].observation
