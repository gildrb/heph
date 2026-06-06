"""Armory-local storage for harness learning attempts."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from hephaion._types import is_string_mapping
from hephaion.learning.actions import AttemptAction, parse_attempt_action
from hephaion.learning.observation import AttemptObservation
from hephaion.learning.reward import AttemptReward, score_action_outcome_reward
from hephaion.rag.context import TurnEvidence

LEARNING_DIR = ".hephaion/learning"
POLICIES_DIR = "policies"
REPLAY_DIR = "replay"
ATTEMPTS_FILE = "attempts.jsonl"
AUTOMATION_EVENTS_FILE = "automation-events.jsonl"
AUTOMATION_STATE_FILE = "automation-state.json"
ATTEMPT_SCHEMA_VERSION = 1
EPISODE_SCHEMA_VERSION = 2


@dataclass(frozen=True, slots=True)
class ValidationState:
    name: str
    passed: bool
    detail: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
        }

    @classmethod
    def from_dict(cls, payload: object) -> ValidationState | None:
        if not is_string_mapping(payload):
            return None
        name = _payload_string(payload, "name")
        if not name:
            return None
        return cls(
            name=name,
            passed=_payload_bool(payload, "passed"),
            detail=_payload_string(payload, "detail"),
        )


@dataclass(frozen=True, slots=True)
class ActionOutcome:
    action: AttemptAction
    observation: AttemptObservation
    reward: AttemptReward
    final_outcome: str
    accepted: bool = False
    abstained: bool = False
    retry_succeeded: bool = False
    attempts: int = 1
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    validation_states: tuple[ValidationState, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "action": self.action.value,
            "observation": self.observation.to_dict(),
            "reward": self.reward.to_dict(),
            "final_outcome": self.final_outcome,
            "accepted": self.accepted,
            "abstained": self.abstained,
            "retry_succeeded": self.retry_succeeded,
            "attempts": self.attempts,
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "validation_states": [state.to_dict() for state in self.validation_states],
        }

    @classmethod
    def from_dict(cls, payload: object) -> ActionOutcome | None:
        if not is_string_mapping(payload):
            return None
        action = parse_attempt_action(payload.get("action"))
        if action is AttemptAction.ACCEPT and payload.get("action") != AttemptAction.ACCEPT.value:
            return None
        return cls(
            action=action,
            observation=AttemptObservation.from_dict(payload.get("observation")),
            reward=AttemptReward.from_dict(payload.get("reward")),
            final_outcome=_payload_string(payload, "final_outcome"),
            accepted=_payload_bool(payload, "accepted"),
            abstained=_payload_bool(payload, "abstained"),
            retry_succeeded=_payload_bool(payload, "retry_succeeded"),
            attempts=max(1, _payload_int(payload, "attempts", 1)),
            latency_ms=_payload_float(payload, "latency_ms"),
            cost_usd=_payload_float(payload, "cost_usd"),
            validation_states=_validation_states_from_payload(payload.get("validation_states")),
        )


@dataclass(frozen=True, slots=True)
class AttemptRecord:
    session_id: str
    turn_id: str
    action: AttemptAction
    observation: AttemptObservation
    reward: AttemptReward
    user_input: str
    reply: str
    evidence: TurnEvidence | None
    created_at: str
    episode_id: str = ""
    attempt_index: int = 1
    accepted: bool = False
    abstained: bool = False
    final_outcome: str = ""
    failed_validation_states: tuple[ValidationState, ...] = ()
    evidence_validation: tuple[ValidationState, ...] = ()
    citation_validation: tuple[ValidationState, ...] = ()
    retry_outcomes: tuple[str, ...] = ()
    action_outcomes: tuple[ActionOutcome, ...] = ()
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    replay_metadata: Mapping[str, object] | None = None
    schema_version: int = ATTEMPT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "episode_id": self.episode_id or self.turn_id,
            "attempt_index": self.attempt_index,
            "action": self.action.value,
            "observation": self.observation.to_dict(),
            "reward": self.reward.to_dict(),
            "accepted": self.accepted,
            "abstained": self.abstained,
            "final_outcome": self.final_outcome,
            "failed_validation_states": [
                state.to_dict() for state in self.failed_validation_states
            ],
            "evidence_validation": [state.to_dict() for state in self.evidence_validation],
            "citation_validation": [state.to_dict() for state in self.citation_validation],
            "retry_outcomes": list(self.retry_outcomes),
            "action_outcomes": [outcome.to_dict() for outcome in self.action_outcomes],
            "latency_ms": self.latency_ms,
            "cost_usd": self.cost_usd,
            "replay_metadata": dict(self.replay_metadata or {}),
            "user_input": self.user_input,
            "reply": self.reply,
        }
        if self.evidence is not None:
            payload["evidence"] = self.evidence.to_dict()
        return payload

    @classmethod
    def from_dict(cls, payload: object) -> AttemptRecord | None:
        if not is_string_mapping(payload):
            return None
        session_id = _payload_string(payload, "session_id")
        turn_id = _payload_string(payload, "turn_id")
        created_at = _payload_string(payload, "created_at")
        if not session_id or not turn_id:
            return None
        return cls(
            schema_version=_payload_int(payload, "schema_version", ATTEMPT_SCHEMA_VERSION),
            created_at=created_at or _now(),
            session_id=session_id,
            turn_id=turn_id,
            episode_id=_payload_string(payload, "episode_id") or turn_id,
            attempt_index=max(1, _payload_int(payload, "attempt_index", 1)),
            action=parse_attempt_action(payload.get("action")),
            observation=AttemptObservation.from_dict(payload.get("observation")),
            reward=AttemptReward.from_dict(payload.get("reward")),
            user_input=_payload_string(payload, "user_input"),
            reply=_payload_string(payload, "reply"),
            evidence=TurnEvidence.from_dict(payload.get("evidence")),
            accepted=_payload_bool(payload, "accepted"),
            abstained=_payload_bool(payload, "abstained"),
            final_outcome=_payload_string(payload, "final_outcome"),
            failed_validation_states=_validation_states_from_payload(
                payload.get("failed_validation_states")
            ),
            evidence_validation=_validation_states_from_payload(
                payload.get("evidence_validation")
            ),
            citation_validation=_validation_states_from_payload(
                payload.get("citation_validation")
            ),
            retry_outcomes=_string_tuple_from_payload(payload.get("retry_outcomes")),
            action_outcomes=_action_outcomes_from_payload(payload.get("action_outcomes")),
            latency_ms=_payload_float(payload, "latency_ms"),
            cost_usd=_payload_float(payload, "cost_usd"),
            replay_metadata=_metadata_from_payload(payload.get("replay_metadata")),
        )

    def outcome_for(self, action: AttemptAction) -> ActionOutcome:
        for outcome in self.action_outcomes:
            if outcome.action is action:
                return outcome
        if action is self.action:
            return ActionOutcome(
                action=self.action,
                observation=self.observation,
                reward=self.reward,
                final_outcome=self.final_outcome,
                accepted=self.accepted,
                abstained=self.abstained,
                retry_succeeded=self.final_outcome == "retry_succeeded",
                attempts=max(1, self.attempt_index),
                latency_ms=self.latency_ms,
                cost_usd=self.cost_usd,
                validation_states=(
                    *self.failed_validation_states,
                    *self.evidence_validation,
                    *self.citation_validation,
                ),
            )
        reward = score_action_outcome_reward(
            self.observation,
            action,
            final_outcome=self.final_outcome,
        )
        return ActionOutcome(
            action=action,
            observation=self.observation,
            reward=reward,
            final_outcome=f"counterfactual_{action.value}",
            accepted=action is AttemptAction.ACCEPT,
            abstained=action is AttemptAction.ABSTAIN,
            retry_succeeded=False,
            attempts=max(1, self.attempt_index + (0 if action is AttemptAction.ACCEPT else 1)),
            latency_ms=self.latency_ms,
            cost_usd=self.cost_usd,
        )


class LearningStore:
    def __init__(self, armory_path: Path) -> None:
        self.armory_path = armory_path

    @property
    def root(self) -> Path:
        return self.armory_path / LEARNING_DIR

    @property
    def attempts_path(self) -> Path:
        return self.root / ATTEMPTS_FILE

    @property
    def policies_dir(self) -> Path:
        return self.root / POLICIES_DIR

    @property
    def replay_dir(self) -> Path:
        return self.root / REPLAY_DIR

    @property
    def automation_state_path(self) -> Path:
        return self.root / AUTOMATION_STATE_FILE

    @property
    def automation_events_path(self) -> Path:
        return self.root / AUTOMATION_EVENTS_FILE

    def ensure_layout(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.policies_dir.mkdir(parents=True, exist_ok=True)
        self.replay_dir.mkdir(parents=True, exist_ok=True)

    def append_attempt(self, record: AttemptRecord) -> None:
        self.ensure_layout()
        with self.attempts_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def iter_attempts(self) -> Iterator[AttemptRecord]:
        path = self.attempts_path
        if not path.is_file():
            return
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if record := _record_from_jsonl(line):
                    yield record


def new_attempt_record(
    *,
    session_id: str,
    turn_id: str,
    action: AttemptAction,
    observation: AttemptObservation,
    reward: AttemptReward,
    user_input: str,
    reply: str,
    evidence: TurnEvidence | None,
    episode_id: str = "",
    attempt_index: int = 1,
    accepted: bool = False,
    abstained: bool = False,
    final_outcome: str = "",
    failed_validation_states: tuple[ValidationState, ...] = (),
    evidence_validation: tuple[ValidationState, ...] = (),
    citation_validation: tuple[ValidationState, ...] = (),
    retry_outcomes: tuple[str, ...] = (),
    action_outcomes: tuple[ActionOutcome, ...] = (),
    latency_ms: float = 0.0,
    cost_usd: float = 0.0,
    replay_metadata: Mapping[str, object] | None = None,
) -> AttemptRecord:
    return AttemptRecord(
        schema_version=EPISODE_SCHEMA_VERSION,
        created_at=_now(),
        session_id=session_id,
        turn_id=turn_id,
        episode_id=episode_id or turn_id,
        attempt_index=attempt_index,
        action=action,
        observation=observation,
        reward=reward,
        user_input=user_input,
        reply=reply,
        evidence=evidence,
        accepted=accepted,
        abstained=abstained,
        final_outcome=final_outcome,
        failed_validation_states=failed_validation_states,
        evidence_validation=evidence_validation,
        citation_validation=citation_validation,
        retry_outcomes=retry_outcomes,
        action_outcomes=action_outcomes,
        latency_ms=latency_ms,
        cost_usd=cost_usd,
        replay_metadata=replay_metadata,
    )


def _record_from_jsonl(line: str) -> AttemptRecord | None:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return None
    return AttemptRecord.from_dict(payload)


def _payload_string(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    return value if isinstance(value, str) else ""


def _payload_int(payload: Mapping[str, object], key: str, default: int) -> int:
    value = payload.get(key)
    if isinstance(value, bool):
        return default
    return value if isinstance(value, int) else default


def _payload_bool(payload: Mapping[str, object], key: str) -> bool:
    value = payload.get(key)
    return value if isinstance(value, bool) else False


def _payload_float(payload: Mapping[str, object], key: str) -> float:
    value = payload.get(key)
    if isinstance(value, bool):
        return 0.0
    return float(value) if isinstance(value, int | float) else 0.0


def _validation_states_from_payload(payload: object) -> tuple[ValidationState, ...]:
    if not isinstance(payload, list):
        return ()
    return tuple(
        state
        for raw_state in payload
        if (state := ValidationState.from_dict(raw_state)) is not None
    )


def _action_outcomes_from_payload(payload: object) -> tuple[ActionOutcome, ...]:
    if not isinstance(payload, list):
        return ()
    return tuple(
        outcome
        for raw_outcome in payload
        if (outcome := ActionOutcome.from_dict(raw_outcome)) is not None
    )


def _string_tuple_from_payload(payload: object) -> tuple[str, ...]:
    if not isinstance(payload, list):
        return ()
    return tuple(item for item in payload if isinstance(item, str))


def _metadata_from_payload(payload: object) -> Mapping[str, object] | None:
    return payload if is_string_mapping(payload) else None


def _now() -> str:
    return datetime.now(UTC).isoformat()
