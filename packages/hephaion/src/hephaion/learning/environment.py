"""Local live and replay environments for Heph harness-policy learning."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from hephaion.learning.actions import AttemptAction
from hephaion.learning.observation import AttemptObservation
from hephaion.learning.reward import AttemptReward
from hephaion.learning.storage import AttemptRecord, LearningStore


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
        reward = record.reward if action == record.action else _mismatched_action_reward()
        self._index += 1
        terminated = self._index >= len(self._records)
        observation = record.observation if terminated else self._current_observation()
        return EnvironmentStep(
            observation=observation,
            reward=reward,
            terminated=terminated,
            info={
                "recorded_action": record.action.value,
                "chosen_action": action.value,
                "matched_record": action == record.action,
            },
        )

    def _current_observation(self) -> AttemptObservation:
        if not self._records:
            return AttemptObservation()
        return self._records[self._index].observation


def _mismatched_action_reward() -> AttemptReward:
    return AttemptReward(total=-0.05, components=())
